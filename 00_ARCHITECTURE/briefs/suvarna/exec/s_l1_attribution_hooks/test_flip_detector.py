#!/usr/bin/env python3
"""Offline self-test for flip_detector.py (no database, no network). Run: python3 test_flip_detector.py   (also collectable by pytest)."""
import copy, json, os, sys, tempfile
from datetime import timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import flip_detector as F

NATIVE = F.NATIVE
OTHER = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"


def base_state():
    facts = []
    for ay in F.AYANS:
        facts += [[ay, "graha_position", "SUN", "sign", "Capricorn", "", "single"], [ay, "graha_position", "MOON", "nakshatra", "Purva Bhadrapada", "", "single"],
                  [ay, "graha_position", "LAGNA", "sign", "Aries", "", "single"], [ay, "graha_position", "MAR", "pada", "", "2", "single"],
                  [ay, "graha_position", "MOON", "longitude_sidereal", "", "327.055230133129", "single"],
                  [ay, "graha_gandanta", "MOON", "is_gandanta", "false", "", "single"], [ay, "argala_natal_matrix", "A1", "net", "", "1", "single"],
                  [ay, "graha_shadbala_total", "SUN", "total", "", "412.5", "two_pass_verified"]]
    for cat, subj, key, val in (("panchanga_tithi", "TITHI_BIRTH", "name", "Shukla Tritiya"), ("panchanga_vara", "VARA_BIRTH", "name", "Ravivara"),
                                ("panchanga_yoga", "YOGA_BIRTH", "name", "Shiva"), ("panchanga_karana", "KARANA_BIRTH", "name", "Garaja")):
        facts.append(["INVARIANT", cat, subj, key, val, "", "single"])
    dash = [["lahiri_chitrapaksha", "vimshottari", 1, "/Jupiter", "1975-08-18T21:50:23+00:00", "1991-08-18T21:50:23+00:00"],
            ["lahiri_chitrapaksha", "vimshottari", 1, "/Saturn", "1991-08-18T21:50:23+00:00", "2010-08-18T15:50:23+00:00"],
            ["lahiri_chitrapaksha", "yogini", 1, "/Pingala", "1950-01-01T00:00:00+00:00", "1951-02-04T23:13:00+00:00"]]
    return {"chart_facts": facts, "divisionals": [["lahiri_chitrapaksha", "D9", "Sun", "varga_position", "sign", "Leo", "", "Leo"]],
            "dashas": dash, "daily": [["2026-07-09", "5", "shukla", "5", "9", "Ashlesha", "3", "6", "7", "Panchami", "Guruvara", "Priti", "Taitila"]]}


def hooks_in(tmp, **files):
    for name, body in files.items():
        json.dump(body, open(os.path.join(tmp, name + ".json"), "w"))
    return F.load_hooks(tmp)


ARGALA = {"lane": "argala", "ruling": "argala", "description": "t", "may_change": [{"table": "chart_facts", "categories": ["argala_natal_matrix"]}]}
TIERS = {"lane": "tiers", "ruling": "tiers", "description": "t", "may_change": [{"table": "chart_facts", "categories": ["graha_shadbala_total"], "change_types": ["tier"]}]}


def run(snap, cur, hooks, chart=NATIVE, herrs=()):
    rep = F.compare_states(snap, cur, hooks, chart)
    return rep, F.exit_code(rep, list(herrs))


def mutate(state, fn):
    s = copy.deepcopy(state)
    fn(s)
    return s


def test_identical_is_clean():
    with tempfile.TemporaryDirectory() as t:
        hooks, errs = hooks_in(t, argala=ARGALA)
        assert not errs
        rep, code = run(base_state(), base_state(), hooks)
        assert code == 0 and rep["changes_total"] == 0 and not rep["ALERT_anchor_changed"]


def test_attributed_change_is_clean_and_names_the_lane():
    def f(s):
        for r in s["chart_facts"]:
            if r[1] == "argala_natal_matrix":
                r[5] = "2"
    with tempfile.TemporaryDirectory() as t:
        hooks, _ = hooks_in(t, argala=ARGALA)
        rep, code = run(base_state(), mutate(base_state(), f), hooks)
        assert code == 0 and rep["changes_total"] == 5 and rep["unattributed"] == 0
        assert all(c["lanes"] == ["argala"] for c in rep["changes"])


