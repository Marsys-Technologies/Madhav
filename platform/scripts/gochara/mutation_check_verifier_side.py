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
    "nm.band-narrowed": ("near_miss_verifier.py", "test_near_miss_verifier.py", "cr.band_intervals(checked, body, centres, orb_deg, lo, hi)", "cr.band_intervals(checked, body, centres, orb_deg * 0.5, lo, hi)"),
    "nm.bb-prunes-all": ("near_miss_verifier.py", "test_near_miss_verifier.py", "            if lower >= best - tol:", "            if True:"),
    "nm.bb-no-sign-check": ("near_miss_verifier.py", "test_near_miss_verifier.py", "        if dm == 0 or (dm > 0) != (d0 > 0):", "        if False:"),
    "nm.window-empty": ("near_miss_verifier.py", "test_near_miss_verifier.py", "    if not hi > lo:", "    if False:"),
    "nm.proximity-tol": ("near_miss_verifier.py", "test_near_miss_verifier.py", "PROXIMITY_TOL = 1.5e-4", "PROXIMITY_TOL = 1.5e-2"),
    "nm.clearance-tol": ("near_miss_verifier.py", "test_near_miss_verifier.py", "CLEARANCE_TOL_DEG = 1e-3", "CLEARANCE_TOL_DEG = 1e-1"),
    "nm.closest-slack": ("near_miss_verifier.py", "test_near_miss_verifier.py", "CLOSEST_SLACK_SECONDS = 5.0", "CLOSEST_SLACK_SECONDS = 6e6"),
    "nm.cert-tol": ("near_miss_verifier.py", "test_near_miss_verifier.py", "CERT_TOL_DEG = GRAZE_MIN_APPROACH_DEG / 10", "CERT_TOL_DEG = 50.0"),
    "nm.junction-tout": ("near_miss_verifier.py", "test_near_miss_verifier.py", "kinds = sorted({k for k, t in events if t_in <= t < t_out})", "kinds = sorted({k for k, t in events if t_in <= t <= t_out})"),
    "nm.junction-tin": ("near_miss_verifier.py", "test_near_miss_verifier.py", "kinds = sorted({k for k, t in events if t_in <= t < t_out})", "kinds = sorted({k for k, t in events if t_in < t < t_out})"),
    "nm.no-speed-floor": ("near_miss_verifier.py", "test_near_miss_verifier.py", "    if vmax_dps is not None and vmax_dps < table:", "    if False:"),
    "nm.compare-skips-clearance": ("near_miss_verifier.py", "test_near_miss_verifier.py", '        if abs(float(s["clearance_deg"]) - w["clearance_deg"]) > CLEARANCE_TOL_DEG:', "        if False:"),
    "nm.compare-skips-junction": ("near_miss_verifier.py", "test_near_miss_verifier.py", "        if (expect[\"kinds\"], expect[\"complete\"]) != (stored_kinds, s.get(\"junction_complete\")):", "        if False:"),
    "nm.edge-unplaced-free": ("near_miss_verifier.py", "test_near_miss_verifier.py", "        elif not (row[\"t_in\"] <= domain[0] or row[\"t_out\"] >= domain[1]):", "        elif False:"),
    "nm.tie-input-order": ("near_miss_verifier.py", "test_near_miss_verifier.py", "key_placed = lambda r: (r[\"t_closest\"], r[\"t_in\"], r[\"t_out\"])", "key_placed = lambda r: (r[\"t_closest\"], 0, 0)"),
    "nm.ni-skip": ("near_miss_verifier.py", "test_near_miss_verifier.py", "        elif layer_on[k] != layer_off[k]:", "        elif False:"),
    "nm.scored-allowed": ("near_miss_verifier.py", "test_near_miss_verifier.py", '    if row.get("score") is not None:', "    if False:"),
    "ndh.saturn-testimony": ("nd_h_tables.py", "test_nd_h_tables.py", 'SATURN_TESTIMONY = {"spiritual_turn": frozenset({12})}', 'SATURN_TESTIMONY = {"spiritual_turn": frozenset({12, 9})}'),
    "ndh.affected-person": ("nd_h_tables.py", "test_nd_h_tables.py", 'AFFECTED_PERSON = {"parental_event": "father"}', 'AFFECTED_PERSON = {"parental_event": "mother"}'),
    "ndh.gain-band": ("nd_h_tables.py", "test_nd_h_tables.py", "GAIN_BAND = 0.40", "GAIN_BAND = 0.45"),
    "ndh.stamp-dvi-role": ("nd_h_tables.py", "test_nd_h_tables.py", '"dvi":     {"provenance": "uncited_extension", "operator_role": "scored"', '"dvi":     {"provenance": "uncited_extension", "operator_role": "testimony"'),
    "ndh.stamp-class-ruling": ("nd_h_tables.py", "test_nd_h_tables.py", "        elif row.get(\"ruling_ref\") != KB_SOURCE[event_class]:", "        elif False:"),
    "nm.cand-skip": ("near_miss_verifier.py", "test_near_miss_verifier.py", "if tc is None or not any(lo - slack <= tc <= hi + slack for lo, hi in cands):", "if tc is None:"),
    "nm.ordinal-skip": ("near_miss_verifier.py", "test_near_miss_verifier.py", 'if s.get("ordinal") != ordinal_of.get(id(w)):', "if False:"),
    "nm.orb-skip": ("near_miss_verifier.py", "test_near_miss_verifier.py", 'if abs(float(s["orb_deg"]) - float(expected_orb_deg)) > 1e-9:', "if False:"),
    "nm.object-skip": ("near_miss_verifier.py", "test_near_miss_verifier.py", 'if s.get("object_id") != expected_object_id:', "if False:"),
    "nm.finite-position": ("near_miss_verifier.py", "test_near_miss_verifier.py", "if v is None or not math.isfinite(float(v)):", "if v is None:"),
    "nm.limit-unstated": ("near_miss_verifier.py", "test_near_miss_verifier.py", 'if search.get("resolution_limit_seconds") != 60.0:', "if False:"),
    "nm.junction-iterator": ("near_miss_verifier.py", "test_near_miss_verifier.py", "    events = list(events)                                              # materialised ONCE: an iterator would be exhausted by the first row", "    events = events"),
    "nm.finite-row": ("near_miss_verifier.py", "test_near_miss_verifier.py", "    if nonfinite:", "    if False:"),
    "ndh.stamp-rule-version": ("nd_h_tables.py", "test_nd_h_tables.py", 'if row.get("rule_version") != RULE_VERSION:', "if False:"),
    "mr.p4-union": ("measuring_report.py", "test_measuring_report.py", "    return _intersect(jup, sat)", "    return _merge([*jup, *sat])"),
    "mr.role": ("measuring_report.py", "test_measuring_report.py", 'if r.role != "scored":', "if False:"),
    "mr.id-rule": ("measuring_report.py", "test_measuring_report.py", 'if start_of(flag, "event_date") != start_of(full, "event_date"):', "if False:"),
    "mr.birth-vocab": ("measuring_report.py", "test_measuring_report.py", 'or row.get("domain") == "other/birth"', "or False"),
    "mr.ist": ("measuring_report.py", "test_measuring_report.py", "IST = timezone(timedelta(hours=5, minutes=30))", "IST = timezone.utc"),
    "mr.marker-incomplete": ("measuring_report.py", "test_measuring_report.py", "if view.marker_horizon is None or view.marker_schema != MARKER_SCHEMA or not view.marker_digest:", "if False:"),
    "mr.excluded-path": ("measuring_report.py", "test_measuring_report.py", 'if c in EXCLUDED_EIGHT and p in ("P1", "P3", "P4"))', "if c in EXCLUDED_EIGHT)"),
    "nm.refine-floor": ("near_miss_verifier.py", "test_near_miss_verifier.py", "for k in (1, 2, 3):", "for k in ():"),
    "nm.closest-evidence": ("near_miss_verifier.py", "test_near_miss_verifier.py", 'if w.get("closest_certified") is not True or not cands:', "if False:"),
    "nm.null-fields": ("near_miss_verifier.py", "test_near_miss_verifier.py", "        if absent:", "        if False:"),
    "nm.band-budget": ("near_miss_verifier.py", "test_near_miss_verifier.py", "if calls[0] > max_position_calls:", "if False:"),
    "mr.scorer-numerator": ("measuring_report.py", "test_measuring_report.py", "(1 if grid.date_inclusive or l_hi != midnight else 0)", "(1 if l_hi != midnight else 0)"),
    "mr.underivable-log": ("measuring_report.py", "test_measuring_report.py", 'if lel_rows and not info["dates"]:', "if False:"),
    "mr.exclusive-vs-class": ("measuring_report.py", "test_measuring_report.py", '"exclusive_days_vs_class": len(mine - others - _day_set(p4_with, grid))', '"exclusive_days_vs_class": len(mine - others)'),
    "mr.digest-shape": ("measuring_report.py", "test_measuring_report.py", "elif not isinstance(view.marker_digest, str) or not _DIGEST.match(view.marker_digest):", "elif False:"),
    # measuring_report
    "mr.no-start-bound": ("measuring_report.py", "test_measuring_report.py", "    if start < SUBSTRATE_DOMAIN_START:\n        return", "    if False:\n        return"),
    "mr.midnight": ("measuring_report.py", "test_measuring_report.py", "if (u.hour, u.minute, u.second, u.microsecond) != (0, 0, 0, 0):", "if False:"),
    "mr.unknown-agent": ("measuring_report.py", "test_measuring_report.py", "        if r.agent not in ALL_AGENTS:", "        if False:"),
    "mr.blacklist": ("measuring_report.py", "test_measuring_report.py", "bad_versions = sorted(set(view.rule_versions) - ALLOWED_RULE_VERSIONS)", "bad_versions = sorted(set(view.rule_versions) & {'1.2.0'})"),
    "mr.census": ("measuring_report.py", "test_measuring_report.py", "    if missing or extra:", "    if False:"),
    "mr.year-trunc": ("measuring_report.py", "test_measuring_report.py", 'start, basis = date(info["dates"][0].year, 1, 1), "first_dated_event"', 'start, basis = info["dates"][0], "first_dated_event"'),
    "mr.fast-split": ("measuring_report.py", "test_measuring_report.py", 'FAST_AGENTS = frozenset({"sun", "moon", "mars", "mercury", "venus"})', 'FAST_AGENTS = frozenset({"sun", "moon", "mercury", "venus"})'),
    "mr.no-birth-bound": ("measuring_report.py", "test_measuring_report.py", "    if birth_date is not None and start < birth_date:", "    if False:"),
    "mr.no-future-refusal": ("measuring_report.py", "test_measuring_report.py", "        if start > build:", "        if False:"),
    "mr.empty-generation": ("measuring_report.py", "test_measuring_report.py", "    if not view.class_paths_with_rows:", "    if False:"),
    "mr.via-path": ("measuring_report.py", "test_measuring_report.py", "        if r.path not in VIA_PATHS[r.via]:", "        if False:"),
    "mr.status": ("measuring_report.py", "test_measuring_report.py", 'if view.status not in (None, "candidate", "published"):', "if False:"),
    "mr.birth-row": ("measuring_report.py", "test_measuring_report.py", "    if len(births) != 1:", "    if False:"),
    "mr.shape-sensitivity": ("measuring_report.py", "test_measuring_report.py", "    if len(set(readings.values())) > 1:", "    if False:"),
    "mr.unbounded": ("measuring_report.py", "test_measuring_report.py", "        if lo_inf or hi_inf or lo is None or hi is None:", "        if False:"),
}
# EQUIVALENT mutants: run, and REPORTED as such when they survive (a survivor with a stated reason is not a gap; a caught one is fine too).
EQUIVALENT = {
    "ndh.finite-share": ("nd_h_tables.py", "test_nd_h_tables.py", "or not math.isfinite(p4_alone_with_dvi_share)", "or False",
                         "the range check `0 <= share <= 1` already refuses NaN and infinity; isfinite is a belt over braces"),
    "mr.merge-touching": ("measuring_report.py", "test_measuring_report.py", "        if merged and a <= merged[-1][1]:", "        if merged and a < merged[-1][1]:",
                          "merging day ranges that only touch does not change any count"),
}


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
    if returncode != 1 and failed:
        return f"UNEXPECTED-RETURN-CODE ({returncode}: pytest reports 1 only for test failures; 2 is an interrupted or errored run)"
    errored = [c for c in cases if c.find("error") is not None]
    if errored:
        return f"ERROR (not a clean failure: {len(errored)})"
    def by_assertion(case) -> bool:
        """caught only by the STRUCTURED junit failure message, whose prefix is the exception that ended the test: pytest writes `assert <expr>` for a
        failed assert statement, `AssertionError: ...` for a raised one and `Failed: DID NOT RAISE ...` for pytest.raises; any other prefix
        (`TypeError: ...`, `KeyError: ...`) is a raw exception, even if the word AssertionError appears later in the text"""
        msg = case.find("failure").get("message", "") or ""
        return msg.startswith("assert ") or msg == "assert" or msg.startswith("AssertionError") or msg.startswith("Failed: DID NOT RAISE")
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
    for name, (module, suite, old, new, reason) in EQUIVALENT.items():
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
        print(f"{name}: " + (f"EQUIVALENT (survived, as documented: {reason})" if verdict == "SURVIVED" else verdict))
        bad += verdict not in ("SURVIVED", "CAUGHT")
    n = len([1 for k in MUTANTS if not only or k == only])
    print(f"{n - bad}/{n} caught")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
