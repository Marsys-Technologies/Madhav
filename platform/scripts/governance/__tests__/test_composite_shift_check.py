"""Offline tests for evidence/composite_shift_check.py (the W7 hand-check for the composite label+number rows of the Moshier -> .se1 move).

flip_detector.py cannot separate a row's class label from its continuous number (it classes any row with a non-empty text as class_text), so
the label check and the per-row numeric bound live in this script. These tests pin that it PASSES the declared change and FAILS every
deviation (each CS check has tamper cases, and each numeric bound is tested one step inside and one step beyond), so it cannot be a vacuous green.
No database, no network: states are the in-memory snapshots of _composite_shift_fixture.py (synthetic values, rehearsal move pattern).
No PyJHora / swisseph / ga_writers import: the two pins that need them (the PyJHora longevity constants and the CS6 writer-boundary pins) live in
platform/python-sidecar/tests/test_composite_shift_check_pyjhora_pins.py, because the governance CI job has no PyJHora.
"""
from __future__ import annotations

import gzip
import importlib.util
import json
import pathlib

import pytest

import _composite_shift_fixture as F

REPO = pathlib.Path(__file__).resolve().parents[4]
SCRIPT = REPO / "00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks/evidence/composite_shift_check.py"
spec = importlib.util.spec_from_file_location("composite_shift_check", SCRIPT)
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


def _row(rows, **where):
    """The single row of `rows` matching every column index given as cN=value."""
    hits = [r for r in rows if all(r[int(k[1:])] == v for k, v in where.items())]
    assert len(hits) == 1, (where, len(hits))
    return hits[0]


def _bump(row, col, delta, nd):
    row[col] = format(round(float(row[col]) + delta, nd), f".{nd}f")


# ----------------------------------------------------------------------------------------------- pins
def test_the_script_table_and_the_fixture_table_are_the_same_transcription_of_the_analysis():
    for ay, vals in F.TABLE.items():
        mine = tuple(abs(x) for x in vals[:7]) + (abs(vals[7]), abs(vals[7]), abs(vals[8]))
        assert M.SHIFT_ARCSEC[ay] == mine, ay
    assert M.BODIES == tuple(F.GRAHAS) and set(M.SHIFT_ARCSEC) == set(F.AYS) and tuple(M.AYAS) == tuple(F.AYS)
    assert tuple(M.VARGAS) == tuple(F.VARGAS)


def test_the_rounding_steps_are_the_writers_own():
    root = REPO / "platform/python-sidecar/ga_writers"
    assert 'round(deg_in_sign, 6)' in (root / "ga_vargas_writer.py").read_text() and "deg_in_sign = d1_long % 30.0" in (root / "ga_vargas_writer.py").read_text()
    sdc = (root / "ga_sensitive_degree_writer.py").read_text()
    assert '"orb_deg": round(orb, 4)' in sdc and '"bhaga_orb_deg": round(bhaga_orb, 4)' in sdc
    ayu = (root / "ga_ayurdaya_writer.py").read_text()
    assert "round(float(v), 4)" in ayu and "round(total, 4)" in ayu  # (the 60/200 slope lives in PyJHora's _amsayu, method=2; the full-longevity tables are pinned in platform/python-sidecar/tests/test_composite_shift_check_pyjhora_pins.py, which needs PyJHora)
    assert M.VARGA_STEP_DEG == 1e-6 and M.SDC_STEP_DEG == 1e-4 and M.AYU_STEP_YEARS == 1e-4 and M.AMSAYU_SLOPE == pytest.approx(0.3)


def test_the_derived_count_bounds_are_the_ones_the_hook_carries():
    assert M.derive_count_bounds() == {"varga_position": (900, 1140), "sensitive_degree_check": (10, 74), "ayurdaya": (0, 120)}
    hook = json.loads((SCRIPT.parent.parent / "ephemeris_backend_shift.json").read_text())["may_change"]
    assert [hook[i]["expected_count"] for i in (27, 28, 29)] == [{"min": 900, "max": 1140}, {"min": 10, "max": 74}, {"min": 0, "max": 120}]


# ----------------------------------------------------------------------------------------------- pass
@pytest.mark.parametrize("kw,n", [({}, 900), ({"varga_sun_crosses": True}, 1050), ({"varga_all_possible": True}, 1140)])
def test_the_declared_change_passes(kw, n):
    bad, stats = M.check(*F.composite_pair(**kw))
    assert bad == [] and stats == {"varga_position": n, "sensitive_degree_check": 20, "ayurdaya": 12}


