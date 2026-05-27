"""
sensitive_points.py — Gulika, Mandi, Upapada Lagna, etc.

SCAFFOLD STUB. Unit 1.2 will fill in the full computation. The shape is
present so the schema is satisfied today.
"""

from __future__ import annotations

from typing import Any

from .schema import Ascendant, GrahaState


def compute_sensitive_points(
    jd_ut: float,
    latitude_deg: float,
    longitude_deg: float,
    grahas: list[GrahaState],
    ascendant: Ascendant,
) -> dict[str, Any]:
    """Stub. Returns a dict with the expected keys and `None` placeholders.

    Unit 1.2 replaces this with real Gulika / Mandi (per Phaladeepika §3) and
    Upapada Lagna (Jaimini Sutra §2.1) computations. The schema permits
    `additionalProperties: True`, so this stub does not violate validation.
    """
    return {
        "gulika": {"longitude_deg": None, "sign_id": None, "status": "stub_unit_1.1"},
        "mandi": {"longitude_deg": None, "sign_id": None, "status": "stub_unit_1.1"},
        "upapada_lagna": {"longitude_deg": None, "sign_id": None, "status": "stub_unit_1.1"},
    }
