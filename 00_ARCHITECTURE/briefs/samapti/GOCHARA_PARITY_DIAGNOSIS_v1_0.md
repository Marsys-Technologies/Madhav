---
artifact: GOCHARA_PARITY_DIAGNOSIS
canonical_id: GOCHARA_PARITY_DIAGNOSIS
version: 1.0
status: CURRENT
created: 2026-07-30
lane: A6-GOCHARA-DIAG (SAMĀPTI conductor swarm)
implements: 00_ARCHITECTURE/briefs/samapti/SAMAPTI_IMPLEMENTATION_BRIEF_v2_0.md §9.3 (T6.3), register item GOCH-1
mode: READ-ONLY diagnosis — no production table was mutated by this lane
feeds: C2-GOCHARA-RUN (completion plan, §5), A7-N8-AUDIT (finding F3, §6)
---

# `ka_gochara_sweep` operator-chart parity — root-cause diagnosis

## §0 — The one-paragraph answer

**`ka_gochara_sweep` is not stalling, not hanging, and not failing to resume. It is being
evicted by its own watchdog budget at exactly the point six hours of compute buys, and the
two operator charts were never re-dispatched the three-to-four further times the canonical
chart received.** The asset's substep plan is 303 substeps (3 populated `event_class`es ×
101 years) and each substep costs ~255–280 s of writer wall-clock, i.e. **~21–24 h for the
whole plan**, against `asset_registry.writer_timeout_seconds = 21600` (6 h, set by migration
462). One dispatch therefore completes 21600 / ~260 ≈ **76–87 substeps ≈ one quarter of the
plan** — which is precisely the "~1/4 of 303" the brief describes. Chart `482012f1` reads
303/303 for exactly one reason: it received **six** sequential resumed dispatches, three of
them full-budget. Chart `1c826d5a` received **one** productive dispatch (→ 78). Chart
`cb73cd3d` received **exactly one dispatch, ever** (→ 70). The plateau is the arithmetic of
budget ÷ per-substep cost. It is not a defect in the writer, and the completion path needs
no code change.

The "~1/4" is not an approximation of a failure. It is `21600 s ÷ 260 s/substep ÷ 303
substeps = 27%`.

---

## §1 — The measurement

`writer_timeout_seconds` and plan shape, live from `asset_registry`:

```
asset_id         | writer_timeout_seconds | has_substeps | target_floor | count_sql
ka_gochara_sweep | 21600                  | True         | 0            | SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1
```

Plan size is `len(event_classes) × _N_YEARS` (`services/ka_gochara_sweep/writer.py:283-290`),
with `_N_YEARS = 101` (`writer.py:113`). All three charts have the same three populated
`gochara_resonance_map` event classes, so all three plan to **303**.

Per-substep cost, computed from consecutive `build_substep_progress.completed_at` deltas
(inter-dispatch gaps > 30 min excluded):

| chart | committed | median s | p90 s | max s |
|---|---|---|---|---|
| `1c826d5a` | 78 | **252.8** | 319.4 | 665.0 |
| `482012f1` | 303 | **255.2** | 321.7 | 1692.9 |
| `cb73cd3d` | 70 | **280.2** | 342.8 | 754.1 |

303 × ~260 s ≈ **78,800 s ≈ 21.9 h**. The budget is 21,600 s. The ratio is **3.6**.

---

## §2 — The decisive evidence: what one full dispatch actually buys

Substeps committed inside each dispatch window, attributed by joining
`build_substep_progress.completed_at` into `build_run_assets.started_at … ended_at`, for the
canonical chart's post-replan campaign (2026-07-24 onward):

```
run      | started_at                     | hours | substeps_committed_in_window
5a4b6d2f | 2026-07-24 15:16:56.249655+00  | 6.00  | 83     <- hit the 21600s budget
8fd6bcf7 | 2026-07-24 22:48:24.654825+00  | 6.00  | 87     <- hit the 21600s budget
53ddc618 | 2026-07-25 05:12:07.818260+00  | 3.14  | 44     <- orphaned_by_crash
e34cdc6a | 2026-07-25 08:20:30.110033+00  | 0.78  | 8      <- orphaned_by_crash
5209969a | 2026-07-25 09:07:25.016698+00  | 6.00  | 76     <- hit the 21600s budget
60954f5a | 2026-07-25 15:10:21.361292+00  | 0.29  | 5      <- COMPLETED (303/303)
```

