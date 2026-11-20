#!/usr/bin/env python3
"""Builds ledger.json for bg_doshas from the read-only extracts + hand-verified findings.
All corpus findings below were read in classical_text_chunks via rq.sh (read-only)."""
import json, os, re, collections

D = os.path.dirname(os.path.abspath(__file__))
cat = {}
for l in open(f"{D}/catalog79.jsonl"):
    r = json.loads(l); cat[r["canonical_id"]] = r
ont = {}
for l in open(f"{D}/onto79.jsonl"):
    r = json.loads(l); ont[r["canonical_id"]] = r
assert len(cat) == 79 and len(ont) == 79 and set(cat) == set(ont)

BPHS = "Santhanam trans., Ranjan Publications"
PHAL = "Sastri trans. 1950"
MC = "Muhurta Chintamani, Mahidhara Sharma bhasha tika, Khemraj Shrikrishnadas Press"
UK = "P.S. Sastri trans., Ranjan Publications"
BNN = "R.G. Rao, Ranjan Publications; MEDIUM provenance"


def c(text_id, chunk_id, page, sloka, quote, role="supports"):
    return {"text_id": text_id, "chunk_id": chunk_id, "page": page,
            "sloka_printed": sloka, "quote": quote, "role": role}


E = {}  # canonical_id -> dict of hand-built fields

# ---------------------------------------------------------------- 26 verse-cited rows
E["badhaka_dosha"] = dict(
    claim="Badhaka lord (11th movable / 9th fixed / 7th dual) afflicting lagna or its lord gives hidden obstacles.",
    state="unsourced_marked", support_class="NONE",
    corpus=[
        c("bphs", "bphs_pg0597_c01", "PG597", "20-21", "Aquarius, Taurus, Leo and Scorpio are Badhake", "context_only_truncated"),
        c("bphs", "bphs_pg0598_c01", "PG598", None, "occasions of great sorrow, imprison ment and diseases during the Dasa", "context_only_other_sense"),
    ],
    inference_step=None, proposed_citation=None, proposed_action="acharya",
    acharya_question=("BPHS (Santhanam) Ch.50 (PG597-598, Narayana-dasa of rasis) prints sl.20-21 on Badhaka signs but the "
                      "held chunk breaks off mid-sentence ('...are Badhake') and the next chunk resumes at '...moveable sign is its Badhaka house'. "
                      "Does BPHS (or another classical text) give the 11th/9th/7th Badhaka-house rule AND the dosha 'Badhaka lord afflicts the lagna "
                      "or its lord (hidden obstacles)', or is the lagna-affliction doctrine later tradition (the held BPHS context is only Badhaka "
                      "house of a dasa-rasi)?"),
    divergence_flags=[],
    notes=("Only BPHS hits for 'badhak' are 3 chunks (pg0485 index line, pg0597, pg0598), all in the Chapter 50 dasa-of-rasis context. "
           "The 11th/9th/7th mapping is not readable (list of 4 signs, rest of sentence lost at chunk boundary); the dosha as defined (badhaka lord "
           "afflicting lagna/lagna lord) is not stated. Existing citation 'bphs' has no chapter."),
    existing_citation_check="not_supported_by_readable_chunk")

E["balarishta"] = dict(
    claim="Malefic affliction to Moon/lagna indicates infant-affliction (balarishta); read with longevity factors.",
    state="sourced_fact", support_class="FACT",
    corpus=[
        c("bphs", "bphs_pg0108_c01", "PG108", None, "Balarishta or mfant mortality", "translator_note_definition"),
        c("bphs", "bphs_pg0109_c01", "PG109", "3-6", "SHORT-LIFE COMBINATIONS (upto sloka 23)", "heading_of_the_arishta_slokas"),
    ],
    inference_step=None,
    proposed_citation="BPHS Ch. 9 (Evils At Birth), Sloka 3-6 as printed — bphs:PG109:C1 (Santhanam trans., Ranjan Publications)",
    proposed_action="recite", acharya_question=None, divergence_flags=[],
    notes=("Row is a generic umbrella; Ch.9 header 'Chapter 9 Evils At Birth' printed at PG108:C1 resolves the chapter number "
           "(row text calls it 'Arishta-adhyaya'; printed title is 'Evils At Birth'). The four specific balarishta_* rows carry the concrete rules."),
    existing_citation_check="chapter_resolved_via_printed_header")

E["balarishta_moon_dusthana"] = dict(
    claim="Waning Moon in 6/8/12, afflicted by malefics without benefic aspect: infant-affliction (BPHS Ch.9).",
    state="sourced_fact", support_class="FACT",
    corpus=[
        c("bphs", "bphs_pg0109_c01", "PG109", "3-6", "Moon be in the 6th,-8th, or the l2th from the ascendant"),
        c("bphs", "bphs_pg0109_c01", "PG109", "3-6", "there be g benefic's aspect, it may live upto 8", "cancellation_text"),
        c("bphs", "bphs_pg0109_c02", "PG109", None, "If she is increasing, this need not be feared.", "translator_note_waxing_exception"),
    ],
    inference_step=None,
    proposed_citation="BPHS Ch. 9 (Evils At Birth), Sloka 3-6 as printed — bphs:PG109:C1 (Santhanam trans., Ranjan Publications)",
    proposed_action="recite", acharya_question=None,
    divergence_flags=["cancellation: text says a benefic's aspect only lets the child live up to age 8 (partial reprieve); row bhanga lists 'benefic in kendra, Jupiter aspect on Moon' as cancelling - kendra-benefic bhanga not printed in the chunk"],
    notes="Formation (Moon in 6/8/12 with malefic aspect; waning per translator's note) is stated. Not counted as contradicted: the formation matches.",
    existing_citation_check="chapter_resolved_via_printed_header")

E["balarishta_paap_kartari"] = dict(
    claim="Lagna or Moon hemmed between malefics (2nd and 12th) with no benefic relief: hemming arishta (BPHS Ch.9).",
    state="sourced_inference", support_class="INFERENCE",
    corpus=[
        c("bphs", "bphs_pg0112_c01", "PG112", "16", "while the ascendant is hemmcd between other malefics will bring early death"),
        c("bphs", "bphs_pg0112_c01", "PG112", "19", "hemmed between malefics will confer premature death"),
        c("bphs", "bphs_pg0112_c01", "PG112", "20", "Moon be in the ascendant hemmed between two malefics"),
    ],
    inference_step=("BPHS prints hemming only as one clause of compound yogas (sl.16: malefics in 12th+6th or 8th+2nd while the ascendant is hemmed; "
                    "sl.19: Moon in asc/7th/8th/12th AND hemmed; sl.20: Moon in asc hemmed AND a malefic in 7th/8th). The row generalises to 'lagna or Moon hemmed "
                    "by malefics in 2nd/12th' and drops the extra placement conditions - an inference/generalisation, not a printed rule."),
    proposed_citation="BPHS Ch. 9 (Evils At Birth), Sloka 16, 19-20 as printed — bphs:PG112:C1 (Santhanam trans., Ranjan Publications)",
    proposed_action="recite", acharya_question=None,
    divergence_flags=["row drops the additional placement conditions BPHS attaches to hemming (sl.19: Moon in 1/7/8/12; sl.20: malefic in 7th/8th)"],
    notes="Sister row papa_kartari_moon (non-balarishta) is sourced separately (Ch.80 sl.42).",
    existing_citation_check="chapter_resolved_via_printed_header")

E["balarishta_sandhi"] = dict(
    claim="Birth at a sign or house junction (sandhi) with lagna/Moon under malefic influence is balarishta (BPHS Ch.9).",
    state="contradicted", support_class="CONTRADICTS",
    corpus=[
        c("bphs", "bphs_pg0110_c02", "PG110", "13", "birth in the morning or evening junctions", "text_says"),
        c("bphs", "bphs_pg0111_c01", "PG111", "14", "morning twilight and evening twilight", "text_defines_sandhya_as_time_twilight"),
        c("bphs", "bphs_pg0111_c01", "PG111", "13", "Ganoanta while the Moon and mabfics occupy angles", "sign_junction_is_the_separate_gandanta_item"),
    ],
    inference_step=None,
    proposed_citation=None, proposed_action="acharya",
    acharya_question=("BPHS Ch.9 sl.13-14 (PG110:C2, PG111:C1) defines the 'junction' birth as Sandhya = the twilight of 3 ghatikas around sunrise/sunset "
                      "(a time junction), listed beside birth in the Moon's hora and birth in Gandanta, each requiring the Moon and malefics in angles. "
                      "The row 'balarishta_sandhi' defines sandhi as a rashi/bhava (sign/house) junction. Should the row be re-defined as Sandhya (twilight) birth, "
                      "with the sign-junction case left to gandanta_dosha, or is a bhava-sandhi balarishta a separate teaching?"),
    divergence_flags=["row's definition of 'sandhi' (sign/house junction) differs from BPHS's 'Sandhya' (twilight, sl.14); required Moon+malefics-in-angles condition absent from row"],
    notes="Contradiction is on the definition of the junction, not on the arishta idea. Row NOT changed.",
    existing_citation_check="chapter_resolved_but_definition_differs")

