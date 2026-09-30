"""Frame enum and inclusive house counting (GOCHARA_DESIGN_SPECS_v1_4 §0).

Frames are explicit everywhere: `moon | lagna | graha:<X> | dasha_lord |
bhavat_bhavam:<house>`. Counting is inclusive of the reference sign (1st =
the sign itself). sign_of = floor(λ/30) per the oracles' constants block.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

SIGNS: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# Whole-sign lordship (Parāśari bhāva doctrine, as P3 [D]).
SIGN_LORDS: dict[str, str] = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

FRAME_KINDS = frozenset({"moon", "lagna", "graha", "dasha_lord", "bhavat_bhavam"})


@dataclass(frozen=True)
class Frame:
    """§0 frame enum. `arg`: graha name for 'graha', house int for
    'bhavat_bhavam', period lord name for 'dasha_lord', None otherwise."""

    kind: str
    arg: str | int | None = None

    def __post_init__(self):
        if self.kind not in FRAME_KINDS:
            raise ValueError(f"unknown frame kind {self.kind!r}")
        if self.kind == "bhavat_bhavam" and not (1 <= int(self.arg) <= 12):
            raise ValueError("bhavat_bhavam arg must be a house 1..12")

    def render(self) -> str:
        if self.arg is None:
            return self.kind
        return f"{self.kind}:{self.arg}"


def sign_of(longitude: float) -> str:
    """sign_of = floor(λ/30): 0 Aries … 11 Pisces (oracles constants.sign_of)."""
    return SIGNS[int(math.floor((longitude % 360.0) / 30.0))]


def frame_sign(frame: Frame, chart: dict) -> str:
    """The reference sign of a frame on a chart.

    chart = {"lagna_deg": float, "natal": {body: longitude}}.
    `dasha_lord` resolves through the natal sign of the period lord named in
    `frame.arg` (spec §2.2 P1: natal sign positions).
    """
    natal = chart["natal"]
    if frame.kind == "moon":
        return sign_of(natal["Moon"])
    if frame.kind == "lagna":
        return sign_of(chart["lagna_deg"])
    if frame.kind == "graha":
        return sign_of(natal[str(frame.arg)])
    if frame.kind == "dasha_lord":
        return sign_of(natal[str(frame.arg)])
    # bhavat_bhavam:<house>: the <house>-th sign from the lagna, inclusive.
    lagna_idx = SIGNS.index(sign_of(chart["lagna_deg"]))
    return SIGNS[(lagna_idx + int(frame.arg) - 1) % 12]


def house_of(longitude: float, frame: Frame, chart: dict) -> int:
    """Inclusive house of a longitude from the frame's sign (1st = the frame
    sign itself). Every count in an oracle shows it (§0)."""
    ref = SIGNS.index(frame_sign(frame, chart))
    tgt = SIGNS.index(sign_of(longitude))
    return (tgt - ref) % 12 + 1


def nth_sign_from(frame: Frame, n: int, chart: dict) -> str:
    """The n-th sign from the frame sign, inclusive count."""
    ref = SIGNS.index(frame_sign(frame, chart))
    return SIGNS[(ref + n - 1) % 12]


def house_span_sign(house: int, frame: Frame, chart: dict) -> str:
    """Sign of a house counted from the frame (whole-sign houses)."""
    return nth_sign_from(frame, house, chart)
