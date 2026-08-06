"""Tests for the bg_parihara_rules writer.

Two tiers, matching the project's test-writer convention:

1. Offline (always runs, no DB required): proves the pure-Python
   materialization functions (activity rules from panchang_engine.
   shastra_tables.EVENT_TABLES; the hand-curated census register; the
   cancellation-condition/citation extraction helpers) are correct,
   deterministic, and honest (no fabricated dispositions/citations).
2. Live (skipped unless DATABASE_URL is set): runs the writer against a real
   DB connection (which JOINS brahma_dosha_catalog + classical_texts) and
   asserts row counts, idempotency, citation non-nullness, and the
   citation-tradition placeholder EXCLUSION invariant.
"""
from __future__ import annotations

import os
import uuid

import pytest
import psycopg

from pipeline.orchestrator.writers.bg_parihara_rules import (
    ACTIVITY_CITATIONS,
    BgPariharaRulesWriter,
    CENSUS_ROWS,
    _build_citation,
    _extract_conditions,
    build_activity_rule_rows,
    build_census_rows,
)
from pipeline.orchestrator.writers import ContextSpec


# ── Offline tests: _extract_conditions (pure function) ───────────────────────

def test_extract_conditions_handles_bhanga_list_shape():
    conditions = _extract_conditions({"bhanga": ["a", "b", "c"]})
    assert conditions == ["a", "b", "c"]


def test_extract_conditions_handles_applies_string_shape():
    """A couple of real brahma_dosha_catalog rows (kuja_dosha_bhanga_own_sign,
    kuja_dosha_bhanga_exaltation) use an 'applies' key holding a plain string,
    not a list — confirmed via live DB query during construction."""
    conditions = _extract_conditions({"applies": "This entry is itself a cancellation record"})
    assert conditions == ["This entry is itself a cancellation record"]


def test_extract_conditions_empty_dict_yields_empty_list():
    assert _extract_conditions({}) == []


# ── Offline tests: _build_citation (pure function) ───────────────────────────

def test_build_citation_skips_classical_tradition_placeholder():
    """The 'classical_tradition' placeholder (found on 53/79 brahma_dosha_catalog
    rows during construction) must NEVER be selected as a citation source."""
    citations = [{"text_id": "classical_tradition"}, {"text_id": "bphs", "chapter": 9}]
    citation, text_id, chapter = _build_citation(citations, {"bphs": "Brihat Parasara Hora Sastra"})
    assert text_id == "bphs"
    assert chapter == 9
    assert "Brihat Parasara Hora Sastra" in citation
    assert "classical_tradition" not in citation


def test_build_citation_without_chapter():
    citation, text_id, chapter = _build_citation([{"text_id": "bphs"}], {"bphs": "Brihat Parasara Hora Sastra"})
    assert text_id == "bphs"
    assert chapter is None
    assert "ch." not in citation


# ── Offline tests: build_activity_rule_rows (pure, reuses panchang_engine) ───

def test_build_activity_rule_rows_covers_all_eight_activities():
    rows = build_activity_rule_rows(build_id=str(uuid.uuid4()))
    activities = {r["activity_class"] for r in rows}
    assert activities == {
        "vivah", "griha_pravesh", "vyapara", "yatra", "property_purchase",
        "mantra_initiation", "upaya_ritual", "sadhana_initiation",
    }


def test_build_activity_rule_rows_only_tithi_nakshatra_vara_factor_types():
    rows = build_activity_rule_rows(build_id=str(uuid.uuid4()))
    factor_types = {r["factor_type"] for r in rows}
    assert factor_types == {"tithi", "nakshatra", "vara"}


def test_build_activity_rule_rows_quality_scores_in_range():
    rows = build_activity_rule_rows(build_id=str(uuid.uuid4()))
    assert rows, "expected non-empty activity rule rows"
    for r in rows:
        assert 0.0 <= r["quality_score"] <= 1.0


def test_build_activity_rule_rows_every_row_has_a_citation():
    rows = build_activity_rule_rows(build_id=str(uuid.uuid4()))
    for r in rows:
        assert r["source_citation"], f"{r['activity_class']}/{r['factor_type']}/{r['factor_id']}: missing citation"


def test_activity_citations_cover_every_event_table_key():
    """Every activity_class the reused EVENT_TABLES dict defines must have an
    explicit citation mapped — no silent fallback-to-generic string."""
    from panchang_engine.shastra_tables import EVENT_TABLES
    for activity_class in EVENT_TABLES:
        assert activity_class in ACTIVITY_CITATIONS, f"missing citation mapping for {activity_class!r}"


