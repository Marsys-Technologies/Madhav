"""test_n169_build_recorded_d3.py: N-169 / SS N-180 Option C, the engine side: Carr.D3 for ga_positions reads the BUILD'S RECEIPT instead of re-deriving from birth data (the census role has no
access to the birth parameters) and instead of a persisted note (the orchestrator persists none on a completed attempt).

What this pins (earned-signal rule: no PASS without a detector, and every mutation turns the cell off PASS):
  * the declaration (REAL asset_declarations.json) validates (read includes build_id; `recorded` names the digest file and the bound verifier), and the validator refuses a malformed one;
  * PASS only when: the latest completed build attempt (state complete AND disposition build) has a PROVEN receipt whose code_digest EQUALS the expected digest, whose build_id is that attempt's run id
    (or a later delta-skip's), and EVERY row carries build_id = that run id, with the declared logical row count; the record passes carriage_d3.d3_evidence_problem and the rollup honours it;
  * NO_DETECTOR (named cause) for: no attempt, a failed attempt read, no completed build attempt, a receipt unread / missing / ambiguous / unproven / stale (code digest) / of another build, an
    unavailable expected digest, unreadable rows, a supplied notes record that is unparseable or names a disallowed backend;
  * FAIL for: an attempt refused by the second calculation (the persisted error text, mismatch or underivable row), rows that are not the verified build's (equal counts, other build_id), a supplied
    record naming a mismatch / another build / disagreeing counts;
  * PARTIAL for: a supplied record's not_derived above the allowance, a logical count that differs from the declaration, a read that does not cover the asset;
  * a PASS needs no notes; the census issues NO statement against `charts` and never calls the birth-parameter read.
Fixtures are synthetic row sets of the real shape (1,205 rows: 5 ayanamshas x 241) and fixture build records / receipts; no database, no birth data.
"""
from __future__ import annotations

import copy
import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402

d3 = ac._carriage_d3()
AID = "ga_positions"
KW = dict(column_types=None, prose_columns=[])
NO_DET, PASS, PARTIAL, FAIL, NA = ac.NO_DET, ac.PASS, ac.PARTIAL, ac.FAIL, ac.NA

AYS = ("lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical")
GRAHAS = ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN")
GRAHA_KEYS = (("graha_position", ("longitude_sidereal", "sign", "sign_lord", "nakshatra", "nakshatra_lord", "pada", "house_d1", "retrograde_flag", "combustion_state")),
              ("graha_sign_attributes", ("sign_num", "degree_in_sign")),
              ("house_chalit", ("chalit_house_sripati", "whole_sign_house", "dist_to_madhya_deg", "dist_to_nearest_boundary_deg", "nearest_boundary")),
              ("sandhi_flag", ("sandhi_flag", "sandhi_reasons")))
LAGNA_KEYS = (("graha_position", ("longitude_sidereal", "sign", "sign_lord", "pada", "house_d1")), ("graha_sign_attributes", ("sign_num", "degree_in_sign")))
CUSPS = tuple(f"{sy}_{e}" for sy in ("sripati", "placidus") for e in ("start", "madhya", "end"))

RUN = "aaaaaaaa-1111-4111-8111-111111111111"
DIGEST = "ab" * 32
RECORD = (f"chart_facts=1205; positions_second_calc matched=1205 not_matched=0 not_derived=0 boundary_tolerated=0 rows=1205 build_id={RUN} ayanamshas="
          + ",".join(f"{a}:241" for a in AYS) + "; ephemeris_backend=swieph")


def _rows():
    rows = []
    for ay in AYS:
        def add(cat, subj, key):
            rows.append(dict(ayanamsha_id=ay, fact_category=cat, fact_subject=subj, fact_key=key, fact_value_num=1.0, fact_value_text=None, build_id=RUN))
        for g in GRAHAS:
            for cat, keys in GRAHA_KEYS:
                for k in keys:
                    add(cat, g, k)
        for cat, keys in LAGNA_KEYS:
            for k in keys:
                add(cat, "LAGNA", k)
        for h in range(1, 13):
            for k in CUSPS:
                add("bhava_cusps", f"BHAVA_{h:02d}", k)
    return rows


def _spec():
    return copy.deepcopy(json.loads((HERE.parent / "asset_declarations.json").read_text())["assets"][AID]["carriage"]["spec"])


