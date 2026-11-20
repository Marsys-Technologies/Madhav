import re, glob, os
D='/private/tmp/claude-504/scratch/curation/bg_reference_A/dump/'
CH={}
for f in glob.glob(D+'*.tsv'):
    t=os.path.basename(f)[:-4]
    for line in open(f,errors='replace'):
        if '\t' not in line: continue
        cid,txt=line.rstrip('\n').split('\t',1)
        CH[cid]=re.sub(r'\s+',' ',txt)

def tid(cid):
    return re.sub(r'_pg\d+_c\d+$','',cid)
def page(cid):
    return 'PG'+str(int(re.search(r'_pg(\d+)_',cid).group(1)))
def cshort(cid):
    m=re.search(r'_pg(\d+)_c(\d+)$',cid); return f"{tid(cid)}:PG{int(m.group(1))}:C{int(m.group(2))}"

# key -> (chunk_id, regex, sloka_printed)
E={
# --- planets: dignity ---
'bphs_exalt_signs':('bphs_pg0037_c02', r'iries, Taurus, Capricorn, Virgo, Cancer, Pisces and Libra','49-50'),
'bphs_exalt_deg':('bphs_pg0038_c01', r'deepest exaltation degrees are respectively 10,\s?3, 2g, 15, 5, 27 1nd 20','49-50'),
'bphs_debil7':('bphs_pg0038_c01', r'in the seventh sign from tle saij exaltation sign each planet has its own debilitation','49-50'),
'pd_exalt_signs':('phaladeepika_pg0040_c01', r'Mesha, Vrishabha, Makara, Kanya, Karkataka, Meena and Tula are the exaltation signs','6'),
'pd_mt':('phaladeepika_pg0041_c01', r'Simha, Vrishbha, Mesha, Kanya, Dhanus, Tula and Kumbha are the Moolatrikona','7'),
'bphs_mt_sun':('bphs_pg0038_c01', r"In Leo the first 20 degrees are the Sun's Moolatrikona",'51-54'),
'bphs_mt_mars':('bphs_pg0038_c01', r'thc first 12 dcgrees in Aries as Moolatrikona','51-54'),
'bphs_mt_merc':('bphs_pg0038_c02', r'first 15 degrces are exaltation zone, the next 5 degrees Moolatri- kona','51-54'),
'bphs_mt_jup':('bphs_pg0038_c02', r'first one third of Sagittarius is the Moolatrikona of Jupiter','51-54'),
'bphs_mt_ven':('bphs_pg0038_c02', r'Venus divides Libra into two halves keeping thc first as Moolatrikona','51-54'),
'bphs_mt_sat':('bphs_pg0038_c02', r"Saturn's arrangements are same in Aquarius as the Sun has in Leo",'51-54'),
'jp_mt_moon':('jataka_parijata_pg0045_c01', r'first three degrees\s+cf Vrishabha \(\^W\) foim the exaltation portion of the\s+Moon, and the rest, her Moolathrikona|first three degrees cf Vrishabha[^.]{0,90}Moolathrikona','26-28'),
'pd_lords':('phaladeepika_pg0040_c01', r'are respectively declared the lords of the signs from Mesha onwards','6'),
'bphs_benefic':('bphs_pg0026_c01', r'are malefics while the rest are benefics','11'),
'bphs_vim_names':('bphs_pg0499_c01', r'Dasas of the Sun, the Moon, Mars, Ralru, Jupiter, Saturn, Meicury','15'),
'bphs_vim_years':('bphs_pg0499_c02', r"18, 16, 19,l'1,7 and20 in thai order",'15'),
'bphs_vim_table':('bphs_pg0500_c01', r"Mercury Ketu Yenus 6 t0'! I E l 6 l9 17 7 20",None),
'bphs_rahu_ex':('bphs_pg0573_c02', r'The sign of exahation of Rahu is Taurus',  '34-39'),
'bphs_ketu_ex':('bphs_pg0574_c01', r'sign of exaltation of Ketu is Scorpio',  '34-39'),
'bphs_node_mt':('bphs_pg0574_c01', r'The Moola tikonas of Rahu and Ketu are Gemini and Sagittarius respectively','34-39'),
'bphs_node_own':('bphs_pg0574_c01', r'The own signs of Rahu and Ketu are Aquarius and Scorpio in that order','34-39'),
'bphs_node_own_alt':('bphs_pg0574_c01', r'Virgo is the own sign of Rahu and Pisces is the own sign of Ketu','34-39'),
'bphs_rahu_debil':('bphs_pg0574_c02', r'sign of debilitation \(Scorpio\)','40-43'),
'bphs_nodes_exalt_views':('bphs_pg0038_c01', r'As for the exaltations and debilitation of the nodes, there are different views','49-50 (Notes)'),
'hs_node_views':('hora_sara_pg0019_c01', r'Bhavartha Ratriakara states that Rahu is exalted in Taurus and Ketu in Scorpio',None),
'hs_node_fall':('hora_sara_pg0019_c01', r'Both are exalted in Scorpio and are in fall in Taurus',None),
'jp_rahu':('jataka_parijata_pg0045_c01', r'Rahu; Mithuna \(fag\*\), the exaltation',None),
'bphs_nodes_180':('bphs_pg0024_c01', r'are exactly apart lS0degrees mutually','Ch.3 Notes (sl.2-3)'),
'bphs_nodes_shadowy':('bphs_pg0023_c01', r'Rahu and Ketu though recognised as planets for astrological delineations are shadowy',None),
# --- signs ---
'pd_lords_signs':('phaladeepika_pg0040_c01', r'are respectively declared the lords of the signs from Mesha onwards','6'),
'bphs_modality':('bphs_pg0048_c01', r'Movable, Fixed and Duafale the names given to the 12 signs in order','5-6'),
'bphs_modality_note':('bphs_pg0048_c01', r'Movable are Aries, Cancer, Libra and Capricorn','5-6 (Notes)'),
'pd_modality':('phaladeepika_pg0042_c01', r'\(Chara\)-moveable or cardinal, \(Sthira\)- fixed and \(Ubhaya\)-dual','9'),
'pd_odd_male':('phaladeepika_pg0042_c01', r'\(5\) odd and even and \(6\) male and female','9'),
'bphs_male_female':('bphs_pg0048_c01', r'thesJ are male and female','5-6'),
'pd_quad':('phaladeepika_pg0041_c01', r'Mesha- Vrishabha, Simha, Dhanus \(latter half\) and Makara \(first half\) are quadruped signs',None),
'pd_biped':('phaladeepika_pg0041_c01', r'The first half of Dhanus, Kanya, Mithuna, Kumbha and Tula are bipeds or human signs',None),
'pd_centiped':('phaladeepika_pg0041_c01', r'Vrischika is a [^ ]+ \(Keeta . reptile\) or centiped sign',None),
'bphs_aries':('bphs_pg0049_c01', r'It is a quadr_ upcd sign','6-7'),
'bphs_aries_fiery':('bphs_pg0049_c02', r'rises with its back \(a prishtodaya si!n\) and is fieryl','6-7'),
'bphs_taurus':('bphs_pg0049_c02', r'It is_long and is a quadruped sign','8'),
'bphs_taurus_earthy':('bphs_pg0049_c02', r'An earthy sign, Taurus','8'),
'bphs_gemini_airy':('bphs_pg0050_c01', r'It lives in the west and is an ,airy sigo','9-9½'),
'bphs_gemini_biped':('bphs_pg0050_c01', r'Itis a biped eign as bell','9-9½'),
'bphs_cancer_watery':('bphs_pg0050_c01', r'is a watery Big!','10-11'),
'bphs_cancer_feet':('bphs_pg0050_c01', r'It has many feet \(i.e. it is a centipcdc eigp\)','10-11'),
'bphs_leo_quad':('bphs_pg0050_c01', r'Leo is ruled by the Sun and is srtwic. It is a quadruped sign','12'),
'bphs_virgo_biped':('bphs_pg0050_c01', r'It is a biped sign and resideq in tbc south','13-14'),
'bphs_libra_biped':('bphs_pg0051_c01', r'has a medium build and is a biped sign. Its lord is Vcnus','15-16'),
'bphs_scorpio_centi':('bphs_pg0051_c01', r'Scorpio has a slender physique and is a centipede rign','15-16'),
'bphs_scorpio_lord':('bphs_pg0051_c01', r'Man is its ruler','15-16'),
'bphs_sag':('bphs_pg0051_c01', r'Sagittarius is biped in first half. Its second half is quadruped','17-18'),
'bphs_sag_fiery':('bphs_pg0051_c01', r'It has strength in night and is fiery','17-18'),
'bphs_cap':('bphs_pg0052_c01', r'Its first half is quadrupcd and second half footless rnoving in water','19-20'),
'bphs_cap_earthy':('bphs_pg0052_c01', r'It is aa earthy eign','19-20'),
'bphs_aqu_airy':('bphs_pg0052_c01', r'It resorts to deep water and is airy','21-22'),
'bphs_aqu_biped':('bphs_pg0052_c01', r'It has a.medium build and a biped sign','21-22'),
'bphs_pisces':('bphs_pg0052_c01', r'It is I watery sigo','22-24'),
'bphs_pisces_footless':('bphs_pg0052_c01', r'It is footless and has a medium build','22-24'),
'bphs_limbs':('bphs_pg0047_c01', r'Head, face, arms, heart, stomach, hip, space below nlvel, privities, thighs, knees, ankles and feet','4-4½'),
'pd_limbs':('phaladeepika_pg0040_c01', r'\(11\) the two calves and \(12\) the two feet',  '4'),
'pd_limbs_a':('phaladeepika_pg0039_c01', r'\(1\) the head \(2\) the face \(3\) the breast \(4\) the heart','4'),
# --- houses ---
'bphs_classes':('bphs_pg0101_c01', r'Kendras \(engles\) are.specially known as ascendant, the 4th house','33-36'),
'bphs_panaphara':('bphs_pg0101_c01', r'2nd. stb, 8th and the llth are Panapharas or succedents|Panapharas or succedents while the 3rd, 6th: gth and the l2th are called Apoklimas','33-36'),
'bphs_trika':('bphs_pg0101_c01', r'Evil houses or Trika houses are the 6th, 8th and the 12th','33-36'),
'bphs_upachaya':('bphs_pg0101_c01', r'The 3rd, 6th, l0th and I lth houses are UPachaYa','33-36'),
'bphs_kona':('bphs_pg0101_c01', r'The 5th and 9th from the ascendant are known by the name Kona or trine','33-36'),
'bphs_bhava_names':('bphs_pg0101_c01', r'Thanu, Dbane, Sahaja, Bandhu, Putra, Ari \(etR\), Yuvati, Randhra, Dharma, K8rma, habha and Vyaya','37-38'),
'bphs_bhava_ind':('bphs_pg0102_c01', r'Bandhu Putra Ari Yuvati Randhra Dharma Karma Laabha : rclatives : progeny : enemies : wife longevity','37-38 (Notes)'),
'pd_house_names1':('phaladeepika_pg0043_c01', r'Vitta \(f\^TrT- wealth\), Vidya \(ft\^n _ learning\)','10-16'),
'pd_house_dusthana':('phaladeepika_pg0046_c01', r'The 8th, the 6th and the 12th houses are known as Dusslhanas','17'),
'pd_house_kendra':('phaladeepika_pg0046_c01', r'The 1st, the 10th, the 7th and the 4th houses are known by the terms Kendra','17'),
'pd_house_panaphara':('phaladeepika_pg0046_c01', r'the 2nd, the 5th, the 8th and the 11th are known as Pana- phara','18'),
'pd_house_apoklima':('phaladeepika_pg0046_c01', r'The 3rd, the 6th, the 9th and the 12th are Apoklima houses','18'),
'pd_house_upachaya':('phaladeepika_pg0046_c01', r'The 10th, the 3rd, the 6th and the 11th houses are called Upa- chaya','18'),
'pd_house_trikona':('phaladeepika_pg0046_c01', r'the 9th and the 5th are known as Tri- kona','18'),
'pd_karakas':('phaladeepika_pg0196_c01', r'The Karakas of the Bhavas beginning with the Lagna or the rising sign are \(1\) the Sun \(2\) Jupiter','17'),
'jp_karakas':('jataka_parijata_pg0107_c01', r'The Karakas of the Bhavas beginning\s+with the Lagoa or the rising sign are','51'),
'bphs_maraka':('bphs_pg0440_c01', r'The 2nd an<l 7th are denoted as Maraka houses','Ch.44 Notes (sl.2-5)'),
'uk_lagna_kona':('uttara_kalamrita_pg0090_c01', r'Lagna is both a kana and a kendra',None),
'hs_lagna_trine':('hora_sara_pg0014_c01', r'According to some astrologers, Lagna is also to be considered as a trine',None),
'pd_lagna_strength':('phaladeepika_pg0073_c01', r'The strength of the Lagna is equal to that of its lord','6'),
'pd_adh4_s2':('phaladeepika_pg0071_c01', r'The Moon gets Cheshtabala when ahe is full','2'),
# --- aspects ---
'bphs_asp_7':('bphs_pg0254_c01', r'Ail planets aspect the Tth fully','2-5'),
'bphs_asp_special':('bphs_pg0254_c01', r'Saturn, Jupiter and Mars have special aspects respectively on 3rd and l0th, 5th and 9th, and 4th and 8th|Saturn, Jupiter and Mars have special aspects respectively on 3rd and','2-5'),
'bphs_asp_slabs':('bphs_pg0254_c01', r'gradually in slabs of quarters i.e l14, 112,3l4thand fult','2-5'),
'uk_asp':('uttara_kalamrita_pg0041_c01', r'All planets aspect fully the seventh from themselves','UK Adh.IV (translated text)'),
'uk_asp_sat':('uttara_kalamrita_pg0040_c01', r'Shant has full aspect on the third and the tenth houses from himself',None),
'uk_asp_jup':('uttara_kalamrita_pg0040_c02', r'Jupiter has a full aspect on the fifth and ninth houses from himself',None),
'uk_asp_mars':('uttara_kalamrita_pg0040_c02', r'Mars has a full aspect on the fourth and eighth houses from himself',None),
'uk_rahu_asp':('uttara_kalamrita_pg0041_c01', r'According to Parasara, Rahu aspects 5, 7, 9 and 12 fully, 2 and 10 by half, and 3 and 6 by a quar- ter',None),
'bphs_rahu_has_asp':('bphs_pg0110_c01', r'This goes to prove that Rahu has aspects',None),
# --- vargas ---
'bphs_16':('bphs_pg0067_c01', r'Rasi, Hora, Drekkana, Chathurthamsa, Sapthamamsa, Navamsa, Dssanoamsa, Dvadasamsa, Shodas- amsa, Vinsamsa','2-4'),
'bphs_16b':('bphs_pg0067_c01', r'Chaturvimsamsa, Sapthavimsamsa,\s+Trimsamsa, Khavedamsa, Akshavedamsa and Shashtiamsa','2-4'),
'bphs_bhamsa':('bphs_pg0077_c01', r'BTIAMSA \(NAKSHATRAMSA OR SAPTAVIMS. AMSA\)','24-26'),
'bphs_hora':('bphs_pg0067_c01', r'The first half of an old sign ris the Hora ruled by tbe Sun','5-6'),
'bphs_vuse1':('bphs_pg0091_c01', r'fortunes from Chaturthamsa, sons and grandsons from saptha- msa, spouse from Navamsa, power \(and position\) from Dasamsa, parents from Dvadasamsa','1-8 (Ch.7)'),
'bphs_vuse0':('bphs_pg0090_c01', r'The physique from the ascendant, through coborn frorn decanate','1-8 (Ch.7)'),
'bphs_vuse2':('bphs_pg0091_c01', r'learn- ing from Chathur Vimsamsa. strength and weakness from Bhamsa,evil, effects from Trimsamsa','1-8 (Ch.7)'),
'bphs_vuse3':('bphs_pg0091_c01', r'auspicious and inauspicious effects from Khavedamsa, and all indications from both Aksha- vedamsa and Shashtiamsa','1-8 (Ch.7)'),
'bphs_vuse_hora':('bphs_pg0090_c01', r'wealth ltom Hora','1-8 (Ch.7)'),
'bphs_vuse_conv':('bphs_pg0091_c01', r'benefits and adversities through conu.yances from Shodasamsa. worship from Vimsamsa','1-8 (Ch.7)'),
'bphs_vnote':('bphs_pg0091_c01', r'Dasamamsa for power and position \(i.e. livelihood etc.\)','Ch.7 Notes'),
'sar_panchamsa':('saravali_pg0136_c02', r'Even, if one planet occupies its own Panchamsa, the subject will become a ruler','63'),
'sar_panchamsa_note':('saravali_pg0136_c02', r'Panchamsa division is a little bit different from Trimsamsa','63 (Notes)'),
# --- upagrahas ---
'bphs_dhuma':('bphs_pg0042_c01', r'Add 4 signs 13 degrees and 20 minutes of arc to the Sun.s longitude','61-64'),
'bphs_vyati':('bphs_pg0042_c01', r'Reduce Dhooma from 12 signs to arrive at Vyatipata','61-64'),
'bphs_pariv':('bphs_pg0042_c01', r'Add six signs to Vyatipata to kqow the position of Parivesha','61-64'),
'bphs_chapa':('bphs_pg0042_c01', r'Deduct Parivesha from 12 signs to arrive at the position of Ctapa','61-64'),
'bphs_upaketu':('bphs_pg0042_c01', r'Add 16 degrees 40 minutes to Chapa which will give Ketu \(Upaketu\) who is a malefic','61-64'),
'bphs_chapa_inausp':('bphs_pg0042_c01', r'\(Indra Dhanus\) who is also inauspicious','61-64'),
'bphs_upa_malefic':('bphs_pg0042_c01', r'These are planets devoid of splendour which are malefics by nature and cause affliction','61-64'),
'bphs_pariv_extreme':('bphs_pg0042_c01', r'He is extremely inauspicious','61-64'),
'bphs_vyati_inausp':('bphs_pg0042_c01', r'Vyatipata is also inauspicious','61-64'),
'bphs_dhuma_inausp':('bphs_pg0042_c01', r'the all-inauspicious Dhooma','61-64'),
'bphs_kv5':('bphs_pg0044_c01', r'Ardha Prahara, Yamaghanlakd, Mrityu, Kala and Gulika are the 5 Kala Velas','65-70 (Notes)'),
'bphs_kv_div':('bphs_pg0044_c01', r'The day duration according to latitude is divided into eight equal parts','65-70 (Notes)'),
'bphs_gulika_pos':('bphs_pg0045_c01', r'The degree ascending at tne time of start of Gulika.s portion','70'),
'bphs_gulika_son':('bphs_pg0045_c01', r'Gulika, son of Saturn','70 (Notes)'),
'bphs_yama_son':('bphs_pg0045_c01', r"Jupirer,s son, yamaghantaka",'70 (Notes)'),
'bphs_ardha_son':('bphs_pg0045_c01', r"Ardhaprahara, Mercury's son",'70 (Notes)'),
'bphs_mrityu_son':('bphs_pg0045_c01', r'Mrityu, son of Mars','70 (Notes)'),
'bphs_kala_son':('bphs_pg0045_c01', r'Kala, a son of the Sun','70 (Notes)'),
'bphs_mandi':('bphs_pg0044_c01', r'Guliks and Mandi are one and the same and.not different','65-70 (Notes)'),
'bphs_gulika_beg':('bphs_pg0060_c01', r"Gulika's longitude will corrcspond to the beginning of Saturn's Muhurta only",'Ch.4 Notes'),
# --- strength ---
'b_uchcha':('bphs_pg0263_c01', r'Deduct frcjm the longitude of thc planet its \(decp\) debilitation point','1'),
'b_uchcha2':('bphs_pg0263_c01', r"divided by 3 which is the planet's uchchabata or exaltation strength",'1'),
'b_uchcha3':('bphs_pg0264_c01', r'Marimum Uchcha bala is always 60 shashtiamsas or I Rupa','1 (Notes)'),
'b_sapta':('bphs_pg0264_c01', r"If a planet is in its Moolatrikona Rasi, it gets 45 Virupas, in own Rasi 30 Virupas, cxtreme. friend's Rasi 20 Virupas",'2-4'),
'b_sapta2':('bphs_pg0264_c01', r"friend's Rasi 15 Virupas, neutral's Rasi l0 Virupas, enemy's Rasi 4 Virr:pas and in extreme enemy's Rasi 2 Virupas",'2-4'),
'b_sapta_vargas':('bphs_pg0264_c01', r'Hora, Decanate, Saptamamsa. Navamm, Dvadasamsa and Trimsamsa','2-4'),
'b_ojha':('bphs_pg0264_c02', r'Each of Venus and the Moon in cven Rasis and others in odd Rasis acquire a quarter of Rupa','4'),
'b_ojha15':('bphs_pg0265_c01', r'Each of Jupiter, the Sun, Mars, Mercury and Saturn get 15 Virupas if they are placed in odd Rasis','4 (Notes)'),
'b_kendradi':('bphs_pg0265_c01', r'A planet in an angle gets full ;trength while one in succedent house gets balfand the one in cadent house gets a quarter','5'),
'b_drek':('bphs_pg0265_c01', r'Male, female and .hernaphro- dite planets respectively got a quarter Ruln acbording to placements in the first, second arrd third decaqatcs|Male, female and .hernaphro- dite planets respectively g[a-z]+ a quarter','6'),
'b_drek_note':('bphs_pg0265_c02', r'Male planet in lst Drelckana. Female planet in 2nd Drekkana. Eunuch planbt in 3rd Drekkana','6 (Notes)'),
'b_sthana':('bphs_pg0266_c01', r'\(5\) Drekkana bala be all added together to get net Sthaana bala','6 (Notes)'),
'b_sthana_list':('bphs_pg0263_c01', r'This strength comprises of lhe following considerations : l. Uchcha Bala','1 (Notes)'),
'b_dig':('bphs_pg0266_c01', r'Deduct the 4th house \(i.e. Nadir\) from the longitudes of Sun and Mars','7-8'),
'b_dig_note':('bphs_pg0266_c01', r'Jupiter and Mercury have Digbata ln the ascendant','7-8 (Notes)'),
'b_dig_note2':('bphs_pg0266_c01', r'Venus and the Moon have this bala in the 4th hquse','7-8 (Notes)'),
'b_nath':('bphs_pg0267_c01', r'Moon, Mars and Saturn cet this strength in the night. The Sun, Jupit-er and Venus eet iiurnat ctr.ength','9-10 (Notes)'),
'b_nath2':('bphs_pg0267_c01', r'Mercury, irrespective of day and night, gets full Nathonnatha Bala','9-10'),
'b_kala_list':('bphs_pg0267_c01', r'Nathonnatha Bala \(diurnal and nocturnal strengths\)','9-10 (Notes)'),
'b_paksha':('bphs_pg0268_c01', r'The Paksha bala of benefic should be deducted from 60 which will go to each malefic as Paksha bala','10-11'),
'b_tribhaga':('bphs_pg0268_c01', r'One Rupa is obtained by Mercury \(if birth is\) in the first one third part of day time','12'),
'b_tribhaga2':('bphs_pg0268_c01', r'the Sun in the second one third part of the day and by Saturn in the last third part of the day','12'),
'b_vmdh':('bphs_pg0269_c01', r'15,.30, 45 and 60 Virupas are in order given to Varsha lord, Maasa lord Dina lord and Hora lord|30, 45 and 60 Virupas are in order given to Varsha lord, Maasa lord Dina lord and Hora lord','13'),
'b_naisarg':('bphs_pg0275_c01', r'Divide one Rupa \(or 60 Virupas\) by 7 and multiply the resultant product by I to 7','14'),
'b_naisarg2':('bphs_pg0275_c01', r'Sun : l\.\(X\[ Rupa Moon: 0\.857 Rupa','14 (Notes)'),
'b_ayana':('bphs_pg0276_c01', r"The Sun's Ayana Bala is again multiplied by 2",'15-17 (Notes)'),
'b_ayana_dir':('bphs_pg0276_c01', r'when the Moon or Saturn have southern Kranti or when the Sun, Mars, Jupiter or Venus have Northern Kranti, take plus','15-17 (Notes)'),
'b_cheshta_sm':('bphs_pg0283_c01', r"The Sun's Cheshta Bala \(or motional strength\) will correspond to his Ayana Bela",'18'),
'b_cheshta_moon':('bphs_pg0283_c01', r"The Moon's Paksha Bala will itself be her Cheshta Bala",'18'),
'b_cheshta_8':('bphs_pg0284_c01', r'The strengths allotted due to such 8 motions are : 60, 30, 15, 30, 15. 7.5, 45 and 30|The strengths allotted due to such 8 motions are : 60, 30, 15, 30, 15','22-23'),
'b_cheshta_k':('bphs_pg0284_c01', r'divided by 3 which will denote the motional strength of the planet','24-25'),
'b_drig':('bphs_pg0283_c01', r'Reduce one fourth of the Drishti Pinda if a planet has malefic aspects on it and add a fourth if it is aspected by a benefic','19'),
'b_drig2':('bphs_pg0283_c01', r'Super add the entire aspect of Mercury and Jupiter','19'),
'b_yuddha':('bphs_pg0283_c01', r"the difference between the Shadbalas of the two should be added to the victor's shadbala",'20'),
'pd_war':('phaladeepika_pg0071_c01', r'In planetary war, those that are posited in the north and who have got brilliant rays should be con. sidered as victorious|In planetary war, those that are posited in the north and who have got brilliant rays','2'),
'b_bhava_dig':('bphs_pg0285_c01', r'Deduct the 7th house \(longitude of descen- dant\) from the bhava if the bhava happens to be in Virgo, Gemini, Libra, Aquarius','26-29'),
'b_bhava_asp':('bphs_pg0285_c01', r'The product after division should be increased by a fourth if the bhava in qucstion has a benefic aspect|should be increased by a fourth if the bhava in qucstion has a benefic aspect','26-29'),
'b_bhava_lord':('bphs_pg0285_c01', r'suleradd the strength acquired by the lord of that Bhava','26-29'),
'b_ishta':('bphs_pg0289_c01', r'Reduce I from each of Cheshta Rasmi and Uchcha Rasmi. Then multiply the products by l0 and add together. Half of the sum will represent the Ishta phala','6'),
'b_kashta':('bphs_pg0289_c01', r"Reduce Ishta Phala from 60 to obtain the planet's Kashta Phala",'6'),
'b_ch28':('bphs_pg0288_c01', r'Chapter 28 Ishta And Kashta Balas',None),
'b_drishti_q':('bphs_pg0254_c01', r'gradually in slabs of quarters','2-5'),
'b_drishti_virupa':('bphs_pg0257_c01', r'Speculum of Aspetual Vdues',None),
'b_drishti_ch26':('bphs_pg0253_c01', r'Chapter 26 Evaluation of Planetary Aspects',None),
'b_vims':('bphs_pg0094_c01', r'The full strength, for each of the divisions respectively are 6,2, 4,5,2 and l','17-19'),
'b_vims2':('bphs_pg0095_c01', r'Vimsopaka score goes thus : Hora 1 Trimsamsa l, decanate l, Shodasamsa 2, Navamsa 3, Rasi 3l','21-25'),
'b_vims3':('bphs_pg0095_c01', r'declines to l8 in .xtreme friend.s V;;"t, to l5 \[ frien<lly Vargas|The Vimsopaka strength remains as 20','21-25'),
'b_vims_note':('bphs_pg0094_c01', r'Vimsopaka strength is the 20 point strength','17-19 (Notes)'),
'b_sbala_ch27':('bphs_pg0262_c01', r'Chapter 27 .Evaluation Of Strengths|Evaluation Of Strengths','1'),
'b_shadbala6':('bphs_pg0263_c01', r'These strengths are called Shadbala','1 (Notes)'),
'b_asht_incl':('bphs_pg0859_c01', r'After preparing the. Ashtakavarga of all the planets including tte ascerida,U','1-2'),
'b_asht_illus':('bphs_pg0891_c01', r"5 in the Ascen- dant's Ashtakavarga",'Ch.72 (illustration)'),
'b_asht_total':('bphs_pg0891_c01', r'The total of rekhas in the Ascendant is 30 in the Samudaya or Aggregratiorrai','Ch.72 (illustration)'),
'b_asht_thr':('bphs_pg0890_c01', r'more than 30 rekhas advance the effects of a house, between 25 and 30 rekhas produce medium effects','Ch.72 sl.6-8'),
'b_asht_thr2':('bphs_pg0890_c01', r'the effects of tle house which contains less than 25 rekhas gets damaged','Ch.72 sl.6-8'),
'b_trik_def':('bphs_pg0859_c01', r'Trikona is made of three rasis equidistant from each other','1-2'),
'b_trik_ch':('bphs_pg0859_c01', r'Chapter 67 Trikona Shbdhana \(rectification\) irthe \$shtakavarga Scheme',None),
'b_ekad':('bphs_pg0867_c01', r'Ekadhipatya Shodhana is done after writing the numbers for rasis arrived at by trikona Shodhana','1-5'),
'b_ekad2':('bphs_pg0867_c01', r'Ekadhipatya Shodhana is done if both the two rasis owned by a planet have gained a number after trikona Shodhana','1-5'),
'b_pinda':('bphs_pg0880_c01', r'Rasi Pinda 80, Grah Pinda 33, Yoga Pinda ll3',None),
'b_pinda2':('bphs_pg0874_c01', r'multiply the number of rekhas with the Yoga Pinda \(Rasi Pinda plus Graha Pinda\)','Ch.70'),
'b_asht_longev':('bphs_pg0885_c01', r'There can be possibility of death or death-like suffering in the 46th year',None),
'b_vim_total':('bphs_pg0499_c01', r'the natural life span of a human being is generally taken as 120 years',  '12-14 (Notes)'),
}

