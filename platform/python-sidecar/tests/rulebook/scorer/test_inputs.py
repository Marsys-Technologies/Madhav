"""Readers for the step-5 timelines and the count_blind outputs, on synthetic files in the exact formats, with hash checks."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from services.rulebook.scorer import config as C

from ._toy import FAKE_COUNT_BLIND_SHA, FAKE_COUNT_BLIND_TESTS_SHA
from services.rulebook.scorer.inputs import (
    AGG_INTS,
    AGG_TEXT,
    DONOR_COLUMNS,
    DONOR_DIAG_COLUMNS,
    DONOR_ELIG_COLUMNS,
    donor_rows,
    TIMELINE_SCHEMA,
    UNIT_COLUMNS,
    AdmissionInputs,
    InputError,
    d7_decisions,
    profile_rows,
    read_count_blind,
    runs_to_states,
)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _write_json(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, sort_keys=True))


def _timeline_doc(cid, first, days, birth):
    h12 = date(birth.year + 12, birth.month, birth.day)
    return {
        "timeline_schema": TIMELINE_SCHEMA,
        "chart_id": cid,
        "confirmatory": True,
        "range": {"first": first.isoformat(), "last": (first + timedelta(days=days - 1)).isoformat(), "days": days},
        "horizon_inputs": {"dasha_first_day": first.isoformat(), "transit_first_day": "1902-02-11", "horizon_start_12y": h12.isoformat(), "dasha_starts_after_12th_birthday": False},
        "sunrise": {"provider": "x", "utc_epoch_seconds_sha256": "0", "no_sunrise_days": 0},
        "manifest_sha256": "m", "bundle_sha256": "b", "engine_version": "rulebook-engine-v1.0",
        "c2_masked_days": {"RB1-D1": 3},
        "members": {
            "RB1-D1": {"unit": "RB1-D1", "plane": "dasha", "polarity": "promotive", "chart_level": False, "runs": [[0, "F"], [10, "T"], [20, "N"], [23, "F"]]},
            "RB1-T1": {"unit": "RB1-VC21", "plane": "transit", "polarity": "obstructive", "chart_level": False, "runs": [[0, "T"], [5, "F"]]},
            "RB1-N1": {"unit": "RB1-N1", "plane": "natal_promise", "polarity": "promotive", "chart_level": True, "runs": [[0, "T"]]},
        },
    }


def _admission(tmp, charts=("C001", "C002"), break_hash=None, offset=None):
    d = tmp / "admission-v1_1"
    first = date(2000, 1, 1)
    hz = {"charts": {}, "provenance": {}, "step": "s5", "under_12_years": {}}
    for i, cid in enumerate(charts):
        birth = date(1980 + i, 3, 4)
        _write_json(d / "timelines" / f"{cid}.json", _timeline_doc(cid, first, 100, birth))
        hz["charts"][cid] = {"confirmatory": "Y", "death_source": "alive", "range_first": first.isoformat(),
                             "families": {"dasha": {"start": (first + timedelta(days=5)).isoformat(), "end": (first + timedelta(days=60)).isoformat(), "days": 56, "years": 0.15, "under_12_years": False},
                                          "transit": {"start": first.isoformat(), "end": (first + timedelta(days=99)).isoformat(), "days": 100, "years": 0.27, "under_12_years": False}}}
    _write_json(d / "out" / "s5_horizons.json", hz)
    offset = {c: (i % 2 == 1) for i, c in enumerate(charts)} if offset is None else offset  # SUR-RB-48 per-chart record
    ledger = {c: ({"admitted": True, "reason": None, "offset_normalised": offset[c]} if c in offset else {"admitted": True, "reason": None}) for c in charts}
    _write_json(d / "out" / "s6_admit.json", {"admitted": list(charts), "dry_run_set": ["C900"], "donor_pool_candidates": list(charts), "ledger": ledger})
    files = {}
    for sub in ("timelines", "out"):
        for p in sorted((d / sub).glob("*.json")):
            files[f"{sub}/{p.name}"] = _sha(p)
    if break_hash:
        files[break_hash] = "0" * 64
    _write_json(d / "out" / "TIMELINES_MANIFEST.json", {"manifest": "x", "format": {}, "provenance": {}, "files": files})
    return d


def test_runs_to_states_expands_and_validates():
    assert runs_to_states([[0, "F"], [2, "T"], [4, "N"]], 6).tolist() == [0, 0, 1, 1, -1, -1]
    for bad in ([[1, "T"]], [[0, "T"], [0, "F"]], [[0, "X"]], [[0, "T"], [9, "F"]], []):
        with pytest.raises(InputError):
            runs_to_states(bad, 6)


def test_admission_timelines_slice_to_the_family_horizon_and_keep_the_plane(tmp_path):
    adm = AdmissionInputs(str(_admission(tmp_path)))
    assert adm.admitted() == ["C001", "C002"] and adm.dry_run_set() == ["C900"]
    d = adm.timeline("C001", "dasha")
    assert set(d.states) == {"RB1-D1"}  # dasha members only; natal and transit members are not read into this family
    assert d.h_start == date(2000, 1, 6).toordinal() and d.n_days == 56
    full = runs_to_states([[0, "F"], [10, "T"], [20, "N"], [23, "F"]], 100)
    assert d.states["RB1-D1"].tolist() == full[5:61].tolist()  # index 0 = range.first; sliced to the horizon
    assert d.birth == date(1980, 3, 4).toordinal()  # from horizon_start_12y minus 12 years
    t = adm.timeline("C002", "transit")
    assert set(t.states) == {"RB1-T1"} and t.n_days == 100
    assert [x.code for x in adm.timelines("dasha")] == ["C001", "C002"]


def test_any_file_that_does_not_match_the_manifest_is_refused(tmp_path):
    d = _admission(tmp_path)
    p = d / "timelines" / "C002.json"
    doc = json.loads(p.read_text())
    doc["members"]["RB1-D1"]["runs"] = [[0, "T"]]  # tampered after the manifest was written
    p.write_text(json.dumps(doc))
    adm = AdmissionInputs(str(d))
    adm.timeline("C001", "dasha")
    with pytest.raises(InputError, match="sha256"):
        adm.timeline("C002", "dasha")
    # a file the manifest does not list is refused as well
    (d / "timelines" / "C003.json").write_text(json.dumps(_timeline_doc("C003", date(2000, 1, 1), 100, date(1985, 1, 1))))
    with pytest.raises(InputError, match="not listed"):
        adm.timeline("C003", "dasha")
    # a missing manifest stops everything
    (d / "out" / "TIMELINES_MANIFEST.json").unlink()
    with pytest.raises(InputError):
        AdmissionInputs(str(d))


def test_timeline_schema_and_chart_id_are_checked(tmp_path):
    d = _admission(tmp_path)
    adm = AdmissionInputs(str(d), verify=False)
    p = d / "timelines" / "C001.json"
    doc = json.loads(p.read_text())
    doc["timeline_schema"] = "something-else"
    p.write_text(json.dumps(doc))
    with pytest.raises(InputError, match="timeline_schema"):
        adm.timeline("C001", "dasha")


# ── count_blind ──────────────────────────────────────────────────────────────────────────────────────
def _csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def _count_blind(tmp, n_charts=20, per=25, opp=6, units_n=12, tamper=False, script_sha=None):
    d = tmp / "count_blind"
    d.mkdir()
    agg = []
    for i in range(n_charts):
        cid = "C%03d" % (i + 1)
        for fam in ("dasha", "transit"):
            # a favourable month row, an unfavourable day row, a mixed row, a G3 row (dropped)
            agg.append([cid, fam, "primary_nonschedulable", "career_adv_change_entry", "favourable", "month", per, per - 2, opp, 1, 0, 0, 2, 0, 0, 0])
            agg.append([cid, fam, "primary_nonschedulable", "illness_chronic_surgery", "unfavourable", "day", 3, 3, 1, 0, 0, 0, 0, 0, 0, 0])
            agg.append([cid, fam, "primary_nonschedulable", "relocation_travel", "mixed", "month", 4, 0, 0, 0, 0, 4, 0, 0, 0, 0])
            agg.append([cid, fam, "all", "career_adv_change_entry", "favourable", "month", per + 5, per + 3, opp, 1, 0, 0, 2, 0, 0, 0])
        agg.append([cid, "dasha", "primary_nonschedulable", "other", "favourable", "year", 0, 0, 0, 0, 0, 0, 0, 0, 1, 0])
    _csv(d / "COUNT_BLIND_AGGREGATES.csv", list(AGG_TEXT + AGG_INTS), agg)
    don = []
    for thr in (3, 5, 8):
        for i in range(n_charts):
            cid = "C%03d" % (i + 1)
            in_pool = 1 if (i < n_charts - 2 or thr == 3) else 0
            don.append([thr, "dasha", "primary_nonschedulable", cid, in_pool, (17 if in_pool else ""), (4 if (in_pool and i % 4 == 0) else (12 if in_pool else ""))])
    _csv(d / "COUNT_BLIND_DONORS.csv", list(DONOR_COLUMNS), don)
    uni = [[thr, "dasha", "primary_nonschedulable", f"RB1-U{k:02d}", (units_n if k < 9 else 3)] for thr in (3, 5, 8) for k in range(12)]
    _csv(d / "COUNT_BLIND_UNITS.csv", list(UNIT_COLUMNS), uni)
    # count_blind v2: per pool chart donor eligibility, and the per-check diagnostic (exact formats, SUR-RB-41)
    dele, ddg = [], []
    for thr in (3, 5, 8):
        pool = [i for i in range(n_charts) if (i < n_charts - 2 or thr == 3)]
        for i in pool:
            # count_blind V3 adds the 95% bar: fewer donors, fewer imputed cells
            dele.append([thr, "dasha", "primary_nonschedulable", "C%03d" % (i + 1), 26, 3, 3, 17, 16, 4, 6, 9, 2, 1, 0])
        n = len(pool)
        ok = int(n >= 15)
        # (b): 95% keeps the floor (16 charts with >= 5 donors at thr 5); (c): 95% misses it (2 charts), share empty
        ddg.append([thr, "dasha", "primary_nonschedulable", "b", n, 0, 0, n, ok, "0.012345", min(n, 16), int(min(n, 16) >= 15), "0.004000"])
        ddg.append([thr, "dasha", "primary_nonschedulable", "c", n, 0, 0, n, ok, "0.023456", 2, 0, ""])
        ddg.append([thr, "transit", "primary_nonschedulable", "b", n, n, ok, n, ok, "", n, ok, ""])
        ddg.append([thr, "transit", "primary_nonschedulable", "c", n, n, ok, n, ok, "", n, ok, ""])
    _csv(d / "COUNT_BLIND_DONOR_ELIGIBILITY.csv", list(DONOR_ELIG_COLUMNS), dele)
    _csv(d / "COUNT_BLIND_DONOR_DIAGNOSTIC.csv", list(DONOR_DIAG_COLUMNS), ddg)
    outs = {p.name: _sha(p) for p in sorted(d.glob("*.csv"))}
    if tamper:
        outs["COUNT_BLIND_UNITS.csv"] = "f" * 64
    (d / "COUNT_BLIND_RUN.log").write_text(json.dumps({"count_blind": "completed", "outputs_sha256": outs}) + "\n")
    (d / "COUNT_BLIND_RUN.json").write_text(json.dumps({"script": "count_blind.py", "script_sha256": script_sha or FAKE_COUNT_BLIND_SHA, "tests_sha256": FAKE_COUNT_BLIND_TESTS_SHA, "outputs_sha256": outs}))
    return d


def test_count_blind_readers_and_d7_decisions(tmp_path):
    cb = read_count_blind(str(_count_blind(tmp_path)))
    d = d7_decisions(cb, 5, "dasha")
    assert d["admitted"] == ["C%03d" % i for i in range(1, 19)]  # in_pool at threshold 5: the last two are out
    assert d["episodes_scored_applicable"] == 18 * (23 + 3)  # favourable + unfavourable rows; mixed and G3 rows never count
    assert d["charts_with_scored"] == 18 and d["counts_ok"] is True
    assert d["dir_episodes"] == 18 * (6 + 1) and d["dir_testable"] is True
    # count_blind v2: the K11 donor counts come from the donor diagnostic under the rule it decides (here P2, 18 charts);
    # the v1 COUNT_BLIND_DONORS horizon-only counts (18 and 13) are no longer what D7 reads
    assert d["donor_charts_b"] == 18 and d["donor_charts_c"] == 18 and d["donor_floor_ok"] is True
    cb.donor_diagnostic = []  # review VERIFY3 G5: without a diagnostic there is no fallback to the v1 counts
    with pytest.raises(InputError, match="no \\(b\\) and \\(c\\) rows"):
        d7_decisions(cb, 5, "dasha")
    cb = read_count_blind(str(tmp_path / "count_blind"))
    assert d["z25_units"] == ["RB1-U%02d" % k for k in range(9)]  # 9 units with >= 10 applicable episodes (>= 8 needed)
    assert d["a7_ok"] is False  # 18 charts < 20
    d3 = d7_decisions(cb, 3, "dasha")
    assert len(d3["admitted"]) == 20 and d3["a7_ok"] is True  # 20 charts and 520 scored-applicable episodes


def test_direction_and_z25_floors_from_counts(tmp_path):
    cb = read_count_blind(str(_count_blind(tmp_path, opp=0, units_n=12)))
    d = d7_decisions(cb, 3, "dasha")
    assert d["dir_episodes"] == 20 and d["dir_testable"] is False  # 20 < 100 episodes with an opposite unit (K4)


def test_z25_needs_eight_units(tmp_path):
    d = _count_blind(tmp_path)
    rows = list(csv.reader(open(d / "COUNT_BLIND_UNITS.csv")))
    for r in rows[1:]:
        if r[3] >= "RB1-U07":
            r[4] = "2"  # only 7 units keep >= 10 episodes
    _csv(d / "COUNT_BLIND_UNITS.csv", rows[0], rows[1:])
    run = json.loads((d / "COUNT_BLIND_RUN.json").read_text())
    run["outputs_sha256"]["COUNT_BLIND_UNITS.csv"] = _sha(d / "COUNT_BLIND_UNITS.csv")
    (d / "COUNT_BLIND_RUN.json").write_text(json.dumps(run))
    assert d7_decisions(read_count_blind(str(d)), 3, "dasha")["z25_units"] == []


def test_count_blind_hash_mismatch_and_format_errors_are_refused(tmp_path):
    with pytest.raises(InputError, match="sha256"):
        read_count_blind(str(_count_blind(tmp_path, tamper=True)))
    sub = tmp_path / "b"
    sub.mkdir()
    d = _count_blind(sub)
    rows = list(csv.reader(open(d / "COUNT_BLIND_DONORS.csv")))
    rows[1][4] = "2"  # in_pool must be 1 or 0
    _csv(d / "COUNT_BLIND_DONORS.csv", rows[0], rows[1:])
    with pytest.raises(InputError):
        read_count_blind(str(d), verify=False)
    rows[0][0] = "thresh"  # wrong header
    rows[1][4] = "1"
    _csv(d / "COUNT_BLIND_DONORS.csv", rows[0], rows[1:])
    with pytest.raises(InputError, match="columns"):
        read_count_blind(str(d), verify=False)


def test_profile_rows_for_part_f(tmp_path):
    cb = read_count_blind(str(_count_blind(tmp_path, n_charts=3, per=4)))
    prof = profile_rows(cb, ["C001", "C002", "C003", "C999"])
    assert len(prof) == 4 and prof[3] == ()
    c1 = prof[0]
    assert c1.count(("career_adv_change_entry", "favourable", C.G2)) == 4  # episodes column, month grade
    assert c1.count(("illness_chronic_surgery", "unfavourable", C.G1)) == 3  # day grade
    assert all(x[1] in ("favourable", "unfavourable") for x in c1)  # mixed rows are never placed


def test_count_blind_v2_donor_outputs_are_read_and_decide_the_p1_trigger(tmp_path):
    cb = read_count_blind(str(_count_blind(tmp_path)))
    assert len(cb.donor_eligibility) == 20 + 18 + 18 and len(cb.donor_diagnostic) == 12
    d = d7_decisions(cb, 5, "dasha")
    # M3 misses the K11 floor for both checks in this file: P2 applies, and its counts decide the floor
    assert d["donor_rule_b"] == "p2_90" and d["donor_rule_c"] == "p2_90"
    assert d["donor_charts_b"] == 18 and d["donor_charts_c"] == 18 and d["donor_floor_ok"] is True
    dr = donor_rows(cb, 5, "dasha")
    assert dr["charts"]["C001"] == {"own_cells": 26, "donors_b_m3": 3, "donors_c_m3": 3, "donors_b_p2": 17, "donors_c_p2": 16, "imputed_cells_b_p2": 4, "imputed_cells_c_p2": 6,
                                  "donors_b_p95": 9, "donors_c_p95": 2, "imputed_cells_b_p95": 1, "imputed_cells_c_p95": 0}
    assert dr["checks"]["b"]["imputed_cell_share_p2"] == "0.012345" and dr["checks"]["b"]["k11_floor_met_m3"] == 0


def test_count_blind_v2_files_are_hash_checked_and_format_checked(tmp_path):
    d = _count_blind(tmp_path)
    rows = list(csv.reader(open(d / "COUNT_BLIND_DONOR_DIAGNOSTIC.csv")))
    rows[1][6] = "2"  # a K11 flag must be 0 or 1
    _csv(d / "COUNT_BLIND_DONOR_DIAGNOSTIC.csv", rows[0], rows[1:])
    with pytest.raises(InputError, match="sha256"):
        read_count_blind(str(d))
    with pytest.raises(InputError, match="k11"):
        read_count_blind(str(d), verify=False)
    sub = tmp_path / "x"
    sub.mkdir()
    d2 = _count_blind(sub)
    (d2 / "COUNT_BLIND_DONOR_ELIGIBILITY.csv").unlink()
    with pytest.raises(Exception):
        read_count_blind(str(d2), verify=False)


def test_sur_rb_48_offset_normalised_charts_are_read_from_s6_admit(tmp_path):
    adm = AdmissionInputs(str(_admission(tmp_path, charts=("C001", "C002", "C003"), offset={"C001": False, "C002": True, "C003": True})))
    assert adm.offset_normalised_count(["C001", "C002", "C003"]) == 2
    assert adm.offset_normalised_count(["C001", "C002"]) == 1 and adm.offset_normalised_count(["C001", "C001"]) == 0
    sub = tmp_path / "missing"
    sub.mkdir()
    adm2 = AdmissionInputs(str(_admission(sub, charts=("C001", "C002"), offset={"C001": True})))  # C002 has no record
    with pytest.raises(InputError, match="SUR-RB-48"):
        adm2.offset_normalised_count(["C001", "C002"])
    assert adm2.offset_normalised_count(["C001"]) == 1
    sub3 = tmp_path / "str"
    sub3.mkdir()
    adm3 = AdmissionInputs(str(_admission(sub3, charts=("C001",), offset={"C001": "yes"})))  # not a boolean
    with pytest.raises(InputError, match="SUR-RB-48"):
        adm3.offset_normalised_count(["C001"])
