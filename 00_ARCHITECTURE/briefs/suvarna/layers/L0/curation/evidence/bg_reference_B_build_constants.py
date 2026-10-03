import json, sys
sys.path.insert(0, '/private/tmp/claude-504/scratch/curation/bg_reference_B')
from lib import *

OUT = []
def add(**kw):
    OUT.append(row(ASSET, 'reference_constants', kw.pop('key'), kw.pop('claim'), kw.pop('cur'), kw.pop('state'),
                   kw.pop('sup'), kw.pop('corpus', None), kw.pop('inf', None), kw.pop('prop', None),
                   kw.pop('act', 'none'), kw.pop('q', None), note=kw.pop('note', None)))

# fetch current rows
rows = {}
for l in rq("select constant_id,name,value_numeric,coalesce(value_text,''),category,source_citation from reference_constants order by constant_id").splitlines()[1:-1]:
    cid, name, vn, vt, cat, sc = l.split('|')
    rows[cid] = dict(name=name, vn=vn, vt=vt, cat=cat, sc=sc)
assert len(rows) == 203, len(rows)
done = set()
def key(cid):
    done.add(cid)
    return {'constant_id': cid}

# ---------------- ashtakavarga (64)
AVN = {'sun': 'sun', 'moon': 'moon', 'mars': 'mars', 'mercury': 'mercury', 'jupiter': 'jupiter', 'venus': 'venus', 'saturn': 'saturn', 'lagna': 'lagna'}
cmp_ = json.load(open(BASE + '/av_compare.json'))
REK = {  # target -> (chunk, sloka, quote)
 'sun': ('bphs_pg0846_c01', '43-45', "Saturn, Mars and the Sun in the 2nd, the 8th and the lst"),
 'moon': ('bphs_pg0848_c01', '46-48', "Vcnus and the Mcon in the 9th"),
 'mars': ('bphs_pg0849_c01', '49-50', "Saturn and Mars in the 4th: Mercury arrd the Sun in the 5th"),
 'mercury': ('bphs_pg0850_c01', '51-52', "Mars and Saturn in the 7th"),
 'jupiter': ('bphs_pg0852_c01', '53-55', "Jupiter, the Sun and Mars in the 8th"),
 'venus': ('bphs_pg0853_c01', '56-58', "Scturn and Mars in tnc 4th"),
 'saturn': ('bphs_pg0854_c01', '59-60', "Jupiter, Saturn and Mars in the 5th"),
 'lagna': ('bphs_pg0857_c01', '65-68', "all except Venus jn the llth"),
}
DOT = {
 'sun': ('bphs_pg0837_c01', '17-19', "Vcnus (l) in thc llth"),
 'moon': ('bphs_pg0839_c01', '20-22', "all theeight in th-c 12th"),
 'mars': ('bphs_pg0841_c01', '23-27', "none in the I l th"),
 'mercury': ('bphs_pg0842_c01', '28-30', "Mercury, the Sun and Jupiter, these 3 in the 4th"),
 'jupiter': ('bphs_pg0843_c01', '31-34', "Saturn in the 2nd and llth"),
 'venus': ('bphs_pg0844_c01', '35-38', "these 2 in thc 5th"),
 'saturn': ('bphs_pg0845_c01', '39-42', "none in tbe llth"),
 'lagna': ('bphs_pg0855_c01', '61-64', "Venus in the 10th : Venus in"),
}
CONTRA = {
 'ashtakavarga_moon_from_moon': dict(
    stmt="text lists Moon among Moon-AV rekhapradas in the 9th (houses 1,3,6,7,9,10,11); row omits 9",
    corpus=lambda: [ev('bphs_pg0848_c01', "Vcnus and the Mcon in the 9th", '46-48')],
    q="In BPHS Ch.66 (Santhanam) the Moon's own Ashtakavarga lists 'Venus and the Moon' (OCR 'Mcon') as rekhapradas in the 9th, i.e. Moon-from-Moon = 1,3,6,7,9,10,11. The platform row has 1,3,6,7,10,11 (no 9th). Is the printed 'Moon' in the 9th a print/translation variant of 'Mars', or should the row follow the held text?"),
 'ashtakavarga_moon_from_mars': dict(
    stmt="text lists Venus and Moon (not Mars) in the 9th of the Moon AV; Mars-from-Moon would be 2,3,5,6,10,11 (no 9); row has 9",
    corpus=lambda: [ev('bphs_pg0848_c01', "Vcnus and the Mcon in the 9th", '46-48')],
    q="Same 9th-house line as Moon-from-Moon: the held text gives 'Venus and the Moon' in the 9th of the Moon AV, so Mars would NOT contribute a rekha at the 9th (platform row includes 9). Which reading is authoritative for Mars-to-Moon: 2,3,5,6,9,10,11 (platform) or 2,3,5,6,10,11 (held text)?"),
 'ashtakavarga_moon_from_jupiter': dict(
    stmt="text gives Jupiter a Moon-AV rekha at the 2nd (with Mars) and none for any planet in the 12th (all eight are dots in the 12th); row has 12 and no 2",
    corpus=lambda: [ev('bphs_pg0848_c01', "Jupiter and Mar; in rhe 2nd", '46-48'),
                    ev('bphs_pg0839_c01', "all theeight in th-c 12th", '20-22')],
    q="BPHS Ch.66 (Santhanam) says 'Jupiter and Mars in the 2nd' and 'No planet is Rekhaprada in the 12th' for the Moon's Ashtakavarga; platform row Moon-from-Jupiter = 1,4,7,8,10,11,12. Should the 12th be replaced by the 2nd (1,2,4,7,8,10,11) to match the held text?"),
 'ashtakavarga_venus_from_mars': dict(
    stmt="text gives Mars a Venus-AV rekha at the 4th (not the 5th): 3,4,6,9,11,12; row has 3,5,6,9,11,12",
    corpus=lambda: [ev('bphs_pg0853_c01', "Scturn and Mars in tnc 4th", '56-58'),
                    ev('bphs_pg0844_c01', "these 2 in thc 5th", '35-38')],
    q="BPHS Ch.66 (Santhanam) lists Mars among Venus-AV rekhapradas in the 4th and lists 'the Sun and Mars' as dots in the 5th; platform row Venus-from-Mars = 3,5,6,9,11,12. Which is correct: 3,4,6,9,11,12 (held text) or 3,5,6,9,11,12 (platform)?"),
 'ashtakavarga_mercury_from_sun': dict(
    stmt="Mercury-AV rekha para (51-52) lists Mercury, Saturn and Venus in the 5th (no Sun); the dot para (28-30) agrees with the row (Sun rekha at 5). Internal text conflict",
    corpus=lambda: [ev('bphs_pg0850_c01', "Mercury, Saturn and Venus in in, itt I", '51-52'),
                    ev('bphs_pg0842_c01', "Mars, the Moon, Saturn and the Ascendant, these 5", '28-30')],
    q="Within BPHS Ch.66 the Mercury AV is internally inconsistent at the 5th house: verse 51-52 lists 'Mercury, Saturn and Venus' as rekhapradas, while verse 28-30 lists 'Jupiter, Mars, the Moon, Saturn and the Ascendant' as dots. The platform rows follow the dot list (Sun rekha at 5, Saturn not). Is 'Saturn' in verse 51-52 a misprint for 'Sun'?"),
 'ashtakavarga_mercury_from_saturn': dict(
    stmt="Mercury-AV rekha para (51-52) lists Saturn as rekha at the 5th (extra house 5); dot para (28-30) lists Saturn as dot at 5 (agrees with row). Internal text conflict",
    corpus=lambda: [ev('bphs_pg0850_c01', "Mercury, Saturn and Venus in in, itt I", '51-52'),
                    ev('bphs_pg0842_c01', "Mars, the Moon, Saturn and the Ascendant, these 5", '28-30')],
    q="Same Mercury-AV 5th-house conflict (Saturn rekha in verse 51-52 vs Saturn dot in verse 28-30). Platform row Mercury-from-Saturn omits 5. Confirm."),
}
SPECIAL_FACT_NOTE = {
 'ashtakavarga_mars_from_saturn': "Dot-name list (23-27) prints 5 names for the 5th although the same verse states '6 planets in ... the 5th'; rekha para (49-50: Mercury and the Sun only in the 5th) and the stated count both agree with the row (5 not in 1,4,7,8,9,10,11).",
}
INF_ROWS = {'ashtakavarga_mercury_from_mars': "10th-house token for Mars is OCR-garbled in the rekha para (51-52); resolved by the dot list (28-30: dots in the 10th are Sun, Jupiter, Venus only, so Mars is a rekha).",
            }
