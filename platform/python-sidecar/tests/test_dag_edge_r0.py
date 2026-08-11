"""
Smoke test: ka_kshetra DAG edge fix — migration 569 (SAMPŪRTI R0, RB-1).

Verifies that migration 569 correctly removes the retired ka_gochara_sweep
dependency edge from ka_kshetra. ka_gochara_sweep was RETIRED by migration 563
(W6.4 UTK-R2, PARISHKARA); its 'stale' throughput row deadlocks every
ka_kshetra dispatch at preflight. This migration drops the edge so dispatches
can proceed.
"""


def test_migration_569_removes_retired_gochara_sweep_dep_from_kshetra():
    """
    The migration SQL must use array_remove to drop ka_gochara_sweep from
    ka_kshetra.depends_on. Verify the SQL text contains the correct terms.
    """
    import pathlib
    migration = pathlib.Path("platform/migrations/569_sampurti_r0_kshetra_dep_fix.sql")
    assert migration.exists(), (
        "Migration 569 not found — R0 gate packet not yet committed. "
        "Run from the repository root."
    )
    content = migration.read_text()
    assert "ka_gochara_sweep" in content, "Migration must reference ka_gochara_sweep"
    assert "ka_kshetra" in content, "Migration must scope to ka_kshetra"
    assert "array_remove" in content, "Migration must use array_remove to drop the edge"
    assert "depends_on" in content, "Migration must update depends_on column"


def test_seed_does_not_declare_gochara_sweep_dep_for_kshetra():
    """
    The asset_registry_seed.ts must not declare ka_gochara_sweep in
    ka_kshetra's depends_on. A stale seed re-inserts the retired edge on
    every runSeed() call, undoing migration 569's fix.
    """
    import pathlib, re
    seed = pathlib.Path("platform/scripts/seed/asset_registry_seed.ts")
    assert seed.exists(), "Seed file not found — run from repo root"
    content = seed.read_text()
    # Find the ka_kshetra block's depends_on array
    # Look for asset_id: 'ka_kshetra' then the depends_on array that follows
    kshetra_block_match = re.search(
        r"asset_id:\s*'ka_kshetra'.*?depends_on:\s*\[(.*?)\]",
        content,
        re.DOTALL,
    )
    assert kshetra_block_match, "ka_kshetra block with depends_on not found in seed"
    deps_text = kshetra_block_match.group(1)
    assert "ka_gochara_sweep" not in deps_text, (
        "ka_gochara_sweep must not appear in ka_kshetra's seed depends_on "
        "(RETIRED by mig-563; removed from DAG by mig-569)"
    )
