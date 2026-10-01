"""test_f3_msr_rebuild_order_guard.py -- the F-3 rebuild-plan invariant (MSR writers strictly before the
cascade-exposed dependents). Offline; ties the guard's producer set to the code and the DB constraint source."""
from __future__ import annotations

import copy
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


# ---- derived dependents (item: derive from DDL and writers, not by hand) ---------------------------------

MAP = json.loads((HERE.parent / "msr_signal_bearing_tables.json").read_text())
MIG_TEXT = {p.name: p.read_text() for d in (PLATFORM / "supabase" / "migrations", PLATFORM / "migrations")
            for p in d.glob("*.sql")}
WRITER_TEXT = {p.stem: p.read_text() for p in WRITERS.glob("*.py")}
_ALL_TABLES = [(t["table"], t["assets"]) for t in MAP["tables"]] + \
    [(t, [a]) for t, a in MAP["transitive_cascade"]["tables"]]


def _writers_of(table: str) -> set[str]:
    return {stem for stem, txt in WRITER_TEXT.items()
            if re.search(rf"INSERT INTO\s+(public\.)?{table}\b", txt)}


@pytest.mark.parametrize("table,assets", _ALL_TABLES)
def test_map_assets_are_exactly_the_writers_that_insert_into_each_table(table, assets):
    assert _writers_of(table) == set(assets)


@pytest.mark.parametrize("t", MAP["tables"], ids=lambda t: t["table"])
def test_map_columns_are_declared_in_the_migrations(t):
    for col in t["columns"]:
        assert any(t["table"] in txt and col in txt for txt in MIG_TEXT.values()), (t["table"], col)


def test_map_covers_every_signal_bearing_column_in_the_catalog_snapshot():
    snap = set(MAP["catalog_snapshot"]) - {c for c in MAP["catalog_snapshot"] if c.startswith("bodha_msr_signals.")}
    assert snap == g.mapped_columns()


def test_ka_yojaka_and_every_signal_bearing_writer_are_dependents():
    assert {"ka_yojaka", "ph_nimitta", "bo_karanajala", "bo_samskara", "bo_sangati", "bo_pratijna"} <= g.DEPENDENTS
    assert g.check_plan_order([["ka_yojaka"], ["bo_laksana"]])           # wave 2 of the real plan
    assert not g.MSR_PRODUCERS & g.DEPENDENTS


# ---- the REAL rebuild plan structure -----------------------------------------------------------------------

REAL = json.loads((HERE / "fixtures" / "f3_canonical_rebuild_plan_waves.json").read_text())["waves"]


def _first_wave(asset):
    return next(i for i, w in enumerate(REAL) if asset in w)


def test_real_plan_has_no_msr_writer_so_the_check_is_vacuous_and_says_so():
    assert g.check_plan_order(REAL) == []
    assert g.plan_vacuity(REAL) == ["no MSR writer in the plan"]


def test_six_msr_writers_before_every_dependent_pass_and_are_not_vacuous():
    plan = [sorted(g.MSR_PRODUCERS)] + copy.deepcopy(REAL)
    assert g.check_plan_order(plan) == [] and g.plan_vacuity(plan) == []


@pytest.mark.parametrize("producer", sorted(g.MSR_PRODUCERS))
def test_each_msr_writer_placed_after_a_kala_asset_fails(producer):
    k = _first_wave("ka_sangam")
    plan = copy.deepcopy(REAL)
    plan.insert(k + 1, [producer])
    viol = g.check_plan_order(plan)
    assert viol and all(v.msr_producer == producer for v in viol)
    assert {"ka_sangam", "ka_kalasutra"} <= {v.dependent for v in viol} or \
        {"ka_sangam"} <= {v.dependent for v in viol}
    same = copy.deepcopy(REAL)
    same[k].append(producer)                                              # same wave: parallel, also a violation
    assert any(v.dependent == "ka_sangam" for v in g.check_plan_order(same))


def test_main_require_nonvacuous_fails_the_real_plan_and_it_is_loud(tmp_path, capsys):
    f = tmp_path / "real.json"
    f.write_text(json.dumps({"waves": REAL}))
    assert g.main(["--manifest", str(f)]) == 0
    assert "VACUOUS (no MSR writer in the plan)" in capsys.readouterr().out
    assert g.main(["--manifest", str(f), "--require-nonvacuous"]) == 1
    ok = tmp_path / "ok.json"
    ok.write_text(json.dumps([sorted(g.MSR_PRODUCERS)] + REAL))
    assert g.main(["--manifest", str(ok), "--require-nonvacuous"]) == 0
    only_msr = tmp_path / "m.json"
    only_msr.write_text(json.dumps([["bo_laksana"]]))
    assert g.main(["--manifest", str(only_msr), "--require-nonvacuous"]) == 1   # nothing to order against


def test_unmapped_columns_reports_every_live_column_the_map_does_not_know():
    known = set(g.mapped_columns())
    assert g.unmapped_columns(known) == []
    assert g.unmapped_columns(known | {"kala_new.signal_id", "bodha_x.signal_ids"}) == ["bodha_x.signal_ids", "kala_new.signal_id"]
    assert g.unmapped_columns(set()) == []


def test_transitive_cascade_assets_are_dependents_even_though_they_hold_no_signal_id():
    assert g.TRANSITIVE_DEPENDENTS == {"ph_pramana", "ph_sankrama", "ph_sodhana", "ph_suddha_sodhana",
                                       "ph_pratikara", "ph_muhurta"}
    assert g.TRANSITIVE_DEPENDENTS <= g.DEPENDENTS
    assert g.check_plan_order([["ph_pramana"], ["bo_laksana"]])
    assert g.check_plan_order([["bo_laksana"], ["ph_pramana"]]) == []
