"""test_n431_empty_slice_conditional.py -- SS N-431 / N-545: the DECLARED `empty_slice_by_conditional` (ga_vichara option A): a conditional produced slice that is
empty is read as EMPTY BY A VERIFIED CONDITIONAL only when the census EARNS it from the writer's own evidence records (post_pass_evidence/1); never when the post-pass
was merely not run. Census side only; the writer side is built elsewhere (pr #3448): every fixture here is a FAKE of exactly the frozen record shape.

How the negative tests are protected (the design's 17 census mutation cases M1-M17): every guarded clause of the detector sits between `#<clause NAME>` and `#</clause NAME>`
markers in the source. `_mutant(fn, *clauses)` DELETES those lines and re-defines the function; each negative case is run twice: the real detector must NOT credit it (and name the
clause), and the mutant (clause deleted) must credit it wrongly or crash -- otherwise the clause is not what protects the case and the test fails.

Offline: psql is faked, nothing touches a database or the network.
"""
from __future__ import annotations

import copy
import inspect
import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import census_postprocess as cp  # noqa: E402

CH = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
PHANTOM = "362f9f17-0000-4000-8000-000000000000"
R = "966719ef-d65a-4f04-b746-f067f1c0ec3f"          # the evidenced (newest complete) build
R0 = "c9590a23-915c-43f5-a6bf-9fbf7c59d5ba"         # an older complete build
RE = "04837859-1111-4111-8111-111111111111"         # a never-started errored attempt (the DEP-ASSERT shape)
PARTS = ["lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"]
EMIT = "platform/python-sidecar/ga_writers/ga_daridra_postpass.py"
ADAPT = "platform/python-sidecar/pipeline/orchestrator/writers/ga_vichara.py"
WRITER = "platform/python-sidecar/ga_writers/ga_vichara_writer.py"
SLICE = dict(table="chart_facts", fact_category="dosha_label", fact_subject="daridra")
WHY = "the daridra post-pass writes the chart_facts row only on a chart where daridra forms, so the slice is empty on a chart where it does not"

EMITTER_SRC = '''
import json
POST_PASS_EVENT_TYPE = "writer.post_pass_evaluated"
POST_PASS_SCHEMA = "post_pass_evidence/1"
POST_PASS_NAME = "daridra_dosha_label"


def record_post_pass_evidence(conn, chart_id, build_id, ayanamsha_id, *, entries_evaluated, formed, rows_written, prior_rows_deleted):
    conn.execute("INSERT INTO orchestrator_event_register (event_type, payload) VALUES (%s, %s)", [POST_PASS_EVENT_TYPE, json.dumps({"schema": POST_PASS_SCHEMA})])


def emit_daridra_label_post_pass(conn, chart_id, build_id, ayanamsha_id):
    rows = build(conn)
    deleted = delete(conn)
    if not rows:
        record_post_pass_evidence(conn, chart_id, build_id, ayanamsha_id, entries_evaluated=1, formed=False, rows_written=0, prior_rows_deleted=deleted)
        return 0
    written = insert(conn, rows)
    record_post_pass_evidence(conn, chart_id, build_id, ayanamsha_id, entries_evaluated=1, formed=True, rows_written=written, prior_rows_deleted=deleted)
    return written
'''
ADAPTER_SRC = '''
CANONICAL_AYANAMSHAS = ["lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"]


class W:
    def plan_substeps(self, ctx):
        return [f"ayanamsha_{a}" for a in CANONICAL_AYANAMSHAS]
'''
ES = dict(
    slice=dict(SLICE), post_pass="daridra_dosha_label",
    run_evidence=dict(source=dict(table="orchestrator_event_register", event_type="writer.post_pass_evaluated"),
                      emitter=dict(file=EMIT, function="record_post_pass_evidence"), caller=dict(file=EMIT, function="emit_daridra_label_post_pass"),
                      partitions_from=dict(file=ADAPT, constant="CANONICAL_AYANAMSHAS")),
    cross_check=dict(table="chart_vichara", partition_column="ayanamsha_id", build_column="build_id"),
    entries=["citation_human"], criteria=["Narr.checkable", "Null.blank_rows", "Vocab.alias"], why=WHY, evidence=WRITER + ":3")
ENTRY = dict(kind="data", evidence=dict(prose_fields=WRITER + ":3"), prose_fields=["value_text", "source_citation", "citation_human"],
             produced_tables=[dict(table="chart_vichara"), dict(table="chart_facts", filter=dict(column="fact_subject", equals="daridra"), why="the daridra post-pass row, one per chart and ayanamsha")],
             empty_slice_by_conditional=ES)


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """A tiny repo tree holding the fake writer files (the shape of pr #3448's emitter / caller / plan_substeps) and make it the census ROOT."""
    for rel, src in ((EMIT, EMITTER_SRC), (ADAPT, ADAPTER_SRC), (WRITER, "# writer\n" * 40)):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(src, encoding="utf-8")
    monkeypatch.setattr(ac, "ROOT", tmp_path)
    return tmp_path


def _put(tree, rel, src):
    (tree / rel).write_text(src, encoding="utf-8")


def _es(**kw):
    d = copy.deepcopy(ES)
    for k, v in kw.items():
        d[k] = v
    return d


# ───────────────────────── the declaration validator (M11, M12) ─────────────────────────

def _validate(es, entry=None):
    e = copy.deepcopy(ENTRY if entry is None else entry)
    e["empty_slice_by_conditional"] = es
    ac.validate_empty_slice_by_conditional_declaration("assets['ga_vichara']", "ga_vichara", es, e)


def _doc(entry=None):
    return dict(version="x", kind_enum=list(ac.DECLARED_KINDS), assets={"ga_vichara": copy.deepcopy(ENTRY if entry is None else entry)})


def test_a_well_formed_declaration_validates_alone_and_inside_a_document(tree):
    _validate(_es())
    ac.validate_declarations(_doc())


def test_the_form_has_a_closed_field_list_and_the_document_may_pin_it(tree):
    d = _doc()
    d["empty_slice_by_conditional_declaration_fields"] = list(ac.ES_DECL_FIELDS)
    ac.validate_declarations(d)
    d["empty_slice_by_conditional_declaration_fields"] = ["slice"]
    with pytest.raises(ac.DeclarationsError, match="empty_slice_by_conditional_declaration_fields"):
        ac.validate_declarations(d)


@pytest.mark.parametrize("name,patch,match", [
    ("unknown field", dict(extra="x"), "unknown field"),
    ("slice wrong table", dict(slice=dict(SLICE, table="chart_vichara")), "slice.table"),
    ("slice subject not produced (kemadruma)", dict(slice=dict(SLICE, fact_subject="kemadruma")), "produced_tables"),
    ("slice field missing", dict(slice=dict(table="chart_facts", fact_subject="daridra")), "slice"),
    ("slice identifier", dict(slice=dict(SLICE, fact_category="dosha label")), "fact_category"),
    ("post_pass malformed", dict(post_pass="Daridra Pass"), "post_pass"),
    ("source table not the register", dict(run_evidence=dict(copy.deepcopy(ES["run_evidence"]), source=dict(table="chart_facts", event_type="writer.post_pass_evaluated"))), "source.table"),
    ("event type not the frozen one", dict(run_evidence=dict(copy.deepcopy(ES["run_evidence"]), source=dict(table="orchestrator_event_register", event_type="writer.other"))), "event_type"),
    ("emitter missing a field", dict(run_evidence=dict(copy.deepcopy(ES["run_evidence"]), emitter=dict(file=EMIT))), "emitter"),
    ("constant not upper case", dict(run_evidence=dict(copy.deepcopy(ES["run_evidence"]), partitions_from=dict(file=ADAPT, constant="canonical"))), "constant"),
    ("cross_check missing field", dict(cross_check=dict(table="chart_vichara")), "cross_check"),
    ("cross_check table is the filtered slice", dict(cross_check=dict(table="chart_facts", partition_column="ayanamsha_id", build_column="build_id")), "WITHOUT a filter"),
    ("entry not a declared prose field", dict(entries=["fact_value_text"]), "prose_fields"),
    ("entries empty", dict(entries=[]), "entries"),
    ("entries duplicate", dict(entries=["citation_human", "citation_human"]), "entries"),
    ("criteria unknown", dict(criteria=["Narr.agree"]), "criteria"),
    ("criteria empty", dict(criteria=[]), "criteria"),
    ("why placeholder", dict(why="TBD"), "why"),
    ("why too short", dict(why="short"), "why"),
    ("evidence unverified", dict(evidence="unverified:i believe the writer does it"), "evidence"),
    ("evidence not a file", dict(evidence="platform/python-sidecar/ga_writers/nope.py:1"), "evidence"),
    ("evidence without a line", dict(evidence=WRITER), "file>.py:<line"),
    ("evidence line beyond the file", dict(evidence=WRITER + ":9999"), "evidence"),
])
def test_a_malformed_declaration_is_refused(tree, name, patch, match):
    with pytest.raises(ac.DeclarationsError, match=match):
        _validate(_es(**patch))


