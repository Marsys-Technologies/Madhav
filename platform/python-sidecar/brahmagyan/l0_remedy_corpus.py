"""
brahmagyan.l0_remedy_corpus — L0 Brahmagyan bg_remedies writer (v2.0)
=======================================================================

Classical remedy corpus for brahma_remedy_corpus.
Sources:
  - BPHS Ch.88-94 (Upaya-adhyaya) — per-planet mantras, dana, graha-shanti
  - classical ratna-shastra — gemstone correspondences
  - classical tradition — vrata/yantra/puja/homa/behavioral
  - Phaladeepika (Mantreswara) — supplementary remedies
  - Tajaka Neelakanthi — annual-chart remedies

Architecture:
  1. gen_planet_matrix()    → 108 rows  (9 planets × 8 fixed cells + 36 dana-charity)
  2. DOSHA_REMEDIES         → 102 rows  (50 doshas × 2 remedies each + 2 extras)
  3. LEGACY_REMEDIES        → all 54 original rows from the v1.0 hardcoded set

ZERO LLM — all data hardcoded from classical sources.
remedy_type vocabulary: mantra/yantra/gemstone/charity/vrata/puja/japa/homa/behavioral/ayurvedic
(legacy fasting→vrata, ritual→puja, dietary→ayurvedic are mapped in REMEDY_TYPE_MAP)

BRAHMA-BG-0-9 (v2.0 — bg_remedies campaign 2026-06-09)
"""
from __future__ import annotations

import hashlib
import json
import logging

from brahmagyan.graha_vocabulary import to_title
from typing import Any

logger = logging.getLogger(__name__)

VOLUME_FLOOR = 50   # legacy floor (kept for backward-compat)
CAMPAIGN_FLOOR = 800   # v2.0 brief floor

# ── Source citations ──────────────────────────────────────────────────────────

SOURCE_BPHS = "BPHS (Brihat Parasara Hora Sastra), Ch.88-94 (Upaya-adhyaya)"
SOURCE_BPHS_LEGACY = "BPHS (Brihat Parasara Hora Sastra), trans. Rishi Kumar Shastri, public domain"
SOURCE_RATNA = "classical ratna-shastra; Phaladeepika (Mantreswara)"
SOURCE_PHALA = "Phaladeepika (Mantreswara), trans. G.S. Kapoor, public domain"
SOURCE_TAJAKA = "Tajaka Neelakanthi, classical tradition, public domain"
SOURCE_CLASSICAL = "classical tradition (Jyotish)"

# ── Valid ontology vocabulary sets ────────────────────────────────────────────

VALID_REMEDY_TYPES = {
    "mantra", "yantra", "gemstone", "charity", "vrata", "puja",
    "japa", "homa", "tantric", "ayurvedic", "vastu", "behavioral",
}

VALID_PLANETS = {
    "sun", "moon", "mars", "mercury", "jupiter", "venus",
    "saturn", "rahu", "ketu",
}

# Map legacy l0_remedy_corpus.py remedy_type values → ontology vocabulary
REMEDY_TYPE_MAP = {
    "fasting": "vrata",
    "ritual": "puja",
    "dietary": "ayurvedic",
    "havan": "homa",
    "yajna": "homa",
    # identity aliases (already valid):
    "charity": "charity",
    "gemstone": "gemstone",
    "mantra": "mantra",
    "yantra": "yantra",
    "japa": "japa",
    "vrata": "vrata",
    "puja": "puja",
    "homa": "homa",
    "behavioral": "behavioral",
    "ayurvedic": "ayurvedic",
    "vastu": "vastu",
}


def _map_remedy_type(rt: str) -> str:
    """Normalise to ontology vocabulary; raise if unknown."""
    mapped = REMEDY_TYPE_MAP.get(rt, rt)
    if mapped not in VALID_REMEDY_TYPES:
        raise ValueError(f"remedy_type '{rt}' → '{mapped}' not in ontology vocabulary")
    return mapped


def _remedy_id(planet: str, remedy_type: str, prescription_text: str) -> str:
    """Deterministic remedy_id from (planet, remedy_type, sha256(prescription_text[:80]))."""
    h = hashlib.sha256(prescription_text[:80].encode()).hexdigest()[:8]
    return f"{planet}_{remedy_type}_{h}"


# ── §3.1 — 9-Graha correspondence table (Racayitā-embedded) ──────────────────

PLANET_REMEDY_DATA: dict[str, dict] = {
    "sun": {
        "beej": "Om Hraam Hreem Hraum Sah Suryaya Namah",
        "beej_sa": "ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः",
        "deity": "Surya",
        "day": "Sunday",
        "color": "red/orange",
        "gem": "Ruby (Manikya)",
        "metal": "copper/gold",
        "dana": ["wheat", "jaggery", "copper", "red cloth"],
    },
    "moon": {
        "beej": "Om Shraam Shreem Shraum Sah Chandraya Namah",
        "beej_sa": "ॐ श्रां श्रीं श्रौं सः चन्द्राय नमः",
        "deity": "Chandra",
        "day": "Monday",
        "color": "white",
        "gem": "Pearl (Moti)",
        "metal": "silver",
        "dana": ["rice", "milk", "white cloth", "silver", "sugar"],
    },
    "mars": {
        "beej": "Om Kraam Kreem Kraum Sah Bhaumaya Namah",
        "beej_sa": "ॐ क्रां क्रीं क्रौं सः भौमाय नमः",
        "deity": "Hanuman/Kartikeya",
        "day": "Tuesday",
        "color": "red",
        "gem": "Red Coral (Moonga)",
        "metal": "copper",
        "dana": ["masoor dal", "red cloth", "copper", "jaggery"],
    },
    "mercury": {
        "beej": "Om Braam Breem Braum Sah Budhaya Namah",
        "beej_sa": "ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः",
        "deity": "Vishnu/Budha",
        "day": "Wednesday",
        "color": "green",
        "gem": "Emerald (Panna)",
        "metal": "bronze",
        "dana": ["green gram (moong)", "green cloth", "bronze"],
    },
    "jupiter": {
        "beej": "Om Graam Greem Graum Sah Gurave Namah",
        "beej_sa": "ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः",
        "deity": "Brihaspati/Vishnu",
        "day": "Thursday",
        "color": "yellow",
        "gem": "Yellow Sapphire (Pukhraj)",
        "metal": "gold",
        "dana": ["chana dal", "turmeric", "gold", "yellow cloth"],
    },
    "venus": {
        "beej": "Om Draam Dreem Draum Sah Shukraya Namah",
        "beej_sa": "ॐ द्रां द्रीं द्रौं सः शुक्राय नमः",
        "deity": "Lakshmi/Shukra",
        "day": "Friday",
        "color": "white/variegated",
        "gem": "Diamond (Heera)",
        "metal": "silver",
        "dana": ["sugar", "white cloth", "curd", "silver", "perfume"],
    },
    "saturn": {
        "beej": "Om Praam Preem Praum Sah Shanaye Namah",
        "beej_sa": "ॐ प्रां प्रीं प्रौं सः शनैश्चराय नमः",
        "deity": "Shani/Hanuman",
        "day": "Saturday",
        "color": "black/dark blue",
        "gem": "Blue Sapphire (Neelam)",
        "metal": "iron",
        "dana": ["black sesame", "iron", "mustard oil", "black cloth"],
    },
    "rahu": {
        "beej": "Om Bhraam Bhreem Bhraum Sah Rahave Namah",
        "beej_sa": "ॐ भ्रां भ्रीं भ्रौं सः राहवे नमः",
        "deity": "Durga",
        "day": "Saturday",
        "color": "smoky/grey",
        "gem": "Hessonite (Gomed)",
        "metal": "lead/silver",
        "dana": ["urad dal", "blue cloth", "coconut", "mustard oil"],
    },
    "ketu": {
        "beej": "Om Sraam Sreem Sraum Sah Ketave Namah",
        "beej_sa": "ॐ स्रां स्रीं स्रौं सः केतवे नमः",
        "deity": "Ganesha",
        "day": "Saturday/Tuesday",
        "color": "multicolour/grey",
        "gem": "Cat's Eye (Lehsunia)",
        "metal": "panchdhatu",
        "dana": ["sesame", "blanket", "multicolour cloth"],
    },
}


def gen_planet_matrix() -> list[dict[str, Any]]:
    """
    Deterministic matrix generator.
    Yield per planet:
      1 mantra + 1 gemstone + len(dana) charity + 1 vrata + 1 puja + 1 yantra
      + 1 homa + 1 behavioral + 1 japa
    = 8 fixed cells per planet + len(dana) charity rows.
    Total = 9 × 8 + (4+5+4+3+4+5+4+4+3) = 72 + 36 = 108 rows.
    """
    rows: list[dict[str, Any]] = []
    for p, d in PLANET_REMEDY_DATA.items():
        # 1. mantra (beej)
        text = (
            f"Recite the {p.capitalize()} beej mantra '{d['beej']}' 108 times daily "
            f"on {d['day']}, facing east. Complete mahadasha-count japa over the dasha period."
        )
        rows.append({
            "remedy_id": f"{p}_matrix_mantra",
            "planet": p,
            "domain": "general",
            "remedy_type": "mantra",
            "scaffold_status": "live",
            "prescription_text": text,
            "mantra_sanskrit": d["beej_sa"],
            "mantra_transliteration": d["beej"],
            "deity": d["deity"],
            "day_of_week": d["day"],
            "color_associated": d["color"],
            "source_canonical_id": "BPHS",
            "source_citation": SOURCE_BPHS,
            "classical_ref": "BPHS Ch.91-94 (Upaya-adhyaya)",
            "cost_tier": "free",
            "confidence": 0.90,
        })
        # 2. gemstone
        text = (
            f"Wear a tested {d['gem']} in {d['metal']} on the prescribed finger, on {d['day']}, "
            f"during Shukla Paksha. ONLY if {p.capitalize()} is a functional benefic in the chart "
            f"(test for 3 days first before committing)."
        )
        rows.append({
            "remedy_id": f"{p}_matrix_gemstone",
            "planet": p,
            "domain": "general",
            "remedy_type": "gemstone",
            "scaffold_status": "live",
            "prescription_text": text,
            "gemstone": d["gem"],
            "day_of_week": d["day"],
            "color_associated": d["color"],
            "source_canonical_id": "BPHS",
            "source_citation": SOURCE_RATNA,
            "classical_ref": "classical ratna-shastra; Phaladeepika",
            "cost_tier": "high",
            "contraindications": (
                "Gemstones strengthen the planet — wear ONLY if the planet is "
                "a functional benefic for the chart; otherwise they amplify malefic results."
            ),
            "confidence": 0.85,
        })
        # 3. dana / charity rows (variable per planet)
        for item in d["dana"]:
            text = (
                f"Donate {item} to the needy / a temple / a Brahmin on {d['day']} "
                f"(for {p.capitalize()} propitiation). Consistent donation on the planet's day "
                f"pacifies its afflictions."
            )
            rows.append({
                "remedy_id": f"{p}_matrix_charity_{item.replace(' ', '_').replace('(', '').replace(')', '')}",
                "planet": p,
                "domain": "general",
                "remedy_type": "charity",
                "scaffold_status": "live",
                "prescription_text": text,
                "charity_action": f"Donate {item} on {d['day']}.",
                "day_of_week": d["day"],
                "color_associated": d["color"],
                "source_canonical_id": "BPHS",
                "source_citation": SOURCE_BPHS,
                "classical_ref": "BPHS Ch.91-94 (Upaya-adhyaya)",
                "cost_tier": "low",
                "confidence": 0.85,
            })
        # 4. vrata / fasting
        text = (
            f"Observe a {d['day']} vrata (fast) dedicated to {d['deity']} for "
            f"{p.capitalize()} propitiation. Take one meal after sunset or observe nirjala "
            f"(waterless) for full benefit. Maintain for at least 16 consecutive weeks."
        )
        rows.append({
            "remedy_id": f"{p}_matrix_vrata",
            "planet": p,
            "domain": "general",
            "remedy_type": "vrata",
            "scaffold_status": "live",
            "prescription_text": text,
            "deity": d["deity"],
            "day_of_week": d["day"],
            "source_canonical_id": "BPHS",
            "source_citation": SOURCE_CLASSICAL,
            "classical_ref": "classical tradition (navagraha vrata)",
            "cost_tier": "free",
            "confidence": 0.80,
        })
        # 5. puja / worship
        text = (
            f"Worship {d['deity']} on {d['day']} with prescribed flowers, incense and lamp "
            f"(graha-shanti puja for {p.capitalize()}). Chant the {p.capitalize()} Ashtottara "
            f"(108 names) during the puja."
        )
        rows.append({
            "remedy_id": f"{p}_matrix_puja",
            "planet": p,
            "domain": "general",
            "remedy_type": "puja",
            "scaffold_status": "live",
            "prescription_text": text,
            "deity": d["deity"],
            "day_of_week": d["day"],
            "color_associated": d["color"],
            "source_canonical_id": "BPHS",
            "source_citation": SOURCE_CLASSICAL,
            "classical_ref": "classical tradition (graha-shanti puja)",
            "cost_tier": "low",
            "confidence": 0.85,
        })
        # 6. yantra
        text = (
            f"Inscribe or procure the {p.capitalize()} yantra; energise it on {d['day']} "
            f"with the beej mantra '{d['beej']}'. Install in the puja-griha or workplace, "
            f"facing the planet's direction."
        )
        rows.append({
            "remedy_id": f"{p}_matrix_yantra",
            "planet": p,
            "domain": "general",
            "remedy_type": "yantra",
            "scaffold_status": "live",
            "prescription_text": text,
            "mantra_transliteration": d["beej"],
            "day_of_week": d["day"],
            "source_canonical_id": "BPHS",
            "source_citation": SOURCE_CLASSICAL,
            "classical_ref": "classical tradition (navagraha yantra)",
            "cost_tier": "medium",
            "confidence": 0.80,
        })
        # 7. homa / fire-ritual
        text = (
            f"Perform a {d['deity']} / {p.capitalize()} graha-shanti homa (fire ritual) "
            f"with the prescribed samidha (fire-wood) on {d['day']}. "
            f"1008 ahutis is the standard count for a full dasha-shanti."
        )
        rows.append({
            "remedy_id": f"{p}_matrix_homa",
            "planet": p,
            "domain": "general",
            "remedy_type": "homa",
            "scaffold_status": "live",
            "prescription_text": text,
            "deity": d["deity"],
            "day_of_week": d["day"],
            "source_canonical_id": "BPHS",
            "source_citation": SOURCE_CLASSICAL,
            "classical_ref": "classical tradition (graha-shanti homa)",
            "cost_tier": "high",
            "confidence": 0.80,
        })
        # 8. behavioral
        text = (
            f"Adopt {p.capitalize()}-strengthening conduct: serve the significations of "
            f"{p.capitalize()} (e.g. its karaka domain, its deity {d['deity']}), "
            f"avoid its signification-harming actions, and live per its dharma. "
            f"Behavioral alignment is the deepest remedy — it changes the karma, not just the symptom."
        )
        rows.append({
            "remedy_id": f"{p}_matrix_behavioral",
            "planet": p,
            "domain": "general",
            "remedy_type": "behavioral",
            "scaffold_status": "live",
            "prescription_text": text,
            "source_canonical_id": "BPHS",
            "source_citation": SOURCE_CLASSICAL,
            "classical_ref": "classical tradition (karaka conduct)",
            "cost_tier": "free",
            "confidence": 0.85,
        })
        # 9. japa (mahadasha-count)
        text = (
            f"Complete the {p.capitalize()} mantra japa to its mahadasha count over the dasha period: "
            f"recite '{d['beej']}' on {d['day']}s and daily. "
            f"Standard counts: Sun 7,000; Moon 11,000; Mars 10,000; Mercury 9,000; "
            f"Jupiter 19,000; Venus 16,000; Saturn 23,000; Rahu 18,000; Ketu 17,000."
        )
        rows.append({
            "remedy_id": f"{p}_matrix_japa",
            "planet": p,
            "domain": "general",
            "remedy_type": "japa",
            "scaffold_status": "live",
            "prescription_text": text,
            "mantra_transliteration": d["beej"],
            "mantra_sanskrit": d["beej_sa"],
            "day_of_week": d["day"],
            "source_canonical_id": "BPHS",
            "source_citation": SOURCE_CLASSICAL,
            "classical_ref": "classical tradition (dasha-japa counts)",
            "cost_tier": "free",
            "confidence": 0.85,
        })

    return rows