for cid in sorted(c for c in rows if c.startswith('ashtakavarga_')):
    r = rows[cid]
    _, tgt, _f, src = cid.split('_')
    db_h = r['vt'].replace(' ', '')
    cl = f"{tgt.capitalize()}'s Ashtakavarga: houses counted from {src.capitalize()} that carry a benefic point = {r['vt']}"
    cur = r['sc']
    rc, rs, rq_ = REK[tgt]
    dc, ds, dq = DOT[tgt]
    if cid in CONTRA:
        c = CONTRA[cid]
        add(key=key(cid), claim=cl, cur=cur, state='contradicted', sup='CONTRADICTS', corpus=c['corpus'](),
            note=c['stmt'] + ". Column unit says 'bindu-houses' but the held text calls benefic houses 'rekhaprada' (Karana/dot = inauspicious).",
            act='acharya', q=c['q'])
        continue
    corpus = [ev(rc, rq_, rs), ev(dc, dq, ds)]
    if tgt == 'jupiter':
        add(key=key(cid), claim=cl, cur=cur, state='sourced_inference', sup='INFERENCE', corpus=corpus,
            inf="Jupiter-AV rekha paragraph (53-55) is OCR-damaged for houses 1-4; those houses derived as the complement of the explicit dot list (31-34); houses 5-12 read from the rekha paragraph and match.",
            prop=cite(rc, '', rs) + ' ; ' + cite(dc, '', ds), act='recite',
            note="Terminology: BPHS (Santhanam) calls these benefic houses 'rekha'/'sthana' and the dots (karana/bindu) inauspicious; the row's unit label 'bindu-houses' follows later usage - houses themselves agree with the held rekhaprada lists.")
    elif cid in INF_ROWS:
        add(key=key(cid), claim=cl, cur=cur, state='sourced_inference', sup='INFERENCE', corpus=corpus, inf=INF_ROWS[cid],
            prop=cite(rc, '', rs) + ' ; ' + cite(dc, '', ds), act='recite')
    else:
        add(key=key(cid), claim=cl, cur=cur, state='sourced_fact', sup='FACT', corpus=corpus,
            prop=cite(rc, '', rs) + ' ; ' + cite(dc, '', ds), act='recite',
            note=(SPECIAL_FACT_NOTE.get(cid, '') + ' ' if cid in SPECIAL_FACT_NOTE else '') +
                 "All 12 houses re-derived from the rekhaprada list of the target planet and cross-checked against its karanaprada (dot) list; held text calls these houses rekhaprada (auspicious).")
    # sanity vs compare file
    assert cmp_[cid]['db'] == [int(x) for x in db_h.split(',')]