def _car():
    return json.loads((HERE.parent / "asset_declarations.json").read_text())["assets"][AID]["carriage"]


def attempt(state="complete", disposition="build", notes=None, error="", run=RUN, when="2026-10-07"):
    return dict(run_id=run, state=state, disposition=disposition, when=when, error=error, notes=notes)


def receipt(**over):
    r = dict(receipt_state="proven", code_digest=DIGEST, build_id=RUN, partition_key="whole_asset", observed_at="2026-10-07 01:00:00+00")
    r.update(over)
    return r


EXPECTED = dict(value=DIGEST, source="platform/src/generated/nirmana-writer-digests.json writers.ga_positions", why="")


REFUSAL = ("PositionsSecondCalcMismatch: positions second calculation: matched=1195 not_matched=10 not_derived=0 first mismatches: lahiri_chitrapaksha:(RAH_MEAN, retrograde_flag, "
           "writer='direct', verifier='retrograde')")


def measure(attempts, rows=None, spec=None, receipts="default", expected="default", **kw):
    kw.setdefault("asset_rows", 1205)
    return d3.d3_recorded_measure(spec or _spec(), attempts, rows if rows is not None else _rows(), "chart_facts",
                                  receipts=[receipt()] if receipts == "default" else receipts, expected_digest=EXPECTED if expected == "default" else expected, **kw)


def test_the_fixture_has_the_real_shape():
    rows = _rows()
    assert len(rows) == 1205 and len({(r["fact_subject"], r["ayanamsha_id"]) for r in rows}) == 110


# ───────────────────────── the declaration ─────────────────────────

def test_the_real_declaration_validates_and_names_the_form():
    spec = _spec()
    assert spec["form"] == d3.FORM_BUILD_RECORDED and spec["recorded"]["marker"] == "positions_second_calc" and spec["recorded"]["not_derived_allowance"] == 0
    assert "build_id" in spec["read"]["columns"]
    assert spec["recorded"]["writer_digest_file"] == "platform/src/generated/nirmana-writer-digests.json"
    assert spec["recorded"]["binds"] == "platform/python-sidecar/ga_writers/_positions_independent_verifier.py"
    d3.validate_spec(spec, "x", asset_id=AID)
    doc = json.loads((HERE.parent / "asset_declarations.json").read_text())
    ac.validate_declarations(doc)


@pytest.mark.parametrize("mutate,msg", [
    (lambda s: s.pop("recorded"), "declared together"),
    (lambda s: s.pop("form"), "declared together"),
    (lambda s: s.__setitem__("form", "nope"), "not a reviewed form"),
    (lambda s: s["recorded"].__setitem__("marker", "other_marker"), "recorded must be"),
    (lambda s: s["recorded"].__setitem__("not_derived_allowance", -1), "recorded must be"),
    (lambda s: s["recorded"].__setitem__("not_derived_allowance", True), "recorded must be"),
    (lambda s: s["recorded"].__setitem__("basis", "short"), "recorded must be"),
    (lambda s: s["recorded"].__setitem__("extra", 1), "recorded must be"),
    (lambda s: s["recorded"].pop("binds"), "recorded must be"),
    (lambda s: s["recorded"].__setitem__("writer_digest_file", "/etc/passwd"), "recorded must be"),
    (lambda s: s["recorded"].__setitem__("binds", "../x.py"), "recorded must be"),
])
def test_the_validator_refuses_a_malformed_form(mutate, msg):
    s = _spec()
    mutate(s)
    with pytest.raises(d3.SpecError, match=msg):
        d3.validate_spec(s, "x", asset_id=AID)


def test_a_declared_pointer_that_does_not_exist_is_refused_by_the_declaration_validator():
    doc = json.loads((HERE.parent / "asset_declarations.json").read_text())
    doc["assets"][AID]["carriage"]["spec"]["recorded"]["binds"] = "platform/python-sidecar/ga_writers/_no_such_verifier.py"
    with pytest.raises(ac.DeclarationsError, match="not an existing"):
        ac.validate_declarations(doc)


def test_a_form_is_not_reviewed_for_a_method_it_does_not_name():
    s = _spec()
    s["method"] = "swisseph_sky_events_v1"
    with pytest.raises(d3.SpecError):
        d3.validate_spec(s, "x")


