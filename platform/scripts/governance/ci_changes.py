#!/usr/bin/env python3
"""ci_changes.py: classify a pull request as DOCS-ONLY or not, so ci.yml can skip its heavy jobs for a change that cannot affect them.

  python3 ci_changes.py --event pull_request --base HEAD^1 --head HEAD     prints `docs_only=true|false` (always exit 0)
  python3 ci_changes.py --files a.md b/c.py                                 classify a given file list (tests)

FAIL-CLOSED: `docs_only=true` is printed ONLY for a pull_request event with a non-empty changed-file list in which EVERY file (old and new
name of a rename, deleted files included: `--no-renames`) is a documentation/evidence file. An error, an empty list, an unreadable diff,
a push / merge_group / workflow_dispatch event all print `docs_only=false`, so every job runs. Post-merge runs on main and the merge queue
always run everything.

A DOCS file: `*.md` or `*.txt`, or any file under `00_ARCHITECTURE/briefs/` or `99_ARCHIVE/`, EXCEPT anything with a code/data/config
extension, anything under `.github/`, `platform/`, `services/`, `00_ARCHITECTURE/control/`, any `__tests__` / `tests` directory, and the
manifest/registry files the governance tests read. The tests read data files (json, jsonl, yaml) and files next to code, so those never skip.
"""
from __future__ import annotations

import argparse
import posixpath
import subprocess
import sys

DOC_EXT = (".md", ".txt")
DOC_TREES = ("00_ARCHITECTURE/briefs/", "99_ARCHIVE/")
CODE_EXT = (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".sql", ".yml", ".yaml", ".json", ".jsonl", ".sh", ".toml", ".lock", ".cfg",
            ".ini", ".css", ".scss", ".html", ".svg", ".ipynb", ".tf", ".env", ".csv", ".parquet", ".sqlite", ".db")
DENY_PREFIX = (".github/", "platform/", "services/", "00_ARCHITECTURE/control/", "00_ARCHITECTURE/autonomy/")
DENY_NAMES = ("CAPABILITY_MANIFEST.json", "package.json", "package-lock.json", "pnpm-lock.yaml", "Dockerfile", "Makefile")
DENY_DIRS = ("__tests__", "tests", "test", "fixtures", "migrations", "node_modules")


def is_doc(path: str) -> bool:
    raw = path.strip().replace("\\", "/")
    if ".." in raw.split("/") or "." in raw.split("/") or raw.startswith("/"):
        return False                                     # git never reports these: anything odd is not a docs file
    p = posixpath.normpath(raw)
    if not p or p == ".":
        return False
    low = p.lower()
    if low.endswith(CODE_EXT) or posixpath.basename(p) in DENY_NAMES:
        return False
    if any(p.startswith(d) for d in DENY_PREFIX) or any(seg in DENY_DIRS for seg in p.split("/")[:-1]):
        return False
    return low.endswith(DOC_EXT) or any(p.startswith(t) for t in DOC_TREES)


def docs_only(files: list[str]) -> bool:
    files = [f for f in (x.strip() for x in files) if f]
    return bool(files) and all(is_doc(f) for f in files)


def changed_files(base: str, head: str) -> list[str] | None:
    try:
        out = subprocess.run(["git", "diff", "--name-only", "--no-renames", "-z", base, head], capture_output=True, timeout=120, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return [f for f in out.decode("utf-8", "surrogateescape").split("\0") if f]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--event", default="pull_request")
    ap.add_argument("--base", default="HEAD^1")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--files", nargs="*")
    a = ap.parse_args(argv)
    try:
        if a.files is not None:
            res = docs_only(a.files)
        elif a.event != "pull_request":
            res = False
        else:
            files = changed_files(a.base, a.head)
            res = files is not None and docs_only(files)
    except Exception:                                    # noqa: BLE001 - fail closed: anything unexpected means "run everything"
        res = False
    print(f"docs_only={'true' if res else 'false'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
