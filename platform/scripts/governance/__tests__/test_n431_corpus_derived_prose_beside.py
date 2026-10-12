"""test_n431_corpus_derived_prose_beside.py: SS N-457, `corpus_derived` BESIDE a declared `prose_fields` (the two modes of the form). Offline: no database, no sandbox process; the data reads, the parser run and the
writer source are the fake world of test_n431_corpus_derived_detector.py (the writer scan and the Null / Narr graders are the engine's REAL ones).

The ruling: "(B) allow corpus_derived BESIDE prose_fields. A corpus_derived PASS grounds Narr.agree, Narr.checkable and (with the golden test) Narr.fidelity_test ONLY. Null.* stay MEASURED and never become N/A
through corpus_derived. A test must prove that a parser-written stand-in keeps Null PARTIAL." Re-derivation proves REPRODUCIBILITY, not the absence of a placeholder: bg_rules' parser composes
`predicate_jsonb.$.description` and writes the words 'bhava' / 'subject' itself when a token is missing; the stored rows then equal the re-derived rows, faithfully.

THE TWO MODES (asset_census, the design note above `CORPUS_DERIVED_NA_CRITERIA`)
  MODE 1, prose_fields null: unchanged. A PASS reads Narr.agree, Narr.checkable, Narr.fidelity_test, Null.schema_default, Null.blank_rows N/A (cause corpus-derived); Narr.lint is untouched.
  MODE 2, prose_fields a non-empty list (every entry's column one of the COMPARED columns): a PASS reads ONLY Narr.agree and Narr.checkable N/A; Narr.fidelity_test (the normal fidelity_tests machinery),
  Narr.lint and both Null cells keep their OWN reading and are never N/A through this form; a mismatch reads Narr.agree FAIL only; an incomplete stage reads Narr.agree / Narr.checkable NO_DETECTOR only.
READING OF 'fidelity_test': the SS wording ("grounds ... with the golden test") is read in the STRICTER way: corpus_derived never makes Narr.fidelity_test N/A; the cell is earned (or not) by the declared
golden test through the existing machinery. A re-derivation is not a golden test of the sentence builder.

Each rule has a MUTATION PROOF below (`test_mutation_*`): the very assertion that guards the rule is run against a deliberately broken engine and must FAIL.
"""
from __future__ import annotations

import ast
import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_n431_corpus_derived_detector as dt  # noqa: E402
import test_n431_corpus_derived_form as ft  # noqa: E402

cdd = dt.cdd
PASS, FAIL, NO_DET, NA, PARTIAL = dt.PASS, dt.FAIL, dt.NO_DET, dt.NA, ac.PARTIAL
CELLS = dt.CELLS
BESIDE = ["Narr.agree", "Narr.checkable"]
NOT_BESIDE = [c for c in CELLS if c not in BESIDE]
NULL2 = ["Null.schema_default", "Null.blank_rows"]
PROSE = "predicate_jsonb.$.description"
AID = "bg_rules_fixture"

# ─────────────────────────── the fake world whose PARSER writes a stand-in word ('bhava') into the declared prose leaf ───────────────────────────
PARSER_STANDIN = dt.PARSER_SRC.replace('"extracted_by": "fake_v2",', '"extracted_by": "fake_v2", "predicate_jsonb": json.dumps({"type": "when_conditional", "description": "when %s in %s" % (body, "house 1" if n == 0 else "bhava")}),')
assert PARSER_STANDIN != dt.PARSER_SRC
TABLE_COLS = dt.TABLE_COLS + ["predicate_jsonb"]

WRITER_STANDIN = '''
import json

SQL = "INSERT INTO rules (rule_id, text_id, predicate_jsonb) VALUES (%(rule_id)s, %(text_id)s, %(predicate_jsonb)s)"


def _predicate(planet, house, sign_num):
    loc_desc = f"house {house}" if house else (f"sign {sign_num}" if sign_num else "bhava")
    return {"type": "when_conditional", "description": f"when {planet} in {loc_desc}"}


def run(conn, rows):
    for r in rows:
        conn.execute(SQL, {"rule_id": r["id"], "text_id": r["text_id"], "predicate_jsonb": json.dumps(_predicate(r["planet"], r["house"], r["sign"]))})
'''
WRITER_CLEAN = WRITER_STANDIN.replace('(f"sign {sign_num}" if sign_num else "bhava")', 'f"sign {sign_num}"')
assert WRITER_CLEAN != WRITER_STANDIN and "bhava" not in WRITER_CLEAN


@pytest.fixture()
def sworld(tmp_path):
    (tmp_path / "parser").mkdir()
    f = tmp_path / "parser" / "l0_fake.py"
    f.write_text(PARSER_STANDIN, encoding="utf-8")
    d = tmp_path / "parser" / "data.json"
    d.write_text('{"k": 1}', encoding="utf-8")
    return dict(root=tmp_path, file=f, data=d, sha=dt.sha(PARSER_STANDIN), data_sha=dt.sha('{"k": 1}'), fn=dt.load_parser(f))


