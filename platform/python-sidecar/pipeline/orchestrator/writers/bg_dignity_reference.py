"""
pipeline/orchestrator/writers/bg_dignity_reference.py
L0 Brahmagyan dignity reference writer — seeds 5 classical reference tables.

Tables seeded (151 rows total):
  bg_dignity_reference           9  rows — exaltation/debilitation/moolatrikona/own_signs per graha
  bg_graha_naisargika_friendship 72 rows — natural friendship relations between every graha pair
  bg_avastha_schemes             35 rows — 5 avastha classification schemes with determination rules
  bg_motion_state_thresholds     27 rows — per-graha speed thresholds for motion state labels
  bg_combustion_orbs              8 rows — combustion + deep-combustion orbs per graha

Classical sources:
  BPHS = Brihat Parashara Hora Shastra
  JP   = Jataka Parijata
  PD   = Phala Deepika
  UK   = Uttara Kalamrita
  SS   = Surya Siddhanta / Saravali

There is no dedicated brahmagyan module for this data (the seed logic lives in
migration 250_bg_dignity_reference.sql). The reference rows are reproduced here
as static Python data structures — appropriate for 151 rows of immutable classical
reference data. ZERO LLM use. ON CONFLICT DO UPDATE (L0 idempotency standard §N.3).

Conforms to FROZEN WriterBase contract (ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2):
- uses ctx.db_conn exclusively (never opens, commits, or closes it)
- returns WriterResult with actual rows_inserted + rows_updated
- honours ctx.dry_run
"""
from __future__ import annotations

import logging
import time
from typing import Any

from pipeline.orchestrator.writers import (
    ContextSpec,
    WriterBase,
    WriterResult,
    register,
)

# Dignity degree table extraction (PAR-R-6, LEDGER_PRATINIDHI.md par/pratinidhi-ledger):
# this data used to live inline here; it now lives in the dependency-free
# brahmagyan/l0_dignity_reference.py, matching the established brahmagyan/l0_*
# family convention every other L0 reference writer already follows
# (l0_class_priors, l0_class_lifetime_counts, l0_dasha_systems, l0_doshas,
# l0_formula_constants, l0_ephemeris). brahmagyan/dignity_oracle.py (the B-01
# shared serving-side classifier) imports the same module — one Python source,
# not two. See l0_dignity_reference.py's own docstring for the full account.
from brahmagyan.l0_dignity_reference import DIGNITY_REFERENCE as _DIGNITY_REFERENCE

logger = logging.getLogger(__name__)

# ── Source citations ───────────────────────────────────────────────────────────

_BPHS_CH27 = "BPHS Ch.27"
_JP_CH7    = "JP Ch.7"
_PD_CH4    = "PD Ch.4"
_UK_CH4    = "UK Ch.4 (Uttara Kalamrita — Rahu/Ketu tatva friendship schema)"
_SS        = "SS / Saravali"
_SARAVALI  = "Saravali Ch.6 / BPHS Ch.3"


# ── 2. bg_graha_naisargika_friendship (72 rows) ───────────────────────────────
# Columns: graha, other_graha, relation ('friend'|'neutral'|'enemy'), classical_citation

