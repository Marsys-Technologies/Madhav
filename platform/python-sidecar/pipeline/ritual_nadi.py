"""
ritual_nadi.py — G39 Vedic Ritual Library + G44 Nadi Astrology Lookup Tables
MARSYS-JIS global reference data module.

G39: Per-occasion Vedic ritual structures (Grihya Sutras, BPHS, Dharmashastra)
G44: Nadi astrology tables — D150 amsa, nakshatra-rishi map, KP sublords, Bhrigu yogas

Classical citations: Ashvalayana Grihya Sutra, Paraskara Grihya Sutra, BPHS,
Brihat Jataka, KP Padhdhati (Krishnamurti), Bhrigu Nadi Granthas.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# G39 — VEDIC_RITUAL_LIBRARY
# Per-occasion ritual structures with sankalpa, sequence, mantras, citations
# ---------------------------------------------------------------------------

VEDIC_RITUAL_LIBRARY: dict[str, dict] = {
    "birth": {
        "ritual_name": "Jatakarma Samskara",
        "sankalpa": "Jatasya shishoḥ āyurvardhanārthaṃ medha-sthira-tejaskarārthaṃ jātakarma kariṣye",
        "timing": "At birth or before umbilical cord cutting; ideally at the auspicious moment of birth",
        "occasion_type": "samskara",
        "ritual_sequence": [
            "Sankalpa — father states intent for child's long life and brilliance",
            "Punya-vachanam — recitation of auspicious Vedic verses",
            "Father touches child's tongue with honey and ghee mixed in a gold spoon",
            "Father whispers sacred syllable 'AUM' into child's right ear",
            "Father whispers child's secret (abhisheka) name into child's ear",
            "Recitation of Medha-janana mantras for intellect",
            "Navagraha invocation for planetary blessings",
            "Purnahuti — final oblation into fire",
        ],
        "mantras": [
            "Om Shrischa te Lakshmiścha patnyāv ahorātre pārśve nakṣatrāṇi rūpaṃ...",
            "Medhāṃ me Varuṇo dadātu medhāṃ Devī Sarasvatī",
            "Aum āyuḥ prāṇaṃ prajāṃ paśuṃ kīrtiṃ draviṇaṃ brahmavarcasam...",
        ],
        "classical_citation": "Ashvalayana Grihya Sutra 1.15; Paraskara Grihya Sutra 1.16; BPHS Samskara Adhyaya",
        "astrological_timing": "Lagna in benefic sign, Moon in trikona from natal Moon; avoid Saturdays and inauspicious tithis",
        "notes": "The honey-ghee mixture symbolises sweet speech and radiant intellect; gold is conductor of solar vitality",
    },

    "naming": {
        "ritual_name": "Namakarana Samskara",
        "sankalpa": "Asya shishoḥ nāmadheya-sthāpanārthaṃ namakaraṇa-saṃskāraṃ kariṣye",
        "timing": "10th or 12th day after birth; some traditions allow up to 1 year",
        "occasion_type": "samskara",
        "ritual_sequence": [
            "Punyavachana — purification of house with Vedic verses",
            "Matrika puja — worship of eight mother goddesses",
            "Navagraha puja — planetary invocation",
            "Jatakarma completion if not done at birth",
            "Father whispers chosen name into child's right ear three times",
            "Mother whispers same name into child's left ear",
            "Public announcement of name to assembled family",
            "Brahmin recites nakshatra-based auspicious akshara (letter) for name",
            "Purnahuti and prasad distribution",
        ],
        "mantras": [
            "Aum nāma tvā dadhāmi śreyase saukhyāya āyuṣe balam...",
            "Idam nāma astu te bhadram subham mangalam sadā...",
        ],
        "classical_citation": "Paraskara Grihya Sutra 1.17; Manusmriti 2.30; BPHS",
        "astrological_timing": "Nakshatra-based name: first syllable derived from Moon nakshatra pada at birth",
        "notes": "Name is chosen per nakshatra pada: Ashwini=Chu/Che/Cho/La; tradition varies by region and gotra",
    },

    "annaprashan": {
        "ritual_name": "Annaprashan Samskara (First Solid Food)",
        "sankalpa": "Asya shishoḥ annaprashanārthaṃ prathama-anna-prāśanaṃ kariṣye",
        "timing": "6th month from birth for boys; 5th or 7th month for girls; even months preferred for boys, odd for girls",
        "occasion_type": "samskara",
        "ritual_sequence": [
            "Purification of space and participants",
            "Ganesha puja for removal of obstacles",
            "Navagraha invocation",
            "Preparation of kheer (sweetened rice) or payasam as first food",
            "Father or maternal uncle feeds first morsel with gold spoon",
            "Mantras recited for digestion, strength, and long life",
            "Placing objects before child (pen, soil, money, book) — symbolic choice of destiny",
            "Community feast and blessings",
        ],
        "mantras": [
            "Annāt parisruto rasaṃ brahmaṇā vyapibat kṣatram payaḥ...",
            "Aum idaṃ viṣṇu vichakrame tredhā nidadhe padam...",
        ],
        "classical_citation": "Ashvalayana Grihya Sutra 1.16; Gobhila Grihya Sutra 2.7",
        "astrological_timing": "Muhurta: Moon in upachaya (3/6/10/11) from natal; avoid Rahu kalam and Gulika kalam",
        "notes": "The symbolic object-choice ritual (dashakarma) reveals innate prarabdha tendencies per classical Dharmashastra",
    },

    "thread_ceremony": {
        "ritual_name": "Upanayana Samskara (Sacred Thread / Brahmacharya Initiation)",
        "sankalpa": "Asya kumārasya upanayana-brahmacharya-dīkṣā-grahaṇārthaṃ upanayanaṃ kariṣye",
        "timing": "Boys: 8th year from birth for Brahmin, 11th for Kshatriya, 12th for Vaishya; spring season preferred",
        "occasion_type": "samskara",
        "ritual_sequence": [
            "Pre-ceremony fast and purification (one day)",
            "Shaving of head (mundana)",
            "Bath and wearing of new white dhoti",
            "Guru (father or acharya) gives the Yajnopavita (sacred thread) — three strands symbolising Brahma/Vishnu/Shiva",
            "Gayatri mantra initiation — whispered into right ear by guru",
            "Brahmacharya vow taken before fire",
            "Begging for alms (madhukara) from mother as first act of studentship",
            "Navagraha homa",
            "Savitri japa — 108 recitations of Gayatri",
            "Community blessing and guru-dakshina",
        ],
        "mantras": [
            "Om bhūr bhuvaḥ svaḥ tatsaviturvareṇyaṃ bhargo devasya dhīmahi dhiyo yo naḥ prachodayāt",
            "Yajñopavītaṃ paramaṃ pavitraṃ prajāpater yatsahajam purastāt...",
        ],
        "classical_citation": "Ashvalayana Grihya Sutra 1.19-22; Manusmriti 2.36-44; BPHS",
        "astrological_timing": "Sun in Uttarayana; Moon in Hasta, Ashwini, Pushya, or Revati; avoid Jyeshtha nakshatra",
        "notes": "The three strands of the sacred thread represent the three debts (rinas): to gods (deva), sages (rishi), and ancestors (pitru)",
    },

    "marriage": {
        "ritual_name": "Vivah Samskara (Vedic Marriage)",
        "sankalpa": "Asya varasya kanyāyāścha dharma-artha-kāma-mokṣa-siddhi-arthaṃ vivāhaṃ kariṣye",
        "timing": "Auspicious tithi: Dwitiya, Tritiya, Panchami, Saptami, Dashami, Dwadashi, Trayodashi; Moon in Rohini, Hasta, Mrigashira, Magha preferred",
        "occasion_type": "samskara",
        "ritual_sequence": [
            "Vagdana — formal betrothal agreement between families",
            "Ganesh puja and Navagraha homa",
            "Kashi yatra — groom's mock pilgrimage interrupted by bride's father",
            "Vara puja — worship of groom as Vishnu by bride's family",
            "Madhuparka — honey-milk-curd mixture offered to groom",
            "Kanyadana — giving away of bride by father with Vedic mantras",
            "Vivah homa — sacred fire established",
            "Pani-grahanam — groom takes bride's hand with Vedic mantra",
            "Saptapadi — seven steps around sacred fire (each step = one vow)",
            "Ashmarohana — bride steps on stone for steadfastness",
            "Laja homa — parched grain offered into fire by couple together",
            "Arundhati-nakshatra darshan — couple views the Arundhati star",
            "Graha pravesh — couple enters groom's home",
        ],
        "mantras": [
            "Imāṃ tvamindra mīḍhvas tubhyaṃ śinvaṃ nyūhathur manasaspatim...",
            "Saptapadī: Ekaṃ iṣe — may we walk together for food; Dve ūrje — for strength...",
            "Somāya dattā Gandharvo'grahīt Agniṃ Gandharvāt...",
        ],
        "classical_citation": "Rigveda Khilani; Ashvalayana Grihya Sutra 1.6-8; BPHS Vivah Adhyaya; Manusmriti 3.27-44",
        "astrological_timing": "Avoid Venus/Jupiter combustion; groom's Ashtama-rashi-shuddi; muhurta chart lagna must be strong",
        "notes": "Saptapadi creates the legal-spiritual bond; each step corresponds to one of seven planets in Vedic cosmology",
    },

    "griha_pravesh": {
        "ritual_name": "Griha Pravesh (Vastu Puja / Housewarming)",
        "sankalpa": "Asya nūtana-gṛhasya pravesha-vāstoṣpate-prīti-arthaṃ gṛha-praveśaṃ kariṣye",
        "timing": "Uttarayana preferred; auspicious lunar day; Rohini, Hasta, Mrigashira, Pushya, Revati nakshatras; avoid Ashlesha, Jyeshtha, Moola, Ardra",
        "occasion_type": "seasonal",
        "ritual_sequence": [
            "Kalasha sthapana — establishing sacred water pot at entrance",
            "Vastu Purusha puja — worship of presiding deity of the building",
            "Pancha-bhuta shuddhi — purification of five elements in each direction",
            "Vastu homa — oblations to Vastu Purusha with specific samidhā (firewood)",
            "Cow and calf enter home first (if available) — auspicious symbol",
            "Ganesha and Lakshmi invocation at threshold",
            "Boiling of milk until it overflows — symbol of abundance",
            "Pradakshina (circumambulation) of fire three times",
            "Purnahuti — final oblation",
            "Feeding of Brahmins and distribution of prasad",
        ],
        "mantras": [
            "Vāstoṣpate pratijaanīhy asmatsvāveśo anamīvo bhavā naḥ...",
            "Om śāntiḥ pratiṣṭhā hi amṛtaṃ hi śāntiḥ...",
            "Dyu-mā-dya mānaṃ pṛthvī-mā nujānām...",
        ],
        "classical_citation": "Rigveda 7.54 (Vastu hymn); Vishvakarma Purana; BPHS Graha Pravesh Adhyaya; Manasara Vastu Shastra",
        "astrological_timing": "Lagna lord strong; no malefics in 4th house of muhurta chart; Jupiter or Venus in kendra",
        "notes": "Vastu Purusha mandala divides the plot into 64 or 81 squares; each zone has a presiding deity per Vastu Shastra",
    },

    "death_rites": {
        "ritual_name": "Antyeshti Samskara (Last Rites + Shraddha)",
        "sankalpa": "Asya pretasya mukti-prāptyarthaṃ sadgati-arthaṃ antyeṣṭiṃ kariṣye",
        "timing": "Cremation within one day (ideally before sunset); shraddha on specific tithis thereafter",
        "occasion_type": "ancestor",
        "ritual_sequence": [
            "Jalasnanam — ritual bath of the body",
            "Pavitrikaran — purification with Ganga water and tulasi",
            "Shroud preparation — white cloth for men, white or red for women",
            "Antim darshan — final viewing by family",
            "Procession to cremation ground with Vedic chanting",
            "Chitagni — eldest son or closest male relative lights pyre",
            "Kapalkriya — symbolic breaking of the skull to release the soul",
            "Ashti sanchayana — collecting ashes on 3rd day",
            "Asthi visarjan — immersing ashes in sacred river (Ganga preferred)",
            "Pinda daan — rice-ball offerings for 13 days",
            "Ekoddishtha shraddha — individual shraddha on 13th day",
            "Sapindikarana — merging soul with pitrus on 1 year anniversary",
        ],
        "mantras": [
            "Aum namo Brahmane namo'stu Agnaye...",
            "Om tryambakaṃ yajāmahe sugandhiṃ puṣṭivardhanam urvārukamiva bandhanān...",
            "Agner varṇo jyotiṣā saṃviśasva...",
        ],
        "classical_citation": "Rigveda 10.14 (Yama hymns); 10.16-18 (cremation hymns); Garuda Purana; BPHS; Ashvalayana Grihya Sutra 4.1",
        "astrological_timing": "Pinda daan on Krishna Ashtami, Amavasya; Pitru Paksha Shraddha on tithi of death",
        "notes": "Sapindikarana merges the newly departed with the pitru-loka collective; after this the soul is no longer treated as individual preta",
    },

    "new_year": {
        "ritual_name": "Ugadi / Gudi Padwa / Vishu Puja (Regional New Year)",
        "sankalpa": "Nava-samvatsare asmin śubha-muhūrte Brahmā-rūpasya kāla-devasya pūjāṃ kariṣye",
        "timing": "Ugadi: Chaitra Shukla Pratipada; Gudi Padwa: same; Vishu: Mesha Sankranti (solar new year)",
        "occasion_type": "seasonal",
        "ritual_sequence": [
            "Prabhata snanam — ritual bath at sunrise",
            "Panchanga shravanam — hearing of the new year's astrological almanac by a jyotishi",
            "Gudi/flag hoisting — bamboo with copper pot symbolising victory (Gudi Padwa specific)",
            "Bevu-bella (neem + jaggery) prasad consumption — symbolises mixed fortunes of the year",
            "Navagraha puja",
            "Brahmin felicitation with dakshina",
            "Pachadi preparation (six-taste dish with neem, mango, coconut, jaggery, tamarind, chilli)",
            "Family feast with new clothes",
            "Community bhajan and temple visit",
        ],
        "mantras": [
            "Om namo Brahmaṇe dhāraṇe pṛthivī tvaṃ dhārayase...",
            "Saṃvatsare śubhe sthite mangalaṃ bhavatu naḥ...",
        ],
        "classical_citation": "Brahma Purana; Skanda Purana; regional Dharmashastra texts; BPHS Samvatsara Phala",
        "astrological_timing": "Panchanga of the new Samvatsara determines the year's ruling planet (Varsha-adhipati = weekday lord of Pratipada)",
        "notes": "Varsha-adhipati (year-lord) governs the general trend of the year; assessed via panchadhikari (5 rulers) in classical Muhurta",
    },

    "navratri": {
        "ritual_name": "Navratri Devi Aradhana (Nine-Night Goddess Worship)",
        "sankalpa": "Navadurgā-prītyarthaṃ śakti-prapti-arthaṃ navadina-pūjāṃ kariṣye",
        "timing": "Chaitra Shukla Pratipada to Navami (spring); Ashwin Shukla Pratipada to Navami (autumn, most important)",
        "occasion_type": "deity",
        "ritual_sequence": [
            "Day 1 (Pratipada) — Kalasha sthapana; Shailaputri puja; sowing of barley seeds (navaratri jyot)",
            "Day 2 (Dwitiya) — Brahmacharini puja; fasting continuation",
            "Day 3 (Tritiya) — Chandraghanta puja",
            "Day 4 (Chaturthi) — Kushmanda puja",
            "Day 5 (Panchami) — Skandamata puja",
            "Day 6 (Shashti) — Katyayani puja",
            "Day 7 (Saptami) — Kalaratri puja; Saraswati-avahan (books, instruments placed before goddess)",
            "Day 8 (Ashtami) — Mahagauri puja; Kanya puja (nine girls worshipped as nine Devis); havan",
            "Day 9 (Navami) — Siddhidatri puja; Maha-puja; Purnahuti; Vijayadashami preparation",
            "Day 10 (Vijaya Dashami) — Aparajita puja; Shami tree worship; weapon puja (Ayudha puja); Saraswati visarjan",
        ],
        "mantras": [
            "Yā devī sarvabhūteṣu śaktirūpeṇa sansthitā namastasyai namastasyai namastasyai namo namaḥ",
            "Sarvamaṅgala māṅgalye śive sarvārthasādhike śaraṇye tryambake gauri nārāyaṇi namo'stute",
            "Om Aim Hreem Kleem Chamundayai Vichche (Navarna mantra)",
        ],
        "classical_citation": "Devi Mahatmyam (Markandeya Purana chapters 81-93); Devi Bhagavata Purana; Kalika Purana",
        "astrological_timing": "Moon transiting Ashwini to Ashlesha during Ashwin Navratri — each nakshatra corresponds to one of nine Devis",
        "notes": "Navarna mantra (9 syllables) is core to Shakta tantra; corresponds to 9 chakras in Srichakra; Navratri mirrors the Sun's strength in the two ayanas",
    },

    "shradh": {
        "ritual_name": "Pitru Paksha Shraddha (Ancestor Propitiation)",
        "sankalpa": "Asya mama pitṛ-mātāmaha-prapitāmahasya... tṛpti-arthaṃ śrāddhaṃ kariṣye",
        "timing": "Pitru Paksha: Bhadrapada Purnima to Sarva-Pitru Amavasya (15 days); also tithi of death, Amavasya, Mahalaya",
        "occasion_type": "ancestor",
        "ritual_sequence": [
            "Sankalpam — naming of all three generations of ancestors (father, grandfather, great-grandfather; same for mother's side)",
            "Invitation to Brahmins (representing Vishvedeva and Pitrus)",
            "Purification — Brahmin's feet washed, given seat",
            "Offering of sesame seeds (tila) mixed with water — most essential element of shraddha",
            "Pinda daan — three rice balls (pindas) for father, grandfather, great-grandfather",
            "Go-gras (offering to cow)",
            "Kaga-bali (offering to crow — crow represents pitrus visiting)",
            "Feeding of Brahmin with complete meal",
            "Dakshina to Brahmin",
            "Tarpana — water libations with sesame, kusha grass, while facing south",
        ],
        "mantras": [
            "Om pitṛbhyaḥ svāhā pitṛbhyaḥ svadhā namas tarpayāmi...",
            "Namas tarpayāmi mātāmahān tarpayāmi prapitāmahān tarpayāmi...",
            "Ye ke chāsmatkule jātā aputrā gotra-saṃbhavāḥ... tebhyaḥ piṇḍaṃ dadāmi...",
        ],
        "classical_citation": "Garuda Purana; Vishnu Purana 3.14-16; Manusmriti 3.122-286; BPHS Pitru Karaka Adhyaya",
        "astrological_timing": "Shraddha on exact tithi of death yields maximum merit; Mahalaya Amavasya is universal — benefits all ancestors regardless of tithi",
        "notes": "Crow as pitru-messenger is a pan-Indian belief; if a crow eats the pinda it signals the ancestor's acceptance; Sun in Kanya rashi during Pitru Paksha is astrologically significant",
    },

    "satyanarayan_puja": {
        "ritual_name": "Satyanarayan Vrata Puja",
        "sankalpa": "Śrī-Satyanārāyaṇa-pūjā-vratasya purataḥ saṅkalpam kariṣye",
        "timing": "Purnima (full moon), Ekadashi, or any auspicious day; monthly or on special occasions",
        "occasion_type": "deity",
        "ritual_sequence": [
            "Kalasha sthapana with mango leaves and coconut",
            "Ganesha puja",
            "Navagraha puja",
            "Satyanarayan's image or yantra installed on altar",
            "Panchamrita abhisheka (milk, curd, honey, ghee, sugar)",
            "Pushpa puja with yellow flowers",
            "Dhupa, Dipa, Naivedya offerings",
            "Reading of Satyanarayan Katha (five chapters from Skanda Purana)",
            "Aarti",
            "Distribution of prasad (panchamrita + charnamrit + sheera/halwa)",
        ],
        "mantras": [
            "Om namo bhagavate Vāsudevāya...",
            "Śrī Satyanārāyaṇa devāya namas...",
        ],
        "classical_citation": "Skanda Purana — Revakhanda; regional Vaishnava Dharmashastra traditions",
        "astrological_timing": "Purnima is universally auspicious; Ekadashi ruled by Vishnu; avoid Amavasya and inauspicious tithis",
        "notes": "Prasad (sheera / banana + panchamrita) must not be refused; Katha narrates five stories illustrating consequences of vow observance and violation",
    },

    "vastu_shanti": {
        "ritual_name": "Vastu Shanti Puja",
        "sankalpa": "Asya gṛhasya vāstu-doṣa-praśamana-arthaṃ vāstu-śāntiṃ kariṣye",
        "timing": "Before or after major construction; when moving into new home; when structural changes made",
        "occasion_type": "seasonal",
        "ritual_sequence": [
            "Brahma sthana puja (center of building)",
            "Dig-devata puja — 8 directional deities worshipped at cardinal and intercardinal points",
            "Vastu Purusha mandala activation (81-square or 64-square grid)",
            "Pancha-bhuta shuddhi of the plot",
            "Navagraha homa",
            "Vastu homa with specific samidhā for each zone defect",
            "Naga puja if plot has serpent-energy imbalance",
            "Brahmin bhojana",
            "Copper plate or yantra installed at Brahma sthana",
        ],
        "mantras": [
            "Vāstoṣpate śagmayā saṃsadā te sakṣīmahi ranvayā gātuvittaye...",
            "Om śāntiḥ śāntiḥ śāntiḥ...",
        ],
        "classical_citation": "Atharvaveda 9.3 (building hymn); Vishvakarma Purana; Manasara; Mayamata",
        "astrological_timing": "Shanti puja: Moon in Hasta, Rohini, Pushya; Sun in fixed sign (Taurus/Leo/Scorpio/Aquarius) for stability",
        "notes": "Vastu Purusha lies with head in northeast — never place kitchen, toilet, or heavy structures in NE per classical Vastu",
    },
}


def get_ritual(occasion: str) -> dict:
    """Return ritual data for a given occasion key.

    Args:
        occasion: Occasion key (e.g. 'birth', 'marriage', 'navratri')

    Returns:
        dict with full ritual data, or empty dict if not found.
    """
    return VEDIC_RITUAL_LIBRARY.get(occasion.lower(), {})


def list_occasions() -> list[str]:
    """Return list of all available occasion keys."""
    return list(VEDIC_RITUAL_LIBRARY.keys())


def get_ritual_by_type(occasion_type: str) -> list[dict]:
    """Return all rituals matching a given occasion_type.

    Args:
        occasion_type: One of 'samskara', 'deity', 'ancestor', 'seasonal'

    Returns:
        List of dicts, each containing the occasion key plus full ritual data.
    """
    result = []
    for key, data in VEDIC_RITUAL_LIBRARY.items():
        if data.get("occasion_type", "").lower() == occasion_type.lower():
            result.append({"occasion": key, **data})
    return result


# ---------------------------------------------------------------------------
# G44 — NADI_LOOKUP_TABLES
# Nadi astrology: nakshatra-rishi mapping, KP sublords, Bhrigu yoga rules
# ---------------------------------------------------------------------------

# 27 Rishis cycling in groups of 9 across the 27 nakshatras
RISHI_NAMES: list[str] = [
    "Vasishtha", "Atri", "Bharadwaja", "Vishwamitra", "Gautama",
    "Jamadagni", "Kashyapa", "Agastya", "Kaundinya",
    "Shaunaka", "Vatsa", "Moudgalya", "Kaushika", "Galava",
    "Bhrigu", "Angiras", "Pulastya", "Pulaha", "Kratu",
    "Daksha", "Prajapati", "Brahma", "Vishnu", "Shiva",
    "Shakti", "Ganesha", "Skanda",
]

# Nakshatra-to-Rishi mapping: 27 nakshatras, repeating the 9 primary rishis
# (Vasishtha, Atri, Bharadwaja, Vishwamitra, Gautama, Jamadagni, Kashyapa,
#  Agastya, Kaundinya) across three cycles of 9
NADI_NAKSHATRA_RISHI: dict[int, str] = {
    # Cycle 1 (nakshatras 1-9)
    1: "Vasishtha",    # Ashwini
    2: "Atri",         # Bharani
    3: "Bharadwaja",   # Krittika
    4: "Vishwamitra",  # Rohini
    5: "Gautama",      # Mrigashira
    6: "Jamadagni",    # Ardra
    7: "Kashyapa",     # Punarvasu
    8: "Agastya",      # Pushya
    9: "Kaundinya",    # Ashlesha
    # Cycle 2 (nakshatras 10-18)
    10: "Vasishtha",   # Magha
    11: "Atri",        # Purva Phalguni
    12: "Bharadwaja",  # Uttara Phalguni
    13: "Vishwamitra", # Hasta
    14: "Gautama",     # Chitra
    15: "Jamadagni",   # Swati
    16: "Kashyapa",    # Vishakha
    17: "Agastya",     # Anuradha
    18: "Kaundinya",   # Jyeshtha
    # Cycle 3 (nakshatras 19-27)
    19: "Vasishtha",   # Moola
    20: "Atri",        # Purva Ashadha
    21: "Bharadwaja",  # Uttara Ashadha
    22: "Vishwamitra", # Shravana
    23: "Gautama",     # Dhanishtha
    24: "Jamadagni",   # Shatabhisha
    25: "Kashyapa",    # Purva Bhadrapada
    26: "Agastya",     # Uttara Bhadrapada
    27: "Kaundinya",   # Revati
}

# KP sub-lord table: each nakshatra has 9 sub-lords in Vimshottari sequence
# Each nakshatra begins with its dasha lord, then continues the standard
# Vimshottari sequence: Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury
# Nakshatra dasha lords (standard KP):
# 1 Ashwini=Ketu, 2 Bharani=Venus, 3 Krittika=Sun, 4 Rohini=Moon, 5 Mrigashira=Mars,
# 6 Ardra=Rahu, 7 Punarvasu=Jupiter, 8 Pushya=Saturn, 9 Ashlesha=Mercury
# (repeating for nakshatras 10-27)
_VIMSHOTTARI_SEQ = ["ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury"]
_NAKSHATRA_DASHA_LORDS = {
    1: "ketu", 2: "venus", 3: "sun", 4: "moon", 5: "mars",
    6: "rahu", 7: "jupiter", 8: "saturn", 9: "mercury",
    10: "ketu", 11: "venus", 12: "sun", 13: "moon", 14: "mars",
    15: "rahu", 16: "jupiter", 17: "saturn", 18: "mercury",
    19: "ketu", 20: "venus", 21: "sun", 22: "moon", 23: "mars",
    24: "rahu", 25: "jupiter", 26: "saturn", 27: "mercury",
}

def _build_kp_sublords() -> dict[int, dict[int, str]]:
    """Build KP sublord table for all 27 nakshatras × 9 sub-positions."""
    table: dict[int, dict[int, str]] = {}
    for nakshatra in range(1, 28):
        dasha_lord = _NAKSHATRA_DASHA_LORDS[nakshatra]
        start_idx = _VIMSHOTTARI_SEQ.index(dasha_lord)
        subs: dict[int, str] = {}
        for sub_pos in range(1, 10):
            subs[sub_pos] = _VIMSHOTTARI_SEQ[(start_idx + sub_pos - 1) % 9]
        table[nakshatra] = subs
    return table

KP_NADI_SUBLORDS: dict[int, dict[int, str]] = _build_kp_sublords()

# D150 amsa table: each nakshatra maps to a primary rishi for Nadi amsa readings
# In D150 (each degree = 150/12 = 12.5 parts per sign), the Nadi technique
# maps sub-lord positions to specific rishis for leaf-reading correlation
NADI_AMSA_TABLE: dict[str, dict] = {
    nakshatra_name: {
        "nakshatra_number": num,
        "primary_rishi": NADI_NAKSHATRA_RISHI[num],
        "d150_parts": 150,  # D150 divides each sign into 150 parts (0.2° each)
        "nadi_classification": "adi" if num % 3 == 1 else ("madhya" if num % 3 == 2 else "antya"),
    }
    for num, nakshatra_name in {
        1: "Ashwini", 2: "Bharani", 3: "Krittika", 4: "Rohini", 5: "Mrigashira",
        6: "Ardra", 7: "Punarvasu", 8: "Pushya", 9: "Ashlesha", 10: "Magha",
        11: "Purva_Phalguni", 12: "Uttara_Phalguni", 13: "Hasta", 14: "Chitra",
        15: "Swati", 16: "Vishakha", 17: "Anuradha", 18: "Jyeshtha",
        19: "Moola", 20: "Purva_Ashadha", 21: "Uttara_Ashadha", 22: "Shravana",
        23: "Dhanishtha", 24: "Shatabhisha", 25: "Purva_Bhadrapada",
        26: "Uttara_Bhadrapada", 27: "Revati",
    }.items()
}

# Bhrigu-Nadi yoga rules — key prediction principles from Bhrigu Nadi tradition
BHRIGU_NADI_YOGAS: list[dict] = [
    {
        "yoga_name": "Sun-Moon-Jupiter conjunction or mutual aspect",
        "prediction": "High spirituality, learning, and dharmic inclinations; fame in spiritual or intellectual fields",
        "houses_involved": "Any — but especially 1st, 5th, 9th",
        "activation": "During Jupiter, Sun, or Moon dashas/antardashas",
        "source": "Bhrigu Nadi",
        "classical_citation": "Bhrigu Samhita — Surya-Chandra-Guru yoga adhyaya",
    },
    {
        "yoga_name": "Sun-Saturn opposition or conjunction",
        "prediction": "Father-son conflict; obstacles in government service or career; chronic health issues related to bones and heart; possibility of delayed success",
        "houses_involved": "1-7 axis or 10th house involvement",
        "activation": "Saturn dasha; Sun-Saturn antardasha",
        "source": "Bhrigu Nadi",
        "classical_citation": "Bhrigu Nadi tradition; Brihat Jataka corroborating",
    },
    {
        "yoga_name": "Moon-Venus conjunction",
        "prediction": "Artistic talents, refined aesthetic sense, luxurious nature, success in entertainment, beauty, or hospitality industries",
        "houses_involved": "1st, 4th, 7th, or 12th especially potent",
        "activation": "Venus or Moon dashas",
        "source": "Bhrigu Nadi",
        "classical_citation": "Bhrigu Samhita; Saravali 18.12",
    },
    {
        "yoga_name": "Jupiter-Saturn conjunction (Brahma-Shani yoga)",
        "prediction": "Philosophical nature; success comes after delay; good for law, judiciary, or long-term projects; wisdom earned through suffering",
        "houses_involved": "9th, 10th, or 1st",
        "activation": "Jupiter-Saturn period; Saturn-Jupiter antardasha",
        "source": "Bhrigu Nadi",
        "classical_citation": "Bhrigu Nadi; BPHS Yoga Phala Adhyaya",
    },
    {
        "yoga_name": "Mars-Saturn conjunction or aspect",
        "prediction": "Accidents, surgical interventions, or injuries to limbs; aggressive temperament with sudden outbursts; indicates disruptions in property matters",
        "houses_involved": "4th, 8th, or Lagna especially",
        "activation": "Mars-Saturn or Saturn-Mars periods",
        "source": "Bhrigu Nadi",
        "classical_citation": "Bhrigu Samhita; Phaladeepika 18",
    },
    {
        "yoga_name": "Mercury-Jupiter conjunction or mutual aspect",
        "prediction": "Exceptional intelligence, scholarly ability, mastery of language; success in education, writing, law, or commerce",
        "houses_involved": "1st, 3rd, 5th, 9th ideal",
        "activation": "Mercury or Jupiter dashas",
        "source": "Bhrigu Nadi",
        "classical_citation": "Bhrigu Nadi; Brihat Parashara Hora Shastra",
    },
    {
        "yoga_name": "Rahu in 10th house (Bhrigu rule)",
        "prediction": "Unconventional career or foreign connections in career; rise through technical, scientific, or taboo fields; fame often comes suddenly",
        "houses_involved": "10th house with or without aspect from Saturn",
        "activation": "Rahu dasha or Rahu-ruled sub-periods",
        "source": "Bhrigu Nadi",
        "classical_citation": "Bhrigu Samhita Rahu Phala; Phaladeepika",
    },
    {
        "yoga_name": "Moon-Saturn conjunction or aspect",
        "prediction": "Melancholy, separation from mother or motherland, chronic emotional burdens; also produces perseverance and detachment; Yoga for renunciation",
        "houses_involved": "4th, 12th, or Moon in Capricorn/Aquarius (Saturn's signs)",
        "activation": "Saturn-Moon or Moon-Saturn periods",
        "source": "Bhrigu Nadi",
        "classical_citation": "Bhrigu Nadi; Hora Ratnam (Balabhadra)",
    },
    {
        "yoga_name": "Venus-Ketu conjunction",
        "prediction": "Detachment from worldly pleasures despite strong sensory nature; creative genius with mystical or spiritual orientation; unusual relationships",
        "houses_involved": "7th or 12th especially",
        "activation": "Venus-Ketu or Ketu-Venus period",
        "source": "Bhrigu Nadi",
        "classical_citation": "Bhrigu Samhita; Jaimini Sutras (Ketu = moksha karaka corroborating)",
    },
    {
        "yoga_name": "Sun-Rahu conjunction (Grahan yoga)",
        "prediction": "Conflict with authority figures and father; eclipse of ego leading to transformation; politics or foreign affairs connection; unconventional leadership",
        "houses_involved": "1st, 10th, or 5th most significant",
        "activation": "Sun-Rahu or Rahu-Sun sub-period; Solar eclipses triggering natal position",
        "source": "Bhrigu Nadi",
        "classical_citation": "Bhrigu Nadi; Brihat Jataka eclipse yoga commentary",
    },
    {
        "yoga_name": "Jupiter-Venus opposition (Guru-Shukra Vipareeta)",
        "prediction": "Conflict between dharma and desire; brilliance in creative-spiritual synthesis; tension between teacher and beloved archetypes; possible excess in pleasures",
        "houses_involved": "1-7 axis or 5-11 axis",
        "activation": "Jupiter-Venus or Venus-Jupiter overlap periods",
        "source": "Bhrigu Nadi",
        "classical_citation": "Bhrigu Samhita; Phaladeepika Guru-Shukra chapter",
    },
    {
        "yoga_name": "Mars-Rahu conjunction (Angarak yoga)",
        "prediction": "Explosive temperament, impulsive actions, danger of accidents or explosions; powerful drive that can be channelled into military, sports, or engineering",
        "houses_involved": "Especially dangerous in 1st, 4th, 7th, 8th, 12th",
        "activation": "Mars or Rahu dashas; Mars transiting natal Rahu or vice versa",
        "source": "Bhrigu Nadi",
        "classical_citation": "Bhrigu Nadi tradition; Phaladeepika Angarak yoga",
    },
]


def get_nadi_rishi(nakshatra: int) -> str:
    """Return the primary Nadi rishi for a given nakshatra number (1-27).

    The 9 primary rishis (Vasishtha through Kaundinya) repeat across
    three cycles of 9 nakshatras each.

    Args:
        nakshatra: Integer 1-27

    Returns:
        Rishi name string.

    Raises:
        ValueError: if nakshatra is outside 1-27 range.
    """
    if not 1 <= nakshatra <= 27:
        raise ValueError(f"nakshatra must be between 1 and 27, got {nakshatra}")
    return NADI_NAKSHATRA_RISHI[nakshatra]


def get_kp_sublord(nakshatra: int, sub_position: int) -> str:
    """Return the KP sub-lord planet for a given nakshatra and sub-position.

    Each nakshatra has 9 sub-lords in the Vimshottari sequence starting
    from the nakshatra's own dasha lord.

    Args:
        nakshatra: Integer 1-27
        sub_position: Integer 1-9 (1 = start of nakshatra, 9 = end)

    Returns:
        Planet name string (e.g. 'ketu', 'venus', 'sun', etc.)

    Raises:
        ValueError: if either argument is out of range.
    """
    if not 1 <= nakshatra <= 27:
        raise ValueError(f"nakshatra must be between 1 and 27, got {nakshatra}")
    if not 1 <= sub_position <= 9:
        raise ValueError(f"sub_position must be between 1 and 9, got {sub_position}")
    return KP_NADI_SUBLORDS[nakshatra][sub_position]


def list_bhrigu_yogas() -> list[dict]:
    """Return the full list of Bhrigu-Nadi yoga rules."""
    return BHRIGU_NADI_YOGAS
