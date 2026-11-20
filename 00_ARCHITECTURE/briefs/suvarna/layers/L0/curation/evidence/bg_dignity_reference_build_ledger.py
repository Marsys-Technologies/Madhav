#!/usr/bin/env python3
# Builds ledger.json for asset bg_dignity_reference (read-only research output).
import json, subprocess, collections

ASSET = "bg_dignity_reference"
RQ = "/Users/Dev/suvarna-evidence/TrackI/ifl0/rq.sh"
OUT = "/private/tmp/claude-504/scratch/curation/bg_dignity_reference/"
L = []


def rq(sql):
    out = subprocess.run([RQ, sql], capture_output=True, text=True).stdout.strip().splitlines()
    hdr = out[0].split("|")
    rows = []
    for ln in out[1:]:
        if ln.startswith("(") and ln.endswith("rows)") or ln.startswith("(1 row"):
            continue
        rows.append(dict(zip(hdr, ln.split("|", len(hdr) - 1))))
    return rows


def c(text_id, chunk_id, page, sloka, quote):
    return {"text_id": text_id, "chunk_id": chunk_id, "page": page, "sloka_printed": sloka, "quote": quote}


def add(table, key, claim, cur, state, cls, corpus, inf, prop, act, q, note=None, partial=None):
    o = {
        "asset": ASSET, "table": table, "row_key": key, "row_count": 1, "claim": claim,
        "current_citation": cur, "state": state, "support_class": cls, "corpus": corpus,
        "inference_step": inf, "proposed_citation": prop, "proposed_action": act,
        "acharya_question": q,
    }
    if note:
        o["note"] = note
    if partial:
        o["unsourced_fields"] = partial
    L.append(o)


# ------------------------------------------------------------------ chunk shorthands
B37A = c("bphs", "bphs_pg0037_c01", "PG37", "49-50", "49-50. EXALTATION AND DEBILITATION")
B37B = c("bphs", "bphs_pg0037_c02", "PG37", "49-50", "Aries [OCR 'iries'], Taurus, Capricorn, Virgo, Cancer, Pisces and Libra")
B38_DEG = c("bphs", "bphs_pg0038_c01", "PG38", "49-50", "deepest exaltation degrees are respectively 10,3, 2g, 15, 5, 27 1nd 20 in those signs")
B38_DEB = c("bphs", "bphs_pg0038_c01", "PG38", "49-50", "in the seventh sign from the said exaltation sign each planet has its own debilitation")
B38_SUN = c("bphs", "bphs_pg0038_c01", "PG38", "51-54", "In Leo the first 20 degrees are the Sun's Moolatrikona")
B38_MARS = c("bphs", "bphs_pg0038_c01", "PG38", "51-54", "the first 12 dcgrees in Aries as Moolatrikona [planet name lost to OCR]")
B38_MER = c("bphs", "bphs_pg0038_c02", "PG38", "51-54", "first 15 degrces are exaltation zone, the next 5 degrees Moolatrikona")
B38_JUP = c("bphs", "bphs_pg0038_c02", "PG38", "51-54", "first one third of Sagittarius is the Moolatrikona of Jupiter")
B38_VEN = c("bphs", "bphs_pg0038_c02", "PG38", "51-54", "Venus divides Libra into two halves keeping thc first as Moolatrikona")
B38_SAT = c("bphs", "bphs_pg0038_c02", "PG38", "51-54", "Saturn's arrangements are same in Aquarius as the Sun has in Leo")
PD40 = c("phaladeepika", "phaladeepika_pg0040_c01", "PG40", "6", "Mesha, Vrishabha, Makara, Kanya, Karkataka, Meena and Tula are the exaltation signs")
PD40F = c("phaladeepika", "phaladeepika_pg0040_c01", "PG40", "6", "their signs of 'fall' being the 7th from their exaltation ones")
PD40L = c("phaladeepika", "phaladeepika_pg0040_c01", "PG40", "6", "Mars, Venus, Mercury, the Moon, the Sun, Mercury, Venus, Mars, Jupiter, Saturn, Saturn and Jupiter")
PD41D = c("phaladeepika", "phaladeepika_pg0041_c01", "PG41", "6", "the 28th, the 15th, the 5th, the 27th and the 20th degrees of the several signs")
PD41M = c("phaladeepika", "phaladeepika_pg0041_c01", "PG41", "7", "Simha, Vrishbha, Mesha, Kanya, Dhanus, Tula and Kumbha are the Moolatrikona signs")
PD41MD = c("phaladeepika", "phaladeepika_pg0041_c01", "PG41", "7", "The first 20 degrees of Simha, the last 27 degrees of Vrishabha")
PD41MER = c("phaladeepika", "phaladeepika_pg0041_c01", "PG41", "7", "5 degrees following the highest exaltation degree of Mercury in Kanya (i.e., 16 to 20)")
PD41R = c("phaladeepika", "phaladeepika_pg0041_c01", "PG41", "7", "the first five degrees in Tula and the first 20 degrees of Kumbha")
PD41AR = c("phaladeepika", "phaladeepika_pg0041_c01", "PG41", "7", "the first 12 degrees of Mesha")
UK26 = c("uttara_kalamrita", "uttara_kalamrita_pg0026_c01", "PG26", None, "lords of the twelve signs from Mesha onwards are Mars. Venus. Mercury, Moon. Sun, Mercury. Venus, Mars, Jupiter, Saturn, Saturn and Jupiter")
UK28 = c("uttara_kalamrita", "uttara_kalamrita_pg0028_c01", "PG28", None, "The Mula trikona degrees are Sun 0 to 20, Moon 4 to 20")
UK27 = c("uttara_kalamrita", "uttara_kalamrita_pg0027_c01", "PG27", None, "Simha is the mulatrikona of the Sun; Vrishabha for the Moon, Mesha for Kuja")
HS18 = c("hora_sara", "hora_sara_pg0018_c01", "PG18", "5-7", "three degrees of Taurus are the Moon's exaltation portion, while the rest is her Moolatrikona")
HS18V = c("hora_sara", "hora_sara_pg0018_c01", "PG18", "6", "For Venus upto 20 degrees in Libra are her Moolatrikona")
HS19J = c("hora_sara", "hora_sara_pg0019_c01", "PG19", "8", "For Jupiter, the first five degrees in Sagittarius are Moolatrikona")
HS19M = c("hora_sara", "hora_sara_pg0019_c01", "PG19", "8", "It is Moolatrikona upto twelve degrees in Aries for Mars")
HS18MER = c("hora_sara", "hora_sara_pg0018_c01", "PG18", "5", "from 15 1' to 20 is Moolatrikona for Mercury")
SV17 = c("saravali", "saravali_pg0017_c02", "PG17", "21-24", "exaltation zone is the first 3 of Taurus, with the remaining portion being her Mlatrikona")
SV17J = c("saravali", "saravali_pg0017_c02", "PG17", "21-24", "In Sagittarius first 10 is Jupiters Mlatrikona, with the rest being own House")
SV17V = c("saravali", "saravali_pg0017_c02", "PG17", "21-24", "The first 5 in Libra [PG18:] is Mlatrikona of Venus")

