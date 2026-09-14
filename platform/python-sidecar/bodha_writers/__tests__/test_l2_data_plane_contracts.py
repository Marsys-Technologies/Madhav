from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

import bodha_writers.data_plane_contracts as contract_module
from bodha_writers import _idempotency

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
    _validate_compatible_l2_set,
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


def test_selected_l2_generation_rejects_stale_transitive_head():
    l1_rows = [{
        "asset_id": "ga_positions", "generation_id": "l1-new",
        "output_digest": "b" * 64,
    }]
    l2_rows = [{
        "asset_id": "bo_laksana", "generation_id": "l2-old",
        "output_digest": "c" * 64,
        "dependency_vector": [{
            "layer": "L1", "asset_id": "ga_positions",
            "generation_id": "l1-old", "semantic_output_digest": "a" * 64,
        }],
    }]
    with pytest.raises(ContractError, match="stale transitive"):
        _validate_compatible_l2_set(
            l1_rows, l2_rows, {"bo_laksana": {("L1", "ga_positions")}},
        )


def test_selected_l2_generation_accepts_one_compatible_set():
    l1_rows = [{
        "asset_id": "ga_positions", "generation_id": "l1-current",
        "output_digest": "a" * 64,
    }]
    l2_rows = [{
        "asset_id": "bo_laksana", "generation_id": "l2-current",
        "output_digest": "b" * 64,
        "dependency_vector": [{
            "layer": "L1", "asset_id": "ga_positions",
            "generation_id": "l1-current", "semantic_output_digest": "a" * 64,
        }],
    }]
    _validate_compatible_l2_set(
        l1_rows, l2_rows, {"bo_laksana": {("L1", "ga_positions")}},
    )


@pytest.mark.parametrize(
    "expected",
    [
        {("L1", "ga_positions"), ("L1", "ga_condition")},
        set(),
    ],
)
def test_selected_l2_generation_rejects_dependency_topology_drift(expected):
    l1_rows = [{
        "asset_id": "ga_positions", "generation_id": "l1-current",
        "output_digest": "a" * 64,
    }]
    l2_rows = [{
        "asset_id": "bo_laksana", "generation_id": "l2-current",
        "output_digest": "b" * 64,
        "dependency_vector": [{
            "layer": "L1", "asset_id": "ga_positions",
            "generation_id": "l1-current", "semantic_output_digest": "a" * 64,
        }],
    }]
    with pytest.raises(ContractError, match="stale dependency topology"):
        _validate_compatible_l2_set(
            l1_rows, l2_rows, {"bo_laksana": expected},
        )


def test_migration_checks_current_dependency_topology_and_locks_msr_scope():
    migration = (
        Path(__file__).resolve().parents[3]
        / "migrations/1034_data_plane_l2_producer_generations.sql"
    ).read_text()
    assert "l2_data_plane_dependency_topology_matches" in migration
    assert "L2 generation dependency topology is stale or incomplete" in migration
    guard = migration.split(
        "CREATE OR REPLACE FUNCTION public.assert_l2_msr_delete_safe", 1,
    )[1].split("CREATE OR REPLACE FUNCTION public.bind_l2_exact_inputs", 1)[0]
    assert "FOR UPDATE" in guard


def test_msr_guard_serializes_cascade_and_set_null_fk_inserts():
    database_url = os.environ.get("L2_CONTRACT_DATABASE_URL")
    if not database_url:
        pytest.skip("L2_CONTRACT_DATABASE_URL not supplied for disposable PostgreSQL proof")
    psycopg = pytest.importorskip("psycopg")
    sql = pytest.importorskip("psycopg.sql")
    chart_id = "10000000-0000-0000-0000-000000000001"
    signal_ids = {
        "l2_guard_probe_cascade": "10000000-0000-0000-0000-000000000002",
        "l2_guard_probe_set_null": "10000000-0000-0000-0000-000000000003",
    }

    with psycopg.connect(database_url, autocommit=True) as admin:
        for table in signal_ids:
            admin.execute(sql.SQL("DROP TABLE IF EXISTS public.{}") .format(sql.Identifier(table)))
        admin.execute("DROP TABLE IF EXISTS public.bodha_msr_signals")
        admin.execute(
            """CREATE TABLE public.bodha_msr_signals (
                 signal_id uuid PRIMARY KEY, chart_id uuid NOT NULL,
                 ayanamsha_id text NOT NULL, signal_type_id text NOT NULL,
                 signal_type_class text NOT NULL
               )"""
        )
        admin.execute(
            """CREATE TABLE public.l2_guard_probe_cascade (
                 id integer PRIMARY KEY, signal_id uuid NOT NULL REFERENCES
                 public.bodha_msr_signals(signal_id) ON DELETE CASCADE
               )"""
        )
        admin.execute(
            """CREATE TABLE public.l2_guard_probe_set_null (
                 id integer PRIMARY KEY, signal_id uuid REFERENCES
                 public.bodha_msr_signals(signal_id) ON DELETE SET NULL
               )"""
        )
        for signal_id in signal_ids.values():
            admin.execute(
                "INSERT INTO public.bodha_msr_signals VALUES (%s, %s, 'lahiri', 'type', 'class')",
                (signal_id, chart_id),
            )

    try:
        for table, signal_id in signal_ids.items():
            with psycopg.connect(database_url) as locker, psycopg.connect(database_url) as inserter:
                locker.execute(
                    "SELECT public.assert_l2_msr_delete_safe(%s::uuid, NULL, NULL, NULL)",
                    (chart_id,),
                )
                inserter.execute("SET LOCAL statement_timeout = '250ms'")
                with pytest.raises(psycopg.errors.QueryCanceled):
                    inserter.execute(
                        sql.SQL("INSERT INTO public.{} (id, signal_id) VALUES (1, %s)")
                        .format(sql.Identifier(table)),
                        (signal_id,),
                    )
                inserter.rollback()
                locker.rollback()

                inserter.execute(
                    sql.SQL("INSERT INTO public.{} (id, signal_id) VALUES (1, %s)")
                    .format(sql.Identifier(table)),
                    (signal_id,),
                )
                inserter.commit()
                with pytest.raises(psycopg.errors.RaiseException, match="cross-layer dependent"):
                    locker.execute(
                        "SELECT public.assert_l2_msr_delete_safe(%s::uuid, NULL, NULL, NULL)",
                        (chart_id,),
                    )
                locker.rollback()
                inserter.execute(sql.SQL("DELETE FROM public.{}") .format(sql.Identifier(table)))
                inserter.commit()
    finally:
        with psycopg.connect(database_url, autocommit=True) as admin:
            for table in signal_ids:
                admin.execute(sql.SQL("DROP TABLE IF EXISTS public.{}") .format(sql.Identifier(table)))
            admin.execute("DROP TABLE IF EXISTS public.bodha_msr_signals")


