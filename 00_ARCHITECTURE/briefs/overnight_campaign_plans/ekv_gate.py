#!/usr/bin/env python3
"""
ekv_gate.py — MECHANICAL completion gate for EKAVĀKYATĀ (overnight remediation arc).

Philosophy inherited from audit_gate.py: prose gates are satisfied by assertion;
this script is not. It enforces the campaign's three invariant rules:
  1. merged-and-live-verified (sha ancestor of origin/main + live probe evidence)
  2. lease conformance (no lane touches unleased paths)
  3. production == main (deployed catalog_version embeds the git sha)

Manifest: <repo>/00_ARCHITECTURE/briefs/ekavakyata/ekv_manifest.json
Sole writer: STREAM E (SAṄGAMA). Everyone else reads.

Manifest shape:
{
  "deployed_main_sha": "<full-git-sha>",                  # E writes after each merge+deploy (EKV-R-2)
  "cl00_cheap_subset_last_run": {"result": "PASS", "at": "..."},
  "lanes": [
    {"lane": "A-01", "wave": 0, "branch": "ekv/a-01-timing-hardfloor",
     "merged_sha": "<full-or-12>", "files_touched": ["platform-mcp/src/tools/registry_bridge.ts"],
     "lease_ok": true, "exit_test": "path-or-cmd", "exit_test_result": "PASS",
     "live_probe_evidence": "briefs/ekavakyata/evidence/a01_judgment_timing.json",
     "status": "LIVE"}          # CLAIMED|BUILT|VERIFIED|MERGED|LIVE|BLOCKED|HANDOFF
  ]
}

Usage:
  ekv_gate.py status  [--repo /path]
  ekv_gate.py verify --wave N [--repo /path]     # exit 0 only if wave N complete
"""
import json, os, subprocess, sys

def sh(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

def load(repo):
    p = os.path.join(repo, "00_ARCHITECTURE/briefs/ekavakyata/ekv_manifest.json")
    if not os.path.exists(p):
        sys.exit(f"FATAL: manifest missing at {p} — conductor seeds it at T0.")
    with open(p) as f:
        return json.load(f), p

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

    if cmd == "status":
        from collections import Counter
        c = Counter(l.get("status","?") for l in lanes)
        print(f"lanes: {len(lanes)} · " + " · ".join(f"{k}={v}" for k,v in sorted(c.items())))
        for l in lanes:
            print(f"  [{l.get('wave','?')}] {l.get('lane','?'):6} {l.get('status','?'):9} {l.get('branch','')}")
        return

    if cmd != "verify" or wave is None:
        sys.exit("usage: ekv_gate.py verify --wave N   (or: status)")

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
    print(f"EKV-WAVE-{wave}-VERIFIED: {len(live)} lanes merged+live "
          f"({', '.join(live)})"
          + (f" · honestly parked: {', '.join(parked)}" if parked else "")
          + f" · prod=main@{main_tip[:12]} · CL-00 cheap subset PASS")
    sys.exit(0)

if __name__ == "__main__":
    main()
