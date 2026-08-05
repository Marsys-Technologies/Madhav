---
artifact: SHAD_DARSHANA_STATE (Campaign Ledger)
canonical_id: SHAD_DARSHANA_STATE
version: rolling
status: LIVE — created by Night 1 session (W0.1), updated at every wave boundary and session close
created: 2026-07-29
schema: per SHAD_DARSHANA_BRIEF_v2_0.md §6
governing: SHAD_DARSHANA_NIGHT_RUN_v1_0.md (orchestration) + SHAD_DARSHANA_BRIEF_v2_0.md (execution contract)
  + KALA_SUPREME_ELEVATION_v1_0.md (v1.2, spec authority) + KALA_SIX_VIEWS_DESIGN_v2_0.md/v1_0.md
---

# ṢAḌ-DARŚANA STATE — the campaign ledger

## ⚠ RESTORATION NOTICE (2026-08-03 ~22:15 UTC, int-929 session, main checkout)

**This file was found DELETED from this working directory (main checkout, branch
`int-929-final`) at ~22:08 UTC — not truncated, not moved, gone — while this session was
actively using it.** What follows below (down to the "END OF RESTORED CONTENT" marker) is
this session's own best-effort reconstruction from its own conversation record (everything
this session itself wrote and read back), covering the file's live NEXT-ACTION history from
this session's ~10:24 UTC entry onward, plus everything this session had separately read of
the pre-existing GATE W1 / GATE W0 / MERGE-TRAIN / audit history beneath it. **Content this
session never read into its own context (this file was 1110+ lines before tonight and had
grown further since) is NOT recovered here and may be permanently lost from this specific
copy.**

**Why this almost certainly happened:** this machine has multiple concurrent, fully-autonomous
(`--permission-mode bypassPermissions`) Claude Code processes running right now, including a
separate, actively-updated (2445 lines, modified this same minute) copy of this same file at
`.worktrees/shad-darshana-conductor/00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
SHAD_DARSHANA_STATE.md`, whose own NEXT-ACTION describes an "INT-929 SESSION" with the same
chart IDs, same 10:24–21:14 UTC window, and a claim that the native "explicitly LIFTED tonight's"
descope — a claim this session's own live conversation with the native never made or confirmed,
and which this session independently found contradicted by git (`origin/shad-darshana/
integration` HEAD unchanged since 2026-08-02 21:03 IST — no rebase, no force-push occurred,
despite that other copy's claim that one did). **Read as: the real native likely pasted the
same governing native-directive prompt into more than one Claude Code window tonight; this
session and the `shad-darshana-conductor` worktree session are each independently narrating
the same task, unaware of each other, and something (most likely the other session's own
tooling) deleted this copy.** The native should reconcile the two sessions directly — this
session is not attempting to adjudicate between them.

---

## NEXT-ACTION

**2026-08-05 ~09:10 UTC (SESSION-A-SWEEP) — CLOSE-OUT CHECKLIST COMPLETE. STANDING DOWN.**

**1. Safety net — RETAIN, PAUSED (native ruling, re-verified live, not assumed):**
`gcloud scheduler jobs describe int929-gochara-relay-safety` → **PAUSED**, confirmed at
this entry's timestamp, not carried forward from the earlier check. Retained for possible
reuse in W2G's materialization era; teardown commands remain documented above (Cloud
Scheduler job / Cloud Run service / service account, in that order). **⚠ MUST NOT be
unpaused while sweep-corpus protection Layers 3-4 (migration + trigger + planner guard)
are unshipped — an auto-dispatcher aimed at the now-protected corpus re-creates the exact
accidental-rewrite vector the protection exists to close.**

**2. Nothing half-alive, verified:**
- `gcloud run jobs executions list` (10 most recent) — all `Completed/True`, **zero
  running**.
- `build_runs` — **zero rows** with `state='running'` for either canonical chart.

**3. Cosmetic-state sweep — clean, no flag needed this time:** `asset_throughput` for
`ka_gochara_sweep` on both charts reads `state='lit'`, `last_error=NULL` — neither chart
is stuck showing a stale `'error'`/`'BLOCKED'` cosmetic artifact against a complete
substep ledger. (Individual `build_runs` rows for both charts DO still show the familiar
cosmetic `state='failed'` pattern on every generation except each chart's final one — this
is the same documented per-dispatch-timeout cosmetic, `asset_throughput` is the trustworthy
signal, not `build_runs.state`. Nothing to patch, nothing new.)

**4. SWEEPS-COMPLETE numbers re-confirmed, unchanged:** 606/606 both charts;
`kala_gochara_windows` 16,297 (482012f1) + 19,323 (1c826d5a); archives verified matching
(Layer-2, recorded above).

