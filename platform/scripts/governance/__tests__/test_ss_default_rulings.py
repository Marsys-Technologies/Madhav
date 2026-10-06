"""test_ss_default_rulings.py -- SS 2026-10-05 defaults (1) K2 accepts a long ruling / adjudication id, (3) `no_table` no-table-no-prose, (4) the prose_none transcription cap is 80.
Offline: pure functions, the committed declarations and the real writers."""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

NA, ND = ac.NA, ac.NO_DET
DECL = ac.load_asset_declarations()


# ───────────────────────── (1) the K2 shape (review MED 2 / MED 3: closed long prefixes, a real date, the number after the final prefix dash) ─────────────────────────

@pytest.mark.parametrize("v", ["ADJUDICATION-9_2026-08-01", "ADJUDICATION-1_2026-01-01", "RULING-12_2026-10-05", "DVA-58_2026-07-30", "ADJUDICATION-9_2028-02-29", "RULING-1_2000-02-29", "N-150", "N-72a", "D-4", "F-2", "N156", "N-156", "D-2"])
def test_k2_accepts_the_declared_shapes(v):
    assert ac._k2_problem(v) is None, v
    assert ac._K2_ID_RE.fullmatch(v)


@pytest.mark.parametrize("v", [
    "RATIFIED-5", "NOTAPPLICABLE-3", "XXXXXXXXXX-3", "ABCDEFGHIJKLMNOPQRSTUVWXYZ-9",                                      # a long word + dash + digit is no id
    "ADJUDICATION-9", "ADJUDICATION-9_2026-08-01x", "ADJUDICATION-9_2026-8-1", "adjudication-9_2026-08-01", "ADJUDICATION9_2026-08-01",     # the long form is exact: closed upper-case prefix, dash, number, _YYYY-MM-DD
    "ADJUDICATION-9_2026-13-45", "ADJUDICATION-9_2026-02-30", "ADJUDICATION-9_2026-04-31", "ADJUDICATION-9_2027-02-29", "ADJUDICATION-9_2026-00-10", "ADJUDICATION-9_2026-01-00",   # a real calendar date
    "ADJUDICATION-0_2026-08-01", "RULING-000_2026-08-01",                                                                  # zero number, long form
    "DVA-1_2026-8-1", "RULING-1_2026-02-30x", "DVA-5_2025-13-01x", "RULING-1_2026-02-30", "DVA-5_2025-13-01", "RULING-1_2026-04-31", "DVA-2_2026-00-00", "RULING-1_2100-02-29", "RULING-1_2026-02-29",   # RULING / DVA fit the short shape too: only the dated long form is accepted
    "DVA-58", "DVA58", "RULING-3", "RULING3",
    "N-0", "XXX-000", "A1-0", "N1-0", "ABC1X2-0", "A9-00", "Z99-0",                                                        # zero number, short form: a digit in the prefix never defeats it
    "TBD-1", "tbd-1", "TODO1", "none-3", "pending-7", "ratified", "adjudication", "Phaladeepika339", "ADJUDICATION 9", "", "9-ADJ", None, 5,
])
def test_k2_still_refuses_what_it_refused_and_the_new_cases(v):
    assert ac._k2_problem(v) is not None, v


def test_the_number_is_read_after_the_final_prefix_dash():
    assert ac._k2_parts("A1-0")[:2] == ("A1", 0) and ac._k2_parts("ABC1X2-7")[:2] == ("ABC1X2", 7) and ac._k2_parts("N150")[:2] == ("N", 150)
    assert ac._k2_parts("N-72a")[:2] == ("N", 72) and ac._k2_parts("ADJUDICATION-9_2026-08-01") == ("ADJUDICATION", 9, (2026, 8, 1))
    assert ac._k2_parts("N1-5")[:2] == ("N1", 5)                                                                 # the 1 inside the prefix is not the number


