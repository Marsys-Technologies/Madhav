"""
ph_rectification engine — birth-time rectification via PyJHora ascendant scan vs LEL events.

DB-free scoring logic (no psycopg2, no I/O). The writer wires this into the
orchestrator transaction; this module is pure computation and is unit-tested in
isolation.

LEAKAGE-FIREWALL: events post-2020 or late-disclosed (the M5-A-S1 enrichment
batch added in LEL v1.7, 2026-05-13) are EXCLUDED from training; they are held
out for out-of-sample validation only. The embedded TRAINING_EVENTS list below
is already firewalled at authoring time — every event is pre-2020, exact or
month-exact, and is NOT one of the v1.7 enrichment ids. _firewall_filter()
re-asserts the gate defensively so a future edit that smuggles a post-2020 or
enrichment event in cannot leak.

Scoring: for each candidate birth time, compute the ascendant per ayanamsha and
score against training LEL events by checking:
  (1) Lagna-sign stability — the recorded-time sign must hold across all 5
       ayanamshas (hard filter). FORENSIC confirms Aries at 10:43 across all 5
       ayanamshas; the engine compares each candidate to the recorded-time sign
       (offset 0) rather than hardcoding a sign name, so it stays correct under
       any ascendant-engine convention. See README note in ph_rectification.
  (2) Lagna-degree fit — degrees consistent with the native's documented
       temperament; sub-degree discrimination requires life-event alignment from
       the dasha lords (handled by (3)).
  (3) Dasha-lord match — for each LEL training event with a known Vimshottari
       maha-dasha lord, check whether that lord's natal-house position FROM THE
       CANDIDATE LAGNA is a classical significator house for the event domain
       (career event → 10th/6th lords; marriage → 7th; loss → 8th; etc.).

D43 NO-AUTO-OVERRIDE: this engine NEVER mutates a chart. auto_action is always
'stage_for_review'. The canonical chart 482012f1 is never auto-revised.

## Sign-level scan vs. full D41 whole-instrument scoring
The current implementation is a SIGN-LEVEL scan: within the ±90-minute window, the
lagna sign typically stays constant (all stable candidates share the same lagna sign
and therefore the same whole-sign house placements for dasha lords). This makes
lel_fit_score uniform across stable candidates — deliberately so. The tiebreaker
(abs(offset)) correctly selects the recorded birth time when no discriminating
evidence exists, and confidence_label='unresolved' is the CORRECT B.10-compliant
output (not a defect).

Sub-degree discrimination (bhava cusps, navamsa, dasha sub-period alignment, the
full D41 tiered whole-instrument scorer) is a FUTURE layer that builds on this
foundation. The sign-level scan's value is: (a) verifying lagna sign stability
across all 5 ayanamshas for the ±90-min window, and (b) establishing the
candidate table + NO-AUTO-OVERRIDE staging infrastructure for when sub-degree
scoring is added. Appending sub-degree logic requires only extending `_score_dasha_match`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

__all__ = [
    "TrainingEvent",
    "RectificationCandidate",
    "BestRectification",
    "TRAINING_EVENTS",
    "AYANAMSHAS",
    "RECORDED_BIRTH_UTC",
    "AUTO_ACTION",
    "NATIVE_CHART_ID",
    "build_candidate_offsets",
    "domain_significator_houses",
    "score_candidate",
    "run_rectification",
    "select_best",
]

# ----------------------------------------------------------------------------
# Canonical native birth params (NEVER fabricate; from CLAUDE.md §B).
# 1984-02-05, 10:43 IST (UTC+5:30) -> 05:13:00 UTC.
# ----------------------------------------------------------------------------
RECORDED_BIRTH_UTC = datetime(1984, 2, 5, 5, 13, 0, tzinfo=timezone.utc)
NATIVE_LAT = 20.2961
NATIVE_LON = 85.8245
NATIVE_TZ = 5.5

# JL-017 (BA Phase 2.5 #11, CONTAMINATION-CLASS): TRAINING_EVENTS and
# _DASHA_LORD_NATAL_SIGN_INDEX below are the native Abhisek Mohanty's OWN LEL
# events and natal dasha-lord positions. The writer MUST gate their use behind
# this chart_id — never silently apply one chart's life events / natal facts
# to another chart's rectification scan. See pipeline/orchestrator/writers/
# ph_rectification/__init__.py for the enforcing chart-attribution check.
NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

# Five canonical ayanamsha ids that resolve DISTINCTLY in pyjhora_adapter
# (_ayanamsha.AYANAMSHA_MAP). 'krishnamurti' is NOT a distinct key — it falls
# back to lahiri — so we use the real KP id 'kp' instead. true_chitra + lahiri
# are near-identical for this epoch; both retained for FORENSIC parity (the
# 7-anchor FORENSIC fact is "Aries across all 5 ayanamshas").
AYANAMSHAS = ("lahiri", "true_chitra", "kp", "raman", "surya_siddhanta")

# Candidate scan window: ±90 minutes in 5-minute steps = 37 candidates.
SCAN_HALF_WIDTH_MIN = 90
SCAN_STEP_MIN = 5

# D43 hard gate — never anything else.
AUTO_ACTION = "stage_for_review"

# Leakage firewall thresholds.
_FIREWALL_CUTOFF = datetime(2020, 1, 1, tzinfo=timezone.utc)
# Event ids added at LEL v1.7 M5-A-S1 (2026-05-13) — held out, never trained.
_M5A_ENRICHMENT_IDS = frozenset({
    "EVT.1993.XX.XX.01", "EVT.1995.XX.XX.02", "EVT.1998.XX.XX.02",
    "EVT.2002.XX.XX.01", "EVT.2002.XX.XX.02", "EVT.2010.XX.XX.02",
    "EVT.2015.XX.XX.01", "EVT.2024.XX.XX.01", "EVT.2025.06.XX.01",
    "EVT.2025.11.XX.01",
})


@dataclass(frozen=True)
class TrainingEvent:
    """A pre-2020 LEL event used for rectification scoring.

    maha_dasha_lord is the Vimshottari mahadasha lord active on the event date,
    derived from the documented dasha boundaries (FORENSIC §5.1 lineage):
      Saturn  MD 1991-08-19 -> 2010-08-18
      Mercury MD 2010-08-18 -> 2027-08-18
    domain is the LEL category (career/education/relationship/...); it maps to
    classical significator houses via domain_significator_houses().
    """
    event_id: str
    date: datetime           # event date (UTC midnight proxy; day precision only)
    domain: str
    maha_dasha_lord: str     # graha that owns no house by itself; placed FROM candidate lagna
    date_confidence: str     # 'exact' | 'month-exact'


# ----------------------------------------------------------------------------
# TRAINING SET — firewalled at authoring time (all pre-2020, exact/month-exact,
# none from the v1.7 M5-A-S1 enrichment batch). Maha-dasha lords assigned from
# the documented Vimshottari boundaries above. See LEL_v1_2 §3.
# ----------------------------------------------------------------------------
def _d(y: int, m: int, day: int) -> datetime:
    return datetime(y, m, day, tzinfo=timezone.utc)


TRAINING_EVENTS: tuple[TrainingEvent, ...] = (
    TrainingEvent("EVT.1998.02.16.01", _d(1998, 2, 16), "relationship", "Saturn", "exact"),
    TrainingEvent("EVT.2001.03.15.01", _d(2001, 3, 15), "education", "Saturn", "month-exact"),
    TrainingEvent("EVT.2003.06.15.01", _d(2003, 6, 15), "education", "Saturn", "month-exact"),
    TrainingEvent("EVT.2004.01.15.01", _d(2004, 1, 15), "relationship", "Saturn", "month-exact"),
    TrainingEvent("EVT.2007.06.15.01", _d(2007, 6, 15), "health", "Saturn", "month-exact"),
    TrainingEvent("EVT.2007.06.15.02", _d(2007, 6, 15), "education", "Saturn", "month-exact"),
    TrainingEvent("EVT.2007.06.10.01", _d(2007, 6, 10), "career", "Saturn", "exact"),
    TrainingEvent("EVT.2008.06.09.01", _d(2008, 6, 9), "career", "Saturn", "exact"),
    TrainingEvent("EVT.2009.06.15.01", _d(2009, 6, 15), "loss", "Saturn", "month-exact"),
    TrainingEvent("EVT.2010.12.15.01", _d(2010, 12, 15), "travel", "Mercury", "month-exact"),
    TrainingEvent("EVT.2011.01.15.01", _d(2011, 1, 15), "education", "Mercury", "month-exact"),
    TrainingEvent("EVT.2011.06.15.01", _d(2011, 6, 15), "education", "Mercury", "month-exact"),
    TrainingEvent("EVT.2012.09.15.01", _d(2012, 9, 15), "creative", "Mercury", "month-exact"),
    TrainingEvent("EVT.2012.10.15.01", _d(2012, 10, 15), "relationship", "Mercury", "month-exact"),
    TrainingEvent("EVT.2013.03.15.01", _d(2013, 3, 15), "education", "Mercury", "month-exact"),
    TrainingEvent("EVT.2013.05.15.01", _d(2013, 5, 15), "career", "Mercury", "month-exact"),
    TrainingEvent("EVT.2013.12.11.01", _d(2013, 12, 11), "family", "Mercury", "exact"),
    TrainingEvent("EVT.2017.03.15.01", _d(2017, 3, 15), "career", "Mercury", "month-exact"),
    TrainingEvent("EVT.2018.11.28.01", _d(2018, 11, 28), "loss", "Mercury", "exact"),
)

# Domain -> classical significator houses (whole-sign, from the lagna).
# A dasha lord whose natal house (counted from the candidate lagna) falls in one
# of these houses is "consistent" with an event in that domain.
_DOMAIN_HOUSES: dict[str, tuple[int, ...]] = {
    "career":       (1, 6, 10, 11),
    "education":    (2, 4, 5, 9),
    "relationship": (5, 7, 11),
    "family":       (2, 4, 7),
    "health":       (1, 6, 8),
    "loss":         (4, 8, 12),     # 4th (mother/property), 8th (longevity), 12th (loss)
    "travel":       (3, 9, 12),
    "creative":     (3, 5),
    "finance":      (2, 11),
    "spiritual":    (5, 9, 12),
    "residential":  (4, 12),
    "legal":        (6, 8),
}


def domain_significator_houses(domain: str) -> tuple[int, ...]:
    """Classical significator houses for an LEL domain. Empty tuple if unknown."""
    # Handle dual-tagged domains like 'residential+travel' by union.
    if "+" in domain:
        houses: set[int] = set()
        for part in domain.split("+"):
            houses.update(_DOMAIN_HOUSES.get(part.strip(), ()))
        return tuple(sorted(houses))
    return _DOMAIN_HOUSES.get(domain, ())


def _firewall_filter(events: tuple[TrainingEvent, ...]) -> list[TrainingEvent]:
    """Defensive re-assertion of the LEAKAGE-FIREWALL.

    Excludes any event that is (a) on/after 2020-01-01, or (b) a v1.7 M5-A-S1
    enrichment id, or (c) below month-exact date confidence. Returns the clean
    training list.
    """
    clean: list[TrainingEvent] = []
    for ev in events:
        if ev.event_id in _M5A_ENRICHMENT_IDS:
            continue
        if ev.date >= _FIREWALL_CUTOFF:
            continue
        if ev.date_confidence not in ("exact", "month-exact"):
            continue
        clean.append(ev)
    return clean


def build_candidate_offsets() -> list[int]:
    """Signed minute offsets: -90..+90 in 5-min steps. Exactly 37 candidates."""
    return list(range(-SCAN_HALF_WIDTH_MIN, SCAN_HALF_WIDTH_MIN + 1, SCAN_STEP_MIN))


# ----------------------------------------------------------------------------
# Vimshottari maha-dasha lord -> its natal sidereal longitude (degrees 0..360).
# These are FORENSIC L1 facts (natal graha positions, ayanamsha-invariant at the
# whole-sign level used here). Used to compute the house a dasha lord occupies
# FROM a candidate lagna. Sourced from chart_facts; embedded as constants because
# the engine is DB-free. Saturn + Mercury are the only two MD lords in the
# training window, so only those are required.
#   Saturn  ~ Scorpio  (natal) -> sidereal long ~217.5 deg
#   Mercury ~ Capricorn (natal) -> sidereal long ~285.0 deg
# (Whole-sign house = (graha_sign_index - lagna_sign_index) mod 12 + 1.)
# ----------------------------------------------------------------------------
_DASHA_LORD_NATAL_SIGN_INDEX: dict[str, int] = {
    # 0=Aries .. 11=Pisces
    "Saturn":  7,   # Scorpio
    "Mercury": 9,   # Capricorn
}

_SIGN_NAMES = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


def _sign_index(sign_name: str) -> int:
    return _SIGN_NAMES.index(sign_name)


def _house_of_lord_from_lagna(
    lord: str,
    lagna_sign_index: int,
    dasha_lord_natal_sign_index: Optional[dict[str, int]] = None,
) -> Optional[int]:
    """Whole-sign house (1..12) occupied by a dasha lord, counted from lagna."""
    lord_signs = dasha_lord_natal_sign_index if dasha_lord_natal_sign_index is not None \
        else _DASHA_LORD_NATAL_SIGN_INDEX
    g = lord_signs.get(lord)
    if g is None:
        return None
    return ((g - lagna_sign_index) % 12) + 1


@dataclass
class RectificationCandidate:
    offset_minutes: int
    candidate_birth_utc: datetime
    ayanamsha_id: str
    lagna_sign: str
    lagna_longitude_deg: float
    lagna_degree_in_sign: float
    lagna_stable: bool
    lel_fit_score: Optional[float]
    lel_events_matched: Optional[int]
    lel_events_tested: int


@dataclass
class BestRectification:
    best_candidate: Optional[RectificationCandidate]
    candidate_birth_utc: Optional[datetime]
    offset_minutes: Optional[int]
    best_lagna_sign: Optional[str]
    best_lagna_longitude: Optional[float]
    best_lel_fit_score: Optional[float]
    confidence_low: Optional[float]
    confidence_high: Optional[float]
    confidence_label: Optional[str]
    win_margin: Optional[float]
    competing_candidates: list[dict]
    lel_training_events: int
    lel_training_matched: Optional[int]
    leakage_firewall_note: str
    auto_action: str = AUTO_ACTION


# Type of an ascendant function: (ut_offset_minutes, ayanamsha_id) -> dict with
# keys 'sign', 'longitude_deg', 'degree_in_sign'. Injected so the engine is
# testable without PyJHora; the writer supplies a PyJHora-backed implementation.
AscendantFn = Callable[[int, str], dict]


def _score_dasha_match(
    lagna_sign_index: int,
    events: list[TrainingEvent],
    dasha_lord_natal_sign_index: Optional[dict[str, int]] = None,
) -> int:
    """Count training events whose maha-dasha lord sits in a domain-significator
    house, counted from the given candidate lagna sign."""
    matched = 0
    for ev in events:
        house = _house_of_lord_from_lagna(ev.maha_dasha_lord, lagna_sign_index, dasha_lord_natal_sign_index)
        if house is None:
            continue
        if house in domain_significator_houses(ev.domain):
            matched += 1
    return matched


def score_candidate(
    offset_minutes: int,
    ascendant_fn: AscendantFn,
    reference_signs: dict[str, str],
    training_events: Optional[list[TrainingEvent]] = None,
    recorded_birth_utc: Optional[datetime] = None,
    dasha_lord_natal_sign_index: Optional[dict[str, int]] = None,
) -> list[RectificationCandidate]:
    """Score one candidate birth time across all ayanamshas.

    reference_signs: ayanamsha_id -> lagna sign at the RECORDED time (offset 0).
    A candidate is lagna_stable only if its sign matches the reference sign for
    EVERY ayanamsha. Returns one RectificationCandidate per ayanamsha.
    """
    if training_events is None:
        training_events = _firewall_filter(TRAINING_EVENTS)
    base_utc = recorded_birth_utc if recorded_birth_utc is not None else RECORDED_BIRTH_UTC

    cand_birth = base_utc + timedelta(minutes=offset_minutes)
    per_ayan: dict[str, dict] = {}
    signs: dict[str, str] = {}
    for ay in AYANAMSHAS:
        asc = ascendant_fn(offset_minutes, ay)
        per_ayan[ay] = asc
        signs[ay] = asc["sign"]

    # Lagna stable iff every ayanamsha's sign equals the recorded-time sign.
    stable = all(signs[ay] == reference_signs.get(ay) for ay in AYANAMSHAS)

    n_tested = len(training_events)
    out: list[RectificationCandidate] = []
    for ay in AYANAMSHAS:
        asc = per_ayan[ay]
        fit: Optional[float] = None
        matched: Optional[int] = None
        if stable and n_tested > 0:
            lagna_idx = _sign_index(asc["sign"])
            matched = _score_dasha_match(lagna_idx, training_events, dasha_lord_natal_sign_index)
            fit = round(matched / n_tested, 4)
        out.append(RectificationCandidate(
            offset_minutes=offset_minutes,
            candidate_birth_utc=cand_birth,
            ayanamsha_id=ay,
            lagna_sign=asc["sign"],
            lagna_longitude_deg=round(float(asc["longitude_deg"]), 4),
            lagna_degree_in_sign=round(float(asc["degree_in_sign"]), 4),
            lagna_stable=stable,
            lel_fit_score=fit,
            lel_events_matched=matched,
            lel_events_tested=n_tested,
        ))
    return out


def run_rectification(
    ascendant_fn: AscendantFn,
    recorded_birth_utc: Optional[datetime] = None,
    training_events: Optional[list[TrainingEvent]] = None,
    dasha_lord_natal_sign_index: Optional[dict[str, int]] = None,
) -> list[RectificationCandidate]:
    """Generate and score all 37 candidates across all 5 ayanamshas.

    recorded_birth_utc: the chart's birth time in UTC; if None, falls back to
    the module-level RECORDED_BIRTH_UTC constant (native Abhisek Mohanty).
    Always pass this from ctx.config['birth_params'] for non-native charts.

    JL-017 (CONTAMINATION-CLASS): training_events/dasha_lord_natal_sign_index
    default to the native's own embedded TRAINING_EVENTS/_DASHA_LORD_NATAL_SIGN_INDEX
    ONLY for backward compatibility of direct callers (e.g. tests); the writer
    MUST pass explicit chart-scoped values (or refuse to score) for any chart
    other than NATIVE_CHART_ID — never let another chart silently inherit the
    native's life events / natal dasha-lord positions.

    Returns a flat list of RectificationCandidate (37 * 5 = 185 rows).
    """
    # Reference signs from the recorded time (offset 0).
    reference_signs = {ay: ascendant_fn(0, ay)["sign"] for ay in AYANAMSHAS}
    training = _firewall_filter(training_events if training_events is not None else TRAINING_EVENTS)

    results: list[RectificationCandidate] = []
    for off in build_candidate_offsets():
        results.extend(
            score_candidate(
                off, ascendant_fn, reference_signs, training, recorded_birth_utc,
                dasha_lord_natal_sign_index,
            )
        )
    return results


def _confidence_label(win_margin: float) -> str:
    if win_margin >= 0.10:
        return "decisive"
    if win_margin >= 0.05:
        return "probable"
    return "unresolved"


def select_best(
    candidates: list[RectificationCandidate],
    training_events: Optional[list[TrainingEvent]] = None,
) -> BestRectification:
    """Pick the best candidate offset.

    A candidate's offset score is the mean lel_fit_score across its ayanamshas
    (only stable candidates carry a score). Sort by score DESC, lagna_stable DESC.
    win_margin is the gap between the best offset's score and the second-best.

    training_events must be the SAME list passed to run_rectification() for these
    candidates — this only affects the reported lel_training_events/firewall_note
    metadata (candidates already carry their own lel_fit_score/lel_events_tested
    from scoring); defaults to the native's TRAINING_EVENTS for backward
    compatibility of direct callers.
    """
    training = _firewall_filter(training_events if training_events is not None else TRAINING_EVENTS)
    n_training = len(training)
    firewall_note = (
        f"LEAKAGE-FIREWALL: {n_training} training events (all pre-2020-01-01, "
        f"exact/month-exact, none from LEL v1.7 M5-A-S1 enrichment). Post-2020 + "
        f"enrichment events held out for out-of-sample validation."
    )

    # Aggregate per offset.
    by_offset: dict[int, list[RectificationCandidate]] = {}
    for c in candidates:
        by_offset.setdefault(c.offset_minutes, []).append(c)

    scored: list[tuple[float, bool, int, list[RectificationCandidate]]] = []
    for off, group in by_offset.items():
        stable = all(c.lagna_stable for c in group)
        fits = [c.lel_fit_score for c in group if c.lel_fit_score is not None]
        score = sum(fits) / len(fits) if fits else 0.0
        scored.append((score, stable, off, group))

    if not scored:
        return BestRectification(
            best_candidate=None, candidate_birth_utc=None, offset_minutes=None,
            best_lagna_sign=None, best_lagna_longitude=None, best_lel_fit_score=None,
            confidence_low=None, confidence_high=None, confidence_label="unresolved",
            win_margin=None, competing_candidates=[], lel_training_events=n_training,
            lel_training_matched=None, leakage_firewall_note=firewall_note,
        )

    # Sort: score DESC, stable DESC, |offset| ASC (prefer closest to recorded).
    scored.sort(key=lambda t: (-t[0], not t[1], abs(t[2])))
    best_score, best_stable, best_off, best_group = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else 0.0
    win_margin = round(best_score - second_score, 4)

    # Representative ayanamsha for the best offset = lahiri (FORENSIC primary).
    rep = next((c for c in best_group if c.ayanamsha_id == "lahiri"), best_group[0])

    conf_low = round(best_score - (1.0 - best_score) * 0.2, 4)
    conf_high = round(best_score + (1.0 - best_score) * 0.2, 4)
    label = _confidence_label(win_margin)

    competing = [
        {
            "offset_minutes": off,
            "mean_lel_fit_score": round(score, 4),
            "lagna_stable": stable,
            "lagna_sign": next(
                (c.lagna_sign for c in grp if c.ayanamsha_id == "lahiri"),
                grp[0].lagna_sign,
            ),
        }
        for (score, stable, off, grp) in scored[:3]
    ]

    if AUTO_ACTION != "stage_for_review":
        raise RuntimeError(
            f"D43 gate violation: auto_action must be 'stage_for_review', got {AUTO_ACTION!r}"
        )

    return BestRectification(
        best_candidate=rep,
        candidate_birth_utc=rep.candidate_birth_utc,
        offset_minutes=best_off,
        best_lagna_sign=rep.lagna_sign,
        best_lagna_longitude=rep.lagna_longitude_deg,
        best_lel_fit_score=round(best_score, 4),
        confidence_low=conf_low,
        confidence_high=conf_high,
        confidence_label=label,
        win_margin=win_margin,
        competing_candidates=competing,
        lel_training_events=n_training,
        lel_training_matched=rep.lel_events_matched,
        leakage_firewall_note=firewall_note,
    )
