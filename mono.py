#!/usr/bin/env python3
"""
Monochrome CLI launcher script.
"""
import sys
from pathlib import Path

# Add repository root to sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from monochrome_cli.main import cli_entrypoint

if __name__ == "__main__":
    cli_entrypoint()
