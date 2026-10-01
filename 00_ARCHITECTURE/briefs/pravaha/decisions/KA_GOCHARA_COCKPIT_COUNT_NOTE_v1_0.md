---
artifact: KA_GOCHARA_COCKPIT_COUNT_NOTE
version: "1.0"
status: "SUPERSEDED 2026-10-02 — steward reversed the ruling on Stream A's evidence (M20261001T231844-fc32): the registered ka_gochara writer writes windows_v2 '2.0'; the integrity check is vacuously true over an empty '4.0' scope; Clear never touches the writer's rows. Remedy: revert the 1091 registry pin by a new migration, re-apply it with the writer switch at D-FLIP. Do not rely on this note's conclusion."
date: 2026-10-01
author: Stream B (Śāstra), item B6.0 (steward M20261001T165421-141b; Suvarṇa's cockpit finding)
writes: "NONE — every production read below is read-only"
---

# ka_gochara cockpit count reads 0 — defect or correct pre-flip reading?

**Finding (Suvarṇa, relayed by the steward):** the cockpit shows `ka_gochara` = 0
because migration 1091 (#2731, WP10 step 5) repointed the registry row to
`kala_gochara_windows WHERE chart_id=$1 AND generation='4.0'` while the registered
`ka_gochara` writer still writes `kala_gochara_windows_v2` at `'2.0'`
(`pipeline/orchestrator/writers/ka_gochara.py:120` — `TABLE = "kala_gochara_windows_v2"`;
`services/w2g/materialize.py:106` — `GENERATION_V2 = "2.0"`): 87 writer rows vs 0
counted rows.

## What 1091 intended

WP10 step 5 of the `'4.0'` cutover (plan §9): repoint `count_sql`, the integrity
conjuncts (a)–(k) and the display `clear_tables` from the `'2.0'`/v2 surfaces to
`'4.0'` on `kala_gochara_windows`, *before* step 6 builds `'4.0'` and step 8 flips
authority — deliberately in that order ("reversed, the integrity conjuncts would
still be scoped to '2.0' while '4.0' rows existed, breaking conjunct (f)"). Its
header says so verbatim: **"EXPECTED AND BENIGN … between steps 5 and 6 cockpit
shows 0 for ka_gochara, because the count now asks about '4.0', which does not
exist yet."** Conjunct (j) pins only `target_table = count_sql`'s relation (both
`kala_gochara_windows` — holds in production); it does not pin the generation
literal to what the writer writes, so the row passes its own gate at 0.

## Read-only production counts (2026-10-01, chart `482012f1…871aa`)

| surface | generation | rows |
|---|---|---|
| `kala_gochara_windows` | `'3.0'` (serving authority — `kala_gochara_authority`, flipped back 2026-09-28T19:29Z, "F-0 safety reversal") | 914 |
| `kala_gochara_windows` | `'v1'` (sweep) | 16,297 |
| `kala_gochara_windows` | `'4.0'` | **0** |
| `kala_gochara_windows_v2` | `'2.0'` (the registered writer's output) | 87 |

`asset_registry.ka_gochara`: `target_table=kala_gochara_windows`,
`count_sql=… generation='4.0'`, `target_floor=83` (a build-gate floor, not a display).

## Defect or correct reading?

**The 0 itself is not the defect; the label it is pinned to is.** 1091 designed
the 0 as a *transient* between steps 5 and 6 of a tranche expected to complete.
The campaign since moved on without it: `'4.0'` was built, flipped, and reversed
as a live hazard, and **the `'4.0'` label is BURNED for this chart** (ADK-0027
§4 — "re-attempt under a new label"); the standing successor is **`'4.1'`**
(narrowed horizon, ADK-0028 sequence via Cloud Run after merge/deploy). A
`count_sql` pinned to `'4.0'` can therefore never go non-zero again: the
"transient" became permanent the day the label burned. Against CLAUDE.md §N.4
(count_sql must count what the writer writes) the row under-reads *by design
during a cutover* — but that design's precondition (a `'4.0'` build is coming)
no longer holds.

## Options

1. **Keep, and re-scope at the `'4.1'` tranche.** Accept 0 as the truthful
   reading ("no unburned `'4.x'` exists") until the A2.6 flip tranche, whose
   migration re-scopes `'4.0'`→`'4.1'` — one new migration, riding a tranche
   that already exists. Until then this note (and a cockpit/runbook pointer) is
   the disclosure that 0 ≠ "asset empty".
2. **Revert now by a NEW migration** (target_table, count_sql and conjuncts
   (a)–(k) back to the `'2.0'`/v2 surfaces the writer writes; re-repin at the
   `'4.1'` tranche). §N.4-strict today, but two protected-window migrations of
   churn, and it makes the cockpit claim the `'2.0'` residue (87 rows, itself
   slated for N-11 disposition) is the asset's current output — a worse untruth,
   and it re-opens the exact `target_table`≠writer-table mismatch 1091 existed
   to close.

## Recommendation

**Option 1 — keep.** The 0 is honest and self-disclosing once recorded; the
repair belongs to the `'4.1'` flip tranche (re-scope the generation literal in
`count_sql` and conjunct (k)'s `'4.%'` pattern stays correct as-is). Action
items: (a) this note linked from the cutover runbook at the step-5 gate so no
future reader files the 0 as a regression; (b) the `'4.1'` tranche packet must
list the count_sql re-scope as a named step, so the burned literal does not
survive a second generation.
