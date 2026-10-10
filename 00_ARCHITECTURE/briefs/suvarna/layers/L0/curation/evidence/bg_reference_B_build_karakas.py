import json, sys
sys.path.insert(0, '/private/tmp/claude-504/scratch/curation/bg_reference_B')
from lib import *

OUT = []
rows = {}
for l in rq("select karaka_id,name_en,karaka_type,applies_to,source_citation,classical_significations::text from reference_karakas order by karaka_id").splitlines()[1:-1]:
    kid, nm, kt, ap, sc, cs = l.split('|', 5)
    rows[kid] = dict(name=nm, type=kt, applies=ap, sc=sc, cs=json.loads(cs))
assert len(rows) == 77

# ---------- evidence library (key -> (chunk, quote, sloka-label))
E = {
 'JS_sun':  ('bphs_jaimini_pg0042_c01', "Ravi—Atmaprabhavasakti or soul force, reputation, vitality and father", '23 (Notes)'),
 'JS_moon': ('bphs_jaimini_pg0042_c01', "Chandra—Manas, Matru, Mani, or Mind, Mother and Gems", '23 (Notes)'),
 'JS_mars': ('bphs_jaimini_pg0042_c01', "Bhumi, Satwa, Bhratru, or Lands, Strength and Brothers", '23 (Notes)'),
 'JS_merc': ('bphs_jaimini_pg0042_c01', "Budha—Pragnya, Matula, Buddhi, Vacha or intelligence, uncle, wisdom and speech", '23 (Notes)'),
 'JS_jup':  ('bphs_jaimini_pg0042_c01', "or Children, Educa. tion, Wealth and Spiritual development", '23 (Notes)'),
 'JS_ven':  ('bphs_jaimini_pg0042_c01', "Kama, Indriasukha, Kalatra—passion, reuse pleasures and wife", '23 (Notes)'),
 'JS_sat':  ('bphs_jaimini_pg0043_c01', "Ayushyam, Jeevanopayam, Maranatn—longevity, means of livelihood and death", '23 (Notes)'),
 'JS_ketu': ('bphs_jaimini_pg0043_c01', "Kaivalya- kataka or one who gives final bliss", '23 (Notes)'),
 'JSU20':   ('bphs_jaimini_pg0040_c01', "from Kuja should be ascertained particulars regarding brothers and sisters", '20'),
 'JSU21':   ('bphs_jaimini_pg0041_c01', "From Mercury should be ascertained details relating to maternal uncles", '21'),
 'JSU22':   ('bphs_jaimini_pg0041_c01', "the husband and children must be found out", '22'),
 'JSU24':   ('bphs_jaimini_pg0043_c01', "prosperity and misfortunes of the elder brothers", '24 (Notes)'),
 'B3_sun':  ('bphs_pg0027_c01', "If the Sun is strong, one wiff have a matured soul", '12-13 (Notes)'),
 'B3_jup':  ('bphs_pg0027_c01', "Knowledge and general happiness wit berpet acquired", '12-13 (Notes)'),
 'B3_sat':  ('bphs_pg0027_c01', "Grief wilt not be there, if Saturn is Uer.ft of strength", '12-13 (Notes)'),
 'B3_cab':  ('bphs_pg0027_c01', "Of royal statusarethe Sun and the Moon while Mars is the army chief", '14-15'),
 'B3_sev':  ('bphs_pg0027_c01', "Saturu is a servant", '14-15'),
 'B32_f':   ('bphs_pg0319_c01', "Stronger of the two indicates father", '18-21 (Notes)'),
 'B32_m':   ('bphs_pg0319_c01', "Stronger of the two indicates mother", '18-21 (Notes)'),
 'B32_mars': ('bphs_pg0319_c01', "Mars denotes sister, brother-in-law, younger brother and mother", '18-21'),
 'B32_mj':  ('bphs_pg0319_c01', "Mercury rules maternal relative while Jupiter indicates paternal grand-", '18-21'),
 'B32_vs':  ('bphs_pg0319_c01', "Husband and sons are respectivcly denoted by Venus and Saturn", '18-21'),
 'B32_h22': ('bphs_pg0320_c01', "The 9th from the Sun denotes father, the 4th from the Moon mother", '22-24'),
 'B32_nj':  ('bphs_pg0320_c01', "Jupiter - Sons (and daughters)", '22-24 (Notes)'),
 'B32_nv':  ('bphs_pg0320_c01', "Venus - wife (or husband)", '22-24 (Notes)'),
 'B32_ns':  ('bphs_pg0320_c01', "Saturn - death (or longeviiy)", '22-24 (Notes)'),
 'B32_nme': ('bphs_pg0320_c01', "Mercury - maternal relatives", '22-24 (Notes)'),
 'B32_nma': ('bphs_pg0320_c01', "Mars - brothers (and sisters)", '22-24 (Notes)'),
 'B32_hk1': ('bphs_pg0324_c01', "2. Jupiter 3. Mars .4. The Moon 5. Jupiter", '31-34 (Notes)'),
 'B32_hk2': ('bphs_pg0324_c01', "6. Mars 7. Venus 8. Saturn 9. Jupiter 10. Mercury", '31-34 (Notes)'),
 'B32_hk3': ('bphs_pg0324_c01', "I l. Jupiter 12. Saturn", '31-34 (Notes)'),
 'B32_h3':  ('bphs_pg0324_c01', "(courage, later-born etc )", '31-34 (Notes)'),
 'B32_h4':  ('bphs_pg0324_c01', "4th house (mother)", '31-34 (Notes)'),
 'B32_h5':  ('bphs_pg0324_c01', "5th house (progeny)", '31-34 (Notes)'),
 'B32_h6':  ('bphs_pg0324_c01', "6th house (enemies)", '31-34 (Notes)'),
 'B32_h7':  ('bphs_pg0324_c01', "(wife, conjugal bliss etc )", '31-34 (Notes)'),
 'B32_h9':  ('bphs_pg0324_c01', "(fortunes, religion etc.)", '31-34 (Notes)'),
 'B32_h12': ('bphs_pg0324_c01', "(expenditure)", '31-34 (Notes)'),
 'B32_emanc': ('bphs_pg0324_c02', "final emancipation as welr for which Saturn is not the indicator but Ketu", '31-34 (Notes)'),
 'B11_2':   ('bphs_pg0120_c01', "Wealth, grains (food etc.), family,", '3'),
 'B11_4':   ('bphs_pg0120_c01', "Conveyancos, relatives, nothcr, bappinoss, treasure, lands and houses", '5'),
 'B11_6':   ('bphs_pg0121_c01', "Maternal unclo, floubts about deatb, cnemies, ulcers, step mother", '7'),
 'B11_8':   ('bphs_pg0121_c01', "longevity, battle, enemies, forts, wealth of the deafi", '9'),
 'B11_9':   ('bphs_pg0121_c01', "visits to shrines ctc", '10'),
 'B11_10':  ('bphs_pg0121_c01', "profass- ion (livelihood), honour, father", '11'),
 'B11_11':  ('bphs_pg0122_c01', "son's wife, in come, prosperity", '12'),
 'B32_atma': ('bphs_pg0316_c01', "prime say on the native just as the king", '3-8'),
 'B32_8': ('bphs_pg0317_c02', "8. Stree Karaka (next to Gnati Karaka in longitude)", '13-17 (Notes)'),
 'B32_5pitru': ('bphs_pg0317_c02', "5: Pitru Karaka (next to Matru Karaka in longitude)", '13-17 (Notes)'),
 'B32_8tab': ('bphs_pg0318_c01', "Gnati Karaka Dara Karaka", '13-17 (Notes)'),
 'B32_7sch': ('bphs_pg0318_c01', "treating Matru Karaka and putra", '13-17 (Notes)'),
 'JC11': ('bphs_jaimini_pg0029_c01', "gets the highest number of degrees becomes the Atmakaraka", '11'),
 'JC13': ('bphs_jaimini_pg0035_c01', "The planet who is next in kalas or degrees to the Atmakaraka will become Amaiyalcaraka", '13'),
 'JC13n': ('bphs_jaimini_pg0036_c01', "Probably when the Amatya or Mantrikaraka is powerful and well combined", '13 (Notes)'),
 'JC14': ('bphs_jaimini_pg0036_c01', "highest number of degrees next to Amatyakaraka becomes Bhrairuha", '14'),
 'JC15': ('bphs_jaimini_pg0036_c01', "next to Bhratrukaraka becomes lord of the mother or Matrakaraka", '15'),
 'JC16': ('bphs_jaimini_pg0037_c01', "next in power in degrees to Matrnkaraka becomes the lord of the children", '16'),
 'JC17': ('bphs_jaimini_pg0038_c01', "Gnathikaraka or Lord of the cousins", '17'),
 'JC18': ('bphs_jaimini_pg0038_c01', "becomes Darakaraka or Lord of wife", '18'),
 'JC19': ('bphs_jaimini_pg0039_c01', "may. be represented by one and the same planet", '19'),
}
def E_(*keys):
    return [ev(E[k][0], E[k][1], E[k][2]) for k in keys]
