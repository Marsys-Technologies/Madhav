"""WP10 step-6 — the episode-enumeration driver (E-018 closure, ADK-0011(i)).

`scripts/kala_gochara_cutover/step06_enumerate_episodes.py` produces the
`--episodes-json` / `--coverage-json` payloads step06_candidate_build.py
consumes. What this file proves:

  * WP1 golden conformance — fixtures/wp1_target_resolution.json (v1.1, 22
    cases) resolved through the driver's resolve_targets against a facts map
    built from each case's chart_facts inputs: point vs interval kind, sign
    spans, honest unavailable/unqualified states, agent qualifiers, and the
    writer-R-1 negative sensitive-check discipline (zero targets);
  * enumeration semantics on synthetic curves (no DB, refine=False — the
    spline reproduces the cubic exactly): the M-1 orb regime (conjunction +
    drishti at --orb-deg 5.0 with the §7 orb_source row id; returns pinned at
    the table's 0.5°), return owner-gating, N-14 (Rahu casts no dṛṣṭi), the
    three boundary relations attached per point target, interval targets
    yielding sign_ingress only (M-5), mechanism_node/M-6 agent restriction;
  * honesty guards: kernel episodes with t_exact=None are excluded and
    counted (1081 t_exact NOT NULL), truncated_at_horizon='both' maps to
    NULL (WP1 §3.1 CHECK), every emitted dict carries tz-aware UTC instants
    and the ledger _normalize_episode shape;
  * end-to-end on the disposable WP6 Postgres (NOT_RUN when unreachable):
    §12.9 overlay-freshness gate (exit 7 on stale, 0 on fresh), the
    produced JSON feeding step06_candidate_build.py to real candidate rows;
  * ADK-0020/ADK-0021/ADK-0022 dedupe (one ledger row per pinned WP1 §3.2
    physical contact): weight-order survival, weight-tie → lexicographic
    target_ref, deeper ties surfaced as map defects, citation-DIVERGENT
    groups carrying NULL with disclosure and every group citation
    recoverable in dropped_refs (ADK-0022 null-and-disclose; agreeing
    citations keep the survivor's), divergence in any other field refusing
    (DedupeRefusal, exit 5),
    _map_weight stripped from the payload, dropped-refs artifact content
    (incl. dropped citations), and the mandatory e2e regression — two map
    rows on one physical target yield one emitted row and one ledger row per
    contact_id.

DB tests use ONLY the disposable WP6 Postgres (env WP6_LEDGER_DSN, default
postgresql://wp6:local@localhost:55433/wp6) and skip NOT_RUN otherwise —
never a fallback DSN. Real-ephemeris tests run under the conftest's F-14
checksum gate (requires_swieph).
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.gochara_kernel import arcs, episodes as gk_episodes  # noqa: E402
from services.gochara_kernel import convention as gk_convention  # noqa: E402
from services.ka_gochara_resonance import writer as resonance_writer  # noqa: E402

from .conftest import (  # noqa: E402
    EPHE_PATH,
    WP6_DSN,
    WP6_DROP_SQL,
    WP6_MIGRATION_1072,
    WP6_MIGRATION_1087,
    requires_swieph,
)

DRIVER_PATH = (
    Path(__file__).resolve().parents[3]
    / "scripts" / "kala_gochara_cutover" / "step06_enumerate_episodes.py"
)
STEP06_PATH = DRIVER_PATH.parent / "step06_candidate_build.py"
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "wp1_target_resolution.json"


def _load_driver():
    spec = importlib.util.spec_from_file_location("step06_enumerate_episodes", DRIVER_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # dataclass resolution needs the module registered
    spec.loader.exec_module(mod)
    return mod


drv = _load_driver()

UTC = timezone.utc
SYNTHETIC_TOL_ARCSEC = 1e-7  # spline reproduces the cubic exactly (wp3a precedent)


# ── synthetic-curve harness (same shape as test_wp3a_kernel) ─────────────────


def _daily_knots(start: date, end: date, curve):
    jds, lons = [], []
    d = start
    while d <= end:
        import swisseph as swe

        jd = swe.julday(d.year, d.month, d.day, 0.0)
        jds.append(jd)
        lons.append(curve(jd) % 360.0)
        d = date.fromordinal(d.toordinal() + 1)
    return jds, lons


def _index(body: str, start: date, end: date, curve):
    jds, lons = _daily_knots(start, end, curve)
    return arcs.build_arc_index(body, jds, lons, tolerance_arcsec=SYNTHETIC_TOL_ARCSEC)


def _jd(y, m, d):
    import swisseph as swe

    return swe.julday(y, m, d, 0.0)


def _point_target(longitude: float, owner: str, target_type: str = "karaka",
                  target_ref: str = "X") -> drv.ResolvedTarget:
    return drv.ResolvedTarget(
        event_class="marriage", target_type=target_type, target_ref=target_ref,
        qualifier=None, classical_citation=None, uncited_extension=False,
        state="resolved", kind="point", longitude_deg=longitude,
        target_sign="Libra", owner_graha=owner,
    )


def _interval_target(span, agent=None, target_type="bhava",
                     target_ref="4") -> drv.ResolvedTarget:
    return drv.ResolvedTarget(
        event_class="property_acquisition", target_type=target_type,
        target_ref=target_ref, qualifier=f"agent:{agent}" if agent else None,
        classical_citation=None, uncited_extension=False, state="resolved",
        kind="interval", span_deg=span, target_sign="Scorpio", agent=agent,
    )


BACKEND = {"backend": "n/a (synthetic)"}


# ── WP1 golden fixture → ResolutionFacts mapper ──────────────────────────────


def _facts_from_case(case: dict) -> tuple[dict, drv.ResolutionFacts]:
    """Build (map_row, ResolutionFacts) from one fixture case's inputs.

    Mirrors what the live fetch SQL reads (fetch_resolution_facts):
    graha_position longitude/sign rows, graha_sign_attributes sign_num rows
    (occupied signs — graha_position 'sign' text rows are folded in too, since
    the L1 store carries both and the M-6 operand fetch reads sign_num),
    arudha_pada sign rows, sensitive_degree_check rows, yoga firings, and the
    nakshatra/gulika-mandi operands. sign_lords is the writer's classical
    table (production reads reference_signs, same content).

    Fixture-mapping notes (NOT driver logic):
      * the `arudha`/`sensitive_degree` cases use symbolic target_refs that
        are not the fact_id of the single sign/check row; production rows
        carry the fact_id, so the single row of that category is aliased to
        the target_ref here;
      * `neg_sensitive_check_zero_targets` simulates writer R-1: the
        negative-result check produces ZERO map rows, so the map row itself
        is dropped (nothing is stored, nothing to resolve).
    """
    inputs = case["inputs"]
    row = dict(inputs["resonance_target"])
    row.setdefault("target_qualifier", None)
    row.setdefault("classical_citation", None)
    row.setdefault("uncited_extension", False)
    # arudha / bhava_arudha rows are the writer's own synthesis (uncited).
    if row["target_type"] in ("arudha", "bhava_arudha"):
        row["uncited_extension"] = True
    # M-6 qualifiers and citations are stamped by the writer from the formula
    # registry (derived_points.YAMAKANTAKA_FORMULAS / MANDI_DISTANCE_*).
    if row["target_type"] == "gulika_mandi_distance":
        row["target_qualifier"] = row["target_qualifier"] or \
            f"agent:{resonance_writer.MANDI_DISTANCE_AGENT}"
        row["classical_citation"] = row["classical_citation"] or \
            resonance_writer.MANDI_DISTANCE_CITATION
    if row["target_type"] == "yamakantaka_difference":
        formula = next(
            f for f in drv.YAMAKANTAKA_FORMULAS if f["ref"] == row["target_ref"])
        row["target_qualifier"] = row["target_qualifier"] or f"agent:{formula['agent']}"
        row["classical_citation"] = row["classical_citation"] or formula["citation"]

    facts = drv.ResolutionFacts(sign_lords=dict(resonance_writer._CLASSICAL_SIGN_LORDS))
    sign_of = drv.sign_num_of
    check_rows, arudha_sign_rows = [], []
    negative_check_seen = False
    for f in inputs.get("chart_facts", []):
        cat, subj, key = f["fact_category"], f["fact_subject"], f["fact_key"]
        if cat == "graha_position":
            if key == "longitude_sidereal":
                slot = facts.positions.setdefault(subj, {})
                slot["longitude"] = float(f["fact_value_num"])
                if f.get("fact_id"):
                    slot["fact_id"] = f["fact_id"]
                    facts.fact_longitudes[f["fact_id"]] = float(f["fact_value_num"])
                    facts.fact_subjects[f["fact_id"]] = subj
            elif key == "sign":
                slot = facts.positions.setdefault(subj, {})
                slot["sign"] = f["fact_value_text"]
                n = sign_of(f["fact_value_text"])
                if n is not None and subj not in facts.graha_sign_nums:
                    facts.graha_sign_nums[subj] = n
        elif cat == "graha_sign_attributes" and key == "sign_num":
            facts.graha_sign_nums[subj] = int(f["fact_value_num"])
        elif cat == "arudha_pada" and key == "sign":
            arudha_sign_rows.append(f)
            facts.arudha_signs_by_fact[f["fact_id"]] = f["fact_value_text"]
            facts.arudha_signs_by_subject[subj] = f["fact_value_text"]
        elif cat == "sensitive_degree_check":
            value = str(f.get("fact_value_text") or "")
            positives = resonance_writer._POSITIVE_SENSITIVE_VALUES.get(
                key, frozenset())
            if value not in positives:
                negative_check_seen = True  # R-1: nothing is stored
                continue
            check_rows.append(f)
            facts.sensitive_checks[f["fact_id"]] = subj
        elif cat == "sensitive_point_gulika_mandi" and key == "sign":
            facts.gulika_mandi_signs[subj] = f["fact_value_text"]
        elif cat == "panchanga_nakshatra_moon" and key == "number":
            facts.moon_nakshatra_id = int(f["fact_value_num"])
    for y in inputs.get("ga_yoga_firings", []):
        if y.get("fired"):
            facts.yoga_firings[y["yoga_canonical_id"]] = [
                str(fid) for fid in (y.get("constituent_fact_ids") or [])]

    # Fixture aliasing (see docstring): symbolic target_ref → the single
    # stored row of the category the ref names.
    tt = row["target_type"]
    if tt == "arudha" and row["target_ref"] not in facts.arudha_signs_by_fact \
            and len(arudha_sign_rows) == 1:
        facts.arudha_signs_by_fact[row["target_ref"]] = \
            arudha_sign_rows[0]["fact_value_text"]
    if tt == "sensitive_degree" and row["target_ref"] not in facts.sensitive_checks \
            and len(check_rows) == 1:
        facts.sensitive_checks[row["target_ref"]] = check_rows[0]["fact_subject"]

    rows = [] if (negative_check_seen and not check_rows) else [row]
    return rows, facts


def _assert_golden(case_id: str, case: dict) -> None:
    rows, facts = _facts_from_case(case)
    out = drv.resolve_targets(rows, facts)
    resolved = [t for t in out if t.state == "resolved"]
    unresolved = [t for t in out if t.state != "resolved"]
    expected = case["expected"]
    assert len(resolved) == expected["target_count"], (
        f"{case_id}: {len(resolved)} resolved != {expected['target_count']}; "
        f"states={[t.state for t in out]}")
    for got, want in zip(resolved, expected["targets"]):
        assert got.target_type == want["target_type"]
        assert got.kind == want["object_kind"]
        if "target_longitude_deg" in want:
            assert got.longitude_deg == pytest.approx(want["target_longitude_deg"])
        if "span_deg" in want:
            assert tuple(got.span_deg) == tuple(want["span_deg"])
        if "target_sign" in want:
            assert got.target_sign == want["target_sign"]
        if "target_fact_id" in want:
            assert got.target_fact_id == want["target_fact_id"]
        if "target_qualifier" in want:
            assert got.qualifier == want["target_qualifier"]
        if "classical_citation" in want:
            assert got.classical_citation == want["classical_citation"]
        if "uncited_extension" in want:
            assert got.uncited_extension == want["uncited_extension"]
        for bad in want.get("forbidden_point_longitudes", []):
            assert got.longitude_deg != bad
    for got, want in zip(unresolved, expected.get("unresolved", [])):
        assert got.target_type == want["target_type"]
        assert got.target_ref == want["target_ref"]
        assert got.state == want["target_resolution_state"]


def test_wp1_golden_target_resolution_all_cases():
    fixture = json.loads(FIXTURE_PATH.read_text())
    assert len(fixture["cases"]) == 22  # v1.1: 8 base + 4 negatives + 10 M-6
    for case_id, case in fixture["cases"].items():
        _assert_golden(case_id, case)


# ── enumeration on synthetic curves ──────────────────────────────────────────

H0 = None  # set per test via _jd


def test_orb_regime_return_gating_and_boundary_attachment():
    """M-1 orb regime: conjunction/drishti at --orb-deg (5.0) with the §7
    orb_source row id; return pinned at the table's 0.5° and only for the
    target's owning graha; the three boundary relations attach per point
    target (the _moon_on_demand precedent)."""
    h0 = _jd(2026, 1, 1)

    def curve(jd):
        return 100.0 + 0.25 * (jd - h0)  # sweeps 100 → ~191 inside the horizon

    index = _index("Saturn", date(2025, 12, 1), date(2027, 3, 1), curve)
    horizon = (_jd(2026, 1, 1), _jd(2027, 1, 1))
    targets = [
        # conjunction at 180 (t=320d) + 3rd-aspect drishti level 120 (t=80d) —
        # aspect direction is the forward count (spec §6.2 inv 6): Saturn's
        # 3rd aspect from λ falls at λ+60, so the aspect lands on target 180
        # with the body at (180 − 60) mod 360 = 120;
        # owner Mars → no return
        _point_target(180.0, "Mars", "karaka", "Mars"),
        # owner Saturn → return present at 0.5°
        _point_target(150.125, "Saturn", "sensitive_degree", "chk"),
    ]
    eps, stats = drv.enumerate_body(
        index, "Saturn", targets, horizon, 5.0, BACKEND,
        ephe_path=None, refine=False)

    by_rel = {}
    for e in eps:
        by_rel.setdefault((e["target_ref"], e["relation"]), []).append(e)

    conj = by_rel[("Mars", "conjunction")]
    assert len(conj) == 1
    assert conj[0]["orb_max_deg"] == 5.0
    assert conj[0]["orb_source"] == "orb_conj_slow"
    assert conj[0]["aspect_deg"] == 0

    drishti = by_rel[("Mars", "drishti_contact")]
    assert {e["aspect_deg"] for e in drishti} == {60.0}  # Saturn's 3rd aspect
    assert all(e["orb_max_deg"] == 5.0 for e in drishti)
    assert all(e["orb_source"] == "orb_drishti_slow" for e in drishti)

    # return only for the owning graha
    assert ("Mars", "return") not in by_rel
    ret = by_rel[("chk", "return")]
    assert len(ret) == 1
    assert ret[0]["orb_max_deg"] == 0.5
    assert ret[0]["orb_source"] == "orb_return_slow"
    # ...and it is narrower than the conjunction band on the same longitude
    assert by_rel[("chk", "conjunction")][0]["orb_max_deg"] == 5.0
    assert ret[0]["t_in"] > by_rel[("chk", "conjunction")][0]["t_in"]

    # boundary relations attach per point target, boundary-exact
    for ref in ("Mars", "chk"):
        for rel in ("sign_ingress", "nakshatra_ingress", "kakshya_cell_crossing"):
            assert by_rel.get((ref, rel)), f"{ref}: no {rel} episodes attached"
            assert all(e["orb_max_deg"] == 0.0 and e["orb_source"] == "orb_ingress"
                       for e in by_rel[(ref, rel)])

    # every emitted dict carries tz-aware UTC instants and the ledger shape
    for e in eps:
        assert e["t_in"].tzinfo is not None and e["t_exact"].tzinfo is not None
        assert e["t_exact"].utcoffset().total_seconds() == 0
        assert e["independence_group"].startswith("sha256:")
        assert e["target_resolution_state"] == "resolved"
        assert e["epistemic_class"] == "observed_event"
        assert e["operator_role"] == "kernel"
    # the two targets share a body but are distinct physical targets: their
    # conjunction groups must differ (H-6 physical hash)
    assert conj[0]["independence_group"] != by_rel[("chk", "conjunction")][0]["independence_group"]
    # searched-relation ledger for coverage
    assert set(stats["searched"]["karaka"]) >= {
        "conjunction", "drishti_contact", "sign_ingress"}
    assert "return" not in stats["searched"]["karaka"]  # Mars is not the owner
    assert "return" in stats["searched"]["sensitive_degree"]


def test_n14_rahu_casts_no_drishti():
    h0 = _jd(2026, 1, 1)

    def curve(jd):
        return 250.0 - 0.05 * (jd - h0)  # retrograde mean node, 250 → 232

    index = _index("Rahu", date(2025, 12, 1), date(2027, 1, 1), curve)
    horizon = (_jd(2026, 1, 1), _jd(2026, 12, 31))
    assert gk_convention.drishti_angles("Rahu") == ()  # N-14 kernel pin
    eps, stats = drv.enumerate_body(
        index, "Rahu", [_point_target(240.0, "Rahu")], horizon, 5.0, BACKEND,
        ephe_path=None, refine=False)
    assert not [e for e in eps if e["relation"] == "drishti_contact"]
    assert [e for e in eps if e["relation"] == "conjunction"]
    assert [e for e in eps if e["relation"] == "return"]  # owner match


def test_interval_target_residence_and_agent_restriction():
    """M-5: interval targets yield sign_ingress episodes only (never point
    contacts); mechanism_node / M-6 spans enumerate for the named agent only."""
    h0 = _jd(2026, 1, 1)

    def curve(jd):
        return 205.0 + 0.1 * (jd - h0)  # crosses 210 at t=50d, 240 far outside

    index = _index("Saturn", date(2025, 12, 1), date(2027, 1, 1), curve)
    horizon = (_jd(2026, 1, 1), _jd(2027, 1, 1))
    bhava = _interval_target((210.0, 240.0), target_type="bhava", target_ref="4")
    mech = _interval_target((210.0, 240.0), agent="Jupiter",
                            target_type="mechanism_node",
                            target_ref="jupiter:double_transit:h4")
    m6 = _interval_target((270.0, 300.0), agent="Saturn",
                          target_type="gulika_mandi_distance",
                          target_ref="mandi_sign_distance_from_8L")
    eps, stats = drv.enumerate_body(
        index, "Saturn", [bhava, mech, m6], horizon, 5.0, BACKEND,
        ephe_path=None, refine=False)

    bhava_eps = [e for e in eps if e["target_ref"] == "4"]
    assert {e["relation"] for e in bhava_eps} == {"sign_ingress"}
    assert len(bhava_eps) == 1
    assert bhava_eps[0]["orb_max_deg"] == 0.0
    assert bhava_eps[0]["t_exact"].date().isoformat() == "2026-02-20"  # t=50d
    # mechanism_node names Jupiter: Saturn never enumerates it
    assert not [e for e in eps if e["target_ref"] == "jupiter:double_transit:h4"]
    assert "mechanism_node" not in stats["searched"]
    # M-6 span [270,300): never entered in the window → no episodes, honest
    assert not [e for e in eps if e["target_ref"] == "mandi_sign_distance_from_8L"]

    # the same mechanism_node span enumerated FOR Jupiter attaches
    jeps, _ = drv.enumerate_body(
        index, "Jupiter", [mech], horizon, 5.0, BACKEND,
        ephe_path=None, refine=False)
    # NOTE: the index is Saturn's curve; passing body="Jupiter" only relabels
    # the episodes (the solver reads the index). This call proves the agent
    # gate, not Jupiter geometry.
    assert [e for e in jeps if e["relation"] == "sign_ingress"]


def test_episodes_without_exact_are_excluded_and_counted():
    """1081 t_exact NOT NULL: an episode whose exact crossing falls outside
    the horizon (orb band entered, exact never reached) is NOT persistable —
    counted in stats['episodes_without_exact'], absent from the payload."""
    h0 = _jd(2026, 1, 1)

    def curve(jd):
        return 194.8 + 0.15 * (jd - h0)  # band entry t≈1.3d; exact at t≈34.7d

    index = _index("Saturn", date(2025, 12, 15), date(2026, 3, 15), curve)
    horizon = (_jd(2026, 1, 1), _jd(2026, 1, 31))  # exact (Feb 4) outside
    eps, stats = drv.enumerate_body(
        index, "Saturn", [_point_target(200.0, "Saturn")], horizon, 5.0, BACKEND,
        ephe_path=None, refine=False)
    assert stats["episodes_without_exact"] == 1
    assert all(e["t_exact"] is not None for e in eps)
    assert not [e for e in eps if e["relation"] == "conjunction"]
    # the return band (0.5°) is narrower; its exact is the same root → also excluded
    assert not [e for e in eps if e["relation"] == "return"]


def test_truncated_both_maps_to_null_and_jd_round_trip():
    """WP1 §3.1 CHECK: kernel 'both' (episode spans the whole horizon) is not
    a storable value; the dict carries NULL. jd_to_dt must round-trip the
    kernel's float JDs to exact tz-aware UTC datetimes."""
    assert drv.jd_to_dt(_jd(2026, 3, 6)) == datetime(2026, 3, 6, tzinfo=UTC)
    h0 = _jd(2026, 1, 1)

    def curve(jd):
        return 199.9 + 0.005 * (jd - h0)  # exact ~t+20d; ±5° band never exits

    index = _index("Saturn", date(2025, 12, 1), date(2026, 4, 1), curve)
    horizon = (_jd(2026, 1, 1), _jd(2026, 1, 31))
    eps = gk_episodes.solve_episodes(
        index, "Saturn", "conjunction", 200.0, horizon, "orb_conj_slow",
        ephe_path=None, refine=False, orb_override_deg=5.0)
    assert len(eps) == 1 and eps[0].truncated_at_horizon == "both"
    d = drv._episode_to_dict(eps[0], _point_target(200.0, "Saturn"), BACKEND)
    assert d["truncated_at_horizon"] is None
    assert d["t_in"] == datetime(2026, 1, 1, tzinfo=UTC)  # clipped, exact
    assert d["t_out"] == datetime(2026, 1, 31, tzinfo=UTC)


