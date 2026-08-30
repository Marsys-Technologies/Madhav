---
artifact: PARIPRASHNA_V3_FINAL_CLOSE_REPORT_v1_0.md
canonical_id: PARIPRASHNA_V3_FINAL_CLOSE_REPORT
version: 1.0
status: SEALED
campaign: pariprashna-experience-assurance-v3
campaign_name: "Paripraśna Experience Assurance Programme v3.0"
date: 2026-08-30
sealed_by: closeout session (final close), on the native's explicit acceptance instruction
authority: NATIVE acceptance fired 2026-08-30T03:14:33Z (CG-6), event 949026fb-e2f2-412a-bc69-e826d4bb285e
supersedes: >
  Nothing. This is the terminal record of the v3.0 campaign. CG6_NATIVE_ACCEPTANCE_PACKET_v1_0.md
  remains the pre-acceptance decision packet and is cited, not replaced, by this report.
changelog:
  - version: 1.0
    date: 2026-08-30
    change: >
      Initial seal. Records the CG-0..CG-7 gate ledger with closing event ids and timestamps;
      the headline V3-E-016 real-chart context leak and the related V3-E-061 red-team fix; per-stream
      S1-S6 outcomes with scenarios executed vs. honestly excluded and per-item exclusion reasons;
      every Surrogate ruling and both native rulings; the residuals carried forward with owners or
      accepted-risk notes; the campaign's own process lessons; and the closing tracker integrity hash.
---

# Paripraśna Experience Assurance Programme v3.0 — Final Close Report

**Status: SEALED.** All eight campaign gates (CG-0 … CG-7) are CLOSED. Native acceptance was
fired by the native's own `native_acceptance` event on 2026-08-30. The control plane's
replay-integrity check reads `ok: true` at seal.

This report is written from the live event ledger (`/api/projection`, `/api/integrity`, and a
read-only replay of `control-plane.sqlite3`), not from any session's self-report. Where a
session's own record disagreed with the ledger, the ledger is quoted and the disagreement is
stated — that discipline is the substance of this campaign, so this report holds itself to it.

---

## §1 — Final gate ledger

Every gate below is CLOSED. `gate_closed` events are written by the `PROGRAMME_INTEGRATOR`
against the gate's own phase stream, each linked to a distinct `INDEPENDENT_VERIFIER`
`verification_accepted` event — the control plane rejects a gate closure that lacks one
(`VERIFICATION_REQUIRED`), and rejects a verifier who is also the finder or fixer
(`SELF_VERIFICATION`). CG-6 is the one gate that cannot be closed by `gate_closed` at all: the
validator raises `NATIVE_REQUIRED` and admits only the native's own `native_acceptance` event.

| Gate | Name | Status | Closing event id | Closed at (UTC) | Closed by | Stream#seq |
|---|---|---|---|---|---|---|
| CG-0 | Control Plane Ready | CLOSED | `ee77f1de-005b-4055-9be1-809d6324c182` | 2026-08-24T21:15:13Z | `integrator-p0b` | P0#4 |
| CG-1 | Takeover Reconciled | CLOSED | `62438a38-6c6e-4da8-9ce5-18bfc83e49d1` | 2026-08-25T21:03:56Z | `integrator-p1` | P1#13 |
| CG-2 | Safe to Test | CLOSED | `031e03fc-7685-4c17-af34-bba115318246` | 2026-08-27T21:22:05Z | `integrator` | P2#32 |
| CG-3 | Stream Complete | CLOSED | `b4bcea81-3a53-4557-baec-ef6f03385f8e` | 2026-08-29T20:25:15Z | `integrator` | P3#3 |
| CG-4 | Integrated Assurance | CLOSED | `2a2f11b0-1238-49f7-b292-a344951a961a` | 2026-08-29T20:39:32Z | `integrator` | P4#6 |
| CG-5 | Operationally Proven | CLOSED | `cb3ee071-3f4e-49f0-a241-63c107e3bd54` | 2026-08-29T20:50:23Z | `integrator` | P5#3 |
| **CG-6** | **Native Accepted** | **CLOSED** | **`949026fb-e2f2-412a-bc69-e826d4bb285e`** | **2026-08-30T03:14:33Z** | **`native`** (role `NATIVE`) | **P6#5** |
| CG-7 | Release Closed | CLOSED | ``fc190e0e-7f12-4a35-a17e-51418868ffad`` | `2026-08-30T03:23:25Z` | `integrator` | P7#`3` |

**Linked independent verifications** (the evidence each gate closure rests on):

| Gate | Verifier event id | Verified at (UTC) |
|---|---|---|
| CG-3 | `638f2c91-11c9-451a-b8b9-10417d984eb0` | 2026-08-29T20:21:47Z |
| CG-4 | `d87d6bcb-08eb-4b4a-8a87-8b05e9f01448` | 2026-08-29T20:39:14Z |
| CG-5 | `b504f419-c134-4ea8-b73f-3b55a90a7bd8` | 2026-08-29T20:50:23Z |
| CG-6 (P6 evidence) | `7e32a45f-c91b-467e-a581-e3811acb3b37` | 2026-08-30T03:06:14Z |
| CG-7 | ``809df40d-df38-487c-84a5-ebe4900a6986`` | `2026-08-30T03:23:03Z` |

**Phase completion at seal** (from the live projection, all eight phases):

