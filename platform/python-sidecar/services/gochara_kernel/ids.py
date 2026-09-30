"""contact_id and independence_group (WP1_CONTRACTS.md §3.2).

The serialization is pinned so an independent reimplementation produces
identical ids — the plan §10 identity tests (partition-seam stability,
rebuild byte-equality) depend on it.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Any


def floor_to_minute_utc_iso(t_epoch_seconds: float) -> str:
    """WP1 §3.2: floor to the 60-second boundary, render UTC ISO-8601
    `YYYY-MM-DDTHH:MM:00Z`. Floor (not round) so the id never changes under a
    ±30 s jitter and re-partitioning cannot move an id across a minute."""
    floored = math.floor(t_epoch_seconds / 60.0) * 60
    return datetime.fromtimestamp(floored, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:00Z"
    )


def _sha256_canonical(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def contact_id(
    *,
    chart_id: str,
    convention_id: str,
    body: str,
    target_type: str,
    relation: str,
    aspect_deg: float,
    t_exact_jd: float | None,
    target_fact_id: str | None = None,
    target_ref: str | None = None,
    method_version: str,
    t_fallback_jd: float | None = None,
) -> str:
    """WP1_CONTRACTS.md §3.2, verbatim key order semantics.

    `target_identity` is `fact:<target_fact_id>` when a fact id is present,
    else `ref:<target_ref>` — the unambiguous prefix makes the two disjoint.
    `t_exact` is floored to the minute. An episode without an exact crossing
    (N3 truncated span, t_exact_jd=None) is identified by flooring its t_in
    instead — the caller MUST pass t_fallback_jd=t_in — and the payload marks
    the substitution explicitly (`"t_exact": null, "t_in": <floored>`) so a
    truncated contact can never collide with an exact one at the same minute.
    The exact-crossing payload is byte-identical to the pre-fallback shape.
    """
    if target_fact_id is None and target_ref is None:
        raise ValueError("contact_id needs target_fact_id or target_ref")
    identity = (
        f"fact:{target_fact_id}" if target_fact_id is not None else f"ref:{target_ref}"
    )
    payload = {
        "chart_id": str(chart_id),
        "convention_id": str(convention_id),
        "body": str(body),
        "target_kind": str(target_type),
        "target_identity": identity,
        "relation": str(relation),
        "aspect_deg": round(float(aspect_deg) % 360.0, 4),
        "method_version": str(method_version),
    }
    if t_exact_jd is None:
        if t_fallback_jd is None:
            raise ValueError(
                "contact_id for a no-exact episode needs t_fallback_jd (t_in)"
            )
        epoch = (float(t_fallback_jd) - 2440587.5) * 86400.0
        payload["t_exact"] = None
        payload["t_in"] = floor_to_minute_utc_iso(epoch)
    else:
        epoch = (float(t_exact_jd) - 2440587.5) * 86400.0
        payload["t_exact"] = floor_to_minute_utc_iso(epoch)
    return _sha256_canonical(payload)


def independence_group(
    *,
    body: str,
    relation: str,
    aspect_deg: float,
    target_deg: float,
    t_exact_jd: float | None,
    t_fallback_jd: float,
) -> str:
    """One physical contribution reached through several targets or rules
    counts ONCE (H-6). Every episode row naming the same physical
    (body, relation, aspect, target degree, minute-floored instant) event
    shares one independence_group value — the group is computed from the
    PHYSICAL event only, never from the resonance rule that referenced it."""
    epoch = (float(t_exact_jd if t_exact_jd is not None else t_fallback_jd) - 2440587.5) * 86400.0
    payload = {
        "body": str(body),
        "relation": str(relation),
        "aspect_deg": round(float(aspect_deg) % 360.0, 4),
        "target_deg": round(float(target_deg) % 360.0, 4),
        "t_minute": floor_to_minute_utc_iso(epoch),
    }
    return _sha256_canonical(payload)


__all__ = ["contact_id", "floor_to_minute_utc_iso", "independence_group"]