def test_build_activity_rule_rows_matches_source_table_row_count():
    """Materialization must be lossless: row count == sum of all (activity,
    factor_type) dict sizes in the reused EVENT_TABLES."""
    from panchang_engine.shastra_tables import EVENT_TABLES
    expected = sum(
        len(factor_map)
        for quality_table in EVENT_TABLES.values()
        for factor_type, factor_map in quality_table.items()
        if factor_type in ("tithi", "nakshatra", "vara")
    )
    rows = build_activity_rule_rows(build_id=str(uuid.uuid4()))
    assert len(rows) == expected


# ── Offline tests: build_census_rows / CENSUS_ROWS (hand-curated register) ───

def test_census_rows_every_row_has_valid_disposition():
    valid = {"computed", "not_computed", "not_in_corpus"}
    for factor_family, factor_name, disposition, note, evidence_pointer, school_tag in CENSUS_ROWS:
        assert disposition in valid, f"{factor_family}/{factor_name}: invalid disposition {disposition!r}"
        assert note, f"{factor_family}/{factor_name}: missing citation_or_gap_note"
        assert evidence_pointer, f"{factor_family}/{factor_name}: missing evidence_pointer"


def test_census_rows_no_duplicate_natural_keys():
    keys = [(fam, name) for fam, name, *_ in CENSUS_ROWS]
    assert len(keys) == len(set(keys)), "duplicate (factor_family, factor_name) in CENSUS_ROWS"


def test_census_has_no_dangling_lattice_pointers():
    """Regression test for the Opus corpus-citation review defect (2026-07-30):
    several bg_muhurta_lattice.py factor_keys (yamakantaka, krakaca,
    sashtighati, visha_ghati, varjyam, panchaka, ghati_muhurta, and the 6
    Sandhya/Vijaya/Godhuli/Nishita keys) were disclosed as
    computed_uncited_convention / 'corpus gap' but had NO corresponding row
    in CENSUS_ROWS -- an honesty mechanism that points to a census entry
    which doesn't exist. Every factor_key bg_muhurta_lattice.py emits must
    resolve to at least one CENSUS_ROWS evidence_pointer mentioning it."""
    from pipeline.orchestrator.writers.bg_muhurta_lattice import (
        COMBINATION_YOGA_CITATIONS,
        KALAM_CITATIONS,
    )

    all_factor_keys = set(COMBINATION_YOGA_CITATIONS.keys()) | set(KALAM_CITATIONS.keys()) | {
        "agni_vasa", "agni_vasa_mc_arithmetic", "ghati_muhurta_30fold",
    }
    # A handful of lattice factor_keys are deliberately renamed in the census
    # (e.g. the census groups amrit_kalam under a combined
    # 'amrita_ghati_amrit_kalam' row, and 'gulika_kalam' under
    # 'gulika_mandi_kalam') -- these resolve via the evidence_pointer's
    # explicit 'factor_key=X' text, checked separately below.
    census_factor_names = {(row[0], row[1]) for row in CENSUS_ROWS}  # (family, name)
    evidence_text = " ".join(row[4] for row in CENSUS_ROWS)  # evidence_pointer is index 4

    missing = []
    for key in sorted(all_factor_keys):
        if key == "ghati_muhurta_30fold":
            if ("ghati_muhurta", "ghati_muhurta_30fold") not in census_factor_names:
                missing.append(key)
            continue
        # Resolves if EITHER some census row's own factor_name IS this key
        # (the common case: combination_yoga/agnivasa keys), OR some row's
        # evidence_pointer explicitly names it via 'factor_key=X' (the
        # day_part-family rows, which reference bg_muhurta_lattice's kalam
        # factor_keys by name even when the census factor_name differs).
        resolved = (
            any(name == key for _fam, name in census_factor_names)
            or f"factor_key={key}" in evidence_text
        )
        if not resolved:
            missing.append(key)

    assert not missing, f"factor_keys with no resolving census evidence_pointer: {missing}"


def test_census_includes_the_named_corpus_gaps_honestly():
    """The brief explicitly names Agnivasa combination-yoga rules as the
    expected 'genuinely lacks a rule' example — the four brief-named
    combination-yogas panchang_engine does NOT implement must be present and
    disposed not_in_corpus, never silently omitted or falsely marked computed."""
    by_name = {(fam, name): disposition for fam, name, disposition, *_ in CENSUS_ROWS}
    for gap in ["mrityu_yoga", "dagdha_yoga", "hutasana_yoga", "jvalamukhi_yoga"]:
        key = ("combination_yoga", gap)
        assert key in by_name, f"expected census row for gap {gap!r}"
        assert by_name[key] == "not_in_corpus", f"{gap!r} must be disposed not_in_corpus, got {by_name[key]!r}"


