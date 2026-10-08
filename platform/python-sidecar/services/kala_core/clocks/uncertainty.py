"""Shared F2 boundary linearisation; consumes an admitted L1 uncertainty artifact.

No L4 read, ephemeris query, default birth sigma, or daśā period construction.
Units: days for time, degrees for angle; covariance has units day × degree.
"""
from dataclasses import dataclass
from datetime import timedelta
from math import isfinite, sqrt


@dataclass(frozen=True)
class BoundaryUncertainty:
    sigma_birth_days: float
    sigma_ayanamsha_deg: float
    velocity_deg_per_day: float
    days_per_degree: float
    birth_ayanamsha_covariance: float
    artifact_id: str
    fact_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        values = (self.sigma_birth_days, self.sigma_ayanamsha_deg, self.velocity_deg_per_day,
                  self.days_per_degree, self.birth_ayanamsha_covariance)
        if not all(isfinite(v) for v in values) or min(self.sigma_birth_days, self.sigma_ayanamsha_deg, self.days_per_degree) < 0:
            raise ValueError("uncertainty inputs must be finite; sigmas and k nonnegative")
        if abs(self.birth_ayanamsha_covariance) > self.sigma_birth_days * self.sigma_ayanamsha_deg:
            raise ValueError("birth/ayanāṃśa covariance is not positive semidefinite")
        if not self.artifact_id or not self.fact_ids or not all(self.fact_ids):
            raise ValueError("uncertainty requires an admitted L1 artifact and fact ids")


def boundary_sigma(inputs: BoundaryUncertainty) -> timedelta:
    """dB=(1−kv)dT+k·dA; adjacent boundaries use this same random shift.

    The old uncertainty.py:268-276 double-counted the correlated birth term as
    two independent squares. This computes their signed sum before squaring.
    k=0 explicitly represents a method without a fractional-arc balance.
    """
    k = inputs.days_per_degree
    a = 1 - k * inputs.velocity_deg_per_day
    variance = (a * inputs.sigma_birth_days) ** 2 + (k * inputs.sigma_ayanamsha_deg) ** 2
    variance += 2 * a * k * inputs.birth_ayanamsha_covariance
    return timedelta(days=sqrt(max(0., variance)))


def boundary_shift(inputs: BoundaryUncertainty, *, birth_shift_days: float, ayanamsha_shift_deg: float) -> timedelta:
    """Sensitivity only: F2 never uses this delta to invent an L1 period row."""
    if not isfinite(birth_shift_days) or not isfinite(ayanamsha_shift_deg):
        raise ValueError("scenario perturbations must be finite")
    k = inputs.days_per_degree
    return timedelta(days=(1 - k * inputs.velocity_deg_per_day) * birth_shift_days + k * ayanamsha_shift_deg)
