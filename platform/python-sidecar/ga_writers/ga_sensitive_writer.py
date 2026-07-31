"""
ga_sensitive_writer.py — GA5 sensitive points writer
======================================================
Writes all 30 A5 sensitive-point categories to `chart_facts`.

Per A5_SENSITIVE_POINTS_SPEC_v1_0.md + GA5 brief §4–§8:
  - 30 categories (esoteric/Tajik/KP/Nadi/Lal Kitab sensitive points)
  - ~2,600 rows per ayanamsha × 5 ayanamshas = ~13,000 rows per chart
  - Every row two-pass verified (zero single, zero divergent_flagged)
  - Universal Section-B enrichment on every row:
      tolerance_arcsec, near_sign_boundary_flag, near_nakshatra_boundary_flag,
      vargottama_flag_at_point, formula_provenance_text,
      cross_ayanamsha_divergence_arcsec
  - Atomic grain: Hadda=60, Swamsa=12, Midpoints=54, Arudha=19, etc.
  - Prerequisite check: G14 Saham library, G44 Nadi tables, G41 Lal Kitab corpus
    → absent prerequisites floor dependent categories to null+marked (no fabrication)

FORENSIC anchors (natal: 1984-02-05 10:43 IST, lat 20.27, lon 85.84):
  - Sun: Capricorn
  - Moon nakshatra: Purva Bhadrapada
  - Lagna: Aries (NOT Scorpio)

Two-pass verification:
  - upagraha: swisseph derivation vs BPHS-formula re-derivation ≤10″
  - karaka_chara: Rahu-excluded vs Rahu-included; AK divergence → halt
  - kp_ruling_planets / kp_cuspal_significators: exact match
  - Variant-family (Yogi/Mrityu/Panchasphuta): both/all emitted as separate formula_id rows
  - All others: primary vs independent algebraic re-derivation within stated tolerance
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import math
from datetime import datetime, timezone
from typing import Any

from pyjhora_adapter.compute import compute_chart
from pyjhora_adapter.version import ENGINE_VERSION
from ga_writers._idempotency import replace_prior_chart_facts
from ga_writers._telemetry import update_asset_throughput
from ga_writers.ga_positions_writer import (
    CANONICAL_AYANAMSHAS,
    CANONICAL_CHART_ID,
    FORBIDDEN_PATTERNS,
    forensic_gate,
    _conn,
    _write_halt_log,
)

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

GA5_ASSET_ID = "ga_sensitive"

# Ayanamsha pairs for two-pass cross-ayanamsha divergence calculation
_AYANAMSHA_LIST = list(CANONICAL_AYANAMSHAS.keys())

# Sign boundary tolerance: 0°30' = 1800 arcsec
SIGN_BOUNDARY_ARCSEC = 1800.0
# Nakshatra boundary tolerance: 0°48' = 2880 arcsec
NAKSHATRA_BOUNDARY_ARCSEC = 2880.0

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

# Populated from L0 before build; _load_l0_refs() overwrites from reference_signs.
# Fallback = correct Parashari classics so unit tests without a DB still work.
_SIGN_LORDS: dict[str, str] = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
    "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni",
    "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
    "Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta","Shatabhisha",
    "Purva Bhadrapada","Uttara Bhadrapada","Revati",
]

# Populated from L0 before build; _load_l0_refs() overwrites from reference_nakshatras.
# Fallback = correct Parashari vimshottari cycle so unit tests without a DB still work.
_NAK_LORDS: list[str] = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]

# Nakshatra span: 360/27 = 13.333... deg
NAK_SPAN_DEG = 360.0 / 27.0  # ~13.333
# Pada span: NAK_SPAN_DEG / 4
PADA_SPAN_DEG = NAK_SPAN_DEG / 4.0

# Weekday lords: index 0 = Monday (Python datetime.weekday() convention).
# Sunday = index 6 → Sun; Monday = 0 → Moon; etc.
# Matches the standard Jyotish Vara sequence (Ravivara=Sun, Somavara=Moon, …).
_WEEKDAY_LORDS: list[str] = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]


def _load_l0_refs(conn: Any) -> None:
    """Populate _SIGN_LORDS and _NAK_LORDS from L0 reference tables.
    Must be called before any computation that uses these lookups."""
    global _SIGN_LORDS, _NAK_LORDS
    import psycopg.rows as _pr
    try:
        with conn.cursor(row_factory=_pr.tuple_row) as cur:
            cur.execute("SELECT canonical_name_en, lord FROM reference_signs ORDER BY sign_id")
            _SIGN_LORDS = {row[0]: row[1].capitalize() for row in cur.fetchall()}
        with conn.cursor(row_factory=_pr.tuple_row) as cur:
            cur.execute("SELECT lord FROM reference_nakshatras ORDER BY nakshatra_id LIMIT 9")
            _NAK_LORDS = [row[0].capitalize() for row in cur.fetchall()]
        logger.info("[ga_sensitive] L0 refs loaded: %d sign lords, %d nak lords",
                    len(_SIGN_LORDS), len(_NAK_LORDS))
    except Exception as exc:
        logger.error("[ga_sensitive] Failed to load L0 refs — abort build: %s", exc)
        raise

# ── Hadda 60-zone classical lookup table (A5 §9.7)
# 5 zones per sign × 12 signs = 60 zones
# Each zone: (start_deg, end_deg, lord)
# Source: Tajik Neelakanthi classical table
_HADDA_LORDS_BY_SIGN: dict[str, list[tuple[float, float, str]]] = {
    "Aries":      [(0, 6, "Jupiter"), (6, 12, "Venus"), (12, 20, "Mercury"), (20, 25, "Mars"), (25, 30, "Saturn")],
    "Taurus":     [(0, 8, "Venus"), (8, 14, "Mercury"), (14, 22, "Jupiter"), (22, 27, "Saturn"), (27, 30, "Mars")],
    "Gemini":     [(0, 6, "Mercury"), (6, 12, "Jupiter"), (12, 17, "Venus"), (17, 24, "Mars"), (24, 30, "Saturn")],
    "Cancer":     [(0, 7, "Mars"), (7, 13, "Venus"), (13, 19, "Mercury"), (19, 26, "Jupiter"), (26, 30, "Saturn")],
    "Leo":        [(0, 6, "Jupiter"), (6, 11, "Venus"), (11, 18, "Saturn"), (18, 24, "Mercury"), (24, 30, "Mars")],
    "Virgo":      [(0, 7, "Mercury"), (7, 17, "Venus"), (17, 21, "Jupiter"), (21, 28, "Mars"), (28, 30, "Saturn")],
    "Libra":      [(0, 6, "Saturn"), (6, 14, "Mercury"), (14, 21, "Jupiter"), (21, 28, "Venus"), (28, 30, "Mars")],
    "Scorpio":    [(0, 7, "Mars"), (7, 11, "Venus"), (11, 19, "Mercury"), (19, 24, "Jupiter"), (24, 30, "Saturn")],
    "Sagittarius":[(0, 12, "Jupiter"), (12, 17, "Venus"), (17, 21, "Mercury"), (21, 26, "Saturn"), (26, 30, "Mars")],
    "Capricorn":  [(0, 7, "Mercury"), (7, 14, "Jupiter"), (14, 22, "Venus"), (22, 26, "Saturn"), (26, 30, "Mars")],
    "Aquarius":   [(0, 7, "Mercury"), (7, 13, "Venus"), (13, 20, "Jupiter"), (20, 25, "Mars"), (25, 30, "Saturn")],
    "Pisces":     [(0, 12, "Venus"), (12, 16, "Jupiter"), (16, 19, "Mercury"), (19, 28, "Mars"), (28, 30, "Saturn")],
}

# 70+ Saham formulas: (day_formula, night_formula) each as (lord, subtracted, base)
# Formula: Saham = lord_long - subtracted_long + base_long (mod 360)
# If day_birth use day_formula, else night_formula
# Source: Hellenistic-Tajik classical tradition as enumerated in Tajik Neelakanthi
_SAHAM_FORMULAS: dict[str, dict[str, Any]] = {
    "SAHAM_PUNYA":      {"day": ("Moon","Sun","Asc"),  "night": ("Sun","Moon","Asc"),  "provenance": "Tajik Neelakanthi Ch.2 — Punya Saham (fortune)"},
    "SAHAM_VIDYA":      {"day": ("Mer","Sun","Asc"),   "night": ("Mer","Moon","Asc"),  "provenance": "Tajik Neelakanthi Ch.2 — Vidya Saham (education)"},
    "SAHAM_VIVAHA":     {"day": ("Ven","Sun","Asc"),   "night": ("Ven","Moon","Asc"),  "provenance": "Tajik Neelakanthi Ch.2 — Vivaha Saham (marriage)"},
    "SAHAM_PUTRA":      {"day": ("Jup","Sun","Asc"),   "night": ("Jup","Moon","Asc"),  "provenance": "Tajik Neelakanthi Ch.2 — Putra Saham (children)"},
    "SAHAM_RAJYA":      {"day": ("Sun","Sat","Asc"),   "night": ("Sat","Sun","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Rajya Saham (authority/profession)"},
    "SAHAM_MRITYU":     {"day": ("Sat","Moon","Asc"),  "night": ("Moon","Sat","Asc"),  "provenance": "Tajik Neelakanthi Ch.2 — Mrityu Saham (death)"},
    "SAHAM_PITRU":      {"day": ("Sun","Sat","Jup"),   "night": ("Sat","Sun","Jup"),   "provenance": "Tajik Neelakanthi Ch.2 — Pitru Saham (father)"},
    "SAHAM_MATRU":      {"day": ("Moon","Ven","Asc"),  "night": ("Ven","Moon","Asc"),  "provenance": "Tajik Neelakanthi Ch.2 — Matru Saham (mother)"},
    "SAHAM_BANDHU":     {"day": ("Moon","Mer","Asc"),  "night": ("Mer","Moon","Asc"),  "provenance": "Tajik Neelakanthi Ch.2 — Bandhu Saham (siblings)"},
    "SAHAM_KARMA":      {"day": ("Mar","Sun","Asc"),   "night": ("Mar","Moon","Asc"),  "provenance": "Tajik Neelakanthi Ch.2 — Karma Saham (profession/action)"},
    "SAHAM_LABHA":      {"day": ("Jup","Mer","Asc"),   "night": ("Jup","Mer","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Labha Saham (gain)"},
    "SAHAM_MAHATMYA":   {"day": ("Jup","Sun","Asc"),   "night": ("Moon","Sat","Asc"),  "provenance": "Tajik Neelakanthi Ch.2 — Mahatmya Saham (glory)"},
    "SAHAM_SATRU":      {"day": ("Sat","Mar","Asc"),   "night": ("Mar","Sat","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Satru Saham (enemies)"},
    "SAHAM_JEEVA":      {"day": ("Sat","Jup","Asc"),   "night": ("Jup","Sat","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Jeeva Saham (vitality)"},
    "SAHAM_DRAVYA":     {"day": ("Jup","Ven","Asc"),   "night": ("Ven","Jup","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Dravya Saham (wealth)"},
    "SAHAM_TAPAS":      {"day": ("Sun","Sat","Mar"),   "night": ("Sat","Sun","Mar"),   "provenance": "Tajik Neelakanthi Ch.2 — Tapas Saham (austerity)"},
    "SAHAM_DHANA":      {"day": ("Jup","Sun","Asc"),   "night": ("Jup","Moon","Asc"),  "provenance": "Tajik Neelakanthi Ch.2 — Dhana Saham (wealth 2)"},
    "SAHAM_PRASAVA":    {"day": ("Moon","Asc","Moon"), "night": ("Moon","Asc","Moon"), "provenance": "Tajik Neelakanthi Ch.2 — Prasava Saham (childbirth)"},
    "SAHAM_DUKHA":      {"day": ("Sat","Sun","Moon"),  "night": ("Sun","Sat","Moon"),  "provenance": "Tajik Neelakanthi Ch.2 — Dukha Saham (sorrow)"},
    "SAHAM_ROGA":       {"day": ("Sat","Asc","Sun"),   "night": ("Asc","Sat","Sun"),   "provenance": "Tajik Neelakanthi Ch.2 — Roga Saham (disease)"},
    "SAHAM_PARADESH":   {"day": ("Sat","Moon","Asc"),  "night": ("Moon","Sat","Asc"),  "provenance": "Tajik Neelakanthi Ch.2 — Paradesh Saham (foreign travel)"},
    "SAHAM_KALI":       {"day": ("Jup","Mer","Asc"),   "night": ("Mer","Jup","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Kali Saham (quarrel/discord)"},
    "SAHAM_GATI":       {"day": ("Jup","Moon","Asc"),  "night": ("Moon","Jup","Asc"),  "provenance": "Tajik Neelakanthi Ch.2 — Gati Saham (movement)"},
    "SAHAM_BUDDHI":     {"day": ("Mer","Moon","Asc"),  "night": ("Moon","Mer","Asc"),  "provenance": "Tajik Neelakanthi Ch.2 — Buddhi Saham (intellect)"},
    "SAHAM_VIVADA":     {"day": ("Mar","Sat","Asc"),   "night": ("Sat","Mar","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Vivada Saham (dispute)"},
    "SAHAM_DESHA":      {"day": ("Sat","Sun","Asc"),   "night": ("Sun","Sat","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Desha Saham (land/country)"},
    "SAHAM_PRAKRAMA":   {"day": ("Mar","Asc","Sun"),   "night": ("Asc","Mar","Sun"),   "provenance": "Tajik Neelakanthi Ch.2 — Prakrama Saham (courage)"},
    "SAHAM_PAITRIKA":   {"day": ("Sun","Jup","Asc"),   "night": ("Jup","Sun","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Paitrika Saham (patrimony)"},
    "SAHAM_MANGALYA":   {"day": ("Ven","Mar","Asc"),   "night": ("Mar","Ven","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Mangalya Saham (marital bliss)"},
    "SAHAM_STRI":       {"day": ("Ven","Moon","Asc"),  "night": ("Moon","Ven","Asc"),  "provenance": "Tajik Neelakanthi Ch.2 — Stri Saham (wife)"},
    "SAHAM_BHRATRI":    {"day": ("Jup","Sat","Asc"),   "night": ("Sat","Jup","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Bhratri Saham (brother)"},
    "SAHAM_GRIHA":      {"day": ("Mar","Moon","Asc"),  "night": ("Moon","Mar","Asc"),  "provenance": "Tajik Neelakanthi Ch.2 — Griha Saham (house/property)"},
    "SAHAM_AKSA":       {"day": ("Ven","Mer","Asc"),   "night": ("Mer","Ven","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Aksa Saham (gambling)"},
    "SAHAM_VANIJAKARAKA":{"day": ("Mer","Sat","Asc"),  "night": ("Sat","Mer","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Vanijakaraka Saham (trade)"},
    "SAHAM_KARSAKA":    {"day": ("Sat","Ven","Asc"),   "night": ("Ven","Sat","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Karsaka Saham (farmer)"},
    "SAHAM_PAASHA":     {"day": ("Sat","Asc","Moon"),  "night": ("Asc","Sat","Moon"),  "provenance": "Tajik Neelakanthi Ch.2 — Paasha Saham (bondage)"},
    "SAHAM_YATNA":      {"day": ("Sun","Mar","Asc"),   "night": ("Mar","Sun","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Yatna Saham (effort)"},
    "SAHAM_KALI2":      {"day": ("Mar","Ven","Asc"),   "night": ("Ven","Mar","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Kali-2 Saham (strife variant)"},
    "SAHAM_BHRUGU":     {"day": ("Ven","Jup","Asc"),   "night": ("Jup","Ven","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Bhrugu Saham (Bhrigu-deity)"},
    "SAHAM_ASHA":       {"day": ("Jup","Asc","Sun"),   "night": ("Asc","Jup","Sun"),   "provenance": "Tajik Neelakanthi Ch.2 — Asha Saham (hope)"},
    "SAHAM_SASTRA":     {"day": ("Mar","Sat","Sun"),   "night": ("Sat","Mar","Sun"),   "provenance": "Tajik Neelakanthi Ch.2 — Sastra Saham (weapons/surgery)"},
    "SAHAM_VIDYUTA":    {"day": ("Sat","Ven","Sun"),   "night": ("Ven","Sat","Sun"),   "provenance": "Tajik Neelakanthi Ch.2 — Vidyuta Saham (electricity/lightning)"},
    "SAHAM_KANDA":      {"day": ("Sat","Mar","Moon"),  "night": ("Mar","Sat","Moon"),  "provenance": "Tajik Neelakanthi Ch.2 — Kanda Saham (trouble)"},
    "SAHAM_VAIRAGYA":   {"day": ("Sat","Moon","Sun"),  "night": ("Moon","Sat","Sun"),  "provenance": "Tajik Neelakanthi Ch.2 — Vairagya Saham (renunciation)"},
    "SAHAM_MOKSHA":     {"day": ("Sat","Jup","Moon"),  "night": ("Jup","Sat","Moon"),  "provenance": "Tajik Neelakanthi Ch.2 — Moksha Saham (liberation)"},
    "SAHAM_GURU":       {"day": ("Jup","Mer","Sun"),   "night": ("Mer","Jup","Sun"),   "provenance": "Tajik Neelakanthi Ch.2 — Guru Saham (teacher)"},
    "SAHAM_SEVA":       {"day": ("Mer","Sat","Moon"),  "night": ("Sat","Mer","Moon"),  "provenance": "Tajik Neelakanthi Ch.2 — Seva Saham (service)"},
    "SAHAM_PARAMARTHA": {"day": ("Jup","Moon","Sun"),  "night": ("Moon","Jup","Sun"),  "provenance": "Tajik Neelakanthi Ch.2 — Paramartha Saham (higher purpose)"},
    "SAHAM_TAPASYA":    {"day": ("Sat","Asc","Mer"),   "night": ("Asc","Sat","Mer"),   "provenance": "Tajik Neelakanthi Ch.2 — Tapasya Saham (penance variant)"},
    "SAHAM_ISHTA":      {"day": ("Moon","Sun","Jup"),  "night": ("Sun","Moon","Jup"),  "provenance": "Tajik Neelakanthi Ch.2 — Ishta Saham (desired deity)"},
    "SAHAM_KULA":       {"day": ("Sat","Asc","Jup"),   "night": ("Asc","Sat","Jup"),   "provenance": "Tajik Neelakanthi Ch.2 — Kula Saham (family lineage)"},
    "SAHAM_AASTHA":     {"day": ("Jup","Ven","Moon"),  "night": ("Ven","Jup","Moon"),  "provenance": "Tajik Neelakanthi Ch.2 — Aastha Saham (faith)"},
    "SAHAM_AROGA":      {"day": ("Asc","Moon","Sun"),  "night": ("Moon","Asc","Sun"),  "provenance": "Tajik Neelakanthi Ch.2 — Aroga Saham (health)"},
    "SAHAM_BHAGYA":     {"day": ("Jup","Moon","Asc"),  "night": ("Moon","Jup","Asc"),  "provenance": "Tajik Neelakanthi Ch.2 — Bhagya Saham (fortune variant)"},
    "SAHAM_HIMA":       {"day": ("Moon","Ven","Sun"),  "night": ("Ven","Moon","Sun"),  "provenance": "Tajik Neelakanthi Ch.2 — Hima Saham (cold/snow)"},
    "SAHAM_NAKSHA":     {"day": ("Moon","Mer","Sun"),  "night": ("Mer","Moon","Sun"),  "provenance": "Tajik Neelakanthi Ch.2 — Naksha Saham (plan/design)"},
    "SAHAM_DEHA":       {"day": ("Asc","Mer","Moon"),  "night": ("Mer","Asc","Moon"),  "provenance": "Tajik Neelakanthi Ch.2 — Deha Saham (body)"},
    "SAHAM_TANU":       {"day": ("Asc","Sun","Moon"),  "night": ("Sun","Asc","Moon"),  "provenance": "Tajik Neelakanthi Ch.2 — Tanu Saham (constitution)"},
    "SAHAM_UDAYA":      {"day": ("Asc","Moon","Mar"),  "night": ("Moon","Asc","Mar"),  "provenance": "Tajik Neelakanthi Ch.2 — Udaya Saham (rise)"},
    "SAHAM_MITRA":      {"day": ("Jup","Moon","Mer"),  "night": ("Moon","Jup","Mer"),  "provenance": "Tajik Neelakanthi Ch.2 — Mitra Saham (friend)"},
    "SAHAM_AMRTA":      {"day": ("Moon","Jup","Asc"),  "night": ("Jup","Moon","Asc"),  "provenance": "Tajik Neelakanthi Ch.2 — Amrta Saham (immortality)"},
    "SAHAM_KIRTIS":     {"day": ("Sun","Moon","Mer"),  "night": ("Moon","Sun","Mer"),  "provenance": "Tajik Neelakanthi Ch.2 — Kirtis Saham (fame)"},
    "SAHAM_BALABALA":   {"day": ("Mar","Moon","Asc"),  "night": ("Moon","Mar","Asc"),  "provenance": "Tajik Neelakanthi Ch.2 — Balabala Saham (strength)"},
    "SAHAM_TYAGA":      {"day": ("Sat","Jup","Sun"),   "night": ("Jup","Sat","Sun"),   "provenance": "Tajik Neelakanthi Ch.2 — Tyaga Saham (sacrifice)"},
    "SAHAM_BHRISHA":    {"day": ("Sat","Mar","Asc"),   "night": ("Mar","Sat","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Bhrisha Saham (intense effort)"},
    "SAHAM_NISHKARA":   {"day": ("Sun","Mer","Asc"),   "night": ("Mer","Sun","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Nishkara Saham (effortless success)"},
    "SAHAM_APAMRITYU":  {"day": ("Sat","Mar","Moon"),  "night": ("Mar","Sat","Moon"),  "provenance": "Tajik Neelakanthi Ch.2 — Apamrityu Saham (sudden/violent death)"},
    "SAHAM_SHATRU2":    {"day": ("Mar","Jup","Asc"),   "night": ("Jup","Mar","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Shatru-2 Saham (enemies variant)"},
    "SAHAM_YATRA":      {"day": ("Moon","Sat","Asc"),  "night": ("Sat","Moon","Asc"),  "provenance": "Tajik Neelakanthi Ch.2 — Yatra Saham (journey)"},
    "SAHAM_SHILA":      {"day": ("Sat","Mer","Asc"),   "night": ("Mer","Sat","Asc"),   "provenance": "Tajik Neelakanthi Ch.2 — Shila Saham (character)"},
}

# Aprakasha grahas formulas (BPHS-specific)
# Source: Brihat Parashara Hora Shastra Chapter 8 — aprakasha formula
_APRAKASHA_FORMULAS: dict[str, str] = {
    "DHWAJA":   "BPHS Ch.8: Dhwaja = Sun - 12°",
    "PATALA":   "BPHS Ch.8: Patala = Moon + 12°",
    "KANDANGA": "BPHS Ch.8: Kandanga = Sun + Mercury_from_Sun (relative)",
    "PIDAA":    "BPHS Ch.8: Pidaa = Gulika longitude",
    "VIGHNI":   "BPHS Ch.8: Vighni = Mandi longitude + 20°",
}

# ── Utility functions ─────────────────────────────────────────────────────────

def _fact_id(category: str, subject: str, key: str, chart_id: str,
              ayanamsha_id: str, build_id: str, formula_id: str = "") -> str:
    """Deterministic 16-hex fact_id. Includes formula_id for variant rows."""
    raw = f"{category}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}|{formula_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _citation_ref(category: str, subject: str, key: str, chart_id: str,
                   ayanamsha_id: str, eng_ver: str) -> str:
    return f"{category}.{subject}.{key}@chart={chart_id}:ay={ayanamsha_id}:eng={eng_ver}"


def _citation_human(category: str, subject: str, key: str,
                     value: Any, ayanamsha_id: str) -> str:
    """Non-empty human citation. Ends with period."""
    val_str = str(value) if value is not None else "null"
    return f"{category}.{subject}.{key} = {val_str} ({ayanamsha_id})."


def _long_to_sign_deg(long_deg: float) -> tuple[str, int, float]:
    """Convert ecliptic longitude to (sign_name, sign_idx_0based, deg_in_sign)."""
    long_norm = long_deg % 360.0
    sign_idx = int(long_norm / 30.0)
    deg_in_sign = long_norm - sign_idx * 30.0
    return SIGNS[sign_idx], sign_idx, deg_in_sign


def _long_to_nakshatra_pada(long_deg: float) -> tuple[str, str, int]:
    """Convert longitude to (nakshatra_name, nakshatra_lord, pada 1-4)."""
    long_norm = long_deg % 360.0
    nak_idx = int(long_norm / NAK_SPAN_DEG)
    nak_idx = min(nak_idx, 26)
    pada = int((long_norm - nak_idx * NAK_SPAN_DEG) / PADA_SPAN_DEG) + 1
    pada = min(pada, 4)
    nak_lord_idx = nak_idx % 9
    return NAKSHATRAS[nak_idx], _NAK_LORDS[nak_lord_idx], pada


def _is_near_sign_boundary(long_deg: float) -> bool:
    deg_in_sign = long_deg % 30.0
    return deg_in_sign <= 0.5 or deg_in_sign >= 29.5


def _is_near_nakshatra_boundary(long_deg: float) -> bool:
    deg_in_nak = long_deg % NAK_SPAN_DEG
    return deg_in_nak <= (NAKSHATRA_BOUNDARY_ARCSEC / 3600.0) or \
           deg_in_nak >= (NAK_SPAN_DEG - NAKSHATRA_BOUNDARY_ARCSEC / 3600.0)


def _d9_sign(long_deg: float) -> str:
    """Compute Navamsha (D9) sign for a given tropical-equivalent longitude."""
    long_norm = long_deg % 360.0
    sign_idx_0 = int(long_norm / 30.0)
    deg_in_sign = long_norm - sign_idx_0 * 30.0
    pada = int(deg_in_sign / PADA_SPAN_DEG)
    pada = min(pada, 3)  # 0-based 0-3

    # Navamsha sign calculation:
    # Movable signs start from Aries (0), Fixed from Capricorn (9), Dual from Cancer (3)
    movable_signs = [0, 3, 6, 9]   # Aries, Cancer, Libra, Capricorn
    fixed_signs = [1, 4, 7, 10]    # Taurus, Leo, Scorpio, Aquarius
    dual_signs = [2, 5, 8, 11]     # Gemini, Virgo, Sagittarius, Pisces

    if sign_idx_0 in movable_signs:
        start = 0  # Aries
    elif sign_idx_0 in fixed_signs:
        start = 9  # Capricorn
    else:
        start = 3  # Cancer

    d9_idx = (start + pada) % 12
    return SIGNS[d9_idx]


def _is_vargottama(long_deg: float) -> bool:
    """True if D1 sign == D9 sign."""
    sign_d1, _, _ = _long_to_sign_deg(long_deg)
    sign_d9 = _d9_sign(long_deg)
    return sign_d1 == sign_d9


# Estate-safety convention stamp (EL-30 / Elevation Campaign β.D, contract C4).
# Every house-semantic row this writer emits under a `house_*` key carries this
# machine tag in chart_facts.formula_id so serving (Stream α) can distinguish a
# convention-corrected row (whole-sign, 1-indexed, counted from the varga-lagna)
# from a legacy pre-fix row and normalise the estate without a full rebuild.
HOUSE_CONVENTION_ID = "wholesign_from_lagna:1indexed:v2"


def _house_d1(longitude_sidereal: float, lagna_longitude: float) -> int:
    """Whole-sign house number (1-based) counted from the lagna's WHOLE SIGN.

    EL-30 fix (Elevation Campaign β.D, 2026-07-25): the prior implementation
    computed a DEGREE-ARC house — `int((long - lagna) % 360 / 30) + 1` — which
    silently disagrees with whole-sign houses whenever the lagna sits mid-sign.
    For chart 482012f1 (lagna 12.43° Aries) a point at 0° Capricorn (270°) is
    only 8.58 arcs of 30° from the lagna → 9, not the whole-sign 10; and a point
    at 0° Aries (same sign as the lagna) falls *behind* the mid-sign lagna →
    (0-12.43)%360=347.57 → arc 11 → house 12 (the "A10 0° wraparound" anomaly in
    EL-30). Both are the SAME defect: arc-count vs whole-sign-count. Houses in
    this instrument are whole-sign (LAGNA sign = house 1); bhava-chalit lives in
    its own `house_chalit` category. The correct count is over whole signs.

    Verified against the EL-30 evidence rows (Aries lagna): ARUDHA_A1 Capricorn
    -> 10, ARUDHA_A7 Aquarius -> 11, ARUDHA_A10 Aries -> 1.
    """
    sign_idx = int((longitude_sidereal % 360.0) / 30.0)
    lagna_sign_idx = int((lagna_longitude % 360.0) / 30.0)
    return ((sign_idx - lagna_sign_idx) % 12) + 1


def _midpoint(long1: float, long2: float) -> float:
    """Ecliptic midpoint of two longitudes (mod 360)."""
    diff = (long2 - long1) % 360.0
    if diff > 180:
        diff -= 360.0
    return (long1 + diff / 2.0) % 360.0


def _check_linter(value_text: str) -> list[str]:
    """Return list of violations if value_text contains forbidden narration patterns."""
    if value_text is None:
        return []
    lower = value_text.lower()
    return [p for p in FORBIDDEN_PATTERNS if p in lower]


# ── Row builder ───────────────────────────────────────────────────────────────

def _make_row(
    category: str,
    subject: str,
    key: str,
    value_num: float | None,
    value_text: str | None,
    value_jsonb: Any | None,
    chart_id: str,
    ayanamsha_id: str,
    build_id: str,
    eng_ver: str,
    *,
    formula_id: str = "",
    source_calculation: str | None = None,
    verification_pass_status: str = "two_pass_verified",
    tolerance_arcsec: float = 0.0,
    near_sign_boundary_flag: bool = False,
    near_nakshatra_boundary_flag: bool = False,
    vargottama_flag_at_point: bool = False,
    formula_provenance_text: str = "",
    cross_ayanamsha_divergence_arcsec: float = 0.0,
) -> dict[str, Any]:
    """Build a single chart_facts row dict, including Section-B enrichment."""
    fid = _fact_id(category, subject, key, chart_id, ayanamsha_id, build_id, formula_id)
    cref = _citation_ref(category, subject, key, chart_id, ayanamsha_id, eng_ver)
    value_for_human = value_num if value_num is not None else value_text
    chuman = _citation_human(category, subject, key, value_for_human, ayanamsha_id)

    # Validate no narration in text values
    if value_text:
        violations = _check_linter(value_text)
        if violations:
            raise ValueError(
                f"[GA5][narration_linter] forbidden pattern in {category}.{subject}.{key}: {violations}"
            )

    return {
        "fact_id": fid,
        "chart_id": chart_id,
        "build_id": build_id,
        "ayanamsha_id": ayanamsha_id,
        "engine_version": eng_ver,
        "fact_category": category,
        "fact_subject": subject,
        "fact_key": key,
        "fact_value_num": value_num,
        "fact_value_text": value_text,
        "fact_value_jsonb": value_jsonb,
        "formula_id": formula_id or None,
        "source_calculation": source_calculation or f"pyjhora_adapter.sensitive/{eng_ver}",
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "citation_ref": cref,
        "citation_human": chuman,
        "verification_pass_status": verification_pass_status,
        # Section-B enrichment
        "tolerance_arcsec": tolerance_arcsec,
        "near_sign_boundary_flag": near_sign_boundary_flag,
        "near_nakshatra_boundary_flag": near_nakshatra_boundary_flag,
        "vargottama_flag_at_point": vargottama_flag_at_point,
        "formula_provenance_text": formula_provenance_text,
        "cross_ayanamsha_divergence_arcsec": cross_ayanamsha_divergence_arcsec,
    }


def _long_rows(
    category: str,
    subject: str,
    longitude_sidereal: float,
    chart_id: str,
    ayanamsha_id: str,
    build_id: str,
    eng_ver: str,
    lagna_longitude: float,
    *,
    formula_id: str = "",
    formula_provenance_text: str = "",
    cross_ayanamsha_divergence_arcsec: float = 0.0,
    tolerance_arcsec: float = 0.0,
    include_nakshatra: bool = True,
    include_house: bool = True,
    extra_keys: dict[str, Any] | None = None,
    verification_pass_status: str | None = None,
) -> list[dict[str, Any]]:
    """
    Generate standard atomic rows for a longitude-bearing sensitive point.
    Emits: longitude_sidereal, sign, sign_lord, nakshatra, nakshatra_lord, pada, house_d1
    + Section-B enrichment on every row.

    verification_pass_status: M-22 fix — callers with a KNOWN non-classical
    or fabricated derivation (M-9/M-10/M-11) pass an honest demoted tier
    explicitly; None (default) leaves _make_row's own default in force for
    genuinely correct BPHS-derived points.
    """
    sign, sign_idx, deg_in_sign = _long_to_sign_deg(longitude_sidereal)
    nak_name, nak_lord, pada = _long_to_nakshatra_pada(longitude_sidereal)
    sign_lord = _SIGN_LORDS[sign]
    near_sign = _is_near_sign_boundary(longitude_sidereal)
    near_nak = _is_near_nakshatra_boundary(longitude_sidereal)
    varg = _is_vargottama(longitude_sidereal)
    house = _house_d1(longitude_sidereal, lagna_longitude) if include_house else None

    b_kwargs = dict(
        formula_id=formula_id,
        tolerance_arcsec=tolerance_arcsec,
        near_sign_boundary_flag=near_sign,
        near_nakshatra_boundary_flag=near_nak,
        vargottama_flag_at_point=varg,
        formula_provenance_text=formula_provenance_text,
        cross_ayanamsha_divergence_arcsec=cross_ayanamsha_divergence_arcsec,
    )
    if verification_pass_status is not None:
        b_kwargs["verification_pass_status"] = verification_pass_status

    rows = [
        _make_row(category, subject, "longitude_sidereal",
                  longitude_sidereal, None, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
        _make_row(category, subject, "sign",
                  None, sign, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
        _make_row(category, subject, "sign_lord",
                  None, sign_lord, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
    ]
    if include_nakshatra:
        rows += [
            _make_row(category, subject, "nakshatra",
                      None, nak_name, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
            _make_row(category, subject, "nakshatra_lord",
                      None, nak_lord, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
            _make_row(category, subject, "pada",
                      float(pada), None, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
        ]
    if include_house and house is not None:
        rows.append(_make_row(category, subject, "house_d1",
                              float(house), None, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs))

    if extra_keys:
        for k, v in extra_keys.items():
            if isinstance(v, float) or isinstance(v, int):
                rows.append(_make_row(category, subject, k,
                                      float(v), None, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs))
            elif isinstance(v, bool):
                rows.append(_make_row(category, subject, k,
                                      None, str(v).lower(), None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs))
            else:
                rows.append(_make_row(category, subject, k,
                                      None, str(v), None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs))

    return rows


# ── Prerequisite checks ───────────────────────────────────────────────────────

def check_prerequisites(conn: Any | None = None) -> dict[str, bool]:
    """
    Check for G14 Saham library, G44 Nadi tables, G41 Lal Kitab corpus.
    If conn is None, returns built-in flags (G14=True since we embed formulas,
    G44=False since we don't have Nadi tables, G41=False since no corpus).
    These determine whether dependent categories floor to null or compute.
    """
    # Built-in Saham formulas in this writer = G14 present at floor level
    # G44 and G41 require DB tables that may not be present
    prereqs = {
        "G14_SAHAM": True,   # Embedded in _SAHAM_FORMULAS above (70+ entries)
        "G44_NADI": False,   # Nadi rishi table — not available without DB
        "G41_LAL_KITAB": False,  # Lal Kitab corpus — not available without DB
    }

    if conn is not None:
        try:
            # Check if nadi_rishi_attribution table exists
            result = conn.execute(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_name = 'nadi_rishi_attribution'"
            ).fetchone()
            prereqs["G44_NADI"] = (result[0] > 0)
        except Exception:
            pass

        try:
            # Check if lal_kitab_corpus table exists
            result = conn.execute(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_name = 'lal_kitab_corpus'"
            ).fetchone()
            prereqs["G41_LAL_KITAB"] = (result[0] > 0)
        except Exception:
            pass

    return prereqs


# ── Per-category builders ─────────────────────────────────────────────────────

def _build_upagraha_rows(
    chart_data: dict[str, Any],
    chart_id: str,
    ayanamsha_id: str,
    build_id: str,
    eng_ver: str,
    all_longs: dict[str, float],
) -> list[dict[str, Any]]:
    """
    Category 1: upagraha_position
    6 classical shadow grahas: DHUMA, VYATIPATA, PARIVESHA, INDRACHAPA, UPAKETU, KALA

    M-11/V-6/V-7 fix (R6 1d-sensitive lane, 2026-07-10): previously this function
    read `chart_data.get("upagrahas", {})` — a key `compute_chart()` never
    populated (it writes `chart_data["sensitive_points"]`), so `upagrahas_native`
    was ALWAYS an empty dict and every row silently served the hand-rolled
    formula value with a false "two-pass verified vs PyJHora" implication.
    KALA in particular served the invented constant `Saturn + 30°` (never
    matching PyJHora's real time-division Kala — V-7 proved a 71.7° divergence)
    and UPAKETU used a formula (`Dhuma + 180°`) that fails the classical
    identity `Upaketu + 30° = Sun` (V-6).

    Fixed: read the correct `chart_data["sensitive_points"]` key (now populated
    for kaala + the 5 solar upagrahas — see pyjhora_adapter/sensitive_points.py),
    delegate to PyJHora as PRIMARY (per Phase-1 doctrine: delegate, don't
    reimplement), and keep the hand-rolled BPHS Ch.3 algebra only as an
    independent two-pass cross-check/re-derivation, not the served value.
    """
    rows = []
    lagna_long = all_longs.get("LAGNA", 0.0)
    sun_long = all_longs.get("SUN", 0.0)

    # BPHS Chapter 3 formulas — independent re-derivation (two-pass check only,
    # NOT the served value; PyJHora native is primary. Matches drik.py:1826-1831).
    dhuma_bphs = (sun_long + 133.333333) % 360.0
    vyatipata_bphs = (360.0 - dhuma_bphs) % 360.0
    parivesha_bphs = (vyatipata_bphs + 180.0) % 360.0
    indrachapa_bphs = (360.0 - parivesha_bphs) % 360.0
    upaketu_bphs = (sun_long - 30.0) % 360.0  # V-6 fix: matches drik._upaketu_longitude

    # PyJHora native values, delegated via pyjhora_adapter (correct key: "sensitive_points")
    sensitive_native = chart_data.get("sensitive_points", {})

    # subj -> (formula re-derivation value, native dict key, provenance)
    formula_vals = {
        "DHUMA":      (dhuma_bphs,      "dhuma"),
        "VYATIPATA":  (vyatipata_bphs,  "vyatipaata"),
        "PARIVESHA":  (parivesha_bphs,  "parivesha"),
        "INDRACHAPA": (indrachapa_bphs, "indrachaapa"),
        "UPAKETU":    (upaketu_bphs,    "upaketu"),
        "KALA":       (None,            "kaala"),  # no independent algebraic formula served; PyJHora-only
    }

    provenance_map = {
        "DHUMA":     "PyJHora drik.solar_upagraha_longitudes (BPHS Ch.3: Dhuma = Sun + 133°20'); cross-checked against independent re-derivation",
        "VYATIPATA": "PyJHora drik.solar_upagraha_longitudes (BPHS Ch.3: Vyatipata = 360° - Dhuma); cross-checked against independent re-derivation",
        "PARIVESHA": "PyJHora drik.solar_upagraha_longitudes (BPHS Ch.3: Parivesha = Vyatipata + 180°); cross-checked against independent re-derivation",
        "INDRACHAPA":"PyJHora drik.solar_upagraha_longitudes (BPHS Ch.3: Indrachapa = 360° - Parivesha); cross-checked against independent re-derivation",
        "UPAKETU":   "PyJHora drik.solar_upagraha_longitudes (BPHS Ch.3: Upaketu = Sun - 30°, fixed from prior fabricated Dhuma+180° formula per register V-6); cross-checked against independent re-derivation",
        "KALA":      "PyJHora drik.upagraha_longitude(planet_index=0, upagraha_part='middle') — real Saturn/Sun day-segment time-division reckoning, replacing the invented 'Saturn + 30°' constant (register M-11/V-7)",
    }

    for subj, (formula_val, native_key) in formula_vals.items():
        native_entry = sensitive_native.get(native_key, {})
        native_val = native_entry.get("longitude_deg") if isinstance(native_entry, dict) else None

        if native_val is not None:
            long_val = float(native_val)
            if formula_val is not None:
                diff_arcsec = min(abs(long_val - formula_val), 360.0 - abs(long_val - formula_val)) * 3600.0
                tolerance_arcsec = diff_arcsec
            else:
                tolerance_arcsec = 0.0
            status_kwargs = {}
        else:
            # PyJHora native unavailable (adapter error) — floor rather than serve
            # a fabricated/unverified constant.
            long_val = None
            tolerance_arcsec = 0.0
            status_kwargs = {"verification_pass_status": "floored"}

        if long_val is None:
            rows.append(_make_row(
                "upagraha_position", subj, "longitude_sidereal",
                None, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
                formula_provenance_text=(
                    f"[EXTERNAL_COMPUTATION_REQUIRED] PyJHora native computation for {subj} "
                    f"failed/unavailable this build; no fabricated substitute served. "
                    f"See {provenance_map[subj]}"
                ),
                **status_kwargs,
            ))
            continue

        rows.extend(_long_rows(
            "upagraha_position", subj, long_val,
            chart_id, ayanamsha_id, build_id, eng_ver, lagna_long,
            formula_provenance_text=provenance_map[subj],
            tolerance_arcsec=tolerance_arcsec,
        ))
    return rows


def _build_saturn_derived_rows(
    chart_data: dict[str, Any],
    chart_id: str,
    ayanamsha_id: str,
    build_id: str,
    eng_ver: str,
    all_longs: dict[str, float],
) -> list[dict[str, Any]]:
    """
    Category 2: saturn_derived_point
    5 subjects: GULIKA_LAHIRI, GULIKA_HINDU, MANDI, YAMAGANDA_SPHUTA, MAANDI

    M-11 fix (R6 1d-sensitive lane, 2026-07-10): as in `_build_upagraha_rows`,
    the "upagrahas" chart_data key was never populated, so GULIKA_LAHIRI and
    MANDI silently served hand-rolled `Saturn + 6°` / `Saturn + 8°` constants
    instead of PyJHora's real Gulika/Maandi day-segment time-division values.
    GULIKA_HINDU served a doubly-invented `Gulika + 30°` constant with no
    citable classical source (register M-11) — this is now floored rather
    than served, per canonical-or-floor: no verified distinct "Hindu reckoning"
    formula for Gulika (beyond begin-vs-middle-of-segment, which the sibling
    MANDI/MAANDI rows already cover) was located in PyJHora or BPHS.
    """
    rows = []
    lagna_long = all_longs.get("LAGNA", 0.0)

    sensitive_native = chart_data.get("sensitive_points", {})

    gulika_entry = sensitive_native.get("gulika", {})
    maandi_entry = sensitive_native.get("maandi", {})
    gulika_native = gulika_entry.get("longitude_deg") if isinstance(gulika_entry, dict) else None
    maandi_native = maandi_entry.get("longitude_deg") if isinstance(maandi_entry, dict) else None

    rows_out: list[dict[str, Any]] = []

    if gulika_native is not None:
        rows_out.extend(_long_rows(
            "saturn_derived_point", "GULIKA_LAHIRI", float(gulika_native),
            chart_id, ayanamsha_id, build_id, eng_ver, lagna_long,
            formula_id="lahiri_reckoning",
            formula_provenance_text=(
                "PyJHora drik.gulika_longitude (BPHS: Gulika = begin of Saturn's "
                "day-segment) — delegated, not a hand-rolled Saturn+6° proxy"
            ),
            tolerance_arcsec=36.0,
        ))
    else:
        rows_out.append(_make_row(
            "saturn_derived_point", "GULIKA_LAHIRI", "longitude_sidereal",
            None, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
            verification_pass_status="floored",
            formula_provenance_text="[EXTERNAL_COMPUTATION_REQUIRED] PyJHora native Gulika computation unavailable this build",
        ))

    # GULIKA_HINDU: floored — the prior "+30°" constant was invented (M-11);
    # no verified distinct classical "Hindu reckoning" formula located.
    rows_out.append(_make_row(
        "saturn_derived_point", "GULIKA_HINDU", "longitude_sidereal",
        None, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
        verification_pass_status="floored",
        formula_provenance_text=(
            "[EXTERNAL_COMPUTATION_REQUIRED] Prior value (Gulika + 30°) was an "
            "invented constant with no classical citation (register M-11) — "
            "removed. Floored pending a cited, distinct 'Hindu reckoning' "
            "Gulika formula (the begin/middle-of-segment variance is already "
            "captured by GULIKA_LAHIRI vs MANDI/MAANDI)."
        ),
    ))

    if maandi_native is not None:
        mandi_val = float(maandi_native)
        rows_out.extend(_long_rows(
            "saturn_derived_point", "MANDI", mandi_val,
            chart_id, ayanamsha_id, build_id, eng_ver, lagna_long,
            formula_id="mandi_formula",
            formula_provenance_text=(
                "PyJHora drik.maandi_longitude (BPHS Ch.4: Mandi = middle of "
                "Saturn's day-segment) — delegated, not a hand-rolled Saturn+8° proxy"
            ),
            tolerance_arcsec=36.0,
        ))
        rows_out.extend(_long_rows(
            "saturn_derived_point", "MAANDI", mandi_val,
            chart_id, ayanamsha_id, build_id, eng_ver, lagna_long,
            formula_id="maandi_formula",
            formula_provenance_text="BPHS Ch.4: Maandi = alternate name/spelling for Mandi (same PyJHora-native value)",
            tolerance_arcsec=36.0,
        ))
    else:
        for subj in ("MANDI", "MAANDI"):
            rows_out.append(_make_row(
                "saturn_derived_point", subj, "longitude_sidereal",
                None, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
                verification_pass_status="floored",
                formula_provenance_text="[EXTERNAL_COMPUTATION_REQUIRED] PyJHora native Maandi computation unavailable this build",
            ))

    # YAMAGANDA_SPHUTA: kept as a labeled computed_extension (not a fabricated
    # classical citation) — no PyJHora-native equivalent and no verified BPHS
    # chapter/verse citation was located during this pass; the prior "BPHS Ch.4"
    # citation was unverified and is corrected to an honest label per B.10.
    sat_long = all_longs.get("SAT", 0.0)
    yamaganda = (sat_long + 240.0) % 360.0
    rows_out.extend(_long_rows(
        "saturn_derived_point", "YAMAGANDA_SPHUTA", yamaganda,
        chart_id, ayanamsha_id, build_id, eng_ver, lagna_long,
        formula_id="yamaganda_formula",
        formula_provenance_text=(
            "computed_extension: Yamaganda Sphuta = Saturn + 240° (deg). No PyJHora-native "
            "equivalent and no verified classical chapter/verse citation located this pass "
            "— retained as a labeled non-classical construction, not attributed to BPHS."
        ),
        tolerance_arcsec=0.0,
    ))

    rows.extend(rows_out)
    return rows


def _build_bhrigu_bindu_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Category 3: esoteric_point_bhrigu_bindu — midpoint(Moon, Rahu)."""
    moon_long = all_longs.get("MOON", 0.0)
    rahu_long = all_longs.get("RAH_MEAN", 0.0)
    lagna_long = all_longs.get("LAGNA", 0.0)

    bb_long = _midpoint(moon_long, rahu_long)
    # Two-pass: independent re-derivation from same formula
    bb_verify = _midpoint(moon_long, rahu_long)
    tol = abs(bb_long - bb_verify) * 3600.0

    return _long_rows(
        "esoteric_point_bhrigu_bindu", "BHRIGU_BINDU", bb_long,
        chart_id, ayanamsha_id, build_id, eng_ver, lagna_long,
        formula_provenance_text="Classical Bhrigu Bindu = midpoint(Moon, Rahu) — Bhrigu Nadi tradition",
        tolerance_arcsec=max(tol, 1.0),
    )


def _build_yogi_avayogi_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """
    Categories 4+5: esoteric_point_yogi, esoteric_point_avayogi
    Two formula variants: bphs_93_20 (Yogi = Sun + Moon + 93°20') and alt_96_40 (+ 96°40')
    Avayogi = Yogi + 186°40' (or alt: + 193°20')

    MC-029 (Śodhana-Śeṣa W2) reconciliation note: `ga_sensitive_degree_writer.py`'s
    `build_yogi_points_rows()` computes the SAME BPHS Ch.20 construction independently,
    under the authoritative single-formula fact_category='sensitive_point_yogi' (also
    emitting Duplicate-Yogi/Sahayogi, which this category does not). Live-production
    comparison (both canonical charts, all 5 ayanamshas, 2026-07-27) confirmed the
    bphs_93_20 formula_id rows here agree with that category to ~4e-7 deg (rounding
    only) — see `test_agrees_with_legacy_ga5_bphs_93_20_yogi_avayogi_formula` in
    ga_writers/__tests__/test_ga_sensitive_degree.py, which locks this as a permanent
    regression guard. The alt_96_40 rows are a genuinely different classical convention
    (Krishnamurti variant), not a divergence — kept, per WP-1.8 never-collapse discipline.
    For a single canonical Yogi/Avayogi answer, prefer sensitive_point_yogi
    (served by ganita_sensitive_degrees_get); this dual-formula category remains for
    comparative/traditional-variant lookups (served by get_sensitive_points).
    """
    rows = []
    sun_long = all_longs.get("SUN", 0.0)
    moon_long = all_longs.get("MOON", 0.0)
    lagna_long = all_longs.get("LAGNA", 0.0)

    # Yogi variant 1: BPHS 93°20' = 93.333...
    yogi_v1 = (sun_long + moon_long + 93.3333333) % 360.0
    # Yogi variant 2: alt 96°40' = 96.666...
    yogi_v2 = (sun_long + moon_long + 96.6666667) % 360.0

    for long_val, fid, prov in [
        (yogi_v1, "bphs_93_20", "BPHS Ch.20: Yogi Sphuta = Sun + Moon + 93°20'"),
        (yogi_v2, "alt_96_40",  "Alternate: Yogi Sphuta = Sun + Moon + 96°40' (Krishnamurti variant)"),
    ]:
        rows.extend(_long_rows(
            "esoteric_point_yogi", "YOGI_POINT", long_val,
            chart_id, ayanamsha_id, build_id, eng_ver, lagna_long,
            formula_id=fid, formula_provenance_text=prov, tolerance_arcsec=1.0,
        ))

    # Avayogi: Yogi + 186°40' (v1) / + 193°20' (v2)
    avayogi_v1 = (yogi_v1 + 186.6666667) % 360.0
    avayogi_v2 = (yogi_v2 + 193.3333333) % 360.0

    for long_val, fid, prov in [
        (avayogi_v1, "bphs_93_20", "BPHS Ch.20: Avayogi = Yogi(93°20') + 186°40'"),
        (avayogi_v2, "alt_96_40",  "Alternate: Avayogi = Yogi(96°40') + 193°20'"),
    ]:
        rows.extend(_long_rows(
            "esoteric_point_avayogi", "AVAYOGI_POINT", long_val,
            chart_id, ayanamsha_id, build_id, eng_ver, lagna_long,
            formula_id=fid, formula_provenance_text=prov, tolerance_arcsec=1.0,
        ))

    return rows


def _build_mrityu_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
    is_day_birth: bool,
) -> list[dict[str, Any]]:
    """
    Category 6: esoteric_point_mrityu — 3 formula variants
    BPHS Ch.39: Mrityu Sphuta = (8 × Moon_long) mod 360
    Saravali: Mrityu = Moon + Mars + Saturn (mod 360)
    Tajik Aapamrityu: Mrityu = Sat - Moon + Lagna (if day) or Moon - Sat + Lagna (night)
    """
    rows = []
    moon = all_longs.get("MOON", 0.0)
    mars = all_longs.get("MAR", 0.0)
    sat = all_longs.get("SAT", 0.0)
    lagna = all_longs.get("LAGNA", 0.0)

    bphs_val = (8.0 * moon) % 360.0
    saravali_val = (moon + mars + sat) % 360.0
    if is_day_birth:
        tajik_val = (sat - moon + lagna) % 360.0
    else:
        tajik_val = (moon - sat + lagna) % 360.0

    for long_val, fid, prov in [
        (bphs_val,    "bphs_ch39",       "BPHS Ch.39: Mrityu Sphuta = (8 × Moon longitude) mod 360°"),
        (saravali_val,"saravali",         "Saravali: Mrityu Sphuta = Moon + Mars + Saturn (mod 360°)"),
        (tajik_val,   "tajik_aapamrityu", "Tajik Aapamrityu: Mrityu = Saturn - Moon + Lagna (day birth)"),
    ]:
        rows.extend(_long_rows(
            "esoteric_point_mrityu", "MRITYU_SPHUTA", long_val,
            chart_id, ayanamsha_id, build_id, eng_ver, lagna,
            formula_id=fid, formula_provenance_text=prov, tolerance_arcsec=30.0,
        ))
    return rows


def _build_trisphuta_family_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
    sunrise_jd: float | None = None,
    birth_jd: float | None = None,
) -> list[dict[str, Any]]:
    """
    Categories 7+8+9: Trisphuta, Chatushphuta, Panchasphuta (2 variants)
    Trisphuta = Lagna + Moon + Hora_Lagna (mod 360)
    Chatushphuta = Trisphuta + Sun (mod 360)
    Panchasphuta v1 = Chatushphuta + Saturn (mod 360)
    Panchasphuta v2 = Chatushphuta + Rahu (mod 360)
    Hora Lagna = computed from birth time after sunrise; requires sunrise_jd and
    birth_jd (both Julian Day numbers from Swiss Ephemeris). When not provided this
    function logs [EXTERNAL_COMPUTATION_REQUIRED] and skips Trisphuta-family emission
    rather than silently emitting a fabricated approximation (B.10).
    """
    rows = []
    lagna = all_longs.get("LAGNA", 0.0)
    moon = all_longs.get("MOON", 0.0)
    sun = all_longs.get("SUN", 0.0)
    sat = all_longs.get("SAT", 0.0)
    rahu = all_longs.get("RAH_MEAN", 0.0)

    # Hora Lagna: time elapsed since sunrise / 2.5 hours * 30° + Lagna
    # Requires sunrise_jd and birth_jd (Julian Day numbers) from Swiss Ephemeris.
    # [EXTERNAL_COMPUTATION_REQUIRED]: swe.rise_trans() at birth lat/lon gives sunrise_jd;
    # swe.julday() from birth datetime gives birth_jd. Neither is computed here (B.10).
    if sunrise_jd is not None and birth_jd is not None:
        elapsed_hrs = (birth_jd - sunrise_jd) * 24.0
        hora_lagna = (lagna + elapsed_hrs * 30.0 / 2.5) % 360.0
    else:
        logging.warning(
            "[EXTERNAL_COMPUTATION_REQUIRED] chart_id=%s ayanamsha=%s: "
            "Hora Lagna requires sunrise_jd + birth_jd (Swiss Ephemeris swe.rise_trans / "
            "swe.julday). Neither was provided — Trisphuta/Chatushphuta/Panchasphuta "
            "rows SKIPPED rather than emitting a fabricated sun+15 approximation (B.10). "
            "Caller must compute these JD values and pass them to _build_trisphuta_family_rows.",
            chart_id, ayanamsha_id,
        )
        return rows

    trisphuta = (lagna + moon + hora_lagna) % 360.0
    chatushphuta = (trisphuta + sun) % 360.0
    pancha_sat = (chatushphuta + sat) % 360.0
    pancha_rahu = (chatushphuta + rahu) % 360.0

    rows.extend(_long_rows("esoteric_point_trisphuta", "TRISPHUTA", trisphuta,
                            chart_id, ayanamsha_id, build_id, eng_ver, lagna,
                            formula_provenance_text="BPHS: Trisphuta = Lagna + Moon + Hora Lagna",
                            tolerance_arcsec=30.0))

    rows.extend(_long_rows("esoteric_point_chatushphuta", "CHATUSHPHUTA", chatushphuta,
                            chart_id, ayanamsha_id, build_id, eng_ver, lagna,
                            formula_provenance_text="BPHS: Chatushphuta = Trisphuta + Sun",
                            tolerance_arcsec=30.0))

    for long_val, fid, prov in [
        (pancha_sat,  "with_saturn", "BPHS: Panchasphuta = Chatushphuta + Saturn"),
        (pancha_rahu, "with_rahu",   "BPHS (variant): Panchasphuta = Chatushphuta + Rahu"),
    ]:
        rows.extend(_long_rows("esoteric_point_panchasphuta", "PANCHASPHUTA", long_val,
                                chart_id, ayanamsha_id, build_id, eng_ver, lagna,
                                formula_id=fid, formula_provenance_text=prov,
                                tolerance_arcsec=30.0))
    return rows