# ───────────────────────── PASS: the receipt, the digest, the build id ─────────────────────────

def test_pass_needs_no_note():
    m = measure([attempt()])
    assert m["v"] == PASS, m["measured"]
    ev = m["d3"]
    assert (ev["rows_total"], ev["rows_checked"], ev["rows_agree"], ev["n_mismatch"], ev["logical_rows"]) == (1205, 1205, 1205, 0, 110)
    assert ev["recorded"] is None and ev["backend"]["name"] == "swieph" and ev["form"] == d3.FORM_BUILD_RECORDED and ev["independence"] == "independent_formula"
    assert ev["receipt"]["receipt_state"] == "proven" and ev["expected_code_digest"] == DIGEST and ev["attempt"]["run_id"] == RUN
    assert d3.d3_evidence_problem(m) == ""
    assert "rests on no persisted note" in ev["claims"] and "re-derived nothing" in ev["claims"]


def test_pass_with_a_supplied_matching_note_is_still_pass():
    m = measure([attempt(notes=RECORD)])
    assert m["v"] == PASS and m["d3"]["recorded"]["build_id"] == RUN and d3.d3_evidence_problem(m) == ""


def test_the_latest_completed_build_attempt_is_the_one_read():
    old = attempt(run="bbbbbbbb-1111-4111-8111-111111111111")
    skip = attempt(disposition="skip_no_delta", run="cccccccc-1111-4111-8111-111111111111")
    m = measure([skip, attempt(), old], receipts=[receipt(build_id="cccccccc-1111-4111-8111-111111111111")])        # a later delta-skip re-stamped the receipt: still this build's
    assert m["v"] == PASS and m["d3"]["attempt"]["run_id"] == RUN


def test_pass_flows_through_the_census_and_the_rollup_honours_it(monkeypatch):
    monkeypatch.setattr(ac, "d3_fetch_rows", lambda table, read, chart_id=None: _rows())
    monkeypatch.setattr(ac, "d3_recorded_attempts", lambda aid, chart_id, limit=25: [attempt()])
    monkeypatch.setattr(ac, "d3_recorded_receipts", lambda aid, chart_id: [receipt()])
    monkeypatch.setattr(ac, "d3_expected_writer_digest", lambda aid, rel: EXPECTED)
    got = ac.carriage_declared_checks(AID, _car(), "chart_facts", True, asset_rows=1205, **KW)
    assert got["Carr.D3"]["v"] == PASS, got["Carr.D3"]["measured"]
    assert got["Carr.D1"]["v"] == NA and got["Carr.D2"]["v"] == NA
    assert ac.rollup_asset("L1", got)["Carr"]["v"] == PASS


def test_the_census_never_reads_charts_or_calls_the_birth_read(monkeypatch):
    sqls = []
    monkeypatch.setattr(ac, "scalar", lambda sql: sqls.append(sql) or ("1205" if sql.startswith("SELECT count") else json.dumps(_rows())))

    def psql(sql, timeout=None, **k):
        sqls.append(sql)
        if "jsonb_agg" in sql:
            return [[json.dumps(_rows())]]
        if "asset_provenance_receipts" in sql:
            r = receipt()
            return [[r["receipt_state"], r["code_digest"], r["build_id"], r["partition_key"], r["observed_at"]]]
        a = attempt()
        return [[a["run_id"], a["state"], a["disposition"], a["when"], a["error"]]]
    monkeypatch.setattr(ac, "psql", psql)
    monkeypatch.setattr(ac, "d3_fetch_inputs", lambda *a, **k: pytest.fail("the build-recorded form must not read the birth parameters"))
    monkeypatch.setattr(ac, "d3_expected_writer_digest", lambda aid, rel: EXPECTED)
    got = ac.carriage_declared_checks(AID, _car(), "chart_facts", True, asset_rows=1205, **KW)
    assert got["Carr.D3"]["v"] == PASS, got["Carr.D3"]["measured"]
    assert not any(re.search(r"\bcharts\b", q) for q in sqls), sqls
    assert any("build_run_assets" in q for q in sqls) and any("asset_provenance_receipts" in q for q in sqls)


# ───────────────────────── NO_DETECTOR, each with its cause ─────────────────────────

