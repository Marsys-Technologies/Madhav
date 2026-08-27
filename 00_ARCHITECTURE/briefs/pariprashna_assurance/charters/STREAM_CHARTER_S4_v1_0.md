---
artifact: PARIPRASHNA_STREAM_CHARTER_S4
version: "1.0"
status: FROZEN — registered as tracker plan revision 4
date: 2026-08-27
stream_id: S4
stream_name: Pipeline Correctness & Door Parity
frozen_by: Session A, Phase A5
---

# Stream charter — S4 (Pipeline Correctness & Door Parity)

- **Owner (actor to register):** `lead-s4`
- **Independent verifier:** `verifier` (Sonnet/high default)
- **Baseline SHA:** `3686772b7000cf9e1d391b97eccc008ef167b8d0`
- **Deployed revision pin:** `amjis-web` @ `cafa894ee7cfc2e86743bb92625e7faf293aec0a`, `amjis-mcp` @ `b8937e0c1a8af03863f5e4d121119f99c4db4060` — both stale behind baseline; the web staleness is the unrelated Nirmana deploy blocker (PR #1601), the MCP staleness pre-dates this session. Re-check both at your own open; S4's per-stage tracing works from source at baseline regardless, but any LIVE-rung stage proof needs the deployed SHAs to actually match what you're tracing against — note any mismatch rather than assume parity.
- **Worktree/branch:** fresh worktree off `origin/main` @ baseline SHA, branch `pariprashna/v3-s4-pipeline-parity`
- **Approved ceiling:** 8h wall-clock; spend by judgment. **Concurrency exception (elevation §11.1):** S4 may run up to 12 concurrent subagents during stage fan-out (vs. the default cap of 8), given its volume.
- **Entry gate and dependencies:** CG-2 CLOSED (`031e03fc-7685-4c17-af34-bba115318246`); P2→P3 RESOLVED (`02d8c469-7ceb-440c-be10-a910cc6bcaa8`)

## Credential status

RESOLVED per A2 — needed for any LIVE-rung dual-door stage proof.

## Test subject

Synthetic chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a`.

## Scope (test plan v2.1 §4 complete — the largest single stream by volume; §4.3 synergy tests; J10 door parity)

**Primary file territory:** `platform/src/lib/pariprashna/pipeline/` stages per the §4.1 anchor map below, plus their `platform-mcp` twins.

**The 11-stage inventory (test plan §4.1), each tested for correctness + optimality + failure-honesty + demonstrated-can-fail:**

| # | Stage | Primary implementation |
|---|---|---|
| S1 | NormalizedQuery → intent/scope classification | `platform-mcp/src/tools/intent_scope_classifier.ts`, `platform/src/lib/vidhi/scope_classifier.ts` |
| S2 | EntitlementDecision | `platform/src/lib/pariprashna/pipeline/safety_gate.ts` (~226), `authorizeChartAccess.ts`, `invoke_tool.ts:80` |
| S3 | SafetyPolicyDecision | `safety_gate.ts` (~281) |
| S4 | ScopeTuple / ClarificationRequest | `scope_classifier.ts` (`ScopeTupleSchema`) |
| S5 | AcharyaPlan (planner) | `plan_stage.ts`, `pipeline_planner.ts`, `compiled_floor_adapter.ts`, `vidhi/compiler.ts`, `budget_arbiter.ts`, `no_leakage_filter.ts` |
| S6 | ToolBroker → dispatch | `evidence_stage.ts`, `retrieval/qos/dispatch_queue.ts` |
| S7 | EvidenceBundle assembly | `evidence_stage.ts`, `bundle/bundle_hydrator.ts` |
| S8 | Interpretation & Adjudication | Portal: `pipeline/synthesis_stage.ts`; MCP: `prashna_ask_synthesis.ts` (truncation flag ~380) |
| S9 | Grounding/Safety Validation | `validation_stage.ts:47`, `streaming_citation_validator.ts`, `register_leak_lint.ts:174` |
| S10 | SemanticReadingParts | `reading_parts.ts`, `block_classifier.ts`, `FrozenBlock.tsx` |
| S11 | TurnProvenance + AcharyaReadingReceipt | `receipt/assemble.ts:538`, `receipt/{schema,validate,hash,store}.ts`, `persistence_stage.ts:554` |

(Note: this table's own "S1"–"S11" numbering is the TEST PLAN's pipeline-stage numbering, unrelated to and not to be confused with the CAMPAIGN's stream ids S1–S6 — you are stream **S4** testing pipeline stages numbered S1 through S11.)

**Dual-door track (test plan §4.1):** S1/S5/S8 have MCP-side twins (`plan_builder.ts`, `scope_resolver.ts`, `prashna_ask_synthesis.ts`, job progress at `register_prashna_ask.ts:202`). Every stage test that can run on both doors runs on both; a stage passing one door and failing the other is a PPR-30 parity finding, filed **per-stage**, never as one opaque "doors differ."

**Per-stage optimality criteria (test plan §4.2) — establish a first-measured baseline for each, target ratified after two weeks (provisional until then):** S1 classifier accuracy/latency/clarification-precision; S5 planner floor-coverage completeness + tool-selection efficiency + plan-latency share; S6 broker per-tool p95 + parallelism efficiency (wall-clock dispatch window ÷ Σ individual latencies — near 1.0 is a serial-execution finding) + queue wait under load; S8 synthesis latency share (live seed: >95% of an 81.3s turn, EDIR E-006) + truncation rate + token cost; S9 validators false-negative rate on seeded corpora + added latency; S11 receipt assembly latency + zero-unearned-fields §N.8 audit.

**Six synergy tests (test plan §4.3), whole-chain — this is where S4's volume concentrates:**
1. Boundary contract enforcement — inject a malformed object at each of the ten inter-stage boundaries; the chain must refuse loudly at that boundary, never propagate. Demonstrated-can-fail at every seam.
2. Degradation propagation honesty — force each stage's degraded mode and verify it surfaces VISIBLY (refusal/clarification/gap-ribbon/judgment-flag *plus prose disclosure*), never absorbed into a confident-looking answer (E-004 is the canonical seed defect this guards).
3. Trace coherence — one `trace_id` joins all 11 stages + both doors' persistence; reconstruct the full stage sequence from telemetry alone for N live turns; any invisible stage is an observability finding.
4. Latency waterfall accounting — Σ(stage durations) vs. wall-clock; unattributed time above a small tolerance is a finding. Feeds S6 (campaign stream)'s NFR baselines.
5. Progress truthfulness — 1s-cadence snapshots across a deep turn must show monotone, phase-accurate, elapsed-accurate advancement on both doors (E-003 seed defect: frozen progress message during synthesis).
6. Cross-door stage parity — the §4.1 per-stage MCP track plus the PPR-30 whole-receipt parity check, same question/chart/build.

**Journey J10 (door parity, elevation crosswalk):** same question/chart/build through Portal and `prashna_ask`; compare the normalized persisted receipt projection (whole-receipt) plus the §4.1 per-stage parity track.

Freeze your denominator: at minimum, 11 stages × 4 dimensions (correctness/optimality/failure-honesty/demonstrated-can-fail) + 3 dual-door repeats (S1/S5/S8 pipeline-stages) + 6 synergy tests + 1 J10 whole-receipt parity — state your exact final count and its derivation in your `work_started` payload before executing.

## Evidence rungs required

Boundary-injection and demonstrated-can-fail tests are INTEGRATION-rung by nature (a real harness, not a read). Trace-coherence and progress-truthfulness need LIVE-rung (real deployed turns) — re-verify the deployed SHA note above before citing a LIVE result.

## EDIR_V3 seeds

`../EDIR_V3_REGISTER_v1_0.md` — file S4 findings as `V3-E-0NN`, `stream: S4`. Note V3-E-004 (a PRELIM branch-census grading on `codex/pariprashna-shadow-deploy`'s `elevation_service.py`) is tracker-infrastructure, not pipeline — not your territory despite the P-PIPE-adjacent name; leave it filed as-is.

## Posture

Trace/harness-heavy, highest volume of the six streams. Sonnet/medium for finder/investigator at volume (12-concurrent exception applies); Sonnet/high verifier default, Opus/high for any S1-severity finding. Waterfall/latency data feeds S6 — coordinate via referral, don't duplicate S6's own NFR battery.
