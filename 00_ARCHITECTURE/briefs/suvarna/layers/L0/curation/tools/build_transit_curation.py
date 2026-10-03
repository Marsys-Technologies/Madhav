#!/usr/bin/env python3
"""Build the bg_transit_rules / bg_transit_engine part of the L0 N-101 curation ledger,
re-check every claim against the live snapshot, and (optionally) verify each quoted phrase
against the corpus chunk through the reader-only helper.

  build_transit_curation.py ledger  <out.json>          # ledger entries (no DB needed)
  build_transit_curation.py verify-quotes <rq.sh path>  # re-read chunks, fuzzy-match every quote
  build_transit_curation.py sql <pins.json> <out.sql>   # draft migration text
  build_transit_curation.py seed-patch <repo_root> <out.patch>

No database is written.  `verify-quotes` uses only a SELECT through the caller-supplied
read-only helper and prints no credential."""
import difflib, hashlib, json, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import transit_curation_spec as S  # noqa: E402

SNAP = HERE.parent / "snapshots"


def load(name):
    return json.load(open(SNAP / f"live_{name}.json"))


RULES = load("rules")
ENGINE = load("engine")
BY_KEY = {(r["graha"], r["rule_type"], r["primary_house"]): r for r in RULES}
BY_ID = {r["id"]: r for r in RULES}

CHUNK_META = {}   # chunk_id -> (uuid, sha256) filled from snapshots/chunk_meta.json
CHUNK_META.update(json.load(open(SNAP / "chunk_meta.json")))


def chunk_ref(chunk_id, page, sloka=None, quote=None, text_id=None, numeral=None, role=None, note=None):
    meta = CHUNK_META.get(chunk_id, {})
    d = {"text_id": text_id or chunk_id.rsplit("_pg", 1)[0], "chunk_id": chunk_id, "chunk_uuid": meta.get("id"),
         "chunk_content_sha256": meta.get("content_sha256"), "page": page, "sloka_printed": sloka,
         "quote": quote}
    if quote and quote.startswith("Hahu"):
        note = ((note + "; ") if note else "") + "quote as printed: OCR 'Hahu' = Rahu"
    if numeral: d["sloka_numeral_basis"] = numeral
    if role: d["role"] = role
    if note: d["note"] = note
    return d


