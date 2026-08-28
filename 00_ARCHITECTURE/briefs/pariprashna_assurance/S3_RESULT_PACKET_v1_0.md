---
artifact: PARIPRASHNA_S3_RESULT_PACKET
version: "1.1"
status: CHECKPOINT — convergence-ready pass, resumed from a prior self-pause
  under new native authorization; still NOT a full CG-3 result_packet_accepted
  closure (scenarios.executed 47 != scenarios.planned 60 — the tracker gate
  correctly withholds it); NOT seeking closure this pass — convergence (Session
  C) owns that. End state: a clean checkpoint handoff.
stream_id: S3
stream_name: Answer Quality & Epistemic Trust
date: 2026-08-29 (v1.1 resume pass; v1.0 originally authored 2026-08-28)
---

# Stream result packet — S3 (Answer Quality & Epistemic Trust)

Per `templates/STREAM_RESULT_PACKET_TEMPLATE.md`. This packet is a link set to
primary evidence; it is not acceptance until an authorised integrator emits
`result_packet_accepted` with its evidence URI.

## Scenarios planned/executed

**60 planned** (5 fixtures × 12 work classes; ruling recorded in commit
`6b81c8cba`). **47 executed** at LIVE rung (up from 33 at the 2026-08-28
self-pause), tracker `scenario_executed` events S3 stream_seq 7-61. Five
independent batches now: 16 + 17 synthetic (2026-08-28), 8 + 2 real-chart
+ 4 previously-missed synthetic `disagreement` (2026-08-29, this resume).

**This resume's work, under the native's V3-E-012 ruling
(`decision_recorded` `99421811-e13d-4b19-88f4-2cc16d7af220`, "the quality
corpus (`fixtures.ts`) only"):**
1. Ran all 10 runnable real-chart-grounded corpus fixtures (11 total minus
   `door-parity-001`, not runnable regardless) against CURRENT production
   (`https://amjis-web-938361928218.asia-south1.run.app` — confirmed via
   `gcloud run services describe` to be the identical service/revision as
   the legacy `amjis-web-qm256lasva-el.a.run.app` host, same project
   number `938361928218`, same revision `amjis-web-01775-lgg` at 100%
   traffic). Every real-chart call scoped the `--chart-id` override
   STRICTLY from the fixture's own declared `chartId === CANONICAL_CHART_ID`
   (never a separate operator-settable flag), with the ruling's event id
   cited in each execution's tracker evidence. Trace ids (turn_id +
   conversation_id) logged for all 10 —
   `platform/scripts/pariprashna/out/s3_live_corpus_trace_s3resume-batchA.json`
   and `..._batchB.json`.
2. Corrected an earlier-session scoping error: `disagreement`-class
   fixtures were wrongly grouped with the seeding-blocked classes. Checked
   directly — all 5 have zero `priorTurns`, fully self-contained. Ran the
   1 real-chart + 4 previously-missed synthetic ones (5 total).
3. Assessed `priorTurns` conversation-seeding infra cost (task: "build if
   cheap, else park honestly"). Built the mechanism (a real 2-call live
   seed-then-continue in `s3_live_corpus_run.ts`) — cheap to BUILD, but
   empirically NOT reliable: 2 independent seed attempts (`drift-002`,
   `drift-003`) both got intercepted by the door's own `clarification_needed`
   classification path and never produced a usable `conversation_id` — this
   is a live-system behavior, not an engineering-cost problem. **Parked**,
   not fabricated — see §Open A3 decisions.

**Still un-executed: 13 of 60** — `door_parity`'s 5 (G4-B-gated, structurally
excluded from qualification scope regardless), plus 8 across
`returning_conversation_drift`/`prediction_capture_outcome` blocked on the
seeding-infra park note above (drift-002/003 have degraded, unseeded
captures on disk from the assessment attempts — NOT counted as executed
scenarios, since they don't fulfill the fixture's actual test intent).

## Findings and root causes

