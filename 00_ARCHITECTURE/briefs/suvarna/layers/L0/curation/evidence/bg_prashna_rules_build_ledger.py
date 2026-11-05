# -*- coding: utf-8 -*-
# Generates ledger.json for asset bg_prashna_rules (read-only research output; no DB access here).
import json

ASSET = "bg_prashna_rules"
TN_ED = "Shrikrishnadas Press ed. with Hindi bhasha-tika; Devanagari OCR, AWAITING_NATIVE_DECISION"
TN_SHORT = "Tajika Nilakanthi (Mahidhara Hindi bhasha-tika)"

rows = []


def tn(page, k=1, sl=None, q=""):
    return {"text_id": "tajaka_neelakanthi",
            "chunk_id": "tajaka_neelakanthi_pg%04d_c%02d" % (page, k),
            "page": "PG%d" % page, "sloka_printed": sl, "quote": q}


def ct(text_id, page, k, sl, q):
    return {"text_id": text_id,
            "chunk_id": "%s_pg%04d_c%02d" % (text_id, page, k),
            "page": "PG%d" % page, "sloka_printed": sl, "quote": q}


def add(table, key, claim, cur, state, sup, corpus, inf, prop, act, q, notes):
    rows.append({
        "asset": ASSET, "table": table, "row_key": key, "row_count": 1,
        "claim": claim, "current_citation": cur, "state": state,
        "support_class": sup, "corpus": corpus, "inference_step": inf,
        "proposed_citation": prop, "proposed_action": act,
        "acharya_question": q, "notes": notes})


def tn_cite(page, sl, what):
    return ("%s, Ṣoḍaśa-yoga-adhyāya (printed 'अथ षोडशयोगाध्यायः'), Sloka %s as printed — "
            "tajaka_neelakanthi:PG%d:C1 (%s) [%s]" % (TN_SHORT, sl, page, TN_ED, what))


# --------------------------------------------------------------------------------------------
# 1. bg_prashna_lagna_methods (5)
# --------------------------------------------------------------------------------------------
T = "bg_prashna_lagna_methods"
add(T, {"id": 1, "method_id": "tajik_moment_lagna"},
    "Prashna Lagna = ascendant of the exact moment and place of the question; primary Tajika horary chart.",
    "Tājika Nīlakaṇṭhī, Ch. 1 (Prashna Lagna Nirūpaṇa); Prashna Mārga Ch. 1",
    "sourced_fact", "FACT",
    [ct("hora_sara", 308, 1, "5", "work out the ascendant prevailing for the time of query"),
     ct("hora_sara", 308, 1, "5", "(which is called Arudha Lagna or Prasna Lagna)"),
     ct("brihat_jataka", 525, 1, "1", "make out the chart of the querist from the rising sign at the time of query")],
    None,
    "Hora Sara, Ch. 27 (printed 'CHAPTER 27'), Sloka 5 as printed — hora_sara:PG308:C1 (Santhanam trans.); "
    "Brihat Jataka, Ch. XXVI, Sloka 1 as printed — brihat_jataka:PG525:C1 (Sastri 2nd ed.)",
    "recite", None,
    "Both held passages state the rule inside lost-horoscopy (Nashta Jataka) text, but they do define 'ascendant at the "
    "time of query' as the Prasna Lagna, which is the whole claim. 'exact moment and location' and 'primary Tajika "
    "horary chart' are not stated in these chunks. Existing 'Ch. 1' locator is chapter-grain and unresolvable "
    "(tajaka_neelakanthi is held but Hindi/Devanagari OCR pending native decision; Prashna Marga not held). "
    "Tajika text itself (Prashna-tantra, tajaka_neelakanthi:PG223) opens its prashna chapter by taking the question "
    "chart's lagna-lord and Moon strength - consistent, not a definition.")

add(T, {"id": 2, "method_id": "kp_249"},
    "Querent picks 1-249; the number maps to a KP sub-lord and the cusp it identifies becomes the Prashna Lagna.",
    "Krishnamurti Paddhati — Prashna system; K.S. Krishnamurti, 'Krishnamurti Padhdhati' Vol. 2, Ch. on Prashna (Horary)",
    "text_not_held", "NONE", [], None, None, "none", None,
    "Krishnamurti Paddhati is not held. Probe of all 15 texts for krishnamurti / sub-lord / sublord / 249 returned no "
    "relevant chunk (only unrelated 'breath'/'249' tokens).")

add(T, {"id": 3, "method_id": "aarudha_based"},
    "Prashna Lagna from the querent's seat/facing direction: East=Aries/Leo/Sag, North=Cancer/Scorpio/Pisces, West=Libra/Aquarius/Gemini, South=Capricorn/Taurus/Virgo.",
    "Prashna Mārga, Ch. 1 (Āruḍha Prashna Lagna Vichāra)",
    "text_not_held", "NONE",
    [ct("hora_sara", 16, 1, None, "East, South, West and North are Aries, Taurus, Gemini and Cancer respectively"),
     ct("hora_sara", 308, 1, "5", "(which is called Arudha Lagna or Prasna Lagna)"),
     ct("hora_sara", 63, 1, None, "(Arudha Lagna is Prasna Lagna in the case of horary chart.)")],
    "Context only, NOT support for the stored derivation: Hora Sara Ch.2 gives direction lordship Aries-East, Taurus-South, "
    "Gemini-West, Cancer-North 'with their trines repeating in the same order' - this is the same sign/direction grouping "
    "the row uses, but no held chunk derives the Prashna Lagna from the querent's seat/facing direction.",
    None, "acharya",
    "In Prashna Mārga's Āruḍha method, is the Prashna Lagna the sign fixed by the direction the querent faces/sits "
    "(East = Aries/Leo/Sagittarius ... via the trine-repeating direction lordship printed in Hora Sara Ch.2), or is "
    "Āruḍha Lagna simply the ascendant at the time of query as Hora Sara Ch.27 Sl.5 and Ch.5 state?",
    "Held Hora Sara uses 'Arudha Lagna' as a synonym of the ascendant at query time (PG308, PG63), a different sense "
    "from the row's seat/direction derivation. Row value is unchanged; flagged because the term collides.")

add(T, {"id": 4, "method_id": "chandra_lagna"},
    "Querent's natal Moon sign used as the Prashna Lagna; houses counted from natal Moon.",
    "Bṛhat Prashna tradition; Prashna Mārga Ch. 2 (Chandra Bala adhyāya)",
    "text_not_held", "NONE",
    [tn(210, 1, None, "पहिला भ्रश्न लभसे, दसरा चनदरस्थानसे, तीसरा सूर्थस्थानसे")],
    "Context only: Tajika Nilakanthi Prashna-tantra (PG209-210) takes the FIRST of several simultaneous questions from the "
    "lagna and the SECOND from the Moon's place at question time - not the natal Moon sign as lagna.",
    None, "mark_unsourced", None,
    "Neither Brihat Prashna nor Prashna Marga is held. The closest held statement (Moon's place as base for the second "
    "question, tajaka_neelakanthi PG209-210) is a different rule and is not offered as support. 'tradition=parashari' "
    "on this row is a platform label.")