# ----------------------------------------------------------------------------------------------- CS2: a class (label) flip fails
def test_CS2_a_flip_of_the_label_fails_on_every_family():
    b, a = F.composite_pair()
    _row(a["divisionals"], c0="raman", c1="D60", c2="Sun", c4="degree_in_sign")[7] = "Taurus"           # the sign column is the divisionals label (a Sun row: unmoved, so only CS2 speaks)
    _row(a["chart_facts"], c0="lahiri_chitrapaksha", c2="SUN", c3="mrityu_bhaga")[4] = "fired"
    _row(a["chart_facts"], c0="true_chitra", c2="PINDAYU", c3="total_years")[4] = "alpayu"
    bad, _ = M.check(b, a)
    assert sorted(x.split(" ")[0] for x in bad) == ["CS2", "CS2", "CS2"], bad
    # a flip on a row whose number ALSO moved is a CS2 and that row no longer counts as a moved composite row (so CS5 may speak too)
    b, a = F.composite_pair()
    _row(a["chart_facts"], c0="lahiri_chitrapaksha", c2="MOON", c3="mrityu_bhaga")[4] = "fired"
    bad, _ = M.check(b, a)
    assert [x.split(" ")[0] for x in bad] == ["CS2"] and "'not_fired' -> 'fired'" in bad[0]


def test_CS2_a_flip_on_a_row_whose_number_did_not_move_also_fails():
    b, a = F.composite_pair()
    _row(a["chart_facts"], c0="raman", c2="VEN", c3="pushkara")[4] = "pushkara"       # Venus pushkara on Raman did not move numerically
    bad, _ = M.check(b, a)
    assert [x.split(" ")[0] for x in bad] == ["CS2"]


# ----------------------------------------------------------------------------------------------- CS3: the numeric bound, one inside / one beyond
def test_CS3_varga_position_bound_is_shift_plus_one_stored_step():
    # Moon on Lahiri: shift 0.6647" (+0.00005" table slack) = 1.8465e-4 deg, plus the 1e-6 step => 1.8565e-4
    def with_delta(delta):
        b, a = F.composite_pair()
        row = _row(a["divisionals"], c0="lahiri_chitrapaksha", c1="D9", c2="Moon", c4="degree_in_sign")
        base = float(_row(b["divisionals"], c0="lahiri_chitrapaksha", c1="D9", c2="Moon", c4="degree_in_sign")[6])
        row[6] = format(base + delta, ".6f")
        return M.check(b, a)[0]
    assert with_delta(1.85e-4) == []
    assert any(x.startswith("CS3") for x in with_delta(1.87e-4))
    assert any(x.startswith("CS3") for x in with_delta(-1.87e-4))


def test_CS3_a_body_with_no_input_shift_may_move_at_most_one_stored_step():
    b, a = F.composite_pair()
    row = _row(a["divisionals"], c0="lahiri_chitrapaksha", c1="D9", c2="Rahu", c4="degree_in_sign")      # mean node on Lahiri: shift exactly 0
    _bump(row, 6, 1e-6, 6)
    bad, _ = M.check(b, a)
    assert bad == []                                                                                        # one step (ulp noise at a rounding boundary) is tolerated...
    _bump(row, 6, 1e-6, 6)
    bad, _ = M.check(b, a)
    assert any(x.startswith("CS3") for x in bad)                                                            # ...two steps are not


def test_CS3_sensitive_degree_check_bound_is_shift_plus_one_stored_step():
    # Jupiter on Raman moved +0.0001 (inside: shift 5.6e-5 deg + 1e-4 step = 1.56e-4); +0.0002 is beyond
    def with_row(delta):
        b, a = F.composite_pair()
        row = _row(a["chart_facts"], c0="raman", c2="JUP", c3="mrityu_bhaga")
        row[5] = format(round(float(_row(b["chart_facts"], c0="raman", c2="JUP", c3="mrityu_bhaga")[5]) + delta, 4), ".4f")
        return M.check(b, a)[0]
    assert with_row(0.0001) == []
    assert any(x.startswith("CS3") for x in with_row(0.0002))
    # Mars (0.118" = 3.3e-5 deg, below the step) may cross one rounding boundary (+0.0001), never two
    b, a = F.composite_pair()
    row = _row(a["chart_facts"], c0="raman", c2="MAR", c3="pushkara")
    _bump(row, 5, 0.0001, 4)
    assert M.check(b, a)[0] == []
    _bump(row, 5, 0.0001, 4)
    assert any(x.startswith("CS3") for x in M.check(b, a)[0])


