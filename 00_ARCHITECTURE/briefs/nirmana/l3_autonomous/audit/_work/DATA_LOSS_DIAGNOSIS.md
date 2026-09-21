# Data-Loss Diagnosis: `kala_activation` / `kala_convergence` at 0 rows for the canonical chart

**Status:** ROOT CAUSE IDENTIFIED, with high-confidence corroborating evidence across all three
charts that currently hold (or once held) `kala_*` signal-linked data. Read-only forensics only —
no DML was executed, no build was dispatched.

**Chart under investigation:** `482012f1-710e-4a25-994a-93821f5871aa` (canonical, Abhisek Mohanty).

---

## 1. Summary verdict

The tables were **not deleted by a bug in `ka_kalasutra` / `ka_sangam`'s own delete-then-insert
scoping**, and **not deleted by a migration, TRUNCATE, or manual purge**. They were emptied by a
**foreign-key `ON DELETE CASCADE` from `kala_activation.signal_id` / `kala_convergence.signal_id`
to `bodha_msr_signals.signal_id`**, deliberately introduced in
`platform/supabase/migrations/403_kala_signal_fk_cascade.sql`. Every time the upstream L2 Bodha
writer (`bo_laksana` / `bo_laksana_rerank`) performs its own per-chart delete-then-insert rebuild
(per `CLAUDE.md` §N.3, which mints **fresh `signal_id` UUIDs on every rebuild** — confirmed via the
`bodha_msr_signals.build_id` column), any `kala_activation` / `kala_convergence` row still pointing
at an now-deleted old `signal_id` is **silently cascade-deleted**, regardless of whether the L3
`ka_kalasutra` / `ka_sangam` writers have ever been re-run.

For the canonical chart, `bo_laksana` rebuilt on **2026-09-08 18:22 UTC** and `bo_laksana_rerank` on
**2026-09-11 15:41 UTC** — both **after** `ka_kalasutra` (2026-08-13 01:15 UTC) and `ka_sangam`
(2026-08-13 01:07 UTC) last ran. Every `bodha_msr_signals` row currently on file for this chart is
dated 2026-09-08 → 2026-09-11 (100% turnover of the signal set) — none of the signal_ids the
2026-08-13 `kala_*` rows referenced still exist, so the cascade removed all of them. This is fully
reproducible logic, not a one-off accident, and **it will recur** for any chart whenever L2 Bodha
rebuilds MSR signals after an L3 Kāla build, unless L3 is rebuilt in lockstep immediately afterward
— which nothing in the orchestrator currently enforces.

---

## 2. What `asset_throughput` actually is (correcting a framing assumption in the task)

```sql
\d asset_throughput
-- Indexes:
--   "asset_throughput_per_chart_idx" UNIQUE, btree (chart_id, asset_id) WHERE chart_id IS NOT NULL
```

`asset_throughput` carries a **UNIQUE constraint on `(chart_id, asset_id)`**. It is an **upsert
table, not an append-only log** — there is exactly **one row per (chart, asset) pair**, continually
overwritten in place. So "query ALL rows ordered by time" (hypothesis 1/5 in the task brief)
doesn't literally apply: there is only ever one row to find, and it already **is** the latest state.

```sql
source /Users/Dev/madhav-l3/dbenv.sh
CHART_ID="482012f1-710e-4a25-994a-93821f5871aa"
SELECT asset_id, chart_id, state, rows_written, last_error, last_built_at
FROM asset_throughput
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND asset_id IN ('ka_kalasutra','ka_sangam');
```
Result:
| asset_id | state | rows_written | last_built_at | last_error |
|---|---|---|---|---|
| ka_sangam | stale | 14868 | 2026-08-13 01:07:13.494312+00 | (null) |
| ka_kalasutra | stale | 335403 | 2026-08-13 01:15:50.567754+00 | (null) |

No global (`chart_id IS NULL`) row exists for either asset either — confirmed:
```sql
SELECT asset_id, chart_id, state, rows_written, last_error, last_built_at
FROM asset_throughput WHERE chart_id IS NULL AND asset_id IN ('ka_kalasutra','ka_sangam');
-- (0 rows)
```

