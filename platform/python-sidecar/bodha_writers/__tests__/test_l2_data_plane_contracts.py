from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

import bodha_writers.data_plane_contracts as contract_module

from bodha_writers.data_plane_contracts import (
    ACCEPTED_L0_RELEASE,
    ACCEPTED_L1_TERMINAL,
    ContractError,
    CURRENT_WRITERS,
    HISTORICAL_FORMAL_WRITERS,
    begin_observation,
    content_digest,
    l2_producer,
    stable_semantic_uuid,
    stable_structural_id,
)
from bodha_writers.data_plane_resource_mechanism_slice import (
    build_resource_mechanism_slice,
)


FIXTURE = Path(__file__).parent / "fixtures" / "l2_resource_mechanism_non_person_v1.json"


def load_fixture():
    return json.loads(FIXTURE.read_text())


def test_denominators_remain_distinct():
    assert len(CURRENT_WRITERS) == 23
    assert len(set(CURRENT_WRITERS)) == 23
    assert len(HISTORICAL_FORMAL_WRITERS) == 22
    assert "bo_grounding" not in HISTORICAL_FORMAL_WRITERS


def test_stable_identity_rejects_volatile_or_nonfinite_material():
    with pytest.raises(ValueError, match="volatile"):
        stable_structural_id("proposition", {"rule": "r1", "build_id": "b1"})
    with pytest.raises(ValueError, match="non-finite"):
        content_digest({"value": float("nan")})
    with pytest.raises(ValueError, match="volatile"):
        stable_structural_id(
            "proposition", {"nested": [{"evidence": {"computed_at": "now"}}]},
        )
    assert stable_semantic_uuid("proposition", {"rule": "r1"}) == stable_semantic_uuid(
        "proposition", {"rule": "r1"},
    )


def _upstream_context(chart_id: str, partition_key: str = "bo_laksana"):
    vector = [{
        "layer": "L1",
        "asset_id": "ga_positions",
        "generation_id": "l1-generation-1",
        "semantic_output_digest": "f" * 64,
    }]
    context = {
        "subject_id": "subject-1",
        "chart_id": chart_id,
        "generation_context_id": "l2:generation-context:exact",
        "calculation_context_id": "l1ctx:exact",
        "ayanamsha_id": "mixed_or_invariant",
        "reference_frame": "sidereal",
        "varga_id": "row_declared_or_D1",
        "partition_key": partition_key,
    }
    return vector, context


def test_observation_is_deterministic_and_fails_wrong_upstream():
    ctx = SimpleNamespace(
        build_id="00000000-0000-0000-0000-000000000001",
        config={"chart_id": "00000000-0000-0000-0000-000000000002"},
    )
    vector, context = _upstream_context(ctx.config["chart_id"])
    first = begin_observation(
        ctx, "bo_laksana", "a" * 64,
        dependency_vector=vector, calculation_context=context,
    )
    second = begin_observation(
        ctx, "bo_laksana", "a" * 64,
        dependency_vector=vector, calculation_context=context,
    )
    assert first == second
    assert first.generation_id.startswith("l2g:")

    bad = SimpleNamespace(
        build_id=ctx.build_id,
        config={
            "chart_id": ctx.config["chart_id"],
            "accepted_l0_release": "wrong",
            "accepted_l1_terminal": ACCEPTED_L1_TERMINAL,
        },
    )
    with pytest.raises(ContractError, match="wrong accepted_l0"):
        begin_observation(
            bad, "bo_laksana", "a" * 64,
            dependency_vector=vector, calculation_context=context,
        )

    missing_context = SimpleNamespace(build_id=ctx.build_id, config={"chart_id": ctx.config["chart_id"]})
    with pytest.raises(ContractError, match="exact completed L1"):
        begin_observation(missing_context, "bo_laksana", "a" * 64)


def test_multi_partition_writer_uses_one_generation_with_exact_partition_contexts():
    ctx = SimpleNamespace(
        build_id="00000000-0000-0000-0000-000000000001",
        config={"chart_id": "00000000-0000-0000-0000-000000000002"},
    )
    vector, lahiri = _upstream_context(ctx.config["chart_id"], "aya_lahiri")
    lahiri["ayanamsha_id"] = "lahiri"
    lahiri["calculation_context_id"] = "l2:partition:lahiri"
    _, kp = _upstream_context(ctx.config["chart_id"], "aya_krishnamurti")
    kp["ayanamsha_id"] = "krishnamurti"
    kp["calculation_context_id"] = "l2:partition:krishnamurti"

    first = begin_observation(
        ctx, "bo_samskara", "a" * 64,
        partition_key="aya_lahiri", dependency_vector=vector,
        calculation_context=lahiri,
    )
    second = begin_observation(
        ctx, "bo_samskara", "a" * 64,
        partition_key="aya_krishnamurti", dependency_vector=vector,
        calculation_context=kp,
    )
    assert first.generation_id == second.generation_id
    assert first.calculation_context_id != second.calculation_context_id
    assert first.partition_key != second.partition_key