def test_every_k2_id_the_committed_declarations_use_still_passes():
    ids = set()
    for a, e in DECL.items():
        s = e.get("source")
        if isinstance(s, dict) and s.get("kind") == "K2":
            ids.add(s["decision_id"])
        if isinstance((e.get("carriage") or {}).get("ruling"), str):
            ids.add(e["carriage"]["ruling"])
    assert {"N-156"} <= ids and "ADJUDICATION-9_2026-08-01" not in ids          # SS 2026-10-06: ADJUDICATION-9 is a document, not a decision in any register: its K2 declaration is withdrawn
    assert all(ac._k2_problem(i) is None for i in ids), ids


def test_the_sql_mirror_of_the_k2_shape_matches_the_python_shape_and_reads_the_number_after_the_final_dash():
    import re
    rx = ac._k2_regex()
    pyrx = re.compile(rx)
    assert rx.startswith("^(?:") and rx.endswith("$") and "ADJUDICATION|RULING|DVA" in rx
    for v in ("ADJUDICATION-9_2026-08-01", "RULING-3_2026-12-31", "DVA-1_2026-04-30", "ADJUDICATION-9_2028-02-29", "N-150", "N-72a", "D-4"):
        assert pyrx.fullmatch(v), v
    for v in ("RATIFIED-5", "NOTAPPLICABLE-3", "XXXXXXXXXX-3", "ADJUDICATION-9", "ADJUDICATION-9_2026-13-45", "ADJUDICATION-9_2026-04-31", "ADJUDICATION-9_2026-02-30", "ADJUDICATION-9_2026-08-01x",
              "ADJUDICATION-9_2026-00-10", "adjudication-9_2026-08-01"):
        assert not pyrx.fullmatch(v), v
    ok = ac._k2_sql_ok("x")
    assert "'^[A-Za-z][A-Za-z0-9]{0,5}-[0-9]'" in ok and "-([0-9]+)" in ok and "(?:ADJUDICATION|RULING|DVA)-[0-9]" in ok          # the dash-aware number read: A1-0 is 0, not 1


def test_bg_kota_chakra_rings_is_an_unverified_transcription_with_an_unsourced_source_and_never_reads_pass(monkeypatch):
    # SS ruling 2026-10-06: the ring partition's own citation says "NOT YET traced to a primary ingested classical text", so it is an unverified transcription (D1 ceiling), not a K2 ratification:
    # ADJUDICATION-9 is a document, not a decision in any register, and its K2 declaration is withdrawn. The closest existing source form is a K1 citation column declared `unsourced`
    # (CITATION_CAPPED_STATES: never a PASS; the cap reads NO_DETECTOR, a FAIL needs a detector change).
    e = DECL["bg_kota_chakra_rings"]
    assert e["carriage"]["nature"] == "unverified_transcription" and e["carriage"]["applies"] == "D1"
    assert e["source"]["level"] == "row" and e["source"]["columns"] == [{"column": "citation", "kinds": ["K1"]}] and e["source"]["citation_state"] == "unsourced"
    assert ac.source_kinds(e["source"]) == {"K1"} and "decision_id" not in e["source"]
    assert ac.source_declaration_problem(e["source"], e) is None
    monkeypatch.setattr(ac, "scalar", lambda q: json.dumps({"citation": "text"} if "pg_attribute" in q else dict(rows=27, lacking=0, sample=[])))
    got = ac.source_declared_check("bg_kota_chakra_rings", e["source"], "bg_kota_chakra_rings", ["table_version", "ring_position", "ring_name", "citation"], rows=27, owned=["bg_kota_chakra_rings"], keys=[])
    assert got["Ldgr.source_presence"]["v"] == ND and got["Ldgr.source_presence"]["citation_state"] == "unsourced"      # never a PASS
    cc = ac.carriage_declared_checks("bg_kota_chakra_rings", e["carriage"], "bg_kota_chakra_rings", column_types=None, prose_columns=[], source=e["source"])
    assert [(c, cc[c]["v"], cc[c]["cause"]) for c in ("Carr.D1", "Carr.D2", "Carr.D3")] == [("Carr.D1", NA, "transcription-not-verified"), ("Carr.D2", NA, "no-per-witness-values"), ("Carr.D3", NA, "not-the-declared-carriage")]