def test_CS3_ayurdaya_contribution_and_total_bounds():
    # amsayu contribution of the Moon on Lahiri: slope 0.3 y/deg x 1.8465e-4 deg = 5.5e-5 y, plus the 1e-4 step => 1.55e-4 y
    def with_moon(delta):
        b, a = F.composite_pair()
        row = _row(a["chart_facts"], c0="surya_siddhanta_classical", c2="MOON", c3="amsayu_contribution_years")
        base = float(_row(b["chart_facts"], c0="surya_siddhanta_classical", c2="MOON", c3="amsayu_contribution_years")[5])
        row[5] = format(round(base + delta, 4), ".4f")
        return M.check(b, a)[0]
    assert with_moon(-0.0001) == []
    assert any(x.startswith("CS3") for x in with_moon(-0.0002))
    # a total: sum of the 7 slopes x shifts + lagna/30 + one step. Lahiri AMSAYU: 0.3 x (sum of the seven shifts, about 1.18 arcsec = 3.3e-4 deg) = 9.8e-5 y, plus 1e-4 => about 2e-4 y
    assert 0.3 * sum(abs(x) for x in F.TABLE["lahiri_chitrapaksha"][:7]) / 3600.0 < 1e-4
    def with_total(delta):
        b, a = F.composite_pair()
        row = _row(a["chart_facts"], c0="lahiri_chitrapaksha", c2="AMSAYU", c3="total_years")
        row[5] = format(round(float(_row(b["chart_facts"], c0="lahiri_chitrapaksha", c2="AMSAYU", c3="total_years")[5]) + delta, 4), ".4f")
        return M.check(b, a)[0]
    assert with_total(-0.0001) == [] and with_total(0.0001) == []
    assert any(x.startswith("CS3") for x in with_total(-0.0003))


def test_CS3_a_mod_12_wrap_of_amsayu_is_a_violation_for_a_human_not_an_accepted_move():
    b, a = F.composite_pair()
    row = _row(a["chart_facts"], c0="lahiri_chitrapaksha", c2="MOON", c3="amsayu_contribution_years")
    _bump(row, 5, 12.0, 4)                                          # the contribution jumped by the modulus
    bad, _ = M.check(b, a)
    assert any(x.startswith("CS3") and "physical bound" in x for x in bad)


# ----------------------------------------------------------------------------------------------- CS1 / CS4 / CS5
def test_CS1_a_row_appearing_or_disappearing_fails():
    b, a = F.composite_pair()
    a["chart_facts"].append(["raman", "ayurdaya", "SUN", "pindayu_contribution_years", "pindayu", "5.0000", "single"])    # a second occurrence
    bad, _ = M.check(b, a)
    assert any(x.startswith("CS1") for x in bad)
    b, a = F.composite_pair()
    a["divisionals"] = [r for r in a["divisionals"] if not (r[2] == "Moon" and r[1] == "D9" and r[0] == "raman" and r[4] == "degree_in_sign")]
    assert any(x.startswith("CS1") for x in M.check(b, a)[0])
    b, a = F.composite_pair()
    a["chart_facts"].append(["raman", "sensitive_degree_check", "MOON", "brand_new_key", "x", "", "single"])
    assert any(x.startswith("CS1") for x in M.check(b, a)[0])


def test_CS4_a_non_composite_row_with_a_number_moving_fails():
    b, a = F.composite_pair()
    _bump(_row(a["divisionals"], c0="raman", c1="D9", c2="Mars", c4="sign_id"), 6, 1.0, 0)
    _bump(_row(a["divisionals"], c0="raman", c1="D9", c2="Mars", c4="house_from_varga_lagna"), 6, 1.0, 0)
    bad, _ = M.check(b, a)
    assert [x.split(" ")[0] for x in bad] == ["CS4", "CS4"], bad
    b, a = F.composite_pair()
    b["chart_facts"].append(["raman", "sensitive_degree_check", "MOON", "kranti", "north", "12.5", "single"])
    a["chart_facts"].append(["raman", "sensitive_degree_check", "MOON", "kranti", "north", "12.6", "single"])
    assert [x.split(" ")[0] for x in M.check(b, a)[0]] == ["CS4"]
    b, a = F.composite_pair()
    _row(a["chart_facts"], c0="raman", c2="CHART", c3="applicable_method")[5] = "3.0"          # a number appearing on a text-only class row
    assert [x.split(" ")[0] for x in M.check(b, a)[0]] == ["CS4"]


