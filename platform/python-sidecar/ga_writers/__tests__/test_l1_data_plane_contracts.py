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
from ga_writers.data_plane_runtime import CONTRACTED_L1_ASSETS
from pipeline.orchestrator.writers import ContextSpec, discover_all, list_writers


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


@pytest.mark.parametrize(
    ("field", "value"),
    [("instant_iso", "2000-01-01T12:00:01+00:00"), ("node_type", "true"),
     ("varga", "D9"), ("varga_formula", "parasara_variant_v2"),
     ("engine_version", "synthetic/2.0")],
)
def test_material_context_changes_rotate_fact_identity(field, value):
    base = FactEnvelope(
        context=_context(varga="D1"), category="position", subject="SUN", key="longitude",
        grain="chart-context-graha", unit="degree", epistemic_class=EpistemicClass.ASTRONOMICAL,
        verification_class="fixture", value_num=1.0,
    )
    changed = replace(base, context=replace(base.context, **{field: value}))
    assert changed.fact_id != base.fact_id


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


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_numeric_values_cannot_be_present(value):
    with pytest.raises(ContractError, match="finite"):
        FactEnvelope(
            context=_context(), category="position", subject="SUN", key="longitude",
            grain="chart-context-graha", unit="degree",
            epistemic_class=EpistemicClass.ASTRONOMICAL,
            verification_class="fixture", value_num=value,
        )


def test_non_finite_nested_json_is_rejected():
    with pytest.raises(ContractError, match="canonical JSON"):
        canonical_json({"value": [float("nan")]})


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
    assert first["content_sha256"] == "25c46b559def7e1a9f8e1a05114be5a6c306a846a23b2665b1b5c917128d3279"
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


def test_slice_rejects_personal_subject_identity():
    fixture = load_fixture()
    fixture["subject_id"] = "person:actual-user-123"
    with pytest.raises(ContractError, match="personal subject"):
        build_slice(fixture)


def test_slice_dependencies_close_and_sensitivity_recomputes_output():
    payload = build_default_slice()
    emitted = {fact["fact_id"] for fact in payload["facts"]}
    resolved = {
        item["dependency_id"] for item in payload["resolved_l0_dependencies"]
    }
    for fact in payload["facts"]:
        for dependency in fact["source_dependencies"]:
            assert dependency in emitted or dependency in resolved
    changed, unchanged = payload["sensitivity"]
    assert changed["baseline_output"] != changed["perturbed_output"]
    assert unchanged["baseline_output"] == unchanged["perturbed_output"]
    assert changed["target_varga_formula"] == "parasara_standard_v1"
    assert changed["baseline_d1_output"] != changed["baseline_output"]
    assert unchanged["baseline_d1_output"] == unchanged["perturbed_d1_output"]


def test_slice_rejects_unknown_l0_dependency_and_varga_formula():
    fixture = load_fixture()
    fixture["facts"][0]["source_dependencies"].append(
        "l0:definitely_not_a_released_identity"
    )
    with pytest.raises(ContractError, match="accepted L0 release"):
        build_slice(fixture)

    fixture = load_fixture()
    fixture["sensitivity"][0]["target_varga_formula"] = "not-a-real-varga-formula"
    with pytest.raises(ContractError, match="unadmitted varga"):
        build_slice(fixture)


def test_all_nineteen_runtime_writers_have_the_contract_boundary():
    discover_all()
    ga_writers = {
        asset_id: writer
        for asset_id, writer in list_writers().items()
        if asset_id.startswith("ga_")
    }
    assert set(ga_writers) == CONTRACTED_L1_ASSETS
    assert len(ga_writers) == 19
    for asset_id, writer in ga_writers.items():
        assert writer.__l1_data_plane_contract__ is True, asset_id
        assert writer.l1_data_plane_contract_version == "l1.data-plane.contract.1.0"


class _RuntimeCursor:
    def __init__(self, statements):
        self.statements = statements

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.statements.append((" ".join(sql.split()), params))
        return self


class _RuntimeConn:
    _l1_contract_test_double = True

    def __init__(self):
        self.statements = []

    def cursor(self, *args, **kwargs):
        return _RuntimeCursor(self.statements)


def test_runtime_boundary_opens_then_completes_a_generation(monkeypatch):
    from ga_writers import ga_positions_writer

    discover_all()
    monkeypatch.setattr(
        ga_positions_writer,
        "build_ga_positions",
        lambda **kwargs: {"total_chart_facts_rows": 9},
    )
    conn = _RuntimeConn()
    ctx = ContextSpec(
        asset_id="ga_positions",
        build_id="11111111-1111-4111-8111-111111111111",
        db_conn=conn,
        config={"chart_id": "22222222-2222-4222-8222-222222222222"},
    )
    result = list_writers()["ga_positions"]().run(ctx)
    sql = [statement for statement, _ in conn.statements]
    assert result.rows_inserted == 9
    assert "set_config('madhav.l1_asset_id'" in sql[0]
    assert "open_l1_data_plane_generation" in sql[1]
    assert "complete_l1_data_plane_partition" in sql[2]
    assert conn.statements[2][1][-1] == 9


