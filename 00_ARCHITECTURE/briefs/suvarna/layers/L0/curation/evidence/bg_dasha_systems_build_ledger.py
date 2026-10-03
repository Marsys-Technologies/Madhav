#!/usr/bin/env python3
"""Builds ledger.json for bg_dasha_systems (read-only research; no DB writes)."""
import json, subprocess, collections

RQ = "/Users/Dev/suvarna-evidence/TrackI/ifl0/rq.sh"
OUT = "/private/tmp/claude-504/scratch/curation/bg_dasha_systems/ledger.json"
ASSET = "bg_dasha_systems"


def rq(sql):
    r = subprocess.run([RQ, sql], capture_output=True, text=True, timeout=100)
    lines = r.stdout.strip().split("\n")
    return [l.split("|") for l in lines[1:] if not (l.startswith("(") and l.endswith(")"))]


# ---- live current citations -------------------------------------------------
bds_cit = {}
for k, cc, sc in rq("select canonical_id, classical_citations::text, source_chunk_ids::text from brahma_dasha_systems order by 1"):
    bds_cit[k] = f"classical_citations={cc}; source_chunk_ids={sc}"
ont_cit = {k: sc for k, sc in rq("select canonical_id, source_citation from brahma_ontology where entity_class='dasha_system' order by 1")}
ref_rows = {k: (n, s) for k, n, s in rq("select canonical_id,name_en,school from reference_dasha_systems order by 1")}
assert len(bds_cit) == 20 and len(ont_cit) == 20 and len(ref_rows) == 20

BP = "(Santhanam trans.)"
JA = "(Suryanarain Rao trans. 1949)"
PH = "(Sastri trans. 1950)"


def c(text_id, chunk, page, sl, quote):
    return {"text_id": text_id, "chunk_id": chunk, "page": page, "sloka_printed": sl, "quote": quote}


def bp(chunk_no, sl, quote):  # BPHS corpus ref
    pg = f"PG{int(chunk_no[:4])}"
    return c("bphs", f"bphs_pg{chunk_no[:4]}_c{chunk_no[6:]}", pg, sl, quote)


def cite_bphs(pg, ck, sl, tail=""):
    s = f"BPHS Ch. 46 (Dasas (Periods) of planets), "
    s += f"Sloka {sl} as printed" if sl else f"p.{pg}"
    return f"{s} — bphs:PG{pg}:C{ck} {BP}{tail}"


# ---- the 20 systems ----------------------------------------------------------
S = {}

# 1 vimshottari
S["vimshottari"] = dict(
    bds=dict(state="sourced_fact", sup="FACT",
             claim="Vimshottari: nine lords Ketu-Venus-Sun-Moon-Mars-Rahu-Jupiter-Saturn-Mercury, 7/20/6/10/7/18/16/19/17 yrs, 120-yr cycle, reckoned from Moon's nakshatra, universal default.",
             corpus=[bp("0499_c01", "12-14", "Sun, the Moon, Mars, Rahu, Jupiter. Saturn, Mercury, Ketu and Venus in that order"),
                     bp("0499_c01", "15", "Meicury. Ketu and Venus are 6,lO, 7,"),
                     bp("0499_c02", "15", "18, 16, 19,l'1,7 and20 in thai order"),
                     bp("0499_c01", None, "natural life span of a human being is generally taken as 120 years"),
                     bp("0500_c01", None, "Makha, Moola and Aswini"),
                     bp("0519_c01", None, "Vimsottari is the main-Dasa system applicable to all")],
             inf=None,
             prop=cite_bphs("499", "1", "12-15"),
             act="recite", q=None,
             note="Existing cite 'BPHS Ch.46' is correct (Chapter 46 'Dasas (Periods) of planets' is printed at PG497:C1 and PG499:C1). BPHS prints the cycle from Krittika/Sun; the row lists the same cyclic order starting at Ketu (Asvini's lord per the PG500 table) - presentation rotation only, no value differs. Year sum 7+20+6+10+7+18+16+19+17 = 120."),
    ont=dict(state="sourced_fact", sup="FACT", claim="Vimshottari is a 120-year parashari dasha system (ontology description).",
             corpus=[bp("0499_c01", None, "natural life span of a human being is generally taken as 120 years")],
             inf=None, prop=cite_bphs("499", "1", "12-15"), act="recite", q=None,
             note="Current 'BPHS Ch.46 (Vimshottari Dasha)': chapter number correct; the parenthetical chapter title is not the printed title ('Dasas (Periods) of planets').")
)

# 2 ashtottari
S["ashtottari"] = dict(
    bds=dict(state="sourced_fact", sup="FACT",
             claim="Ashtottari: eight lords Sun6 Moon15 Mars8 Mercury17 Saturn10 Jupiter19 Rahu12 Venus21 = 108; conditional (Rahu placement; paksha rules); Ketu excluded.",
             corpus=[bp("0506_c01", "17-20", "Sun, the Moon, Mars, Mercury, Saturn, Jupiter, Rahu and Venus are 6, 15"),
                     bp("0506_c01", "17-20", "only 8 planets play the role of Dasa lords, Ketu having been denied"),
                     bp("0505_c01", "17-20", "Astottari Dasa, when Rahu not being in Lagna, in any other Kendra"),
                     bp("0508_c01", "23", "adopt the Astottari Dasa if the birth be in the day ... Shukla Paksha")],
             inf="Total 108 is the arithmetic sum of the printed years (6+15+8+17+10+19+12+21). The paksha clause (sl.23) is only partly legible in the OCR ('...in Shukla Paksha'); the Krishna/day half is not legible, so only the Rahu-placement rule is claimed as FACT.",
             prop=cite_bphs("505", "1", "17-20", "; PG506:C1 for years") , act="recite", q=None,
             note="Existing cite 'BPHS Ch.48' is wrong for this corpus: Ch.48 is 'Distinctive effects of the Nakshatra Dasa' (TOC PG483); Ashtottari is defined in Ch.46."),
    ont=dict(state="sourced_fact", sup="FACT", claim="Ashtottari is a 108-year parashari dasha system.",
             corpus=[bp("0506_c01", "17-20", "Sun, the Moon, Mars, Mercury, Saturn, Jupiter, Rahu and Venus are 6, 15")],
             inf="108 = sum of printed years.", prop=cite_bphs("505", "1", "17-20", "; PG506:C1"), act="recite", q=None,
             note="Current 'BPHS Ch.48 (Conditional Nakshatra Dashas)': chapter and title are not what the corpus prints; Ch.46 is the defining chapter.")
)

