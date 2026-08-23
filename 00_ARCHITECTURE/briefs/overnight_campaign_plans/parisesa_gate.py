#!/usr/bin/env python3
"""
parisesa_gate.py — MECHANICAL completion gate for PARIŚEṢA (the remaining 71).

Philosophy inherited from audit_gate.py: prose gates are satisfied by assertion;
this script is not. It enforces the campaign's three invariant rules:
  1. merged-and-live-verified (sha ancestor of origin/main + live probe evidence)
  2. lease conformance (no lane touches unleased paths)
  3. production == main (deployed catalog_version embeds the git sha)

Manifest: <repo>/00_ARCHITECTURE/briefs/parisesa/parisesa_manifest.json
Sole writer: INTEGRATOR. Everyone else reads.

PARIŚEṢA adds a FOURTH rule to the three inherited from ekv_gate.py:
  4. two-pass conformance — every LIVE lane carries REVIEW.md with verdict COMPLETE
     (no code was written from an unreviewed remediation spec).

PAR-R-12 (PRATINIDHI ruling, 2026-08-16) adds a FIFTH rule, tightening rule 4:
  5. review-integrity — "a REVIEW.md exists with verdict COMPLETE" is not, by itself,
     evidence the review was actually authored by VERIFIER (self-dispatched reviewers
     can write a REVIEW.md too). Two implementations PRATINIDHI explicitly rejected:
     git commit author (everyone commits as the same bot identity) and a self-asserted
     `reviewer: VERIFIER` frontmatter field alone (forgeable, no independent check).
     What works: two-artifact agreement across a single-writer boundary. For every LIVE
     lane the gate checks (a) REVIEW.md's OWN frontmatter carries `reviewer: VERIFIER`
     + `verdict: COMPLETE`, (b) LEDGER_VERIFIER.md (VERIFIER's sole-write ledger) carries
     an independent verdict-index row for the same finding id, and (c) the two agree.
     A self-dispatched reviewer can forge (a) but cannot write VERIFIER's own ledger.
     Disagreement between (a) and (b) — or a missing (b) — is a HARD FAIL routed to
     PRATINIDHI; the gate never auto-resolves a disagreement.

LEDGER_VERIFIER.md verdict-index contract (coordinated with VERIFIER):
  VERIFIER's ledger is free-form prose above a single required section:

    ## PARISESA-VERDICT-INDEX

    | finding | verdict | at |
    |---|---|---|
    | F-62 | COMPLETE | 2026-08-16T14:59:00+05:30 |

  Append-only: VERIFIER never edits or deletes an existing row, even to correct an
  earlier verdict (mirrors VERIFIER's own demonstrated practice elsewhere in the ledger
  of keeping a superseded pass and adding a correction on top, not overwriting it) — a
  correction is a NEW row for the same finding id. The gate takes the LAST row for a
  given finding id (table order = chronological, latest wins) as VERIFIER's current
  verdict for that finding.

Manifest shape:
{
  "deployed_main_sha": "<full-git-sha>",                  # E writes after each merge+deploy (EKV-R-2)
  "cl00_cheap_subset_last_run": {"result": "PASS", "at": "..."},
  "lanes": [
    {"lane": "F-34", "wave": 1, "branch": "par/s3-f34-horizon-disclosure",
     "merged_sha": "<full-or-12>", "files_touched": ["platform-mcp/src/tools/registry_bridge.ts"],
     "lease_ok": true, "exit_test": "path-or-cmd", "exit_test_result": "PASS",
     "live_probe_evidence": "00_ARCHITECTURE/briefs/parisesa/evidence/F-34_live.json",
     "review_verdict": "COMPLETE",   # Stage-R second pass (PARIŚEṢA rule 4)
     "review_doc": "00_ARCHITECTURE/briefs/parisesa/lanes/F-34/REVIEW.md",
     "status": "LIVE"}          # CLAIMED|BUILT|VERIFIED|MERGED|LIVE|BLOCKED|HANDOFF
  ]
}

Usage:
  parisesa_gate.py status  [--repo /path]
  parisesa_gate.py verify --wave N [--repo /path]     # exit 0 only if wave N complete
"""
import json, os, re, subprocess, sys

