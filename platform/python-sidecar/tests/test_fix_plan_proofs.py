"""
PRE_REGEN_FIX_PLAN proof-tests — 6 fixes, 1 proof each.

§0 governing rule: every assertion targets the ACTUAL offending value, not the
author's assumed pattern.  Three 'fixed≠complete' misses have preceded this
file; do not add a fourth.

Fixes covered:
  FIX 1 — F-W5-001: l4_anchors chart_id guard (non-native → empty)
  FIX 2 — F-W4-005: ka_dasha_kala _update_registry_health cursor, not conn.execute
  FIX 3 — F-W5-003: ph_muhurta career lord derived per chart, not hardcoded Aries-H10
  FIX 4 — F-W5-002: strip_lel_citations catches LEL EVT.* parenthetical + bare patterns
  FIX 5 — F-W4-002: ka_sangam._build_enrichment_context method exists + signature
  FIX 6 — F-W4-004: ka_vighnakara stubs return non-None with detail.stub=True
"""
import inspect
import re
import pytest


# ---------------------------------------------------------------------------
# FIX 1 — F-W5-001: l4_anchors chart_id guard
# ---------------------------------------------------------------------------

def test_fix1_non_native_chart_id_returns_empty_anchors():
    """Non-native chart_id must return ok=True with empty anchors list."""
    from brahmagyan.phala.l4_anchors import query_phala_anchors, NATIVE_CHART_ID

    NON_NATIVE = "aaaaaaaa-0000-0000-0000-000000000000"
    assert NON_NATIVE != NATIVE_CHART_ID, "test precondition: must use a different chart_id"

    result = query_phala_anchors(
        chart_id=NON_NATIVE,
        date_range={"start": "2025-01-01", "end": "2027-12-31"},
    )
    assert result["ok"] is True
    assert result["anchors"] == [], f"expected [], got {result['anchors']!r}"
    assert result["anchor_count"] == 0


def test_fix1_native_chart_id_returns_anchors():
    """NATIVE_CHART_ID must return at least 20 anchors (volume floor is ≥20)."""
    from brahmagyan.phala.l4_anchors import query_phala_anchors, NATIVE_CHART_ID

    result = query_phala_anchors(
        chart_id=NATIVE_CHART_ID,
        date_range={"start": "2024-01-01", "end": "2040-12-31"},
    )
    assert result["ok"] is True
    assert result["anchor_count"] >= 20, (
        f"native chart should return >=20 anchors, got {result['anchor_count']}"
    )


# ---------------------------------------------------------------------------
# FIX 2 — F-W4-005: ka_dasha_kala _update_registry_health uses cursor
# ---------------------------------------------------------------------------

def test_fix2_registry_health_uses_cursor_not_conn_execute():
    """_update_registry_health must NOT call conn.execute() directly.

    The offending line was conn.execute(...) — psycopg3 connections have no
    .execute() on the connection object.  The fix uses:
        with conn.cursor() as cur: cur.execute(...)
    """
    import inspect
    from services.ka_dasha_kala.writer import _update_registry_health

    src = inspect.getsource(_update_registry_health)
    # Must not have bare conn.execute( — only cur.execute( is acceptable
    assert "conn.execute(" not in src, (
        "_update_registry_health still calls conn.execute() — psycopg3 AttributeError. "
        "Use 'with conn.cursor() as cur: cur.execute(...)'"
    )
    assert "cur.execute(" in src, (
        "_update_registry_health must delegate to cur.execute(), not conn.execute()"
    )


def test_fix2_run_extracts_chart_id():
    """KaDashaKalaWriter.run() must extract build chart_id from ctx.config.

    Uses source inspection to avoid triggering duplicate @register error
    from _build_writer_class() (registration is a singleton side-effect).
    """
    import services.ka_dasha_kala.writer as _mod
    # Read source directly — the writer is defined inside _build_writer_class
    src = inspect.getsource(_mod)
    assert "ctx.config" in src, (
        "run() must extract chart_id via ctx.config.get('chart_id', '')"
    )
    assert "_CANONICAL_CHART_ID" in src, (
        "run() must compare build chart_id against _CANONICAL_CHART_ID"
    )