E["combust_dosha"] = dict(
    claim="Planet within its classical combustion orb of the Sun (Maudhya); orbs Moon 12, Mars 17, Mercury 14/12r, Jupiter 11, Venus 10/8r, Saturn 15.",
    state="sourced_fact", support_class="FACT",
    corpus=[
        c("bphs", "bphs_pg0099_c01", "PG99", None, "Please see ths following table for degrees of combustion", "translator_note_table_OCR_partly_garbled"),
        c("bphs", "bphs_pg0099_c01", "PG99", None, "Rahu and Ketu should not be treatcd as combust", "supports_nodes_excluded"),
        c("uttara_kalamrita", "uttara_kalamrita_pg0135_c01", "PG135", None, "Moon 12. Kuja 17. Budha 14 and when retrograde only 12", "full_orb_list_translator_note"),
        c("uttara_kalamrita", "uttara_kalamrita_pg0135_c01", "PG135", None, "Shukra 10 and when retrograde only 8, and Shani 15", "full_orb_list_translator_note"),
        c("uttara_kalamrita", "uttara_kalamrita_pg0048_c01", "PG48", None, "Chandra 12, Kuja 17, Budha 14, Guru 11, Shukra 10, and Shani 15", "corroborates_orbs"),
    ],
    inference_step=None,
    proposed_citation="BPHS, translator's Notes (combustion-degree table), printed p.100 — bphs:PG99:C1 (Santhanam trans., Ranjan Publications); full orb list also Uttara Kalamrita, Notes p.139 — uttara_kalamrita:PG135:C1 (P.S. Sastri trans., Ranjan Publications)",
    proposed_action="recite", acharya_question=None,
    divergence_flags=["BPHS PG99 table is OCR-garbled: legible Moon 12, Mars 17, Mercury 14, Jupiter 11, Venus 10; Saturn 15 and the two retrograde values are only fully legible in Uttara Kalamrita PG135/PG48",
                      "orbs are in a translator's Note (Santhanam), not a numbered BPHS sloka; row effect text ('ego overwhelms the planet') and bhanga 'own/exaltation sign despite combustion' are not stated in the chunks"],
    notes="Existing citation 'bphs' has no chapter; orb values themselves are FACT in the corpus. Venus/Saturn do not lose rays in combust state for Ayurdaya (BPHS PG99 note) - not the row's claim.",
    existing_citation_check="no_chapter_given_value_found_page_anchored")

E["dusthana_trikona_dosha"] = dict(
    claim="Natural malefic in a trikona (1/5/9) that is not itself a trikona lord damages fortune, progeny, dharma.",
    state="unsourced_marked", support_class="NONE", corpus=[],
    inference_step=None, proposed_citation=None, proposed_action="mark_unsourced", acharya_question=None, divergence_flags=[],
    notes=("Cited 'BPHS Ch.9' (Evils At Birth, PG108-118) was read: no statement that a malefic in a trikona harms fortune/progeny/dharma. "
           "Full-text probe of all BPHS chunks for malefic+trine/5th+9th found no such rule (hits are Karakamsa and Rahu-dasa contexts)."),
    existing_citation_check="cited_chapter_does_not_state_it")

E["gandanta_dosha"] = dict(
    claim="Moon (or lagna) at a water-fire sign/nakshatra junction (gandanta): early-life vulnerability.",
    state="sourced_inference", support_class="INFERENCE",
    corpus=[
        c("bphs", "bphs_pg0111_c01", "PG111", "13 (translator note)", "The last Navamsas of Cancer, of Scorpio and of lisces are called as Gandanta"),
        c("bphs", "bphs_pg1018_c01", "PG1018", "3", "last two ghatikas of Revti and first two ntikas of Aswini", "Ch.92 nakshatra gandanta (also Ashlesha/Makha, Jyestha/Moola)"),
        c("bphs", "bphs_pg1019_c01", "PG1019", "4", "The last half ghatika of Pisces and-first half ghatika of Aries", "Ch.92 lagna gandanta (also Cancer/Leo, Scorpio/Sagittarius)"),
    ],
    inference_step=("Junction pairs (Pisces|Aries, Cancer|Leo, Scorpio|Sagittarius; Revati|Ashwini, Ashlesha|Magha, Jyeshtha|Mula) are printed in Ch.92. "
                    "The row's measure 'last/first 3deg20'' is the Ch.9 translator's 'last Navamsa' for the water signs; BPHS Ch.92 itself measures in 'half ghatika'. "
                    "Reading 'Moon (or lagna)' dosha effect from Ch.92 (gandanta births 'likely to cause death', remedies) is an inference; Ch.9 sl.13 requires Moon and malefics in angles."),
    proposed_citation="BPHS Ch. 92 (Remedies from Birth in Gandanta), Sloka 3-4 as printed — bphs:PG1018:C1 and bphs:PG1019:C1 (Santhanam trans., Ranjan Publications); see also Ch. 9, Sloka 13 — bphs:PG110:C2",
    proposed_action="recite", acharya_question=None,
    divergence_flags=["existing citation Ch.9 only names Gandanta inside a compound early-death yoga (Moon+malefics in angles); the definition lives in Ch.92",
                      "degree measure 3deg20' vs BPHS 'half ghatika' (not identical units)"],
    notes="Citation Ch.9 resolves (printed header) but the definition is in Ch.92 (printed 'Chapter 92 Remedies from Birth in Gandanta' at PG1018/1019).",
    existing_citation_check="chapter_resolved_definition_is_in_other_chapter_92")

E["graha_yuddha_dosha"] = dict(
    claim="Two planets (not Sun/Moon/nodes) within 1 degree = planetary war; loser (lower declination) weakened.",
    state="sourced_inference", support_class="INFERENCE",
    corpus=[
        c("bphs", "bphs_pg0942_c01", "PG942", "9", "within one degree of each other), Venus is the conquerer", "Ch.79"),
        c("bphs", "bphs_pg0942_c01", "PG942", "9", "is thc canquerer and that in the South is coqi{ered defeated in the planetary war", "Ch.79"),
        c("bphs", "bphs_pg0124_c01", "PG124", None, "If a planet is defeated in planetary war, its bhava's potence is void.", "translator_note_effect"),
    ],
    inference_step=("BPHS Ch.79 sl.9 names the five tara-grahas, 1 degree orbit, Venus always conqueror, otherwise the one in the North conquers. Row's 'lower declination "
                    "loses' is a reading of 'South = defeated' as declination; the translator's note (PG124) gives other criteria (lesser longitude / higher latitude, C.G. Rajan). "
                    "Effect ('weakened for the life') is the translator's note on bhava potence, not a sloka."),
    proposed_citation="BPHS Ch. 79, Sloka 9 as printed — bphs:PG942:C1 (Santhanam trans., Ranjan Publications)",
    proposed_action="recite",
    acharya_question=("BPHS Ch.79 sl.9 (PG942:C1): within 1 degree, Venus always conquers and among Mars/Mercury/Jupiter/Saturn the one in the North conquers, the Southern is defeated; "
                      "the translator also cites 'lesser longitude wins' (PG124:C1). The row says the loser is the one with lower declination and omits the Venus rule. "
                      "Which criterion should the row carry?"),
    divergence_flags=["row omits 'Venus is always the conqueror'", "loser criterion 'lower declination' vs BPHS 'South/North' vs translator note 'lesser longitude'", "row bhanga (loser in own/exaltation sign may win) is not printed"],
    notes="Chapter 79 printed at PG941:C1 ('Chapter 79', Pravrajya/ascetic yogas); sl.9 on PG942.",
    existing_citation_check="no_chapter_given_value_found_page_anchored")

