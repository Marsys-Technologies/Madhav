from services.kala_core.promise import (
    Attachment, Conclusion, Defeat, EffectiveState, FactState, Mechanism,
    MechanismRoute, PromiseGraph, PromiseNode,
)


def graph():
    result = PromiseGraph()
    result.add_node(PromiseNode("graha:Ju", "graha", ("ga.graha.jupiter",)))
    result.add_mechanism(Mechanism("m:career", MechanismRoute.ADMITTED, "career", ("graha:Ju",), ("ga.graha.jupiter",), "L0:R-1"))
    result.conclusions["c:career"] = Conclusion("c:career", "m:career", FactState.PRESENT, ("ga.graha.jupiter",))
    return result


def test_fact_removal_changes_admitted_graph_state_but_attachment_removal_does_not():
    subject = graph()
    subject.attach(Attachment("msr:1", "m:career", "MSR"))
    assert subject.fact_state("m:career", {"ga.graha.jupiter"}) is FactState.PRESENT
    assert subject.attachments_for("m:career") == (Attachment("msr:1", "m:career", "MSR"),)
    assert subject.fact_state("m:career", set()) is FactState.MISSING_FACT
    subject.attachments.clear()
    assert subject.fact_state("m:career", {"ga.graha.jupiter"}) is FactState.PRESENT


def test_defeat_alters_only_its_target_conclusion_and_keeps_formation_present():
    subject = graph()
    subject.conclusions["c:other"] = Conclusion("c:other", "m:career", FactState.PRESENT, ("ga.graha.jupiter",))
    subject.defeats.append(Defeat("c:career", ("ga.graha.jupiter",), "L0:R-2"))
    assert subject.effective_state("c:career", {"ga.graha.jupiter"}) is EffectiveState.DEFEATED
    assert subject.effective_state("c:other", {"ga.graha.jupiter"}) is EffectiveState.IN_FORCE
    assert subject.nodes["graha:Ju"].fact_ids == ("ga.graha.jupiter",)


def test_node_without_l1_fact_reference_is_rejected():
    try:
        PromiseNode("graha:Ju", "graha", ())
    except ValueError as error:
        assert "fact ids" in str(error)
    else:
        raise AssertionError("a node without a fact reference must fail")
