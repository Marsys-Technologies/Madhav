"""Mutation harness for the verifier-side modules (measuring_report, nd_h_tables, near_miss_verifier).

Each mutant is one literal replacement in one module; the module's whole pure suite must then FAIL BY ASSERTION. The baseline must
pass first (a harness that cannot pass cleanly measures nothing). Classification is from the structured junit report: only a test
failure whose element is an assertion failure counts as CAUGHT; a collection error, an import error, a non-assertion exception or a
missing report is NOT caught (it would pass for the wrong reason). Equivalent mutants are listed with the reason they are skipped.

Run from platform/python-sidecar:  python ../scripts/gochara/mutation_check_verifier_side.py [--only NAME]
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

SIDECAR = Path(__file__).resolve().parents[2] / "python-sidecar"
K = SIDECAR / "services" / "gochara_kernel"

# name -> (module file, suite, old, new)
MUTANTS = {
    # nd_h_tables
    "ndh.band": ("nd_h_tables.py", "test_nd_h_tables.py", "BAND_DEG = 1.0", "BAND_DEG = 1.5"),
    "ndh.node-aspect": ("nd_h_tables.py", "test_nd_h_tables.py", '"rahu": frozenset({"conjunction"})', '"rahu": frozenset({"conjunction", "aspect"})'),
    "ndh.guard-ge": ("nd_h_tables.py", "test_nd_h_tables.py", "p4_alone_with_dvi_share > GAIN_BAND", "p4_alone_with_dvi_share >= GAIN_BAND"),
    "ndh.dvi-in-p3": ("nd_h_tables.py", "test_nd_h_tables.py", '    if path in ("P1", "P3"):\n        return t.core', '    if path in ("P1",):\n        return t.core\n    if path == "P3":\n        return t.core | t.dvi'),
    "ndh.saturn-karaka": ("nd_h_tables.py", "test_nd_h_tables.py", '"financial_deception": frozenset({"rahu"}),       #', '"financial_deception": frozenset({"rahu", "saturn"}),       #'),
    "ndh.frame": ("nd_h_tables.py", "test_nd_h_tables.py", "(anchor + offset - 2) % 12 + 1", "(anchor + offset - 1) % 12 + 1"),
    "ndh.p4-nodes": ("nd_h_tables.py", "test_nd_h_tables.py", 'P4_KB_AGENTS = frozenset({"jupiter", "saturn"})', 'P4_KB_AGENTS = frozenset({"jupiter", "saturn", "rahu", "ketu"})'),
    "ndh.bereavement-moon": ("nd_h_tables.py", "test_nd_h_tables.py", '    "bereavement": "sun",                             # ND-P2', '    "bereavement": "moon",                             # ND-P2'),
    "ndh.mother-resolves": ("nd_h_tables.py", "test_nd_h_tables.py", 'if person == "mother":', 'if person == "motherX":'),
    "ndh.karakatva-native": ("nd_h_tables.py", "test_nd_h_tables.py", "AFFECTED_PERSON.get(cls, DEFAULT_PERSON)): KARAKA_A", "AFFECTED_PERSON.get(cls)): KARAKA_A"),
    "ndh.unknown-agent": ("nd_h_tables.py", "test_nd_h_tables.py", '    if agent not in NINE:\n        raise ValueError(f"unknown_agent: {agent!r} (the nine, lower-case)")\n', ""),
    # near_miss_verifier
    "nm.min-approach": ("near_miss_verifier.py", "test_near_miss_verifier.py", "GRAZE_MIN_APPROACH_DEG = 5e-3", "GRAZE_MIN_APPROACH_DEG = 5e-2"),
    "nm.band-exclusive": ("near_miss_verifier.py", "test_near_miss_verifier.py", "    return abs(d) <= orb                # INCLUSIVE", "    return abs(d) < orb                # INCLUSIVE"),
    "nm.junction-tout": ("near_miss_verifier.py", "test_near_miss_verifier.py", "kinds = sorted({k for k, t in events if t_in <= t < t_out})", "kinds = sorted({k for k, t in events if t_in <= t <= t_out})"),
    "nm.junction-tin": ("near_miss_verifier.py", "test_near_miss_verifier.py", "kinds = sorted({k for k, t in events if t_in <= t < t_out})", "kinds = sorted({k for k, t in events if t_in < t < t_out})"),
    "nm.no-speed-floor": ("near_miss_verifier.py", "test_near_miss_verifier.py", "    if vmax_dps is not None and vmax_dps < table:", "    if False:"),
    "nm.no-normalised-guard": ("near_miss_verifier.py", "test_near_miss_verifier.py", "    if any(abs(d) > 180.0 + 1e-9 for d in ds):", "    if False:"),
    "nm.compare-skips-clearance": ("near_miss_verifier.py", "test_near_miss_verifier.py", "        if abs(s[\"clearance_deg\"] - w[\"clearance_deg\"]) > CLEARANCE_TOL_DEG:", "        if False:"),
    "nm.compare-skips-junction": ("near_miss_verifier.py", "test_near_miss_verifier.py", "        if (expect[\"kinds\"], expect[\"complete\"]) != (stored_kinds, s.get(\"junction_complete\")):", "        if False:"),
    "nm.edge-unplaced-free": ("near_miss_verifier.py", "test_near_miss_verifier.py", "        elif not (row[\"t_in\"] <= domain[0] or row[\"t_out\"] >= domain[1]):", "        elif False:"),
    "nm.tie-input-order": ("near_miss_verifier.py", "test_near_miss_verifier.py", "key_placed = lambda r: (r[\"t_closest\"], r[\"t_in\"], r[\"t_out\"])", "key_placed = lambda r: (r[\"t_closest\"], 0, 0)"),
    "nm.ni-skip": ("near_miss_verifier.py", "test_near_miss_verifier.py", "        elif layer_on[k] != layer_off[k]:", "        elif False:"),
    "nm.scored-allowed": ("near_miss_verifier.py", "test_near_miss_verifier.py", '    if row.get("score") is not None:', "    if False:"),
    # measuring_report
    "mr.no-start-bound": ("measuring_report.py", "test_measuring_report.py", "    if start < SUBSTRATE_DOMAIN_START:\n        return", "    if False:\n        return"),
    "mr.midnight": ("measuring_report.py", "test_measuring_report.py", "if (u.hour, u.minute, u.second, u.microsecond) != (0, 0, 0, 0):", "if False:"),
    "mr.unknown-agent": ("measuring_report.py", "test_measuring_report.py", "        if r.agent not in ALL_AGENTS:", "        if False:"),
    "mr.blacklist": ("measuring_report.py", "test_measuring_report.py", "bad_versions = sorted(set(view.rule_versions) - ALLOWED_RULE_VERSIONS)", "bad_versions = sorted(set(view.rule_versions) & {'1.2.0'})"),
    "mr.census": ("measuring_report.py", "test_measuring_report.py", "    if missing or extra:", "    if False:"),
    "mr.year-trunc": ("measuring_report.py", "test_measuring_report.py", 'start, basis = date(min(events).year, 1, 1), "first_dated_event"', 'start, basis = min(events), "first_dated_event"'),
    "mr.unbounded": ("measuring_report.py", "test_measuring_report.py", "        if lo_inf or hi_inf or lo is None or hi is None:", "        if False:"),
}
# Equivalent mutants (skipped, with the reason): merging touching day ranges (`a <= merged[-1][1]` -> `<`) leaves every count unchanged;
# ordinal order by t_closest vs t_in is identical for the disjoint stretches of one object.
EQUIVALENT = {"mr.merge-touching": "merging touching day ranges does not change a count"}


def run_suite(suite: str):
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as fh:
        xml_path = fh.name
    proc = subprocess.run([sys.executable, "-m", "pytest", f"tests/l3/gochara/{suite}", "-q", "-p", "no:cacheprovider", f"--junitxml={xml_path}"],
                          cwd=SIDECAR, capture_output=True, text=True)
    return proc.returncode, xml_path


def classify(returncode: int, xml_path: str) -> str:
    try:
        root = ET.parse(xml_path).getroot()
    except (ET.ParseError, FileNotFoundError):
        return "INFRASTRUCTURE (no report)"
    cases = list(root.iter("testcase"))
    if not cases:
        return "COLLECTION-FAILURE (no test ran)"
    failed = [c for c in cases if c.find("failure") is not None]
    errored = [c for c in cases if c.find("error") is not None]
    if errored:
        return f"ERROR (not a clean failure: {len(errored)})"
    def by_assertion(case) -> bool:
        f = case.find("failure")
        text = (f.get("message", "") or "") + "\n" + (f.text or "")
        return "AssertionError" in text or "DID NOT RAISE" in text or "Regex pattern did not match" in text
    if failed and all(by_assertion(c) for c in failed):
        return "CAUGHT"
    if failed:
        return "UNEXPECTED-EXCEPTION (failed, but not by assertion)"
    return "SURVIVED"


def main(argv) -> int:
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    suites = sorted({v[1] for v in MUTANTS.values()})
    for suite in suites:
        rc, xml = run_suite(suite)
        if rc != 0:
            print(f"BASELINE FAILED for {suite}: the harness needs a passing baseline")
            return 2
    print("BASELINE green")
    bad = 0
    for name, (module, suite, old, new) in MUTANTS.items():
        if only and name != only:
            continue
        path = K / module
        original = path.read_text()
        if old not in original:
            print(f"{name}: SETUP-ERROR (the mutated text is not in {module})")
            bad += 1
            continue
        try:
            path.write_text(original.replace(old, new, 1))
            rc, xml = run_suite(suite)
            verdict = classify(rc, xml)
        finally:
            path.write_text(original)
        print(f"{name}: {verdict}")
        bad += verdict != "CAUGHT"
    n = len([1 for k in MUTANTS if not only or k == only])
    print(f"{n - bad}/{n} caught")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