**This one fact alone already rules out hypothesis 1 and hypothesis 4** (a later run of these
writers, successful or failed, for this chart): if either writer had run again — even a run that
wrote 0 rows, or errored — `rows_written`/`last_built_at`/`last_error` would show it, and they don't.
The writer's own row is frozen exactly at its 2026-08-13 success.

### 2.1 There IS a real audit trail — `asset_throughput_state_audit`

`asset_throughput` has a trigger (`trg_asset_throughput_state_audit`) that logs every `state`
transition to a genuine append-only table:

```sql
\sf _record_asset_throughput_state_change
-- INSERT INTO asset_throughput_state_audit
--   (chart_id, asset_id, old_state, new_state, db_user, application_name, triggered_by, changed_at)
```

```sql
SELECT chart_id, asset_id, old_state, new_state, triggered_by, changed_at
FROM asset_throughput_state_audit
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND asset_id IN ('ka_kalasutra','ka_sangam')
ORDER BY changed_at ASC;
```
Result — **exactly one transition each, at the identical millisecond**:
| chart_id | asset_id | old_state | new_state | triggered_by | changed_at |
|---|---|---|---|---|---|
| 482012f1… | ka_sangam | lit | stale | asset_runner | 2026-09-04 19:42:09.672448+00 |
| 482012f1… | ka_kalasutra | lit | stale | asset_runner | 2026-09-04 19:42:09.672448+00 |

Both assets flipped `lit → stale` **simultaneously** on 2026-09-04, driven by `asset_runner` — this
is the orchestrator's normal "upstream hash changed, mark downstream stale" staleness-cascade
mechanism, correctly detecting that something upstream had (or was about to be) rebuilt. It is **not**
itself a data-deleting event (staleness is just a flag) and it **predates** the actual signal-cascade
delete described below by several days — see §5 for the residual gap this leaves.

No further audit rows exist for these two (chart, asset) pairs — confirming, independently of
`rows_written`, that neither writer has run since 2026-08-13.

---

## 3. Ruling out a rogue/mis-scoped DELETE from another chart (hypothesis 2)

```sql
SELECT chart_id, asset_id, state, rows_written, last_built_at, last_error
FROM asset_throughput WHERE asset_id IN ('ka_kalasutra','ka_sangam')
ORDER BY last_built_at DESC NULLS LAST;
```
All charts that have ever built these two assets:
| chart_id | asset_id | state | rows_written | last_built_at |
|---|---|---|---|---|
| 482012f1… (**canonical, target**) | ka_kalasutra | stale | 335403 | 2026-08-13 01:15 |
| 482012f1… | ka_sangam | stale | 14868 | 2026-08-13 01:07 |
| 1c826d5a… (Abhinandan) | ka_kalasutra | stale | 336093 | 2026-08-12 17:09 |
| 1c826d5a… | ka_sangam | stale | 17957 | 2026-08-12 16:58 |
| cb73cd3d… | ka_kalasutra | stale | 335447 | 2026-07-27 14:20 |
| cb73cd3d… | ka_sangam | stale | 32845 | 2026-07-27 14:13 |

Current actual row counts in the two tables, by chart:
```sql
SELECT chart_id, count(*) FROM kala_activation GROUP BY chart_id;
--  1c826d5a… | 336093   (matches rows_written EXACTLY)
--  cb73cd3d… |   1,055  (vs rows_written 335,447 — mostly gone)
--  482012f1… |  (absent — 0 rows)              <- our target
SELECT chart_id, count(*) FROM kala_convergence GROUP BY chart_id;
--  1c826d5a… | 17,957   (matches rows_written EXACTLY)
--  cb73cd3d… |  2,540   (vs rows_written 32,845 — mostly gone)
--  482012f1… |  (absent — 0 rows)
```

If this were a chart-scoping bug in someone else's DELETE, we would expect the damage pattern to
correlate with *build order across charts*, not with each chart's *own* upstream-vs-downstream
timing. That is exactly what we found instead (§4) — **1c826d5a is completely untouched**, which
rules out a global/mis-scoped DELETE hitting all charts, or a delete triggered by *one specific
other chart's* build (that chart's own data would be equally exposed to whatever bug fired, and
it wasn't). The pattern is per-chart-correct; it just crosses a **layer boundary** (L2 → L3) rather
than a chart boundary.

