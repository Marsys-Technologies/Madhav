"""Directed graha dṛṣṭi geometry (pure; no ephemeris, no roots).

The angle table is the kernel's ruled one (BPHS ch.26; N-14: the nodes cast
none) and is imported, never restated. Aspects count forward: a graha at λ
casts its angle-a dṛṣṭi on (λ + a) mod 360, so it reaches a target T when it
sits at (T − a) mod 360. The relation is directed — Saturn's 3rd on a point
does not make that point's occupant aspect Saturn.
"""
from __future__ import annotations

from math import isfinite

from services.gochara_kernel.convention import drishti_angles as _kernel_angles

from .identity import kernel_body


def _arc(a: float, b: float) -> float:
    """Unsigned shortest angular distance in degrees."""
    d = (float(a) - float(b)) % 360.0
    return min(d, 360.0 - d)


def drishti_angles(body: str) -> tuple[float, ...]:
    return _kernel_angles(kernel_body(body))


def aspected_points(body: str, longitude_deg: float) -> tuple[tuple[float, float], ...]:
    """(angle, aspected longitude) for every dṛṣṭi `body` casts from λ."""
    return tuple((a, (float(longitude_deg) + a) % 360.0) for a in drishti_angles(body))


def contact_level(target_deg: float, angle_deg: float) -> float:
    """Where the caster must sit for its angle-a dṛṣṭi to land on the target."""
    return (float(target_deg) - float(angle_deg)) % 360.0


def aspects(body: str, caster_deg: float, target_deg: float, orb_deg: float) -> tuple[float, ...]:
    """The angles by which `body` at caster_deg aspects target_deg within orb."""
    if not (isfinite(orb_deg) and orb_deg >= 0.0):
        raise ValueError("orb_deg must be a finite non-negative degree value")
    return tuple(a for a, point in aspected_points(body, caster_deg)
                 if _arc(point, target_deg) <= orb_deg)


__all__ = ["aspected_points", "aspects", "contact_level", "drishti_angles"]