def test_the_class_priors_and_lifetime_counts_declare_no_source_and_no_carriage_after_the_ss_ruling():
    # SS ruling 2026-10-06: their rows are hand-written literals, not generated, and no decision ratifies them: the K3 sources are removed, and not_a_transcription (checked against a K2 / K3 / LEDGER
    # source) goes with them. Fix-list note: priors need a source or an explicit ratification with reasoning (an acharya-level item, not engine).
    for aid in ("bg_class_priors", "bg_class_lifetime_counts"):
        assert "source" not in DECL[aid] and not DECL[aid]["carriage"].get("nature"), aid


def test_bg_texts_is_an_unverified_transcription_not_a_single_derivation_after_the_ss_ruling():
    e = DECL["bg_texts"]
    assert (e["carriage"]["applies"], e["carriage"]["nature"]) == ("D1", "unverified_transcription") and "machine translation" in e["carriage"]["why"]
    assert e["source"]["columns"] == [{"column": "source_citation", "kinds": ["K1"]}] and [t["table"] for t in e["produced_tables"]] == ["classical_text_chunks", "classical_texts"]      # the writer also upserts classical_texts (bg_texts.py:360)


def test_the_vidhi_assets_keep_their_n156_k2_source_as_ruled():
    for aid in ("bg_vidhi_floors", "bg_vidhi_primitives"):
        assert DECL[aid]["source"]["kind"] == "K2" and DECL[aid]["source"]["decision_id"] == "N-156" and DECL[aid]["carriage"]["nature"] == "not_a_transcription", aid


# ───────────────────────── (3) no_table: the shape ─────────────────────────

SVC = {"kind": "service", "has_writer": False, "prose_fields": None, "no_table": dict(why="the service owns no table and no count_sql table, so no column could carry prose",
                                                                                   evidence="platform/scripts/seed/asset_registry_seed.ts:465")}


def test_the_two_services_declare_it_and_every_declaration_is_well_formed():
    assert sorted(a for a, e in DECL.items() if e.get("no_table")) == ["bg_ephemeris_engine", "bg_panchanga"]
    assert ac.no_table_problem(SVC) is None and ac.no_table_problem({}) is None


@pytest.mark.parametrize("mut", [
    dict(no_table="text"), dict(no_table=dict(why="x")), dict(no_table=dict(SVC["no_table"], extra=1)), dict(no_table=dict(SVC["no_table"], why="short")),
    dict(no_table=dict(SVC["no_table"], why="the service has no storage of any kind whatsoever here")), dict(no_table=dict(SVC["no_table"], why="the service owns no table, tbd later")),
    dict(no_table=dict(SVC["no_table"], evidence="unverified:the seed was read")), dict(no_table=dict(SVC["no_table"], evidence="platform/nope.ts:1")),
    dict(no_table=dict(SVC["no_table"], evidence="platform/scripts/seed/asset_registry_seed.ts")),
    dict(has_writer=True), dict(has_writer=None), dict(kind="data"), dict(prose_fields=["citation_human"]), dict(prose_none=dict(why="x")),
])
def test_a_malformed_or_inconsistent_declaration_is_refused(mut):
    assert ac.no_table_problem(dict(SVC, **mut))


# ───────────────────────── the block and the records ─────────────────────────

def _block(**kw):
    base = dict(entry=SVC, asset_kind="service", registry_has_writer=False, target_table=None, count_tables=[], register_files=0, register_mentions=[])
    base.update(kw)
    return ac.no_table_block(base.pop("entry"), base.pop("asset_kind"), base.pop("registry_has_writer"), base.pop("target_table"), base.pop("count_tables"), base.pop("register_files"), base.pop("register_mentions"))


