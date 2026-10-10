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

Volume: 9 engine rows + 68 writer-owned rule rows + 7 retained migration-owned
double-transit rule rows + 27 moorti rows.

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

# F-145: Venus unfavourable houses 6/7/10 — verified directly against the ingested
# classical-text corpus (read_classical_text / find_verses_about), not cited secondhand.
# Phaladeepika Adh. XXVI Slokas 2, 8 & 21 establish Venus transit unfavourable at 6th,
# 7th, 10th from the Moon (and favourable at all other houses, including 11th/12th,
# which BG_TRANSIT_RULES already carries as favourable — ids 179/180). Owner-ruled
# 2026-08-22; do NOT cite "BPHS Ch.29" for these three rows — that citation could not
# be verified against the corpus for this content.
PD_ADH26_S2_8_21 = "Phaladeepika Adh. XXVI, Slokas 2, 8 & 21 (Gochara — Sastri trans. 1950)"

# L0 repair item 1 (KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md §1): the 35 favourable+vedha
# rows for the seven classical grahas previously cited "BPHS Ch.29" — refuted; BPHS
# page 29 in the served corpus is Bhava Padas, and no BPHS transit-vedha chapter
# exists (bg_gochara_citation_resolution.GOGACHARA_PHALA_BPHS_29 = unresolved,
# migration 565). Their content is verbatim Phaladipika Adh. XXVI slokas 3-8,
# row-verified against the corpus (KSHETRA_INDEPENDENT_REVIEW_7_8_9_v1_0.md,
# corroborated by KIMI_K3_CLOSE_REVIEW_KSHETRA_v1_0.md). Re-cited PAGE-ANCHORED —
# verse_ref in this corpus is page-based; a chapter.sloka citation does not resolve.
PD_ADH26_PG322_SUN     = "Phaladipika Adh. XXVI, Sloka 3 — phaladeepika:PG322:C1 (Sastri trans. 1950)"
PD_ADH26_PG322_MOON    = "Phaladipika Adh. XXVI, Sloka 4 — phaladeepika:PG322:C1 (Sastri trans. 1950)"
PD_ADH26_PG322_MARS    = "Phaladipika Adh. XXVI, Sloka 5 — phaladeepika:PG322:C1 (Sastri trans. 1950)"
PD_ADH26_PG322_SATURN  = "Phaladipika Adh. XXVI, Sloka 5 — phaladeepika:PG322:C1 (Sastri trans. 1950)"
PD_ADH26_PG323_MERCURY = "Phaladipika Adh. XXVI, Sloka 6 — phaladeepika:PG323:C1 (Sastri trans. 1950)"
PD_ADH26_PG323_JUPITER = "Phaladipika Adh. XXVI, Sloka 7 — phaladeepika:PG323:C1 (Sastri trans. 1950)"
PD_ADH26_PG323_VENUS   = "Phaladipika Adh. XXVI, Sloka 8 — phaladeepika:PG323:C1 (Sastri trans. 1950)"

# Citation Pass 2 (decision OS-2026-10-05-CITATIONS, PASS2_DECISIONS.tsv, six rows), FORM (b) ruled by SS via Pravaha: the six Rahu/Ketu house-vedha
# rows (3rd/6th/11th from the Moon). Pass 2 read Phaladeepika XXVI sl.2 (phaladeepika:PG321:C1: the Sun is good in the 6th, 3rd and 10th and "Rahu and
# Ketu are similar to the Sun"; Ketu rows) and sl.24 (phaladeepika:PG331:C1: Rahu's results by house; Rahu rows) and found the TRANSIT RESULT sourced.
# Only the vedha partner house is an inference (the Sun's vedha, sl.3, carried to the node), so the citation stays UNSOURCED for it and says so:
#   UNSOURCED (vedha partner: inference, not in the cited verses) — transit result: <text, sl.> [machine locus <text_id>:PG<n>:C<n>] "<excerpt>"
# It MUST START with UNSOURCED: services/gochara_rules/vedha_derive.py (pairs_from_rows) refuses a node vedha row that does not (ND-NODE-VEDHA is open),
# and ka_vedha_gochara derives its stamps from that prefix. Nothing the loader checks changes: rule_type 'favourable', primary_house / vedha_house, exactly
# 3 Rahu + 3 Ketu rows, one row per (graha, primary_house). The text sits inside the loader's pairs_content_digest, so that digest changes by construction.
# The census reads this shape through the declared split_citation of bg_transit_rules' source declaration (asset_census.py: the transit result must
# resolve to a corpus chunk; any other UNSOURCED text stays a placeholder). Known finding: vedha partner unsourced, awaiting the owner ruling ND-NODE-VEDHA.
# Rows keep their identity (no id churn: gochara_resonance_map.source_rule_id references them); the phala text stays project prose; each rule_notes
# carries, as literal text, "disposition sourced Phaladeepika XXVI.2 (both nodes) and XXVI.24 (Rahu); vedha pair INFERRED from the Sun's (śl.3) via the
# śl.2 equivalence" (Literals, not concatenations: test_e6_l0_batch2_declarations pins every text-building expression of this module.)
# The pre-change rows hashed to migration 1078's pin (1dbdd265...); the rebuilt rows hash to the pin migration 1320 writes, both re-derived by
# tests/l0/test_citation_pass2_transit.py on a disposable Postgres.
# (Line count of this block is fixed on purpose: FINGERPRINT_DECLARATIONS.json cites the INSERT statements below by line number.)
# Per row (decision text, PASS2_DECISIONS.tsv): ALL six rows name BOTH verses, sl.2 (phaladeepika:PG321:C1) and sl.24 (phaladeepika:PG331:C1), in the locus words; the one bracketed machine locus
# (the shape allows exactly one) is the verse that states the row's house result: sl.24 for Rahu, sl.2 for Ketu. Excerpts are sub-sequences of the decision's quotations, at most 25 words (checked).
# The machine locus resolves to the chunk id <text_id>_pg<4-digit page>_c<2-digit chunk>: phaladeepika_pg0331_c01 / phaladeepika_pg0321_c01 (read in pass 2).
# Why a split form and not a K1 string: the vedha partner is NOT stated for the nodes (SS ruling via Pravaha, form b); the transit result is. The decision text is unchanged.
# Apply order: migration 1320 first (it moves the stored pin to the rebuilt content), then the governed rebuild in expected-change mode, held until the L0 data batch after S-L2.
# Every other seed row of this table is unchanged (hashed against a pin in the test).
#

