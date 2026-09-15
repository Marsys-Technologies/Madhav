from __future__ import annotations

import json
import inspect
import os
from pathlib import Path
from types import SimpleNamespace

from bodha_writers.formulas import ResonanceInputs, resonance_score_v1
from pipeline.orchestrator.writers import bo_pramana_mapa
from pipeline.orchestrator.writers import bo_pratijna, bo_samskara, bo_samvada, bo_upaya
from pipeline.orchestrator.writers.bo_sangati import _build_cdlm_cells


def _signal(
    signal_id: str,
    *,
    root: str,
    signal_class: str = "dosha",
    contradictions: list[str] | None = None,
    valence: str = "malefic",
) -> dict:
    return {
        "signal_id": signal_id,
        "signal_type_class": signal_class,
        "signal_tradition": "parashari",
        "domains_affected_array": ["career", "wealth"],
        "computed_salience": 0.5,
        "verification_pass_status": "two_pass_verified",
        "salience_formula_version": "v2",
        "constituent_facts_array": [root],
        "shared_factor_keys_jsonb": None,
        "contradicts_signals_array": contradictions,
        "valence": valence,
        "classical_sources_jsonb": {"rule_ids": ["rule-1"]},
    }


def test_resonance_is_invariant_to_l3_dasha_input():
    base = ResonanceInputs(shadbala_normalized=0.25, dasha_proximity_activation_score=0.0)
    temporally_claimed = ResonanceInputs(
        shadbala_normalized=0.25, dasha_proximity_activation_score=1.0,
    )
    unavailable = ResonanceInputs(
        shadbala_normalized=0.25, dasha_proximity_activation_score=None,
    )
    assert resonance_score_v1(base) == resonance_score_v1(temporally_claimed)
    assert resonance_score_v1(base) == resonance_score_v1(unavailable)


def test_cdlm_independence_uses_root_ancestry_and_dosha_is_not_automatically_negative():
    signals = [
        _signal("00000000-0000-0000-0000-000000000001", root="fact:shared"),
        _signal("00000000-0000-0000-0000-000000000002", root="fact:shared"),
    ]
    rows = _build_cdlm_cells(
        "00000000-0000-0000-0000-000000000010",
        "lahiri_chitrapaksha",
        "00000000-0000-0000-0000-000000000020",
        signals,
        set(),
        "2026-09-14T00:00:00+00:00",
    )
    cell = next(row for row in rows if row["domain_row"] == "career" and row["domain_col"] == "wealth")
    assert cell["shared_signal_count"] == 2
    assert cell["shared_factor_count"] == 1
    assert json.loads(cell["shared_factor_keys_jsonb"])["shared_root_groups"] == ["fact:shared"]
    assert cell["negative_contribution"] == 0
    assert cell["cross_domain_contradiction_flag"] is False

    signals[0]["contradicts_signals_array"] = [signals[1]["signal_id"]]
    qualified = _build_cdlm_cells(
        "00000000-0000-0000-0000-000000000010",
        "lahiri_chitrapaksha",
        "00000000-0000-0000-0000-000000000020",
        signals,
        set(),
        "2026-09-14T00:00:00+00:00",
    )[0]
    assert qualified["negative_contribution"] > 0
    assert qualified["cross_domain_contradiction_flag"] is True


def test_quality_detectors_have_reachable_false_branches(monkeypatch):
    def violations(_conn, sql, _params):
        if "bodha_question_lenses" in sql:
            return 1
        if "bodha_cdlm_cells" in sql:
            return 2
        if "bodha_discoveries" in sql:
            return 3
        if "l2_data_plane_row_snapshots" in sql:
            return 4
        if "bodha_cgm_edges" in sql:
            return 5
        raise AssertionError(sql)

    monkeypatch.setattr(bo_pramana_mapa, "_count_one", violations)
    result = bo_pramana_mapa.detect_l2_contract_integrity(object(), "chart-1")
    assert result["no_pre_answer"]["pass"] is False
    assert result["ledger_independence_and_duplicate_root"]["pass"] is False
    assert result["discovery_grounding"]["pass"] is False
    assert result["context_generation"]["pass"] is False
    assert result["signed_relation_and_cancellation"]["pass"] is False


