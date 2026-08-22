"""
Tests for Transit/Gochara Subsystem Gate-1.

Covers:
  - bg_transit_rules writer registration and run()
  - ga_transit_anchors writer registration, has_substeps, plan_substeps
  - L0 data integrity (classical_citation hard-gate)
  - Saturn vedha pairs
  - Jupiter favourable houses
  - FORENSIC Moon sign assertion
  - dry_run returns 0 rows
"""
from __future__ import annotations

import pytest


# ── 1. bg_transit_rules writer — registration ─────────────────────────────────

def test_bg_transit_rules_writer_registered():
    """bg_transit_rules must be importable and registered."""
    from pipeline.orchestrator.writers import get_writer  # type: ignore[attr-defined]

    writer_cls = get_writer("bg_transit_rules")
    assert writer_cls is not None, "bg_transit_rules must be registered"
    assert writer_cls.asset_id == "bg_transit_rules"


def test_bg_transit_rules_is_writer_base_subclass():
    """bg_transit_rules must subclass WriterBase."""
    from pipeline.orchestrator.writers import WriterBase, get_writer
    writer_cls = get_writer("bg_transit_rules")
    assert issubclass(writer_cls, WriterBase)


# ── 2. ga_transit_anchors writer — registration + heavy-writer metadata ───────

def test_ga_transit_anchors_writer_registered():
    """ga_transit_anchors must be importable and registered."""
    from pipeline.orchestrator.writers import get_writer
    writer_cls = get_writer("ga_transit_anchors")
    assert writer_cls is not None, "ga_transit_anchors must be registered"
    assert writer_cls.asset_id == "ga_transit_anchors"


def test_ga_transit_anchors_has_substeps_true():
    """ga_transit_anchors is a heavy writer: has_substeps must be True."""
    from pipeline.orchestrator.writers.ga_transit_anchors import GaTransitAnchorsWriter
    assert GaTransitAnchorsWriter.has_substeps is True


def test_ga_transit_anchors_is_writer_base_subclass():
    """ga_transit_anchors must subclass WriterBase."""
    from pipeline.orchestrator.writers import WriterBase
    from pipeline.orchestrator.writers.ga_transit_anchors import GaTransitAnchorsWriter
    assert issubclass(GaTransitAnchorsWriter, WriterBase)


# ── 3. plan_substeps returns exactly 5 sub-steps ─────────────────────────────

def test_plan_substeps_returns_five():
    """plan_substeps must return exactly 5 sub-steps (one per ayanamsha)."""
    from unittest.mock import MagicMock
    from pipeline.orchestrator.writers.ga_transit_anchors import GaTransitAnchorsWriter
    from pipeline.orchestrator.writers import ContextSpec

    writer = GaTransitAnchorsWriter()
    ctx = MagicMock()
    steps = writer.plan_substeps(ctx)
    assert len(steps) == 5, f"Expected 5 sub-steps, got {len(steps)}"


def test_plan_substeps_keys_are_ayanamsha_prefixed():
    """Each sub-step key must start with 'ayanamsha_'."""
    from unittest.mock import MagicMock
    from pipeline.orchestrator.writers.ga_transit_anchors import GaTransitAnchorsWriter
    from pipeline.orchestrator.writers import ContextSpec

    writer = GaTransitAnchorsWriter()
    ctx = MagicMock()
    steps = writer.plan_substeps(ctx)
    for step in steps:
        assert step.key.startswith("ayanamsha_"), (
            f"Sub-step key '{step.key}' must start with 'ayanamsha_'"
        )


def test_plan_substeps_covers_lahiri():
    """lahiri_chitrapaksha must be one of the 5 sub-step ayanamshas."""
    from unittest.mock import MagicMock
    from pipeline.orchestrator.writers.ga_transit_anchors import GaTransitAnchorsWriter
    from pipeline.orchestrator.writers import ContextSpec

    writer = GaTransitAnchorsWriter()
    ctx = MagicMock()
    steps = writer.plan_substeps(ctx)
    keys = {s.key for s in steps}
    assert "ayanamsha_lahiri_chitrapaksha" in keys


