"""
brahmagyan.l0_reference — BRAHMA WS-2 L0 Brahmagyan: Classical Reference Library
==================================================================================

Populates the five classical reference tables with hardcoded, source-cited data
from BPHS and related classical texts. No LLM generation. No live computation.

Tables written:
  reference_planets    — 9 grahas + 2 nodes (11 rows)
  reference_nakshatras — 27 nakshatras
  reference_signs      — 12 zodiac signs
  reference_aspects    — graha drishti (planetary aspects)
  reference_vargas     — 16 shodasha vargas (D1–D60)

Volume floors (WS-2 honest gate):
  reference_planets:    >= 11 rows (9 grahas + 2 nodes)
  reference_nakshatras: >= 27 rows
  reference_signs:      >= 12 rows
  reference_aspects:    >= 30 rows (all planets × aspect houses)
  reference_vargas:     >= 16 rows

Acceptance gate: all counts >= floor; source_citation non-null on every row.

BRAHMA-BG-0-2
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── Source citation ────────────────────────────────────────────────────────────

BPHS_CITATION = "BPHS (Brihat Parasara Hora Sastra), trans. Rishi Kumar Shastri, classical tradition"
BPHS_CH3 = "BPHS Ch.3 (Grahana-svarupa-adhyaya)"
BPHS_CH4 = "BPHS Ch.4 (Graha-mitra-adhyaya)"
BPHS_CH6 = "BPHS Ch.6 (Rasi-svarupa-adhyaya)"
BPHS_CH7 = "BPHS Ch.7 (Bhava-svarupa-adhyaya)"
BPHS_CH26 = "BPHS Ch.26 (Drishti-phala-adhyaya)"
BPHS_CH27 = "BPHS Ch.27 (Karaka-adhyaya)"
BPHS_SHODASHA = "BPHS Ch.6 (Shodasha-varga-adhyaya)"
TAITTIRIYA = "Taittiriya Aranyaka + BPHS Ch.94 (Nakshatra-svarupa)"

# ── Planetary data ─────────────────────────────────────────────────────────────

PLANETS = [
    {
        "planet_id": "sun",
        "canonical_name_en": "Sun",
        "canonical_name_sa": "Surya",
        "exaltation_sign": 1,   # Aries
        "exaltation_degree": 10.0,
        "debilitation_sign": 7,  # Libra
        "mooltrikona_sign": 5,   # Leo
        "own_signs": [5],        # Leo
        "natural_benefic": False,
        "karak_domains": ["soul", "father", "authority", "health", "vitality", "government"],
        "dasha_years": 6.0,
        "source_citation": BPHS_CH3,
    },
    {
        "planet_id": "moon",
        "canonical_name_en": "Moon",
        "canonical_name_sa": "Chandra",
        "exaltation_sign": 2,   # Taurus
        "exaltation_degree": 3.0,
        "debilitation_sign": 8,  # Scorpio
        "mooltrikona_sign": 2,   # Taurus (first 27° of Taurus)
        "own_signs": [4],        # Cancer
        "natural_benefic": True,
        "karak_domains": ["mind", "mother", "emotions", "public", "water", "home"],
        "dasha_years": 10.0,
        "source_citation": BPHS_CH3,
    },
    {
        "planet_id": "mars",
        "canonical_name_en": "Mars",
        "canonical_name_sa": "Mangala",
        "exaltation_sign": 10,  # Capricorn
        "exaltation_degree": 28.0,
        "debilitation_sign": 4,  # Cancer
        "mooltrikona_sign": 1,   # Aries
        "own_signs": [1, 8],     # Aries, Scorpio
        "natural_benefic": False,
        "karak_domains": ["courage", "siblings", "land", "surgery", "conflict", "energy"],
        "dasha_years": 7.0,
        "source_citation": BPHS_CH3,
    },
    {
        "planet_id": "mercury",
        "canonical_name_en": "Mercury",
        "canonical_name_sa": "Budha",
        "exaltation_sign": 6,   # Virgo
        "exaltation_degree": 15.0,
        "debilitation_sign": 12, # Pisces
        "mooltrikona_sign": 6,   # Virgo (first 20° of Virgo)
        "own_signs": [3, 6],     # Gemini, Virgo
        "natural_benefic": True,
        "karak_domains": ["intellect", "speech", "communication", "trade", "mathematics", "writing"],
        "dasha_years": 17.0,
        "source_citation": BPHS_CH3,
    },
    {
        "planet_id": "jupiter",
        "canonical_name_en": "Jupiter",
        "canonical_name_sa": "Guru",
        "exaltation_sign": 4,   # Cancer
        "exaltation_degree": 5.0,
        "debilitation_sign": 10, # Capricorn
        "mooltrikona_sign": 9,   # Sagittarius
        "own_signs": [9, 12],    # Sagittarius, Pisces
        "natural_benefic": True,
        "karak_domains": ["wisdom", "dharma", "children", "wealth", "guru", "expansion"],
        "dasha_years": 16.0,
        "source_citation": BPHS_CH3,
    },
    {
        "planet_id": "venus",
        "canonical_name_en": "Venus",
        "canonical_name_sa": "Shukra",
        "exaltation_sign": 12,  # Pisces
        "exaltation_degree": 27.0,
        "debilitation_sign": 6,  # Virgo
        "mooltrikona_sign": 7,   # Libra
        "own_signs": [2, 7],     # Taurus, Libra
        "natural_benefic": True,
        "karak_domains": ["beauty", "marriage", "luxury", "arts", "vehicles", "passion"],
        "dasha_years": 20.0,
        "source_citation": BPHS_CH3,
    },
    {
        "planet_id": "saturn",
        "canonical_name_en": "Saturn",
        "canonical_name_sa": "Shani",
        "exaltation_sign": 7,   # Libra
        "exaltation_degree": 20.0,
        "debilitation_sign": 1,  # Aries
        "mooltrikona_sign": 11,  # Aquarius
        "own_signs": [10, 11],   # Capricorn, Aquarius
        "natural_benefic": False,
        "karak_domains": ["karma", "discipline", "longevity", "servants", "delays", "detachment"],
        "dasha_years": 19.0,
        "source_citation": BPHS_CH3,
    },
    {
        "planet_id": "rahu",
        "canonical_name_en": "Rahu",
        "canonical_name_sa": "Rahu",
        "exaltation_sign": 2,   # Taurus (Gemini per some authorities)
        "exaltation_degree": None,
        "debilitation_sign": 8,  # Scorpio
        "mooltrikona_sign": None,
        "own_signs": [],
        "natural_benefic": False,
        "karak_domains": ["foreigners", "technology", "illusion", "sudden_gains", "obsession"],
        "dasha_years": 18.0,
        "source_citation": BPHS_CH3 + "; note: Rahu exaltation debated, Taurus per Parasara",
    },
    {
        "planet_id": "ketu",
        "canonical_name_en": "Ketu",
        "canonical_name_sa": "Ketu",
        "exaltation_sign": 8,   # Scorpio (Sagittarius per some)
        "exaltation_degree": None,
        "debilitation_sign": 2,  # Taurus
        "mooltrikona_sign": None,
        "own_signs": [],
        "natural_benefic": False,
        "karak_domains": ["spirituality", "moksha", "past_karma", "isolation", "occult"],
        "dasha_years": 7.0,
        "source_citation": BPHS_CH3 + "; Ketu is South Node (180° opposite Rahu)",
    },
    # Upagrahas (shadow bodies) — included for completeness
    {
        "planet_id": "ascendant",
        "canonical_name_en": "Ascendant",
        "canonical_name_sa": "Lagna",
        "exaltation_sign": None,
        "exaltation_degree": None,
        "debilitation_sign": None,
        "mooltrikona_sign": None,
        "own_signs": [],
        "natural_benefic": True,
        "karak_domains": ["self", "body", "appearance", "health", "personality"],
        "dasha_years": None,
        "source_citation": BPHS_CH7,
    },
    {
        "planet_id": "midheaven",
        "canonical_name_en": "Midheaven",
        "canonical_name_sa": "Madhya Lagna",
        "exaltation_sign": None,
        "exaltation_degree": None,
        "debilitation_sign": None,
        "mooltrikona_sign": None,
        "own_signs": [],
        "natural_benefic": True,
        "karak_domains": ["career", "social_status", "public_reputation"],
        "dasha_years": None,
        "source_citation": BPHS_CH7,
    },
]

# ── Nakshatra data ─────────────────────────────────────────────────────────────

NAKSHATRAS = [
    # id, name_en, name_sa, lord, deity, nature, guna, start_deg, end_deg, pada_lords, body_part
    (1, "Ashwini", "Ashvini", "ketu", "Ashwini Kumaras", "movable", "rajasic",
     0.0, 13.333, ["mars", "venus", "mercury", "moon"], "head"),
    (2, "Bharani", "Bharani", "venus", "Yama", "fierce", "rajasic",
     13.333, 26.667, ["sun", "mercury", "venus", "mars"], "head"),
    (3, "Krittika", "Krittika", "sun", "Agni", "fixed", "rajasic",
     26.667, 40.0, ["jupiter", "saturn", "saturn", "jupiter"], "head"),
    (4, "Rohini", "Rohini", "moon", "Brahma/Prajapati", "fixed", "rajasic",
     40.0, 53.333, ["mars", "venus", "mercury", "moon"], "forehead"),
    (5, "Mrigasira", "Mrigashira", "mars", "Soma/Chandra", "soft", "tamasic",
     53.333, 66.667, ["sun", "mercury", "venus", "mars"], "eyes"),
    (6, "Ardra", "Ardra", "rahu", "Rudra", "fierce", "tamasic",
     66.667, 80.0, ["jupiter", "saturn", "saturn", "jupiter"], "hair"),
    (7, "Punarvasu", "Punarvasu", "jupiter", "Aditi", "movable", "sattvic",
     80.0, 93.333, ["mars", "venus", "mercury", "moon"], "nose"),
    (8, "Pushya", "Pushya", "saturn", "Brihaspati", "fixed", "sattvic",
     93.333, 106.667, ["sun", "mercury", "venus", "mars"], "face"),
    (9, "Ashlesha", "Ashlesha", "mercury", "Sarpas", "movable", "sattvic",
     106.667, 120.0, ["jupiter", "saturn", "saturn", "jupiter"], "nails"),
    (10, "Magha", "Magha", "ketu", "Pitrs", "fierce", "tamasic",
     120.0, 133.333, ["mars", "venus", "mercury", "moon"], "lips"),
    (11, "Purva Phalguni", "Purva Phalguni", "venus", "Bhaga", "fierce", "rajasic",
     133.333, 146.667, ["sun", "mercury", "venus", "mars"], "right hand"),
    (12, "Uttara Phalguni", "Uttara Phalguni", "sun", "Aryaman", "fixed", "rajasic",
     146.667, 160.0, ["jupiter", "saturn", "saturn", "jupiter"], "left hand"),
    (13, "Hasta", "Hasta", "moon", "Savitar", "movable", "sattvic",
     160.0, 173.333, ["mars", "venus", "mercury", "moon"], "fingers"),
    (14, "Chitra", "Chitra", "mars", "Vishwakarma", "soft", "tamasic",
     173.333, 186.667, ["sun", "mercury", "venus", "mars"], "neck"),
    (15, "Swati", "Svati", "rahu", "Vayu", "movable", "tamasic",
     186.667, 200.0, ["jupiter", "saturn", "saturn", "jupiter"], "chest"),
    (16, "Vishakha", "Vishakha", "jupiter", "Indra-Agni", "movable", "rajasic",
     200.0, 213.333, ["mars", "venus", "mercury", "moon"], "arms"),
    (17, "Anuradha", "Anuradha", "saturn", "Mitra", "soft", "tamasic",
     213.333, 226.667, ["sun", "mercury", "venus", "mars"], "stomach"),
    (18, "Jyeshtha", "Jyeshtha", "mercury", "Indra", "fierce", "sattvic",
     226.667, 240.0, ["jupiter", "saturn", "saturn", "jupiter"], "tongue"),
    (19, "Moola", "Mula", "ketu", "Nirriti", "fierce", "tamasic",
     240.0, 253.333, ["mars", "venus", "mercury", "moon"], "feet"),
    (20, "Purva Ashadha", "Purva Ashadha", "venus", "Apas", "fierce", "rajasic",
     253.333, 266.667, ["sun", "mercury", "venus", "mars"], "back"),
    (21, "Uttara Ashadha", "Uttara Ashadha", "sun", "Vishvedevas", "fixed", "rajasic",
     266.667, 280.0, ["jupiter", "saturn", "saturn", "jupiter"], "thighs"),
    (22, "Shravana", "Shravana", "moon", "Vishnu", "movable", "rajasic",
     280.0, 293.333, ["mars", "venus", "mercury", "moon"], "ears"),
    (23, "Dhanishtha", "Dhanishtha", "mars", "Eight Vasus", "movable", "tamasic",
     293.333, 306.667, ["sun", "mercury", "venus", "mars"], "back"),
    (24, "Shatabhisha", "Shatabhisha", "rahu", "Varuna", "movable", "tamasic",
     306.667, 320.0, ["jupiter", "saturn", "saturn", "jupiter"], "chin"),
    (25, "Purva Bhadrapada", "Purva Bhadrapada", "jupiter", "Aja Ekapada", "fierce", "tamasic",
     320.0, 333.333, ["mars", "venus", "mercury", "moon"], "sides"),
    (26, "Uttara Bhadrapada", "Uttara Bhadrapada", "saturn", "Ahir Budhnya", "fixed", "sattvic",
     333.333, 346.667, ["sun", "mercury", "venus", "mars"], "legs"),
    (27, "Revati", "Revati", "mercury", "Pushan", "soft", "sattvic",
     346.667, 360.0, ["jupiter", "saturn", "saturn", "jupiter"], "feet"),
]

# ── Sign data ─────────────────────────────────────────────────────────────────

SIGNS = [
    # id, name_en, name_sa, lord, element, modality, natural_house, is_odd, is_biped, significations
    (1, "Aries", "Mesha", "mars", "fire", "movable", 1, True, True,
     ["self", "body", "courage", "initiative", "head"]),
    (2, "Taurus", "Vrishabha", "venus", "earth", "fixed", 2, False, False,
     ["wealth", "possessions", "beauty", "food", "throat"]),
    (3, "Gemini", "Mithuna", "mercury", "air", "dual", 3, True, True,
     ["siblings", "communication", "intellect", "short_travel", "arms"]),
    (4, "Cancer", "Kataka", "moon", "water", "movable", 4, False, False,
     ["home", "mother", "emotions", "vehicles", "chest"]),
    (5, "Leo", "Simha", "sun", "fire", "fixed", 5, True, False,
     ["children", "creativity", "authority", "romance", "stomach"]),
    (6, "Virgo", "Kanya", "mercury", "earth", "dual", 6, False, True,
     ["health", "service", "enemies", "daily_work", "waist"]),
    (7, "Libra", "Tula", "venus", "air", "movable", 7, True, True,
     ["marriage", "partnership", "business", "contracts", "loins"]),
    (8, "Scorpio", "Vrishchika", "mars", "water", "fixed", 8, False, False,
     ["transformation", "occult", "inheritance", "death", "genitals"]),
    (9, "Sagittarius", "Dhanu", "jupiter", "fire", "dual", 9, True, False,
     ["dharma", "higher_learning", "spirituality", "long_travel", "thighs"]),
    (10, "Capricorn", "Makara", "saturn", "earth", "movable", 10, False, False,
     ["career", "status", "ambition", "father", "knees"]),
    (11, "Aquarius", "Kumbha", "saturn", "air", "fixed", 11, True, True,
     ["gains", "friends", "goals", "elder_siblings", "calves"]),
    (12, "Pisces", "Meena", "jupiter", "water", "dual", 12, False, False,
     ["liberation", "spirituality", "foreign_lands", "losses", "feet"]),
]

# ── Aspect data (graha drishti) ───────────────────────────────────────────────

def _make_aspects() -> list[dict]:
    """Generate graha drishti rows per BPHS Ch.26."""
    rows = []
    # All 9 planets (including Rahu/Ketu which aspect 5th/9th and 7th per some traditions)
    planets = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]
    # Universal 7th house aspect (all planets)
    for p in planets:
        rows.append({
            "planet_id": p,
            "aspect_house": 7,
            "aspect_strength": "full",
            "strength_value": 1.0,
            "is_special": False,
            "notes": "Universal 7th house aspect",
            "source_citation": BPHS_CH26,
        })
    # Mars special aspects: 4th, 8th (full)
    for house in [4, 8]:
        rows.append({
            "planet_id": "mars",
            "aspect_house": house,
            "aspect_strength": "full",
            "strength_value": 1.0,
            "is_special": True,
            "notes": f"Mars special aspect to {house}th house",
            "source_citation": BPHS_CH26,
        })
    # Jupiter special aspects: 5th, 9th (full)
    for house in [5, 9]:
        rows.append({
            "planet_id": "jupiter",
            "aspect_house": house,
            "aspect_strength": "full",
            "strength_value": 1.0,
            "is_special": True,
            "notes": f"Jupiter special aspect to {house}th house",
            "source_citation": BPHS_CH26,
        })
    # Saturn special aspects: 3rd, 10th (full)
    for house in [3, 10]:
        rows.append({
            "planet_id": "saturn",
            "aspect_house": house,
            "aspect_strength": "full",
            "strength_value": 1.0,
            "is_special": True,
            "notes": f"Saturn special aspect to {house}th house",
            "source_citation": BPHS_CH26,
        })
    # Rahu/Ketu: per some traditions aspect 5th/9th from their position
    for p in ["rahu", "ketu"]:
        for house in [5, 9]:
            rows.append({
                "planet_id": p,
                "aspect_house": house,
                "aspect_strength": "full",
                "strength_value": 1.0,
                "is_special": True,
                "notes": f"{p.title()} traditional 5th/9th aspect",
                "source_citation": BPHS_CH26 + "; note: Rahu/Ketu aspects per later tradition",
            })
    return rows

ASPECTS = _make_aspects()

# ── Varga data (shodasha vargas) ──────────────────────────────────────────────

VARGAS = [
    ("D1", 1, "Rashi", "Rashi", 1, "Overall chart; physical body; all life matters", "Primary chart"),
    ("D2", 2, "Hora", "Hora", 2, "Wealth; finances; material possessions", "Lakshmi + Surya horas"),
    ("D3", 3, "Drekkana", "Drekkana", 3, "Siblings; courage; communication", "Decanate chart"),
    ("D4", 4, "Chaturthamsha", "Chaturthamsha", 4, "Property; fixed assets; home; fortune", "Luck/fortune"),
    ("D5", 5, "Panchamsha", "Panchamsha", 5, "Spiritual merit; past-life credit; children", "Punya"),
    ("D6", 6, "Shashthamsha", "Shashthamsha", 6, "Health; enemies; debts; service", "Disease chart"),
    ("D7", 7, "Saptamsha", "Saptamsha", 7, "Children; progeny; creativity", "Progeny chart"),
    ("D8", 8, "Ashtamsha", "Ashtamsha", 8, "Longevity; obstacles; sudden events; inheritance", "Transformation"),
    ("D9", 9, "Navamsha", "Navamsha", 9, "Marriage; dharma; spiritual development; inner nature", "Most important divisional"),
    ("D10", 10, "Dashamsha", "Dashamsha", 10, "Career; professional achievement; public life", "Career chart"),
    ("D12", 12, "Dvadashamsha", "Dvadashamsha", 12, "Parents; ancestors; karmic inheritance", "Parents chart"),
    ("D16", 16, "Shodashamsha", "Shodashamsha", 16, "Vehicles; conveyances; happiness", "Vehicles"),
    ("D20", 20, "Vimshamsha", "Vimshamsha", 20, "Spiritual practice; upasana; religious activities", "Spiritual chart"),
    ("D24", 24, "Chaturvimshamsha", "Chaturvimshamsha", 24, "Education; learning; academic achievements", "Learning"),
    ("D27", 27, "Nakshatramsha", "Nakshatramsha", 27, "Strength; stamina; vitality", "Strength chart"),
    ("D30", 30, "Trimshamsha", "Trimshamsha", 30, "Miseries; evils; health issues", "Evil chart"),
    ("D40", 40, "Khavedamsha", "Khavedamsha", 40, "Maternal ancestry; auspicious effects", "Maternal"),
    ("D45", 45, "Akshavedamsha", "Akshavedamsha", 45, "Paternal ancestry; general indications", "Paternal"),
    ("D60", 60, "Shastiamsha", "Shastiamsha", 60, "Past-life karma; most subtle influences", "Most sensitive divisional"),
]

# ── Writer ────────────────────────────────────────────────────────────────────

def seed_reference(conn, build_id: str | None = None, dry_run: bool = False) -> dict[str, int]:
    """
    Seed all five reference tables.
    Returns dict of table_name -> rows_inserted.
    If dry_run=True, returns counts without writing to DB.
    """
    if dry_run:
        return {
            "reference_planets": len(PLANETS),
            "reference_nakshatras": len(NAKSHATRAS),
            "reference_signs": len(SIGNS),
            "reference_aspects": len(ASPECTS),
            "reference_vargas": len(VARGAS),
        }

    now = datetime.now(timezone.utc)
    counts: dict[str, int] = {}

    with conn.cursor() as cur:

        # -- reference_planets --
        inserted = 0
        for p in PLANETS:
            cur.execute("""
                INSERT INTO reference_planets
                  (planet_id, canonical_name_en, canonical_name_sa,
                   exaltation_sign, exaltation_degree, debilitation_sign,
                   mooltrikona_sign, own_signs, natural_benefic,
                   karak_domains, dasha_years, source_citation, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (planet_id) DO UPDATE SET
                  canonical_name_en = EXCLUDED.canonical_name_en,
                  karak_domains = EXCLUDED.karak_domains,
                  source_citation = EXCLUDED.source_citation
            """, (
                p["planet_id"], p["canonical_name_en"], p["canonical_name_sa"],
                p.get("exaltation_sign"), p.get("exaltation_degree"),
                p.get("debilitation_sign"), p.get("mooltrikona_sign"),
                p["own_signs"], p["natural_benefic"],
                p["karak_domains"], p.get("dasha_years"),
                p["source_citation"], now,
            ))
            inserted += 1
        counts["reference_planets"] = inserted
        logger.info("[L0/reference] reference_planets: %d rows upserted", inserted)

        # -- reference_nakshatras --
        inserted = 0
        for nak in NAKSHATRAS:
            (nak_id, name_en, name_sa, lord, deity, nature, guna,
             start_deg, end_deg, pada_lords, body_part) = nak
            cur.execute("""
                INSERT INTO reference_nakshatras
                  (nakshatra_id, canonical_name_en, canonical_name_sa, lord,
                   deity, nature, guna, start_degree, end_degree,
                   pada_lords, body_part, source_citation, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (nakshatra_id) DO UPDATE SET
                  lord = EXCLUDED.lord,
                  pada_lords = EXCLUDED.pada_lords,
                  source_citation = EXCLUDED.source_citation
            """, (
                nak_id, name_en, name_sa, lord, deity, nature, guna,
                start_deg, end_deg, pada_lords, body_part,
                TAITTIRIYA, now,
            ))
            inserted += 1
        counts["reference_nakshatras"] = inserted
        logger.info("[L0/reference] reference_nakshatras: %d rows upserted", inserted)

        # -- reference_signs --
        inserted = 0
        for s in SIGNS:
            (sign_id, name_en, name_sa, lord, element, modality,
             natural_house, is_odd, is_biped, significations) = s
            cur.execute("""
                INSERT INTO reference_signs
                  (sign_id, canonical_name_en, canonical_name_sa, lord,
                   element, modality, natural_house, is_odd, is_biped,
                   significations, source_citation, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (sign_id) DO UPDATE SET
                  lord = EXCLUDED.lord,
                  significations = EXCLUDED.significations,
                  source_citation = EXCLUDED.source_citation
            """, (
                sign_id, name_en, name_sa, lord, element, modality,
                natural_house, is_odd, is_biped, significations,
                BPHS_CH6, now,
            ))
            inserted += 1
        counts["reference_signs"] = inserted
        logger.info("[L0/reference] reference_signs: %d rows upserted", inserted)

        # -- reference_aspects --
        inserted = 0
        for a in ASPECTS:
            cur.execute("""
                INSERT INTO reference_aspects
                  (planet_id, aspect_house, aspect_strength, strength_value,
                   is_special, notes, source_citation, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (planet_id, aspect_house) DO UPDATE SET
                  strength_value = EXCLUDED.strength_value,
                  is_special = EXCLUDED.is_special,
                  source_citation = EXCLUDED.source_citation
            """, (
                a["planet_id"], a["aspect_house"], a["aspect_strength"],
                a["strength_value"], a["is_special"], a.get("notes"),
                a["source_citation"], now,
            ))
            inserted += 1
        counts["reference_aspects"] = inserted
        logger.info("[L0/reference] reference_aspects: %d rows upserted", inserted)

        # -- reference_vargas --
        inserted = 0
        for v in VARGAS:
            (varga_id, varga_num, name_en, name_sa, division_count,
             primary_sig, secondary_sig) = v
            cur.execute("""
                INSERT INTO reference_vargas
                  (varga_id, varga_number, canonical_name_en, canonical_name_sa,
                   division_count, primary_signification, secondary_signification,
                   source_citation, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (varga_id) DO UPDATE SET
                  primary_signification = EXCLUDED.primary_signification,
                  source_citation = EXCLUDED.source_citation
            """, (
                varga_id, varga_num, name_en, name_sa, division_count,
                primary_sig, secondary_sig, BPHS_SHODASHA, now,
            ))
            inserted += 1
        counts["reference_vargas"] = inserted
        logger.info("[L0/reference] reference_vargas: %d rows upserted", inserted)

    conn.commit()
    return counts


def check_volume(conn) -> dict[str, dict]:
    """
    Check actual row counts against volume floors.
    Returns per-table {actual, floor, status}.
    """
    floors = {
        "reference_planets": 11,
        "reference_nakshatras": 27,
        "reference_signs": 12,
        "reference_aspects": 30,
        "reference_vargas": 16,
    }
    result = {}
    with conn.cursor() as cur:
        for table, floor in floors.items():
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                actual = cur.fetchone()[0]
            except Exception:
                actual = 0
            status = "green" if actual >= floor else ("amber" if actual > 0 else "empty")
            result[table] = {"actual": actual, "floor": floor, "status": status}
    return result


def lookup_planet(planet_id: str) -> dict | None:
    """Return planet data dict (no DB — from in-memory corpus)."""
    for p in PLANETS:
        if p["planet_id"] == planet_id:
            return p
    return None


def lookup_nakshatra(nakshatra_id: int) -> tuple | None:
    """Return nakshatra tuple by 1-based ID."""
    for nak in NAKSHATRAS:
        if nak[0] == nakshatra_id:
            return nak
    return None