83 + 87 + 44 + 8 + 76 + 5 = **303**, exactly.

**A full six-hour dispatch of this asset completes 76–87 substeps (n = 3 observed: 83, 87,
76).** The operator charts' 78 and 70 are each precisely one such dispatch — not a partial
one, not a crashed one. They are what the budget pays for.

Dispatch counts, from `build_runs ⋈ build_run_assets` where `asset_id='ka_gochara_sweep'`:

| chart | dispatches | productive | result |
|---|---|---|---|
| `482012f1` | 18 (2026-07-19 → 07-25) | 6 post-replan | 303/303, `lit` |
| `1c826d5a` | 12 | **1** (`fef77aaf`, 21598 s) | 78/303, `error` |
| `cb73cd3d` | **1** (`8e4da1f9`, 21597 s) | 1 | 70/303, `error` |

`cb73cd3d` has been dispatched once in its entire history. There is no mystery to explain on
that chart beyond §0: nobody ran it a second time.

---

## §3 — Alternative mechanisms tested and REFUTED

A diagnosis is only worth as much as the hypotheses it kills. Each of these was tested
against live state, not reasoned about.

**R1 — "Resumption is broken; each attempt wipes and restarts" (REFUTED).**
`plan_substeps` calls `_load_completed_substeps`, which returns `None` — triggering
`DELETE FROM kala_gochara_windows` + `DELETE FROM build_substep_progress` and a full replan
(`writer.py:319-330`) — whenever the stored `build_fingerprint` set differs from the
recomputed one. If that fired every attempt, the charts would livelock at ~1 dispatch's
worth forever, which matches the symptom. It does not fire. Recomputing
`_compute_build_fingerprint` (`writer.py:621-628`) from live DB state — `_RESUME_VERSION=7`,
`chart_id`, `_derive_birth_year` from `public.charts.birth_date`, `_discover_event_classes`
from `gochara_resonance_map` — reproduces the stored fingerprint **exactly** on all three
charts:

```
chart=482012f1  birth_year=1984  recomputed=aa29b9133f9f71f3…  stored=[aa29b9133f9f71f3…]  RESUME
chart=1c826d5a  birth_year=1985  recomputed=ce81aca0f7c562d1…  stored=[ce81aca0f7c562d1…]  RESUME
chart=cb73cd3d  birth_year=1971  recomputed=070be7ad979eebd3…  stored=[070be7ad979eebd3…]  RESUME
```

Each chart also stores exactly **one** distinct fingerprint (`count(DISTINCT
build_fingerprint) = 1`). Independently corroborated by §2: the canonical chart demonstrably
*accumulated* 83 → 170 → 214 → 222 → 298 → 303 across six dispatches, which is only possible
if resumption works. **Resumption is sound. A resumed dispatch will resume, not wipe.**

**R2 — "The server's idle-in-transaction killer terminates the connection during CPU-heavy
substeps" (REFUTED).** The role does carry the killer — `pg_roles.rolconfig` for `amjis_app`
is `['idle_in_transaction_session_timeout=600s', 'statement_timeout=1800s']` — and the
orchestrator does hold a transaction open with `SAVEPOINT writer_exec` across the entire
substep (`asset_runner.py:438-444`). But `pipeline/orchestrator/db.py:44-47` defends against
exactly this, twice: the libpq `options="-c idle_in_transaction_session_timeout=0"` startup
parameter, **and** — because a proxy may strip startup options — an explicit
`SET idle_in_transaction_session_timeout = 0` / `SET statement_timeout = 0` issued as real
statements after connect. Confirmed empirically: the canonical chart has a substep whose
inter-commit delta was **1692.9 s** (~28 min) and it committed successfully. A 600 s killer
was not in force. **Not the mechanism.**