# TI-L0-10 (SS Q3, INDEX section 8): the 19 rows that cited "BPHS Ch.29 (Gochara Phala)"
# and the 5 rows that cited the chapter-only "Phaladeepika Ch.26" are re-sourced to the
# Phaladipika Adh. XXVI result slokas (9-24) that state each result. Every (sloka, page)
# pair below was read in the served corpus (classical_text_chunks, text_id='phaladeepika',
# verse_ref PG324:C1..PG331:C1) on 2026-10-03; the valence of each sloka agrees with the
# row's rule_type. verse_ref is PAGE-based in this corpus, so the citation is
# page-anchored (a chapter.sloka locator does not resolve). Evidence table and quotes:
# 00_ARCHITECTURE/briefs/suvarna/layers/L0/L0_WAVE_REBUILD_PLAN_v1_0.md (TI-L0-10).
_PD_ED = "(Sastri trans. 1950)"


def _pd_result(sloka: int, pages: str) -> str:
    return f"Phaladipika Adh. XXVI, Sloka {sloka} \u2014 phaladeepika:{pages} {_PD_ED}"


# (graha, primary_house) -> citation for the 18 classical-graha/Rahu rows the corpus states directly.
PD_RESULT_CITATION: dict[tuple[str, int], str] = {
    ("sun", 1): _pd_result(9, "PG324:C1"),
    ("sun", 5): _pd_result(10, "PG324:C1"),
    ("sun", 8): _pd_result(10, "PG324:C1-PG325:C1"),      # sloka 10 runs across the page break
    ("moon", 8): _pd_result(12, "PG325:C1"),
    ("mars", 1): _pd_result(13, "PG326:C1"),
    ("mars", 4): _pd_result(13, "PG326:C1"),
    ("mars", 8): _pd_result(15, "PG326:C1-PG327:C1"),     # sloka 15 runs across the page break
    ("jupiter", 4): _pd_result(18, "PG328:C1"),
    ("jupiter", 8): _pd_result(19, "PG328:C1"),
    ("saturn", 1): _pd_result(22, "PG330:C1"),
    ("saturn", 4): _pd_result(22, "PG330:C1"),
    ("saturn", 8): _pd_result(22, "PG330:C1"),
    ("rahu", 1): _pd_result(24, "PG331:C1"),
    ("rahu", 2): _pd_result(24, "PG331:C1"),
    ("rahu", 4): _pd_result(24, "PG331:C1"),
    ("rahu", 7): _pd_result(24, "PG331:C1"),
    ("rahu", 8): _pd_result(24, "PG331:C1"),
    ("rahu", 12): _pd_result(24, "PG331:C1"),
}

# Ketu has no sloka of its own in the served corpus. Adh. XXVI Sloka 2 (PG321:C1) states the equivalence ("Rahu and Ketu are
# similar to the Sun"), so the five Ketu rows whose valence agrees with that reading cite the equivalence HONESTLY as an
# equivalence AND name the SUN sloka it refers to for that house (not Rahu's Sloka 24: the equivalence equates Ketu with the Sun):
# Sun 1st/2nd/4th = Sloka 9 (PG324:C1), Sun 7th = Sloka 10 (PG324:C1), Sun 8th = Sloka 10 (PG324:C1-PG325:C1). An acharya must
# accept the equivalence (spot-check item); if not accepted these five become UNSOURCED like the six node vedha rows.
_KETU_SUN_SLOKA: dict[int, tuple[int, str, str]] = {
    1: (9, "PG324:C1", "1st"), 2: (9, "PG324:C1", "2nd"), 4: (9, "PG324:C1", "4th"),
    7: (10, "PG324:C1", "7th"), 8: (10, "PG324:C1-PG325:C1", "8th"),
}


def _ketu_equivalence_citation(house: int) -> str:
    sloka, pages, ordinal = _KETU_SUN_SLOKA[house]
    return (
        "Phaladipika Adh. XXVI, Sloka 2 \u2014 phaladeepika:PG321:C1 (\"Rahu and Ketu are similar to the Sun\"), "
        f"read with the SUN's Sloka {sloka} \u2014 phaladeepika:{pages} for the {ordinal} house. "
        "BY STATED EQUIVALENCE, not a Ketu-specific sloka; acharya acceptance pending " + _PD_ED
    )


KETU_BY_EQUIVALENCE_CITATION: dict[int, str] = {h: _ketu_equivalence_citation(h) for h in _KETU_SUN_SLOKA}