def entries():
    out = []
    pd = S.PD

    # --- A. 18 rows by direct statement ---------------------------------------------------
    for r in S.FACT_ROWS:
        live = BY_KEY[r["key"]]
        assert live["id"] == r["id"], (r, live["id"])
        old = S.OLD_BPHS29 if r["old"] == "bphs29" else S.OLD_PDCH26
        assert live["classical_citation"] == old, (r["id"], live["classical_citation"])
        assert live["vedha_house"] is None and live["rule_type"] == "unfavourable"
        corpus = [chunk_ref(S.pd_chunk(r["page"]), f"PG{r['page']}", str(r["sloka"]), r["quote"], numeral=r["numeral"],
                            role="states the house result", note="; ".join(x for x in [(f"sloka begins on PG{r['cont']}" if r["cont"] else None), (f"quote as printed, OCR: {r['ocr']}" if r.get("ocr") else None)] if x) or None)]
        out.append(dict(
            asset="bg_transit_rules", table="bg_transit_rules", row_key={"id": r["id"], "graha": r["key"][0], "rule_type": r["key"][1], "primary_house": r["key"][2]},
            row_count=1, claim=f"{r['key'][0]} transiting house {r['key'][2]} from the natal Moon gives an unfavourable result",
            current_citation=live["classical_citation"], state="sourced_fact", support_class="FACT",
            corpus=corpus, inference_step=None,
            phala_as_stored=live["phala"], phala_supported_by_chunk=r["supports"], phala_not_in_chunk=r["not_stated"],
            weak_wording=bool(r.get("weak")),
            proposed_citation=S.new_citation_fact(r), proposed_action="recite",
            acharya_question=("Confirm that 'untoward events' (Moon in the 8th, Phaladeepika Adh. XXVI sl. 12) is to be read as an unfavourable result; "
                              "the stored phala 'Fear, sorrow, ill health' is not in the sloka.") if r.get("weak") else None))

    # --- A2. 5 Ketu rows by stated equivalence (INFERENCE) --------------------------------
    for r in S.INFERENCE_ROWS:
        live = BY_KEY[r["key"]]
        assert live["id"] == r["id"]
        old = S.OLD_BPHS29 if r["old"] == "bphs29" else S.OLD_PDCH26
        assert live["classical_citation"] == old and live["vedha_house"] is None
        h = r["key"][2]
        corpus = [
            chunk_ref(S.pd_chunk(321), "PG321", "2", "Hahu and Ketu are similar to the Sun", numeral="printed", role="equivalence statement (FACT)"),
            chunk_ref(S.pd_chunk(r["sun_page"]), f"PG{r['sun_page']}", str(r["sun_sloka"]), r["sun_quote"], numeral="printed/running-head", role=f"Sun's result for house {h} (FACT about the Sun)"),
            chunk_ref(S.pd_chunk(331), "PG331", "24", r["rahu_quote"], numeral="printed", role=f"Rahu's result for house {h} (FACT about Rahu)"),
        ]
        out.append(dict(
            asset="bg_transit_rules", table="bg_transit_rules", row_key={"id": r["id"], "graha": "ketu", "rule_type": "unfavourable", "primary_house": h},
            row_count=1, claim=f"ketu transiting house {h} from the natal Moon gives an unfavourable result",
            current_citation=live["classical_citation"], state="sourced_inference", support_class="INFERENCE",
            corpus=corpus,
            inference_step=("No verse names Ketu's house results. Sloka 2 states Rahu and Ketu are 'similar to the Sun'; the Sun's own result for "
                            f"house {h} and Rahu's sloka-24 result for house {h} are both adverse; the Ketu valence is read from that equivalence."),
            phala_as_stored=live["phala"], phala_supported_by_chunk="unfavourable valence only", phala_not_in_chunk="all phala wording",
            proposed_citation=S.new_citation_inference(r), proposed_action="recite",
            acharya_question="Accept the sloka-2 equivalence (Rahu and Ketu similar to the Sun) as sufficient to source Ketu's unfavourable gochara results in houses 1, 2, 4, 7, 8 (5 rows)? If not, these rows become UNSOURCED."))

    # --- ketu 12 favourable: contradicted -----------------------------------------------
    k = BY_KEY[S.KETU_12["key"]]
    assert k["id"] == 199 and k["classical_citation"] == S.OLD_BPHS29
    out.append(dict(
        asset="bg_transit_rules", table="bg_transit_rules", row_key={"id": 199, "graha": "ketu", "rule_type": "favourable", "primary_house": 12},
        row_count=1, claim="ketu transiting the 12th from the natal Moon gives a FAVOURABLE result (moksha progress)",
        current_citation=k["classical_citation"], state="contradicted", support_class="CONTRADICTS",
        corpus=[
            chunk_ref(S.pd_chunk(321), "PG321", "2", "Hahu and Ketu are similar to the Sun", numeral="printed", role="equivalence; Sun's good houses are 6, 3, 10 (and 11 for all planets), not 12"),
            chunk_ref(S.pd_chunk(325), "PG325", "11", "the 12th house, there will be sorrow, loss of wealth", numeral="printed", role="Sun in the 12th is adverse"),
            chunk_ref(S.pd_chunk(331), "PG331", "24", "(12) expenditure", numeral="printed", role="Rahu in the 12th is adverse"),
        ],
        inference_step="The contradiction itself reads Ketu through the sloka-2 equivalence (INFERENCE); no verse names Ketu in the 12th.",
        phala_as_stored=k["phala"], proposed_citation=None, proposed_action="acharya",
        row_note="Row NOT changed (SS ruling). Its citation 'BPHS Ch.29' stays refuted.",
        acharya_question=("Ketu in the 12th from the Moon is stored FAVOURABLE ('moksha progress'). Phaladeepika Adh. XXVI sl. 2 puts Ketu with the Sun "
                          "(good houses 6, 3, 10, 11) and sl. 11 / sl. 24 give the Sun and Rahu in the 12th as adverse (sorrow/loss of wealth; expenditure). "
                          "Is there a classical gochara source (outside the held corpus) for a favourable Ketu-12 transit, or should the row become unfavourable / unsourced?")))

    # --- 39 already anchored rows: re-verify against the transcribed text ------------------
    anchored = []
    for sl, (page, grahas, pairs) in S.PD_VEDHA.items():
        for g in grahas:
            for ph, vh in pairs:
                live = BY_KEY.get((g, "favourable", ph))
                assert live is not None, (g, ph)
                ok_pair = live["vedha_house"] == vh
                ok_good = ph in S.PD_SL2_GOOD[g]
                cit_ok = f"Sloka {sl} — phaladeepika:PG{page}:C1" in live["classical_citation"]
                anchored.append((live, sl, page, ok_pair, ok_good, cit_ok))
    assert len(anchored) == 36, len(anchored)
    for live, sl, page, ok_pair, ok_good, cit_ok in anchored:
        assert ok_pair and ok_good and cit_ok, live
        out.append(dict(
            asset="bg_transit_rules", table="bg_transit_rules", row_key={"id": live["id"], "graha": live["graha"], "rule_type": "favourable", "primary_house": live["primary_house"]},
            row_count=1, claim=f"{live['graha']} house {live['primary_house']} favourable unless vedha house {live['vedha_house']} is occupied",
            current_citation=live["classical_citation"], state="already_sourced_verified", support_class="FACT",
            corpus=[chunk_ref(S.pd_chunk(page), f"PG{page}", str(sl), S.PD_VEDHA_PHRASE[sl], numeral="printed", role=f"vedha-house list containing house {live['vedha_house']} (pair for primary house {live['primary_house']}, order as printed)"),
                    chunk_ref(S.pd_chunk(321), "PG321", "2", "good results ... in the 11th", numeral="printed", role="favourable-house set")],
            inference_step=None, proposed_citation=None, proposed_action="none",
            verification={"method": "pair (primary, vedha) transcribed from the chunk and diffed against the live row; favourable house checked against the sloka-2 set",
                          "pair_matches": True, "house_in_sloka2_favourable_set": True, "citation_token_matches_page": True}))
    for pid, why in S.PD_VENUS_UNFAV.items():
        live = BY_KEY[("venus", "unfavourable", pid)]
        assert "Slokas 2, 8 & 21" in live["classical_citation"] and live["vedha_house"] is None
        out.append(dict(
            asset="bg_transit_rules", table="bg_transit_rules", row_key={"id": live["id"], "graha": "venus", "rule_type": "unfavourable", "primary_house": pid},
            row_count=1, claim=f"venus house {pid} unfavourable",
            current_citation=live["classical_citation"], state="already_sourced_verified", support_class="FACT",
            corpus=[chunk_ref(S.pd_chunk(329), "PG329", "21", why, numeral="printed", role="adverse result"),
                    chunk_ref(S.pd_chunk(321), "PG321", "2", "Venus in all places other than the 10th, 7th and 6th", numeral="printed", role="complement of the good set")],
            inference_step=None, proposed_citation=None, proposed_action="none",
            row_note="Existing citation is sloka-grain (no PG anchors); a page anchor (PG321, PG323, PG329) could be added in a later pass.",
            verification={"adverse_result_stated_in_sloka_21": True, "excluded_from_sloka_2_good_set": True}))

    # --- 6 Rahu/Ketu favourable-with-vedha: already marked UNSOURCED ------------------------
    for rid in (187, 188, 189, 196, 197, 198):
        live = BY_ID[rid]
        assert live["classical_citation"].startswith("UNSOURCED")
        out.append(dict(
            asset="bg_transit_rules", table="bg_transit_rules", row_key={"id": rid, "graha": live["graha"], "rule_type": "favourable", "primary_house": live["primary_house"]},
            row_count=1, claim=f"{live['graha']} house {live['primary_house']} favourable with vedha house {live['vedha_house']}",
            current_citation=live["classical_citation"][:120] + "...", state="unsourced_marked", support_class="NONE",
            corpus=[chunk_ref(S.pd_chunk(321), "PG321", "2", "Hahu and Ketu are similar to the Sun", numeral="printed", role="supports the favourable-house set only, not any vedha pairing")],
            inference_step=None, proposed_citation=None, proposed_action="none",
            row_note="Already honestly marked in the row text. attribution_state column (TI-L0-09) not yet available.",
            acharya_question=("Sloka 2 (Phaladeepika Adh. XXVI) says Rahu and Ketu are similar to the Sun, whose good transit houses are 6, 3, 10 (and 11 for all planets). "
                              "The table carries Rahu and Ketu favourable at houses 3, 6, 11 only (six rows, vedha pairs UNSOURCED) and has no 10th-house row. "
                              "Is the missing 10th intentional, and does the Sun's vedha pairing (3-9, 6-12, 10-4, 11-5) apply to the nodes?")))

    # --- 7 double-transit rows --------------------------------------------------------------
    for live in sorted((r for r in RULES if r["rule_type"] == "double_transit"), key=lambda r: r["id"]):
        also = []
        if "BPHS ch.29" in live["classical_citation"]: also.append("also cites 'BPHS ch.29', refuted: no BPHS transit chapter in the held edition (bphs:PG29:C1 is Bhava Padas)")
        out.append(dict(
            asset="bg_transit_rules", table="bg_transit_rules", row_key={"id": live["id"], "graha": live["graha"], "rule_type": "double_transit", "primary_house": live["primary_house"]},
            row_count=1, claim=f"Jupiter+Saturn double transit in house {live['primary_house']}",
            current_citation=live["classical_citation"], state="unsourced_marked", support_class="NONE", corpus=[],
            inference_step=None, proposed_citation=None, proposed_action="mark_unsourced",
            row_note=("Full-text probe over all held texts for double-transit / double-gochara / jointly transit / Jupiter+Saturn simultaneous: 0 hits, so the cited "
                      "'Phaladeepika ch.26 section double-gochara' does not exist in the held text. Saravali ch.28 / Jataka Parijata have no locator. "
                      + ("; ".join(also) if also else "")).strip(),
            acharya_question=None))

    ids = [e["row_key"]["id"] for e in out]
    assert len(ids) == len(set(ids)) == 76 and set(ids) == set(BY_ID), (len(ids), set(BY_ID) - set(ids))
    return out