def stored_rows(sworld, chunks=None):
    rows = dt.simulate_writer(sworld, chunks if chunks is not None else dt.mk_chunks())
    for r in rows:
        r["predicate_jsonb"] = json.loads(r["predicate_jsonb"])
    return rows


def entry2(sworld, prose=(PROSE,), **over):
    d = dt.decl_for(sworld)
    d["derived"]["json_columns"] = d["derived"]["json_columns"] + ["predicate_jsonb"]
    d.update(over)
    return {"prose_fields": list(prose) if prose is not None else None, "corpus_derived": d}


def writer_units(tmp_path, src):
    p = tmp_path / "fake_rules_writer.py"
    p.write_text(src, encoding="utf-8")
    return [dict(rel=p.name, path=p, tree=ast.parse(src), nodes=[ast.parse(src)], hop=0, via=p.name)]


def measure2(sworld, monkeypatch, tmp_path, entry=None, stored=None, writer=WRITER_STANDIN, runner=None, pin_check=None, apply_corpus=True, prose_checks_only=False):
    """`_measure_prose` on the fake world with the REAL prose_checks and the REAL writer scan over `writer` (source text). STUBBED: the psql reads (row counts per prose entry: 3 checkable rows, none blank; the
    catalog), the corpus_derived data reads (FakeDB) and the sandbox (the fake runner); the writer scope is the in-memory source."""
    chunks = dt.mk_chunks()
    entry = entry or entry2(sworld)
    rows = stored if stored is not None else stored_rows(sworld, chunks)
    db = dt.FakeDB(rows, chunks)
    db.cols["rules"] = list(TABLE_COLS)
    units = writer_units(tmp_path, writer)
    monkeypatch.setattr(ac, "_cd_default_fetch", lambda: db)
    monkeypatch.setattr(ac, "_cd_default_runner", lambda: runner or dt.make_runner(sworld))
    monkeypatch.setattr(ac, "_cd_default_normaliser", lambda: dt.normaliser)
    monkeypatch.setattr(ac, "_cd_default_pin_check", lambda: pin_check or (lambda e: None))
    monkeypatch.setattr(ac, "_cd_default_allowed", lambda: dt.allowed_for(sworld))
    monkeypatch.setattr(ac, "ROOT", sworld["root"])
    monkeypatch.setattr(ac, "_delegation_scope", lambda aid, files, hops=None, strict=False: (units, []))
    monkeypatch.setattr(ac, "writer_scan_scope", lambda aid, files: (units, []))
    monkeypatch.setattr(ac, "_group_counts", lambda groups, r, own, shared: {e: dict(blank=0, checkable=3, scope="table") for es in groups.values() for e in es})
    if not apply_corpus:
        monkeypatch.setattr(ac, "corpus_derived_applies", lambda decl: False)
    cat = dict(exists={"rules"}, cols={"rules": list(TABLE_COLS)}, types={"rules": {c: ("jsonb" if c.endswith("_jsonb") or c == "extraction_pass_log" else "text") for c in TABLE_COLS}},
               defaults={"rules": {}}, udts=None, keys=None)
    return ac._measure_prose(AID, entry, dict(target_table="rules"), ["fake_rules_writer.py"], cat, [], set(), (), set())


# ═════════════════════════════ 1. the validator ═════════════════════════════

def _validator_facts(root):
    """The assertions about the load-time validator (a function so that the mutation proofs can run the SAME assertions against a broken validator)."""
    repo = ft._fixture_repo(root)
    cd = ft._cd(repo)
    ok = lambda **kw: ac.corpus_derived_problem(ft._entry(cd, **kw))                       # noqa: E731
    assert ok() is None                                                                    # mode 1: prose_fields null (unchanged)
    assert ok(prose_fields=["body"]) is None and ok(prose_fields=["predicate_jsonb.$.description"]) is None        # mode 2: the combination is allowed
    assert ok(prose_fields=["rule_id", "extraction_pass_log.$.x"]) is None                 # a key column / the cite column are compared columns
    bad = ok(prose_fields=["created_at"])                                                    # an ignored column is NOT compared
    assert bad and bad.startswith("corpus_derived") and "created_at" in bad and "cannot be grounded" in bad
    bad = ok(prose_fields=["body", "created_at.$.d"])
    assert bad and "created_at" in bad and "cannot be grounded" in bad
    bad = ok(prose_fields=["_quality"])                                                      # an ephemeral derived key is dropped before the comparison
    assert bad and "_quality" in bad and "drop_keys" in bad and "cannot be grounded" in bad
    cd_ign = ft._cd(repo, ignore_columns=["created_at", "updated_at"])
    bad = ac.corpus_derived_problem(ft._entry(cd_ign, prose_fields=["updated_at"]))
    assert bad and "updated_at" in bad and "cannot be grounded" in bad
    return True


def test_the_validator_allows_the_combination_and_refuses_a_prose_column_the_rederivation_does_not_compare(tmp_path):
    assert _validator_facts(tmp_path) is True