def test_a_declaration_with_a_missing_field_is_refused_even_if_the_rest_is_perfect(tree):
    for f in ac.ES_DECL_FIELDS:
        es = _es()
        del es[f]
        with pytest.raises(ac.DeclarationsError, match="missing field"):
            _validate(es)


def test_slice_without_a_filter_in_produced_tables_is_refused(tree):
    e = copy.deepcopy(ENTRY)
    e["produced_tables"][1] = dict(table="chart_facts", why="the whole table")           # a whole table is never a conditional slice
    with pytest.raises(ac.DeclarationsError, match="whole table is never a conditional slice"):
        _validate(_es(), e)


def test_an_asset_that_declares_no_writer_is_refused(tree):
    e = copy.deepcopy(ENTRY)
    e["has_writer"] = False
    with pytest.raises(ac.DeclarationsError, match="has_writer false"):
        _validate(_es(), e)


def test_declaration_without_the_emitter_in_the_writer_source_is_refused(tree):                  # M11
    _put(tree, EMIT, EMITTER_SRC.replace("def record_post_pass_evidence", "def something_else"))
    with pytest.raises(ac.DeclarationsError, match="emitter function"):
        _validate(_es())


def test_declaration_without_the_event_type_literal_in_the_emitter_is_refused(tree):             # M11
    _put(tree, EMIT, EMITTER_SRC.replace('"writer.post_pass_evaluated"', '"writer.renamed"'))
    with pytest.raises(ac.DeclarationsError, match="event type"):
        _validate(_es())


def test_declaration_without_the_schema_literal_in_the_emitter_is_refused(tree):
    _put(tree, EMIT, EMITTER_SRC.replace('"post_pass_evidence/1"', '"post_pass_evidence/9"'))
    with pytest.raises(ac.DeclarationsError, match="evidence schema"):
        _validate(_es())


def test_declaration_whose_caller_never_calls_the_emitter_is_refused(tree):
    _put(tree, EMIT, EMITTER_SRC.replace("record_post_pass_evidence(conn, chart_id, build_id, ayanamsha_id, entries_evaluated=", "other_call(conn, chart_id, build_id, ayanamsha_id, entries_evaluated="))
    with pytest.raises(ac.DeclarationsError, match="never calls the emitter"):
        _validate(_es())


def test_caller_that_records_only_on_the_not_formed_branch_is_refused(tree):                   # W7 mirrored: the formed branch must record too
    src = EMITTER_SRC.replace("    record_post_pass_evidence(conn, chart_id, build_id, ayanamsha_id, entries_evaluated=1, formed=True, rows_written=written, prior_rows_deleted=deleted)\n", "")
    assert src != EMITTER_SRC
    _put(tree, EMIT, src)
    with pytest.raises(ac.DeclarationsError, match="without calling the emitter"):
        _validate(_es())


def test_caller_that_records_only_on_the_formed_branch_is_refused(tree):
    src = EMITTER_SRC.replace("        record_post_pass_evidence(conn, chart_id, build_id, ayanamsha_id, entries_evaluated=1, formed=False, rows_written=0, prior_rows_deleted=deleted)\n", "")
    assert src != EMITTER_SRC
    _put(tree, EMIT, src)
    with pytest.raises(ac.DeclarationsError, match="without calling the emitter"):
        _validate(_es())


def test_a_guarded_caller_that_can_return_early_without_the_record_is_refused(tree):
    src = EMITTER_SRC.replace("    rows = build(conn)\n", "    if conn.dry_run:\n        return 0\n    rows = build(conn)\n")
    _put(tree, EMIT, src)
    with pytest.raises(ac.DeclarationsError, match="without calling the emitter"):
        _validate(_es())


def test_a_record_before_a_branch_covers_every_later_return(tree):
    src = EMITTER_SRC.replace("    if not rows:\n        record_post_pass_evidence(conn, chart_id, build_id, ayanamsha_id, entries_evaluated=1, formed=False, rows_written=0, prior_rows_deleted=deleted)\n        return 0\n",
                              "    record_post_pass_evidence(conn, chart_id, build_id, ayanamsha_id, entries_evaluated=1, formed=not not rows, rows_written=0, prior_rows_deleted=deleted)\n    if not rows:\n        return 0\n")
    _put(tree, EMIT, src)
    _validate(_es())


def test_declaration_whose_post_pass_name_the_caller_does_not_carry_is_refused(tree):
    with pytest.raises(ac.DeclarationsError, match="post_pass"):
        _validate(_es(post_pass="some_other_pass"))


def test_declaration_whose_partition_constant_is_absent_or_unread_is_refused(tree):
    _put(tree, ADAPT, ADAPTER_SRC.replace("CANONICAL_AYANAMSHAS =", "OTHER ="))
    with pytest.raises(ac.DeclarationsError, match="CANONICAL_AYANAMSHAS"):
        _validate(_es())
    _put(tree, ADAPT, ADAPTER_SRC.replace("for a in CANONICAL_AYANAMSHAS", "for a in ['x']"))
    with pytest.raises(ac.DeclarationsError, match="plan_substeps"):
        _validate(_es())
    _put(tree, ADAPT, ADAPTER_SRC.replace('"raman", ', '"raman", "raman", '))
    with pytest.raises(ac.DeclarationsError, match="distinct"):
        _validate(_es())


# ───────────────────────── a fake of the database the detector reads ─────────────────────────

T0 = 1_000_000.0
WINDOW = dict(ok=True, epoch=T0, opens="2026-10-12T00:00:00Z", inclusive=False, basis="fixture")
PATHS = [EMIT, ADAPT, WRITER]


def _rec(part, run=R, chart=CH, at=T0 + 1030, flat=True, **over):
    body = {"schema": "post_pass_evidence/1", "post_pass": "daridra_dosha_label", "ayanamsha_id": part, "slice": dict(SLICE), "entries_evaluated": 1, "formed": False,
            "rows_written": 0, "prior_rows_deleted": 0}
    body.update(over)
    if flat:       # the whole event dict (persist_event) is a SUPERSET of the frozen keys
        body = dict(body, type="writer.post_pass_evaluated", chart_id=chart, asset_id="ga_vichara", run_id=run, rows_present=body["rows_written"])
    return dict(run=run, chart=chart, asset="ga_vichara", at=at, rows=str(over.get("rows_written", 0)), payload=body)


class DB:
    """What the census reads: attempts (oldest first), register rows (newest first), the live slice count and the cross-check table."""

    def __init__(self):
        self.attempts = [
            dict(run=R0, chart=CH, state="complete", disp="build", started=True, created=T0 - 500, st=T0 - 499, en=T0 - 440),
            dict(run=R, chart=CH, state="complete", disp="build", started=True, created=T0 + 1000, st=T0 + 1001, en=T0 + 1060),
        ]
        self.records = [_rec(p) for p in PARTS][::-1]
        self.slice_rows = 0
        self.vichara = {p: (str(1550 + i), "1", R, R) for i, p in enumerate(PARTS)}
        self.errors = {}
        self.ragged = set()
        self.sql = []

    def psql(self, sql, *a, **k):
        self.sql.append(sql)
        for key, tag in (("FROM build_run_assets", "attempts"), ("FROM orchestrator_event_register", "register"), ('FROM "chart_facts"', "slice"), ('FROM "chart_vichara"', "vichara")):
            if key in sql:
                break
        else:
            raise ac.Unknown(f"unexpected sql {sql[:60]}")
        if tag in self.errors:
            raise ac.Unknown(self.errors[tag])
        if tag == "attempts":
            rows = [[a["run"], a["chart"], a["state"], a["disp"], "t" if a["started"] else "f", str(a["created"]), "" if a.get("st") is None else str(a["st"]), "" if a.get("en") is None else str(a["en"])]
                    for a in reversed(self.attempts)]
        elif tag == "register":
            rows = [[str(100 + i), r["run"], r["chart"], r["asset"], str(r["at"]), r["rows"], json.dumps(r["payload"])] for i, r in enumerate(self.records)]
        elif tag == "slice":
            rows = [[str(self.slice_rows)]]
        else:
            rows = [[p, n, d, lo, hi] for p, (n, d, lo, hi) in sorted(self.vichara.items())]
        if tag in self.ragged:
            rows = [r[:-1] for r in rows] or [["x"]]
        return rows


@pytest.fixture
def db(tree, monkeypatch):
    d = DB()
    monkeypatch.setattr(ac, "psql", d.psql)
    return d


def _run(**kw):
    a = dict(window=WINDOW, code_paths=PATHS)
    a.update(kw)
    return ac.empty_slice_conditional_outcome(ES, "ga_vichara", a.pop("chart", CH), **a)