| Phase | Name | Weight | Completion | Work items |
|---|---|---|---|---|
| P0 | Campaign Control and Live Tracker | 5 | 100% | 1/1 |
| P1 | Previous-Campaign Takeover and Reconciliation | 8 | 100% | 1/1 |
| P2 | Known-Blocker Clearance and Safe-to-Test | 17 | 100% | 1/1 |
| P3 | Six Parallel Closed-Loop Streams | 45 | 100% | 42/42 |
| P4 | Integration and Cross-Stream Regression | 10 | 100% | 1/1 |
| P5 | Long-Window Canary and Operational Evidence | 7 | 100% | 1/1 |
| P6 | Native Acceptance | 5 | 100% | 1/1 |
| P7 | Release Decision and Campaign Closeout | 3 | 100% | 1/1 |

**Campaign completion at seal: 100.0%** (`earned_campaign_points` 100.0 / `planned_campaign_points`
100.0). The 97% reading that stood immediately before this session was correct and honest at the
time: P7's 3 campaign points were genuinely unearned, because P7's evidence — this report — did not
yet exist. It was not withheld by a bookkeeping gap.

---

## §2 — The headline finding: V3-E-016, the real-chart context leak

### What it was

The native's own private chart corpus — approximately **79 KB** of Chart Gestalt Map and other
native-bound documents belonging to chart `482012f1-710e-4a25-994a-93821f5871aa` — was being
injected, unscoped, into the synthesis system prompt of **every** chart query the product served.

The mechanism was a data-flow leak rather than an authorization bypass: the corpus-assembly path
selected native-bound assets without gating them on the chart actually under query. Compounding it,
`public.charts.native_id` carried `DEFAULT='abhisek'` on all six production rows, so nothing
downstream could distinguish "this chart's native" from "the native."

### Blast radius (measured, not estimated)

- **5 of 6 production charts** received the corpus in their synthesis prompts.
- **4 of those 5 belong to other real people** — this was a genuine third-party exposure, not a
  self-exposure or a synthetic-fixture artifact.
- The exposure window was live for approximately **16+ hours** before the resuming session began.
- Severity CRITICAL, discovered on stream S3, with the same underlying defect separately carried
  as **B1** in S5's security lane and as **V3-E-032** (CRITICAL, S3, root-cause group `V3-E-016`).

### The fix

**PR #1655** — "Pariprashna V3 B1: fix V3-E-016 real-chart context leak (CRITICAL, S3)" — merged
`693536e9342be31331a8529874c62084b36c8027` at 2026-08-29T17:06:53Z. The fix introduces a dedicated
scope layer, `platform/src/lib/bundle/native_corpus_scope.ts`, which gates native-corpus asset
access on the chart binding rather than on the ambient `native_id` default, plus a real-manifest
test (`platform/src/__tests__/lib/bundle/native_corpus_scope.real_manifest.test.ts`).

### Proof, at the strongest tier available

- **Pre-merge:** RED→GREEN across the actual affected code path, mutation testing, and a dedicated
  NO-LEAKAGE canary gate. The RED→GREEN proof was captured across three independent turns
  (production RED, local RED control, local GREEN) — a control that distinguishes "the fix works"
  from "the test environment differs."
- **Post-merge, live:** re-proofed on the deployed Cloud Run revision, and re-confirmed again during
  the CG-5 whole-product live pass.
- **Independently ratified twice:** Native Surrogate ruling `fb54d19b-…` (RATIFY as fixed and
  verified for the full 6-chart blast radius) and Independent Verifier event `209addec-…`
  (`verification_accepted`, `finding_id: V3-E-016`).

### Live re-proof at seal (this session, independently re-derived)

Verified in this closing session rather than inherited from any prior report:

- Fix commit `693536e93` is an **ancestor** of the currently deployed SHA (`git merge-base
  --is-ancestor` → true).
- The deployed Cloud Run revision is `amjis-web-01805-mhr`, image tag
  `5f112179373a16ccffbd18aa3347f0771bf86bd4`, `commit-sha` label identical — i.e. **production is
  at `origin/main` HEAD** and carries the fix.
- `native_corpus_scope.ts` and its real-manifest test are both present on `origin/main`.

### Forensic follow-up on actual capture

A full database forensic check found **zero evidence that any exposed content was ever captured or
persisted anywhere retrievable** on the four affected real charts: three had no conversations at
all, and the one that did was an empty shell with zero messages. This does not erase the exposure
window — it bounds the downstream harm, and it was the material fact behind the native's disclosure
ruling (§4).

### The related red-team fix: V3-E-061

A mandatory red-team pass this session found that the **citation-redaction path could fail open** —
under the failure branch it emitted genuine content rather than a redacted token. This was proven
with a synthetic PII-shaped test token, not asserted from code reading.

**PR #1659** (merged 2026-08-29T19:15:32Z) makes the path fail **closed**, architecturally, rather
than by extending a pattern list — a pattern list can only redact what it anticipates.

Surrogate ruling `d9fd0274-…` graded it honestly: **COMMISSION_FIX_THIS_CAMPAIGN**, explicitly *not*
an emergency fast-path — it is a real defect and a real fail-open, but unlike V3-E-016 it is not a
confirmed data exposure. Calling it one would have been the padding this campaign exists to prevent.

---

