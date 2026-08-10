"""
services/gochara_v3/mechanisms/w22_moorti_nirnaya.py — W2.2 candidate mechanism.

Moorti nirnaya quality modifier — svarṇa / rajata / tāmra / loha multiplier
applied to gochara windows that overlap a graha's sign-ingress span.

WHAT THIS MODULE DOES
─────────────────────
Classical moorti-nirnaya (Phaladeepika Ch.27; BPHS Ch.28) grades each
sign-ingress of a transiting graha as gold / silver / copper / iron quality
based on the Moon's nakshatra AT INGRESS relative to the native's janma
nakshatra. The L3 writer (`ka_moorti_nirnaya`) already computes and stores
this quality tier per sign-run in `kala_moorti_nirnaya`. This mechanism
reads those pre-stored rows (via ClassContext — no new DB access) and converts
the quality tier into a multiplicative modifier on the lambda_v3 window score.

ADMISSION STATE
───────────────
This is a CANDIDATE mechanism (Wave 2, not wired into engine.py — Wave 4).
It is implemented here as a togglable module so it can be independently
ablation-tested before admission. The toggle is controlled by the engine's
mechanism registry; callers pass `enabled=False` to get a pass-through
modifier of 1.0 without any computation cost.

DB ACCESS
─────────
None. ClassContext is the sole data source. If the context carries no moorti
data (e.g. kala_moorti_nirnaya was not built for this chart), the module
returns modifier=1.0 honestly — graceful degrade, never a fabricated value.

HONESTY DISCIPLINE (§N.7 item 6)
──────────────────────────────────
- When moorti quality cannot be determined (no matching row, or
  `moorti_computed=False`), modifier is 1.0 — unit pass-through, not a guess.
- The `detail` dict in MechanismResult carries the reason whenever modifier
  stays at 1.0 so callers can distinguish "not applicable" from "svarna applied".
- Multipliers are bounded constants; modifier is always in [MULTIPLIER_MIN,
  MULTIPLIER_MAX] by construction. An explicit clamp is applied as a safety net
  for any future table extension.

CITATION
────────
Phaladeepika Ch.27 — Moorti nirnaya; bg_transit_moorti 27 rows (migration 401).
BPHS Ch.28 — Nakshatra Gochara + Moorti Nirnaya.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta, timezone, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.gochara_v3.context import ClassContext

logger = logging.getLogger(__name__)

# ── Public identifiers ─────────────────────────────────────────────────────────

MECHANISM_ID = "w22_moorti_nirnaya"
TOGGLE_KEY = "w22_moorti_nirnaya"

# ── Classical four-tier multipliers (§N.7: named constants, never bare literals)

# Svarna (gold) — the most auspicious tier: the transiting graha's Moon-nakshatra
# at ingress is in a dharmic (1st, 5th, 9th, etc.) offset from the janma nakshatra.
# Amplifies the window's contribution.
MOORTI_MULTIPLIER_SVARNA: float = 1.25

# Rajata (silver) — auspicious but moderate.
MOORTI_MULTIPLIER_RAJATA: float = 1.10

# Tamra (copper) — inauspicious; mild dampening.
MOORTI_MULTIPLIER_TAMRA: float = 0.90

# Loha (iron) — most inauspicious tier; strongest dampening.
MOORTI_MULTIPLIER_LOHA: float = 0.75

# Convenience map (also used externally in tests)
MOORTI_MULTIPLIERS: dict[str, float] = {
    "svarna": MOORTI_MULTIPLIER_SVARNA,
    "rajata": MOORTI_MULTIPLIER_RAJATA,
    "tamra": MOORTI_MULTIPLIER_TAMRA,
    "loha": MOORTI_MULTIPLIER_LOHA,
}

# Aliases: bg_transit_moorti stores "swarna" (with a 'w'); accept both spellings.
_MOORTI_NAME_NORMALISE: dict[str, str] = {
    "svarna": "svarna",
    "swarna": "svarna",   # alternate romanisation in the DB
    "rajata": "rajata",
    "tamra": "tamra",
    "loha": "loha",
}

# Safety clamp bounds — the multipliers above already live in this range, but
# we clamp defensively so any future table extension cannot produce a modifier
# that breaks downstream assumptions.
MULTIPLIER_MIN: float = 0.50
MULTIPLIER_MAX: float = 2.00


# ── Result dataclass ───────────────────────────────────────────────────────────

@dataclass
class MechanismResult:
    """Return value of compute().

    modifier  — multiplicative adjustment in [MULTIPLIER_MIN, MULTIPLIER_MAX].
                1.0 means no adjustment (disabled, no data, or not applicable).
    sentences — list of sentence dicts compatible with the v3 engine's sentence
                pool format (may be empty for this mechanism).
    detail    — diagnostic key/value pairs explaining how modifier was derived.
    mechanism_id — always MECHANISM_ID; present for registry-level introspection.
    enabled   — mirrors the `enabled` flag passed to compute().
    """
    modifier: float = 1.0
    sentences: list[dict] = field(default_factory=list)
    detail: dict = field(default_factory=dict)
    mechanism_id: str = MECHANISM_ID
    enabled: bool = True


# ── Internal helpers ───────────────────────────────────────────────────────────

def _jd_to_date(t_jd: float) -> date:
    """Convert a Julian Day Number to a UTC calendar date.

    Uses the standard astronomical JD epoch (noon 1 Jan 4713 BC = JD 0.0).
    Day-grade precision only — matches the kala_moorti_nirnaya writer's own
    day-grade discipline (SHAD_DARSHANA_BRIEF_v2_0.md §4).
    """
    # JD 2440587.5 = 1970-01-01 00:00:00 UTC
    unix_days = t_jd - 2440587.5
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    dt = epoch + timedelta(days=unix_days)
    return dt.date()


def _normalise_moorti_name(raw: str | None) -> str | None:
    """Normalise a moorti_name string to the canonical four-value set."""
    if raw is None:
        return None
    return _MOORTI_NAME_NORMALISE.get(raw.lower().strip())


def _find_overlapping_moorti(context: "ClassContext", t_jd: float) -> str | None:
    """Return the normalised moorti_name for the graha sign-run that overlaps
    the given Julian Day, or None if no computed row covers this instant.

    Searches `context.natal_facts` for moorti data held on the context.
    The actual moorti rows are not currently part of ClassContext (they live in
    kala_moorti_nirnaya, pre-built by the L3 writer). This mechanism reads
    whatever moorti signal is available from the context.

    Strategy:
    1. If context carries explicit moorti_rows (future W4 integration path),
       use them directly.
    2. Otherwise fall back to natal_facts if it carries any moorti hint.
    3. If nothing is available, return None (honest absence).

    Currently kala_moorti_nirnaya data is NOT plumbed into ClassContext (that
    is Wave 4 wiring work). This module is a CANDIDATE mechanism: it defines
    the correct interface and returns honest None / 1.0 when the data path is
    not yet live. The test suite uses injected fixture data on context to verify
    the multiplier logic independently of the wiring.
    """
    # Future wiring point: if ClassContext gains a `moorti_rows` attribute,
    # check it here first. For now we rely on any moorti data the caller
    # injects via a subclassed or monkey-patched context for testing, or the
    # natal_facts fallback (which does not carry moorti quality — honest None).
    moorti_rows = getattr(context, "moorti_rows", None)
    if not moorti_rows:
        return None

    as_of = _jd_to_date(t_jd)
    for row in moorti_rows:
        # Each row must have: window_start (date or str), window_end (date or
        # str), moorti_name (str), moorti_computed (bool).
        try:
            w_start = row.get("window_start")
            w_end = row.get("window_end")
            computed = row.get("moorti_computed", False)
            if not computed:
                continue
            if isinstance(w_start, str):
                w_start = date.fromisoformat(w_start)
            if isinstance(w_end, str):
                w_end = date.fromisoformat(w_end)
            if w_start <= as_of <= w_end:
                return _normalise_moorti_name(row.get("moorti_name"))
        except Exception:  # noqa: BLE001
            continue
    return None


# ── Public API ─────────────────────────────────────────────────────────────────

def compute(
    context: "ClassContext",
    t_jd: float,
    *,
    enabled: bool = True,
) -> MechanismResult:
    """Compute the moorti nirnaya modifier for the given Julian Day.

    Parameters
    ----------
    context:
        The pre-fetched ClassContext for this (chart x event_class) pair.
        Must not be None.
    t_jd:
        The Julian Day being evaluated (day-grade — sub-day precision is
        not expected or used).
    enabled:
        When False, returns a unit modifier (1.0) immediately without any
        computation. Controlled by the engine's mechanism toggle registry.

    Returns
    -------
    MechanismResult with modifier in [MULTIPLIER_MIN, MULTIPLIER_MAX].
    """
    if not enabled:
        return MechanismResult(
            modifier=1.0,
            detail={"reason": "disabled"},
            enabled=False,
        )

    # ── Attempt to resolve moorti quality for this JD ─────────────────────────
    moorti_name = _find_overlapping_moorti(context, t_jd)

    if moorti_name is None:
        # Honest absence: no moorti data available in context (either the L3
        # asset was not built for this chart, or this JD falls outside all
        # computed ingress windows). Unit pass-through — not a guess.
        logger.debug(
            "[w22_moorti_nirnaya] no moorti data for chart=%s jd=%.2f — modifier=1.0",
            getattr(context, "chart_id", "?"),
            t_jd,
        )
        return MechanismResult(
            modifier=1.0,
            detail={"reason": "no_moorti_data"},
        )

    raw_modifier = MOORTI_MULTIPLIERS.get(moorti_name)
    if raw_modifier is None:
        # Unknown quality name — honest gap rather than a guess.
        logger.warning(
            "[w22_moorti_nirnaya] unrecognised moorti_name=%r for chart=%s — modifier=1.0",
            moorti_name,
            getattr(context, "chart_id", "?"),
        )
        return MechanismResult(
            modifier=1.0,
            detail={"reason": "unrecognised_moorti_name", "moorti_name": moorti_name},
        )

    # Clamp for safety (the constants already satisfy this; defensive only).
    modifier = max(MULTIPLIER_MIN, min(MULTIPLIER_MAX, raw_modifier))

    return MechanismResult(
        modifier=modifier,
        detail={
            "moorti_name": moorti_name,
            "raw_multiplier": raw_modifier,
            "modifier": modifier,
            "reason": "moorti_quality_applied",
        },
    )


__all__ = [
    "MECHANISM_ID",
    "TOGGLE_KEY",
    "MOORTI_MULTIPLIERS",
    "MOORTI_MULTIPLIER_SVARNA",
    "MOORTI_MULTIPLIER_RAJATA",
    "MOORTI_MULTIPLIER_TAMRA",
    "MOORTI_MULTIPLIER_LOHA",
    "MULTIPLIER_MIN",
    "MULTIPLIER_MAX",
    "MechanismResult",
    "compute",
]