def _mutant(fn, *clauses):
    """`fn` re-defined with the lines between each `#<clause NAME>` and `#</clause NAME>` marker DELETED (the guard is gone, nothing else changes)."""
    src = inspect.getsource(fn)
    for c in clauses:
        pat = re.compile(rf"^[ ]*#<clause {re.escape(c)}>\n.*?^[ ]*#</clause {re.escape(c)}>\n", re.S | re.M)
        src, n = pat.subn("", src)
        assert n == 1, f"clause {c!r} not found exactly once in {fn.__name__}"
    g = dict(vars(ac))
    exec(compile(src, f"<mutant {fn.__name__} -{','.join(clauses)}>", "exec"), g)
    return g[fn.__name__]


def _wrongly_credited(*clauses, **kw):
    """True when the detector with `clauses` deleted credits the case (or crashes where the guard used to answer)."""
    mut = _mutant(ac._es_outcome, *clauses)
    a = dict(window=WINDOW, code_paths=PATHS)
    a.update(kw)
    try:
        out = mut(ES, "ga_vichara", a.pop("chart", CH), a["window"], a["code_paths"])
    except Exception:                                                      # noqa: BLE001
        return True
    return out["state"] == "holds"


def test_positive_control_all_clauses_hold(db):
    out = _run()
    assert out["state"] == "holds" and out["clause"] is None, out
    b = out["evidence"]
    assert b["verified"] is True and b["run_id"] == R and b["partitions"] == sorted(PARTS) and set(b["entries_evaluated"].values()) == {1} and b["live_slice_rows"] == 0
    assert ac.empty_slice_problem("Narr.checkable", dict(empty_slice=b)) is None
    d = out["detail"]
    for needle in (R, "5/5 ayanamsha partitions", "entries evaluated 1/1/1/1/1", "formed false", "chart_facts[fact_category=dosha_label, fact_subject=daridra]"):
        assert needle in d, (needle, d)


def test_the_detector_reads_only_through_read_only_selects_on_validated_identifiers(db):
    _run()
    assert db.sql and all(s.lstrip().upper().startswith("SELECT") for s in db.sql)
    assert all(CH in s for s in db.sql)


@pytest.mark.parametrize("flat", [True, False])
def test_the_record_may_be_the_whole_flat_event_or_the_nested_design_shape(db, flat):
    db.records = [dict(_rec(p, flat=True), payload=(_rec(p, flat=True)["payload"] if flat else {"type": "writer.post_pass_evaluated", "payload": _rec(p, flat=False)["payload"]})) for p in PARTS]
    assert _run()["state"] == "holds"


def test_direct_insert_shape_the_exact_frozen_keys_only_holds(db):
    db.records = [_rec(p, flat=False) for p in PARTS]
    assert _run()["state"] == "holds"


def test_extra_keys_are_tolerated(db):
    db.records = [_rec(p, extra_key="x", another=1) for p in PARTS]
    assert _run()["state"] == "holds"


# ───────────────────────── M1 .. M17 and the headline refusals (each with its mutant) ─────────────────────────
# every row: (id, how to break the world, expected state, expected clause, the clauses the mutant deletes)

def _no_records(d):
    d.records = []


def _four_of_five(d):
    d.records = [_rec(p) for p in PARTS[:4]][::-1]


def _other_chart(d):                                                     # right run id, other chart: a register that hands back rows it was not asked for
    d.records = [_rec(p, chart=OTHER) for p in PARTS][::-1]


def _payload_chart_differs(d):                                           # the payload says another chart than the register column
    d.records = [dict(_rec(p), payload=dict(_rec(p)["payload"], chart_id=OTHER)) for p in PARTS][::-1]


def _older_build_only(d):                                                # evidence exists for the OLDER complete build only
    d.records = [_rec(p, run=R0, at=T0 - 470) for p in PARTS][::-1]


def _older_build_only_in_bracket(d):
    d.records = [_rec(p, run=R0) for p in PARTS][::-1]


def _run_older_than_window(d):
    d.attempts[-1]["created"] = T0 - 10


def _newer_error_never_started(d):                                       # the DEP-ASSERT shape: an errored attempt that never started, newer than the evidenced build
    d.attempts.append(dict(run=RE, chart=CH, state="error", disp="blocked_dependency", started=False, created=T0 + 2000, st=None, en=None))


def _newer_error_started_earlier(d):                                     # created later but its started_at is EARLIER than R's: ordering is by run creation, not started_at
    d.attempts.append(dict(run=RE, chart=CH, state="error", disp="", started=True, created=T0 + 2000, st=T0 + 500, en=T0 + 501))


def _newer_aborted(d):
    d.attempts.append(dict(run=RE, chart=CH, state="aborted", disp="", started=True, created=T0 + 2000, st=T0 + 2001, en=T0 + 2002))


def _newer_running(d):
    d.attempts.append(dict(run=RE, chart=CH, state="running", disp="", started=True, created=T0 + 2000, st=T0 + 2001, en=None))


def _newer_queued_never_started(d):
    d.attempts.append(dict(run=RE, chart=CH, state="queued", disp="", started=False, created=T0 + 2000, st=None, en=None))


def _newer_global_error(d):                                              # a chart-less (global) run that errored after the build
    d.attempts.append(dict(run=RE, chart="", state="error", disp="", started=True, created=T0 + 2000, st=T0 + 2001, en=T0 + 2002))


def _entries_zero(d):
    d.records = [_rec(p, entries_evaluated=0) for p in PARTS][::-1]


def _slice_nonempty(d):
    d.slice_rows = 5


def _formed_true(d):
    d.records = [_rec(p, formed=True, rows_written=1) for p in PARTS][::-1]


def _formed_true_rows_zero(d):
    d.records = [_rec(p, formed=True) for p in PARTS][::-1]


def _rows_written_nonzero(d):
    d.records = [_rec(p, rows_written=1) for p in PARTS][::-1]


def _row_count_disagrees(d):
    d.records = [_rec(p, chart_vichara_rows_inserted=1) for p in PARTS][::-1]       # the live chart_vichara count is 1550+


def _duplicate(d):
    d.records = d.records + [_rec(PARTS[0])]


def _conflicting_duplicate(d):
    d.records = d.records + [_rec(PARTS[0], formed=True, rows_written=1)]           # the older (lower id) record contradicts the newer one


def _vichara_other_build(d):
    d.vichara["raman"] = ("1553", "1", R0, R0)


def _vichara_two_builds(d):
    d.vichara["raman"] = ("1553", "2", R0, R)


def _vichara_partition_missing(d):
    del d.vichara["raman"]


def _outside_bracket_late(d):
    d.records = [_rec(p, at=T0 + 1060 + 600) for p in PARTS][::-1]


def _outside_bracket_early(d):
    d.records = [_rec(p, at=T0 + 900) for p in PARTS][::-1]


def _run_never_ended(d):
    d.attempts[-1]["en"] = None


def _record_json_broken(d):
    d.records[0]["payload"] = "not an object"


def _wrong_post_pass(d):
    d.records = [_rec(p, post_pass="other_pass") for p in PARTS][::-1]


def _wrong_slice(d):
    d.records = [_rec(p, slice=dict(SLICE, fact_subject="kemadruma")) for p in PARTS][::-1]


def _wrong_schema(d):
    d.records = [_rec(p, schema="post_pass_evidence/2") for p in PARTS][::-1]


def _rows_present_column_disagrees(d):
    d.records = [dict(_rec(p), rows="3") for p in PARTS][::-1]


def _phantom_world(d):                                                   # a world in which the evidence IS for the dead phantom chart: only the chart guard refuses it
    d.records = [_rec(p, chart=PHANTOM) for p in PARTS][::-1]


def _unplanned_partition(d):
    d.records = [_rec(p) for p in PARTS][::-1] + [_rec("made_up")]


