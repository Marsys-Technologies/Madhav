"""test_n430_retired_sarvatobhadra_dag.py -- SS ruling N-430 / migration 1360 (retire the unbuilt bg_sarvatobhadra_grid).

What the census does with the retired asset and with ka_vedha_gochara's edge to it, measured with the census's own functions (offline, no database):

  * Build.dag `exists` clause: "every depends_on entry is an ACTIVE registry asset". With the edge KEPT and the grid inactive the clause FAILs for
    ka_vedha_gochara (the reason migration 1360 removes the edge); with the edge removed it PASSes.
  * Build.dag reads-match clause: table owners are the active WRITER-BACKED assets (`build_table_owners`); the grid has no writer, so the table the
    ka_vedha_gochara writer still reads has no owner and cannot be reported as a missing edge, before or after the retirement.
  * Population: `is_active AND NOT dead_flag` excludes the retired row, so the census reads it as excluded_inactive.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

GRID = "bg_sarvatobhadra_grid"
VEDHA = "ka_vedha_gochara"
KEPT = ["ga_positions", "bg_ephemeris", "bg_transit_rules", GRID, "bg_vedha_malefic_scale", "bg_phaladeepika_latta"]
REMOVED = [d for d in KEPT if d != GRID]
ACTIVE = [d for d in REMOVED] + [VEDHA]                     # the grid is inactive after migration 1360: not in the active graph, not in `known`


def _reg(deps):
    return dict(asset_id=VEDHA, has_writer=True, target_table="kala_vedha_gochara", count_sql="SELECT COUNT(*) FROM kala_vedha_gochara WHERE chart_id=$1",
                depends_on=list(deps))


def _dag(deps):
    graph = {a: [] for a in ACTIVE}
    return ac._measure_dag(VEDHA, _reg(deps), [], set(ACTIVE), "ka_", lambda: {}, graph)


def test_exists_clause_fails_when_the_edge_to_the_inactive_grid_is_kept():
    got = _dag(KEPT)
    assert got["v"] == ac.FAIL
    assert f"exists: depends_on references unknown or inactive assets: ['{GRID}']" in got["measured"], got["measured"]


def test_exists_clause_passes_when_the_edge_is_removed():
    got = _dag(REMOVED)
    assert "exists: all 5 are active registry assets (every layer)" in got["measured"], got["measured"]
    assert "unknown or inactive" not in got["measured"]


def test_a_no_writer_grid_owns_no_table_so_its_read_is_never_a_missing_edge():
    rows = [(VEDHA, "kala_vedha_gochara", "SELECT COUNT(*) FROM kala_vedha_gochara WHERE chart_id=$1", True),
            (GRID, GRID, "SELECT COUNT(*) FROM bg_sarvatobhadra_grid", False)]
    owners = ac.build_table_owners(rows)
    assert GRID not in owners and owners == {"kala_vedha_gochara": [VEDHA]}


def test_the_retired_row_is_outside_the_census_population_filter():
    # the filter text is the census's own (produced_table_owners / registry population): `is_active AND NOT coalesce(dead_flag,false)`
    src = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    assert "WHERE is_active AND NOT coalesce(dead_flag,false)" in src


def test_a_declaration_for_the_retired_grid_is_refused_by_the_schema_validator_on_a_full_census_run():
    """UNKNOWN RESOLVED for migration 1360: a declaration for an INACTIVE asset trips `validate_declarations`.

    A full census run validates the declarations file against the ids of the census's measured (active) assets, and an id outside that set raises
    DeclarationsError("asset id is not in the census registry set"). Once 1360 has retired the grid, `excluded_inactive` is not in that set, so the
    grid's entry in asset_declarations.json (Engine's file, not edited here) must be dropped, or the validator taught to accept excluded_inactive ids,
    BEFORE the next live full-registry census/rollup. This test pins the mechanism while the entry exists and passes once Engine has removed it."""
    decl = ac.load_asset_declarations()                       # the committed file against no registry set: loads
    active_after_1360 = set(decl) - {GRID}
    if GRID in decl:
        try:
            ac.load_asset_declarations(registry_ids=active_after_1360)
        except ac.DeclarationsError as exc:
            assert f"assets['{GRID}']: asset id is not in the census registry set" in str(exc)
        else:
            raise AssertionError("expected DeclarationsError for the declared-but-inactive grid")
    else:
        assert ac.load_asset_declarations(registry_ids=active_after_1360) is not None
