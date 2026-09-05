#!/usr/bin/env python3
"""Create one exact frozen Nirmana campaign wave and dispatch it safely.

The command is rollback-only unless ``--commit`` and the explicit confirmation
token are supplied. It never records campaign acceptance evidence; verification
and acceptance remain a separate responsibility after the production run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Mapping, Sequence


CAMPAIGN_ID = "nirmana-elevation"
DEFAULT_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
DEFAULT_DEFINITION_REVISION = "t0-2026-08-25-4a78a5c4"
CONFIRMATION = "NIRMANA_CAMPAIGN_WAVE"
LAYERS = frozenset({"L0", "L1", "L2", "L3", "L4", "L5"})
LAYER_RANK = {f"L{index}": index for index in range(6)}
REGISTRY_LAYER = {
    "L0": "brahmagyan",
    "L1": "ganita",
    "L2": "bodha",
    "L3": "kala",
    "L4": "phala",
    "L5": "mimamsa",
}
REGISTRY_CONTRACT_FIELDS = (
    "sort_order",
    "scope",
    "asset_kind",
    "catalog_status",
    "is_active",
    "has_writer",
    "target_table",
    "count_sql",
    "integrity_check_sql",
    "health_probe",
    "natural_key_partition",
    "superseded_by",
    "data_disposition",
    "dead_flag",
)
# Charter C5's ratified concurrency budget. Until v2.1 this guard was an unconditional
# `if active:` -- refuse if ANY build run is in flight anywhere -- which was correct when
# the campaign ran one wave at a time by design, and which makes slots 2 and 3 of the
# charter's published three-slot ledger unreachable: the second session to claim a slot
# gets a RuntimeError after posting a valid claim.
#
# The value is measured, not inherited. Cloud SQL `max_connections` is 50 with 9 in use
# at the time of writing (4 reserved for cloudsqladmin), so three concurrent build runs
# sit well inside the budget the charter derived the number from. Heavy/monster writers
# count double and run solo -- that remains ledger-enforced on the coordination issue,
# because "is this writer a monster" is a judgement the dispatcher cannot make from the
# manifest. Raising this constant without re-measuring headroom would be exactly the
# unearned-signal move the campaign's doctrines forbid.
MAX_CONCURRENT_CAMPAIGN_RUNS = 3


BUILD_AUTHORIZING_VERDICTS = frozenset(
    {
        "optimize",
        "correct",
        "optimize_and_correct",
        "examined_and_already_efficient",
    }
)
WRITER_DIGESTS_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "generated"
    / "nirmana-writer-digests.json"
)
ANALYSIS_LAYER_PINS_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "generated"
    / "nirmana-analysis-layer-pins.json"
)


def _stable_json(value: object, *, ensure_ascii: bool) -> str:
    return json.dumps(
        value,
        ensure_ascii=ensure_ascii,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256_json(value: object, *, ensure_ascii: bool) -> str:
    return hashlib.sha256(
        _stable_json(value, ensure_ascii=ensure_ascii).encode("utf-8")
    ).hexdigest()


def _valid_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _valid_git_commit_source(row: Mapping[str, Any]) -> bool:
    source_ref = row.get("source_ref")
    return (
        row.get("source_kind") == "git_commit"
        and isinstance(source_ref, str)
        and source_ref.startswith("git:")
        and len(source_ref) == 44
        and all(char in "0123456789abcdef" for char in source_ref[4:])
    )


def _valid_git_commit_sha(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 40
        and all(char in "0123456789abcdef" for char in value)
    )


def _load_layer_receipt_pin(layer: str) -> dict[str, Any]:
    """Read the checked-in receipt grounding pin for one layer, or fail closed.

    Reads the generated pin record the TypeScript receipt module also consumes,
    so a changed writer inventory cannot authorize a rebuild until that layer's
    convergence is explicitly reviewed.

    This used to regex-scrape `export const NIRMANA_L0_... = '...' as const` out
    of the TypeScript source.  Both sides now read the same generated JSON: one
    source of truth, no parser to drift, and the record is regenerable
    (`scripts/generate/nirmana_analysis_layer_pins.py`).
    """
    try:
        record = json.loads(ANALYSIS_LAYER_PINS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("canonical analysis receipt pin record is unavailable") from exc
    pin = (record.get("layers") or {}).get(layer)
    if not isinstance(pin, Mapping):
        raise RuntimeError(f"canonical analysis receipt pin is missing for {layer}")
    if not _valid_git_commit_sha(pin.get("convergence_commit")):
        raise RuntimeError(f"canonical analysis receipt pin for {layer} has an invalid convergence commit")
    if not _valid_sha256(pin.get("writer_inventory_sha256")):
        raise RuntimeError(f"canonical analysis receipt pin for {layer} has an invalid inventory aggregate")
    if not isinstance(pin.get("asset_prefix"), str) or not pin["asset_prefix"]:
        raise RuntimeError(f"canonical analysis receipt pin for {layer} has no asset prefix")
    return dict(pin)


def _validated_layer_writer_inventory(
    writer_digests: Mapping[str, str],
    *,
    layer: str,
    asset_prefix: str,
    expected_aggregate: str,
) -> dict[str, str]:
    """Require the complete current inventory FOR THIS LAYER to equal its pin.

    Per-layer, deliberately: a global aggregate would mean any layer's writer
    fix invalidates every other layer's accepted analyses (adjudication #1715,
    ruling requirement 1).
    """
    layer_inventory = {
        asset_id: digest
        for asset_id, digest in writer_digests.items()
        if isinstance(asset_id, str) and asset_id.startswith(asset_prefix)
    }
    if not layer_inventory or any(not _valid_sha256(digest) for digest in layer_inventory.values()):
        raise RuntimeError(f"current {layer} writer inventory is incomplete or invalid")
    aggregate = _sha256_json(layer_inventory, ensure_ascii=True)
    if aggregate != expected_aggregate:
        raise RuntimeError(
            f"current {layer} writer inventory does not match the reviewed canonical "
            "receipt convergence"
        )
    return layer_inventory


def _canonical_analysis_digest(
    *,
    layer: str,
    frozen_manifest_asset: Mapping[str, Any],
    current_registry_contract: Mapping[str, Any],
    writer_digest: str,
    convergence_commit: str,
) -> str:
    """Match canonicalNirmanaAssetAnalysisDigestForRegistryRow exactly."""
    asset_id = frozen_manifest_asset.get("asset_id")
    if not isinstance(asset_id, str) or frozen_manifest_asset.get("layer") != layer:
        raise RuntimeError(f"canonical {layer} analysis receipt has an invalid frozen asset")
    return _sha256_json(
        {
            "schema_version": "nirmana-asset-analysis-receipt/v1",
            "base": {
                "schema_version": "nirmana-asset-analysis-receipt-base/v1",
                "asset_id": asset_id,
                "layer": layer,
                "writer_digest_sha256": writer_digest,
                "grounding": {
                    "convergence_commit": convergence_commit,
                    "frozen_manifest_source": "nirmana_elevation_campaign_definitions.manifest",
                    "writer_digest_ref": "platform/src/generated/nirmana-writer-digests.json",
                },
            },
            "frozen_manifest_asset": dict(frozen_manifest_asset),
            "current_registry_contract": dict(current_registry_contract),
        },
        ensure_ascii=False,
    )


def _current_analysis_receipt_digests(
    *,
    layer: str,
    selected_assets: Sequence[Mapping[str, Any]],
    candidates_by_id: Mapping[str, Mapping[str, Any]],
    writer_digests: Mapping[str, str],
) -> tuple[dict[str, str], str]:
    """Reconstruct this layer's evidence receipts from current code + live contracts.

    Was L0-only, and the call site was gated on `layer == "L0"` (adjudication
    #1718).  For L1-L5 that left C2 condition 3 uncovered: `REGISTRY_CONTRACT_FIELDS`
    carries no writer digest, so a W3 writer edit landing after W2 acceptance
    left the analysis reading "current" while the build dispatched against an
    analysis of different code -- an unearned green in the CLAUDE.md §N.8 sense.
    Reconstructing per layer closes that for all six.
    """
    pin = _load_layer_receipt_pin(layer)
    layer_inventory = _validated_layer_writer_inventory(
        writer_digests,
        layer=layer,
        asset_prefix=pin["asset_prefix"],
        expected_aggregate=pin["writer_inventory_sha256"],
    )
    digests: dict[str, str] = {}
    for frozen_asset in selected_assets:
        asset_id = frozen_asset.get("asset_id")
        if not isinstance(asset_id, str):
            raise RuntimeError(f"frozen {layer} wave contains an invalid asset ID")
        candidate = candidates_by_id.get(asset_id)
        writer_digest = layer_inventory.get(asset_id)
        if candidate is None or writer_digest is None:
            raise RuntimeError(
                f"canonical {layer} analysis receipt is unavailable for {asset_id}"
            )
        digests[asset_id] = _canonical_analysis_digest(
            layer=layer,
            frozen_manifest_asset=frozen_asset,
            current_registry_contract={
                "asset_id": asset_id,
                "layer": layer,
                # Sort to match the canonical server computation
                # (registryContractFingerprintInput sorts depends_on); an
                # unsorted multi-dependency list here diverges from the digest
                # the evidence route accepted, breaking dispatch for such assets.
                "depends_on": sorted(candidate.get("depends_on") or []),
                "registry_contract": _live_registry_contract(candidate),
            },
            writer_digest=writer_digest,
            convergence_commit=pin["convergence_commit"],
        )
    return digests, pin["convergence_commit"]


def _live_registry_contract(candidate: Mapping[str, Any]) -> dict[str, Any]:
    return {field: candidate.get(field) for field in REGISTRY_CONTRACT_FIELDS}


def _live_registry_fingerprint(
    candidate: Mapping[str, Any],
    *,
    campaign_layer: str,
) -> str:
    asset_id = candidate.get("asset_id")
    if not isinstance(asset_id, str) or not asset_id:
        raise ValueError("live registry row has an invalid asset ID")
    if campaign_layer not in LAYERS or candidate.get("layer") != REGISTRY_LAYER[campaign_layer]:
        raise ValueError(f"live registry contract changed for {asset_id}: layer")
    dependencies = candidate.get("depends_on") or []
    if not isinstance(dependencies, list) or any(
        not isinstance(dependency, str) for dependency in dependencies
    ):
        raise ValueError(f"live dependencies are invalid for {asset_id}")
    return _sha256_json(
        {
            "asset_id": asset_id,
            "layer": campaign_layer,
            # Sort to match the canonical server fingerprint
            # (registryContractFingerprintInput sorts depends_on); an unsorted
            # multi-dependency list diverges from the frozen manifest's stored
            # fingerprint and the accepted analysis, breaking dispatch.
            "depends_on": sorted(dependencies),
            "registry_contract": _live_registry_contract(candidate),
        },
        ensure_ascii=False,
    )


def validate_wave_evidence_bindings(
    *,
    asset_ids: Sequence[str],
    live_registry_fingerprints: Mapping[str, str],
    evidence_rows: Sequence[Mapping[str, Any]],
    canonical_analysis_digests: Mapping[str, str] | None = None,
    reviewed_deployment_sha: str | None = None,
) -> dict[str, dict[str, str]]:
    """Require one exact current analysis and one verdict bound to it per asset."""
    expected_assets = set(asset_ids)
    if len(expected_assets) != len(asset_ids):
        raise RuntimeError("frozen wave contains duplicate asset identities")
    if set(live_registry_fingerprints) != expected_assets or any(
        not _valid_sha256(fingerprint)
        for fingerprint in live_registry_fingerprints.values()
    ):
        raise RuntimeError("live registry fingerprints are incomplete or invalid")
    if (canonical_analysis_digests is None) != (reviewed_deployment_sha is None):
        raise RuntimeError("canonical L0 receipt and reviewed deployment binding must be supplied together")
    if canonical_analysis_digests is not None:
        if set(canonical_analysis_digests) != expected_assets or any(
            not _valid_sha256(digest) for digest in canonical_analysis_digests.values()
        ):
            raise RuntimeError("canonical L0 analysis receipts are incomplete or invalid")
        if not isinstance(reviewed_deployment_sha, str) or len(reviewed_deployment_sha) != 40 or any(
            char not in "0123456789abcdef" for char in reviewed_deployment_sha
        ):
            raise RuntimeError("reviewed deployment convergence SHA is invalid")

    rows_by_asset: dict[str, list[Mapping[str, Any]]] = {
        asset_id: [] for asset_id in asset_ids
    }
    for row in evidence_rows:
        entity_id = row.get("entity_id")
        event_type = row.get("event_type")
        if entity_id not in expected_assets or event_type not in {
            "asset_analysis_accepted",
            "optimization_verdict_accepted",
        }:
            raise RuntimeError("campaign evidence query returned an unexpected receipt")
        rows_by_asset[entity_id].append(row)

    bindings: dict[str, dict[str, str]] = {}
    for asset_id in asset_ids:
        current_fingerprint = live_registry_fingerprints[asset_id]
        current_rows: dict[str, list[tuple[Mapping[str, Any], str]]] = {
            "asset_analysis_accepted": [],
            "optimization_verdict_accepted": [],
        }
        for row in rows_by_asset[asset_id]:
            payload = row.get("evidence_payload")
            if not isinstance(payload, Mapping):
                continue
            if payload.get("registry_fingerprint_sha256") != current_fingerprint:
                continue
            analysis_digest = payload.get("analysis_digest")
            if not _valid_sha256(analysis_digest) or not _valid_git_commit_source(row):
                raise RuntimeError(
                    f"current campaign evidence has invalid provenance for {asset_id}"
                )
            if canonical_analysis_digests is not None:
                # Evidence is append-only.  A prior valid receipt may retain
                # the same registry fingerprint while an explicitly reviewed
                # deployment advances the canonical receipt/source pair.  It
                # remains auditable history, not current dispatch authority.
                if (
                    analysis_digest != canonical_analysis_digests[asset_id]
                    or row["source_ref"] != f"git:{reviewed_deployment_sha}"
                ):
                    continue
            current_rows[row["event_type"]].append((row, analysis_digest))

        analyses = current_rows["asset_analysis_accepted"]
        if not analyses:
            raise RuntimeError(
                "accepted asset analysis does not match the current live "
                f"registry contract for {asset_id}"
            )
        if len(analyses) != 1:
            raise RuntimeError(f"ambiguous asset analysis evidence for {asset_id}")
        analysis_digest = analyses[0][1]

        verdicts = current_rows["optimization_verdict_accepted"]
        if not verdicts:
            raise RuntimeError(
                "optimization verdict does not match the current live "
                f"registry contract for {asset_id}"
            )
        if len(verdicts) != 1:
            raise RuntimeError(f"ambiguous optimization verdict evidence for {asset_id}")
        if verdicts[0][1] != analysis_digest:
            raise RuntimeError(
                f"optimization verdict is not bound to the same accepted analysis for {asset_id}"
            )
        verdict_payload = verdicts[0][0].get("evidence_payload")
        if (
            not isinstance(verdict_payload, Mapping)
            or verdict_payload.get("verdict") not in BUILD_AUTHORIZING_VERDICTS
        ):
            raise RuntimeError(
                f"optimization verdict does not authorize a build for {asset_id}"
            )
        bindings[asset_id] = {
            "registry_fingerprint_sha256": current_fingerprint,
            "analysis_digest": analysis_digest,
        }
    return bindings


def _select_frozen_build_assets(
    *,
    chart_id: str,
    definition_revision: str,
    definition_manifest: Mapping[str, Any],
    definition_manifest_digest: str,
    layer: str,
    wave_index: int,
    asset_ids: frozenset[str] | None = None,
) -> list[dict[str, Any]]:
    if chart_id != DEFAULT_CHART_ID:
        raise ValueError("campaign dispatch is restricted to the approved chart")
    if not definition_revision.strip():
        raise ValueError("campaign definition revision is required")
    if layer not in LAYERS:
        raise ValueError(f"unsupported campaign layer: {layer}")
    if wave_index < 0:
        raise ValueError("campaign wave index cannot be negative")
    if definition_manifest.get("chart_id") != chart_id:
        raise ValueError("definition manifest chart does not match the approved chart")
    if not _valid_sha256(definition_manifest_digest):
        raise ValueError("definition manifest digest is invalid")
    actual_definition_digest = _sha256_json(definition_manifest, ensure_ascii=False)
    if actual_definition_digest != definition_manifest_digest:
        raise ValueError("definition manifest digest does not match frozen contents")
    assets = definition_manifest.get("assets")
    if not isinstance(assets, list):
        raise ValueError("definition manifest assets are invalid")
    selected = [
        asset
        for asset in assets
        if isinstance(asset, dict)
        and asset.get("layer") == layer
        and asset.get("wave_index") == wave_index
        and asset.get("execution_obligation") == "build"
    ]
    if not selected:
        raise ValueError(f"{layer} wave {wave_index} has no build obligations")
    if asset_ids is not None:
        # Per-asset/per-tier dispatch control: narrow to an explicit subset of
        # this wave's build obligations rather than requiring every asset in
        # the wave to be ready at once. Never silently drop a requested ID --
        # a typo or an asset genuinely outside this wave/layer must fail
        # loudly, not select fewer assets than asked for.
        available = {asset["asset_id"] for asset in selected}
        unknown = sorted(asset_ids - available)
        if unknown:
            raise ValueError(
                f"{layer} wave {wave_index} has no build obligation for: {', '.join(unknown)}"
            )
        selected = [asset for asset in selected if asset["asset_id"] in asset_ids]
    return selected


# ---------------------------------------------------------------------------
# WP-6 BLAST RADIUS (native directive D-NATIVE-05; charter C13)
#
# The campaign's DAG models ANCESTORS, and the E-gate gates on ancestors. Nothing
# modelled the other direction until a `bo_laksana` MSR rebuild -- ordinary,
# planned, `rebuild_only` work -- was found to cascade-delete 710,899 rows across
# five L3 tables and orphan ~151,777 more, reaching `phala_anchors`, the table a
# separate campaign-wide hold exists to protect (issues #1770, #1732, #1748).
#
# The native's framing, which is the whole specification:
#
#     "bo_laksana had no idea those tables existed; no writer should be able to
#      not-know again."
#
# So this is not advisory. A committed dispatch REFUSES unless the operator has
# both a snapshot and an explicit acknowledgement naming what will be destroyed.
#
# Note what this does NOT do: it does not decide whether destruction is
# acceptable. That is a W2 route decision and an adjudication matter. It makes
# destruction IMPOSSIBLE TO NOT-KNOW ABOUT, which is the failure that occurred.
# ---------------------------------------------------------------------------

# Referencing columns that carry NO foreign key. These ORPHAN rather than cascade,
# which is the harder failure to detect -- a stale pointer still RESOLVES, so
# nothing reads false (§N.8). They cannot be discovered from pg_constraint by
# definition, so they are enumerated here and each owes a disposition to its
# owning layer (D-NATIVE-05 action 7): a real FK with an intended delete rule, or
# documented orphan-tolerance WITH a detector. Silent orphaning is worse than
# loud cascade.
NO_FK_REFERRERS: dict[str, tuple[tuple[str, str], ...]] = {
    "bodha_msr_signals": (
        ("kala_activation_predicates", "signal_id"),   # L3
        ("mimamsa_attribution", "signal_id"),          # L5
        ("mimamsa_load_bearing", "signal_id"),         # L5
        ("phala_anchors", "signal_id"),                # L4
        ("bodha_triangulation", "signal_ids"),         # L2 (array column)
    ),
}

_LAYER_BY_TABLE_PREFIX = (
    ("brahma_", "L0"), ("bg_", "L0"),
    ("chart_", "L1"), ("ga_", "L1"),
    ("bodha_", "L2"),
    ("kala_", "L3"),
    ("phala_", "L4"),
    ("mimamsa_", "L5"), ("lel_", "L5"),
)


def _layer_of_table(table: str) -> str:
    for prefix, layer in _LAYER_BY_TABLE_PREFIX:
        if table.startswith(prefix):
            return layer
    return "?"


def blast_radius(cur: Any, tables: Sequence[str]) -> dict[str, Any]:
    """Enumerate everything a delete from `tables` would destroy or orphan.

    Returns {"cascade": [...], "orphan": [...], "destroys_rows": bool,
             "cross_layer": bool}. Read-only.

    The cascade walk is TRANSITIVE and that is load-bearing: the defect that
    prompted this reached `phala_anchors` at depth 2 and four more phala_* tables
    at depth 3, via `kala_convergence`. A depth-1 check would have reported the
    L3 damage and missed the L4 damage entirely.
    """
    if not tables:
        return {"cascade": [], "orphan": [], "destroys_rows": False, "cross_layer": False}

    cur.execute(
        """
        WITH RECURSIVE fk AS (
          SELECT confrelid::regclass::text AS parent, conrelid::regclass::text AS child
            FROM pg_constraint
           WHERE contype = 'f' AND confdeltype = 'c'
             AND conrelid::regclass::text !~ '__ssv_'
        ), chain AS (
          SELECT f.child, f.parent AS root, 1 AS depth, ARRAY[f.parent, f.child] AS path
            FROM fk f WHERE f.parent = ANY(%s)
          UNION ALL
          SELECT f.child, c.root, c.depth + 1, c.path || f.child
            FROM chain c JOIN fk f ON f.parent = c.child
           WHERE c.depth < 8 AND NOT f.child = ANY(c.path)
        )
        SELECT DISTINCT ON (child) child, root, depth, path
          FROM chain ORDER BY child, depth
        """,
        (list(tables),),
    )
    cascade_rows = cur.fetchall()

    cascade: list[dict[str, Any]] = []
    for row in cascade_rows:
        child = row["child"]
        # count(*) via a parameterised identifier is not expressible, and `child`
        # comes from pg_constraint (never from user input), so format() on a
        # catalogue-sourced identifier is safe here. quote_ident keeps it honest.
        cur.execute("SELECT quote_ident(%s) AS q", (child,))
        cur.execute(f"SELECT count(*) AS n FROM {cur.fetchone()['q']}")
        cascade.append(
            {
                "table": child,
                "layer": _layer_of_table(child),
                "depth": row["depth"],
                "path": " -> ".join(row["path"]),
                "live_rows": int(cur.fetchone()["n"]),
            }
        )

    orphan: list[dict[str, Any]] = []
    for table in tables:
        for ref_table, ref_col in NO_FK_REFERRERS.get(table, ()):  # type: ignore[arg-type]
            cur.execute(
                "SELECT to_regclass(%s) IS NOT NULL AS present", (ref_table,)
            )
            if not cur.fetchone()["present"]:
                continue
            cur.execute("SELECT quote_ident(%s) AS q", (ref_table,))
            cur.execute(f"SELECT count(*) AS n FROM {cur.fetchone()['q']}")
            orphan.append(
                {
                    "table": ref_table,
                    "column": ref_col,
                    "layer": _layer_of_table(ref_table),
                    "live_rows": int(cur.fetchone()["n"]),
                    "references": table,
                }
            )

    own_layers = {_layer_of_table(t) for t in tables}
    cross_layer = any(
        entry["layer"] not in own_layers and entry["layer"] != "?"
        for entry in (*cascade, *orphan)
    )
    destroys = any(e["live_rows"] > 0 for e in cascade) or any(
        e["live_rows"] > 0 for e in orphan
    )
    return {
        "cascade": cascade,
        "orphan": orphan,
        "destroys_rows": destroys,
        "cross_layer": cross_layer,
    }


def format_blast_radius(report: Mapping[str, Any]) -> str:
    lines: list[str] = []
    for e in sorted(report["cascade"], key=lambda r: (-r["live_rows"], r["table"])):
        lines.append(
            f"    CASCADE  {e['layer']:>2}  {e['live_rows']:>9,} rows  "
            f"{e['table']}  (depth {e['depth']}: {e['path']})"
        )
    for e in sorted(report["orphan"], key=lambda r: (-r["live_rows"], r["table"])):
        lines.append(
            f"    ORPHAN   {e['layer']:>2}  {e['live_rows']:>9,} rows  "
            f"{e['table']}.{e['column']}  (no FK -- will NOT cascade, will dangle)"
        )
    return "\n".join(lines) if lines else "    (none)"


def campaign_prerequisite_asset_ids(
    *,
    definition_manifest: Mapping[str, Any],
    layer: str,
    wave_index: int,
    dispatch_asset_ids: Sequence[str],
) -> list[str]:
    """Return the transitive depends_on ancestors the E-gate requires frozen.

    This is charter C2 condition 1, and it is deliberately NOT what this function
    used to compute. Until v2.1 the campaign ran strictly sequentially, so this
    returned *every* asset of every lower-ranked layer plus every earlier wave of
    the same layer -- dependency edges were never consulted. That was correct for
    the topology it was written for and is wrong for the one the native ratified.

    Concretely, under the old rule an L3 wave-0 dispatch required all 81 assets of
    L0+L1+L2 frozen, while `ka_gochara_resonance`'s real ancestor closure is one
    asset (`bg_transit_rules`) which is already frozen. Under the old rule no layer
    session could dispatch anything at all, and asset-frontier pipelining degraded
    to the sequential campaign with five sessions waiting on each other.

    The gate is not loosened, it is re-aimed: an asset whose ancestors are unfrozen
    is still refused, just as loudly, and an asset with no dependencies is no longer
    made to wait for assets it does not depend on. Layers still FREEZE strictly in
    order (charter C2, W6 ceremonies) -- that ordering lives in the freeze-ack
    protocol, not here.

    Ancestors are resolved over the FROZEN definition manifest, never the live
    registry, so a live `depends_on` edit cannot silently widen or narrow the gate.
    `depends_on` is sorted at every hash site for the same reason (see
    `_live_registry_fingerprint`); here order is irrelevant since the result is a set.
    """
    if layer not in LAYERS:
        raise ValueError(f"unsupported campaign layer: {layer}")
    assets = definition_manifest.get("assets")
    if not isinstance(assets, list):
        raise ValueError("definition manifest assets are invalid")

    dependencies_by_asset: dict[str, list[str]] = {}
    for asset in assets:
        if not isinstance(asset, dict):
            raise ValueError("definition manifest contains an invalid asset")
        asset_id = asset.get("asset_id")
        asset_layer = asset.get("layer")
        asset_wave = asset.get("wave_index")
        if (
            not isinstance(asset_id, str)
            or asset_layer not in LAYERS
            or not isinstance(asset_wave, int)
        ):
            raise ValueError("definition manifest contains an invalid asset identity")
        dependencies = asset.get("depends_on") or []
        if not isinstance(dependencies, list) or any(
            not isinstance(dependency, str) for dependency in dependencies
        ):
            raise ValueError(f"definition manifest has invalid depends_on for {asset_id}")
        dependencies_by_asset[asset_id] = dependencies

    for asset_id in dispatch_asset_ids:
        if asset_id not in dependencies_by_asset:
            raise ValueError(f"dispatch asset is not in the frozen definition: {asset_id}")

    # Breadth-first transitive closure. Visiting each asset once terminates even if
    # a manifest ever contained a cycle -- fail-closed on data, not a hang.
    ancestors: set[str] = set()
    frontier = [
        dependency
        for asset_id in dispatch_asset_ids
        for dependency in dependencies_by_asset[asset_id]
    ]
    while frontier:
        current = frontier.pop()
        if current in ancestors:
            continue
        ancestors.add(current)
        if current not in dependencies_by_asset:
            raise ValueError(
                f"frozen definition has a dangling depends_on edge: {current}"
            )
        frontier.extend(dependencies_by_asset[current])

    # An asset never gates itself, even via a cycle.
    ancestors.difference_update(dispatch_asset_ids)
    return sorted(ancestors)


def build_campaign_wave_manifest(
    *,
    chart_id: str,
    definition_revision: str,
    definition_manifest: Mapping[str, Any],
    definition_manifest_digest: str,
    layer: str,
    wave_index: int,
    candidates: Sequence[Mapping[str, Any]],
    writer_digests: Mapping[str, str],
    snapshot_ref: str | None = None,
    requested_asset_ids: frozenset[str] | None = None,
) -> tuple[dict[str, Any], str, list[str]]:
    """Validate frozen/live/code identity and create a runner manifest."""
    selected = _select_frozen_build_assets(
        chart_id=chart_id,
        definition_revision=definition_revision,
        definition_manifest=definition_manifest,
        definition_manifest_digest=definition_manifest_digest,
        layer=layer,
        asset_ids=requested_asset_ids,
        wave_index=wave_index,
    )
    candidate_by_id = {
        candidate.get("asset_id"): candidate
        for candidate in candidates
        if isinstance(candidate.get("asset_id"), str)
    }
    if len(candidate_by_id) != len(candidates):
        raise ValueError("live registry query returned duplicate or invalid asset rows")
    asset_ids: list[str] = []
    manifest_assets: list[dict[str, Any]] = []
    for frozen_asset in selected:
        asset_id = frozen_asset.get("asset_id")
        if not isinstance(asset_id, str) or not asset_id:
            raise ValueError("frozen wave contains an invalid asset ID")
        candidate = candidate_by_id.get(asset_id)
        if candidate is None:
            raise ValueError(f"live registry row missing for {asset_id}")
        if candidate.get("layer") != REGISTRY_LAYER[layer]:
            raise ValueError(f"live registry contract changed for {asset_id}: layer")
        frozen_dependencies = frozen_asset.get("depends_on")
        if not isinstance(frozen_dependencies, list) or any(
            not isinstance(dependency, str) for dependency in frozen_dependencies
        ):
            raise ValueError(f"frozen dependencies are invalid for {asset_id}")
        live_dependencies = candidate.get("depends_on") or []
        if (
            not isinstance(live_dependencies, list)
            or len(set(live_dependencies)) != len(live_dependencies)
            or len(set(frozen_dependencies)) != len(frozen_dependencies)
            or sorted(live_dependencies) != sorted(frozen_dependencies)
        ):
            raise ValueError(f"live registry contract changed for {asset_id}: depends_on")
        frozen_contract = frozen_asset.get("registry_contract")
        if not isinstance(frozen_contract, dict):
            raise ValueError(f"frozen registry contract missing for {asset_id}")
        live_contract = _live_registry_contract(candidate)
        if (
            live_contract["is_active"] is not True
            or live_contract["has_writer"] is not True
            or live_contract["catalog_status"] == "RETIRED"
            or live_contract["asset_kind"] == "service"
        ):
            raise ValueError(f"live registry asset is not buildable: {asset_id}")
        live_fingerprint = _live_registry_fingerprint(
            candidate,
            campaign_layer=layer,
        )
        expected_code_digest = writer_digests.get(asset_id)
        if not _valid_sha256(expected_code_digest):
            raise ValueError(f"writer digest missing or invalid for {asset_id}")
        asset_ids.append(asset_id)
        manifest_assets.append(
            {
                "asset_id": asset_id,
                "scope": live_contract["scope"],
                "depends_on": list(frozen_dependencies),
                "natural_key_partition": live_contract["natural_key_partition"],
                "has_cowriters": bool(candidate.get("has_cowriters")),
                "expected_code_digest": expected_code_digest,
                "registry_contract": live_contract,
                "registry_fingerprint_sha256": live_fingerprint,
            }
        )
    if set(candidate_by_id) != set(asset_ids):
        raise ValueError("live registry query returned assets outside the frozen build wave")

    scope_target = ",".join(asset_ids)
    manifest: dict[str, Any] = {
        "version": "nirmana-run-manifest/v1",
        "chart_id": chart_id,
        "scope": "asset_set",
        "scope_target": scope_target,
        "action": "rebuild",
        "waves": [list(asset_ids)],
        "assets": manifest_assets,
    }
    if snapshot_ref is not None:
        if not snapshot_ref.strip():
            raise ValueError("snapshot reference cannot be blank")
        manifest["campaign_control"] = {
            "campaign_id": CAMPAIGN_ID,
            "definition_revision": definition_revision,
            "layer": layer,
            "wave_index": wave_index,
            "snapshot_ref": snapshot_ref,
        }
    return (
        manifest,
        _sha256_json(manifest, ensure_ascii=True),
        asset_ids,
    )


def _load_writer_digests() -> dict[str, str]:
    inventory = json.loads(WRITER_DIGESTS_PATH.read_text(encoding="utf-8"))
    writers = inventory.get("writers")
    if not isinstance(writers, dict):
        raise RuntimeError("writer digest inventory is invalid")
    return writers


def _triggered_by(
    definition_revision: str,
    layer: str,
    wave_index: int,
    asset_ids: frozenset[str] | None = None,
) -> str:
    base = f"{CAMPAIGN_ID}:{definition_revision}:{layer}:wave-{wave_index}"
    if asset_ids is None:
        return base
    # A scoped subset must not consume the wave's "one run per triggered_by"
    # slot -- dispatching one asset now must never block dispatching the rest
    # of the wave (or a different subset) later. Keying on the exact sorted
    # asset set, not a hash, keeps this readable directly from the DB.
    return f"{base}:assets-{','.join(sorted(asset_ids))}"


def _load_definition(cur, definition_revision: str) -> dict[str, Any]:
    # Plain SELECT, not FOR SHARE: not every caller of create_campaign_run
    # holds UPDATE on nirmana_elevation_campaign_definitions (e.g. amjis_app,
    # used for the build_runs/build_run_assets INSERT, has only SELECT
    # there) -- same fix as _load_candidates below and the identical bug
    # already fixed on asset_registry/campaign_events elsewhere in this repo.
    # create_campaign_run runs this transaction under SERIALIZABLE isolation
    # (set immediately after connecting, before this call), which provides
    # the same conflict protection via SSI without needing a lock.
    cur.execute(
        """
        SELECT definition_revision, definition_status, manifest, manifest_sha256
          FROM nirmana_evidence.nirmana_elevation_campaign_definitions
         WHERE campaign_id=%s AND definition_revision=%s
           AND superseded_at IS NULL
        """,
        (CAMPAIGN_ID, definition_revision),
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError("frozen campaign definition is missing")
    if row["definition_status"] != "frozen":
        raise RuntimeError("campaign definition is not frozen")
    return dict(row)


def _load_candidates(cur, asset_ids: list[str]) -> list[dict[str, Any]]:
    # Plain SELECT, not FOR SHARE OF ar: nirmana_campaign_control_writer is
    # deliberately SELECT-only (no UPDATE) on asset_registry, and Postgres's
    # row-locking clauses require UPDATE privilege -- see the identical fix
    # in platform/src/lib/nirmana-elevation/definitions.ts's accept/supersede
    # asset_registry reads and dispatch_nirmana_f0_canary.py's _load_candidate.
    # create_campaign_run runs this transaction under SERIALIZABLE isolation
    # (set immediately after connecting, before this call), which provides
    # the same conflict protection via SSI without needing a lock.
    cur.execute(
        """
        SELECT ar.asset_id, ar.layer, COALESCE(ar.depends_on, '{}') AS depends_on,
               ar.sort_order, ar.scope, ar.asset_kind, ar.catalog_status,
               ar.is_active, ar.has_writer, ar.target_table, ar.count_sql,
               ar.integrity_check_sql, ar.health_probe, ar.natural_key_partition,
               ar.superseded_by, ar.data_disposition, ar.dead_flag,
               EXISTS (
                 SELECT 1 FROM asset_registry peer
                  WHERE peer.target_table = ar.target_table
                    AND ar.target_table IS NOT NULL
                    AND peer.asset_id <> ar.asset_id
                    AND peer.is_active = true AND peer.has_writer = true
               ) AS has_cowriters
          FROM asset_registry ar
         WHERE ar.asset_id = ANY(%s)
        """,
        (asset_ids,),
    )
    return [dict(row) for row in cur.fetchall()]


def create_campaign_run(
    *,
    database_url: str,
    chart_id: str,
    definition_revision: str,
    layer: str,
    wave_index: int,
    commit: bool,
    snapshot_ref: str | None = None,
    expected_manifest_digest: str | None = None,
    reviewed_deployment_sha: str | None = None,
    requested_asset_ids: frozenset[str] | None = None,
    acknowledge_destroys: bool = False,
) -> dict[str, Any]:
    if commit and not snapshot_ref:
        raise ValueError("committed campaign wave requires a recovery snapshot reference")
    if commit and not expected_manifest_digest:
        raise ValueError("committed campaign wave requires the reviewed preview manifest digest")
    if layer == "L0" and not _valid_git_commit_sha(reviewed_deployment_sha):
        raise ValueError(
            "L0 campaign dispatch requires an exact reviewed deployed commit SHA"
        )
    import psycopg
    import psycopg.rows

    connection = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
    connection.autocommit = False
    # SERIALIZABLE, not the psycopg/Postgres default READ COMMITTED: this is
    # what lets _load_candidates's asset_registry read safely drop
    # FOR SHARE OF ar (see that function's comment).
    connection.isolation_level = psycopg.IsolationLevel.SERIALIZABLE
    try:
        cur = connection.cursor()
        triggered_by = _triggered_by(
            definition_revision, layer, wave_index, asset_ids=requested_asset_ids
        )
        cur.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
            (triggered_by,),
        )
        definition = _load_definition(cur, definition_revision)
        selected = _select_frozen_build_assets(
            chart_id=chart_id,
            definition_revision=definition_revision,
            definition_manifest=definition["manifest"],
            definition_manifest_digest=definition["manifest_sha256"],
            layer=layer,
            wave_index=wave_index,
            asset_ids=requested_asset_ids,
        )
        asset_ids = [asset["asset_id"] for asset in selected]

        candidates = _load_candidates(cur, asset_ids)
        candidate_by_id = {
            candidate.get("asset_id"): candidate
            for candidate in candidates
            if isinstance(candidate.get("asset_id"), str)
        }
        if set(candidate_by_id) != set(asset_ids) or len(candidate_by_id) != len(candidates):
            raise RuntimeError("live registry rows do not exactly match the frozen build wave")
        live_registry_fingerprints = {
            asset_id: _live_registry_fingerprint(
                candidate_by_id[asset_id],
                campaign_layer=layer,
            )
            for asset_id in asset_ids
        }
        writer_digests = _load_writer_digests()
        # Every layer, not just L0 (adjudication #1718, folded into #1715's
        # ruling): reconstructing the canonical analysis digest from CURRENT
        # code is what makes a post-acceptance writer edit detectable.
        canonical_analysis_digests: Mapping[str, str] | None
        canonical_analysis_digests, _convergence_commit = (
            _current_analysis_receipt_digests(
                layer=layer,
                selected_assets=selected,
                candidates_by_id=candidate_by_id,
                writer_digests=writer_digests,
            )
        )

        required_evidence_types = (
            "asset_analysis_accepted",
            "optimization_verdict_accepted",
        )
        cur.execute(
            """
            SELECT event_id, entity_id, event_type, evidence_payload,
                   source_kind, source_ref
              FROM nirmana_evidence.nirmana_elevation_campaign_events
             WHERE campaign_id=%s AND definition_revision=%s
               AND entity_type='asset' AND layer=%s
               AND entity_id = ANY(%s) AND event_type = ANY(%s)
             ORDER BY event_id
            """,
            (
                CAMPAIGN_ID,
                definition_revision,
                layer,
                asset_ids,
                list(required_evidence_types),
            ),
        )
        validate_wave_evidence_bindings(
            asset_ids=asset_ids,
            live_registry_fingerprints=live_registry_fingerprints,
            evidence_rows=cur.fetchall(),
            canonical_analysis_digests=canonical_analysis_digests,
            reviewed_deployment_sha=reviewed_deployment_sha,
        )

        prerequisites = campaign_prerequisite_asset_ids(
            definition_manifest=definition["manifest"],
            layer=layer,
            wave_index=wave_index,
            dispatch_asset_ids=asset_ids,
        )
        if prerequisites:
            cur.execute(
                """
                SELECT DISTINCT entity_id
                  FROM nirmana_evidence.nirmana_elevation_campaign_events
                 WHERE campaign_id=%s AND definition_revision=%s
                   AND event_type='asset_frozen' AND entity_id = ANY(%s)
                """,
                (CAMPAIGN_ID, definition_revision, prerequisites),
            )
            frozen_prerequisites = {row["entity_id"] for row in cur.fetchall()}
            missing_prerequisites = [
                asset_id
                for asset_id in prerequisites
                if asset_id not in frozen_prerequisites
            ]
            if missing_prerequisites:
                raise RuntimeError(
                    "E-gate refused: the dispatched assets have unfrozen DAG ancestors "
                    f"({len(missing_prerequisites)} remain): "
                    + ", ".join(missing_prerequisites[:10])
                    + ("," if len(missing_prerequisites) > 10 else "")
                )

        cur.execute(
            """SELECT id, chart_id, state FROM build_runs
                 WHERE state IN ('planned', 'running', 'paused')
                 ORDER BY created_at"""
        )
        active = cur.fetchall()
        if len(active) >= MAX_CONCURRENT_CAMPAIGN_RUNS:
            raise RuntimeError(
                "concurrent build-run cap reached; campaign wave refused "
                f"({len(active)} active, cap {MAX_CONCURRENT_CAMPAIGN_RUNS}). "
                "Release a run slot on the coordination issue before retrying."
            )

        # ---- WP-6 BLAST RADIUS (D-NATIVE-05 / charter C13) ------------------
        # Enumerate what this dispatch DESTROYS downstream, and refuse to commit
        # unless the operator has acknowledged it. Deliberately runs for dry runs
        # too: the preview is where an operator should first learn the cost, not
        # the commit.
        target_tables = sorted(
            {str(c["target_table"]) for c in candidates if c.get("target_table")}
        )
        radius = blast_radius(cur, target_tables)
        if radius["cascade"] or radius["orphan"]:
            print(
                "\nWP-6 BLAST RADIUS -- this dispatch destroys downstream data:\n"
                + format_blast_radius(radius),
                file=sys.stderr,
            )
        if commit and radius["destroys_rows"] and not acknowledge_destroys:
            raise RuntimeError(
                "WP-6 refused: this dispatch would destroy or orphan downstream rows "
                "the run has not acknowledged.\n"
                + format_blast_radius(radius)
                + "\n\nBefore proceeding (charter C13 -- hard floor, not discretion):\n"
                "  1. take a FRESH VERIFIED snapshot covering every table above;\n"
                "  2. confirm with each owning layer that its data is regenerable;\n"
                "  3. re-run with --acknowledge-destroys.\n"
                + (
                    "  THIS CROSSES A LAYER BOUNDARY: another session owns rows listed "
                    "above. File an adjudication issue and obtain an ordering ruling "
                    "before acknowledging.\n"
                    if radius["cross_layer"]
                    else ""
                )
            )

        # Only a genuinely in-flight run blocks a fresh dispatch of the same
        # (definition_revision, layer, wave, asset_ids) tuple -- the same "active"
        # state set the existing build_runs_one_active_per_chart_idx partial index
        # already uses elsewhere in this table. A run that reached a terminal state
        # (completed/stopped/failed) without ever submitting accepted_rebuild_observed
        # must not permanently consume its triggered_by key: since there is exactly
        # one frozen definition_revision for the whole campaign, that key can never
        # recur differently, so an unqualified block here would refuse re-authorization
        # forever. An asset that DID already reach accepted_rebuild_observed is refused
        # by the separate, independent check immediately below regardless of this one.
        cur.execute(
            "SELECT id, state FROM build_runs WHERE triggered_by=%s"
            " AND state = ANY(%s) ORDER BY created_at",
            (triggered_by, ["planned", "running", "paused"]),
        )
        prior_runs = cur.fetchall()
        if prior_runs:
            raise RuntimeError(
                "a run already exists for this frozen campaign wave; duplicate execution refused"
            )

        cur.execute(
            """
            SELECT entity_id
              FROM nirmana_evidence.nirmana_elevation_campaign_events
             WHERE campaign_id=%s AND definition_revision=%s
               AND event_type='accepted_rebuild_observed'
               AND entity_id = ANY(%s)
            """,
            (CAMPAIGN_ID, definition_revision, asset_ids),
        )
        accepted = [row["entity_id"] for row in cur.fetchall()]
        if accepted:
            raise RuntimeError(
                f"accepted rebuild evidence already exists for {len(accepted)} selected assets"
            )

        cur.execute(
            """SELECT asset_id FROM build_protected_assets
                 WHERE chart_id=%s AND asset_id = ANY(%s)
                 ORDER BY asset_id""",
            (chart_id, asset_ids),
        )
        protected = [row["asset_id"] for row in cur.fetchall()]
        if protected:
            raise RuntimeError(
                f"campaign wave contains protected assets: {','.join(protected)}"
            )

        manifest, manifest_digest, asset_ids = build_campaign_wave_manifest(
            chart_id=chart_id,
            definition_revision=definition_revision,
            definition_manifest=definition["manifest"],
            definition_manifest_digest=definition["manifest_sha256"],
            layer=layer,
            wave_index=wave_index,
            candidates=candidates,
            writer_digests=writer_digests,
            snapshot_ref=snapshot_ref,
            requested_asset_ids=requested_asset_ids,
        )
        if expected_manifest_digest is not None:
            if not _valid_sha256(expected_manifest_digest):
                raise RuntimeError("expected preview manifest digest is invalid")
            if manifest_digest != expected_manifest_digest:
                raise RuntimeError(
                    "runner manifest no longer matches the reviewed dry-run preview"
                )
        run_id = str(uuid.uuid4())
        scope_target = manifest["scope_target"]
        cur.execute(
            """
            INSERT INTO build_runs
              (id, chart_id, scope, scope_target, action, state, plan,
               plan_manifest, plan_manifest_digest, triggered_by)
            VALUES (%s, %s, 'asset_set', %s, 'rebuild', 'planned', %s::jsonb,
                    %s::jsonb, %s, %s)
            """,
            (
                run_id,
                chart_id,
                scope_target,
                json.dumps(asset_ids),
                json.dumps(manifest),
                manifest_digest,
                triggered_by,
            ),
        )
        cur.executemany(
            """INSERT INTO build_run_assets (run_id, asset_id, position, state)
               VALUES (%s, %s, %s, 'queued')""",
            [(run_id, asset_id, position) for position, asset_id in enumerate(asset_ids)],
        )
        if commit:
            connection.commit()
        else:
            connection.rollback()
        return {
            "run_id": run_id,
            "chart_id": chart_id,
            "definition_revision": definition_revision,
            "layer": layer,
            "wave_index": wave_index,
            "asset_count": len(asset_ids),
            "asset_ids": asset_ids,
            "manifest_digest": manifest_digest,
            "triggered_by": triggered_by,
            "committed": commit,
            "acceptance_event_recorded": False,
            "snapshot_ref": snapshot_ref,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def dispatch_campaign_run(
    *,
    run_id: str,
    project: str,
    region: str,
    job: str,
    run_command=subprocess.run,
) -> str:
    result = run_command(
        [
            "gcloud",
            "run",
            "jobs",
            "execute",
            job,
            f"--project={project}",
            f"--region={region}",
            f"--args=--run-id,{run_id}",
            "--async",
            "--format=value(metadata.name)",
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "unknown gcloud error").strip()[:1000]
        raise RuntimeError(detail)
    execution = result.stdout.strip()
    if not execution:
        raise RuntimeError("gcloud returned no execution name")
    return execution


def terminalize_dispatch_failure(cur, *, run_id: str, error: str) -> None:
    message = f"campaign wave dispatch failed: {error}"[:2000]
    cur.execute(
        """WITH failed_run AS (
               UPDATE build_runs
                  SET state='failed', ended_at=NOW(), last_error=%s
                WHERE id=%s AND state='planned'
            RETURNING id
           )
           UPDATE build_run_assets
              SET state='aborted', ended_at=NOW(), error=%s
            WHERE run_id IN (SELECT id FROM failed_run)
              AND state='queued'""",
        (message, run_id, message),
    )


def mark_dispatch_failed(*, database_url: str, run_id: str, error: str) -> None:
    import psycopg

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cur:
            terminalize_dispatch_failure(cur, run_id=run_id, error=error)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create one exact frozen Nirmana campaign build wave"
    )
    parser.add_argument("--layer", required=True, choices=sorted(LAYERS))
    parser.add_argument("--wave", required=True, type=int)
    parser.add_argument("--definition-revision", default=DEFAULT_DEFINITION_REVISION)
    parser.add_argument("--project", default="madhav-astrology")
    parser.add_argument("--region", default="asia-south1")
    parser.add_argument("--job", default="brahma-build-pipeline-job")
    parser.add_argument(
        "--snapshot-ref",
        help="Recovery snapshot/backup reference to bind into the reviewed manifest",
    )
    parser.add_argument(
        "--expected-manifest-digest",
        help="Required with --commit; must equal the prior dry-run preview digest",
    )
    parser.add_argument(
        "--reviewed-deployment-sha",
        default=os.environ.get("NIRMANA_DEPLOYED_SHA"),
        help=(
            "Exact current deployed commit SHA for L0 evidence; defaults to "
            "NIRMANA_DEPLOYED_SHA when configured"
        ),
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Commit and dispatch the run; omission is a rollback-only dry run",
    )
    parser.add_argument("--confirm", help=f"Required with --commit: {CONFIRMATION}")
    parser.add_argument(
        "--acknowledge-destroys",
        action="store_true",
        help=(
            "Required with --commit when the dispatch would cascade-delete or orphan "
            "downstream rows (WP-6 / charter C13). Acknowledges the printed blast "
            "radius. Take a fresh verified snapshot FIRST -- this flag asserts you "
            "have one; it does not create one."
        ),
    )
    parser.add_argument(
        "--assets",
        help=(
            "Optional comma-separated asset_id subset of the frozen wave to dispatch "
            "(e.g. for staged per-asset rollout ahead of a full wave). Omit to dispatch "
            "the wave's full build obligation."
        ),
    )
    args = parser.parse_args()

    requested_asset_ids: frozenset[str] | None = None
    if args.assets:
        requested_asset_ids = frozenset(
            asset_id.strip() for asset_id in args.assets.split(",") if asset_id.strip()
        )
        if not requested_asset_ids:
            parser.error("--assets must name at least one asset_id")

    if args.commit and args.confirm != CONFIRMATION:
        parser.error(f"--commit requires --confirm {CONFIRMATION}")
    if args.commit and not args.snapshot_ref:
        parser.error("--commit requires --snapshot-ref")
    if args.commit and not args.expected_manifest_digest:
        parser.error("--commit requires --expected-manifest-digest from a reviewed dry run")
    if args.layer == "L0" and not _valid_git_commit_sha(args.reviewed_deployment_sha):
        parser.error(
            "L0 requires --reviewed-deployment-sha (or configured NIRMANA_DEPLOYED_SHA)"
        )
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print(
            "ERROR: DATABASE_URL is required; obtain it from configured secret access without printing it.",
            file=sys.stderr,
        )
        return 1
    try:
        receipt = create_campaign_run(
            database_url=database_url,
            chart_id=DEFAULT_CHART_ID,
            definition_revision=args.definition_revision,
            layer=args.layer,
            wave_index=args.wave,
            commit=args.commit,
            snapshot_ref=args.snapshot_ref,
            expected_manifest_digest=args.expected_manifest_digest,
            reviewed_deployment_sha=args.reviewed_deployment_sha,
            requested_asset_ids=requested_asset_ids,
            acknowledge_destroys=args.acknowledge_destroys,
        )
    except Exception as exc:
        print(f"ERROR: campaign wave run not created: {exc}", file=sys.stderr)
        return 2
    if args.commit:
        try:
            receipt["execution_name"] = dispatch_campaign_run(
                run_id=receipt["run_id"],
                project=args.project,
                region=args.region,
                job=args.job,
            )
        except Exception as exc:
            mark_dispatch_failed(
                database_url=database_url,
                run_id=receipt["run_id"],
                error=str(exc),
            )
            print(
                f"ERROR: campaign wave dispatch failed and run was terminalized: {exc}",
                file=sys.stderr,
            )
            return 3
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