def test_lel_detector_is_self_contained_and_serving_refresh_is_passive():
    assert "life_events" not in bo_pramana_mapa._LEL_TERM_B_SQL
    assert "source_l1_asset" in bo_pramana_mapa._LEL_TERM_B_SQL
    assert "source_l1_asset IS NULL" in bo_pramana_mapa._LEL_TERM_B_SQL
    assert "jsonb_exists_any" not in bo_pramana_mapa._LEL_TERM_C_SQL
    assert "configuration_jsonb::text" in bo_pramana_mapa._LEL_TERM_C_SQL
    run_source = inspect.getsource(bo_pramana_mapa.BoPramanaMapa.run)
    assert "_refresh_mv(" not in run_source
    assert "mv_cdlm_dasha_window_lookup" not in run_source


def test_quality_context_detector_rejects_stale_selected_heads():
    assert "l2_data_plane_generation_is_compatible" in bo_pramana_mapa._CONTEXT_GENERATION_SQL
    assert "declared_upstream" in bo_pramana_mapa._CONTEXT_GENERATION_SQL
    assert "JOIN selected_upstream" in bo_pramana_mapa._CONTEXT_GENERATION_SQL


def test_quality_context_detector_database_negative_for_topology_staleness():
    database_url = os.environ.get("L2_CONTRACT_DATABASE_URL")
    if not database_url:
        import pytest
        pytest.skip("L2_CONTRACT_DATABASE_URL not supplied for disposable PostgreSQL proof")
    import psycopg

    chart_id = "20000000-0000-0000-0000-000000000001"
    vector = json.dumps([{
        "layer": "L1", "asset_id": "ga_detector_a",
        "generation_id": "l1-a", "semantic_output_digest": "a" * 64,
    }])
    with psycopg.connect(database_url) as conn:
        conn.execute(
            """INSERT INTO public.asset_registry(asset_id, depends_on)
               VALUES ('ga_detector_a', ARRAY[]::text[]),
                      ('ga_detector_b', ARRAY[]::text[]),
                      ('bo_detector_probe', ARRAY['ga_detector_a']::text[]),
                      ('bo_pramana_mapa', ARRAY['bo_detector_probe']::text[])
               ON CONFLICT (asset_id) DO UPDATE SET depends_on=EXCLUDED.depends_on"""
        )
        conn.execute(
            """INSERT INTO public.l1_data_plane_generations
                 (chart_id, asset_id, generation_id, contract_version,
                  l0_semantic_release_id, l0_semantic_release_digest,
                  l0_config_generation_id, l0_config_digest,
                  base_context_jsonb, expected_partitions, completed_partitions,
                  status, semantic_output_digest, completed_at)
               VALUES (%s, 'ga_detector_a', 'l1-a',
                       'l1.data-plane.contract.1.0',
                       'l0.semantic.2026-09-13.1', %s,
                       'l0-resource-config-g1', %s,
                       '{}'::jsonb, 1, 1, 'complete', %s, clock_timestamp())""",
            (
                chart_id,
                "665096a74a59ea7e0e50ce98fc685899b89f325aca0d91c214f0040e4d259dd1",
                "d516aecff9d4e05d929dc7fd71a113fd5c53d1f6ea1eb2582caafd3a339c279a",
                "a" * 64,
            ),
        )
        conn.execute(
            """INSERT INTO public.l1_data_plane_generation_heads
                 (chart_id, asset_id, current_generation_id)
               VALUES (%s, 'ga_detector_a', 'l1-a')""",
            (chart_id,),
        )
        conn.execute(
            """INSERT INTO public.data_plane_l2_producer_generations
                 (chart_id, asset_id, generation_id, initial_build_id,
                  contract_version, accepted_l0_release, accepted_l1_terminal,
                  calculation_context_id, calculation_context_jsonb,
                  dependency_vector_jsonb, producer_role, source_digest,
                  expected_partitions, completed_partitions, state,
                  semantic_output_digest, completed_at)
               VALUES (%s, 'bo_detector_probe', 'l2-a', 'build-a',
                       'MADHAV_DATA_PLANE_L2_BODHA_CONTRACT/2.0', %s, %s,
                       'ctx-a', '{}'::jsonb, %s::jsonb, 'quality', %s,
                       1, 1, 'complete', %s, clock_timestamp())""",
            (
                chart_id,
                "f6fed12c794224329f6b3b436f8b1b814499d06d",
                "18503e9c2dbb140f5d17b4bc34a5f6d087f97c38",
                vector, "c" * 64, "b" * 64,
            ),
        )
        conn.execute(
            """INSERT INTO public.l2_data_plane_generation_heads
                 (chart_id, asset_id, current_generation_id)
               VALUES (%s, 'bo_detector_probe', 'l2-a')""",
            (chart_id,),
        )
        # Runtime ordering: while a replacement scorecard is being built, the
        # producer's own previous head may be stale. It is not an upstream
        # dependency and must not make the candidate scorecard falsely red.
        conn.execute(
            """INSERT INTO public.data_plane_l2_producer_generations
                 (chart_id, asset_id, generation_id, initial_build_id,
                  contract_version, accepted_l0_release, accepted_l1_terminal,
                  calculation_context_id, calculation_context_jsonb,
                  dependency_vector_jsonb, producer_role, source_digest,
                  expected_partitions, completed_partitions, state,
                  semantic_output_digest, completed_at)
               VALUES (%s, 'bo_pramana_mapa', 'l2-stale-self', 'build-old',
                       'MADHAV_DATA_PLANE_L2_BODHA_CONTRACT/2.0', %s, %s,
                       'ctx-old', '{}'::jsonb, '[]'::jsonb, 'quality', %s,
                       1, 1, 'complete', %s, clock_timestamp())""",
            (
                chart_id,
                "f6fed12c794224329f6b3b436f8b1b814499d06d",
                "18503e9c2dbb140f5d17b4bc34a5f6d087f97c38",
                "d" * 64, "e" * 64,
            ),
        )
        conn.execute(
            """INSERT INTO public.l2_data_plane_generation_heads
                 (chart_id, asset_id, current_generation_id)
               VALUES (%s, 'bo_pramana_mapa', 'l2-stale-self')""",
            (chart_id,),
        )
        assert bo_pramana_mapa._count_one(
            conn, bo_pramana_mapa._CONTEXT_GENERATION_SQL, [chart_id],
        ) == 0

        conn.execute(
            """UPDATE public.asset_registry
               SET depends_on=ARRAY['ga_detector_a','ga_detector_b']::text[]
               WHERE asset_id='bo_detector_probe'"""
        )
        assert bo_pramana_mapa._count_one(
            conn, bo_pramana_mapa._CONTEXT_GENERATION_SQL, [chart_id],
        ) == 1
        conn.rollback()