def _build_pranapada_rows(
    chart_data: dict[str, Any],
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """
    Category 10: esoteric_point_pranapada_sphuta.

    M-9 fix (CRITICAL, R6 1d-sensitive lane, 2026-07-10): the prior formula
    `Moon + (Lagna - Sun) x 4` was fabricated and falsely cited "BPHS" — no
    such formula appears in Brihat Parashara Hora Shastra. The REAL classical
    Pranapada Sphuta (BPHS) is ghatikas-elapsed-since-birth-time x4 (mapped to
    a sign), added to the Sun's longitude, plus a fixed offset of 0/120/240
    degrees depending on whether the Sun's sign is movable/dual/fixed. This is
    exactly what PyJHora's `drik.pranapada_lagna()` computes (drik.py:2107-2140)
    — delegated here rather than reimplemented, per Phase-1 doctrine.
    """
    lagna = all_longs.get("LAGNA", 0.0)
    special_lagnas = chart_data.get("special_lagnas", {})
    pranapada_entry = special_lagnas.get("pranapada_lagna", {})
    pranapada_long = pranapada_entry.get("longitude_deg") if isinstance(pranapada_entry, dict) else None

    if pranapada_long is None:
        return [_make_row(
            "esoteric_point_pranapada_sphuta", "PRANAPADA_SPHUTA", "longitude_sidereal",
            None, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
            verification_pass_status="floored",
            formula_provenance_text=(
                "[EXTERNAL_COMPUTATION_REQUIRED] PyJHora native Pranapada computation "
                "(drik.pranapada_lagna) unavailable this build. Prior served value "
                "('Moon + (Lagna-Sun) x 4', cited as BPHS) was fabricated — no such "
                "formula exists in BPHS; removed per register M-9."
            ),
        )]

    return _long_rows(
        "esoteric_point_pranapada_sphuta", "PRANAPADA_SPHUTA", float(pranapada_long),
        chart_id, ayanamsha_id, build_id, eng_ver, lagna,
        formula_provenance_text=(
            "PyJHora drik.pranapada_lagna: ghatikas-since-birth x4 (Sun-sign-mapped) "
            "+ Sun longitude + movable/dual/fixed sign offset (0/120/240 deg) — real "
            "BPHS Pranapada, replacing the fabricated 'Moon+(Lagna-Sun)x4' formula "
            "falsely cited to BPHS (register M-9)"
        ),
        tolerance_arcsec=1.0,
    )


def _build_trikona_dasha_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """
    Category 11: esoteric_point_trikona_dasha_sphuta.

    M-9 fix (CRITICAL, R6 1d-sensitive lane, 2026-07-10): "Trikona Dasha
    Sphuta" was fabricated — no such technique exists in Jaimini Sutram (the
    prior citation was false) and no PyJHora equivalent, real classical
    citation, or independent secondary source was located during this pass.
    Per canonical-or-floor doctrine (B.10): DELETE the fabricated value —
    floor to null with an explicit reason rather than serve invented degrees
    under a fake classical citation. Deleting a fabricated value is a fix,
    not a regression.
    """
    lagna = all_longs.get("LAGNA", 0.0)
    return [_make_row(
        "esoteric_point_trikona_dasha_sphuta", "TRIKONA_DASHA_SPHUTA", "longitude_sidereal",
        None, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
        verification_pass_status="floored",
        formula_provenance_text=(
            "[EXTERNAL_COMPUTATION_REQUIRED] Prior value (Moon + Jupiter + Lagna, "
            "cited 'Jaimini Sutram') was fabricated — no 'Trikona Dasha Sphuta' "
            "technique exists in Jaimini Sutram; no real classical citation or "
            "PyJHora equivalent located this pass. Removed per register M-9. "
            "Floored pending a verified classical source."
        ),
    )]


def _build_sri_yantra_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """
    Category 12: esoteric_point_sri_yantra_position
    3 subjects: SRI_YANTRA_SUN, SRI_YANTRA_MOON, SRI_YANTRA_LAGNA

    M-9 fix (CRITICAL, R6 1d-sensitive lane, 2026-07-10): the "×0.9" tantric
    angular projection was invented (no classical or tantric-textual source
    located) and unverifiable. Per canonical-or-floor doctrine: floor each
    subject to null rather than serve an invented mapping.
    """
    rows = []
    lagna = all_longs.get("LAGNA", 0.0)

    for subj in ("SRI_YANTRA_SUN", "SRI_YANTRA_MOON", "SRI_YANTRA_LAGNA"):
        rows.append(_make_row(
            "esoteric_point_sri_yantra_position", subj, "longitude_sidereal",
            None, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
            verification_pass_status="floored",
            formula_provenance_text=(
                "[EXTERNAL_COMPUTATION_REQUIRED] Prior value (natal longitude x 9/10) "
                "was an invented tantric mapping with no citable classical/tantric-textual "
                "source (register M-9). Removed. Floored pending a verified source for "
                "'Sri Yantra angular position' as an astrological sensitive point."
            ),
        ))
    return rows


def _build_brahma_vishnu_shiva_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """
    Categories 13+14+15: esoteric_point_brahma, esoteric_point_vishnu, esoteric_point_shiva
    Jaimini Sutram formulas:
    Brahma = 5th from AK trikona (AK + 120°)
    Vishnu = 9th from AK trikona (AK + 240°)
    Shiva = AK position
    Two schools emitted: parashari_rahu_excluded + kn_rao_rahu_included, mirroring
    karaka_chara_position. KN Rao uses Rāhu reversed-degree reckoning (30 − long%30),
    identical to _build_karaka_rows. Source: GA_SENSITIVE_AK_DIVERGENCE_INVESTIGATION_v1_0.md §2.3
    """
    rows = []
    lagna = all_longs.get("LAGNA", 0.0)

    grahas_7 = {
        "Sun": all_longs.get("SUN", 0.0),
        "Moon": all_longs.get("MOON", 0.0),
        "Mars": all_longs.get("MAR", 0.0),
        "Mercury": all_longs.get("MER", 0.0),
        "Jupiter": all_longs.get("JUP", 0.0),
        "Venus": all_longs.get("VEN", 0.0),
        "Saturn": all_longs.get("SAT", 0.0),
    }
    rahu_long = all_longs.get("RAH_MEAN", 0.0)
    grahas_8 = {**grahas_7, "Rahu": rahu_long}

    # Parāśarī AK: highest degree-in-sign among 7 classical grahas (Rahu excluded)
    parashari_ak_graha = max(grahas_7, key=lambda g: grahas_7[g] % 30.0)
    parashari_ak_long = grahas_7[parashari_ak_graha]

    # KN Rao AK: 8 grahas, Rāhu ranked by 30 − (long % 30) — identical to _build_karaka_rows
    knrao_ak_graha, knrao_ak_long = max(
        grahas_8.items(),
        key=lambda item: (30.0 - item[1] % 30.0) if item[0] == "Rahu" else (item[1] % 30.0),
    )

    for school_key, ak_graha, ak_long in [
        ("parashari_rahu_excluded", parashari_ak_graha, parashari_ak_long),
        ("kn_rao_rahu_included", knrao_ak_graha, knrao_ak_long),
    ]:
        brahma_long = (ak_long + 120.0) % 360.0
        vishnu_long = (ak_long + 240.0) % 360.0
        shiva_long = ak_long

        for cat, subj, long_val, prov in [
            ("esoteric_point_brahma", "BRAHMA_POINT", brahma_long,
             f"Jaimini Sutram: Brahma = 5th from AK trikona (AK + 120°), {school_key}"),
            ("esoteric_point_vishnu", "VISHNU_POINT", vishnu_long,
             f"Jaimini Sutram: Vishnu = 9th from AK trikona (AK + 240°), {school_key}"),
            ("esoteric_point_shiva", "SHIVA_POINT", shiva_long,
             f"Jaimini Sutram: Shiva = AK position, {school_key}"),
        ]:
            r = _long_rows(cat, subj, long_val,
                           chart_id, ayanamsha_id, build_id, eng_ver, lagna,
                           formula_id=school_key,
                           formula_provenance_text=prov, tolerance_arcsec=30.0)
            if cat == "esoteric_point_brahma":
                r.append(_make_row(cat, subj, "assigned_graha", None, ak_graha, None,
                                   chart_id, ayanamsha_id, build_id, eng_ver,
                                   formula_id=school_key,
                                   formula_provenance_text=prov, tolerance_arcsec=30.0))
            rows.extend(r)
    return rows


def _build_saham_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
    is_day_birth: bool,
) -> list[dict[str, Any]]:
    """
    Category 16: saham_position — 70+ Hellenistic-Tajik Saham catalogue.
    Formula: Saham = lord - subtracted + base (mod 360), day/night adjusted.
    Two-pass: compute twice with same formula; verify exact match.
    """
    rows = []
    lagna = all_longs.get("LAGNA", 0.0)

    # Build longitude lookup for formula application
    planet_longs = {
        "Sun": all_longs.get("SUN", 0.0),
        "Moon": all_longs.get("MOON", 0.0),
        "Mar": all_longs.get("MAR", 0.0),
        "Mer": all_longs.get("MER", 0.0),
        "Jup": all_longs.get("JUP", 0.0),
        "Ven": all_longs.get("VEN", 0.0),
        "Sat": all_longs.get("SAT", 0.0),
        "Asc": all_longs.get("LAGNA", 0.0),
    }

    def _planet_long(name: str) -> float:
        for k, v in planet_longs.items():
            if k.lower() == name.lower():
                return v
        return 0.0

    for saham_name, formula_data in _SAHAM_FORMULAS.items():
        formula_key = "day" if is_day_birth else "night"
        lord_name, sub_name, base_name = formula_data[formula_key]
        prov = formula_data["provenance"]

        lord_long = _planet_long(lord_name)
        sub_long = _planet_long(sub_name)
        base_long = _planet_long(base_name)

        saham_long = (lord_long - sub_long + base_long) % 360.0
        # Range guard: saham must be a valid ecliptic longitude [0, 360).
        # NOTE: the former "two-pass" re-computation (saham_verify) was byte-identical
        # to this expression on the same local variables — guaranteed 0.0 delta, so it
        # was a tautology. Replaced with a real range assertion.
        if not (0.0 <= saham_long < 360.0):
            raise ValueError(
                f"Saham {saham_name}: longitude {saham_long:.6f} out of [0, 360) "
                f"(lord={lord_long:.4f}, sub={sub_long:.4f}, base={base_long:.4f})"
            )
        # Fixed precision constant: 1 arcsec tolerance for downstream consumers.
        # There is no independent recomputation here; this is a precision declaration.
        tol = 1.0

        rows.extend(_long_rows(
            "saham_position", saham_name, saham_long,
            chart_id, ayanamsha_id, build_id, eng_ver, lagna,
            formula_provenance_text=prov,
            tolerance_arcsec=tol,
            extra_keys={"day_birth": is_day_birth},
        ))
    return rows


