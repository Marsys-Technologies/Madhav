"""
remedial_library.py — MARSYS-JIS Global Lookup G27
Integrated remedial library: per-graha complete remedial set
linking mantras (G33) + gemstones (G34) + yantras (G35) + rituals.

Classical citations:
  - Brihat Parashara Hora Shastra (BPHS) — Upaaya / remedial chapters
  - Garuda Purana — gemstone science (ratna-pariksha)
  - Mani Mala — classical Indian gemology
  - Vishnu Dharmottara Purana — yantra science
  - Skanda Purana — graha shanti procedures
  - Lal Kitab — alternative remedies
  - Muhurta Chintamani — auspicious timing for remedies

Mantra IDs reference the MANTRAS list in mantras.py (G33).
Gemstone data cross-references GEMSTONE_REFERENCE in gemstone_yantra_compat.py (G34).
Yantra names cross-reference YANTRA_REFERENCE in gemstone_yantra_compat.py (G35).
"""

from __future__ import annotations
from typing import Optional

# ---------------------------------------------------------------------------
# REMEDIAL_LIBRARY — one entry per graha
# ---------------------------------------------------------------------------

REMEDIAL_LIBRARY: dict[str, dict] = {
    "sun": {
        # Cross-refs to G33 mantras.py
        "mantra_ids": [
            "sun_beej_mantra",      # Oṃ hrāṃ hrīṃ hrauṃ saḥ sūryāya namaḥ
            "surya_gayatri",        # Surya Gayatri Mantra
            "aditya_hridayam_full", # Aditya Hridayam (31 verses)
            "surya_stotra_vyasa",   # Navagraha Stotra verse 1
            "gayatri_mantra",       # Universal Gayatri (Surya-aspect)
        ],
        # Cross-ref to G34 gemstone_yantra_compat.py
        "gemstone": {
            "primary": "Ruby",
            "alternate_name": "Manikya",
            "substitute": ["Red Spinel", "Red Garnet", "Red Zircon"],
            "weight_ratti": "3-6",
        },
        "metal": "Gold",
        "finger": "Ring finger, right hand",
        # Cross-ref to G35
        "yantra": "Surya Yantra",
        "yantra_citation": "Vishnu Dharmottara Purana; Tantrasara §4",
        "fasting_day": "Sunday",
        "charity": (
            "Wheat, jaggery, red cloth, copper, red flowers on Sunday at sunrise; "
            "donate to government officials or those in authority"
        ),
        "ritual": (
            "Surya Namaskar (108 rounds at sunrise); offer Gangajal + red flowers "
            "to the rising Sun; light ghee lamp; recite Aditya Hridayam"
        ),
        "gemstone_activation": (
            "On Sunday morning in Surya hora: wash in raw milk + honey + Gangajal, "
            "then dry with red cloth; consecrate with 'Om Hraam Hreem Hraum Sah "
            "Suryaya Namah' × 108; set in gold on ring finger right hand"
        ),
        "classical_citation": (
            "BPHS Ch.86 (Upaaya); Garuda Purana Ch.68; Mani Mala §3; "
            "Skanda Purana — Surya Mahatmya; Bhavishya Purana"
        ),
        "upagraha_remedy": (
            "Propitiate Kala (upagraha, shadow of Sun) via Shiva worship on Sundays; "
            "recite Maha Mrityunjaya Mantra to mitigate Kala influence"
        ),
        "special_remedy": (
            "Feed wheat + jaggery to a cow on Sunday; respect and serve father figures; "
            "donate copper vessel filled with water at sunrise; "
            "avoid arguments with superiors during Sun dasha/antardasha"
        ),
        "best_timing": "Sunrise on Sunday in Surya (Sun) hora",
        "deity": "Surya (Vivasvat / Aditya)",
        "color": "Red / Orange-Red",
        "direction": "East",
        "sacred_tree": "Arka (Calotropis gigantea — Madar)",
    },

    "moon": {
        "mantra_ids": [
            "moon_beej_mantra",     # Oṃ śrāṃ śrīṃ śrauṃ saḥ candrāya namaḥ
            "chandra_gayatri",      # Chandra Gayatri Mantra
            "maha_mrityunjaya",     # Maha Mrityunjaya (Shiva / Moon-ruled)
            "chandra_stotra_vyasa", # Navagraha Stotra verse 2
            "soma_vedic_mantra",    # Rigveda Soma mantra
        ],
        "gemstone": {
            "primary": "Pearl",
            "alternate_name": "Moti",
            "substitute": ["Moonstone", "White Coral", "White Topaz"],
            "weight_ratti": "2-6",
        },
        "metal": "Silver",
        "finger": "Little finger, right hand",
        "yantra": "Chandra Yantra",
        "yantra_citation": "Vishnu Dharmottara Purana; Tantrasara §4",
        "fasting_day": "Monday",
        "charity": (
            "Rice, milk, white cloth, silver, camphor on Monday; "
            "feed milk to the poor; donate white flowers at Shiva temple"
        ),
        "ritual": (
            "Offer milk + white flowers to Shiva (Shiva is Moon's lord); "
            "water Shivling on Mondays with raw milk; "
            "moonbath meditation on Purnima (full moon night)"
        ),
        "gemstone_activation": (
            "On Monday in Chandra hora: wash pearl in raw milk + rose water + Gangajal, "
            "dry with white cloth; consecrate with 'Om Shraam Shreem Shraum Sah "
            "Chandraya Namah' × 108; set in silver on little finger right hand"
        ),
        "classical_citation": (
            "BPHS Ch.86 (Upaaya); Garuda Purana Ch.68; Mani Mala §4; "
            "Skanda Purana — Chandra Mahatmya; Shiva Purana (Moon as Shiva's ornament)"
        ),
        "upagraha_remedy": (
            "Propitiate Mandi (upagraha, Gulika) via Shani worship when Moon is afflicted; "
            "recite Maha Mrityunjaya Mantra to strengthen Moon's life-force aspect"
        ),
        "special_remedy": (
            "Offer water to the Moon on Purnima nights; respect and serve mother figures; "
            "donate white rice or milk on Mondays; "
            "keep home clean and emotionally harmonious to strengthen Moon"
        ),
        "best_timing": "Monday night in Chandra (Moon) hora, ideally on Shukla Panchami or Purnima",
        "deity": "Chandra (Soma / Shashi)",
        "color": "White / Silver",
        "direction": "Northwest",
        "sacred_tree": "Palasha (Butea monosperma — Flame of the Forest)",
    },

    "mars": {
        "mantra_ids": [
            "mars_beej_mantra",       # Oṃ krāṃ krīṃ krauṃ saḥ bhaumāya namaḥ
            "mangala_gayatri",        # Mangala Gayatri
            "mangala_stotra_vyasa",   # Navagraha Stotra verse 3
            "mangala_kavach_seed",    # Mangala Kavach
            "hanuman_beej_mantra",    # Hanuman (Mars's deity)
        ],
        "gemstone": {
            "primary": "Red Coral",
            "alternate_name": "Moonga / Praval",
            "substitute": ["Carnelian", "Red Jasper", "Blood Stone"],
            "weight_ratti": "3-9",
        },
        "metal": "Gold or Copper",
        "finger": "Ring finger, right hand",
        "yantra": "Mangala Yantra",
        "yantra_citation": "Vishnu Dharmottara Purana; Skanda Purana — Bhoomi Puja",
        "fasting_day": "Tuesday",
        "charity": (
            "Red lentils (masoor dal), red cloth, copper vessel, jaggery on Tuesday; "
            "donate to soldiers or athletes; feed sweet red fruits"
        ),
        "ritual": (
            "Hanuman puja on Tuesdays (Hanuman is the deity of Mars); "
            "recite Hanuman Chalisa; offer sindoor + red flowers; "
            "chant Mangala Beej Mantra 108 times at sunrise"
        ),
        "gemstone_activation": (
            "On Tuesday in Mangala hora: wash Red Coral in raw honey + Gangajal, "
            "dry with red cloth; consecrate with 'Om Kraam Kreem Kraum Sah "
            "Bhaumaya Namah' × 108; set in gold/copper on ring finger right hand"
        ),
        "classical_citation": (
            "BPHS Ch.86 (Upaaya); Garuda Purana Ch.68 (Praval); Mani Mala §5; "
            "Skanda Purana — Mangala Mahatmya; Lal Kitab (alternate Mars remedies)"
        ),
        "upagraha_remedy": (
            "Propitiate Kuja (Mars upagraha) via Bhoomi (Earth) worship; "
            "place copper plate in earth near south wall of home"
        ),
        "special_remedy": (
            "Donate blood on a Tuesday (if medically eligible); "
            "serve at a military or fire-brigade institution; "
            "plant red flowers in garden; resolve conflicts with siblings (Mars = siblings); "
            "avoid initiating litigation during Mars affliction"
        ),
        "best_timing": "Sunrise on Tuesday in Mangala (Mars) hora",
        "deity": "Kartikeya (Skanda / Murugan) + Hanuman",
        "color": "Red / Blood Red",
        "direction": "South",
        "sacred_tree": "Khadira (Acacia catechu — Cutch tree)",
    },

    "mercury": {
        "mantra_ids": [
            "mercury_beej_mantra",  # Oṃ brāṃ brīṃ brauṃ saḥ budhāya namaḥ
            "budha_gayatri",        # Budha Gayatri
            "budha_stotra_vyasa",   # Navagraha Stotra verse 4
            "budha_kavach_seed",    # Budha Kavach
            "saraswati_beej_mantra", # Saraswati (Mercury's deity for learning)
        ],
        "gemstone": {
            "primary": "Emerald",
            "alternate_name": "Panna",
            "substitute": ["Green Tourmaline", "Peridot", "Green Jade"],
            "weight_ratti": "3-5",
        },
        "metal": "Gold",
        "finger": "Little finger, right hand",
        "yantra": "Budha Yantra",
        "yantra_citation": "Vishnu Dharmottara Purana; Tantrasara §4",
        "fasting_day": "Wednesday",
        "charity": (
            "Green moong dal, green cloth, books, writing instruments on Wednesday; "
            "donate to students or educational institutions; "
            "feed cows green grass"
        ),
        "ritual": (
            "Saraswati puja on Wednesdays; "
            "recite Budha Beej Mantra before study or business dealings; "
            "light incense and offer green flowers at Vishnu temple"
        ),
        "gemstone_activation": (
            "On Wednesday in Budha hora: wash Emerald in raw milk + tulsi water, "
            "dry with green cloth; consecrate with 'Om Braam Breem Braum Sah "
            "Budhaya Namah' × 108; set in gold on little finger right hand"
        ),
        "classical_citation": (
            "BPHS Ch.86 (Upaaya); Garuda Purana Ch.68 (Panna); Mani Mala §6; "
            "Skanda Purana — Budha Mahatmya; Vishnu Purana (Budha as son of Soma)"
        ),
        "upagraha_remedy": (
            "Propitiate Parvati (Budha's presiding deity) via Saraswati worship; "
            "green offerings at Durga/Parvati temple on Wednesdays"
        ),
        "special_remedy": (
            "Feed green vegetables or fodder to animals on Wednesdays; "
            "donate books or school supplies; "
            "keep business accounts honest (Mercury = commerce); "
            "chant Gayatri Mantra to strengthen Mercury's discernment"
        ),
        "best_timing": "Wednesday morning in Budha (Mercury) hora",
        "deity": "Vishnu (Narayana) + Saraswati",
        "color": "Green",
        "direction": "North",
        "sacred_tree": "Apamarga (Achyranthes aspera — Chaff-flower)",
    },

    "jupiter": {
        "mantra_ids": [
            "jupiter_beej_mantra",  # Oṃ grāṃ grīṃ grauṃ saḥ guruve namaḥ
            "guru_gayatri",         # Guru Gayatri
            "guru_stotra_vyasa",    # Navagraha Stotra verse 5
            "brihaspati_stuti",     # Brihaspati Stuti (Rigveda 4.50.6)
            "vishnu_sahasranama_seed", # Vishnu Sahasranama (Jupiter's deity)
        ],
        "gemstone": {
            "primary": "Yellow Sapphire",
            "alternate_name": "Pukhraj",
            "substitute": ["Yellow Topaz", "Citrine", "Yellow Beryl"],
            "weight_ratti": "3-7",
        },
        "metal": "Gold",
        "finger": "Index finger, right hand",
        "yantra": "Guru Yantra",
        "yantra_citation": "Vishnu Dharmottara Purana; Tantrasara §4",
        "fasting_day": "Thursday",
        "charity": (
            "Yellow cloth, turmeric, yellow sweets, banana, chana dal on Thursday; "
            "donate to teachers, priests, or Brahmin scholars; "
            "feed poor with yellow foods"
        ),
        "ritual": (
            "Vishnu / Brihaspati puja on Thursdays; "
            "recite Vishnu Sahasranama; offer yellow flowers + turmeric; "
            "light ghee lamp and read Bhagavad Gita"
        ),
        "gemstone_activation": (
            "On Thursday in Guru hora: wash Yellow Sapphire in raw milk + turmeric water + Gangajal, "
            "dry with yellow cloth; consecrate with 'Om Graam Greem Graum Sah "
            "Gurave Namah' × 108; set in gold on index finger right hand"
        ),
        "classical_citation": (
            "BPHS Ch.86 (Upaaya); Garuda Purana Ch.68 (Pushparagam); Mani Mala §7; "
            "Skanda Purana — Guru Mahatmya; Rigveda 4.50 (Brihaspati Suktam)"
        ),
        "upagraha_remedy": (
            "Propitiate Indra (Jupiter's deity-king) via Vishnu worship; "
            "offer banana and yellow flowers at Vishnu temple on Thursdays"
        ),
        "special_remedy": (
            "Feed banana to monkeys on Thursdays; "
            "serve and respect teachers and spiritual guides; "
            "donate to educational trusts; "
            "perform Satyanarayan Katha on auspicious Thursdays"
        ),
        "best_timing": "Thursday morning in Guru (Jupiter) hora",
        "deity": "Brihaspati / Indra / Vishnu",
        "color": "Yellow / Golden Yellow",
        "direction": "Northeast",
        "sacred_tree": "Peepal (Ficus religiosa — Sacred Fig)",
    },

    "venus": {
        "mantra_ids": [
            "venus_beej_mantra",    # Oṃ drāṃ drīṃ drauṃ saḥ śukrāya namaḥ
            "shukra_gayatri",       # Shukra Gayatri
            "shukra_stotra_vyasa",  # Navagraha Stotra verse 6
            "shukra_kavach_seed",   # Shukra Kavach
            "lakshmi_beej_mantra",  # Shrim Lakshmi Beej (Venus-Lakshmi link)
        ],
        "gemstone": {
            "primary": "Diamond",
            "alternate_name": "Heera / Vajra",
            "substitute": ["White Sapphire", "White Zircon", "White Topaz"],
            "weight_ratti": "0.5-2",
        },
        "metal": "Silver or Platinum",
        "finger": "Middle finger or ring finger, right hand",
        "yantra": "Shukra Yantra",
        "yantra_citation": "Vishnu Dharmottara Purana; Tantrasara §4",
        "fasting_day": "Friday",
        "charity": (
            "White rice, white cloth, cow's ghee, sugar, camphor on Friday; "
            "donate to women or artists; offer perfume and white flowers; "
            "feed sweet white foods to young women"
        ),
        "ritual": (
            "Lakshmi puja on Fridays; "
            "recite Lakshmi Ashtottaram + Shukra Beej Mantra; "
            "offer white flowers + sandalwood paste at Lakshmi or Durga temple; "
            "light scented candle or incense"
        ),
        "gemstone_activation": (
            "On Friday in Shukra hora: wash Diamond/substitute in rose water + Gangajal, "
            "dry with white silk; consecrate with 'Om Draam Dreem Draum Sah "
            "Shukraya Namah' × 108; set in silver on middle finger right hand"
        ),
        "classical_citation": (
            "BPHS Ch.86 (Upaaya); Garuda Purana Ch.68 (Vajra); Mani Mala §8; "
            "Skanda Purana — Shukra Mahatmya; Devi Bhagavata (Lakshmi-Shukra link)"
        ),
        "upagraha_remedy": (
            "Propitiate Indrani (Venus deity, queen of the gods) via Lakshmi worship; "
            "offer white flowers and sweets at Lakshmi temple on Fridays"
        ),
        "special_remedy": (
            "Donate white sweets to young girls on Fridays; "
            "respect and honour women, especially in one's own family; "
            "recite Lalita Sahasranama to strengthen Venus; "
            "keep bedroom clean and aesthetically pleasing (Venus rules pleasure/comforts)"
        ),
        "best_timing": "Friday morning in Shukra (Venus) hora",
        "deity": "Lakshmi / Indrani / Parashurama (guru of Shukra)",
        "color": "White / Cream / Pink",
        "direction": "Southeast",
        "sacred_tree": "Gular (Ficus racemosa — Cluster Fig)",
    },

    "saturn": {
        "mantra_ids": [
            "saturn_beej_mantra",        # Oṃ prāṃ prīṃ prauṃ saḥ śanaiścarāya namaḥ
            "shani_gayatri",             # Shani Gayatri
            "shani_stotra_vyasa",        # Navagraha Stotra verse 7
            "shani_shanti_stotra",       # Shani Shanti Stotra (Skanda Purana)
            "shani_dasharatha_stotra_seed", # Dasharatha Shani Stotra
            "shani_oil_lamp_mantra",     # Om Sham Shanaischaraya Namah
        ],
        "gemstone": {
            "primary": "Blue Sapphire",
            "alternate_name": "Neelam",
            "substitute": ["Amethyst", "Blue Topaz", "Iolite"],
            "weight_ratti": "3-6",
        },
        "metal": "Iron or Silver",
        "finger": "Middle finger, right hand",
        "yantra": "Shani Yantra",
        "yantra_citation": "Vishnu Dharmottara Purana; Tantrasara §4; Shani Mahatmya",
        "fasting_day": "Saturday",
        "charity": (
            "Black sesame seeds, black urad dal, black cloth, iron, mustard oil on Saturday; "
            "donate to the poor, labourers, disabled, or elderly; "
            "feed crows (Saturn's vehicle is a crow/vulture)"
        ),
        "ritual": (
            "Light sesame-oil lamp under a Peepal tree on Saturday evening; "
            "recite Shani Beej Mantra 108× or 23,000× (complete sadhana); "
            "offer black sesame + mustard oil to Shani idol; "
            "read/recite Shani Mahatmya from Skanda Purana on Saturdays"
        ),
        "gemstone_activation": (
            "CAUTION: Blue Sapphire must be tested before wearing — hold near body for 3 days. "
            "On Saturday in Shani hora: wash in black sesame water + Gangajal, "
            "dry with black/blue cloth; consecrate with 'Om Praam Preem Praum Sah "
            "Shanaischaraya Namah' × 108; set in iron or silver on middle finger right hand"
        ),
        "classical_citation": (
            "BPHS Ch.86 (Upaaya); Garuda Purana Ch.68 (Neela); Mani Mala §9; "
            "Skanda Purana — Shani Mahatmya; Dasharatha Shani Stotra"
        ),
        "upagraha_remedy": (
            "Propitiate Gulika (primary upagraha of Saturn) via Shiva worship; "
            "offer black sesame to Shiva + recite Maha Mrityunjaya Mantra on Saturdays"
        ),
        "special_remedy": (
            "Feed crows on Saturdays with black sesame or rice; "
            "serve labourers, sweepers, or the elderly without ego; "
            "avoid non-vegetarian food and alcohol during Saturn mahadasha; "
            "perform Hanuman puja on Saturdays (Hanuman mitigates Shani affliction); "
            "donate iron implements (tools) to the poor"
        ),
        "best_timing": "Saturday evening in Shani (Saturn) hora at Peepal tree",
        "deity": "Yama / Brahma (as Saturn's teacher) / Hanuman (for mitigation)",
        "color": "Black / Dark Blue",
        "direction": "West",
        "sacred_tree": "Shami (Prosopis cineraria — Khejri tree)",
    },

    "rahu": {
        "mantra_ids": [
            "rahu_beej_mantra",      # Oṃ bhrāṃ bhrīṃ bhrauṃ saḥ rāhave namaḥ
            "rahu_gayatri",          # Rahu Gayatri
            "rahu_stotra_vyasa",     # Navagraha Stotra verse 8
            "rahu_kavach_seed",      # Rahu Kavach
            "rahu_ketu_shanti_mantra", # Combined Rahu-Ketu Shanti (18,000 count)
            "durga_beej_mantra",     # Rahu's deity is Durga/Kali
        ],
        "gemstone": {
            "primary": "Hessonite Garnet",
            "alternate_name": "Gomed / Gomedha",
            "substitute": ["Zircon (Brown)", "Orange Topaz", "Spessartite Garnet"],
            "weight_ratti": "5-8",
        },
        "metal": "Silver or Panchdhatu (5-metal alloy)",
        "finger": "Middle finger, right hand (or as prescribed by jyotishi)",
        "yantra": "Rahu Yantra",
        "yantra_citation": "Vishnu Dharmottara Purana; Tantrasara §4; Skanda Purana Rahu chapter",
        "fasting_day": "Saturday (or Wednesday per some traditions)",
        "charity": (
            "Black sesame, blue-black cloth, coconut, iron, coal on Saturday; "
            "donate to foreigners, outcasts, or marginalized communities; "
            "feed coal workers or miners"
        ),
        "ritual": (
            "Durga / Kali puja for Rahu mitigation; "
            "recite Rahu Beej Mantra 18,000× (one complete sadhana); "
            "offer blue/black flowers + coconut at Bhairava or Kali temple; "
            "perform Rahu Ketu Shanti Homa on Rahu Kalam Saturdays"
        ),
        "gemstone_activation": (
            "CAUTION: Hessonite must be tested before wearing — seek jyotishi confirmation. "
            "On Saturday in Rahu kalam: wash in cow urine + Gangajal, "
            "dry with blue/grey cloth; consecrate with 'Om Bhraam Bhreem Bhraum Sah "
            "Rahave Namah' × 108; set in silver on middle finger right hand"
        ),
        "classical_citation": (
            "BPHS Ch.86 (Upaaya — Rahu/Ketu remedial section); "
            "Garuda Purana Ch.68 (Gomedha); Mani Mala §10; "
            "Skanda Purana — Rahu Mahatmya; Tantrasara (shadow-graha remedies)"
        ),
        "upagraha_remedy": (
            "Rahu himself is classified as a chaya graha (shadow planet); "
            "propitiate via Durga/Kali (fierce form of Devi) and Saraswati; "
            "Rahu's main deity is Durga — offer sindoor and red hibiscus"
        ),
        "special_remedy": (
            "Donate to hospitals or snake-sanctuaries (Rahu = serpent); "
            "feed stray dogs on Saturdays; "
            "recite Rahu Stotra on Amavasya (new moon) nights; "
            "avoid speculative investments during Rahu dasha if poorly placed; "
            "perform Sarpa Dosha Nivaran puja if natal Rahu afflicts 1st/5th/7th"
        ),
        "best_timing": "Rahu Kalam on Saturday, or at dusk on Amavasya",
        "deity": "Durga (Mahishasura-mardini) / Kali / Saraswati",
        "color": "Smoky Grey / Dark Blue / Black",
        "direction": "Southwest",
        "sacred_tree": "Durva (Cynodon dactylon — Bermuda Grass) / Coconut palm",
    },

    "ketu": {
        "mantra_ids": [
            "ketu_beej_mantra",      # Oṃ srāṃ srīṃ srauṃ saḥ ketave namaḥ
            "ketu_gayatri",          # Ketu Gayatri
            "ketu_stotra_vyasa",     # Navagraha Stotra verse 9
            "ketu_kavach_seed",      # Ketu Kavach
            "rahu_ketu_shanti_mantra", # Combined Rahu-Ketu Shanti (17,000 count for Ketu)
            "ganesha_beej_mantra",   # Ketu's deity is Ganesha / Chitragupta
        ],
        "gemstone": {
            "primary": "Cat's Eye",
            "alternate_name": "Lehsunia / Vaidurya",
            "substitute": ["Tiger's Eye", "Chrysoberyl (pale)", "Tourmaline (green-brown)"],
            "weight_ratti": "3-8",
        },
        "metal": "Silver or Panchdhatu (5-metal alloy)",
        "finger": "Little finger, right hand (or as prescribed by jyotishi)",
        "yantra": "Ketu Yantra",
        "yantra_citation": "Vishnu Dharmottara Purana; Tantrasara §4; Skanda Purana Ketu chapter",
        "fasting_day": "Tuesday (or Thursday per some traditions)",
        "charity": (
            "Grey-brown cloth, mustard, sesame, black blanket on Tuesday; "
            "donate to ascetics, renunciants, or spiritual seekers; "
            "feed dogs and brown/spotted animals"
        ),
        "ritual": (
            "Ganesha puja for Ketu mitigation (Ganesha is Ketu's deity); "
            "recite Ganesha Vandana + Ketu Beej Mantra 17,000×; "
            "offer modak + durva grass at Ganesha temple; "
            "perform Ketu Shanti Homa on Shashti (6th lunar day)"
        ),
        "gemstone_activation": (
            "CAUTION: Cat's Eye must be tested before wearing — seek jyotishi confirmation. "
            "On Tuesday in Ketu hora: wash in honey + Gangajal, "
            "dry with brown/grey cloth; consecrate with 'Om Sraam Sreem Sraum Sah "
            "Ketave Namah' × 108; set in silver on little finger right hand"
        ),
        "classical_citation": (
            "BPHS Ch.86 (Upaaya — Rahu/Ketu remedial section); "
            "Garuda Purana Ch.68 (Vaidurya — Cat's Eye); Mani Mala §11; "
            "Skanda Purana — Ketu Mahatmya; Tantrasara (chaya-graha remedies)"
        ),
        "upagraha_remedy": (
            "Ketu is itself classified as a chaya graha (headless shadow planet); "
            "propitiate via Ganesha (remover of obstacles) + Chitragupta (karmic recorder); "
            "recite Ketu Stotra on Chaturdashi (14th lunar day) nights"
        ),
        "special_remedy": (
            "Donate blankets to renunciants or ascetics; "
            "feed dogs on Tuesdays (Ketu governs dogs); "
            "recite Ganesh Sahasranama to remove past-life karmic blocks (Ketu = past karma); "
            "avoid excessive attachment to outcomes during Ketu dasha; "
            "engage in spiritual practices: meditation, tantra, moksha-oriented disciplines"
        ),
        "best_timing": "Tuesday or Thursday during Ketu hora, or on Chaturdashi (14th lunar day)",
        "deity": "Ganesha / Chitragupta / Indra (some traditions)",
        "color": "Smoky / Ash-Grey / Brown-Grey",
        "direction": "Northeast (shared with Jupiter) or Southwest (shared with Rahu)",
        "sacred_tree": "Kusha (Desmostachya bipinnata — Halfa grass) / Darbha grass",
    },
}