def test_the_agreeing_block_releases_exactly_the_seven_checks():
    recs = ac.no_table_records("bg_x", SVC, _block())
    assert sorted(recs) == sorted(ac.NO_TABLE_CRITERIA) and len(recs) == 7
    assert all(r["v"] == NA and r["cause"] == "no-table-no-prose" and r["no_table"]["declared"] is True for r in recs.values())
    assert ac.no_table_records("bg_x", {}, _block()) == {}


@pytest.mark.parametrize("kw,what", [
    (dict(asset_kind="data"), "registry asset_kind"), (dict(registry_has_writer=True), "registry says has_writer"), (dict(target_table="t"), "target_table"),
    (dict(count_tables=["t"]), "count_sql"), (dict(register_files=1), "@register"), (dict(register_mentions=["w.py"]), "register( call"),
    (dict(entry=dict(SVC, has_writer=None)), "declared"), (dict(entry=dict(SVC, kind="data")), "declared"),
])
def test_any_disagreeing_fact_is_a_noderector_never_a_release(kw, what):
    recs = ac.no_table_records("bg_x", SVC if "entry" not in kw else kw["entry"], _block(**kw))
    assert all(r["v"] == ND and r["declaration_disagreements"] for r in recs.values()), recs
    assert any(what in r["measured"] or what in r["declaration_disagreements"][0] for r in recs.values())


def test_the_rollup_honours_only_a_record_that_carries_the_agreeing_block():
    recs = ac.no_table_records("bg_x", SVC, _block())
    def chk(crit, rec):
        return next(c for c in ac.rollup_asset("L0", {crit: rec})[crit.split(".")[0]]["checks"] if c["criterion"] == crit)
    for crit, rec in recs.items():
        assert chk(crit, rec)["v"] == NA, crit
        forged = dict(rec, no_table=dict(rec["no_table"], target_table="t"))
        assert chk(crit, forged)["v"] == ND, crit
        assert chk(crit, dict(rec, no_table=None))["v"] == ND, crit
        assert ac.no_table_na_problem(crit, forged) and ac.no_table_na_problem(crit, rec) is None
    assert ac.no_table_na_problem("Dens.served", dict(v=NA, cause="no-table-no-prose")) is None          # the cause is registered only for the seven


def test_the_rule_rows_and_causes_exist_for_the_seven_and_only_the_seven():
    for crit in ac.NO_TABLE_CRITERIA:
        assert "no-table-no-prose" in ac.NA_CAUSES[crit]
        assert ac.NA_RULE_DECISIONS[f"{crit}#measured:no-table-no-prose"].startswith("SS 2026-10-05 no-table-no-prose")
    assert sorted(c for c, v in ac.NA_CAUSES.items() if "no-table-no-prose" in v) == sorted(ac.NO_TABLE_CRITERIA)
    ac.validate_na_rule_decisions()


def test_dens_and_the_other_gates_of_a_service_are_untouched():
    assert "Dens.served" not in ac.NO_TABLE_CRITERIA and not any(c.startswith(("Build", "Carr", "Ldgr", "Earn")) for c in ac.NO_TABLE_CRITERIA)


def test_the_real_services_agree_with_the_registry_facts_and_the_scan():
    reg = ac.registered_ids("")
    for aid in ("bg_ephemeris_engine", "bg_panchanga"):
        blk = ac.no_table_block(DECL[aid], "service", False, None, [], len(reg.get(aid) or []), ac.register_call_mentions(aid))
        assert ac.no_table_block_problem(blk) is None, (aid, blk)


def test_a_table_owning_asset_that_declares_no_table_is_contradicted_not_released():
    blk = ac.no_table_block(dict(SVC, kind="service"), "data", True, "bg_texts", ["bg_texts"], 1, [])
    assert all(r["v"] == ND for r in ac.no_table_records("bg_texts", SVC, blk).values())


# ───────────────────────── (4) the transcription cap ─────────────────────────