def test_generation_base_context_is_partition_invariant():
    from pathlib import Path

    migration = Path("platform/migrations/1033_data_plane_l1_producer_history.sql").read_text()
    base_context = migration.split("v_context := jsonb_build_object(", 1)[1].split(
        "INSERT INTO public.l1_data_plane_generations", 1
    )[0]
    row_context = migration.split("v_context := v_base || jsonb_build_object(", 1)[1].split(
        "v_context_id :=", 1
    )[0]
    assert "'ayanamsha_id', 'mixed_or_invariant'" in base_context
    assert "p_partition_key ~ '^ayanamsha[:_]'" not in base_context
    assert "v_partition ~ '^ayanamsha[:_]'" in row_context


def test_generation_history_freezes_completed_rows_and_exposes_latest_typed_views():
    from pathlib import Path

    migration = Path("platform/migrations/1033_data_plane_l1_producer_history.sql").read_text()
    assert "complete generation % cannot admit new row" in migration
    assert "complete generation % replay changed output" in migration
    assert "l1_data_plane_jsonb_has_nonfinite(v_row)" in migration
    assert "CREATE TABLE IF NOT EXISTS public.l1_data_plane_fact_snapshots" in migration
    assert "CREATE TABLE IF NOT EXISTS public.l1_data_plane_configuration_snapshots" in migration
    current_rows = migration.split(
        "CREATE OR REPLACE VIEW public.l1_data_plane_current_rows AS", 1
    )[1].split("CREATE OR REPLACE VIEW public.l1_data_plane_current_facts", 1)[0]
    assert "DISTINCT ON (s.chart_id, s.asset_id, s.source_table, s.row_identity)" in current_rows


def test_runtime_boundary_does_not_complete_a_failed_writer(monkeypatch):
    from ga_writers import ga_positions_writer

    discover_all()

    def fail(**kwargs):
        raise RuntimeError("numerical failure")

    monkeypatch.setattr(ga_positions_writer, "build_ga_positions", fail)
    conn = _RuntimeConn()
    ctx = ContextSpec(
        asset_id="ga_positions",
        build_id="11111111-1111-4111-8111-111111111111",
        db_conn=conn,
        config={"chart_id": "22222222-2222-4222-8222-222222222222"},
    )
    with pytest.raises(RuntimeError, match="numerical failure"):
        list_writers()["ga_positions"]().run(ctx)
    assert not any(
        "complete_l1_data_plane_partition" in statement
        for statement, _ in conn.statements
    )


def test_structural_boundary_rejects_missing_or_defaulted_geometry():
    from ga_writers.ga_structural_writer import _validate_chart_output_complete

    with pytest.raises(RuntimeError, match="ascendant"):
        _validate_chart_output_complete({"grahas": []})
    with pytest.raises(RuntimeError, match="required grahas missing"):
        _validate_chart_output_complete({
            "ascendant": {"sign": "Aries", "sign_id": 1, "longitude": 0.0},
            "grahas": [],
        })


def test_sensitive_helpers_reject_missing_lagna_and_vara():
    from ga_writers.ga_sensitive_writer import (
        _build_gulika_mandi_sensitive_rows,
        _build_saham_rows,
    )

    with pytest.raises(ValueError, match="LAGNA"):
        _build_saham_rows({}, "chart", "lahiri", "build", "engine", True)
    with pytest.raises(ValueError, match="vara_id"):
        _build_gulika_mandi_sensitive_rows(
            {}, {"LAGNA": 10.0, "SAT": 20.0},
            "chart", "lahiri", "build", "engine", {},
        )


def test_sensitive_vara_contract_accepts_numeric_alias_and_rejects_conflict():
    from ga_writers.ga_sensitive_writer import _require_vara_id

    assert _require_vara_id({"vara": 0}) == 0
    assert _require_vara_id({"vara_id": 0, "vara": "Sunday"}) == 0
    with pytest.raises(ValueError, match="conflicts"):
        _require_vara_id({"vara_id": 0, "vara": 1})


def test_sensitive_day_night_uses_astronomical_sunrise_and_sunset():
    from ga_writers.ga_sensitive_writer import _derive_is_day_birth

    common = {
        "latitude_deg": 20.27,
        "longitude_deg": 85.84,
        "tz_offset_hours": 5.5,
    }
    assert _derive_is_day_birth({
        **common, "datetime_iso": "1984-02-05T10:43:00+05:30",
    }) is True
    assert _derive_is_day_birth({
        **common, "datetime_iso": "1984-02-05T23:00:00+05:30",
    }) is False


def test_sensitive_day_night_rejects_timezone_conflict():
    from ga_writers.ga_sensitive_writer import _derive_is_day_birth

    with pytest.raises(ValueError, match="conflicts"):
        _derive_is_day_birth({
            "datetime_iso": "1984-02-05T10:43:00+00:00",
            "latitude_deg": 20.27,
            "longitude_deg": 85.84,
            "tz_offset_hours": 5.5,
        })