# 3 shodashottari
S["shodashottari"] = dict(
    bds=dict(state="sourced_fact", sup="FACT",
             claim="Shodashottari: Sun11 Mars12 Jupiter13 Saturn14 Ketu15 Moon16 Mercury17 Venus18 = 116; conditional (paksha + lagna rules).",
             corpus=[bp("0509_c01", "24-26", "Dasas of the Sun, Mars, Jupiter, Saturn, Ketu, Moon, Mercury and Venus"),
                     bp("0509_c01", "24-26", "arc of 11, l:, t3, 14, 15,16,17 and 18 years"),
                     bp("0509_c01", None, "birth is in Shukla Paksha and the Ascendant is in the Hora of the Sun")],
             inf="Total 116 = arithmetic sum of printed years. The worked example states the Shukla-paksha + Sun-hora condition; the sloka's own wording is OCR-garbled.",
             prop=cite_bphs("509", "1", "24-26"), act="recite", q=None,
             note="Existing cite 'BPHS Ch.48' wrong for this corpus (defined in Ch.46)."),
    ont=dict(state="sourced_fact", sup="FACT", claim="Shodashottari is a 116-year parashari dasha system.",
             corpus=[bp("0509_c01", "24-26", "arc of 11, l:, t3, 14, 15,16,17 and 18 years")],
             inf="116 = sum of printed years.", prop=cite_bphs("509", "1", "24-26"), act="recite", q=None,
             note="Current 'BPHS Ch.48 (Conditional Nakshatra Dashas)' - Ch.46 is the defining chapter in this corpus.")
)

# 4 dwadashottari
S["dwadashottari"] = dict(
    bds=dict(state="sourced_fact", sup="FACT",
             claim="Dwadashottari: Sun7 Jupiter9 Ketu11 Mercury13 Rahu15 Mars17 Saturn19 Moon21 = 112; conditional nakshatra dasha.",
             corpus=[bp("0511_c01", "27-28", "The Dasa order is the Sun, Jupiter, Ketu, Mercury, Rahu, Mars, Saturn, Moon"),
                     bp("0511_c01", "27-28", "The Dasas wiil be of 7,9,11, 13, 15,17, 19 and 21 years")],
             inf="Total 112 = arithmetic sum of printed years. Applicability sentence (Venus navamsa condition) is garbled in the OCR; the row's generic 'conditional' wording is not contradicted.",
             prop=cite_bphs("511", "1", "27-28"), act="recite", q=None,
             note="Existing cite 'BPHS Ch.48' wrong for this corpus (defined in Ch.46)."),
    ont=dict(state="sourced_fact", sup="FACT", claim="Dwadashottari is a 112-year parashari dasha system.",
             corpus=[bp("0511_c01", "27-28", "The Dasas wiil be of 7,9,11, 13, 15,17, 19 and 21 years")],
             inf="112 = sum of printed years.", prop=cite_bphs("511", "1", "27-28"), act="recite", q=None,
             note="Current 'BPHS Ch.48 (Conditional Nakshatra Dashas)' - Ch.46 is the defining chapter.")
)

# 5 panchottari
S["panchottari"] = dict(
    bds=dict(state="sourced_fact", sup="FACT",
             claim="Panchottari: Sun12 Mercury13 Saturn14 Mars15 Venus16 Moon17 Jupiter18 = 105; conditional nakshatra dasha.",
             corpus=[bp("0511_c01", "29-31", "The order of the Dasa lords is the Sun, Mercury, Saturn, Mars, Venus, Moon and Jupiter"),
                     bp("0511_c01", "29-31", "The Dasa of the planets are of 12,13,14,15,16,17"),
                     bp("0511_c02", None, "and l8 years in the aforesaid'order")],
             inf="Total 105 = arithmetic sum of printed years. Printed applicability: Ascendant Cancer and Cancer Dwadasamsa; row's generic 'conditional' is not contradicted.",
             prop=cite_bphs("511", "1", "29-31", "; PG511:C2 for the last year"), act="recite", q=None,
             note="Existing cite 'BPHS Ch.48' wrong for this corpus (defined in Ch.46)."),
    ont=dict(state="sourced_fact", sup="FACT", claim="Panchottari is a 105-year parashari dasha system.",
             corpus=[bp("0511_c01", "29-31", "The Dasa of the planets are of 12,13,14,15,16,17")],
             inf="105 = sum of printed years.", prop=cite_bphs("511", "1", "29-31"), act="recite", q=None,
             note="Current 'BPHS Ch.48 (Conditional Nakshatra Dashas)' - Ch.46 is the defining chapter.")
)