@pytest.mark.parametrize("kw,cause", [
    (dict(attempts=None), "attempt-read-failed"),
    (dict(attempts=[]), "no-build-record"),
    (dict(attempts=[attempt(state="error", disposition="", error="RuntimeError: boom")]), "no-completed-build-attempt"),
    (dict(attempts=[attempt(disposition="skip_no_delta")]), "no-completed-build-attempt"),
    (dict(attempts=[attempt(state="error", disposition="build")]), "no-completed-build-attempt"),          # only state 'complete' counts
    (dict(attempts=[attempt(state="aborted", disposition="build")]), "no-completed-build-attempt"),
    (dict(attempts=[attempt()], receipts=None), "receipt-read-failed"),
    (dict(attempts=[attempt()], receipts=[]), "receipt-missing"),
    (dict(attempts=[attempt()], receipts=[receipt(), receipt(partition_key="other")]), "receipt-ambiguous"),
    (dict(attempts=[attempt()], receipts=[receipt(receipt_state="unknown")]), "receipt-unproven"),
    (dict(attempts=[attempt()], receipts=[receipt(receipt_state="")]), "receipt-unproven"),
    (dict(attempts=[attempt()], receipts=[receipt(code_digest="cd" * 32)]), "receipt-code-digest-not-current"),
    (dict(attempts=[attempt()], receipts=[receipt(code_digest=None)]), "receipt-code-digest-not-current"),
    (dict(attempts=[attempt()], expected=None), "expected-digest-unavailable"),
    (dict(attempts=[attempt()], expected=dict(value=None, source="x", why="OSError reading the inventory")), "expected-digest-unavailable"),
    (dict(attempts=[attempt()], expected=dict(value="not-hex", source="x", why="")), "expected-digest-unavailable"),
    (dict(attempts=[attempt()], receipts=[receipt(build_id="dddddddd-1111-4111-8111-111111111111")]), "receipt-not-from-this-build"),
    (dict(attempts=[attempt()], receipts=[receipt(build_id=None)]), "receipt-not-from-this-build"),
    (dict(attempts=[attempt(notes="chart_facts=1205")]), "record-unparseable"),
    (dict(attempts=[attempt(notes=RECORD.replace("rows=1205", "rows=twelve"))]), "record-unparseable"),
    (dict(attempts=[attempt(notes=RECORD.replace("lahiri_chitrapaksha:241,", "lahiri_chitrapaksha:241,lahiri_chitrapaksha:241,"))]), "record-unparseable"),
    (dict(attempts=[attempt(notes=RECORD.replace("ephemeris_backend=swieph", "ephemeris_backend=moseph"))]), "backend-not-allowed"),
    (dict(attempts=[attempt(notes=RECORD.replace("matched=1205", "matched=1000"))]), "record-inconsistent"),
])
def test_no_detector_names_its_cause(kw, cause):
    m = measure(**kw)
    assert m["v"] == NO_DET and m["d3"]["cause"] == cause, m["measured"]


OLD = "bbbbbbbb-1111-4111-8111-111111111111"
LATER = "cccccccc-1111-4111-8111-111111111111"


def test_a_receipt_of_an_older_attempt_is_not_of_this_build():
    """Review MED: the receipt names an OLDER attempt's run id (a build before the one that wrote the rows): NO_DETECTOR, never PASS."""
    m = measure([attempt(), attempt(run=OLD)], receipts=[receipt(build_id=OLD)])
    assert m["v"] == NO_DET and m["d3"]["cause"] == "receipt-not-from-this-build"


@pytest.mark.parametrize("later", [
    dict(disposition=""),                                   # a probe-green style completion (complete, no disposition)
    dict(disposition="probe_green"),
    dict(disposition="blocked_dependency"),
    dict(disposition="skip_no_delta", state="error"),       # the skip disposition without a completed state
    dict(disposition="skip_no_delta", state="aborted"),
])
def test_a_later_attempt_that_is_not_a_completed_delta_skip_cannot_excuse_the_receipt(later):
    """The `later_skips` rule: only a LATER attempt that is `complete` AND `skip_no_delta` may stand for the build the receipt was re-stamped by. Any other later attempt, with
    the receipt naming it, leaves the receipt not of this build (mutations: accept any later attempt; drop the disposition requirement; drop the state requirement)."""
    m = measure([attempt(run=LATER, **later), attempt()], receipts=[receipt(build_id=LATER)])
    assert m["v"] == NO_DET and m["d3"]["cause"] == "receipt-not-from-this-build", m["measured"]


