---
artifact: S6_RESULT_IN_PROGRESS
version: "1.0"
status: IN PROGRESS — NOT a result packet, NOT a closure claim. Stream closure
  (result_packet_accepted) is deferred to the convergence session (Session C)
  by native decision; this document does not attempt it and must not be read
  as one.
date: 2026-08-28
stream_id: S6
produced_by: Paripraśna assurance stream S6 (Performance, Resilience &
  Observability), checkpoint-and-premise-correction pass
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/charters/STREAM_CHARTER_S6_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/S4_LATENCY_WATERFALL_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md#S6-V3-E-001
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md#S6-V3-E-002
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md#S6-V3-E-003
changelog:
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

## 2 — Real evidence banked this session (N = 3 of 31 scenarios; 1 finding)

All logged to the tracker (`lead-s6`, HTTP-only writes, full evidence per
event) and cross-referenced in EDIR. Tracker state as of this checkpoint:
`S6: RUNNING, scenarios {executed: 3, planned: 31}, findings: 1`.

| Scenario | Result | Trace/evidence |
|---|---|---|
| `S6-SC-M01-first-signal-full-turn-latency` | Third independent LIVE reproduction of the turn-latency-unattributed finding: 86,945ms end-to-end, only 0.52% attributable to tool dispatch. Corroborates S4's **V3-E-015** (E-006: 81.3s/4.9%; S4: 102.4s/0.69%; S6: 86.9s/0.52%). | `trace_id 69ac9756-2c01-402b-8fff-b8abfbbfec2e`, `job_id a0480ded-9647-430c-9843-432bce0b5a8c` |
| `S6-SC-M02-planning-stage-latency-segmentation` | 265 real Portal-door samples of `planning_latency_ms` for the synthetic chart: avg 5,955ms, min 1,974ms, **max 99,339ms**. New finding, not mere corroboration — see below. | Read-only DB query via `cloud-sql-proxy 127.0.0.1:5433/amjis`, `amjis_app` role, scoped to `chart_id=1c826d5a-...` only |
| `S6-SC-M03-prediction-capture-resolution-coverage` | 56 rows in `mimamsa_predictions`, 6 in `pariprashna_predictive_samples` for the synthetic chart — confirms capture is non-zero; resolution-status breakdown not yet queried. | Same DB access path, read-only |

**Finding S6-V3-E-003** (proposed HIGH, pending Native Surrogate triage): the
planner stage (S5 in S4's decomposition) has a real, undocumented tail up to
99.3s on production turns for the synthetic chart — comparable to or
exceeding the whole-turn provisional interpretive p95 target (<90s) on its
own. This also **partially revises** S4's claim that no per-stage timer
exists for S1–S5: the timer exists for this stage on the Portal door (S4
measured only the MCP door, where `persistence.status: "none"` — confirmed
independently this session too — and no such field is exposed).

## 3 — What is reachable now vs. what needs the net-new harness

**Reachable now, no new infrastructure** (the remaining ~7-9 of the "cheap"
batch this checkpoint was scoped to; not attempted further this pass —
parked for the next working session, not abandoned):
- More `prashna_ask` baseline calls for other work classes / query classes (each ~90s real wall-clock).
- DB-backed: cost-per-turn (needs tracing `llm_call_log`/`llm_usage_events` to a `turn_id`, not yet done), client-error rates, resolution-status breakdown on the 56/6 prediction rows above, `pariprashna_persistence_outbox` current-state snapshot (queried this session: 0 rows currently — an empty-queue snapshot, not a resilience proof).
- Reusing `post_deploy_behavior_smoke.ts` as-is for the demonstrated-can-fail scenario, **after** first re-verifying whether its 2026-08-23 RED status (JSON parse error) still holds — not re-verified this session.

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
  will be sought from this session.
- 3 of 31 scenarios executed is reported as **3/31**, not rounded up, not
  described as "baseline phase complete."
- The §10.3 battery is reported as **not started**, not "in progress" — no
  scenario in that category has been executed.
- Finding S6-V3-E-003's severity is **proposed**, not final, per register
  law.

*End S6 result-in-progress v1.0 — checkpoint only.*