DIG = "bg_dignity_reference"
CIT3 = "BPHS Ch.3"

# ------------------------------------------------------------------ 1. bg_dignity_reference (9 rows)
base_prop = lambda extra: ("BPHS Chapter 3, Sloka 49-50 (exaltation, debilitation) and 51-54 (Moolatrikona, own) as printed — "
                           "bphs:PG37:C2, bphs:PG38:C1, bphs:PG38:C2 (Santhanam trans.)" + extra)

add(DIG, {"id": 1, "graha": "Sun"},
    "Sun: exalted Aries 10, debilitated Libra 10, Moolatrikona Leo 0-20, own Leo.", CIT3, "sourced_fact", "FACT",
    [B37A, B37B, B38_DEG, B38_DEB, B38_SUN, PD40L, PD41M, PD41MD, UK27],
    None, base_prop("; own sign Leo: Phaladeepika Adh. I, Sloka 6 — phaladeepika:PG40:C1 (Sastri trans. 1950)"), "recite", None,
    note="Debilitation sign/degree obtained by counting the seventh sign from the printed exaltation sign (rule printed in the same sloka; PD Sl.6 says the same). BPHS own-sign statement not located by me; PD Sl.6 and UK PG26 state sign lordship.")

add(DIG, {"id": 2, "graha": "Moon"},
    "Moon: exalted Taurus 3, debilitated Scorpio 3, Moolatrikona Taurus 4-30, own Cancer.", CIT3, "sourced_fact", "FACT",
    [B37B, B38_DEG, B38_DEB, PD41MD, HS18, SV17, UK28],
    None,
    base_prop("; Moolatrikona 4-30: Phaladeepika Adh. I, Sloka 7 — phaladeepika:PG41:C1 (Sastri trans. 1950)"), "recite",
    "Uttara Kalamrita (Sastri) p.28 prints the Moon's Moolatrikona as '4 to 20' degrees; Phaladeepika Sl.7 ('last 27 degrees of Vrishabha'), Hora Sara Sl.6 and Saravali Sl.21-24 give 3-30 (Moolatrikona 4-30). Please confirm 4-30 as canonical and that the UK figure is a misprint.",
    note="BPHS PG38:C1 Moon sentence of Sl.51-54 is lost to OCR (only Sun and the Aries-12 sentences survive), so the Moolatrikona range is sourced to PD/HS/Saravali, not the cited BPHS chunk.")

add(DIG, {"id": 3, "graha": "Mars"},
    "Mars: exalted Capricorn 28, debilitated Cancer 28, Moolatrikona Aries 0-12, own Aries/Scorpio.", CIT3, "sourced_fact", "FACT",
    [B37B, B38_DEG, B38_DEB, B38_MARS, PD41AR, HS19M, PD40L],
    None, base_prop("; Moolatrikona named for Mars: Phaladeepika Adh. I, Sloka 7 — phaladeepika:PG41:C1 (Sastri trans. 1950)"), "recite", None,
    note="BPHS Sl.51-54 Mars sentence survives without the planet name (OCR); PD Sl.7 and Hora Sara Sl.8 name Mars explicitly.")

add(DIG, {"id": 4, "graha": "Mercury"},
    "Mercury: exalted Virgo 15, debilitated Pisces 15, Moolatrikona Virgo 16-20, own Gemini/Virgo.", CIT3, "sourced_fact", "FACT",
    [B37B, B38_DEG, B38_DEB, B38_MER, PD41MER, HS18MER, UK28],
    None, base_prop("; '16 to 20': Phaladeepika Adh. I, Sloka 7 — phaladeepika:PG41:C1 (Sastri trans. 1950)"), "recite", None,
    note="BPHS says first 15 degrees exaltation, next 5 Moolatrikona (15-20 as longitude); PD/UK print 16-20 (ordinal degrees). DB 16 = ordinal convention, consistent.")

add(DIG, {"id": 5, "graha": "Jupiter"},
    "Jupiter: exalted Cancer 5, debilitated Capricorn 5, Moolatrikona Sagittarius 0-10, own Sagittarius/Pisces.", CIT3, "sourced_fact", "FACT",
    [B37B, B38_DEG, B38_DEB, B38_JUP, PD41R, SV17J, HS19J],
    None, base_prop("; Moolatrikona 0-10 also Phaladeepika Adh. I, Sloka 7 — phaladeepika:PG41:C1 (Sastri trans. 1950)"), "recite",
    "Hora Sara (Santhanam) Sl.8 prints Jupiter's Moolatrikona as the first FIVE degrees of Sagittarius, whereas BPHS ('first one third'), Phaladeepika, Saravali and Uttara Kalamrita give the first 10. Is the Hora Sara figure a variant tradition or a misprint?",
    note="DB value (0-10) agrees with BPHS, PD, Saravali, UK; Hora Sara differs.")

add(DIG, {"id": 6, "graha": "Venus"},
    "Venus: exalted Pisces 27, debilitated Virgo 27, Moolatrikona Libra 0-15, own Taurus/Libra.", CIT3, "sourced_fact", "FACT",
    [B37B, B38_DEG, B38_DEB, B38_VEN, UK28, PD41R, SV17V, HS18V],
    None, base_prop(""), "recite",
    "The held texts give four different Moolatrikona extents for Venus in Libra: BPHS Sl.51-54 'first half' (0-15) and Uttara Kalamrita p.28 (0-15, OCR 'ISO'); Phaladeepika Sl.7 and Saravali Sl.21-24 'first five degrees'; Hora Sara Sl.6 'upto 20 degrees'. The table stores 0-15 (BPHS). Which extent is canonical, and should the others be recorded as variant traditions?",
    note="DB 0-15 agrees with BPHS (the cited text) and UK; PD/Saravali (5) and Hora Sara (20) differ. Not a contradiction of the cited text.")

add(DIG, {"id": 7, "graha": "Saturn"},
    "Saturn: exalted Libra 20, debilitated Aries 20, Moolatrikona Aquarius 0-20, own Capricorn/Aquarius.", CIT3, "sourced_fact", "FACT",
    [B37B, B38_DEG, B38_DEB, B38_SAT, PD41R, UK28],
    None, base_prop(""), "recite", None)

NODE_Q = ("BPHS Ch.47 Sl.34-39 states Rahu: exalted Taurus, debilitated Scorpio, Moolatrikona Gemini, own Aquarius (some: Virgo); "
          "Ketu: exalted Scorpio, Moolatrikona Sagittarius, own Scorpio (some: Pisces); Hora Sara p.19 lists further variants (Gemini/Sagittarius exaltation in Syama Sangraham). "
          "The rows store own_signs={} and no Moolatrikona, and label Gemini/Sagittarius as a 'Kerala school' view and an 'Exclusionist' view that no held text names. "
          "Should own_signs/Moolatrikona be populated from BPHS Ch.47, and which variant labels may stay?")