def test_a_later_completed_build_is_the_build_read_and_the_earlier_rows_are_not_its():
    rows = _rows()                                          # still the rows of the earlier build RUN
    m = measure([attempt(run=LATER), attempt()], rows, receipts=[receipt(build_id=LATER)])
    assert m["v"] == FAIL and m["d3"]["cause"] == "rows-not-from-verified-build" and m["d3"]["attempt"]["run_id"] == LATER
    m = measure([attempt(run=LATER), attempt()], rows, receipts=[receipt(build_id=RUN)])        # and a receipt of the EARLIER build is not the later build's
    assert m["v"] == NO_DET and m["d3"]["cause"] == "receipt-not-from-this-build"


def test_a_completed_delta_skip_after_the_build_is_the_only_excuse():
    m = measure([attempt(run=LATER, disposition="skip_no_delta"), attempt()], receipts=[receipt(build_id=LATER)])
    assert m["v"] == PASS
    m = measure([attempt(run=LATER, disposition="skip_no_delta"), attempt(run=OLD, disposition="skip_no_delta"), attempt()], receipts=[receipt(build_id=OLD)])
    assert m["v"] == PASS                                   # a delta-skip between the build and the latest skip: still after the build
    m = measure([attempt(), attempt(run=LATER, disposition="skip_no_delta")], rows=[dict(r, build_id=LATER) for r in _rows()], receipts=[receipt(build_id=LATER)])
    assert m["v"] == NO_DET                                 # a skip BEFORE the build (older) cannot excuse a receipt either: the build is the later attempt and the receipt is not its


def test_a_receipt_of_the_probe_or_of_other_code_is_never_the_writers():
    """A probe-green receipt carries the probe digest; an older writer's receipt carries its digest: neither equals the expected writer digest."""
    for other in ("00" * 32, "ff" * 32):
        m = measure([attempt()], receipts=[receipt(code_digest=other)])
        assert m["v"] == NO_DET and m["d3"]["cause"] == "receipt-code-digest-not-current"


def test_unreadable_rows_are_no_detector():
    m = d3.d3_recorded_measure(_spec(), [attempt()], None, "chart_facts", asset_rows=1205, receipts=[receipt()], expected_digest=EXPECTED)
    assert m["v"] == NO_DET and m["d3"]["cause"] == "rows-unreadable"


# ───────────────────────── MED-1: the rows are bound to the build ─────────────────────────

def test_rows_rewritten_after_the_build_with_equal_counts_are_not_the_verified_rows():
    rows = _rows()
    rows[5] = dict(rows[5], build_id="eeeeeeee-1111-4111-8111-111111111111", fact_value_num=999.0)          # one row replaced by a later write: counts unchanged
    m = measure([attempt()], rows)
    assert len(rows) == 1205 and m["v"] == FAIL and m["d3"]["cause"] == "rows-not-from-verified-build" and "1 of the table's 1205" in m["measured"]


def test_every_row_must_carry_the_build_id_not_just_most():
    rows = [dict(r, build_id=None) if i == 1204 else r for i, r in enumerate(_rows())]
    assert measure([attempt()], rows)["v"] == FAIL
    rows = [dict(r, build_id="eeeeeeee-1111-4111-8111-111111111111") for r in _rows()]            # all rows from some other build
    m = measure([attempt()], rows)
    assert m["v"] == FAIL and "1205 of the table's 1205" in m["measured"]


def test_rows_without_a_build_id_column_do_not_pass():
    rows = [{k: v for k, v in r.items() if k != "build_id"} for r in _rows()]
    assert measure([attempt()], rows)["v"] == FAIL


# ───────────────────────── FAIL ─────────────────────────

REFUSAL = ("PositionsSecondCalcMismatch: positions second calculation: matched=1195 not_matched=10 not_derived=0 first mismatches: lahiri_chitrapaksha:(RAH_MEAN, retrograde_flag, "
           "writer='direct', verifier='retrograde')")