| ID | Severity | Summary | Status |
|---|---|---|---|
| V3-E-012 | MEDIUM | 11 pre-existing corpus fixtures ground in the native's real chart | **CLOSED-AS-RULED** (2026-08-29) — native authorization received and executed |
| V3-E-016 | CRITICAL | Deployed web door hallucinates the native's real chart facts on a synthetic-chart query | OPEN — **fresh LIVE verdict 2026-08-29: still reproduces identically on current production.** Confirmed mechanically DISTINCT from S5's now-fixed panchang/E-018 leak (E-018 = IDOR on an explicitly-requested real chart_id; V3-E-016 = synthesis-layer hallucination on a correctly-synthetic-scoped request — different route, different layer, different fix shape). Numeric collision with unrelated `S4-V3-E-016` (MEDIUM, `register_leak_lint.ts`) flagged for Session C. |
| V3-E-032 | CRITICAL | Citation precision: 0 trustworthy across all measured live turns | OPEN, filed to S4 — **now 210 total citation attempts / 0 trustworthy across FOUR independent batches (43 fixtures), confirmed on BOTH the synthetic chart and the native's real chart** — closes the one gap the 2026-08-28 refuter panel flagged (chart-specific data-thinness confound). Formally routed to S4 this session (cross-referenced **S3-V3-E-001**; recorded as `reproduction_recorded` `f990078e-c52d-40a7-94c2-79358c30e982` rather than a duplicate `finding_discovered` — this stream's remediation plan was already frozen from the prior session, `FINDING_FREEZE`-blocking a genuinely new finding id; same tracker/process gap S1 flagged earlier). S3-territory scorer-bug half remains CLOSED (PR #1619). |
| V3-E-033 | MEDIUM | `b11_coverage.ts` contradicts its own docblock | OPEN, unchanged — still needs a `bars.ts` design ruling, not rushed |

## Remediations verified/rejected

**Landed 2026-08-28 (unchanged, still merged):**
1. `citation_precision.ts` double-counting fix — PR #1619, merged
   `8a36e32d`, independent verifier ACCEPT (algebraic non-leniency proof).
2. `probe_output_adapter.test.ts` gitignored-file CI failure — fixed in
   the same PR.

**This resume (2026-08-29):** no new code changes proposed — this pass was
corpus execution, live re-verification, and cross-stream routing, not a
fix session. `s3_live_corpus_run.ts` was extended (chart-scoping-from-
fixture-data, priorTurns seeding attempt, trace logging, configurable
service URL) but this is test-harness tooling in S3's own territory, not
yet proposed as a separate PR — bundled with this checkpoint's docs/data
commit.

**Deliberately NOT fixed (S3-owned, filed open, unchanged):**
- V3-E-033 — needs a `bars.ts`/RS-4 design ruling first.

**Referred, not fixed (cross-territory):**
- V3-E-016 / V3-E-032's platform-defect half → S4 (`citation_resolver.ts`
  primary lead), S5 (V3-E-016 privacy/disclosure angle).

## Tracker governance chain

**2026-08-28 (unchanged):** `work_started` → 33× `scenario_executed` → 4×
`finding_discovered` → 4× `finding_triaged` (surrogate) →
`remediation_approved` (4-entry frozen plan) → `remediation_implemented`
(citation_precision.ts) → `verification_accepted` (verifier, ACCEPT) →
`paused` (self-pause, event `4cfe94bd-d713-4790-a94d-b4c809867d90`).

**2026-08-29 resume, this pass:** integrity check on wake — confirmed S3
stream_seq unchanged at 47 (later 61) with zero events from any actor
other than `lead-s3` since the last self-pause; no undisclosed-writer
violation. **Process correction, disclosed:** this resume switched tracker
writes from the `cli.py` wrapper (which instantiates a fresh `EventStore`
directly against the on-disk runtime, bypassing the live server process)
to the mandated `HTTP POST 127.0.0.1:8787/api/events` interface with a
`Bearer` token — the correct interface per this pass's own instructions.
The live server also now enforces a `writer_instance_id`
single-writer-per-stream lease (`stream_scenario_write_leases`, added to
the control plane since the 2026-08-28 pause) that `cli.py`'s bypass path
did not exercise; this resume generated one instance id
(`0b594f19-cd0b-433e-a967-c0525bf24fa6`) and used it consistently for
every `scenario_executed` write this pass. 14× `scenario_executed` (10
real-chart + 4 disagreement) → 1× `reproduction_recorded` (V3-E-032
cross-chart update + S4 routing, `f990078e-c52d-40a7-94c2-79358c30e982`).
No new `finding_discovered` this pass (blocked by the standing
`FINDING_FREEZE` from the already-frozen remediation plan — see V3-E-032
row above).

## Regression evidence

Full corpus test suite: 104/104 at every 2026-08-28 commit (unchanged this
pass — no corpus-library code touched this resume, only the driver
script and documents). PR #1619 remains merged and green.

