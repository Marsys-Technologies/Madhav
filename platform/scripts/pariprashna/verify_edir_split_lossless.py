#!/usr/bin/env python3
"""Prove the EDIR_V3_REGISTER A5 split (2026-08-29) is lossless.

Context
-------
Six concurrent overnight streams (S1-S6) were all appending finding entries
to the single, shared `EDIR_V3_REGISTER_v1_0.md`'s §4. That produced
repeated git merge conflicts and at least one self-caught near-miss where an
in-progress edit silently deleted an entry header. The fix (this lane,
pariprashna/v3-a5-edir-split) splits the file into:

  - EDIR_V3_REGISTER_v1_0.md            (INDEX: §0-§3 unchanged, §4 -> a
                                          pointer, new §4a -> six per-stream
                                          files)
  - EDIR_V3_REGISTER_ARCHIVE_PRECONVERGENCE_v1_0.md
                                         (frozen, verbatim copy of the OLD
                                          §4 onward)
  - EDIR_V3_REGISTER_S1_v1_0.md .. S6_v1_0.md
                                         (new, empty-at-split per-stream
                                          live files)

This script is the "provably lossless" detector for that split, run against
a real git ref rather than trusted by assertion (CLAUDE.md §N.8: a signal
without a real detector behind it is null, not green). It does NOT trust
that the split was done correctly — it independently re-derives what the
pre-split file's §4 onward and §0-§3 head SHOULD look like from git history,
and diffs that against what actually landed on disk.

Checks performed
-----------------
1. §4-onward byte-for-byte equality: `git show <SPLIT_COMMIT>:<REGISTER_PATH>`
   lines [SPLIT_LINE, EOF] (the exact content that used to be §4) must be
   byte-for-byte identical to the archive file's body (everything after its
   own frontmatter + banner, located by the same start-of-content marker
   line that also opens the pre-split §4).
2. §0-§3 byte-for-byte equality: the same original commit's lines
   [FRONTMATTER_END+1, SPLIT_LINE-1] — everything from the end of the
   original YAML frontmatter through end of §3 (Register law, Entry schema,
   §0 historical import, §1-§3 branch census; i.e. everything NOT moved and
   NOT frontmatter) — must be byte-for-byte identical to the same range in
   the current index file. The YAML frontmatter itself (lines 1..
   FRONTMATTER_END) is EXPECTED to differ (version bump, changelog entry,
   new relates_to pointers) and is deliberately excluded from this check.
3. Heading-set equality: every markdown heading line (`^#{2,6} `) found in
   the original §4-onward range must appear, verbatim, exactly once, in the
   archive body, in the same relative order — a structural cross-check
   independent of the byte diff above, so a bug in the byte-range math alone
   could not silently pass both checks.
4. Entry-id coverage: every `V3-E-\\d+` / `S\\d-V3-E-\\d+[a-z]?` token that
   appears anywhere in the original §4-onward range appears at least once,
   somewhere, in the archive body (a fact-selection-style safety net: even
   an id mentioned only in prose, not as a heading, must survive).

Exit code 0 = every check passed. Exit code 1 = at least one check failed
(and the specific failure is printed) — this script fails loudly, it does
not silently degrade to "probably fine."
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REGISTER_PATH = "00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md"
ARCHIVE_PATH = "00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_ARCHIVE_PRECONVERGENCE_v1_0.md"

# The exact heading line that opened the moved section in the pre-split
# file. Used both to find the split point in the original commit (so this
# script does not hardcode a line number that could silently go stale) and
# to locate the start of the archive file's body after its frontmatter.
SPLIT_MARKER = "## §4 — V3 entries opened by A3-ABSORB"

# The exact heading line the split introduces in the INDEX file, replacing
# SPLIT_MARKER. Used as the end-of-unchanged-head boundary in the CURRENT
# index file, whose frontmatter is longer than the original's (version
# bump, new changelog entry, new relates_to pointers) so a fixed line
# offset cannot be reused across the two files.
NEW_INDEX_SECTION_MARKER = "## §4 — Historical V3 entries (FROZEN, moved 2026-08-29)"

HEADING_RE = re.compile(r"^#{2,6}\s+\S")
ID_RE = re.compile(r"\b(?:S\d-)?V3-E-\d+[a-z]?\b")


def run_git_show(repo_root: Path, commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{commit}:{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"FAIL: could not read {path} @ {commit}: {result.stderr.strip()}"
        )
    return result.stdout


def find_split_line(original_lines: list[str]) -> int:
    """1-indexed line number of SPLIT_MARKER in the original file."""
    for i, line in enumerate(original_lines, start=1):
        if line.rstrip("\n") == SPLIT_MARKER:
            return i
    raise SystemExit(
        f"FAIL: split marker {SPLIT_MARKER!r} not found in the pre-split commit's "
        f"register — the split-point re-derivation has nothing to anchor on."
    )


def find_frontmatter_end(lines: list[str]) -> int:
    """1-indexed line number of the SECOND '---' line (YAML frontmatter close).

    The first '---' (line 1) opens the frontmatter block; the second closes
    it. Everything up to and including that second line is expected to
    legitimately change across the split (version bump, changelog); this
    function exists so the "unchanged" check below starts right after it,
    not before.
    """
    seen_first = False
    for i, line in enumerate(lines, start=1):
        if line.rstrip("\n") == "---":
            if not seen_first:
                seen_first = True
                continue
            return i
    raise SystemExit("FAIL: could not locate the closing '---' of the YAML frontmatter")


def find_archive_body_start(archive_lines: list[str]) -> int:
    """0-indexed list position where the archive's moved body begins."""
    for i, line in enumerate(archive_lines):
        if line.rstrip("\n") == SPLIT_MARKER:
            return i
    raise SystemExit(
        f"FAIL: split marker {SPLIT_MARKER!r} not found anywhere in the archive "
        f"file — the archive does not contain the moved content at all."
    )