def test_coverage_rows_shape_and_invariants():
    """build_coverage_rows emits the ledger write_coverage shape: full state
    counts including resolved, targets_requested consistent, partitions
    sorted, horizon carried as text."""
    targets = [
        _point_target(200.0, "Saturn", "karaka", "Venus"),
        drv.ResolvedTarget(
            event_class="career_advancement", target_type="yoga_constituent",
            target_ref="chatra_yoga", qualifier=None, classical_citation=None,
            uncited_extension=False, state="unavailable"),
        _interval_target((210.0, 240.0), target_type="bhava", target_ref="4"),
    ]
    searched = {
        "Saturn": {"karaka": ["conjunction", "drishti_contact", "return",
                              "sign_ingress", "nakshatra_ingress",
                              "kakshya_cell_crossing"]},
        "Jupiter": {"bhava": ["sign_ingress"]},
    }
    rows = drv.build_coverage_rows(
        "wp1-synth-x", "4.0", targets, searched, "[2026-01-01,2027-01-01)",
        "sha256:test", BACKEND)
    assert [r["partition_key"] for r in rows] == sorted(r["partition_key"] for r in rows)
    by_key = {r["partition_key"]: r for r in rows}
    sat = by_key["saturn:karaka"]
    assert sat["targets_requested"] == 1
    assert sat["target_resolution_state_counts"] == {"resolved": 1}
    assert sat["requested_horizon"] == "[2026-01-01,2027-01-01)"
    jup = by_key["jupiter:bhava"]
    assert jup["target_resolution_state_counts"] == {"resolved": 1}
    assert jup["relations_searched"] == ["sign_ingress"]