## Independent verifier verdict

Unchanged from 2026-08-28: **ACCEPT** on PR #1619 (see prior packet
version / EDIR register for the full report). No new code change this
pass required a fresh verification.

## Additional deliverables (test plan §7 dimensions) — updated with resume data

- **Citation density:** unchanged from 2026-08-28 (mean 2.68/100 words,
  n=10) — not re-measured this pass; the real-chart batch's readings are
  available in `s3_live_corpus_trace_s3resume-batchA/B.json` for a future
  pass to fold in.
- **Formal qualification-gate results:** directionally unchanged — the
  2026-08-28 packet's n=33 table (factual/interpretive/predictive NOT
  QUALIFIED on `b11_coverage`/`citation_precision`; sensitive QUALIFIED
  but thin) still holds; the real-chart batch reproduces the same
  `citation_precision: 0` pattern (see V3-E-032 above) but was not
  re-run through `evaluateQualification` per work class this pass — a
  small, cheap follow-up for whoever resumes next.
- **J4 language half:** unchanged (clean qualitative PASS, 2026-08-28
  synthetic-chart sensitive turns). Not re-checked against the real-chart
  `sensitive-001-ayurdaya-longevity` turn this pass — worth a quick look
  next (a real-chart longevity question is exactly the kind of
  higher-stakes case J4 exists to protect).

## Open A3 decisions and residual risks

- **V3-E-012: CLOSED.** No longer open.
- V3-E-033's `bars.ts`/`b11_coverage.ts` design tension: still open,
  unchanged.
- **`priorTurns` seeding: assessed and PARKED, not built.** Concrete
  finding for whoever picks this up: the door's `clarification_needed`
  classifier intercepts standalone prior-turn seed questions before a
  real `conversation_id` is ever established — 2/2 tested seed attempts
  failed this way, including a very specific yes/no question ("Do I have
  Mangal Dosha?"), suggesting the classifier's threshold for "needs
  clarification" may itself be miscalibrated for a first-turn message
  with no established topic (worth a quality observation on its own,
  possibly S2/S4 territory — not chased further here). Also structurally:
  `prediction_capture_outcome`'s `priorTurns` is `assistant`-role-only (a
  claimed PAST prediction) — there is no live mechanism to seed a
  prediction the system never actually made; this class cannot be
  faithfully live-tested without either (a) a genuine multi-session setup
  (ask a real prediction, wait, ask about the outcome later) or (b) a
  direct, riskier conversation-history database seed, neither attempted
  here.
- 13 of 60 planned fixtures remain un-executed: 5 `door_parity` (G4-B
  gate, independent of this stream), 8 seeding-blocked (park note above).
- S4/S5 have not yet responded to the V3-E-016/V3-E-032/V3-E-033/S3-V3-E-001
  referrals as of this packet's authoring.
- The V3-E-012 triple-heading document collision (S1's entry duplicated
  across two merge passes) was cleaned up this session (an orphaned
  heading stub removed, the one complete S1 entry kept) — the underlying
  NUMBER collision between S3's V3-E-012 and S1's own two document-only
  entries is still unresolved and still needs Session C to assign S1
  fresh, tracker-registered ids.
- The V3-E-016 / `S4-V3-E-016` numeric collision (different findings,
  same number) needs the same Session C treatment.

## Checkpoint (not closure)

PR #1619 remains merged; V3-E-012 is closed under native authorization
and executed; V3-E-032 is now confirmed chart-independent and formally
routed to S4; V3-E-016 carries a fresh LIVE verdict distinguishing it from
S5's fixed panchang leak; seeding infra is honestly parked with a precise
diagnosis, not fabricated. Scenarios: 47/60. This is a checkpoint, not a
closure — convergence (Session C) owns the closure decision. Resume point
for whoever picks this up next: (a) build real multi-turn seeding
infrastructure for `returning_conversation_drift` (feasible; `prediction_
capture_outcome` needs a different approach per the note above) or accept
those 8 fixtures as a permanently-excluded class with a governed scope
revision; (b) `door_parity`'s 5 remain blocked on G4-B regardless of
anything S3 can do; (c) once S4 and S5 disposition their referrals,
S3-V3-E-001/V3-E-016/V3-E-032/V3-E-033 can close on the merits; (d) the
two flagged id collisions need Session C's renumbering pass. This packet,
the EDIR register, and the tracker's own event ledger are the durable
state — no handoff text is authoritative over them.