# ---------------------------------------------------------------------------
# FIX 3 — F-W5-003: ph_muhurta career lord derived per chart
# ---------------------------------------------------------------------------

def test_fix3_resolve_career_lord_sagittarius_lagna():
    """A chart with Sagittarius lagna should yield H10=Virgo=Mercury, not Saturn.

    H10 from Sagittarius (9): ((9-1+9) % 12) + 1 = 17%12+1 = 6 → Mercury.
    Native Aries (1): ((1-1+9) % 12) + 1 = 10 → Saturn.
    The fix proves non-native lagnas produce the correct non-native lord.
    """
    from pipeline.orchestrator.writers.ph_muhurta import PhMuhurtaWriter

    writer = PhMuhurtaWriter()

    class _MockCursor:
        def __init__(self, sign):
            self._sign = sign
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def execute(self, *a, **kw):
            pass
        def fetchone(self):
            return (self._sign,)

    class _MockConn:
        def __init__(self, sign):
            self._sign = sign
        def cursor(self):
            return _MockCursor(self._sign)

    # Sagittarius lagna → H10 is Mercury
    result = writer._resolve_career_lord(_MockConn('Sagittarius'), 'fake-chart-id')
    assert result == 'mercury', (
        f"Sagittarius lagna should yield career_lord='mercury', got {result!r}"
    )

    # Aries lagna (native) → H10 is Saturn
    result_aries = writer._resolve_career_lord(_MockConn('Aries'), 'fake-chart-id')
    assert result_aries == 'saturn', (
        f"Aries lagna should yield career_lord='saturn', got {result_aries!r}"
    )


def test_fix3_run_builds_action_graha_overrides():
    """run() must create action_graha_overrides that can differ from native default."""
    from pipeline.orchestrator.writers.ph_muhurta import PhMuhurtaWriter
    src = inspect.getsource(PhMuhurtaWriter.run)
    assert "action_graha_overrides" in src, (
        "run() must build action_graha_overrides dict with chart-specific career lord"
    )
    assert "_resolve_career_lord" in src, (
        "run() must call self._resolve_career_lord(conn, chart_id)"
    )


# ---------------------------------------------------------------------------
# FIX 4 — F-W5-002: strip_lel_citations sweeps ANCHOR_CATALOG clean
# ---------------------------------------------------------------------------

def test_fix4_strip_lel_citations_clears_lel_evt_parenthetical():
    """strip_lel_citations must remove '(LEL EVT.YYYY ...)' blocks.

    Offending string (ANC.CAREER.2027.01):
        '(LEL EVT.2019 approximate; exact date in LEL gap register).'
    """
    from brahmagyan.phala.l4_anchors import strip_lel_citations

    offending = (
        "Native transitions into a US-based career trajectory "
        "(LEL EVT.2019 approximate; exact date in LEL gap register). "
        "Outer planets confirm."
    )
    cleaned = strip_lel_citations(offending)
    assert 'LEL' not in cleaned, (
        f"strip_lel_citations still leaks LEL in: {cleaned!r}"
    )


def test_fix4_strip_lel_citations_clears_per_lel():
    """strip_lel_citations must remove 'per LEL...' phrases."""
    from brahmagyan.phala.l4_anchors import strip_lel_citations

    offending = "Native already experiencing separation strain per LEL. 4-signal basis."
    cleaned = strip_lel_citations(offending)
    assert 'LEL' not in cleaned, (
        f"strip_lel_citations still leaks LEL in: {cleaned!r}"
    )


def test_fix4_entire_anchor_catalog_clean():
    """MANDATORY: every notes string in ANCHOR_CATALOG must be LEL-free after stripping.

    This is the §0-level proof: sweep the ACTUAL catalog, not synthetic data.
    """
    from brahmagyan.phala.l4_anchors import ANCHOR_CATALOG, strip_lel_citations

    leaking = []
    for anchor in ANCHOR_CATALOG:
        notes = anchor.get('notes', '') or ''
        # strip_lel_citations is the same function the API will call
        cleaned = strip_lel_citations(notes)
        if 'lel' in cleaned.lower():
            leaking.append({
                'anchor_id': anchor.get('anchor_id'),
                'raw':       notes[:120],
                'stripped':  cleaned[:120],
            })

    assert leaking == [], (
        f"ANCHOR_CATALOG still leaks LEL citations after strip in {len(leaking)} anchor(s):\n"
        + "\n".join(str(x) for x in leaking)
    )