_NAISARGIKA_FRIENDSHIP: list[tuple[str, str, str, str]] = [
    # Sun (8 rows)
    ("Sun", "Moon",    "friend",  _BPHS_CH27),
    ("Sun", "Mars",    "friend",  _BPHS_CH27),
    ("Sun", "Jupiter", "friend",  _BPHS_CH27),
    ("Sun", "Mercury", "neutral", _BPHS_CH27),
    ("Sun", "Venus",   "enemy",   _BPHS_CH27),
    ("Sun", "Saturn",  "enemy",   _BPHS_CH27),
    ("Sun", "Rahu",    "enemy",   _BPHS_CH27),
    ("Sun", "Ketu",    "neutral", _BPHS_CH27),
    # Moon (8 rows)
    ("Moon", "Sun",     "friend",  _BPHS_CH27),
    ("Moon", "Mercury", "friend",  _BPHS_CH27),
    ("Moon", "Mars",    "neutral", _BPHS_CH27),
    ("Moon", "Jupiter", "neutral", _BPHS_CH27),
    ("Moon", "Venus",   "neutral", _BPHS_CH27),
    ("Moon", "Saturn",  "neutral", _BPHS_CH27),
    ("Moon", "Rahu",    "enemy",   _BPHS_CH27),
    ("Moon", "Ketu",    "neutral", _BPHS_CH27),
    # Mars (8 rows)
    ("Mars", "Sun",     "friend",  _BPHS_CH27),
    ("Mars", "Moon",    "friend",  _BPHS_CH27),
    ("Mars", "Jupiter", "friend",  _BPHS_CH27),
    ("Mars", "Venus",   "neutral", _BPHS_CH27),
    ("Mars", "Saturn",  "neutral", _BPHS_CH27),
    ("Mars", "Mercury", "enemy",   _BPHS_CH27),
    ("Mars", "Rahu",    "neutral", _BPHS_CH27),
    ("Mars", "Ketu",    "friend",  _BPHS_CH27),
    # Mercury (8 rows)
    ("Mercury", "Sun",     "friend",  _BPHS_CH27),
    ("Mercury", "Venus",   "friend",  _BPHS_CH27),
    ("Mercury", "Mars",    "neutral", _BPHS_CH27),
    ("Mercury", "Jupiter", "neutral", _BPHS_CH27),
    ("Mercury", "Saturn",  "neutral", _BPHS_CH27),
    ("Mercury", "Moon",    "enemy",   _BPHS_CH27),
    ("Mercury", "Rahu",    "friend",  _BPHS_CH27),
    ("Mercury", "Ketu",    "neutral", _BPHS_CH27),
    # Jupiter (8 rows)
    ("Jupiter", "Sun",     "friend",  _BPHS_CH27),
    ("Jupiter", "Moon",    "friend",  _BPHS_CH27),
    ("Jupiter", "Mars",    "friend",  _BPHS_CH27),
    ("Jupiter", "Saturn",  "neutral", _BPHS_CH27),
    ("Jupiter", "Mercury", "enemy",   _BPHS_CH27),
    ("Jupiter", "Venus",   "enemy",   _BPHS_CH27),
    ("Jupiter", "Rahu",    "neutral", _BPHS_CH27),
    ("Jupiter", "Ketu",    "neutral", _BPHS_CH27),
    # Venus (8 rows)
    ("Venus", "Mercury", "friend",  _BPHS_CH27),
    ("Venus", "Saturn",  "friend",  _BPHS_CH27),
    ("Venus", "Mars",    "neutral", _BPHS_CH27),
    ("Venus", "Jupiter", "neutral", _BPHS_CH27),
    ("Venus", "Sun",     "enemy",   _BPHS_CH27),
    ("Venus", "Moon",    "enemy",   _BPHS_CH27),
    ("Venus", "Rahu",    "friend",  _BPHS_CH27),
    ("Venus", "Ketu",    "friend",  _BPHS_CH27),
    # Saturn (8 rows)
    ("Saturn", "Mercury", "friend",  _BPHS_CH27),
    ("Saturn", "Venus",   "friend",  _BPHS_CH27),
    ("Saturn", "Jupiter", "neutral", _BPHS_CH27),
    ("Saturn", "Sun",     "enemy",   _BPHS_CH27),
    ("Saturn", "Moon",    "enemy",   _BPHS_CH27),
    ("Saturn", "Mars",    "enemy",   _BPHS_CH27),
    ("Saturn", "Rahu",    "friend",  _BPHS_CH27),
    ("Saturn", "Ketu",    "friend",  _BPHS_CH27),
    # Rahu (8 rows)
    ("Rahu", "Venus",   "friend",  _UK_CH4),
    ("Rahu", "Saturn",  "friend",  _UK_CH4),
    ("Rahu", "Mercury", "friend",  _UK_CH4),
    ("Rahu", "Sun",     "enemy",   _UK_CH4),
    ("Rahu", "Moon",    "enemy",   _UK_CH4),
    ("Rahu", "Mars",    "neutral", _UK_CH4),
    ("Rahu", "Jupiter", "neutral", _UK_CH4),
    ("Rahu", "Ketu",    "enemy",   _UK_CH4),
    # Ketu (8 rows)
    ("Ketu", "Mars",    "friend",  _UK_CH4),
    ("Ketu", "Venus",   "friend",  _UK_CH4),
    ("Ketu", "Saturn",  "friend",  _UK_CH4),
    ("Ketu", "Sun",     "neutral", _UK_CH4),
    ("Ketu", "Moon",    "neutral", _UK_CH4),
    ("Ketu", "Mercury", "neutral", _UK_CH4),
    ("Ketu", "Jupiter", "neutral", _UK_CH4),
    ("Ketu", "Rahu",    "enemy",   _UK_CH4),
]