def test_samvada_preserves_serving_view_without_ddl():
    class Conn:
        def __init__(self):
            self.calls = []

        def execute(self, sql, params=None):
            self.calls.append((sql, params))

    conn = Conn()
    result = bo_samvada.BoSamvadaWriter().run(SimpleNamespace(
        dry_run=False, db_conn=conn, config={}, build_id="test-build",
    ))
    assert result.rows_inserted == 0
    assert result.rows_skipped == 1
    assert conn.calls == []


def test_samvada_passive_receipt_cannot_promote_legacy_view_rows(monkeypatch):
    from pipeline.orchestrator import asset_runner as ar
    from tests.test_d16_state_write_defect import (
        FakeConn, FakeCursor, _final_rows_written, _final_state, _patch_common,
    )

    events = []
    _patch_common(monkeypatch, bo_samvada.BoSamvadaWriter, events)
    legacy_count_sql = "SELECT count(*) FROM vw_chart_digest WHERE chart_id = $1"
    cur = FakeCursor(rows_present=5, count_sql=legacy_count_sql, target_floor=0)
    ar._run_data_writer(
        FakeConn(), cur, "run-passive", "chart-passive", "bo_samvada",
    )
    assert _final_state(cur) == "lit"
    assert _final_rows_written(cur) == 0
    assert not any("vw_chart_digest" in sql for sql, _params in cur.executed)

    migration = (
        Path(__file__).resolve().parents[3]
        / "supabase/migrations/1036_data_plane_l2_producer_generations.sql"
    ).read_text()
    assert "target_floor IS DISTINCT FROM 0" in migration
    assert "count_sql IS DISTINCT FROM 'SELECT 0 AS count'" in migration
    assert (
        "E1036_PREFLIGHT_BO_SAMVADA: registry transition was not performed by "
        "DBA preflight"
    ) in migration
    assert "asset_output_digest_specs" in migration
    assert "asset_id='bo_samvada' AND retired_at IS NULL" in migration
    assert (
        "E1036_PREFLIGHT_BO_SAMVADA: digest specification was not retired by "
        "DBA preflight"
    ) in migration


