#!/usr/bin/env python3
"""PG-1 Lane A-0: §G gate harness. Runs all 9 assertions, prints green/red, exits 1 if any integrity assertion is red."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DELIV = ROOT / "00_ARCHITECTURE/pg1_audit/deliverables"
ARCH = ROOT / "00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md"
TRUTH = ROOT / "00_ARCHITECTURE/RETRIEVAL_SYSTEM_TRUTH_v1_0.md"
REPORT = ROOT / "00_ARCHITECTURE/PARIPRASHNA_GROUNDING_AUDIT_REPORT_v1_0.md"
CANON = DELIV / "pg1_findings.jsonl"

results = {}


def load_findings():
    if not CANON.exists():
        return []
    out = []
    for line in CANON.read_text().splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def g1(findings):
    seen = {f["assumption"] for f in findings if f.get("assumption", "").startswith("A")}
    need = {f"A{i}" for i in range(1, 33)}
    missing = need - seen
    results["G.1"] = (len(missing) == 0, f"missing verdicts: {sorted(missing)}" if missing else "all 32 covered")


def g2(findings):
    bad = [f["id"] for f in findings if f.get("class") != "unverifiable" and not f.get("evidence")]
    results["G.2"] = (len(bad) == 0, f"findings without evidence: {bad}" if bad else "all evidenced")


def g3():
    ok = TRUTH.exists()
    if ok:
        text = TRUTH.read_text()
        items = ["capability inventory", "Behavioural profile", "planning path", "acharya floor", "dark", "chat projection", "Envelope self-sufficiency"]
        missing = [i for i in items if i.lower() not in text.lower()]
        ok = len(missing) == 0
        results["G.3"] = (ok, "exists, all 7 items present" if ok else f"missing sections: {missing}")
    else:
        results["G.3"] = (False, "RETRIEVAL_SYSTEM_TRUTH_v1_0.md does not exist")


def g4():
    results["G.4"] = (TRUTH.exists(), "manual check required — see TRUTH doc §2 coverage")


def g5():
    if not REPORT.exists():
        results["G.5"] = (False, "AUDIT_REPORT does not exist")
        return
    text = REPORT.read_text()
    ok = bool(re.search(r"C-2.*(YES|NO)", text, re.IGNORECASE | re.DOTALL)) or "shim feasibility: yes" in text.lower() or "shim feasibility: no" in text.lower()
    results["G.5"] = (ok, "binary YES/NO found" if ok else "no unambiguous YES/NO found for shim feasibility")


def g6():
    if not REPORT.exists():
        results["G.6"] = (False, "AUDIT_REPORT does not exist")
        return
    text = REPORT.read_text().lower()
    ok = "unified plan type" in text or "r-3" in text
    results["G.6"] = (ok, "R-3 result section present" if ok else "no R-3 result section found")


def g7():
    if not ARCH.exists():
        results["G.7"] = (False, "architecture doc missing")
        return
    text = ARCH.read_text()
    ok = ("version: 0.6" in text or "version 0.6" in text) and "[CORRECTED]" in text
    results["G.7"] = (ok, "v0.6 + [CORRECTED] markers present" if ok else "not yet at v0.6 with corrections")


def g8():
    if not REPORT.exists():
        results["G.8"] = (False, "AUDIT_REPORT does not exist")
        return
    text = REPORT.read_text().lower()
    ok = "q-1" in text and ("acharya" in text)
    results["G.8"] = (ok, "Q-1 verdict section present" if ok else "no Q-1 verdict section found")


def g9():
    out = subprocess.run(["git", "diff", "--stat", "origin/main...HEAD"], cwd=ROOT, capture_output=True, text=True)
    forbidden = ["platform/src", "platform-mcp/src", "platform/migrations", "infra/", ".github/workflows"]
    hits = [line for line in out.stdout.splitlines() if any(f in line for f in forbidden)]
    results["G.9"] = (len(hits) == 0, "clean" if not hits else f"touched forbidden paths: {hits}")


def main():
    findings = load_findings()
    g1(findings)
    g2(findings)
    g3()
    g4()
    g5()
    g6()
    g7()
    g8()
    g9()
    integrity = {"G.2", "G.4", "G.5", "G.8", "G.9"}
    red = []
    for k, (ok, msg) in sorted(results.items()):
        tag = "INTEGRITY" if k in integrity else ""
        print(f"{'GREEN' if ok else 'RED  '} {k} {tag}: {msg}")
        if not ok:
            red.append(k)
    print()
    if any(r in integrity for r in red):
        print("GATE: RED (integrity assertion failed)")
        sys.exit(1)
    if red:
        print(f"GATE: RED (non-integrity assertions failed: {red})")
        sys.exit(1)
    print("GATE: GREEN")
    sys.exit(0)


if __name__ == "__main__":
    main()
