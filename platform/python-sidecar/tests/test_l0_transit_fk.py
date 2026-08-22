"""
Integration test: bg_transit_rules writer uses upsert plus a category-scoped
retirement sweep (F-145) — never a blanket delete-then-insert.

Original defect this guarded: DELETE FROM bg_transit_rules was blocked by the
gochara_resonance_map FK (ForeignKeyViolation), because delete-then-insert renumbers
the SERIAL `id` column and silently corrupts gochara_resonance_map.source_rule_id
citation references.

F-145 (writer-owned category reconciliation) intentionally introduced a real,
narrowly-scoped retirement sweep: `DELETE FROM bg_transit_rules WHERE id = %s`,
restricted to rows in the writer's own owned (rule_type, graha) categories whose key
is absent from BG_TRANSIT_RULES. A bare literal-source-string check
(`'DELETE FROM bg_transit_rules' not in source`) can no longer distinguish "the
dangerous blanket delete regressed" from "the ruled, id-scoped retirement sweep is
present and correct" — it would now fail on correct code. Per CLAUDE.md §N.8, this
test is upgraded to assert the real safety property (scoped-by-id, never blanket)
and the real reconciliation behaviour, instead of a string that stopped being able to
distinguish the two cases it exists to distinguish.
"""
import inspect
import logging
from unittest.mock import MagicMock

import pytest

from brahmagyan.l0_transit import (
    BG_TRANSIT_RULES,
    _owned_categories,
    compute_stale_rule_ids,
    seed_transit_rules,
)


# ── Sibling literal-source checks (unaffected by F-145; still correct) ──────────

def test_no_delete_from_bg_transit_engine():
    """seed_transit_rules must NOT delete from bg_transit_engine."""
    source = inspect.getsource(seed_transit_rules)
    assert 'DELETE FROM bg_transit_engine' not in source


def test_no_delete_from_bg_transit_moorti():
    """seed_transit_rules must NOT delete from bg_transit_moorti."""
    source = inspect.getsource(seed_transit_rules)
    assert 'DELETE FROM bg_transit_moorti' not in source


def test_upsert_patterns_present():
    """ON CONFLICT upsert patterns must exist for all three tables."""
    source = inspect.getsource(seed_transit_rules)
    assert 'ON CONFLICT (graha) DO UPDATE' in source, "Missing upsert for bg_transit_engine"
    assert 'ON CONFLICT (graha, rule_type, primary_house) DO UPDATE' in source, "Missing upsert for bg_transit_rules"
    assert 'ON CONFLICT (nakshatra_offset) DO UPDATE' in source, "Missing upsert for bg_transit_moorti"


# ── F-145: real-behaviour replacement for the old literal-string check ──────────

def test_bg_transit_rules_delete_is_scoped_by_id_never_blanket():
    """
    Any DELETE FROM bg_transit_rules in seed_transit_rules must be scoped to a single
    row id (`WHERE id = %s`) — never a blanket/unscoped delete. A blanket delete would
    renumber the SERIAL id column and corrupt gochara_resonance_map FK references,
    which is the exact defect this test file exists to catch.
    """
    source = inspect.getsource(seed_transit_rules)
    assert 'DELETE FROM bg_transit_rules' in source, (
        "Expected the F-145 retirement sweep's scoped DELETE to be present"
    )
    assert 'DELETE FROM bg_transit_rules WHERE id = %s' in source, (
        "Found DELETE FROM bg_transit_rules that is not scoped to a single id — "
        "this would renumber the SERIAL id column and corrupt "
        "gochara_resonance_map.source_rule_id FK references"
    )


def test_owned_categories_derived_from_rules_never_hardcoded():
    """_owned_categories must compute ownership from the passed-in rules list, not
    from a hardcoded constant — this is what lets the ownership boundary track
    BG_TRANSIT_RULES as it grows."""
    fake_rules = [
        {"rule_type": "favourable", "graha": "venus", "primary_house": 1},
        {"rule_type": "unfavourable", "graha": "venus", "primary_house": 6},
    ]
    owned_types, owned_grahas = _owned_categories(fake_rules)
    assert owned_types == {"favourable", "unfavourable"}
    assert owned_grahas == {"venus"}


def test_compute_stale_rule_ids_retires_owned_absent_rows():
    """
    A DB row inside an owned category, but whose (graha, rule_type, primary_house)
    key is absent from the current source list, must be retired. Mirrors the real
    F-145 fixture: ids 49/50 (venus/unfavourable houses 11/12) are absent from the
    corrected source list and must be flagged; ids 46/47 (houses 6/7) are present and
    must not be.
    """
    fake_rules = [
        {"rule_type": "unfavourable", "graha": "venus", "primary_house": 6},
        {"rule_type": "unfavourable", "graha": "venus", "primary_house": 7},
    ]
    db_rows = [
        (46, "venus", "unfavourable", 6),
        (47, "venus", "unfavourable", 7),
        (49, "venus", "unfavourable", 11),
        (50, "venus", "unfavourable", 12),
    ]
    stale = compute_stale_rule_ids(fake_rules, db_rows)
    assert set(stale) == {49, 50}