add(T, {"id": 5, "method_id": "swara_based"},
    "Prashna Lagna from the active nostril at asking (right = odd signs, left = even signs); sign refined by time and Tithi.",
    "Swara Śāstra (Śiva Swarodaya); Prashna Mārga Ch. 4 (Swara adhyāya)",
    "text_not_held", "NONE", [], None, None, "none", None,
    "Swara Shastra / Shiva Swarodaya and Prashna Marga are not held. Probe for nostril / swara / svara / breath over all "
    "texts returned only anatomical (Brihat Jataka/Samhita/BPHS body-part) hits, none about Prashna Lagna.")

# --------------------------------------------------------------------------------------------
# 2. bg_prashna_tajik_yogas (16)
# --------------------------------------------------------------------------------------------
T = "bg_prashna_tajik_yogas"
CH_NOTE = (" Existing locator 'Ch. 4 (<X> adhyaya)' does not match the held edition: all sixteen yogas sit in ONE "
           "'षोडशयोगाध्यायः' (the chapter after 'ग्रहचारदृष्टिविचार द्वितीयोऽध्यायः', Samjna-tantra, PG49-83), and "
           "the held text is Devanagari OCR awaiting native decision, with corpus pages 74, 76 and 79 missing.")

yoga_list_chunk = tn(49, 1, "1-2", "अथ पोडशयोगाध्यायः । प्रागिक्रवालोऽपरदंदुवारस्तथेत्थशालोऽपरदशराफः")

# 1 ithasala
add(T, {"id": 1, "yoga_id": "ithasala"},
    "Applying aspect between lagna lord and lord of the matter's house; faster planet behind slower; within mutual orbs (half the sum of orbs); strongest positive.",
    "Tājika Nīlakaṇṭhī, Ch. 4 (Ithashāla adhyāya); Prashna Mārga Ch. 6",
    "sourced_inference", "INFERENCE",
    [tn(50, 1, "4", "शीघ्र अपना तज अग्रगत भदग्रहको दे दता है इसको मुथशिखयोग कहते हं"),
     tn(52, 1, None, "ठग्रेश ओर कार्येशका इत्थशाट हानेसे उस कायंकी सिद्ध होती हे"),
     ct("uttara_kalamrita", 173, 1, None, "The lord of the lagna and the lord of the action must have an applying aspect")],
    "Core FACT: Tajika text names the yoga (मुथशिल = इत्थशाल), defines it as the faster planet behind the slower one with mutual "
    "aspect inside the deeptamsha, and says it accomplishes the matter when formed by lagna lord and karyesh. The 'half the sum "
    "of the two orbs' formula is NOT printed in the readable OCR (text speaks of both planets being within their dipta-amsha; "
    "PG49 prints per-planet dipta-amsha values - Moon 12, Mars 8, Mercury 7, Venus 7 legible, Sun/Jupiter/Saturn digits garbled); Uttara Kalamrita Ch.VII "
    "prints a flat 12-degree orb instead. Orb rule left unverified." + CH_NOTE,
    tn_cite(50, "4", "core definition; orb rule unverified"), "acharya",
    "Tājika Nīlakaṇṭhī (Ṣoḍaśa-yoga ch.) makes Ithaśāla a faster planet behind a slower one, both inside their dīptāṃśa; Uttara "
    "Kalāmṛta Ch.VII uses a flat 12-degree orb. Which orb convention should the platform state for the formation rule: per-planet "
    "dīptāṃśa with a pairwise (half-sum) moiety, or a flat figure?",
    "Near-contradiction on the orb only (UK 12 deg vs row's half-sum); not counted as contradicted because the half-sum is a "
    "standard moiety convention that the readable TN passages neither state nor deny.")

# 2 eesarpha
add(T, {"id": 2, "yoga_id": "eesarpha"},
    "Separating aspect: faster planet has passed the exact aspect and moves away; matter past/declined.",
    "Tājika Nīlakaṇṭhī, Ch. 4 (Ithashāla adhyāya, Eesarpha section)",
    "sourced_fact", "FACT",
    [tn(55, 1, "10", "एके अंश भी आगे बढ जाय ता इसराफ योग होता है"),
     tn(54, 1, None, "इण्व०-शीघ्रो यदा मंदगतेरथेकमप्यंशमभ्येति तदेशराफः"),
     ct("uttara_kalamrita", 173, 1, None, "If there is a separating aspect, the good results may not follow")],
    None,
    tn_cite(55, "10", "Isarpha: faster planet one degree beyond the slower"),
    "recite", None,
    "Text: if the faster planet advances even one degree beyond the slower it is Isarpha (also called Musharif); it destroys/reverses "
    "the matter that Ithasala would have accomplished; worse if both are malefic. Row's 'matter decided/past/declined' is a "
    "paraphrase of 'कार्य का नाश / विपरीत' - consistent." + CH_NOTE,)

# 3 nakta
add(T, {"id": 3, "yoga_id": "nakta"},
    "No direct applying aspect between the significators; a third planet takes light from one and gives it to the other; matter via intermediary.",
    "Tājika Nīlakaṇṭhī, Ch. 4 (Nakta adhyāya)",
    "sourced_fact", "FACT",
    [tn(55, 1, "11", "अपने पीछेवारे स्वल्पांश ब्रहका तज ठकर अगिवाठे ब्ृहरदेशका देदेताहै"),
     tn(55, 1, "11", "यह योग अन्यद्रारा कायंसिद्धि करता है"),
     ct("uttara_kalamrita", 173, 1, None, "result comes easily. but through a middleman")],
    None,
    tn_cite(55, "11", "Nakta"), "recite", None,
    "Text: lagna lord and karyesh have no mutual aspect, but a FASTER planet between/behind them aspects both, takes the light of "
    "the lesser-degree planet behind and gives it to the slower ahead; the work is accomplished through another person. Matches the "
    "row's configuration. Row's etymology ('nakta = one who goes between') is not in the chunk (not part of the claim)." + CH_NOTE)

# 4 yamaya
add(T, {"id": 4, "yoga_id": "yamaya"},
    "Both significators in mutual exchange of signs (parivartana); matter occurs with mutual dependency/compromise.",
    "Tājika Nīlakaṇṭhī, Ch. 4 (Yamaya adhyāya)",
    "contradicted", "CONTRADICTS",
    [tn(56, 1, "14", "ठग्रेश ओर कार्येश किसी भावों हौ उनकी परस्पर दृटि न हो किंतु दानासं मदगतिको ही रह"),
     tn(57, 1, "14", "इस योगका नाम यमा है. कार्थकी सिद्धि दुसरेके द्रारा करता है")],
    None,
    None, "acharya",
    "Tājika Nīlakaṇṭhī Sl.14 defines Yamayā as: lagna lord and karyesh have no mutual aspect, but a SLOWER planet aspects both, takes "
    "the faster one's light and hands it to the slower - success through another. The row defines Yamaya as parivartana "
    "(mutual sign exchange). Is the exchange definition from another school/text, and which should the platform keep?",
    "HELD TEXT: Yamaya is the slow-planet light-transfer counterpart of Nakta (fast-planet transfer). Row: parivartana. "
    "Different definition; row value NOT changed." + CH_NOTE)

