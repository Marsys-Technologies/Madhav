"""
mechanisms.py -- significator definitions, ported verbatim from
platform/scripts/audit/t0_retrodiction/lib/mechanisms.ts (same
LOSS_SIGNIFICATORS / WINDFALL_SIGNIFICATORS / DOMAIN_LORDS /
CATEGORY_TO_DOMAIN tables -- these are NOT re-derived here, they are copied
from the already-verified-live T-0 constants, cross-checked in this lane
against a fresh `ganita_dasha_lord_capability_get` call on 482012f1
(2026-07-18): DOMAIN_LORDS below matches the live tool response exactly --
wealth={Jupiter:1.0,Saturn:0.8,Venus:1.0}, career={Saturn:0.8},
health={Mercury:1.0}, marriage={Venus:1.0} -- see
cache/dasha_lord_capability.json for the raw cross-check).
"""
from __future__ import annotations

LOSS_SIGNIFICATORS: dict[str, float] = {"Mars": 1.0}
WINDFALL_SIGNIFICATORS: dict[str, float] = {"Venus": 1.0, "Jupiter": 1.0}

DOMAIN_LORDS: dict[str, dict[str, float]] = {
    "wealth": {"Jupiter": 1.0, "Saturn": 0.8, "Venus": 1.0},
    "career": {"Saturn": 0.8},
    "health": {"Mercury": 1.0},
    "marriage": {"Venus": 1.0},
    "general": {"Mars": 1.0, "Sun": 1.0},
}

CATEGORY_TO_DOMAIN: dict[str, str] = {
    "finance": "wealth",
    "loss": "wealth",
    "career": "career",
    "health": "health",
    "psychological": "health",
    "relationship": "marriage",
    "family": "marriage",
    "education": "general",
    "creative": "general",
    "spiritual": "general",
    "travel": "general",
    "other": "general",
    "residential+travel": "general",
}


def domain_for_category(category: str) -> str:
    return CATEGORY_TO_DOMAIN.get(category, "general")


def significators_for_category(category: str) -> dict[str, float]:
    domain = domain_for_category(category)
    return DOMAIN_LORDS.get(domain, DOMAIN_LORDS["general"])