# 6 shatabdika
S["shatabdika"] = dict(
    bds=dict(state="contradicted", sup="CONTRADICTS",
             claim="Shatabdika: eight lords Venus5 Sun5 Moon10 Mars10 Mercury10 Jupiter20 Saturn20 Rahu20 = 100; nadi tradition.",
             corpus=[bp("0513_c01", None, "Sun, the Moon, Venus, Mercury, Jupiter, Mars and saturn"),
                     bp("0513_c01", None, "of 5,5,10,1il,20,20 and 30 years"),
                     bp("0513_c01", None, "Rahu and Ketu do not have a place in this Dasa system")],
             inf="BPHS prints seven lords in the order Sun, Moon, Venus, Mercury, Jupiter, Mars, Saturn with years 5,5,10,10,20,20,30 (sum 100; the OCR garbles one '10') and states Rahu/Ketu are excluded. Row has 8 lords incl. Rahu 20, Mars 10, Saturn 20. Only the 100-yr total agrees. Sloka number is not printed for this system (between sl.29-31 and the later 35-36).",
             prop=None, act="acharya",
             q="Shatabdika (BPHS Santhanam PG513:C1, sl. between 31 and 35): the printed text gives 7 lords Sun5, Moon5, Venus10, Mercury10, Jupiter20, Mars20, Saturn30 with Rahu/Ketu excluded; the row has 8 lords (Venus5, Sun5, Moon10, Mars10, Mercury10, Jupiter20, Saturn20, Rahu20). Which lord order and year table should the platform carry?",
             note="'nadi tradition' in conditions_for_use is not stated; printed applicability fragment is 'lagna ... in the same rasi' (OCR; reads like a vargottama-type condition). Existing cite 'BPHS Ch.48' wrong for this corpus (Ch.46)."),
    ont=dict(state="sourced_fact", sup="FACT", claim="Shatabdika is a 100-year dasha system.",
             corpus=[bp("0513_c01", None, "of 5,5,10,1il,20,20 and 30 years")],
             inf="100 = sum of printed years 5+5+10+10+20+20+30.", prop=cite_bphs("513", "1", None), act="recite", q=None,
             note="Only the total is checked here; the description does not carry the lord table. The synonym '100-year conditional dasha' is consistent. See the brahma_dasha_systems row for the contradicted sequence.")
)

# 7 chaturashiti_sama
S["chaturashiti_sama"] = dict(
    bds=dict(state="sourced_fact", sup="FACT",
             claim="Chaturashiti-sama: 7 lords x 12 years = 84 (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn); conditional on 10th-lord-in-10th charts.",
             corpus=[bp("0515_c01", None, "Count from Swati to the Janma Nakshatra and divide this number by 7"),
                     bp("0515_c01", None, "The Sun, The Moon, Mars, Mercury, Jupiter Venus and Saturn"),
                     bp("0515_c01", None, "The Dasa of each planet is of 12 years")],
             inf="84 = 7 x 12 (arithmetic). The applicability clause ('10th-lord-in-10th') is NOT legible in the held text: the English of the sloka's first half is missing (only the Sanskrit line survives), so that clause is left unsourced (not contradicted). Sloka number not printed.",
             prop=cite_bphs("515", "1", None, "; conditions_for_use clause remains unsourced"), act="recite", q=None,
             note="Existing cite 'BPHS Ch.49' wrong for this corpus (Ch.49 = Effects of Kalachakra Dasa; definition is Ch.46)."),
    ont=dict(state="sourced_fact", sup="FACT", claim="Chaturashiti-sama is an 84-year parashari dasha system.",
             corpus=[bp("0515_c01", None, "The Dasa of each planet is of 12 years")],
             inf="84 = 7 x 12.", prop=cite_bphs("515", "1", None), act="recite", q=None,
             note="Current 'BPHS Ch.49 (Kalachakra & Conditional Dashas)': Ch.49 in this corpus is 'Effects of the Kalachakra Dasa'.")
)

# 8 dwisaptati_sama
S["dwisaptati_sama"] = dict(
    bds=dict(state="sourced_fact", sup="FACT",
             claim="Dwisaptati-sama: 8 lords x 9 years = 72 (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu); conditional on lagna-lord/7th-lord exchange.",
             corpus=[bp("0515_c01", "37-39", "The Sun. the Moon, Mars, Mercury, Jupiter, Venus, Saturn and Rahu"),
                     bp("0515_c01", "37-39", "all the eight planetr have Dasa of 9 years each"),
                     bp("0515_c01", "37-39", "lord of the Ascendant is in the ... 7th")],
             inf="72 = 8 x 9. Applicability: the OCR prints only 'the lord of the Ascendant is in the [garbled] ... 7th'; the row's 'lagna-lord/7th-lord exchange' (mutual) is a stronger condition than the legible fragment and is not confirmable here.",
             prop=cite_bphs("515", "1", "37-39"), act="recite",
             q="Dwisaptati-sama applicability (BPHS Santhanam PG515:C1 sl.37-39; OCR legible only as 'the lord of the Ascendant is in the ... 7th'): is the condition 'lagna lord in the 7th (or 7th lord in lagna)' or a mutual exchange between them as the row states?",
             note="Existing cite 'BPHS Ch.49' wrong for this corpus (defined in Ch.46)."),
    ont=dict(state="sourced_fact", sup="FACT", claim="Dwisaptati-sama is a 72-year parashari dasha system.",
             corpus=[bp("0515_c01", "37-39", "all the eight planetr have Dasa of 9 years each")],
             inf="72 = 8 x 9.", prop=cite_bphs("515", "1", "37-39"), act="recite", q=None,
             note="Current 'BPHS Ch.49 (Kalachakra & Conditional Dashas)': Ch.49 in this corpus is Effects of Kalachakra Dasa.")
)