# 5 manaau
add(T, {"id": 5, "yoga_id": "manaau"},
    "The two significators in square aspect (90 deg): tense, uncertain, obstacles.",
    "Tājika Nīlakaṇṭhī, Ch. 4",
    "contradicted", "CONTRADICTS",
    [tn(58, 1, "17-19", "इसको मणड योग कहत है इत्थशाकका विरुदफल अथात्‌ कायंनाश"),
     tn(57, 1, "17", "मण योगका क्षण कहते हं, यह नक्तयागके तरह है परन्तु शनि वा"),
     tn(59, 1, "18-19", "मंगकके मणठं कृरनेमे यह कायं नक होगा")],
    None, None, "acharya",
    "Tājika Nīlakaṇṭhī Sl.17-19 defines Maṇaū (मणऊ) as Mars or Saturn, placed near the faster significator, taking its light and not "
    "passing it to the slower one, so the Ithaśāla result is reversed (matter destroyed). The row defines Manaau as a 90-degree "
    "aspect between the significators. Should the platform's definition follow the printed Mars/Saturn light-stealing rule?",
    "HELD TEXT contradicts the row's square-aspect definition (both are negative in polarity). Row value NOT changed." + CH_NOTE)

# 6 kambula
add(T, {"id": 6, "yoga_id": "kambula"},
    "Moon applies to either the querent significator or the quesited significator within orb; timely, favorable.",
    "Tājika Nīlakaṇṭhī, Ch. 4 (Kambūla adhyāya)",
    "sourced_inference", "INFERENCE",
    [tn(60, 1, "21-22", "चन्द्रमा श वा कयेश वा दोनेकि साथ इत्यशाठी रहे"),
     tn(60, 1, "21-22", "ठत्रेश कायेशको पूर्वोक्त प्रकारसे इत्थशाल हो"),
     tn(61, 1, None, "कंबूड पारशीय पद कदल पर्याय हे")],
    "Core FACT: Kambula = Moon in Ithasala with the lagna lord, the karyesh, or both. INFERENCE gap: the printed rule ALSO requires "
    "that lagna lord and karyesh are themselves in Ithasala ('लग्नेश कार्येश का इत्थशाल हो और चन्द्रमा ... इत्थशाली रहे'); the row "
    "omits that precondition and does not carry the text's 32/16 grades of Kambula (Moon's dignity)." + CH_NOTE,
    tn_cite(60, "22", "Kambula: precondition and grading not in the row"), "acharya",
    "Tājika Nīlakaṇṭhī Sl.21-22: Kambūla needs the lagna lord and karyesh already in Ithaśāla AND the Moon in Ithaśāla with one or both "
    "(with sixteen Moon-dignity grades, uttamottama ... adhamādhama). Should the platform's formation rule add the precondition "
    "(lagna lord + karyesh already Ithaśāla) or is the looser 'Moon applies to either' deliberate?",
    "Row is a looser statement of the printed rule; not contradicted.")

# 7 gairi kambula
add(T, {"id": 7, "yoga_id": "gairi_kambula"},
    "Moon has already separated from the significator; inverse of Kambula; opportunity already spent.",
    "Tājika Nīlakaṇṭhī, Ch. 4 (Kambūla adhyāya, Gairi section)",
    "contradicted", "CONTRADICTS",
    [tn(72, 1, "40-41", "चन्द्रमा शून्य मागं हो ओर रग्नेश काययेशएक वा दोनहूं एसेही शन्या-"),
     tn(72, 1, "39", "जो ग्रह स्वगृह वा स्योच वा स्वरेष्काण स्वनवांशमे कईं भी शुभा-धिकारी नही है"),
     tn(73, 1, "40-41", "यहं गैरिकम्बढ ... अशभ फल देतौ है")],
    None, None, "acharya",
    "Tājika Nīlakaṇṭhī Sl.38-44 defines Gairi-Kambūla through a 'śūnya-mārga/śūnyādhvaga' Moon (no own-sign, exaltation, decanate, "
    "navāṃśa or other dignity and no aspect from any planet) that is not in Ithaśāla with the significators: in one form the Moon "
    "is about to enter a sign where the dignified ruler/exaltee sits and at once makes Ithaśāla with it (fruit like Kambūla); in "
    "the other the Moon makes Ithaśāla with a void planet in its own sign (inauspicious). The row defines it as 'Moon already "
    "separated from the significator, inverse of Kambula'. Which definition is wanted?",
    "HELD TEXT states a different (void-of-dignity/void-of-aspect Moon) definition with two forms of mixed polarity; the row's "
    "'separated Moon' definition is not printed. Row NOT changed." + CH_NOTE)

# 8 dutthottha
add(T, {"id": 8, "yoga_id": "dutthottha"},
    "Significator in the 8th from its own sign: weakness, obstruction, hidden impediment.",
    "Tājika Nīlakaṇṭhī, Ch. 4 (Duttoththa adhyāya)",
    "contradicted", "CONTRADICTS",
    [tn(77, 1, "49", "किसी ओरकी सहायतासे कायं सिद्ध होगा"),
     tn(77, 1, "49", "इस योगका नाम दृत्थोत्थदिवीर ... पारसीय शब्द हे")],
    None, None, "acharya",
    "In Tājika Nīlakaṇṭhī Sl.48-49 the yoga (Duttottha-Davīra/Dutthottha-divīra, ONE yoga) is read in the surviving tail as: weak "
    "(e.g. debilitated) lagna lord/karyesh, with a strong planet (fast-moving, in dignity) helping, still accomplishing the "
    "matter through someone else's help. The row defines Dutthottha as the significator in the 8th from its own sign and gives "
    "obstruction. Which is the intended yoga and outcome?",
    "PARTIAL EVIDENCE: the first half of the definition (Sl.48) falls on corpus page 76 which is MISSING; the readable tail (PG77) "
    "states the outcome (success through help) and the name. The row's 8th-from-own-sign definition appears nowhere. Outcome "
    "polarity is opposite (success vs obstruction), hence contradicted; row NOT changed." + CH_NOTE)

# 9 rudda
add(T, {"id": 9, "yoga_id": "rudda"},
    "A malefic interposed between the significators blocks the applying aspect; matter blocked/prevented.",
    "Tājika Nīlakaṇṭhī, Ch. 4 (Rudda adhyāya = prevention)",
    "unsourced_marked", "NONE",
    [tn(75, 1, "47", "प्रथम वृह कायं सिद्ध होकर अन्तमं नष्ट हो जायगा")],
    "Context only: the readable Sl.47 variant of Radda (रद्द) is an Ithasala between a planet in a kendra and one in an apoklima - "
    "result first accomplished then destroyed (or the reverse) - not a malefic interposition. The primary definition falls on "
    "missing corpus page 74, so no contradiction verdict is recorded.",
    None, "acharya",
    "Tājika Nīlakaṇṭhī's Raddā (Sl.46-48) is partly preserved: the readable variant makes it an Ithaśāla between a kendra planet and an "
    "apoklima planet, fulfilment followed by destruction (or the reverse). The row says 'malefic interposed between the "
    "significators, blocking'. Which does the acharya want, and from what source?",
    "Adverse-but-incomplete evidence (page 74/76 absent). Row value kept; name 'Rudda' = Radda confirmed in the sixteen-name list (PG49-50)." + CH_NOTE)

