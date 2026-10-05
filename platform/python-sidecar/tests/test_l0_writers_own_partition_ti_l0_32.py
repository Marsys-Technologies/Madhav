"""TI-L0-32 (CF-02): a shared L0 writer reports ITS OWN partition in `rows_written`.

Live defect (Build.completion FAIL, record-only): the medical writer is registered for three asset
ids and returns the sum of its three seeds (60 = 21 + 27 + 12) against a count_sql that sees 21 for
bg_medical_mappings; the transit writer returns 104 (9 engine + 68 rule + 27 moorti) against 76.
After this change `rows_written` for a dispatched id equals that id's own table count, a row seeded
in a sibling table cannot move it, and a dispatch id the class does not own fails loudly.

No row in any table changes: this is a build-record attribution fix. (The declared produced-table
set naming bg_transit_moorti is a declarations-file change and is NOT done here.)
"""
from __future__ import annotations

import pytest

import brahmagyan.l0_medical as M
import brahmagyan.l0_transit as T
from pipeline.orchestrator.writers import ContextSpec, get_writer
from pipeline.orchestrator.writers.bg_medical_mappings import BgMedicalMappingsWriter
from pipeline.orchestrator.writers.bg_transit_rules import BgTransitRulesWriter
from tests._l0d_pg import requires_pg, scratch_schema


def ctx(asset_id, conn=None, dry_run=False):
    return ContextSpec(asset_id=asset_id, build_id="b", db_conn=conn, dry_run=dry_run)


# ── 1. unit (writer logic, seed stubbed) ─────────────────────────────────────

@pytest.mark.parametrize("asset,own", [("bg_medical_mappings", 21), ("bg_nakshatra_medical", 27), ("bg_sign_medical", 12)])
def test_medical_writer_reports_the_dispatched_assets_own_count(monkeypatch, asset, own):
    import pipeline.orchestrator.writers.bg_medical_mappings as W
    monkeypatch.setattr(W, "seed_medical_mappings", lambda **_k: {"bg_medical_mappings": 21, "bg_nakshatra_medical": 27, "bg_sign_medical": 12})
    r = BgMedicalMappingsWriter().run(ctx(asset))
    assert r.rows_inserted == own and "of 60 total" in r.notes


def test_medical_writer_refuses_an_id_it_does_not_own(monkeypatch):
    import pipeline.orchestrator.writers.bg_medical_mappings as W
    monkeypatch.setattr(W, "seed_medical_mappings", lambda **_k: {"bg_medical_mappings": 21, "bg_nakshatra_medical": 27, "bg_sign_medical": 12})
    with pytest.raises(RuntimeError, match="refusing to report another asset"):
        BgMedicalMappingsWriter().run(ctx("bg_ontology"))


def test_medical_dry_run_still_works_for_every_registered_id(monkeypatch):
    for a in ("bg_medical_mappings", "bg_nakshatra_medical", "bg_sign_medical"):
        assert BgMedicalMappingsWriter().run(ctx(a, dry_run=True)).rows_inserted == 0


@pytest.mark.parametrize("asset,own", [("bg_transit_rules", 69), ("bg_transit_engine", 9)])
def test_transit_writer_reports_the_dispatched_assets_own_count(monkeypatch, asset, own):
    monkeypatch.setattr(T, "seed_transit_rules", lambda conn, dry_run=False: {
        "bg_transit_engine": 9, "bg_transit_rules": 69, "bg_transit_moorti": 27, "total": 105})
    r = BgTransitRulesWriter().run(ctx(asset))
    assert r.rows_inserted == own and "bg_transit_moorti=27" in r.notes and "of 105 total" in r.notes


def test_transit_writer_refuses_an_id_it_does_not_own(monkeypatch):
    monkeypatch.setattr(T, "seed_transit_rules", lambda conn, dry_run=False: {"bg_transit_engine": 9, "bg_transit_rules": 69, "bg_transit_moorti": 27, "total": 105})
    with pytest.raises(RuntimeError, match="refusing to report another asset"):
        BgTransitRulesWriter().run(ctx("bg_transit_moorti"))


def test_registrations_are_unchanged():
    assert get_writer("bg_sign_medical") is BgMedicalMappingsWriter
    assert get_writer("bg_nakshatra_medical") is BgMedicalMappingsWriter
    assert get_writer("bg_medical_mappings") is BgMedicalMappingsWriter
    assert get_writer("bg_transit_engine") is BgTransitRulesWriter and get_writer("bg_transit_rules") is BgTransitRulesWriter


# ── 2. real PostgreSQL ───────────────────────────────────────────────────────

