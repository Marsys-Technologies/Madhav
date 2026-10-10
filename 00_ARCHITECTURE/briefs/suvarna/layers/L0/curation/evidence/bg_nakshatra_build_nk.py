import json
from refdata import *
d=json.load(open('db.json')); nk={int(r['nakshatra_id']):r for r in d['nk']}
def c(t,ch,pg,sl,qt): return dict(text_id=t,chunk_id=ch,page=pg,sloka_printed=sl,quote=qt)
B500=c('bphs','bphs_pg0500_c01','PG500',None,"Table of Dasas Constellations Dasa Lord Years")
B501=c('bphs','bphs_pg0501_c01','PG501',None,"One nakshatra measures 13°-20' of arc and consists of four padas")
B501b=c('bphs','bphs_pg0501_c02','PG501',None,"Span in Degrees (table continues; figures only)")
B502=c('bphs','bphs_pg0502_c01','PG502',None,"Chittra (3,4) ... Swati (1,2,3,4) ... Revti (1,2,3,4)")
BJ343=c('brihat_jataka','brihat_jataka_pg0343_c01','PG343',None,"Ruler of the Aswini Bharani Krittika ... Good . Ketu .... Good Venus")
B29=c('bphs','bphs_pg0029_c01','PG29',None,"Likewise, the Nakshatras too have presiding deities. The 27 deities are")
MC36=c('muhurta_chintamani','muhurta_chintamani_pg0036_c01','PG36','1',"अरिवनीके अस्विनीकुमार । भरणीके यम । एसे ही कत्तकाका अग्नि")
MC37=c('muhurta_chintamani','muhurta_chintamani_pg0037_c02','PG37','2-5',"उत्तरा्यरोहिण्यो भास्करश्च धुवं स्थिरम्")
MC38=c('muhurta_chintamani','muhurta_chintamani_pg0038_c01','PG38','6-8',"हस्ताश्विपुष्यामिजितः क्षिप्रं लघु")
MC94=c('muhurta_chintamani','muhurta_chintamani_pg0094_c01','PG94','25-26',"उत्तराषाढा, अभिजित्‌ नेवला । रोहिणी, मृगशिर सप")
MC95=c('muhurta_chintamani','muhurta_chintamani_pg0095_c01','PG95','29',"राक्षसगण । तीनों पूर्वा ... मनुष्यगण । ... देवगण है")
MC96=c('muhurta_chintamani','muhurta_chintamani_pg0096_c02','PG96','34',"ज्येष्ठा ... आद्य नाडी ... Puṣya, Indu's star ... middle (madhya)")
MC97=c('muhurta_chintamani','muhurta_chintamani_pg0097_c01','PG97','34',"Marriage ... within one and the same nāḍī is not good")
MC54=c('muhurta_chintamani','muhurta_chintamani_pg0054_c02','PG54','59-60',"अरिवनी घोडाकासा मुख, भरणी भग, कृ (क्षुर)")
MC55=c('muhurta_chintamani','muhurta_chintamani_pg0055_c01','PG55','59-60',"त्रिकोण, ० वामन, ध० मृदंग, श० वृत्त; पू० मञ्चा")
MC105=c('muhurta_chintamani','muhurta_chintamani_pg0105_c02','PG105','55',"उत्तराषाढाका चतुर्थचरण एवं श्रवणकं आदि ४ घटी अभिजित")
MC102=c('muhurta_chintamani','muhurta_chintamani_pg0102_c01','PG102','43',"ज्येष्ठा, रेवती, आरकेषाके अन्त्यकी २ घटी, अश्विनी मघा मूके आदिकी २ घटी")
B1018=c('bphs','bphs_pg1018_c01','PG1018','3',"last two ghatikas of Revti and first two ... of Aswini")
MC51=c('muhurta_chintamani','muhurta_chintamani_pg0051_c01','PG51','48',"मीन कुम्भकं चनदरमामें पञ्चक होते हँ")
CITE={ # paste-able citation fragments (house style)
'span':"BPHS (Santhanam trans.), Ch.46 as printed, p.509-510 (nakshatra/rasi table; 13°20' per nakshatra) — bphs:PG501:C1, bphs:PG501:C2, bphs:PG502:C1",
'lord':"BPHS (Santhanam trans.), Ch.46 as printed, printed p.508 (Table of Dasas, nakshatra->Dasa lord) — bphs:PG500:C1; Brihat Jataka Ch.XVI (nakshatra rulers) — brihat_jataka:PG343:C1 (Sastri trans., 2nd ed.)",
'deity':"Muhurta-Cintamani, Nakshatra-prakarana (Prakarana 2), Sloka 1 as printed — muhurta_chintamani:PG36:C1 (Mahidhara bhasha tika, Khemraj ed.)",
'type':"Muhurta-Cintamani, Prakarana 2, Slokas 2-8 as printed — muhurta_chintamani:PG37:C2, muhurta_chintamani:PG38:C1 (Mahidhara bhasha tika, Khemraj ed.)",
'yoni':"Muhurta-Cintamani, Vivaha-prakarana (Prakarana 6), Slokas 25-26 as printed — muhurta_chintamani:PG94:C1 (Mahidhara bhasha tika, Khemraj ed.)",
'gana':"Muhurta-Cintamani, Vivaha-prakarana (Prakarana 6), Sloka 29 as printed — muhurta_chintamani:PG95:C1 (Mahidhara bhasha tika, Khemraj ed.)",
'nadi':"Muhurta-Cintamani, Vivaha-prakarana (Prakarana 6), Sloka 34 as printed — muhurta_chintamani:PG96:C2, muhurta_chintamani:PG97:C1 (Mahidhara bhasha tika, Khemraj ed.)",
'form':"Muhurta-Cintamani, Prakarana 2, Slokas 59-60 as printed — muhurta_chintamani:PG54:C2, muhurta_chintamani:PG55:C1 (Mahidhara bhasha tika, Khemraj ed.)",
'gandanta':"BPHS (Santhanam trans.), Gandanta chapter, Sloka 3 as printed — bphs:PG1018:C1; Muhurta-Cintamani, Vivaha-prakarana, Sloka 43 as printed — muhurta_chintamani:PG102:C1",
'panchaka':"Muhurta-Cintamani, Prakarana 2, Sloka 48 as printed (Moon in Pisces/Aquarius = panchaka) — muhurta_chintamani:PG51:C1",
'abhijit':"Muhurta-Cintamani, Vivaha-prakarana, Sloka 55 as printed (Abhijit = 4th pada of Uttarashadha + first 4 ghatis of Shravana) — muhurta_chintamani:PG105:C2",
}
UNSRC=['name/alt_names/devanagari (identity vocabulary)','yoni_sex','varna (nakshatra-level 7-class scheme; MC gives varna by rashi only)','tatva','guna','pakshi','nakshatra_gender','disha','shakti','body_part','paramayus','naisargika_maturity_age','deity_domain','motivation','secondary_deities','favorable_acts / prohibited_acts (MC Prakarana 2 pp.36-37 lists acts per nakshatra, but the DB vocabulary was NOT mapped/compared in this pass)','is_mula_sangya']
FINF={'span_start_end':"arithmetic from the stated 13°20' span and the 0°-Aries origin",'presiding_deity':'name equivalence (Soma=Chandra, Rudra=Shiva, Savitar=Surya, Brihaspati=ijya, Sarpa=uraga, Apas=jala, Aja-Ekapada=Ajacharana, Vidhi=Brahma) where the DB name differs from the printed one','nadi':"'each taken with its pair' read as the named star plus the following star",'yoni_en/yoni_sa':'Goat/Aja accepted as variant of the printed Mesha (ram)','symbol':'form-word equivalence and order-based assignment of the abbreviated tika list','is_panchaka':'Moon in Aquarius/Pisces mapped to the stars lying in those signs via the BPHS rasi table','rashis_spanned':'arithmetic placement of 276°40\'-280°53\' in Capricorn'}
out=[]
for n in range(1,29):
    r=nk[n]; fc={}; corpus=[]; cites=[]; qs=[]; contra=[]; has_inf=False; has_fact=False
    def add(field,state,sc,chunks,note,cite=None):
        global has_inf,has_fact
        fc[field]=dict(state=state,support_class=sc,chunks=[x['chunk_id'] for x in chunks],note=note)
        for x in chunks:
            if x not in corpus: corpus.append(x)
        if sc=='INFERENCE': has_inf=True
        if sc=='FACT': has_fact=True
        if sc=='CONTRADICTS': contra.append(field)
        if cite and sc!='CONTRADICTS' : cites.append(CITE[cite])
    fc['identity']=dict(state='not_a_classical_claim',support_class='NONE',chunks=[],note='name_sa_iast/devanagari/name_en/alt_names/nakshatra_id are platform vocabulary and ids')
    if n<=27:
        add('span_start_end',('sourced_inference'),'INFERENCE',[B501],f"BPHS states 13°20' per nakshatra and that rasis/nakshatras are reckoned from 0° Aries; DB start/end ({r['start_longitude']}-{r['end_longitude']}) equals (n-1)*13°20' .. n*13°20' (script-checked). Inference = arithmetic from the stated span + zero point.",'span')
        add('rashis_spanned','sourced_fact','FACT',[B501,B501b,B502],f"BPHS rasi->nakshatra table lists {NAMES[n]} under {'/'.join(BPHS_RASHI[n])}; DB rashis_spanned={r['rashis_spanned']} (script-checked 27/27 equal). Table columns are OCR-separated; pada-split rows (e.g. 'Krittika (1)' / 'Krittika (2,3,4)') read in printed order.",'span')
        add('vimshottari_lord+ruling_planet','sourced_fact','FACT',[B500,BJ343],f"BPHS Table of Dasas groups {NAMES[n]} under {BPHS_LORD[n]}; DB vimshottari_lord={r['vimshottari_lord']}, ruling_planet={r['ruling_planet']} (equal). Table columns (nakshatra groups vs lords) are OCR-separated and aligned by the printed Sun..Venus order; Brihat Jataka Ch.XVI independently lists the same ruler order (OCR columns, same alignment step).",'lord')
        dm,kind=MC_DEITY[n]
        add('presiding_deity','sourced_fact' if kind=='D' else 'sourced_inference','FACT' if kind=='D' else 'INFERENCE',[MC36],f"MC Sloka 1 / tika gives '{dm}'; DB presiding_deity='{r['presiding_deity']}'. "+("Same deity name." if kind=='D' else "Equivalence step needed (synonym/epithet or OCR-joined verse word).")+(" NOTE BPHS PG29:C1 also prints a 27-name deity list (separate OCR column); its mid-list alignment is unreliable (slots near Ashlesha/Magha read 'Rahu'/'Sun') so it is NOT used as support." if n in (9,10,11,12,13) else ""),'deity')
        add('gana','sourced_fact','FACT',[MC95],f"MC Sloka 29 lists {NAMES[n]} under {MC_GANA[n]}-gana; DB gana={r['gana']}.",'gana')
        yk=MC_YONI[n]; dbn=r['yoni_en']
        if yk=='deer(harina)':
            add('yoni_en/yoni_sa','contradicted','CONTRADICTS',[MC94],f"MC tika gives harina (deer) for Jyeshtha/Anuradha; DB yoni_en='{dbn}', yoni_sa='{r['yoni_sa']}' (hare). Likely mriga/harina translation variant, but the held text says deer. Acharya to rule.")
            qs.append(f"{NAMES[n]}: Muhurta-Cintamani PG94 (Sloka 25-26 tika) gives the yoni animal as harina (deer); the row says Hare (Shasha). Is 'Hare' an accepted equivalent, or should the row read Deer (Mriga)?")
        elif yk=='sheep(mesha)':
            add('yoni_en/yoni_sa','sourced_inference','INFERENCE',[MC94],f"MC tika gives mesha/medha (ram) for {NAMES[n]}; DB yoni_en='Goat', yoni_sa='Aja'. Inference: Goat/Aja treated as equal to Mesha(ram); accept as variant.",'yoni')
        else:
            add('yoni_en/yoni_sa','sourced_fact','FACT',[MC94],f"MC tika lists {NAMES[n]} under {yk}; DB yoni_en={dbn}.",'yoni')
        nm=MC_NADI[n]
        if r['nadi']==nm:
            head=n in NADI_NAMED_HEAD
            add('nadi','sourced_fact' if head else 'sourced_inference','FACT' if head else 'INFERENCE',[MC96,MC97],f"MC Sloka 34 puts {NAMES[n]} in {nm} nadi; DB nadi={r['nadi']}."+("" if head else " This star is one of the 'each taken with its pair' stars: inference = the pair is the star following the named one (tika: 'two nakshatras each, counted from these'); 9/9/9 totals confirm."),'nadi')
        else:
            add('nadi','contradicted','CONTRADICTS',[MC96,MC97],f"MC Sloka 34 puts {NAMES[n]} in {nm} nadi; DB nadi={r['nadi']}. DB follows a plain Adi,Madhya,Antya cycle through nakshatra_id; MC uses the 9/9/9 zig-zag grouping.")
            qs.append(f"{NAMES[n]}: Muhurta-Cintamani PG96-97 (Sloka 34) places it in {nm} nadi (Adya/Madhya/Antya grouping); the row says {r['nadi']}. Which nadi allocation does the platform adopt, and should the whole 27-row nadi column be re-derived from the cited grouping?")
        mt=MC_TYPE[n]
        add('muhurta_type','sourced_fact','FACT',[MC37,MC38],f"MC Slokas 2-8 class {NAMES[n]} as {mt}; DB muhurta_type={r['muhurta_type']}. (MC uses Kshipra and Laghu as two names of one class.)",'type')
        fm,mk=MC_FORM[n]
        if mk=='X':
            add('symbol','contradicted','CONTRADICTS',[MC54,MC55],f"MC Sloka 59-60 tika form for {NAMES[n]}: {fm}; DB symbol='{r['symbol']}' (no alternative matches). OCR position->nakshatra assignment of the abbreviated list is by printed order (inference). Different-tradition symbol, low severity; confidence medium because the tika list is abbreviated and assigned by printed order.")
            qs.append(f"{NAMES[n]}: Muhurta-Cintamani PG54-55 (Sloka 59-60 tika) gives its form as {fm}; the row's symbol field lists '{r['symbol']}'. Which tradition's symbol does the platform want, and is the MC form to be added as an alternative?")
        else:
            add('symbol','sourced_fact' if mk=='M' else 'sourced_inference','FACT' if mk=='M' else 'INFERENCE',[MC54,MC55],f"MC Sloka 59-60 tika form for {NAMES[n]}: {fm}; DB symbol='{r['symbol']}' contains a matching alternative."+(" Equivalence step needed." if mk=='I' else "")+" Abbreviated tika list is assigned to nakshatras by printed order (inference).",'form')
            if mk=='M': pass
        g=r['is_gandanta']=='t'; sh=n in (1,9,10,18,19,27)
        if g==sh: add('is_gandanta','sourced_fact','FACT',[B1018,MC102],f"BPHS gandanta Sloka 3 and MC Sloka 43 name Revati/Ashwini, Ashlesha/Magha, Jyeshtha/Moola junctions; DB is_gandanta={r['is_gandanta']} is consistent for {NAMES[n]}.",'gandanta')
        else:
            add('is_gandanta','contradicted','CONTRADICTS',[B1018,MC102],f"BPHS Sloka 3 and MC Sloka 43 make {NAMES[n]} a nakshatra-gandanta star (first 2 ghatikas of Ashwini); DB is_gandanta=false although Magha, Moola, Ashlesha, Jyeshtha, Revati are true.")
            qs.append("Ashwini: BPHS PG1018 (Sloka 3) and Muhurta-Cintamani PG102 both include Ashwini (first 2 ghatikas) in nakshatra-gandanta, but is_gandanta=false for it while the other five junction stars are true. Set it true (gandanta is a junction condition on the first 2 ghatikas of Ashwini/Magha/Moola and last 2 of Revati/Ashlesha/Jyeshtha), or is the flag meant at whole-star level?")
        if n in (23,24,25,26,27):
            add('is_panchaka','sourced_inference','INFERENCE',[MC51],"MC Sloka 48: Moon in Pisces or Aquarius makes panchaka. Inference: Dhanishtha(3,4) .. Revati are the stars within Aquarius/Pisces (BPHS rasi table); DB flag true. Dhanishtha is only half within Aquarius.",'panchaka')
        else:
            add('is_panchaka','sourced_inference','INFERENCE',[MC51],f"MC Sloka 48 (panchaka = Moon in Pisces/Aquarius); {NAMES[n]} lies outside those signs per the BPHS rasi table and DB is_panchaka=false (absence-based inference).",'panchaka')
        # row-level
    else: # Abhijit
        add('span_start_end','sourced_inference','INFERENCE',[MC105],f"MC Sloka 55: Abhijit = 4th pada of Uttarashadha + first 4 ghatis of Shravana. DB 276.66667-280.88889 = 266°40'+10° .. 280°+4/60*13°20' (script-checked). Inference: ghati->degree uses the nominal 60-ghati nakshatra.",'abhijit')
        add('rashis_spanned','sourced_inference','INFERENCE',[MC105,B502],"Capricorn: 276°40'-280°53' lies within Capricorn (270-300°) by the BPHS rasi table; arithmetic inference.",'abhijit')
        add('presiding_deity','sourced_inference','INFERENCE',[MC36],"MC tika: 'abhijit ka vidhi' (Vidhi = Brahma, equivalence step); DB 'Brahma'.",'deity')
        add('muhurta_type','sourced_fact','FACT',[MC38],"MC Sloka 6: Hasta, Ashwini, Pushya, Abhijit = Kshipra/Laghu; DB 'Laghu'.",'type')
        add('symbol','sourced_inference','INFERENCE',[MC54,MC55],"MC tika list ends '... u. mancha, a. | trikona' across the PG54/PG55 break; 'a.' read as Abhijit by printed order; DB 'Triangle (three stars of Lyra / Vega)' matches 'triangle'.",'form')
        add('yoni_en/yoni_sa','sourced_fact','FACT',[MC94],"MC tika puts Abhijit with Uttarashadha under nakula (mongoose); DB yoni_en/yoni_sa are EMPTY for Abhijit (completeness gap, not a conflicting value).",'yoni')
        qs.append("Abhijit: Muhurta-Cintamani PG94 (Sloka 25-26 tika) lists Abhijit in the mongoose (Nakula) yoni with Uttarashadha; the row has no yoni. Fill yoni_en=Mongoose / yoni_sa=Nakula, or keep Abhijit outside the 27-fold yoni/kuta scheme?")
        fc['vimshottari_lord+ruling_planet']=dict(state='unsourced_marked',support_class='NONE',chunks=[],note="DB 'sun' for Abhijit: no held chunk gives an Abhijit dasa lord (only inferable from its UAshadha/Shravana position, which would be Sun/Moon).")
        fc['gana']=dict(state='unsourced_marked',support_class='NONE',chunks=[],note="MC Sloka 29 lists 27 stars only; no gana for Abhijit. DB 'Deva' is unsourced.")
        fc['nadi']=dict(state='unsourced_marked',support_class='NONE',chunks=[],note="DB nadi empty; MC Sloka 34 does not place Abhijit.")
    unsrc=[u for u in UNSRC]
    if n==28: unsrc+= ['vimshottari_lord','gana','varna','nadi (empty)']
    states=[v['state'] for v in fc.values()]
    if contra: st='contradicted'; sc='CONTRADICTS'
    elif has_inf: st='sourced_inference'; sc='INFERENCE'
    elif has_fact: st='sourced_fact'; sc='FACT'
    else: st='unsourced_marked'; sc='NONE'
    cur=r['classical_source']
    note=("Existing citation '%s' is a book-chapter token: bphs PG92 is Shodasamsa notes (not nakshatra content) so it cannot be resolved; the supporting chunks below were found elsewhere in the held corpus."%cur) if n<=27 else ("Existing citation 'muhurta_chintamani:ch7' cannot be resolved to a chunk (Prakarana 7 is Vadhu-pravesha etc.); the Abhijit support sits in Prakarana 2 (PG36-38, PG54-55) and Prakarana 6 (PG94, PG105).")
    ac=" || ".join(qs) if qs else None
    out.append(dict(asset='bg_nakshatra',table='reference_nakshatra',row_key=dict(nakshatra_id=n,name_en=NAMES[n]),row_count=1,
      claim=f"Nakshatra reference attributes for {NAMES[n]} (span, rashis, dasa lord, deity, gana, yoni, nadi, type, symbol, gandanta/panchaka flags)",
      current_citation=cur,state=st,support_class=sc,corpus=corpus,
      inference_step="; ".join(f"{k}: {FINF.get(k,'see field note')}" for k,v in fc.items() if v['support_class']=='INFERENCE') or None,
      proposed_citation=(" ; ".join(dict.fromkeys(cites))) if cites else None,
      proposed_action='acharya' if (contra or qs) else 'recite',acharya_question=ac,
      citation_resolution_note=note,field_checks=fc,unsourced_fields=unsrc,contradicted_fields=contra))
json.dump(out,open('ledger_nk.json','w'),ensure_ascii=False,indent=1)
import collections
print(collections.Counter(o['state'] for o in out))
fs=collections.Counter()
for o in out:
    for k,v in o['field_checks'].items(): fs[(k,v['state'])]+=1
for k,v in sorted(fs.items()): print(k,v)
print([ (o['row_key']['nakshatra_id'],o['contradicted_fields']) for o in out if o['contradicted_fields']])
