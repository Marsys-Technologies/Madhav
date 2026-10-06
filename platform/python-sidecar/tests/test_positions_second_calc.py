"""N-169: the independent second calculation of the natal positions INSIDE the ga_positions build.

What this pins (CLAUDE.md N.8: a check is real only if a mutation turns it red):

  A. PARITY       the sidecar verifier (`ga_writers/_positions_independent_verifier.py`) and the reviewed governance method it ports
                  (`platform/scripts/governance/carriage_d3_methods.py`, `swisseph_sidereal_positions_v1`) give IDENTICAL values on public
                  fixtures and on the native chart's birth inputs, for every subject, key and ayanamsha.
  B. REAL ROWS    the real writer's own rows (pyjhora_adapter route) agree with the verifier on every row but the one the engine already
                  names as a finding: Rahu/Ketu `retrograde_flag` stored `direct` while the mean-node longitude moves backward (10 rows).
                  That pin flips when the node convention is ruled.
  C. MUTATION     perturb ONE longitude in the writer's computed rows and the write is REFUSED: it raises, nothing is inserted or deleted, and
                  the message carries matched / not_matched and the (subject, key, writer value, verifier value) pair.
  D. SUCCESS      with the node convention ruled, the build proceeds and records the fixed `positions_second_calc` line.
  E. PRIVACY      neither the recorded line nor any error text carries a birth parameter.
No birth data is hard-coded beyond what the repository's other writer tests already carry (the native's anchors) and synthetic public fixtures.
"""
from __future__ import annotations

import copy
import importlib.util
import pathlib
import re
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers import _positions_independent_verifier as V  # noqa: E402
from ga_writers import ga_positions_writer as W  # noqa: E402

GOV_METHODS = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "governance" / "carriage_d3_methods.py"

NATIVE = {"datetime_iso": "1984-02-05T10:43:00", "latitude_deg": 20.27, "longitude_deg": 85.84, "tz_offset_hours": 5.5,
          "place_name": "Bhubaneswar", "subject_label": "Abhisek"}
NATIVE_ROW = {"birth_date": "1984-02-05", "birth_time": "10:43:00", "birth_lat": 20.27, "birth_lng": 85.84, "timezone_id": "Asia/Kolkata"}
SYNTH = {"datetime_iso": "1990-06-15T14:30:00", "latitude_deg": 40.71, "longitude_deg": -74.0, "tz_offset_hours": -4.0,
         "place_name": "Synthetic City", "subject_label": "Synthetic"}
SYNTH_ROW = {"birth_date": "1990-06-15", "birth_time": "14:30:00", "birth_lat": 40.71, "birth_lng": -74.0, "timezone_id": "America/New_York"}
FIXTURES = [("native", NATIVE, NATIVE_ROW), ("synthetic-new-york", SYNTH, SYNTH_ROW)]

_COLUMN_TO_KEY = {v: k for k, v in V._KEY_TO_COLUMN.items()}


