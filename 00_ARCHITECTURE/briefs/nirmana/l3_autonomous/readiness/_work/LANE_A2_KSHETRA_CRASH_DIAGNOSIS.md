---
artifact: KSHETRA_CRASH_DIAGNOSIS
version: "1.0"
status: CURRENT — hypothesis with strong circumstantial support, NOT yet reproduced
date: 2026-09-22
scope: >
  Why the layer's largest asset (ka_kshetra) is sitting in `error` with a lost connection, and
  what that implies for elevating it. Diagnosis is read-only; no rebuild was attempted.
---

# Why `ka_kshetra` crashed — and why that may already be fixed without anyone noticing

## The observation

`asset_throughput` for the canonical chart, live 2026-09-22:

| asset | state | rows_written claimed | last_built | error |
|---|---|---|---|---|
| `ka_kshetra` | **error** | 1,183,134 | 2026-09-11 | `worker_crash: OperationalError: the connection is lost` |
| `ka_avadhi` | **error** | 1,169 | 2026-09-10 | `post-write integrity check failed: integrity_check_sql → F` |
| `ka_gochara_v3_century_materialize` | **error** | 914 | 2026-08-21 | `BUILD-PROTECTED` guard (working as designed) |
| `ka_gochara_sweep` | error | 0 | 2026-08-12 | `no writer registered` (retired identity) |

## The hypothesis, and the evidence for it

`ka_kshetra` is a `has_substeps=true` heavy writer (`services/ka_kshetra/writer.py:277`
`plan_substeps`, `:489` `run_substep`). The orchestrator holds ONE transaction open across a
substep while the writer does long stretches of pure CPU with **no DB traffic** — exactly the
shape an idle-in-transaction killer terminates.

`pipeline/orchestrator/db.py:46-70` documents this hazard in its own comments: it passes
`options="-c idle_in_transaction_session_timeout=1800000"` (30 min) precisely because
"legitimately slow ayanamsha substeps (up to ~20 min of pure CPU with no DB traffic) survive",
and warns that the libpq startup option is **not guaranteed to reach the server** through a
Cloud SQL Auth Proxy or pooler, in which case a role-level default "silently wins".

Measured live, role-level settings:

| role | `rolconfig` |
|---|---|
| `amjis_app` | `idle_in_transaction_session_timeout=600s`, `statement_timeout=1800s` |
| `data_plane_builder` | **(none)** |

**The timeline is the load-bearing part.** `data_plane_builder` was created by migrations
1035/1036 (`platform/supabase/migrations/`), the data-plane ownership cutover applied
**2026-09-18**. `ka_kshetra` crashed **2026-09-11** — a week BEFORE the cutover. So that build ran
as **`amjis_app`**, the role that carries the 600 s idle-in-transaction killer.

A substep exceeding 600 s of CPU with no DB traffic would be terminated server-side, surfacing in
the worker exactly as `OperationalError: the connection is lost`. That is the observed error.

## Why this matters for the elevation campaign

1. **The failure mode may already be gone, and nobody has checked.** Builds now run as
   `data_plane_builder`, which has NO role-level timeout. The 600 s killer that most plausibly
   caused this crash does not apply to the new identity. `ka_kshetra` has not been re-run since
   the cutover, so this is untested either way.
2. **But the new identity has no safety net either.** `data_plane_builder` has no
   `idle_in_transaction_session_timeout` AND no `statement_timeout`. The 30-minute bound exists
   only if db.py's startup option survives the proxy. If it does not, a genuinely hung build has
   **no server-side bound at all** — it holds a transaction open indefinitely. That is the
   opposite failure and arguably the worse one for an unattended overnight campaign.
   **Recommend: set an explicit `ALTER ROLE data_plane_builder SET
   idle_in_transaction_session_timeout` to a deliberate value rather than inheriting silence.**
   That is a one-line migration in the L3 range and removes an environment dependency instead of
   relying on a libpq option surviving a network path.
3. **`ka_avadhi`'s error is a different and more interesting class.** It is not a crash — the
   build completed and then its own post-write integrity check returned FALSE, and the
   orchestrator correctly refused to promote it. That is an earned signal working as designed
   (§N.8), and it means `ka_avadhi` has a real data-correctness problem waiting behind it, not an
   infrastructure problem.

## What would confirm this

Re-run `ka_kshetra` for one chart under `data_plane_builder` on a disposable instance sized to
hold its output, with per-substep wall-clock timing recorded. If any substep exceeds 600 s, the
diagnosis is confirmed and the old identity was the cause. This was NOT attempted here: the asset
claims 1.18M rows and the readiness worktree has no seeded upstream data at that scale.
**COULD NOT VERIFY: the actual per-substep duration.** The hypothesis rests on the timeline, the
role configuration, the writer's substep shape, and db.py's own documented warning — strong
circumstantial agreement, not a reproduction.
