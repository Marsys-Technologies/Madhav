import json, sys, collections
sys.path.insert(0, '/private/tmp/claude-504/scratch/curation/bg_reference_B')
from lib import *

rows = {}
for l in rq("select term_id,term_en,category,classical_citation,regexp_replace(coalesce(definition,''),'[|]',' ','g') from reference_glossary order by term_id").splitlines()[1:-1]:
    tid, en, cat, cc, df = l.split('|', 4)
    rows[tid] = dict(en=en, cat=cat, cit=cc, df=df)
assert len(rows) == 364

G = {
 'BEN': ('bphs_pg0026_c01', "are malefics while the rest are benefics", '11'),
 'ASP': ('bphs_pg0254_c01', "in slabs of quarters i.e l14, 112,3l4thand fult", '2-5'),
 'SB_S': ('bphs_pg0263_c01', "1. Sthaana Bala (or positional strength)", None),
 'SB_D': ('bphs_pg0263_c01', "2. Dig Bala (or directional strength)", None),
 'SB_K': ('bphs_pg0263_c01', "3. Kala Bala (Temporal Strcngtb) inclusive of Ayana Bala", None),
 'SB_C': ('bphs_pg0263_c01', "4. Cheshta Bala (or motional strength)", None),
 'SB_N': ('bphs_pg0263_c01', "5. Naisargika Bala (or natural strength)", None),
 'SB_R': ('bphs_pg0263_c01', "6. Drik Bala (or aspectual strength)", None),
 'SB_ALL': ('bphs_pg0263_c01', "These strengths are called Shadbala", None),
 'SB_U': ('bphs_pg0263_c01', "1. Uchcha Bala (or exaltation strength)", None),
 'SB_O': ('bphs_pg0263_c01', "Ojhayugmarasiamsa Bala (strength acquired by place_", None),
 'SB_KE': ('bphs_pg0263_c01', "4. Kendradi Bala", None),
 'SB_DR': ('bphs_pg0263_c01', "5. Drekkana Bala (due to .placement in first, second or", None),
 'SB_SAP': ('bphs_pg0264_c01', "2-4. SAPTAVARGAJA BALA", '2-4'),
 'SB_NATH': ('bphs_pg0267_c01', "Nathonnatha Bala (diurnal and nocturnal strengths)", '8-9'),
 'SB_PAK': ('bphs_pg0267_c01', "Paksha Bala (Paksha:fortnight)", '8-9'),
 'SB_TRI': ('bphs_pg0267_c01', "Tribhaga Bala (strength due to day/nigbt", '8-9'),
 'SB_AY': ('bphs_pg0267_c01', "Ayana Bala (equinoctial strenglh)", '8-9'),
 'RUPA': ('bphs_pg0256_c01', "60 such units make onq Rupa", None),
 'KASHTA': ('bphs_pg0289_c01', "Reduce Ishta Phala from 60 to obtain the planet's Kashta Phala", '6'),
 'ISHTA_F': ('bphs_pg0289_c01', "multiply the products by l0 and add together", '6'),
 'YUDDHA': ('bphs_pg0942_c01', "within one degree of each other", '9'),
 'MOT': ('bphs_pg0283_c02', "Eight kinds of motions are attributed to planets. These are Vakra", None),
 'KPERM': ('bphs_jaimini_pg0030_c01', "Naisargika Karakas or permanent Lords", '13 (Notes)'),
 'DHANA': ('bphs_jaimini_pg0042_c01', "or Children, Educa. tion, Wealth and Spiritual development", '23 (Notes)'),
 'D_FRIEND': ('bphs_pg0039_c01', "ihe 2nd,4th,5th,8th,9th and l2th lords are its friends", '55 (Notes)'),
 'D_TAT': ('bphs_pg0040_c01', "The planet posited in the l0th, 4th, llth,3rd, 2nd or the l2tlt", '56'),
 'D_ENM2': ('bphs_pg0041_c01', "Should there be enmity in both manners, extreme enmity is obtained", '57-58'),
 'D_NEUT': ('bphs_pg0041_c01', "if there is friendship with enmity, then also neutrality will prevail", '57-58 (Notes)'),
 'D_XFR': ('bphs_pg0041_c01', "Friendship Extreme tnendship", '57-58 (Notes)'),
 'D_RATIO': ('bphs_pg0041_c01', "in Mooratrikona it is berert or its aispl- cious effects by one fourth", '59-60'),
 'D_COMB': ('bphs_pg0099_c01', "If a planet is eclipsed in the Sun, it proves impotcnt", None),
 'D_EXALT': ('bphs_pg0037_c02', "Taurus, Capricorn, Virgo, Cancer, Pisces and Libra", '49-50'),
 'D_DEEP': ('bphs_pg0038_c01', "in the seventh sign from tle saij exaltation sign each planet has its own debilitation", '49-50'),
 'LY_SUN': ('bphs_pg0384_c01', "in the 2nd from the Moon Sunapha yoga, in the l2th Anapha yoga", '7-10'),
 'LY_KEM': ('bphs_pg0385_c01', "Kemadruma yoga is formed", '11-13'),
 'LY_VES': ('bphs_pg0385_c01', "in the 2nd from the Sun Vesi yoga, in the l2th Vosi yoga", '1'),
 'LY_ADHI': ('bphs_pg0384_c01', "benefics occupy the 8th, 6th and ?th counted from the Moon, Adhi yoga obtains", '5'),
 'NB_NAMES': ('bphs_pg0357_c01', "Asraya yogas are Rajju, Musala and Nala yogas", '3-6'),
 'NB_32': ('bphs_pg0357_c01', "Thus these are32 in total", '3-6'),
 'NB_YUPA': ('bphs_pg0358_c02', "4 houses commencing from the ascen' dant they cause Yupa yoga", '13'),
 'NB_GOLA': ('bphs_pg0359_c01', "If all planets are in one rign Gola yoga is formed", '16-17'),
 'NB_NALA': ('saravali_pg0058_c02', "Should all the planets be in Dual Rasis, Nala Yoga is formed", '18'),
 'NB_MUS': ('saravali_pg0058_c02', "Fixed Rasis, Musala Yoga takes place and in Movable Rasis Rajju Yoga", '18'),
 'NB_ARD': ('saravali_pg0058_c01', "seven Houses commencing from a House, which is not angular to the Ascendant", '13'),
 'NK_27': ('bphs_pg0024_c01', "The said zodiac comprises of 27 asterisms commencing from Aswini", '4-6'),
 'NK_PADA': ('bphs_pg0501_c01', "consists of four padas (quarters)", None),
 'NK_LORD': ('bphs_pg0499_c01', "Beginning from Krittika the lords of Dasas (periods) are the Sun", '12-14'),
 'VIM': ('bphs_pg0499_c01', "natural life span of a human being is generally taken as 120 years", '12-14'),
 'AST': ('bphs_pg0506_c01', "are 6, 15, g, 17,10, 19, 12 and 21, in that order", None),
 'AST_C': ('bphs_pg0505_c01', "the learneds have 'ecommended the adoption of Astottari Dasa, when Rahu", '17-20'),
 'YOG': ('bphs_pg0564_c01', "Sankata are of 1,2,3,4,5,6,7 and 8 years respectively", '195-199'),
 'ABH': ('bphs_pg0508_c02', "Abhijit Nakshatra is taken ir:to consideration onlv in the Astottari", None),
 'MAR_H': ('bphs_pg0439_c01', "Out of the two (i.e 2nd and 7th) the 2nd is a powerful Maraka house", '3'),
 'MAR_T': ('bphs_pg0347_c01', "Venus will prove a killer as he is the 2nd and 7th lord", None),
 'AYU': ('bphs_pg0564_c01', "will be the same as Pindayu, Amsayu and Nisargayu", '201-202'),
 'AV_B': ('bphs_pg0123_c01', "Baala, Kumafa, YUtbna, Vriddha and Mrita", '14-16 (Notes)'),
 'AV_D': ('bphs_pg0449_c01', "nine kinds of other states, viz. Deepta, Swastha, Pramudita", '7'),
 'SG_MOV': ('bphs_pg0048_c01', "Movable are Aries, Cancer, Libra and Capricorn", '5-51 (Notes)'),
 'SG_FIX': ('bphs_pg0048_c01', "The signs Taurus, Leo, Scorpio and Aquarius are fixed or immovable", '5-51 (Notes)'),
 'SG_DUAL': ('bphs_pg0048_c01', "Gimini, Virgo, Sagittarius and Pisces are dual or cQmmon", '5-51 (Notes)'),
 'KP': ('bphs_pg0047_c01', "The time personified has his limbs as under with referencc to the 12 signs", '4-4'),
 'RA12': ('bphs_pg0047_c01', "The 12 signs of the zodiac in order are : Aries, Taurus, Gemini", '3'),
 'HC_A': ('bphs_pg0101_c01', "2nd, 5th, 8th and llth 3rd, 6th, 9th and l2th", '33-36'),
 'HC_B': ('bphs_pg0101_c01', "5th and 9th 6th, 8th and l2th 4th and 8th 3rd, 6tb, lOth and llth", '33-36'),
 'HC_K': ('bphs_pg0101_c01', "Kendras or angles : Ascendant 4th, 7th and ,10th", '33-36'),
 'VG': ('bphs_pg0383_c01', "Vargothama indicates a planct occupying the same Rasi and the same Navamsa", None),
 'V_H': ('bphs_pg0067_c01', "Half of Rasi is called Hora", '5-6'),
 'V_D3': ('bphs_pg0068_c01', "Oue third of a Rasi is called Drckkane", '7-8'),
 'V_D4': ('bphs_pg0091_c01', "fortunes from Chaturthamsa", '1-8'),
 'V_D7': ('bphs_pg0091_c01', "sons and grandsons from saptha'", '1-8'),
 'V_D9': ('bphs_pg0091_c01', "spouse from Navamsa", '1-8'),
 'V_D10': ('bphs_pg0091_c01', "power (and position) from Dasamsa", '1-8'),
 'V_D12': ('bphs_pg0091_c01', "parents from Dvadasamsa", '1-8'),
 'V_D16': ('bphs_pg0091_c01', "through conu.yances from Shodasamsa", '1-8'),
 'V_D20': ('bphs_pg0091_c01', "worship from Vimsamsa", '1-8'),
 'V_D24': ('bphs_pg0091_c01', "ing from Chathur Vimsamsa", '1-8'),
 'V_D27': ('bphs_pg0091_c01', "strength and weakness from Bhamsa", '1-8'),
 'V_D30': ('bphs_pg0091_c01', "effects from Trimsamsa", '1-8'),
 'V_D40': ('bphs_pg0091_c01', "auspicious and inauspicious effects from Khavedamsa", '1-8'),
 'V_D4560': ('bphs_pg0091_c01', "all indications from both Aksha- vedamsa and Shashtiamsa", '1-8'),
 'V_GRP': ('bphs_pg0087_c01', "Dasa Varga (10 divisions considered) and Shodasa yarga", '42-53'),
 'VIMS': ('bphs_pg0094_c01', "Vimsopaka strength is the 20 point strength obta-", '17-19 (Notes)'),
 'SPL_B': ('bphs_pg0061_c01', "Bhqva lagm, Hora Iagna and Ghatika Lagna", '1'),
 'SPL_K': ('bphs_pg0390_c01', "the native will become a king", '12'),
 'MP': ('bphs_pg0916_c01', "give rise to Ruchaka, Bhadra, Hamsa, Malarrya and Sasa yo.gas respectively", '1-2'),
 'PH_AMALA': ('phaladeepika_pg0091_c01', "When benefics occupy the 10th house counted from the Lagna or the Moon", '19-20'),
 'PH_SANKHA': ('phaladeepika_pg0099_c01', "If the lords of a Kendra and a Kona h© similarly placed", '37'),
 'PH_SRI': ('phaladeepika_pg0094_c01', "If Venus, the lord of the 9th and Mercury be similarly placed, the Yoga is called", '28'),
 'PH_SARAS': ('phaladeepika_pg0093_c01', "Jupiter be also in his exaltation, his own or a friendly house", '26'),
 'PH_LAK': ('phaladeepika_pg0092_c01', "If the lord of the 9th and Venus be posited in their own or exaltation houses", '21-25'),
 'PH_DUS': ('phaladeepika_pg0105_c01', "lords of the several Bhavas from the Lagna onwards occupy the 6th, 3th oi 12th", '57'),
 'PH_SAK': ('phaladeepika_pg0089_c01', "The Moon in the 12th, 8th or 6th houso from Jupiter causes", '14'),
 'PH_MBH': ('phaladeepika_pg0089_c01', "the Sun, the Moon and the Lagna are in odd signs", '14'),
 'PH_VAS': ('phaladeepika_pg0091_c01', "whether reckoned from the Lagna or the Moon, the resulting Yoga is termed", '19'),
 'B36_GAJ': ('bphs_pg0367_c01', "Shoutd Jupiter be in an angle from the ascendant or from the Moon", '3-4'),
 'B36_AMA': ('bphs_pg0369_c01', "If there be exclusively a benefic in the l0th from the ascendant or the Moon", '5-6'),
 'B36_SUB': ('bphs_pg0365_c01', "If there be a benefic in the ascendant, Subha yoga is produced", '1-2'),
 'B36_PAR': ('bphs_pg0371_c01', "Benefics in angles will produce Parvatha loga, as the 7th and 8th are vacant", '7-8'),
 'B36_KAH': ('bphs_pg0372_c01', "the 4th lord and Jupiter be in mutual angles", '9-10'),
 'B36_KAH2': ('bphs_pg0372_c02', "of the ninth and fourth are in mutual angles", '9-10 (Notes)'),
 'B36_CHA': ('bphs_pg0373_c01', "ascendant lord is exalted in an angle and be aspected by Jupiter", '11-12'),
 'B36_SAN': ('bphs_pg0373_c02', "lords of the 5th and 6th are in mutual angles", '13-14'),
 'B36_BHE': ('bphs_pg0374_c01', "BHERI YOGA", '15-16'),
 'B36_MRI': ('bphs_pg0374_c01', "MRIDANGA YOGA", '17'),
 'B36_SRI': ('bphs_pg0374_c01', "If the ?th lord ie in the lOth while the lOth lord is exalted", '18'),
 'B36_MAT': ('bphs_pg0375_c01', "MATSYA YOGA", '21-22'),
 'B36_KUR': ('bphs_pg0376_c01', "KOORMA YOGA", '23-24'),
 'B36_KHA': ('bphs_pg0376_c01', "an exchange irf signs between the lords of the 2nd and the 9rh", '25-26'),
 'B36_LAK': ('bphs_pg0376_c01', "If the 9th lord is in an angte identical with his Moolatrikona sign", '27-28'),
 'B36_KAL': ('bphs_pg0377_c01', "Jupiter be in the 2nd or the 5th and be aspected by Mercury and Venus", '31-32'),
 'B36_KDM': ('bphs_pg0377_c01', "Note the foilowing four planets", '33-34'),
 'B36_LAG': ('bphs_pg0382_c01', "Should benefics be in the Zth and the 8th counted from the ascendant", '37'),
 'SAR_PUSH': ('saravali_pg0142_c01', "Moon Sign Lord and the Ascendant Lord be with strength", '145'),
 'JA_ARG': ('bphs_jaimini_pg0023_c01', "The fourth, second and eleventh places, (or planets in them)", '5'),
 'JA_ARG9': ('bphs_jaimini_pg0023_c01', "The houses or planets in thribonas (5 and 9) similarly influence the Argala", '9'),
 'JA_VIR': ('bphs_jaimini_pg0023_c01', "Planets in the tenth, twelfth and third from Argala cause obstruction", '7'),
 'JA_UPA': ('bphs_jaimini_pg0124_c01', "How calculate the Upapada Lagna. Take the 12th from -Lagoa", None),
 'JA_KAR': ('bphs_pg0088_c01', "means the Navamsa occupied by Atma Karaka i.e. Kara- kamsa ascendant", '52 (Notes)'),
 'JA_STH': ('bphs_jaimini_pg0182_c01', "In the Sthira or fixed sign Dasa, the movable sign Dasa will be 7", '3'),
 'JA_DRIG': ('bphs_jaimini_pg0202_c01', "Drigdasas are formed commencing with the 9th from Lagna", '21'),
 'JA_SHO': ('bphs_jaimini_pg0157_c01', "Trikona Dasas are what are technically called Shoola Das", '38 (Notes)'),
 'JA_NIR': ('bphs_jaimini_pg0200_c01', "Sbt>ola Dasas are marked as death inflicting", None),
 'JA_MAH': ('bphs_jaimini_pg0160_c01', "The lor 1 of 8th home from Atmakiraka goes under the name of Maheswara", '44'),
 'JA_RUD': ('bphs_jaimini_pg0158_c01', "If the two Rudris become evil, death will come in the first Shoola Dasa", None),
 'JA_BRA': ('bphs_jaimini_pg0162_c01', "Find out which is the stronger of the two Rasis, Lagna and Saptami or 7th", '47'),
 'JC11': ('bphs_jaimini_pg0029_c01', "gets the highest number of degrees becomes the Atmakaraka", '11'),
 'JC13': ('bphs_jaimini_pg0035_c01', "The planet who is next in kalas or degrees to the Atmakaraka will become Amaiyalcaraka", '13'),
 'JC14': ('bphs_jaimini_pg0036_c01', "highest number of degrees next to Amatyakaraka becomes Bhrairuha", '14'),
 'JC15': ('bphs_jaimini_pg0036_c01', "next to Bhratrukaraka becomes lord of the mother or Matrakaraka", '15'),
 'JC16': ('bphs_jaimini_pg0037_c01', "next in power in degrees to Matrnkaraka becomes the lord of the children", '16'),
 'JC17': ('bphs_jaimini_pg0038_c01', "Gnathikaraka or Lord of the cousins", '17'),
 'JC18': ('bphs_jaimini_pg0038_c01', "becomes Darakaraka or Lord of wife", '18'),
 'B32_8': ('bphs_pg0317_c02', "8. Stree Karaka (next to Gnati Karaka in longitude)", '13-17 (Notes)'),
 'JS_sun': ('bphs_jaimini_pg0042_c01', "Ravi—Atmaprabhavasakti or soul force, reputation, vitality and father", '23 (Notes)'),
 'B32_YK': ('bphs_pg0320_c01', "Yogakarakas (or mutual co-workers)", '25-30'),
 'B32_YK2': ('bphs_pg0320_c01', "if they are in nrutual ansles identical with own signs, exaltation, or", '25-30'),
 'AV_BIND': ('bphs_pg0858_c01', "Karana is inauspicious while Sthana (rvn) is auspicious", '69'),
 'AV_BIND2': ('bphs_pg0858_c01', "a bindu or dot ( 0 ) and Sthana (ttn) by a rekha", '69'),
 'AV_8': ('bphs_pg0836_c01', "The meaning of Ashtakavarga is literally the group of", '13-15 (Notes)'),
 'AV_TR': ('bphs_pg0837_c02', "he wifl yield unfavourablc resuls", '16-19 (Notes)'),
 'AV_TRI': ('bphs_pg0859_c01', "Trikona Shbdhana (rectification) irthe $shtakavarga", None),
 'AV_EKA': ('bphs_pg0867_c01', "Ekadhipatl a Shodhana in the 'Ashtakavarga Scheme", None),
 'AV_SARVA': ('bphs_pg0889_c01', "Aggregrhtional Ashtakavarga", None),
 'BDH': ('bphs_pg0598_c01', "moveable sign is its Badhaka house", '22'),
 'GAN': ('bphs_pg0111_c01', "The last Navamsas of Cancer, of Scorpio and of lisces are called as Ganda", None),
 'ABH_K': ('bphs_pg0508_c02', "Abhijit Nakshatra is taken ir:to consideration onlv in the Astottari", None),
 'YAMAGH': ('bphs_pg0044_c01', "Ardha Prahara, Yamaghanlakd, Mrityu, Kala and Gulika are the 5 Kala Velas", None),
 'RITU': ('bphs_pg0036_c01', "Vasanta, Greeshma,", '45-46') if False else ('bphs_pg0036_c01', "Varsha, Sarad, Hemanta and Sisira are the six Ritus", '45-46'),
 'TITHI': ('jataka_parijata_pg0616_c01', "Each lunar month conststs of thirty tithis", '29-30'),
 'KARANA': ('jataka_parijata_pg0649_c01', "(Karana) called (Chatushpada), will have a multitude of misfortunes", '103'),
}
def E_(*keys):
    return [ev(*G[k]) for k in keys]