def test_unattributed_class_change_stops_the_wave():
    def f(s):
        for r in s["chart_facts"]:
            if r[1] == "graha_position" and r[2] == "MAR" and r[0] == "lahiri_chitrapaksha":
                r[5] = "3"
    with tempfile.TemporaryDirectory() as t:
        hooks, _ = hooks_in(t, argala=ARGALA)
        rep, code = run(base_state(), mutate(base_state(), f), hooks)
        assert code == 2 and rep["unattributed"] == 1


def test_continuous_and_timestamp_changes_are_not_class_changes():
    def f(s):
        for r in s["chart_facts"]:
            if r[3] == "longitude_sidereal":
                r[5] = "327.055415"
    rep, code = run(base_state(), mutate(base_state(), f), [])
    assert code == 0 and rep["changes_total"] == 0 and rep["continuous"]["chart_facts"]["changed"] == 5


def test_tier_change_needs_a_hook():
    def f(s):
        for r in s["chart_facts"]:
            if r[1] == "graha_shadbala_total":
                r[6] = "classical_match"
    rep, code = run(base_state(), mutate(base_state(), f), [])
    assert code == 2 and rep["unattributed"] == 5
    with tempfile.TemporaryDirectory() as t:
        hooks, _ = hooks_in(t, tiers=TIERS)
        rep, code = run(base_state(), mutate(base_state(), f), hooks)
        assert code == 0 and all(c["lanes"] == ["tiers"] for c in rep["changes"])


def test_expectation_mismatch_stops():
    h = copy.deepcopy(ARGALA)
    h["may_change"][0]["expected_count"] = {"exact": 3}

    def f(s):
        for r in s["chart_facts"]:
            if r[1] == "argala_natal_matrix":
                r[5] = "2"
    with tempfile.TemporaryDirectory() as t:
        hooks, errs = hooks_in(t, argala=h)
        assert not errs
        rep, code = run(base_state(), mutate(base_state(), f), hooks)
        assert code == 2 and rep["unattributed"] == 0 and len(rep["expectation_mismatches"]) == 1
        h["may_change"][0]["expected_count"] = {"min": 4, "max": 6}
        hooks, _ = hooks_in(t, argala=h)
        rep, code = run(base_state(), mutate(base_state(), f), hooks)
        assert code == 0


def test_anchor_change_is_alert_and_wins_over_unattributed():
    def f(s):
        for r in s["chart_facts"]:
            if r[0] == "lahiri_chitrapaksha" and r[1] == "graha_position" and r[2] == "LAGNA":
                r[4] = "Taurus"
    rep, code = run(base_state(), mutate(base_state(), f), [])
    assert code == 3 and rep["ALERT_anchor_changed"] and rep["unattributed"] == 1
    # anchors are native-only
    rep, code = run(base_state(), mutate(base_state(), f), [], chart=OTHER)
    assert code == 2 and not rep["ALERT_anchor_changed"]


def test_chart_scope_of_a_hook():
    h = copy.deepcopy(ARGALA)
    h["charts"] = [OTHER[:8]]

    def f(s):
        for r in s["chart_facts"]:
            if r[1] == "argala_natal_matrix":
                r[5] = "2"
    with tempfile.TemporaryDirectory() as t:
        hooks, _ = hooks_in(t, argala=h)
        assert run(base_state(), mutate(base_state(), f), hooks, chart=NATIVE)[1] == 2
        assert run(base_state(), mutate(base_state(), f), hooks, chart=OTHER)[1] == 0


