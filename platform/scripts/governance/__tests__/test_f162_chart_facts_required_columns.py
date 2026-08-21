"""test_f162_chart_facts_required_columns.py — F-162 prove-it-can-fail gate.

F-162: check_chart_facts_schema() read `schema.get("columns", [])` against
CHART_FACTS_SCHEMA.json, a file that has never carried a "columns" key (it is a
category/fact_key taxonomy, not a column contract). `declared_columns` was therefore
always an empty set, so the check always took the always-taken "schema_file_empty"
early return and NEVER reached live-DB comparison. The entire HIGH
"chart_facts_column_missing" class had never once executed — a CLAUDE.md §N.8
gate-that-cannot-fail defect.

Fix: the column contract now lives as REQUIRED_CHART_FACTS_COLUMNS (a short,
explicitly-declared, DB-verified constant), checked directly against
`_query_live_chart_facts_columns()` (psql / information_schema) — no second
hand-maintained registry.

These tests prove the fixed check CAN fail (mutation-checked: reverting the fix — i.e.
reintroducing the old `declared_columns` early return — makes
`test_missing_required_column_is_a_high_finding` fail, because the check would never
reach the point of comparing against a live/injected column set at all).

Run:
  python -m pytest platform/scripts/governance/__tests__/test_f162_chart_facts_required_columns.py -v
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import drift_detector  # noqa: E402


REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
REAL_SCHEMA_PATH = REPO_ROOT / "platform/scripts/governance/CHART_FACTS_SCHEMA.json"


# ── Sanity on the module constant itself ─────────────────────────────────────

def test_required_columns_constant_exists_and_is_nonempty():
    assert isinstance(drift_detector.REQUIRED_CHART_FACTS_COLUMNS, frozenset)
    assert len(drift_detector.REQUIRED_CHART_FACTS_COLUMNS) > 0


def test_computed_at_iso_not_resurrected():
    """The old dead B-series check named 'computed_at_iso' as required, but that
    column does not exist on the real table (the real column is 'computed_at').
    F-162's own plan text says explicitly: do not resurrect it."""
    assert "computed_at_iso" not in drift_detector.REQUIRED_CHART_FACTS_COLUMNS


def test_real_schema_file_has_no_columns_key():
    """Documents the root cause: CHART_FACTS_SCHEMA.json is a taxonomy, not a column
    contract, and the fixed check must not depend on a 'columns' key existing."""
    if not REAL_SCHEMA_PATH.exists():
        pytest.skip("CHART_FACTS_SCHEMA.json not found in this checkout")
    schema = json.loads(REAL_SCHEMA_PATH.read_text(encoding="utf-8"))
    assert "columns" not in schema
    assert "categories" in schema and "channels" in schema


# ── The can-fail proof ───────────────────────────────────────────────────────

def test_missing_required_column_is_a_high_finding(monkeypatch, tmp_path):
    """THE load-bearing test. Inject a live-column set missing one required column
    and assert the check emits a HIGH chart_facts_column_missing finding naming it.

    Mutation-check: reverting check_chart_facts_schema() to the old
    `declared_columns = {col["name"] for col in schema.get("columns", [])}` shape
    makes this test fail — that code path always hits the always-empty-declared-
    columns branch and returns a MEDIUM 'schema_file_empty' finding instead, never
    calling _query_live_chart_facts_columns() at all, so this monkeypatch would never
    even be consulted.
    """
    schema_path = tmp_path / "CHART_FACTS_SCHEMA.json"
    schema_path.write_text(json.dumps({
        "schema_version": "1.0", "categories": {}, "channels": {},
    }), encoding="utf-8")
    monkeypatch.setattr(
        drift_detector, "REQUIRED_CHART_FACTS_COLUMNS",
        frozenset({"chart_id", "fact_id", "ayanamsha_id"}),
    )

    fake_live_columns = {"chart_id", "fact_id"}  # missing 'ayanamsha_id'
    monkeypatch.setattr(
        drift_detector, "_query_live_chart_facts_columns",
        lambda: (fake_live_columns, None),
    )

    # Redirect the repo_root the check computes schema_path from, by placing our
    # fixture at the exact relative path the check expects.
    fixture_repo_root = tmp_path
    gov_dir = fixture_repo_root / "platform" / "scripts" / "governance"
    gov_dir.mkdir(parents=True, exist_ok=True)
    (gov_dir / "CHART_FACTS_SCHEMA.json").write_text(schema_path.read_text(encoding="utf-8"), encoding="utf-8")

    findings = drift_detector.check_chart_facts_schema(fixture_repo_root)

    missing_findings = [f for f in findings if f.cls == "chart_facts_column_missing"]
    assert len(missing_findings) == 1, (
        f"Expected exactly one chart_facts_column_missing finding, got: {findings}"
    )
    assert missing_findings[0].severity == "HIGH"
    assert "ayanamsha_id" in missing_findings[0].evidence


