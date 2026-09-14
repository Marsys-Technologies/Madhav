"""L2 Bodha data-plane producer contract (DP-SD-015).

This module conforms to, and does not extend, the frozen WriterBase interface.
The decorator validates immutable upstream pins, assigns one observation
generation per chart/build, and records an append-only producer receipt in the
caller's transaction.  Stable structural identities deliberately exclude the
observation build and wall clock.
"""
from __future__ import annotations

import functools
import hashlib
import inspect
import json
from dataclasses import dataclass
from typing import Any, Callable, Mapping, TypeVar


CONTRACT_VERSION = "MADHAV_DATA_PLANE_L2_BODHA_CONTRACT/1.0"
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


@dataclass(frozen=True)
class ProducerObservation:
    asset_id: str
    chart_id: str
    build_id: str
    generation_id: str
    calculation_context_id: str
    source_digest: str
    role: str


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _canonical(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, tuple):
        return [_canonical(v) for v in value]
    if isinstance(value, list):
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


def stable_structural_id(kind: str, semantic_payload: Mapping[str, Any]) -> str:
    """Return a build/time-independent content identity."""
    if not kind or not semantic_payload:
        raise ValueError("structural identity requires kind and semantic payload")
    forbidden = {"build_id", "computed_at", "created_at", "updated_at", "query_time"}
    overlap = forbidden.intersection(semantic_payload)
    if overlap:
        raise ValueError(f"volatile structural identity fields: {sorted(overlap)}")
    return f"l2:{kind}:{content_digest(semantic_payload)[:32]}"


def _context_projection(config: Mapping[str, Any]) -> dict[str, Any]:
    allowed = (
        "chart_id", "subject_id", "calculation_context_id", "resource_config_id",
        "accepted_l1_generation_id", "ayanamsha_id", "reference_frame", "varga_id",
    )
    return {key: config[key] for key in allowed if key in config}


def begin_observation(ctx: Any, asset_id: str, source_digest: str) -> ProducerObservation:
    if asset_id not in CURRENT_WRITERS:
        raise ValueError(f"unknown L2 producer: {asset_id}")
    config = getattr(ctx, "config", None)
    if not isinstance(config, dict):
        raise ValueError("L2 producer requires a mutable context config")
    chart_id = config.get("chart_id")
    if not isinstance(chart_id, str) or not chart_id.strip():
        raise ValueError("L2 producer requires non-empty chart_id")
    build_id = getattr(ctx, "build_id", None)
    if not isinstance(build_id, str) or not build_id.strip():
        raise ValueError("L2 producer requires non-empty build_id")

    supplied_l0 = config.get("accepted_l0_release", ACCEPTED_L0_RELEASE)
    supplied_l1 = config.get("accepted_l1_terminal", ACCEPTED_L1_TERMINAL)
    if supplied_l0 != ACCEPTED_L0_RELEASE:
        raise ValueError("wrong accepted L0 release for L2 producer")
    if supplied_l1 != ACCEPTED_L1_TERMINAL:
        raise ValueError("wrong accepted L1 terminal for L2 producer")

    context_projection = _context_projection(config)
    calculation_context_id = config.get("calculation_context_id") or stable_structural_id(
        "calculation_context", context_projection,
    )
    generation_id = "l2g:" + content_digest({
        "contract": CONTRACT_VERSION,
        "accepted_l0": ACCEPTED_L0_RELEASE,
        "accepted_l1": ACCEPTED_L1_TERMINAL,
        "chart_id": chart_id,
        "build_id": build_id,
        "calculation_context_id": calculation_context_id,
    })[:32]
    observations = config.setdefault("_l2_producer_observations", {})
    prior = observations.get(asset_id)
    if prior is not None and prior != generation_id:
        raise ValueError(f"mixed L2 generation for {asset_id}")
    observations[asset_id] = generation_id
    return ProducerObservation(
        asset_id=asset_id,
        chart_id=chart_id,
        build_id=build_id,
        generation_id=generation_id,
        calculation_context_id=calculation_context_id,
        source_digest=source_digest,
        role=_ROLE[asset_id],
    )