# ── disposable-DB end-to-end ─────────────────────────────────────────────────

E2E_CHART = "22222222-3333-4444-5555-666666666666"

MIGRATION_1082 = (
    Path(__file__).resolve().parents[4]
    / "migrations/1082_nirmana_l3_vedha_moorti_stamp_columns.sql"
)

# Overlay + reference DDL lifted from test_wp9_stamp_columns.BASE_DDL (the
# real migration-525/526 shapes), minus its chart_facts/ephemeris_daily
# (this fixture needs fact_value_text on chart_facts and no ephemeris).
from .test_wp9_stamp_columns import BASE_DDL as _WP9_BASE_DDL  # noqa: E402

E2E_EXTRA_DDL = """
ALTER TABLE chart_facts ADD COLUMN IF NOT EXISTS fact_value_text TEXT;

CREATE TABLE IF NOT EXISTS reference_signs (
  sign_id SMALLINT PRIMARY KEY CHECK (sign_id BETWEEN 1 AND 12),
  lord TEXT NOT NULL
);

DROP TABLE IF EXISTS ga_yoga_firings;
CREATE TABLE ga_yoga_firings (
  id SERIAL PRIMARY KEY,
  chart_id UUID NOT NULL,
  ayanamsha_id TEXT NOT NULL,
  yoga_canonical_id TEXT NOT NULL,
  fired BOOLEAN NOT NULL DEFAULT TRUE,
  constituent_fact_ids JSONB,
  UNIQUE (chart_id, ayanamsha_id, yoga_canonical_id)
);

DROP TABLE IF EXISTS gochara_resonance_map;
CREATE TABLE gochara_resonance_map (
  id BIGSERIAL PRIMARY KEY,
  chart_id UUID NOT NULL,
  event_class TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_ref TEXT NOT NULL,
  weight NUMERIC NOT NULL,
  classical_citation TEXT,
  uncited_extension BOOLEAN NOT NULL DEFAULT FALSE,
  source_rule_id INTEGER,
  computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  target_resolution_state TEXT NOT NULL DEFAULT 'resolved'
    CHECK (target_resolution_state IN ('resolved','unavailable','unqualified')),
  target_qualifier TEXT,
  UNIQUE(chart_id, event_class, target_type, target_ref)
);
"""


