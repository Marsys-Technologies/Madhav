---
artifact: S6_RESULT_IN_PROGRESS
version: "1.1"
status: IN PROGRESS — NOT a result packet, NOT a closure claim. Stream closure
  (result_packet_accepted) is deferred to the convergence session (Session C)
  by native decision; this document does not attempt it and must not be read
  as one.
date: 2026-08-29
stream_id: S6
produced_by: Paripraśna assurance stream S6 (Performance, Resilience &
  Observability), convergence-ready pass (session 2)
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/charters/STREAM_CHARTER_S6_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/S4_LATENCY_WATERFALL_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md#S6-V3-E-001
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md#S6-V3-E-002
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md#S6-V3-E-003
changelog:
  - "1.1 (2026-08-29, convergence-ready pass): 4 more scenarios executed (7/31
    total). S6-V3-E-003 independently re-verified by code read and reconciled
    with S4's V3-E-043 — one coherent instrumentation story, not two adjacent
    claims. New real data: cost-per-turn ($0.29 avg on synthesis), safety
    verdicts (302 decisions, 292 clean), prediction resolution (0/56
    resolved — honest gap, not a defect). Harness build spec reviewed:
    confirmed complete and convergence-legible, unchanged."
  - "1.0 (2026-08-28): initial checkpoint after premise-correction pass. 3/31
    scenarios executed with LIVE/DB evidence; 1 finding filed; harness build
    scoped and explicitly parked, not attempted."
---

# S6 — Result in progress (checkpoint, not closure)

## 1 — Premise correction (recorded here per the checkpoint instruction, in
addition to EDIR S6-V3-E-001)

