---
brief_id: EXEC_BRIEF_PHASE_6
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-27
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PHASE_6_v1_0.md and execute it."
phase: 6
phase_name: LLM Checkpoints
risk_classification: MEDIUM
parallelizable_with: [EXEC_BRIEF_PHASE_4_v1_0.md, EXEC_BRIEF_PHASE_5_v1_0.md, EXEC_BRIEF_PHASE_9_HOTFIX_v1_0.md, M2/B.5 work]
depends_on: [EXEC_BRIEF_PHASE_3_v1_0.md (COMPLETE)]
estimated_streams: 4
---

# EXEC_BRIEF — Phase 6 — LLM Checkpoints

## Mission

Insert three LLM-driven quality gates into the pipeline that catch failure modes the structural validators (P1/P2/P5) cannot detect. The structural validators in Phase 3 verify *form* (layer separation, citation discipline, signal-id resolution); the Phase 6 checkpoints verify *substance*:

- **Checkpoint 4.5 — Resolve→Retrieve gate.** After entity resolution, before retrieval: is the resolved entity actually what the user asked about? Catches subtle ambiguity (e.g., "the Sun in the 4th" — natal Sun, transit Sun, or progressed Sun?) that the deterministic resolver collapsed too early.
- **Checkpoint 5.5 — Retrieve→Validate gate.** After bundle assembly, before synthesis: does the retrieved bundle contain enough material to answer the question, or is a critical signal missing? Catches "I retrieved 19 holistic signals but none of them are about the actual subject of the query."
- **Checkpoint 8.5 — Synthesize→Discipline gate.** After synthesis, before disclosure-tier filtering: does the synthesized answer match the validators' shape AND make a coherent claim? Catches "the validators all passed because the synthesis avoided making any claim at all" (the empty-shell failure mode).

Checkpoint 8.5 also extracts a **structured prediction object** when the synthesis contains a time-indexed claim — replacing the heuristic prediction extractor in Phase 4 Stream C with an LLM-generated typed object.

## Scope (`may_touch` / `must_not_touch`)

**`may_touch`:**
- `platform/src/lib/checkpoints/**` (new — checkpoint module: types, runners, results)
- `platform/src/lib/checkpoints/__tests__/**`
- `platform/src/lib/prompts/checkpoints/**` (new — three checkpoint prompt templates)
- `platform/src/lib/synthesis/orchestrator.ts` (extension only — add checkpoint hook calls behind feature flags; existing behavior preserved when flags off)
- `platform/src/lib/synthesis/__tests__/**` (add checkpoint integration tests)
- `package.json` — add `checkpoint:eval` script for offline accuracy testing

