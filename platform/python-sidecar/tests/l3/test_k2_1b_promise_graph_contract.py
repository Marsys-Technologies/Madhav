"""K2-1b additive candidate-partition contracts for the Yojaka promise graph."""
from pathlib import Path


ROOT = Path(__file__).parents[2]
WRITER = ROOT / "pipeline/orchestrator/writers/ka_yojaka.py"
MIGRATION = ROOT.parent / "migrations/1334_k2_1b_promise_graph_columns.sql"


def test_k2_1b_migration_adds_only_promise_graph_columns():
    sql = MIGRATION.read_text()
    assert "ADD COLUMN IF NOT EXISTS generation" in sql
    assert "ADD COLUMN IF NOT EXISTS mechanism_route" in sql
    assert "ADD COLUMN IF NOT EXISTS conclusion_state_jsonb" in sql
    assert "DROP COLUMN" not in sql


def test_yojaka_writer_uses_candidate_generation_without_deleting_legacy_rows():
    source = WRITER.read_text()
    assert "candidate_generation" in source
    assert "WHERE chart_id = %s AND generation = %s" in source
    assert '"DELETE FROM kala_activation_predicates WHERE chart_id = %s"' not in source