DDL = """
CREATE TABLE bg_medical_mappings (id serial PRIMARY KEY, graha text NOT NULL UNIQUE, dosha text[], dhatu text[], organ_systems text[],
  body_part text[], disease_tendency text[], classical_citation text NOT NULL);
CREATE TABLE bg_nakshatra_medical (id serial PRIMARY KEY, nakshatra_name text NOT NULL UNIQUE, nakshatra_number integer, body_part text NOT NULL,
  classical_citation text NOT NULL, dosha text);
CREATE TABLE bg_sign_medical (sign_number integer PRIMARY KEY CHECK (sign_number BETWEEN 1 AND 12), sign_name text NOT NULL UNIQUE, body_part text NOT NULL,
  organ_systems text[], element text NOT NULL CHECK (element IN ('fire','earth','air','water')), dosha text NOT NULL, classical_citation text NOT NULL);
CREATE TABLE bg_transit_engine (id serial PRIMARY KEY, graha text NOT NULL UNIQUE, avg_daily_motion_deg double precision NOT NULL,
  zodiac_period_days double precision NOT NULL, sign_residence_days double precision NOT NULL, classical_citation text NOT NULL);
CREATE TABLE bg_transit_rules (id serial PRIMARY KEY, rule_type text NOT NULL, graha text NOT NULL, primary_house integer NOT NULL, vedha_house integer,
  phala text NOT NULL, classical_citation text NOT NULL, rule_notes text, CONSTRAINT u UNIQUE (graha, rule_type, primary_house));
CREATE TABLE bg_transit_moorti (nakshatra_offset integer PRIMARY KEY, moorti_name text NOT NULL, quality_tier integer NOT NULL, phala_brief text NOT NULL,
  classical_citation text NOT NULL, rule_notes text);
"""


def count(conn, t):
    return conn.execute(f"SELECT count(*) AS n FROM {t}").fetchone()["n"]


@requires_pg
def test_real_medical_rows_written_equals_the_dispatched_tables_count_and_ignores_siblings():
    with scratch_schema(DDL) as conn:
        for a, t in (("bg_medical_mappings", "bg_medical_mappings"), ("bg_nakshatra_medical", "bg_nakshatra_medical"), ("bg_sign_medical", "bg_sign_medical")):
            r = BgMedicalMappingsWriter().run(ctx(a, conn))
            conn.commit()
            assert r.rows_inserted == count(conn, t), (a, r.rows_inserted, count(conn, t))
        assert (count(conn, "bg_medical_mappings"), count(conn, "bg_nakshatra_medical"), count(conn, "bg_sign_medical")) == (21, 27, 12)
        # a stray row in a SIBLING table must not move this asset's figure
        conn.execute("INSERT INTO bg_sign_medical VALUES (1,'zz_extra','x','{}', 'fire','x','x') ON CONFLICT DO NOTHING")
        conn.execute("DELETE FROM bg_sign_medical WHERE sign_name='zz_extra'")
        before = {t: list(conn.execute(f"SELECT * FROM {t} ORDER BY 1")) for t in ("bg_medical_mappings", "bg_nakshatra_medical", "bg_sign_medical")}
        r = BgMedicalMappingsWriter().run(ctx("bg_medical_mappings", conn))
        conn.commit()
        assert r.rows_inserted == 21
        assert {t: list(conn.execute(f"SELECT * FROM {t} ORDER BY 1")) for t in before} == before, "no row changed by the attribution fix"


@requires_pg
def test_real_transit_rows_written_equals_the_dispatched_tables_count_and_no_row_changes():
    with scratch_schema(DDL) as conn:
        r_rules = BgTransitRulesWriter().run(ctx("bg_transit_rules", conn))
        conn.commit()
        r_engine = BgTransitRulesWriter().run(ctx("bg_transit_engine", conn))
        conn.commit()
        assert r_rules.rows_inserted == count(conn, "bg_transit_rules") == len(T.BG_TRANSIT_RULES)
        assert r_engine.rows_inserted == count(conn, "bg_transit_engine") == 9
        assert count(conn, "bg_transit_moorti") == 27 and "bg_transit_moorti=27" in r_rules.notes
        before = {t: list(conn.execute(f"SELECT * FROM {t} ORDER BY 1")) for t in ("bg_transit_rules", "bg_transit_engine", "bg_transit_moorti")}
        BgTransitRulesWriter().run(ctx("bg_transit_rules", conn))
        conn.commit()
        assert {t: list(conn.execute(f"SELECT * FROM {t} ORDER BY 1")) for t in before} == before
