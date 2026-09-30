"""Metrics arithmetic tests (protocol §5, §6, §8) with hand-computed figures.

Scenario A (T-cover / T-time):
  held-out: E1 exact 2010-05-20 surgery; E2 exact 2012-08-10 surgery.
  extract surgery windows:
    W1 2010-05-01→2010-06-01 pk 2010-05-25 si 0.9   (overlaps E1)
    W2 2011-01-01→2011-02-01 pk 2011-01-10 si 0.5   (overlaps neither)
  by hand:
    T-cover: E1 hit, E2 miss           -> 1/2
    T-time:  E1 error = |05-25 − 05-20| = 5 d; E2 miss = 182 (cap)
             capped median of [5, 182] = (5+182)/2 = 93.5
             uncapped hits = [[E1, 5]]; misses = 1
    T-rank:  surgery base rate = (32+32)/10334 = 0.62% — wait: W1 32 d + W2 32 d
             = 64/10334 = 0.619% -> >= 0.5 so NOT two-horns low; peak-diverse
             (2 distinct si) but N for E1's year 2010 = 1 < 3 -> ineligible;
             floor = 2//2+1 = 2; eligible 0 -> RANK-UNPROVEN.

Scenario B (T-rank percentiles, worst-rank miss convention):
  class career_advancement, four 2010 windows (70 admitted days = 0.677% of H,
  inside the 0.5-40% gain band):
    A 2010-01-01→2010-01-20 pk 01-10 si 0.9   (overlaps E1 2010-01-15)
    B 2010-03-01→2010-03-20 si 0.7
    C 2010-06-01→2010-06-20 si 0.5
    D 2010-09-01→2010-09-10 si 0.3
  E1 exact 2010-01-15: N=4, rank desc A,B,C,D -> A rank 1 -> pct 100(1-1)/4 = 0.0
  E2 exact 2010-12-25: N=4, no overlap -> miss -> percentile entered at 100 (§4.4)
  timing-usable 2, floor 2, both eligible -> VALID, median([0, 100]) = 50.0
  T-time: E1 error |01-10 − 01-15| = 5; E2 = 182 -> median 93.5; T-cover 1/2.
"""
from __future__ import annotations

import pytest

from services.gochara_eval import load_extract, load_registry
from services.gochara_eval.metrics import score_generation

from .conftest import synth_registry, write_json