REFUSAL_UNDERIVABLE = "PositionsSecondCalcMismatch: positions second calculation: matched=1205 not_matched=0 not_derived=241 first mismatches: some_future_ayanamsha:(SUN, longitude_sidereal, writer=1.0, verifier='not_derived')"


def test_the_latest_attempt_refused_by_the_second_calculation_is_a_fail():
    m = measure([attempt(state="error", disposition="", error=REFUSAL), attempt()])
    assert m["v"] == FAIL and m["d3"]["cause"] == "recorded-mismatch"
    assert m["d3"]["recorded"]["not_matched"] == 10 and "REFUSED" in m["measured"]


def test_a_refusal_for_an_underivable_row_is_a_fail_too():
    m = measure([attempt(state="error", disposition="", error=REFUSAL_UNDERIVABLE), attempt()])
    assert m["v"] == FAIL and m["d3"]["recorded"]["not_derived"] == 241


def test_an_unrelated_error_on_the_latest_attempt_is_not_a_mismatch():
    m = measure([attempt(state="error", disposition="", error="OperationalError: connection lost"), attempt()])
    assert m["v"] == PASS


def test_a_supplied_note_naming_a_mismatch_or_another_build_is_a_fail():
    m = measure([attempt(notes=RECORD.replace("matched=1205 not_matched=0", "matched=1204 not_matched=1"))])
    assert m["v"] == FAIL and m["d3"]["cause"] == "recorded-mismatch"
    m = measure([attempt(notes=RECORD.replace(RUN, "dddddddd-1111-4111-8111-111111111111"))])
    assert m["v"] == FAIL and m["d3"]["cause"] == "recorded-mismatch" and "another build" in m["measured"]


def test_a_supplied_note_whose_counts_disagree_with_the_rows_is_a_fail():
    rows = _rows()
    moved = next(i for i, r in enumerate(rows) if r["ayanamsha_id"] == AYS[0])
    rows[moved] = dict(rows[moved], ayanamsha_id=AYS[1])
    m = measure([attempt(notes=RECORD)], rows)
    assert len(rows) == 1205 and m["v"] == FAIL and m["d3"]["cause"] == "counts-disagree"
    rows = _rows()
    del rows[17]
    assert measure([attempt(notes=RECORD)], rows)["v"] == FAIL


# ───────────────────────── PARTIAL ─────────────────────────

def test_a_supplied_note_with_not_derived_above_the_allowance_is_partial_not_pass():
    rec = RECORD.replace("matched=1205 not_matched=0 not_derived=0", "matched=1204 not_matched=0 not_derived=1")
    m = measure([attempt(notes=rec)])
    assert m["v"] == PARTIAL and m["d3"]["cause"] == "not-derived-above-allowance" and "unchecked claims" in m["measured"]
    s = _spec()
    s["recorded"]["not_derived_allowance"] = 1
    m = measure([attempt(notes=rec)], spec=s)
    assert m["v"] == PASS and m["d3"]["rows_total"] == 1204 and d3.d3_evidence_problem(m) == ""


def test_a_logical_row_count_that_differs_from_the_declaration_is_partial():
    s = _spec()
    s["expected_rows"] = 111
    m = measure([attempt()], spec=s)
    assert m["v"] == PARTIAL and m["d3"]["cause"] == "logical-count"


def test_an_asset_that_holds_more_rows_than_the_read_covers_is_partial():
    m = measure([attempt()], asset_rows=1300)
    assert m["v"] == PARTIAL and m["d3"]["cause"] == "coverage"


# ───────────────────────── mutations: every one leaves PASS ─────────────────────────