add(DIG, {"id": 8, "graha": "Rahu"},
    "Rahu: exalted Taurus, debilitated Scorpio; no own signs/Moolatrikona stored; variants Gemini (Kerala), exclusionist.",
    "BPHS Ch.3 (Santanam); Phaladeepika Ch.1; Saravali — Parashari consensus: Taurus", "sourced_fact", "FACT",
    [c("bphs", "bphs_pg0573_c02", "PG573", "34-39", "The sign of exaltation of Rahu is Taurus."),
     c("bphs", "bphs_pg0574_c02", "PG574", "34-39", "sign of debilitation (Scorpio), there will be loss of position"),
     c("bphs", "bphs_pg0574_c01", "PG574", "34-39", "The own signs of Rahu and Ketu are Aquarius and Scorpio in that order"),
     c("bphs", "bphs_pg0574_c01", "PG574", "34-39", "The Moola tikonas of Rahu and Ketu are Gemini and Sagittarius respectively"),
     c("bphs", "bphs_pg0038_c01", "PG38", None, "As for the exaltations and debilitation of the nodes, there are different views"),
     c("hora_sara", "hora_sara_pg0019_c01", "PG19", None, "Syama Sangraham says that Gemini and Sagittarius are exaltation and Neecha for Rahu")],
    None,
    "BPHS Chapter 47, Sloka 34-39 as printed — bphs:PG573:C2, bphs:PG574:C1, bphs:PG574:C2 (Santhanam trans.); variants: Hora Sara p.19 — hora_sara:PG19:C1 (Santhanam trans.)",
    "recite", NODE_Q,
    note="The existing citation is wrong at chapter grain: BPHS Ch.3 (PG38) only says the nodes have 'different views'; the statement is in BPHS Ch.47. Neither Phaladeepika Adh. I Sl.6-7 nor Saravali Ch.3 Sl.21-24 mention the nodes (searched). The 'Kerala school / Prashna Marga lineage' and 'Exclusionist' labels have no held source (Prashna Marga not held). DB own_signs={} / Moolatrikona NULL omits what BPHS Ch.47 states (omission, not contradiction).")
add(DIG, {"id": 9, "graha": "Ketu"},
    "Ketu: exalted Scorpio, debilitated Taurus; no own signs/Moolatrikona stored; variants Sagittarius (Kerala), exclusionist.",
    "BPHS Ch.3 (Santanam); Phaladeepika Ch.1; Saravali — reverse of Rahu", "sourced_fact", "FACT",
    [c("bphs", "bphs_pg0574_c01", "PG574", "34-39", "sign of exaltation of Ketu is Scorpio."),
     c("hora_sara", "hora_sara_pg0019_c01", "PG19", None, "Sarvartha Chintamani gives ... Scorpio-Taurus as exaltation and debilitation for Ketu"),
     c("bphs", "bphs_pg0574_c01", "PG574", "34-39", "The own signs of Rahu and Ketu are Aquarius and Scorpio in that order"),
     c("hora_sara", "hora_sara_pg0019_c01", "PG19", None, "Syama Sangraham says ... the reverse is true for Ketu")],
    None,
    "BPHS Chapter 47, Sloka 34-39 as printed — bphs:PG574:C1 (Santhanam trans.); debilitation (Taurus): Hora Sara p.19 — hora_sara:PG19:C1 (Santhanam trans.)",
    "recite", NODE_Q,
    note="Ketu's debilitation sign is not printed in the surviving BPHS text; it is stated only second-hand by the Hora Sara translator's note (reporting Sarvartha Chintamani) and by the exaltation-opposite rule. Same citation-chapter error as Rahu row.")

# ------------------------------------------------------------------ 2. bg_graha_naisargika_friendship (72 rows)
FT = "bg_graha_naisargika_friendship"
rows = rq("select id, graha, other_graha, relation, classical_citation from bg_graha_naisargika_friendship order by id")
assert len(rows) == 72, len(rows)
P7 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
UK_F = {"Sun": "Moon, Mars and Jupiter are the Sun's friends.", "Moon": "Moon's friends are the Sun and Mercury.",
        "Mars": "Sun. Moon and Jupiter are the friends of Mars.", "Mercury": "Sun and Venus are the friends of Mercury.",
        "Jupiter": "Sun. Moon and Mars are the friends of Jupiter.", "Venus": "The friends of Venus are Mercury and Saturn.",
        "Saturn": "The friends of Saturn are Mercury and Venus."}
UK_E = {"Sun": "Saturn and Venus are the enemies of the Sun.", "Moon": "The Moon has no enemies.",
        "Mars": "The enemy of Mars is Mercury", "Mercury": "that of Mercury is the Moon.",
        "Jupiter": "Jupiter's enemies are Mercury and Venus.", "Venus": "The foes of Venus are the Sun and Moon.",
        "Saturn": "Saturn's enemies are the Sun, Moon and Mars."}
UK_N = "The remaining ones in each case are neutrals."
BP_RULE = c("bphs", "bphs_pg0039_c01", "PG39", "55", "the 2nd,4th,5th,8th,9th and l2th lords are its friends. The rest ... are its enemies")
BP_TAB = c("bphs", "bphs_pg0039_c02", "PG39", "55", "Friends Enemies Dquals [table; OCR scrambled]")
BP_MOON = c("bphs", "bphs_pg0040_c01", "PG40", "55", "Sun and Mercury are Moon's friends while others are her neutrals")
PROP_F7 = ("BPHS Chapter 3, Sloka 55 (natural relationships; table at PG39:C2, Moon note PG40:C1) as printed — bphs:PG39:C1 (Santhanam trans.); "
           "corroborated Uttara Kalamrita Ch. II p.28 — uttara_kalamrita:PG26:C1 (Sastri trans.)")
NOTE_F7 = ("Existing 'BPHS Ch.27' is the Shadbala chapter in this edition (bphs:PG284:C1 header 'Chapter 27'); natural relationships are in BPHS Ch.3 Sl.55. "
           "All 42 seven-graha rows were compared programmatically with the explicit UK list (0 mismatches) and with the BPHS Sl.55 rule applied to the Moolatrikona signs (0 mismatches).")

BPHS_NODE = {"Rahu": {"Sun": "enemy", "Moon": "enemy", "Mars": "enemy", "Jupiter": "friend", "Venus": "friend", "Saturn": "friend", "Mercury": "neutral"},
             "Ketu": {"Sun": "enemy", "Moon": "enemy", "Mars": "friend", "Venus": "friend", "Saturn": "friend", "Mercury": "neutral", "Jupiter": "neutral"}}
# Sarvartha Chintamani Stanza 108 friends (translator's note adds Sun/Moon enemies; Mercury/Mars 'neutral at least')
SC_F = {"Rahu": {"Venus", "Jupiter", "Saturn"}, "Ketu": {"Venus", "Saturn", "Jupiter"}}
def BP_NODE_Q(n, o):
    if n == "Rahu":
        q = {"Sun": "The Sun, Moon and Mars are his enemies", "Moon": "The Sun, Moon and Mars are his enemies", "Mars": "The Sun, Moon and Mars are his enemies",
             "Jupiter": "Jupiter, Venus and Saturn are his friends", "Venus": "Jupiter, Venus and Saturn are his friends", "Saturn": "Jupiter, Venus and Saturn are his friends",
             "Mercury": "Mercury is his ncutral"}[o]
    else:
        q = {"Sun": "The luminaries are his enemics", "Moon": "The luminaries are his enemics", "Mars": "Mars' Venus and Saturn are his friends",
             "Venus": "Mars' Venus and Saturn are his friends", "Saturn": "Mars' Venus and Saturn are his friends",
             "Mercury": "while Mercury and Jupiter are his neutralS", "Jupiter": "while Mercury and Jupiter are his neutralS"}[o]
    return c("bphs", "bphs_pg0040_c01", "PG40", "55 (notes)", q)
