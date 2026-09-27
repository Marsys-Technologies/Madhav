"""WP10 step-6a — class-context permission wiring (ADK-0017 carried block 4).

`scripts/kala_gochara_cutover/step06a_class_context.py` produces the
`--class-context-json` document step06b consumes, from the REAL permission
machinery (`gochara_intensity.permission`'s DR-14 12-generator plurality sum
+ the served target fetch + the valence read) instead of a rehearsal-synthetic
constant. What this file proves:

  * unit (no DB): union semantics — a system is active for a class iff it
    fires at ≥1 of the class's sampled contact instants; the emitted dict
    covers all 12 pinned system ids; permission_value is the pinned
    legacy_semantics.compute_permission of the same set; a class whose
    targets do not resolve is OMITTED (None), never fabricated.
  * disposable-DB integration (WP6 DSN only, NOT_RUN when unreachable): the
    producer reads a real candidate ledger (step06 build) + chart_dashas
    fixture rows; the vimshottari lord matching the class's karaka fires and
    no other dasha system does; t_exact-NULL contacts are excluded and
    counted; the emitted JSON feeds step06b end-to-end (class projected with
    the wired permission, not the rehearsal-synthetic one); the honest-skip
    negative — a class with contacts but no wired context lands in
    skipped_classes and yields ZERO '4.0' windows, never a projection;
    exit 4 production refusal; exit 3 with no candidate contacts.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from .conftest import (  # noqa: E402
    WP6_DSN,
    WP6_DROP_SQL,
    WP6_MIGRATION_1072,
    WP6_MIGRATION_1087,
)
from .test_step06b_windows_projection import EXTRA_DDL, _episode  # noqa: E402
from .test_wp9_stamp_columns import BASE_DDL as _WP9_BASE_DDL  # noqa: E402

SIDECAR = Path(__file__).resolve().parents[3]
PRODUCER_PATH = SIDECAR / "scripts" / "kala_gochara_cutover" / "step06a_class_context.py"
WRITER_PATH = SIDECAR / "scripts" / "kala_gochara_cutover" / "step06b_windows_projection.py"
STEP06_PATH = SIDECAR / "scripts" / "kala_gochara_cutover" / "step06_candidate_build.py"
MIGRATION_1082 = (
    Path(__file__).resolve().parents[4]
    / "migrations/1082_nirmana_l3_vedha_moorti_stamp_columns.sql"
)


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


s6a = _load(PRODUCER_PATH, "step06a_class_context")
leg = s6a.leg
perm = s6a.perm


# ── unit: union semantics + honest omission (no DB) ──────────────────────────


def _unit_ctx(monkeypatch, active_by_instant):
    """Run build_class_context with the DB-touching seams monkeypatched:
    targets resolve to one synthetic karaka row; compute_permission returns
    canned systems_active per instant; valence fixed."""
    class _T:  # minimal ResonanceTarget stand-in for the monkeypatched seams
        pass

    monkeypatch.setattr(s6a, "fetch_resonance_targets",
                        lambda conn, chart_id, cls: [_T()])
    monkeypatch.setattr(s6a.enrichment, "enrich_targets",
                        lambda conn, targets: targets)
    monkeypatch.setattr(s6a.valence, "is_adverse",
                        lambda conn, cls: (False, "gain"))
    calls = iter(active_by_instant)
    monkeypatch.setattr(
        s6a.perm, "compute_permission",
        lambda swe, conn, cid, cls, targets, t_jd, dasha_periods=None:
            (0.0, {"systems_active": next(calls)}))
    return s6a.build_class_context(
        None, None, "chart-x", "marriage", [100.0, 200.0], [])


def test_union_semantics_across_sampled_instants(monkeypatch):
    entry = _unit_ctx(monkeypatch, [["vimshottari"], ["sade_sati", "vimshottari"]])
    ps = entry["permission_systems"]
    assert ps["vimshottari"] is True
    assert ps["sade_sati"] is True
    assert ps["mudda"] is False
    # exactly the 12 pinned ids, no more, no fewer
    assert set(ps) == set(leg.PERMISSION_SYSTEM_IDS)
    # permission_value is the pinned algebra over the same set
    assert entry["permission_value"] == pytest.approx(
        leg.compute_permission(ps))
    assert entry["sampled_instants"] == 2
    assert entry["per_system_fire_counts"] == {"vimshottari": 2, "sade_sati": 1}
    assert entry["class_valence"] == "gain" and entry["class_is_adverse"] is False


def test_no_system_fires_is_honest_zero_not_omission(monkeypatch):
    entry = _unit_ctx(monkeypatch, [[], []])
    assert entry is not None
    assert set(entry["systems_active"]) == set()
    assert entry["permission_value"] == 0.0
    assert all(v is False for v in entry["permission_systems"].values())


def test_unresolved_targets_omit_never_fabricate(monkeypatch):
    monkeypatch.setattr(s6a, "fetch_resonance_targets",
                        lambda conn, chart_id, cls: [])
    monkeypatch.setattr(s6a.enrichment, "enrich_targets",
                        lambda conn, targets: targets)
    assert s6a.build_class_context(
        None, None, "chart-x", "career", [100.0], []) is None


# ── disposable-DB integration ────────────────────────────────────────────────

S6A_CHART = "55555555-6666-7777-8888-999999999999"

DASHA_DDL = """
DROP TABLE IF EXISTS chart_dashas;
CREATE TABLE chart_dashas (
  chart_id UUID NOT NULL,
  ayanamsha_id TEXT NOT NULL,
  system_id TEXT NOT NULL,
  level_n INT NOT NULL,
  lord_graha TEXT,
  start_iso TEXT NOT NULL,
  end_iso TEXT NOT NULL
);
"""


def _wp6_reachable() -> bool:
    try:
        import psycopg
        with psycopg.connect(WP6_DSN, connect_timeout=3):
            return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def s6a_schema():
    if not _wp6_reachable():
        pytest.skip("NOT_RUN: disposable WP6 database unreachable")
    import psycopg

    conn = psycopg.connect(WP6_DSN, autocommit=True)
    conn.execute(_WP9_BASE_DDL)
    conn.execute(MIGRATION_1082.read_text())
    conn.execute(EXTRA_DDL)
    conn.execute(DASHA_DDL)
    conn.execute(WP6_DROP_SQL)
    conn.execute(WP6_MIGRATION_1072.read_text())
    conn.execute(WP6_MIGRATION_1087.read_text())
    conn.close()
    return True


EPISODES = [
    # marriage: Venus karaka contact, t_exact inside the vimshottari-Venus
    # fixture period (2020..2030)
    _episode("2026-02-05T12:00:00+00:00", "2026-02-15T12:00:00+00:00",
             "2026-02-25T12:00:00+00:00", body="Saturn", target_ref="Venus"),
    # career: Mars karaka contact; no fixture dasha lord matches Mars
    _episode("2026-03-01T12:00:00+00:00", "2026-03-10T12:00:00+00:00",
             "2026-03-20T12:00:00+00:00", body="Jupiter", target_ref="Mars"),
]

# The litigation contact (Saturn karaka, t_exact NULL — excluded from sampling
# and counted, so the class never enters the producer output) cannot go
# through the candidate build: t_exact feeds the contact_id hash, so the
# ledger writer rejects NULL. It is inserted by direct SQL after the build.
_NULL_TEXACT_CONTACT_SQL = """
INSERT INTO kala_gochara_contacts (
  chart_id, generation, contact_id, independence_group, body, relation,
  aspect_deg, target_type, target_ref, target_fact_id,
  target_resolution_state, target_longitude_deg, t_in, t_exact, t_out,
  bracket_seconds, tolerance_arcsec, truncated_at_horizon, branch,
  station_flag, exact_crossing, orb_max_deg, orb_source, dwell_days,
  epistemic_class, completeness_state, operator_role, precision_regime,
  time_basis, comparable_with, inclusivity, tier_basis, convention_id,
  ephemeris_backend, evidence_fact_ids, classical_citation,
  uncited_extension, corpus_verifiable, input_generation_vector_id,
  build_id, computed_at)