def test_compute_stale_rule_ids_empty_when_source_matches_db():
    """No stale ids when every owned DB row's key is present in the source list —
    the sweep must not retire rows that are still current."""
    fake_rules = [{"rule_type": "favourable", "graha": "sun", "primary_house": 1}]
    db_rows = [(1, "sun", "favourable", 1)]
    assert compute_stale_rule_ids(fake_rules, db_rows) == []


def test_migration_owned_rows_never_classified_as_owned():
    """
    Migration-owned rows (migration 397's 7 double_transit rows, title-case
    'Jupiter'/'Saturn') must never be reachable via `_owned_categories` derived from
    the real BG_TRANSIT_RULES — they never appear in it, so the SQL WHERE clause in
    seed_transit_rules (rule_type = ANY(owned_types) AND graha = ANY(owned_grahas))
    structurally never selects them as sweep candidates. This is a deliberate
    case-sensitive exact-match design (BG_TRANSIT_RULES graha values are always
    lowercase), not a `lower()` coincidence.
    """
    owned_types, owned_grahas = _owned_categories(BG_TRANSIT_RULES)
    assert "double_transit" not in owned_types
    assert "vedha" not in owned_types
    assert "Jupiter" not in owned_grahas
    assert "Saturn" not in owned_grahas
    # sanity: the writer really does own these two rule_types today
    assert owned_types == {"favourable", "unfavourable"}


def test_reconciliation_sweep_deletes_owned_absent_row_scoped_by_id():
    """
    Behavioural mutation-check: with a mocked DB connection whose candidate-select
    returns one owned-but-absent row, seed_transit_rules must issue exactly one
    scoped `DELETE FROM bg_transit_rules WHERE id = %s` for that row's id. Revert the
    sweep in seed_transit_rules and this test fails (no delete call at all).
    """
    mock_cursor = MagicMock()
    # Candidate fetch: one owned row (venus/unfavourable/house=99) absent from the
    # real BG_TRANSIT_RULES — must be retired.
    mock_cursor.fetchall.return_value = [(9999, "venus", "unfavourable", 99)]
    # Freshness count matches, so the freshness WARNING path is not exercised here.
    mock_cursor.fetchone.return_value = (len(BG_TRANSIT_RULES),)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    seed_transit_rules(mock_conn, dry_run=False)

    delete_calls = [
        call
        for call in mock_cursor.execute.call_args_list
        if call.args and isinstance(call.args[0], str) and "DELETE FROM bg_transit_rules" in call.args[0]
    ]
    assert len(delete_calls) == 1, f"Expected exactly one scoped DELETE, got {delete_calls}"
    assert delete_calls[0].args[0].strip() == "DELETE FROM bg_transit_rules WHERE id = %s"
    assert delete_calls[0].args[1] == (9999,)


def test_reconciliation_sweep_no_delete_when_no_stale_rows():
    """Negative control: when the candidate select finds nothing absent from the
    source list, no DELETE FROM bg_transit_rules is issued at all."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []
    mock_cursor.fetchone.return_value = (len(BG_TRANSIT_RULES),)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    seed_transit_rules(mock_conn, dry_run=False)

    delete_calls = [
        call
        for call in mock_cursor.execute.call_args_list
        if call.args and isinstance(call.args[0], str) and "DELETE FROM bg_transit_rules" in call.args[0]
    ]
    assert delete_calls == []


# ── F-145: freshness assertion (§N.8 — a detector, not just a one-time cleanup) ──

def test_freshness_assertion_warns_on_mismatch(caplog):
    """
    If the owned-category row count doesn't match len(BG_TRANSIT_RULES) after the
    upsert+retire sweep, seed_transit_rules must log a WARNING. This is the
    detector half of F-145 — without it, silent re-accretion of stray rows (or a
    retirement blocked by an FK reference) would go unnoticed on every future run.
    """
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []  # nothing to retire
    # Freshness COUNT deliberately wrong — one short of len(BG_TRANSIT_RULES).
    mock_cursor.fetchone.return_value = (len(BG_TRANSIT_RULES) - 1,)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with caplog.at_level(logging.WARNING, logger="brahmagyan.l0_transit"):
        seed_transit_rules(mock_conn, dry_run=False)

    assert any("freshness check failed" in record.message for record in caplog.records), (
        "Expected a WARNING log when owned-category row count mismatches BG_TRANSIT_RULES"
    )


def test_freshness_assertion_silent_when_matching(caplog):
    """Regression guard: when the owned-category row count matches
    len(BG_TRANSIT_RULES), no freshness WARNING is logged."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []
    mock_cursor.fetchone.return_value = (len(BG_TRANSIT_RULES),)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with caplog.at_level(logging.WARNING, logger="brahmagyan.l0_transit"):
        seed_transit_rules(mock_conn, dry_run=False)

    assert not any("freshness check failed" in record.message for record in caplog.records)