## §3 — Per-stream outcomes (S1–S6)

All six streams reached `lifecycle: COMPLETE` at 100% with an accepted `result_packet_accepted`
event, an independent `stream_closure_recommended`, and every non-closure work item accepted.

**A necessary honesty note on the scenario denominators below.** The tracker has no
denominator-reduction event type. A scenario that is genuinely unreachable is therefore recorded as
a `scenario_executed` event carrying `outcome: STRUCTURALLY_EXCLUDED` and a per-item reason. This
means the projection's `scenarios.executed` counter reads 60/60 for S3 and 31/31 for S6 while the
truthful reading is **47 substantively executed + 13 structurally excluded** and **14 + 17**
respectively. The exclusions are individually enumerated in §3.7 below. Excluded is not failed, and
it is also not executed — this report refuses to let the counter say otherwise.

### §3.1 — S1 · Navigation, Shell and History

- **Lifecycle:** COMPLETE, 100%. **Scenarios:** 10 executed / 10 planned, zero exclusions.
- **Fixes landed:** 2 real fixes — **PR #1610** and **PR #1614**. #1614 wired
  `PariprashnaApp.tsx` to real persisted conversation history via
  `GET /api/conversations?readingsOnly=true`: the sidebar thread list had been derived purely from
  in-memory `state.turns`, so a page reload lost all history even though the `conversations` rows
  persisted correctly server-side. The same PR guards the pre-existing rename affordance against a
  mis-target bug the fixer caught in its own work while landing it.
- **Governance note:** S1-V3-E-012a was admitted *after* S1's remediation plan had frozen, via the
  campaign's one and only `finding_freeze_exception_granted` event (`830dec98-…`, authorized by the
  Surrogate) — a governed scope path, not a quiet reopen.
- **Residuals:** (a) breadcrumb colour-contrast (axe SERIOUS) in
  `platform/components/shared/AppShellBreadcrumb.tsx` — deferred with named ownership, outside S1's
  chartered territory (ruling `dffa00e4-…`); (b) a CI-retargeting process gap — stream-branch PRs
  receive **zero CI** unless retargeted to `main` or added to `ci.yml`'s `pull_request.branches`
  allowlist, discovered when #1614 initially targeted its own stream branch and silently got no CI
  run at all (ruling `026445b6-…`).

### §3.2 — S2 · Conversation and Reading Experience

- **Lifecycle:** COMPLETE, 100%. **Scenarios:** 30 executed / 30 planned, zero exclusions.
- **Fixes landed:** 5 pre-session fixes plus 2 this session (**PR #1661**). V3-E-062 fully fixed;
  V3-E-060 **partially** fixed with the residual disclosed rather than rounded up to "fixed".
- **Dispositions:** 1 duplicate voided; 2 referred to S4 (V3-E-014, V3-E-021); 1 deferred pending a
  native/design decision; 1 escalated externally as V3-E-061 (§2).
- **Residual:** V3-E-060's unfixed half, honestly recorded in the stream's own closure ceremony
  record (v3.0 → v4.0 CLOSED, PR #1663).

### §3.3 — S3 · Answer Quality and Epistemic Trust

- **Lifecycle:** COMPLETE, 100%. **Scenarios: 47 substantively executed, 13 structurally excluded,
  of a frozen denominator of 60** (5 fixtures × 12 work classes).
- **Findings:** the headline leak under S3's own numbering; **V3-E-032** (CRITICAL, root-cause group
  `V3-E-016`) confirmed fixed via S4's PR #1646; **V3-E-033** (MEDIUM) Surrogate-ruled to adopt the
  docblock's stated intent as authoritative rather than re-score (`f1a63de7-…`); **V3-E-012**
  authorized by native ruling (`99421811-…`) to ground the quality corpus in the native's real chart.
- **The 13 exclusions, with per-item reasons** (ruling `bd5946c2-…`, which recomputed the count
  against the frozen 60 and arrived at exactly 60−13=47, matching what had already been executed —
  the count was derived, not fitted):
  - **5 × "G4-B roadmap gate not landed"** — `door-parity-001-lagna-sign`, `-002-sun-sign`,
    `-003-jupiter-house`, `-004-moon-nakshatra-pada`, `-005-saturn-sign`.
  - **4 × "clarification_needed classifier intercept"** — `drift-002-mercury-combust-then-dasha`,
    `-003-manglik-cancelled-then-matchmaker-pushback`,
    `-004-jupiter-neecha-bhanga-then-residual-weakness`, `-005-saturn-rahu-dasha-then-whats-next`.
    The chat door's own clarification classifier intercepted the seeding turn; this is real live-system
    behaviour, reproducible, not a harness defect.
  - **4 × "no live seeding mechanism for an assistant-role past-prediction claim"** —
    `outcome-002-saturn-venus-ad-2017-2020`, `-003-saturn-sun-ad-2020-2021`,
    `-004-saturn-moon-ad-2021-2022`, `-005-saturn-rahu-ad-2023-2026`.

### §3.4 — S4 · Pipeline Correctness and Door Parity

- **Lifecycle:** COMPLETE, 100%. **Scenarios:** 54 executed / 54 planned, zero exclusions.
- **Volume:** 44 of the campaign's 73 findings originated here.
- **Fixes landed:** 10 real fixes — PRs **#1620–#1624** (pre-session) and **#1643–#1645** (this
  session), plus **#1646** which closed S3's V3-E-032.
