#!/usr/bin/env python3
"""Detects the PR-merged -> ledger-status sync gap that was caught (and re-caught)
by hand twice in the PARISESA-V4-CONDUCTOR-20260820T191407Z overnight session.

The defect: a PR referencing a finding (e.g. "F-68" in its title/body) merges to
main, but the campaign's own finding_status closure event for that finding is
never emitted -- so ledger.json's terminal_status stays null even though the fix
already shipped. This happened three separate times in one session (F-68 et al.'s
sibling batch, then F-112-DOCSTRING/F-124/F-73, then F-71's copy-paste artifact
surfaced the same drift risk in a different shape) because the correction each
time was "fix the drift found," not "add a check that prevents new drift."

Usage:
    python3 check_ledger_pr_sync.py [--repo OWNER/NAME] [--ledger PATH]

Exits 0 if no drift found, 1 if drift found (script prints the mismatched
findings). Read-only: never writes to ledger.json, journal.ndjson, or GitHub --
flags candidates for a human/session to then emit the correct finding_status
event via build_tracker.py, the same way every real closure in this campaign was
recorded.

KNOWN FALSE-POSITIVE SHAPE (seen on the first real run, 2026-08-21): the F-number
regex matches ANY mention in a PR's title or body, including incidental prose
("...after F-35 landed and touched the same file...", "needs a separate lease,
PAR-F-26-NEEDS-LEASE") that is not a claim the PR itself fixes that finding. Every
hit this script reports is a CANDIDATE for a human to read and confirm, not an
auto-actionable closure -- treat "drift_found: true" as "go look," not "go close."
The 2026-08-21 first run found 3 candidates: 2 were incidental-prose false
positives (F-31 mentioned in #1382's body while discussing a since-superseded
judgment_flag; "F-26-NEEDS" was a lease-name fragment, not a finding ID), and one
(F-35, in #1386's body) was a REAL stale-ledger catch -- #1386's body correctly
described F-35's own fix as already landed via an earlier PR (#1316) that had
closed F-63 from the same commit but never closed F-35. See the campaign journal
for that correction's outcome.
"""
import argparse
import json
import re
import subprocess
import sys

F_NUMBER_RE = re.compile(r"\bF-\d+(?:-[A-Z]+)?\b")

TERMINAL_STATUSES = {
    "SERVICE_CLOSED",
    "HISTORICAL_STALE_CLOSED",
    "CONTROL_CLOSED",
    "NOT_APPLICABLE_CLOSED",
    "EXTERNAL_HOLD_TERMINAL",
}


def load_ledger(path):
    with open(path) as f:
        return json.load(f)


def fetch_merged_parisesa_prs(repo):
    # NOTE: "fix(parisesa) in:title" as a --search value silently matches zero
    # PRs -- GitHub's search syntax treats the parentheses specially rather than
    # as literal characters. Search on the bare "parisesa" token instead and
    # filter titles locally; this was caught by actually running this script
    # against the real repo, not assumed from the query looking reasonable.
    out = subprocess.run(
        [
            "gh", "pr", "list", "--repo", repo, "--state", "merged",
            "--search", "parisesa in:title", "--limit", "200",
            "--json", "number,title,body,mergeCommit,mergedAt",
        ],
        capture_output=True, text=True, check=True,
    )
    prs = json.loads(out.stdout)
    return [pr for pr in prs if pr["title"].startswith("fix(parisesa)")]


def extract_f_numbers(pr):
    text = f"{pr.get('title', '')}\n{pr.get('body', '') or ''}"
    return set(F_NUMBER_RE.findall(text))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="Marsys-Technologies/Madhav")
    ap.add_argument(
        "--ledger",
        default=(
            "/Users/Dev/par-night/parisesa-v4-state/00_ARCHITECTURE/briefs/"
            "parisesa/state/ledger.json"
        ),
    )
    args = ap.parse_args()

    ledger = load_ledger(args.ledger)
    findings = ledger.get("findings", {})

    prs = fetch_merged_parisesa_prs(args.repo)

    drift = []
    for pr in prs:
        for fnum in extract_f_numbers(pr):
            row = findings.get(fnum)
            if row is None:
                # A PR cites a finding_id this ledger has never heard of --
                # worth a look, but not necessarily drift (could be a sub-finding
                # or a typo in the PR title). Report separately, don't fail on it.
                drift.append({
                    "finding_id": fnum,
                    "pr_number": pr["number"],
                    "pr_title": pr["title"],
                    "merge_sha": (pr.get("mergeCommit") or {}).get("oid"),
                    "issue": "PR_CITES_UNKNOWN_FINDING_ID",
                })
                continue
            if row.get("terminal_status") not in TERMINAL_STATUSES:
                drift.append({
                    "finding_id": fnum,
                    "pr_number": pr["number"],
                    "pr_title": pr["title"],
                    "merge_sha": (pr.get("mergeCommit") or {}).get("oid"),
                    "ledger_status": row.get("status"),
                    "issue": "PR_MERGED_BUT_LEDGER_NOT_TERMINAL",
                })

    if drift:
        print(json.dumps({"drift_found": True, "entries": drift}, indent=2))
        sys.exit(1)

    print(json.dumps({"drift_found": False, "checked_prs": len(prs)}, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
