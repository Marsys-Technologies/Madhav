---
artifact: PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN
version: 2.1
status: CURRENT — the master test plan governing P3 stream execution. Promoted
  2026-08-27 from the self-paused historical campaign's PROPOSAL artifact; see
  promotion note below. Still authorizes no code, deployment, flag change, data
  mutation, or campaign-state transition on its own — dispatch of the P3 streams
  it describes remains gated on CG-2 closing per the campaign dependency law
  (P0→P1→P2→P3; see PARIPRASHNA_CODEX_TO_CLAUDE_CODE_HANDOFF_v1_0.md §4.1). This
  document fixes WHAT the assurance programme is, not WHEN it may run.
date: 2026-08-24
promoted_date: 2026-08-27
authoritative_side: claude
role: >
  The full experience-and-assurance test programme for Paripraśna. v2.0 elevates
  v1.0 on three native directives: (1) the channel-neutral pipeline is now tested
  stage-by-stage — each stage individually for correctness AND optimality, and all
  stages synergistically as one product; (2) the UX battery is executed by the
  agent through the real deployed Portal in a browser, experiencing the product
  as a user does; (3) every end-to-end run is a GUIDED execution — the agent
  observes the surface, the wire, and the serving code behind them in one pass,
  and every divergence lands as a structured entry in the companion EDIR register,
  which is the programme's primary fix-driving output.
promotion_note: >
  This artifact originates on the self-paused campaign branch
  `campaign/pariprashna-assurance-autonomous` at commit c41d01bf0, under
  `00_ARCHITECTURE/briefs/pariprashna_swarm/`. It is copied here byte-for-byte
  below the frontmatter (body untouched) at the explicit, recorded direction of
  the project owner (Claude Code session, 2026-08-27), who confirmed via an
  explicit choice — offered specifically because promotion is a governance
  decision this repo's own handoff material (PARIPRASHNA_CODEX_TO_CLAUDE_CODE_
  HANDOFF_v1_0.md §1.2) says is NOT self-authorizing from merely reading that
  handoff — that the intent was "formally promote it as the current plan," not
  merely make it locally readable. The companion EDIR register
  (PARIPRASHNA_EXPERIENCE_DEFECT_AND_IMPROVEMENT_REGISTER_v1_0.md, 7944 lines)
  is deliberately NOT copied alongside it: P1's own historical-inventory
  manifest (P1_HISTORICAL_INVENTORY_AND_EVIDENCE_MANIFEST_v1_0.md) already
  classifies that register as ACCEPTED_PRIMARY_EVIDENCE in place at its
  historical path, without importing it — duplicating it here would create a
  second copy of a living, append-only register, which is exactly the
  GA.1-class "registries must not disagree" failure mode this project's own
  doctrine (B.8) warns against. The register stays cited by reference at its
  original path; this promotion changes where the test PLAN lives, not where
  the FINDINGS live.
relates_to:
  - 00_ARCHITECTURE/PARIPRASHNA_ARCHITECTURE_v1_0.md
  - 00_ARCHITECTURE/PARIPRASHNA_VERIFICATION_MATRIX_v1_0.md
  - 00_ARCHITECTURE/PARIPRASHNA_ASBUILT_BASELINE_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_swarm/PARIPRASHNA_EXPERIENCE_DEFECT_AND_IMPROVEMENT_REGISTER_v1_0.md
    (intentionally left at its historical path on campaign/pariprashna-assurance-autonomous
    — see promotion_note; not present on main)
  - 00_ARCHITECTURE/briefs/pariprashna_v012/NFR_SLO_AND_EVAL_v0_1_PROPOSAL.md
  - 00_ARCHITECTURE/briefs/pariprashna_build/BRIEF_PB-4.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/TEST_PLAN_PROMOTION_DECISION_v1_0.md
    (the decision record for this promotion)
proof_law: >
  STATIC → REPLAY → INTEGRATION → LIVE → NATIVE ACCEPTANCE. A lower rung never
  substitutes for a higher rung. A green suite, a merged PR, a flag, or a code
  review is not live-product evidence.
test_data_law: >
  All live probes default to the synthetic consented chart
  1c826d5a-41cb-4450-b4dc-59d440e5f75a (Abhinandan Mohanty). The native's real
  chart (482012f1) is used only where a scenario specifically requires it AND
  the native has authorized that specific use. Restore drills, credential
  revocation, and destructive-adjacent exercises additionally require their own
  stipulated authority per Verification Matrix rows PPR-27/PPR-33.
changelog:
  - "2.1 (2026-08-27, Claude Code): PROMOTED from the historical campaign's
    PROPOSAL artifact to CURRENT status at
    00_ARCHITECTURE/briefs/pariprashna_assurance/ on origin/main, per explicit
    native/owner direction recorded in promotion_note above and in the
    companion TEST_PLAN_PROMOTION_DECISION_v1_0.md. Body content (§1–§12)
    unchanged from v2.0 — this is a status/location promotion, not a content
    revision. The EDIR register it depends on was deliberately NOT copied
    alongside it (see promotion_note)."
  - "2.0 (2026-08-24, Claude/Fable 5): elevation on three native directives —
    new §4 Pipeline Assurance Programme (per-stage + synergy, code-anchored);
    §5 rebuilt as agent-executed browser battery; new §6 Guided Execution
    Protocol (three-lens glass-box method) with the EDIR as primary output;
    §11 execution order now names G7–G9 explicitly instead of omitting them;
    synthetic-chart default promoted from a principle to frontmatter law;
    PPR-17 rung-label correction folded into §12 deliverables. Seed evidence
    from the 2026-08-23 reconciliation session cited throughout."
  - "1.0 (2026-08-24, codex): initial proposed experience-and-assurance test plan."
