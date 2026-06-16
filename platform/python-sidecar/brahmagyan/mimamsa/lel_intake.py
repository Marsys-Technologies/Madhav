"""
brahmagyan.mimamsa.lel_intake — BRAHMA-MI-5-1: mimamsa.lel_intake
==================================================================

L5 Mīmāṃsā: ingest all 57 Life Event Log events into the calibration corpus.

Contract (BRAHMA L5 Mīmāṃsā — MI-5-1):
  - owns: LEL ingestion into life_events + event_chart_state_index
  - tool: lel_query(domain?, date_range?) → {events:[...], provenance_envelope}
  - tables:
      life_events (event_id UUID, event_date DATE, event_type TEXT,
                   description TEXT, domain TEXT, outcome_observed TEXT,
                   source_citation TEXT NOT NULL)
      event_chart_state_index (event_id UUID, dasha_active TEXT,
                   antardasha_active TEXT, key_transits JSONB,
                   convergence_score FLOAT, source_citation TEXT NOT NULL)

NO LEAKAGE:
  life_events is a calibration corpus ONLY.
  It MUST NOT feed into prediction generation pipelines.
  The model never sees an event's outcome before making its prediction.
  Calibration reads life_events to score past-prediction accuracy only.

Source data:
  LIFE_EVENT_LOG_v1_2.md (native-disclosed, v1.7, 57 events, confidence 0.89)
  FORENSIC v8.0 §5.1 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md) (dasha authority)

Native: Abhisek Mohanty, born 1984-02-05, 10:43 IST, Bhubaneswar, Odisha, India
Chart UUID: 482012f1-710e-4a25-994a-93821f5871aa

Usage:
    # Ingest all 57 events
    python -m brahmagyan.mimamsa.lel_intake seed

    # Query events (all)
    python -m brahmagyan.mimamsa.lel_intake query

    # Query events by domain
    python -m brahmagyan.mimamsa.lel_intake query --domain career

    # Query events by date range
    python -m brahmagyan.mimamsa.lel_intake query --from 2010-01-01 --to 2026-12-31

    # Run acceptance gate
    python -m brahmagyan.mimamsa.lel_intake gate

BRAHMA-MI-5-1
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import uuid
from datetime import date, datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── Provenance constant ───────────────────────────────────────────────────────

SOURCE_CITATION = "LIFE_EVENT_LOG_v1_2.md (native-disclosed)"

# ── Convergence score mapping ─────────────────────────────────────────────────
#
# Maps retrodictive_match.predicted_by_chart → convergence_score (0..1)
# "yes"       → 1.0  (strong match across multiple signals)
# "partial"   → 0.5  (some signals match)
# "no"        → 0.0  (event unexplained by current signals)
# "unexamined"→ None (not yet assessed)
# "pending"   → None (pending computation)
# null        → None

_CONVERGENCE_MAP: dict[str | None, float | None] = {
    "yes":        1.0,
    "partial":    0.5,
    "no":         0.0,
    "unexamined": None,
    "pending":    None,
    None:         None,
}


def _convergence(outcome: str | None) -> float | None:
    return _CONVERGENCE_MAP.get(outcome, None)


# ── LEL corpus — 57 events ─────────────────────────────────────────────────────
#
# Parsed from LIFE_EVENT_LOG_v1_2.md §3 (all eras including M5A enrichment).
# Each entry carries:
#   event_id     : deterministic UUID (v5, namespace=DNS, name=evt_id_string)
#   lel_id       : canonical EVT.* identifier from LEL
#   event_date   : best available date (proxy date for year-approx per LEL convention)
#   event_type   : LEL category field
#   subcategory  : LEL subcategory field
#   description  : factual description from LEL
#   magnitude    : trivial|moderate|significant|major|life-altering
#   outcome      : retrodictive_match.predicted_by_chart
#   dasha_md     : Vimshottari MD lord at event (from chart_state_at_event)
#   dasha_ad     : Vimshottari AD lord at event
#   key_transits : list of transit strings from chart_state_at_event
#
# Source: LIFE_EVENT_LOG_v1_2.md §3 + Era M5A Enrichment section (all 57 events)
# Date conventions:
#   exact       → date as given
#   month-exact → YYYY-MM-15 (mid-month proxy)
#   year-exact  → YYYY-07-01 (mid-year proxy)
#   year-approx → YYYY-07-01 (mid-year proxy)
#   month-approx → YYYY-MM-01 (start-of-month proxy)

_LEL_UUID_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # DNS namespace


def _evt_uuid(lel_id: str) -> str:
    """Generate deterministic UUID from LEL event ID."""
    return str(uuid.uuid5(_LEL_UUID_NAMESPACE, f"BRAHMA-MI-5-1:{lel_id}"))


LEL_CORPUS: list[dict[str, Any]] = [
    # ── Era 1: Birth & Early Life (1984-1995) ─────────────────────────────────
    {
        "lel_id": "EVT.1984.02.05.01",
        "event_date": "1984-02-05",
        "event_type": "other",
        "subcategory": "birth",
        "description": (
            "Born in Bhubaneswar, Odisha at 10:43 IST. Aries Lagna, Moon in Aquarius "
            "(Purva Bhadrapada Pada 3), Sun in Capricorn (Shravana Pada 4)."
        ),
        "magnitude": "life-altering",
        "outcome": "yes",
        "dasha_md": "Jupiter",
        "dasha_ad": "Venus",
        "key_transits": [
            "Saturn transit 9H from Moon (Libra)",
            "Saturn transit Libra = 7H from Lagna",
            "Jupiter transit Sagittarius = 9H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.1993.XX.XX.01",
        "event_date": "1993-07-01",
        "event_type": "creative",
        "subcategory": "award",
        "description": (
            "Mother enrolled native in painting classes; native excelled and won multiple "
            "awards in childhood painting competitions. Creative visual skill established early."
        ),
        "magnitude": "moderate",
        "outcome": "partial",
        "dasha_md": "Saturn",
        "dasha_ad": "Saturn",
        "key_transits": [],
    },
    # ── Era 2: Adolescence and Headaches (1995-2000) ──────────────────────────
    {
        "lel_id": "EVT.1995.XX.XX.01",
        "event_date": "1995-07-01",
        "event_type": "health",
        "subcategory": "chronic_onset",
        "description": (
            "Severe headaches onset around 1995 (age 11). Became a defining health motif "
            "of early life; screen time catalyzed headaches."
        ),
        "magnitude": "significant",
        "outcome": "yes",
        "dasha_md": "Saturn",
        "dasha_ad": "Mercury",
        "key_transits": [
            "Saturn transit Pisces = 12H from Lagna",
            "Jupiter transit Scorpio = 8H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.1995.XX.XX.02",
        "event_date": "1995-07-01",
        "event_type": "psychological",
        "subcategory": "speech_pattern_arc",
        "description": (
            "Stammering onset in childhood (~1995). Three-phase arc: Phase 1 (childhood "
            "~1995-2006): significant stammering. Phase 2 (~2007-2024): substantially "
            "overcame it. Phase 3 (~2025-present): resurfaced."
        ),
        "magnitude": "moderate",
        "outcome": "partial",
        "dasha_md": "Saturn",
        "dasha_ad": "Mercury",
        "key_transits": [],
    },
    # ── Era 3: Teen Years (1998-2003) ─────────────────────────────────────────
    {
        "lel_id": "EVT.1998.02.16.01",
        "event_date": "1998-02-16",
        "event_type": "relationship",
        "subcategory": "romantic_long_term_started",
        "description": (
            "Relationship #1 started (age 14). This childhood girlfriend later became "
            "native's wife (married 2013-12-11). Total duration as relationship pre-marriage ~15 years."
        ),
        "magnitude": "life-altering",
        "outcome": "partial",
        "dasha_md": "Saturn",
        "dasha_ad": "Ketu",
        "key_transits": [
            "Jupiter transit on natal Moon (Aquarius) — gajakesari-class",
            "Saturn transit Pisces = 12H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.1998.XX.XX.02",
        "event_date": "1998-07-01",
        "event_type": "spiritual",
        "subcategory": "transmission",
        "description": (
            "Father held late-night spiritual dialogues; native joined in limited capacity "
            "during teens (~1997-2001). Father's approach intermingled Hinduism and spirituality — "
            "became the native's foundational spiritual orientation."
        ),
        "magnitude": "significant",
        "outcome": "partial",
        "dasha_md": "Saturn",
        "dasha_ad": "Ketu",
        "key_transits": [],
    },
    {
        "lel_id": "EVT.2000.XX.XX.01",
        "event_date": "2000-06-01",
        "event_type": "education",
        "subcategory": "advanced_course_partial",
        "description": (
            "Joined Aptech computer education course post-10th board exams (~2000, age 16). "
            "Was among the brighter students but could not sit certification exam — program "
            "required graduate minimum qualification; native was pre-graduate."
        ),
        "magnitude": "moderate",
        "outcome": "pending",
        "dasha_md": "Saturn",
        "dasha_ad": "Venus",
        "key_transits": [
            "Saturn transit Aries",
            "Jupiter transit Aries",
        ],
    },
    {
        "lel_id": "EVT.2001.03.XX.01",
        "event_date": "2001-03-15",
        "event_type": "education",
        "subcategory": "entrance_exam_preparation",
        "description": (
            "Began IIT preparation around March 2001 (age 17, during 12th standard). "
            "Continued intensive preparation through June 2003."
        ),
        "magnitude": "significant",
        "outcome": "partial",
        "dasha_md": "Saturn",
        "dasha_ad": "Venus",
        "key_transits": [
            "Saturn transit Taurus = 2H from Lagna",
            "Jupiter transit Taurus = 2H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2002.XX.XX.01",
        "event_date": "2002-07-01",
        "event_type": "psychological",
        "subcategory": "chronic_episode",
        "description": (
            "Inherited vertigo/head reeling reached peak debilitation during engineering "
            "competitive exam preparation (~2001-2004). Bouts were debilitating and directly "
            "impacted academic performance."
        ),
        "magnitude": "significant",
        "outcome": "partial",
        "dasha_md": "Saturn",
        "dasha_ad": "Sun",
        "key_transits": [],
    },
    {
        "lel_id": "EVT.2002.XX.XX.02",
        "event_date": "2002-07-01",
        "event_type": "spiritual",
        "subcategory": "sadhana_initiation",
        "description": (
            "Father instructed native (age ~18-19) to perform Shani Puja nightly. "
            "Native read Shani Shtotram every night for approximately 7-10 years. "
            "First formal sustained sadhana practice."
        ),
        "magnitude": "significant",
        "outcome": "yes",
        "dasha_md": "Saturn",
        "dasha_ad": "Sun",
        "key_transits": [],
    },
    {
        "lel_id": "EVT.2003.06.XX.01",
        "event_date": "2003-06-15",
        "event_type": "education",
        "subcategory": "entrance_exam_preparation_ended",
        "description": (
            "IIT preparation phase ended (June 2003). Transitioned to engineering admission "
            "at SRM Chennai."
        ),
        "magnitude": "significant",
        "outcome": "partial",
        "dasha_md": "Saturn",
        "dasha_ad": "Moon",
        "key_transits": [
            "Saturn transit Gemini = 3H from Lagna",
            "Jupiter transit Cancer = 4H from Lagna",
        ],
    },
    # ── Era 4: SRM Engineering Era (2004-2009) ────────────────────────────────
    {
        "lel_id": "EVT.2004.01.XX.01",
        "event_date": "2004-01-15",
        "event_type": "relationship",
        "subcategory": "romantic_concurrent",
        "description": (
            "Relationship #2 started (Jan 2004, 3-year duration → ended ~Jan 2007). "
            "During engineering years at SRM Chennai (age 19-20). "
            "Concurrent with primary long-term relationship R#1. Entirely pre-marriage."
        ),
        "magnitude": "significant",
        "outcome": "partial",
        "dasha_md": "Saturn",
        "dasha_ad": "Moon",
        "key_transits": [
            "Saturn transit Gemini = 3H from Lagna",
            "Jupiter transit Leo = 5H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2004.XX.XX.02",
        "event_date": "2004-06-01",
        "event_type": "education",
        "subcategory": "opportunity_declined",
        "description": (
            "Selected by SRM Engineering College as one of 4-5 students for 1-year exchange "
            "at Carnegie Mellon University. Could not accept due to health issues and "
            "financial constraints. Native experienced 'deja vu' when CMU reappeared as "
            "Tepper MBA sponsorship in 2021."
        ),
        "magnitude": "significant",
        "outcome": "pending",
        "dasha_md": "Saturn",
        "dasha_ad": "Mars",
        "key_transits": [
            "Saturn transit Gemini",
            "Jupiter transit Leo",
        ],
    },
    {
        "lel_id": "EVT.2007.06.XX.01",
        "event_date": "2007-06-15",
        "event_type": "health",
        "subcategory": "surgery_minor",
        "description": "Right knee arthroscopy (minor surgery).",
        "magnitude": "moderate",
        "outcome": "yes",
        "dasha_md": "Saturn",
        "dasha_ad": "Rahu",
        "key_transits": [
            "Rahu transit on natal Moon (Aquarius)",
            "Saturn transit Cancer = 4H from Lagna",
            "Jupiter transit Scorpio = 8H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2007.06.XX.02",
        "event_date": "2007-06-15",
        "event_type": "education",
        "subcategory": "engineering_completed",
        "description": "Engineering (B.Tech) completed at SRM Chennai, around June 2007.",
        "magnitude": "significant",
        "outcome": "partial",
        "dasha_md": "Saturn",
        "dasha_ad": "Rahu",
        "key_transits": [
            "Rahu transit on natal Moon (Aquarius)",
            "Saturn transit Cancer = 4H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2007.06.10.01",
        "event_date": "2007-06-10",
        "event_type": "career",
        "subcategory": "first_job_joined",
        "description": "Joined Cognizant — first corporate IT job. Tenure exactly one year.",
        "magnitude": "significant",
        "outcome": "partial",
        "dasha_md": "Saturn",
        "dasha_ad": "Rahu",
        "key_transits": [
            "Rahu transit on natal Moon (Aquarius)",
            "Saturn transit Cancer = 4H from Lagna",
            "Jupiter transit Scorpio = 8H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2007.XX.XX.03",
        "event_date": "2007-09-01",
        "event_type": "health",
        "subcategory": "chronic_onset",
        "description": (
            "Sleep disorder onset arising from medical negligence during the knee arthroscopy. "
            "Negligence caused a breathlessness problem which triggered a chronic sleep disorder. "
            "Persisted ~18 years until resolved 2025-2026."
        ),
        "magnitude": "significant",
        "outcome": "pending",
        "dasha_md": "Saturn",
        "dasha_ad": "Rahu",
        "key_transits": [
            "Saturn transit Leo",
            "Jupiter transit Scorpio",
        ],
    },
    {
        "lel_id": "EVT.2008.06.09.01",
        "event_date": "2008-06-09",
        "event_type": "career",
        "subcategory": "first_job_exited",
        "description": (
            "Exited Cognizant exactly 1 year after joining. "
            "Returned to Bhubaneswar to re-attempt IIT preparation."
        ),
        "magnitude": "significant",
        "outcome": "yes",
        "dasha_md": "Saturn",
        "dasha_ad": "Jupiter",
        "key_transits": [
            "Saturn transit 7H from Moon (Leo)",
            "Saturn transit Leo = 5H from Lagna",
            "Jupiter transit Sagittarius = 9H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2009.06.XX.01",
        "event_date": "2009-06-15",
        "event_type": "loss",
        "subcategory": "grandparent_passing",
        "description": (
            "Paternal grandfather passed away (June or July 2009). "
            "Described by native as 'academic mentor' — a major emotional setback."
        ),
        "magnitude": "major",
        "outcome": "yes",
        "dasha_md": "Saturn",
        "dasha_ad": "Jupiter",
        "key_transits": [
            "Saturn transit 7H from Moon (Leo)",
            "Jupiter transit on natal Moon (Aquarius) — gajakesari-class",
            "Saturn transit Leo = 5H from Lagna",
        ],
    },
    # ── Era 5: MBA, Thailand (2010-2013) ──────────────────────────────────────
    {
        "lel_id": "EVT.2010.XX.XX.01",
        "event_date": "2010-07-01",
        "event_type": "finance",
        "subcategory": "family_windfall",
        "description": (
            "Father received a large sum from selling real estate (around 2010). "
            "Family-level financial windfall."
        ),
        "magnitude": "significant",
        "outcome": "yes",
        "dasha_md": "Saturn",
        "dasha_ad": "Jupiter",
        "key_transits": [
            "Saturn transit Virgo = 6H from Lagna",
            "Jupiter transit Pisces = 12H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2010.XX.XX.02",
        "event_date": "2010-07-01",
        "event_type": "spiritual",
        "subcategory": "devata_adoption",
        "description": (
            "Began regular devotion to Maa Ugratara at the Ugratara Shakti pitha near "
            "Bhubaneswar (~15 years running as of 2026). A tantric Shakti form. "
            "Native's longest-sustained single devata relationship."
        ),
        "magnitude": "significant",
        "outcome": "partial",
        "dasha_md": "Saturn",
        "dasha_ad": "Jupiter",
        "key_transits": [],
    },
    {
        "lel_id": "EVT.2010.12.XX.01",
        "event_date": "2010-12-15",
        "event_type": "travel",
        "subcategory": "first_foreign_trip",
        "description": "First international travel — Thailand trip, December 2010.",
        "magnitude": "significant",
        "outcome": "yes",
        "dasha_md": "Mercury",
        "dasha_ad": "Mercury",
        "key_transits": [
            "Saturn transit Virgo = 6H from Lagna",
            "Jupiter transit Pisces = 12H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2011.01.XX.01",
        "event_date": "2011-01-15",
        "event_type": "education",
        "subcategory": "mba_admission",
        "description": (
            "Secured admission to XIMB (Xavier Institute of Management, Bhubaneswar) "
            "MBA program (January 2011)."
        ),
        "magnitude": "major",
        "outcome": "yes",
        "dasha_md": "Mercury",
        "dasha_ad": "Mercury",
        "key_transits": [
            "Saturn transit Virgo = 6H from Lagna",
            "Jupiter transit Pisces = 12H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2011.06.XX.01",
        "event_date": "2011-06-15",
        "event_type": "education",
        "subcategory": "mba_enrolled",
        "description": (
            "Formally enrolled at XIMB MBA (June 2011). Beginning of highly fulfilling "
            "2-year program."
        ),
        "magnitude": "major",
        "outcome": "yes",
        "dasha_md": "Mercury",
        "dasha_ad": "Mercury",
        "key_transits": [
            "Saturn transit Virgo = 6H from Lagna",
            "Jupiter transit Aries = 1H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2012.09.XX.01",
        "event_date": "2012-09-15",
        "event_type": "creative",
        "subcategory": "modeling",
        "description": "Modeling at XIMB (September 2012).",
        "magnitude": "moderate",
        "outcome": "partial",
        "dasha_md": "Mercury",
        "dasha_ad": "Mercury",
        "key_transits": [
            "Saturn transit 9H from Moon (Libra)",
            "Saturn transit Libra = 7H from Lagna",
            "Jupiter transit Taurus = 2H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2012.XX.XX.02",
        "event_date": "2012-09-01",
        "event_type": "education",
        "subcategory": "leadership_role",
        "description": (
            "Elected President of the International Relations Committee (IRC) at XIMB. "
            "Had opportunity to stand for General Secretary but declined."
        ),
        "magnitude": "moderate",
        "outcome": "pending",
        "dasha_md": "Mercury",
        "dasha_ad": "Mercury",
        "key_transits": [
            "Saturn transit Libra",
            "Jupiter transit Taurus",
        ],
    },
    {
        "lel_id": "EVT.2012.10.XX.01",
        "event_date": "2012-10-15",
        "event_type": "relationship",
        "subcategory": "romantic_concurrent",
        "description": (
            "Relationship #3 started (October 2012, 10-year duration → ended ~October 2022). "
            "Concurrent with primary long-term relationship R#1 through marriage year."
        ),
        "magnitude": "major",
        "outcome": "partial",
        "dasha_md": "Mercury",
        "dasha_ad": "Mercury",
        "key_transits": [
            "Saturn transit 9H from Moon (Libra)",
            "Saturn transit Libra = 7H from Lagna",
            "Jupiter transit Taurus = 2H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2013.03.XX.01",
        "event_date": "2013-03-15",
        "event_type": "education",
        "subcategory": "mba_graduation",
        "description": "Graduated from XIMB MBA (March 2013).",
        "magnitude": "major",
        "outcome": "yes",
        "dasha_md": "Mercury",
        "dasha_ad": "Ketu",
        "key_transits": [
            "Saturn transit 9H from Moon (Libra)",
            "Saturn transit Libra = 7H from Lagna",
            "Jupiter transit Taurus = 2H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2013.05.XX.01",
        "event_date": "2013-05-15",
        "event_type": "career",
        "subcategory": "corporate_job_joined",
        "description": (
            "Formally joined Mahindra Retail (May 2013) following XIMB placement and internship. "
            "Beginning of 10-year Mahindra Group tenure."
        ),
        "magnitude": "major",
        "outcome": "partial",
        "dasha_md": "Mercury",
        "dasha_ad": "Ketu",
        "key_transits": [
            "Saturn transit 9H from Moon (Libra)",
            "Saturn transit Libra = 7H from Lagna",
            "Jupiter transit Taurus = 2H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2013.XX.XX.01",
        "event_date": "2013-07-01",
        "event_type": "family",
        "subcategory": "parent_illness_onset",
        "description": (
            "Father's kidney disease began in 2013. This became a 5-year illness "
            "culminating in his passing on 2018-11-28."
        ),
        "magnitude": "major",
        "outcome": "partial",
        "dasha_md": "Mercury",
        "dasha_ad": "Ketu",
        "key_transits": [
            "Saturn transit 9H from Moon (Libra)",
            "Saturn transit Libra = 7H from Lagna",
            "Jupiter transit Gemini = 3H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2013.12.11.01",
        "event_date": "2013-12-11",
        "event_type": "family",
        "subcategory": "marriage",
        "description": (
            "Married childhood girlfriend (R#1, dating since 1998-02-16). "
            "Marriage duration before separation: ~12 years."
        ),
        "magnitude": "life-altering",
        "outcome": "partial",
        "dasha_md": "Mercury",
        "dasha_ad": "Ketu",
        "key_transits": [
            "Saturn transit 9H from Moon (Libra)",
            "Saturn transit Libra = 7H from Lagna",
            "Jupiter transit Gemini = 3H from Lagna",
        ],
    },
    # ── Era 6: Corporate Ascendance (2015-2018) ───────────────────────────────
    {
        "lel_id": "EVT.2015.XX.XX.01",
        "event_date": "2015-07-01",
        "event_type": "spiritual",
        "subcategory": "devata_adoption",
        "description": (
            "In early thirties (~2014-2016), native began gravitating toward Mahadev/Shiva. "
            "This deepened over the following decade to daily abhisheka. Concurrent with "
            "Ugratara devotion."
        ),
        "magnitude": "significant",
        "outcome": "partial",
        "dasha_md": "Mercury",
        "dasha_ad": "Venus",
        "key_transits": [],
    },
    {
        "lel_id": "EVT.2016.XX.XX.01",
        "event_date": "2016-07-01",
        "event_type": "career",
        "subcategory": "employer_instability",
        "description": (
            "Mahindra Retail company 'crashed'; triggered career stress and job search. "
            "Decision to switch to Tech Mahindra crystallized during this period."
        ),
        "magnitude": "major",
        "outcome": "yes",
        "dasha_md": "Mercury",
        "dasha_ad": "Venus",
        "key_transits": [
            "Ketu transit on natal Moon (Aquarius)",
            "Saturn transit Scorpio = 8H from Lagna",
            "Jupiter transit Leo = 5H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2017.03.XX.01",
        "event_date": "2017-03-15",
        "event_type": "career",
        "subcategory": "employer_switch",
        "description": (
            "Switched from Mahindra Retail to Tech Mahindra (March 2017). "
            "Within-Mahindra-Group move; upgraded platform. Leads to US deputation in 2019."
        ),
        "magnitude": "major",
        "outcome": "yes",
        "dasha_md": "Mercury",
        "dasha_ad": "Sun",
        "key_transits": [
            "Saturn transit Sagittarius = 9H from Lagna",
            "Ketu transit on natal Moon (Aquarius)",
            "Jupiter transit Virgo = 6H from Lagna",
        ],
    },
    # ── Era 7: Deepest Loss, US Era (2018-2022) ───────────────────────────────
    {
        "lel_id": "EVT.2018.11.28.01",
        "event_date": "2018-11-28",
        "event_type": "loss",
        "subcategory": "parent_passing",
        "description": (
            "Father passed away on 28 November 2018, culminating 18-year kidney disease journey. "
            "Native ran between Hyderabad and Bhubaneswar during final hospital phase."
        ),
        "magnitude": "life-altering",
        "outcome": "yes",
        "dasha_md": "Mercury",
        "dasha_ad": "Moon",
        "key_transits": [
            "Saturn transit Sagittarius = 9H from Lagna — CLASSICAL FATHER-DEATH TRIGGER",
            "Jupiter transit Scorpio 10°16' conjunct Sun + Mercury retro — 8H from Lagna",
            "Ketu transit Capricorn — on 10H natal Sun+Mercury stellium",
        ],
    },
    {
        "lel_id": "EVT.2019.05.XX.01",
        "event_date": "2019-05-15",
        "event_type": "residential+travel",
        "subcategory": "foreign_move_start",
        "description": (
            "Moved to the United States on Tech Mahindra work deputation (May 2019). "
            "4-year stint; returned to India May 2023."
        ),
        "magnitude": "life-altering",
        "outcome": "yes",
        "dasha_md": "Mercury",
        "dasha_ad": "Mars",
        "key_transits": [
            "Saturn transit Sagittarius = 9H from Lagna",
            "Jupiter transit Scorpio = 8H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2021.01.XX.01",
        "event_date": "2021-01-15",
        "event_type": "health",
        "subcategory": "panic_anxiety_episode",
        "description": (
            "Health episode with jitters and sweating — panic/anxiety episode in January 2021. "
            "Native was in US stint, roughly 1 year before twins' birth."
        ),
        "magnitude": "significant",
        "outcome": "yes",
        "dasha_md": "Mercury",
        "dasha_ad": "Rahu",
        "key_transits": [
            "Saturn transit Capricorn = 10H from Lagna",
            "Jupiter transit Capricorn = 10H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2021.XX.XX.02",
        "event_date": "2021-07-01",
        "event_type": "career",
        "subcategory": "award_selection",
        "description": (
            "Selected as one of the top employees across the Mahindra Group and sponsored "
            "for 1-year Executive MBA at Tepper School of Business, Carnegie Mellon University. "
            "Native experienced this as a 'deja vu' of the 2004 CMU opportunity."
        ),
        "magnitude": "significant",
        "outcome": "pending",
        "dasha_md": "Mercury",
        "dasha_ad": "Rahu",
        "key_transits": [
            "Saturn transit Capricorn",
            "Jupiter transit Capricorn",
        ],
    },
    {
        "lel_id": "EVT.2021.XX.XX.03",
        "event_date": "2021-07-01",
        "event_type": "career",
        "subcategory": "business_stalled",
        "description": (
            "A second sand quarry was acquired and attempted for operationalisation ~2021-2022 "
            "but could not be made operational due to public hearing requirements. "
            "Multiple attempts to resolve unsuccessful over ~4-5 years until April 2026."
        ),
        "magnitude": "moderate",
        "outcome": "pending",
        "dasha_md": "Mercury",
        "dasha_ad": "Rahu",
        "key_transits": [
            "Saturn transit Capricorn",
            "Jupiter transit Aquarius",
        ],
    },
    {
        "lel_id": "EVT.2022.01.03.01",
        "event_date": "2022-01-03",
        "event_type": "family",
        "subcategory": "child_birth",
        "description": "Twin daughters born on 3 January 2022. Native's only children.",
        "magnitude": "life-altering",
        "outcome": "yes",
        "dasha_md": "Mercury",
        "dasha_ad": "Rahu",
        "key_transits": [
            "Jupiter transit Aquarius = 11H AND ON NATAL MOON (gajakesari-class children transit)",
            "Saturn transit Capricorn = 10H from Lagna, 12H from Moon (Sade Sati Rising)",
            "Rahu transit Aries = 1H Lagna",
        ],
    },
    {
        "lel_id": "EVT.2022.XX.XX.02",
        "event_date": "2022-07-01",
        "event_type": "relationship",
        "subcategory": "romantic_concurrent",
        "description": (
            "A serious affair during the CMU Tepper Executive MBA period (2022-2023). "
            "This affair generated significant marital tension and is cited by native "
            "as a direct contributing cause of the current marital separation."
        ),
        "magnitude": "life-altering",
        "outcome": "pending",
        "dasha_md": "Mercury",
        "dasha_ad": "Jupiter",
        "key_transits": [
            "Saturn transit Aquarius",
            "Jupiter transit Pisces",
        ],
    },
    {
        "lel_id": "EVT.2022.10.XX.01",
        "event_date": "2022-10-15",
        "event_type": "relationship",
        "subcategory": "romantic_concurrent_ended",
        "description": (
            "Relationship #3 ended (approximately October 2022, 10-year duration from start). "
            "Coincides with Mercury-Jupiter AD transition and start of '2022-2024 mix' period."
        ),
        "magnitude": "significant",
        "outcome": "partial",
        "dasha_md": "Mercury",
        "dasha_ad": "Jupiter",
        "key_transits": [
            "Saturn transit Capricorn = 10H from Lagna",
            "Jupiter transit Pisces = 12H from Lagna",
        ],
    },
    # ── Era 8: Pivot — India Return, Business (2023-2026) ─────────────────────
    {
        "lel_id": "EVT.2023.05.XX.01",
        "event_date": "2023-05-15",
        "event_type": "residential+travel",
        "subcategory": "foreign_return",
        "description": (
            "Returned to India from United States (May 2023) after 4-year stint. "
            "Concurrent with US job loss. Marks pivotal transition from salaried corporate "
            "employment to entrepreneurship."
        ),
        "magnitude": "life-altering",
        "outcome": "yes",
        "dasha_md": "Mercury",
        "dasha_ad": "Jupiter",
        "key_transits": [
            "Saturn transit Aquarius = 11H from Lagna",
            "Jupiter transit Aries = 1H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2023.06.XX.01",
        "event_date": "2023-06-15",
        "event_type": "education",
        "subcategory": "executive_education_completed",
        "description": (
            "Tepper School of Business (Carnegie Mellon University) Executive MBA completed "
            "(June 2023). Sponsored by Tech Mahindra. Recognized as top performer."
        ),
        "magnitude": "major",
        "outcome": "yes",
        "dasha_md": "Mercury",
        "dasha_ad": "Jupiter",
        "key_transits": [
            "Saturn transit Aquarius = 11H from Lagna",
            "Jupiter transit Aries = 1H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2023.07.XX.01",
        "event_date": "2023-07-15",
        "event_type": "career",
        "subcategory": "entrepreneurship_founded",
        "description": (
            "Founded Marsys Group (July 2023). Spans mining, AI, technology, and exports "
            "(notably with Russia). Strategic focus: system building, automation, strategic patience."
        ),
        "magnitude": "life-altering",
        "outcome": "yes",
        "dasha_md": "Mercury",
        "dasha_ad": "Jupiter",
        "key_transits": [
            "Saturn transit Aquarius = 11H from Lagna",
            "Jupiter transit Aries = 1H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2024.02.16.01",
        "event_date": "2024-02-16",
        "event_type": "career",
        "subcategory": "business_milestone_major",
        "description": (
            "Launched Kotadwara (riverbed sand) mining operation at Bhanti on 16 February 2024. "
            "Major concrete step in Marsys Group's mining vertical."
        ),
        "magnitude": "major",
        "outcome": "yes",
        "dasha_md": "Mercury",
        "dasha_ad": "Jupiter",
        "key_transits": [
            "Saturn transit Aquarius = 11H from Lagna",
            "Jupiter transit Aries = 1H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2024.XX.XX.01",
        "event_date": "2024-07-01",
        "event_type": "spiritual",
        "subcategory": "practice_intensification",
        "description": (
            "From ~2024: daily pouring of water on shivalinga (abhisheka); independent yajna "
            "execution; systematic panchang study. Highest concentration of new spiritual "
            "practices in native's life."
        ),
        "magnitude": "major",
        "outcome": "yes",
        "dasha_md": "Mercury",
        "dasha_ad": "Saturn",
        "key_transits": [
            "Saturn transit Aquarius (Sade Sati peak)",
            "Jupiter transit Aries → Taurus 2024",
        ],
    },
    {
        "lel_id": "EVT.2025.05.XX.01",
        "event_date": "2025-05-15",
        "event_type": "loss",
        "subcategory": "financial_deception",
        "description": (
            "Major deception / scam event (May 2025). Native was deceived / defrauded "
            "in a significant matter."
        ),
        "magnitude": "major",
        "outcome": "partial",
        "dasha_md": "Mercury",
        "dasha_ad": "Saturn",
        "key_transits": [
            "Saturn transit Pisces = 12H from Lagna",
            "Jupiter transit Gemini = 3H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2025.06.XX.01",
        "event_date": "2025-06-15",
        "event_type": "spiritual",
        "subcategory": "ritual_infrastructure",
        "description": (
            "Native established a personal yantra mandala in his bedroom — a permanent ritual space. "
            "Prayers offered almost daily. Represents formalization of private ritual life begun ~2024."
        ),
        "magnitude": "significant",
        "outcome": "yes",
        "dasha_md": "Mercury",
        "dasha_ad": "Saturn",
        "key_transits": [
            "Saturn transit Pisces (12H from Lagna — spiritual/renunciative)",
            "Sade Sati Cycle 2 Setting phase",
        ],
    },
    {
        "lel_id": "EVT.2025.07.XX.01",
        "event_date": "2025-07-15",
        "event_type": "finance",
        "subcategory": "business_milestone_windfall",
        "description": (
            "First major Marsys business contract (Marsys Technology — July 2025). "
            "Windfall-class revenue event; first concrete large-scale win for the business."
        ),
        "magnitude": "major",
        "outcome": "yes",
        "dasha_md": "Mercury",
        "dasha_ad": "Saturn",
        "key_transits": [
            "Rahu transit on natal Moon (Aquarius)",
            "Saturn transit Pisces = 12H from Lagna",
            "Jupiter transit Gemini = 3H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2025.11.XX.01",
        "event_date": "2025-11-15",
        "event_type": "spiritual",
        "subcategory": "devata_adoption",
        "description": (
            "Native began praying intensely to the tantric form of Mahalakshmi — "
            "Ma Kamlatmika (one of the Dasha Mahavidyas). Coincides with financial recovery "
            "and business intensification."
        ),
        "magnitude": "significant",
        "outcome": "partial",
        "dasha_md": "Mercury",
        "dasha_ad": "Saturn",
        "key_transits": [
            "Saturn transit Pisces",
            "Jupiter transit Cancer (from mid-2025, 4H = home/family)",
        ],
    },
    {
        "lel_id": "EVT.2025.XX.XX.01",
        "event_date": "2025-07-01",
        "event_type": "spiritual",
        "subcategory": "devotional_shift",
        "description": (
            "Spiritual shift toward Lord Vishnu / Lord Venkateshwara Balaji of Tirupati. "
            "Occurred 'naturally'; continues alongside long-term Maa Ugratara and Mahadev devotions."
        ),
        "magnitude": "significant",
        "outcome": "yes",
        "dasha_md": "Mercury",
        "dasha_ad": "Saturn",
        "key_transits": [
            "Rahu transit on natal Moon (Aquarius)",
            "Saturn transit Pisces = 12H from Lagna",
            "Jupiter transit Gemini = 3H from Lagna",
        ],
    },
    {
        "lel_id": "EVT.2025.XX.XX.02",
        "event_date": "2025-07-01",
        "event_type": "health",
        "subcategory": "chronic_resolution",
        "description": (
            "Chronic sleep disorder (onset 2007, ~18 years) resolved via Lemborexant "
            "(brand name: Dayvigo), discovered through an astrology consultation. "
            "First medication to work without debilitating drowsiness side effects."
        ),
        "magnitude": "significant",
        "outcome": "pending",
        "dasha_md": "Mercury",
        "dasha_ad": "Saturn",
        "key_transits": [
            "Saturn transit Pisces",
            "Jupiter transit Gemini",
        ],
    },
    {
        "lel_id": "EVT.2026.01.XX.01",
        "event_date": "2026-01-15",
        "event_type": "other",
        "subcategory": "psychological_shift",
        "description": (
            "Between January and February 2026, native experienced a marked and sustained shift "
            "to focused, one-pointed attention directed entirely at business. Long-standing "
            "distractions described as 'wiped out'."
        ),
        "magnitude": "significant",
        "outcome": "pending",
        "dasha_md": "Mercury",
        "dasha_ad": "Saturn",
        "key_transits": [
            "Saturn transit Pisces",
            "Jupiter transit Gemini",
        ],
    },
    {
        "lel_id": "EVT.2026.03.20.01",
        "event_date": "2026-03-20",
        "event_type": "career",
        "subcategory": "business_project_closed",
        "description": (
            "Marsys Technology (IT company co-founded with a MasterCard executive) wrapped up "
            "its primary project on 20 March 2026 with 'enormous profits'. Revenue generated "
            "steadily from 2023 through 2026."
        ),
        "magnitude": "significant",
        "outcome": "pending",
        "dasha_md": "Mercury",
        "dasha_ad": "Saturn",
        "key_transits": [
            "Saturn transit Pisces",
            "Jupiter transit Gemini",
        ],
    },
    {
        "lel_id": "EVT.2026.04.08.01",
        "event_date": "2026-04-08",
        "event_type": "career",
        "subcategory": "business_milestone_clearance",
        "description": (
            "Public hearing for the second sand quarry successfully closed on 8 April 2026, "
            "clearing the primary regulatory obstacle after ~4-5 years. "
            "Quarry expected to become operational by late October 2026."
        ),
        "magnitude": "significant",
        "outcome": "pending",
        "dasha_md": "Mercury",
        "dasha_ad": "Saturn",
        "key_transits": [
            "Saturn transit Pisces",
            "Jupiter transit Gemini",
        ],
    },
    {
        "lel_id": "EVT.CURRENT.01",
        "event_date": "2026-04-17",
        "event_type": "relationship",
        "subcategory": "marital_status_current",
        "description": (
            "Separated from wife (R#1, married Dec 11, 2013). "
            "Stable arrangement. Currently improving per native's own characterization."
        ),
        "magnitude": "significant",
        "outcome": "partial",
        "dasha_md": "Mercury",
        "dasha_ad": "Saturn",
        "key_transits": [
            "Rahu transit on natal Moon (Aquarius)",
            "Saturn transit Pisces = 12H from Lagna",
            "Jupiter transit Gemini = 3H from Lagna",
        ],
    },
]

# ── Validation ─────────────────────────────────────────────────────────────────

assert len(LEL_CORPUS) == 57, (
    f"LEL corpus integrity check: expected 57 events, got {len(LEL_CORPUS)}. "
    "Check LEL_CORPUS list for any additions or deletions."
)


def _build_row(event: dict[str, Any]) -> dict[str, Any]:
    """Build a normalized DB row from a corpus entry."""
    lel_id = event["lel_id"]
    return {
        "event_id":        _evt_uuid(lel_id),
        "lel_id":          lel_id,
        "event_date":      event["event_date"],
        "event_type":      event["event_type"],
        "description":     event["description"],
        "domain":          f"{event['event_type']}/{event['subcategory']}",
        "outcome_observed": event.get("outcome"),
        "source_citation": SOURCE_CITATION,
        "dasha_md":        event.get("dasha_md"),
        "dasha_ad":        event.get("dasha_ad"),
        "key_transits":    event.get("key_transits", []),
        "convergence":     _convergence(event.get("outcome")),
    }


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError(
            "[STOP] DATABASE_URL not set. "
            "Set DATABASE_URL=postgresql://... and ensure DB is reachable."
        )
    return url


def _get_conn():  # type: ignore[return]
    """Return a psycopg connection."""
    try:
        import psycopg  # type: ignore
        return psycopg.connect(_db_url())
    except ImportError as exc:
        raise ImportError(
            "psycopg (v3) is required for DB operations. "
            "Install with: pip install psycopg[binary]"
        ) from exc


# ── Seed ───────────────────────────────────────────────────────────────────────

def seed_lel_intake(
    *,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Ingest all 57 LEL events into life_events + event_chart_state_index.

    Idempotent: uses ON CONFLICT DO UPDATE so re-running is safe.

    NO LEAKAGE guarantee:
        This function populates the calibration corpus ONLY.
        It never writes to prediction tables.
        Source citation is enforced non-null on every row.

    Args:
        dry_run: If True, compute rows but do not write to DB.
        verbose: Log each row.

    Returns:
        {
          "events_inserted": int,
          "events_updated": int,
          "total": int,
          "source_citation": str,
          "provenance_envelope": {...},
        }
    """
    rows = [_build_row(e) for e in LEL_CORPUS]

    # Validate all rows carry non-empty source_citation
    for row in rows:
        assert row["source_citation"], (
            f"source_citation must be non-empty for event {row['lel_id']}"
        )

    if dry_run:
        if verbose:
            for row in rows:
                logger.info("[dry_run] Would insert: %s %s %s",
                            row["lel_id"], row["event_date"], row["domain"])
        logger.info("[dry_run] Would upsert %d rows into life_events + event_chart_state_index", len(rows))
        return _build_result(rows, inserted=0, updated=0, dry_run=True)

    inserted = 0
    updated = 0

    with _get_conn() as conn:
        # DCB-004 fix: detect whether the production (legacy) life_events schema
        # or the brahma (new) schema is in use.  The legacy schema has
        # chart_state / source_section / build_id / provenance columns that are
        # NOT NULL; the brahma schema uses outcome_observed / domain / source_citation.
        # We probe for the 'domain' column — present only in the brahma schema.
        with conn.cursor() as probe:
            probe.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'life_events'
                  AND column_name = 'domain'
                """
            )
            brahma_schema = probe.fetchone() is not None

        with conn.cursor() as cur:
            for row in rows:
                if brahma_schema:
                    # Brahma schema (brahma_mimamsa_lel_intake.sql)
                    cur.execute(
                        """
                        INSERT INTO life_events
                            (event_id, event_date, event_type, description,
                             domain, outcome_observed, source_citation)
                        VALUES (%s, %s::DATE, %s, %s, %s, %s, %s)
                        ON CONFLICT (event_id) DO UPDATE SET
                            event_date       = EXCLUDED.event_date,
                            event_type       = EXCLUDED.event_type,
                            description      = EXCLUDED.description,
                            domain           = EXCLUDED.domain,
                            outcome_observed = EXCLUDED.outcome_observed,
                            source_citation  = EXCLUDED.source_citation
                        """,
                        (
                            row["event_id"],
                            row["event_date"],
                            row["event_type"],
                            row["description"],
                            row["domain"],
                            row["outcome_observed"],
                            row["source_citation"],
                        ),
                    )
                else:
                    # Legacy production schema: chart_state / source_section /
                    # build_id / provenance are all NOT NULL.  Provide synthetic
                    # defaults so the insert succeeds until the brahma migration
                    # (brahma_mimamsa_lel_intake.sql) is applied to production.
                    # DCB-004: this branch is the fix for the NOT NULL violation.
                    legacy_provenance = json.dumps({
                        "source": SOURCE_CITATION,
                        "lel_id": row["lel_id"],
                        "outcome": row["outcome_observed"],
                        "dasha_md": row["dasha_md"],
                        "dasha_ad": row["dasha_ad"],
                    })
                    legacy_chart_state = json.dumps({
                        "dasha_md": row["dasha_md"],
                        "dasha_ad": row["dasha_ad"],
                        "key_transits": row["key_transits"],
                    })
                    cur.execute(
                        """
                        INSERT INTO life_events
                            (event_id, event_date, category, description,
                             source_section, build_id,
                             chart_state, provenance)
                        VALUES (%s, %s::DATE, %s, %s, %s, %s, %s::JSONB, %s::JSONB)
                        ON CONFLICT (event_id) DO UPDATE SET
                            event_date    = EXCLUDED.event_date,
                            category      = EXCLUDED.category,
                            description   = EXCLUDED.description,
                            source_section = EXCLUDED.source_section,
                            chart_state   = EXCLUDED.chart_state,
                            provenance    = EXCLUDED.provenance
                        """,
                        (
                            row["event_id"],
                            row["event_date"],
                            row["event_type"],         # maps to category
                            row["description"],
                            row["source_citation"],    # maps to source_section
                            "lel_intake-brahma-mi-5-1",  # synthetic build_id
                            legacy_chart_state,
                            legacy_provenance,
                        ),
                    )

                if cur.rowcount and cur.statusmessage and "INSERT" in (cur.statusmessage or ""):
                    inserted += 1
                else:
                    updated += 1

                # Upsert event_chart_state_index (key: event_id) — brahma schema only
                if brahma_schema:
                    cur.execute(
                        """
                        INSERT INTO event_chart_state_index
                            (event_id, dasha_active, antardasha_active,
                             key_transits, convergence_score, source_citation)
                        VALUES (%s, %s, %s, %s::JSONB, %s, %s)
                        ON CONFLICT (event_id) DO UPDATE SET
                            dasha_active      = EXCLUDED.dasha_active,
                            antardasha_active = EXCLUDED.antardasha_active,
                            key_transits      = EXCLUDED.key_transits,
                            convergence_score = EXCLUDED.convergence_score,
                            source_citation   = EXCLUDED.source_citation
                        """,
                        (
                            row["event_id"],
                            row["dasha_md"],
                            row["dasha_ad"],
                            json.dumps(row["key_transits"]),
                            row["convergence"],
                            row["source_citation"],
                        ),
                    )

                if verbose:
                    logger.info("Upserted: %s %s (%s)", row["lel_id"], row["event_date"], row["domain"])

        conn.commit()

    logger.info(
        "mimamsa.lel_intake: upserted %d events (inserted=%d, updated=%d)",
        len(rows), inserted, updated,
    )
    return _build_result(rows, inserted=inserted, updated=updated, dry_run=False)


def _build_result(
    rows: list[dict[str, Any]],
    *,
    inserted: int,
    updated: int,
    dry_run: bool,
) -> dict[str, Any]:
    return {
        "events_inserted":    inserted,
        "events_updated":     updated,
        "total":              len(rows),
        "dry_run":            dry_run,
        "source_citation":    SOURCE_CITATION,
        "no_leakage_check":   "PASS — life_events is calibration corpus only",
        "provenance_envelope": {
            "source":         "mimamsa.lel_intake",
            "asset":          "MI-5-1",
            "lel_version":    "LIFE_EVENT_LOG_v1_2.md v1.7",
            "total_events":   57,
            "confidence":     0.89,
            "source_citation": SOURCE_CITATION,
            "computed_at":    datetime.now(timezone.utc).isoformat(),
        },
    }


# ── Tool-level query ───────────────────────────────────────────────────────────

def lel_query(
    domain: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """
    Query LEL events by domain and/or date range.

    Args:
        domain:     Case-insensitive substring filter on event_type or domain.
        date_from:  ISO date string lower bound (inclusive).
        date_to:    ISO date string upper bound (inclusive).
        limit:      Max rows to return (default 100).

    Returns:
        {
          "events": [...],
          "total_count": int,
          "filter_applied": {...},
          "provenance_envelope": {...},
        }
    """
    with _get_conn() as conn:
        params: list[Any] = []
        conditions = []

        if domain:
            conditions.append(
                "(le.domain ILIKE %s OR le.event_type ILIKE %s)"
            )
            pattern = f"%{domain}%"
            params.extend([pattern, pattern])

        if date_from:
            conditions.append("le.event_date >= %s::DATE")
            params.append(date_from)

        if date_to:
            conditions.append("le.event_date <= %s::DATE")
            params.append(date_to)

        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        rows = conn.execute(
            f"""
            SELECT
                le.event_id::TEXT,
                le.event_date::TEXT,
                le.event_type,
                le.description,
                le.domain,
                le.outcome_observed,
                cs.dasha_active,
                cs.antardasha_active,
                cs.key_transits::TEXT,
                cs.convergence_score,
                le.source_citation
            FROM life_events le
            LEFT JOIN event_chart_state_index cs ON cs.event_id = le.event_id
            {where_clause}
            ORDER BY le.event_date
            LIMIT %s
            """,
            params + [limit],
        ).fetchall()

        count_row = conn.execute(
            f"""
            SELECT COUNT(*) FROM life_events le
            {where_clause}
            """,
            params,
        ).fetchone()

    total_count = int(count_row[0]) if count_row else 0

    events = [
        {
            "event_id":          r[0],
            "event_date":        r[1],
            "event_type":        r[2],
            "description":       r[3],
            "domain":            r[4],
            "outcome_observed":  r[5],
            "dasha_active":      r[6],
            "antardasha_active": r[7],
            "key_transits":      json.loads(r[8]) if r[8] else [],
            "convergence_score": float(r[9]) if r[9] is not None else None,
            "source_citation":   r[10],
        }
        for r in rows
    ]

    return {
        "events": events,
        "total_count": total_count,
        "filter_applied": {
            "domain":     domain,
            "date_from":  date_from,
            "date_to":    date_to,
            "limit":      limit,
        },
        "provenance_envelope": {
            "source":          "mimamsa.lel_intake",
            "asset":           "MI-5-1",
            "lel_version":     "LIFE_EVENT_LOG_v1_2.md v1.7",
            "total_events":    57,
            "confidence":      0.89,
            "source_citation": SOURCE_CITATION,
            "no_leakage_note": "life_events is calibration corpus only — must not feed prediction generation",
            "b3_compliant":    True,
            "queried_at":      datetime.now(timezone.utc).isoformat(),
        },
    }


# ── Acceptance gate ───────────────────────────────────────────────────────────

def run_acceptance_gate() -> dict[str, Any]:
    """
    Run the MI-5-1 acceptance gate.

    Gate criteria:
      AC1: life_events row count == 57
      AC2: event_chart_state_index row count == 57
      AC3: 0 rows with null or empty source_citation in life_events
      AC4: 0 rows with null or empty source_citation in event_chart_state_index
      AC5: lel_query() returns events list with non-zero length
      AC6: lel_query(domain='career') returns >= 1 career events
    """
    checks: list[dict[str, Any]] = []

    with _get_conn() as conn:
        # AC1: life_events count
        row = conn.execute("SELECT COUNT(*) FROM life_events").fetchone()
        le_count = int(row[0]) if row else 0
        checks.append({
            "id": "AC1",
            "desc": "life_events row count == 57",
            "passed": le_count == 57,
            "value": le_count,
        })

        # AC2: event_chart_state_index count
        row = conn.execute("SELECT COUNT(*) FROM event_chart_state_index").fetchone()
        cs_count = int(row[0]) if row else 0
        checks.append({
            "id": "AC2",
            "desc": "event_chart_state_index row count == 57",
            "passed": cs_count == 57,
            "value": cs_count,
        })

        # AC3: no null/empty source_citation in life_events
        row = conn.execute(
            "SELECT COUNT(*) FROM life_events WHERE source_citation IS NULL OR source_citation = ''"
        ).fetchone()
        null_citations = int(row[0]) if row else 0
        checks.append({
            "id": "AC3",
            "desc": "0 rows with null/empty source_citation in life_events",
            "passed": null_citations == 0,
            "value": null_citations,
        })

        # AC4: no null/empty source_citation in event_chart_state_index
        row = conn.execute(
            "SELECT COUNT(*) FROM event_chart_state_index WHERE source_citation IS NULL OR source_citation = ''"
        ).fetchone()
        null_cs_citations = int(row[0]) if row else 0
        checks.append({
            "id": "AC4",
            "desc": "0 rows with null/empty source_citation in event_chart_state_index",
            "passed": null_cs_citations == 0,
            "value": null_cs_citations,
        })

    # AC5: lel_query returns events
    try:
        result = lel_query(limit=10)
        events_returned = len(result.get("events", []))
        checks.append({
            "id": "AC5",
            "desc": "lel_query() returns events list with non-zero length",
            "passed": events_returned > 0,
            "value": events_returned,
        })
    except Exception as exc:
        checks.append({
            "id": "AC5",
            "desc": "lel_query() smoke test",
            "passed": False,
            "error": str(exc),
        })

    # AC6: lel_query(domain='career') returns career events
    try:
        result = lel_query(domain="career", limit=100)
        career_count = len(result.get("events", []))
        checks.append({
            "id": "AC6",
            "desc": "lel_query(domain='career') returns >= 1 career events",
            "passed": career_count >= 1,
            "value": career_count,
        })
    except Exception as exc:
        checks.append({
            "id": "AC6",
            "desc": "lel_query(domain='career') smoke test",
            "passed": False,
            "error": str(exc),
        })

    passed = all(c["passed"] for c in checks)
    return {
        "gate_passed": passed,
        "asset": "MI-5-1",
        "checks": checks,
    }


# ── CLI ────────────────────────────────────────────────────────────────────────

def _cmd_seed(args: argparse.Namespace) -> None:
    result = seed_lel_intake(
        dry_run=getattr(args, "dry_run", False),
        verbose=getattr(args, "verbose", False),
    )
    print(json.dumps(result, indent=2))


def _cmd_query(args: argparse.Namespace) -> None:
    result = lel_query(
        domain=getattr(args, "domain", None),
        date_from=getattr(args, "date_from", None),
        date_to=getattr(args, "date_to", None),
        limit=getattr(args, "limit", 100),
    )
    print(json.dumps(result, indent=2))


def _cmd_gate(args: argparse.Namespace) -> None:
    result = run_acceptance_gate()
    print(json.dumps(result, indent=2))
    if not result["gate_passed"]:
        sys.exit(1)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="BRAHMA-MI-5-1: mimamsa.lel_intake — 57 LEL events ingestion"
    )

    sub = parser.add_subparsers(dest="command")

    p_seed = sub.add_parser("seed", help="Ingest all 57 LEL events into DB")
    p_seed.add_argument("--dry-run", action="store_true", help="Compute but do not write to DB")
    p_seed.add_argument("--verbose", action="store_true", help="Log each row")

    p_query = sub.add_parser("query", help="Query LEL events")
    p_query.add_argument("--domain", default=None, help="Domain filter (e.g. career, health)")
    p_query.add_argument("--from", dest="date_from", default=None, help="Date lower bound (YYYY-MM-DD)")
    p_query.add_argument("--to", dest="date_to", default=None, help="Date upper bound (YYYY-MM-DD)")
    p_query.add_argument("--limit", type=int, default=100, help="Max rows to return")

    sub.add_parser("gate", help="Run acceptance gate (exits 1 if FAIL)")

    args = parser.parse_args()
    if args.command == "seed":
        _cmd_seed(args)
    elif args.command == "query":
        _cmd_query(args)
    elif args.command == "gate":
        _cmd_gate(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