def test_census_includes_computed_combination_yogas_that_do_exist():
    by_name = {(fam, name): disposition for fam, name, disposition, *_ in CENSUS_ROWS}
    for real in ["sarvartha_siddhi", "amrit_siddhi", "ravi_pushya", "guru_pushya",
                 "tripushkar", "dwipushkar", "siddha_yoga"]:
        key = ("combination_yoga", real)
        assert key in by_name, f"expected census row for {real!r}"
        assert by_name[key] == "computed", f"{real!r} must be disposed computed, got {by_name[key]!r}"


def test_build_census_rows_row_count_matches_constant():
    rows = build_census_rows(build_id=str(uuid.uuid4()))
    assert len(rows) == len(CENSUS_ROWS)


# ── Offline: writer registration + dry_run ────────────────────────────────────

def test_writer_registered():
    from pipeline.orchestrator.writers import get_writer
    writer_cls = get_writer("bg_parihara_rules")
    assert writer_cls is BgPariharaRulesWriter
    assert writer_cls.asset_id == "bg_parihara_rules"


def test_writer_dry_run_no_db_needed():
    writer = BgPariharaRulesWriter()
    ctx = ContextSpec(
        asset_id="bg_parihara_rules", build_id=str(uuid.uuid4()), db_conn=None, dry_run=True,
    )
    result = writer.run(ctx)
    assert result.asset_id == "bg_parihara_rules"
    assert result.rows_inserted == 0
    assert result.notes == "dry_run"


# ── Live tests (require DATABASE_URL; skipped otherwise) ─────────────────────

@pytest.fixture(scope="module")
def db_conn():
    url = os.environ.get("DATABASE_URL") or os.environ.get("PROD_DB_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    conn = psycopg.connect(url, row_factory=psycopg.rows.dict_row)
    yield conn
    conn.rollback()
    conn.close()


def test_bg_parihara_rules_writer_runs(db_conn):
    writer = BgPariharaRulesWriter()
    ctx = ContextSpec(asset_id="bg_parihara_rules", build_id=str(uuid.uuid4()), db_conn=db_conn)
    result = writer.run(ctx)
    db_conn.commit()
    assert result.asset_id == "bg_parihara_rules"
    assert result.rows_inserted >= 0


def test_bg_parihara_rules_excludes_classical_tradition_placeholder(db_conn):
    """Hard invariant: no row in bg_parihara_rules may trace to the
    'classical_tradition' placeholder citation — every row must be REAL-cited."""
    cur = db_conn.cursor()
    cur.execute("SELECT count(*) AS n FROM bg_parihara_rules WHERE source_text_id = 'classical_tradition'")
    n = cur.fetchone()["n"]
    assert n == 0, f"bg_parihara_rules has {n} rows citing the classical_tradition placeholder"


def test_bg_parihara_rules_no_null_citations(db_conn):
    for table in ("bg_parihara_rules", "bg_muhurta_activity_rules"):
        cur = db_conn.cursor()
        cur.execute(f"SELECT count(*) AS n FROM {table} WHERE source_citation IS NULL")
        n = cur.fetchone()["n"]
        assert n == 0, f"{table} has {n} rows with NULL source_citation"


def test_bg_muhurta_factor_census_dispositions_are_valid(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT DISTINCT disposition FROM bg_muhurta_factor_census")
    dispositions = {r["disposition"] for r in cur.fetchall()}
    assert dispositions <= {"computed", "not_computed", "not_in_corpus"}


def test_bg_parihara_rules_writer_idempotent(db_conn):
    """Re-running the writer refreshes (upserts) rather than duplicates —
    row count must be stable across two consecutive runs in the same
    transaction (§N.3 upsert idempotency: DO UPDATE, not DO NOTHING, since
    this writer mirrors a live upstream table)."""
    writer = BgPariharaRulesWriter()
    ctx = ContextSpec(asset_id="bg_parihara_rules", build_id=str(uuid.uuid4()), db_conn=db_conn)

    writer.run(ctx)
    db_conn.commit()

    cur = db_conn.cursor()
    cur.execute(
        "SELECT (SELECT count(*) FROM bg_parihara_rules) + "
        "(SELECT count(*) FROM bg_muhurta_activity_rules) + "
        "(SELECT count(*) FROM bg_muhurta_factor_census) AS n"
    )
    count_before = cur.fetchone()["n"]

    result = writer.run(ctx)
    db_conn.commit()

    cur.execute(
        "SELECT (SELECT count(*) FROM bg_parihara_rules) + "
        "(SELECT count(*) FROM bg_muhurta_activity_rules) + "
        "(SELECT count(*) FROM bg_muhurta_factor_census) AS n"
    )
    count_after = cur.fetchone()["n"]

    assert count_before == count_after, f"Idempotency broken: {count_before} -> {count_after}"
    assert result.rows_inserted >= 0
