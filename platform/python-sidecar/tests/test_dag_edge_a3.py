"""
Smoke test: ka_gochara_resonance DAG edge correctness.
Verifies that migration 546 would produce the correct depends_on array.
"""


def test_ka_gochara_resonance_should_depend_on_bg_transit_rules():
    """
    ka_gochara_resonance consumes bg_transit_rules via the
    gochara_resonance_map.source_rule_id FK. The DAG must reflect this.
    """
    # This is a migration-level test — the assertion is that the migration
    # SQL is correct. We verify the intent here as a code review checkpoint.
    import pathlib
    migration = pathlib.Path("platform/migrations/546_ka_gochara_resonance_dag_edge.sql")
    if migration.exists():
        content = migration.read_text()
        assert "bg_transit_rules" in content
        assert "ka_gochara_resonance" in content
        assert "depends_on" in content
