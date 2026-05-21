"""
validators.p5_signal_id_resolution — P5 signal ID resolution validator.
Phase B.1. Per M2A_EXEC_PLAN_v1_0.md §PLAN B.1 Task 1.5 + PHASE_B_PLAN_v1_0.md §E.6.
Validates that all SIG.MSR.NNN IDs in chunk content resolve against MSR_v5_0.md registry.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# ── Signal registry ──────────────────────────────────────────────────────────

_SIGNAL_REGISTRY: set[str] | None = None

_SIGNAL_ID_PATTERN = re.compile(r"\bSIG\.MSR\.(\d{3}[a-z]?)\b")

_MSR_PATH = (
    Path(__file__).parent.parent.parent.parent.parent
    / "025_HOLISTIC_SYNTHESIS"
    / "MSR_v5_0.md"
)


def _build_signal_registry() -> set[str]:
    """Scan MSR_v5_0.md and cache all SIG.MSR.NNN IDs."""
    if not _MSR_PATH.exists():
        alt = Path(__file__).parents[5] / "025_HOLISTIC_SYNTHESIS" / "MSR_v5_0.md"
        path = alt if alt.exists() else _MSR_PATH
    else:
        path = _MSR_PATH
    text = path.read_text(encoding="utf-8")
    # Boundary lines look like "SIG.MSR.001:" or "SIG.MSR.391a:" (sub-signals)
    return {f"SIG.MSR.{m}" for m in re.findall(r"^SIG\.MSR\.(\d{3}[a-z]?):", text, re.MULTILINE)}


def get_signal_registry() -> set[str]:
    global _SIGNAL_REGISTRY
    if _SIGNAL_REGISTRY is None:
        _SIGNAL_REGISTRY = _build_signal_registry()
    return _SIGNAL_REGISTRY


def validate(chunk: dict[str, Any]) -> dict[str, Any]:
    """
    Validate P5 signal ID resolution.

    Rules:
    - msr_signal doc_type chunks: signal_id in metadata MUST be in registry → BLOCK if not.
    - All other chunks: scan content for SIG.MSR.NNN patterns; any match NOT in registry
      → emit WARNING (not block).

    Returns:
        {"valid": bool, "citation_valid": bool, "reason": str | None}
        valid=False means BLOCK (hard stop on write).
    """
    doc_type = chunk.get("doc_type", "")
    content = chunk.get("content", "")
    metadata = chunk.get("metadata", {})
    registry = get_signal_registry()

    if doc_type == "msr_signal":
        signal_id = metadata.get("signal_id", "")
        if not signal_id:
            signal_id = chunk.get("signal_id", "")
        if signal_id not in registry:
            return {
                "valid": False,
                "citation_valid": False,
                "reason": f"P5: msr_signal chunk has unresolvable signal_id '{signal_id}' — BLOCK write",
            }
        return {"valid": True, "citation_valid": True, "reason": None}

    # All other doc types: scan content for references
    refs_in_content = set(_SIGNAL_ID_PATTERN.findall(content))
    unresolved = {f"SIG.MSR.{n}" for n in refs_in_content if f"SIG.MSR.{n}" not in registry}
    if unresolved:
        return {
            "valid": True,  # warning, not block
            "citation_valid": True,
            "reason": f"P5: content references unresolvable signal IDs (WARNING): {sorted(unresolved)}",
        }

    return {"valid": True, "citation_valid": True, "reason": None}