def _wp6_reachable() -> bool:
    import psycopg

    try:
        with psycopg.connect(WP6_DSN, connect_timeout=3):
            return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def wp6_enum_schema():
    """The step-6 producer/consumer pair on the disposable WP6 Postgres:
    overlay tables (real 525/526 DDL + 1082), reference_signs, chart_facts,
    ga_yoga_firings, gochara_resonance_map, and the 1081/1087 ledger the
    consumer writes. NOT_RUN when the disposable DB is unreachable."""
    if not _wp6_reachable():
        pytest.skip("NOT_RUN: disposable WP6 database unreachable")
    import psycopg

    conn = psycopg.connect(WP6_DSN, autocommit=True)
    conn.execute(_WP9_BASE_DDL)
    conn.execute(MIGRATION_1082.read_text())
    conn.execute(E2E_EXTRA_DDL)
    conn.execute(WP6_DROP_SQL)
    conn.execute(WP6_MIGRATION_1072.read_text())
    conn.execute(WP6_MIGRATION_1087.read_text())
    _seed_e2e(conn)
    conn.close()
    return True


def _seed_e2e(conn) -> None:
    """One coherent synthetic chart (LAGNA Cancer): a point target per point
    type, interval targets incl. mechanism_node and both M-6 formulas, and
    overlay rows stamped with the CURRENT upstream fingerprints (fresh)."""
    import psycopg

    ay = resonance_writer._CANONICAL_AYANAMSHA
    facts = [
        # (fact_id, subject, category, key, num, text)
        ("e2e.lagna.signnum", "LAGNA", "graha_sign_attributes", "sign_num", 4, None),
        ("e2e.sat.signnum", "SAT", "graha_sign_attributes", "sign_num", 2, None),
        ("e2e.mar.signnum", "MAR", "graha_sign_attributes", "sign_num", 8, None),
        ("e2e.moon.signnum", "MOON", "graha_sign_attributes", "sign_num", 3, None),
        ("e2e.ven.lon", "VEN", "graha_position", "longitude_sidereal", 300.0, None),
        ("e2e.ven.sign", "VEN", "graha_position", "sign", None, "Capricorn"),
        ("e2e.sat.lon", "SAT", "graha_position", "longitude_sidereal", 287.25, None),
        ("e2e.sat.sign", "SAT", "graha_position", "sign", None, "Taurus"),
        ("e2e.moon.lon", "MOON", "graha_position", "longitude_sidereal", 10.5, None),
        ("e2e.jup.lon", "JUP", "graha_position", "longitude_sidereal", 11.0, None),
        ("e2e.a7.sign", "A7", "arudha_pada", "sign", None, "Gemini"),
        ("e2e.ba7.sign", "ARUDHA_A7", "arudha_pada", "sign", None, "Gemini"),
        ("e2e.sat.check", "SAT", "sensitive_degree_check", "kartari", None, "papa_kartari"),
        ("e2e.mandi.sign", "MANDI", "sensitive_point_gulika_mandi", "sign", None, "Virgo"),
        ("e2e.yama.sign", "YAMAKANTAKA", "sensitive_point_gulika_mandi", "sign", None, "Leo"),
        ("e2e.moon.nak", "NAKSHATRA_MOON_BIRTH", "panchanga_nakshatra_moon", "number", 1, None),
    ]
    with conn.cursor() as cur:
        cur.execute("DELETE FROM chart_facts WHERE chart_id = %s", (E2E_CHART,))
        cur.executemany(
            "INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id, fact_category,"
            " fact_subject, fact_key, fact_value_num, fact_value_text)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            [(fid, E2E_CHART, ay, cat, subj, key, num, text)
             for fid, subj, cat, key, num, text in facts],
        )
        cur.execute("DELETE FROM reference_signs")
        cur.executemany(
            "INSERT INTO reference_signs (sign_id, lord) VALUES (%s,%s)",
            sorted(resonance_writer._CLASSICAL_SIGN_LORDS.items()),
        )
        cur.execute("DELETE FROM ga_yoga_firings WHERE chart_id = %s", (E2E_CHART,))
        cur.execute(
            "INSERT INTO ga_yoga_firings (chart_id, ayanamsha_id, yoga_canonical_id,"
            " fired, constituent_fact_ids) VALUES (%s,%s,%s,true,%s)",
            (E2E_CHART, ay, "gajakesari_yoga",
             json.dumps(["e2e.moon.lon", "e2e.jup.lon"])),
        )
        # reference rows the freshness fingerprints digest
        cur.execute("DELETE FROM bg_transit_rules")
        cur.execute("DELETE FROM bg_vedha_malefic_scale")
        cur.execute("DELETE FROM bg_transit_moorti")
        cur.execute(
            "INSERT INTO bg_transit_rules (rule_type, graha, primary_house,"
            " vedha_house, phala, classical_citation) VALUES"
            " ('favourable','sun',3,9,'gain','Phaladipika Adh. XXVI, Sloka 3')")
        cur.execute(
            "INSERT INTO bg_vedha_malefic_scale (malefic_count, effect_grade,"
            " effect_description, source_citation) VALUES (1,'agitation','x','PG353')")
        cur.execute(
            "INSERT INTO bg_transit_moorti (nakshatra_offset, moorti_name,"
            " quality_tier, phala_brief, classical_citation) VALUES"
            " (1,'swarna',1,'x','Phaladeepika Ch.26')")
        map_rows = [
            ("marriage", "karaka", "Venus", 0.9, None, False, "resolved", None),
            # ADK-0020 e2e: a second map row (another event_class) resolving
            # to the SAME physical target (VEN longitude fact) at lower weight
            # — the driver must dedupe it to one row per physical contact.
            ("career_advancement", "karaka", "Venus", 0.6, None, False,
             "resolved", None),
            ("marriage", "lord", "7L", 0.8, None, False, "resolved", None),
            ("property_acquisition", "bhava", "8", 0.7, None, False, "resolved", None),
            ("career_advancement", "mechanism_node", "jupiter:double_transit:h11",
             0.5, "test-rule", False, "resolved", None),
            ("illness_acute", "sensitive_degree", "e2e.sat.check", 0.5, None, True,
             "resolved", None),
            ("wealth_gain", "yoga_constituent", "gajakesari_yoga", 0.7, None, True,
             "resolved", None),
            ("wealth_gain", "arudha", "e2e.a7.sign", 0.6, None, True, "resolved", None),
            ("marriage", "bhava_arudha", "BHAVA_ARUDHA_A7", 0.6, None, True,
             "resolved", None),
            ("bereavement", "gulika_mandi_distance", "mandi_sign_distance_from_8L",
             0.5, "PG220:C1 śl.26", False, "resolved", "agent:Saturn"),
            ("bereavement", "yamakantaka_difference", "sun_minus_yamakantaka",
             0.5, "PG214:C1 śl.7", False, "resolved", "agent:Jupiter"),
        ]
        cur.execute("DELETE FROM gochara_resonance_map WHERE chart_id = %s", (E2E_CHART,))
        cur.executemany(
            "INSERT INTO gochara_resonance_map (chart_id, event_class, target_type,"
            " target_ref, weight, classical_citation, uncited_extension,"
            " target_resolution_state, target_qualifier)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [(E2E_CHART, *r) for r in map_rows],
        )

    # Overlay rows stamped FRESH against the seeded reference tables.
    from services.ka_vedha_gochara.freshness import (
        current_fingerprint, current_moorti_fingerprint)

    vedha_fp = current_fingerprint(conn)
    moorti_fp = current_moorti_fingerprint(conn)
    with conn.cursor() as cur:
        cur.execute("DELETE FROM kala_vedha_gochara WHERE chart_id = %s", (E2E_CHART,))
        cur.execute("DELETE FROM kala_moorti_nirnaya WHERE chart_id = %s", (E2E_CHART,))
        cur.execute(
            "INSERT INTO kala_vedha_gochara (chart_id, ayanamsha_id, vedha_kind,"
            " graha, window_start, window_end, start_truncated, end_truncated,"
            " janma_reference_fact_id, classical_citation, uncited_extension,"
            " grid_basis, detail, formula_version) VALUES"
            " (%s,%s,'house_vedha','Sun',%s,%s,false,false,%s,%s,false,NULL,%s,'e2e')",
            (E2E_CHART, ay, date(2026, 1, 1), date(2026, 2, 1), "e2e.moon.lon",
             "Phaladipika Adh. XXVI, Sloka 3",
             json.dumps({"upstream_fingerprint": vedha_fp})),
        )
        cur.execute(
            "INSERT INTO kala_moorti_nirnaya (chart_id, ayanamsha_id, graha,"
            " target_sign_idx, target_sign_name, window_start, window_end,"
            " start_truncated, end_truncated, moorti_computed,"
            " janma_nakshatra_idx, janma_nakshatra_fact_id, formula_version,"
            " upstream_fingerprint) VALUES"
            " (%s,%s,'Sun',2,'Gemini',%s,%s,false,false,false,0,%s,'e2e',%s)",
            (E2E_CHART, ay, date(2026, 1, 1), date(2026, 2, 1), "e2e.moon.nak",
             json.dumps(moorti_fp)),
        )
    conn.commit()