def test_prose_fields_empty_and_malformed_entries_stay_refused_and_the_other_exclusivities_hold_in_mode_2(tmp_path):
    repo = ft._fixture_repo(tmp_path)
    cd = ft._cd(repo)
    assert "prose_fields null" in ac.corpus_derived_problem(ft._entry(cd, prose_fields=[]))               # [] is the prose_none account: refused, as before N-457
    for bad in ("two words", "a.b", "col.$", 7):
        msg = ac.corpus_derived_problem(ft._entry(cd, prose_fields=["body", bad]))
        assert msg and msg.startswith("corpus_derived") and "not a prose entry" in msg, (bad, msg)
    for k in ("prose_none", "prose_coupling", "curated_corpus", "writer_constant_phrases", "no_table"):
        msg = ac.corpus_derived_problem(ft._entry(cd, prose_fields=["body"], **{k: {"x": 1}}))
        assert msg and k in msg and msg.startswith("corpus_derived")
    assert ac.corpus_derived_problem(ft._entry(cd, prose_fields=["body"], produced_tables=[{"table": "other_table"}]))      # the produced_tables rule applies in mode 2 too


def test_the_real_bg_rules_declaration_with_its_prose_column_loads_through_the_generic_validator():
    doc = copy.deepcopy(json.loads((HERE.parent / "asset_declarations.json").read_text(encoding="utf-8")))
    e = doc["assets"]["bg_rules"]
    e["corpus_derived"] = ft._real_cd()
    e["prose_fields"] = [PROSE]
    e["evidence"] = dict(e["evidence"], prose_fields="platform/python-sidecar/brahmagyan/l0_rules.py:1609")
    ac.validate_declarations(doc)
    e.pop("fidelity_tests", None)                                                                         # the committed bg_rules declares golden tests that cover its real prose entry; this mutation replaces the entry
    e["prose_fields"] = ["created_at"]                                                                    # the real declaration ignores created_at
    with pytest.raises(ac.DeclarationsError, match=r"cannot be grounded"):
        ac.validate_declarations(doc)


def test_the_mode_helpers_read_one_column_set_everywhere():
    assert ac.corpus_derived_mode({"prose_fields": None}) == 1 and ac.corpus_derived_mode({"prose_fields": []}) == 1 and ac.corpus_derived_mode(None) == 1
    assert ac.corpus_derived_mode({"prose_fields": [PROSE]}) == 2
    assert ac.corpus_derived_prose_columns([PROSE, "predicate_jsonb.$.x", "body"]) == ["predicate_jsonb", "body"]
    assert ac.corpus_derived_prose_columns(None) == [] and ac.corpus_derived_prose_columns([]) == [] and ac.corpus_derived_prose_columns("x") == []
    for pf in (None, [], [PROSE], ["a", "a.$.b", "c.$.d.e"]):
        assert cdd.prose_columns_of({"prose_fields": pf}) == ac.corpus_derived_prose_columns(pf)
    assert cdd.prose_columns_of({"prose_fields": "x"}) is None and cdd.prose_columns_of({"prose_fields": [3]}) is None and cdd.prose_columns_of({"corpus_derived": {}}) == []
    assert ac.corpus_derived_applies({"corpus_derived": {}, "prose_fields": [PROSE]}) is True and ac.corpus_derived_applies({"corpus_derived": {}, "prose_fields": None}) is True
    assert ac.corpus_derived_applies({"corpus_derived": {}, "prose_fields": []}) is False and ac.corpus_derived_applies({"prose_fields": [PROSE]}) is False


# ═════════════════════════════ 2. the detector: the prose column must be a compared column ═════════════════════════════

def test_the_detector_block_names_the_compared_and_prose_columns(sworld):
    res, _ = _detect(sworld, entry2(sworld))
    assert res["v"] == PASS, res["measured"]
    b = res["block"]
    assert b["prose_columns"] == ["predicate_jsonb"] and "created_at" not in b["compared_columns"] and "predicate_jsonb" in b["compared_columns"]
    assert b["compared_columns"] == [c for c in TABLE_COLS if c != "created_at"]
    res1, _ = _detect(sworld, entry2(sworld, prose=None))
    assert res1["v"] == PASS and res1["block"]["prose_columns"] == []                                    # mode 1 carries an empty list


def _db(sworld, rows=None):
    chunks = dt.mk_chunks()
    db = dt.FakeDB(rows if rows is not None else stored_rows(sworld, chunks), chunks)
    db.cols["rules"] = list(TABLE_COLS)
    return db


def _detect(sworld, entry, rows=None, **kw):
    kw.setdefault("allowed", dt.allowed_for(sworld))
    kw["caps"] = {"full_scan_chunks": 0, **(kw.get("caps") or {})}
    db = _db(sworld, rows)
    return cdd.detect_corpus_derived(entry, fetch=db, runner=dt.make_runner(sworld), normaliser=dt.normaliser, repo_root=str(sworld["root"]), **kw), db