# ── 3. bg_avastha_schemes (35 rows) ───────────────────────────────────────────
# Columns: scheme_name, state_name, state_order, determination_rule (JSON str),
#          classical_citation, notes

_AVASTHA_SCHEMES: list[tuple[str, str, int, str, str, str | None]] = [
    # Baladi — 5 states by degree in sign (Jataka Parijata)
    ("baladi", "bala",    1,
     '{"type":"degree_in_sign","range_from":0,"range_to":6}',
     _JP_CH7, "Infant (0–6°): weak, impressionable"),
    ("baladi", "kumara",  2,
     '{"type":"degree_in_sign","range_from":6,"range_to":12}',
     _JP_CH7, "Youth (6–12°): growing strength"),
    ("baladi", "yuva",    3,
     '{"type":"degree_in_sign","range_from":12,"range_to":18}',
     _JP_CH7, "Prime (12–18°): peak vitality"),
    ("baladi", "vriddha", 4,
     '{"type":"degree_in_sign","range_from":18,"range_to":24}',
     _JP_CH7, "Elder (18–24°): declining potency"),
    ("baladi", "mrita",   5,
     '{"type":"degree_in_sign","range_from":24,"range_to":30}',
     _JP_CH7, "Dead (24–30°): minimal efficacy"),

    # Jagradadi — 3 states (BPHS Ch.45)
    ("jagradadi", "jagrata",  1,
     '{"type":"sign_dignity","dignity_map":{"exalted":"jagrata","moolatrikona":"jagrata","own":"jagrata"}}',
     "BPHS Ch.45", "Awake: full expression — own/exaltation/moolatrikona"),
    ("jagradadi", "svapna",   2,
     '{"type":"sign_dignity","dignity_map":{"great_friend_sign":"svapna","friend_sign":"svapna"}}',
     "BPHS Ch.45", "Dreaming: partial expression — friendly sign"),
    ("jagradadi", "sushupti", 3,
     '{"type":"sign_dignity","dignity_map":{"neutral_sign":"sushupti","enemy_sign":"sushupti","great_enemy_sign":"sushupti","debilitated":"sushupti"}}',
     "BPHS Ch.45", "Deep sleep: subdued expression — neutral/enemy/debilitation"),

    # Deeptaadi — 9 states (Phala Deepika)
    ("deeptaadi", "deepta",  1,
     '{"type":"sign_dignity_combustion_retrograde","condition":"exalted_or_own"}',
     _PD_CH4, "Bright: exalted or own sign — highest functional output"),
    ("deeptaadi", "swastha", 2,
     '{"type":"sign_dignity_combustion_retrograde","condition":"friend_sign"}',
     _PD_CH4, "Comfortable: friendly sign"),
    ("deeptaadi", "mudita",  3,
     '{"type":"sign_dignity_combustion_retrograde","condition":"friend_navamsa"}',
     _PD_CH4, "Joyful: own or friendly navamsa sign"),
    ("deeptaadi", "shanta",  4,
     '{"type":"sign_dignity_combustion_retrograde","condition":"neutral_sign"}',
     _PD_CH4, "Peaceful: neutral sign"),
    ("deeptaadi", "shakta",  5,
     '{"type":"sign_dignity_combustion_retrograde","condition":"conjunct_benefic"}',
     _PD_CH4, "Powerful: conjunct natural benefic"),
    ("deeptaadi", "dina",    6,
     '{"type":"sign_dignity_combustion_retrograde","condition":"enemy_sign"}',
     _PD_CH4, "Dejected: enemy sign"),
    ("deeptaadi", "peedit",  7,
     '{"type":"sign_dignity_combustion_retrograde","condition":"combust_or_conjunct_malefic"}',
     _PD_CH4, "Tormented: combust or conjunct malefic"),
    ("deeptaadi", "khala",   8,
     '{"type":"sign_dignity_combustion_retrograde","condition":"debilitated"}',
     _PD_CH4, "Wicked: debilitation sign"),
    ("deeptaadi", "vikala",  9,
     '{"type":"sign_dignity_combustion_retrograde","condition":"retrograde_in_enemy"}',
     _PD_CH4, "Disabled: retrograde in enemy sign"),

    # Lajjitaadi — 6 states (Uttara Kalamrita)
    ("lajjitaadi", "lajjita",   1,
     '{"type":"house_conjunctions","requires_chart_context":true,"condition":"in_5th_with_malefic"}',
     "UK Ch.4", "Ashamed: in 5th house with malefic conjunction"),
    ("lajjitaadi", "garvita",   2,
     '{"type":"house_conjunctions","requires_chart_context":true,"condition":"own_or_exaltation_sign"}',
     "UK Ch.4", "Proud: own or exaltation sign"),
    ("lajjitaadi", "kshudhita", 3,
     '{"type":"house_conjunctions","requires_chart_context":true,"condition":"enemy_sign_or_conjunct_enemy"}',
     "UK Ch.4", "Hungry: enemy sign or conjunct enemy planet"),
    ("lajjitaadi", "trishita",  4,
     '{"type":"house_conjunctions","requires_chart_context":true,"condition":"conjunct_saturn_no_benefic"}',
     "UK Ch.4", "Thirsty: conjunct Saturn with no benefic relief"),
    ("lajjitaadi", "mudita",    5,
     '{"type":"house_conjunctions","requires_chart_context":true,"condition":"conjunct_friend_in_own_sign"}',
     "UK Ch.4", "Delighted: conjunct/aspected by natural friend in own sign"),
    ("lajjitaadi", "kshobhita", 6,
     '{"type":"house_conjunctions","requires_chart_context":true,"condition":"conjunct_sun_or_aspected_malefic"}',
     "UK Ch.4", "Agitated: conjunct Sun or aspected by malefic"),

    # Sayanadi — 12 states (Phala Deepika / Jataka Parijata)
    ("sayanadi", "sayana",         1,
     '{"type":"planet_count_in_sign","note":"12-state posture; count of planets in sign determines posture index"}',
     "PD Ch.4; JP Ch.7", "Sleeping"),
    ("sayanadi", "upavesana",       2,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     "PD Ch.4; JP Ch.7", "Sitting"),
    ("sayanadi", "netrapani",       3,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     "PD Ch.4; JP Ch.7", "Eyes in hand (protective)"),
    ("sayanadi", "prakasana",       4,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     "PD Ch.4; JP Ch.7", "Illuminating"),
    ("sayanadi", "gamana",          5,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     "PD Ch.4; JP Ch.7", "Moving/going"),
    ("sayanadi", "agamana",         6,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     "PD Ch.4; JP Ch.7", "Arriving"),
    ("sayanadi", "sabha",           7,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     "PD Ch.4; JP Ch.7", "In assembly"),
    ("sayanadi", "agama",           8,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     "PD Ch.4; JP Ch.7", "Approach"),
    ("sayanadi", "bhojanaprapta",   9,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     "PD Ch.4; JP Ch.7", "Receiving food (prosperity)"),
    ("sayanadi", "kautuka",         10,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     "PD Ch.4; JP Ch.7", "Curious/sporting"),
    ("sayanadi", "nidraksita",      11,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     "PD Ch.4; JP Ch.7", "Deep sleep"),
    ("sayanadi", "deeptamsa",       12,
     '{"type":"planet_count_in_sign","note":"12-state posture scheme"}',
     "PD Ch.4; JP Ch.7", "Bright portion (peak)"),
]


