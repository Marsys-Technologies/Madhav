"""
reconciliation.py — internal-consistency checks (NO external oracle).

Two invariants every chart must satisfy:
  1. House 1's sign equals the Lagna (ascendant) sign — whole-sign discipline.
  2. Rahu and Ketu are 180 deg apart (within tolerance).

These are pure structural checks against the engine's own output; they do not
compare to any external ground truth (per brief: verification is
internal-consistency ONLY).
"""
from __future__ import annotations

from typing import Any


def _ang_sep(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def reconcile(
    ascendant: dict[str, Any],
    houses: list[dict[str, Any]],
    grahas: list[dict[str, Any]],
    *,
    node_tolerance_deg: float = 0.5,
) -> dict[str, Any]:
    issues: list[str] = []

    # 1. House-1 sign == Lagna sign
    asc_sign_id = int(ascendant["sign_id"])
    house1 = next((h for h in houses if int(h.get("house_number", h.get("house_num", 0))) == 1), None)
    house1_ok = house1 is not None and int(house1["sign_id"]) == asc_sign_id
    if not house1_ok:
        issues.append(
            f"house1_sign_mismatch: asc_sign_id={asc_sign_id} "
            f"house1_sign_id={house1.get('sign_id') if house1 else None}"
        )

    # 2. Rahu/Ketu 180 deg apart
    rahu = next((g for g in grahas if g["name"] == "Rahu"), None)
    ketu = next((g for g in grahas if g["name"] == "Ketu"), None)
    nodes_ok = False
    node_sep = None
    if rahu and ketu:
        node_sep = _ang_sep(float(rahu["longitude_deg"]), float(ketu["longitude_deg"]))
        nodes_ok = abs(node_sep - 180.0) <= node_tolerance_deg
        if not nodes_ok:
            issues.append(f"node_opposition_violation: sep={node_sep:.4f} (expected ~180)")
    else:
        issues.append("nodes_missing: Rahu and/or Ketu absent from grahas")

    return {
        "house1_lagna_consistent": house1_ok,
        "nodes_opposed": nodes_ok,
        "node_separation_deg": node_sep,
        "consistent": house1_ok and nodes_ok,
        "issues": issues,
    }