def test_a_declared_prose_column_the_run_does_not_compare_is_no_detector_declaration(sworld):
    for prose in (["created_at"], [PROSE, "no_such_column"]):                                              # an ignored column; a column the table does not have
        res, _ = _detect(sworld, entry2(sworld, prose=prose))
        assert res["v"] == NO_DET and res["stage"] == "declaration" and "cannot be grounded" in res["measured"], res
    res, _ = _detect(sworld, dict(entry2(sworld), prose_fields="predicate_jsonb"))
    assert res["v"] == NO_DET and res["stage"] == "declaration"


# ═════════════════════════════ 3. the cells ═════════════════════════════

def _base_cells(sworld, monkeypatch, tmp_path, **kw):
    """The cells with the corpus_derived overlay switched off: what prose_checks (and the writer scan) say on their own."""
    with monkeypatch.context() as m:
        return measure2(sworld, m, tmp_path, apply_corpus=False, **kw)


def _mode2_pass_facts(sworld, monkeypatch, tmp_path):
    got = measure2(sworld, monkeypatch, tmp_path, writer=WRITER_CLEAN)
    base = _base_cells(sworld, monkeypatch, tmp_path, writer=WRITER_CLEAN)
    assert sorted(got) == sorted(CELLS)
    assert sorted(c for c in CELLS if got[c]["v"] == NA) == sorted(BESIDE)                                  # exactly {Narr.agree, Narr.checkable} are N/A, nothing else
    for c in BESIDE:
        assert got[c]["cause"] == "corpus-derived" and ac.CORPUS_DERIVED_NA_TEXT_BESIDE_PROSE in got[c]["measured"]
        assert "compared columns" in got[c]["measured"] and "predicate_jsonb" in got[c]["measured"] and "re-ran the pinned parser" in got[c]["measured"]
        assert got[c]["corpus_derived"]["verified"] is True and got[c]["corpus_derived"]["prose_columns"] == ["predicate_jsonb"]
        assert ac.corpus_derived_na_problem(c, got[c]) is None
    for c in NOT_BESIDE:                                                                                    # Null.*, Narr.fidelity_test, Narr.lint: byte-for-byte what the own detectors said
        assert got[c] == base[c], c
        assert "corpus_derived" not in got[c]
    assert got["Narr.fidelity_test"]["v"] != NA and got["Narr.lint"]["v"] != NA
    assert all(got[c]["v"] != NA for c in NULL2)
    return got


def test_mode_2_pass_releases_exactly_narr_agree_and_narr_checkable(sworld, monkeypatch, tmp_path):
    got = _mode2_pass_facts(sworld, monkeypatch, tmp_path)
    assert [got[c]["v"] for c in NULL2] == [PASS, PASS]                                                    # a clean writer earns Null.* by the writer scan, not by corpus_derived
    assert all("writer_scan" in got[c] for c in NULL2)
    assert got["Narr.fidelity_test"]["v"] in (PARTIAL, NO_DET)                                             # no golden test is declared in this world: the machinery's own reading, never N/A
    assert [c for c, m in ac.CORPUS_DERIVED_CELL_MAP_BESIDE_PROSE.items() if m["PASS"] == "N/A"] == BESIDE and set(ac.CORPUS_DERIVED_CELL_MAP_BESIDE_PROSE) == set(BESIDE)


def _standin_facts(sworld, monkeypatch, tmp_path):
    """REQUIRED (SS N-457): the PARSER itself writes a stand-in word; stored rows == re-derived rows (corpus_derived PASS); prose_fields declared; the real Null grading over the writer SOURCE that contains the
    literal stand-in keeps Null.schema_default / Null.blank_rows PARTIAL: re-derivation did not launder it."""
    rows = stored_rows(sworld)
    assert any(r["predicate_jsonb"]["description"].endswith(" in bhava") for r in rows)                      # the stand-in really is in the stored prose
    got = measure2(sworld, monkeypatch, tmp_path, stored=rows, writer=WRITER_STANDIN)
    assert got["Narr.agree"]["v"] == NA and got["Narr.agree"]["corpus_derived"]["verified"] is True and got["Narr.agree"]["corpus_derived"]["mismatches"] == 0     # corpus_derived PASSED on it
    assert got["Narr.agree"]["corpus_derived"]["matched_rows"] == len(rows)
    for c in NULL2:
        r = got[c]
        assert r["v"] == PARTIAL, (c, r)                                                                    # NOT N/A and NOT PASS
        assert "writer scan NOT clean" in r["measured"] and "'bhava'" in r["measured"] and "literal_fallback" in r["measured"]
        assert "corpus_derived" not in r and "writer_scan" not in r
    return got


def test_a_stand_in_the_parser_itself_writes_keeps_both_null_cells_partial_although_corpus_derived_passes(sworld, monkeypatch, tmp_path):
    _standin_facts(sworld, monkeypatch, tmp_path)