- **Adversarial catch:** **S4-V3-E-056** (CRITICAL) was absorbed through a genuine
  REJECT → fix → ACCEPT cycle — the independent verifier rejected the first submission and the
  finding was only accepted after the rework. It was admitted post-freeze only after being correctly
  refused at the freeze boundary (`FINDING_FREEZE` rejection, ledger-recorded).
- **A recording defect caught by verification, not by self-report:** one referral's justification
  text had been copy-pasted from a *different* finding. The independent verifier caught it; it was
  corrected on the ledger (`correction_recorded a940722c-…`, restating what V3-E-042 is actually
  about) and re-verified.
- **Dispositions:** 6 referred cross-territory; 1 already tracked elsewhere; 1 no-action-needed;
  30 honestly deferred with reasons.

### §3.5 — S5 · Security, Privacy and Data Integrity

- **Lifecycle:** COMPLETE, 100%. **Scenarios:** 45 distinct slots executed / 45 planned — from **53
  recorded `scenario_executed` events**. The 8-event gap is the concurrent-writer defect and its fix,
  documented in §6.2; it is not padding and not double-counting in the final figure.
- **Fixes landed:** 9 findings, all fixed and merged — including **PR #1615**, which the Surrogate
  ruled (`5e1a5a17-…`) to **EXTEND** beyond its original empty-table scope to cover two live
  data-bearing tables (364 + 195 real rows), and which the Surrogate then re-verified against the
  *actual diff* at head `5e2cee5d…` rather than against the report describing it (`b03625f4-…`).
- **Evidence-rung upgrade, self-initiated:** `correction_recorded df1148b3-…` upgraded V3-E-018's
  remediation record from STATIC+INTEGRATION to **LIVE**, closing a limitation the session had itself
  declared and that two independent verifiers had separately named as the weakest point in the
  stream's evidence.
- **Residual:** S5-V3-E-024 — a dead API endpoint, fail-closed, zero data risk, still broken, low
  priority.

### §3.6 — S6 · Performance, Resilience and Observability

- **Lifecycle:** COMPLETE, 100%. **Scenarios: 14 measured live, 17 structurally excluded**, of a
  frozen denominator of 31 (15 §10.1 baseline metric categories + 15 §10.3 resilience/load battery
  + 1 demonstrated-can-fail).
- **Fixes landed:** 1 HIGH fix — **PR #1662**, disclosing MCP-door planning latency (S6-V3-E-003) —
  plus 1 measurement-correction fix.
- **The 17 exclusions, per item** (scope disposition `098a7dda-…`). Sixteen of these share one root
  cause: **no load generator, fault/chaos injector, or scriptable-reconnect SSE client exists
  anywhere in this repository, on any branch.** `probe/ask.ts` consumes a real happy-path SSE stream
  to completion and has no fault-injection capability. Each was recorded individually with its own
  reason rather than as one bulk waiver:
  - `R01-slow-first-token` — needs a controllable fault point delaying the provider's first token.
  - `R02-one-byte-trickle` — needs an interceptor/proxy streaming the response one byte at a time.
  - `R03-long-inter-event-gap` — needs an artificial inter-event gap beyond what real traffic
    produces (distinct from the REAL max-gap measurement, which *was* taken).
  - `R04-provider-timeout` — needs the upstream LLM provider forced to time out on demand.
  - `R05-malformed-citation-sentinel` — needs a malformed citation injected into a live stream.
  - `R06-giant-table` — needs a tool result large enough to stress table rendering at scale.
  - `R07-citation-dense-answer` — needs prompt/response shaping for artificial citation density.
  - `R08-reconnect-inside-buffer-ttl` — needs a scriptable SSE client that disconnects and
    reconnects mid-stream inside the TTL window.
  - `R09-reconnect-outside-buffer-ttl` — same gap as R08, outside-TTL case.
  - `R10-visibility-change-reconnect` — needs a real browser session simulating a mid-turn
    visibility-change event.
  - `R11-server-loss-mid-persist` — `dd16_outbox_recovery_test.ts` covers one narrow form
    (crash-kill / outbox replay against `pariprashna_persistence_outbox`) but not the general case.
  - `R12-outbox-retry` — overlaps R11's dd16 probe (not re-run this session); the full controlled
    retry battery needs the same absent harness.
  - `R13-provider-fallback` — needs the primary provider forced to fail so a fallback activates
    under observation.
  - `R14-rate-spend-rejection` — needs traffic deliberately driven past the rate/spend ceiling
    under controlled conditions.
  - `R15-concurrent-interactive-batch-pressure` — needs a concurrency driver running N parallel
    turns with a shared rate/timing collector.
  - `R16-post-deploy-smoke-demonstrated-can-fail` — `post_deploy_behavior_smoke.ts` exists (9
    targeted demonstrated-can-fail mutations) but its last known run predates this campaign
    (2026-08-23), so its result could not be claimed as current.
  - `R17-section-10-1-residual-instrumentation-bucket` — three §10.1 sub-items unreachable without
    **new instrumentation build-out**, not merely new measurement effort.
- **Residual:** the §10.3 load/chaos/CWV harness itself — see §5, residual R-1.

### §3.7 — Cross-stream totals