E.update({
'jp_mt_moon':('jataka_parijata_pg0045_c01', r'exaltation portion of the Moon, and the rest, her Moolathrikona','26-28'),
'bphs_rahu_debil':('bphs_pg0574_c02', r'ign of debilitation \(Scorpio\)','40-43'),
'bphs_bhava_ind':('bphs_pg0102_c01', r'Bandhu Putra Ari Yuvati Randhra Dharma Karma Laabha','37-38 (Notes)'),
'pd_house_kendra':('phaladeepika_pg0046_c01', r'the 10th, the 7th and the 4th houses are known by the terms Kendra','17'),
'pd_karakas':('phaladeepika_pg0196_c01', r'The Karakas of the Bhavas beginning with the Lagna or the rising sign','17'),
'uk_rahu_asp':('uttara_kalamrita_pg0041_c01', r'Rahu aspects 5, 7, 9 and 12 fully, 2 and 10 by half',None),
'uk_asp_jup':('uttara_kalamrita_pg0040_c02', r'aspect on the fifth and ninth houses from himself',None),
'bphs_16b':('bphs_pg0067_c01', r'Chaturvimsamsa, Sapthavimsamsa, Trimsamsa, Khavcdamsa, Akshavedamsa and Shashtiamsa','2-4'),
'bphs_vuse1':('bphs_pg0091_c01', r"fortunes from Chaturthamsa, sons and grandsons from saptha' msa, spouse from Navamsa",'1-8 (Ch.7)'),
'bphs_vuse1b':('bphs_pg0091_c01', r'power \(and position\) from Dasamsa, parents from Dvadasamsa','1-8 (Ch.7)'),
'bphs_vuse2':('bphs_pg0091_c01', r"learn' ing from Chathur Vimsamsa. strength and weakness from Bhamsa,evil, effects from Trimsamsa",'1-8 (Ch.7)'),
'bphs_upa_malefic':('bphs_pg0042_c01', r'planets devoid of splendour which are malefics by nature and cause affiiction','61-64'),
'bphs_upaketu':('bphs_pg0042_c01', r'Add 16 degrees 40 minutes to Chapa which will give Ketu','61-64'),
'b_sapta':('bphs_pg0264_c01', r'in its Moolatrikona Rasi, it gets 45 Virupas, in own Rasi 30 Virupas','2-4'),
'b_sapta2':('bphs_pg0264_c01', r"cxtreme. friend's Rasi 20 Virupas, friend's Rasi 15 Virupas, neutral's Rasi l0 Virupas",'2-4'),
'b_sapta3':('bphs_pg0264_c01', r"enemy's Rasi 4 Virr:pas and in extreme enemy's Rasi 2 Virupas",'2-4'),
'b_ojha':('bphs_pg0264_c02', r'Venus and the Moon in cven Rasis and others in odd Rasis','4'),
'b_ojha15':('bphs_pg0265_c01', r'get 15 Virupas if they are placed in odd Rasis','4 (Notes)'),
'b_kendradi':('bphs_pg0265_c01', r'A planet in an angle gets full ;trength while one in succedent house gets balf','5'),
'b_drek':('bphs_pg0265_c01', r'female and .hernaphro- dite planets respectively g9t a quarter Ruln','6'),
'b_nath':('bphs_pg0267_c01', r'Moon, Mars and Saturn cet this strength in the night','9-10 (Notes)'),
'b_paksha':('bphs_pg0268_c01', r'Paksha bala of benefic should be deducted from 60 which will go to each malefic','10-11'),
'b_tribhaga':('bphs_pg0268_c01', r'One Rupa is obtained by Mercury \(if birth is\) in the first one third','12'),
'b_tribhaga2':('bphs_pg0268_c02', r'second one third part of the day and by Saturn in the last third part','12'),
'b_vmdh':('bphs_pg0269_c01', r'45 and 60 Virupas are in order given to Varsha lord, Maasa lord Dina lord','13'),
'b_naisarg':('bphs_pg0275_c01', r'Divide one Rupa \(or 60 Virupas\) by 7 and multiply','14'),
'b_ayana_dir':('bphs_pg0276_c01', r'Sun, Mars, Jupiter or Venus have Northern Kranti, take plus','15-17 (Notes)'),
'b_cheshta_sm':('bphs_pg0283_c01', r"Sun's Cheshta Bala \(or motional strength\) will correspond to his Ayana Bela",'18'),
'b_cheshta_8':('bphs_pg0284_c01', r'strengths allotted due to such 8 motions are : 60, 30, 15, 30, 15','22-23'),
'b_drig':('bphs_pg0283_c01', r'Reduce one fourth of the Drishti Pinda if a planet has malefic aspects on it','19'),
'pd_war':('phaladeepika_pg0071_c01', r'those that are posited in the north and who have got brilliant rays','2'),
'b_bhava_dig':('bphs_pg0285_c01', r'Deduct the 7th house \(longitude of descen- dant\) from the bhava','26-29'),
'b_bhava_asp':('bphs_pg0285_c01', r'increased by a fourth if the bhava in qucstion has a benefic aspect','26-29'),
'b_ishta':('bphs_pg0289_c01', r'Half of the sum will represent the Ishta phala \(benefic tendency\)','6'),
'b_ishta_a':('bphs_pg0289_c01', r'Reduce I from each of Cheshta Rasmi and Uchcha Rasmi','6'),
'b_ch28':('bphs_pg0288_c01', r'C.bepter 28 Ishta And Kashta Balas',None),
'b_drishti_virupa':('bphs_pg0257_c01', r'Spccdum of Aspetual Vdues \(Conrputerlzed\)',None),
'b_vims2':('bphs_pg0095_c01', r'Hora 1 Trimsamsa l, decanate l, Shodasamsa 2, Navamsa 3, Rasi 3l','21-25'),
'b_asht_thr':('bphs_pg0890_c01', r'more than 30 rekhas advance the effects of a house','Ch.72 sl.6-8'),
'b_ekad2':('bphs_pg0867_c01', r'done if both the two rasis owned by a planet have gained a number','1-5'),
'b_pinda2':('bphs_pg0874_c01', r'Yoga Pinda \(Rasi Pinda plus Graha Pinda\)','Ch.70'),
})

