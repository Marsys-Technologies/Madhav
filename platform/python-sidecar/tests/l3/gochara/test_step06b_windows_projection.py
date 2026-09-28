"""WP10 step-6b — the E-012 '4.0' windows projection writer (ADK-0012).

`scripts/kala_gochara_cutover/step06b_windows_projection.py` projects the '4.0'
candidate contact ledger into the SERVED table kala_gochara_windows under
generation '4.0'. What this file proves:

  * unit (no DB): the M-1 linear_no_box decay shape; the per-class lambda
    evaluator equals the pinned legacy_semantics algebra term-for-term;
    find_components on single / disjoint / sub-day-bump series (breakpoint
    augmentation makes a sub-day span visible); H-5 — every admitted peak is
    stored (the pre-H-5 cap of 3 is removed, the pinned 90-day separation
    retained); the relation→primitive map vocabulary; the delta report's
    honest '—' nulls for absent baseline factors.
  * disposable-DB integration (WP6 DSN only, NOT_RUN when unreachable): the
    flip gate windows_present goes RED→GREEN across the writer; era/month/day
    rows with parent linkage; 'v1'/'3.0' rows untouched; the candidate
    manifest's row_counts.windows gains the real count; reruns are
    idempotent; the delta report file is written; a contact with no map row
    yields no window (counted, never silently dropped); a class with contacts
    but no context is an honest skip; §12.9 stale overlays refuse (exit 7);
    production DSNs refuse (exit 4); a published generation refuses (exit 6).
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from .conftest import (  # noqa: E402
    WP6_DSN,
    WP6_DROP_SQL,
    WP6_MIGRATION_1072,
    WP6_MIGRATION_1087,
)
from .test_wp9_stamp_columns import BASE_DDL as _WP9_BASE_DDL  # noqa: E402

WRITER_PATH = (
    Path(__file__).resolve().parents[3]
    / "scripts" / "kala_gochara_cutover" / "step06b_windows_projection.py"
)
STEP06_PATH = WRITER_PATH.parent / "step06_candidate_build.py"
STEP07_PATH = WRITER_PATH.parent / "step07_flip_gates.py"
MIGRATION_1082 = (
    Path(__file__).resolve().parents[4]
    / "migrations/1082_nirmana_l3_vedha_moorti_stamp_columns.sql"
)

UTC = timezone.utc


def _load_writer():
    spec = importlib.util.spec_from_file_location(
        "step06b_windows_projection", WRITER_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


w = _load_writer()
leg = w.leg


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


def _contact(cid: str, t_exact: datetime, *, half_days: float = 10.0,
             body: str = "Saturn", relation: str = "conjunction",
             target_type: str = "karaka", target_ref: str = "Venus") -> dict:
    span = timedelta(days=half_days)
    return {
        "contact_id": cid, "body": body, "relation": relation,
        "target_type": target_type, "target_ref": target_ref,
        "orb_max_deg": 5.0, "completeness_state": "applied",
        "_primitive": w.RELATION_TO_PRIMITIVE[relation],
        "_t_in_jd": w.jd_of(t_exact - span),
        "_t_exact_jd": w.jd_of(t_exact),
        "_t_out_jd": w.jd_of(t_exact + span),
    }


def _ctx(weights=None, perms=None, weights_by_ref=None) -> w.ClassContext:
    return w.ClassContext(
        "marriage", weights if weights is not None else [0.9],
        perms if perms is not None else {"vimshottari": True},
        weight_by_target_ref=(
            weights_by_ref if weights_by_ref is not None else {"Venus": 0.9}))


def _open_gates(date_iso: str):
    return leg.compute_quality_gates([], date_iso, date_iso, {})


# ── unit: M-1 decay shape ────────────────────────────────────────────────────


def test_linear_no_box_decay_shape():
    t_in, t_exact, t_out = 100.0, 110.0, 130.0
    assert w.linear_no_box_decay(100.0, t_in, t_exact, t_out) == 0.0
    assert w.linear_no_box_decay(130.0, t_in, t_exact, t_out) == 0.0
    assert w.linear_no_box_decay(99.0, t_in, t_exact, t_out) == 0.0
    assert w.linear_no_box_decay(131.0, t_in, t_exact, t_out) == 0.0
    assert w.linear_no_box_decay(110.0, t_in, t_exact, t_out) == 1.0
    assert w.linear_no_box_decay(105.0, t_in, t_exact, t_out) == pytest.approx(0.5)
    assert w.linear_no_box_decay(120.0, t_in, t_exact, t_out) == pytest.approx(0.5)
    # no ±5-day box: at event ± 6 days the contribution is NOT flat
    assert w.linear_no_box_decay(116.0, t_in, t_exact, t_out) == pytest.approx(0.7)
    # degenerate spans stay honest (never a division error, never a flat 1.0)
    assert w.linear_no_box_decay(110.0, t_in, None, t_out) == 0.0
    assert w.linear_no_box_decay(110.0, 110.0, 110.0, 110.0) == 0.0


# ── unit: the evaluator is the pinned algebra ────────────────────────────────


def test_eval_matches_pinned_algebra():
    ctx = _ctx()
    contact = _contact("c1", _dt("2026-02-15T00:00:00+00:00"))
    evaluate = w.make_eval_fn(ctx, [contact], _open_gates)
    at_exact = evaluate(contact["_t_exact_jd"])
    # hand-computed pinned terms at t_exact (decay = 1.0)
    sentences = [leg.Sentence(
        primitive="degree_contact", target_ref="Venus", transit_planet="Saturn",
        event_jd=contact["_t_exact_jd"], detail={"orb_strength": 1.0})]
    activity, _, _ = leg.compute_activity_v3(sentences, {"Venus": 0.9})
    supportive, afflicting, _ = leg.compute_signed_channels_v3(
        sentences, {"Venus": 0.9})
    assembled = leg.assemble_lambda_v3(
        promise=ctx.promise, permission=ctx.permission, activity=activity,
        tara_modifier=ctx.tara["modifier"], w30_modifier=ctx.w30["modifier"],
        quality_gates=1.0)
    assert at_exact["activity"] == pytest.approx(activity)
    assert at_exact["lambda_raw"] == pytest.approx(assembled["lambda_raw"])
    assert at_exact["supportive"] == pytest.approx(supportive)
    assert at_exact["active_contact_ids"] == ["c1"]
    # outside the span the class evaluates to exactly zero (no F-08 floor)
    outside = evaluate(contact["_t_out_jd"] + 1.0)
    assert outside["activity"] == 0.0
    assert outside["lambda_raw"] == 0.0
    assert outside["active_contact_ids"] == []


# ── unit: component machinery ────────────────────────────────────────────────


def test_find_components_single_and_disjoint():
    # tent over [10, 20] and [40, 50], zero elsewhere
    def f(t):
        if 10.0 <= t <= 20.0:
            return 1.0 - abs(t - 15.0) / 5.0
        if 40.0 <= t <= 50.0:
            return 1.0 - abs(t - 45.0) / 5.0
        return 0.0

    points = [float(i) for i in range(0, 61)]
    comps = w.find_components(f, points, 1e-9)
    assert len(comps) == 2
    (e0, x0, _, _), (e1, x1, _, _) = comps
    assert e0 == pytest.approx(10.0, abs=1e-3)
    assert x0 == pytest.approx(20.0, abs=1e-3)
    assert e1 == pytest.approx(40.0, abs=1e-3)
    assert x1 == pytest.approx(50.0, abs=1e-3)


def test_find_components_subday_bump_visible():
    """A 4-hour span is invisible to the uniform daily grid; the breakpoint
    augmentation (t_in/t_exact/t_out on the series) is load-bearing."""
    t_in, t_exact, t_out = 100.4166667, 100.5, 100.5833333  # 4h around noon

    def f(t):
        return w.linear_no_box_decay(t, t_in, t_exact, t_out)

    grid = [float(i) for i in range(95, 106)]  # daily grid: every value is 0.0
    assert all(f(t) == 0.0 for t in grid)
    series = sorted(set(grid) | {t_in, t_exact, t_out})
    comps = w.find_components(f, series, 1e-9)
    assert len(comps) == 1
    enter, exit_jd, _, _ = comps[0]
    assert enter == pytest.approx(t_in, abs=1e-3)
    assert exit_jd == pytest.approx(t_out, abs=1e-3)


# ── unit: H-5 — every admitted peak is stored ────────────────────────────────


def test_h5_all_admitted_peaks_retained():
    ctx = _ctx()
    base = _dt("2026-01-15T12:00:00+00:00")
    contacts = [
        _contact(f"c{i}", base + timedelta(days=120 * i)) for i in range(5)
    ]
    horizon = (w.jd_of(_dt("2026-01-01T00:00:00+00:00")),
               w.jd_of(_dt("2027-08-01T00:00:00+00:00")))
    rows, report = w.project_class_windows(ctx, contacts, horizon, _open_gates)
    assert report["components"] == 5
    assert report["peaks_admitted"] == 5
    # H-5: the pre-H-5 cap of 3/era is removed; each era keeps its peak
    assert report["peaks_retained"] == 5
    tiers = [r["resolution"] for r in rows]
    assert tiers.count("era") == 5
    assert tiers.count("month") == 5
    assert tiers.count("day") == 5
    # every month/day row names its parent key; day peaks sit on t_exact
    for r in rows:
        if r["resolution"] == "era":
            assert r["parent_key"] is None
        else:
            assert r["parent_key"] is not None
    day_peaks = sorted(r["peak_date"] for r in rows if r["resolution"] == "day")
    assert day_peaks == sorted(
        (base + timedelta(days=120 * i)).date() for i in range(5))


# ── unit: relation vocabulary + era slice key ────────────────────────────────


def test_relation_to_primitive_vocabulary():
    assert w.RELATION_TO_PRIMITIVE == {
        "conjunction": "degree_contact",
        "return": "degree_contact",
        "drishti_contact": "drishti_contact",
        "sign_ingress": "sign_ingress",
        "nakshatra_ingress": "nakshatra_ingress_tara",
        "kakshya_cell_crossing": "kakshya_cell_crossing",
        "station_retro_loop": "station_retro_loop",
        "eclipse_degree": "eclipse_degree",
    }
    # every mapped primitive is a real ACTIVITY_PRIMITIVES member
    assert set(w.RELATION_TO_PRIMITIVE.values()) <= set(leg.ACTIVITY_PRIMITIVES)
    # K3-F1 regression: every relation the contact enumerator can emit
    # (contacts.py EXACT_SEPARATION_RELATIONS / BOUNDARY_RELATIONS plus the
    # station/eclipse families) must be a KEY of this map — an unmapped key
    # silently drops that relation family from the activity function.
    enumerator_relations = {
        "conjunction", "return", "drishti_contact",
        "sign_ingress", "nakshatra_ingress", "kakshya_cell_crossing",
        "station_retro_loop", "eclipse_degree",
    }
    assert enumerator_relations <= set(w.RELATION_TO_PRIMITIVE)


# ── unit: delta report honest nulls ──────────────────────────────────────────


def _fake_class_report(cls="marriage"):
    return {
        "event_class": cls, "promise": 0.9, "promise_target_count": 1,
        "permission": 0.25, "permission_systems_active": ["vimshottari"],
        "tara_modifier": 1.0, "tara_skip_reason": "transit_body_longitude_deg not supplied",
        "w30_modifier": 1.0, "w30_skip_reason": "mechanism disabled via toggle",
        "class_valence": "mixed", "class_is_adverse": False,
        "context_source": "test", "components": 1, "peaks_admitted": 1,
        "peaks_retained": 1, "era_windows": 1, "month_windows": 1,
        "day_windows": 1, "quality_gates_fired": 0, "mean_quality_gates": 1.0,
    }


def test_delta_report_honest_null_cells_without_baseline():
    report = w.build_delta_report(
        chart_id="chart-x", generation="4.0", baseline="3.0",
        class_reports=[_fake_class_report()],
        window_rows=[{
            "resolution": "era", "event_class": "marriage",
            "peak_date": _dt("2026-02-15T00:00:00+00:00").date(),
            "raw_intensity": 0.2, "signed_intensity": 0.2, "valence": "favourable",
        }],
        baseline_rows=[], flags=w.CANDIDATE_FLAGS, fingerprints=None,
        run_meta={"generated_at": "2026-09-27T00:00:00Z", "build_id": "test",
                  "horizon": "test", "class_context_source": "test"})
    assert "| 0 | — | — |" in report  # no baseline rows: honest nulls, no 0.0
    assert "| — | — | — |" in report  # era-tier delta row: no nearest peak
    assert "honest null" in report


def test_delta_report_with_baseline_deltas():
    report = w.build_delta_report(
        chart_id="chart-x", generation="4.0", baseline="3.0",
        class_reports=[_fake_class_report()],
        window_rows=[{
            "resolution": "era", "event_class": "marriage",
            "peak_date": _dt("2026-02-15T00:00:00+00:00").date(),
            "raw_intensity": 0.3, "signed_intensity": 0.3, "valence": "favourable",
        }],
        baseline_rows=[{
            "event_class": "marriage",
            "peak_date": _dt("2013-05-01T00:00:00+00:00").date(),
            "raw_intensity": 0.2, "signed_intensity": 0.2,
        }],
        flags=w.CANDIDATE_FLAGS, fingerprints={"house_vedha": "sha256:x"},
        run_meta={"generated_at": "2026-09-27T00:00:00Z", "build_id": "test",
                  "horizon": "test", "class_context_source": "test"})
    assert "0.300000" in report
    assert "2013-05-01" in report  # nearest baseline peak named
    assert "0.100000" in report    # per-era Δ raw


# ── disposable-DB integration ────────────────────────────────────────────────

S6B_CHART = "33333333-4444-5555-6666-777777777777"

EXTRA_DDL = """
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