CASES = [
    ("M1 post-pass not run (no evidence rows)", _no_records, {}, "does_not_hold", "evidence-present", ("evidence-present", "partition-complete")),
    ("M2 only 4 of 5 ayanamsha records", _four_of_five, {}, "does_not_hold", "partition-complete", ("partition-complete",)),
    ("M3 evidence of ANOTHER chart", _other_chart, {}, "does_not_hold", "chart-binding", ("chart-binding",)),
    ("M3 payload chart differs from its column", _payload_chart_differs, {}, "does_not_hold", "record-shape", ("record-shape",)),
    ("M4 evidence from an OLDER build only", _older_build_only_in_bracket, {}, "does_not_hold", "evidence-present", ("run-binding", "evidence-present", "time-bracket")),
    ("M4 older build evidence (also outside the bracket)", _older_build_only, {}, "does_not_hold", "evidence-present", ("run-binding", "evidence-present", "time-bracket")),
    ("M4 the evidenced build predates the writer-code window", _run_older_than_window, {}, "does_not_hold", "in-window", ("in-window",)),
    ("M5 newer attempt errored, never started", _newer_error_never_started, {}, "unverified", "newer-attempt", ("newer-attempt",)),
    ("M5 newer errored attempt created later but started earlier", _newer_error_started_earlier, {}, "unverified", "newer-attempt", ("newer-attempt",)),
    ("M5 newer attempt aborted", _newer_aborted, {}, "unverified", "newer-attempt", ("newer-attempt",)),
    ("M5 newer attempt running", _newer_running, {}, "unverified", "newer-attempt", ("newer-attempt",)),
    ("M5 newer attempt queued, never started", _newer_queued_never_started, {}, "unverified", "newer-attempt", ("newer-attempt",)),
    ("M5 newer errored run of no chart (global)", _newer_global_error, {}, "unverified", "newer-attempt", ("newer-attempt",)),
    ("M6 entries_evaluated = 0", _entries_zero, {}, "does_not_hold", "evaluated", ("evaluated",)),
    ("M7 slice NON-empty now", _slice_nonempty, {}, "does_not_hold", "slice-empty", ("slice-empty",)),
    ("M7 formed = true (rows written 1) while the slice is empty", _formed_true, {}, "does_not_hold", "not-formed", ("not-formed",)),
    ("M7 formed = true with rows_written 0", _formed_true_rows_zero, {}, "does_not_hold", "not-formed", ("not-formed",)),
    ("M7 rows_written 1 while formed false", _rows_written_nonzero, {}, "does_not_hold", "not-formed", ("not-formed",)),
    ("M7 rows the post-pass saw differ from the live count", _row_count_disagrees, {}, "does_not_hold", "same-build", ("same-build",)),
    ("M8 duplicate record for a partition", _duplicate, {}, "does_not_hold", "single-record", ("single-record",)),
    ("M8 conflicting duplicate record", _conflicting_duplicate, {}, "does_not_hold", "single-record", ("single-record",)),
    ("M9 chart_vichara rows come from another build", _vichara_other_build, {}, "does_not_hold", "same-build", ("same-build",)),
    ("M9 chart_vichara rows of two builds in one partition", _vichara_two_builds, {}, "does_not_hold", "same-build", ("same-build",)),
    ("M9 a partition without chart_vichara rows", _vichara_partition_missing, {}, "does_not_hold", "same-build", ("same-build",)),
    ("M10 record after the run ended", _outside_bracket_late, {}, "does_not_hold", "time-bracket", ("time-bracket",)),
    ("M10 record before the run started", _outside_bracket_early, {}, "does_not_hold", "time-bracket", ("time-bracket",)),
    ("M10 the run has no end time", _run_never_ended, {}, "does_not_hold", "time-bracket", ("time-bracket",)),
    ("M11 closure: the emitter is not in the writer closure the window dates", None, dict(code_paths=[WRITER]), "unverified", "closure", ("closure",)),
    ("M14 window cannot be dated", None, dict(window=dict(ok=False, reason="shallow clone")), "unverified", "window", ("window",)),
    ("M14 window not supplied", None, dict(window=None), "unverified", "window", ("window",)),
    ("M15 the phantom chart", _phantom_world, dict(chart=PHANTOM), "unverified", "chart", ("chart",)),
    ("M15 a malformed chart", None, dict(chart="not-a-chart"), "unverified", "chart", ("chart", "attempts")),
    ("record not a JSON object", _record_json_broken, {}, "does_not_hold", "record-shape", None),            # structural: the parse step itself, no guard clause to delete
    ("record names another post-pass", _wrong_post_pass, {}, "does_not_hold", "record-shape", ("record-shape",)),
    ("record names another slice", _wrong_slice, {}, "does_not_hold", "record-shape", ("record-shape",)),
    ("record names another schema", _wrong_schema, {}, "does_not_hold", "record-shape", ("record-shape",)),
    ("register rows_present disagrees with rows_written", _rows_present_column_disagrees, {}, "does_not_hold", "record-shape", ("record-shape",)),
    ("a partition the writer does not plan", _unplanned_partition, {}, "does_not_hold", "partition-complete", ("partition-complete",)),
]


@pytest.mark.parametrize("name,break_world,kw,state,clause,mutated", CASES, ids=[c[0] for c in CASES])
def test_the_case_is_not_credited_and_the_clause_is_what_stops_it(db, name, break_world, kw, state, clause, mutated):
    if break_world is not None:
        break_world(db)
    out = _run(**kw)
    assert out["state"] == state and out["clause"] == clause, out
    assert out["state"] != "holds" and "evidence" not in out
    assert clause in out["clause"] and out["detail"]
    if mutated is not None:
        assert _wrongly_credited(*mutated, **kw), f"deleting {mutated} does not credit this case: the clause is not what protects it"


def test_newer_skip_no_delta_or_probe_rows_do_not_block_the_evidence(db):
    for disp in ("skip_no_delta", ""):
        d = DB()
        d.attempts.append(dict(run=RE, chart=CH, state="complete", disp=disp, started=True, created=T0 + 2000, st=T0 + 2001, en=T0 + 2002))
        ac.psql = d.psql
        assert _run()["state"] == "holds", disp


def test_newer_attempt_of_another_chart_is_not_this_charts_attempt(db):
    # the fake returns every row it holds; the SQL itself restricts to the chart (or a chart-less run): assert the SQL does
    _run()
    q = next(s for s in db.sql if "FROM build_run_assets" in s)
    assert f"r.chart_id::text = '{CH}' OR r.chart_id IS NULL" in q and "started_at IS NOT NULL" not in q.replace("(a.started_at IS NOT NULL)::text", "")
    assert "ORDER BY r.created_at DESC, a.run_id DESC" in q                   # the Build.history ordering convention: run creation, then run id


def test_no_complete_build_at_all_is_unverified_and_the_clause_cannot_be_deleted(db):
    db.attempts = [dict(run=R, chart=CH, state="complete", disp="skip_no_delta", started=True, created=T0 + 1000, st=T0 + 1001, en=T0 + 1002)]
    out = _run()
    assert out["state"] == "unverified" and out["clause"] == "latest-build"
    assert _wrongly_credited("latest-build")                                   # without the guard the detector crashes where it used to answer: it is structural


def test_an_errored_build_is_not_a_complete_build(db):
    db.attempts = [dict(run=R, chart=CH, state="error", disp="build", started=True, created=T0 + 1000, st=T0 + 1001, en=T0 + 1002)]
    assert _run()["clause"] == "latest-build"


def test_the_newest_of_two_complete_builds_is_the_evidenced_one(db):
    db.records = [_rec(p, run=R0, at=T0 - 470) for p in PARTS][::-1]          # only the older build left evidence: the newer one is judged and is not credited
    assert _run()["clause"] == "evidence-present"
    d = DB()
    d.attempts.append(dict(run=RE, chart=CH, state="complete", disp="build", started=True, created=T0 + 3000, st=T0 + 3001, en=T0 + 3060))
    ac.psql = d.psql
    assert _run()["clause"] == "evidence-present"                              # R is no longer the newest; the newest has no record


def test_a_window_that_opens_exactly_at_the_run_counts_only_when_inclusive(db):
    db.attempts[-1]["created"] = T0
    assert _run()["clause"] == "in-window"
    assert _run(window=dict(WINDOW, inclusive=True))["state"] == "holds"


# ───────────────────────── M13 and the unreadable cases: NO_DETECTOR with the cause, never PASS ─────────────────────────

@pytest.mark.parametrize("tag,msg,cause", [
    ("register", "ERROR:  permission denied for table orchestrator_event_register (SQLSTATE 42501)", "permission-denied"),
    ("register", 'ERROR:  relation "orchestrator_event_register" does not exist', "table-missing"),
    ("register", "connection refused", "read-failed"),
])
def test_an_unreadable_register_is_no_detector_with_the_cause(db, tag, msg, cause):                  # M13
    db.errors[tag] = msg
    out = _run()
    assert out["state"] == "unverified" and out.get("no_detector") is True and out.get("cause") == cause and out["detail"].startswith("NO_DETECTOR"), out
    assert "evidence" not in out and out["clause"] == "register-read"
    with pytest.raises(Exception):                                                                   # the mutant has no register read at all: it cannot answer
        _mutant(ac._es_outcome, "register-read")(ES, "ga_vichara", CH, WINDOW, PATHS)


def test_a_ragged_register_answer_is_not_read(db):
    db.ragged.add("register")
    out = _run()
    assert out["state"] == "unverified" and out["clause"] == "register-read" and out.get("no_detector") is True
    assert _wrongly_credited("register-read")


def test_an_unreadable_attempt_log_is_unverified(db):
    db.errors["attempts"] = "permission denied for table build_run_assets"
    out = _run()
    assert out["state"] == "unverified" and out["clause"] == "attempts" and out.get("cause") == "permission-denied"
    assert _wrongly_credited("attempts")


def test_an_unreadable_live_slice_or_cross_check_is_unverified(db):
    db.errors["slice"] = "statement timeout"
    assert _run()["clause"] == "slice-read" and _run()["state"] == "unverified"
    del db.errors["slice"]
    db.errors["vichara"] = "boom"
    out = _run()
    assert out["state"] == "unverified" and out["clause"] == "same-build-read"


def test_a_ragged_slice_count_is_not_credited(db):
    db.slice_rows = "maybe"
    assert _run()["clause"] == "slice-empty" and _run()["state"] == "unverified"