def cit(keys):
    seen = []
    for k in keys:
        c = cite(E[k][0], '', E[k][2])
        if c not in seen:
            seen.append(c)
    return ' ; '.join(seen)

# ---------- Jaimini 8 rows
JROWS = {
 'atmakaraka': ('sourced_fact', ['JC11', 'B32_atma'], None, ["self/soul (name)", "'king of the chart' (analogy supported by BPHS Ch.32: 'prime say on the native just as the king')"], None),
 'amatyakaraka': ('sourced_fact', ['JC13', 'JC13n'], None, ["career/counsel: Jaimini notes say 'great Minister or Councillor' (counsel supported; 'career, livelihood' as such not stated)"], None),
 'bhratrikaraka': ('sourced_inference', ['JC14'], "rank 3 = the planet next to the Amatyakaraka in the 'next in degrees' chain Su.11,13,14", ["role extras 'courage, guru, dharma' not in held text (text: lord of brothers)"], None),
 'matrikaraka': ('sourced_inference', ['JC15'], "rank 4 by counting the chain Su.11,13,14,15", ["role extras 'home, vehicles, comforts' not in held text (text: lord of the mother)"], None),
 'putrakaraka': ('sourced_inference', ['JC16', 'JC19'], "rank 5 by counting the chain Su.11,13-16 (the 7-karaka scheme; BPHS Ch.32's 8-scheme inserts Pitrukaraka at 5 so Putra is 6th there; Su.19 mentions the view that Matru and Putra karakas coincide)", ["role extras 'intelligence, purva-punya' not in held text (text: lord of the children)"], None),
 'gnatikaraka': ('sourced_inference', ['JC17'], "rank 6 by counting the chain; held text: lord of the cousins", ["role 'enemies, disease, obstacles' not in held text (text: cousins/kin only)"], None),
 'darakaraka': ('sourced_inference', ['JC18', 'B32_8tab'], "rank 7 by counting the chain Su.11,13-18 (7-karaka scheme). In BPHS Ch.32's 8-scheme the Dara karaka (= Stree karaka) is the 8th", ["role 'partnership' not in held text (text: lord of wife)"], None),
}
for kid, (st, keys, inf, extras, _) in JROWS.items():
    r = rows[kid]
    assert r['type'] == 'chara_jaimini' and r['sc'] == 'Jaimini Sutram Ch.1'
    OUT.append(row(ASSET, 'reference_karakas', {'karaka_id': kid}, f"{r['name']} = rank {r['cs'].get('rank')} by longitude among the planets (Jaimini chara karaka)",
                   r['sc'], st, 'FACT' if st == 'sourced_fact' else 'INFERENCE', E_(*keys), inf, cit(keys), 'recite',
                   note='Unsupported role extras: ' + '; '.join(extras)))