# ── 4. bg_motion_state_thresholds (27 rows) ───────────────────────────────────
# Columns: graha, motion_state, speed_threshold_low, speed_threshold_high,
#          threshold_type, typical_speed_dps, classical_citation, notes

_MOTION_STATE_THRESHOLDS: list[dict[str, Any]] = [
    # Sun: never retrograde
    {"graha": "Sun",     "motion_state": "sama",     "speed_threshold_low": None, "speed_threshold_high": None, "threshold_type": "always", "typical_speed_dps": 0.9856, "classical_citation": _SS, "notes": "Sun mean motion"},
    {"graha": "Sun",     "motion_state": "atichara", "speed_threshold_low": 1.02, "speed_threshold_high": None, "threshold_type": "above",  "typical_speed_dps": None,   "classical_citation": _SS, "notes": "Sun fast (perihelion season)"},
    # Moon: very fast
    {"graha": "Moon",    "motion_state": "sama",     "speed_threshold_low": None, "speed_threshold_high": None, "threshold_type": "always", "typical_speed_dps": 13.176, "classical_citation": _SS, "notes": "Moon mean motion"},
    {"graha": "Moon",    "motion_state": "atichara", "speed_threshold_low": 15.0, "speed_threshold_high": None, "threshold_type": "above",  "typical_speed_dps": None,   "classical_citation": _SS, "notes": "Moon fast"},
    # Mars (5 rows)
    {"graha": "Mars",    "motion_state": "vakra",    "speed_threshold_low": None, "speed_threshold_high": 0,    "threshold_type": "below",  "typical_speed_dps": None,  "classical_citation": _SS, "notes": "Retrograde: speed < 0"},
    {"graha": "Mars",    "motion_state": "anuvakra", "speed_threshold_low": 0,    "speed_threshold_high": 0.1,  "threshold_type": "range",  "typical_speed_dps": None,  "classical_citation": _SS, "notes": "Station / slow (0–0.1°/day)"},
    {"graha": "Mars",    "motion_state": "manda",    "speed_threshold_low": 0.1,  "speed_threshold_high": 0.5,  "threshold_type": "range",  "typical_speed_dps": None,  "classical_citation": _SS, "notes": "Slow (0.1–0.5°/day)"},
    {"graha": "Mars",    "motion_state": "sama",     "speed_threshold_low": 0.5,  "speed_threshold_high": 0.8,  "threshold_type": "range",  "typical_speed_dps": 0.524, "classical_citation": _SS, "notes": "Normal range"},
    {"graha": "Mars",    "motion_state": "atichara", "speed_threshold_low": 0.8,  "speed_threshold_high": None, "threshold_type": "above",  "typical_speed_dps": None,  "classical_citation": _SS, "notes": "Fast"},
    # Mercury (4 rows)
    {"graha": "Mercury", "motion_state": "vakra",    "speed_threshold_low": None, "speed_threshold_high": 0,    "threshold_type": "below",  "typical_speed_dps": None,  "classical_citation": _SS, "notes": "Retrograde"},
    {"graha": "Mercury", "motion_state": "anuvakra", "speed_threshold_low": 0,    "speed_threshold_high": 0.1,  "threshold_type": "range",  "typical_speed_dps": None,  "classical_citation": _SS, "notes": "Station / slow"},
    {"graha": "Mercury", "motion_state": "sama",     "speed_threshold_low": 0.1,  "speed_threshold_high": 2.0,  "threshold_type": "range",  "typical_speed_dps": 1.383, "classical_citation": _SS, "notes": "Normal range"},
    {"graha": "Mercury", "motion_state": "atichara", "speed_threshold_low": 2.0,  "speed_threshold_high": None, "threshold_type": "above",  "typical_speed_dps": None,  "classical_citation": _SS, "notes": "Fast (observed max ~2.2°/day; 2.5 was unreachable)"},
    # Jupiter (4 rows)
    {"graha": "Jupiter", "motion_state": "vakra",    "speed_threshold_low": None, "speed_threshold_high": 0,    "threshold_type": "below",  "typical_speed_dps": None,  "classical_citation": _SS, "notes": "Retrograde"},
    {"graha": "Jupiter", "motion_state": "anuvakra", "speed_threshold_low": 0,    "speed_threshold_high": 0.05, "threshold_type": "range",  "typical_speed_dps": None,  "classical_citation": _SS, "notes": "Station / slow"},
    {"graha": "Jupiter", "motion_state": "sama",     "speed_threshold_low": 0.05, "speed_threshold_high": 0.15, "threshold_type": "range",  "typical_speed_dps": 0.083, "classical_citation": _SS, "notes": "Normal range"},
    {"graha": "Jupiter", "motion_state": "atichara", "speed_threshold_low": 0.15, "speed_threshold_high": None, "threshold_type": "above",  "typical_speed_dps": None,  "classical_citation": _SS, "notes": "Fast"},
    # Venus (4 rows)
    {"graha": "Venus",   "motion_state": "vakra",    "speed_threshold_low": None, "speed_threshold_high": 0,    "threshold_type": "below",  "typical_speed_dps": None,  "classical_citation": _SS, "notes": "Retrograde"},
    {"graha": "Venus",   "motion_state": "anuvakra", "speed_threshold_low": 0,    "speed_threshold_high": 0.05, "threshold_type": "range",  "typical_speed_dps": None,  "classical_citation": _SS, "notes": "Station / slow"},
    {"graha": "Venus",   "motion_state": "sama",     "speed_threshold_low": 0.05, "speed_threshold_high": 1.3,  "threshold_type": "range",  "typical_speed_dps": 1.202, "classical_citation": _SS, "notes": "Normal range"},
    {"graha": "Venus",   "motion_state": "atichara", "speed_threshold_low": 1.3,  "speed_threshold_high": None, "threshold_type": "above",  "typical_speed_dps": None,  "classical_citation": _SS, "notes": "Fast"},
    # Saturn (4 rows)
    {"graha": "Saturn",  "motion_state": "vakra",    "speed_threshold_low": None, "speed_threshold_high": 0,    "threshold_type": "below",  "typical_speed_dps": None,  "classical_citation": _SS, "notes": "Retrograde"},
    {"graha": "Saturn",  "motion_state": "anuvakra", "speed_threshold_low": 0,    "speed_threshold_high": 0.02, "threshold_type": "range",  "typical_speed_dps": None,  "classical_citation": _SS, "notes": "Station / slow"},
    {"graha": "Saturn",  "motion_state": "sama",     "speed_threshold_low": 0.02, "speed_threshold_high": 0.13, "threshold_type": "range",  "typical_speed_dps": 0.034, "classical_citation": _SS, "notes": "Normal range"},
    {"graha": "Saturn",  "motion_state": "atichara", "speed_threshold_low": 0.13, "speed_threshold_high": None, "threshold_type": "above",  "typical_speed_dps": None,  "classical_citation": _SS, "notes": "Fast"},
    # Rahu / Ketu: always vakra
    {"graha": "Rahu",    "motion_state": "vakra",    "speed_threshold_low": None, "speed_threshold_high": None, "threshold_type": "always", "typical_speed_dps": -0.053, "classical_citation": _SS, "notes": "Rahu mean node is always retrograde; speed ≈ –0.053°/day"},
    {"graha": "Ketu",    "motion_state": "vakra",    "speed_threshold_low": None, "speed_threshold_high": None, "threshold_type": "always", "typical_speed_dps": -0.053, "classical_citation": _SS, "notes": "Ketu mean node is always retrograde; speed ≈ –0.053°/day"},
]


