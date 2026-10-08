import pytest

from services.kala_core.promise import (
    AttachmentInput, AttachmentSource, Conclusion, Defeat, EdgePolarity,
    EffectiveState, FactState, Mechanism, MechanismRoute, PromiseEdge,
    PromiseGraph, PromiseNode, attachment_input_from_mapping,
    load_l2_attachments,
)


FACT_ID = "ga.graha.jupiter"


def graph():
    result = PromiseGraph()
    result.add_node(PromiseNode("graha:Ju", "graha", (FACT_ID,)))
    result.add_mechanism(Mechanism("m:career", MechanismRoute.ADMITTED, "career_change", ("graha:Ju",), (FACT_ID,), "L0:R-1"))
    result.conclusions["c:career"] = Conclusion("c:career", "m:career", FactState.PRESENT, (FACT_ID,))
    return result


def test_fact_removal_is_missing_fact_but_an_evaluated_empty_attachment_is_distinct():
    subject = graph()
    loaded = load_l2_attachments("m:career", (AttachmentInput("msr:1", AttachmentSource.MSR, (FACT_ID,), evaluated_empty=True),), {FACT_ID})
    assert loaded[0].state is FactState.EVALUATED_EMPTY
    assert subject.fact_state("m:career", {FACT_ID}) is FactState.PRESENT
    assert subject.fact_state("m:career", set()) is FactState.MISSING_FACT


def test_attachment_missing_fact_is_not_evaluated_empty():
    attachment = load_l2_attachments("m:career", (AttachmentInput("cgm:1", AttachmentSource.CGM, (FACT_ID,), evaluated_empty=True),), set())[0]
    assert attachment.state is FactState.MISSING_FACT


def test_loader_accepts_only_msr_cgm_and_pratijna_sources():
    attachments = load_l2_attachments("m:career", (
        AttachmentInput("msr:1", AttachmentSource.MSR, (FACT_ID,)),
        AttachmentInput("cgm:1", AttachmentSource.CGM, (FACT_ID,)),
        AttachmentInput("pratijna:1", AttachmentSource.PRATIJNA, (FACT_ID,)),
    ), {FACT_ID})
    assert [item.source for item in attachments] == [AttachmentSource.MSR, AttachmentSource.CGM, AttachmentSource.PRATIJNA]


def test_l2_attachment_restatement_mutation_is_rejected():
    with pytest.raises(ValueError, match="may not restate values"):
        attachment_input_from_mapping({"attachment_id": "msr:1", "source": "MSR", "fact_ids": [FACT_ID], "value": "Jupiter"})


def test_every_node_reference_must_resolve_in_chart_facts():
    subject = graph()
    subject.validate_node_facts({FACT_ID})
    with pytest.raises(ValueError, match="do not resolve"):
        subject.validate_node_facts(set())


def test_signed_edges_require_known_nodes_and_keep_frame_and_provenance():
    subject = graph()
    edge = PromiseEdge("graha:Ju", "graha:Ju", "governs", EdgePolarity.SUPPORTS, "natal", "L0:R-1", "1", "L0")
    subject.add_edge(edge)
    assert subject.edges == [edge]
    with pytest.raises(ValueError, match="unknown node"):
        subject.add_edge(PromiseEdge("missing", "graha:Ju", "governs", EdgePolarity.OPPOSES, "natal", "L0:R-1", "1", "L0"))


def test_event_class_must_be_from_the_single_ontology_roster():
    subject = PromiseGraph()
    subject.add_node(PromiseNode("graha:Ju", "graha", (FACT_ID,)))
    with pytest.raises(ValueError, match="canonical ontology roster"):
        subject.add_mechanism(Mechanism("m:invented", MechanismRoute.ADMITTED, "invented", ("graha:Ju",), (FACT_ID,), "L0:R-1"))


def test_defeat_alters_only_its_target_conclusion_and_keeps_formation_present():
    subject = graph()
    subject.conclusions["c:other"] = Conclusion("c:other", "m:career", FactState.PRESENT, (FACT_ID,))
    subject.defeats.append(Defeat("c:career", (FACT_ID,), "L0:R-2"))
    assert subject.effective_state("c:career", {FACT_ID}) is EffectiveState.DEFEATED
    assert subject.effective_state("c:other", {FACT_ID}) is EffectiveState.IN_FORCE


def test_typed_defeat_and_exception_are_registered_only_against_known_conclusions():
    """K2-1b: the formation survives, while rule-targeted conclusions change state."""
    subject = graph()
    subject.add_defeat(Defeat("c:career", (FACT_ID,), "L0:bhanga", "defeats"))
    subject.add_defeat(Defeat("c:career", (FACT_ID,), "L0:apavada", "excepts"))

    assert [item.kind for item in subject.defeats] == ["defeats", "excepts"]
    assert subject.effective_state("c:career", {FACT_ID}) is EffectiveState.DEFEATED
    with pytest.raises(ValueError, match="unknown conclusion"):
        subject.add_defeat(Defeat("c:missing", (FACT_ID,), "L0:bhanga"))


def test_candidate_conclusion_requires_a_known_admitted_or_testimony_mechanism():
    subject = graph()
    conclusion = Conclusion("c:route", "m:career", FactState.PRESENT, (FACT_ID,))
    subject.add_conclusion(conclusion)

    assert subject.conclusions[conclusion.conclusion_id] is conclusion
    with pytest.raises(ValueError, match="unknown mechanism"):
        subject.add_conclusion(Conclusion("c:bad", "m:missing", FactState.PRESENT, (FACT_ID,)))
