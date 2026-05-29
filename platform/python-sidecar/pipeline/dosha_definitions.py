"""
dosha_definitions.py — G13 Dosha Definitions Library
=====================================================
Comprehensive classical Jyotish dosha catalogue covering all major dosha
categories: Mangal, Kala Sarpa (dosha form), Pitru, Matri, Naga, Sarpa,
Guru Chandal, Grahan, Daridra, Shakata, Vish, Punarphoo, Angarak,
Kemadrum, Shrapit, ancestral debt variants, planetary war, gandanta,
and papa kartari.

Classical sources:
  - Brihat Parashara Hora Shastra (BPHS), dosha and marriage chapters
  - Parashari tradition, standard commentaries
  - Classical muhurta texts (Muhurta Chintamani, Muhurta Martanda)

canonical_id: G13
stream: A
session: G13-S1 [BUILD-ORCH-A-24]
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# DOSHA_DEFINITIONS
# ---------------------------------------------------------------------------
# Each entry: {
#   "name":                 str   — display name
#   "category":             str   — mangal | kala_sarpa | pitru | matri |
#                                   graha_dosha | dasha_dosha | yoga_dosha |
#                                   miscellaneous
#   "constituent_predicate": str  — plain English formation rule
#   "severity":             str   — mild | moderate | severe | very_severe
#   "cancellation_rules":   list[str] — conditions that cancel/mitigate this dosha
#   "classical_citation":   str   — BPHS chapter/verse or classical text reference
#   "affected_domains":     list[str] — domains affected
#   "remedy_approach":      str   — brief remedy approach
# }

DOSHA_DEFINITIONS: dict[str, dict] = {

    # -----------------------------------------------------------------------
    # MANGAL DOSHA — Mars in 6 classical dosha-producing house positions
    # -----------------------------------------------------------------------

    "mangal_dosha_1h": {
        "name": "Mangal Dosha — 1st House",
        "category": "mangal",
        "constituent_predicate": "Mars is placed in the 1st house (ascendant) of the natal chart",
        "severity": "moderate",
        "cancellation_rules": [
            "Mars occupies Aries or Scorpio (own signs) in the 1st house for the relevant Ascendant",
            "Mars occupies Capricorn (exaltation) in the 1st house",
            "For Aries or Scorpio Ascendant, Mars in 1H is in own house — no dosha",
            "Jupiter aspects Mars or the 1st house strongly",
            "Venus is conjunct Mars in the 1st house",
            "Partner also has Mangal Dosha (mutual cancellation)",
            "Mars is in Jupiter's sign (Sagittarius or Pisces)",
        ],
        "classical_citation": "BPHS Ch. 73 (Vivaha chapter); Phaladeepika Ch. 14 v.1-6; Muhurta Chintamani",
        "affected_domains": ["marriage", "health", "temperament", "longevity_of_spouse"],
        "remedy_approach": "Kumbh Vivah (symbolic marriage to a pot or tree), Mangal puja, wearing red coral after expert consultation, fasting on Tuesdays",
    },

    "mangal_dosha_2h": {
        "name": "Mangal Dosha — 2nd House",
        "category": "mangal",
        "constituent_predicate": "Mars is placed in the 2nd house of the natal chart",
        "severity": "moderate",
        "cancellation_rules": [
            "Mars in 2H occupies Gemini or Virgo (Mercury's signs — Mars is enemy of Mercury; traditional exception)",
            "Mars in 2H is in own sign (Aries or Scorpio) or exaltation (Capricorn)",
            "Jupiter aspects the 2nd house strongly",
            "Partner also has Mangal Dosha in 2H or another classical dosha house",
            "Venus is in the 2nd house with Mars",
            "A natural benefic (Jupiter, Venus, well-placed Mercury) is in the 7th house",
        ],
        "classical_citation": "BPHS Ch. 73; Phaladeepika Ch. 14; Parashari tradition — 2H counted by many commentators",
        "affected_domains": ["marriage", "family", "speech", "wealth", "kutumba"],
        "remedy_approach": "Mangal puja, recitation of Mangal stotra, red coral, Kumbh Vivah if very afflicted, charity on Tuesdays",
    },

    "mangal_dosha_4h": {
        "name": "Mangal Dosha — 4th House",
        "category": "mangal",
        "constituent_predicate": "Mars is placed in the 4th house of the natal chart",
        "severity": "moderate",
        "cancellation_rules": [
            "Mars in 4H occupies Cancer (where Moon rules — opposing energy mitigates through domicile tension)",
            "Mars in own sign (Scorpio for 4H in Aries Ascendant) or exaltation",
            "Jupiter aspects the 4th house or Mars",
            "Venus is in the 4th house with Mars",
            "Partner also has Mangal Dosha",
            "Moon is strongly placed and unafflicted, counterbalancing Mars in 4H",
        ],
        "classical_citation": "BPHS Ch. 73; Vivaha yoga chapter; Muhurta Martanda on Mangal dosha",
        "affected_domains": ["marriage", "domestic_happiness", "property", "mother", "homeland"],
        "remedy_approach": "Mangal puja, land/property donation, recitation of Hanuman Chalisa, fasting on Tuesdays",
    },

    "mangal_dosha_7h": {
        "name": "Mangal Dosha — 7th House",
        "category": "mangal",
        "constituent_predicate": "Mars is placed in the 7th house of the natal chart — the most intensely positioned Mangal Dosha",
        "severity": "severe",
        "cancellation_rules": [
            "Mars in 7H occupies own sign (Aries or Scorpio) reducing the destructive quality",
            "Mars in 7H is in Capricorn (exaltation) — strength shifts the dosha toward career drive, not marital destruction",
            "Jupiter aspects the 7th house strongly (9th or 5th from Jupiter covers 7H)",
            "A natural malefic is also in the 7th (same affliction on both sides of the partnership equation — some commentators accept mutual cancellation)",
            "Partner also has Mangal Dosha (the classical mutual cancellation rule)",
            "Venus is conjunct Mars in the 7th house with no additional affliction",
            "Mars is in Jupiter's sign (Sagittarius or Pisces) in the 7th",
            "For Libra Ascendant: Mars (lord of 2nd and 7th) in 7H is in own sign — lordship argument partially cancels",
        ],
        "classical_citation": "BPHS Ch. 73 v.1-12; Phaladeepika Ch. 14 v.1-8; Saravali; considered most intense of all Mangal Dosha positions",
        "affected_domains": ["marriage", "spouse", "longevity_of_spouse", "partnerships", "health_of_partner"],
        "remedy_approach": "Kumbh Vivah strongly recommended, Mangal Yantra, wearing red coral under expert guidance, Mangal Kavach, fasting on Tuesdays, matching with Mangalik partner",
    },

    "mangal_dosha_8h": {
        "name": "Mangal Dosha — 8th House",
        "category": "mangal",
        "constituent_predicate": "Mars is placed in the 8th house of the natal chart",
        "severity": "severe",
        "cancellation_rules": [
            "Mars in 8H occupies Scorpio (own sign) — in own sign the destructive 8H quality is partially neutralised",
            "Jupiter aspects the 8th house or Mars directly",
            "Mars is in Capricorn (exaltation) in the 8th house",
            "Partner also has Mangal Dosha",
            "Venus aspects the 8th house strongly",
            "For Cancer Ascendant, Mars is yogakaraka (4th and 9th lord) — benefic lordship mitigates",
        ],
        "classical_citation": "BPHS Ch. 73; Phaladeepika Ch. 14; 8H Mars affects ayu (longevity) of spouse and sudden disruptions",
        "affected_domains": ["marriage", "longevity_of_spouse", "sudden_events", "inheritance", "occult"],
        "remedy_approach": "Kumbh Vivah, Mangal puja, reading Sundarkand, matching with Mangalik partner, red coral after consultation",
    },

    "mangal_dosha_12h": {
        "name": "Mangal Dosha — 12th House",
        "category": "mangal",
        "constituent_predicate": "Mars is placed in the 12th house of the natal chart",
        "severity": "moderate",
        "cancellation_rules": [
            "Mars in 12H occupies Pisces (Jupiter's sign — cancellation by benefic ownership)",
            "Jupiter aspects the 12th house or Mars from the 4th, 8th, or 3rd",
            "Venus is in the 12th house with Mars",
            "For Aries or Scorpio Ascendant, Mars in 12H is in Pisces — mutual benefic moderation",
            "Partner also has Mangal Dosha",
            "Mars is in its own sign (Pisces is not own — needs Aries/Scorpio overlay via alternate counting)",
        ],
        "classical_citation": "BPHS Ch. 73; Phaladeepika Ch. 14; 12H Mars affects bed pleasures and foreign-land expenditure",
        "affected_domains": ["marriage", "bed_pleasures", "expenditure", "foreign_travel", "liberation"],
        "remedy_approach": "Mangal puja on Tuesdays, recitation of Mangal stotra, red coral under consultation, Kumbh Vivah if other factors confirm",
    },

    # -----------------------------------------------------------------------
    # KALA SARPA — dosha form (general)
    # -----------------------------------------------------------------------

    "kala_sarpa_dosha": {
        "name": "Kala Sarpa Dosha",
        "category": "kala_sarpa",
        "constituent_predicate": "All seven classical planets (Sun through Saturn) are hemmed between Rahu and Ketu on one arc of the zodiac; no planet falls outside the Rahu-Ketu axis",
        "severity": "severe",
        "cancellation_rules": [
            "Any planet falls outside the Rahu-Ketu containment arc — breaks the dosha",
            "Jupiter aspects Rahu from a kendra or trikona — significant mitigation",
            "Rahu or Ketu is conjunct or aspected by its dispositor in own or exaltation sign",
            "Strong Ascendant lord unafflicted by the nodal axis",
            "Chart has multiple strong Raja Yogas or Pancha Mahapurusha yoga — positive yogas override",
        ],
        "classical_citation": "Kala Sarpa doctrine; Parashari tradition; Rahu-Ketu Shakti texts; see also BPHS Ch. 28 on nodal effects",
        "affected_domains": ["career", "marriage", "wealth", "health", "mental_peace", "family", "progeny"],
        "remedy_approach": "Kala Sarpa puja at Trimbakeshwar or Ujjain, Naga puja, Rahu-Ketu homa, wearing hessonite and cat's eye under expert guidance, Sarpa sukta recitation",
    },

    # -----------------------------------------------------------------------
    # PITRU DOSHA — ancestral karmic debt (paternal lineage)
    # -----------------------------------------------------------------------

    "pitru_dosha": {
        "name": "Pitru Dosha",
        "category": "pitru",
        "constituent_predicate": "Sun is afflicted by Rahu, Ketu, or Saturn in the 9th or 10th house; or Sun and Moon are simultaneously afflicted in the 9th house; indicating unresolved ancestral karmic debt from the paternal lineage",
        "severity": "moderate",
        "cancellation_rules": [
            "Jupiter aspects Sun or the 9th house strongly — wisdom and dharma neutralise the ancestral burden",
            "Sun is in own sign (Leo) in the 9th or 10th despite nodal affliction",
            "The afflicting planet is in its own sign or exaltation in the same house",
            "Native performs regular Pitru Tarpan (ancestral water offerings) — ritual observance mitigates karmic burden",
            "Sun is exalted (Aries) in the relevant house",
        ],
        "classical_citation": "BPHS Ch. 59 (Pitru dosha); Parashari tradition; Dharma Sindhu; Nirnaya Sindhu on Shraddha observances",
        "affected_domains": ["father", "authority", "career", "dharma", "progeny", "ancestral_lineage"],
        "remedy_approach": "Shraddha and Pitru Tarpan on Pitru Paksha, Pind Daan at Gaya or Varanasi, feeding Brahmins, Sun puja on Sundays, recitation of Aditya Hridayam",
    },

    # -----------------------------------------------------------------------
    # MATRI DOSHA — affliction to mother significations
    # -----------------------------------------------------------------------

    "matri_dosha": {
        "name": "Matri Dosha",
        "category": "matri",
        "constituent_predicate": "Moon is afflicted by Rahu, Ketu, Saturn, or Mars in the 4th house; or Moon is very weak (neecha, combust, or in Krishna Ashtami/amavasya phase) and additionally afflicted — indicating disruption to maternal blessings and emotional stability",
        "severity": "moderate",
        "cancellation_rules": [
            "Jupiter aspects the 4th house or Moon strongly",
            "Moon is in own sign (Cancer) despite being in 4H with affliction — domicile strength mitigates",
            "Moon is in exaltation (Taurus) in the 4th house",
            "Venus is conjunct Moon in the 4th house without additional malefic interference",
            "Strong 4th lord in kendra or trikona compensates for Moon's affliction",
        ],
        "classical_citation": "BPHS Ch. 54 (Matri bhava); Phaladeepika Ch. 11; classical house signification texts",
        "affected_domains": ["mother", "homeland", "emotional_stability", "domestic_happiness", "property"],
        "remedy_approach": "Chandra puja on Mondays, recitation of Sri Sukta and Chandra kavach, offering milk to Shiva, wearing pearl under expert guidance, service to mother and elderly women",
    },

    # -----------------------------------------------------------------------
    # NAGA DOSHA — ancestral snake karma
    # -----------------------------------------------------------------------

    "naga_dosha": {
        "name": "Naga Dosha",
        "category": "graha_dosha",
        "constituent_predicate": "Rahu is placed in the 1st, 2nd, 5th, or 7th house, afflicting those house significations with serpentine ancestral karma; particularly relevant when Rahu is unaspected by benefics",
        "severity": "moderate",
        "cancellation_rules": [
            "Jupiter aspects Rahu's house strongly",
            "Rahu is in its exaltation sign (Taurus or Gemini per tradition) in the affected house",
            "The 5th lord is strong and unafflicted",
            "Rahu's dispositor is in a kendra or trikona in full strength",
            "Native has performed Naga puja or inherited Naga worship in family tradition",
        ],
        "classical_citation": "Parashari tradition; Naga dosha texts; Muhurta Chintamani; Tamil Nadi tradition on Rahu in specific houses",
        "affected_domains": ["progeny", "marriage", "health", "family", "ancestral_karma"],
        "remedy_approach": "Naga puja at snake shrines, releasing live snakes into forests, Naga Panchami worship, recitation of Naga Gayatri, performing Sarpa Samskara rituals",
    },

    # -----------------------------------------------------------------------
    # SARPA DOSHA — intense malefic triple affliction in trines
    # -----------------------------------------------------------------------

    "sarpa_dosha": {
        "name": "Sarpa Dosha",
        "category": "graha_dosha",
        "constituent_predicate": "Multiple malefic planets (Rahu, Saturn, and Mars — or any two of the three) are simultaneously placed in the trine houses (1st, 5th, and 9th) without benefic mitigation, creating an intense negative serpentine pattern across the dharma trikona",
        "severity": "very_severe",
        "cancellation_rules": [
            "Jupiter is in one of the trikona houses, counterbalancing the malefic concentration",
            "Malefic planets in the trikona are in their own or exaltation signs",
            "Strong benefic aspects cover all three trikona houses",
            "Ascendant lord is exceptionally strong (vargottama, exalted, or in own sign in kendra)",
        ],
        "classical_citation": "Parashari tradition; Nadi texts on multiple malefics in trines; BPHS Ch. 28 (Rahu-Ketu effects); classical sarpa dosha identification",
        "affected_domains": ["dharma", "progeny", "fortune", "mental_peace", "health", "longevity"],
        "remedy_approach": "Naga and Sarpa puja, Rahu-Ketu homa, recitation of Maha Mrityunjaya mantra, Kala Sarpa puja, feeding serpents, Naga Pratishtha (installation of Naga image in temple)",
    },

    # -----------------------------------------------------------------------
    # GURU CHANDAL DOSHA — Jupiter afflicted by Rahu/Ketu
    # -----------------------------------------------------------------------

    "guru_chandal_dosha": {
        "name": "Guru Chandal Dosha",
        "category": "graha_dosha",
        "constituent_predicate": "Jupiter is conjunct Rahu or Ketu in the same house, or Jupiter is aspected by Rahu or Ketu within a strong orb; corrupts Jupiter's natural significations of wisdom, dharma, children, and teacher-student relationships",
        "severity": "moderate",
        "cancellation_rules": [
            "Jupiter is in own sign (Sagittarius or Pisces) despite Rahu/Ketu conjunction — dignity partially counteracts the corruption",
            "Jupiter is exalted (Cancer) despite the nodal affliction",
            "Jupiter is conjunct Rahu in a trikona house with strong dispositor — some traditions consider this a powerful though unconventional combination",
            "Strong Venus aspects Jupiter — balances the wisdom corruption",
            "Native is born in Shukla Paksha with strong Moon — counteracts the mental corruption",
        ],
        "classical_citation": "BPHS Ch. 28 (Rahu-Ketu effects on grahas); Phaladeepika; Parashari tradition; modern commentary by B.V. Raman",
        "affected_domains": ["dharma", "wisdom", "progeny", "guru_relationship", "higher_education", "jupiter"],
        "remedy_approach": "Jupiter and Rahu puja, recitation of Guru mantra (Om Graam Greem Graum Sah Guruve Namah), donation of yellow items on Thursdays, Durga puja, avoiding unethical advice-giving",
    },

    # -----------------------------------------------------------------------
    # GRAHAN DOSHA — eclipse point dosha
    # -----------------------------------------------------------------------

    "grahan_dosha": {
        "name": "Grahan Dosha",
        "category": "graha_dosha",
        "constituent_predicate": "Sun or Moon is within 10 degrees of Rahu or Ketu at birth (eclipse proximity zone); Sun grahan dosha affects vitality, father, and authority; Moon grahan dosha affects mind, emotions, and mother",
        "severity": "moderate",
        "cancellation_rules": [
            "The afflicted Sun or Moon is in own sign or exaltation despite being near the node",
            "Jupiter aspects the Sun or Moon eclipsed by nodal proximity",
            "Birth is during the daytime with Sun strong (Sun grahan) or during Shukla Paksha with waxing Moon (Moon grahan)",
            "The nodal planet is also the Ascendant lord in the native's chart — karmic integration rather than destruction",
            "Sun or Moon is in a kendra and aspected by a strong benefic",
        ],
        "classical_citation": "BPHS Ch. 28; eclipse dosha in Muhurta Chintamani; Prasna Marga on eclipse-born natives; Nadi tradition",
        "affected_domains": ["sun_grahan: vitality, father, authority, career", "moon_grahan: mind, emotions, mother, mental_health"],
        "remedy_approach": "Surya puja for Sun grahan, Chandra puja for Moon grahan, recitation of Aditya Hridayam (Sun) or Sri Sukta (Moon), donation at solar/lunar eclipse, Rahu-Ketu homa",
    },

    # -----------------------------------------------------------------------
    # DARIDRA DOSHA — chronic poverty pattern
    # -----------------------------------------------------------------------

    "daridra_dosha": {
        "name": "Daridra Dosha",
        "category": "yoga_dosha",
        "constituent_predicate": "Lord of the 11th house (income and gains) is placed in the 6th, 8th, or 12th house (dusthanas); or both the 2nd lord (accumulated wealth) and 11th lord are simultaneously weak, debilitated, or afflicted by malefics — indicating a chronic pattern of financial insufficiency",
        "severity": "moderate",
        "cancellation_rules": [
            "11th lord in dusthana is also a kendra lord — double lordship compensates",
            "Jupiter or Venus aspects the 11th house or its lord",
            "Strong 2nd lord in kendra or exaltation counterbalances the 11th lord weakness",
            "Vipareeta Raja Yoga formed — 11th lord in 6th/8th/12th can indicate Vipareeta gain",
            "The 11th lord in dusthana is exalted in that dusthana",
        ],
        "classical_citation": "BPHS Ch. 39 (Dhana yoga chapter — reverse conditions); Phaladeepika Ch. 9 on poverty indicators; Saravali on 11th lord in dusthana",
        "affected_domains": ["wealth", "income", "gains", "financial_stability", "career"],
        "remedy_approach": "Lakshmi puja, recitation of Sri Sukta and Kubera mantra, donation to the poor, keeping home clean and clutter-free, placing Kubera yantra, performing Lakshmi homa on Fridays",
    },

    # -----------------------------------------------------------------------
    # SHAKATA DOSHA — fortune wheel / fluctuation pattern
    # -----------------------------------------------------------------------

    "shakata_dosha": {
        "name": "Shakata Dosha",
        "category": "yoga_dosha",
        "constituent_predicate": "Moon is placed in the 6th, 8th, or 12th house from Jupiter (dusthanas from Jupiter); or Jupiter and Moon are in a mutual 6-8 or 12-2 configuration — creating a wheel-like pattern of fortune fluctuation and repeated ups and downs in life",
        "severity": "mild",
        "cancellation_rules": [
            "Moon is in a kendra from the Ascendant despite being in dusthana from Jupiter",
            "Jupiter aspects Moon from its placement",
            "Moon is in own sign (Cancer) or exaltation (Taurus) despite the unfavorable position from Jupiter",
            "Strong Venus provides stability to Moon's fluctuations",
            "Moon is in Shukla Paksha (bright fortnight) with good strength",
        ],
        "classical_citation": "BPHS Ch. 33 (lunar yogas — Shakata is the reverse of Gaja Kesari); Saravali Ch. 19; Phaladeepika Ch. 6",
        "affected_domains": ["fortune", "career", "mental_peace", "relationships", "financial_stability"],
        "remedy_approach": "Ganesha puja to stabilise the wheel of fortune, recitation of Vishnu Sahasranama, Monday fasting for Moon, Jupiter puja on Thursdays, wearing yellow sapphire and pearl together under consultation",
    },

    # -----------------------------------------------------------------------
    # VISH DOSHA — Saturn-Moon conjunction (toxic pattern)
    # -----------------------------------------------------------------------

    "vish_dosha": {
        "name": "Vish Dosha (Vish Yoga)",
        "category": "graha_dosha",
        "constituent_predicate": "Saturn and Moon are placed in the same sign (conjunction) in the natal chart, creating a toxic (visha = poison) interaction between the mind-significator Moon and the grief-significator Saturn — producing chronic pessimism, mental distress, and health vulnerabilities",
        "severity": "moderate",
        "cancellation_rules": [
            "Jupiter aspects the Saturn-Moon conjunction strongly",
            "Moon is in Shukla Paksha (waxing) and relatively strong despite the conjunction",
            "The conjunction occurs in Cancer (Moon's own sign) — Moon's dignity partially counteracts Saturn's gloom",
            "Venus is conjunct the Saturn-Moon pair, softening the harshness",
            "The conjunction occurs in an upachaya house (3, 6, 10, 11) — upachaya placement improves with time",
        ],
        "classical_citation": "BPHS Ch. 44 (Saturn-Moon conjunction effects); Phaladeepika; Parashari tradition; classical Vish Yoga texts",
        "affected_domains": ["mental_health", "health", "relationships", "emotional_wellbeing", "longevity"],
        "remedy_approach": "Shani puja on Saturdays, Chandra puja on Mondays, recitation of Shani stotra and Sri Sukta, oil massage and donation of black sesame, wearing blue sapphire or pearl under expert consultation, Maha Mrityunjaya mantra",
    },

    # -----------------------------------------------------------------------
    # PUNARPHOO DOSHA — delays and repeated disappointments
    # -----------------------------------------------------------------------

    "punarphoo_dosha": {
        "name": "Punarphoo Dosha",
        "category": "graha_dosha",
        "constituent_predicate": "Saturn aspects or conjoins Moon in the natal chart; or Moon is placed in Saturn's signs (Capricorn or Aquarius); associated with repeated disappointments in marriage and relationships, delays in finding a life partner, and the tendency for events to recur or reverse (punah = again, phoo = blossoming)",
        "severity": "moderate",
        "cancellation_rules": [
            "Jupiter aspects Moon or Saturn's position — wisdom and expansion overcome delays",
            "Moon is in Shukla Paksha and in a good nakshatra",
            "Saturn is in exaltation (Libra) or own sign (Capricorn or Aquarius) — disciplined energy rather than obstructing",
            "Venus is strongly placed in the 7th house or aspecting Moon",
            "The native's 7th house is protected by benefic aspect",
        ],
        "classical_citation": "Tamil Nadi tradition (Punarphoo concept); Parashari commentary on Saturn-Moon; Krishnamurti Paddhati references; classical marriage delay indicators",
        "affected_domains": ["marriage", "relationships", "partnership", "emotional_fulfillment", "delays"],
        "remedy_approach": "Saturn puja, recitation of Shani Ashtakam, offering black sesame and mustard oil to Saturn on Saturdays, Shiva puja, patience practices, delay-acceptance rituals, seeking blessings from elderly and Saturn-type figures",
    },

    # -----------------------------------------------------------------------
    # ANGARAK DOSHA — Mars-Rahu conjunction
    # -----------------------------------------------------------------------

    "angarak_dosha": {
        "name": "Angarak Dosha",
        "category": "graha_dosha",
        "constituent_predicate": "Mars is conjunct Rahu (or in some traditions Ketu) in the same house; the explosive energy of Mars amplified by Rahu's insatiable and unconventional nature produces Angarak (fire-like) results — extreme temper, impulsive violence, accidents, fire hazards, and legal troubles",
        "severity": "severe",
        "cancellation_rules": [
            "Jupiter aspects the Mars-Rahu conjunction strongly — wisdom contains the explosive energy",
            "Mars is in its own sign (Aries or Scorpio) or exaltation (Capricorn) — dignity channels the aggression constructively",
            "The conjunction occurs in an upachaya house (3, 6, 10, 11) — upachaya placement improves over time",
            "Venus is conjunct or aspecting Mars-Rahu — softens the fire",
            "A strong Ascendant lord in kendra protects the native from the worst manifestations",
        ],
        "classical_citation": "BPHS Ch. 28 (Rahu effects on co-joined planets); Parashari tradition; Angarak yoga texts; modern commentary on Mars-Rahu effects",
        "affected_domains": ["temper", "accidents", "fire_hazards", "legal_troubles", "enemies", "health"],
        "remedy_approach": "Mars and Rahu puja, recitation of Hanuman Chalisa and Bhairav stotra, wearing red coral under consultation, donation of lentils (masoor dal) and copper on Tuesdays, avoiding risky activities, anger management practices",
    },

    # -----------------------------------------------------------------------
    # VISHA YOGA (VISHA DOSHA) — near-death and chronic disease pattern
    # -----------------------------------------------------------------------

    "visha_yoga": {
        "name": "Visha Yoga (Visha Dosha)",
        "category": "graha_dosha",
        "constituent_predicate": "Saturn and Moon are together in the 1st house, or Saturn is placed in Moon's nakshatra while Moon is simultaneously afflicted by malefics — associated with near-death experiences, chronic undiagnosable disease, and deep karmic health burdens",
        "severity": "very_severe",
        "cancellation_rules": [
            "Jupiter aspects the 1st house or the Saturn-Moon combination",
            "Moon is in Shukla Paksha (bright half) and gaining strength",
            "Strong Ascendant lord in kendra mitigates the first-house concentration of malefics",
            "Venus is present in the 1st house with Saturn and Moon",
            "The native survives a critical health crisis and emerges with medical/healing gifts (Visha Yoga's classical transformation potential)",
        ],
        "classical_citation": "BPHS Ch. 44 (Saturn in 1H with Moon); classical Visha Yoga texts; Nadi tradition on chronic disease indicators",
        "affected_domains": ["health", "longevity", "mental_health", "vitality", "chronic_disease"],
        "remedy_approach": "Maha Mrityunjaya mantra japa (minimum 1.25 lakh recitations), Vishnu puja, Mrityunjaya homa, wearing Mahamrityunjaya yantra, fasting on Mondays and Saturdays, seeking medical treatment promptly for any health issue",
    },

    # -----------------------------------------------------------------------
    # KEMADRUM DOSHA — Moon without support
    # -----------------------------------------------------------------------

    "kemadrum_dosha": {
        "name": "Kemadrum Dosha",
        "category": "yoga_dosha",
        "constituent_predicate": "Moon has no planets (other than Sun) in its 2nd or 12th house, AND Moon is not in a kendra from the Ascendant, AND Moon is not aspected by or conjunct any planet — the most isolated Moon configuration, indicating lack of support, loneliness, and hardship",
        "severity": "moderate",
        "cancellation_rules": [
            "Moon is in a kendra (1, 4, 7, 10) from the Ascendant — this alone cancels Kemadrum per most authorities",
            "Moon is conjunct any planet (other than Sun)",
            "Moon is aspected by Jupiter",
            "A planet is in the 2nd or 12th from Moon (forming Sunafa or Anapha yoga instead)",
            "Moon is in own sign (Cancer) or exaltation (Taurus)",
            "Moon is in the same sign as the Ascendant lord",
        ],
        "classical_citation": "BPHS Ch. 33; Saravali Ch. 19; Phaladeepika Ch. 5 — standard lunar yoga texts",
        "affected_domains": ["social_support", "relationships", "mental_peace", "prosperity", "loneliness"],
        "remedy_approach": "Chandra puja on Mondays, recitation of Sri Sukta and Chandra stotra, wearing pearl, association with supportive community, strengthening social bonds, offering milk to Shiva on Mondays",
    },

    # -----------------------------------------------------------------------
    # SHRAPIT DOSHA — Saturn-Rahu conjunction (cursed past-life karma)
    # -----------------------------------------------------------------------

    "shrapit_dosha": {
        "name": "Shrapit Dosha",
        "category": "graha_dosha",
        "constituent_predicate": "Saturn and Rahu are conjunct in the same house in the natal chart; Shrapit (cursed) — indicates severe past-life karmic obstruction causing chronic delays, frustrations, broken relationships, career instability, and a feeling of being cursed or blocked in every endeavour",
        "severity": "very_severe",
        "cancellation_rules": [
            "Jupiter aspects the Saturn-Rahu conjunction strongly",
            "The conjunction occurs in an upachaya house (3, 6, 10, 11) — improvements come with time and effort",
            "Saturn is in exaltation (Libra) or own sign (Capricorn or Aquarius) — disciplined energy counteracts the curse",
            "Strong Ascendant lord in kendra protects the native",
            "Venus is conjunct or closely aspecting the Saturn-Rahu pair",
            "Native performs Saturn and Rahu remedies sincerely — karmic debt can be repaid through service",
        ],
        "classical_citation": "BPHS Ch. 28 (Rahu in conjunction with Saturn); Parashari tradition; Shrapit dosha texts; Tamil Nadi tradition",
        "affected_domains": ["career", "marriage", "relationships", "prosperity", "mental_peace", "longevity"],
        "remedy_approach": "Shani-Rahu puja, recitation of Shani Chalisa and Rahu mantra, donation of iron and black sesame, feeding crows (Rahu's bird) on Saturdays, Shiva abhisheka, performing Shraddha rites for ancestors, volunteer service",
    },

    # -----------------------------------------------------------------------
    # PITRA RIN DOSHA — Sun-Saturn variant of ancestral debt
    # -----------------------------------------------------------------------

    "pitra_rin_dosha": {
        "name": "Pitra Rin Dosha (Ancestral Debt)",
        "category": "pitru",
        "constituent_predicate": "Sun and Saturn are conjunct in the 9th house (dharma house), or Saturn aspects the Sun in the 9th house — indicating unresolved debt to the paternal lineage arising from the conflict between soul-authority (Sun) and karmic-law (Saturn) in the house of dharma and father",
        "severity": "moderate",
        "cancellation_rules": [
            "Jupiter aspects the 9th house or the Sun-Saturn combination",
            "Sun is in Leo (own sign) in the 9th house despite Saturn's presence",
            "The 9th lord is strong in kendra or trikona compensating for the afflicted 9th house",
            "Native performs regular Pitru Shraddha and ancestral rites",
        ],
        "classical_citation": "BPHS Ch. 59 (Pitra dosha variants); Dharma Sindhu; Nirnaya Sindhu on ancestral debt rituals",
        "affected_domains": ["father", "dharma", "fortune", "ancestral_lineage", "authority", "career"],
        "remedy_approach": "Pitru Tarpan on Amavasya days, Shraddha rites on Pitru Paksha, Surya Namaskar with Sun mantra, offering water to the Sun daily, Pind Daan at Gaya, donating to temples on Sundays",
    },

    # -----------------------------------------------------------------------
    # MATRI RIN DOSHA — Moon-Rahu in 4th house variant
    # -----------------------------------------------------------------------

    "matri_rin_dosha": {
        "name": "Matri Rin Dosha (Maternal Ancestral Debt)",
        "category": "matri",
        "constituent_predicate": "Moon and Rahu are conjunct in the 4th house, or Rahu afflicts the 4th house while Moon is simultaneously weak — indicating unresolved karmic debt to the maternal lineage or past-life harm done to a mother-figure",
        "severity": "moderate",
        "cancellation_rules": [
            "Jupiter aspects the 4th house or Moon-Rahu conjunction",
            "Moon is in own sign (Cancer) in the 4th house despite Rahu's presence",
            "Strong Venus aspects the 4th house",
            "Native performs maternal ancestral rites (Matri Shraddha)",
            "Rahu's dispositor is exalted or in own sign",
        ],
        "classical_citation": "BPHS Ch. 54 (4th house afflictions); Parashari commentary on Moon-Rahu; Nadi tradition on maternal debt indicators",
        "affected_domains": ["mother", "maternal_lineage", "homeland", "emotional_stability", "property"],
        "remedy_approach": "Chandra puja on Mondays, offerings to the Moon and to the Goddess, service to mother and maternal relatives, Matri Shraddha rites, wearing pearl under consultation",
    },

    # -----------------------------------------------------------------------
    # GRAHA YUDDHA DOSHA — planetary war
    # -----------------------------------------------------------------------

    "graha_yuddha_dosha": {
        "name": "Graha Yuddha Dosha (Planetary War)",
        "category": "graha_dosha",
        "constituent_predicate": "Two planets (other than Sun, Moon, Rahu, Ketu) are within 1 degree of each other in the same sign (planetary war condition); the planet with the lower degree of longitude is traditionally the winner, the planet with the higher degree is the loser — the losing planet loses significant strength and its significations become afflicted",
        "severity": "moderate",
        "cancellation_rules": [
            "The winning planet is a natural benefic (Jupiter or Venus) — even victory reduces affliction",
            "The losing planet is in its own sign or exaltation despite the war — intrinsic strength partially compensates",
            "Jupiter aspects the war zone (house containing the warring planets)",
            "The losing planet is not the Ascendant lord or lord of a key house",
        ],
        "classical_citation": "BPHS Ch. 3 (Graha Yuddha chapter); Phaladeepika Ch. 4; Saravali Ch. 5 — all classical texts define 1° orb for planetary war",
        "affected_domains": ["significations_of_losing_planet", "career", "health", "relationships"],
        "remedy_approach": "Puja for the losing planet in the war, wearing the gemstone of the losing planet under consultation, reciting the losing planet's mantra, performing homa for the afflicted planet on its ruling day",
    },

    # -----------------------------------------------------------------------
    # GANDANTA DOSHA — junction zone between water and fire signs
    # -----------------------------------------------------------------------

    "gandanta_dosha": {
        "name": "Gandanta Dosha",
        "category": "miscellaneous",
        "constituent_predicate": "A planet (especially Moon, Ascendant, or Ascendant lord) is placed in the last 3 degrees 20 minutes (last pada) of a water sign (Cancer, Scorpio, Pisces) or the first 3 degrees 20 minutes (first pada) of a fire sign (Aries, Leo, Sagittarius) — the junction zone between water and fire is called Gandanta (knot), indicating a zone of karmic intensity and potential difficulty",
        "severity": "moderate",
        "cancellation_rules": [
            "Moon is in a strong nakshatra despite being in the Gandanta zone — nakshatra lord's strength mitigates",
            "Jupiter aspects the Gandanta planet strongly",
            "The Gandanta planet is not Moon or the Ascendant lord — less impactful for secondary planets",
            "The native undergoes Gandanta shanti puja within 27 days of birth",
            "Strong overall chart with multiple benefic yogas offsets the Gandanta affliction",
        ],
        "classical_citation": "BPHS Ch. 8 (Gandanta); Muhurta Chintamani on Gandanta births; Prasna Marga; classical nakshatra texts defining the three Gandanta zones",
        "affected_domains": ["longevity", "health", "parents", "mental_peace", "overall_fortune"],
        "remedy_approach": "Gandanta shanti puja performed immediately after birth (or within 27 days), Nakshatra puja for the specific Gandanta nakshatra, recitation of Maha Mrityunjaya mantra by parents, Jupiter and Guru puja",
    },

    # -----------------------------------------------------------------------
    # PAPA KARTARI DOSHA — benefic planet hemmed between malefics
    # -----------------------------------------------------------------------

    "papa_kartari_dosha": {
        "name": "Papa Kartari Dosha (Malefic Scissors)",
        "category": "miscellaneous",
        "constituent_predicate": "A benefic planet (Jupiter, Venus, Mercury, or well-placed Moon) is hemmed between two malefic planets occupying its adjacent houses (one malefic in the 12th house from the benefic and another malefic in the 2nd house from the benefic) — the malefic scissors squeeze the benefic's positive energy",
        "severity": "mild",
        "cancellation_rules": [
            "One of the flanking malefics is in its own sign or exaltation — strength of the malefic reduces its scissors effect",
            "The hemmed benefic itself is in own sign or exaltation — strong dignity overcomes the hemming",
            "Jupiter aspects the hemmed benefic planet",
            "The hemmed benefic is a kendra or trikona lord — lordship importance overcomes the positional weakness",
        ],
        "classical_citation": "BPHS Ch. 16 (Kartari yoga chapter); Parashari tradition on Subha/Papa Kartari; classical yoga identification texts",
        "affected_domains": ["significations_of_hemmed_planet", "health", "prosperity", "relationships"],
        "remedy_approach": "Puja for the hemmed benefic planet, wearing its gemstone under consultation, reciting its mantra, strengthening the benefic through its natural diet and lifestyle recommendations (e.g., yellow for Jupiter, white for Venus)",
    },

    # -----------------------------------------------------------------------
    # KALATRA DOSHA — 7th house affliction (general marriage dosha)
    # -----------------------------------------------------------------------

    "kalatra_dosha": {
        "name": "Kalatra Dosha (Marriage House Affliction)",
        "category": "miscellaneous",
        "constituent_predicate": "Multiple malefics (Saturn, Mars, Rahu, Ketu, or Sun) afflict the 7th house simultaneously without any benefic aspect; or the 7th lord is placed in a dusthana (6th, 8th, or 12th) while also being debilitated or combust — indicating general affliction to the marriage and partnership sphere beyond Mangal Dosha specifically",
        "severity": "moderate",
        "cancellation_rules": [
            "Jupiter aspects the 7th house strongly",
            "Venus (natural karaka of marriage) is strong in the 7th or aspecting it",
            "The 7th lord despite being in dusthana is exalted in that house",
            "Partner chart has strong 7th house and 7th lord compensating",
            "Navamsa 7th house is strongly supported",
        ],
        "classical_citation": "BPHS Ch. 73 (Vivaha chapter); Phaladeepika Ch. 14; Saravali Ch. 30 — 7th house affliction analysis",
        "affected_domains": ["marriage", "partnerships", "spouse", "relationships", "business_partnerships"],
        "remedy_approach": "Venus and Jupiter puja, recitation of Sri Sukta and Venus mantra, wearing diamond or white sapphire under consultation, Swayamvara Parvati puja for marriage, fasting on Fridays and Thursdays",
    },

    # -----------------------------------------------------------------------
    # RAHU KETU DOSHA — general nodal affliction to key houses
    # -----------------------------------------------------------------------

    "rahu_ketu_dosha": {
        "name": "Rahu-Ketu Dosha (Nodal Axis Affliction)",
        "category": "graha_dosha",
        "constituent_predicate": "Rahu and Ketu's axis falls across key houses (1-7, 4-10, or 5-11) and both luminary planets (Sun and Moon) are simultaneously afflicted by the nodal axis through conjunction or aspect — creating a comprehensive nodal affliction to the chart's core pillars",
        "severity": "moderate",
        "cancellation_rules": [
            "Jupiter aspects both nodes or their houses strongly",
            "Nodal dispositors are in kendra or trikona in strength",
            "Sun and Moon are in their own or exaltation signs despite nodal proximity",
            "Strong overall chart with multiple positive yogas",
        ],
        "classical_citation": "BPHS Ch. 28 (Rahu-Ketu comprehensive effects); Parashari tradition; Jataka Parijata on nodal axis houses",
        "affected_domains": ["overall_fortune", "health", "mental_peace", "career", "relationships", "spiritual_growth"],
        "remedy_approach": "Rahu puja on Saturdays and Rahu Kalam, Ketu puja, Naga puja, recitation of Rahu and Ketu mantras, hessonite for Rahu or cat's eye for Ketu under expert guidance, ancestral rites",
    },

}

# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------


def get_dosha(name: str) -> dict:
    """Return dosha dict by name (case-insensitive).

    Args:
        name: Dosha canonical name (case-insensitive), e.g. 'mangal_dosha_7h'.

    Returns:
        The dosha definition dict.

    Raises:
        KeyError: if the dosha name is not found in DOSHA_DEFINITIONS.
    """
    return DOSHA_DEFINITIONS[name.lower()]


def list_doshas_by_category(category: str) -> list[str]:
    """Return sorted list of dosha names for the given category.

    Args:
        category: Category string, e.g. 'mangal', 'pitru'.

    Returns:
        Sorted list of dosha names matching the category.
        Returns empty list if category not found.
    """
    return sorted(
        name for name, d in DOSHA_DEFINITIONS.items()
        if d["category"] == category
    )


def list_doshas_by_severity(severity: str) -> list[str]:
    """Return sorted list of dosha names with the given severity.

    Args:
        severity: Severity string — one of: 'mild', 'moderate', 'severe', 'very_severe'.

    Returns:
        Sorted list of dosha names with the given severity.
        Returns empty list if no doshas match.
    """
    return sorted(
        name for name, d in DOSHA_DEFINITIONS.items()
        if d["severity"] == severity
    )


def get_all_dosha_categories() -> list[str]:
    """Return sorted unique list of all category strings in DOSHA_DEFINITIONS.

    Returns:
        Sorted list of unique category strings.
    """
    return sorted({d["category"] for d in DOSHA_DEFINITIONS.values()})


def get_mangal_dosha_houses() -> list[int]:
    """Return the list of house numbers where Mars causes Mangal Dosha.

    Classical tradition: 1st, 2nd, 4th, 7th, 8th, and 12th houses.

    Returns:
        Sorted list of house numbers: [1, 2, 4, 7, 8, 12].
    """
    return [1, 2, 4, 7, 8, 12]


# ---------------------------------------------------------------------------
# MODULE-LEVEL ASSERTIONS
# ---------------------------------------------------------------------------

assert len(DOSHA_DEFINITIONS) >= 20, (
    f"Expected 20+ doshas, got {len(DOSHA_DEFINITIONS)}"
)
assert all("constituent_predicate" in v for v in DOSHA_DEFINITIONS.values()), (
    "Every dosha must have a 'constituent_predicate' field"
)
assert all("severity" in v for v in DOSHA_DEFINITIONS.values()), (
    "Every dosha must have a 'severity' field"
)
assert all("classical_citation" in v for v in DOSHA_DEFINITIONS.values()), (
    "Every dosha must have a 'classical_citation' field"
)
assert all("cancellation_rules" in v for v in DOSHA_DEFINITIONS.values()), (
    "Every dosha must have a 'cancellation_rules' field"
)
assert "mangal_dosha_7h" in DOSHA_DEFINITIONS, (
    "'mangal_dosha_7h' must be in DOSHA_DEFINITIONS"
)
assert "guru_chandal_dosha" in DOSHA_DEFINITIONS, (
    "'guru_chandal_dosha' must be in DOSHA_DEFINITIONS"
)
assert "grahan_dosha" in DOSHA_DEFINITIONS, (
    "'grahan_dosha' must be in DOSHA_DEFINITIONS"
)