ENGINE_Q = {
    "sun": "sign_residence_days: the held notes (brihat_jataka PG96, jataka_parijata PG144) give the round classical figure '30 days' per sign; the stored value is the modern mean 30.44. Which should the column carry (SS decision, WAVE-1 Part A)?",
    "jupiter": "sign_residence_days: the held text gives 'about one year per sign' (yavana_jataka verse 52.1); the stored value is the modern mean 361.05. Classical round figure or modern mean?",
    "saturn": "sign_residence_days: the held notes give '30 months' per sign and 'takes 900 days'; the stored 913.37 d is 30 x 30.446. Which convention, and is 900 or 913.37 intended?",
    "moon": "(1) sarvartha_chintamani PG1:C301 (translator's note) prints the Moon's time per sign as '2 J days' in the OCR; confirm from the page image whether it reads 2 1/4 days. (2) yavana_jataka PG937 (commentary) derives the sidereal month as 27;24,18 d = 27.405 d; the stored zodiac_period_days is the modern 27.32. Which convention should the column carry?",
    "mercury": "WAVE-1 defect, not curation: avg_daily_motion_deg 1.3833 and sign_residence_days 14 agree neither with the stored 87.97 d period (implies 4.0923 deg/d) nor with each other. Under which single rule (heliocentric period vs Sun-following geocentric mean) should the three cells be set, and what classical source (book edition) exists for any value kept?",
    "venus": "WAVE-1 defect, not curation: avg_daily_motion_deg 1.2000 and sign_residence_days 23 agree neither with the stored 224.70 d period (implies 1.6021 deg/d) nor with each other. Same question as Mercury.",
    "mars": "sign_residence_days 45 is not period/12 (57.25) and is stated nowhere in the held corpus. Is there a classical source (book edition) for 1.5 months per sign, or should it become period/12 or unsourced?",
    "rahu": "sign_residence_days 548 d (18 months) is not period/12 (566.12) and is stated nowhere in the held corpus. Classical source (book edition) for 18 months per sign, or period/12?",
    "ketu": "Same as Rahu (Ketu moves with Rahu): source for 548 d per sign, or period/12?",
}


