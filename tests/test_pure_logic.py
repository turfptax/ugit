"""Tests for pure-logic functions in ugit.

These functions have no side effects and don't touch the filesystem
or network. They are the highest-value tests for the project.
"""
import hashlib
import binascii
import ugit


class TestIsIgnored:
    """Tests for _is_ignored(path, ignore)."""

    def test_exact_match(self):
        assert ugit._is_ignored('/config.json', ['/config.json']) is True

    def test_no_match(self):
        assert ugit._is_ignored('/main.py', ['/config.json']) is False

    def test_directory_prefix_match(self):
        assert ugit._is_ignored('/lib/aioble/core.mpy', ['/lib']) is True

    def test_directory_prefix_no_false_positive(self):
        # /lib must NOT match /library/foo.py
        assert ugit._is_ignored('/library/foo.py', ['/lib']) is False

    def test_trailing_slash_in_ignore(self):
        assert ugit._is_ignored('/lib/foo.py', ['/lib/']) is True

    def test_empty_ignore_list(self):
        assert ugit._is_ignored('/anything.py', []) is False

    def test_root_path_exact(self):
        assert ugit._is_ignored('/ugit.py', ['/ugit.py']) is True

    def test_multiple_ignore_entries(self):
        ignore = ['/config.json', '/lib', '/data']
        assert ugit._is_ignored('/data/sensor.log', ignore) is True
        assert ugit._is_ignored('/main.py', ignore) is False

    def test_nested_directory_match(self):
        assert ugit._is_ignored('/lib/aioble/__init__.mpy', ['/lib']) is True

    def test_similar_prefix_no_match(self):
        # /lib should not match /lib2/foo.py
        assert ugit._is_ignored('/lib2/foo.py', ['/lib']) is False


class TestGitBlobHash:
    """Tests for _git_blob_hash(data).

    Must match GitHub's blob SHA1: sha1('blob {size}\\0{content}')
    """

    def test_empty_content(self):
        # GitHub's known SHA1 for empty blob
        assert ugit._git_blob_hash(b'') == 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391'

    def test_known_content(self):
        data = b'hello world\n'
        header = b'blob %d\x00' % len(data)
        expected = binascii.hexlify(
            hashlib.sha1(header + data).digest()
        ).decode()
        assert ugit._git_blob_hash(data) == expected

    def test_string_input_matches_bytes(self):
        result_str = ugit._git_blob_hash('test')
        result_bytes = ugit._git_blob_hash(b'test')
        assert result_str == result_bytes

    def test_binary_content(self):
        data = bytes(range(256))
        result = ugit._git_blob_hash(data)
        assert len(result) == 40
        assert all(c in '0123456789abcdef' for c in result)


class TestFmtSize:
    """Tests for _fmt_size(b)."""

    def test_zero(self):
        assert ugit._fmt_size(0) == '0 B'

    def test_bytes_range(self):
        assert ugit._fmt_size(512) == '512 B'
        assert ugit._fmt_size(1023) == '1023 B'

    def test_kilobytes(self):
        assert ugit._fmt_size(1024) == '1 KB'
        assert ugit._fmt_size(2048) == '2 KB'

    def test_megabytes(self):
        assert ugit._fmt_size(1024 * 1024) == '1.0 MB'
        assert ugit._fmt_size(2 * 1024 * 1024) == '2.0 MB'


class TestEnsureIgnore:
    """Tests for _ensure_ignore(ignore)."""

    def test_none_input(self):
        result = ugit._ensure_ignore(None)
        assert '/ugit.py' in result
        assert '/config.json' in result
        assert '/ugit.backup' in result
        assert '/ugit_log.txt' in result
        assert '/lib' in result

    def test_empty_list(self):
        result = ugit._ensure_ignore([])
        assert len(result) == 5  # 5 protected entries

    def test_preserves_user_entries(self):
        result = ugit._ensure_ignore(['/my_data.json'])
        assert '/my_data.json' in result
        assert '/ugit.py' in result

    def test_no_duplicates(self):
        result = ugit._ensure_ignore(['/ugit.py', '/lib'])
        assert result.count('/ugit.py') == 1
        assert result.count('/lib') == 1

    def test_all_protected_files_present(self):
        result = ugit._ensure_ignore([])
        expected = {'/ugit.py', '/config.json', '/ugit.backup', '/ugit_log.txt', '/lib'}
        assert expected == set(result)


