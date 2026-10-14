import pytest
from dataclasses import replace

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


@pytest.mark.parametrize('state', [FactState.EVALUATED_EMPTY, FactState.MISSING_FACT])
def test_empty_candidate_never_in_force(state):
    subject = graph()
    subject.conclusions['c:career'] = Conclusion('c:career', 'm:career', state, (FACT_ID,))
    assert subject.effective_state('c:career', {FACT_ID}) is EffectiveState.UNRESOLVED


def test_additional_unknown_defeat_does_not_weaken_full_defeat():
    subject = graph()
    subject.add_defeat(Defeat('c:career', (FACT_ID,), 'full'))
    subject.add_defeat(Defeat('c:career', ('missing',), 'unknown'))
    assert subject.effective_state('c:career', {FACT_ID}) is EffectiveState.DEFEATED


def test_unknown_defeating_evidence_is_unresolved_not_in_force():
    subject = graph()
    subject.add_defeat(Defeat('c:career', ('missing',), 'unknown'))
    assert subject.effective_state('c:career', {FACT_ID}) is EffectiveState.UNRESOLVED


@pytest.mark.parametrize('pattern', ['partial', 'contested'])
def test_partial_or_contested_evidence_reads_unresolved_with_typed_reason(pattern):
    """Ruling 16: promoting the unassessed gate to in_force must fail."""
    subject = graph()
    roots = (FACT_ID, 'ga.graha.saturn')
    subject.add_node(PromiseNode('graha:Sa', 'graha', (roots[1],)))
    subject.add_mechanism(Mechanism('m:pair', MechanismRoute.ADMITTED,
        'career_change', ('graha:Ju', 'graha:Sa'), roots, 'fixture:rule'))
    subject.conclusions['c:career'] = Conclusion('c:career', 'm:pair',
        FactState.PRESENT, roots)
    if pattern == 'partial':
        subject.add_defeat(Defeat('c:career', (FACT_ID,), 'fixture:subset'))
        expected_reason = 'partial_defeat_unassessed'
        expected_conclusions = ('c:career',)
        expected_defeats = ('fixture:subset',)
    else:
        subject.conclusions['c:career'] = replace(subject.conclusions['c:career'],
            target_id='graha:Ju', valence=EdgePolarity.SUPPORTS)
        subject.add_conclusion(Conclusion('c:opposed', 'm:pair', FactState.PRESENT,
            roots, target_id='graha:Ju', valence=EdgePolarity.OPPOSES))
        # All defeat evidence remains visible, even when it is ungrounded.
        subject.add_defeat(Defeat('c:opposed', ('missing',), 'fixture:unknown'))
        expected_reason = 'contestation_unassessed'
        expected_conclusions = ('c:career', 'c:opposed')
        expected_defeats = ('fixture:unknown',)

    for cid in expected_conclusions:
        assert subject.effective_state(cid, iter(roots)) is EffectiveState.UNRESOLVED
        result = subject.effective_result(cid, iter(roots))
        assert result.state is EffectiveState.UNRESOLVED
        assert result.null_reason == expected_reason
        assert result.conclusion_ids == expected_conclusions
        assert result.defeat_ids == expected_defeats
    assert set(subject.conclusions) == set(expected_conclusions)
    assert subject.fact_state('m:pair', roots) is FactState.PRESENT


def test_subset_coverage_keeps_all_defeat_ids_even_with_extra_roots_and_full_defeat():
    subject = graph()
    roots = (FACT_ID, 'ga.graha.saturn')
    subject.conclusions['c:career'] = replace(subject.conclusions['c:career'], fact_ids=roots)
    subject.add_defeat(Defeat('c:career', (FACT_ID, 'f:affliction'), 'fixture:rule', defeat_id='d:partial'))
    subject.add_defeat(Defeat('c:career', roots, 'fixture:rule', defeat_id='d:full'))
    subject.add_defeat(Defeat('c:career', ('missing',), 'fixture:rule', defeat_id='d:unknown'))
    result = subject.effective_result('c:career', (*roots, 'f:affliction'))
    assert result.state is EffectiveState.UNRESOLVED
    assert result.null_reason == 'partial_defeat_unassessed'
    assert result.conclusion_ids == ('c:career',)
    assert result.defeat_ids == ('d:full', 'd:partial', 'd:unknown')


@pytest.mark.parametrize('difference', ['target', 'event_class', 'valence', 'missing_fact', 'empty_candidate'])
def test_conclusions_without_grounded_opposition_do_not_create_contestation(difference):
    subject = graph()
    subject.conclusions['c:career'] = replace(subject.conclusions['c:career'],
        target_id='graha:Ju', valence=EdgePolarity.SUPPORTS)
    subject.add_mechanism(Mechanism('m:other', MechanismRoute.ADMITTED,
        'major_gain' if difference == 'event_class' else 'career_change',
        ('graha:Ju',), (FACT_ID,), 'fixture:rule'))
    subject.add_conclusion(Conclusion('c:other', 'm:other',
        FactState.EVALUATED_EMPTY if difference == 'empty_candidate' else FactState.PRESENT,
        ('missing',) if difference == 'missing_fact' else (FACT_ID,),
        target_id='graha:Sa' if difference == 'target' else 'graha:Ju',
        valence=EdgePolarity.SUPPORTS if difference == 'valence' else EdgePolarity.OPPOSES))
    assert subject.effective_state('c:career', {FACT_ID}) is EffectiveState.IN_FORCE
    assert subject.effective_result('c:career', {FACT_ID}).null_reason is None