---

## 4. The mechanism, proven with data: MSR signal-rebuild → FK CASCADE

### 4.1 The FK is real, deliberate, and CASCADE

```sql
SELECT conname, confdeltype FROM pg_constraint
WHERE conname IN ('kala_activation_signal_id_fkey','kala_convergence_signal_id_fkey',
                   'kala_activation_chart_id_fkey','kala_convergence_chart_id_fkey',
                   'asset_throughput_chart_id_fkey');
```
| conname | confdeltype |
|---|---|
| asset_throughput_chart_id_fkey | a (NO ACTION) |
| kala_activation_chart_id_fkey | c (CASCADE) |
| kala_convergence_chart_id_fkey | c (CASCADE) |
| kala_activation_signal_id_fkey | c (CASCADE) |
| kala_convergence_signal_id_fkey | c (CASCADE) |

(`asset_throughput`'s FK to `charts(id)` is plain NO ACTION/RESTRICT — this rules out a
delete-and-recreate of the `charts` row itself as the mechanism, since that would have required
`asset_throughput`'s own row for this chart to be deleted first, and it wasn't.)

The CASCADE was **deliberately added**, not inherited by accident:

```
platform/supabase/migrations/403_kala_signal_fk_cascade.sql
-- Migration 403: kala_* signal_id FKs → ON DELETE CASCADE
--
-- Five kāla tables reference bodha_msr_signals.signal_id (currently CASCADE or
-- SET NULL in prod). Standardising all to ON DELETE CASCADE so kāla rebuild
-- regenerates cleanly from fresh bodha data.
```
(applies to `kala_activation`, `kala_bhavishya`, `kala_convergence`, `kala_darshana`,
`kala_obstruction` — all five, not just the two under audit here.)

The migration's own comment states the design assumption plainly: *"kāla rebuild regenerates
cleanly from fresh bodha data"* — i.e. it assumed L3 would always be rebuilt again shortly after any
L2 signal rebuild. **Nothing actually enforces that lockstep coupling.** The 2026-09-04 staleness
flag (§2.1) is the only signal that fires, and it is passive — nothing currently treats
`state='stale' AND rows_written(current) = 0` as build-fatal or alerts on it.

### 4.2 `bodha_msr_signals` mints fresh `signal_id`s every rebuild (per CLAUDE §N.3)

```sql
SELECT chart_id, count(*), min(computed_at), max(computed_at)
FROM bodha_msr_signals
WHERE chart_id IN ('482012f1-710e-4a25-994a-93821f5871aa',
                    '1c826d5a-41cb-4450-b4dc-59d440e5f75a',
                    'cb73cd3d-9eba-4220-9902-0de91566e980')
GROUP BY chart_id;
```
| chart_id | count | min(computed_at) | max(computed_at) |
|---|---|---|---|
| 1c826d5a… (Abhinandan) | 50,171 | 2026-07-26 07:31 | 2026-08-12 16:27 |
| **482012f1… (canonical, target)** | 50,678 | **2026-09-08 18:20** | **2026-09-11 12:09** |
| cb73cd3d… | 49,875 | 2026-07-27 11:34 | 2026-08-07 14:55 |

For the canonical chart: **every single `bodha_msr_signals` row on file today postdates
`ka_kalasutra`/`ka_sangam`'s 2026-08-13 build by nearly a month.** None of the old signal_ids that
the 2026-08-13 `kala_activation`/`kala_convergence` rows referenced still exist — 100% turnover —
so the CASCADE removed 100% of the `kala_*` rows. This lines up exactly with `bo_laksana`'s own
`asset_throughput` row for this chart (`last_built_at = 2026-09-08 18:22:33`) and
`bo_laksana_rerank`'s (`last_built_at = 2026-09-11 15:41:00`) — both confirmed rebuilds, both after
2026-08-13:

