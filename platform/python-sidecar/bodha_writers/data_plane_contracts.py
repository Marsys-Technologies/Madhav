"""L2 Bodha producer boundary for DP-SD-015.

The frozen :class:`WriterBase` API remains unchanged. Registered ``bo_*``
writers opt into this decorator, which resolves their exact completed upstream
L1/L2 generation vector, opens one append-only L2 generation partition, lets
the legacy active-table writer run, and completes the partition only after the
writer succeeds. Migration 1034 snapshots inserted/updated output rows under
the transaction-local generation context.

Ordinary unit-test connection doubles are deliberately ignored. Contract
tests must opt in with ``_l2_contract_test_double = True`` so a small fake can
never be mistaken for persistence evidence.
"""
from __future__ import annotations

import functools
import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence, TypeVar


CONTRACT_VERSION = "MADHAV_DATA_PLANE_L2_BODHA_CONTRACT/2.0"
ACCEPTED_L0_RELEASE = "f6fed12c794224329f6b3b436f8b1b814499d06d"
ACCEPTED_L1_TERMINAL = "18503e9c2dbb140f5d17b4bc34a5f6d087f97c38"
ACCEPTED_L1_SLICE_DIGEST = (
    "25c46b559def7e1a9f8e1a05114be5a6c306a846a23b2665b1b5c917128d3279"
)

CURRENT_WRITERS = (
    "bo_laksana", "bo_laksana_rerank", "bo_bimba", "bo_karanajala",
    "bo_cgm_paths", "bo_cgm_motifs", "bo_yantra_mechanism", "bo_sangati",
    "bo_cdlm_summary", "bo_pratijna", "bo_arudha", "bo_special_lagna",
    "bo_sudarshana", "bo_vargottama_dhana", "bo_nakshatra_semantic",
    "bo_upaya", "bo_samskara", "bo_anveshana", "bo_drishti",
    "bo_chart_gestalt", "bo_samvada", "bo_pramana_mapa", "bo_grounding",
)
HISTORICAL_FORMAL_WRITERS = tuple(x for x in CURRENT_WRITERS if x != "bo_grounding")

_ROLE = {
    "bo_laksana": "structural_proposition",
    "bo_laksana_rerank": "same_evidence_navigation",
    "bo_bimba": "configuration_node",
    "bo_karanajala": "signed_relationship",
    "bo_cgm_paths": "ordered_path_candidate",
    "bo_cgm_motifs": "motif_candidate",
    "bo_yantra_mechanism": "mechanism_candidate",
    "bo_sangati": "multidomain_linkage",
    "bo_cdlm_summary": "navigation_summary",
    "bo_pratijna": "occurrence_condition_ledger",
    "bo_arudha": "reference_frame_proposition",
    "bo_special_lagna": "specialized_proposition",
    "bo_sudarshana": "correlated_static_frame",
    "bo_vargottama_dhana": "specialized_proposition",
    "bo_nakshatra_semantic": "symbolic_structural_proposition",
    "bo_upaya": "attributed_practice_eligibility",
    "bo_samskara": "content_addressed_navigation",
    "bo_anveshana": "discovery_candidate",
    "bo_drishti": "question_obligation",
    "bo_chart_gestalt": "whole_chart_pointer",
    "bo_samvada": "corrected_navigation_digest",
    "bo_pramana_mapa": "scoped_quality_detector",
    "bo_grounding": "source_rule_match",
}

_VOLATILE_IDENTITY_KEYS = frozenset({
    "build_id", "generation_id", "computed_at", "created_at", "updated_at",
    "recorded_at", "scored_at", "query_time", "captured_at", "opened_at",
    "completed_at",
})
_SEMANTIC_UUID_NAMESPACE = uuid.UUID("125f1f55-9bb7-55e4-a953-8bea42e2a17f")


class ContractError(RuntimeError):
    """The runtime invocation cannot make an exact L2 producer claim."""


