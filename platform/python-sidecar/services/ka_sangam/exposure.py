"""E6 exposure manifest, outcome record, and binomial gate evaluator.

Implements the D-1/D-2/D-3 evaluation-boundary discipline for ka_sangam:
  - exposure manifest publishes measured window-issuance rates by stratum
  - outcome record carries observation × derivation axes
  - per-stratum and instrument-level binomial gates with honest
    PROVISIONAL_INSUFFICIENT_N / CENSORING_BLOCKED / EMPIRICALLY_EVALUATED states

All functions are pure (no DB/I/O).  The writer attaches the exposure manifest
 to WriterResult.notes as JSON; outcomes are evaluated later from real outcome
 data, not invented by the writer.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from typing import Optional

# ── D-1 gate design constants (exact binomial, first-order approximation) ─────
# Re-set 2026-09-24 on the native's written instruction ("bring it down considerably and
# reasonably"): 35/100 -> 20/50.  The false-pass rate is unchanged (alpha <= 0.05);
# what moved is the smallest lift the gate can see at ~80% power: per-stratum from
# a doubling (0.20->0.40) to 2.5x (0.20->0.50); instrument-level from 1.6x to 2x.
# Power at the OLD alternatives is published beside the design so "no signal" can
# be read honestly: per-stratum 0.584 at 0.40; instrument 0.553 at 0.32.
PER_STRATUM_N = 20
PER_STRATUM_CRITICAL = 8
PER_STRATUM_ALPHA = 0.0321426631   # exact P(X>=8 | Bin(20, 0.20)) to 10 dp; presented as 0.0321
PER_STRATUM_POWER = 0.868
PER_STRATUM_ALTERNATIVE = 0.50
PER_STRATUM_POWER_AT_2X = 0.584

INSTRUMENT_N = 50
INSTRUMENT_CRITICAL = 16
INSTRUMENT_ALPHA = 0.0308034228    # exact P(X>=16 | Bin(50, 0.20)) to 10 dp; presented as 0.0308
INSTRUMENT_POWER = 0.904
INSTRUMENT_ALTERNATIVE = 0.40
INSTRUMENT_POWER_AT_1P6X = 0.553

NULL_RATE = 0.20

# ── D-2 censoring gradient ───────────────────────────────────────────────────
CENSORING_ELEVATED_PCT = 10.0
CENSORING_BLOCK_PCT = 20.0

# ── D-3 evaluation population ────────────────────────────────────────────────
# Evaluation is only valid for consenting charts with real outcomes.
# Synthetic/test charts must carry evaluation_eligible=False.

# Same prefix→domain map used by engine._school_consensus_score.
# Signature classes that do not match any prefix fall to 'OTHER' rather than
# being silently dropped; this keeps every window in the denominator.
SIGNATURE_CLASS_DOMAIN_PREFIXES = (
    ('CAREER', 'CAREER'),
    ('HEALTH', 'HEALTH'),
    ('RELATIONSHIP', 'RELATIONSHIP'),
    ('SPIRITUAL', 'SPIRITUAL'),
    ('PSYCHOLOGICAL', 'PSYCHOLOGICAL'),
)


def _extract_signature_class(comparability_class: Optional[str]) -> str:
    """comparability_class is 'ka_sangam/{signature_class}'."""
    s = (comparability_class or '').split('/')
    return s[-1].strip() if s and s[-1].strip() else 'UNKNOWN'


def infer_domain(signature_class: Optional[str]) -> str:
    """Map a signature-class name to its life-domain bucket."""
    sc = (signature_class or '').upper()
    for prefix, domain in SIGNATURE_CLASS_DOMAIN_PREFIXES:
        if sc.startswith(prefix):
            return domain
    return 'OTHER'


def stratum_key(window: dict) -> tuple[str, str, str]:
    """Stratum = (domain × route × method_version), D-1."""
    sig_class = _extract_signature_class(window.get('comparability_class'))
    domain = infer_domain(sig_class)
    # Mirrors the writer insert path, which stores a missing mode as 'A'
    # (writers/ka_sangam.py _insert_windows: mode = w.get('mode', 'A')).
    route = window.get('mode') or 'A'
    method_version = window.get('kernel_version') or 'UNKNOWN'
    return (domain, str(route), str(method_version))


def _window_span_years(window: dict) -> float:
    """Return the length of a [window_start, window_end) range in years."""
    ws = window.get('window_start')
    we = window.get('window_end')
    if ws is None or we is None:
        return 0.0
    try:
        if isinstance(ws, str):
            ws = date.fromisoformat(ws)
        if isinstance(we, str):
            we = date.fromisoformat(we)
        delta = we - ws
        days = delta.days
        if days < 0:
            return 0.0
        return days / 365.25
    except Exception:
        return 0.0


# ── Exposure manifest ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class StratumExposure:
    domain: str
    route: str
    method_version: str
    window_count: int
    window_years: float
    issuance_rate: float  # windows per chart-year


@dataclass(frozen=True)
class ExposureManifest:
    strata: dict[tuple[str, str, str], StratumExposure]
    total_windows: int
    total_window_years: float
    horizon_start: Optional[date]
    horizon_end: Optional[date]
    evaluation_eligible: bool
    is_synthetic: bool
    completeness: str  # 'complete' | 'incomplete' | 'unavailable'

    def to_json(self) -> str:
        """Serialise to JSON; dict keys are rendered as 'domain|route|version'."""
        payload = {
            'strata': {
                f"{s.domain}|{s.route}|{s.method_version}": {
                    'domain': s.domain,
                    'route': s.route,
                    'method_version': s.method_version,
                    'window_count': s.window_count,
                    'window_years': round(s.window_years, 6),
                    'issuance_rate': round(s.issuance_rate, 6),
                }
                for s in self.strata.values()
            },
            'total_windows': self.total_windows,
            'total_window_years': round(self.total_window_years, 6),
            'horizon_start': self.horizon_start.isoformat() if self.horizon_start else None,
            'horizon_end': self.horizon_end.isoformat() if self.horizon_end else None,
            'evaluation_eligible': self.evaluation_eligible,
            'is_synthetic': self.is_synthetic,
            'completeness': self.completeness,
        }
        return json.dumps(payload, sort_keys=True)


def _completeness(total_window_years: float) -> str:
    if total_window_years <= 0.0:
        return 'unavailable'
    if total_window_years >= 30.0:
        return 'complete'
    return 'incomplete'


def compute_exposure_manifest(
    windows: list[dict],
    horizon_start: Optional[date] = None,
    horizon_end: Optional[date] = None,
    *,
    evaluation_eligible: bool = True,
    is_synthetic: bool = False,
) -> ExposureManifest:
    """Build an exposure manifest from a list of ka_sangam window dicts."""
    buckets: dict[tuple[str, str, str], dict[str, int | float]] = defaultdict(
        lambda: {'count': 0, 'years': 0.0}
    )
    for w in windows:
        key = stratum_key(w)
        buckets[key]['count'] = int(buckets[key]['count']) + 1  # type: ignore[assignment]
        buckets[key]['years'] = float(buckets[key]['years']) + _window_span_years(w)  # type: ignore[assignment]

    strata: dict[tuple[str, str, str], StratumExposure] = {}
    for (domain, route, method_version), vals in buckets.items():
        count = int(vals['count'])
        years = float(vals['years'])
        rate = count / years if years > 0.0 else 0.0
        strata[(domain, route, method_version)] = StratumExposure(
            domain=domain,
            route=route,
            method_version=method_version,
            window_count=count,
            window_years=years,
            issuance_rate=rate,
        )

    total_windows = len(windows)
    total_years = sum(float(v['years']) for v in buckets.values())
    completeness = _completeness(total_years)

    return ExposureManifest(
        strata=strata,
        total_windows=total_windows,
        total_window_years=total_years,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        evaluation_eligible=evaluation_eligible,
        is_synthetic=is_synthetic,
        completeness=completeness,
    )


# ── Binomial helpers ─────────────────────────────────────────────────────────

def _binomial_sf(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p).  Exact, small-n safe."""
    if k > n or n < 0:
        return 0.0
    if k <= 0:
        return 1.0
    return sum(
        math.comb(n, i) * (p ** i) * ((1.0 - p) ** (n - i))
        for i in range(k, n + 1)
    )


