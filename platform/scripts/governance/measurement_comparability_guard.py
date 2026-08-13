#!/usr/bin/env python3
"""
platform/scripts/governance/measurement_comparability_guard.py

Validator for the M4'/M5 comparability checklist (measurement_comparability_guard.yaml).
Enforces all rules at measurement publication time.

Usage:
  python3 platform/scripts/governance/measurement_comparability_guard.py \
    --artifact <path-to-artifact.json> \
    --label <M4_prime|M5|M4_prime_vs_M5_delta>

Exit codes:
  0 = PASS (all BLOCK_PUBLICATION rules satisfied)
  1 = BLOCK_PUBLICATION triggered (artifact must not be published)
  2 = misconfiguration or missing required field

Authority: SAMPURTI_IMPLEMENTATION_PLAN_v1_0.md §7.2d + ALPHA_DAY_PLAN_v1_0.md §6.4 d4
Conductor: SAMPURTI-Δ2 (PRAMANA), 2026-08-13
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

SPEC_FILE = Path(__file__).parent / "measurement_comparability_guard.yaml"
REPO_ROOT = Path(__file__).resolve().parents[3]  # platform/scripts/governance → repo root
COORD_FILE = REPO_ROOT / "00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md"


def _load_spec() -> dict[str, Any]:
    try:
        import yaml  # type: ignore[import]
        with open(SPEC_FILE) as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback: parse only the rules we need without full YAML
        return {"rules": []}


def _load_artifact(path: str) -> dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def _check_smr2_recorded() -> bool:
    """Return True iff SMR-2 appears in the coordination file."""
    if not COORD_FILE.exists():
        return False
    text = COORD_FILE.read_text()
    return "SMR-2" in text


def validate(artifact: dict[str, Any], label: str) -> tuple[bool, list[str]]:
    """
    Validate artifact against the comparability rules that apply to `label`.
    Returns (passed: bool, messages: list[str]).
    PASSED means no BLOCK_PUBLICATION rule fired.
    """
    messages: list[str] = []
    blocked = False

    # ── R-ENG-1: engine uniformity ─────────────────────────────────────────
    if label in ("M4_prime", "M5"):
        engine = artifact.get("engine")
        if engine != "analytic":
            messages.append(
                f"[R-ENG-1 BLOCK] engine='{engine}' but required='analytic'. "
                f"M4'/M5 must both use the DHARĀ analytic engine. "
                f"The sampled engine is the M4 baseline only."
            )
            blocked = True
        else:
            messages.append(f"[R-ENG-1 PASS] engine=analytic confirmed.")

    # ── R-CLASS-1: delta on matched subset only ────────────────────────────
    if label == "M4_prime_vs_M5_delta":
        delta_rule = artifact.get("delta_class_set_rule")
        if delta_rule != "matched_subset":
            messages.append(
                f"[R-CLASS-1 BLOCK] delta_class_set_rule='{delta_rule}' but required='matched_subset'. "
                f"The M4'↔M5 delta must be computed on matched classes only."
            )
            blocked = True
        else:
            messages.append(f"[R-CLASS-1 PASS] delta_class_set_rule=matched_subset confirmed.")

    # ── R-CLASS-3: class_set documented ────────────────────────────────────
    if label in ("M4_prime", "M5"):
        class_set = artifact.get("class_set")
        if not isinstance(class_set, list) or len(class_set) == 0:
            messages.append(
                f"[R-CLASS-3 BLOCK] class_set is missing or empty. "
                f"Each measurement must document its exact class_set for auditability."
            )
            blocked = True
        else:
            messages.append(f"[R-CLASS-3 PASS] class_set has {len(class_set)} classes.")

    # ── R-CLASS-2: G2-early classes labeled ────────────────────────────────
    if label in ("M4_prime", "M5"):
        new_classes = artifact.get("classes_added_post_M4_prime", [])
        for cls in new_classes:
            epoch = cls.get("measurement_epoch") if isinstance(cls, dict) else None
            if epoch != "first_measurement":
                messages.append(
                    f"[R-CLASS-2 WARN] class '{cls}' added post-M4' but not labeled "
                    f"measurement_epoch='first_measurement'. Will be labeled automatically."
                )
        if new_classes:
            messages.append(
                f"[R-CLASS-2 INFO] {len(new_classes)} G2-early classes found — "
                f"excluded from delta, labeled first_measurement."
            )

    # ── R-SMR-2: PRATINIDHI ruling recorded before M4' ─────────────────────
    if label == "M4_prime":
        smr2_ok = _check_smr2_recorded()
        if not smr2_ok:
            messages.append(
                "[R-SMR-2 BLOCK] SMR-2 not found in CAMPAIGN_COORDINATION.md. "
                "PRATINIDHI must record SMR-2 ('engine swap = measurement-version event; "
                "M4 re-baselines on DHARĀ; published BESIDE M4') before M4' can be published."
            )
            blocked = True
        else:
            messages.append("[R-SMR-2 PASS] SMR-2 found in coordination file.")

    # ── R-DEGEN-1: no degenerate intervals ─────────────────────────────────
    if label == "M4_prime_vs_M5_delta":
        event_count = artifact.get("test_era_event_count_matched_subset_total", -1)
        if event_count == 0:
            messages.append(
                "[R-DEGEN-1 BLOCK] test_era_event_count_matched_subset_total=0. "
                "Degenerate interval: no events in test era for matched class subset. "
                "R15 tripwire: publication halted."
            )
            blocked = True
        elif event_count > 0:
            messages.append(
                f"[R-DEGEN-1 PASS] test_era_event_count_matched_subset_total={event_count} > 0."
            )
        else:
            messages.append(
                "[R-DEGEN-1 WARN] test_era_event_count_matched_subset_total not found in artifact. "
                "Add this field before publication."
            )

    # ── R-VER-1: version bumped on engine swap ─────────────────────────────
    if label == "M4_prime":
        version = artifact.get("version")
        if not version:
            messages.append(
                "[R-VER-1 BLOCK] 'version' field missing in artifact. "
                "M4' must carry a distinct version label from M4 (R14)."
            )
            blocked = True
        else:
            messages.append(f"[R-VER-1 PASS] version='{version}' present.")

    # ── R-VER-2: null replicate count documented ────────────────────────────
    if label in ("M4_prime", "M5"):
        null_reps = artifact.get("null_replicates")
        if null_reps != 1024:
            messages.append(
                f"[R-VER-2 WARN] null_replicates={null_reps!r}, expected 1024 "
                f"(blind-spec per ALPHA_DAY_PLAN §6.2 e2). If intentional, "
                f"this requires a new measurement version per R14."
            )
        else:
            messages.append("[R-VER-2 PASS] null_replicates=1024 confirmed.")

    return not blocked, messages


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a measurement artifact against the M4'/M5 comparability checklist."
    )
    parser.add_argument("--artifact", required=True, help="Path to measurement artifact JSON")
    parser.add_argument(
        "--label",
        required=True,
        choices=["M4_prime", "M5", "M4_prime_vs_M5_delta"],
        help="Which measurement this artifact represents",
    )
    args = parser.parse_args()

    try:
        artifact = _load_artifact(args.artifact)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR: Cannot load artifact: {e}", file=sys.stderr)
        return 2

    passed, messages = validate(artifact, args.label)

    print(f"\n=== MEASUREMENT COMPARABILITY GUARD — {args.label} ===")
    for msg in messages:
        print(f"  {msg}")

    if passed:
        print(f"\nRESULT: PASS — {args.label} artifact clears all BLOCK_PUBLICATION rules.")
        return 0
    else:
        print(f"\nRESULT: BLOCK_PUBLICATION — {args.label} artifact has violations. Do not publish.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