```sql
SELECT chart_id, asset_id, state, rows_written, last_built_at
FROM asset_throughput WHERE asset_id ILIKE '%laksana%' ORDER BY chart_id, last_built_at DESC;
```
| chart_id | asset_id | last_built_at |
|---|---|---|
| 1c826d5a… | bo_laksana_rerank | 2026-08-12 16:47 |
| 1c826d5a… | bo_laksana | 2026-08-07 14:40 |
| **482012f1…** | **bo_laksana_rerank** | **2026-09-11 15:41** |
| **482012f1…** | **bo_laksana** | **2026-09-08 18:22** |
| cb73cd3d… | bo_laksana | 2026-08-07 14:56 |
| cb73cd3d… | bo_laksana_rerank | 2026-07-27 11:37 (stale) |

### 4.3 Corroboration #1 — 1c826d5a (Abhinandan): fully intact, and *why*

`bo_laksana`/`bo_laksana_rerank`'s **last** MSR rebuild for this chart was 2026-08-07 / 2026-08-12
16:47 — both **before** `ka_kalasutra` (2026-08-12 17:09) and `ka_sangam` (2026-08-12 16:58) ran.
No MSR rebuild has happened since kāla last ran for this chart, so the CASCADE has never fired.
Current row counts match `asset_throughput.rows_written` **exactly** (336,093 = 336,093; 17,957 =
17,957) — the strongest possible confirmation that the writers themselves are correct and
idempotent; the *only* variable that differs from the canonical chart is build-order relative to
L2.

### 4.4 Corroboration #2 — cb73cd3d: partially emptied, and the join proves the mechanism directly

`bodha_msr_signals` for this chart shows **two distinct `build_id` generations**:
```sql
SELECT build_id, count(*), min(computed_at), max(computed_at)
FROM bodha_msr_signals WHERE chart_id='cb73cd3d-9eba-4220-9902-0de91566e980'
GROUP BY build_id ORDER BY min(computed_at);
```
| build_id | count | min(computed_at) | max(computed_at) |
|---|---|---|---|
| d47f0e98-7283-440e-9cc0-730903d58217 | **145** | 2026-07-27 11:34:48 | 2026-07-27 11:34:51 |
| 26918057-e127-40cc-8f74-4f68dea989d4 | 49,730 | 2026-08-07 14:52:42 | 2026-08-07 14:55:38 |

`ka_kalasutra`/`ka_sangam` ran for this chart on 2026-07-27 14:13–14:20 — **after** the `d47f0e98`
generation was written, **before** the `26918057` rebuild on 2026-08-07 replaced almost all of it
(49,730 of the original ~49,875 signals were deleted and replaced; only 145 old-generation signals
happened to survive that particular rebuild un-deleted).

Direct join — which `bodha_msr_signals` generation do the 1,055 *surviving* `kala_activation` rows
for this chart actually reference?

```sql
SELECT s.computed_at, s.build_id, count(*)
FROM kala_activation ka JOIN bodha_msr_signals s ON s.signal_id = ka.signal_id
WHERE ka.chart_id = 'cb73cd3d-9eba-4220-9902-0de91566e980'
GROUP BY s.computed_at, s.build_id ORDER BY s.computed_at;
```
Result: **all 1,055 rows** (360+360+125+160+50) resolve to `build_id = d47f0e98…` (the *original*,
July generation) — **zero** resolve to the 49,730-row `26918057…` rebuild. This is the decisive
proof: the 334,392 `kala_activation` rows that vanished for this chart are precisely the ones whose
`signal_id` was deleted by the 2026-08-07 MSR rebuild; the 1,055 that remain are precisely the ones
whose `signal_id` happened to survive that rebuild. There is no other explanation consistent with
this join result other than the FK CASCADE.

`kala_convergence.signal_id` is non-null for **100%** of rows in both surviving charts (17,957/17,957
for 1c826d5a; 2,540/2,540 for cb73cd3d), confirming the same mechanism fully accounts for
`kala_convergence`'s parallel 0-row state on the canonical chart — it is not a coincidentally
separate cause.

---

## 5. What remains genuinely undiagnosable read-only