_RECEIPT_SQL = """
INSERT INTO data_plane_l2_producer_generations (
  generation_id, asset_id, partition_key, chart_id, build_id, contract_version,
  accepted_l0_release, accepted_l1_terminal, calculation_context_id,
  producer_role, source_digest, rows_inserted, rows_updated, rows_skipped,
  temporal_semantics_status, state
) VALUES (
  %(generation_id)s, %(asset_id)s, %(partition_key)s, %(chart_id)s, %(build_id)s, %(contract_version)s,
  %(accepted_l0_release)s, %(accepted_l1_terminal)s, %(calculation_context_id)s,
  %(producer_role)s, %(source_digest)s, %(rows_inserted)s, %(rows_updated)s,
  %(rows_skipped)s, 'UNAVAILABLE_AT_L2', 'completed'
)
ON CONFLICT (generation_id, asset_id, partition_key) DO UPDATE SET
  rows_inserted = EXCLUDED.rows_inserted,
  rows_updated = EXCLUDED.rows_updated,
  rows_skipped = EXCLUDED.rows_skipped
WHERE data_plane_l2_producer_generations.state <> 'completed'
"""


def _record_receipt(ctx: Any, observation: ProducerObservation, result: Any) -> None:
    params = {
        "generation_id": observation.generation_id,
        "asset_id": observation.asset_id,
        "partition_key": getattr(result, "_l2_partition_key", observation.asset_id),
        "chart_id": observation.chart_id,
        "build_id": observation.build_id,
        "contract_version": CONTRACT_VERSION,
        "accepted_l0_release": ACCEPTED_L0_RELEASE,
        "accepted_l1_terminal": ACCEPTED_L1_TERMINAL,
        "calculation_context_id": observation.calculation_context_id,
        "producer_role": observation.role,
        "source_digest": observation.source_digest,
        "rows_inserted": int(getattr(result, "rows_inserted", 0)),
        "rows_updated": int(getattr(result, "rows_updated", 0)),
        "rows_skipped": int(getattr(result, "rows_skipped", 0)),
    }
    conn = ctx.db_conn
    if hasattr(conn, "execute"):
        conn.execute(_RECEIPT_SQL, params)
    else:
        with conn.cursor() as cur:
            cur.execute(_RECEIPT_SQL, params)


T = TypeVar("T")


def l2_producer(asset_id: str) -> Callable[[T], T]:
    """Adopt the common L2 contract without altering WriterBase."""
    if asset_id not in CURRENT_WRITERS:
        raise ValueError(f"unknown L2 producer decorator identity: {asset_id}")

    def decorate(cls: T) -> T:
        declared_asset_id = getattr(cls, "asset_id", None)
        if declared_asset_id not in (None, "", asset_id):
            raise ValueError(f"decorator/class asset mismatch: {asset_id}")
        if not declared_asset_id:
            setattr(cls, "asset_id", asset_id)
        owned_entries = [
            (name, cls.__dict__[name])
            for name in ("run", "run_substep")
            if name in cls.__dict__
        ]
        if not owned_entries:
            raise ValueError(f"L2 producer {asset_id} has no owned execution entry")
        source_digest = hashlib.sha256(
            "\n".join(inspect.getsource(fn) for _, fn in owned_entries).encode("utf-8")
        ).hexdigest()

        def wrap_entry(name: str, original: Callable[..., Any]) -> Callable[..., Any]:
            @functools.wraps(original)
            def contracted(self: Any, ctx: Any, *args: Any, **kwargs: Any) -> Any:
                partition_key = asset_id
                if name == "run_substep" and args:
                    partition_key = str(getattr(args[0], "key", asset_id))
                observation = begin_observation(ctx, asset_id, source_digest)
                result = original(self, ctx, *args, **kwargs)
                setattr(result, "_l2_partition_key", partition_key)
                if not getattr(ctx, "dry_run", False):
                    _record_receipt(ctx, observation, result)
                suffix = (
                    f"l2_generation={observation.generation_id} "
                    f"partition={partition_key} temporal=UNAVAILABLE_AT_L2"
                )
                result.notes = f"{result.notes}; {suffix}" if result.notes else suffix
                return result
            return contracted

        for entry_name, entry in owned_entries:
            setattr(cls, entry_name, wrap_entry(entry_name, entry))
        setattr(cls, "l2_contract_version", CONTRACT_VERSION)
        setattr(cls, "l2_producer_role", _ROLE[asset_id])
        return cls

    return decorate
