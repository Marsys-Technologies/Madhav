#!/usr/bin/env python3
"""verify_cutover.py -- E4.3 ledger cut-over verifier (read-only; no DB, no network, no writes).

CUTOVER.json (next to this file) records, for the three cut-over artifacts (asset_gaps.jsonl,
asset_certs.jsonl, NIKASHA_CHANGE_REGISTER_v2_0.md), the line count, byte count and md5 they have at the cut
commit (`cut_sha`, a commit of origin/campaign/nikasha-test). This script recomputes those numbers

  (a) from the working tree, and compares them with what CUTOVER.json recorded; and
  (b) from `git show <cut_sha>:<path>`, when the cut commit is reachable in the repository, and compares
      them with the working tree.

Two modes:
  exact   (default)  every file's WHOLE content must equal the cut: lines, bytes and md5. This is the cut-over
                     check itself, run once at the merge of the ledger PR.
  prefix             the two ledgers are append-only, so after the cut-over their first `bytes` bytes must still
                     equal the cut (a historical row was not rewritten) while later rows are allowed. The register
                     is not append-only: it is not checked in this mode (the report says so).

Exit codes (the verdict is never PASS unless every comparison that exists was made and agreed):
  0  verified: recorded values agree with the working tree AND with git show <cut_sha>
  1  MISMATCH or unreadable: a file is missing, or any number/md5 differs
  4  NO_DETECTOR: the working tree agrees with the record but the cut commit is not reachable here, so the
     git-side comparison could not be made. This is a non-zero, non-passing result by design -- a check that
     could not run must not read as green (CLAUDE.md section N.8).
  2  usage error (bad CUTOVER.json)

Usage:  python3 00_ARCHITECTURE/control/E4.3/verify_cutover.py [--mode exact|prefix] [--root DIR] [--git-repo DIR]
        [--cutover PATH] [--no-git]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parents[2]
DEFAULT_CUTOVER = HERE / "CUTOVER.json"

EXIT_OK, EXIT_MISMATCH, EXIT_USAGE, EXIT_NO_DETECTOR = 0, 1, 2, 4
PLACEHOLDER = "FILLED_AFTER_MERGE"


def measure(data: bytes) -> dict:
    """Line count (newline bytes, i.e. `wc -l`), byte count and md5 of `data`."""
    return {"lines": data.count(b"\n"), "bytes": len(data), "md5": hashlib.md5(data).hexdigest()}


def cut_reachable(git_repo: pathlib.Path, cut_sha: str) -> bool:
    try:
        r = subprocess.run(["git", "-C", str(git_repo), "cat-file", "-e", f"{cut_sha}^{{commit}}"],
                           capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False
    return r.returncode == 0


def git_show(git_repo: pathlib.Path, cut_sha: str, rel: str) -> bytes | None:
    try:
        r = subprocess.run(["git", "-C", str(git_repo), "show", f"{cut_sha}:{rel}"], capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def verify(root: pathlib.Path, cutover: dict, mode: str = "exact", git_repo: pathlib.Path | None = None,
           use_git: bool = True) -> tuple[int, list[str]]:
    """Return (exit_code, report_lines). Pure function of the inputs; never writes."""
    if mode not in ("exact", "prefix"):
        return EXIT_USAGE, [f"unknown mode {mode!r}"]
    cut_sha = cutover.get("cut_sha")
    files = cutover.get("files")
    if not (isinstance(cut_sha, str) and len(cut_sha) == 40) or not isinstance(files, dict) or not files:
        return EXIT_USAGE, ["CUTOVER.json lacks a 40-hex cut_sha or a non-empty files map"]
    git_repo = git_repo or root
    report: list[str] = []
    bad = False
    reachable = use_git and cut_reachable(git_repo, cut_sha)

    for rel, rec in sorted(files.items()):
        append_only = bool(rec.get("append_only"))
        if mode == "prefix" and not append_only:
            report.append(f"SKIP  {rel}: not append-only, checked in exact mode only")
            continue
        p = root / rel
        try:
            wt = p.read_bytes()
        except OSError as exc:
            report.append(f"FAIL  {rel}: unreadable in the working tree ({exc.__class__.__name__})")
            bad = True
            continue
        n = rec["old_bytes"]
        view = wt[:n] if mode == "prefix" else wt        # prefix: compare only the bytes that existed at the cut
        got = measure(view)
        want = {"lines": rec["old_lines"], "bytes": rec["old_bytes"], "md5": rec["old_md5"]}
        if mode == "prefix" and len(wt) < n:
            report.append(f"FAIL  {rel}: working tree is SHORTER ({len(wt)} B) than the cut ({n} B): rows removed")
            bad = True
            continue
        if got != want:
            report.append(f"FAIL  {rel}: working tree {got} != recorded cut {want}")
            bad = True
            continue
        report.append(f"ok    {rel}: working tree ({mode}) == recorded cut ({got['lines']} lines, {got['md5']})")
        if reachable:
            blob = git_show(git_repo, cut_sha, rel)
            if blob is None:
                report.append(f"FAIL  {rel}: not present at {cut_sha[:9]} (git show failed)")
                bad = True
            elif measure(blob) != measure(view):
                report.append(f"FAIL  {rel}: working tree ({mode}) {measure(view)} != git show {cut_sha[:9]} {measure(blob)}")
                bad = True
            else:
                report.append(f"ok    {rel}: working tree ({mode}) == git show {cut_sha[:9]}")

    if bad:
        return EXIT_MISMATCH, report
    if not reachable:
        report.append(f"NO_DETECTOR: cut commit {cut_sha[:9]} is not reachable in {git_repo}"
                      f"{' (git disabled)' if not use_git else ''}; only the working-tree-vs-record comparison "
                      "was made, which is not a verification of the cut. Not a pass.")
        return EXIT_NO_DETECTOR, report
    if cutover.get("main_sha") == PLACEHOLDER:
        report.append(f"note  main_sha is still {PLACEHOLDER}: fill it after the merge")
    return EXIT_OK, report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mode", choices=("exact", "prefix"), default="exact")
    ap.add_argument("--root", type=pathlib.Path, default=DEFAULT_ROOT, help="repo root holding the working-tree files")
    ap.add_argument("--git-repo", type=pathlib.Path, default=None, help="repo to read the cut commit from (default: --root)")
    ap.add_argument("--cutover", type=pathlib.Path, default=DEFAULT_CUTOVER)
    ap.add_argument("--no-git", action="store_true", help="skip the git-side comparison (result is then NO_DETECTOR)")
    a = ap.parse_args(argv)
    try:
        cutover = json.loads(a.cutover.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"verify_cutover: cannot read {a.cutover}: {exc}", file=sys.stderr)
        return EXIT_USAGE
    code, report = verify(a.root, cutover, a.mode, a.git_repo, use_git=not a.no_git)
    print("\n".join(report))
    print(f"verify_cutover: {'VERIFIED' if code == EXIT_OK else 'NO_DETECTOR' if code == EXIT_NO_DETECTOR else 'MISMATCH' if code == EXIT_MISMATCH else 'USAGE'}"
          f" (exit {code}, mode {a.mode})")
    return code


if __name__ == "__main__":
    sys.exit(main())