**R3 — "It timed out" (REJECTED as a non-answer, and as stated, false).** The writer does not
time out in the sense of failing. It is *evicted*, having committed every substep it
finished, durably, with a correct resume ledger. The distinction is the whole diagnosis: an
eviction at 26% with sound resumption needs three more dispatches; a timeout at 26% would
need a code fix. This asset needs the former.

**R4 — "The 100-year horizon anchor is still wrong / the span is truncated at 2027"
(REFUTED as a cause; real as a scheduling defect — see F5).**
`asset_throughput.last_error` on `1c826d5a` reads *"78/303 substeps committed (horizon
truncated at 2027 vs the full birth+100y span to 2084)"*. The **plan** is not truncated: it
is 303 substeps spanning `year_idx` 0…100, i.e. birth_year → birth_year+100, verified by
fingerprint match and by the `generate_series(0,100)` reconciliation in §5. What is pinned to
2027 is the dispatch **priority tier** (`_SCORING_SPAN_END_YEAR`), which changes only the
*order* substeps run in, never which substeps exist. The note describes a real defect (F5)
but misattributes the plateau to it.

---

## §4 — The 2026-07-28 re-dispatch incident (separate, and honestly unresolved in part)

`1c826d5a` was re-dispatched **eleven** times on 2026-07-28 under
`triggered_by='ci-parked-item3-ka-gochara-sweep-resume'`. **Every one of them committed zero
substeps**: `max(build_substep_progress.completed_at)` for that chart is
`2026-07-26 19:58:29+00`, two days earlier. They died after 46–1155 s with:

```
worker_crash: OperationalError: the connection is lost      (516s, 46s, 110s, 1011s, 1155s)
orphaned_by_crash: prior orchestrator terminated while asset was in-flight   (223s, 163s)
```

The server side names the cause, from the Cloud SQL Postgres log, `user=amjis_app`, in
**pairs** — matching the two connections the orchestrator opens per run (the main run
connection plus the per-asset `worker()` connection, `runner.py:483-485`):

```
2026-07-28T14:36:35  FATAL: terminating connection due to administrator command   (×2)
2026-07-28T14:38:39  FATAL: terminating connection due to administrator command   (×2)
2026-07-28T14:45:31  FATAL: terminating connection due to administrator command   (×2)
2026-07-28T16:17:41  FATAL: terminating connection due to administrator command   (×2)
```

What that message is **not**: it is not `idle_in_transaction_session_timeout` (different
message, and disabled per R2), not `statement_timeout` (also disabled), and not a Cloud SQL
instance restart — `gcloud sql operations list --instance=amjis-postgres` records no
`RESTART` on 2026-07-28, only `BACKUP_VOLUME` at 02:43. `FATAL: terminating connection due to
administrator command` is a backend SIGTERM, i.e. an explicit `pg_terminate_backend()`.

**Honest boundary: `pg_terminate_backend` appears nowhere in this repository**
(`grep -rn "pg_terminate_backend\|pg_cancel_backend"` over `*.ts *.py *.sql *.sh *.yml`,
excluding `node_modules` → zero hits). The terminations were issued by something outside the
codebase, and **this lane cannot identify the caller from available evidence.** I am not
going to invent one. What can be said with confidence is that this incident is *not* the
cause of the 78/303 plateau — the plateau predates it by two days and the incident added
zero substeps — and that a second, compounding operational error is visible in the same
window: the eleven runs were fired 1–12 minutes apart while prior workers were still
in-flight, which is what produced the `orphaned_by_crash` cascade. §5's plan forbids that.

One residual artefact of the incident: run `fcc50d4f` (started 2026-07-28 16:37:34) still
carries `build_run_assets.state='building'` with `ended_at IS NULL` under a
`build_runs.state='failed'` parent.

---

## §5 — Completion plan for C2-GOCHARA-RUN (runnable; no code change required)

Remaining substeps, reconciled against the full `3 × generate_series(0,100)` plan:

| chart | career_advancement | major_gain | marriage | **remaining** | est. wall-clock | dispatches @ 6 h |
|---|---|---|---|---|---|---|
| `1c826d5a` | 58 | 67 | 100 | **225** | 225 × 253 s ≈ **15.8 h** | **3** |
| `cb73cd3d` | 44 | 89 | 100 | **233** | 233 × 280 s ≈ **18.1 h** | **4** |

