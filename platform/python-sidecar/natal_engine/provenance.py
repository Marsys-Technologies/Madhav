"""
provenance.py — Content-addressed provenance helper (MASTER_PLAN §15.2).

Every chart emitted by `natal_engine.compute_chart` carries a provenance block:

    {
      "chart_id": str,             # content-derived; stable across re-runs with same inputs
      "engine_version": str,       # e.g. "natal_engine/0.1.0-scaffold"
      "ayanamsha_config_id": str,  # e.g. "lahiri-chitrapaksha-true"
      "inputs_hash": str,          # sha256 of canonical-json(inputs)
      "computed_at_iso": str,      # ISO-8601 UTC timestamp at emission
    }

The `inputs_hash` is the load-bearing identity: two charts with identical
inputs + engine_version + ayanamsha_config get the same chart_id, which lets
downstream caches / dedup work without storing the inputs themselves.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .schema import Provenance


def canonical_inputs_hash(inputs: dict[str, Any]) -> str:
    """Deterministic sha256 over canonical-JSON-serialised inputs.

    Keys are sorted; separators are tight. Floats are NOT rounded — caller's
    responsibility to normalise upstream if they want lat/lon at fixed precision.
    """
    blob = json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def make_chart_id(
    inputs_hash: str, engine_version: str, ayanamsha_config_id: str
) -> str:
    """Content-addressed chart id.

    Format: `chart_<12-char hex>` derived from sha256 of the three identity
    components. Short enough to read; long enough to avoid practical collisions.
    """
    composite = f"{inputs_hash}|{engine_version}|{ayanamsha_config_id}".encode("utf-8")
    digest = hashlib.sha256(composite).hexdigest()
    return f"chart_{digest[:12]}"


def build_provenance(
    inputs: dict[str, Any],
    engine_version: str,
    ayanamsha_config_id: str,
    computed_at_iso: str | None = None,
) -> Provenance:
    """Compose a full Provenance row from raw inputs + engine identity."""
    inp_hash = canonical_inputs_hash(inputs)
    chart_id = make_chart_id(inp_hash, engine_version, ayanamsha_config_id)
    ts = computed_at_iso or datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    return Provenance(
        chart_id=chart_id,
        engine_version=engine_version,
        ayanamsha_config_id=ayanamsha_config_id,
        inputs_hash=inp_hash,
        computed_at_iso=ts,
    )