| Measure | Value |
|---|---|
| Findings recorded | 73 (9 CRITICAL, 34 HIGH, 26 MEDIUM, 4 LOW) |
| Remediations | 73 — **73/73 `VERIFIED`** |
| Independent verifications | 124 — **124/124 `ACCEPTED`**, 0 outstanding |
| `scenario_executed` events | 238 (208 substantive + 30 `STRUCTURALLY_EXCLUDED`) |
| Result packets accepted | 6 / 6 streams |
| Total ledger events | 731 (2026-08-24T21:07:18Z → 2026-08-30T03:14:33Z) |
| Rejected writes (validator held the line) | 266 |

**A terminology caveat, stated because a dashboard cannot state it.** The tracker's
`remediations[].status: VERIFIED` label applies identically to a real code fix and to an honestly
verified "no fix, deferred" disposition. Roughly half of the 73 are the latter. The underlying event
text is honest in every case, but "73 VERIFIED" must **not** be read as "73 defects fixed." The
count of merged fix PRs, not the count of VERIFIED remediations, is the fix figure.

---

## §4 — Rulings

### §4.1 — Both native rulings (recorded on the native's own instruction)

Recorded on stream P6 at seq 1 and 2 on 2026-08-30, and labelled in their own payloads as native
rulings rather than surrogate decisions. Both are reproduced in substance below.

**Native ruling 1 — V3-E-016 disclosure question** (event `9a3a3755-5268-4e31-b761-a6cf157f4a07`,
2026-08-30T03:05:52Z):

> **NO DISCLOSURE required**; neither suggested follow-up (provider-terms review, written rationale
> note) is required. Native's rationale: this is the astrological product and transmission of chart
> data to the AI provider is essential and inherent to how it works; the exposed corpus was the
> native's OWN data, and other chart subjects' data was not exposed. **CLOSED.**

*Scope:* V3-E-016 / CG-6 open question 1 of 2. No follow-up actions required.

**Native ruling 2 — V3-E-054 subject-consent gate** (event
`3561e052-d808-4d0e-a0a2-03804c0ce6ee`, 2026-08-30T03:05:53Z):

> V3-E-054 subject-consent gate (`SUBJECT_CONSENT_ENFORCEMENT`, default OFF): **CONFIRMED AS
> INTENDED PRODUCTION POSTURE.** No consent mechanism is required for this product; the safety switch
> **REMAINS OFF**. **No trigger condition attached** — this is the intended posture, not a deferral.
> **CLOSED.**

*Scope:* V3-E-054 / CG-6 open question 2 of 2. `posture: OFF_BY_DESIGN`. The flag lives in
`consent/flag.ts` and gates minor/guardian protections; with the flag OFF the gate returns *allow*
and `guardian_minor` is the primary refusal reason it would otherwise raise. Recording this as
"intended posture, no trigger condition" rather than as a deferral is deliberate: a deferral implies
a future obligation that the native explicitly did not create.

**Native acceptance** (event `949026fb-e2f2-412a-bc69-e826d4bb285e`, 2026-08-30T03:14:33Z,
`decision: ACCEPTED`, `authority: NATIVE`): fired on the native's explicit instruction after review
of the CG-6 packet and after both open questions above were ruled.

### §4.2 — Surrogate rulings

Forty-four `decision_recorded` events were written across the campaign, every one under
`NATIVE_SURROGATE` authority and every one folded into the projection under the standing label
**"SURROGATE DECISION — not native acceptance."** The load-bearing ones:

**Control-plane and takeover era (P0–P2):**

- `d7eeee05-…` — **self-pause at A0**, rather than proceeding past a boundary the session could not
  clear on its own authority.
- `9c9d967c-…` — **A2/R-1 RESOLVED via genuine self-provisioning**, no new secret and no new DB row:
  an existing credential minted a session for a pre-existing guest uid that already held exactly one
  `chart_grants` row. Scope was then *proved live* on deployed Cloud Run — allowed chart HTTP 200,
  native chart HTTP 307→`/dashboard` (denial probe only, no data read), versus HTTP 307→`/login` for
  an unauthenticated control, proving the deny was authz-specific rather than a generic bounce.
- `7d18ef56-…` — **A3-ABSORB complete: 81/81 unmerged branches dispositioned** (70 SUPERSEDED,
  7 ARCHIVE, 2 EVIDENCE-ONLY, 2 SALVAGE) against `origin/main@cc6b1a55e`, with the headline that
  **no** unmerged branch touched the route behind P2-B-001 — so there was no historical fix to
  salvage and the fix had to be written.
- `bfab930d-…` — **B-001 (E-012) triage:** `GET /api/charts/[id]` checked only that a caller was
  logged in, not that they owned or held a grant on the requested chart. Closed with a full live
  deployed re-proof (`2cdfd695-…`).
- `605d1071-…` / `df7ccbc9-…` — **B-002 (RLS gap) NO-GO on live remediation**, DOCUMENTED-NOT-CLOSED
  with a narrowed proof. PR #1598 added test-only detectors and explicitly did **not** close the
  finding.
- `465a692c-…` / `f98d8f68-…` — **scope-growth accepted honestly:** the B-001 verifier's adversarial
  sweep surfaced B-007 (cockpit `clear`/`clear/execute` with no ownership check, CRITICAL); the B-007
  verifier's sibling sweep then surfaced B-008 (`cockpit/runs` plus 6 more routes, same
  destructive-delete class). Both were opened as new blockers rather than absorbed silently.
