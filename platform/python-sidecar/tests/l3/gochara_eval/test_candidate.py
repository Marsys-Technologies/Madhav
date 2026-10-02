"""Candidate adapter + scorer (services/gochara_eval/candidate.py): unknown handling, bounds soundness, '3.0' reproduction.

Synthetic extracts throughout; the '3.0' reproduction and the random equivalence property run only with the campaign checkout.
"""
from __future__ import annotations

import datetime as dt
import json
import random

import pytest

from services.gochara_eval import load_extract, load_registry, score_generation
from services.gochara_eval.candidate import (CandWindow, event_bounds, load_candidate_extract, merge_candidates,
                                             plateau_verdict, score_candidate)
from services.gochara_eval.extract import InputRejected, merge_windows
from services.gochara_eval.metrics import event_hit

from .conftest import (CAMPAIGN_MEASUREMENT, CONTROLS_V1_3, EXTRACT_3_0, EXTRACT_3_0_PIN, REGISTRY_V2_3, needs_campaign,
                       synth_registry, synth_registry_counts, write_json)

CLS = "career_advancement"


def reg_one_exact(tmp_path, date="2010-05-20"):
    events = [{"eid": "EVT.X.01", "tier": "held_out_timing", "obs_type": "point", "grain": "exact", "date": date, "class": CLS}]
    counts = {**synth_registry_counts(), "logged_events": 1, "dev": 0, "held_out": 1, "held_out_timing": 1,
              "held_out_year": 0, "excluded": 0, "annotation_rows": 0, "exact_cohort": 1}
    return load_registry(write_json(tmp_path / "reg.json", synth_registry(events, counts)))


def row(ws, we, pk, si, cls=CLS):
    return {"event_class": cls, "ws": ws, "we": we, "pk": pk, "si": si, "valence": "gain", "adv": False,
            "resolution": None, "temporal_shape": "interval"}


def ext(tmp_path, rows, name="x.json"):
    p = write_json(tmp_path / name, {"artifact": "t", "version": "0", "rows": rows})
    return load_candidate_extract(p)


def year_rows(unknown_a=False, unknown_other=False):
    """2010 candidate set for the class: A holds the event (si .5), B (.9), C (.1) elsewhere in the year; optionally an unknown."""
    rows = [row("2010-04-01", "2010-07-01", "2010-05-18", None if unknown_a else 0.5),
            row("2010-08-01", "2010-08-10", "2010-08-05", 0.9),
            row("2010-10-01", "2010-10-10", "2010-10-05", 0.1)]
    if unknown_other:
        rows.append(row("2010-12-01", "2010-12-10", "2010-12-05", None))
    return rows