def _run_driver(tmp_path, *extra):
    return subprocess.run(
        [sys.executable, str(DRIVER_PATH), "--dsn", WP6_DSN,
         "--chart-id", E2E_CHART,
         "--horizon-start", "2026-01-01T00:00:00+00:00",
         "--horizon-end", "2026-04-01T00:00:00+00:00",
         "--ephe-path", EPHE_PATH,
         "--episodes-out", str(tmp_path / "eps.json"),
         "--coverage-out", str(tmp_path / "cov.json"), *extra],
        capture_output=True, text=True, timeout=600)


@requires_swieph
def test_end_to_end_enumerate_and_consume(wp6_enum_schema, tmp_path):
    """Fresh overlays → exit 0; the produced JSON feeds step06_candidate_build
    to real candidate rows (the producer/consumer pair contract, E-018)."""
    r = _run_driver(tmp_path)
    assert r.returncode == 0, r.stderr
    report = json.loads(r.stdout)
    assert report["chart_id"] == E2E_CHART
    assert report["candidate_flags"]["orb_max_deg"] == 5.0
    assert report["candidate_flags"]["activity_shape"] == "linear_no_box"
    assert report["upstream_fingerprints"]["house_vedha"]
    assert report["upstream_fingerprints"]["moorti"]
    assert report["target_resolution_state_counts"].get("resolved", 0) >= 10
    assert report["episodes_emitted"] > 0

    episodes = json.loads((tmp_path / "eps.json").read_text())
    coverage = json.loads((tmp_path / "cov.json").read_text())
    assert episodes and coverage
    assert all(e["t_exact"] is not None for e in episodes)
    assert {e["body"] for e in episodes} <= set(drv.PERSISTED_BODIES)
    assert "Moon" not in {e["body"] for e in episodes}  # M-3/R7
    # resolved re-derivation landed the known targets
    by_type = {}
    for e in episodes:
        by_type.setdefault(e["target_type"], set()).add(e["relation"])
    assert "conjunction" in by_type["karaka"]
    assert by_type.get("bhava") == {"sign_ingress"}  # M-5: intervals, never points
    # the agent-gated M-6 span may only be touched by its named graha
    for e in episodes:
        if e["target_ref"] == "mandi_sign_distance_from_8L":
            assert e["body"] == "Saturn"
        if e["target_ref"] == "sun_minus_yamakantaka":
            assert e["body"] == "Jupiter"
    # orb regime on the real ephemeris too
    conj = [e for e in episodes if e["relation"] == "conjunction"]
    assert conj and all(e["orb_max_deg"] == 5.0 for e in conj)
    for e in episodes:
        if e["relation"] == "return":
            assert e["orb_max_deg"] == 0.5
    cov_counts = [c["target_resolution_state_counts"] for c in coverage]
    assert any("resolved" in c for c in cov_counts)

    # consumer: the pair contract end-to-end into the 1081/1087 ledger
    r2 = subprocess.run(
        [sys.executable, str(STEP06_PATH), "--dsn", WP6_DSN,
         "--chart-id", E2E_CHART,
         "--horizon-start", "2026-01-01T00:00:00+00:00",
         "--horizon-end", "2026-04-01T00:00:00+00:00",
         "--episodes-json", str(tmp_path / "eps.json"),
         "--coverage-json", str(tmp_path / "cov.json")],
        capture_output=True, text=True, timeout=300)
    assert r2.returncode == 0, r2.stderr

    import psycopg

    with psycopg.connect(WP6_DSN) as conn:
        n_contacts = conn.execute(
            "SELECT count(*) FROM kala_gochara_contacts"
            " WHERE chart_id=%s AND generation='4.0'", (E2E_CHART,)).fetchone()[0]
        n_cov = conn.execute(
            "SELECT count(*) FROM kala_gochara_coverage"
            " WHERE chart_id=%s AND generation='4.0'", (E2E_CHART,)).fetchone()[0]
        status = conn.execute(
            "SELECT status FROM kala_gochara_publication"
            " WHERE chart_id=%s AND generation='4.0'", (E2E_CHART,)).fetchone()[0]
    assert n_contacts == len(episodes)
    assert n_cov == len(coverage)
    assert status == "candidate"