def test_database_topology_match_detects_dependency_addition_and_removal():
    database_url = os.environ.get("L2_CONTRACT_DATABASE_URL")
    if not database_url:
        pytest.skip("L2_CONTRACT_DATABASE_URL not supplied for disposable PostgreSQL proof")
    psycopg = pytest.importorskip("psycopg")
    vector = json.dumps([{
        "layer": "L1", "asset_id": "ga_topology_a",
        "generation_id": "g-a", "semantic_output_digest": "a" * 64,
    }])
    with psycopg.connect(database_url) as conn:
        conn.execute(
            """INSERT INTO public.asset_registry(asset_id, depends_on)
               VALUES ('ga_topology_a', ARRAY[]::text[]),
                      ('ga_topology_b', ARRAY[]::text[]),
                      ('bo_topology_probe', ARRAY['ga_topology_a']::text[])
               ON CONFLICT (asset_id) DO UPDATE SET depends_on=EXCLUDED.depends_on"""
        )
        assert conn.execute(
            "SELECT public.l2_data_plane_dependency_topology_matches(%s, %s::jsonb)",
            ("bo_topology_probe", vector),
        ).fetchone()[0] is True

        conn.execute(
            "UPDATE public.asset_registry SET depends_on=ARRAY['ga_topology_a','ga_topology_b']::text[] WHERE asset_id='bo_topology_probe'"
        )
        assert conn.execute(
            "SELECT public.l2_data_plane_dependency_topology_matches(%s, %s::jsonb)",
            ("bo_topology_probe", vector),
        ).fetchone()[0] is False

        conn.execute(
            "UPDATE public.asset_registry SET depends_on=ARRAY[]::text[] WHERE asset_id='bo_topology_probe'"
        )
        assert conn.execute(
            "SELECT public.l2_data_plane_dependency_topology_matches(%s, %s::jsonb)",
            ("bo_topology_probe", vector),
        ).fetchone()[0] is False
        conn.rollback()


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
    assert a["independent_support_count"] == 1
    assert a["independent_opposition_count"] == 1
    assert {root["epistemic_class"] for root in a["evidence_roots"]} == {
        "rule_derived", "deterministic_derivation",
    }
    assert all("magnitude_semantics" in rel for rel in a["relationships"])
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

    fixture = load_fixture()
    del fixture["selected_configuration"]["paths"][0]["magnitude_semantics"]
    with pytest.raises(ValueError, match="magnitude semantics"):
        build_resource_mechanism_slice(fixture)


def test_migration_guards_replay_stale_sets_nonfinite_and_cross_layer_delete():
    migration = (
        Path(__file__).resolve().parents[3]
        / "migrations" / "1034_data_plane_l2_producer_generations.sql"
    ).read_text()
    assert "l2_data_plane_run_rows" in migration
    assert "observed_row_count" in migration
    assert "replay changed counts or semantic output" in migration
    assert "l2_data_plane_generation_is_compatible" in migration
    assert "l2_data_plane_jsonb_has_nonfinite(v_row)" in migration
    assert "assert_l2_msr_delete_safe" in migration


def test_msr_replacement_invokes_cross_layer_guard_before_delete():
    class Cursor:
        rowcount = 1

    class Conn:
        _l2_contract_test_double = True

        def __init__(self):
            self.calls = []

        def execute(self, sql, params=None):
            self.calls.append((sql, params))
            return Cursor()

    conn = Conn()
    _idempotency.replace_prior_msr_for_chart(
        conn, "11111111-1111-1111-1111-111111111111", "lahiri", ["yoga"],
    )
    guard = next(i for i, (sql, _) in enumerate(conn.calls) if "assert_l2_msr_delete_safe" in sql)
    first_delete = next(i for i, (sql, _) in enumerate(conn.calls) if sql.startswith("DELETE"))
    assert guard < first_delete
