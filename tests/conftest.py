"""Pytest configuration for ugit tests.

Installs MicroPython mocks before ugit is imported, then provides
the ugit module and common fixtures to all test files.
"""
import sys
import os
import pytest

# Ensure tests/ is on sys.path so mock_micropython can be imported
sys.path.insert(0, os.path.dirname(__file__))

# Install mocks BEFORE any test imports ugit
from mock_micropython import install, set_machine, reset_machine
install()

# Now safe to import on CPython
import ugit


@pytest.fixture
def ugit_module():
    """Provide the ugit module with clean state between tests."""
    reset_machine()
    return ugit


@pytest.fixture
def mock_filesystem(tmp_path, monkeypatch):
    """Redirect ugit config operations to a temp directory.

    Monkeypatches _CONFIG_PATH so create_config() / _load_config()
    read and write inside tmp_path instead of the real filesystem.
    """
    config_path = str(tmp_path / 'config.json')
    monkeypatch.setattr(ugit, '_CONFIG_PATH', config_path)

    class FS:
        root = tmp_path
        config = config_path

        @staticmethod
        def write(relpath, content):
            p = tmp_path / relpath.lstrip('/')
            p.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                p.write_bytes(content)
            else:
                p.write_text(content, encoding='utf-8')
            return str(p)

        @staticmethod
        def read(relpath):
            p = tmp_path / relpath.lstrip('/')
            return p.read_text(encoding='utf-8')

    return FS()


@pytest.fixture
def set_board_machine():
    """Fixture to control os.uname().machine for USB-CDC tests."""
    def _set(machine_str):
        set_machine(machine_str)
    yield _set
    reset_machine()