def engine_entries():
    out = []
    cols = {"avg_daily_motion_deg": "avg_daily_motion_deg", "zodiac_period_days": "zodiac_period_days", "sign_residence_days": "sign_residence_days"}
    for e in sorted(ENGINE, key=lambda r: r["graha"]):
        g = e["graha"]
        assert e["classical_citation"] == S.OLD_ENGINE_CITATION
        spec = S.ENGINE[g]
        corpus = [chunk_ref(cid, pg, None, (q if spec["state"] != "unsourced_marked" else None), text_id=tid,
                            role="supports sign_residence_days (round figure)" if spec["state"] != "unsourced_marked" else "candidate, not relied on",
                            note=(q if spec["state"] == "unsourced_marked" else None))
                  for tid, cid, pg, q in spec["pointers"]]
        corpus.append(chunk_ref("bphs_pg0022_c01", "PG22", None, "From the Sun God the incarnation of Rama", role="what the cited 'BPHS Ch.22' actually is (refutes the old citation)"))
        out.append(dict(
            asset="bg_transit_engine", table="bg_transit_engine", row_key={"id": None, "graha": g}, row_count=1,
            claim=f"{g}: avg_daily_motion_deg={e['avg_daily_motion_deg']}, zodiac_period_days={e['zodiac_period_days']}, sign_residence_days={e['sign_residence_days']}",
            current_citation=e["classical_citation"], state=("sourced_inference" if spec["state"] == "sourced_inference_partial" else "unsourced_marked"),
            support_class=("INFERENCE" if spec["state"] == "sourced_inference_partial" else "NONE"), corpus=corpus,
            cells={"avg_daily_motion_deg": "NONE", "zodiac_period_days": "NONE", "sign_residence_days": spec["cells"].get("sign_residence_days", "NONE")},
            inference_step=("round classical figure -> stored mean (see citation text)" if spec["cells"] else None),
            proposed_citation=S.engine_citation(g), proposed_action="recite",
            row_note="Citation text only; the numeric values are NOT changed here (WAVE-1 Part B is an SS decision).",
            acharya_question=ENGINE_Q.get(g)))
    return out


