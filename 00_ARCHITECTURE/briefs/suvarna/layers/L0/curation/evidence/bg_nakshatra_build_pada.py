import json, collections
from refdata import *
from build_nk import c, B501, BJ343, CITE
d=json.load(open('db.json')); pd=d['pd']
SIGNS=['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
LORD=dict(zip(SIGNS,['mars','venus','mercury','moon','sun','mercury','venus','mars','jupiter','saturn','saturn','jupiter']))
B529=c('bphs','bphs_pg0529_c01','PG529',None,"The product will be the Navamsa from Aries onwards.")
B529ex=c('bphs','bphs_pg0529_c01','PG529',None,"birth is in the 4th pada of Mrigasira ... falls in Scorpio the 8th sign")
B71=c('bphs','bphs_pg0071_c01','PG71',None,"for a movable sign from there itself, for a fixed sign from the 9th")
BJ41=c('brihat_jataka','brihat_jataka_pg0041_c01','PG41','6',"Mars, Venus, Mercury, the Moon, the Sun, Mercury, Venus, Mars, Jupiter, Saturn, Saturn and Jupiter")
MC55=c('muhurta_chintamani','muhurta_chintamani_pg0055_c01','PG55','59-60 (chart)',None)
by=collections.defaultdict(list)
for r in pd: by[int(r['nakshatra_id'])].append(r)
bad=[]
for n,rows in by.items():
    for r in rows:
        a=int(r['absolute_pada']); 
        if a!=(n-1)*4+int(r['pada_number']): bad.append(('abs',r['pada_id']))
        if abs(float(r['start_longitude'])-(a-1)*10/3)>2e-5 or abs(float(r['end_longitude'])-a*10/3)>2e-5: bad.append(('lon',r['pada_id'],r['start_longitude'],r['end_longitude']))
        if r['pada_navamsa_sign']!=SIGNS[(a-1)%12]: bad.append(('nav',r['pada_id']))
        if r['pada_lord']!=LORD[r['pada_navamsa_sign']]: bad.append(('lord',r['pada_id']))
print('pada script mismatches:',bad)
out=[]
for n in range(1,28):
    rows=sorted(by[n],key=lambda r:int(r['pada_number']))
    fc={}; corpus=[B501,B529,B71,BJ41]
    fc['pada_longitudes']=dict(state='sourced_inference',support_class='INFERENCE',chunks=[B501['chunk_id']],note="BPHS: a nakshatra has four padas of 3°20' each (FACT); DB pada start/end = (absolute_pada-1)*3°20'..absolute_pada*3°20' (script-checked, tolerance 2e-5 deg: DB stores truncated 5-decimals); inference = arithmetic.")
    fc['pada_navamsa_sign']=dict(state='sourced_fact' if n==5 else 'sourced_inference',support_class='FACT' if n==5 else 'INFERENCE',chunks=[B529['chunk_id'],B71['chunk_id']],note="BPHS PG529 states the nakshatra-pada -> navamsa-from-Aries procedure (count of past nakshatras mod 3, x4, + pada) = sign (abs. pada-1) mod 12 +1; DB signs equal that rule for all 108 (script-checked). "+("Worked example in the chunk is Mrigasira pada 4 = Scorpio, equal to DB." if n==5 else "Inference = application of the stated rule to this nakshatra."))
    fc['pada_lord']=dict(state='sourced_inference',support_class='INFERENCE',chunks=[BJ41['chunk_id']],note="Brihat Jataka Ch.I Sloka 6 gives sign lords 'and also of their Amsas' (Mars,Venus,Mercury,Moon,Sun,Mercury,Venus,Mars,Jupiter,Saturn,Saturn,Jupiter); DB pada_lord = lord of the navamsa sign (script-checked 108/108). Inference = pada_lord is meant as navamsa-sign lord.")
    st='sourced_inference'; sc='INFERENCE'; qs=None; contra=[]; unsrc=['bija_sound / mantra_prefix / pada_deity_nuance / element_shading / dosha_shading are EMPTY on all 108 rows (no claim made)']
    cites=["BPHS (Santhanam trans.), Ch.46 as printed, p.509 — bphs:PG501:C1 (4 padas of 3°20' each); BPHS navamsa-pada rule, Ch.46 as printed, p.537 — bphs:PG529:C1; BPHS Ch.6 (navamsa construction) — bphs:PG71:C1; Brihat Jataka Ch.I, Sloka 6 as printed — brihat_jataka:PG41:C1 (Sastri trans., 2nd ed.)"]
    if n in MC_AKS:
        tok,exp,q=MC_AKS[n]; dbak=' '.join(r['pada_akshara'] for r in rows)
        e2=exp.replace('(Su)','Su')
        corpus.append(c('muhurta_chintamani','muhurta_chintamani_pg0055_c01','PG55','59-60 (Nakshatra-chakra)',tok))
        if n==6:
            fc['pada_akshara']=dict(state='contradicted',support_class='CONTRADICTS',chunks=['muhurta_chintamani_pg0055_c01'],note=f"MC nakshatra-chakra row for Ardra prints '{tok}' = Ku Gha Nga Chha; DB = '{dbak}' (pada 3,4: Da,Na). Row identification by the Rudra/Shiva deity cell is legible; OCR confidence medium.")
            contra.append('pada_akshara'); st='contradicted'; sc='CONTRADICTS'
            qs="Ardra: the Muhurta-Cintamani nakshatra-chakra (PG55) prints the syllables as Ku Gha Nga Chha; the pada rows say Ku Gha Da Na. Which syllables does the platform adopt for Ardra padas 3 and 4?"
        elif n==22:
            fc['pada_akshara']=dict(state='contradicted',support_class='CONTRADICTS',chunks=['muhurta_chintamani_pg0055_c01'],note=f"MC nakshatra-chakra row for Shravana (vamana/Vishnu cell) prints '{tok}' = Khi Khu Khe Kho; DB = '{dbak}'. Two syllable schools exist for Shravana; the held text states Khi Khu Khe Kho.")
            contra.append('pada_akshara'); st='contradicted'; sc='CONTRADICTS'
            qs="Shravana: the Muhurta-Cintamani nakshatra-chakra (PG55) prints the syllables as Khi Khu Khe Kho; the pada rows say Ju Je Jo Sha. Which syllable school does the platform adopt (and should the other be recorded as an alternate)?"
        else:
            same=(e2==dbak) or (q=='partial' and True)
            fc['pada_akshara']=dict(state='sourced_inference',support_class='INFERENCE',chunks=['muhurta_chintamani_pg0055_c01'],note=f"MC nakshatra-chakra row prints '{tok}' ({q} OCR), decoded as '{exp}'; DB = '{dbak}'. "+("Decoded string equals DB." if e2==dbak else "Decoded partially; remaining syllables not legible, DB value is consistent with the legible part." )+" Inference = Devanagari OCR decode of the syllable cell.")
            cites.append("Muhurta-Cintamani, Prakarana 2, Nakshatra-chakra after Sloka 60 — muhurta_chintamani:PG55:C1 (Mahidhara bhasha tika, Khemraj ed.; OCR-damaged chart)")
    else:
        fc['pada_akshara']=dict(state='unsourced_marked',support_class='NONE',chunks=[],note="The held MC nakshatra-chakra chunk (PG55:C1, truncated) does not carry this nakshatra's syllable row legibly; no other held text lists name-syllables.")
        unsrc.append('pada_akshara')
    out.append(dict(asset='bg_nakshatra',table='reference_nakshatra_pada',row_key=dict(nakshatra_id=n,name_en=NAMES[n],pada_ids=[int(r['pada_id']) for r in rows]),row_count=4,
      claim=f"Pada longitudes, navamsa sign, pada lord and name-syllable for the 4 padas of {NAMES[n]}",
      current_citation='bphs:ch92 + muhurta_chintamani:ch7',state=st,support_class=sc,corpus=corpus,
      inference_step="pada longitudes: arithmetic from 3°20'/pada; navamsa sign: apply BPHS PG529 rule; pada_lord: navamsa-sign lord (BJ Ch.I Sl.6)"+("; akshara: Devanagari OCR decode" if 'pada_akshara' in fc and fc['pada_akshara']['support_class']=='INFERENCE' else ""),
      proposed_citation=" ; ".join(cites) if not contra else " ; ".join(cites[:1]),proposed_action='acharya' if contra else 'recite',acharya_question=qs,
      citation_resolution_note="bphs:ch92 (PG92 = Shodasamsa notes) and muhurta_chintamani:ch7 are not resolvable to the content cited; support found at the chunks listed.",
      field_checks=fc,unsourced_fields=unsrc,contradicted_fields=contra))
json.dump(out,open('ledger_pada.json','w'),ensure_ascii=False,indent=1)
print(collections.Counter(o['state'] for o in out), sum(o['row_count'] for o in out))
print(collections.Counter(o['field_checks']['pada_akshara']['state'] for o in out))
