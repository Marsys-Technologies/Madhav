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


# ── Storage-format codes (ADHIṢṬHĀNA Lane A3, 2026-08-08) ──────────────────────
# The exact short codes L1 writers emit into chart_facts.fact_subject/fact_key
# (PLANET_TO_SUBJECT convention — ga_positions_writer.py, ga_vargas_writer.py
# BODY_TO_SUBJECT — plus the bare full-name forms; both confirmed live against
# chart_id=482012f1-710e-4a25-994a-93821f5871aa 2026-08-08). 'MC' is the
# BODY_TO_SUBJECT code for midheaven — evidenced in source (a floored body,
# not yet populated for this native's chart, hence not live-confirmed there).
BPHS_CITATION_STORAGE_CODE = (
    "PLANET_TO_SUBJECT (ga_positions_writer.py) / BODY_TO_SUBJECT (ga_vargas_writer.py) "
    "— L1 writer storage-format convention, live-confirmed against chart_facts.fact_subject "
    "for chart_id=482012f1-710e-4a25-994a-93821f5871aa 2026-08-08"
)

ENTITIES += [
    _e("planet", "sun", "Sun", "Surya",
       ["surya", "ravi", "aditya", "Sol", "Sūrya", "Arka", "arka", "bhaskar",
        "SUN"],
       "Soul, father, authority, vitality; natural malefic"),
    _e("planet", "moon", "Moon", "Chandra",
       ["chandra", "soma", "luna", "indu", "Chandra", "Moon", "chandrama",
        "MOON"],
       "Mind, mother, emotions, public; natural benefic"),
    _e("planet", "mars", "Mars", "Mangala",
       ["mangala", "kuja", "angaraka", "bhumi", "Mars", "Mangal",
        "MAR", "MARS"],
       "Courage, siblings, land, surgery; natural malefic"),
    _e("planet", "mercury", "Mercury", "Budha",
       ["budha", "buddha", "Mercury", "Budh",
        "MER", "MERCURY"],
       "Intellect, speech, trade, mathematics; natural benefic"),
    _e("planet", "jupiter", "Jupiter", "Guru",
       ["guru", "brihaspati", "brhaspati", "Jupiter", "Brahmanaspati", "devaguru",
        "JUP", "JUPITER"],
       "Wisdom, dharma, children, expansion; natural benefic"),
    _e("planet", "venus", "Venus", "Shukra",
       ["shukra", "sukra", "Venus", "Bhargava", "usana",
        "VEN", "VENUS"],
       "Beauty, marriage, luxury, arts; natural benefic"),
    _e("planet", "saturn", "Saturn", "Shani",
       ["shani", "sani", "Saturn", "shanaischar", "manda", "Shanaischara",
        "SAT", "SATURN"],
       "Karma, discipline, longevity, delays; natural malefic"),
    _e("planet", "rahu", "Rahu", "Rahu",
       ["rahu", "caput_draconis", "north_node", "dragon_head", "ascending_node",
        "RAH_MEAN", "RAHU"],
       "North lunar node; foreigners, technology, obsession; shadow planet"),
    _e("planet", "ketu", "Ketu", "Ketu",
       ["ketu", "cauda_draconis", "south_node", "dragon_tail", "descending_node",
        "KET_MEAN", "KETU"],
       "South lunar node; spirituality, moksha, past karma; shadow planet"),
    _e("planet", "ascendant", "Ascendant", "Lagna",
       ["lagna", "ascendant", "rising_sign", "udaya_lagna", "AC",
        "LAGNA"],
       "First house cusp; self, body, personality"),
    _e("planet", "midheaven", "Midheaven", "Madhya Lagna",
       ["mc", "midheaven", "madhya_lagna", "medium_coeli",
        "MC"],
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
    # ADHIṢṬHĀNA Lane A3: storage-format codes actually used in
    # chart_facts.fact_subject — both zero-padded ("HOUSE_07") and unpadded
    # ("HOUSE_7") forms are live writer output (ga_kp_significators.py uses
    # f"HOUSE_{h:02d}"; ga_strength_writer.py/ga_structural_writer.py use
    # f"HOUSE_{h}") — both confirmed present for chart_id=
    # 482012f1-710e-4a25-994a-93821f5871aa 2026-08-08. The short "H7" idiom
    # appears only embedded in compound varga-house fact_subjects
    # (e.g. "D9.H7", "D108_H1") on this chart, never standalone, but is
    # added defensively since it is a real code idiom in the writer source
    # (ga_vargas_writer.py f"H{house}").
    storage_codes = list(dict.fromkeys(
        [f"HOUSE_{house_num:02d}", f"HOUSE_{house_num}", f"H{house_num}"]
    ))
    all_synonyms = synonyms + [c for c in storage_codes if c not in synonyms]
    ENTITIES.append(_e(
        "house", f"house_{house_num:02d}",
        name_en, name_sa, all_synonyms, desc,
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


# ── Karakas (77) — canonical_ids MUST match reference_karakas.karaka_id ────────

KARAKA_DATA = [
    # 8 Chara Jaimini karakas
    ("atmakaraka", "Atmakaraka", "Ātmakāraka",
     ["atmakaraka", "AK", "soul_significator", "atmakarak"],
     "Highest-longitude planet; Jaimini soul significator"),
    ("amatyakaraka", "Amatyakaraka", "Amātyakāraka",
     ["amatyakaraka", "AMK", "minister_significator"],
     "2nd-highest-longitude planet; career/minister significator"),
    ("bhratrikaraka", "Bhratrikaraka", "Bhrātṛkāraka",
     ["bhratrikaraka", "BK", "sibling_significator"],
     "3rd-highest-longitude planet; sibling significator"),
    ("matrikaraka", "Matrikaraka", "Mātṛkāraka",
     ["matrikaraka", "MK", "mother_significator"],
     "4th-highest-longitude planet; mother significator"),
    ("putrakaraka", "Putrakaraka", "Putrakāraka",
     ["putrakaraka", "PK", "children_significator"],
     "5th-highest-longitude planet; children significator"),
    ("gnatikaraka", "Gnatikaraka", "Jñātikāraka",
     ["gnatikaraka", "GK", "kinsman_significator"],
     "6th-highest-longitude planet; kinsman/disease significator"),
    ("darakaraka", "Darakaraka", "Dārakāraka",
     ["darakaraka", "DK", "spouse_significator"],
     "7th-highest-longitude planet; spouse significator"),
    ("strikaraka", "Strikaraka", "Strīkāraka",
     ["strikaraka", "SK", "co_spouse_significator"],
     "8th-highest-longitude (8-karaka scheme); co-spouse significator"),
    # 7 Sthira planet karakas
    ("karaka_sun", "Sun as Karaka", "Sūrya Kāraka",
     ["karaka_sun", "sun_karaka"], "Sun as natural significator of soul, father, authority"),
    ("karaka_moon", "Moon as Karaka", "Chandra Kāraka",
     ["karaka_moon", "moon_karaka"], "Moon as natural significator of mind, mother, emotions"),
    ("karaka_mars", "Mars as Karaka", "Maṅgala Kāraka",
     ["karaka_mars", "mars_karaka"], "Mars as natural significator of courage, siblings, land"),
    ("karaka_mercury", "Mercury as Karaka", "Budha Kāraka",
     ["karaka_mercury", "mercury_karaka"], "Mercury as natural significator of intellect, speech, trade"),
    ("karaka_jupiter", "Jupiter as Karaka", "Guru Kāraka",
     ["karaka_jupiter", "jupiter_karaka"], "Jupiter as natural significator of dharma, wisdom, children"),
    ("karaka_venus", "Venus as Karaka", "Śukra Kāraka",
     ["karaka_venus", "venus_karaka"], "Venus as natural significator of marriage, beauty, arts"),
    ("karaka_saturn", "Saturn as Karaka", "Śani Kāraka",
     ["karaka_saturn", "saturn_karaka"], "Saturn as natural significator of karma, discipline, longevity"),
    # 62 Sthira house/topic karakas
    ("karaka_father", "Significator of Father", "Pitṛ Kāraka",
     ["karaka_father", "father_karaka"], "Significator for father (9H/10H; Sun)"),
    ("karaka_mother", "Significator of Mother", "Mātṛ Kāraka",
     ["karaka_mother", "mother_karaka"], "Significator for mother (4H; Moon)"),
    ("karaka_spouse", "Significator of Spouse", "Kalatra Kāraka",
     ["karaka_spouse", "spouse_karaka"], "Significator for spouse (7H; Venus)"),
    ("karaka_children", "Significator of Children", "Putra Kāraka",
     ["karaka_children", "children_karaka"], "Significator for children (5H; Jupiter)"),
    ("karaka_career", "Significator of Career", "Karma Kāraka",
     ["karaka_career", "career_karaka"], "Significator for career/profession (10H; Saturn)"),
    ("karaka_wealth", "Significator of Wealth", "Dhana Kāraka",
     ["karaka_wealth", "wealth_karaka"], "Significator for wealth (2H; Jupiter)"),
    ("karaka_longevity", "Significator of Longevity", "Āyuṣ Kāraka",
     ["karaka_longevity", "longevity_karaka"], "Significator for longevity (8H; Saturn)"),
    ("karaka_courage", "Significator of Courage", "Parākrama Kāraka",
     ["karaka_courage", "courage_karaka"], "Significator for courage/valor (3H; Mars)"),
    ("karaka_education", "Significator of Education", "Vidyā Kāraka",
     ["karaka_education"], "Significator for education (5H; Mercury/Jupiter)"),
    ("karaka_higher_learning", "Significator of Higher Learning", "Uccha-Vidyā Kāraka",
     ["karaka_higher_learning"], "Significator for higher learning (9H; Jupiter)"),
    ("karaka_intelligence", "Significator of Intelligence", "Buddhi Kāraka",
     ["karaka_intelligence"], "Significator for intellect/reasoning (Mercury)"),
    ("karaka_speech", "Significator of Speech", "Vāk Kāraka",
     ["karaka_speech"], "Significator for speech/communication (2H; Mercury/Jupiter)"),
    ("karaka_vehicles", "Significator of Vehicles", "Vāhana Kāraka",
     ["karaka_vehicles"], "Significator for vehicles/transport (4H; Venus)"),
    ("karaka_conveyance", "Significator of Conveyance", "Yāna Kāraka",
     ["karaka_conveyance"], "Significator for comforts/conveyance (Venus)"),
    ("karaka_happiness", "Significator of Happiness", "Sukha Kāraka",
     ["karaka_happiness"], "Significator for inner happiness/contentment (Moon)"),
    ("karaka_home", "Significator of Home", "Gṛha Kāraka",
     ["karaka_home"], "Significator for home/dwelling (4H; Moon)"),
    ("karaka_land", "Significator of Land", "Bhūmi Kāraka",
     ["karaka_land"], "Significator for land (Mars)"),
    ("karaka_property", "Significator of Property", "Sthāvara Kāraka",
     ["karaka_property"], "Significator for immovable property (Mars)"),
    ("karaka_agriculture", "Significator of Agriculture", "Kṛṣi Kāraka",
     ["karaka_agriculture"], "Significator for agriculture/farming (Mars)"),
    ("karaka_enemies", "Significator of Enemies", "Śatru Kāraka",
     ["karaka_enemies"], "Significator for enemies/opposition (6H; Mars/Saturn)"),
    ("karaka_disease", "Significator of Disease", "Roga Kāraka",
     ["karaka_disease"], "Significator for disease/illness (6H/8H; Mars/Saturn)"),
    ("karaka_debts", "Significator of Debts", "Ṛṇa Kāraka",
     ["karaka_debts"], "Significator for debts/obligations (6H; Mars)"),
    ("karaka_maternal_uncle", "Significator of Maternal Uncle", "Mātula Kāraka",
     ["karaka_maternal_uncle"], "Significator for maternal uncle (3H/6H; Mars)"),
    ("karaka_litigation", "Significator of Litigation", "Vivāda Kāraka",
     ["karaka_litigation"], "Significator for litigation/legal disputes (Mars/Saturn)"),
    ("karaka_gains", "Significator of Gains", "Lābha Kāraka",
     ["karaka_gains"], "Significator for gains/profits (11H; Jupiter)"),
    ("karaka_losses", "Significator of Losses", "Vyaya Kāraka",
     ["karaka_losses"], "Significator for losses/expenditure (12H; Saturn)"),
    ("karaka_inheritance", "Significator of Inheritance", "Dāya Kāraka",
     ["karaka_inheritance"], "Significator for inheritance (Saturn)"),
    ("karaka_moksha", "Significator of Liberation", "Mokṣa Kāraka",
     ["karaka_moksha"], "Significator for liberation/moksha (12H; Ketu/Saturn)"),
    ("karaka_dharma", "Significator of Dharma", "Dharma Kāraka",
     ["karaka_dharma"], "Significator for righteousness/dharma (9H; Jupiter)"),
    ("karaka_fame", "Significator of Fame", "Kīrti Kāraka",
     ["karaka_fame"], "Significator for fame/recognition (Sun)"),
    ("karaka_status", "Significator of Status", "Pada Kāraka",
     ["karaka_status"], "Significator for social status/position (Sun)"),
    ("karaka_government", "Significator of Government", "Rāja Kāraka",
     ["karaka_government"], "Significator for government/authority (Sun)"),
    ("karaka_power", "Significator of Power", "Adhikāra Kāraka",
     ["karaka_power"], "Significator for power/authority (Sun/Mars/Saturn)"),
    ("karaka_food", "Significator of Food", "Anna Kāraka",
     ["karaka_food"], "Significator for food/sustenance (Jupiter)"),
    ("karaka_wisdom", "Significator of Wisdom", "Jñāna Kāraka",
     ["karaka_wisdom"], "Significator for wisdom/knowledge (Jupiter)"),
    ("karaka_grief", "Significator of Grief", "Duḥkha Kāraka",
     ["karaka_grief"], "Significator for sorrow/grief (Saturn)"),
    ("karaka_servants", "Significator of Servants", "Bhṛtya Kāraka",
     ["karaka_servants"], "Significator for servants/subordinates (Saturn)"),
    ("karaka_pleasure", "Significator of Pleasure", "Bhoga Kāraka",
     ["karaka_pleasure"], "Significator for sensory pleasure (Venus)"),
    ("karaka_marriage", "Significator of Marriage", "Vivāha Kāraka",
     ["karaka_marriage"], "Significator for marriage/union (7H; Venus)"),
    ("karaka_passion", "Significator of Passion", "Kāma Kāraka",
     ["karaka_passion"], "Significator for desire/passion (Venus)"),
    ("karaka_arts", "Significator of Arts", "Kalā Kāraka",
     ["karaka_arts"], "Significator for arts/creative expression (Venus)"),
    ("karaka_mind", "Significator of Mind", "Manas Kāraka",
     ["karaka_mind"], "Significator for mind/mental faculty (Moon)"),
    ("karaka_emotions", "Significator of Emotions", "Bhāva Kāraka",
     ["karaka_emotions"], "Significator for emotional nature (Moon)"),
    ("karaka_trade", "Significator of Trade", "Vāṇijya Kāraka",
     ["karaka_trade"], "Significator for trade/commerce (Mercury)"),
    ("karaka_relatives", "Significator of Relatives", "Bandhu Kāraka",
     ["karaka_relatives"], "Significator for relatives/extended kin (Mercury)"),
    ("karaka_friends", "Significator of Friends", "Mitra Kāraka",
     ["karaka_friends"], "Significator for friends/allies (11H; Mercury)"),
    ("karaka_elder_siblings", "Significator of Elder Siblings", "Agraja Kāraka",
     ["karaka_elder_siblings"], "Significator for elder siblings (Jupiter)"),
    ("karaka_younger_siblings", "Significator of Younger Siblings", "Anuja Kāraka",
     ["karaka_younger_siblings"], "Significator for younger siblings (Mars)"),
    ("karaka_foreign_travel", "Significator of Foreign Travel", "Videśa Kāraka",
     ["karaka_foreign_travel"], "Significator for foreign travel/residence (Rahu/Saturn)"),
    ("karaka_pilgrimage", "Significator of Pilgrimage", "Tīrtha Kāraka",
     ["karaka_pilgrimage"], "Significator for pilgrimage/sacred journeys (Jupiter)"),
    ("karaka_occult", "Significator of Occult", "Gupta Kāraka",
     ["karaka_occult"], "Significator for occult/hidden knowledge (Ketu/Saturn)"),
    ("karaka_research", "Significator of Research", "Anuṣandhāna Kāraka",
     ["karaka_research"], "Significator for research/investigation (Saturn/Ketu)"),
    ("karaka_spirituality", "Significator of Spirituality", "Adhyātma Kāraka",
     ["karaka_spirituality"], "Significator for spiritual development (Ketu/Jupiter)"),
    ("karaka_diseases_chronic", "Significator of Chronic Disease", "Cira-Roga Kāraka",
     ["karaka_diseases_chronic"], "Significator for chronic/long-term disease (Saturn)"),
    ("karaka_accidents", "Significator of Accidents", "Durghaṭanā Kāraka",
     ["karaka_accidents"], "Significator for accidents/sudden injury (Mars/Rahu)"),
    ("karaka_sudden_events", "Significator of Sudden Events", "Ākasmika Kāraka",
     ["karaka_sudden_events"], "Significator for unexpected events (Rahu/Ketu)"),
    ("karaka_wealth_accumulated", "Significator of Accumulated Wealth", "Saṃcita-Dhana Kāraka",
     ["karaka_wealth_accumulated"], "Significator for stored/accumulated wealth (Jupiter)"),
    ("karaka_speculation", "Significator of Speculation", "Satkā Kāraka",
     ["karaka_speculation"], "Significator for speculation/risk-taking (5H; Jupiter/Mercury)"),
    ("karaka_romance", "Significator of Romance", "Prema Kāraka",
     ["karaka_romance"], "Significator for romantic love (Venus)"),
    ("karaka_progeny", "Significator of Progeny", "Santāna Kāraka",
     ["karaka_progeny"], "Significator for progeny/offspring (5H; Jupiter)"),
    ("karaka_vitality", "Significator of Vitality", "Ojas Kāraka",
     ["karaka_vitality"], "Significator for life-force/vitality (Sun)"),
    ("karaka_discipline", "Significator of Discipline", "Saṃyama Kāraka",
     ["karaka_discipline"], "Significator for self-discipline/restraint (Saturn)"),
]

for cid, name_en, name_sa, synonyms, desc in KARAKA_DATA:
    ENTITIES.append(_e("karaka", cid, name_en, name_sa, synonyms, desc))

# ── Upagrahas (11) — canonical_ids MUST match reference_upagrahas.upagraha_id ─

ENTITIES += [
    _e("upagraha", "gulika", "Gulika", "Gulika",
       ["gulika", "gulika_mandi"], "Saturn's sub-planet; most potent malefic upagraha (BPHS Ch.5)"),
    _e("upagraha", "maandi", "Maandi", "Māndi",
       ["maandi", "mandi"], "Saturn's sub-planet; strong malefic (BPHS Ch.3)"),
    _e("upagraha", "dhuma", "Dhuma", "Dhūma",
       ["dhuma", "smoke_point"], "Sun-derived upagraha; smoky/obscuring influence"),
    _e("upagraha", "vyatipata", "Vyatipata", "Vyatīpāta",
       ["vyatipata"], "Sun-derived upagraha; calamitous/inauspicious influence"),
    _e("upagraha", "parivesha", "Parivesha", "Pariveśa",
       ["parivesha", "halo_point"], "Sun-derived upagraha; halo influence"),
    _e("upagraha", "indrachapa", "Indrachapa", "Indracāpa",
       ["indrachapa", "rainbow_point"], "Sun-derived upagraha; rainbow/bow influence"),
    _e("upagraha", "upaketu", "Upaketu", "Upaketu",
       ["upaketu", "comet_point"], "Sun-derived upagraha; comet-like malefic influence"),
    _e("upagraha", "kala", "Kala", "Kāla",
       ["kala", "kala_upagraha"], "Sun-derived upagraha; time/death influence"),
    _e("upagraha", "mrityu", "Mrityu", "Mṛtyu",
       ["mrityu", "death_point"], "Mars-derived upagraha; mortality influence"),
    _e("upagraha", "ardhaprahara", "Ardhaprahara", "Ardhaprahara",
       ["ardhaprahara"], "Mercury-derived upagraha; half-watch sub-planet"),
    _e("upagraha", "yamaghantaka", "Yamaghantaka", "Yamaghaṇṭaka",
       ["yamaghantaka", "yama_ghantaka"], "Jupiter-derived upagraha; Yama's bell"),
]

# ── Aspect types (13) ─────────────────────────────────────────────────────────

ENTITIES += [
    _e("aspect_type", "parashari_7th", "7th-house aspect", "Saptama Drishti",
       ["7th aspect", "opposition", "sapta drishti"],
       "Universal full aspect of every planet to the 7th from itself"),
    _e("aspect_type", "mars_4th", "Mars 4th aspect", "Mangala Chaturtha Drishti",
       ["mars 4th"], "Mars special full aspect to the 4th house from itself"),
    _e("aspect_type", "mars_8th", "Mars 8th aspect", "Mangala Ashtama Drishti",
       ["mars 8th"], "Mars special full aspect to the 8th house from itself"),
    _e("aspect_type", "jupiter_5th", "Jupiter 5th aspect", "Guru Panchama Drishti",
       ["jupiter 5th", "trine aspect"], "Jupiter special full aspect to the 5th"),
    _e("aspect_type", "jupiter_9th", "Jupiter 9th aspect", "Guru Navama Drishti",
       ["jupiter 9th"], "Jupiter special full aspect to the 9th"),
    _e("aspect_type", "saturn_3rd", "Saturn 3rd aspect", "Shani Tritiya Drishti",
       ["saturn 3rd"], "Saturn special full aspect to the 3rd"),
    _e("aspect_type", "saturn_10th", "Saturn 10th aspect", "Shani Dashama Drishti",
       ["saturn 10th"], "Saturn special full aspect to the 10th"),
    _e("aspect_type", "rahu_5th_9th", "Rahu/Ketu trinal aspect", "Rahu Trikona Drishti",
       ["rahu aspect", "ketu aspect"], "Node aspects to 5th/9th per later tradition"),
    _e("aspect_type", "jaimini_rashi_drishti", "Jaimini sign aspect", "Rāśi Drishti",
       ["rashi drishti", "sign aspect"],
       "Jaimini: movable↔fixed (non-adjacent), dual↔dual sign aspects"),
    _e("aspect_type", "graha_drishti", "Planetary aspect (general)", "Graha Drishti",
       ["graha drishti", "planet aspect"],
       "General planet-to-planet/house aspect by house-distance"),
    _e("aspect_type", "argala", "Intervention aspect", "Argalā",
       ["argala", "intervention"],
       "Jaimini: planetary intervention from 2/4/11 (and 5) houses"),
    _e("aspect_type", "virodhargala", "Counter-intervention", "Virodhārgalā",
       ["virodhargala", "counter argala"],
       "Jaimini: obstruction of argala from 12/10/3"),
    _e("aspect_type", "kp_sublord", "KP sub-lord aspect", "Sub-lord",
       ["kp sublord", "sub lord"],
       "Krishnamurti Paddhati significator via star/sub lord"),
]

# ── Remedy types (12) ─────────────────────────────────────────────────────────

ENTITIES += [
    _e("remedy_type", "mantra", "Mantra", "Mantra",
       ["mantra", "japa_mantra"], "Sound-based remedy (deity/planetary mantra)"),
    _e("remedy_type", "yantra", "Yantra", "Yantra",
       ["yantra", "geometric_diagram"], "Geometric diagram remedy"),
    _e("remedy_type", "gemstone", "Gemstone", "Ratna",
       ["gemstone", "ratna", "gem"], "Planetary gemstone remedy"),
    _e("remedy_type", "charity", "Charity", "Dāna",
       ["charity", "daan", "dana"], "Donation/charity remedy"),
    _e("remedy_type", "vrata", "Fasting/Vow", "Vrata",
       ["vrata", "fast", "upavasa"], "Fasting or religious vow remedy"),
    _e("remedy_type", "puja", "Worship", "Pūjā",
       ["puja", "pooja", "worship"], "Ritual worship remedy"),
    _e("remedy_type", "japa", "Repetition", "Japa",
       ["japa", "recitation"], "Mantra-repetition count remedy"),
    _e("remedy_type", "homa", "Fire-ritual", "Homa",
       ["homa", "havan", "yajna"], "Fire-offering ritual remedy"),
    _e("remedy_type", "tantric", "Tantric", "Tāntrika",
       ["tantric", "tantrik"], "Tantric remedy (source-vetted only)"),
    _e("remedy_type", "ayurvedic", "Ayurvedic", "Āyurvedika",
       ["ayurvedic", "herbal"], "Ayurvedic/herbal remedy"),
    _e("remedy_type", "vastu", "Vastu", "Vāstu",
       ["vastu", "vaastu"], "Directional/architectural remedy"),
    _e("remedy_type", "behavioral", "Behavioural", "Ācāra",
       ["behavioral", "conduct", "achara"], "Conduct/lifestyle remedy"),
]

# ── Schools (8) ───────────────────────────────────────────────────────────────

ENTITIES += [
    _e("school", "parashari", "Parashari", "Pārāśarī",
       ["parashari", "parasari", "bphs"], "The Parashara school; foundational system (BPHS)"),
    _e("school", "jaimini", "Jaimini", "Jaiminīya",
       ["jaimini", "jaimini sutram"], "The Jaimini system; rashi-based, chara karakas/dashas"),
    _e("school", "kp", "Krishnamurti Paddhati", "KP",
       ["kp", "krishnamurti", "stellar"], "Sub-lord stellar system (K.S. Krishnamurti)"),
    _e("school", "tajaka", "Tajaka", "Tājaka",
       ["tajaka", "tajik", "varshaphal"], "Tajaka/annual-chart (Persian-influenced) system"),
    _e("school", "lal_kitab", "Lal Kitab", "Lāl Kitāb",
       ["lal kitab", "lalkitab", "red book"], "Lal Kitab remedial system"),
    _e("school", "nadi", "Nadi", "Nāḍī",
       ["nadi", "naadi"], "Nadi (palm-leaf) predictive system"),
    _e("school", "ashtakavarga", "Ashtakavarga", "Aṣṭakavarga",
       ["ashtakavarga", "ashtaka varga"], "Ashtakavarga point-based transit/strength system"),
    _e("school", "phaladeepika", "Phaladeepika", "Phaladīpikā",
       ["phaladeepika", "phala deepika", "mantreswara"],
       "Mantreswara's Phaladeepika synthesis school"),
]

# ── Classical texts (15) ──────────────────────────────────────────────────────

ENTITIES += [
    _e("text", "bphs", "Brihat Parashara Hora Shastra", "Bṛhat Parāśara Horā Śāstra",
       ["bphs", "brihat parasara", "parashara hora"], "Foundational Parashari text"),
    _e("text", "phaladeepika", "Phaladeepika", "Phaladīpikā",
       ["phaladeepika"], "Mantreswara's predictive synthesis"),
    _e("text", "jataka_parijata", "Jataka Parijata", "Jātaka Pārijāta",
       ["jataka parijata", "parijata"], "Vaidyanatha Dikshita's comprehensive natal text"),
    _e("text", "uttara_kalamrita", "Uttara Kalamrita", "Uttara Kālāmṛta",
       ["uttara kalamrita", "kalamrita"], "Kalidasa's compact reference"),
    _e("text", "jaimini_sutram", "Jaimini Sutram", "Jaimini Sūtram",
       ["jaimini sutram", "jaimini sutras"], "The Jaimini aphorisms"),
    _e("text", "brihat_jataka", "Brihat Jataka", "Bṛhat Jātaka",
       ["brihat jataka", "varahamihira jataka"], "Varahamihira's natal classic"),
    _e("text", "saravali", "Saravali", "Sārāvalī",
       ["saravali", "kalyana varma"], "Kalyana Varma's extensive yoga catalog"),
    _e("text", "hora_sara", "Hora Sara", "Horā Sāra",
       ["hora sara", "prithuyasas"], "Prithuyasas's predictive text"),
    _e("text", "sarvartha_chintamani", "Sarvartha Chintamani", "Sarvārtha Cintāmaṇi",
       ["sarvartha chintamani", "chintamani"], "Venkatesha's predictive compendium"),
    _e("text", "brihat_samhita", "Brihat Samhita", "Bṛhat Saṃhitā",
       ["brihat samhita", "samhita"], "Varahamihira's mundane/omens encyclopedia"),
    _e("text", "tajaka_neelakanthi", "Tajaka Neelakanthi", "Tājaka Nīlakaṇṭhī",
       ["tajaka neelakanthi", "neelakanthi"], "Neelakantha's annual-chart text"),
    _e("text", "yavana_jataka", "Yavana Jataka", "Yavana Jātaka",
       ["yavana jataka"], "Sphujidhvaja's Greek-influenced natal text"),
    _e("text", "bhrigu_samhita", "Bhrigu Samhita", "Bhṛgu Saṃhitā",
       ["bhrigu samhita", "bhrigu"], "Bhrigu's predictive compendium (extracts)"),
    _e("text", "muhurta_chintamani", "Muhurta Chintamani", "Muhūrta Cintāmaṇi",
       ["muhurta chintamani"], "Rama's electional-astrology text"),
    _e("text", "lal_kitab_text", "Lal Kitab", "Lāl Kitāb",
       ["lal kitab text"], "The Lal Kitab remedial corpus"),
]

# ── Domains — additional entries to reach ≥40 total ──────────────────────────

DOMAIN_EXTRA = [
    ("profession", "Profession", "Vritti",
     ["profession", "vocation", "livelihood"], "Vocation/livelihood as a life domain"),
    ("business", "Business", "Vyāpāra",
     ["business", "enterprise", "commerce"], "Business/entrepreneurial activity"),
    ("service", "Service", "Sevā",
     ["service", "employment", "job"], "Employment and service under others"),
    ("spouse", "Spouse", "Kalatra",
     ["spouse", "partner", "kalatra"], "Spouse and marital relationship quality"),
    ("progeny_domain", "Progeny", "Santāna",
     ["progeny", "offspring", "santana"], "Progeny and fertility life domain"),
    ("finance", "Finance", "Artha",
     ["finance", "money_management", "artha"], "Financial management and cash flow"),
    ("debt", "Debt", "Ṛṇa",
     ["debt", "loan", "rina"], "Debts, loans, and financial obligations"),
    ("vehicles_domain", "Vehicles", "Vāhana",
     ["vehicles", "transport"], "Vehicles, transport, and conveyances"),
    ("higher_learning", "Higher Learning", "Uccha Vidyā",
     ["higher_learning", "university", "uccha_vidya"], "Higher education and scholarly pursuits"),
    ("disease_domain", "Disease", "Roga",
     ["disease", "illness", "roga"], "Disease and health afflictions as a domain"),
    ("foreign_travel", "Foreign Travel", "Videśa Yātrā",
     ["foreign_travel", "abroad", "foreign_land"], "Foreign travel, residence, and immigration"),
    ("moksha_domain", "Liberation", "Mokṣa",
     ["moksha", "liberation", "spiritual_release"], "Spiritual liberation/moksha as a life domain"),
    ("fame", "Fame", "Kīrti",
     ["fame", "reputation", "kirti"], "Public reputation, fame, and recognition"),
    ("status", "Status", "Māna",
     ["status", "prestige", "social_standing"], "Social status and prestige"),
    ("father", "Father", "Pitā",
     ["father", "pita"], "Father and paternal lineage"),
    ("mother_domain", "Mother", "Mātā",
     ["mother", "maternal"], "Mother and maternal lineage"),
    ("friends_domain", "Friends", "Mitra",
     ["friends", "allies", "mitra"], "Friends, allies, and social network"),
    ("litigation", "Litigation", "Vivāda",
     ["litigation", "legal", "court", "vivada"], "Legal disputes, court cases, and litigation"),
    ("inheritance_domain", "Inheritance", "Dāya",
     ["inheritance", "legacy", "daya"], "Inherited wealth and legacy"),
    ("speculation_domain", "Speculation", "Satta",
     ["speculation", "gambling", "stock_market"], "Speculation, trading, and high-risk finance"),
    ("romance", "Romance", "Prema",
     ["romance", "love_affair", "prema"], "Romantic relationships before/outside marriage"),
    ("sexuality", "Sexuality", "Kāma",
     ["sexuality", "kama", "desire"], "Sexuality and kama as a life domain"),
    ("agriculture_domain", "Agriculture", "Kṛṣi",
     ["agriculture", "farming", "krishi"], "Agricultural pursuits and land cultivation"),
    ("government", "Government", "Rāja",
     ["government", "politics", "state", "raja"], "Government service and political life"),
    ("sports", "Sports", "Khela",
     ["sports", "athletics", "competition", "khela"], "Sports, athletics, and physical competition"),
    ("arts_domain", "Arts", "Kalā",
     ["arts", "creativity", "fine_arts", "kala"], "Arts, music, and creative expression"),
    ("writing", "Writing", "Lekhana",
     ["writing", "authorship", "lekhana"], "Writing, authorship, and literary pursuits"),
    ("research_domain", "Research", "Anusandhāna",
     ["research", "investigation", "anusandhana"], "Research, investigation, and scholarship"),
    ("occult_domain", "Occult", "Gupta Vidyā",
     ["occult", "esoteric", "gupta_vidya"], "Occult, esoteric, and hidden-knowledge pursuits"),
    ("politics", "Politics", "Rājnīti",
     ["politics", "policy", "rajniti"], "Political career and public policy"),
]

for cid, name_en, name_sa, synonyms, desc in DOMAIN_EXTRA:
    ENTITIES.append(_e("domain", cid, name_en, name_sa, synonyms, desc))

# ── Concepts — additional entries to reach ≥150 total ────────────────────────

CONCEPT_EXTRA = [
    # Divisional charts (D-charts)
    ("drekkana", "Drekkana", "Drekkāṇa", ["drekkana", "D3"], "D-3 chart; siblings, courage, innate nature"),
    ("chaturthamsa", "Chaturthamsa", "Caturthāṃśa", ["chaturthamsa", "D4"], "D-4 chart; property, home, fixed assets"),
    ("saptamsa", "Saptamsa", "Saptāṃśa", ["saptamsa", "D7"], "D-7 chart; progeny and children"),
    ("navamsa", "Navamsa", "Navāṃśa", ["navamsa", "D9", "navamsha"], "D-9 chart; dharma, spouse, inner nature; most important divisional"),
    ("dasamsa", "Dasamsa", "Daśāṃśa", ["dasamsa", "D10"], "D-10 chart; career and professional activity"),
    ("dwadasamsa", "Dwadasamsa", "Dvādaśāṃśa", ["dwadasamsa", "D12"], "D-12 chart; parents, ancestors"),
    ("shodasamsa", "Shodasamsa", "Ṣoḍaśāṃśa", ["shodasamsa", "D16"], "D-16 chart; vehicles and pleasures"),
    ("vimsamsa", "Vimsamsa", "Viṃśāṃśa", ["vimsamsa", "D20"], "D-20 chart; spiritual progress"),
    ("chaturvimsamsa", "Chaturvimsamsa", "Caturviṃśāṃśa", ["chaturvimsamsa", "D24"], "D-24 chart; education and learning"),
    ("nakshatramsa", "Nakshatramsa", "Nakṣatrāṃśa", ["nakshatramsa", "D27", "bhamsa"], "D-27 chart; strength and body"),
    ("trimsamsa", "Trimsamsa", "Triṃśāṃśa", ["trimsamsa", "D30"], "D-30 chart; evils and misfortunes"),
    ("khavedamsa", "Khavedamsa", "Khavedāṃśa", ["khavedamsa", "D40"], "D-40 chart; auspicious/inauspicious tendencies"),
    ("akshavedamsa", "Akshavedamsa", "Akṣavedāṃśa", ["akshavedamsa", "D45"], "D-45 chart; paternal/maternal heritage"),
    ("shashtiamsa", "Shashtiamsa", "Ṣaṣṭyāṃśa", ["shashtiamsa", "D60"], "D-60 chart; past-life karma; most sensitive divisional"),
    # Planetary dignities
    ("exaltation", "Exaltation", "Uccha", ["exaltation", "uccha", "ucha"], "State of maximum planetary strength in its exaltation sign"),
    ("debilitation", "Debilitation", "Nīca", ["debilitation", "neecha", "neechu"], "State of minimum planetary strength in its debilitation sign"),
    ("moolatrikona", "Moolatrikona", "Mūlatrikoṇa", ["moolatrikona", "moola trikona"], "Intermediate dignity zone between own-sign and exaltation"),
    ("own_sign", "Own Sign", "Sva Rāśi", ["own_sign", "swa_rashi", "svakshetra"], "Planet in its own sign; strong and comfortable"),
    ("great_friend_sign", "Great Friend Sign", "Paramitra Rāśi", ["great_friend_sign", "paramitra"], "Planet in sign of a great friend"),
    ("friend_sign", "Friend Sign", "Mitra Rāśi", ["friend_sign", "mitra_rashi"], "Planet in sign of a friend"),
    ("neutral_sign", "Neutral Sign", "Sama Rāśi", ["neutral_sign", "sama_rashi"], "Planet in sign of a neutral planet"),
    ("enemy_sign", "Enemy Sign", "Shatru Rāśi", ["enemy_sign", "shatru_rashi"], "Planet in sign of an enemy"),
    ("great_enemy_sign", "Great Enemy Sign", "Parashatru Rāśi", ["great_enemy_sign", "parashatru"], "Planet in sign of a great enemy"),
    ("combustion", "Combustion", "Maudhya", ["combustion", "maudhya", "combust", "asta"], "Planet too close to Sun; weakened/hidden"),
    ("retrogradation", "Retrogradation", "Vakra", ["retrogradation", "vakra", "retrograde"], "Apparent backward motion; intensified/internalized energy"),
    ("vargottama", "Vargottama", "Vargottama", ["vargottama"], "Planet in same sign in both rashi and navamsa; strengthened"),
    ("neecha_bhanga", "Neecha Bhanga", "Nīca Bhaṅga", ["neecha_bhanga", "cancellation_of_debility"], "Cancellation of debilitation; can give raja yoga effects"),
    ("planetary_war", "Planetary War", "Graha Yuddha", ["planetary_war", "graha_yuddha"], "Two planets within 1 degree; one wins, one loses strength"),
    # House classifications
    ("kendra", "Kendra", "Kendra", ["kendra", "angular"], "Angular houses (1,4,7,10); powerful positions"),
    ("trikona", "Trikona", "Trikoṇa", ["trikona", "trine"], "Trine houses (1,5,9); dharma houses; auspicious"),
    ("panapara", "Panapara", "Paṇaphara", ["panapara", "succedent"], "Succedent houses (2,5,8,11); moderate strength"),
    ("apoklima", "Apoklima", "Āpoklima", ["apoklima", "cadent"], "Cadent houses (3,6,9,12); weaker position"),
    ("dusthana", "Dusthana", "Duḥsthāna", ["dusthana", "evil_houses"], "Evil houses (6,8,12); difficulties and challenges"),
    ("upachaya", "Upachaya", "Upacaya", ["upachaya"], "Houses of growth (3,6,10,11); improve with time"),
    ("maraka", "Maraka", "Māraka", ["maraka", "death_inflicting"], "Death-inflicting houses (2,7) and their lords"),
    ("trika", "Trika", "Trika", ["trika"], "The trika houses (6,8,12); dusthana trio"),
    ("trishadaya", "Trishadaya", "Triṣaḍāya", ["trishadaya", "trishadya"], "The 3-6-11 houses; enemy/upachaya group"),
    # Aspect/relationship concepts
    ("graha_yuddha", "Graha Yuddha", "Graha Yuddha", ["graha_yuddha", "planetary_war_concept"], "Planetary war between two close planets"),
    ("parivartana", "Parivartana", "Parivartana", ["parivartana", "mutual_exchange"], "Mutual sign exchange (lord of A in B, lord of B in A)"),
    ("yuti", "Yuti", "Yuti", ["yuti", "conjunction", "graha_mela"], "Planetary conjunction; planets in the same sign/house"),
    ("kartari", "Kartari", "Kartarī", ["kartari", "scissors_yoga"], "Planetary scissors; planet hemmed between two others"),
    # Strength systems
    ("bindu", "Bindu", "Bindu", ["bindu", "benefic_point"], "Benefic point in ashtakavarga; score ≥28 is strong"),
    ("rekha", "Rekha", "Rekhā", ["rekha", "malefic_point"], "Malefic mark in ashtakavarga; opposite of bindu"),
    ("kakshya", "Kakshya", "Kakṣyā", ["kakshya", "octant"], "1/8 division of a sign; transit sub-division in ashtakavarga"),
    ("vimsopaka", "Vimsopaka", "Viṃśopaka", ["vimsopaka", "twenty_point_strength"], "20-point strength combining multiple divisional charts"),
    ("ishtaphala", "Ishtaphala", "Iṣṭaphala", ["ishtaphala", "desired_result"], "Benefic result score from shadbala"),
    ("kashtaphala", "Kashtaphala", "Kaṣṭaphala", ["kashtaphala", "difficulty_result"], "Malefic result score from shadbala"),
    ("dig_bala", "Dig Bala", "Dig Bala", ["dig_bala", "directional_strength"], "Directional strength of a planet in a specific angular house"),
    # Lunar/solar calendar
    ("tithi", "Tithi", "Tithi", ["tithi", "lunar_day"], "Lunar day; one of 30 tithis in a month"),
    ("paksha", "Paksha", "Pakṣa", ["paksha", "fortnight"], "Lunar fortnight; shukla (waxing) or krishna (waning)"),
    ("vara", "Vara", "Vāra", ["vara", "weekday"], "Day of the week; each ruled by a planet"),
    ("yoga_panchanga", "Yoga (Panchanga)", "Yoga", ["yoga_panchanga", "panchanga_yoga"], "27 luni-solar combinations in the panchanga"),
    ("karana", "Karana", "Karaṇa", ["karana"], "Half-tithi; 11 karanas (7 movable + 4 fixed)"),
    ("pada", "Pada", "Pāda", ["pada", "nakshatra_pada"], "Quarter of a nakshatra (9° each); 108 padas total"),
    ("gandanta", "Gandanta", "Gaṇḍānta", ["gandanta", "gandant"], "Junction between water and fire signs; sensitive degrees"),
    ("abhijit", "Abhijit", "Abhijit", ["abhijit", "the_victorious_nakshatra"], "The 28th nakshatra; arc near Vega; auspicious muhurta"),
    # Arudha/Jaimini concepts
    ("arudha_lagna", "Arudha Lagna", "Ārūḍha Lagna", ["arudha_lagna", "AL", "image_ascendant"], "The perceived self/image; Jaimini arudha of the 1st house"),
    ("upapada", "Upapada Lagna", "Upapada Lagna", ["upapada", "UL"], "Arudha of 12th house; spouse quality indicator"),
    ("karakamsa", "Karakamsa", "Kārakāṃśa", ["karakamsa"], "Navamsa sign of the atmakaraka; inner nature indicator"),
    ("swamsa", "Swamsa", "Svāṃśa", ["swamsa", "svamsa"], "Atmakaraka's navamsa sign; soul's desires"),
    ("chara_dasha", "Chara Dasha", "Chara Daśā", ["chara_dasha", "jaimini_chara_dasha"], "Jaimini sign-based movable dasha system"),
    ("sthira_dasha", "Sthira Dasha", "Sthira Daśā", ["sthira_dasha"], "Jaimini fixed-sign dasha system"),
    # Timing and transit concepts
    ("pratyantardasha", "Pratyantardasha", "Pratyantardaśā", ["pratyantardasha", "sub_sub_period", "pratyantar"], "3rd-level sub-period within antardasha"),
    ("sookshma_dasha", "Sookshma Dasha", "Sūkṣma Daśā", ["sookshma_dasha", "4th_level_period"], "4th-level sub-period (minute sub-period)"),
    ("prana_dasha", "Prana Dasha", "Prāṇa Daśā", ["prana_dasha", "5th_level_period"], "5th-level dasha (the finest sub-period)"),
    ("gochara", "Gochara", "Gocara", ["gochara", "transit", "gochar"], "Current planetary transit over natal chart positions"),
    ("vedha", "Vedha", "Vedha", ["vedha", "piercing"], "Transit obstruction; counteracts another transit's effect"),
    ("dhaiya", "Dhaiya", "Ḍhaiyā", ["dhaiya", "dhayya", "saturn_2.5"], "Saturn transit over 4H or 8H from natal Moon (2.5 years)"),
    ("tarabala", "Tarabala", "Tārabala", ["tarabala", "star_strength"], "Natal nakshatra vs transit nakshatra strength assessment"),
    ("chandrabala", "Chandrabala", "Candrabala", ["chandrabala", "moon_strength"], "Moon's transit strength by house count from natal Moon"),
    # Result types / yogas
    ("raja_yoga", "Raja Yoga", "Rāja Yoga", ["raja_yoga", "royal_combination"], "Planetary combination producing status, power, success"),
    ("dhana_yoga", "Dhana Yoga", "Dhana Yoga", ["dhana_yoga", "wealth_yoga"], "Planetary combination producing wealth and prosperity"),
    ("viparita_raja_yoga", "Viparita Raja Yoga", "Viparīta Rāja Yoga",
     ["viparita_raja_yoga", "vipareeta_raja_yoga"], "Dusthana lords in dusthanas; reversal producing rise"),
    ("neecha_bhanga_raja_yoga", "Neecha Bhanga Raja Yoga", "Nīca Bhaṅga Rāja Yoga",
     ["neecha_bhanga_raja_yoga"], "Cancelled debilitation yoga giving rise after fall"),
    ("arishta", "Arishta", "Ariṣṭa", ["arishta", "evil_combination"], "Malefic planetary combination causing suffering"),
    ("balarishta", "Balarishta", "Balāriṣṭa", ["balarishta", "infant_danger"], "Danger to life in early childhood; childhood arishta"),
    # Additional structural concepts
    ("pushkara_navamsa", "Pushkara Navamsa", "Puṣkara Navāṃśa",
     ["pushkara_navamsa", "nourishing_navamsa"], "Benefic navamsa degrees; nourishing and strengthening"),
    ("mrityu_bhaga", "Mrityu Bhaga", "Mṛtyu Bhāga",
     ["mrityu_bhaga", "death_degree"], "Specific sensitive degree of each sign; mortality-related"),
    ("atichara", "Atichara", "Aticāra",
     ["atichara", "accelerated_motion"], "Faster-than-normal planetary motion"),
    ("vakri", "Vakri", "Vakrī",
     ["vakri", "retrograde_planet"], "Retrograde planet (same as retrogradation concept at the concrete level)"),
    ("narayana_dasha", "Narayana Dasha", "Nārāyaṇa Daśā",
     ["narayana_dasha"], "Jaimini sign-based dasha; progression through signs"),
    ("bhava_bala", "Bhava Bala", "Bhāva Bala",
     ["bhava_bala", "house_strength"], "Strength of a bhava (house); from shadbala calculations"),
    ("bhava_adhipati", "Bhava Adhipati", "Bhāva Adhipati",
     ["bhava_adhipati", "house_lord"], "Lord/ruler of a house (bhava)"),
    ("ayanamsha", "Ayanamsha", "Ayanāṃśa",
     ["ayanamsha", "ayanamsa", "precession_correction"], "Correction factor between tropical and sidereal zodiac"),
    ("tropical_zodiac", "Tropical Zodiac", "Sāyana",
     ["tropical", "sayana", "western_zodiac"], "Sun-earth relationship-based zodiac (equinox-anchored)"),
    ("sidereal_zodiac", "Sidereal Zodiac", "Nirāyana",
     ["sidereal", "nirayana", "star_based_zodiac"], "Fixed-star-based zodiac used in Jyotish"),
    ("bhava_chalit", "Bhava Chalit", "Bhāva Cālit",
     ["bhava_chalit", "chalit_chart"], "Equal-house chart showing actual house occupancy vs sign"),
    ("rahu_kalam", "Rahu Kalam", "Rāhu Kālam",
     ["rahu_kalam", "rahu_kaalam", "inauspicious_period"], "Inauspicious daily time period governed by Rahu"),
    ("gulika_kalam", "Gulika Kalam", "Gulika Kālam",
     ["gulika_kalam"], "Inauspicious daily time period associated with Saturn/Gulika"),
    ("varshaphal", "Varshaphal", "Varṣaphala",
     ["varshaphal", "annual_chart", "solar_return_jyotish"], "Annual horoscope / solar return chart in Tajaka system"),
    ("sudarshana_chakra", "Sudarshana Chakra", "Sudarśana Cakra",
     ["sudarshana_chakra"], "Three-chart synthesis: lagna, moon, sun concentric wheels"),
    ("shoola_dasha", "Shoola Dasha", "Śūla Daśā",
     ["shoola_dasha", "trident_dasha"], "Jaimini dasha for longevity and timing of death"),
    ("yogakaraka", "Yogakaraka", "Yogakāraka",
     ["yogakaraka", "yoga_planet"], "Planet ruling both a kendra and a trikona; powerful benefic"),
    ("badhaka", "Badhaka", "Bādhaka",
     ["badhaka", "obstacle_lord"], "Obstacle house/lord; sign-type-specific affliction point"),
    ("prashna", "Prashna", "Praśna",
     ["prashna", "horary_jyotish"], "Horary Jyotish; chart for the moment of a question"),
    ("jataka", "Jataka", "Jātaka",
     ["jataka", "natal_chart"], "Natal horoscopy; chart cast for time of birth"),
    ("mundane_astrology", "Mundane Astrology", "Mediniī Jyotiṣa",
     ["mundane", "mundane_astrology", "mediniya"], "Astrology of world events, nations, weather"),
    ("medical_astrology", "Medical Astrology", "Āyur Jyotiṣa",
     ["medical_astrology", "ayur_jyotish"], "Astrological analysis of health and disease"),
    ("electional_astrology", "Electional Astrology", "Muhūrta Jyotiṣa",
     ["electional_astrology", "muhurta_jyotish"], "Choosing auspicious times for actions"),
    ("naisargika_dasha", "Naisargika Dasha", "Naisargika Daśā",
     ["naisargika_dasha", "natural_dasha"], "Natural sequence dasha ordered by planet speed"),
    ("bhavat_bhavam", "Bhavat Bhavam", "Bhāvat Bhāvam",
     ["bhavat_bhavam"], "The house from the house; amplified signification technique"),
    ("lagna_bala", "Lagna Bala", "Lagna Bala",
     ["lagna_bala"], "Strength of the ascendant sign/lord in the chart"),
    ("pinda", "Pinda", "Piṇḍa",
     ["pinda", "longevity_calculation_sum"], "Sum of planetary years in longevity calculations"),
    ("hora_bala", "Hora Bala", "Horā Bala",
     ["hora_bala"], "Strength derived from the planetary hora ruling the birth hour"),
    ("chesta_bala", "Chesta Bala", "Ceṣṭā Bala",
     ["chesta_bala", "motional_strength"], "Motional strength of a planet (one of the six shadbala components)"),
    ("naisargika_bala", "Naisargika Bala", "Naisargika Bala",
     ["naisargika_bala", "natural_strength"], "Natural strength of each planet by rank (Sun highest)"),
    ("kaala_bala", "Kaala Bala", "Kāla Bala",
     ["kaala_bala", "temporal_strength"], "Temporal strength of a planet by time of birth"),
    ("sthana_bala", "Sthana Bala", "Sthāna Bala",
     ["sthana_bala", "positional_strength"], "Positional strength from sign placement, exaltation, etc."),
    ("uccha_bala", "Uccha Bala", "Ucca Bala",
     ["uccha_bala", "exaltation_strength"], "Strength from proximity to exaltation degree"),
    ("varsha_kundali", "Varsha Kundali", "Varṣa Kuṇḍalī",
     ["varsha_kundali", "annual_kundali"], "Annual chart erected for solar return in Parashari tradition"),
    ("sarvatobhadra_chakra", "Sarvatobhadra Chakra", "Sārvatobhadra Cakra",
     ["sarvatobhadra_chakra", "all_auspicious_wheel"], "Nakshatra grid used for transit analysis and muhurta"),
    ("kota_chakra", "Kota Chakra", "Koṭa Cakra",
     ["kota_chakra", "fort_wheel"], "Fort wheel for mundane and personal protection analysis"),
    ("vipat_nakshatra", "Vipat Nakshatra", "Vipat Nakṣatra",
     ["vipat_nakshatra", "danger_star"], "3rd nakshatra from janma nakshatra; danger influence"),
    ("kshema_nakshatra", "Kshema Nakshatra", "Kṣema Nakṣatra",
     ["kshema_nakshatra", "welfare_star"], "4th nakshatra from janma nakshatra; welfare influence"),
    ("janma_nakshatra", "Janma Nakshatra", "Janma Nakṣatra",
     ["janma_nakshatra", "birth_star"], "Moon's nakshatra at birth; primary natal star"),
    ("sadhaka_nakshatra", "Sadhaka Nakshatra", "Sādhaka Nakṣatra",
     ["sadhaka_nakshatra", "accomplishment_star"], "5th from janma nakshatra; achievement and accomplishment"),
]

for cid, name_en, name_sa, synonyms, desc in CONCEPT_EXTRA:
    ENTITIES.append(_e("concept", cid, name_en, name_sa, synonyms, desc))

# ── Vargas (divisional charts, 30) — ADHIṢṬHĀNA Lane A3, 2026-08-08 ───────────
# Reconciliation: l0_reference.py's VARGAS (19: D1,D2,D3,D4,D5,D6,D7,D8,D9,D10,
# D12,D16,D20,D24,D27,D30,D40,D45,D60) is a STRICT SUBSET of the L1 writer's
# 30-varga computational set (ga_vargas_writer.py ALL_30_VARGAS = PARASHARI_16
# + SUPPLEMENTARY_11 + NADI_3; A6_VARGAS_SPEC_v1_0.md §1) — 19/19 overlap, 0
# conflicts, delta = 11 new (D11,D14,D15,D21,D32,D33,D50,D54,D108,D150,D2700).
# Canonical set seeded here = the full 30 (the writer's set, since it strictly
# contains l0_reference's 19).
#
# KNOWN COLLISION (documented, not fixed here — additive-only constraint for
# this lane): 14 of these 30 codes (D3,D4,D7,D9,D10,D12,D16,D20,D24,D27,D30,
# D40,D45,D60) already appear as a bare 'D<n>' synonym on a PRE-EXISTING
# entity_class='concept' row (e.g. canonical_id='navamsa' carries synonym
# 'D9', added under CONCEPT_EXTRA above, long before this lane). This lane
# cannot remove that legacy synonym (R19-style additive-only discipline);
# instead resolve_entity.ts's SQL now carries an explicit ORDER BY that
# prefers entity_class='varga' on a tie, so ref_entity_resolve('D9') resolves
# deterministically to THIS row, not the legacy concept one — see
# resolve_entity.ts. A genuine cleanup of the stale concept-level D-codes
# belongs to Lane A5/A6 (Fact Identity Index / registry-parity gate), not
# this lane.
CITATION_VARGA_CORE = (
    "BPHS Ch.6 (Shodasha-varga-adhyaya) / Ch.7 (Vimshati-varga extension); "
    "name + signification per brahmagyan/l0_reference.py VARGAS "
    "(reference_vargas seed, BPHS_SHODASHA citation)"
)
CITATION_VARGA_SUPPLEMENTARY = (
    "Not in l0_reference.py's 19-varga BPHS-cited set. Sanskrit ordinal-numeral "
    "+ \"aṃśa\" divisional-chart naming convention (same pattern as the 19 "
    "BPHS-cited vargas, e.g. D4=Chaturthamsha/D20=Vimshamsha), applied to the "
    "L1 writer's supplementary Parashari varga set (ga_vargas_writer.py "
    "SUPPLEMENTARY_11 / A6_VARGAS_SPEC_v1_0.md §1); signification per "
    "ga_vargas_writer.py VARGA_KARYA."
)
CITATION_VARGA_NADI = (
    "Not in l0_reference.py's 19-varga BPHS-cited set. \"Nadiamsa\" terminology "
    "and rishi/karma-type attribution per ga_vargas_writer.py inline "
    "documentation (D150_RISHIS/D2700_SUB_RISHIS) and A6_VARGAS_SPEC_v1_0.md "
    "§Q5/Q6 (K.N. Rao Nadi-jyotish tradition, 27-rishi cycle); D108/D2700 "
    "named by the same ordinal-numeral convention as the core set."
)


def _e_varga(n: int, name_en: str, name_sa: str, extra_synonyms: list[str],
             description: str, citation: str) -> dict:
    code = f"D{n}"
    synonyms = list(dict.fromkeys([code] + extra_synonyms))
    return {
        "entity_class": "varga",
        "canonical_id": f"d{n}",
        "canonical_name_en": name_en,
        "canonical_name_sa": name_sa,
        "synonyms": synonyms,
        "description": description,
        "source_citation": citation,
    }


# (n, name_en, name_sa, extra_synonyms, description, citation)
VARGA_DATA = [
    (1, "Rashi", "Rashi", ["rashi_chart", "d1_chart"],
     "Overall chart; physical body; all life matters (the birth/natal chart itself)",
     CITATION_VARGA_CORE),
    (2, "Hora", "Hora", ["hora_chart"],
     "Wealth; finances; material possessions", CITATION_VARGA_CORE),
    (3, "Drekkana", "Drekkana", ["drekkana_chart"],
     "Siblings; courage; communication (3 formula variants: Parashari/Jagannatha/Somanatha)",
     CITATION_VARGA_CORE),
    (4, "Chaturthamsha", "Chaturthamsha", ["chaturthamsa"],
     "Property; fixed assets; home; fortune", CITATION_VARGA_CORE),
    (5, "Panchamsha", "Panchamsha", ["panchamsa"],
     "Spiritual merit; past-life credit; children", CITATION_VARGA_CORE),
    (6, "Shashthamsha", "Shashthamsha", ["shashthamsa"],
     "Health; enemies; debts; service", CITATION_VARGA_CORE),
    (7, "Saptamsha", "Saptamsha", ["saptamsa"],
     "Children; progeny; creativity", CITATION_VARGA_CORE),
    (8, "Ashtamsha", "Ashtamsha", ["ashtamsa"],
     "Longevity; obstacles; sudden events; inheritance", CITATION_VARGA_CORE),
    (9, "Navamsha", "Navamsha", ["navamsha_chart"],
     "Marriage; dharma; spiritual development; inner nature — most important divisional",
     CITATION_VARGA_CORE),
    (10, "Dashamsha", "Dashamsha", ["dasamsa"],
     "Career; professional achievement; public life", CITATION_VARGA_CORE),
    (11, "Rudramsha", "Rudramsha", ["ekadashamsha", "ekadasamsa"],
     "Gains; elder siblings; fulfillment of desires (11H significations)",
     CITATION_VARGA_SUPPLEMENTARY),
    (12, "Dvadashamsha", "Dvadashamsha", ["dwadasamsa"],
     "Parents; ancestors; karmic inheritance", CITATION_VARGA_CORE),
    (14, "Chaturdashamsha", "Chaturdashamsha", [],
     "Father, paternal matters (secondary emphasis)", CITATION_VARGA_SUPPLEMENTARY),
    (15, "Panchadashamsha", "Panchadashamsha", [],
     "Children, progeny (tertiary emphasis)", CITATION_VARGA_SUPPLEMENTARY),
    (16, "Shodashamsha", "Shodashamsha", ["shodasamsa"],
     "Vehicles; conveyances; happiness", CITATION_VARGA_CORE),
    (20, "Vimshamsha", "Vimshamsha", ["vimsamsa"],
     "Spiritual practice; upasana; religious activities", CITATION_VARGA_CORE),
    (21, "Ekavimshamsha", "Ekavimshamsha", [],
     "Mother, maternal matters (secondary emphasis)", CITATION_VARGA_SUPPLEMENTARY),
    (24, "Chaturvimshamsha", "Chaturvimshamsha", ["chaturvimsamsa"],
     "Education; learning; academic achievements", CITATION_VARGA_CORE),
    (27, "Nakshatramsha", "Nakshatramsha", ["bhamsa", "saptavimshamsha"],
     "Strength; stamina; vitality", CITATION_VARGA_CORE),
    (30, "Trimshamsha", "Trimshamsha", ["trimsamsa"],
     "Miseries; evils; health issues", CITATION_VARGA_CORE),
    (32, "Dvatrimshamsha", "Dvatrimshamsha", [],
     "Secondary navamsha-linked harmonics", CITATION_VARGA_SUPPLEMENTARY),
    (33, "Trayastrimshamsha", "Trayastrimshamsha", [],
     "Secondary ashtamsha-linked harmonics (longevity/obstacles)", CITATION_VARGA_SUPPLEMENTARY),
    (40, "Khavedamsha", "Khavedamsha", ["khavedamsa"],
     "Maternal ancestry; auspicious effects", CITATION_VARGA_CORE),
    (45, "Akshavedamsha", "Akshavedamsha", ["akshavedamsa"],
     "Paternal ancestry; general indications", CITATION_VARGA_CORE),
    (50, "Panchashamsha", "Panchashamsha", [],
     "Higher/subtle significations (secondary emphasis)", CITATION_VARGA_SUPPLEMENTARY),
    (54, "Chatuhpanchashamsha", "Chatuhpanchashamsha", [],
     "Higher/subtle significations (tertiary emphasis)", CITATION_VARGA_SUPPLEMENTARY),
    (60, "Shastiamsha", "Shastiamsha", ["shashtiamsa", "shashtyamsha"],
     "Past-life karma; most subtle influences", CITATION_VARGA_CORE),
    (108, "Ashtottaramsha", "Ashtottaramsha", ["ashtottaramsa"],
     "Karma-type attribution; finest Nadi-tradition subdivision", CITATION_VARGA_NADI),
    (150, "Nadiamsha", "Nadiamsha", ["nadiamsa"],
     "Nadi rishi attribution; 27-rishi cycle; finest Nadi-tradition subdivision",
     CITATION_VARGA_NADI),
    (2700, "Sukshma Nadiamsha", "Sukshma-Nadiamsha", ["sub_nadiamsa", "atinadiamsa"],
     "Sub-Nadi (sub-rishi) attribution; finest Nadi-tradition sub-subdivision",
     CITATION_VARGA_NADI),
]

for n, name_en, name_sa, extra_synonyms, description, citation in VARGA_DATA:
    ENTITIES.append(_e_varga(n, name_en, name_sa, extra_synonyms, description, citation))

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
