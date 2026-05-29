"""
G40 — CAREER_MAPPING: classical professions per graha (BPHS + Phaladeepika)
G45 — AYURVEDA_MAPPING: dosha/body/disease classical mappings
Sources: BPHS Adhyaya 81-83, Phaladeepika Ch 8; Ashtanga Hridayam Sutrasthana
"""

# ---------------------------------------------------------------------------
# G40 — CAREER MAPPING
# ---------------------------------------------------------------------------

CAREER_MAPPING = {
    'sun': {
        'professions': [
            'government official', 'king/ruler', 'politician', 'physician',
            'gemologist', 'gold dealer', 'wool trader', 'administrator',
            'treasury official', 'public servant',
        ],
        'significations': ['authority', 'government', 'medicine', 'leadership', 'father'],
        'industry': ['government', 'healthcare', 'mining', 'energy'],
        'bphs_chapter': '81-83',
        'classical_citation': 'BPHS Adhyaya 82, Phaladeepika Ch 8',
    },
    'moon': {
        'professions': [
            'nurse', 'water trader', 'pearl dealer', 'silver dealer', 'cloth dealer',
            'farmer', 'dairy worker', 'sailor', 'traveler', 'midwife',
            'hotel/hospitality', 'food industry',
        ],
        'significations': ['nurturing', 'liquids', 'public', 'travel', 'mother'],
        'industry': ['agriculture', 'dairy', 'shipping', 'hospitality', 'textiles'],
        'bphs_chapter': '81-83',
        'classical_citation': 'BPHS Adhyaya 82, Phaladeepika Ch 8',
    },
    'mars': {
        'professions': [
            'soldier', 'military officer', 'police officer', 'surgeon',
            'engineer', 'fire service', 'real estate agent', 'metal trader',
            'chemist', 'butcher', 'weapons manufacturer',
        ],
        'significations': ['courage', 'fire', 'weapons', 'blood', 'energy'],
        'industry': ['military', 'defense', 'construction', 'metals', 'surgery'],
        'bphs_chapter': '81-83',
        'classical_citation': 'BPHS Adhyaya 82, Phaladeepika Ch 8',
    },
    'mercury': {
        'professions': [
            'accountant', 'writer', 'astrologer', 'teacher', 'broker',
            'printer', 'IT professional', 'software developer', 'journalist',
            'mathematician', 'translator', 'merchant', 'communicator',
        ],
        'significations': ['intelligence', 'communication', 'trade', 'learning', 'analysis'],
        'industry': ['education', 'finance', 'publishing', 'technology', 'trade'],
        'bphs_chapter': '81-83',
        'classical_citation': 'BPHS Adhyaya 82, Phaladeepika Ch 8',
    },
    'jupiter': {
        'professions': [
            'judge', 'lawyer', 'priest', 'teacher', 'professor', 'banker',
            'financial advisor', 'theologian', 'philosopher', 'spiritual guide',
            'counselor', 'charity worker',
        ],
        'significations': ['wisdom', 'dharma', 'wealth', 'religion', 'children'],
        'industry': ['law', 'religion', 'banking', 'education', 'philosophy'],
        'bphs_chapter': '81-83',
        'classical_citation': 'BPHS Adhyaya 82, Phaladeepika Ch 8',
    },
    'venus': {
        'professions': [
            'artist', 'designer', 'musician', 'luxury goods dealer', 'fashion designer',
            'beauty professional', 'entertainer', 'diplomat', 'perfumer',
            'jeweler', 'film/media', 'hospitality',
        ],
        'significations': ['beauty', 'luxury', 'pleasure', 'arts', 'relationships'],
        'industry': ['arts', 'fashion', 'entertainment', 'diplomacy', 'luxury'],
        'bphs_chapter': '81-83',
        'classical_citation': 'BPHS Adhyaya 82, Phaladeepika Ch 8',
    },
    'saturn': {
        'professions': [
            'laborer', 'miner', 'oil industry worker', 'construction worker',
            'antiques dealer', 'leather worker', 'farmer', 'servant',
            'ascetic', 'undertaker', 'waste management',
        ],
        'significations': ['discipline', 'service', 'karma', 'masses', 'delay'],
        'industry': ['mining', 'oil', 'construction', 'agriculture', 'waste'],
        'bphs_chapter': '81-83',
        'classical_citation': 'BPHS Adhyaya 82, Phaladeepika Ch 8',
    },
    'rahu': {
        'professions': [
            'researcher', 'aviation professional', 'technology specialist',
            'foreign trade professional', 'spy/intelligence', 'chemist',
            'drug industry', 'unconventional healer', 'electrician',
            'digital media', 'cryptocurrency',
        ],
        'significations': ['illusion', 'foreign', 'unconventional', 'obsession', 'amplification'],
        'industry': ['technology', 'aviation', 'pharmaceuticals', 'foreign trade', 'research'],
        'bphs_chapter': '81-83',
        'classical_citation': 'BPHS Adhyaya 82, Phaladeepika Ch 8',
    },
    'ketu': {
        'professions': [
            'occultist', 'researcher', 'spiritual teacher', 'moksha guide',
            'surgeon combined with spirituality', 'healer', 'mystic',
            'astrologer', 'tantric', 'veterinarian', 'toxicologist',
        ],
        'significations': ['liberation', 'spirituality', 'mysticism', 'past life', 'dissolution'],
        'industry': ['occult', 'spirituality', 'research', 'medicine', 'mysticism'],
        'bphs_chapter': '81-83',
        'classical_citation': 'BPHS Adhyaya 82, Phaladeepika Ch 8',
    },
}