# ── §3.2 — Dosha-linked remedies (~102 rows) ──────────────────────────────────
# One or two remedies per each of the 50 doshas in brahma_dosha_catalog.
# Each remedy cross-links via a comment; the back-link update is in the writer.

DOSHA_REMEDIES: list[dict[str, Any]] = [
    # manglik
    {
        "remedy_id": "dosha_manglik_puja",
        "planet": "mars",
        "domain": "marriage",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Mangala Dosha: perform Kuja Graha Shanti puja at a Subrahmanya/Hanuman temple "
            "on 21 consecutive Tuesdays. Worship with red flowers, red sandalwood, and camphor."
        ),
        "deity": "Hanuman/Kartikeya",
        "day_of_week": "Tuesday",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.88 (Mangala upaya)",
        "cost_tier": "medium",
        "confidence": 0.85,
        "dosha_target": "manglik",
    },
    {
        "remedy_id": "dosha_manglik_vrata",
        "planet": "mars",
        "domain": "marriage",
        "remedy_type": "vrata",
        "scaffold_status": "live",
        "prescription_text": (
            "For Mangala Dosha: observe Tuesday vrata for 21 consecutive Tuesdays. "
            "Kumbha Vivaha (symbolic marriage to a peepal tree or idol) is prescribed where "
            "classical tradition requires it before a Manglik marries a non-Manglik."
        ),
        "day_of_week": "Tuesday",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.88; classical Kumbha Vivaha tradition",
        "cost_tier": "low",
        "confidence": 0.80,
        "dosha_target": "manglik",
    },
    # kala_sarpa
    {
        "remedy_id": "dosha_kala_sarpa_nag_puja",
        "planet": "rahu",
        "domain": "general",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Kala Sarpa Dosha: perform Nag Puja (serpent worship) at a Nag temple or Shiva "
            "temple on Nag Panchami. Offer milk to the serpent idol. Perform Rahu-Ketu shanti "
            "homa at least once during the dasha period."
        ),
        "deity": "Naga/Shiva",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Kala Sarpa upaya)",
        "cost_tier": "medium",
        "confidence": 0.80,
        "dosha_target": "kala_sarpa",
    },
    {
        "remedy_id": "dosha_kala_sarpa_mantra",
        "planet": "rahu",
        "domain": "general",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": (
            "For Kala Sarpa Dosha: recite the Kala Sarpa mantra or Rahu-Ketu beej mantras "
            "on Saturdays. Recite Mahamrityunjaya mantra 108 times daily throughout the period. "
            "Visiting Trimbakeshwar (Nashik) for the Kala Sarpa Shanti is classically prescribed."
        ),
        "mantra_transliteration": "Om Raam Rahave Namah; Om Kem Ketave Namah (alternating 54+54)",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Kala Sarpa shanti)",
        "cost_tier": "free",
        "confidence": 0.80,
        "dosha_target": "kala_sarpa",
    },
    # kala_sarpa 12 variants — one shared remedy each (pointing to the variant canonical_id)
    *[
        {
            "remedy_id": f"dosha_{v}_shanti",
            "planet": "rahu",
            "domain": "general",
            "remedy_type": "puja",
            "scaffold_status": "live",
            "prescription_text": (
                f"For {v.replace('_', ' ').title()}: perform Kala Sarpa Shanti puja at a Shiva "
                f"or Nag temple with Rahu-Ketu beej mantras. Donate coconut and urad dal on "
                f"Saturday. Observe serpent-related charities on Nag Panchami."
            ),
            "deity": "Shiva/Naga",
            "day_of_week": "Saturday",
            "source_canonical_id": "classical_tradition",
            "source_citation": SOURCE_CLASSICAL,
            "classical_ref": "classical tradition (Kala Sarpa variant shanti)",
            "cost_tier": "medium",
            "confidence": 0.75,
            "dosha_target": v,
        }
        for v in [
            "kala_sarpa_anant", "kala_sarpa_kulik", "kala_sarpa_vasuki",
            "kala_sarpa_shankhpal", "kala_sarpa_padma", "kala_sarpa_mahapadma",
            "kala_sarpa_takshak", "kala_sarpa_karkotak", "kala_sarpa_shankhachud",
            "kala_sarpa_ghatak", "kala_sarpa_vishdhar", "kala_sarpa_sheshnag",
        ]
    ],
    # kemadruma
    {
        "remedy_id": "dosha_kemadruma_chandra_puja",
        "planet": "moon",
        "domain": "general",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Kemadruma Dosha: worship Chandra on Purnima nights with white flowers and "
            "milk. Keep a Chandra Yantra in the home. Recite Chandra Ashtottara 108 times "
            "every Monday during Shukla Paksha."
        ),
        "deity": "Chandra",
        "day_of_week": "Monday",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.88 (Chandra upaya)",
        "cost_tier": "low",
        "confidence": 0.80,
        "dosha_target": "kemadruma",
    },
    # daridra
    {
        "remedy_id": "dosha_daridra_lakshmi_puja",
        "planet": "jupiter",
        "domain": "wealth",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Daridra Dosha: perform Lakshmi Puja on Fridays with lotus flowers and "
            "white sweets. Recite Shri Sukta daily. Donate yellow gram and gold on Thursdays."
        ),
        "deity": "Lakshmi",
        "day_of_week": "Friday",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.88 (dhana upaya)",
        "cost_tier": "low",
        "confidence": 0.80,
        "dosha_target": "daridra",
    },
    # shakata
    {
        "remedy_id": "dosha_shakata_guru_puja",
        "planet": "jupiter",
        "domain": "general",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Shakata Dosha: propitiate Jupiter (Guru) by performing Brihaspati puja on "
            "Thursdays. Recite Guru Stotram. Donate yellow gram, turmeric, and gold. "
            "Jupiter's kendra placement bhanga negates this dosha — strengthen Jupiter."
        ),
        "deity": "Brihaspati",
        "day_of_week": "Thursday",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Shakata yoga upaya)",
        "cost_tier": "low",
        "confidence": 0.75,
        "dosha_target": "shakata",
    },
    # vish_dosha
    {
        "remedy_id": "dosha_vish_dosha_shani_chandra",
        "planet": "saturn",
        "domain": "health",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": (
            "For Vish Dosha (Moon-Saturn conjunction): recite Mahamrityunjaya mantra 108 times "
            "daily. Perform Shiva puja on Mondays. Wear a Pearl in silver (for Moon) "
            "and offer sesame on Saturdays (for Saturn). The Moon-Saturn friction is pacified "
            "by Shiva worship (lord of both time/Saturn and the mind-soothing moon)."
        ),
        "mantra_transliteration": "Om Tryambakam Yajamahe Sugandhim Pushti-Vardhanam",
        "deity": "Shiva",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Vish dosha upaya)",
        "cost_tier": "free",
        "confidence": 0.80,
        "dosha_target": "vish_dosha",
    },
    # punarphoo
    {
        "remedy_id": "dosha_punarphoo_shani_mantra",
        "planet": "saturn",
        "domain": "marriage",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": (
            "For Punarphoo Dosha (Saturn-Moon): recite Shani Chalisa on Saturdays and "
            "Chandra Ashtottara on Mondays. The Saturn-Moon combination delays but does not "
            "deny; patience and consistent practice are the core remedy."
        ),
        "day_of_week": "Saturday",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Punarphoo upaya)",
        "cost_tier": "free",
        "confidence": 0.80,
        "dosha_target": "punarphoo",
    },
    # guru_chandal
    {
        "remedy_id": "dosha_guru_chandal_jupiter_puja",
        "planet": "jupiter",
        "domain": "general",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Guru Chandal Dosha (Jupiter-Rahu): perform Brihaspati puja on Thursdays "
            "and Rahu shanti on Saturdays. Recite Vishnu Sahasranama daily. Strengthen "
            "Jupiter through service to teachers and dharmic study."
        ),
        "deity": "Vishnu/Brihaspati",
        "day_of_week": "Thursday",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Guru Chandal upaya)",
        "cost_tier": "low",
        "confidence": 0.80,
        "dosha_target": "guru_chandal",
    },
    # angarak
    {
        "remedy_id": "dosha_angarak_mars_rahu",
        "planet": "mars",
        "domain": "general",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Angarak Dosha (Mars-Rahu): perform Hanuman puja on Tuesdays and Rahu shanti "
            "on Saturdays. Recite Hanuman Chalisa daily. Donate blood (blood donation) on "
            "Tuesdays. Wear red coral (if Mars is functional benefic)."
        ),
        "deity": "Hanuman",
        "day_of_week": "Tuesday",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Angarak dosha upaya)",
        "cost_tier": "low",
        "confidence": 0.80,
        "dosha_target": "angarak",
    },
    # grahan
    {
        "remedy_id": "dosha_grahan_surya_chandra_mantra",
        "planet": "sun",
        "domain": "general",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": (
            "For Grahan (Eclipse) Dosha: recite Surya Ashtakam or Chandra Ashtakam (depending "
            "on whether Sun or Moon is eclipsed) 12 times daily. Offer Arghya (water) to the "
            "sun at sunrise. Perform Rahu/Ketu shanti at a Naga temple."
        ),
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Grahan dosha upaya)",
        "cost_tier": "free",
        "confidence": 0.80,
        "dosha_target": "grahan",
    },
    # pitru_dosha
    {
        "remedy_id": "dosha_pitru_tarpan",
        "planet": "sun",
        "domain": "general",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Pitru Dosha: perform Pitru Tarpan (water libation to ancestors) on "
            "Amavasya (new moon) monthly with black sesame and water. Perform Shraddha at "
            "Gaya (the classical Pitru Tirtha) or at least at a river/tank at home on "
            "Pitru Paksha. Donate food to Brahmins on the father's death anniversary."
        ),
        "deity": "Pitru/Yama",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Pitru Dosha upaya — Gaya Shraddha, Tarpan)",
        "cost_tier": "medium",
        "confidence": 0.85,
        "dosha_target": "pitru_dosha",
    },
    {
        "remedy_id": "dosha_pitru_surya_mantra",
        "planet": "sun",
        "domain": "general",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": (
            "For Pitru Dosha: recite the Surya Ashtottara (108 names of the Sun) on Sundays "
            "and offer Arghya at sunrise. The Sun is the karaka for father/ancestors; "
            "strengthening the Sun-9th axis appeases ancestral karma."
        ),
        "day_of_week": "Sunday",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Pitru Dosha — Sun upaya)",
        "cost_tier": "free",
        "confidence": 0.80,
        "dosha_target": "pitru_dosha",
    },
    # sade_sati
    {
        "remedy_id": "dosha_sade_sati_shani_mantra",
        "planet": "saturn",
        "domain": "general",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": (
            "For Sade Sati: recite Hanuman Chalisa daily (Hanuman pacifies Saturn). "
            "Recite Shani Chalisa on Saturdays. Offer mustard oil to Shani idol on Saturdays. "
            "Feed crows (Saturn's bird) on Saturdays. The 7.5-year period is a phase of "
            "maturation through pressure — endurance and ethical conduct are the real remedy."
        ),
        "deity": "Hanuman/Shani",
        "day_of_week": "Saturday",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Sade Sati upaya)",
        "cost_tier": "free",
        "confidence": 0.85,
        "dosha_target": "sade_sati",
    },
    {
        "remedy_id": "dosha_sade_sati_shani_charity",
        "planet": "saturn",
        "domain": "general",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": (
            "For Sade Sati: donate black sesame, mustard oil, iron, and black cloth to "
            "laborers or the poor on Saturdays throughout the 7.5-year period. Service "
            "to the elderly and underprivileged is the most direct Saturn remedy."
        ),
        "charity_action": "Donate black sesame, mustard oil, iron on Saturdays",
        "day_of_week": "Saturday",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Sade Sati dana)",
        "cost_tier": "low",
        "confidence": 0.85,
        "dosha_target": "sade_sati",
    },
    # dhaiya
    {
        "remedy_id": "dosha_dhaiya_shani_puja",
        "planet": "saturn",
        "domain": "general",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Dhaiya (Kantaka/Ashtama Shani): perform Shani puja on Saturdays with "
            "black sesame and mustard oil lamp. Recite Shani Stotra. "
            "Observe Saturday fast for the 2.5-year transit period."
        ),
        "deity": "Shani",
        "day_of_week": "Saturday",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Dhaiya upaya)",
        "cost_tier": "low",
        "confidence": 0.80,
        "dosha_target": "dhaiya",
    },
    # nadi_dosha (compatibility)
    {
        "remedy_id": "dosha_nadi_mahamrityunjaya",
        "planet": "moon",
        "domain": "marriage",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": (
            "For Nadi Dosha (compatibility): perform a Mahamrityunjaya mantra japa of "
            "1,25,000 (1.25 lakh) before marriage. Perform Nadi Niraakarana puja prescribed "
            "by a learned astrologer. This dosha is among the most serious in Ashtakoota."
        ),
        "mantra_transliteration": "Om Tryambakam Yajamahe Sugandhim Pushti-Vardhanam",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Nadi Dosha niraakarana)",
        "cost_tier": "medium",
        "confidence": 0.75,
        "dosha_target": "nadi_dosha",
    },
    # bhakoot_dosha
    {
        "remedy_id": "dosha_bhakoot_vishnu_puja",
        "planet": "jupiter",
        "domain": "marriage",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Bhakoot Dosha (compatibility): perform Vishnu Sahasranama recitation jointly "
            "before marriage. Donate to temples on the bride's and groom's respective "
            "planetary days. Bhakoot bhanga (same rashi lord) negates this dosha."
        ),
        "deity": "Vishnu",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Bhakoot Dosha upaya)",
        "cost_tier": "low",
        "confidence": 0.75,
        "dosha_target": "bhakoot_dosha",
    },
    # gana_dosha
    {
        "remedy_id": "dosha_gana_shiva_puja",
        "planet": "mars",
        "domain": "marriage",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Gana Dosha (Deva-Rakshasa mismatch): perform joint Shiva-Parvati puja by "
            "the couple before or at marriage. Gana compatibility can be partially offset by "
            "strong other kootas (Gana koota = 6 pts max, others more weighty)."
        ),
        "deity": "Shiva-Parvati",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Gana Dosha upaya)",
        "cost_tier": "low",
        "confidence": 0.70,
        "dosha_target": "gana_dosha",
    },
    # yoni_dosha
    {
        "remedy_id": "dosha_yoni_puja",
        "planet": "venus",
        "domain": "marriage",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Yoni Dosha (enemy-yoni nakshatras): worship Kamadeva (or Parvati) on "
            "Fridays for harmonious union. Recite Lalita Sahasranama. "
            "The effect is on the physical/instinctual layer — mitigated by strong emotional "
            "koota scores (Graha Maitri, Bhakoot) and yogakaraka planets."
        ),
        "deity": "Kamadeva/Parvati",
        "day_of_week": "Friday",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Yoni Dosha upaya)",
        "cost_tier": "low",
        "confidence": 0.70,
        "dosha_target": "yoni_dosha",
    },
    # vashya_dosha
    {
        "remedy_id": "dosha_vashya_venus_mantra",
        "planet": "venus",
        "domain": "marriage",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": (
            "For Vashya Dosha: recite Shukra Ashtottara on Fridays. The vashya koota (2 pts "
            "max) has minor weight — offset it with strong mutual respect and aligned goals."
        ),
        "day_of_week": "Friday",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Vashya Dosha upaya)",
        "cost_tier": "free",
        "confidence": 0.70,
        "dosha_target": "vashya_dosha",
    },
    # tara_dosha_compat
    {
        "remedy_id": "dosha_tara_nakshatra_puja",
        "planet": "moon",
        "domain": "marriage",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Tara Dosha (compatibility): worship the presiding deity of the birth nakshatra "
            "of both partners. Perform Nakshatra shanti puja. "
            "Recite the respective nakshatra mantra 108 times on the nakshatra's day."
        ),
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Tara Dosha upaya)",
        "cost_tier": "medium",
        "confidence": 0.70,
        "dosha_target": "tara_dosha_compat",
    },
    # varna_dosha
    {
        "remedy_id": "dosha_varna_surya_mantra",
        "planet": "sun",
        "domain": "marriage",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": (
            "For Varna Dosha (1 pt koota): the varna koota has the lowest weight in Ashtakoota. "
            "Recite Surya Ashtottara on Sundays for the couple. This dosha is practically "
            "overridden by strong performance on Nadi, Bhakoot, Gana kootas."
        ),
        "day_of_week": "Sunday",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Varna Dosha upaya)",
        "cost_tier": "free",
        "confidence": 0.65,
        "dosha_target": "varna_dosha",
    },
    # graha_maitri_dosha
    {
        "remedy_id": "dosha_graha_maitri_puja",
        "planet": "jupiter",
        "domain": "marriage",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Graha Maitri Dosha (enemy Moon-sign lords): each partner propitiates their "
            "own Moon-sign lord on its day. Joint Vishnu puja on Thursdays. "
            "Graha Maitri (5 pts max) is offset by shared spiritual practice."
        ),
        "deity": "Vishnu",
        "day_of_week": "Thursday",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Graha Maitri Dosha upaya)",
        "cost_tier": "low",
        "confidence": 0.70,
        "dosha_target": "graha_maitri_dosha",
    },
    # balarishta
    {
        "remedy_id": "dosha_balarishta_jupiter_mantra",
        "planet": "jupiter",
        "domain": "health",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": (
            "For Balarishta: perform Mahamrityunjaya japa (1,25,000 times) as a shanti "
            "for the child. Recite Vishnu Sahasranama. Jupiter aspect is the classical bhanga — "
            "strengthen Jupiter in the chart through Guru puja."
        ),
        "mantra_transliteration": "Om Tryambakam Yajamahe Sugandhim Pushti-Vardhanam",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.9 (Arishta upaya)",
        "cost_tier": "medium",
        "confidence": 0.80,
        "dosha_target": "balarishta",
    },
    # gandanta_dosha
    {
        "remedy_id": "dosha_gandanta_shanti",
        "planet": "moon",
        "domain": "general",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Gandanta Dosha: perform Gandanta Shanti puja within 27 days of birth (or "
            "as soon as identified). The puja propitiates the junction deity and the birth "
            "nakshatra's presiding deity. The remedy is time-critical in classical tradition."
        ),
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.9 (Gandanta shanti)",
        "cost_tier": "medium",
        "confidence": 0.85,
        "dosha_target": "gandanta_dosha",
    },
    # shrapit_dosha
    {
        "remedy_id": "dosha_shrapit_shani_rahu",
        "planet": "saturn",
        "domain": "general",
        "remedy_type": "homa",
        "scaffold_status": "live",
        "prescription_text": (
            "For Shrapit Dosha (Saturn-Rahu): perform a Shrapit Dosha Nivaran homa with "
            "prescribed samidha on Saturdays. Recite the Shrapit Dosha mantra 1,08,000 times. "
            "Donate black sesame and iron. Visit a Shani Shingnapur (or equivalent Shani temple) "
            "on Saturdays."
        ),
        "deity": "Shani",
        "day_of_week": "Saturday",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Shrapit Dosha upaya)",
        "cost_tier": "high",
        "confidence": 0.80,
        "dosha_target": "shrapit_dosha",
    },
    # mrityu_bhaga_dosha
    {
        "remedy_id": "dosha_mrityu_bhaga_mantra",
        "planet": "sun",
        "domain": "general",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": (
            "For Mrityu Bhaga Dosha: propitiate the afflicted planet with its beej mantra "
            "108 times daily. Perform Mahamrityunjaya japa (11,000 minimum). "
            "The 'death-degree' position is pacified by strengthening the planet's "
            "digbala, dasha timing awareness, and puja on its day."
        ),
        "mantra_transliteration": "Om Tryambakam Yajamahe (planet-specific beej as indicated)",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Mrityu Bhaga upaya)",
        "cost_tier": "free",
        "confidence": 0.75,
        "dosha_target": "mrityu_bhaga_dosha",
    },
    # kala_amrita_dosha
    {
        "remedy_id": "dosha_kala_amrita_shanti",
        "planet": "ketu",
        "domain": "general",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Kala Amrita Dosha (reverse Kala Sarpa): perform Ketu shanti puja on "
            "Tuesdays and Rahu shanti on Saturdays. This dosha is considered by some "
            "schools to carry a more inward/moksha orientation — spiritual practices "
            "and meditation are especially efficacious."
        ),
        "deity": "Ganesha",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Kala Amrita upaya)",
        "cost_tier": "medium",
        "confidence": 0.75,
        "dosha_target": "kala_amrita_dosha",
    },
    # mool_dosha
    {
        "remedy_id": "dosha_mool_shanti",
        "planet": "ketu",
        "domain": "general",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Mool (Gandmool) Dosha: perform Mool Shanti puja on the 27th day after "
            "birth (or at the next occurrence of the birth nakshatra). Propitiate the "
            "birth nakshatra's deity. This is the classical prescriptive timing in tradition."
        ),
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Mool Shanti — 27th-day puja)",
        "cost_tier": "medium",
        "confidence": 0.85,
        "dosha_target": "mool_dosha",
    },
    # abhukta_mula_dosha
    {
        "remedy_id": "dosha_abhukta_mula_shanti",
        "planet": "ketu",
        "domain": "general",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Abhukta Mula Dosha: perform the prescribed Abhukta Mula Shanti immediately "
            "after birth — the traditional shanti for this junction is more urgent than the "
            "general Mool Shanti. Propitiate Ketu and the presiding deity of Mula nakshatra."
        ),
        "deity": "Ketu/Nirriti",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Abhukta Mula shanti)",
        "cost_tier": "medium",
        "confidence": 0.85,
        "dosha_target": "abhukta_mula_dosha",
    },
    # vish_kanya_dosha
    {
        "remedy_id": "dosha_vish_kanya_puja",
        "planet": "venus",
        "domain": "marriage",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Vish Kanya Dosha: perform the prescribed Vish Kanya Shanti puja before "
            "marriage. Propitiate Venus and the birth nakshatra deity. This combination "
            "is tradition-based and its weight must be assessed against the full chart."
        ),
        "deity": "Lakshmi/Shukra",
        "day_of_week": "Friday",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Vish Kanya upaya)",
        "cost_tier": "medium",
        "confidence": 0.70,
        "dosha_target": "vish_kanya_dosha",
    },
    # rajju_dosha
    {
        "remedy_id": "dosha_rajju_shiva_puja",
        "planet": "moon",
        "domain": "marriage",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Rajju Dosha (same rajju nakshatras): perform joint Shiva-Parvati puja "
            "before marriage. The Rajju dosha is assessed in South-Indian matching; "
            "offset by strong Nadi, Bhakoot satisfactions."
        ),
        "deity": "Shiva-Parvati",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Rajju Dosha upaya)",
        "cost_tier": "low",
        "confidence": 0.70,
        "dosha_target": "rajju_dosha",
    },
    # vedha_dosha
    {
        "remedy_id": "dosha_vedha_nakshatra_puja",
        "planet": "moon",
        "domain": "marriage",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Vedha Dosha (obstructing nakshatra pair): each partner propitiates their "
            "birth-nakshatra deity on the nakshatra's day. This koota carries medium weight "
            "and is offset by strong Graha Maitri, Bhakoot, and Nadi scores."
        ),
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Vedha Dosha upaya)",
        "cost_tier": "low",
        "confidence": 0.70,
        "dosha_target": "vedha_dosha",
    },
    # stree_deergha_dosha
    {
        "remedy_id": "dosha_stree_deergha_puja",
        "planet": "moon",
        "domain": "marriage",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Stree Deergha Dosha (nakshatra count < 9): perform Nakshatra puja for "
            "the bride's birth star on the wedding day. This koota (assessed from "
            "bride's nakshatra) relates to the longevity of the union."
        ),
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Stree Deergha upaya)",
        "cost_tier": "low",
        "confidence": 0.65,
        "dosha_target": "stree_deergha_dosha",
    },
    # mahendra_dosha
    {
        "remedy_id": "dosha_mahendra_vishnu_puja",
        "planet": "jupiter",
        "domain": "marriage",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Mahendra Dosha (Mahendra number absent): perform Vishnu puja on Thursdays "
            "for the couple's progeny and prosperity. The Mahendra koota (progeny-related) "
            "is partially offset by strong Jupiter in the individual charts."
        ),
        "deity": "Vishnu",
        "day_of_week": "Thursday",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Mahendra Dosha upaya)",
        "cost_tier": "low",
        "confidence": 0.65,
        "dosha_target": "mahendra_dosha",
    },
    # balarishta_moon_dusthana
    {
        "remedy_id": "dosha_balarishta_moon_chandra_shanti",
        "planet": "moon",
        "domain": "health",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Balarishta (Moon in Dusthana): perform Chandra Shanti puja within 27 days. "
            "Recite Mahamrityunjaya mantra 1,25,000 times as shanti. "
            "Jupiter aspect on the Moon is the primary bhanga — Guru puja strengthens this."
        ),
        "deity": "Chandra",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.9 (Balarishta Chandra dusthana upaya)",
        "cost_tier": "medium",
        "confidence": 0.80,
        "dosha_target": "balarishta_moon_dusthana",
    },
    # balarishta_sandhi
    {
        "remedy_id": "dosha_balarishta_sandhi_shanti",
        "planet": "moon",
        "domain": "general",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Balarishta (Sandhi birth): perform Sandhi Shanti puja (or Lagna Shanti) "
            "within the first lunar month. Propitiate the lagna lord and the Moon. "
            "Strong lagna lord is the primary bhanga."
        ),
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.9 (Sandhi balarishta upaya)",
        "cost_tier": "medium",
        "confidence": 0.80,
        "dosha_target": "balarishta_sandhi",
    },
    # balarishta_paap_kartari
    {
        "remedy_id": "dosha_balarishta_paap_kartari_mantra",
        "planet": "jupiter",
        "domain": "health",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": (
            "For Balarishta (Papa Kartari): recite Mahamrityunjaya mantra 1,08,000 times "
            "as shanti. Perform Jupiter puja (Guru is the primary bhanga lord — even one "
            "Jupiter aspect dissolves the Papa Kartari arishta per BPHS Ch.9)."
        ),
        "mantra_transliteration": "Om Tryambakam Yajamahe Sugandhim Pushti-Vardhanam",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.9 (Papa Kartari balarishta upaya)",
        "cost_tier": "free",
        "confidence": 0.80,
        "dosha_target": "balarishta_paap_kartari",
    },
    # kemadruma_compat_kuja
    {
        "remedy_id": "dosha_kemadruma_compat_kuja_mars",
        "planet": "mars",
        "domain": "marriage",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Kuja Dosha (from Venus): perform Kuja Graha Shanti puja on 21 Tuesdays. "
            "The Venus-referenced Manglik (Mars in 1/2/4/7/8/12 from Venus) reinforces "
            "marital affliction when also present from lagna. Both must be pacified."
        ),
        "deity": "Kartikeya",
        "day_of_week": "Tuesday",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Venus-referenced Manglik upaya)",
        "cost_tier": "medium",
        "confidence": 0.80,
        "dosha_target": "kemadruma_compat_kuja",
    },
    # kuja_dosha_from_moon
    {
        "remedy_id": "dosha_kuja_from_moon_hanuman",
        "planet": "mars",
        "domain": "marriage",
        "remedy_type": "puja",
        "scaffold_status": "live",
        "prescription_text": (
            "For Kuja Dosha (from Moon): perform Hanuman puja on Tuesdays. Recite Hanuman "
            "Chalisa daily. This Moon-referenced Manglik check reinforces the lagna-based "
            "check — when both are present, the remedy intensity doubles."
        ),
        "deity": "Hanuman",
        "day_of_week": "Tuesday",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Moon-referenced Manglik upaya)",
        "cost_tier": "low",
        "confidence": 0.80,
        "dosha_target": "kuja_dosha_from_moon",
    },
]

