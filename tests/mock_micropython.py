"""Mock MicroPython-only modules so ugit.py can be imported on CPython.

Call install() before importing ugit. This is typically done once
in conftest.py at module level.
"""
import sys
import os
from unittest.mock import MagicMock
from collections import namedtuple

_UnameResult = namedtuple('uname_result',
    ['sysname', 'nodename', 'release', 'version', 'machine'])

# Default: generic ESP32 (not USB-CDC)
DEFAULT_MACHINE = 'ESP32 module with ESP32'

_current_machine = DEFAULT_MACHINE


def set_machine(machine_str):
    """Change the os.uname().machine value for testing."""
    global _current_machine
    _current_machine = machine_str


def reset_machine():
    """Reset os.uname().machine to the default (non-USB-CDC ESP32)."""
    global _current_machine
    _current_machine = DEFAULT_MACHINE


def fake_uname():
    return _UnameResult('micropython', 'micropython', '1.27.0',
                        '1.27.0', _current_machine)


def fake_statvfs(path):
    """Default: 4KB blocks, 1024 total blocks (4MB), 512 free (2MB)."""
    return (4096, 0, 1024, 512, 0, 0, 0, 0, 0, 0)


def install():
    """Insert mock MicroPython modules into sys.modules and patch os."""
    # urequests — MicroPython HTTP library
    sys.modules['urequests'] = MagicMock()

    # machine — hardware control (machine.reset(), etc.)
    sys.modules['machine'] = MagicMock()

    # network — WiFi connectivity
    mock_network = MagicMock()
    mock_network.STA_IF = 0
    sys.modules['network'] = mock_network

    # Always override os.uname to ensure deterministic behavior
    os.uname = fake_uname

    # Patch os.statvfs if it doesn't exist (Windows)
    if not hasattr(os, 'statvfs'):
        os.statvfs = fake_statvfs
