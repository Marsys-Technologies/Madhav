#!/usr/bin/env python3
"""reserve_migration_number.py — Paripraśna P0-B migration-number allocator (RF-2/X-6).

Computes the next free migration number for a lane to CLAIM in
`origin/campaign-coordination`'s `00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md`
"## 2. MIGRATION NUMBER CLAIMS" table, per the repo's existing, live convention
(claim-at-PR-open; renumber-on-collision stands; a single global sequence spans
BOTH `platform/migrations/` and `platform/supabase/migrations/` despite
`MIGRATION_DIRECTORY_POLICY_v1_0.md`'s 2026-05-22 text nominally saying the
supabase directory is frozen — live practice has continued to allocate from both
directories against one shared counter, and the CCD table is the authority, not
that doc).

THIS SCRIPT NEVER WRITES TO `origin/campaign-coordination` OR ANY GOVERNANCE
FILE. It only computes a number and prints a ready-to-paste table row. Per
X-6 ("migration numbers reserved there before authoring") and X-2 (governance
registries are close-only, written in one announced/leased step), the actual
append to the coordination file is a conductor action, done from a scratch
worktree, never automated by this tool and never by a lane builder directly.

Usage
-----
    python3 platform/scripts/governance/reserve_migration_number.py \\
        --campaign PARIPRASHNA \\
        --file 574_pariprashna_p1_foo.sql \\
        --description "short description of what it does" \\
        --context "P1 lane X, PR not yet open" \\
        [--repo-root /path/to/checkout] \\
        [--ccd-file /path/to/already-checked-out/CAMPAIGN_COORDINATION.md]

Without --ccd-file, the script tries `git show origin/campaign-coordination:
00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md` from --repo-root (default:
this script's repo). This is a READ (git show), not a checkout/merge — safe
to run from any worktree, per X-7 (origin/main / origin/<branch> is the only
truth; always fetch, never trust a local ref that may be stale). Run
`git fetch origin campaign-coordination` first if you want a fresh read.

Exit codes: 0 = computed cleanly; 1 = could not determine a safe number
(e.g. CCD read failed and no --ccd-file given) — in that case this tool
deliberately refuses to guess rather than risk a collision.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

MIGRATION_DIRS = ("platform/migrations", "platform/supabase/migrations")
CLAIM_TABLE_HEADER = "## 2. MIGRATION NUMBER CLAIMS"
# Matches leading-number-or-range table cells, e.g. "| 574 |" or "| 570+ |" or "| 558–563 |".
ROW_NUM_RE = re.compile(r"^\|\s*(\d+)(?:[–—-](\d+))?\+?\s*\|")


def local_ceiling(repo_root: Path) -> int:
    """Highest migration number present on disk across both migration dirs."""
    highest = 0
    for rel in MIGRATION_DIRS:
        d = repo_root / rel
        if not d.is_dir():
            continue
        for f in d.glob("*.sql"):
            m = re.match(r"^(\d+)_", f.name)
            if m:
                highest = max(highest, int(m.group(1)))
    return highest


def ccd_ceiling(ccd_text: str) -> int:
    """Highest migration number claimed/merged in the CCD's own claim table."""
    highest = 0
    in_table = False
    for line in ccd_text.splitlines():
        if line.strip().startswith(CLAIM_TABLE_HEADER):
            in_table = True
            continue
        if in_table:
            if line.strip().startswith("## "):
                break  # left the section
            m = ROW_NUM_RE.match(line.strip())
            if m:
                lo = int(m.group(1))
                hi = int(m.group(2)) if m.group(2) else lo
                highest = max(highest, lo, hi)
    return highest


def fetch_ccd_text(repo_root: Path) -> str | None:
    try:
        out = subprocess.run(
            [
                "git",
                "show",
                "origin/campaign-coordination:00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md",
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout
    except subprocess.CalledProcessError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--campaign", required=True, help="e.g. PARIPRASHNA")
    ap.add_argument("--file", required=True, help="proposed migration filename, WITHOUT the number prefix, e.g. pariprashna_p1_foo.sql")
    ap.add_argument("--description", required=True, help="one-line description for the CCD row")
    ap.add_argument("--context", required=True, help="lane/PR context for the CCD row, e.g. 'P1 lane X, PR not yet open'")
    ap.add_argument("--repo-root", default=".", help="path to a checkout of this repo (default: cwd)")
    ap.add_argument("--ccd-file", default=None, help="path to an already-checked-out CAMPAIGN_COORDINATION.md (skips the git show read)")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()

    if args.ccd_file:
        ccd_text = Path(args.ccd_file).read_text()
    else:
        ccd_text = fetch_ccd_text(repo_root)
        if ccd_text is None:
            print(
                "ERROR: could not `git show origin/campaign-coordination:...CAMPAIGN_COORDINATION.md`. "
                "Run `git fetch origin campaign-coordination` first, or pass --ccd-file. "
                "Refusing to guess a migration number without reading the live claim ledger.",
                file=sys.stderr,
            )
            return 1

    disk_ceiling = local_ceiling(repo_root)
    table_ceiling = ccd_ceiling(ccd_text)
    next_free = max(disk_ceiling, table_ceiling) + 1

    filename = args.file
    if not re.match(r"^\d", filename):
        filename = f"{next_free}_{filename}"

    print(f"disk ceiling (platform/migrations + platform/supabase/migrations): {disk_ceiling}")
    print(f"CCD claim-table ceiling (origin/campaign-coordination):            {table_ceiling}")
    print(f"NEXT FREE (max + 1):                                               {next_free}")
    print()
    print("Paste this row into '## 2. MIGRATION NUMBER CLAIMS' in origin/campaign-coordination")
    print("(conductor action only, from a scratch worktree, never the main checkout — X-4/X-6):")
    print()
    print(f"| {next_free} | {args.campaign} | {filename} ({args.description}) | CLAIMED — {args.context} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
