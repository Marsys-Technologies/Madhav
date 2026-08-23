---
lane: F-141
stream: S6_ADHARA
stage: D (DIAGNOSE) — COMPLETE
author: ADHARA-LEAD (sonnet)
---

# F-141 — ka_kshetra asset_throughput: state='lit' beside a last_error that denies promotion

## 1. Live reproduction (this session, via `mcp__postgres__query`, read-only)

```sql
SELECT asset_id, state, rows_written, last_built_at, left(coalesce(last_error,''),240)
FROM asset_throughput
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND (asset_id='ka_kshetra' OR asset_id LIKE 'mi_%');
```

Confirmed exactly as claimed: `ka_kshetra` row has `state='lit'`, `rows_written=11069325`,
`last_error='orphan-watchdog: heartbeat went stale while a substep plan was in flight. 301
substep(s) committed and 8599775 data row(s) are present, but this route cannot prove the
plan finished, so the asset was NOT promoted to 'lit'. Re-run the build...'`. All 12 `mi_*`
rows for this chart carry `last_error=''`. REPRODUCES. Not ALREADY-FIXED.

Row-count cross-check also confirmed live:
`kala_field(8,599,775) + provenance(1,839,618) + windows(31,350) + salience(31,350) +
null(250) + insights(431) + timeline_spec(6) = 10,502,780` exactly, vs. `rows_written =
11,069,325` — an overstatement of 566,545, matching the corpus figure exactly.

## 2. Claim decomposition

- **C1** — the row is internally self-contradictory: `state='lit'` (implying earned,
  provable completion) sits beside a `last_error` whose own text says the opposite
  ("was NOT promoted to 'lit'").
- **C2** — `rows_written` overstates the actual present row count by 566,545.
- **C3 (non-claim, explicitly disclaimed by the corpus)** — the underlying field DATA is
  NOT claimed corrupt; `field_content_hash` is unchanged and still what `kala_now_get`
  serves. This finding is about the build-state signal's truthfulness, not data integrity.

## 3. Mechanism (file:line, read directly — this session traced it further than the
   corpus's own "DIAGNOSIS-INCOMPLETE on the exact write path")

`platform/src/app/api/cockpit/watchdog/route.ts` (SAMĀPTI B-WATCHDOG-LIT, the exact
"orphan-watchdog: heartbeat went stale..." string originates here, line ~288-291). Read the
full withheld-promotion branch (lines ~264-310): when this route finds a `state='building'`
row whose heartbeat went stale mid-substep-plan and cannot prove the plan finished, it
writes **`state = 'incomplete'`** (line 281) — never `'lit'` — alongside the same
`last_error` text this chart's row carries.

**This means the CURRENT code cannot have produced the row as it exists today.** The
current watchdog logic, run today, would set `state='incomplete'`, not `state='lit'`, for
exactly the last_error text stored. The row's `state='lit'` must have come from a different
write path than this one — either an older pre-fix version of this same route (before the
SAMĀPTI B-WATCHDOG-LIT correction that introduced the `'incomplete'` branch), or a manual
out-of-band UPDATE. `grep -r "orphan-watchdog"` across the whole repo (Python + SQL + shell)
finds this exact string ONLY in this one TypeScript file — there is no other code path,
current or otherwise findable in source, that generates this message. This is consistent
with (and independently corroborates, from the code side rather than the docs side)
`CURRENT_STATE_v1_0.md` v6.60's own account that `state='lit'` was set via a manual local
repair after an OOM, not earned through this route's own predicate.

**Sibling census:** the `'incomplete'` branch (lines 278-310) is the only place in this file
writing `last_error` alongside a non-`'lit'` state for a withheld promotion; the `trulyStuck`
branch (line ~312-324) writes `state='error'` with a different `last_error` text
("writer never reported back") and is not implicated. No other asset for this chart shows
the same pattern (query in §1) — this is a single stale row, not a systemic recurring
defect in the current code.

## 4. Blast radius / lease note

`platform/src/app/api/cockpit/watchdog/route.ts` is **outside S6's lease**
(`platform/python-sidecar/ga_writers/**`, `pipeline/orchestrator/writers/**`,
`platform/scripts/governance/**`, `00_ARCHITECTURE/**`) — and per this diagnosis, the file
does not need editing anyway; its current logic is already correct (it is the OLD state of
this route, or a manual repair, that produced the stale row, not a live bug in today's
code). The actual remediation is a **one-time data repair** on the single stale row (no code
change) plus, optionally, a **recurrence guard** — a governance check script asserting the
invariant `NOT (state='lit' AND last_error IS NOT NULL AND last_error != '')` across
`asset_throughput`, which legitimately belongs in S6's lease
(`platform/scripts/governance/**`) and would have caught this exact class of manual-repair
mistake.

