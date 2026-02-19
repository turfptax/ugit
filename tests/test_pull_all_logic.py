"""Tests for pull_all() sync and delete logic.

These tests verify the core safety property: pull_all() must
never delete files that are in the ignore list, and must never
delete files that exist in the remote repo.

The bricking bug occurred when /lib/* files were deleted because
the ignore matching was broken. These tests guard against regression.
"""
import pytest
from unittest.mock import MagicMock
import ugit


def make_git_tree(files):
    """Build a git_tree dict from a list of (path, sha, size) tuples."""
    tree = []
    dirs_seen = set()
    for path, sha, size in files:
        parts = path.strip('/').split('/')
        for i in range(len(parts) - 1):
            d = '/'.join(parts[:i + 1])
            if d not in dirs_seen:
                dirs_seen.add(d)
                tree.append({'path': d, 'type': 'tree'})
        tree.append({
            'path': path.lstrip('/'),
            'type': 'blob',
            'sha': sha,
            'size': size,
        })
    return {'tree': tree, 'truncated': False}


class TestPullAllDeleteLogic:
    """Test which files pull_all() decides to delete."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self, monkeypatch):
        """Mock all network and filesystem operations."""
        monkeypatch.setattr(ugit, 'wificonnect', lambda *a, **kw: None)

        self.pulled_files = []

        def fake_pull(filepath, raw_url, token=''):
            self.pulled_files.append(filepath)

        monkeypatch.setattr(ugit, 'pull', fake_pull)
        monkeypatch.setattr('os.chdir', lambda p: None)
        monkeypatch.setattr('os.mkdir', lambda p: None)

        self.deleted_files = []
        monkeypatch.setattr('os.remove',
                            lambda p: self.deleted_files.append(p))

        # Mock log file writing
        monkeypatch.setattr('builtins.open',
                            lambda *a, **kw: MagicMock())

        monkeypatch.setattr(ugit, '_load_config', lambda: {})

    def test_local_only_file_gets_deleted(self, monkeypatch):
        """A file on device but not in repo should be deleted."""
        monkeypatch.setattr(ugit, 'pull_git_tree', lambda *a, **kw:
            make_git_tree([('main.py', 'sha1', 100)]))
        monkeypatch.setattr(ugit, '_build_internal_tree', lambda: {
            '/main.py': 'sha1',
            '/old_file.py': 'sha_old',
        })

        ugit.pull_all(user='u', repository='r', isconnected=True)
        assert '/old_file.py' in self.deleted_files

    def test_ignored_file_never_deleted(self, monkeypatch):
        """Auto-protected files must NEVER be deleted."""
        monkeypatch.setattr(ugit, 'pull_git_tree', lambda *a, **kw:
            make_git_tree([('main.py', 'sha1', 100)]))
        monkeypatch.setattr(ugit, '_build_internal_tree', lambda: {
            '/main.py': 'sha1',
            '/config.json': 'sha_cfg',
            '/ugit.py': 'sha_ugit',
            '/ugit.backup': 'sha_bak',
            '/ugit_log.txt': 'sha_log',
        })

        ugit.pull_all(user='u', repository='r', isconnected=True)
        assert '/config.json' not in self.deleted_files
        assert '/ugit.py' not in self.deleted_files
        assert '/ugit.backup' not in self.deleted_files
        assert '/ugit_log.txt' not in self.deleted_files

    def test_lib_directory_protected(self, monkeypatch):
        """Files under /lib/ must never be deleted (mip packages).

        This is the regression test for the bricking bug: ugit deleted
        /lib/aioble/*.mpy, then machine.reset() rebooted into a crash
        loop because main.py imported aioble.
        """
        monkeypatch.setattr(ugit, 'pull_git_tree', lambda *a, **kw:
            make_git_tree([('main.py', 'sha1', 100)]))
        monkeypatch.setattr(ugit, '_build_internal_tree', lambda: {
            '/main.py': 'sha1',
            '/lib/aioble/core.mpy': 'sha_aioble',
            '/lib/aioble/__init__.mpy': 'sha_init',
            '/lib/aioble/peripheral.mpy': 'sha_peri',
            '/lib/neopixel.mpy': 'sha_neo',
            '/lib/ugit.py': 'sha_ugit_lib',
        })

        ugit.pull_all(user='u', repository='r', isconnected=True)
        assert '/lib/aioble/core.mpy' not in self.deleted_files
        assert '/lib/aioble/__init__.mpy' not in self.deleted_files
        assert '/lib/aioble/peripheral.mpy' not in self.deleted_files
        assert '/lib/neopixel.mpy' not in self.deleted_files
        assert '/lib/ugit.py' not in self.deleted_files

    def test_unchanged_files_not_downloaded(self, monkeypatch):
        """Files with matching SHA should not be re-downloaded."""
        monkeypatch.setattr(ugit, 'pull_git_tree', lambda *a, **kw:
            make_git_tree([
                ('main.py', 'sha_same', 100),
                ('boot.py', 'sha_different', 200),
            ]))
        monkeypatch.setattr(ugit, '_build_internal_tree', lambda: {
            '/main.py': 'sha_same',
            '/boot.py': 'sha_old',
        })

        ugit.pull_all(user='u', repository='r', isconnected=True)
        assert '/main.py' not in self.pulled_files
        assert '/boot.py' in self.pulled_files

    def test_new_file_downloaded(self, monkeypatch):
        """Files in repo but not on device should be downloaded."""
        monkeypatch.setattr(ugit, 'pull_git_tree', lambda *a, **kw:
            make_git_tree([('new_file.py', 'sha_new', 100)]))
        monkeypatch.setattr(ugit, '_build_internal_tree', lambda: {})

        ugit.pull_all(user='u', repository='r', isconnected=True)
        assert '/new_file.py' in self.pulled_files

    def test_user_ignore_list_respected(self, monkeypatch):
        """Custom ignore entries with directory prefix should work."""
        monkeypatch.setattr(ugit, 'pull_git_tree', lambda *a, **kw:
            make_git_tree([('main.py', 'sha1', 100)]))
        monkeypatch.setattr(ugit, '_build_internal_tree', lambda: {
            '/main.py': 'sha1',
            '/calibration.json': 'sha_cal',
            '/data/readings.csv': 'sha_data',
        })

        ugit.pull_all(user='u', repository='r',
                      ignore=['/calibration.json', '/data'],
                      isconnected=True)
        assert '/calibration.json' not in self.deleted_files
        assert '/data/readings.csv' not in self.deleted_files

    def test_usb_cdc_skips_reset(self, monkeypatch, set_board_machine):
        """USB-CDC boards must skip machine.reset() even with reset_after=True."""
        import machine
        machine.reset = MagicMock()

        set_board_machine('ESP32S3 module with ESP32S3')
        monkeypatch.setattr(ugit, 'pull_git_tree', lambda *a, **kw:
            make_git_tree([('main.py', 'sha1', 100)]))
        monkeypatch.setattr(ugit, '_build_internal_tree', lambda: {
            '/main.py': 'sha1',
        })

        ugit.pull_all(user='u', repository='r', isconnected=True,
                      reset_after=True)
        machine.reset.assert_not_called()

    def test_non_usb_cdc_resets_when_requested(self, monkeypatch,
                                                set_board_machine):
        """Regular ESP32 boards should reset when reset_after=True."""
        import machine
        import time
        machine.reset = MagicMock()
        monkeypatch.setattr(time, 'sleep', lambda s: None)

        set_board_machine('ESP32 module with ESP32')
        monkeypatch.setattr(ugit, 'pull_git_tree', lambda *a, **kw:
            make_git_tree([('main.py', 'sha1', 100)]))
        monkeypatch.setattr(ugit, '_build_internal_tree', lambda: {
            '/main.py': 'sha1',
        })

        ugit.pull_all(user='u', repository='r', isconnected=True,
                      reset_after=True)
        machine.reset.assert_called_once()