# ---------------------------------------------------------------------------
# FIX 5 — F-W4-002: ka_sangam _build_enrichment_context present + wired
# ---------------------------------------------------------------------------

def test_fix5_build_enrichment_context_method_exists():
    """KaSangamWriter must have a _build_enrichment_context method."""
    from pipeline.orchestrator.writers.ka_sangam import KaSangamWriter

    assert hasattr(KaSangamWriter, '_build_enrichment_context'), (
        "KaSangamWriter missing _build_enrichment_context — C7/C11/C12 always score 0.0"
    )


def test_fix5_generate_windows_accepts_enrichment_context():
    """_generate_windows must accept an enrichment_context parameter."""
    from pipeline.orchestrator.writers.ka_sangam import KaSangamWriter

    sig = inspect.signature(KaSangamWriter._generate_windows)
    assert 'enrichment_context' in sig.parameters, (
        "_generate_windows missing enrichment_context parameter — context never passed to mode_a/mode_b"
    )


def test_fix5_mode_calls_pass_enrichment_context():
    """mode_a_search and mode_b_sweep must receive enrichment_context inside _generate_windows."""
    from pipeline.orchestrator.writers.ka_sangam import KaSangamWriter

    src = inspect.getsource(KaSangamWriter._generate_windows)
    assert 'enrichment_context' in src, (
        "_generate_windows does not pass enrichment_context to mode_a_search/mode_b_sweep"
    )


def test_fix5_plan_substeps_builds_enrichment_ctx():
    """plan_substeps must assign self._enrichment_ctx."""
    from pipeline.orchestrator.writers.ka_sangam import KaSangamWriter

    src = inspect.getsource(KaSangamWriter.plan_substeps)
    assert '_enrichment_ctx' in src, (
        "plan_substeps does not build self._enrichment_ctx — context built but never attached"
    )


# ---------------------------------------------------------------------------
# FIX 6 — F-W4-004: ka_vighnakara stubs return non-None with stub=True
# ---------------------------------------------------------------------------

def test_fix6_check_gandanta_returns_stub_dict():
    """_check_gandanta(date) must return a dict with detail.stub=True, not None."""
    from pipeline.orchestrator.writers.ka_vighnakara import _check_gandanta
    from datetime import date

    result = _check_gandanta(date(2026, 6, 15))
    assert result is not None, (
        "_check_gandanta returns None — silent coverage gap; must return stub dict"
    )
    assert isinstance(result, dict), f"expected dict, got {type(result)}"
    assert result.get('obstruction_type') == 'gandanta'
    assert result.get('detail', {}).get('stub') is True, (
        "gandanta stub must have detail.stub=True so callers know it is not a real check"
    )


def test_fix6_check_papakartari_returns_stub_dict():
    """_check_papakartari(date) must return a dict with detail.stub=True, not None."""
    from pipeline.orchestrator.writers.ka_vighnakara import _check_papakartari
    from datetime import date

    result = _check_papakartari(date(2026, 6, 15))
    assert result is not None, (
        "_check_papakartari returns None — silent coverage gap; must return stub dict"
    )
    assert isinstance(result, dict), f"expected dict, got {type(result)}"
    assert result.get('obstruction_type') == 'papakartari'
    assert result.get('detail', {}).get('stub') is True, (
        "papakartari stub must have detail.stub=True"
    )


def test_fix6_none_peak_date_still_returns_none():
    """_check_gandanta(None) and _check_papakartari(None) must return None (no stub for unknown date)."""
    from pipeline.orchestrator.writers.ka_vighnakara import _check_gandanta, _check_papakartari

    assert _check_gandanta(None) is None, "_check_gandanta(None) should return None"
    assert _check_papakartari(None) is None, "_check_papakartari(None) should return None"