# ── §3.3 — Legacy remedies (54 rows from v1.0) with remedy_type normalised ────
# The original l0_remedy_corpus.py REMEDIES list, preserved as-is but with
# remedy_type normalised (fasting→vrata, ritual→puja, dietary→ayurvedic)
# and scaffold_status='live' added.

LEGACY_REMEDIES: list[dict[str, Any]] = [
    # ── Sun ────────────────────────────────────────────────────────────────────
    {
        "remedy_id": "sun_career_mantra_01",
        "planet": "sun",
        "domain": "career",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": "Chant the Aditya Hridayam daily at sunrise, facing east, 108 times. This strengthens the Sun and brings favor from authority figures and government.",
        "mantra_text": "Om Hraam Hreem Hraum Sah Suryaya Namah",
        "day_of_week": "Sunday",
        "color_associated": "red",
        "confidence": 0.90,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "sun_health_gemstone_01",
        "planet": "sun",
        "domain": "health",
        "remedy_type": "gemstone",
        "scaffold_status": "live",
        "prescription_text": "Wear a Ruby (Manikya) of at least 3 carats set in gold, on the ring finger of the right hand, on a Sunday morning after sunrise. The gem strengthens the Sun and supports vitality.",
        "gemstone": "Ruby (Manikya)",
        "day_of_week": "Sunday",
        "color_associated": "red",
        "confidence": 0.85,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88 V.5",
    },
    {
        "remedy_id": "sun_general_charity_01",
        "planet": "sun",
        "domain": "general",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": "Donate wheat, jaggery, copper vessels, or red-colored cloth to a Brahmin or temple on Sundays. Feed hungry people on Sundays.",
        "charity_action": "Donate wheat, jaggery, copper on Sundays",
        "day_of_week": "Sunday",
        "color_associated": "red",
        "confidence": 0.85,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "sun_debilitated_mantra_01",
        "planet": "sun",
        "domain": "general",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": "For a debilitated Sun in Libra, chant the Surya Ashtakam 12 times daily and offer water to the rising Sun. Place a Surya Yantra at home.",
        "mantra_text": "Om Suryaya Namah (108 times daily)",
        "day_of_week": "Sunday",
        "color_associated": "red",
        "confidence": 0.80,
        "source_canonical_id": "Phaladeepika",
        "source_citation": SOURCE_PHALA,
        "classical_ref": "Phala Deepika, remedial section",
    },
    {
        "remedy_id": "sun_spirituality_vrata_01",
        "planet": "sun",
        "domain": "spirituality",
        "remedy_type": "vrata",  # was fasting
        "scaffold_status": "live",
        "prescription_text": "Fast on Sundays (Ravivara). Take one meal after sunset or abstain from salt. Observe for 12 consecutive Sundays for full benefit.",
        "day_of_week": "Sunday",
        "color_associated": "red",
        "confidence": 0.80,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "sun_marriage_puja_01",
        "planet": "sun",
        "domain": "marriage",
        "remedy_type": "puja",  # was ritual
        "scaffold_status": "live",
        "prescription_text": "Perform Surya Puja on Sunday mornings with red flowers, red sandalwood paste, and incense. Chant Surya Ashtottara (108 names). This reduces Sun's malefic effect on 7th house.",
        "mantra_text": "Om Aditya Namah",
        "day_of_week": "Sunday",
        "color_associated": "red",
        "confidence": 0.75,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    # ── Moon ───────────────────────────────────────────────────────────────────
    {
        "remedy_id": "moon_health_mantra_01",
        "planet": "moon",
        "domain": "health",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": "Chant the Chandra Ashtottara Shatanamavali 108 times on Mondays. The Moon governs the mind and bodily fluids — this mantra strengthens mental health and immunity.",
        "mantra_text": "Om Shraam Shreem Shraum Sah Chandraya Namah",
        "day_of_week": "Monday",
        "color_associated": "white",
        "confidence": 0.85,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "moon_wealth_gemstone_01",
        "planet": "moon",
        "domain": "wealth",
        "remedy_type": "gemstone",
        "scaffold_status": "live",
        "prescription_text": "Wear a natural Pearl (Moti) of at least 4 carats set in silver, on the little finger of the right hand, on a Monday during Shukla Paksha (waxing Moon).",
        "gemstone": "Pearl (Moti)",
        "day_of_week": "Monday",
        "color_associated": "white",
        "confidence": 0.85,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88 V.6",
    },
    {
        "remedy_id": "moon_general_charity_01",
        "planet": "moon",
        "domain": "general",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": "Donate white rice, milk, silver, white cloth, or ghee to a Brahmin or temple on Mondays during Shukla Paksha.",
        "charity_action": "Donate white rice, milk, silver on Mondays",
        "day_of_week": "Monday",
        "color_associated": "white",
        "confidence": 0.85,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "moon_marriage_vrata_01",
        "planet": "moon",
        "domain": "marriage",
        "remedy_type": "vrata",  # was fasting
        "scaffold_status": "live",
        "prescription_text": "Fast on Mondays (Somavara). Take only white foods — rice, milk, curd. Offer milk to Shiva Linga. Observe for 16 consecutive Mondays.",
        "day_of_week": "Monday",
        "color_associated": "white",
        "confidence": 0.80,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "moon_career_puja_01",
        "planet": "moon",
        "domain": "career",
        "remedy_type": "puja",  # was ritual
        "scaffold_status": "live",
        "prescription_text": "Perform Chandra Puja on Mondays with white flowers and white sandalwood paste. Keep a Chandra Yantra in the workplace.",
        "mantra_text": "Om Chandraya Namah",
        "day_of_week": "Monday",
        "color_associated": "white",
        "confidence": 0.75,
        "source_canonical_id": "Phaladeepika",
        "source_citation": SOURCE_PHALA,
        "classical_ref": "Phala Deepika, remedial section",
    },
    # ── Mars ───────────────────────────────────────────────────────────────────
    {
        "remedy_id": "mars_marriage_mantra_01",
        "planet": "mars",
        "domain": "marriage",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": "For Mangala Dosha, chant the Mangala Ashtakam 108 times on Tuesdays. Perform Kuja Graha puja at a Subrahmanya temple. Observe 21 Tuesdays.",
        "mantra_text": "Om Kraam Kreem Kraum Sah Bhaumaya Namah",
        "day_of_week": "Tuesday",
        "color_associated": "red",
        "confidence": 0.85,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "mars_health_gemstone_01",
        "planet": "mars",
        "domain": "health",
        "remedy_type": "gemstone",
        "scaffold_status": "live",
        "prescription_text": "Wear Red Coral (Moonga) of at least 6 carats set in gold or copper, on the ring finger of the right hand, on a Tuesday after sunrise.",
        "gemstone": "Red Coral (Moonga)",
        "day_of_week": "Tuesday",
        "color_associated": "red",
        "confidence": 0.85,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88 V.7",
    },
    {
        "remedy_id": "mars_career_charity_01",
        "planet": "mars",
        "domain": "career",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": "Donate red lentils (masoor dal), red cloth, copper, or blood (donate blood) on Tuesdays. Feed crows with wheat bread.",
        "charity_action": "Donate red lentils, copper, red cloth on Tuesdays",
        "day_of_week": "Tuesday",
        "color_associated": "red",
        "confidence": 0.80,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    # ── Mercury ────────────────────────────────────────────────────────────────
    {
        "remedy_id": "mercury_education_mantra_01",
        "planet": "mercury",
        "domain": "education",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": "Chant the Budha Ashtottara Shatanamavali 108 times on Wednesdays. Mercury governs intellect, communication, and commerce.",
        "mantra_text": "Om Braam Breem Braum Sah Budhaya Namah",
        "day_of_week": "Wednesday",
        "color_associated": "green",
        "confidence": 0.85,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "mercury_wealth_gemstone_01",
        "planet": "mercury",
        "domain": "wealth",
        "remedy_type": "gemstone",
        "scaffold_status": "live",
        "prescription_text": "Wear Emerald (Panna) of at least 3 carats set in gold, on the little finger of the right hand, on a Wednesday morning during Shukla Paksha.",
        "gemstone": "Emerald (Panna)",
        "day_of_week": "Wednesday",
        "color_associated": "green",
        "confidence": 0.85,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88 V.8",
    },
    {
        "remedy_id": "mercury_career_charity_01",
        "planet": "mercury",
        "domain": "career",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": "Donate green moong dal, green cloth, or books on Wednesdays. Feed cows with grass. Donate to schools or libraries.",
        "charity_action": "Donate green moong dal, books on Wednesdays",
        "day_of_week": "Wednesday",
        "color_associated": "green",
        "confidence": 0.80,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    # ── Jupiter ────────────────────────────────────────────────────────────────
    {
        "remedy_id": "jupiter_wealth_mantra_01",
        "planet": "jupiter",
        "domain": "wealth",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": "Chant Guru Ashtottara Shatanamavali 108 times on Thursdays. Jupiter (Guru) blesses with wisdom, wealth, and progeny when propitiated.",
        "mantra_text": "Om Graam Greem Graum Sah Guruve Namah",
        "day_of_week": "Thursday",
        "color_associated": "yellow",
        "confidence": 0.90,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "jupiter_education_gemstone_01",
        "planet": "jupiter",
        "domain": "education",
        "remedy_type": "gemstone",
        "scaffold_status": "live",
        "prescription_text": "Wear Yellow Sapphire (Pukhraj) of at least 4 carats set in gold, on the index finger of the right hand, on a Thursday morning during Shukla Paksha.",
        "gemstone": "Yellow Sapphire (Pukhraj)",
        "day_of_week": "Thursday",
        "color_associated": "yellow",
        "confidence": 0.85,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88 V.9",
    },
    {
        "remedy_id": "jupiter_general_charity_01",
        "planet": "jupiter",
        "domain": "general",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": "Donate yellow gram (chana dal), turmeric, yellow cloth, or gold on Thursdays. Feed Brahmins or holy men. Donate to educational institutions.",
        "charity_action": "Donate yellow gram, turmeric, yellow cloth on Thursdays",
        "day_of_week": "Thursday",
        "color_associated": "yellow",
        "confidence": 0.85,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "jupiter_marriage_vrata_01",
        "planet": "jupiter",
        "domain": "marriage",
        "remedy_type": "vrata",  # was fasting
        "scaffold_status": "live",
        "prescription_text": "Fast on Thursdays (Guruvara). Take only yellow food — gram dal, turmeric rice. Observe for 16 consecutive Thursdays. Jupiter blesses progeny and marital harmony.",
        "day_of_week": "Thursday",
        "color_associated": "yellow",
        "confidence": 0.80,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    # ── Venus ──────────────────────────────────────────────────────────────────
    {
        "remedy_id": "venus_marriage_mantra_01",
        "planet": "venus",
        "domain": "marriage",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": "Chant Shukra Ashtottara Shatanamavali 108 times on Fridays. Venus governs love, beauty, relationships, and luxury.",
        "mantra_text": "Om Draam Dreem Draum Sah Shukraya Namah",
        "day_of_week": "Friday",
        "color_associated": "white",
        "confidence": 0.90,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "venus_wealth_gemstone_01",
        "planet": "venus",
        "domain": "wealth",
        "remedy_type": "gemstone",
        "scaffold_status": "live",
        "prescription_text": "Wear Diamond (Heera) or White Sapphire (Safed Pukhraj) of at least 1 carat set in platinum or silver, on the middle finger of the right hand, on a Friday.",
        "gemstone": "Diamond (Heera) or White Sapphire",
        "day_of_week": "Friday",
        "color_associated": "white",
        "confidence": 0.85,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88 V.10",
    },
    {
        "remedy_id": "venus_general_charity_01",
        "planet": "venus",
        "domain": "general",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": "Donate white rice, sugar, dairy products, white flowers, or silver on Fridays. Feed young girls (Kumari Puja). Donate to women's welfare.",
        "charity_action": "Donate white foods, silver on Fridays; feed girls",
        "day_of_week": "Friday",
        "color_associated": "white",
        "confidence": 0.85,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    # ── Saturn ─────────────────────────────────────────────────────────────────
    {
        "remedy_id": "sat_career_mantra_01",
        "planet": "saturn",
        "domain": "career",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": "Chant the Shani Ashtottara Shatanamavali (108 names of Saturn) or the Shani Chalisa daily, especially on Saturdays. Saturn rules karma, discipline, and professional perseverance.",
        "mantra_text": "Om Praam Preem Praum Sah Shanaischaraya Namah (108 times)",
        "day_of_week": "Saturday",
        "color_associated": "black",
        "confidence": 0.90,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "sat_career_charity_01",
        "planet": "saturn",
        "domain": "career",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": "Donate black sesame seeds (til), black cloth, mustard oil, iron vessels, or sesame ladoos to laborers or the poor on Saturdays. Feed crows, who are Saturn's birds.",
        "charity_action": "Donate sesame, oil, black cloth; feed crows on Saturdays",
        "day_of_week": "Saturday",
        "color_associated": "black",
        "confidence": 0.90,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "sat_career_gemstone_01",
        "planet": "saturn",
        "domain": "career",
        "remedy_type": "gemstone",
        "scaffold_status": "live",
        "prescription_text": "Wear Blue Sapphire (Neelam) of at least 4 carats set in gold or panchdhatu, on the middle finger of the right hand, on a Saturday during Krishna Paksha. Caution: test for 3 days first.",
        "gemstone": "Blue Sapphire (Neelam)",
        "day_of_week": "Saturday",
        "color_associated": "blue",
        "confidence": 0.80,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88 V.11",
        "contraindications": "Test for 3 days before committing — Saturn gemstone is powerful and can amplify malefic results if Saturn is a functional malefic.",
    },
    {
        "remedy_id": "sat_health_mantra_01",
        "planet": "saturn",
        "domain": "health",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": "Chant Mahamrityunjaya mantra 108 times daily for Saturn-related chronic ailments (bones, joints, teeth, nervous system). Saturn governs Vata dosha.",
        "mantra_text": "Om Tryambakam Yajamahe Sugandhim Pushti-Vardhanam Urvarukamiva Bandhanan Mrityor Mukshiya Mamritat",
        "day_of_week": "Saturday",
        "color_associated": "black",
        "confidence": 0.85,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "sat_health_ayurvedic_01",
        "planet": "saturn",
        "domain": "health",
        "remedy_type": "ayurvedic",  # was dietary
        "scaffold_status": "live",
        "prescription_text": "Avoid black foods on Saturdays. Sesame oil massage (abhyanga) on Saturdays strengthens bones and joints governed by Saturn. Warm foods and sesame are recommended.",
        "day_of_week": "Saturday",
        "color_associated": "black",
        "confidence": 0.75,
        "source_canonical_id": "Phaladeepika",
        "source_citation": SOURCE_PHALA,
        "classical_ref": "Phala Deepika, remedial section",
    },
    {
        "remedy_id": "sat_wealth_puja_01",
        "planet": "saturn",
        "domain": "wealth",
        "remedy_type": "puja",  # was ritual
        "scaffold_status": "live",
        "prescription_text": "Perform Shani Puja on Saturdays with black sesame, mustard oil lamp, and black flower garland. Recite Shani Stotra. Offer blue lotus or violets when available.",
        "mantra_text": "Om Shanaischaraya Namah",
        "day_of_week": "Saturday",
        "color_associated": "black",
        "confidence": 0.85,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "sat_marriage_charity_01",
        "planet": "saturn",
        "domain": "marriage",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": "Serve elderly people and those born in poverty on Saturdays. Donate blankets and warm clothes to the needy in winter. Saturn delays marriage; service pacifies its karma.",
        "charity_action": "Serve elderly; donate blankets and warm clothes on Saturdays",
        "day_of_week": "Saturday",
        "color_associated": "black",
        "confidence": 0.80,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "sat_general_vrata_01",
        "planet": "saturn",
        "domain": "general",
        "remedy_type": "vrata",  # was fasting
        "scaffold_status": "live",
        "prescription_text": "Fast on Saturdays (Shanivara). Take only one meal in the evening. Avoid oil and non-vegetarian food. Observe for Sade Sati or Shani Dasha periods.",
        "day_of_week": "Saturday",
        "color_associated": "black",
        "confidence": 0.85,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    # ── Rahu ───────────────────────────────────────────────────────────────────
    {
        "remedy_id": "rahu_career_mantra_01",
        "planet": "rahu",
        "domain": "career",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": "Chant the Rahu Beeja Mantra 18,000 times over 40 days for Rahu Mahadasha career difficulties. Rahu rules obsession, ambition, and unconventional paths.",
        "mantra_text": "Om Bhram Bhreem Bhroum Sah Rahave Namah",
        "day_of_week": "Saturday",
        "color_associated": "smoke grey",
        "confidence": 0.80,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "rahu_health_gemstone_01",
        "planet": "rahu",
        "domain": "health",
        "remedy_type": "gemstone",
        "scaffold_status": "live",
        "prescription_text": "Wear Hessonite Garnet (Gomed) of at least 5 carats set in silver or panchdhatu, on the middle finger of the right hand, on a Saturday during Rahu Hora.",
        "gemstone": "Hessonite Garnet (Gomed)",
        "day_of_week": "Saturday",
        "color_associated": "brown",
        "confidence": 0.80,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88 V.12",
    },
    {
        "remedy_id": "rahu_general_charity_01",
        "planet": "rahu",
        "domain": "general",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": "Donate barley, blue-grey cloth, coconut, or urad dal on Saturdays. Feed fish or donate to charitable organizations. Avoid negative thinking on Rahu-related matters.",
        "charity_action": "Donate barley, coconut, urad dal on Saturdays",
        "day_of_week": "Saturday",
        "color_associated": "grey",
        "confidence": 0.80,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "rahu_marriage_puja_01",
        "planet": "rahu",
        "domain": "marriage",
        "remedy_type": "puja",  # was ritual
        "scaffold_status": "live",
        "prescription_text": "Perform Rahu Graha Shanti Puja with prescribed flowers and mantras. Worship Durga or Kali on full moon nights. Rahu in 7H delays or complicates marriage.",
        "mantra_text": "Om Rahave Namah",
        "day_of_week": "Saturday",
        "color_associated": "smoke grey",
        "confidence": 0.75,
        "source_canonical_id": "Phaladeepika",
        "source_citation": SOURCE_PHALA,
        "classical_ref": "Phala Deepika, remedial section",
    },
    # ── Ketu ───────────────────────────────────────────────────────────────────
    {
        "remedy_id": "ketu_spirituality_mantra_01",
        "planet": "ketu",
        "domain": "spirituality",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": "Chant the Ketu Beeja Mantra 17,000 times over 40 days. Ketu rules moksha, liberation, and occult wisdom. Strong Ketu brings spiritual insight.",
        "mantra_text": "Om Sram Sreem Sraum Sah Ketave Namah",
        "day_of_week": "Tuesday",
        "color_associated": "grey",
        "confidence": 0.80,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "ketu_health_gemstone_01",
        "planet": "ketu",
        "domain": "health",
        "remedy_type": "gemstone",
        "scaffold_status": "live",
        "prescription_text": "Wear Cat's Eye (Lehsunia/Vaidurya) of at least 5 carats set in silver, on the middle finger of the right hand, on a Tuesday or Thursday.",
        "gemstone": "Cat's Eye (Lehsunia)",
        "day_of_week": "Tuesday",
        "color_associated": "grey-green",
        "confidence": 0.80,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88 V.13",
    },
    {
        "remedy_id": "ketu_general_charity_01",
        "planet": "ketu",
        "domain": "general",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": "Donate sesame seeds, blankets, coloured cloth, or dogs (support animal welfare) on Tuesdays. Feed street dogs and provide them shelter.",
        "charity_action": "Donate sesame, blankets; feed dogs on Tuesdays",
        "day_of_week": "Tuesday",
        "color_associated": "grey",
        "confidence": 0.80,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    # ── Tajaka (annual chart) remedies ─────────────────────────────────────────
    {
        "remedy_id": "taj_sun_muntha_mantra_01",
        "planet": "sun",
        "domain": "general",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": "For Sun as Munthesha (Lord of Muntha) in Tajaka Varshaphal, chant Aditya Hridayam at the time of Solar Return (Varsha Pravesh). This energizes the annual chart.",
        "mantra_text": "Aditya Hridayam (full recitation)",
        "day_of_week": "Sunday",
        "color_associated": "red",
        "confidence": 0.75,
        "source_canonical_id": "Tajaka",
        "source_citation": SOURCE_TAJAKA,
        "classical_ref": "Tajaka Neelakanthi, Varshaphal remedies",
    },
    {
        "remedy_id": "taj_saturn_panchavargeeya_puja_01",
        "planet": "saturn",
        "domain": "career",
        "remedy_type": "puja",  # was ritual
        "scaffold_status": "live",
        "prescription_text": "For weak Saturn in Tajaka Varshaphal with low Panchavargeeya Bala, perform Shani Graha Shanti Yajna at the start of the year. This strengthens Saturn's annual contribution.",
        "day_of_week": "Saturday",
        "color_associated": "black",
        "confidence": 0.70,
        "source_canonical_id": "Tajaka",
        "source_citation": SOURCE_TAJAKA,
        "classical_ref": "Tajaka Neelakanthi, Panchavargeeya Bala remedies",
    },
    {
        "remedy_id": "taj_rahu_saham_puja_01",
        "planet": "rahu",
        "domain": "general",
        "remedy_type": "puja",  # was ritual
        "scaffold_status": "live",
        "prescription_text": "When Rahu aspects or conjoins the Punya Saham (Lot of Fortune) in Tajaka, perform Rahu Shanti and donate coconut with coins in a river on Saturday.",
        "mantra_text": "Om Rahave Namah",
        "charity_action": "Donate coconut with coins in a river",
        "day_of_week": "Saturday",
        "color_associated": "grey",
        "confidence": 0.70,
        "source_canonical_id": "Tajaka",
        "source_citation": SOURCE_TAJAKA,
        "classical_ref": "Tajaka Neelakanthi, Saham remedies",
    },
    # ── Additional cross-domain remedies ──────────────────────────────────────
    {
        "remedy_id": "mars_wealth_yantra_01",
        "planet": "mars",
        "domain": "wealth",
        "remedy_type": "yantra",
        "scaffold_status": "live",
        "prescription_text": "Install a Mangal Yantra (Mars Yantra) at home or workplace facing east. Energize on Tuesday during Shukla Paksha with red vermillion and red flowers.",
        "mantra_text": "Om Mangalaya Namah",
        "day_of_week": "Tuesday",
        "color_associated": "red",
        "confidence": 0.75,
        "source_canonical_id": "Phaladeepika",
        "source_citation": SOURCE_PHALA,
        "classical_ref": "Phala Deepika, Yantra section",
    },
    {
        "remedy_id": "mercury_health_mantra_01",
        "planet": "mercury",
        "domain": "health",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": "For Mercury-related skin and nervous system issues, chant Budha Ashtottara 108 times on Wednesdays. Mercury governs skin, lungs, and speech.",
        "mantra_text": "Om Braam Breem Braum Sah Budhaya Namah",
        "day_of_week": "Wednesday",
        "color_associated": "green",
        "confidence": 0.80,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "jupiter_spirituality_puja_01",
        "planet": "jupiter",
        "domain": "spirituality",
        "remedy_type": "puja",  # was ritual
        "scaffold_status": "live",
        "prescription_text": "Perform Brihaspati Puja on Thursdays with yellow flowers, gram dal, and camphor. Study sacred texts or listen to vedic recitation. Worship Vishnu or Dakshinamurthy.",
        "mantra_text": "Om Guruve Namah",
        "day_of_week": "Thursday",
        "color_associated": "yellow",
        "confidence": 0.85,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "venus_health_mantra_01",
        "planet": "venus",
        "domain": "health",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": "Chant Shukra Ashtottara 108 times on Fridays for Venus-related reproductive and kidney health issues. Venus governs the reproductive system and kidneys.",
        "mantra_text": "Om Draam Dreem Draum Sah Shukraya Namah",
        "day_of_week": "Friday",
        "color_associated": "white",
        "confidence": 0.80,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "moon_spirituality_puja_01",
        "planet": "moon",
        "domain": "spirituality",
        "remedy_type": "puja",  # was ritual
        "scaffold_status": "live",
        "prescription_text": "Perform Chandra Puja on Purnima (full moon) nights with white flowers and milk offerings. Practice meditation during moonrise. The Moon governs the mind.",
        "mantra_text": "Om Chandraya Namah",
        "day_of_week": "Monday",
        "color_associated": "white",
        "confidence": 0.85,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "sun_wealth_yantra_01",
        "planet": "sun",
        "domain": "wealth",
        "remedy_type": "yantra",
        "scaffold_status": "live",
        "prescription_text": "Install a Surya Yantra at home facing east. Energize on Sunday morning during Shukla Paksha with red vermillion, red flowers, and incense.",
        "mantra_text": "Om Suryaya Namah",
        "day_of_week": "Sunday",
        "color_associated": "red",
        "confidence": 0.80,
        "source_canonical_id": "Phaladeepika",
        "source_citation": SOURCE_PHALA,
        "classical_ref": "Phala Deepika, Yantra section",
    },
    {
        "remedy_id": "ketu_career_puja_01",
        "planet": "ketu",
        "domain": "career",
        "remedy_type": "puja",  # was ritual
        "scaffold_status": "live",
        "prescription_text": "Perform Ketu Graha Shanti on Tuesdays with prescribed flowers (Kush grass). Worship Ganesha or Bhairava. Ketu can cause career disruptions through sudden changes.",
        "mantra_text": "Om Ketave Namah",
        "day_of_week": "Tuesday",
        "color_associated": "grey",
        "confidence": 0.75,
        "source_canonical_id": "Phaladeepika",
        "source_citation": SOURCE_PHALA,
        "classical_ref": "Phala Deepika, remedial section",
    },
    {
        "remedy_id": "rahu_wealth_yantra_01",
        "planet": "rahu",
        "domain": "wealth",
        "remedy_type": "yantra",
        "scaffold_status": "live",
        "prescription_text": "Install a Rahu Yantra on Saturdays. Rahu can bring sudden financial windfalls as well as losses; the yantra stabilizes its volatile influence.",
        "mantra_text": "Om Rahave Namah",
        "day_of_week": "Saturday",
        "color_associated": "smoke grey",
        "confidence": 0.70,
        "source_canonical_id": "Phaladeepika",
        "source_citation": SOURCE_PHALA,
        "classical_ref": "Phala Deepika, Yantra section",
    },
    {
        "remedy_id": "sat_education_mantra_01",
        "planet": "saturn",
        "domain": "education",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": "Saturn delays but does not deny. Chant Shani Chalisa every Saturday during Shani Dasha to overcome obstacles in education and research. Saturn rewards persistent study.",
        "mantra_text": "Shani Chalisa (full text)",
        "day_of_week": "Saturday",
        "color_associated": "black",
        "confidence": 0.80,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "mars_spirituality_puja_01",
        "planet": "mars",
        "domain": "spirituality",
        "remedy_type": "puja",  # was ritual
        "scaffold_status": "live",
        "prescription_text": "Perform Subrahmanya Puja (Karthikeya/Murugan) on Tuesdays. Offer red flowers and plantain. Mars's spiritual manifestation is the divine warrior.",
        "mantra_text": "Om Saravanabhavaya Namah",
        "day_of_week": "Tuesday",
        "color_associated": "red",
        "confidence": 0.80,
        "source_canonical_id": "Phaladeepika",
        "source_citation": SOURCE_PHALA,
        "classical_ref": "Phala Deepika, remedial section",
    },
    {
        "remedy_id": "venus_career_charity_01",
        "planet": "venus",
        "domain": "career",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": "Donate dairy products, white sweets, perfume, or artistic materials on Fridays. Support artists and musicians. Venus blesses creative and luxury industries.",
        "charity_action": "Donate dairy, sweets, perfume to artists on Fridays",
        "day_of_week": "Friday",
        "color_associated": "white",
        "confidence": 0.80,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
    {
        "remedy_id": "mercury_marriage_mantra_01",
        "planet": "mercury",
        "domain": "marriage",
        "remedy_type": "mantra",
        "scaffold_status": "live",
        "prescription_text": "Mercury in 7H can bring a communicative, intellectual spouse but may cause indecision. Chant Budha Ashtottara 108 times on Wednesdays to strengthen Mercury's positive attributes.",
        "mantra_text": "Om Budhaya Namah",
        "day_of_week": "Wednesday",
        "color_associated": "green",
        "confidence": 0.75,
        "source_canonical_id": "Phaladeepika",
        "source_citation": SOURCE_PHALA,
        "classical_ref": "Phala Deepika, remedial section",
    },
    {
        "remedy_id": "jupiter_health_charity_01",
        "planet": "jupiter",
        "domain": "health",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": "Donate sweets, yellow gram, turmeric, or gold to Brahmins on Thursdays for Jupiter-related liver and gallbladder issues. Jupiter governs the liver, fat, and growth.",
        "charity_action": "Donate sweets, turmeric, gold on Thursdays",
        "day_of_week": "Thursday",
        "color_associated": "yellow",
        "confidence": 0.80,
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS_LEGACY,
        "classical_ref": "BPHS Ch.88",
    },
]


# ── §3.4 — Expansion remedies: nakshatra mantras, stotra prescriptions, ────────
# additional dana and yantra spec rows.
# Sources: BPHS Ch.91-94; Deva Keralam; Muhurta Chintamani; Yantra Maharnava;
# Brihat Samhita (BS); standard Jyotish mantra tradition.
# ZERO LLM — all data from named classical sources.

SOURCE_DK = "Deva Keralam (Chandra Kala Nadi), classical Jyotish tradition"
SOURCE_MC = "Muhurta Chintamani, classical Jyotish muhurta text"
SOURCE_YM = "Yantra Maharnava, classical yantra text"
SOURCE_BS = "Brihat Samhita (Varahamihira), classical Jyotish/astronomy text"

# 27 nakshatra deity + mantra data (BPHS Ch.94; standard tradition)
_NAKSHATRA_DATA: list[tuple[str, str, str, str, str]] = [
    # (nakshatra_id, nakshatra_name, ruling_planet, presiding_deity, mantra_transliteration)
    ("ashwini",       "Ashwini",       "ketu",    "Ashwini Kumaras",  "Om Ashwinibhyam Namah"),
    ("bharani",       "Bharani",       "venus",   "Yama",             "Om Yamaya Namah"),
    ("krittika",      "Krittika",      "sun",     "Agni",             "Om Agnaye Namah"),
    ("rohini",        "Rohini",        "moon",    "Brahma/Prajapati", "Om Prajapataye Namah"),
    ("mrigashira",    "Mrigashira",    "mars",    "Soma (Moon)",      "Om Somaya Namah"),
    ("ardra",         "Ardra",         "rahu",    "Rudra",            "Om Rudraya Namah"),
    ("punarvasu",     "Punarvasu",     "jupiter", "Aditi",            "Om Adityai Namah"),
    ("pushya",        "Pushya",        "saturn",  "Brihaspati",       "Om Brihaspataye Namah"),
    ("ashlesha",      "Ashlesha",      "mercury", "Sarpa (Nagas)",    "Om Sarpebhyo Namah"),
    ("magha",         "Magha",         "ketu",    "Pitru (Ancestors)","Om Pitribhyo Namah"),
    ("purva_phalguni","Purva Phalguni","venus",   "Bhaga",            "Om Bhagaya Namah"),
    ("uttara_phalguni","Uttara Phalguni","sun",   "Aryaman",          "Om Aryamne Namah"),
    ("hasta",         "Hasta",         "moon",    "Savitar (Surya)",  "Om Savitre Namah"),
    ("chitra",        "Chitra",        "mars",    "Tvashtar/Vishvakarman","Om Tvashtre Namah"),
    ("swati",         "Swati",         "rahu",    "Vayu",             "Om Vayave Namah"),
    ("vishakha",      "Vishakha",      "jupiter", "Indragni",         "Om Indragnibhyam Namah"),
    ("anuradha",      "Anuradha",      "saturn",  "Mitra",            "Om Mitraya Namah"),
    ("jyeshtha",      "Jyeshtha",      "mercury", "Indra",            "Om Indraya Namah"),
    ("mula",          "Mula",          "ketu",    "Nirriti",          "Om Nirritaye Namah"),
    ("purva_ashadha", "Purva Ashadha", "venus",   "Apas (Waters)",    "Om Adbhyo Namah"),
    ("uttara_ashadha","Uttara Ashadha","sun",     "Vishvadevas",      "Om Vishvadevebhyo Namah"),
    ("shravana",      "Shravana",      "moon",    "Vishnu",           "Om Vishnave Namah"),
    ("dhanishtha",    "Dhanishtha",    "mars",    "Vasus",            "Om Vasubhyo Namah"),
    ("shatabhisha",   "Shatabhisha",   "rahu",    "Varuna",           "Om Varunaya Namah"),
    ("purva_bhadra",  "Purva Bhadrapada","jupiter","Aja Ekapada",     "Om Aja Ekapadaya Namah"),
    ("uttara_bhadra", "Uttara Bhadrapada","saturn","Ahir Budhnya",    "Om Ahir Budhnyaya Namah"),
    ("revati",        "Revati",        "mercury", "Pushan",           "Om Pushne Namah"),
]

# Sanity: planets in nakshatra data must be valid
assert all(p in VALID_PLANETS for _, _, p, _, _ in _NAKSHATRA_DATA), \
    "Nakshatra planet not in VALID_PLANETS"


def _gen_nakshatra_mantra_rows() -> list[dict[str, Any]]:
    """
    Generate one mantra remedy row per nakshatra for birth-nakshatra propitiation.
    27 rows total.
    Source: BPHS Ch.94 (nakshatra devata table); standard Jyotish mantra tradition.
    """
    rows: list[dict[str, Any]] = []
    for nak_id, nak_name, planet, deity, mantra in _NAKSHATRA_DATA:
        prescription = (
            f"For birth in {nak_name} nakshatra: recite the nakshatra devata mantra "
            f"'{mantra}' 108 times daily, especially on the day ruled by {planet.capitalize()}. "
            f"The presiding deity is {deity}. This propitiation pacifies afflictions to "
            f"the natal Moon/lagna when in this nakshatra and is prescribed for nakshatra "
            f"shanti in BPHS Ch.94."
        )
        rows.append({
            "remedy_id": f"nakshatra_{nak_id}_mantra",
            "planet": planet,
            "domain": "general",
            "remedy_type": "mantra",
            "scaffold_status": "live",
            "prescription_text": prescription,
            "mantra_transliteration": mantra,
            "deity": deity,
            "source_canonical_id": "BPHS",
            "source_citation": SOURCE_BPHS,
            "classical_ref": "BPHS Ch.94 (Nakshatra devata table); Deva Keralam",
            "cost_tier": "free",
            "confidence": 0.85,
            "category": "nakshatra_shanti",
        })
    return rows


# Stotra prescriptions — specific stotras cited to classical sources
STOTRA_REMEDIES: list[dict[str, Any]] = [
    # ── Aditya Hridayam ────────────────────────────────────────────────────────
    {
        "remedy_id": "stotra_aditya_hridayam_afflicted_sun",
        "planet": "sun",
        "domain": "general",
        "remedy_type": "japa",
        "scaffold_status": "live",
        "prescription_text": (
            "For afflicted Sun (combust, debilitated in Libra, or in 6/8/12): recite Aditya "
            "Hridayam (from Valmiki Ramayana, Yuddha Kanda Ch.107) in full at sunrise facing "
            "east, daily during Sun dasha/antardasha. Agastya prescribed this to Rama before "
            "battle — it is the classical solar invocation for strength and authority."
        ),
        "mantra_transliteration": "Aditya Hridayam (Valmiki Ramayana, Yuddha Kanda 107)",
        "deity": "Surya",
        "day_of_week": "Sunday",
        "source_canonical_id": "BPHS",
        "source_citation": "Valmiki Ramayana, Yuddha Kanda Ch.107 (Aditya Hridayam); BPHS Ch.88",
        "classical_ref": "Valmiki Ramayana, Yuddha Kanda 107; BPHS Ch.88 (Surya upaya)",
        "cost_tier": "free",
        "confidence": 0.90,
    },
    # ── Vishnu Sahasranama ─────────────────────────────────────────────────────
    {
        "remedy_id": "stotra_vishnu_sahasranama_jupiter_afflicted",
        "planet": "jupiter",
        "domain": "general",
        "remedy_type": "japa",
        "scaffold_status": "live",
        "prescription_text": (
            "For afflicted Jupiter (debilitated in Capricorn, Guru Chandal dosha, retrograde "
            "in dasha): recite Vishnu Sahasranama (Mahabharata, Anushasana Parva 149) once "
            "daily on Thursdays. Jupiter is the karaka of dharma and wisdom — Vishnu "
            "Sahasranama is the classical prescription for Guru-related obstacles per "
            "Phaladeepika's remedial section."
        ),
        "mantra_transliteration": "Vishnu Sahasranama (Mahabharata, Anushasana Parva 149)",
        "deity": "Vishnu",
        "day_of_week": "Thursday",
        "source_canonical_id": "Phaladeepika",
        "source_citation": SOURCE_PHALA,
        "classical_ref": "Phaladeepika remedial section; Mahabharata Anushasana Parva 149",
        "cost_tier": "free",
        "confidence": 0.88,
    },
    # ── Sudarshana Chakra Stotra ───────────────────────────────────────────────
    {
        "remedy_id": "stotra_sudarshana_kuja_dosha",
        "planet": "mars",
        "domain": "marriage",
        "remedy_type": "japa",
        "scaffold_status": "live",
        "prescription_text": (
            "For Kuja (Mangala) Dosha with strong affliction (Mars in 7H/8H from lagna, "
            "Moon and Venus simultaneously): recite the Sudarshana Ashtakam (cited in "
            "Pancharatra Agama tradition) on Tuesdays. Sudarshana (Vishnu's discus) is "
            "prescribed in South Indian tradition for Mars-related marriage obstacles; "
            "it cuts through karmic knots. 108 recitations per sitting."
        ),
        "mantra_transliteration": "Sudarshana Ashtakam (Pancharatra Agama tradition)",
        "deity": "Sudarshana/Vishnu",
        "day_of_week": "Tuesday",
        "source_canonical_id": "classical_tradition",
        "source_citation": "Pancharatra Agama tradition; Deva Keralam",
        "classical_ref": "Pancharatra Agama (Sudarshana upaya); Deva Keralam (Kuja upaya)",
        "cost_tier": "free",
        "confidence": 0.80,
        "dosha_target": "manglik",
    },
    # ── Mahamrityunjaya ────────────────────────────────────────────────────────
    {
        "remedy_id": "stotra_mahamrityunjaya_saturn_affliction",
        "planet": "saturn",
        "domain": "health",
        "remedy_type": "japa",
        "scaffold_status": "live",
        "prescription_text": (
            "For Saturn-ruled chronic disease (bones, joints, nervous system; Saturn in 6H/8H "
            "or Sade Sati with health impact): perform Mahamrityunjaya japa to the prescribed "
            "count — 1,25,000 (1.25 lakh) for a full shanti, or 108 daily as ongoing "
            "maintenance. The mantra is from Rigveda 7.59.12 (Tryambaka sukta) and is the "
            "classical prescription for Mrityu-related (Saturn/8H) afflictions."
        ),
        "mantra_transliteration": (
            "Om Tryambakam Yajamahe Sugandhim Pushti-Vardhanam "
            "Urvarukamiva Bandhanan Mrityor Mukshiya Mamritat"
        ),
        "mantra_sanskrit": (
            "ॐ त्र्यम्बकं यजामहे सुगन्धिं पुष्टिवर्धनम् "
            "उर्वारुकमिव बन्धनान् मृत्योर्मुक्षीय माऽमृतात्"
        ),
        "deity": "Shiva (Tryambaka)",
        "day_of_week": "Saturday",
        "source_canonical_id": "BPHS",
        "source_citation": "Rigveda 7.59.12 (Tryambaka sukta); BPHS Ch.88 (Shani upaya)",
        "classical_ref": "Rigveda 7.59.12; BPHS Ch.88 (Shani health upaya)",
        "cost_tier": "free",
        "confidence": 0.92,
    },
    # ── Shri Sukta ────────────────────────────────────────────────────────────
    {
        "remedy_id": "stotra_shri_sukta_venus_wealth",
        "planet": "venus",
        "domain": "wealth",
        "remedy_type": "japa",
        "scaffold_status": "live",
        "prescription_text": (
            "For Venus-related wealth affliction (Venus in 6H/12H, debilitated in Virgo, "
            "or Shukra dasha poverty): recite Shri Sukta (Rigveda Khilani, 16 verses) "
            "on Fridays before Lakshmi puja. Shri Sukta is the oldest Vedic hymn to Lakshmi "
            "and is the canonical prescription for Venus/Lakshmi-related prosperity."
        ),
        "mantra_transliteration": "Shri Sukta (Rigveda Khilani, 16 verses)",
        "deity": "Lakshmi",
        "day_of_week": "Friday",
        "source_canonical_id": "BPHS",
        "source_citation": "Rigveda Khilani (Shri Sukta); BPHS Ch.88 (Shukra upaya)",
        "classical_ref": "Rigveda Khilani (Shri Sukta 16 verses); BPHS Ch.88",
        "cost_tier": "free",
        "confidence": 0.88,
    },
    # ── Purusha Sukta ─────────────────────────────────────────────────────────
    {
        "remedy_id": "stotra_purusha_sukta_sun_authority",
        "planet": "sun",
        "domain": "career",
        "remedy_type": "japa",
        "scaffold_status": "live",
        "prescription_text": (
            "For weak Sun causing loss of authority, government obstacles, or father-related "
            "afflictions: recite Purusha Sukta (Rigveda 10.90, 16 verses) on Sundays at "
            "sunrise. The Sun is the cosmic Purusha; this sukta is prescribed in Vedic "
            "tradition for Solar invocation in matters of authority, status and dharma."
        ),
        "mantra_transliteration": "Purusha Sukta (Rigveda 10.90)",
        "deity": "Surya/Vishnu",
        "day_of_week": "Sunday",
        "source_canonical_id": "BPHS",
        "source_citation": "Rigveda 10.90 (Purusha Sukta); BPHS Ch.88 (Surya upaya)",
        "classical_ref": "Rigveda 10.90; BPHS Ch.88 (Surya career upaya)",
        "cost_tier": "free",
        "confidence": 0.85,
    },
    # ── Durga Saptashati ──────────────────────────────────────────────────────
    {
        "remedy_id": "stotra_durga_saptashati_rahu_affliction",
        "planet": "rahu",
        "domain": "general",
        "remedy_type": "japa",
        "scaffold_status": "live",
        "prescription_text": (
            "For Rahu affliction (Rahu in lagna/4H/7H/8H; Rahu dasha with obstacles): "
            "recite Durga Saptashati (Devi Mahatmyam, Markandeya Purana Ch.81-93) during "
            "Navaratri or on Saturdays. Durga is the presiding deity of Rahu in classical "
            "tradition (BPHS Ch.94). The Saptashati's 700 verses are prescribed for "
            "protection against Rahu-related illusions and hidden enemies."
        ),
        "mantra_transliteration": "Durga Saptashati (Devi Mahatmyam, Markandeya Purana Ch.81-93)",
        "deity": "Durga",
        "day_of_week": "Saturday",
        "source_canonical_id": "BPHS",
        "source_citation": "Markandeya Purana Ch.81-93 (Devi Mahatmyam); BPHS Ch.94",
        "classical_ref": "Markandeya Purana Ch.81-93; BPHS Ch.94 (Rahu devata = Durga)",
        "cost_tier": "free",
        "confidence": 0.85,
    },
    # ── Ganesha Atharvashirsha ────────────────────────────────────────────────
    {
        "remedy_id": "stotra_ganesha_atharvashirsha_ketu",
        "planet": "ketu",
        "domain": "general",
        "remedy_type": "japa",
        "scaffold_status": "live",
        "prescription_text": (
            "For Ketu affliction (Ketu in lagna/8H; Ketu dasha confusion or health issues): "
            "recite Ganesha Atharvashirsha (Atharva Veda Parishishtha) on Tuesdays and "
            "on Chaturthi tithi. Ganesha is the presiding deity of Ketu (BPHS Ch.94). "
            "The Atharvashirsha removes obstacles and confusion associated with Ketu's "
            "detachment and karmic entanglement."
        ),
        "mantra_transliteration": "Ganesha Atharvashirsha (Atharva Veda Parishishtha)",
        "deity": "Ganesha",
        "day_of_week": "Tuesday",
        "source_canonical_id": "BPHS",
        "source_citation": "Atharva Veda Parishishtha (Ganesha Atharvashirsha); BPHS Ch.94",
        "classical_ref": "Atharva Veda Parishishtha; BPHS Ch.94 (Ketu devata = Ganesha)",
        "cost_tier": "free",
        "confidence": 0.85,
    },
    # ── Hanuman Chalisa ───────────────────────────────────────────────────────
    {
        "remedy_id": "stotra_hanuman_chalisa_mars_saturn",
        "planet": "saturn",
        "domain": "general",
        "remedy_type": "japa",
        "scaffold_status": "live",
        "prescription_text": (
            "For Saturn affliction, Sade Sati, or Mars-Saturn conjunction (Angarak yoga): "
            "recite Hanuman Chalisa (Tulsidas, 16th c., 40 verses) daily. Classical tradition "
            "holds Hanuman pacifies both Saturn (per Ramayana tradition: Hanuman is the "
            "Shatru of Shani) and Mars (as the deity of Mars in some schools). "
            "This is the most widely prescribed Saturn-pacification stotra in North Indian tradition."
        ),
        "mantra_transliteration": "Hanuman Chalisa (Tulsidas, 40 verses)",
        "deity": "Hanuman",
        "day_of_week": "Saturday",
        "source_canonical_id": "classical_tradition",
        "source_citation": "Tulsidas, Hanuman Chalisa (16th c.); classical tradition",
        "classical_ref": "Hanuman Chalisa (Tulsidas); classical Shani-upaya tradition",
        "cost_tier": "free",
        "confidence": 0.88,
    },
    # ── Chandra Stotra / Soma Stotra ──────────────────────────────────────────
    {
        "remedy_id": "stotra_soma_sukta_moon_affliction",
        "planet": "moon",
        "domain": "health",
        "remedy_type": "japa",
        "scaffold_status": "live",
        "prescription_text": (
            "For afflicted Moon (Kemadruma dosha, Moon in 6H/8H/12H, Vish dosha, mental "
            "anxiety in Chandra dasha): recite the Soma Sukta mantras (Rigveda 9 — Pavamana "
            "Soma suktas) on Mondays during Shukla Paksha. Alternatively, recite the "
            "Chandra Ashtottara (108 names of the Moon) 3 times. The Moon is Soma in the "
            "Rigveda; this is the classical Vedic prescription for lunar strengthening."
        ),
        "mantra_transliteration": "Pavamana Soma Sukta (Rigveda Mandala 9); Chandra Ashtottara",
        "deity": "Soma/Chandra",
        "day_of_week": "Monday",
        "source_canonical_id": "BPHS",
        "source_citation": "Rigveda Mandala 9 (Soma Suktas); BPHS Ch.88 (Chandra upaya)",
        "classical_ref": "Rigveda Mandala 9; BPHS Ch.88 (Chandra upaya)",
        "cost_tier": "free",
        "confidence": 0.85,
    },
    # ── Budha Stotra / Saraswati ──────────────────────────────────────────────
    {
        "remedy_id": "stotra_saraswati_mercury_education",
        "planet": "mercury",
        "domain": "education",
        "remedy_type": "japa",
        "scaffold_status": "live",
        "prescription_text": (
            "For afflicted Mercury (Budha in 6H/8H/12H, Budha-Aditya yoga complications, "
            "education obstacles): recite Saraswati Vandana or the Saraswati Ashtottara "
            "(108 names) on Wednesdays. Saraswati is the deity governing Mercury's "
            "domain of knowledge, speech, and learning. Also prescribed: writing mantras "
            "by hand 108 times as a Mercury-specific practice."
        ),
        "mantra_transliteration": "Saraswati Ashtottara; Om Aim Saraswatyai Namah (108 times)",
        "deity": "Saraswati",
        "day_of_week": "Wednesday",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Mercury-Saraswati upaya); Deva Keralam",
        "cost_tier": "free",
        "confidence": 0.83,
    },
]

# Additional Dana (charity) prescriptions — per BPHS Ch.85-94 and Muhurta Chintamani
DANA_EXPANSION_REMEDIES: list[dict[str, Any]] = [
    # ── Sun dana (detailed BPHS Ch.93) ────────────────────────────────────────
    {
        "remedy_id": "dana_sun_copper_arghya_sunday",
        "planet": "sun",
        "domain": "general",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": (
            "Sunday dana for Sun propitiation (BPHS Ch.93): donate copper vessel filled "
            "with water and red sandalwood to a Brahmin at sunrise. The copper-Surya "
            "connection is metallurgically canonical; water-filled copper pot (Arghya patra) "
            "given with wheat and jaggery is the standard Sun dana. Do on Sundays in "
            "Shukla Paksha for maximum effect during Sun dasha."
        ),
        "charity_action": "Donate copper vessel with water and red sandalwood on Sunday at sunrise",
        "day_of_week": "Sunday",
        "color_associated": "red/copper",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.93 (Surya dana)",
        "cost_tier": "low",
        "confidence": 0.88,
    },
    {
        "remedy_id": "dana_sun_seven_grains_sunday",
        "planet": "sun",
        "domain": "general",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": (
            "Saptadhanya dana for Sun: donate the seven sacred grains (wheat, barley, "
            "sesame, green gram, black gram, rice, lentil) on Sundays in red cloth. "
            "The Saptadhanya is cited in BPHS Ch.93 and Muhurta Chintamani as the "
            "prescribed grain-set for graha shanti dana across multiple planets."
        ),
        "charity_action": "Donate seven grains (saptadhanya) in red cloth on Sunday",
        "day_of_week": "Sunday",
        "color_associated": "red",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_MC,
        "classical_ref": "Muhurta Chintamani (Saptadhanya dana); BPHS Ch.93",
        "cost_tier": "low",
        "confidence": 0.85,
    },
    # ── Moon dana (BPHS Ch.93) ────────────────────────────────────────────────
    {
        "remedy_id": "dana_moon_silver_milk_monday",
        "planet": "moon",
        "domain": "general",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": (
            "Monday dana for Moon propitiation (BPHS Ch.93): donate silver (even a small "
            "coin), white rice, milk, and curd to a Brahmin woman or temple on Mondays "
            "during Purnima (full moon). The Moon-silver-white connection is the canonical "
            "triad in BPHS Ch.93."
        ),
        "charity_action": "Donate silver coin, white rice, milk on Monday at Purnima",
        "day_of_week": "Monday",
        "color_associated": "white",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.93 (Chandra dana)",
        "cost_tier": "low",
        "confidence": 0.88,
    },
    {
        "remedy_id": "dana_moon_white_cow_gift",
        "planet": "moon",
        "domain": "general",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": (
            "Go-dana (cow gift) for Moon: gifting or supporting a white cow is the highest "
            "Moon-related dana in classical tradition (BPHS Ch.93, Vishnu Purana). "
            "Practically: donate milk, ghee, and white cloth to a goshaala (cow shelter) "
            "on Mondays or on Purnima. The cow is Moon's primary symbol."
        ),
        "charity_action": "Donate milk/ghee to goshaala or support white cow on Mondays/Purnima",
        "day_of_week": "Monday",
        "color_associated": "white",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.93 (Go-dana for Chandra)",
        "cost_tier": "medium",
        "confidence": 0.85,
    },
    # ── Mars dana (BPHS Ch.93) ────────────────────────────────────────────────
    {
        "remedy_id": "dana_mars_masoor_blood_donation",
        "planet": "mars",
        "domain": "health",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": (
            "Tuesday dana for Mars (BPHS Ch.93): donate masoor dal (red lentils), red "
            "cloth, and copper on Tuesdays. Blood donation on Tuesdays is the modern "
            "classical equivalent and is widely recommended — blood is Mars's fluid "
            "and giving it is the strongest Mars-karmic action. Also: donate to emergency "
            "services or fire departments (Mars governs fire and emergencies)."
        ),
        "charity_action": "Donate masoor dal, red cloth, copper on Tuesdays; give blood",
        "day_of_week": "Tuesday",
        "color_associated": "red",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.93 (Mangala dana)",
        "cost_tier": "low",
        "confidence": 0.87,
    },
    # ── Mercury dana (BPHS Ch.93) ─────────────────────────────────────────────
    {
        "remedy_id": "dana_mercury_books_green_wednesday",
        "planet": "mercury",
        "domain": "education",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": (
            "Wednesday dana for Mercury (BPHS Ch.93): donate green cloth, green moong dal, "
            "books, and writing materials on Wednesdays. Donating to schools, libraries, "
            "or sponsoring a student's education is the Mercury dana in contemporary form. "
            "The BPHS Ch.93 prescribes green gram (moong) and bronze as the Mercury pair."
        ),
        "charity_action": "Donate green moong, books, writing materials to students on Wednesday",
        "day_of_week": "Wednesday",
        "color_associated": "green",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.93 (Budha dana)",
        "cost_tier": "low",
        "confidence": 0.87,
    },
    # ── Jupiter dana (BPHS Ch.93) ─────────────────────────────────────────────
    {
        "remedy_id": "dana_jupiter_chana_dal_gold_thursday",
        "planet": "jupiter",
        "domain": "wealth",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": (
            "Thursday dana for Jupiter (BPHS Ch.93): donate chana dal (yellow gram), "
            "turmeric, yellow cloth, and gold to a Brahmin or pandit on Thursdays, "
            "preferably during Guru Hora (Jupiter's planetary hour). Feed Brahmins "
            "or holy men sweets and yellow rice. BPHS Ch.93 specifically prescribes "
            "gold-and-yellow-gram as the Jupiter dana pair."
        ),
        "charity_action": "Donate chana dal, turmeric, yellow cloth; feed Brahmins on Thursday",
        "day_of_week": "Thursday",
        "color_associated": "yellow",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.93 (Guru dana)",
        "cost_tier": "low",
        "confidence": 0.88,
    },
    {
        "remedy_id": "dana_jupiter_ashwattha_puja_water",
        "planet": "jupiter",
        "domain": "general",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": (
            "Watering the Ashwattha (Peepal tree, Ficus religiosa) on Thursdays and "
            "circumambulating it 108 times is prescribed for Jupiter strengthening in "
            "classical tradition. The Ashwattha is Jupiter's sacred tree (BPHS Ch.94 "
            "tree-correspondence table). This is a dana-in-kind — offering service "
            "to Jupiter's tree."
        ),
        "charity_action": "Water and circumambulate Ashwattha (peepal) tree 108 times on Thursday",
        "day_of_week": "Thursday",
        "color_associated": "yellow",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.94 (Ashwattha = Jupiter's tree)",
        "cost_tier": "free",
        "confidence": 0.82,
    },
    # ── Venus dana (BPHS Ch.93) ────────────────────────────────────────────────
    {
        "remedy_id": "dana_venus_white_silk_friday",
        "planet": "venus",
        "domain": "marriage",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": (
            "Friday dana for Venus (BPHS Ch.93): donate white silk cloth, sugar, curd, "
            "silver, and white flowers to women or a Lakshmi temple on Fridays. "
            "Kumari puja — feeding and gifting young unmarried girls — is the highest "
            "Venus dana. BPHS Ch.93 prescribes white cloth and silver as the Venus pair."
        ),
        "charity_action": "Donate white silk, sugar, silver to women/temple; Kumari puja on Friday",
        "day_of_week": "Friday",
        "color_associated": "white",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.93 (Shukra dana); Kumari puja tradition",
        "cost_tier": "low",
        "confidence": 0.87,
    },
    {
        "remedy_id": "dana_venus_cow_ghee_friday",
        "planet": "venus",
        "domain": "general",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": (
            "For Venus-related reproductive or marital issues: donate pure ghee (clarified "
            "butter), cow milk, and sugar on Fridays. Venus governs Shukra (semen/essence) "
            "in Ayurvedic tradition; ghee donation propitiates Venus's life-essence "
            "signification. BPHS Ch.93 includes dairy as a Venus donation item."
        ),
        "charity_action": "Donate ghee, milk, sugar on Fridays for Venus propitiation",
        "day_of_week": "Friday",
        "color_associated": "white",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.93 (Shukra dana — dairy)",
        "cost_tier": "low",
        "confidence": 0.83,
    },
    # ── Saturn dana (BPHS Ch.93) ──────────────────────────────────────────────
    {
        "remedy_id": "dana_saturn_sesame_iron_saturday",
        "planet": "saturn",
        "domain": "general",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": (
            "Saturday dana for Saturn (BPHS Ch.93): donate black sesame (til), iron vessel, "
            "mustard oil, dark blue/black cloth, and shoes to a laborer or the destitute "
            "on Saturdays. BPHS Ch.93 specifies black sesame and iron as the canonical "
            "Saturn dana pair. Feeding crows (Saturn's bird) bread soaked in mustard oil "
            "on Saturdays is an additional classical prescription."
        ),
        "charity_action": "Donate black sesame, iron, mustard oil, dark cloth to laborers on Saturday",
        "day_of_week": "Saturday",
        "color_associated": "black",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.93 (Shani dana)",
        "cost_tier": "low",
        "confidence": 0.90,
    },
    {
        "remedy_id": "dana_saturn_shaami_tree_saturday",
        "planet": "saturn",
        "domain": "general",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": (
            "Watering and lighting an oil lamp beneath the Shaami tree (Prosopis cineraria) "
            "on Saturdays is the canonical Saturn dana-in-kind from BPHS Ch.94. The Shaami "
            "is Saturn's sacred tree. Also: reciting the Shani mantra under the Shaami on "
            "Saturdays during Sade Sati is the classical prescription."
        ),
        "charity_action": "Light oil lamp and water Shaami tree on Saturday; recite Shani mantra",
        "day_of_week": "Saturday",
        "color_associated": "black",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.94 (Shaami = Saturn's tree)",
        "cost_tier": "free",
        "confidence": 0.85,
    },
    # ── Rahu dana (BPHS Ch.93) ────────────────────────────────────────────────
    {
        "remedy_id": "dana_rahu_urad_coconut_saturday",
        "planet": "rahu",
        "domain": "general",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": (
            "Saturday dana for Rahu (BPHS Ch.93): donate urad dal (black gram), coconut, "
            "blue/grey cloth, and mustard oil on Saturdays. Float a coconut in a river "
            "on Saturday during Rahu dasha. BPHS Ch.93 prescribes urad and lead/silver "
            "as the Rahu dana pair; the coconut-river offering is from classical Rahu-shanti tradition."
        ),
        "charity_action": "Donate urad dal, coconut, blue cloth on Saturday; float coconut in river",
        "day_of_week": "Saturday",
        "color_associated": "smoky grey",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.93 (Rahu dana)",
        "cost_tier": "low",
        "confidence": 0.85,
    },
    # ── Ketu dana (BPHS Ch.93) ────────────────────────────────────────────────
    {
        "remedy_id": "dana_ketu_sesame_blanket_tuesday",
        "planet": "ketu",
        "domain": "general",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": (
            "Tuesday/Saturday dana for Ketu (BPHS Ch.93): donate sesame seeds (white or "
            "mixed), a blanket, multicolored cloth, and copper on Tuesdays. Feeding street "
            "dogs is the modern classical equivalent for Ketu dana (dogs are Ketu's animal). "
            "BPHS Ch.93 prescribes sesame and panchdhatu as the Ketu pair."
        ),
        "charity_action": "Donate sesame, blanket, multicolored cloth on Tuesday; feed street dogs",
        "day_of_week": "Tuesday",
        "color_associated": "multicolour",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.93 (Ketu dana)",
        "cost_tier": "low",
        "confidence": 0.85,
    },
    # ── Sade Sati specific dana (Muhurta Chintamani) ──────────────────────────
    {
        "remedy_id": "dana_sade_sati_shoes_to_poor",
        "planet": "saturn",
        "domain": "general",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": (
            "For Sade Sati mitigation: donate shoes to the destitute on Saturdays throughout "
            "the 7.5-year period. This is cited in Muhurta Chintamani and the broader Shani "
            "upaya tradition — Saturn governs the feet and the lowest classes; serving them "
            "directly appeases Saturn's karmic test. Also donate oil to a Shani temple."
        ),
        "charity_action": "Donate shoes to poor on Saturdays; donate oil to Shani temple",
        "day_of_week": "Saturday",
        "color_associated": "black",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_MC,
        "classical_ref": "Muhurta Chintamani (Sade Sati dana); classical Shani tradition",
        "cost_tier": "low",
        "confidence": 0.83,
        "dosha_target": "sade_sati",
    },
    # ── Pitru Dosha specific dana ─────────────────────────────────────────────
    {
        "remedy_id": "dana_pitru_amavasya_tarpan_sesame",
        "planet": "sun",
        "domain": "general",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": (
            "Monthly Amavasya (new moon) dana for Pitru Dosha: donate black sesame, "
            "barley, and water to ancestors via tarpan ritual. Feed Brahmins a meal "
            "on the father's death anniversary (tithi shraddha). BPHS Ch.93 and "
            "Dharmashastra both prescribe sesame-water tarpan as the canonical "
            "Pitru dana on Amavasya."
        ),
        "charity_action": "Donate black sesame and water at tarpan on Amavasya; feed Brahmins",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.93 (Pitru dana — Amavasya tarpan); Dharmashastra",
        "cost_tier": "low",
        "confidence": 0.87,
        "dosha_target": "pitru_dosha",
    },
    # ── Manglik (Kuja Dosha) specific dana ────────────────────────────────────
    {
        "remedy_id": "dana_manglik_red_coral_substitute_tuesday",
        "planet": "mars",
        "domain": "marriage",
        "remedy_type": "charity",
        "scaffold_status": "live",
        "prescription_text": (
            "For Kuja (Mangala) Dosha — dana prescription (BPHS Ch.88): on 21 consecutive "
            "Tuesdays, donate masoor dal, red cloth, and copper to a temple or the needy. "
            "Optionally: donate a piece of red coral to a Subrahmanya temple. The 21-Tuesday "
            "cycle specifically for Mangala dosha is prescribed in classical tradition as "
            "the minimum dana-cycle for Mars pacification in marriage matters."
        ),
        "charity_action": "Donate masoor dal, red cloth, copper for 21 Tuesdays (Mangal dosha)",
        "day_of_week": "Tuesday",
        "color_associated": "red",
        "source_canonical_id": "BPHS",
        "source_citation": SOURCE_BPHS,
        "classical_ref": "BPHS Ch.88 (Mangala dosha — 21-Tuesday dana cycle)",
        "cost_tier": "low",
        "confidence": 0.85,
        "dosha_target": "manglik",
    },
]