# Required keys that every graha entry must carry (used in validation)
REQUIRED_KEYS = frozenset({
    "mantra_ids",
    "gemstone",
    "metal",
    "finger",
    "yantra",
    "fasting_day",
    "charity",
    "ritual",
    "gemstone_activation",
    "classical_citation",
    "upagraha_remedy",
    "special_remedy",
    "best_timing",
})

REQUIRED_GEMSTONE_KEYS = frozenset({"primary", "substitute", "weight_ratti"})

ALL_GRAHAS = frozenset(REMEDIAL_LIBRARY.keys())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_remedies(graha: str) -> dict:
    """Return the full remedial entry for a graha.

    Args:
        graha: lowercase graha name ('sun', 'moon', 'mars', 'mercury',
               'jupiter', 'venus', 'saturn', 'rahu', 'ketu')

    Returns:
        dict with all remedial fields, or empty dict if graha not found.
    """
    return REMEDIAL_LIBRARY.get(graha.lower(), {})


def get_gemstone_recommendation(graha: str) -> dict:
    """Return gemstone dict for a graha (primary + substitutes + weight).

    Args:
        graha: lowercase graha name

    Returns:
        dict with keys: primary, substitute (list), weight_ratti, alternate_name.
        Empty dict if graha not found.
    """
    entry = get_remedies(graha)
    return entry.get("gemstone", {})