# ── 5. bg_combustion_orbs (8 rows) ────────────────────────────────────────────
# Columns: graha, orb_degrees, deep_orb_degrees, retrograde_note, classical_citation
# Sun is never combust — no row for Sun.

_COMBUSTION_ORBS: list[tuple[str, int, int, str | None, str]] = [
    ("Moon",    12, 10, None,
     _SARAVALI),
    ("Mars",    17, 15, None,
     _SARAVALI),
    ("Mercury", 14, 12,
     "Retrograde Mercury not considered combust by some authorities (Saravali)",
     _SARAVALI),
    ("Jupiter", 11,  9, None,
     _SARAVALI),
    ("Venus",   10,  8,
     "Retrograde Venus (Vipra-chara) immune from combustion per some authorities",
     _SARAVALI),
    ("Saturn",  15, 12, None,
     _SARAVALI),
    ("Rahu",     9,  7,
     "Nodes combust per some traditions; excluded by others",
     "BPHS Ch.3 (combustion doctrine; Rahu/Ketu orb per traditional commentary)"),
    ("Ketu",     9,  7,
     "Nodes combust per some traditions; excluded by others",
     "BPHS Ch.3 (combustion doctrine; Rahu/Ketu orb per traditional commentary)"),
]


# ── Writer ─────────────────────────────────────────────────────────────────────