1. **Exact intermediate MSR build history for the canonical chart between 2026-08-13 and
   2026-09-11.** `asset_throughput` only retains the *latest* state per (chart, asset) — there could
   have been one MSR rebuild or several between those dates; we can only bound it ("some rebuild(s)
   completed by 2026-09-08/09-11, and by then 100% of the pre-08-13 signal set was gone"), not
   enumerate them. A build-history/event-sourcing table for `bodha_msr_signals` builds (if one
   exists outside the DB, e.g. CI/deploy logs) would be needed to fully reconstruct it.
2. **The 4-day gap between the 2026-09-04 lit→stale flag and the 2026-09-08 actual rebuild.** The
   staleness audit fired on 2026-09-04 19:42:09 (§2.1), four days before `bo_laksana`'s recorded
   `last_built_at` of 2026-09-08. This could mean an earlier, smaller upstream hash change triggered
   the staleness flag before the full signal-turnover rebuild landed, or the flag and the rebuild are
   from unrelated causes that happened to land close together. `asset_throughput_state_audit`'s
   `application_name` field came back blank for both rows in our queries, so we cannot identify the
   triggering session/job from the DB alone; this would need application/CI logs.
3. **Whether the same CASCADE has already emptied the other three tables migration 403 also
   touched** (`kala_bhavishya`, `kala_darshana`, `kala_obstruction`) for this or other charts. Not
   queried here — out of the two-table scope given — but structurally certain to be exposed to the
   identical hazard, and worth a fast follow-up check given the shared root cause.
4. **Whether any process anywhere currently detects "`state='stale'` and current row count = 0"**
   as a distinguishable, alertable condition. We found no such gate in the schema/migrations
   reviewed; confirming its absence definitively would require reading the orchestrator's staleness/
   promotion code (`asset_runner`), which is source-code archaeology, not a DB query — flagged as a
   fast, high-value follow-up rather than attempted here to keep this diagnosis DB-forensics-scoped.

---

## 6. Does this change the severity/framing of the finding?

**Yes — the finding is not "mysterious data loss," it is fully explained, deterministic, and
already reproducible on other charts (cb73cd3d), which if anything makes it more consequential, not
less:**

- It is **not** hypothesis 5's "prior audit queried the wrong row" scenario — there genuinely is
  no later build record to have missed; the single `asset_throughput` row already *is* the latest,
  and it is frozen at the 2026-08-13 success.
- It is **not** a one-off bug confined to this chart — the identical mechanism has already partially
  fired on `cb73cd3d` and has not (yet) fired on `1c826d5a` purely because that chart's L2 rebuild
  order happened to land before its L3 build, not after. The canonical chart was simply unlucky in
  build ordering, and **will be unlucky again** the next time L2 Bodha rebuilds MSR signals for it,
  unless L3 is rebuilt in the same breath.
- The `ON DELETE CASCADE` was a **deliberate, documented** architectural choice (migration 403) built
  on an assumption — automatic, lockstep L3-after-L2 rebuilding — that is not actually enforced
  anywhere in the orchestrator. The `state='stale'` flag correctly fires (§2.1) but is purely
  informational; nothing currently escalates "stale AND empty" as distinct from merely "stale."
- Practical exposure: at minimum `ka_kalasutra`, `ka_sangam`, plus (per migration 403, unverified
  here) `kala_bhavishya`, `kala_darshana`, `kala_obstruction` — i.e. a meaningful slice of the 22
  active `ka_*` identities in the current L3 data-plane elevation campaign — inherit this same FK
  and the same hazard whenever their signal-linked rows outlive the MSR generation they were built
  from.

**Recommended remediation directions** (diagnosis only — not actioned in this read-only pass):
(a) have the orchestrator automatically rebuild any `state='stale'` L3 asset immediately once its
upstream L2 build completes, closing the gap the migration 403 comment assumed was already closed;
or (b) replace/augment the CASCADE with an explicit reconciliation step in the L3 writers' own
delete-then-insert pass; or, at minimum, (c) add a monitor/gate that treats
`state='stale' AND current_row_count = 0` as a distinguishable, alertable condition rather than an
ordinary "needs rebuild" state indistinguishable from "slightly outdated."
