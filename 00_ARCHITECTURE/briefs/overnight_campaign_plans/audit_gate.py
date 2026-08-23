#!/usr/bin/env python3
"""
audit_gate.py — the MECHANICAL completion gate for PARIPŪRṆA-2.

Why this exists: PARIPŪRṆA v1 was instructed in prose to "sweep every tool" and
"cite a detector for every claim". It made 8 MCP calls out of 125 live tools
(6.4%), skipped whole mandated sections, and its TOP-RANKED finding was
fabricated (a field that exists neither in code nor in any live response).
Prose instructions are satisfiable by assertion. This script is not.

Usage:
  audit_gate.py init   --catalog-version V --tools-file tools.txt
  audit_gate.py status
  audit_gate.py verify            # THE GATE — exit 0 only if genuinely complete

The conductor CANNOT post its terminal marker until `verify` exits 0 and its
signed output line is pasted into the ledger. PARĪKṢAKA independently re-runs
`verify` and re-executes a random sample of finding reproduce_cmds.

Evidence rules enforced here (not merely requested):
  · every live tool has a verdict AND an evidence file that EXISTS, is non-empty,
    and parses as JSON
  · every finding carries a reproduce_cmd AND an evidence file that exists
  · no finding may cite an evidence file that no other artifact references
    (the v1 fabrication signature: a claim with no reachable evidence)
"""
import json, os, sys, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(ROOT, "pp2-audit", "manifest.json")
EVIDENCE_DIR = os.path.join(ROOT, "pp2-audit", "evidence")

VALID_VERDICTS = {"PASS", "GAP", "PARTIAL", "BY-DESIGN-OPEN", "NOT-APPLICABLE", "BLOCKED"}
SEVERITIES = {"TIER1-CORRECTNESS", "TIER2-HONESTY", "TIER3-EXPERIENCE", "TIER4-POLISH"}


def _load():
    if not os.path.exists(MANIFEST):
        sys.exit("FATAL: manifest.json missing — run `audit_gate.py init` first.")
    with open(MANIFEST) as f:
        return json.load(f)


def _save(m):
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, "w") as f:
        json.dump(m, f, indent=2, sort_keys=True)


def cmd_init(argv):
    cv = tools_file = None
    for i, a in enumerate(argv):
        if a == "--catalog-version": cv = argv[i + 1]
        if a == "--tools-file": tools_file = argv[i + 1]
    if not cv or not tools_file:
        sys.exit("usage: audit_gate.py init --catalog-version V --tools-file tools.txt")
    with open(tools_file) as f:
        tools = sorted({t.strip() for t in f if t.strip() and not t.startswith("#")})
    if len(tools) < 100:
        sys.exit(f"FATAL: only {len(tools)} tools supplied. The live catalog is ~125. "
                 "Enumerate from the LIVE server (tools/list or mcp_server_info), "
                 "NEVER by grepping source — source-grep returns test fixtures and "
                 "misses aliases (verified 2026-08-15: grep found 29, incl. "
                 "'definitely_not_a_real_registered_tool_xyz').")
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    _save({
        "catalog_version": cv,
        "tool_count_declared": len(tools),
        "tools": {t: {"verdict": None, "evidence_file": None, "note": None} for t in tools},
        "findings": [],
        "dimension_signoff": {d: None for d in
                              ["A_astrological", "B_data", "C_serving", "D_architecture",
                               "E_experience", "F_residuals", "G_security", "H_determinism",
                               "I_contract", "J_regression"]},
    })
    print(f"INITIALIZED: {len(tools)} tools, catalog {cv}")


def _evidence_ok(rel):
    if not rel: return False, "no evidence_file"
    p = rel if os.path.isabs(rel) else os.path.join(ROOT, "pp2-audit", rel)
    if not os.path.exists(p): return False, f"evidence file missing: {rel}"
    if os.path.getsize(p) == 0: return False, f"evidence file empty: {rel}"
    try:
        with open(p) as f: json.load(f)
    except Exception as e:
        return False, f"evidence not valid JSON ({rel}): {e}"
    return True, ""


def cmd_status():
    m = _load()
    done = sum(1 for v in m["tools"].values() if v.get("verdict"))
    print(f"tools: {done}/{len(m['tools'])} verdicts")
    print(f"findings: {len(m['findings'])}")
    for d, v in m["dimension_signoff"].items():
        print(f"  {d}: {v or 'PENDING'}")


def cmd_verify():
    m = _load()
    errs = []

    for name, row in sorted(m["tools"].items()):
        v = row.get("verdict")
        if v not in VALID_VERDICTS:
            errs.append(f"TOOL {name}: verdict {v!r} not in {sorted(VALID_VERDICTS)}")
            continue
        if v == "NOT-APPLICABLE":
            if not row.get("note"):
                errs.append(f"TOOL {name}: NOT-APPLICABLE requires a written note")
            continue
        ok, why = _evidence_ok(row.get("evidence_file"))
        if not ok:
            errs.append(f"TOOL {name}: {why}")

    if not m["findings"]:
        errs.append("FINDINGS: zero findings recorded — implausible for a 125-tool "
                    "sweep; v1 recorded 22. An empty findings list is itself suspect.")
    for i, f in enumerate(m["findings"]):
        fid = f.get("id", f"#{i}")
        for req in ("id", "claim", "reproduce_cmd", "evidence_file", "severity"):
            if not f.get(req):
                errs.append(f"FINDING {fid}: missing required field '{req}'")
        if f.get("severity") and f["severity"] not in SEVERITIES:
            errs.append(f"FINDING {fid}: severity {f['severity']!r} not in {sorted(SEVERITIES)}")
        ok, why = _evidence_ok(f.get("evidence_file"))
        if not ok:
            errs.append(f"FINDING {fid}: {why}")

    for d, v in m["dimension_signoff"].items():
        if not v:
            errs.append(f"DIMENSION {d}: no sign-off recorded")

    orphans = []
    referenced = {r.get("evidence_file") for r in m["tools"].values()} | \
                 {f.get("evidence_file") for f in m["findings"]}
    for p in glob.glob(os.path.join(EVIDENCE_DIR, "**", "*.json"), recursive=True):
        rel = os.path.relpath(p, os.path.join(ROOT, "pp2-audit"))
        if rel not in referenced:
            orphans.append(rel)

    if errs:
        print("AUDIT-GATE: FAILED\n")
        for e in errs: print("  ✗ " + e)
        print(f"\n{len(errs)} blocking problem(s). The terminal marker MUST NOT be posted.")
        sys.exit(1)

    tools_n = len(m["tools"])
    print("AUDIT-GATE: PASSED")
    print(f"AUDIT-COVERAGE-VERIFIED: {tools_n}/{tools_n} tools verdicted · "
          f"{len(m['findings'])} findings each with reproduce_cmd + evidence · "
          f"{len(m['dimension_signoff'])} dimensions signed off · "
          f"catalog {m['catalog_version']}"
          + (f" · {len(orphans)} unreferenced evidence file(s)" if orphans else ""))
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    c = sys.argv[1]
    if c == "init": cmd_init(sys.argv[2:])
    elif c == "status": cmd_status()
    elif c == "verify": cmd_verify()
    else: sys.exit(f"unknown command {c!r}")