@register("bg_dignity_reference")
class BgDignityReferenceWriter(WriterBase):
    """
    Seeds all 5 dignity/condition reference tables (151 rows total).

    L0 (Brahmagyan) writer — chart-agnostic static reference only.
    No PyJHora calls, no per-chart computation, no LLM.
    Idempotency: ON CONFLICT DO UPDATE (L0 standard §N.3).

    All seed data is sourced from migration 250_bg_dignity_reference.sql
    and validated against the constants in ga_writers/ga_condition_writer.py.

    Table row counts:
      bg_dignity_reference           9
      bg_graha_naisargika_friendship 72
      bg_avastha_schemes             35
      bg_motion_state_thresholds     27
      bg_combustion_orbs              8
                             total: 151
    """

    asset_id = "bg_dignity_reference"

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()

        if ctx.dry_run:
            logger.info("[bg_dignity_reference] dry_run=True — skipping INSERT")
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes="dry_run",
                duration_seconds=round(time.time() - t0, 2),
            )

        counts: dict[str, int] = {}
        conn = ctx.db_conn

        with conn.cursor() as cur:
            counts["bg_dignity_reference"] = self._seed_dignity_reference(cur)
            counts["bg_graha_naisargika_friendship"] = self._seed_naisargika_friendship(cur)
            counts["bg_avastha_schemes"] = self._seed_avastha_schemes(cur)
            counts["bg_motion_state_thresholds"] = self._seed_motion_state_thresholds(cur)
            counts["bg_combustion_orbs"] = self._seed_combustion_orbs(cur)

        total = sum(counts.values())
        elapsed = round(time.time() - t0, 2)
        logger.info(
            "[bg_dignity_reference] complete — %d rows upserted in %.2fs: %s",
            total, elapsed, counts,
        )
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total,
            duration_seconds=elapsed,
            notes=str(counts),
        )

    # ── private seed methods ───────────────────────────────────────────────────

    def _seed_dignity_reference(self, cur: Any) -> int:
        """Seed bg_dignity_reference (9 rows, one per graha)."""
        affected = 0
        for row in _DIGNITY_REFERENCE:
            cur.execute(
                """
                INSERT INTO bg_dignity_reference
                  (graha, exaltation_sign, exaltation_degree,
                   debilitation_sign, debilitation_degree,
                   moolatrikona_sign, moolatrikona_from, moolatrikona_to,
                   own_signs, classical_citation, notes, variant_traditions)
                VALUES
                  (%(graha)s, %(exaltation_sign)s, %(exaltation_degree)s,
                   %(debilitation_sign)s, %(debilitation_degree)s,
                   %(moolatrikona_sign)s, %(moolatrikona_from)s, %(moolatrikona_to)s,
                   %(own_signs)s, %(classical_citation)s, %(notes)s,
                   %(variant_traditions)s::jsonb)
                ON CONFLICT (graha) DO UPDATE SET
                  exaltation_sign     = EXCLUDED.exaltation_sign,
                  exaltation_degree   = EXCLUDED.exaltation_degree,
                  debilitation_sign   = EXCLUDED.debilitation_sign,
                  debilitation_degree = EXCLUDED.debilitation_degree,
                  moolatrikona_sign   = EXCLUDED.moolatrikona_sign,
                  moolatrikona_from   = EXCLUDED.moolatrikona_from,
                  moolatrikona_to     = EXCLUDED.moolatrikona_to,
                  own_signs           = EXCLUDED.own_signs,
                  classical_citation  = EXCLUDED.classical_citation,
                  notes               = EXCLUDED.notes,
                  variant_traditions  = EXCLUDED.variant_traditions
                """,
                row,
            )
            affected += cur.rowcount
        return affected

    def _seed_naisargika_friendship(self, cur: Any) -> int:
        """Seed bg_graha_naisargika_friendship (72 rows)."""
        cur.executemany(
            """
            INSERT INTO bg_graha_naisargika_friendship
              (graha, other_graha, relation, classical_citation)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (graha, other_graha) DO UPDATE SET
              relation           = EXCLUDED.relation,
              classical_citation = EXCLUDED.classical_citation
            """,
            _NAISARGIKA_FRIENDSHIP,
        )
        return cur.rowcount

    def _seed_avastha_schemes(self, cur: Any) -> int:
        """Seed bg_avastha_schemes (35 rows)."""
        cur.executemany(
            """
            INSERT INTO bg_avastha_schemes
              (scheme_name, state_name, state_order, determination_rule,
               classical_citation, notes)
            VALUES (%s, %s, %s, %s::jsonb, %s, %s)
            ON CONFLICT (scheme_name, state_name) DO UPDATE SET
              state_order        = EXCLUDED.state_order,
              determination_rule = EXCLUDED.determination_rule,
              classical_citation = EXCLUDED.classical_citation,
              notes              = EXCLUDED.notes
            """,
            _AVASTHA_SCHEMES,
        )
        return cur.rowcount

    def _seed_motion_state_thresholds(self, cur: Any) -> int:
        """Seed bg_motion_state_thresholds (27 rows)."""
        affected = 0
        for row in _MOTION_STATE_THRESHOLDS:
            cur.execute(
                """
                INSERT INTO bg_motion_state_thresholds
                  (graha, motion_state, speed_threshold_low, speed_threshold_high,
                   threshold_type, typical_speed_dps, classical_citation, notes)
                VALUES
                  (%(graha)s, %(motion_state)s, %(speed_threshold_low)s,
                   %(speed_threshold_high)s, %(threshold_type)s,
                   %(typical_speed_dps)s, %(classical_citation)s, %(notes)s)
                ON CONFLICT (graha, motion_state) DO UPDATE SET
                  speed_threshold_low  = EXCLUDED.speed_threshold_low,
                  speed_threshold_high = EXCLUDED.speed_threshold_high,
                  threshold_type       = EXCLUDED.threshold_type,
                  typical_speed_dps    = EXCLUDED.typical_speed_dps,
                  classical_citation   = EXCLUDED.classical_citation,
                  notes                = EXCLUDED.notes
                """,
                row,
            )
            affected += cur.rowcount
        return affected

    def _seed_combustion_orbs(self, cur: Any) -> int:
        """Seed bg_combustion_orbs (8 rows; Sun is never combust — no row)."""
        cur.executemany(
            """
            INSERT INTO bg_combustion_orbs
              (graha, orb_degrees, deep_orb_degrees, retrograde_note, classical_citation)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (graha) DO UPDATE SET
              orb_degrees        = EXCLUDED.orb_degrees,
              deep_orb_degrees   = EXCLUDED.deep_orb_degrees,
              retrograde_note    = EXCLUDED.retrograde_note,
              classical_citation = EXCLUDED.classical_citation
            """,
            _COMBUSTION_ORBS,
        )
        return cur.rowcount