kid = 'strikaraka'
r = rows[kid]
OUT.append(row(ASSET, 'reference_karakas', {'karaka_id': kid}, "Strikaraka ('Co-spouse Significator') = 8th-ranked planet, separate from the Darakaraka (rank 7)",
               r['sc'], 'contradicted', 'CONTRADICTS', E_('B32_8', 'B32_8tab', 'B32_5pitru', 'JC18'), None, None, 'acharya',
               "Held BPHS Ch.32 (8-karaka scheme) lists Atma, Amatya, Bhratru, Matru, Pitru, Putra, Gnati and Stree (= Dara) karakas: the 8th, 'Stree Karaka (next to Gnati Karaka)', is labelled 'Dara Karaka' in its worked table, i.e. Stree and Dara are ONE karaka, and a Pitrukaraka is rank 5. The row makes Strikaraka a separate 'co-spouse' significator at rank 8 and has no Pitrukaraka; held Jaimini (7-karaka scheme) has no 8th karaka at all. Should reference_karakas hold the 8-scheme as BPHS states it (adding pitrukaraka, folding strikaraka into darakaraka), or keep the 7-scheme only?",
               note="Citation 'Jaimini Sutram Ch.1' does not support an 8th karaka; the 8-scheme is BPHS Ch.32 sloka 13-17 (bphs_pg0317_c01/c02, pg0318_c01)."))

