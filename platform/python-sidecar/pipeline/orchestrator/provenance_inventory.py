"""Generate the sidecar-owned writer digest inventory consumed by the planner.

The web planner must never attempt to parse or hash Python implementation files.
Instead, this module discovers the exact writers the sidecar can execute and
materialises their content digests as a checked-in build artefact.  CI verifies
that the artefact is current, so a code change cannot ship with an old digest.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .asset_runner import get_probe_source_hash, get_writer_source_hash
from .writers import WRITER_REGISTRY, discover_all


INVENTORY_VERSION = "nirmana-writer-digest-inventory/v1"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[3] / "src/generated/nirmana-writer-digests.json"


def build_inventory() -> dict[str, Any]:
    """Return deterministic digests for every executable sidecar writer."""
    discover_all()
    return {
        "version": INVENTORY_VERSION,
        "probe_digest": get_probe_source_hash(),
        "writers": {
            asset_id: get_writer_source_hash(asset_id)
            for asset_id in sorted(WRITER_REGISTRY)
        },
    }


def render_inventory(inventory: dict[str, Any]) -> str:
    return json.dumps(inventory, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or verify Nirmana writer digests")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="fail if the checked-in inventory is stale")
    args = parser.parse_args()

    expected = render_inventory(build_inventory())
    if args.check:
        actual = args.output.read_text(encoding="utf-8") if args.output.is_file() else ""
        if actual != expected:
            raise SystemExit(
                f"writer digest inventory is stale: run python -m "
                f"pipeline.orchestrator.provenance_inventory --output {args.output}"
            )
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(expected, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
