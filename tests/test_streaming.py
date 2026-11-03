"""Tests for the chunked (low-memory) hashing, download and backup paths.

On small MCUs a whole-file read() can fail with ENOMEM, so these paths must
work in fixed-size chunks. Files here are deliberately larger than the chunk
size and include multi-byte UTF-8 characters that straddle chunk boundaries.
"""
import io
import hashlib
import binascii
import pytest
import ugit


def _git_sha(data):
    return hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()


class TestLocalFileHash:

    @pytest.mark.parametrize('size', [0, 1, 511, 512, 513, 5000])
    def test_matches_git_blob_hash(self, tmp_path, size):
        data = bytes(range(256)) * (size // 256 + 1)
        data = data[:size]
        p = tmp_path / 'f.bin'
        p.write_bytes(data)
        assert ugit._local_file_hash(str(p)) == _git_sha(data)

    def test_missing_file_hashes_as_empty(self, tmp_path):
        assert ugit._local_file_hash(str(tmp_path / 'nope')) == _git_sha(b'')


class _FakeResponse:
    def __init__(self, body, status=200):
        self.status_code = status
        self.raw = io.BytesIO(body)
        self.closed = False

    def close(self):
        self.closed = True


class TestPull:

    def test_streams_to_file(self, tmp_path, monkeypatch):
        body = b'x' * 5000 + b'end'
        resp = _FakeResponse(body)
        monkeypatch.setattr(ugit.urequests, 'get', lambda *a, **k: resp,
                            raising=False)
        dest = tmp_path / 'sub' / 'main.py'
        n = ugit.pull(str(dest), 'http://example/main.py')
        assert n == len(body)
        assert dest.read_bytes() == body
        assert resp.closed
        assert not (tmp_path / 'sub' / 'main.py.ugit_tmp').exists()

    def test_replaces_existing_file(self, tmp_path, monkeypatch):
        dest = tmp_path / 'main.py'
        dest.write_bytes(b'old')
        monkeypatch.setattr(ugit.urequests, 'get',
                            lambda *a, **k: _FakeResponse(b'new'),
                            raising=False)
        ugit.pull(str(dest), 'http://example/main.py')
        assert dest.read_bytes() == b'new'

    def test_http_error_keeps_existing_file(self, tmp_path, monkeypatch):
        dest = tmp_path / 'main.py'
        dest.write_bytes(b'old')
        resp = _FakeResponse(b'404: Not Found', status=404)
        monkeypatch.setattr(ugit.urequests, 'get', lambda *a, **k: resp,
                            raising=False)
        with pytest.raises(Exception):
            ugit.pull(str(dest), 'http://example/main.py')
        assert dest.read_bytes() == b'old'
        assert resp.closed
        assert not (tmp_path / 'main.py.ugit_tmp').exists()

    def test_failed_download_keeps_existing_file(self, tmp_path, monkeypatch):
        class Boom(_FakeResponse):
            def __init__(self):
                super().__init__(b'')
                self.raw = self

            def readinto(self, buf):
                raise OSError(12)

        dest = tmp_path / 'main.py'
        dest.write_bytes(b'old')
        monkeypatch.setattr(ugit.urequests, 'get', lambda *a, **k: Boom(),
                            raising=False)
        with pytest.raises(OSError):
            ugit.pull(str(dest), 'http://example/main.py')
        assert dest.read_bytes() == b'old'
        assert not (tmp_path / 'main.py.ugit_tmp').exists()


class TestCopyUtf8:

    def test_multibyte_across_chunk_boundary(self):
        # offset by one byte so 3-byte characters straddle every boundary
        text = 'a' + '日本語ランタン' * 300
        dst = io.StringIO()
        ugit._copy_utf8(io.BytesIO(text.encode('utf-8')), dst)
        assert dst.getvalue() == text

    def test_invalid_utf8_raises(self):
        with pytest.raises(ValueError):
            ugit._copy_utf8(io.BytesIO(b'ok\xff\xfe' * 300), io.StringIO())

    def test_truncated_utf8_at_eof_raises(self):
        with pytest.raises(ValueError):
            ugit._copy_utf8(io.BytesIO('日'.encode('utf-8')[:2]),
                            io.StringIO())


class TestBackupRoundTrip:

    def test_backup_then_restore(self, tmp_path, monkeypatch):
        text = 'a' + '日本語\n' * 400
        files = {
            'main.py': text.encode('utf-8'),
            'empty.txt': b'',
            'blob.bin': bytes(range(256)) * 10,
        }
        local_tree = {}
        for name, data in files.items():
            p = tmp_path / name
            p.write_bytes(data)
            local_tree['/' + name] = _git_sha(data)
        # backup() writes with absolute /name paths; map them into tmp_path
        backup_path = str(tmp_path / 'ugit.backup')
        original_open = open

        def patched_open(path, mode='r', *a, **kw):
            path = str(path)
            if path == '/ugit.backup':
                return original_open(backup_path, mode, *a, **kw)
            if path.startswith('/') and not path.startswith(str(tmp_path)):
                return original_open(str(tmp_path) + path, mode, *a, **kw)
            return original_open(path, mode, *a, **kw)

        monkeypatch.setattr(ugit, '_build_internal_tree', lambda: local_tree)
        monkeypatch.setattr(ugit, '_ensure_ignore', lambda ign: ign or [])
        monkeypatch.setattr(ugit, '_get_storage_info',
                            lambda: (10**7, 10**7, 0))
        monkeypatch.setattr(ugit, '_file_size',
                            lambda p: len(files[p.lstrip('/')]))
        monkeypatch.setattr('builtins.open', patched_open)

        assert ugit.backup() == 3

        restored = {}
        monkeypatch.setattr(ugit, '_restore_file',
                            lambda path, content: restored.update(
                                {path: content}))
        assert ugit.restore() is True

        assert restored['/main.py'] == text
        # binary files are skipped, not written as partial garbage
        assert '/blob.bin' not in restored