@requires_swieph
def test_dedupe_two_map_rows_one_physical_target(wp6_enum_schema, tmp_path):
    """ADK-0020 mandatory e2e regression: two map rows (marriage/karaka/Venus
    @0.9, career_advancement/karaka/Venus @0.6) resolve to the SAME physical
    target (the VEN longitude fact) → the driver emits ONE row per physical
    contact (the higher-weight row survives), the dedupe count is disclosed in
    the enumeration report, the dropped-refs artifact records the dropped
    target_ref, and the ledger lands exactly one contact row with one
    independence_group per pinned §3.2 contact_id."""
    r = _run_driver(tmp_path)
    assert r.returncode == 0, r.stderr
    report = json.loads(r.stdout)
    dedupe = report["dedupe"]
    assert dedupe["episodes_before"] > dedupe["episodes_after"]
    assert dedupe["rows_dropped"] == (
        dedupe["episodes_before"] - dedupe["episodes_after"])
    assert dedupe["rows_dropped"] > 0
    assert dedupe["duplicate_groups"] > 0
    # the Venus pair shares both citations (null) → no refusal; survival came
    # from the weight tier
    assert dedupe["per_survival_tier"]["weight"] > 0
    assert dedupe["deeper_tie_groups"] == []
    # ADK-0022 disclosure ships in every run report, N per chart per run
    assert "citation_rule" in dedupe
    assert f"on {dedupe['groups_with_divergent_citations']} citation-divergent " \
        "groups no rule earns a single citation and the field is NULL" \
        in dedupe["citation_rule"]

    episodes = json.loads((tmp_path / "eps.json").read_text())
    # no dasha-duplicate: every physical contact appears once per contact_id
    from collections import Counter

    sys.path.insert(0, str(DRIVER_PATH.parent))
    from step06_candidate_build import CONVENTION_VECTOR

    conv_id = gk_convention.canonical_convention_id()

    def _cid(e):
        return drv._contact_id_of(
            {**e, "t_exact": datetime.fromisoformat(e["t_exact"])},
            E2E_CHART, conv_id, CONVENTION_VECTOR["method_version"])

    counts = Counter(_cid(e) for e in episodes)
    assert all(v == 1 for v in counts.values()), \
        "a pinned §3.2 contact_id still appears twice after dedupe"
    # the duplicate pair is Venus-referenced on BOTH rows; its contacts survived
    venus_eps = [e for e in episodes if e["target_ref"] == "Venus"]
    assert venus_eps
    assert len({_cid(e) for e in venus_eps}) == len(venus_eps)
    # dropped refs recoverable, keyed by contact_id; the Venus pair's entries
    # show survivor and dropped rows both naming target_ref "Venus"
    dropped = json.loads((tmp_path / "eps.json.dropped_refs.json").read_text())
    assert dropped
    assert any(v["survivor_target_ref"] == "Venus"
               and v["dropped_target_refs"] == ["Venus"]
               for v in dropped.values())
    # the survivor/dropped rows belong to duplicate groups: exactly one ledger
    # row per contact after the build consumes the deduped payload
    r2 = subprocess.run(
        [sys.executable, str(STEP06_PATH), "--dsn", WP6_DSN,
         "--chart-id", E2E_CHART,
         "--horizon-start", "2026-01-01T00:00:00+00:00",
         "--horizon-end", "2026-04-01T00:00:00+00:00",
         "--episodes-json", str(tmp_path / "eps.json"),
         "--coverage-json", str(tmp_path / "cov.json")],
        capture_output=True, text=True, timeout=300)
    assert r2.returncode == 0, r2.stderr

    import psycopg

    with psycopg.connect(WP6_DSN) as conn:
        rows = conn.execute(
            "SELECT contact_id, count(*) FROM kala_gochara_contacts"
            " WHERE chart_id=%s AND generation='4.0' GROUP BY contact_id"
            " HAVING count(*) > 1", (E2E_CHART,)).fetchall()
        venus_rows = conn.execute(
            "SELECT count(*) FROM kala_gochara_contacts"
            " WHERE chart_id=%s AND generation='4.0'"
            " AND target_ref='Venus'", (E2E_CHART,)).fetchone()[0]
    assert rows == [], f"duplicate contact_id rows in the ledger: {rows[:3]}"
    # exactly one ledger row per surviving Venus contact (the deduped payload)
    assert venus_rows == len([e for e in episodes if e["target_ref"] == "Venus"])