E["gulika_dosha"] = dict(
    claim="Gulika (Mandi) in a kendra, trikona or conjunct a planet poisons the house/planet it touches (chronic hidden affliction).",
    state="contradicted", support_class="CONTRADICTS",
    corpus=[
        c("bphs", "bphs_pg0246_c01", "PG246", "62", "lf Gulika is in the ascendant, the nutive will ie-africtcd by diseases", "agrees_house_1"),
        c("bphs", "bphs_pg0247_c01", "PG247", "65", "If Gulika is in rhe 4rh, the native will be sickly, devoid of happiness", "agrees_house_4"),
        c("bphs", "bphs_pg0248_c01", "PG248", "66", "If Gulika is in the 5rh, the native will not be praise- worthy, be poor", "agrees_house_5"),
        c("bphs", "bphs_pg0249_c01", "PG249", "70", "If Gulika is in the 9th, the native will undergo many ordeals", "agrees_house_9"),
        c("bphs", "bphs_pg0249_c01", "PG249", "71", "lf Gulika is in the l0th, the native will beendowed with sons, be happy", "CONTRADICTS_house_10_is_a_kendra"),
    ],
    inference_step=None, proposed_citation=None, proposed_action="acharya",
    acharya_question=("BPHS Ch.25 sl.62-73 (PG246-250) gives Gulika's effect house by house: adverse in the 1st, 2nd, 4th, 5th, 8th, 9th, 12th but favourable in the 3rd, 10th (sons, happy, "
                      "meditation, sl.71) and 11th (sl.72). The row says Gulika in ANY kendra/trikona or conjunct a planet is a dosha. Is the row's kendra/trikona/conjunction rule "
                      "a classical statement (which text?) or later tradition; should the 10th (a kendra) be excluded?"),
    divergence_flags=["row's 'kendra' includes the 10th, which BPHS sl.71 calls favourable", "row's 'conjunct a major planet' rule has no printed counterpart in the Gulika slokas", "row bhanga 'Jupiter aspects Gulika' not printed"],
    notes=("Partial contradiction: BPHS agrees the 1st/4th/5th/9th placements are adverse, so the dosha idea is attested house-wise; the generic kendra+trikona+conjunction formation "
           "is not, and the 10th is stated favourable. Gulika's computation note (Saturn's muhurta) is attested in BPHS Ch.4 notes (PG60) - not the dosha claim. Row NOT changed."),
    existing_citation_check="chapter_not_given_house_wise_slokas_found_ch25")

E["karaka_dosha"] = dict(
    claim="A planet placed in the house it naturally signifies (e.g. Jupiter in 5th) harms that bhava ('karako bhava nashaya').",
    state="unsourced_marked", support_class="NONE",
    corpus=[c("uttara_kalamrita", "uttara_kalamrita_pg0085_c01", "PG85", None, "If a malefic is posited in a sign owned by a Karaka", "different_rule_not_the_maxim")],
    inference_step=None, proposed_citation=None, proposed_action="mark_unsourced", acharya_question=None, divergence_flags=[],
    notes=("Probes over all 15 texts for 'karako', 'bhava nasha(ya)', 'significator/karaka ... own house ... destroy/harm' found no statement of the maxim or of the karaka-in-own-bhava dosha "
           "(only the unrelated Uttara Kalamrita rule about a malefic in a karaka-owned sign). Cited 'bphs' has no chapter."),
    existing_citation_check="not_found_in_cited_text")

E["kemadruma"] = dict(
    claim="No planet (excluding Sun) with the Moon or in 2nd/12th from it, nor in an angle from the ascendant: Kemadruma.",
    state="sourced_fact", support_class="FACT",
    corpus=[
        c("bphs", "bphs_pg0385_c01", "PG385", "11-13", "no planet with the Moon or in the 2nd/l2th from the Moon", "formation"),
        c("bphs", "bphs_pg0385_c01", "PG385", "11-13", "reduced to penury and perils", "effect"),
    ],
    inference_step=None,
    proposed_citation="BPHS Ch. 37, Sloka 11-13 as printed — bphs:PG385:C1 (Santhanam trans., Ranjan Publications)",
    proposed_action="recite",
    acharya_question=("BPHS Ch.37 sl.11-13 (PG385:C1) excludes only the Sun and counts an angle from the ASCENDANT. The row also excludes the nodes and adds 'none in kendra from the Moon'. "
                      "Should the row's kendra-from-Moon cancellation and node exclusion be kept, attributed to another text, or aligned to BPHS?"),
    divergence_flags=["row excludes nodes; BPHS excludes only the Sun", "row adds 'kendra from the Moon' as cancellation; BPHS names 'an angle from the ascendant' only", "row bhanga 'Moon aspected by a benefic' not printed", "row effects 'loneliness, mental restlessness' not printed (text: reproached, bereft of intelligence and learning, penury and perils)"],
    notes="Chapter 37 printed at PG384:C1 header; a Kemadruma-in-dasa remark is at PG339:C1 (not used).",
    existing_citation_check="no_chapter_given_value_found_page_anchored")

for cid, house, comment in (("kuja_dosha_bhanga_exaltation", "exaltation", "Mars exalted (Capricorn)"),
                            ("kuja_dosha_bhanga_own_sign", "own sign", "Mars in own sign (Aries/Scorpio)")):
    E[cid] = dict(
        claim=f"Kuja Dosha is cancelled when {comment} stands in a Kuja-dosha house.",
        state="unsourced_marked", support_class="NONE",
        corpus=[c("bphs", "bphs_pg0956_c01", "PG956", "48-49", "If the man and woman possessing this yoga join in wedlock, the yoga ceases", "only_cancellation_BPHS_prints_not_this_one")],
        inference_step=None, proposed_citation=None, proposed_action="mark_unsourced", acharya_question=None, divergence_flags=[],
        notes=("BPHS prints one cancellation only: both partners Manglik (sl.48-49). Mars in exaltation/own sign as a cancellation is not stated in the cited text. "
               "Ontology label 'BPHS Ch.78 (Kuja Dosha / Vivaha Dosha adhyaya)' is wrong for the held BPHS: Ch.78 is the Ascendants-description chapter (PG935:C1); the Kuja/widowhood sloka is in Ch.80 (Female Horoscopy)."),
        existing_citation_check="cited_chapter_78_is_a_different_chapter")

KUJA_PROPOSED = "BPHS Ch. 80 (Female Horoscopy), Sloka 47 as printed — bphs:PG956:C1 (Santhanam trans., Ranjan Publications)"
KUJA_CORPUS = [
    c("bphs", "bphs_pg0956_c01", "PG956", "47", "The woman born becomes a widow, if Mars the l2th, 4th, 7th or 8th from", "house_list"),
    c("bphs", "bphs_pg0956_c01", "PG956", "48-49", "are called IVlangali or Mangalik", "translator_note_names_Manglik"),
]
KUJA_FLAGS_COMMON = ["existing citation 'BPHS Ch.78' is a different chapter in the held BPHS (Ascendants description, PG935:C1); the rule is in Ch.80 (printed 'Chapter 80' at PG955:C1 and PG957:C1; contents list '80. FEMALE HOROSCOPY 935')",
                     "sl.47 is a rule about a woman's widowhood (sl.48-49 extend to a man's widowerhood); OCR of the benefic-condition clause is garbled ('unaspected ... associated with any benefic'), reading uncertain",
                     "row's detailed effect wording (bedroom discord, property disputes, divorce) is not printed; the printed effect is widowhood only"]
for cid, h, claim in (("kuja_dosha_lagna_12th", 12, "Mars in the 12th from lagna: Kuja Dosha (loss/expense, bedroom affliction)."),
                      ("kuja_dosha_lagna_4th", 4, "Mars in the 4th from lagna: Kuja Dosha (domestic friction, marital tension)."),
                      ("kuja_dosha_lagna_7th", 7, "Mars in the 7th from lagna: classic severe Kuja Dosha (harm to spouse)."),
                      ("kuja_dosha_lagna_8th", 8, "Mars in the 8th from lagna: severe Kuja Dosha (longevity of marriage threatened).")):
    corp = list(KUJA_CORPUS)
    fl = list(KUJA_FLAGS_COMMON)
    note = "House membership (12/4/7/8 from the Ascendant) is a printed list; bhanga 'both partners Manglik' is printed (sl.48-49); other bhanga clauses are not."
    if h == 7:
        corp += [c("phaladeepika", "phaladeepika_pg0147_c01", "PG147", None, "if Mars occupies it (the 7th), the female born will, become a widow", "corroboration_other_text"),
                 c("saravali", "saravali_pg0102_c02", "PG102", "32", "If Mars is posited in 7th, the native will lose his wife", "corroboration_other_text")]
        note += " Mars-in-7th is additionally attested in Phaladeepika and Saravali (other held texts)."
    E[cid] = dict(claim=claim, state="sourced_fact", support_class="FACT", corpus=corp, inference_step=None,
                  proposed_citation=KUJA_PROPOSED, proposed_action="recite", acharya_question=None,
                  divergence_flags=fl, notes=note, existing_citation_check="cited_chapter_78_wrong_value_found_in_ch80")