# ---------------- vimshottari
VY = {'sun': 6, 'moon': 10, 'mars': 7, 'rahu': 18, 'jupiter': 16, 'saturn': 19, 'mercury': 17, 'ketu': 7, 'venus': 20}
for p, y in VY.items():
    cid = 'vimshottari_years_' + p
    assert int(rows[cid]['vn']) == y, (cid, rows[cid])
    corpus = [ev('bphs_pg0499_c01', "Ketu and Venus are 6,lO, 7,", '15'), ev('bphs_pg0499_c02', "18, 16, 19,l'1,7 and20 in thai order", '15')]
    if p in ('mercury', 'moon'):
        add(key=key(cid), claim=f"{p.capitalize()} Vimshottari dasha = {y} years", cur=rows[cid]['sc'], state='sourced_inference', sup='INFERENCE', corpus=corpus,
            inf=("OCR digit repair: printed \"l'1\" read as 17" if p == 'mercury' else "OCR digit repair: printed 'lO' read as 10") + "; order Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury, Ketu, Venus fixed by the same sloka; total 120 corroborates.",
            prop=cite('bphs_pg0499_c01', '', '15') + ' ; ' + cite('bphs_pg0499_c02', '', '15'), act='recite')
    else:
        add(key=key(cid), claim=f"{p.capitalize()} Vimshottari dasha = {y} years", cur=rows[cid]['sc'], state='sourced_fact', sup='FACT', corpus=corpus,
            prop=cite('bphs_pg0499_c01', '', '15') + ' ; ' + cite('bphs_pg0499_c02', '', '15'), act='recite',
            note="Sloka lists dasha periods for 'the Sun, the Moon, Mars, Rahu, Jupiter, Saturn, Mercury, Ketu and Venus' in that order.")
add(key=key('vimshottari_total'), claim='Vimshottari total cycle = 120 years', cur=rows['vimshottari_total']['sc'], state='sourced_fact', sup='FACT',
    corpus=[ev('bphs_pg0505_c01', "total of which comes to 120 years", None)],
    prop=cite('bphs_pg0505_c01', ''), act='recite',
    note="Translator's note at the end of Ch.46 dasha tables; sloka 12-14 note (bphs_pg0499_c01) also ties Vimshottari to the 120-year Kaliyuga life span.")

# ---------------- exaltation / debilitation
EX = {'sun': ('aries', 10), 'moon': ('taurus', 3), 'mars': ('capricorn', 28), 'mercury': ('virgo', 15), 'jupiter': ('cancer', 5), 'venus': ('pisces', 27), 'saturn': ('libra', 20)}
DB = {'sun': ('libra', 10), 'moon': ('scorpio', 3), 'mars': ('cancer', 28), 'mercury': ('pisces', 15), 'jupiter': ('capricorn', 5), 'venus': ('virgo', 27), 'saturn': ('aries', 20)}
exalt_ev = lambda: [ev('bphs_pg0037_c02', "Taurus, Capricorn, Virgo, Cancer, Pisces and Libra", '49-50'),
                    ev('bphs_pg0038_c01', "The deepest exaltation degrees are respectively 10,3, 2g, 15, 5,", '49-50')]
for p, (sg, dg) in EX.items():
    cid = 'exalt_deg_' + p
    assert rows[cid]['vt'] == f"{sg} {dg}°" and int(rows[cid]['vn']) == dg, rows[cid]
    if p == 'mars':
        add(key=key(cid), claim=f"{p.capitalize()} deep exaltation at {sg} {dg} deg", cur=rows[cid]['sc'], state='sourced_inference', sup='INFERENCE',
            corpus=exalt_ev() + [ev('hora_sara_pg0018_c01', "Capricorn 28°", None)],
            inf="BPHS prints Mars's deepest-exaltation degree as '2g' (OCR); read as 28, corroborated by the Hora Sara table (Mars Capricorn 28 deg). Sign by 'respectively' order (Aries, Taurus, Capricorn, ...).",
            prop=cite('bphs_pg0038_c01', '', '49-50') + ' ; ' + cite('bphs_pg0037_c02', '', '49-50'), act='recite')
    else:
        add(key=key(cid), claim=f"{p.capitalize()} deep exaltation at {sg} {dg} deg", cur=rows[cid]['sc'], state='sourced_fact', sup='FACT', corpus=exalt_ev(),
            prop=cite('bphs_pg0037_c02', '', '49-50') + ' ; ' + cite('bphs_pg0038_c01', '', '49-50'), act='recite',
            note="'For the seven planets from the Sun on, the signs of exaltation are respectively ...' and 'deepest exaltation degrees are respectively 10, 3, 28, 15, 5, 27 and 20' (positional mapping).")
for p, (sg, dg) in DB.items():
    cid = 'debil_deg_' + p
    assert rows[cid]['vt'] == f"{sg} {dg}°" and int(rows[cid]['vn']) == dg, rows[cid]
    corpus = [ev('bphs_pg0038_c01', "in the seventh sign from tle saij exaltation sign each planet has its own debilitation", '49-50'),
              ev('bphs_pg0038_c01', "same degrees of deep exaltation apply to deep fall", '49-50')]
    add(key=key(cid), claim=f"{p.capitalize()} deep debilitation at {sg} {dg} deg", cur=rows[cid]['sc'], state='sourced_inference', sup='INFERENCE', corpus=corpus,
        inf=f"Debilitation sign computed as the 7th sign from the exaltation sign ({EX[p][0]} -> {sg}) and the degree taken equal to the exaltation degree ({dg})" + ("; Mars degree '2g' read as 28 (OCR)." if p == 'mars' else "."),
        prop=cite('bphs_pg0038_c01', '', '49-50'), act='recite')