---

# Paripraśna — Experience and Assurance Test Plan

## 1 — Purpose and release posture

Paripraśna is not ready merely because its route returns prose. A user must be
able to ask, understand what is happening, read a stable and grounded answer,
inspect why a statement is supported, return to it later, and recover honestly
from interruption or uncertainty. The same turn must also remain safe,
authorized, auditable, reproducible, and operationally supportable — and the
pipeline that produces it must be demonstrably healthy at every one of its
eleven stages, not only at its mouth.

This plan makes those outcomes testable. It supplements the PPR verification
matrix; it does not replace or loosen it. Any row below that requires LIVE or
NATIVE ACCEPTANCE evidence remains open until dated evidence against the
deployed artifact is attached.

**What is new in v2.0, in one paragraph.** v1.0 tested the product from its two
doors inward — outputs, surfaces, journeys. It never opened the pipeline. This
version adds three things: a per-stage pipeline assurance programme (§4) that
tests each of the eleven stages individually for correctness and optimality and
all of them together for synergy; an execution model (§5) in which the agent —
not a script alone — drives the deployed Portal in a real browser and
experiences every journey as a user; and a guided-execution protocol (§6) that
exploits the agent's unique position of seeing the browser, the wire, and the
serving code simultaneously, converting every divergence into a structured
entry in the Experience Defect & Improvement Register (EDIR), the artifact this
whole programme exists to fill and the native will use to direct fixes.

### 1.1 In scope

- the Portal Paripraśna surface: history sidebar, main reading viewport,
  working region, answer, citations, right dock, composer, errors, recovery,
  mobile layout, and Samīkṣā affordances;
- the equivalent `prashna_ask` / `prashna_status` door where parity is required;
- **the channel-neutral pipeline itself, stage by stage** (§4): classifier,
  entitlement, safety gate, scope resolution, planner, tool broker, evidence
  assembly, synthesis/adjudication, validation, reading-parts assembly,
  provenance/receipt;
- response quality, safety, consent, privacy, persistence, provenance,
  prediction lifecycle, accessibility, performance, resilience, and release
  operations;
- the observable experience of a real user, rather than component appearance
  alone.

### 1.2 Out of scope

- changing the current architecture, feature flags, data, model policy, or
  release sequence;
- declaring any PPR, gate, lane, or campaign complete;
- re-testing the sealed L0–L5 engine layers for their own correctness (that is
  the layer seals' and the Nirmāṇa campaign's territory) — the pipeline
  programme in §4 tests Paripraśna's *consumption* of those layers, not their
  internal build;
- inventing a second history, quality, or telemetry system where the existing
  contracts already define one.

### 1.3 Test principles

1. **User outcome over component presence.** A visible control passes only
   when it changes the promised user-observable behaviour.
2. **Demonstrated-can-fail.** Every blocking check has a seeded or controlled
   violation which demonstrably turns it red.
3. **Real route before release.** Fixtures exercise edge cases; they never
   stand in for a deployed-route proof.
4. **Honest absence.** A gap, empty state, degraded provider, or unfinished
   turn is stated plainly, never filled with plausible-looking content.
5. **Synthetic chart by default.** Per the frontmatter test-data law. A probe
   against the native's real chart without specific authorization is itself an
   EDIR process finding (see EDIR E-010 for the precedent).
6. **Every divergence is a register entry.** No finding lives only in a chat
   transcript, a screenshot folder, or an agent's memory. If it was observed
   and it diverges from expectation, it gets an EDIR row with evidence, or it
   didn't happen.
7. **Optimality is a test dimension, not a vibe.** "Working" and "working in
   an optimized manner" are different claims. Each pipeline stage carries a
   quantitative optimality criterion (§4.2) with a measured baseline, so
   "suboptimal" is a number, never an impression.

## 2 — Assurance pyramid and evidence package

| Layer | Purpose | Required evidence |
|---|---|---|
| Unit | Deterministic transformations, state machines, and policy edges | focused test name and demonstrated red proof |
| Replay | Recorded SSE, reducer, visual-state, and failure fixtures | fixture id + result, including malformed/slow streams |
| Integration | UI, route, database, outbox, authz, and model adapter together | isolated service/DB result and artefact hash |
| Live | Deployed URL, production-shaped auth, real persistence and telemetry | timestamped probe transcript, browser observation, DB query, or dashboard link |
| Native acceptance | Week-of-use trust and friction judgement | seven daily rubric cards and explicit binary verdict |

