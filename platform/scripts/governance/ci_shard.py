#!/usr/bin/env python3
"""ci_shard.py: deterministic, complete, disjoint partition of the governance test files across CI shards.

The `Governance Tool Tests (pytest)` job outgrew its 10-minute ceiling as the Nikaṣa suites grew (median ~8.5 min, max ~10 min on main).
It now runs as K parallel shard jobs (test steps only) plus an aggregate job that keeps the ORIGINAL job name, so the required check and
every `ci_job_passed` plan detector that names it keep meaning "the whole governance test directory passed".

  python3 ci_shard.py --index I --count K     print the test files of shard I (1-based), one per line
  python3 ci_shard.py --count K --verify      fail unless the K shards together are exactly every test file, each once

Assignment: every `test_*.py` / `*_test.py` under `__tests__/` (the files pytest would collect), largest file first (a size proxy for run
time; ties by path), each placed on the currently lightest shard (ties: lowest index). Pure function of the tree: no timings, no randomness,
so a shard's content does not move between runs. A new test file lands in some shard automatically; nothing is listed by hand.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent / "__tests__"


def test_files(root: Path = TESTS) -> list[Path]:
    """Exactly what pytest's default collection takes from the directory (test_*.py, *_test.py), by repo-relative sorted path."""
    found = {p for pat in ("test_*.py", "*_test.py") for p in root.rglob(pat) if p.is_file()}
    return sorted(found, key=lambda p: p.as_posix())


def partition(files: list[Path], count: int) -> list[list[Path]]:
    if count < 1:
        raise ValueError("count must be >= 1")
    shards: list[list[Path]] = [[] for _ in range(count)]
    load = [0] * count
    for f in sorted(files, key=lambda p: (-p.stat().st_size, p.as_posix())):
        i = min(range(count), key=lambda k: (load[k], k))
        shards[i].append(f)
        load[i] += f.stat().st_size
    return [sorted(s, key=lambda p: p.as_posix()) for s in shards]


def verify(files: list[Path], shards: list[list[Path]]) -> list[str]:
    flat = [f for s in shards for f in s]
    problems = []
    if len(flat) != len(set(flat)):
        problems.append("a test file is in more than one shard: " + ", ".join(sorted({f.as_posix() for f in flat if flat.count(f) > 1})))
    missing = set(files) - set(flat)
    if missing:
        problems.append("test files in no shard: " + ", ".join(sorted(f.as_posix() for f in missing)))
    extra = set(flat) - set(files)
    if extra:
        problems.append("shard files that are not test files: " + ", ".join(sorted(f.as_posix() for f in extra)))
    empty = [i + 1 for i, s in enumerate(shards) if not s]
    if empty:
        problems.append(f"empty shard(s): {empty}")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--index", type=int, help="1-based shard index to print")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--root", type=Path, default=TESTS)
    a = ap.parse_args(argv)
    files = test_files(a.root)
    shards = partition(files, a.count)
    if a.verify:
        probs = verify(files, shards)
        for p in probs:
            print(f"ci_shard: {p}", file=sys.stderr)
        print(f"ci_shard: {len(files)} test files in {a.count} shards: " + ", ".join(str(len(s)) for s in shards) + (" OK" if not probs else " FAIL"))
        return 1 if probs else 0
    if a.index is None or not 1 <= a.index <= a.count:
        print("ci_shard: --index must be between 1 and --count", file=sys.stderr)
        return 2
    base = a.root.parent.parent.parent.parent if a.root == TESTS else Path.cwd()
    for f in shards[a.index - 1]:
        try:
            print(f.relative_to(base).as_posix())
        except ValueError:
            print(f.as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
