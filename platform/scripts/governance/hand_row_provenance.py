"""hand_row_provenance.py — R15/R29 (NIKASHA_CHANGE_REGISTER_v2_0.md).

R15: the hand/machine rule — everything MEASURABLE belongs to the inspector (`asset_census.py`);
a hand-written row (opportunity, disposition, judgement) carries the census run id it was judged
against, so a later reviewer (or a staleness check) can tell which measurement a human judgement
responded to, and whether a newer census run has since re-measured the same criterion.

R29: the mechanical consequence — hand-written rows carry `census_run_id`.

The census's own `generated` field (`asset_census.measure()`'s caller sets
`dict(generated=dt.datetime.now().astimezone().isoformat(timespec="seconds"), ...)`) IS the
census_run_id this rule refers to — an ISO timestamp, already computed once per run, already
present in every census JSON output. No second identifier is invented; a hand row's
`census_run_id` is simply that value, copied at the time the judgement was written.

Enforcement scope (documented, not silently assumed): this wave cannot retroactively add
`census_run_id` to the ledger's 857 pre-existing rows without a second real write to
`asset_gaps.jsonl`, which this wave's hard constraint forbids (one authorized write only, already
spent on R80+R81). `missing_census_run_id()` therefore checks only rows timestamped at or after
`CUTOFF_TS` (this wave's own date) — exactly the same grandfather pattern the ledger's own
`_schema` doc already uses for `kind` ("Rows without `kind` are read as kind=gap
(pre-2026-09-26 rows)"). A row before the cutoff is exempt, not silently passed as compliant.

C2 (W3-1_REVIEW.md §10, gate review correction, 2026-09-28): the hand/machine discriminator
(`is_hand_written`/`is_machine_written`) reads `detector`, not `owner` — see `is_machine_written`'s
own docstring for the reviewer's demonstrated failure mode this replaces (a census-driven CLOSED/
RE-OPENED transition on a hand-owned gap_id used to misread as a hand row, because `emit_gaps`
deliberately carries the hand `owner` forward onto its own transition rows).
"""
from __future__ import annotations

CUTOFF_TS = "2026-09-29T00:00:00+05:30"  # the day AFTER this wave (2026-09-28) — R15/R29 bind
# from the next session forward, not against this wave's own R81 migration output. R81's 22
# hand-owned rows (11 content + 11 hand-side supersessions) carry `ts` values from this wave's own
# real-write timestamp (2026-09-28, this wave's date) — they are a one-time migration record, not
# a fresh hand judgement, and retroactively adding census_run_id to them would need a second real
# write this wave's hard constraint forbids (one authorized write only, already spent). Binding
# the cutoff to the day after this wave closes grandfathers them honestly instead of either
# silently exempting all of today (which would also grandfather a genuine new hand judgement
# written later today) or falsely flagging a one-time migration as a rule violation.


def is_machine_written(row: dict) -> bool:
    """C2 (W3-1_REVIEW.md §10, reviewer's demonstrated defect): whether THIS ROW was written by
    `asset_census.py`'s `emit_gaps()` — never the current `owner` field, which is not reliable for
    this. `emit_gaps` deliberately CARRIES the prior row's `owner`/`change`/`gate` forward onto its
    own CLOSED/RE-OPENED transition rows (D4; the whole point is that a hand annotation survives a
    machine transition). So a hand-owned gap_id's census-driven closure is a row the census wrote,
    still bearing the hand owner — `owner != "asset_census"` on that row is true, and the
    owner-only check the original R15/R29 landing used misread it as a hand row.

    `detector` is the reliable signal instead: every row `emit_gaps` ever writes — the gap_id's
    first OPEN row AND every later CLOSED/RE-OPENED transition — sets
    `detector=f"asset_census.py --layer {layer} ({criterion})"` itself (asset_census.py's
    `emit_gaps`), regardless of whose `owner` it carries forward. A hand-authored `detector` string
    (free text describing a probe or census a human ran) never begins with that literal prefix.
    """
    return str(row.get("detector") or "").startswith("asset_census.py")


def is_hand_written(row: dict) -> bool:
    """A row is hand-written iff THIS ROW was not written by the census itself (see
    `is_machine_written` for why that is not the same question as "is the row's current `owner`
    the census"). The T5_LEDGER_DRIFT.md §A discriminator (`owner`) identifies who a row's
    judgement belongs to, which is a different, and for this purpose insufficient, question from
    who wrote this specific line."""
    return not is_machine_written(row)


def is_judgemental_kind(row: dict) -> bool:
    """R15 names three hand-row kinds explicitly: opportunity, disposition, judgement. The
    ledger's own `kind` vocabulary today is only "gap" or "opportunity" (asset_gaps.jsonl
    `_schema`); a hand-written "gap" row is itself a disposition/judgement about a measurable
    finding (exactly the G-numbered rows R81 this wave re-keyed), so it is in scope too."""
    return row.get("kind") in ("gap", "opportunity")


def missing_census_run_id(rows: list[dict], cutoff_ts: str = CUTOFF_TS) -> list[str]:
    """Returns the gap_ids of every hand-written, judgemental row timestamped at or after
    `cutoff_ts` that carries no `census_run_id` — the mechanical check R29 is. A row's own `ts`
    missing entirely is treated as pre-cutoff (grandfathered), never as a violation by omission."""
    violations: list[str] = []
    for r in rows:
        if not is_hand_written(r) or not is_judgemental_kind(r):
            continue
        ts = r.get("ts") or ""
        if not ts or ts < cutoff_ts:
            continue  # grandfathered — absent or written before this rule bound
        if not r.get("census_run_id"):
            violations.append(r.get("gap_id", "<no gap_id>"))
    return violations
