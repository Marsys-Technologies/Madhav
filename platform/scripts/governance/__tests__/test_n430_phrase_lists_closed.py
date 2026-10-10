"""test_n430_phrase_lists_closed.py: SS N-430 (part 2), the JSON-leaf constant-phrase form of `writer_constant_phrases` (SS N-279).

bo_chart_gestalt builds nine JSON columns from one builder and stores seven fixed pointer sentences in their `note` leaves; the writer scan attributes EVERY fixed literal it finds to EVERY declared entry of the
column family, so 8 JSON-leaf entries x 7 sentences = 56 findings, and the longest sentence is 233 characters. Three OPT-IN additions (a declaration that uses none of them reads and measures exactly as before):
  (a) `entry` may be a LIST of declared entries: one declaration states a sentence once, the check is still per (entry, literal);
  (b) `literal_max` (160 default, 400 ceiling): a longer sentence is allowed only where the declaration says so, still verbatim in the writer source;
  (c) `closed`: the DISTINCT string leaves stored at the entry (bounded, scoped to the measured chart) must be a subset of the declared literals; a stray value is a Narr.agree FAIL naming it and the Null cap stays.
Source-only tests plus the live closure on a throw-away PostgreSQL (the engine's own `label_read` and read scope, no mock of the SQL).
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
import _formgap_support as fs  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401

WS = ac._lint_module("writer_literal_scan")
POINTER = "pointer-only: follow signal_id to the signals table for content"
SPINE = "zoom spine: gestalt to domain signal ids to hubs"
ENTRIES = ["a_jsonb.$.note", "b_jsonb.$.note", "c_jsonb.$.note"]
SRC = f'''
SQL = """INSERT INTO gest (chart_id, a_jsonb, b_jsonb, c_jsonb) VALUES (%(chart_id)s, %(a_jsonb)s, %(b_jsonb)s, %(c_jsonb)s)"""
def build(chart_id):
    a = {{"signal_ids": [1], "note": "{POINTER}"}}
    b = {{"ids": [2], "note": "{SPINE}"}}
    c = {{"x": 1, "note": "a composed sentence " + "word " * 3}}
    return {{"chart_id": chart_id, "a_jsonb": a, "b_jsonb": b, "c_jsonb": c}}
def run(conn, chart_id):
    conn.execute(SQL, build(chart_id))
'''
EVID = "platform/python-sidecar/pipeline/orchestrator/writers/bo_chart_gestalt.py:158"
CHART_A, CHART_B = fs.CHART_A, fs.CHART_B


def _units(src, name="w.py"):
    tree = ast.parse(src)
    return [dict(rel=name, path=pathlib.Path(name), tree=tree, nodes=[tree], hop=0, via=name)]


def _scan(src=SRC, entries=ENTRIES):
    u = _units(src)
    cols = {ac.parse_prose_field(e)[0]: ["gest"] for e in entries}
    return WS.scan(u, list(entries), cols, is_placeholder=ac.ldgr_placeholder_py, sql_texts=ac._sql_texts, parse_entry=ac.parse_prose_field), u


def _item(literal, entry, **extra):
    return dict(file="w.py", entry=entry, form="constant_write", literal=literal,
                why="the note leaf carries one fixed pointer sentence of the builder by design, not a stand-in for a missing value", evidence=EVID, **extra)


def _records():
    return {c: dict(v=ac.PARTIAL, clean=True, measured="no schema default / no blank row; writer literal scan is not read") for c in ac.NULL_CHECKS}


def _apply(items, entries=ENTRIES, ctx_extra=None, src=SRC, out=None):
    ws, u = _scan(src, entries)
    out = out or _records()
    out.setdefault("Narr.agree", dict(v=ac.PARTIAL, measured="n"))
    ctx = dict(scan_result=ws, scan_units=u, units=u, **(ctx_extra or {}))
    ac._apply_constant_phrases(out, list(entries), ctx, dict(writer_constant_phrases=items))
    return out, ws


LIST_ITEMS = [_item(POINTER, ENTRIES), _item(SPINE, ENTRIES)]
FLAT_ITEMS = [_item(lit, e) for lit in (POINTER, SPINE) for e in ENTRIES]


# ───────────────────────── (a) one declaration for a list of entries ─────────────────────────

def test_the_scan_reports_every_fixed_sentence_on_every_entry():
    ws, _ = _scan()
    assert len(ws["problems"]) == len(ENTRIES) * 2 == 6 and {p["kind"] for p in ws["problems"]} == {"constant_write"}


def test_two_list_declarations_lift_what_six_single_entry_declarations_lift():
    out_l, _ = _apply(LIST_ITEMS)
    out_f, _ = _apply(FLAT_ITEMS)
    for c in ac.NULL_CHECKS:
        assert out_l[c]["v"] == ac.PASS and out_f[c]["v"] == ac.PASS
        pl = out_l[c]["writer_scan"]["constant_phrases"]
        assert len(pl) == 6 and all(x["verified"] is True and x["findings"] == 1 for x in pl)
        assert sorted((x["entry"], x["literal"]) for x in pl) == sorted((x["entry"], x["literal"]) for x in out_f[c]["writer_scan"]["constant_phrases"])
        assert ac.writer_scan_problem(out_l[c]) is None
    assert ac.writer_scan_earned("Null.blank_rows", out_l["Null.blank_rows"], out_l)


def test_without_the_list_form_two_declarations_leave_four_findings_open():
    out, _ = _apply([_item(POINTER, ENTRIES[0]), _item(SPINE, ENTRIES[0])])
    assert all(r["v"] == ac.PARTIAL and "outside every declared phrase" in r["measured"] and "writer_scan" not in r for r in (out[c] for c in ac.NULL_CHECKS))


def test_a_listed_entry_the_literal_does_not_flag_is_a_stale_declaration_naming_it():
    entries = ENTRIES[:2]                                           # the scan reads two entries; the declaration also names a third
    out, _ = _apply([_item(POINTER, ENTRIES), _item(SPINE, entries)], entries=entries)
    assert all(r["v"] == ac.NO_DET and "c_jsonb.$.note" in r["measured"] and "not one of the asset's declared prose_fields" in r["measured"] for r in (out[c] for c in ac.NULL_CHECKS))


def test_an_edited_literal_refuses_the_whole_list_declaration():
    out, _ = _apply([_item(POINTER, ENTRIES), _item(SPINE, ENTRIES)], src=SRC.replace(POINTER, POINTER + "!"))
    assert all(r["v"] == ac.NO_DET and "not present verbatim" in r["measured"] for r in (out[c] for c in ac.NULL_CHECKS))


# ───────────────────────── (b) the literal length rule ─────────────────────────

LONG = "fragility_class is None here by construction — a single ayanamsha's write cannot compare across ayanamshas. " * 2


def test_a_literal_past_160_characters_needs_a_declared_literal_max_and_stays_bounded():
    assert len(LONG) > 160
    assert ac.writer_constant_phrases_problem(dict(writer_constant_phrases=[_item(LONG, ENTRIES[0])]))
    assert ac.writer_constant_phrases_problem(dict(writer_constant_phrases=[_item(LONG, ENTRIES[0], literal_max=300)])) is None
    assert ac.writer_constant_phrases_problem(dict(writer_constant_phrases=[_item(LONG, ENTRIES[0], literal_max=len(LONG) - 1)]))          # the literal exceeds its own declared maximum
    assert ac.writer_constant_phrases_problem(dict(writer_constant_phrases=[_item("x" * 401, ENTRIES[0], literal_max=401)]))                 # the ceiling is fixed in the engine
    assert ac.writer_constant_phrases_problem(dict(writer_constant_phrases=[_item("x" * 400, ENTRIES[0], literal_max=400)])) is None
    for bad in (159, 401, True, "300", 200.0):
        assert ac.writer_constant_phrases_problem(dict(writer_constant_phrases=[_item("short phrase here", ENTRIES[0], literal_max=bad)])), bad


def test_a_long_literal_is_still_checked_verbatim_against_the_writer_source():
    src = SRC.replace(POINTER, LONG.replace('"', "'"))
    lit = LONG.replace('"', "'")
    out, _ = _apply([_item(lit, ENTRIES, literal_max=300), _item(SPINE, ENTRIES)], src=src)
    assert all(r["v"] == ac.PASS for r in (out[c] for c in ac.NULL_CHECKS))
    out, _ = _apply([_item(lit[:-1], ENTRIES, literal_max=300), _item(SPINE, ENTRIES)], src=src)           # one character short of the source
    assert all(r["v"] == ac.NO_DET and "not present verbatim" in r["measured"] for r in (out[c] for c in ac.NULL_CHECKS))


# ───────────────────────── the shape of the new keys ─────────────────────────

def test_the_new_keys_are_validated():
    ok = dict(writer_constant_phrases=[_item(POINTER, ENTRIES, closed=True), _item(SPINE, ENTRIES, closed=[ENTRIES[0]])])
    assert ac.writer_constant_phrases_problem(ok) is None
    for mut in (lambda d: d[0].update(entry=[]), lambda d: d[0].update(entry=[ENTRIES[0], ENTRIES[0]]), lambda d: d[0].update(entry=[ENTRIES[0], 3]),
                lambda d: d[0].update(entry=[f"c{i}_jsonb.$.note" for i in range(17)]), lambda d: d[0].update(entry=["  "]), lambda d: d[0].update(closed=False),
                lambda d: d[0].update(closed="yes"), lambda d: d[0].update(closed=[]), lambda d: d[0].update(closed=["z_jsonb.$.note"]), lambda d: d[0].update(form="optional_suffix"),
                lambda d: d[1].update(closed=[ENTRIES[0], ENTRIES[0]]), lambda d: d[0].update(extra=1),
                lambda d: d.append(_item(POINTER, ENTRIES[1]))):                       # the single entry is already inside the list declaration: listed twice
        d = copy.deepcopy(ok)
        mut(d["writer_constant_phrases"])
        assert ac.writer_constant_phrases_problem(d), d["writer_constant_phrases"][0]


def test_the_declaration_count_cap_and_the_expanded_cap_hold():
    many = [_item(f"fixed sentence number {i} of the builder", ENTRIES[0]) for i in range(ac.WRITER_CONSTANT_PHRASES_MAX + 1)]
    assert ac.writer_constant_phrases_problem(dict(writer_constant_phrases=many))
    wide = [_item(f"fixed sentence number {i} of the builder", [f"c{j}_jsonb.$.note" for j in range(16)]) for i in range(9)]         # 144 (entry, literal) pairs
    assert ac.writer_constant_phrases_problem(dict(writer_constant_phrases=wide))
    assert ac.writer_constant_phrases_problem(dict(writer_constant_phrases=wide[:8])) is None                                           # 128 pairs


def test_a_closed_entry_cannot_carry_an_optional_suffix():
    suffix = SRC.replace('c = {{', 'c = {{').replace('"note": "a composed sentence " + "word " * 3', '"note": "stem" + (" (more)" if chart_id else "")')
    ws, u = _scan(suffix)
    sfx = dict(file="w.py", entry=ENTRIES[2], form="optional_suffix", literal=" (more)", why="the optional suffix is a fixed phrase by design, not a stand-in", evidence=EVID)
    out = _records()
    out["Narr.agree"] = dict(v=ac.PARTIAL, measured="n")
    ac._apply_constant_phrases(out, ENTRIES, dict(scan_result=ws, scan_units=u, units=u), dict(writer_constant_phrases=[_item(POINTER, ENTRIES, closed=[ENTRIES[2]]), _item(SPINE, ENTRIES), sfx]))
    assert all(out[c]["v"] == ac.NO_DET and "cannot also carry an optional_suffix" in out[c]["measured"] for c in ac.NULL_CHECKS)


def test_a_tampered_closed_block_is_not_earned():
    block = {"constant_phrases": [dict(verified=True, file="w.py", entry="a", form="constant_write", literal="L1", findings=1), dict(verified=True, file="w.py", entry="a", form="constant_write", literal="L2", findings=1)]}
    assert ac.constant_phrases_block_problem(block["constant_phrases"], ["a"]) is None
    assert ac.constant_phrases_block_problem(block["constant_phrases"], ["a"], {"a": dict(verified=True, stored=["L1"])}) is None
    for bad in ({"a": dict(verified=True, stored=["L3"])}, {"a": dict(verified=True, stored=[])}, {"a": dict(verified=False, stored=["L1"])}, {"z": dict(verified=True, stored=["L1"])}, {}, {"a": "x"}):
        assert ac.constant_phrases_block_problem(block["constant_phrases"], ["a"], bad), bad


# ───────────────────────── the real bo_chart_gestalt writer ─────────────────────────

GEST = "bo_chart_gestalt"


def _gestalt_scan():
    d = ac.load_asset_declarations()[GEST]
    units, _ = ac.writer_scan_scope(GEST, ac.registered_ids("")[GEST])
    pf = list(d["prose_fields"])
    ws = WS.scan(units, pf, {ac.parse_prose_field(e)[0]: ["bodha_chart_gestalt"] for e in pf}, is_placeholder=ac.ldgr_placeholder_py, sql_texts=ac._sql_texts, parse_entry=ac.parse_prose_field)
    return d, pf, ws, units


def test_the_real_gestalt_writer_is_covered_by_seven_list_declarations_with_a_declared_literal_max():
    d, pf, ws, units = _gestalt_scan()
    jl = [e for e in pf if ".$." in e]
    lits = sorted({ast.literal_eval(p["text"].split("a literal: ", 1)[1]) for p in ws["problems"]}, key=len)
    assert len(ws["problems"]) == len(jl) * len(lits) == 56 and len(lits) == 7 and len(jl) == 8                   # the engine's own reading, not typed
    assert len(lits[-1]) > ac.WRITER_CONSTANT_PHRASES_LITERAL_DEFAULT and len(lits[-1]) <= ac.WRITER_CONSTANT_PHRASES_LITERAL_CEILING
    items = [dict(file="bo_chart_gestalt.py", entry=jl, form="constant_write", literal=x, why="the note leaf carries one fixed pointer sentence of the builder by design, not a stand-in for a missing value",
                  evidence=EVID, **(dict(literal_max=ac.WRITER_CONSTANT_PHRASES_LITERAL_CEILING) if len(x) > 160 else {})) for x in lits]
    assert ac.writer_constant_phrases_problem(dict(writer_constant_phrases=items)) is None and len(items) <= ac.WRITER_CONSTANT_PHRASES_MAX
    chk = ac.constant_phrases_check(items, pf, ws, units)
    assert chk["problems"] == [] and chk["left"] == [] and len(chk["flat"]) == 56 and set(chk["covered"].values()) == {1}
    no_max = [{k: v for k, v in i.items() if k != "literal_max"} for i in items]
    assert ac.writer_constant_phrases_problem(dict(writer_constant_phrases=no_max))                                 # the 233-character sentence needs its declared maximum


def test_the_committed_declarations_are_untouched_by_the_new_keys():
    decls = ac.load_asset_declarations()
    for aid in ("bo_karanajala", "bo_anveshana"):
        assert all(not (set(x) & set(ac.WRITER_CONSTANT_PHRASES_OPTIONAL)) and isinstance(x["entry"], str) for x in decls[aid]["writer_constant_phrases"])
    assert "writer_constant_phrases" not in decls[GEST]                                                              # nothing is declared for the real asset yet (the director walks the declarations)


# ───────────────────────── (c) the live closure ─────────────────────────
# SS N-436: the `test_live_pg_*` tests need a real PostgreSQL (disposable_pg); they run in the CI shard that has one. The `test_fake_*` tests below prove the same claims with the engine's own
# `label_read` replaced by a fake that answers like the database (a distinct-values list, or None), and the SQL text itself is asserted without a database.

@pytest.fixture()
def db(disposable_pg, monkeypatch):
    pg = disposable_pg
    fs.psql(pg, "DROP TABLE IF EXISTS gest CASCADE")
    fs.psql(pg, "CREATE TABLE gest (chart_id uuid, ayanamsha_id text, a_jsonb jsonb, b_jsonb jsonb, c_jsonb jsonb)")
    point_psql_at(pg, monkeypatch)
    yield pg
    ac.set_read_scope(None)
    fs.psql(pg, "DROP TABLE IF EXISTS gest CASCADE")


def _j(note):
    return "'" + json.dumps(dict(note=note)).replace("'", "''") + "'::jsonb"


def _row(db, chart, a=POINTER, b=SPINE, c="a composed sentence word word word"):
    fs.psql(db, f"INSERT INTO gest VALUES ('{chart}', 'lahiri', {_j(a)}, {_j(b)}, {_j(c)})")


COLS = ["chart_id", "ayanamsha_id", "a_jsonb", "b_jsonb", "c_jsonb"]
OWN = {"gest": (COLS, {c: ("uuid" if c == "chart_id" else "text" if c == "ayanamsha_id" else "jsonb") for c in COLS}, {})}
CLOSED_ITEMS = [_item(POINTER, ENTRIES, closed=ENTRIES[:2]), _item(SPINE, ENTRIES)]            # a and b are closed; c (a composed sentence) is covered but not closed


def _live(items, scope=True):
    ac.set_read_scope({"gest": dict(where=f"chart_id = '{CHART_A}'", label="measured chart")} if scope else None)
    return _apply(items, ctx_extra=dict(own=OWN))


def test_live_pg_a_closed_entry_whose_stored_leaves_are_inside_the_declared_literals_is_earned(db):
    _row(db, CHART_A)
    _row(db, CHART_A, a=SPINE, b=POINTER)                                    # both declared sentences, on either closed entry: still a subset
    out, _ = _live(CLOSED_ITEMS)
    for c in ac.NULL_CHECKS:
        r = out[c]
        assert r["v"] == ac.PASS and r["writer_scan"]["closed_entries"] == {e: dict(verified=True, stored=sorted([POINTER, SPINE])) for e in ENTRIES[:2]}, r["measured"][:300]
        assert ac.writer_scan_problem(r) is None
    assert ac.writer_scan_earned("Null.blank_rows", out["Null.blank_rows"], out)
    assert out["Narr.agree"]["v"] == ac.PARTIAL                              # untouched


def test_live_pg_a_stored_value_outside_the_declared_literals_fails_narr_agree_naming_it_and_keeps_the_cap(db):
    _row(db, CHART_A)
    _row(db, CHART_A, a="a sentence the writer never declared")
    out, _ = _live(CLOSED_ITEMS)
    assert out["Narr.agree"]["v"] == ac.FAIL and "a sentence the writer never declared" in out["Narr.agree"]["measured"] and ENTRIES[0] in out["Narr.agree"]["measured"]
    for c in ac.NULL_CHECKS:
        assert out[c]["v"] == ac.PARTIAL and "writer_scan" not in out[c] and "outside the declared literals" in out[c]["measured"]


def test_live_pg_the_closure_is_scoped_to_the_measured_chart(db):
    _row(db, CHART_A)
    _row(db, CHART_B, b="another chart holds a stray sentence")
    out, _ = _live(CLOSED_ITEMS)
    assert all(out[c]["v"] == ac.PASS for c in ac.NULL_CHECKS) and out["Narr.agree"]["v"] == ac.PARTIAL
    out, _ = _live(CLOSED_ITEMS, scope=False)                                # the same data read whole: the other chart's stray value now counts
    assert out["Narr.agree"]["v"] == ac.FAIL and "another chart holds a stray sentence" in out["Narr.agree"]["measured"]


def test_live_pg_an_entry_that_is_not_closed_is_never_read(db):
    _row(db, CHART_A, c="a composed sentence the declaration does not list")
    out, _ = _live(CLOSED_ITEMS)                                             # c holds a sentence outside the corpus, but c is not closed
    assert all(out[c]["v"] == ac.PASS for c in ac.NULL_CHECKS)
    out, _ = _live([_item(POINTER, ENTRIES, closed=True), _item(SPINE, ENTRIES)])      # closing it as well makes the same data a FAIL
    assert out["Narr.agree"]["v"] == ac.FAIL and "the declaration does not list" in out["Narr.agree"]["measured"]


def test_live_pg_a_closure_over_no_stored_string_is_vacuous_and_keeps_the_cap(db):
    out, _ = _live(CLOSED_ITEMS)                                             # no row at all
    for c in ac.NULL_CHECKS:
        assert out[c]["v"] == ac.PARTIAL and "writer_scan" not in out[c] and "closure is not verified" in out[c]["measured"]
    fs.psql(db, f"INSERT INTO gest VALUES ('{CHART_A}', 'lahiri', '{{\"note\": 3}}', '{{\"note\": null}}', '{{}}')")               # rows, but no string leaf at the closed paths
    out, _ = _live(CLOSED_ITEMS)
    assert all(out[c]["v"] == ac.PARTIAL and "closure is not verified" in out[c]["measured"] for c in ac.NULL_CHECKS) and out["Narr.agree"]["v"] == ac.PARTIAL


def test_live_pg_a_read_that_did_not_happen_never_fails_and_never_passes(db, monkeypatch):
    _row(db, CHART_A)
    def boom(sql, *a, **k):
        raise ac.Unknown("connection lost")
    monkeypatch.setattr(ac, "psql", boom)
    out, _ = _live(CLOSED_ITEMS)
    assert out["Narr.agree"]["v"] == ac.PARTIAL
    assert all(out[c]["v"] == ac.PARTIAL and "the live read did not happen" in out[c]["measured"] for c in ac.NULL_CHECKS)


def test_a_closed_entry_in_a_table_the_asset_does_not_own_is_unread():
    out, _ = _apply(CLOSED_ITEMS)                                            # no owned-table facts in the context
    assert all(out[c]["v"] == ac.PARTIAL and "the live read did not happen" in out[c]["measured"] for c in ac.NULL_CHECKS)


def test_without_closed_nothing_is_read_and_the_record_is_the_n279_one(monkeypatch):
    def boom(sql, *a, **k):
        raise AssertionError("an undeclared closure must not read the database")
    monkeypatch.setattr(ac, "psql", boom)
    monkeypatch.setattr(ac, "label_read", boom)
    out, _ = _apply(LIST_ITEMS, ctx_extra=dict(own=OWN))
    assert all(out[c]["v"] == ac.PASS and "closed_entries" not in out[c]["writer_scan"] for c in ac.NULL_CHECKS)


# ───────────────────────── the same claims with a fake reader (no database) ─────────────────────────

def _fake_reader(monkeypatch, data, calls=None):
    """label_read replaced by a fake over {entry: [distinct stored strings] | None}; the call is recorded as (table, entry, tuple(values))."""
    def fake(table, entry, values):
        if calls is not None:
            calls.append((table, entry, tuple(values)))
        return data.get(entry)
    monkeypatch.setattr(ac, "label_read", fake)


def _fake_run(items, own=OWN):
    return _apply(items, ctx_extra=dict(own=own))


def test_fake_stored_values_inside_the_corpus_are_earned_with_the_stored_values_in_the_block(monkeypatch):
    calls = []
    _fake_reader(monkeypatch, {ENTRIES[0]: [POINTER], ENTRIES[1]: [SPINE, POINTER]}, calls)
    out, _ = _fake_run(CLOSED_ITEMS)
    for c in ac.NULL_CHECKS:
        r = out[c]
        assert r["v"] == ac.PASS and r["writer_scan"]["closed_entries"] == {ENTRIES[0]: dict(verified=True, stored=[POINTER]), ENTRIES[1]: dict(verified=True, stored=sorted([SPINE, POINTER]))}
        assert ac.writer_scan_problem(r) is None
    assert ac.writer_scan_earned("Null.blank_rows", out["Null.blank_rows"], out)
    assert sorted((t, e) for t, e, _v in calls) == [("gest", ENTRIES[0]), ("gest", ENTRIES[1])]            # only the closed entries are read, each in its owned table
    assert all(set(v) == {POINTER, SPINE} for _t, _e, v in calls)                                        # against the declared literals of that entry


def test_fake_a_stray_value_fails_narr_agree_naming_it_and_the_cap_stays(monkeypatch):
    _fake_reader(monkeypatch, {ENTRIES[0]: [POINTER, "a sentence the writer never declared"], ENTRIES[1]: [SPINE]})
    out, _ = _fake_run(CLOSED_ITEMS)
    assert out["Narr.agree"]["v"] == ac.FAIL and "a sentence the writer never declared" in out["Narr.agree"]["measured"] and ENTRIES[0] in out["Narr.agree"]["measured"]
    for c in ac.NULL_CHECKS:
        assert out[c]["v"] == ac.PARTIAL and "writer_scan" not in out[c] and "outside the declared literals" in out[c]["measured"]


def test_fake_a_bounded_existence_read_with_a_stray_is_a_fact_without_one_it_is_unread(monkeypatch):
    _fake_reader(monkeypatch, {ENTRIES[0]: dict(stray=["x"]), ENTRIES[1]: [SPINE]})
    out, _ = _fake_run(CLOSED_ITEMS)
    assert out["Narr.agree"]["v"] == ac.FAIL
    _fake_reader(monkeypatch, {ENTRIES[0]: dict(stray=[]), ENTRIES[1]: [SPINE]})
    out, _ = _fake_run(CLOSED_ITEMS)
    assert out["Narr.agree"]["v"] == ac.PARTIAL and all(out[c]["v"] == ac.PARTIAL and "closure is not verified" in out[c]["measured"] for c in ac.NULL_CHECKS)


@pytest.mark.parametrize("answer", [None, [], dict(blocked="no rows in scope")])
def test_fake_a_closure_over_nothing_or_an_unread_entry_never_passes_and_never_fails(monkeypatch, answer):
    _fake_reader(monkeypatch, {ENTRIES[0]: answer, ENTRIES[1]: [SPINE]})
    out, _ = _fake_run(CLOSED_ITEMS)
    assert out["Narr.agree"]["v"] == ac.PARTIAL
    assert all(out[c]["v"] == ac.PARTIAL and "writer_scan" not in out[c] and "closure is not verified" in out[c]["measured"] for c in ac.NULL_CHECKS)


def test_fake_an_entry_that_is_not_closed_is_never_read(monkeypatch):
    calls = []
    _fake_reader(monkeypatch, {ENTRIES[0]: [POINTER], ENTRIES[1]: [SPINE], ENTRIES[2]: ["a sentence outside the corpus"]}, calls)
    out, _ = _fake_run(CLOSED_ITEMS)
    assert all(out[c]["v"] == ac.PASS for c in ac.NULL_CHECKS) and ENTRIES[2] not in {e for _t, e, _v in calls}
    out, _ = _fake_run([_item(POINTER, ENTRIES, closed=True), _item(SPINE, ENTRIES)])
    assert out["Narr.agree"]["v"] == ac.FAIL and "a sentence outside the corpus" in out["Narr.agree"]["measured"]


def test_fake_a_table_the_asset_does_not_own_leaves_the_entry_unread(monkeypatch):
    _fake_reader(monkeypatch, {e: [POINTER] for e in ENTRIES})
    out, _ = _fake_run(CLOSED_ITEMS, own={"other": (["x"], {}, {})})
    assert all(out[c]["v"] == ac.PARTIAL and "the live read did not happen" in out[c]["measured"] for c in ac.NULL_CHECKS)


def test_the_closure_read_is_chart_scoped_in_its_sql_text():
    ac.set_read_scope({"gest": dict(where=f"chart_id = '{CHART_A}'", label="measured chart")})
    try:
        sql = ac.label_distinct_sql("gest", ENTRIES[0])
    finally:
        ac.set_read_scope(None)
    assert f"chart_id = '{CHART_A}'" in sql and "jsonb_typeof" in sql and "'{note}'" in sql and f"LIMIT {ac.MAX_LABEL_VALUES + 1}" in sql
    assert "chart_id" not in ac.label_distinct_sql("gest", ENTRIES[0])                                      # no scope installed: the read is whole (and the cell says so elsewhere)
