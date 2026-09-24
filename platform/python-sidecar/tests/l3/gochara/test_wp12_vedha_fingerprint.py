"""§12.9 — upstream fingerprint, staleness detector, and the candidate-build gate.

The defect (§N.8, earned signal). `ka_vedha_gochara` copies each `bg_transit_rules`
citation verbatim but recorded nothing about the input it consumed. After the L0
repair re-cited the rules, the canonical chart's 132 house_vedha rows (built
2026-09-07) still cite the struck 'BPHS Ch.29', and NOTHING in the system could
report that — no code path existed that could read "stale".

What this file proves:
  * the fingerprint is deterministic and sensitive to exactly the inputs consumed;
  * a rebuild stamps it on every house_vedha row;
  * the detector reads STALE for (a) a changed upstream rule and (b) rows that
    carry no fingerprint at all — the pre-existing 132-row situation — and FRESH
    only after a rebuild;
  * the step-6 gate refuses to build a candidate on stale rows (exit 7).

Pure tests run anywhere; DB tests use the disposable WP6 Postgres only and skip
NOT_RUN when unreachable.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import psycopg
import pytest

from services.ka_vedha_gochara.logic import upstream_fingerprint

from .test_wp9_stamp_columns import (
    BASE_DDL,
    CHART_ID,
    MIGRATION_1082,
    WP6_DSN,
    _seed,
    _wp6_reachable,
)

KIT = Path(__file__).resolve().parents[3] / "scripts" / "kala_gochara_cutover"

RULE_A = {"vedha_house": 5, "phala": "gain", "classical_citation": "Phaladipika Adh. XXVI, Sloka 3"}
RULE_B = {"vedha_house": 9, "phala": "loss", "classical_citation": "UNSOURCED"}
SCALE = {1: {"effect_grade": "agitation", "source_citation": "PG353"}}


# ── pure: the fingerprint itself ─────────────────────────────────────────────
def test_fingerprint_is_deterministic_and_order_independent():
    a = upstream_fingerprint({("sun", 3): RULE_A, ("rahu", 11): RULE_B}, SCALE)
    b = upstream_fingerprint({("rahu", 11): RULE_B, ("sun", 3): RULE_A}, SCALE)
    assert a == b
    assert a["bg_transit_rules"] and a["bg_vedha_malefic_scale"]
    assert a["n_transit_rules"] == 2


def test_fingerprint_changes_when_a_citation_changes():
    """The exact defect: an upstream re-citation must change the digest."""
    before = upstream_fingerprint({("sun", 3): RULE_A}, SCALE)
    recited = dict(RULE_A, classical_citation="BPHS Ch.29 (Gochara Phala — Transit Results)")
    after = upstream_fingerprint({("sun", 3): recited}, SCALE)
    assert before["bg_transit_rules"] != after["bg_transit_rules"]
    assert before["bg_vedha_malefic_scale"] == after["bg_vedha_malefic_scale"]


@pytest.mark.parametrize("field,new", [("phala", "different"), ("vedha_house", 6)])
def test_fingerprint_changes_when_other_consumed_fields_change(field, new):
    base = upstream_fingerprint({("sun", 3): RULE_A}, SCALE)
    changed = upstream_fingerprint({("sun", 3): dict(RULE_A, **{field: new})}, SCALE)
    assert base["bg_transit_rules"] != changed["bg_transit_rules"]


def test_fingerprint_changes_when_the_malefic_scale_changes():
    base = upstream_fingerprint({("sun", 3): RULE_A}, SCALE)
    other = upstream_fingerprint(
        {("sun", 3): RULE_A}, {1: {"effect_grade": "fear", "source_citation": "PG353"}}
    )
    assert base["bg_vedha_malefic_scale"] != other["bg_vedha_malefic_scale"]


def test_adding_or_removing_a_rule_changes_the_fingerprint():
    one = upstream_fingerprint({("sun", 3): RULE_A}, SCALE)
    two = upstream_fingerprint({("sun", 3): RULE_A, ("rahu", 11): RULE_B}, SCALE)
    assert one["bg_transit_rules"] != two["bg_transit_rules"]
    assert (one["n_transit_rules"], two["n_transit_rules"]) == (1, 2)


# ── DB: build → fresh; upstream change → stale; unfingerprinted rows → stale ─
@pytest.fixture()
def db():
    if not _wp6_reachable():
        pytest.skip("NOT_RUN: disposable WP6 database unreachable")
    c = psycopg.connect(WP6_DSN, autocommit=True)
    c.execute(BASE_DDL)
    c.execute(MIGRATION_1082.read_text())
    c.close()
    seed = psycopg.connect(WP6_DSN)
    _seed(seed)
    seed.commit()
    seed.close()
    yield
    # leave the schema in place; every test that needs it rebuilds it


def _build():
    import services.ka_vedha_gochara.writer as vw

    conn = psycopg.connect(WP6_DSN)
    ctx = SimpleNamespace(db_conn=conn, config={"chart_id": CHART_ID}, dry_run=False)
    orig = vw._compute_ayanamsha_offset
    vw._compute_ayanamsha_offset = lambda _d: 0.0
    try:
        vw.KaVedhaGocharaWriter().run(ctx)
        conn.commit()
    finally:
        vw._compute_ayanamsha_offset = orig
        conn.close()


def _check():
    from services.ka_vedha_gochara.freshness import check_house_vedha_freshness

    with psycopg.connect(WP6_DSN, autocommit=True) as c:
        return check_house_vedha_freshness(c, CHART_ID)


def _exec(sql, params=()):
    with psycopg.connect(WP6_DSN, autocommit=True) as c:
        c.execute(sql, params)


def test_rebuild_stamps_the_fingerprint_and_the_detector_reads_fresh(db):
    _build()
    with psycopg.connect(WP6_DSN, autocommit=True) as c:
        n, n_fp = c.execute(
            "SELECT count(*), count(detail->'upstream_fingerprint') "
            "FROM kala_vedha_gochara WHERE vedha_kind='house_vedha'"
        ).fetchone()
    assert n > 0, "vacuous: the fixture produced no house_vedha rows"
    assert n_fp == n, f"{n - n_fp} house_vedha rows carry no upstream fingerprint"
    r = _check()
    assert r.state == "fresh", r
    assert (r.total, r.missing, r.mismatched) == (n, 0, 0)


def test_an_upstream_recitation_makes_existing_rows_stale(db):
    """The L0 repair scenario: rules re-cited AFTER the rows were built."""
    _build()
    assert _check().state == "fresh"
    _exec("UPDATE bg_transit_rules SET classical_citation = 'Phaladipika Adh. XXVI, Sloka 3 (re-cited)' "
          "WHERE graha = 'sun'")
    r = _check()
    assert r.state == "stale", r
    assert r.mismatched == r.total > 0 and r.missing == 0


def test_rows_with_no_fingerprint_read_stale_not_fresh(db):
    """The 132-row situation: built before fingerprints existed. Unknown provenance
    must never read as fresh."""
    _build()
    _exec("UPDATE kala_vedha_gochara SET detail = detail - 'upstream_fingerprint' "
          "WHERE vedha_kind = 'house_vedha'")
    r = _check()
    assert r.state == "stale", r
    assert r.missing == r.total > 0 and r.mismatched == 0


def test_a_rebuild_after_the_change_restores_fresh(db):
    _build()
    _exec("UPDATE bg_transit_rules SET phala = 'changed upstream' WHERE graha = 'sun'")
    assert _check().state == "stale"
    _build()
    assert _check().state == "fresh"


def test_no_rows_is_reported_as_no_rows_not_fresh(db):
    _exec("DELETE FROM kala_vedha_gochara")
    assert _check().state == "no_rows"


def test_absent_table_is_not_run_not_fresh():
    from services.ka_vedha_gochara.freshness import check_house_vedha_freshness

    if not _wp6_reachable():
        pytest.skip("NOT_RUN: disposable WP6 database unreachable")
    with psycopg.connect(WP6_DSN, autocommit=True) as c:
        c.execute("DROP TABLE IF EXISTS kala_vedha_gochara")
        r = check_house_vedha_freshness(c, CHART_ID)
    assert r.state == "table_absent"


# ── the gate ─────────────────────────────────────────────────────────────────
def test_gate_admits_only_a_fresh_report():
    from services.ka_vedha_gochara.freshness import FreshnessReport, gate_allows_build

    for state, ok in [("fresh", True), ("stale", False), ("no_rows", False), ("table_absent", False)]:
        assert gate_allows_build(FreshnessReport(state=state, total=1, missing=0, mismatched=0, current=None)) is ok


def _load_step06():
    sys.path.insert(0, str(KIT))
    try:
        spec = importlib.util.spec_from_file_location("step06_under_test", KIT / "step06_candidate_build.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.path.remove(str(KIT))


def test_step06_refuses_to_build_on_stale_vedha_rows(db, tmp_path, monkeypatch, capsys):
    """The gate is wired: stale rows -> exit 7, before any ledger write."""
    _build()
    _exec("UPDATE kala_vedha_gochara SET detail = detail - 'upstream_fingerprint' "
          "WHERE vedha_kind = 'house_vedha'")
    (tmp_path / "e.json").write_text("[]")
    (tmp_path / "c.json").write_text("[]")
    step06 = _load_step06()
    monkeypatch.setattr(sys, "argv", [
        "step06", "--dsn", WP6_DSN, "--chart-id", CHART_ID,
        "--episodes-json", str(tmp_path / "e.json"), "--coverage-json", str(tmp_path / "c.json"),
    ])
    rc = step06.main()
    assert rc == 7, f"expected refusal (7), got {rc}"
    assert "stale" in capsys.readouterr().err.lower()
