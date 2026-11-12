#!/usr/bin/env python3
"""Apply strict style to every tracked YAML file."""
import os
from pathlib import Path
import subprocess


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    tracked = subprocess.check_output(
        ["git", "ls-files", "-z", "--", "*.yaml", "*.yml"], cwd=root
    )
    lint_paths = [os.fsdecode(name) for name in tracked.split(b"\0") if name]
    print(f"YAML style: {len(lint_paths)} tracked files", flush=True)
    if not lint_paths:
        return 0
    return subprocess.run(["yamllint", "--strict", "--", *lint_paths], cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
