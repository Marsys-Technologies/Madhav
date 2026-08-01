"""
w2g_validations.types — shared result vocabulary for the W2G (GOCHARA-2.0)
bind-time validations V1–V6.

WAVE ID: W2G (ADJUDICATION-3 — `D-6` is RETIRED as a wave label and appears
nowhere in this package).

DATA-HONESTY RAIL (brief §7 / CLAUDE.md §N.8 Earned-Signal Principle): a
validation's status is computed by a detector that measures the specific
claim the status asserts. Three statuses, and only three:

  PASS           — the detector ran against real data and the claim holds.
  FAIL           — the detector ran against real data and the claim does NOT
                   hold. A FAIL is a FINDING (design §5: drift is a finding,
                   never a tuning opportunity), not a defect in the harness.
  INDETERMINATE  — the detector could not run (input substrate absent,
                   optional dependency missing, or the claim is not yet
                   measurable because the thing it measures does not exist
                   yet). `reason` is MANDATORY and `status` is NEVER
                   silently upgraded to PASS.

There is deliberately no "PASS with caveats". A validation that cannot
measure its claim reports INDETERMINATE and says why.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

WAVE_ID = "W2G"

PASS = "PASS"
FAIL = "FAIL"
INDETERMINATE = "INDETERMINATE"

VALID_STATUSES = (PASS, FAIL, INDETERMINATE)


@dataclass(frozen=True)
class ValidationResult:
    """One bind-time validation's outcome.

    Attributes
    ----------
    validation_id : "V1".."V6"
    title         : human-readable one-liner naming the claim under test.
    status        : PASS | FAIL | INDETERMINATE (see module docstring).
    summary       : one sentence stating the measured outcome.
    data          : machine-readable evidence. Everything a downstream lane
                    (or the ledger) needs, as data — never as prose only.
                    Per ADJUDICATION-5, values like `calendar_epoch_start`
                    are SURFACED HERE AS DATA, not assumed by a consumer.
    findings      : honest findings. MAY be non-empty on a PASS (a claim can
                    hold while the measurement surfaces something the next
                    lane must know).
    reason        : mandatory iff status == INDETERMINATE — what specifically
                    could not be measured, and why.
    """

    validation_id: str
    title: str
    status: str
    summary: str
    data: dict[str, Any] = field(default_factory=dict)
    findings: list[str] = field(default_factory=list)
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(
                f"{self.validation_id}: status {self.status!r} not one of {VALID_STATUSES}"
            )
        if self.status == INDETERMINATE and not self.reason:
            raise ValueError(
                f"{self.validation_id}: INDETERMINATE requires a non-empty `reason` "
                "(DATA-HONESTY RAIL — an unmeasurable claim must say what it could not measure)"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "wave": WAVE_ID,
            "validation_id": self.validation_id,
            "title": self.title,
            "status": self.status,
            "summary": self.summary,
            "data": self.data,
            "findings": list(self.findings),
            "reason": self.reason,
        }


__all__ = [
    "WAVE_ID",
    "PASS",
    "FAIL",
    "INDETERMINATE",
    "VALID_STATUSES",
    "ValidationResult",
]