def sh(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

def load(repo):
    p = os.path.join(repo, "00_ARCHITECTURE/briefs/parisesa/parisesa_manifest.json")
    if not os.path.exists(p):
        sys.exit(f"FATAL: manifest missing at {p} — conductor seeds it at T0.")
    with open(p) as f:
        return json.load(f), p

def _parse_frontmatter_field(text, key):
    """Read a `key: value` line from a `---`-delimited YAML-ish frontmatter block and
    return the value's FIRST TOKEN only (up to the first whitespace or opening paren).
    Real REVIEW.md frontmatter in this campaign carries trailing commentary on the same
    line, e.g. `reviewer: VERIFIER (author != reviewer — ...)` or
    `verdict: COMPLETE (PASS 2, superseding PASS 1's INCOMPLETE-RETURN below)` — the
    bare leading token is the actual value; the parenthetical is prose, not data.
    Returns None if the frontmatter block or the key is not found.
    """
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return None
    fm = m.group(1)
    for line in fm.splitlines():
        line = line.strip()
        if line.startswith(f"{key}:"):
            value = line[len(key) + 1:].strip()
            first = re.split(r"[\s(]", value, maxsplit=1)[0]
            return first or None
    return None

def _parse_verifier_ledger_index(path):
    """Parse LEDGER_VERIFIER.md's '## PARISESA-VERDICT-INDEX' markdown table into
    {finding_id: verdict}, taking the LAST row for a given finding id (append-only
    ledger — a correction is a new row, not an edit to the old one; last row wins).
    Returns {} if the file or the section doesn't exist (callers treat that as "no
    independent record", which is itself a hard-fail condition per PAR-R-12 — this
    function does not itself decide pass/fail, only extracts what's there).
    """
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        text = f.read()
    m = re.search(r"^## PARISESA-VERDICT-INDEX\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL | re.MULTILINE)
    if not m:
        return {}
    section = m.group(1)
    verdicts = {}
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2 or cells[0] in ("finding", "---", ""):
            continue
        if set(cells[0]) <= {"-", " "}:
            continue
        finding_id, verdict = cells[0], cells[1]
        verdicts[finding_id] = verdict  # last matching row overwrites — latest wins
    return verdicts

def main():
    args = sys.argv[1:]
    if not args: sys.exit(__doc__)
    cmd = args[0]
    repo = "/Users/Dev/Vibe-Coding/Apps/Madhav"
    wave = None
    for i, a in enumerate(args):
        if a == "--repo": repo = args[i+1]
        if a == "--wave": wave = int(args[i+1])
    m, mp = load(repo)
    lanes = m.get("lanes", [])
    ledger_path = os.path.join(repo, "00_ARCHITECTURE/briefs/parisesa/LEDGER_VERIFIER.md")

    if cmd == "status":
        from collections import Counter
        c = Counter(l.get("status","?") for l in lanes)
        print(f"lanes: {len(lanes)} · " + " · ".join(f"{k}={v}" for k,v in sorted(c.items())))
        for l in lanes:
            print(f"  [{l.get('wave','?')}] {l.get('lane','?'):6} {l.get('status','?'):9} {l.get('branch','')}")
        return

    if cmd != "verify" or wave is None:
        sys.exit("usage: parisesa_gate.py verify --wave N   (or: status)")

    errs = []
    sh("git fetch origin main --quiet", cwd=repo)
    rc, main_tip, _ = sh("git rev-parse origin/main", cwd=repo)
    if rc != 0: errs.append("cannot resolve origin/main")

    # Rule 3: production == main (EKV-R-2: use deployed_main_sha, not catalog_version)
    # Stream E writes deployed_main_sha after each merge+deploy; catalog_version +r suffix
    # is SHA256(tool_names).slice(0,12) — not a git SHA, never comparable to origin/main.
    dep_sha = m.get("deployed_main_sha", "")
    if not dep_sha or main_tip[:12] != dep_sha[:12]:
        errs.append(f"PROD-SYNC: manifest deployed_main_sha '{dep_sha[:12] if dep_sha else 'MISSING'}' != origin/main tip {main_tip[:12]}")

    # CL-00 regression baseline
    cl = m.get("cl00_cheap_subset_last_run", {})
    if cl.get("result") != "PASS":
        errs.append(f"CL-00 cheap subset not PASS (got {cl.get('result')!r}) — regression baseline unproven")

    wave_lanes = [l for l in lanes if l.get("wave") == wave]
    if not wave_lanes:
        errs.append(f"no lanes registered for wave {wave} — implausible")
    for l in wave_lanes:
        lid = l.get("lane", "?")
        st = l.get("status")
        if st in ("BLOCKED", "HANDOFF"):
            if not l.get("handoff_note"):
                errs.append(f"{lid}: {st} without handoff_note — dishonest park")
            continue  # honest park is not a gate failure, but it IS counted
        if st != "LIVE":
            errs.append(f"{lid}: status {st!r} — wave lanes must be LIVE or honestly parked")
            continue
        sha = l.get("merged_sha") or ""
        if not sha:
            errs.append(f"{lid}: merged_sha is null/missing — not yet recorded by Stream E")
        else:
            rc, _, _ = sh(f"git merge-base --is-ancestor {sha} origin/main", cwd=repo)
            if rc != 0:
                errs.append(f"{lid}: merged_sha {sha[:12]} is NOT an ancestor of origin/main (PR#1287 rule)")
        if not l.get("lease_ok"):
            errs.append(f"{lid}: lease_ok is not true — isolation unproven")
        if l.get("exit_test_result") != "PASS":
            errs.append(f"{lid}: exit_test_result {l.get('exit_test_result')!r}")
        # PARIŚEṢA rule 4 — the two-pass gate: code may not exist without a COMPLETE review
        if l.get("review_verdict") != "COMPLETE":
            errs.append(f"{lid}: review_verdict {l.get('review_verdict')!r} — Stage-R second pass not COMPLETE")
        rd = l.get("review_doc", "")
        rdp = rd if os.path.isabs(rd) else os.path.join(repo, rd)
        if not rd or not os.path.exists(rdp) or os.path.getsize(rdp) == 0:
            errs.append(f"{lid}: REVIEW.md missing/empty: {rd!r} — two-pass unprovable")
        else:
            # PAR-R-12 rule 5 — review-integrity: two-artifact agreement across a
            # single-writer boundary. REVIEW.md's own frontmatter (forgeable by anyone
            # with repo write access) is checked AGAINST LEDGER_VERIFIER.md (VERIFIER's
            # sole-write file, which a self-dispatched/forged reviewer cannot write) —
            # neither artifact alone is trusted; both must independently say COMPLETE.
            with open(rdp) as f:
                review_text = f.read()
            reviewer_field = _parse_frontmatter_field(review_text, "reviewer")
            verdict_field = _parse_frontmatter_field(review_text, "verdict")
            if reviewer_field != "VERIFIER":
                errs.append(f"{lid}: REVIEW.md frontmatter 'reviewer' is {reviewer_field!r}, not VERIFIER (PAR-R-12)")
            if verdict_field != "COMPLETE":
                errs.append(f"{lid}: REVIEW.md frontmatter 'verdict' is {verdict_field!r}, not COMPLETE (PAR-R-12)")
            ledger_verdicts = _parse_verifier_ledger_index(ledger_path)
            ledger_verdict = ledger_verdicts.get(lid)
            if ledger_verdict is None:
                errs.append(
                    f"{lid}: PAR-R-12 REVIEW-INTEGRITY — no LEDGER_VERIFIER.md verdict-index row for {lid}. "
                    f"REVIEW.md claims a VERIFIER review but VERIFIER's own sole-write ledger has no "
                    f"independent record. HARD FAIL, route to PRATINIDHI — gate does not auto-resolve."
                )
            elif ledger_verdict != "COMPLETE":
                errs.append(
                    f"{lid}: PAR-R-12 REVIEW-INTEGRITY — REVIEW.md claims COMPLETE but LEDGER_VERIFIER.md's "
                    f"latest verdict-index row for {lid} says {ledger_verdict!r}. Disagreement between the "
                    f"two artifacts. HARD FAIL, route to PRATINIDHI — gate does not auto-resolve."
                )
        ev = l.get("live_probe_evidence", "")
        evp = ev if os.path.isabs(ev) else os.path.join(repo, ev)
        if not ev or not os.path.exists(evp) or os.path.getsize(evp) == 0:
            errs.append(f"{lid}: live probe evidence missing/empty: {ev!r}")
        else:
            try:
                with open(evp) as f: json.load(f)
            except Exception as e:
                errs.append(f"{lid}: live evidence not valid JSON: {e}")

    parked = [l["lane"] for l in wave_lanes if l.get("status") in ("BLOCKED","HANDOFF")]
    if errs:
        print("EKV-GATE: FAILED")
        for e in errs: print("  ✗ " + e)
        print(f"\n{len(errs)} blocking problem(s). Terminal marker MUST NOT be posted.")
        sys.exit(1)
    live = [l["lane"] for l in wave_lanes if l.get("status") == "LIVE"]
    print("EKV-GATE: PASSED")
    print(f"PARISESA-WAVE-{wave}-VERIFIED: {len(live)} lanes merged+live "
          f"({', '.join(live)})"
          + (f" · honestly parked: {', '.join(parked)}" if parked else "")
          + f" · prod=main@{main_tip[:12]} · CL-00 cheap subset PASS · two-pass REVIEW COMPLETE on all"
          + f" · PAR-R-12 review-integrity (REVIEW.md x LEDGER_VERIFIER.md) agrees on all")
    sys.exit(0)

if __name__ == "__main__":
    main()
