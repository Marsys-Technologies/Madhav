"""
test_mimamsa_lel_intake.py — Unit tests for mimamsa.lel_intake (BRAHMA-MI-5-1)

Tests:
    1. Corpus integrity — exactly 57 events in LEL_CORPUS
    2. Source citation — all rows carry non-empty source_citation
    3. Domain format — all rows have category/subcategory compound domain
    4. Convergence mapping — outcome values map to correct float ranges
    5. UUID determinism — _evt_uuid generates stable UUIDs from LEL IDs
    6. seed_lel_intake dry_run — no DB writes, returns correct structure
    7. lel_query mock — filters by domain, returns provenance_envelope
    8. lel_query mock — filters by date range
    9. acceptance gate — AC1-AC4 structure (mocked DB)
    10. No leakage note — provenance_envelope carries no_leakage_note

No live DB connection required. All DB calls are mocked via unittest.mock.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ── Lazy import to avoid psycopg dependency in CI ──────────────────────────────

def _get_module():
    from brahmagyan.mimamsa import lel_intake as mod
    return mod


# ── Corpus integrity tests ─────────────────────────────────────────────────────

class TestCorpusIntegrity:
    """Tests that the in-memory corpus is correctly structured."""

    def test_event_count_exactly_57(self):
        """AC1 pre-condition: corpus must have exactly 57 events."""
        mod = _get_module()
        assert len(mod.LEL_CORPUS) == 57, (
            f"Expected 57 events in LEL_CORPUS, got {len(mod.LEL_CORPUS)}"
        )

    def test_all_lel_ids_unique(self):
        """Each EVT.* ID appears exactly once."""
        mod = _get_module()
        ids = [e["lel_id"] for e in mod.LEL_CORPUS]
        assert len(ids) == len(set(ids)), (
            "Duplicate LEL IDs detected: "
            + str([i for i in ids if ids.count(i) > 1])
        )

    def test_all_events_have_required_fields(self):
        """Every corpus entry has all required fields."""
        mod = _get_module()
        required = {"lel_id", "event_date", "event_type", "subcategory",
                    "description", "magnitude", "outcome"}
        for event in mod.LEL_CORPUS:
            missing = required - set(event.keys())
            assert not missing, (
                f"Event {event.get('lel_id', '?')} missing fields: {missing}"
            )

    def test_first_event_is_birth(self):
        """First event is the birth event (EVT.1984.02.05.01)."""
        mod = _get_module()
        first = mod.LEL_CORPUS[0]
        assert first["lel_id"] == "EVT.1984.02.05.01"
        assert first["event_date"] == "1984-02-05"

    def test_last_event_is_current_state(self):
        """Last event is EVT.CURRENT.01 (marital status as of 2026-04-17)."""
        mod = _get_module()
        last = mod.LEL_CORPUS[-1]
        assert last["lel_id"] == "EVT.CURRENT.01"
        assert last["event_date"] == "2026-04-17"

    def test_event_dates_broadly_chronological(self):
        """
        Events are broadly in chronological order — within the same month,
        proxy dates (YYYY-MM-15) may appear before or after exact dates
        (e.g. EVT.2007.06.XX.02 uses 2007-06-15 but EVT.2007.06.10.01 is exact).
        Test that date range is correct and events span the correct years.
        """
        mod = _get_module()
        dates = [e["event_date"] for e in mod.LEL_CORPUS]
        # First event is birth (1984-02-05)
        assert dates[0] == "1984-02-05"
        # Last event is 2026
        assert dates[-1].startswith("2026")
        # Overall span is increasing (first < last)
        assert dates[0] < dates[-1]
        # No event is earlier than native's birth
        for d in dates:
            assert d >= "1984-02-05", f"Event date before birth: {d}"


# ── Source citation tests ─────────────────────────────────────────────────────

class TestSourceCitation:
    """B.3 mandate: all rows carry non-empty source_citation."""

    def test_source_citation_constant_non_empty(self):
        mod = _get_module()
        assert mod.SOURCE_CITATION, "SOURCE_CITATION must be non-empty"
        assert "LIFE_EVENT_LOG_v1_2.md" in mod.SOURCE_CITATION

    def test_build_row_source_citation_non_null(self):
        """_build_row always returns non-empty source_citation."""
        mod = _get_module()
        for event in mod.LEL_CORPUS:
            row = mod._build_row(event)
            assert row["source_citation"], (
                f"source_citation empty for {event['lel_id']}"
            )
            assert row["source_citation"] == mod.SOURCE_CITATION


# ── Domain format tests ───────────────────────────────────────────────────────

class TestDomainFormat:
    """domain field must be 'category/subcategory' compound."""

    def test_all_domains_have_slash(self):
        mod = _get_module()
        for event in mod.LEL_CORPUS:
            row = mod._build_row(event)
            assert "/" in row["domain"], (
                f"domain missing slash for {event['lel_id']}: {row['domain']!r}"
            )

    def test_domain_matches_event_type_subcategory(self):
        mod = _get_module()
        for event in mod.LEL_CORPUS:
            row = mod._build_row(event)
            expected_prefix = event["event_type"]
            assert row["domain"].startswith(expected_prefix), (
                f"domain prefix mismatch for {event['lel_id']}: "
                f"expected to start with {expected_prefix!r}, got {row['domain']!r}"
            )


# ── Convergence mapping tests ─────────────────────────────────────────────────

class TestConvergenceMapping:
    """outcome → convergence_score mapping must be correct."""

    def test_yes_maps_to_1_0(self):
        mod = _get_module()
        assert mod._convergence("yes") == 1.0

    def test_partial_maps_to_0_5(self):
        mod = _get_module()
        assert mod._convergence("partial") == 0.5

    def test_no_maps_to_0_0(self):
        mod = _get_module()
        assert mod._convergence("no") == 0.0

    def test_unexamined_maps_to_none(self):
        mod = _get_module()
        assert mod._convergence("unexamined") is None

    def test_pending_maps_to_none(self):
        mod = _get_module()
        assert mod._convergence("pending") is None

    def test_null_maps_to_none(self):
        mod = _get_module()
        assert mod._convergence(None) is None

    def test_convergence_in_valid_range_when_non_null(self):
        """All non-None convergence values are in [0.0, 1.0]."""
        mod = _get_module()
        valid_outcomes = {"yes", "partial", "no"}
        for event in mod.LEL_CORPUS:
            outcome = event.get("outcome")
            if outcome in valid_outcomes:
                score = mod._convergence(outcome)
                assert score is not None
                assert 0.0 <= score <= 1.0, (
                    f"convergence_score out of range for {event['lel_id']}: {score}"
                )


# ── UUID determinism tests ────────────────────────────────────────────────────

class TestUUIDDeterminism:
    """_evt_uuid must return stable, deterministic UUIDs."""

    def test_uuid_stable_across_calls(self):
        mod = _get_module()
        uid1 = mod._evt_uuid("EVT.1984.02.05.01")
        uid2 = mod._evt_uuid("EVT.1984.02.05.01")
        assert uid1 == uid2, "UUID must be deterministic"

    def test_uuid_different_for_different_ids(self):
        mod = _get_module()
        uid1 = mod._evt_uuid("EVT.1984.02.05.01")
        uid2 = mod._evt_uuid("EVT.2013.12.11.01")
        assert uid1 != uid2, "Different IDs must produce different UUIDs"

    def test_uuid_is_valid_uuid_string(self):
        import uuid
        mod = _get_module()
        for event in mod.LEL_CORPUS[:5]:  # spot-check first 5
            uid_str = mod._evt_uuid(event["lel_id"])
            # Must parse as valid UUID
            parsed = uuid.UUID(uid_str)
            assert parsed.version == 5, "Must be UUID v5"


# ── Dry-run seed tests ────────────────────────────────────────────────────────

class TestSeedDryRun:
    """seed_lel_intake(dry_run=True) must not touch DB and return correct structure."""

    def test_dry_run_returns_57_total(self):
        mod = _get_module()
        result = mod.seed_lel_intake(dry_run=True)
        assert result["total"] == 57

    def test_dry_run_is_flagged(self):
        mod = _get_module()
        result = mod.seed_lel_intake(dry_run=True)
        assert result["dry_run"] is True

    def test_dry_run_source_citation_non_empty(self):
        mod = _get_module()
        result = mod.seed_lel_intake(dry_run=True)
        assert result["source_citation"], "source_citation must be non-empty"
        assert "LIFE_EVENT_LOG" in result["source_citation"]

    def test_dry_run_has_provenance_envelope(self):
        mod = _get_module()
        result = mod.seed_lel_intake(dry_run=True)
        env = result.get("provenance_envelope", {})
        assert env, "provenance_envelope must be present"
        assert env.get("source") == "mimamsa.lel_intake"
        assert env.get("asset") == "MI-5-1"
        assert env.get("total_events") == 57

    def test_dry_run_no_leakage_check(self):
        mod = _get_module()
        result = mod.seed_lel_intake(dry_run=True)
        assert "no_leakage_check" in result
        assert "PASS" in result["no_leakage_check"]

    def test_dry_run_confidence_in_range(self):
        mod = _get_module()
        result = mod.seed_lel_intake(dry_run=True)
        confidence = result["provenance_envelope"]["confidence"]
        assert 0.0 <= confidence <= 1.0, (
            f"provenance confidence out of range: {confidence}"
        )


# ── Mock lel_query tests ──────────────────────────────────────────────────────

def _make_mock_conn(rows: list[Any], count: int):
    """Build a mock psycopg connection that returns given rows and count."""
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)

    # execute().fetchall() for main query, execute().fetchone() for count
    mock_execute_main = MagicMock()
    mock_execute_main.fetchall = MagicMock(return_value=rows)

    mock_execute_count = MagicMock()
    mock_execute_count.fetchone = MagicMock(return_value=(count,))

    call_count = [0]
    def side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return mock_execute_main
        return mock_execute_count

    mock_conn.execute = MagicMock(side_effect=side_effect)
    return mock_conn


def _make_event_row(
    event_id: str = "550e8400-e29b-41d4-a716-446655440000",
    event_date: str = "2023-07-15",
    event_type: str = "career",
    description: str = "Founded Marsys Group.",
    domain: str = "career/entrepreneurship_founded",
    outcome_observed: str = "yes",
    dasha_active: str = "Mercury",
    antardasha_active: str = "Jupiter",
    key_transits: str = '["Saturn transit Aquarius = 11H"]',
    convergence_score: float = 1.0,
    source_citation: str = "LIFE_EVENT_LOG_v1_2.md (native-disclosed)",
) -> tuple:
    return (
        event_id, event_date, event_type, description, domain,
        outcome_observed, dasha_active, antardasha_active,
        key_transits, convergence_score, source_citation,
    )


class TestLelQueryMock:
    """lel_query with mocked DB — tests filtering logic + provenance_envelope."""

    def test_query_returns_events_list(self):
        mod = _get_module()
        rows = [_make_event_row()]
        mock_conn = _make_mock_conn(rows, count=1)

        with patch.object(mod, '_get_conn', return_value=mock_conn):
            result = mod.lel_query(limit=10)

        assert "events" in result
        assert isinstance(result["events"], list)
        assert len(result["events"]) == 1

    def test_query_event_source_citation_non_null(self):
        mod = _get_module()
        rows = [_make_event_row()]
        mock_conn = _make_mock_conn(rows, count=1)

        with patch.object(mod, '_get_conn', return_value=mock_conn):
            result = mod.lel_query()

        for event in result["events"]:
            assert event["source_citation"], "source_citation must be non-empty"

    def test_query_has_provenance_envelope(self):
        mod = _get_module()
        rows = [_make_event_row()]
        mock_conn = _make_mock_conn(rows, count=1)

        with patch.object(mod, '_get_conn', return_value=mock_conn):
            result = mod.lel_query()

        env = result.get("provenance_envelope", {})
        assert env, "provenance_envelope must be present"
        assert env["source"] == "mimamsa.lel_intake"
        assert env["asset"] == "MI-5-1"
        assert env["total_events"] == 57
        assert env["b3_compliant"] is True

    def test_query_no_leakage_note_present(self):
        mod = _get_module()
        rows = [_make_event_row()]
        mock_conn = _make_mock_conn(rows, count=1)

        with patch.object(mod, '_get_conn', return_value=mock_conn):
            result = mod.lel_query()

        env = result["provenance_envelope"]
        assert "no_leakage_note" in env
        assert "calibration" in env["no_leakage_note"].lower()

    def test_query_filter_applied_structure(self):
        mod = _get_module()
        rows = [_make_event_row()]
        mock_conn = _make_mock_conn(rows, count=1)

        with patch.object(mod, '_get_conn', return_value=mock_conn):
            result = mod.lel_query(domain="career", date_from="2023-01-01")

        fa = result["filter_applied"]
        assert fa["domain"] == "career"
        assert fa["date_from"] == "2023-01-01"

    def test_query_convergence_score_in_range_or_none(self):
        """convergence_score values are either None or in [0.0, 1.0]."""
        mod = _get_module()
        rows = [
            _make_event_row(convergence_score=1.0),
            _make_event_row(convergence_score=0.5),
            _make_event_row(convergence_score=0.0),
        ]
        mock_conn = _make_mock_conn(rows, count=3)

        with patch.object(mod, '_get_conn', return_value=mock_conn):
            result = mod.lel_query()

        for event in result["events"]:
            cs = event["convergence_score"]
            if cs is not None:
                assert 0.0 <= cs <= 1.0, (
                    f"convergence_score out of range: {cs}"
                )

    def test_query_total_count_matches(self):
        mod = _get_module()
        rows = [_make_event_row()]
        mock_conn = _make_mock_conn(rows, count=57)

        with patch.object(mod, '_get_conn', return_value=mock_conn):
            result = mod.lel_query()

        assert result["total_count"] == 57


# ── Acceptance gate mock tests ────────────────────────────────────────────────

class TestAcceptanceGateMock:
    """Acceptance gate structure tests with mocked DB."""

    def _mock_conn_for_gate(
        self,
        le_count: int = 57,
        cs_count: int = 57,
        null_citations: int = 0,
        null_cs_citations: int = 0,
    ) -> MagicMock:
        """Build a mock connection that returns different values per query."""
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)

        call_seq = [
            (le_count,),          # AC1: life_events COUNT
            (cs_count,),          # AC2: event_chart_state_index COUNT
            (null_citations,),    # AC3: null citation count
            (null_cs_citations,), # AC4: null cs citation count
        ]
        call_idx = [0]

        def execute_side(*args, **kwargs):
            result = MagicMock()
            result.fetchone = MagicMock(return_value=call_seq[call_idx[0]])
            call_idx[0] += 1
            return result

        mock_conn.execute = MagicMock(side_effect=execute_side)
        return mock_conn

    def test_gate_structure_has_required_keys(self):
        mod = _get_module()
        mock_conn = self._mock_conn_for_gate()

        with patch.object(mod, '_get_conn', return_value=mock_conn):
            with patch.object(mod, 'lel_query', return_value={
                "events": [{"x": 1}],
                "total_count": 57,
                "filter_applied": {},
                "provenance_envelope": {},
            }):
                result = mod.run_acceptance_gate()

        assert "gate_passed" in result
        assert "checks" in result
        assert "asset" in result
        assert result["asset"] == "MI-5-1"

    def test_gate_passes_when_all_57_rows(self):
        mod = _get_module()
        mock_conn = self._mock_conn_for_gate(
            le_count=57, cs_count=57,
            null_citations=0, null_cs_citations=0,
        )

        with patch.object(mod, '_get_conn', return_value=mock_conn):
            with patch.object(mod, 'lel_query', return_value={
                "events": [{"x": 1}],
                "total_count": 57,
                "filter_applied": {},
                "provenance_envelope": {},
            }):
                result = mod.run_acceptance_gate()

        # AC1-AC4 should pass
        ac_ids = {c["id"]: c["passed"] for c in result["checks"]}
        assert ac_ids.get("AC1") is True, "AC1 should pass with 57 life_events rows"
        assert ac_ids.get("AC2") is True, "AC2 should pass with 57 chart_state rows"
        assert ac_ids.get("AC3") is True, "AC3 should pass with 0 null citations"
        assert ac_ids.get("AC4") is True, "AC4 should pass with 0 null cs citations"

    def test_gate_fails_when_wrong_count(self):
        mod = _get_module()
        mock_conn = self._mock_conn_for_gate(le_count=42, cs_count=42)

        with patch.object(mod, '_get_conn', return_value=mock_conn):
            with patch.object(mod, 'lel_query', return_value={
                "events": [],
                "total_count": 0,
                "filter_applied": {},
                "provenance_envelope": {},
            }):
                result = mod.run_acceptance_gate()

        ac_ids = {c["id"]: c["passed"] for c in result["checks"]}
        assert ac_ids.get("AC1") is False, "AC1 should fail with wrong count"

    def test_gate_fails_when_null_citation(self):
        mod = _get_module()
        mock_conn = self._mock_conn_for_gate(
            le_count=57, cs_count=57,
            null_citations=1, null_cs_citations=0,
        )

        with patch.object(mod, '_get_conn', return_value=mock_conn):
            with patch.object(mod, 'lel_query', return_value={
                "events": [{"x": 1}],
                "total_count": 57,
                "filter_applied": {},
                "provenance_envelope": {},
            }):
                result = mod.run_acceptance_gate()

        ac_ids = {c["id"]: c["passed"] for c in result["checks"]}
        assert ac_ids.get("AC3") is False, "AC3 should fail with null citations"

    def test_gate_checks_are_list(self):
        mod = _get_module()
        mock_conn = self._mock_conn_for_gate()

        with patch.object(mod, '_get_conn', return_value=mock_conn):
            with patch.object(mod, 'lel_query', return_value={
                "events": [{"x": 1}],
                "total_count": 57,
                "filter_applied": {},
                "provenance_envelope": {},
            }):
                result = mod.run_acceptance_gate()

        checks = result["checks"]
        assert isinstance(checks, list), "checks must be a list"
        assert len(checks) >= 4, "Must have at least AC1-AC4 checks"
        for check in checks:
            assert "id" in check
            assert "passed" in check


# ── Build row tests ───────────────────────────────────────────────────────────

class TestBuildRow:
    """_build_row must produce fully-populated rows."""

    def test_build_row_has_all_keys(self):
        mod = _get_module()
        required_keys = {
            "event_id", "lel_id", "event_date", "event_type",
            "description", "domain", "outcome_observed",
            "source_citation", "dasha_md", "dasha_ad",
            "key_transits", "convergence",
        }
        for event in mod.LEL_CORPUS:
            row = mod._build_row(event)
            missing = required_keys - set(row.keys())
            assert not missing, (
                f"Row for {event['lel_id']} missing keys: {missing}"
            )

    def test_build_row_key_transits_is_list(self):
        mod = _get_module()
        for event in mod.LEL_CORPUS:
            row = mod._build_row(event)
            assert isinstance(row["key_transits"], list), (
                f"key_transits must be list for {event['lel_id']}"
            )