# ── ADK-0020 dedupe unit tests (no DB) ───────────────────────────────────────

DEDUPE_CHART = "dedupe-chart"
DEDUPE_CONV = "sha256:test-convention"
DEDUPE_MV = "1.0.0"


def _dedupe_ep(target_ref: str, weight, citation=None,
               target_fact_id: str = "fact.X",
               t_exact: datetime = datetime(2026, 2, 1, tzinfo=UTC)) -> dict:
    """A minimal episode dict in the driver's post-_episode_to_dict shape;
    same chart/body/relation/aspect/t_exact/target_fact_id ⇒ same pinned
    §3.2 contact_id (a physical duplicate from a second map row)."""
    return {
        "independence_group": "sha256:ig-physical",  # same physical contact ⇒ same ig
        "body": "Saturn",
        "relation": "conjunction",
        "aspect_deg": 0,
        "target_type": "karaka",
        "target_ref": target_ref,
        "target_fact_id": target_fact_id,
        "t_in": t_exact,
        "t_exact": t_exact,
        "t_out": t_exact,
        "classical_citation": citation,
        "_map_weight": weight,
    }


def test_dedupe_weight_order_wins(tmp_path):
    eps = [_dedupe_ep("low", 0.6), _dedupe_ep("high", 0.9)]
    survivors, report = drv.dedupe_episodes(
        eps, chart_id=DEDUPE_CHART, convention_id=DEDUPE_CONV,
        method_version=DEDUPE_MV,
        dropped_refs_path=str(tmp_path / "dropped.json"))
    assert [e["target_ref"] for e in survivors] == ["high"]
    assert report["episodes_before"] == 2 and report["episodes_after"] == 1
    assert report["rows_dropped"] == 1 and report["duplicate_groups"] == 1
    assert report["per_survival_tier"]["weight"] == 1
    assert report["per_relation_dropped"] == {"conjunction": 1}
    dropped = json.loads((tmp_path / "dropped.json").read_text())
    (cid, entry), = dropped.items()
    assert cid.startswith("sha256:")
    assert entry["survivor_target_ref"] == "high"
    assert entry["dropped_target_refs"] == ["low"]
    assert entry["dropped_rows"] == 1
    assert report["dropped_refs_artifact"] == str(tmp_path / "dropped.json")
    assert report["dropped_refs_contacts"] == 1


def test_dedupe_weight_tie_breaks_lexicographic():
    eps = [_dedupe_ep("Beta", 0.7), _dedupe_ep("Alpha", 0.7)]
    survivors, report = drv.dedupe_episodes(
        eps, chart_id=DEDUPE_CHART, convention_id=DEDUPE_CONV,
        method_version=DEDUPE_MV)
    assert [e["target_ref"] for e in survivors] == ["Alpha"]
    assert report["per_survival_tier"]["weight_tie_lexicographic"] == 1
    assert report["deeper_tie_groups"] == []


def test_dedupe_deeper_tie_surfaced_not_silent():
    # same weight AND same target_ref — a map defect: deterministic survivor,
    # surfaced in the report (never silently resolved)
    eps = [_dedupe_ep("same", 0.7), _dedupe_ep("same", 0.7)]
    survivors, report = drv.dedupe_episodes(
        eps, chart_id=DEDUPE_CHART, convention_id=DEDUPE_CONV,
        method_version=DEDUPE_MV)
    assert len(survivors) == 1
    assert report["per_survival_tier"]["deeper_tie"] == 1
    (group,) = report["deeper_tie_groups"]
    assert group["target_ref"] == "same" and group["weight"] == 0.7
    assert group["rows"] == 2 and group["contact_id"].startswith("sha256:")


def test_dedupe_none_weight_loses_to_any_number():
    eps = [_dedupe_ep("unweighted", None), _dedupe_ep("weighted", 0.1)]
    survivors, report = drv.dedupe_episodes(
        eps, chart_id=DEDUPE_CHART, convention_id=DEDUPE_CONV,
        method_version=DEDUPE_MV)
    assert [e["target_ref"] for e in survivors] == ["weighted"]
    assert report["per_survival_tier"]["weight"] == 1


def test_dedupe_divergent_citations_nulled_with_disclosure(tmp_path):
    """ADK-0022 (amending ADK-0021): a group whose rows differ ONLY in
    classical_citation survives, but the surviving row's citation is NULL —
    no rule earns a single citation when the group diverges (on real data
    every divergent group resolves at deeper_tie, i.e. json.dumps order).
    The divergent group is counted and disclosed; EVERY group citation is
    recoverable in the dropped-refs artifact keyed by contact_id."""
    eps = [_dedupe_ep("winner", 0.9, citation="BPHS ch.7 (vivaha)"),
           _dedupe_ep("loser", 0.6, citation="BPHS ch.4 (sukha)")]
    survivors, report = drv.dedupe_episodes(
        eps, chart_id=DEDUPE_CHART, convention_id=DEDUPE_CONV,
        method_version=DEDUPE_MV,
        dropped_refs_path=str(tmp_path / "dropped.json"))
    assert [e["target_ref"] for e in survivors] == ["winner"]
    assert survivors[0]["classical_citation"] is None  # null-and-disclose
    assert report["groups_with_divergent_citations"] == 1
    # disclosure wording: substance verbatim per ADK-0022 (1), N per run
    rule = report["citation_rule"]
    assert "classical_citation follows the surviving map row where the " \
        "group's citations agree" in rule
    assert "on 1 citation-divergent groups no rule earns a single citation " \
        "and the field is NULL" in rule
    assert "all group citations recoverable in .dropped_refs.json keyed by " \
        "contact_id" in rule
    # every group citation recoverable, keyed by contact_id; the entry's
    # survivor_citation is null too (the field IS null on the row)
    dropped = json.loads((tmp_path / "dropped.json").read_text())
    (cid, entry), = dropped.items()
    assert cid.startswith("sha256:")
    assert entry["survivor_citation"] is None
    assert entry["dropped_citations"] == ["BPHS ch.4 (sukha)",
                                          "BPHS ch.7 (vivaha)"]