# Ketu 12th is stored FAVOURABLE. The old "BPHS Ch.29" citation is refuted (BPHS page 29 is
# Bhava Padas), and the corpus reading above points the OTHER way (Sun 12th: sorrow, loss of
# wealth, Sloka 11 PG325:C1; Rahu 12th: expenditure, Sloka 24 PG331:C1). The row is kept (B.10:
# never silently dropped) and its valence is NOT changed here (that is an acharya decision);
# the citation says plainly that it is unsourced and contradicted.
KETU_12_UNSOURCED_CONTRADICTED = (
    "UNSOURCED \u2014 the former citation (BPHS Ch.29) is refuted (BPHS page 29 in the served "
    "corpus is Bhava Padas). The served Phaladeepika text points the other way: Sloka 2 "
    "(phaladeepika:PG321:C1) makes Ketu similar to the Sun, whose 12th-house transit gives "
    "sorrow and loss of wealth (Sloka 11, phaladeepika:PG325:C1), and Rahu's 12th is "
    "expenditure (Sloka 24, phaladeepika:PG331:C1). Valence retained pending acharya review."
)

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
    # ── SUN (Surya) Gochara — Phaladeepika Adh. XXVI (TI-L0-10: citations page-anchored per row) ────────────────────────────────────
    {
        "rule_type": "favourable",
        "graha": "sun",
        "primary_house": 3,
        "vedha_house": 9,
        "phala": "Courage, travel, gain from siblings",
        "classical_citation": PD_ADH26_PG322_SUN,
        "rule_notes": (
            "Vedha from 9th house transit nullifies result. Exception (sl. 3): "
            "a Saturn transit through the vedha house does not nullify — L0 repair "
            "item 2 Sec.4; bg_transit_rules has no exception column, declared here "
            "as an honest precision limit, not silently resolved."
        ),
    },
    {
        "rule_type": "favourable",
        "graha": "sun",
        "primary_house": 6,
        "vedha_house": 12,
        "phala": "Defeat of enemies, health improvement",
        "classical_citation": PD_ADH26_PG322_SUN,
        "rule_notes": (
            "Vedha from 12th house transit nullifies result. Exception (sl. 3): "
            "a Saturn transit through the vedha house does not nullify — L0 repair "
            "item 2 Sec.4; bg_transit_rules has no exception column, declared here "
            "as an honest precision limit, not silently resolved."
        ),
    },
    {
        "rule_type": "favourable",
        "graha": "sun",
        "primary_house": 10,
        "vedha_house": 4,
        "phala": "Career success, fame, royal favour",
        "classical_citation": PD_ADH26_PG322_SUN,
        "rule_notes": (
            "Vedha from 4th house transit nullifies result. Exception (sl. 3): "
            "a Saturn transit through the vedha house does not nullify — L0 repair "
            "item 2 Sec.4; bg_transit_rules has no exception column, declared here "
            "as an honest precision limit, not silently resolved."
        ),
    },
    {
        "rule_type": "favourable",
        "graha": "sun",
        "primary_house": 11,
        "vedha_house": 5,
        "phala": "Financial gains, fulfillment of desires",
        "classical_citation": PD_ADH26_PG322_SUN,
        "rule_notes": (
            "Vedha from 5th house transit nullifies result. Exception (sl. 3): "
            "a Saturn transit through the vedha house does not nullify — L0 repair "
            "item 2 Sec.4; bg_transit_rules has no exception column, declared here "
            "as an honest precision limit, not silently resolved."
        ),
    },
    {
        "rule_type": "unfavourable",
        "graha": "sun",
        "primary_house": 1,
        "vedha_house": None,
        "phala": "Ill health, loss of position, eye trouble",
        "classical_citation": PD_RESULT_CITATION[("sun", 1)],
        "rule_notes": "Generally inauspicious for health and status",
    },
    {
        "rule_type": "unfavourable",
        "graha": "sun",
        "primary_house": 5,
        "vedha_house": None,
        "phala": "Trouble with children, loss of intelligence",
        "classical_citation": PD_RESULT_CITATION[("sun", 5)],
        "rule_notes": "Afflicts progeny and wisdom matters",
    },
    {
        "rule_type": "unfavourable",
        "graha": "sun",
        "primary_house": 8,
        "vedha_house": None,
        "phala": "Disease, obstacle, conflict with authority",
        "classical_citation": PD_RESULT_CITATION[("sun", 8)],
        "rule_notes": "Transit through 8th from Moon — serious affliction",
    },
    # ── MOON (Chandra) Gochara — Phaladeepika Adh. XXVI (TI-L0-10: citations page-anchored per row) ──────────────────────────────────
    {
        "rule_type": "favourable",
        "graha": "moon",
        "primary_house": 1,
        "vedha_house": 5,
        "phala": "Good health, mental peace, bodily comforts",
        "classical_citation": PD_ADH26_PG322_MOON,
        "rule_notes": (
            "Vedha from 5th house nullifies result. Exception (sl. 4): a Mercury "
            "transit through the vedha house does not nullify — L0 repair item 2 "
            "Sec.4; bg_transit_rules has no exception column, declared here as an "
            "honest precision limit, not silently resolved."
        ),
    },
    {
        "rule_type": "favourable",
        "graha": "moon",
        "primary_house": 3,
        "vedha_house": 9,
        "phala": "Gain from siblings, short journeys, enterprise",
        "classical_citation": PD_ADH26_PG322_MOON,
        "rule_notes": (
            "Vedha from 9th nullifies result. Exception (sl. 4): a Mercury transit "
            "through the vedha house does not nullify — L0 repair item 2 Sec.4; "
            "bg_transit_rules has no exception column, declared here as an honest "
            "precision limit, not silently resolved."
        ),
    },
    {
        "rule_type": "favourable",
        "graha": "moon",
        "primary_house": 6,
        "vedha_house": 12,
        "phala": "Defeat of enemies, good health",
        "classical_citation": PD_ADH26_PG322_MOON,
        "rule_notes": (
            "Vedha from 12th nullifies result. Exception (sl. 4): a Mercury transit "
            "through the vedha house does not nullify — L0 repair item 2 Sec.4; "
            "bg_transit_rules has no exception column, declared here as an honest "
            "precision limit, not silently resolved."
        ),
    },
    {
        "rule_type": "favourable",
        "graha": "moon",
        "primary_house": 7,
        "vedha_house": 2,
        "phala": "Gain in partnership, conjugal happiness",
        "classical_citation": PD_ADH26_PG322_MOON,
        "rule_notes": (
            "Vedha from 2nd nullifies result. Exception (sl. 4): a Mercury transit "
            "through the vedha house does not nullify — L0 repair item 2 Sec.4; "
            "bg_transit_rules has no exception column, declared here as an honest "
            "precision limit, not silently resolved."
        ),
    },
    {
        "rule_type": "favourable",
        "graha": "moon",
        "primary_house": 10,
        "vedha_house": 4,
        "phala": "Professional success, recognition",
        "classical_citation": PD_ADH26_PG322_MOON,
        "rule_notes": (
            "Vedha from 4th nullifies result. Exception (sl. 4): a Mercury transit "
            "through the vedha house does not nullify — L0 repair item 2 Sec.4; "
            "bg_transit_rules has no exception column, declared here as an honest "
            "precision limit, not silently resolved."
        ),
    },
    {
        "rule_type": "favourable",
        "graha": "moon",
        "primary_house": 11,
        "vedha_house": 8,
        "phala": "Gains, fulfilment of wishes",
        "classical_citation": PD_ADH26_PG322_MOON,
        "rule_notes": (
            "Vedha from 8th nullifies result. Exception (sl. 4): a Mercury transit "
            "through the vedha house does not nullify — L0 repair item 2 Sec.4; "
            "bg_transit_rules has no exception column, declared here as an honest "
            "precision limit, not silently resolved."
        ),
    },
    {
        "rule_type": "unfavourable",
        "graha": "moon",
        "primary_house": 8,
        "vedha_house": None,
        "phala": "Fear, sorrow, ill health",
        "classical_citation": PD_RESULT_CITATION[("moon", 8)],
        "rule_notes": "Moon in 8th from natal Moon is afflictive",
    },
    # ── MARS (Mangal) Gochara — Phaladeepika Adh. XXVI (TI-L0-10: citations page-anchored per row) ──────────────────────────────────
    {
        "rule_type": "favourable",
        "graha": "mars",
        "primary_house": 3,
        "vedha_house": 12,
        "phala": "Courage, bravery, victory over enemies",
        "classical_citation": PD_ADH26_PG322_MARS,
        "rule_notes": "Vedha from 12th nullifies result",
    },
    {
        "rule_type": "favourable",
        "graha": "mars",
        "primary_house": 6,
        "vedha_house": 9,
        "phala": "Defeat of enemies, liberation from debts",
        "classical_citation": PD_ADH26_PG322_MARS,
        "rule_notes": "Vedha from 9th nullifies result",
    },
    {
        "rule_type": "favourable",
        "graha": "mars",
        "primary_house": 11,
        "vedha_house": 5,
        "phala": "Financial gains, political success",
        "classical_citation": PD_ADH26_PG322_MARS,
        "rule_notes": "Vedha from 5th nullifies result",
    },
    {
        "rule_type": "unfavourable",
        "graha": "mars",
        "primary_house": 1,
        "vedha_house": None,
        "phala": "Fever, accidents, injury, quarrels",
        "classical_citation": PD_RESULT_CITATION[("mars", 1)],
        "rule_notes": "Mars transiting natal Moon sign — danger and conflict",
    },
    {
        "rule_type": "unfavourable",
        "graha": "mars",
        "primary_house": 4,
        "vedha_house": None,
        "phala": "Domestic strife, trouble to mother, property loss",
        "classical_citation": PD_RESULT_CITATION[("mars", 4)],
        "rule_notes": "Mars 4th from Moon — family and home afflictions",
    },
    {
        "rule_type": "unfavourable",
        "graha": "mars",
        "primary_house": 8,
        "vedha_house": None,
        "phala": "Danger, accidents, surgical risk",
        "classical_citation": PD_RESULT_CITATION[("mars", 8)],
        "rule_notes": "Mars 8th from Moon — severe affliction",
    },
    # ── MERCURY (Budha) Gochara — Phaladeepika Adh. XXVI (TI-L0-10: citations page-anchored per row) ─────────────────────────────────
    {
        "rule_type": "favourable",
        "graha": "mercury",
        "primary_house": 2,
        "vedha_house": 5,
        "phala": "Eloquence, financial gain through communication",
        "classical_citation": PD_ADH26_PG323_MERCURY,
        "rule_notes": (
            "Vedha from 5th nullifies result. Exception (sl. 6): a Moon transit "
            "through the vedha house does not nullify — L0 repair item 2 Sec.4; "
            "bg_transit_rules has no exception column, declared here as an honest "
            "precision limit, not silently resolved."
        ),
    },
    {
        "rule_type": "favourable",
        "graha": "mercury",
        "primary_house": 4,
        "vedha_house": 3,
        "phala": "Good education, domestic happiness, vehicles",
        "classical_citation": PD_ADH26_PG323_MERCURY,
        "rule_notes": (
            "Vedha from 3rd nullifies result. Exception (sl. 6): a Moon transit "
            "through the vedha house does not nullify — L0 repair item 2 Sec.4; "
            "bg_transit_rules has no exception column, declared here as an honest "
            "precision limit, not silently resolved."
        ),
    },
    {
        "rule_type": "favourable",
        "graha": "mercury",
        "primary_house": 6,
        "vedha_house": 9,
        "phala": "Victory over enemies, success in disputes",
        "classical_citation": PD_ADH26_PG323_MERCURY,
        "rule_notes": (
            "Vedha from 9th nullifies result. Exception (sl. 6): a Moon transit "
            "through the vedha house does not nullify — L0 repair item 2 Sec.4; "
            "bg_transit_rules has no exception column, declared here as an honest "
            "precision limit, not silently resolved."
        ),
    },
    {
        "rule_type": "favourable",
        "graha": "mercury",
        "primary_house": 8,
        "vedha_house": 1,
        "phala": "Success in trade or profession through resourcefulness",
        "classical_citation": PD_ADH26_PG323_MERCURY,
        "rule_notes": (
            "L0 repair item 2 Sec.3 (KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md): the "
            "text's sixth Mercury pair, absent from this table until this INSERT — "
            "phala phrasing follows this writer's existing Mercury convention "
            "(e.g. ids for houses 10/11), not invented. Vedha from 1st nullifies "
            "result. Exception (sl. 6): a Moon transit through the vedha house "
            "does not nullify — bg_transit_rules has no exception column, "
            "declared here as an honest precision limit, not silently resolved."
        ),
    },
    {
        "rule_type": "favourable",
        "graha": "mercury",
        "primary_house": 10,
        "vedha_house": 8,
        "phala": "Success in trade, professional recognition",
        "classical_citation": PD_ADH26_PG323_MERCURY,
        "rule_notes": (
            "Vedha from 8th nullifies result. Exception (sl. 6): a Moon transit "
            "through the vedha house does not nullify — L0 repair item 2 Sec.4; "
            "bg_transit_rules has no exception column, declared here as an honest "
            "precision limit, not silently resolved."
        ),
    },
    {
        "rule_type": "favourable",
        "graha": "mercury",
        "primary_house": 11,
        "vedha_house": 12,
        "phala": "Financial gains, accomplishment of desires",
        "classical_citation": PD_ADH26_PG323_MERCURY,
        "rule_notes": (
            "Vedha from 12th nullifies result. Exception (sl. 6): a Moon transit "
            "through the vedha house does not nullify — L0 repair item 2 Sec.4; "
            "bg_transit_rules has no exception column, declared here as an honest "
            "precision limit, not silently resolved."
        ),
    },
    # ── JUPITER (Guru) Gochara — Phaladeepika Adh. XXVI (TI-L0-10: citations page-anchored per row) ──────────────────────────────────
    {
        "rule_type": "favourable",
        "graha": "jupiter",
        "primary_house": 2,
        "vedha_house": 12,
        "phala": "Wealth accumulation, family happiness",
        "classical_citation": PD_ADH26_PG323_JUPITER,
        "rule_notes": "Jupiter 2nd from Moon — dhana yoga; vedha from 12th",
    },
    {
        "rule_type": "favourable",
        "graha": "jupiter",
        "primary_house": 5,
        "vedha_house": 4,
        "phala": "Good children, happiness, wisdom, spiritual gains",
        "classical_citation": PD_ADH26_PG323_JUPITER,
        "rule_notes": "Jupiter 5th from Moon; vedha from 4th",
    },
    {
        "rule_type": "favourable",
        "graha": "jupiter",
        "primary_house": 7,
        "vedha_house": 3,
        "phala": "Marital happiness, partnership gains",
        "classical_citation": PD_ADH26_PG323_JUPITER,
        "rule_notes": "Jupiter 7th from Moon; vedha from 3rd",
    },
    {
        "rule_type": "favourable",
        "graha": "jupiter",
        "primary_house": 9,
        "vedha_house": 10,
        "phala": "Dharmic activity, father's wellbeing, fortune",
        "classical_citation": PD_ADH26_PG323_JUPITER,
        "rule_notes": "Jupiter 9th from Moon; vedha from 10th",
    },
    {
        "rule_type": "favourable",
        "graha": "jupiter",
        "primary_house": 11,
        "vedha_house": 8,
        "phala": "Major gains, fulfilment of wishes, income rise",
        "classical_citation": PD_ADH26_PG323_JUPITER,
        "rule_notes": "Jupiter 11th from Moon — best transit; vedha from 8th",
    },
    {
        "rule_type": "unfavourable",
        "graha": "jupiter",
        "primary_house": 4,
        "vedha_house": None,
        "phala": "Domestic trouble, loss of comforts, mother's illness",
        "classical_citation": PD_RESULT_CITATION[("jupiter", 4)],
        "rule_notes": "Ashtama Guru precedes the 5th favourable transit",
    },
    {
        "rule_type": "unfavourable",
        "graha": "jupiter",
        "primary_house": 8,
        "vedha_house": None,
        "phala": "Obstacles, loss of position, health issues",
        "classical_citation": PD_RESULT_CITATION[("jupiter", 8)],
        "rule_notes": "Jupiter 8th from Moon — significant affliction",
    },
    # ── VENUS (Shukra) Gochara — Phaladeepika Adh. XXVI (TI-L0-10: citations page-anchored per row) ──────────────────────────────────
    {
        "rule_type": "favourable",
        "graha": "venus",
        "primary_house": 1,
        "vedha_house": 8,
        "phala": "Good health, pleasures, marital happiness",
        "classical_citation": PD_ADH26_PG323_VENUS,
        "rule_notes": "Venus 1st from Moon; vedha from 8th",
    },
    {
        "rule_type": "favourable",
        "graha": "venus",
        "primary_house": 2,
        "vedha_house": 7,
        "phala": "Wealth, food, comforts, family happiness",
        "classical_citation": PD_ADH26_PG323_VENUS,
        "rule_notes": "Venus 2nd from Moon; vedha from 7th",
    },
    {
        # L0 repair item 2 (KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md Sec.2, row id 35):
        # vedha_house corrected 11 -> 1 to match the text's 3rd-house pair. This
        # row is an exact transposition of id 179's (11,3) pair (reversed), which
        # explains its origin; primary_house=3 is correct and needed (deleting
        # this row would remove the table's only 3rd-house Venus pair), so the
        # repair is an UPDATE of vedha_house only, never a delete. Row 179 is
        # untouched.
        "rule_type": "favourable",
        "graha": "venus",
        "primary_house": 3,
        "vedha_house": 1,
        "phala": "Gains from siblings, short journeys, new ventures",
        "classical_citation": PD_ADH26_PG323_VENUS,
        "rule_notes": "Venus 3rd from Moon; vedha from 1st",
    },
    {
        "rule_type": "favourable",
        "graha": "venus",
        "primary_house": 4,
        "vedha_house": 10,
        "phala": "Domestic happiness, comforts, mother's well-being",
        "classical_citation": PD_ADH26_PG323_VENUS,
        "rule_notes": "Venus 4th from Moon; vedha from 10th",
    },
    {
        "rule_type": "favourable",
        "graha": "venus",
        "primary_house": 5,
        "vedha_house": 9,
        "phala": "Children, romance, creativity, speculative gains",
        "classical_citation": PD_ADH26_PG323_VENUS,
        "rule_notes": "Venus 5th from Moon; vedha from 9th",
    },
    {
        # L0 repair item 2 (KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md Sec.2, row id 44):
        # vedha_house corrected 1 -> 5 to match the text's 8th-house pair. This
        # row is an exact transposition of id 33's (1,8) pair (reversed), which
        # explains its origin; primary_house=8 is correct and needed (deleting
        # this row would remove the table's only 8th-house Venus pair), so the
        # repair is an UPDATE of vedha_house only, never a delete. Row 33 is
        # untouched.
        "rule_type": "favourable",
        "graha": "venus",
        "primary_house": 8,
        "vedha_house": 5,
        "phala": "Longevity support, gains through inheritance or partner",
        "classical_citation": PD_ADH26_PG323_VENUS,
        "rule_notes": "Venus 8th from Moon; vedha from 5th",
    },
    {
        # L0 repair item 2 (KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md Sec.2, row id 45):
        # vedha_house corrected 2 -> 11 — a content typo, not a transposition
        # (nearest text pair 9th->11th); primary_house=9 is unaffected, UPDATE only.
        "rule_type": "favourable",
        "graha": "venus",
        "primary_house": 9,
        "vedha_house": 11,
        "phala": "Dharmic fortune, prosperity, guru's grace",
        "classical_citation": PD_ADH26_PG323_VENUS,
        "rule_notes": "Venus 9th from Moon; vedha from 11th",
    },
    {
        "rule_type": "favourable",
        "graha": "venus",
        "primary_house": 11,
        "vedha_house": 3,
        "phala": "Gains, fulfilment of desires, elder sibling prosperity",
        "classical_citation": PD_ADH26_PG323_VENUS,
        "rule_notes": "Venus 11th from Moon; vedha from 3rd",
    },
    {
        "rule_type": "favourable",
        "graha": "venus",
        "primary_house": 12,
        "vedha_house": 6,
        "phala": "Pleasures of the bed, foreign travel, liberation-tending",
        "classical_citation": PD_ADH26_PG323_VENUS,
        "rule_notes": "Venus 12th from Moon; vedha from 6th",
    },
    # F-145: Venus unfavourable set (6th/7th/10th from Moon) — the writer previously
    # emitted zero Venus unfavourable rows at all, a real coverage gap. Verified against
    # the corpus (Phaladeepika Adh. XXVI, Slokas 2, 8 & 21); owner-ruled 2026-08-22.
    {
        "rule_type": "unfavourable",
        "graha": "venus",
        "primary_house": 6,
        "vedha_house": None,
        "phala": "Mishap; disputes and ill-health",
        "classical_citation": PD_ADH26_S2_8_21,
        "rule_notes": "Venus 6th from Moon — unfavourable transit",
    },
    {
        "rule_type": "unfavourable",
        "graha": "venus",
        "primary_house": 7,
        "vedha_house": None,
        "phala": "Trouble to wife; marital and partnership stress",
        "classical_citation": PD_ADH26_S2_8_21,
        "rule_notes": "Venus 7th from Moon — unfavourable despite Venus being karaka of 7th",
    },
    {
        "rule_type": "unfavourable",
        "graha": "venus",
        "primary_house": 10,
        "vedha_house": None,
        "phala": "Quarrel; professional friction",
        "classical_citation": PD_ADH26_S2_8_21,
        "rule_notes": "Venus 10th from Moon — unfavourable transit",
    },
    # ── SATURN (Shani) Gochara — Phaladeepika Adh. XXVI (TI-L0-10: citations page-anchored per row) ─────────────────────────────────
    {
        "rule_type": "favourable",
        "graha": "saturn",
        "primary_house": 3,
        "vedha_house": 12,
        "phala": "Courage, perseverance, enterprise, gains from effort",
        "classical_citation": PD_ADH26_PG322_SATURN,
        "rule_notes": (
            "Saturn 3rd from Moon — best transit; vedha from 12th. Exception "
            "(sl. 5): a Sun transit through the vedha house does not nullify — "
            "L0 repair item 2 Sec.4; bg_transit_rules has no exception column, "
            "declared here as an honest precision limit, not silently resolved."
        ),
    },
    {
        "rule_type": "favourable",
        "graha": "saturn",
        "primary_house": 6,
        "vedha_house": 9,
        "phala": "Victory over enemies, servants, legal gains",
        "classical_citation": PD_ADH26_PG322_SATURN,
        "rule_notes": (
            "Saturn 6th from Moon; vedha from 9th nullifies. Exception (sl. 5): "
            "a Sun transit through the vedha house does not nullify — L0 repair "
            "item 2 Sec.4; bg_transit_rules has no exception column, declared "
            "here as an honest precision limit, not silently resolved."
        ),
    },
    {
        "rule_type": "favourable",
        "graha": "saturn",
        "primary_house": 11,
        "vedha_house": 5,
        "phala": "Sustained income, gains through persistence",
        "classical_citation": PD_ADH26_PG322_SATURN,
        "rule_notes": (
            "Saturn 11th from Moon; vedha from 5th nullifies. Exception (sl. 5): "
            "a Sun transit through the vedha house does not nullify — L0 repair "
            "item 2 Sec.4; bg_transit_rules has no exception column, declared "
            "here as an honest precision limit, not silently resolved."
        ),
    },
    {
        "rule_type": "unfavourable",
        "graha": "saturn",
        "primary_house": 1,
        "vedha_house": None,
        "phala": "Sade Sati peak — hardship, health issues, delays",
        "classical_citation": PD_RESULT_CITATION[("saturn", 1)],
        "rule_notes": "Central phase of Sade Sati (7.5 year Saturn affliction cycle)",
    },
    {
        "rule_type": "unfavourable",
        "graha": "saturn",
        "primary_house": 4,
        "vedha_house": None,
        "phala": "Domestic troubles, loss of property, mother's illness",
        "classical_citation": PD_RESULT_CITATION[("saturn", 4)],
        "rule_notes": "Kantaka Saturn (4th) — classic obstacle transit",
    },
    {
        "rule_type": "unfavourable",
        "graha": "saturn",
        "primary_house": 8,
        "vedha_house": None,
        "phala": "Serious illness, accidents, prolonged suffering",
        "classical_citation": PD_RESULT_CITATION[("saturn", 8)],
        "rule_notes": "Ashtama Shani — worst Saturn transit position",
    },
    # ── RAHU Gochara — Phaladeepika Adh. XXVI (TI-L0-10: citations page-anchored per row) ──────────────────────
    {
        "rule_type": "favourable",
        "graha": "rahu",
        "primary_house": 3,
        "vedha_house": 9,
        "phala": "Enterprise, travel, gain through courage; sibling support",
        "classical_citation": "UNSOURCED (vedha partner: inference, not in the cited verses) — transit result: Phaladīpikā Adh. XXVI, Śl. 2 / 24 (Śl. 2 phaladeepika:PG321:C1 nodes like the Sun; Śl. 24 phaladeepika:PG331:C1 Rahu's transit effects) [machine locus phaladeepika:PG331:C1] \"Sun ... in the 6th, 3rd and 10th ... Rahu and Ketu are similar to the Sun; effects caused by Rahu ... (3) happiness\"",
        "rule_notes": "Rahu 3rd from Moon — gain and initiative. L0 repair item 3: vedha_house retained, disposition sourced Phaladeepika XXVI.2 (both nodes) and XXVI.24 (Rahu); vedha pair INFERRED from the Sun's (śl.3) via the śl.2 equivalence.",
    },
    {
        "rule_type": "favourable",
        "graha": "rahu",
        "primary_house": 6,
        "vedha_house": 12,
        "phala": "Defeat of enemies, legal victories, health improvement",
        "classical_citation": "UNSOURCED (vedha partner: inference, not in the cited verses) — transit result: Phaladīpikā Adh. XXVI, Śl. 2 / 24 (Śl. 2 phaladeepika:PG321:C1 nodes like the Sun; Śl. 24 phaladeepika:PG331:C1 Rahu's transit effects) [machine locus phaladeepika:PG331:C1] \"Sun ... in the 6th, 3rd and 10th ... Rahu and Ketu are similar to the Sun; effects caused by Rahu ... (6) happiness\"",
        "rule_notes": "Rahu 6th from Moon — ari-bhava placement aids in enemy removal. L0 repair item 3: vedha_house retained, disposition sourced Phaladeepika XXVI.2 (both nodes) and XXVI.24 (Rahu); vedha pair INFERRED from the Sun's (śl.3) via the śl.2 equivalence.",
    },
    {
        "rule_type": "favourable",
        "graha": "rahu",
        "primary_house": 11,
        "vedha_house": 5,
        "phala": "Financial gains, labha, fulfillment of desires through unconventional means",
        "classical_citation": "UNSOURCED (vedha partner: inference, not in the cited verses) — transit result: Phaladīpikā Adh. XXVI, Śl. 2 / 24 (Śl. 2 phaladeepika:PG321:C1 nodes like the Sun; Śl. 24 phaladeepika:PG331:C1 Rahu's transit effects) [machine locus phaladeepika:PG331:C1] \"all planets in the 11th ... Rahu and Ketu are similar to the Sun; effects caused by Rahu ... (11) happiness\"",
        "rule_notes": "Rahu 11th from Moon — labha amplified; shadow planet in gain house. L0 repair item 3: vedha_house retained, disposition sourced Phaladeepika XXVI.2 (both nodes) and XXVI.24 (Rahu); vedha pair INFERRED from the Sun's (śl.3) via the śl.2 equivalence.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "rahu",
        "primary_house": 1,
        "vedha_house": None,
        "phala": "Ill health, confusion, loss of clarity; fear and anxiety",
        "classical_citation": PD_RESULT_CITATION[("rahu", 1)],
        "rule_notes": "Rahu over natal Moon — mental disturbance; Sade-Sati-class affliction for Rahu.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "rahu",
        "primary_house": 2,
        "vedha_house": None,
        "phala": "Speech affliction, family disputes, financial drain",
        "classical_citation": PD_RESULT_CITATION[("rahu", 2)],
        "rule_notes": "Rahu 2nd from Moon — kutumba and dhana affliction.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "rahu",
        "primary_house": 4,
        "vedha_house": None,
        "phala": "Domestic troubles, property loss, mother's health affected",
        "classical_citation": PD_RESULT_CITATION[("rahu", 4)],
        "rule_notes": "Rahu 4th from Moon — Kantaka-class obstruction; home and sukha affliction.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "rahu",
        "primary_house": 7,
        "vedha_house": None,
        "phala": "Partnership conflicts, danger in travel, hidden adversaries",
        "classical_citation": PD_RESULT_CITATION[("rahu", 7)],
        "rule_notes": "Rahu 7th from Moon — kalatra and travel affliction.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "rahu",
        "primary_house": 8,
        "vedha_house": None,
        "phala": "Accidents, sudden illness, hidden dangers; fear of death",
        "classical_citation": PD_RESULT_CITATION[("rahu", 8)],
        "rule_notes": "Rahu 8th from Moon — randhra affliction; severe; longevity concern.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "rahu",
        "primary_house": 12,
        "vedha_house": None,
        "phala": "Hidden expenditure, foreign travel under duress, separation",
        "classical_citation": PD_RESULT_CITATION[("rahu", 12)],
        "rule_notes": "Rahu 12th from Moon — vyaya affliction; loss and isolation.",
    },
    # ── KETU Gochara — Phaladeepika Adh. XXVI (TI-L0-10: citations page-anchored per row) ──────────────────────
    {
        "rule_type": "favourable",
        "graha": "ketu",
        "primary_house": 3,
        "vedha_house": 9,
        "phala": "Moderate gain through effort; spiritual enterprise; sibling support",
        "classical_citation": "UNSOURCED (vedha partner: inference, not in the cited verses) — transit result: Phaladīpikā Adh. XXVI, Śl. 2 / 24 (Śl. 2 phaladeepika:PG321:C1 nodes like the Sun; Śl. 24 phaladeepika:PG331:C1 Rahu's transit effects) [machine locus phaladeepika:PG321:C1] \"Sun ... in the 6th, 3rd and 10th ... Rahu and Ketu are similar to the Sun; effects caused by Rahu ... (3) happiness\"",
        "rule_notes": "Ketu 3rd from Moon — paurushabala enterprise; less potent than Rahu here. L0 repair item 3: vedha_house retained, disposition sourced Phaladeepika XXVI.2 (both nodes) and XXVI.24 (Rahu); vedha pair INFERRED from the Sun's (śl.3) via the śl.2 equivalence.",
    },
    {
        "rule_type": "favourable",
        "graha": "ketu",
        "primary_house": 6,
        "vedha_house": 12,
        "phala": "Enemies subdued; disease removal; spiritual purification",
        "classical_citation": "UNSOURCED (vedha partner: inference, not in the cited verses) — transit result: Phaladīpikā Adh. XXVI, Śl. 2 / 24 (Śl. 2 phaladeepika:PG321:C1 nodes like the Sun; Śl. 24 phaladeepika:PG331:C1 Rahu's transit effects) [machine locus phaladeepika:PG321:C1] \"Sun ... in the 6th, 3rd and 10th ... Rahu and Ketu are similar to the Sun; effects caused by Rahu ... (6) happiness\"",
        "rule_notes": "Ketu 6th from Moon — moksha-karak in ari-bhava aids liberation from obstacles. L0 repair item 3: vedha_house retained, disposition sourced Phaladeepika XXVI.2 (both nodes) and XXVI.24 (Rahu); vedha pair INFERRED from the Sun's (śl.3) via the śl.2 equivalence.",
    },
    {
        "rule_type": "favourable",
        "graha": "ketu",
        "primary_house": 11,
        "vedha_house": 5,
        "phala": "Spiritual gains, gains through research or occult; modest material labha",
        "classical_citation": "UNSOURCED (vedha partner: inference, not in the cited verses) — transit result: Phaladīpikā Adh. XXVI, Śl. 2 / 24 (Śl. 2 phaladeepika:PG321:C1 nodes like the Sun; Śl. 24 phaladeepika:PG331:C1 Rahu's transit effects) [machine locus phaladeepika:PG321:C1] \"all planets in the 11th ... Rahu and Ketu are similar to the Sun; effects caused by Rahu ... (11) happiness\"",
        "rule_notes": "Ketu 11th from Moon — gains oriented toward karmic fulfilment. L0 repair item 3: vedha_house retained, disposition sourced Phaladeepika XXVI.2 (both nodes) and XXVI.24 (Rahu); vedha pair INFERRED from the Sun's (śl.3) via the śl.2 equivalence.",
    },
    {
        "rule_type": "favourable",
        "graha": "ketu",
        "primary_house": 12,
        "vedha_house": None,
        "phala": "Spiritual liberation, moksha progress, renunciation; retreat and deep contemplation",
        "classical_citation": KETU_12_UNSOURCED_CONTRADICTED,
        "rule_notes": "Ketu 12th from Moon — moksha-karaka in vyaya: uniquely auspicious for spiritual seekers.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "ketu",
        "primary_house": 1,
        "vedha_house": None,
        "phala": "Bodily affliction, confusion, spiritual restlessness; detachment from self",
        "classical_citation": KETU_BY_EQUIVALENCE_CITATION[1],
        "rule_notes": "Ketu over natal Moon — dissociation and health disturbance.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "ketu",
        "primary_house": 2,
        "vedha_house": None,
        "phala": "Financial loss, family separation, speech affliction",
        "classical_citation": KETU_BY_EQUIVALENCE_CITATION[2],
        "rule_notes": "Ketu 2nd from Moon — kutumba and dhana affliction.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "ketu",
        "primary_house": 4,
        "vedha_house": None,
        "phala": "Home disruption, loss of comforts, mother's health concerns",
        "classical_citation": KETU_BY_EQUIVALENCE_CITATION[4],
        "rule_notes": "Ketu 4th from Moon — Kantaka-class; domestic troubles and vehicle accidents.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "ketu",
        "primary_house": 7,
        "vedha_house": None,
        "phala": "Marital friction, separation, hidden adversary in partnership",
        "classical_citation": KETU_BY_EQUIVALENCE_CITATION[7],
        "rule_notes": "Ketu 7th from Moon — kalatra affliction; relationships tested.",
    },
    {
        "rule_type": "unfavourable",
        "graha": "ketu",
        "primary_house": 8,
        "vedha_house": None,
        "phala": "Surgery, accidents, sudden health crisis; karmic debt activation",
        "classical_citation": KETU_BY_EQUIVALENCE_CITATION[8],
        "rule_notes": "Ketu 8th from Moon — randhra + moksha karak: severe; karmic reckoning.",
    },
]