# ---------------- moolatrikona
MT = {
 'sun': ('sourced_fact', [ev('bphs_pg0038_c01', "In Leo the first 20 degrees are the Sun's Moolatrikona", '51-54')], None),
 'moon': ('sourced_inference', [ev('hora_sara_pg0018_c01', "The first three degrees of Taurus are the Moon's exaltation", None)],
          "BPHS Ch.3 sloka 51-54 (bphs_pg0038_c01) has the Moon's moolatrikona line lost to OCR garble; the Hora Sara chunk (different text) says Taurus first 3 deg exaltation, 'the rest is her Moolatrikona'. Row's '4-30' reads as 'from the 4th degree' = after 3 elapsed degrees."),
 'mars': ('sourced_fact', [ev('bphs_pg0038_c01', "first 12 dcgrees in Aries as Moolatrikona", '51-54')], None),
 'mercury': ('sourced_inference', [ev('bphs_pg0038_c02', "first 15 degrces are exaltation zone, the next 5 degrees Moolatri- kona", '51-54')],
             "15 deg exaltation zone + next 5 deg = elapsed 15-20 deg = ordinal 16th-20th degree. The row uses ordinal '16-20' while the Sun/Mars rows use elapsed '0-20'/'0-12' (mixed convention inside the same category)."),
 'jupiter': ('sourced_inference', [ev('bphs_pg0038_c02', "first one third of Sagittarius is the Moolatrikona of Jupiter", '51-54')],
             "one third of 30 deg = 10 deg (arithmetic). Hora Sara states first 5 deg (hora_sara_pg0019_c01) - a cross-text variant, not a contradiction of the BPHS-cited row."),
 'venus': ('sourced_inference', [ev('bphs_pg0038_c02', "Venus divides Libra into two halves keeping thc first as Moolatrikona", '51-54')],
           "half of 30 deg = 15 deg (arithmetic). Hora Sara says up to 20 deg (hora_sara_pg0018_c01) - cross-text variant."),
 'saturn': ('sourced_inference', [ev('bphs_pg0038_c02', "Saturn's arrangements are same in Aquarius as the Sun has in Leo", '51-54')],
            "equivalence statement: Saturn/Aquarius = Sun/Leo = first 20 deg."),
}
for p, (st, corpus, infs) in MT.items():
    cid = 'moolatrikona_' + p
    r = rows[cid]
    if p == 'moon':
        prop = cite('hora_sara_pg0018_c01', '') + '  [cites Hora Sara; the BPHS Ch.3 moolatrikona line for the Moon is OCR-lost]'
    else:
        prop = cite(corpus[0]['chunk_id'], '', '51-54')
    add(key=key(cid), claim=f"{p.capitalize()} moolatrikona span = {r['vt']}", cur=r['sc'], state=st,
        sup='FACT' if st == 'sourced_fact' else 'INFERENCE', corpus=corpus, inf=infs, prop=prop, act='recite')

# ---------------- digbala
DG = {'jupiter': 1, 'mercury': 1, 'moon': 4, 'venus': 4, 'saturn': 7, 'sun': 10, 'mars': 10}
for p, h in DG.items():
    cid = 'digbala_house_' + p
    assert int(rows[cid]['vn']) == h
    pq = {'jupiter': "Jupiter and Mercury have Digbata ln the ascendant", 'mercury': "Jupiter and Mercury have Digbata ln the ascendant",
          'venus': "Venus and the Moon have this bala in the 4th hquse (i e, Nadir)", 'moon': "Venus and the Moon have this bala in the 4th hquse (i e, Nadir)",
          'saturn': "Saturn in tho descendant and the Sun and Matq op the meridian", 'sun': "Saturn in tho descendant and the Sun and Matq op the meridian",
          'mars': "from the longitudes of Sun and Mars"}[p]
    corpus = [ev('bphs_pg0266_c01', pq, '7-71')]
    add(key=key(cid), claim=f"{p.capitalize()} directional-strength house = {h}", cur=rows[cid]['sc'], state='sourced_fact', sup='FACT', corpus=corpus,
        prop=cite('bphs_pg0266_c01', '', '7-71'), act='recite',
        note="Sloka 7-7(1/2): zero-point houses (Sun, Mars: 4th; Jupiter, Mercury: 7th; Venus, Moon: 10th; Saturn: ascendant); Notes state the strong houses: Jupiter/Mercury ascendant, Venus/Moon 4th, Saturn descendant, Sun/Mars meridian (OCR 'Matq' for Mars in Notes; Mars pairing with the Sun is explicit in the sloka).")

# ---------------- drishti
add(key=key('drishti_full'), claim='Full aspect fraction = 1', cur=rows['drishti_full']['sc'], state='sourced_fact', sup='FACT',
    corpus=[ev('bphs_pg0254_c01', "All planets aspect the Tth fully", '2-5')] if False else [ev('bphs_pg0254_c01', "in slabs of quarters i.e l14, 112,3l4thand fult", '2-5')],
    prop=cite('bphs_pg0254_c01', '', '2-5'), act='recite', note="'All planets aspect the 7th fully' (OCR 'Tth').")
for k, fr in (('half', '0.5'), ('quarter', '0.25'), ('three_quarter', '0.75')):
    cid = 'drishti_' + k
    add(key=key(cid), claim=f"{k} aspect fraction = {fr}", cur=rows[cid]['sc'], state='sourced_inference', sup='INFERENCE',
        corpus=[ev('bphs_pg0254_c01', "in slabs of quarters i.e l14, 112,3l4thand fult", '2-5')],
        inf="Printed fractions are OCR-garbled ('l14, 112, 3l4'); read as 1/4, 1/2, 3/4 from the clear phrase 'in slabs of quarters' and 'fult'(=full).",
        prop=cite('bphs_pg0254_c01', '', '2-5'), act='recite')
SA = {'jupiter': '5,9', 'mars': '4,8', 'saturn': '3,10'}
for p, hs in SA.items():
    cid = 'special_aspect_' + p
    assert rows[cid]['vt'] == hs
    add(key=key(cid), claim=f"{p.capitalize()} special aspect houses = {hs}", cur=rows[cid]['sc'], state='sourced_fact', sup='FACT',
        corpus=[ev('bphs_pg0254_c01', "Saturn, Jupiter and Mars have special aspects respectively on 3rd and lOth", '2-5'),
                ev('bphs_pg0254_c01', "5th and 9th, and 4th and 8th", '2-5')],
        prop=cite('bphs_pg0254_c01', '', '2-5'), act='recite')

