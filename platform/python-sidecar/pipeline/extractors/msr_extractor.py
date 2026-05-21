"""
pipeline.extractors.msr_extractor — Extract MSR signals from MSR_v5_0.md.
Phase 14D Stream B. Calls _parse_signals from rag.chunkers.msr_signal.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from rag.chunkers.msr_signal import _parse_signals

log = logging.getLogger(__name__)

SOURCE_FILE = "025_HOLISTIC_SYNTHESIS/MSR_v5_0.md"
SOURCE_VERSION = "5.0"
EXPECTED_COUNT = 573

_VALENCE_MAP: dict[str, str] = {
    "benefic": "positive",
    "malefic": "negative",
}


def _normalize_valence(raw: str) -> str:
    """Normalize valence: benefic → positive, malefic → negative, others pass through."""
    return _VALENCE_MAP.get(raw.lower().strip(), raw.lower().strip()) if raw else "neutral"


def _extract_entities(entities: list[Any]) -> tuple[list[str], list[int], list[str]]:
    """Split entities_involved into planets, houses, and signs lists."""
    planets: list[str] = []
    houses: list[int] = []
    signs: list[str] = []

    for e in entities:
        if not isinstance(e, str):
            continue
        if e.startswith("PLN."):
            planets.append(e.split(".", 1)[1])
        elif e.startswith("HSE."):
            part = e.split(".", 1)[1]
            if part.isdigit():
                houses.append(int(part))
        elif e.startswith("SGN."):
            signs.append(e.split(".", 1)[1])

    return planets, houses, signs


def extract_msr_signals(repo_root: str) -> list[dict[str, Any]]:
    """
    Parse MSR_v5_0.md and return one dict per signal matching the l25_msr_signals schema.

    Args:
        repo_root: Absolute path to the repository root.

    Returns:
        List of exactly 499 signal dicts.

    Raises:
        FileNotFoundError: If MSR_v5_0.md is not found.
        ValueError: If the parsed count is not exactly 499.
    """
    msr_path = Path(repo_root) / SOURCE_FILE
    if not msr_path.exists():
        raise FileNotFoundError(f"MSR_v5_0.md not found at {msr_path}")

    raw_signals = _parse_signals(msr_path)
    rows: list[dict[str, Any]] = []

    for sig_id, _yaml_body, data in raw_signals:
        # Derive signal_number from the trailing digits in sig_id (SIG.MSR.001 → 1)
        num_part = sig_id.rsplit(".", 1)[-1]
        # Strip any trailing lowercase letters (e.g. SIG.MSR.001a → "001a" → strip alpha)
        digits = "".join(c for c in num_part if c.isdigit())
        signal_number = int(digits) if digits else 0

        # Core fields
        name = data.get("signal_name", sig_id)
        category = data.get("signal_type", "unknown")
        raw_valence = data.get("valence", "neutral")
        valence = _normalize_valence(str(raw_valence))

        # Weight: prefer strength_score, fall back to confidence
        weight_raw = data.get("strength_score") or data.get("confidence")
        weight = float(weight_raw) if weight_raw is not None else None

        # Entity decomposition
        entities_raw = data.get("entities_involved", [])
        if not isinstance(entities_raw, list):
            entities_raw = []
        planets, houses, signs = _extract_entities(entities_raw)

        # 8 new source fields (raw, unmodified; None when absent)
        signal_type_raw: str | None = data.get("signal_type") or None
        temporal_activation_raw: str | None = data.get("temporal_activation") or None
        valence_raw: str | None = data.get("valence") or None
        entities_involved_raw = entities_raw if entities_raw else None
        supporting_rules_raw = data.get("supporting_rules") or None
        if supporting_rules_raw is not None and not isinstance(supporting_rules_raw, list):
            supporting_rules_raw = None
        rpt_deep_dive_raw: str | None = data.get("rpt_deep_dive") or None
        v6_ids_consumed_raw = data.get("v6_ids_consumed") or None
        if v6_ids_consumed_raw is not None and not isinstance(v6_ids_consumed_raw, list):
            v6_ids_consumed_raw = None
        prior_id_raw: str | None = data.get("prior_id") or None

        # Provenance dict
        provenance: dict[str, Any] = {
            "source_uri": SOURCE_FILE,
            "source_version": SOURCE_VERSION,
            "signal_id": sig_id,
        }

        row: dict[str, Any] = {
            "signal_id": sig_id,
            "signal_number": signal_number,
            "name": name,
            "category": category,
            "valence": valence,
            "weight": weight,
            "planets_involved": planets,
            "houses_involved": houses,
            "signs_involved": signs,
            "entities_involved": entities_raw,
            "description": name,
            "source_section": f"MSR_v5_0 §{sig_id}",
            "provenance": provenance,
            # New source fields for msr_signals (raw, not normalized)
            "signal_type": signal_type_raw,
            "temporal_activation": temporal_activation_raw,
            "valence_raw": valence_raw,
            "entities_involved_raw": entities_involved_raw,
            "supporting_rules": supporting_rules_raw,
            "rpt_deep_dive": rpt_deep_dive_raw,
            "v6_ids_consumed": v6_ids_consumed_raw,
            "prior_id": prior_id_raw,
        }
        rows.append(row)

    if len(rows) != EXPECTED_COUNT:
        raise ValueError(
            f"MSR extractor expected {EXPECTED_COUNT} signals, got {len(rows)}. "
            "Check MSR_v5_0.md parse."
        )

    log.info("msr_extractor: extracted %d signals", len(rows))
    return rows