SC127 = c("sarvartha_chintamani", "sarvartha_chintamani_pg0001_c127", "PG1:C127", "108",
          "Rahu has Sukra, Guru and Sani as friends. Keihu has Sukra, Sani and Guru")
SC128 = c("sarvartha_chintamani", "sarvartha_chintamani_pg0001_c128", "PG1:C128", "108 (translator note)",
          "Ravi and Chandra are the declared enemies of Rahu and Kethu.")
UKTOC = c("uttara_kalamrita", "uttara_kalamrita_pg0009_c01", "PG9", None,
          "Exaltation, debilitation, mulatrikona and own signs of Rahu and Ketu. Their friends and others 151")
NODE_Q2 = ("Held texts disagree with each other and with the table on how Rahu/Ketu regard the planets: BPHS (Santhanam notes under Sl.55, PG40) says Rahu: Sun/Moon/Mars enemies, Jupiter/Venus/Saturn friends, Mercury neutral; "
           "Ketu: Sun and Moon enemies, Mars/Venus/Saturn friends, Mercury/Jupiter neutral; Sarvartha Chintamani Stanza 108 lists Venus, Jupiter, Saturn as friends of both. "
           "The table has Rahu->Mercury friend, Rahu->Mars neutral, Rahu->Jupiter neutral, Ketu->Sun neutral, Ketu->Moon neutral. The cited Uttara Kalamrita passage (contents p.151) is not in the held pages. "
           "Which source and which values are canonical for the node-to-graha direction, and are the 14 graha-to-node rows meant to mirror the node-to-graha rows?")

for r in rows:
    i, g, o, rel, cit = int(r["id"]), r["graha"], r["other_graha"], r["relation"], r["classical_citation"]
    key = {"id": i, "graha": g, "other_graha": o}
    claim = f"{g} regards {o} as natural {rel}."
    if g in P7 and o in P7:
        if rel == "friend":
            q = UK_F[g]
        elif rel == "enemy":
            q = UK_E[g]
        else:
            q = UK_N
        corp = [c("uttara_kalamrita", "uttara_kalamrita_pg0026_c01", "PG26", None, q), BP_RULE, BP_TAB]
        if g == "Moon":
            corp.append(BP_MOON)
        add(FT, key, claim, cit, "sourced_fact", "FACT", corp, None, PROP_F7, "recite", None, note=NOTE_F7)
    elif g in P7 and o in ("Rahu", "Ketu"):
        recip = BPHS_NODE[o][g]
        agree = "matches" if recip == rel else "differs from"
        add(FT, key, claim, cit, "unsourced_marked", "NONE",
            [BP_NODE_Q(o, g)], None, None, "mark_unsourced",
            NODE_Q2 if i in (7, 15) else None,
            note=(f"No held text states how {g} regards {o}. BPHS PG40 (notes under Sl.55) states only the node's own view ({o}->{g} = {recip}); "
                  f"the stored value '{rel}' {agree} that reciprocal reading. Reciprocity is not assumed in the 7x7 table (it is asymmetric, e.g. Mars friend of Moon, Moon neutral to Mars), so no inference is drawn. "
                  "Existing 'BPHS Ch.27' is the Shadbala chapter, not a relationship table."))
    elif g in ("Rahu", "Ketu") and o in P7:
        b = BPHS_NODE[g][o]
        scf = o in SC_F[g]
        sc_enemy = o in ("Sun", "Moon")
        corp = [BP_NODE_Q(g, o), SC127, SC128, UKTOC]
        if rel == b:
            add(FT, key, claim, cit, "sourced_fact", "FACT", corp[:2] + [UKTOC], None,
                f"BPHS Chapter 3, notes under Sloka 55 (PG40) — bphs:PG40:C1 (Santhanam trans.)" + (
                    "; Sarvartha Chintamani, Stanza 108 as printed — sarvartha_chintamani:PG1:C127 (Suryanarayana Row trans., 1899)" if (scf and rel == "friend") else ""),
                "recite", None,
                note=(f"DB '{rel}' = BPHS PG40 ({g}: {o} {b})." +
                      (f" Sarvartha Chintamani Stanza 108 differs (lists {o} as friend of {g})." if (rel != "friend" and scf) else "") +
                      " Existing citation UK Ch.4 could not be verified: Uttara Kalamrita's own passage (contents entry 'Their friends and others', p.151) falls in pages 142-155 which are absent from the held corpus."))
        else:
            note = (f"DB '{rel}' vs BPHS PG40 '{b}'" +
                    (f"; Sarvartha Chintamani Stanza 108 lists {o} as a friend of {g}" if scf else "") +
                    ("; Sarvartha Chintamani translator's note says Sun/Moon are declared enemies of both nodes" if sc_enemy else "") +
                    ("; Sarvartha Chintamani translator's note says Mercury/Mars 'may safely be classed as neutrals at least' (an inference, not a stanza)" if o in ("Mercury", "Mars") else "") +
                    ". No held text agrees with the stored value. The cited UK passage (contents p.151) is not in the held pages.")
            add(FT, key, claim, cit, "contradicted", "CONTRADICTS", corp, None, None, "acharya", NODE_Q2, note=note)
    else:  # Rahu<->Ketu
        add(FT, key, claim, cit, "unsourced_marked", "NONE",
            [SC127, UKTOC, c("sarvartha_chintamani", "sarvartha_chintamani_pg0001_c129", "PG1:C129", None, "Rahu and Kethu form one party")],
            None, None, "mark_unsourced", None,
            note="No held text states a Rahu-Ketu relationship. Sarvartha Chintamani's translator's note groups them as 'one party' (in tension with 'enemy', but not a statement of their mutual relation). UK passage not in held pages.")

# ------------------------------------------------------------------ 3. bg_avastha_schemes (35 rows)
AT = "bg_avastha_schemes"
arows = rq("select id, scheme_name, state_name, state_order, classical_citation from bg_avastha_schemes order by id")
assert len(arows) == 35
cit = {int(r["id"]): r["classical_citation"] for r in arows}
nm = {int(r["id"]): (r["scheme_name"], r["state_name"], int(r["state_order"])) for r in arows}