def test_all_required_columns_present_yields_no_missing_finding(monkeypatch, tmp_path):
    """Positive control: when the injected live-column set is a superset of
    REQUIRED_CHART_FACTS_COLUMNS, no chart_facts_column_missing finding is emitted."""
    gov_dir = tmp_path / "platform" / "scripts" / "governance"
    gov_dir.mkdir(parents=True, exist_ok=True)
    (gov_dir / "CHART_FACTS_SCHEMA.json").write_text(
        json.dumps({"schema_version": "1.0", "categories": {}, "channels": {}}),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        drift_detector, "REQUIRED_CHART_FACTS_COLUMNS",
        frozenset({"chart_id", "fact_id"}),
    )
    monkeypatch.setattr(
        drift_detector, "_query_live_chart_facts_columns",
        lambda: ({"chart_id", "fact_id", "some_other_column"}, None),
    )

    findings = drift_detector.check_chart_facts_schema(tmp_path)
    assert not [f for f in findings if f.cls == "chart_facts_column_missing"]


def test_db_unreachable_still_degrades_to_low_not_a_false_pass(monkeypatch, tmp_path):
    """The psql-absent / DB-down degradation path must still be honest: LOW finding,
    not a silent PASS and not a HIGH false positive."""
    gov_dir = tmp_path / "platform" / "scripts" / "governance"
    gov_dir.mkdir(parents=True, exist_ok=True)
    (gov_dir / "CHART_FACTS_SCHEMA.json").write_text(
        json.dumps({"schema_version": "1.0", "categories": {}, "channels": {}}),
        encoding="utf-8",
    )

    unreachable = drift_detector.Finding(
        cls="schema_db_unreachable", severity="LOW", canonical_id=None,
        surfaces_involved=["platform/scripts/governance/CHART_FACTS_SCHEMA.json"],
        evidence="psql not found on PATH — skipping live column verification",
        suggested_remediation="Install postgresql-client to enable live schema checks",
    )
    monkeypatch.setattr(
        drift_detector, "_query_live_chart_facts_columns",
        lambda: (None, unreachable),
    )

    findings = drift_detector.check_chart_facts_schema(tmp_path)
    assert len(findings) == 1
    assert findings[0].cls == "schema_db_unreachable"
    assert findings[0].severity == "LOW"


def test_missing_schema_file_is_high():
    findings = drift_detector.check_chart_facts_schema(pathlib.Path("/nonexistent/repo/root/xyz"))
    assert len(findings) == 1
    assert findings[0].cls == "schema_file_missing"
    assert findings[0].severity == "HIGH"


# ── Live-DB integration proof (ruled: "a one-time recorded pass... against the live
# schema"). Skips honestly if the DB/psql are not reachable in this environment. ────

def test_live_db_query_helper_reaches_real_chart_facts():
    """Not mocked: actually invoke _query_live_chart_facts_columns() against
    whatever DB this environment has configured (or skip honestly if unreachable),
    to record a real pass/fail rather than only a monkeypatched one."""
    columns, unreachable = drift_detector._query_live_chart_facts_columns()
    if unreachable is not None:
        pytest.skip(f"DB/psql unreachable in this environment: {unreachable.evidence}")
    assert columns is not None
    # The columns confirmed live against production during F-162 triage (2026-08-22):
    for expected in drift_detector.REQUIRED_CHART_FACTS_COLUMNS:
        assert expected in columns, (
            f"REQUIRED_CHART_FACTS_COLUMNS names '{expected}' but it is absent from "
            f"the live chart_facts table this test actually queried."
        )