def test_dedupe_agreeing_non_null_citations_keep_the_citation(tmp_path):
    """ADK-0022 (1)(a): identical non-null citations survive unambiguous —
    the surviving row KEEPS the agreed citation and the group is not counted
    as divergent."""
    eps = [_dedupe_ep("winner", 0.9, citation="BPHS ch.7 (vivaha)"),
           _dedupe_ep("loser", 0.6, citation="BPHS ch.7 (vivaha)")]
    survivors, report = drv.dedupe_episodes(
        eps, chart_id=DEDUPE_CHART, convention_id=DEDUPE_CONV,
        method_version=DEDUPE_MV,
        dropped_refs_path=str(tmp_path / "dropped.json"))
    assert survivors[0]["classical_citation"] == "BPHS ch.7 (vivaha)"
    assert report["groups_with_divergent_citations"] == 0
    dropped = json.loads((tmp_path / "dropped.json").read_text())
    (entry,) = dropped.values()
    assert entry["survivor_citation"] == "BPHS ch.7 (vivaha)"
    assert entry["dropped_citations"] == ["BPHS ch.7 (vivaha)"]


def test_dedupe_non_citation_divergence_refuses():
    """The exit-5 refusal's residual domain (ADK-0021 (4)): divergence in any
    field BEYOND target_ref and classical_citation still refuses — narrowed,
    never removed."""
    a = _dedupe_ep("a", 0.9)
    b = _dedupe_ep("b", 0.8)
    b["orb_max_deg"] = 0.5  # a field the survival rule does not own
    with pytest.raises(drv.DedupeRefusal):
        drv.dedupe_episodes(
            [a, b], chart_id=DEDUPE_CHART, convention_id=DEDUPE_CONV,
            method_version=DEDUPE_MV)


def test_dedupe_deeper_tie_with_divergent_citations_surfaces_defect():
    """ADK-0022 (1)(c): divergent citations coinciding with a deeper weight
    tie still surface the map defect (deeper_tie_groups) — and the surviving
    row's citation is NULL (the deeper-tie pick is json.dumps order, so no
    rule earns a single citation)."""
    eps = [_dedupe_ep("same", 0.7, citation="BPHS ch.4"),
           _dedupe_ep("same", 0.7, citation="BPHS ch.7")]
    survivors, report = drv.dedupe_episodes(
        eps, chart_id=DEDUPE_CHART, convention_id=DEDUPE_CONV,
        method_version=DEDUPE_MV)
    assert len(survivors) == 1
    assert report["per_survival_tier"]["deeper_tie"] == 1
    assert len(report["deeper_tie_groups"]) == 1
    assert report["groups_with_divergent_citations"] == 1
    assert survivors[0]["classical_citation"] is None


def test_dedupe_identical_null_citations_do_not_refuse():
    eps = [_dedupe_ep("a", 0.9), _dedupe_ep("b", 0.8, citation=None)]
    survivors, report = drv.dedupe_episodes(
        eps, chart_id=DEDUPE_CHART, convention_id=DEDUPE_CONV,
        method_version=DEDUPE_MV)
    assert len(survivors) == 1 and report["duplicate_groups"] == 1


def test_dedupe_strips_map_weight_and_keeps_singletons():
    solo = _dedupe_ep("solo", 0.5, target_fact_id="fact.Y",
                      t_exact=datetime(2026, 3, 1, tzinfo=UTC))
    dup_a = _dedupe_ep("a", 0.9)
    dup_b = _dedupe_ep("b", 0.8)
    survivors, report = drv.dedupe_episodes(
        [dup_b, solo, dup_a], chart_id=DEDUPE_CHART,
        convention_id=DEDUPE_CONV, method_version=DEDUPE_MV)
    assert len(survivors) == 2
    assert all("_map_weight" not in e for e in survivors)
    # sorted by t_in: the Feb duplicate-survivor before the March singleton
    assert [e["target_ref"] for e in survivors] == ["a", "solo"]
    assert report["episodes_before"] == 3 and report["episodes_after"] == 2


@requires_swieph
def test_stale_overlay_refused_exit_7(wp6_enum_schema, tmp_path):
    """§12.9: an overlay row with no upstream fingerprint reads STALE; the
    driver refuses BEFORE enumerating (exit 7), writing no payload."""
    import psycopg

    with psycopg.connect(WP6_DSN, autocommit=True) as conn:
        conn.execute(
            "UPDATE kala_vedha_gochara SET detail = detail - 'upstream_fingerprint'"
            " WHERE chart_id = %s", (E2E_CHART,))
    try:
        r = _run_driver(tmp_path / "stale")
        assert r.returncode == 7, r.stderr
        assert "REFUSED" in r.stderr
        assert not (tmp_path / "stale" / "eps.json").exists()
    finally:
        with psycopg.connect(WP6_DSN, autocommit=True) as conn:
            from services.ka_vedha_gochara.freshness import current_fingerprint

            conn.execute(
                "UPDATE kala_vedha_gochara SET detail = jsonb_set(detail,"
                " '{upstream_fingerprint}', %s::jsonb) WHERE chart_id = %s",
                (json.dumps(current_fingerprint(conn)), E2E_CHART))


@requires_swieph
def test_bodies_subset_equivalence(wp6_enum_schema, tmp_path):
    """--bodies chunked runs concatenate EXACTLY to the full run's payload for
    those bodies (F-0 P2 century-scale memory mitigation): dedupe groups key
    on the pinned §3.2 contact_id which includes body, so no group spans a
    chunk boundary."""
    for sub in ("full", "a", "b"):
        (tmp_path / sub).mkdir()
    full = _run_driver(tmp_path / "full")
    assert full.returncode == 0, full.stderr
    part_a = _run_driver(tmp_path / "a", "--bodies", "Sun,Saturn,Jupiter,Rahu")
    assert part_a.returncode == 0, part_a.stderr
    part_b = _run_driver(tmp_path / "b", "--bodies", "Mercury,Venus,Mars,Ketu")
    assert part_b.returncode == 0, part_b.stderr

    def eps(p):
        return json.loads((p / "eps.json").read_text())

    def key(e):
        return (e["body"], e["target_type"], e["target_ref"], e["relation"],
                str(e.get("aspect_deg")), e["t_exact"])

    full_keys = {key(e) for e in eps(tmp_path / "full")}
    chunk_keys = {key(e) for e in eps(tmp_path / "a")} | \
        {key(e) for e in eps(tmp_path / "b")}
    assert chunk_keys == full_keys
    assert {e["body"] for e in eps(tmp_path / "a")} == {
        "Sun", "Saturn", "Jupiter", "Rahu"}
    rep = json.loads(part_a.stdout)
    assert rep["bodies_enumerated"] == ["Sun", "Saturn", "Jupiter", "Rahu"]
    # coverage partitions are body-scoped, so the union is exact too
    cov_a = json.loads((tmp_path / "a" / "cov.json").read_text())
    cov_b = json.loads((tmp_path / "b" / "cov.json").read_text())
    cov_full = json.loads((tmp_path / "full" / "cov.json").read_text())
    pkey = lambda c: (c["partition_kind"], c["partition_key"])  # noqa: E731
    assert {pkey(c) for c in cov_a} | {pkey(c) for c in cov_b} == \
        {pkey(c) for c in cov_full}


@requires_swieph
def test_bodies_subset_validation(wp6_enum_schema, tmp_path):
    # exit-3 paths refuse before any payload write, so the missing payload
    # parent dir is not touched; point them at tmp_path itself.
    r = _run_driver(tmp_path, "--bodies", "Pluto")
    assert r.returncode == 3 and "--bodies" in r.stderr
    r = _run_driver(tmp_path, "--bodies", "Sun,Sun")
    assert r.returncode == 3 and "duplicates" in r.stderr