@dataclass(frozen=True)
class ProducerObservation:
    asset_id: str
    chart_id: str
    build_id: str
    generation_id: str
    calculation_context_id: str
    source_digest: str
    role: str
    partition_key: str
    calculation_context: Mapping[str, Any]
    dependency_vector: Sequence[Mapping[str, Any]]


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _canonical(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("non-finite values are forbidden in L2 identity material")
    return value


def content_digest(value: Any) -> str:
    encoded = json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _volatile_paths(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in _VOLATILE_IDENTITY_KEYS:
                found.append(child_path)
            found.extend(_volatile_paths(child, child_path))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            found.extend(_volatile_paths(child, f"{path}[{index}]"))
    return found


def stable_structural_id(kind: str, semantic_payload: Mapping[str, Any]) -> str:
    """Return a build/time-independent content identity."""
    if not kind or not semantic_payload:
        raise ValueError("structural identity requires kind and semantic payload")
    volatile = _volatile_paths(semantic_payload)
    if volatile:
        raise ValueError(f"volatile structural identity fields: {volatile}")
    return f"l2:{kind}:{content_digest(semantic_payload)[:32]}"


def stable_semantic_uuid(kind: str, semantic_payload: Mapping[str, Any]) -> str:
    """Return a canonical UUID for a semantic row/object identity."""
    return str(uuid.uuid5(
        _SEMANTIC_UUID_NAMESPACE,
        stable_structural_id(kind, semantic_payload),
    ))


def _contract_sql_enabled(conn: Any) -> bool:
    if getattr(conn, "_l2_contract_test_double", False):
        return True
    return conn.__class__.__module__.split(".", 1)[0] == "psycopg"


def _as_mapping(row: Any, description: Any = None) -> dict[str, Any]:
    if isinstance(row, Mapping):
        return dict(row)
    if description is None:
        raise ContractError("L2 context query returned an unlabelled row")
    names = [getattr(column, "name", column[0]) for column in description]
    return dict(zip(names, row, strict=True))


def _fetchall(cur: Any) -> list[dict[str, Any]]:
    return [
        _as_mapping(row, getattr(cur, "description", None))
        for row in cur.fetchall()
    ]


def _resolve_upstream_context(
    conn: Any,
    *,
    chart_id: str,
    asset_id: str,
    partition_key: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Resolve exact selected transitive L1/L2 dependency generations."""
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH RECURSIVE dependency_tree(asset_id) AS (
              SELECT unnest(COALESCE(depends_on, ARRAY[]::text[]))
              FROM public.asset_registry WHERE asset_id = %s
              UNION
              SELECT unnest(COALESCE(r.depends_on, ARRAY[]::text[]))
              FROM public.asset_registry r
              JOIN dependency_tree d ON d.asset_id = r.asset_id
            )
            SELECT asset_id FROM dependency_tree
            WHERE asset_id <> %s AND (asset_id LIKE 'ga_%%' OR asset_id LIKE 'bo_%%')
            ORDER BY asset_id
            """,
            (asset_id, asset_id),
        )
        dependency_assets = [str(row["asset_id"]) for row in _fetchall(cur)]
        ga_assets = [item for item in dependency_assets if item.startswith("ga_")]
        bo_assets = [item for item in dependency_assets if item.startswith("bo_")]
        if not ga_assets:
            raise ContractError(f"{asset_id} has no transitive L1 producer dependency")

        cur.execute(
            """
            SELECT h.asset_id, h.current_generation_id AS generation_id,
                   g.semantic_output_digest AS output_digest,
                   g.base_context_jsonb AS calculation_context
            FROM public.l1_data_plane_generation_heads h
            JOIN public.l1_data_plane_generations g
              ON g.chart_id = h.chart_id AND g.asset_id = h.asset_id
             AND g.generation_id = h.current_generation_id
            WHERE h.chart_id = %s::uuid AND h.asset_id = ANY(%s::text[])
              AND g.status = 'complete'
            ORDER BY h.asset_id
            """,
            (chart_id, ga_assets),
        )
        l1_rows = _fetchall(cur)
        observed_ga = {str(row["asset_id"]) for row in l1_rows}
        if observed_ga != set(ga_assets):
            missing = sorted(set(ga_assets) - observed_ga)
            raise ContractError(f"missing completed selected L1 dependencies: {missing}")

        l2_rows: list[dict[str, Any]] = []
        if bo_assets:
            cur.execute(
                """
                SELECT h.asset_id, h.current_generation_id AS generation_id,
                       g.semantic_output_digest AS output_digest,
                       g.calculation_context_jsonb AS calculation_context
                FROM public.l2_data_plane_generation_heads h
                JOIN public.data_plane_l2_producer_generations g
                  ON g.chart_id = h.chart_id AND g.asset_id = h.asset_id
                 AND g.generation_id = h.current_generation_id
                WHERE h.chart_id = %s::uuid AND h.asset_id = ANY(%s::text[])
                  AND g.state = 'complete'
                ORDER BY h.asset_id
                """,
                (chart_id, bo_assets),
            )
            l2_rows = _fetchall(cur)
            observed_bo = {str(row["asset_id"]) for row in l2_rows}
            if observed_bo != set(bo_assets):
                missing = sorted(set(bo_assets) - observed_bo)
                raise ContractError(f"missing completed selected L2 dependencies: {missing}")

    context_fields = (
        "subject_id", "chart_id", "instant_iso", "latitude_deg", "longitude_deg",
        "timezone_name", "input_precision", "frame", "node_type", "house_convention",
    )
    projected_contexts = [
        {key: row["calculation_context"].get(key) for key in context_fields}
        for row in l1_rows
    ]
    if len({content_digest(context) for context in projected_contexts}) != 1:
        raise ContractError("selected L1 generations have incompatible calculation contexts")
    base_context = projected_contexts[0]
    if str(base_context.get("chart_id")) != chart_id:
        raise ContractError("selected L1 calculation context does not match chart")
    if not base_context.get("subject_id"):
        raise ContractError("selected L1 calculation context has no subject")

    ayanamsha_id = "mixed_or_invariant"
    if partition_key.startswith("aya_") and len(partition_key) > 4:
        ayanamsha_id = partition_key[4:]
    calculation_context = {
        **base_context,
        "generation_context_id": stable_structural_id(
            "generation_context",
            {
                **base_context,
                "reference_frame": base_context.get("frame"),
                "partition_scope": "writer_declared",
            },
        ),
        "ayanamsha_id": ayanamsha_id,
        "reference_frame": base_context.get("frame"),
        "partition_scope": "writer_declared",
        "varga_id": "row_declared_or_D1",
        "partition_key": partition_key,
    }
    calculation_context["calculation_context_id"] = stable_structural_id(
        "calculation_context", calculation_context,
    )

    vector: list[dict[str, Any]] = []
    for layer, rows in (("L1", l1_rows), ("L2", l2_rows)):
        for row in rows:
            digest = str(row.get("output_digest") or "")
            if len(digest) != 64:
                raise ContractError(
                    f"selected {layer} dependency {row['asset_id']} lacks output digest"
                )
            vector.append({
                "layer": layer,
                "asset_id": str(row["asset_id"]),
                "generation_id": str(row["generation_id"]),
                "semantic_output_digest": digest,
            })
    vector.sort(key=lambda item: (item["layer"], item["asset_id"]))
    return vector, calculation_context


def _validate_config_pin(config: Mapping[str, Any], key: str, expected: Any) -> None:
    supplied = config.get(key)
    if supplied is not None and supplied != expected:
        raise ContractError(f"wrong {key} for L2 producer")


def begin_observation(
    ctx: Any,
    asset_id: str,
    source_digest: str,
    *,
    partition_key: str | None = None,
    dependency_vector: Sequence[Mapping[str, Any]] | None = None,
    calculation_context: Mapping[str, Any] | None = None,
) -> ProducerObservation:
    if asset_id not in CURRENT_WRITERS:
        raise ContractError(f"unknown L2 producer: {asset_id}")
    config = getattr(ctx, "config", None)
    if not isinstance(config, dict):
        raise ContractError("L2 producer requires a mutable context config")
    chart_id = config.get("chart_id")
    if not isinstance(chart_id, str) or not chart_id.strip():
        raise ContractError("L2 producer requires non-empty chart_id")
    build_id = getattr(ctx, "build_id", None)
    if not isinstance(build_id, str) or not build_id.strip():
        raise ContractError("L2 producer requires non-empty build_id")
    if len(source_digest) != 64 or any(c not in "0123456789abcdef" for c in source_digest):
        raise ContractError("L2 producer requires a dependency-aware SHA-256 source digest")

    _validate_config_pin(config, "accepted_l0_release", ACCEPTED_L0_RELEASE)
    _validate_config_pin(config, "accepted_l1_terminal", ACCEPTED_L1_TERMINAL)
    partition = partition_key or asset_id
    vector = list(dependency_vector or config.get("_l2_upstream_vector") or [])
    context = dict(calculation_context or config.get("_l2_calculation_context") or {})
    if not vector or not any(item.get("layer") == "L1" for item in vector):
        raise ContractError("L2 producer requires an exact completed L1 dependency vector")
    required_context = (
        "subject_id", "chart_id", "generation_context_id",
        "calculation_context_id", "ayanamsha_id", "reference_frame",
        "varga_id", "partition_key",
    )
    missing = [key for key in required_context if context.get(key) in (None, "")]
    if missing:
        raise ContractError(f"L2 producer calculation context is incomplete: {missing}")
    if str(context["chart_id"]) != chart_id or str(context["partition_key"]) != partition:
        raise ContractError("L2 producer context chart/partition mismatch")

    config.update({
        "accepted_l0_release": ACCEPTED_L0_RELEASE,
        "accepted_l1_terminal": ACCEPTED_L1_TERMINAL,
        "accepted_l1_generation_id": "l1v:" + content_digest([
            item for item in vector if item.get("layer") == "L1"
        ])[:32],
        "generation_context_id": context["generation_context_id"],
        "calculation_context_id": context["calculation_context_id"],
        "subject_id": context["subject_id"],
        "ayanamsha_id": context["ayanamsha_id"],
        "reference_frame": context["reference_frame"],
        "varga_id": context["varga_id"],
        "_l2_upstream_vector": vector,
        "_l2_calculation_context": context,
    })
    generation_id = "l2g:" + content_digest({
        "contract": CONTRACT_VERSION,
        "accepted_l0": ACCEPTED_L0_RELEASE,
        "accepted_l1_terminal": ACCEPTED_L1_TERMINAL,
        "asset_id": asset_id,
        "chart_id": chart_id,
        "source_digest": source_digest,
        "generation_context_id": context["generation_context_id"],
        "dependency_vector": vector,
    })[:40]
    observations = config.setdefault("_l2_producer_observations", {})
    observation_key = f"{asset_id}:{partition}"
    prior = observations.get(observation_key)
    if prior is not None and prior != generation_id:
        raise ContractError(f"mixed L2 generation for {asset_id}/{partition}")
    observations[observation_key] = generation_id
    return ProducerObservation(
        asset_id=asset_id,
        chart_id=chart_id,
        build_id=build_id,
        generation_id=generation_id,
        calculation_context_id=str(context["calculation_context_id"]),
        source_digest=source_digest,
        role=_ROLE[asset_id],
        partition_key=partition,
        calculation_context=context,
        dependency_vector=vector,
    )


def _expected_partition_count(writer: Any, ctx: Any) -> int:
    if not getattr(writer, "has_substeps", False):
        return 1
    count = len(writer.plan_substeps(ctx))
    if count < 1:
        raise ContractError(f"{writer.asset_id} declared no producer partitions")
    return count


def _open_generation(
    ctx: Any,
    observation: ProducerObservation,
    *,
    expected_partitions: int,
) -> None:
    correction_of = (ctx.config or {}).get("l2_correction_of_generation_id")
    with ctx.db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              set_config('madhav.l2_asset_id', %s, true),
              set_config('madhav.l2_chart_id', %s, true),
              set_config('madhav.l2_generation_id', %s, true),
              set_config('madhav.l2_partition_key', %s, true),
              set_config('madhav.l2_build_id', %s, true),
              set_config('madhav.l2_contract_version', %s, true)
            """,
            (
                observation.asset_id, observation.chart_id,
                observation.generation_id, observation.partition_key,
                observation.build_id, CONTRACT_VERSION,
            ),
        )
        cur.execute(
            """
            SELECT public.open_l2_data_plane_generation(
              %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s,
              %s::jsonb, %s::jsonb, %s
            )
            """,
            (
                observation.chart_id, observation.asset_id,
                observation.generation_id, observation.partition_key,
                expected_partitions, observation.build_id, correction_of,
                CONTRACT_VERSION, observation.source_digest,
                json.dumps(observation.calculation_context, sort_keys=True),
                json.dumps(observation.dependency_vector, sort_keys=True),
                observation.role,
            ),
        )
        cur.execute(
            "SELECT public.bind_l2_exact_inputs(%s::uuid, %s::jsonb)",
            (
                observation.chart_id,
                json.dumps(observation.dependency_vector, sort_keys=True),
            ),
        )


def _complete_partition(ctx: Any, observation: ProducerObservation, result: Any) -> None:
    with ctx.db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT public.complete_l2_data_plane_partition(
              %s::uuid, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                observation.chart_id, observation.asset_id,
                observation.generation_id, observation.partition_key,
                observation.build_id,
                int(getattr(result, "rows_inserted", 0)),
                int(getattr(result, "rows_updated", 0)),
                int(getattr(result, "rows_skipped", 0)),
            ),
        )


def _writer_source_digest(asset_id: str) -> str:
    from pipeline.orchestrator.asset_runner import get_writer_source_hash

    return get_writer_source_hash(asset_id)


T = TypeVar("T")


def l2_producer(asset_id: str) -> Callable[[T], T]:
    """Adopt the common L2 contract without altering ``WriterBase``."""
    if asset_id not in CURRENT_WRITERS:
        raise ContractError(f"unknown L2 producer decorator identity: {asset_id}")

    def decorate(cls: T) -> T:
        declared_asset_id = getattr(cls, "asset_id", None)
        if declared_asset_id not in (None, "", asset_id):
            raise ContractError(f"decorator/class asset mismatch: {asset_id}")
        if not declared_asset_id:
            setattr(cls, "asset_id", asset_id)
        owned_entries = [
            (name, cls.__dict__[name])
            for name in ("run", "run_substep")
            if name in cls.__dict__
        ]
        if not owned_entries:
            raise ContractError(f"L2 producer {asset_id} has no owned execution entry")

        def wrap_entry(name: str, original: Callable[..., Any]) -> Callable[..., Any]:
            @functools.wraps(original)
            def contracted(self: Any, ctx: Any, *args: Any, **kwargs: Any) -> Any:
                if getattr(ctx, "dry_run", False) or not _contract_sql_enabled(ctx.db_conn):
                    return original(self, ctx, *args, **kwargs)
                partition_key = asset_id
                if name == "run_substep" and args:
                    partition_key = str(getattr(args[0], "key", ""))
                if not partition_key:
                    raise ContractError(f"{asset_id} substep has no partition key")
                chart_id = str((ctx.config or {}).get("chart_id") or "")
                if not chart_id:
                    raise ContractError("L2 runtime producer context requires chart_id")
                source_digest = _writer_source_digest(asset_id)
                vector, calculation_context = _resolve_upstream_context(
                    ctx.db_conn,
                    chart_id=chart_id,
                    asset_id=asset_id,
                    partition_key=partition_key,
                )
                observation = begin_observation(
                    ctx,
                    asset_id,
                    source_digest,
                    partition_key=partition_key,
                    dependency_vector=vector,
                    calculation_context=calculation_context,
                )
                _open_generation(
                    ctx,
                    observation,
                    expected_partitions=_expected_partition_count(self, ctx),
                )
                result = original(self, ctx, *args, **kwargs)
                setattr(result, "_l2_partition_key", partition_key)
                _complete_partition(ctx, observation, result)
                suffix = (
                    f"l2_generation={observation.generation_id} "
                    f"partition={partition_key} temporal=UNAVAILABLE_AT_L2"
                )
                result.notes = f"{result.notes}; {suffix}" if result.notes else suffix
                return result

            contracted.__l2_data_plane_contract__ = True  # type: ignore[attr-defined]
            return contracted

        for entry_name, entry in owned_entries:
            setattr(cls, entry_name, wrap_entry(entry_name, entry))
        setattr(cls, "l2_contract_version", CONTRACT_VERSION)
        setattr(cls, "l2_producer_role", _ROLE[asset_id])
        return cls

    return decorate