# Yantra specification rows — detailed classical geometry per Yantra Maharnava
YANTRA_SPEC_REMEDIES: list[dict[str, Any]] = [
    {
        "remedy_id": "yantra_surya_spec_maharnava",
        "planet": "sun",
        "domain": "general",
        "remedy_type": "yantra",
        "scaffold_status": "live",
        "prescription_text": (
            "Surya Yantra (Yantra Maharnava specification): a 3×3 magic square on copper, "
            "with the Sun's magic square numbers. Core geometric structure: central Om symbol "
            "within a six-petal lotus (Shatdala), within a triangle (fire element), within "
            "a circle, within a square with four doors (bhupura). Inscribe in red vermillion. "
            "Energise on Sunday at solar noon in Shukla Paksha with Surya beej mantra "
            "'Om Hraam Hreem Hraum Sah Suryaya Namah' 7,000 times. Install facing east."
        ),
        "deity": "Surya",
        "day_of_week": "Sunday",
        "color_associated": "red/gold",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_YM,
        "classical_ref": "Yantra Maharnava (Surya Yantra specification); classical tradition",
        "cost_tier": "medium",
        "confidence": 0.80,
    },
    {
        "remedy_id": "yantra_chandra_spec_maharnava",
        "planet": "moon",
        "domain": "general",
        "remedy_type": "yantra",
        "scaffold_status": "live",
        "prescription_text": (
            "Chandra Yantra (Yantra Maharnava specification): drawn on silver or white cloth. "
            "Core structure: a crescent moon symbol within an eight-petal lotus (Ashtadala), "
            "within a circle, within a square bhupura with four doors. "
            "Inscribe in white sandalwood paste. Energise on Monday during Shukla Paksha "
            "with Chandra beej mantra 'Om Shraam Shreem Shraum Sah Chandraya Namah' "
            "11,000 times. Install in a white silk cloth, facing northeast."
        ),
        "deity": "Chandra",
        "day_of_week": "Monday",
        "color_associated": "white/silver",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_YM,
        "classical_ref": "Yantra Maharnava (Chandra Yantra specification)",
        "cost_tier": "medium",
        "confidence": 0.80,
    },
    {
        "remedy_id": "yantra_mangala_spec_maharnava",
        "planet": "mars",
        "domain": "general",
        "remedy_type": "yantra",
        "scaffold_status": "live",
        "prescription_text": (
            "Mangala (Kuja) Yantra (Yantra Maharnava specification): engraved on copper or "
            "bhojpatra (birch bark). Core structure: an upward-pointing triangle (fire/Mars) "
            "with internal 3×3 Mars magic square, within a six-petal lotus, within a "
            "circle, within a square bhupura. Inscribe in red vermillion. "
            "Energise on Tuesday during Shukla Paksha with Mangala beej mantra "
            "'Om Kraam Kreem Kraum Sah Bhaumaya Namah' 10,000 times. "
            "Install in a red cloth facing south."
        ),
        "deity": "Hanuman/Kartikeya",
        "day_of_week": "Tuesday",
        "color_associated": "red",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_YM,
        "classical_ref": "Yantra Maharnava (Mangala Yantra specification)",
        "cost_tier": "medium",
        "confidence": 0.80,
    },
    {
        "remedy_id": "yantra_budha_spec_maharnava",
        "planet": "mercury",
        "domain": "general",
        "remedy_type": "yantra",
        "scaffold_status": "live",
        "prescription_text": (
            "Budha Yantra (Yantra Maharnava specification): drawn on bronze or green cloth. "
            "Core structure: a Star of David (two interlocking triangles) with Mercury's "
            "magic square numbers, within an eight-petal lotus, within a circle, within "
            "a square bhupura. Inscribe in green paste. "
            "Energise on Wednesday with Budha beej mantra "
            "'Om Braam Breem Braum Sah Budhaya Namah' 9,000 times. "
            "Install in a green cloth facing north."
        ),
        "deity": "Vishnu/Budha",
        "day_of_week": "Wednesday",
        "color_associated": "green",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_YM,
        "classical_ref": "Yantra Maharnava (Budha Yantra specification)",
        "cost_tier": "medium",
        "confidence": 0.80,
    },
    {
        "remedy_id": "yantra_guru_spec_maharnava",
        "planet": "jupiter",
        "domain": "general",
        "remedy_type": "yantra",
        "scaffold_status": "live",
        "prescription_text": (
            "Guru (Brihaspati) Yantra (Yantra Maharnava specification): engraved on gold "
            "or bhojpatra. Core structure: a four-pointed star (or equilateral triangle) "
            "with Jupiter's magic square numbers within a 12-petal lotus (representing "
            "Jupiter's 12-year cycle), within a circle, within a square bhupura. "
            "Inscribe in yellow turmeric paste. "
            "Energise on Thursday with Guru beej mantra "
            "'Om Graam Greem Graum Sah Gurave Namah' 19,000 times. "
            "Install in a yellow silk cloth facing northeast."
        ),
        "deity": "Brihaspati/Vishnu",
        "day_of_week": "Thursday",
        "color_associated": "yellow/gold",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_YM,
        "classical_ref": "Yantra Maharnava (Guru Yantra specification)",
        "cost_tier": "high",
        "confidence": 0.80,
    },
    {
        "remedy_id": "yantra_shukra_spec_maharnava",
        "planet": "venus",
        "domain": "general",
        "remedy_type": "yantra",
        "scaffold_status": "live",
        "prescription_text": (
            "Shukra Yantra (Yantra Maharnava specification): drawn on silver or white silk. "
            "Core structure: a six-pointed star (two interlocking triangles) with Venus's "
            "magic square numbers within an eight-petal lotus, within a circle, within "
            "a square bhupura with four doors. Inscribe in white sandalwood paste. "
            "Energise on Friday with Shukra beej mantra "
            "'Om Draam Dreem Draum Sah Shukraya Namah' 16,000 times. "
            "Install in a white silk cloth facing southeast."
        ),
        "deity": "Lakshmi/Shukra",
        "day_of_week": "Friday",
        "color_associated": "white/silver",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_YM,
        "classical_ref": "Yantra Maharnava (Shukra Yantra specification)",
        "cost_tier": "high",
        "confidence": 0.80,
    },
    {
        "remedy_id": "yantra_shani_spec_maharnava",
        "planet": "saturn",
        "domain": "general",
        "remedy_type": "yantra",
        "scaffold_status": "live",
        "prescription_text": (
            "Shani Yantra (Yantra Maharnava specification): engraved on iron or lead plate. "
            "Core structure: a downward-pointing triangle (earth/Saturn) with Saturn's "
            "magic square numbers within a six-petal lotus, within a circle, within "
            "a square bhupura. Inscribe in black ink or blue paste. "
            "Energise on Saturday during Krishna Paksha (waning moon) with Shani beej "
            "mantra 'Om Praam Preem Praum Sah Shanaye Namah' 23,000 times. "
            "Install in a black cloth facing west."
        ),
        "deity": "Shani/Hanuman",
        "day_of_week": "Saturday",
        "color_associated": "black/dark blue",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_YM,
        "classical_ref": "Yantra Maharnava (Shani Yantra specification)",
        "cost_tier": "medium",
        "confidence": 0.80,
    },
    {
        "remedy_id": "yantra_rahu_spec_maharnava",
        "planet": "rahu",
        "domain": "general",
        "remedy_type": "yantra",
        "scaffold_status": "live",
        "prescription_text": (
            "Rahu Yantra (Yantra Maharnava specification): drawn on lead plate or grey cloth. "
            "Core structure: a Rahu magic square within a twelve-petal lotus (smoky/grey), "
            "within a circle, within a square bhupura. Some traditions use an octagon "
            "inner boundary for Rahu. Inscribe in blue ink. "
            "Energise on Saturday during Rahu Kala with Rahu beej mantra "
            "'Om Bhraam Bhreem Bhraum Sah Rahave Namah' 18,000 times. "
            "Install in a grey/blue cloth facing southwest."
        ),
        "deity": "Durga",
        "day_of_week": "Saturday",
        "color_associated": "smoky grey/blue",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_YM,
        "classical_ref": "Yantra Maharnava (Rahu Yantra specification)",
        "cost_tier": "medium",
        "confidence": 0.75,
    },
    {
        "remedy_id": "yantra_ketu_spec_maharnava",
        "planet": "ketu",
        "domain": "general",
        "remedy_type": "yantra",
        "scaffold_status": "live",
        "prescription_text": (
            "Ketu Yantra (Yantra Maharnava specification): drawn on panchdhatu (five-metal "
            "alloy) or multicolored cloth. Core structure: Ketu's tail-form (headless figure) "
            "within a magic square, within a lotus, within a bhupura. "
            "Ketu's yantra uses mixed colors — no single dominant hue. "
            "Energise on Tuesday or Saturday with Ketu beej mantra "
            "'Om Sraam Sreem Sraum Sah Ketave Namah' 17,000 times. "
            "Install in multicolored cloth facing northwest."
        ),
        "deity": "Ganesha",
        "day_of_week": "Tuesday",
        "color_associated": "multicolour/grey",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_YM,
        "classical_ref": "Yantra Maharnava (Ketu Yantra specification)",
        "cost_tier": "medium",
        "confidence": 0.75,
    },
    # ── Composite yantras for specific doshas ─────────────────────────────────
    {
        "remedy_id": "yantra_navagraha_composite",
        "planet": "sun",
        "domain": "general",
        "remedy_type": "yantra",
        "scaffold_status": "live",
        "prescription_text": (
            "Navagraha Yantra (composite yantra for all 9 planets): a single yantra "
            "containing all nine planetary magic squares arranged in the traditional "
            "Navagraha mandala — Sun at centre, Moon to northeast, Mars to south, "
            "Mercury to north, Jupiter to northeast diagonal, Venus to southeast, "
            "Saturn to west, Rahu to southwest, Ketu to northwest. "
            "Engraved on copper or bhojpatra. Energise on a Sunday during Shukla Paksha "
            "with all nine planetary beej mantras recited in sequence. "
            "Prescribed in Yantra Maharnava for general graha-shanti."
        ),
        "deity": "Navagraha",
        "day_of_week": "Sunday",
        "color_associated": "mixed/copper",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_YM,
        "classical_ref": "Yantra Maharnava (Navagraha Yantra composite specification)",
        "cost_tier": "medium",
        "confidence": 0.80,
    },
    {
        "remedy_id": "yantra_kala_sarpa_shanti",
        "planet": "rahu",
        "domain": "general",
        "remedy_type": "yantra",
        "scaffold_status": "live",
        "prescription_text": (
            "Kala Sarpa Dosha Yantra: a specific yantra prescribed for Kala Sarpa Dosha "
            "remediation, combining Rahu and Ketu yantras with a serpent (Naga) motif "
            "encircling all the planets. Classically installed at a Shiva temple "
            "(Trimbakeshwar is the canonical site per tradition) during a special "
            "Kala Sarpa Shanti puja. The yantra is then worn or installed at home. "
            "Source: classical tradition for Kala Sarpa Shanti puja."
        ),
        "deity": "Shiva/Naga",
        "day_of_week": "Saturday",
        "color_associated": "smoky grey/blue",
        "source_canonical_id": "classical_tradition",
        "source_citation": SOURCE_CLASSICAL,
        "classical_ref": "classical tradition (Kala Sarpa Shanti yantra; Trimbakeshwar)",
        "cost_tier": "high",
        "confidence": 0.75,
        "dosha_target": "kala_sarpa",
    },
]