# 9 shashtihayani
S["shashtihayani"] = dict(
    bds=dict(state="contradicted", sup="CONTRADICTS",
             claim="Shashtihayani: Sun-centric 60-year scheme; lords listed Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu (9 lords); conditional on Sun-dominant charts.",
             corpus=[bp("0517_c01", "40-41", "Jupiter, the Sun, Mars, the Moon, Mercury, Venus, Saturn and Rahu"),
                     bp("0517_c01", "40-41", "adopted in cases where the Sun is posited in the Ascendant"),
                     bp("0517_c01", "40-41", "The remaining planets have Dasas of 6 years each")],
             inf="BPHS names 8 lords (no Ketu); the row's lords array adds Ketu (9). Also the OCR prints 'Jupiter, the Sun and Mars are of 13 years' but the worked example deducts from '10 years' for the Sun; 3x10+5x6 = 60 fits the row's 60-year total, 3x13+5x6 = 69 does not - the '13' is probably an OCR error but is unconfirmed.",
             prop=None, act="acharya",
             q="Shashtihayani (BPHS Santhanam PG517:C1 sl.40-41): the text lists 8 lords (Jupiter, Sun, Mars, Moon, Mercury, Venus, Saturn, Rahu) with no Ketu, and Sun/Mars/Jupiter 13 [or 10?] years, the other five 6 years. Should the row carry 8 lords without Ketu, and are the three long periods 10 years (total 60)?",
             note="Condition 'Sun-dominant' ~ 'Sun in the Ascendant' (consistent). Existing cite 'BPHS Ch.49' wrong for this corpus (Ch.46)."),
    ont=dict(state="sourced_inference", sup="INFERENCE", claim="Shashtihayani is a 60-year parashari dasha system.",
             corpus=[bp("0517_c01", "40-41", "The remaining planets have Dasas of 6 years each"),
                     bp("0517_c01", None, "deducting the result form l0 years, we will get the balance")],
             inf="60 follows only if Jupiter/Sun/Mars carry 10 years (the worked example) and not the printed '13'; 3x10 + 5x6 = 60. The BPHS text does not print the number 60.",
             prop=cite_bphs("517", "1", "40-41", "; total 60 by arithmetic from example (acharya to confirm 10 vs 13)"), act="recite", q=None,
             note="Current 'BPHS Ch.49 (Kalachakra & Conditional Dashas)': Ch.46 is the defining chapter.")
)

# 10 shattrimsha_sama
S["shattrimsha_sama"] = dict(
    bds=dict(state="contradicted", sup="CONTRADICTS",
             claim="Shattrimsha-sama: 36-year cycle; lord order depends on day vs night birth (Sun-first by day, Moon-first by night).",
             corpus=[bp("0517_c01", "42-43", "The Moon, the Sun, Jupiter, Mars, Mercury, Saturn, Venus and Rahu"),
                     bp("0517_c02", "42-43", "Their Dasas will be 1, 2, 3, 4, 5, 6, 7, 8 years in that order"),
                     bp("0519_c01", None, "birth is at night and the Ascendant be in the Hora of the Moon")],
             inf="BPHS prints ONE fixed order starting with the Moon (no day/night order flip). Day-birth-with-Sun-Hora vs night-birth-with-Moon-Hora is printed as the APPLICABILITY condition for choosing this system, not as a change of lord order. Total 36 = 1+..+8 agrees.",
             prop=None, act="acharya",
             q="Shattrimsha-sama (BPHS Santhanam PG517:C1-C2 sl.42-43, PG519:C1): the text gives one order (Moon, Sun, Jupiter, Mars, Mercury, Saturn, Venus, Rahu; 1..8 yrs) and uses day-birth/Sun-Hora or night-birth/Moon-Hora only to decide whether the system applies. The row says the lord order itself flips (Sun-first by day, Moon-first by night). Which is correct for the platform?",
             note="Existing cite 'BPHS Ch.49' wrong for this corpus (Ch.46)."),
    ont=dict(state="sourced_fact", sup="FACT", claim="Shattrimsha-sama is a 36-year dasha system.",
             corpus=[bp("0517_c02", "42-43", "Their Dasas will be 1, 2, 3, 4, 5, 6, 7, 8 years in that order")],
             inf="36 = 1+2+...+8.", prop=cite_bphs("517", "1", "42-43", "; PG517:C2"), act="recite", q=None,
             note="Current 'BPHS Ch.49 (Kalachakra & Conditional Dashas)': Ch.46 is the defining chapter.")
)

# 11 kalachakra
S["kalachakra"] = dict(
    bds=dict(state="contradicted", sup="CONTRADICTS",
             claim="Kalachakra: 100-yr; sign sequence savya/apasavya from Moon's nakshatra-pada; sign years Aries/Scorpio7 Taurus/Libra16 Gemini/Virgo9 Cancer/Leo21 Cap/Aqu4 Sag/Pis10.",
             corpus=[bp("0527_c01", "84", "Dasa spans of the Sun, Moon, Mars, Mercury, Jupiter, Venus and Saturn in that order"),
                     c("phaladeepika", "phaladeepika_pg0281_c01", "PG281", "3", "5, 21, 7, 9, 10, 16 and 4 are the numbers representing the"),
                     c("phaladeepika", "phaladeepika_pg0281_c01", "PG281", "2", "years assigned to a planet constitute the Dasa-period of the Rasi owned by that planet"),
                     bp("0529_c01", "89", "For the Amsa in Aries 100 Years")],
             inf="Planet years (Sun5 Moon21 Mars7 Mercury9 Jupiter10 Venus16 Saturn4; OCR prints 's' for 5, Phaladeepika prints 5) give each sign the years of its lord, so Leo = Sun = 5, but the row assigns Leo 21 (with Cancer). Every other sign pair in the row agrees. The row's 100-yr total is the Aries-amsa 'Poorna Ayu'; Taurus/Gemini/Cancer amsas are 85/83/86 per sl.89 (the cycle length depends on the Deha amsa).",
             prop=None, act="acharya",
             q="Kalachakra sign-year table: BPHS (Santhanam PG527:C1 sl.84) and Phaladeepika Adh. XXII sl.3 (PG281:C1) give Sun 5, Moon 21, Mars 7, Mercury 9, Jupiter 10, Venus 16, Saturn 4, so Leo (Sun's sign) = 5 years; the row carries 'Cancer/Leo 21'. Confirm Leo = 5.",
             note="Existing cite 'BPHS Ch.49' wrong for this corpus: Ch.49 = Effects of the Kalachakra Dasa; Kalachakra is defined at Ch.46 sl.52-122 (PG521-PG539). Kalachakra is listed as the 100-year dasha; total cycle varies by amsa (100/85/83/86...)."),
    ont=dict(state="sourced_inference", sup="INFERENCE", claim="Kalachakra is a 100-year parashari dasha system.",
             corpus=[bp("0529_c01", "89", "For the Amsa in Aries 100 Years"),
                     bp("0529_c01", "89", "For the Asma in Taurus 85 years")],
             inf="'100-year' is the maximum Poorna Ayu (Aries-type amsa); the text gives different totals for other amsas (85, 83, 86), so 100 is not the universal cycle length.",
             prop=cite_bphs("529", "1", "89"), act="recite", q=None,
             note="Current 'BPHS Ch.49 (Kalachakra & Conditional Dashas)': Kalachakra definition is in Ch.46.")
)

