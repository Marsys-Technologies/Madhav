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
import re
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
L0_ANALYSIS_RECEIPTS_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "generated"
    / "nirmana-l0-analysis-receipts.ts"
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


def _load_l0_canonical_receipt_contract() -> dict[str, str]:
    """Read the checked-in L0 receipt grounding contract or fail closed.

    The TypeScript receipt module is the existing canonical source used when
    evidence is accepted.  This dispatcher deliberately reads its exported
    pins rather than duplicating them, so a changed writer inventory cannot
    authorize a rebuild until the receipt convergence is explicitly reviewed.
    """
    try:
        source = L0_ANALYSIS_RECEIPTS_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError("canonical L0 analysis receipt contract is unavailable") from exc

    def exported_sha(name: str) -> str:
        match = re.search(
            rf"export const {name} = '([0-9a-f]{{64}})' as const",
            source,
        )
        if match is None:
            raise RuntimeError(f"canonical L0 analysis receipt contract is invalid: {name}")
        return match.group(1)

    match = re.search(
        r"export const NIRMANA_L0_CONVERGENCE_COMMIT = '([0-9a-f]{40})' as const",
        source,
    )
    if match is None:
        raise RuntimeError("canonical L0 analysis receipt contract is invalid: convergence commit")
    return {
        "convergence_commit": match.group(1),
        "writer_inventory_sha256": exported_sha(
            "NIRMANA_L0_WRITER_INVENTORY_SHA256"
        ),
    }


def _validated_l0_writer_inventory(
    writer_digests: Mapping[str, str],
    *,
    expected_aggregate: str,
) -> dict[str, str]:
    """Require the complete current L0 inventory to equal the receipt pin."""
    l0_inventory = {
        asset_id: digest
        for asset_id, digest in writer_digests.items()
        if isinstance(asset_id, str) and asset_id.startswith("bg_")
    }
    if not l0_inventory or any(not _valid_sha256(digest) for digest in l0_inventory.values()):
        raise RuntimeError("current L0 writer inventory is incomplete or invalid")
    aggregate = _sha256_json(l0_inventory, ensure_ascii=True)
    if aggregate != expected_aggregate:
        raise RuntimeError(
            "current L0 writer inventory does not match the reviewed canonical receipt convergence"
        )
    return l0_inventory


def _canonical_l0_analysis_digest(
    *,
    frozen_manifest_asset: Mapping[str, Any],
    current_registry_contract: Mapping[str, Any],
    writer_digest: str,
    convergence_commit: str,
) -> str:
    """Match canonicalNirmanaAssetAnalysisDigestForRegistryRow exactly."""
    asset_id = frozen_manifest_asset.get("asset_id")
    if not isinstance(asset_id, str) or frozen_manifest_asset.get("layer") != "L0":
        raise RuntimeError("canonical L0 analysis receipt has an invalid frozen asset")
    return _sha256_json(
        {
            "schema_version": "nirmana-asset-analysis-receipt/v1",
            "base": {
                "schema_version": "nirmana-asset-analysis-receipt-base/v1",
                "asset_id": asset_id,
                "layer": "L0",
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


def _current_l0_analysis_receipt_digests(
    *,
    selected_assets: Sequence[Mapping[str, Any]],
    candidates_by_id: Mapping[str, Mapping[str, Any]],
    writer_digests: Mapping[str, str],
) -> tuple[dict[str, str], str]:
    """Reconstruct L0 evidence receipts from current code and live contracts."""
    contract = _load_l0_canonical_receipt_contract()
    l0_inventory = _validated_l0_writer_inventory(
        writer_digests,
        expected_aggregate=contract["writer_inventory_sha256"],
    )
    digests: dict[str, str] = {}
    for frozen_asset in selected_assets:
        asset_id = frozen_asset.get("asset_id")
        if not isinstance(asset_id, str):
            raise RuntimeError("frozen L0 wave contains an invalid asset ID")
        candidate = candidates_by_id.get(asset_id)
        writer_digest = l0_inventory.get(asset_id)
        if candidate is None or writer_digest is None:
            raise RuntimeError(
                f"canonical L0 analysis receipt is unavailable for {asset_id}"
            )
        digests[asset_id] = _canonical_l0_analysis_digest(
            frozen_manifest_asset=frozen_asset,
            current_registry_contract={
                "asset_id": asset_id,
                "layer": "L0",
                # Sort to match the canonical server computation
                # (registryContractFingerprintInput sorts depends_on); an
                # unsorted multi-dependency list here diverges from the digest
                # the evidence route accepted, breaking dispatch for such assets.
                "depends_on": sorted(candidate.get("depends_on") or []),
                "registry_contract": _live_registry_contract(candidate),
            },
            writer_digest=writer_digest,
            convergence_commit=contract["convergence_commit"],
        )
    return digests, contract["convergence_commit"]


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


def campaign_prerequisite_asset_ids(
    *,
    definition_manifest: Mapping[str, Any],
    layer: str,
    wave_index: int,
) -> list[str]:
    """Return every asset that strict layer/wave sequencing requires frozen."""
    if layer not in LAYERS:
        raise ValueError(f"unsupported campaign layer: {layer}")
    assets = definition_manifest.get("assets")
    if not isinstance(assets, list):
        raise ValueError("definition manifest assets are invalid")
    prerequisites: list[str] = []
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
        if LAYER_RANK[asset_layer] < LAYER_RANK[layer] or (
            asset_layer == layer and asset_wave < wave_index
        ):
            prerequisites.append(asset_id)
    return prerequisites


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
          FROM nirmana_elevation_campaign_definitions
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
        canonical_analysis_digests: Mapping[str, str] | None = None
        if layer == "L0":
            canonical_analysis_digests, _convergence_commit = (
                _current_l0_analysis_receipt_digests(
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
              FROM nirmana_elevation_campaign_events
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
        )
        if prerequisites:
            cur.execute(
                """
                SELECT DISTINCT entity_id
                  FROM nirmana_elevation_campaign_events
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
                    "strict campaign sequencing requires all prior layers/waves frozen "
                    f"({len(missing_prerequisites)} assets remain)"
                )

        cur.execute(
            """SELECT id, chart_id, state FROM build_runs
                 WHERE state IN ('planned', 'running', 'paused')
                 ORDER BY created_at"""
        )
        active = cur.fetchall()
        if active:
            raise RuntimeError(f"active build runs exist; campaign wave refused ({len(active)})")

        cur.execute(
            "SELECT id, state FROM build_runs WHERE triggered_by=%s ORDER BY created_at",
            (triggered_by,),
        )
        prior_runs = cur.fetchall()
        if prior_runs:
            raise RuntimeError(
                "a run already exists for this frozen campaign wave; duplicate execution refused"
            )

        cur.execute(
            """
            SELECT entity_id
              FROM nirmana_elevation_campaign_events
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