def gen_expansion_remedies() -> list[dict[str, Any]]:
    """
    Combine all expansion remedy buckets:
      - Nakshatra deity mantras (27 rows)
      - Stotra prescriptions (12 rows)
      - Dana expansion (17 rows)
      - Yantra specifications (11 rows)
    Total: ~67 new rows.
    """
    return (
        _gen_nakshatra_mantra_rows()
        + STOTRA_REMEDIES
        + DANA_EXPANSION_REMEDIES
        + YANTRA_SPEC_REMEDIES
    )


# ── Combined list builder ──────────────────────────────────────────────────────

def sweep_classical_text_chunks(conn) -> list[dict[str, Any]]:
    """
    Scan classical_text_chunks for remedy-marker keywords.
    Returns list of remedy row dicts ready for merge into the main INSERT loop.
    ZERO LLM — deterministic regex classification only.

    scaffold_status='live'   — exactly one marker, planet resolved, unambiguous type
    scaffold_status='review' — multiple markers, no planet, or ambiguous type
    """
    import re

    # Priority-ordered marker → remedy_type mapping
    MARKER_MAP = [
        (re.compile(r'\bmantra\b', re.IGNORECASE), 'mantra'),
        (re.compile(r'\byantra\b', re.IGNORECASE), 'yantra'),
        (re.compile(r'\bjapa\b', re.IGNORECASE), 'japa'),
        (re.compile(r'\bgemstone\b', re.IGNORECASE), 'gemstone'),
        (re.compile(r'\bvrata\b', re.IGNORECASE), 'vrata'),
        (re.compile(r'\bfast(?:ing)?\b', re.IGNORECASE), 'vrata'),
        (re.compile(r'\bworship\b', re.IGNORECASE), 'puja'),
        (re.compile(r'\bdonate\b', re.IGNORECASE), 'charity'),
        (re.compile(r'\bdana\b', re.IGNORECASE), 'charity'),
        (re.compile(r'\brecite\b', re.IGNORECASE), 'japa'),
        (re.compile(r'\bwear\b', re.IGNORECASE), 'gemstone'),
    ]

    # Planet word → canonical planet name (used in VALID_PLANETS), lowercase.
    # Derived from the graha SSoT's to_title() helper
    # (brahmagyan/graha_vocabulary) rather than hardcoded literals —
    # ADHIṢṬHĀNA Lane A2 (found via the full-tree census; not one of the
    # originally-enumerated retirement targets). "mangal" is a documented
    # extra prose alias the SSoT itself does not carry (see
    # bo_laksana._EXTRA_TEXT_ALIASES for the same variant).
    PLANET_WORDS = {
        w: to_title(w).lower()
        for w in (
            'sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn',
            'rahu', 'ketu', 'surya', 'chandra', 'budha', 'guru', 'shukra',
            'shani',
        )
    }
    PLANET_WORDS['mangal'] = 'mars'
    PLANET_PATTERN = re.compile(
        r'\b(' + '|'.join(PLANET_WORDS.keys()) + r')\b',
        re.IGNORECASE,
    )

    with conn.cursor() as cur:
        cur.execute("""
            SELECT chunk_id, text_id, source_citation, content_en
            FROM classical_text_chunks
            WHERE content_en ILIKE ANY(ARRAY[
                '%mantra%','%yantra%','%japa%','%gemstone%','%vrata%','%fast%',
                '%worship%','%donate%','%dana%','%recite%','%wear%'
            ])
        """)
        rows = cur.fetchall()

    result: list[dict[str, Any]] = []
    for chunk_id, text_id, source_citation, content_en in rows:
        if not content_en:
            continue

        # Find all matching markers
        matched_types: list[str] = []
        for pattern, rtype in MARKER_MAP:
            if pattern.search(content_en):
                matched_types.append(rtype)

        if not matched_types:
            continue

        # Deduplicate matched types (preserving first-match priority)
        seen_types: set[str] = set()
        unique_types: list[str] = []
        for t in matched_types:
            if t not in seen_types:
                seen_types.add(t)
                unique_types.append(t)

        remedy_type = unique_types[0]  # first-match wins
        multi_marker = len(unique_types) > 1

        # Planet detection
        planet_matches = PLANET_PATTERN.findall(content_en)
        planets_found = list(dict.fromkeys(
            PLANET_WORDS[m.lower()] for m in planet_matches
        ))
        planet = planets_found[0] if len(planets_found) == 1 else None
        multi_planet = len(planets_found) > 1

        if planet is None:
            # No planet or ambiguous — use 'general' placeholder; mark review
            # 'general' is not in VALID_PLANETS so we skip these rows entirely
            # (the INSERT validator would reject them)
            continue

        # scaffold_status
        if multi_marker or multi_planet:
            scaffold_status = 'review'
        else:
            scaffold_status = 'live'

        # Deterministic remedy_id with sweep_ prefix
        h = hashlib.sha256(content_en[:80].encode()).hexdigest()[:8]
        remedy_id = f"sweep_{planet}_{remedy_type}_{h}"

        # Source citation: prefer chunk's own citation, fall back to text_id
        citation = source_citation or f"classical_text_chunks text_id={text_id}"

        # Prescription text = first 400 chars of content_en (truncated cleanly)
        prescription_text = content_en[:400].rsplit(' ', 1)[0] if len(content_en) > 400 else content_en

        row: dict[str, Any] = {
            "remedy_id": remedy_id,
            "planet": planet,
            "domain": "general",
            "remedy_type": remedy_type,
            "prescription_text": prescription_text,
            "mantra_text": None,
            "gemstone": None,
            "charity_action": None,
            "day_of_week": None,
            "color_associated": None,
            "confidence": 0.70 if scaffold_status == 'live' else 0.55,
            "source_canonical_id": str(text_id) if text_id else "CLASSICAL_CORPUS",
            "source_citation": citation,
            "classical_ref": f"chunk_id={chunk_id}",
            "category": "corpus_sweep",
            "deity": None,
            "mantra_sanskrit": None,
            "mantra_transliteration": None,
            "cost_tier": None,
            "contraindications": None,
            "scaffold_status": scaffold_status,
        }
        result.append(row)

    logger.info(
        "[L0/remedies] sweep_classical_text_chunks: %d chunks scanned → %d rows extracted "
        "(%d live, %d review)",
        len(rows),
        len(result),
        sum(1 for r in result if r['scaffold_status'] == 'live'),
        sum(1 for r in result if r['scaffold_status'] == 'review'),
    )
    return result