def _mutations():
    rows = _rows()
    rows[3] = dict(rows[3], build_id="eeeeeeee-1111-4111-8111-111111111111")
    yield "one-row-other-build", measure([attempt()], rows)
    yield "state-error", measure([attempt(state="error")])
    yield "disposition-skip", measure([attempt(disposition="skip_no_delta")])
    yield "receipt-unknown", measure([attempt()], receipts=[receipt(receipt_state="unknown")])
    yield "receipt-missing", measure([attempt()], receipts=[])
    yield "receipt-stale-digest", measure([attempt()], receipts=[receipt(code_digest="cd" * 32)])
    yield "expected-digest-moved", measure([attempt()], expected=dict(EXPECTED, value="cd" * 32))
    yield "receipt-other-build", measure([attempt()], receipts=[receipt(build_id="dddddddd-1111-4111-8111-111111111111")])
    yield "refused", measure([attempt(state="error", disposition="", error=REFUSAL)])
    yield "no-attempt", measure([])
    yield "note-mismatch", measure([attempt(notes=RECORD.replace("matched=1205 not_matched=0", "matched=1204 not_matched=1"))])
    yield "note-other-build", measure([attempt(notes=RECORD.replace(RUN, "dddddddd-1111-4111-8111-111111111111"))])
    yield "note-backend", measure([attempt(notes=RECORD.replace("swieph", "moseph"))])
    rows = _rows()
    rows.pop()
    yield "row-dropped-note", measure([attempt(notes=RECORD)], rows)
    yield "logical-count", measure([attempt()], spec=dict(_spec(), expected_rows=109))


def test_every_mutation_of_a_passing_record_leaves_pass():
    assert measure([attempt()])["v"] == PASS
    for name, m in _mutations():
        assert m["v"] != PASS, (name, m["measured"])


def test_a_forged_recorded_pass_without_its_evidence_is_not_honoured():
    m = {"Carr.D3": dict(v=PASS, measured="hypothetical PASS (proof only)", d3=dict(form=d3.FORM_BUILD_RECORDED)),
         "Carr.D1": dict(v=NA, cause="not-the-declared-carriage", measured="n/a"), "Carr.D2": dict(v=NA, cause="not-the-declared-carriage", measured="n/a")}
    cell = ac.rollup_asset("L1", m)["Carr"]
    assert next(c for c in cell["checks"] if c["criterion"] == "Carr.D3")["v"] == NO_DET


# ───────────────────────── parsing, the three reads, the expected digest ─────────────────────────

def test_parse_second_calc_line_reads_the_fixed_format_and_nothing_else():
    rec = d3.parse_second_calc_line(RECORD, "positions_second_calc")
    assert rec == dict(matched=1205, not_matched=0, not_derived=0, boundary_tolerated=0, rows=1205, build_id=RUN, ayanamshas={a: 241 for a in AYS}, backend="swieph")
    assert d3.parse_second_calc_line("positions_second_calc matched=1", "positions_second_calc") is None
    assert d3.parse_second_calc_line(RECORD.replace(f"build_id={RUN} ", ""), "positions_second_calc") is None          # the old shape (no build_id) is not read
    assert d3.parse_second_calc_line(None, "positions_second_calc") is None
    assert d3.parse_second_calc_line(RECORD, "") is None
    assert d3.parse_second_calc_mismatch(REFUSAL) == dict(matched=1195, not_matched=10, not_derived=0)
    assert d3.parse_second_calc_mismatch(REFUSAL_UNDERIVABLE) == dict(matched=1205, not_matched=0, not_derived=241)
    assert d3.parse_second_calc_mismatch("RuntimeError: other") is None


def test_the_attempt_read_is_one_stated_select_and_notes_are_not_available(monkeypatch):
    sqls = []
    monkeypatch.setattr(ac, "psql", lambda sql, **k: sqls.append(sql) or [["r1", "complete", "build", "2026-10-07", ""], ["r0", "error", "", "2026-10-06", "X: y"]])
    got = ac.d3_recorded_attempts(AID, ac.CHART_ID)
    assert [a["run_id"] for a in got] == ["r1", "r0"] and all(a["notes"] is None for a in got) and got[1]["error"] == "X: y"
    assert len(sqls) == 1 and sqls[0].startswith("SELECT") and "ORDER BY r.created_at DESC, a.run_id DESC" in sqls[0] and f"r.chart_id::text = '{ac.CHART_ID}'" in sqls[0]
    assert not re.search(r"\bcharts\b", sqls[0])
    for bad in (("ga_positions; drop", ac.CHART_ID), (AID, "not-a-uuid")):
        with pytest.raises(ac.Unknown):
            ac.d3_recorded_attempts(*bad)
    monkeypatch.setattr(ac, "psql", lambda sql, **k: [["only", "three", "fields"]])
    with pytest.raises(ac.Unknown, match="5 selected fields"):
        ac.d3_recorded_attempts(AID, ac.CHART_ID)


