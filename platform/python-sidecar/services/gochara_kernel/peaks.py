"""Plateau-aware peak admission (WP2 case 12; H-5 context).

WP2 pin: ALL tied maxima are admitted with the SAME rank — no first-day-wins,
no arbitrary single pick, no "duplicate" drops. With H-5 (the fixed cap on
stored peaks per era per decade removed), every admitted peak persists;
trimming happens only at serve time (a serve-time `max_rows` may be passed,
applied after admission, never changing ranks).

This is a projection helper, not contact geometry — it lives in the kernel
package because WP2's acceptance fixtures (case 12) must pass against the
kernel's own test suite; WP3b/WP4 consume it over ledger episodes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class AdmittedPeak:
    index: int
    value: float
    rank: int


def admit_peaks(
    values: Sequence[float],
    max_rows: int | None = None,
) -> list[AdmittedPeak]:
    """Admit every index attaining the global maximum, each with rank 1
    (the plateau-tie rule, WP2 case 12). `max_rows` models serve-time
    trimming only: admission is cap-free (H-5); a trim is stable (lowest
    indices first) and never re-ranks."""
    if not values:
        return []
    peak_value = max(values)
    admitted = [
        AdmittedPeak(index=i, value=float(v), rank=1)
        for i, v in enumerate(values)
        if v == peak_value
    ]
    if max_rows is not None and len(admitted) > max_rows:
        admitted = admitted[:max_rows]
    return admitted


__all__ = ["AdmittedPeak", "admit_peaks"]