def test_a_declaration_whose_pointers_no_longer_hold_is_not_credited_at_measure_time(db, tree):      # M11 (the measure-time re-check)
    _put(tree, EMIT, EMITTER_SRC.replace("def record_post_pass_evidence", "def gone"))
    out = _run()
    assert out["state"] == "does_not_hold" and out["clause"] == "declaration"
    with pytest.raises(Exception):
        _mutant(ac._es_outcome, "declaration")(ES, "ga_vichara", CH, WINDOW, PATHS)       # the partitions are unknown without it: it cannot answer


def test_the_detector_never_raises(db, monkeypatch):
    monkeypatch.setattr(ac, "_es_outcome", lambda *a: (_ for _ in ()).throw(ValueError("x")))
    out = _run()
    assert out["state"] == "unverified" and out.get("no_detector") is True


# ───────────────────────── the frozen keys: each missing or mistyped key is refused (each with its mutant) ─────────────────────────

FROZEN = ["schema", "post_pass", "ayanamsha_id", "slice", "entries_evaluated", "formed", "rows_written", "prior_rows_deleted"]


@pytest.mark.parametrize("key", FROZEN)
@pytest.mark.parametrize("flat", [True, False])
def test_a_missing_frozen_key_is_refused_and_the_clause_is_what_stops_it(db, key, flat):
    recs = []
    for p in PARTS:
        r = _rec(p, flat=flat)
        r["payload"] = {k: v for k, v in r["payload"].items() if k != key}
        recs.append(r)
    db.records = recs[::-1]
    out = _run()
    assert out["state"] == "does_not_hold" and out["clause"] == "record-shape" and key in out["detail"], out
    assert _wrongly_credited("record-shape") or key == "ayanamsha_id"       # a record without its partition cannot be grouped at all: the mutant crashes, which is the same refusal


MISTYPED = [("schema", 7), ("post_pass", None), ("slice", "chart_facts"), ("entries_evaluated", "1"), ("entries_evaluated", True), ("entries_evaluated", -1),
            ("entries_evaluated", 1.0), ("formed", 0), ("formed", "false"), ("rows_written", "0"), ("rows_written", False), ("rows_written", -1),
            ("prior_rows_deleted", None), ("prior_rows_deleted", True), ("prior_rows_deleted", -3), ("prior_rows_deleted", "0")]


@pytest.mark.parametrize("key,val", MISTYPED)
def test_a_mistyped_frozen_key_is_refused_and_the_clause_is_what_stops_it(db, key, val):
    db.records = [_rec(p, **{key: val}) for p in PARTS][::-1]
    out = _run()
    assert out["state"] == "does_not_hold" and out["clause"] == "record-shape", out
    # the mutant (record-shape deleted) lets the same record through: it credits, or it crashes on the bad value (a frozen key mistyped is never read as a number)
    later = {"entries_evaluated": ("evaluated",), "formed": ("not-formed",), "rows_written": ("not-formed",)}.get(key, ())       # a later clause also refuses these values: the mutant deletes both
    assert _wrongly_credited("record-shape", *later), (key, val)


def test_a_mistyped_optional_row_count_is_refused_and_the_clause_is_what_stops_it(db):
    db.records = [_rec(p, chart_vichara_rows_inserted=db.vichara[p][0]) for p in PARTS][::-1]          # the right number, as a string
    out = _run()
    assert out["clause"] == "record-shape"
    assert _wrongly_credited("record-shape")
    for bad in (None, -1, True, 1.5, [1]):                                                             # other mistypes: refused (the cross-check would also disagree)
        db.records = [_rec(p, chart_vichara_rows_inserted=bad) for p in PARTS][::-1]
        assert _run()["state"] == "does_not_hold"


def test_the_optional_row_count_when_right_is_checked_and_when_absent_is_said_skipped(db):
    db.records = [_rec(p, chart_vichara_rows_inserted=int(db.vichara[p][0])) for p in PARTS][::-1]
    out = _run()
    assert out["state"] == "holds" and out["evidence"]["cross_check"]["row_count_hardening"] == "checked in every partition"
    db.records = [_rec(p) for p in PARTS][::-1]
    assert "skipped in 5 partition" in _run()["evidence"]["cross_check"]["row_count_hardening"]


def test_mutation_of_the_type_checks_is_caught_for_each_numeric_key(db):
    for key, val in (("entries_evaluated", "1"), ("rows_written", "0"), ("prior_rows_deleted", -3), ("formed", 0)):
        d = DB()
        d.records = [_rec(p, **{key: val}) for p in PARTS][::-1]
        ac.psql = d.psql
        assert _run()["clause"] in ("record-shape", "evaluated", "not-formed")
        assert _run()["state"] == "does_not_hold"


# ───────────────────────── M12 / M17: the exemption stays inside its slice table and its entries ─────────────────────────

def test_an_entry_that_a_measured_table_also_holds_is_never_exempted():                              # M12
    blk = dict(entries=["citation_human"])
    own1 = {"chart_vichara": (["value_text", "source_citation"], None, None), "chart_facts": (["citation_human"], None, None)}
    assert ac._es_entry_exempt(blk, "chart_facts", "citation_human", own1) is True
    own2 = {"chart_vichara": (["value_text", "citation_human"], None, None), "chart_facts": (["citation_human"], None, None)}
    assert ac._es_entry_exempt(blk, "chart_facts", "citation_human", own2) is False
    assert ac._es_entry_exempt(blk, "chart_facts", "value_text", own1) is False                       # not a declared entry
    mut = _mutant(ac._es_entry_exempt, "entry-holders")
    assert mut(blk, "chart_facts", "citation_human", own2) is True                                    # the mutant exempts an entry a measured table holds


def _outcome_holds():
    return dict(state="holds", clause=None, detail="d", evidence=_block())


def _block(**kw):
    b = dict(verified=True, form=ac.ES_FORM, slice=dict(SLICE), post_pass="daridra_dosha_label", run_id=R, chart=CH, partitions=sorted(PARTS), partitions_expected=sorted(PARTS),
             entries=["citation_human"], criteria=["Narr.checkable", "Null.blank_rows", "Vocab.alias"], entries_evaluated={p: 1 for p in sorted(PARTS)}, formed=False, rows_written=0,
             window_opens="2026-10-12T00:00:00Z", window_inclusive=False, live_slice_rows=0, cross_check=dict(table="chart_vichara", partitions=5, rows=7774, row_count_hardening="checked in every partition"),
             source=dict(table="orchestrator_event_register", event_type="writer.post_pass_evaluated", schema="post_pass_evidence/1"), records=5)
    b.update(kw)
    return b


def test_the_exemption_does_not_leak_to_another_table(monkeypatch):                                  # M17
    fn = ac.empty_slice_exempt_fn(ES, _outcome_holds)
    assert fn("chart_facts", {})["state"] == "holds"
    assert fn("chart_vichara", {}) is None and fn("some_other_table", {}) is None
    leaked = _mutant(ac.empty_slice_exempt_fn, "per-table-exemption")(ES, _outcome_holds)
    assert leaked("chart_vichara", {})["state"] == "holds"                                            # the mutant exempts every empty table


def _scopes():
    return {"chart_vichara": dict(where='"chart_id" = \'x\'', label="chart 482012f1"), "chart_facts": dict(where='"chart_id" = \'x\' AND (fact_subject = \'daridra\')', label="chart 482012f1; fact_subject = 'daridra'")}


def _both_empty(monkeypatch):
    monkeypatch.setattr(ac, "scalar", lambda sql: "f")


def test_mark_empty_scopes_exempts_only_the_slice_table_and_only_when_it_holds(monkeypatch):
    _both_empty(monkeypatch)
    sc = ac.mark_empty_scopes(_scopes(), exempt_fn=ac.empty_slice_exempt_fn(ES, _outcome_holds))
    cf, cv = sc["chart_facts"], sc["chart_vichara"]
    assert cf["exempt"]["run_id"] == R and "block" not in cf and cf["empty"] is True and "EMPTY BY VERIFIED CONDITIONAL" in cf["label"] and "NO ROWS" not in cf["label"] and "5/5 ayanamsha partitions" in cf["label"]
    assert cv.get("exempt") is None and "NO rows" in cv["block"] and "NO ROWS" in cv["label"]                 # chart_vichara empty: its block stands (M17)


def test_a_declared_but_declined_outcome_keeps_the_block_and_names_the_clause(monkeypatch):
    _both_empty(monkeypatch)
    declined = lambda: dict(state="does_not_hold", clause="evidence-present", detail="no record for the newest build")        # noqa: E731
    sc = ac.mark_empty_scopes(_scopes(), exempt_fn=ac.empty_slice_exempt_fn(ES, declined))
    cf = sc["chart_facts"]
    assert "block" in cf and cf.get("exempt") is None and cf["empty_slice_declined"]["clause"] == "evidence-present"
    assert "NOT credited (evidence-present)" in cf["label"]