def test_the_same_world_with_a_writer_that_has_no_stand_in_earns_null_pass_so_the_partial_above_is_the_stand_ins(sworld, monkeypatch, tmp_path):
    got = measure2(sworld, monkeypatch, tmp_path, stored=stored_rows(sworld), writer=WRITER_CLEAN)
    assert [got[c]["v"] for c in NULL2] == [PASS, PASS]


def test_the_rollup_never_reads_null_na_beside_prose_even_when_a_record_forges_it(sworld, monkeypatch, tmp_path):
    reg = _registered(monkeypatch)                                                                            # noqa: F841
    got = measure2(sworld, monkeypatch, tmp_path, stored=stored_rows(sworld), writer=WRITER_STANDIN)
    facts = {"declared_prose_fields": [PROSE]}
    r = ac.rollup_asset("L0", dict(got), facts)
    checks = {c["criterion"]: c for c in r["Null"]["checks"]}
    assert r["Null"]["v"] == PARTIAL and all(checks[c]["v"] == PARTIAL for c in NULL2)
    assert {c["criterion"]: c["v"] for c in r["Narr"]["checks"] if c["v"] == NA} == {"Narr.agree": NA, "Narr.checkable": NA}          # honoured: both carry the verified block and its prose columns
    forged = copy.deepcopy(got)
    for c in NULL2:
        forged[c] = dict(ac._na("forged", "corpus-derived"), corpus_derived=copy.deepcopy(got["Narr.agree"]["corpus_derived"]))
    r2 = ac.rollup_asset("L0", forged, facts)
    for c in r2["Null"]["checks"]:
        assert c["v"] == NO_DET and "SS N-457" in c["reason"] and "never reads N/A through this form" in c["reason"], c
    r3 = ac.rollup_asset("L0", forged, None)                                                                  # even without the declaration facts: the block itself says prose_fields is declared
    assert all(c["v"] == NO_DET and "SS N-457" in c["reason"] for c in r3["Null"]["checks"])
    assert all(ac._na_released(c, forged[c], facts=facts) is False for c in NULL2) and all(ac._na_released(c, got[c], facts=facts) is True for c in BESIDE)


def _registered(monkeypatch):
    causes, rules = dict(ac.NA_CAUSES), dict(ac.NA_RULE_DECISIONS)
    for c, add in ac.CORPUS_DERIVED_NA_CAUSES.items():
        causes[c] = tuple(causes[c]) + tuple(add)
    rules.update(ac.CORPUS_DERIVED_NA_RULE_DECISIONS)
    monkeypatch.setattr(ac, "NA_CAUSES", causes)
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", rules)


def _mismatch_facts(sworld, monkeypatch, tmp_path):
    rows = stored_rows(sworld)
    rows[0]["predicate_jsonb"]["description"] = "HAND-EDITED"
    got = measure2(sworld, monkeypatch, tmp_path, stored=rows, writer=WRITER_CLEAN)
    base = _base_cells(sworld, monkeypatch, tmp_path, stored=rows, writer=WRITER_CLEAN)
    assert got["Narr.agree"]["v"] == FAIL and "differs" in got["Narr.agree"]["measured"] and "predicate_jsonb" in got["Narr.agree"]["measured"] and "HAND-EDITED" not in json.dumps(got)
    for c in CELLS:
        if c != "Narr.agree":
            assert got[c] == base[c], c                                                                      # every other cell: its own detector's reading, not forced to NO_DETECTOR
    assert all(got[c]["v"] != NO_DET for c in NULL2)
    return got


def test_mode_2_mismatch_reads_narr_agree_fail_and_leaves_every_other_cell_to_its_own_detector(sworld, monkeypatch, tmp_path):
    _mismatch_facts(sworld, monkeypatch, tmp_path)


@pytest.mark.parametrize("stage", ["pin", "spawn", "run", "output"])
def test_mode_2_incomplete_stage_reads_narr_agree_and_checkable_no_detector_and_nothing_else(sworld, monkeypatch, tmp_path, stage):
    got = measure2(sworld, monkeypatch, tmp_path, writer=WRITER_CLEAN, runner=dt.make_runner(sworld, fail=stage))
    base = _base_cells(sworld, monkeypatch, tmp_path, writer=WRITER_CLEAN)
    for c in BESIDE:
        assert got[c]["v"] == NO_DET and f"stage '{stage}'" in got[c]["measured"]
    for c in NOT_BESIDE:
        assert got[c] == base[c], c


def test_mode_2_declaration_stage_failures_leave_the_null_cells_untouched(sworld, monkeypatch, tmp_path):
    got = measure2(sworld, monkeypatch, tmp_path, writer=WRITER_CLEAN, entry=entry2(sworld, prose=["created_at"]))
    base = _base_cells(sworld, monkeypatch, tmp_path, writer=WRITER_CLEAN, entry=entry2(sworld, prose=["created_at"]))
    assert all(got[c]["v"] == NO_DET and "stage 'declaration'" in got[c]["measured"] for c in BESIDE)
    assert all(got[c] == base[c] for c in NOT_BESIDE)


