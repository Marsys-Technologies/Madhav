from __future__ import annotations

from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.bg_ghatana import GhatanaWriter


def test_writer_reports_all_rows_written_across_both_owned_tables(monkeypatch):
    """Dropping activity rows from telemetry must fail this co-writer contract."""
    monkeypatch.setattr(
        "pipeline.orchestrator.writers.bg_ghatana.seed_ghatana",
        lambda *_args, **_kwargs: {
            "brahma_event_ontology": 27,
            "brahma_activity_ontology": 12,
        },
    )

    result = GhatanaWriter().run(ContextSpec(
        asset_id="bg_ghatana",
        build_id="co-writer-count",
        db_conn=object(),
    ))

    assert result.rows_inserted == 39
    assert "27 events" in result.notes
    assert "12 activities" in result.notes
