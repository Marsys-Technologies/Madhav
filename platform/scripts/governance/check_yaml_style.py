#!/usr/bin/env python3
"""Apply strict style to tracked YAML, preserving exact historical artifacts."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    config_path = root / ".github/yaml-style-exceptions.json"
    exceptions = json.loads(config_path.read_text(encoding="utf-8"))["entries"]
    tracked = subprocess.check_output(
        ["git", "ls-files", "-z", "--", "*.yaml", "*.yml"], cwd=root
    )
    lint_paths = []
    preserved = 0
    for name in filter(None, tracked.split(b"\0")):
        path = os.fsdecode(name)
        exception = exceptions.get(path)
        if exception and hashlib.sha256((root / path).read_bytes()).hexdigest() == exception["sha256"]:
            preserved += 1
            continue
        lint_paths.append(path)

    print(f"YAML style: {len(lint_paths)} tracked files, {preserved} exact revisions preserved", flush=True)
    if not lint_paths:
        return 0
    return subprocess.run(["yamllint", "--strict", "--", *lint_paths], cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