class TestAdapter:
    def test_unknown_si_stays_in_the_candidate_set_and_in_n(self, tmp_path):
        reg = reg_one_exact(tmp_path)
        known = ext(tmp_path, year_rows())
        withu = ext(tmp_path, year_rows(unknown_other=True), "y.json")
        assert event_bounds(reg.held[0], known.merged, reg)["N"] == 3
        assert event_bounds(reg.held[0], withu.merged, reg)["N"] == 4          # counted, never dropped or zero-filled
        assert withu.unknown_rows == 1

    def test_merge_group_with_an_unknown_member_has_an_unqualified_representative(self):
        m = merge_candidates([row("2010-01-01", "2010-01-31", "2010-01-10", 0.7),
                              row("2010-02-01", "2010-02-10", "2010-02-05", None)])      # abutting -> one group
        (w,) = m[CLS]
        assert (w.si, w.pk, w.unknown_members, w.members) == (None, None, 1, 2)
        assert (w.ws, w.we) == (dt.date(2010, 1, 1), dt.date(2010, 2, 10))              # the extent is admission: still known

    @pytest.mark.parametrize("seed", range(10))
    def test_known_groups_merge_exactly_like_the_existing_adapter(self, seed):
        rng = random.Random(seed)
        rows = []
        for _ in range(40):
            d0 = dt.date(2005, 1, 1) + dt.timedelta(days=rng.randrange(0, 900))
            d1 = d0 + dt.timedelta(days=rng.randrange(0, 40))
            rows.append(row(d0.isoformat(), d1.isoformat(), (d0 + (d1 - d0) // 2).isoformat(),
                            rng.choice([0.1, 0.1 + 0.5e-9, 0.3, 0.7]), cls=rng.choice([CLS, "marriage"])))
        new, old = merge_candidates(rows), merge_windows(rows)
        assert {c: [(w.ws, w.we, w.pk, w.si) for w in ws] for c, ws in new.items()} == \
               {c: [(w.ws, w.we, w.pk, w.si) for w in ws] for c, ws in old.items()}

    @pytest.mark.parametrize("bad,reason", [
        ({"si": -0.01}, "si < 0"), ({"si": float("nan")}, "non-finite"), ({"si": float("inf")}, "non-finite"),
        ({"event_class": "not_a_class"}, "27-class"), ({"we": "2009-01-01"}, "we < ws"),
    ])
    def test_input_rejected(self, tmp_path, bad, reason):
        r = {**row("2010-04-01", "2010-07-01", "2010-05-18", 0.5), **bad}
        p = write_json(tmp_path / "b.json", {"rows": [r]})
        with pytest.raises(InputRejected) as e:
            load_candidate_extract(p)
        assert reason in e.value.reason

    def test_absent_si_key_is_rejected_but_explicit_null_is_not(self, tmp_path):
        r = row("2010-04-01", "2010-07-01", "2010-05-18", 0.5)
        del r["si"]
        with pytest.raises(InputRejected, match="no `si` key"):
            load_candidate_extract(write_json(tmp_path / "a.json", {"rows": [r]}))
        load_candidate_extract(write_json(tmp_path / "b.json", {"rows": [{**r, "si": None}]}))

    def test_known_si_without_a_peak_is_rejected(self, tmp_path):
        r = row("2010-04-01", "2010-07-01", None, 0.5)
        with pytest.raises(InputRejected, match="peak date"):
            load_candidate_extract(write_json(tmp_path / "a.json", {"rows": [r]}))

    def test_hash_pin_is_measured(self, tmp_path):
        p = write_json(tmp_path / "a.json", {"rows": [row("2010-04-01", "2010-07-01", "2010-05-18", 0.5)]})
        with pytest.raises(InputRejected, match="sha256"):
            load_candidate_extract(p, declared_pin="0" * 64)


class TestBounds:
    def test_known_percentile(self, tmp_path):
        reg = reg_one_exact(tmp_path)
        b = event_bounds(reg.held[0], ext(tmp_path, year_rows()).merged, reg)
        assert (b["hit"], b["N"], b["pct"], b["bounds_status"]) == (True, 3, pytest.approx(100 * (2 - 1) / 3), "EXACT")

    def test_unknown_competitor_widens_to_a_range(self, tmp_path):
        reg = reg_one_exact(tmp_path)
        b = event_bounds(reg.held[0], ext(tmp_path, year_rows(unknown_other=True)).merged, reg)
        # matched .5; known others .9, .1; one unknown; N=4: u<.5 -> rank 2 -> 25; tie -> 37.5; u>.5 -> rank 3 -> 50
        assert (b["pct_lo"], b["pct_hi"], b["pct"]) == (25.0, 50.0, None)
        assert b["bounds_status"] == "BOUNDED"

    def test_matched_at_zero_cannot_be_beaten_from_below(self, tmp_path):
        reg = reg_one_exact(tmp_path)
        rows = [row("2010-04-01", "2010-07-01", "2010-05-18", 0.0), row("2010-08-01", "2010-08-10", "2010-08-05", 2.0),
                row("2010-10-01", "2010-10-10", "2010-10-05", 1.0), row("2010-11-01", "2010-11-05", "2010-11-02", None),
                row("2010-12-01", "2010-12-05", "2010-12-02", None)]
        b = event_bounds(reg.held[0], ext(tmp_path, rows).merged, reg)
        assert (b["pct_lo"], b["pct_hi"]) == (60.0, 80.0)        # the round-8 worked case, through the production adapter

    def test_unknown_in_the_containing_window_makes_the_timing_target_unqualified(self, tmp_path):
        reg = reg_one_exact(tmp_path)
        res = score_candidate(reg, ext(tmp_path, year_rows(unknown_a=True)))
        assert res["t_time"]["pass"] is None and res["t_time"]["status"] == "UNQUALIFIED"
        assert res["t_time"]["capped_median_range"] == [0, 182]
        assert res["t_time"]["unqualified_events"] == ["EVT.X.01"]
        assert res["t_cover"]["hits"] == 1                      # admission is untouched by qualification

    def test_known_target_gives_a_qualified_time(self, tmp_path):
        reg = reg_one_exact(tmp_path)
        res = score_candidate(reg, ext(tmp_path, year_rows(unknown_other=True)))
        assert res["t_time"]["status"] == "QUALIFIED" and res["t_time"]["pass"] is True     # |05-18 - 05-20| = 2 d
        assert res["t_time"]["capped_median_days"] == 2

    def test_budget_exceeded_is_unqualified_never_guessed(self, tmp_path):
        reg = reg_one_exact(tmp_path)
        rows = year_rows() + [row(f"2010-{m:02d}-20", f"2010-{m:02d}-21", f"2010-{m:02d}-20", None) for m in (2, 3, 9, 11)]
        res = score_candidate(reg, ext(tmp_path, rows), budget=50)
        pe = res["per_event"][0]
        assert pe["bounds_status"] == "BUDGET_EXCEEDED" and (pe["pct_lo"], pe["pct_hi"]) == (0.0, 100.0)
        assert res["unknown_competitors"]["budget_exceeded_events"] == ["EVT.X.01"]

    @pytest.mark.parametrize("seed", range(25))
    def test_any_concrete_assignment_lies_inside_the_bounds(self, tmp_path, seed):
        """Soundness: replace each unknown by an arbitrary concrete value; the concrete percentile / time must be in the range."""
        rng = random.Random(seed)
        reg = reg_one_exact(tmp_path)
        rows = [row("2010-04-01", "2010-07-01", "2010-05-18", None if rng.random() < .4 else rng.choice([0.0, .5, 1.0])),
                row("2010-08-01", "2010-08-10", "2010-08-05", rng.choice([None, 0.0, 0.5, 0.5 + 0.6e-9, 2.0])),
                row("2010-10-01", "2010-10-10", "2010-10-05", rng.choice([None, 0.0, 1.0])),
                row("2010-12-01", "2010-12-10", "2010-12-05", rng.choice([None, .5, 3.0]))]
        res = score_candidate(reg, ext(tmp_path, rows, f"u{seed}.json"))
        pe = res["per_event"][0]
        concrete = [{**r, "si": r["si"] if r["si"] is not None else rng.choice([0.0, 0.25, 0.5, 0.5 + 0.5e-9, 1.0, 7.5])}
                    for r in rows]
        cc = ext(tmp_path, concrete, f"c{seed}.json")
        b = event_bounds(reg.held[0], cc.merged, reg)
        assert pe["pct_lo"] - 1e-9 <= b["pct"] <= pe["pct_hi"] + 1e-9
        tt = score_candidate(reg, cc)["t_time"]["capped_median_days"]
        lo, hi = res["t_time"]["capped_median_range"]
        assert lo <= tt <= hi


class TestPlateau:
    def test_bridge_makes_the_verdict_unqualified(self, tmp_path):
        vals = [0.0, 0.0, 1.5e-9, 1.5e-9, 1.0, 2.0, 3.0, None]
        rows = [row(f"2010-{i + 1:02d}-01", f"2010-{i + 1:02d}-05", f"2010-{i + 1:02d}-02", v) for i, v in enumerate(vals)]
        c = ext(tmp_path, rows)
        assert plateau_verdict(CLS, 2010, c.merged) == "unqualified"

    def test_known_verdicts(self, tmp_path):
        c = ext(tmp_path, [row(f"2010-{i + 1:02d}-01", f"2010-{i + 1:02d}-05", f"2010-{i + 1:02d}-02", 0.5) for i in range(4)])
        assert plateau_verdict(CLS, 2010, c.merged) == "plateau"
        c = ext(tmp_path, [row(f"2010-{i + 1:02d}-01", f"2010-{i + 1:02d}-05", f"2010-{i + 1:02d}-02", 0.1 * (i + 1)) for i in range(4)])
        assert plateau_verdict(CLS, 2010, c.merged) == "diverse"

    def test_no_windows_is_diverse(self, tmp_path):
        assert plateau_verdict(CLS, 2010, {}) == "diverse"


class TestRankEligibilityWithUnknowns:
    """T-rank: a plateau verdict that is not invariant over the unknowns reduces eligibility — it never relaxes the floor."""

    def rows(self, last):
        vals = [0.0, 0.0, 1.5e-9, 1.5e-9, 1.0, 2.0, 3.0, last]
        return [row(f"2010-{i + 1:02d}-01", f"2010-{i + 1:02d}-10", f"2010-{i + 1:02d}-05", v) for i, v in enumerate(vals)]

    def test_non_invariant_plateau_makes_t_rank_unqualified(self, tmp_path):
        reg = reg_one_exact(tmp_path, "2010-05-05")
        res = score_candidate(reg, ext(tmp_path, self.rows(None)))
        assert res["t_rank"]["status"] == "UNQUALIFIED" and res["t_rank"]["pass"] is None
        assert res["t_rank"]["eligibility_unqualified"] == ["EVT.X.01"] and res["t_rank"]["eligible_definite"] == 0
        assert res["per_event"][0]["rank_status"] == "eligibility_unqualified"

    def test_the_same_set_with_a_known_value_is_eligible_and_valid(self, tmp_path):
        reg = reg_one_exact(tmp_path, "2010-05-05")
        res = score_candidate(reg, ext(tmp_path, self.rows(5.0), "k.json"))
        assert res["per_event"][0]["rank_status"] == "eligible" and res["t_rank"]["status"] == "VALID"

    def test_a_range_straddling_the_bar_is_unqualified_not_a_pass(self, tmp_path):
        reg = reg_one_exact(tmp_path, "2010-05-05")
        rows = [row(f"2010-{i + 1:02d}-01", f"2010-{i + 1:02d}-10", f"2010-{i + 1:02d}-05", v)
                for i, v in enumerate([0.9, 0.8, 0.05, 0.1, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, None, None])]
        res = score_candidate(reg, ext(tmp_path, rows))
        assert res["t_rank"]["status"] == "UNQUALIFIED" and res["t_rank"]["pass"] is None
        lo, hi = res["t_rank"]["median_range"]
        assert (lo, hi) == (pytest.approx(100 * 2 / 12), pytest.approx(100 * 4 / 12)) and lo <= 25 < hi


class TestFrozenTieGroupingIsAdjacentGap:
    def test_chain_divergence_from_the_target_anchored_rank_is_pinned(self, tmp_path):
        """metrics.event_hit anchors ties on the target value; the frozen addendum chains adjacent gaps. Disclosed, not hidden."""
        reg = reg_one_exact(tmp_path)
        rows = [row("2010-04-01", "2010-07-01", "2010-05-18", 0.0), row("2010-08-01", "2010-08-10", "2010-08-05", 0.75e-9),
                row("2010-10-01", "2010-10-10", "2010-10-05", 1.5e-9), row("2010-12-01", "2010-12-10", "2010-12-05", 5.0)]
        new = event_bounds(reg.held[0], ext(tmp_path, rows).merged, reg)
        old_merged = merge_windows(rows)
        _t, _n, old_pct = event_hit(reg.held[0], old_merged, reg)
        assert new["pct"] == pytest.approx(100 * ((2 + 3 + 4) / 3 - 1) / 4)       # one chained group at ranks 2-4
        assert old_pct == pytest.approx(100 * ((3 + 4) / 2 - 1) / 4)               # target-anchored: only 0 and 0.75e-9
        assert new["pct"] != old_pct


@needs_campaign
class TestReproduces30:
    """The detector that the adapter measures what the protocol says: the recorded '3.0' numbers, from the pinned extract."""

    @pytest.fixture(scope="class")
    def res(self):
        return score_candidate(load_registry(REGISTRY_V2_3), load_candidate_extract(EXTRACT_3_0, EXTRACT_3_0_PIN))

    @pytest.fixture(scope="class")
    def rec(self):
        return json.loads((CAMPAIGN_MEASUREMENT / "rerun_result_v2_3.json").read_text())

    def test_every_recorded_figure(self, res, rec):
        for k in ("t_cover", "t_fp", "t_fp_gain", "t_fp_overall", "degeneracy", "t_rank"):
            assert res[k] == rec[k], k
        for k in ("capped_median_days", "misses", "uncapped_hits", "n_exact", "bar_days", "pass"):
            assert res["t_time"][k] == rec["t_time"][k], k
        assert load_candidate_extract(EXTRACT_3_0, EXTRACT_3_0_PIN).dedup_table == rec["dedup_table"]
        assert res["t_time"]["status"] == "QUALIFIED" and res["unknown_competitors"]["unknown_rows"] == 0
        assert res["t_honesty"]["status"] == rec["t_honesty"]["status"] == "UNVERIFIABLE"

    def test_per_event_records_equal_the_recorded_file(self, res):
        rec = json.loads((CAMPAIGN_MEASUREMENT / "rerun_per_event_v2_3.json").read_text())
        keys = ("eid", "cls", "grain", "tier", "N", "hit", "pct", "rank_status")
        assert [{k: p.get(k) for k in keys} for p in res["per_event"]] == [{k: p.get(k) for k in keys} for p in rec]

    def test_headline_numbers(self, res):
        assert (res["t_cover"]["hits"], res["t_cover"]["total"]) == (32, 47)
        assert res["t_time"]["capped_median_days"] == 182 and res["t_rank"]["status"] == "VOID"

    def test_equals_the_existing_harness_on_the_same_extract(self, res):
        old = score_generation(load_registry(REGISTRY_V2_3), load_extract(EXTRACT_3_0, EXTRACT_3_0_PIN))
        assert res["t_cover"] == old["t_cover"] and res["t_rank"] == old["t_rank"] and res["t_fp"] == old["t_fp"]


@needs_campaign
class TestEquivalenceOnRandomKnownExtracts:
    """On any fully-known extract (no chains within tolerance) the new scorer equals the existing one — range collapses to a point."""

    @pytest.mark.parametrize("seed", range(8))
    def test_matches_score_generation(self, tmp_path, seed):
        from services.gochara_eval import CLASSES_27
        rng = random.Random(1000 + seed)
        reg = load_registry(REGISTRY_V2_3)
        rows = []
        for c in CLASSES_27:
            for _ in range(rng.randint(0, 25)):
                d0 = dt.date(1996, 1, 1) + dt.timedelta(days=rng.randrange(0, 11000))
                d1 = d0 + dt.timedelta(days=rng.randrange(0, 120))
                rows.append(row(d0.isoformat(), d1.isoformat(), (d0 + (d1 - d0) // 2).isoformat(),
                                rng.choice([0.0, 0.1, 0.25, 0.5, 0.9, 1.7, 3.0]), cls=c))
        p = write_json(tmp_path / "r.json", {"rows": rows})
        new = score_candidate(reg, load_candidate_extract(p))
        old = score_generation(reg, load_extract(p))
        assert new["t_cover"] == old["t_cover"] and new["t_fp"] == old["t_fp"] and new["t_fp_gain"] == old["t_fp_gain"]
        assert new["degeneracy"] == old["degeneracy"]
        for k in ("capped_median_days", "misses", "uncapped_hits", "pass"):
            assert new["t_time"][k] == old["t_time"][k], k
        assert {k: v for k, v in new["t_rank"].items() if k != "median_range"} == old["t_rank"]
        keys = ("eid", "N", "hit", "pct", "rank_status")
        assert [{k: p.get(k) for k in keys} for p in new["per_event"]] == [{k: p.get(k) for k in keys} for p in old["per_event"]]