for cid, h in (("kuja_dosha_lagna_1st", 1), ("kuja_dosha_lagna_2nd", 2)):
    E[cid] = dict(
        claim=f"Mars in the {h}{'st' if h == 1 else 'nd'} from lagna counts as a Kuja Dosha house" + (" (mildest)." if h == 1 else " (admitted by Parashara, BPHS Ch.78, though debated)."),
        state="contradicted", support_class="CONTRADICTS",
        corpus=[c("bphs", "bphs_pg0956_c01", "PG956", "47", "The woman born becomes a widow, if Mars the l2th, 4th, 7th or 8th from", "text_lists_four_houses_only")],
        inference_step=("Contradiction is by exclusion from an enumerated list: the held BPHS names Mars in 12th, 4th, 7th, 8th from the Ascendant and does not include the "
                        f"{'1st' if h == 1 else '2nd'}; no other BPHS chunk adds it. Read as 'the text names a different set', not as an explicit denial."),
        proposed_citation=None, proposed_action="acharya",
        acharya_question=("BPHS (Santhanam) Ch.80 sl.47 (PG956:C1) lists Mars in the 12th, 4th, 7th or 8th from the Ascendant ONLY; the 1st and 2nd houses (and the Moon/Venus reckoning in 'manglik') "
                          "are not in the held text. Is there a classical verse (which text, which sloka) that adds the 1st/2nd, or should kuja_dosha_lagna_1st and _2nd (and the 1/2/4/7/8/12 set in "
                          "'manglik') be re-attributed from BPHS to later tradition?"),
        divergence_flags=KUJA_FLAGS_COMMON[:1] + ["row 2nd text says 'considered Kuja Dosha by Parashara (BPHS Ch.78)'; the held Parashara text does not list the 2nd" if h == 2 else "row presents the 1st as a Kuja Dosha house with a BPHS citation; BPHS list excludes it"],
        notes="Row NOT changed. Sister rows for 12th/4th/7th/8th are sourced_fact against the same sloka.",
        existing_citation_check="cited_chapter_78_wrong_and_house_not_in_ch80_list")

E["manglik"] = dict(
    claim="Mars in 1/2/4/7/8/12 from lagna (and additionally from Moon and Venus) afflicts marriage.",
    state="sourced_inference", support_class="INFERENCE",
    corpus=KUJA_CORPUS + [c("bphs", "bphs_pg0956_c01", "PG956", "48-49", "If the man and woman possessing this yoga join in wedlock, the yoga ceases", "bhanga_both_manglik")],
    inference_step=("The printed core (Mars in 12th/4th/7th/8th from the Ascendant, widowhood; both-Manglik cancellation; term 'Mangalik/Manglik' used in the translator's note) is FACT. "
                    "The row's additional houses (1st, 2nd) and the Moon- and Venus-reckoning are NOT in the held BPHS; they are therefore unsourced extensions, and the row is only inference-level."),
    proposed_citation=KUJA_PROPOSED, proposed_action="recite",
    acharya_question=None,
    divergence_flags=["houses 1 and 2 and the Moon/Venus references are not printed (see kuja_dosha_lagna_1st/_2nd acharya question)"] + KUJA_FLAGS_COMMON[:2]
    + ["row bhanga items other than both-Manglik (own/exaltation, Jupiter, sign-specific) are not printed"],
    notes="Umbrella row; the per-house rows carry the detail.",
    existing_citation_check="no_chapter_given_value_found_page_anchored")

E["neecha_dosha"] = dict(
    claim="Planet in debilitation sign without neecha-bhanga functions at minimum strength; lordships weakened.",
    state="sourced_inference", support_class="INFERENCE",
    corpus=[
        c("phaladeepika", "phaladeepika_pg0247_c01", "PG247", "30", "at its mini- mum or nil according as the planets are in the exalta-", "debilitation_gives_nil_or_minimum_good_influence"),
        c("phaladeepika", "phaladeepika_pg0117_c01", "PG117", "26", "be in a Kendra position with respect to the Moon's place or the Lagna", "neecha_bhanga_lord_of_depression_or_exaltation_sign_in_kendra"),
        c("phaladeepika", "phaladeepika_pg0118_c01", "PG118", "27-29", "planet is in depression, but is- aspected by the lord of that Rasi", "extra_bhanga_not_in_row"),
    ],
    inference_step=("Phaladeepika prints (a) good influence 'at its minimum or nil' in the depression sign (Adh. XX sl.30) and (b) neecha-bhanga conditions that turn a debilitated planet into a king-making yoga "
                    "(Adh. VI sl.26-29: dispositor / exaltation-lord in kendra from Moon or Lagna; aspect by the sign-lord). Reading (b) as 'cancels the neecha dosha' and (a) as "
                    "'lordships weakened' is an inference. The cited text BPHS contains no neecha-bhanga rule (only a modern horoscope anecdote at PG230:C2)."),
    proposed_citation="Phaladipika Adh. XX, Sloka 30 — phaladeepika:PG247:C1 and Adh. VI, Sloka 26-29 — phaladeepika:PG117:C1, phaladeepika:PG118:C1 (Sastri trans. 1950)",
    proposed_action="recite", acharya_question=None,
    divergence_flags=["existing citation 'bphs' (no chapter) is not supported by any BPHS chunk; support is in Phaladeepika", "row bhanga 'planet exalted in navamsa' and 'mutual debilitation aspect' not printed", "Phaladeepika adds 'aspect by lord of the depression sign' bhanga not in the row"],
    notes="Re-citation to another held text; BPHS citation should be replaced, not kept, if the row is re-cited.",
    existing_citation_check="not_found_in_cited_text_found_in_phaladeepika")

E["papa_kartari_lagna"] = dict(
    claim="Malefics in both the 2nd and 12th from lagna hem the ascendant (papa-kartari on lagna).",
    state="sourced_fact", support_class="FACT",
    corpus=[
        c("phaladeepika", "phaladeepika_pg0087_c01", "PG87", "8", "when Ihe above two houses are occupied by malefics", "formation_12th_and_2nd_from_Lagna"),
        c("phaladeepika", "phaladeepika_pg0088_c01", "PG88", "11", "poor, impure, unhappy, bereft of wife and children, deprived of some limb", "effect"),
    ],
    inference_step=None,
    proposed_citation="Phaladipika Adh. VI, Sloka 8 and 11 — phaladeepika:PG87:C1, phaladeepika:PG88:C1 (Sastri trans. 1950)",
    proposed_action="recite", acharya_question=None,
    divergence_flags=["row effect wording ('obstacles to self-expression'; 'physical vulnerability') is looser than the printed effect (poor, impure, unhappy, bereft of wife and children, limb-deprived, short-lived)", "row bhanga (shubha-kartari also present; strong lagna lord) not printed"],
    notes="Existing citation 'phaladeepika' had no locator; now page-anchored. Sloka numbers read from 'Sloka 8'/'Sloka 11' markers in the chunks.",
    existing_citation_check="no_locator_given_value_found_page_anchored")

E["papa_kartari_moon"] = dict(
    claim="Malefics in the 2nd and 12th from the Moon hem the mind; anxiety, emotional suppression.",
    state="sourced_fact", support_class="FACT",
    corpus=[
        c("bphs", "bphs_pg0955_c01", "PG955", "42", "the Moon and the Ascendant be Subjected to Papa Kartari Yoga", "formation_translator_gloss_12th_and_2nd"),
        c("bphs", "bphs_pg0112_c01", "PG112", "19", "hemmed between malefics will confer premature death", "Ch.9_arishta_context"),
    ],
    inference_step=None,
    proposed_citation="BPHS Ch. 80 (Female Horoscopy), Sloka 42 as printed — bphs:PG955:C1 (Santhanam trans., Ranjan Publications); see also Ch. 9, Sloka 19 — bphs:PG112:C1",
    proposed_action="recite", acharya_question=None,
    divergence_flags=["existing citation Ch.9 prints the Moon-hemmed case only inside an early-death yoga (sl.19-20); the explicit Papa-Kartari-on-Moon wording is in Ch.80 sl.42",
                      "row effects (anxiety, emotional suppression, reinforcing kemadruma) are not printed; BPHS effect is premature death (Ch.9) / destroyer of husband's and father's family (Ch.80 sl.42)"],
    notes="Formation FACT; effect text of the row is unsourced (differs in kind from BPHS).",
    existing_citation_check="chapter_resolved_value_also_found_in_ch80")