# 10 khallasara
add(T, {"id": 10, "yoga_id": "khallasara"},
    "Faster significator transfers light to an intermediate planet that completes the link to the slower significator (A->B->C); delayed.",
    "Tājika Nīlakaṇṭhī, Ch. 4 (Khallāsara adhyāya)",
    "unsourced_marked", "NONE",
    [yoga_list_chunk],
    "Only the NAME (खल्लासर, 10th of the sixteen) is printed in a readable chunk (PG49-50); its definition (about Sl.45-46) falls on "
    "corpus page 74, which is missing.",
    None, "mark_unsourced", None,
    "Definition unverifiable in the corpus (page gap). Note the row's configuration is near-identical to the row for Nakta "
    "(third planet transfers light) - internal redundancy, see summary." + CH_NOTE)

# 11 duhphali kuttha
add(T, {"id": 11, "yoga_id": "duhphali_kuttha"},
    "The two significators in opposition (180 deg): open conflict, matter pulled two ways.",
    "Tājika Nīlakaṇṭhī, Ch. 4 (Duḥphalī Kuṭṭha adhyāya)",
    "unsourced_marked", "NONE",
    [yoga_list_chunk],
    "Only the NAME (दुफालिकुत्थ, 12th of the sixteen) is printed in a readable chunk; the definition (about Sl.48) is on missing corpus "
    "page 76. No held chunk states an opposition-based definition.",
    None, "mark_unsourced", None,
    "Definition unverifiable (page gap)." + CH_NOTE)

# 12 ikbal
add(T, {"id": 12, "yoga_id": "ikbal"},
    "A planet that has turned direct after retrograde applies to the significator; renewed momentum (variant of Ithasala).",
    "Tājika Nīlakaṇṭhī, Ch. 4 (Ikbāl adhyāya — application after station)",
    "contradicted", "CONTRADICTS",
    [tn(50, 1, "3", "इस योगका नाम इक्वाट हे, इसका फट राज्य सुख है"),
     tn(49, 1, "1", "प्रागिक्रवालोऽपरदंदुवारस्तथेत्थशालोऽपरदशराफः")],
    None, None, "acharya",
    "Tājika Nīlakaṇṭhī Sl.3 defines Ikkavāla/Ikbāl as ALL planets in kendras (1,4,7,10) and paṇaphara (2,5,8,11) with none in an "
    "apoklima (3,6,9,12), giving royal comfort; its counterpart Induvāra is all planets in apoklimas (inauspicious). The row "
    "defines Ikbal as a recently direct planet applying to a significator. Should the row be restated to the printed definition?",
    "HELD TEXT states a different definition (house-distribution of all planets). Row NOT changed." + CH_NOTE)

# 13 kuttha
add(T, {"id": 13, "yoga_id": "kuttha"},
    "A malefic between the significators makes an exact applying aspect to the slower one first and severs the connection.",
    "Tājika Nīlakaṇṭhī, Ch. 4 (Kuṭṭha adhyāya — cutting/severing)",
    "contradicted", "CONTRADICTS",
    [tn(78, 1, "51", "पन्द्रहवां कुत्थयोगका लक्षण, कुत्थ पारसीय शब्दसे बी रह लिया जाता है"),
     tn(81, 1, "54", "कृत्थ शब्दसे बटी रह छिया जाता है")],
    None, None, "acharya",
    "Tājika Nīlakaṇṭhī Sl.51-54 defines Kuttha as the Ithaśāla-making planet being strong ('कुत्थ' = a strong planet: lagna-seeing, "
    "kendra, own sign/exaltation, mid-motion etc.) - a favourable condition. The row defines Kuttha as a malefic that cuts the "
    "connection. Which is intended?",
    "HELD TEXT: Kuttha = strength of the Ithasala planet (the opposite polarity to the row's 'severing'). Row NOT changed." + CH_NOTE)

# 14 dutthadhuta
add(T, {"id": 14, "yoga_id": "dutthadhuta"},
    "A malefic in exact applying trine/square to one significator; malefic messenger, matter arrives corrupted.",
    "Tājika Nīlakaṇṭhī, Ch. 4 (Dutthadhūta adhyāya — malefic aspect messenger)",
    "unsourced_marked", "NONE",
    [yoga_list_chunk],
    "Absence only: the sixteen names printed in Sl.1-2 are Ikkavāla, Induvāra, Ithaśāla, Īsarāpha, Nakta, Yamayā, Maṇaū, Kambūla, "
    "Gairi-kambūla, Khallāsara, Raddā, Duḥphāli-kuttha, Duttottha-divīra, Tambīra, Kuttha, Duruppha; 'Dutthadhuta' is not among them "
    "and 'Induvāra' is. Recorded as adverse evidence (absence = inference), not as a contradiction.",
    None, "acharya",
    "The held Tājika Nīlakaṇṭhī lists sixteen yogas that include Induvāra and a single 'Duttottha-divīra' but no 'Dutthadhuta'. "
    "Is 'Dutthadhuta' an attested yoga in some other Tajika text, or should the platform's sixteen be reconciled with the printed list?",
    "Platform row set differs from the printed sixteen by membership: row set has Dutthottha + Dutthadhuta + Ikbal(different) and "
    "lacks Induvara; see summary." + CH_NOTE)

# 15 tambira
add(T, {"id": 15, "yoga_id": "tambira"},
    "Venus as a morning star (ahead of the Sun) as significator is especially auspicious.",
    "Tājika Nīlakaṇṭhī, Ch. 4 (Tambira adhyāya — Venus morning star)",
    "contradicted", "CONTRADICTS",
    [tn(77, 1, "50", "तवीरयोगके छक्षण कहते है"),
     tn(77, 1, "50", "तीसरेको तेज देता है यह तवीरयोग हआ. फल इसका कार्यसाधक")],
    None, None, "acharya",
    "Tājika Nīlakaṇṭhī Sl.50 defines Tambīra as: lagna lord and karyesh not in Ithaśāla with each other, but one of them is about to "
    "change sign and will make a future Ithaśāla with a strong planet in the next sign, to which it gives its light - the matter "
    "is accomplished (worked example: Saturn at 29 deg Aquarius with Jupiter at 5 deg Pisces). The row defines it as Venus "
    "morning-star auspiciousness. Which is intended?",
    "HELD TEXT states a different definition (future-sign Ithasala light transfer). No held chunk links Tambira to Venus. Row NOT changed." + CH_NOTE)

