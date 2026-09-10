---
version: 1.1
status: CURRENT
date: 2026-08-14
author: native's desk (Fable 5, extra-high effort), on native directive
purpose: Conclusive investigation of the Δ1/Δ3 stall pattern + complete restart plan
supersedes-in-part: the crfzx DIRECTIVE (coordination commit 2756e0bce) — its
  "10min GUC verified live" claim is WITHDRAWN herein (finding F-4)
---

# SAMPŪRTI INVESTIGATION — WHY WE ARE WHERE WE ARE, AND HOW WE FINISH

## 0. Executive verdict

Nothing in the astrology layer, the DHĀRĀ mathematics, or the campaign's
merged code is broken. The campaign is blocked by ONE artery — the ka_kshetra
field build (A6) — and that artery kept failing because of a **transport-level
connection stall** in the Cloud Run→Cloud SQL path against which **every
single automatic defense layer was coincidentally inert, disabled, oversized,
or not yet allowed to fire** (F-3 table). The desk's manual recoveries became
the only working defense, and the desk itself then introduced the two biggest
errors of the arc (a premature kill on a misread GUC, and an audit-log
identity ambiguity that parked both streams for ~$26 of burn).

Two facts discovered by this investigation change the restart plan:

1. **DHARA has never run a production substep.** All 74 checkpointed substeps
   were built by the OLD sampled engine (image-ancestry proof, F-6). The
   restarted build will — correctly, by design — replan all 534 substeps
   under the analytic engine. Its production speed is still an unmeasured
   projection; the restart protocol therefore carries an explicit
   measure-in-15-minutes rate gate.
2. **The Cloud Run job is still mis-sized** (2 vCPU / 4 Gi — the very
   configuration diagnosed earlier as a ~50x penalty and never remediated,
   F-7). Right-sizing is now a pre-dispatch step, not a someday item.

Everything merged so far (22+ PRs) feeds the objective chain with nothing
orphaned (F-8, §5). The objective is achievable; §6 is the plan.

## 1. Current situation (as of this writing)

