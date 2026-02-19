"""Tests for backup format and restore parsing.

The restore() parser is safety-critical: a bug here means corrupted
restores. We test it by writing known backup content to tmp_path
and verifying restore reads it correctly.
"""
import pytest
from unittest.mock import MagicMock
import ugit


class TestRestoreParser:
    """Test the restore() function's backup file parsing."""

    def _setup_restore(self, tmp_path, monkeypatch, backup_content,
                       ignore=None):
        """Write backup file, mock open() to redirect, capture restores."""
        backup_path = str(tmp_path / 'ugit.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(backup_content)

        restored_files = []

        def fake_restore_file(filepath, content):
            restored_files.append((filepath, content))

        monkeypatch.setattr(ugit, '_restore_file', fake_restore_file)
        monkeypatch.setattr(ugit, '_ensure_ignore',
                            lambda ign: ign if ign else [])

        original_open = open

        def patched_open(path, mode='r', *a, **kw):
            if 'ugit.backup' in str(path):
                return original_open(backup_path, mode, *a, **kw)
            return original_open(path, mode, *a, **kw)

        monkeypatch.setattr('builtins.open', patched_open)
        return restored_files

    def test_single_file(self, tmp_path, monkeypatch):
        content = (
            'ugit backup v2\n'
            'FILE:/main.py SHA:abc123\n'
            '---\n'
            'print("hello")\n'
            '---\n'
        )
        restored = self._setup_restore(tmp_path, monkeypatch, content)
        result = ugit.restore(ignore=[])

        assert result is True
        assert len(restored) == 1
        assert restored[0] == ('/main.py', 'print("hello")')

    def test_multiline_file(self, tmp_path, monkeypatch):
        content = (
            'ugit backup v2\n'
            'FILE:/boot.py SHA:def456\n'
            '---\n'
            'import ugit\n'
            'ugit.pull_all()\n'
            '---\n'
        )
        restored = self._setup_restore(tmp_path, monkeypatch, content)
        result = ugit.restore(ignore=[])

        assert result is True
        assert restored[0][1] == 'import ugit\nugit.pull_all()'

    def test_multiple_files(self, tmp_path, monkeypatch):
        content = (
            'ugit backup v2\n'
            'FILE:/main.py SHA:aaa\n'
            '---\n'
            'main code\n'
            '---\n'
            'FILE:/boot.py SHA:bbb\n'
            '---\n'
            'boot code\n'
            '---\n'
        )
        restored = self._setup_restore(tmp_path, monkeypatch, content)
        result = ugit.restore(ignore=[])

        assert result is True
        assert len(restored) == 2
        assert restored[0] == ('/main.py', 'main code')
        assert restored[1] == ('/boot.py', 'boot code')

    def test_skips_binary(self, tmp_path, monkeypatch):
        content = (
            'ugit backup v2\n'
            'FILE:/lib/mod.mpy SHA:abc\n'
            '---BINARY:1024---\n'
            'FILE:/main.py SHA:def\n'
            '---\n'
            'code\n'
            '---\n'
        )
        restored = self._setup_restore(tmp_path, monkeypatch, content)
        result = ugit.restore(ignore=[])

        assert result is True
        assert len(restored) == 1
        assert restored[0][0] == '/main.py'

    def test_invalid_format_returns_false(self, tmp_path, monkeypatch):
        content = 'not a backup file\n'
        self._setup_restore(tmp_path, monkeypatch, content)
        result = ugit.restore(ignore=[])
        assert result is False

    def test_missing_backup_returns_false(self, monkeypatch):
        def fail_open(path, mode='r', *a, **kw):
            if 'ugit.backup' in str(path):
                raise OSError('No such file')
            return open(path, mode, *a, **kw)

        monkeypatch.setattr('builtins.open', fail_open)
        result = ugit.restore(ignore=[])
        assert result is False

    def test_respects_ignore_list(self, tmp_path, monkeypatch):
        content = (
            'ugit backup v2\n'
            'FILE:/config.json SHA:aaa\n'
            '---\n'
            'secret\n'
            '---\n'
            'FILE:/main.py SHA:bbb\n'
            '---\n'
            'code\n'
            '---\n'
        )
        # Don't use _setup_restore since we need custom _ensure_ignore
        backup_path = str(tmp_path / 'ugit.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)

        restored_files = []

        def fake_restore_file(filepath, content):
            restored_files.append((filepath, content))

        monkeypatch.setattr(ugit, '_restore_file', fake_restore_file)
        # Return a real ignore list with /config.json
        monkeypatch.setattr(ugit, '_ensure_ignore',
                            lambda ign: ['/config.json'])

        original_open = open

        def patched_open(path, mode='r', *a, **kw):
            if 'ugit.backup' in str(path):
                return original_open(backup_path, mode, *a, **kw)
            return original_open(path, mode, *a, **kw)

        monkeypatch.setattr('builtins.open', patched_open)

        result = ugit.restore(ignore=['/config.json'])
        assert result is True
        # config.json should be skipped, only main.py restored
        assert len(restored_files) == 1
        assert restored_files[0][0] == '/main.py'