# 16 durupha
add(T, {"id": 16, "yoga_id": "durupha"},
    "Lord of the matter retrograde: return to past conditions; may still fructify with delay/reversal.",
    "Tājika Nīlakaṇṭhī, Ch. 4 (Durupha adhyāya — retrograde influence on fructification)",
    "sourced_inference", "INFERENCE",
    [tn(83, 1, "56", "निबंर हा तो इत्थशा- लोक्त फक नही देता; इसका नाम दुरफ योग है"),
     tn(82, 1, "55", "पारशीय डरफ शब्द निबेटवाची हं"),
     tn(82, 1, "55", "शक्तराशेस्थ नीचरशिगत वकग-")],
    "Core FACT: Duruppha/Durupha = the Ithasala-making planet is weak ('निर्बल'); one cause listed is vakra (retrograde) together "
    "with 12th-house, enemy/debilitated sign, combustion etc. INFERENCE: the row narrows the cause to retrograde only and says "
    "the matter 'may still fructify'; the text says a weak Ithasala planet does NOT give the Ithasala fruit." + CH_NOTE,
    tn_cite(83, "56", "Durupha: weakness of the Ithasala planet (retrograde one cause)"), "acharya",
    "Tājika Nīlakaṇṭhī Sl.55-56 makes Duruppha the weakness of the Ithaśāla planet (twelfth place, enemy/fall sign, retrograde, "
    "combust, aspect-less, etc.) and says the Ithaśāla fruit is then not given. The row limits it to 'quesited significator "
    "retrograde' and allows fructification with delay. Which statement should the platform keep?",
    "Partial overlap; outcome strength differs. Not counted as contradicted (retrograde is among the printed causes).")

# --------------------------------------------------------------------------------------------
# 3. bg_prashna_significators (12)
# --------------------------------------------------------------------------------------------
T = "bg_prashna_significators"
BN = ("Tājika Nīlakaṇṭhī, Prashna-tantra, Bhāva-nirṇaya (printed 'अथ भवनिणयः'), Sloka %s as printed — "
      "tajaka_neelakanthi:PG%d:C1 (" + TN_ED + ") [house-assignment only; planetary karakas not stated]")
SIG_INF = ("House-level skeleton is FACT in the held Tajika text (Bhava-nirnaya list: bhava -> matters; and the matching "
           "bhava chapter makes lagna lord and/or Moon the querent and the matter's house lord the quesited). Inference gaps: "
           "%s. The row's cited Prashna Marga chapter is not held and is not re-verified.")

add(T, {"id": 1, "question_class": "marriage"},
    "Marriage: lagna lord + Moon (querent) vs 7th lord + Venus + Jupiter; Ithasala 1st-7th lord/Venus the primary positive.",
    "Prashna Mārga, Ch. 14 (Vivāha Prashna)",
    "sourced_inference", "INFERENCE",
    [tn(222, 1, "53-54", "सप्तममं सीसंबेधी, नवमम धमसंबधी,दशममे गरु वा राजसबधी"),
     tn(213, 1, "7", "वणिग्दृत्ति अन्यक सथं विवाद्‌ वा संधि तथा गमन आग-"),
     tn(225, 1, "12", "रग्न सप्तम सप्तम्रश ठ्न दह कवा ठप्रशं सप्तमशका इत्थशाट")],
    SIG_INF % "Venus and Jupiter as natural karakas and the 'Jupiter for female querents' clause are not stated; there is no 'vivāha' prashna chapter in the held Tajika text (7th-house chapter treats spouse/relations; zero 'विवाह' hits in PG207-290), so 7th = spouse/wife is read from the 7th-lord ('जायेश') passages",
    BN % ("7", 213), "acharya",
    "May the marriage row be re-cited to the Tājika Nīlakaṇṭhī Bhāva-nirṇaya (7th = wife/spouse, lagna lord with 7th lord Ithaśāla) "
    "while Venus/Jupiter karakas and the female-querent clause stay marked unsourced, or does the acharya hold a source for them?",
    "Moon as co-querent with the lagna lord is attested in the Tajika bhava chapters for health (PG243), wealth (PG224), children (PG235), career (PG269), journey (PG261).")

add(T, {"id": 2, "question_class": "career"},
    "Career: lagna lord + Moon vs 10th lord + Saturn + Sun; 2nd and 11th lords supporting.",
    "Prashna Mārga, Ch. 19 (Karma Prashna)",
    "sourced_inference", "INFERENCE",
    [tn(214, 1, "10", "राज्य, मद्रा आदि चिह ओर पुण्य, निवासस्थानः, पिता तथा प्रयोजन ... दशमभावसं"),
     tn(269, 1, "1", "राज्यलाम प्रशमं ठेश वो चंद्रमा दशमेशसे मृथशिी हो"),
     tn(214, 1, "11", "हाथी घोडे डोटी आदि सवारी वच्च अन्न सवणे कन्या")],
    SIG_INF % "the held 10th-house chapter is a 'rājya-prāpti' (kingdom/authority) prashna, narrower than 'career/profession'; Saturn and Sun karakas and the 2nd/11th supporting-lord clause are not stated for this class (11th = vehicles/clothes/grain/gold per Sl.11, 2nd = jewels/metals per Sl.2)",
    BN % ("10", 214), "acharya",
    "The Tājika Nīlakaṇṭhī 10th-house chapter treats rājya-prāpti (authority/kingdom) with lagna lord or Moon in Ithaśāla with the 10th "
    "lord; may 'career' be re-cited there with the Saturn/Sun karakas and the 2nd/11th support left explicitly unsourced?",
    "Existing locator 'Ch. 19' unresolvable (Prashna Marga not held).")

add(T, {"id": 3, "question_class": "litigation_legal"},
    "Litigation: lagna lord + Moon vs 6th lord + Mars; 8th and 12th lords adversarial.",
    "Prashna Mārga, Ch. 17 (Śatru Prashna)",
    "sourced_inference", "INFERENCE",
    [tn(213, 1, "6", "चोरभीति, शत्रु, संथाम ... रोग, चाकर इनका विचार छदे स्थानम्‌ करना"),
     tn(213, 1, "7", "वणिग्दृत्ति अन्यक सथं विवाद्‌ वा संधि"),
     tn(244, 1, "21", "विवादप्रश्चमं करग्रह ठग्नम्‌ बदट्वानच्‌ हो तो विवादमं प्रष्टा ्जतिगा")],
    SIG_INF % "the held text assigns enemies/war to the 6th (Sl.6) but 'vivāda' (dispute/litigation) to the 7th (Sl.7), and its dispute prashna (PG244 Sl.21-23) compares lagna with the 7th (the opponent); Mars as litigation karaka is not stated",
    BN % ("6", 213), "acharya",
    "In Tājika Nīlakaṇṭhī the opponent in a vivāda is the 7th (Sl.7; PG244 Sl.21-23) while the 6th covers enemies/war. Should "
    "'litigation_legal' keep the 6th lord as quesited, or move to (or add) the 7th lord with the 6th as secondary?",
    "Possible house mismatch (6th vs 7th) for 'disputes'; row value unchanged.")