def cit(keys):
    seen = []
    for k in keys:
        c = cite(G[k][0], '', G[k][2])
        if c not in seen:
            seen.append(c)
    return ' ; '.join(seen)

A = {}   # term -> dict(state, sup, keys, inf, note, act, q, group)
def put(term, state, keys=(), group='', inf=None, note=None, act=None, q=None):
    assert term in rows and term not in A, term
    sup = {'sourced_fact': 'FACT', 'sourced_inference': 'INFERENCE', 'contradicted': 'CONTRADICTS', 'unsourced_marked': 'NONE',
           'not_a_classical_claim': 'NONE', 'existing_citation_unverifiable': 'NONE', 'text_not_held': 'NONE'}[state]
    if act is None:
        act = {'sourced_fact': 'recite', 'sourced_inference': 'recite', 'contradicted': 'acharya', 'unsourced_marked': 'mark_unsourced'}.get(state, 'none')
    A[term] = dict(state=state, sup=sup, keys=list(keys), group=group, inf=inf, note=note, act=act, q=q)
def SF(terms, keys, group, note=None):
    for t in terms.split():
        put(t, 'sourced_fact', keys, group, note=note)
def SI(terms, keys, group, inf, note=None):
    for t in terms.split():
        put(t, 'sourced_inference', keys, group, inf=inf, note=note)
