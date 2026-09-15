#!/usr/bin/env python3
"""Generate the Nirmāṇa per-layer analysis-receipt pin record.

Why this script exists
----------------------
`nirmana-l0-analysis-receipts.ts` was hand-maintained committed output with no
generator.  That is the defect behind the convergence-pin drift recorded in
CAMPAIGN_STATE: a pin nobody can regenerate is a pin nobody can verify.
Generalising the receipt spine to six layers without a generator would multiply
that hazard by six (adjudication #1715, Conductor ruling, requirement 4).

What a "pin" is
---------------
One record per layer, holding:

  asset_prefix            the writer-id prefix that identifies the layer
  convergence_commit      the reviewed commit whose writer inventory this pins
  writer_inventory_sha256 sha256 over the layer's slice of the writer inventory
  receipt_count           how many receipt bases the layer must produce
  non_writer_assets       manifest assets with no sidecar writer (probe/static/
                          empty obligations), which still need a receipt base

`writer_inventory_sha256` is what makes the spine **fail closed PER LAYER**: a
writer edit in one layer changes only that layer's aggregate, so only that
layer's receipts become unavailable.  A single global pin would let any layer's
writer fix silently invalidate every other layer's accepted analyses — the
cross-layer failure the original L0-only design could not even express.

L0's three pinned values are INPUTS here, never recomputed: re-deriving them
would invalidate 29 already-frozen L0 capsules.  `--check` proves they survive.

Usage
-----
  python -m scripts.generate.nirmana_analysis_layer_pins            # regenerate (needs DB)
  python -m scripts.generate.nirmana_analysis_layer_pins --check    # verify (no DB needed)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

GENERATED = Path(__file__).resolve().parents[2] / "src" / "generated"
WRITER_DIGESTS_PATH = GENERATED / "nirmana-writer-digests.json"
PINS_PATH = GENERATED / "nirmana-analysis-layer-pins.json"

PINS_VERSION = "nirmana-analysis-layer-pins/v2"
LEGACY_PINS_VERSION = "nirmana-analysis-layer-pins/v1"
SUCCESSOR_SCHEMA_VERSION = "nirmana-analysis-layer-successor/v1"
ALLOWED_DELTA_CLASSIFICATIONS = frozenset(
    {
        "approved_intentional_change",
        "derived_import_change",
        "generator_defect",
        "stale_receipt",
        "unapproved_foreign_source",
    }
)

# D-NATIVE-11 (#2258, native-ruled 2026-09-07): supporting infrastructure
# writers are registered in the orchestrator DAG (so they run and their
# dependents see them) but are NOT elevation-denominator assets -- they never
# join the frozen manifest, produce no terminal capsule, and are verified as
# part of the grounding of the assets they serve. They therefore stay OUT of
# receipt_count arithmetic, while remaining IN writer_inventory_sha256: a
# supporting writer's code change must still fail the spine closed and force
# a reviewed re-pin, exactly like any other writer in the layer.
SUPPORTING_WRITERS = frozenset({"bo_grounding"})

LAYER_PREFIX = {
    "L0": "bg_",
    "L1": "ga_",
    "L2": "bo_",
    "L3": "ka_",
    "L4": "ph_",
    "L5": "mi_",
}

# L0's reviewed convergence, carried forward verbatim from the pre-generalisation
# nirmana-l0-analysis-receipts.ts.  Changing either value re-computes every L0
# analysis digest and invalidates the frozen L0 capsules — see --check.
#
# `writer_inventory_sha256` re-pinned 2026-09-06 (D-NATIVE-06, native-ratified
# transparent re-derivation): the previous value (8650e7a7...) was superseded
# because bg_yogas's writer was fixed (a dict-row-as-tuple bug in
# extract_yogas_from_corpus silently yielded 0 corpus-extracted yogas on every
# real dispatch). This aggregate is NOT part of any per-asset
# NirmanaAnalysisReceiptBase (see nirmana-analysis-receipts.ts's
# buildLayerReceipts — only writer_digest_sha256, layer, convergence_commit,
# and the two static grounding constants feed the hashed base); it only gates
# whether NEW analysis-acceptance calls resolve for the layer at all. Verified
# before re-pinning: regenerating platform/src/generated/nirmana-writer-digests.json
# changed exactly one entry (bg_yogas); the other 35 frozen L0 writers' digests
# are byte-identical to before, so no other asset's already-accepted
# analysis_digest is affected by this re-pin.
#
# Re-pinned again 2026-09-07 (issue #2122, F-D21/F-D23): bg_vidhi_primitives.py's
# from_moon_view entry was corrected (re-pointed from the inert reference_point
# arg on ganita_chart_facts_get to the real ganita_transit_anchors_get consumer).
# Same verification discipline: regenerating the writer inventory changed
# exactly one entry (bg_vidhi_primitives); the other 35 frozen L0 writers'
# digests (bg_yogas included) are byte-identical to the prior re-pin.
L0_FROZEN_PINS = {
    "convergence_commit": "49bb5c98b864a2cb2fee037cdb7f14f6892a8263",
    "writer_inventory_sha256": "5125cccb68715ebc6054c3ce47bc4c047684445249503a4c4dabd85e0d036178",
    "receipt_count": 40,
}


def layer_inventory_sha256(writer_digests: dict[str, str], prefix: str) -> str:
    """Aggregate over one layer's slice, matching the TS assert byte for byte.

    Mirrors assertNirmanaL0WriterInventoryMatchesConvergence: filter by prefix,
    sort by key, JSON.stringify (no spaces, no ASCII escaping), sha256.
    """
    layer_inventory = {
        asset_id: digest
        for asset_id, digest in sorted(writer_digests.items())
        if asset_id.startswith(prefix)
    }
    if not layer_inventory:
        raise SystemExit(f"writer inventory has no entries for prefix {prefix!r}")
    encoded = json.dumps(
        layer_inventory, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def load_frozen_manifest_assets() -> list[dict[str, Any]]:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit(
            "DATABASE_URL is required to regenerate pins (the frozen manifest is the "
            "authority for receipt_count and non_writer_assets). Use --check offline."
        )
    import psycopg2  # imported lazily so --check needs no driver

    connection = psycopg2.connect(database_url)
    connection.set_session(readonly=True)
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT manifest FROM nirmana_evidence.nirmana_elevation_campaign_definitions "
            "WHERE definition_status='frozen' AND superseded_at IS NULL"
        )
        rows = cursor.fetchall()
    finally:
        connection.close()
    if len(rows) != 1:
        raise SystemExit(f"expected exactly one frozen campaign definition; found {len(rows)}")
    return list(rows[0][0]["assets"])


def build_pins(
    writer_digests: dict[str, str],
    manifest_assets: list[dict[str, Any]],
    convergence_commit: str,
) -> dict[str, Any]:
    layers: dict[str, Any] = {}
    for layer, prefix in LAYER_PREFIX.items():
        manifest_ids = sorted(
            asset["asset_id"] for asset in manifest_assets if asset["layer"] == layer
        )
        if not manifest_ids:
            raise SystemExit(f"frozen manifest carries no assets for {layer}")
        non_writer = [a for a in manifest_ids if a not in writer_digests]
        pin = {
            "asset_prefix": prefix,
            "convergence_commit": convergence_commit,
            "writer_inventory_sha256": layer_inventory_sha256(writer_digests, prefix),
            "receipt_count": len(manifest_ids),
            "non_writer_assets": non_writer,
        }
        if layer == "L0":
            # convergence_commit is a RECORDED INPUT, not a derived value: it
            # names the commit whose inventory was reviewed, which no later
            # regeneration can rediscover.  Carry L0's forward verbatim.
            pin["convergence_commit"] = L0_FROZEN_PINS["convergence_commit"]
            # The other two ARE derived, so they must still agree with the frozen
            # record.  Drift here means the L0 writer inventory or manifest cohort
            # has moved under 29 already-frozen capsules — a real finding.  Stop
            # rather than silently re-pin it.
            for key in ("writer_inventory_sha256", "receipt_count"):
                if pin[key] != L0_FROZEN_PINS[key]:
                    raise SystemExit(
                        f"L0 {key} derives to {pin[key]!r} but is frozen at "
                        f"{L0_FROZEN_PINS[key]!r}; re-pinning L0 would invalidate "
                        "its accepted analyses. Investigate before regenerating."
                    )
        layers[layer] = pin
    return {
        "version": PINS_VERSION,
        "layers": layers,
        "history": {layer: [] for layer in LAYER_PREFIX},
    }


def render(pins: dict[str, Any]) -> str:
    return json.dumps(pins, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def layer_writer_slice(writer_digests: dict[str, str], prefix: str) -> dict[str, str]:
    return {
        asset_id: digest
        for asset_id, digest in sorted(writer_digests.items())
        if asset_id.startswith(prefix)
    }


def generation_id(layer: str, pin: dict[str, Any]) -> str:
    return (
        f"{layer.lower()}:{pin['convergence_commit'][:12]}:"
        f"{pin['writer_inventory_sha256'][:12]}"
    )


def _validate_sha(value: str, label: str) -> None:
    if not re.fullmatch(r"[a-f0-9]{40}", value):
        raise SystemExit(f"{label} must be an exact 40-hex commit, got {value!r}")


def _is_immutable_ref(value: str) -> bool:
    return bool(
        re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", value)
        or re.fullmatch(r"[^@\s]+@[a-f0-9]{40}|[^@\s]+@[a-f0-9]{64}", value)
    )


def _inventory_at_commit(commit: str) -> dict[str, str]:
    _validate_sha(commit, "source commit")
    try:
        raw = subprocess.run(
            [
                "git",
                "show",
                f"{commit}:platform/src/generated/nirmana-writer-digests.json",
            ],
            cwd=Path(__file__).resolve().parents[3],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        return json.loads(raw)["writers"]
    except (subprocess.CalledProcessError, KeyError, json.JSONDecodeError) as exc:
        raise SystemExit(
            f"source commit {commit} does not carry a readable writer inventory"
        ) from exc


def parse_classifications(values: list[str]) -> dict[str, str]:
    classifications: dict[str, str] = {}
    for value in values:
        asset_id, separator, classification = value.partition("=")
        if not separator or not asset_id:
            raise SystemExit(
                f"classification must be asset_id=category, got {value!r}"
            )
        if classification not in ALLOWED_DELTA_CLASSIFICATIONS:
            raise SystemExit(
                f"unsupported classification {classification!r}; expected one of "
                f"{sorted(ALLOWED_DELTA_CLASSIFICATIONS)}"
            )
        if asset_id in classifications:
            raise SystemExit(f"duplicate classification for {asset_id}")
        classifications[asset_id] = classification
    return classifications


def admit_successor(
    committed: dict[str, Any],
    *,
    layer: str,
    previous_writer_digests: dict[str, str],
    candidate_writer_digests: dict[str, str],
    source_commit: str,
    review_refs: list[str],
    authority_decision: str,
    authority_commit: str,
    reason: str,
    classifications: dict[str, str],
    historical_snapshot_commit: str,
) -> dict[str, Any]:
    """Append one fail-closed provenance successor without rewriting history.

    The implementation predecessor carries the candidate inventory.  This
    receipt commit therefore references an already-immutable tree and never
    tries to name its own future SHA.  The superseded pin plus its complete
    layer writer snapshot remain embedded so historical receipt bases can be
    reconstructed byte-for-byte without consulting mutable current files.
    """
    if layer not in LAYER_PREFIX:
        raise SystemExit(f"unknown layer {layer!r}; expected one of {sorted(LAYER_PREFIX)}")
    _validate_sha(source_commit, "source commit")
    _validate_sha(authority_commit, "authority commit")
    _validate_sha(historical_snapshot_commit, "historical snapshot commit")
    if not authority_decision.strip() or not reason.strip():
        raise SystemExit("authority decision and reason must be non-empty")
    if not review_refs or any(
        not _is_immutable_ref(ref) or "PENDING" in ref.upper() for ref in review_refs
    ):
        raise SystemExit("at least one completed immutable review ref is required")

    document = json.loads(json.dumps(committed))
    if document.get("version") == LEGACY_PINS_VERSION:
        document["version"] = PINS_VERSION
        document["history"] = {known_layer: [] for known_layer in LAYER_PREFIX}
    elif document.get("version") != PINS_VERSION:
        raise SystemExit(
            f"cannot admit successor from pins version {document.get('version')!r}"
        )
    document.setdefault("history", {known_layer: [] for known_layer in LAYER_PREFIX})

    prefix = LAYER_PREFIX[layer]
    old_pin = document["layers"][layer]
    old_slice = layer_writer_slice(previous_writer_digests, prefix)
    new_slice = layer_writer_slice(candidate_writer_digests, prefix)
    old_aggregate = layer_inventory_sha256(previous_writer_digests, prefix)
    new_aggregate = layer_inventory_sha256(candidate_writer_digests, prefix)
    if old_aggregate != old_pin.get("writer_inventory_sha256"):
        raise SystemExit(
            f"{layer} historical inventory derives {old_aggregate}, but the active "
            f"predecessor pin says {old_pin.get('writer_inventory_sha256')}"
        )
    changed_assets = sorted(
        asset_id
        for asset_id in set(old_slice) | set(new_slice)
        if old_slice.get(asset_id) != new_slice.get(asset_id)
    )
    if not changed_assets:
        raise SystemExit(f"{layer} has no source delta to admit")
    if sorted(classifications) != changed_assets:
        missing = sorted(set(changed_assets) - set(classifications))
        excess = sorted(set(classifications) - set(changed_assets))
        raise SystemExit(
            f"{layer} classifications must cover exactly the changed assets; "
            f"missing={missing}, excess={excess}"
        )
    unsupported = sorted(
        set(classifications.values()) - ALLOWED_DELTA_CLASSIFICATIONS
    )
    if unsupported:
        raise SystemExit(f"unsupported delta classifications: {unsupported}")
    if "unapproved_foreign_source" in classifications.values():
        raise SystemExit(
            "unapproved/foreign source cannot be admitted; exclude it from the candidate"
        )

    predecessor_generation = old_pin.get("generation_id") or generation_id(layer, old_pin)
    successor_pin = {
        "asset_prefix": prefix,
        "convergence_commit": source_commit,
        "non_writer_assets": list(old_pin.get("non_writer_assets") or []),
        "receipt_count": old_pin["receipt_count"],
        "writer_inventory_sha256": new_aggregate,
    }
    successor_generation = generation_id(layer, successor_pin)
    successor_pin.update(
        {
            "generation_id": successor_generation,
            "supersedes_generation_id": predecessor_generation,
            "admission": {
                "schema_version": SUCCESSOR_SCHEMA_VERSION,
                "authority_decision": authority_decision,
                "authority_commit": authority_commit,
                "source_commit": source_commit,
                "review_refs": sorted(review_refs),
                "reason": reason,
                "changed_assets": changed_assets,
                "delta_classifications": {
                    asset_id: classifications[asset_id] for asset_id in changed_assets
                },
            },
        }
    )
    history_entry = {
        "generation_id": predecessor_generation,
        "historical_snapshot_commit": historical_snapshot_commit,
        "superseded_by_generation_id": successor_generation,
        "pin": old_pin,
        "writer_digests": old_slice,
    }
    existing_ids = {
        entry.get("generation_id") for entry in document["history"].setdefault(layer, [])
    }
    if predecessor_generation in existing_ids:
        raise SystemExit(f"{layer} predecessor generation is already archived")
    document["history"][layer].append(history_entry)
    document["layers"][layer] = successor_pin
    return document


def check(pins: dict[str, Any], writer_digests: dict[str, str]) -> list[str]:
    """Offline verification: every claim in the committed pins must re-derive.

    Deliberately re-derives rather than re-reads, so this fails on a hand-edited
    pin file — the exact failure mode the missing generator allowed.
    """
    failures: list[str] = []
    if pins.get("version") != PINS_VERSION:
        failures.append(f"pins version is {pins.get('version')!r}, expected {PINS_VERSION!r}")
    history = pins.get("history")
    if not isinstance(history, dict):
        failures.append("successor history is missing or is not an object")
        history = {}
    inventory_commit_cache: dict[str, dict[str, str] | None] = {}

    def inventory_at_commit(commit: str, label: str) -> dict[str, str] | None:
        if commit not in inventory_commit_cache:
            try:
                inventory_commit_cache[commit] = _inventory_at_commit(commit)
            except SystemExit as exc:
                failures.append(f"{label}: {exc}")
                inventory_commit_cache[commit] = None
        return inventory_commit_cache[commit]

    for layer, prefix in LAYER_PREFIX.items():
        pin = pins.get("layers", {}).get(layer)
        if pin is None:
            failures.append(f"{layer}: missing from the pin record")
            continue
        if pin.get("asset_prefix") != prefix:
            failures.append(f"{layer}: asset_prefix {pin.get('asset_prefix')!r} != {prefix!r}")
        if not re.fullmatch(r"[a-f0-9]{40}", str(pin.get("convergence_commit", ""))):
            failures.append(f"{layer}: convergence commit is invalid")
        invalid_active_digests = sorted(
            asset_id
            for asset_id, digest in layer_writer_slice(writer_digests, prefix).items()
            if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest)
        )
        if invalid_active_digests:
            failures.append(
                f"{layer}: current writer inventory carries invalid digests for "
                f"{invalid_active_digests}"
            )
        derived = layer_inventory_sha256(writer_digests, prefix)
        if pin.get("writer_inventory_sha256") != derived:
            failures.append(
                f"{layer}: writer_inventory_sha256 is stale — committed "
                f"{pin.get('writer_inventory_sha256')}, current inventory derives {derived}"
            )
        expected_receipts = pin.get("receipt_count")
        actual_receipts = sum(
            1
            for asset_id in writer_digests
            if asset_id.startswith(prefix) and asset_id not in SUPPORTING_WRITERS
        ) + len(pin.get("non_writer_assets") or [])
        if expected_receipts != actual_receipts:
            failures.append(
                f"{layer}: receipt_count {expected_receipts} != "
                f"{actual_receipts} writers+non-writers currently available"
            )
        current_generation = pin.get("generation_id")
        if current_generation and current_generation != generation_id(layer, pin):
            failures.append(
                f"{layer}: generation_id {current_generation!r} does not match its pin"
            )
        if current_generation:
            admission = pin.get("admission")
            if not isinstance(admission, dict):
                failures.append(f"{layer}: successor pin has no admission record")
            else:
                if admission.get("schema_version") != SUCCESSOR_SCHEMA_VERSION:
                    failures.append(f"{layer}: successor admission schema is invalid")
                if admission.get("source_commit") != pin.get("convergence_commit"):
                    failures.append(
                        f"{layer}: successor source commit does not match its convergence pin"
                    )
                source_commit = str(admission.get("source_commit", ""))
                if re.fullmatch(r"[a-f0-9]{40}", source_commit):
                    source_inventory = inventory_at_commit(
                        source_commit, f"{layer} source commit"
                    )
                    if (
                        source_inventory is not None
                        and layer_writer_slice(source_inventory, prefix)
                        != layer_writer_slice(writer_digests, prefix)
                    ):
                        failures.append(
                            f"{layer}: current layer inventory does not match its "
                            "immutable source commit"
                        )
                if not re.fullmatch(
                    r"[a-f0-9]{40}", str(admission.get("authority_commit", ""))
                ):
                    failures.append(f"{layer}: successor authority commit is invalid")
                if not str(admission.get("authority_decision", "")).strip():
                    failures.append(f"{layer}: successor authority decision is missing")
                if not str(admission.get("reason", "")).strip():
                    failures.append(f"{layer}: successor reason is missing")
                review_refs = admission.get("review_refs")
                if (
                    not isinstance(review_refs, list)
                    or not review_refs
                    or review_refs != sorted(set(review_refs))
                    or any(
                        not isinstance(ref, str)
                        or not _is_immutable_ref(ref)
                        or "PENDING" in ref.upper()
                        for ref in review_refs
                    )
                ):
                    failures.append(f"{layer}: completed immutable review refs are invalid")
                changed_assets = admission.get("changed_assets")
                classifications = admission.get("delta_classifications")
                if not isinstance(changed_assets, list) or changed_assets != sorted(set(changed_assets)):
                    failures.append(f"{layer}: changed_assets must be sorted and unique")
                if not isinstance(classifications, dict) or sorted(classifications) != changed_assets:
                    failures.append(f"{layer}: delta classifications do not exactly cover changed_assets")
                elif any(value not in ALLOWED_DELTA_CLASSIFICATIONS for value in classifications.values()):
                    failures.append(f"{layer}: delta classification vocabulary is invalid")
                elif "unapproved_foreign_source" in classifications.values():
                    failures.append(f"{layer}: an unapproved/foreign delta was admitted")

        seen_generations: set[str] = set()
        layer_history = history.get(layer, [])
        if not isinstance(layer_history, list):
            failures.append(f"{layer}: history is not a list")
            continue
        for entry in layer_history:
            if not isinstance(entry, dict):
                failures.append(f"{layer}: malformed history entry")
                continue
            archived_pin = entry.get("pin")
            archived_writers = entry.get("writer_digests")
            archived_generation = entry.get("generation_id")
            if not isinstance(archived_pin, dict) or not isinstance(archived_writers, dict):
                failures.append(f"{layer}: historical pin or writer snapshot is missing")
                continue
            if archived_pin.get("asset_prefix") != prefix:
                failures.append(f"{layer}: historical pin carries the wrong asset prefix")
            foreign_archived_assets = sorted(
                asset_id
                for asset_id in archived_writers
                if not isinstance(asset_id, str) or not asset_id.startswith(prefix)
            )
            if foreign_archived_assets:
                failures.append(
                    f"{layer}: historical writer snapshot carries foreign assets "
                    f"{foreign_archived_assets}"
                )
            invalid_archived_digests = sorted(
                asset_id
                for asset_id, digest in archived_writers.items()
                if not isinstance(digest, str)
                or not re.fullmatch(r"[a-f0-9]{64}", digest)
            )
            if invalid_archived_digests:
                failures.append(
                    f"{layer}: historical writer snapshot carries invalid digests for "
                    f"{invalid_archived_digests}"
                )
            if archived_generation != generation_id(layer, archived_pin):
                failures.append(f"{layer}: historical generation id does not match its pin")
            if archived_generation in seen_generations:
                failures.append(f"{layer}: duplicate historical generation {archived_generation}")
            seen_generations.add(archived_generation)
            try:
                archived_aggregate = layer_inventory_sha256(archived_writers, prefix)
            except SystemExit as exc:
                failures.append(f"{layer}: invalid historical writer snapshot: {exc}")
                continue
            if archived_aggregate != archived_pin.get("writer_inventory_sha256"):
                failures.append(
                    f"{layer}: historical aggregate {archived_aggregate} does not match "
                    f"{archived_pin.get('writer_inventory_sha256')}"
                )
            archived_count = sum(
                1 for asset_id in archived_writers
                if asset_id.startswith(prefix) and asset_id not in SUPPORTING_WRITERS
            ) + len(archived_pin.get("non_writer_assets") or [])
            if archived_count != archived_pin.get("receipt_count"):
                failures.append(f"{layer}: historical receipt count is not reconstructable")
            if not re.fullmatch(r"[a-f0-9]{40}", str(entry.get("historical_snapshot_commit", ""))):
                failures.append(f"{layer}: historical snapshot commit is invalid")
            else:
                historical_inventory = inventory_at_commit(
                    entry["historical_snapshot_commit"],
                    f"{layer} historical snapshot commit",
                )
                if (
                    historical_inventory is not None
                    and layer_writer_slice(historical_inventory, prefix)
                    != archived_writers
                ):
                    failures.append(
                        f"{layer}: archived writer snapshot does not match its immutable "
                        "historical commit"
                    )

        if current_generation:
            predecessor_generation = pin.get("supersedes_generation_id")
            predecessor_entries = [
                entry
                for entry in layer_history
                if isinstance(entry, dict)
                and entry.get("generation_id") == predecessor_generation
            ]
            if len(predecessor_entries) != 1:
                failures.append(
                    f"{layer}: successor does not name exactly one archived predecessor"
                )
            else:
                predecessor = predecessor_entries[0]
                if predecessor.get("superseded_by_generation_id") != current_generation:
                    failures.append(
                        f"{layer}: predecessor does not point to the active successor"
                    )
                archived_writers = predecessor.get("writer_digests")
                admission = pin.get("admission")
                if isinstance(archived_writers, dict) and isinstance(admission, dict):
                    current_slice = layer_writer_slice(writer_digests, prefix)
                    exact_delta = sorted(
                        asset_id
                        for asset_id in set(archived_writers) | set(current_slice)
                        if archived_writers.get(asset_id) != current_slice.get(asset_id)
                    )
                    if admission.get("changed_assets") != exact_delta:
                        failures.append(
                            f"{layer}: admitted changed_assets do not match the exact "
                            "predecessor-to-successor delta"
                        )

        all_generation_ids = seen_generations | ({current_generation} if current_generation else set())
        for entry in layer_history:
            if isinstance(entry, dict) and entry.get("superseded_by_generation_id") not in all_generation_ids:
                failures.append(
                    f"{layer}: historical generation points to an unknown successor"
                )

    l0_history = history.get("L0", []) if isinstance(history, dict) else []
    active_l0 = pins.get("layers", {}).get("L0", {})
    if not all(active_l0.get(key) == value for key, value in L0_FROZEN_PINS.items()) and not any(
        isinstance(entry, dict)
        and all(entry.get("pin", {}).get(key) == frozen_value for key, frozen_value in L0_FROZEN_PINS.items())
        for entry in l0_history
    ):
        failures.append("L0 immutable frozen baseline is absent from successor history")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the committed pins (no DB)")
    parser.add_argument(
        "--convergence-commit",
        help="reviewed commit to pin for layers other than L0 (required to regenerate)",
    )
    parser.add_argument(
        "--admit-successor",
        action="store_true",
        help="append one reviewed layer successor while retaining the complete predecessor",
    )
    parser.add_argument("--source-commit", help="immutable implementation predecessor")
    parser.add_argument(
        "--historical-snapshot-commit",
        help="immutable commit whose writer inventory reconstructs the active predecessor",
    )
    parser.add_argument("--authority-decision", help="decision authorizing this successor")
    parser.add_argument("--authority-commit", help="immutable approval commit")
    parser.add_argument(
        "--review-ref",
        action="append",
        default=[],
        help="completed immutable review reference; repeat when multiple reviews apply",
    )
    parser.add_argument("--reason", help="bounded evidence-backed successor reason")
    parser.add_argument(
        "--classification",
        action="append",
        default=[],
        help="asset_id=classification; must cover every and only changed layer identity",
    )
    parser.add_argument(
        "--layer",
        help=(
            "regenerate ONLY this layer's record (e.g. L3), preserving every other "
            "layer's committed pin verbatim. Use this when your own writers changed: "
            "the whole-file regeneration restates every non-L0 layer's "
            "convergence_commit, which is a false claim about other sessions' review "
            "state. See NIRMANA issue #1814."
        ),
    )
    parser.add_argument("--output", type=Path, default=PINS_PATH)
    args = parser.parse_args()

    writer_digests = json.loads(WRITER_DIGESTS_PATH.read_text(encoding="utf-8"))["writers"]

    if args.check:
        if not args.output.is_file():
            print(f"ERROR: {args.output} does not exist", file=sys.stderr)
            return 1
        failures = check(json.loads(args.output.read_text(encoding="utf-8")), writer_digests)
        if failures:
            print("Nirmana analysis layer pins are STALE or INVALID:", file=sys.stderr)
            for failure in failures:
                print(f"  - {failure}", file=sys.stderr)
            print(
                "\nRegenerate with: python -m scripts.generate.nirmana_analysis_layer_pins "
                "--convergence-commit <reviewed sha>",
                file=sys.stderr,
            )
            return 1
        print(f"Nirmana analysis layer pins are current ({args.output.name}).")
        return 0

    if args.admit_successor:
        required = {
            "--layer": args.layer,
            "--source-commit": args.source_commit,
            "--historical-snapshot-commit": args.historical_snapshot_commit,
            "--authority-decision": args.authority_decision,
            "--authority-commit": args.authority_commit,
            "--reason": args.reason,
        }
        missing = [flag for flag, value in required.items() if not value]
        if missing:
            print(f"ERROR: successor admission requires {', '.join(missing)}", file=sys.stderr)
            return 1
        source_inventory = _inventory_at_commit(args.source_commit)
        if source_inventory != writer_digests:
            print(
                "ERROR: current writer inventory is not byte-equivalent to the immutable "
                "source commit inventory",
                file=sys.stderr,
            )
            return 1
        previous_inventory = _inventory_at_commit(args.historical_snapshot_commit)
        committed = json.loads(args.output.read_text(encoding="utf-8"))
        successor = admit_successor(
            committed,
            layer=args.layer,
            previous_writer_digests=previous_inventory,
            candidate_writer_digests=writer_digests,
            source_commit=args.source_commit,
            review_refs=args.review_ref,
            authority_decision=args.authority_decision,
            authority_commit=args.authority_commit,
            reason=args.reason,
            classifications=parse_classifications(args.classification),
            historical_snapshot_commit=args.historical_snapshot_commit,
        )
        args.output.write_text(render(successor), encoding="utf-8")
        print(
            f"Wrote {args.output} -- admitted {args.layer} successor "
            f"{successor['layers'][args.layer]['generation_id']}."
        )
        return 0

    if not args.convergence_commit or len(args.convergence_commit) != 40:
        print(
            "ERROR: --convergence-commit <40-hex sha> is required to regenerate.",
            file=sys.stderr,
        )
        return 1
    pins = build_pins(
        writer_digests, load_frozen_manifest_assets(), args.convergence_commit
    )

    if args.layer:
        # Per-layer regeneration (NIRMANA issue #1814, Conductor ruling option A).
        #
        # Whole-file regeneration rewrites every non-L0 layer's convergence_commit
        # from the single --convergence-commit argument. For a layer that did not
        # change, that restates "the reviewed commit whose writer inventory this
        # pins" as a value nobody reviewed it at -- a false claim about four other
        # sessions' review state, and the D-CND-16 defect committed by a tool
        # rather than by a comment. It also makes two lanes re-pinning in parallel
        # fight over one file.
        #
        # So: splice in ONLY the named layer's freshly-derived record and carry
        # every other layer's committed record through byte-for-byte.
        if not args.output.is_file():
            print(f"ERROR: --layer needs an existing {args.output}", file=sys.stderr)
            return 1
        committed = json.loads(args.output.read_text(encoding="utf-8"))
        if args.layer not in committed.get("layers", {}):
            print(
                f"ERROR: unknown layer {args.layer!r}; "
                f"known: {sorted(committed.get('layers', {}))}",
                file=sys.stderr,
            )
            return 1
        if args.layer == "L0":
            # L0's three pins are frozen against 29 accepted capsules. Re-deriving
            # them would invalidate every one of them, and no L0 writer change is
            # in scope for this campaign.
            print(
                "ERROR: refusing to re-pin L0 -- its pins are frozen against "
                "accepted capsules (#1715 requirement 3).",
                file=sys.stderr,
            )
            return 1
        fresh = pins["layers"][args.layer]
        before = committed["layers"][args.layer]
        committed["layers"][args.layer] = fresh
        args.output.write_text(render(committed), encoding="utf-8")
        moved = [k for k in fresh if before.get(k) != fresh.get(k)]
        print(f"Wrote {args.output} -- {args.layer} only.")
        print(f"  fields changed: {', '.join(moved) if moved else '(none)'}")
        print(f"  layers untouched: {', '.join(k for k in committed['layers'] if k != args.layer)}")
        return 0

    args.output.write_text(render(pins), encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