An earlier S6 session reported to the operator that
`platform/scripts/probe/ask.ts`, `post_deploy_behavior_smoke.ts`, and
`dd16_outbox_recovery_test.ts` were "fabricated" / did not exist anywhere in
the repo. **That was false.** All three exist, at exactly the path the
original kickoff plan cited, on `origin/main` and in this worktree, present
since worktree creation (`git log --diff-filter=A`: `ask.ts` 2026-08-20 PR
#1374, `dd16_outbox_recovery_test.ts` 2026-08-20 PR #1396,
`post_deploy_behavior_smoke.ts` 2026-08-22 PR #1494). Full account, including
what could and could not be reconstructed about the root cause of the
original error, is at EDIR **S6-V3-E-001**.

What the three files actually are (accurate characterization, neither
over- nor under-claiming):

| File | What it is | What it is NOT |
|---|---|---|
| `probe/ask.ts` | Standing LIVE `/api/pariprashna` driver: mints a session via `probe-service-account` chart-grant impersonation, POSTs, consumes SSE to completion, writes one JSON per turn. The hard part (the auth seam) is already solved and documented in its own header. | A load generator — it drives one turn at a time. |
| `probe/post_deploy_behavior_smoke.ts` | A real authenticated LIVE turn on the synthetic chart, built on `ask.ts`, asserting real engine behaviour with 9 targeted demonstrated-can-fail mutations. Per memory of a 2026-08-23 run it was RED on a service-side JSON parse error at that time — **not re-verified this session**. | A load or chaos test — it runs one turn and asserts. |
| `probe/dd16_outbox_recovery_test.ts` | A real crash-kill / outbox-recovery replay test against the live `pariprashna_persistence_outbox` table (migration 578), self-cleaning. This already covers one §10.3 scenario (server-loss-mid-persist / outbox retry) in its narrow form. | A general chaos-injection framework — it tests one specific failure mode. |

**No load generator, fault/chaos injector, or browser/CWV harness exists
anywhere in this repo, on any branch checked.** That gap is real and is
Section 5 below.

## 2 — Real evidence banked (N = 7 of 31 scenarios; 1 finding, reconciled)

All logged to the tracker (`lead-s6`, HTTP-only writes, full evidence per
event, `writer_instance_id` lease honored per the D-127 hardening that
landed on `origin/main` between sessions — re-derived and adopted live, not
assumed) and cross-referenced in EDIR. Tracker state as of this pass:
`S6: RUNNING, scenarios {executed: 7, planned: 31}, findings: 1`.

| Scenario | Result | Trace/evidence |
|---|---|---|
| `S6-SC-M01-first-signal-full-turn-latency` | Third independent LIVE reproduction: 86,945ms end-to-end, 0.52% attributable to tool dispatch. Corroborates S4's **V3-E-015**. | `trace_id 69ac9756-2c01-402b-8fff-b8abfbbfec2e` |
| `S6-SC-M02-planning-stage-latency-segmentation` | 265 real samples of `planning_latency_ms`, `/api/pariprashna` route: avg 5,955ms, min 1,974ms, **max 99,339ms**. | Read-only DB query, `chart_id=1c826d5a-...` only |
| `S6-SC-M03-prediction-capture-resolution-coverage` | 56 rows in `mimamsa_predictions`, 6 in `pariprashna_predictive_samples`. | Same DB access path |
| `S6-SC-M04-cost-per-turn-channel-model` | 255 synthesis calls (`llm_usage_events`, `pipeline_stage='synthesize'`), 1:1 with 255 conversations (no retries in-sample): total $73.79, **avg $0.2894/turn**, avg 121,381 input / 4,276 output tokens, latency 6,569–**179,830ms**. `llm_call_log` does NOT capture pariprashna calls (only an incidental `title` call, cost_usd NULL) — `llm_usage_events` is the correct source table. | Read-only DB, n=255 |
| `S6-SC-M05-fourth-latency-reproduction` | Fourth LIVE sample: 96,337ms, 0.30% attributed. Intended to segment a new work class (dasha timing) but the planner classified it `predictive` again — reported honestly as an additional predictive-class sample, not a new segment. | `trace_id 4645e719-3e62-4d52-b3b5-63add2e58aa8` |
| `S6-SC-M06-safety-verdicts` | 302 `pariprashna_safety_decisions` rows, all `enforced=true`: 292 clean/`proceed`, 5 `hard_stop`→`seal_pending_signoff`, 3 `review_required`→`seal_pending_signoff`, 2 `hard_stop`/`hard_stop`. Flagged (not adjudicated) as a cross-stream observation for S5's `V3-E-054` ("safety gate ships flag-OFF by default") — this table shows historically-enforced decisions on this chart; doesn't itself establish current deployed flag state. | Read-only DB, n=302 |
| `S6-SC-M07-persistence-outcome-and-prediction-resolution-detail` | Outbox: 0 rows (empty-queue snapshot, not a resilience proof). Predictions: all 56 rows `lifecycle_status='pending'` — **0% resolved**, reported as an honest gap consistent with L5 Mimāṃsā's documented STRUCTURAL-mode seal (calibration fills in as outcome data accrues, by design), not escalated as a defect. | Read-only DB |

**Finding S6-V3-E-003** (proposed HIGH, pending Native Surrogate triage,
**independently re-verified and reconciled this pass**): the planner stage
has a real, undocumented tail up to 99.3s on production turns for the
synthetic chart. Re-verification method: read the actual application code
rather than re-running the DB query. `platform/src/app/api/pariprashna/route.ts`
imports `runPlanStage` (sets `planning_latency_ms`) and `runPersistenceStage`
(persists it to `conversation_messages.metadata_json`) — confirms the DB
finding traces to a real, in-charter-scope route. The code path that
actually serves the `prashna_ask` MCP tool call
(`platform-mcp/src/lib/prashna_ask_bridge.ts` → HTTP →
`platform/src/app/api/mcp/prashna_ask/route.ts`, a **third**, separate
route) has zero planning-stage timer, grep-confirmed. **Reconciliation: this
is a precise restatement of S4's already-filed `V3-E-043`** (three
independent, mutually-disjoint telemetry surfaces — `/api/chat/consult`,
`/api/pariprashna`, and the MCP door), not a second independent defect. The
finding's original "Portal door vs MCP door" framing was imprecise against
the real three-surface architecture (there is no single "Portal door" vs
"MCP door" binary) — corrected in EDIR, cross-referenced to both `V3-E-015`
and `V3-E-043` now. One coherent instrumentation story for convergence.

## 3 — What is reachable now vs. what needs the net-new harness