def _mode1_facts(sworld, monkeypatch, tmp_path):
    """MODE 1 is unchanged: prose_fields null -> the five cells N/A, Narr.lint untouched; FAIL -> Narr.agree FAIL and the other five NO_DETECTOR; an incomplete stage -> all six NO_DETECTOR."""
    ent = entry2(sworld, prose=None)
    got = measure2(sworld, monkeypatch, tmp_path, entry=ent, stored=stored_rows(sworld))
    assert sorted(c for c in CELLS if got[c]["v"] == NA) == sorted(dt.FIVE) and all(got[c]["cause"] == "corpus-derived" for c in dt.FIVE)
    assert all(ac.CORPUS_DERIVED_NA_TEXT in got[c]["measured"] and "compared columns" not in got[c]["measured"] for c in dt.FIVE)
    assert got["Narr.lint"]["v"] == NO_DET and "corpus_derived" not in got["Narr.lint"]
    assert all(got[c]["corpus_derived"]["prose_columns"] == [] for c in dt.FIVE)
    rows = stored_rows(sworld)
    rows[0]["body"] = "HAND-EDITED"
    bad = measure2(sworld, monkeypatch, tmp_path, entry=ent, stored=rows)
    assert bad["Narr.agree"]["v"] == FAIL and all(bad[c]["v"] == NO_DET and "unproven" in bad[c]["measured"] for c in CELLS[1:])
    inc = measure2(sworld, monkeypatch, tmp_path, entry=ent, stored=stored_rows(sworld), runner=dt.make_runner(sworld, fail="run"))
    assert all(inc[c]["v"] == NO_DET and "stage 'run'" in inc[c]["measured"] for c in CELLS)
    assert [c for c, m in ac.CORPUS_DERIVED_CELL_MAP.items() if m["PASS"] == "N/A"] == dt.FIVE
    assert ac.corpus_derived_mode(ent) == 1
    return True


def test_mode_1_prose_fields_null_is_unchanged(sworld, monkeypatch, tmp_path):
    assert _mode1_facts(sworld, monkeypatch, tmp_path) is True


# ═════════════════════════════ 4. the pure N/A check ═════════════════════════════

BLOCK2 = dict(ft.BLOCK, prose_columns=["predicate_jsonb"], compared_columns=["rule_id", "predicate_jsonb", "extraction_pass_log"])


def _na2(block=None, **over):
    return dict(v=ac.NA, cause="corpus-derived", measured="x", corpus_derived=dict(copy.deepcopy(BLOCK2 if block is None else block), **over))


def _na_check_facts():
    f2 = {"declared_prose_fields": [PROSE]}
    for crit in BESIDE:                                                                                      # mode 2: Narr.agree / Narr.checkable honoured with the coverage shown
        assert ac.corpus_derived_na_problem(crit, _na2()) is None and ac.corpus_derived_na_problem(crit, _na2(), f2) is None
    for crit in ("Null.schema_default", "Null.blank_rows", "Narr.fidelity_test"):                           # mode 2: a contradiction, from the block alone or from the declaration facts alone
        for rec, facts in ((_na2(), None), (_na2(), f2), (dict(v=ac.NA, cause="corpus-derived", measured="x", corpus_derived=copy.deepcopy(ft.BLOCK)), f2)):
            bad = ac.corpus_derived_na_problem(crit, rec, facts)
            assert bad and "SS N-457" in bad and crit in bad and "never reads N/A through this form" in bad, (crit, bad)
    for crit in BESIDE:
        for rec, facts, needle in ((_na2(prose_columns=["other"]), f2, "not the declared prose_fields columns"),                      # the block names other columns than the declaration
                                   (dict(v=ac.NA, cause="corpus-derived", measured="x", corpus_derived=copy.deepcopy(ft.BLOCK)), f2, "not the declared prose_fields columns"),   # a mode-1 block under a mode-2 declaration
                                   (_na2(compared_columns=["rule_id"]), None, "among the columns the re-derivation compared"),
                                   (_na2(compared_columns=None), None, "among the columns the re-derivation compared"),
                                   (_na2(prose_columns="predicate_jsonb"), None, "not a list of column names")):
            bad = ac.corpus_derived_na_problem(crit, rec, facts)
            assert bad and needle in bad, (crit, needle, bad)
    return True


def test_the_na_check_refuses_null_and_fidelity_na_beside_prose_and_a_block_that_does_not_cover_the_prose_column():
    assert _na_check_facts() is True


def _na_mode1_facts():
    """Mode 1 (unchanged): a block with no prose_columns and facts that declare no prose is honoured for all five cells, exactly as before N-457."""
    for crit in ac.CORPUS_DERIVED_NA_CRITERIA:
        assert ac.corpus_derived_na_problem(crit, ft._na()) is None
        assert ac.corpus_derived_na_problem(crit, ft._na(prose_columns=[]), {"declared_prose_fields": []}) is None
        assert ac.corpus_derived_na_problem(crit, ft._na(prose_columns=[]), {}) is None
        assert ac.corpus_derived_na_problem(crit, ft._na(), {"declared_prose_fields": []}) is None
        assert ac.corpus_derived_na_problem(crit, ft._na(), "not a dict") is None
    return True


