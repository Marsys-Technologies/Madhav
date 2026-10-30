"""SUR-RB-39 (4). Full ruling: (1) masks-only reading rule for coverage, percentiles and D8; (2) the own chart's applicable unit set
defines the (b)/(c) coverage and donor eligibility; (3) p_dir averages only episodes with defined own and opposite
scores; (4) the q = 30% sanity check per testable family, with the q-curve on a shortfall."""

from __future__ import annotations

import numpy as np
import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer.core import FamilyContext, assemble, donor_sets, reading_coverage, run_donor_check, scorable_mask
from services.rulebook.scorer.footprint import unit_touch
from services.rulebook.scorer.model import ChartTimeline, Episode, MemberSpec, UnitSpec

from ._toy import BASE, month_window, runs_series

CAREER = "career_adv_change_entry"


def _unit(uid, groups, pol="promotive", tags=None):
    gs = tuple(tuple(MemberSpec(r, frozenset(tags or [C.GENERAL])) for r in g) for g in groups)
    return UnitSpec(uid, C.FAMILY_DASHA, pol, "cluster", gs)


# ── (4) sanity per testable family; the q-curve on a shortfall ─────────────────────────────────────────────
def test_4_sanity_is_required_for_each_testable_family_only():
    from services.rulebook.scorer_calib import harness as H

    assert H.sanity_ok({"dasha": 0.85, "transit": 0.5}, testable=["dasha"]) is True
    assert H.sanity_ok({"dasha": 0.85, "transit": 0.5}, testable=["dasha", "transit"]) is False
    assert H.sanity_ok({"dasha": 0.85}, testable=["dasha", "transit"]) is False  # a testable family not measured
    assert H.sanity_ok({}, testable=[]) is False


def test_4_a_shortfall_reports_the_q_curve_and_the_unit_test_status():
    from services.rulebook.scorer_calib import harness as H

    rep = H.sanity_report({"dasha": 0.6, "transit": 0.9}, testable=["dasha", "transit"],
                          q_curves={"dasha": {"0.1": 0.1, "0.2": 0.3, "0.3": 0.6, "0.4": 0.8}}, unit_tests={"passed": 187, "failed": 0})
    assert rep["ok"] is False and rep["freeze"] == "DO NOT FREEZE"
    assert set(rep["q_curve"]["dasha"]) == {"0.1", "0.2", "0.3", "0.4"} and rep["unit_tests"]["failed"] == 0
    assert "low power" in rep["reading"]
    rep2 = H.sanity_report({"dasha": 0.6}, testable=["dasha"], q_curves={"dasha": {"0.1": 0.0, "0.2": 0.0, "0.3": 0.6, "0.4": 0.9}}, unit_tests={"passed": 180, "failed": 3})
    assert "defect" in rep2["reading"]
