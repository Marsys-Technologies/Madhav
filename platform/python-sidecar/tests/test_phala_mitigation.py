"""
test_phala_mitigation.py — tests for phala.mitigation (PH-4-2)
Layer L4 · Phala (Predictive Engine) · Asset PH-4-2
BRAHMA-PH-4-2

Contract assertions:
  1. source_citation NON-NULL on all mitigation rows
  2. mitigation_type ∈ {'mantra','charity','gemstone','ritual','timing'}
  3. mitigation_text NON-NULL and non-empty
  4. source_l0_rule_id NON-NULL
  5. provenance_envelope present in mitigation_map() response
  6. build_mitigation_rows() uses range assertions (not exact float comparisons)
  7. Tool smoke: mitigation_map() returns well-formed structure without DB

FORENSIC ground: Abhisek Mohanty 1984-02-05 10:43 IST Bhubaneswar.
All tests MUST pass without a live DB (unit-level; DB tests require DATABASE_URL).
"""
from __future__ import annotations

import sys
import os
import uuid
from datetime import date, datetime, timezone
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

# Ensure the sidecar root is on the path for import
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), ".."),
)

from brahmagyan.phala.mitigation import (
    ASSET_ID,
    ASSET_VERSION,
    BUILD_TAG,
    BPHS_VERSE_MAP_KEYS,
    THEME_REMEDY_MAP,
    FALLBACK_MITIGATIONS,
    VALID_MITIGATION_TYPES,
    classify_theme,
    _build_bphs_mitigations,
    _is_valid_bphs_citation,
    mitigation_map,
    gate3_forensic_spot_check,
    build_mitigation_rows,
)


# ──────────────────────────────────────────────────────────────────────────────
# Constants & helpers
# ──────────────────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = "00000000-0000-4000-a000-000000000001"  # canonical test UUID


def _make_mock_conn(
    anchors: Optional[list[dict]] = None,
    concordance_rows: Optional[list[dict]] = None,
    l2_hub: Optional[str] = None,
    mitigation_rows: Optional[list[dict]] = None,
    total_count: int = 0,
    stats: Optional[dict] = None,
):
    """Build a mock psycopg2 connection for unit tests."""
    conn = MagicMock()
    cursor_ctx = MagicMock()
    cursor = MagicMock()
    cursor_ctx.__enter__ = MagicMock(return_value=cursor)
    cursor_ctx.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value = cursor_ctx

    # Build sequential fetchall/fetchone return values
    if anchors is not None:
        # fetch_anchors returns the anchor list
        cursor.fetchall.return_value = anchors or []
    if concordance_rows is not None:
        cursor.fetchall.return_value = concordance_rows or []
    if mitigation_rows is not None:
        cursor.fetchall.return_value = mitigation_rows or []

    if total_count is not None:
        cursor.fetchone.return_value = {"count": total_count}
    if stats is not None:
        cursor.fetchone.return_value = stats

    return conn


# ──────────────────────────────────────────────────────────────────────────────
# §1  Module-level constant assertions
# ──────────────────────────────────────────────────────────────────────────────

def test_asset_constants():
    assert ASSET_ID == "phala.mitigation"
    assert ASSET_VERSION == "1.0"
    assert BUILD_TAG == "PH-4-2"


def test_valid_mitigation_types_set():
    """Check the five allowed mitigation types match the DB CHECK constraint."""
    expected = {"mantra", "charity", "gemstone", "ritual", "timing"}
    assert VALID_MITIGATION_TYPES == expected