SELECT chart_id, generation, 's6a-litigation-null-texact',
  independence_group, 'Saturn', relation, aspect_deg, target_type, 'Saturn',
  target_fact_id, target_resolution_state, target_longitude_deg,
  '2026-04-01T00:00:00+00:00'::timestamptz, NULL,
  '2026-04-20T00:00:00+00:00'::timestamptz, bracket_seconds,
  tolerance_arcsec, truncated_at_horizon, branch, station_flag,
  exact_crossing, orb_max_deg, orb_source, dwell_days, epistemic_class,
  completeness_state, operator_role, precision_regime, time_basis,
  comparable_with, inclusivity, tier_basis, convention_id,
  ephemeris_backend, evidence_fact_ids, classical_citation,
  uncited_extension, corpus_verifiable, input_generation_vector_id,
  build_id, computed_at
FROM kala_gochara_contacts
WHERE chart_id = %s AND generation = '4.0' AND target_ref = 'Venus'
"""

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


@pytest.fixture()
def built(s6a_schema, tmp_path):
    """Candidate ledger (step06) + resolved map rows + a vimshottari dasha
    period whose lord is Venus (the marriage karaka). The producer has NOT
    run yet."""
    import psycopg

    from services.ka_vedha_gochara.freshness import (
        current_fingerprint, current_moorti_fingerprint)

    conn = psycopg.connect(WP6_DSN, autocommit=True)
    with conn.cursor() as cur:
        for table in ("kala_gochara_contacts", "kala_gochara_coverage",
                      "kala_gochara_publication", "gochara_resonance_map",
                      "kala_gochara_windows", "kala_vedha_gochara",
                      "kala_moorti_nirnaya", "chart_dashas"):
            cur.execute(f"DELETE FROM {table} WHERE chart_id = %s", (S6A_CHART,))
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
            [(S6A_CHART, "marriage", "karaka", "Venus", 0.9, None, True,
              "resolved", None),
             (S6A_CHART, "career", "karaka", "Mars", 0.5, None, True,
              "resolved", None),
             (S6A_CHART, "litigation", "karaka", "Saturn", 0.6, None, True,
              "resolved", None)])
        cur.executemany(
            "INSERT INTO chart_dashas (chart_id, ayanamsha_id, system_id,"
            " level_n, lord_graha, start_iso, end_iso) VALUES"
            " (%s,'lahiri_chitrapaksha',%s,1,%s,%s,%s)",
            [(S6A_CHART, "vimshottari", "Venus",
              "2020-01-01T00:00:00+00:00", "2030-01-01T00:00:00+00:00"),
             (S6A_CHART, "yogini", "Mangala",  # -> Moon; matches NO fixture class
              "2020-01-01T00:00:00+00:00", "2030-01-01T00:00:00+00:00")])

    vedha_fp = current_fingerprint(conn)
    moorti_fp = current_moorti_fingerprint(conn)
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO kala_vedha_gochara (chart_id, ayanamsha_id, vedha_kind,"
            " graha, window_start, window_end, start_truncated, end_truncated,"
            " janma_reference_fact_id, classical_citation, uncited_extension,"
            " grid_basis, detail, formula_version) VALUES"
            " (%s,%s,'house_vedha','Sun','2026-01-01','2026-02-01',false,false,"
            " 's6a.moon.lon','Phaladipika Adh. XXVI, Sloka 3',false,NULL,%s,'s6a')",
            (S6A_CHART, 'lahiri_chitrapaksha',
             json.dumps({"upstream_fingerprint": vedha_fp})))
        cur.execute(
            "INSERT INTO kala_moorti_nirnaya (chart_id, ayanamsha_id, graha,"
            " target_sign_idx, target_sign_name, window_start, window_end,"
            " start_truncated, end_truncated, moorti_computed,"
            " janma_nakshatra_idx, janma_nakshatra_fact_id, formula_version,"
            " upstream_fingerprint) VALUES"
            " (%s,%s,'Sun',2,'Gemini','2026-01-01','2026-02-01',false,false,false,"
            " 0,'s6a.moon.nak','s6a',%s)",
            (S6A_CHART, 'lahiri_chitrapaksha', json.dumps(moorti_fp)))
    conn.close()

    eps_path = tmp_path / "eps.json"
    cov_path = tmp_path / "cov.json"
    eps_path.write_text(json.dumps(EPISODES))
    cov_path.write_text(json.dumps(COVERAGE))
    r = subprocess.run(
        [sys.executable, str(STEP06_PATH), "--dsn", WP6_DSN,
         "--chart-id", S6A_CHART,
         "--horizon-start", "2026-01-01T00:00:00+00:00",
         "--horizon-end", "2026-06-01T00:00:00+00:00",
         "--episodes-json", str(eps_path), "--coverage-json", str(cov_path)],
        capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stderr
    with psycopg.connect(WP6_DSN, autocommit=True) as conn:
        # 1072 makes t_exact NOT NULL; the producer's NULL-t_exact exclusion is
        # defense for rows from divergent/older generations, so the fixture
        # relaxes the constraint locally to exercise it (the writer's own
        # fetch_contacts already tolerates t_exact None).
        conn.execute("ALTER TABLE kala_gochara_contacts"
                     " ALTER COLUMN t_exact DROP NOT NULL")
        conn.execute(_NULL_TEXACT_CONTACT_SQL, (S6A_CHART,))
    return {"chart": S6A_CHART, "ctx_out": tmp_path / "ctx.json"}


def _run_producer(chart, *extra, dsn=WP6_DSN):
    return subprocess.run(
        [sys.executable, str(PRODUCER_PATH), "--dsn", dsn,
         "--chart-id", chart, *extra],
        capture_output=True, text=True, timeout=300)


def _q(sql, args=()):
    import psycopg

    with psycopg.connect(WP6_DSN, autocommit=True) as conn:
        return conn.execute(sql, args).fetchone()[0]


def test_producer_wires_from_real_permission_and_feeds_writer(built):
    chart = built["chart"]
    r = _run_producer(chart, "--out", str(built["ctx_out"]))
    assert r.returncode == 0, r.stderr
    report = json.loads(r.stdout)
    assert report["classes_wired"] == ["career", "marriage"]
    assert report["contacts_null_t_exact_excluded"] == 1  # the litigation contact

    ctx = json.loads(built["ctx_out"].read_text())
    assert set(ctx) == {"marriage", "career"}  # litigation omitted (no usable instants)

    m = ctx["marriage"]
    assert set(m["permission_systems"]) == set(leg.PERMISSION_SYSTEM_IDS)
    # the vimshottari Venus period covers the contact instant and Venus is
    # the class karaka -> fires; the yogini Mangala(Moon) period matches no
    # marriage target -> does not
    assert m["permission_systems"]["vimshottari"] is True
    assert m["permission_systems"]["yogini"] is False
    assert "vimshottari" in m["systems_active"]
    assert m["permission_value"] == pytest.approx(
        leg.compute_permission(m["permission_systems"]))
    assert m["permission_value"] > 0.0
    assert m["context_source"].startswith("l1_permission_wiring:v1")

    # career: no fixture dasha lord matches Mars -> all twelve honest False
    c = ctx["career"]
    assert all(v is False for v in c["permission_systems"].values())
    assert c["permission_value"] == 0.0

    # the wired JSON feeds step06b end-to-end: marriage is projected with the
    # WIRED permission (not the rehearsal-synthetic one); litigation — contacts
    # but no context entry — lands in skipped_classes, zero '4.0' windows.
    rw = subprocess.run(
        [sys.executable, str(WRITER_PATH), "--dsn", WP6_DSN, "--chart-id", chart,
         "--horizon-start", "2026-01-01T00:00:00+00:00",
         "--horizon-end", "2026-06-01T00:00:00+00:00",
         "--class-context-json", str(built["ctx_out"])],
        capture_output=True, text=True, timeout=300)
    assert rw.returncode == 0, rw.stderr
    wrep = json.loads(rw.stdout)
    assert wrep["class_context_source"] if "class_context_source" in wrep else True
    skipped = {s["event_class"] for s in wrep["skipped_classes"]}
    assert "litigation" in skipped
    assert _q("SELECT count(*) FROM kala_gochara_windows WHERE chart_id=%s"
              " AND generation='4.0' AND event_class='litigation'",
              (chart,)) == 0
    by_class = {r["event_class"]: r for r in wrep["class_reports"]}
    assert by_class["marriage"]["permission"] == pytest.approx(
        m["permission_value"])
    assert "vimshottari" in by_class["marriage"]["permission_systems_active"]
    assert _q("SELECT count(*) FROM kala_gochara_windows WHERE chart_id=%s"
              " AND generation='4.0' AND event_class='marriage'",
              (chart,)) > 0
    # the projected rows carry the wired contributing system
    assert _q("SELECT bool_and(contributing_systems @> '[\"vimshottari\"]'::jsonb)"
              " FROM kala_gochara_windows WHERE chart_id=%s"
              " AND generation='4.0' AND event_class='marriage'",
              (chart,)) is True
    # career wired at honest 0.0 permission projects zero windows (never a
    # fabricated floor)
    assert _q("SELECT count(*) FROM kala_gochara_windows WHERE chart_id=%s"
              " AND generation='4.0' AND event_class='career'",
              (chart,)) == 0


def test_production_refusal_exit_4():
    r = _run_producer(
        S6A_CHART, dsn="postgresql://u:x@db.prod.example:5432/prod")
    assert r.returncode == 4 and "REFUSED" in r.stderr
    r2 = _run_producer(S6A_CHART, dsn="postgresql://u:x@127.0.0.1:5433/prod")
    assert r2.returncode == 4 and "REFUSED" in r2.stderr


def test_no_candidate_contacts_exit_3(built):
    import psycopg

    with psycopg.connect(WP6_DSN, autocommit=True) as conn:
        conn.execute("DELETE FROM kala_gochara_contacts WHERE chart_id = %s",
                     (S6A_CHART,))
    r = _run_producer(S6A_CHART)
    assert r.returncode == 3, (r.returncode, r.stdout, r.stderr)