E['b_kala_list']=('bphs_pg0267_c01', r'Kaala Bata \(or temporal strength\) comprises of the following sub divisions','9-10 (Notes)')


_SL={'bphs_gemini_airy':'9-9½','bphs_gemini_biped':'9-9½','bphs_aqu_airy':'21-21½','bphs_aqu_biped':'21-21½',
'b_asht_thr':'6-6½ (OCR "6-6*")','b_asht_thr2':'6-6½ (OCR "6-6*")','b_pinda2':None,'b_cheshta_8':'21-23',
'b_dig':'7-7½','b_dig_note':'7-7½ (Notes)','b_dig_note2':'7-7½ (Notes)','b_nath':'8-9 (Notes)','b_nath2':'8-9','b_kala_list':'8-9 (Notes)',
'b_uchcha':'1-1½','b_uchcha2':'1-1½','b_uchcha3':'1-1½ (Notes)','b_ojha':'4½','b_ojha15':'4½ (Notes)','b_asht_longev':None}
for _k,_v in _SL.items():
    _c,_r,_s=E[_k]; E[_k]=(_c,_r,_v)

_SL2={'bphs_maraka':'2-5 (Notes)','bphs_gulika_beg':None,'b_asht_illus':None,'b_asht_total':None,'uk_asp':None,'bphs_nodes_180':None,
'bphs_vuse0':'1-8','bphs_vuse1':'1-8','bphs_vuse1b':'1-8','bphs_vuse2':'1-8','bphs_vuse3':'1-8','bphs_vuse_hora':'1-8','bphs_vuse_conv':'1-8','bphs_vnote':'1-8 (Notes)',
'bphs_nodes_exalt_views':'49-50 (Notes)'}
for _k,_v in _SL2.items():
    _c,_r,_s=E[_k]; E[_k]=(_c,_r,_v)

def get(key):
    cid,rx,sl=E[key]
    txt=CH.get(cid)
    if txt is None: return None
    m=re.search(rx,txt)
    return (cid,m.group(0) if m else None,sl)
if __name__=='__main__':
    bad=0
    for k in E:
        r=get(k)
        if r is None or r[1] is None:
            bad+=1; print('MISS',k,E[k][0], (CH.get(E[k][0]) or '')[:0])
        else:
            n=len(r[1].split())
            if n>15: print('LONG',k,n)
    print('missing',bad,'of',len(E))