def test_CS5_the_changed_row_count_must_lie_in_the_derived_bound():
    # a rebuild that did not move the varga positions / sensitive degrees (0 < the guaranteed minimum 900 / 10)
    bad, stats = M.check(*F.composite_pair(varga_moved=False, sdc_moved=False))
    assert sorted(x.split(" ")[1] for x in bad) == ["sensitive_degree_check:", "varga_position:"] and all(x.startswith("CS5") for x in bad)
    # ayurdaya may be 0 (no row is guaranteed to cross)
    assert M.check(*F.composite_pair(ayu_moved=False))[0] == []
    # more than the physical maximum: every possible row plus a zero-shift node on Lahiri, one stored step each (1,170 > 1,140)
    b, a = F.composite_pair(varga_all_possible=True)
    for r in a["divisionals"]:
        if r[0] == "lahiri_chitrapaksha" and r[2] == "Rahu" and r[4] == "degree_in_sign":
            _bump(r, 6, 1e-6, 6)
    bad, stats = M.check(b, a)
    assert stats["varga_position"] == 1170 and [x.split(" ")[0] for x in bad] == ["CS5"] and "[900, 1140]" in bad[0]


# ----------------------------------------------------------------------------------------------- CS6: the label expectation is derived (x n per varga)


def test_CS6_is_silent_on_the_fixture_base():
    s = M.margin_summary(F.composite_pair()[0])
    assert {k: v["within_bound"] for k, v in s.items()} == {"varga_position": 0, "sensitive_degree_check": 0, "ayurdaya": 0}
    assert {k: v["rows"] for k, v in s.items()} == {"varga_position": 1500, "sensitive_degree_check": 135, "ayurdaya": 15}


def _set_natal_degree(b, a, ay, body, lam):
    """Every varga row of (ay, body) carries the NATAL degree; set it before, and before + the body's shift after (a consistent move)."""
    d = F.shift_deg(ay, body)
    for state, val in ((b, lam), (a, lam + d)):
        for r in state["divisionals"]:
            if r[0] == ay and r[2] == body and r[4] == "degree_in_sign":
                r[6] = format(round(val, 6), ".6f")


def _move(ay, body):
    return M.shift_deg(ay, body) + M._slack_deg() + M.D1_DEG_ROUNDING


@pytest.mark.parametrize("n", [2700, 150, 9])
def test_CS6_varga_bound_is_the_shift_times_n_per_varga(n):
    """Place the Moon (Lahiri) at 0.95 / 1.05 of its move from a D-n boundary k*30/n (k chosen so it is NOT a boundary of D1..D(n-1)
    and lies 0.01 deg from every boundary it is not on). Exactly the vargas that own that boundary (k*m divisible by n: D-n and its
    multiples, e.g. D2700) speak, and only when the D-n longitude margin is inside n x shift; every other varga stays silent."""
    ay, body, move = "lahiri_chitrapaksha", "Moon", _move("lahiri_chitrapaksha", "Moon")
    ns = [int(v[1:]) for v in M.VARGAS]

    def owns(m, k):
        return (k * m) % n == 0

    def clear_elsewhere(k):
        edge = k * 30.0 / n
        return all(min((edge * m / 30.0) % 1, 1 - (edge * m / 30.0) % 1) * 30.0 / m > 0.01 for m in ns if not owns(m, k))
    k = next(k for k in range(int(12.0 * n / 30.0), 10 ** 6) if not any(owns(m, k) for m in ns if m < n) and clear_elsewhere(k))
    edge = k * 30.0 / n
    owners = sorted(f"D{m}" for m in ns if owns(m, k))
    assert f"D{n}" in owners and not any(owns(m, k) for m in ns if m < n)
    for frac, expect in ((1.05, []), (0.95, owners)):
        b, a = F.composite_pair()
        _set_natal_degree(b, a, ay, body, edge + frac * move)
        bad, _ = M.check(b, a)
        hits = sorted({x.split("'")[3] for x in bad if x.startswith("CS6 varga_position")})
        assert hits == expect, (frac, bad[:3])
        assert not [x for x in bad if not x.startswith("CS6")], bad[:3]
        # the x n is what makes it bite: in varga degrees margin = n x (frac x move), bound = n x move (+- the 6-decimal storage, x n)
        mg, bd = [(mg, bd) for f, kk, mg, bd in M.label_margins(b) if f == "varga_position" and kk == (ay, f"D{n}", body)][0]
        assert bd == pytest.approx(n * move) and mg == pytest.approx(n * frac * move, abs=n * 1e-6)


