"""
brahmagyan.l0_ontology — BRAHMA WS-2 L0 Brahmagyan: Controlled Vocabulary / Ontology
======================================================================================

Populates brahma_ontology with canonical entity definitions across classes:
  - planet        — 9 grahas + 2 shadow nodes + ascendant/midheaven
  - nakshatra     — 27 nakshatras
  - sign          — 12 zodiac signs
  - house         — 12 bhavas with natural significations
  - dasha_system  — Vimshottari, Yogini, Chara, Kalachakra
  - domain        — life domains (career, marriage, health, wealth, ...)
  - concept       — key Jyotish concepts (yoga, dosha, strength, ...)

Volume floor: >= 100 entities total
Acceptance gate:
  - resolve('Shani') -> 'saturn' (planet class)
  - resolve('PuraBhadra') -> 'purva_bhadrapada' (nakshatra)
  - COUNT(*) >= 100

BRAHMA-BG-0-5
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

BPHS_CITATION = "BPHS (Brihat Parasara Hora Sastra), classical tradition"

# ── Entity corpus ──────────────────────────────────────────────────────────────

ENTITIES: list[dict] = []

def _e(entity_class: str, canonical_id: str, name_en: str, name_sa: str,
       synonyms: list[str], description: str | None = None) -> dict:
    return {
        "entity_class": entity_class,
        "canonical_id": canonical_id,
        "canonical_name_en": name_en,
        "canonical_name_sa": name_sa,
        "synonyms": synonyms,
        "description": description,
        "source_citation": BPHS_CITATION,
    }

# ── Planets ────────────────────────────────────────────────────────────────────

ENTITIES += [
    _e("planet", "sun", "Sun", "Surya",
       ["surya", "ravi", "aditya", "Sol", "Sūrya", "Arka", "arka", "bhaskar"],
       "Soul, father, authority, vitality; natural malefic"),
    _e("planet", "moon", "Moon", "Chandra",
       ["chandra", "soma", "luna", "indu", "Chandra", "Moon", "chandrama"],
       "Mind, mother, emotions, public; natural benefic"),
    _e("planet", "mars", "Mars", "Mangala",
       ["mangala", "kuja", "angaraka", "bhumi", "Mars", "Mangal"],
       "Courage, siblings, land, surgery; natural malefic"),
    _e("planet", "mercury", "Mercury", "Budha",
       ["budha", "buddha", "Mercury", "Budh"],
       "Intellect, speech, trade, mathematics; natural benefic"),
    _e("planet", "jupiter", "Jupiter", "Guru",
       ["guru", "brihaspati", "brhaspati", "Jupiter", "Brahmanaspati", "devaguru"],
       "Wisdom, dharma, children, expansion; natural benefic"),
    _e("planet", "venus", "Venus", "Shukra",
       ["shukra", "sukra", "Venus", "Bhargava", "usana"],
       "Beauty, marriage, luxury, arts; natural benefic"),
    _e("planet", "saturn", "Saturn", "Shani",
       ["shani", "sani", "Saturn", "shanaischar", "manda", "Shanaischara"],
       "Karma, discipline, longevity, delays; natural malefic"),
    _e("planet", "rahu", "Rahu", "Rahu",
       ["rahu", "caput_draconis", "north_node", "dragon_head", "ascending_node"],
       "North lunar node; foreigners, technology, obsession; shadow planet"),
    _e("planet", "ketu", "Ketu", "Ketu",
       ["ketu", "cauda_draconis", "south_node", "dragon_tail", "descending_node"],
       "South lunar node; spirituality, moksha, past karma; shadow planet"),
    _e("planet", "ascendant", "Ascendant", "Lagna",
       ["lagna", "ascendant", "rising_sign", "udaya_lagna", "AC"],
       "First house cusp; self, body, personality"),
    _e("planet", "midheaven", "Midheaven", "Madhya Lagna",
       ["mc", "midheaven", "madhya_lagna", "medium_coeli"],
       "10th house cusp; career, social status"),
]

# ── Nakshatras ─────────────────────────────────────────────────────────────────

NAK_DATA = [
    (1, "Ashwini", "Ashvini", ["ashwini", "ashvini", "aswini"]),
    (2, "Bharani", "Bharani", ["bharani", "bharni"]),
    (3, "Krittika", "Krittika", ["krittika", "krttika", "kritika"]),
    (4, "Rohini", "Rohini", ["rohini", "rohni"]),
    (5, "Mrigasira", "Mrigashira", ["mrigasira", "mrigashira", "mrigsira", "mrigashirsha"]),
    (6, "Ardra", "Ardra", ["ardra", "aridra"]),
    (7, "Punarvasu", "Punarvasu", ["punarvasu", "punarvashu"]),
    (8, "Pushya", "Pushya", ["pushya", "pushyami", "tishya"]),
    (9, "Ashlesha", "Ashlesha", ["ashlesha", "aslesha", "aslesa"]),
    (10, "Magha", "Magha", ["magha", "makha"]),
    (11, "Purva Phalguni", "Purva Phalguni", ["purva_phalguni", "poorva_phalguni", "pubba"]),
    (12, "Uttara Phalguni", "Uttara Phalguni", ["uttara_phalguni", "uttaraphalguni", "uttara"]),
    (13, "Hasta", "Hasta", ["hasta", "hastam"]),
    (14, "Chitra", "Chitra", ["chitra", "chithrai"]),
    (15, "Swati", "Svati", ["swati", "svati", "swaati"]),
    (16, "Vishakha", "Vishakha", ["vishakha", "visakha", "radha"]),
    (17, "Anuradha", "Anuradha", ["anuradha", "anuradhe"]),
    (18, "Jyeshtha", "Jyeshtha", ["jyeshtha", "jyestha", "kettai"]),
    (19, "Moola", "Mula", ["moola", "mula", "mool"]),
    (20, "Purva Ashadha", "Purva Ashadha", ["purva_ashadha", "poorva_ashadha", "pooradam"]),
    (21, "Uttara Ashadha", "Uttara Ashadha", ["uttara_ashadha", "uttarashadha", "uttaradam"]),
    (22, "Shravana", "Shravana", ["shravana", "sravana", "thiruvonam"]),
    (23, "Dhanishtha", "Dhanishtha", ["dhanishtha", "dhanistha", "sravishtha", "avittam"]),
    (24, "Shatabhisha", "Shatabhisha", ["shatabhisha", "shatabhisaj", "shatabhisak", "sadayam"]),
    (25, "Purva Bhadrapada", "Purva Bhadrapada", ["purva_bhadrapada", "purvabhadra", "poorattadhi"]),
    (26, "Uttara Bhadrapada", "Uttara Bhadrapada", ["uttara_bhadrapada", "uttarabhadra", "uttarattadhi"]),
    (27, "Revati", "Revati", ["revati", "revathi"]),
]

for nak_id, name_en, name_sa, synonyms in NAK_DATA:
    ENTITIES.append(_e(
        "nakshatra", f"nak_{nak_id:02d}_{name_en.lower().replace(' ', '_')}",
        name_en, name_sa, synonyms,
        f"Nakshatra {nak_id}/27",
    ))

# ── Signs ──────────────────────────────────────────────────────────────────────

SIGN_DATA = [
    (1, "Aries", "Mesha", ["aries", "mesha", "mesh"]),
    (2, "Taurus", "Vrishabha", ["taurus", "vrishabha", "vrishab"]),
    (3, "Gemini", "Mithuna", ["gemini", "mithuna", "mithun"]),
    (4, "Cancer", "Kataka", ["cancer", "kataka", "karka"]),
    (5, "Leo", "Simha", ["leo", "simha", "singh"]),
    (6, "Virgo", "Kanya", ["virgo", "kanya"]),
    (7, "Libra", "Tula", ["libra", "tula"]),
    (8, "Scorpio", "Vrishchika", ["scorpio", "vrishchika", "vrishchik", "vrischika"]),
    (9, "Sagittarius", "Dhanu", ["sagittarius", "dhanu", "dhanus"]),
    (10, "Capricorn", "Makara", ["capricorn", "makara", "makar"]),
    (11, "Aquarius", "Kumbha", ["aquarius", "kumbha", "kumbh"]),
    (12, "Pisces", "Meena", ["pisces", "meena", "meen"]),
]

for sign_id, name_en, name_sa, synonyms in SIGN_DATA:
    ENTITIES.append(_e(
        "sign", name_en.lower(),
        name_en, name_sa, synonyms,
        f"Sign {sign_id}/12",
    ))

# ── Houses (Bhavas) ────────────────────────────────────────────────────────────

HOUSE_DATA = [
    (1, "First House", "Prathama Bhava", ["1h", "first_house", "lagna_bhava"],
     "Self, body, personality, appearance, overall health"),
    (2, "Second House", "Dvitiya Bhava", ["2h", "second_house", "dhana_bhava"],
     "Wealth, speech, family, food, face"),
    (3, "Third House", "Tritiya Bhava", ["3h", "third_house", "sahaja_bhava"],
     "Siblings, courage, communication, short travel, hands"),
    (4, "Fourth House", "Chaturdha Bhava", ["4h", "fourth_house", "sukha_bhava"],
     "Home, mother, vehicles, property, emotions"),
    (5, "Fifth House", "Panchamsha Bhava", ["5h", "fifth_house", "putra_bhava"],
     "Children, creativity, speculation, romance, intellect"),
    (6, "Sixth House", "Shashtha Bhava", ["6h", "sixth_house", "ripu_bhava"],
     "Health, enemies, debts, daily routine, service"),
    (7, "Seventh House", "Saptama Bhava", ["7h", "seventh_house", "kalatra_bhava"],
     "Marriage, partnerships, business, public dealings"),
    (8, "Eighth House", "Ashtama Bhava", ["8h", "eighth_house", "ayur_bhava"],
     "Longevity, transformation, occult, inheritance, sudden events"),
    (9, "Ninth House", "Navama Bhava", ["9h", "ninth_house", "dharma_bhava"],
     "Dharma, higher learning, father, long travel, spirituality"),
    (10, "Tenth House", "Dashama Bhava", ["10h", "tenth_house", "karma_bhava"],
     "Career, profession, status, government, public life"),
    (11, "Eleventh House", "Ekadasha Bhava", ["11h", "eleventh_house", "labha_bhava"],
     "Gains, friends, elder siblings, fulfillment of desires"),
    (12, "Twelfth House", "Dvadasha Bhava", ["12h", "twelfth_house", "vyaya_bhava"],
     "Losses, foreign lands, liberation, isolation, spirituality"),
]

for house_num, name_en, name_sa, synonyms, desc in HOUSE_DATA:
    ENTITIES.append(_e(
        "house", f"house_{house_num:02d}",
        name_en, name_sa, synonyms, desc,
    ))

# ── Dasha systems ──────────────────────────────────────────────────────────────

ENTITIES += [
    _e("dasha_system", "vimshottari", "Vimshottari Dasha", "Vimshottari",
       ["vimshottari", "vimsottari", "120_year_dasha", "nakshatra_dasha"],
       "120-year Moon-nakshatra-based dasha system; primary Parashari system"),
    _e("dasha_system", "yogini", "Yogini Dasha", "Yogini",
       ["yogini", "yogini_dasha"],
       "36-year dasha system; eight yoginis"),
    _e("dasha_system", "jaimini_chara", "Jaimini Chara Dasha", "Chara",
       ["chara", "jaimini_chara", "char_dasha"],
       "Sign-based Jaimini dasha system"),
    _e("dasha_system", "kalachakra", "Kalachakra Dasha", "Kalachakra",
       ["kalachakra", "kala_chakra"],
       "Nakshatra-pada-based dasha system"),
    _e("dasha_system", "ashtottari", "Ashtottari Dasha", "Ashtottari",
       ["ashtottari", "108_year_dasha"],
       "108-year Rahu-excluded dasha (used when Rahu not in specific conditions)"),
]

# ── Life domains ───────────────────────────────────────────────────────────────

DOMAIN_DATA = [
    ("career", "Career", "Karma / Vritti",
     ["career", "profession", "work", "job", "occupation", "business"],
     "Professional life, career, livelihood"),
    ("marriage", "Marriage", "Vivaha",
     ["marriage", "spouse", "partner", "relationship", "vivaha"],
     "Marriage, partnership, spouse quality"),
    ("health", "Health", "Arogya",
     ["health", "disease", "illness", "arogya", "medical"],
     "Physical health, disease, vitality"),
    ("wealth", "Wealth", "Dhana",
     ["wealth", "money", "finance", "dhana", "financial", "income"],
     "Financial prosperity, wealth accumulation"),
    ("children", "Children", "Santana",
     ["children", "progeny", "child", "santana", "offspring"],
     "Children, progeny, creativity"),
    ("spirituality", "Spirituality", "Dharma / Moksha",
     ["spirituality", "moksha", "dharma", "liberation", "spiritual"],
     "Spiritual development, dharma, liberation"),
    ("education", "Education", "Vidya",
     ["education", "learning", "study", "vidya", "academic"],
     "Education, knowledge, learning"),
    ("property", "Property", "Bhumi / Griha",
     ["property", "real_estate", "land", "home", "house", "bhumi"],
     "Property, real estate, home"),
    ("travel", "Travel", "Yatra",
     ["travel", "journey", "yatra", "foreign", "abroad"],
     "Travel, journeys, foreign lands"),
    ("siblings", "Siblings", "Sahaja",
     ["siblings", "brother", "sister", "sahaja"],
     "Siblings, courage, communication"),
    ("parents", "Parents", "Matru / Pitru",
     ["parents", "father", "mother", "matru", "pitru"],
     "Parents, ancestors, family heritage"),
    ("enemies", "Enemies / Obstacles", "Ripu / Shatru",
     ["enemies", "obstacles", "debts", "ripu", "shatru"],
     "Enemies, competition, legal disputes, debts"),
    ("longevity", "Longevity", "Ayu",
     ["longevity", "lifespan", "ayu", "death", "transformation"],
     "Longevity, transformation, sudden events"),
    ("social", "Social Life", "Mitra / Labha",
     ["social", "friends", "network", "gains", "labha", "mitra"],
     "Social network, friends, gains, elder siblings"),
    ("losses", "Losses / Foreign", "Vyaya",
     ["losses", "foreign", "isolation", "vyaya", "expenditure"],
     "Losses, expenditure, foreign, isolation"),
]

for cid, name_en, name_sa, synonyms, desc in DOMAIN_DATA:
    ENTITIES.append(_e("domain", cid, name_en, name_sa, synonyms, desc))

# ── Key Jyotish concepts ───────────────────────────────────────────────────────

CONCEPT_DATA = [
    ("yoga", "Yoga", "Yoga",
     ["yoga", "planetary_combination", "raj_yoga", "dhana_yoga"],
     "Planetary combination/combination producing specific effects"),
    ("dosha", "Dosha", "Dosha",
     ["dosha", "defect", "mangal_dosha", "kaal_sarp"],
     "Planetary affliction or defect in the chart"),
    ("shadbala", "Shadbala", "Shadbala",
     ["shadbala", "planetary_strength", "six_fold_strength"],
     "Six-fold planetary strength system"),
    ("ashtakavarga", "Ashtakavarga", "Ashtakavarga",
     ["ashtakavarga", "bindus", "contribution_points"],
     "Eight-source contributory strength system"),
    ("sade_sati", "Sade Sati", "Sade Sati",
     ["sade_sati", "sadhe_sati", "saturn_transit_moon"],
     "Saturn transit over Moon sign ± 1 (7.5 year cycle)"),
    ("antardasha", "Antardasha", "Antardasha",
     ["antardasha", "bhukti", "sub_period"],
     "Sub-period within a major dasha"),
    ("mahadasha", "Mahadasha", "Mahadasha",
     ["mahadasha", "major_period", "main_dasha"],
     "Major planetary period"),
    ("pratyantar", "Pratyantar Dasha", "Pratyantar",
     ["pratyantar", "sub_sub_period", "pratyantardasha"],
     "Sub-sub period (3rd level dasha)"),
    ("transit", "Transit", "Gochar",
     ["transit", "gochar", "planetary_movement"],
     "Current planetary positions vs natal chart"),
    ("muhurta", "Muhurta", "Muhurta",
     ["muhurta", "electional", "auspicious_time"],
     "Auspicious timing / electional astrology"),
    ("bhava", "Bhava", "Bhava",
     ["bhava", "house_system", "bhava_chart"],
     "House / domain division of the zodiac"),
    ("graha", "Graha", "Graha",
     ["graha", "planet", "planetary"],
     "Planetary body in Jyotish"),
    ("lagna", "Lagna", "Lagna",
     ["lagna", "ascendant", "rising"],
     "Ascendant / rising sign / first house cusp"),
    ("rashi", "Rashi", "Rashi",
     ["rashi", "sign", "zodiac_sign"],
     "Zodiac sign in Jyotish"),
    ("nakshatra_concept", "Nakshatra", "Nakshatra",
     ["nakshatra", "lunar_mansion", "asterism"],
     "Lunar mansion; 27 divisions of the zodiac"),
    ("panchanga", "Panchanga", "Panchanga",
     ["panchanga", "panchaanga", "almanac", "five_limbs"],
     "Five limbs of the day: Tithi, Vara, Nakshatra, Yoga, Karana"),
    ("upaya", "Upaya", "Upaya",
     ["upaya", "remedy", "remedial", "jyotish_remedy"],
     "Astrological remedy / remedial measure"),
    ("drishti", "Drishti", "Drishti",
     ["drishti", "aspect", "graha_drishti", "planetary_aspect"],
     "Planetary aspect / line of sight"),
    ("karaka", "Karaka", "Karaka",
     ["karaka", "significator", "natural_karaka"],
     "Natural or temporal significator planet for a life area"),
    ("hora", "Hora", "Hora",
     ["hora", "planetary_hour"],
     "Planetary hour; 1/2 of a zodiac sign; time division"),
]

for cid, name_en, name_sa, synonyms, desc in CONCEPT_DATA:
    ENTITIES.append(_e("concept", cid, name_en, name_sa, synonyms, desc))


# ── Resolve function ───────────────────────────────────────────────────────────

def resolve(term: str) -> dict | None:
    """
    Resolve any synonym/alias to its canonical entity.
    Returns the entity dict or None.
    Case-insensitive.
    """
    t = term.lower().replace(" ", "_").replace("-", "_")
    for entity in ENTITIES:
        if entity["canonical_id"] == t:
            return entity
        if entity["canonical_name_en"].lower().replace(" ", "_") == t:
            return entity
        if entity.get("canonical_name_sa", "").lower().replace(" ", "_") == t:
            return entity
        if t in [s.lower() for s in entity["synonyms"]]:
            return entity
    return None


# ── Writer ─────────────────────────────────────────────────────────────────────

def seed_ontology(conn, build_id: str | None = None, dry_run: bool = False,
                  autocommit: bool = True) -> dict:
    """
    Seed brahma_ontology with all entities.
    Returns {total: int, inserted: int, skipped: int, by_class: dict}.

    autocommit=True  — legacy behaviour; function commits before returning.
    autocommit=False — caller owns the transaction; function does NOT commit.
                       Use this when the caller (e.g. a writer) manages the boundary.
    """
    if dry_run:
        by_class: dict[str, int] = {}
        for e in ENTITIES:
            by_class[e["entity_class"]] = by_class.get(e["entity_class"], 0) + 1
        return {"total": len(ENTITIES), "inserted": len(ENTITIES), "skipped": 0,
                "by_class": by_class}

    now = datetime.now(timezone.utc)
    inserted = 0
    skipped = 0

    with conn.cursor() as cur:
        for e in ENTITIES:
            cur.execute("""
                INSERT INTO brahma_ontology
                  (entity_class, canonical_id, canonical_name_en, canonical_name_sa,
                   synonyms, description, source_citation, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (entity_class, canonical_id) DO NOTHING
            """, (
                e["entity_class"], e["canonical_id"],
                e["canonical_name_en"], e.get("canonical_name_sa"),
                e["synonyms"], e.get("description"),
                e["source_citation"], now,
            ))
            if cur.rowcount > 0:
                inserted += 1
            else:
                skipped += 1

    if autocommit:
        conn.commit()

    by_class: dict[str, int] = {}
    for e in ENTITIES:
        by_class[e["entity_class"]] = by_class.get(e["entity_class"], 0) + 1

    logger.info("[L0/ontology] brahma_ontology: %d inserted, %d skipped", inserted, skipped)
    return {"total": inserted + skipped, "inserted": inserted, "skipped": skipped,
            "by_class": by_class}


def check_volume(conn) -> dict:
    """Check actual vs floor for brahma_ontology."""
    floor = 100
    with conn.cursor() as cur:
        try:
            cur.execute("SELECT COUNT(*) FROM brahma_ontology")
            actual = cur.fetchone()[0]
        except Exception:
            actual = 0
    status = "green" if actual >= floor else ("amber" if actual > 0 else "empty")
    return {"brahma_ontology": {"actual": actual, "floor": floor, "status": status}}