def test_heavy_writer_records_each_substep_partition_in_callers_transaction(monkeypatch):
    executed = []

    class Cursor:
        description = None

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, sql, params):
            executed.append((sql, params))

    class Conn:
        _l2_contract_test_double = True

        def cursor(self):
            return Cursor()

    @l2_producer("bo_samskara")
    class Heavy:
        asset_id = "bo_samskara"

        def run_substep(self, ctx, step):
            return SimpleNamespace(rows_inserted=2, rows_updated=0, rows_skipped=1, notes="")

    ctx = SimpleNamespace(
        build_id="00000000-0000-0000-0000-000000000001",
        config={"chart_id": "00000000-0000-0000-0000-000000000002"},
        db_conn=Conn(),
        dry_run=False,
    )
    vector, context = _upstream_context(ctx.config["chart_id"], "lahiri")
    monkeypatch.setattr(
        contract_module, "_resolve_upstream_context", lambda *_args, **_kwargs: (vector, context),
    )
    monkeypatch.setattr(contract_module, "_writer_source_digest", lambda _asset_id: "a" * 64)
    result = Heavy().run_substep(ctx, SimpleNamespace(key="lahiri"))
    assert result._l2_partition_key == "lahiri"
    sql = "\n".join(item[0] for item in executed)
    assert "open_l2_data_plane_generation" in sql
    assert "bind_l2_exact_inputs" in sql
    assert "complete_l2_data_plane_partition" in sql
    assert any("lahiri" in tuple(str(value) for value in params) for _, params in executed)


def test_slice_is_deterministic_complete_non_temporal_and_non_promotable():
    fixture = load_fixture()
    a = build_resource_mechanism_slice(fixture)
    b = build_resource_mechanism_slice(deepcopy(fixture))
    assert a == b
    assert a["content_digest"] == fixture["expected_output_digest"]
    assert a["fixture_class"] == "ENGINEERING_ONLY"
    assert a["promotable"] is False
    assert a["grounding"]["qualification_state"] == "UNQUALIFIED_SOURCE"
    assert a["grounding"]["positive_doctrinal_arm"] == "NOT_REACHABLE"
    assert a["activation_windows"] is None
    assert a["temporal_semantics_status"] == "UNAVAILABLE_AT_L2"
    assert {x["role"] for x in a["domains"]} == {"creation", "receipts", "retention", "relief"}
    assert {x["polarity"] for x in a["relationships"]} == {-1, 1}
    assert a["independent_support_count"] == 2
    assert any(x["rank"] == 999 and x["decisive"] for x in a["discovery_pointers"])


def test_domain_order_alias_and_unrelated_configuration_are_invariant():
    base = load_fixture()
    expected = build_resource_mechanism_slice(base)
    changed = deepcopy(base)
    changed["selected_configuration"]["domains"].reverse()
    for domain in changed["selected_configuration"]["domains"]:
        if domain["domain"] == "income":
            domain["domain"] = "receipts"
    changed["unrelated_configurations"].append(
        {"configuration_id": "synthetic:unrelated-02", "domain": "health", "rank": 0}
    )
    assert build_resource_mechanism_slice(changed) == expected


def test_condition_change_is_local_and_cancellation_polarity_is_not_flattened():
    base = load_fixture()
    original = build_resource_mechanism_slice(base)
    condition = deepcopy(base)
    condition["selected_configuration"]["condition_ledger"]["affliction_value"] = 3.0
    changed = build_resource_mechanism_slice(condition)
    assert changed["configuration_id"] == original["configuration_id"]
    assert changed["proposition_id"] == original["proposition_id"]
    assert changed["relationships"] == original["relationships"]
    assert changed["condition_ledger"] != original["condition_ledger"]
    assert changed["content_digest"] != original["content_digest"]

    reversed_fixture = deepcopy(base)
    for path in reversed_fixture["selected_configuration"]["paths"]:
        if path["path_id"] == "path:opposition":
            path["polarity"] = 1
    reversed_fixture["selected_configuration"]["cancellation"]["target_original_polarity"] = 1
    reversed_bundle = build_resource_mechanism_slice(reversed_fixture)
    assert original["cancellation"]["resulting_role"] == "attenuated_opposition"
    assert reversed_bundle["cancellation"]["resulting_role"] == "attenuated_support"


@pytest.mark.parametrize("field", ["chart_id", "calculation_context_id", "generation_id", "ayanamsha_id"])
def test_wrong_partition_fails_closed(field):
    fixture = load_fixture()
    fixture["selected_configuration"][field] = "wrong"
    with pytest.raises(ValueError, match=f"wrong slice {field}"):
        build_resource_mechanism_slice(fixture)


def test_unqualified_rule_cannot_be_promoted():
    fixture = load_fixture()
    fixture["selected_configuration"]["qualification_state"] = "QUALIFIED"
    with pytest.raises(ValueError, match="must remain unqualified"):
        build_resource_mechanism_slice(fixture)


def test_slice_rejects_caller_invented_roots_units_and_component_polarity():
    fixture = load_fixture()
    fixture["selected_configuration"]["paths"][0]["shared_root_group"] = "invented"
    with pytest.raises(ValueError, match="root ancestry"):
        build_resource_mechanism_slice(fixture)

    fixture = load_fixture()
    fixture["selected_configuration"]["occurrence_ledger"]["unit"] = "percent"
    with pytest.raises(ValueError, match="occurrence ledger"):
        build_resource_mechanism_slice(fixture)

    fixture = load_fixture()
    fixture["selected_configuration"]["condition_ledger"]["components"][0]["polarity"] = 0
    with pytest.raises(ValueError, match=r"exactly -1 or \+1"):
        build_resource_mechanism_slice(fixture)
