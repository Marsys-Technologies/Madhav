"""test_r15_r29_hand_row_census_run_id.py — R15 + R29 (NIKASHA_CHANGE_REGISTER_v2_0.md).

R15: the hand/machine rule — everything measurable belongs to the inspector (asset_census.py); a
hand-written row (opportunity, disposition, judgement) carries the census run id it was judged
against. R29: the mechanical consequence — hand-written rows carry `census_run_id`.

`missing_census_run_id()` is the enforcement half, scoped going forward from this wave's own date
(CUTOFF_TS) since retroactively adding the field to the ledger's 857 pre-existing rows would need
a second real write this wave's hard constraint forbids (one authorized write only).

Fails without the fix: the module does not exist / does not flag a post-cutoff hand row missing
the field, or wrongly flags a pre-cutoff (grandfathered) or machine-written one.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import hand_row_provenance as hrp  # noqa: E402

REAL_LEDGER = HERE.parents[3] / "00_ARCHITECTURE/control/asset_gaps.jsonl"

BEFORE = "2026-09-28T00:00:00+05:30"  # this wave's own date — grandfathered (R81's migration output)
AFTER = "2026-09-30T00:00:00+05:30"   # the day after CUTOFF_TS — a genuinely new hand judgement


def _hand(gid, ts, kind="gap", census_run_id=None, owner="bg_x brief"):
    row = dict(asset=gid.split("-", 1)[0], gap_id=gid, kind=kind, criterion="Foo.bar",
               what="w", change="c", detector="d", owner=owner,
               gate="this asset's certification", state="OPEN", ts=ts)
    if census_run_id:
        row["census_run_id"] = census_run_id
    return row


def _census(gid, ts):
    return dict(asset=gid.split("-", 1)[0], gap_id=gid, kind="gap", criterion="Foo.bar",
                what="w", change="", detector="asset_census.py --layer L0 (Foo.bar)",
                owner="asset_census", gate="this asset's certification", state="OPEN", ts=ts)


def test_pre_cutoff_hand_row_missing_census_run_id_is_grandfathered_not_a_violation():
    rows = [_hand("bg_x-G01", BEFORE)]
    assert hrp.missing_census_run_id(rows) == []


def test_post_cutoff_hand_row_missing_census_run_id_is_a_violation():
    rows = [_hand("bg_x-G02", AFTER)]
    assert hrp.missing_census_run_id(rows) == ["bg_x-G02"]


def test_post_cutoff_hand_row_carrying_census_run_id_is_not_a_violation():
    rows = [_hand("bg_x-G03", AFTER, census_run_id="2026-09-28T12:00:00+05:30")]
    assert hrp.missing_census_run_id(rows) == []


def test_machine_written_row_is_never_a_violation_regardless_of_timestamp():
    rows = [_census("bg_x-Foo.bar", AFTER)]
    assert hrp.missing_census_run_id(rows) == []


def test_opportunity_kind_is_in_scope_gap_kind_is_in_scope_other_kinds_are_not():
    rows = [
        _hand("bg_x-O1", AFTER, kind="opportunity"),
        _hand("bg_x-G04", AFTER, kind="gap"),
        _hand("bg_x-BT01", AFTER, kind="something_else"),
    ]
    assert sorted(hrp.missing_census_run_id(rows)) == ["bg_x-G04", "bg_x-O1"]


def test_row_with_no_ts_at_all_is_grandfathered_not_flagged_by_omission():
    rows = [dict(asset="bg_x", gap_id="bg_x-G05", kind="gap", criterion="Foo.bar", what="w",
                 change="", detector="d", owner="bg_x brief", gate="this asset's certification",
                 state="OPEN")]
    assert hrp.missing_census_run_id(rows) == []


def test_is_hand_written_and_is_judgemental_kind_helpers():
    assert hrp.is_hand_written({"owner": "bg_x brief"})
    assert not hrp.is_hand_written({"owner": "asset_census"})
    assert hrp.is_judgemental_kind({"kind": "gap"})
    assert hrp.is_judgemental_kind({"kind": "opportunity"})
    assert not hrp.is_judgemental_kind({"kind": "something_else"})


def test_real_ledger_has_zero_violations_today_every_row_predates_the_cutoff():
    """Packet-proof: the grandfather clause (CUTOFF_TS = the day after this wave) correctly exempts
    every one of the real ledger's 857 rows, including the 22 hand-owned rows R81's migration
    this wave produced (their `ts` carries this wave's own real-write timestamp, 2026-09-28) —
    confirming R15/R29 introduces no false-positive violation against this wave's own output."""
    with REAL_LEDGER.open(encoding="utf-8") as f:
        rows = [json.loads(ln) for ln in f if ln.strip()]
    violations = hrp.missing_census_run_id(rows)
    assert violations == [], f"unexpected violations against real production data: {violations}"