**Not executed this session:** the live data repair itself. This chart (`482012f1`) is the
project's canonical production chart (CLAUDE.md §B), and correcting `state`/`last_error`/
`rows_written` on a live production row is a judgment call between two dispositions —
(a) restate `state='incomplete'` to match what `last_error` already says (the row admits it
cannot prove completion), or (b) if a rebuild can now cleanly re-verify and legitimately
promote it, re-run the build instead of hand-editing the row — and SP-1 ("choose the option
that discloses more") does not obviously pick one over the other without knowing whether a
clean rebuild is feasible/cheap. Flagging for Stage S / PRATINIDHI rather than picking one
unilaterally and writing to production data on a same-session judgment call, consistent with
the PAR-R-7 discipline this session was just corrected on for a lower-stakes decision.

## 5. PAR-R-9 addendum — both refused, rescoped to detector + disclosure

PRATINIDHI ruled (PAR-R-9, `LEDGER_PRATINIDHI.md`, `par/pratinidhi-ledger`, independently
verified this session by reading the ledger directly): **NEITHER (a) nor (b) — no DB write
authorized.** Two corrections to this diagnosis, both independently re-verified live this
session (read-only, `mcp__postgres__query`) rather than taken on the ruling's word:

1. **The overstatement is not 566,545 — it is 2,469,550**, when measured against the
   `last_error` text's own stated `8,599,775` present-row figure (`11,069,325 -
   8,599,775`), vs. this diagnosis's original figure (`11,069,325 - 10,502,780`, the full
   7-table sum, which is a different and also-real baseline). Both numbers are genuine;
   they measure against different baselines (last_error's self-report vs. the actual
   table-sum this session independently computed), and PRATINIDHI's point stands regardless
   of which is used: the row overstates in either framing, by a wide margin.
2. **It is not one row — it is five**, confirmed this session via direct SQL against
   `asset_throughput WHERE state IN ('lit','mature') AND last_error IS NOT NULL AND
   last_error <> ''`: `ka_kshetra`/482012f1 (this row) plus four global `chart_id IS NULL`
   service singletons — `bg_reference` (`KeyError: 0`), `bg_transit_rules` /
   `bg_transit_engine` (matching `ForeignKeyViolation` on key 133, same `last_built_at`
   second — likely one failed build event, not two independent ones), `bg_ghatana`
   (`NotNullViolation`) — all dated 2026-08-02/07, ~13 days before the `ka_kshetra` row.
   These are raw exception traces, not watchdog-authored prose — a different mechanism
   class from `ka_kshetra`'s row. Full disclosure with the live-queried rows:
   `evidence/F-141_pre_write.json`.

**Why both fixes this diagnosis implicitly left open are refused (full reasoning in
PAR-R-9):** (a) restate-`state` is foreclosed by plan §6.0 in terms ("green by ruling" is
explicitly named as the failure mode to avoid), is itself a §N.8 violation (a typed value
standing in for a computed one), and leaves the overstatement standing regardless of which
figure is used (SP-3, partial remediation). (b) rebuild is refused **now, not in
principle** — PRATINIDHI traced all three orchestrator promote paths
(`asset_runner.py:335`, `:517-518`, `:696`) and confirmed every one sets `last_error =
NULL`, extending this diagnosis's own finding (which only traced the watchdog route) to the
orchestrator's own promote paths too: **no known current code path can produce this row.**
The mechanism is genuinely untraced, not merely under-investigated, and a rebuild would
overwrite the only live specimen of a state class nobody has explained. It also only
addresses 1 of 5 rows (SP-3 again).

**Rescoped remediation (real work, SP-8's disclosure-only path, not a deferral):**
1. **Detector** — `platform/scripts/governance/ekv_controls.py`'s pre-existing `F-102`
   control already checked almost this exact invariant, but scoped to `state='lit'` only
   (missing `'mature'`) — widened this session to `state IN ('lit','mature')` per
   PAR-R-9's exact spec, verified live to still return count=5. **More important finding**:
   `ekv_controls.py` is referenced by zero files under `.github/workflows/` (verified via
   `grep -rl ekv_controls .github/workflows/`) — the detector function has existed in the
   codebase, but no automated pipeline has ever called it. That is the literal mechanism
   behind "nothing detects this today": not a missing function, a missing wire. Wiring it
   into CI is a SENTINEL/conductor-level call (workflow files are outside S6's
   `platform/scripts/governance/**` lease) — flagged, not done. PR:
   `par/s6-f141-lit-beside-error` → #1312.
2. **Honest disclosure** — `evidence/F-141_pre_write.json`, all 5 rows, preserve-don't-repair.
3. **Continued trace (budget-permitting, not exhaustive this session)** — read
   `asset_runner.py` lines ~575-660 (the D-1.6 no-op-completion / `zero_rows_is_complete`
   logic PRATINIDHI named as prime suspect for the four global singletons). Did not find an
   explicit, guaranteed `last_error = NULL` clear on that specific branch for the
   `chart_id IS NULL` / `zero_rows_is_complete` case — consistent with, but not proof of,
   the suspicion. **Not confirmed as the mechanism.** Genuinely open; next session/lane
   should trace this branch to its actual DB write (this diagnosis ran out of budget before
   locating the exact UPDATE statement this branch feeds into).
4. **Pre-write snapshot** — `evidence/F-141_pre_write.json` doubles as this; captured
   before any future write per PAR-R-9's explicit requirement.

**Expected close state:** PARKED-WITH-DETECTOR, not LIVE — per plan §9, an honest partial
close is the correct outcome here, not a gap to be papered over.