def _counts(held, timing, year, exact, interval=0):
    return {"logged_events": held, "dev": 0, "held_out": held,
            "held_out_timing": timing, "held_out_year": year, "excluded": 0,
            "annotation_rows": 0, "exact_cohort": exact, "month_grain": 0,
            "interval_grain": interval, "t_rank_floor": timing // 2 + 1}


def _run(tmp_path, events, rows):
    reg_path = write_json(tmp_path / "reg.json", synth_registry(
        events, _counts(len(events),
                        sum(1 for e in events if e["tier"] == "held_out_timing"),
                        sum(1 for e in events if e["tier"] == "held_out_year"),
                        sum(1 for e in events if e["grain"] == "exact"),
                        sum(1 for e in events if e["grain"] == "interval"))))
    ext_path = write_json(tmp_path / "ext.json",
                          {"artifact": "t", "version": "0", "rows": rows})
    return score_generation(load_registry(reg_path), load_extract(ext_path))


def _ev(eid, grain, date, cls, tier="held_out_timing", span=None):
    d = {"eid": eid, "tier": tier, "obs_type": "point", "grain": grain,
         "class": cls}
    if span is not None:
        d["span"] = span
    else:
        d["date"] = date
    return d


def _w(cls, ws, we, pk, si, mechanism=None):
    r = {"event_class": cls, "ws": ws, "we": we, "pk": pk, "si": si,
         "valence": "gain"}
    if mechanism is not None:
        r["mechanism"] = mechanism
    return r


class TestScenarioA:
    def test_cover_and_time_arithmetic(self, tmp_path):
        events = [_ev("E1", "exact", "2010-05-20", "surgery"),
                  _ev("E2", "exact", "2012-08-10", "surgery")]
        rows = [_w("surgery", "2010-05-01", "2010-06-01", "2010-05-25", 0.9),
                _w("surgery", "2011-01-01", "2011-02-01", "2011-01-10", 0.5)]
        res = _run(tmp_path, events, rows)
        assert res["t_cover"]["hits"] == 1 and res["t_cover"]["total"] == 2
        assert res["t_cover"]["misses"] == ["E2"]
        assert res["t_cover"]["pass"] is False  # 1 < 32 bar
        tt = res["t_time"]
        assert tt["capped_median_days"] == 93.5   # median([5, 182])
        assert tt["misses"] == 1
        assert tt["uncapped_hits"] == [["E1", 5]]
        assert res["t_rank"]["status"] == "RANK-UNPROVEN"
        assert res["t_rank"]["floor"] == 2
        # T-FP: surgery burden 64/10334 = 0.6193% <= budget 5.2359% (n_c=2)
        assert res["t_fp"]["surgery"]["burden_pct"] == pytest.approx(0.6193, abs=1e-4)
        assert res["t_fp"]["surgery"]["pass"] is True


class TestScenarioB:
    def _res(self, tmp_path):
        events = [_ev("E1", "exact", "2010-01-15", "career_advancement"),
                  _ev("E2", "exact", "2010-12-25", "career_advancement")]
        rows = [_w("career_advancement", "2010-01-01", "2010-01-20",
                   "2010-01-10", 0.9),
                _w("career_advancement", "2010-03-01", "2010-03-20",
                   "2010-03-05", 0.7),
                _w("career_advancement", "2010-06-01", "2010-06-20",
                   "2010-06-05", 0.5),
                _w("career_advancement", "2010-09-01", "2010-09-10",
                   "2010-09-05", 0.3)]
        return _run(tmp_path, events, rows)

    def test_rank_percentile_and_worst_rank_miss(self, tmp_path):
        res = self._res(tmp_path)
        per = {p["eid"]: p for p in res["per_event"]}
        assert per["E1"]["N"] == 4 and per["E1"]["pct"] == 0.0
        assert per["E2"]["hit"] is False and per["E2"]["pct"] is None
        tr = res["t_rank"]
        assert tr["status"] == "VALID"
        # misses enter at percentile 100 -> median([0.0, 100.0]) = 50.0
        assert tr["median_percentile"] == 50.0 and tr["pass"] is False
        assert tr["eligible"] == 2 and tr["floor"] == 2

    def test_gain_band_enforced(self, tmp_path):
        res = self._res(tmp_path)
        g = res["t_fp_gain"]["career_advancement"]
        assert g["pass"] is True  # 0.677% inside 0.5-40%
        assert res["t_fp_overall"]["pass"] is True
        # T-time: median([5, 182]) = 93.5
        assert res["t_time"]["capped_median_days"] == 93.5

    def test_gain_band_fails_blanket_class(self, tmp_path):
        # one class covering the whole horizon -> 100% > 40% -> band FAIL
        events = [_ev("E1", "exact", "2010-01-15", "career_advancement")]
        rows = [_w("career_advancement", "1998-01-01", "2026-04-17",
                   "2010-01-15", 0.9)]
        res = _run(tmp_path, events, rows)
        assert res["t_fp_gain"]["career_advancement"]["pass"] is False
        assert res["t_fp_overall"]["pass"] is False


class TestRankVoid:
    def test_era_fingerprint_voids_rank_machine_readably(self, tmp_path):
        # two classes with identical window boundaries -> 100% of pairs -> VOID
        events = [_ev("E1", "exact", "2010-01-15", "career_advancement")]
        rows = [_w("career_advancement", "2010-01-01", "2010-01-20",
                   "2010-01-10", 0.9),
                _w("marriage", "2010-01-01", "2010-01-20", "2010-01-10", 0.4)]
        res = _run(tmp_path, events, rows)
        tr = res["t_rank"]
        assert tr["status"] == "VOID"
        assert "era-fingerprint" in tr["reason"]
        assert "median_percentile" not in tr  # no rank median emitted as result
        assert res["degeneracy"]["era_indiscriminate"] is True
        assert res["degeneracy"]["identical_pairs"] == [1, 1]

    def test_zero_candidates_no_crash_no_fake_number(self, tmp_path):
        events = [_ev("E1", "exact", "2010-01-15", "career_advancement")]
        res = _run(tmp_path, events, [])
        tr = res["t_rank"]
        assert tr["status"] in ("RANK-UNPROVEN", "VOID")
        assert "median_percentile" not in tr
        assert res["t_cover"]["hits"] == 0
        assert res["t_time"]["capped_median_days"] == 182  # lone miss at cap


class TestMechanismAttribution:
    def test_hit_attributed_to_window_mechanism(self, tmp_path):
        events = [_ev("E1", "exact", "2010-05-20", "surgery")]
        rows = [_w("surgery", "2010-05-01", "2010-06-01", "2010-05-20", 0.9,
                   mechanism="saturn_transit_8th")]
        res = _run(tmp_path, events, rows)
        assert res["mechanism_attribution"] == {
            "saturn_transit_8th": {"hits": 1, "eids": ["E1"]}}


class TestIntervalAndMaskClip:
    def test_span_years_clipped_candidate_set(self, tmp_path):
        # interval event [2007-01-01, 2008-12-31]; a window touching only 2008
        # joins the candidate set (§4.6) and scores a hit (C2 F2 probe shape)
        events = [_ev("E1", "interval", None, "chronic_onset",
                      span=["2007-01-01", "2008-12-31"])]
        rows = [_w("chronic_onset", "2008-03-01", "2008-05-30",
                   "2008-04-01", 0.8)]
        res = _run(tmp_path, events, rows)
        per = res["per_event"][0]
        assert per["hit"] is True and per["N"] == 1

    def test_post_mask_window_dropped_from_candidate_set(self, tmp_path):
        # window wholly after the 2026-04-17 mask is clipped out of N (C2 F3)
        events = [_ev("E1", "exact", "2026-03-20", "career_advancement")]
        rows = [_w("career_advancement", "2026-03-01", "2026-04-17",
                   "2026-03-20", 0.9),
                _w("career_advancement", "2026-05-01", "2026-06-01",
                   "2026-05-10", 0.8)]
        res = _run(tmp_path, events, rows)
        per = res["per_event"][0]
        assert per["hit"] is True and per["N"] == 1