# House-level career significations
HOUSE_CAREER = {
    1: 'self, appearance, personality, overall constitution affecting career',
    2: 'earned income, family wealth, speech, accumulated resources',
    3: 'skills, communication, self-effort, younger siblings, courage',
    4: 'real estate, vehicles, education, mother, domestic matters',
    5: 'creativity, speculation, education, intelligence, children',
    6: 'service, employment, competition, enemies, health, daily work',
    7: 'business partnerships, foreign trade, spouse, public dealings',
    8: 'transformation, occult, legacy, research, inheritance, hidden matters',
    9: 'dharma, father, higher education, luck, religious authority',
    10: 'primary career house, government, public standing, profession, status, reputation',
    11: 'gains, income, large organizations, social networks, elder siblings',
    12: 'foreign lands, expenses, moksha, isolated service, hospitals',
}


# ---------------------------------------------------------------------------
# G40 — Public API
# ---------------------------------------------------------------------------

def get_career_by_graha(graha: str) -> dict:
    """Return full career dict for a graha. Returns empty dict for unknown graha."""
    return CAREER_MAPPING.get(graha.lower(), {})


def get_professions_by_graha(graha: str) -> list:
    """Return list of classical professions for a graha."""
    entry = CAREER_MAPPING.get(graha.lower(), {})
    return entry.get('professions', [])


def get_house_career_signification(house: int) -> str:
    """Return career signification for a given house number (1–12)."""
    return HOUSE_CAREER.get(house, '')


# ---------------------------------------------------------------------------
# G45 — AYURVEDA MAPPING
# ---------------------------------------------------------------------------

DOSHA_BY_SIGN = {
    'aries':       {'primary_dosha': 'pitta',       'secondary_dosha': None},
    'taurus':      {'primary_dosha': 'kapha',       'secondary_dosha': None},
    'gemini':      {'primary_dosha': 'vata',        'secondary_dosha': None},
    'cancer':      {'primary_dosha': 'kapha',       'secondary_dosha': 'pitta'},
    'leo':         {'primary_dosha': 'pitta',       'secondary_dosha': None},
    'virgo':       {'primary_dosha': 'vata',        'secondary_dosha': 'kapha'},
    'libra':       {'primary_dosha': 'vata',        'secondary_dosha': None},
    'scorpio':     {'primary_dosha': 'kapha',       'secondary_dosha': 'pitta'},
    'sagittarius': {'primary_dosha': 'pitta',       'secondary_dosha': 'vata'},
    'capricorn':   {'primary_dosha': 'vata',        'secondary_dosha': 'kapha'},
    'aquarius':    {'primary_dosha': 'vata',        'secondary_dosha': None},
    'pisces':      {'primary_dosha': 'kapha',       'secondary_dosha': 'vata'},
}