E["sarpa_yoga_dosha"] = dict(
    claim="Malefics in three kendras (Nabhasa Sarpa/Bhujanga yoga as a dosha): hardship, poverty, cruelty.",
    state="sourced_fact", support_class="FACT",
    corpus=[
        c("bphs", "bphs_pg0358_c01", "PG358", "8", "malefics so placed will cause Bhujanga or Sarpa yoga", "formation_Ch.35"),
        c("bphs", "bphs_pg0360_c01", "PG360", "22", "will be crooked, cruel, poor, miserable and will depend on others", "effect"),
    ],
    inference_step=None,
    proposed_citation="BPHS Ch. 35 (Nabhasa Yogas), Sloka 8 and 22 as printed — bphs:PG358:C1, bphs:PG360:C1 (Santhanam trans., Ranjan Publications)",
    proposed_action="recite", acharya_question=None,
    divergence_flags=["row adds 'with benefics not in kendras'; BPHS says '3 angles are occupied by ... malefics'", "row bhanga not printed"],
    notes="Chapter 35 printed at PG358:C1 and PG360:C1 headers; existing chapter citation verified.",
    existing_citation_check="chapter_resolved_via_printed_header")

E["trikona_dusthana_parivartana_dosha"] = dict(
    claim="Sign exchange between a trikona lord (1/5/9) and a dusthana lord (6/8/12) - Dainya parivartana tainting fortune.",
    state="sourced_inference", support_class="INFERENCE",
    corpus=[
        c("phaladeepika", "phaladeepika_pg0096_c01", "PG96", "32", "caused by the lords of the 6th, 8th and 12th and are termed (Dainya) Yogas", "definition_of_Dainya_parivartana"),
        c("phaladeepika", "phaladeepika_pg0097_c01", "PG97", "33", "will be a fool, will be reviling others and commit sin- iul actions", "effect"),
    ],
    inference_step=("Phaladeepika's Dainya yoga = ANY mutual sign exchange of a 6th/8th/12th lord with any other house lord (30 combinations). The row's trikona-dusthana "
                    "exchange is a subset of that set (Lagna/5th/9th lord with a 6/8/12 lord); reading the subset as the row's 'tainting fortune' is the inference."),
    proposed_citation="Phaladipika Adh. VI, Sloka 32-33 — phaladeepika:PG96:C1, phaladeepika:PG97:C1 (Sastri trans. 1950)",
    proposed_action="recite", acharya_question=None,
    divergence_flags=["existing citation 'BPHS Ch.39' is the Raja Yogas chapter (printed 'Chapter 39 Raja Yogas', PG386:C1); a probe of every BPHS chunk for dainya/parivartana/exchange found no Dainya rule there - existing citation not supported",
                      "printed effects are 'fool, reviling, sinful, tormented by enemies, interruptions to undertakings'; row effects (fortune/dharma house contaminated by dusthana themes) are an interpretation"],
    notes="Re-citation to Phaladeepika; the BPHS Ch.39 citation should be replaced if the row is re-cited.",
    existing_citation_check="cited_chapter_39_does_not_state_it")

# ---------------------------------------------------------------- 12 name-hit rows
SRC_NOTE_MC = ("muhurta_chintamani chunks carry source_citation '[MEDIUM] ... AWAITING_NATIVE_DECISION: Devanagari multilingual OCR path'; PG93-95 are Devanagari OCR of the Hindi tika "
               "(read by the worker), PG96-101 are an English/IAST translation of the same Vivaha section. Any re-citation to MC depends on the native's decision on that text.")

E["nadi_dosha"] = dict(
    claim="Bride and groom share the same Nadi (Aadi/Madhya/Antya): 8 of 8 koota points lost; gravest compatibility dosha.",
    state="sourced_fact", support_class="FACT",
    corpus=[
        c("muhurta_chintamani", "muhurta_chintamani_pg0097_c01", "PG97", "34", "Marriage of a couple falling within one and the same nāḍī is not good", "formation"),
        c("muhurta_chintamani", "muhurta_chintamani_pg0097_c01", "PG97", "34", "falling in the middle nāḍī, it means the death of both", "severity"),
        c("muhurta_chintamani", "muhurta_chintamani_pg0096_c02", "PG96", "34", "this is the first (ādya) nāḍī", "nakshatra-to-nadi table starts"),
        c("muhurta_chintamani", "muhurta_chintamani_pg0100_c01", "PG100", "37", "There is no doṣa (affliction) of nāḍī or of the gaṇas", "bhanga_same_nakshatra_different_pada"),
        c("muhurta_chintamani", "muhurta_chintamani_pg0093_c01", "PG93", "21", "नाडीमे गुण ८)", "8_points_for_nadi_Devanagari"),
    ],
    inference_step="'8 of 8 points lost' combines the printed allocation (nadi = 8 gunas, v.21) with the printed 'not good' - the loss of all 8 is the standard reading, not printed in words. 'Health/progeny concerns' is not printed (MC says death of both for middle nadi).",
    proposed_citation="Muhurta Chintamani, Vivaha (Prakarana 6, Ashtakuta-vichara), Verse 34 as printed — muhurta_chintamani:PG96:C2 and :PG97:C1; exception Verse 37 — :PG100:C1 (Mahidhara Sharma bhasha tika, Khemraj)",
    proposed_action="recite", acharya_question=None,
    divergence_flags=["severity printed is 'death of both' for the middle nadi; row says 'health/progeny concerns'", "MC also states the doshas of the two flanking nadis do not apply south of the Godavari or to Kshatriyas (not in row)", "MC status AWAITING_NATIVE_DECISION"],
    notes=SRC_NOTE_MC + " Prior WAVE note counted Nadi's 393 name hits as mostly Nadi-astrology; the IAST/Devanagari spellings (nāḍī / नाडी) were invisible to the ASCII name-match. The genuine statement is in MC.",
    existing_citation_check="token_replaced_by_page_anchored_source")

E["gana_dosha"] = dict(
    claim="Nakshatra-gana mismatch (Deva/Manushya/Rakshasa) - worst when Deva-bride and Rakshasa-groom.",
    state="sourced_fact", support_class="FACT",
    corpus=[
        c("muhurta_chintamani", "muhurta_chintamani_pg0095_c01", "PG95", "29-30", "राक्षस मनुष्यका मृत्यु, देव राक्षसका हो तो कलह होता है", "mismatch_effects_Devanagari"),
        c("muhurta_chintamani", "muhurta_chintamani_pg0095_c01", "PG95", "29", "रक्षोनरामरगणाः", "gana_nakshatra_classification_heading"),
        c("muhurta_chintamani", "muhurta_chintamani_pg0096_c01", "PG96", "33", "there is no doṣa of the gaṇas", "bhanga_friendship_of_rashi_and_amsa_lords"),
        c("muhurta_chintamani", "muhurta_chintamani_pg0100_c01", "PG100", "37", "There is no doṣa (affliction) of nāḍī or of the gaṇas", "bhanga_same_nakshatra_different_pada"),
    ],
    inference_step=None,
    proposed_citation="Muhurta Chintamani, Vivaha (Prakarana 6, Ashtakuta-vichara), Verse 29-30 as printed — muhurta_chintamani:PG95:C1; cancellation Verse 33 — :PG96:C1 (Mahidhara Sharma bhasha tika, Khemraj)",
    proposed_action="recite",
    acharya_question=("Muhurta Chintamani v.30 (PG95:C1, Hindi tika) ranks Rakshasa-Manushya as death (groom Manushya + bride Rakshasa: groom's death), Deva-Rakshasa as quarrel, "
                      "Deva-Manushya as middling. The gana_dosha row names 'Deva-bride & Rakshasa-groom' as worst. Which severity ordering should the row carry?"),
    divergence_flags=["row's 'worst when Deva-bride & Rakshasa-groom' is not the printed worst (Manushya-Rakshasa = death)", "row bhanga 'same rashi/nakshatra lord; Bhakoot satisfied' only partly matches the printed bhanga (friendship of rashi-lords and amsa-lords; same nakshatra different pada)", "MC status AWAITING_NATIVE_DECISION", "Devanagari OCR reading by worker"],
    notes=SRC_NOTE_MC, existing_citation_check="token_replaced_by_page_anchored_source")