Every release-gate evidence packet records: commit SHA, deployed revision,
environment, chart class, test data disposition, exact scenario, observed
result, expected result, evidence link, rollback/recovery result, and whether
the check was made to fail. A pass without this packet is a finding, not a
release signal.

## 3 — The three examination programmes

The plan now runs three interlocking programmes. Each produces EDIR entries;
none replaces another; a turn is only fully assured when all three have
covered it.

| Programme | Question it answers | Method | Section |
|---|---|---|---|
| **P-PIPE** — Pipeline assurance | Is each stage correct, optimal, and honest — alone and in concert? | Stage-isolated harness runs + full-trace waterfall accounting | §4 |
| **P-PORTAL** — Agent-as-user browser battery | Does a real user, in a real browser, on the deployed product, get the promised experience? | Agent-driven Playwright/CDP sessions against the deployed Portal | §5 |
| **P-GUIDED** — Guided glass-box executions | For one real turn, does what the user saw, what crossed the wire, and what the code did all tell the same true story? | Three-lens trace: surface ↔ wire ↔ code, per journey | §6 |

## 4 — P-PIPE: the Pipeline Assurance Programme

The channel-neutral core (`ARCHITECTURE §3`) is a chain of eleven typed
stages. v1.0 tested only its ends. This programme opens the chain: every stage
is tested **individually** (correctness, optimality, failure honesty,
demonstrated-can-fail) and the chain is tested **synergistically** (boundary
contracts, degradation propagation, trace coherence, latency accounting).

### 4.1 Stage inventory with code anchors

Each stage row binds to the modules that implement it, so tests target real
seams and EDIR entries carry real anchors. The stage-contract spine is
`platform/src/lib/pariprashna/pipeline/stage_context.ts`; the Portal
orchestrator invoking every stage in order is
`platform/src/app/api/pariprashna/route.ts`.

