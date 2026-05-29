"""
saham_formulas.py — Tajik Saham (Arabic Part / Sensitive Point) formula library
for MARSYS-JIS.

A Saham (Sanskrit: lot, portion, sensitive point) is a synthetic sensitive point
computed from three-body arithmetic:
    day-birth:   point = (body_A - body_B + body_C) % 360
    night-birth: point = (body_B - body_A + body_C) % 360  [A and B swapped]

Sahams originate in Arabic astrology (Parts) and were absorbed into Tajik
(Varshaphala / Annual Horoscopy) as a core predictive mechanism. The standard
text is Tajika Neelakanthi (Neelakantha, 17th c.); secondary sources include
Saravali (Kalyana Varma), Phala Deepika, and Jataka Parijata.

Body identifier strings used in formula tuples (must match keys in positions
dict passed to compute_saham_longitude):
    'sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn',
    'rahu', 'ketu', 'asc'

Usage:
    from pipeline.saham_formulas import (
        SAHAM_FORMULAS,
        get_saham,
        compute_saham_longitude,
        list_sahams_by_domain,
    )
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Master formula dictionary
# key = canonical lowercase name (no spaces)
# ---------------------------------------------------------------------------

SAHAM_FORMULAS: dict[str, dict] = {

    # -----------------------------------------------------------------------
    # Group 1 — Core Life-Domain Sahams
    # -----------------------------------------------------------------------

    "punya": {
        "name": "Punya",
        "domain": "fortune",
        "day_formula": ("moon", "sun", "asc"),
        "night_formula": ("sun", "moon", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Punya-saham: Chandra-Ravi+Lagna (day); "
            "reversed at night. Also: Saravali ch. 40."
        ),
    },

    "vidya": {
        "name": "Vidya",
        "domain": "learning",
        "day_formula": ("mercury", "sun", "asc"),
        "night_formula": ("sun", "mercury", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Vidya-saham: Budha-Ravi+Lagna (day)."
        ),
    },

    "yasas": {
        "name": "Yasas",
        "domain": "fame",
        "day_formula": ("jupiter", "sun", "asc"),
        "night_formula": ("sun", "jupiter", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Yasas-saham: Guru-Ravi+Lagna (day)."
        ),
    },

    "vivah": {
        "name": "Vivah",
        "domain": "marriage",
        "day_formula": ("venus", "sun", "asc"),
        "night_formula": ("sun", "venus", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Vivah-saham: Shukra-Ravi+Lagna (day). "
            "Phala Deepika ch. 27."
        ),
    },

    "karma": {
        "name": "Karma",
        "domain": "career",
        "day_formula": ("saturn", "sun", "asc"),
        "night_formula": ("sun", "saturn", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Karma-saham: Shani-Ravi+Lagna (day)."
        ),
    },

    "bhagya": {
        "name": "Bhagya",
        "domain": "luck",
        "day_formula": ("jupiter", "sun", "asc"),
        "night_formula": ("sun", "jupiter", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Bhagya-saham: Guru-Ravi+Lagna (day). "
            "Variant: some use 9th lord in place of Jupiter."
        ),
    },

    "putra": {
        "name": "Putra",
        "domain": "children",
        "day_formula": ("jupiter", "moon", "asc"),
        "night_formula": ("moon", "jupiter", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Putra-saham: Guru-Chandra+Lagna (day)."
        ),
    },

    "aayur": {
        "name": "Aayur",
        "domain": "longevity",
        "day_formula": ("saturn", "moon", "asc"),
        "night_formula": ("moon", "saturn", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Aayur-saham: Shani-Chandra+Lagna (day). "
            "Jataka Parijata ch. 14."
        ),
    },

    "mrityu": {
        "name": "Mrityu",
        "domain": "death",
        "day_formula": ("mars", "moon", "asc"),
        "night_formula": ("moon", "mars", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Mrityu-saham: Kuja-Chandra+Lagna (day). "
            "Variant: Lagna-Chandra+Kuja."
        ),
    },

    "roga": {
        "name": "Roga",
        "domain": "disease",
        "day_formula": ("saturn", "moon", "asc"),
        "night_formula": ("moon", "saturn", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Roga-saham: same bodies as Aayur variant; "
            "differs in interpretation context (6th-house afflictions)."
        ),
    },

    "raja": {
        "name": "Raja",
        "domain": "royalty",
        "day_formula": ("jupiter", "sun", "asc"),
        "night_formula": ("sun", "jupiter", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Raja-saham: Guru-Ravi+Lagna (day). "
            "Significance: authority, power, position."
        ),
    },

    "matri": {
        "name": "Matri",
        "domain": "mother",
        "day_formula": ("moon", "venus", "asc"),
        "night_formula": ("venus", "moon", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Matri-saham: Chandra-Shukra+Lagna (day)."
        ),
    },

    "pitri": {
        "name": "Pitri",
        "domain": "father",
        "day_formula": ("sun", "saturn", "asc"),
        "night_formula": ("saturn", "sun", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Pitri-saham: Ravi-Shani+Lagna (day)."
        ),
    },

    "bandhu": {
        "name": "Bandhu",
        "domain": "friends",
        "day_formula": ("mercury", "moon", "asc"),
        "night_formula": ("moon", "mercury", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Bandhu-saham: Budha-Chandra+Lagna (day)."
        ),
    },

    "shatru": {
        "name": "Shatru",
        "domain": "enemies",
        "day_formula": ("mars", "saturn", "asc"),
        "night_formula": ("saturn", "mars", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Shatru-saham: Kuja-Shani+Lagna (day)."
        ),
    },

    # -----------------------------------------------------------------------
    # Group 2 — Wealth, Prosperity, Business Sahams
    # -----------------------------------------------------------------------

    "kosha": {
        "name": "Kosha",
        "domain": "wealth_treasury",
        "day_formula": ("jupiter", "venus", "asc"),
        "night_formula": ("venus", "jupiter", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Kosha-saham: Guru-Shukra+Lagna (day). "
            "Treasury and stored wealth."
        ),
    },

    "mashik": {
        "name": "Mashik",
        "domain": "monthly_prosperity",
        "day_formula": ("mercury", "moon", "asc"),
        "night_formula": ("moon", "mercury", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Mashik-saham: monthly cash flow indicator."
        ),
    },

    "labha": {
        "name": "Labha",
        "domain": "gains",
        "day_formula": ("jupiter", "saturn", "asc"),
        "night_formula": ("saturn", "jupiter", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Labha-saham: Guru-Shani+Lagna (day). "
            "11th house gains and fulfilment of desires."
        ),
    },

    "vaisya": {
        "name": "Vaisya",
        "domain": "business",
        "day_formula": ("mercury", "jupiter", "asc"),
        "night_formula": ("jupiter", "mercury", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Vaisya-saham: trade and commercial activity."
        ),
    },

    "dhana": {
        "name": "Dhana",
        "domain": "wealth_acquired",
        "day_formula": ("jupiter", "moon", "asc"),
        "night_formula": ("moon", "jupiter", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Dhana-saham: accumulated wealth. "
            "Closely related to Putra; context determines application."
        ),
    },

    "artha": {
        "name": "Artha",
        "domain": "financial_purpose",
        "day_formula": ("venus", "jupiter", "asc"),
        "night_formula": ("jupiter", "venus", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Artha-saham: financial purpose and "
            "material achievement (one of Purusharthas)."
        ),
    },

    "sapada": {
        "name": "Sapada",
        "domain": "property",
        "day_formula": ("mars", "venus", "asc"),
        "night_formula": ("venus", "mars", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Sapada-saham: immovable property and land."
        ),
    },

    # -----------------------------------------------------------------------
    # Group 3 — Travel, Foreign, Journeys
    # -----------------------------------------------------------------------

    "desa": {
        "name": "Desa",
        "domain": "foreign_land",
        "day_formula": ("saturn", "jupiter", "asc"),
        "night_formula": ("jupiter", "saturn", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Desa-saham: relocation and travel to "
            "distant lands."
        ),
    },

    "paradesa": {
        "name": "Paradesa",
        "domain": "long_travel",
        "day_formula": ("saturn", "sun", "asc"),
        "night_formula": ("sun", "saturn", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Paradesa-saham: foreign settlement and "
            "extended travel abroad."
        ),
    },

    "jaladhi": {
        "name": "Jaladhi",
        "domain": "water_journey",
        "day_formula": ("moon", "saturn", "asc"),
        "night_formula": ("saturn", "moon", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Jaladhi-saham: sea voyages and water "
            "crossings."
        ),
    },

    # -----------------------------------------------------------------------
    # Group 4 — Honour, Respect, Power
    # -----------------------------------------------------------------------

    "mana": {
        "name": "Mana",
        "domain": "respect_honor",
        "day_formula": ("jupiter", "sun", "asc"),
        "night_formula": ("sun", "jupiter", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Mana-saham: social respect and honour "
            "from society."
        ),
    },

    "parakrama": {
        "name": "Parakrama",
        "domain": "courage",
        "day_formula": ("mars", "asc", "sun"),
        "night_formula": ("asc", "mars", "sun"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Parakrama-saham: courage and valour; "
            "note non-standard third body placement."
        ),
    },

    "bahu": {
        "name": "Bahu",
        "domain": "physical_strength",
        "day_formula": ("mars", "moon", "asc"),
        "night_formula": ("moon", "mars", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Bahu-saham: arm strength and physical "
            "prowess."
        ),
    },

    "bala": {
        "name": "Bala",
        "domain": "strength_child",
        "day_formula": ("sun", "moon", "asc"),
        "night_formula": ("moon", "sun", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Bala-saham: inherent strength of native; "
            "also child's vitality."
        ),
    },

    "siddhi": {
        "name": "Siddhi",
        "domain": "attainment",
        "day_formula": ("jupiter", "mercury", "asc"),
        "night_formula": ("mercury", "jupiter", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Siddhi-saham: spiritual and practical "
            "attainment and accomplishment."
        ),
    },

    "raksha": {
        "name": "Raksha",
        "domain": "protection",
        "day_formula": ("jupiter", "mars", "asc"),
        "night_formula": ("mars", "jupiter", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Raksha-saham: divine protection and "
            "refuge."
        ),
    },

    "durgha": {
        "name": "Durgha",
        "domain": "fortress",
        "day_formula": ("mars", "saturn", "moon"),
        "night_formula": ("saturn", "mars", "moon"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Durgha-saham: fortress (physical refuge "
            "and strategic stronghold)."
        ),
    },

    # -----------------------------------------------------------------------
    # Group 5 — Relationship, Spouse, Social
    # -----------------------------------------------------------------------

    "priya": {
        "name": "Priya",
        "domain": "spouse_satisfaction",
        "day_formula": ("venus", "moon", "asc"),
        "night_formula": ("moon", "venus", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Priya-saham: beloved; marital harmony "
            "and mutual affection."
        ),
    },

    "vahana": {
        "name": "Vahana",
        "domain": "vehicles",
        "day_formula": ("venus", "moon", "asc"),
        "night_formula": ("moon", "venus", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Vahana-saham: conveyances and vehicles. "
            "Variant uses Mars as modifier."
        ),
    },

    "stri": {
        "name": "Stri",
        "domain": "female_matters",
        "day_formula": ("venus", "sun", "moon"),
        "night_formula": ("sun", "venus", "moon"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Stri-saham: female relatives and women "
            "in native's life."
        ),
    },

    "mitra": {
        "name": "Mitra",
        "domain": "friend_ally",
        "day_formula": ("mercury", "venus", "asc"),
        "night_formula": ("venus", "mercury", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Mitra-saham: true friends and loyal "
            "allies."
        ),
    },

    "punya_bandhu": {
        "name": "PunyaBandhu",
        "domain": "spiritual_friend",
        "day_formula": ("jupiter", "venus", "moon"),
        "night_formula": ("venus", "jupiter", "moon"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Punya-Bandhu-saham: spiritually "
            "elevated companions and dharmic associates."
        ),
    },

    "brahmin": {
        "name": "Brahmin",
        "domain": "learned_one",
        "day_formula": ("jupiter", "mercury", "sun"),
        "night_formula": ("mercury", "jupiter", "sun"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Brahmin-saham: connection to learned, "
            "scholarly, and priestly persons."
        ),
    },

    # -----------------------------------------------------------------------
    # Group 6 — Adversity, Loss, Bondage
    # -----------------------------------------------------------------------

    "pasa": {
        "name": "Pasa",
        "domain": "bondage",
        "day_formula": ("saturn", "mars", "asc"),
        "night_formula": ("mars", "saturn", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Pasa-saham: noose, bondage, captivity "
            "and entanglement."
        ),
    },

    "bandhan": {
        "name": "Bandhan",
        "domain": "captivity",
        "day_formula": ("saturn", "rahu", "asc"),
        "night_formula": ("rahu", "saturn", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Bandhan-saham: imprisonment and "
            "restriction of freedom."
        ),
    },

    "naasa": {
        "name": "Naasa",
        "domain": "loss",
        "day_formula": ("rahu", "moon", "asc"),
        "night_formula": ("moon", "rahu", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Naasa-saham: destruction and irreversible "
            "loss."
        ),
    },

    "vivad": {
        "name": "Vivad",
        "domain": "dispute",
        "day_formula": ("mars", "mercury", "asc"),
        "night_formula": ("mercury", "mars", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Vivad-saham: litigation, quarrels and "
            "legal disputes."
        ),
    },

    "satru_karana": {
        "name": "SatruKarana",
        "domain": "enemy_making",
        "day_formula": ("mars", "rahu", "asc"),
        "night_formula": ("rahu", "mars", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Satru-Karana-saham: creation of enemies "
            "and hostile actors."
        ),
    },

    "rogasthana": {
        "name": "Rogasthana",
        "domain": "disease_house",
        "day_formula": ("saturn", "rahu", "moon"),
        "night_formula": ("rahu", "saturn", "moon"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Rogasthana-saham: seat of chronic "
            "disease and debilitating illness."
        ),
    },

    # -----------------------------------------------------------------------
    # Group 7 — Spirituality, Speech, Mind
    # -----------------------------------------------------------------------

    "satya": {
        "name": "Satya",
        "domain": "truth",
        "day_formula": ("sun", "mercury", "asc"),
        "night_formula": ("mercury", "sun", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Satya-saham: adherence to truth and "
            "veracity of speech."
        ),
    },

    "vak": {
        "name": "Vak",
        "domain": "speech",
        "day_formula": ("mercury", "asc", "moon"),
        "night_formula": ("asc", "mercury", "moon"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Vak-saham: eloquence and communicative "
            "ability."
        ),
    },

    "nidra": {
        "name": "Nidra",
        "domain": "sleep",
        "day_formula": ("moon", "saturn", "jupiter"),
        "night_formula": ("saturn", "moon", "jupiter"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Nidra-saham: quality of sleep and rest; "
            "related to mental peace."
        ),
    },

    "manda": {
        "name": "Manda",
        "domain": "slowness",
        "day_formula": ("saturn", "mars", "moon"),
        "night_formula": ("mars", "saturn", "moon"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Manda-saham: delay, slowness, and "
            "chronic obstacles."
        ),
    },

    "asha": {
        "name": "Asha",
        "domain": "hope",
        "day_formula": ("jupiter", "moon", "mercury"),
        "night_formula": ("moon", "jupiter", "mercury"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Asha-saham: hope, aspiration and "
            "future expectations."
        ),
    },

    # -----------------------------------------------------------------------
    # Group 8 — Progeny, Extended Family
    # -----------------------------------------------------------------------

    "santan": {
        "name": "Santan",
        "domain": "progeny_extended",
        "day_formula": ("jupiter", "venus", "asc"),
        "night_formula": ("venus", "jupiter", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Santan-saham: extended progeny concerns "
            "and children's welfare over time."
        ),
    },

    # -----------------------------------------------------------------------
    # Group 9 — Shadowy Bodies, Nodes
    # -----------------------------------------------------------------------

    "rahu_saham": {
        "name": "RahuSaham",
        "domain": "rahu_influence",
        "day_formula": ("rahu", "saturn", "asc"),
        "night_formula": ("saturn", "rahu", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Rahu-saham: areas where Rahu's "
            "obsessive-karmic pull manifests."
        ),
    },

    "ketu_saham": {
        "name": "KetuSaham",
        "domain": "ketu_influence",
        "day_formula": ("ketu", "saturn", "asc"),
        "night_formula": ("saturn", "ketu", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Ketu-saham: areas of Ketu's "
            "liberation/separation energy."
        ),
    },

    "chandra_saham": {
        "name": "ChandraSaham",
        "domain": "lunar_shadow",
        "day_formula": ("moon", "rahu", "asc"),
        "night_formula": ("rahu", "moon", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Chandra-saham: lunar shadow point "
            "reflecting subconscious mind."
        ),
    },

    "surya_saham": {
        "name": "SuryaSaham",
        "domain": "solar_point",
        "day_formula": ("sun", "rahu", "asc"),
        "night_formula": ("rahu", "sun", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Surya-saham: solar vitality and "
            "ego-related sensitive point."
        ),
    },

    # -----------------------------------------------------------------------
    # Group 10 — Miscellaneous / Specialised
    # -----------------------------------------------------------------------

    "aksha": {
        "name": "Aksha",
        "domain": "gambling",
        "day_formula": ("mercury", "mars", "asc"),
        "night_formula": ("mars", "mercury", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Aksha-saham: gambling, speculation and "
            "games of chance."
        ),
    },

    "paradesa_short": {
        "name": "ParadesaShort",
        "domain": "short_travel",
        "day_formula": ("mercury", "saturn", "asc"),
        "night_formula": ("saturn", "mercury", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — short-journey variant of Paradesa-saham."
        ),
    },

    "vahana_mars": {
        "name": "VahanaMars",
        "domain": "vehicles",
        "day_formula": ("venus", "mars", "asc"),
        "night_formula": ("mars", "venus", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Vahana-saham (Mars variant): aggressive "
            "or mechanised transport."
        ),
    },

    "aayur_alt": {
        "name": "AayurAlt",
        "domain": "longevity",
        "day_formula": ("saturn", "jupiter", "moon"),
        "night_formula": ("jupiter", "saturn", "moon"),
        "same_day_night": False,
        "classical_citation": (
            "Jataka Parijata ch. 14 — alternate Aayur-saham formula used by "
            "Kerala tradition."
        ),
    },

    "raja_alt": {
        "name": "RajaAlt",
        "domain": "royalty",
        "day_formula": ("sun", "jupiter", "asc"),
        "night_formula": ("jupiter", "sun", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Raja-saham alternate (Ravi-Guru+Lagna) "
            "used in annual-horoscopy."
        ),
    },

    "karma_alt": {
        "name": "KarmaAlt",
        "domain": "career",
        "day_formula": ("sun", "saturn", "moon"),
        "night_formula": ("saturn", "sun", "moon"),
        "same_day_night": False,
        "classical_citation": (
            "Saravali ch. 40 — alternate Karma-saham (Ravi-Shani+Chandra) used "
            "in natal horoscopy."
        ),
    },

    "pitri_alt": {
        "name": "PitriAlt",
        "domain": "father",
        "day_formula": ("saturn", "sun", "jupiter"),
        "night_formula": ("sun", "saturn", "jupiter"),
        "same_day_night": False,
        "classical_citation": (
            "Phala Deepika ch. 27 — alternate Pitri-saham using Jupiter as "
            "third body."
        ),
    },

    "matri_alt": {
        "name": "MatriAlt",
        "domain": "mother",
        "day_formula": ("venus", "moon", "jupiter"),
        "night_formula": ("moon", "venus", "jupiter"),
        "same_day_night": False,
        "classical_citation": (
            "Phala Deepika ch. 27 — alternate Matri-saham using Jupiter as "
            "third body."
        ),
    },

    "vivah_night_same": {
        "name": "VivahNightSame",
        "domain": "marriage",
        "day_formula": ("venus", "moon", "asc"),
        "night_formula": ("venus", "moon", "asc"),
        "same_day_night": True,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — invariant marriage-saham variant; "
            "some authorities hold this constant day and night."
        ),
    },

    "mrityu_alt": {
        "name": "MrityuAlt",
        "domain": "death",
        "day_formula": ("asc", "moon", "mars"),
        "night_formula": ("moon", "asc", "mars"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Mrityu alternate: Lagna-Chandra+Kuja."
        ),
    },

    "siddhi_pratyantar": {
        "name": "SiddhiPratyantar",
        "domain": "attainment",
        "day_formula": ("jupiter", "sun", "mercury"),
        "night_formula": ("sun", "jupiter", "mercury"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — sub-variant of Siddhi saham for "
            "sub-period specific attainments."
        ),
    },

    "labha_alt": {
        "name": "LabhaAlt",
        "domain": "gains",
        "day_formula": ("venus", "saturn", "asc"),
        "night_formula": ("saturn", "venus", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Labha alternate: Venus-Saturn+Lagna; "
            "gains through patient enterprise."
        ),
    },

    "desa_alt": {
        "name": "DesaAlt",
        "domain": "foreign_land",
        "day_formula": ("saturn", "moon", "mercury"),
        "night_formula": ("moon", "saturn", "mercury"),
        "same_day_night": False,
        "classical_citation": (
            "Saravali ch. 40 — alternate Desa-saham; foreign environments "
            "and cultural displacement."
        ),
    },

    "naasa_alt": {
        "name": "NaasaAlt",
        "domain": "loss",
        "day_formula": ("saturn", "ketu", "asc"),
        "night_formula": ("ketu", "saturn", "asc"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Naasa alternate (Saturn-Ketu): loss "
            "through renunciation or unseen forces."
        ),
    },

    "aksha_alt": {
        "name": "AkshaAlt",
        "domain": "gambling",
        "day_formula": ("mars", "venus", "mercury"),
        "night_formula": ("venus", "mars", "mercury"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Aksha alternate: risk appetite in "
            "creative speculation."
        ),
    },

    "asha_alt": {
        "name": "AshaAlt",
        "domain": "hope",
        "day_formula": ("moon", "venus", "jupiter"),
        "night_formula": ("venus", "moon", "jupiter"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Asha alternate: hope anchored in "
            "devotion and faith."
        ),
    },

    "punya_alt": {
        "name": "PunyaAlt",
        "domain": "fortune",
        "day_formula": ("moon", "sun", "jupiter"),
        "night_formula": ("sun", "moon", "jupiter"),
        "same_day_night": False,
        "classical_citation": (
            "Saravali ch. 40 — Punya alternate using Jupiter as third body "
            "instead of Ascendant."
        ),
    },

    "yasas_alt": {
        "name": "YasasAlt",
        "domain": "fame",
        "day_formula": ("jupiter", "mercury", "moon"),
        "night_formula": ("mercury", "jupiter", "moon"),
        "same_day_night": False,
        "classical_citation": (
            "Phala Deepika ch. 27 — Yasas alternate: intellectual fame and "
            "scholarly reputation."
        ),
    },

    "karma_sun_asc": {
        "name": "KarmaSunAsc",
        "domain": "career",
        "day_formula": ("sun", "asc", "saturn"),
        "night_formula": ("asc", "sun", "saturn"),
        "same_day_night": False,
        "classical_citation": (
            "Tajika Neelakanthi ch. 5 — Sun-Asc variant for career Saham; "
            "solar career drive grounded through Lagna."
        ),
    },

    "santan_alt": {
        "name": "SantanAlt",
        "domain": "children",
        "day_formula": ("moon", "jupiter", "venus"),
        "night_formula": ("jupiter", "moon", "venus"),
        "same_day_night": False,
        "classical_citation": (
            "Phala Deepika ch. 27 — Santan alternate: nurturing capacity for "
            "children."
        ),
    },

    "bandhu_alt": {
        "name": "BandhuAlt",
        "domain": "friends",
        "day_formula": ("venus", "moon", "mercury"),
        "night_formula": ("moon", "venus", "mercury"),
        "same_day_night": False,
        "classical_citation": (
            "Saravali ch. 40 — Bandhu alternate: social magnetism and depth "
            "of friendships."
        ),
    },
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_saham(name: str) -> dict:
    """Return saham formula by name (case-insensitive key lookup).

    Args:
        name: Canonical dictionary key, e.g. 'punya', 'PUNYA', or 'vivah'.

    Returns:
        The saham formula dict.

    Raises:
        KeyError: If name not found in SAHAM_FORMULAS.
    """
    normalised = name.strip().lower()
    if normalised not in SAHAM_FORMULAS:
        raise KeyError(
            f"Saham '{name}' not found. "
            f"Available: {sorted(SAHAM_FORMULAS.keys())}"
        )
    return SAHAM_FORMULAS[normalised]


def compute_saham_longitude(
    name: str,
    positions: dict[str, float],
    is_day_birth: bool,
) -> float:
    """Compute saham longitude given planetary positions.

    Formula:
        day:   (body_A - body_B + body_C) % 360
        night: (body_B - body_A + body_C) % 360  [A and B swapped]

    For sahams where same_day_night=True, the day formula is always used.

    Args:
        name: Saham key (case-insensitive).
        positions: Dict mapping body identifier to ecliptic longitude (0–360).
                   Required keys depend on the saham; typical keys:
                   'sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus',
                   'saturn', 'rahu', 'ketu', 'asc'.
        is_day_birth: True if born during day (sun above horizon).

    Returns:
        Saham longitude in range [0, 360).

    Raises:
        KeyError: If saham name not found or required body missing in positions.
        TypeError: If a position value cannot be interpreted as float.
    """
    formula_entry = get_saham(name)

    if formula_entry["same_day_night"] or is_day_birth:
        body_a, body_b, body_c = formula_entry["day_formula"]
    else:
        body_a, body_b, body_c = formula_entry["night_formula"]

    try:
        lon_a = float(positions[body_a])
        lon_b = float(positions[body_b])
        lon_c = float(positions[body_c])
    except KeyError as exc:
        raise KeyError(
            f"Saham '{name}' requires body '{exc.args[0]}' in positions dict."
        ) from exc

    return (lon_a - lon_b + lon_c) % 360.0


def list_sahams_by_domain(domain: str) -> list[str]:
    """Return list of saham canonical keys whose domain matches (case-insensitive).

    Args:
        domain: Domain string, e.g. 'marriage', 'children', 'career'.

    Returns:
        Sorted list of matching saham keys.  Empty list if none match.
    """
    target = domain.strip().lower()
    return sorted(
        key
        for key, entry in SAHAM_FORMULAS.items()
        if entry["domain"].lower() == target
    )