add(T, {"id": 4, "question_class": "lost_object"},
    "Lost object: 2nd = movable objects, 4th = fixed/hidden; lord of 2nd or 4th; 4th sign gives direction/colour; Ithasala = recovery.",
    "Prashna Mārga, Ch. 20 (Nashṭa Dravya Prashna)",
    "sourced_inference", "INFERENCE",
    [tn(213, 1, "2", "रत्न, शुव्णादि धातु,धनवश्च ... विचार दुसर मावसे करना"),
     tn(213, 1, "4", "रध कदर सरग आदिकोमं प्रवेश इतने चतथंभावस देखने"),
     tn(227, 1, "23", "सप्तम स्थानसे चोर) चत॒थसे उसकी प्रापि, छ्रसे द्रव्य ओर चन्द्रमा धनका स्वामी"),
     tn(226, 1, "18-19", "ठञ्मे प्रथम द्रेष्काण हो तो षरकं द्वारसमीप वस्तु है")],
    SIG_INF % "Tajika nashta-dhana chapter (PG224-229) names lagna = the article, 7th = thief, 4th = recovery, Moon/2nd lord = the wealth, with the direction read from the Moon's/lagna's position and decanate - not '4th = fixed objects, sign colour'",
    BN % ("2 and 4", 213), "acharya",
    "For a lost object the Tājika Nīlakaṇṭhī nashta-dhana chapter uses lagna (article), 2nd/Moon (wealth), 4th (recovery), 7th "
    "(thief) and a decanate/Moon-based direction. Should the row be restated to that scheme or kept as the Prashna Mārga 2nd/4th "
    "movable-fixed split?",
    "The 2nd (jewels/metals) and 4th (buried treasure, wells) significations at Sl.2 and Sl.4 do support the row's split; the colour/direction clause does not appear.")

add(T, {"id": 5, "question_class": "health_illness"},
    "Health: 1st = body, 6th = disease, 8th lord = chronic/critical; Moon, Saturn karakas.",
    "Prashna Mārga, Ch. 13 (Ārogya Prashna)",
    "sourced_inference", "INFERENCE",
    [tn(243, 1, "13", "ठ्ेश वा चन्द्रमा ष्ठेशसे मृथशिरी हो वा अस्तगत हो तो रोगी होगा"),
     tn(213, 1, "6", "चोरभीति, शत्रु, संथाम ... रोग, चाकर इनका विचार छदे स्थानम्‌ करना"),
     tn(242, 1, "7", "अष्टमेश अस्त वा नष्ट बी होकर कंद्रम हो लग्ेशसे मथगशिल करता हो तो रोगप्रशमं मृत्यु होगी")],
    SIG_INF % "Saturn as chronic-disease karaka is not stated; the Tajika sick-person prashna (PG241 Sl.1) also assigns physician to the 7th, disease to the 10th and medicine to the 4th, which differs from the row's single 6th-house focus",
    BN % ("6", 213), "acharya",
    "Tājika Nīlakaṇṭhī's illness prashna (PG241 Sl.1-4) reads lagna/7th/10th/4th for patient/physician/disease/medicine and the "
    "6th lord for 'will he fall ill'. Should the health row keep a single 6th-house frame with Saturn, or be restated?",
    "House-level 6th = roga is FACT (Sl.6); the multi-house illness scheme is an extension the row does not carry.")

add(T, {"id": 6, "question_class": "finance_wealth"},
    "Finance: 2nd (wealth) and 11th (gains); Jupiter karaka; Ithasala lord-1/lord-2 or Jupiter = gain; lord-12 afflicting = loss.",
    "Prashna Mārga, Ch. 15 (Dhana Prashna)",
    "sourced_inference", "INFERENCE",
    [tn(224, 1, "6", "ठगरेश चन्द्रराशि तथा धनभावेश इत्थशार ... धनलाभ"),
     tn(213, 1, "2", "रत्न, शुव्णादि धातु,धनवश्च ... विचार दुसर मावसे करना"),
     tn(214, 1, "12", "व्ययभावसे जाने")],
    SIG_INF % "the Tajika dhana-labha rule (Sl.6) is lagna lord + lord of the Moon's sign + 2nd lord in Ithasala with benefic influence = gain; Jupiter as karaka and 'lord-12 afflicting lord-2' are not stated (12th = expenditure per Sl.12)",
    BN % ("2", 213), "acharya",
    "Tājika Nīlakaṇṭhī Sl.6 requires lagna lord, the Moon-sign lord and the 2nd lord in Ithaśāla (with benefic yoga/aspect) for "
    "dhana-lābha; may the finance row cite it for the 2nd-lord part while the Jupiter karaka and 12th-lord-loss clause stay unsourced?",
    "Closest of the 12 rows to a verbatim match for the lord skeleton.")

add(T, {"id": 7, "question_class": "travel_journey"},
    "Travel: 9th (long journeys), 12th (foreign), Mercury and Saturn karakas; lords of 9th and 12th quesited.",
    "Prashna Mārga, Ch. 21 (Yātrā Prashna)",
    "sourced_inference", "INFERENCE",
    [tn(214, 1, "9", "उपदेश, यात्रा, मढ ओर धममकायं नवमस्थानसे विचारके कहना"),
     tn(261, 1, "1", "छग्नेश वा चंद्रमासे नवमशका मथाशे हो वा छग्नेश नवम हो ता गमन होगा"),
     tn(214, 1, "12", "व्ययभावसे जाने")],
    SIG_INF % "12th = foreign travel, Mercury (short journeys) and Saturn (sea/arduous journeys) are not stated; the Tajika 12th covers expenditure/renunciation/disputes (Sl.12)",
    BN % ("9", 214), "acharya",
    "Tājika Nīlakaṇṭhī's journey chapter (PG261-268) turns on lagna lord/Moon with the 9th lord; may the row cite it for the "
    "9th-lord part while the 12th-house foreign-travel and Mercury/Saturn karaka clauses stay unsourced?",
    "9th = yatra is FACT (Sl.9).")

add(T, {"id": 8, "question_class": "property_land"},
    "Property: 4th = immovable property/land/home; Mars (land) and Moon (home) karakas; Ithasala lord-1/lord-4 or Mars = acquisition.",
    "Prashna Mārga, Ch. 16 (Bhūmi Prashna)",
    "sourced_inference", "INFERENCE",
    [tn(213, 1, "4", "रध कदर सरग आदिकोमं प्रवेश इतने चतथंभावस देखने"),
     tn(243, 1, "18", "गृहभूमिस्थानानां चलन प्रश्न ... पुरोक्त एव विधिः")],
    SIG_INF % "the Tajika Sl.4 list for the 4th names wells, granary/threshing floor, farming, treasure-trove and caves - home/land are not named in the readable text; Mars and Moon karakas are not stated",
    BN % ("4", 213), "acharya",
    "May 'property_land' be re-cited to Tājika Nīlakaṇṭhī Sl.4 (4th: wells, fields, treasure, caves) as partial support, with the "
    "explicit 'home/land' wording and the Mars/Moon karakas left unsourced?",
    "Weakest of the 12 for the specific wording; Sl.4's OCR is noisy.")

add(T, {"id": 9, "question_class": "children_progeny"},
    "Children: 5th (children/conception/intelligence); Jupiter and Moon karakas; Ithasala lord-1/lord-5 or Jupiter = fulfilment.",
    "Prashna Mārga, Ch. 18 (Santāna Prashna)",
    "sourced_inference", "INFERENCE",
    [tn(235, 1, "1", "ठञ्ेश चंद्रमा पच मृश प्रस्पर इत्थशाटी हा तो सतति हागी"),
     tn(213, 1, "5", "गभेधारण, सन्तान ... इत्यादि पचम भावसे विचारना")],
    SIG_INF % "Jupiter as karaka is not stated in these passages (FACT for lagna lord + Moon + 5th lord Ithasala = progeny)",
    BN % ("5", 213), "recite",
    None,
    "Matches the lord skeleton exactly; proposed action is a partial re-cite (house + lords only).")