DROP TABLE IF EXISTS kala_gochara_windows;
CREATE TABLE kala_gochara_windows (
  id BIGSERIAL PRIMARY KEY,
  chart_id UUID NOT NULL,
  event_class TEXT NOT NULL,
  temporal_shape TEXT NOT NULL CHECK (temporal_shape IN ('point','interval','chain')),
  window_start DATE NOT NULL,
  window_end DATE NOT NULL,
  peak_date DATE NOT NULL,
  milestone_id TEXT,
  is_irreversibility_milestone BOOLEAN NOT NULL DEFAULT FALSE,
  signed_intensity NUMERIC NOT NULL,
  raw_intensity NUMERIC NOT NULL,
  valence TEXT NOT NULL,
  is_adverse BOOLEAN NOT NULL,
  active_sentences JSONB NOT NULL DEFAULT '[]'::jsonb,
  contributing_systems JSONB NOT NULL DEFAULT '[]'::jsonb,
  suppression_state JSONB NOT NULL DEFAULT '{}'::jsonb,
  peak_basis TEXT NOT NULL DEFAULT 'gochara_lambda_e_v1',
  calibration_state TEXT NOT NULL DEFAULT 'structural_prior',
  source TEXT NOT NULL DEFAULT 'live' CHECK (source IN ('live','fixture')),
  computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  generation TEXT NOT NULL DEFAULT 'v1',
  era_slice_key TEXT,
  parent_window_id BIGINT,
  resolution TEXT
);
"""


def _wp6_reachable() -> bool:
    import psycopg

    try:
        import psycopg as _p
        with _p.connect(WP6_DSN, connect_timeout=3):
            return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def s6b_schema():
    """Overlay + reference + map + windows + the 1081/1087 ledger on the
    disposable WP6 Postgres. NOT_RUN when unreachable."""
    if not _wp6_reachable():
        pytest.skip("NOT_RUN: disposable WP6 database unreachable")
    import psycopg

    conn = psycopg.connect(WP6_DSN, autocommit=True)
    conn.execute(_WP9_BASE_DDL)
    conn.execute(MIGRATION_1082.read_text())
    conn.execute(EXTRA_DDL)
    conn.execute(WP6_DROP_SQL)
    conn.execute(WP6_MIGRATION_1072.read_text())
    conn.execute(WP6_MIGRATION_1087.read_text())
    conn.close()
    return True


def _episode(t_in, t_exact, t_out, *, body, target_ref) -> dict:
    return {
        "independence_group": f"ig-s6b-{body.lower()}-{target_ref.lower()}",
        "body": body, "relation": "conjunction", "aspect_deg": 0,
        "target_type": "karaka", "target_ref": target_ref, "target_fact_id": None,
        "target_resolution_state": "resolved", "target_longitude_deg": 300.0,
        "t_in": t_in, "t_exact": t_exact, "t_out": t_out,
        "bracket_seconds": 300, "tolerance_arcsec": 2.0,
        "truncated_at_horizon": None, "branch": "direct",
        "orb_max_deg": 5.0, "orb_source": "orb_conj_slow",
        "epistemic_class": "observed_event", "completeness_state": "applied",
        "operator_role": "kernel", "precision_regime": "instant_grain",
        "time_basis": "event_time_utc",
        "comparable_with": "same_convention_same_inputs",
        "ephemeris_backend": {"backend": "swieph", "retflag": 258},
        "evidence_fact_ids": [], "classical_citation": None,
        "uncited_extension": True, "corpus_verifiable": None,
    }


EPISODES = [
    # Venus karaka contact -> joins (marriage, karaka, Venus, 0.9)
    _episode("2026-02-05T12:00:00+00:00", "2026-02-15T12:00:00+00:00",
             "2026-02-25T12:00:00+00:00", body="Saturn", target_ref="Venus"),
    # Mars karaka contact -> joins (career, karaka, Mars, 0.5); the class
    # context below names only 'marriage' -> career is an honest skip
    _episode("2026-03-01T00:00:00+00:00", "2026-03-10T00:00:00+00:00",
             "2026-03-20T00:00:00+00:00", body="Jupiter", target_ref="Mars"),
    # Jupiter-target contact with NO map row -> counted unmapped, no window
    _episode("2026-04-01T00:00:00+00:00", "2026-04-10T00:00:00+00:00",
             "2026-04-20T00:00:00+00:00", body="Saturn", target_ref="Jupiter"),
]

COVERAGE = [{
    "partition_kind": "body_target", "partition_key": "saturn:karaka",
    "requested_horizon": "[2026-01-01,2026-06-01)",
    "completed_horizon": "[2026-01-01,2026-06-01)",
    "resolution": 2.0, "relations_searched": ["conjunction"],
    "targets_requested": 3,
    "target_resolution_state_counts": {"resolved": 3, "unavailable": 0,
                                       "unqualified": 0},
    "unavailable_inputs": {}, "unsearched_reason": None,
}]

CLASS_CONTEXT = {"marriage": {"permission_systems": {"vimshottari": True}}}


@pytest.fixture()
def built(s6b_schema, tmp_path):
    """Clean chart scope, fresh-stamped overlays, map + baseline window rows,
    and a step06 candidate build. The windows projection is NOT yet run."""
    import psycopg

    from services.ka_vedha_gochara.freshness import (
        current_fingerprint, current_moorti_fingerprint)

    conn = psycopg.connect(WP6_DSN, autocommit=True)
    with conn.cursor() as cur:
        for table in ("kala_gochara_contacts", "kala_gochara_coverage",
                      "kala_gochara_publication", "gochara_resonance_map",
                      "kala_gochara_windows", "kala_vedha_gochara",
                      "kala_moorti_nirnaya"):
            cur.execute(f"DELETE FROM {table} WHERE chart_id = %s", (S6B_CHART,))
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
        cur.executemany(
            "INSERT INTO gochara_resonance_map (chart_id, event_class, target_type,"
            " target_ref, weight, classical_citation, uncited_extension,"
            " target_resolution_state, target_qualifier)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [(S6B_CHART, "marriage", "karaka", "Venus", 0.9, None, False,
              "resolved", None),
             (S6B_CHART, "career", "karaka", "Mars", 0.5, None, False,
              "resolved", None)])
        cur.executemany(
            "INSERT INTO kala_gochara_windows (chart_id, event_class,"
            " temporal_shape, window_start, window_end, peak_date,"
            " signed_intensity, raw_intensity, valence, is_adverse, generation)"
            " VALUES (%s,'marriage','point',%s,%s,%s,1,1,'gain',false,%s)",
            [(S6B_CHART, "2001-01-01", "2001-01-01", "2001-01-01", "v1"),
             (S6B_CHART, "2002-01-01", "2002-01-01", "2002-01-01", "v1"),
             (S6B_CHART, "2013-05-01", "2013-05-01", "2013-05-01", "3.0"),
             (S6B_CHART, "2014-05-01", "2014-05-01", "2014-05-01", "3.0")])

    vedha_fp = current_fingerprint(conn)
    moorti_fp = current_moorti_fingerprint(conn)
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO kala_vedha_gochara (chart_id, ayanamsha_id, vedha_kind,"
            " graha, window_start, window_end, start_truncated, end_truncated,"
            " janma_reference_fact_id, classical_citation, uncited_extension,"
            " grid_basis, detail, formula_version) VALUES"
            " (%s,%s,'house_vedha','Sun','2026-01-01','2026-02-01',false,false,"
            " 's6b.moon.lon','Phaladipika Adh. XXVI, Sloka 3',false,NULL,%s,'s6b')",
            (S6B_CHART, 'lahiri_chitrapaksha',
             json.dumps({"upstream_fingerprint": vedha_fp})))
        cur.execute(
            "INSERT INTO kala_moorti_nirnaya (chart_id, ayanamsha_id, graha,"
            " target_sign_idx, target_sign_name, window_start, window_end,"
            " start_truncated, end_truncated, moorti_computed,"
            " janma_nakshatra_idx, janma_nakshatra_fact_id, formula_version,"
            " upstream_fingerprint) VALUES"
            " (%s,%s,'Sun',2,'Gemini','2026-01-01','2026-02-01',false,false,false,"
            " 0,'s6b.moon.nak','s6b',%s)",
            (S6B_CHART, 'lahiri_chitrapaksha', json.dumps(moorti_fp)))
    conn.close()

    eps_path = tmp_path / "eps.json"
    cov_path = tmp_path / "cov.json"
    ctx_path = tmp_path / "ctx.json"
    eps_path.write_text(json.dumps(EPISODES))
    cov_path.write_text(json.dumps(COVERAGE))
    ctx_path.write_text(json.dumps(CLASS_CONTEXT))

    r = subprocess.run(
        [sys.executable, str(STEP06_PATH), "--dsn", WP6_DSN,
         "--chart-id", S6B_CHART,
         "--horizon-start", "2026-01-01T00:00:00+00:00",
         "--horizon-end", "2026-06-01T00:00:00+00:00",
         "--episodes-json", str(eps_path), "--coverage-json", str(cov_path)],
        capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stderr
    return {"chart": S6B_CHART, "ctx_path": ctx_path,
            "delta_path": tmp_path / "delta.md"}


def _run_writer(chart, ctx_path, *extra, dsn=WP6_DSN):
    args = [sys.executable, str(WRITER_PATH), "--dsn", dsn, "--chart-id", chart,
            "--horizon-start", "2026-01-01T00:00:00+00:00",
            "--horizon-end", "2026-06-01T00:00:00+00:00"]
    if ctx_path is not None:
        args += ["--class-context-json", str(ctx_path)]
    return subprocess.run([*args, *extra],
                          capture_output=True, text=True, timeout=300)


def _q(sql, args=()):
    import psycopg

    with psycopg.connect(WP6_DSN, autocommit=True) as conn:
        return conn.execute(sql, args).fetchone()[0]


def test_windows_gate_red_then_green_and_hierarchy(built):
    chart = built["chart"]
    # RED before the writer runs (E-012 gate sees zero '4.0' window rows)
    r0 = subprocess.run(
        [sys.executable, str(STEP07_PATH), "--dsn", WP6_DSN,
         "--chart-id", chart],
        capture_output=True, text=True, timeout=120)
    assert r0.returncode == 7, (r0.returncode, r0.stdout, r0.stderr)
    assert '"windows_present"' in r0.stdout

    r = _run_writer(chart, built["ctx_path"],
                    "--delta-report-out", str(built["delta_path"]))
    assert r.returncode == 0, r.stderr
    report = json.loads(r.stdout)
    assert report["windows_written"] > 0
    assert report["contacts_read"] == 3
    assert report["contacts_unmapped_no_class"] == 1  # Jupiter: no map row
    assert report["contacts_unmapped_relation"] == 0
    assert report["skipped_classes"] and \
        report["skipped_classes"][0]["event_class"] == "career"
    assert report["class_reports"][0]["event_class"] == "marriage"
    tiers = report["windows_by_tier"]
    assert tiers["era"] >= 1 and tiers["month"] >= 1 and tiers["day"] >= 1

    # rows: era/month/day for '4.0' only; parent linkage wired; tier + key set
    n4 = _q("SELECT count(*) FROM kala_gochara_windows"
            " WHERE chart_id=%s AND generation='4.0'", (chart,))
    assert n4 == report["windows_written"]
    orphans = _q(
        "SELECT count(*) FROM kala_gochara_windows c WHERE c.chart_id=%s"
        " AND c.generation='4.0' AND c.resolution IN ('month','day')"
        " AND (c.parent_window_id IS NULL OR NOT EXISTS"
        "   (SELECT 1 FROM kala_gochara_windows p WHERE p.id = c.parent_window_id"
        "    AND p.chart_id = c.chart_id AND p.generation = '4.0'))", (chart,))
    assert orphans == 0
    day_parents = _q(
        "SELECT count(*) FROM kala_gochara_windows d JOIN kala_gochara_windows p"
        " ON p.id = d.parent_window_id WHERE d.chart_id=%s AND d.generation='4.0'"
        " AND d.resolution='day' AND p.resolution='month'", (chart,))
    assert day_parents == tiers["day"]
    # era_slice_key stays NULL on '4.0' rows: migration 1091 conjunct (g)
    # reads a non-null era_slice_key inside generation '4.0' as contamination.
    assert _q("SELECT count(*) FROM kala_gochara_windows WHERE chart_id=%s"
              " AND generation='4.0' AND era_slice_key IS NOT NULL",
              (chart,)) == 0
    assert _q("SELECT bool_and(peak_basis='gochara_lambda_v3:m1_linear_no_box:step06b'"
              " AND source='live') FROM kala_gochara_windows"
              " WHERE chart_id=%s AND generation='4.0'", (chart,)) is True
    # the peak lands on the contact's t_exact (M-1 vertex)
    assert str(_q("SELECT peak_date FROM kala_gochara_windows WHERE chart_id=%s"
                  " AND generation='4.0' AND resolution='day' LIMIT 1",
                  (chart,))) == "2026-02-15"

    # cross-generation preservation: 'v1'/'3.0' untouched
    assert _q("SELECT count(*) FROM kala_gochara_windows WHERE chart_id=%s"
              " AND generation='v1'", (chart,)) == 2
    assert _q("SELECT count(*) FROM kala_gochara_windows WHERE chart_id=%s"
              " AND generation='3.0'", (chart,)) == 2

    # the candidate manifest records the real windows count
    assert _q("SELECT (row_counts->>'windows')::int FROM kala_gochara_publication"
              " WHERE chart_id=%s AND generation='4.0'", (chart,)) == n4

    # delta report written with honest nulls against the '3.0' baseline
    delta = built["delta_path"].read_text()
    assert "Per-class factors" in delta
    assert "2014-05-01" in delta  # nearest '3.0' peak named on the era row

    # GREEN after the writer
    r1 = subprocess.run(
        [sys.executable, str(STEP07_PATH), "--dsn", WP6_DSN,
         "--chart-id", chart],
        capture_output=True, text=True, timeout=120)
    assert r1.returncode == 0, (r1.returncode, r1.stdout, r1.stderr)
    assert '"pass": true' in r1.stdout

    # idempotent rerun: delete-then-insert under the candidate, same counts
    r2 = _run_writer(chart, built["ctx_path"])
    assert r2.returncode == 0, r2.stderr
    assert _q("SELECT count(*) FROM kala_gochara_windows"
              " WHERE chart_id=%s AND generation='4.0'", (chart,)) == n4


def test_production_refusal_exit_4():
    r = subprocess.run(
        [sys.executable, str(WRITER_PATH),
         "--dsn", "postgresql://u:x@db.prod.example:5432/prod",
         "--chart-id", S6B_CHART, "--rehearse-synthetic"],
        capture_output=True, text=True, timeout=60)
    assert r.returncode == 4 and "REFUSED" in r.stderr
    r2 = subprocess.run(
        [sys.executable, str(WRITER_PATH),
         "--dsn", "postgresql://u:x@127.0.0.1:5433/prod",
         "--chart-id", S6B_CHART, "--rehearse-synthetic"],
        capture_output=True, text=True, timeout=60)
    assert r2.returncode == 4 and "REFUSED" in r2.stderr


def test_stale_overlay_refused_exit_7(built):
    import psycopg

    with psycopg.connect(WP6_DSN, autocommit=True) as conn:
        conn.execute(
            "UPDATE kala_vedha_gochara SET detail = detail - 'upstream_fingerprint'"
            " WHERE chart_id = %s", (S6B_CHART,))
    try:
        r = _run_writer(S6B_CHART, built["ctx_path"])
        assert r.returncode == 7, (r.returncode, r.stdout, r.stderr)
        assert "REFUSED" in r.stderr
        assert _q("SELECT count(*) FROM kala_gochara_windows WHERE chart_id=%s"
                  " AND generation='4.0'", (S6B_CHART,)) == 0
    finally:
        with psycopg.connect(WP6_DSN, autocommit=True) as conn:
            from services.ka_vedha_gochara.freshness import current_fingerprint

            conn.execute(
                "UPDATE kala_vedha_gochara SET detail = jsonb_set(detail,"
                " '{upstream_fingerprint}', %s::jsonb) WHERE chart_id = %s",
                (json.dumps(current_fingerprint(conn)), S6B_CHART))


def test_published_generation_refused_exit_6(built):
    r = _run_writer(S6B_CHART, built["ctx_path"])
    assert r.returncode == 0, r.stderr
    import psycopg

    with psycopg.connect(WP6_DSN, autocommit=True) as conn:
        conn.execute(
            "UPDATE kala_gochara_publication SET status = 'published'"
            " WHERE chart_id = %s AND generation = '4.0'", (S6B_CHART,))
    try:
        r2 = _run_writer(S6B_CHART, built["ctx_path"])
        assert r2.returncode == 6, (r2.returncode, r2.stdout, r2.stderr)
        assert "REFUSED" in r2.stderr
    finally:
        with psycopg.connect(WP6_DSN, autocommit=True) as conn:
            conn.execute(
                "UPDATE kala_gochara_publication SET status = 'candidate'"
                " WHERE chart_id = %s AND generation = '4.0'", (S6B_CHART,))


def test_no_candidate_manifest_exit_3(built):
    """A chart whose manifest is gone cannot proceed (step 6 has not run)."""
    import psycopg

    with psycopg.connect(WP6_DSN, autocommit=True) as conn:
        conn.execute("DELETE FROM kala_gochara_contacts WHERE chart_id = %s",
                     (S6B_CHART,))
        conn.execute("DELETE FROM kala_gochara_coverage WHERE chart_id = %s",
                     (S6B_CHART,))
        conn.execute("DELETE FROM kala_gochara_publication WHERE chart_id = %s",
                     (S6B_CHART,))
    r = _run_writer(S6B_CHART, built["ctx_path"])
    assert r.returncode == 3, (r.returncode, r.stdout, r.stderr)