# 12 tara_dasha
S["tara_dasha"] = dict(
    bds=dict(state="contradicted", sup="CONTRADICTS",
             claim="Tara Dasha: 120-yr; reckoned via the 9-tara cycle from Moon's nakshatra; used in nakshatra/tarabala timing.",
             corpus=[bp("0567_c01", "207-249 [sic]", "Tara Dasa which is like Vimsottari Dasa"),
                     bp("0567_c01", "207-249 [sic]", "aprrlied in those casesonlv 'here there are planets in kendras"),
                     bp("0567_c01", "207-249 [sic]", "first Dasa will belong to the strongest amongst them"),
                     bp("0567_c01", None, "Dasa years will be the same as prescribed for Vimsottari Dasa")],
             inf="Supported: 120 yrs (same years as Vimshottari) and the nine tara names (Janma, Sampat, Vipat, Kshema, Pratyak, Sadhana, Naidhana/Vadha, Maitra, Atimaitra in the table). Differs: BPHS starts the Tara Dasa with the strongest planet in a kendra (planets in kendras take the tara names), not from the Moon's nakshatra, and applies it only when planets occupy kendras; 'nakshatra/tarabala timing' use is not stated. Sloka number is OCR'd '207-249' (sic).",
             prop=None, act="acharya",
             q="Tara Dasa (BPHS Santhanam PG567:C1, sl. printed '207-249', OCR for ~207-209): the text starts it with the strongest planet in a kendra and uses it only when planets are in kendras; the row says it is reckoned from the Moon's nakshatra via the 9-tara cycle. Which start rule should the platform carry?",
             note="Existing cite 'BPHS Ch.47' wrong for this corpus (Ch.47 = Effects of Dasas; definition is Ch.46)."),
    ont=dict(state="sourced_inference", sup="INFERENCE", claim="Tara Dasha is a 120-year parashari dasha system.",
             corpus=[bp("0567_c01", None, "Dasa years will be the same as prescribed for Vimsottari Dasa")],
             inf="120 follows from 'same years as Vimsottari' (9 lords, 120-yr total).", prop=cite_bphs("567", "1", "207-249 [sic]"), act="recite", q=None,
             note="Current 'BPHS Ch.47 (Tara Chakra & Nakshatra Dashas)' - title not printed; Ch.47 is Effects of Dasas. 'tara chakra dasha' / 'nakshatra tara' synonyms are not in the held text.")
)

# 13 yogini
S["yogini"] = dict(
    bds=dict(state="sourced_fact", sup="FACT",
             claim="Yogini: Moon1 Sun2 Jupiter3 Mars4 Mercury5 Saturn6 Venus7 Rahu8 (Mangala..Sankata) = 36; short-cycle dasha used for timing and muhurta.",
             corpus=[bp("0564_c01", "195-199", "Mangala, Pingala, Dhanya, Bhramari, Bhadrika, Ulka, Siddha and Sankata"),
                     bp("0564_c01", "195-199", "Moon, the Sun, Jupiter, Mars, Mercury, Saturn, Venus and Rahu, are born from Mangala"),
                     bp("0564_c01", "195-199", "are of 1,2,3,4,5,6,7 and 8 years respectively")],
             inf="Total 36 = 1+..+8. 'especially for timing and muhurta' in conditions_for_use is not stated in the held text (BPHS only says add 3 to the nakshatra number and divide by 8); the descriptive wording is left unsourced.",
             prop=cite_bphs("564", "1", "195-199"), act="recite", q=None,
             note="Existing cite 'BPHS Ch.50' wrong for this corpus (Ch.50 = Effects of Chara etc. Dasas; Yogini is defined in Ch.46)."),
    ont=dict(state="sourced_fact", sup="FACT", claim="Yogini is a 36-year parashari dasha system.",
             corpus=[bp("0564_c01", "195-199", "are of 1,2,3,4,5,6,7 and 8 years respectively")],
             inf="36 = 1+..+8.", prop=cite_bphs("564", "1", "195-199"), act="recite", q=None,
             note="Current 'BPHS Ch.50 (Yogini Dasha)': chapter number wrong for this corpus (Ch.46).")
)

