"""
test_l5_bigquery_export_disabled.py — brahmagyan.mimamsa.l5_bigquery_export must be
an inert refusing stub (SS N-109 / lifeevents-audit F1b).

The old module built `mimamsa_events` rows with the people-entered free-text
`description` (plus event ids/dates/outcomes) from the in-source corpus and sent
them to BigQuery or a local JSONL file. These tests pin that it can no longer do
either, with synthetic inputs only (no DB, no GCP, no real event content).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

CHART_ID = "00000000-0000-0000-0000-000000000001"  # synthetic
MODULE_PATH = (
    Path(__file__).resolve().parent.parent / "brahmagyan" / "mimamsa" / "l5_bigquery_export.py"
)


@pytest.fixture(autouse=True)
def _no_egress_even_if_module_regresses(monkeypatch):
    """Safety net: if the stub ever regresses to the old exporter, these tests must
    still be unable to reach BigQuery/GCS or write a file (no ADC use, no network)."""
    monkeypatch.setitem(sys.modules, "google.cloud.bigquery", None)  # ImportError on import
    monkeypatch.setitem(sys.modules, "google.cloud.storage", None)

    real_open = Path.open

    def _blocked(*a, **k):
        raise AssertionError("file write attempted by l5_bigquery_export")

    def _open(self, mode="r", *a, **k):
        if any(c in mode for c in "wax+"):
            return _blocked()
        return real_open(self, mode, *a, **k)

    monkeypatch.setattr(Path, "open", _open)
    monkeypatch.setattr(Path, "write_text", _blocked)
    yield


def _mod():
    from brahmagyan.mimamsa import l5_bigquery_export as m

    return m


class TestEveryEntryPointRefuses:
    def test_build_export_payload_refuses(self):
        m = _mod()
        with pytest.raises(m.BigQueryExportDisabled, match="disabled"):
            m.build_export_payload(chart_id=CHART_ID)

    def test_run_export_refuses_in_every_mode(self):
        m = _mod()
        for kwargs in (
            {},
            {"dry_run": True},
            {"force_jsonl": True},
            {"include_multipliers": True},
        ):
            with pytest.raises(m.BigQueryExportDisabled):
                m.run_export(chart_id=CHART_ID, **kwargs)

    def test_export_to_bigquery_refuses_and_never_touches_gcp(self):
        m = _mod()
        fake_bq = MagicMock()
        with patch.dict(sys.modules, {"google.cloud.bigquery": fake_bq, "google.cloud": MagicMock()}):
            with pytest.raises(m.BigQueryExportDisabled):
                m.export_to_bigquery({"mimamsa_events": [{"description": "SYNTHETIC"}]})
        fake_bq.Client.assert_not_called()

    def test_export_to_jsonl_refuses_and_writes_nothing(self, tmp_path):
        m = _mod()
        out = tmp_path / "preview.jsonl"
        with pytest.raises(m.BigQueryExportDisabled):
            m.export_to_jsonl({"mimamsa_events": [{"description": "SYNTHETIC"}]}, output_path=out)
        assert not out.exists()

    def test_cli_exits_nonzero_with_message(self, monkeypatch):
        m = _mod()
        monkeypatch.setattr("sys.argv", ["l5_bigquery_export", "--chart-id", CHART_ID, "--jsonl"])
        with pytest.raises(SystemExit) as exc:
            m.main()
        assert "disabled" in str(exc.value.code)
        assert "people-entered" in str(exc.value.code)

    def test_removed_event_payload_builders_are_gone(self):
        m = _mod()
        for name in (
            "_build_mimamsa_events_payload",
            "_build_chart_state_index_payload",
            "_build_calibration_substrate_payload",
            "_build_multiplier_payload",
            "JSONL_FALLBACK_PATH",
            "GCS_BUCKET",
            "BQ_DATASET",
        ):
            assert not hasattr(m, name), name


class TestSourceIsInert:
    """Static scan: the stub must not be able to read events or reach external services."""

    def _tree(self):
        return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))

    def test_no_event_text_columns_or_payload_keys(self):
        # string-literal dict keys / args only (the docstring legitimately discusses them)
        tree = self._tree()
        literals = {
            n.value
            for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and len(n.value) < 40
        }
        assert "description" not in literals
        assert "mimamsa_events" not in literals
        assert "event_id" not in literals
        assert "calibration_only" not in literals

    def test_no_imports_of_event_corpus_or_cloud_clients(self):
        tree = self._tree()
        imported: set[str] = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                imported.update(a.name for a in n.names)
            elif isinstance(n, ast.ImportFrom):
                imported.add(n.module or "")
        forbidden = ("google", "psycopg", "brahmagyan.mimamsa.l5_lel_intake",
                     "brahmagyan.mimamsa.lel_intake", "brahmagyan.mimamsa.l5_event_chart_state_index",
                     "json", "pathlib", "os")
        for mod in imported:
            assert not any(mod == f or mod.startswith(f + ".") for f in forbidden), mod

    def test_no_file_open_or_write_calls(self):
        tree = self._tree()
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                fn = n.func
                name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
                assert name not in {"open", "write", "write_text", "mkdir", "load_table_from_json",
                                    "load_table_from_uri", "upload_from_string"}, name
