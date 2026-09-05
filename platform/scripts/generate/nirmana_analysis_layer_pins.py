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
import sys
from pathlib import Path
from typing import Any

GENERATED = Path(__file__).resolve().parents[2] / "src" / "generated"
WRITER_DIGESTS_PATH = GENERATED / "nirmana-writer-digests.json"
PINS_PATH = GENERATED / "nirmana-analysis-layer-pins.json"

PINS_VERSION = "nirmana-analysis-layer-pins/v1"
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
L0_FROZEN_PINS = {
    "convergence_commit": "49bb5c98b864a2cb2fee037cdb7f14f6892a8263",
    "writer_inventory_sha256": "8650e7a7e85beb27adbb66087344a13f3ee77b3fb1c84ebbb6170b9d7ad1c2ae",
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
    return {"version": PINS_VERSION, "layers": layers}


def render(pins: dict[str, Any]) -> str:
    return json.dumps(pins, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def check(pins: dict[str, Any], writer_digests: dict[str, str]) -> list[str]:
    """Offline verification: every claim in the committed pins must re-derive.

    Deliberately re-derives rather than re-reads, so this fails on a hand-edited
    pin file — the exact failure mode the missing generator allowed.
    """
    failures: list[str] = []
    if pins.get("version") != PINS_VERSION:
        failures.append(f"pins version is {pins.get('version')!r}, expected {PINS_VERSION!r}")
    for layer, prefix in LAYER_PREFIX.items():
        pin = pins.get("layers", {}).get(layer)
        if pin is None:
            failures.append(f"{layer}: missing from the pin record")
            continue
        if pin.get("asset_prefix") != prefix:
            failures.append(f"{layer}: asset_prefix {pin.get('asset_prefix')!r} != {prefix!r}")
        derived = layer_inventory_sha256(writer_digests, prefix)
        if pin.get("writer_inventory_sha256") != derived:
            failures.append(
                f"{layer}: writer_inventory_sha256 is stale — committed "
                f"{pin.get('writer_inventory_sha256')}, current inventory derives {derived}"
            )
        expected_receipts = pin.get("receipt_count")
        actual_receipts = sum(
            1 for asset_id in writer_digests if asset_id.startswith(prefix)
        ) + len(pin.get("non_writer_assets") or [])
        if expected_receipts != actual_receipts:
            failures.append(
                f"{layer}: receipt_count {expected_receipts} != "
                f"{actual_receipts} writers+non-writers currently available"
            )
    for key, frozen_value in L0_FROZEN_PINS.items():
        if pins.get("layers", {}).get("L0", {}).get(key) != frozen_value:
            failures.append(
                f"L0 {key} has moved off its frozen value {frozen_value!r} — this would "
                "invalidate the accepted L0 analyses behind 29 frozen capsules"
            )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the committed pins (no DB)")
    parser.add_argument(
        "--convergence-commit",
        help="reviewed commit to pin for layers other than L0 (required to regenerate)",
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
