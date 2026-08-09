"""
services.ka_tulana.ranker — Cross-pattern prioritization engine (L3 Kāla, QT-4).

I-11 composite weights (NATIVE-RATIFIED 2026-06-21):
  convergence_score : 0.40  — primary rigor quality signal
  rarity_years      : 0.25  — cost-of-omission (rarer = more attention)
  confidence_score  : 0.20  — discounts speculative findings
  proximity_factor  : 0.15  — slightly favors sooner windows for actionability

NEVER writes to DB. NEVER calls conn.commit() / .rollback().
NEVER restates or recomputes kala_convergence / kala_darshana scores — reads only.
G13/PA-4 (R17): domain vocabulary sourced from brahmagyan.domain_vocabulary (13-domain
canonical SSoT) — formerly a local 7-domain list mirroring bo_sangati.KNOWN_DOMAINS.
"""
from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional

from brahmagyan.domain_vocabulary import CANONICAL_DOMAINS

logger = logging.getLogger(__name__)

# G13/PA-4 (R17): local 7-domain list deleted; import canonical 13-domain vocabulary
# from brahmagyan.domain_vocabulary (the L0 SSoT).
# KNOWN_DOMAINS was a literal ["career", "wealth", "health", "relationship",
#                               "spirituality", "character", "general"] (7 domains).
# The ranker now buckets by all 13 canonical domains.
# Public name kept for backward compatibility with existing callers / tests that
# import `KNOWN_DOMAINS` from this module.
KNOWN_DOMAINS = CANONICAL_DOMAINS
_KNOWN_DOMAINS = CANONICAL_DOMAINS  # private alias used internally

# I-11 ratified composite weights (native sign-off 2026-06-21)
I11_WEIGHTS = {
    'convergence_score': 0.40,
    'rarity_years':      0.25,
    'confidence_score':  0.20,
    'proximity_factor':  0.15,
}

# Rarity normalization cap: Saturn conjunction ≈ 29.5yr is the practical ceiling
_RARITY_CAP_YR = 30.0

# Confidence label → numeric score mapping
_CONFIDENCE_NUMERIC = {'high': 1.0, 'moderate': 0.6, 'speculative': 0.2}

# Net-label dissonance detection — these indicate cross-domain tension
_DISSONANCE_LABELS = {'obstructed', 'obstructed_severe', 'mixed', 'neutral'}


@dataclass
class WindowInput:
    """
    Normalised window record fed into ka_tulana from kala_convergence /
    kala_darshana. All fields optional except convergence_score + peak_date.
    """
    window_id: str
    mode: str                                # 'A' or 'B'
    peak_date: date
    window_start: Optional[date] = None
    window_end: Optional[date] = None
    convergence_score: float = 0.0
    confidence_label: str = 'speculative'    # 'high'|'moderate'|'speculative'
    rarity_years: Optional[float] = None
    net_label: Optional[str] = None          # from kala_darshana
    domains: list[str] = field(default_factory=list)
    signal_id: Optional[str] = None
    source_citation: Optional[str] = None
    # Dissonance: True when another domain is in danger for this window
    has_dissonance: bool = False
    dissonance_domains: list[str] = field(default_factory=list)


@dataclass
class FactorBreakdown:
    convergence_score: float
    rarity_norm: float       # normalised to [0,1]
    confidence_score: float  # numeric from label
    proximity_factor: float
    composite: float
    # Which factor drove the difference in a head-to-head comparison
    decisive_factor: Optional[str] = None


@dataclass
class RankedWindow:
    rank: int
    window: WindowInput
    factors: FactorBreakdown
    rationale: str  # human-readable "why" (structured; LLM narrates from this)


@dataclass
class CompareVerdict:
    winner: WindowInput
    loser: WindowInput
    winner_factors: FactorBreakdown
    loser_factors: FactorBreakdown
    decisive_factor: str
    confidence_label: str  # label of the winner
    rationale: str
    dissonance_note: Optional[str] = None  # CF.L3.5 / I-23 dissonance note
    recommendation: str = 'proceed'        # 'proceed'|'defer'|'proceed_with_mitigation'


@dataclass
class AttentionMap:
    """
    Ranked list of windows across all domains — "what matters most" map
    for the native's attention budget (QT-4 multi-domain use case).
    """
    ranked: list[RankedWindow]              # global rank order
    by_domain: dict[str, list[RankedWindow]]  # top window per known domain
    horizon_days: int