def find_frontmatter_end_in(lines: list[str], label: str) -> int:
    try:
        return find_frontmatter_end(lines)
    except SystemExit as exc:
        raise SystemExit(f"{exc} (looking in {label})") from exc


def find_marker_line(lines: list[str], marker: str, label: str) -> int:
    """1-indexed line number of an exact-match marker line."""
    for i, line in enumerate(lines, start=1):
        if line.rstrip("\n") == marker:
            return i
    raise SystemExit(f"FAIL: marker {marker!r} not found in {label}")


def extract_headings(text: str) -> list[str]:
    return [line.rstrip("\n") for line in text.splitlines() if HEADING_RE.match(line)]


def extract_ids(text: str) -> set[str]:
    return set(ID_RE.findall(text))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--split-commit",
        default="eb34040ef",
        help="git ref for the pre-split state of the register (default: the "
        "commit this worktree was created from, eb34040ef).",
    )
    parser.add_argument(
        "--repo-root",
        default=Path(__file__).resolve().parents[3],
        type=Path,
        help="repo root (default: derived from this script's location).",
    )
    args = parser.parse_args()

    repo_root: Path = args.repo_root
    failures: list[str] = []

    # --- Load the pre-split original from git (not from disk: the disk
    # copy has already been split by this lane's own changes, so re-reading
    # git history is what makes this an independent check rather than a
    # tautology). ---
    original_text = run_git_show(repo_root, args.split_commit, REGISTER_PATH)
    original_lines = original_text.splitlines(keepends=True)
    split_line = find_split_line(original_lines)
    frontmatter_end = find_frontmatter_end(original_lines)
    print(f"Split marker found at original line {split_line} (1-indexed) "
          f"in {args.split_commit}:{REGISTER_PATH}")
    print(f"Frontmatter close found at original line {frontmatter_end} "
          f"(this line and everything before it is excluded from the "
          f"unchanged-head check — it is expected to change)")

    # §0-§3: frontmatter is deliberately excluded (expected to change).
    original_head = "".join(original_lines[frontmatter_end : split_line - 1])
    original_moved = "".join(original_lines[split_line - 1 :])  # old §4 onward

    # --- Load the two files as they exist on disk now (post-split). ---
    index_path = repo_root / REGISTER_PATH
    archive_path = repo_root / ARCHIVE_PATH
    if not index_path.exists():
        raise SystemExit(f"FAIL: {REGISTER_PATH} does not exist on disk")
    if not archive_path.exists():
        raise SystemExit(f"FAIL: {ARCHIVE_PATH} does not exist on disk")

    index_lines = index_path.read_text().splitlines(keepends=True)
    archive_lines = archive_path.read_text().splitlines(keepends=True)

    # Check 2: §0-§3 head unchanged (frontmatter excluded on both sides;
    # the current index file's frontmatter is a different length than the
    # original's, so we re-locate its own boundary rather than reusing the
    # original's line numbers).
    current_frontmatter_end = find_frontmatter_end_in(index_lines, REGISTER_PATH + " (on disk)")
    current_section_end = find_marker_line(index_lines, NEW_INDEX_SECTION_MARKER, REGISTER_PATH + " (on disk)")
    current_head = "".join(index_lines[current_frontmatter_end : current_section_end - 1])
    if current_head != original_head:
        failures.append(
            "HEAD MISMATCH: index file's §0-§3 content (frontmatter close "
            f"line {current_frontmatter_end} through the line before "
            f"{NEW_INDEX_SECTION_MARKER!r}) differs from the pre-split "
            "original's same logical range (frontmatter excluded on both "
            "sides). §0-§3 were declared out of scope for the split and "
            "must be byte-identical."
        )
    else:
        print(f"OK: index §0-§3 content ({len(current_head.splitlines())} "
              f"lines, frontmatter excluded) byte-identical to pre-split "
              f"original")

    # Check 1: archive body byte-identical to the moved original content.
    archive_body_start = find_archive_body_start(archive_lines)
    archive_body = "".join(archive_lines[archive_body_start:])
    if archive_body != original_moved:
        failures.append(
            "BODY MISMATCH: archive file's body (from its own copy of the "
            "split marker onward) is not byte-identical to the pre-split "
            "original's §4-onward content. This is the core lossless claim "
            "and it did not hold."
        )
        # Help debugging: first differing line.
        orig_body_lines = original_moved.splitlines()
        arch_body_lines = archive_body.splitlines()
        for idx, (a, b) in enumerate(zip(orig_body_lines, arch_body_lines)):
            if a != b:
                failures.append(
                    f"  first divergence at body line {idx + 1}:\n"
                    f"    original: {a!r}\n"
                    f"    archive : {b!r}"
                )
                break
        else:
            if len(orig_body_lines) != len(arch_body_lines):
                failures.append(
                    f"  line count differs: original={len(orig_body_lines)} "
                    f"archive={len(arch_body_lines)}"
                )
    else:
        print(f"OK: archive body ({len(archive_body.splitlines())} lines) "
              f"byte-identical to pre-split §4-onward content")

    # Check 3: heading-set + order equality (independent structural check).
    original_headings = extract_headings(original_moved)
    archive_headings = extract_headings(archive_body)
    if original_headings != archive_headings:
        missing = [h for h in original_headings if h not in archive_headings]
        extra = [h for h in archive_headings if h not in original_headings]
        failures.append(
            f"HEADING MISMATCH: {len(original_headings)} headings in the "
            f"original moved range vs {len(archive_headings)} in the "
            f"archive body (or order differs).\n"
            f"  missing from archive: {missing}\n"
            f"  extra in archive: {extra}"
        )
    else:
        print(f"OK: all {len(original_headings)} headings preserved, "
              f"verbatim, in original order")

    # Check 4: every id token mentioned anywhere survives somewhere.
    original_ids = extract_ids(original_moved)
    archive_ids = extract_ids(archive_body)
    missing_ids = original_ids - archive_ids
    if missing_ids:
        failures.append(
            f"ID COVERAGE FAILURE: {len(missing_ids)} id token(s) present in "
            f"the original moved range are absent from the archive body: "
            f"{sorted(missing_ids)}"
        )
    else:
        print(f"OK: all {len(original_ids)} distinct id tokens "
              f"(V3-E-*/S<n>-V3-E-*) present in the archive body")

    print()
    if failures:
        print(f"RESULT: FAIL ({len(failures)} problem(s))")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("RESULT: PASS — the A5 split is verified lossless against "
          f"{args.split_commit}:{REGISTER_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