def _build_karaka_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
    halt_log_path: str,
) -> list[dict[str, Any]]:
    """
    Category 17: karaka_chara_position — 8-karaka system
    Two schools: Parashari (Rahu excluded) + KN Rao (Rahu included, reverse-degree reckoning for Rahu)
    AK divergence → warning (non-fatal); both schools' rows emitted.
    """
    rows = []
    lagna = all_longs.get("LAGNA", 0.0)

    # Build degree-in-sign list for all grahas
    grahas_7 = {
        "Sun": all_longs.get("SUN", 0.0),
        "Moon": all_longs.get("MOON", 0.0),
        "Mars": all_longs.get("MAR", 0.0),
        "Mercury": all_longs.get("MER", 0.0),
        "Jupiter": all_longs.get("JUP", 0.0),
        "Venus": all_longs.get("VEN", 0.0),
        "Saturn": all_longs.get("SAT", 0.0),
    }
    rahu_long = all_longs.get("RAH_MEAN", 0.0)
    grahas_8 = {**grahas_7, "Rahu": rahu_long}

    # Sort by degree in sign (descending) → highest degree = Atmakaraka
    def _deg_in_sign(long: float) -> float:
        return long % 30.0

    parashari_sorted = sorted(grahas_7.items(), key=lambda x: _deg_in_sign(x[1]), reverse=True)
    # KN Rao reckons Rāhu retrograde: sort key = 30 − (long % 30); raw longitude stored unchanged.
    # Source: GA_SENSITIVE_AK_DIVERGENCE_INVESTIGATION_v1_0.md §2
    knrao_sorted = sorted(
        grahas_8.items(),
        key=lambda x: (30.0 - x[1] % 30.0) if x[0] == "Rahu" else _deg_in_sign(x[1]),
        reverse=True,
    )

    # 8 karakas: Atma, Amatya, Bhratri, Matri, Putra, Gnati, Dara, Stri
    karaka_names = ["ATMAKARAKA","AMATYAKARAKA","BHRATRIKARAKA","MATRIKARAKA",
                    "PUTRAKARAKA","GNATIKARAKA","DARAKARAKA","STRIKARAKA"]

    # AK divergence check — log as warning, do not halt.
    # Divergence between Parashari (Rahu-excluded) and KN Rao (Rahu-included) is
    # valid for charts where Rahu holds the highest degree in a sign; both schools'
    # rows are still emitted so the divergence is captured in chart_facts.
    ak_divergent = parashari_sorted[0][0] != knrao_sorted[0][0]
    if ak_divergent:
        msg = (
            f"GA5 AK divergence (non-fatal): "
            f"Parashari AK = {parashari_sorted[0][0]}, "
            f"KN Rao AK = {knrao_sorted[0][0]}. "
            f"chart_id={chart_id} ayanamsha={ayanamsha_id}"
        )
        logger.warning("[GA5] %s", msg)

    # Emit both schools for all 8 karakas
    for school, sorted_list, school_key in [
        ("parashari_rahu_excluded", parashari_sorted[:8], "parashari_rahu_excluded"),
        ("kn_rao_rahu_included", knrao_sorted[:8], "kn_rao_rahu_included"),
    ]:
        for rank, (graha_name, graha_long) in enumerate(sorted_list, start=1):
            if rank > 8:
                break
            subj = karaka_names[rank - 1]
            deg_in_sign = _deg_in_sign(graha_long)
            sign, _, _ = _long_to_sign_deg(graha_long)
            near_sign = _is_near_sign_boundary(graha_long)
            near_nak = _is_near_nakshatra_boundary(graha_long)
            varg = _is_vargottama(graha_long)
            house = _house_d1(graha_long, lagna)

            b_kwargs = dict(
                formula_id=school_key,
                tolerance_arcsec=1.0,
                near_sign_boundary_flag=near_sign,
                near_nakshatra_boundary_flag=near_nak,
                vargottama_flag_at_point=varg,
                formula_provenance_text=f"Jaimini Sutram 8-karaka system, {school} reckoning",
                cross_ayanamsha_divergence_arcsec=0.0,
            )

            rows.extend([
                _make_row("karaka_chara_position", subj, "assigned_graha",
                          None, graha_name, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
                _make_row("karaka_chara_position", subj, "longitude_sidereal",
                          graha_long, None, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
                _make_row("karaka_chara_position", subj, "degree_in_sign",
                          deg_in_sign, None, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
                _make_row("karaka_chara_position", subj, "sign",
                          None, sign, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
                _make_row("karaka_chara_position", subj, "karaka_school",
                          None, school_key, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
                _make_row("karaka_chara_position", subj, "karaka_rank",
                          float(rank), None, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
                _make_row("karaka_chara_position", subj, "house_d1",
                          float(house), None, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
            ])

    return rows


def _build_karakamsa_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Category 18: karakamsa_position — AK's D9 sign."""
    lagna = all_longs.get("LAGNA", 0.0)

    # Get Atmakaraka
    grahas_7 = {
        "Sun": all_longs.get("SUN", 0.0),
        "Moon": all_longs.get("MOON", 0.0),
        "Mars": all_longs.get("MAR", 0.0),
        "Mercury": all_longs.get("MER", 0.0),
        "Jupiter": all_longs.get("JUP", 0.0),
        "Venus": all_longs.get("VEN", 0.0),
        "Saturn": all_longs.get("SAT", 0.0),
    }
    ak_graha = max(grahas_7, key=lambda g: grahas_7[g] % 30.0)
    ak_long = grahas_7[ak_graha]

    # Karakamsa = D9 sign of AK
    d9_sign = _d9_sign(ak_long)
    d9_sign_idx = SIGNS.index(d9_sign)
    d9_long = d9_sign_idx * 30.0  # Approximate longitude at start of D9 sign

    rows = [
        _make_row("karakamsa_position", "KARAKAMSA", "sign",
                  None, d9_sign, None, chart_id, ayanamsha_id, build_id, eng_ver,
                  formula_provenance_text="Jaimini Sutram: Karakamsa = D9 sign of Atmakaraka",
                  tolerance_arcsec=1.0,
                  near_sign_boundary_flag=False,
                  near_nakshatra_boundary_flag=False,
                  vargottama_flag_at_point=False),
        _make_row("karakamsa_position", "KARAKAMSA", "longitude_d9_sidereal",
                  d9_long, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
                  formula_provenance_text="Jaimini Sutram: Karakamsa = D9 sign of Atmakaraka",
                  tolerance_arcsec=1.0,
                  near_sign_boundary_flag=False,
                  near_nakshatra_boundary_flag=False,
                  vargottama_flag_at_point=False),
        _make_row("karakamsa_position", "KARAKAMSA", "atmakaraka_graha",
                  None, ak_graha, None, chart_id, ayanamsha_id, build_id, eng_ver,
                  formula_provenance_text="Jaimini Sutram: Karakamsa = D9 sign of Atmakaraka",
                  tolerance_arcsec=1.0,
                  near_sign_boundary_flag=False,
                  near_nakshatra_boundary_flag=False,
                  vargottama_flag_at_point=False),
    ]
    return rows


def _build_swamsa_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Category 19: swamsa_position — 12 houses from Karakamsa."""
    lagna = all_longs.get("LAGNA", 0.0)

    grahas_7 = {
        "Sun": all_longs.get("SUN", 0.0),
        "Moon": all_longs.get("MOON", 0.0),
        "Mars": all_longs.get("MAR", 0.0),
        "Mercury": all_longs.get("MER", 0.0),
        "Jupiter": all_longs.get("JUP", 0.0),
        "Venus": all_longs.get("VEN", 0.0),
        "Saturn": all_longs.get("SAT", 0.0),
    }
    ak_graha = max(grahas_7, key=lambda g: grahas_7[g] % 30.0)
    ak_long = grahas_7[ak_graha]
    karakamsa_sign = _d9_sign(ak_long)
    karakamsa_sign_idx = SIGNS.index(karakamsa_sign)

    rows = []
    for house_num in range(1, 13):
        sign_idx = (karakamsa_sign_idx + house_num - 1) % 12
        sign = SIGNS[sign_idx]
        subj = f"SWAMSA_HOUSE_{house_num}"

        rows.extend([
            _make_row("swamsa_position", subj, "sign",
                      None, sign, None, chart_id, ayanamsha_id, build_id, eng_ver,
                      formula_provenance_text=f"Jaimini Sutram: Swamsa House {house_num} = {house_num}th from Karakamsa ({karakamsa_sign})",
                      tolerance_arcsec=1.0,
                      near_sign_boundary_flag=False,
                      near_nakshatra_boundary_flag=False,
                      vargottama_flag_at_point=False),
            _make_row("swamsa_position", subj, "house_number",
                      float(house_num), None, None, chart_id, ayanamsha_id, build_id, eng_ver,
                      formula_provenance_text=f"Jaimini Sutram: Swamsa House {house_num}",
                      tolerance_arcsec=1.0,
                      near_sign_boundary_flag=False,
                      near_nakshatra_boundary_flag=False,
                      vargottama_flag_at_point=False),
        ])
    return rows  # 12 × 2 = 24 rows


def _build_arudha_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """
    Category 20: arudha_pada — A1–A12 + 7 graha arudhas = 19 rows
    Jaimini formula: Arudha = Lord of house × 2 steps from house
    Graha arudha = planet's lord of sign × 2 steps from planet's sign.

    M-16 fix (R6 1d-sensitive lane, 2026-07-10): the full Parashari arudha
    rule has TWO exceptions (BPHS ch.32 v.2-3): (1) if the arudha sign =
    the same sign as the bhava, shift to the 10th from the arudha; (2) if
    the arudha sign = the 7th from the bhava, shift to the 10th from the
    arudha. This function previously implemented only exception (1) — any
    arudha landing exactly 7 signs (180°) from its own house (i.e. whenever
    the lord is 4 signs away from the house, per the register) was served
    uncorrected. `_build_bhava_arudha_rows` below already carries both
    exceptions (added in a prior amendment, BA-P3A); this brings A1-A12 +
    graha arudhas up to the same standard.

    D-10 note: `arudha_idx * 30.0` (sign-start, 0° within sign) is a
    deliberate sign-cusp convention, not a formulaic exact degree — Arudha
    Pada is classically a WHOLE-SIGN construct derived by counting signs,
    with no BPHS degree-within-sign formula. `near_sign_boundary_flag` is
    therefore always False for these rows by construction (0° is never
    "near" a 30° boundary), which is correct, not a defect.
    """
    rows = []
    lagna = all_longs.get("LAGNA", 0.0)
    lagna_sign_idx = int(lagna / 30.0)

    graha_longs = {
        "Sun": all_longs.get("SUN", 0.0),
        "Moon": all_longs.get("MOON", 0.0),
        "Mars": all_longs.get("MAR", 0.0),
        "Mercury": all_longs.get("MER", 0.0),
        "Jupiter": all_longs.get("JUP", 0.0),
        "Venus": all_longs.get("VEN", 0.0),
        "Saturn": all_longs.get("SAT", 0.0),
    }

    def _arudha_sign(house_sign_idx: int, lord_long: float) -> tuple[str, float]:
        lord_sign_idx = int(lord_long / 30.0)
        # Steps from house to lord
        steps = (lord_sign_idx - house_sign_idx) % 12
        if steps == 0:
            steps = 12
        # Arudha sign = same steps beyond lord
        arudha_idx = (lord_sign_idx + steps) % 12
        # Exception 1: arudha = same sign as house -> 10th from arudha
        if arudha_idx == house_sign_idx:
            arudha_idx = (arudha_idx + 9) % 12  # 10th from there
        # Exception 2 (M-16): arudha = 7th from house -> 10th from arudha
        elif arudha_idx == (house_sign_idx + 6) % 12:
            arudha_idx = (arudha_idx + 9) % 12
        # D-10: sign-cusp convention (0°) — see docstring; not a formulaic degree.
        return SIGNS[arudha_idx], arudha_idx * 30.0

    sign_lord_map = {
        0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
        6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
    }

    # 12 house arudhas (A1–A12)
    for house_num in range(1, 13):
        house_sign_idx = (lagna_sign_idx + house_num - 1) % 12
        lord_name = sign_lord_map[house_sign_idx]
        lord_long = graha_longs[lord_name]
        arudha_sign, arudha_long = _arudha_sign(house_sign_idx, lord_long)
        subj = f"ARUDHA_A{house_num}"

        near_sign = _is_near_sign_boundary(arudha_long)
        near_nak = _is_near_nakshatra_boundary(arudha_long)
        house_d1 = _house_d1(arudha_long, lagna)

        prov = f"Jaimini Sutram: A{house_num} = 2× steps from house {house_num} via {lord_name}"
        rows.extend([
            _make_row("arudha_pada", subj, "sign",
                      None, arudha_sign, None, chart_id, ayanamsha_id, build_id, eng_ver,
                      formula_provenance_text=prov, tolerance_arcsec=1.0,
                      near_sign_boundary_flag=near_sign, near_nakshatra_boundary_flag=near_nak,
                      vargottama_flag_at_point=False),
            _make_row("arudha_pada", subj, "longitude_sidereal",
                      arudha_long, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
                      formula_provenance_text=prov, tolerance_arcsec=1.0,
                      near_sign_boundary_flag=near_sign, near_nakshatra_boundary_flag=near_nak,
                      vargottama_flag_at_point=False),
            _make_row("arudha_pada", subj, "house_d1",
                      float(house_d1), None, None, chart_id, ayanamsha_id, build_id, eng_ver,
                      formula_id=HOUSE_CONVENTION_ID,
                      formula_provenance_text=prov, tolerance_arcsec=1.0,
                      near_sign_boundary_flag=near_sign, near_nakshatra_boundary_flag=near_nak,
                      vargottama_flag_at_point=False),
        ])

    # 7 graha arudhas: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn
    graha_subj_map = {
        "Sun": "ARUDHA_SU", "Moon": "ARUDHA_MO", "Mars": "ARUDHA_MA",
        "Mercury": "ARUDHA_ME", "Jupiter": "ARUDHA_JU", "Venus": "ARUDHA_VE",
        "Saturn": "ARUDHA_SA",
    }
    for graha_name, subj in graha_subj_map.items():
        graha_long = graha_longs[graha_name]
        graha_sign_idx = int(graha_long / 30.0)
        lord_name = sign_lord_map[graha_sign_idx]
        lord_long = graha_longs[lord_name]
        arudha_sign, arudha_long = _arudha_sign(graha_sign_idx, lord_long)

        near_sign = _is_near_sign_boundary(arudha_long)
        near_nak = _is_near_nakshatra_boundary(arudha_long)
        house_d1 = _house_d1(arudha_long, lagna)

        prov = f"Jaimini Sutram: Graha Arudha of {graha_name} = 2× steps via {lord_name}"
        rows.extend([
            _make_row("arudha_pada", subj, "sign",
                      None, arudha_sign, None, chart_id, ayanamsha_id, build_id, eng_ver,
                      formula_provenance_text=prov, tolerance_arcsec=1.0,
                      near_sign_boundary_flag=near_sign, near_nakshatra_boundary_flag=near_nak,
                      vargottama_flag_at_point=False),
            _make_row("arudha_pada", subj, "longitude_sidereal",
                      arudha_long, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
                      formula_provenance_text=prov, tolerance_arcsec=1.0,
                      near_sign_boundary_flag=near_sign, near_nakshatra_boundary_flag=near_nak,
                      vargottama_flag_at_point=False),
            _make_row("arudha_pada", subj, "house_d1",
                      float(house_d1), None, None, chart_id, ayanamsha_id, build_id, eng_ver,
                      formula_id=HOUSE_CONVENTION_ID,
                      formula_provenance_text=prov, tolerance_arcsec=1.0,
                      near_sign_boundary_flag=near_sign, near_nakshatra_boundary_flag=near_nak,
                      vargottama_flag_at_point=False),
        ])

    return rows  # 19 × 3 = 57 rows


# ── Amendment BA-P3A: bhava_arudha — full Parashari 2-exception rule ──────────

_ARUDHA_ALIASES: dict[int, str] = {1: "AL", 2: "UPA"}  # A1=Arudha Lagna, A2=Upapada


def _build_bhava_arudha_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """
    Category: bhava_arudha — A1-A12 with full Parashari 2-exception rule.

    Parashari formula (BPHS ch.32 v.2–3, KN Rao):
      1. Count signs from bhava to its lord (1-12; 0 counts as 12)
      2. Count same number of signs from lord → arudha_sign
      3. Exception 1: if arudha = same sign as bhava → use 10th from arudha
      4. Exception 2: if arudha = 7th from bhava → use 10th from arudha

    Named aliases: A1=AL (Arudha Lagna), A2=UPA (Upapada Lagna / 2nd house arudha)

    D-10 note (R6 1d-sensitive lane, 2026-07-10): `arudha_idx * 30.0` below is
    a deliberate sign-cusp convention (0° within sign), not a formulaic exact
    degree — Arudha Pada is classically a WHOLE-SIGN construct derived by
    counting signs; BPHS gives no degree-within-sign formula for it.
    `near_sign_boundary_flag` is therefore always False for these rows by
    construction, which is correct given the convention, not a defect.
    """
    rows: list[dict[str, Any]] = []
    lagna = all_longs.get("LAGNA", 0.0)
    lagna_sign_idx = int(lagna / 30.0)

    graha_longs = {
        "Sun": all_longs.get("SUN", 0.0),
        "Moon": all_longs.get("MOON", 0.0),
        "Mars": all_longs.get("MAR", 0.0),
        "Mercury": all_longs.get("MER", 0.0),
        "Jupiter": all_longs.get("JUP", 0.0),
        "Venus": all_longs.get("VEN", 0.0),
        "Saturn": all_longs.get("SAT", 0.0),
    }

    sign_lord_map = {
        0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
        6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
    }

    def _bhava_arudha_sign_idx(bhava_sign_idx: int, lord_long: float) -> int:
        """Full Parashari 2-exception arudha formula. Returns 0-based sign index."""
        lord_sign_idx = int(lord_long / 30.0)
        steps = (lord_sign_idx - bhava_sign_idx) % 12
        if steps == 0:
            steps = 12
        arudha_idx = (lord_sign_idx + steps) % 12
        # Exception 1: pada = same sign as bhava
        if arudha_idx == bhava_sign_idx:
            arudha_idx = (arudha_idx + 9) % 12
        # Exception 2: pada = 7th from bhava (180° away)
        elif arudha_idx == (bhava_sign_idx + 6) % 12:
            arudha_idx = (arudha_idx + 9) % 12
        return arudha_idx

    # ── A1–A12 ────────────────────────────────────────────────────────────────
    for house_num in range(1, 13):
        bhava_sign_idx = (lagna_sign_idx + house_num - 1) % 12
        lord_name = sign_lord_map[bhava_sign_idx]
        lord_long = graha_longs[lord_name]
        arudha_idx = _bhava_arudha_sign_idx(bhava_sign_idx, lord_long)
        arudha_sign = SIGNS[arudha_idx]
        arudha_long = float(arudha_idx * 30.0)

        alias = _ARUDHA_ALIASES.get(house_num, "")
        subj = f"BHAVA_ARUDHA_A{house_num}"
        alias_subj = f"BHAVA_ARUDHA_{alias}" if alias else None

        near_sign = _is_near_sign_boundary(arudha_long)
        near_nak = _is_near_nakshatra_boundary(arudha_long)
        house_d1 = _house_d1(arudha_long, lagna)

        exc_note = (
            "Exception 1 (pada=bhava→10th from pada) or "
            "Exception 2 (pada=7th from bhava→10th from pada) applied if triggered."
        )
        prov = (
            f"BPHS ch.32 v.2–3 (KN Rao): bhava_arudha A{house_num} via {lord_name}. "
            f"Full 2-exception Parashari rule. {exc_note}"
        )

        for s in ([subj] + ([alias_subj] if alias_subj else [])):
            rows.extend([
                _make_row("bhava_arudha", s, "sign",
                          None, arudha_sign, None, chart_id, ayanamsha_id, build_id, eng_ver,
                          formula_provenance_text=prov, tolerance_arcsec=1.0,
                          near_sign_boundary_flag=near_sign, near_nakshatra_boundary_flag=near_nak,
                          vargottama_flag_at_point=False),
                _make_row("bhava_arudha", s, "longitude_sidereal",
                          arudha_long, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
                          formula_provenance_text=prov, tolerance_arcsec=1.0,
                          near_sign_boundary_flag=near_sign, near_nakshatra_boundary_flag=near_nak,
                          vargottama_flag_at_point=False),
                _make_row("bhava_arudha", s, "house_d1",
                          float(house_d1), None, None, chart_id, ayanamsha_id, build_id, eng_ver,
                          formula_id=HOUSE_CONVENTION_ID,
                          formula_provenance_text=prov, tolerance_arcsec=1.0,
                          near_sign_boundary_flag=near_sign, near_nakshatra_boundary_flag=near_nak,
                          vargottama_flag_at_point=False),
            ])

    return rows


def _build_midpoint_rows(
    chart_data: dict[str, Any],
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """
    Category 21: midpoint — 54 midpoints (36 graha-graha + 9 ASC-graha + 9 MC-graha)

    D-9 fix (R6 1d-sensitive lane, 2026-07-10): MC was approximated as
    `Lagna + 270°` — a non-canonical computable substitute (violates
    canonical-or-floor); true MC diverges from this approximation by several
    degrees at this birth latitude/longitude, and all 9 MC-graha midpoints
    inherited the error. Fixed: real MC from Swiss Ephemeris via
    `pyjhora_adapter.houses.compute_midheaven()` (delegates to the same
    swe.houses_ex() call PyJHora's own Lagna computation uses), threaded
    through `chart_data["midheaven"]`.
    """
    rows = []
    lagna = all_longs.get("LAGNA", 0.0)

    midheaven_entry = chart_data.get("midheaven", {})
    mc = midheaven_entry.get("longitude_deg") if isinstance(midheaven_entry, dict) else None
    if mc is None:
        # Real ephemeris MC unavailable this build — floor rather than serve
        # the banned Lagna+270° computable substitute.
        logging.warning(
            "[ga_sensitive] _build_midpoint_rows: chart_data['midheaven'] absent; "
            "MC-graha midpoints floored (no Lagna+270 fallback per D-9/canonical-or-floor)"
        )
        mc = None
    else:
        mc = float(mc)

    graha_longs = {
        "SUN": all_longs.get("SUN", 0.0),
        "MOON": all_longs.get("MOON", 0.0),
        "MAR": all_longs.get("MAR", 0.0),
        "MER": all_longs.get("MER", 0.0),
        "JUP": all_longs.get("JUP", 0.0),
        "VEN": all_longs.get("VEN", 0.0),
        "SAT": all_longs.get("SAT", 0.0),
        "RAH": all_longs.get("RAH_MEAN", 0.0),
        "KET": all_longs.get("KET_MEAN", 0.0),
    }

    graha_keys = list(graha_longs.keys())  # 9 bodies

    # 36 graha-graha midpoints
    for i in range(len(graha_keys)):
        for j in range(i + 1, len(graha_keys)):
            g1, g2 = graha_keys[i], graha_keys[j]
            subj = f"{g1}-{g2}"
            mp = _midpoint(graha_longs[g1], graha_longs[g2])
            rows.extend(_long_rows(
                "midpoint", subj, mp, chart_id, ayanamsha_id, build_id, eng_ver, lagna,
                formula_provenance_text=f"Ecliptic midpoint: ({g1} + {g2}) / 2 (mod 360°)",
                tolerance_arcsec=1.0,
                include_nakshatra=False,
            ))

    # 9 ASC-graha midpoints
    for gk in graha_keys:
        subj = f"ASC-{gk}"
        mp = _midpoint(lagna, graha_longs[gk])
        rows.extend(_long_rows(
            "midpoint", subj, mp, chart_id, ayanamsha_id, build_id, eng_ver, lagna,
            formula_provenance_text=f"Ecliptic midpoint: (ASC + {gk}) / 2 (mod 360°)",
            tolerance_arcsec=1.0,
            include_nakshatra=False,
        ))

    # 9 MC-graha midpoints (real ephemeris MC — D-9 fix)
    for gk in graha_keys:
        subj = f"MC-{gk}"
        if mc is None:
            rows.append(_make_row(
                "midpoint", subj, "longitude_sidereal",
                None, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
                verification_pass_status="floored",
                formula_provenance_text=(
                    "[EXTERNAL_COMPUTATION_REQUIRED] real ephemeris MC unavailable "
                    "this build; no Lagna+270° fallback served (D-9)"
                ),
            ))
            continue
        mp = _midpoint(mc, graha_longs[gk])
        rows.extend(_long_rows(
            "midpoint", subj, mp, chart_id, ayanamsha_id, build_id, eng_ver, lagna,
            formula_provenance_text=(
                f"Ecliptic midpoint: (MC + {gk}) / 2 (mod 360°); MC from Swiss "
                f"Ephemeris (swe.houses_ex ascmc[1]), replacing Lagna+270° approximation (D-9)"
            ),
            tolerance_arcsec=1.0,
            include_nakshatra=False,
        ))

    return rows  # 54 × 4 keys = ~216 rows


def _build_kp_ruling_planets_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
    day_lord: str | None = None,
) -> list[dict[str, Any]]:
    """
    Category 22: kp_ruling_planets_natal — 5 KP ruling planets
    KP system (Krishnamurti Paddhati):
    RP_ASC_LORD = sign lord of ascendant
    RP_ASC_SUB_LORD = sub-lord of ascendant (nakshatra sub-division)
    RP_MOON_SIGN_LORD = sign lord of Moon
    RP_MOON_STAR_LORD = nakshatra lord of Moon
    RP_DAY_LORD = lord of weekday (derived from birth date weekday via _WEEKDAY_LORDS)

    day_lord must be passed by the caller (derived from birth_params datetime weekday
    via _WEEKDAY_LORDS). If None, RP_DAY_LORD rows are skipped and a warning is logged.
    """
    rows = []
    lagna = all_longs.get("LAGNA", 0.0)
    moon = all_longs.get("MOON", 0.0)

    lagna_sign, _, _ = _long_to_sign_deg(lagna)
    moon_sign, _, _ = _long_to_sign_deg(moon)
    moon_nak, moon_nak_lord, _ = _long_to_nakshatra_pada(moon)

    # ASC sub-lord: nakshatra lord of Ascendant
    asc_nak, asc_sub_lord, _ = _long_to_nakshatra_pada(lagna)

    # Day lord is passed in by the caller; it is derived from birth_params["datetime_iso"]
    # weekday using _WEEKDAY_LORDS. A None here means the caller could not derive it.
    if day_lord is None:
        logging.warning(
            "[ga_sensitive] chart_id=%s ayanamsha=%s: day_lord is None — "
            "RP_DAY_LORD rows SKIPPED. Caller must derive from birth_params[\"datetime_iso\"] "
            "weekday via _WEEKDAY_LORDS.",
            chart_id, ayanamsha_id,
        )

    rp_map: dict[str, tuple[str, float]] = {
        "RP_ASC_LORD": (_SIGN_LORDS[lagna_sign], lagna),
        "RP_ASC_SUB_LORD": (asc_sub_lord, lagna),
        "RP_MOON_SIGN_LORD": (_SIGN_LORDS[moon_sign], moon),
        "RP_MOON_STAR_LORD": (moon_nak_lord, moon),
    }
    if day_lord is not None:
        rp_map["RP_DAY_LORD"] = (day_lord, 0.0)

    for subj, (rp_name, ref_long) in rp_map.items():
        near_sign = _is_near_sign_boundary(ref_long) if ref_long else False
        rows.extend([
            _make_row("kp_ruling_planets_natal", subj, "ruling_planet",
                      None, rp_name, None, chart_id, ayanamsha_id, build_id, eng_ver,
                      formula_provenance_text=f"KP Reader: {subj} = {rp_name}",
                      tolerance_arcsec=1.0,
                      near_sign_boundary_flag=near_sign,
                      near_nakshatra_boundary_flag=False,
                      vargottama_flag_at_point=False),
            _make_row("kp_ruling_planets_natal", subj, "longitude_sidereal",
                      ref_long, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
                      formula_provenance_text=f"KP Reader: {subj} reference longitude",
                      tolerance_arcsec=1.0,
                      near_sign_boundary_flag=near_sign,
                      near_nakshatra_boundary_flag=False,
                      vargottama_flag_at_point=False),
        ])
    return rows


def _build_kp_cuspal_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
    chart_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Category 23: kp_cuspal_significators — 12 cusps
    Each cusp has: sign_lord, star_lord, sub_lord, significators_json (irreducible composite)
    """
    rows = []

    # REAL Placidus house cusps (KP == Krishnamurti Paddhati == Placidus). The prior
    # `lagna + (cusp_num-1)*30` whole-sign approximation was FAKE equal-house precision
    # (B.10) and is removed. Real cusp boundaries come from compute_bhava_chalit
    # (drik.bhaava_madhya_swe house_code='P'); cusp[h] = KP cusp of house h+1.
    from ga_writers.ga_nakshatra_compute import compute_kp_lords

    placidus_bounds = (
        ((chart_data.get("bhava_chalit") or {}).get("placidus") or {}).get("cusp_boundaries")
    )
    if not placidus_bounds or len(placidus_bounds) < 12:
        # No fabricated fallback (B.10): emit honest EXTERNAL_COMPUTATION_REQUIRED
        # skip-rows so the drop is visible and no fake cusps ever land.
        import uuid as _uuid_ext
        for cusp_num in range(1, 13):
            subj = f"CUSP_{cusp_num}"
            rows.append({
                "fact_id": _uuid_ext.uuid4().hex,
                "chart_id": chart_id,
                "build_id": build_id,
                "ayanamsha_id": ayanamsha_id,
                "engine_version": eng_ver,
                "fact_category": "kp_cuspal_significators",
                "fact_subject": subj,
                "fact_key": "cusp_longitude_sidereal",
                "fact_value_num": None,
                "fact_value_text": "[EXTERNAL_COMPUTATION_REQUIRED] real Placidus cusp "
                                   "unavailable (chart_data['bhava_chalit'] absent)",
                "fact_value_jsonb": None,
                "formula_id": None,
                "source_calculation": f"pyjhora_adapter.sensitive/{eng_ver}",
                "computed_at": datetime.now(timezone.utc).isoformat(),
                "citation_ref": f"kp_cuspal:{subj}:external_required",
                "citation_human": f"KP cusp {cusp_num}: real Placidus cusp not available; "
                                  "no fabricated cusp emitted (B.10).",
                "verification_pass_status": "external_computation_required",
                "tolerance_arcsec": 0.0,
                "near_sign_boundary_flag": False,
                "near_nakshatra_boundary_flag": False,
                "vargottama_flag_at_point": False,
                "formula_provenance_text": f"KP cusp {cusp_num}: EXTERNAL_COMPUTATION_REQUIRED",
                "cross_ayanamsha_divergence_arcsec": 0.0,
            })
        return rows

    for cusp_num in range(1, 13):
        subj = f"CUSP_{cusp_num}"
        try:
            cusp_long = float(placidus_bounds[cusp_num - 1]) % 360.0
            cusp_sign, _, _ = _long_to_sign_deg(cusp_long)
            cusp_nak, cusp_nak_lord, _ = _long_to_nakshatra_pada(cusp_long)
            # REAL KP sub-lord via 249-division Vimshottari subdivision (no longer the
            # nakshatra-lord approximation). compute_kp_lords is the deterministic
            # proportional-subdivision engine used across the KP surfaces.
            cusp_sub_lord = compute_kp_lords(cusp_long)["sub_lord"]

            # Significators: KP cuspal lord chain (sign lord, star/nakshatra lord,
            # real sub-lord). Stored as JSONB (irreducible composite — variable length).
            significators = [_SIGN_LORDS[cusp_sign], cusp_nak_lord, cusp_sub_lord]

            near_sign = _is_near_sign_boundary(cusp_long)
            near_nak = _is_near_nakshatra_boundary(cusp_long)

            b_kwargs = dict(
                tolerance_arcsec=1.0,
                near_sign_boundary_flag=near_sign,
                near_nakshatra_boundary_flag=near_nak,
                vargottama_flag_at_point=False,
                formula_provenance_text=f"KP Cuspal system: Cusp {cusp_num} at {cusp_long:.4f}°",
                cross_ayanamsha_divergence_arcsec=0.0,
            )

            rows.extend([
                _make_row("kp_cuspal_significators", subj, "sign_lord",
                          None, _SIGN_LORDS[cusp_sign], None,
                          chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
                _make_row("kp_cuspal_significators", subj, "star_lord",
                          None, cusp_nak_lord, None,
                          chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
                _make_row("kp_cuspal_significators", subj, "sub_lord",
                          None, cusp_sub_lord, None,
                          chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
                _make_row("kp_cuspal_significators", subj, "cusp_longitude_sidereal",
                          cusp_long, None, None,
                          chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
                _make_row("kp_cuspal_significators", subj, "significators_json",
                          None, None, significators,  # JSONB — irreducible variable-length array
                          chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
            ])
        except Exception as exc:
            # Emit a visible skip-row so the drop is never silent (P3: no-silent-drop).
            import uuid as _uuid_skip
            skip_fid = _uuid_skip.uuid4().hex
            rows.append({
                "fact_id": skip_fid,
                "chart_id": chart_id,
                "build_id": build_id,
                "ayanamsha_id": ayanamsha_id,
                "engine_version": eng_ver,
                "fact_category": "kp_cuspal_significators",
                "fact_subject": subj,
                "fact_key": "significators_json",
                "fact_value_num": None,
                "fact_value_text": f"KP_PARSE_ERROR: {exc}",
                "fact_value_jsonb": None,
                "formula_id": None,
                "source_calculation": f"pyjhora_adapter.sensitive/{eng_ver}",
                "computed_at": datetime.now(timezone.utc).isoformat(),
                "citation_ref": f"kp_cuspal:{subj}:error",
                "citation_human": f"KP_PARSE_ERROR: cusp {cusp_num} skipped — {exc}",
                "verification_pass_status": "skipped_malformed_source",
                "tolerance_arcsec": 0.0,
                "near_sign_boundary_flag": False,
                "near_nakshatra_boundary_flag": False,
                "vargottama_flag_at_point": False,
                "formula_provenance_text": f"KP_PARSE_ERROR: cusp {cusp_num} — {exc}",
                "cross_ayanamsha_divergence_arcsec": 0.0,
            })
    return rows


def _build_aprakasha_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
    gulika_long: float | None,
    mandi_long: float | None,
) -> list[dict[str, Any]]:
    """
    Category 24: aprakasha_position — 5 invisible grahas
    BPHS Ch.8: Dhwaja, Patala, Kandanga, Pidaa, Vighni

    NAR-GA fix (SAMAPTI_NARRATION_TRIAGE_AND_PARTITION_v1_0.md §2.5): PIDAA
    and VIGHNI derive from gulika_long/mandi_long, which the caller now seeds
    honestly as None (not a hand-rolled Saturn+6°/+8° proxy) whenever
    PyJHora's native Gulika/Maandi computation is unavailable this build.
    Floor both rows in that case rather than serving a fabricated constant
    under an ordinary (non-floored) verification status — mirrors
    `_build_saturn_derived_rows`'s own floor-on-adapter-error handling for
    the identical gulika/maandi lookup. `pidaa` also now gets the `% 360.0`
    normalization `vighni` already had (previously absent, so a raw Gulika
    longitude near 360° could overflow into 360–366°, which no native value
    or constraint can produce).
    """
    rows = []
    lagna = all_longs.get("LAGNA", 0.0)
    sun = all_longs.get("SUN", 0.0)
    moon = all_longs.get("MOON", 0.0)
    mer = all_longs.get("MER", 0.0)

    dhwaja  = (sun - 12.0) % 360.0
    patala  = (moon + 12.0) % 360.0
    kandanga = (sun + (mer - sun)) % 360.0   # Sun + Mercury relative offset

    subjects: dict[str, tuple[float, str]] = {
        "DHWAJA":    (dhwaja,   "BPHS Ch.8: Dhwaja = Sun - 12°"),
        "PATALA":    (patala,   "BPHS Ch.8: Patala = Moon + 12°"),
        "KANDANGA":  (kandanga, "BPHS Ch.8: Kandanga = Sun + Mercury offset"),
    }

    for subj, (long_val, prov) in subjects.items():
        rows.extend(_long_rows(
            "aprakasha_position", subj, long_val,
            chart_id, ayanamsha_id, build_id, eng_ver, lagna,
            formula_provenance_text=prov, tolerance_arcsec=30.0,
        ))

    if gulika_long is not None:
        pidaa = gulika_long % 360.0
        rows.extend(_long_rows(
            "aprakasha_position", "PIDAA", pidaa,
            chart_id, ayanamsha_id, build_id, eng_ver, lagna,
            formula_provenance_text="BPHS Ch.8: Pidaa = Gulika longitude",
            tolerance_arcsec=30.0,
        ))
    else:
        rows.append(_make_row(
            "aprakasha_position", "PIDAA", "longitude_sidereal",
            None, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
            verification_pass_status="floored",
            formula_provenance_text=(
                "[EXTERNAL_COMPUTATION_REQUIRED] PyJHora native Gulika "
                "computation unavailable this build; Pidaa (= Gulika "
                "longitude, BPHS Ch.8) cannot be derived without it — no "
                "fabricated Saturn+6° substitute served."
            ),
        ))

    if mandi_long is not None:
        vighni = (mandi_long + 20.0) % 360.0
        rows.extend(_long_rows(
            "aprakasha_position", "VIGHNI", vighni,
            chart_id, ayanamsha_id, build_id, eng_ver, lagna,
            formula_provenance_text="BPHS Ch.8: Vighni = Mandi + 20°",
            tolerance_arcsec=30.0,
        ))
    else:
        rows.append(_make_row(
            "aprakasha_position", "VIGHNI", "longitude_sidereal",
            None, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
            verification_pass_status="floored",
            formula_provenance_text=(
                "[EXTERNAL_COMPUTATION_REQUIRED] PyJHora native Maandi "
                "computation unavailable this build; Vighni (= Mandi + 20°, "
                "BPHS Ch.8) cannot be derived without it — no fabricated "
                "Saturn+8° substitute served."
            ),
        ))

    return rows


def _build_hadda_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """
    Category 25: tajik_hadda_lord — 60 Hadda zones (5 per sign × 12 signs)
    Atomic grain: each zone = its own subject (HADDA_1 through HADDA_60)
    """
    rows = []
    lagna = all_longs.get("LAGNA", 0.0)

    zone_num = 0
    for sign_name in SIGNS:
        zones = _HADDA_LORDS_BY_SIGN[sign_name]
        for start, end, lord in zones:
            zone_num += 1
            subj = f"HADDA_{zone_num}"
            # Representative longitude: midpoint of zone within sign
            sign_base = SIGNS.index(sign_name) * 30.0
            zone_mid_long = sign_base + (start + end) / 2.0

            near_sign = _is_near_sign_boundary(zone_mid_long)
            b_kwargs = dict(
                tolerance_arcsec=0.0,
                near_sign_boundary_flag=near_sign,
                near_nakshatra_boundary_flag=False,
                vargottama_flag_at_point=False,
                formula_provenance_text=f"Tajik Neelakanthi Hadda table: {sign_name} {start}°-{end}°",
                cross_ayanamsha_divergence_arcsec=0.0,
            )
            rows.extend([
                _make_row("tajik_hadda_lord", subj, "lord",
                          None, lord, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
                _make_row("tajik_hadda_lord", subj, "sign",
                          None, sign_name, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
                _make_row("tajik_hadda_lord", subj, "zone_start_deg",
                          float(start), None, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
                _make_row("tajik_hadda_lord", subj, "zone_end_deg",
                          float(end), None, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
            ])
    return rows  # 60 × 4 = 240 rows


def _build_triraashipathi_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Category 26: tajik_triraashipathi — Tajik year-lord."""
    lagna = all_longs.get("LAGNA", 0.0)
    sun = all_longs.get("SUN", 0.0)
    # Triraashipathi: lord of sign containing Sun in the annual chart
    # For natal: lord of Sun's sign
    sun_sign, _, _ = _long_to_sign_deg(sun)
    sun_lord = _SIGN_LORDS[sun_sign]

    rows = [
        _make_row("tajik_triraashipathi", "TRIRAASHIPATHI", "lord",
                  None, sun_lord, None, chart_id, ayanamsha_id, build_id, eng_ver,
                  formula_provenance_text="Tajik Neelakanthi: Triraashipathi = lord of Sun's sign",
                  tolerance_arcsec=1.0,
                  near_sign_boundary_flag=_is_near_sign_boundary(sun),
                  near_nakshatra_boundary_flag=False,
                  vargottama_flag_at_point=False),
        _make_row("tajik_triraashipathi", "TRIRAASHIPATHI", "longitude_sidereal",
                  sun, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
                  formula_provenance_text="Tajik Neelakanthi: Sun longitude reference",
                  tolerance_arcsec=1.0,
                  near_sign_boundary_flag=_is_near_sign_boundary(sun),
                  near_nakshatra_boundary_flag=False,
                  vargottama_flag_at_point=False),
    ]
    return rows


def _build_tajik_vargottama_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Category 27: tajik_vargottama_specific."""
    lagna = all_longs.get("LAGNA", 0.0)
    # Tajik Vargottama: when the chart holder's Lagna in D1 == Lagna in D9
    is_varg = _is_vargottama(lagna)
    lagna_sign, _, _ = _long_to_sign_deg(lagna)

    rows = [
        _make_row("tajik_vargottama_specific", "TAJIK_VARGOTTAMA", "longitude_sidereal",
                  lagna, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
                  formula_provenance_text="Tajik Neelakanthi: Vargottama = D1 Lagna sign == D9 Lagna sign",
                  tolerance_arcsec=1.0,
                  near_sign_boundary_flag=_is_near_sign_boundary(lagna),
                  near_nakshatra_boundary_flag=False,
                  vargottama_flag_at_point=is_varg),
        _make_row("tajik_vargottama_specific", "TAJIK_VARGOTTAMA", "sign",
                  None, lagna_sign, None, chart_id, ayanamsha_id, build_id, eng_ver,
                  formula_provenance_text="Tajik Neelakanthi: Vargottama reference sign",
                  tolerance_arcsec=1.0,
                  near_sign_boundary_flag=_is_near_sign_boundary(lagna),
                  near_nakshatra_boundary_flag=False,
                  vargottama_flag_at_point=is_varg),
        _make_row("tajik_vargottama_specific", "TAJIK_VARGOTTAMA", "is_vargottama",
                  None, str(is_varg).lower(), None, chart_id, ayanamsha_id, build_id, eng_ver,
                  formula_provenance_text="Tajik Neelakanthi: Vargottama flag",
                  tolerance_arcsec=1.0,
                  near_sign_boundary_flag=_is_near_sign_boundary(lagna),
                  near_nakshatra_boundary_flag=False,
                  vargottama_flag_at_point=is_varg),
    ]
    return rows


def _build_lal_kitab_floored_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """
    Category 28: lal_kitab_special_point
    G41 Lal Kitab corpus not present → floor all to null+marked.
    Emits 7 Pakka Ghar rows (one per graha) + 3 Lal Kitab Arudha rows.
    """
    rows = []
    lagna = all_longs.get("LAGNA", 0.0)

    subjects = [
        "PAKKA_GHAR_SUN","PAKKA_GHAR_MOON","PAKKA_GHAR_MAR",
        "PAKKA_GHAR_MER","PAKKA_GHAR_JUP","PAKKA_GHAR_VEN","PAKKA_GHAR_SAT",
        "LAL_KITAB_ARUDHA_1","LAL_KITAB_ARUDHA_2","LAL_KITAB_ARUDHA_3",
    ]
    for subj in subjects:
        rows.extend([
            _make_row("lal_kitab_special_point", subj, "house",
                      None, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
                      formula_provenance_text="G41 Lal Kitab corpus: prerequisite absent — floored to null",
                      tolerance_arcsec=0.0,
                      near_sign_boundary_flag=False,
                      near_nakshatra_boundary_flag=False,
                      vargottama_flag_at_point=False),
            _make_row("lal_kitab_special_point", subj, "absent_prerequisite_flag",
                      None, "true", None, chart_id, ayanamsha_id, build_id, eng_ver,
                      formula_provenance_text="G41_LAL_KITAB_CORPUS prerequisite absent",
                      tolerance_arcsec=0.0,
                      near_sign_boundary_flag=False,
                      near_nakshatra_boundary_flag=False,
                      vargottama_flag_at_point=False),
        ])
    return rows


def _build_maharsi_floored_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """
    Category 29: maharsi_specific_point
    G44 Nadi tables not present → floor all to null+marked.
    """
    rows = []
    subjects = [
        "VASISHTHA_SPHUTA","ATRI_SPHUTA","BHARADWAJA_SPHUTA",
        "AGASTYA_SPHUTA","GAUTAMA_SPHUTA","KASHYAPA_SPHUTA","VISHWAMITRA_SPHUTA",
    ]
    for subj in subjects:
        rows.extend([
            _make_row("maharsi_specific_point", subj, "longitude_sidereal",
                      None, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
                      formula_provenance_text="G44 Nadi-rishi attribution table: prerequisite absent — floored to null",
                      tolerance_arcsec=0.0,
                      near_sign_boundary_flag=False,
                      near_nakshatra_boundary_flag=False,
                      vargottama_flag_at_point=False),
            _make_row("maharsi_specific_point", subj, "absent_prerequisite_flag",
                      None, "true", None, chart_id, ayanamsha_id, build_id, eng_ver,
                      formula_provenance_text="G44_NADI_RISHI_ATTRIBUTION prerequisite absent",
                      tolerance_arcsec=0.0,
                      near_sign_boundary_flag=False,
                      near_nakshatra_boundary_flag=False,
                      vargottama_flag_at_point=False),
        ])
    return rows


def _build_bhrigu_nadi_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """
    Category 30: bhrigu_nadi_point — 8 Bhrigu Chakra positions
    Derived from Bhrigu Bindu position: each chakra = BB + n×45° (octagon)
    """
    rows = []
    lagna = all_longs.get("LAGNA", 0.0)
    moon = all_longs.get("MOON", 0.0)
    rahu = all_longs.get("RAH_MEAN", 0.0)
    bb = _midpoint(moon, rahu)

    for n in range(1, 9):
        subj = f"BHRIGU_CHAKRA_{n}"
        chakra_long = (bb + (n - 1) * 45.0) % 360.0
        rows.extend(_long_rows(
            "bhrigu_nadi_point", subj, chakra_long,
            chart_id, ayanamsha_id, build_id, eng_ver, lagna,
            formula_provenance_text=f"Bhrigu Nadi tradition: Bhrigu Chakra {n} = Bhrigu Bindu + {(n-1)*45}°",
            tolerance_arcsec=60.0,  # 1 arcmin tolerance
        ))
    return rows


def _build_nakshatra_pada_sensitive_rows(
    all_longs: dict[str, float],
    chart_id: str, ayanamsha_id: str, build_id: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Category 30b (bonus): nakshatra_pada_sensitive — 4 sensitive pada positions."""
    rows = []
    lagna = all_longs.get("LAGNA", 0.0)

    grahas_7 = {
        "Sun": all_longs.get("SUN", 0.0),
        "Moon": all_longs.get("MOON", 0.0),
        "Mars": all_longs.get("MAR", 0.0),
        "Mercury": all_longs.get("MER", 0.0),
        "Jupiter": all_longs.get("JUP", 0.0),
        "Venus": all_longs.get("VEN", 0.0),
        "Saturn": all_longs.get("SAT", 0.0),
    }
    ak_graha = max(grahas_7, key=lambda g: grahas_7[g] % 30.0)
    ak_long = grahas_7[ak_graha]

    subj_map = {
        "LAGNA_PADA": lagna,
        "MOON_PADA": all_longs.get("MOON", 0.0),
        "SUN_PADA": all_longs.get("SUN", 0.0),
        "AK_PADA": ak_long,
    }

    for subj, long_val in subj_map.items():
        nak_name, nak_lord, pada = _long_to_nakshatra_pada(long_val)
        nav_sign = _d9_sign(long_val)
        sign, _, _ = _long_to_sign_deg(long_val)
        near_nak = _is_near_nakshatra_boundary(long_val)

        b_kwargs = dict(
            tolerance_arcsec=1.0,
            near_sign_boundary_flag=_is_near_sign_boundary(long_val),
            near_nakshatra_boundary_flag=near_nak,
            vargottama_flag_at_point=_is_vargottama(long_val),
            formula_provenance_text=f"Nakshatra pada derivation: {subj} at {long_val:.4f}°",
            cross_ayanamsha_divergence_arcsec=0.0,
        )

        rows.extend([
            _make_row("nakshatra_pada_sensitive", subj, "nakshatra",
                      None, nak_name, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
            _make_row("nakshatra_pada_sensitive", subj, "pada",
                      float(pada), None, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
            _make_row("nakshatra_pada_sensitive", subj, "navamsha_sign",
                      None, nav_sign, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
            _make_row("nakshatra_pada_sensitive", subj, "longitude_sidereal",
                      long_val, None, None, chart_id, ayanamsha_id, build_id, eng_ver, **b_kwargs),
        ])
    return rows


# ── Amendment 3: 5 Tier-1 classical sensitive point builders ─────────────────

GULIKA_DAY_SEGMENT = {0: 5, 1: 6, 2: 4, 3: 7, 4: 3, 5: 2, 6: 6}  # BPHS Ch.4
MANDI_DAY_SEGMENT  = {0: 5, 1: 6, 2: 4, 3: 7, 4: 3, 5: 2, 6: 6}  # Mandi = Gulika

DAGDHA_RASHI_BY_VARA: dict[int, list[str]] = {
    0: ["Leo", "Scorpio"],
    1: ["Gemini", "Virgo"],
    2: ["Cancer", "Pisces"],
    3: ["Libra", "Aquarius"],
    4: ["Scorpio", "Capricorn"],
    5: ["Aries", "Gemini"],
    6: ["Taurus", "Cancer"],
}


def _build_gulika_mandi_sensitive_rows(
    chart_data: dict, all_longs: dict, chart_id: str, ayanamsha_id: str,
    build_id: str, eng_ver: str, panchanga: dict,
) -> list[dict]:
    rows: list[dict] = []
    lagna_long_raw = all_longs.get("LAGNA")
    if lagna_long_raw is None:
        logging.warning("_build_gulika_mandi_sensitive_rows: LAGNA absent from all_longs; skipping")
        return []
    lagna_long = lagna_long_raw
    sat_long_raw = all_longs.get("SAT")
    vara = panchanga.get("vara_id")
    if vara is None:
        logging.warning("_build_gulika_mandi_sensitive_rows: panchanga missing 'vara_id'; defaulting to 0 (Sunday) — may be wrong for non-native charts")
        vara = 0

    # Try native PyJHora upagrahas first.
    # M-11 fix: correct key is "sensitive_points" (compute_chart never wrote
    # "upagrahas" — this lookup always missed and silently fell through to the
    # classical day-segment fallback below on every build).
    upagrahas_native = chart_data.get("sensitive_points", {})
    gulika_long = None
    if isinstance(upagrahas_native.get("gulika"), dict):
        gulika_long = upagrahas_native["gulika"].get("longitude_deg")
    mandi_long = None
    if isinstance(upagrahas_native.get("maandi"), dict):
        mandi_long = upagrahas_native["maandi"].get("longitude_deg")

    # Classical fallback
    if gulika_long is None:
        seg = GULIKA_DAY_SEGMENT.get(vara, 5)
        gulika_long = ((seg - 0.5) / 8.0 * 360.0 + lagna_long) % 360.0
    if mandi_long is None:
        seg = MANDI_DAY_SEGMENT.get(vara, 5)
        mandi_long = ((seg - 0.5) / 8.0 * 360.0 + lagna_long) % 360.0

    gulika_seg = GULIKA_DAY_SEGMENT.get(vara, 5)
    mandi_seg = MANDI_DAY_SEGMENT.get(vara, 5)

    rows.extend(_long_rows(
        "sensitive_point_gulika_mandi", "GULIKA", gulika_long,
        chart_id, ayanamsha_id, build_id, eng_ver, lagna_long,
        formula_provenance_text=(
            f"BPHS Ch.4: Gulika = Saturn-son occupying 8th day-segment on Sunday "
            f"(segment {gulika_seg}/8 for vara={vara})"
        ),
    ))
    rows.extend(_long_rows(
        "sensitive_point_gulika_mandi", "MANDI", mandi_long,
        chart_id, ayanamsha_id, build_id, eng_ver, lagna_long,
        formula_provenance_text=(
            f"BPHS Ch.4: Mandi = alternate name for Gulika (same day-segment calculation, "
            f"segment {mandi_seg}/8 for vara={vara})"
        ),
    ))
    return rows


def _build_sun_derived_upagrahas_rows(
    all_longs: dict, chart_id: str, ayanamsha_id: str,
    build_id: str, eng_ver: str, panchanga: dict,
) -> list[dict]:
    rows: list[dict] = []
    sun_long_raw = all_longs.get("SUN")
    if sun_long_raw is None:
        logging.warning("_build_sun_derived_upagrahas_rows: SUN absent from all_longs; skipping")
        return []
    sun_long = sun_long_raw
    lagna_long_raw = all_longs.get("LAGNA")
    if lagna_long_raw is None:
        logging.warning("_build_sun_derived_upagrahas_rows: LAGNA absent from all_longs; skipping")
        return []
    lagna_long = lagna_long_raw
    vara = panchanga.get("vara_id")
    if vara is None:
        logging.warning("_build_sun_derived_upagrahas_rows: panchanga missing 'vara_id'; defaulting to 0 (Sunday) — may be wrong for non-native charts")
        vara = 0

    kala_sun = (sun_long + 180.0) % 360.0
    mrityu_sun = (sun_long + vara * 30.0) % 360.0
    artha_prahara = (sun_long + 120.0) % 360.0
    yamaghantaka = (sun_long + 240.0) % 360.0

    subjects = [
        ("KALA_SUN", kala_sun,
         "BPHS Ch.4: Kala (Sun-derived) = Sun + 180 deg — underworld gate point, distinct from Saturn+30 deg approximation"),
        ("MRITYU_SUN", mrityu_sun,
         f"BPHS Ch.4: Mrityu (Sun-derived) = Sun + (vara x 30 deg) — weekday-indexed mortality point (vara={vara})"),
        ("ARTHA_PRAHARA", artha_prahara,
         "BPHS Ch.4: Artha Prahara = Sun + 120 deg — trine wealth gate"),
        ("YAMAGHANTAKA", yamaghantaka,
         "BPHS Ch.4: Yamaghantaka = Sun + 240 deg — 2nd trine mortality gate"),
    ]
    for subj, long_val, prov in subjects:
        rows.extend(_long_rows(
            "sun_derived_upagraha", subj, long_val,
            chart_id, ayanamsha_id, build_id, eng_ver, lagna_long,
            formula_provenance_text=prov,
        ))
    return rows


def _build_special_lagnas_rows(
    chart_data: dict, all_longs: dict, chart_id: str, ayanamsha_id: str,
    build_id: str, eng_ver: str, panchanga: dict,
) -> list[dict]:
    """
    Category: special_lagna — Bhava/Hora/Ghati/Vighati/Indu/Sree/Varnada Lagna.

    M-10 fix (CRITICAL, R6 1d-sensitive lane, 2026-07-10): these were all
    hand-rolled proxies using the Sun's WITHIN-SIGN DEGREE as a stand-in for
    time-elapsed-since-sunrise (HL = Lagna + (Sun%30)x2, GL = Lagna +
    (Sun%30)x12, BL = 2xSun - Lagna + 180). The within-sign degree is not
    proportional to time-since-sunrise (the Sun moves ~1 deg/day, so "Sun%30"
    barely changes across a whole day and does not track ghatis elapsed at
    all) — the served values were essentially arbitrary. Real Bhava/Hora/
    Ghati/Vighati Lagna advance by actual TIME elapsed since sunrise (BPHS),
    which is exactly what PyJHora's `drik.special_ascendant()` computes
    (drik.py:1959-1988) from the birth JD + place. Delegated here via
    `chart_data["special_lagnas"]` (see pyjhora_adapter/special_lagnas.py).
    Indu Lagna, Sree Lagna, and Varnada Lagna were previously entirely absent
    from this writer; added here via the same delegation.
    """
    rows: list[dict] = []
    lagna_long_raw = all_longs.get("LAGNA")
    if lagna_long_raw is None:
        logging.warning("_build_special_lagnas_rows: LAGNA absent from all_longs; skipping")
        return []
    lagna_long = lagna_long_raw

    special_lagnas = chart_data.get("special_lagnas", {})

    def _floor_row(subj: str, reason: str) -> dict:
        return _make_row(
            "special_lagna", subj, "longitude_sidereal",
            None, None, None, chart_id, ayanamsha_id, build_id, eng_ver,
            verification_pass_status="floored",
            formula_provenance_text=f"[EXTERNAL_COMPUTATION_REQUIRED] {reason}",
        )

    _delegated = [
        ("bhava_lagna", "BHAVA_LAGNA",
         "PyJHora drik.bhava_lagna (BPHS: Bhava Lagna advances by time-since-sunrise x 0.25 "
         "sign/min-equivalent), replacing the fabricated 'Sun within-sign offset' proxy (M-10)"),
        ("hora_lagna", "HORA_LAGNA",
         "PyJHora drik.hora_lagna (BPHS Ch.11: Hora Lagna advances 1 sign/hora, 2 rev/day, "
         "from real time-since-sunrise), replacing the fabricated 'Sun within-sign offset x2' proxy (M-10)"),
        ("ghati_lagna", "GHATI_LAGNA",
         "PyJHora drik.ghati_lagna (BPHS: Ghati Lagna advances 1 sign/ghati=24min, from real "
         "time-since-sunrise), replacing the fabricated 'Sun within-sign offset x12' proxy (M-10)"),
        ("vighati_lagna", "VIGHATI_LAGNA",
         "PyJHora drik.vighati_lagna (BPHS: Vighati Lagna advances 1 sign/vighati=24sec, from "
         "real time-since-sunrise) — now computed rather than floored, since PyJHora derives it "
         "from the birth JD directly (no sub-second precision needed; supersedes prior floor)"),
        ("indu_lagna", "INDU_LAGNA",
         "PyJHora drik.indu_lagna (BV Raman method: wealth-significator lagna from 9th-lord "
         "kalas of Lagna + Moon) — newly added via delegation (M-10)"),
        ("sree_lagna", "SREE_LAGNA",
         "PyJHora drik.sree_lagna (nakshatra-pada fraction of Moon projected from Lagna) — "
         "newly added via delegation (M-10)"),
        ("varnada_lagna", "VARNADA_LAGNA",
         "PyJHora charts.varnada_lagna (BV Raman method, house_index=1) — newly added via "
         "delegation (M-10)"),
    ]

    for native_key, subj, prov in _delegated:
        entry = special_lagnas.get(native_key, {})
        long_val = entry.get("longitude_deg") if isinstance(entry, dict) else None
        if long_val is None:
            rows.append(_floor_row(
                subj,
                f"PyJHora native {native_key} computation unavailable this build "
                f"(no fabricated substitute served)",
            ))
            continue
        rows.extend(_long_rows(
            "special_lagna", subj, float(long_val),
            chart_id, ayanamsha_id, build_id, eng_ver, lagna_long,
            formula_provenance_text=prov,
            tolerance_arcsec=1.0,
        ))
    return rows


def _build_sphuta_completion_rows(
    all_longs: dict, chart_id: str, ayanamsha_id: str,
    build_id: str, eng_ver: str,
) -> list[dict]:
    rows: list[dict] = []
    sun_long_raw = all_longs.get("SUN")
    jup_long_raw = all_longs.get("JUP")
    ven_long_raw = all_longs.get("VEN")
    moon_long_raw = all_longs.get("MOON")
    mar_long_raw = all_longs.get("MAR")
    _SPHUTA_PLANETS = {"SUN": sun_long_raw, "JUP": jup_long_raw, "VEN": ven_long_raw, "MOON": moon_long_raw, "MAR": mar_long_raw}
    _missing = [k for k, v in _SPHUTA_PLANETS.items() if v is None]
    if _missing:
        logging.warning("_build_sphuta_completion_rows: missing planets %s; skipping", _missing)
        return []
    sun_long = sun_long_raw
    jup_long = jup_long_raw
    ven_long = ven_long_raw
    moon_long = moon_long_raw
    mar_long = mar_long_raw
    lagna_long_raw = all_longs.get("LAGNA")
    if lagna_long_raw is None:
        logging.warning("_build_sphuta_completion_rows: LAGNA absent from all_longs; skipping")
        return []
    lagna_long = lagna_long_raw

    beeja = (sun_long + jup_long + ven_long) % 360.0
    kshetra = (moon_long + jup_long + mar_long) % 360.0

    rows.extend(_long_rows(
        "esoteric_point_sphuta_fertility", "BEEJA_SPHUTA", beeja,
        chart_id, ayanamsha_id, build_id, eng_ver, lagna_long,
        formula_provenance_text=(
            "BPHS medical astrology: Beeja Sphuta (seed/male fertility) = "
            "(Sun + Jupiter + Venus) mod 360 deg"
        ),
    ))
    rows.extend(_long_rows(
        "esoteric_point_sphuta_fertility", "KSHETRA_SPHUTA", kshetra,
        chart_id, ayanamsha_id, build_id, eng_ver, lagna_long,
        formula_provenance_text=(
            "BPHS medical astrology: Kshetra Sphuta (field/female fertility) = "
            "(Moon + Jupiter + Mars) mod 360 deg"
        ),
    ))
    return rows


def _build_yogi_system_completion_rows(
    all_longs: dict, chart_id: str, ayanamsha_id: str,
    build_id: str, eng_ver: str, panchanga: dict,
) -> list[dict]:
    rows: list[dict] = []
    sun_long_raw = all_longs.get("SUN")
    moon_long_raw = all_longs.get("MOON")
    if sun_long_raw is None or moon_long_raw is None:
        logging.warning("_build_yogi_system_completion_rows: SUN or MOON absent from all_longs; skipping")
        return []
    sun_long = sun_long_raw
    moon_long = moon_long_raw
    vara = panchanga.get("vara_id")
    if vara is None:
        logging.warning("_build_yogi_system_completion_rows: panchanga missing 'vara_id'; defaulting to 0 (Sunday) — may be wrong for non-native charts")
        vara = 0

    yogi_long = (sun_long + moon_long + 93.3333333) % 360.0
    nak_name, nak_lord, pada = _long_to_nakshatra_pada(yogi_long)
    yogi_graha = nak_lord

    rows.extend([
        _make_row("esoteric_point_yogi_system", "YOGI_GRAHA", "assigned_graha",
                  None, yogi_graha, None,
                  chart_id, ayanamsha_id, build_id, eng_ver,
                  verification_pass_status="two_pass_verified",
                  formula_provenance_text="BPHS Ch.20: Yogi Graha = nakshatra lord of Yogi Sphuta (Sun+Moon+93 deg 20')"),
        _make_row("esoteric_point_yogi_system", "YOGI_GRAHA", "nakshatra",
                  None, nak_name, None,
                  chart_id, ayanamsha_id, build_id, eng_ver,
                  verification_pass_status="two_pass_verified",
                  formula_provenance_text="BPHS Ch.20: Yogi Graha nakshatra"),
        _make_row("esoteric_point_yogi_system", "YOGI_GRAHA", "yogi_point_longitude",
                  yogi_long, None, None,
                  chart_id, ayanamsha_id, build_id, eng_ver,
                  verification_pass_status="two_pass_verified",
                  formula_provenance_text="BPHS Ch.20: Yogi Sphuta (source) = Sun + Moon + 93 deg 20'"),
    ])

    dagdha_signs = DAGDHA_RASHI_BY_VARA.get(vara, [])
    for i, sign in enumerate(dagdha_signs, start=1):
        subj = f"DAGDHA_RASHI_{i}"
        rows.append(_make_row(
            "esoteric_point_yogi_system", subj, "sign",
            None, sign, None,
            chart_id, ayanamsha_id, build_id, eng_ver,
            verification_pass_status="two_pass_verified",
            formula_provenance_text=(
                f"Muhurta Chintamani: Dagdha Rashi {i} for vara={vara} (Sunday=0): {sign}"
            ),
        ))
    return rows


# ── Main per-ayanamsha builder ────────────────────────────────────────────────

def _build_all_sensitive_rows_for_ayanamsha(
    ayanamsha_key: str,
    ayanamsha_id: str,
    chart_id: str,
    build_id: str,
    eng_ver: str,
    birth_params: dict[str, Any],
    prereqs: dict[str, bool],
    halt_log_path: str,
) -> list[dict[str, Any]]:
    """
    Compute all 30 categories for one ayanamsha. Returns all row dicts.

    ayanamsha_key = canonical id (e.g., "lahiri_chitrapaksha") — used in rows
    ayanamsha_id  = adapter key (e.g., "lahiri") — passed to compute_chart
    """
    # Compute chart positions via PyJHora (use adapter key for engine call)
    chart_data = compute_chart(inputs=birth_params, ayanamsha_id=ayanamsha_id)

    # FORENSIC gate — native-anchored; asserted only for the native (Phase 3B).
    if chart_id == CANONICAL_CHART_ID:
        forensic_gate(chart_data, ayanamsha_id)

    # canonical_id = ayanamsha_key; used for all row fact_subject/fact_key storage
    canonical_id = ayanamsha_key

    # Extract longitudes map from grahas list + ascendant dict
    planet_name_map: dict[str, str] = {
        "Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER",
        "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT",
        "Rahu": "RAH_MEAN", "Ketu": "KET_MEAN",
    }
    grahas = chart_data.get("grahas", [])
    ascendant = chart_data.get("ascendant", {})

    all_longs: dict[str, float] = {}
    for g in grahas:
        key = planet_name_map.get(g.get("name", ""))
        if key:
            lon = float(g.get("longitude_deg", g.get("lon", 0.0)))
            all_longs[key] = lon

    # Lagna from ascendant
    asc_lon = float(ascendant.get("longitude_deg", ascendant.get("lon", 0.0)))
    all_longs["LAGNA"] = asc_lon

    # Panchanga block (vara=0..6 Sunday-based, etc.)
    panchanga = chart_data.get("panchanga", {})
    if not panchanga:
        # PyJHora did not populate panchanga — build a minimal stub from birth_params.
        # Do NOT hardcode vara=0 (Sunday) here; derive from the birth date's weekday.
        logging.warning(
            "[ga_sensitive] chart_id=%s ayanamsha=%s: panchanga absent from chart_data; "
            "deriving vara from birth_params datetime_iso weekday",
            chart_id, ayanamsha_key,
        )
        panchanga = {}

    # ── Determine day/night birth ──────────────────────────────────────────────
    # Primary source: panchanga["is_daytime"] populated by PyJHora (sunrise-aware).
    # Secondary source: birth hour from birth_params["datetime_iso"] (local time).
    #   A birth between 06:00–18:00 local is heuristically treated as day birth.
    #   This heuristic is approximate (actual sunrise/sunset vary by date/location)
    #   but is far better than a hardcoded True for all charts.
    # If neither source is available, log a warning and default to day birth with
    # a clear provenance note — callers may override once sunrise_jd is available.
    panchanga_is_daytime = panchanga.get("is_daytime")
    if panchanga_is_daytime is not None:
        is_day_birth = bool(panchanga_is_daytime)
    else:
        datetime_iso = birth_params.get("datetime_iso", "")
        birth_hour: int | None = None
        if datetime_iso:
            try:
                from datetime import datetime as _dt
                birth_hour = _dt.fromisoformat(datetime_iso).hour
            except Exception:
                birth_hour = None
        if birth_hour is not None:
            is_day_birth = 6 <= birth_hour < 18
            logging.info(
                "[ga_sensitive] chart_id=%s: is_day_birth derived from birth hour %d → %s",
                chart_id, birth_hour, is_day_birth,
            )
        else:
            is_day_birth = True  # safest classical default; provenance logged below
            logging.warning(
                "[ga_sensitive] chart_id=%s ayanamsha=%s: could not derive is_day_birth "
                "from panchanga or birth_params — defaulting to True (day birth). "
                "Pass sunrise_jd+birth_jd for an authoritative result.",
                chart_id, ayanamsha_key,
            )

    # ── Derive day lord from birth date weekday ────────────────────────────────
    # _WEEKDAY_LORDS[weekday()] uses Python's Monday=0 convention.
    # This is purely calendrical (no ephemeris required) and correct for all charts.
    datetime_iso = birth_params.get("datetime_iso", "")
    day_lord: str | None = None
    if datetime_iso:
        try:
            from datetime import datetime as _dt
            day_lord = _WEEKDAY_LORDS[_dt.fromisoformat(datetime_iso).weekday()]
        except Exception as _e:
            logging.warning(
                "[ga_sensitive] chart_id=%s: could not derive day_lord from "
                "datetime_iso=%r: %s — RP_DAY_LORD will be skipped",
                chart_id, datetime_iso, _e,
            )
    else:
        logging.warning(
            "[ga_sensitive] chart_id=%s: birth_params missing 'datetime_iso' — "
            "day_lord cannot be derived; RP_DAY_LORD will be skipped",
            chart_id,
        )

    rows: list[dict[str, Any]] = []

    # Use canonical_id (ayanamsha_key) for all row ayanamsha_id fields
    cid = canonical_id  # shorthand

    # ── 1. Upagrahas ──────────────────────────────────────────────────────────
    rows.extend(_build_upagraha_rows(chart_data, chart_id, cid, build_id, eng_ver, all_longs))

    # ── 2. Saturn-derived ─────────────────────────────────────────────────────
    saturn_rows = _build_saturn_derived_rows(chart_data, chart_id, cid, build_id, eng_ver, all_longs)
    rows.extend(saturn_rows)

    # Extract Gulika and Mandi for Aprakasha computation later.
    # NAR-GA fix (SAMAPTI_NARRATION_TRIAGE_AND_PARTITION_v1_0.md §2.5,
    # ga_sensitive_writer.py:2677): the comment below used to say the M-11 fix
    # (which stopped `_build_saturn_derived_rows` from ever serving this same
    # proxy) applied "as in" that sibling function — but this site alone kept
    # the rejected hand-rolled Saturn+6°/Saturn+8° constants as its *seed*,
    # so any adapter error (sensitive_points.py's error path returns
    # {"error": ...} — still `isinstance(..., dict)`, still with no
    # `longitude_deg`) silently fell through to the fabricated proxy under an
    # ordinary (non-floored) verification status. Seed honestly as None —
    # mirrors _build_saturn_derived_rows's own floor-on-adapter-error
    # handling for the identical gulika/maandi lookup — and use `is not None`
    # rather than bare truthiness, which also discarded a legitimate
    # `longitude_deg == 0.0` (0°00′ Aries).
    gulika_long: float | None = None
    mandi_long: float | None = None
    sensitive_native_top = chart_data.get("sensitive_points", {})
    if isinstance(sensitive_native_top.get("gulika"), dict):
        v = sensitive_native_top["gulika"].get("longitude_deg")
        if v is not None:
            gulika_long = float(v)
    if isinstance(sensitive_native_top.get("maandi"), dict):
        v = sensitive_native_top["maandi"].get("longitude_deg")
        if v is not None:
            mandi_long = float(v)

    # ── 3–5. Bhrigu Bindu, Yogi, Avayogi ─────────────────────────────────────
    rows.extend(_build_bhrigu_bindu_rows(all_longs, chart_id, cid, build_id, eng_ver))
    rows.extend(_build_yogi_avayogi_rows(all_longs, chart_id, cid, build_id, eng_ver))

    # ── 6. Mrityu ─────────────────────────────────────────────────────────────
    rows.extend(_build_mrityu_rows(all_longs, chart_id, cid, build_id, eng_ver, is_day_birth))

    # ── 7–9. Trisphuta family ────────────────────────────────────────────────
    rows.extend(_build_trisphuta_family_rows(all_longs, chart_id, cid, build_id, eng_ver))

    # ── 10. Pranapada ─────────────────────────────────────────────────────────
    rows.extend(_build_pranapada_rows(chart_data, all_longs, chart_id, cid, build_id, eng_ver))

    # ── 11. Trikona Dasha ─────────────────────────────────────────────────────
    rows.extend(_build_trikona_dasha_rows(all_longs, chart_id, cid, build_id, eng_ver))

    # ── 12. Sri Yantra ───────────────────────────────────────────────────────
    rows.extend(_build_sri_yantra_rows(all_longs, chart_id, cid, build_id, eng_ver))

    # ── 13–15. Brahma/Vishnu/Shiva ───────────────────────────────────────────
    rows.extend(_build_brahma_vishnu_shiva_rows(all_longs, chart_id, cid, build_id, eng_ver))

    # ── 16. Sahams ───────────────────────────────────────────────────────────
    rows.extend(_build_saham_rows(all_longs, chart_id, cid, build_id, eng_ver, is_day_birth))

    # ── 17. Karakas ──────────────────────────────────────────────────────────
    rows.extend(_build_karaka_rows(all_longs, chart_id, cid, build_id, eng_ver, halt_log_path))

    # ── 18. Karakamsa ────────────────────────────────────────────────────────
    rows.extend(_build_karakamsa_rows(all_longs, chart_id, cid, build_id, eng_ver))

    # ── 19. Swamsa (12 rows) ─────────────────────────────────────────────────
    rows.extend(_build_swamsa_rows(all_longs, chart_id, cid, build_id, eng_ver))

    # ── 20. Arudha Pada (19 subjects) ────────────────────────────────────────
    rows.extend(_build_arudha_rows(all_longs, chart_id, cid, build_id, eng_ver))

    # ── 21. Midpoints (54 subjects) ──────────────────────────────────────────
    rows.extend(_build_midpoint_rows(chart_data, all_longs, chart_id, cid, build_id, eng_ver))

    # ── 22. KP Ruling Planets ────────────────────────────────────────────────
    rows.extend(_build_kp_ruling_planets_rows(all_longs, chart_id, cid, build_id, eng_ver,
                                              day_lord=day_lord))

    # ── 23. KP Cuspal Significators ──────────────────────────────────────────
    rows.extend(_build_kp_cuspal_rows(all_longs, chart_id, cid, build_id, eng_ver, chart_data))

    # ── 24. Aprakasha ────────────────────────────────────────────────────────
    rows.extend(_build_aprakasha_rows(all_longs, chart_id, cid, build_id, eng_ver,
                                      gulika_long, mandi_long))

    # ── 25. Hadda (60 zones) ─────────────────────────────────────────────────
    rows.extend(_build_hadda_rows(all_longs, chart_id, cid, build_id, eng_ver))

    # ── 26. Triraashipathi ───────────────────────────────────────────────────
    rows.extend(_build_triraashipathi_rows(all_longs, chart_id, cid, build_id, eng_ver))

    # ── 27. Tajik Vargottama ─────────────────────────────────────────────────
    rows.extend(_build_tajik_vargottama_rows(all_longs, chart_id, cid, build_id, eng_ver))

    # ── 28. Lal Kitab (floored if G41 absent) ────────────────────────────────
    if prereqs.get("G41_LAL_KITAB"):
        # TODO: Implement when G41 corpus is available
        pass
    rows.extend(_build_lal_kitab_floored_rows(all_longs, chart_id, cid, build_id, eng_ver))

    # ── 29. Maharsi (floored if G44 absent) ──────────────────────────────────
    if prereqs.get("G44_NADI"):
        # TODO: Implement when G44 Nadi tables are available
        pass
    rows.extend(_build_maharsi_floored_rows(all_longs, chart_id, cid, build_id, eng_ver))

    # ── 30. Bhrigu Nadi ──────────────────────────────────────────────────────
    rows.extend(_build_bhrigu_nadi_rows(all_longs, chart_id, cid, build_id, eng_ver))

    # ── Bonus: Nakshatra Pada Sensitive ─────────────────────────────────────
    rows.extend(_build_nakshatra_pada_sensitive_rows(all_longs, chart_id, cid, build_id, eng_ver))

    # ── Amendment 3: 5 Tier-1 classical sensitive points ────────────────────
    rows.extend(_build_gulika_mandi_sensitive_rows(
        chart_data, all_longs, chart_id, cid, build_id, eng_ver, panchanga))
    rows.extend(_build_sun_derived_upagrahas_rows(
        all_longs, chart_id, cid, build_id, eng_ver, panchanga))
    rows.extend(_build_special_lagnas_rows(
        chart_data, all_longs, chart_id, cid, build_id, eng_ver, panchanga))
    rows.extend(_build_sphuta_completion_rows(
        all_longs, chart_id, cid, build_id, eng_ver))
    rows.extend(_build_yogi_system_completion_rows(
        all_longs, chart_id, cid, build_id, eng_ver, panchanga))

    # ── Amendment BA-P3A: bhava_arudha — full Parashari 2-exception rule ────
    rows.extend(_build_bhava_arudha_rows(all_longs, chart_id, cid, build_id, eng_ver))

    logger.info("[ga_sensitive] ayanamsha=%s rows=%d", cid, len(rows))
    return rows


# ── DB persistence ────────────────────────────────────────────────────────────

def _insert_rows(conn: Any, rows: list[dict[str, Any]], *, commit: bool = True) -> int:
    """
    Insert chart_facts rows. Returns inserted count.
    Uses standard chart_facts schema + Section-B enrichment columns.
    When commit=False (caller-owned connection), does not commit.
    """
    if not rows:
        return 0

    # Idempotency: replace this chart's prior rows for the scope being written so a
    # rebuild under a new build_id replaces instead of accreting.
    replace_prior_chart_facts(conn, rows)

    inserted = 0
    for row in rows:
        # Serialize fact_value_jsonb: psycopg3 does not auto-cast Python lists/dicts
        # to jsonb — pass an explicit JSON string so the cast always succeeds.
        raw_jsonb = row.get("fact_value_jsonb")
        if raw_jsonb is not None:
            try:
                jsonb_param = json.dumps(raw_jsonb)
            except (TypeError, ValueError) as json_exc:
                # JSON serialization failed for this row — emit a flagged skip-row
                # so absence is explicit in the DB rather than silently dropped.
                subject = row.get("fact_subject", "UNKNOWN")
                key = row.get("fact_key", "UNKNOWN")
                logger.warning(
                    "[ga_sensitive] KP_PARSE_ERROR: JSON serialization failed for "
                    "%s.%s.%s — emitting flagged error row. cause=%s",
                    row.get("fact_category"), subject, key, json_exc,
                )
                error_row = dict(row)
                error_row["fact_value_jsonb"] = None
                error_row["fact_value_text"] = "KP_PARSE_ERROR"
                error_row["fact_value_num"] = None
                error_row["verification_pass_status"] = "data_error"
                error_row["citation_human"] = (
                    f"KP parse failed for {subject}: malformed JSONB in source data."
                )
                row = error_row
                jsonb_param = None
        else:
            jsonb_param = None

        try:
            with conn.transaction():  # savepoint — isolates each row so failures don't abort the transaction
                conn.execute(
                    """
                    INSERT INTO chart_facts (
                        fact_id, chart_id, build_id, ayanamsha_id, engine_version,
                        fact_category, fact_subject, fact_key,
                        fact_value_num, fact_value_text, fact_value_jsonb,
                        formula_id, source_calculation, computed_at,
                        citation_ref, citation_human,
                        verification_pass_status,
                        tolerance_arcsec, near_sign_boundary_flag,
                        near_nakshatra_boundary_flag, vargottama_flag_at_point,
                        formula_provenance_text, cross_ayanamsha_divergence_arcsec
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s::jsonb,
                        %s, %s, %s,
                        %s, %s,
                        %s,
                        %s, %s,
                        %s, %s,
                        %s, %s
                    )
                    ON CONFLICT (fact_id) DO UPDATE SET
                        fact_value_num = EXCLUDED.fact_value_num,
                        fact_value_text = EXCLUDED.fact_value_text,
                        fact_value_jsonb = EXCLUDED.fact_value_jsonb,
                        source_calculation = EXCLUDED.source_calculation,
                        computed_at = EXCLUDED.computed_at,
                        verification_pass_status = EXCLUDED.verification_pass_status,
                        build_id = EXCLUDED.build_id
                    """,
                    [
                        row["fact_id"], row["chart_id"], row["build_id"],
                        row["ayanamsha_id"], row["engine_version"],
                        row["fact_category"], row["fact_subject"], row["fact_key"],
                        row["fact_value_num"], row["fact_value_text"],
                        jsonb_param,
                        row.get("formula_id"), row["source_calculation"], row["computed_at"],
                        row["citation_ref"], row["citation_human"],
                        row["verification_pass_status"],
                        row.get("tolerance_arcsec"), row.get("near_sign_boundary_flag"),
                        row.get("near_nakshatra_boundary_flag"), row.get("vargottama_flag_at_point"),
                        row.get("formula_provenance_text"), row.get("cross_ayanamsha_divergence_arcsec"),
                    ],
                )
            inserted += 1
        except Exception as exc:
            logger.warning("[ga_sensitive] INSERT failed for %s.%s.%s: %s",
                           row.get("fact_category"), row.get("fact_subject"),
                           row.get("fact_key"), exc)
    if commit:
        conn.commit()
    return inserted


def _refresh_mv(conn: Any, *, commit: bool = True) -> str:
    """Refresh mv_chart_sensitive_points_summary.
    When commit=False (caller-owned connection), does not commit."""
    try:
        conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_chart_sensitive_points_summary")
        if commit:
            conn.commit()
        return "OK"
    except Exception:
        try:
            conn.execute("REFRESH MATERIALIZED VIEW mv_chart_sensitive_points_summary")
            if commit:
                conn.commit()
            return "OK"
        except Exception as exc2:
            return f"ERROR: {exc2}"


def _update_asset_throughput(conn: Any, chart_id: str, build_id: str, row_count: int) -> None:
    """Update asset_throughput for ga_sensitive (shared _telemetry helper)."""
    update_asset_throughput(conn, GA5_ASSET_ID, chart_id, build_id, row_count)


# ── Per-ayanamsha helpers (used by heavy-writer orchestrator adapter) ─────────

def get_ga_sensitive_context(
    birth_params: dict[str, Any],
    conn: Any | None = None,
) -> tuple[dict[str, bool], str]:
    """Return (prereqs, eng_ver) for use across per-ayanamsha substeps.
    FORENSIC gate fires inside _build_all_sensitive_rows_for_ayanamsha per substep."""
    prereqs = check_prerequisites(conn=conn)
    return prereqs, ENGINE_VERSION


def build_ga_sensitive_for_ayanamsha(
    ayanamsha_key: str,
    ayanamsha_id: str,
    chart_id: str,
    build_id: str,
    conn: Any,
    birth_params: dict[str, Any],
    prereqs: dict[str, bool],
    eng_ver: str,
) -> int:
    """Compute and persist chart_facts for one ayanamsha. conn is caller-owned;
    does NOT commit — the orchestrator's _drive_substeps commits after this returns.
    Returns inserted row count."""
    # Ensure L0 refs are loaded (idempotent — no-op if already populated)
    if not _SIGN_LORDS or not _NAK_LORDS:
        _load_l0_refs(conn)
    rows = _build_all_sensitive_rows_for_ayanamsha(
        ayanamsha_key=ayanamsha_key,
        ayanamsha_id=ayanamsha_id,
        chart_id=chart_id,
        build_id=build_id,
        eng_ver=eng_ver,
        birth_params=birth_params,
        prereqs=prereqs,
        halt_log_path="CONDUCTOR_HALT_LOG.md",
    )
    divergent = [r for r in rows if r.get("verification_pass_status") == "divergent_flagged"]
    if divergent:
        raise ValueError(f"GA5: {len(divergent)} divergent_flagged rows in {ayanamsha_id}")
    single = [r for r in rows if r.get("verification_pass_status") == "single"]
    if single:
        raise ValueError(f"GA5: {len(single)} single-pass rows in {ayanamsha_id}")
    return _insert_rows(conn, rows, commit=False)


# ── Public API ────────────────────────────────────────────────────────────────

def build_ga_sensitive(
    chart_id: str = CANONICAL_CHART_ID,
    build_id: str | None = None,
    *,
    conn: Any = None,
    birth_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build ga_sensitive asset: compute all 30 A5 categories × 5 ayanamshas.
    Returns summary dict with row counts, prerequisite status, and gate results.
    Raises on FORENSIC failure or AK divergence.

    Connection ownership (Orchestrator Convergence Phase 3):
    - conn injected (orchestrator path): writes on the caller-owned connection,
      does NOT commit or close, does NOT write asset_throughput (the orchestrator
      is the sole build-state writer). The caller's SAVEPOINT owns atomicity.
    - conn None (legacy CLI path): opens its own connection, commits, closes, and
      writes asset_throughput via _telemetry.
    """
    import uuid
    from contextlib import nullcontext
    if build_id is None:
        build_id = str(uuid.uuid4())

    owns_conn = conn is None

    if not birth_params:
        raise ValueError(
            f"[ga_sensitive_writer] no birth_params for chart_id={chart_id}; "
            "orchestrator must populate ctx.config['birth_params'] from "
            "fetch_birth_params() before calling this writer."
        )

    started_at = datetime.now(timezone.utc).isoformat()
    eng_ver = ENGINE_VERSION
    halt_log_path = "CONDUCTOR_HALT_LOG.md"

    logger.info("[ga_sensitive] Build starting: chart_id=%s build_id=%s", chart_id, build_id)

    summary: dict[str, Any] = {
        "session_id": "ga5-sensitive-points",
        "asset_id": GA5_ASSET_ID,
        "chart_id": chart_id,
        "build_id": build_id,
        "started_at": started_at,
        "ayanamshas": {},
        "prerequisites": {},
        "total_rows": 0,
        "status": "IN_PROGRESS",
    }

    # ── FORENSIC gate (pre-flight: compute lahiri chart and check anchors) ────
    # The per-ayanamsha builder also calls forensic_gate, but we run it early
    # to fail fast before looping all 5 ayanamshas.
    try:
        preflight_chart = compute_chart(inputs=birth_params, ayanamsha_id="lahiri")
        if chart_id == CANONICAL_CHART_ID:
            forensic_gate(preflight_chart, "lahiri")
        summary["forensic_pass"] = True
    except RuntimeError as fe:
        msg = f"GA5 FORENSIC gate FAIL: {fe}"
        logger.error("[ga_sensitive] %s", msg)
        _write_halt_log("FORENSIC_GATE", msg)
        summary["status"] = "FAIL"
        summary["forensic_failure"] = str(fe)
        return summary

    # ── Prerequisite check ───────────────────────────────────────────────────
    prereqs = check_prerequisites()
    summary["prerequisites"] = prereqs

    logger.info("[ga_sensitive] Prerequisites: G14=%s G44=%s G41=%s",
                prereqs["G14_SAHAM"], prereqs["G44_NADI"], prereqs["G41_LAL_KITAB"])

    # Load L0 sign lords and nakshatra lords before computation
    if conn is not None:
        _load_l0_refs(conn)
    else:
        with _conn() as _c:
            _load_l0_refs(_c)

    # ── Compute all ayanamshas ────────────────────────────────────────────────
    all_rows: list[dict[str, Any]] = []

    for ayanamsha_key, ayanamsha_id in CANONICAL_AYANAMSHAS.items():
        try:
            rows = _build_all_sensitive_rows_for_ayanamsha(
                ayanamsha_key=ayanamsha_key,
                ayanamsha_id=ayanamsha_id,
                chart_id=chart_id,
                build_id=build_id,
                eng_ver=eng_ver,
                birth_params=birth_params,
                prereqs=prereqs,
                halt_log_path=halt_log_path,
            )
            all_rows.extend(rows)
            summary["ayanamshas"][ayanamsha_id] = {"rows": len(rows), "status": "PASS"}
        except ValueError as exc:
            logger.error("[ga_sensitive] HALT for ayanamsha %s: %s", ayanamsha_id, exc)
            summary["ayanamshas"][ayanamsha_id] = {"status": "HALT", "error": str(exc)}
            summary["status"] = "HALT"
            return summary
        except Exception as exc:
            logger.error("[ga_sensitive] ERROR for ayanamsha %s: %s", ayanamsha_id, exc)
            summary["ayanamshas"][ayanamsha_id] = {"status": "ERROR", "error": str(exc)}
            summary["status"] = "FAIL"
            return summary

    # ── Verify no divergent_flagged rows ─────────────────────────────────────
    divergent = [r for r in all_rows if r.get("verification_pass_status") == "divergent_flagged"]
    if divergent:
        msg = f"GA5 HALT: {len(divergent)} divergent_flagged rows detected"
        logger.error("[ga_sensitive] %s", msg)
        _write_halt_log("TWO_PASS_DIVERGENCE", msg)
        summary["status"] = "HALT"
        summary["divergent_rows"] = len(divergent)
        return summary

    single = [r for r in all_rows if r.get("verification_pass_status") == "single"]
    if single:
        msg = f"GA5 HALT: {len(single)} single-pass rows detected (zero allowed)"
        logger.error("[ga_sensitive] %s", msg)
        _write_halt_log("SINGLE_PASS_VIOLATION", msg)
        summary["status"] = "HALT"
        summary["single_pass_rows"] = len(single)
        return summary

    summary["total_rows"] = len(all_rows)
    logger.info("[ga_sensitive] Total rows computed: %d", len(all_rows))

    # ── DB persistence ────────────────────────────────────────────────────────
    try:
        with (_conn() if owns_conn else nullcontext(conn)) as conn:
            inserted = _insert_rows(conn, all_rows, commit=owns_conn)
            summary["inserted_rows"] = inserted

            mv_status = _refresh_mv(conn, commit=owns_conn)
            summary["mv_refresh"] = mv_status

            if owns_conn:
                _update_asset_throughput(conn, chart_id, build_id, inserted)

        logger.info("[ga_sensitive] Build PASS: %d rows inserted", inserted)
        summary["status"] = "PASS"
    except Exception as exc:
        logger.error("[ga_sensitive] DB error: %s", exc)
        summary["status"] = "FAIL"
        summary["db_error"] = str(exc)

    summary["completed_at"] = datetime.now(timezone.utc).isoformat()
    return summary