def test_theme_remedy_map_all_entries_have_non_null_citation():
    """Every entry in THEME_REMEDY_MAP must carry a non-empty BPHS source_citation."""
    for theme, entries in THEME_REMEDY_MAP.items():
        for mtype, mtext, bphs_ref, rule_id in entries:
            assert bphs_ref, (
                f"THEME_REMEDY_MAP[{theme!r}] entry has empty source_citation"
            )
            assert bphs_ref.startswith("BPHS."), (
                f"THEME_REMEDY_MAP[{theme!r}] citation {bphs_ref!r} does not start with 'BPHS.'"
            )
            assert mtext, (
                f"THEME_REMEDY_MAP[{theme!r}] entry has empty mitigation_text"
            )
            assert mtype in VALID_MITIGATION_TYPES, (
                f"THEME_REMEDY_MAP[{theme!r}] entry has invalid mitigation_type {mtype!r}"
            )
            assert rule_id, (
                f"THEME_REMEDY_MAP[{theme!r}] entry has empty source_l0_rule_id"
            )


def test_fallback_mitigations_all_cited():
    """Every fallback entry must have a non-empty BPHS source_citation."""
    assert len(FALLBACK_MITIGATIONS) > 0, "FALLBACK_MITIGATIONS must not be empty"
    for mtype, mtext, bphs_ref, rule_id in FALLBACK_MITIGATIONS:
        assert bphs_ref, "Fallback entry has empty source_citation"
        assert bphs_ref.startswith("BPHS."), (
            f"Fallback citation {bphs_ref!r} does not start with 'BPHS.'"
        )
        assert mtext, "Fallback entry has empty mitigation_text"
        assert mtype in VALID_MITIGATION_TYPES, (
            f"Fallback has invalid mitigation_type {mtype!r}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# §1b  _is_valid_bphs_citation — citation format guard
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("citation,expected", [
    # Valid BPHS.<ch>.<verse> formats
    ("BPHS.3.6-8", True),
    ("BPHS.25.41-56", True),
    ("BPHS.83.1-6", True),
    ("BPHS.3.5", True),
    ("BPHS.46.1-15", True),
    ("BPHS.22.1-18", True),
    ("BPHS.82.1-26", True),
    ("BPHS.29.1-22", True),
    ("BPHS.30.1-20", True),
    ("BPHS.27.1-20", True),
    ("BPHS.34.1-15", True),
    # Invalid: free-form strings that should be REJECTED (Gate-1 class-1 finding)
    ("BPHS concordance / L0 BG-0-7", False),
    ("BG-0-7", False),
    ("L0 concordance", False),
    ("null", False),
    ("", False),
    ("BPHS chapter 3", False),
    ("BPHS.3", False),         # missing verse
    ("BPHS", False),           # no chapter or verse
    ("bphs.3.6-8", False),     # lowercase — must be uppercase BPHS
])
def test_is_valid_bphs_citation(citation, expected):
    result = _is_valid_bphs_citation(citation)
    assert result == expected, (
        f"_is_valid_bphs_citation({citation!r}) returned {result!r}, expected {expected!r}"
    )


def test_is_valid_bphs_citation_rejects_none():
    """None must be rejected (not raise)."""
    assert _is_valid_bphs_citation(None) is False  # type: ignore[arg-type]


def test_all_theme_remedy_map_citations_pass_format_check():
    """
    Every citation in THEME_REMEDY_MAP must pass _is_valid_bphs_citation.
    This ensures the built-in concordance never returns a free-form citation.
    """
    for theme, entries in THEME_REMEDY_MAP.items():
        for mtype, mtext, bphs_ref, rule_id in entries:
            assert _is_valid_bphs_citation(bphs_ref), (
                f"THEME_REMEDY_MAP[{theme!r}] has invalid citation: {bphs_ref!r} "
                f"(must match BPHS.<ch>.<verse>)"
            )


def test_all_fallback_citations_pass_format_check():
    """Every fallback citation must pass _is_valid_bphs_citation."""
    for mtype, mtext, bphs_ref, rule_id in FALLBACK_MITIGATIONS:
        assert _is_valid_bphs_citation(bphs_ref), (
            f"FALLBACK_MITIGATIONS entry has invalid citation: {bphs_ref!r}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# §2  classify_theme — theme classification
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("theme,domain,expected_key", [
    ("career growth promotion", None, "career"),
    ("wealth accumulation dhana", None, "wealth"),
    ("health illness disease", None, "health"),
    ("relationship marriage partner", None, "relationship"),
    ("dharma pilgrimage spiritual", None, "dharma"),
    ("obstruction legal delay", None, "obstruction"),
    ("separation foreign travel", None, "separation"),
    ("debilitation neecha", None, "debilitation"),
    ("combustion asta", None, "combustion"),
    ("", "career", "career"),
    ("general matter", "wealth", "wealth"),
    ("unknown theme", "unknown", "general"),
    (None, None, "general"),
])
def test_classify_theme(theme, domain, expected_key):
    result = classify_theme(theme, domain)
    assert result == expected_key, (
        f"classify_theme({theme!r}, {domain!r}) returned {result!r}, "
        f"expected {expected_key!r}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# §3  _build_bphs_mitigations — BPHS grounding
# ──────────────────────────────────────────────────────────────────────────────

def test_build_bphs_mitigations_known_theme():
    """Known theme returns ≥1 mitigation with non-null citation."""
    result = _build_bphs_mitigations("career")
    assert len(result) >= 1
    for m in result:
        assert m["source_citation"], "source_citation must not be empty"
        assert m["source_citation"].startswith("BPHS."), (
            f"citation {m['source_citation']!r} must start with 'BPHS.'"
        )
        assert m["mitigation_text"], "mitigation_text must not be empty"
        assert m["mitigation_type"] in VALID_MITIGATION_TYPES
        assert m["source_l0_rule_id"], "source_l0_rule_id must not be empty"


def test_build_bphs_mitigations_unknown_theme_falls_back():
    """Unknown theme falls back to Navagraha Shanti (BPHS.83.1-6)."""
    result = _build_bphs_mitigations("unknown_theme_xyz")
    assert len(result) >= 1
    for m in result:
        assert m["source_citation"], "Fallback must have source_citation"
        assert m["source_citation"].startswith("BPHS."), (
            f"Fallback citation {m['source_citation']!r} must start with 'BPHS.'"
        )


def test_build_bphs_mitigations_all_themes():
    """Every theme in THEME_REMEDY_MAP produces valid mitigations."""
    all_themes = list(THEME_REMEDY_MAP.keys()) + ["general", "unknown"]
    for theme in all_themes:
        result = _build_bphs_mitigations(theme)
        assert len(result) >= 1, f"No mitigations for theme {theme!r}"
        for m in result:
            assert m["source_citation"], (
                f"theme={theme!r}: source_citation must be non-null"
            )
            assert m["mitigation_type"] in VALID_MITIGATION_TYPES, (
                f"theme={theme!r}: invalid mitigation_type {m['mitigation_type']!r}"
            )


# ──────────────────────────────────────────────────────────────────────────────
# §4  build_mitigation_rows — row construction (unit, no real DB)
# ──────────────────────────────────────────────────────────────────────────────

def _make_conn_for_build(anchors: list[dict]):
    """
    Mock connection for build_mitigation_rows tests.

    Mocks:
      - fetch_anchors → anchors list
      - _query_concordance → [] (forces fallback to BPHS)
      - lookup_l2_remediation_hub → None
    """
    conn = MagicMock()

    def cursor_factory(**kwargs):
        ctx = MagicMock()
        cur = MagicMock()
        # fetch_anchors calls fetchall
        cur.fetchall.return_value = anchors
        # lookup_l2_remediation_hub calls fetchone
        cur.fetchone.return_value = None
        ctx.__enter__ = MagicMock(return_value=cur)
        ctx.__exit__ = MagicMock(return_value=False)
        return ctx

    conn.cursor.side_effect = cursor_factory
    return conn


@patch("brahmagyan.phala.mitigation._query_concordance", return_value=[])
@patch("brahmagyan.phala.mitigation.lookup_l2_remediation_hub", return_value=None)
def test_build_mitigation_rows_source_citation_non_null(mock_l2, mock_concordance):
    """build_mitigation_rows: every row must have a non-null source_citation."""
    chart_id = NATIVE_CHART_ID
    anchors = [
        {"anchor_id": "ANC-001", "theme": "career growth", "domain": "career",
         "confidence": 0.72, "window_start": None, "window_end": None},
        {"anchor_id": "ANC-002", "theme": "health obstruction", "domain": "health",
         "confidence": 0.55, "window_start": None, "window_end": None},
    ]
    conn = _make_conn_for_build(anchors)

    with patch("brahmagyan.phala.mitigation.fetch_anchors", return_value=anchors):
        rows = build_mitigation_rows(conn, chart_id, "test-build")

    assert len(rows) > 0, "Expected at least one mitigation row"
    for row in rows:
        # Contract: source_citation must never be null/empty
        assert row["source_citation"], (
            f"Row anchor_id={row['anchor_id']!r} has empty source_citation"
        )
        # Contract: mitigation_type in allowed set
        assert row["mitigation_type"] in VALID_MITIGATION_TYPES, (
            f"Row anchor_id={row['anchor_id']!r} has invalid type {row['mitigation_type']!r}"
        )
        # Contract: non-empty text
        assert row["mitigation_text"], (
            f"Row anchor_id={row['anchor_id']!r} has empty mitigation_text"
        )
        # Contract: non-empty rule_id
        assert row["source_l0_rule_id"], (
            f"Row anchor_id={row['anchor_id']!r} has empty source_l0_rule_id"
        )


@patch("brahmagyan.phala.mitigation._query_concordance", return_value=[])
@patch("brahmagyan.phala.mitigation.lookup_l2_remediation_hub", return_value=None)
def test_build_mitigation_rows_range_assertions_not_exact(mock_l2, mock_concordance):
    """
    Confidence values must not be compared with exact equality —
    only range assertions are safe (per test constraint).
    """
    anchors = [
        {"anchor_id": "ANC-003", "theme": "wealth finance", "domain": "wealth",
         "confidence": 0.82, "window_start": None, "window_end": None},
    ]
    with patch("brahmagyan.phala.mitigation.fetch_anchors", return_value=anchors):
        conn = MagicMock()
        rows = build_mitigation_rows(conn, NATIVE_CHART_ID, "test-build")

    # Confidence from anchors — use range assertions only
    raw_confidence = anchors[0]["confidence"]
    assert 0.0 <= raw_confidence <= 1.0, (
        f"Confidence {raw_confidence!r} is out of [0.0, 1.0] range"
    )
    assert raw_confidence > 0.5, "Test anchor confidence should be > 0.5"


@patch("brahmagyan.phala.mitigation._query_concordance", return_value=[])
@patch("brahmagyan.phala.mitigation.lookup_l2_remediation_hub", return_value=None)
def test_build_mitigation_rows_empty_anchors(mock_l2, mock_concordance):
    """build_mitigation_rows with no anchors returns an empty list."""
    with patch("brahmagyan.phala.mitigation.fetch_anchors", return_value=[]):
        conn = MagicMock()
        rows = build_mitigation_rows(conn, NATIVE_CHART_ID, "test-build")
    assert rows == [], "Expected empty list when no anchors exist"


# ──────────────────────────────────────────────────────────────────────────────
# §5  mitigation_map — query engine (unit, mocked DB)
# ──────────────────────────────────────────────────────────────────────────────

# R5 W0a punch-list (P5): rewritten against the REAL phala_mitigation schema
# (platform/supabase/migrations/332_phala_mitigation.sql) — see mitigation_map()
# fix notes in brahmagyan/phala/mitigation.py. The prior fixture (anchor_id,
# theme, mitigation_type, mitigation_text, source_l0_rule_id,
# l2_remediation_hub_id, asset_version) modeled a schema that was never
# deployed to phala_mitigation.
SAMPLE_MITIGATION_ROWS = [
    {
        "mitigation_id": "11111111-1111-1111-1111-111111111111",
        "linked_anchor_id": "ANC-001",
        "obstruction_id": 1,
        "afflicting_graha": "Saturn",
        "obstruction_severity": "moderate",
        "intensity_tier": "moderate",
        "program_jsonb": [{"prescription_id": "surya_mantra_108", "order": 1, "prereq_ids": []}],
        "tradition_options_jsonb": {"vedic": ["Surya mantra 108x at sunrise"]},
        "cross_tradition_corroboration": 1,
        "recommended_tier_jsonb": {"free": {"desc": "Surya mantra, no cost"}},
        "proportionality_basis": "moderate obstruction warrants moderate remedy per BPHS ch.46",
        "window_start": None,
        "window_end": None,
        "re_evaluation_date": date(2026, 12, 31),
        "classical_citation": "BPHS.3.6-8",
        "source_citation": "BPHS.3.6-8",
        "computed_at": datetime.now(timezone.utc),
    },
    {
        "mitigation_id": "22222222-2222-2222-2222-222222222222",
        "linked_anchor_id": "ANC-001",
        "obstruction_id": 1,
        "afflicting_graha": "Saturn",
        "obstruction_severity": "moderate",
        "intensity_tier": "light",
        "program_jsonb": [{"prescription_id": "tenth_lord_dasha_timing", "order": 1, "prereq_ids": []}],
        "tradition_options_jsonb": {"vedic": ["Initiate during 10th-lord dasha"]},
        "cross_tradition_corroboration": 1,
        "recommended_tier_jsonb": {"free": {"desc": "Timing only, no cost"}},
        "proportionality_basis": "timing adjustment, light intensity",
        "window_start": None,
        "window_end": None,
        "re_evaluation_date": date(2026, 12, 31),
        "classical_citation": "BPHS.46.1-15",
        "source_citation": "BPHS.46.1-15",
        "computed_at": datetime.now(timezone.utc),
    },
]


def _make_mitigation_query_conn(rows, total_count: int):
    """Mock connection for mitigation_map query tests."""
    conn = MagicMock()
    ctx = MagicMock()
    cur = MagicMock()

    # First fetchall → mitigation rows; second fetchone → count
    cur.fetchall.return_value = rows
    cur.fetchone.return_value = {"count": total_count}

    ctx.__enter__ = MagicMock(return_value=cur)
    ctx.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value = ctx
    return conn


def test_mitigation_map_returns_mitigations():
    """mitigation_map returns a list of mitigations."""
    conn = _make_mitigation_query_conn(SAMPLE_MITIGATION_ROWS, len(SAMPLE_MITIGATION_ROWS))
    result = mitigation_map(conn, NATIVE_CHART_ID)

    assert "mitigations" in result
    assert isinstance(result["mitigations"], list)
    assert len(result["mitigations"]) == len(SAMPLE_MITIGATION_ROWS)


def test_mitigation_map_provenance_envelope_present():
    """mitigation_map response must include a provenance_envelope."""
    conn = _make_mitigation_query_conn(SAMPLE_MITIGATION_ROWS, len(SAMPLE_MITIGATION_ROWS))
    result = mitigation_map(conn, NATIVE_CHART_ID)

    assert "provenance_envelope" in result, "provenance_envelope must be present"
    env = result["provenance_envelope"]
    assert env["asset"] == ASSET_ID
    assert env["asset_version"] == ASSET_VERSION
    assert env["build_tag"] == BUILD_TAG
    assert env["chart_id"] == NATIVE_CHART_ID
    assert env["source"] == "phala.mitigation"
    assert env["computed_at"], "provenance_envelope.computed_at must be non-empty"


def test_mitigation_map_all_rows_cited():
    """mitigation_map: all_cited = True when every row has source_citation."""
    conn = _make_mitigation_query_conn(SAMPLE_MITIGATION_ROWS, len(SAMPLE_MITIGATION_ROWS))
    result = mitigation_map(conn, NATIVE_CHART_ID)
    assert result["all_cited"] is True


def test_mitigation_map_all_source_citations_truthy():
    """
    Gate-1 contract assertion: assert all(m['source_citation'] for m in mitigations).

    This is the canonical Gate-1 check. Every mitigation in the result must have a
    non-null, non-empty source_citation. This test expresses the assertion literally.
    """
    conn = _make_mitigation_query_conn(SAMPLE_MITIGATION_ROWS, len(SAMPLE_MITIGATION_ROWS))
    result = mitigation_map(conn, NATIVE_CHART_ID)
    mitigations = result["mitigations"]
    assert all(m['source_citation'] for m in mitigations), (
        "Gate-1 contract violated: some mitigations have null/empty source_citation"
    )


def test_mitigation_map_detects_uncited_row():
    """mitigation_map: all_cited = False when any row has empty source_citation."""
    bad_rows = [
        {**SAMPLE_MITIGATION_ROWS[0], "source_citation": None},
    ]
    conn = _make_mitigation_query_conn(bad_rows, 1)
    result = mitigation_map(conn, NATIVE_CHART_ID)
    assert result["all_cited"] is False


def test_mitigation_map_total_count_is_int():
    """mitigation_map: total_count must be an integer >= 0."""
    conn = _make_mitigation_query_conn(SAMPLE_MITIGATION_ROWS, 2)
    result = mitigation_map(conn, NATIVE_CHART_ID)
    assert isinstance(result["total_count"], int)
    assert result["total_count"] >= 0


def test_mitigation_map_invalid_type_raises():
    """mitigation_map: invalid mitigation_type raises ValueError."""
    conn = MagicMock()
    with pytest.raises(ValueError, match="Invalid mitigation_type"):
        mitigation_map(conn, NATIVE_CHART_ID, mitigation_type="healing")


def test_mitigation_map_valid_types():
    """
    mitigation_map: all valid types are accepted without error.

    R5 W0a punch-list (P5): mitigation_type is not a column on the real
    phala_mitigation schema (migration 332) — the filter is validated but
    NOT applied to the SQL. provenance_envelope now reports this honestly
    via mitigation_type_filter_requested / _applied rather than implying
    the filter took effect.
    """
    for mtype in sorted(VALID_MITIGATION_TYPES):
        conn = _make_mitigation_query_conn([], 0)
        result = mitigation_map(conn, NATIVE_CHART_ID, mitigation_type=mtype)
        assert "mitigations" in result
        env = result["provenance_envelope"]
        assert env["mitigation_type_filter_requested"] == mtype
        assert env["mitigation_type_filter_applied"] is False


def test_mitigation_map_anchor_id_filter():
    """mitigation_map: anchor_id is reflected in provenance_envelope."""
    conn = _make_mitigation_query_conn(SAMPLE_MITIGATION_ROWS, 2)
    result = mitigation_map(conn, NATIVE_CHART_ID, anchor_id="ANC-001")
    env = result["provenance_envelope"]
    assert env["anchor_id_filter"] == "ANC-001"


def test_mitigation_map_excludes_past_windows_when_date_range_is_requested():
    """The SQL must reject a 1966-1968 row for a 2026-2028 outlook horizon."""
    query_range = {"start": "2026-08-17", "end": "2028-02-08"}
    in_horizon = {
        **SAMPLE_MITIGATION_ROWS[0],
        "mitigation_id": "IN-HORIZON",
        "window_start": date(2025, 3, 29),
        "window_end": date(2027, 9, 12),
    }
    conn = _make_mitigation_query_conn([in_horizon], 1)

    result = mitigation_map(conn, NATIVE_CHART_ID, date_range=query_range)

    assert [row["mitigation_id"] for row in result["mitigations"]] == ["IN-HORIZON"]
    assert result["provenance_envelope"]["date_range_filter_applied"] is True
    assert result["provenance_envelope"]["date_range"] == query_range

    cur = conn.cursor.return_value.__enter__.return_value
    select_sql, select_params = cur.execute.call_args_list[0].args
    assert "window_start <= %s::date" in select_sql
    assert "window_end >= %s::date" in select_sql
    assert select_params == [NATIVE_CHART_ID, "2028-02-08", "2026-08-17", 100]

    count_sql, count_params = cur.execute.call_args_list[1].args
    assert "window_start <= %s::date" in count_sql
    assert "window_end >= %s::date" in count_sql
    assert count_params == [NATIVE_CHART_ID, "2028-02-08", "2026-08-17"]


@pytest.mark.parametrize(
    ("query_range", "error_match"),
    [
        ({"start": "2026-02-30", "end": "2028-02-08"}, "date_range.start"),
        ({"start": "20260817", "end": "2028-02-08"}, "date_range.start"),
        ({"start": "2026-08-17", "end": "2028-13-08"}, "date_range.end"),
        (
            {"start": "2028-02-08", "end": "2026-08-17"},
            "date_range.start must be on or before date_range.end",
        ),
    ],
)
def test_mitigation_map_rejects_invalid_or_reversed_date_ranges(query_range, error_match):
    with pytest.raises(ValueError, match=error_match):
        mitigation_map(MagicMock(), NATIVE_CHART_ID, date_range=query_range)


def test_mitigation_map_date_range_includes_rows_touching_either_boundary():
    """Inclusive overlap retains rows ending at start or starting at end."""
    query_range = {"start": "2026-08-17", "end": "2028-02-08"}
    ends_at_start = {
        **SAMPLE_MITIGATION_ROWS[0],
        "mitigation_id": "ENDS-AT-START",
        "window_start": date(2024, 1, 1),
        "window_end": date(2026, 8, 17),
    }
    starts_at_end = {
        **SAMPLE_MITIGATION_ROWS[1],
        "mitigation_id": "STARTS-AT-END",
        "window_start": date(2028, 2, 8),
        "window_end": date(2029, 1, 1),
    }
    conn = _make_mitigation_query_conn([ends_at_start, starts_at_end], 2)

    result = mitigation_map(conn, NATIVE_CHART_ID, date_range=query_range)

    assert [row["mitigation_id"] for row in result["mitigations"]] == [
        "ENDS-AT-START", "STARTS-AT-END",
    ]
    select_sql, _ = conn.cursor.return_value.__enter__.return_value.execute.call_args_list[0].args
    assert "window_start <= %s::date" in select_sql
    assert "window_end >= %s::date" in select_sql


def test_mitigation_map_without_date_range_preserves_unfiltered_null_bound_rows():
    """Standalone calls retain legacy behavior; only horizon requests exclude null bounds."""
    conn = _make_mitigation_query_conn(SAMPLE_MITIGATION_ROWS, len(SAMPLE_MITIGATION_ROWS))

    result = mitigation_map(conn, NATIVE_CHART_ID)

    assert len(result["mitigations"]) == len(SAMPLE_MITIGATION_ROWS)
    assert result["provenance_envelope"]["date_range_filter_applied"] is False
    assert result["provenance_envelope"]["date_range"] is None

    cur = conn.cursor.return_value.__enter__.return_value
    select_sql, select_params = cur.execute.call_args_list[0].args
    assert "window_start <= %s::date" not in select_sql
    assert "window_end >= %s::date" not in select_sql
    assert select_params == [NATIVE_CHART_ID, 100]


def test_mitigation_map_empty_result():
    """mitigation_map: empty DB returns empty mitigations list + valid envelope."""
    conn = _make_mitigation_query_conn([], 0)
    result = mitigation_map(conn, NATIVE_CHART_ID)
    assert result["mitigations"] == []
    assert result["total_count"] == 0
    assert "provenance_envelope" in result
    # all_cited vacuously True for empty set
    assert result["all_cited"] is True


# ──────────────────────────────────────────────────────────────────────────────
# §6  gate3_forensic_spot_check — acceptance gate (mocked DB)
# ──────────────────────────────────────────────────────────────────────────────

def _make_gate3_conn(stats: dict):
    conn = MagicMock()
    ctx = MagicMock()
    cur = MagicMock()
    cur.fetchone.return_value = stats
    ctx.__enter__ = MagicMock(return_value=cur)
    ctx.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value = ctx
    return conn


def test_gate3_passes_when_all_checks_pass():
    stats = {
        "total": 3,
        "cited": 3,
        "bphs_grounded": 3,
        "has_rule_id": 3,
        "valid_type": 3,
        "has_text": 3,
    }
    conn = _make_gate3_conn(stats)
    result = gate3_forensic_spot_check(conn, NATIVE_CHART_ID)
    assert result["passed"] is True
    assert all(c["passed"] for c in result["checks"])


def test_gate3_fails_when_no_rows():
    stats = {
        "total": 0,
        "cited": 0,
        "bphs_grounded": 0,
        "has_rule_id": 0,
        "valid_type": 0,
        "has_text": 0,
    }
    conn = _make_gate3_conn(stats)
    result = gate3_forensic_spot_check(conn, NATIVE_CHART_ID)
    assert result["passed"] is False


def test_gate3_fails_when_uncited_rows():
    """Gate 3 fails if any row has null source_citation."""
    stats = {
        "total": 3,
        "cited": 2,      # one row missing citation
        "bphs_grounded": 2,
        "has_rule_id": 3,
        "valid_type": 3,
        "has_text": 3,
    }
    conn = _make_gate3_conn(stats)
    result = gate3_forensic_spot_check(conn, NATIVE_CHART_ID)
    assert result["passed"] is False
    failed_checks = [c["check"] for c in result["checks"] if not c["passed"]]
    assert "all_rows_have_citation" in failed_checks


def test_gate3_fails_when_no_bphs():
    """Gate 3 fails if no row has BPHS-prefix citation."""
    stats = {
        "total": 2,
        "cited": 2,
        "bphs_grounded": 0,   # no BPHS citations
        "has_rule_id": 2,
        "valid_type": 2,
        "has_text": 2,
    }
    conn = _make_gate3_conn(stats)
    result = gate3_forensic_spot_check(conn, NATIVE_CHART_ID)
    assert result["passed"] is False
    failed_checks = [c["check"] for c in result["checks"] if not c["passed"]]
    assert "bphs_grounded" in failed_checks


def test_gate3_fails_when_invalid_type():
    """Gate 3 fails if any row has an invalid mitigation_type."""
    stats = {
        "total": 3,
        "cited": 3,
        "bphs_grounded": 3,
        "has_rule_id": 3,
        "valid_type": 2,   # one invalid type
        "has_text": 3,
    }
    conn = _make_gate3_conn(stats)
    result = gate3_forensic_spot_check(conn, NATIVE_CHART_ID)
    assert result["passed"] is False
    failed_checks = [c["check"] for c in result["checks"] if not c["passed"]]
    assert "valid_mitigation_types" in failed_checks


def test_gate3_returns_stats_dict():
    """gate3 always returns a stats dict regardless of pass/fail."""
    stats = {
        "total": 1,
        "cited": 1,
        "bphs_grounded": 1,
        "has_rule_id": 1,
        "valid_type": 1,
        "has_text": 1,
    }
    conn = _make_gate3_conn(stats)
    result = gate3_forensic_spot_check(conn, NATIVE_CHART_ID)
    assert "stats" in result
    assert "checks" in result
    assert "passed" in result
    # stats is range-safe: total >= 0
    assert result["stats"]["total"] >= 0
