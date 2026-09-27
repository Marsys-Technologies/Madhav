#!/usr/bin/env python3
"""Proof 4: every transition the --emit-gaps dry run appended to the ledger COPY, by type, and a
check that every CLOSED row rests on a genuine PASS or a justified N/A in the census it came from."""
import json, collections, sys
S = "/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/e1effe6d-cae4-4643-b098-d49444a83a68/scratchpad/w2-1"
BASE_LINES = 263
rows = [json.loads(l) for l in open(f"{S}/ctrl_emit/asset_gaps.jsonl", encoding="utf-8") if l.strip()]
new = rows[BASE_LINES:]
census = {}
for L in "L0 L1 L2 L3 L4 L5".split():
    for a in json.load(open(f"{S}/ctrl_emit/census_{L}.json"))[L]["assets"]:
        census[a["asset_id"]] = a["measurements"]
kind = collections.Counter()
for r in new:
    w = r["what"]
    k = "CLOSED" if r["state"] == "CLOSED" else ("RE-OPENED" if w.startswith("RE-OPENED") else "OPEN (new)")
    kind[(k, r["criterion"])] += 1
print("appended rows:", len(new))
for (k, c), n in sorted(kind.items()): print(f"  {k:11s} {c:24s} {n}")
# The N/A reasons the enumeration labels genuine/justified (text prefixes of the measured field).
JUSTIFIED_NA = ("no writer, and the registry agrees", "no count_sql and nothing to count",
                "target_floor=0: the registry declares", "no declared dependencies",
                "never run, and it has no writer", "never run; check 7 owns this",
                "0 module(s): none", "count_sql=no, integrity_check_sql=no")
# Build.target N/A: justified for a declared service or an asset with no writer; for asset_kind='data'
# WITH a writer it is the contested R53 branch (W2-2) — reported separately, never counted as justified.
def justified(m):
    s = m["measured"]
    if s.startswith(JUSTIFIED_NA): return True
    return s.startswith("no target_table;") and ("asset_kind='service'" in s or "has_writer=False" in s)
bad = []
for r in new:
    if r["state"] != "CLOSED": continue
    m = census.get(r["asset"], {}).get(r["criterion"])
    ok = m is not None and (m["v"] == "PASS" or (m["v"] == "N/A" and justified(m)))
    print(f"  CLOSED {r['gap_id']}: census {m['v'] if m else '<absent>'} — {(m or {}).get('measured','')[:110]}"
          f"  => {'OK' if ok else 'UNJUSTIFIED'}")
    if not ok: bad.append(r["gap_id"])
print("CLOSED rows lacking a genuine PASS / justified N/A:", bad or "none")
# every census verdict that is closable must be PASS or a justified N/A (whether or not a gap existed)
unj = [(aid, c, m["measured"][:80]) for aid, ms in census.items() for c, m in ms.items()
       if m["v"] == "N/A" and not justified(m)]
print("N/A verdicts in the census outside the justified set (contested, R53 W2-2):", len(unj))
for x in unj: print("   ", x)

na = collections.Counter((c, m["measured"][:40]) for ms in census.values() for c, m in ms.items() if m["v"] == "N/A")
print("all N/A verdicts in the census (criterion, reason prefix):")
for k, n in sorted(na.items()): print(f"   {n:4d} {k}")
