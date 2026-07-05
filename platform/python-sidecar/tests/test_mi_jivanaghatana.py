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
    _is_template_event_id,
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

# Some LEL sections group more than one event under a single ```yaml fence;
# a narrative-colon break anywhere in the block must not drop the others.
BROKEN_MULTI_EVENT_BLOCK = '''EVT.2000.XX.XX.01:
  date: 2000-XX-XX
  category: education
  subcategory: school_start
  magnitude: moderate
  notes: fine, no colons
EVT.2001.03.XX.01:
  date: 2001-03-XX
  category: education
  subcategory: school_transition
  magnitude: moderate
  native_reflection: "Transferred schools." Doc framing: "Mid-year: switch."'''

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
    assert len(recovered) == 1
    ev = recovered[0]
    assert ev["event_id"] == "EVT.2019.05.XX.01"
    assert ev["date"] == "2019-05-XX"
    assert ev["category"] == "residential+travel"
    assert ev["subcategory"] == "foreign_move_start"
    assert ev["magnitude"] == "life-altering"
    # Narrative fields are not consumed — the fallback doesn't need them.
    assert "description" not in ev
    assert "native_reflection" not in ev
    assert "notes" not in ev


def test_raw_fallback_recovers_all_events_in_a_multi_event_block():
    recovered = _parse_block_raw(BROKEN_MULTI_EVENT_BLOCK)
    ids = {ev["event_id"] for ev in recovered}
    assert ids == {"EVT.2000.XX.XX.01", "EVT.2001.03.XX.01"}
    by_id = {ev["event_id"]: ev for ev in recovered}
    assert by_id["EVT.2000.XX.XX.01"]["date"] == "2000-XX-XX"
    assert by_id["EVT.2001.03.XX.01"]["date"] == "2001-03-XX"
    assert by_id["EVT.2001.03.XX.01"]["subcategory"] == "school_transition"


def test_raw_fallback_rejects_non_event_blocks():
    assert _parse_block_raw(NON_EVENT_BLOCK) == []


def test_template_event_id_detection():
    assert _is_template_event_id("EVT.YYYY.MM.DD.XX")
    # XX is a legitimate "unknown day/month" marker on real events —
    # only the literal YYYY placeholder marks the illustrative template.
    assert not _is_template_event_id("EVT.2019.05.XX.01")
    assert not _is_template_event_id("EVT.CURRENT.01")


def test_template_block_does_not_leak_via_normal_yaml_path(tmp_path):
    md = tmp_path / "LEL.md"
    md.write_text(
        "```yaml\nEVT.YYYY.MM.DD.XX:\n  date: [YYYY-MM-DD | YYYY-MM-XX]\n  category: [placeholder]\n```\n",
        encoding="utf-8",
    )
    events, _sha = _parse_lel_markdown(md)
    assert events == []


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


def _real_evt_keys(text: str) -> set[str]:
    """Every distinct top-level EVT.* key in the file, excluding the
    illustrative EVT.YYYY.MM.DD.XX template block (not a real event —
    _is_template_event_id filters it at parse time)."""
    import re
    blocks = re.findall(r'```yaml\n(.*?)\n```', text, re.DOTALL)
    keys: set[str] = set()
    for b in blocks:
        keys.update(re.findall(r'^(EVT\.\S+):\s*$', b, re.MULTILINE))
    return {k for k in keys if not _is_template_event_id(k)}


def test_real_lel_file_recovers_every_real_evt_event_with_date_and_category():
    assert _LEL_MARKDOWN_PATH.exists(), (
        f"LEL markdown not found at resolved path {_LEL_MARKDOWN_PATH}"
    )
    text = _LEL_MARKDOWN_PATH.read_text(encoding="utf-8")
    expected_ids = _real_evt_keys(text)
    assert expected_ids, "expected at least one real EVT.* key in the LEL file"

    events, _sha = _parse_lel_markdown(_LEL_MARKDOWN_PATH)
    parsed_ids = {e["event_id"] for e in events}

    missing = expected_ids - parsed_ids
    assert not missing, f"real EVT events dropped by the parser: {sorted(missing)}"
    extra = parsed_ids - expected_ids
    assert not extra, f"spurious non-event entries leaked into parsed events: {sorted(extra)}"

    missing_date = [e["event_id"] for e in events if not e.get("date")]
    missing_category = [e["event_id"] for e in events if not e.get("category")]
    assert not missing_date, f"events missing date: {missing_date}"
    assert not missing_category, f"events missing category: {missing_category}"