def NC(terms, group, note):
    for t in terms.split():
        put(t, 'not_a_classical_claim', (), group, note=note)
def UM(terms, group, note):
    for t in terms.split():
        put(t, 'unsourced_marked', (), group, note=note)
def EU(terms, group, note='Doctrinal definition at a held-text chapter grain; not individually checked in this pass (no supporting chunk searched/read).'):
    for t in terms.split():
        put(t, 'existing_citation_unverifiable', (), group, note=note)
def CT(term, keys, group, q, note=None):
    put(term, 'contradicted', keys, group, note=note, q=q)

# ============ BPHS Ch.1/2/26/27/3
NC('swakshetra', 'ch1-vocab', 'Plain definition of "own sign"; no doctrinal assertion.')
SF('benefic malefic', ['BEN'], 'ch2-benefic-malefic', "Natural malefics (Sun, Saturn, Mars, waning Moon, Rahu, Ketu) vs the rest are benefics: Ch.3 sloka 11, not Ch.2.")
NC('graha_bheda', 'ch2-vocab', 'Generic heading "classification of grahas by nature".')
NC('drishti graha_drishti', 'ch26-vocab', 'Generic definitions of aspect.')
SI('ardha_drishti pada_drishti poorna_drishti', ['ASP'], 'ch26-aspect-fractions', "Printed fractions are OCR-garbled ('l14, 112, 3l4, fult' = 1/4, 1/2, 3/4, full); read as quarter/half/three-quarter/full aspect.")
SF('sthanabala', ['SB_S'], 'ch27-shadbala-components'); SF('digbala_g digbala_term', ['SB_D'], 'ch27-shadbala-components')
SF('kalabala', ['SB_K'], 'ch27-shadbala-components'); SF('cheshtabala', ['SB_C'], 'ch27-shadbala-components')
SF('naisargikabala', ['SB_N'], 'ch27-shadbala-components'); SF('drikbala', ['SB_R'], 'ch27-shadbala-components')
SF('shadbala_term', ['SB_ALL'], 'ch27-shadbala-components'); SF('uchchabala', ['SB_U'], 'ch27-shadbala-components')
SF('ojhayugmabala', ['SB_O'], 'ch27-shadbala-components'); SF('kendradibala', ['SB_KE'], 'ch27-shadbala-components')
SF('drekkanabala', ['SB_DR'], 'ch27-shadbala-components'); SF('saptavargajabala', ['SB_SAP'], 'ch27-shadbala-components')
SF('nathonnata_bala', ['SB_NATH'], 'ch27-shadbala-components'); SF('paksha_bala', ['SB_PAK'], 'ch27-shadbala-components')
SF('tribhaga_bala', ['SB_TRI'], 'ch27-shadbala-components')
SI('ayana_bala', ['SB_AY'], 'ch27-shadbala-components', "Held text calls it 'equinoctial strength' and computes it from Kranti (declination) - the row's 'Declination strength' is that computation's input.")
SF('rupa virupa', ['RUPA'], 'ch27-units', "Chunk (Ch.26 text, p.257): 'Virupa' denotes Shashtiamsas/Kalas and 60 such units make one Rupa.")
SF('kashtaphala', ['KASHTA'], 'ch27-ishta-kashta', "Ch.28 sloka 6 (not Ch.27).")
CT('ishtaphala', ['ISHTA_F'], 'ch27-ishta-kashta', "BPHS Ch.28 sloka 6 (Santhanam) gives Ishta phala as half the sum of (Uchcha rasmi-1)x10 and (Cheshta rasmi-1)x10 - an arithmetic mean, not sqrt(uccha x cheshta) as the glossary states. Which formula is canonical for the platform's ishta/kashta phala?",
   note="Definition 'sqrt(uccha x cheshta) capacity' does not match the held formula.")
