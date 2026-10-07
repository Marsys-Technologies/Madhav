"""Run one REVIEW on Kimi K3-256k at HIGH effort (native rule, 2026-10-01).

Execution and coding go through the stream runners at LOW effort; a review dispatched to Kimi uses this launcher,
which pins HIGH for its own start (under the shared config lock) and restores LOW afterwards.

  python3 -m pravaha_tracker.kimi_review --prompt-file P.md --cwd /path/to/checkout --out review.md
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "pravaha_tracker"

from pravaha_tracker import runner  # noqa: E402

REVIEW_MODEL = os.environ.get("PRAVAHA_KIMI_REVIEW_MODEL", "kimi-code/k3-256k")
REVIEW_EFFORT = os.environ.get("PRAVAHA_KIMI_REVIEW_EFFORT", "high")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--cwd", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=int, default=3 * 3600)
    args = ap.parse_args(argv)
    prompt = open(args.prompt_file, encoding="utf-8").read()
    with open(args.out, "w", encoding="utf-8") as out:
        proc = runner.launch_with_effort(REVIEW_MODEL, REVIEW_EFFORT, [runner.KIMI, "-m", REVIEW_MODEL, "-p", prompt],
                                         cwd=args.cwd, stdout=out, stderr=subprocess.STDOUT)
        try:
            return proc.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            return 124


if __name__ == "__main__":
    raise SystemExit(main())