BA = {  # baladi
    1: ("Infant state (Baalavastha) - 0 to.6o", "bala", "0-6"),
    2: ("Youthful state (Kumaravastha) _ 6 to 12", "kumara", "6-12"),
    3: ("Adolescent state (yuvavastlra) -12 to lg", "yuva", "12-18"),
    4: ("Advanced state (Vridhdhavastha) _lg to 24.", "vriddha", "18-24"),
    5: ("In exrremis (Mritavastha) _24 to 30o", "mrita", "24-30"),
}
BAL3 = c("bphs", "bphs_pg0448_c01", "PG448", "3", "six degrees in odd signs. This arrangement is reverse in the case of even signs.")
BAL_Q = ("BPHS Sl.3 gives the Baladi sequence (Infant, Youthful, Adolescent, Old, Dead) at six degrees each in ODD signs and the REVERSE order in EVEN signs, "
         "but the stored rule is a bare degree range with no sign-parity field. Should the rule carry odd/even-sign reversal?")
for i, (q, st, rng) in BA.items():
    add(AT, {"id": i, "scheme_name": "baladi", "state_name": st}, f"Baladi state {st} = {rng} degrees in sign.", cit[i],
        "sourced_fact", "FACT",
        [c("bphs", "bphs_pg0448_c01", "PG448", "3", q), BAL3], None,
        "BPHS Chapter 45, Sloka 3 (Baladi avasthas) as printed — bphs:PG448:C1 (Santhanam trans.)", "recite", BAL_Q,
        note="Cited 'JP Ch.7' is not locatable: no Jataka Parijata chunk states the Baladi degree scheme (searched). Support is BPHS Ch.45 (a different held text). Degrees/names/order agree for odd signs; stored rule omits the even-sign reversal (scope gap, not a contradiction of the odd-sign statement). The degree table itself is in the translator's notes; the 6-degree rule is in the sloka.")

JG = {
    6: ("jagrata", "sourced_inference", "INFERENCE",
        [c("bphs", "bphs_pg0448_c01", "PG448", "5", "own sign or in exaltatioa it is said to be in a state of awakening"),
         c("jataka_parijata", "jataka_parijata_pg0118_c01", "PG118", "85", "Navamsa which is owned by it, they say, is its waking state")],
        "BPHS names own sign and exaltation only; 'moolatrikona' maps to awake by treating the Moolatrikona sign as the planet's own sign.",
        "BPHS Chapter 45, Sloka 5 as printed — bphs:PG448:C1 (Santhanam trans.)", "recite", None,
        "Moolatrikona is not itself named in Sl.5; inference rests on the Moolatrikona sign being the planet's own sign."),
    7: ("svapna", "contradicted", "CONTRADICTS",
        [c("bphs", "bphs_pg0448_c01", "PG448", "5", "In the sign of a friend or of a neutral it is in dreaming state"),
         c("jataka_parijata", "jataka_parijata_pg0118_c01", "PG118", "85", "The Navamsa belonging to a friendly planet is its dreaming state")],
        None, None, "acharya",
        "BPHS Sl.5 puts a planet in a NEUTRAL sign in the dreaming (svapna) state; the table maps neutral_sign to sushupti (deep sleep) and lists only friend/great-friend signs for svapna. Which is canonical?",
        "DB omits neutral_sign from svapna (BPHS includes it)."),
    8: ("sushupti", "contradicted", "CONTRADICTS",
        [c("bphs", "bphs_pg0448_c01", "PG448", "5", "while in eiemy's sign or in debjlitation it is in a state of sleeping"),
         c("bphs", "bphs_pg0448_c01", "PG448", "5", "In the sign of a friend or of a neutral it is in dreaming state")],
        None, None, "acharya",
        "BPHS Sl.5 restricts the sleeping (sushupti) state to enemy sign or debilitation; the table also maps neutral_sign to sushupti although BPHS puts neutral signs in the dreaming state. Which is canonical?",
        "DB includes neutral_sign in sushupti; BPHS does not (enemy/great-enemy/debilitated agree)."),
}
for i, (st, state, cls, corp, inf, prop, act, q, note) in JG.items():
    add(AT, {"id": i, "scheme_name": "jagradadi", "state_name": st}, f"Jagradadi state {st} by sign dignity.", cit[i], state, cls, corp, inf, prop, act, q,
        note=(note or "") + " Cited 'BPHS Ch.45' is resolvable (printed 'Chapter 45', PG448:C1).")

# deeptaadi
SV15 = lambda q: c("saravali", "saravali_pg0015_c01", "PG15", "2-4", q)
BP449 = lambda q: c("bphs", "bphs_pg0449_c01", "PG449", "8-10", q)
PDS = lambda ch, pg, sl, q: c("phaladeepika", ch, pg, sl, q)
DA_PROP = "Phaladeepika Adh. III, Sloka 18-20 (avasthas; chapter end printed at PG70:C1) as printed — phaladeepika:PG69:C1, phaladeepika:PG70:C1 (Sastri trans. 1950)"
DA_NOTE = ("Cited 'PD Ch.4': the avastha passage is printed in Adhyaya III (the 3rd Adhyaya closes at PG70:C1 right after Sl.20); Adhyaya IV opens with Shadbala. "
           "Matching PD's English glosses (blazing, confident, delighted, calm, capable, tortured, base, distressed, afraid, failing) to the Sanskrit state names is an inference; BPHS Sl.8-10 and Saravali Sl.2-4 print the Sanskrit names. "
           "PD lists ten states (incl. bheeta) vs nine in the table; BPHS lists a different nine-state set (Deepta, Swastha, Pramudita, Santa, Deena, Vikala, Khala, Kopa; text says 'nine' but OCR lists eight).")
DAQ = ("Held texts give three different dignity-to-state maps for the Deepta-Swastha-Mudita group (BPHS Ch.45 Sl.8-10, Phaladeepika Adh. III Sl.18-20, Saravali Ch.5 Sl.2-4); none matches the table's map "
       "(deepta=exalted/own, swastha=friend sign, mudita=friend navamsa, shanta=neutral sign, shakta=conjunct benefic, dina=enemy sign, peedit=combust/conjunct malefic, khala=debilitated, vikala=retrograde in enemy). "
       "Which scheme is intended, and should the table follow one text row-for-row?")