# ---------------- naisargika
NB = {'sun': 60, 'moon': 51.43, 'venus': 42.86, 'jupiter': 34.29, 'mercury': 25.71, 'mars': 17.14, 'saturn': 8.57}
for p, v in NB.items():
    cid = 'naisargika_bala_' + p
    assert abs(float(rows[cid]['vn']) - v) < 1e-6
    add(key=key(cid), claim=f"{p.capitalize()} naisargika bala = {v} virupa", cur=rows[cid]['sc'], state='sourced_inference', sup='INFERENCE',
        corpus=[ev('bphs_pg0275_c01', "Divide one Rupa (or 60 Virupas) by 7 and multiply", '14'),
                ev('bphs_pg0275_c01', "Moon: 0.857 Rupa", '14')],
        inf="Rule: 60/7 virupas x (1..7 for Saturn, Mars, Mercury, Jupiter, Venus, Moon, Sun); the row's virupa figure is that product rounded to 2 dp (chunk gives the Rupa table: Sun 1.0, Moon 0.857, Mars 0.286, Mercury 0.429, Jupiter 0.571, Venus 0.714, Saturn 0.143).",
        prop=cite('bphs_pg0275_c01', '', '14'), act='recite')

# ---------------- own sign
OWN = {
 'sun': ('leo', [('bphs_pg0050_c01', "Leo is ruled by the Sun", '12')], 'sourced_fact', None),
 'moon': ('cancer', [('bphs_pg0050_c01', "It rises with its back and is ruled by the Moon", '10-11')], 'sourced_fact', None),
 'mars': ('aries,scorpio', [('bphs_pg0049_c02', "Its ruler is Mars", '6-7'), ('bphs_pg0051_c01', "Man is its ruler", '15-16')], 'sourced_inference',
          "Aries ruler printed 'Mars'; Scorpio's ruler is printed as 'Man' (OCR for Mars)."),
 'mercury': ('gemini,virgo', [('bphs_pg0050_c01', "nrler is MercurY", '9-91'), ('bphs_pg0051_c01', "Its ruler is Mcrcury", '13-14')], 'sourced_fact', None),
 'jupiter': ('sagittarius,pisces', [('bphs_pg0051_c01', "is .lorded by Jupiter", '17-18'), ('bphs_pg0052_c01', "It is ruled by Jupiter", '22-24')], 'sourced_fact', None),
 'venus': ('taurus,libra', [('bphs_pg0049_c02', "is lorded by Venus", '8'), ('bphs_pg0051_c01', "Its lord is Vcnus", '15-16')], 'sourced_fact', None),
 'saturn': ('capricorn,aquarius', [('bphs_pg0051_c02', "C;apricorn is lorded by Satugr", '19-20'), ('bphs_pg0052_c01', "Its lord is Saturn, the Sun's offspring", '21-21t')], 'sourced_inference',
            "Capricorn's lord is printed 'Satugr' (OCR for Saturn); Aquarius states Saturn clearly."),
}
for p, (signs, evs, st, infs) in OWN.items():
    cid = 'own_sign_' + p
    assert rows[cid]['vt'] == signs, rows[cid]
    corpus = [ev(c, qt, s) for c, qt, s in evs]
    add(key=key(cid), claim=f"{p.capitalize()} owns {signs}", cur=rows[cid]['sc'], state=st, sup='FACT' if st == 'sourced_fact' else 'INFERENCE',
        corpus=corpus, inf=infs, prop=' ; '.join(cite(c, '', s) for c, _, s in evs), act='recite',
        note="Existing citation 'BPHS Ch.1' does not resolve: sign lordships are stated in the 'Zodiacal Signs Described' chapter (Chapter 4 per the page-47 header). Ch.3 (bphs_pg0038_c01/02) also treats the same signs as own houses of the respective planets.")

# ---------------- panchanga
PAN = {
 'drekkana_span': ('Each drekkana spans 10 deg', [ev('bphs_pg0069_c01', "Each decanate is l0 degrees in length", '7-8')], 'sourced_fact', None, "Translator's note under sloka 7-8; existing citation 'BPHS Ch.7' - the decanate text is in the 16-divisions chapter (Chapter 6 header on page 68)."),
 'hora_span': ('Each hora spans 15 deg', [ev('bphs_pg0067_c01', "Half of Rasi is called Hora", '5-6'), ev('bphs_pg0067_c01', "lordehipo of Horas (15\" cach) of the 12 signs", '5-6')], 'sourced_fact', None, None),
 'karana_count': ('There are 11 karanas', [ev('jataka_parijata_pg0648_c01', "(Garaja karana), he will be without foes and powerful", '101-102'),
                                           ev('jataka_parijata_pg0649_c01', "(Karana) called (Chatushpada), will have a multitude of misfortunes", '103')], 'sourced_inference',
                  "Count of the eleven karana names listed across Jataka Parijata Adh. IX slokas 101-103 (Bava, Balava, Kaulava, Thaitila, Garaja, Vanija, Vishti, Sakuna, Chatushpada, 'Migavakaram'[Naga, OCR], Kimstughna); no sloka states the number 11. Not found in the held BPHS.",
                  None),
 'nakshatra_count': ('There are 27 nakshatras', [ev('bphs_pg0024_c01', "The said zodiac comprises of 27 asterisms commencing from Aswini", '4-6')], 'sourced_fact', None, None),
 'nakshatra_span': ('A nakshatra spans 13 deg 20 min (13.3333)', [ev('bphs_pg0501_c01', "of a nakshatra 13'-20'", None)], 'sourced_fact', None,
                    "Printed '13\\'-20\\'' (and 't3\"-20\\'' elsewhere in the chunk) = 13 deg 20 min; decimal 13.3333 is its conversion."),
 'pada_span': ('A nakshatra pada spans 3 deg 20 min (3.3333)', [ev('bphs_pg0501_c01', "consists of four padas (quarters) -of 3\"-20'each", None)], 'sourced_fact', None, None),
 'rasi_count': ('There are 12 rasis', [ev('bphs_pg0024_c01', "divided in 12 parts equal to 12 Rasis", '4-6')], 'sourced_fact', None, None),
 'rasi_span': ('A rasi spans 30 deg', [ev('bphs_pg0501_c01', "The longitudinal span of a rasi or sign being 30o", None)], 'sourced_fact', None, None),
 'tithi_count': ('30 tithis in a lunar month', [ev('jataka_parijata_pg0616_c01', "Each lunar month conststs of thirty tithis", '29-30')], 'sourced_fact', None,
                 "Translator's note in Jataka Parijata (not BPHS); replaces the non-provenance token 'classical_tradition'."),
}
for cid, (cl, corpus, st, infs, nt) in PAN.items():
    assert cid in rows
    add(key=key(cid), claim=cl, cur=rows[cid]['sc'], state=st, sup='FACT' if st == 'sourced_fact' else 'INFERENCE', corpus=corpus, inf=infs,
        prop=' ; '.join(dict.fromkeys(cite(c['chunk_id'], '', c['sloka_printed']) for c in corpus)), act='recite', note=nt)
