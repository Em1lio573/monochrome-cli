"""
Platform detection and path utilities for Termux and Linux.
"""
import os
import sys
from pathlib import Path


def is_termux() -> bool:
    return (
        'TERMUX_VERSION' in os.environ
        or os.path.exists('/data/data/com.termux')
        or 'com.termux' in os.environ.get('PREFIX', '')
    )


def is_android() -> bool:
    return is_termux() or os.path.exists('/sdcard')


def get_default_music_dir() -> Path:
    # 1. Check Termux shared storage
    termux_shared = Path(os.path.expanduser('~/storage/shared/Music'))
    if termux_shared.exists() and os.access(termux_shared, os.W_OK):
        return termux_shared

    # 2. Check direct /sdcard/Music
    sdcard_music = Path('/sdcard/Music')
    if sdcard_music.exists() and os.access(sdcard_music, os.W_OK):
        return sdcard_music

    # 3. Standard Linux / macOS ~/Music
    user_music = Path(os.path.expanduser('~/Music/Monochrome'))
    return user_music


def get_config_dir() -> Path:
    if is_termux():
        base = Path(os.path.expanduser('~/.config/monochrome-cli'))
    elif sys.platform == 'win32':
        appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
        base = Path(appdata) / 'monochrome-cli'
    else:
        base = Path(os.path.expanduser('~/.config/monochrome-cli'))
    base.mkdir(parents=True, exist_ok=True)
    return base
