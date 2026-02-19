# ugit v2.0
# MicroPython OTA update from GitHub
# Created by TURFPTAx for the OpenMuscle project
# https://openmuscle.org
#
# Install:
#   import mip; mip.install("github:turfptax/ugit")
#
# Quick start (one-time setup via REPL or Thonny):
#   import ugit
#   ugit.create_config(ssid='YourWifi', password='YourPass',
#                      user='github_user', repository='your-repo')
#
# Then in your main.py (safe to commit — no secrets in code):
#   import ugit
#   ugit.pull_all()
#
# Credentials are stored in /config.json on the device only.
# This file is auto-ignored so ugit will never delete or overwrite it.
# NEVER commit config.json to your GitHub repository.

__version__ = '2.1.0'

import os
import urequests
import json
import hashlib
import binascii
import machine
import time
import network

_GITHUB_API = 'https://api.github.com/repos'
_GITHUB_RAW = 'https://raw.githubusercontent.com'
_USER_AGENT = 'ugit-turfptax'
_CONFIG_PATH = '/config.json'


def _headers(token=''):
    h = {'User-Agent': _USER_AGENT}
    if token:
        h['authorization'] = 'bearer %s' % token
    return h


def _git_blob_hash(data):
    """Compute SHA1 the way GitHub does: sha1('blob {size}\\0{content}')"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    header = ('blob %d\0' % len(data)).encode('utf-8')
    sha = hashlib.sha1(header + data)
    return binascii.hexlify(sha.digest()).decode('utf-8')


def _local_file_hash(filepath):
    """Get the GitHub-compatible blob SHA1 of a local file."""
    try:
        f = open(filepath, 'rb')
        data = f.read()
        f.close()
    except:
        data = b''
    return _git_blob_hash(data)


def _is_directory(path):
    try:
        # stat[0] has mode bits; 0x4000 is the directory flag
        return os.stat(path)[0] & 0x4000 != 0
    except:
        return False


def _build_internal_tree(path='/'):
    """Recursively scan the device filesystem, return {'/path': 'sha1hash'}."""
    tree = {}
    os.chdir(path)
    for item in os.listdir():
        full = path + item if path.endswith('/') else path + '/' + item
        if _is_directory(full):
            if os.listdir(full):
                tree.update(_build_internal_tree(full))
        else:
            try:
                tree[full] = _local_file_hash(full)
            except OSError:
                pass
    os.chdir('/')
    return tree


def _get_storage_info():
    """Get filesystem storage info in bytes. Returns (total, free, used)."""
    stat = os.statvfs('/')
    block_size = stat[0]
    total_blocks = stat[2]
    free_blocks = stat[3]
    total = block_size * total_blocks
    free = block_size * free_blocks
    used = total - free
    return total, free, used


def _file_size(filepath):
    """Get size of a single file in bytes."""
    try:
        return os.stat(filepath)[6]
    except:
        return 0


def _is_usb_cdc():
    """Detect if this board likely uses native USB-CDC for serial.

    USB-CDC boards (ESP32-S2, S3, C3, C6) lose their serial port on
    machine.reset(). If boot.py/main.py crashes before USB re-enumerates,
    the device becomes inaccessible and requires reflashing.
    """
    try:
        machine_str = os.uname().machine.upper()
        for chip in ('ESP32S3', 'ESP32S2', 'ESP32C6', 'ESP32C3', 'ESP32H2'):
            if chip in machine_str:
                return True
    except:
        pass
    return False


def _is_ignored(path, ignore):
    """Check if path matches any ignore entry (exact or directory prefix).

    '/lib' in ignore matches '/lib/aioble/core.mpy' but not '/library/foo.py'.
    """
    for entry in ignore:
        e = entry.rstrip('/')
        if path == e or path.startswith(e + '/'):
            return True
    return False


def _repo_download_size(git_tree, local_tree, ignore):
    """Estimate bytes that will be downloaded (only changed/new files)."""
    download = 0
    for item in git_tree['tree']:
        if item['type'] != 'blob':
            continue
        path = item['path']
        if not path.startswith('/'):
            path = '/' + path
        if _is_ignored(path, ignore):
            continue
        git_sha = item.get('sha', '')
        local_sha = local_tree.get(path, '')
        if not (git_sha and local_sha and git_sha == local_sha):
            download += item.get('size', 0)
    return download


def _fmt_size(b):
    """Format bytes as human-readable string."""
    if b < 1024:
        return '%d B' % b
    elif b < 1024 * 1024:
        return '%d KB' % (b // 1024)
    else:
        return '%d.%d MB' % (b // (1024 * 1024), (b % (1024 * 1024)) * 10 // (1024 * 1024))


def storage_info():
    """Print human-readable storage info for the device."""
    total, free, used = _get_storage_info()
    print('Storage: %s total, %s used, %s free (%d%% free)' % (
        _fmt_size(total), _fmt_size(used), _fmt_size(free),
        (free * 100) // total if total else 0))
    return {'total': total, 'free': free, 'used': used}


def _ensure_ignore(ignore):
    """Make sure config.json and ugit.py are always in the ignore list."""
    if ignore is None:
        ignore = []
    protected = ['/ugit.py', _CONFIG_PATH, '/ugit.backup', '/ugit_log.txt', '/lib', '/sd']
    for p in protected:
        if p not in ignore:
            ignore.append(p)
    return ignore


def _load_config():
    """Load config from /config.json. Returns dict or empty dict if not found."""
    try:
        f = open(_CONFIG_PATH, 'r')
        cfg = json.loads(f.read())
        f.close()
        return cfg
    except:
        return {}


def _resolve_config(user=None, repository=None, branch=None, token=None,
                    ssid=None, password=None, ignore=None):
    """Merge explicit arguments with config.json, arguments take priority."""
    cfg = _load_config()
    return {
        'user': user or cfg.get('user', ''),
        'repository': repository or cfg.get('repository', ''),
        'branch': branch or cfg.get('branch', 'main'),
        'token': token if token is not None else cfg.get('token', ''),
        'ssid': ssid or cfg.get('ssid', ''),
        'password': password or cfg.get('password', ''),
        'ignore': ignore if ignore is not None else cfg.get('ignore', []),
    }


def create_config(ssid='', password='', user='', repository='',
                  branch='main', token='', ignore=None):
    """
    Save credentials to /config.json on the device.

    Run this once via REPL or Thonny to set up your device.
    The config file stays on the device and is never synced to GitHub.

    Example:
        ugit.create_config(
            ssid='MyWifi',
            password='MyPassword',
            user='turfptax',
            repository='my-project',
            token='ghp_xxxx'  # optional, for private repos
        )
    """
    if ignore is None:
        ignore = []
    cfg = {
        'ssid': ssid,
        'password': password,
        'user': user,
        'repository': repository,
        'branch': branch,
        'token': token,
        'ignore': ignore,
    }
    # MicroPython devices have no secure keychain; credentials must be stored
    # on the local filesystem. config.json is auto-protected from sync and
    # should never be committed to the GitHub repository.
    f = open(_CONFIG_PATH, 'w')
    f.write(json.dumps(cfg))
    f.close()
    # Print confirmation (field names only, never values)
    field_names = [k for k in cfg if cfg[k]]
    print('Config saved to %s' % _CONFIG_PATH)
    print('Fields stored: %s' % ', '.join(field_names))
    print('WARNING: config.json contains credentials. Never commit it to GitHub.')


def show_config():
    """Display current config (passwords are masked)."""
    cfg = _load_config()
    if not cfg:
        print('No config found. Run ugit.create_config() to set up.')
        return
    for k, v in cfg.items():
        if k in ('password', 'token') and v:
            print('  %s: %s' % (k, v[:3] + '*' * (len(v) - 3)))
        else:
            print('  %s: %s' % (k, v))


def wificonnect(ssid=None, password=None):
    """Connect to WiFi. Returns the WLAN object.
    If ssid/password not provided, reads from config.json."""
    if not ssid or not password:
        cfg = _load_config()
        ssid = ssid or cfg.get('ssid', '')
        password = password or cfg.get('password', '')
    if not ssid or not password:
        raise ValueError('No WiFi credentials. Pass ssid/password or run ugit.create_config()')
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    wlan.active(True)
    wlan.connect(ssid, password)
    retries = 0
    while not wlan.isconnected():
        time.sleep(1)
        retries += 1
        if retries > 30:
            raise OSError('WiFi connection timed out')
    print('WiFi connected:', wlan.ifconfig()[0])
    return wlan


def pull_git_tree(user, repository, branch='main', token=''):
    """Fetch the full recursive tree from GitHub API."""
    url = '%s/%s/%s/git/trees/%s?recursive=1' % (_GITHUB_API, user, repository, branch)
    r = urequests.get(url, headers=_headers(token))
    data = json.loads(r.content.decode('utf-8'))
    r.close()
    if 'tree' not in data:
        raise Exception('Branch "%s" not found for %s/%s' % (branch, user, repository))
    return data


def pull(filepath, raw_url, token=''):
    """Download a single file from GitHub and write it to the device."""
    r = urequests.get(raw_url, headers=_headers(token))
    data = r.content
    r.close()
    # ensure parent directory exists
    parts = filepath.split('/')
    for i in range(1, len(parts)):
        d = '/'.join(parts[:i])
        if d:
            try:
                os.mkdir(d)
            except:
                pass
    f = open(filepath, 'wb')
    f.write(data)
    f.close()
    return data


def pull_all(user=None, repository=None, branch=None, token=None,
             ssid=None, password=None, ignore=None,
             isconnected=False, reset_after=False):
    """
    Sync device filesystem with a GitHub repository.

    Only downloads files whose SHA1 hash differs from the local copy.
    Deletes local files not present in the repo (except ignored files).

    All arguments are optional if config.json exists on the device.
    Explicit arguments override config.json values.

    Args:
        user:         GitHub username
        repository:   GitHub repository name
        branch:       Branch to pull from (default 'main')
        token:        Personal access token for private repos
        ssid:         WiFi SSID (skipped if isconnected=True)
        password:     WiFi password
        ignore:       Extra file paths to never touch
        isconnected:  Set True if already connected to WiFi
        reset_after:  Reset the device after update (default False).
                      Ignored on USB-CDC boards (ESP32-S2/S3/C3/C6) to
                      prevent bricking if boot code has errors.
    """
    c = _resolve_config(user, repository, branch, token, ssid, password, ignore)
    ignore = _ensure_ignore(c['ignore'])

    if not c['user'] or not c['repository']:
        raise ValueError('user and repository required. Pass them or run ugit.create_config()')

    if not isconnected:
        wificonnect(c['ssid'], c['password'])

    os.chdir('/')
    raw_base = '%s/%s/%s/%s/' % (_GITHUB_RAW, c['user'], c['repository'], c['branch'])

    # fetch repo tree from GitHub
    print('Fetching repository tree...')
    git_tree = pull_git_tree(c['user'], c['repository'], c['branch'], c['token'])

    # build local file tree with hashes
    print('Scanning local files...')
    local_tree = _build_internal_tree()

    log = []
    updated = 0
    skipped = 0
    deleted = 0
    git_files = set()

    for item in git_tree['tree']:
        path = item['path']
        # normalize to absolute path
        if not path.startswith('/'):
            path = '/' + path

        if item['type'] == 'tree':
            try:
                os.mkdir(path)
            except:
                pass
            continue

        git_files.add(path)

        if _is_ignored(path, ignore):
            skipped += 1
            continue

        # compare hashes — only download if changed or new
        git_sha = item.get('sha', '')
        local_sha = local_tree.get(path, '')

        if git_sha and local_sha and git_sha == local_sha:
            skipped += 1
            log.append(path + ' unchanged')
            continue

        # download the file
        try:
            pull(path, raw_base + item['path'], c['token'])
            updated += 1
            log.append(path + ' updated')
            print('  updated:', path)
        except Exception as e:
            log.append(path + ' FAILED: ' + str(e))
            print('  FAILED:', path, e)

    # delete local files not in the repo (except ignored)
    for local_path in local_tree:
        if local_path not in git_files and not _is_ignored(local_path, ignore):
            try:
                os.remove(local_path)
                deleted += 1
                log.append(local_path + ' deleted')
                print('  deleted:', local_path)
            except:
                log.append(local_path + ' delete failed')

    # write log
    summary = 'ugit: %d updated, %d skipped, %d deleted' % (updated, skipped, deleted)
    print(summary)
    log.insert(0, summary)
    try:
        f = open('/ugit_log.txt', 'w')
        f.write('\n'.join(log))
        f.close()
    except:
        pass

    if reset_after:
        if _is_usb_cdc():
            print('WARNING: USB-CDC board detected (%s).' % os.uname().machine)
            print('machine.reset() skipped — reset manually or power-cycle.')
            print('Auto-reset can brick USB-CDC boards if boot.py/main.py crashes.')
        else:
            print('Resetting device in 5 seconds...')
            time.sleep(5)
            machine.reset()

    return log


def check_for_updates(user=None, repository=None, branch=None, token=None,
                      ignore=None, isconnected=False,
                      ssid=None, password=None):
    """
    Check if the repo has changes without downloading anything.
    Returns a dict with 'new', 'changed', 'deleted' file lists.

    All arguments are optional if config.json exists on the device.
    """
    c = _resolve_config(user, repository, branch, token, ssid, password, ignore)
    ignore = _ensure_ignore(c['ignore'])

    if not c['user'] or not c['repository']:
        raise ValueError('user and repository required. Pass them or run ugit.create_config()')

    if not isconnected:
        wificonnect(c['ssid'], c['password'])

    os.chdir('/')
    git_tree = pull_git_tree(c['user'], c['repository'], c['branch'], c['token'])
    local_tree = _build_internal_tree()
    git_files = set()

    new = []
    changed = []
    deleted = []

    for item in git_tree['tree']:
        if item['type'] != 'blob':
            continue
        path = item['path']
        if not path.startswith('/'):
            path = '/' + path
        git_files.add(path)
        if _is_ignored(path, ignore):
            continue
        local_sha = local_tree.get(path, '')
        if not local_sha:
            new.append(path)
        elif item.get('sha', '') != local_sha:
            changed.append(path)

    for local_path in local_tree:
        if local_path not in git_files and not _is_ignored(local_path, ignore):
            deleted.append(local_path)

    return {'new': new, 'changed': changed, 'deleted': deleted}


def update(branch=None, token=None):
    """Update ugit.py itself from this repository.

    Args:
        branch:  Branch to pull from (default: 'main'). Use this to test
                 development branches, e.g. ugit.update('fix/my-branch')
        token:   GitHub token for private repos (reads from config if None)

    Detects where ugit was imported from (e.g. /lib/ugit.py vs /ugit.py)
    and updates in-place so mip-installed copies are updated correctly.
    """
    if token is None:
        cfg = _load_config()
        token = cfg.get('token', '')
    if branch is None:
        branch = 'main'
    # Update in the same location ugit was imported from
    try:
        dest = __file__
    except:
        dest = '/ugit.py'
    raw_url = '%s/turfptax/ugit/%s/ugit.py' % (_GITHUB_RAW, branch)
    pull(dest, raw_url, token)
    print('ugit updated at %s from branch %s. Reset device to use new version.' % (dest, branch))


def backup(ignore=None):
    """Backup all files on the device to /ugit.backup.
    Returns the number of files backed up, or -1 if not enough space."""
    ignore = _ensure_ignore(ignore)
    local_tree = _build_internal_tree()

    # estimate backup size: sum of file contents + metadata overhead
    backup_size = 0
    file_count = 0
    for path in local_tree:
        if not _is_ignored(path, ignore):
            backup_size += _file_size(path) + len(path) + 80  # metadata per file
            file_count += 1

    _, free, _ = _get_storage_info()
    if backup_size > free:
        print('Not enough space for backup.')
        print('  Need: %s, Free: %s' % (_fmt_size(backup_size), _fmt_size(free)))
        return -1

    f = open('/ugit.backup', 'w')
    f.write('ugit backup v2\n')
    for path, sha in local_tree.items():
        if _is_ignored(path, ignore):
            continue
        f.write('FILE:%s SHA:%s\n' % (path, sha))
        try:
            df = open(path, 'rb')
            content = df.read()
            df.close()
            try:
                f.write('---\n')
                f.write(content.decode('utf-8'))
                f.write('\n---\n')
            except:
                f.write('---BINARY:%d---\n' % len(content))
        except:
            f.write('---ERROR---\n')
    f.close()
    print('Backup saved to /ugit.backup (%d files, ~%s)' % (
        file_count, _fmt_size(backup_size)))
    return file_count


def restore(ignore=None):
    """
    Restore files from /ugit.backup.

    Reads the backup file, recreates directories, and writes files back.
    Use this if an OTA update went wrong.

    Example:
        ugit.restore()
    """
    ignore = _ensure_ignore(ignore)
    try:
        f = open('/ugit.backup', 'r')
    except:
        print('No backup file found at /ugit.backup')
        return False

    header = f.readline().strip()
    if not header.startswith('ugit backup'):
        print('Invalid backup file format.')
        f.close()
        return False

    restored = 0
    skipped = 0
    current_path = None
    current_content = None
    in_content = False

    for line in f:
        line_stripped = line.rstrip('\n')

        if line_stripped.startswith('FILE:'):
            # save previous file if we have one
            if current_path and current_content is not None:
                if not _is_ignored(current_path, ignore):
                    _restore_file(current_path, current_content)
                    restored += 1
                else:
                    skipped += 1
            # parse new file entry: FILE:/path SHA:hash
            parts = line_stripped.split(' SHA:')
            current_path = parts[0][5:]  # strip 'FILE:'
            current_content = None
            in_content = False

        elif line_stripped == '---' and not in_content:
            in_content = True
            current_content = ''

        elif line_stripped == '---' and in_content:
            in_content = False

        elif line_stripped.startswith('---BINARY:') or line_stripped == '---ERROR---':
            in_content = False
            current_content = None
            print('  skip (binary/error): %s' % current_path)

        elif in_content:
            if current_content:
                current_content += '\n' + line_stripped
            else:
                current_content = line_stripped

    # save last file
    if current_path and current_content is not None:
        if not _is_ignored(current_path, ignore):
            _restore_file(current_path, current_content)
            restored += 1
        else:
            skipped += 1

    f.close()
    print('Restore complete: %d files restored, %d skipped' % (restored, skipped))
    return True


def _restore_file(filepath, content):
    """Write a file back to the device, creating directories as needed."""
    parts = filepath.split('/')
    for i in range(1, len(parts)):
        d = '/'.join(parts[:i])
        if d:
            try:
                os.mkdir(d)
            except:
                pass
    f = open(filepath, 'w')
    f.write(content)
    f.close()
    print('  restored:', filepath)


def safe_pull_all(user=None, repository=None, branch=None, token=None,
                  ssid=None, password=None, ignore=None,
                  isconnected=False, reset_after=False):
    """
    Like pull_all(), but checks available storage first and creates a
    backup before updating. If the update fails, the backup remains
    on the device for manual restore via ugit.restore().

    Pre-flight checks:
      1. Estimates download size from GitHub tree
      2. Estimates backup size from local files
      3. Verifies enough free space for backup + downloads
      4. Creates backup
      5. Runs the update
      6. If update fails, prints restore instructions

    reset_after defaults to False. On USB-CDC boards (ESP32-S2/S3/C3/C6),
    machine.reset() is always skipped to prevent bricking.

    Example:
        ugit.safe_pull_all()
    """
    c = _resolve_config(user, repository, branch, token, ssid, password, ignore)
    ignore = _ensure_ignore(c['ignore'])

    if not c['user'] or not c['repository']:
        raise ValueError('user and repository required. Pass them or run ugit.create_config()')

    if not isconnected:
        wificonnect(c['ssid'], c['password'])

    os.chdir('/')

    # step 1: gather info
    print('Pre-flight check...')
    total, free, used = _get_storage_info()
    print('  Storage: %s free of %s' % (_fmt_size(free), _fmt_size(total)))

    git_tree = pull_git_tree(c['user'], c['repository'], c['branch'], c['token'])
    local_tree = _build_internal_tree()

    # step 2: estimate sizes
    download_size = _repo_download_size(git_tree, local_tree, ignore)

    backup_size = 0
    for path in local_tree:
        if not _is_ignored(path, ignore):
            backup_size += _file_size(path) + len(path) + 80

    # we need space for: backup file + downloaded files + 4KB buffer
    needed = backup_size + download_size + 4096
    print('  Backup estimate: %s' % _fmt_size(backup_size))
    print('  Download estimate: %s' % _fmt_size(download_size))
    print('  Total needed: %s' % _fmt_size(needed))

    if needed > free:
        shortfall = needed - free
        print('\nNot enough space! Short by %s.' % _fmt_size(shortfall))
        print('Free up space or use pull_all() without backup.')
        return None

    # step 3: backup
    print('\nCreating backup...')
    result = backup(ignore)
    if result == -1:
        print('Backup failed. Aborting safe update.')
        return None

    # step 4: run the update
    print('\nStarting update...')
    try:
        log = pull_all(
            user=c['user'], repository=c['repository'],
            branch=c['branch'], token=c['token'],
            ignore=ignore, isconnected=True, reset_after=False
        )
    except Exception as e:
        print('\nUpdate FAILED: %s' % str(e))
        print('Your backup is at /ugit.backup')
        print('Run ugit.restore() to roll back.')
        return None

    print('\nUpdate complete with backup at /ugit.backup')
    if reset_after:
        if _is_usb_cdc():
            print('WARNING: USB-CDC board detected (%s).' % os.uname().machine)
            print('machine.reset() skipped — reset manually or power-cycle.')
            print('Auto-reset can brick USB-CDC boards if boot.py/main.py crashes.')
        else:
            print('Resetting device in 5 seconds...')
            time.sleep(5)
            machine.reset()

    return log