def find_critical_value(n: int, alpha: float, null_rate: float = NULL_RATE) -> int:
    """Smallest c such that P(X >= c | Bin(n, null_rate)) <= alpha + 1e-9."""
    for c in range(0, n + 1):
        if _binomial_sf(c, n, null_rate) <= alpha + 1e-9:
            return c
    return n + 1


def compute_power(n: int, critical: int, alternative_rate: float) -> float:
    """Power = P(X >= critical | Bin(n, alternative_rate))."""
    return _binomial_sf(critical, n, alternative_rate)


# ── Outcome record ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class StratumOutcome:
    domain: str
    route: str
    method_version: str

    # Observation axis
    hits: int
    misses: int
    ambiguous: int
    censored: int
    unobserved: int

    # Derivation axis
    valid: int
    invalidated: int
    superseded: int

    n_evaluated: int            # hits + misses (fully observed, non-censored)
    total: int                  # all five observation states
    hit_rate_interval: tuple[float, float]
    claim_rate: float           # adverse-end lower bound = hits / total
    censoring_rate: float       # (ambiguous + censored) / total
    gate_status: str
    actual_n: int               # n_evaluated, carried even when insufficient

    def to_dict(self) -> dict:
        d = asdict(self)
        d['hit_rate_interval'] = list(self.hit_rate_interval)
        return d


