"""test_r81_ledger_overlap_fold.py — R81 (NIKASHA_CHANGE_REGISTER_v2_0.md, D4 ruling re-scope).

The 11 hand<->census overlap pairs measured in T5_LEDGER_DRIFT.md §A: each is folded per D4
(§D4, adopted 2026-09-27) — re-keyed to a registered criterion in derived `<asset>-<Gate>.<check>`
form (never a hand G-numbered id kept as survivor), hand `change`/`owner`/`gate` carried onto the
new row, the old id(s) superseded via `superseded_by` (append-only: a NEW line, nothing edited or
deleted). Group 8 (bg_panchanga) is the one partial overlap — its hand row is re-keyed to its own
criterion `Earn.service_state` and is never folded onto a timing id; its census siblings
(`Earn.build_record`, `Cost.baseline`) are untouched.

`fold_overlap_pairs()` never opens a file — it is a pure function over an in-memory list of
already-parsed rows, returning only the NEW rows to append. Every test here runs against synthetic
fixtures OR a scratch COPY of the real ledger (read via `pathlib`, never written back) — this file
never writes `00_ARCHITECTURE/control/asset_gaps.jsonl`. The real file's one authorized write
happens in a separate, isolated script/commit, proven against this same function first.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import ledger_r81_migration as mig  # noqa: E402
import _r81_pre_migration_fixture as fx  # noqa: E402

REAL_LEDGER = HERE.parents[3] / "00_ARCHITECTURE/control/asset_gaps.jsonl"
TS = "2026-09-28T00:00:00+05:30"


def _hand(gid, crit, what="hand finding", change="hand change", owner="layer packet",
          gate="this asset's certification", state="OPEN"):
    return dict(asset=gid.split("-", 1)[0], gap_id=gid, kind="gap", criterion=crit, what=what,
                change=change, detector="hand detector", owner=owner, gate=gate, state=state, ts="t0")


def _census(gid, crit, what="census finding"):
    asset = gid.split("-", 1)[0]
    return dict(asset=asset, gap_id=gid, kind="gap", criterion=crit, what=what, change="",
                detector=f"asset_census.py --layer L0 ({crit})", owner="asset_census",
                gate="this asset's certification", state="OPEN", ts="t1")


# ── synthetic, minimal fixture covering one "same criterion" pair and one "distinct" pair ──

def _synthetic_rows():
    return [
        _hand("bg_ontology-G02", "Earn.build_record", what="hand: rows_written=0 vs 741 live"),
        _census("bg_ontology-Earn.build_record", "Earn.build_record", what="census: rps=NULL"),
        _hand("bg_ontology-G05", "Carr.D1", what="hand: no D1 detector, 741/741 cited"),
        _census("bg_ontology-Carr.detector", "Carr.detector", what="census: no D1/D2/D3 detector"),
    ]


def test_same_criterion_pair_preserves_the_census_derived_id_and_folds_the_hand_detail(monkeypatch):
    monkeypatch.setattr(mig, "OVERLAP_PAIRS", [
        dict(n=1, asset="bg_ontology", criterion="Earn.build_record",
             hand_old_id="bg_ontology-G02", census_old_id="bg_ontology-Earn.build_record",
             winner_is_census_id=True),
    ])
    new = mig.fold_overlap_pairs(_synthetic_rows(), TS)
    by_id = {r["gap_id"]: r for r in new if r["gap_id"] != "bg_ontology-Carr.detector"}
    assert len(new) == 2  # one enriched winner row + one superseded hand row
    winner = by_id["bg_ontology-Earn.build_record"]
    assert "superseded_by" not in winner
    assert "hand: rows_written=0 vs 741 live" in winner["what"]
    assert "census: rps=NULL" in winner["what"]
    assert winner["change"] == "hand change"  # carried from the hand row, not the census default
    loser = by_id["bg_ontology-G02"]
    assert loser["superseded_by"] == "bg_ontology-Earn.build_record"


def test_distinct_criterion_pair_mints_a_new_id_and_supersedes_both_old_ones(monkeypatch):
    monkeypatch.setattr(mig, "OVERLAP_PAIRS", [
        dict(n=4, asset="bg_ontology", criterion="Carr.D1",
             hand_old_id="bg_ontology-G05", census_old_id="bg_ontology-Carr.detector",
             winner_is_census_id=False),
    ])
    rows = _synthetic_rows()
    new = mig.fold_overlap_pairs(rows, TS)
    assert len(new) == 3  # one new winner row + two superseded (hand + census)
    d1_rows = new
    winner = next(r for r in d1_rows if r["gap_id"] == "bg_ontology-Carr.D1")
    assert winner["criterion"] == "Carr.D1"
    assert "superseded_by" not in winner
    hand_loser = next(r for r in d1_rows if r["gap_id"] == "bg_ontology-G05")
    census_loser = next(r for r in d1_rows if r["gap_id"] == "bg_ontology-Carr.detector")
    assert hand_loser["superseded_by"] == "bg_ontology-Carr.D1"
    assert census_loser["superseded_by"] == "bg_ontology-Carr.D1"


def test_partial_overlap_group_8_never_folds_onto_a_timing_id(monkeypatch):
    monkeypatch.setattr(mig, "OVERLAP_PAIRS", [
        dict(n=8, asset="bg_panchanga", criterion="Earn.service_state",
             hand_old_id="bg_panchanga-G01", census_old_id=None,
             winner_is_census_id=False),
    ])
    rows = [
        _hand("bg_panchanga-G01", "Earn.service_state", what="hand: no liveness signal"),
        _census("bg_panchanga-Earn.build_record", "Earn.build_record", what="census: rps=NULL"),
        _census("bg_panchanga-Cost.baseline", "Cost.baseline", what="census: rps=-"),
    ]
    new = mig.fold_overlap_pairs(rows, TS)
    assert len(new) == 2  # the re-keyed winner + the superseded G01 — nothing else touched
    ids_touched = {r["gap_id"] for r in new}
    assert ids_touched == {"bg_panchanga-Earn.service_state", "bg_panchanga-G01"}
    winner = next(r for r in new if r["gap_id"] == "bg_panchanga-Earn.service_state")
    assert winner["what"] == "hand: no liveness signal"  # nothing folded in — partial overlap
    assert "superseded_by" not in winner


def test_idempotent_a_second_run_on_the_first_runs_own_output_appends_nothing(monkeypatch):
    monkeypatch.setattr(mig, "OVERLAP_PAIRS", [
        dict(n=1, asset="bg_ontology", criterion="Earn.build_record",
             hand_old_id="bg_ontology-G02", census_old_id="bg_ontology-Earn.build_record",
             winner_is_census_id=True),
        dict(n=4, asset="bg_ontology", criterion="Carr.D1",
             hand_old_id="bg_ontology-G05", census_old_id="bg_ontology-Carr.detector",
             winner_is_census_id=False),
    ])
    rows = _synthetic_rows()
    first = mig.fold_overlap_pairs(rows, TS)
    second = mig.fold_overlap_pairs(rows + first, "2026-09-28T00:00:01+05:30")
    assert second == []


def test_missing_hand_row_raises_rather_than_silently_skipping(monkeypatch):
    import pytest
    monkeypatch.setattr(mig, "OVERLAP_PAIRS", [
        dict(n=1, asset="bg_ontology", criterion="Earn.build_record",
             hand_old_id="bg_ontology-G02", census_old_id="bg_ontology-Earn.build_record",
             winner_is_census_id=True),
    ])
    with pytest.raises(KeyError):
        mig.fold_overlap_pairs([_census("bg_ontology-Earn.build_record", "Earn.build_record")], TS)


# ── the FROZEN pre-migration fixture: proves the migration's real shape (27 rows: 11 content + ──
# ── 16 superseding) against the actual 11 pairs' actual pre-migration content, independent of ──
# ── the real ledger's current (now post-migration) state — see _r81_pre_migration_fixture.py ──

def test_frozen_fixture_migration_produces_27_new_rows_11_content_plus_16_supersessions():
    new = mig.fold_overlap_pairs(list(fx.ROWS), TS)
    assert len(new) == 27
    content_rows = [r for r in new if "superseded_by" not in r]
    superseding_rows = [r for r in new if "superseded_by" in r]
    assert len(content_rows) == 11
    assert len(superseding_rows) == 16


def test_frozen_fixture_migration_is_idempotent():
    rows = list(fx.ROWS)
    first = mig.fold_overlap_pairs(rows, TS)
    second = mig.fold_overlap_pairs(rows + first, "2026-09-28T00:00:01+05:30")
    assert second == []


def test_frozen_fixture_migration_leaves_zero_duplicate_live_identities_among_touched_ids():
    """Packet proof #2: a ledger scan finds zero (asset, criterion) identities with more than one
    live row among every id this migration ever touches."""
    rows = list(fx.ROWS)
    migrated = rows + mig.fold_overlap_pairs(rows, TS)
    latest, ever = mig._latest_and_superseded(migrated)
    touched = set()
    for p in mig.OVERLAP_PAIRS:
        touched.add(p["hand_old_id"])
        if p["census_old_id"]:
            touched.add(p["census_old_id"])
        touched.add(mig._gap_id_for(p["asset"], p["criterion"]))
    seen: dict[tuple, list[str]] = {}
    for gid in touched:
        if gid in ever:
            continue
        row = latest.get(gid)
        if row is None:
            continue
        key = (row["asset"], row["criterion"])
        seen.setdefault(key, []).append(gid)
    dupes = {k: v for k, v in seen.items() if len(v) > 1}
    assert dupes == {}, dupes


def test_frozen_fixture_migration_never_mutates_or_deletes_an_existing_line():
    rows = list(fx.ROWS)
    before = [json.dumps(r, sort_keys=True) for r in rows]
    mig.fold_overlap_pairs(rows, TS)
    after = [json.dumps(r, sort_keys=True) for r in rows]
    assert before == after, "fold_overlap_pairs must never mutate the rows list it is given"


# ── the REAL ledger, read-only, post-migration: confirms the one authorized real write (commit ──
# ── "Nikaṣa wave3 R80+R81: the one authorized real write to asset_gaps.jsonl this wave makes") ──
# ── actually left the ledger in the state R81 requires, and stays idempotent from here on ──

def _real_rows():
    with REAL_LEDGER.open(encoding="utf-8") as f:
        return [json.loads(ln) for ln in f if ln.strip()]


def test_real_ledger_all_11_pairs_old_ids_are_now_superseded():
    """Every old id this migration folds AWAY must be superseded — the hand id always, and the
    census id too EXCEPT for the 5 pairs where the census id was itself already the winning,
    derived-form id (it is enriched in place, not superseded onto itself)."""
    rows = _real_rows()
    _, ever = mig._latest_and_superseded(rows)
    expected_superseded = set()
    for p in mig.OVERLAP_PAIRS:
        final_id = p["census_old_id"] if p["winner_is_census_id"] else mig._gap_id_for(p["asset"], p["criterion"])
        if p["hand_old_id"] != final_id:
            expected_superseded.add(p["hand_old_id"])
        if p["census_old_id"] and p["census_old_id"] != final_id:
            expected_superseded.add(p["census_old_id"])
    missing = expected_superseded - ever
    assert not missing, f"still not superseded in the real ledger: {missing}"


def test_real_ledger_bg_panchanga_partial_overlap_left_its_census_siblings_untouched():
    """Group 8's own rule: bg_panchanga-Earn.build_record and bg_panchanga-Cost.baseline must NOT
    be superseded — only bg_panchanga-G01 was re-keyed."""
    rows = _real_rows()
    _, ever = mig._latest_and_superseded(rows)
    assert "bg_panchanga-Earn.build_record" not in ever
    assert "bg_panchanga-Cost.baseline" not in ever
    assert "bg_panchanga-G01" in ever


def test_real_ledger_migration_is_now_a_confirmed_no_op():
    """The real ledger already carries R81's fold (this wave's one authorized write) — running
    the same function against it today must find nothing left to do."""
    rows = _real_rows()
    new = mig.fold_overlap_pairs(rows, TS)
    assert new == []


def test_real_ledger_schema_row_documents_superseded_by():
    rows = _real_rows()
    assert "superseded_by" in rows[0]["_doc"]
    assert rows[0]["asset"] == "_schema"