def test_CS6_sensitive_degree_check_and_ayurdaya_label_margins():
    ay = "raman"
    def run(mutate):
        b, a = F.composite_pair()
        mutate(b, a)
        return [x for x in M.check(b, a)[0] if x.startswith("CS6")]
    move_moon = M.shift_deg(ay, "Moon") + M._slack_deg() + M.ORB_ROUNDING
    def orb(key, value):
        def f(b, a):
            for s in (b, a):
                _row(s["chart_facts"], c0=ay, c2="MOON", c3=key)[5] = format(round(value, 4), ".4f")
        return f
    # mrityu_bhaga: Moon tolerance 2/3 deg
    assert run(orb("mrityu_bhaga", 2 / 3 + 3 * move_moon)) == []
    assert ["tolerance" in x for x in run(orb("mrityu_bhaga", 2 / 3 + 0.0001))] == [True]
    # pushkara bhaga orb edge 0.5
    assert run(orb("pushkara", 0.5 + 3 * move_moon)) == []
    assert ["bhaga_orb" in x for x in run(orb("pushkara", 0.5 + 0.0001))] == [True]
    # pushkara navamsa edge (Aries: 20 deg): the D1 degree within the move of 20 deg
    hits = run(lambda b, a: _set_natal_degree(b, a, ay, "Moon", 20.0 + 0.5 * _move(ay, "Moon")))
    assert any("navamsa_edge" in x for x in hits)
    # ayurdaya total_years: 32 / 64 edges, bound = the total's CS3 bound
    bnd = M._bound_ayu(ay, "total_years", "PINDAYU")
    def total(v):
        def f(b, a):
            for s in (b, a):
                _row(s["chart_facts"], c0=ay, c2="PINDAYU", c3="total_years")[5] = format(round(v, 4), ".4f")
        return f
    assert run(total(64.0 + 3 * bnd)) == []
    assert ["ayurdaya" in x for x in run(total(64.0 - 0.0001))] == [True]


# ----------------------------------------------------------------------------------------------- CLI
def _write(path, state, chart=M.CANONICAL):
    with gzip.open(path, "wt") as f:
        json.dump(dict(state, meta={"chart_id": chart}), f)


def test_cli_exit_codes(tmp_path, capsys):
    b, a = F.composite_pair()
    _write(tmp_path / "b.json.gz", b)
    _write(tmp_path / "a.json.gz", a)
    assert M.main(["--compare", str(tmp_path / "b.json.gz"), str(tmp_path / "a.json.gz")]) == 0
    assert "composite_shift_check: PASS" in capsys.readouterr().out
    _row(a["divisionals"], c0="raman", c1="D9", c2="Moon", c4="degree_in_sign")[7] = "Taurus"
    _write(tmp_path / "a2.json.gz", a)
    assert M.main(["--compare", str(tmp_path / "b.json.gz"), str(tmp_path / "a2.json.gz")]) == 2
    out = capsys.readouterr().out
    assert "FAIL CS2" in out and "composite_shift_check: FAIL" in out
    _write(tmp_path / "other.json.gz", a, chart="1c826d5a-41cb-4450-b4dc-59d440e5f75a")
    assert M.main(["--compare", str(tmp_path / "b.json.gz"), str(tmp_path / "other.json.gz")]) == 6          # the bounds are unmeasured for any other chart
    capsys.readouterr()
    assert M.main(["--derive"]) == 0
    assert json.loads(capsys.readouterr().out)["ayurdaya"] == {"max": 120, "min": 0}
    assert M.main(["--nonsense"]) == 64
    assert M.main(["--margins", str(tmp_path / "b.json.gz")]) == 0
    assert json.loads(capsys.readouterr().out)["varga_position"]["within_bound"] == 0
    _set_natal_degree(b, a, "raman", "Moon", 15.0 + 0.5 * _move("raman", "Moon"))                       # a D1/D2 boundary within the shift
    _write(tmp_path / "b3.json.gz", b)
    assert M.main(["--margins", str(tmp_path / "b3.json.gz")]) == 2
    capsys.readouterr()
    assert M.main(["--margins", str(tmp_path / "other.json.gz")]) == 6