- `54838d8c-…` — **B-007/B-008 deployed re-proof BLOCKED** by an unrelated failure in a *different*
  campaign's deploy pipeline (Nirmana PR #1601). Recorded as an honest external block, not as a pass.
- `e42f4fa8-…` — B-003 and B-005 **SUPERSEDED-BY-ARCHITECTURE**, closed without live remediation.

**Stream era (P3):**

- `37e0b7a8-…` — **the severity doctrine:** *severity tracks what a real reader or auditor is told,
  not how alarming a finding reads or how cheap it is to fix.*
- `3264bda1-…` — defer all per-stream `result_packet_accepted` to the convergence session; streams
  produce packets but do not each run the 7-stage ceremony separately.
- `99421811-…` — V3-E-012: the native **authorizes** the quality corpus's use of the native's real
  chart in fixtures, because reading-quality assessment is most meaningful against the real chart and
  real life events.
- `08fff7a9-…` — **V3-E-016 declared an active, severe, currently-exploitable production privacy
  leak**, in those terms, at discovery.
- `bd5946c2-…` — S3's 13-scenario exclusion ruling (§3.3).
- `098a7dda-…` — S6's scope disposition against the frozen 31 (§3.6).
- `f1a63de7-…` — V3-E-033: adopt the docblock's stated intent as authoritative.
- `9a6fd596-…` — V3-E-032's S4-referral half was investigated and found **NOT** absorbed under other
  numbering; recorded as a genuine tracker gap rather than assumed handled.
- `dffa00e4-…`, `026445b6-…` — S1's two deferred residuals with named ownership (§3.1).

**Closeout era:**

- `fb54d19b-…` — **RATIFY V3-E-016 as fixed and verified** for the full 6-chart blast radius.
- `e526c889-…` — control-plane P2-release upgrade blocker **DEFERRED as a non-blocking residual**;
  live service confirmed healthy, `source_sha` unchanged.
- `5e1a5a17-…` — **PR #1615: EXTEND** (not merge-as-is, not defer) to cover two live data-bearing
  tables; `b03625f4-…` then signs off after re-verifying the actual diff rather than the report.
- `9f5e1658-…` — **B-002: RECORD ACCEPTED-RISK**, do not commission a full remediation build now.
  Reasoning turned on the finding not being currently exploitable in production as a cross-tenant
  leak, per `B002_NARROWED_PROOF`.
- `d9fd0274-…` — **V3-E-061: COMMISSION_FIX_THIS_CAMPAIGN**, explicitly not an emergency fast-path
  (§2).
- `37c87c12-…`, `13348a55-…`, `55bf2978-…` — the three **Phase E / CG-4 referral reconciliations**,
  which found that referrals had been marked "referral filed = VERIFIED" by the *referring* stream
  without the *target* stream ever picking them up, and re-opened six of them with named ownership
  (§5, R-3).

---

## §5 — Residuals carried forward

Each residual below has an owner or an explicit accepted-risk note. None is closed by this seal.