def test_mode_1_na_check_is_unchanged():
    assert _na_mode1_facts() is True


def test_the_data_constants_keep_the_shape_the_revision_28_generator_reads():
    assert ac.CORPUS_DERIVED_NA_CRITERIA == ("Narr.agree", "Narr.checkable", "Narr.fidelity_test", "Null.schema_default", "Null.blank_rows")        # mode 1 still emits all five cause tuples
    assert ac.CORPUS_DERIVED_NA_CRITERIA_BESIDE_PROSE == ("Narr.agree", "Narr.checkable")
    assert set(ac.CORPUS_DERIVED_NA_CAUSES) == set(ac.CORPUS_DERIVED_APPLICABILITY_ADDITIONS) == set(ac.CORPUS_DERIVED_NA_CRITERIA)
    assert all(v == ("corpus-derived",) for v in ac.CORPUS_DERIVED_NA_CAUSES.values())
    assert set(ac.CORPUS_DERIVED_NA_RULE_DECISIONS) == {f"{c}#measured:corpus-derived" for c in ac.CORPUS_DERIVED_NA_CRITERIA}
    for crit, tail in ac.CORPUS_DERIVED_APPLICABILITY_ADDITIONS.items():
        assert isinstance(tail, str) and tail.startswith(" N-431 (REGISTRY_REVISION 28)") and f"{crit}#measured:corpus-derived" in tail and "SS N-457" in tail
        assert "Mode 1" in tail or "mode 1" in tail
        assert ("Mode 2 (SS N-457" in tail) == (crit in BESIDE)
        assert ("NEVER releases it" in tail) == (crit not in BESIDE)
    for crit, text in ac.CORPUS_DERIVED_NA_RULE_DECISIONS.items():
        assert text.startswith("SS N-431") and "SS N-457" in text
    assert all(tail in ac.CRITERION_REGISTRY[crit]["applicability"] and ac.CRITERION_REGISTRY[crit]["applicability"].count("N-457") == 1 for crit, tail in ac.CORPUS_DERIVED_APPLICABILITY_ADDITIONS.items())     # the ONE revision-28 bump merged every tail into the registry text (rev28_registry_edits.json)


def test_the_emitting_literal_slug_survives_for_the_na_cause_scan():
    src = (HERE.parent / "asset_census.py").read_text(encoding="utf-8")
    assert '_na(what, "corpus-derived")' in src and ac.CORPUS_DERIVED_CAUSE == "corpus-derived"


# ═════════════════════════════ 5. mutation proofs: each rule's assertion FAILS against a broken engine ═════════════════════════════

def _fails(fn, *a):
    with pytest.raises(AssertionError):
        fn(*a)


def test_mutation_a_null_cells_made_na_in_mode_2(sworld, monkeypatch, tmp_path):
    """(a) mode 2 releasing Null.* through the form (the MODE 1 map used for a mode 2 asset, or a map that lists Null.*): the cell facts fail, and so does the stand-in test."""
    with monkeypatch.context() as m:
        m.setattr(ac, "CORPUS_DERIVED_CELL_MAP_BESIDE_PROSE", dict(ac.CORPUS_DERIVED_CELL_MAP_BESIDE_PROSE, **{c: dict(PASS="N/A", FAIL=None, NO_DETECTOR="NO_DETECTOR") for c in NULL2}))
        _fails(_mode2_pass_facts, sworld, m, tmp_path)
        _fails(_standin_facts, sworld, m, tmp_path)
    with monkeypatch.context() as m:
        m.setattr(ac, "CORPUS_DERIVED_CELL_MAP_BESIDE_PROSE", ac.CORPUS_DERIVED_CELL_MAP)                      # the whole mode-1 table for a mode-2 asset
        _fails(_mode2_pass_facts, sworld, m, tmp_path)
        _fails(_standin_facts, sworld, m, tmp_path)
    with monkeypatch.context() as m:                                                                          # the N/A check no longer refuses a Null.* N/A beside prose
        m.setattr(ac, "_cd_na_mode_problem", lambda crit, blk, facts, pre: None)
        _fails(_na_check_facts)
    with monkeypatch.context() as m:                                                                          # a mismatch that forces Null.* to NO_DETECTOR (the mode-1 mapping) is also caught
        m.setattr(ac, "CORPUS_DERIVED_CELL_MAP_BESIDE_PROSE", ac.CORPUS_DERIVED_CELL_MAP)
        _fails(_mismatch_facts, sworld, m, tmp_path)