DE = {
    9: ("deepta", "contradicted", "CONTRADICTS",
        [BP449("it is in Deepta-vastha, in own sign Swastha"), PDS("phaladeepika_pg0069_c01", "PG69", "18", "A planet is blazing when he is in his exaltation"),
         SV15("A planet in its exaltation is said to be in Diptavastha.")],
        "Table: exalted_or_own. All three held texts: exaltation only; own sign is the next state (Swastha/confident).", None),
    10: ("swastha", "contradicted", "CONTRADICTS",
         [BP449("it is in Deepta-vastha, in own sign Swastha"), PDS("phaladeepika_pg0069_c01", "PG69", "18", "he is confident in his own house"),
          SV15("In its own House, it is in Svasthavastha")],
         "Table: friend_sign. BPHS (named), Saravali (named) and PD (gloss 'confident in his own house'): own sign.", None),
    11: ("mudita", "contradicted", "CONTRADICTS",
         [SV15("friendly House Muditavastha"), PDS("phaladeepika_pg0069_c01", "PG69", "18", "he is delighted in a friend's house"),
          BP449("in thick friend's sign Pramudita, in friendly sign Santa")],
         "Table: friend_navamsa (own or friendly navamsa). Held texts: friendly house/sign (Saravali, PD), thick-friend's sign for Pramudita (BPHS); none speaks of a navamsa.", None),
    12: ("shanta", "contradicted", "CONTRADICTS",
         [SV15("in beneficial Vargas Santavastha"), PDS("phaladeepika_pg0069_c01", "PG69", "18", "calm when he has reached the Varga of a benefic planet"),
          BP449("in friendly sign Santa, in neutral's sign Deena")],
         "Table: neutral_sign. Saravali/PD: benefic varga; BPHS: friendly sign (neutral sign = Deena).", None),
    13: ("shakta", "contradicted", "CONTRADICTS",
         [SV15("with bright rays Saktavastha"), PDS("phaladeepika_pg0069_c01", "PG69", "18", "He is capable when ho shines bright with unclouded splendour")],
         "Table: conjunct_benefic. Saravali (named) and PD (gloss): bright/unclouded rays.", None),
    14: ("dina", "sourced_inference", "INFERENCE",
         [PDS("phaladeepika_pg0070_c01", "PG70", "19", "He is exceedingly distressed when he occupies an enemy's house"),
          BP449("in neutral's sign Deena, in the company of a malefic' Vikata")],
         "Table: enemy_sign. PD (cited text): 'exceedingly distressed' in an enemy's house; reading that gloss as 'Dina/Deena' is the inference. BPHS (named) puts Deena in a NEUTRAL sign and Khala in an enemy sign, so the held texts disagree with each other.",
         "Is Dina = enemy sign (Phaladeepika) or neutral sign (BPHS)?"),
    15: ("peedit", "contradicted", "CONTRADICTS",
         [SV15("if defeated in planetary war, Nipidita"), PDS("phaladeepika_pg0069_c01", "PG69", "19", "He is tortured when overcome by another planet")],
         "Table: combust_or_conjunct_malefic. Saravali (named Nipidita) and PD (gloss 'tortured'): defeated in planetary war. Saravali assigns combustion to Vikala.", None),
    16: ("khala", "contradicted", "CONTRADICTS",
         [SV15("in malefic Vargas Khalavastha and, if in fall, in Bhitavastha"), BP449("in an enemy's sign Khala"),
          PDS("phaladeepika_pg0069_c01", "PG69", "19", "He is base by union with the Varga of a malefic")],
         "Table: debilitated. Held texts: malefic varga (Saravali, PD) or enemy's sign (BPHS); debilitation is Bhita (Saravali; PD 'greatly afraid').", None),
    17: ("vikala", "contradicted", "CONTRADICTS",
         [SV15("in combustion Vikalavastha"), PDS("phaladeepika_pg0070_c01", "PG70", "19", "He is failing when he has set or disappeared"),
          BP449("in the company of a malefic' Vikata")],
         "Table: retrograde_in_enemy. Held texts: combust/set (Saravali, PD) or in company of a malefic (BPHS); none says retrograde-in-enemy.", None),
}
for i, (st, state, cls, corp, diff, q) in DE.items():
    add(AT, {"id": i, "scheme_name": "deeptaadi", "state_name": st}, f"Deeptaadi state {st} per its determination condition.", cit[i], state, cls, corp,
        ("Matching PD's English gloss to the Sanskrit state name; BPHS and Saravali disagree with PD on this state." if state == "sourced_inference" else None),
        (DA_PROP if state == "sourced_inference" else None), "recite" if state == "sourced_inference" else "acharya",
        (q or DAQ), note=diff + " " + DA_NOTE)

# lajjitaadi
BP450 = lambda q: c("bphs", "bphs_pg0450_c01", "PG450", "11-18 (OCR 'I l-18')", q)
JP119 = lambda q: c("jataka_parijata", "jataka_parijata_pg0119_c01", "PG119", None, q)
UKMISS = ("Cited 'UK Ch.4': no Uttara Kalamrita chunk states the Lajjitadi avasthas (searched 'lajjit': only BPHS and Jataka Parijata). "
          "The comparison below is therefore against BPHS Ch.45 Sl.11-18 and Jataka Parijata (PG119, 'Six varieties ... declared by Sambhu'), which agree with each other.")
LAJQ = ("BPHS Ch.45 Sl.11-18 and Jataka Parijata (PG119) define Lajjita (5th house with Rahu/Ketu/Sun/Saturn/Mars), Garvita (exaltation or Moolatrikona), Kshudita (enemy sign / conjunct or aspected by enemy / with Saturn), "
        "Trushita (watery sign, aspected by a malefic, not by a benefic), Mudita (friendly sign or conjunct/aspected by benefic or Jupiter), Kshobhita (with the Sun and aspected by or conjunct a malefic / aspected by enemy). "
        "The table's conditions for Garvita, Trishita, Mudita and Kshobhita differ. Which version does the platform follow?")
LJ = {
    18: ("lajjita", "sourced_inference", "INFERENCE",
         [BP450("associated with a node or with the Sun, Saturn or Mars, it is in Lajjitavastba"),
          JP119("occupies the 5th house in conjunction with Rahu, Ketu, the Sun, Saturn or Mars")],
         "Texts name five malefics (Rahu, Ketu, Sun, Saturn, Mars); the table says generic 'malefic' - equal only if the engine's malefic set is that five.", None),
    19: ("garvita", "contradicted", "CONTRADICTS",
         [BP450("If a planet is in exaltation or in Moolatrikona, it is Garvitavastha."), JP119("Garvitha when it is in it* exaltation position")],
         "Table: own_or_exaltation_sign. Both held texts: exaltation or Moolatrikona (not every own sign).", None),
    20: ("kshudhita", "sourced_fact", "FACT",
         [BP450("Kshudita if the planet is in an enemy's sign, or conjunct an enemy"), JP119("occupies an inimical house or is in conjunction with Saturn or an inimical planet")],
         "Table encodes two of the four stated conditions (enemy sign; conjunct enemy); omits aspected-by-enemy and conjunct-Saturn.", None),
    21: ("trishita", "contradicted", "CONTRADICTS",
         [BP450("in a watery sign and be in aspect to a malefic but not a benefic"), JP119("being in a watery sign be at the same time aspected by an inimical planet")],
         "Table: conjunct_saturn_no_benefic. Held texts: watery sign + malefic aspect without benefic aspect; conjunction with Saturn belongs to Kshudita.", None),
    22: ("mudita", "contradicted", "CONTRADICTS",
         [BP450("in a friendly sign, or conjunct or aspected by a benefic or is conjunct Jupiter"), JP119("occupies a friend's house and be in conjunction with a friendly planet, or Jupiter")],
         "Table: conjunct_friend_in_own_sign. Held texts: friendly sign (BPHS: or conjunct/aspected by benefic or Jupiter); not 'own sign'.", None),
    23: ("kshobhita", "contradicted", "CONTRADICTS",
         [BP450("conjunct the Sun and is aspected by or conjunct a malefic"), c("jataka_parijata", "jataka_parijata_pg0119_c02", "PG119", None, "it is eclipsed bj the Sun and has on it the aspect of maleficx")],
         "Table: conjunct_sun_or_aspected_malefic (OR). Held texts require the Sun conjunction AND a malefic/enemy aspect or conjunction.", None),
}
for i, (st, state, cls, corp, diff, q) in LJ.items():
    add(AT, {"id": i, "scheme_name": "lajjitaadi", "state_name": st}, f"Lajjitaadi state {st} per its determination condition.", cit[i], state, cls, corp,
        ("'malefic' read as the five planets the texts name." if state == "sourced_inference" else None),
        ("BPHS Chapter 45, Sloka 11-18 (Lajjitadi avasthas) as printed — bphs:PG450:C1 (Santhanam trans.); Jataka Parijata p.119 — jataka_parijata:PG119:C1 (Subramanya Shashtri trans.)"
         if state != "contradicted" else None),
        "recite" if state != "contradicted" else "acharya", (LAJQ if state == "contradicted" else None),
        note=diff + " " + UKMISS)