class TestHeaders:
    """Tests for _headers(token)."""

    def test_no_token(self):
        h = ugit._headers()
        assert h['User-Agent'] == 'ugit-turfptax'
        assert 'authorization' not in h

    def test_empty_token(self):
        h = ugit._headers('')
        assert 'authorization' not in h

    def test_with_token(self):
        h = ugit._headers('ghp_abc123')
        assert h['authorization'] == 'bearer ghp_abc123'
        assert h['User-Agent'] == 'ugit-turfptax'


class TestRepoDownloadSize:
    """Tests for _repo_download_size(git_tree, local_tree, ignore)."""

    def test_all_new_files(self):
        git_tree = {'tree': [
            {'path': 'main.py', 'type': 'blob', 'sha': 'aaa', 'size': 100},
            {'path': 'boot.py', 'type': 'blob', 'sha': 'bbb', 'size': 200},
        ]}
        assert ugit._repo_download_size(git_tree, {}, []) == 300

    def test_unchanged_files_not_counted(self):
        git_tree = {'tree': [
            {'path': 'main.py', 'type': 'blob', 'sha': 'aaa', 'size': 100},
        ]}
        local_tree = {'/main.py': 'aaa'}
        assert ugit._repo_download_size(git_tree, local_tree, []) == 0

    def test_changed_files_counted(self):
        git_tree = {'tree': [
            {'path': 'main.py', 'type': 'blob', 'sha': 'aaa', 'size': 100},
        ]}
        local_tree = {'/main.py': 'old_sha'}
        assert ugit._repo_download_size(git_tree, local_tree, []) == 100

    def test_ignored_files_not_counted(self):
        git_tree = {'tree': [
            {'path': 'ugit.py', 'type': 'blob', 'sha': 'aaa', 'size': 500},
            {'path': 'main.py', 'type': 'blob', 'sha': 'bbb', 'size': 100},
        ]}
        assert ugit._repo_download_size(git_tree, {}, ['/ugit.py']) == 100

    def test_tree_entries_skipped(self):
        git_tree = {'tree': [
            {'path': 'src', 'type': 'tree'},
            {'path': 'src/main.py', 'type': 'blob', 'sha': 'aaa', 'size': 100},
        ]}
        assert ugit._repo_download_size(git_tree, {}, []) == 100

    def test_path_normalization(self):
        # git paths lack leading '/', local_tree has them
        git_tree = {'tree': [
            {'path': 'main.py', 'type': 'blob', 'sha': 'aaa', 'size': 100},
        ]}
        local_tree = {'/main.py': 'aaa'}
        assert ugit._repo_download_size(git_tree, local_tree, []) == 0


class TestIsUsbCdc:
    """Tests for _is_usb_cdc() board detection."""

    def test_esp32s3_detected(self, set_board_machine):
        set_board_machine('ESP32S3 module with ESP32S3')
        assert ugit._is_usb_cdc() is True

    def test_esp32s3_spiram(self, set_board_machine):
        set_board_machine('Generic ESP32S3 module with Octal-SPIRAM with ESP32S3')
        assert ugit._is_usb_cdc() is True

    def test_esp32s2_detected(self, set_board_machine):
        set_board_machine('ESP32S2 module with ESP32S2')
        assert ugit._is_usb_cdc() is True

    def test_esp32c3_detected(self, set_board_machine):
        set_board_machine('ESP32C3 module with ESP32C3')
        assert ugit._is_usb_cdc() is True

    def test_esp32c6_detected(self, set_board_machine):
        set_board_machine('ESP32C6 module with ESP32C6')
        assert ugit._is_usb_cdc() is True

    def test_regular_esp32_not_detected(self, set_board_machine):
        set_board_machine('ESP32 module with ESP32')
        assert ugit._is_usb_cdc() is False

    def test_rp2040_not_detected(self, set_board_machine):
        set_board_machine('Raspberry Pi Pico W with RP2040')
        assert ugit._is_usb_cdc() is False
