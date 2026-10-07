"""test_formgap_templated.py: FORM-GAP form 5 (SS N-191): the TEMPLATED-CLOSURE form of `prose_none` for a derivation pointer that embeds the chart id.

ga_dashas writes `chart_dashas.citation_ref` at 13 f-string sites, every one of which embeds the chart id (`chart_dashas.vimshottari.L2.Jupiter-Saturn@chart=<uuid>:ay=lahiri_chitrapaksha:eng=...`). The column is
not narration, not a key and not a K1 source, so no older form could close it. `templated_columns` closes it by TEMPLATES: literal text plus `{placeholder}`s. `{chart_id}` is bound at MEASURE time to the MEASURED
chart (the declaration never stores a chart id: a uuid-shaped literal is refused); every other placeholder is a closed set of values, a dash-joined sequence of them, or a named class. The data decides:
a value that matches no template, or that carries ANOTHER chart's id, is a FAIL; a read that did not happen is NO_DETECTOR.

Real DDL (migration 206 chart_dashas) on a disposable PostgreSQL; the engine's own `_measure_prose`; mutation tests; two-chart tests through the engine's read scope; Python / PostgreSQL pattern parity.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import _formgap_support as fs  # noqa: E402
import prose_forms as pf  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401
from _formgap_support import CHART_A, CHART_B, NA, FAIL, NO_DET, CELLS  # noqa: E402

GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
AYAS = ["lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"]
EV = "platform/python-sidecar/ga_writers/ga_dashas_writer.py:1310"      # a real line of the real writer; the cited FILE must mention the column
PH = {"n": dict(values=["1", "2", "3", "4"]), "chain": dict(values=GRAHAS, join="-", min=1, max=4), "ay": dict(values=AYAS), "vn": {"class": "int"}}
TEMPLATES = [
    "chart_dashas.vimshottari.L{n}.{chain}@chart={chart_id}:ay={ay}:eng=pyjhora_adapter/0.1.0",
    "chart_dashas.mudda.L1.varsha{vn}.{chain}@chart={chart_id}:ay={ay}:eng=pyjhora_adapter/4.8.6",
    "L1_GANITA_SCOPE_CAP",                                                          # a fixed value (the scope-cap sentinel row): a template with no placeholder
]
PH_USED = {k: PH[k] for k in ("n", "chain", "ay", "vn")}


def _tp(**kw):
    d = dict(column="citation_ref", why="the column is a derivation pointer built from fixed templates, never a sentence about a computed value", evidence=EV, templates=TEMPLATES, placeholders=PH_USED)
    d.update(kw)
    return d


def _decl(*tpl, **kw):
    return {"prose_fields": [], "evidence": {"prose_fields": fs.EV}, "prose_none": dict(why=fs.WHY, closed_columns=[], templated_columns=list(tpl) or [_tp()], **kw)}


GOOD = ["chart_dashas.vimshottari.L2.Jupiter-Saturn@chart={c}:ay=lahiri_chitrapaksha:eng=pyjhora_adapter/0.1.0",
        "chart_dashas.vimshottari.L1.Sun@chart={c}:ay=raman:eng=pyjhora_adapter/0.1.0",
        "chart_dashas.mudda.L1.varsha31.Mercury@chart={c}:ay=true_chitra:eng=pyjhora_adapter/4.8.6",
        "L1_GANITA_SCOPE_CAP"]


# ───────────────────────────── the template language ─────────────────────────────

def test_the_declaration_is_sound_and_the_fields_are_closed():
    assert ac.prose_none_problem(_decl()) is None
    assert ac.TEMPLATED_FIELDS == ("column", "table", "templates", "placeholders", "why", "evidence") and "templated_columns" in ac.PROSE_NONE_DECL_FIELDS


@pytest.mark.parametrize("templates,ph,needle", [
    (["a {x} b"], {}, "placeholders must describe exactly"),                                   # a placeholder with no spec
    (["a b"], {"x": dict(values=["1"])}, "placeholders must describe exactly"),               # a spec nobody uses
    (["a {chart_id} b"], {"chart_id": dict(values=["1"])}, "takes no spec"),                  # the chart placeholder is bound at measure time
    (["a {X} b"], {"X": dict(values=["1"])}, "lower-case identifier"),
    (["a {} b"], {}, "lower-case identifier"),
    (["a {x"], {}, "outside the whitelist|may hold only"),
    (["a } b"], {}, "may hold only"),
    (["chart=482012f1-710e-4a25-994a-93821f5871aa:{x}"], {"x": dict(values=["1"])}, "uuid-shaped literal"),   # the chart id is never written into the declaration
    (["a\\b {x}"], {"x": dict(values=["1"])}, "may hold only"),
    (["a\"b {x}"], {"x": dict(values=["1"])}, "may hold only"),
    (["aé {x}"], {"x": dict(values=["1"])}, "may hold only"),
    ([], {}, "1 to 32"),
    (["a {x}", "a {x}"], {"x": dict(values=["1"])}, "1 to 32 distinct"),
    ([f"t{i} {{x}}" for i in range(33)], {"x": dict(values=["1"])}, "1 to 32"),
    (["a {x}"], {"x": dict(values=[])}, "values must be"),
    (["a {x}"], {"x": dict(values=["1", "1"])}, "values must be"),
    (["a {x}"], {"x": dict(values=["482012f1-710e-4a25-994a-93821f5871aa"])}, "uuid-shaped"),   # a value may never carry a chart id
    (["a {x}"], {"x": dict(values=["a;b\n"])}, "short string"),
    (["a {x}"], {"x": {"class": "uuid"}}, "class must be one of"),
    (["a {x}"], {"x": {"class": "int", "values": ["1"]}}, "exactly one of"),
    (["a {x}"], {"x": dict(values=["1"], join="-", min=1, max=2, extra=1)}, "sequence spec is exactly"),
    (["a {x}"], {"x": dict(values=["1"], join="--", min=1, max=2)}, "one separator character"),
    (["a {x}"], {"x": dict(values=["1"], join="-", min=0, max=2)}, "min and max"),
    (["a {x}"], {"x": dict(values=["1"], join="-", min=3, max=2)}, "min and max"),
    (["a {x}"], {"x": dict(values=["1"], join="-", min=1, max=99)}, "min and max"),
    (["a {x}"], {"x": dict(values=["a-b"], join="-", min=1, max=2)}, "own separator"),
    (["a {x}"], "not an object", "must be an object"),
    (["a {x}"], {"x": "1"}, "exactly one of"),
])
def test_a_malformed_template_set_is_refused(templates, ph, needle):
    got = pf.templates_problem(templates, ph)
    assert got is not None and re.search(needle, got), got


def test_the_entry_level_validator_refuses_a_malformed_entry():
    P = ac.prose_none_problem
    assert "unknown field" in P(_decl(_tp(extra=1)))
    assert "placeholders must be an object" in P(_decl({k: v for k, v in _tp().items() if k != "placeholders"}))
    assert "templates must be" in P(_decl({k: v for k, v in _tp().items() if k != "templates"}))
    assert P(_decl(_tp(evidence="unverified: somewhere in the writer"))) is not None
    assert "does not mention 'citation_ref'" in P(_decl(_tp(evidence="platform/scripts/governance/golden_test_scan.py:1")))
    assert "listed twice" in P(_decl(_tp(), _tp()))
    assert "declared by both" in P({"prose_fields": [], "evidence": {"prose_fields": fs.EV},
                                    "prose_none": dict(why=fs.WHY, closed_columns=[dict(column="citation_ref", why="a closed list that is not this column", values=["x"])], templated_columns=[_tp()])})


# ───────────────────────────── the compiled pattern: Python re and PostgreSQL ARE agree ─────────────────────────────

def test_the_compiled_pattern_binds_the_chart_id_and_matches_what_it_should():
    rx = pf.compile_templates(TEMPLATES, PH_USED, CHART_A)
    assert rx.startswith("^(?:") and rx.endswith(")$") and "\\" not in rx and "'" not in rx            # no backslash, no quote: a safe SQL literal and valid in both engines
    for g in GOOD:
        assert pf.template_matches(rx, g.format(c=CHART_A)), g
    bad = [GOOD[0].format(c=CHART_B), GOOD[0].format(c=CHART_A.upper()), GOOD[0].format(c=CHART_A) + " extra", " " + GOOD[0].format(c=CHART_A),
           "chart_dashas.vimshottari.L5.Sun@chart=%s:ay=raman:eng=pyjhora_adapter/0.1.0" % CHART_A,         # level outside the set
           "chart_dashas.vimshottari.L1.Pluto@chart=%s:ay=raman:eng=pyjhora_adapter/0.1.0" % CHART_A,        # a lord outside the set
           "chart_dashas.vimshottari.L1.Sun-Moon-Mars-Mercury-Jupiter@chart=%s:ay=raman:eng=pyjhora_adapter/0.1.0" % CHART_A,   # a chain longer than 4
           "chart_dashas.vimshottari.L1.Sun@chart=%s:ay=raman:eng=pyjhora_adapter/9.9.9" % CHART_A,          # a literal that differs
           "chart_dashas.mudda.L1.varshaX.Sun@chart=%s:ay=raman:eng=pyjhora_adapter/4.8.6" % CHART_A,        # the integer class
           "L1_GANITA_SCOPE_CAP ", "l1_ganita_scope_cap", "a sentence about Jupiter in Saturn", ""]
    for b in bad:
        assert not pf.template_matches(rx, b), b


@pytest.fixture()
def db(monkeypatch, disposable_pg):
    pg = disposable_pg
    point_psql_at(pg, monkeypatch)
    fs.drop_tables(pg, "chart_dashas")
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "206_ga3_supporting_tables.sql", "chart_dashas"))
    yield pg
    fs.drop_tables(pg, "chart_dashas")


def _row(pg, ref, chart=CHART_A, sysid="vimshottari", n=1):
    r = ref.replace("'", "''")
    fs.psql(pg, "INSERT INTO chart_dashas (chart_id, ayanamsha_id, build_id, system_id, level_n, lord_graha, start_date, end_date, start_iso, end_iso, duration_days, verification_pass_status, "
                "verification_method, citation_ref, citation_human, engine_version) "
                f"VALUES ('{chart}', 'raman', gen_random_uuid(), '{sysid}', {n}, 'Sun', DATE '2000-01-01', DATE '2001-01-01', TIMESTAMPTZ '2000-01-01 00:00+00', TIMESTAMPTZ '2001-01-01 00:00+00', 366, "
                f"'single', 'm', '{r}', 'h', 'e') ON CONFLICT DO NOTHING")


def test_REAL_SQL_python_and_postgresql_read_every_pattern_alike(db):
    rx = pf.compile_templates(TEMPLATES, PH_USED, CHART_A)
    values = [g.format(c=CHART_A) for g in GOOD] + [GOOD[0].format(c=CHART_B), "chart_dashas.vimshottari.L5.Sun@chart=%s:ay=raman:eng=pyjhora_adapter/0.1.0" % CHART_A,
                                                      "Sun in Aries (a sentence)", "L1_GANITA_SCOPE_CAP ", "chart_dashas.vimshottari.L1.Sun-Moon-Mars-Mercury-Jupiter@chart=%s:ay=raman:eng=pyjhora_adapter/0.1.0" % CHART_A]
    for v in values:
        pg_says = fs.psql(db, f"SELECT ({ac._sql_lit(v)} ~ {ac._rx_lit(rx)})::text").strip() == "true"
        assert pg_says is pf.template_matches(rx, v), v


def test_the_read_is_one_bounded_statement_with_two_limited_scans_and_a_prefix_test_before_every_pattern():
    pairs = pf.compile_each(TEMPLATES, PH_USED, CHART_A)
    assert [p for p, _ in pairs] == ["chart_dashas.vimshottari.L", "chart_dashas.mudda.L1.varsha", "L1_GANITA_SCOPE_CAP"]
    sql = ac.templated_read_sql("chart_dashas", "citation_ref", pairs, CHART_A, None)
    assert sql.count("LIMIT 3") == 2 and "count(" not in sql.lower().replace("jsonb_agg", "") and "ORDER BY" not in sql.upper() and "DISTINCT" not in sql.upper()
    assert sql.count('FROM "chart_dashas"') == 2 and "NOT (" in sql and "replace(" in sql
    assert sql.count("starts_with(") == 3 and sql.index("starts_with(") < sql.index(" ~ '")                   # the cheap prefix test precedes every pattern (the alternation of all templates costs 8x per row)


def test_the_per_template_patterns_accept_exactly_what_the_union_pattern_accepts():
    union = pf.compile_templates(TEMPLATES, PH_USED, CHART_A)
    pairs = pf.compile_each(TEMPLATES, PH_USED, CHART_A)
    samples = [g.format(c=CHART_A) for g in GOOD] + [GOOD[0].format(c=CHART_B), "L1_GANITA_SCOPE_CAP ", "a sentence", "chart_dashas.mudda.L1.varshaX.Sun@chart=%s:ay=raman:eng=pyjhora_adapter/4.8.6" % CHART_A,
                                                       "chart_dashas.vimshottari.L1.Sun@chart=%s:ay=raman:eng=pyjhora_adapter/0.1.0\n" % CHART_A]
    for v in samples:
        each = any(v.startswith(p) and pf.template_matches(r, v) for p, r in pairs)
        assert each is pf.template_matches(union, v), v


# ───────────────────────────── the detector on a disposable database ─────────────────────────────

AID = "ga_dashas"


def _measure(pg, monkeypatch, decl=None, scope=None):
    # the real writer file gives the scope its units; what it writes into chart_dashas is the writer's COPY (not an INSERT), so the written-columns read is stood in below
    monkeypatch.setattr(ac, "written_columns", lambda units, tables: {"chart_dashas": {"citation_ref"}})
    d = decl or _decl()
    return fs.measure(AID, pg, monkeypatch, ac.registered_ids("")[AID], "chart_dashas", ["chart_dashas"], d, scope=scope)


def _full(*tpl):
    """The asset judged on the column its writer writes (`column_scope: written`; the written-columns read is stood in by `_measure`): this file is about citation_ref only."""
    d = _decl(*tpl)
    d["prose_none"]["column_scope"] = "written"
    return d


def test_REAL_SQL_every_value_a_template_instance_reads_na_on_all_six_with_the_verified_block(db, monkeypatch):
    for i, g in enumerate(GOOD):
        _row(db, g.format(c=CHART_A), n=i + 1)
    got = _measure(db, monkeypatch, _full())
    fs.all_na(got)
    blk = got["Narr.agree"]["prose_none"]["forms"]["templated"]
    assert blk == [dict(table="chart_dashas", column="citation_ref", verified=True, chart_id_bound=True, templates=3)]
    assert CHART_A not in json.dumps(got["Narr.agree"]["prose_none"])                                # the measured chart id never enters the record's block either


def test_the_chart_id_is_never_stored_in_the_declaration():
    d = _full()
    assert not re.search(pf.UUID_ANY_RE, json.dumps(d["prose_none"]["templated_columns"]))
    assert ac.prose_none_problem(_decl(_tp(templates=[f"chart_dashas.x@chart={CHART_A}:{{n}}"], placeholders=dict(n=PH["n"])))) is not None


def test_MUTATION_a_value_of_another_chart_is_a_FAIL_and_the_cell_names_it(db, monkeypatch):
    _row(db, GOOD[0].format(c=CHART_A))
    _row(db, GOOD[1].format(c=CHART_B), n=2)                                                         # a row of the measured chart that points at ANOTHER chart
    got = _measure(db, monkeypatch, _full())
    assert got["Narr.agree"]["v"] == FAIL and "carries another chart's id" in got["Narr.agree"]["measured"] and CHART_B in got["Narr.agree"]["measured"]
    assert all(got[c]["v"] == NO_DET for c in CELLS[1:])


def test_MUTATION_a_sentence_in_the_pointer_column_is_a_FAIL(db, monkeypatch):
    _row(db, GOOD[0].format(c=CHART_A))
    _row(db, "Jupiter rules the dasha because it is exalted in the tenth house", n=2)
    got = _measure(db, monkeypatch, _full())
    assert got["Narr.agree"]["v"] == FAIL and "matches none of the 3 declared template(s)" in got["Narr.agree"]["measured"] and "Jupiter rules" in got["Narr.agree"]["measured"]


@pytest.mark.parametrize("drift", [
    "chart_dashas.vimshottari.L5.Sun@chart={c}:ay=raman:eng=pyjhora_adapter/0.1.0",                  # a level outside the closed set
    "chart_dashas.vimshottari.L1.Pluto@chart={c}:ay=raman:eng=pyjhora_adapter/0.1.0",                # a lord outside the closed set
    "chart_dashas.vimshottari.L1.Sun@chart={c}:ay=lahiri:eng=pyjhora_adapter/0.1.0",                 # an ayanamsha spelling outside the set
    "chart_dashas.vimshottari.L1.Sun@chart={c}:ay=raman:eng=pyjhora_adapter/0.2.0",                  # a drifted literal
    "chart_dashas.vimshottari.L1.Sun@chart={c}:ay=raman:eng=pyjhora_adapter/0.1.0 (rebuilt)",
])
def test_MUTATION_any_drift_of_one_value_from_every_template_is_a_FAIL(db, monkeypatch, drift):
    for i, g in enumerate(GOOD):
        _row(db, g.format(c=CHART_A), n=i + 1)
    assert _measure(db, monkeypatch, _full())["Narr.agree"]["v"] == NA
    _row(db, drift.format(c=CHART_A), n=9)
    assert _measure(db, monkeypatch, _full())["Narr.agree"]["v"] == FAIL


def test_MUTATION_a_forged_declaration_with_templates_that_do_not_describe_the_column_FAILS(db, monkeypatch):
    for i, g in enumerate(GOOD):
        _row(db, g.format(c=CHART_A), n=i + 1)
    forged = _full(_tp(templates=["something else entirely {n}"], placeholders=dict(n=PH["n"])))
    got = _measure(db, monkeypatch, forged)
    assert got["Narr.agree"]["v"] == FAIL and "matches none of the 1 declared template(s)" in got["Narr.agree"]["measured"]


def test_REAL_SQL_two_charts_only_the_measured_charts_rows_are_judged(db, monkeypatch):
    for i, g in enumerate(GOOD):
        _row(db, g.format(c=CHART_A), chart=CHART_A, n=i + 1)
    for i, g in enumerate(GOOD):
        _row(db, g.format(c=CHART_B), chart=CHART_B, n=i + 1)                                        # chart B's rows are well-formed for chart B, which is not the measured chart
    scope_a = {"chart_dashas": dict(where=f"chart_id = '{CHART_A}'", label="the measured chart")}
    assert _measure(db, monkeypatch, _full(), scope=scope_a)["Narr.agree"]["v"] == NA               # with the engine's scope: chart A's rows only
    whole = _measure(db, monkeypatch, _full())                                                       # without a scope (a unit test): chart B's pointers carry another chart's id
    assert whole["Narr.agree"]["v"] == FAIL and "another chart's id" in whole["Narr.agree"]["measured"]
    scope_b = {"chart_dashas": dict(where=f"chart_id = '{CHART_B}'", label="the other chart")}
    got = _measure(db, monkeypatch, _full(), scope=scope_b)                                          # measuring chart B against chart A's bound id: every pointer names B, not A
    assert got["Narr.agree"]["v"] == FAIL


def test_REAL_SQL_a_scope_with_no_row_is_vacuous(db, monkeypatch):
    _row(db, GOOD[0].format(c=CHART_B), chart=CHART_B)
    scope = {"chart_dashas": dict(where=f"chart_id = '{CHART_A}'", label="the measured chart", block="no rows in the read scope: nothing to judge")}
    got = _measure(db, monkeypatch, _full(), scope=scope)
    assert all(got[c]["v"] == NO_DET for c in CELLS) and "nothing to judge" in got["Narr.agree"]["measured"]


def test_the_phantom_chart_and_a_malformed_chart_id_are_never_bound(monkeypatch):
    tables = {"t": (["citation_ref"], {"citation_ref": "text"}, None)}
    d = _decl(_tp(column="citation_ref"))
    monkeypatch.setattr(ac, "scalar", lambda q: (_ for _ in ()).throw(AssertionError("no read may be made")))
    for cid, why in (("362f9f17-0000-4000-8000-000000000000", "dead phantom"), ("not-a-uuid", "not a canonical lower-case uuid"), (CHART_A.upper(), "not a canonical lower-case uuid")):
        out = ac.formgap_reads("x", d, tables, "t", udts={}, chart_id=cid)
        assert why in out["templated"][("t", "citation_ref")]["unread"], cid


TIMEOUT = "ERROR:  canceling statement due to statement timeout"


@pytest.mark.parametrize("err", [ac.Unknown(TIMEOUT), ac.CheckTimeout("client-side timeout after 180s (psql killed)"), ac.Unknown("ERROR:  permission denied for table chart_dashas")])
def test_a_read_that_timed_out_or_was_refused_is_no_detector_never_pass(monkeypatch, err):
    def boom(q):
        raise err
    monkeypatch.setattr(ac, "scalar", boom)
    tables = {"t": (["citation_ref"], {"citation_ref": "text"}, None)}
    forms = ac.formgap_reads("x", _decl(_tp()), tables, "t", udts={}, chart_id=CHART_A)
    assert "unread" in forms["templated"][("t", "citation_ref")]
    got = ac.grade_prose_none("x", _decl(_tp()), tables, "t", {}, forms=forms)
    assert all(got[c]["v"] == NO_DET for c in CELLS) and got["Narr.agree"]["prose_none"]["unread"]


def test_the_grader_states():
    g = ac.grade_templated
    assert g(dict(unmatched=[], other_chart=[]), 3)["state"] == "ok"
    assert g(dict(unmatched=["x"], other_chart=[]), 3)["state"] == "wrong"
    assert g(dict(unmatched=[], other_chart=["x"]), 3)["state"] == "wrong" and "another chart" in g(dict(unmatched=["y"], other_chart=["x"]), 3)["text"]    # the cross-chart finding wins
    assert g(dict(unread="t"), 3)["state"] == "unread" and g(None, 3)["state"] == "unread"


def test_the_rollup_guard_refuses_a_templated_entry_that_is_not_verified(db, monkeypatch):
    for i, g in enumerate(GOOD):
        _row(db, g.format(c=CHART_A), n=i + 1)
    rec = _measure(db, monkeypatch, _full())["Narr.agree"]
    assert ac.prose_none_na_problem("Narr.agree", rec) is None
    forged = json.loads(json.dumps(rec))
    forged["prose_none"]["forms"]["templated"][0]["verified"] = False
    assert "not all verified" in ac.prose_none_na_problem("Narr.agree", forged)


# ───────────────────────────── a quote and the right arrow are allowed literal characters (the nakshatra matrix pointers) ─────────────────────────────

def test_a_quote_and_the_right_arrow_are_template_literals_and_reach_postgresql_intact(db):
    t = ["nakshatra_id={n} → rajju '{r}'", "dist={d},pos={p}"]
    ph = {"n": {"class": "int"}, "r": dict(values=["Pada", "Kati", "Nabhi"]), "d": {"class": "int"}, "p": {"class": "int"}}
    assert pf.templates_problem(t, ph) is None
    rx = pf.compile_templates(t, ph, CHART_A)
    assert "'" in rx and "→" in rx and "\\" not in rx
    for v, want in (("nakshatra_id=4 → rajju 'Kati'", True), ("nakshatra_id=4 → rajju Kati", False), ("nakshatra_id=4 -> rajju 'Kati'", False), ("nakshatra_id=4 → rajju 'Head'", False),
                    ("dist=3,pos=7", True), ("dist=3,pos=", False), ("dist=3;pos=7", False)):
        assert pf.template_matches(rx, v) is want, v
        assert (fs.psql(db, f"SELECT ({ac._sql_lit(v)} ~ {ac._rx_lit(rx)})::text").strip() == "true") is want, v
    assert ac._rx_lit("a'b") == "'a''b'"
    with pytest.raises(ac.Unknown):
        ac._rx_lit("a\\b")
    for bad in (["a ← {x}"], ["a é {x}"], ['a "{x}']):
        assert pf.templates_problem(bad, {"x": dict(values=["1"])}) is not None, bad