@dataclass(frozen=True)
class InstrumentOutcome:
    method_version: str
    hits: int
    misses: int
    ambiguous: int
    censored: int
    unobserved: int
    valid: int
    invalidated: int
    superseded: int
    n_evaluated: int
    total: int
    hit_rate_interval: tuple[float, float]
    claim_rate: float
    censoring_rate: float
    gate_status: str
    actual_n: int
    strata: list[StratumOutcome]

    def to_dict(self) -> dict:
        d = asdict(self)
        d['hit_rate_interval'] = list(self.hit_rate_interval)
        d['strata'] = [s.to_dict() for s in self.strata]
        return d


def _evaluate_gate(
    n_evaluated: int,
    hits: int,
    total: int,
    ambiguous: int,
    censored: int,
    threshold_n: int,
    critical: int,
    alpha: float,
    evaluation_eligible: bool,
    is_synthetic: bool,
) -> str:
    """Return the gate status string for a single binomial gate."""
    if not evaluation_eligible or is_synthetic:
        return 'NOT_ELIGIBLE'
    if total == 0:
        return 'UNAVAILABLE'
    censoring_rate = (ambiguous + censored) / total if total else 0.0
    if censoring_rate > (CENSORING_BLOCK_PCT / 100.0):
        return 'CENSORING_BLOCKED'
    if n_evaluated < threshold_n:
        return 'PROVISIONAL_INSUFFICIENT_N'
    p_value = _binomial_sf(hits, n_evaluated, NULL_RATE)
    if hits >= critical and p_value <= alpha + 1e-9:   # +eps: the design point's p-value equals alpha exactly
        # Binomial gate is passed, but EMPIRICALLY_EVALUATED stays closed until
        # the M-6 five conditions (predeclared protocol, held-out chronology,
        # frozen version, native-ratified n, censoring rules) are satisfied.
        return 'BINOMIAL_GATE_PASSED'
    return 'BELOW_CRITICAL'