add(T, {"id": 10, "question_class": "death_longevity"},
    "Death/longevity: 8th; Saturn karaka; lord-8 afflicted and lord-1 weak = concern for life.",
    "Prashna Mārga, Ch. 22 (Āyu Prashna)",
    "sourced_inference", "INFERENCE",
    [tn(214, 1, "8", "इतने विचार अष्टम भावसे देखना"),
     tn(242, 1, "7", "अष्टमेश अस्त वा नष्ट बी होकर कंद्रम हो लग्ेशसे मथगशिल करता हो तो रोगप्रशमं मृत्यु होगी"),
     tn(241, 1, "5", "ठम अष्टमेश ओर ठञ्चश एवं चन्द्रमा अष्टम हो ता भी मृत्य होवे")],
    SIG_INF % "Saturn as karaka of death is not stated; the Tajika death indications are specific lagna-lord/8th-lord/Moon placement rules in the sick-person prashna",
    BN % ("8", 214), "acharya",
    "May the death_longevity row cite Tājika Nīlakaṇṭhī (8th; 8th lord with lagna lord/Moon in specified places = death in an illness "
    "prashna) while the Saturn karaka stays unsourced?",
    "8th-house link is FACT; the row's Ayu Prashna scheme is not reproduced.")

add(T, {"id": 11, "question_class": "spiritual_religious"},
    "Spiritual: 9th (dharma, guru, pilgrimage); Jupiter karaka; 5th lord and 12th lord supporting.",
    "Prashna Mārga, Ch. 23 (Dharma Prashna)",
    "sourced_inference", "INFERENCE",
    [tn(214, 1, "9", "उपदेश, यात्रा, मढ ओर धममकायं नवमस्थानसे विचारके कहना"),
     tn(222, 1, "53-54", "सप्तममं सीसंबेधी, नवमम धमसंबधी,दशममे गरु वा राजसबधी")],
    SIG_INF % "Jupiter as karaka and the 5th/12th supporting clause are not stated; 9th = dharma/diksha/math is FACT (Sl.9)",
    BN % ("9", 214), "acharya",
    "May the spiritual row cite Tājika Nīlakaṇṭhī Sl.9 (9th: dīkṣā, yātrā, maṭha, dharma-kārya) for the 9th-house part while "
    "the Jupiter karaka and the 5th/12th-lord support stay unsourced?",
    "House-level support only.")

add(T, {"id": 12, "question_class": "enemy_conflict"},
    "Enemy/conflict: 6th (enemies, opponents); Mars and Sun karakas; lord-1 stronger than lord-6 = victory; malefics in 6th/12th.",
    "Prashna Mārga, Ch. 17 (Śatru Prashna)",
    "sourced_inference", "INFERENCE",
    [tn(213, 1, "6", "चोरभीति, शत्रु, संथाम ... रोग, चाकर इनका विचार छदे स्थानम्‌ करना"),
     tn(256, 1, "1-3", "राजाके संयामपरश्षमं ठञ् तथा टग्रेश ... शत्रका जय पराजय")],
    SIG_INF % "the Tajika war prashna (PG256-261) compares lagna/lagna lord with the 7th/7th lord (the enemy) rather than the 6th lord; Mars and Sun karakas and the 12th-malefic-hidden-foe clause are not stated",
    BN % ("6", 213), "acharya",
    "Tājika Nīlakaṇṭhī gives enemies/war to the 6th (Sl.6) yet its war prashna weighs lagna against the 7th. Should 'enemy_conflict' "
    "keep the 6th lord only, or add the 7th lord as the opposing party?",
    "Same 6th/7th ambiguity as litigation_legal.")

# --------------------------------------------------------------------------------------------
# 4. bg_prashna_fructification_rules (5)
# --------------------------------------------------------------------------------------------
T = "bg_prashna_fructification_rules"
FR_NOTE = (" Existing locator 'Ch. 5 (Phala adhyaya)' is unresolvable: the held Tajika Nilakanthi (Devanagari OCR, awaiting native "
           "decision) has no readable degree/sign -> hours/days/months/years timing table; its readable timing statements are "
           "(a) the Ithasala degree-difference x 12 -> days remark (PG53 Sl.5-6) and (b) a gunaka-division method (PG218-219 "
           "Sl.36-41); Uttara Kalamrita Ch.VII (PG172-173) has a number-division method and a flat 12-degree 'quick' orb "
           "(its horary pages PG163-171 are absent from the corpus).")

add(T, {"id": 1, "rule_id": "degree_to_hours"},
    "1 degree of remaining orb in the applying aspect = 1 hour; movable lagna and fast quesited planet; same-day events.",
    "Tājika Nīlakaṇṭhī, Ch. 5 (Phala adhyāya — fructification timing)",
    "unsourced_marked", "NONE", [], None, None, "mark_unsourced", None,
    "No held chunk states a degree-to-hour conversion, nor the movable-lagna/fast-planet applicability." + FR_NOTE)

add(T, {"id": 2, "rule_id": "degree_to_days"},
    "1 degree of remaining orb = 1 day; default short-term timing rule for dual-sign lagnas and ordinary questions.",
    "Tājika Nīlakaṇṭhī, Ch. 5 (Phala adhyāya); Prashna Mārga Ch. 7",
    "contradicted", "CONTRADICTS",
    [tn(53, 1, "5-6", "जो शेष रह उस बारह १२ से गुनदेना, इतन दिनोमं उस इत्थशाटका फट होगा"),
     ct("uttara_kalamrita", 173, 1, None, "If it is within twelve degrees. the result comes quickly.")],
    None, None, "acharya",
    "Tājika Nīlakaṇṭhī Sl.5-6 (commentary, PG53): take the difference of the two Ithaśāla planets' degrees, multiply by twelve, and "
    "that many days is when the Ithaśāla result comes ('ऐसे सर्वत्र जानना'). The row converts one degree to one day. Which "
    "conversion should the platform use, and does it depend on sign quality (movable/fixed/dual)?",
    "Single OCR passage (verse text itself not OCR'd; only the Hindi commentary). Digits and word agree on 'twelve' (बारह १२). "
    "Row NOT changed; lower confidence than the yoga-definition contradictions." + FR_NOTE)

add(T, {"id": 3, "rule_id": "sign_to_months"},
    "Each sign traversed by the slower significator = 1 month (or 1 degree = 1 month); fixed lagna, medium-speed planets.",
    "Tājika Nīlakaṇṭhī, Ch. 5 (Phala adhyāya)",
    "unsourced_marked", "NONE", [], None, None, "mark_unsourced", None,
    "No held chunk states a sign-to-month conversion." + FR_NOTE)

add(T, {"id": 4, "rule_id": "sign_to_years"},
    "Each sign traversed = 1 year; 1 degree = 1 year for very slow matters; Saturn/Jupiter quesited.",
    "Tājika Nīlakaṇṭhī, Ch. 5 (Phala adhyāya)",
    "unsourced_marked", "NONE", [], None, None, "mark_unsourced", None,
    "No held chunk states a sign-to-year conversion." + FR_NOTE)