def test_without_a_declaration_or_an_exempt_fn_the_scopes_read_exactly_as_before(monkeypatch):
    _both_empty(monkeypatch)
    a = ac.mark_empty_scopes(_scopes())
    b = ac.mark_empty_scopes(_scopes(), exempt_fn=None)
    assert a == b and all("block" in v and v["empty"] and "exempt" not in v for v in a.values())


def test_an_exempt_fn_that_raises_never_exempts(monkeypatch):
    _both_empty(monkeypatch)
    sc = ac.mark_empty_scopes(_scopes(), exempt_fn=lambda t, v: (_ for _ in ()).throw(RuntimeError("x")))
    assert all("block" in v and "exempt" not in v for v in sc.values())


def test_the_exemption_lifts_the_vocab_block_only_when_the_declaration_names_vocab_alias(monkeypatch):
    _both_empty(monkeypatch)
    no_vocab = lambda: dict(state="holds", clause=None, detail="d", evidence=_block(criteria=["Narr.checkable", "Null.blank_rows"]))      # noqa: E731
    sc = ac.mark_empty_scopes(_scopes(), exempt_fn=ac.empty_slice_exempt_fn(ES, no_vocab))
    assert sc["chart_facts"]["exempt"] and "block" in sc["chart_facts"]


def test_a_probe_that_finds_rows_never_asks_the_detector(monkeypatch):
    monkeypatch.setattr(ac, "scalar", lambda sql: "t")
    asked = []
    sc = ac.mark_empty_scopes(_scopes(), exempt_fn=lambda t, v: asked.append(t))
    assert not asked and all("block" not in v for v in sc.values())


# ───────────────────────── the graders (Narr.checkable, Null.blank_rows) ─────────────────────────

PF = ["value_text", "source_citation", "citation_human"]
SCOPE = "chart-scoped by count_sql"
COUNTS = {"value_text": dict(checkable=7509, blank=0, scope=SCOPE), "source_citation": dict(checkable=7774, blank=0, scope=SCOPE), "citation_human": None}


def _ex(block=None):
    return dict(COUNTS, citation_human=dict(exempt=_block() if block is None else block))


def test_today_the_unknown_entry_keeps_both_cells_partial_and_not_clean():
    assert ac.grade_narr_checkable(PF, COUNTS)["v"] == ac.PARTIAL
    br = ac.grade_null_blank_rows(PF, COUNTS)
    assert br["v"] == ac.PARTIAL and "clean" not in br


def test_a_verified_exempt_entry_reads_pass_and_clean_and_states_the_evidence():
    n = ac.grade_narr_checkable(PF, _ex())
    assert n["v"] == ac.PASS and "citation_human=n/a" in n["measured"] and R in n["measured"] and "5/5 ayanamsha partitions" in n["measured"] and "entries evaluated 1/1/1/1/1" in n["measured"], n
    assert n["empty_slice"]["run_id"] == R and n["exempt_entries"] == ["citation_human"]
    b = ac.grade_null_blank_rows(PF, _ex())
    assert b["v"] == ac.PARTIAL and b["clean"] is True and R in b["measured"] and b["measured"].index(R) < b["measured"].index("; schema defaults"), b


@pytest.mark.parametrize("bad", [dict(verified=False), dict(run_id=None), dict(run_id="not-a-uuid"), dict(partitions=sorted(PARTS)[:4]), dict(entries_evaluated={p: 0 for p in PARTS}),
                                 dict(formed=True), dict(rows_written=2), dict(live_slice_rows=3), dict(criteria=["Vocab.alias"]), dict(form="other"), dict(entries=[])])
def test_a_block_that_fails_its_own_re_check_is_not_an_exemption(bad):
    c = _ex(_block(**bad))
    n, b = ac.grade_narr_checkable(PF, c), ac.grade_null_blank_rows(PF, c)
    assert n["v"] == ac.PARTIAL and b["v"] == ac.PARTIAL and "clean" not in b                  # read as unknown, exactly as today
    assert "empty_slice" not in n


def test_all_entries_exempt_is_inconclusive_never_a_pass():
    c = {e: dict(exempt=_block(entries=PF)) for e in PF}
    assert ac.grade_narr_checkable(PF, c)["v"] == ac.NO_DET and ac.grade_null_blank_rows(PF, c)["v"] == ac.NO_DET


def test_an_exempt_entry_does_not_hide_a_blank_row_in_a_measured_entry():
    c = _ex()
    c["value_text"] = dict(checkable=7509, blank=2, scope=SCOPE)
    assert ac.grade_null_blank_rows(PF, c)["v"] == ac.FAIL


def test_the_exemption_is_per_criterion():
    c = _ex(_block(criteria=["Narr.checkable"]))
    assert ac.grade_narr_checkable(PF, c)["v"] == ac.PASS
    assert ac.grade_null_blank_rows(PF, c)["v"] == ac.PARTIAL and "clean" not in ac.grade_null_blank_rows(PF, c)


def test_group_counts_exempts_only_the_declared_entry_of_the_exempt_table(monkeypatch):
    own = {"chart_vichara": (["value_text", "source_citation"], None, None), "chart_facts": (["citation_human", "fact_value_text"], None, None)}
    r = dict(count_sql="SELECT COUNT(*) FROM chart_vichara WHERE chart_id = $1")
    monkeypatch.setattr(ac, "_READ_SCOPE", {"chart_facts": dict(exempt=_block()), "chart_vichara": dict()})
    seen = []
    monkeypatch.setattr(ac, "_table_scope", lambda t, r_, own_, sh: (seen.append(t) or ("WHERE chart_id = $1", SCOPE)))
    monkeypatch.setattr(ac, "prose_row_counts", lambda t, es, tail, types=None: {e: dict(checkable=5, blank=0) for e in es})
    got = ac._group_counts({"chart_facts": ["citation_human", "fact_value_text"], "chart_vichara": ["value_text"]}, r, own, set())
    assert got["citation_human"]["exempt"]["run_id"] == R
    assert got["fact_value_text"]["checkable"] == 5 and got["value_text"]["checkable"] == 5          # a non-declared entry of the empty table is measured as before
    assert seen.count("chart_facts") == 1


# ───────────────────────── the joint Null lift on the REAL ga_vichara writer scan ─────────────────────────

def _real_null_lift(counts):
    aid = "ga_vichara"
    decl = ac.load_asset_declarations()[aid]
    pf = decl["prose_fields"]
    files = ac.registered_ids("")[aid]
    own = {"chart_vichara": (["value_text", "source_citation", "id"], None, None), "chart_facts": (["citation_human", "fact_value_text"], None, None)}
    sd = dict(v=ac.PARTIAL, clean=True, measured="no schema default on the declared prose column(s); writer literal fallbacks and constant columns are not measured here")
    out = {"Null.schema_default": sd, "Null.blank_rows": ac.grade_null_blank_rows(pf, counts)}
    units, beyond = ac._delegation_scope(aid, files)
    su, sb = ac.writer_scan_scope(aid, files)
    ac._apply_writer_scan(out, pf, dict(table="chart_vichara", own=own, units=units, beyond=beyond, scan_units=su, scan_beyond=sb))
    return out


def test_the_joint_null_lift_reads_pass_on_the_real_writer_scan_with_a_verified_exemption_and_not_without():
    before = _real_null_lift(COUNTS)
    assert before["Null.schema_default"]["v"] == ac.PARTIAL and before["Null.blank_rows"]["v"] == ac.PARTIAL, before
    after = _real_null_lift(_ex())
    for c in ac.NULL_CHECKS:
        assert after[c]["v"] == ac.PASS and after[c]["writer_scan"]["verified"] is True, (c, after[c])
        assert after[c]["empty_slice"]["run_id"] == R and R in after[c]["measured"], after[c]["measured"]
    assert "citation_human" in after["Null.schema_default"]["measured"]
    bad = _real_null_lift(_ex(_block(verified=False)))
    assert all(bad[c]["v"] == ac.PARTIAL for c in ac.NULL_CHECKS)


# ───────────────────────── the rollup guard (M16) ─────────────────────────

def _contribution(crit, **meas):
    m = dict(v=ac.PASS, measured="x", **meas)
    return ac._check_contribution(crit, "L1", m, None, None)


@pytest.mark.parametrize("bad", [dict(verified=False), dict(run_id=None), dict(partitions=[]), dict(partitions_expected=["a"]), dict(entries_evaluated={p: 0 for p in PARTS}),
                                 dict(formed=True), dict(rows_written=1), dict(live_slice_rows=2), dict(criteria=["Vocab.alias"]), dict(form="x")])
def test_a_hand_edited_record_that_claims_an_exemption_without_a_verified_block_is_not_credited(bad):   # M16
    got = ac._check_contribution("Narr.checkable", "L1", dict(v=ac.PASS, measured="x", empty_slice=_block(**bad)), None, None)
    assert got["v"] == ac.NO_DET and "not credited" in got["reason"], got
    mut = _mutant(ac._check_contribution, "empty-slice-rollup")
    assert mut("Narr.checkable", "L1", dict(v=ac.PASS, measured="x", empty_slice=_block(**bad)), None, None)["v"] == ac.PASS           # the mutant credits it