def test_the_cap_is_80_and_the_two_large_seed_assets_no_longer_declare_their_entries():
    assert ac.PROSE_NONE_MAX_TRANSCRIPTIONS == 80 and ac.PROSE_NONE_MAX_IDENTIFIERS == 32
    for aid in ("bg_nakshatra", "bg_reference"):                                          # SS audit 2026-10-06: their 51 / 60 entries covered composed f-string cross-products and could not be shown true
        assert DECL[aid].get("prose_none") is None and DECL[aid]["prose_fields"] is None, aid
    pn = DECL["bg_prashna_rules"]["prose_none"]
    assert len(pn["transcription_columns"]) == 24 and ac.prose_none_problem(DECL["bg_prashna_rules"]) is None
    big = copy.deepcopy(DECL["bg_prashna_rules"])
    tc = big["prose_none"]["transcription_columns"]
    while len(tc) <= 80:
        tc.append(dict(tc[0], column=f"extra_{len(tc)}", table="t"))
    assert "list of 1 to 80" in ac.prose_none_problem(big)


def test_the_k2_date_is_real_in_python_and_in_the_sql_mirror_for_every_day_of_220_years():
    import datetime as dt
    import re
    pyrx = re.compile(ac._k2_regex())
    bad = []
    for y in range(1890, 2110):
        for m in range(1, 13):
            for d in range(1, 32):
                v = f"RULING-1_{y:04d}-{m:02d}-{d:02d}"
                try:
                    dt.date(y, m, d)
                    real = True
                except ValueError:
                    real = False
                if real != bool(pyrx.fullmatch(v)) or real != (ac._k2_problem(v) is None):
                    bad.append(v)
    assert bad == [], bad[:5]
    assert pyrx.fullmatch("RULING-1_2000-02-29") and pyrx.fullmatch("RULING-1_2024-02-29") and not pyrx.fullmatch("RULING-1_1900-02-29") and not pyrx.fullmatch("RULING-1_2100-02-29")


def test_the_sql_short_form_excludes_the_long_prefixes():
    import re
    pyrx = re.compile(ac._k2_regex())
    assert "(?!(?:ADJUDICATION|RULING|DVA)(?![A-Za-z]))" in ac._k2_regex()
    for v in ("DVA-58", "DVA58", "RULING-3", "RULING3", "DVA-1_2026-8-1", "DVA-5_2025-13-01"):
        assert not pyrx.fullmatch(v), v
    for v in ("N-150", "D-4", "F-2", "DVAX-3", "RULIN-3", "DVA-58_2026-07-30"):
        assert pyrx.fullmatch(v), v


def test_no_carriage_evidence_pointer_cites_a_decorator_a_docstring_a_comment_a_log_call_or_a_seed_asset_id_line():
    # SS audit 2026-10-06 (LOW): the 58 carriage pointers that cited an @register line, a docstring, a comment or a seed `asset_id:` line now cite the statement the claim rests on
    import ast
    import re
    bad = []
    for a, e in DECL.items():
        ev = (e.get("carriage") or {}).get("evidence")
        if not ev:
            continue
        path, line = ev.rsplit(":", 1)
        f = ac.ROOT / path
        text = f.read_text(encoding="utf-8").splitlines()[int(line) - 1].strip()
        if path.endswith(".ts"):
            if re.match(r"asset_id:", text) or text.startswith(("//", "*")):
                bad.append((a, ev, text[:60]))
            continue
        if text.startswith(("@register", "#", "logger.")) or "@register" in text and text.startswith(("*", "-", "Thin")):
            bad.append((a, ev, text[:60]))
            continue
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and n.body and isinstance(n.body[0], ast.Expr) \
                    and isinstance(getattr(n.body[0], "value", None), ast.Constant) and isinstance(n.body[0].value.value, str) and n.body[0].lineno <= int(line) <= n.body[0].end_lineno:
                bad.append((a, ev, "docstring"))
    assert bad == [], bad
