#!/usr/bin/env python3
"""
M9-C-S1: Multi-School Analysis Runner
Executes all 7 Jyotish school engines across 5 domains for Abhisek's natal chart.
Produces 35 SchoolResult records + convergence per domain.
DB insertion and GCS upload deferred (proxy unavailable at M9-C-S1 execution context).

Usage:
    python run_multi_school_analysis.py [--output-dir <dir>] [--json-only]

Output:
    MULTI_SCHOOL_ANALYSIS_v1_0.md  (human-readable; default: 09_MULTI_SCHOOL_TRIANGULATION/)
    <school>_analysis.json × 7     (machine-readable; default: same dir)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import date
from typing import Any, Literal, TypedDict

# ---------------------------------------------------------------------------
# Type definitions (mirrors platform/src/lib/schools/types.ts)
# ---------------------------------------------------------------------------

Domain = Literal["CAREER", "HEALTH", "RELATIONSHIP", "SPIRITUAL", "PSYCHOLOGICAL"]
Direction = Literal["positive", "negative", "neutral"]
SchoolName = Literal["parashari", "jaimini", "tajika", "kp", "nadi", "bnn", "yogini"]
ConvergenceLevel = Literal["HIGH", "MEDIUM", "LOW"]

DOMAINS: list[str] = ["CAREER", "HEALTH", "RELATIONSHIP", "SPIRITUAL", "PSYCHOLOGICAL"]
SCHOOLS: list[str] = ["parashari", "jaimini", "tajika", "kp", "nadi", "bnn", "yogini"]


class SignalScore(TypedDict, total=False):
    signalId: str
    signalName: str
    score: float
    weight: float
    attributionRef: str


class SchoolResult(TypedDict):
    school: str
    domain: str
    domainScore: float
    direction: str
    topSignals: list[SignalScore]
    schoolVerdict: str
    signalCoverage: str
    pendingFlags: list[str]


# ---------------------------------------------------------------------------
# ABHISEK_CHART constant (mirrors types.ts ABHISEK_CHART)
# ---------------------------------------------------------------------------

ABHISEK_CHART = {
    "chartId": "abhisek_primary",
    "chartType": "natal",
    "ascendant": "capricorn",
    "moonSign": "virgo",
    "sunSign": "capricorn",
    "birthDate": "1984-02-05",
    "birthTime": "10:43",
    "birthPlace": "Bhubaneswar, Odisha, India",
    "planets": [
        {"planet": "sun",     "sign": "capricorn",  "house": 1,  "degree": 21.5, "isExalted": False},
        {"planet": "moon",    "sign": "virgo",      "house": 9,  "degree": 15.2, "isExalted": False},
        {"planet": "mars",    "sign": "aries",      "house": 4,  "degree": 8.7,  "isExalted": False},
        {"planet": "mercury", "sign": "capricorn",  "house": 1,  "degree": 14.3, "isExalted": False},
        {"planet": "jupiter", "sign": "sagittarius","house": 12, "degree": 6.1,  "isExalted": False},
        {"planet": "venus",   "sign": "aquarius",   "house": 2,  "degree": 19.4, "isExalted": False},
        {"planet": "saturn",  "sign": "libra",      "house": 10, "degree": 12.8, "isExalted": True},
        {"planet": "rahu",    "sign": "gemini",      "house": 6,  "degree": 22.1, "isExalted": False},
        {"planet": "ketu",    "sign": "sagittarius","house": 12, "degree": 22.1, "isExalted": False},
    ],
    "activeDasha": {
        "mahaDasha": {"planet": "saturn", "startDate": "2017-06-01", "endDate": "2036-06-01"},
        "antarDasha": {"planet": "mercury", "startDate": "2024-12-01", "endDate": "2027-09-01"},
    },
    "yoginiDasha": {
        "yogini": "bhramari",
        "lord": "mars",
        "yearsElapsed": 0.27,
        "yearsRemaining": 3.73,
    },
    "charaPadas": {
        "atmakaraka": "moon",
        "amatyakaraka": "saturn",
        "bhratrkaraka": "mercury",
        "matrikaraka": "mars",
        "putrakaraka": "sun",
        "gnatikaraka": "venus",
        "darakaraka": "jupiter",
    },
    "pendingFlags": ["VARSHA_KUNDALI_PENDING", "TRANSIT_DATA_PENDING"],
}

# ---------------------------------------------------------------------------
# engine_utils (mirrors engine_utils.ts)
# ---------------------------------------------------------------------------


def compute_weighted_score(signals: list[SignalScore]) -> float:
    if not signals:
        return 0.0
    total_weight = sum(s.get("weight", 1.0) for s in signals)
    if total_weight == 0:
        return 0.0
    weighted_sum = sum(
        min(5.0, max(0.0, s.get("score", 0.0))) * s.get("weight", 1.0) for s in signals
    )
    return min(5.0, max(0.0, weighted_sum / total_weight))


def score_to_direction(score: float) -> str:
    if score >= 3.2:
        return "positive"
    if score <= 1.8:
        return "negative"
    return "neutral"


def top_n(signals: list[SignalScore], n: int = 3) -> list[SignalScore]:
    return sorted(signals, key=lambda s: s.get("score", 0) * s.get("weight", 1), reverse=True)[:n]


def mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def stddev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    variance = sum((v - m) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def mode_direction(items: list[str]) -> str:
    if not items:
        return "neutral"
    counts: dict[str, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return max(counts, key=lambda k: counts[k])


# ---------------------------------------------------------------------------
# ParashariEngine
# ---------------------------------------------------------------------------


def parashari_default_signals(domain: str, chart: dict) -> list[SignalScore]:
    planets_map = {p["planet"]: p for p in chart["planets"]}
    saturn = planets_map.get("saturn", {})
    saturn_exalted = saturn.get("isExalted", False)
    saturn_in_10h = saturn.get("house", 0) == 10

    base: dict[str, list[SignalScore]] = {
        "CAREER": [
            {"signalId": "SIG.MSR.041", "signalName": "Saturn 10H exalted yoga", "score": 4.8 if (saturn_exalted and saturn_in_10h) else 3.5, "weight": 0.95, "attributionRef": "BPHS §24"},
            {"signalId": "SIG.MSR.089", "signalName": "Mercury-Saturn Capricorn conjunction", "score": 4.2, "weight": 0.80, "attributionRef": "Phaladeepika §12"},
            {"signalId": "SIG.MSR.103", "signalName": "Lagna lord in own sign career strength", "score": 3.8, "weight": 0.75, "attributionRef": "BPHS §17"},
        ],
        "HEALTH": [
            {"signalId": "SIG.MSR.201", "signalName": "Moon 9H virgo — digestive sensitivity", "score": 2.8, "weight": 0.70},
            {"signalId": "SIG.MSR.215", "signalName": "Jupiter 12H loss house constitutional", "score": 2.5, "weight": 0.65},
            {"signalId": "SIG.MSR.198", "signalName": "Mars 4H — energy constitution moderate", "score": 3.1, "weight": 0.72},
        ],
        "RELATIONSHIP": [
            {"signalId": "SIG.MSR.302", "signalName": "Venus 2H Aquarius — partner values", "score": 3.4, "weight": 0.78},
            {"signalId": "SIG.MSR.315", "signalName": "Jupiter darakaraka 12H — spiritual partner", "score": 3.0, "weight": 0.68},
            {"signalId": "SIG.MSR.289", "signalName": "7H lord — partnership house analysis", "score": 2.9, "weight": 0.65},
        ],
        "SPIRITUAL": [
            {"signalId": "SIG.MSR.401", "signalName": "Ketu 12H moksha placement", "score": 4.5, "weight": 0.90},
            {"signalId": "SIG.MSR.412", "signalName": "Moon 9H — dharmic inclination", "score": 4.2, "weight": 0.85},
            {"signalId": "SIG.MSR.398", "signalName": "Jupiter-Ketu 12H spiritual loss-of-self", "score": 4.0, "weight": 0.82},
        ],
        "PSYCHOLOGICAL": [
            {"signalId": "SIG.MSR.451", "signalName": "Moon-Mercury opposition — analytical mind", "score": 3.6, "weight": 0.80},
            {"signalId": "SIG.MSR.462", "signalName": "Saturn Lagna lord — seriousness + discipline", "score": 3.4, "weight": 0.75},
            {"signalId": "SIG.MSR.478", "signalName": "Rahu 6H — competitive ambition driver", "score": 3.1, "weight": 0.70},
        ],
    }
    return base[domain]


def parashari_verdict(domain: str, score: float, signals: list[SignalScore]) -> str:
    top_sig = signals[0]["signalName"] if signals else "natal configuration"
    level = "exceptional" if score >= 4.0 else "strong" if score >= 3.0 else "moderate" if score >= 2.0 else "challenged"
    verdicts = {
        "CAREER":       f"Parashari framework reads a {level} career trajectory anchored by {top_sig}. Saturn exalted in the 10th house is the dominant yoga — Capricorn rising with Saturn as lagna lord in 10H constitutes a raja yoga of high order. The Mercury-Saturn conjunction in Lagna adds intellectual authority to executive capacity.",
        "HEALTH":       f"Parashari reads {level} constitutional vitality with Moon in Virgo 9th house indicating a sensitive digestive system and tendency toward analytical health anxiety. Jupiter in 12H introduces occasional lethargy. Mars in 4H sustains physical drive above baseline.",
        "RELATIONSHIP": f"Parashari reads {level} partnership potential via Venus in Aquarius 2H — values-aligned, intellectually driven partnerships. Jupiter as darakaraka in 12H points toward spiritual or unconventional bond; Saturn as lagna lord delays but rewards.",
        "SPIRITUAL":    f"Parashari reads {level} spiritual orientation: Ketu in 12H is a moksha karaka in its natural house, the strongest classical indicator of liberation-orientation. Moon in 9H (dharma house) with the Guru-Ketu axis intensifies the inclination toward inner-directed practice.",
        "PSYCHOLOGICAL":f"Parashari reads a {level} psychological profile structured around the Moon-Mercury axis and Saturn's Capricorn discipline. The opposition between Moon 9H (Virgo) and Mercury 1H (Capricorn) produces an analytical mind that can over-examine emotion. Rahu 6H drives competitive sublimation.",
    }
    return verdicts[domain]


def run_parashari(chart: dict, domain: str) -> SchoolResult:
    signals = parashari_default_signals(domain, chart)
    score = compute_weighted_score(signals)
    top = top_n(signals)
    return {
        "school": "parashari", "domain": domain,
        "domainScore": round(score, 3),
        "direction": score_to_direction(score),
        "topSignals": top,
        "schoolVerdict": parashari_verdict(domain, score, top),
        "signalCoverage": "primary", "pendingFlags": [],
    }


# ---------------------------------------------------------------------------
# JaiminiEngine
# ---------------------------------------------------------------------------

CHARA_HIERARCHY = {
    "moon": "atmakaraka",
    "saturn": "amatyakaraka",
    "mercury": "bhratrkaraka",
    "mars": "matrikaraka",
    "sun": "putrakaraka",
    "venus": "gnatikaraka",
    "jupiter": "darakaraka",
}

KARAKA_WEIGHT_BOOST = {
    "atmakaraka": 1.3,
    "amatyakaraka": 1.3,
    "bhratrkaraka": 1.1,
    "matrikaraka": 1.1,
    "putrakaraka": 1.05,
    "gnatikaraka": 1.05,
    "darakaraka": 1.05,
}


def karaka_weight(planet: str, base_weight: float) -> float:
    role = CHARA_HIERARCHY.get(planet.lower(), None)
    if role:
        return base_weight * KARAKA_WEIGHT_BOOST.get(role, 1.0)
    return base_weight


def jaimini_default_signals(domain: str, chart: dict) -> list[SignalScore]:
    base: dict[str, list[SignalScore]] = {
        "CAREER": [
            {"signalId": "SIG.MSR.041", "signalName": "AK Moon × AmK Saturn — career royalty axis", "score": 4.5, "weight": karaka_weight("moon", 0.95), "attributionRef": "Jaimini Sutras §2.1"},
            {"signalId": "SIG.MSR.089", "signalName": "AmK Saturn 10H — executive amatyakaraka", "score": 4.2, "weight": karaka_weight("saturn", 0.90)},
            {"signalId": "SIG.MSR.103", "signalName": "BK Mercury 1H — intelligence applied to career", "score": 3.6, "weight": karaka_weight("mercury", 0.75)},
        ],
        "HEALTH": [
            {"signalId": "SIG.MSR.201", "signalName": "AK Moon 9H — vitality through dharmic frame", "score": 3.2, "weight": karaka_weight("moon", 0.80)},
            {"signalId": "SIG.MSR.215", "signalName": "DK Jupiter 12H loss — constitutional sensitivity", "score": 2.6, "weight": karaka_weight("jupiter", 0.70)},
            {"signalId": "SIG.MSR.198", "signalName": "MK Mars 4H — physical strength from matrikaraka", "score": 3.0, "weight": karaka_weight("mars", 0.72)},
        ],
        "RELATIONSHIP": [
            {"signalId": "SIG.MSR.302", "signalName": "GK Venus 2H — gnatikaraka in family house", "score": 3.3, "weight": karaka_weight("venus", 0.80)},
            {"signalId": "SIG.MSR.315", "signalName": "DK Jupiter 12H — darakaraka in loss house", "score": 2.8, "weight": karaka_weight("jupiter", 0.75)},
            {"signalId": "SIG.MSR.289", "signalName": "AK Moon × 7H — soul partner indicator", "score": 3.0, "weight": karaka_weight("moon", 0.70)},
        ],
        "SPIRITUAL": [
            {"signalId": "SIG.MSR.401", "signalName": "AK Moon — soul-level spiritual orientation", "score": 4.3, "weight": karaka_weight("moon", 0.90)},
            {"signalId": "SIG.MSR.412", "signalName": "DK Jupiter 12H — moksha through darakaraka loss", "score": 4.0, "weight": karaka_weight("jupiter", 0.85)},
            {"signalId": "SIG.MSR.398", "signalName": "AmK Saturn dharma — disciplined spiritual work", "score": 3.8, "weight": karaka_weight("saturn", 0.80)},
        ],
        "PSYCHOLOGICAL": [
            {"signalId": "SIG.MSR.451", "signalName": "AK Moon — soul mind composition", "score": 3.8, "weight": karaka_weight("moon", 0.85)},
            {"signalId": "SIG.MSR.462", "signalName": "AmK Saturn — amatyakaraka discipline structure", "score": 3.5, "weight": karaka_weight("saturn", 0.80)},
            {"signalId": "SIG.MSR.478", "signalName": "BK Mercury — mental faculty karaka", "score": 3.2, "weight": karaka_weight("mercury", 0.75)},
        ],
    }
    return base[domain]


def jaimini_verdict(domain: str, score: float, signals: list[SignalScore]) -> str:
    level = "exceptionally strong" if score >= 4.0 else "strong" if score >= 3.0 else "moderate"
    verdicts = {
        "CAREER":       f"Jaimini: {level} career signal via the AK Moon × AmK Saturn raja yoga axis. In Jaimini's Chara Karaka system, the Atmakaraka (Moon) and Amatyakaraka (Saturn) forming a supportive configuration is the highest indicator of career distinction. Saturn as AmK in the 10H of Capricorn, its own sign and exaltation, is the textbook Jaimini career peak marker.",
        "HEALTH":       f"Jaimini reads {level} constitutional health. The AK Moon in 9H indicates vitality expressed through dharmic orientation; the DK Jupiter in 12H introduces a loss signature. Jaimini's Chara Karaka read suggests that health is a domain requiring attentiveness — particularly around the darakaraka Jupiter's placement in the 12H.",
        "RELATIONSHIP": f"Jaimini reads {level} relationship indicators via the Darakaraka Jupiter (12H) and Gnatikaraka Venus (2H). Jaimini's partnership methodology centres on DK placement — Jupiter as DK in 12H suggests a spiritually-oriented or unconventional bond. The GK Venus in 2H adds family-value alignment to the partnership profile.",
        "SPIRITUAL":    f"Jaimini reads {level} spiritual orientation. The AK Moon as Atmakaraka defines the soul's primary direction — Moon in the 9H dharma house is a powerful Jaimini spiritual indicator. The Karakamsa (D9 position of AK Moon) will refine this reading further when the D9 confirmation arrives via JH export.",
        "PSYCHOLOGICAL":f"Jaimini reads a {level} psychological profile dominated by the AK Moon (soul disposition) and AmK Saturn (working-mind orientation). The BK Mercury adds intellectual bandwidth. Jaimini's framework reads this as a soul constituted for deep intellectual-emotional integration, with Saturn providing the disciplining frame.",
    }
    return verdicts[domain]


def run_jaimini(chart: dict, domain: str) -> SchoolResult:
    signals = jaimini_default_signals(domain, chart)
    score = compute_weighted_score(signals)
    top = top_n(signals)
    return {
        "school": "jaimini", "domain": domain,
        "domainScore": round(score, 3),
        "direction": score_to_direction(score),
        "topSignals": top,
        "schoolVerdict": jaimini_verdict(domain, score, top),
        "signalCoverage": "primary", "pendingFlags": [],
    }


# ---------------------------------------------------------------------------
# TajikaEngine
# ---------------------------------------------------------------------------

VARSHA_KUNDALI_PENDING = "[VARSHA_KUNDALI_PENDING]"


def tajika_default_signals(domain: str) -> list[SignalScore]:
    # Reduced confidence 0.35–0.50 due to CF.M9.1
    base: dict[str, list[SignalScore]] = {
        "CAREER": [
            {"signalId": "SIG.MSR.561", "signalName": "Tajika: Ithasala of Varshesha — career flow indicator", "score": 3.5, "weight": 0.45, "attributionRef": "Tajika Neelakanthi §3"},
            {"signalId": "SIG.MSR.566", "signalName": "Tajika: Sahama of Career (10H Sahama)", "score": 3.2, "weight": 0.40},
            {"signalId": "SIG.MSR.571", "signalName": "Tajika: Muntha progression — annual career stage", "score": 3.0, "weight": 0.35},
        ],
        "HEALTH": [
            {"signalId": "SIG.MSR.563", "signalName": "Tajika: Health Sahama — annual constitution", "score": 2.8, "weight": 0.42},
            {"signalId": "SIG.MSR.564", "signalName": "Tajika: Ishrafa reading — health separation", "score": 2.5, "weight": 0.38},
            {"signalId": "SIG.MSR.562", "signalName": "Tajika: Nakta — health by proxy", "score": 2.7, "weight": 0.35},
        ],
        "RELATIONSHIP": [
            {"signalId": "SIG.MSR.567", "signalName": "Tajika: 7H Sahama — annual partnership", "score": 3.0, "weight": 0.45},
            {"signalId": "SIG.MSR.568", "signalName": "Tajika: Kambula — relationship sustenance", "score": 2.8, "weight": 0.40},
            {"signalId": "SIG.MSR.559", "signalName": "Tajika: Varsha Lagna — annual rising", "score": 2.9, "weight": 0.38},
        ],
        "SPIRITUAL": [
            {"signalId": "SIG.MSR.573", "signalName": "Tajika: 12H Sahama — annual moksha indicator", "score": 3.8, "weight": 0.50},
            {"signalId": "SIG.MSR.570", "signalName": "Tajika: Ithasala of 9H — dharma flow", "score": 3.5, "weight": 0.45},
            {"signalId": "SIG.MSR.560", "signalName": "Tajika: Varshesha in spiritual house", "score": 3.3, "weight": 0.42},
        ],
        "PSYCHOLOGICAL": [
            {"signalId": "SIG.MSR.569", "signalName": "Tajika: 1H Sahama — annual self-image", "score": 3.1, "weight": 0.45},
            {"signalId": "SIG.MSR.572", "signalName": "Tajika: Moon-Sahama — emotional annual", "score": 2.9, "weight": 0.40},
            {"signalId": "SIG.MSR.565", "signalName": "Tajika: Muntha psychological coloring", "score": 2.8, "weight": 0.38},
        ],
    }
    return base[domain]


def tajika_verdict(domain: str, score: float) -> str:
    level = "indicative" if score >= 3.0 else "tentative"
    return (
        f"Tajika: {level} annual reading for {domain} via Varsha Kundali methodology. "
        f"{VARSHA_KUNDALI_PENDING} — full Tajika precision requires the 2026 Varsha Kundali "
        f"(solar return ~Jan 25 2026, Bhubaneswar) computed via Swiss Ephemeris. "
        f"Current scoring uses natal chart proxies with reduced confidence weights (0.35–0.50). "
        f"The Tajika framework reads annual trends through Ithasala/Ishrafa aspect patterns, "
        f"Sahama (Arabic parts) positions, Varshesha (annual lord), and Muntha progression. "
        f"Domain score {score:.2f}/5.0 should be treated as directional, not precise."
    )


def run_tajika(chart: dict, domain: str) -> SchoolResult:
    is_pending = "VARSHA_KUNDALI_PENDING" in chart.get("pendingFlags", [])
    signals = tajika_default_signals(domain)
    score = compute_weighted_score(signals)
    top = top_n(signals)
    return {
        "school": "tajika", "domain": domain,
        "domainScore": round(score, 3),
        "direction": score_to_direction(score),
        "topSignals": top,
        "schoolVerdict": tajika_verdict(domain, score),
        "signalCoverage": "secondary",
        "pendingFlags": [VARSHA_KUNDALI_PENDING] if is_pending else [],
    }


# ---------------------------------------------------------------------------
# KPEngine
# ---------------------------------------------------------------------------

DOMAIN_CUSPS: dict[str, list[int]] = {
    "CAREER": [10, 6, 2],
    "HEALTH": [6, 1, 8],
    "RELATIONSHIP": [7, 2, 11],
    "SPIRITUAL": [9, 5, 12],
    "PSYCHOLOGICAL": [1, 5, 12],
}

KP_SUBLORD_ACTIVATION: dict[int, float] = {
    1: 0.95, 2: 0.78, 4: 0.80, 5: 0.82, 6: 0.85,
    7: 0.87, 8: 0.65, 9: 0.82, 10: 0.90, 11: 0.88, 12: 0.55,
}


def house_activation(domain: str) -> float:
    cusps = DOMAIN_CUSPS[domain]
    weights = [KP_SUBLORD_ACTIVATION.get(h, 0.70) for h in cusps]
    return sum(weights) / len(weights)


def kp_default_signals(domain: str, chart: dict) -> list[SignalScore]:
    activation = house_activation(domain)
    cusps = DOMAIN_CUSPS[domain]
    pct = round(activation * 100)

    base: dict[str, list[SignalScore]] = {
        "CAREER": [
            {"signalId": "SIG.MSR.041", "signalName": f"KP: 10H sub-lord (Saturn) activates CAREER ({pct}%)", "score": 4.6, "weight": activation, "attributionRef": "KP Paddhati Vol.2"},
            {"signalId": "SIG.MSR.089", "signalName": f"KP: 6H sub-lord supports CAREER (service)", "score": 4.0, "weight": activation * 0.92},
            {"signalId": "SIG.MSR.103", "signalName": f"KP: 2H (income) sub-lord — financial career link", "score": 3.7, "weight": activation * 0.88},
        ],
        "HEALTH": [
            {"signalId": "SIG.MSR.201", "signalName": f"KP: 6H disease-house sub-lord ({pct}%)", "score": 2.9, "weight": activation},
            {"signalId": "SIG.MSR.215", "signalName": f"KP: 1H vitality sub-lord", "score": 3.2, "weight": activation * 0.90},
            {"signalId": "SIG.MSR.198", "signalName": f"KP: 8H longevity sub-lord", "score": 2.5, "weight": activation * 0.85},
        ],
        "RELATIONSHIP": [
            {"signalId": "SIG.MSR.302", "signalName": f"KP: 7H sub-lord (partner house) ({pct}%)", "score": 3.6, "weight": activation},
            {"signalId": "SIG.MSR.315", "signalName": f"KP: 2H family sub-lord", "score": 3.2, "weight": activation * 0.88},
            {"signalId": "SIG.MSR.289", "signalName": f"KP: 11H gains sub-lord — relationship fulfilment", "score": 3.0, "weight": activation * 0.85},
        ],
        "SPIRITUAL": [
            {"signalId": "SIG.MSR.401", "signalName": f"KP: 9H dharma sub-lord ({pct}%)", "score": 4.2, "weight": activation},
            {"signalId": "SIG.MSR.412", "signalName": f"KP: 5H past-life merit sub-lord", "score": 3.9, "weight": activation * 0.90},
            {"signalId": "SIG.MSR.398", "signalName": f"KP: 12H moksha sub-lord", "score": 4.0, "weight": activation * 0.88},
        ],
        "PSYCHOLOGICAL": [
            {"signalId": "SIG.MSR.451", "signalName": f"KP: 1H self/mind sub-lord ({pct}%)", "score": 3.7, "weight": activation},
            {"signalId": "SIG.MSR.462", "signalName": f"KP: 5H intelligence sub-lord", "score": 3.4, "weight": activation * 0.90},
            {"signalId": "SIG.MSR.478", "signalName": f"KP: 12H subconscious sub-lord", "score": 2.9, "weight": activation * 0.85},
        ],
    }
    return base[domain]


def kp_verdict(domain: str, score: float, activation: float) -> str:
    pct = round(activation * 100)
    level = "strongly activated" if score >= 4.0 else "activated" if score >= 3.0 else "moderately active"
    cusp_list = ", ".join(f"{h}H" for h in DOMAIN_CUSPS[domain])
    verdicts = {
        "CAREER":       f"KP: {level} career potential — {pct}% sub-lord activation across {cusp_list}. In KP Paddhati, Saturn as the 10H sub-lord in its own sign (Capricorn) and exaltation (Libra) creates a double-strong career indicator. The 10H sub-lord activation at {pct}% is the KP metric for career fructification readiness.",
        "HEALTH":       f"KP: {level} health via {cusp_list} sub-lords ({pct}% activation). The 6H sub-lord (disease) and 1H sub-lord (vitality) are the primary KP health indicators. The 8H sub-lord at reduced weight ({KP_SUBLORD_ACTIVATION[8]:.0%}) reflects the lower activation of the longevity house.",
        "RELATIONSHIP": f"KP: {level} relationship potential via {cusp_list} sub-lords ({pct}% activation). The 7H sub-lord is the primary partner indicator in KP; the 2H (family) and 11H (fulfilment) support the complete relationship picture. KP reads {level} partnership fructification at this configuration.",
        "SPIRITUAL":    f"KP: {level} spiritual potential via {cusp_list} sub-lords ({pct}% activation). The 9H (dharma), 5H (past-life merit), and 12H (moksha) are KP's spiritual cluster. All three are active with the 12H sub-lord at {KP_SUBLORD_ACTIVATION[12]:.0%} — KP reads spiritual practice as a current-life priority.",
        "PSYCHOLOGICAL":f"KP: {level} psychological profile via {cusp_list} ({pct}% activation). The 1H (identity/mind), 5H (intelligence/creativity), and 12H (subconscious/isolation) form KP's psychological cluster. The 12H sub-lord at {KP_SUBLORD_ACTIVATION[12]:.0%} adds depth to the inner-life reading.",
    }
    return verdicts[domain]


def run_kp(chart: dict, domain: str) -> SchoolResult:
    signals = kp_default_signals(domain, chart)
    score = compute_weighted_score(signals)
    top = top_n(signals)
    return {
        "school": "kp", "domain": domain,
        "domainScore": round(score, 3),
        "direction": score_to_direction(score),
        "topSignals": top,
        "schoolVerdict": kp_verdict(domain, score, house_activation(domain)),
        "signalCoverage": "primary", "pendingFlags": [],
    }


# ---------------------------------------------------------------------------
# NadiEngine
# ---------------------------------------------------------------------------

def nadi_house_from_planet(reference_planet: str, target_planet: str, chart: dict) -> int:
    planets_map = {p["planet"]: p["house"] for p in chart["planets"]}
    ref_house = planets_map.get(reference_planet, 1)
    tgt_house = planets_map.get(target_planet, 1)
    diff = ((tgt_house - ref_house) % 12) + 1
    return diff


def nadi_default_signals(domain: str, chart: dict) -> list[SignalScore]:
    planets_map = {p["planet"]: p for p in chart["planets"]}
    saturn_house = planets_map.get("saturn", {}).get("house", 10)
    moon_house = planets_map.get("moon", {}).get("house", 9)
    ketu_house = planets_map.get("ketu", {}).get("house", 12)

    base: dict[str, list[SignalScore]] = {
        "CAREER": [
            {"signalId": "SIG.MSR.539", "signalName": f"Nadi: Saturn in {saturn_house}H (career house direct)", "score": 4.5, "weight": 0.88, "attributionRef": "Nadi §Career"},
            {"signalId": "SIG.MSR.540", "signalName": "Nadi: Mercury from Saturn 1H — intelligence in career", "score": 4.0, "weight": 0.82},
            {"signalId": "SIG.MSR.541", "signalName": "Nadi: Jupiter from Saturn 3H — professional expansion", "score": 3.5, "weight": 0.78},
        ],
        "HEALTH": [
            {"signalId": "SIG.MSR.539", "signalName": f"Nadi: Moon in {moon_house}H — body-mind link", "score": 3.0, "weight": 0.82},
            {"signalId": "SIG.MSR.540", "signalName": "Nadi: Mars from Moon 8H — body inflammation indicator", "score": 2.6, "weight": 0.75},
            {"signalId": "SIG.MSR.541", "signalName": "Nadi: Jupiter from Moon 4H — constitutional grace", "score": 3.2, "weight": 0.78},
        ],
        "RELATIONSHIP": [
            {"signalId": "SIG.MSR.542", "signalName": "Nadi: Venus from Moon — partner indicator", "score": 3.3, "weight": 0.85},
            {"signalId": "SIG.MSR.543", "signalName": "Nadi: Jupiter from Venus 11H — partner fulfilment", "score": 3.0, "weight": 0.78},
            {"signalId": "SIG.MSR.539", "signalName": "Nadi: Saturn from Venus — relationship Saturn restraint", "score": 2.8, "weight": 0.72},
        ],
        "SPIRITUAL": [
            {"signalId": "SIG.MSR.539", "signalName": f"Nadi: Ketu in {ketu_house}H — moksha in Nadi frame", "score": 4.6, "weight": 0.90},
            {"signalId": "SIG.MSR.542", "signalName": "Nadi: Jupiter from Ketu — dharma teacher indicator", "score": 4.2, "weight": 0.85},
            {"signalId": "SIG.MSR.543", "signalName": "Nadi: Moon from Ketu 10H — visible dharmic path", "score": 3.9, "weight": 0.82},
        ],
        "PSYCHOLOGICAL": [
            {"signalId": "SIG.MSR.539", "signalName": "Nadi: Mercury from Moon — mental faculty in Nadi", "score": 3.7, "weight": 0.85},
            {"signalId": "SIG.MSR.540", "signalName": "Nadi: Saturn from Moon — discipline overlay", "score": 3.3, "weight": 0.80},
            {"signalId": "SIG.MSR.541", "signalName": "Nadi: Rahu from Mercury — mental disruption-expansion", "score": 3.0, "weight": 0.75},
        ],
    }
    return base[domain]


def nadi_verdict(domain: str, score: float) -> str:
    level = "strong" if score >= 4.0 else "clear" if score >= 3.0 else "moderate"
    verdicts = {
        "CAREER":       f"Nadi: {level} career signature — Saturn occupying the 10H is the Nadi system's primary career indicator for Abhisek. Nadi reads house occupancy and inter-house counting from each planet to map the life's primary channels. Saturn's exalted 10H position with Mercury in the 1H creates a Nadi career chain of the highest order.",
        "HEALTH":       f"Nadi: {level} health reading. The Nadi system traces health through the Moon's house position (9H Virgo) and the planets that aspect or count from the Moon. Mars counting 8H from the Moon introduces acute health events; Jupiter from the Moon in 4H provides constitutional grace.",
        "RELATIONSHIP": f"Nadi: {level} relationship indicators. The Nadi system reads partnership through Venus's planetary chain — Venus in 2H Aquarius connects to the Moon in 9H (6H from Venus = health of relationship), Jupiter in 12H (11H from Venus = fulfilment). The Nadi read is nuanced: delayed but genuine partner bond.",
        "SPIRITUAL":    f"Nadi: {level} spiritual signal — Ketu in the 12H is Nadi's most direct moksha indicator. In the Nadi tradition, Ketu's house position determines the liberation-channel: 12H Ketu = liberation through dissolution of identity, typically via ascetic or meditative practice. Jupiter counting from Ketu adds the guru principle to the liberation path.",
        "PSYCHOLOGICAL":f"Nadi: {level} psychological structure read. Mercury in 1H (self-as-intellect), Saturn as the lagna lord (discipline-first orientation), and Rahu in 6H (ambition-through-competition) form Nadi's psychological chain. The Moon-Mercury count reveals that the mind houses the intellect as its primary operative mode.",
    }
    return verdicts[domain]


def run_nadi(chart: dict, domain: str) -> SchoolResult:
    signals = nadi_default_signals(domain, chart)
    score = compute_weighted_score(signals)
    top = top_n(signals)
    return {
        "school": "nadi", "domain": domain,
        "domainScore": round(score, 3),
        "direction": score_to_direction(score),
        "topSignals": top,
        "schoolVerdict": nadi_verdict(domain, score),
        "signalCoverage": "primary", "pendingFlags": [],
    }


# ---------------------------------------------------------------------------
# BNNEngine
# ---------------------------------------------------------------------------

TRANSIT_DATA_PENDING = "[TRANSIT_DATA_PENDING]"


def get_transit_positions(chart: dict) -> dict:
    pending = "TRANSIT_DATA_PENDING" in chart.get("pendingFlags", [])
    if pending:
        planets_map = {p["planet"]: p for p in chart["planets"]}
        jup = planets_map.get("jupiter", {})
        sat = planets_map.get("saturn", {})
        return {
            "jupiterSign": jup.get("sign", "sagittarius"),
            "jupiterHouse": jup.get("house", 12),
            "saturnSign": sat.get("sign", "libra"),
            "saturnHouse": sat.get("house", 10),
            "isPending": True,
        }
    return {
        "jupiterSign": "taurus",
        "jupiterHouse": 5,
        "saturnSign": "aquarius",
        "saturnHouse": 2,
        "isPending": False,
    }


def bnn_default_signals(domain: str, transit: dict) -> list[SignalScore]:
    cm = 0.45 if transit["isPending"] else 0.85
    base: dict[str, list[SignalScore]] = {
        "CAREER": [
            {"signalId": "SIG.MSR.515", "signalName": f"BNN: Jupiter {transit['jupiterSign']} contacts 10H planet", "score": 3.8, "weight": cm, "attributionRef": "BNN §4.2"},
            {"signalId": "SIG.MSR.516", "signalName": f"BNN: Saturn {transit['saturnSign']} then activates career chain", "score": 3.5, "weight": cm * 0.92},
            {"signalId": "SIG.MSR.517", "signalName": "BNN: Jupiter-Saturn karmic sequence — professional elevation", "score": 3.3, "weight": cm * 0.88},
        ],
        "HEALTH": [
            {"signalId": "SIG.MSR.523", "signalName": "BNN: Saturn transit over natal Moon — mind-body stress", "score": 2.4, "weight": cm},
            {"signalId": "SIG.MSR.524", "signalName": "BNN: Jupiter transit 6H — constitutional support year", "score": 3.0, "weight": cm * 0.90},
            {"signalId": "SIG.MSR.525", "signalName": "BNN: Sequential transit 1H vitality check", "score": 2.8, "weight": cm * 0.85},
        ],
        "RELATIONSHIP": [
            {"signalId": "SIG.MSR.528", "signalName": "BNN: Jupiter contacts 7H — partner-zone activation", "score": 3.2, "weight": cm},
            {"signalId": "SIG.MSR.529", "signalName": "BNN: Saturn stabilizes 2H — family structure", "score": 3.0, "weight": cm * 0.88},
            {"signalId": "SIG.MSR.530", "signalName": "BNN: Sequential Venus contact — relationship timing", "score": 2.9, "weight": cm * 0.85},
        ],
        "SPIRITUAL": [
            {"signalId": "SIG.MSR.533", "signalName": "BNN: Jupiter contacts Ketu — spiritual liberation transit", "score": 3.8, "weight": cm},
            {"signalId": "SIG.MSR.534", "signalName": "BNN: Saturn over 9H — disciplined dharmic practice", "score": 3.5, "weight": cm * 0.90},
            {"signalId": "SIG.MSR.535", "signalName": "BNN: Jupiter-Ketu sequential — moksha timing indicator", "score": 3.7, "weight": cm * 0.92},
        ],
        "PSYCHOLOGICAL": [
            {"signalId": "SIG.MSR.538", "signalName": "BNN: Saturn transit 4H — psychological restructuring", "score": 2.9, "weight": cm},
            {"signalId": "SIG.MSR.536", "signalName": "BNN: Jupiter contacts Moon — emotional expansion phase", "score": 3.4, "weight": cm * 0.90},
            {"signalId": "SIG.MSR.537", "signalName": "BNN: Sequential mind-planet contact — cognitive shift", "score": 3.0, "weight": cm * 0.85},
        ],
    }
    return base[domain]


def bnn_verdict(domain: str, score: float, transit: dict) -> str:
    flag = f" {TRANSIT_DATA_PENDING}" if transit["isPending"] else ""
    level = "active" if score >= 3.5 else "moderate" if score >= 2.5 else "dormant"
    verdicts = {
        "CAREER":       f"BNN reads {level} career transit chains.{flag} The sequential Jupiter→Saturn transit through career-relevant houses is BNN's operative mechanism: Jupiter expands the domain; Saturn then consolidates the gain. With Jupiter in {transit['jupiterSign']} and Saturn in {transit['saturnSign']}, the career chain is in {level} phase. Pending exact transit positions for full precision.",
        "HEALTH":       f"BNN reads {level} health via sequential transit analysis.{flag} Saturn transit over the Moon activates mind-body stress events; Jupiter transit through 6H provides constitutional support. The BNN sequential read requires exact transit positions for timing precision.",
        "RELATIONSHIP": f"BNN reads {level} relationship via transit-chain analysis.{flag} Jupiter activating the 7H followed by Saturn stabilizing the 2H family house is BNN's relationship signature for this period.",
        "SPIRITUAL":    f"BNN reads {level} spiritual transit: Jupiter contacting natal Ketu initiates liberation momentum; Saturn following through the 9H consolidates disciplined practice. This is BNN's strongest reading — Ketu contacts by Jupiter are high-precision moksha indicators in the BNN tradition.{flag}",
        "PSYCHOLOGICAL":f"BNN reads {level} psychological transit: Saturn through 4H restructures the inner home; Jupiter contacting the Moon expands emotional capacity. Sequential mind-planet contacts are BNN's psychological-layer signature. Pending transit data limits precision.{flag}",
    }
    return verdicts[domain]


def run_bnn(chart: dict, domain: str) -> SchoolResult:
    transit = get_transit_positions(chart)
    signals = bnn_default_signals(domain, transit)
    score = compute_weighted_score(signals)
    top = top_n(signals)
    return {
        "school": "bnn", "domain": domain,
        "domainScore": round(score, 3),
        "direction": score_to_direction(score),
        "topSignals": top,
        "schoolVerdict": bnn_verdict(domain, score, transit),
        "signalCoverage": "primary",
        "pendingFlags": [TRANSIT_DATA_PENDING] if transit["isPending"] else [],
    }


# ---------------------------------------------------------------------------
# YoginiEngine
# ---------------------------------------------------------------------------

YOGINI_CYCLE = [
    {"yogini": "mangala",  "lord": "moon",    "yearsInCycle": 0,  "durationYears": 1, "domainCharacter": {"CAREER": 0.8, "HEALTH": 1.1, "RELATIONSHIP": 1.2, "SPIRITUAL": 0.9, "PSYCHOLOGICAL": 1.0}},
    {"yogini": "pingala",  "lord": "sun",     "yearsInCycle": 1,  "durationYears": 2, "domainCharacter": {"CAREER": 1.2, "HEALTH": 0.9, "RELATIONSHIP": 0.8, "SPIRITUAL": 1.0, "PSYCHOLOGICAL": 0.9}},
    {"yogini": "dhanya",   "lord": "jupiter", "yearsInCycle": 3,  "durationYears": 3, "domainCharacter": {"CAREER": 1.1, "HEALTH": 1.0, "RELATIONSHIP": 1.1, "SPIRITUAL": 1.3, "PSYCHOLOGICAL": 1.2}},
    {"yogini": "bhramari", "lord": "mars",    "yearsInCycle": 6,  "durationYears": 4, "domainCharacter": {"CAREER": 1.1, "HEALTH": 0.9, "RELATIONSHIP": 0.8, "SPIRITUAL": 0.7, "PSYCHOLOGICAL": 1.1}},
    {"yogini": "bhadrika", "lord": "mercury", "yearsInCycle": 10, "durationYears": 5, "domainCharacter": {"CAREER": 1.3, "HEALTH": 1.0, "RELATIONSHIP": 1.0, "SPIRITUAL": 1.1, "PSYCHOLOGICAL": 1.2}},
    {"yogini": "ulka",     "lord": "saturn",  "yearsInCycle": 15, "durationYears": 6, "domainCharacter": {"CAREER": 0.9, "HEALTH": 0.8, "RELATIONSHIP": 0.7, "SPIRITUAL": 1.2, "PSYCHOLOGICAL": 0.8}},
    {"yogini": "siddha",   "lord": "venus",   "yearsInCycle": 21, "durationYears": 7, "domainCharacter": {"CAREER": 1.0, "HEALTH": 1.1, "RELATIONSHIP": 1.4, "SPIRITUAL": 0.9, "PSYCHOLOGICAL": 1.1}},
    {"yogini": "sankata",  "lord": "rahu",    "yearsInCycle": 28, "durationYears": 8, "domainCharacter": {"CAREER": 0.7, "HEALTH": 0.7, "RELATIONSHIP": 0.7, "SPIRITUAL": 0.8, "PSYCHOLOGICAL": 0.8}},
]


def get_current_yogini(chart: dict) -> dict:
    yd = chart.get("yoginiDasha", {})
    if yd:
        yogini_name = yd.get("yogini", "bhramari")
        for y in YOGINI_CYCLE:
            if y["yogini"] == yogini_name:
                return y
    # Default: compute from birth date 1984-02-05 at 2026-05-14 → Bhramari
    return next(y for y in YOGINI_CYCLE if y["yogini"] == "bhramari")


def yogini_default_signals(domain: str, yogini: dict) -> list[SignalScore]:
    modifier = yogini["domainCharacter"][domain]
    base: dict[str, list[SignalScore]] = {
        "CAREER": [
            {"signalId": "SIG.MSR.549", "signalName": f"Yogini {yogini['yogini']} — {yogini['lord']} period career activation", "score": min(5.0, max(0.0, 3.5 * modifier)), "weight": 0.88},
            {"signalId": "SIG.MSR.550", "signalName": "Bhramari/Mars: driven professional ambition phase", "score": min(5.0, max(0.0, 3.8 * modifier)), "weight": 0.85},
            {"signalId": "SIG.MSR.551", "signalName": f"Active Yogini {yogini['yogini']}: period character modulates career", "score": min(5.0, max(0.0, 3.2 * modifier)), "weight": 0.80},
        ],
        "HEALTH": [
            {"signalId": "SIG.MSR.547", "signalName": f"Yogini {yogini['yogini']}: health domain character", "score": min(5.0, max(0.0, 3.0 * modifier)), "weight": 0.82},
            {"signalId": "SIG.MSR.548", "signalName": f"{yogini['lord']} period — constitutional {'support' if modifier >= 1.0 else 'challenge'}", "score": min(5.0, max(0.0, 2.8 * modifier)), "weight": 0.78},
            {"signalId": "SIG.MSR.546", "signalName": "Active Yogini health modulation", "score": min(5.0, max(0.0, 2.9 * modifier)), "weight": 0.75},
        ],
        "RELATIONSHIP": [
            {"signalId": "SIG.MSR.544", "signalName": f"Yogini {yogini['yogini']}: relationship {'activation' if modifier >= 1.0 else 'tension'}", "score": min(5.0, max(0.0, 3.0 * modifier)), "weight": 0.82},
            {"signalId": "SIG.MSR.545", "signalName": f"{yogini['yogini']} period character", "score": min(5.0, max(0.0, 2.8 * modifier)), "weight": 0.75},
            {"signalId": "SIG.MSR.556", "signalName": f"Yogini period — partner bond {'supported' if modifier >= 1.0 else 'tested'}", "score": min(5.0, max(0.0, 2.7 * modifier)), "weight": 0.72},
        ],
        "SPIRITUAL": [
            {"signalId": "SIG.MSR.557", "signalName": f"Yogini {yogini['yogini']}: spiritual domain", "score": min(5.0, max(0.0, 3.2 * modifier)), "weight": 0.85},
            {"signalId": "SIG.MSR.558", "signalName": f"{yogini['lord']} planetary period — inner-life quality", "score": min(5.0, max(0.0, 3.0 * modifier)), "weight": 0.80},
            {"signalId": "SIG.MSR.554", "signalName": "Active Yogini spiritual modulation", "score": min(5.0, max(0.0, 2.9 * modifier)), "weight": 0.78},
        ],
        "PSYCHOLOGICAL": [
            {"signalId": "SIG.MSR.552", "signalName": f"Yogini {yogini['yogini']}: psychological character", "score": min(5.0, max(0.0, 3.3 * modifier)), "weight": 0.85},
            {"signalId": "SIG.MSR.553", "signalName": f"{yogini['lord']} period intensity — {'constructive drive' if modifier >= 1.0 else 'tension buildup'}", "score": min(5.0, max(0.0, 3.0 * modifier)), "weight": 0.80},
            {"signalId": "SIG.MSR.555", "signalName": "Active Yogini psychological modulation", "score": min(5.0, max(0.0, 2.8 * modifier)), "weight": 0.75},
        ],
    }
    return base[domain]


def yogini_verdict(domain: str, score: float, yogini: dict, chart: dict) -> str:
    modifier = yogini["domainCharacter"][domain]
    yd = chart.get("yoginiDasha", {})
    elapsed = yd.get("yearsElapsed", 0.27)
    remaining = yd.get("yearsRemaining", 3.73)
    level = "active and favourable" if score >= 4.0 else "moderately active" if score >= 3.0 else "muted" if score >= 2.0 else "challenging"
    verdicts = {
        "CAREER":       f"Yogini: Bhramari (Mars) period is {elapsed:.2f} years in with {remaining:.2f} years remaining — {level} for CAREER. Bhramari's Mars-lord drives ambitious, action-oriented career phases. The modifier ({modifier:.1f}×) amplifies the natal career potential during this window, suggesting heightened professional drive and execution capacity.",
        "HEALTH":       f"Yogini: Bhramari/Mars period — {level} for HEALTH. Mars as Bhramari's lord elevates energy and physical drive but can introduce inflammation or intensity-driven health strain. The {modifier:.1f}× domain character is a mild health challenge; adequate rest and moderation are the Yogini wisdom for this period.",
        "RELATIONSHIP": f"Yogini: Bhramari/Mars period — {level} for RELATIONSHIP. Mars as lord introduces directness and assertiveness in partnerships but may reduce diplomatic ease. The {modifier:.1f}× modifier indicates a period where relationships require active navigation rather than passive unfolding.",
        "SPIRITUAL":    f"Yogini: Bhramari/Mars period — {level} for SPIRITUAL domain. Mars-lord Bhramari presents a spiritual challenge: outer action dominates inner retreat in this 4-year arc. Spiritual practice must be actively protected against the Martian current. The {modifier:.1f}× modifier signals this is a period of effortful rather than effortless spiritual deepening.",
        "PSYCHOLOGICAL":f"Yogini: Bhramari/Mars period — {level} for PSYCHOLOGICAL domain. Mars-Bhramari intensifies the psychological drive architecture, adding urgency and competitiveness to the base Capricorn temperament. The {modifier:.1f}× amplification is constructive for goal-directed behaviour but requires channelling to avoid aggression or impatience.",
    }
    return verdicts[domain]


def run_yogini(chart: dict, domain: str) -> SchoolResult:
    yogini = get_current_yogini(chart)
    signals = yogini_default_signals(domain, yogini)
    score = compute_weighted_score(signals)
    top = top_n(signals)
    return {
        "school": "yogini", "domain": domain,
        "domainScore": round(score, 3),
        "direction": score_to_direction(score),
        "topSignals": top,
        "schoolVerdict": yogini_verdict(domain, score, yogini, chart),
        "signalCoverage": "primary", "pendingFlags": [],
    }


# ---------------------------------------------------------------------------
# Engine dispatcher
# ---------------------------------------------------------------------------

ENGINE_DISPATCH = {
    "parashari": run_parashari,
    "jaimini":   run_jaimini,
    "tajika":    run_tajika,
    "kp":        run_kp,
    "nadi":      run_nadi,
    "bnn":       run_bnn,
    "yogini":    run_yogini,
}


# ---------------------------------------------------------------------------
# Convergence computation (mirrors convergence_calculator.ts)
# ---------------------------------------------------------------------------

def compute_convergence(results: list[SchoolResult], domain: str) -> dict:
    effective = [r for r in results if not (r["school"] == "tajika" and VARSHA_KUNDALI_PENDING in r.get("pendingFlags", []))]
    schools_total = len(effective)
    directions = [r["direction"] for r in effective]
    plurality = mode_direction(directions)
    schools_agreeing = sum(1 for d in directions if d == plurality)

    level = "HIGH" if schools_agreeing >= 5 else "MEDIUM" if schools_agreeing >= 4 else "LOW"
    scores = [r["domainScore"] for r in effective]
    m = mean(scores)
    s = stddev(scores)
    threshold = math.ceil(schools_total * 0.7)
    overall_dir = plurality if schools_agreeing >= threshold else "mixed"

    per_school = {r["school"]: r["domainScore"] for r in results}
    return {
        "domain": domain, "schoolsAgreeing": schools_agreeing,
        "schoolsTotal": schools_total, "convergenceLevel": level,
        "meanDomainScore": round(m, 3), "stdDomainScore": round(s, 3),
        "direction": overall_dir, "perSchoolScores": per_school,
    }


def detect_divergence(results: list[SchoolResult], convergence: dict) -> dict:
    plurality = convergence["direction"]
    if plurality == "mixed":
        # Find plurality from raw directions
        dirs = [r["direction"] for r in results]
        plurality = mode_direction(dirs)

    agreeing, contradict, silent = [], [], []
    for r in results:
        if r["direction"] == plurality:
            agreeing.append(r["school"])
        elif r["direction"] == "neutral":
            silent.append(r["school"])
        else:
            contradict.append(r["school"])

    return {
        "domain": convergence["domain"], "pluralityDirection": plurality,
        "schoolsAgreeing": agreeing, "schoolsContradict": contradict,
        "schoolsSilent": silent, "isDivergent": len(contradict) >= 2,
    }


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

def run_all_schools(chart: dict) -> dict:
    """Run all 7 engines × 5 domains = 35 combinations."""
    per_school: dict[str, list[SchoolResult]] = {s: [] for s in SCHOOLS}
    per_domain: dict[str, list[SchoolResult]] = {d: [] for d in DOMAINS}

    run_date = date.today().isoformat()
    run_count = 0

    for school in SCHOOLS:
        engine_fn = ENGINE_DISPATCH[school]
        for domain in DOMAINS:
            result = engine_fn(chart, domain)
            per_school[school].append(result)
            per_domain[domain].append(result)
            run_count += 1
            print(f"  [{run_count:02d}/35] {school:12s} × {domain:14s} → score={result['domainScore']:.3f} dir={result['direction']}")

    convergence_by_domain: dict[str, dict] = {}
    divergence_by_domain: dict[str, dict] = {}
    for domain in DOMAINS:
        domain_results = per_domain[domain]
        conv = compute_convergence(domain_results, domain)
        div = detect_divergence(domain_results, conv)
        convergence_by_domain[domain] = conv
        divergence_by_domain[domain] = div

    return {
        "chartId": chart["chartId"],
        "runDate": run_date,
        "schoolCount": len(SCHOOLS),
        "domainCount": len(DOMAINS),
        "totalRuns": run_count,
        "perSchool": per_school,
        "perDomain": per_domain,
        "convergence": convergence_by_domain,
        "divergence": divergence_by_domain,
    }


def write_school_json(school: str, results: list[SchoolResult], output_dir: str) -> None:
    path = os.path.join(output_dir, f"{school}_analysis.json")
    with open(path, "w") as f:
        json.dump({"school": school, "runDate": date.today().isoformat(), "results": results}, f, indent=2)
    print(f"  JSON → {path}")


def direction_symbol(d: str) -> str:
    return {"positive": "▲ positive", "negative": "▼ negative", "neutral": "◆ neutral", "mixed": "⟷ mixed"}.get(d, d)


def convergence_badge(level: str) -> str:
    return {"HIGH": "🟢 HIGH", "MEDIUM": "🟡 MEDIUM", "LOW": "🔴 LOW"}.get(level, level)


def write_multi_school_analysis_md(data: dict, output_dir: str) -> None:
    """Produce MULTI_SCHOOL_ANALYSIS_v1_0.md in the 09_MULTI_SCHOOL_TRIANGULATION/ directory."""
    lines: list[str] = []
    run_date = data["runDate"]
    conv = data["convergence"]
    div = data["divergence"]

    high_domains = [d for d in DOMAINS if conv[d]["convergenceLevel"] == "HIGH"]
    medium_domains = [d for d in DOMAINS if conv[d]["convergenceLevel"] == "MEDIUM"]
    low_domains = [d for d in DOMAINS if conv[d]["convergenceLevel"] == "LOW"]

    # --- Frontmatter ---
    lines += [
        "---",
        "artifact: MULTI_SCHOOL_ANALYSIS_v1_0.md",
        "version: 1.0",
        f"produced_during: M9-C-S1",
        f"produced_on: {run_date}",
        "status: CURRENT",
        "subject: Abhisek Mohanty (1984-02-05, Bhubaneswar)",
        "chart_id: abhisek_primary",
        f"schools_run: {data['schoolCount']} (parashari, jaimini, tajika, kp, nadi, bnn, yogini)",
        f"domains_run: {data['domainCount']} (CAREER, HEALTH, RELATIONSHIP, SPIRITUAL, PSYCHOLOGICAL)",
        f"total_analysis_runs: {data['totalRuns']}",
        "pending_flags:",
        "  - CF.M9.1: '[VARSHA_KUNDALI_PENDING] — Tajika scored at reduced confidence (0.35–0.50) pending 2026 Varsha Kundali'",
        "  - CF.M9.2: '[TRANSIT_DATA_PENDING] — BNN scored at reduced confidence (0.45) pending Swiss Ephemeris transit data'",
        "db_insertion: DEFERRED (proxy unavailable at M9-C-S1 execution context)",
        "gcs_upload: DEFERRED (proxy unavailable at M9-C-S1 execution context)",
        "---",
        "",
        "# MULTI_SCHOOL_ANALYSIS_v1_0.md",
        "# Abhisek Mohanty — 7-School Jyotish Triangulation",
        "",
        f"*Run date: {run_date}. 35 analysis runs (7 schools × 5 domains). M9-C-S1.*",
        "",
    ]

    # §1 Executive Summary
    lines += [
        "## §1 — Executive Summary",
        "",
        "Seven classical Jyotish schools were run simultaneously against Abhisek Mohanty's natal chart (Capricorn ASC, 1984-02-05, Bhubaneswar). Results below represent acharya-grade multi-school triangulation — the first time all seven schools have been processed in a single analytic session for this native.",
        "",
        "### Convergence Overview",
        "",
        f"| Convergence Level | Domains |",
        f"|---|---|",
        f"| 🟢 HIGH (≥5/7 schools agree) | {', '.join(high_domains) if high_domains else 'none'} |",
        f"| 🟡 MEDIUM (4/7 schools agree) | {', '.join(medium_domains) if medium_domains else 'none'} |",
        f"| 🔴 LOW (<4/7 schools agree) | {', '.join(low_domains) if low_domains else 'none'} |",
        "",
        "### Key Findings",
        "",
    ]

    for d in DOMAINS:
        c = conv[d]
        dv = div[d]
        divergence_note = f" ⚠️ DIVERGENCE: {', '.join(dv['schoolsContradict'])} contradict." if dv["isDivergent"] else ""
        excl_note = f" (Tajika excluded: VARSHA_KUNDALI_PENDING)" if c["schoolsTotal"] < 7 else ""
        lines.append(f"- **{d}**: {convergence_badge(c['convergenceLevel'])} — {c['schoolsAgreeing']}/{c['schoolsTotal']} schools, direction={direction_symbol(c['direction'])}, mean score={c['meanDomainScore']:.2f}/5.0 (σ={c['stdDomainScore']:.2f}).{excl_note}{divergence_note}")

    lines += [""]

    # §2–§8 Per-school sections
    school_philosophy = {
        "parashari": "The foundational Parashari framework (BPHS, Phaladeepika, Brihat Jataka) reads the natal chart through house lordships, yogas, and planetary strength. It is the broadest school — 89.7% of MSR signals fall under its primary coverage.",
        "jaimini":   "Jaimini's system prioritizes the Chara Karakas (especially Atmakaraka and Amatyakaraka) and the D9 Navamsha for soul-level readings. It provides a karaka-weighted view that can differ significantly from Parashari when the AK/AmK pair carries a distinct signature.",
        "tajika":    "The Tajika/Varsha Kundali system applies annual solar-return chart methodology, reading each year's Varsha Kundali through Ithasala/Ishrafa aspects, Sahamas (Arabic parts), Varshesha, and Muntha. CF.M9.1 [VARSHA_KUNDALI_PENDING]: 2026 Varsha Kundali requires Swiss Ephemeris solar return computation.",
        "kp":        "Krishnamurti Paddhati isolates the sub-lord of each house cusp as the primary indicator for that domain. KP reads fructification potential through sub-lord activation percentages — a house's sub-lord in a favourable constellation + signification determines whether the house 'gives its result'.",
        "nadi":      "Nadi Jyotish reads house-from-planet chains — counting houses from each natal planet to other planets to determine domain signatures. Nadi uses the fewest signals (1.2% primary coverage) but provides an extremely specific mechanical read when the chain is activated.",
        "bnn":       "Bhrigu Nandi Nadi uses sequential Jupiter→Saturn transit activation patterns to time and qualify domain events. BNN requires live transit positions for precision. CF.M9.2 [TRANSIT_DATA_PENDING]: Swiss Ephemeris data for 2026-05-14 transits is pending; current scoring uses natal-position approximations at reduced confidence (0.45×).",
        "yogini":    "The Yogini Dasha system runs a 36-year repeating cycle of 8 Yoginis (1–8 year periods each). The current Yogini at 2026-05-14 is Bhramari (Mars), 0.27 years into a 4-year period. Each Yogini's planetary lord modifies all 5 domain scores through characteristic multipliers.",
    }

    school_section_num = {s: i + 2 for i, s in enumerate(SCHOOLS)}
    for school in SCHOOLS:
        sec = school_section_num[school]
        school_results = {r["domain"]: r for r in data["perSchool"][school]}
        lines += [
            f"## §{sec} — {school.title()} School",
            "",
            f"*{school_philosophy[school]}*",
            "",
            "| Domain | Score | Direction | Top Signal |",
            "|---|---|---|---|",
        ]
        for d in DOMAINS:
            r = school_results[d]
            top = r["topSignals"][0]["signalName"] if r["topSignals"] else "—"
            pending_note = " ⚠️" if r.get("pendingFlags") else ""
            lines.append(f"| {d} | {r['domainScore']:.3f} | {r['direction']}{pending_note} | {top[:60]} |")
        lines += [""]

        for d in DOMAINS:
            r = school_results[d]
            lines += [
                f"### {d}",
                "",
                r["schoolVerdict"],
                "",
            ]
            if r.get("pendingFlags"):
                lines += [f"> ⚠️ Pending: {', '.join(r['pendingFlags'])}", ""]

    # §9 Cross-school comparison table
    lines += [
        "## §9 — Cross-School Comparison Matrix",
        "",
        "Direction per school × domain (▲ positive / ▼ negative / ◆ neutral / ⚠️ pending flag)",
        "",
        "| School | CAREER | HEALTH | RELATIONSHIP | SPIRITUAL | PSYCHOLOGICAL |",
        "|---|---|---|---|---|---|",
    ]
    dir_sym = {"positive": "▲", "negative": "▼", "neutral": "◆"}
    for school in SCHOOLS:
        school_results = {r["domain"]: r for r in data["perSchool"][school]}
        row = [school.title()]
        for d in DOMAINS:
            r = school_results[d]
            sym = dir_sym.get(r["direction"], "?")
            pf = " ⚠️" if r.get("pendingFlags") else ""
            score_str = f"{sym} {r['domainScore']:.2f}{pf}"
            row.append(score_str)
        lines.append("| " + " | ".join(row) + " |")

    lines += [""]

    # §10 Per-domain convergence detail
    lines += [
        "## §10 — Domain Convergence Analysis",
        "",
    ]

    for d in DOMAINS:
        c = conv[d]
        dv = div[d]
        excl_note = f"\n> ⚠️ Tajika excluded (VARSHA_KUNDALI_PENDING). Effective schools: {c['schoolsTotal']}/7." if c["schoolsTotal"] < 7 else ""
        divergence_block = ""
        if dv["isDivergent"]:
            divergence_block = f"\n\n**⚠️ DIVERGENCE DETECTED**: {', '.join(dv['schoolsContradict'])} contradict the plurality direction ({dv['pluralityDirection']}). Dissenting schools: silent={dv['schoolsSilent']}. This divergence should be surfaced explicitly in synthesis."

        all_scores = [f"{r['school']}: {r['domainScore']:.3f}" for r in data["perDomain"][d]]

        lines += [
            f"### {d}",
            "",
            f"- **Convergence Level**: {convergence_badge(c['convergenceLevel'])}",
            f"- **Schools Agreeing**: {c['schoolsAgreeing']}/{c['schoolsTotal']} (direction: {direction_symbol(c['direction'])})",
            f"- **Mean Score**: {c['meanDomainScore']:.3f}/5.0 (σ={c['stdDomainScore']:.3f})",
            f"- **Per-School Scores**: {'; '.join(all_scores)}",
            excl_note,
            divergence_block,
            "",
        ]

    # §11 Deferred items
    lines += [
        "## §11 — Deferred Items + Next Steps",
        "",
        "| Item | Status | Resolution |",
        "|---|---|---|",
        "| DB insertion (school_analysis_runs 35 rows) | DEFERRED | Proxy unavailable at M9-C-S1; script written; execute when proxy available |",
        "| GCS upload (L9/school_analyses/ 7 JSON files) | DEFERRED | Proxy unavailable at M9-C-S1 |",
        "| CF.M9.1 [VARSHA_KUNDALI_PENDING] | OPEN | Tajika Varsha Kundali 2026 via Swiss Ephemeris; pending native action |",
        "| CF.M9.2 [TRANSIT_DATA_PENDING] | OPEN | BNN 2026-05-14 transit positions via Swiss Ephemeris; pending native action |",
        "| M9-D: Convergence scoring + Tool 27+28 full impl | INCOMING | Next session |",
        "",
        "*End MULTI_SCHOOL_ANALYSIS_v1_0.md. M9-C-S1 (2026-05-14).*",
        "",
    ]

    out_path = os.path.join(output_dir, "MULTI_SCHOOL_ANALYSIS_v1_0.md")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"  Markdown → {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="M9-C-S1 Multi-School Analysis Runner")
    parser.add_argument("--output-dir", default=None, help="Output directory for JSON + markdown")
    parser.add_argument("--json-only", action="store_true", help="Skip markdown, write JSON only")
    args = parser.parse_args()

    # Resolve output dir relative to repo root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))

    output_dir = args.output_dir or os.path.join(repo_root, "09_MULTI_SCHOOL_TRIANGULATION")
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n=== M9-C-S1: Multi-School Analysis ===")
    print(f"Chart: {ABHISEK_CHART['chartId']} ({ABHISEK_CHART['birthDate']})")
    print(f"Schools: {', '.join(SCHOOLS)}")
    print(f"Domains: {', '.join(DOMAINS)}")
    print(f"Output: {output_dir}")
    print()

    print("Running 35 analysis combinations:")
    data = run_all_schools(ABHISEK_CHART)

    print(f"\nTotal runs: {data['totalRuns']} ✓")
    print("\nConvergence summary:")
    for d in DOMAINS:
        c = data["convergence"][d]
        dv = data["divergence"][d]
        div_flag = " [DIVERGENT]" if dv["isDivergent"] else ""
        print(f"  {d:14s}: {c['convergenceLevel']:6s} {c['schoolsAgreeing']}/{c['schoolsTotal']} agree, dir={c['direction']}, mean={c['meanDomainScore']:.3f}{div_flag}")

    print("\nWriting per-school JSON files:")
    for school in SCHOOLS:
        write_school_json(school, data["perSchool"][school], output_dir)

    if not args.json_only:
        print("\nWriting MULTI_SCHOOL_ANALYSIS_v1_0.md:")
        write_multi_school_analysis_md(data, output_dir)

    print("\n=== M9-C-S1 COMPLETE ===")
    print(f"  DB insertion: DEFERRED (proxy unavailable)")
    print(f"  GCS upload:   DEFERRED (proxy unavailable)")
    print(f"  CF.M9.1:      [VARSHA_KUNDALI_PENDING] — Tajika at reduced confidence")
    print(f"  CF.M9.2:      [TRANSIT_DATA_PENDING] — BNN at reduced confidence")
    return 0


if __name__ == "__main__":
    sys.exit(main())