# TI-L0-10 / independent review L0A LOW-2 + NIT-1: a sloka-level citation now sits beside a `phala` summary that, for several rows,
# carries detail the cited sloka does not state (e.g. Moon 8th "Fear, sorrow, ill health" vs Sloka 12 "(8) untoward events"). Only the
# VALENCE (rule_type) of a re-sourced row is sloka-supported. Rather than rewrite summaries without an acharya decision (which would
# be inventing in the other direction), every re-sourced row says so in `rule_notes`. Ketu 12th's favourable valence is unsourced.
PHALA_INFERENCE_NOTE = (
    " [L0A: only the valence is supported by the cited sloka; any detail in `phala` beyond what that sloka states is INFERENCE, "
    "not sloka-derived - acharya review pending]"
)
KETU_12_NOTE = (
    " [L0A: the favourable valence of this row is UNSOURCED and the served Phaladeepika text points the other way (see "
    "classical_citation); `phala` and this note record the earlier reading - acharya decision pending]"
)


def _annotate_resourced_rows(rules: list[dict[str, Any]]) -> None:
    for r in rules:
        key = (r["graha"], r["primary_house"])
        if r["rule_type"] == "double_transit":
            continue
        if key == ("ketu", 12):
            r["rule_notes"] = (r.get("rule_notes") or "") + KETU_12_NOTE
        elif key in PD_RESULT_CITATION or (r["graha"] == "ketu" and r["rule_type"] == "unfavourable" and key[1] in _KETU_SUN_SLOKA):
            r["rule_notes"] = (r.get("rule_notes") or "") + PHALA_INFERENCE_NOTE


