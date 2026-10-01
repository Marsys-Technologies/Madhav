"""test_f3_msr_rebuild_order_guard.py -- the F-3 rebuild-plan invariant (MSR writers strictly before the
cascade-exposed dependents). Offline; ties the guard's producer set to the code and the DB constraint source."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import msr_rebuild_order_guard as g  # noqa: E402

PLATFORM = HERE.parents[2]
WRITERS = PLATFORM / "python-sidecar" / "pipeline" / "orchestrator" / "writers"
M1036 = PLATFORM / "supabase" / "migrations" / "1036_data_plane_l2_producer_generations.sql"


def test_msr_producers_equal_the_writers_that_insert_into_bodha_msr_signals():
    inserting = {p.stem for p in WRITERS.glob("bo_*.py")
                 if re.search(r"INSERT INTO\s+(public\.)?bodha_msr_signals", p.read_text())}
    assert inserting == set(g.MSR_PRODUCERS)


def test_msr_producers_equal_the_producer_asset_check_constraint():
    src = M1036.read_text()
    start = src.index("ADD CONSTRAINT bodha_msr_signals_producer_asset_check")
    block = src[start:src.index(");", start)]
    assert set(re.findall(r"'(bo_[a-z_]+)'", block)) == set(g.MSR_PRODUCERS)


def test_direct_dependents_are_the_five_fk_dropped_kala_assets():
    assert g.DIRECT_DEPENDENTS == {"ka_sangam", "ka_kalasutra", "ka_vighnakara", "ka_kala_darshana",
                                   "ka_bhavishya_lekha"}
    assert not g.DEPENDENTS & g.MSR_PRODUCERS


def test_order_violations_same_wave_later_wave_and_clean():
    assert g.check_plan_order([["bo_laksana"], ["ka_sangam"], ["ka_kalasutra"]]) == []
    same = g.check_plan_order([["bo_laksana", "ka_sangam"]])
    assert [(v.msr_producer, v.dependent) for v in same] == [("bo_laksana", "ka_sangam")]
    late = g.check_plan_order([["ka_sangam"], ["x"], ["bo_arudha"]])
    assert (late[0].msr_wave, late[0].dependent_wave) == (3, 1)
    # a producer planned twice: the LAST occurrence is the one that must precede every dependent
    assert g.check_plan_order([["bo_laksana"], ["ka_sangam"], ["bo_laksana"]])
    # a dependent planned twice: its FIRST occurrence is the one an MSR writer must precede
    assert g.check_plan_order([["ka_sangam"], ["bo_laksana"], ["ka_sangam"]])
    # transitive (phala) dependents are covered, assets outside both sets are not
    assert g.check_plan_order([["ph_nimitta"], ["bo_sudarshana"]])
    assert g.check_plan_order([["mi_bhavisya"], ["bo_laksana"]]) == []


def test_every_msr_producer_is_checked_against_every_dependent():
    for p in g.MSR_PRODUCERS:
        for d in g.DEPENDENTS:
            assert len(g.check_plan_order([[d], [p]])) == 1, (p, d)
            assert g.check_plan_order([[p], [d]]) == [], (p, d)


def test_parse_waves_accepts_manifest_and_bare_list_and_rejects_junk():
    assert g.parse_waves({"waves": [["a"], ["b"]]}) == [["a"], ["b"]]
    assert g.parse_waves([["a"]]) == [["a"]]
    with pytest.raises(ValueError):
        g.parse_waves({"waves": ["a"]})


def test_stale_against_msr_flags_only_dependents_built_before_the_last_msr_end():
    t = datetime(2026, 9, 8)
    rows = [("ka_sangam", t - timedelta(days=26), t), ("ka_kalasutra", t + timedelta(hours=1), t),
            ("ka_vighnakara", None, t), ("ka_kala_darshana", t, None), ("ph_nimitta", t, t)]
    assert g.stale_against_msr(rows) == ["ka_sangam"]


def test_main_manifest_exit_codes_and_vacuity_note(tmp_path, capsys):
    ok, bad, empty = tmp_path / "ok.json", tmp_path / "bad.json", tmp_path / "e.json"
    ok.write_text(json.dumps({"waves": [["bo_laksana"], ["ka_sangam"]]}))
    bad.write_text(json.dumps([["ka_sangam"], ["bo_laksana"]]))
    empty.write_text(json.dumps([["ka_sangam"]]))
    assert g.main(["--manifest", str(ok)]) == 0
    assert "VACUOUS" not in capsys.readouterr().out
    assert g.main(["--manifest", str(bad)]) == 1
    capsys.readouterr()
    assert g.main(["--manifest", str(empty)]) == 0
    assert "VACUOUS" in capsys.readouterr().out
    assert g.main(["--manifest", str(tmp_path / "missing.json")]) == 2
    assert g.main([]) == 2
    assert g._run_self_test() == 0
