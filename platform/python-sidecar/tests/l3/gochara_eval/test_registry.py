"""Registry validation tests (protocol v2.3 §1, §2, §9.2, §9.4)."""
from __future__ import annotations

import json

import pytest

from services.gochara_eval import load_registry
from services.gochara_eval.registry import RegistryError, WORKED_EVENT_DATES

from .conftest import (REGISTRY_V2_3, needs_campaign, synth_registry,
                       synth_registry_counts, write_json)


class TestClassUniverse:
    def test_unknown_class_is_input_rejected(self, tmp_path):
        doc = synth_registry()
        doc["events"][3]["class"] = "lottery_win"  # outside the §2 table
        path = write_json(tmp_path / "reg.json", doc)
        with pytest.raises(RegistryError, match="INPUT_REJECTED"):
            load_registry(path)

    def test_all_27_classes_accepted(self, tmp_path):
        from services.gochara_eval import CLASSES_27
        events = [
            {"eid": f"EVT.T{i:02d}", "tier": "dev", "obs_type": "point",
             "grain": "exact", "date": "2010-01-01", "class": c}
            for i, c in enumerate(CLASSES_27)
        ]
        counts = synth_registry_counts()
        counts.update({"logged_events": 27, "dev": 27, "held_out": 0,
                       "held_out_timing": 0, "held_out_year": 0, "excluded": 0,
                       "exact_cohort": 0})
        path = write_json(tmp_path / "reg.json", synth_registry(events, counts))
        reg = load_registry(path)
        assert len(reg.dev) == 27 and not reg.held


class TestTiers:
    def test_dev_rows_excluded_from_held_out(self, synth_registry_path):
        reg = load_registry(synth_registry_path)
        held_dates = {e.date_or_span for e in reg.held}
        # the three worked events are dev-tier and never scored as held-out
        for d in WORKED_EVENT_DATES:
            assert d not in held_dates
        assert {e.tier for e in reg.held} <= {"held_out_timing", "held_out_year"}
        assert len(reg.held) == 2
        assert len(reg.dev) == 3

    def test_worked_event_leaking_into_held_out_rejected(self, tmp_path):
        doc = synth_registry()
        doc["events"].append(
            {"eid": "EVT.2013.12.11.99", "tier": "held_out_timing",
             "obs_type": "point", "grain": "exact", "date": "2013-12-11",
             "class": "marriage"})
        counts = synth_registry_counts()
        counts.update({"logged_events": 7, "held_out": 3, "held_out_timing": 2,
                       "exact_cohort": 2, "t_rank_floor": 2})
        doc["conventions"]["counts"] = counts
        path = write_json(tmp_path / "reg.json", doc)
        with pytest.raises(RegistryError, match="worked/development"):
            load_registry(path)

    def test_excluded_and_annotation_never_scored(self, tmp_path):
        events = [
            {"eid": "E1", "tier": "excluded", "obs_type": "status",
             "grain": "exact", "date": "2024-01-01", "class": "chronic_onset"},
            {"eid": "A1", "tier": "annotation", "obs_type": "exacerbation",
             "grain": "month", "date": "2004-03", "class": "illness_acute"},
        ]
        counts = synth_registry_counts()
        counts.update({"logged_events": 2, "dev": 0, "held_out": 0,
                       "held_out_timing": 0, "held_out_year": 0,
                       "excluded": 1, "annotation_rows": 1,
                       "exact_cohort": 0})
        path = write_json(tmp_path / "reg.json", synth_registry(events, counts))
        reg = load_registry(path)
        assert not reg.held and len(reg.excluded) == 1 and len(reg.annotations) == 1


class TestSourceReconciliation:
    def test_header_count_mismatch_halts(self, tmp_path):
        doc = synth_registry()
        doc["conventions"]["counts"]["held_out"] = 99  # header lies
        path = write_json(tmp_path / "reg.json", doc)
        with pytest.raises(RegistryError, match="SOURCE-RECONCILIATION"):
            load_registry(path)


@needs_campaign
class TestRealRegistry:
    def test_v2_3_registry_validates(self):
        reg = load_registry(REGISTRY_V2_3)
        assert len(reg.held) == 47
        assert reg.n_timing_usable == 32
        assert reg.reconciliation["status"] == "MATCH"
        assert len(reg.dev) == 3 and len(reg.excluded) == 7
        assert len(reg.annotations) == 1

    def test_2007_08_interval_is_731_days(self):
        reg = load_registry(REGISTRY_V2_3)
        row = next(e for e in reg.held if e.eid == "EVT.2007.XX.XX.03")
        lo, hi = row.span()
        assert (hi - lo).days + 1 == 731  # 2008 is a leap year (protocol §3)