def test_a_verified_block_is_honoured_and_a_record_without_one_reads_as_before():
    assert ac._check_contribution("Narr.checkable", "L1", dict(v=ac.PASS, measured="x", empty_slice=_block()), None, None)["v"] == ac.PASS
    assert ac._check_contribution("Narr.checkable", "L1", dict(v=ac.PARTIAL, measured="x"), None, None)["v"] == ac.PARTIAL
    assert ac.empty_slice_problem("Narr.checkable", dict(v=ac.PASS)) is None
    assert ac.empty_slice_problem("Null.schema_default", dict(empty_slice=_block())) is None                          # rides on Null.blank_rows
    assert ac.empty_slice_problem("Null.schema_default", dict(empty_slice=_block(criteria=["Narr.checkable"]))) is not None


# ───────────────────────── Vocab.alias: the exempt table is not read and is not `unread` ─────────────────────────

def _vocab(monkeypatch, scopes):
    monkeypatch.setattr(ac, "vocab_lexicon", lambda *a, **k: None)
    monkeypatch.setattr(ac, "vocab_registered_load", lambda *a, **k: None)
    own = {"chart_facts": (["citation_human", "fact_value_text"], {"citation_human": "text", "fact_value_text": "text"})}
    return ac.vocab_value_detect(own, None, scopes=scopes)


def test_vocab_alias_an_exempt_table_is_neither_read_nor_unread(monkeypatch):
    blocked = _vocab(monkeypatch, {"chart_facts": dict(where="x", label="chart 482012f1; NO ROWS in this scope", block="the table holds NO rows in the read scope (c): vacuous")})
    assert "NO rows" in blocked["measured"] and "empty_slice" not in blocked                      # today: the zero-row text is an unread finding
    ok = _vocab(monkeypatch, {"chart_facts": dict(where="x", label="l", exempt=_block())})
    assert "NO rows" not in ok["measured"] and "unread" not in ok["measured"], ok["measured"]
    assert ok["empty_slice"]["run_id"] == R and ok["measured"].endswith(ac.empty_slice_text(_block())) and R in ok["measured"]
    leaky = _vocab(monkeypatch, {"chart_facts": dict(where="x", label="l", exempt=_block(criteria=["Narr.checkable"]), block="the table holds NO rows in the read scope (c): vacuous")})
    assert "NO rows" in leaky["measured"] and "empty_slice" not in leaky


VOCAB_CELL = ("vocabulary values found by value in 3 column(s): chart_vichara.subject (graha: JUP, KET_MEAN, MAR), chart_vichara.actor (graha: JUP, KET_MEAN, MAR, MER, MOON, RAH_MEAN), "
              "chart_vichara.value_jsonb (rashi: Aries, Libra, Scorpio); every whole value found is canonical, but: chart_vichara.value_jsonb was read by a bounded sample only{unread}; "
              "embedded vocabulary, spelling unchecked: chart_vichara.ayanamsha_id ('true_chitra'); chart_vichara.target ('D108_HOUSE_10', 'D108_HOUSE_11', 'D108_HOUSE_12'); chart_vichara.value_jsonb ('sign')")
ZERO_ROW_UNREAD = ("; unread: chart_facts: the table holds NO rows in the read scope (chart 482012f1; the asset's declared produced rows (1 filter, ORed): fact_subject = 'daridra'): "
                   "there is nothing to judge, and a closure / vocabulary / source over zero rows is vacuous, never a pass")


def test_postprocess_the_zero_row_unread_text_stays_a_blocker_and_the_verified_text_is_a_named_ceiling():
    today = VOCAB_CELL.format(unread=ZERO_ROW_UNREAD)
    assert cp.m_vocab("ga_vichara", today) is None and cp.m_vocab_embedded_only("ga_vichara", today) is None
    verified = VOCAB_CELL.format(unread="") + f"; chart_facts: {ac.empty_slice_text(_block())}"
    got = cp.m_vocab("ga_vichara", verified)
    assert got and "bounded sample only: chart_vichara.value_jsonb" in got and "embedded text, spelling unchecked, in chart_vichara.ayanamsha_id" in got, got
    assert cp.m_vocab("ga_vichara", VOCAB_CELL.format(unread="")) == got                          # the segment is evidence: it changes nothing else
    assert cp.m_vocab("ga_vichara", VOCAB_CELL.format(unread="") + "; chart_facts: something else entirely") is None


# ───────────────────────── the data constants (registry text proposals) and the bookkeeping table ─────────────────────────

def test_the_registry_text_proposals_are_data_with_the_shape_the_earlier_forms_use():
    adds = ac.ES_APPLICABILITY_ADDITIONS
    assert set(adds) == set(ac.ES_REVISION_BUMPS) == {"Vocab.alias", "Null.blank_rows", "Narr.checkable", "Null.schema_default"}
    for crit, tail in adds.items():
        assert tail.startswith("; SS N-431/N-545 (opt-in") and "empty_slice_by_conditional" in tail and 150 < len(tail) < 3000, crit
        assert tail.count(";") >= 1 and "\n" not in tail and tail == tail.strip(), crit
        old, new = ac.ES_REVISION_BUMPS[crit]
        assert new == old + 1
        rev = ac.CRITERION_REGISTRY[crit]["revision"]
        assert rev in (old, new), (crit, rev)
        if rev == old:                                               # not yet bumped (the ONE bump is a later step): the text is not in the registry either
            assert tail not in ac.CRITERION_REGISTRY[crit]["applicability"]
        else:
            assert tail in ac.CRITERION_REGISTRY[crit]["applicability"]
    assert all(c in ac.CRITERION_REGISTRY for c in adds)
    for crit in ("Vocab.alias", "Null.blank_rows", "Narr.checkable"):
        for word in ("NEWEST", "ALL of", "orchestrator_event_register", "post_pass_evidence/1", "NO_DETECTOR"):
            assert word in adds[crit], (crit, word)


def test_this_branch_did_not_bump_the_registry_or_change_criterion_text():
    assert ac.REGISTRY_REVISION == 29
    for crit in ac.ES_APPLICABILITY_ADDITIONS:
        assert ac.CRITERION_REGISTRY[crit]["revision"] == ac.ES_REVISION_BUMPS[crit][0]
        assert "empty_slice_by_conditional" not in ac.CRITERION_REGISTRY[crit]["applicability"]


def test_the_event_register_is_an_orchestrator_bookkeeping_table():
    assert "orchestrator_event_register" in ac.BOOKKEEPING_TABLES


def test_the_pinned_constants_are_the_frozen_contract():
    assert ac.ES_EVENT_TYPE == "writer.post_pass_evaluated" and ac.ES_EVIDENCE_SCHEMA == "post_pass_evidence/1"
    assert set(ac.ES_PAYLOAD_REQUIRED) == set(FROZEN) and ac.ES_PAYLOAD_OPTIONAL == ("chart_vichara_rows_inserted",)


# ───────────────────────── the committed declarations file and the ga_vichara patch ─────────────────────────

PATCH = pathlib.Path("/Users/Dev/suvarna-evidence/N431/declaration_patches_ga_vichara_empty_slice.json")


def test_the_committed_declarations_do_not_declare_the_form_yet():
    assert [a for a, e in ac.load_asset_declarations().items() if ac.ES_FORM in e] == []


def test_the_form_is_inert_for_an_asset_that_does_not_declare_it(monkeypatch):
    _both_empty(monkeypatch)
    called = []
    sc = ac.mark_empty_scopes(_scopes(), exempt_fn=None)
    assert not called and all("exempt" not in v and "empty_slice_declined" not in v for v in sc.values())


# ───────────────────────── measure() wiring (the hook points of design 3.3), with the heavy readers stubbed ─────────────────────────