# ---------- BPHS rows
N, F, I = 'NONE', 'FACT', 'INF'
TOP = {   # topic -> list of (planet, class, [evidence keys], note)
 'accidents': [('mars', N, [], ''), ('rahu', N, [], '')],
 'agriculture': [('mars', N, [], "'lands' (Bhumi) is stated for Mars, agriculture is not")],
 'arts': [('venus', N, [], '')],
 'career': [('sun', N, [], ''), ('mercury', I, ['B32_hk2', 'B11_10'], "Mercury is the karaka of the 10th house; the 10th signifies profession (livelihood)"),
            ('jupiter', N, [], ''), ('saturn', I, ['JS_sat'], "'means of livelihood' read as career")],
 'children': [('jupiter', F, ['JS_jup', 'B32_nj', 'B32_hk1'], '')],
 'conveyance': [('venus', N, [], "held text: conveyances belong to the 4th house (Ch.11 sl.5) whose karaka is the Moon (Ch.32)")],
 'courage': [('mars', F, ['B32_hk1', 'B32_h3'], "3rd house (courage) - karaka Mars")],
 'debts': [('mars', N, [], '')],
 'dharma': [('jupiter', I, ['B32_hk2', 'B32_h9'], "9th house (fortunes, religion) karaka Jupiter; 'dharma' read as religion")],
 'discipline': [('saturn', N, [], '')],
 'disease': [('mars', I, ['B32_hk2', 'B32_h6', 'B11_6'], "Mars is the 6th-house karaka; Ch.11 lists ulcers under the 6th"), ('saturn', N, [], '')],
 'chronic_disease': [('saturn', N, [], '')],
 'education': [('mercury', N, [], ''), ('jupiter', F, ['JS_jup'], "Vidya/education")],
 'elder_siblings': [('jupiter', 'CONTRA', ['JSU24'], "held Jaimini notes assign the elder brothers to Saturn (Sani), not Jupiter")],
 'emotions': [('moon', N, [], "mind (Manas) is stated for the Moon; 'emotions' is not")],
 'enemies': [('mars', F, ['B32_hk2', 'B32_h6'], "6th house (enemies) - karaka Mars"), ('saturn', N, [], '')],
 'fame': [('sun', I, ['JS_sun'], "'reputation' read as fame")],
 'father': [('sun', F, ['JS_sun', 'B32_f', 'B32_h22'], ''), ('jupiter', I, ['B32_hk2', 'B11_10'], "alt: the 9th house is a primary house of the father (Ch.11 sl.11 notes) and its karaka is Jupiter; Jupiter is stated for the paternal grandfather")],
 'food': [('jupiter', I, ['B11_2', 'B32_hk1'], "2nd house (grains/food) karaka Jupiter")],
 'foreign_travel': [('rahu', N, [], ''), ('saturn', N, [], '')],
 'friends': [('mercury', N, [], '')],
 'gains': [('jupiter', I, ['B11_11', 'B32_hk3'], "11th house (income) karaka Jupiter")],
 'government': [('sun', I, ['B3_cab'], "'royal status' read as government")],
 'grief': [('saturn', F, ['B3_sat'], '')],
 'happiness': [('moon', I, ['B32_hk1', 'B11_4'], "4th house (happiness among its topics) karaka Moon"), ('mercury', N, [], ''), ('mars', N, [], '')],
 'higher_learning': [('jupiter', I, ['JS_jup', 'B3_jup'], "education / knowledge read as higher learning")],
 'home': [('moon', I, ['B32_hk1', 'B11_4'], "4th house (lands and houses) karaka Moon")],
 'inheritance': [('saturn', I, ['B32_hk2', 'B11_8'], "8th house (wealth of the dead) karaka Saturn")],
 'intelligence': [('mercury', F, ['JS_merc'], "Pragnya/intelligence")],
 'land': [('mars', F, ['JS_mars'], "Bhumi/lands")],
 'litigation': [('mars', N, [], ''), ('saturn', N, [], '')],
 'longevity': [('saturn', F, ['JS_sat', 'B32_ns'], '')],
 'losses': [('saturn', I, ['B32_hk3', 'B32_h12'], "12th house (expenditure) karaka Saturn; losses read as expenditure")],
 'marriage': [('venus', I, ['JS_ven', 'B32_nv', 'B32_h7'], "wife / conjugal bliss read as marriage")],
 'maternal_uncle': [('mars', I, ['B32_hk2', 'B11_6'], "Mars is the 6th-house karaka and Ch.11 lists the maternal uncle under the 6th; BUT held text names MERCURY as the maternal-relative/uncle significator (see note)")],
 'mind': [('moon', F, ['JS_moon'], "Manas/mind")],
 'moksha': [('ketu', F, ['JS_ketu', 'B32_emanc'], ''), ('saturn', 'CONTRA', ['B32_emanc'], "held text: 'Saturn is not the indicator [of final emancipation] but Ketu'")],
 'mother': [('moon', F, ['JS_moon', 'B32_m', 'B32_h22'], '')],
 'occult': [('ketu', N, [], ''), ('saturn', N, [], '')],
 'passion': [('venus', F, ['JS_ven'], "Kama/passion")],
 'pilgrimage': [('jupiter', I, ['B11_9', 'B32_hk2'], "9th house (visits to shrines) karaka Jupiter")],
 'pleasure': [('venus', F, ['JS_ven'], "Indriasukha/sense pleasures")],
 'power': [('sun', I, ['B3_cab'], "royal status"), ('mars', I, ['B3_cab'], "army chief"), ('saturn', N, [], "held text calls Saturn a servant")],
 'progeny': [('jupiter', F, ['B32_hk1', 'B32_h5', 'B32_nj'], '')],
 'property': [('mars', I, ['JS_mars'], "lands read as property")],
 'relatives': [('mercury', I, ['B32_nme', 'JSU21'], "maternal relatives only; generic 'relatives' read from it")],
 'research': [('saturn', N, [], ''), ('ketu', N, [], '')],
 'romance': [('venus', I, ['JS_ven'], "passion / sense pleasures read as romance")],
 'servants': [('saturn', I, ['B3_sev'], "'Saturn is a servant' (planetary cabinet) read as significator of servants")],
 'speculation': [('jupiter', N, [], ''), ('mercury', N, [], '')],
 'speech': [('mercury', F, ['JS_merc'], "Vacha/speech"), ('jupiter', N, [], '')],
 'spirituality': [('ketu', I, ['JS_ketu'], "final bliss/emancipation read as spirituality"), ('jupiter', F, ['JS_jup'], "spiritual development")],
 'spouse': [('venus', F, ['B32_nv', 'JS_ven', 'B32_h7'], "note 'Jupiter for husband' is supported by Jaimini Su.22 (JSU22) but BPHS Ch.32 names Venus for the husband")],
 'status': [('sun', I, ['B3_cab'], "'royal status'")],
 'sudden_events': [('rahu', N, [], ''), ('ketu', N, [], '')],
 'trade': [('mercury', N, [], "Ch.11 lists trade under the 7th house (karaka Venus)")],
 'vehicles': [('venus', N, [], '')],
 'vitality': [('sun', F, ['JS_sun'], '')],
 'wealth': [('jupiter', F, ['JS_jup', 'B32_hk1'], '')],
 'accumulated_wealth': [('jupiter', I, ['JS_jup'], "Dhana/wealth read as accumulated wealth")],
 'wisdom': [('jupiter', I, ['B3_jup', 'JS_jup'], "knowledge/Gnana read as wisdom; NB held Jaimini notes list 'wisdom (Buddhi)' under Mercury")],
 'younger_siblings': [('mars', F, ['B32_mars', 'JSU20', 'B32_h3'], '')],
}
PLANET = {  # planet row -> list of (element, class, keys, note)
 'sun': [('soul', F, ['B3_sun', 'JS_sun'], ''), ('father', F, ['JS_sun', 'B32_f'], ''), ('authority', I, ['B3_cab'], 'royal status'), ('health', N, [], "'vitality' is stated, 'health' is not"),
         ('government', I, ['B3_cab'], 'royal status'), ('vitality', F, ['JS_sun'], '')],
 'moon': [('mind', F, ['JS_moon'], ''), ('mother', F, ['JS_moon', 'B32_m'], ''), ('emotions', N, [], ''), ('fluids', N, [], ''), ('public', N, [], '')],
 'mars': [('siblings', F, ['JS_mars', 'B32_nma'], ''), ('courage', F, ['B32_hk1', 'B32_h3'], ''), ('land', F, ['JS_mars'], ''), ('energy', I, ['JS_mars'], "'strength' (Satwa) read as energy"),
          ('conflict', N, [], ''), ('surgery', N, [], '')],
 'mercury': [('intellect', F, ['JS_merc'], ''), ('speech', F, ['JS_merc'], ''), ('trade', N, [], ''), ('education', N, [], ''), ('relatives', I, ['B32_nme'], 'maternal relatives only')],
 'jupiter': [('children', F, ['JS_jup', 'B32_nj'], ''), ('wisdom', I, ['B3_jup', 'JS_jup'], 'knowledge/Gnana'), ('wealth', F, ['JS_jup', 'B32_hk1'], ''), ('guru', N, [], ''), ('dharma', I, ['B32_hk2', 'B32_h9'], '9th-house karaka (religion)')],
 'venus': [('spouse', F, ['B32_nv', 'JS_ven'], ''), ('marriage', I, ['JS_ven', 'B32_h7'], 'wife / conjugal bliss'), ('luxury', I, ['JS_ven'], 'sense pleasures'), ('vehicles', N, [], ''), ('arts', N, [], '')],
 'saturn': [('longevity', F, ['JS_sat', 'B32_ns'], ''), ('karma', N, [], ''), ('grief', F, ['B3_sat'], ''), ('servants', I, ['B3_sev'], "'Saturn is a servant'"), ('discipline', N, [], '')],
}
QMAP = {
 'elder_siblings': "Held Jaimini Sutras notes (Su.24) assign the elder brothers' prosperity to Saturn; the platform row assigns elder siblings to Jupiter. Which significator does the platform adopt for elder siblings, and on what text?",
 'moksha': "BPHS Ch.32 (31-34 Notes) states that for the 12th house's final emancipation 'Saturn is not the indicator but Ketu'. reference_karakas lists [ketu, saturn] for moksha. Should Saturn be removed from the moksha karaka row?",
 'maternal_uncle': "Held texts name Mercury for the maternal uncle in three places (BPHS Ch.32 sl.18-24 and notes; Jaimini Su.21 and notes). The row assigns Mars (reachable only via the 6th-house chain). Should Mercury be the (or an additional) significator?",
 'happiness': "BPHS Ch.3 (planetary governances, Notes) ties 'knowledge and general happiness' to Jupiter. The row lists [moon, mercury, mars] for happiness and omits Jupiter. Which planets should the happiness karaka row carry?",
}
def unit_planet_cls(c): return c
hk_rows = [k for k, v in rows.items() if v['type'] == 'sthira_house']
pl_rows = [k for k, v in rows.items() if v['type'] == 'sthira_planet']
assert len(hk_rows) == 62 and len(pl_rows) == 7, (len(hk_rows), len(pl_rows))
topics_in_db = {rows[k]['applies'] for k in hk_rows}
assert topics_in_db == set(TOP.keys()), (topics_in_db ^ set(TOP.keys()))

