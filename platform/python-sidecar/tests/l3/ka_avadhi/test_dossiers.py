"""ALGO 3.2 dossier oracles; every value comes from a pinned input."""
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from pipeline.orchestrator.writers.ka_avadhi import build_dossier, validate_dossier
from services.kala_core import sky
from services.kala_core.clocks import Applicability, PeriodContext

START = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)
END = datetime(2001, 1, 1, 12, tzinfo=timezone.utc)


def period(lord="Mars", level=1):
    return dict(system_id="vimshottari", lord_graha=lord, level_n=level,
                start_iso=START, end_iso=END, dasha_row_id="period",
                lord_to_parent_relationship="friend" if level == 2 else None)


def fact(subject, key, value, category="graha_position", extra=None):
    return dict(fact_id=f"CODEX-{subject}-{key}", fact_subject=subject, fact_key=key,
                fact_category=category, fact_value_text=value if isinstance(value, str) else None,
                fact_value_num=value if isinstance(value, (int, float)) else None,
                fact_value_jsonb=extra, citation_ref="CODEX-l1")


def facts():
    return [fact("MAR", "house_d1", 3), fact("MAR", "longitude_sidereal", 12),
            fact("MAR", "retrograde_flag", "direct"),
            fact("D1_MAR", "dignity_state", "own", "graha_dignity_per_varga", {"varga": "D1"}),
            fact("VEN", "house_d1", 7)]


def clock():
    return PeriodContext(START, {"MD": "Saturn", "AD": "Mars"}, {"MD": "md", "AD": "ad"},
                         "applicable", None, None, False, END - START, False,
                         applicability_detail=Applicability("applicable"))


def mechanism(graha="Mars", state="defeated"):
    return dict(mechanism_id="CODEX-mechanism", mechanism_route="admitted",
                derivation_ledger_jsonb={"constituent_planets": [graha], "fact_ids": ["CODEX-MAR-house_d1"],
                    "graph_edges": [{"source_id": "fact", "target_id": "formation", "polarity": "supports"}],
                    "source": "CODEX-rule", "rule_version": "v1"},
                conclusion_state_jsonb={"effective_state": state, "qualification": "sourced",
                                        "defeats": [{"rule_id": "CODEX-bhanga"}], "excepts": []})


def dossier(lord="Mars", source_facts=None, mechanisms=None, level=1):
    return build_dossier(period(lord, level), facts() if source_facts is None else source_facts,
                         [mechanism()] if mechanisms is None else mechanisms, clock(), sky.unavailable(
                             sky.coverage_of((2451545., 2451545.), None, backend="swieph", convention_id="CODEX")))


def test_lord_condition_carries_values_and_fact_ids():
    assert dossier()["lord_condition"]["value"]["dignity_state"] == {
        "value": "own", "fact_ids": ["CODEX-D1_MAR-dignity_state"], "null_reason": None}


def test_changing_mars_dignity_changes_only_mars_dossiers():
    changed = deepcopy(facts()); changed[3]["fact_value_text"] = "debilitated"
    assert [dossier(l, changed) != dossier(l) for l in ["Mars", "Venus"]] == [True, False]


def test_changed_condition_changes_dossier_without_moving_interval():
    changed = deepcopy(facts()); changed[0]["fact_value_num"] = 6
    assert dossier(source_facts=changed) != dossier()


def test_unrelated_mechanism_never_attaches():
    assert dossier(mechanisms=[mechanism("Jupiter")])["attached_mechanisms"] == []


def test_attached_cancellation_and_signed_roles_are_not_promoted():
    assert dossier()["attached_mechanisms"][0]["effective_state"] == "defeated"
    assert dossier()["attached_mechanisms"][0]["roles"][0]["polarity"] == "supports"


def test_commencement_equals_real_sky_at_exact_boundary():
    convention = sky.SkyConvention()
    answer = sky.ephemeris_at(2451545., convention, bodies=("mars",))
    assert answer.available, "the pinned campaign Swiss corpus is required"
    actual = build_dossier(period(), facts(), [], clock(), answer)
    assert actual["commencement_condition"]["value"] == {
        "instant": START.isoformat(), "jd": answer.values[0].jd,
        "position": {"body": "Mars", "longitude_deg": answer.values[0].position("Mars").longitude_deg,
                     "speed_deg_per_day": answer.values[0].position("Mars").speed_deg_per_day},
        "convention_id": convention.convention_id, "backend": "swieph"}


def test_every_unknown_has_a_typed_null_and_no_quality_or_score():
    result = dossier(source_facts=[])
    assert result["lord_condition"] == {"value": None, "null_reason": "missing_fact", "fact_ids": []}
    assert result["commencement_condition"]["null_reason"] == "information_unavailable"
    assert result["evaluated_rule_conclusions"]["null_reason"] == "information_unavailable"
    validate_dossier(result)


@pytest.mark.parametrize("key", ["score", "quality", "quality_label", "numeric_weight"])
def test_score_quality_mutants_fail(key):
    result = dossier(); result[key] = 0.5
    with pytest.raises(ValueError): validate_dossier(result)


def test_ad_parent_and_child_roles_are_preserved():
    result = dossier(level=2)
    assert result["sublord_modulation"] == {"graha": "Saturn", "note": "AD lord Mars modulates MD lord Saturn."}


def test_md_has_no_sublord_modulation():
    assert dossier()["sublord_modulation"] is None


def test_missing_motion_does_not_invent_a_fruition_phase():
    assert dossier(source_facts=[fact("MAR", "longitude_sidereal", 12)])["fruition_phase"]["null_reason"] == "missing_fact"


def test_untyped_null_mutant_fails():
    result = dossier(); result['fruition_phase'] = {'value': None, 'null_reason': None}
    with pytest.raises(ValueError): validate_dossier(result)


def test_zero_sigma_and_scenario_are_carried_without_defaulting():
    from datetime import timedelta
    from dataclasses import replace
    answer = sky.unavailable(sky.coverage_of((1, 1), None, backend='swieph', convention_id='CODEX'))
    context = replace(clock(), sigma_boundary=timedelta(0), scenario_id='CODEX-scenario')
    result = build_dossier(period(), facts(), [], context, answer)
    assert (result['sigma_boundary']['value'], result['scenario']['value']) == (0, 'CODEX-scenario')


@pytest.mark.parametrize('motion,third', [('direct', 1), ('retrograde', 3)])
def test_fruition_uses_canonical_l1_motion(motion, third):
    source = facts(); source[2]['fact_value_text'] = motion; source[1]['fact_value_num'] = 2
    assert dossier(source_facts=source)['fruition_phase']['value']['third'] == third


def test_known_stationary_motion_is_not_reported_as_missing_fact():
    source = facts(); source[2]['fact_value_text'] = 'stationary'
    assert dossier(source_facts=source)['fruition_phase']['null_reason'] == 'information_unavailable'


def test_lagna_lord_relationship_is_projected_from_pinned_l1_not_recomputed():
    source = facts() + [fact('LAGNA', 'sign_lord', 'Venus'),
                        fact('MAITRI_MAR_VEN', 'compound_relation', 'enemy', 'panchadha_maitri')]
    assert dossier(source_facts=source)['placement']['relation_to_lagna_lord'] == {
        'value': 'enemy', 'null_reason': None,
        'fact_ids': ['CODEX-LAGNA-sign_lord', 'CODEX-MAITRI_MAR_VEN-compound_relation']}