E["yoni_dosha"] = dict(
    claim="Nakshatra-yoni (animal symbols) of the partners are natural enemies (cat-rat, cow-tiger); Yoni koota max 4.",
    state="sourced_fact", support_class="FACT",
    corpus=[
        c("muhurta_chintamani", "muhurta_chintamani_pg0094_c01", "PG94", "25-26", "स्पर योनिवेरमे अशुभ होना है । इनका वैर-गौ व्याघका", "formation_Devanagari"),
        c("muhurta_chintamani", "muhurta_chintamani_pg0094_c01", "PG94", "25-26", "एक योनिके वर कन्या उत्तम मित्र; समयोनिकं सामान्य", "bhanga_same_or_neutral_yoni"),
        c("muhurta_chintamani", "muhurta_chintamani_pg0094_c01", "PG94", "25-26", "बिल्ली चूहा", "cat-rat_enemy_pair"),
    ],
    inference_step=None,
    proposed_citation="Muhurta Chintamani, Vivaha (Prakarana 6, Ashtakuta-vichara), Verse 25-26 as printed — muhurta_chintamani:PG94:C1 (and :PG93:C2 where v.25 begins) (Mahidhara Sharma bhasha tika, Khemraj)",
    proposed_action="recite", acharya_question=None,
    divergence_flags=["row effect 'sexual/instinctual incompatibility' is an interpretation; MC prints 'inauspicious' and 4 gunas for yoni-maitri", "MC status AWAITING_NATIVE_DECISION", "Devanagari OCR reading by worker"],
    notes=SRC_NOTE_MC + " 'yoni' hits in ASCII search were other senses (Yavana Jataka 'category', Saravali 'Graha Yoni').",
    existing_citation_check="token_replaced_by_page_anchored_source")

E["varna_dosha"] = dict(
    claim="Groom's Moon-sign varna (water=Brahmin, fire=Kshatriya, earth=Vaishya, air=Shudra) lower than the bride's; Varna koota 1 point.",
    state="sourced_fact", support_class="FACT",
    corpus=[
        c("muhurta_chintamani", "muhurta_chintamani_pg0093_c01", "PG93", "22", "वरसे हीनवणं कन्या शुभ, कन्याके व्णसे हीनवणं वर अच्छा नहीं होता", "formation_Devanagari"),
        c("muhurta_chintamani", "muhurta_chintamani_pg0093_c01", "PG93", "22", "मीन, वृर्चिक, ककंट ब्राहाण तथा १।५.। ९। क्षत्रिय", "sign_to_varna_table_Devanagari"),
    ],
    inference_step="The fourth varna (Shudra for signs 3/7/11) is garbled in the OCR ('श्रवणं'); read as Shudra by elimination of the other three varnas printed in the same list. Brahmin=Pisces/Scorpio/Cancer (water), Kshatriya=1/5/9 (fire), Vaishya=2/6/10 (earth) are printed.",
    proposed_citation="Muhurta Chintamani, Vivaha (Prakarana 6, Ashtakuta-vichara), Verse 22 as printed — muhurta_chintamani:PG93:C1 (Mahidhara Sharma bhasha tika, Khemraj)",
    proposed_action="recite", acharya_question=None,
    divergence_flags=["MC status AWAITING_NATIVE_DECISION", "Devanagari OCR reading by worker (Shudra entry garbled)"],
    notes=SRC_NOTE_MC + " Row bhanga 'groom varna >= bride varna' matches the printed rule (varna-higher groom gets the 1 guna; bride higher does not).",
    existing_citation_check="token_replaced_by_page_anchored_source")

E["daridra"] = dict(
    claim="Lord of gains (11th) in a dusthana, or wealth-house lords debilitated/combust: chronic financial difficulty.",
    state="sourced_inference", support_class="INFERENCE",
    corpus=[
        c("phaladeepika", "phaladeepika_pg0105_c01", "PG105", "57", "lords of the several Bhavas from the Lagna onwards occupy the 6th, 3th oi 12th", "Daridra is #11 of 12 named yogas for the 12 bhavas"),
        c("phaladeepika", "phaladeepika_pg0108_c01", "PG108", "68", "will be loaded with debts, cruel, foremost among the poor", "effect"),
        c("bphs", "bphs_pg0133_c01", "PG133", "6-7", "the lords of the 2nd and the llth are botli combust or be with malefics", "penury_from_birth_Ch.13"),
    ],
    inference_step=("Phaladeepika Adh. VI sl.57 lists 12 yogas in bhava order (Daridra = 11th) arising when the lord of that bhava occupies 6/8/12 (or the bhava is hit by malefics): "
                    "reading 'Daridra = 11th lord in 6/8/12' rests on the ordering. BPHS Ch.13 sl.6-7 'Yogas for Poverty' supports 'wealth-house lords combust' but requires BOTH the 2nd and 11th lords "
                    "(and, in the first yoga, a malefic in the 2nd), not the 11th lord alone."),
    proposed_citation="Phaladipika Adh. VI, Sloka 57-58 and 68 — phaladeepika:PG105:C1, phaladeepika:PG108:C1 (Sastri trans. 1950); BPHS Ch. 13 (Effects of Second House), Sloka 6-7 as printed — bphs:PG133:C1 (Santhanam trans., Ranjan Publications)",
    proposed_action="recite", acharya_question=None,
    divergence_flags=["BPHS requires both 2nd and 11th lords afflicted; row says 11th lord alone in a dusthana", "row 'debilitated' for wealth-house lords is not printed in these chunks (BPHS sl.6-7 says combust or with malefics)", "row bhanga (dhana/raja yoga present; 11th lord retrograde-strong) not printed",
                      "name hits were mostly other senses (Jaimini, Hora Sara, Jataka Parijata 'Daridra yoga' sl.37-38 is a different Moon-based yoga whose formation sloka is OCR-unreadable)"],
    notes="Upgrade from the token to a page-anchored source is supportable but through the sloka-57 ordering inference.",
    existing_citation_check="token_replaced_by_page_anchored_source")

E["guru_chandal"] = dict(
    claim="Jupiter conjunct Rahu (wisdom-corruption combination): distorted judgment, unorthodox beliefs.",
    state="sourced_inference", support_class="INFERENCE",
    corpus=[
        c("bhrigu_nandi_nadi", "bhrigu_nandi_nadi_pg0188_c02", "PG188", None, "Saturn and Mars first meet Jupiter and Rahu in the watery sign Cancer", "worked-example_remark"),
        c("bhrigu_nandi_nadi", "bhrigu_nandi_nadi_pg0188_c02", "PG188", None, "By this Guru Chandala Yoga is formed.", "naming_remark"),
    ],
    inference_step="The only hit is the commentator's remark on a worked example horoscope (R.G. Rao, MEDIUM-provenance translation): Jupiter+Rahu in Cancer 'forms Guru Chandala Yoga'. Generalising the example to the rule 'Jupiter conjunct Rahu' is an inference; effects and bhanga are not stated.",
    proposed_citation="Bhrigu Nandi Nadi, commentary on example chart, p.188 — bhrigu_nandi_nadi:PG188:C2 (R.G. Rao, Ranjan; MEDIUM provenance)",
    proposed_action="acharya",
    acharya_question="Is the Bhrigu Nandi Nadi translator's remark (PG188:C2) 'Jupiter and Rahu ... Guru Chandala Yoga is formed' acceptable as the source for Guru Chandal Dosha (formation only), or does the row stay unsourced until a classical verse is named?",
    divergence_flags=["only formation (as a worked-example remark) - effects 'distorted judgment...' and bhanga not stated", "source is a modern commentary layer inside a nadi text, MEDIUM provenance"],
    notes="Single name hit of the 'Guru Chandal' pattern in the corpus.",
    existing_citation_check="token_replaced_by_weak_source_pending_acharya")

