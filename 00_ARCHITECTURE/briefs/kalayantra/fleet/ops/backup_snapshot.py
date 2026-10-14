#!/usr/bin/env python3
"""Executor adapter; default dry-run; no import-time effects."""
from common import main

if __name__ == "__main__":
    raise SystemExit(main('backup_snapshot'))