add(key=key('yoga_panchanga_count'), claim='There are 27 panchanga yogas (Sun+Moon longitude division)', cur=rows['yoga_panchanga_count']['sc'],
    state='unsourced_marked', sup='NONE',
    corpus=[ev('jataka_parijata_pg0646_c01', "if born in the dmmr (Sowbhagya) yoga", '97')] if False else [],
    prop=None, act='mark_unsourced',
    note="Jataka Parijata Adh. IX slokas 97-99 (jataka_parijata_pg0646_c01..0648_c01) list the birth-yoga names, but the enumeration is OCR-damaged (about 25-26 names legible, Shukla/Brahma lost) and no sloka states '27'; the count was not reconstructed. Token 'classical_tradition' is not provenance (SS ruling Q3). Value stays.")

# ---------------- ayanamsha
add(key=key('lahiri_ayanamsha_2000'), claim='Lahiri ayanamsha at J2000.0 = 23.853 deg (~23d51m)', cur=rows['lahiri_ayanamsha_2000']['sc'], state='not_a_classical_claim', sup='NONE',
    note="Modern computed convention (20th-century Lahiri/Chitrapaksha standard), not a statement of any held classical text; the held corpus gives no ayanamsha value. Not checked against an ephemeris here (read-only research lane; no JH-parity oracle).", act='none')

# ---------------- saptavargaja
SV = {
 'moolatrikona': ('sourced_fact', '45', [ev('bphs_pg0264_c01', "Moolatrikona Rasi, it gets 45 Virupas, in own Rasi 30 Virupas", '2-4')], None),
 'own': ('sourced_fact', '30', [ev('bphs_pg0264_c01', "Moolatrikona Rasi, it gets 45 Virupas, in own Rasi 30 Virupas", '2-4')], None),
 'friend': ('sourced_fact', '15', [ev('bphs_pg0264_c01', "friend's Rasi 20 Virupas, friend's Rasi 15 Virupas", '2-4')], None),
 'great_friend': ('contradicted', '22.5', [ev('bphs_pg0264_c01', "friend's Rasi 20 Virupas, friend's Rasi 15 Virupas", '2-4'),
                                           ev('bphs_pg0289_c01', "60, 45, 30, 22,15,t,4,2 and 0 are the Subhankas", '7-9')],
                  "Ch.27 sloka 2-4 states 20 virupas for the extreme-friend sign; row has 22.5 (the 45-30-22.5-15-7.5-3.75-1.875 halving series). Ch.28 sloka 7-9 prints the series as '60,45,30,22,15,t,4,2,0' (22 for extreme friend) - the held text is internally inconsistent (20 vs 22)."),
 'neutral': ('contradicted', '7.5', [ev('bphs_pg0264_c01', "neutral's Rasi l0 Virupas, enemy's Rasi 4 Virr:pas", '2-4'),
                                     ev('bphs_pg0289_c01', "60, 45, 30, 22,15,t,4,2 and 0 are the Subhankas", '7-9')],
             "Ch.27 sloka 2-4 states 10 virupas for a neutral sign; row has 7.5. Ch.28 sloka 7-9 shows an OCR-illegible token ('t') for the equal's-sign value."),
 'enemy': ('contradicted', '3.75', [ev('bphs_pg0264_c01', "neutral's Rasi l0 Virupas, enemy's Rasi 4 Virr:pas", '2-4')],
           "Ch.27 states 4 virupas (row 3.75): rounding-level difference; both Ch.27 and Ch.28 print 4."),
 'great_enemy': ('contradicted', '1.875', [ev('bphs_pg0264_c01', "extreme enemy's Rasi 2 Virupas", '2-4')],
                 "Ch.27 states 2 virupas (row 1.875): rounding-level difference; Ch.28 prints 2 as well."),
}
for k, (st, val, corpus, nt) in SV.items():
    cid = 'saptavargaja_' + k
    assert abs(float(rows[cid]['vn']) - float(val)) < 1e-9, (cid, rows[cid])
    if st == 'contradicted':
        add(key=key(cid), claim=f"Saptavargaja points for {k.replace('_', ' ')} sign = {val} virupa", cur=rows[cid]['sc'], state=st, sup='CONTRADICTS', corpus=corpus, note=nt,
            act='acharya', q="BPHS Ch.27 sloka 2-4 (Santhanam) prints the saptavargaja series 45, 30, 20, 15, 10, 4, 2 virupas (moolatrikona, own, extreme friend, friend, equal, enemy, extreme enemy), while the platform stores 45, 30, 22.5, 15, 7.5, 3.75, 1.875 and Ch.28 sloka 7-9 prints 60,45,30,22,15,?,4,2,0. Which series is canonical for the platform?")
    else:
        add(key=key(cid), claim=f"Saptavargaja points for {k.replace('_', ' ')} sign = {val} virupa", cur=rows[cid]['sc'], state=st, sup='FACT', corpus=corpus,
            prop=cite('bphs_pg0264_c01', '', '2-4'), act='recite')