# ── Scoring helpers ───────────────────────────────────────────────────────────

def _normalise_rarity(rarity_years: Optional[float]) -> float:
    """Map rarity_years → [0,1]; None → 0.5 neutral."""
    if rarity_years is None:
        return 0.5
    return min(1.0, rarity_years / _RARITY_CAP_YR)


def _proximity_factor(peak_date: date, reference_date: date) -> float:
    """
    Sooner windows score higher for actionability.
    30d  → 1.0
    90d  → 0.5  (interpolated linearly between 30–90)
    365d → 0.1
    >1yr → 0.05 (floor)
    """
    days = (peak_date - reference_date).days
    if days < 0:
        return 0.05  # past window
    if days <= 30:
        return 1.0
    if days <= 90:
        return 1.0 - 0.5 * (days - 30) / 60.0
    if days <= 365:
        return 0.5 - 0.4 * (days - 90) / 275.0
    return 0.05


def _composite(w: WindowInput, reference_date: date) -> FactorBreakdown:
    """Compute I-11 composite score for a single window."""
    cs  = max(0.0, min(1.0, w.convergence_score))
    rar = _normalise_rarity(w.rarity_years)
    con = _CONFIDENCE_NUMERIC.get(w.confidence_label, 0.2)
    prx = _proximity_factor(w.peak_date, reference_date)

    composite = (
        I11_WEIGHTS['convergence_score'] * cs +
        I11_WEIGHTS['rarity_years']      * rar +
        I11_WEIGHTS['confidence_score']  * con +
        I11_WEIGHTS['proximity_factor']  * prx
    )
    return FactorBreakdown(
        convergence_score=round(cs, 4),
        rarity_norm=round(rar, 4),
        confidence_score=round(con, 4),
        proximity_factor=round(prx, 4),
        composite=round(composite, 4),
    )


def _rationale(w: WindowInput, fb: FactorBreakdown, rank: int) -> str:
    """Build a structured rationale string for a ranked window."""
    parts = [
        f"Rank #{rank}:",
        f"convergence={fb.convergence_score:.2f} (weight 40%)",
        f"rarity_norm={fb.rarity_norm:.2f} (~{w.rarity_years or 'unknown'}yr cycle, weight 25%)",
        f"confidence={fb.confidence_score:.2f} ({w.confidence_label}, weight 20%)",
        f"proximity={fb.proximity_factor:.2f} (peak {w.peak_date}, weight 15%)",
        f"→ composite={fb.composite:.3f}",
    ]
    if w.has_dissonance and w.dissonance_domains:
        parts.append(
            f"[DISSONANCE: favorable for {','.join(w.domains or ['?'])} "
            f"but danger in {','.join(w.dissonance_domains)}]"
        )
    return " | ".join(parts)


# ── Core API ─────────────────────────────────────────────────────────────────

