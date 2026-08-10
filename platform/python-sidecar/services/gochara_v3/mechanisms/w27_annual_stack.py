"""
services/gochara_v3/mechanisms/w27_annual_stack.py — W2.7 annual context stack.

Three sub-mechanism PERMISSION generators, each independently togglable:

  w27a_tajaka_year_lord  — Is the transiting body the Tājaka year-lord
                           for the native's current varsha?
  w27b_tithi_pravesha    — Praveśa-chart annual tone for the event class
                           (favourable / mixed / adverse annual chart).
  w27c_sudarshana        — Sudarśana cakra house placement of the transit
                           body at evaluation time.

ADMISSION STATE
───────────────
CANDIDATE mechanisms (Wave 2, Lane W2.7). NOT wired into engine.py — that
wiring is Wave 4 work. Each sub-mechanism is implemented here as a separate,
independently-togglable unit so ablation evidence can be collected before
admission. The top-level ``compute()`` combines all three into one
MechanismResult whose modifier is the product of the three sub-modifiers
(each contributes independently; product preserves [0,1]→[0,2] range).

DATA SOURCE
───────────
ClassContext is the sole data source (no DB access). The three sub-mechanisms
read from optional fields on the context that are populated when the annual
layer data has been built:

  w27a — context.tajaka_year_lords  (list of dicts from l1_tajik_varsha_year_lords)
          or context.annual_data     (same, alternate field name)
  w27b — context.tithi_pravesha_rows (list of dicts from kala_tithi_pravesha)
  w27c — context.sudarshana_rows    (list of dicts from kala_sudarshana / bo_sudarshana)

When any of these fields is absent or empty, the corresponding sub-mechanism
returns modifier=1.0 honestly (§N.7 item 6 — honest null beats invented judgment).

HONESTY DISCIPLINE
──────────────────
- Missing annual data → modifier 1.0 with detail.reason = "no_annual_data".
- All modifiers clamped to [MODIFIER_MIN, MODIFIER_MAX] = [0.0, 2.0].
- Each sub-mechanism reports its own detail dict; the top-level detail
  aggregates them under "sub_mechanisms".
- No fabricated value: if data is absent we do NOT substitute a guess.

CLASSICAL GROUNDING
───────────────────
w27a: Tājaka/Vārṣaphal — year-lord (Vārṣeśa) is the primary significator
      of the year's outcomes (Tājaka Nīlakaṇṭhī Ch.1; BPHS Tājaka chapter).
      A transit by the year-lord is classically more potent.
w27b: Tithi Praveśa chart — the Praveśa chart at the annual tithi entry gives
      the annual tone for each domain (Kṛṣṇa Miśra / Tājaka tradition).
w27c: Sudarśana cakra — house placement of a transit body as seen from the
      Sudarśana perspective (Sun-ascendant composite chart) modifies the
      transit's classical effectiveness (Sudarśana Cakra Paddhati).

DOCUMENTED GAP (permission.py:60-68)
──────────────────────────────────────
This module directly addresses the honest scope gap documented in
``services/gochara_intensity/permission.py`` lines 60–68: "a standalone
Tājaka varṣaphala year-lord signal distinct from mudda." W2.7 is that
signal plus two companion annual-context generators.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Mechanism IDs ────────────────────────────────────────────────────────────

MECHANISM_ID_A = "w27a_tajaka_year_lord"
MECHANISM_ID_B = "w27b_tithi_pravesha"
MECHANISM_ID_C = "w27c_sudarshana"

# Combined ID for the top-level result
MECHANISM_ID = "w27_annual_stack"

TOGGLE_KEY_A = "w27a_tajaka_year_lord"
TOGGLE_KEY_B = "w27b_tithi_pravesha"
TOGGLE_KEY_C = "w27c_sudarshana"

# ── Modifier constants ───────────────────────────────────────────────────────

MODIFIER_MIN = 0.0
MODIFIER_MAX = 2.0
MODIFIER_NEUTRAL = 1.0

# w27a: year-lord match amplifies, non-match is neutral (absence is not adverse)
_YL_MATCH_MODIFIER = 1.35      # year-lord transit — amplify
_YL_NOMATCH_MODIFIER = 1.0     # no match — neutral

# w27b: pravesha tone → modifier
_TP_FAVOURABLE_MODIFIER = 1.25
_TP_MIXED_MODIFIER = 1.0
_TP_ADVERSE_MODIFIER = 0.80

# w27c: Sudarshana house placement modifiers (1-indexed house, classical schedule)
# Houses 1, 4, 7, 10 (kendras) → amplify; 2, 5, 9 (trikonas+2) → mild amplify;
# 3, 6, 10, 11 → mixed; 8, 12 → damp; 6 (dusthana) → mild damp
_SD_HOUSE_MODIFIERS: dict[int, float] = {
    1: 1.30,   # Lagna — strongest
    2: 1.10,
    3: 0.95,
    4: 1.25,   # kendra
    5: 1.20,   # trikona
    6: 0.85,   # dusthana — damp
    7: 1.25,   # kendra
    8: 0.75,   # dusthana — strong damp
    9: 1.20,   # trikona
    10: 1.30,  # kendra — strongest
    11: 1.10,
    12: 0.80,  # dusthana — damp
}
_SD_DEFAULT_MODIFIER = MODIFIER_NEUTRAL  # unknown house → neutral


# ── MechanismResult ──────────────────────────────────────────────────────────

@dataclass
class MechanismResult:
    """Result returned by ``compute()`` and each sub-compute function.

    modifier: multiplicative factor for lambda_e.
        1.0 = no effect
        < 1.0 = damping
        > 1.0 = amplification
    sentences: list of sentence-level detail dicts.
    detail: summary dict for this mechanism.
    mechanism_id: the mechanism id string.
    enabled: False when the mechanism was disabled at call time.
    """
    modifier: float = MODIFIER_NEUTRAL
    sentences: list[dict] = field(default_factory=list)
    detail: dict = field(default_factory=dict)
    mechanism_id: str = MECHANISM_ID
    enabled: bool = True


# ── Helper: clamp ────────────────────────────────────────────────────────────

def _clamp(value: float) -> float:
    return max(MODIFIER_MIN, min(MODIFIER_MAX, value))


# ── Helper: JD → approximate ISO year ───────────────────────────────────────

def _jd_to_approx_year(t_jd: float) -> int:
    """Rough Julian Day → Gregorian year (±1 day accuracy is fine here)."""
    # JD 2451545.0 = 2000-01-01.5; 365.25 days/year
    return int(2000 + (t_jd - 2451545.0) / 365.25)


# ── Sub-mechanism A: Tājaka year-lord ────────────────────────────────────────

def compute_tajaka_year_lord(
    context: Any,
    t_jd: float,
    *,
    enabled: bool = True,
) -> MechanismResult:
    """Check whether the transiting graha is the Tājaka year-lord (Vārṣeśa).

    Reads context.tajaka_year_lords (or context.annual_data) — a list/tuple
    of dicts with at minimum keys:
        "varsha_year" (int),
        "year_lord"   (str, graha name),
        "varsha_start_iso" (str, YYYY-MM-DD),
        "varsha_end_iso"   (str, YYYY-MM-DD).

    The resonance targets' grahas are extracted from context.resonance_targets;
    if the year-lord graha appears in that set, the modifier fires (amplify).

    Missing data → modifier=1.0, honest detail.
    """
    if not enabled:
        return MechanismResult(
            modifier=MODIFIER_NEUTRAL,
            sentences=[],
            detail={"reason": "disabled"},
            mechanism_id=MECHANISM_ID_A,
            enabled=False,
        )

    # Retrieve annual year-lord rows
    annual_rows = (
        getattr(context, "tajaka_year_lords", None)
        or getattr(context, "annual_data", None)
        or []
    )
    if not annual_rows:
        return MechanismResult(
            modifier=MODIFIER_NEUTRAL,
            sentences=[],
            detail={
                "reason": "no_annual_data",
                "note": (
                    "tajaka_year_lords is absent or empty — no Tājaka annual data "
                    "available for this chart; modifier held at 1.0 per honest-null doctrine."
                ),
            },
            mechanism_id=MECHANISM_ID_A,
            enabled=True,
        )

    # Collect resonance target grahas from context
    resonance_targets = getattr(context, "resonance_targets", ()) or ()
    target_grahas: set[str] = set()
    for t in resonance_targets:
        graha = getattr(t, "graha", None) or getattr(t, "target_ref", None)
        if graha:
            target_grahas.add(str(graha))

    # Also include relevant_grahas from context (pre-computed set)
    rel_grahas = getattr(context, "relevant_grahas", frozenset()) or frozenset()
    target_grahas |= set(rel_grahas)

    # Approximate current varsha from t_jd
    approx_year = _jd_to_approx_year(t_jd)

    # Find the matching varsha row — prefer exact date match, fall back to year
    matching_row: Optional[dict] = None
    for row in annual_rows:
        if not isinstance(row, dict):
            continue
        start_iso = row.get("varsha_start_iso") or ""
        end_iso = row.get("varsha_end_iso") or ""
        # Try ISO date comparison (YYYY-MM-DD prefix of start/end)
        start_year = int(start_iso[:4]) if start_iso and len(start_iso) >= 4 else 0
        end_year = int(end_iso[:4]) if end_iso and len(end_iso) >= 4 else 9999
        if start_year <= approx_year <= end_year:
            matching_row = row
            break

    if matching_row is None:
        # Fall back: use the most recent row by varsha_year
        rows_with_year = [r for r in annual_rows if isinstance(r, dict) and r.get("varsha_year")]
        if rows_with_year:
            matching_row = max(rows_with_year, key=lambda r: r.get("varsha_year", 0))

    if matching_row is None:
        return MechanismResult(
            modifier=MODIFIER_NEUTRAL,
            sentences=[],
            detail={
                "reason": "no_matching_varsha",
                "approx_year": approx_year,
                "note": "No varsha row matched the evaluation JD; holding neutral.",
            },
            mechanism_id=MECHANISM_ID_A,
            enabled=True,
        )

    year_lord = str(matching_row.get("year_lord") or "")
    varsha_year = matching_row.get("varsha_year")

    # Does the year-lord appear in our resonance-target/relevant-graha set?
    year_lord_matches = bool(year_lord and year_lord in target_grahas)

    if year_lord_matches:
        modifier = _clamp(_YL_MATCH_MODIFIER)
        classification = "year_lord_match"
        note = (
            f"Year-lord {year_lord!r} (varsha {varsha_year}) is in the resonance "
            f"target set {sorted(target_grahas)!r} → amplify"
        )
    else:
        modifier = _clamp(_YL_NOMATCH_MODIFIER)
        classification = "year_lord_no_match"
        note = (
            f"Year-lord {year_lord!r} (varsha {varsha_year}) not in target set "
            f"{sorted(target_grahas)!r} → neutral"
        )

    sentence = {
        "mechanism_id": MECHANISM_ID_A,
        "year_lord": year_lord,
        "varsha_year": varsha_year,
        "classification": classification,
        "modifier": modifier,
        "target_grahas": sorted(target_grahas),
        "note": note,
        "t_jd": t_jd,
    }

    return MechanismResult(
        modifier=modifier,
        sentences=[sentence],
        detail={
            "mechanism_id": MECHANISM_ID_A,
            "year_lord": year_lord,
            "varsha_year": varsha_year,
            "year_lord_matches": year_lord_matches,
            "modifier": modifier,
            "classification": classification,
            "approx_year": approx_year,
        },
        mechanism_id=MECHANISM_ID_A,
        enabled=True,
    )


# ── Sub-mechanism B: Tithi Praveśa tone ──────────────────────────────────────

def compute_tithi_pravesha(
    context: Any,
    t_jd: float,
    *,
    enabled: bool = True,
) -> MechanismResult:
    """Annual Praveśa-chart tone modifier for the event class.

    Reads context.tithi_pravesha_rows — a list/tuple of dicts with keys:
        "event_class"   (str),
        "tone"          (str: "favourable" | "mixed" | "adverse"),
        "varsha_start_iso" (str, YYYY-MM-DD),
        "varsha_end_iso"   (str, YYYY-MM-DD).

    The tone maps to a fixed modifier (§_TP_* constants). When the tone is
    absent or unrecognised, modifier=1.0 (honest null).
    """
    if not enabled:
        return MechanismResult(
            modifier=MODIFIER_NEUTRAL,
            sentences=[],
            detail={"reason": "disabled"},
            mechanism_id=MECHANISM_ID_B,
            enabled=False,
        )

    pravesha_rows = getattr(context, "tithi_pravesha_rows", None) or []
    if not pravesha_rows:
        return MechanismResult(
            modifier=MODIFIER_NEUTRAL,
            sentences=[],
            detail={
                "reason": "no_annual_data",
                "note": (
                    "tithi_pravesha_rows is absent or empty — no Praveśa-chart tone "
                    "data available; modifier held at 1.0 per honest-null doctrine."
                ),
            },
            mechanism_id=MECHANISM_ID_B,
            enabled=True,
        )

    event_class = getattr(context, "event_class", "") or ""
    approx_year = _jd_to_approx_year(t_jd)

    # Find the row matching event_class and covering the evaluation year
    matching_row: Optional[dict] = None
    for row in pravesha_rows:
        if not isinstance(row, dict):
            continue
        row_class = str(row.get("event_class") or "")
        if row_class and row_class != event_class:
            continue  # filter by event_class when present
        start_iso = row.get("varsha_start_iso") or ""
        end_iso = row.get("varsha_end_iso") or ""
        start_year = int(start_iso[:4]) if start_iso and len(start_iso) >= 4 else 0
        end_year = int(end_iso[:4]) if end_iso and len(end_iso) >= 4 else 9999
        if start_year <= approx_year <= end_year:
            matching_row = row
            break

    # Fall back to any row for the event class (ignore year)
    if matching_row is None:
        for row in pravesha_rows:
            if not isinstance(row, dict):
                continue
            row_class = str(row.get("event_class") or "")
            if not row_class or row_class == event_class:
                matching_row = row
                break

    if matching_row is None:
        return MechanismResult(
            modifier=MODIFIER_NEUTRAL,
            sentences=[],
            detail={
                "reason": "no_matching_row",
                "event_class": event_class,
                "approx_year": approx_year,
                "note": "No pravesha row matched event_class + JD; holding neutral.",
            },
            mechanism_id=MECHANISM_ID_B,
            enabled=True,
        )

    tone = str(matching_row.get("tone") or "").lower()
    _tone_map = {
        "favourable": _TP_FAVOURABLE_MODIFIER,
        "favorable": _TP_FAVOURABLE_MODIFIER,  # spelling variant
        "auspicious": _TP_FAVOURABLE_MODIFIER,
        "mixed": _TP_MIXED_MODIFIER,
        "neutral": _TP_MIXED_MODIFIER,
        "adverse": _TP_ADVERSE_MODIFIER,
        "inauspicious": _TP_ADVERSE_MODIFIER,
        "unfavourable": _TP_ADVERSE_MODIFIER,
    }
    modifier = _clamp(_tone_map.get(tone, MODIFIER_NEUTRAL))
    classification = tone if tone in _tone_map else "unrecognised_tone"

    note = (
        f"Praveśa tone={tone!r} for event_class={event_class!r} → modifier={modifier:.3f}"
    )
    sentence = {
        "mechanism_id": MECHANISM_ID_B,
        "tone": tone,
        "event_class": event_class,
        "classification": classification,
        "modifier": modifier,
        "note": note,
        "t_jd": t_jd,
    }

    return MechanismResult(
        modifier=modifier,
        sentences=[sentence],
        detail={
            "mechanism_id": MECHANISM_ID_B,
            "tone": tone,
            "event_class": event_class,
            "classification": classification,
            "modifier": modifier,
            "approx_year": approx_year,
        },
        mechanism_id=MECHANISM_ID_B,
        enabled=True,
    )


# ── Sub-mechanism C: Sudarśana house placement ────────────────────────────────

def compute_sudarshana(
    context: Any,
    t_jd: float,
    *,
    enabled: bool = True,
) -> MechanismResult:
    """Sudarśana cakra house placement modifier.

    Reads context.sudarshana_rows — a list/tuple of dicts with keys:
        "graha"          (str),
        "house_number"   (int, 1–12),
        "window_start_iso" (str, YYYY-MM-DD),
        "window_end_iso"   (str, YYYY-MM-DD).

    For each resonance-target graha with a Sudarśana house placement
    covering the evaluation JD, the house modifier from _SD_HOUSE_MODIFIERS
    is applied. Aggregate = geometric mean of applicable per-graha modifiers.

    Missing data → modifier=1.0, honest detail.
    """
    if not enabled:
        return MechanismResult(
            modifier=MODIFIER_NEUTRAL,
            sentences=[],
            detail={"reason": "disabled"},
            mechanism_id=MECHANISM_ID_C,
            enabled=False,
        )

    sudarshana_rows = getattr(context, "sudarshana_rows", None) or []
    if not sudarshana_rows:
        return MechanismResult(
            modifier=MODIFIER_NEUTRAL,
            sentences=[],
            detail={
                "reason": "no_annual_data",
                "note": (
                    "sudarshana_rows is absent or empty — no Sudarśana data "
                    "available; modifier held at 1.0 per honest-null doctrine."
                ),
            },
            mechanism_id=MECHANISM_ID_C,
            enabled=True,
        )

    # Collect resonance target grahas
    resonance_targets = getattr(context, "resonance_targets", ()) or ()
    target_grahas: set[str] = set()
    for t in resonance_targets:
        graha = getattr(t, "graha", None) or getattr(t, "target_ref", None)
        if graha:
            target_grahas.add(str(graha))
    rel_grahas = getattr(context, "relevant_grahas", frozenset()) or frozenset()
    target_grahas |= set(rel_grahas)

    approx_year = _jd_to_approx_year(t_jd)

    sentences: list[dict] = []
    per_graha_modifiers: list[float] = []

    for row in sudarshana_rows:
        if not isinstance(row, dict):
            continue
        graha = str(row.get("graha") or "")
        if graha and target_grahas and graha not in target_grahas:
            continue  # only evaluate target grahas

        # Check temporal coverage
        start_iso = row.get("window_start_iso") or row.get("varsha_start_iso") or ""
        end_iso = row.get("window_end_iso") or row.get("varsha_end_iso") or ""
        start_year = int(start_iso[:4]) if start_iso and len(start_iso) >= 4 else 0
        end_year = int(end_iso[:4]) if end_iso and len(end_iso) >= 4 else 9999
        if not (start_year <= approx_year <= end_year):
            continue

        house_raw = row.get("house_number")
        try:
            house = int(house_raw)
        except (TypeError, ValueError):
            house = 0

        row_modifier = _clamp(_SD_HOUSE_MODIFIERS.get(house, _SD_DEFAULT_MODIFIER))
        per_graha_modifiers.append(row_modifier)

        note = (
            f"Graha {graha!r} in Sudarśana house {house} → modifier={row_modifier:.3f}"
            if house else
            f"Graha {graha!r}: house_number absent or invalid → neutral"
        )
        sentences.append({
            "mechanism_id": MECHANISM_ID_C,
            "graha": graha,
            "house_number": house,
            "row_modifier": row_modifier,
            "note": note,
            "t_jd": t_jd,
        })

    if not per_graha_modifiers:
        return MechanismResult(
            modifier=MODIFIER_NEUTRAL,
            sentences=[],
            detail={
                "reason": "no_applicable_rows",
                "note": (
                    "sudarshana_rows present but no row covered the evaluation JD "
                    "or matched target grahas; holding neutral."
                ),
                "approx_year": approx_year,
                "target_grahas": sorted(target_grahas),
            },
            mechanism_id=MECHANISM_ID_C,
            enabled=True,
        )

    # Geometric mean of per-graha modifiers (same aggregation as W2.1)
    log_sum = sum(math.log(max(m, 1e-9)) for m in per_graha_modifiers)
    agg_modifier = _clamp(math.exp(log_sum / len(per_graha_modifiers)))

    return MechanismResult(
        modifier=agg_modifier,
        sentences=sentences,
        detail={
            "mechanism_id": MECHANISM_ID_C,
            "rows_evaluated": len(per_graha_modifiers),
            "per_graha_modifiers": per_graha_modifiers,
            "aggregate_modifier": agg_modifier,
            "target_grahas": sorted(target_grahas),
            "approx_year": approx_year,
        },
        mechanism_id=MECHANISM_ID_C,
        enabled=True,
    )


# ── Top-level compute ─────────────────────────────────────────────────────────

def compute(
    context: Any,
    t_jd: float,
    *,
    enabled: bool = True,
    enabled_a: bool = True,
    enabled_b: bool = True,
    enabled_c: bool = True,
) -> MechanismResult:
    """Compute the combined W2.7 annual context stack modifier.

    Combines all three sub-mechanisms into one MechanismResult.
    The aggregate modifier is the product of the three sub-modifiers,
    clamped to [MODIFIER_MIN, MODIFIER_MAX].

    Parameters
    ----------
    context:
        A ClassContext-like object. Sub-mechanisms read optional attributes
        (tajaka_year_lords, tithi_pravesha_rows, sudarshana_rows, resonance_targets,
        relevant_grahas, event_class). Missing attributes degrade gracefully to 1.0.
    t_jd:
        Julian Day of the evaluation point.
    enabled:
        Master toggle. When False the combined result is a unit pass-through
        (modifier=1.0) with all three sub-mechanisms also disabled.
    enabled_a, enabled_b, enabled_c:
        Per-sub-mechanism toggles (independent ablation). Only effective when
        ``enabled=True``.
    """
    if not enabled:
        return MechanismResult(
            modifier=MODIFIER_NEUTRAL,
            sentences=[],
            detail={"reason": "disabled"},
            mechanism_id=MECHANISM_ID,
            enabled=False,
        )

    result_a = compute_tajaka_year_lord(context, t_jd, enabled=enabled_a)
    result_b = compute_tithi_pravesha(context, t_jd, enabled=enabled_b)
    result_c = compute_sudarshana(context, t_jd, enabled=enabled_c)

    combined_modifier = _clamp(result_a.modifier * result_b.modifier * result_c.modifier)

    all_sentences = result_a.sentences + result_b.sentences + result_c.sentences

    combined_detail = {
        "mechanism_id": MECHANISM_ID,
        "combined_modifier": combined_modifier,
        "sub_mechanisms": {
            MECHANISM_ID_A: result_a.detail,
            MECHANISM_ID_B: result_b.detail,
            MECHANISM_ID_C: result_c.detail,
        },
        "sub_modifiers": {
            MECHANISM_ID_A: result_a.modifier,
            MECHANISM_ID_B: result_b.modifier,
            MECHANISM_ID_C: result_c.modifier,
        },
        "enabled_flags": {
            MECHANISM_ID_A: enabled_a,
            MECHANISM_ID_B: enabled_b,
            MECHANISM_ID_C: enabled_c,
        },
    }

    return MechanismResult(
        modifier=combined_modifier,
        sentences=all_sentences,
        detail=combined_detail,
        mechanism_id=MECHANISM_ID,
        enabled=True,
    )


__all__ = [
    "MECHANISM_ID",
    "MECHANISM_ID_A",
    "MECHANISM_ID_B",
    "MECHANISM_ID_C",
    "TOGGLE_KEY_A",
    "TOGGLE_KEY_B",
    "TOGGLE_KEY_C",
    "MODIFIER_MIN",
    "MODIFIER_MAX",
    "MODIFIER_NEUTRAL",
    "MechanismResult",
    "compute",
    "compute_tajaka_year_lord",
    "compute_tithi_pravesha",
    "compute_sudarshana",
]