E["pitru_dosha"] = dict(
    claim="Affliction to Sun, 9th house or its lord by Rahu/Ketu/Saturn (ancestral karmic debt); father-related obstacles.",
    state="unsourced_marked", support_class="NONE",
    corpus=[
        c("bphs", "bphs_pg0981_c01", "PG981", "29-30 (OCR '2G30')", "no male issue as a result of the cursc of the father", "related_but_different_concept_Ch.83_curses"),
        c("bphs", "bphs_pg0982_c01", "PG982", "31-33", "To get deliverance form the curse of the father the rcmedial measures are", "remedies_for_the_same_Ch.83_curse"),
    ],
    inference_step=None, proposed_citation=None, proposed_action="acharya",
    acharya_question=("BPHS Ch.83 'Effects of curses in the previous birth' (contents list PG492:C1; sl.29-33 at PG981-982) gives 'curse of the father' yogas that cause lack of male issue "
                      "(e.g. Sun debilitated in Saturn's navamsa hemmed between malefics in the 5th; Sun in 9th + Saturn in 5th + 5th lord with Rahu) with Gaya-shraddha remedies. "
                      "The Pitru Dosha row defines a different formation (Sun / 9th house / 9th lord afflicted by Rahu, Ketu, Saturn). Is the row a rendering of the Ch.83 Pitru-shapa doctrine, "
                      "or a later-tradition doshas that must stay unsourced?"),
    divergence_flags=["Ch.83 is about putra-hani from a pre-natal curse, not 9th-house/Sun affliction as such"],
    notes=("48 name hits of 'pitru/pitri' are other senses (rites, Jaimini pitri-karaka, Brihat Samhita, Nadi Navamsa). No chunk states the row's formation. "
           "Sloka numbers at PG981 are OCR-garbled ('2G30'); '29-30' is by sequence with the clearly printed '31-33' at PG982."),
    existing_citation_check="token_not_provenance")

E["angarak"] = dict(
    claim="Mars conjunct Rahu (fire-poison combination): anger, accidents, inflammation.",
    state="unsourced_marked", support_class="NONE",
    corpus=[c("bhrigu_nandi_nadi", "bhrigu_nandi_nadi_pg0047_c02", "PG47", None, "This native has Angaraka Dosha (Mars in Aries).", "different_formation_commentator_usage")],
    inference_step=None, proposed_citation=None, proposed_action="mark_unsourced", acharya_question=None, divergence_flags=["the only 'Angaraka Dosha' usage defines it as Mars in Aries (commentator, worked example), not Mars-Rahu"],
    notes="The other 7 hits are 'Angaraka' as a name of Mars (Hora Sara, Jataka Parijata, Saravali, Jaimini sutra on shadvargas, Yavana Jataka contents).",
    existing_citation_check="token_not_provenance")

E["vish_dosha"] = dict(
    claim="Moon conjunct Saturn (poison combination): emotional heaviness, depression, chronic worry.",
    state="unsourced_marked", support_class="NONE", corpus=[],
    inference_step=None, proposed_citation=None, proposed_action="mark_unsourced", acharya_question=None, divergence_flags=[],
    notes=("Whole-word 'vish' has 0 hits; 'vish[a-z]* yoga/dosha' hits only 'Vishkambha yoga' (Jataka Parijata, a panchanga yoga). The 173 substring hits are Vishnu/Vishakha/etc. "
           "Chunks that mention Moon with Saturn state conjunction effects under other names, not a 'Vish' dosha."),
    existing_citation_check="token_not_provenance")

for cid, claim, pr_note in (
        ("vedha_dosha", "The two janma-nakshatras form a vedha (mutually obstructing) pair per the classical vedha table.",
         "MC PG105-106 prints 'pañcaśalākā-vedha' (a table of nakshatra pairs) but for choosing the WEDDING-DAY nakshatra, not for bride/groom janma-nakshatra compatibility; "
         "Phaladeepika's 15-17 'vedha' hits are transit vedha."),
        ("rajju_dosha", "Partners' janma-nakshatras occupy the same rajju (rajju-chakra); inauspicious (esp. siro, pada).",
         "'Rajju' hits are the Nabhasa Rajju yoga (BPHS, Brihat Jataka, Saravali, Hora Sara, Jataka Parijata, Yavana Jataka)."),
        ("mahendra_dosha", "Bride->groom nakshatra count is not a mahendra number: the mahendra (progeny/well-being) factor is absent.",
         "'Mahendra' hits are place names (hills, Brihat Samhita), the Mahendra ayurdaya school (Saravali, Jataka Parijata, Hora Sara), and 'Mahendra yoga' (Hora Sara).")):
    E[cid] = dict(
        claim=claim, state="unsourced_marked", support_class="NONE",
        corpus=[c("uttara_kalamrita", "uttara_kalamrita_pg0181_c01", "PG181", None, "These are Dina. gana, yorn, Rajju, Vedha, Nadi, Mahendra", "translator_note_names_the_kuta_only_no_rule")],
        inference_step=None, proposed_citation=None, proposed_action="mark_unsourced", acharya_question=None,
        divergence_flags=[], notes=pr_note + " The only chunk using the row's sense is a translator's note listing kuta names (no rule). No Devanagari/IAST form found in muhurta_chintamani (searched रज्जु, महेन्द्र, rajju, mahendra).",
        existing_citation_check="token_not_provenance")