# ── 4. L0 seed data — classical_citation hard-gate ───────────────────────────

def test_all_engine_rows_have_classical_citation():
    """Hard gate: every row in BG_TRANSIT_ENGINE must have non-empty classical_citation."""
    from brahmagyan.l0_transit import BG_TRANSIT_ENGINE

    for row in BG_TRANSIT_ENGINE:
        assert row.get("classical_citation"), (
            f"BG_TRANSIT_ENGINE row graha='{row.get('graha')}' is missing classical_citation"
        )


def test_all_rule_rows_have_classical_citation():
    """Hard gate: every row in BG_TRANSIT_RULES must have non-empty classical_citation."""
    from brahmagyan.l0_transit import BG_TRANSIT_RULES

    for row in BG_TRANSIT_RULES:
        assert row.get("classical_citation"), (
            f"BG_TRANSIT_RULES row graha='{row.get('graha')}' "
            f"primary_house={row.get('primary_house')} is missing classical_citation"
        )


def test_engine_has_nine_grahas():
    """BG_TRANSIT_ENGINE must have exactly 9 grahas (Sun through Ketu)."""
    from brahmagyan.l0_transit import BG_TRANSIT_ENGINE

    grahas = {row["graha"] for row in BG_TRANSIT_ENGINE}
    expected = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"}
    assert grahas == expected, f"Missing grahas: {expected - grahas}"


# ── 5. Saturn vedha pairs ─────────────────────────────────────────────────────

def test_saturn_3rd_vedha_is_12th():
    """Saturn 3rd from Moon (best transit) must have vedha_house = 12."""
    from brahmagyan.l0_transit import BG_TRANSIT_RULES

    saturn_3 = next(
        (r for r in BG_TRANSIT_RULES
         if r["graha"] == "saturn" and r["rule_type"] == "favourable" and r["primary_house"] == 3),
        None,
    )
    assert saturn_3 is not None, "Saturn favourable house 3 rule must exist"
    assert saturn_3["vedha_house"] == 12, (
        f"Saturn 3rd vedha must be 12th, got {saturn_3['vedha_house']}"
    )


def test_saturn_11th_vedha_is_5th():
    """Saturn 11th from Moon must have vedha_house = 5."""
    from brahmagyan.l0_transit import BG_TRANSIT_RULES

    saturn_11 = next(
        (r for r in BG_TRANSIT_RULES
         if r["graha"] == "saturn" and r["rule_type"] == "favourable" and r["primary_house"] == 11),
        None,
    )
    assert saturn_11 is not None, "Saturn favourable house 11 rule must exist"
    assert saturn_11["vedha_house"] == 5, (
        f"Saturn 11th vedha must be 5th, got {saturn_11['vedha_house']}"
    )


# ── 6. Jupiter favourable houses ─────────────────────────────────────────────

def test_jupiter_11th_is_favourable():
    """Jupiter 11th from Moon must be marked favourable (the best Jupiter transit)."""
    from brahmagyan.l0_transit import BG_TRANSIT_RULES

    jup_11 = next(
        (r for r in BG_TRANSIT_RULES
         if r["graha"] == "jupiter" and r["primary_house"] == 11 and r["rule_type"] == "favourable"),
        None,
    )
    assert jup_11 is not None, "Jupiter favourable house 11 must exist in BG_TRANSIT_RULES"


def test_jupiter_favourable_houses_include_2_5_7_9_11():
    """Jupiter favourable houses must include 2, 5, 7, 9, 11 per BPHS Ch.29."""
    from brahmagyan.l0_transit import BG_TRANSIT_RULES

    jupiter_favourable = {
        r["primary_house"]
        for r in BG_TRANSIT_RULES
        if r["graha"] == "jupiter" and r["rule_type"] == "favourable"
    }
    required = {2, 5, 7, 9, 11}
    assert required.issubset(jupiter_favourable), (
        f"Jupiter favourable houses must include {required}; found {jupiter_favourable}"
    )