def decide(elems):
    cls = [e[1] for e in elems]
    if 'CONTRA' in cls:
        return 'contradicted'
    if all(c == F for c in cls):
        return 'sourced_fact'
    if all(c in (F, I) for c in cls):
        return 'sourced_inference'
    return 'unsourced_marked'
def mk(kid, claim, elems, extra_q=None):
    r = rows[kid]
    st = decide(elems)
    keys = []
    for e in elems:
        for k in e[2]:
            if k not in keys:
                keys.append(k)
    sup = {'sourced_fact': 'FACT', 'sourced_inference': 'INFERENCE', 'unsourced_marked': 'NONE', 'contradicted': 'CONTRADICTS'}[st]
    elements = {}
    for e in elems:
        elements[e[0]] = {'FACT': 'FACT', 'INF': 'INFERENCE', 'NONE': 'NONE', 'CONTRA': 'CONTRADICTS'}[e[1]] + (' - ' + e[3] if e[3] else '')
    unsup = [e[0] for e in elems if e[1] == N]
    inf_steps = [f"{e[0]}: {e[3]}" for e in elems if e[1] == I and e[3]]
    inf = ('; '.join(inf_steps)) if inf_steps else None
    if st == 'unsourced_marked':
        act = 'mark_unsourced'
        note = ("Partly supported: " + ', '.join(e[0] for e in elems if e[1] in (F, I)) + ". " if any(e[1] in (F, I) for e in elems) else '') + \
               "Not stated in the held corpus: " + ', '.join(unsup) + ". Existing citation 'BPHS Ch.27' is the Shadbala chapter and cannot support karaka assignments."
        prop = None
    elif st == 'contradicted':
        act = 'acharya'
        note = "Existing citation 'BPHS Ch.27' is the Shadbala chapter; the karaka statements live in Ch.32 (and Jaimini notes). See acharya question."
        prop = None
    else:
        act = 'recite'
        note = "Existing citation 'BPHS Ch.27' is the Shadbala chapter and does not contain karaka assignments; evidence found in Ch.3/Ch.11/Ch.32 and the Jaimini Sutras notes."
        prop = cit(keys)
    q = QMAP.get(r['applies']) if r['type'] == 'sthira_house' else None
    if kid == 'karaka_maternal_uncle':
        act = 'acharya'   # sourced_inference but with explicit alternative
    if kid == 'karaka_happiness':
        act = 'acharya'
    OUT.append(row(ASSET, 'reference_karakas', {'karaka_id': kid}, claim, r['sc'], st, sup, E_(*keys), inf, prop, act, q,
                   note=note, extra={'elements': elements}))

for kid in sorted(hk_rows):
    r = rows[kid]
    t = r['applies']
    pls = r['cs'].get('planet')
    if isinstance(pls, str):
        pls = [pls]
    alt = r['cs'].get('alt')
    exp = [e[0] for e in TOP[t]]
    got = list(pls) + ([alt] if alt else [])
    assert sorted(exp) == sorted(got), (kid, exp, got)
    mk(kid, f"Karaka (significator) of {t.replace('_', ' ')} = {', '.join(got)}" + (f" ({r['cs']['note']})" if 'note' in r['cs'] else ''), TOP[t])
for kid in sorted(pl_rows):
    p = rows[kid]['applies']
    got = rows[kid]['cs']['of']
    exp = [e[0] for e in PLANET[p]]
    assert got == exp, (kid, got, exp)
    mk(kid, f"{p.capitalize()} as natural significator of: {', '.join(got)}", PLANET[p])

assert len(OUT) == 77, len(OUT)
json.dump(OUT, open(BASE + '/ledger_karakas.json', 'w'), indent=1, ensure_ascii=False)
from collections import Counter
print(Counter(o['state'] for o in OUT))
bad = verify_all()
print('quote problems', len(bad))
for b in bad[:60]: print(b)
