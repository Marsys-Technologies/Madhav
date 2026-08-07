"""
brahmagyan.l0_transit — L0 Brahmagyan: Transit/Gochara Reference Tables
=========================================================================

Populates three reference tables:
  1. bg_transit_engine  — graha average motions and period data
  2. bg_transit_rules   — classical Gochara rules from BPHS, Phaladeepika, Saravali
  3. bg_transit_moorti  — BA-P7A: Moorti Nirnaya (27 nakshatra-offset → quality tier)

Chart-agnostic static reference data only (L0 Brahmagyan layer).
ZERO LLM — all data is hardcoded attested classical values.

Sources:
  BPHS = Brihat Parashara Hora Shastra
  PD   = Phaladeepika by Mantresvara
  SS   = Saravali by Kalyana Varma
  UK   = Uttara Kalamrita by Kalidasa

Volume: 9 engine rows + ~55 rule rows + 27 moorti rows.

Gate: Transit/Gochara Subsystem Gate-1
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Citation constants ─────────────────────────────────────────────────────────

BPHS_CH29 = "BPHS Ch.29 (Gochara Phala — Transit Results)"
BPHS_CH28 = "BPHS Ch.28 (Nakshatra Gochara + Moorti Nirnaya)"
BPHS_CH22 = "BPHS Ch.22 (Graha Gati — Planetary Motion)"
PD_CH26   = "Phaladeepika Ch.26 (Gochara Vedha and Transit Phala)"
SS_CH12   = "Saravali Ch.12 (Gochara Phala adhyaya)"
UK_CH4    = "Uttara Kalamrita Ch.4 (Graha Bala — Gochara context)"

# ── §1 — BG_TRANSIT_ENGINE: Graha average motion parameters ──────────────────
#
# avg_daily_motion_deg: classical average daily motion in degrees
# zodiac_period_days:   approximate time for one full zodiac traversal
# sign_residence_days:  average days spent per sign
# classical_citation:   textual source for motion parameters

BG_TRANSIT_ENGINE: list[dict[str, Any]] = [
    {
        "graha": "sun",
        "avg_daily_motion_deg": 0.9856,
        "zodiac_period_days": 365.25,
        "sign_residence_days": 30.44,
        "classical_citation": BPHS_CH22,
    },
    {
        "graha": "moon",
        "avg_daily_motion_deg": 13.1764,
        "zodiac_period_days": 27.32,
        "sign_residence_days": 2.28,
        "classical_citation": BPHS_CH22,
    },
    {
        "graha": "mars",
        "avg_daily_motion_deg": 0.5240,
        "zodiac_period_days": 686.97,
        "sign_residence_days": 45.0,
        "classical_citation": BPHS_CH22,
    },
    {
        "graha": "mercury",
        "avg_daily_motion_deg": 1.3833,
        "zodiac_period_days": 87.97,
        "sign_residence_days": 14.0,
        "classical_citation": BPHS_CH22,
    },
    {
        "graha": "jupiter",
        "avg_daily_motion_deg": 0.0831,
        "zodiac_period_days": 4332.59,
        "sign_residence_days": 361.05,
        "classical_citation": BPHS_CH22,
    },
    {
        "graha": "venus",
        "avg_daily_motion_deg": 1.2000,
        "zodiac_period_days": 224.70,
        "sign_residence_days": 23.0,
        "classical_citation": BPHS_CH22,
    },
    {
        "graha": "saturn",
        "avg_daily_motion_deg": 0.0335,
        "zodiac_period_days": 10759.22,
        "sign_residence_days": 913.37,
        "classical_citation": BPHS_CH22,
    },
    {
        "graha": "rahu",
        "avg_daily_motion_deg": -0.0529,
        "zodiac_period_days": 6793.50,
        "sign_residence_days": 548.00,
        "classical_citation": BPHS_CH22,
    },
    {
        "graha": "ketu",
        "avg_daily_motion_deg": -0.0529,
        "zodiac_period_days": 6793.50,
        "sign_residence_days": 548.00,
        "classical_citation": BPHS_CH22,
    },
]

# ── §2 — BG_TRANSIT_RULES: Classical Gochara rules (favourable/unfavourable/vedha) ──
#
# rule_type:          'favourable' | 'unfavourable' | 'vedha'
# graha:              graha to which the rule applies
# primary_house:      house FROM MOON that is favourable/unfavourable
# vedha_house:        house that obstructs the primary result (vedha)
# phala:              brief Sanskrit/English result phrase
# classical_citation: source
# rule_notes:         clarifying note (vedha exceptions, nakshatra nuances, etc.)

BG_TRANSIT_RULES: list[dict[str, Any]] = [
    # ── SUN (Surya) Gochara — BPHS Ch.29 ────────────────────────────────────
    {
        "rule_type": "favourable",
        "graha": "sun",
        "primary_house": 3,
        "vedha_house": 9,
        "phala": "Courage, travel, gain from siblings",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Vedha from 9th house transit nullifies result",
    },
    {
        "rule_type": "favourable",
        "graha": "sun",
        "primary_house": 6,
        "vedha_house": 12,
        "phala": "Defeat of enemies, health improvement",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Vedha from 12th house transit nullifies result",
    },
    {
        "rule_type": "favourable",
        "graha": "sun",
        "primary_house": 10,
        "vedha_house": 4,
        "phala": "Career success, fame, royal favour",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Vedha from 4th house transit nullifies result",
    },
    {
        "rule_type": "favourable",
        "graha": "sun",
        "primary_house": 11,
        "vedha_house": 5,
        "phala": "Financial gains, fulfillment of desires",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Vedha from 5th house transit nullifies result",
    },
    {
        "rule_type": "unfavourable",
        "graha": "sun",
        "primary_house": 1,
        "vedha_house": None,
        "phala": "Ill health, loss of position, eye trouble",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Generally inauspicious for health and status",
    },
    {
        "rule_type": "unfavourable",
        "graha": "sun",
        "primary_house": 5,
        "vedha_house": None,
        "phala": "Trouble with children, loss of intelligence",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Afflicts progeny and wisdom matters",
    },
    {
        "rule_type": "unfavourable",
        "graha": "sun",
        "primary_house": 8,
        "vedha_house": None,
        "phala": "Disease, obstacle, conflict with authority",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Transit through 8th from Moon — serious affliction",
    },
    # ── MOON (Chandra) Gochara — BPHS Ch.29 ──────────────────────────────────
    {
        "rule_type": "favourable",
        "graha": "moon",
        "primary_house": 1,
        "vedha_house": 5,
        "phala": "Good health, mental peace, bodily comforts",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Vedha from 5th house nullifies result",
    },
    {
        "rule_type": "favourable",
        "graha": "moon",
        "primary_house": 3,
        "vedha_house": 9,
        "phala": "Gain from siblings, short journeys, enterprise",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Vedha from 9th nullifies result",
    },
    {
        "rule_type": "favourable",
        "graha": "moon",
        "primary_house": 6,
        "vedha_house": 12,
        "phala": "Defeat of enemies, good health",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Vedha from 12th nullifies result",
    },
    {
        "rule_type": "favourable",
        "graha": "moon",
        "primary_house": 7,
        "vedha_house": 2,
        "phala": "Gain in partnership, conjugal happiness",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Vedha from 2nd nullifies result",
    },
    {
        "rule_type": "favourable",
        "graha": "moon",
        "primary_house": 10,
        "vedha_house": 4,
        "phala": "Professional success, recognition",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Vedha from 4th nullifies result",
    },
    {
        "rule_type": "favourable",
        "graha": "moon",
        "primary_house": 11,
        "vedha_house": 8,
        "phala": "Gains, fulfilment of wishes",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Vedha from 8th nullifies result",
    },
    {
        "rule_type": "unfavourable",
        "graha": "moon",
        "primary_house": 8,
        "vedha_house": None,
        "phala": "Fear, sorrow, ill health",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Moon in 8th from natal Moon is afflictive",
    },
    # ── MARS (Mangal) Gochara — BPHS Ch.29 ──────────────────────────────────
    {
        "rule_type": "favourable",
        "graha": "mars",
        "primary_house": 3,
        "vedha_house": 12,
        "phala": "Courage, bravery, victory over enemies",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Vedha from 12th nullifies result",
    },
    {
        "rule_type": "favourable",
        "graha": "mars",
        "primary_house": 6,
        "vedha_house": 9,
        "phala": "Defeat of enemies, liberation from debts",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Vedha from 9th nullifies result",
    },
    {
        "rule_type": "favourable",
        "graha": "mars",
        "primary_house": 11,
        "vedha_house": 5,
        "phala": "Financial gains, political success",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Vedha from 5th nullifies result",
    },
    {
        "rule_type": "unfavourable",
        "graha": "mars",
        "primary_house": 1,
        "vedha_house": None,
        "phala": "Fever, accidents, injury, quarrels",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Mars transiting natal Moon sign — danger and conflict",
    },
    {
        "rule_type": "unfavourable",
        "graha": "mars",
        "primary_house": 4,
        "vedha_house": None,
        "phala": "Domestic strife, trouble to mother, property loss",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Mars 4th from Moon — family and home afflictions",
    },
    {
        "rule_type": "unfavourable",
        "graha": "mars",
        "primary_house": 8,
        "vedha_house": None,
        "phala": "Danger, accidents, surgical risk",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Mars 8th from Moon — severe affliction",
    },
    # ── MERCURY (Budha) Gochara — BPHS Ch.29 ─────────────────────────────────
    {
        "rule_type": "favourable",
        "graha": "mercury",
        "primary_house": 2,
        "vedha_house": 5,
        "phala": "Eloquence, financial gain through communication",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Vedha from 5th nullifies result",
    },
    {
        "rule_type": "favourable",
        "graha": "mercury",
        "primary_house": 4,
        "vedha_house": 3,
        "phala": "Good education, domestic happiness, vehicles",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Vedha from 3rd nullifies result",
    },
    {
        "rule_type": "favourable",
        "graha": "mercury",
        "primary_house": 6,
        "vedha_house": 9,
        "phala": "Victory over enemies, success in disputes",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Vedha from 9th nullifies result",
    },
    {
        "rule_type": "favourable",
        "graha": "mercury",
        "primary_house": 10,
        "vedha_house": 8,
        "phala": "Success in trade, professional recognition",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Vedha from 8th nullifies result",
    },
    {
        "rule_type": "favourable",
        "graha": "mercury",
        "primary_house": 11,
        "vedha_house": 12,
        "phala": "Financial gains, accomplishment of desires",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Vedha from 12th nullifies result",
    },
    # ── JUPITER (Guru) Gochara — BPHS Ch.29 ──────────────────────────────────
    {
        "rule_type": "favourable",
        "graha": "jupiter",
        "primary_house": 2,
        "vedha_house": 12,
        "phala": "Wealth accumulation, family happiness",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Jupiter 2nd from Moon — dhana yoga; vedha from 12th",
    },
    {
        "rule_type": "favourable",
        "graha": "jupiter",
        "primary_house": 5,
        "vedha_house": 4,
        "phala": "Good children, happiness, wisdom, spiritual gains",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Jupiter 5th from Moon; vedha from 4th",
    },
    {
        "rule_type": "favourable",
        "graha": "jupiter",
        "primary_house": 7,
        "vedha_house": 3,
        "phala": "Marital happiness, partnership gains",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Jupiter 7th from Moon; vedha from 3rd",
    },
    {
        "rule_type": "favourable",
        "graha": "jupiter",
        "primary_house": 9,
        "vedha_house": 10,
        "phala": "Dharmic activity, father's wellbeing, fortune",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Jupiter 9th from Moon; vedha from 10th",
    },
    {
        "rule_type": "favourable",
        "graha": "jupiter",
        "primary_house": 11,
        "vedha_house": 8,
        "phala": "Major gains, fulfilment of wishes, income rise",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Jupiter 11th from Moon — best transit; vedha from 8th",
    },
    {
        "rule_type": "unfavourable",
        "graha": "jupiter",
        "primary_house": 4,
        "vedha_house": None,
        "phala": "Domestic trouble, loss of comforts, mother's illness",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Ashtama Guru precedes the 5th favourable transit",
    },
    {
        "rule_type": "unfavourable",
        "graha": "jupiter",
        "primary_house": 8,
        "vedha_house": None,
        "phala": "Obstacles, loss of position, health issues",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Jupiter 8th from Moon — significant affliction",
    },
    # ── VENUS (Shukra) Gochara — BPHS Ch.29 ──────────────────────────────────
    {
        "rule_type": "favourable",
        "graha": "venus",
        "primary_house": 1,
        "vedha_house": 8,
        "phala": "Good health, pleasures, marital happiness",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Venus 1st from Moon; vedha from 8th",
    },
    {
        "rule_type": "favourable",
        "graha": "venus",
        "primary_house": 2,
        "vedha_house": 7,
        "phala": "Wealth, food, comforts, family happiness",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Venus 2nd from Moon; vedha from 7th",
    },
    {
        "rule_type": "favourable",
        "graha": "venus",
        "primary_house": 3,
        "vedha_house": 11,
        "phala": "Gains from siblings, short journeys, new ventures",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Venus 3rd from Moon; vedha from 11th",
    },
    # BPHS Ch.29 — complete favourable set; Wave 2 audit fix
    {
        "rule_type": "favourable",
        "graha": "venus",
        "primary_house": 4,
        "vedha_house": 10,
        "phala": "Domestic happiness, comforts, mother's well-being",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Venus 4th from Moon; vedha from 10th",
    },
    {
        "rule_type": "favourable",
        "graha": "venus",
        "primary_house": 5,
        "vedha_house": 9,
        "phala": "Children, romance, creativity, speculative gains",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Venus 5th from Moon; vedha from 9th",
    },
    {
        "rule_type": "favourable",
        "graha": "venus",
        "primary_house": 8,
        "vedha_house": 1,
        "phala": "Longevity support, gains through inheritance or partner",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Venus 8th from Moon; vedha from 1st",
    },
    {
        "rule_type": "favourable",
        "graha": "venus",
        "primary_house": 9,
        "vedha_house": 2,
        "phala": "Dharmic fortune, prosperity, guru's grace",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Venus 9th from Moon; vedha from 2nd",
    },
    {
        "rule_type": "favourable",
        "graha": "venus",
        "primary_house": 11,
        "vedha_house": 3,
        "phala": "Gains, fulfilment of desires, elder sibling prosperity",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Venus 11th from Moon; vedha from 3rd",
    },
    {
        "rule_type": "favourable",
        "graha": "venus",
        "primary_house": 12,
        "vedha_house": 6,
        "phala": "Pleasures of the bed, foreign travel, liberation-tending",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Venus 12th from Moon; vedha from 6th",
    },
    # ── SATURN (Shani) Gochara — BPHS Ch.29 ─────────────────────────────────
    {
        "rule_type": "favourable",
        "graha": "saturn",
        "primary_house": 3,
        "vedha_house": 12,
        "phala": "Courage, perseverance, enterprise, gains from effort",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Saturn 3rd from Moon — best transit; vedha from 12th",
    },
    {
        "rule_type": "favourable",
        "graha": "saturn",
        "primary_house": 6,
        "vedha_house": 9,
        "phala": "Victory over enemies, servants, legal gains",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Saturn 6th from Moon; vedha from 9th nullifies",
    },
    {
        "rule_type": "favourable",
        "graha": "saturn",
        "primary_house": 11,
        "vedha_house": 5,
        "phala": "Sustained income, gains through persistence",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Saturn 11th from Moon; vedha from 5th nullifies",
    },
    {
        "rule_type": "unfavourable",
        "graha": "saturn",
        "primary_house": 1,
        "vedha_house": None,
        "phala": "Sade Sati peak — hardship, health issues, delays",
        "classical_citation": PD_CH26,
        "rule_notes": "Central phase of Sade Sati (7.5 year Saturn affliction cycle)",
    },
    {
        "rule_type": "unfavourable",
        "graha": "saturn",
        "primary_house": 4,
        "vedha_house": None,
        "phala": "Domestic troubles, loss of property, mother's illness",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Kantaka Saturn (4th) — classic obstacle transit",
    },
    {
        "rule_type": "unfavourable",
        "graha": "saturn",
        "primary_house": 8,
        "vedha_house": None,
        "phala": "Serious illness, accidents, prolonged suffering",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Ashtama Shani — worst Saturn transit position",
    },
    # ── RAHU Gochara — BPHS Ch.29 + Phaladeepika Ch.26 ──────────────────────
    {
        "rule_type": "favourable",
        "graha": "rahu",
        "primary_house": 3,
        "vedha_house": 9,
        "phala": "Enterprise, travel, gain through courage; sibling support",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Rahu 3rd from Moon — gain and initiative; vedha from 9th nullifies.",
    },
    {
        "rule_type": "favourable",
        "graha": "rahu",
        "primary_house": 6,
        "vedha_house": 12,
        "phala": "Defeat of enemies, legal victories, health improvement",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Rahu 6th from Moon — ari-bhava placement aids in enemy removal; vedha from 12th.",
    },
    {
        "rule_type": "favourable",
        "graha": "rahu",
        "primary_house": 11,
        "vedha_house": 5,
        "phala": "Financial gains, labha, fulfillment of desires through unconventional means",
        "classical_citation": PD_CH26,
        "rule_notes": "Rahu 11th from Moon — labha amplified; shadow planet in gain house; vedha from 5th.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "rahu",
        "primary_house": 1,
        "vedha_house": None,
        "phala": "Ill health, confusion, loss of clarity; fear and anxiety",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Rahu over natal Moon — mental disturbance; Sade-Sati-class affliction for Rahu.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "rahu",
        "primary_house": 2,
        "vedha_house": None,
        "phala": "Speech affliction, family disputes, financial drain",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Rahu 2nd from Moon — kutumba and dhana affliction.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "rahu",
        "primary_house": 4,
        "vedha_house": None,
        "phala": "Domestic troubles, property loss, mother's health affected",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Rahu 4th from Moon — Kantaka-class obstruction; home and sukha affliction.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "rahu",
        "primary_house": 7,
        "vedha_house": None,
        "phala": "Partnership conflicts, danger in travel, hidden adversaries",
        "classical_citation": PD_CH26,
        "rule_notes": "Rahu 7th from Moon — kalatra and travel affliction.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "rahu",
        "primary_house": 8,
        "vedha_house": None,
        "phala": "Accidents, sudden illness, hidden dangers; fear of death",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Rahu 8th from Moon — randhra affliction; severe; longevity concern.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "rahu",
        "primary_house": 12,
        "vedha_house": None,
        "phala": "Hidden expenditure, foreign travel under duress, separation",
        "classical_citation": PD_CH26,
        "rule_notes": "Rahu 12th from Moon — vyaya affliction; loss and isolation.",
    },
    # ── KETU Gochara — BPHS Ch.29 + Phaladeepika Ch.26 ──────────────────────
    {
        "rule_type": "favourable",
        "graha": "ketu",
        "primary_house": 3,
        "vedha_house": 9,
        "phala": "Moderate gain through effort; spiritual enterprise; sibling support",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Ketu 3rd from Moon — paurushabala enterprise; less potent than Rahu here; vedha from 9th.",
    },
    {
        "rule_type": "favourable",
        "graha": "ketu",
        "primary_house": 6,
        "vedha_house": 12,
        "phala": "Enemies subdued; disease removal; spiritual purification",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Ketu 6th from Moon — moksha-karak in ari-bhava aids liberation from obstacles.",
    },
    {
        "rule_type": "favourable",
        "graha": "ketu",
        "primary_house": 11,
        "vedha_house": 5,
        "phala": "Spiritual gains, gains through research or occult; modest material labha",
        "classical_citation": PD_CH26,
        "rule_notes": "Ketu 11th from Moon — gains oriented toward karmic fulfilment; vedha from 5th.",
    },
    {
        "rule_type": "favourable",
        "graha": "ketu",
        "primary_house": 12,
        "vedha_house": None,
        "phala": "Spiritual liberation, moksha progress, renunciation; retreat and deep contemplation",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Ketu 12th from Moon — moksha-karaka in vyaya: uniquely auspicious for spiritual seekers.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "ketu",
        "primary_house": 1,
        "vedha_house": None,
        "phala": "Bodily affliction, confusion, spiritual restlessness; detachment from self",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Ketu over natal Moon — dissociation and health disturbance.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "ketu",
        "primary_house": 2,
        "vedha_house": None,
        "phala": "Financial loss, family separation, speech affliction",
        "classical_citation": PD_CH26,
        "rule_notes": "Ketu 2nd from Moon — kutumba and dhana affliction.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "ketu",
        "primary_house": 4,
        "vedha_house": None,
        "phala": "Home disruption, loss of comforts, mother's health concerns",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Ketu 4th from Moon — Kantaka-class; domestic troubles and vehicle accidents.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "ketu",
        "primary_house": 7,
        "vedha_house": None,
        "phala": "Marital friction, separation, hidden adversary in partnership",
        "classical_citation": PD_CH26,
        "rule_notes": "Ketu 7th from Moon — kalatra affliction; relationships tested.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "ketu",
        "primary_house": 8,
        "vedha_house": None,
        "phala": "Surgery, accidents, sudden health crisis; karmic debt activation",
        "classical_citation": BPHS_CH29,
        "rule_notes": "Ketu 8th from Moon — randhra + moksha karak: severe; karmic reckoning.",
    },
]

# ── §3 — BG_TRANSIT_MOORTI: Moorti Nirnaya (BA-P7A) ──────────────────────────
#
# nakshatra_offset: count of transit nakshatra from natal janma nakshatra (1–27).
# moorti_name:      swarna/rajata/tamra/loha quality tier.
# quality_tier:     1 (best) → 4 (worst); consumed by ka_gochara for transit scoring.
# classical source: Phaladeepika Ch.26 §moorti-nirnaya; BPHS Ch.28.
#
# Cycle: offsets mod 4 → 1=swarna, 2=rajata, 3=tamra, 0=loha
# (with offset 27 = tamra, not loha, per Phaladeepika — last entry of tamra group).

_MOORTI_CYCLE: list[tuple[int, str, int, str]] = [
    # (nakshatra_offset, moorti_name, quality_tier, phala_brief)
    (1,  "swarna", 1, "Janma nakshatra — full Swarna moorti; all endeavours prosper."),
    (2,  "rajata", 2, "Second from janma — Rajata moorti; moderate gains and comfort."),
    (3,  "tamra",  3, "Third from janma — Tamra moorti; mixed results; caution advised."),
    (4,  "loha",   4, "Fourth from janma — Loha moorti; hardship, obstacles, health risk."),
    (5,  "swarna", 1, "Fifth from janma — Swarna moorti; gains and good health."),
    (6,  "rajata", 2, "Sixth from janma — Rajata moorti; enemies manageable, health fair."),
    (7,  "tamra",  3, "Seventh from janma — Tamra moorti; relationship and travel caution."),
    (8,  "loha",   4, "Eighth from janma — Loha moorti; avoid new ventures; obstruction."),
    (9,  "swarna", 1, "Ninth from janma — Swarna moorti; dharma and fortune favoured."),
    (10, "rajata", 2, "Tenth from janma — Rajata moorti; career matters advance moderately."),
    (11, "tamra",  3, "Eleventh from janma — Tamra moorti; gains delayed or obstructed."),
    (12, "loha",   4, "Twelfth from janma — Loha moorti; losses and expenditure likely."),
    (13, "swarna", 1, "Thirteenth from janma — Swarna moorti; auspicious outcomes."),
    (14, "rajata", 2, "Fourteenth from janma — Rajata moorti; positive outcomes with effort."),
    (15, "tamra",  3, "Fifteenth from janma — Tamra moorti; mixed; health attention needed."),
    (16, "loha",   4, "Sixteenth from janma — Loha moorti; disputes and health affliction."),
    (17, "swarna", 1, "Seventeenth from janma — Swarna moorti; prosperity and recognition."),
    (18, "rajata", 2, "Eighteenth from janma — Rajata moorti; moderate auspiciousness."),
    (19, "tamra",  3, "Nineteenth from janma — Tamra moorti; efforts yield partial results."),
    (20, "loha",   4, "Twentieth from janma — Loha moorti; career and domestic troubles."),
    (21, "swarna", 1, "Twenty-first from janma — Swarna moorti; success in enterprises."),
    (22, "rajata", 2, "Twenty-second from janma — Rajata moorti; partial success likely."),
    (23, "tamra",  3, "Twenty-third from janma — Tamra moorti; undertakings face friction."),
    (24, "loha",   4, "Twenty-fourth from janma — Loha moorti; delays and loss."),
    (25, "swarna", 1, "Twenty-fifth from janma — Swarna moorti; gains and blessings."),
    (26, "rajata", 2, "Twenty-sixth from janma — Rajata moorti; gains with moderate delay."),
    (27, "tamra",  3, "Twenty-seventh from janma — Tamra moorti; cycle end; caution."),
]

BG_TRANSIT_MOORTI: list[dict[str, Any]] = [
    {
        "nakshatra_offset": offset,
        "moorti_name": name,
        "quality_tier": tier,
        "phala_brief": phala,
        "classical_citation": f"{BPHS_CH28}; {PD_CH26}",
        "rule_notes": (
            "Offset 1 = transit in birth nakshatra; strongest Swarna position."
            if offset == 1
            else "Offset 27 = last Tamra entry per Phaladeepika consensus; cycle completes."
            if offset == 27
            else None
        ),
    }
    for offset, name, tier, phala in _MOORTI_CYCLE
]


def seed_transit_rules(conn, *, dry_run: bool = False) -> dict[str, int]:
    """
    Seed bg_transit_engine, bg_transit_rules, and bg_transit_moorti reference tables.

    L0 idempotency: ON CONFLICT DO UPDATE (upsert).
    Never commits — caller owns the transaction.
    Returns counts by table and total.
    """
    if dry_run:
        return {
            "bg_transit_engine": len(BG_TRANSIT_ENGINE),
            "bg_transit_rules": len(BG_TRANSIT_RULES),
            "bg_transit_moorti": len(BG_TRANSIT_MOORTI),
            "total": len(BG_TRANSIT_ENGINE) + len(BG_TRANSIT_RULES) + len(BG_TRANSIT_MOORTI),
        }

    cur = conn.cursor()

    # Idempotency: ON CONFLICT upserts below handle updates. DELETE-then-insert
    # was removed because (a) bg_transit_rules.id is SERIAL — delete+insert
    # renumbers every rule, silently corrupting gochara_resonance_map.source_rule_id
    # references (B.10 citation corruption), and (b) migration 459 added an FK
    # from gochara_resonance_map.source_rule_id → bg_transit_rules.id that
    # correctly prevents this. If retirement semantics are ever needed, add a
    # post-insert sweep scoped to keys absent from BG_TRANSIT_RULES — it will
    # FK-fail loudly only when a genuinely-referenced rule is retired.
    logger.info("[transit] upserting bg_transit_engine, bg_transit_rules, bg_transit_moorti")

    # ── Insert bg_transit_engine rows ─────────────────────────────────────────
    engine_count = 0
    for row in BG_TRANSIT_ENGINE:
        cur.execute(
            """
            INSERT INTO bg_transit_engine
                (graha, avg_daily_motion_deg, zodiac_period_days,
                 sign_residence_days, classical_citation)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (graha) DO UPDATE SET
                avg_daily_motion_deg = EXCLUDED.avg_daily_motion_deg,
                zodiac_period_days   = EXCLUDED.zodiac_period_days,
                sign_residence_days  = EXCLUDED.sign_residence_days,
                classical_citation   = EXCLUDED.classical_citation
            """,
            (
                row["graha"],
                row["avg_daily_motion_deg"],
                row["zodiac_period_days"],
                row["sign_residence_days"],
                row["classical_citation"],
            ),
        )
        engine_count += 1

    # ── Insert bg_transit_rules rows ──────────────────────────────────────────
    rules_count = 0
    for row in BG_TRANSIT_RULES:
        cur.execute(
            """
            INSERT INTO bg_transit_rules
                (rule_type, graha, primary_house, vedha_house,
                 phala, classical_citation, rule_notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (graha, rule_type, primary_house) DO UPDATE SET
                vedha_house        = EXCLUDED.vedha_house,
                phala              = EXCLUDED.phala,
                classical_citation = EXCLUDED.classical_citation,
                rule_notes         = EXCLUDED.rule_notes
            """,
            (
                row["rule_type"],
                row["graha"],
                row["primary_house"],
                row.get("vedha_house"),
                row["phala"],
                row["classical_citation"],
                row.get("rule_notes"),
            ),
        )
        rules_count += 1

    # ── Insert bg_transit_moorti rows (BA-P7A) ───────────────────────────────────
    moorti_count = 0
    for row in BG_TRANSIT_MOORTI:
        cur.execute(
            """
            INSERT INTO bg_transit_moorti
                (nakshatra_offset, moorti_name, quality_tier,
                 phala_brief, classical_citation, rule_notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (nakshatra_offset) DO UPDATE SET
                moorti_name        = EXCLUDED.moorti_name,
                quality_tier       = EXCLUDED.quality_tier,
                phala_brief        = EXCLUDED.phala_brief,
                classical_citation = EXCLUDED.classical_citation,
                rule_notes         = EXCLUDED.rule_notes
            """,
            (
                row["nakshatra_offset"],
                row["moorti_name"],
                row["quality_tier"],
                row["phala_brief"],
                row["classical_citation"],
                row.get("rule_notes"),
            ),
        )
        moorti_count += 1

    cur.close()

    return {
        "bg_transit_engine": engine_count,
        "bg_transit_rules": rules_count,
        "bg_transit_moorti": moorti_count,
        "total": engine_count + rules_count + moorti_count,
    }