# ---------------------------------------------------------------- 41 remaining token rows
G41_NAMES = []
CAND = {
    "abhukta_mula_dosha": [("bphs", "bphs_pg1019_c01", "rule_text", "Ch.92 sl.5 prints 'last 6 ghatikas of Jyestha and first 8 ghatikas of Moola are known as Abhukta Moola'; Ch.93 (PG1021:C1) gives its remedies"), ("bphs", "bphs_pg1021_c01", "rule_text", "Ch.93 Remedies from Birth in Abhukta Moola")],
    "mool_dosha": [("bphs", "bphs_pg1018_c01", "rule_text", "Ch.92 sl.3 Nakshatra Gandanta: Revati|Ashwini, Ashlesha|Magha, Jyestha|Moola junctions (the six gand-mula nakshatras)"), ("bphs", "bphs_pg1026_c01", "rule_text", "remedies for Jyestha Moola, Ashlesha Makha gandantas")],
    "bhakoot_dosha": [("muhurta_chintamani", "muhurta_chintamani_pg0096_c01", "rule_text", "v.31-32 (IAST): shatru-shadashtaka brings death; 5-9 loss of sons; 2-12 poverty; parihara of evil bhakuta")],
    "graha_maitri_dosha": [("muhurta_chintamani", "muhurta_chintamani_pg0094_c01", "rule_text", "v.27-28 (Devanagari) graha-kuta friendship table"), ("muhurta_chintamani", "muhurta_chintamani_pg0094_c02", "rule_text", "ṭīkā points for graha-maitri"), ("muhurta_chintamani", "muhurta_chintamani_pg0096_c01", "rule_text", "v.32-33 parihara of graha-kuta")],
    "vashya_dosha": [("muhurta_chintamani", "muhurta_chintamani_pg0093_c01", "rule_text", "v.23 (Devanagari) vashya groups; 2 points")],
    "tara_dosha_compat": [("muhurta_chintamani", "muhurta_chintamani_pg0093_c01", "rule_text", "v.24 (Devanagari) tara count by 9, 3 points")],
    "stree_deergha_dosha": [("uttara_kalamrita", "uttara_kalamrita_pg0181_c01", "mention_only", "translator's list of kutas names 'Strtdtrgha'; no rule")],
    "vish_kanya_dosha": [("bphs", "bphs_pg0955_c01", "rule_text", "Ch.80 sl.43-44 Visha Kanya birth day/nakshatra/tithi combinations and ascendant condition"), ("bphs", "bphs_pg0956_c01", "rule_text", "Ch.80 sl.45-46 effects and cancellation")],
    "mrityu_bhaga_dosha": [("phaladeepika", "phaladeepika_pg0169_c01", "rule_text_scope_differs", "Adh. XIII sl.10-11 degree lists for the Moon / 'fateful degrees' per sign - child-death context"), ("uttara_kalamrita", "uttara_kalamrita_pg0179_c01", "rule_text_OCR_garbled", "Mrityu Bhaga table")],
    "shakata": [("phaladeepika", "phaladeepika_pg0089_c01", "rule_text", "Adh. VI sl.14 'Moon in the 12th, 8th or 6th from Jupiter causes Sakata; no Sakata if Moon is in a kendra from the Lagna'"), ("phaladeepika", "phaladeepika_pg0090_c01", "rule_text", "Adh. VI sl.17 effects of Sakata yoga")],
    "naga_dosha_nodes_kendra": [("bphs", "bphs_pg0979_c01", "different_sense", "Ch.83 sl.9-16 'no male issue due to the curse of a serpent' (Rahu in 5th etc.)"), ("phaladeepika", "phaladeepika_pg0161_c01", "different_sense", "Rahu in 5th = curse of a serpent")],
    "naga_dosha_rahu_lagna": [("bphs", "bphs_pg0979_c01", "different_sense", "Ch.83 serpent-curse yogas"), ("phaladeepika", "phaladeepika_pg0161_c01", "different_sense", "Rahu in 5th = curse of a serpent")],
    "shrapit_dosha": [("bphs", "bphs_pg0978_c01", "different_sense", "Ch.83 yogas for various curses (serpent, father, mother, brother) causing sonlessness")],
    "kuja_dosha_from_moon": [("bphs", "bphs_pg0956_c01", "scope_differs", "Ch.80 sl.47 reckons Mars from the Ascendant only; no Moon reckoning printed")],
    "kemadruma_compat_kuja": [("bphs", "bphs_pg0956_c01", "scope_differs", "Ch.80 sl.47 reckons Mars from the Ascendant only; no Venus reckoning printed")],
    "chandal_yoga_dosha": [("hora_sara", "hora_sara_pg0275_c01", "different_formation", "Chandala yoga = Mars+Saturn in angle, Rahu in Lagna, benefics in 12th/6th (not Moon-Rahu)")],
    "sade_sati": [("phaladeepika", "phaladeepika_pg0330_c01", "different_framing", "Adh. XXVI per-house Saturn transit results (12th/1st/2nd, 4th, 8th from Moon) - no 7.5-year unit named")],
    "dhaiya": [("phaladeepika", "phaladeepika_pg0330_c01", "different_framing", "Adh. XXVI per-house Saturn transit results (4th/8th) - no 'dhaiya' unit named")],
    "grahan": [("bphs", "bphs_pg1016_c01", "different_sense", "Ch.91 birth DURING a solar/lunar eclipse (not natal Sun/Moon-node conjunction)")],
    "surya_grahan_dosha": [("bphs", "bphs_pg1016_c01", "different_sense", "Ch.91 birth during solar eclipse")],
    "chandra_grahan_dosha": [("bphs", "bphs_pg1016_c01", "different_sense", "Ch.91 birth during lunar eclipse")],
    "lagna_lord_grahan_dosha": [("bphs", "bphs_pg1016_c01", "different_sense", "Ch.91 eclipse birth; no lagna-lord/node rule")],
    "pitra_dosha_9th_lord_afflicted": [("bphs", "bphs_pg0981_c01", "different_sense", "Ch.83 father's-curse yogas (PG981-982)")],
    "pitra_dosha_sun_12th_malefic": [("bphs", "bphs_pg0981_c01", "different_sense", "Ch.83 father's-curse yogas")],
    "pitra_dosha_sun_rahu": [("bphs", "bphs_pg0982_c01", "different_sense", "Ch.83 sl.29-30 item (9): Sun in 9th, Saturn in 5th, 5th lord with Rahu - not Sun-Rahu conjunction")],
    "pitra_dosha_sun_saturn_conjunction": [("bphs", "bphs_pg0981_c01", "different_sense", "Ch.83 father's-curse yogas (Sun hemmed/with malefics)")],
}
for ks in ["kala_sarpa", "kala_sarpa_anant", "kala_sarpa_ghatak", "kala_sarpa_karkotak", "kala_sarpa_kulik", "kala_sarpa_mahapadma", "kala_sarpa_padma",
           "kala_sarpa_shankhachud", "kala_sarpa_shankhpal", "kala_sarpa_sheshnag", "kala_sarpa_takshak", "kala_sarpa_vasuki", "kala_sarpa_vishdhar", "kala_amrita_dosha"]:
    CAND[ks] = [("nadi_navamsa_patel", "nadi_navamsa_patel_pg0749_c01", "mention_only", "names 'Kalasarpa Yoga' and its bhanga, no formation printed"),
                ("bhrigu_nandi_nadi", "bhrigu_nandi_nadi_pg0159_c01", "mention_only", "worked example: 'All the planets are stationed between Rahu and Ketu'")]

TOKEN_IDS = [cid for cid in cat if cat[cid]["cit"] == [{"text_id": "classical_tradition"}]]
assert len(TOKEN_IDS) == 53
REST41 = [cid for cid in TOKEN_IDS if cid not in E]
assert len(REST41) == 41, len(REST41)
G41_Q = ("Batch question G41 (one question for 41 rows): for each of these 41 doshas of the Dosha catalogue that cite only the placeholder 'classical_tradition': "
         + "; ".join(cat[c_]["name_en"] for c_ in REST41)
         + ". For each name, please state either (a) the classical text, chapter and sloka that states its formation rule (so it can be re-cited and checked against the corpus), "
           "or (b) that it is later tradition with no classical verse, so the row is marked unsourced. Where the worker found a candidate chunk "
           "(see undecided_candidates in each row; e.g. Shakata, Abhukta-Mula, Mool, Bhakoot, Graha-Maitri, Vashya, Tara, Vish-Kanya, Mrityu-Bhaga), please also say whether that chunk is the rule you mean.")

for cid in REST41:
    ft = " ".join(cat[cid]["formation_text"].split()[:25])
    cands = [dict(text_id=t, chunk_id=ch, relevance=rel, note=n) for (t, ch, rel, n) in CAND.get(cid, [])]
    E[cid] = dict(
        claim=ft, state="unsourced_marked", support_class="NONE", corpus=[], inference_step=None, proposed_citation=None,
        proposed_action="acharya", acharya_question=G41_Q, divergence_flags=[],
        notes=("Not decided by this lane (ruling: 41 token rows go to the acharya as one grouped question). Citation is the token {\"text_id\":\"classical_tradition\"} (not provenance, SS ruling Q3). "
               "The earlier 'zero corpus mentions' probe used ASCII name-matches only; candidate chunks listed in undecided_candidates were found by script-/spelling-aware probes and are NOT adopted."
               if cands else
               "Not decided by this lane (grouped acharya question G41). Citation is the token (not provenance). No candidate chunk found by ASCII, IAST or Devanagari-aware probes."),
        existing_citation_check="token_not_provenance", undecided_candidates=cands)

# ---------------------------------------------------------------- assemble
ledger = []
for cid in sorted(cat):
    e = E[cid]
    r = cat[cid]
    cur = json.dumps(r["cit"], ensure_ascii=False)
    o = ont[cid]
    obj = {
        "asset": "bg_doshas", "table": "brahma_dosha_catalog (+ reference_doshas + brahma_ontology[entity_class='dosha'])",
        "row_key": {"canonical_id": cid,
                    "brahma_dosha_catalog.canonical_id": cid,
                    "reference_doshas.canonical_id": cid,
                    "brahma_ontology.id": o["id"], "brahma_ontology.entity_class": "dosha"},
        "row_count": 3,
        "name_en": r["name_en"],
        "claim": e["claim"],
        "current_citation": f"catalog.classical_citations={cur}; ontology.source_citation={o['src']!r}; reference_doshas: no citation column (canonical_id, name_en, category only)",
        "state": e["state"], "support_class": e["support_class"],
        "corpus": e["corpus"], "inference_step": e.get("inference_step"),
        "proposed_citation": e.get("proposed_citation"), "proposed_action": e["proposed_action"],
        "acharya_question": e.get("acharya_question"),
        "divergence_flags": e.get("divergence_flags", []),
        "notes": e.get("notes", ""), "existing_citation_check": e.get("existing_citation_check"),
    }
    if "undecided_candidates" in e:
        obj["undecided_candidates"] = e["undecided_candidates"]
    ledger.append(obj)

assert len(ledger) == 79
json.dump(ledger, open(f"{D}/ledger.json", "w"), ensure_ascii=False, indent=1)

cnt = collections.Counter(x["state"] for x in ledger)
print(dict(cnt))
print("total objects", len(ledger), "rows covered", sum(x["row_count"] for x in ledger))
print("proposed re-citations", sum(1 for x in ledger if x["proposed_citation"]))
print("contradicted", [x["row_key"]["canonical_id"] for x in ledger if x["state"] == "contradicted"])
grp = collections.defaultdict(list)
for x in ledger:
    grp[(x["current_citation"].split("; ontology")[0][:60], x["state"])].append(x["row_key"]["canonical_id"])
for k, v in sorted(grp.items(), key=lambda kv: kv[0]):
    print(k, len(v))
json.dump({"G41_names": [cat[c_]["name_en"] for c_ in REST41], "G41_ids": REST41, "G41_question": G41_Q}, open(f"{D}/g41.json", "w"), ensure_ascii=False, indent=1)