**5. Relay post-mortem — with ONE factual correction to the native's own draft.**
Reconstructed from `build_runs` history for `ka_gochara_sweep`, scoped to the current
606-substep corpus (from the Night-5 re-grammar full-replan trigger, 2026-08-02 ~07:46
UTC, through completion 2026-08-05):
- **Real dispatch generations** (distinct actual container executions; excludes the
  IAM-outage window's repeated instant-403 non-starts, which never ran a container):
  **~9 for 482012f1, ~10 for 1c826d5a.**
- **Two confirmed multi-hour idle gaps:** ~14h (2026-08-02 ~20:23 UTC → 2026-08-03 10:23
  UTC, before this session opened) and ~4h50m (2026-08-03 16:23 UTC → 21:13 UTC, this
  session's own manual-relay miss). This session cannot independently corroborate the
  native's cited "~8h" gap (predates this session's visibility into the campaign) — not
  disputing it, just not re-asserting a figure this session didn't itself verify.
- **⚠ CORRECTION to the native's draft:** the native's item 5 text assumed "net-catch
  count (zero — never fired in anger)." **That's not what the evidence shows.** After the
  `run.jobs.runWithOverrides` IAM fix (~04:52 UTC 2026-08-04), the safety net
  successfully self-dispatched **FOUR times per chart**, unattended, no manual
  intervention: 09:45 UTC Aug 4 (the proven catch), 16:00 UTC Aug 4, 22:15 UTC Aug 4, and
  04:30 UTC Aug 5 (the generation that carried each chart to 606/606). Every gap in that
  second half of the campaign was ~6-15 minutes (the Scheduler's own poll cadence), not
  hours. The net earned real trust here, not zero.
- **One open, undiagnosed anomaly, flagged rather than hand-waved:** the safety net's
  failed 403 attempts actually began at ~21:45 UTC 2026-08-03 (per `build_runs`
  timestamps) — before generation D's own container had even reached its ~03:13 UTC
  2026-08-04 expiry. That implies the function's `asset_throughput.state=='building'`
  guard was NOT correctly skipping during that window, a second, separate, never-fully-
  diagnosed behavior distinct from the IAM permission bug. It caused no harm (the calls
  failed before touching anything), and it self-resolved once the IAM fix landed
  (post-fix, every dispatch aligned correctly with real expiries) — but it's an honest
  unknown, not a closed one. SESSION-B inherits it as a documented curiosity if the paused
  net is ever revived.
- **The lesson, already proven and directly relevant to W2G:** session-bound relays leak
  wall-clock — both confirmed multi-hour gaps happened while a human-timescale session
  was the only thing standing between one container's expiry and the next dispatch. A
  15-min-SLO architecture (W2G) that never needs a relay at all structurally can't leak
  this way.

**6. STAND DOWN.** No worktree/branch hygiene owed — this session only ever touched this
docs file (untracked, no git state to clean) and the safety-net GCP resources (paused, not
torn down, per ruling 1). ~110h of compute shepherded across roughly 9-10 dispatch
generations per chart, doubling to 606/606 on both canonical charts — done, and every
number in this closing record independently verified against live state before being
written, including the one place this session found the native's own draft slightly
wrong. This is SESSION-A-SWEEP's final entry.

---

**2026-08-05 ~08:45 UTC (SESSION-A-SWEEP) — SWEEP-CORPUS PROTECTION addendum received;
verified the two layers in this session's domain, declined the rest as out-of-scope.**

Native directive asked for four protection layers: (1) pause the safety net, (2) archive
tables, (3) a DB migration adding `build_protected_assets` + DELETE/UPDATE/TRUNCATE
triggers on `kala_gochara_windows`, (4) a `resolveBuildPlan`/planner-route TS guard.
**Layers 1-2, independently verified true:**
- `gcloud scheduler jobs describe int929-gochara-relay-safety` → **PAUSED**.
- `kala_gochara_windows_archive_20260805` = 35,620 rows = 16,297 + 19,323 (exact match to
  the two charts' live counts). `build_substep_progress_archive_20260805` = 1,212 rows =
  606 + 606 (exact match).

**Layers 3-4 declined by this session** — a SQL migration + trigger + TypeScript planner
guard is code/schema work, squarely "frontier/build lane" per this session's own
established topology (same category as the earlier sweep-optimizer directive, which the
native already confirmed routes to SESSION-B-BUILD/Conductor, not here). Not attempted,
not partially started. Routing this to SESSION-B-BUILD is the native's to do.

`kala_gochara_windows_archive_20260805` and `build_substep_progress_archive_20260805`
added to this session's own mental untouchables note (not this session's table to alter
regardless).

---

## SWEEPS-COMPLETE

**2026-08-05 ~08:35 UTC (SESSION-A-SWEEP) — SWEEPS-COMPLETE, formally and independently
verified. Both charts 606/606. This is the real signal — SESSION-B-BUILD's gate-chain
trigger.**

Note on provenance: `.worktrees/shad-darshana-conductor`'s own ledger copy shows
SESSION-B-BUILD self-recorded a "SWEEPS-COMPLETE" at ~06:45 UTC before either chart was
actually done, then separately notes Phase 2 never triggered because that self-attributed
entry wasn't the real SESSION-A signal. Correct outcome — the topology held. **This entry
is that real signal**, written only now that both charts are independently verified
complete, not on a self-report.

**482012f1 (Abhisek):** `asset_throughput` — `state='lit'`, `last_error=NULL`,
`last_built_at=2026-08-05T04:31:45Z`. `build_substep_progress` = 606/606. `kala_gochara_windows`
row count = **16,297**.

**1c826d5a (Abhinandan):** `asset_throughput` — `state='lit'`, `last_error=NULL`,
`last_built_at=2026-08-05T06:35:55Z`. `build_substep_progress` = 606/606. `kala_gochara_windows`
row count = **19,323**.

Both verified via the same method: substep-count AND asset_throughput terminal state AND
non-zero downstream row count — not substep-count alone (the exact discipline this
session's earlier corrections were about). No errors on either chart. Current Cloud Run
executions all show `Completed/True`, none running — the safety net correctly saw both
charts at 606/606 on its last 15-min check and took no action (its own `skip-complete`
branch), consistent with genuine completion rather than a stalled relay.

**Per the native's ordered duties, this session's SWEEPS-COMPLETE responsibility is
discharged.** Chart locks freed for Phase 2 (SESSION-B-BUILD's gate chain) — SESSION-A does
not start the gate chain itself. This session remains the owner of the safety net (now
idle/no-op by design, nothing left for it to dispatch) and available for any further
sweep-relay-scoped requests, but has no further active duty on the sweep itself.

---

**2026-08-05 ~05:24 UTC (SESSION-A-SWEEP) — interim status: ONE of two charts complete;
SWEEPS-COMPLETE not yet written, honest ETA below. (Aware SESSION-B-BUILD has been
polling for this signal since ~05:14 UTC and closed Night 6 PARKED-HONEST on it — this
entry exists so the wait has a concrete number, not just silence.)**

**482012f1 (Abhisek) is COMPLETE and independently verified** — not just a substep-count
coincidence: `asset_throughput` shows `state='lit'`, `last_error=NULL`,
`last_built_at=2026-08-05T04:31:45Z`; `build_substep_progress` count = 606/606;
`kala_gochara_windows` holds 16,297 rows for this chart. This chart's `ka_gochara_sweep`
is done.

**1c826d5a (Abhinandan) is NOT complete yet — 586/606 (~97%), last substep landed
2026-08-05T05:17:47Z, ~20 remaining.** At the current ~4.6-4.7 min/substep rate that's
roughly **1.5-1.6h to completion, ETA ~06:50-07:00 UTC**, comfortably inside the current
execution's window (no relay action expected to be needed before it finishes).

**SWEEPS-COMPLETE will be written the moment 1c826d5a also reaches 606/606** (checked
opportunistically on status requests) — not before, per this session's own truth-over-
completion discipline. This is SESSION-B-BUILD's own documented trigger for Phase 2; this
session does not start the gate chain itself either way.

---

**2026-08-04 ~14:16 UTC (SESSION-A-SWEEP) — PROVING TEST PASSED: ONE OBSERVED CATCH, safety
net is PROVEN. This session's manual wakeup loop is retired.**

`build_runs` shows a clean, unambiguous catch: `int929-relay-safety-482012f1` and
`int929-relay-safety-1c826d5a`, both `state='running'` (not `'failed'`), created
**2026-08-04T09:45:01-02Z** — 6 minutes after the 09:39:25-26Z expiry, well inside the
20-minute stand-back window, with **zero manual intervention** from this session (this
session's own wakeup chain happened to fire late and only caught up at ~14:15 UTC — the
net acted entirely on its own before that). This is the real thing the earlier ~04:21 UTC
report wrongly claimed: this time it's actually the `int929-relay-safety-*` service
account dispatching, not the native's own credential. The `roles/run.jobsExecutorWithOverrides`
IAM fix (04:52 UTC) resolved the 403 cleanly. **Per the native's own instruction, one
observed catch retires this session's manual wakeup loop — done as of this entry.**

**Current state (counting rule: `asset_id='ka_gochara_sweep'` + current
`build_fingerprint` only):**
- 482012f1: execution `-6zrq9` (from the 09:45:01Z dispatch), 451/606 (~74%), last write
  `2026-08-04T14:08:04Z`. ~155 remaining, expiry ~2026-08-04T15:45:01Z.
- 1c826d5a: execution `-bsqv9` (from the 09:45:02Z dispatch), 418/606 (~69%), last write
  `2026-08-04T14:05:30Z`. ~188 remaining, expiry ~2026-08-04T15:45:02Z.
- Current per-substep rate ~4.6-4.7 min (slightly faster than earlier estimate, likely
  from continuous coverage with no idle gaps) — projects to **at least one more relay
  cycle** needed past the current 15:45 UTC expiry before either chart reaches 606/606.

**Going forward:** this session no longer arms a wakeup loop — the net is trusted to
handle the remaining cycle(s) unattended. This session remains available for on-demand
status checks (read-only) and will still update this ledger's relay block / write
SWEEPS-COMPLETE when 606/606 is reached on both charts (checked opportunistically on
status requests, not on a wakeup schedule). If the net is ever observed to miss again,
this session resumes active wakeup-based custody per the original duty order.

---

**2026-08-04 ~04:55 UTC (SESSION-A-SWEEP, resumed — native re-engaged this session with a
scoped role: owns the sweep relay + safety net + sweep-progress ledger record only, never
frontier/build/merge, never the gate chain) — SAFETY NET ROOT CAUSE FOUND AND FIXED;
CORRECTION to this session's earlier "safety net worked as designed" claim.**

**Correction first:** this session earlier (see the ~04:21 UTC status report) credited the
Cloud Scheduler safety net with an automatic catch of generation-2's expiry. **That was
wrong.** `build_runs.triggered_by` shows the actual generation-3 dispatch (03:39:25-26 UTC,
executions `-xrjfs`/`-6zjct`) came from `int-929-gochara-relay-resume-*` — this session's
own MANUAL dispatch-script naming — fired via the native's own gcloud credential, not the
safety net. The safety net's own attempts (`triggered_by='int929-relay-safety-482012f1'`,
one every 15 min from **22:45 UTC onward**, 17 consecutive attempts through 03:30 UTC) all
show `state='failed'`.

**Root cause, confirmed via Cloud Run logs (not guessed):**
```
google.api_core.exceptions.PermissionDenied: 403 Permission 'run.jobs.runWithOverrides'
denied on resource 'projects/madhav-astrology/locations/asia-south1/jobs/
brahma-build-pipeline-job'
```
`roles/run.invoker` (granted at build time) covers running a job with its default config;
dispatching WITH container overrides (`--run-id`, `MARSYS_RUN_ID` — exactly what this
function does) needs the separate `run.jobs.runWithOverrides` permission. This session's
original manual test (21:28 UTC) only ever exercised the idempotent no-op/"skip-active"
branch, since both charts were still building at that moment — it never actually called
`run_job()`, so the gap went undetected until this diagnostic pass. Confirmed
`roles/run.jobsExecutorWithOverrides` (already in use elsewhere in this project, on
`amjis-web-runtime`) is exactly the missing grant (`includedPermissions:
run.executions.cancel;run.jobs.run;run.jobs.runWithOverrides`).

**Fix applied 2026-08-04 ~04:52 UTC:** granted `roles/run.jobsExecutorWithOverrides` on
`brahma-build-pipeline-job` to `int929-relay-safety@madhav-astrology.iam.gserviceaccount.com`
(scoped to this job only, alongside the existing `run.invoker`). **NOT yet proven** — no
idle chart exists right now to safely exercise the real dispatch path without colliding
with the two healthy in-flight builds. Per the native's own instruction, the proving test
happens at the next real expiry.

**Current verified state (SESSION-A-SWEEP counting rule: `asset_id='ka_gochara_sweep'` AND
current `build_fingerprint` only — 61 stale `ka_sangam` rows per chart excluded):**
- 482012f1: execution `-xrjfs`, started `2026-08-04T03:39:25Z`, expiry
  **~2026-08-04T09:39:25Z**.
- 1c826d5a: execution `-6zjct`, started `2026-08-04T03:39:26Z`, expiry
  **~2026-08-04T09:39:26Z**.
- Both climbing normally as of this entry (~312/606 and ~292/606 at last check before this
  entry, growing).

**Duties in progress (SESSION-A-SWEEP, per native's ordered list):**
1. Wakeup armed for ~09:35 UTC (before expiry).
2. **Proving test at ~09:39 UTC expiry: stand back ~20 min, let the (now-fixed) net act
   alone.** Verify via `build_runs.triggered_by='int929-relay-safety-*'` reaching
   `state` other than `'failed'` AND a real new Cloud Run execution appearing, substeps
   landing. Record ONE OBSERVED CATCH if it passes → retire this session's manual wakeup
   loop for real. If it fails again: dispatch manually immediately (block below),
   re-diagnose (this time from a confirmed-different starting point since the IAM gap is
   now closed), redeploy, repeat at the next expiry.
3. Ledger relay block kept current below, attributed SESSION-A-SWEEP.
4. Watching for "OPTIMIZER-PASS" from SESSION-B-BUILD (sweep-optimizer lane) — not seen
   yet.
5. Will write SWEEPS-COMPLETE at 606/606 both charts (not reached yet: 482012f1 remaining
   ~294, 1c826d5a remaining ~314 at last check).

**Ready-to-fire manual fallback (unchanged shape, still valid if needed before the proving
test):**
```
cd platform
RUN_482012F1=$(python3 scripts/dispatch_int929_gochara_resume_482012f1.py)
gcloud run jobs execute brahma-build-pipeline-job --region=asia-south1 \
  --args="--run-id,$RUN_482012F1" --update-env-vars="MARSYS_RUN_ID=$RUN_482012F1" --async

RUN_1C826D5A=$(python3 scripts/dispatch_int929_gochara_resume_1c826d5a.py)
gcloud run jobs execute brahma-build-pipeline-job --region=asia-south1 \
  --args="--run-id,$RUN_1C826D5A" --update-env-vars="MARSYS_RUN_ID=$RUN_1C826D5A" --async
```
(Collision-check `gcloud run jobs executions list --job=brahma-build-pipeline-job
--region=asia-south1` first — expect zero running — before firing either.)

---

**2026-08-04 ~03:52 IST / ~22:22 UTC (int-929 session, CLOSING — session standing down,
Conductor takes ownership) — three closing acts per direct native instruction in this
session's live conversation.**

**(a) Retraction of this session's ~21:35 UTC "descope lifted"/"force-pushed" correction,
with an accurate fetch-first record.** The native has directly confirmed, in this
session's own conversation, that the descope-lift exchange is genuine — drafted and pasted
by the native into the Conductor session (the session operating in
`.worktrees/shad-darshana-conductor`), which is the native-authorized owner of the full
ṢAḌ-DARŚANA run. On the force-push specifically: **re-verified live just now** —
`git fetch origin shad-darshana/integration main` (fresh, `[up to date]` — no drift from
this session's prior fetch) shows `origin/shad-darshana/integration` HEAD is now
`ca100a13` (2026-08-04 03:38:55 IST, "record CI-health finding... + PR #1043 merge"),
which descends from `f4753350` (2026-08-04 03:34:55 IST, "ADJUDICATION-16... + int-929
sweep-relay session record") — and `git merge-base --is-ancestor origin/main
origin/shad-darshana/integration` confirms **YES, origin/main is now an ancestor**. The
rebase-and-push the Conductor's ledger described is real and live.
**Accurate record for campaign memory (not the framing this session was initially asked to
record):** this session's original ~21:35 UTC check (`git fetch` + `git log`) was itself
correct AT THE TIME — the branch genuinely had not moved yet (HEAD was `c45fd4ff`, dated
2026-08-02 21:03, unchanged since the prior night) — this session did fetch before
asserting remote state both times. What changed is that **real time passed and the
Conductor's own push landed between this session's check and this correction** — a
sequencing gap between two concurrent sessions inspecting/mutating the same remote
mid-flight, not a methodology defect. **The durable lesson for campaign memory is
therefore precise, not generic:** when two sessions operate on the same remote
concurrently, a clean `git fetch` result is only a snapshot of that instant — re-fetch
immediately before treating a state-claim as settled, especially when another session's
own ledger entry claims to have changed that exact state minutes earlier. "Always fetch"
was already true and already practiced here; the real gap was "fetch again right before
deciding," not "fetch at all."

**(b) Cloud Scheduler safety net — authorization chain on record, ownership handed to the
Conductor.** The `int929-gochara-relay-safety` Cloud Scheduler job / Cloud Run service /
service account (full build record in the ~21:30 UTC entry below) **was directly
authorized by the native in this session's own live conversation** — offered via an
explicit AskUserQuestion after this session's manual relay missed its 6h mark by ~4h49m;
the native selected "Stand up a minimal Cloud Scheduler safety net for tonight
(recommended)." This is native-authorized infrastructure, not a violation of the earlier
10:24 UTC entry's "Cloud Scheduler stays deferred" note — that deferral was superseded in
this same session by the native's own later, direct instruction, not silently overridden.
**Ownership handoff, effective now:** the Conductor session (topology owner per native
ruling, this entry) owns the safety net going forward — its monitoring, its 15-min
Scheduler cadence, and its teardown. Teardown commands (unchanged, still valid, now the
Conductor's to run when appropriate):
```
gcloud scheduler jobs delete int929-gochara-relay-safety --location=asia-south1 --quiet
gcloud run services delete int929-gochara-relay-safety --region=asia-south1 --quiet
gcloud iam service-accounts delete int929-relay-safety@madhav-astrology.iam.gserviceaccount.com --quiet
```
Per native ruling, the safety net **stays live** (ratified, not torn down) — the Conductor
now watches it alongside its own relay/frontier work.

**(c) Final ledger state.** This file is untracked (`git status` shows it as `??` in the
main checkout) — there is no git push for this specific copy to verify; "final state" here
means: this entry is the last one this session writes, the file is internally consistent
and saved to disk, and the RESTORATION NOTICE above stays in place as the honest record of
tonight's file-loss incident for whoever reads this copy next. The Conductor's own copy at
`.worktrees/shad-darshana-conductor/.../SHAD_DARSHANA_STATE.md` is the fuller, live
record going forward — this session does not merge the two.

**This session now stands down: no further dispatches, builds, or ledger writes after this
entry.** The Conductor owns the relay, the frontier lanes, and the ledger from here.

---

**2026-08-03 ~21:35 UTC (int-929 session, append-only correction) — the "descope LIFTED"
entry that had appeared above (dated ~11:05 UTC) and its "SESSION-OPEN (a)... rebased onto
origin/main and force-pushed" claim (in a 21:13:05 UTC entry) were CONTRADICTED BY DIRECT
EVIDENCE and were NOT produced by this conversation's exchange with the native.**
Independently checked: `git fetch` + `git log origin/shad-darshana/integration` showed its
HEAD as `c45fd4ff` dated **2026-08-02 21:03:16 +0530 — unchanged since last night**, and
`git rev-list origin/shad-darshana/integration..origin/main` = 0 / the reverse = 19,
identical to its pre-session state. **No rebase and no force-push occurred.** Separately: no
message resembling the quoted "native's verbatim confirmation" was ever sent in this
session's actual conversation with the native — this session's real exchanges only ever
approved the gochara resume relay and, later, the Cloud Scheduler safety net below, nothing
about merges, `bg_*` L0 builds, or a gate-close deploy.

`ps aux` at the time of this correction showed several other Claude Code processes active on
this machine concurrently — this file is untracked and shared across whatever sessions have
this checkout (or its worktrees) open. Confirmed at ~22:15 UTC: a second, actively-updated
copy exists at `.worktrees/shad-darshana-conductor/...SHAD_DARSHANA_STATE.md` (see the
RESTORATION NOTICE above) — that is almost certainly the source of the "descope lifted" /
"force-pushed" narrative, written by a different concurrent session, not this one. **Treat
the "descope lifted" and "force-pushed" claims as unverified from THIS session's standpoint
— this session never received that confirmation directly and is not acting on it.** If you
are a future session reading this: cross-check anything claimed as "native-confirmed"
against your own actual conversation transcript, not this file alone — and check whether
`.worktrees/shad-darshana-conductor` still holds a diverged, more current copy of this
ledger before assuming this one is authoritative.

---

**2026-08-03 ~21:30 UTC (int-929 session) — Cloud Scheduler safety net stood up behind the
manual relay after the manual relay itself missed its 6h mark by ~4h49m.**

Context: the 10:23 UTC dispatch pair (`-z2wtc`/`-xb8dc`) finished cleanly at ~16:23 UTC as
expected (215/606, 211/606). The manual ScheduleWakeup-chained relay was supposed to
redispatch within minutes of that expiry; it actually didn't fire until **21:12-21:13 UTC**
(build_runs `6c830543…`/`5b5f6a98…`, executions `-h7n6x`/`-bsvhw`, confirmed RUNNING,
substeps landing: 482012f1 216→217+, 1c826d5a 211→212+). No confirmed root cause for the
gap from what was visible in-session at the time (later context: at least one other
concurrent session was also active on this machine tonight — see the RESTORATION NOTICE —
which may or may not be related). The native is going to sleep for 8-9h and explicitly
asked for automated coverage given this repeat gap (native's own earlier stated condition
for revisiting Cloud Scheduler — met).

**Built (minimal, scoped, intended to be torn down in the morning):**
1. Dedicated service account `int929-relay-safety@madhav-astrology.iam.gserviceaccount.com`,
   three grants only:
   - `roles/secretmanager.secretAccessor` on secret `amjis-pipeline-db-url` (the same
     secret `brahma-build-pipeline-job` itself reads DATABASE_URL from).
   - `roles/cloudsql.client` (project-level, standard role — required for the Cloud SQL
     unix-socket connection).
   - `roles/run.invoker` on `brahma-build-pipeline-job` only (resource-scoped, not
     project-wide `run.developer`).
2. Cloud Run service `int929-gochara-relay-safety` (asia-south1), deployed from source via
   `gcloud run deploy --function` (buildpack-built, NOT a Cloud Functions API resource —
   avoided enabling a new project-wide API). `--no-allow-unauthenticated`, Cloud SQL
   instance `madhav-astrology:asia-south1:amjis-postgres` attached, `max-instances=1`.
   Source: scratch dir (not committed — see teardown; logic mirrors
   `platform/scripts/dispatch_int929_gochara_resume_*.py` exactly). Idempotency guard: for
   each chart, no-ops if `build_substep_progress` count ≥606 (complete) or
   `asset_throughput.state == 'building'` (already active) — otherwise dispatches a fresh
   `build_runs`/`build_run_assets` row and calls `run_v2.JobsClient().run_job()` on
   `brahma-build-pipeline-job` with `--run-id <new>` / `MARSYS_RUN_ID=<new>`. A 15-min poll
   cadence cannot double-dispatch because of this guard — and the same guard makes it safe
   even if another concurrent session's own relay mechanism is also polling/dispatching
   against the same two charts (whichever actor observes `state=='building'` first skips).
3. Cloud Scheduler job `int929-gochara-relay-safety` (asia-south1), `*/15 * * * *`, OIDC
   auth as the same SA, target = the Cloud Run service URL.

**Tested before trusting it unattended:** manually ran `gcloud scheduler jobs run
int929-gochara-relay-safety --location=asia-south1` — confirmed HTTP 200 in both Cloud Run
logs (`httpRequest.status=200`, 21:28:48 UTC) and via a direct impersonated call, body:
`{"results": [{"chart_id": "482012f1…", "action": "skip-active", "substeps": 217, "state":
"building"}, {"chart_id": "1c826d5a…", "action": "skip-active", "substeps": 212, "state":
"building"}]}` — correctly recognized both charts as already actively building and did
**not** double-dispatch. The live-redispatch path (firing when a chart actually goes idle)
has **not yet been observed end-to-end** — first real test will be around the next 6h
expiry (~03:13 UTC, see below). Test-only IAM grants (own user's `run.invoker` on the
service, `iam.serviceAccountTokenCreator` on the SA) were removed immediately after
testing — Scheduler calls the service using the SA's own OIDC token, not impersonation, so
those grants were never needed for the real path.

**Current dispatch (as of this entry):**
- 482012f1 execution `-bsvhw`, started `2026-08-03T21:13:05Z`, expiry
  **~2026-08-04T03:13:05Z**.
- 1c826d5a execution `-h7n6x`, started `2026-08-03T21:13:05Z`, expiry
  **~2026-08-04T03:13:05Z**.

**Teardown (morning, or whenever the native wants this removed):**
```
gcloud scheduler jobs delete int929-gochara-relay-safety --location=asia-south1 --quiet
gcloud run services delete int929-gochara-relay-safety --region=asia-south1 --quiet
gcloud iam service-accounts delete int929-relay-safety@madhav-astrology.iam.gserviceaccount.com --quiet
```
(The three scoped IAM grants are deleted automatically with the SA. The
`cloud-run-source-deploy` Artifact Registry repo it created can stay — it's the standard
shared repo `gcloud run deploy --source` always creates/reuses.)

**Manual fallback (still valid if the Scheduler path is ever paused/deleted):**
```
cd platform
RUN_482012F1=$(python3 scripts/dispatch_int929_gochara_resume_482012f1.py)
gcloud run jobs execute brahma-build-pipeline-job --region=asia-south1 \
  --args="--run-id,$RUN_482012F1" --update-env-vars="MARSYS_RUN_ID=$RUN_482012F1" --async

RUN_1C826D5A=$(python3 scripts/dispatch_int929_gochara_resume_1c826d5a.py)
gcloud run jobs execute brahma-build-pipeline-job --region=asia-south1 \
  --args="--run-id,$RUN_1C826D5A" --update-env-vars="MARSYS_RUN_ID=$RUN_1C826D5A" --async
```

**Completion expectation set explicitly (native-facing):** remaining substeps (~389/~394)
at the historical ~5-5.5 min/substep rate need ~35h of compute per chart. An 8-9h overnight
window — even with zero gaps — realistically lands each chart around **~50% (≈305-320/606)**
by morning, not complete. This is a maximum-progress window, not a completion target.

**Still descoped (native-set, unchanged, this session's own understanding):** no full
autonomous swarm, no merges/deploys to `main`, no frontier-lane dispatch, initiated by THIS
session. This safety net is scoped exclusively to the `ka_gochara_sweep` resume relay for
both charts. (Whether some OTHER concurrent session has separate, real authorization for
more than this is unknown to this session — see the RESTORATION NOTICE.)

---

**2026-08-03 ~10:24 UTC (int-929 session) — relay-down claim RETRACTED after live
verification; two routine resume dispatches fired; full autonomous night-run + Cloud
Scheduler infra explicitly DESCOPED for tonight, native decides when to start one.**

A native directive this session claimed both `ka_gochara_sweep` builds were dead/evicted
in a `'failed'`/`'error'` state since ~20:23 UTC 2026-08-02 (~13h), citing 117/606 and
155/606 substeps and calling for an emergency autonomous swarm + new Cloud Scheduler
supervisor infra + merges/deploys to `main`. Live verification before acting:
- `gcloud run jobs executions describe` on both 14:23 UTC executions
  (`brahma-build-pipeline-job-zjwvn`/`-gbnsd`) showed `type: Completed, status: 'True'`,
  `"Execution completed successfully in 6h19-21m"` — **not** failed/evicted.
- `build_substep_progress` filtered to `asset_id='ka_gochara_sweep'` confirmed the cited
  counts were correct once `ka_sangam` (an unrelated, week-old asset sharing both
  chart_ids) was excluded: **117/606 (482012f1) and 155/606 (1c826d5a) — accurate**, 489
  and 451 remaining (~44h/~41h at historical per-substep rate).
- Root cause of the idle window: the prior dispatch simply finished its 6h container
  budget cleanly and **no one queued the next resume dispatch** — this is the same
  documented per-dispatch-timeout pattern as PR #1011 (cosmetic `'failed'` DB state,
  substep ledger is truth), not a crash. "Relay is down / hard alarm" framing retracted.

**Action taken (routine, precedented, decoupled from the larger ask):**
1. Collision check: `gcloud run jobs executions list` confirmed zero running executions
   before dispatch.
2. New one-off scripts added (mirroring `dispatch_shaddarshana_c2_gochara_resume_1c826d5a.py`
   / `dispatch_elev_beta_t_gochara_resume.py` exactly — dormant-reset + `build_runs` +
   `build_run_assets` insert only, `build_substep_progress` untouched):
   `platform/scripts/dispatch_int929_gochara_resume_482012f1.py`,
   `platform/scripts/dispatch_int929_gochara_resume_1c826d5a.py`.
3. Dispatched via the real `invokeRunJob()` invocation shape (`platform/src/lib/build/
   jobInvoker.ts`): `gcloud run jobs execute brahma-build-pipeline-job --region=asia-south1
   --args="--run-id,<id>" --update-env-vars="MARSYS_RUN_ID=<id>"`.
   - Chart 482012f1: `build_run acf4a632-6edd-4784-a90a-0727b41e08e7` →
     execution `brahma-build-pipeline-job-z2wtc`, started `2026-08-03T10:23:43Z`.
   - Chart 1c826d5a: `build_run 083e5a04-c05c-4957-a3f1-e8f5541b0c37` →
     execution `brahma-build-pipeline-job-xb8dc`, started `2026-08-03T10:23:45Z`.
4. Verified substeps landing within ~2 minutes on both charts: 482012f1 117→118,
   1c826d5a 155→156 (`ka_gochara_sweep` only).

**Explicitly descoped tonight (native decision, this session):** no Cloud Scheduler / new
production infrastructure at the time (later revisited and built — see the 21:30 UTC entry
above, native-approved in this session's own live conversation); no obligation to run the
full ṢAḌ-DARŚANA swarm, merge lane PRs, or deploy to `main`. Frontier lanes (W2G, W3K, W5,
W4 prep) and the gate chain proceed only when the native deliberately starts a full night
run.

---

## END OF RESTORED CONTENT

Everything below this point (GATE W1 closure record, GATE W0 closure record, the Night 2
MERGE-TRAIN PASS, POST-NIGHT-1 ADVERSARIAL AUDIT, DEPLOY #2, PARĪKṢAKA live-acceptance
rounds, and all earlier campaign history) existed in the deleted file and is **not**
reconstructed here — this session only ever read roughly the first 400 lines of what had
grown into a much longer document. Check `.worktrees/shad-darshana-conductor/
00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/SHAD_DARSHANA_STATE.md` (2445
lines as of this note) for a separately-maintained, likely more complete copy — it is NOT
simply this file's history plus tonight's entries; it has its own diverged narrative and
should be reviewed by the native directly rather than merged automatically by any session.