# ---------------- shadbala min
SM = {'sun': ('6.5', "The Sun : 6.5 Rupas"), 'moon': ('6', "The Moon: 6.0 Rupas"), 'mars': ('5', "Mars : 5.0 Rupas"),
      'mercury': ('7', "MercurY : 7'0 RuPas"), 'jupiter': ('6.5', "Jupiter : 6.5 Rupas"), 'venus': ('5.5', "Venus : 5.5 Rupas"), 'saturn': ('5', "Saturn - 5.0 Rapas")}
for p, (v, qt) in SM.items():
    cid = 'shadbala_min_' + p
    assert abs(float(rows[cid]['vn']) - float(v)) < 1e-9
    add(key=key(cid), claim=f"{p.capitalize()} minimum shadbala = {v} rupa", cur=rows[cid]['sc'], state='sourced_fact', sup='FACT',
        corpus=[ev('bphs_pg0286_c01', qt, '32-33')], prop=cite('bphs_pg0286_c01', '', '32-33'), act='recite',
        note="Sloka 32-33 gives the same requirement in virupas (390, 360, 300, 420, 390, 330, 300) for 'the Sun etc. (upto Saturn)'.")

# ---------------- varga divisors
VD = {
 'd1': ('not_a_classical_claim', None, "Rasi (the sign itself) is the first of the 16 vargas listed in bphs_pg0067_c01 (sloka 2-4); divisor 1 is identity, a platform convention."),
 'd2': ('sourced_fact', [ev('bphs_pg0067_c01', "Half of Rasi is called Hora", '5-6')], None),
 'd3': ('sourced_fact', [ev('bphs_pg0068_c01', "Oue third of a Rasi is called Drckkane", '7-8')], None),
 'd4': ('sourced_fact', [ev('bphs_pg0069_c01', "Each Chathurthamsa is one fourth of a Rasi", '9')], None),
 'd7': ('sourced_fact', [ev('bphs_pg0070_c01', "(one seventh of a Rasi)", '10-11')], None),
 'd9': ('sourced_fact', [ev('bphs_pg0071_c01', "Navamsa is l/9th part of a sign", '12')], None),
 'd10': ('sourced_fact', [ev('bphs_pg0072_c01', "the l0 Dasamsas each of 3o are reckoned", '13-14')], None),
 'd12': ('sourced_fact', [ev('bphs_pg0072_c01', "(one twelfth of a sign", '15')], None),
 'd16': ('sourced_fact', [ev('bphs_pg0073_c01', "(l6th part of a sigrr", '16')], None),
 'd20': ('sourced_fact', [ev('bphs_pg0075_c01', "Vimsamsa ( l/20th of a lign", '17-21')], None),
 'd24': ('sourced_fact', [ev('bphs_pg0076_c01', "The Siddhamsa (ll24th part of a", '22-23')], None),
 'd27': ('sourced_fact', [ev('bphs_pg0078_c01', "there are 27 such divisions in a sign", '24-26')], None),
 'd30': ('sourced_inference', [ev('bphs_pg0079_c01', "in order rules 5,5,8,7 and 5 degrees", '27-28')],
         "Trimsamsa is NOT an equal 1/30 division: each odd sign is cut into five unequal parts of 5,5,8,7,5 degrees (30 = total degrees). The numeric 'divisor 30' is only the nominal D30 label."),
 'd40': ('sourced_fact', [ev('bphs_pg0079_c01', "CHATI/ARIMSAMSA ( I l40th part of a sign)", '29-30')], None),
 'd45': ('sourced_fact', [ev('bphs_pg0080_c01', "AKSHA VEDAMSA (Il4sth part of a sisn)", '31-32')], None),
 'd60': ('sourced_fact', [ev('bphs_pg0082_c01', "SHASHTIAMSA (ll60th part a of sign or half-a-", '33-41')], None),
}
for d, (st, corpus, nt) in VD.items():
    cid = 'varga_divisor_' + d
    assert int(rows[cid]['vn']) == int(d[1:])
    if st == 'not_a_classical_claim':
        add(key=key(cid), claim='D1 varga divisor = 1', cur=rows[cid]['sc'], state=st, sup='NONE', note=nt, act='none')
    elif d == 'd30':
        add(key=key(cid), claim='D30 varga divisor = 30', cur=rows[cid]['sc'], state=st, sup='INFERENCE', corpus=corpus,
            inf="The chunk names the Trimsamsa and its 5/5/8/7/5-degree lords; 30 as a 'divisor' is not stated.", prop=cite(corpus[0]['chunk_id'], '', '27-28'),
            act='acharya', note=nt,
            q="Does the platform treat the D30 'divisor' of 30 as a count of equal parts? BPHS (Santhanam) divides each sign's 30 degrees into five unequal Trimsamsas (5,5,8,7,5 degrees), so a plain 'divide the sign into 30 parts' use would be non-classical.")
    else:
        add(key=key(cid), claim=f"{d.upper()} varga divisor = {d[1:]} (sign split into {d[1:]} parts)", cur=rows[cid]['sc'], state=st, sup='FACT', corpus=corpus,
            prop=cite(corpus[0]['chunk_id'], '', corpus[0]['sloka_printed']), act='recite',
            note="Existing citation 'BPHS Ch.7' - the sixteen divisions are described in Chapter 6 of this edition (page-68 header)." if d == 'd2' else None)

