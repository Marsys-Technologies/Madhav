"""
test_mi_jivanaghatana.py — LEL markdown raw-field fallback parser (A6, BA
Pre-Rebuild Gate, 2026-07-05) + native-contamination gate / graceful-empty
build (BA-P3 FIX 1, 2026-07-05).

DB-free tests for pipeline.orchestrator.writers.mi_jivanaghatana's LEL
markdown parser. Covers the recurring failure mode: narrative prose fields
(description / native_reflection / notes) contain unquoted colons that break
strict YAML block-mapping, even though this writer never reads those fields.
The fallback recovers the event via its consumed top-level fields (date,
category, subcategory, magnitude, ...) as raw uninterpreted strings.
"""
from __future__ import annotations

import logging

import pytest

from pipeline.orchestrator.writers.mi_jivanaghatana import (
    NATIVE_CHART_ID,
    MiJivanaghatanaWriter,
    _is_template_event_id,
    _parse_block_raw,
    _parse_lel_markdown,
    _LEL_MARKDOWN_PATH,
)

NON_NATIVE_CHART_ID = "1c826d5a-0000-4000-8000-000000000000"

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


# ── BA-P3 FIX 1: native-contamination gate + graceful empty ──────────────────

class _FakeCursor:
    """Answers the life_events queries run() issues, incl. the presence COUNT.

    `count` overrides the reported chart-scoped count (defaults to the number of
    source rows). It can be set independently to exercise the defensive
    anti-masking guard (count > 0 while the source read returns 0)."""
    def __init__(self, life_events_rows, count=None):
        self._life_events_rows = life_events_rows
        self._count = count if count is not None else len(life_events_rows)
        self._result = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if "information_schema.columns" in s:
            self._result = [{"column_name": "chart_id"}, {"column_name": "event_id"}]
        elif "COUNT(*)" in s.upper():
            self._result = [(self._count,)]
        elif "FROM life_events WHERE chart_id" in s:
            self._result = list(self._life_events_rows)
        else:
            self._result = []

    def fetchall(self):
        return list(self._result)

    def fetchone(self):
        return self._result[0] if self._result else None

    def executemany(self, sql, params_list):
        self._result = []


class _FakeConn:
    def __init__(self, life_events_rows=(), count=None):
        self._life_events_rows = list(life_events_rows)
        self._count = count

    def cursor(self, row_factory=None):
        return _FakeCursor(self._life_events_rows, self._count)


class _FakeCtx:
    def __init__(self, chart_id, db_conn, dry_run=False):
        self.config = {"chart_id": chart_id}
        self.db_conn = db_conn
        self.dry_run = dry_run


def test_non_native_chart_never_opens_native_markdown_builds_zero_success(monkeypatch, tmp_path):
    md = tmp_path / "LEL.md"
    md.write_text(f"```yaml\n{WELL_FORMED_BLOCK}\n```\n", encoding="utf-8")
    monkeypatch.setattr(
        "pipeline.orchestrator.writers.mi_jivanaghatana._LEL_MARKDOWN_PATH", md
    )

    def _boom(path):
        raise AssertionError("non-native chart must never parse the native LEL markdown")

    monkeypatch.setattr(
        "pipeline.orchestrator.writers.mi_jivanaghatana._parse_lel_markdown", _boom
    )

    writer = MiJivanaghatanaWriter()
    ctx = _FakeCtx(NON_NATIVE_CHART_ID, _FakeConn(life_events_rows=[]))
    result = writer.run(ctx)

    assert result.rows_inserted == 0


def test_zero_event_chart_is_success_not_exception(monkeypatch, tmp_path):
    missing_md = tmp_path / "does_not_exist.md"
    monkeypatch.setattr(
        "pipeline.orchestrator.writers.mi_jivanaghatana._LEL_MARKDOWN_PATH", missing_md
    )

    writer = MiJivanaghatanaWriter()
    ctx = _FakeCtx(NON_NATIVE_CHART_ID, _FakeConn(life_events_rows=[]))
    result = writer.run(ctx)

    assert result.rows_inserted == 0
    assert "zero provenance rows" in result.notes


def test_native_chart_with_file_present_still_ingests_events(monkeypatch, tmp_path):
    md = tmp_path / "LEL.md"
    md.write_text(f"```yaml\n{WELL_FORMED_BLOCK}\n```\n", encoding="utf-8")
    monkeypatch.setattr(
        "pipeline.orchestrator.writers.mi_jivanaghatana._LEL_MARKDOWN_PATH", md
    )
    monkeypatch.setattr(
        "pipeline.orchestrator.writers.mi_jivanaghatana._lookup_event_class",
        lambda conn, category, subcategory: None,
    )

    writer = MiJivanaghatanaWriter()
    ctx = _FakeCtx(NATIVE_CHART_ID, _FakeConn(life_events_rows=[]))
    result = writer.run(ctx)

    assert result.rows_inserted == 1


def test_genuinely_empty_chart_is_healthy_no_warning(monkeypatch, tmp_path, caplog):
    """BA-P4 R2.2/W2.2 presence-branching: a chart with ZERO life_events rows
    (count 0) and no markdown is a HEALTHY empty build — no anti-masking warning.
    This is the Abhinandan / pre-intake case: structural, not an error."""
    missing_md = tmp_path / "does_not_exist.md"
    monkeypatch.setattr(
        "pipeline.orchestrator.writers.mi_jivanaghatana._LEL_MARKDOWN_PATH", missing_md
    )
    writer = MiJivanaghatanaWriter()
    ctx = _FakeCtx(NATIVE_CHART_ID, _FakeConn(life_events_rows=[], count=0))
    with caplog.at_level(logging.WARNING):
        result = writer.run(ctx)

    assert result.rows_inserted == 0
    assert not any("built ZERO" in rec.message for rec in caplog.records), \
        "a genuinely empty chart must NOT trigger the anti-masking warning"


def test_present_rows_but_zero_build_warns_presence_based(monkeypatch, tmp_path, caplog):
    """Defensive anti-masking (presence, not identity): if a chart's life_events
    count is > 0 but the build sourced zero (a sourcing/packaging bug), warn
    loudly rather than silently succeed. Any chart, not just the native."""
    missing_md = tmp_path / "does_not_exist.md"
    monkeypatch.setattr(
        "pipeline.orchestrator.writers.mi_jivanaghatana._LEL_MARKDOWN_PATH", missing_md
    )
    writer = MiJivanaghatanaWriter()
    # Inconsistent state the guard exists to catch: COUNT says 57, source read []
    ctx = _FakeCtx(NON_NATIVE_CHART_ID, _FakeConn(life_events_rows=[], count=57))
    with caplog.at_level(logging.WARNING):
        result = writer.run(ctx)

    assert result.rows_inserted == 0
    assert any(
        "has 57 life_events rows but" in rec.message and "ZERO" in rec.message
        for rec in caplog.records
    ), "a chart with rows present but a zero build must warn (presence-based anti-masking)"