def test_the_receipt_read_is_one_stated_select_for_the_measured_chart(monkeypatch):
    sqls = []
    monkeypatch.setattr(ac, "psql", lambda sql, **k: sqls.append(sql) or [["proven", DIGEST, RUN, "whole_asset", "2026-10-07 01:00:00+00"], ["unknown", "", "", "p2", ""]])
    got = ac.d3_recorded_receipts(AID, ac.CHART_ID)
    assert got[0] == receipt() and got[1]["code_digest"] is None and got[1]["build_id"] is None
    assert len(sqls) == 1 and "FROM asset_provenance_receipts p" in sqls[0] and f"p.chart_id::text = '{ac.CHART_ID}'" in sqls[0] and f"p.asset_id = '{AID}'" in sqls[0]
    assert not re.search(r"\bcharts\b", sqls[0])
    for bad in (("ga_positions; drop", ac.CHART_ID), (AID, "not-a-uuid")):
        with pytest.raises(ac.Unknown):
            ac.d3_recorded_receipts(*bad)
    monkeypatch.setattr(ac, "psql", lambda sql, **k: [["x"]])
    with pytest.raises(ac.Unknown, match="5 selected fields"):
        ac.d3_recorded_receipts(AID, ac.CHART_ID)


def test_the_expected_digest_is_read_from_the_generated_inventory_of_this_tree():
    real = json.loads((ac.ROOT / "platform/src/generated/nirmana-writer-digests.json").read_text())["writers"][AID]
    got = ac.d3_expected_writer_digest(AID, "platform/src/generated/nirmana-writer-digests.json")
    assert got["value"] == real and re.fullmatch(r"[0-9a-f]{64}", real) and got["why"] == ""
    assert ac.d3_expected_writer_digest("ga_no_such_asset", "platform/src/generated/nirmana-writer-digests.json")["value"] is None
    assert ac.d3_expected_writer_digest(AID, "platform/src/generated/no_such_file.json")["value"] is None


def test_a_failed_attempt_or_receipt_read_degrades_to_no_detector_not_errored(monkeypatch):
    monkeypatch.setattr(ac, "d3_fetch_rows", lambda table, read, chart_id=None: _rows())
    monkeypatch.setattr(ac, "d3_expected_writer_digest", lambda aid, rel: EXPECTED)

    def boom(*a, **k):
        raise ac.Unknown("connection refused")
    monkeypatch.setattr(ac, "d3_recorded_attempts", boom)
    monkeypatch.setattr(ac, "d3_recorded_receipts", lambda aid, chart_id: [receipt()])
    got = ac.carriage_declared_checks(AID, _car(), "chart_facts", True, asset_rows=1205, **KW)
    assert got["Carr.D3"]["v"] == NO_DET and got["Carr.D3"]["d3"]["cause"] == "attempt-read-failed"
    monkeypatch.setattr(ac, "d3_recorded_attempts", lambda aid, chart_id, limit=25: [attempt()])
    monkeypatch.setattr(ac, "d3_recorded_receipts", boom)
    got = ac.carriage_declared_checks(AID, _car(), "chart_facts", True, asset_rows=1205, **KW)
    assert got["Carr.D3"]["v"] == NO_DET and got["Carr.D3"]["d3"]["cause"] == "receipt-read-failed"


def test_a_failed_row_read_is_errored_for_this_check_only(monkeypatch):
    def boom(*a, **k):
        raise ac.Unknown("connection refused")
    monkeypatch.setattr(ac, "d3_fetch_rows", boom)
    got = ac.carriage_declared_checks(AID, _car(), "chart_facts", True, **KW)
    assert got["Carr.D3"]["v"] == ac.ERRORED and got["Carr.D1"]["v"] == NA


def test_a_spec_without_the_form_is_still_the_reference_route_and_reads_no_detector_under_the_census_role(monkeypatch):
    c = _car()
    for k in ("form", "recorded"):
        c["spec"].pop(k)
    monkeypatch.setattr(ac, "d3_fetch_rows", lambda *a, **k: pytest.fail("the unreadable inputs table is decided before any read"))
    got = ac.carriage_declared_checks(AID, c, "chart_facts", True, **KW)
    assert got["Carr.D3"]["v"] == NO_DET and got["Carr.D3"]["d3"]["cause"] == ac.D3_NEEDS_READABLE_CAUSE