def test_mutation_b_fidelity_test_made_na_in_mode_2(sworld, monkeypatch, tmp_path):
    with monkeypatch.context() as m:
        m.setattr(ac, "CORPUS_DERIVED_CELL_MAP_BESIDE_PROSE", dict(ac.CORPUS_DERIVED_CELL_MAP_BESIDE_PROSE, **{"Narr.fidelity_test": dict(PASS="N/A", FAIL=None, NO_DETECTOR="NO_DETECTOR")}))
        _fails(_mode2_pass_facts, sworld, m, tmp_path)
    with monkeypatch.context() as m:                                                                          # a mode-2 N/A check that lets Narr.fidelity_test through
        real = ac._cd_na_mode_problem
        m.setattr(ac, "_cd_na_mode_problem", lambda crit, blk, facts, pre: None if crit == "Narr.fidelity_test" else real(crit, blk, facts, pre))
        _fails(_na_check_facts)


def test_mutation_c_prose_column_outside_the_compared_columns_accepted(sworld, monkeypatch, tmp_path):
    with monkeypatch.context() as m:
        m.setattr(ac, "_cd_prose_beside_problem", lambda pf, cd_canon: None)
        _fails(_validator_facts, tmp_path / "m1")
    with monkeypatch.context() as m:                                                                          # the validator that checks only ignore_columns but not the dropped derived keys
        real = ac._cd_prose_beside_problem
        m.setattr(ac, "_cd_prose_beside_problem", lambda pf, cd_canon: real(pf, dict(cd_canon, derived=dict(cd_canon["derived"], drop_keys=[]))))
        _fails(_validator_facts, tmp_path / "m2")
    with monkeypatch.context() as m:                                                                          # the validator that checks only the dropped keys but not ignore_columns
        real = ac._cd_prose_beside_problem
        m.setattr(ac, "_cd_prose_beside_problem", lambda pf, cd_canon: real(pf, dict(cd_canon, ignore_columns=[])))
        _fails(_validator_facts, tmp_path / "m3")
    # and the detector's own coverage check (the live column list)
    real_prose = cdd.prose_columns_of
    with monkeypatch.context() as m:
        m.setattr(cdd, "prose_columns_of", lambda entry: [])
        res, _ = _detect(sworld, entry2(sworld, prose=["created_at"]))
        assert res["v"] == PASS                                                                                # the mutant detector accepts an uncovered prose column ...
    res, _ = _detect(sworld, entry2(sworld, prose=["created_at"]))
    assert res["v"] == NO_DET and cdd.prose_columns_of is real_prose                                          # ... the real one refuses it


def test_mutation_d_mode_1_behaviour_changed(sworld, monkeypatch, tmp_path):
    with monkeypatch.context() as m:                                                                          # mode 1 stops releasing Null.blank_rows
        m.setattr(ac, "CORPUS_DERIVED_CELL_MAP", dict(ac.CORPUS_DERIVED_CELL_MAP, **{"Null.blank_rows": dict(PASS=None, FAIL="NO_DETECTOR", NO_DETECTOR="NO_DETECTOR")}))
        _fails(_mode1_facts, sworld, m, tmp_path)
    with monkeypatch.context() as m:                                                                          # mode 1 treated as mode 2 (the cells helper ignores the mode argument)
        real = ac.corpus_derived_cells
        m.setattr(ac, "corpus_derived_cells", lambda aid, res, mode=1: real(aid, res, 2))
        _fails(_mode1_facts, sworld, m, tmp_path)
    with monkeypatch.context() as m:                                                                          # the mode-1 N/A check starts demanding a prose_columns key / refusing Null.* without prose
        real = ac._cd_na_mode_problem
        m.setattr(ac, "_cd_na_mode_problem", lambda crit, blk, facts, pre: f"{pre}: mutant" if crit.startswith("Null.") else real(crit, blk, facts, pre))
        _fails(_na_mode1_facts)
    with monkeypatch.context() as m:                                                                          # mode 1 starts releasing Narr.lint
        m.setattr(ac, "CORPUS_DERIVED_CELL_MAP", dict(ac.CORPUS_DERIVED_CELL_MAP, **{"Narr.lint": dict(PASS="N/A", FAIL="NO_DETECTOR", NO_DETECTOR="NO_DETECTOR")}))
        _fails(_mode1_facts, sworld, m, tmp_path)


def test_mutation_stand_in_laundered_by_the_writer_scan_being_skipped(sworld, monkeypatch, tmp_path):
    """The stand-in test can fail: with a writer source WITHOUT the literal the Null cells earn PASS, so a 'PARTIAL' assertion over that world is false (the PARTIAL above is the stand-in's)."""
    with monkeypatch.context() as m:
        got = measure2(sworld, m, tmp_path, stored=stored_rows(sworld), writer=WRITER_CLEAN)
        assert [got[c]["v"] for c in NULL2] != [PARTIAL, PARTIAL]


# ═════════════════════════════ hygiene ═════════════════════════════

def test_the_changed_python_files_parse_under_the_311_grammar():
    for p in (HERE.parent / "asset_census.py", HERE.parent / "corpus_derived_detector.py", pathlib.Path(__file__)):
        ast.parse(p.read_text(encoding="utf-8"), feature_version=(3, 11))