add(T, {"id": 5, "rule_id": "sign_quality_timing_matrix"},
    "Movable = short, fixed = long, dual = medium time; shorter of rising sign and significator's sign prevails; applied before degree count.",
    "Tājika Nīlakaṇṭhī, Ch. 5 (Phala adhyāya); Prashna Mārga Ch. 7 (Kāla Nirṇaya)",
    "unsourced_marked", "NONE", [], None, None, "mark_unsourced", None,
    "No readable held chunk states the movable/fixed/dual timing matrix. Uttara Kalamrita's table of contents (PG10) lists "
    "'Terms chara, sthira, dvisvabhava ... Time of fructification' in its horary chapter, but those body pages are absent from "
    "the corpus, so nothing can be read." + FR_NOTE)

# --------------------------------------------------------------------------------------------
# 5. bg_prashna_special_techniques (3)
# --------------------------------------------------------------------------------------------
T = "bg_prashna_special_techniques"
add(T, {"id": 1, "technique_id": "nashta_jataka"},
    "Prashna chart for the moment of asking used as proxy birth chart: Prashna Lagna = proxy birth Lagna; positions read as natal.",
    "Prashna Mārga, Ch. 28 (Naṣṭa Jātaka adhyāya)",
    "sourced_inference", "INFERENCE",
    [ct("brihat_jataka", 525, 1, "1", "make out the chart of the querist from the rising sign at the time of query"),
     ct("brihat_jataka", 527, 1, "2", "position of Jupiter should be located in one of the 4 houses"),
     ct("hora_sara", 307, 1, None, "This is called Nashta Jataka Paddhati."),
     ct("saravali", 195, 1, None, "The Navansa Lagna at the time of query may also be the natal Ascendant."),
     ct("saravali", 194, 2, None, "the 5th and the 9th therefrom will indicate the natal Rasi")],
    "Topic FACT: three held texts (Brihat Jataka Ch.XXVI, Hora Sara Ch.27, Saravali 'Lost Horoscopy') cast a chart at the time of "
    "query to recover unknown birth data. INFERENCE gap: they DERIVE natal factors by rules (ayana from the half of the lagna sign; "
    "natal Jupiter from the lagna decanate; Ritu from decanate lord; natal Moon from the 5th/9th of the query lagna; "
    "Jupiter = 2x asc / 5) - the query-time planetary positions are not simply read as natal positions, and only one Saravali variant "
    "equates the query Navamsa Lagna with the natal ascendant ('may also be').",
    "Brihat Jataka, Ch. XXVI (printed 'CHAPTER XXVI'), Sloka 1 as printed — brihat_jataka:PG525:C1 (Sastri 2nd ed.); "
    "Hora Sara, Ch. 27, Sloka 5 as printed — hora_sara:PG308:C1 (Santhanam trans.); "
    "Saravali, 'Lost Horoscopy' — saravali:PG195:C1 (Santhanam trans. attr.)",
    "acharya",
    "Brihat Jataka Ch.XXVI, Hora Sara Ch.27 and Saravali derive the lost birth data from the query chart by rules (Jupiter, Ritu, "
    "Moon from the 5th/9th of the query lagna, etc.) rather than reading the query chart as the birth chart. Should the technique "
    "be restated as 'derive natal data from the query chart per these rules' instead of 'use the Prashna chart as a proxy natal chart'?",
    "Row's 'proxy' statement is a simplification of the held procedures (Saravali's 'may also be' variant aside); the Prashna "
    "Marga Ch.28 citation is not held. Not marked contradicted because one held variant does equate query Navamsa Lagna with natal ascendant.")

add(T, {"id": 2, "technique_id": "tithi_nakshatra_yoga"},
    "Panchanga elements at question time (Tithi, Moon's nakshatra, Yoga) are classified benefic/malefic/mixed before judgment.",
    "Prashna Mārga, Ch. 3 (Pañcāṅga Vichāra in Prashna)",
    "text_not_held", "NONE", [], None, None, "none", None,
    "Prashna Marga not held. Held Brihat Samhita Adh. XCVIII-XCIX (PG761-766) give general nakshatra/tithi properties for "
    "undertakings, not a question-moment panchanga screen; only one chunk in the Tajika Prashna-tantra pages (PG207-290) mentions "
    "tithi or nakshatra at all. The 'traditional Tajika Nakshatra table' is not found.")

add(T, {"id": 3, "technique_id": "omen_nimitta"},
    "Omens at the moment of the question (animal-call direction, objects in view, sounds) interpreted by explicit classical nimitta rules.",
    "Prashna Mārga, Ch. 2 (Nimitta adhyāya); Bṛhat Saṃhitā (Nimitta sections)",
    "sourced_inference", "INFERENCE",
    [ct("brihat_samhita", 425, 1, "1", "direction, speech place and articles brought at the time"),
     ct("brihat_samhita", 688, 1, "80", "When at a query the querist or an omen stands in any of the eight quarters"),
     ct("brihat_samhita", 689, 1, "1", "An omen crying in the East ... indicates the arrival of an officer of the king"),
     ct("brihat_samhita", 676, 1, "39", "conch shells ... are auspicious to the left of a traveller")],
    "General claim FACT: Brihat Samhita prescribes query-time observation of direction, speech, articles, limbs touched and omens "
    "(Adh. LI Sl.1; Adh. LXXXVI Sl.79-80; Adh. LXXXVII Sl.1-12). INFERENCE gap: none of the row's four illustrative rules is "
    "stated - 'bird from east auspicious for sunrise questions, north inauspicious', 'iron = Saturn/obstacles', 'flowers = Venus', "
    "'conch = Vishnu', 'drum = war'. Held BS says a tranquil omen crying in the East brings an officer's arrival; conch shells are "
    "an auspicious sound to the left of a traveller; drums/musical instruments in the NW quarter are linked with getting such "
    "instruments and meeting bards (PG691 Sl.12), not war.",
    "Brihat Samhita, Adh. LI (Prediction through Limbs), Sloka 1 as printed — brihat_samhita:PG425:C1 (Sastri 1946); "
    "Adh. LXXXVI, Sloka 80 as printed — brihat_samhita:PG688:C1; Adh. LXXXVII, Sloka 1 as printed — brihat_samhita:PG689:C1",
    "acharya",
    "The omen row's four example rules (east/north bird at sunrise, iron = Saturn, flowers = Venus, conch = Vishnu, drum = war) are "
    "not in Brihat Samhita as read. Should the examples be removed or each be traced to an explicit source before the row keeps "
    "'only rules with explicit classical textual support are applied'?",
    "Row's own safeguard ('only rules with explicit textual support') is not met by the listed examples. PG689 sloka numbering "
    "(Sl.1) is read from 'Sloka 1.-' printed in the chunk.")

# --------------------------------------------------------------------------------------------
with open("/private/tmp/claude-504/scratch/curation/bg_prashna_rules/ledger.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)

from collections import Counter
c = Counter(r["state"] for r in rows)
t = Counter(r["table"] for r in rows)
print(len(rows), dict(c))
print(dict(t))
