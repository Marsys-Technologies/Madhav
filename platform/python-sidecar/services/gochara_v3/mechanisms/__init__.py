"""gochara_v3 mechanisms package.

Dormant mechanism modules for Wave 2 of the GOCHARA-UTKARSHA campaign.
These modules are NOT wired into engine.py yet — they are candidate mechanisms
that exist as standalone compute units and register themselves via a YAML
registry entry. Admission into the live scoring path requires ablation evidence
and a formal admission ruling.

MechanismResult
---------------
The return type every mechanism's compute() must produce.

Fields
------
mechanism_id    : str  — matches the YAML registry's mechanism_id.
modifier        : float — the multiplicative modifier in [0, ∞).
                  Most mechanisms target a bounded range (e.g. [1.0, 1.30]).
                  1.0 == no effect. >1.0 amplifies. <1.0 suppresses.
enabled         : bool  — True when the mechanism actually ran and produced a
                  non-unit modifier. False when skipped (disabled, wrong class,
                  data unavailable).
detail          : str   — human-readable explanation of why this modifier was
                  chosen. Always non-empty; used for audit/logging.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MechanismResult:
    """Return type for every gochara_v3 mechanism compute() call."""

    mechanism_id: str
    modifier: float
    enabled: bool
    detail: str

    def __post_init__(self) -> None:
        if self.modifier < 0.0:
            raise ValueError(
                f"MechanismResult.modifier must be >= 0.0, got {self.modifier!r} "
                f"for mechanism_id={self.mechanism_id!r}"
            )


__all__ = ["MechanismResult"]