DOSHA_BY_GRAHA = {
    'sun':     'pitta',
    'moon':    'vata+kapha',
    'mars':    'pitta',
    'mercury': 'vata',
    'jupiter': 'kapha',
    'venus':   'kapha+vata',
    'saturn':  'vata',
    'rahu':    'vata',
    'ketu':    'vata+pitta',
}

# Kalapurusha — Cosmic Person body part assignments by sign
KALAPURUSHA_BODY = {
    'aries':       'head',
    'taurus':      'face/neck',
    'gemini':      'shoulders/arms',
    'cancer':      'chest',
    'leo':         'stomach/heart',
    'virgo':       'abdomen',
    'libra':       'kidneys/lower back',
    'scorpio':     'reproductive organs',
    'sagittarius': 'thighs/hips',
    'capricorn':   'knees',
    'aquarius':    'ankles/calves',
    'pisces':      'feet',
}

DISEASE_BY_GRAHA = {
    'sun': [
        'heart disease', 'eye problems', 'bone disorders', 'fevers',
        'spine problems', 'headaches', 'vitiligo',
    ],
    'moon': [
        'mental health disorders', 'blood disorders', 'colds/flu',
        'fluid imbalance', 'diabetes', 'respiratory problems',
        'insomnia', 'anemia',
    ],
    'mars': [
        'injuries', 'need for surgery', 'inflammation', 'blood disorders',
        'muscle problems', 'accidents', 'burns', 'hypertension',
    ],
    'mercury': [
        'nervous system disorders', 'skin diseases', 'mental disorders',
        'speech impediments', 'allergies', 'vertigo',
    ],
    'jupiter': [
        'liver problems', 'obesity', 'diabetes', 'jaundice',
        'gallstones', 'excess bile', 'tumors',
    ],
    'venus': [
        'reproductive disorders', 'kidney problems', 'diabetes',
        'venereal diseases', 'urinary tract issues', 'hormonal imbalance',
    ],
    'saturn': [
        'chronic diseases', 'arthritis', 'dental problems', 'bone weakness',
        'paralysis', 'nerve degeneration', 'constipation', 'depression',
    ],
    'rahu': [
        'poisoning', 'unusual diseases', 'epidemics', 'accidents',
        'phobias', 'mysterious ailments', 'drug reactions',
    ],
    'ketu': [
        'mysterious diseases', 'parasitic infections', 'wounds that heal slowly',
        'occult-related afflictions', 'spiritual crises', 'psychosomatic disorders',
    ],
}


# ---------------------------------------------------------------------------
# G45 — Public API
# ---------------------------------------------------------------------------

def get_dosha_by_sign(sign: str) -> dict:
    """Return {'primary_dosha': str, 'secondary_dosha': str|None} for a rashi."""
    return DOSHA_BY_SIGN.get(sign.lower(), {})


def get_dosha_by_graha(graha: str) -> str:
    """Return primary dosha string for a graha (e.g. 'pitta', 'vata+kapha')."""
    return DOSHA_BY_GRAHA.get(graha.lower(), '')


def get_body_part(sign: str) -> str:
    """Return Kalapurusha body region for a rashi."""
    return KALAPURUSHA_BODY.get(sign.lower(), '')


def get_diseases_by_graha(graha: str) -> list:
    """Return list of classical diseases/disorders associated with a graha."""
    return DISEASE_BY_GRAHA.get(graha.lower(), [])
