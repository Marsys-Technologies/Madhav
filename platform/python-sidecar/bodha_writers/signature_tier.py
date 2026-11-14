"""Absolute salience tiers for the Bodha signature writers."""

_TIER_CHART_DEFINING = 2.0
_TIER_MAJOR = 0.8
_TIER_SUPPORTING = 0.3


def _signature_tier(computed_salience: float) -> str:
    if computed_salience >= _TIER_CHART_DEFINING:
        return "chart_defining"
    if computed_salience >= _TIER_MAJOR:
        return "major"
    if computed_salience >= _TIER_SUPPORTING:
        return "supporting"
    return "background"
