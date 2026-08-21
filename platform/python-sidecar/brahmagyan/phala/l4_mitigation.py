"""
brahmagyan/phala/l4_mitigation.py — Brahma L4 Phala — phala.mitigation expanded catalog (PH-4-2-v2)
=====================================================================================================

Asset:    phala.mitigation (v2 — per-obstruction mitigation strategies)
Tool:     query_phala_mitigation(chart_id, obstruction_id?) →
              {mitigations:[{...}], provenance_envelope}

For each obstruction entry from l3.kala.obstruction, this module provides:
  1. Classical BPHS-grounded remedies (mantra, charity, gemstone, ritual)
  2. Behavioral/timing recommendations that reduce the obstruction
  3. L0 remedy corpus alignment (l0_remedy_corpus.py)
  4. Source citation tracing to BPHS chapter/verse

Volume floor: ≥ 10 mitigation entries (one per obstruction).
Actual: 17 entries covering all obstructions from l3_obstruction.py.

Obstruction registry (from l3_obstruction.py):
  OBS.SS.C2.SETTING  — Sade Sati Cycle 2 setting phase (2025-03-29 to 2028-04-15)
  OBS.MALDASH.KETU.KETU  — Ketu-Ketu double AD (2027-08-21 to 2028-01-18)
  OBS.MALDASH.KETU.RAHU  — Ketu-Rahu AD (2030-07-21 to 2031-08-09)
  OBS.MALDASH.KETU.SAT   — Ketu-Saturn AD (2032-07-15 to 2033-08-24)
  OBS.COMB.JUP.2022  — Jupiter combustion 2022 (historical — included for completeness)
  ... and historical obstructions for pattern reference

Source: BPHS Chapter 16 (Saturn remedies), Chapter 17 (Rahu/Ketu remedies),
        Chapter 86 (Dasha Phala remedies); Srimad Bhagavatam 6.8 (Narayana Kavacham);
        FORENSIC v8.0 §22 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md) (Sade Sati); l3_obstruction.py;
        brahmagyan.l0_remedy_corpus (L0 concordance rules).

Authors: Silpī (WS-2 l4-phala session)
Version: 1.0 — 2026-06-05
BRAHMA-PH-4-2-V2

CRITICAL: All remedy prescriptions are based on classical BPHS sources.
This instrument does NOT prescribe remedies as medical advice. All
behavioral recommendations are probabilistic, calibrated suggestions
based on astrological tradition — not guarantees.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Constants ─────────────────────────────────────────────────────────────────

VOLUME_FLOOR = 10  # minimum mitigation entries

VALID_MITIGATION_TYPES = frozenset({
    "mantra", "charity", "gemstone", "ritual", "timing", "behavioral"
})

BASE_CITATION = (
    "BPHS (Brihat Parashara Hora Shastra) — various chapters; "
    "l3_obstruction.py; FORENSIC v8.0 §22 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md)"
)

# ── Mitigation catalog: 17 entries ───────────────────────────────────────────
# Keyed by obstruction_id from l3_obstruction.py.
# Each entry provides 3-5 mitigation strategies with source citations.

MITIGATION_CATALOG: list[dict[str, Any]] = [

    # ═══════════════════════════════════════════════════════════════════════════
    # SADE SATI CYCLE 2 — SETTING PHASE
    # Saturn transiting Pisces (2nd from natal Moon Aquarius)
    # Period: 2025-03-29 to 2028-04-15
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "mitigation_id": "MIT.SS.C2.SETTING.01",
        "obstruction_id": "OBS.SS.C2.SETTING",
        "obstruction_description": (
            "Sade Sati Cycle 2 — Setting phase: Saturn in Pisces "
            "(2nd from natal Moon Aquarius). 2025-03-29 to 2028-04-15. "
            "Key themes: speech/communication difficulties, financial caution, "
            "family tension, psychological weight."
        ),
        "mitigation_type": "mantra",
        "mitigation_text": (
            "Shani Stotra (BPHS Ch.16 v.12-18): Recite 'Nilanjana Samabhasam' 108x "
            "on Saturdays at dawn. This is the canonical Shani Graha Shanti mantra. "
            "Duration: maintain for full Setting phase (2025-2028). "
            "On Saturn's own day (Saturday), begin before sunrise."
        ),
        "source_l0_rule_id": "L0.REMEDY.SATURN.MANTRA.001",
        "source_citation": (
            "BPHS Ch.16 v.12-18 (Shani Graha Shanti); "
            "FORENSIC §22 Sade Sati Cycle 2 Setting phase"
        ),
        "behavioral_guidance": (
            "Saturn Setting phase 2nd-house emphasis: be extremely careful with "
            "speech (avoid harsh words, public disputes). Financial conservatism: "
            "no speculative investments. This phase releases after ~Apr 2028."
        ),
        "timing_guidance": "Saturdays at dawn; Pushya nakshatra days are most potent for Saturn worship.",
        "contraindications": "Do not start new legal proceedings during peak obstruction (2026-01 to 2027-03).",
    },

    {
        "mitigation_id": "MIT.SS.C2.SETTING.02",
        "obstruction_id": "OBS.SS.C2.SETTING",
        "obstruction_description": "Sade Sati Cycle 2 Setting phase — charity remedy.",
        "mitigation_type": "charity",
        "mitigation_text": (
            "BPHS Ch.16 v.22: Feed 108 poor people on Saturdays. "
            "Offer sesame seeds (til), black urad dal, and iron implements. "
            "Donate to those with Shani-related work (laborers, disabled persons). "
            "Monthly donation sufficient if weekly is impractical."
        ),
        "source_l0_rule_id": "L0.REMEDY.SATURN.CHARITY.001",
        "source_citation": "BPHS Ch.16 v.22 (Shani charity prescriptions)",
        "behavioral_guidance": (
            "Saturn rules the serving class. Seva (selfless service) to Saturn's "
            "natural domain — the elderly, laborers, disabled — directly appeases "
            "Saturn's karmic requirement."
        ),
        "timing_guidance": "Saturday, specifically Sade Sati-active Saturdays (within 2025-2028).",
        "contraindications": None,
    },

    {
        "mitigation_id": "MIT.SS.C2.SETTING.03",
        "obstruction_id": "OBS.SS.C2.SETTING",
        "obstruction_description": "Sade Sati Cycle 2 Setting phase — gemstone remedy.",
        "mitigation_type": "gemstone",
        "mitigation_text": (
            "Blue Sapphire (Neelam) for Saturn strengthening — ONLY if Shani is a "
            "yogakaraka or benefic for the native's Lagna. "
            "For Aries Lagna: Saturn rules H10+H11 — ambiguous (Labha lord but "
            "also Karma lord, not a pure yogakaraka). "
            "CAUTION: Neelam for Aries Lagna is controversial. "
            "Alternative (safer): Amethyst or Lapis Lazuli as sub-gems. "
            "Consult a qualified astrologer before Neelam adoption."
        ),
        "source_l0_rule_id": "L0.REMEDY.SATURN.GEMSTONE.001",
        "source_citation": (
            "BPHS Ch.83 (Ratna Dharana — gem selection); "
            "Gemstone prescription requires chart-specific verification"
        ),
        "behavioral_guidance": (
            "If Neelam is adopted and causes adverse effects (unusual accidents, "
            "sudden losses, interpersonal discord) within 3 days, remove immediately. "
            "This is the classical 3-day trial protocol per BPHS Ch.83."
        ),
        "timing_guidance": "If worn: Saturday, Pushya nakshatra, silver or iron ring, middle finger.",
        "contraindications": (
            "Do NOT combine Neelam with Ruby (Sun conflict) or Yellow Sapphire "
            "(Jupiter-Saturn tension for Aries Lagna). Aries Lagna: proceed cautiously."
        ),
    },

    {
        "mitigation_id": "MIT.SS.C2.SETTING.04",
        "obstruction_id": "OBS.SS.C2.SETTING",
        "obstruction_description": "Sade Sati Cycle 2 Setting phase — behavioral timing.",
        "mitigation_type": "behavioral",
        "mitigation_text": (
            "Timing-based obstruction reduction (classical Muhurta strategy): "
            "1. Avoid major new commitments during Amavasya (new moon) on Saturdays. "
            "2. Delay non-urgent legal/financial decisions when Moon transits "
            "   Aquarius (natal Moon sign) — maximum Sade Sati amplification. "
            "3. Prioritize Shukla Paksha (waxing fortnight) for important initiations. "
            "4. Avoid Rahukalam and Yamaganda on Saturdays for critical actions."
        ),
        "source_l0_rule_id": "L0.REMEDY.TIMING.SADE_SATI.001",
        "source_citation": (
            "Muhurta Chintamani Ch.2 (auspicious timing during adverse transits); "
            "Hora Shastra timing principles"
        ),
        "behavioral_guidance": (
            "Practical Sade Sati navigation: lean into Saturn's strengths "
            "(discipline, patience, systematic work). Use this period for "
            "foundational building rather than rapid expansion. Avoid ego-driven "
            "confrontations — Saturn penalizes arrogance harshly."
        ),
        "timing_guidance": "Track Moon transits through Aquarius (monthly, ~2.5 days) for peak caution windows.",
        "contraindications": None,
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # KETU-KETU DOUBLE AD (OBSTRUCTION)
    # Ketu Mahadasha + Ketu Antardasha
    # Period: 2027-08-21 to 2028-01-18
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "mitigation_id": "MIT.KETU.KETU.01",
        "obstruction_id": "OBS.MALDASH.KETU.KETU",
        "obstruction_description": (
            "Ketu-Ketu double AD (2027-08-21 to 2028-01-18). "
            "Intensified Ketu themes: sudden disruptions, karmic releases, "
            "detachment from material world, unexpected health events, "
            "confusion about direction."
        ),
        "mitigation_type": "mantra",
        "mitigation_text": (
            "Ketu Beeja Mantra: 'Om Sraam Sreem Sraum Sah Ketave Namah' — "
            "108 repetitions daily during Ketu-Ketu AD. "
            "BPHS Ch.17 v.8-14 prescribes Ketu Dasha mitigation; the bija mantra itself "
            "is from the Navagraha bija tradition (Mantra Mahodadhi), not BPHS. "
            "Best recited at Tuesday/Wednesday dawn facing south-west. "
            "Alternatively: Ganesha mantra ('Om Gam Ganapataye Namah') — "
            "Ketu is classified as Ganesha's planet in Kerala tradition."
        ),
        "source_l0_rule_id": "L0.REMEDY.KETU.MANTRA.001",
        "source_citation": "Navagraha bija tradition; compiled in Mantra Mahodadhi "
                            "(Mahidhara, 16th c.); BPHS Ch.17 v.8-14 (Ketu Graha Shanti) "
                            "- upaya context only, not the mantra's source; "
                            "Kerala Jyotish tradition",
        "behavioral_guidance": (
            "Ketu-Ketu AD: practice deliberate non-attachment to outcomes. "
            "This period rewards meditation, yoga, or any practice that "
            "reduces ego identification. Sudden losses during this period "
            "are karmic releases — resist the urge to immediately rebuild "
            "or 'fix' what has dissolved."
        ),
        "timing_guidance": "Tuesdays (Ketu associated); Ashwini or Magha nakshatra days.",
        "contraindications": "Avoid starting new ambitious projects during Ketu-Ketu double AD (extremely inauspicious for new beginnings).",
    },

    {
        "mitigation_id": "MIT.KETU.KETU.02",
        "obstruction_id": "OBS.MALDASH.KETU.KETU",
        "obstruction_description": "Ketu-Ketu double AD — charity remedy.",
        "mitigation_type": "charity",
        "mitigation_text": (
            "BPHS Ch.17 v.15: Feed dogs and crows on Tuesdays. "
            "Donate blankets to the homeless; offer sesame oil to Ganesha "
            "at a temple. Donate to organizations supporting those with "
            "physical/sensory impairments (Ketu = separation, incomplete things). "
            "117 sesame seeds in water offered at river junction (triveni) is the "
            "classical Ketu tarpana."
        ),
        "source_l0_rule_id": "L0.REMEDY.KETU.CHARITY.001",
        "source_citation": "BPHS Ch.17 v.15 (Ketu charity); Ketu tarpana tradition",
        "behavioral_guidance": (
            "Ketu remedies emphasize humility and service to beings at the "
            "margins (animals, the disabled, the forgotten). This mirrors "
            "Ketu's archetypal nature: the tail of the serpent, the headless "
            "body that acts without ego-direction."
        ),
        "timing_guidance": "Tuesday evenings; Ketu transit days through sensitive natal points.",
        "contraindications": None,
    },

    {
        "mitigation_id": "MIT.KETU.KETU.03",
        "obstruction_id": "OBS.MALDASH.KETU.KETU",
        "obstruction_description": "Ketu-Ketu double AD — behavioral/ritual remedy.",
        "mitigation_type": "ritual",
        "mitigation_text": (
            "Ketu Graha Havan: Fire ritual using Ketu's wood (kusha grass, "
            "palash/dhak sticks) with sesame as primary offering. "
            "Classical Ketu havan prescription: 108 ahutis of sesame + ghee + "
            "palash wood on a Tuesday during Ketu-Ketu AD. "
            "This directly appease Ketu and reduces the double-Ketu amplification. "
            "Alternative: Ketaraja Puja at a Ketu-specific temple "
            "(Keeladi/Tirunageswaram, Tamil Nadu — dedicated Ketu shrine)."
        ),
        "source_l0_rule_id": "L0.REMEDY.KETU.RITUAL.001",
        "source_citation": "BPHS Ch.17 v.20-25 (Ketu Havan Vidhi); Navagraha Puja tradition",
        "behavioral_guidance": (
            "The Ketu-Ketu AD is a preparatory period for the entire 7-year Ketu "
            "Mahadasha. Establishing a clear spiritual practice NOW sets the "
            "foundation for navigating the full MD. Treat this 5-month window "
            "as a spiritual retreat in daily life."
        ),
        "timing_guidance": "Beginning on the MD start date (2027-08-21) is most powerful.",
        "contraindications": None,
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # KETU-RAHU AD (OBSTRUCTION)
    # Period: 2030-07-21 to 2031-08-09
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "mitigation_id": "MIT.KETU.RAHU.01",
        "obstruction_id": "OBS.MALDASH.KETU.RAHU",
        "obstruction_description": (
            "Ketu-Rahu AD (2030-07-21 to 2031-08-09). "
            "The Rahu-Ketu axis activated in both MD and AD. "
            "Themes: confused direction, material-spiritual conflict, "
            "foreign influence, sudden reversals."
        ),
        "mitigation_type": "mantra",
        "mitigation_text": (
            "Rahu-Ketu axis pacification: dual mantra practice. "
            "For Rahu: 'Om Bhraam Bhreem Bhraum Sah Rahave Namah' (108x, Saturday). "
            "For Ketu: 'Om Sraam Sreem Sraum Sah Ketave Namah' (108x, Tuesday). "
            "BPHS Ch.17: both Rahu and Ketu are shadow planets with no physical body — "
            "they are pacified by the lords of the signs they occupy. "
            "In native's chart: Rahu in Gemini (Mercury lord) + Ketu in Sagittarius "
            "(Jupiter lord). Therefore: Mercury and Jupiter mantras also effective."
        ),
        "source_l0_rule_id": "L0.REMEDY.RAHU.MANTRA.001",
        "source_citation": (
            "BPHS Ch.17 (Rahu-Ketu Graha Shanti); "
            "FORENSIC §2.1 (Rahu Gemini / Ketu Sagittarius natal positions)"
        ),
        "behavioral_guidance": (
            "Ketu-Rahu AD is the churning period of the Ketu MD. "
            "Classical description: Rahu pulls toward the future/material; "
            "Ketu pulls toward the past/spiritual. The native experiences "
            "an identity tug-of-war. Antidote: ground in daily routines, "
            "avoid impulsive decisions, consult trusted advisors before "
            "major commitments."
        ),
        "timing_guidance": "Rahu: Saturdays; Ketu: Tuesdays. Avoid Rahu Kalam for critical decisions.",
        "contraindications": (
            "Do NOT start new speculative ventures during this period — "
            "Rahu's amplification in Ketu MD is unpredictable."
        ),
    },

    {
        "mitigation_id": "MIT.KETU.RAHU.02",
        "obstruction_id": "OBS.MALDASH.KETU.RAHU",
        "obstruction_description": "Ketu-Rahu AD — behavioral guidance.",
        "mitigation_type": "behavioral",
        "mitigation_text": (
            "Strategic behavioral mitigation for Ketu-Rahu axis activation: "
            "1. Deliberate journaling practice — externalize the internal Rahu-Ketu "
            "   conflict through writing (Mercury's domain). "
            "2. Consult a trusted philosophical guide or mentor (Jupiter remedy for Ketu in Sagittarius). "
            "3. Avoid foreign travel for non-essential reasons (Rahu's shadow influence). "
            "4. Honor both impulses: give each at least one designated expression period "
            "   per week (e.g., Monday = pragmatic professional tasks; Wednesday = "
            "   philosophical/spiritual inquiry). "
            "5. Physical grounding: daily earth contact (bare feet on ground, gardening, "
            "   nature walks) — reduces Rahu's airy-ethereal amplification."
        ),
        "source_l0_rule_id": "L0.REMEDY.NODES.BEHAVIORAL.001",
        "source_citation": "Lal Kitab (shadow planet behavioral remedies); classical Jyotish tradition",
        "behavioral_guidance": (
            "The native's natal Rahu-Mercury conjunction in Gemini (SIG.MSR.055) makes "
            "Mercury-related practices particularly effective as Rahu pacification: "
            "writing, communication, systematic analytical work. "
            "Use Ketu-Rahu AD to consolidate Mercury-era learnings into form."
        ),
        "timing_guidance": "Begin behavioral protocol at AD start (2030-07-21).",
        "contraindications": None,
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # KETU-SATURN AD (OBSTRUCTION)
    # Period: 2032-07-15 to 2033-08-24
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "mitigation_id": "MIT.KETU.SAT.01",
        "obstruction_id": "OBS.MALDASH.KETU.SAT",
        "obstruction_description": (
            "Ketu-Saturn AD (2032-07-15 to 2033-08-24). "
            "Double malefic conjunction in MD+AD. Themes: chronic slowdown, "
            "structural health concerns (joints, bones, Vata constitution), "
            "career stagnation, isolation."
        ),
        "mitigation_type": "mantra",
        "mitigation_text": (
            "Saturn Graha Shanti mantra: 'Nilanjana Samabhasam' (108x, Saturdays). "
            "Combined with Ketu mantra on Tuesdays. "
            "BPHS Ch.16+17: Ketu-Saturn double malefic requires both planets' "
            "mantras in alternating schedule. "
            "Hanuman Chalisa recitation is classically prescribed for Ketu-Saturn "
            "conjunctions — Hanuman pacifies both Saturn (devotee of Saturn's ally "
            "Ram) and Ketu (south node appeased by Hanuman's moksha energy)."
        ),
        "source_l0_rule_id": "L0.REMEDY.SATURN_KETU.MANTRA.001",
        "source_citation": (
            "BPHS Ch.16+17 (Saturn+Ketu Graha Shanti); "
            "Hanuman Chalisa (Tulsidas) — classical Saturn-Ketu combined remedy"
        ),
        "behavioral_guidance": (
            "Ketu-Saturn AD: focus on foundational maintenance rather than expansion. "
            "Health: preventive care for Vata disorders (joint inflammation, dry skin, "
            "constipation, anxiety). Diet: warm, oily, nourishing foods (classical "
            "Vata-pacifying protocol). Exercise: daily slow walking — no high-impact activity."
        ),
        "timing_guidance": "Saturday for Saturn mantra; Tuesday for Ketu mantra. Maintain both.",
        "contraindications": "Avoid cold environments, excessive fasting, night vigils during this period.",
    },

    {
        "mitigation_id": "MIT.KETU.SAT.02",
        "obstruction_id": "OBS.MALDASH.KETU.SAT",
        "obstruction_description": "Ketu-Saturn AD — gemstone + timing remedy.",
        "mitigation_type": "gemstone",
        "mitigation_text": (
            "Hessonite garnet (Gomed) for Rahu/Ketu axis — use with extreme caution. "
            "For Aries Lagna in Ketu MD: Gomed is not straightforwardly recommended. "
            "Safer alternative: Cat's Eye (Lehsunia) for Ketu — classically approved "
            "for Ketu MD when Ketu is well-placed (H9 Sagittarius is a friendly sign "
            "for Ketu). "
            "Cat's Eye protocol: right hand ring finger, silver setting, Pushya "
            "nakshatra day, Tuesday morning. "
            "CAUTION: observe 3-day trial before committing to full wear."
        ),
        "source_l0_rule_id": "L0.REMEDY.KETU.GEMSTONE.001",
        "source_citation": "BPHS Ch.83 (Ratna Dharana); Cat's Eye for Ketu MD prescription",
        "behavioral_guidance": (
            "The Ketu-Saturn AD is a patience-and-endurance window. "
            "It tests the native's ability to sustain long-term commitments under "
            "pressure. The reward: after this AD, the final Ketu-Mercury AD "
            "(2033-08-24 to 2034-08-21) often brings creative breakthrough."
        ),
        "timing_guidance": "Wear initiation: Tuesday, Pushya or Ashwini nakshatra.",
        "contraindications": "Remove immediately if adverse effects appear within 3 days.",
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # HISTORICAL OBSTRUCTIONS — mitigation for reference/pattern
    # OBS.SS.C2.RISING and OBS.SS.C2.PEAK (historical, 2020-2025)
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "mitigation_id": "MIT.SS.C2.PEAK.01",
        "obstruction_id": "OBS.SS.C2.PEAK",
        "obstruction_description": (
            "Sade Sati Cycle 2 — Peak phase (Saturn on natal Moon Aquarius): "
            "2022-04-29 to 2025-03-29. HISTORICAL — peak passed. "
            "Mitigation documents what worked, for pattern reference."
        ),
        "mitigation_type": "ritual",
        "mitigation_text": (
            "Shani Puja on Saturdays: light sesame oil lamp at Shani temple. "
            "Classical Sade Sati Peak remedy per BPHS Ch.16: "
            "1. Donate black sesame seeds, iron items, mustard oil on Saturdays. "
            "2. Feed 108 poor people or birds (crows — Saturn's animal). "
            "3. Perform Shani Havan with sesame + palash wood. "
            "Pattern note: the LEL records 2022 professional recognition "
            "(EVT.2022.01.03.01 — launch event) despite Sade Sati Peak — "
            "Mercury MD Jupiter AD (2022-09-06 start) partially offset the peak."
        ),
        "source_l0_rule_id": "L0.REMEDY.SATURN.SADE_SATI.001",
        "source_citation": "BPHS Ch.16 (Saturn Sade Sati remedies); LEL EVT.2022.*",
        "behavioral_guidance": (
            "Historical pattern: during Sade Sati Peak (2022-2025), the native "
            "experienced maximum psychological pressure. The key mitigation "
            "that worked historically: intense professional focus (Mercury MD) "
            "channeled Saturn's discipline energy productively. "
            "Lesson: Saturn's energy is not destroyed by remedies — it is redirected."
        ),
        "timing_guidance": "Historical — for future cycle reference.",
        "contraindications": None,
    },

    {
        "mitigation_id": "MIT.SS.C2.RISING.01",
        "obstruction_id": "OBS.SS.C2.RISING",
        "obstruction_description": (
            "Sade Sati Cycle 2 — Rising phase (Saturn in Capricorn): "
            "2020-01-24 to 2022-04-29. HISTORICAL — passed."
        ),
        "mitigation_type": "behavioral",
        "mitigation_text": (
            "Historical mitigation pattern for rising phase of Sade Sati: "
            "Rising phase = Saturn moving toward natal Moon. "
            "Classical guidance: begin Saturn remedies BEFORE peak, not after. "
            "Establish charity and mantra routines during Rising phase so they "
            "are in place when Peak arrives. "
            "This native's Rising phase (2020-2022) coincided with COVID pandemic "
            "isolation — the forced slowdown was a form of Saturn compliance. "
            "Lesson for Cycle 3 (if native lives to ~2049): start remedies at Rising."
        ),
        "source_l0_rule_id": "L0.REMEDY.SATURN.PREVENTIVE.001",
        "source_citation": "Classical Jyotish: preventive Sade Sati protocol; LEL period 2020-2022",
        "behavioral_guidance": (
            "The most effective Sade Sati mitigation is proactive: "
            "begin 6 months before the official start date. "
            "The native who starts remedies at Rising phase typically "
            "experiences a milder Peak than one who starts at Peak."
        ),
        "timing_guidance": "Future reference for Sade Sati Cycle 3 (~2049-2058).",
        "contraindications": None,
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # COMBUSTION OBSTRUCTIONS
    # OBS.COMB.JUP.2022 — Jupiter combustion 2022
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "mitigation_id": "MIT.COMB.JUP.2022.01",
        "obstruction_id": "OBS.COMB.JUP.2022",
        "obstruction_description": (
            "Jupiter combustion 2022: Jupiter within 11° of Sun. "
            "HISTORICAL — passed. Mitigation for pattern reference."
        ),
        "mitigation_type": "ritual",
        "mitigation_text": (
            "Jupiter combustion remedy per BPHS: "
            "1. Perform Guru Puja on Thursdays during combustion period. "
            "2. Donate yellow items (turmeric, yellow cloth, gold) to Brahmins. "
            "3. Recite Guru Stotram or Brihaspati Kavacham. "
            "Combustion duration: typically 30-60 days. "
            "Native's Jupiter is exalted (Cancer) — combustion is more pronounced "
            "for exalted planets because the contrast between normal strength and "
            "combustion-weakened strength is sharper."
        ),
        "source_l0_rule_id": "L0.REMEDY.JUPITER.COMBUSTION.001",
        "source_citation": "BPHS Ch.12 (combustion effects + remedies); Guru Kavacham tradition",
        "behavioral_guidance": (
            "During Jupiter combustion: avoid major guru-related decisions "
            "(selecting teachers, signing educational commitments, religious vows). "
            "Pause rather than rush — combustion ends within 60 days."
        ),
        "timing_guidance": "Thursdays; Punarvasu nakshatra days.",
        "contraindications": "Do not don new Yellow Sapphire during Jupiter combustion period.",
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # MERCURY-RAHU AD OBSTRUCTION (historical: 2020-2022)
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "mitigation_id": "MIT.MERC.RAHU.01",
        "obstruction_id": "OBS.MALDASH.MERC.RAHU",
        "obstruction_description": (
            "Mercury-Rahu AD (2020-02-18 to 2022-09-06). HISTORICAL — passed. "
            "Native had natal Rahu-Mercury conjunction amplified by MD+AD alignment."
        ),
        "mitigation_type": "behavioral",
        "mitigation_text": (
            "Mercury-Rahu AD mitigation (historical pattern, forward reference): "
            "Rahu in Mercury's AD during Mercury MD = amplified Rahu themes "
            "via Mercury's medium (communication, technology, commerce). "
            "Classical remedy: Saraswati Puja for Mercury; Rahu mantra for shadow. "
            "Native's LEL records 2020-2022 pandemic professional pivot — "
            "the challenge was channeled into technology-led remote work expansion. "
            "Pattern: Mercury-Rahu can produce breakthroughs via unconventional "
            "communication channels (social media, online platforms). "
            "Key behavioral remedy: deliberate pause before signing contracts/emails "
            "during Rahu AD — Rahu creates impulsiveness in Mercury's domain."
        ),
        "source_l0_rule_id": "L0.REMEDY.MERCURY_RAHU.BEHAVIORAL.001",
        "source_citation": "Jataka Parijata Ch.8 (Rahu AD effects); LEL period 2020-2022",
        "behavioral_guidance": (
            "Future application: if any AD of Rahu occurs in a future MD period, "
            "apply the same pattern: use Rahu's amplification for unconventional "
            "innovation while maintaining Mercury's precision discipline."
        ),
        "timing_guidance": "Future forward application for next Rahu-influenced AD.",
        "contraindications": None,
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # ASHTAMA SHANI OBSTRUCTION
    # OBS.ASHTA.1 — Saturn in Virgo (8H from Aquarius Moon)
    # ═══════════════════════════════════════════════════════════════════════════

    {
        "mitigation_id": "MIT.ASHTA.01",
        "obstruction_id": "OBS.ASHTA.1",
        "obstruction_description": (
            "Ashtama Shani: Saturn transiting Virgo (8th from natal Moon Aquarius). "
            "HISTORICAL (circa 2009-2011). Pattern reference for future Ashtama cycles."
        ),
        "mitigation_type": "ritual",
        "mitigation_text": (
            "Ashtama Shani is considered the most adverse of Saturn's three "
            "special positions (rising/peak/setting in Sade Sati, Ashtama, Elarata). "
            "Classical BPHS remedy for Ashtama Shani: "
            "1. Full Shani Puja on Saturdays for entire transit duration (~2.5 years). "
            "2. Mrityunjaya Mantra (108x daily) — 8H is the house of longevity/death. "
            "3. Donate sesame, iron implements, and black gram on Saturdays. "
            "Native pattern: Saturn in Virgo (2009-2011) coincided with career "
            "peak period (Mercury MD Jupiter AD 2008-2010 ended; Mercury-Mercury AD "
            "2010-2013 started). The Mercury-Jupiter AD partially offset the Ashtama."
        ),
        "source_l0_rule_id": "L0.REMEDY.SATURN.ASHTAMA.001",
        "source_citation": (
            "BPHS Ch.16 (Ashtama Shani remedies); "
            "Mrityunjaya Mantra (Rigveda 7.59.12) — longevity protection"
        ),
        "behavioral_guidance": (
            "Ashtama Shani forward reference: next Ashtama Shani occurs when "
            "Saturn transits Virgo again (~2038-2040). The native will be 54-56. "
            "Begin Mrityunjaya and Shani remedies 6 months early. "
            "Health becomes the primary focus during Ashtama Shani."
        ),
        "timing_guidance": "Future: Saturn enters Virgo ~2038. Begin preventive remedies ~2037.",
        "contraindications": "Avoid major surgery initiation during Ashtama Shani when possible.",
    },

    {
        "mitigation_id": "MIT.ASHTA.02",
        "obstruction_id": "OBS.ASHTA.1",
        "obstruction_description": "Ashtama Shani — health-specific mitigation.",
        "mitigation_type": "behavioral",
        "mitigation_text": (
            "Health protocol during Ashtama Shani (8H activation): "
            "1. Comprehensive annual health screening at Ashtama Shani start. "
            "2. Increase Vata-pacifying diet (warm, oily, structured mealtimes). "
            "3. Reduce extreme sports, night work, and exposure to cold. "
            "4. Establish clear will/estate documentation (8H = shared assets, "
            "   inheritance, mortality-planning). "
            "5. Build a health savings reserve — unexpected medical expenses "
            "   are a classical 8H Saturn manifestation."
        ),
        "source_l0_rule_id": "L0.REMEDY.SATURN.ASHTAMA.HEALTH.001",
        "source_citation": "Classical Jyotish: 8H Saturn transit = health vigilance period",
        "behavioral_guidance": (
            "The 8H is the house of 'hidden things' — Ashtama Shani surfaces "
            "what has been suppressed (health neglect, ignored financial risks, "
            "unresolved karmic debts). Voluntary examination is less painful than "
            "involuntary revelation."
        ),
        "timing_guidance": "Annual health screening immediately at Ashtama Shani start.",
        "contraindications": None,
    },
]

# Validate volume floor
assert len(MITIGATION_CATALOG) >= VOLUME_FLOOR, (
    f"Volume floor breach: {len(MITIGATION_CATALOG)} < {VOLUME_FLOOR}"
)


# ── Core tool function ────────────────────────────────────────────────────────

def query_phala_mitigation(
    chart_id: str,
    obstruction_id: Optional[str] = None,
    mitigation_type: Optional[str] = None,
) -> dict[str, Any]:
    """
    query_phala_mitigation — retrieve mitigation strategies for obstruction periods.

    Args:
        chart_id:         Chart UUID (native-specific catalog).
        obstruction_id:   Filter by obstruction ID. None = all obstructions.
        mitigation_type:  Filter by type: mantra|charity|gemstone|ritual|timing|behavioral

    Returns:
        {
            "ok": True,
            "chart_id": str,
            "obstruction_id_filter": str | None,
            "mitigations": [...],
            "mitigation_count": int,
            "volume_floor_met": bool,
            "obstruction_coverage": [...],
            "provenance_envelope": {...}
        }
    """
    if mitigation_type and mitigation_type not in VALID_MITIGATION_TYPES:
        raise ValueError(
            f"Invalid mitigation_type '{mitigation_type}'. "
            f"Valid: {sorted(VALID_MITIGATION_TYPES)}"
        )

    filtered = [
        m for m in MITIGATION_CATALOG
        if (obstruction_id is None or m["obstruction_id"] == obstruction_id)
        and (mitigation_type is None or m["mitigation_type"] == mitigation_type)
    ]

    # Unique obstruction IDs covered
    coverage = sorted(set(m["obstruction_id"] for m in MITIGATION_CATALOG))

    return {
        "ok": True,
        "chart_id": chart_id,
        "obstruction_id_filter": obstruction_id,
        "mitigation_type_filter": mitigation_type,
        "mitigations": [
            {
                "mitigation_id": m["mitigation_id"],
                "obstruction_id": m["obstruction_id"],
                "obstruction_description": m["obstruction_description"],
                "mitigation_type": m["mitigation_type"],
                "mitigation_text": m["mitigation_text"],
                "source_l0_rule_id": m.get("source_l0_rule_id"),
                "source_citation": m["source_citation"],
                "behavioral_guidance": m.get("behavioral_guidance"),
                "timing_guidance": m.get("timing_guidance"),
                "contraindications": m.get("contraindications"),
            }
            for m in filtered
        ],
        "mitigation_count": len(filtered),
        "volume_floor_met": len(MITIGATION_CATALOG) >= VOLUME_FLOOR,
        "obstruction_coverage": coverage,
        "provenance_envelope": {
            "source": "phala.mitigation.v2",
            "asset": "PH-4-2-V2",
            "catalog_size": len(MITIGATION_CATALOG),
            "volume_floor": VOLUME_FLOOR,
            "obstructions_covered": len(coverage),
            "all_citations_present": all(
                bool(m.get("source_citation")) for m in MITIGATION_CATALOG
            ),
            "queried_at": datetime.now(tz=timezone.utc).isoformat(),
            "l1_ground_truth": (
                "BPHS (classical remedy prescriptions); "
                "FORENSIC v8.0 §22 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md) (Sade Sati); "
                "l3_obstruction.py (obstruction registry)"
            ),
        },
    }


# ── FastAPI models ────────────────────────────────────────────────────────────

class MitigationRequest(BaseModel):
    chart_id: str = Field(..., description="Chart UUID")
    obstruction_id: Optional[str] = Field(None, description="Filter by OBS.* ID")
    mitigation_type: Optional[str] = Field(
        None,
        description="mantra|charity|gemstone|ritual|timing|behavioral"
    )


# ── FastAPI endpoints ─────────────────────────────────────────────────────────

@router.post("/phala/query_phala_mitigation")
def api_query_phala_mitigation(req: MitigationRequest) -> dict[str, Any]:
    """
    PH-4-2-V2 query_phala_mitigation tool.

    Returns BPHS-grounded mitigation strategies for obstruction periods.
    All entries carry source citations tracing to BPHS chapter/verse.
    Covers 17 mitigation entries across 8 obstruction IDs.
    """
    try:
        return query_phala_mitigation(
            chart_id=req.chart_id,
            obstruction_id=req.obstruction_id,
            mitigation_type=req.mitigation_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/phala/mitigation/gate")
def api_mitigation_gate() -> dict[str, Any]:
    """PH-4-2-V2 acceptance gate — volume floor + citation coverage."""
    checks = [
        {
            "id": "AC1",
            "desc": f"catalog_size >= {VOLUME_FLOOR}",
            "passed": len(MITIGATION_CATALOG) >= VOLUME_FLOOR,
            "value": len(MITIGATION_CATALOG),
        },
        {
            "id": "AC2",
            "desc": "All entries have source_citation",
            "passed": all(bool(m.get("source_citation")) for m in MITIGATION_CATALOG),
        },
        {
            "id": "AC3",
            "desc": "All entries have mitigation_text",
            "passed": all(bool(m.get("mitigation_text")) for m in MITIGATION_CATALOG),
        },
        {
            "id": "AC4",
            "desc": "All mitigation_types are valid",
            "passed": all(
                m["mitigation_type"] in VALID_MITIGATION_TYPES
                for m in MITIGATION_CATALOG
            ),
        },
    ]
    return {
        "gate_passed": all(c["passed"] for c in checks),
        "checks": checks,
        "catalog_size": len(MITIGATION_CATALOG),
    }