def get_mantra_ids(graha: str) -> list[str]:
    """Return list of mantra IDs (cross-references to mantras.py G33) for a graha.

    Args:
        graha: lowercase graha name

    Returns:
        list of mantra ID strings; empty list if graha not found.
    """
    entry = get_remedies(graha)
    return entry.get("mantra_ids", [])


def get_full_remedy_text(graha: str) -> str:
    """Return a formatted human-readable summary of all remedies for a graha.

    Args:
        graha: lowercase graha name

    Returns:
        Multi-line text string; empty string if graha not found.
    """
    entry = get_remedies(graha)
    if not entry:
        return ""

    gem = entry.get("gemstone", {})
    lines = [
        f"=== REMEDIAL LIBRARY: {graha.upper()} ===",
        "",
        f"Deity        : {entry.get('deity', 'N/A')}",
        f"Direction    : {entry.get('direction', 'N/A')}",
        f"Color        : {entry.get('color', 'N/A')}",
        f"Metal        : {entry.get('metal', 'N/A')}",
        f"Finger       : {entry.get('finger', 'N/A')}",
        f"Fasting Day  : {entry.get('fasting_day', 'N/A')}",
        f"Best Timing  : {entry.get('best_timing', 'N/A')}",
        "",
        "GEMSTONE:",
        f"  Primary    : {gem.get('primary', 'N/A')} ({gem.get('alternate_name', '')})",
        f"  Substitutes: {', '.join(gem.get('substitute', []))}",
        f"  Weight     : {gem.get('weight_ratti', 'N/A')} ratti",
        "",
        "YANTRA:",
        f"  {entry.get('yantra', 'N/A')}",
        f"  Citation: {entry.get('yantra_citation', 'N/A')}",
        "",
        f"MANTRA IDs   : {', '.join(entry.get('mantra_ids', []))}",
        "",
        "CHARITY:",
        f"  {entry.get('charity', 'N/A')}",
        "",
        "RITUAL:",
        f"  {entry.get('ritual', 'N/A')}",
        "",
        "GEMSTONE ACTIVATION:",
        f"  {entry.get('gemstone_activation', 'N/A')}",
        "",
        "UPAGRAHA REMEDY:",
        f"  {entry.get('upagraha_remedy', 'N/A')}",
        "",
        "SPECIAL REMEDY:",
        f"  {entry.get('special_remedy', 'N/A')}",
        "",
        "CLASSICAL CITATIONS:",
        f"  {entry.get('classical_citation', 'N/A')}",
    ]
    return "\n".join(lines)