# 14 yogardha_dasha
S["yogardha_dasha"] = dict(
    bds=dict(state="contradicted", sup="CONTRADICTS",
             claim="Yogardha: 108-yr; average (half-sum) of Vimshottari and Ashtottari period-lengths per lord; Ketu carries the Vimshottari value.",
             corpus=[bp("0552_c01", "174", "half of the total of the of Chara and Sthira Dasas"),
                     c("bphs_jaimini", "bphs_jaimini_pg0201_c01", "PG201", "19", "extent of yogardhadasa will be half of the two Dasas combined"),
                     bp("0552_c01", "174", "commence from the sign of the Ascendant or the seventh house whichever is stronger")],
             inf="Both held texts define Yogardha as a RASI dasha: each sign's period is half the sum of its Chara and Sthira years, starting from the stronger of Lagna/7th. Neither mentions an average of Vimshottari and Ashtottari lord-periods, nor a 108-yr cycle. The row's definition, base_unit (nakshatra_lord), method and school (parashari, nakshatra-based) do not match.",
             prop=None, act="acharya",
             q="Yogardha: BPHS (Santhanam PG552:C1 sl.174) and Jaimini (Rao PG201:C1 Adh.2 Pada 4 Su.19) both define it as a rashi dasha with each sign's years = half of (Chara + Sthira years), started from the stronger of Lagna/7th. The row defines it as the average of Vimshottari and Ashtottari lord-periods (108-yr, nakshatra_lord). Which definition should the platform carry?",
             note="Existing cite 'BPHS Ch.48' wrong for this corpus (Yogardha is in Ch.46)."),
    ont=dict(state="contradicted", sup="CONTRADICTS", claim="Yogardha is a 108-year parashari dasha; synonym 'vimshottari ashtottari mean'.",
             corpus=[bp("0552_c01", "174", "half of the total of the of Chara and Sthira Dasas")],
             inf="Same contradiction: held definition is a rashi dasha (half of Chara+Sthira); the '108-year' and 'vimshottari ashtottari mean' synonym are not in the held text.",
             prop=None, act="acharya",
             q="See brahma_dasha_systems yogardha_dasha question (definition: half of Chara+Sthira vs average of Vimshottari and Ashtottari).",
             note="Current 'BPHS Ch.48 (Conditional Nakshatra Dashas)' - wrong chapter for this corpus.")
)

# 15 chara_jaimini
S["chara_jaimini"] = dict(
    bds=dict(state="contradicted", sup="CONTRADICTS",
             claim="Chara (Jaimini): 144-yr; starts from lagna; odd/even direction (movable direct, fixed reverse); years per sign = count to the lord's sign minus 1 (1-12).",
             corpus=[c("bphs_jaimini", "bphs_jaimini_pg0046_c01", "PG46", "28", "found in the 7th house from Mesha. Therefore Mesha Dasa extends for 7 years"),
                     c("bphs_jaimini", "bphs_jaimini_pg0046_c01", "PG46", "28", "Count from Mesha to Simha we get 5. This will be the number of years"),
                     bp("0545_c01", "155-156", "reckoned from the Rasi up to the house in which its lord is posited"),
                     bp("0546_c01", "158-166", "their Dasa will be of 12 years"),
                     bp("0547_c01", "167", "The counting would be in the reverse order if the pada be even")],
             inf="Held Jaimini (Rao) counts the signs from the dasa-sign to its lord's sign as the years with NO subtraction (lord 7th from Mesha = 7 yrs; 5th = 5 yrs), plus a +1 / -1 rule for exaltation / debilitation (PG48) and 12 yrs for both Scorpio/Aquarius lords in own sign; the row says 'minus 1'. Direction: BPHS makes it depend on odd/even pada of the 9th-house sign (sl.167), not movable/fixed as in the row. 144 is not stated as a cycle length (PG55 Su.34 only says 12 signs x 12 = 144 for the sub-period arithmetic); actual cycle = sum of 12 counts, chart-dependent.",
             prop=None, act="acharya",
             q="Chara dasa year-count: Jaimini (Rao PG46:C1 Adh.1 Pada 1 Su.28) counts the signs inclusive from the dasa-sign to its lord (Mesha with Mars in the 7th = 7 yrs); the row says 'count minus 1'. Which counting convention should the platform carry, and is the cycle really a fixed 144 years (the held text gives 144 only as 12 x 12 for sub-periods)? Also BPHS (PG547:C1 sl.167) ties direction to odd/even pada of the 9th-house sign, whereas the row says movable direct / fixed reverse.",
             note="Existing cite 'jaimini_sutram Ch.1': 'jaimini_sutram' is not a corpus text_id (held Jaimini = bphs_jaimini, Rao trans.); the rasi-dasa sutra is Adhyaya 1 Pada 1 Su.28 so 'Ch.1' is right in grain only."),
    ont=dict(state="unsourced_marked", sup="NONE", claim="Chara is a 144-year jaimini dasha system.",
             corpus=[c("bphs_jaimini", "bphs_jaimini_pg0055_c01", "PG55", "34", "All the Rasis put together at 12 each will come up to 144")],
             inf="144 appears only as 12 signs x 12 for the antardasha arithmetic, not as a Chara cycle length; no held text states a 144-year Chara cycle.",
             prop=None, act="mark_unsourced", q=None,
             note="Current 'Jaimini Sutram Ch.1 (Upadesa Sutra - Rashi Dasha systems)': 'Upadesa Sutra' is not a printed title in the held Rao translation.")
)