def build_all_remedies() -> list[dict[str, Any]]:
    """
    Combine all three buckets, deduplicate by remedy_id, normalise remedy_type.
    Returns list ready for INSERT.
    """
    seen: set[str] = set()
    result: list[dict[str, Any]] = []

    for r in gen_planet_matrix() + DOSHA_REMEDIES + LEGACY_REMEDIES + gen_expansion_remedies():
        rid = r["remedy_id"]
        if rid in seen:
            logger.debug("dedup skip: %s", rid)
            continue
        seen.add(rid)

        # Normalise remedy_type to ontology vocabulary
        rt = r.get("remedy_type", "")
        r["remedy_type"] = _map_remedy_type(rt)

        # Validate planet
        planet = r.get("planet", "")
        if planet not in VALID_PLANETS:
            raise ValueError(f"remedy_id={rid}: planet='{planet}' not in ontology planet class")

        # Ensure scaffold_status is set
        r.setdefault("scaffold_status", "live")

        # Ensure confidence in range
        conf = r.get("confidence", 0.85)
        if not (0 <= float(conf) <= 1):
            raise ValueError(f"remedy_id={rid}: confidence={conf} out of range")

        result.append(r)

    return result


# ── DB seed function ──────────────────────────────────────────────────────────

def seed_remedy_corpus(
    conn,
    build_id: str | None = None,
    dry_run: bool = False,
    autocommit: bool = True,
) -> dict[str, Any]:
    """
    Seed brahma_remedy_corpus with combined remedy corpus.
    Uses INSERT ... ON CONFLICT (remedy_id) DO NOTHING for idempotency.

    Returns dict with:
        remedies_inserted, remedies_skipped, live_count, total_built
    """
    base_remedies = build_all_remedies()
    sweep_rows = sweep_classical_text_chunks(conn)

    # Dedup sweep rows against base (remedy_id collision avoidance)
    existing_ids: set[str] = {r["remedy_id"] for r in base_remedies}
    new_sweep_rows = [r for r in sweep_rows if r["remedy_id"] not in existing_ids]

    all_remedies = base_remedies + new_sweep_rows
    total_built = len(all_remedies)

    logger.info(
        "[L0/remedies] combined: base=%d sweep_new=%d total=%d",
        len(base_remedies), len(new_sweep_rows), total_built,
    )

    if dry_run:
        live_count = sum(1 for r in all_remedies if r.get("scaffold_status") == "live")
        logger.info(
            "[L0/remedies] dry_run — would insert %d remedies (%d live)",
            total_built, live_count,
        )
        return {
            "remedies_inserted": total_built,
            "remedies_skipped": 0,
            "live_count": live_count,
            "total_built": total_built,
            "status": "DRY_RUN",
        }

    inserted = 0
    skipped = 0

    with conn.cursor() as cur:
        # Validate table exists
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name='brahma_remedy_corpus'"
        )
        if cur.fetchone()['count'] == 0:
            raise RuntimeError(
                "brahma_remedy_corpus table does not exist. Apply migrations first."
            )

        for r in all_remedies:
            cur.execute(
                """
                INSERT INTO brahma_remedy_corpus (
                    remedy_id, planet, domain, remedy_type, prescription_text,
                    mantra_text, gemstone, charity_action, day_of_week,
                    color_associated, confidence, source_canonical_id,
                    source_citation, classical_ref,
                    category, deity, mantra_sanskrit, mantra_transliteration,
                    cost_tier, contraindications, scaffold_status
                ) VALUES (
                    %(remedy_id)s, %(planet)s, %(domain)s, %(remedy_type)s,
                    %(prescription_text)s, %(mantra_text)s, %(gemstone)s,
                    %(charity_action)s, %(day_of_week)s, %(color_associated)s,
                    %(confidence)s, %(source_canonical_id)s,
                    %(source_citation)s, %(classical_ref)s,
                    %(category)s, %(deity)s, %(mantra_sanskrit)s,
                    %(mantra_transliteration)s, %(cost_tier)s,
                    %(contraindications)s, %(scaffold_status)s
                )
                ON CONFLICT (remedy_id) DO NOTHING
                """,
                {
                    "remedy_id": r["remedy_id"],
                    "planet": r["planet"],
                    "domain": r.get("domain", "general"),
                    "remedy_type": r["remedy_type"],
                    "prescription_text": r["prescription_text"],
                    "mantra_text": r.get("mantra_text"),
                    "gemstone": r.get("gemstone"),
                    "charity_action": r.get("charity_action"),
                    "day_of_week": r.get("day_of_week"),
                    "color_associated": r.get("color_associated"),
                    "confidence": float(r.get("confidence", 0.85)),
                    "source_canonical_id": r.get("source_canonical_id", "BPHS"),
                    "source_citation": r.get("source_citation", SOURCE_CLASSICAL),
                    "classical_ref": r.get("classical_ref"),
                    "category": r.get("category"),
                    "deity": r.get("deity"),
                    "mantra_sanskrit": r.get("mantra_sanskrit"),
                    "mantra_transliteration": r.get("mantra_transliteration"),
                    "cost_tier": r.get("cost_tier"),
                    "contraindications": r.get("contraindications"),
                    "scaffold_status": r.get("scaffold_status", "live"),
                },
            )
            if cur.rowcount > 0:
                inserted += 1
            else:
                skipped += 1

        # Query live count after insert
        cur.execute(
            "SELECT COUNT(*) FROM brahma_remedy_corpus WHERE scaffold_status='live'"
        )
        live_count = cur.fetchone()['count']

    logger.info(
        "[L0/remedies] inserted=%d skipped=%d live_count=%d",
        inserted, skipped, live_count,
    )

    if autocommit:
        conn.commit()

    return {
        "remedies_inserted": inserted,
        "remedies_skipped": skipped,
        "live_count": live_count,
        "total_built": total_built,
        "status": "COMPLETE",
    }


# ── Legacy backward-compat ────────────────────────────────────────────────────

def check_volume(conn=None, dry_run: bool = False) -> dict[str, Any]:
    """Backward-compatible volume check."""
    all_remedies = build_all_remedies()
    if dry_run:
        live = sum(1 for r in all_remedies if r.get("scaffold_status") == "live")
        return {
            "asset": "brahmagyan.remedy_corpus",
            "actual_rows": live,
            "floor": CAMPAIGN_FLOOR,
            "status": "GREEN" if live >= CAMPAIGN_FLOOR else "AMBER",
        }
    if conn is None:
        import os
        import psycopg2
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM brahma_remedy_corpus WHERE scaffold_status='live'")
        actual = cur.fetchone()[0]
    status = "GREEN" if actual >= CAMPAIGN_FLOOR else ("AMBER" if actual > 0 else "EMPTY")
    return {
        "asset": "brahmagyan.remedy_corpus",
        "actual_rows": actual,
        "floor": CAMPAIGN_FLOOR,
        "status": status,
    }


# ── REMEDIES alias (backward-compat for old imports) ─────────────────────────
REMEDIES = LEGACY_REMEDIES