class KaTulanaService:
    """
    Cross-pattern prioritization service (L3 Kāla, QT-4).

    Pure ranking logic over already-computed kala_convergence windows.
    No DB writes. No commit/rollback.
    """

    def rank_windows(
        self,
        windows: list[WindowInput],
        reference_date: Optional[date] = None,
    ) -> list[RankedWindow]:
        """
        Rank windows by I-11 composite score (desc).

        Parameters
        ----------
        windows : list[WindowInput]
            Windows from kala_convergence / kala_darshana for this chart.
        reference_date : date | None
            The "today" for proximity computation. Defaults to date.today().

        Returns
        -------
        list[RankedWindow]  — ordered best-first; includes per-factor breakdown + rationale.
        """
        ref = reference_date or date.today()
        scored = []
        for w in windows:
            fb = _composite(w, ref)
            scored.append((fb.composite, w, fb))

        scored.sort(key=lambda x: x[0], reverse=True)

        result: list[RankedWindow] = []
        for rank, (_, w, fb) in enumerate(scored, start=1):
            fb.decisive_factor = None  # single-window ranking has no "vs" context
            result.append(RankedWindow(
                rank=rank,
                window=w,
                factors=fb,
                rationale=_rationale(w, fb, rank),
            ))
        return result

    def compare(
        self,
        window_a: WindowInput,
        window_b: WindowInput,
        reference_date: Optional[date] = None,
    ) -> CompareVerdict:
        """
        Head-to-head comparison of two windows (QT-4 explicit compare).

        Returns the winner, per-factor breakdown, decisive factor, and
        dissonance-aware recommendation (proceed / defer / proceed_with_mitigation).
        """
        ref = reference_date or date.today()
        fb_a = _composite(window_a, ref)
        fb_b = _composite(window_b, ref)

        # Determine decisive factor: largest per-factor difference
        factor_deltas = {
            'convergence_score': abs(fb_a.convergence_score - fb_b.convergence_score),
            'rarity_years':      abs(fb_a.rarity_norm      - fb_b.rarity_norm),
            'confidence_score':  abs(fb_a.confidence_score - fb_b.confidence_score),
            'proximity_factor':  abs(fb_a.proximity_factor - fb_b.proximity_factor),
        }
        decisive = max(factor_deltas, key=factor_deltas.get)

        if fb_a.composite >= fb_b.composite:
            winner, loser, wfb, lfb = window_a, window_b, fb_a, fb_b
        else:
            winner, loser, wfb, lfb = window_b, window_a, fb_b, fb_a

        wfb.decisive_factor = decisive
        lfb.decisive_factor = decisive

        # Dissonance-aware recommendation (I-23)
        dissonance_note = None
        recommendation = 'proceed'
        if winner.has_dissonance and winner.dissonance_domains:
            danger_doms = ', '.join(winner.dissonance_domains)
            favorable = ', '.join(winner.domains or ['the target domain'])
            if winner.confidence_label == 'speculative':
                recommendation = 'defer'
                dissonance_note = (
                    f"TENSION: window is favorable for {favorable} but danger exists "
                    f"in {danger_doms}. Low confidence → defer."
                )
            else:
                recommendation = 'proceed_with_mitigation'
                dissonance_note = (
                    f"TENSION: window is favorable for {favorable} but danger exists "
                    f"in {danger_doms}. Proceed with mitigation for {danger_doms} "
                    f"(→ ph_pratikara remediation layer)."
                )

        # Build rationale
        win_label = _CONFIDENCE_NUMERIC.get(winner.confidence_label, 0.2)
        lose_label = _CONFIDENCE_NUMERIC.get(loser.confidence_label, 0.2)
        rationale_parts = [
            f"Winner: window {winner.window_id} (peak {winner.peak_date}) over "
            f"window {loser.window_id} (peak {loser.peak_date}).",
            f"Decisive factor: {decisive} "
            f"(Δ={factor_deltas[decisive]:.3f}).",
            f"Composite: winner={wfb.composite:.3f} vs loser={lfb.composite:.3f}.",
        ]
        if dissonance_note:
            rationale_parts.append(dissonance_note)
        rationale_parts.append(f"Recommendation: {recommendation}.")

        return CompareVerdict(
            winner=winner,
            loser=loser,
            winner_factors=wfb,
            loser_factors=lfb,
            decisive_factor=decisive,
            confidence_label=winner.confidence_label,
            rationale=' '.join(rationale_parts),
            dissonance_note=dissonance_note,
            recommendation=recommendation,
        )

    def attention_map(
        self,
        windows: list[WindowInput],
        reference_date: Optional[date] = None,
        horizon_days: int = 365,
    ) -> AttentionMap:
        """
        Multi-domain attention budget: rank all windows globally + per-domain.
        Answers "of my N windows across ALL domains, where should attention go?"

        Only windows within horizon_days of reference_date are included.
        """
        ref = reference_date or date.today()

        # Filter to horizon
        in_horizon = [
            w for w in windows
            if 0 <= (w.peak_date - ref).days <= horizon_days
        ]

        ranked = self.rank_windows(in_horizon, ref)

        # Top window per known domain — G13/PA-4: over all 13 canonical domains
        by_domain: dict[str, list[RankedWindow]] = {d: [] for d in _KNOWN_DOMAINS}
        for rw in ranked:
            for domain in (rw.window.domains or ['general']):
                if domain in by_domain:
                    by_domain[domain].append(rw)

        return AttentionMap(
            ranked=ranked,
            by_domain=by_domain,
            horizon_days=horizon_days,
        )