# 16 sthira_dasha
S["sthira_dasha"] = dict(
    bds=dict(state="contradicted", sup="CONTRADICTS",
             claim="Sthira (Jaimini): 86-yr cycle; sign periods fixed movable 7 / fixed 8 / dual 9.",
             corpus=[c("bphs_jaimini", "bphs_jaimini_pg0182_c01", "PG182", "3", "movable sign Dasa will be 7, the fixed Dasa will be 8 years"),
                     c("bphs_jaimini", "bphs_jaimini_pg0182_c01", "PG182", "3", "the Dasa of the common Rasi will extend to 9 years"),
                     c("bphs_jaimini", "bphs_jaimini_pg0182_c01", "PG182", "4", "The Sthira Dasa commences from the Rasi occupied by Brahma"),
                     bp("0549_c01", "168-169", "are the Dasa spans of the movable, fixed and dual signs")],
             inf="Per-sign years 7/8/9 agree with both texts (the row's own fixed_years also say so). But 12 signs = 4 x (7+8+9) = 96, not 86; the held texts do not state 86, and 86 is inconsistent with the row's own sequence. Likely a transcription slip for 96.",
             prop=None, act="acharya",
             q="Sthira dasa total: the held texts give 7/8/9 yrs for movable/fixed/dual signs (Jaimini Rao PG182:C1 Adh.2 Pada 3 Su.3; BPHS PG548-549 sl.168-169), i.e. 4x(7+8+9) = 96 yrs for twelve signs; the row says total_cycle_years = 86. Confirm 96.",
             note="Existing cite 'jaimini_sutram Ch.1': 'jaimini_sutram' is not a corpus text_id (held = bphs_jaimini); the Sthira sutra is Adhyaya 2 Pada 3 Su.3-4, not Ch.1."),
    ont=dict(state="contradicted", sup="CONTRADICTS", claim="Sthira is an 86-year jaimini dasha system.",
             corpus=[c("bphs_jaimini", "bphs_jaimini_pg0182_c01", "PG182", "3", "movable sign Dasa will be 7, the fixed Dasa will be 8 years")],
             inf="Same as the brahma_dasha_systems row: 4x(7+8+9) = 96, not 86.", prop=None, act="acharya",
             q="See brahma_dasha_systems sthira_dasha question (86 vs 96).",
             note="Current 'Jaimini Sutram Ch.1 (Upadesa Sutra - Rashi Dasha systems)': Sthira is in Adhyaya 2 Pada 3.")
)

# 17 niryana_shoola
S["niryana_shoola"] = dict(
    bds=dict(state="contradicted", sup="CONTRADICTS",
             claim="Niryana Shoola (Jaimini): 108-yr; trikona-based, longevity/maraka timing; fixed_years movable7 / fixed8 / dual9.",
             corpus=[bp("0557_c01", "181-182", "The Dasa years in this system are as adopted for the Sthira Dasa"),
                     bp("0557_c01", "181-182", "des-igned the'Shoola Dasa for determining the"),
                     c("bphs_jaimini", "bphs_jaimini_pg0200_c01", "PG200", "16", "Shoola Dasas are marked as death inflicting")],
             inf="Years 7/8/9 (as Sthira) and the death/maraka purpose agree; BPHS starts it from the stronger of the 2nd/8th, Jaimini takes trikona (1,5,9) shoola rasis. But 12 signs at 7/8/9 = 96, not 108 (108 = 12 x 9, the Navamsa-dasa total, Jaimini Adh.2 Pada 3 Su.1 PG181).",
             prop=None, act="acharya",
             q="Niryana Shoola total: both texts give the Sthira year table (7/8/9; BPHS PG557:C1 sl.181-182) for the shoola dasa, i.e. 96 yrs for twelve signs, and 108 is the Navamsa-dasa total (12 x 9); the row has total_cycle_years = 108 together with fixed_years 7/8/9. Which total is intended?",
             note="Existing cite 'jaimini_sutram Ch.1': not a corpus text_id; Shoola dasa discussion is Adhyaya 2 Pada 2-4 (and BPHS Ch.46 sl.181-182)."),
    ont=dict(state="contradicted", sup="CONTRADICTS", claim="Niryana Shoola is a 108-year jaimini dasha system.",
             corpus=[bp("0557_c01", "181-182", "The Dasa years in this system are as adopted for the Sthira Dasa")],
             inf="Same as brahma_dasha_systems row: 96 by the Sthira table, not 108.", prop=None, act="acharya",
             q="See brahma_dasha_systems niryana_shoola question (96 vs 108).",
             note="Current 'Jaimini Sutram Ch.1 (Upadesa Sutra - Rashi Dasha systems)': wrong grain (Adhyaya 2).")
)

# 18 brahma_dasha
S["brahma_dasha"] = dict(
    bds=dict(state="sourced_inference", sup="INFERENCE",
             claim="Brahma Dasha (Jaimini): 120-yr; rashi dasha reckoned from the Brahma graha; longevity/maraka analysis.",
             corpus=[c("bphs_jaimini", "bphs_jaimini_pg0190_c01", "PG190", "25", "Dasas or periods commence from the sign occupied by the Brahma"),
                     c("bphs_jaimini", "bphs_jaimini_pg0190_c01", "PG190", "25", "that number will be the extent in years of that Dasa"),
                     c("bphs_jaimini", "bphs_jaimini_pg0191_c01", "PG191", "26", "in even signs the Dasas commence from the 7th Rasi from the sign")],
             inf="Identifies the row's 'Brahma Dasha' with the Jaimini Adh.2 Pada 3 Su.25-26 dasa that starts from the Brahma sign (the held text does not name it 'Brahma Dasha'). The 120-yr total_cycle_years is NOT stated: the text gives per-sign years = house-number of the 6th lord, so the cycle is chart-dependent.",
             prop="Jaimini Sutras (Rao), Adhyaya 2 Pada 3, Su. 25-26 as printed - bphs_jaimini:PG190:C1 and PG191:C1 (Suryanarain Rao trans. 1949); total_cycle_years 120 unsourced",
             act="mark_unsourced",
             q="Brahma Dasha: the held Jaimini text (Rao PG190:C1 Su.25) starts the dasas from the Brahma sign with each sign's years = the house-number of the lord of the 6th from it, so no fixed 120-year cycle is stated. What is the source of total_cycle_years = 120 for this system?",
             note="Existing cite 'jaimini_sutram Ch.1': not a corpus text_id; Brahma dasa is at Adhyaya 2 Pada 3."),
    ont=dict(state="unsourced_marked", sup="NONE", claim="Brahma Dasha is a 120-year jaimini dasha system.",
             corpus=[c("bphs_jaimini", "bphs_jaimini_pg0190_c01", "PG190", "25", "that number will be the extent in years of that Dasa")],
             inf="No held text states a 120-year Brahma Dasha cycle (per-sign years are chart-dependent house numbers).", prop=None, act="mark_unsourced", q=None,
             note="Current 'Jaimini Sutram Ch.1 (Upadesa Sutra - Rashi Dasha systems)': wrong grain (Adhyaya 2 Pada 3).")
)