def _measure_world(monkeypatch, tmp_path, decl_extra, outcome):
    reg = dict(asset_id="ga_vichara", has_writer=True, target_table="chart_vichara", count_sql="SELECT COUNT(*) FROM chart_vichara WHERE chart_id = $1",
               has_integrity=False, integrity_sql=None, depends_on=[], target_floor="0", catalog_status="CURRENT", asset_kind="data")
    rec = dict(state="lit", rows_written="7774", rps="", last_built="2026-10-11", n_rows=1, ambiguous=False, _key=(0.0, 0.0), built_epoch="0", duration=None)
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    monkeypatch.setattr(ac, "registry", lambda k: ({"ga_vichara": reg}, dict(registry_total=1, active=1, excluded_inactive=[])))
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists={"chart_vichara", "chart_facts"}, keys={"chart_vichara": [], "chart_facts": []},
                                                       cols={"chart_vichara": ["id", "chart_id", "ayanamsha_id", "value_text", "source_citation", "build_id"],
                                                             "chart_facts": ["id", "chart_id", "fact_subject", "fact_category", "citation_human", "fact_value_text"]}))
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {})
    monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: ({x: 7774 for x in r}, {}))
    monkeypatch.setattr(ac, "throughput", lambda prefix, *a, **k: {"ga_vichara": {ac.CHART_ID: dict(rec)}})
    monkeypatch.setattr(ac, "build_history", lambda prefix, *a, **k: dict(per={}, global_runs=0, global_with_layer=0, lit=set()))
    monkeypatch.setattr(ac, "latest_attempts", lambda ids: ({}, None))
    monkeypatch.setattr(ac, "dependency_graph", lambda: {"ga_vichara": []}, raising=False)
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: False)
    monkeypatch.setattr(ac, "capability_scan", lambda d, t, **kw: dict(modules=[], density=0, note="stub"))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=1, full=[], never=[], note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)
    monkeypatch.setattr(ac, "produced_set_reading", lambda *a, **k: dict(error=None, total=7774, parts=[], excluded=[], extra=[], complete=True, unproven=[]))
    monkeypatch.setattr(ac, "produced_set_text", lambda p: "stub produced set")
    monkeypatch.setattr(ac, "produced_set_verdict", lambda cell, p: cell)
    d = dict(kind="data", prose_fields=list(PF), produced_tables=copy.deepcopy(ENTRY["produced_tables"]))
    d.update(decl_extra)
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {"ga_vichara": d})
    monkeypatch.setattr(ac, "psql", lambda sql, *a, **k: [["f" if '"chart_facts"' in sql else "t"]] if "EXISTS" in sql else (_ for _ in ()).throw(ac.Unknown("not faked")))
    seen = dict(vocab=None, prose=None, asked=[])
    monkeypatch.setattr(ac, "_measure_prose", lambda *a, **k: (seen.__setitem__("prose", copy.deepcopy(dict(ac._READ_SCOPE))) or
                                                             {"Narr.checkable": dict(v=ac.PARTIAL, measured="x"), "Null.blank_rows": dict(v=ac.PARTIAL, measured="y")}))
    monkeypatch.setattr(ac, "vocab_value_detect", lambda own, udts=None, **k: (seen.__setitem__("vocab", copy.deepcopy(k.get("scopes"))) or dict(v=ac.PARTIAL, measured="z")))
    monkeypatch.setattr(_WH, "window", lambda self, aid, hw, files: (WINDOW, PATHS))

    def out(decl_, aid, chart, **kw):
        seen["asked"].append((aid, chart, kw))
        return outcome
    monkeypatch.setattr(ac, "empty_slice_conditional_outcome", out)
    return seen


_WH = ac._WindowedHistory


def _cells(census):
    return next(a for a in census["assets"] if a["asset_id"] == "ga_vichara")["measurements"]


def test_measure_hands_the_verified_exemption_to_the_prose_and_vocabulary_readers(monkeypatch, tmp_path):
    seen = _measure_world(monkeypatch, tmp_path, {ac.ES_FORM: _es()}, _outcome_holds())
    m = _cells(ac.measure("L1"))
    assert seen["asked"] and seen["asked"][0][0] == "ga_vichara" and seen["asked"][0][1] == ac.CHART_ID
    assert seen["asked"][0][2]["window"] == WINDOW and seen["asked"][0][2]["code_paths"] == PATHS
    for where in ("vocab", "prose"):
        sc = seen[where]
        assert sc["chart_facts"]["exempt"]["run_id"] == R and "block" not in sc["chart_facts"], (where, sc["chart_facts"])
        assert "exempt" not in sc["chart_vichara"]
    assert "empty_slice_declined" not in m["Narr.checkable"]
    assert "EMPTY BY VERIFIED CONDITIONAL" in m["Narr.checkable"]["read_scope"]["chart_facts"]


def test_measure_a_declined_exemption_reads_as_today_and_names_the_clause_on_the_cells(monkeypatch, tmp_path):
    seen = _measure_world(monkeypatch, tmp_path, {ac.ES_FORM: _es()}, dict(state="does_not_hold", clause="evidence-present", detail="no record"))
    m = _cells(ac.measure("L1"))
    assert "block" in seen["vocab"]["chart_facts"] and "exempt" not in seen["vocab"]["chart_facts"]
    for crit in ("Narr.checkable", "Null.blank_rows"):
        assert m[crit]["v"] == ac.PARTIAL and m[crit]["measured"] in ("x", "y")                                # the text is untouched
        assert m[crit]["empty_slice_declined"]["clause"] == "evidence-present" and m[crit]["empty_slice_declined"]["table"] == "chart_facts"
        assert "NOT credited (evidence-present)" in m[crit]["read_scope"]["chart_facts"]


def test_measure_without_a_declaration_never_asks_the_detector(monkeypatch, tmp_path):
    seen = _measure_world(monkeypatch, tmp_path, {}, _outcome_holds())
    m = _cells(ac.measure("L1"))
    assert seen["asked"] == [] and "block" in seen["vocab"]["chart_facts"] and "empty_slice_declined" not in m["Narr.checkable"]
    assert "NO ROWS in this scope" in m["Narr.checkable"]["read_scope"]["chart_facts"]


@pytest.mark.skipif(not PATCH.is_file(), reason="the declaration patch file lives in the suvarna evidence folder, outside the repository")
def test_the_ga_vichara_patch_applies_its_guards_and_validates_once_the_writer_side_is_in_the_tree(monkeypatch):
    patch = json.loads(PATCH.read_text(encoding="utf-8"))
    assert patch["version"] == "0" and all(o["asset"] == "ga_vichara" and o["op"] == "set" and "expect" in o for o in patch["ops"])
    e = copy.deepcopy(ac.load_asset_declarations()["ga_vichara"])
    for op in patch["ops"]:
        node = e
        for k in op["path"][:-1]:
            node = node[k]
        k = op["path"][-1]
        cur = node[k] if ((isinstance(node, dict) and k in node) or (isinstance(node, list) and isinstance(k, int) and k < len(node))) else None
        assert cur == op["expect"], op["path"]                                    # the guard
        node[op["path"][-1]] = op["value"]
    es = e["empty_slice_by_conditional"]
    assert es["slice"] == SLICE and es["entries"] == ["citation_human"] and es["post_pass"] == "daridra_dosha_label" and es["run_evidence"]["emitter"]["function"] == "record_post_pass_evidence"
    assert es["run_evidence"]["caller"] == dict(file=EMIT, function="emit_daridra_label_post_pass") and es["run_evidence"]["partitions_from"] == dict(file=ADAPT, constant="CANONICAL_AYANAMSHAS")
    # the writer side (pr #3448) is not in this tree: the validator refuses the declaration here, exactly as it must (a declaration without its emitter) ...
    with pytest.raises(ac.DeclarationsError, match="record_post_pass_evidence"):
        ac.validate_empty_slice_by_conditional_declaration("assets['ga_vichara']", "ga_vichara", es, e)
    # ... and, with only the pointer check stood in for, every other rule of the form holds
    monkeypatch.setattr(ac, "empty_slice_static_problem", lambda d: (None, list(PARTS)))
    ac.validate_empty_slice_by_conditional_declaration("assets['ga_vichara']", "ga_vichara", es, e)


def test_a_writer_that_inserts_the_evidence_record_does_not_write_an_undeclared_table(monkeypatch):
    """Build.completion FAILs a table the writer writes that the declared set does not name -- except the orchestrator's bookkeeping tables: the evidence register is one of them."""
    import ast as _ast
    src = ('def f(conn):\n    conn.execute("INSERT INTO chart_vichara (a) VALUES (1)")\n'
           '    conn.execute("INSERT INTO orchestrator_event_register (event_type, payload) VALUES (%s, %s)", [1, 2])\n'
           '    conn.execute("INSERT INTO some_other_table (a) VALUES (1)")\n')
    tree = _ast.parse(src)
    units = [dict(rel="w.py", path=pathlib.Path("w.py"), tree=tree, nodes=[tree], hop=0, via="w.py")]
    monkeypatch.setattr(ac, "_delegation_scope", lambda aid, files, hops=None: (units, []))
    got = ac.produced_set_written("ga_vichara", ["w.py"])
    assert "orchestrator_event_register" not in got["written"] and got["written"] == ["chart_vichara", "some_other_table"]


@pytest.mark.parametrize("patch", [dict(cross_check=dict(table="chart_vichara; drop", partition_column="ayanamsha_id", build_column="build_id")),
                                   dict(slice=dict(SLICE, fact_subject="daridra' OR '1'='1")), dict(post_pass="X Y"), dict(slice="x"),
                                   dict(run_evidence=dict(ES["run_evidence"], source=dict(table="chart_facts", event_type="writer.post_pass_evaluated")))])
def test_a_declaration_that_was_not_validated_is_never_interpolated_into_a_statement(db, patch):
    d = _es(**patch)
    out = ac.empty_slice_conditional_outcome(d, "ga_vichara", CH, window=WINDOW, code_paths=PATHS)
    assert out["state"] == "unverified" and out["clause"] == "declaration" and db.sql == []
    assert ac.empty_slice_conditional_outcome(ES, "ga_vichara; x", CH, window=WINDOW, code_paths=PATHS)["state"] == "unverified"
