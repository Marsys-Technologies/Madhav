"""
test_ph_sodhana_engine.py — Regression test for the ph_sodhana UUID-serialization defect.

Bug: detect_confidence_degenerate() (added in 4d4f3adc, chart-wide
confidence_degenerate detector) embedded ctx.chart_id raw into
derivation_ledger_jsonb. When chart_id arrives as a uuid.UUID object
(as it does in production — psycopg returns uuid.UUID for a `uuid` column),
json.dumps(rec.derivation_ledger_jsonb) in ph_sodhana.py raises
TypeError: Object of type UUID is not JSON serializable, which aborts
ph_sodhana and cascades the orchestrator's upstream-success gate to block
ph_suddha_sodhana, ph_pramana, and ph_phaladesa — 4 of 9 ph_* assets never
run on an otherwise-healthy L4 Phala rebuild.

No live DB connection required.
"""
from __future__ import annotations

import json
import uuid

from services.ph_sodhana.engine import AnchorRow, SodhanaContext, derive_sodhana_flags


def _make_anchor(anchor_id: str, confidence_high: float) -> AnchorRow:
    return AnchorRow(
        anchor_id=anchor_id,
        anchor_source="ph_nimitta",
        domain="career",
        confidence_high=confidence_high,
        confidence_basis="structural_not_yet_empirical",
        falsifier="some falsifier text",
        derivation_ledger_jsonb={"anchor_source": "ph_nimitta"},
    )


def test_confidence_degenerate_ledger_is_json_serializable_with_uuid_chart_id():
    """chart_id as a real uuid.UUID (the production shape) must not crash json.dumps."""
    chart_id = uuid.UUID("482012f1-710e-4a25-994a-93821f5871aa")
    anchors = [_make_anchor(f"PH-4-1.A{i}", 0.75) for i in range(6)]
    ctx = SodhanaContext(chart_id=chart_id, anchors=anchors)

    flags = derive_sodhana_flags(ctx)

    degenerate = [f for f in flags if f.anomaly_type == "confidence_degenerate"]
    assert len(degenerate) == 1

    # This is the exact call ph_sodhana.py:85 makes against the writer's DB cursor.
    json.dumps(degenerate[0].derivation_ledger_jsonb)