# ---------------- vimshopaka
VW = json.load(open(BASE + '/_vw.json')) if False else None
SHAD = {'d1': 6, 'd2': 2, 'd3': 4, 'd9': 5, 'd12': 2, 'd30': 1}
SAPT = {'d1': 5, 'd2': 2, 'd3': 3, 'd7': 2.5, 'd9': 4.5, 'd12': 2, 'd30': 1}
DASH = {'d1': 3, 'd2': 1.5, 'd3': 1.5, 'd7': 1.5, 'd9': 1.5, 'd10': 1.5, 'd12': 1.5, 'd16': 1.5, 'd30': 1.5, 'd60': 5}
SHOD = {'d1': 3.5, 'd2': 1, 'd3': 1, 'd4': .5, 'd7': .5, 'd9': 3, 'd10': .5, 'd12': .5, 'd16': 2, 'd20': .5, 'd24': .5, 'd27': .5, 'd30': 1, 'd40': .5, 'd45': .5, 'd60': 4}
for scheme, mp in (('shadvarga', SHAD), ('saptavarga', SAPT), ('dashavarga', DASH), ('shodashavarga', SHOD)):
    for d, v in mp.items():
        cid = f'vimshopaka_{scheme}_{d}'
        assert abs(float(rows[cid]['vn']) - v) < 1e-9, (cid, rows[cid]['vn'], v)
        if scheme == 'shadvarga':
            add(key=key(cid), claim=f"Vimshopaka {scheme} weight {d.upper()} = {v}", cur=rows[cid]['sc'], state='sourced_fact', sup='FACT',
                corpus=[ev('bphs_pg0094_c01', "respectively are 6,2, 4,5,2 and l", '17-19')], prop=cite('bphs_pg0094_c01', '', '17-19'), act='recite',
                note="Divisions listed in the same sloka: Rasi, Hora, decanate, Navamsa, Dvadasamsa, Trimsamsa; 'l' is OCR for 1.")
        elif scheme == 'saptavarga':
            add(key=key(cid), claim=f"Vimshopaka {scheme} weight {d.upper()} = {v}", cur=rows[cid]['sc'], state='sourced_inference', sup='INFERENCE',
                corpus=[ev('bphs_pg0094_c01', "we get Sapta Varga, the Vimsopaka", '17-19'), ev('bphs_pg0094_c01', "strength for which is : 5, 2, 3,2t,412, 2 and 1", '17-19')],
                inf="Printed series '5, 2, 3, 2t, 412, 2 and 1' (OCR 2t=2.5, 412=4.5; total 20) is assigned to Rasi, Hora, Drekkana, Saptamsa, Navamsa, Dvadasamsa, Trimsamsa by order - the sloka does not say where Saptamsa is inserted among the Shadvarga divisions.",
                prop=cite('bphs_pg0094_c01', '', '17-19'), act='recite')
        elif scheme == 'dashavarga':
            if d in ('d1', 'd60'):
                add(key=key(cid), claim=f"Vimshopaka {scheme} weight {d.upper()} = {v}", cur=rows[cid]['sc'], state='sourced_fact', sup='FACT',
                    corpus=[ev('bphs_pg0095_c01', "5 for Shashtiamsa", '20')], prop=cite('bphs_pg0095_c01', '', '20'), act='recite',
                    note="Sloka 20 (OCR-fused 'is3forRas'): 3 for Rasi, 5 for Shashtiamsa, 'the other 8 divisions' share the rest.")
            else:
                add(key=key(cid), claim=f"Vimshopaka {scheme} weight {d.upper()} = {v}", cur=rows[cid]['sc'], state='sourced_inference', sup='INFERENCE',
                    corpus=[ev('bphs_pg0095_c01', "for the other 8 divisions' I I each'", '20')],
                    inf="'I I each' is OCR for 1 1/2 each; confirmed by the notes table (bphs_pg0096_c01 values 1.5) and the total of 20.",
                    prop=cite('bphs_pg0095_c01', '', '20'), act='recite')
        else:
            if d == 'd1':
                add(key=key(cid), claim=f"Vimshopaka {scheme} weight {d.upper()} = {v}", cur=rows[cid]['sc'], state='sourced_fact', sup='FACT',
                    corpus=[ev('bphs_pg0097_c01', "in Rasi Division under Shodasa Varga, you fintl 3.5", None)],
                    prop=cite('bphs_pg0097_c01', ''), act='recite', note="Sloka 21-25 prints 'Rasi 3l' (OCR 3.5); the notes state 3.5 for Rasi explicitly.")
            elif v == .5:
                add(key=key(cid), claim=f"Vimshopaka {scheme} weight {d.upper()} = {v}", cur=rows[cid]['sc'], state='sourced_fact', sup='FACT',
                    corpus=[ev('bphs_pg0095_c01', "and the rest of the nine divisions each a half", '21-25')], prop=cite('bphs_pg0095_c01', '', '21-25'), act='recite')
            else:
                qt = {'d2': "Hora 1", 'd3': "decanate l", 'd9': "Navamsa 3", 'd16': "Shodasamsa", 'd30': "Trimsamsa l", 'd60': "Shashtiamsa"}[d]
                add(key=key(cid), claim=f"Vimshopaka {scheme} weight {d.upper()} = {v}", cur=rows[cid]['sc'], state='sourced_fact', sup='FACT',
                    corpus=[ev('bphs_pg0095_c01', qt, '21-25')], prop=cite('bphs_pg0095_c01', '', '21-25'), act='recite',
                    note="Sloka 21-25: 'Hora 1, Trimsamsa 1, decanate 1, Shodasamsa 2, Navamsa 3, Rasi 3.5, Shashtiamsa 4, the rest of the nine divisions each a half' (single digits '1' OCR'd as 'l').")

missing = set(rows) - done
assert not missing, sorted(missing)[:10]
assert len(OUT) == 203, len(OUT)
json.dump(OUT, open(BASE + '/ledger_constants.json', 'w'), indent=1, ensure_ascii=False)
print('constants rows', len(OUT))
from collections import Counter
print(Counter(o['state'] for o in OUT))
bad = verify_all()
print('quote problems', len(bad))
for b in bad[:60]:
    print(b)