**Reachable, executed this pass** (4 more beyond the prior checkpoint's 3):
cost-per-turn, a 4th/5th latency sample, safety verdicts, persistence-outbox
snapshot + prediction resolution detail. Proxy torn down after (PID 50232).

**Still reachable, not yet attempted** (parked, not abandoned — smaller
remainder than before):
- More `prashna_ask` baseline calls, deliberately targeting a genuinely
  non-predictive `query_class` (both attempts this pass classified as
  `predictive` — a `chart_overview` or `remedy_lookup`-shaped question may
  be needed to actually reach a `factual`-equivalent segment).
- Client-error rates — no `client_error`/`lint` table was found in this
  DB; this metric category may not be DB-observable at all without a
  browser/client-side probe (a real gap, not yet resolved either way).
- Reusing `post_deploy_behavior_smoke.ts` for the demonstrated-can-fail
  scenario, after first re-verifying whether its 2026-08-23 RED status
  still holds — **still not re-verified**.

**Needs the net-new §10.3 harness** (the load generator / chaos injector /
CWV-browser battery — genuinely does not exist, per Section 1):
- Concurrent/load scenarios (concurrent interactive/batch pressure, rate/spend rejection under real concurrency).
- Fault injection (slow first token, 1-byte trickle, long inter-event gap, provider timeout, provider fallback) — these need a controllable fault point, not just observation of `ask.ts`'s happy path.
- Reconnect scenarios (inside/outside buffer TTL, visibility-change) — need a scriptable SSE client that can deliberately disconnect/reconnect mid-stream; `ask.ts` consumes to completion, it doesn't interrupt itself.
- Core Web Vitals at p75 — needs a real browser (Lighthouse / Chrome DevTools), not a Node/tsx script.

## 4 — Harness build spec (recommendation for a dedicated build session, NOT built here)

Per the checkpoint instruction, this is scoped and parked, not attempted.
Recommended shape for that dedicated session:

1. **Reuse `ask.ts`'s auth seam directly** — do not re-derive session-cookie minting. Import or shell out to it.
2. **Concurrency driver**: wrap N parallel `ask.ts` invocations with a shared rate/timing collector; this is the smallest net-new piece (~150-250 lines) and unlocks 3 of the remaining §10.3 scenarios (concurrent pressure, rate/spend rejection, provider fallback observation under load).
3. **Fault injection**: needs either (a) a local proxy/interceptor in front of the deployed route that can inject latency/truncation/drops — meaningfully more infrastructure — or (b) a lower-fidelity but honest fallback: point `ask.ts` at a local dev server with deliberately-mocked provider responses for the specific fault shapes (slow-first-token, trickle, timeout). Recommend (b) first — it is buildable in the same session, and (a) is flagged as a possible follow-up if (b)'s fidelity proves insufficient at triage.
4. **Reconnect harness**: a thin SSE client wrapper around `ask.ts`'s stream-consumption logic that can deliberately abort and resume, checked against the buffer TTL. Model directly on `dd16_outbox_recovery_test.ts`'s "interrupt mid-operation, verify recovery" shape — same pattern, different interruption point.
5. **CWV**: use Chrome DevTools MCP / Lighthouse against the deployed Portal directly — no custom code needed, just a driven session (the `chrome-devtools-mcp` skill available in this environment already covers this).
6. **Rough size estimate**: steps 2+4 (concurrency + reconnect) are a half-day build-and-dry-run session, similar in shape to the harness build-and-dry-run pattern `STREAM_EXECUTION_HARNESS_v1_0.md` §9 already specifies for the fleet-launch harness (prove each scenario type on ONE throwaway case before trusting the full battery). Step 3(a) (real fault injection) and step 5 (CWV) can run in parallel in the same or a follow-on session — step 5 has zero code dependency on 2/3/4.
7. **Do not build this as part of an open-ended S6 session** — scope it as its own precondition-style session with a fixed ceiling, exactly as the checkpoint instruction says, and dry-run each new scenario type once before trusting the battery, mirroring the fleet-harness precedent's own dry-run discipline.

## 5 — Explicit non-claims

- This is **not** a stream closure. No `result_packet_accepted` was sought or
  will be sought from this or the prior session.
- 7 of 31 scenarios executed is reported as **7/31**, not rounded up, not
  described as "baseline phase complete" — several §10.1 categories (client
  errors, lint firings, full segmentation-by-work-class) remain unattempted.
- The §10.3 battery is reported as **not started**, not "in progress" — no
  scenario in that category has been executed, across two sessions.
- Finding S6-V3-E-003's severity is **proposed**, not final, per register
  law — triage by the Native Surrogate has not occurred.
- The reconciliation with `V3-E-043` in Section 2 corrects this document's
  own prior imprecise "Portal door vs MCP door" framing; it does not claim
  S4's `V3-E-043` itself needed correction — that entry was already accurate
  and is the senior finding here.

## 6 — Task-3 confirmation: harness build spec reviewed, unchanged

Re-read Section 4 this pass against the convergence-legibility bar (reuse
spec + reachable-vs-needs-infra split + size estimate, all present and
specific to named files). No thinness found — the spec already names exact
files to reuse (`ask.ts`'s auth seam, `dd16`'s interrupt-and-verify shape),
gives a concrete size estimate (half-day for concurrency+reconnect), and
explicitly separates what needs zero new infra (CWV via Chrome DevTools MCP)
from what needs real build work (fault injection). Section 3 above was
refreshed to reflect what two sessions' worth of "reachable now" work
actually found reachable vs. not, which is the part that most needed
updating — Section 4's harness spec itself did not need a rewrite.

*End S6 result-in-progress v1.1 — checkpoint only, not closure.*