class _NoMutationConn:
    def execute(self, *_args, **_kwargs):
        raise AssertionError("dry run attempted SQL mutation")

    def cursor(self):
        raise AssertionError("dry run attempted cursor mutation")


def test_pratijna_and_upaya_dry_run_before_every_mutation():
    ctx = SimpleNamespace(
        dry_run=True,
        db_conn=_NoMutationConn(),
        config={"chart_id": "00000000-0000-0000-0000-000000000001"},
        build_id="dry-run",
    )
    pratijna = bo_pratijna.BoPratijnaWriter().run(ctx)
    upaya = bo_upaya.BoUpayaWriter().run(ctx)
    assert pratijna.rows_inserted == 0
    assert upaya.rows_inserted == 0


def test_samskara_reuse_is_immutable_and_partial_batches_fail_closed():
    reuse_source = inspect.getsource(bo_samskara._fetch_existing_embeddings)
    assert "l2_data_plane_row_snapshots" in reuse_source
    assert "l2_data_plane_generation_is_compatible" in reuse_source
    assert "AS MATERIALIZED" in reuse_source
    assert reuse_source.count("l2_data_plane_generation_is_compatible") == 1
    run_source = inspect.getsource(bo_samskara.BoSamskaraWriter.run_substep)
    assert "refusing a partial generation" in run_source


def _pratijna_score(status: str):
    return SimpleNamespace(
        status=status,
        rubric_version="rubric-v1",
        occurrence_label="MODERATE",
        condition_label="AFFLICTED",
        occurrence_pre_denial=0.5,
        occurrence=0.5,
        condition=2.0,
        engine_version="engine-v1",
        weights={},
        factor_ledger=[],
        denials=[],
        condition_ledger=[],
        provenance={},
    )


def test_pratijna_persists_units_and_polarities_for_value_and_missingness():
    for status in ("scored", "no_evidence"):
        row = bo_pratijna._row_for_score(
            chart_id="chart", aya="lahiri", build_id="build",
            event_class_id="event", score=_pratijna_score(status), now="now",
        )
        derivation = json.loads(row["derivation"])
        assert derivation["occurrence_unit"] == "probability_like_structural_score_0_1"
        assert derivation["occurrence_polarity"] == "higher_is_more_formed"
        assert derivation["condition_unit"] == "affliction_0_10"
        assert derivation["condition_polarity"] == "higher_is_more_afflicted"
