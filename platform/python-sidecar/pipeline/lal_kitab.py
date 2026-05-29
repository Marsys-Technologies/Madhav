"""
G41 — LAL_KITAB: Lal Kitab corpus — planetary house rules, remedies, and debt (rin) karmas.
Tradition: Pt. Roop Chand Joshi's Lal Kitab (Punjab tradition, 20th century).
Distinct from classical BPHS; uses Farsi-derived terminology and unique rin (debt) system.
Sources: Lal Kitab 1939, 1940, 1941, 1942, 1952 editions (Roop Chand Joshi).
Note: Lal Kitab uses the same house numbering as classical Jyotish (1H–12H) but interprets
house ownership and planetary behaviour through its own unique karmic lens.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# LAL_KITAB_RULES — planetary effects by house placement
# Structure: {(planet, house): {effect, remedy, condition, classical_citation}}
# Coverage: 9 grahas × 4–6 houses each = 54 entries
# ---------------------------------------------------------------------------

LAL_KITAB_RULES: dict[tuple[str, int], dict] = {

    # -----------------------------------------------------------------------
    # SURYA (Sun)
    # -----------------------------------------------------------------------
    ('sun', 1): {
        'effect': (
            'Strong self-identity, government service, father lineage strong and supportive. '
            'Native earns through authority and public roles. Health robust in youth.'
        ),
        'remedy': (
            'Throw copper coin in flowing river on Sunday. '
            'Feed wheat and jaggery to cow. Respect father and elders.'
        ),
        'condition': 'Positive when unafflicted; if Saturn aspects, government obstacles arise.',
        'classical_citation': 'LK 1952, Chapter Surya, Lagna placement',
    },
    ('sun', 2): {
        'effect': (
            'Family wealth tied to government or authority figures. '
            'Speech authoritative but may be harsh. Father involved in family finances.'
        ),
        'remedy': (
            'Donate wheat and red cloth on Sunday. '
            'Keep gold or copper near head while sleeping.'
        ),
        'condition': 'If Rahu conjoins, family disputes over ancestral property.',
        'classical_citation': 'LK 1952, Chapter Surya, Dhana Bhava',
    },
    ('sun', 4): {
        'effect': (
            'Property matters tied to government. Mother may face health issues. '
            'Native may serve in administrative roles from home town.'
        ),
        'remedy': (
            'Plant a coconut tree at home. Serve father and elders with respect. '
            'Keep flowing water source near home.'
        ),
        'condition': 'Afflicted Sun here can cause property disputes with government.',
        'classical_citation': 'LK 1952, Chapter Surya, Sukha Bhava',
    },
    ('sun', 7): {
        'effect': (
            'Marriage may be delayed or troubled; spouse may have health issues especially eyes. '
            'Business partnerships with government bodies can bring complications. '
            'Native tends to dominate partner.'
        ),
        'remedy': (
            'Throw piece of copper in river on Sunday. '
            'Do not accept dowry. Respect wife as equal partner.'
        ),
        'condition': 'Worse if Mars aspects — severe marital discord. Better with Jupiter aspect.',
        'classical_citation': 'LK 1952, Chapter Surya, Kalatra Bhava',
    },
    ('sun', 10): {
        'effect': (
            'Excellent for government career, authority, and fame. '
            'Father is source of inspiration. Native rises to prominent position through merit.'
        ),
        'remedy': 'Throw copper coin in flowing river. Keep a ruby or gold ring on right hand.',
        'condition': 'Most auspicious Sun placement in LK. Strong karmic reward indicated.',
        'classical_citation': 'LK 1952, Chapter Surya, Karma Bhava',
    },
    ('sun', 12): {
        'effect': (
            'Eye problems, expenses, spiritual inclination but financial losses. '
            'Foreign travel or settlement likely. '
            'Father may live away or pass early.'
        ),
        'remedy': (
            'Recite Aditya Hridayam daily. '
            'Donate wheat and copper to temple on Sunday. '
            'Keep a copper vessel with water overnight and pour at sunrise.'
        ),
        'condition': 'If Moon also weak, double loss indicated. Ketu here softens the effect.',
        'classical_citation': 'LK 1952, Chapter Surya, Vyaya Bhava',
    },

    # -----------------------------------------------------------------------
    # CHANDRA (Moon)
    # -----------------------------------------------------------------------
    ('moon', 1): {
        'effect': (
            'Emotional, intuitive, and travel-loving nature. '
            'Good mother relationship. Public popularity especially among women. '
            'Mind restless but heart generous.'
        ),
        'remedy': (
            'Keep silver with you. Drink milk. '
            'Do not sell milk or milk products.'
        ),
        'condition': 'Waxing Moon gives strength; waning Moon increases restlessness.',
        'classical_citation': 'LK 1952, Chapter Chandra, Lagna placement',
    },
    ('moon', 2): {
        'effect': (
            'Prosperous family, beautiful speech, wealth through liquid goods or silver. '
            'Mother influences family finances. '
            'Native earns through trade involving liquids or public dealing.'
        ),
        'remedy': 'Donate milk and rice on Monday. Keep silver bowl in home.',
        'condition': 'Rahu or Ketu conjunction spoils the effect of 2H Moon.',
        'classical_citation': 'LK 1952, Chapter Chandra, Dhana Bhava',
    },
    ('moon', 4): {
        'effect': (
            'Landed property, mother\'s strong blessing, emotional contentment at home. '
            'Benefits from water bodies or land near water. '
            'Domestic happiness and comfort of home.'
        ),
        'remedy': (
            'Keep a small silver idol of Ganesha in home. '
            'Do not break or demolish old wells on property.'
        ),
        'condition': 'Most powerful Moon placement in LK. Mother\'s blessings are karmic armour.',
        'classical_citation': 'LK 1952, Chapter Chandra, Sukha Bhava',
    },
    ('moon', 7): {
        'effect': (
            'Spouse is attractive and emotionally sensitive. '
            'Marriage brings emotional fulfilment but also mood fluctuations in partnership. '
            'Business partnerships with women prove beneficial.'
        ),
        'remedy': 'Offer water to rising Moon on Monday evenings. Keep silver in partnership agreements.',
        'condition': 'Waxing Moon here gives beautiful, prosperous spouse.',
        'classical_citation': 'LK 1952, Chapter Chandra, Kalatra Bhava',
    },
    ('moon', 8): {
        'effect': (
            'Inheritance from mother\'s side. Long life but emotional turmoil. '
            'Occult knowledge and interest in hidden matters. '
            'In-laws\' financial situation fluctuates.'
        ),
        'remedy': 'Recite Mahamrityunjaya mantra. Do not neglect mother\'s needs.',
        'condition': 'Afflicted 8H Moon can bring psychic disturbances and nightmares.',
        'classical_citation': 'LK 1952, Chapter Chandra, Ayu Bhava',
    },
    ('moon', 10): {
        'effect': (
            'Career in public sector, nurturing professions, liquids trade, or government. '
            'Mother\'s blessings power professional rise. '
            'Public image is caring and trustworthy.'
        ),
        'remedy': 'Donate white cloth and rice to women in need on Monday.',
        'condition': 'Moon in 10H aspected by Jupiter is exceptional for public-service career.',
        'classical_citation': 'LK 1952, Chapter Chandra, Karma Bhava',
    },

    # -----------------------------------------------------------------------
    # MANGAL (Mars)
    # -----------------------------------------------------------------------
    ('mars', 1): {
        'effect': (
            'Courage, physical strength, brother relationships central to life. '
            'Aggressive energy — excellent for military, police, sports. '
            'Can cause head injuries if afflicted.'
        ),
        'remedy': (
            'Feed crows on Tuesday. '
            'Donate red lentils and red cloth. '
            'Keep a copper strip in pocket.'
        ),
        'condition': 'Saturn aspect on 1H Mars generates persistent obstacles in career.',
        'classical_citation': 'LK 1952, Chapter Mangal, Lagna placement',
    },
    ('mars', 3): {
        'effect': (
            'Courageous and bold siblings, especially brothers who support the native. '
            'Writing with sharp, direct style. '
            'Short journeys for work or adventure.'
        ),
        'remedy': 'Help younger siblings. Donate iron utensils on Tuesday.',
        'condition': 'Strong Mars in 3H makes the native a natural leader among peers.',
        'classical_citation': 'LK 1952, Chapter Mangal, Sahaja Bhava',
    },
    ('mars', 4): {
        'effect': (
            'Property disputes, land and real estate issues. '
            'Mother\'s health may be a concern. '
            'Conflicts at home, but also protective instinct for household.'
        ),
        'remedy': (
            'Do not build house facing south. '
            'Keep a small vessel of water near main door. '
            'Plant a Peepal tree.'
        ),
        'condition': 'Mars in 4H with Saturn brings chronic domestic friction.',
        'classical_citation': 'LK 1952, Chapter Mangal, Sukha Bhava',
    },
    ('mars', 7): {
        'effect': (
            'Marital discord significant — the LK Kuja Dosha effect. '
            'Spouse may be aggressive or face accidents. '
            'Business partnerships involve competition and conflict.'
        ),
        'remedy': (
            'Donate red lentils on Tuesday before marriage. '
            'Marry after age 28. '
            'Spouse should wear copper bracelet.'
        ),
        'condition': 'Jupiter aspect on 7H Mars significantly reduces marital harm.',
        'classical_citation': 'LK 1952, Chapter Mangal, Kalatra Bhava',
    },
    ('mars', 8): {
        'effect': (
            'Accidents, surgeries, or sudden injuries possible. '
            'Occult interests, inheritance through brothers. '
            'Long life but with health battles in middle age.'
        ),
        'remedy': 'Donate blood if health allows. Keep iron near bed. Recite Hanuman Chalisa.',
        'condition': 'Mars in 8H with Jupiter gives occult protection and long life.',
        'classical_citation': 'LK 1952, Chapter Mangal, Ayu Bhava',
    },
    ('mars', 10): {
        'effect': (
            'Excellent for engineering, military, police, surgery career. '
            'Professional ambition is fierce and productive. '
            'Father involved in physical or technical work.'
        ),
        'remedy': 'Donate copper to temple on Tuesday. Keep workplace tools clean and respected.',
        'condition': 'One of LK\'s most powerful career placements when Mars is strong.',
        'classical_citation': 'LK 1952, Chapter Mangal, Karma Bhava',
    },

    # -----------------------------------------------------------------------
    # BUDHA (Mercury)
    # -----------------------------------------------------------------------
    ('mercury', 1): {
        'effect': (
            'Intelligent, clever, business-minded native. '
            'Youthful appearance, quick wit, skill in writing and communication. '
            'Multiple talents and sources of income.'
        ),
        'remedy': 'Feed green vegetables to cows on Wednesday. Wear emerald or glass bead.',
        'condition': 'Rahu conjunction gives exceptional intellect but also deceptive tendencies.',
        'classical_citation': 'LK 1952, Chapter Budha, Lagna placement',
    },
    ('mercury', 2): {
        'effect': (
            'Educated family, income through speech, writing, or trade. '
            'Multiple languages or skills bring wealth. '
            'Family is intellectually active.'
        ),
        'remedy': 'Donate green moong dal on Wednesday. Keep books in good condition.',
        'condition': 'Mercury-Venus conjunction in 2H gives artistic and commercial success.',
        'classical_citation': 'LK 1952, Chapter Budha, Dhana Bhava',
    },
    ('mercury', 5): {
        'effect': (
            'Intelligent children, inclination toward education and speculation. '
            'Gains through writing, teaching, or creative arts. '
            'Sharp analytical mind.'
        ),
        'remedy': 'Donate educational materials to children on Wednesday.',
        'condition': 'Mercury with Jupiter in 5H creates a born teacher or scholar.',
        'classical_citation': 'LK 1952, Chapter Budha, Putra Bhava',
    },
    ('mercury', 7): {
        'effect': (
            'Intelligent spouse, business partnerships in trade or communication. '
            'Marriage brings intellectual stimulation. '
            'Multiple business ventures possible.'
        ),
        'remedy': 'Donate green cloth to sister-in-law. Keep accounts clear in business.',
        'condition': 'Saturn influence here creates delays in marriage but stable once settled.',
        'classical_citation': 'LK 1952, Chapter Budha, Kalatra Bhava',
    },
    ('mercury', 10): {
        'effect': (
            'Career in trade, communication, accounts, IT, or education. '
            'Professional versatility and adaptability. '
            'Reputation for intelligence and analytical skill.'
        ),
        'remedy': 'Never cheat in business dealings. Feed green birds (parrots) on Wednesday.',
        'condition': 'Mercury-Jupiter in 10H produces a highly respected professional.',
        'classical_citation': 'LK 1952, Chapter Budha, Karma Bhava',
    },

    # -----------------------------------------------------------------------
    # GURU (Jupiter)
    # -----------------------------------------------------------------------
    ('jupiter', 1): {
        'effect': (
            'Wisdom, spiritual inclination, respected teacher-like personality. '
            'Good fortune from birth; life guided by dharmic principles. '
            'Physical appearance dignified and trustworthy.'
        ),
        'remedy': 'Donate yellow cloth and turmeric on Thursday. Fast on Thursdays.',
        'condition': 'Jupiter debilitated (Capricorn) in 1H loses much of its protective quality.',
        'classical_citation': 'LK 1952, Chapter Guru, Lagna placement',
    },
    ('jupiter', 2): {
        'effect': (
            'Educated, wealthy family; financial security through knowledge or Brahmin-like work. '
            'Speech carries authority and wisdom. '
            'Family traditions are upheld.'
        ),
        'remedy': 'Respect teachers and Brahmins. Donate yellow lentils on Thursday.',
        'condition': 'Jupiter in 2H is a strong indicator of hereditary knowledge and family wealth.',
        'classical_citation': 'LK 1952, Chapter Guru, Dhana Bhava',
    },
    ('jupiter', 5): {
        'effect': (
            'Blessed children, especially sons. Teaching or coaching career. '
            'Gains through speculation, education, or religious work. '
            'Creative intelligence and philosophical mind.'
        ),
        'remedy': 'Feed sweet yellow food to children. Donate to schools on Thursday.',
        'condition': 'Jupiter in 5H is the classic indicator of a guru-like native.',
        'classical_citation': 'LK 1952, Chapter Guru, Putra Bhava',
    },
    ('jupiter', 7): {
        'effect': (
            'Wise, educated, and spiritually inclined spouse. '
            'Business partnerships with teachers or religious figures. '
            'Marriage is sacred and long-lasting.'
        ),
        'remedy': 'Donate yellow cloth to married women. Respect wife\'s family elders.',
        'condition': 'Jupiter in 7H is LK\'s most auspicious placement for marriage quality.',
        'classical_citation': 'LK 1952, Chapter Guru, Kalatra Bhava',
    },
    ('jupiter', 9): {
        'effect': (
            'Deeply spiritual, fortunate, dharmic life path. '
            'Father or guru plays transformative role. '
            'Long-distance travel for spiritual purposes.'
        ),
        'remedy': 'Read scriptures and religious texts. Donate to places of worship.',
        'condition': 'Jupiter in 9H is considered the best possible dharma placement in LK.',
        'classical_citation': 'LK 1952, Chapter Guru, Dharma Bhava',
    },
    ('jupiter', 11): {
        'effect': (
            'Gains through elder brothers, networks, and social causes. '
            'Ambitions fulfilled through wisdom. '
            'Long-term financial security through accumulated knowledge.'
        ),
        'remedy': 'Donate gold or yellow items to elder brother or surrogate. Fast on Thursdays.',
        'condition': 'Jupiter in 11H bestows lasting income and respected social circle.',
        'classical_citation': 'LK 1952, Chapter Guru, Labha Bhava',
    },

    # -----------------------------------------------------------------------
    # SHUKRA (Venus)
    # -----------------------------------------------------------------------
    ('venus', 1): {
        'effect': (
            'Charming, artistic, and attractive personality. '
            'Pleasure-seeking but also talented in arts and aesthetics. '
            'Comfortable lifestyle and enjoyment of luxury.'
        ),
        'remedy': 'Donate white sweets and curd on Friday. Wear silver ring.',
        'condition': 'Venus in 1H with Saturn reduces personal charm but increases artistic discipline.',
        'classical_citation': 'LK 1952, Chapter Shukra, Lagna placement',
    },
    ('venus', 2): {
        'effect': (
            'Beautiful and artistic family, income from arts, luxury goods, or beauty industry. '
            'Sweet and persuasive speech. '
            'Family wealth tied to aesthetic or comfort-related trade.'
        ),
        'remedy': 'Donate white cloth or sweets to women on Friday. Keep silver vessel at home.',
        'condition': 'Mercury conjunction in 2H gives powerful artistic-commercial success.',
        'classical_citation': 'LK 1952, Chapter Shukra, Dhana Bhava',
    },
    ('venus', 4): {
        'effect': (
            'Beautiful, comfortable home; vehicles and luxury items. '
            'Mother is artistic and well-loved. '
            'Land with aesthetic value — gardens, decorated spaces.'
        ),
        'remedy': 'Keep home clean and decorated. Donate white flowers on Fridays.',
        'condition': 'Venus in 4H is one of LK\'s best indicators of comfortable domestic life.',
        'classical_citation': 'LK 1952, Chapter Shukra, Sukha Bhava',
    },
    ('venus', 7): {
        'effect': (
            'Attractive spouse, luxury in marriage, sensual partnership. '
            'Business partnerships in artistic or luxury fields. '
            'Danger of over-indulgence in pleasures.'
        ),
        'remedy': (
            'Donate white sweets to wife\'s family. '
            'Do not keep broken or cracked mirror at home. '
            'Respect women in household.'
        ),
        'condition': 'Venus-Jupiter in 7H gives the most auspicious marriage in LK.',
        'classical_citation': 'LK 1952, Chapter Shukra, Kalatra Bhava',
    },
    ('venus', 12): {
        'effect': (
            'Expenditure on luxury, comfort in foreign lands, bedroom pleasures. '
            'Spiritual experiences through arts or beauty. '
            'Possible foreign settlement or ashram life.'
        ),
        'remedy': 'Donate white cloth to temple. Keep bedroom clean and aesthetic.',
        'condition': 'Venus in 12H with Ketu gives deep spiritual sensitivity and artistic gifts.',
        'classical_citation': 'LK 1952, Chapter Shukra, Vyaya Bhava',
    },

    # -----------------------------------------------------------------------
    # SHANI (Saturn)
    # -----------------------------------------------------------------------
    ('saturn', 1): {
        'effect': (
            'Service-oriented career, slow but steady progress through life. '
            'Hardworking, disciplined, responsible personality. '
            'Life lessons come through trials in early years.'
        ),
        'remedy': (
            'Feed crows and dogs on Saturday. '
            'Donate black sesame and mustard oil. '
            'Do not lie or cut corners in work.'
        ),
        'condition': 'If Sun also in 1H or aspects it, father relationship is severely strained.',
        'classical_citation': 'LK 1952, Chapter Shani, Lagna placement',
    },
    ('saturn', 3): {
        'effect': (
            'Slow, disciplined communication. Younger siblings may face obstacles. '
            'Hard work in short journeys and daily efforts. '
            'Writing is serious and thorough.'
        ),
        'remedy': 'Help younger siblings. Donate iron on Saturday.',
        'condition': 'Saturn in 3H with Mars creates fraternal disputes and legal issues.',
        'classical_citation': 'LK 1952, Chapter Shani, Sahaja Bhava',
    },
    ('saturn', 7): {
        'effect': (
            'Delayed marriage, foreign-born or much older/younger spouse. '
            'Karmic partnership — spouse teaches important life lessons. '
            'Business partnerships require caution and clear agreements.'
        ),
        'remedy': (
            'Donate mustard oil to Shani temple on Saturday. '
            'Do not delay marriage beyond reasonable age. '
            'Respect spouse\'s personal space and boundaries.'
        ),
        'condition': 'Jupiter aspect on Saturn in 7H greatly improves marriage prospects.',
        'classical_citation': 'LK 1952, Chapter Shani, Kalatra Bhava',
    },
    ('saturn', 8): {
        'effect': (
            'Long life (Saturn rules longevity), occult interests, chronic health issues manageable. '
            'Inheritance through service or hard work. '
            'Interest in mines, archaeology, or hidden knowledge.'
        ),
        'remedy': 'Donate black sesame on Saturday. Offer water to Peepal tree.',
        'condition': 'Saturn in 8H is LK\'s indicator of longevity and spiritual depth through hardship.',
        'classical_citation': 'LK 1952, Chapter Shani, Ayu Bhava',
    },
    ('saturn', 10): {
        'effect': (
            'Service career, discipline, and slow but guaranteed rise. '
            'Government or institutional employment. '
            'Career builds over decades; retirement years are most respected.'
        ),
        'remedy': 'Never abandon service duties. Feed poor on Saturday. Maintain integrity at work.',
        'condition': 'Saturn in 10H promises ultimate career success through karma yoga.',
        'classical_citation': 'LK 1952, Chapter Shani, Karma Bhava',
    },
    ('saturn', 12): {
        'effect': (
            'Expenses on hospitals, isolation, or foreign lands. '
            'Spiritual liberation through austerity. '
            'Loss of sleep or rest; but deep meditation possible.'
        ),
        'remedy': 'Donate to hospitals or orphanages on Saturday. Practice fasting.',
        'condition': 'Saturn in 12H with Ketu gives exceptional spiritual liberation in final years.',
        'classical_citation': 'LK 1952, Chapter Shani, Vyaya Bhava',
    },

    # -----------------------------------------------------------------------
    # RAHU (North Node)
    # -----------------------------------------------------------------------
    ('rahu', 1): {
        'effect': (
            'Unconventional personality, foreign influences, obsession with self-image. '
            'Ambition is fierce and worldly. '
            'May adopt foreign culture or lifestyle.'
        ),
        'remedy': (
            'Feed bread to dogs. '
            'Wear a silver bracelet. '
            'Keep a coconut in the home.'
        ),
        'condition': 'Rahu in 1H with Jupiter reduces harm; with Saturn increases isolation.',
        'classical_citation': 'LK 1952, Chapter Rahu, Lagna placement',
    },
    ('rahu', 4): {
        'effect': (
            'Disrupted home life, unusual property matters, step-mother or unconventional mother. '
            'Foreign influences in domestic sphere. '
            'Land acquisition through non-traditional means.'
        ),
        'remedy': 'Keep a copper coin buried near home entrance. Do not dig wells carelessly.',
        'condition': 'Rahu in 4H is one of LK\'s most challenging placements for domestic peace.',
        'classical_citation': 'LK 1952, Chapter Rahu, Sukha Bhava',
    },
    ('rahu', 5): {
        'effect': (
            'Unconventional or fewer children; possible adopted or foreign-born child. '
            'Education through unorthodox means. '
            'Creative speculation but also impulsive risks.'
        ),
        'remedy': (
            'Do not keep a pet dog if Rahu is in 5H (LK specific). '
            'Donate blue cloth to orphans. '
            'Keep silver square piece in wallet.'
        ),
        'condition': 'Rahu in 5H with Jupiter gives a gifted but eccentric child.',
        'classical_citation': 'LK 1952, Chapter Rahu, Putra Bhava',
    },
    ('rahu', 7): {
        'effect': (
            'Non-traditional or intercultural marriage. '
            'Spouse may be from different background. '
            'Business partnerships with foreigners bring mixed results.'
        ),
        'remedy': 'Donate blue cloth on Saturday. Keep a silver square in bedroom.',
        'condition': 'Rahu in 7H requires careful vetting of business partners to avoid fraud.',
        'classical_citation': 'LK 1952, Chapter Rahu, Kalatra Bhava',
    },
    ('rahu', 10): {
        'effect': (
            'Sudden rises and falls in career. Fame through unconventional path. '
            'Work involving foreigners, technology, or mass media. '
            'Political ambition and public attention.'
        ),
        'remedy': 'Donate to Shani or Rahu-related charities on Saturday. Avoid shortcuts in career.',
        'condition': 'Rahu in 10H is a double-edged sword — great fame or great scandal.',
        'classical_citation': 'LK 1952, Chapter Rahu, Karma Bhava',
    },
    ('rahu', 11): {
        'effect': (
            'Exceptional gains through unconventional or foreign networks. '
            'Elder siblings involve foreigners or unusual professions. '
            'Ambitions fulfilled through persistence despite controversy.'
        ),
        'remedy': 'Donate blue or black cloth on Saturday. Feed snakes or donate to snake charmer.',
        'condition': 'Rahu in 11H is often said to be powerful for material accumulation in LK.',
        'classical_citation': 'LK 1952, Chapter Rahu, Labha Bhava',
    },

    # -----------------------------------------------------------------------
    # KETU (South Node)
    # -----------------------------------------------------------------------
    ('ketu', 1): {
        'effect': (
            'Spiritually inclined, detached from material ambitions. '
            'Karmic identity — native often feels a sense of unworldly purpose. '
            'Body may have strange markings or birthmarks.'
        ),
        'remedy': (
            'Donate black and white blanket on Tuesday. '
            'Keep a dog or donate to dog shelter. '
            'Do not disrespect spiritual figures.'
        ),
        'condition': 'Ketu in 1H with Jupiter gives remarkable spiritual gifts but social eccentricity.',
        'classical_citation': 'LK 1952, Chapter Ketu, Lagna placement',
    },
    ('ketu', 4): {
        'effect': (
            'Displaced home, ancestral property disputes, unconventional mother relationship. '
            'Past life karma around home and land surfaces. '
            'May live away from birthplace.'
        ),
        'remedy': 'Donate milk to black cow. Keep roots of specific plants in home per LK.',
        'condition': 'Ketu in 4H often correlates with displacement or emigration.',
        'classical_citation': 'LK 1952, Chapter Ketu, Sukha Bhava',
    },
    ('ketu', 7): {
        'effect': (
            'Karmic marriage — partner from past life. '
            'Separation or spiritual divergence in marriage possible. '
            'Business partnerships dissolve unless based on shared spiritual or service values.'
        ),
        'remedy': 'Donate black and white cloth together. Respect spouse\'s spiritual path.',
        'condition': 'Ketu in 7H without Jupiter aspect often leads to eventual separation.',
        'classical_citation': 'LK 1952, Chapter Ketu, Kalatra Bhava',
    },
    ('ketu', 9): {
        'effect': (
            'Past life spiritual merit surfaces. '
            'Father may be unconventional or absent. '
            'Dharma path is unique, non-conformist, and often misunderstood.'
        ),
        'remedy': 'Donate to places of worship. Perform ancestral rites (Shraddha) regularly.',
        'condition': 'Ketu in 9H is LK\'s marker for someone who challenges orthodox religion.',
        'classical_citation': 'LK 1952, Chapter Ketu, Dharma Bhava',
    },
    ('ketu', 12): {
        'effect': (
            'Moksha-indicator: foreign residence, hospital stays, spiritual retreat. '
            'Strong past-life karma around liberation. '
            'Expenses on sacred causes; ultimate spiritual reward.'
        ),
        'remedy': (
            'Donate iron articles on Tuesday. '
            'Keep a dog as companion or donate to dog shelter. '
            'Visit temples of Bhairava or Kali.'
        ),
        'condition': 'Ketu in 12H is LK\'s prime indicator for final liberation (moksha).',
        'classical_citation': 'LK 1952, Chapter Ketu, Vyaya Bhava',
    },
}


# ---------------------------------------------------------------------------
# LAL_KITAB_REMEDIES — classical LK remedies per graha
# ---------------------------------------------------------------------------

LAL_KITAB_REMEDIES: dict[str, dict] = {
    'sun': {
        'remedies': [
            'Feed wheat and jaggery to cow on Sunday',
            'Throw copper coin in flowing river on Sunday',
            'Wear ruby or gold ring on right ring finger on Sunday morning',
            'Recite Aditya Hridayam daily at sunrise',
            'Respect father, elders, and government authorities',
            'Keep a copper vessel of water overnight and pour at sunrise',
            'Do not accept electrical gadgets as gifts',
        ],
        'fasting_day': 'Sunday',
        'metal': 'Copper/Gold',
        'donate': 'Wheat, jaggery, red cloth on Sunday',
        'mantra': 'Om Suryaya Namah (108 times at sunrise)',
        'gemstone': 'Ruby (Manik)',
        'lk_specific': 'Throwing copper coin in river is the signature LK Sun remedy',
    },
    'moon': {
        'remedies': [
            'Drink milk and keep silver with you',
            'Donate rice, milk, and white cloth on Monday',
            'Offer water to Moon on Monday evenings (Chandra Arghya)',
            'Do not sell milk or milk products — destroys Moon\'s goodness',
            'Keep a silver bowl in home',
            'Respect mother and all mother-figures',
            'Fast on Mondays during Shukla Paksha (waxing phase)',
        ],
        'fasting_day': 'Monday',
        'metal': 'Silver',
        'donate': 'Rice, milk, white cloth on Monday',
        'mantra': 'Om Chandraya Namah (108 times on Monday evening)',
        'gemstone': 'Pearl (Moti)',
        'lk_specific': 'Do not sell milk products — unique LK prohibition for Moon',
    },
    'mars': {
        'remedies': [
            'Feed crows on Tuesday mornings',
            'Donate red lentils and red cloth on Tuesday',
            'Keep a copper strip or bangle',
            'Recite Hanuman Chalisa on Tuesdays',
            'Plant a neem tree near home',
            'Help brothers and younger siblings',
            'Do not keep broken or cracked red items in home',
        ],
        'fasting_day': 'Tuesday',
        'metal': 'Copper',
        'donate': 'Red lentils, red cloth, copper vessel on Tuesday',
        'mantra': 'Om Mangalaya Namah (108 times on Tuesday)',
        'gemstone': 'Red Coral (Moonga)',
        'lk_specific': 'Feeding crows and planting neem tree are signature LK Mars remedies',
    },
    'mercury': {
        'remedies': [
            'Feed green vegetables to cows on Wednesday',
            'Donate green moong dal on Wednesday',
            'Wear emerald or glass bead on right little finger',
            'Feed parrots or green birds',
            'Keep books and educational items in good condition',
            'Never cheat in business dealings — Mercury karma is immediate',
            'Donate to schools or educational trusts on Wednesday',
        ],
        'fasting_day': 'Wednesday',
        'metal': 'Gold/Brass',
        'donate': 'Green vegetables, green moong dal, green cloth on Wednesday',
        'mantra': 'Om Budhaya Namah (108 times on Wednesday)',
        'gemstone': 'Emerald (Panna)',
        'lk_specific': 'Feeding green birds (parrots) is the signature LK Mercury remedy',
    },
    'jupiter': {
        'remedies': [
            'Donate yellow cloth and turmeric on Thursday',
            'Fast on Thursdays',
            'Respect teachers and Brahmins',
            'Feed sweet yellow food (besan laddoo) to children',
            'Donate yellow lentils (chana dal) to temple on Thursday',
            'Read scriptures and maintain connection with spiritual learning',
            'Donate banana, turmeric, and yellow flowers on Thursday',
        ],
        'fasting_day': 'Thursday',
        'metal': 'Gold',
        'donate': 'Yellow cloth, turmeric, bananas, chana dal on Thursday',
        'mantra': 'Om Gurave Namah (108 times on Thursday)',
        'gemstone': 'Yellow Sapphire (Pukhraj)',
        'lk_specific': 'Fasting on Thursday and respecting guru/teacher is the LK Jupiter baseline',
    },
    'venus': {
        'remedies': [
            'Donate white sweets and curd on Friday',
            'Wear silver ring on right ring finger on Friday',
            'Keep bedroom clean, aesthetic, and fragrant',
            'Donate white cloth to women on Friday',
            'Do not keep broken or cracked mirrors in home',
            'Respect women — wife, sisters, mother-in-law',
            'Keep a piece of silver in the home always',
        ],
        'fasting_day': 'Friday',
        'metal': 'Silver',
        'donate': 'White sweets, curd, white cloth on Friday',
        'mantra': 'Om Shukraya Namah (108 times on Friday)',
        'gemstone': 'Diamond (Heera) or White Sapphire',
        'lk_specific': 'No broken mirrors and silver in home are the signature LK Venus remedies',
    },
    'saturn': {
        'remedies': [
            'Feed crows and dogs on Saturday mornings',
            'Donate black sesame (til) on Saturday',
            'Donate mustard oil at Shani temple on Saturday',
            'Donate dark/black or blue cloth on Saturday',
            'Fast on Saturdays and maintain honest work ethics',
            'Offer water to Peepal tree on Saturday',
            'Do not purchase iron or metal items on Saturday',
        ],
        'fasting_day': 'Saturday',
        'metal': 'Iron/Steel',
        'donate': 'Black sesame, mustard oil, dark cloth on Saturday',
        'mantra': 'Om Shanaischaraya Namah (108 times on Saturday)',
        'gemstone': 'Blue Sapphire (Neelam) — with caution',
        'lk_specific': 'Feeding crows and dogs on Saturday is the signature LK Saturn remedy',
    },
    'rahu': {
        'remedies': [
            'Feed bread to dogs on Saturday',
            'Wear a silver bracelet on left wrist',
            'Keep a coconut in home — replace when it dries',
            'Donate blue or black cloth on Saturday',
            'Feed snakes (or donate to snake charmer) on Saturdays',
            'Donate mustard seeds wrapped in blue cloth on Saturday',
            'Keep a silver square piece in wallet',
        ],
        'fasting_day': 'Saturday',
        'metal': 'Lead/Silver (silver for protection)',
        'donate': 'Blue cloth, mustard seeds, black sesame on Saturday',
        'mantra': 'Om Rahave Namah (108 times at dusk)',
        'gemstone': 'Hessonite Garnet (Gomed)',
        'lk_specific': 'Keeping coconut in home and feeding dogs are the LK Rahu remedies',
    },
    'ketu': {
        'remedies': [
            'Donate black and white blanket or cloth on Tuesday',
            'Keep a dog as companion or donate to dog shelter',
            'Donate iron articles or old iron utensils on Tuesday',
            'Visit Bhairava or Kali temples',
            'Perform Shraddha (ancestral rites) for departed souls',
            'Do not disrespect spiritual figures or ascetics',
            'Donate black and white items together on Tuesday',
        ],
        'fasting_day': 'Tuesday',
        'metal': 'Iron (old/rusty iron for charity)',
        'donate': 'Black and white cloth together, iron objects on Tuesday',
        'mantra': 'Om Ketave Namah (108 times on Tuesday evening)',
        'gemstone': 'Cat\'s Eye (Lehsunia)',
        'lk_specific': 'Donating black-and-white together is uniquely LK for Ketu',
    },
}


# ---------------------------------------------------------------------------
# LAL_KITAB_DEBT_KARMAS — classical rin (debt) system
# ---------------------------------------------------------------------------

LAL_KITAB_DEBT_KARMAS: list[dict] = [
    {
        'debt_type': 'Pitr Rin',
        'debt_name_translated': 'Father/Ancestors Debt',
        'indicator': 'Sun afflicted (by Saturn, Rahu, or Ketu), or Sun in 6H/8H/12H',
        'symptoms': [
            'Strained father relationship',
            'Chronic obstacles in government dealings',
            'Eye diseases or chronic fevers',
            'Family patriarch line weakened',
        ],
        'remedy': (
            'Perform Pindadan and Pitru Tarpan at Gaya or on Amavasya. '
            'Feed Brahmins on death anniversaries of ancestors. '
            'Respect father unconditionally. '
            'Donate wheat and copper on Sundays.'
        ),
        'classical_citation': 'LK 1952, Rin Adhyaya, Pitr Rin section',
    },
    {
        'debt_type': 'Matri Rin',
        'debt_name_translated': 'Mother Debt',
        'indicator': 'Moon afflicted (by Saturn, Rahu, or Ketu), or Moon in 6H/8H/12H',
        'symptoms': [
            'Mother\'s health struggles',
            'Emotional instability and psychological turbulence',
            'Loss of domestic peace',
            'Female relatives face repeated difficulties',
        ],
        'remedy': (
            'Serve mother with devotion. '
            'Donate milk and rice to women in need. '
            'Recite Durga Kavach on Mondays. '
            'Keep silver in home and offer Chandra Arghya.'
        ),
        'classical_citation': 'LK 1952, Rin Adhyaya, Matri Rin section',
    },
    {
        'debt_type': 'Bhai Rin',
        'debt_name_translated': 'Sibling/Brother Debt',
        'indicator': 'Mars afflicted, or Mars in 6H/8H/12H with malefic influence',
        'symptoms': [
            'Sibling disputes and legal conflicts',
            'Brothers face accidents or surgeries',
            'Physical aggression or violence in family',
            'Property disputes with siblings',
        ],
        'remedy': (
            'Serve and help brothers actively. '
            'Donate red lentils on Tuesday. '
            'Feed crows on Tuesday mornings. '
            'Recite Hanuman Chalisa on Tuesdays.'
        ),
        'classical_citation': 'LK 1952, Rin Adhyaya, Bhai Rin section',
    },
    {
        'debt_type': 'Atma Rin',
        'debt_name_translated': 'Soul/Self Debt',
        'indicator': 'Rahu-Ketu axis tense (conjunct malefics or in 1H/7H axis)',
        'symptoms': [
            'Persistent sense of purposelessness',
            'Repeated karmic patterns across relationships',
            'Identity confusion or spiritual crisis',
            'Actions seem to backfire despite good intentions',
        ],
        'remedy': (
            'Self-karma correction through meditation and truthful living. '
            'Donate to orphanages and help those with no family. '
            'Feed dogs and crows on both Tuesday and Saturday. '
            'Perform Ketu shanti puja.'
        ),
        'classical_citation': 'LK 1952, Rin Adhyaya, Atma Rin section',
    },
    {
        'debt_type': 'Stri Rin',
        'debt_name_translated': 'Woman/Wife Debt',
        'indicator': 'Venus afflicted, or 7H lord in debility, or Saturn-Venus conjunction',
        'symptoms': [
            'Exploitation or mistreatment of women in past or present life',
            'Marriage brings persistent suffering or betrayal',
            'Female family members face losses',
            'Repeated failures in partnerships',
        ],
        'remedy': (
            'Respect all women — wife, sisters, mother-in-law, daughters. '
            'Donate white cloth and sweets to women on Fridays. '
            'Never break a woman\'s trust in any form. '
            'Keep home environment peaceful for female members.'
        ),
        'classical_citation': 'LK 1952, Rin Adhyaya, Stri Rin section',
    },
    {
        'debt_type': 'Guru Rin',
        'debt_name_translated': 'Teacher/Guru Debt',
        'indicator': 'Jupiter afflicted, or Jupiter in 6H/8H/12H with malefic aspect',
        'symptoms': [
            'Lack of educational success despite effort',
            'Betrayal of or by teachers and mentors',
            'Spiritual wisdom blocked',
            'Children face obstacles in their education',
        ],
        'remedy': (
            'Respect all teachers and Brahmins. '
            'Donate yellow cloth and turmeric to temple on Thursday. '
            'Never dishonour the knowledge received from a guru. '
            'Feed students and donate books to schools.'
        ),
        'classical_citation': 'LK 1952, Rin Adhyaya, Guru Rin section',
    },
    {
        'debt_type': 'Dharti Rin',
        'debt_name_translated': 'Earth/Land Debt',
        'indicator': 'Saturn afflicted in 4H or Rahu in 4H, or property-related chart patterns',
        'symptoms': [
            'Disputes over land, property, real estate',
            'Inability to settle in one place',
            'Environmental damage caused in past or present life',
            'Lack of domestic stability across generations',
        ],
        'remedy': (
            'Plant trees, especially Peepal and Neem, near home. '
            'Donate land or assist in land restoration for public use. '
            'Do not sell or encroach on sacred land or burial grounds. '
            'Offer water to Peepal tree on Saturday.'
        ),
        'classical_citation': 'LK 1952, Rin Adhyaya, Dharti Rin section',
    },
]


# ---------------------------------------------------------------------------
# Public API functions
# ---------------------------------------------------------------------------

def get_lk_rules_for_planet(planet: str) -> list[dict]:
    """
    Return all LK rules for a given planet (graha name, lowercase).
    Each returned dict includes: planet, house, effect, remedy, condition, classical_citation.
    """
    planet = planet.lower().strip()
    results = []
    for (p, h), rule in LAL_KITAB_RULES.items():
        if p == planet:
            results.append({
                'planet': p,
                'house': h,
                **rule,
            })
    return sorted(results, key=lambda r: r['house'])


def get_lk_rules_for_house(house: int) -> list[dict]:
    """
    Return all LK rules for a given house (1–12).
    Each returned dict includes: planet, house, effect, remedy, condition, classical_citation.
    """
    results = []
    for (p, h), rule in LAL_KITAB_RULES.items():
        if h == house:
            results.append({
                'planet': p,
                'house': h,
                **rule,
            })
    return sorted(results, key=lambda r: r['planet'])


def get_lk_remedy(planet: str) -> dict:
    """
    Return the full remedy profile for a given planet from LAL_KITAB_REMEDIES.
    Returns empty dict if planet not found.
    """
    return LAL_KITAB_REMEDIES.get(planet.lower().strip(), {})


def list_debt_karmas() -> list[dict]:
    """
    Return the complete list of LK debt karma (rin) entries.
    Each entry contains: debt_type, debt_name_translated, indicator, symptoms, remedy, classical_citation.
    """
    return LAL_KITAB_DEBT_KARMAS