NC('ishta_term kashta_term kashtaphala_bala karaka_term', 'ch27-vocab', 'Generic definitions of benefic/malefic capacity and significator.')
SF('dhana_karaka', ['DHANA'], 'ch27-karaka', "Jaimini notes (Naisargika karakas): Guru - Dhana/wealth.")
SF('sthira_karaka', ['KPERM'], 'ch27-karaka', "Jaimini notes: 'Naisargika Karakas or permanent Lords'.")
SF('retrograde', ['MOT'], 'ch27-motion', "Vakra (retrogression) is one of eight motions that determine Cheshta bala (Ch.27 sloka 'Eight kinds of motions').")
SF('graha_yuddha', ['YUDDHA'], 'ch27-yuddha', "Ch.? planetary-war sloka (bphs_pg0942_c01) - 'within one degree'; row is cited to Ch.27.")
UM('yuddha_bala bhava_bala', 'ch27-unfound', "Term not found in the held BPHS text by direct search ('yuddha bala', 'bhava bala'); value (definition) unchanged.")
# ---- Ch.3
SI('adhimitra', ['D_XFR'], 'ch3-dignity', "Compound-relationship table: friendship + friendship = 'extreme friendship' (OCR 'tnendship').")
SF('adhishatru', ['D_ENM2'], 'ch3-dignity'); SF('combust', ['D_COMB'], 'ch3-dignity')
SI('mitra shatru', ['D_FRIEND'], 'ch3-dignity', "Friend/enemy of a planet's sign lord derived from sloka 55 (2/4/5/8/9/12 lords are friends, the rest enemies).")
SF('naisargika_mitra', ['D_FRIEND'], 'ch3-dignity'); SF('tatkalika_mitra', ['D_TAT'], 'ch3-dignity'); SF('sama', ['D_NEUT'], 'ch3-dignity')
SF('moolatrikona', ['D_RATIO'], 'ch3-dignity', "Moolatrikona loses only one quarter of exaltation's beneficence (sloka 59-60).")
SI('neecha', ['D_DEEP'], 'ch3-dignity', "Debilitation = the 7th sign from exaltation, same degree (sloka 49-50).")
SF('uchcha', ['D_EXALT'], 'ch3-dignity')
EU('gulika_term', 'ch3-gulika', "Gulika-as-Saturn's-portion not individually checked (BPHS p.44 note says Gulika and Mandi are one point).")
UM('neechabhanga', 'ch3-neechabhanga', "Held BPHS gives only an example horoscope mentioning 'Neechabhanga' (p.230); the cancellation conditions are not stated in the held text.")
# ---- Ch.30 (actually Ch.37/38)
SF('sunapha_term anapha_term durudhara_term', ['LY_SUN'], 'ch30-lunar-yogas', "Actual chapter: 37 (Lunar Yogas) sloka 7-10; also Saravali p.38.")
SF('kemadruma_term kemadruma_yoga', ['LY_KEM'], 'ch30-lunar-yogas', "Ch.37 sloka 11-13.")
SF('veshi voshi vesi_yoga vasi_yoga ubhayachari_term', ['LY_VES'], 'ch30-solar-yogas', "Ch.38 (Solar Yogas) sloka 1: 2nd from Sun = Vesi, 12th = Vosi, both = Ubhayachari (planet other than the Moon).")
EU('parivartana', 'ch32-parivartana')
UM('functional_benefic', 'ch34-fbm', "Functional benefic/malefic by lagna lordship is discussed in Ch.34 commentary but the exact label/definition was not located in the held text.")
CT('yogakaraka', ['B32_YK', 'B32_YK2'], 'ch34-yogakaraka', "In the held BPHS (Ch.32 sloka 25-30) 'Yogakaraka' means planets in mutual angles with exaltation/own/friendly dignity ('mutual co-workers'), not 'a graha lording both a kendra and a trikona' (the glossary's Ch.34 meaning). Should the glossary state the Ch.32 sense, the later lordship sense (with a text-free note), or both?")
# ---- Ch.35 nabhasa
SF('nabhasa', ['NB_32'], 'ch35-nabhasa', "Thirty-two Nabhasa yogas (Ch.35 sloka 3-6).")
SF('rajju_yoga musala_yoga nala_yoga', ['NB_NALA', 'NB_MUS'], 'ch35-nabhasa', "Rajju=movable, Musala=fixed, Nala=dual: stated clearly in Saravali p.58; the BPHS Ch.35 sloka 7-8 text is OCR-scrambled in the held copy.")
SF('yupa_yoga', ['NB_YUPA'], 'ch35-nabhasa'); SF('gola_yoga', ['NB_GOLA'], 'ch35-nabhasa')
SF('ardhachandra', ['NB_ARD'], 'ch35-nabhasa', "Definition is in Saravali p.58 (the BPHS Ch.35 chunk gives only the name); wording 'seven successive houses from a non-angular house'.")
# ---- Ch.36
SI('adhi_term adhiyoga', ['LY_ADHI'], 'ch36-adhi', "Ch.37 sloka 5: benefics in the 8th, 6th and '?th' (OCR) from the Moon; 7th read in.")
UM('chandra_mangala', 'ch36-unfound', "'Chandra-Mangala' not found in the held BPHS (Ch.36/37) text.")
# ---- Ch.39/41
UM('neechabhanga_rajayoga', 'ch39-unfound', "Neechabhanga raja yoga conditions not stated in the held text (only an example mention, p.230).")
EU('dharma_karmadhipati', 'ch39-raja')
NC('rajayoga dhanayoga', 'ch39-vocab', 'Generic "power/wealth combination" labels.')
# ---- Ch.4
SF('nakshatra_lord', ['NK_LORD'], 'ch4-nakshatra', "Vimshottari lords per nakshatra (Ch.46 sloka 12-14).")
SF('nakshatra_term', ['NK_27'], 'ch4-nakshatra', "Ch.3 sloka 4-6.")
SF('pada_nakshatra', ['NK_PADA'], 'ch4-nakshatra', "Ch.46 notes.")
NC('nakshatra_p pada_p', 'ch4-vocab', 'Duplicate vocabulary entries (panchanga category).')
# ---- Ch.43/45/46..
SF('amsa_ayu pinda_ayu nisarga_ayu', ['AYU'], 'ch43-ayu', "The three methods are named Pindayu, Amsayu, Nisargayu (Ch.46 sloka 201-202); existence only.")
NC('ayurdaya', 'ch43-vocab', 'Generic "computed life-span".')
SF('maraka_house', ['MAR_H'], 'ch43-maraka'); SF('maraka_term', ['MAR_T'], 'ch43-maraka')
SF('baladi_avastha', ['AV_B'], 'ch45-avastha'); SF('deeptadi_avastha', ['AV_D'], 'ch45-avastha', "Printed '9 other states'; only eight names legible.")
NC('graha_avastha', 'ch45-vocab', 'Generic "condition of a graha".')
SF('vimshottari_term', ['VIM'], 'ch46-dasha')
NC('antardasha mahadasha pratyantardasha balance_of_dasha', 'ch46-vocab', 'Standard dasha-level vocabulary.')
EU('pranadasha sookshmadasha naisargika_dasha kala_chakra_gochara kalachakra_term', 'ch46-49-dasha-unchecked')
SI('ashtottari_term', ['AST', 'AST_C'], 'ch48-ashtottari', "108 = 6+15+8+17+10+19+12+21 (sum of the eight periods); 'conditional' = the Rahu-position condition of sloka 17-20.")
SI('yogini_term', ['YOG'], 'ch50-yogini', "36 = 1+2+...+8 years of the eight Yogini dasas.")
EU('gochara gocharaphala vedha', 'ch55-transit-unchecked')
# ---- Ch.6
SF('chara_rashi', ['SG_MOV'], 'ch6-signs', "Actual chapter 4 Notes (sign classification)."); SF('sthira_rashi', ['SG_FIX'], 'ch6-signs'); SF('dvisvabhava', ['SG_DUAL'], 'ch6-signs')
SF('kalapurusha', ['KP'], 'ch6-signs', "Ch.4 sloka 4-4(1/2): limbs of Kalapurusha.")
NC('lagna rasi yuti avayava', 'ch6-vocab', 'Generic structural vocabulary (ascendant, sign, conjunction, body part of a sign).')
# ---- Ch.66
SF('ashtakavarga_term', ['AV_8'], 'ch66-av', "Notes under sloka 13-15: group of 8 things (7 planets + Ascendant).")
CT('bindu', ['AV_BIND', 'AV_BIND2'], 'ch66-bindu-rekha', "In BPHS Ch.66 (Santhanam sloka 69 and 13-15) the bindu/dot (Karana) is INAUSPICIOUS and the rekha/line (Sthana) AUSPICIOUS. The glossary defines 'bindu: a benefic point' and 'rekha: a malefic mark' (reversed), and reference_constants labels benefic houses as 'bindu-houses'. Which terminology is canonical: the held classical one (rekha = benefic) or the modern bindu = benefic usage?")
CT('rekha', ['AV_BIND', 'AV_BIND2'], 'ch66-bindu-rekha', "Same as bindu: held BPHS says rekha (Sthana) is auspicious, glossary says 'A malefic mark'.")
SI('ashtakavarga_transit', ['AV_TR'], 'ch66-av', "Transit through dot houses is unfavourable (notes under 16-19); 'read by bindu count' is the modern reading of that rule.")
SI('trikona_shodhana', ['AV_TRI'], 'ch66-av-shodhana', "Ch.67 is 'Trikona Shodhana' (first reduction); ordinal 'first' from chapter order 67 then 68.")
SI('ekadhipatya_shodhana', ['AV_EKA'], 'ch66-av-shodhana', "Ch.68 is 'Ekadhipatya Shodhana' (second reduction by chapter order).")
SI('sarvashtakavarga', ['AV_SARVA'], 'ch66-av', "Ch.72 'Aggregational Ashtakavarga' is the aggregate chart.")
NC('bhinnashtakavarga', 'ch66-vocab', 'Name for the per-planet chart (naming only).')
EU('kakshya kakshya_transit shodhya_pinda', 'ch66-av-unchecked')
# ---- Ch.7
SF('hora_div', ['V_H'], 'ch7-varga-names'); SF('drekkana_div', ['V_D3'], 'ch7-varga-names')
SF('chaturthamsa', ['V_D4'], 'ch7-varga-names', "Sloka 1-8 names the use; one-fourth in sloka 9.")
SF('saptamsa', ['V_D7'], 'ch7-varga-names'); SF('dwadasamsa', ['V_D12'], 'ch7-varga-names'); SF('shodasamsa', ['V_D16'], 'ch7-varga-names')
SF('vimsamsa', ['V_D20'], 'ch7-varga-names'); SF('chaturvimsamsa', ['V_D24'], 'ch7-varga-names'); SF('bhamsa', ['V_D27'], 'ch7-varga-names')
SF('trimsamsa', ['V_D30'], 'ch7-varga-names'); SF('khavedamsa', ['V_D40'], 'ch7-varga-names'); SF('akshavedamsa', ['V_D4560'], 'ch7-varga-names')
SI('navamsa', ['V_D9'], 'ch7-varga-names', "'spouse from Navamsa' stated; the gloss 'dharma' is not.")
SI('dasamsa', ['V_D10'], 'ch7-varga-names', "'power (and position) from Dasamsa' read as career.")
SI('shashtiamsa', ['V_D4560'], 'ch7-varga-names', "'all indications' stated; 'past-karma' gloss is not.")
SF('shadvarga saptavarga dashavarga shodashavarga', ['V_GRP'], 'ch7-varga-groups', "Sloka 42-53 (Ch.6) defines the 6/7/10/16-division groups.")
SF('vimsopaka', ['VIMS'], 'ch7-varga-groups')
SF('apoklima panapara', ['HC_A'], 'ch7-house-classes', "Ch.7 sloka 33-36."); SF('kendra', ['HC_K'], 'ch7-house-classes')
SF('dusthana trika upachaya', ['HC_B'], 'ch7-house-classes', "Evil/Trika = 6,8,12; Upachaya = 3,6,10,11 (Ch.7 sloka 33-36).")
put('trikona', 'unsourced_marked', ['HC_B'], 'ch7-house-classes', note="Held text names only the 5th and 9th as Kona/trine ('5th and 9th from the ascendant are known by the name Kona'); the 1st house in the row's '1st/5th/9th' is not named a Kona in the chunk.")
SF('vargottama', ['VG'], 'ch7-dignity')
SI('bhava_lagna', ['SPL_B'], 'ch7-special-lagnas', "Existence of Bhava/Hora/Ghatika Lagna stated in the special-ascendants chapter (Ch.5).", note="Gloss 'special lagna' only.")
SI('ghati_lagna', ['SPL_B', 'SPL_K'], 'ch7-special-lagnas', "Existence stated in Ch.5; 'for power' read from Ch.39 sloka 12 (aspect on natal/Hora/Ghatika Lagna makes one a king).")
UM('hora_lagna', 'ch7-special-lagnas', "Hora Lagna exists (Ch.5) but its gloss 'a special lagna for wealth' is not stated in the held text.")
EU('kendra_relation trine_relation vargottama_pada', 'ch7-relations-unchecked')
NC('bhava bhava_madhya bhava_sandhi', 'ch7-vocab', 'Generic house vocabulary.')
# ---- Ch.75, 9, 91
SF('pancha_mahapurusha ruchaka_term bhadra_term hamsa_term malavya_term sasa_term', ['MP'], 'ch75-mahapurusha', "Mars, Mercury, Jupiter, Venus, Saturn in own/exaltation sign in a kendra = Ruchaka, Bhadra, Hamsa, Malavya, Sasa (Ch.75 sloka 1-2).")
NC('arishta balarishta', 'ch9-vocab', 'Generic affliction vocabulary (Ch.9 deals with balarishta).')
NC('daana mantra upaya', 'ch91-vocab', 'Generic remedy vocabulary.')
# ---- Phaladeepika
SF('amala', ['PH_AMALA'], 'phaladeepika-yogas', "Same definition in BPHS Ch.36 sloka 5-6.")
SF('bheri bheri_yoga', ['B36_BHE'], 'phaladeepika-yogas', "Held Phaladeepika has no Bheri yoga (0 hits); BPHS Ch.36 sloka 15-16 names it (named auspicious yoga). Cite BPHS Ch.36, not Phaladeepika.")
SF('mridanga mridanga_yoga', ['B36_MRI'], 'phaladeepika-yogas', "Held Phaladeepika has no Mridanga yoga (0 hits); BPHS Ch.36 sloka 17. Cite BPHS Ch.36.")
SF('chamara', ['B36_CHA'], 'phaladeepika-yogas', "Definition from BPHS Ch.36 sloka 11-12 (lagna lord exalted in an angle, aspected by Jupiter); Phaladeepika's version differs (benefic in lagna and lagna lord well placed).")
SF('sankha_yoga shankha', ['B36_SAN'], 'phaladeepika-yogas', "BPHS Ch.36 sloka 13-14 matches the row (lords of 5th and 6th in mutual angles, lagna lord strong). The held Phaladeepika Adh. VI sloka 37 defines Sankha differently (lords of a kendra and a kona conjunct in an auspicious bhava) - cite BPHS, not Phaladeepika.")
SF('srinatha', ['B36_SRI'], 'phaladeepika-yogas', "BPHS Ch.36 sloka 18 matches the row; held Phaladeepika Adh. VI sloka 28 gives a different Srinatha (Venus, 9th lord and Mercury in kendra/trikona in dignity).")
SI('harsha sarala vimala', ['PH_DUS'], 'phaladeepika-viparita', "Phaladeepika Adh. VI sloka 57: when lords of the bhavas occupy 6/8/12 twelve yogas arise, Harsha=6th bhava, Sarala=8th, Vimala=12th (by list position); the row's '6th/8th/12th-lord viparita raja yoga' reading is an interpretation of that list.")
UM('viparita_rajayoga', 'phaladeepika-viparita', "'Viparita' as a yoga name is not found in the held Phaladeepika/BPHS (only 'vipareeta argala/vedha' in BPHS Ch.31).")
SF('lakshmi_yoga', ['B36_LAK'], 'phaladeepika-yogas', "BPHS Ch.36 sloka 27-28: 9th lord in an angle in own/moolatrikona/exaltation, lagna lord strong; Phaladeepika Adh. VI sloka 21-25 adds Venus - both are 9th-lord wealth/fortune yogas.")
# ---- Saravali
SI('gajakesari', ['B36_GAJ'], 'saravali-yogas', "Not in the held Saravali; BPHS Ch.36 sloka 3-4 (Jupiter in an angle from lagna or Moon, with a benefic's conjunction/aspect) - row's 'Jupiter-Moon kendra' is the common simplified form.")
SI('kahala', ['B36_KAH', 'B36_KAH2'], 'saravali-yogas', "Not in the held Saravali; BPHS Ch.36 sloka 9-10 main text: 4th lord and Jupiter in mutual angles, lagna lord strong; the '4th/9th-lord' form is the Notes' Tamil-edition variant.")
SI('kalanidhi', ['B36_KAL'], 'saravali-yogas', "Not in the held Saravali; BPHS Ch.36 sloka 31-32: Jupiter in the 2nd or 5th aspected by Mercury and Venus (the row omits the 2nd/5th placement and says 'with/aspected').")
SI('khadga', ['B36_KHA'], 'saravali-yogas', "Not in the held Saravali; BPHS Ch.36 sloka 25-26: exchange of signs between 2nd and 9th lords with lagna lord in angle/trine (wealth, fortune).")
SF('kurma', ['B36_KUR'], 'saravali-yogas', "Name exists as Koorma yoga in BPHS Ch.36 sloka 23-24 (not in the held Saravali).")
SF('matsya', ['B36_MAT'], 'saravali-yogas', "Name exists as Matsya yoga in BPHS Ch.36 sloka 21-22 (not in the held Saravali).")
SI('parvata', ['B36_PAR'], 'saravali-yogas', "Not in the held Saravali; BPHS Ch.36 sloka 7-8 main text: benefics in angles with the 7th and 8th vacant/benefic-only; the row's 'empty dusthanas' matches only one of the Notes' variants.")
SI('pushkala', ['SAR_PUSH'], 'saravali-yogas', "Saravali sloka 145: Moon-sign lord and lagna lord strong, in an angle in a close friend's sign, aspecting the lagna - row's 'lagna lord with lord of Moon sign' omits the strength/angle conditions.")
SI('saraswati', ['PH_SARAS'], 'saravali-yogas', "Not in the held Saravali; Phaladeepika Adh. VI sloka 26 defines Saraswati (Jupiter, Venus, Mercury placement with Jupiter in dignity).")
SI('vasumati', ['PH_VAS'], 'saravali-yogas', "Not in the held Saravali; Phaladeepika Adh. VI sloka 19 'Vasumat': benefics in upachayas from Lagna or Moon.")
UM('dhwaja', 'saravali-yogas', "Dhwaja yoga not found in the held Saravali, BPHS or Phaladeepika.")
# ---- Jaimini
SF('atmakaraka_j atmakaraka_term', ['JC11'], 'jaimini-chara-karakas'); SF('chara_karaka chara_karaka_j', ['JC11', 'KPERM'], 'jaimini-chara-karakas', "Chart-dependent (degree-ranked) vs permanent karakas contrasted in Su.13 notes.")
SF('amatyakaraka_term', ['JC13'], 'jaimini-chara-karakas'); SI('amatyakaraka_j', ['JC13'], 'jaimini-chara-karakas', "Rank 2 stated; 'career' read from the notes' 'Minister or Councillor'.")
SI('bhratrikaraka', ['JC14'], 'jaimini-chara-karakas', "Rank 3 by counting the chain; gloss 'siblings/guru': only brothers stated.")
SI('matrikaraka', ['JC15'], 'jaimini-chara-karakas', "Rank 4 by counting the chain.")
SI('putrakaraka', ['JC16'], 'jaimini-chara-karakas', "Rank 5 by counting the chain (7-scheme).")
SI('gnatikaraka', ['JC17'], 'jaimini-chara-karakas', "Rank 6 by counting the chain; gloss 'kin/obstacles': only cousins stated.")
SI('darakaraka', ['JC18'], 'jaimini-chara-karakas', "Rank 7 by counting the chain (7-scheme).")
SF('strikaraka', ['B32_8'], 'jaimini-chara-karakas', "Supported by BPHS Ch.32 (8-karaka scheme: 'Stree Karaka (next to Gnati Karaka)' is the 8th), NOT by the held Jaimini Sutras; cite BPHS Ch.32. (Stree = Dara there; see the reference_karakas strikaraka acharya question.)")
SI('chara_atmakaraka', ['JC11'], 'jaimini-chara-karakas', "'Movable soul significator' is the platform's name for the degree-ranked Atmakaraka.")
SI('sthira_atmakaraka', ['JS_sun'], 'jaimini-chara-karakas', "Naisargika karaka of 'soul force' is the Sun (Jaimini notes), so the fixed soul significator = Sun.")
SF('sthira_karaka_j', ['KPERM'], 'jaimini-chara-karakas')
SF('argala argala_j', ['JA_ARG', 'JA_ARG9'], 'jaimini-argala', "Su.5 gives the 4th, 2nd and 11th; Su.9 adds the trine (5th/9th) houses - the row's 2/4/11/5.")
SF('virodhargala virodhargala_j', ['JA_VIR'], 'jaimini-argala', "Su.7: planets in the 10th, 12th and 3rd obstruct the argala.")
SF('upapada upapada_j', ['JA_UPA'], 'jaimini-lagnas', "Upapada = the arudha of the 12th (worked example: 'Take the 12th from Lagna').")
SF('karakamsa karakamsa_j', ['JA_KAR'], 'jaimini-lagnas', "BPHS Ch.6 notes define Karakamsa/Swamsa as the Navamsa occupied by Atmakaraka (Jaimini translation pages describe the same).")
SF('swamsa swamsa_j', ['JA_KAR'], 'jaimini-lagnas')
SI('karakamsa_lagna', ['JA_KAR'], 'jaimini-lagnas', "Lagna reckoned from the Karakamsa sign (Ch.33 'Effects of Karakamsa').")
SF('sthira_dasha sthira_dasha_j', ['JA_STH'], 'jaimini-dasha', "Su.3 (Sthira dasa: movable/fixed/dual signs give 7/8/9 years).")
SF('drig_dasha', ['JA_DRIG'], 'jaimini-dasha')
SF('trikona_dasha shoola_dasha', ['JA_SHO'], 'jaimini-dasha', "Held notes: 'Trikona Dasas are what are technically called Shoola Dasas'; shoola dashas are marked death-inflicting (Su.16 notes).")
SF('niryana_dasha', ['JA_NIR'], 'jaimini-dasha')
SF('maheshwara', ['JA_MAH'], 'jaimini-longevity', "Su.44: lord of the 8th from the Atmakaraka = Maheswara (Jaimini longevity chapter).")
SF('rudra_j', ['JA_RUD'], 'jaimini-longevity', "Rudra rasis/'Rudris' used with the Shoola Dasa death timing (Su.39-45).")
SI('brahma_j brahma_dasha', ['JA_BRA'], 'jaimini-longevity', "Brahma is a longevity-determining planet (Su.47-52); 'Brahma dasa' as a dasa name is listed in the contents, definition not individually read.")
UM('kevala yogada', 'jaimini-unfound', "Term not found in the held Jaimini Sutras text by direct search (0 hits).")
EU('chara_dasha chara_dasha_j arudha_j arudha_lagna arudha_lagna_j darapada pada_j pada_jaimini rashi_drishti rashi_drishti_j trikona_aspect', 'jaimini-unchecked')
# ---- other named texts
NC('japa beej_mantra', 'mantra-mahodadhi-vocab', 'Generic mantra vocabulary. Text cited (Mantra Mahodadhi) is NOT held in the corpus.')
put('muhurta', 'text_not_held', [], 'muhurta-chintamani', note="Cited text Muhurta Chintamani is held only as Devanagari/Hindi OCR awaiting decision (no English definition to verify). Term 'muhurta' itself is vocabulary.")
put('nakshatra_deity', 'text_not_held', [], 'taittiriya', note="Taittiriya Aranyaka is not held; the 27 nakshatra deities are listed in BPHS Ch.3 (bphs_pg0029_c01) but that was not checked against this row.")
NC('mudda_dasha muntha munthapati patyamsha varshaphal varshesha', 'tajaka-neelakanthi-vocab', 'Tajaka Neelakanthi is held only as Devanagari/Hindi OCR (no English text to verify against); the terms are Tajaka-system vocabulary labels.')
NC('dina_pravesh ishrafa ithasala janma_dina kambula nakta yamaya', 'tajaka-tradition-vocab', 'Source is a "tradition" token (Tajaka), not a held text; terms are Tajaka-system vocabulary.')
# ---- classical_tradition token (97)
SI('abhijit', ['ABH'], 'ct-verified', "Held BPHS: Abhijit is counted only in the Astottari and Shastihayani dasas (sloka text, Ch.46 notes); 'the 28th intercalary nakshatra' is the usual gloss, not stated there.")
SF('gandanta', ['GAN'], 'ct-verified', "BPHS Ch.9 notes (p.111): last navamsas of Cancer, Scorpio and Pisces; Ch.92 adds nakshatra and tithi gandanta.")
SF('kalpadruma', ['B36_KDM'], 'ct-verified', "BPHS Ch.36 sloka 33-34 (four-planet dispositor chain in angles/trines or exalted).")
SI('badhaka', ['BDH'], 'ct-verified', "BPHS Ch.50 sloka 20-22: badhaka house per movable/fixed/dual sign (row's 'lord of the obstructing house').")
SI('sakata', ['PH_SAK'], 'ct-verified', "Phaladeepika Adh. VI sloka 14: Moon in the 6th, 8th or 12th from Jupiter (row says 6/8 only); BPHS Nabhasa 'Sakata' is a different yoga.")
SF('maha_bhagya', ['PH_MBH'], 'ct-verified', "Phaladeepika Adh. VI sloka 14 (day birth male, Sun/Moon/Lagna in odd signs; night birth female, even signs).")
SI('yamaganda gulika_kala', ['YAMAGH'], 'ct-verified', "BPHS p.44 notes list Ardha Prahara, Yamaghantaka, Mrityu, Kala and Gulika as the five Kala-velas; row glosses 'inauspicious daily period'.")
SF('ritu', ['RITU'], 'ct-verified', "Ch.3 sloka 45-46 names the six Ritus (term 'season' itself is vocabulary).")
SF('tithi', ['TITHI'], 'ct-verified', "Jataka Parijata translator's note: thirty tithis in a lunar month.")
SI('karana', ['KARANA'], 'ct-verified', "Eleven karana names in Jataka Parijata Adh. IX slokas 101-103 (count by listing); 'half a tithi' not stated there.")
CT('lagnadhi_yoga', ['B36_LAG'], 'ct-contradicted', "BPHS Ch.36 sloka 37 (Santhanam): Lagnadhi yoga = benefics in the 7th and 8th from the ascendant (no 6th). The glossary says 'Benefics 6/7/8 from lagna' (the Adhi-yoga-from-Moon pattern). Which is canonical?")
CT('subha_yoga', ['B36_SUB'], 'ct-contradicted', "BPHS Ch.36 sloka 1-2: Subha yoga = a benefic in the ascendant (or benefics in both the 12th and 2nd from the ascendant); the glossary says 'Benefic in 2nd from Moon'. Which definition is canonical?")
CT('asubha_yoga', ['B36_SUB'], 'ct-contradicted', "BPHS Ch.36 sloka 1-2: Asubha yoga = a malefic in the ascendant (or malefics in both 12th and 2nd from the ascendant); the glossary says 'Malefic in 2nd from Moon'. Which definition is canonical?")
NC('abhisheka akaraka amavasya aushadha ayana ayanamsha_term bhanga bhavat_bhavam brahma_muhurta dasha_sandhi dhatu dosha dvirdvadasha graha_shanti homa hora_p hora_timing janma_nakshatra kala_hora kartari kavacha krishna_paksha masa navapancham neecha_bhilashi nirayana panchanga papakartari papapati parihara pradakshina puja purnima rasi_sandhi ratna rudraksha samasaptaka sankranti sayana shadashtaka shraddha shubhakartari shukla_paksha stotra subhapati tarpana uccha_bhilashi upavasa vara vastu vrata yantra',
   'ct-vocabulary', "Pure vocabulary / ritual-practice / naming entry: the definition names a concept or practice (calendar unit, remedy type, geometric relation) without asserting a checkable classical rule. Token 'classical_tradition' is not provenance and is left as is.")
