"""
test_b4_lord_tokenizer.py — TDD red: failing tests for lord tokenizer fix (B4).

Six acceptance criteria — all FAIL at this commit because:
  - _LORD_TOKEN_RE does not exist yet in writer.py
  - _build_lord_rows emits compound strings as-is (verbatim)

AC-E1: qualifier 'afflicted' stripped, clean lord ref emitted
AC-E2: compound 'maraka lords (2L/7L)' expands to 2L + 7L
AC-E3: slash-compound '2L/11L afflicted' expands to 2L + 11L
AC-E4: regression guard — already-clean '7L','2L' unchanged
AC-E5: _LORD_TOKEN_RE constant importable and correct pattern
AC-E6: pure-text entry with no \\d+L tokens yields zero rows
"""
from __future__ import annotations

import re
import pytest

from services.ka_gochara_resonance.writer import _build_lord_rows


# ── AC-E5: constant must be importable and have the right pattern ─────────────

def test_ac_e5_lord_token_re_importable_and_correct():
    """_LORD_TOKEN_RE is importable, compiled, pattern == r'\\d+L'."""
    from services.ka_gochara_resonance.writer import _LORD_TOKEN_RE
    assert isinstance(_LORD_TOKEN_RE, re.Pattern), (
        "_LORD_TOKEN_RE must be a compiled re.Pattern"
    )
    assert _LORD_TOKEN_RE.pattern == r'\d+L', (
        f"Expected pattern r'\\d+L', got {_LORD_TOKEN_RE.pattern!r}"
    )


# ── AC-E1: qualifier stripping ────────────────────────────────────────────────

def test_ac_e1_qualifier_stripped_single():
    """'10L afflicted' -> exactly one row with target_ref == '10L'."""
    rows = _build_lord_rows("career_setback", ["10L afflicted"], None)
    refs = [r["target_ref"] for r in rows]
    assert len(rows) == 1, f"Expected 1 row, got {len(rows)}: {refs}"
    assert refs[0] == "10L", f"Expected '10L', got {refs[0]!r}"


# ── AC-E2: compound with parenthesised pair ───────────────────────────────────

def test_ac_e2_compound_paren_expands():
    """'maraka lords (2L/7L)' plus clean '8L' -> 3 rows: {8L, 2L, 7L}."""
    rows = _build_lord_rows("bereavement", ["8L", "maraka lords (2L/7L)"], None)
    refs = {r["target_ref"] for r in rows}
    assert len(rows) == 3, f"Expected 3 rows, got {len(rows)}: sorted={sorted(refs)}"
    assert refs == {"8L", "2L", "7L"}, f"Expected {{'8L','2L','7L'}}, got {refs}"


# ── AC-E3: slash-compound with qualifier ─────────────────────────────────────

def test_ac_e3_slash_compound_expands():
    """'2L/11L afflicted' plus clean '12L' -> 3 rows: {2L, 11L, 12L}."""
    rows = _build_lord_rows("major_loss", ["2L/11L afflicted", "12L"], None)
    refs = {r["target_ref"] for r in rows}
    assert len(rows) == 3, f"Expected 3 rows, got {len(rows)}: sorted={sorted(refs)}"
    assert refs == {"2L", "11L", "12L"}, f"Expected {{'2L','11L','12L'}}, got {refs}"


# ── AC-E4: regression guard — already-clean refs unchanged ───────────────────

def test_ac_e4_clean_refs_unchanged():
    """Already-clean '7L','2L' -> exactly 2 rows with those exact refs."""
    rows = _build_lord_rows("marriage", ["7L", "2L"], None)
    refs = {r["target_ref"] for r in rows}
    assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}: sorted={sorted(refs)}"
    assert refs == {"7L", "2L"}, f"Expected {{'7L','2L'}}, got {refs}"


# ── AC-E6: pure-text entry (no \\d+L) yields zero rows ───────────────────────

def test_ac_e6_pure_text_entry_dropped():
    """Entry with no \\d+L token -> zero rows emitted."""
    rows = _build_lord_rows("test", ["some text with no lord ref"], None)
    assert rows == [], f"Expected [], got {rows}"
