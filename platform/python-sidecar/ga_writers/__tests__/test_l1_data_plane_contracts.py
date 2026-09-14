from __future__ import annotations

from dataclasses import replace
import uuid

import pytest

from ga_writers.data_plane_contracts import (
    CalculationContext,
    ConfigurationOccurrence,
    ContractError,
    EpistemicClass,
    FactEnvelope,
    MissingnessState,
    OccurrenceState,
    QualificationState,
    assert_join_compatible,
    canonical_json,
    stable_fact_id,
    stabilize_hierarchical_uuids,
)
from ga_writers.data_plane_resource_config_slice import (
    build_default_slice,
    build_slice,
    load_fixture,
)


def _context(**overrides):
    values = {
        "subject_id": "synthetic-subject:test",
        "chart_id": "synthetic:test",
        "build_id": "build-1",
        "generation_id": "generation-1",
        "instant_iso": "2000-01-01T12:00:00+00:00",
        "latitude_deg": 0.0,
        "longitude_deg": 0.0,
        "timezone_name": "UTC",
        "input_precision": "second",
        "frame": "sidereal",
        "ayanamsha_id": "lahiri_chitrapaksha",
        "node_type": "mean",
        "house_convention": "whole_sign",
        "varga": "D1",
        "varga_formula": "parasara_standard_v1",
        "varga_domain": "natal",
        "karaka_school": "jaimini_eight_karaka",
        "engine_version": "synthetic/1.0",
    }
    values.update(overrides)
    return CalculationContext(**values)


def test_context_identity_is_stable_across_build_generation_but_join_is_not():
    left = _context()
    right = replace(left, build_id="build-2", generation_id="generation-2")
    assert left.context_id == right.context_id
    with pytest.raises(ContractError, match="build_id, generation_id"):
        assert_join_compatible(left, right)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("chart_id", "synthetic:other"),
        ("ayanamsha_id", "raman"),
        ("varga", "D9"),
        ("node_type", "true"),
        ("house_convention", "placidus"),
    ],
)
def test_material_context_changes_rotate_context_identity(field, value):
    base = _context()
    assert replace(base, **{field: value}).context_id != base.context_id


def test_context_requires_aware_instant_and_explicit_node_variant():
    with pytest.raises(ContractError, match="UTC offset"):
        _context(instant_iso="2000-01-01T12:00:00")
    with pytest.raises(ContractError, match="mean and true"):
        _context(node_type="ambiguous")


def test_stable_fact_id_excludes_build_generation_and_keeps_real_variants():
    first = stable_fact_id("position", "RAH_MEAN", "longitude", "chart", "lahiri")
    replay = stable_fact_id("position", "RAH_MEAN", "longitude", "chart", "lahiri")
    true_node = stable_fact_id("position", "RAH_TRUE", "longitude", "chart", "lahiri")
    assert first == replay
    assert first != true_node


@pytest.mark.parametrize(
    "factory",
    [
        lambda build: __import__("ga_writers.ga_vargas_writer", fromlist=["_fact_id"])._fact_id("D9", "SUN", "varga_position", "sign", "chart", "lahiri", build),
        lambda build: __import__("ga_writers.ga_strength_writer", fromlist=["_fact_id"])._fact_id("graha_shadbala_total", "SUN", "rupa", "chart", "lahiri", build),
        lambda build: __import__("ga_writers.ga_structural_writer", fromlist=["_fact_id"])._fact_id("aspect", "SUN", "MOON", "chart", "lahiri", build),
        lambda build: __import__("ga_writers.ga_sensitive_writer", fromlist=["_fact_id"])._fact_id("special_lagna", "GHATI", "longitude", "chart", "lahiri", build, "formula-v1"),
        lambda build: __import__("ga_writers.ga_sensitive_degree_writer", fromlist=["_fact_id"])._fact_id("YOGI", "longitude", "chart", "lahiri", build),
        lambda build: __import__("ga_writers.ga_panchanga_writer", fromlist=["_fact_id"])._fact_id("panchanga", "TITHI", "index", "chart", "lahiri", build),
        lambda build: __import__("ga_writers.ga_ayurdaya_writer", fromlist=["_fact_id"])._fact_id("PINDAYU", "years", "chart", "lahiri", build),
        lambda build: __import__("ga_writers.ga_sade_sati_writer", fromlist=["_fact_id"])._fact_id("sade_sati_cycle", "CYCLE_1", "start", "chart", "lahiri", build),
        lambda build: __import__("pipeline.orchestrator.writers.ga_nakshatra", fromlist=["_fact_id"])._fact_id("graha_nakshatra_join", "SUN", "nakshatra", "chart", "lahiri", build),
    ],
)
def test_corrected_writer_fact_ids_are_stable_across_builds(factory):
    assert factory("build-one") == factory("build-two")


@pytest.mark.parametrize(
    "state",
    [
        MissingnessState.UNAVAILABLE,
        MissingnessState.FLOORED,
        MissingnessState.INAPPLICABLE,
        MissingnessState.UNQUALIFIED_SOURCE,
        MissingnessState.FAILED,
        MissingnessState.UNEXPLORED,
    ],
)
def test_non_value_states_are_reasoned_and_never_serialize_as_zero(state):
    fact = FactEnvelope(
        context=_context(),
        category="condition",
        subject="JUP",
        key=state.value,
        grain="chart-context-graha",
        unit=None,
        epistemic_class=EpistemicClass.DETERMINISTIC_DERIVATION,
        verification_class="fixture",
        missingness=state,
        reason=f"fixture {state.value}",
    )
    payload = fact.to_dict()
    assert payload["missingness"] == state.value
    assert payload["value_num"] is None