| # | Residual | Severity | Disposition / owner |
|---|---|---|---|
| **R-1** | **S6 §10.3 load/chaos/CWV harness does not exist** — no load generator, fault/chaos injector, or scriptable-reconnect SSE client anywhere in the repo. Blocks 16 of S6's 31 scenarios (§3.6). | HIGH (coverage) | **Deferred to a dedicated future session**, per the original closeout plan's own instruction — not a shortcut invented at close. Spec already written. **Owner: unassigned — needs a named owner.** Not a CG-3 or campaign blocker; it is a real, standing coverage gap. |
| **R-2** | **Conversation-replay re-hydration architectural gap** (red-team). `/consult/continue`, `/regenerate` and `/resume` replay persisted conversation content **verbatim, without re-hydration or re-linting** — so any pre-fix leaked content, had it been captured, would still be served today. | HIGH (architectural) | **No remediation needed for actual harm** — the DB forensic check found zero leaked content was ever captured (§2). **The architectural gap itself is real and unfixed.** Harden by adding re-hydration / re-lint on all replay paths. **Owner: unassigned — needs a named owner.** This bore directly on native ruling 1. |
| **R-3** | **Six cross-stream referrals** re-opened by the Phase E audit after being marked "referral filed = VERIFIED" without any target stream picking them up: V3-E-042→S1, V3-E-044→S5, V3-E-031→S6, V3-E-053→S6, V3-E-014→S4, V3-E-021→S4. | MIXED | **Open, owned, deferred** with the named target streams above. Correctly tracked as open rather than closed-by-referral. |
| **R-4** | **B-002 / E-002 / E-015 — RLS gap.** `chart_facts` / `chart_dashas` have zero RLS objects; all ~360 public-schema tables share an owner. | MEDIUM | **ACCEPTED RISK** per Surrogate ruling `9f5e1658-…`: not currently exploitable in production as a cross-tenant leak (`role_web_serve` scoping, per `B002_NARROWED_PROOF_v1_0.md`). Recorded here as the standing record so it stops being re-discovered as new. |
| **R-5** | **S5-V3-E-024** — dead API endpoint, fail-closed. | LOW | Still broken, **zero data risk**, low priority. Owner: S5 territory. |
| **R-6** | **S2 V3-E-060 partial fix** — the unfixed half. | MEDIUM | Disclosed, not rounded up to "fixed". Owner: S2 territory. |
| **R-7** | **S1 breadcrumb colour-contrast** (axe SERIOUS) in `AppShellBreadcrumb.tsx`. | LOW/MEDIUM (a11y) | Deferred with named ownership ask per ruling `dffa00e4-…`; outside S1's chartered territory. |
| **R-8** | **CI does not run on stream-branch PRs** unless retargeted to `main` or allowlisted in `ci.yml`'s `pull_request.branches`. A PR can appear "green" by having had no checks at all. | MEDIUM (process) | Open process gap, ruling `026445b6-…`. Affects any future campaign using stream branches. **Owner: repo CI configuration.** |
| **R-9** | **Ceremony audit-trail thinness** — 6 of S5's `verification_accepted` events carry no verdict/note text. | LOW (documentation) | The underlying work is independently corroborated (PRs merged, matching diffs). A discipline note for future sessions; **not** a re-verification requirement. |
| **R-10** | **`VERIFIED` terminology ambiguity** — the tracker label does not distinguish "fixed" from "deferred, honestly verified" (§3.7). | LOW (tooling) | Future tracker UI/label clarity improvement. |
| **R-11** | **Control-plane P2-release upgrade blocker.** | LOW | Deferred as non-blocking per `e526c889-…`; service confirmed healthy. |
| **R-12** | **Two unrelated open PRs (#1608, #1513)** carry real merge conflicts from this campaign's rapid merge cadence. | LOW | Need a rebase. Unrelated to Paripraśna's scope; noted so they are not mistaken for campaign debt. |

---

## §6 — Process lessons

This campaign's own failures are part of its record. Each of the four below was a real failure that
real evidence caught — none was discovered by reasoning about what might go wrong.

### §6.1 — The silent stall, and the anti-stall protocol

The v1.0 overnight run **stalled silently for roughly 12 hours** (last ledger event
2026-08-28T23:50:59Z, then zero events and zero file writes), and later stalled again for ~16 hours
with the critical V3-E-016 fix — PR #1655 — sitting merged-ready but unmerged. **Nobody knew until
the native asked.** The system reported nothing because nothing failed; it simply stopped.

The correction, landed as §1 of `PARIPRASHNA_AUTONOMOUS_CLOSEOUT_PLAN_v2_0.md`, is the
**Anti-Stall / Liveness Protocol**: a heartbeat at ≤10-minute intervals, durable checkpoints, and —
the load-bearing clause — **a stall is a first-class failure, not silence.** An autonomous system
that can only report failures it detects will never report the failure mode of not running.

This is §N.8's Earned-Signal Principle at the campaign level: *liveness* was the signal with no
detector behind it. "Still running" was being inferred from the absence of an error, which is exactly
the proxy-instead-of-claim defect §N.8 names.

### §6.2 — The concurrent-writer / false-count defect

Two sessions wrote to stream S5 as the same actor (`lead-s5`) within ten minutes, **neither aware of
the other**. Both independently allocated scenario ids `S5-SC-14..21`, distinguished only by suffix
(`s5wrap-` vs `s5-reproof-`). Together they drove `scenarios.executed` to exactly **45 of the frozen
denominator 45** — a perfect-looking completion figure produced by collision, not by coverage.

What makes this the campaign's best moment rather than its worst: **both sessions self-disclosed
independently and reached the same verdict.** `correction_recorded d1808d88-…` states the incident
and warns in terms: *"THAT 45/45 MUST NOT BE READ AS…"*. `correction_recorded 561637ce-…` is the
*other* session confirming and adopting that verdict, and explicitly declining to vouch for events it
had not written: *"I did NOT write ledger_seq 408-415… and cannot vouch for them."*

**The fix is in the control plane, not in a convention.** `scenario_slot()` now derives a canonical
numeric slot (`S{N}-SC-{NN}`) from any scenario id *independent of its descriptive suffix*, and the
validator rejects a second write to an already-used slot with `DUPLICATE_SCENARIO` — "a scenario
numeric slot can be executed only once per stream, regardless of slug." Two such rejections and five
`SCENARIO_DENOMINATOR_EXCEEDED` rejections are on the ledger as the guard actually firing. The final
S5 figure — 45 distinct slots from 53 recorded events — is the deduplicated truth, and the 8-event
gap is the audit trail of the defect rather than an unexplained discrepancy.

### §6.3 — The phantom-event vocabulary error

Closeout plan v1.0's ceremony runbook instructed streams to emit **`remediation_verified`** — an
event type that **does not exist** in the tracker's vocabulary. **S4 correctly refused to emit it.**

The lesson is not "check the vocabulary." It is that a runbook is an unverified claim about a system
until something executes it against the real system, and that the correct response to an instruction
that does not typecheck against reality is refusal, not improvisation. Had S4 invented a nearby event
type that *did* exist, the ceremony would have appeared to complete while recording something other
than what it claimed. Plan v2.0's §5 pins the ceremony vocab exactly and states plainly: *"There is
no `remediation_verified`."*

### §6.4 — Verify before trust

Self-reports were wrong repeatedly, and independent verification caught **each** one. This is the
campaign's central finding about its own method:

- A session's own merged-PR list claimed **#1664** was merged; `gh pr view` showed it still OPEN,
  which meant the CG-4 gate-closure evidence path did not resolve on `main`. Caught by the CG-6
  packet's own verification pass. *(Now genuinely merged — `d84ab9706` on `main`.)*
- An S4 referral's justification text was **copy-pasted from a different finding**. Caught by the
  independent verifier, corrected on the ledger, re-verified.
- A stream's `deployed_revision` was **stale** — recorded at `work_started` and never refreshed past
  the V3-E-016 fix's own deploy. Caught and corrected by re-checking `gh run list` live rather than
  trusting the stored number (`correction_recorded 3857c1a5-…`).
- V3-E-018's evidence rung was **over-claimed as stronger than it was** until two independent
  verifiers separately named it the weakest point in the stream's evidence — after which it was
  upgraded to a genuine LIVE proof (`df1148b3-…`), not re-labelled.
- The **266 rejected writes** are the machine half of the same discipline: `SELF_VERIFICATION`
  blocked finders from verifying their own closures, `FINDING_FREEZE` blocked post-freeze findings
  from entering ungoverned, `ROLE_FORBIDDEN` blocked the integrator from writing a decision reserved
  to the surrogate, and 226 `SEQUENCE_CONFLICT` rejections blocked every concurrent write that would
  have silently interleaved.

The generalizable rule: **an actor's report of its own work is a hypothesis.** Every load-bearing
claim in this campaign that turned out to be false was a self-report, and every one of them was
caught by someone or something that re-derived the fact from the primary source instead of reading
the report.

---

## §7 — Closing tracker state

**Integrity at seal** (`GET /api/integrity`) — full hash-chain replay, recomputed and compared:

```
{
    "ok": true,
    "reason": "ok",
    "expected_hash": "65a4a88e1675e4aebc2658ddc4c06cd7d2cd14741fd822f301838890abc48aa4",
    "actual_hash": "65a4a88e1675e4aebc2658ddc4c06cd7d2cd14741fd822f301838890abc48aa4",
    "materialized_hash": "65a4a88e1675e4aebc2658ddc4c06cd7d2cd14741fd822f301838890abc48aa4",
    "event_log_hash": "0cf2609c1fa67e4d6bc946cac2cebc33778cfb631ab7196aba2f5bec7f80bfe8",
    "as_of": "2026-08-30T03:23:25Z"
}
```

`ok: true` means the materialized projection, the recomputed replay, and the stored hash chain all
agree. Per the campaign's own red-team note, **integrity ≠ veracity**: this proves the ledger has not
been altered since it was written, not that every claim written into it is true. The veracity work is
§3–§6 above.

**Closing ledger snapshot:**

| Field | Value |
|---|---|
| Campaign | `pariprashna-experience-assurance-v3` |
| Completion | **100.0%** (100.0 / 100.0 campaign points) |
| Gates | **8 / 8 CLOSED** (CG-0 … CG-7) |
| Phases | **8 / 8 at 100%** (P0 … P7) |
| Streams | **6 / 6 COMPLETE**, 6/6 result packets accepted |
| Findings | 73 recorded · 73 remediations, all `VERIFIED` |
| Verifications | 124, all `ACCEPTED` |
| Total events | `734` |
| First event | 2026-08-24T21:07:18Z |
| Final event | `2026-08-30T03:23:25Z` (CG-7 `gate_closed`) |
| Rejected writes | 266 (the validator holding the line) |
| Integrity | `ok: true` |

**Production at seal:** deployed Cloud Run revision `amjis-web-01805-mhr`, image tag
``5f112179373a16ccffbd18aa3347f0771bf86bd4``, `commit-sha` label identical — production equals `main`, and the V3-E-016 fix commit
`693536e93` is an ancestor of it.

---

## §8 — What this campaign proved, and what it did not

**Proved.** That a live, hash-chained, role-separated event ledger with a validator that *rejects*
malformed ceremony can hold an autonomous multi-session campaign to honest accounting — including
against the campaign's own sessions. Every attempt to self-verify, to skip the freeze, to double-count
a scenario slot, or to write out of sequence was refused by the machine rather than by good intentions.
That a real CRITICAL third-party data exposure can be found, root-caused, fixed, deployed, live-re-proofed
and independently ratified inside a single campaign arc. And that a system's own failures — a silent
stall, a false 45/45, a phantom event type — are recoverable when the response is to write them down
and build a detector, rather than to route around them.

**Did not prove.** That the product is performant or resilient under load: 16 of S6's 31 scenarios
could not run because the harness to run them does not exist (R-1). That replayed conversation content
is safe: the re-hydration gap is real and unfixed, and is safe today only because nothing was captured
(R-2). That the six re-opened cross-stream referrals are handled (R-3). And, per §3.7, that 73
`VERIFIED` remediations means 73 defects fixed — roughly half are honest deferrals.

An honest gap beats a padded close. This report states both.

---

*End of report. Sealed 2026-08-30. Written from the live event ledger, `gh`, `git`, and `gcloud`
state — not from any session's self-report. Predecessor packet:
`CG6_NATIVE_ACCEPTANCE_PACKET_v1_0.md`. Campaign plan of record:
`PARIPRASHNA_AUTONOMOUS_CLOSEOUT_PLAN_v2_0.md`. Test plan:
`PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md`.*