# sayanadi
SAYQ = ("BPHS Ch.45 Sl.30-37 and Jataka Parijata (PG120-121) give the 12 Sayanadi avasthas in the order Sayana, Upavesana, Netrapani, Prakasana, Gamana(echcha), Gamana/Agamana, Sabha, Agama, Bhojana, Nrityalipsa, Kautuka, Nidra, "
        "and fix a planet's state by a formula (star number x planet order x navamsa number + birth star + ghatis + lagna, mod 12). The table's rule is 'count of planets in sign determines posture index' and its states 10-12 are kautuka, nidraksita, deeptamsa. "
        "Which method and which twelve names does the platform intend?")
BP453 = lambda q: c("bphs", "bphs_pg0453_c01", "PG453", "30-37", q)
JP120 = c("jataka_parijata", "jataka_parijata_pg0120_c01", "PG120", None, "(10) Nrutyi lipsa (desire to dance) (11) Kiuthuha (delight, joy, pleasure) and (12) Nidn (sleep)")
JP121 = c("jataka_parijata", "jataka_parijata_pg0121_c01", "PG121", None, "Divide the result by 12. The remainder will indicate the order of the Avastha")
BP453R = BP453("This figure be divided by 12 and the iemainder will indicate the corresponding Avastha")
BP453L = BP453("Sayana, Upavesana, Netrapani, Prakasana, Gamana, Aagamana, Sabha, Aiama, Bhojane, Nrityalipsa, Kautuka and Nidra")
SAYNAMES = {24: ("sayana", "name/order = BPHS 1st"), 25: ("upavesana", "BPHS 2nd"), 26: ("netrapani", "BPHS 3rd"), 27: ("prakasana", "BPHS 4th"),
            28: ("gamana", "BPHS 5th (JP: 5th is Gamanechcha, 6th Gamana)"), 29: ("agamana", "BPHS 6th (JP 8th)"), 30: ("sabha", "BPHS 7th"),
            31: ("agama", "BPHS 8th"), 32: ("bhojanaprapta", "BPHS 9th is 'Bhojane' (name variant)"),
            33: ("kautuka", "TABLE order 10; BPHS/JP: 10th = Nrityalipsa, Kautuka is 11th"),
            34: ("nidraksita", "TABLE order 11; BPHS/JP: 11th = Kautuka, 12th = Nidra; 'nidraksita' not printed"),
            35: ("deeptamsa", "TABLE order 12; not among the twelve in BPHS/JP (12th = Nidra)")}
for i, (st, nn) in SAYNAMES.items():
    add(AT, {"id": i, "scheme_name": "sayanadi", "state_name": st}, f"Sayanadi state {st} (order {nm[i][2]}) determined by planet count in sign.", cit[i],
        "contradicted", "CONTRADICTS", [BP453L, BP453R, JP120, JP121], None, None, "acharya", SAYQ,
        note=("Determination rule 'planet_count_in_sign' is contradicted by the formula printed in BPHS Sl.30-37 (PG453:C1-C2, PG454) and Jataka Parijata (PG121:C1); both are cited/held texts. "
              f"Name/order: {nn}. Cited 'PD Ch.4': no Sayanadi passage found in Phaladeepika (its Adh. III avasthas are the Deepta group; Adh. IV opens with Shadbala). 'JP Ch.7' is the book chapter of the cited JP page; chunk page is PG120-121."))

# ------------------------------------------------------------------ 4. bg_motion_state_thresholds (27 rows)
MT = "bg_motion_state_thresholds"
mrows = rq("select id, graha, motion_state, threshold_type, classical_citation from bg_motion_state_thresholds order by id")
assert len(mrows) == 27
BPM = lambda q, pg="PG284", ch="bphs_pg0284_c01": c("bphs", ch, pg, None, q)
M_EIGHT = c("bphs", "bphs_pg0283_c02", "PG283", None, "Eight kinds of motions are attributed to planets. These are Vakra")
M_ANU = BPM("Anuvakra (entering the previous sign in retrograde motion)")
M_VIK = BPM("Vikala (devoid of Motion or in stationary position)")
M_ATI = BPM("Atichara (entering next sign in accelerated motion)")
M_VAK = BPM("(retrogression), Anuvakra (entering the previous sign in retro- grade motion)")
M_MAN = BPM("Manda (somewhat slower motion than usual)")
M_SAM = BPM("Sama (somewhat increasing in motion as against Manda)")
NODE_RETRO = [c("bphs", "bphs_pg0569_c01", "PG569", None, "Rahu and Ketu who are always retrograde"),
              c("phaladeepika", "phaladeepika_pg0348_c01", "PG348", "48", "In the case of Rahu and Ketu, which are always retrograde")]
SS_NOTE = ("Cited 'SS / Saravali': Surya Siddhanta is not held; the held Saravali (Ch.4 Sl.36-37, Ch.5) discusses motional strength qualitatively and states no per-day speed thresholds (searched). ")
MQ = ("BPHS Ch.27 (Shadbala, Cheshta Bala) names eight motions - Vakra (retrogression), Anuvakra (entering the previous sign in retrograde motion), Vikala (stationary), Manda, Mandatara, Sama, Chara, Atichara (entering the next sign in accelerated motion) - "
      "with no degrees-per-day thresholds. The table gives Anuvakra as 'station/slow 0-0.1 deg/day' and every other state a numeric speed band. "
      "Is Anuvakra to be the retrograde sign-ingress motion (BPHS) or the stationary-slow band, and are the numeric speed bands platform conventions rather than classical values?")