# ── 6b. F-145: Venus unfavourable set (6th/7th/10th from Moon) ──────────────────

def test_venus_unfavourable_houses_are_exactly_6_7_10():
    """
    F-145: Venus's unfavourable transit houses must be exactly {6, 7, 10} per
    Phaladeepika Adh. XXVI Slokas 2, 8 & 21 (verified against the ingested corpus,
    owner-ruled 2026-08-22). 11th and 12th are classically favourable — the writer
    already carries those as favourable rows — and must NOT appear here.
    """
    from brahmagyan.l0_transit import BG_TRANSIT_RULES

    venus_unfavourable = {
        r["primary_house"]
        for r in BG_TRANSIT_RULES
        if r["graha"] == "venus" and r["rule_type"] == "unfavourable"
    }
    assert venus_unfavourable == {6, 7, 10}, (
        f"Venus unfavourable houses must be exactly {{6, 7, 10}}; found {venus_unfavourable}"
    )


def test_venus_unfavourable_rows_cite_phaladeepika_not_bphs():
    """
    F-145: the three Venus unfavourable rows must cite the verified Phaladeepika
    source (PD_ADH26_S2_8_21) — never 'BPHS Ch.29', which could not be verified
    against the ingested corpus for this specific content.
    """
    from brahmagyan.l0_transit import BG_TRANSIT_RULES, PD_ADH26_S2_8_21

    venus_unfavourable = [
        r
        for r in BG_TRANSIT_RULES
        if r["graha"] == "venus" and r["rule_type"] == "unfavourable"
    ]
    assert len(venus_unfavourable) == 3
    for row in venus_unfavourable:
        assert row["classical_citation"] == PD_ADH26_S2_8_21
        assert "BPHS" not in row["classical_citation"]
        assert row["vedha_house"] is None


def test_venus_unfavourable_houses_omitted_when_absent_from_source():
    """
    Constructed-state test: if a house is missing from a BG_TRANSIT_RULES-shaped
    source list, the reconciliation logic must treat any corresponding DB row as
    stale (to be retired/omitted); if present, it must not.
    """
    from brahmagyan.l0_transit import compute_stale_rule_ids

    # Source list missing house 10 (only 6 and 7 present).
    partial_source = [
        {"rule_type": "unfavourable", "graha": "venus", "primary_house": 6},
        {"rule_type": "unfavourable", "graha": "venus", "primary_house": 7},
    ]
    db_rows = [
        (46, "venus", "unfavourable", 6),
        (47, "venus", "unfavourable", 7),
        (48, "venus", "unfavourable", 10),
    ]
    assert compute_stale_rule_ids(partial_source, db_rows) == [48]

    # Full source list (6, 7, 10 all present) — nothing stale.
    full_source = partial_source + [
        {"rule_type": "unfavourable", "graha": "venus", "primary_house": 10},
    ]
    assert compute_stale_rule_ids(full_source, db_rows) == []


# ── 7. dry_run returns 0 rows ─────────────────────────────────────────────────

def test_bg_transit_rules_dry_run_returns_zero():
    """bg_transit_rules writer: dry_run=True must return 0 DB writes."""
    from unittest.mock import MagicMock
    from pipeline.orchestrator.writers import get_writer

    writer_cls = get_writer("bg_transit_rules")
    writer = writer_cls()
    ctx = MagicMock()
    ctx.dry_run = True
    ctx.db_conn = MagicMock()
    ctx.build_id = "test-dry-build"
    ctx.config = {}

    result = writer.run(ctx)

    assert result.asset_id == "bg_transit_rules"
    assert result.rows_inserted == 0, (
        f"dry_run must return 0 rows_inserted, got {result.rows_inserted}"
    )
    # dry_run: seed_transit_rules returns counts but makes no DB calls
    ctx.db_conn.cursor.assert_not_called()