def test_real_zero_is_distinct_from_unavailable():
    zero = FactEnvelope(
        context=_context(), category="condition", subject="JUP", key="zero",
        grain="chart-context-graha", unit="degree",
        epistemic_class=EpistemicClass.DETERMINISTIC_DERIVATION,
        verification_class="fixture", missingness=MissingnessState.ZERO,
        value_num=0,
    )
    assert zero.to_dict()["value_num"] == 0
    with pytest.raises(ContractError, match="explicit numeric zero"):
        replace(zero, value_num=None)


def test_unqualified_source_cannot_become_positive_doctrinal_occurrence():
    kwargs = {
        "context": _context(),
        "configuration_id": "bhavat.synthetic",
        "configuration_version": "1",
        "source_rule_id": "bhavat_bhavam.odd_house_nonrecursive.v1",
        "source_rule_version": "l0-resource-config-g1",
        "qualification_state": QualificationState.UNQUALIFIED_SOURCE,
        "state": OccurrenceState.UNQUALIFIED_SOURCE,
        "participants": ({"role": "primary_house", "subject": "HOUSE_1"},),
        "satisfied_clauses": ("primary_house_present",),
        "failed_clauses": ("qualified_witness_absent",),
    }
    occurrence = ConfigurationOccurrence(**kwargs)
    assert occurrence.positive_doctrinal_arm == "NOT_REACHABLE"
    with pytest.raises(ContractError, match="cannot yield"):
        ConfigurationOccurrence(**{**kwargs, "state": OccurrenceState.FORMED})


def test_engineering_state_machine_can_be_exercised_without_doctrinal_authority():
    occurrence = ConfigurationOccurrence(
        context=_context(),
        configuration_id="engineering.state-machine",
        configuration_version="1",
        source_rule_id="engineering.fixture",
        source_rule_version="1",
        qualification_state=QualificationState.ENGINEERING_ONLY,
        state=OccurrenceState.FORMED,
        participants=({"role": "actor", "subject": "A"},),
        satisfied_clauses=("a",),
        failed_clauses=(),
        epistemic_class=EpistemicClass.ENGINEERING_FIXTURE,
        doctrinal=False,
    )
    assert occurrence.state is OccurrenceState.FORMED
    assert occurrence.to_dict()["doctrinal"] is False


def test_hierarchical_clock_ids_are_build_independent_and_parent_safe():
    def rows(build_id):
        root = str(uuid.uuid4())
        child = str(uuid.uuid4())
        return [
            {"dasha_row_id": root, "parent_row_id": None, "chart_id": "chart",
             "ayanamsha_id": "lahiri", "build_id": build_id, "system_id": "vimshottari",
             "level_n": 1, "lord_graha": "JUP", "start_iso": "2000-01-01T00:00:00+00:00",
             "end_iso": "2016-01-01T00:00:00+00:00", "kp_sublevel": None,
             "kp_sub_lord": None, "kp_sub_sub_lord": None},
            {"dasha_row_id": child, "parent_row_id": root, "chart_id": "chart",
             "ayanamsha_id": "lahiri", "build_id": build_id, "system_id": "vimshottari",
             "level_n": 2, "lord_graha": "SAT", "start_iso": "2000-01-01T00:00:00+00:00",
             "end_iso": "2002-07-01T00:00:00+00:00", "kp_sublevel": None,
             "kp_sub_lord": None, "kp_sub_sub_lord": None},
        ]

    first = rows("build-1")
    replay = rows("build-2")
    fields = (
        "chart_id", "ayanamsha_id", "system_id", "level_n", "lord_graha",
        "start_iso", "end_iso", "kp_sublevel", "kp_sub_lord", "kp_sub_sub_lord",
    )
    stabilize_hierarchical_uuids(first, id_field="dasha_row_id", parent_field="parent_row_id", identity_fields=fields, kind="dasha_interval")
    stabilize_hierarchical_uuids(replay, id_field="dasha_row_id", parent_field="parent_row_id", identity_fields=fields, kind="dasha_interval")
    assert [row["dasha_row_id"] for row in first] == [row["dasha_row_id"] for row in replay]
    assert first[1]["parent_row_id"] == first[0]["dasha_row_id"]


def test_default_slice_is_deterministic_non_person_and_preserves_all_states():
    first = build_default_slice()
    second = build_default_slice()
    assert canonical_json(first) == canonical_json(second)
    assert first["fixture_class"] == "deterministic_non_person"
    assert first["context"]["chart_id"].startswith("synthetic:")
    assert first["configuration"]["positive_doctrinal_arm"] == "NOT_REACHABLE"
    assert first["bhavat_bhavam"] == {
        "method_id": "bhavat_bhavam.odd_house_nonrecursive.v1",
        "qualification_state": "UNQUALIFIED_SOURCE",
        "application_owner": "L2 Bodha",
        "applied": False,
        "positive_doctrinal_arm": "NOT_REACHABLE",
        "primary_house_facts_preserved": True,
    }
    assert set(first["missingness_states_proved"]) == {
        "present", "zero", "unavailable", "floored", "inapplicable",
        "unqualified_source", "failed", "unexplored",
    }
    assert [item["classification"] for item in first["sensitivity"]] == ["changed", "unchanged"]


def test_slice_rejects_personal_or_stored_chart_identity():
    fixture = load_fixture()
    fixture["chart_id"] = "482012f1-710e-4a25-994a-93821f5871aa"
    with pytest.raises(ContractError, match="stored/personal"):
        build_slice(fixture)