| # | Stage (port) | Primary implementation | Individual assurance focus |
|---|---|---|---|
| S1 | NormalizedQuery → intent/scope classification | `platform-mcp/src/tools/intent_scope_classifier.ts` · `platform/src/lib/vidhi/scope_classifier.ts` | Classification accuracy corpus (per intent × domain × depth); ambiguity → ClarificationRequest, never a guessed tuple; adversarial phrasings mis-classify safely |
| S2 | EntitlementDecision | `platform/src/lib/pariprashna/pipeline/safety_gate.ts` (~line 226) · `platform/src/lib/auth/authorizeChartAccess.ts` · `CHART_REQUIRED` at `platform/src/lib/gateway/invoke_tool.ts:80` | Resolves from the authenticated call ONLY (PPR-11); fail-closed on every denial path; question text can never widen entitlement |
| S3 | SafetyPolicyDecision | `platform/src/lib/pariprashna/pipeline/safety_gate.ts` (refusal path ~line 281) | Runs BEFORE planning (PPR-12); each HS-1..6 hard stop observably blocks/reframes/seals; receipt records the action |
| S4 | ScopeTuple / ClarificationRequest | `platform/src/lib/vidhi/scope_classifier.ts` (`ScopeTupleSchema`) | Tuple → depth/width actually changes downstream behaviour (ties to PPR-16's missing visible-depth fixture / GAP-8) |
| S5 | AcharyaPlan (planner) | `platform/src/lib/pariprashna/pipeline/plan_stage.ts` · `platform/src/lib/pipeline/pipeline_planner.ts` · floor compilation via `compiled_floor_adapter.ts` + `vidhi/compiler.ts` · `budget_arbiter.ts` · `no_leakage_filter.ts` | Plan quality vs. floor oracle: B.11 floor coverage compiled in, never by convention (PPR-15); NO-LEAKAGE strip observable (live seed: `lel_query` stripped, 2026-08-23); budget arbitration never silently zeroes a floor-mandated tool |
| S6 | ToolBroker → dispatch | `platform/src/lib/pariprashna/pipeline/evidence_stage.ts` · `retrieval/qos/dispatch_queue.ts` | Per-tool latency within budget; parallelism actually parallel (waterfall test, §4.3); cap ceiling honest (`cap_tripped` earns its value per §N.8); unserved/unresolved lists truthful |
| S7 | EvidenceBundle assembly | `evidence_stage.ts` · `platform/src/lib/bundle/bundle_hydrator.ts` | Empty results reported as empty (never dropped, never faked); bundle content = exactly what dispatch returned |
| S8 | Interpretation & Adjudication (synthesis) | Portal: `pipeline/synthesis_stage.ts` · MCP: `platform/src/lib/pipeline/prashna_ask_synthesis.ts` (truncation flag set at line 380) | Evidence-truncation is DISCLOSED in reader-visible prose, not only flagged in the envelope (live seed defect: EDIR E-004); every asserted fact traces to bundle evidence; alternatives/falsifiers surface per §5 quality dimensions |
| S9 | Grounding/Safety Validation | `pipeline/validation_stage.ts:47` · `synthesis/streaming_citation_validator.ts` · register-leak lint `citations/register_leak_lint.ts:174` (call points: `synthesis_stage.ts:827`, `reading_parts.ts:205,463`, `citations/rewriter.ts:217,330`, `reader_text/review.ts:40`) | Every call point actually fires on the live path (not only in fixtures); lint demonstrated-can-fail on the deployed route; citation density measured, not assumed (live seed: 2 footnotes on a many-claim reading, EDIR E-005) |
| S10 | SemanticReadingParts | `pipeline/reading_parts.ts` (`ReadingPartsAssembler`) · `semantics/block_classifier.ts` · renderer `components/pariprashna/answer/FrozenBlock.tsx` + block components | Block classification correct per semantic type; GAP-6's unbuilt producers (verse/gap-ribbon/heading/roles/prediction_card) never silently downgrade to paragraph without an honest marker |
| S11 | TurnProvenance + AcharyaReadingReceipt | `receipt/assemble.ts:538` · `receipt/{schema,validate,hash,store}.ts` · called from `persistence_stage.ts:554` · completeness via `receipt_stage.ts` + `vidhi/completeness_receipt.ts` | Every receipt field earned by a real detector (§N.8); receipt ↔ rendered prose agreement (a claim in prose absent from receipt grounding = finding); hash stability across re-render |

**MCP-door parallel track.** S1/S5/S8 have MCP-side twins
(`platform-mcp/src/resources/vidhi/plan_builder.ts`, `scope_resolver.ts`,
`prashna_ask_synthesis.ts`, job progress at
`platform-mcp/src/tools/register_prashna_ask.ts:202`). Every stage test that
can run on both doors runs on both; a stage passing on one door and failing on
the other is a PPR-30 parity finding, filed per-stage rather than as one
opaque "doors differ."

### 4.2 Individual-stage optimality criteria

"Optimized" is claimed only against a measured number. For each stage, the
programme establishes a baseline (first measured run), then a target
(ratified after two weeks of measurement, per the NFR proposal's own
provisional discipline). Minimum criteria set:

- **S1 classifier:** accuracy ≥ target on the versioned corpus (per §7);
  p95 classification latency; clarification-trigger precision (asks when it
  should, doesn't when it shouldn't — both directions fixtured).
- **S5 planner:** floor-coverage completeness (compiled floor satisfied on
  100% of interpretive turns or receipt carries the honest gap); tool-selection
  efficiency = dispatched tools that contributed evidence actually cited or
  used in adjudication ÷ dispatched tools (a persistently low ratio is
  over-dispatch — cost without value); plan latency share of turn.
- **S6 broker:** per-tool p95 vs. per-tool budget; **parallelism efficiency**
  = wall-clock dispatch window ÷ Σ(individual tool latencies) — near 1.0 means
  serial execution of parallelizable calls (finding); queue wait time under
  concurrent load (§9.3).
- **S8 synthesis:** latency share of turn (live seed, 2026-08-23: tool
  dispatch summed ≈4.0s of an 81.3s turn — >95% of wall time sits in
  planning/synthesis/overhead, EDIR E-006 — this is exactly the class of
  insight per-stage accounting exists to surface); truncation rate; token cost
  per turn class.
- **S9 validators:** false-negative rate on seeded leak/citation corpora
  (100% seeded-id catch retained per PPR-04); added latency ≤ budget.
- **S11 receipt:** assembly latency; zero unearned fields on the §N.8 audit.

### 4.3 Synergistic (whole-chain) assurance

1. **Boundary contract enforcement.** Every port's output is schema-validated
   at the boundary ("a malformed object never crosses" — ARCHITECTURE §3).
   Test: inject a malformed object at each of the ten boundaries in an
   integration harness; the chain must refuse loudly at that boundary, never
   propagate. Demonstrated-can-fail at every seam.
2. **Degradation propagation honesty.** Force each stage into its degraded
   mode (classifier low-confidence, entitlement denial, safety reframe, tool
   timeout, empty bundle, synthesis truncation, validator strip) and verify
   the degradation is VISIBLE at the surface in the designed form — refusal,
   clarification, gap ribbon, judgment flag *plus prose disclosure* — never
   absorbed into a confident-looking answer. (The truncation-undisclosed seed
   defect E-004 is the canonical instance this test class exists to catch.)
3. **Trace coherence.** One `trace_id` joins all eleven stages plus both
   doors' persistence. Test: for N live turns, reconstruct the full stage
   sequence from telemetry alone; any stage invisible in the trace is an
   observability finding.
4. **Latency waterfall accounting.** Per turn: Σ(stage durations) vs.
   wall-clock. Unattributed time above a small tolerance is a finding (it is
   where regressions hide). The waterfall is the primary artifact of every
   guided execution (§6) and feeds the §9 SLO baselines.
5. **Progress truthfulness.** The user-facing progress channel (Portal working
   region; MCP `prashna_status`) must track actual pipeline position. Live
   seed defect: progress message froze at "10/~25 tool calls made, 4.0s
   elapsed" from ~32s to ~67s of an 81s turn while synthesis ran — stale
   message, stale elapsed figure, no synthesis-phase signal
   (`register_prashna_ask.ts:202`; EDIR E-003). Test: progress snapshots at
   1s cadence across a deep turn must show monotone, phase-accurate,
   elapsed-accurate advancement on both doors.
6. **Cross-door stage parity.** §4.1's per-stage MCP track, plus the PPR-30
   whole-receipt parity check, run on the same question/chart/build.

## 5 — P-PORTAL: the agent-executed browser battery

**Execution model (native directive).** The screen-level battery below is
executed by the agent driving a real browser (Playwright / Chrome DevTools
automation) against the **deployed** Portal — not against a local fixture
server, and not by human clicking alone. The agent runs each journey as a
user, captures evidence (screenshots, accessibility snapshots, console and
network logs, timing), and — because the same agent can read the serving code —
escalates anything surprising straight into a §6 guided execution rather than
filing a shallow "it looked wrong."

### 5.0 Access prerequisites (blocking, resolve before first run)

| Prerequisite | Status | Action |
|---|---|---|
| Deployed Portal URL (`/clients/[id]/pariprashna`) | Known (`amjis-web` Cloud Run service) | pin exact revision in the preflight packet |
| Authenticated session for the synthetic chart (Firebase) | **NOT provisioned for agent use** | native to provision a test credential scoped to chart `1c826d5a` only; its scope proven by a cross-chart denial probe before any journey runs; revocable same-day (PPR-27 discipline) |
| Browser automation tooling | Available (Playwright MCP / CDP MCP) | verify against deployed URL in preflight |
| Baseline screenshot store + diff policy | Not yet established | create per §8.1 before first visual assertion |

The credential item is the known blocker class from DD-33 (the malformed
`FIREBASE_ADMIN_CREDENTIALS` CI credential parked P3-E's smoke). This plan
does not work around it; it names it as the first preflight item.

### 5.1 Screen-level battery

Run on desktop, tablet, and mobile viewports, in light/standard system
settings plus reduced motion, high zoom, and poor-network cases where
applicable.

| Region | What the user must experience | Automated coverage | Agent-in-browser proof |
|---|---|---|---|
| **History sidebar** | Past readings grouped by chart then recency; active and streaming states unmistakable; collapse state remembered; title, relative time, keyboard activation, empty/loading/error state, and long-title truncation clear. Selecting a real prior thread swaps it in-shell with no reload or data leak. | component, route, keyboard, visual-regression, large-list performance | revisit a saved reading after refresh and from a second session; locate an old reading unaided; attempt (and be denied) another chart's thread |
| **Main viewport** | A focused, stable reading surface. Settled blocks never jump or mutate; only one live tail changes; scroll follows only while the reader has not intentionally scrolled away. Tables, verses, honest gaps, errors, clarification asks, and prediction cards read as their actual semantic type. | reducer/replay, CLS/caret/viewport/transmutation browser gates, semantic-block contract | complete a deep reading; inspect a table and a difficult finding; interrupt and resume without losing place |
| **Working region** | Progress is informative, calm, and truthful: what the instrument is doing, without internal ids, fabricated certainty, or distraction. **Truthfulness is now testable against the §4.3.5 progress-cadence check — the surface must not claim less (or more) progress than the pipeline has made.** | event schema, lexicon, throttle and ARIA tests | can the agent-as-user tell "working", "waiting", "needs clarification", and "finished" apart at every 5s sample of a deep turn? |
| **Right dock** | Citation chips open the exact evidence card: source, evidence grade, confidence, relevance, caveat. Alternatives and falsifiers discoverable, not forced into prose. Empty states explain absence. | chip-to-card, focus, scroll/highlight, confidence, visual and a11y tests | answer "why should I trust this sentence?" and "what would change it?" quickly and accurately, from the dock alone |
| **Composer** | Input labelled, focus predictable, usable by keyboard, IME, paste, touch, mobile keyboard. Send, Stop, retry, validation work. Model/depth/length settings either affect the request and received outcome or are absent. | component/contract tests, mobile viewport and keyboard tests | toggle each setting; confirm the resulting turn is intelligibly different where promised (GAP-8's cosmetic pickers are the seeded-failure case) |
| **History, return, memory** | A settled reading survives refresh, relogin, reconnect, device return, chart switch. History is private, fast, semantically identical to the sealed original. | persistence, replay parity, authz, cross-chart denial, performance tests | return to a prior reading, locate its supporting citation, continue the conversation naturally |
| **Errors and recovery** | A failure explains what happened, protects entered text, identifies incomplete content, provides a safe next step, never silently promotes a partial answer. | failure, disconnect, snapshot, outbox, retry, chaos fixtures | deliberately kill the network / press Stop mid-turn; recover without reconstructing context by hand |

### 5.2 Mandatory user journeys

1. First visit: orient to the chart, understand the empty state, choose a
   prompt, ask a question.
2. Standard interpretive reading: stream, inspect a citation, open a
   non-selected interpretation, understand a falsifier.
3. Timing/deep-dive reading: inspect a semantic table/verse and retain place
   through a long stream.
4. Sensitive or blocked request: a calm, safe, unambiguous response; no
   unsafe answer path.
5. Clarification: answer the instrument's question; the resulting turn
   retains context without accidental re-submission.
6. Interruption: Stop or disconnect mid-turn; return via replay or disclosed
   incomplete state.
7. History: return after reload, select a prior thread, rename if permitted,
   verify no other chart is accessible.
8. Prediction: identify a prediction, log/review it, resolve it including
   "can't tell", verify its state visible and reversible only via the defined
   lifecycle.
9. Mobile: journeys 1, 2, 4, 6 on a 390×844 viewport with software keyboard
   open.
10. Door parity: same question/chart/build through Portal and `prashna_ask`;
    compare the normalized persisted receipt projection (whole-receipt), plus
    the §4.1 per-stage parity track.

**Every journey is run in guided mode (§6) at least once.** Repeat runs for
regression may be surface-only, but the first pass of each journey per gate
produces a full three-lens record.

## 6 — P-GUIDED: the Guided Execution Protocol

The native's directive, stated plainly: the tester here is not a black-box
user. The agent has the browser AND the code AND the database. A guided
execution exploits all three at once, so a single turn yields not "it worked /
it didn't" but a complete account of what worked, what didn't, and what fell
short of its own design intent — each shortfall filed, evidenced, and
anchored to the code that produced it.

### 6.1 The three lenses

Every guided execution records one turn through three synchronized lenses:

| Lens | What is captured | Instruments |
|---|---|---|
| **L-USER** (surface) | What a user saw and could do: screenshots at state transitions, the rendered reading, progress messages as sampled, controls exercised, moments of confusion or wait | agent-driven browser, timestamped |
| **L-WIRE** (transport + data) | The SSE event sequence (or `prashna_status` poll series), request/response envelopes, judgment flags, completeness receipt, DB rows written (message_parts, receipt store, prediction ledger, llm_usage_events), per-tool latencies, cost | network capture, envelope archive, read-only DB queries |
| **L-CODE** (mechanism) | Which stage modules handled the turn (per the §4.1 anchor map); for every L-USER or L-WIRE anomaly, the specific code path that produced it, read and cited as file:line | repository read access, §4.1 anchor map |

### 6.2 The divergence discipline

After each guided run, the three lenses are reconciled. A divergence is any of:

- **surface ≠ wire** — the envelope knows something the user wasn't told
  (seed instance: `synthesis_evidence_truncated` in judgment_flags, nothing in
  prose — E-004), or the surface implies something the wire doesn't support;
- **wire ≠ code intent** — the recorded behaviour contradicts what the
  implementing module is written to do, or exercises a path its tests never
  cover (seed instance: progress message computed once at dispatch and never
  refreshed through synthesis — E-003 at `register_prashna_ask.ts:202`);
- **code ≠ design** — the module's behaviour is faithful to its code but the
  code falls short of the ratified requirement (PPR row, §N.6/§N.7/§N.8
  doctrine, or this plan's optimality criteria);
- **anything ≠ expectation of quality** — no rule violated, but the
  experience, latency share, citation density, or prose honesty is below the
  standard the native would accept (these file as IMPROVEMENT class, not
  DEFECT class — the register holds both).

Every divergence becomes an EDIR entry **before the session ends**, with all
three lenses' evidence attached. No divergence is "noted for later."

### 6.3 The register (EDIR) — primary output

The companion artifact
`PARIPRASHNA_EXPERIENCE_DEFECT_AND_IMPROVEMENT_REGISTER_v1_0.md` is the
programme's single accumulation point and the native's fix-direction surface.
Schema (every entry):

`E-nnn · title · class (DEFECT / IMPROVEMENT / BASELINE / DOC / PROCESS) ·
severity (S1 blocking / S2 major / S3 minor / S4 polish) · lens(es) ·
pipeline stage (S1–S11 or SURFACE/CROSS) · journey · expected (with the
requirement or doctrine it traces to) · observed (dated, evidenced) · code
anchor (file:line) · PPR / gap-register cross-reference · proposed fix class ·
status (OPEN → TRIAGED → FIX-PLANNED → FIXED → VERIFIED@rung → CLOSED, or
PARKED / RETRACTED) · verification rung required to close`

Register law, inherited from the project's own doctrine: an entry closes only
at its named rung with dated evidence (§N.8 — the fix must be *demonstrated*,
not merged); a RETRACTED entry keeps its full history; severity is assigned at
triage, not by the finder; the register never self-certifies a gate.

The register opens pre-seeded with the eleven findings of the 2026-08-23
reconciliation session (PPR-26 audit-grant failure, C1 RLS absence, stale MCP
progress, undisclosed truncation, citation density, latency waterfall
baseline, stale/empty evidence cells, rung mislabel, real-chart probe process
finding) so the programme starts from evidence, not a blank page.

## 7 — Reading-quality and epistemic evaluation

Maintain a versioned corpus for factual, interpretive whole-chart, timing,
cross-domain contradiction, remedial, sensitive, ambiguous/clarification,
incomplete-evidence, returning-conversation, disagreement/correction,
prediction/outcome, and Portal–MCP parity queries. Each work class has at
least five fixtures before qualification; new failures become regression
fixtures after triage. The same corpus drives the S1 classifier-accuracy
metric (§4.2), so classifier and reading quality are scored from one
versioned source.

| Dimension | Pass condition |
|---|---|
| Factual integrity | every asserted fact resolves to the referenced source; no re-derived shadow value |
| Acharya floor | required B.11 coverage present, or the receipt carries an honest, comprehensible gap |
| Reasoning quality | significant judgement has alternatives, selection rationale, and falsifier, or measured waiver |
| Citation usefulness | citations support the exact claim, show their grade, and can be understood by a reader; **citation density measured per reading and reported** (seed baseline: E-005) |
| Confidence honesty | type, language, and numerical precision never exceed the evidence or calibration activation state |
| Safety and consent | sensitive requests take the defined action; no unsafe content, unauthorized chart, or C3 leakage crosses the boundary |
| Voice and clarity | one reader register, Sanskrit glossed inline, no internal identifiers, no imperative remedy, difficult findings lead with uncertainty |
| Model discipline | every serving model passes its work-class qualification; unequal fallback visibly degrades or queues |

Score with deterministic checks where possible, blinded human/native review
for reading quality, and an independent refuter pass for release-blocking
claims. Report failures by dimension, model, provider, query class, and
evidence grade; never collapse them into one flattering aggregate.

## 8 — UX design, visual, and accessibility standards

### 8.1 Visual and interaction regression

Maintain approved visual baselines at desktop, tablet, and mobile for empty,
thinking, streaming (25/50/75/100%), multi-pass, settled, citation-dense,
giant-table, honest-gap, interrupted, reconnecting, error, and dock/sidebar
expanded/collapsed states. Record a reviewable difference image for every
intentional change.

Hard interaction assertions:

- no unexpected layout shift above the volatile tail;
- no post-commit mutation of settled blocks except the explicitly versioned
  citation-anchor transition;
- caret remains inside the live tail; page and viewport geometry remain
  stable while the transcript scrolls;
- no hover-only essential affordance; all key actions work with pointer,
  keyboard, and touch;
- every visible control is functional or absent; no decorative search,
  picker, status, or action.

### 8.2 Accessibility

Target **WCAG 2.2 AA**. Automated axe is a floor, not proof. Test every
screen state for zero critical/serious violations, then manually verify:

- keyboard-only navigation, logical focus order, visible focus, Escape
  behaviour, no focus obscured by composer, dock, sheet, or keyboard;
- VoiceOver and NVDA smoke of empty, stream, settled, citation, error, and
  reconnect states; one polite live region only, with settled blocks removed
  from it;
- 200% zoom/reflow, contrast, 44×44px touch targets where the action is
  touch-first, reduced motion, no drag-only interaction;
- accessible names, roles, values, status announcements, input instructions,
  and error recovery.

Note for the §12 matrix: the G-MOBILE and G-AXE suites already exist and pass
(30/30 with seeded red-proofs, verified 2026-08-23) — the Verification
Matrix's PPR-19 "pending" annotation is stale (EDIR E-007). The remaining
work here is the manual screen-reader/zoom/contrast battery, not the
automated floor.

### 8.3 Usability and comprehension sessions

Run moderated, task-based sessions before the default flip. Include a
first-time reader, returning reader, mobile-first reader, and a reader
encountering a difficult/sensitive response. Observe rather than teach. For
each journey, record completion, time, wrong turns, help requested,
comprehension of evidence/uncertainty, perceived trust, free-form friction.

The release question is not "did the participant like the screen?" It is:
"could they find, understand, challenge, return to, and safely act on the
instrument's output without being misled by the interface?"

## 9 — Security, safety, privacy, and data integrity

These existing PPR tests are release blockers, not back-office work:

- deployed hard-stop corpus for mortality, self-harm, health/mental-health,
  retraction, and predictive sampling; each must demonstrably block/reframe/
  seal and record the receipt action;
- question-borne and retrieved-content prompt injection, plan-closure,
  tool-sequence anomaly, and cross-chart exfiltration attempts;
- object-level authorization, roles/grants, RLS cross-context denial,
  consent-absent/minor/withdrawal/deletion workflow, disclosure-class
  restrictions, and audit hash-chain or INSERT-only proof — **the 2026-08-23
  live probes already show PPR-26 failing (app credential holds
  DELETE/UPDATE/TRUNCATE on `audit_log`; EDIR E-001) and zero RLS policy
  objects on the C1 tables `chart_facts`/`chart_dashas` (E-002, sharper than
  GAP-2's "defined but inert"); these enter the G1 lane as confirmed
  defects, not open questions**;
- rate and spend limits on both doors, provider data-posture checks,
  no-leakage canary/mutation checks, same-day credential/session revocation
  drill;
- crash-consistent persistence, replay, semantic-hash parity, schema
  compatibility, immutable provenance, prediction immutability, restore drill.

## 10 — Performance, resilience, and operational quality

### 10.1 Metrics to collect

RUM plus server traces for first signal, TTFT, full-turn latency by work
class, **per-stage latency waterfall (§4.3.4)**, delta-to-commit lag, largest
inter-event gap, reconnect/replay and snapshot rate, persistence outcome,
client errors, Core Web Vitals, cost per turn/user/channel/model, safety
verdicts, lint firings, prediction capture/resolution coverage. Segment by
device class, network quality, model, and request class.

### 10.2 Provisional experience targets

The existing NFR proposal remains provisional until two weeks of real
measurement. Its intended Paripraśna targets: first signal <300ms; TTFT p50
<4s and p90 <12s for interpretive turns; factual TTFT p50 <2s; factual turn
p95 <20s, interpretive p95 <90s, deep-dive p95 <240s; ≥99% replay recovery
within buffer TTL with zero content loss; no settled turn silently undurable.
First live sample on record: 81.3s end-to-end for one standard interpretive
turn via the MCP door (2026-08-23, EDIR E-006) — inside the provisional p95,
with >95% of wall time in planning/synthesis, which is where optimization
attention goes first.

Also track Core Web Vitals at the 75th percentile: LCP ≤2.5s, INP ≤200ms,
CLS ≤0.1. Page-experience measures; they do not replace turn-level TTFT or
quality evidence.

### 10.3 Resilience and load battery

Controlled load and failure tests for slow first token, 1-byte trickle, long
inter-event gap, provider timeout, malformed citation sentinel, giant table,
citation-dense answer, reconnect inside/outside buffer TTL, visibility-change
reconnect, server loss mid-persist, outbox retry, provider fallback,
rate/spend rejection, and concurrent interactive/batch pressure.

The result reports tail latency, failures, recoveries, lost/duplicated
blocks, memory/CPU growth, queue shedding, cost, and whether the reader
received an honest visible state. A throughput number without these user
outcomes is not a pass.

## 11 — Execution order and release decision

1. **Preflight:** pin commit/revision, freeze the artifact, classify test
   data, provision and scope-prove the §5.0 test credential, verify
   environment, confirm test authority.
2. **Safety and integrity (G1):** run G1 privacy/authz/DR checks first —
   starting from the two confirmed G1 defects E-001/E-002 rather than from
   zero. Stop on any exposure, authorization, consent, safety, or restore
   failure.
3. **Pipeline assurance (P-PIPE, cross-gate):** establish the §4 stage
   baselines and boundary-contract proofs early — they instrument everything
   after them and their waterfall feeds G5's SLO baselining.
4. **Surface truth (G2):** semantic/render/citation/control/persistence/
   provenance/mobile/a11y batteries via §5 agent-in-browser runs; attach
   live evidence.
5. **Quality (G3):** corpus, receipt, confidence, voice, model qualification.
6. **Parity (G4):** Portal–MCP persisted semantic-receipt parity plus the
   per-stage parity track.
7. **Performance and canary (G5):** two-week measurement, bind approved SLOs,
   demonstrated-can-fail post-deploy smoke, seven consecutive green smokes.
8. **Native acceptance (G6):** the seven-day AC-15 experience review; binary,
   native-owned.
9. **Hygiene sweep (G7):** the Baseline's GAP-15 (dead error classifier) and
   GAP-17 (audience_tier residue) close here; the sweep also retires any EDIR
   DOC-class entries still open.
10. **Feedback and dispute (G8):** window-overlap ask (PPR-18), dispute
    capture and digest transport (PPR-31 / GAP-12), post-six-views narration
    audit (GAP-18).
11. **Calibration seal (G9):** calibration sink and scoring-method suite
    (PPR-28/29 / GAP-13). **G8 and G9 are sequenced after native acceptance
    deliberately — they gate the instrument's learning loop, not its
    conversational release — but they are named here so their omission is a
    decision on record, not a silence** (v1.0 omitted them without comment;
    that omission class is exactly what test principle 4 forbids).
12. **Post-release:** monitor the same metrics, sample reading quality,
    re-run safety/adversarial corpus on policy or model change, execute
    restore drills quarterly, add every material production defect to the
    EDIR and its fix to regression.

Release is **NO-GO** if any blocking PPR lacks its required proof rung; if a
control is decorative; if an unsafe, unauthorized, or silent-loss path is
found; if any S1-severity EDIR entry is OPEN; if the reader cannot understand
evidence and uncertainty; or if the recovery and monitoring evidence cannot
distinguish a healthy experience from a silently degraded one.

## 12 — Deliverables and evidence ledger

Before the gate package can be presented, produce:

- **the EDIR, current and complete** — every observed divergence, all three
  lenses of evidence, statuses honest (this is the primary deliverable; the
  rest support it);
- a traceable test matrix mapping every scenario here to PPR, pipeline stage,
  owner, test layer, required rung, automation location, and dated evidence —
  and correcting the known Verification Matrix cell defects while it is
  built (PPR-19 stale "pending"; PPR-03/PPR-05 empty cells despite passing
  suites; PPR-17 rung label STATIC→REPLAY);
- per-stage pipeline baseline report (§4.2 numbers, first waterfall set);
- approved visual baselines and diff-review policy;
- accessibility audit with automated findings, keyboard results,
  screen-reader notes, contrast/touch-target checks, remediation status;
- quality-corpus version, scorer rubric, per-model qualification report,
  regression-delta report;
- live performance/SLO baseline, load/chaos report, dashboard links;
- screenshots/transcripts/DB proofs for the end-to-end guided journeys;
- a release decision record stating PASS, NO-GO, or explicitly PARKED items.

No document in this list may self-certify a gate. The independent verifier
and gate runner must reproduce the claimed evidence from the frozen deployed
artifact.

*End PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN v2.0.*