**Do not raise `writer_timeout_seconds` to cover the plan in one dispatch.** The plan needs
~22 h and the Cloud Run job task timeout is 86400 s (24 h) per migration 462's own note —
that leaves no margin, and it would trade a safe, resumable, evidence-producing sequence for
a single all-or-nothing run. The budget is not the bug; the missing re-dispatches are.

Procedure, per chart, under BUILD-LOCK, **one dispatch at a time**:

1. Confirm the shared Cloud SQL Auth Proxy is listening on `127.0.0.1:5433` (see F8).
2. Record `SELECT count(*) FROM build_substep_progress WHERE chart_id=<c> AND
   asset_id='ka_gochara_sweep'` as `N_before`.
3. Reset `asset_throughput` to `dormant` for `(chart, ka_gochara_sweep)` — the orchestrator
   skips an asset already in `error`, which is why a plain rebuild dispatch is a no-op here.
   Use the established shape in `platform/scripts/dispatch_elev_beta_t_gochara_resume.py`
   (adapted to the chart id). **Leave `build_substep_progress` untouched** — it is the resume
   ledger and R1 proves it is valid.
4. Dispatch one build run. **Wait for `build_run_assets.ended_at` to be non-NULL before
   dispatching again.** Never overlap dispatches on the same chart+asset — that is what
   caused the 07-28 `orphaned_by_crash` cascade.
5. **Progress assertion (the gate that makes this non-thrashing):** after each dispatch,
   require `N_after − N_before ≥ 40`. A full-budget dispatch delivers 76–87 (§2); anything
   under 40 means the dispatch died early rather than being evicted at budget, and the run
   must stop and report rather than retry. Eleven consecutive zero-progress dispatches is the
   failure this gate exists to prevent.
6. Repeat until `count = 303`, then verify `asset_throughput.state` reached `lit` **by the
   orchestrator's own completion path**, not by the watchdog (F3).

Expected total: 3 dispatches for `1c826d5a`, 4 for `cb73cd3d`; ~34 h of wall-clock across
the two charts.

**Standing native instruction, applied.** The brief's rule is: *if it stalls again for the
same unresolved reason, PARK-HONEST — do not force it.* The reason for the plateau is now
resolved (budget ÷ per-substep cost, §0–§2), so C2 may proceed. The instruction still binds
on the §4 signature: **if `FATAL: terminating connection due to administrator command`
recurs during C2 and the progress assertion in step 5 trips, that is a genuinely unresolved
reason and C2 should PARK-HONEST rather than keep re-dispatching.**

---

## §6 — Findings discovered in this lane, out of its read-only scope

**F3 — `lit` is still forgeable through the cockpit watchdog (falsely-lit, live).**
`platform/src/app/api/cockpit/watchdog/route.ts:86-157` selects assets `building` with a
stale `last_built_at`, probes `asset_registry.count_sql`, and promotes to **`lit`** whenever
`actualRows > 0 || target_floor === 0` — with **no substep-plan completeness check**. The
Python path was fixed for exactly this defect: `asset_runner.py:612-675` re-probes
`writer.plan_substeps(ctx)` for `has_substeps=true` writers and marks `incomplete`, not
`lit`, when substeps remain. The TypeScript watchdog never received that fix. It
demonstrably fired on `1c826d5a` **at 78/303**, twice:

```
2026-07-28T15:05:05Z amjis-web [watchdog] RESCUED stuck asset ka_gochara_sweep
  (chart 1c826d5a-…): 1267 row(s) confirmed present via count_sql — marked 'lit' instead of
  blind-failing a heartbeat timeout with no data-presence check.
2026-07-28T16:35:06Z amjis-web [watchdog] RESCUED stuck asset ka_gochara_sweep (…) — same.
```

`ka_gochara_sweep` has `has_substeps = true` and `target_floor = 0`, so it satisfies the
promotion predicate two ways. This is a live instance of the SATYA-DĪPA falsely-lit class in
a surface SATYA-DĪPA did not sweep, and it bears directly on **C3-BUILDSTATE-RECON**, whose
`EP-1 NOT-APPLICABLE` disposition rests on the falsely-lit population being "empirically
zero". Route to A7-N8-AUDIT / a B-lane; do not fix here.

