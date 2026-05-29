"""
muhurta_rule_library.py — G37 Muhurta Rule Library
====================================================
Comprehensive Vedic muhurta rule library for 30+ activity types.
Pure Python, no DB. Global reference module.

Each activity entry defines:
  - required_tithis: auspicious tithi numbers (1–30); empty = any acceptable
  - forbidden_tithis: inauspicious tithi numbers; empty = none forbidden
  - required_varas: auspicious weekdays (lowercase English); empty = any
  - forbidden_varas: inauspicious weekdays for this activity
  - required_nakshatras: auspicious nakshatras (snake_case); empty = any
  - forbidden_nakshatras: inauspicious nakshatras for this activity
  - lagna_requirements: lagna sign requirements / guidelines
  - special_conditions: special planetary conditions and avoidances
  - classical_citation: textual source

Classical sources:
  - Muhurta-Chintamani (Ramadayalu)
  - Muhurta-Martanda
  - Jyotish-Ratnamala
  - BPHS muhurta chapters (Brihat Parashara Hora Shastra)

canonical_id: G37
stream: A
session: G37-S1 [BUILD-ORCH-A-22]
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# MUHURTA_RULES — main data structure
# ---------------------------------------------------------------------------

MUHURTA_RULES: dict[str, dict] = {

    # 1. Marriage
    "vivah": {
        "name": "Vivah (Marriage)",
        "category": "lifecycle",
        "required_tithis": [2, 3, 5, 7, 10, 11, 13],
        "forbidden_tithis": [4, 8, 12, 14, 30],
        "required_varas": ["monday", "wednesday", "thursday", "friday"],
        "forbidden_varas": ["tuesday", "saturday", "sunday"],
        "required_nakshatras": [
            "rohini", "mrigashira", "magha", "uttara_phalguni", "hasta",
            "swati", "anuradha", "mula", "uttara_ashadha",
            "uttara_bhadrapada", "revati",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola"],
        "lagna_requirements": [
            "Fixed signs (Taurus, Leo, Scorpio, Aquarius) preferred for stability",
            "Avoid malefics in 7H or 8H from lagna",
            "Venus and Jupiter must be direct (not retrograde)",
            "Lagna lord should be in kendra or trikona",
        ],
        "special_conditions": [
            "No retrograde Venus or Jupiter",
            "Avoid Guruashtami (Jupiter in 8H from Sun)",
            "Avoid solar and lunar eclipses within 15 days",
            "Moon must be waxing (Shukla Paksha) or at least not in Krishna Chaturdashi/Amavasya",
            "Avoid Kharmas (Sun in Sagittarius or Pisces last 15 days)",
        ],
        "classical_citation": "Muhurta-Chintamani ch. 10; BPHS Vivaha-muhurta adhyaya",
    },

    # 2. Housewarming
    "griha_pravesh": {
        "name": "Griha Pravesh (Housewarming / Entry into New Home)",
        "category": "property",
        "required_tithis": [2, 3, 5, 7, 10, 11, 13],
        "forbidden_tithis": [4, 8, 12, 14, 30],
        "required_varas": ["monday", "wednesday", "thursday", "friday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "rohini", "mrigashira", "hasta", "anuradha",
            "uttara_phalguni", "uttara_ashadha", "uttara_bhadrapada", "revati",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola", "bharani"],
        "lagna_requirements": [
            "Fixed lagna preferred for permanence and stability",
            "Lagna lord strong and well-placed",
            "4H lord strong (house signification)",
        ],
        "special_conditions": [
            "No eclipse within 15 days of ceremony",
            "Sun must be above the horizon at time of entry",
            "Avoid Dakshinayana (Sun's southward journey) if possible — prefer Uttarayana",
            "Avoid monsoon months (Ashadha, Shravana) per some traditions",
        ],
        "classical_citation": "Muhurta-Chintamani ch. 11; Muhurta-Martanda Griha-Pravesh section",
    },

    # 3. Journey / Travel
    "yatra": {
        "name": "Yatra (Journey / Travel)",
        "category": "journey",
        "required_tithis": [2, 3, 5, 6, 7, 10, 11, 12, 13],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["wednesday", "thursday", "friday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "ashwini", "mrigashira", "punarvasu", "pushya", "hasta",
            "anuradha", "shravana", "dhanishtha", "shatabhisha", "revati",
        ],
        "forbidden_nakshatras": ["bharani", "ashlesha", "jyestha", "moola"],
        "lagna_requirements": [
            "Movable (chara) lagna preferred for ease of journey",
            "Avoid malefics in 8H from lagna (danger on journey)",
        ],
        "special_conditions": [
            "Observe Disha Shool (inauspicious direction per weekday): Sun=East, Mon=North, Tue=North, Wed=North, Thu=South, Fri=West, Sat=East",
            "Moon should not be in 8H from lagna",
            "Avoid Bhadra (Vishti karana) for journey start",
        ],
        "classical_citation": "Muhurta-Chintamani ch. 15 Yatra-muhurta; BPHS ch. 99",
    },

    # 4. Beginning of Education
    "vidyarambha": {
        "name": "Vidyarambha (Beginning of Education / Studies)",
        "category": "education",
        "required_tithis": [2, 3, 5, 10, 11, 13],
        "forbidden_tithis": [4, 8, 9, 14, 30],
        "required_varas": ["wednesday", "thursday", "friday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "ashwini", "rohini", "mrigashira", "punarvasu", "pushya",
            "hasta", "anuradha", "uttara_phalguni", "uttara_ashadha",
            "uttara_bhadrapada", "revati", "shatabhisha",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola", "bharani"],
        "lagna_requirements": [
            "Mercury or Jupiter should influence lagna (aspect or placement)",
            "5H lord strong for intellect",
            "Lagna in Gemini, Virgo, or Sagittarius especially favored",
        ],
        "special_conditions": [
            "Mercury should not be combust or retrograde",
            "Jupiter should be direct and strong",
            "Avoid Rahu Kalam and Yamaganda for the start time",
        ],
        "classical_citation": "Muhurta-Chintamani ch. 14 Vidya-adhyaya; Jyotish-Ratnamala",
    },

    # 5. Weapons / Tools Worship
    "shastra_puja": {
        "name": "Shastra Puja (Weapons / Tools Worship)",
        "category": "spiritual",
        "required_tithis": [1, 2, 3, 5, 6, 7, 10, 11, 12, 13, 15],  # any shukla paksha
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["tuesday", "saturday"],
        "forbidden_varas": ["thursday"],
        "required_nakshatras": ["ardra", "ashlesha", "magha", "jyestha"],
        "forbidden_nakshatras": ["rohini", "uttara_phalguni", "revati"],
        "lagna_requirements": [
            "Mars strong and well-placed",
            "Aries or Scorpio lagna favored",
        ],
        "special_conditions": [
            "Performed on Vijayadashami (Dashami of Ashwin Shukla) as per tradition",
            "Mars should not be debilitated or combust",
            "Invoking Durga or Saraswati aspect for different weapons",
        ],
        "classical_citation": "Muhurta-Martanda Shastra-puja section; Devi Purana tradition",
    },

    # 6. Medical Treatment / Surgery Start
    "shastra_arambha": {
        "name": "Shastra Arambha (Medical Treatment / Surgical Procedure Start)",
        "category": "medical",
        "required_tithis": [2, 3, 5, 7, 10, 11, 12, 13],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["monday", "wednesday", "thursday", "friday"],
        "forbidden_varas": ["tuesday"],
        "required_nakshatras": [
            "ashwini", "rohini", "pushya", "anuradha", "hasta", "uttara_phalguni",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola", "bharani"],
        "lagna_requirements": [
            "Fixed lagna for stability of treatment",
            "Avoid Mars in 8H or 12H from lagna",
            "6H (disease) lord weak preferred",
            "8H (surgery/danger) lord weak preferred",
        ],
        "special_conditions": [
            "Avoid surgery on Tuesdays",
            "Moon in Shukla Paksha preferred",
            "Avoid surgery when Moon is in the sign ruling the body part being operated",
            "Physician's 5H and 10H lords should be strong",
        ],
        "classical_citation": "Muhurta-Chintamani Chikitsa section; BPHS Vaidya muhurta",
    },

    # 7. Commerce / Business Launch
    "vanijya_arambha": {
        "name": "Vanijya Arambha (Commerce / Business Launch)",
        "category": "business",
        "required_tithis": [2, 3, 5, 6, 7, 10, 11, 12, 13],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["wednesday", "thursday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "rohini", "mrigashira", "punarvasu", "pushya", "hasta",
            "anuradha", "uttara_phalguni", "revati",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola"],
        "lagna_requirements": [
            "Benefics in 1H, 2H, 10H, or 11H from lagna",
            "2H lord and 11H lord strong for financial gain",
            "Mercury should be strong (commerce planet)",
        ],
        "special_conditions": [
            "Avoid Rahu Kalam for inauguration",
            "Jupiter direct preferred",
            "Moon in waxing phase (Shukla Paksha) favored",
            "Avoid Ashtami and Chaturdashi Krishna",
        ],
        "classical_citation": "Muhurta-Martanda Vanijya section; Jyotish-Ratnamala",
    },

    # 8. Construction of House
    "griha_nirman": {
        "name": "Griha Nirman (Construction / Foundation Laying)",
        "category": "property",
        "required_tithis": [2, 3, 5, 7, 10, 11, 13],
        "forbidden_tithis": [4, 8, 12, 14, 30],
        "required_varas": ["monday", "wednesday", "thursday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "rohini", "uttara_phalguni", "uttara_ashadha", "uttara_bhadrapada",
            "hasta", "anuradha", "shravana",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola", "bharani", "krittika"],
        "lagna_requirements": [
            "Fixed or movable lagna; avoid dual lagna",
            "4H lord strong for property matters",
            "Avoid malefics in 4H lagna",
        ],
        "special_conditions": [
            "Sun must be in Uttarayana (northern course) for major construction",
            "Avoid monsoon season for foundation laying if possible",
            "Vastu Puja to be performed before or at muhurta",
            "Avoid Kharmas (Sun in Sagittarius or Pisces)",
        ],
        "classical_citation": "Muhurta-Chintamani ch. 12 Griha-nirman; BPHS",
    },

    # 9. Groundbreaking / Bhumi Puja
    "bhumi_puja": {
        "name": "Bhumi Puja (Groundbreaking Ceremony)",
        "category": "property",
        "required_tithis": [2, 3, 5, 7, 10, 11, 13],
        "forbidden_tithis": [4, 8, 12, 14, 30],
        "required_varas": ["monday", "wednesday", "thursday", "friday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "rohini", "mrigashira", "uttara_phalguni", "uttara_ashadha",
            "uttara_bhadrapada", "hasta", "anuradha", "shravana",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola", "bharani"],
        "lagna_requirements": [
            "Fixed lagna preferred for permanence of the property",
            "Sun should be above horizon at time of ceremony",
            "4H lord and Saturn (earth lord) both strong",
        ],
        "special_conditions": [
            "Sun must be above horizon",
            "Avoid monsoon season for outdoor ceremony",
            "Earth goddess propitiation mandatory",
            "Avoid Bhadra (Vishti karana) and Rahu Kalam",
        ],
        "classical_citation": "Muhurta-Chintamani Vastu-puja section; Griha-sutras tradition",
    },

    # 10. Naming Ceremony
    "namakarana": {
        "name": "Namakarana (Naming Ceremony — 11th day of birth)",
        "category": "lifecycle",
        "required_tithis": [2, 3, 5, 6, 7, 10, 11, 12, 13, 15],
        "forbidden_tithis": [4, 9, 14, 30],
        "required_varas": ["monday", "wednesday", "thursday", "friday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "ashwini", "rohini", "mrigashira", "punarvasu", "pushya",
            "uttara_phalguni", "hasta", "anuradha", "shravana", "revati",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola", "bharani"],
        "lagna_requirements": [
            "Lagna lord strong",
            "Moon strong (important for name association)",
        ],
        "special_conditions": [
            "Avoid rikta tithis (4, 9, 14, 30) — inauspicious",
            "Child's natal nakshatra lord should not be debilitated",
            "Name syllable selected per child's natal nakshatra pada",
        ],
        "classical_citation": "Grihya-Sutras; Muhurta-Chintamani Jatakarma section",
    },

    # 11. First Solid Food Ceremony
    "annaprashana": {
        "name": "Annaprashana (First Solid Food Ceremony)",
        "category": "lifecycle",
        "required_tithis": [2, 3, 5, 6, 7, 10, 11, 12, 13],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["monday", "wednesday", "thursday", "friday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "rohini", "mrigashira", "punarvasu", "pushya",
            "hasta", "shravana", "revati",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola"],
        "lagna_requirements": [
            "Moon strong and unafflicted",
            "Lagna lord in kendra or trikona",
            "Performed traditionally in the 6th month of life",
        ],
        "special_conditions": [
            "Performed ideally in child's 6th month (odd month for boys per some traditions)",
            "Avoid Rahu Kalam at time of first feeding",
            "Jupiter or benefic should aspect lagna or Moon",
        ],
        "classical_citation": "Grihya-Sutras; Muhurta-Martanda Samskaras section",
    },

    # 12. Sacred Thread Ceremony
    "upanayana": {
        "name": "Upanayana (Sacred Thread / Yajnopavita Ceremony)",
        "category": "lifecycle",
        "required_tithis": [2, 3, 5, 7, 10, 11, 13],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["monday", "wednesday", "thursday"],
        "forbidden_varas": ["tuesday", "saturday", "sunday"],
        "required_nakshatras": [
            "rohini", "mrigashira", "punarvasu", "pushya", "hasta",
            "uttara_phalguni", "uttara_ashadha", "uttara_bhadrapada", "revati",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola", "bharani"],
        "lagna_requirements": [
            "Lagna lord in kendra or trikona",
            "Jupiter should influence lagna or 5H (education and brahmacharya)",
            "5H lord strong",
        ],
        "special_conditions": [
            "Performed in Uttarayana (Jan–June) strongly preferred",
            "Jupiter must be direct and not combust",
            "Avoid solar and lunar eclipses within 15 days",
            "Brahmacharya period begins at this ceremony — lagna must be strong",
        ],
        "classical_citation": "Grihya-Sutras; Muhurta-Chintamani Upanayana chapter",
    },

    # 13. First Haircut Ceremony
    "mundan": {
        "name": "Mundan (First Haircut / Chudakarma Ceremony)",
        "category": "lifecycle",
        "required_tithis": [2, 3, 5, 6, 7, 10, 11, 12, 13],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["monday", "wednesday", "thursday", "friday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "ashwini", "mrigashira", "punarvasu", "pushya",
            "hasta", "anuradha", "shravana", "revati",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola", "bharani"],
        "lagna_requirements": [
            "Lagna lord strong",
            "Odd months of child's life preferred per tradition",
        ],
        "special_conditions": [
            "Performed traditionally in odd year of child's life (1st or 3rd year)",
            "Avoid Tuesdays strongly for hair removal ceremonies",
            "Moon should not be in the natal nakshatra of the child on this day (some traditions)",
        ],
        "classical_citation": "Grihya-Sutras; Muhurta-Martanda Chudakarma section",
    },

    # 14. Initiation / Diksha
    "deeksha": {
        "name": "Deeksha (Initiation / Spiritual Diksha)",
        "category": "spiritual",
        "required_tithis": [1, 2, 3, 5, 6, 7, 10, 11, 12, 13, 15],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["thursday", "monday", "saturday"],
        "forbidden_varas": ["tuesday"],
        "required_nakshatras": [
            "pushya", "uttara_bhadrapada", "rohini", "anuradha",
            "punarvasu", "revati", "hasta",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola"],
        "lagna_requirements": [
            "Shukla Paksha strongly preferred",
            "Jupiter strong for Vaishnava diksha",
            "Saturn strong for Shaiva diksha",
            "Guru (teacher) muhurta — Jupiter in kendra or trikona",
        ],
        "special_conditions": [
            "Guru (teacher/Guru) must be in a strong, auspicious position",
            "Thursday is the most favored day for spiritual initiation",
            "Saturday favored for Shiva-related initiations",
            "Avoid planetary war (graha-yuddha) at time of initiation",
        ],
        "classical_citation": "Tantra-Shastra; Muhurta-Martanda Diksha section; Jyotish-Ratnamala",
    },

    # 15. Fire Ceremony / Havan / Yagya
    "yagya": {
        "name": "Yagya / Havan (Fire Ceremony)",
        "category": "spiritual",
        "required_tithis": [2, 3, 5, 6, 7, 10, 11, 12, 13, 15],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["monday", "wednesday", "thursday", "friday", "sunday"],
        "forbidden_varas": [],
        "required_nakshatras": [
            "ashwini", "rohini", "mrigashira", "punarvasu", "pushya",
            "uttara_phalguni", "hasta", "anuradha", "uttara_ashadha",
            "uttara_bhadrapada", "revati",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "bharani"],
        "lagna_requirements": [
            "Avoid malefics in 8H from lagna",
            "10H should be strong — fire ceremony for public good",
            "Sun strong (Agni deity association)",
        ],
        "special_conditions": [
            "Brahma muhurta (pre-dawn) is most auspicious for Yagya",
            "Agni (fire) should be lit at an auspicious nakshatra",
            "Avoid performing during lunar or solar eclipse",
            "Brahmin priests should have auspicious natal positions",
        ],
        "classical_citation": "BPHS Yagya-muhurta; Muhurta-Chintamani Homa section",
    },

    # 16. Starting New Job / Service
    "seva_arambha": {
        "name": "Seva Arambha (Starting New Job / Service)",
        "category": "business",
        "required_tithis": [2, 3, 5, 6, 7, 10, 11, 12, 13],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["monday", "wednesday", "thursday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "rohini", "hasta", "anuradha", "shravana", "pushya",
            "uttara_phalguni", "uttara_ashadha",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola"],
        "lagna_requirements": [
            "10H (career) lord strong and well-placed",
            "6H (service) lord favorable",
            "Saturn (service planet) strong but not afflicting lagna",
        ],
        "special_conditions": [
            "Avoid Rahu Kalam for reporting time",
            "Moon should be in Shukla Paksha or at least waxing",
            "Avoid eclipse within 7 days",
        ],
        "classical_citation": "Muhurta-Martanda Karma-arambha section; Jyotish-Ratnamala",
    },

    # 17. Agriculture Start / Sowing
    "krishi_arambha": {
        "name": "Krishi Arambha (Agriculture Start / Sowing)",
        "category": "agriculture",
        "required_tithis": [2, 3, 5, 6, 10, 11, 13],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["monday", "wednesday", "thursday", "friday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "rohini", "mrigashira", "shravana", "anuradha", "hasta",
            "punarvasu", "revati",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola", "bharani"],
        "lagna_requirements": [
            "Waxing Moon (Shukla Paksha) strongly preferred",
            "Moon strong and in a fruitful nakshatra",
            "Movable or fixed lagna",
        ],
        "special_conditions": [
            "Moon should be waxing for sowing — promotes growth",
            "Avoid sowing during lunar eclipse",
            "Rain forecast (water element) favorable for tropical sowing",
            "Rohini nakshatra is classically the most auspicious for sowing",
        ],
        "classical_citation": "Muhurta-Chintamani Krishi section; Brihat Samhita agricultural chapters",
    },

    # 18. Vehicle Purchase
    "vahan_kharidi": {
        "name": "Vahan Kharidi (Vehicle Purchase)",
        "category": "business",
        "required_tithis": [2, 3, 5, 7, 10, 11],
        "forbidden_tithis": [4, 8, 12, 14, 30],
        "required_varas": ["wednesday", "thursday", "friday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "rohini", "hasta", "pushya", "revati", "ashwini", "anuradha",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola", "bharani"],
        "lagna_requirements": [
            "Fixed lagna for stability and durability of vehicle",
            "Venus strong (vehicle pleasure planet)",
            "4H lord strong (vehicle is a moveable property / Chara dhan)",
        ],
        "special_conditions": [
            "Venus should not be combust or debilitated",
            "Avoid Ashtami (8th tithi) strongly for vehicle purchases",
            "Pushya nakshatra is highly auspicious for all purchases",
        ],
        "classical_citation": "Muhurta-Martanda Kharidi section; Jyotish-Ratnamala",
    },

    # 19. Starting Industry / Factory
    "udyog_arambha": {
        "name": "Udyog Arambha (Starting Industry / Factory)",
        "category": "business",
        "required_tithis": [2, 3, 5, 7, 10, 11, 13],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["monday", "wednesday", "thursday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "rohini", "pushya", "anuradha", "uttara_phalguni", "shravana",
            "uttara_ashadha",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola"],
        "lagna_requirements": [
            "10H strong with benefics for business success",
            "2H lord and 11H lord strong for profit",
            "Avoid debilitated planets in kendra",
        ],
        "special_conditions": [
            "Inauguration should be during Abhijit muhurta if possible",
            "Avoid Rahu Kalam for ribbon-cutting ceremony",
            "Jupiter direct for sustainable growth",
        ],
        "classical_citation": "Muhurta-Martanda Udyoga section; Jyotish-Ratnamala",
    },

    # 20. Idol Installation in Temple
    "pratishtapana": {
        "name": "Pratishtapana (Idol / Deity Installation in Temple)",
        "category": "spiritual",
        "required_tithis": [1, 9, 10, 11, 12, 13, 15],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["sunday", "monday", "thursday", "friday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "rohini", "mrigashira", "uttara_phalguni", "hasta",
            "anuradha", "uttara_ashadha", "uttara_bhadrapada", "revati",
            "pushya",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola", "bharani"],
        "lagna_requirements": [
            "Fixed lagna strongly preferred for permanence of installation",
            "Sun strong (divine authority)",
            "Jupiter strong and influencing lagna",
        ],
        "special_conditions": [
            "Navami or Pratipada of Shukla Paksha preferred per many traditions",
            "Sun must be strong — not debilitated or combust",
            "Jupiter direct and ideally in own sign or exaltation",
            "Prana-pratishtha ritual performed by qualified acharya",
            "Avoid any planetary war (graha-yuddha) at exact installation moment",
        ],
        "classical_citation": "Agama Shastra; Muhurta-Chintamani Pratishtapana chapter; BPHS",
    },

    # 21. Ancestor Rites
    "shraddha": {
        "name": "Shraddha (Ancestor Rites / Pitru Karma)",
        "category": "spiritual",
        "required_tithis": [30],  # Amavasya is primary; also specific Krishna tithis
        "forbidden_tithis": [1, 2, 3, 5, 10, 11, 13, 15],
        "required_varas": ["saturday"],
        "forbidden_varas": [],
        "required_nakshatras": [
            "ashlesha", "magha", "jyestha",
        ],
        "forbidden_nakshatras": [],
        "lagna_requirements": [
            "Kutumba (family) houses strong",
            "Moon in Krishna Paksha for most shraddha rites",
        ],
        "special_conditions": [
            "Amavasya is the principal day for monthly Shraddha",
            "Pitru Paksha (Krishna Paksha of Bhadra/Ashwin month) dedicated to all ancestor rites",
            "Performed at the tithi matching ancestor's death tithi in Pitru Paksha",
            "Saturday is additionally favored for ancestor worship",
            "Avoid performing regular (non-shraddha) work during this period",
        ],
        "classical_citation": "Dharma-Sindhu; Muhurta-Chintamani Shraddha section; Garuda Purana",
    },

    # 22. Charity / Donation
    "daan": {
        "name": "Daan (Charity / Donation)",
        "category": "spiritual",
        "required_tithis": [2, 3, 5, 6, 7, 10, 11, 12, 13, 15],
        "forbidden_tithis": [],
        "required_varas": ["monday", "wednesday", "thursday", "friday"],
        "forbidden_varas": [],
        "required_nakshatras": [
            "rohini", "punarvasu", "pushya", "hasta", "anuradha",
            "uttara_phalguni", "uttara_ashadha", "revati",
        ],
        "forbidden_nakshatras": [],
        "lagna_requirements": [
            "Jupiter strong for dharmic giving",
            "12H (expenditure/loss) lord manageable — giving from surplus",
        ],
        "special_conditions": [
            "Any auspicious tithi and vara is generally acceptable for dana",
            "Specific items have specific planetary associations (gold=Sun, silver=Moon, food=Jupiter/Moon)",
            "Avoid giving on Amavasya for certain categories (some traditions)",
            "Sankranti (solar transit) days are highly auspicious for charity",
        ],
        "classical_citation": "Dharma-Sindhu; BPHS Dana-muhurta; Muhurta-Martanda",
    },

    # 23. Joining Monastery / Spiritual Retreat
    "ashram_pravesh": {
        "name": "Ashram Pravesh (Joining Monastery / Spiritual Retreat)",
        "category": "spiritual",
        "required_tithis": [2, 3, 5, 7, 10, 11, 13, 15],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["thursday", "monday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "rohini", "pushya", "uttara_bhadrapada", "anuradha",
            "punarvasu", "uttara_phalguni",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola"],
        "lagna_requirements": [
            "Shukla Paksha strongly preferred",
            "12H (renunciation) positively activated",
            "Jupiter (Guru planet) strong and in good position",
        ],
        "special_conditions": [
            "Jupiter must be direct and strong",
            "Guru's (teacher's) approval required before entering",
            "Moon in Shukla Paksha for entering a new phase of life",
        ],
        "classical_citation": "Muhurta-Martanda Ashrama-pravesh section; Dharma-Sindhu",
    },

    # 24. Loan Repayment
    "loan_repayment": {
        "name": "Loan Repayment (Paying Off Debt)",
        "category": "business",
        "required_tithis": [2, 5, 7, 10, 11, 13],
        "forbidden_tithis": [4, 8, 9, 12, 14, 30],
        "required_varas": ["wednesday", "thursday", "friday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "ashwini", "rohini", "pushya", "hasta", "anuradha", "revati",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola"],
        "lagna_requirements": [
            "6H (debt) lord weak is favorable — debts dissolving",
            "Jupiter strong for financial resolution",
        ],
        "special_conditions": [
            "Avoid Ashtami (8 / 23) — inauspicious for financial clearance",
            "Avoid Navami — inauspicious for debt settlement per tradition",
            "Shukla Paksha preferred — waxing energy supports liberation from debt",
            "Avoid Saturday for debt repayment per some traditions",
        ],
        "classical_citation": "Muhurta-Martanda Artha section; Jyotish-Ratnamala",
    },

    # 25. Land Purchase
    "bhoomi_kharidi": {
        "name": "Bhoomi Kharidi (Land Purchase)",
        "category": "property",
        "required_tithis": [2, 3, 5, 7, 10, 11, 13],
        "forbidden_tithis": [4, 8, 12, 14, 30],
        "required_varas": ["wednesday", "thursday", "friday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "rohini", "uttara_phalguni", "uttara_ashadha", "uttara_bhadrapada",
            "pushya", "hasta",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola", "bharani"],
        "lagna_requirements": [
            "Fixed lagna for permanence of land ownership",
            "4H lord strong (land/property house)",
            "Saturn strong (earth/land signification)",
        ],
        "special_conditions": [
            "Uttara Phalguni preferred among nakshatras for land acquisition",
            "Avoid purchase during Kharmas (Sun in Sagittarius or Pisces)",
            "Jupiter direct for long-term investment value",
            "Pushya nakshatra highly auspicious for all purchases including land",
        ],
        "classical_citation": "Muhurta-Chintamani Bhoomi section; Muhurta-Martanda",
    },

    # 26. Wedding Vows (part of vivah)
    "vivah_saptapadi": {
        "name": "Vivah Saptapadi (Seven Sacred Steps — Wedding Vows)",
        "category": "lifecycle",
        "required_tithis": [2, 3, 5, 7, 10, 11, 13],
        "forbidden_tithis": [4, 8, 12, 14, 30],
        "required_varas": ["monday", "wednesday", "thursday", "friday"],
        "forbidden_varas": ["tuesday", "saturday", "sunday"],
        "required_nakshatras": ["magha", "uttara_phalguni"],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola"],
        "lagna_requirements": [
            "Fixed lagna for marital stability",
            "Uttara Phalguni nakshatra is the most sacred for the saptapadi vows",
            "Magha nakshatra associated with ancestral blessings at the time of union",
        ],
        "special_conditions": [
            "Part of Vivah ceremony — inherits all vivah constraints",
            "Fire (agni) must be lit and present as witness",
            "Arundati-Vashishtha (Mizar-Alcor binary) viewed at ceremony per tradition",
            "Lagna rising at the exact moment of the 7th step is the marriage lagna",
        ],
        "classical_citation": "Grihya-Sutras; Muhurta-Chintamani Vivah-saptapadi section",
    },

    # 27. Medical Treatment (general, not surgery)
    "chikitsa_arambha": {
        "name": "Chikitsa Arambha (Medical Treatment / Therapy Start)",
        "category": "medical",
        "required_tithis": [2, 3, 5, 6, 7, 10, 11, 12, 13],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["monday", "wednesday", "thursday", "friday"],
        "forbidden_varas": ["tuesday"],
        "required_nakshatras": [
            "ashwini", "rohini", "pushya", "anuradha", "hasta",
            "uttara_phalguni", "punarvasu",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola", "bharani"],
        "lagna_requirements": [
            "Lagna strong and free from malefic aspect",
            "6H lord (disease) weak and 8H lord (chronic issues) weak preferred",
            "12H lord (hospitalization) not in lagna",
        ],
        "special_conditions": [
            "Avoid surgery on Tuesdays",
            "Moon should not be in the nakshatra ruling the body part being treated",
            "Ashwini nakshatra (Ashwini Kumars = divine physicians) auspicious",
            "Avoid Rahu Kalam and Yamaganda for treatment start",
        ],
        "classical_citation": "Muhurta-Chintamani Chikitsa section; BPHS Vaidya muhurta",
    },

    # 28. Giving Daughter in Marriage
    "kanya_daan": {
        "name": "Kanya Daan (Giving Daughter in Marriage)",
        "category": "lifecycle",
        "required_tithis": [2, 3, 5, 7, 10, 11, 13],
        "forbidden_tithis": [4, 8, 12, 14, 30],
        "required_varas": ["monday", "wednesday", "thursday", "friday"],
        "forbidden_varas": ["tuesday", "saturday", "sunday"],
        "required_nakshatras": [
            "uttara_phalguni", "rohini", "mrigashira", "hasta",
            "anuradha", "uttara_ashadha", "uttara_bhadrapada", "revati",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola"],
        "lagna_requirements": [
            "ASC (Lagna) lord strong for the bride's wellbeing",
            "Uttara Phalguni nakshatra specifically auspicious for kanya daan",
            "7H (marriage partner) clean and benefic-influenced",
        ],
        "special_conditions": [
            "Part of Vivah ceremony — inherits all vivah constraints",
            "Daughter's horoscope must be matched (guna-milan) with groom's",
            "Venus and Jupiter must both be direct and strong",
            "Father of the bride's lagna lord must be auspicious",
        ],
        "classical_citation": "Grihya-Sutras; Muhurta-Chintamani Kanya-daan section; BPHS",
    },

    # 29. Military Expedition
    "sena_yatra": {
        "name": "Sena Yatra (Military Expedition / Battle Commencement)",
        "category": "journey",
        "required_tithis": [2, 3, 5, 6, 7, 10, 11],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["tuesday", "saturday"],
        "forbidden_varas": ["thursday", "friday"],
        "required_nakshatras": ["ardra", "ashlesha", "jyestha"],
        "forbidden_nakshatras": ["rohini", "revati", "punarvasu"],
        "lagna_requirements": [
            "Mars strong and prominent for military action",
            "Fixed lagna for endurance; movable for speed of campaign",
        ],
        "special_conditions": [
            "Mars must be strong — not debilitated or combust",
            "Aggressive nakshatras (Ugra and Tikshna class) preferred",
            "Commander's natal Mars should be in a strong position",
            "Vijayadashami (Ashwin Dashami) traditionally most auspicious for expeditions",
        ],
        "classical_citation": "Brihat Samhita Sena-yatra chapter; Muhurta-Martanda",
    },

    # 30. Metal / Gold Purchase
    "dhatu_kharidi": {
        "name": "Dhatu Kharidi (Metal / Gold / Precious Metals Purchase)",
        "category": "business",
        "required_tithis": [2, 3, 5, 7, 10, 11, 13],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["sunday", "monday", "thursday"],  # gold=Sun/Thursday; silver=Monday
        "forbidden_varas": ["tuesday"],
        "required_nakshatras": [
            "pushya", "rohini", "uttara_phalguni", "hasta", "revati", "ashwini",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola"],
        "lagna_requirements": [
            "Pushya nakshatra is considered the most auspicious for gold purchase",
            "Sunday for gold (Sun governs gold)",
            "Thursday for gold (Jupiter governs wealth)",
            "Monday for silver (Moon governs silver)",
            "Venus strong for luxury metals",
        ],
        "special_conditions": [
            "Gold: Sunday or Thursday in Pushya nakshatra is the supreme combination",
            "Silver: Monday preferred",
            "Copper: Tuesday acceptable (Mars rules copper)",
            "Iron: Saturday acceptable (Saturn rules iron)",
            "Tin/Bronze: Wednesday acceptable (Mercury rules tin)",
            "Avoid Ashtami for all precious metal purchases",
        ],
        "classical_citation": "Muhurta-Martanda Dhatu-kharidi section; Jyotish-Ratnamala",
    },

    # 31. Sena Pratishtha / Coronation / Installation of Leader
    "rajyabhisheka": {
        "name": "Rajyabhisheka (Coronation / Installation of Ruler / Leader)",
        "category": "social",
        "required_tithis": [1, 2, 3, 5, 10, 11, 12, 13, 15],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["sunday", "thursday", "monday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "rohini", "hasta", "pushya", "uttara_phalguni",
            "anuradha", "uttara_ashadha", "shravana",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola"],
        "lagna_requirements": [
            "Leo or Aries lagna strongly preferred (royal signs)",
            "Sun strong and prominent (royal authority)",
            "Jupiter in kendra or trikona",
        ],
        "special_conditions": [
            "Sun (royal planet) must not be debilitated or combust",
            "Uttarayana preferred for coronations",
            "Abhijit muhurta highly favorable",
            "No eclipses within 15 days",
        ],
        "classical_citation": "Brihat Samhita Rajyabhisheka chapter; Muhurta-Martanda",
    },

    # 32. Partnership / Contract Signing
    "samjhauta": {
        "name": "Samjhauta (Partnership / Agreement / Contract Signing)",
        "category": "business",
        "required_tithis": [2, 3, 5, 6, 7, 10, 11, 12, 13],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["wednesday", "thursday", "friday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "rohini", "mrigashira", "pushya", "hasta", "anuradha",
            "uttara_phalguni", "revati",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola"],
        "lagna_requirements": [
            "Mercury strong (contracts and agreements)",
            "7H (partnership) lord strong and unafflicted",
            "2H lord strong for financial agreements",
        ],
        "special_conditions": [
            "Mercury should not be retrograde for signing agreements",
            "Both parties' horoscopes should have compatible ruling planets",
            "Avoid planetary war (graha-yuddha) at signing moment",
        ],
        "classical_citation": "Muhurta-Martanda Vanijya section; Jyotish-Ratnamala",
    },

    # 33. Garbhadhana (Conception Ceremony)
    "garbhadhana": {
        "name": "Garbhadhana (Conception Ceremony / First Conjugal Union for Progeny)",
        "category": "lifecycle",
        "required_tithis": [1, 2, 3, 5, 7, 10, 11, 13],
        "forbidden_tithis": [4, 8, 12, 14, 30],
        "required_varas": ["monday", "wednesday", "thursday", "friday"],
        "forbidden_varas": ["tuesday", "saturday", "sunday"],
        "required_nakshatras": [
            "rohini", "mrigashira", "anuradha", "hasta", "uttara_phalguni",
            "uttara_ashadha", "uttara_bhadrapada", "shravana",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola", "bharani", "krittika"],
        "lagna_requirements": [
            "Jupiter influences lagna for progeny (5H significator)",
            "5H lord strong and unafflicted",
            "Moon should be in an auspicious nakshatra (dhruva or mridu class)",
        ],
        "special_conditions": [
            "Performed traditionally on 4th–16th night after menstruation",
            "Even nights favored for male progeny; odd nights for female (traditional belief)",
            "Jupiter direct and strong",
            "Avoid malefics in 5H from lagna",
        ],
        "classical_citation": "Grihya-Sutras; Muhurta-Chintamani Garbhadhana section; BPHS",
    },

    # 34. Punya-Puja / Griha Shanti (House Purification)
    "griha_shanti": {
        "name": "Griha Shanti (House Purification / Vastu Shanti)",
        "category": "spiritual",
        "required_tithis": [2, 3, 5, 7, 10, 11, 13, 15],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["monday", "wednesday", "thursday", "friday"],
        "forbidden_varas": ["tuesday", "saturday"],
        "required_nakshatras": [
            "rohini", "mrigashira", "punarvasu", "pushya", "hasta",
            "anuradha", "uttara_phalguni", "revati",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola"],
        "lagna_requirements": [
            "Fixed lagna for permanent pacification",
            "4H (home/house) lord strong",
            "No malefics in 4H from lagna",
        ],
        "special_conditions": [
            "Performed typically before or during Griha Pravesh",
            "Vastu Purusha (house deity) propitiated per directional Vastu rules",
            "All 8 directional deities invoked",
            "Avoid Rahu Kalam for the main puja",
        ],
        "classical_citation": "Vastu-Shastra; Muhurta-Martanda Griha-shanti section",
    },

    # 35. Jaladhivasa (Water Immersion / Idol Immersion)
    "visarjana": {
        "name": "Visarjana (Idol Immersion / Deity Farewell Ceremony)",
        "category": "spiritual",
        "required_tithis": [10, 11, 12, 13, 14, 15],
        "forbidden_tithis": [1, 4, 8, 30],
        "required_varas": ["monday", "thursday", "friday"],
        "forbidden_varas": ["tuesday"],
        "required_nakshatras": [
            "rohini", "hasta", "anuradha", "uttara_bhadrapada", "revati",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola"],
        "lagna_requirements": [
            "Water signs (Cancer, Scorpio, Pisces) in lagna for immersion",
            "Moon strong for water ceremonies",
        ],
        "special_conditions": [
            "Performed at the conclusion of festival periods (e.g., Ganesh Chaturthi, Durga Puja)",
            "Specific traditional calendar dates override muhurta calculations",
            "Water body must be natural — river or ocean preferred",
        ],
        "classical_citation": "Dharma-Sindhu; tradition per festival calendars; Muhurta-Martanda",
    },

    # 36. Raksha Bandhan / Protection Ceremony
    "raksha_bandhan": {
        "name": "Raksha Bandhan (Protection / Protective Thread Ceremony)",
        "category": "social",
        "required_tithis": [15],  # Shravana Purnima specifically
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["monday", "thursday", "friday"],
        "forbidden_varas": ["tuesday"],
        "required_nakshatras": ["shravana", "rohini", "hasta", "pushya"],
        "forbidden_nakshatras": ["ashlesha", "jyestha"],
        "lagna_requirements": [
            "Moon strong (Purnima is peak Moon day)",
            "Protective deity (Indra) invoked for the ceremony",
        ],
        "special_conditions": [
            "Traditionally performed on Shravana Purnima",
            "Bhadra (Vishti karana) must have passed before tying the raksha",
            "Elder ties raksha during Aparahna (afternoon) per tradition",
        ],
        "classical_citation": "Dharma-Sindhu; tradition per festival calendar; Muhurta-Martanda",
    },

    # 37. Vivah Panchami (Sita-Ram spiritual anniversary)
    "vivah_panchami": {
        "name": "Vivah Panchami (Sita-Ram Sacred Anniversary Worship)",
        "category": "spiritual",
        "required_tithis": [5],  # 5th of Margashirsha shukla paksha
        "forbidden_tithis": [],
        "required_varas": [],
        "forbidden_varas": [],
        "required_nakshatras": [],
        "forbidden_nakshatras": [],
        "lagna_requirements": [
            "Observed on Margashirsha Shukla Panchami regardless of muhurta",
            "This is a fixed calendar observance, not a muhurta to be chosen",
        ],
        "special_conditions": [
            "Falls on 5th day of bright fortnight of Margashirsha month",
            "Commemorates the sacred marriage of Sita and Ram per Ramayana tradition",
            "Worship and reading of Ramcharitmanas is the primary observance",
        ],
        "classical_citation": "Ramcharitmanas; Vaishnavite tradition; Dharma-Sindhu",
    },

    # 38. Navagraha Puja
    "navagraha_puja": {
        "name": "Navagraha Puja (Nine-Planet Worship Ceremony)",
        "category": "spiritual",
        "required_tithis": [2, 3, 5, 6, 7, 10, 11, 12, 13, 15],
        "forbidden_tithis": [4, 8, 14, 30],
        "required_varas": ["sunday", "monday", "wednesday", "thursday"],
        "forbidden_varas": [],
        "required_nakshatras": [
            "pushya", "rohini", "hasta", "anuradha",
            "uttara_phalguni", "revati",
        ],
        "forbidden_nakshatras": ["ashlesha", "jyestha", "moola"],
        "lagna_requirements": [
            "All 9 planets considered — lagna should be free from affliction",
            "Specific planet's vara amplifies its puja efficacy",
        ],
        "special_conditions": [
            "Performed for planetary peace (shanti) before major life events",
            "Each planet's day (vara) amplifies its specific puja",
            "Rahu/Ketu puja traditionally on Saturday",
        ],
        "classical_citation": "BPHS Navagraha-puja chapter; Muhurta-Chintamani",
    },
}


# ---------------------------------------------------------------------------
# Module-level assertions — guard invariants
# ---------------------------------------------------------------------------

assert len(MUHURTA_RULES) >= 30, f"Expected >= 30 activities, got {len(MUHURTA_RULES)}"
assert all("required_tithis" in v for v in MUHURTA_RULES.values()), \
    "Some entry missing 'required_tithis'"
assert all("forbidden_varas" in v for v in MUHURTA_RULES.values()), \
    "Some entry missing 'forbidden_varas'"
assert all("required_nakshatras" in v for v in MUHURTA_RULES.values()), \
    "Some entry missing 'required_nakshatras'"
assert all("classical_citation" in v for v in MUHURTA_RULES.values()), \
    "Some entry missing 'classical_citation'"
assert "vivah" in MUHURTA_RULES
assert "griha_pravesh" in MUHURTA_RULES
assert "vidyarambha" in MUHURTA_RULES


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

_VALID_VARAS = frozenset({
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
})


def get_muhurta_rules(activity: str) -> dict:
    """Return the rules dict for the given activity.

    Case-insensitive. Raises KeyError if activity not found.

    Args:
        activity: snake_case activity name (e.g. "vivah", "VIVAH")

    Returns:
        The rules dict for the activity.

    Raises:
        KeyError: if activity is not in MUHURTA_RULES
    """
    key = activity.lower()
    if key not in MUHURTA_RULES:
        raise KeyError(
            f"Activity '{activity}' not found in MUHURTA_RULES. "
            f"Available: {sorted(MUHURTA_RULES)}"
        )
    return MUHURTA_RULES[key]


def list_activities_by_category(category: str) -> list[str]:
    """Return list of activity names for the given category.

    Args:
        category: one of lifecycle, journey, property, spiritual, medical,
                  business, agriculture, education, social

    Returns:
        List of activity snake_case names belonging to this category.
        Empty list if no activities match.
    """
    cat = category.lower()
    return [k for k, v in MUHURTA_RULES.items() if v.get("category", "").lower() == cat]


def get_auspicious_tithis(activity: str) -> list[int]:
    """Return required_tithis list for activity.

    Args:
        activity: snake_case activity name (case-insensitive)

    Returns:
        List of auspicious tithi numbers (1–30). Empty list means any tithi
        is acceptable.

    Raises:
        KeyError: if activity not found
    """
    return get_muhurta_rules(activity)["required_tithis"]


def get_auspicious_varas(activity: str) -> list[str]:
    """Return required_varas list for activity.

    Args:
        activity: snake_case activity name (case-insensitive)

    Returns:
        List of auspicious weekday names (lowercase English). Empty list
        means any vara is acceptable.

    Raises:
        KeyError: if activity not found
    """
    return get_muhurta_rules(activity)["required_varas"]


def get_auspicious_nakshatras(activity: str) -> list[str]:
    """Return required_nakshatras list for activity.

    Args:
        activity: snake_case activity name (case-insensitive)

    Returns:
        List of auspicious nakshatra names (snake_case). Empty list means
        any nakshatra is acceptable.

    Raises:
        KeyError: if activity not found
    """
    return get_muhurta_rules(activity)["required_nakshatras"]


def is_vara_suitable(activity: str, vara: str) -> bool:
    """Return True if vara is NOT in forbidden_varas for this activity.

    Args:
        activity: snake_case activity name (case-insensitive)
        vara: weekday name (case-insensitive, e.g. "Tuesday", "tuesday")

    Returns:
        True if the vara is not forbidden for this activity.
        Note: returns True even if vara is not in required_varas — the
        forbidden check is the classical primary constraint.

    Raises:
        KeyError: if activity not found
    """
    rules = get_muhurta_rules(activity)
    forbidden = {v.lower() for v in rules.get("forbidden_varas", [])}
    return vara.lower() not in forbidden