def build_stratum_outcome(
    *,
    domain: str,
    route: str,
    method_version: str,
    hits: int = 0,
    misses: int = 0,
    ambiguous: int = 0,
    censored: int = 0,
    unobserved: int = 0,
    valid: int = 0,
    invalidated: int = 0,
    superseded: int = 0,
    evaluation_eligible: bool = True,
    is_synthetic: bool = False,
    threshold_n: int = PER_STRATUM_N,
    critical: int = PER_STRATUM_CRITICAL,
    alpha: float = PER_STRATUM_ALPHA,
) -> StratumOutcome:
    """Build a per-stratum outcome record and evaluate its binomial gate."""
    n_evaluated = hits + misses
    total = hits + misses + ambiguous + censored + unobserved

    if total == 0:
        hit_rate_interval = (0.0, 0.0)
        claim_rate = 0.0
        censoring_rate = 0.0
    else:
        lower = hits / total
        upper = (hits + ambiguous) / total
        hit_rate_interval = (lower, upper)
        claim_rate = lower
        censoring_rate = (ambiguous + censored) / total

    gate_status = _evaluate_gate(
        n_evaluated=n_evaluated,
        hits=hits,
        total=total,
        ambiguous=ambiguous,
        censored=censored,
        threshold_n=threshold_n,
        critical=critical,
        alpha=alpha,
        evaluation_eligible=evaluation_eligible,
        is_synthetic=is_synthetic,
    )

    return StratumOutcome(
        domain=domain,
        route=route,
        method_version=method_version,
        hits=hits,
        misses=misses,
        ambiguous=ambiguous,
        censored=censored,
        unobserved=unobserved,
        valid=valid,
        invalidated=invalidated,
        superseded=superseded,
        n_evaluated=n_evaluated,
        total=total,
        hit_rate_interval=hit_rate_interval,
        claim_rate=claim_rate,
        censoring_rate=censoring_rate,
        gate_status=gate_status,
        actual_n=n_evaluated,
    )


def evaluate_instrument_outcome(
    strata_outcomes: list[StratumOutcome],
    *,
    method_version: Optional[str] = None,
    evaluation_eligible: bool = True,
    is_synthetic: bool = False,
    threshold_n: int = INSTRUMENT_N,
    critical: int = INSTRUMENT_CRITICAL,
    alpha: float = INSTRUMENT_ALPHA,
) -> InstrumentOutcome:
    """Pool strata within ONE method_version and evaluate the instrument gate."""
    if not strata_outcomes:
        mv = method_version or 'UNKNOWN'
        return InstrumentOutcome(
            method_version=mv,
            hits=0, misses=0, ambiguous=0, censored=0, unobserved=0,
            valid=0, invalidated=0, superseded=0,
            n_evaluated=0, total=0,
            hit_rate_interval=(0.0, 0.0),
            claim_rate=0.0,
            censoring_rate=0.0,
            gate_status='UNAVAILABLE',
            actual_n=0,
            strata=[],
        )

    mv = method_version or strata_outcomes[0].method_version
    hits = sum(s.hits for s in strata_outcomes)
    misses = sum(s.misses for s in strata_outcomes)
    ambiguous = sum(s.ambiguous for s in strata_outcomes)
    censored = sum(s.censored for s in strata_outcomes)
    unobserved = sum(s.unobserved for s in strata_outcomes)
    valid = sum(s.valid for s in strata_outcomes)
    invalidated = sum(s.invalidated for s in strata_outcomes)
    superseded = sum(s.superseded for s in strata_outcomes)

    n_evaluated = hits + misses
    total = hits + misses + ambiguous + censored + unobserved

    if total == 0:
        hit_rate_interval = (0.0, 0.0)
        claim_rate = 0.0
        censoring_rate = 0.0
    else:
        lower = hits / total
        upper = (hits + ambiguous) / total
        hit_rate_interval = (lower, upper)
        claim_rate = lower
        censoring_rate = (ambiguous + censored) / total

    gate_status = _evaluate_gate(
        n_evaluated=n_evaluated,
        hits=hits,
        total=total,
        ambiguous=ambiguous,
        censored=censored,
        threshold_n=threshold_n,
        critical=critical,
        alpha=alpha,
        evaluation_eligible=evaluation_eligible,
        is_synthetic=is_synthetic,
    )

    return InstrumentOutcome(
        method_version=mv,
        hits=hits,
        misses=misses,
        ambiguous=ambiguous,
        censored=censored,
        unobserved=unobserved,
        valid=valid,
        invalidated=invalidated,
        superseded=superseded,
        n_evaluated=n_evaluated,
        total=total,
        hit_rate_interval=hit_rate_interval,
        claim_rate=claim_rate,
        censoring_rate=censoring_rate,
        gate_status=gate_status,
        actual_n=n_evaluated,
        strata=list(strata_outcomes),
    )