for r in mrows:
    i, g, st, tt, ct = int(r["id"]), r["graha"], r["motion_state"], r["threshold_type"], r["classical_citation"]
    key = {"id": i, "graha": g, "motion_state": st}
    claim = f"{g} {st}: {tt} speed threshold (deg/day)."
    if g in ("Rahu", "Ketu"):
        add(MT, key, f"{g} motion state vakra always (mean node speed ~ -0.053 deg/day).", ct, "sourced_fact", "FACT", NODE_RETRO, None,
            "BPHS Chapter 47 (Dasa effects of Rahu and Ketu) p.571 — bphs:PG569:C1 (Santhanam trans.); Phaladeepika Adh. XXVI, Sloka 48 — phaladeepika:PG348:C1 (Sastri trans. 1950)",
            "recite", None,
            note=SS_NOTE + "Qualitative claim 'always retrograde' is stated; the -0.053 deg/day figure is a computed mean-node rate, not a classical statement (not in corpus).")
    elif st == "vakra":
        add(MT, key, f"{g} vakra when speed < 0 (retrograde).", ct, "sourced_inference", "INFERENCE", [M_EIGHT, M_VAK],
            "BPHS names Vakra as retrogression; 'speed below 0 deg/day' is the astronomical test of retrogression (not stated in any held text).",
            "BPHS Chapter 27 (Cheshta Bala; motion types) — bphs:PG283:C2, bphs:PG284:C1 (Santhanam trans.)", "recite", None, note=SS_NOTE)
    elif st == "anuvakra":
        add(MT, key, f"{g} anuvakra = station/slow speed band.", ct, "contradicted", "CONTRADICTS", [M_ANU, M_VIK], None, None, "acharya", MQ,
            note=SS_NOTE + "BPHS (held) defines Anuvakra as entering the previous sign in retrograde motion and assigns the stationary state to Vikala; no held text defines Anuvakra as a slow/stationary speed band.")
    else:
        extra = {"manda": M_MAN, "sama": M_SAM, "atichara": M_ATI}[st]
        add(MT, key, claim, ct, "unsourced_marked", "NONE", [M_EIGHT, extra], None, None, "mark_unsourced", MQ if i in (2, 4) else None,
            note=SS_NOTE + f"BPHS names '{st}' as a qualitative motion type only; the numeric speed thresholds/typical speed are not stated in the held corpus (platform-chosen or from the unheld Surya Siddhanta).")

# ------------------------------------------------------------------ 5. bg_combustion_orbs (8 rows)
CT = "bg_combustion_orbs"
crows = rq("select id, graha, orb_degrees, deep_orb_degrees, classical_citation from bg_combustion_orbs order by id")
assert len(crows) == 8
UKC = lambda q: c("uttara_kalamrita", "uttara_kalamrita_pg0135_c01", "PG135", None, q)
JPC = lambda q: c("jataka_parijata", "jataka_parijata_pg0262_c01", "PG262", None, q)
BPC = c("bphs", "bphs_pg0099_c01", "PG99", "28-29 (notes)", "Please see ths following table for degrees of combustion. [table OCR-garbled]")
PROP_C = ("Uttara Kalamrita Ch. VI (Notes), p.139 — uttara_kalamrita:PG135:C1 (Sastri trans.); Jataka Parijata commentary, p.262 — jataka_parijata:PG262:C1 (Subramanya Shashtri trans.); "
          "BPHS Chapter 7, notes to Sloka 28-29 — bphs:PG99:C1 (Santhanam trans.)")
CNOTE = ("Cited 'Saravali Ch.6 / BPHS Ch.3': neither locates the orb table. Held Saravali states no combustion orbs (qualitative only; PG145: 'A combust planet, excepting Venus and Saturn, loses all the rays'). "
         "BPHS Ch.3 has no combustion text; the BPHS table is in Ch.7 notes (PG98 header 'Chapter 7', table PG99:C1, OCR-garbled). Orbs are in translator's notes in UK/JP/BPHS, not primary verses. ")
CQ = ("Held texts give direct orbs Moon 12, Mars 17, Mercury 14, Jupiter 11, Venus 10, Saturn 15 and retrograde orbs only for Mercury 12 and Venus 8 (UK, JP). The table's second column (deep_orb_degrees: Moon 10, Mars 15, Jupiter 9, Saturn 12, Rahu/Ketu 7) "
      "has no source in the held corpus, and BPHS says Rahu and Ketu are not to be treated as combust while the table gives them orbs 9/7. What does deep_orb_degrees mean, which values are sourced, and should the nodes carry orbs at all?")
for r in crows:
    i, g, o, d = int(r["id"]), r["graha"], int(r["orb_degrees"]), int(r["deep_orb_degrees"])
    key = {"id": i, "graha": g}
    ct = r["classical_citation"]
    if g in ("Rahu", "Ketu"):
        add(CT, key, f"{g} combust within {o} degrees (deep {d}).", ct, "contradicted", "CONTRADICTS",
            [BPC, c("bphs", "bphs_pg0099_c01", "PG99", "28-29 (notes)", "Rahu and Ketu should not be treated as combust although they may bc longitudinally close"),
             c("sarvartha_chintamani", "sarvartha_chintamani_pg0001_c219", "PG1:C219", None, "Rahu and Ketliu have no com bud [combustion]")],
            None, None, "acharya", CQ,
            note=("Table gives the node an orb (9, deep 7); BPHS (translator's note, PG99) and Sarvartha Chintamani (PG1:C219) state the nodes are not combust (they eclipse the Sun instead). "
                  "No held text gives a node orb. Row note ('combust per some traditions; excluded by others') concedes the dispute but still stores 9/7. Constant brahma_formula_constants.combustion_orbs holds the same 9/7."))
    else:
        corp = {
            "Moon": [UKC("Moon 12. Kuja 17. Budha 14 and when retrograde only 12"), JPC("The Moon when within 12 from the Sun"), BPC],
            "Mars": [UKC("Moon 12. Kuja 17. Budha 14"), JPC("Mars when within 17"), BPC],
            "Mercury": [UKC("Budha 14 and when retrograde only 12"), JPC("Mercury when within 14 but when retrograde 12")],
            "Jupiter": [JPC("Jupiter when within 11"), UKC("Or.ru II, Shukra 10 and when retrograde only 8")],
            "Venus": [UKC("Shukra 10 and when retrograde only 8"), JPC("Venus 10 but when retrograde 8")],
            "Saturn": [UKC("and Shani 15"), JPC("Saturn when within 15")],
        }[g]
        full = g in ("Mercury", "Venus")
        add(CT, key, f"{g} combust within {o} degrees (deep/retrograde {d}).", ct, "sourced_fact", "FACT", corp, None, PROP_C, "recite",
            None if full else CQ,
            note=CNOTE + (f"Both values supported (retrograde {d} stated)." if full else
                          f"Direct orb {o} supported; the second value {d} is not stated for {g} in any held text (UK/JP give retrograde orbs only for Mercury and Venus)."),
            partial=None if full else ["deep_orb_degrees"])


# contradiction basis tag (who disagrees with the stored value)
for o in L:
    if o["state"] != "contradicted":
        continue
    t, k = o["table"], o["row_key"]
    if t == "bg_graha_naisargika_friendship" or t == "bg_motion_state_thresholds" or (t == "bg_avastha_schemes" and k["scheme_name"] == "lajjitaadi"):
        o["contradiction_basis"] = "other_held_text (cited passage not in held corpus; a different held text states otherwise)"
    else:
        o["contradiction_basis"] = "cited_text (the text the row cites, or the same-named passage, states otherwise)"

# ------------------------------------------------------------------ write
json.dump(L, open(OUT + "ledger.json", "w"), indent=1, ensure_ascii=False)
cnt = collections.Counter((o["table"], o["state"]) for o in L)
for k in sorted(cnt):
    print(k, cnt[k])
print("total", len(L))