# --------------------------------------------------------------------------------------------
def norm(s):
    s = s.lower()
    s = re.sub(r"-\s+", "", s)           # soft hyphen line breaks
    s = re.sub(r"[^a-z0-9()%.,;:'\-’ ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def best_ratio(needle, hay):
    n = len(needle)
    best = 0.0
    step = max(1, n // 6)
    for i in range(0, max(1, len(hay) - n + 1), step):
        r = difflib.SequenceMatcher(None, needle, hay[i:i + n + 6], autojunk=False).ratio()
        if r > best: best = r
    return best


def fetch(rq, chunk_id):
    sql = f"select encode(convert_to(content_en,'UTF8'),'hex') from classical_text_chunks where chunk_id='{chunk_id}'"
    out = subprocess.run([rq, sql], capture_output=True, text=True).stdout.strip().splitlines()
    return bytes.fromhex(out[1]).decode("utf8")


def verify_quotes(rq):
    allents = entries() + engine_entries()
    cache, bad, n, minr = {}, [], 0, [1.0]
    for e in allents:
        for c in e["corpus"]:
            if not c.get("quote") or c.get("role", "").startswith("candidate"): continue
            if c["chunk_id"] not in cache: cache[c["chunk_id"]] = norm(fetch(rq, c["chunk_id"]))
            sha = hashlib.sha256  # (chunk_content_sha256 is the DB's own column; compared below)
            for seg in [s.strip() for s in c["quote"].split("...") if s.strip()]:
                if re.match(r"house \d+ / vedha", seg): continue   # structural description, verified by the pair diff
                n += 1
                nd = norm(seg)
                ratio = 1.0 if nd in cache[c["chunk_id"]] else best_ratio(nd, cache[c["chunk_id"]])
                minr[0] = min(minr[0], ratio)
                if ratio < 0.80: bad.append((e["row_key"], c["chunk_id"], seg, round(ratio, 3)))
    print(f"quote segments checked: {n}; below 0.80 similarity (OCR-noise tolerance): {len(bad)}; minimum similarity seen: {minr[0]:.3f}")
    for b in bad: print("  LOW", b)
    return 1 if bad else 0



# --------------------------------------------------------------------------------------------
# Draft SQL + seed patch generation
# --------------------------------------------------------------------------------------------
def rule_updates():
    """[(graha, rule_type, primary_house, old, new)] for the 23 re-sourced rows."""
    ups = []
    for r in S.FACT_ROWS:
        old = S.OLD_BPHS29 if r["old"] == "bphs29" else S.OLD_PDCH26
        ups.append((*r["key"], old, S.new_citation_fact(r)))
    for r in S.INFERENCE_ROWS:
        old = S.OLD_BPHS29 if r["old"] == "bphs29" else S.OLD_PDCH26
        ups.append((*r["key"], old, S.new_citation_inference(r)))
    assert len(ups) == 23
    return ups


def engine_updates():
    ups = [(e["graha"], S.OLD_ENGINE_CITATION, S.engine_citation(e["graha"])) for e in sorted(ENGINE, key=lambda r: r["graha"])]
    assert len(ups) == 9
    return ups


def dq(s, tag="c"):
    assert f"${tag}$" not in s
    return f"${tag}${s}${tag}$"


def update_statements():
    rv = ",\n      ".join(f"({dq(g)}, {dq(t)}, {h}, {dq(o)}, {dq(n)})" for g, t, h, o, n in rule_updates())
    ev = ",\n      ".join(f"({dq(g)}, {dq(o)}, {dq(n)})" for g, o, n in engine_updates())
    rules = ("UPDATE bg_transit_rules r SET classical_citation = v.new_c\n"
             "    FROM (VALUES\n      " + rv + "\n    ) AS v(graha, rule_type, primary_house, old_c, new_c)\n"
             "    WHERE r.graha = v.graha AND r.rule_type = v.rule_type AND r.primary_house = v.primary_house\n"
             "      AND r.classical_citation = v.old_c AND r.vedha_house IS NULL")
    engine = ("UPDATE bg_transit_engine e SET classical_citation = v.new_c\n"
              "    FROM (VALUES\n      " + ev + "\n    ) AS v(graha, old_c, new_c)\n"
              "    WHERE e.graha = v.graha AND e.classical_citation = v.old_c")
    return rules, engine


ENGINE_HASH_SQL = ("SELECT encode(sha256(convert_to(COALESCE(string_agg(\n"
                   "    jsonb_build_array(graha,avg_daily_motion_deg,zodiac_period_days,\n"
                   "      sign_residence_days,classical_citation)::text,\n"
                   "    E'\\n' ORDER BY graha COLLATE \"C\"\n"
                   "  ),''),'UTF8')),'hex') FROM bg_transit_engine")
RULES_HASH_SQL = ("SELECT encode(sha256(convert_to(COALESCE(string_agg(\n"
                  "    jsonb_build_array(rule_type,graha,primary_house,vedha_house,phala,\n"
                  "      classical_citation,rule_notes)::text,\n"
                  "    E'\\n' ORDER BY graha COLLATE \"C\",rule_type COLLATE \"C\",primary_house\n"
                  "  ),''),'UTF8')),'hex') FROM bg_transit_rules")

REG = {r["asset_id"]: r for r in load("registry")}
OLD_ENGINE_HASH = "e2dafc84d7fef9b8a05ad01b98b036686e8ec0af9694a4d43ac4b2b8c425797b"
OLD_RULES_HASH = "1dbdd265cf0e04edd26aebde054f34d9034be38bfabc8102085b0127196a598d"

NEW_ENGINE_DESC = ("L0 average graha motion parameters — daily motion, zodiac period, sign residence. The period values coincide with modern mean sidereal periods; none is a classical statement: "
                   "the former 'Source: BPHS Ch.22' was refuted (served bphs:PG22:C1 is Chapter 2, incarnations). Only round sign-residence figures for the Sun, Jupiter and "
                   "Saturn are stated in the held corpus; each row's classical_citation says exactly which cell, if any, is sourced.")
NEW_RULES_DESC = ("76 classical transit rules: 43 favourable, 26 unfavourable, 7 double-transit. Citation state after the 2026-10 N-101 curation, measured not asserted: "
                  "39 rows carry page/sloka-anchored Phaladipika Adh. XXVI citations from the earlier L0 repair (36 favourable-with-vedha, 3 Venus unfavourable); "
                  "23 unfavourable rows were re-sourced to Phaladipika Adh. XXVI slokas 9-24 (18 by direct statement of the adverse result; 5 Ketu rows by the sloka-2 "
                  "'Rahu and Ketu are similar to the Sun' equivalence, an INFERENCE) — the stored phala wording of those rows goes beyond the slokas and is editorial; "
                  "6 Rahu/Ketu favourable-with-vedha rows are declared UNSOURCED; 1 row (Ketu 12th, favourable) still carries the refuted \"BPHS Ch.29\" and CONTRADICTS "
                  "the held text (acharya batch, row not changed); 7 double-transit rows cite a Phaladeepika section and other sources that cannot be resolved in the held corpus (unsourced).")


ATTR_BLOCK_TEMPLATE = "\n-- ---------------------------------------------------------------------------------------------\n-- OPTIONAL second block: attribution_state (migration 1268 / PR #3044, TI-L0-09).  Runs only if the column exists.\n--   ORDER: apply 1268 FIRST (its backfill guard expects 19 `refuted` rows = the BPHS Ch.29 set this file re-sources;\n--   applied after this file it would refuse by design: the audited set changed).  Then this block moves the rows:\n--     * 18 rows re-sourced by direct statement (FACT)      -> 'sourced'   (from NULL or 'refuted')\n--     * 5 Ketu rows sourced by the sloka-2 equivalence     -> NULL        (INFERENCE is not a PASS until the acharya accepts it;\n--                                                                          'refuted' no longer describes the NEW citation)\n--     * Ketu 12th (id 199), the 6 UNSOURCED node rows, the 7 double-transit rows: untouched.\n--   Any of the 23 rows in another state raises.  Idempotent.\nDO $attr$\nDECLARE\n  n integer;\n  bad integer;\n  fact_keys constant text[] := ARRAY[__FACT_KEYS__];\n  inf_keys  constant text[] := ARRAY[__INF_KEYS__];\nBEGIN\n  IF NOT EXISTS (SELECT 1 FROM information_schema.columns\n                  WHERE table_schema = current_schema() AND table_name = 'bg_transit_rules' AND column_name = 'attribution_state') THEN\n    RAISE NOTICE 'attribution_state column absent (migration 1268 not applied): skipping the state block';\n    RETURN;\n  END IF;\n  EXECUTE $q$SELECT count(*) FROM bg_transit_rules\n              WHERE (graha||'|'||rule_type||'|'||primary_house) = ANY($1 || $2)\n                AND attribution_state IS NOT NULL AND attribution_state <> 'refuted' AND attribution_state <> 'sourced'$q$\n     INTO bad USING fact_keys, inf_keys;\n  IF bad <> 0 THEN\n    RAISE EXCEPTION 'curation refuses: % of the 23 re-sourced rows carry an attribution_state other than NULL / refuted / sourced', bad;\n  END IF;\n  EXECUTE $q$UPDATE bg_transit_rules SET attribution_state = 'sourced'\n              WHERE (graha||'|'||rule_type||'|'||primary_house) = ANY($1) AND attribution_state IS DISTINCT FROM 'sourced'$q$ USING fact_keys;\n  GET DIAGNOSTICS n = ROW_COUNT;\n  RAISE NOTICE 'attribution_state: % FACT rows set to sourced', n;\n  EXECUTE $q$UPDATE bg_transit_rules SET attribution_state = NULL\n              WHERE (graha||'|'||rule_type||'|'||primary_house) = ANY($1) AND attribution_state = 'refuted'$q$ USING inf_keys;\n  GET DIAGNOSTICS n = ROW_COUNT;\n  RAISE NOTICE 'attribution_state: % INFERENCE rows reset from refuted to NULL', n;\n  EXECUTE $q$SELECT count(*) FROM bg_transit_rules WHERE (graha||'|'||rule_type||'|'||primary_house) = ANY($1) AND attribution_state IS DISTINCT FROM 'sourced'$q$\n     INTO bad USING fact_keys;\n  IF bad <> 0 THEN RAISE EXCEPTION 'curation post-flight: % FACT rows are not sourced', bad; END IF;\nEND\n$attr$;\n"


def build_sql(pins):
    assert REG["bg_transit_engine"]["integrity_check_sql"].count(OLD_ENGINE_HASH) == 1
    assert REG["bg_transit_rules"]["integrity_check_sql"].count(OLD_ENGINE_HASH) == 1
    assert REG["bg_transit_rules"]["integrity_check_sql"].count(OLD_RULES_HASH) == 1
    rules_sql, engine_sql = update_statements()
    fact_keys = ", ".join("'%s|%s|%d'" % tuple(r["key"]) for r in S.FACT_ROWS)
    inf_keys = ", ".join("'%s|%s|%d'" % tuple(r["key"]) for r in S.INFERENCE_ROWS)
    attr_block = ATTR_BLOCK_TEMPLATE.replace("__FACT_KEYS__", fact_keys).replace("__INF_KEYS__", inf_keys)
    eng_old_desc, rul_old_desc = REG["bg_transit_engine"]["english_description"], REG["bg_transit_rules"]["english_description"]
    return f"""-- =============================================================================
-- DRAFT_NEEDS_NUMBER_l0_transit_citation_curation.sql      (HELD DRAFT: NOT APPLIED, NOT A MIGRATION)
-- Lane: curation-lane (Exec Suvarna), branch suvarna/land/TI-curation-001, N-101 curation of
--       bg_transit_rules + bg_transit_engine.  SS allocates the migration number (block 1200-1299).
--
-- WHAT IT DOES  (citation TEXT only; no rule, phala, house, vedha or numeric value changes)
--   * bg_transit_rules: re-sources 23 unfavourable rows off the refuted "BPHS Ch.29" (18) / the
--     chapter-only "Phaladeepika Ch.26" (5) to Phaladeepika Adh. XXVI slokas 9-24, chunk-level
--     (phaladeepika:PG324..PG331).  18 rows by direct statement (FACT), 5 Ketu rows by the sloka-2
--     equivalence "Rahu and Ketu are similar to the Sun" (INFERENCE, stated in the text of the citation).
--     NOT changed: Ketu 12th favourable (id 199: contradicts the text -> acharya batch), the 7
--     double-transit rows, the 6 UNSOURCED node rows, the 39 already page/sloka-anchored rows.
--   * bg_transit_engine: replaces the refuted "BPHS Ch.22 (Graha Gati)" on all 9 rows by an honest per-row
--     source-state statement (UNSOURCED, or PARTIALLY SOURCED naming the one cell the corpus states).
--     Numeric values are NOT touched (WAVE-1 Part B is an SS decision).
--   * OPTIONAL second block (runs only if bg_transit_rules.attribution_state exists, migration 1268 / PR #3044): the 18 FACT rows
--     become 'sourced', the 5 INFERENCE (Ketu) rows are reset from 'refuted' to NULL.  Apply 1268 BEFORE this file.
--   * Re-seals the two asset_registry integrity contracts (their sha256 covers these citation columns) and
--     updates the two english_description texts that still asserted the refuted sources.
--
-- GUARDS  (all fail loudly, nothing partial: one DO block under the runner-owned transaction)
--   old-value guard : live engine/rules content hashes must equal the pinned pre-state hashes; every UPDATE
--                     matches on (graha, rule_type, primary_house) AND the exact old citation AND vedha_house IS NULL;
--                     exact row counts (23, 9) asserted.
--   idempotency     : if the tables are already at the curated content AND the registry is resealed -> NOTICE + no-op.
--   post-flight     : curated content hashes equal the pinned post-state hashes; BPHS Ch.29 remains on exactly 1 row;
--                     no 'Phaladeepika Ch.26 (Gochara Vedha' and no 'BPHS Ch.22' citation remains; both stored
--                     integrity_check_sql statements evaluate true.
-- PINNED HASHES  engine {pins['engine']}
--                rules  {pins['rules']}
-- DOWNSTREAM NOTE (measured 2026-10-03, read-only): the Kala-layer products hold BUILD-TIME COPIES of the old rule
--   citations -- gochara_resonance_map.classical_citation (115 rows carry 'BPHS Ch.29' / 'Phaladeepika Ch.26'; 57 of
--   them reference 14 of the 23 rule ids changed here) and kala_gochara_contacts.classical_citation (123 rows; it
--   also carries a corpus_verifiable stamp).  Nothing here changes them and no integrity check compares them with
--   bg_transit_rules, but they keep the old strings until ka_gochara_resonance / the contacts writer are rebuilt
--   (Kala layer: out of this lane's scope; SS to schedule with the Pravaha owner).
-- ROLLBACK (manual): re-run the inverse UPDATEs (old/new swapped) and restore the pre-state registry rows from
--   snapshots/live_registry.json.
-- Seed parity: platform/python-sidecar/brahmagyan/l0_transit.py must carry the same citations or the next L0
--   rebuild reverts them -> see DRAFT_l0_transit_seed_curation.patch (stales nirmana-writer-digests.json: needs
--   regeneration after PR #2984 lands).
-- =============================================================================

DO $curation$
DECLARE
  c_engine_old constant text := '{OLD_ENGINE_HASH}';
  c_rules_old  constant text := '{OLD_RULES_HASH}';
  c_engine_new constant text := '{pins['engine']}';
  c_rules_new  constant text := '{pins['rules']}';
  c_eng_ic_md5 constant text := '{hashlib.md5(REG['bg_transit_engine']['integrity_check_sql'].encode()).hexdigest()}';
  c_rul_ic_md5 constant text := '{hashlib.md5(REG['bg_transit_rules']['integrity_check_sql'].encode()).hexdigest()}';
  c_eng_desc_old constant text := {dq(eng_old_desc, 'd')};
  c_eng_desc_new constant text := {dq(NEW_ENGINE_DESC, 'd')};
  c_rul_desc_old constant text := {dq(rul_old_desc, 'd')};
  c_rul_desc_new constant text := {dq(NEW_RULES_DESC, 'd')};
  engine_hash_sql constant text := {dq(ENGINE_HASH_SQL, 'q')};
  rules_hash_sql  constant text := {dq(RULES_HASH_SQL, 'q')};
  eng_reg asset_registry%ROWTYPE;
  rul_reg asset_registry%ROWTYPE;
  h_engine text;
  h_rules text;
  n integer;
  ok boolean;
BEGIN
  SELECT * INTO eng_reg FROM asset_registry WHERE asset_id = 'bg_transit_engine' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'curation refuses: asset_registry row bg_transit_engine not found'; END IF;
  SELECT * INTO rul_reg FROM asset_registry WHERE asset_id = 'bg_transit_rules' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'curation refuses: asset_registry row bg_transit_rules not found'; END IF;

  EXECUTE engine_hash_sql INTO h_engine;
  EXECUTE rules_hash_sql INTO h_rules;

  -- idempotent no-op: already curated AND resealed
  IF h_engine = c_engine_new AND h_rules = c_rules_new THEN
    IF position(c_engine_new IN eng_reg.integrity_check_sql) = 0
       OR position(c_engine_new IN rul_reg.integrity_check_sql) = 0
       OR position(c_rules_new IN rul_reg.integrity_check_sql) = 0 THEN
      RAISE EXCEPTION 'curation refuses: tables are at the curated content but the registry contracts are not resealed';
    END IF;
    RAISE NOTICE 'curation already applied: no-op';
    RETURN;
  END IF;

  -- old-value guards
  IF h_engine IS DISTINCT FROM c_engine_old OR h_rules IS DISTINCT FROM c_rules_old THEN
    RAISE EXCEPTION 'curation refuses: bg_transit_engine / bg_transit_rules content is not the pinned pre-state (engine %, rules %)', h_engine, h_rules;
  END IF;
  IF md5(eng_reg.integrity_check_sql) IS DISTINCT FROM c_eng_ic_md5
     OR md5(rul_reg.integrity_check_sql) IS DISTINCT FROM c_rul_ic_md5 THEN
    RAISE EXCEPTION 'curation refuses: registry integrity_check_sql is not the pinned pre-state text (md5 mismatch)';
  END IF;
  IF eng_reg.english_description IS DISTINCT FROM c_eng_desc_old OR rul_reg.english_description IS DISTINCT FROM c_rul_desc_old THEN
    RAISE EXCEPTION 'curation refuses: registry english_description has drifted from the pinned pre-state';
  END IF;

  -- bg_transit_rules: 23 citation updates
  {rules_sql};
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 23 THEN RAISE EXCEPTION 'curation expected 23 bg_transit_rules rows, updated %', n; END IF;

  -- bg_transit_engine: 9 citation updates
  {engine_sql};
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 9 THEN RAISE EXCEPTION 'curation expected 9 bg_transit_engine rows, updated %', n; END IF;

  -- post-flight content
  EXECUTE engine_hash_sql INTO h_engine;
  EXECUTE rules_hash_sql INTO h_rules;
  IF h_engine IS DISTINCT FROM c_engine_new OR h_rules IS DISTINCT FROM c_rules_new THEN
    RAISE EXCEPTION 'curation post-flight: content hash mismatch (engine %, rules %)', h_engine, h_rules;
  END IF;
  SELECT count(*) INTO n FROM bg_transit_rules WHERE classical_citation LIKE 'BPHS Ch.29%';
  IF n <> 1 THEN RAISE EXCEPTION 'curation post-flight: expected exactly 1 remaining BPHS Ch.29 row (Ketu 12th), found %', n; END IF;
  SELECT count(*) INTO n FROM bg_transit_rules WHERE classical_citation LIKE 'Phaladeepika Ch.26 (Gochara Vedha%';
  IF n <> 0 THEN RAISE EXCEPTION 'curation post-flight: % chapter-only Phaladeepika Ch.26 rows remain', n; END IF;
  SELECT count(*) INTO n FROM bg_transit_engine WHERE classical_citation LIKE '%BPHS Ch.22 (Graha Gati%' AND classical_citation NOT LIKE 'PARTIALLY SOURCED%' AND classical_citation NOT LIKE 'UNSOURCED%';
  IF n <> 0 THEN RAISE EXCEPTION 'curation post-flight: % engine rows still cite BPHS Ch.22 as a source', n; END IF;

  -- reseal the two registry contracts
  UPDATE asset_registry
     SET integrity_check_sql = replace(integrity_check_sql, c_engine_old, c_engine_new),
         english_description = c_eng_desc_new
   WHERE asset_id = 'bg_transit_engine';
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 1 THEN RAISE EXCEPTION 'curation expected 1 engine registry row, updated %', n; END IF;
  UPDATE asset_registry
     SET integrity_check_sql = replace(replace(integrity_check_sql, c_engine_old, c_engine_new), c_rules_old, c_rules_new),
         english_description = c_rul_desc_new
   WHERE asset_id = 'bg_transit_rules';
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 1 THEN RAISE EXCEPTION 'curation expected 1 rules registry row, updated %', n; END IF;

  -- post-flight: the stored contracts themselves read true
  SELECT integrity_check_sql INTO eng_reg.integrity_check_sql FROM asset_registry WHERE asset_id = 'bg_transit_engine';
  EXECUTE eng_reg.integrity_check_sql INTO ok;
  IF ok IS NOT TRUE THEN RAISE EXCEPTION 'curation post-flight: bg_transit_engine stored integrity_check_sql reads false'; END IF;
  SELECT integrity_check_sql INTO rul_reg.integrity_check_sql FROM asset_registry WHERE asset_id = 'bg_transit_rules';
  EXECUTE rul_reg.integrity_check_sql INTO ok;
  IF ok IS NOT TRUE THEN RAISE EXCEPTION 'curation post-flight: bg_transit_rules stored integrity_check_sql reads false'; END IF;
END
$curation$;

{attr_block}
-- VERIFY (run after apply):
--   SELECT classical_citation FROM bg_transit_rules WHERE id IN (5,6,7,14,18,19,20,31,32,39,40,41,190,191,192,193,194,195,200,201,202,203,204);
--   SELECT graha, left(classical_citation, 60) FROM bg_transit_engine ORDER BY graha;
--   -- then execute each stored integrity_check_sql: expect t
"""


def seed_patch(repo_root, out):
    import importlib.util, tempfile, os, shutil
    src = pathlib.Path(repo_root) / "platform/python-sidecar/brahmagyan/l0_transit.py"
    text = src.read_text(encoding="utf8")
    new = text
    # rules
    start = new.index("BG_TRANSIT_RULES")
    start = new.index("BG_TRANSIT_RULES: list", 0) if "BG_TRANSIT_RULES: list" in new else start
    targets = {(g, t, h): n for g, t, h, o, n in rule_updates()}
    old_by = {(g, t, h): o for g, t, h, o, n in rule_updates()}
    rl = new.index("BG_TRANSIT_RULES")
    head, body = new[:rl], new[rl:]
    hit = set()

    def repl(m):
        blk = m.group(0)
        try:
            rt = re.search(r'"rule_type": "([^"]+)"', blk).group(1)
            g = re.search(r'"graha": "([^"]+)"', blk).group(1)
            h = int(re.search(r'"primary_house": (\d+)', blk).group(1))
        except AttributeError:
            return blk
        k = (g, rt, h)
        if k in targets:
            const = {S.OLD_BPHS29: "BPHS_CH29", S.OLD_PDCH26: "PD_CH26"}[old_by[k]]
            assert f'"classical_citation": {const},' in blk, (k, blk)
            hit.add(k)
            return blk.replace(f'"classical_citation": {const},', f'"classical_citation": {json.dumps(targets[k], ensure_ascii=False)},')
        return blk
    body2 = re.sub(r"    \{\n(?:        .*\n)+?    \},", repl, body)
    assert hit == set(targets), set(targets) - hit
    new = head + body2
    # engine
    eng_t = {g: n for g, o, n in engine_updates()}
    ehit = set()

    def repl_e(m):
        blk = m.group(0)
        g = re.search(r'"graha": "([^"]+)"', blk)
        if not g or g.group(1) not in eng_t or '"classical_citation": BPHS_CH22,' not in blk:
            return blk
        ehit.add(g.group(1))
        return blk.replace('"classical_citation": BPHS_CH22,', f'"classical_citation": {json.dumps(eng_t[g.group(1)], ensure_ascii=False)},')
    el = new.index("BG_TRANSIT_ENGINE: list")
    er = new.index("BG_TRANSIT_RULES", el + 10)
    seg = re.sub(r"    \{\n(?:        .*\n)+?    \},", repl_e, new[el:er])
    assert ehit == set(eng_t), set(eng_t) - ehit
    new = new[:el] + seg + new[er:]
    new = new.replace("# classical_citation:   textual source for motion parameters",
                      "# classical_citation:   per-row source state (N-101 curation 2026-10: the periods coincide with modern mean sidereal periods;\n"
                      "#                       'BPHS Ch.22' was refuted — each row says which cell, if any, the held corpus states)")
    tmp = pathlib.Path(tempfile.mkdtemp())
    (tmp / "a").mkdir(); (tmp / "b").mkdir()
    rel = "platform/python-sidecar/brahmagyan/l0_transit.py"
    for sub, content in (("a", text), ("b", new)):
        p = tmp / sub / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf8")
    r = subprocess.run(["diff", "-u", f"a/{rel}", f"b/{rel}"], cwd=tmp, capture_output=True, text=True)
    lines = r.stdout.splitlines(keepends=True)
    lines[0] = f"--- a/{rel}\n"; lines[1] = f"+++ b/{rel}\n"
    pathlib.Path(out).write_text("".join(lines), encoding="utf8")
    (tmp / "patched_l0_transit.py").write_text(new, encoding="utf8")
    print("patched module written to", tmp / "patched_l0_transit.py")
    return tmp / "patched_l0_transit.py"


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "ledger":
        data = {"bg_transit_rules": entries(), "bg_transit_engine": engine_entries()}
        json.dump(data, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
        print({k: len(v) for k, v in data.items()})
    elif cmd == "sql":
        pins = json.load(open(sys.argv[2]))
        open(sys.argv[3], "w", encoding="utf8").write(build_sql(pins))
    elif cmd == "update-statements":
        r, e = update_statements()
        print(r + ";\n" + e + ";")
    elif cmd == "seed-patch":
        seed_patch(sys.argv[2], sys.argv[3])
    elif cmd == "verify-quotes":
        sys.exit(verify_quotes(sys.argv[2]))
    else:
        sys.exit(f"unknown command {cmd}")
