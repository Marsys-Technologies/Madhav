"""K2-1b promise-graph contracts owned by the Yojaka test surface."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from services.kala_core.promise import (
    Conclusion,
    Defeat,
    FactState,
    Mechanism,
    MechanismRoute,
    PromiseGraph,
    PromiseNode,
)


FACT_ID = "ga.graha.jupiter"
ROOT = Path(__file__).parents[3]
WRITER = ROOT / "pipeline/orchestrator/writers/ka_yojaka.py"
MIGRATION = ROOT.parent / "migrations/1339_k2_1b_promise_graph_columns.sql"


@pytest.mark.parametrize("entry_point", ["run", "run_substep"])
def test_dry_run_requires_no_build_inputs_or_database(entry_point):
    from pipeline.orchestrator.writers import SubStep
    from pipeline.orchestrator.writers.ka_yojaka import KaYojakaWriter

    # Missing config/build_id/db_conn catches any input access before refusal
    # to write; both the whole-asset and class entry points must remain inert.
    ctx = SimpleNamespace(dry_run=True)
    writer = KaYojakaWriter()
    result = (writer.run(ctx) if entry_point == "run" else
              writer.run_substep(ctx, SubStep("class:unqualified")))
    assert result.rows_inserted == 0
    assert result.notes == "dry_run=True"


def _graph() -> PromiseGraph:
    graph = PromiseGraph()
    graph.add_node(PromiseNode("graha:Ju", "graha", (FACT_ID,)))
    graph.add_mechanism(
        Mechanism("m:admitted", MechanismRoute.ADMITTED, "career_change", ("graha:Ju",), (FACT_ID,), "L0:R-1")
    )
    graph.add_mechanism(
        Mechanism("m:testimony", MechanismRoute.TESTIMONY, "career_change", ("graha:Ju",), (), "L2:MSR-1")
    )
    graph.add_conclusion(Conclusion("c:career", "m:admitted", FactState.PRESENT, (FACT_ID,)))
    return graph


def test_typed_defeat_and_exception_target_one_registered_conclusion():
    graph = _graph()
    graph.add_defeat(Defeat("c:career", (FACT_ID,), "L0:bhanga", "defeats"))
    graph.add_defeat(Defeat("c:career", (FACT_ID,), "L0:apavada", "excepts"))

    assert [item.kind for item in graph.defeats] == ["defeats", "excepts"]
    with pytest.raises(ValueError, match="unknown conclusion"):
        graph.add_defeat(Defeat("c:missing", (FACT_ID,), "L0:bhanga"))


def test_candidate_conclusion_accepts_both_declared_mechanism_routes():
    graph = _graph()
    conclusion = Conclusion("c:testimony", "m:testimony", FactState.PRESENT, ())
    graph.add_conclusion(conclusion)

    assert graph.conclusions[conclusion.conclusion_id] is conclusion


def test_candidate_generation_is_additive_and_never_deletes_legacy_rows():
    sql = MIGRATION.read_text()
    writer = WRITER.read_text()

    assert "ADD COLUMN IF NOT EXISTS generation" in sql
    assert "(chart_id, signal_id, ayanamsha_id, generation)" in sql
    assert "WHERE chart_id = %s AND generation = %s" in writer
    assert '"DELETE FROM kala_activation_predicates WHERE chart_id = %s"' not in writer
