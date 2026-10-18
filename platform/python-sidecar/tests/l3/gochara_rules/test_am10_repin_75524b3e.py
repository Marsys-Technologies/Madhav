"""AM-10 rule 2(g), amended by J-4p: both readers accept one settled build.
Only the reviewed settlement licenses a singleton; unknown builds refuse.
"""
import importlib.util
import pathlib
import sys

import pytest

from services.gochara_grammar.dasha_data import DashaReadConflict
from services.gochara_kernel import inventory_verifier
from services.gochara_rules.permission import DASHA_READ_CONTRACT

_P = pathlib.Path(__file__).resolve().parents[3] / "scripts" / "kala_gochara_cutover" / "step06a_class_context.py"
_spec = importlib.util.spec_from_file_location("step06a_class_context_am10", _P)
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)
select_dasha_read_contract = _mod.select_dasha_read_contract

OLD, NEW = "1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb", "75524b3e-102a-43ec-8cee-3f57fee752c3"


def rows(build):
    return [{"system_id": "vimshottari", "build_id": build, "level_n": 1}]


@pytest.mark.parametrize("build", ["7377833e-5d3b-4e70-8bef-1318904f470e"])
def test_reader_and_verifier_accept_the_same_single_settled_build(build):
    from datetime import datetime, timezone
    a, b = datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 2, 1, tzinfo=timezone.utc)
    row = {"dasha_row_id": "11111111-1111-4111-8111-111111111111", "level_n": 1,
           "parent_row_id": None, "lord_graha": "Saturn", "start_iso": a, "end_iso": b,
           "build_id": build, "system_id": "vimshottari", "ayanamsha_id": "lahiri_chitrapaksha",
           "verification_pass_status": "two_pass_verified"}
    assert select_dasha_read_contract(DASHA_READ_CONTRACT["chart_id"], [row])["build_id"] == build
    assert inventory_verifier.check_dasha_population(
        [row], [row], chart_id=DASHA_READ_CONTRACT["chart_id"], horizon=(a, b),
        consumed_ids=[row["dasha_row_id"]]) == []


@pytest.mark.parametrize("builds", [[OLD, NEW], [NEW, None], [None], []])
def test_mixed_null_and_unsettled_populations_are_still_refused(builds):
    with pytest.raises(DashaReadConflict):
        select_dasha_read_contract(DASHA_READ_CONTRACT["chart_id"],
                                  [r for build in builds for r in rows(build)])


@pytest.mark.parametrize("build", [OLD, NEW, "22222222-2222-4222-8222-222222222222"])
def test_cutover_refuses_an_ungoverned_singleton(build):
    with pytest.raises(DashaReadConflict, match="settled_build_absent"):
        select_dasha_read_contract(DASHA_READ_CONTRACT["chart_id"], rows(build))