_annotate_resourced_rows(BG_TRANSIT_RULES)

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


# ── F-145 — writer-owned category reconciliation ─────────────────────────────
#
# bg_transit_rules.id is SERIAL and gochara_resonance_map.source_rule_id FK-references
# it (migration 459) — a blanket delete-then-reinsert would renumber ids and silently
# corrupt live citations (see the seed_transit_rules docstring/comment below). The
# ruled design instead scopes retirement to rows the writer actually OWNS: rows whose
# (rule_type, graha) both appear somewhere in BG_TRANSIT_RULES today. Anything outside
# that — migration 397's 7 `double_transit` rows (title-case 'Jupiter'/'Saturn'), and
# any future 'vedha' rule_type row, since this writer has never emitted one — is
# structurally excluded from the SQL WHERE clause in `_owned_row_filter`, not merely
# protected by a `lower()` coincidence: the ownership match below is deliberately
# case-sensitive, against the literal graha/rule_type strings BG_TRANSIT_RULES itself
# uses (always lowercase, by writer convention). A row belongs to this sweep only if
# it matches one of those literal values exactly.


def _owned_categories(rules: list[dict[str, Any]]) -> tuple[set[str], set[str]]:
    """Compute the (rule_type, graha) categories this writer owns, from the source list.

    Never hardcode this set — it must always be derived from `rules`
    (normally `BG_TRANSIT_RULES`) so the ownership boundary tracks the writer's actual
    output as it grows, rather than drifting behind it.
    """
    owned_types = {r["rule_type"] for r in rules}
    owned_grahas = {r["graha"] for r in rules}
    return owned_types, owned_grahas