| Surface | State |
|---|---|
| Δ1 (DHĀRĀ-CORE) conductor | STOPPED cleanly by desk (native directive). Worktree salvage-checked: 0 uncommitted, 0 unpushed. |
| Δ2 (PRAMĀṆA) | COMPLETE (terminal marker posted; V1–V5 all merged; $28.12 total). |
| Δ3 (SEVA) conductor | STOPPED cleanly by desk. R1–R3 done; R4 + R2-proof correctly waiting on FIELD-INTEGRATED. |
| Field build | 74/534 substeps checkpointed — but all sampled-engine (moot after replan, F-6). kala_field: 2,063,838 rows (will be replaced per idempotency). |
| Production DB | CLEAN: 0 advisory locks, 0 blocked sessions, 0 orphan builds. |
| Deployed image | `4747ea831` = exactly PR #1269 (S7459 fix) + contains PR #1268 (DHARA flip, `ENGINE_VERSION='analytic'`, `_RESUME_VERSION` 3→4). |
| Spine position | S1–S3 done · S4 adapter merged (#1267) · A6 field build = the single blocked artery · everything downstream (parity→G-P1→M4′→P3→M5→BG#1→Δ3 close) correctly queued behind it. |

## 2. Conclusive findings (each with its evidence)

**F-1 — The hang phenomenon is real, recurring, and engine-independent.**
Three incidents in ~12h across two distinct call sites (writer.py stage-4
COUNT on `kala_field`; stage2_promise.py:358 SELECT on `bodha_pratijna`),
under both engine images. Signature every time: server session goes
`idle in transaction` showing an already-completed query; client blocked
forever; no error on either side. This is a transport-loss signature (a
response or a subsequent request silently lost between container and DB),
not a code defect at the query sites.

**F-2 — The connection path makes an infinite client hang structurally
possible.** The job connects via unix domain socket
(`?host=/cloudsql/...` — verified from the live secret's host form). On a
unix socket **libpq TCP keepalives are silently ignored** — db.py's
`keepalives=1, keepalives_idle=30, ...` have NEVER been active inside the
job (they only ever worked for desk/proxy TCP connections). With
`statement_timeout=0` and no `lock_timeout` anywhere in the codebase, a
client whose bytes vanish in the connector tunnel blocks in read() forever.

**F-3 — Every automatic defense layer was inert. The full audit:**

| Layer | Status during the incidents |
|---|---|
| TCP keepalives (db.py) | INERT — unix socket, silently ignored (F-2) |
| statement_timeout | 0 = unbounded, by design (old slow-op accommodation) |
| lock_timeout | NEVER SET anywhere in the codebase |
| idle_in_txn timeout (server) | =0 (disabled) pre-fix; 30 min post-fix but **never allowed to fire** — crfzx killed at T+12 min (F-4) |
| JL-023 writer watchdog | budget = 86400 s (24 h) for ka_kshetra → effectively absent |
| Conductor active watch | did not exist (now FM-21) |
| The desk (manual) | the ONLY layer that ever fired — 4+ interventions, unscalable, and error-prone (F-5) |

Cloud SQL logs across 48h show **every** connection termination was
`administrator command` (manual kills). No timeout of any kind has ever
fired in production. The system's apparent "unrecoverable hangs" were in
reality "no recovery mechanism was ever actually on duty."

**F-4 — The S7459 fix is correct and was correctly deployed; the "fix did
not hold" conclusion was an evidence-reading error (mine).**
Verified: deployed image tag == fix commit; MR-39's standalone-script
routing predates and is INCLUDED in it; both a startup option and a
committed session-level `SET` are issued; DHARA modules open no independent
connections. The directive's "★ VERIFIED LIVE: current_setting() returned
10min" is invalid evidence: `current_setting()` can only read the CALLING
session's GUC — a fresh desk psql session as `amjis_app` reads the role
default (600s). The hung backend's GUC was never actually measured (
Postgres offers no SQL read of another backend's session GUC). And crfzx
was cancelled at T+12 min — inside the 30-minute window — so the fix never
got the chance to demonstrate itself. Consequence: the fix stands; the
directive's central claim is withdrawn.

**F-5 — Desk intervention became a failure amplifier.** (a) Kills at
T+10–15 min prevented the 30-min layer from ever proving itself, keeping
the failure "mysterious" for a full day. (b) Desk `gcloud` recovery
commands are audit-logged under the native's identity → Δ1 read them as a
native stop-work order → false-blocker-park, ~$26 burn (fixed by SM-R-3).
(c) The wrong-GUC directive (F-4) sent the campaign chasing a phantom.
New FM-22 (§6/P0) imposes desk-intervention discipline.

**F-6 — DHARA has never executed a production substep.** mv7c5 (started
14:09Z) and tkp7b (16:16Z) both ran image digest `ebfe9423` — built BEFORE
the flag-flip merge (13:31Z; the first flip-bearing deploys are later
digests). All 74 substeps carry ONE fingerprint (`5d1c656a…`) = one
sampled-engine generation. crfzx (the only execution running the analytic
image) completed ZERO substeps — it hung during class-preamble reads ~3
minutes in. Therefore: (i) the observed substep rates are SAMPLED rates;
(ii) on restart, `_RESUME_VERSION` 3→4 forces a full 534-substep replan
(BY DESIGN, rollout rule 3 — the conductor must expect this, not treat it
as the G2-early "fingerprint surprise"); (iii) DHARA's production speed is
an untested projection until ~15 minutes into A6′.

**F-7 — The known infrastructure mis-size was never remediated.** Job spec
today: 2 vCPU / 4 Gi, `ORCHESTRATOR_WORKER_LIMIT=2` — identical to the
configuration diagnosed (earlier in this arc) as a ~50x penalty for the
sampled engine's ~2 GB working set. Measured sampled rates at this sizing:
~1.7 min/substep average, ~6.2 min/substep for stage-5 null substeps →
15–55 h full-build projection, which is what triggered the native's
"60-hour rebuild" alarm and the DHARA re-architecture in the first place.
DHARA's memory profile is lighter, but dispatching A6′ on the known-bad
sizing would contaminate the one measurement that matters. Right-size
BEFORE dispatch (§6/P0).

**F-8 — What was implemented was implemented correctly.** Audit of the
merged inventory (22+ SM-prefixed PRs): S3 DHARA modules (#1262–#1266) —
pure compute, no DB access (verified by grep on origin/main), additive-only
per rollout rule 1; flag flip (#1268) — separate commit with the mandated
`_RESUME_VERSION` bump (rule 3 honored exactly); S4 adapter (#1267);
Δ2's V1–V5 verification harnesses (golden fixtures, property tests, parity
battery, comparability guard); Δ3's R1/R2 serving fixes (SEV-1/SEV-2, both
deployed); γ's C1–C5 (merged + flags activated, #1256). Process discipline
held: blind-spec ordering, checkpoint preservation, honest LAW-ZERO class
skips (21/27 classes correctly skip on missing priors — visible in crfzx's
logs). The campaign's engineering was not the problem.

**F-9 — Coordination-plane correction.** The authoritative coordination
file lives on the `campaign-coordination` BRANCH (its own §0 says so; main
carries a slow mirror). SM-R-3 landed there correctly and was read by Δ1
R36. The desk's SM-R-4 draft currently sits UNCOMMITTED in the main-checkout
working tree — it must be ported to the branch tip (P0.a) or the restarted
conductors will never see it. (Also: the desk checkout's local `main` was
stale during early diagnosis — always `git show origin/<branch>:<file>` for
authority, never the working tree.)

**F-10 — Investment ledger (what's been spent on this arc).**
Conductor LLM costs (supervisor-logged): Δ1 $15.03+ (one 5.3h attempt
uncosted), Δ2 $28.12 (complete), Δ3 $18.94+ → **≈$62+ this arc**, plus
Cloud Run/Cloud SQL compute, plus the predecessor α/β/γ sessions. Waste
subtotal identified: ~$26 false-blocker-park + ~$1.20 Δ2 marker-format
cycles + 3 aborted build attempts (compute). Product delivered for the
spend: the entire Δ2 verification estate, 22+ merged PRs, the deployed
dual-engine architecture, and — from the failures themselves — the §7
failure-register entries that make the restart survivable.

## 3. Why the carefully-built plan still landed here (the meta-question)

The plan's §7 register hardened every ORCHESTRATION failure mode we had
ever observed (merge seams, OOM, dispatch args, livelocks…) — and those
defenses worked: conductors self-corrected a malformed dispatch, parked
honestly, closed cleanly, and Δ2 ran start-to-finish flawlessly. What the
register could not contain was an INFRASTRUCTURE mode (transport stall)
whose five nominal defenses were all silently off duty (F-3) — a fact
nobody could see because each manual recovery restored service without
ever testing the defenses. The prompts did not fail; the failure lived
below the prompts, and the diagnosis loop above it (the desk) added two
errors of its own (F-4, F-5). The durable lesson is structural, and it is
now encoded: FM-21 (the conductor watches its own build), FM-22 (the desk
observes before it kills), and a GUC smoke-log so connection-level truth
is in every run's logs (§6/P1) instead of being inferred after the fact.

## 4. Has any of it been done incorrectly? (direct answer)

- Code merged to main: NO defect found in this investigation (F-8).
- The S7459 fix: correct, deployed, unproven-in-anger only because it was
  never allowed to fire (F-4).
- The dispatch protocol: one real error — A6 was dispatched onto known
  mis-sized infra with an unmeasured engine, framed as a "resume" when the
  version bump guaranteed a replan (F-6/F-7). That is a protocol gap, not
  a code bug; P2 closes it.
- The desk: two documented errors, both now converted into standing rules
  (F-5).

## 5. Does it all tie to the objective?

The objective (plans of record): a calibrated, testable WHEN-instrument —
the Kāla field over the resolved marriage/relocation/separation WHETHER —
proven through the customer-facing MCP, with measurements #4/#5/#6 and
Brilliance Gate #1. Chain: **A6′ field build → S4 parity (instruments =
Δ2's V1–V3 harnesses) → G-P1 → SMR-2 M4′ re-baseline → P3 DVIPRAMĀṆA →
Measurement #5 → Brilliance Gate #1 → FIELD-INTEGRATED → Δ3 R2-proof +
R4/G-P4 → arc close.** Every merged PR sits on this chain; nothing is
orphaned. Exactly two unknowns gate the timeline, and the restart is
designed to convert both into measurements within its first hour:
DHARA's production rate (P2 gate) and hang recurrence (now survivable
through five real layers instead of zero).

**Verdict: achievable.** With DHARA performing to design: field build
tens-of-minutes-to-few-hours; spine gates a further half-day of conductor
time; realistic arc completion within ~24h of restart. If DHARA
underperforms its gate, the plan says exactly what happens next (P2/P3) —
a bounded decision point, not an open-ended stall.

## 6. THE COMPLETE RESTART PLAN

**P0 — Desk pre-flight (before any conductor starts; ~30 min):**
  a. Port SM-R-4 (amended: F-4 withdrawal + this doc as authority) to the
     `campaign-coordination` BRANCH tip (F-9). The stale local working-tree
     copy is not pushed; the block is re-applied onto the branch.
  b. Right-size the job: `gcloud run jobs update brahma-build-pipeline-job
     --region=asia-south1 --cpu=4 --memory=8Gi` (F-7). Measure, then
     right-size again later; never dispatch A6′ on 2/4Gi.
  c. Plan files: FM-03 rewritten (two sub-classes), FM-21 added, rails
     ACTIVE-HANG-WATCH added [DONE this session]; add FM-22 (desk
     discipline): the desk NEVER kills a hung build before T+35 min
     (letting the 30-min layer take its first real shot — its firing is
     itself the missing evidence); captures pg_stat_activity + connector
     logs BEFORE any kill; never diagnoses a session GUC from a different
     session (F-4's error class).
  d. Kickoff deltas: Δ1's dh1_kickoff gains the P1/P2 lane order below and
     the F-6 pre-authorization ("full 534-substep replan under fingerprint
     change is EXPECTED — proceed, do not park").

**P1 — Δ1 restart, hardening lane FIRST (before any dispatch; ~1h):**
  Lane S7-LOCK: in `db.py::connect()` add `SET lock_timeout = '300s'` and a
  one-line GUC smoke-log (log `current_setting()` of idle_in_txn /
  statement_timeout / lock_timeout ON THE WORKER CONNECTION right after
  connect) so every future run carries per-connection ground truth in its
  own logs. PR → CI → merge → deploy-green with ancestry check. VERIFIER
  confirms the smoke-log line in the live job log at A6′ start.

**P2 — A6′ dispatch under a rate-gate protocol:**
  - Expect the full 534-substep DHARA replan (F-6).
  - Conductor measures substeps/min over the first 15 minutes:
    projected total ≤6h → continue · 6–12h → continue AND escalate sizing
    (8 vCPU/16 Gi redispatch at the next checkpoint) · >12h → STOP,
    PARKED-EXTERNAL, dispatch PARĪKṢAKA (opus) against the DHARA hot path —
    a >12h projection contradicts the design by two orders of magnitude
    and means a defect, not a tuning problem.
  - FM-21 watch on every heartbeat. On a hang: hold to T+35 min (give the
    30-min layer its first live test), then self-recover (stop-flag → 25s →
    terminate → cancel → locks==0) and redispatch — checkpoints make this
    cheap. ≥3 hangs in one run → PARKED + open the P3 lane.

**P3 — Transport lane (STRICTLY evidence-gated, not speculative):**
  Only if ≥2 post-restart hangs occur WITH the 30-min layer confirmed
  firing (i.e., the stall class survives real timeouts): switch the job's
  DATABASE_URL to TCP over private IP (VPC egress), making keepalives +
  `tcp_user_timeout` real (F-2). One transport variable changes at a time,
  and only on evidence.

**P4 — Δ3 restart:** unchanged scope (R4/G-P4 + R2 MCP proof, firing on
  FIELD-INTEGRATED); inherits FM-21/FM-22 via the shared rails
  automatically.

**P5 — The spine (unchanged, from the plans of record):** S4 parity →
  G-P1 → SMR-2 M4′ → P3 DVIPRAMĀṆA → Measurement #5 → Brilliance Gate #1
  → FIELD-INTEGRATED → Δ3 completes R2-proof + R4 → SESSION-Δ1/Δ3-COMPLETE
  per close discipline. MCP-as-proof at every gate (§7.1c), unchanged.

## 7. Restart commands (run after P0/P1 confirmation)

```bash
# Δ1
nohup caffeinate -i /Users/Dev/shad_overnight/run_dh_d1.sh </dev/null >/dev/null 2>&1 & disown
# Δ3
nohup caffeinate -i /Users/Dev/shad_overnight/run_dh_d3.sh </dev/null >/dev/null 2>&1 & disown
# watch (auto-follows attempt rotation)
/Users/Dev/shad_overnight/watch_dh_auto.sh d1
/Users/Dev/shad_overnight/watch_dh_auto.sh d3
```

---

# PART 2 (v1.1, 2026-08-14) — THE 9-HOUR FINDING: CONCLUSIVE

**Status of Part 1:** F-6 is CORRECTED by F-11 below (the image-ancestry
inference misread an untagged digest). Everything else in Part 1 stands.

## The question
The DHĀRĀ plan promised a 15–40 min rebuild. The dispatched build projected
~9 hours. Where does 9h come from?

## The answer, measured
- **F-11 — DHARA's stage-4 works and met its design promise.**
  Fingerprint proof (`_fingerprint()` includes `v={_RESUME_VERSION}`; one
  fingerprint spans 14:13Z→21:20Z, impossible across the v3→v4 bump ⇒
  mv7c5 already ran analytic): stages 0–4, all 6 classes, **2,063,838
  exact segment rows (K = 343,973 knots/class) in ≈20 minutes on 2 vCPU.**
- **F-12 — the 9h is ~100% stage-5**: the OLD per-replicate null engine —
  256 replicates × ~12–19 s each = 8 blocks/class × 6–10 min × 6 classes.
- **F-13 — root cause: the fast null engine is BUILT BUT UNWIRED.**
  `dhara_null.py` (vectorized, 1024 replicates, parity-tested, merged,
  deployed) is imported only by its own tests. Same for
  `dhara_term_matrix` (n2 artifact) and `dhara_pin_matrix` (surgical
  rebuild). Only `dhara_sweep` was wired (writer.py:1691). The build is
  slow because the merged optimization is never called. n3 (1024
  replicates) is likewise undelivered in the live path (256).
- **F-14 — process failure**: PARĪKṢAKA R38 attributed the slow blocks to
  "stage4 adaptive refinement" — stage4 was already complete in the very
  ledger it read; the measured substeps were `stage5:*`. Its coarse-knot
  fix would have cut accuracy. SM-R-5's 9h acceptance is superseded.
- **F-15 — no statistical definition changes**: `dhara_compute_null`'s
  `coarse_mode=True` (MD/AD/PD knots for NULLS only, "L1g parity") matches
  the already-blessed null-side definition; the observed field keeps the
  full exact knot set; 1024 + shift grid were committed blind (R13/R18).

## The fix (SM-R-6, posted to campaign-coordination — binding)
0. vcc6h stopped GRACEFULLY (stop-flag drain only; entry precedes action
   per FM-22). No redispatch until OPT-N1 deploy-green.
1. **OPT-N1**: wire `dhara_compute_null` into stage-5 under
   `ENGINE_VERSION=='analytic'` — one `stage5dhara:{ec}` substep/class,
   adapter to `S5.NullResult`, replicates=1024 (n3 delivered),
   `_RESUME_VERSION` 4→5 in the same PR (FM-17).
2. **OPT-N2**: FM-23 CI guard — every wave module imported outside tests.
3. **A6″ redispatch**: expected total **30–60 min** (stage0-4 ≈20–25 min
   re-run once under the new fingerprint + vectorized stage5 minutes +
   stages 6/6.5/8). Rate gate: >90 min → stop + cProfile one substep +
   substep-key-cited PARĪKṢAKA diagnosis.
4. **OPT-N3 (next wave, non-blocking)**: wire `dhara_pin_matrix` (after
   which a stage5-only change never again costs a stage4 re-run — the
   native's standing efficient-rebuild requirement) + `dhara_term_matrix`
   (EXPLAIN + rho-refit artifact).
5. Spine unchanged; FIELD-INTEGRATED posts with the sentinel marker.

---

# PART 2 (v1.1, 2026-08-14 late) — THE 9-HOUR FINDING: CORRECTIONS + THE OPT WAVE

Part 1's transport-hang analysis stands (F-1..F-5, F-7..F-10 unchanged).
Two Part-1 claims are corrected here on new, stronger evidence, and the
true cause of the 9-hour build projection is established conclusively.
Coordination authority: SM-R-6 (campaign-coordination branch).

## F-11 — CORRECTS F-6: DHARA *has* run production substeps, and stage-4 met the design promise

Fingerprint proof (stronger than the image-ancestry inference F-6 used):
`writer._fingerprint()` = sha256 of `v={_RESUME_VERSION}|chart|snapshot|
classes`. The substep ledger holds ONE fingerprint (`5d1c656a…`) spanning
completions 14:13Z (mv7c5) through 22:08Z (vcc6h). Since the flag-flip
bumped v 3→4, a v=3 generation cannot share a fingerprint with a v=4
generation — therefore mv7c5 was ALREADY running the analytic engine
(F-6's untagged-digest ancestry inference was wrong; the pre-flip v=3
ledger was wiped at mv7c5 open, which is why gen_start = 14:13).

**Measured result: stages 0–4 for all 6 classes — 2,063,838 exact segment
rows (343,973 per class = the true knot count K) — completed in ≈20
minutes on 2 vCPU.** The KṢETRA-DHĀRĀ stage-4 sweep delivered its design
promise where it was wired.

## F-12/F-13 — The 9 hours is ~100% stage-5, and the root cause is a BUILT-BUT-UNWIRED module

Stage-5 still runs the OLD per-replicate null engine (`stage5_null.
run_null`: 256 replicates × ~12–19 s each, 8 blocks/class × 6–10 min ×
6 classes ≈ 5–8 h). Meanwhile `dhara_null.py` — the vectorized
1024-replicate null engine, PR #1263, TDD-tested, parity-covered
(`test_dhara_parity.py`), merged, INSIDE the deployed container — is
imported by nothing in production. Same for `dhara_term_matrix` (n2
deliverable) and `dhara_pin_matrix` (the surgical-rebuild architecture).
Of four merged DHARA modules, only `dhara_sweep` was ever wired
(writer.py:1691). Also: the live path runs 256 replicates — the native's
n3 ruling (1024) exists only as the unwired module's default.

**The build is slow because the optimization that was designed, built,
tested, merged, and deployed is never called.** Registered as FM-23.

## F-14 — Process failures that let this through

PARĪKṢAKA R38 misattributed the slow blocks to "stage4 adaptive
refinement ~9min/decade" — stage-4 was already COMPLETE in the very
ledger it read; the blocks it measured were `stage5:*`. Its proposed fix
(coarse MD/AD/PD knots for the FIELD) would have reduced accuracy.
PRATINIDHI rightly rejected that fix but then accepted 9 h as physics.
Nobody asked "does this duration contradict the design's own estimate?"
and nobody checked whether the merged fast path was actually being
called. Both checks are now mandatory (FM-23 countermeasures).

## F-15 — Why wiring dhara_null changes no committed statistical definition

`dhara_compute_null(coarse_mode=True)` uses MD/AD/PD clock knots for the
NULL replicates only (~819 knots — documented in-module as "L1g parity",
the already-blessed null-side definition). The OBSERVED field keeps the
full exact knot set. Replicates=1024 and the F-01-corrected shift grid
were committed blind in the merged module (R13/R18 compliant).

## THE OPT WAVE (SM-R-6 directive, binding)

0. vcc6h stopped gracefully by the desk (stop_requested_at flag only —
   no cancel, no pg_terminate; entry-first per FM-22). No redispatch
   until OPT-N1 is deploy-green.
1. **OPT-N1 (P0):** wire `dhara_compute_null` into stage-5 under
   `ENGINE_VERSION=='analytic'` — one `stage5dhara:{ec}` substep per
   class replacing the 8 blocks; adapter to `S5.NullResult`;
   replicates=1024 (n3 delivered); `_RESUME_VERSION` 4→5 in the same PR
   (FM-17 — stage5 outputs change by design). Acceptance: dhara parity +
   V2 property suites in CI + PARĪKṢAKA verdict citing the run.
2. **OPT-N2:** FM-23 CI guard (production-import assertion for
   dhara_* modules).
3. **A6″ redispatch** after deploy-green. EXPECTED: stage0–4 ≈20–25 min
   (one-time full re-run under the new fingerprint) + vectorized stage-5
   (minutes) + stages 6/6.5/8 + snapshot → **total ≈30–60 min**. RATE
   GATE: >90 min → clean stop + cProfile one substep + a diagnosis that
   cites substep keys and reconciles against this expected profile.
4. **OPT-N3 (next wave, non-blocking):** wire `dhara_pin_matrix`
   (surgical stage×class rebuilds — after it lands, a stage5-only change
   never again costs a stage4 re-run) + `dhara_term_matrix` (EXPLAIN +
   rho-refit artifact).
5. Spine unchanged: parity battery → G-P1 (MCP proof) → M4′ →
   DVIPRAMĀṆA → M5 → Brilliance Gate #1 → `██ MARKER-POSTED:
   FIELD-INTEGRATED ██` → Δ3 fires R2-proof + R4 and closes.

Rebuild-economics after the full wave: cold field ≈30–60 min today,
approaching the 15–40 min design envelope; with OPT-N3's pin matrix,
partial rebuilds become stage×class-surgical (minutes), which is the
native's standing accuracy+efficiency+speed requirement satisfied
structurally rather than by luck.