def _gov():
    if not GOV_METHODS.exists():
        pytest.skip("governance tree not present (build image / sparse checkout): the parity test needs carriage_d3_methods.py")
    spec = importlib.util.spec_from_file_location("carriage_d3_methods_for_parity", GOV_METHODS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FakeConn:
    """The recording fake connection the repo's writer tests use: every statement is kept; nothing is committed."""

    def __init__(self) -> None:
        self.statements: list[tuple[str, object]] = []

    def execute(self, sql, params=None):
        self.statements.append((" ".join(str(sql).split()), params))
        return self

    rowcount = 0

    def cursor(self, *a, **k):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def inserts(self) -> int:
        return sum(1 for s, _ in self.statements if s.startswith("INSERT INTO chart_facts"))

    def deletes(self) -> int:
        return sum(1 for s, _ in self.statements if s.startswith("DELETE FROM chart_facts"))


# ───────────────────────────── A. parity ─────────────────────────────

@pytest.mark.parametrize("label,bp,row", FIXTURES, ids=[f[0] for f in FIXTURES])
def test_verifier_and_governance_method_give_identical_values(label, bp, row):
    gov = _gov()
    spec = {"conventions": {"position_model": {"value": "true_geometric"}}}
    ctx = gov.positions_context([], [row], spec)
    keys_seen = 0
    for ay in W.CANONICAL_AYANAMSHAS:
        mine = V.derive_reference(bp, ay)
        theirs: dict[tuple[str, str], object] = {}
        for subj in (*V._GRAHA_SUBJECTS, V.LAGNA_SUBJECT, *V._BHAVA_SUBJECTS):
            ref = gov.positions_ref({"ayanamsha": ay, "subject": subj, "unknown_keys": []}, ctx)
            for col, val in ref.items():
                if val is not None:
                    theirs[(subj, _COLUMN_TO_KEY.get(col, col))] = val
        assert set(mine) == set(theirs), (label, ay, sorted(set(mine) ^ set(theirs))[:5])
        for k, d in mine.items():
            t = theirs[k]
            if isinstance(t, float):
                assert d.value == pytest.approx(t, abs=1e-9), (label, ay, k)
            else:
                assert d.value == t, (label, ay, k, d.value, t)
        keys_seen += len(mine)
    assert keys_seen == 5 * 241


def test_the_tolerances_and_boundary_rule_are_the_declared_ones():
    import json
    decl = GOV_METHODS.parent / "asset_declarations.json"
    if not decl.exists():
        pytest.skip("governance tree not present")
    spec = json.loads(decl.read_text())["assets"]["ga_positions"]["carriage"]["spec"]
    for col, d in spec["columns"].items():
        if d["kind"] in ("circular_deg", "circular_30", "linear"):
            assert d["tol"] == V.TOL_DEG, col
        assert V._kind(col) == d["kind"], col
    assert {c: (b["width"], b["cells"]) for c, b in spec["boundary"].items()} == pytest.approx(V._BOUNDARY)
    assert spec["conventions"]["position_model"]["value"] == "true_geometric"
    assert spec["conventions"]["node_model"]["value"] == "mean_node"


# ───────────────────────────── B. real writer rows ─────────────────────────────

_ROWS_CACHE: dict[str, list[dict]] = {}


def _real_rows(ay: str, bp=NATIVE) -> list[dict]:
    key = f"{ay}|{bp['datetime_iso']}"
    if key not in _ROWS_CACHE:
        from pyjhora_adapter.compute import compute_chart
        co = compute_chart(inputs=bp, ayanamsha_id=W.CANONICAL_AYANAMSHAS[ay])
        rows = W._build_position_rows(co, "chart-n169", "b", ay, W.CANONICAL_AYANAMSHAS[ay], "2026-01-01T00:00:00+00:00")
        rows += W._build_chalit_rows(co, "chart-n169", "b", ay, "2026-01-01T00:00:00+00:00")
        _ROWS_CACHE[key] = rows
    return copy.deepcopy(_ROWS_CACHE[key])


def _rule_nodes(rows: list[dict]) -> list[dict]:
    """The nodes' retrograde flag set to the sign of the mean-node motion: the variant in which the open convention question is ruled (as the
    governance test's `fix_nodes`)."""
    for r in rows:
        if r["fact_key"] == "retrograde_flag" and r["fact_subject"] in ("RAH_MEAN", "KET_MEAN"):
            r["fact_value_text"] = "retrograde"
    return rows


@pytest.mark.parametrize("ay", list(W.CANONICAL_AYANAMSHAS))
def test_real_writer_rows_agree_except_the_open_node_retrograde_finding(ay):
    cmp_ = V.compare_rows(_real_rows(ay), V.derive_reference(NATIVE, ay))
    assert cmp_.rows == 241 and cmp_.derivable == 241 and cmp_.not_derived == 0
    assert cmp_.matched == 239 and cmp_.not_matched == 2, cmp_.mismatches
    assert {(s, k) for s, k, _w, _v in cmp_.mismatches} == {("RAH_MEAN", "retrograde_flag"), ("KET_MEAN", "retrograde_flag")}
    assert {(w, v) for _s, _k, w, v in cmp_.mismatches} == {("direct", "retrograde")}


@pytest.mark.parametrize("ay", list(W.CANONICAL_AYANAMSHAS))
def test_real_writer_rows_with_the_node_convention_ruled_match_in_full(ay):
    cmp_ = V.compare_rows(_rule_nodes(_real_rows(ay)), V.derive_reference(NATIVE, ay))
    assert (cmp_.matched, cmp_.not_matched, cmp_.not_derived, cmp_.rows) == (241, 0, 0, 241), cmp_.mismatches


# ───────────────────────────── helpers for the build-level tests ─────────────────────────────

def _drive(monkeypatch, *, rule_nodes: bool, mutate=None, birth=NATIVE):
    """Run the REAL build_ga_positions (real compute_chart, real verifier) on a fake connection; `rule_nodes` and `mutate` act on the rows the
    writer is about to insert (the writer's computed output)."""
    real = W._build_position_rows

    def wrapped(co, chart_id, build_id, canon, adapter, computed_at):
        rows = real(co, chart_id, build_id, canon, adapter, computed_at)
        if rule_nodes:
            _rule_nodes(rows)
        if mutate:
            mutate(canon, rows)
        return rows

    real_chalit = W._build_chalit_rows

    def wrapped_chalit(co, chart_id, build_id, canon, computed_at):
        rows = real_chalit(co, chart_id, build_id, canon, computed_at)
        if mutate:
            mutate(canon, rows)
        return rows

    monkeypatch.setattr(W, "_build_position_rows", wrapped)
    monkeypatch.setattr(W, "_build_chalit_rows", wrapped_chalit)
    conn = FakeConn()
    try:
        s = W.build_ga_positions("chart-n169", "build-n169", conn=conn, birth_params=dict(birth))
        return conn, s, None
    except Exception as exc:  # noqa: BLE001
        return conn, None, exc


def _bump_longitude(canon, rows):
    if canon != "lahiri_chitrapaksha":
        return
    if not any(r["fact_key"] == "longitude_sidereal" for r in rows):          # the chalit builder's rows carry no longitude: this mutation is the position builder's
        return
    for r in rows:
        if r["fact_subject"] == "SUN" and r["fact_key"] == "longitude_sidereal":
            r["fact_value_num"] = r["fact_value_num"] + 0.01          # 36 arcsec: 10x the declared tolerance
            return
    raise AssertionError("no SUN longitude row")


# ───────────────────────────── C. mutation: the write is refused ─────────────────────────────

def test_one_perturbed_longitude_refuses_the_write_and_names_the_pair(monkeypatch):
    conn, summary, exc = _drive(monkeypatch, rule_nodes=True, mutate=_bump_longitude)
    assert isinstance(exc, W.PositionsSecondCalcMismatch) and summary is None
    assert conn.inserts() == 0 and conn.deletes() == 0 and conn.statements == [], "nothing may be written or deleted"
    msg = str(exc)
    assert msg.startswith("positions second calculation: matched=1204 not_matched=1 not_derived=0 first mismatches: ")
    assert "lahiri_chitrapaksha:(SUN, longitude_sidereal, writer=" in msg and "verifier=" in msg
    m = re.search(r"writer=([\d.]+), verifier=([\d.]+)\)", msg)
    assert abs(float(m.group(1)) - float(m.group(2)) - 0.01) < 1e-5


def test_a_discrete_value_flipped_is_refused(monkeypatch):
    def flip(canon, rows):
        for r in rows:
            if canon == "raman" and r["fact_subject"] == "MOON" and r["fact_key"] == "nakshatra":
                r["fact_value_text"] = "Ashwini"
                return

    conn, _s, exc = _drive(monkeypatch, rule_nodes=True, mutate=flip)
    assert isinstance(exc, W.PositionsSecondCalcMismatch) and conn.statements == []
    assert "raman:(MOON, nakshatra, writer='Ashwini', verifier='nakshatra_num=25')" in str(exc)


def test_a_dropped_row_is_refused_as_not_matched(monkeypatch):
    def drop(canon, rows):
        if canon == "krishnamurti":
            rows[:] = [r for r in rows if not (r["fact_subject"] == "BHAVA_07" and r["fact_key"] == "placidus_start")]

    conn, _s, exc = _drive(monkeypatch, rule_nodes=True, mutate=drop)
    assert isinstance(exc, W.PositionsSecondCalcMismatch) and conn.statements == []
    assert "matched=1204 not_matched=1" in str(exc) and "krishnamurti:(BHAVA_07, placidus_start, writer=None, verifier=" in str(exc)


def test_the_unruled_node_flag_refuses_the_real_build_naming_ten_rows(monkeypatch):
    """The writer as it stands: Rahu/Ketu `retrograde_flag` `direct` against the mean-node motion. The build refuses until SS rules the convention."""
    conn, _s, exc = _drive(monkeypatch, rule_nodes=False)
    assert isinstance(exc, W.PositionsSecondCalcMismatch) and conn.statements == []
    assert str(exc).startswith("positions second calculation: matched=1195 not_matched=10 not_derived=0 first mismatches: ")
    assert str(exc).count("retrograde_flag") == 10          # the cap is 10 named pairs: all ten are the node rows


def test_at_most_ten_pairs_are_named(monkeypatch):
    def many(canon, rows):
        for r in rows:
            if r["fact_key"] == "degree_in_sign":
                r["fact_value_num"] = (r["fact_value_num"] + 1.0) % 30.0

    _c, _s, exc = _drive(monkeypatch, rule_nodes=True, mutate=many)
    assert isinstance(exc, W.PositionsSecondCalcMismatch)
    assert str(exc).count("writer=") == 10 and "not_matched=50" in str(exc)


# ───────────────────────────── D. success path ─────────────────────────────

NOTES_RE = re.compile(r"positions_second_calc matched=(\d+) not_matched=(\d+) not_derived=(\d+) boundary_tolerated=(\d+) rows=(\d+) ayanamshas=(\S+)")


def test_success_records_the_fixed_line_and_leaves_the_tier_alone(monkeypatch):
    conn, s, exc = _drive(monkeypatch, rule_nodes=True)
    assert exc is None
    assert s["total_chart_facts_rows"] == 1205 and conn.inserts() == 1205
    line = s["positions_second_calc"]
    m = NOTES_RE.fullmatch(line)
    assert m, line
    assert m.groups()[:5] == ("1205", "0", "0", "0", "1205")
    assert m.group(6) == ",".join(f"{a}:241" for a in W.CANONICAL_AYANAMSHAS)
    # the check changes no stored tier: Pravaha pins `verification_pass_status`
    tiers = {p["verification_pass_status"] for sql, p in conn.statements if sql.startswith("INSERT INTO chart_facts")}
    assert tiers == {"single"}


def test_the_writer_follows_a_reduction_of_the_ayanamsha_set(monkeypatch):
    monkeypatch.setattr(W, "CANONICAL_AYANAMSHAS", {"lahiri_chitrapaksha": "lahiri"})
    conn, s, exc = _drive(monkeypatch, rule_nodes=True)
    assert exc is None and conn.inserts() == 241
    assert s["positions_second_calc"] == ("positions_second_calc matched=241 not_matched=0 not_derived=0 boundary_tolerated=0 rows=241 "
                                          "ayanamshas=lahiri_chitrapaksha:241")


def test_the_adapter_carries_the_line_in_notes(monkeypatch):
    from pipeline.orchestrator.writers import ContextSpec, discover_all, get_writer
    discover_all()
    line = W._second_calc_line(1205, 0, 0, 0, {a: 241 for a in W.CANONICAL_AYANAMSHAS})
    monkeypatch.setattr(W, "build_ga_positions", lambda **kw: {"total_chart_facts_rows": 1205, "positions_second_calc": line})
    ctx = ContextSpec(asset_id="ga_positions", build_id="b", db_conn=FakeConn(), config={"chart_id": "chart-n169", "birth_params": dict(NATIVE)})
    res = get_writer("ga_positions")().run(ctx)
    assert res.notes.startswith("chart_facts=1205; positions_second_calc matched=1205 not_matched=0 ")
    assert NOTES_RE.search(res.notes)


# ───────────────────────────── the verifier's own edges ─────────────────────────────

def test_an_unknown_ayanamsha_is_not_derived_never_matched():
    rows = [r for r in _real_rows("lahiri_chitrapaksha") if r["fact_subject"] == "SUN"]
    cmp_ = V.compare_rows(rows, V.derive_reference(NATIVE, "some_future_ayanamsha"))
    assert (cmp_.matched, cmp_.not_matched, cmp_.not_derived, cmp_.rows, cmp_.derivable) == (0, 0, len(rows), len(rows), 0)


def test_a_row_the_verifier_has_no_derivation_for_is_not_derived():
    rows = _rule_nodes(_real_rows("lahiri_chitrapaksha"))
    rows.append(dict(rows[0], fact_key="longitude_tropical", fact_category="graha_position"))
    cmp_ = V.compare_rows(rows, V.derive_reference(NATIVE, "lahiri_chitrapaksha"))
    assert (cmp_.matched, cmp_.not_matched, cmp_.not_derived, cmp_.rows) == (241, 0, 1, 242)


def test_a_discrete_cell_at_the_declared_edge_is_tolerated_and_counted():
    d = {("SUN", "sign_num"): V.Derived(V.KIND_EXACT, 10, 270.0004)}               # the reference longitude is 0.0004 degree past the Capricorn edge
    rows = [dict(fact_subject="SUN", fact_key="sign_num", fact_category="graha_sign_attributes", fact_value_num=9.0, fact_value_text=None)]
    cmp_ = V.compare_rows(rows, d)
    assert (cmp_.matched, cmp_.not_matched, cmp_.boundary_tolerated) == (1, 0, 1)
    rows[0]["fact_value_num"] = 8.0                                                   # two cells away: never tolerated
    assert V.compare_rows(rows, d).not_matched == 1
    far = {("SUN", "sign_num"): V.Derived(V.KIND_EXACT, 10, 275.0)}                  # next to the right value but nowhere near an edge
    rows[0]["fact_value_num"] = 9.0
    assert V.compare_rows(rows, far).not_matched == 1


def test_a_longitude_on_the_wrap_compares_circularly():
    d = {("SUN", "longitude_sidereal"): V.Derived(V.KIND_CIRCULAR_DEG, 359.9995)}
    row = dict(fact_subject="SUN", fact_key="longitude_sidereal", fact_category="graha_position", fact_value_num=0.0003, fact_value_text=None)
    assert V.compare_rows([row], d).matched == 1


# ───────────────────────────── E. privacy ─────────────────────────────

BIRTH_STRINGS = ("1984", "10:43", "20.27", "85.84", "Bhubaneswar", "Abhisek", "1990", "14:30", "40.71", "74.0", "Synthetic")


def _no_birth(text: str) -> None:
    for s in BIRTH_STRINGS:
        assert s not in text, f"birth parameter {s!r} leaked into {text[:200]!r}"


def test_no_birth_parameter_in_the_recorded_line_or_the_refusal_text(monkeypatch):
    _c, s, exc = _drive(monkeypatch, rule_nodes=True)
    _no_birth(s["positions_second_calc"])
    _c, _s, exc = _drive(monkeypatch, rule_nodes=True, mutate=_bump_longitude)
    _no_birth(str(exc))
    _c, _s, exc = _drive(monkeypatch, rule_nodes=False)
    _no_birth(str(exc))


def test_a_verifier_that_cannot_run_names_only_the_exception_type():
    bad = dict(NATIVE, datetime_iso="1984-13-45T25:61:00 Bhubaneswar")
    with pytest.raises(V.SecondCalcError) as ei:
        V.derive_reference(bad, "lahiri_chitrapaksha")
    assert str(ei.value) == "positions second calculation could not run (ValueError)"
    assert ei.value.__suppress_context__ and ei.value.__cause__ is None
    import traceback
    _no_birth("".join(traceback.format_exception(ei.value)))


# ───────────────────────── the record the engine reads ─────────────────────────

def test_the_engines_parser_reads_exactly_what_the_writer_records(monkeypatch):
    """The writer's line (and the decorator's backend fragment) parse with the engine's own parser: the two formats cannot drift apart."""
    d3_path = GOV_METHODS.parent / "carriage_d3.py"
    if not d3_path.exists():
        pytest.skip("governance tree not present (build image / sparse checkout)")
    spec = importlib.util.spec_from_file_location("carriage_d3_for_format_pin", d3_path)
    d3 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(d3)
    _c, s, exc = _drive(monkeypatch, rule_nodes=True)
    assert exc is None
    notes = f"chart_facts={s['total_chart_facts_rows']}; {s['positions_second_calc']}; ephemeris_backend=swieph"
    rec = d3.parse_second_calc_line(notes, W.SECOND_CALC_MARKER)
    assert rec == dict(matched=1205, not_matched=0, not_derived=0, boundary_tolerated=0, rows=1205, ayanamshas={a: 241 for a in W.CANONICAL_AYANAMSHAS}, backend="swieph")
    assert d3.parse_second_calc_mismatch(str(_drive(monkeypatch, rule_nodes=True, mutate=_bump_longitude)[2])) == dict(matched=1204, not_matched=1, not_derived=0)
    assert d3.RECORDED_FORMS[d3.FORM_BUILD_RECORDED]["swisseph_sidereal_positions_v1"] == W.SECOND_CALC_MARKER