**`must_not_touch`:**
- `platform/src/lib/validators/**` (Phase 3 frozen — checkpoints are *additional* gates, not replacements)
- `platform/src/lib/prompts/*.ts` and existing prompt files outside the new `checkpoints/` subdirectory (Phase 3 prompt registry frozen)
- `platform/src/lib/disclosure/**`, `platform/src/lib/router/**`, `platform/src/lib/bundle/**`, `platform/src/lib/retrieve/**` (frozen)
- `platform/src/lib/audit/**`, `platform/src/lib/prediction/**` (Phase 4 territory — Phase 6 emits via the existing telemetry hook only; does NOT directly write to audit_log or prediction_ledger)
- `platform/src/components/**` (Phase 5 territory)
- `platform/python-sidecar/**`
- Any DB migration (Phase 6 is code-only; Phase 4 owns schema)
- Any flag-OFF code path
- `platform/src/app/api/consume/route.ts` (Phase 3 owns; Phase 6 extends via the orchestrator only)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`

## Sub-streams (4 total)

### Stream A — Checkpoint 4.5 (Resolve→Retrieve)

- New file `platform/src/lib/checkpoints/checkpoint_4_5.ts`. Function `runCheckpoint4_5(input: ResolveOutput): Promise<CheckpointResult>`.
- Prompt template at `platform/src/lib/prompts/checkpoints/checkpoint_4_5.md`. Inputs: original query, resolved entities, list of resolution alternatives the resolver discarded. Output: structured JSON `{verdict: 'pass'|'warn'|'halt', confidence: number, reasoning: string, suggested_revision?: ResolveOutput}`.
- LLM call uses the Phase 0 provider abstraction. Default model: `claude-haiku-4-5` (fast + cheap; checkpoints run inline in the response path).
- Result schema in `platform/src/lib/checkpoints/types.ts`. Zod-validated parse with strict failure mode.
- Behavior:
  - `pass` → continue to retrieval with original resolved entities
  - `warn` → continue but emit warning to telemetry; if `suggested_revision` present, log it but do not apply (deterministic-resolver is source of truth)
  - `halt` → short-circuit synthesis with a structured failure object the UI's `<ValidatorFailureView />` (Phase 5) can render
- Feature flag `CHECKPOINT_4_5_ENABLED` defaults to `false`. Flag-OFF = checkpoint not invoked = zero behavior change.
- Sub-flag `CHECKPOINT_4_5_FAIL_HARD` defaults to `false` (warn-only mode). Native flips to `true` after observing a few weeks of warn data.
- 10+ tests: pass/warn/halt branches; flag-OFF skip; LLM-output parse failure → defaults to pass with warning; latency budget verified (<800ms p95 against Haiku 4.5).

### Stream B — Checkpoint 5.5 (Retrieve→Validate)

- New file `platform/src/lib/checkpoints/checkpoint_5_5.ts`. Function `runCheckpoint5_5(input: RetrieveOutput): Promise<CheckpointResult>`.
- Prompt template at `platform/src/lib/prompts/checkpoints/checkpoint_5_5.md`. Inputs: original query, query class, the assembled bundle's asset_id list + first 200 chars of each, the list of signals retrieved with their definitions. Output: same structured JSON shape as 4.5 with an additional optional field `missing_signal_hints: string[]` (free-text hints about what kinds of signals appear absent).
- Default model: `claude-haiku-4-5`. Larger context window than 4.5's prompt due to bundle content.
- Behavior identical to 4.5 (`pass`/`warn`/`halt`). `halt` short-circuits synthesis. `warn` continues to validate+synthesize; warning logged.
- Feature flags `CHECKPOINT_5_5_ENABLED` (default `false`) + `CHECKPOINT_5_5_FAIL_HARD` (default `false`).
- 10+ tests: pass/warn/halt; missing-signal-hint extraction; flag-OFF skip; bundle-too-large truncation handling; latency budget verified (<1200ms p95).

### Stream C — Checkpoint 8.5 (Synthesize→Discipline) + Structured Prediction Extraction

- New file `platform/src/lib/checkpoints/checkpoint_8_5.ts`. Function `runCheckpoint8_5(input: SynthesisOutput, validatorResults: ValidatorResult[]): Promise<CheckpointResult & {prediction?: StructuredPrediction}>`.
- Prompt template at `platform/src/lib/prompts/checkpoints/checkpoint_8_5.md`. Inputs: synthesized text, validator pass/fail breakdown, query class. Output: structured JSON with the standard `verdict`/`confidence`/`reasoning` fields PLUS an optional `prediction` field that is the structured object Phase 4 expects to log into `prediction_ledger`.
- The `prediction` object schema (zod-validated) matches Phase 4's `Prediction` type:
  ```
  {
    prediction_text: string,
    confidence: number (0-1),
    horizon_start: ISO date string,
    horizon_end: ISO date string,
    falsifier: string,
    subject: string  // default 'native:abhisek'
  }
  ```
- If the synthesis contains no time-indexed claim, the `prediction` field is omitted. The checkpoint does not fabricate predictions to fill the slot.
- Default model: `claude-sonnet-4-6` (synthesis-coherence judgment is harder than entity-resolution sanity-check; warrants the larger model).
- Behavior:
  - `pass` → continue to discipline (disclosure filter); if `prediction` populated, attach to the audit telemetry payload as `payload.prediction = {...}`. Phase 4's audit consumer picks it up and routes it to `prediction_ledger.writer`.
  - `warn` → continue but log; prediction still attached if present
  - `halt` → empty-shell or contradiction case; short-circuit to validator-failure view
- Feature flags `CHECKPOINT_8_5_ENABLED` (default `false`), `CHECKPOINT_8_5_FAIL_HARD` (default `false`), `CHECKPOINT_8_5_PREDICTION_EXTRACT` (default `false` — gates only the prediction extraction half so 8.5 can run for coherence-checking before the prediction logging is enabled).
- 12+ tests: pass/warn/halt; prediction extracted from time-indexed synthesis; no-prediction case; malformed prediction → falls back to no-prediction with warning; sub-flag interactions; latency budget verified (<2500ms p95 against Sonnet 4.6).

### Stream D — Orchestrator wiring + integration tests

- Extend `platform/src/lib/synthesis/orchestrator.ts` with three additive hook points: post-resolve (4.5), post-retrieve (5.5), post-synthesize (8.5). Each hook is a no-op when its flag is off. The orchestrator's existing path remains unchanged in flag-off configurations.
- The orchestrator emits the checkpoint results as nested optional fields on the existing audit event payload (under `payload.checkpoints = {c4_5?: ..., c5_5?: ..., c8_5?: ...}`). Phase 4's audit consumer (v1 schema) stores the entire payload as JSONB and ignores the new fields gracefully — no Phase 4 schema bump required.
- The structured `prediction` object from 8.5 attaches at `payload.prediction` so Phase 4's prediction-ledger writer (already conditional on `payload.prediction` presence) routes it correctly. Phase 6 thus replaces Phase 4's heuristic prediction extractor — but only when `CHECKPOINT_8_5_PREDICTION_EXTRACT=true`. When off, Phase 4's heuristic extractor remains in effect.
- Add `npm run checkpoint:eval` script. Runs all three checkpoints against a small offline corpus (10 hand-labeled examples per checkpoint with expected verdicts). Reports per-checkpoint accuracy. Used as a regression gate.
- 8+ tests at the orchestrator level: flag-OFF → orchestrator path is byte-identical to Phase 3 baseline; flag-ON each → checkpoint hook called once; halt-on-4.5 short-circuits 5.5 and synthesis; halt-on-5.5 short-circuits synthesis; halt-on-8.5 short-circuits disclosure tier filter; multi-checkpoint warn → all logged; prediction-flag interaction.

## Critical constraints

- **Audit event compatibility.** Phase 6 emits via the existing v1 audit event schema. Checkpoint results live in optional nested fields. Phase 4's v1 consumer stores them as opaque JSONB. No coordination with Phase 4 required to ship in parallel.
- **All flags default OFF.** Phase 6 ships dark exactly like Phase 3. The native flips checkpoints on individually after observing logs in warn-mode for some duration.
- **Flag-OFF behavior is byte-identical.** When all three `CHECKPOINT_X_Y_ENABLED` flags are false, the orchestrator's path is the Phase 3 baseline. Regression suite proves this.
- **Latency budgets are real.** Each checkpoint adds inline latency to the response. Budget targets: 4.5 ≤800ms p95, 5.5 ≤1200ms p95, 8.5 ≤2500ms p95. Combined ≤4500ms p95 (acceptable for synthesis-grade queries; not all classes will run all three).
- **No fabricated predictions.** Checkpoint 8.5 must not invent a prediction to fill the optional field. If the synthesis is non-time-indexed, the field is omitted. Test this explicitly with a non-predictive query class.
- **Halt-state UX**. The halt structured failure must conform to the same shape Phase 5's `<ValidatorFailureView />` renders for P1/P2/P5 failures. Same shape = same renderer; checkpoint halts surface as just another failure type to the UI.
- **Sacrosanct held-out rule (extends from CLAUDE.md §E to Phase 6).** When the prediction object reaches `prediction_ledger.writer` (via Phase 4), it carries no `outcome` field. Phase 4's writer rejects with-outcome inserts. Phase 6 obeys this by never emitting `outcome` in its prediction schema.

## Done criteria

1. Stream A: checkpoint 4.5 module + prompt + tests pass; offline eval ≥80% accuracy on 10-example labeled set.
2. Stream B: checkpoint 5.5 module + prompt + tests pass; offline eval ≥80% accuracy.
3. Stream C: checkpoint 8.5 module + prompt + structured-prediction extraction + tests pass; offline eval ≥80% on coherence + ≥75% on prediction-extraction.
4. Stream D: orchestrator wiring; `checkpoint:eval` script reports accuracy; flag-OFF regression suite passes byte-identical.
5. Live LLM smoke: with each flag set ON in dev, run all 8 query classes through; visually inspect telemetry payloads. Verify checkpoint results land in `payload.checkpoints.*` and (where applicable) `payload.prediction`.
6. Latency: per-checkpoint p95 within budgets above on a 50-query sample.
7. Phase 4 compatibility: with both Phase 4 (when shipped) and Phase 6 enabled, audit_log rows render the checkpoint payload as JSONB in the existing column; prediction_ledger receives the structured prediction object correctly.
8. `lint` + `type-check` clean.
9. `must_not_touch` verified by directory diff.
10. All flags stay OFF after Phase 6 acceptance — flag flips are separate native operational decisions, ideally done one checkpoint at a time with warn-mode observation periods between.
11. Native acceptance.

## Risk classification: MEDIUM

Phase 6 extends an active code path (synthesis orchestrator) and adds inline LLM calls that affect latency and cost. Mitigations:
- Per-checkpoint flags + warn/halt sub-flags allow extremely fine-grained rollout
- Flag-OFF path is byte-identical to Phase 3 baseline (regression-proof)
- Audit event payload is backward-compatible with Phase 4's v1 schema (no cross-phase coordination required)
- Latency budgets enforced by tests
- Offline accuracy gates prevent shipping checkpoints that don't actually catch failures
- Halt-state UX reuses Phase 5's existing failure renderer (no new UI work)

## Forward implications

- **Phase 7 (Panel Mode)** — checkpoints will run on the adjudicator's output (not on each panel member's individual output). Phase 7 will reuse Phase 6's checkpoint module by injecting a panel-aware prompt variant.
- **Phase 8 (Audit View UI)** — will surface checkpoint verdicts as a sub-section of each audit row, alongside structural validators.
- **Phase 10 (Calibration Loop)** — will use the structured prediction objects flowing through `prediction_ledger`, which Phase 6 generates with much higher quality than Phase 4's heuristic extractor.
- **Eventual schema bump.** When Phase 4 evolves to v2 (richer audit shape), the checkpoint payload location may move from `payload.checkpoints` to first-class columns. That's a Phase 4-led change; Phase 6's writer code already isolates the emission shape via a single helper, so the migration is one-file.

## How native triggers

Open a Claude Code session in Anti-Gravity (Sonnet 4.6 in VS Code extension). Paste:

> Read EXEC_BRIEF_PHASE_6_v1_0.md and execute it.

This brief is disjoint from Phase 4 (DB), Phase 5 (UI), and the Phase 9 hotfix (retrieve). Four concurrent Claude Code sessions safe.

## Status updates

- AUTHORED 2026-04-27
- IN_PROGRESS_ALL_STREAMS — 2026-04-28 (Sonnet 4.6, Claude Code / Anti-Gravity)
- COMPLETE — set when all 11 done-criteria pass and native accepts
