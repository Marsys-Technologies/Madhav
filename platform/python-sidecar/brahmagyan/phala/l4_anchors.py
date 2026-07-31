"""
brahmagyan/phala/l4_anchors.py — Brahma L4 Phala — phala.anchors expanded catalog (PH-4-1-v2)
==============================================================================================

Asset:    phala.anchors (v2 — 2026-2040 expanded catalog)
Tool:     query_phala_anchors(chart_id, date_range, min_confidence?, domain?) →
              {anchors:[{...}], provenance_envelope}

Volume floor: ≥ 20 anchors across 2026-2040.
Actual: 24 anchors across 6 domains covering Mercury MD / Ketu MD / Venus MD.

Anchor structure (each):
  anchor_id         — ANC.<DOMAIN>.<YYYY>.<NN>
  dasha_period      — {md, ad, pd?, start, end}
  event_type        — human-readable theme label
  direction         — "elevated" | "suppressed"
  signal_basis      — list of L2 signal_ids (MSR SIG.* / CVG.*)
  kala_window       — {start, end, convergence_type, source_obs_id?}
  falsifier         — specific observable that refutes the anchor
  confidence        — 0.0–1.0 (multi-signal convergence required for >0.80)
  domain            — career | relationship | financial | spiritual | health | transition

Confidence calibration (AUTONOMOUS_MODE rule):
  Single signal:      max 0.55
  2 signals:          max 0.65
  3 signals:          max 0.72
  3+ signals + kala:  max 0.78
  ≥4 + kala + dasha:  up to 0.80 (hard ceiling)

Native chart state (current, 2026-06-05):
  Mahadasha:   Mercury (2010-08-21 → 2027-08-21)
  Antardasha:  Saturn (2024-12-12 → 2027-08-21)
  Pratyantara: Sun (active mid-2026)
  Sade Sati:   Cycle 2 Setting phase (Saturn in Pisces/2nd from Moon=Aquarius)
  Jupiter:     Exalted Cancer (H4 from Lagna=Aries)
  Score:       49/100 NEUTRAL

Source: FORENSIC v8.0 §5.1 §22 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md); MSR_v5_0.md; LEL_v1_2.md;
        l3_convergence.py SIGNAL_ANCHORS; l3_obstruction.py SADE_SATI_WINDOWS.
Authors: Silpī (WS-2 l4-phala session)
Version: 1.0 — 2026-06-05
BRAHMA-PH-4-1-V2
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Privacy guard: strip LEL citations from public notes field (C2-002) ───────

def strip_lel_citations(text: str) -> str:
    """Remove LEL citation patterns from public-facing notes fields.

    C2-002: LEL data is isolated in mimamsa.lel_events and must not leak
    into the retrieval API surface via the notes field.

    Patterns caught:
      - '(LEL EVT.YYYY ...)' parenthetical blocks
      - 'per LEL...' phrases up to period
      - bare 'LEL EVT.YYYY' fragments
      - any remaining sentence still containing 'LEL' (catch-all)

    NARRATION FIDELITY FIX (SAMAPTI B-NAR-PH, P2 :211 re-derived — see
    tests/test_nar_ph_l4_anchors.py). The catch-all used to be
    `[^.]*\\bLEL\\b[^.]*(?:\\.|$)`, which treats ANY bare '.' as a sentence
    end — including periods inside a mid-sentence identifier like
    'PATTERN.ACROPHOBIA.01'. Live production catalog data hit exactly this:
    ANC.HLTH.2026.01's note reads "...Active LEL chronic patterns: headaches,
    acrophobia (PATTERN.ACROPHOBIA.01)." — the old regex stopped at the first
    period inside "PATTERN.ACROPHOBIA", leaking "ACROPHOBIA.01)." (private
    health information, sourced from LEL) into the served notes field. This
    was a live C2-002 privacy violation in the very function meant to
    prevent it, not merely a cosmetic residue.

    Fixed by splitting on REAL sentence boundaries only — a '.'/'!'/'?'
    followed by whitespace or end-of-string, never a bare mid-token period —
    then dropping any whole sentence that still contains 'LEL'. A trailing
    dangling-space artifact left by the parenthetical strip (e.g.
    "...native's US move ." from ANC.CAREER.2027.01, the original :211
    pointer) is also tidied.
    """
    if not text:
        return text
    # Strip '(LEL EVT...)' parenthetical blocks
    cleaned = re.sub(r'\(LEL\s+EVT[^)]*\)', '', text, flags=re.IGNORECASE)
    # Strip 'per LEL...' up to period
    cleaned = re.sub(r'\bper LEL\b[^.]*\.?', '', cleaned, flags=re.IGNORECASE)
    # Strip bare 'LEL EVT.XXXX' fragments not already caught
    cleaned = re.sub(r'\bLEL\s+EVT\.[^\s,;)]+', '', cleaned, flags=re.IGNORECASE)
    # Catch-all: drop any WHOLE SENTENCE that still contains 'LEL'. Sentence
    # boundary = a '.'/'!'/'?' followed by whitespace (or end of string) —
    # NOT every bare period, so a mid-sentence identifier cannot fool this
    # into truncating before the leak is fully removed.
    sentences = re.split(r'(?<=[.!?])\s+', cleaned)
    cleaned = ' '.join(s for s in sentences if 'lel' not in s.lower())
    # Tidy a dangling space-before-punctuation artifact the parenthetical
    # strip can leave behind (e.g. "...move ." → "...move.").
    cleaned = re.sub(r'\s+([.,;:])', r'\1', cleaned)
    # Collapse multiple spaces
    return re.sub(r'  +', ' ', cleaned).strip()


# ── Constants ─────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = os.environ.get(
    "NATIVE_CHART_ID", "482012f1-710e-4a25-994a-93821f5871aa"
)

SOURCE_CITATION = (
    "FORENSIC v8.0 §5.1 (Vimshottari) §22 (Sade Sati) (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md); "
    "MSR_v5_0.md SIG.* (573-signal ensemble); "
    "LEL_v1_2.md (57 life events); "
    "l3_convergence.py (23 convergence windows); "
    "l3_obstruction.py (17 obstruction entries)"
)

VOLUME_FLOOR = 20  # minimum anchors over 2026-2040

VALID_DOMAINS = frozenset({
    "career", "relationship", "financial", "spiritual", "health", "transition"
})

# ── Anchor catalog: 24 anchors across 2026-2040 ──────────────────────────────
# All anchors grounded in FORENSIC §5.1 dasha schedule + MSR signals.
# Confidence ceiling: 0.80 (hard limit — no anchor claims certainty).

ANCHOR_CATALOG: list[dict[str, Any]] = [

    # ═══════════════════════════════════════════════════════════════════════════
    # DOMAIN: CAREER  (Mercury MD = analytical/technical lord in own sign/exalt)
    # Mercury rules Gemini (3H) and Virgo (6H from Aries Lagna)
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "anchor_id": "ANC.CAREER.2026.01",
        "dasha_period": {
            "md": "Mercury", "ad": "Saturn",
            "start": "2024-12-12", "end": "2027-08-21",
        },
        "event_type": "Structured career authority elevation",
        "direction": "elevated",
        "signal_basis": [
            "SIG.MSR.018",   # Mercury 10L transit activation
            "SIG.MSR.042",   # Saturn discipline-builder in MD lord's period
            "CVG.003",       # Career-peak convergence 2024-2027 window
        ],
        "kala_window": {
            "start": "2026-01-01", "end": "2026-12-31",
            "convergence_type": "career_peak",
            "source_obs_id": None,
        },
        "falsifier": (
            "If no formal authority upgrade (title change, role expansion, "
            "new organizational scope, or significant client/contract uplift) "
            "occurs between 2026-01-01 and 2026-12-31, this anchor is falsified."
        ),
        "confidence": 0.72,
        "domain": "career",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "Mercury-Saturn AD = disciplined intellectual execution. Saturn disposits "
            "Aquarius Moon (H11) — gains through structured effort. Jupiter exalted "
            "in Cancer H4 aspects natal Moon and 7H (partnerships) — expansion support."
        ),
    },

    {
        "anchor_id": "ANC.CAREER.2026.02",
        "dasha_period": {
            "md": "Mercury", "ad": "Saturn",
            "start": "2024-12-12", "end": "2027-08-21",
        },
        "event_type": "AI/technology leadership visibility",
        "direction": "elevated",
        "signal_basis": [
            "SIG.MSR.019",   # Mercury in Makara (10H) — career-house emphasis
            "SIG.MSR.055",   # Rahu conjunct Mercury in natal chart — tech amplification
        ],
        "kala_window": {
            "start": "2026-03-01", "end": "2026-09-30",
            "convergence_type": "career_peak",
            "source_obs_id": None,
        },
        "falsifier": (
            "If native does not publish, present, lead, or receive recognition for "
            "a technology/AI initiative between 2026-03-01 and 2026-09-30, falsified."
        ),
        "confidence": 0.61,
        "domain": "career",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "Rahu-Mercury natal conjunction (SIG.MSR.055) creates strong amplification "
            "of Mercury-domain themes. 2-signal basis only → capped at 0.65."
        ),
    },

    {
        "anchor_id": "ANC.CAREER.2027.01",
        "dasha_period": {
            "md": "Mercury", "ad": "Saturn",
            "start": "2024-12-12", "end": "2027-08-21",
        },
        "event_type": "Mahadasha transition — Mercury to Ketu: regime discontinuity",
        "direction": "suppressed",
        "signal_basis": [
            "SIG.MSR.101",   # Mahadasha change = karmic reset
            "SIG.MSR.102",   # Ketu MD = detachment from Mercury-domain (commerce/tech)
            "CVG.018",       # Regime-discontinuity Mercury-to-Ketu convergence
        ],
        "kala_window": {
            "start": "2027-06-01", "end": "2027-10-31",
            "convergence_type": "life_transition_preparatory",
            "source_obs_id": None,
        },
        "falsifier": (
            "If native shows no career disruption, role change, or significant "
            "strategic pivot within 6 months of 2027-08-21 (Ketu MD start), falsified."
        ),
        "confidence": 0.75,
        "domain": "career",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "Every Mahadasha change produces a perceptible discontinuity within ±6 months. "
            "Mercury-to-Ketu is among the sharpest regime changes: Mercury = analytical/commercial, "
            "Ketu = withdrawal/moksha. Historically: Saturn-to-Mercury MD in 2010 corresponded "
            "to native's US move (LEL EVT.2019 approximate; exact date in LEL gap register)."
        ),
    },

    {
        "anchor_id": "ANC.CAREER.2029.01",
        "dasha_period": {
            "md": "Ketu", "ad": "Venus",
            "start": "2028-01-18", "end": "2029-03-18",
        },
        "event_type": "Creative/consulting career emergence under Ketu-Venus",
        "direction": "elevated",
        "signal_basis": [
            "SIG.MSR.078",   # Venus 7H lord (from natal chart) — partnership-career axis
            "SIG.MSR.079",   # Ketu in 9H (Sagittarius from Aries Lagna) — philosophical expansion
        ],
        "kala_window": {
            "start": "2028-04-01", "end": "2029-01-31",
            "convergence_type": "spiritual_peak",
            "source_obs_id": None,
        },
        "falsifier": (
            "If native does not initiate a new creative/consulting/independent work "
            "arrangement between 2028-04-01 and 2029-01-31, falsified."
        ),
        "confidence": 0.58,
        "domain": "career",
        "source_citation": SOURCE_CITATION,
        "notes": "2-signal basis, moderate confidence only.",
    },

    {
        "anchor_id": "ANC.CAREER.2032.01",
        "dasha_period": {
            "md": "Ketu", "ad": "Jupiter",
            "start": "2031-08-09", "end": "2032-07-15",
        },
        "event_type": "Philosophical teaching or wisdom-transmission career phase",
        "direction": "elevated",
        "signal_basis": [
            "SIG.MSR.082",   # Jupiter exalted Cancer natal — wisdom/guru nature
            "SIG.MSR.083",   # Ketu-Jupiter AD = spiritual-intellectual peak
            "CVG.021",       # Spiritual peak convergence
        ],
        "kala_window": {
            "start": "2031-08-09", "end": "2032-07-15",
            "convergence_type": "spiritual_peak",
            "source_obs_id": None,
        },
        "falsifier": (
            "If native shows no teaching, mentoring, publishing, or philosophical "
            "leadership activity between 2031-08-09 and 2032-07-15, falsified."
        ),
        "confidence": 0.68,
        "domain": "career",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "Ketu-Jupiter AD is the highest spiritual/philosophical period of the Ketu "
            "MD. Ketu MD = moksha orientation; Jupiter = guru. 3-signal basis, no "
            "kala obstruction → 0.68."
        ),
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # DOMAIN: RELATIONSHIP
    # Sade Sati Setting Phase (Saturn Pisces, 2nd from Moon Aquarius) active
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "anchor_id": "ANC.REL.2026.01",
        "dasha_period": {
            "md": "Mercury", "ad": "Saturn",
            "start": "2024-12-12", "end": "2027-08-21",
        },
        "event_type": "Marital/partnership tension peaks (Sade Sati setting + Saturn AD)",
        "direction": "suppressed",
        "signal_basis": [
            "SIG.MSR.011",   # Venus weakened in natal chart (Venus 12H from Lagna)
            "SIG.MSR.022",   # Sade Sati cycle 2 setting phase — relationship strain
            "SIG.MSR.023",   # Saturn AD during Sade Sati = compounded relational weight
            "CVG.009",       # Obstruction convergence OBS.SS.C2.SETTING
        ],
        "kala_window": {
            "start": "2026-01-01", "end": "2027-03-31",
            "convergence_type": "health_attention",
            "source_obs_id": "OBS.SS.C2.SETTING",
        },
        "falsifier": (
            "If native's primary relationship (current legal spouse or new significant "
            "partnership) shows no significant legal, emotional, or structural change "
            "between 2026-01-01 and 2027-03-31, this anchor is falsified."
        ),
        "confidence": 0.76,
        "domain": "relationship",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "Sade Sati Setting Phase + Mercury-Saturn AD = heaviest relational load of this "
            "MD. Native already experiencing separation strain per LEL. 4-signal basis → 0.76. "
            "Saturn as AD lord during Sade Sati creates a double-malefic compound for Moon-ruled "
            "areas (emotions, mother, public relationships)."
        ),
    },

    {
        "anchor_id": "ANC.REL.2026.02",
        "dasha_period": {
            "md": "Mercury", "ad": "Saturn",
            "start": "2024-12-12", "end": "2027-08-21",
        },
        "event_type": "Legal resolution of separation/divorce proceedings",
        "direction": "elevated",
        "signal_basis": [
            "SIG.MSR.044",   # Saturn as karmic finalizer — brings difficult matters to conclusion
            "SIG.MSR.022",   # Sade Sati setting = release after peak
        ],
        "kala_window": {
            "start": "2026-06-01", "end": "2027-08-21",
            "convergence_type": "life_transition_preparatory",
            "source_obs_id": "OBS.SS.C2.SETTING",
        },
        "falsifier": (
            "If no legal documentation (petition, decree, separation agreement) "
            "related to the marriage is filed between 2026-06-01 and 2027-08-21, falsified."
        ),
        "confidence": 0.62,
        "domain": "relationship",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "Saturn finalizes Saturnine themes (delays, separations, legal matters). "
            "Sade Sati setting phase is the karmic release window. 2-signal basis → capped 0.65."
        ),
    },

    {
        "anchor_id": "ANC.REL.2028.01",
        "dasha_period": {
            "md": "Ketu", "ad": "Venus",
            "start": "2028-01-18", "end": "2029-03-18",
        },
        "event_type": "New relational opening after Sade Sati release (Ketu-Venus AD)",
        "direction": "elevated",
        "signal_basis": [
            "SIG.MSR.078",   # Venus 7H lord — partnership activation
            "SIG.MSR.031",   # Post-Sade Sati release (Saturn leaves Pisces ~2025-03)
        ],
        "kala_window": {
            "start": "2028-04-01", "end": "2029-01-31",
            "convergence_type": "relationship",
            "source_obs_id": None,
        },
        "falsifier": (
            "If native does not form a significant new romantic, creative, or "
            "business partnership between 2028-04-01 and 2029-01-31, falsified."
        ),
        "confidence": 0.55,
        "domain": "relationship",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "Post-Sade Sati (Saturn left Pisces ~Mar 2025) + Ketu-Venus AD creates "
            "a window. Venus = Darakaraka (spouse-significator) in Ketu MD. "
            "Conservative confidence (0.55) — Ketu MD is fundamentally renunciatory."
        ),
    },

    {
        "anchor_id": "ANC.REL.2030.01",
        "dasha_period": {
            "md": "Ketu", "ad": "Moon",
            "start": "2029-07-24", "end": "2030-02-24",
        },
        "event_type": "Emotional healing and reconnection with family/child",
        "direction": "elevated",
        "signal_basis": [
            "SIG.MSR.006",   # Moon AK (Atmakaraka) in H11 — emotional fulfillment
            "SIG.MSR.035",   # Ketu-Moon AD = deep emotional processing
        ],
        "kala_window": {
            "start": "2029-07-24", "end": "2030-02-24",
            "convergence_type": "relationship",
            "source_obs_id": None,
        },
        "falsifier": (
            "If native shows no significant improvement in family/child relationship "
            "or emotional resolution of prior partnership karma between "
            "2029-07-24 and 2030-02-24, falsified."
        ),
        "confidence": 0.58,
        "domain": "relationship",
        "source_citation": SOURCE_CITATION,
        "notes": "Moon Atmakaraka + Ketu-Moon AD = soul-level emotional theme.",
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # DOMAIN: FINANCIAL
    # Jupiter transit H2/H5/H11 = traditional wealth-house transits
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "anchor_id": "ANC.FIN.2026.01",
        "dasha_period": {
            "md": "Mercury", "ad": "Saturn",
            "start": "2024-12-12", "end": "2027-08-21",
        },
        "event_type": "Income growth through structured professional expansion",
        "direction": "elevated",
        "signal_basis": [
            "SIG.MSR.042",   # Saturn discipline-builder in career-financial axis
            "SIG.MSR.056",   # Jupiter exalted Cancer 4H — asset/property support
            "CVG.003",       # Career-peak convergence 2024-2027
        ],
        "kala_window": {
            "start": "2026-01-01", "end": "2026-12-31",
            "convergence_type": "career_peak",
            "source_obs_id": None,
        },
        "falsifier": (
            "If native's total compensation or primary income stream does not "
            "increase by at least 15% in the 2026 calendar year, falsified."
        ),
        "confidence": 0.65,
        "domain": "financial",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "Mercury MD = commerce/analytics lord. Saturn AD = disciplined wealth "
            "accumulation. Jupiter exalted in H4 = real-estate/asset-base support. "
            "3-signal basis → 0.65."
        ),
    },

    {
        "anchor_id": "ANC.FIN.2026.02",
        "dasha_period": {
            "md": "Mercury", "ad": "Saturn",
            "start": "2024-12-12", "end": "2027-08-21",
        },
        "event_type": "Property/real-estate consideration or transaction",
        "direction": "elevated",
        "signal_basis": [
            "SIG.MSR.056",   # Jupiter exalted H4 — home/property expansion
            "SIG.MSR.057",   # Saturn AD — structured long-term asset acquisition
        ],
        "kala_window": {
            "start": "2026-06-01", "end": "2027-06-30",
            "convergence_type": "career_peak",
            "source_obs_id": None,
        },
        "falsifier": (
            "If native does not make a property purchase, lease commitment, or "
            "significant real-estate decision between 2026-06-01 and 2027-06-30, falsified."
        ),
        "confidence": 0.58,
        "domain": "financial",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "Jupiter exalted in Cancer H4 (home, property, mother) is highly activated "
            "during Mercury-Saturn AD. 2-signal basis."
        ),
    },

    {
        "anchor_id": "ANC.FIN.2028.01",
        "dasha_period": {
            "md": "Ketu", "ad": "Ketu",
            "start": "2027-08-21", "end": "2028-01-18",
        },
        "event_type": "Financial simplification / asset liquidation phase",
        "direction": "suppressed",
        "signal_basis": [
            "SIG.MSR.097",   # Ketu MD = renunciation, detachment from material
            "SIG.MSR.098",   # Ketu-Ketu double AD = intensified Ketu themes
        ],
        "kala_window": {
            "start": "2027-08-21", "end": "2028-01-18",
            "convergence_type": "life_transition_preparatory",
            "source_obs_id": "OBS.MALDASH.KETU.KETU",
        },
        "falsifier": (
            "If native does not reduce financial complexity (sell assets, exit "
            "investments, simplify income streams) between 2027-08-21 and "
            "2028-01-18, this suppression anchor is falsified."
        ),
        "confidence": 0.64,
        "domain": "financial",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "Ketu-Ketu AD is the strongest Ketu-period expression. Classical teaching: "
            "Ketu MD native is often forced to give up material things involuntarily "
            "or chooses voluntary renunciation. 2-signal + obstruction → 0.64."
        ),
    },

    {
        "anchor_id": "ANC.FIN.2034.01",
        "dasha_period": {
            "md": "Venus", "ad": "Venus",
            "start": "2034-08-21", "end": "2037-12-21",
        },
        "event_type": "Venus MD financial renaissance — creativity monetized",
        "direction": "elevated",
        "signal_basis": [
            "SIG.MSR.010",   # Venus 7H lord from Lagna — partnership wealth
            "SIG.MSR.011",   # Venus in Aquarius — idealistic but connective
            "SIG.MSR.078",   # Venus-Venus double AD = peak Venus-period activation
            "CVG.022",       # Venus-MD career_peak convergence
        ],
        "kala_window": {
            "start": "2034-08-21", "end": "2036-12-31",
            "convergence_type": "career_peak",
            "source_obs_id": None,
        },
        "falsifier": (
            "If native's creative or consultative income does not materially expand "
            "within the first 24 months of Venus MD (by 2036-08-21), falsified."
        ),
        "confidence": 0.72,
        "domain": "financial",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "Venus MD is classically auspicious for wealth — Venus is the Darakaraka "
            "and 7H lord (Libra from Aries). Venus-Venus double AD at MD start is the "
            "peak activation. 4-signal basis → 0.72."
        ),
    },

    {
        "anchor_id": "ANC.FIN.2038.01",
        "dasha_period": {
            "md": "Venus", "ad": "Sun",
            "start": "2037-12-21", "end": "2038-12-21",
        },
        "event_type": "Public recognition + income elevation in Sun-themed domains",
        "direction": "elevated",
        "signal_basis": [
            "SIG.MSR.003",   # Sun H10 lord (Capricorn) aspects career
            "SIG.MSR.012",   # Sun-Mars combination — decisive authority
        ],
        "kala_window": {
            "start": "2037-12-21", "end": "2038-12-21",
            "convergence_type": "career_peak",
            "source_obs_id": None,
        },
        "falsifier": (
            "If native does not receive a public-facing authority elevation or "
            "significant recognition between 2037-12-21 and 2038-12-21, falsified."
        ),
        "confidence": 0.56,
        "domain": "financial",
        "source_citation": SOURCE_CITATION,
        "notes": "2-signal basis only — moderate confidence.",
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # DOMAIN: SPIRITUAL / LEARNING
    # Ketu sub-periods + Jupiter H4 exaltation
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "anchor_id": "ANC.SPR.2026.01",
        "dasha_period": {
            "md": "Mercury", "ad": "Saturn",
            "start": "2024-12-12", "end": "2027-08-21",
        },
        "event_type": "Deepened astrological/philosophical study (Jupiter H4 exalt)",
        "direction": "elevated",
        "signal_basis": [
            "SIG.MSR.056",   # Jupiter exalted H4 — home-based wisdom tradition
            "SIG.MSR.060",   # Jupiter aspects 12H — moksha and foreign learning
            "CVG.010",       # Spiritual_peak convergence 2025-2027
        ],
        "kala_window": {
            "start": "2025-10-01", "end": "2027-02-28",
            "convergence_type": "spiritual_peak",
            "source_obs_id": None,
        },
        "falsifier": (
            "If native does not begin or significantly deepen a formal "
            "philosophical/spiritual practice (meditation, study, teaching, "
            "writing) between 2025-10-01 and 2027-02-28, falsified."
        ),
        "confidence": 0.68,
        "domain": "spiritual",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "Jupiter exalted in Cancer H4 is the dominant benefic of this period. "
            "H4 = grihastha ashrama + home learning. Mercury MD + Jupiter aspect = "
            "intellectual spiritual inquiry. 3-signal basis → 0.68."
        ),
    },

    {
        "anchor_id": "ANC.SPR.2027.01",
        "dasha_period": {
            "md": "Ketu", "ad": "Ketu",
            "start": "2027-08-21", "end": "2028-01-18",
        },
        "event_type": "Renunciation impulse or formal spiritual commitment",
        "direction": "elevated",
        "signal_basis": [
            "SIG.MSR.090",   # Ketu 9H (Sagittarius) — dharmic withdrawal
            "SIG.MSR.091",   # Ketu-Ketu double AD = peak Ketu expression
            "CVG.017",       # Spiritual_peak convergence Ketu-Ketu AD
        ],
        "kala_window": {
            "start": "2027-08-21", "end": "2028-01-18",
            "convergence_type": "spiritual_peak",
            "source_obs_id": "OBS.MALDASH.KETU.KETU",
        },
        "falsifier": (
            "If native shows no deepened spiritual commitment, retreat, "
            "or formal renunciation gesture between 2027-08-21 and "
            "2028-01-18, falsified."
        ),
        "confidence": 0.70,
        "domain": "spiritual",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "Ketu-Ketu double AD at MD start = strongest possible Ketu activation. "
            "3-signal + kala convergence → 0.70. Ketu in H9 (Sagittarius from Aries) "
            "gives dharmic philosophical nature + past-life guru connection."
        ),
    },

    {
        "anchor_id": "ANC.SPR.2030.01",
        "dasha_period": {
            "md": "Ketu", "ad": "Rahu",
            "start": "2030-07-21", "end": "2031-08-09",
        },
        "event_type": "Karmic confrontation — Rahu-Ketu axis activated",
        "direction": "suppressed",
        "signal_basis": [
            "SIG.MSR.053",   # Rahu-Ketu axis in Gemini-Sagittarius — communication/dharma tension
            "SIG.MSR.095",   # Ketu-Rahu AD = churning of material vs. spiritual desires
        ],
        "kala_window": {
            "start": "2030-07-21", "end": "2031-08-09",
            "convergence_type": "health_attention",
            "source_obs_id": "OBS.MALDASH.KETU.RAHU",
        },
        "falsifier": (
            "If native does not experience a significant identity/direction crisis "
            "or forced karmic confrontation between 2030-07-21 and 2031-08-09, falsified."
        ),
        "confidence": 0.65,
        "domain": "spiritual",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "Ketu-Rahu AD is among the most churning periods — Rahu's material ambition "
            "versus Ketu's spiritual withdrawal creates internal tension. Obstruction "
            "OBS.MALDASH.KETU.RAHU is a known adversity window. 2-signal + kala → 0.65."
        ),
    },

    {
        "anchor_id": "ANC.SPR.2031.01",
        "dasha_period": {
            "md": "Ketu", "ad": "Jupiter",
            "start": "2031-08-09", "end": "2032-07-15",
        },
        "event_type": "Guru encounter or spiritual teaching transmission",
        "direction": "elevated",
        "signal_basis": [
            "SIG.MSR.082",   # Jupiter exalted Cancer — guru grace
            "SIG.MSR.083",   # Ketu-Jupiter AD = dharmic wisdom peak
            "SIG.MSR.089",   # Jupiter aspects 9H — blessings of dharma house
            "CVG.021",       # Spiritual-peak convergence 2031-2032
        ],
        "kala_window": {
            "start": "2031-08-09", "end": "2032-07-15",
            "convergence_type": "spiritual_peak",
            "source_obs_id": None,
        },
        "falsifier": (
            "If native does not encounter a transformative teacher, initiation, "
            "or spiritual teaching event between 2031-08-09 and 2032-07-15, falsified."
        ),
        "confidence": 0.74,
        "domain": "spiritual",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "4-signal + kala convergence → 0.74. Jupiter exalted in Cancer H4 "
            "has been the dominant benefic since 2024-25. In Ketu-Jupiter AD, "
            "the guru archetype is highly activated. This is the highest spiritual "
            "window of the entire 2026-2040 arc."
        ),
    },

    {
        "anchor_id": "ANC.SPR.2033.01",
        "dasha_period": {
            "md": "Ketu", "ad": "Mercury",
            "start": "2033-08-24", "end": "2034-08-21",
        },
        "event_type": "Spiritual writing or teaching crystallized into form",
        "direction": "elevated",
        "signal_basis": [
            "SIG.MSR.018",   # Mercury — analytical articulation
            "SIG.MSR.097",   # Ketu MD — spiritual orientation
        ],
        "kala_window": {
            "start": "2033-08-24", "end": "2034-08-21",
            "convergence_type": "spiritual_peak",
            "source_obs_id": None,
        },
        "falsifier": (
            "If native does not produce a significant written, digital, or teaching "
            "artifact in a dharmic/philosophical domain between 2033-08-24 and "
            "2034-08-21, falsified."
        ),
        "confidence": 0.58,
        "domain": "spiritual",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "Ketu-Mercury AD = spiritual wisdom expressed through Mercury's medium "
            "(writing, speech, analysis). 2-signal basis."
        ),
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # DOMAIN: HEALTH ATTENTION
    # Sade Sati obstructions from l3 + malefic AD periods
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "anchor_id": "ANC.HLTH.2026.01",
        "dasha_period": {
            "md": "Mercury", "ad": "Saturn",
            "start": "2024-12-12", "end": "2027-08-21",
        },
        "event_type": "Stress-related health attention (Sade Sati Setting + Saturn AD)",
        "direction": "suppressed",
        "signal_basis": [
            "SIG.MSR.022",   # Sade Sati cycle 2 setting — physical/mental load on Moon
            "SIG.MSR.043",   # Saturn as 6H significator — health burdens
            "CVG.011",       # Obstruction convergence: Sade Sati Setting + Saturn AD
        ],
        "kala_window": {
            "start": "2026-01-01", "end": "2027-03-31",
            "convergence_type": "health_attention",
            "source_obs_id": "OBS.SS.C2.SETTING",
        },
        "falsifier": (
            "If native experiences no significant health disruption (requiring medical "
            "attention, work absence ≥2 weeks, or lifestyle modification) between "
            "2026-01-01 and 2027-03-31, falsified."
        ),
        "confidence": 0.65,
        "domain": "health",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "Sade Sati Setting phase classically correlates with health issues related "
            "to Moon-ruled areas: mental health, chest, digestion, sleep. "
            "3-signal + kala → 0.65. Active LEL chronic patterns: headaches, "
            "acrophobia (PATTERN.ACROPHOBIA.01)."
        ),
    },

    {
        "anchor_id": "ANC.HLTH.2028.01",
        "dasha_period": {
            "md": "Ketu", "ad": "Ketu",
            "start": "2027-08-21", "end": "2028-01-18",
        },
        "event_type": "Physiological purification / detox period",
        "direction": "suppressed",
        "signal_basis": [
            "SIG.MSR.098",   # Ketu-Ketu double AD — systemic purification
            "SIG.MSR.099",   # Ketu in H9 — 12H from H10 (foreign health intervention?)
        ],
        "kala_window": {
            "start": "2027-08-21", "end": "2028-01-18",
            "convergence_type": "health_attention",
            "source_obs_id": "OBS.MALDASH.KETU.KETU",
        },
        "falsifier": (
            "If native does not undertake a significant health/lifestyle reset "
            "(dietary, medical, or therapeutic) between 2027-08-21 and 2028-01-18, falsified."
        ),
        "confidence": 0.55,
        "domain": "health",
        "source_citation": SOURCE_CITATION,
        "notes": "2-signal + kala. Ketu MD is commonly associated with unexpected health events.",
    },

    {
        "anchor_id": "ANC.HLTH.2032.01",
        "dasha_period": {
            "md": "Ketu", "ad": "Saturn",
            "start": "2032-07-15", "end": "2033-08-24",
        },
        "event_type": "Structural health consideration (joints, bones, chronic pattern)",
        "direction": "suppressed",
        "signal_basis": [
            "SIG.MSR.040",   # Saturn — chronic/structural health (bones, joints, Vata)
            "SIG.MSR.093",   # Ketu-Saturn AD = obstructed Vata + chronic suppression
        ],
        "kala_window": {
            "start": "2032-07-15", "end": "2033-08-24",
            "convergence_type": "health_attention",
            "source_obs_id": "OBS.MALDASH.KETU.SAT",
        },
        "falsifier": (
            "If native does not experience a bone/joint/chronic condition requiring "
            "medical attention between 2032-07-15 and 2033-08-24, falsified."
        ),
        "confidence": 0.60,
        "domain": "health",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "Ketu-Saturn AD is an obstruction window (OBS.MALDASH.KETU.SAT). "
            "Saturn's chronic nature + Ketu's 8H (longevity/transformation) aspect "
            "creates physiological slowdown. 2-signal + kala → 0.60."
        ),
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # DOMAIN: TRANSITION (life-regime discontinuity anchors)
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "anchor_id": "ANC.TRANS.2027.01",
        "dasha_period": {
            "md": "Ketu", "ad": "Ketu",
            "start": "2027-08-21", "end": "2028-01-18",
        },
        "event_type": "Geographic relocation or major lifestyle reorganization",
        "direction": "elevated",
        "signal_basis": [
            "SIG.MSR.101",   # Mahadasha change — always produces regime discontinuity
            "SIG.MSR.102",   # Ketu MD = detachment from current environment
            "SIG.MSR.060",   # Jupiter aspects 12H — foreign horizons
        ],
        "kala_window": {
            "start": "2027-06-01", "end": "2028-06-30",
            "convergence_type": "life_transition_preparatory",
            "source_obs_id": "OBS.MALDASH.KETU.KETU",
        },
        "falsifier": (
            "If native does not relocate (city or country change), restructure "
            "living arrangements, or make a major lifestyle reorganization "
            "within 12 months of 2027-08-21, falsified."
        ),
        "confidence": 0.67,
        "domain": "transition",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "MD-change-to-Ketu is among the most disruptive transitions. Ketu = "
            "sudden, decisive, karmic. Native's history: Mercury MD start (2010) "
            "corresponded to US move. 3-signal + kala → 0.67. Historical precedent "
            "of relocation at MD change strongly supports this anchor."
        ),
    },

    {
        "anchor_id": "ANC.TRANS.2034.01",
        "dasha_period": {
            "md": "Venus", "ad": "Venus",
            "start": "2034-08-21", "end": "2037-12-21",
        },
        "event_type": "Venus MD renaissance: creative professional reinvention",
        "direction": "elevated",
        "signal_basis": [
            "SIG.MSR.010",   # Venus 7H lord — partnerships activated
            "SIG.MSR.078",   # Venus Darakaraka — spouse/partner energy reactivated
            "SIG.MSR.011",   # Venus in Aquarius — group/network creativity
            "CVG.022",       # Venus MD career-peak convergence
        ],
        "kala_window": {
            "start": "2034-08-21", "end": "2037-12-21",
            "convergence_type": "career_peak",
            "source_obs_id": None,
        },
        "falsifier": (
            "If native's work domain (nature of work, partnerships, creative output) "
            "does not significantly transform between 2034-08-21 and 2037-12-21, "
            "this transition anchor is falsified."
        ),
        "confidence": 0.70,
        "domain": "transition",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "Venus MD is the 20-year culmination period after Ketu's renunciation. "
            "Classical: Ketu MD people often experience their most materially "
            "abundant period in Venus MD (compensatory). 4-signal → 0.70."
        ),
    },

    {
        "anchor_id": "ANC.TRANS.2040.01",
        "dasha_period": {
            "md": "Venus", "ad": "Moon",
            "start": "2038-12-21", "end": "2040-08-21",
        },
        "event_type": "Emotional integration and public-facing maturity",
        "direction": "elevated",
        "signal_basis": [
            "SIG.MSR.006",   # Moon AK (Atmakaraka) — soul integration
            "SIG.MSR.010",   # Venus 7H lord — public partnerships
        ],
        "kala_window": {
            "start": "2038-12-21", "end": "2040-08-21",
            "convergence_type": "career_peak",
            "source_obs_id": None,
        },
        "falsifier": (
            "If native does not achieve a stable, publicly visible relational or "
            "professional configuration between 2038-12-21 and 2040-08-21, falsified."
        ),
        "confidence": 0.55,
        "domain": "transition",
        "source_citation": SOURCE_CITATION,
        "notes": (
            "Horizon endpoint of the 2026-2040 arc. Moon AK in Venus MD = emotional "
            "soul work brought to fruition. 2-signal basis, distant horizon → "
            "conservative 0.55."
        ),
    },
]

# Validate volume floor at module load
assert len(ANCHOR_CATALOG) >= VOLUME_FLOOR, (
    f"Volume floor breach: {len(ANCHOR_CATALOG)} anchors < {VOLUME_FLOOR} required"
)


# ── Core tool function ────────────────────────────────────────────────────────

def query_phala_anchors(
    chart_id: str,
    date_range: dict[str, str],
    min_confidence: Optional[float] = None,
    domain: Optional[str] = None,
) -> dict[str, Any]:
    """
    query_phala_anchors — retrieve calibrated event anchors for 2026-2040.

    This is a static-catalog tool: anchors are pre-computed from FORENSIC L1
    data + MSR signals + l3 kala convergence/obstruction windows. No DB query
    required; the catalog is embedded in this module and shared across all
    chart_ids (anchors are native-specific — only chart_id=NATIVE_CHART_ID
    returns results; others return empty).

    Args:
        chart_id:       Chart UUID. Only native chart returns results.
        date_range:     {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
        min_confidence: Filter threshold [0.0, 1.0]. Default 0.0.
        domain:         Optional domain filter:
                        career | relationship | financial | spiritual | health | transition

    Returns:
        {
            "ok": True,
            "chart_id": str,
            "query_window": {"start": str, "end": str},
            "anchors": [...],
            "anchor_count": int,
            "volume_floor_met": bool,
            "confidence_distribution": {...},
            "provenance_envelope": {...}
        }
    """
    # Validate domain
    if domain and domain not in VALID_DOMAINS:
        raise ValueError(
            f"Invalid domain '{domain}'. Valid: {sorted(VALID_DOMAINS)}"
        )

    # chart_id guard: this catalog is native-specific.
    # Non-native chart_ids receive an explicit empty response (not the native's data).
    if chart_id != NATIVE_CHART_ID:
        return {
            "ok": True,
            "chart_id": chart_id,
            "query_window": {
                "start": date_range.get("start", ""),
                "end": date_range.get("end", ""),
            },
            "anchors": [],
            "anchor_count": 0,
            "volume_floor_met": len(ANCHOR_CATALOG) >= VOLUME_FLOOR,
            "confidence_distribution": {"high_ge_0.70": 0, "mid_0.55_to_0.70": 0, "low_lt_0.55": 0},
            "provenance_envelope": {
                "source": "phala.anchors.v2",
                "note": "chart_id is not the native chart — no anchors available",
            },
        }

    # Parse date range
    try:
        range_start = date.fromisoformat(date_range["start"])
        range_end = date.fromisoformat(date_range["end"])
    except (KeyError, ValueError) as exc:
        raise ValueError(f"date_range must have 'start'/'end' ISO dates: {exc}") from exc

    if range_start > range_end:
        raise ValueError(f"date_range start must not be after end")

    effective_min_conf = min_confidence if min_confidence is not None else 0.0
    if not (0.0 <= effective_min_conf <= 1.0):
        raise ValueError(f"min_confidence must be in [0.0, 1.0], got {effective_min_conf}")

    # Filter catalog
    filtered: list[dict[str, Any]] = []
    for anchor in ANCHOR_CATALOG:
        # Domain filter
        if domain and anchor.get("domain") != domain:
            continue
        # Confidence filter
        if anchor["confidence"] < effective_min_conf:
            continue
        # Date range overlap with kala_window
        kw = anchor["kala_window"]
        try:
            kw_start = date.fromisoformat(kw["start"])
            kw_end = date.fromisoformat(kw["end"])
        except (KeyError, ValueError):
            # Fallback to dasha_period dates
            dp = anchor["dasha_period"]
            kw_start = date.fromisoformat(dp["start"])
            kw_end = date.fromisoformat(dp["end"])

        # Overlap: kw_start <= range_end AND kw_end >= range_start
        if kw_start <= range_end and kw_end >= range_start:
            filtered.append(anchor)

    # Build response anchors (serialise dates as strings)
    anchors_out = []
    for a in filtered:
        anchors_out.append({
            "anchor_id": a["anchor_id"],
            "dasha_period": a["dasha_period"],
            "event_type": a["event_type"],
            "direction": a["direction"],
            "domain": a["domain"],
            "signal_basis": a["signal_basis"],
            "kala_window": a["kala_window"],
            "falsifier": a["falsifier"],
            "confidence": a["confidence"],
            "source_citation": a["source_citation"],
            "notes": strip_lel_citations(a.get("notes", "")),
        })

    # Confidence distribution
    high = sum(1 for a in filtered if a["confidence"] >= 0.70)
    mid = sum(1 for a in filtered if 0.55 <= a["confidence"] < 0.70)
    low = sum(1 for a in filtered if a["confidence"] < 0.55)

    return {
        "ok": True,
        "chart_id": chart_id,
        "query_window": {"start": range_start.isoformat(), "end": range_end.isoformat()},
        "anchors": anchors_out,
        "anchor_count": len(anchors_out),
        "volume_floor_met": len(ANCHOR_CATALOG) >= VOLUME_FLOOR,
        "confidence_distribution": {
            "high_ge_0.70": high,
            "mid_0.55_to_0.70": mid,
            "low_lt_0.55": low,
        },
        "provenance_envelope": {
            "source": "phala.anchors.v2",
            "asset": "PH-4-1-V2",
            "catalog_size": len(ANCHOR_CATALOG),
            "volume_floor": VOLUME_FLOOR,
            "algorithm": "FORENSIC §5.1 dasha schedule × MSR signal ensemble × l3 kala windows",
            "confidence_ceiling": 0.80,
            "calibration_rule": (
                "Single signal ≤0.55; 2 signals ≤0.65; "
                "3 signals ≤0.72; 3+kala ≤0.78; ≥4+kala ≤0.80"
            ),
            "all_falsifiers_present": all(bool(a.get("falsifier")) for a in filtered),
            "b3_citation_compliant": all(bool(a.get("source_citation")) for a in filtered),
            "queried_at": datetime.now(tz=timezone.utc).isoformat(),
            "l1_ground_truth": "FORENSIC v8.0 §5.1 §22 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md)",
        },
    }


# ── Acceptance gate ───────────────────────────────────────────────────────────

def run_acceptance_gate(chart_id: str) -> dict[str, Any]:
    """
    PH-4-1-V2 acceptance gate.

    AC1: catalog_size >= 20 (volume floor)
    AC2: all anchors have non-empty falsifier
    AC3: all confidence values in [0.0, 0.80] (ceiling enforced)
    AC4: query_phala_anchors returns ≥20 anchors for 2026-2040
    AC5: domain filter works (at least 1 anchor per domain)
    """
    checks: list[dict[str, Any]] = []

    # AC1: volume floor
    checks.append({
        "id": "AC1",
        "desc": "catalog_size >= 20",
        "passed": len(ANCHOR_CATALOG) >= 20,
        "value": len(ANCHOR_CATALOG),
    })

    # AC2: all falsifiers non-empty
    missing_falsifiers = [a["anchor_id"] for a in ANCHOR_CATALOG if not a.get("falsifier")]
    checks.append({
        "id": "AC2",
        "desc": "All anchors have non-empty falsifier",
        "passed": len(missing_falsifiers) == 0,
        "missing": missing_falsifiers,
    })

    # AC3: confidence in [0.0, 0.80]
    out_of_range = [
        (a["anchor_id"], a["confidence"])
        for a in ANCHOR_CATALOG
        if not (0.0 <= a["confidence"] <= 0.80)
    ]
    checks.append({
        "id": "AC3",
        "desc": "All confidence values in [0.0, 0.80]",
        "passed": len(out_of_range) == 0,
        "out_of_range": out_of_range,
    })

    # AC4: query returns ≥20 for 2026-2040
    try:
        result = query_phala_anchors(
            chart_id=chart_id,
            date_range={"start": "2026-01-01", "end": "2040-12-31"},
        )
        checks.append({
            "id": "AC4",
            "desc": "query_phala_anchors returns ≥20 anchors for 2026-2040",
            "passed": result["anchor_count"] >= 20,
            "value": result["anchor_count"],
        })
    except Exception as exc:
        checks.append({"id": "AC4", "desc": "query 2026-2040", "passed": False, "error": str(exc)})

    # AC5: domain filter
    domain_ok = True
    domain_counts = {}
    for d in VALID_DOMAINS:
        result = query_phala_anchors(
            chart_id=chart_id,
            date_range={"start": "2026-01-01", "end": "2040-12-31"},
            domain=d,
        )
        domain_counts[d] = result["anchor_count"]
        if result["anchor_count"] == 0:
            domain_ok = False
    checks.append({
        "id": "AC5",
        "desc": "At least 1 anchor per domain over 2026-2040",
        "passed": domain_ok,
        "domain_counts": domain_counts,
    })

    gate_passed = all(c["passed"] for c in checks)
    return {"chart_id": chart_id, "gate_passed": gate_passed, "checks": checks}


# ── FastAPI models ────────────────────────────────────────────────────────────

class DateRange(BaseModel):
    start: str = Field(..., description="ISO date YYYY-MM-DD")
    end: str = Field(..., description="ISO date YYYY-MM-DD")


class PhalaAnchorsRequest(BaseModel):
    chart_id: str = Field(..., description="Chart UUID")
    date_range: DateRange
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    domain: Optional[str] = Field(
        None,
        description="career|relationship|financial|spiritual|health|transition"
    )


# ── FastAPI endpoints ─────────────────────────────────────────────────────────

@router.post("/phala/query_phala_anchors")
def api_query_phala_anchors(req: PhalaAnchorsRequest) -> dict[str, Any]:
    """
    PH-4-1-V2 query_phala_anchors tool.

    Returns calibrated 2026-2040 event anchors for the requested window.
    All anchors carry explicit falsifiers (Learning Layer rule #4) and
    source citations (B.3 mandate). Confidence ceiling: 0.80.
    """
    try:
        return query_phala_anchors(
            chart_id=req.chart_id,
            date_range={"start": req.date_range.start, "end": req.date_range.end},
            min_confidence=req.min_confidence,
            domain=req.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/phala/query_phala_anchors/gate/{chart_id}")
def api_acceptance_gate(chart_id: str) -> dict[str, Any]:
    """PH-4-1-V2 acceptance gate — AC1 through AC5."""
    return run_acceptance_gate(chart_id)
