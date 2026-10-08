"""K2-1b additive candidate-partition contracts for the Yojaka promise graph."""
from pathlib import Path


ROOT = Path(__file__).parents[2]
WRITER = ROOT / "pipeline/orchestrator/writers/ka_yojaka.py"
MIGRATION = ROOT.parent / "migrations/1335_k2_1b_promise_graph_columns.sql"
SANGAM_READER = ROOT / "pipeline/orchestrator/writers/ka_sangam.py"
KALASUTRA_READER = ROOT / "pipeline/orchestrator/writers/ka_kalasutra.py"


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


def test_candidate_generation_is_part_of_the_predicate_identity():
    sql = MIGRATION.read_text()
    assert "(chart_id, signal_id, ayanamsha_id, generation)" in sql


def test_yojaka_refuses_legacy_as_a_candidate_generation():
    source = WRITER.read_text()
    assert "candidate_generation == 'legacy'" in source


def test_downstream_readers_exclude_candidate_partitions():
    for reader in (SANGAM_READER, KALASUTRA_READER):
        assert "generation NOT LIKE 'candidate:%'" in reader.read_text()