def compute_stale_rule_ids(
    rules: list[dict[str, Any]],
    owned_db_rows: list[dict[str, Any]],
) -> list[int]:
    """
    Pure reconciliation logic (F-145). Given the writer's current source-of-truth
    `rules` (normally `BG_TRANSIT_RULES`) and the DB's current rows **already scoped**
    to the writer's owned categories (see `_owned_categories` — this function does not
    re-derive ownership from row shape), return the `id`s of rows whose
    `(graha, rule_type, primary_house)` key is absent from `rules` and should be
    retired.

    `owned_db_rows` must be dict-shaped rows with keys `id`, `graha`, `rule_type`,
    `primary_house` — the same shape `cur.fetchall()` returns on the orchestrator's
    connection, which is opened via `pipeline.orchestrator.db.connect()` with
    `row_factory=psycopg.rows.dict_row` (see `db.py`). A `seed_transit_rules` cursor
    inherits that connection-level row_factory, so its `SELECT id, graha, rule_type,
    primary_house FROM bg_transit_rules ...` rows arrive as dicts, never plain tuples
    — unpacking them as a 4-tuple would silently bind `row_id` to the literal string
    `"id"` (iterating the dict's keys) instead of the integer id, and the follow-on
    `DELETE FROM bg_transit_rules WHERE id = %s` would then crash with
    `invalid input syntax for type integer: "id"` (F-145 followup). Callers must
    never pass migration-owned or otherwise unowned rows into this function.
    """
    current_keys = {(r["graha"], r["rule_type"], r["primary_house"]) for r in rules}
    return [
        row["id"]
        for row in owned_db_rows
        if (row["graha"], row["rule_type"], row["primary_house"]) not in current_keys
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
            "bg_transit_rules_retired": 0,
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

    # ── F-145: retire stale rows in owned categories, absent from BG_TRANSIT_RULES ──
    # Scoped strictly to (rule_type, graha) pairs the writer owns (see `_owned_categories`
    # docstring above) — migration-owned rows (double_transit, title-case Jupiter/Saturn)
    # and the never-emitted 'vedha' rule_type never match this WHERE clause, so they are
    # never even fetched as candidates, let alone deleted. Safe because a genuinely
    # FK-referenced row (gochara_resonance_map.source_rule_id → bg_transit_rules.id,
    # migration 459) will raise loudly rather than being silently dropped — the same
    # design the :798 comment above documents for why delete-then-insert was removed.
    owned_types, owned_grahas = _owned_categories(BG_TRANSIT_RULES)
    retired_ids: list[int] = []
    if owned_types and owned_grahas:
        cur.execute(
            """
            SELECT id, graha, rule_type, primary_house
            FROM bg_transit_rules
            WHERE rule_type = ANY(%s) AND graha = ANY(%s)
            """,
            (sorted(owned_types), sorted(owned_grahas)),
        )
        retired_ids = compute_stale_rule_ids(BG_TRANSIT_RULES, cur.fetchall())
        for stale_id in retired_ids:
            cur.execute("DELETE FROM bg_transit_rules WHERE id = %s", (stale_id,))
        if retired_ids:
            logger.warning(
                "[transit] F-145 reconciliation: retired %d stale bg_transit_rules "
                "row(s) absent from BG_TRANSIT_RULES source-of-truth (owned "
                "categories only) — ids=%s",
                len(retired_ids), retired_ids,
            )

    # ── F-145: freshness assertion ────────────────────────────────────────────────
    # Detects silent re-accretion of stray rows in owned categories on future runs —
    # without this the cleanup above is a one-time fix, not a standing detector
    # (CLAUDE.md §N.8: a signal without a real, currently-running check is null).
    if owned_types and owned_grahas:
        cur.execute(
            "SELECT COUNT(*) AS owned_row_count FROM bg_transit_rules "
            "WHERE rule_type = ANY(%s) AND graha = ANY(%s)",
            (sorted(owned_types), sorted(owned_grahas)),
        )
        # `cur` inherits the connection's dict_row row_factory (see db.py / the
        # compute_stale_rule_ids docstring above) — `cur.fetchone()` returns a dict,
        # not a 1-tuple. `(owned_row_count,) = cur.fetchone()` would silently unpack
        # to the dict's sole KEY ("count"/"owned_row_count", a string) rather than
        # the count value, making this comparison always-true and this warning fire
        # on every single build (the same defect class as compute_stale_rule_ids,
        # F-145 followup).
        owned_row_count = cur.fetchone()["owned_row_count"]
        if owned_row_count != len(BG_TRANSIT_RULES):
            logger.warning(
                "[transit] F-145 freshness check failed: bg_transit_rules owned-category "
                "row count is %d, expected %d (len(BG_TRANSIT_RULES)) — possible silent "
                "re-accretion of stray rows, or a retirement blocked by an FK reference; "
                "investigate before trusting this build",
                owned_row_count, len(BG_TRANSIT_RULES),
            )

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
        "bg_transit_rules_retired": len(retired_ids),
        "bg_transit_moorti": moorti_count,
        "total": engine_count + rules_count + moorti_count,
    }
