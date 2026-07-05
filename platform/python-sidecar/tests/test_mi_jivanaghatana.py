"""
test_mi_jivanaghatana.py — LEL markdown raw-field fallback parser (A6, BA
Pre-Rebuild Gate, 2026-07-05).

DB-free tests for pipeline.orchestrator.writers.mi_jivanaghatana's LEL
markdown parser. Covers the recurring failure mode: narrative prose fields
(description / native_reflection / notes) contain unquoted colons that break
strict YAML block-mapping, even though this writer never reads those fields.
The fallback recovers the event via its consumed top-level fields (date,
category, subcategory, magnitude, ...) as raw uninterpreted strings.
"""
from __future__ import annotations

from pipeline.orchestrator.writers.mi_jivanaghatana import (
    _parse_block_raw,
    _parse_lel_markdown,
    _LEL_MARKDOWN_PATH,
)

BROKEN_BLOCK = '''EVT.2019.05.XX.01:
  date: 2019-05-XX
  date_confidence: month-exact
  category: residential+travel
  subcategory: foreign_move_start
  description: Moved to the United States on deputation.
  magnitude: life-altering
  valence: positive
  native_reflection: "The move happened in May 2019." Doc framing: "US Stint: work permit."
  notes: Sets up entrepreneurial awakening post-2023.'''

WELL_FORMED_BLOCK = '''EVT.1998.02.16.01:
  date: 1998-02-16
  category: education
  subcategory: school_transfer
  magnitude: significant
  notes: no colons here'''

NON_EVENT_BLOCK = '''PATTERN.SPORTS_LUCK.01:
  trait: Sports participation correlates with better luck.
  note: unrelated pattern block, not an EVT'''


def test_broken_block_fails_strict_yaml():
    import yaml
    try:
        yaml.safe_load(BROKEN_BLOCK)
        assert False, "expected this block to fail strict YAML parsing"
    except yaml.YAMLError:
        pass


def test_raw_fallback_recovers_consumed_fields():
    recovered = _parse_block_raw(BROKEN_BLOCK)
    assert recovered is not None
    assert recovered["event_id"] == "EVT.2019.05.XX.01"
    assert recovered["date"] == "2019-05-XX"
    assert recovered["category"] == "residential+travel"
    assert recovered["subcategory"] == "foreign_move_start"
    assert recovered["magnitude"] == "life-altering"
    # Narrative fields are not consumed — the fallback doesn't need them.
    assert "description" not in recovered
    assert "native_reflection" not in recovered
    assert "notes" not in recovered


def test_raw_fallback_rejects_non_event_blocks():
    assert _parse_block_raw(NON_EVENT_BLOCK) is None


def test_well_formed_block_parses_via_normal_yaml_path(tmp_path):
    md = tmp_path / "LEL.md"
    md.write_text(f"```yaml\n{WELL_FORMED_BLOCK}\n```\n", encoding="utf-8")
    events, _sha = _parse_lel_markdown(md)
    assert len(events) == 1
    assert events[0]["event_id"] == "EVT.1998.02.16.01"
    assert events[0]["category"] == "education"


def test_broken_block_recovers_via_fallback_end_to_end(tmp_path):
    md = tmp_path / "LEL.md"
    md.write_text(f"```yaml\n{BROKEN_BLOCK}\n```\n", encoding="utf-8")
    events, _sha = _parse_lel_markdown(md)
    assert len(events) == 1
    assert events[0]["event_id"] == "EVT.2019.05.XX.01"
    assert events[0]["date"] == "2019-05-XX"


def test_real_lel_file_recovers_all_evt_blocks_with_date_and_category():
    assert _LEL_MARKDOWN_PATH.exists(), (
        f"LEL markdown not found at resolved path {_LEL_MARKDOWN_PATH}"
    )
    events, _sha = _parse_lel_markdown(_LEL_MARKDOWN_PATH)
    assert len(events) > 0
    missing_date = [e["event_id"] for e in events if not e.get("date")]
    missing_category = [e["event_id"] for e in events if not e.get("category")]
    assert not missing_date, f"events missing date: {missing_date}"
    assert not missing_category, f"events missing category: {missing_category}"