**F5 — `_SCORING_SPAN_END_YEAR` and the specimen years are chart `482012f1`'s biography,
hardcoded, applied to every chart (CR-87 class; scheduling-only).**
`writer.py:182` pins `_SCORING_SPAN_END_YEAR = 2027` and `writer.py:307-310` pins the
priority specimens to calendar 2010/2011 (`major_gain`) and 2013 (`marriage`) — the native's
logged life events. Both are converted to `year_idx` by subtracting *the subject chart's*
birth year, so on other charts they land on unrelated years. Verified live:

| chart | birth_year | major_gain specimen year_idx | marriage specimen year_idx | tier-1 span |
|---|---|---|---|---|
| `482012f1` | 1984 | 26, 27 | 29 | year_idx 0–43 |
| `1c826d5a` | 1985 | 25, 26 | 28 | year_idx 0–42 |
| `cb73cd3d` | 1971 | 39, 40 | 42 | year_idx 0–56 |

The consequence is visible in the committed data: on **both** operator charts `marriage` has
exactly **one** committed substep, and it sits at precisely that borrowed specimen index —
`year_idx 28` on `1c826d5a`, `year_idx 42` on `cb73cd3d`. This is scheduling only: it changes
dispatch order, never a committed row's values, and it does not affect the plateau. But it
does mean **the quarter that is built on the operator charts is the wrong quarter for those
natives** — prioritized by someone else's life events — which matters if a partial build is
ever served. It is also the true referent of the misleading "horizon truncated at 2027" note
in `asset_throughput.last_error` (R4).

**F4 — `_keepalive` is dead code (cosmetic; explicitly NOT a bug).**
`writer.py:364-366` defines `_keepalive()` (a `SELECT 1` on `ctx.db_conn`) and never calls it
or passes it to `sweep_event_class_chunk`. `ka_sangam.py` — the writer that pioneered this
substep-resumption pattern — threads its identical keepalive through five call sites
(`:553, :597, :656, :692, :718, :740`) with the docstring *"optional callable to prevent
idle-in-transaction timeout"*. It is tempting to call this the root cause. It is not:
`db.py:44-47` disables the server-side idle-in-transaction killer on every orchestrator
connection (R2), so the keepalive has nothing to defend against and its absence costs
nothing. Reported as dead code to delete or wire for consistency, not as a defect.

**F6 — orphaned in-flight marker.** Run `fcc50d4f` / `1c826d5a` still reads
`build_run_assets.state='building'`, `ended_at IS NULL`. Cosmetic; C2 should expect the
15-minute watchdog rule to interact with it (and F3 to fire again).

**F7 — the instance is undersized for this workload.** `amjis-postgres` is `db-g1-small`
(shared-core, ~1.7 GB, `ZONAL`, no HA) carrying a build that needs ~22 h of continuous
transactional work per chart. Not causal to anything diagnosed here — the cost is client-side
CPU in Cloud Run, not DB — but worth a DVA note before three more multi-hour dispatches.

**F8 — the shared Cloud SQL Auth Proxy on `127.0.0.1:5433` went down mid-session.** This
lane's own connection began failing with `could not receive data from server: Connection
refused` and no process was listening on 5433. This lane did **not** restart the shared
proxy (it may be another lane's); it completed its reads through a private proxy on port
5434. C2 requires 5433 up.

---

## §7 — Read-only attestation

Every database access in this lane was a `SELECT`. The helper used
(`scratchpad/q.py`) refuses any statement not matching `^(select|with)` and sets
`conn.read_only = True`; the fingerprint reproducer (`scratchpad/fp.py`) likewise sets
`conn.read_only = True` and issues only `SELECT`s. `build_substep_progress`,
`asset_throughput`, `build_runs`, `build_run_assets`, `kala_gochara_windows` and
`gochara_resonance_map` were read and **never written**. No rebuild was dispatched. The
only non-read action taken anywhere was starting a private read-only Cloud SQL Auth Proxy
listener on port 5434 (F8), which touches no database state.

---

*End of GOCHARA_PARITY_DIAGNOSIS v1.0.*
