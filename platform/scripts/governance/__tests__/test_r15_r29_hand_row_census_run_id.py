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
    assert hrp.is_hand_written({"owner": "bg_x brief", "detector": "the probe fails when down"})
    assert not hrp.is_hand_written({"owner": "asset_census", "detector": "asset_census.py --layer L0 (Foo.bar)"})
    assert hrp.is_judgemental_kind({"kind": "gap"})
    assert hrp.is_judgemental_kind({"kind": "opportunity"})
    assert not hrp.is_judgemental_kind({"kind": "something_else"})


# ── C2 (W3-1_REVIEW.md §10): the reviewer's demonstrated failure mode ──
#
# emit_gaps() CARRIES a prior row's `owner` forward onto its own CLOSED/RE-OPENED transition rows
# (by design — D4: a hand annotation survives a machine transition). R81 made five census-derived
# ids hand-owned (folding the hand row's owner onto the surviving, previously-census-owned id: e.g.
# bg_ontology-Dens.served now carries owner="layer packet"). From 2026-09-29, the first real census
# run that CLOSES or RE-OPENS one of those hand-owned ids appends a MACHINE-WRITTEN row that still
# reads owner="layer packet" — a row an owner-only check misreads as hand-written and (wrongly)
# expects to carry census_run_id.

def test_owner_only_discriminator_would_have_flagged_a_census_transition_on_a_hand_owned_id():
    """Reproduces the reviewer's exact scenario: bg_ontology-Dens.served starts as a hand-owned id
    (R81's fold carried the hand row's owner onto it), then a later census run CLOSES it. The
    resulting CLOSED row is machine-written (emit_gaps wrote it, detector says so) but still reads
    owner="layer packet" (carried forward, unchanged) — exactly emit_gaps's own documented
    contract. The FIXED discriminator (detector-based) must not flag it; the OLD one (owner-based,
    reproduced inline below as `_naive_owner_only_is_hand_written`, not `hrp`'s own function) would
    have."""
    rows = [
        # R81's fold: bg_ontology-Dens.served survives with the hand row's owner carried onto it.
        dict(asset="bg_ontology", gap_id="bg_ontology-Dens.served", kind="gap", criterion="Dens.served",
             what="folded", change="declare density_contract on resolve_entity and list_entities",
             detector="asset_census.py --layer L0 (Dens.served)", owner="layer packet",
             gate="W-L0-8", state="OPEN", ts="2026-09-28T03:12:00+05:30"),
        # A later (post-cutoff) census run closes it by measurement — machine-written, hand owner
        # carried forward unchanged, exactly as emit_gaps's own CLOSED-branch code does.
        dict(asset="bg_ontology", gap_id="bg_ontology-Dens.served", kind="gap", criterion="Dens.served",
             what="CLOSED by measurement: 2 module(s) now declare density_contract",
             change="declare density_contract on resolve_entity and list_entities",
             detector="asset_census.py --layer L0 (Dens.served)", owner="layer packet",
             gate="W-L0-8", state="CLOSED", ts=AFTER),
    ]

    def _naive_owner_only_is_hand_written(row):
        return row.get("owner") != "asset_census"

    naive_flags = [r.get("gap_id") for r in rows
                   if _naive_owner_only_is_hand_written(r) and hrp.is_judgemental_kind(r)
                   and (r.get("ts") or "") >= hrp.CUTOFF_TS and not r.get("census_run_id")]
    assert naive_flags == ["bg_ontology-Dens.served"], (
        "the naive owner-only check must reproduce the reviewer's false positive on this fixture"
    )

    assert hrp.missing_census_run_id(rows) == [], (
        "the fixed, detector-based discriminator must recognise the CLOSED row as machine-written "
        "and never flag it, even though its carried-forward owner is a hand owner"
    )


def test_real_ledger_has_zero_violations_today_every_row_predates_the_cutoff():
    """Packet-proof: the grandfather clause (CUTOFF_TS = the day after this wave) correctly exempts
    every one of the real ledger's 857 rows, including the 22 hand-owned rows R81's migration
    this wave produced (their `ts` carries this wave's own real-write timestamp, 2026-09-28) —
    confirming R15/R29 introduces no false-positive violation against this wave's own output."""
    with REAL_LEDGER.open(encoding="utf-8") as f:
        rows = [json.loads(ln) for ln in f if ln.strip()]
    violations = hrp.missing_census_run_id(rows)
    assert violations == [], f"unexpected violations against real production data: {violations}"