def test_ga_transit_anchors_dry_run_substep_returns_zero():
    """ga_transit_anchors: dry_run=True substep must return 0 rows, no DB cursor."""
    from unittest.mock import MagicMock
    from pipeline.orchestrator.writers.ga_transit_anchors import GaTransitAnchorsWriter
    from pipeline.orchestrator.writers import SubStep

    writer = GaTransitAnchorsWriter()
    ctx = MagicMock()
    ctx.config = {"chart_id": "482012f1-710e-4a25-994a-93821f5871aa"}
    ctx.build_id = "test-dry-build"
    ctx.dry_run = True
    ctx.db_conn = MagicMock()

    step = SubStep(key="ayanamsha_lahiri_chitrapaksha", label="test")
    result = writer.run_substep(ctx, step)

    assert result.rows_inserted == 0, f"dry_run must return 0 rows, got {result.rows_inserted}"
    ctx.db_conn.cursor.assert_not_called()


# ── 8. FORENSIC Moon sign assertion ──────────────────────────────────────────

def test_forensic_moon_sign_assertion_raises_on_wrong_sign():
    """
    FORENSIC assertion: if Moon natal_sign != 'aquarius' for canonical chart_id,
    run_substep must raise AssertionError.
    """
    from unittest.mock import MagicMock
    from pipeline.orchestrator.writers.ga_transit_anchors import GaTransitAnchorsWriter
    from pipeline.orchestrator.writers import SubStep

    writer = GaTransitAnchorsWriter()
    # Use plain MagicMock (no spec=) so attribute access isn't restricted
    ctx = MagicMock()
    ctx.config = {"chart_id": "482012f1-710e-4a25-994a-93821f5871aa"}
    ctx.build_id = "test-forensic"
    ctx.dry_run = False

    # Simulate DB returning Moon in wrong sign (scorpio instead of aquarius)
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchall.return_value = [
        ("MOON", "sign", "scorpio", None),
        ("MOON", "longitude_sidereal", None, 300.0),
        ("SUN", "sign", "capricorn", None),
        ("SUN", "longitude_sidereal", None, 285.0),
    ]
    ctx.db_conn.cursor.return_value = mock_cursor

    step = SubStep(key="ayanamsha_lahiri_chitrapaksha", label="test")

    with pytest.raises(AssertionError, match="FORENSIC VIOLATION"):
        writer.run_substep(ctx, step)


def test_forensic_moon_sign_passes_for_aquarius():
    """
    FORENSIC assertion: Moon natal_sign = 'aquarius' for canonical chart must NOT raise.
    Uses a minimal mock that simulates only MOON + SUN rows.
    """
    from unittest.mock import MagicMock
    from pipeline.orchestrator.writers.ga_transit_anchors import GaTransitAnchorsWriter
    from pipeline.orchestrator.writers import SubStep

    writer = GaTransitAnchorsWriter()
    ctx = MagicMock()
    ctx.config = {"chart_id": "482012f1-710e-4a25-994a-93821f5871aa"}
    ctx.build_id = "test-forensic-pass"
    ctx.dry_run = False

    call_count = 0
    fetch_results = [
        [
            ("MOON", "sign", "aquarius", None),
            ("MOON", "longitude_sidereal", None, 315.5),
            ("SUN", "sign", "capricorn", None),
            ("SUN", "longitude_sidereal", None, 285.3),
        ],
        [],   # DELETE returns nothing
        [],   # INSERT returns nothing
    ]

    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)

    def _fetchall():
        nonlocal call_count
        result = fetch_results[min(call_count, len(fetch_results) - 1)]
        call_count += 1
        return result

    mock_cursor.fetchall.side_effect = _fetchall
    ctx.db_conn.cursor.return_value = mock_cursor

    step = SubStep(key="ayanamsha_lahiri_chitrapaksha", label="test")
    # Should NOT raise — Moon is aquarius (FORENSIC pass)
    result = writer.run_substep(ctx, step)
    assert result.asset_id == "ga_transit_anchors"
    assert result.rows_inserted > 0, (
        f"Expected rows_inserted > 0 on FORENSIC-pass substep, got {result.rows_inserted}"
    )