UM('abhijit_muhurta ashtakoota ashtama_shani bhakoot chandrabala chandrabala_p chatussagara choghadiya dhaiya_term gana graha_maitri kala_dasha kantaka_shani mahendra nadi rahu_kala rajju rajju_compat sade_sati_term stri_dirgha tarabala tarabala_p tara_compat trishadaya varna vashya vedha_compat vela yoga_panchanga yoni budha_aditya',
   'ct-unsourced', "Doctrinal rule / compatibility factor / timing convention with no supporting chunk found in the held texts (muhurta/tajaka/sarvartha texts are held only as Devanagari-Hindi or image-only OCR). Token 'classical_tradition' is not provenance (SS ruling Q3): stays unsourced-marked.")
# fix helper placeholders

# anything left?
left = sorted(set(rows) - set(A))
assert not left, left
extra = sorted(set(A) - set(rows))
assert not extra, extra
print('assigned', len(A))

# ---------------- emit grouped ledger objects
OUT = []
groups = collections.OrderedDict()
for t in sorted(rows):
    a = A[t]
    key_ = (rows[t]['cit'], a['group'], a['state'])
    groups.setdefault(key_, []).append(t)
for (cit_, grp, st), terms in groups.items():
    a0 = A[terms[0]]
    # evidence union (dedupe by chunk+quote)
    keys = []
    for t in terms:
        for k in A[t]['keys']:
            if k not in keys:
                keys.append(k)
    corpus = E_(*keys[:12]) if keys else []
    notes = []
    infs = []
    qs = []
    for t in terms:
        if A[t]['note'] and A[t]['note'] not in notes:
            notes.append(A[t]['note'])
        if A[t]['inf'] and A[t]['inf'] not in infs:
            infs.append(A[t]['inf'])
        if A[t]['q'] and A[t]['q'] not in qs:
            qs.append(A[t]['q'])
    sup = a0['sup']
    act = a0['act']
    prop = cit(keys[:12]) if (keys and st in ('sourced_fact', 'sourced_inference')) else None
    claim = "Glossary definitions (%d terms) in sub-family '%s': %s" % (len(terms), grp, ', '.join('%s = "%s"' % (t, rows[t]['df'][:70]) for t in terms[:4])) + (' ...' if len(terms) > 4 else '')
    OUT.append(row(ASSET, 'reference_glossary', {'classical_citation': cit_, 'subfamily': grp}, claim[:600], cit_, st, sup, corpus,
                   ' | '.join(infs) if infs else None, prop, act, ' || '.join(qs) if qs else None, row_count=len(terms),
                   note=' | '.join(notes) if notes else None,
                   extra={'row_keys': {'term_id': terms}, 'row_key_query': "select term_id from reference_glossary where classical_citation='%s' order by term_id" % cit_.replace("'", "''")}))
assert sum(o['row_count'] for o in OUT) == 364
json.dump(OUT, open(BASE + '/ledger_glossary.json', 'w'), indent=1, ensure_ascii=False)
json.dump({t: {'state': A[t]['state'], 'group': A[t]['group'], 'cit': rows[t]['cit']} for t in rows}, open(BASE + '/glossary_assign.json', 'w'), indent=1)
print('glossary objects', len(OUT))
print(collections.Counter({s: sum(o['row_count'] for o in OUT if o['state'] == s) for s in set(o['state'] for o in OUT)}))
bad = verify_all()
print('quote problems', len(bad))
for b in bad: print(b)