def test_dasha_shift_and_rowset_need_hooks():
    def shift(s):
        for r in s["dashas"]:
            if r[1] == "vimshottari":
                for i in (4, 5):
                    r[i] = (F.ts_parse(r[i]) + timedelta(seconds=6993)).isoformat()
    rep, code = run(base_state(), mutate(base_state(), shift), [])
    assert code == 2 and rep["dasha_shift_unattributed"]
    eph = {"lane": "ephemeris", "ruling": "ephemeris backend", "description": "t",
           "may_change": [{"table": "chart_dashas", "kind": "dasha_shift", "systems": ["vimshottari"], "shift_range_sec": [6990, 6996]}]}
    with tempfile.TemporaryDirectory() as t:
        hooks, errs = hooks_in(t, ephemeris=eph)
        assert not errs
        rep, code = run(base_state(), mutate(base_state(), shift), hooks)
        assert code == 0 and rep["dashas"]["lahiri_chitrapaksha|vimshottari"]["lanes"] == ["ephemeris"]
        eph["may_change"][0]["shift_range_sec"] = [100, 200]
        hooks, _ = hooks_in(t, ephemeris=eph)
        assert run(base_state(), mutate(base_state(), shift), hooks)[1] == 2

    def drop(s):
        s["dashas"] = [r for r in s["dashas"] if r[3] != "/Saturn"]
    rep, code = run(base_state(), mutate(base_state(), drop), [])  # current lacks /Saturn
    assert code == 2 and [c["change"] for c in rep["changes"]] == ["disappeared"]
    rep, code = run(mutate(base_state(), drop), base_state(), [])  # current has an extra /Saturn
    assert code == 2 and [c["change"] for c in rep["changes"]] == ["appeared"]
    rowset = {"lane": "ephemeris", "ruling": "ephemeris backend", "description": "t",
              "may_change": [{"table": "chart_dashas", "categories": ["vimshottari"], "change_types": ["appeared", "disappeared"], "expected_count": {"exact": 1}}]}
    with tempfile.TemporaryDirectory() as t:
        hooks, errs = hooks_in(t, ephemeris=rowset)
        assert not errs
        assert run(base_state(), mutate(base_state(), drop), hooks)[1] == 0


def test_hook_validation():
    bad = {
        "empty": {"lane": "empty", "ruling": "x", "description": "d", "may_change": []},
        "wrongstem": {"lane": "other", "ruling": "x", "description": "d", "may_change": [{"table": "chart_facts", "categories": ["a"]}]},
        "regex": {"lane": "regex", "ruling": "x", "description": "d", "may_change": [{"table": "chart_facts", "categories": ["argala.*"]}]},
        "badtable": {"lane": "badtable", "ruling": "x", "description": "d", "may_change": [{"table": "charts", "categories": ["a"]}]},
        "nocat": {"lane": "nocat", "ruling": "x", "description": "d", "may_change": [{"table": "chart_facts", "categories": []}]},
        "badcount": {"lane": "badcount", "ruling": "x", "description": "d", "may_change": [{"table": "chart_facts", "categories": ["a"], "expected_count": {"exact": 1, "max": 2}}]},
        "unknownfield": {"lane": "unknownfield", "ruling": "x", "description": "d", "may_change": [{"table": "chart_facts", "categories": ["a"], "guess": "x.*"}]},
    }
    with tempfile.TemporaryDirectory() as t:
        for name, body in bad.items():
            for f in os.listdir(t):
                os.remove(os.path.join(t, f))
            hooks, errs = hooks_in(t, **{name: body})
            assert errs and not hooks, name
        for f in os.listdir(t):
            os.remove(os.path.join(t, f))
        hooks, errs = hooks_in(t, argala=ARGALA)
        assert not errs
        hooks, errs = F.load_hooks(t, required=["argala", "daridra"])
        assert len(errs) == 1 and "MISSING HOOK" in errs[0] and "daridra" in errs[0]
        assert F.exit_code(None, errs) == 2


def test_repo_seed_hooks_are_valid_and_daridra_is_absent():
    hooks, errs = F.load_hooks(HERE)
    assert not errs, errs
    lanes = {h["lane"] for h in hooks}
    assert {"argala", "gandanta"} <= lanes
    assert "daridra" not in lanes and not os.path.exists(os.path.join(HERE, "daridra.json"))


def test_read_only_guard():
    for bad in ("update chart_facts set x=1", "delete from chart_facts", "insert into x values (1)", "drop table x", "with a as (select 1) delete from x"):
        try:
            F.q(bad)
        except RuntimeError as e:
            assert "read-only" in str(e)
        else:
            raise AssertionError("non-SELECT statement was not refused: " + bad)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("PASS", t.__name__)
    print(f"{len(tests)} tests passed")