# 19 narayana
S["narayana"] = dict(
    bds=dict(state="unsourced_marked", sup="NONE",
             claim="Narayana Dasha: 144-yr; starts from Lagna if odd else 7th; always zodiacal; years = count to lord's sign (1-12).",
             corpus=[], inf=None, prop=None, act="mark_unsourced",
             q="Narayana Dasha is not named in any held text (searched all 15; 'Narayana' hits are the deity or personal names only). What source supports the start rule (Lagna if odd else 7th), always-zodiacal progression and the 144-year total?",
             note="Existing cite 'jaimini_sutram Ch.1' does not resolve: not a corpus text_id and the held Rao Jaimini never names a Narayana dasa (its Navamsa dasa, Adh.2 Pada 3, uses a different start rule). The row's own conditions text records the variant-commentary caveat."),
    ont=dict(state="unsourced_marked", sup="NONE", claim="Narayana is a 144-year jaimini dasha system.",
             corpus=[], inf=None, prop=None, act="mark_unsourced", q=None,
             note="Not in the held corpus; same as brahma_dasha_systems row.")
)

# 20 kp
S["kp"] = dict(
    bds=dict(state="text_not_held", sup="NONE",
             claim="KP sub-period system: 120-yr proportional subdivision of the Vimshottari windows (Ketu7...Mercury17); Placidus cusps; judgment method independent.",
             corpus=[bp("0499_c01", "12-15", "Sun, the Moon, Mars, Rahu, Jupiter. Saturn, Mercury, Ketu and Venus in that order"),
                     bp("0499_c01", "15", "Meicury. Ketu and Venus are 6,lO, 7,"),
                     bp("0499_c02", "15", "18, 16, 19,l'1,7 and20 in thai order")],
             inf="The BPHS part of the citation (Vimshottari constants, TIER-I) is verified: lord order and years match. The KP-specific conventions (sub-lord division, Placidus cusps, significator method) cite K. S. Krishnamurti, KP Reader I-III, which the corpus does not hold (the row itself says so, text_id null).",
             prop=None, act="none", q=None,
             note="Row's second citation already honestly marks the KP Reader as not ingested."),
    ont=dict(state="text_not_held", sup="NONE", claim="KP is a 120-year kp dasha system (BPHS Ch.46 constants; KP Reader).",
             corpus=[bp("0499_c01", "15", "Meicury. Ketu and Venus are 6,lO, 7,"),
                     bp("0499_c02", "15", "18, 16, 19,l'1,7 and20 in thai order")],
             inf="Constants verified at BPHS Ch.46; KP Reader not held.", prop=None, act="none", q=None,
             note="Citation already states 'KP conventions not ingested'.")
)

# ---- assemble --------------------------------------------------------------
ledger = []


def mk(table, key, row, cur, claim_default=None, rowkey_name="canonical_id"):
    d = {
        "asset": ASSET, "table": table,
        "row_key": ({rowkey_name: key} if table != "brahma_ontology" else {"entity_class": "dasha_system", "canonical_id": key}),
        "row_count": 1,
        "claim": row["claim"][:200],
        "current_citation": cur,
        "state": row["state"],
        "support_class": row["sup"],
        "corpus": row["corpus"],
        "inference_step": row["inf"],
        "proposed_citation": row["prop"],
        "proposed_action": row["act"],
        "acharya_question": row["q"],
        "note": row.get("note"),
    }
    return d


for key in sorted(S):
    ledger.append(mk("brahma_dasha_systems", key, S[key]["bds"], bds_cit[key]))
for key in sorted(S):
    ledger.append(mk("reference_dasha_systems", key,
                     dict(claim=f"Identity row: canonical_id/name_en/school = {ref_rows[key][0]} / {ref_rows[key][1]}; platform vocabulary, no classical assertion.",
                          state="not_a_classical_claim", sup="NONE", corpus=[], inf=None, prop=None, act="none", q=None,
                          note="reference_dasha_systems has only (canonical_id, name_en, school) - no citation/source column. 'school' is a platform classification (not a dated textual claim); the classical content is in the brahma_dasha_systems row of the same id."),
                     "no citation/source column in reference_dasha_systems"))
for key in sorted(S):
    ledger.append(mk("brahma_ontology", key, S[key]["ont"], ont_cit[key]))

json.dump(ledger, open(OUT, "w"), indent=1, ensure_ascii=False)
cnt = collections.Counter((d["table"], d["state"]) for d in ledger)
print(len(ledger))
for k in sorted(cnt):
    print(k, cnt[k])
print(collections.Counter(d["state"] for d in ledger))
# sanity: quotes <=15 words
for d in ledger:
    for q in d["corpus"]:
        n = len(q["quote"].split())
        if n > 16:
            print("LONG QUOTE", d["table"], d["row_key"], n, q["quote"])
