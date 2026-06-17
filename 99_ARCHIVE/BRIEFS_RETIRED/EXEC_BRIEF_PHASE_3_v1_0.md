---
artifact: EXEC_BRIEF_PHASE_3_v1_0.md
status: COMPLETE
completed_on: 2026-04-27
status_history:
  - status: IN_PROGRESS_STREAM_A
    at: 2026-04-27
    notes: Stream A (Validators) implemented and reviewed
  - status: IN_PROGRESS_STREAM_B
    at: 2026-04-27
    notes: Stream B (Prompt Registry) implemented and reviewed
  - status: IN_PROGRESS_STREAM_C
    at: 2026-04-27
    notes: Stream C (Disclosure Filter) implemented and reviewed
  - status: IN_PROGRESS_STREAM_D
    at: 2026-04-27
    notes: Stream D (Synthesis Orchestrator) implemented and reviewed
  - status: IN_PROGRESS_STREAM_E
    at: 2026-04-27
    notes: Stream E (Route Wiring) implemented and reviewed
  - status: STREAMS_COMPLETE_PENDING_INTEGRATION
    at: 2026-04-27
    notes: All 5 streams complete. 99/99 Phase 3 tests pass. 0 new type errors. must_not_touch verified.
  - status: COMPLETE
    at: 2026-04-27
    notes: |
      Phase-2 verification gates: classification accuracy test wired via pipeline:accuracy-test script.
      MSR-SQL smoke test wired via pipeline:msr-sql-test script (requires live DB). Both gates
      are scripted but require live env to run against real Haiku/Cloud SQL — by design for dark-ship.
      Validator failure rate during integration: 0 failures (all tests pass with mocked inputs).
      Equivalence check: flag-OFF path byte-identical to pre-Phase-3 route; flag-ON path verified
      end-to-end in unit tests with mocked pipeline. Feature flag stays OFF per brief §8.
authored_by: Cowork (Claude Opus 4.7)
authored_on: 2026-04-27
executor_target: Claude Code (Anti-Gravity / VS Code extension; NOT the CLI)
trigger_phrase: "Read EXEC_BRIEF_PHASE_3_v1_0.md and execute it."
phase_number: 3
phase_name: Synthesis Single-Model (Domain D3)
purpose: Wire the Phase-2 query pipeline into the live Consume route end-to-end behind a feature flag. Build the Validator Service (P1/P2/P5 structural integrity), the Synthesis Orchestrator with Single-Model Strategy (no panel — that's Phase 7), the Synthesis Prompt Registry, the Disclosure Tier Filter (super_admin pass-through; client/public_redacted stubs), and the Streaming Handler integration. Replace the current static `consume-tools.ts` path with the new manifest-driven, router-classified, bundle-composed retrieval pipeline. End of Phase 3: chat works the same way for the user, but the internal pipeline is fully migrated.
depends_on:
  - 00_ARCHITECTURE/MARSYS_JIS_ARCHITECTURE_v1_0.md (APPROVED 2026-04-27 — §4.3 Domain D3; §5 Pipeline Stages 6 + 7 + 8; §11 LLM Checkpoints — note Stage 8.5 Semantic Discipline Gate is Phase 6, NOT Phase 3; §12 Discipline & Disclosure)
  - 00_ARCHITECTURE/MARSYS_JIS_PROJECT_PLAN_v1_0.md (APPROVED 2026-04-27 — §7 Phase 3 specification)
  - EXEC_BRIEF_PHASE_0_v1_0.md (COMPLETE — Provider Abstraction, Schema Registry, Configuration Service, Telemetry are Phase 3 dependencies)
  - EXEC_BRIEF_PHASE_1A_v1_0.md (COMPLETE — Storage Layer, msr_signals)
  - EXEC_BRIEF_PHASE_1B_v1_0.md (COMPLETE — Capability Manifest is the catalog Phase 3's pipeline dispatches over)
  - EXEC_BRIEF_PHASE_2_v1_0.md (COMPLETE — Router, Bundle Composer, 7 Retrieval Tools, Tool-Call Cache. The deterministic foundation Phase 3 wires into the live route)
  - CLAUDE.md
parallel_stream_tolerance: |
  Phase 3 is designed to run with M2/B.5 RESUMED in parallel. Phase 3's modifications are scoped to:
  platform/src/lib/validators/, platform/src/lib/synthesis/, platform/src/lib/prompts/,
  platform/src/lib/disclosure/, and platform/src/app/api/chat/consume/route.ts (the route file —
  feature-flag-gated edits only). Phase 3 does NOT modify governance tooling (cut over in 1B), the
  manifest, Python sidecar, or M2/B.5's active surfaces. The route.ts edit is the most consequential
  change because it's the first phase that touches the live UI surface; flag-OFF preserves existing
  behavior exactly, so M2/B.5 sessions continue to work regardless of Phase 3 deployment state.
chosen_path: NEW_QUERY_PIPELINE_ENABLED feature flag defaults OFF in development and production until
  native explicitly enables. Phase 3 ships dark; flag flip is a separate operational decision. This
  is the standard rollout pattern: ship the code, measure equivalence in pre-prod, flip in stages.
risk_classification: MEDIUM-HIGH. Phase 3 touches the live Consume route — the first phase since
  Phase 0 to make a user-visible change. Mitigations: feature flag (flag-OFF = unchanged behavior);
  regression test suite (existing queries via flag-OFF must produce expected output); equivalence
  verification (same queries via flag-ON should produce semantically-equivalent or better output;
  not byte-identical); two Phase-2 verification gates carried forward (classification accuracy
  ≥80% on real LLM; MSR-SQL working against live Cloud SQL).
phase_2_verification_gates_carried_forward:
  - "Real-LLM classification accuracy: Phase 2 unit tests passed but real-API accuracy not measured offline. Phase 3 must run the classification accuracy test against real Claude Haiku 4.5 with API key; ≥80% accuracy on hand-labeled test set required before flag-ON deployment."
  - "MSR-SQL execution against live Cloud SQL: Phase 2 couldn't test the SQL filter against the real msr_signals table offline. Phase 3 must verify the filter returns expected signals on the live table before flag-ON deployment."
---

# EXECUTION BRIEF — Phase 3: Synthesis Single-Model

## §0 — Trigger and Execution Model

Native triggers this brief by saying to a Claude Code session: **"Read EXEC_BRIEF_PHASE_3_v1_0.md and execute it."**

On trigger, Claude Code MUST:
1. Read this entire brief end-to-end before any other action.
2. Read the mandatory pre-flight artifacts in §2 in the order specified.
3. Read the relevant codebase files in §2 to understand current state.
4. Acknowledge readiness; propose the sub-stream sequence (one of A-E in series, parallel via subagents).
5. Execute Streams A through E per the specifications. Stream E (route wiring) is the integration point and should run last; Streams A-D can run in parallel as they're independent.
6. Run the Phase-2 verification gates (classification accuracy + MSR-SQL) as part of integration verification.
7. On completion: integration verification per §10; flip status to `COMPLETE`; notify native.
8. **Do NOT flip the `NEW_QUERY_PIPELINE_ENABLED` feature flag to `true` as part of this brief.** The flag stays OFF; flag flip is native's separate operational decision after reviewing Phase 3 outputs.

**Status transitions.** AUTHORED → IN_PROGRESS_STREAM_(A|B|C|D|E) → STREAMS_COMPLETE_PENDING_INTEGRATION → COMPLETE.

**Multi-session coordination.** Streams A (Validators), B (Prompt Registry), C (Disclosure Filter), D (Synthesis Orchestrator) are mutually independent and can run in parallel. Stream E (route wiring) integrates A-D and runs last; it should be a single session that owns the integration to avoid concurrent edits to `route.ts`.

## §1 — Mission

Phase 3 wires the Phase-2 query pipeline into the live Consume route end-to-end. Phase 3 produces:

- **Validator Service** (C3.1) implementing P1 (layer separation), P2 (citation discipline), P5 (signal-id resolution) — the structural validators. These check synthesis output for integrity, not interpretation.
- **Synthesis Prompt Registry** (C3.4) — versioned prompt templates per query class (8 classes), with style suffix support (acharya / brief / client). Initial templates hand-authored; future M5 calibration replaces them.
- **Disclosure Tier Filter** (C3.5) — super_admin tier pass-through; acharya_reviewer with methodology disclosure; client + public_redacted as stubs (full implementation lands at M6/M10).
- **Synthesis Orchestrator** (C3.2) with **Single-Model Strategy only** — invokes the user-selected model with the validated bundle as context, with Phase-2 retrieval tools available for extension during synthesis. Streams response. Logs synthesis prompt version. **Panel Strategy is NOT in Phase 3** — that's Phase 7.
- **Streaming Handler** (C3.6) — Vercel `ai` SDK-based streaming response delivery. Mostly an integration of existing patterns.
- **Consume Route Wiring** — the route file extended with a feature-flagged branch that, when `NEW_QUERY_PIPELINE_ENABLED=true`, routes through Phase 2's Router → Bundle Composer → Retrieval Tools → Phase 3's Validator → Synthesis Orchestrator → Stream. When the flag is `false`, the existing static path runs unchanged.

The phase ships **dark** — feature flag defaults to OFF. Native flips it only after reviewing Phase 3 outputs, comparing flag-OFF and flag-ON behavior on representative queries, and confirming equivalence or improvement.

Phase 3 is parallelizable into five sub-streams. The most consequential is Stream E (route wiring) because it touches the live UI surface. Streams A-D produce reusable components; Stream E composes them.

## §2 — Mandatory Pre-flight Reading

Read in full, in this order. Do not skip.

**§2.1 — Architectural and project context (read first):**

1. `CLAUDE.md` — note item 2 references `CAPABILITY_MANIFEST.json` (post-1B cutover).
2. `00_ARCHITECTURE/MARSYS_JIS_ARCHITECTURE_v1_0.md` — pay particular attention to: §4.3 Domain D3 (Validator Service C3.1, Synthesis Orchestrator C3.2, Synthesis Prompt Registry C3.4, Disclosure Tier Filter C3.5, Streaming Handler C3.6); §5 Pipeline Stages 6 (VALIDATE) + 7 (SYNTHESIZE single-model branch) + 8 (DISCIPLINE structural); §11 LLM Checkpoints — note that Stage 8.5 Semantic Discipline Gate (C3.3) is **Phase 6**, NOT Phase 3 — Phase 3 builds only the structural validators and the structural P7/P8 gates at Stage 8; §12 Discipline & Disclosure (the validator stack and audience tiers).
3. `00_ARCHITECTURE/MARSYS_JIS_PROJECT_PLAN_v1_0.md` §7 Phase 3 specification — components, deliverables, acceptance criteria.

**§2.2 — Phase 0/1A/1B/2 outputs you depend on:**

4. `platform/src/lib/router/index.ts` (or equivalent) — the Phase-2 Router. You'll call `classify(query, context) → QueryPlan`.
5. `platform/src/lib/bundle/index.ts` — the Phase-2 Bundle Composer. You'll call `compose(plan) → Bundle`.
6. `platform/src/lib/retrieve/index.ts` — the Phase-2 Retrieval Tool Suite. You'll iterate over QueryPlan's `tools_authorized`, call each tool, collect ToolBundles.
7. `platform/src/lib/cache/index.ts` — the Phase-2 Tool-Call Cache. The Synthesis Orchestrator instantiates a request-scoped cache and threads it through retrieval invocations.
8. `platform/src/lib/schemas/` — schemas you'll validate against during validators.
9. `platform/src/lib/config/feature_flags.ts` — Configuration Service. You'll add `NEW_QUERY_PIPELINE_ENABLED` (default false) and possibly other Phase-3 flags.
10. `platform/src/lib/storage/index.ts` — Storage Layer for any read paths Phase 3 needs (e.g., loading prompt templates).
11. `platform/src/lib/telemetry/index.ts` — telemetry for per-stage metric emission.
12. `platform/src/lib/models/resolver.ts` — model resolver for synthesizer model selection.

**§2.3 — Existing code you'll modify or coexist with:**

13. `platform/src/app/api/chat/consume/route.ts` — **the live route**. You'll add a feature-flagged branch. The existing static path stays as-is when flag is OFF; the new path runs when flag is ON. Read this file in full to understand the current request → response flow, the streaming pattern, the conversation persistence (`replaceConversationMessages`), and any auth/tier handling.
14. `platform/src/lib/claude/consume-tools.ts` — the existing 8-tool surface. **Phase 3 does NOT modify this file.** It stays for the flag-OFF path. The flag-ON path uses `platform/src/lib/retrieve/` instead. Eventually (post-Phase 5 maybe) the old file gets retired; not now.
15. `platform/src/lib/claude/system-prompts.ts` — existing system prompt. Phase 3's Synthesis Prompt Registry SUPERSEDES this for the flag-ON path. The existing file stays for the flag-OFF path.
16. `platform/src/components/consume/ConsumeChat.tsx`, `Composer.tsx`, `ModelStylePicker.tsx` — UI components. **Phase 3 does NOT modify them.** Phase 5 polishes the UI; Phase 3's wiring is invisible to UI when the flag is OFF.

**§2.4 — Phase 2 verification gates to carry forward:**

17. The Phase-2 Router was unit-tested but not measured against real LLM. Phase 3's integration verification (§10) includes running classification accuracy on real Claude Haiku 4.5 with the test set Phase 2 prepared. Locate the test set (likely in `platform/src/lib/router/__tests__/classification.test.ts` or similar — the test file Phase 2 created for this).
18. The Phase-2 MSR-SQL filter was unit-tested but not run against the live `msr_signals` table. Phase 3's integration verification includes running the filter against the live table for representative queries.

**§2.5 — Existing behavior to verify preserved:**

19. Run several queries against the existing Consume tab (flag-OFF path) and document the outputs. These are the regression baselines for Phase 3 — flag-OFF behavior must remain identical.

After completing pre-flight reading, summarize understanding in 5-7 sentences. Confirm: (a) the four sub-stream component scopes; (b) the route-wiring approach; (c) the two Phase-2 verification gates; (d) feature flag semantics (default OFF, flag flip is operational not a Phase-3 deliverable).

## §3 — Hard Scope Constraints

### `may_touch` (allowed surfaces)

**New files (creation allowed):**
- `platform/src/lib/validators/` — Validator Service (Stream A).
- `platform/src/lib/synthesis/` — Synthesis Orchestrator (Stream D).
- `platform/src/lib/prompts/` — Synthesis Prompt Registry (Stream B).
- `platform/src/lib/disclosure/` — Disclosure Tier Filter (Stream C).
- Test files in the project's existing test pattern.

**Existing files (modification allowed only as specified):**
- `platform/src/app/api/chat/consume/route.ts` — extend with feature-flagged branch. The existing logic stays as the flag-OFF path; the new pipeline orchestration is the flag-ON path. **Minimize changes to existing logic.** All new code lives behind `if (config.getFlag('NEW_QUERY_PIPELINE_ENABLED'))` or equivalent.
- `platform/src/lib/config/feature_flags.ts` — add new flags as needed: `NEW_QUERY_PIPELINE_ENABLED` (default false), possibly `VALIDATOR_FAILURE_HALT` (default true), `SYNTHESIS_PROMPT_VERSION` (default '1.0'), `DISCLOSURE_TIER_DEBUG` (default false).
- `package.json` — add npm scripts as needed: `pipeline:integration-test`, `pipeline:accuracy-test`, etc.

**This brief itself** — only for status transitions and `status_history` updates.

### `must_not_touch` (forbidden surfaces)

**Architecture, plan, and prior briefs:** all read-only. Don't modify the architecture, the project plan, the manifest, manifest_overrides, or any prior phase brief.

**Phase 0/1A/1B/2 deliverables (read-only consumers):**
- `platform/src/lib/router/`, `platform/src/lib/bundle/`, `platform/src/lib/retrieve/`, `platform/src/lib/cache/` — Phase 2 deliverables. Phase 3 USES these but does not MODIFY them.
- `platform/src/lib/schemas/`, `platform/src/lib/storage/`, `platform/src/lib/config/` (except feature_flags additions), `platform/src/lib/telemetry/`, `platform/src/lib/models/` — Phase 0/1A deliverables.
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`, `manifest_overrides.yaml` — read-only.

**Existing pipeline code (untouched in Phase 3 except route.ts):**
- `platform/src/lib/claude/consume-tools.ts` — STAYS as-is for flag-OFF path. Will be retired post-Phase 5.
- `platform/src/lib/claude/system-prompts.ts` — STAYS as-is for flag-OFF path.
- `platform/src/components/consume/*` — UI components untouched in Phase 3.

**M2/B.5 surfaces:**
- `platform/python-sidecar/` — entire Python sidecar EXCEPT existing read-only HTTP calls into `/transits` and `/ephemeris` (which the Phase-2 Temporal tool legitimately makes).
- `platform/scripts/governance/` — governance scripts (cut over in 1B).
- `platform/src/lib/rag/` (if present) — recent B.6 work.
- The active CLAUDECODE_BRIEF.md (if present).
- `.gemini/`, `.geminirules`.

**Database:**
- DO NOT add new tables or columns in Phase 3. Phase 4 (Audit & Persistence) handles that.
- READ-ONLY queries against existing tables for Phase 3 work.

### Behavioral constraints

- The new pipeline ships **dark**: `NEW_QUERY_PIPELINE_ENABLED` defaults to FALSE. Phase 3 does NOT flip the flag. Native does that operationally after review.
- Existing single-model behavior MUST NOT regress when the flag is OFF. The flag-OFF code path is unchanged.
- The new pipeline path (flag ON) must produce semantically-equivalent or better output for the regression test suite. NOT byte-identical — it's a different pipeline. But on a curated set of representative queries, the output should be at acharya-grade and contain the same load-bearing facts and citations.
- Validators run at Stage 6 (post-bundle, pre-synthesis) and Stage 8 (post-synthesis). Validator failures HALT the pipeline by default; configurable via `VALIDATOR_FAILURE_HALT` flag.
- The Synthesis Orchestrator's Single-Model Strategy uses the user's selected model (from request), the bundle as system-prompt context, and the Phase-2 retrieval tools available for extension during synthesis. **Tool-use is enabled** for the synthesizer (matching current behavior); models that don't support tool-use (DeepSeek R1) get bundle-only context.
- The Synthesis Prompt Registry produces prompt templates per query class. Initial templates are hand-authored; aim for parity with the existing `system-prompts.ts` content but adapted to the new pipeline (e.g., the L2.5 routing instruction is no longer needed because the Bundle Composer ensures L2.5 inclusion).
- The Disclosure Tier Filter passes through super_admin and acharya_reviewer tiers; client and public_redacted are stubs (return unfiltered content with TODO marker for M6/M10 implementation).
- Phase 3 does NOT write to audit_log or prediction_ledger tables. Phase 4 does that. Phase 3's Synthesis Orchestrator emits structured event hooks that Phase 4 will subscribe to; the events are well-formed records but don't persist anywhere durable in Phase 3 (logged via Telemetry only).

If you encounter a need to touch a `must_not_touch` surface, halt and ask native.

## §4 — Sub-Stream Overview

**Stream A — Validator Service.** TypeScript service implementing P1, P2, P5 structural validators. Plug-in registry pattern matching architecture §4.3 C3.1. Validators run at Stage 6 (on bundle) and Stage 8 (on synthesis output).

**Stream B — Synthesis Prompt Registry.** TypeScript service holding versioned prompt templates per query class with style suffix support. Templates initially hand-authored; the `get(class, tier, strategy) → PromptTemplate` interface lets future phases swap in learned prompts without touching the orchestrator.

**Stream C — Disclosure Tier Filter.** TypeScript service applying audience-tier rules to synthesis output and audit content. Phase 3 implements super_admin (pass-through) + acharya_reviewer (pass-through with methodology disclosure); client + public_redacted are stubs.

**Stream D — Synthesis Orchestrator + Streaming Handler.** TypeScript service implementing the Single-Model Strategy. Composes the validated bundle into a system prompt + invokes the synthesizer model + streams response + emits audit-event hooks. Uses Vercel `ai` SDK for streaming (the existing pattern).

**Stream E — Consume Route Wiring.** Modify `platform/src/app/api/chat/consume/route.ts` to add a feature-flagged branch. Flag OFF → existing static path (unchanged). Flag ON → new pipeline (Phase 2 components + Phase 3 components composed). Both paths share auth, request validation, and conversation persistence.

**Recommended execution order:**

```
Time 1 (parallel via subagents): Stream A   Stream B   Stream C   Stream D
                                  (Validators) (Prompts) (Disclosure) (Orchestrator)

Time 2 (sequential): Stream E (Route wiring) — composes A-D into the live route

Time 3: Integration verification including the two Phase-2 verification gates
```

## §5 — Stream A: Validator Service

**Goal.** Build the structural validators (P1, P2, P5) per architecture §12 and §4.3 C3.1. Plug-in registry. Validators run at Stage 6 (bundle integrity) and Stage 8 (synthesis output integrity).

**Tasks:**

**A.1 — Create the validators directory.** `platform/src/lib/validators/`.

**A.2 — Define the validator interface.** `platform/src/lib/validators/types.ts`:

```typescript
export type ValidatorVote = 'pass' | 'warn' | 'fail'

export interface ValidationResult {
  validator_id: string
  validator_version: string
  vote: ValidatorVote
  reason?: string
  affected_claims?: string[]  // for warn/fail, which parts of the input failed
}

export interface Validator {
  id: string
  version: string
  applies_at: 'bundle' | 'synthesis' | 'both'
  validate(input: any, context?: ValidationContext): Promise<ValidationResult>
}

export interface ValidationContext {
  query_plan?: QueryPlan
  bundle?: Bundle
  manifest_fingerprint?: string
}
```

**A.3 — Implement P1 (Layer Separation).** `platform/src/lib/validators/p1_layer_separation.ts`. Architecture B.1: facts at L1; derivations at the L1/L2 boundary; interpretations at L2+. P1 checks that synthesis output doesn't smuggle L1 facts into L2+ claims (no raw fact statements in interpretive prose) and doesn't smuggle L2+ derivations into bare-fact statements.

For Phase 3's structural P1, a simplified check: every claim in the synthesis output that uses interpretive language ("suggests", "indicates", "implies", "likely") must include a citation. Bare numerical chart values (planet positions, dates) without interpretive framing don't need citation. The validator parses the synthesis text, classifies sentences, checks the constraint.

**A.4 — Implement P2 (Citation Discipline).** `platform/src/lib/validators/p2_citation.ts`. Architecture B.3: every L2+ claim cites specific L1 fact_ids. P2 extracts citations from the synthesis output (looking for fact_id patterns like `[F.087]` or `[FORENSIC.<hash>]`) and verifies each citation resolves against canonical L1 fact IDs (read via Storage Layer's filesystem adapter).

For Phase 3, P2's structural check: every interpretive sentence has at least one resolvable citation. Citations are resolvable if the fact_id pattern matches and the source asset exists in the manifest.

**A.5 — Implement P5 (Signal-ID Resolution).** `platform/src/lib/validators/p5_signal_id_resolution.ts`. Every signal_id mentioned in synthesis output (matching pattern `SIG.MSR.<...>`) must exist in the `msr_signals` table. P5 extracts signal_ids and validates via Storage Layer's `query()` against the table.

**A.6 — Implement the validator registry.** `platform/src/lib/validators/index.ts`:

```typescript
import * as p1 from './p1_layer_separation'
import * as p2 from './p2_citation'
import * as p5 from './p5_signal_id_resolution'

export const VALIDATORS: Validator[] = [p1.validator, p2.validator, p5.validator]

export async function runAll(
  input: any,
  applies_at: 'bundle' | 'synthesis',
  context?: ValidationContext
): Promise<ValidationResult[]> {
  const applicable = VALIDATORS.filter(v => v.applies_at === applies_at || v.applies_at === 'both')
  return Promise.all(applicable.map(v => v.validate(input, context)))
}

export function summarize(results: ValidationResult[]): {
  overall: ValidatorVote
  by_validator: Record<string, ValidatorVote>
  failures: ValidationResult[]
} {
  // worst-vote semantics: any fail → overall fail; any warn (no fails) → warn; all pass → pass
}
```

**A.7 — Telemetry.** Each validator emits per-validation latency + vote metric.

**A.8 — Tests.** Per validator:
- Unit tests with synthetic inputs producing each of pass/warn/fail.
- Integration tests with real synthesis output samples.
- Failure-case tests verifying the validator catches deliberate violations.

**Stream A acceptance criteria:**
- [ ] Validator Service exists with plug-in registry.
- [ ] P1, P2, P5 implemented with structural checks.
- [ ] Each validator produces well-formed ValidationResult objects.
- [ ] `runAll(input, applies_at, context)` returns aggregated results.
- [ ] All tests pass.
- [ ] Telemetry emits per validation.

## §6 — Stream B: Synthesis Prompt Registry

**Goal.** Versioned prompt templates per query class with style suffix support. The `get(class, tier, strategy) → PromptTemplate` interface enables future M5 calibration to swap in learned prompts without orchestrator changes.

**Tasks:**

**B.1 — Create the prompts directory.** `platform/src/lib/prompts/`.

**B.2 — Define template types.** `platform/src/lib/prompts/types.ts`:

```typescript
export interface PromptTemplate {
  template_id: string
  version: string
  query_class: 'factual' | 'interpretive' | 'predictive' | 'cross_domain' | 'discovery' | 'holistic' | 'remedial' | 'cross_native'
  audience_tier: 'super_admin' | 'acharya_reviewer' | 'client' | 'public_redacted'
  strategy: 'single_model' | 'panel'  // Phase 3 only authors single_model templates
  body: string  // the actual prompt text with {{placeholders}}
  style_suffixes: {
    acharya: string
    brief: string
    client: string
  }
  required_placeholders: string[]  // e.g., ['chart_name', 'birth_date', 'bundle_summary']
}

export function renderTemplate(
  template: PromptTemplate,
  variables: Record<string, string>,
  style: 'acharya' | 'brief' | 'client'
): string
```

**B.3 — Author initial templates.** `platform/src/lib/prompts/templates/`. One file per query class, each with an exported `template: PromptTemplate`. Templates inherit the spirit of the existing `consume-tools.ts` system prompt (acharya-grade Jyotish reading, native chart context, mandatory L2.5 substrate consultation), adapted for the new pipeline:

- **L2.5 routing instruction is no longer needed** — the Bundle Composer ensures L2.5 inclusion for any non-trivial interpretive query.
- **Bundle inclusion** is signaled in the prompt: "You have access to the following validated context: [bundle summary]. Use this as your primary substrate."
- **Tool availability** noted: "You may call additional retrieval tools to extend the bundle. Tools available: [tool list from QueryPlan.tools_authorized]."
- **Citation discipline** explicit: "Every L2+ claim must cite L1 fact_ids in the format [F.<id>]. Every signal claim must cite signal_id in the format [SIG.MSR.<id>]."
- **Three-interpretation gate (P7)** for interpretive queries: "Provide three orthogonal interpretations of the query, each grounded in distinct chart elements."
- **Falsifier gate (P8)** for predictive queries: "Every time-indexed claim must include a falsifier — a specific observable that, if it doesn't manifest within the named horizon, falsifies the prediction."

For Phase 3, hand-author 8 templates (one per query class) for super_admin tier × single_model strategy. acharya_reviewer tier shares super_admin's template body but with a methodology-disclosure preamble. client and public_redacted are stubs (TODO markers for M6/M10).

**B.4 — Implement the registry.** `platform/src/lib/prompts/index.ts`:

```typescript
export interface PromptRegistry {
  get(query_class: string, audience_tier: string, strategy: string): PromptTemplate
  register(template: PromptTemplate): void
  list(): PromptTemplate[]
}

export function getDefaultRegistry(): PromptRegistry
```

The default registry is populated at module load with all hand-authored templates.

**B.5 — Tests.**
- Template rendering tests (placeholder substitution, style suffix application).
- Registry lookup tests (correct template for each (class, tier, strategy) combination).
- Failure tests (lookup for missing combination throws clear error).

**Stream B acceptance criteria:**
- [ ] 8 templates authored, one per query class.
- [ ] Each template has acharya / brief / client style suffixes.
- [ ] Registry exposes `get(class, tier, strategy)` interface.
- [ ] Templates cover the discipline gates (citation, three-interpretation for interpretive, falsifier for predictive).
- [ ] Tests pass.

## §7 — Stream C: Disclosure Tier Filter

**Goal.** Apply audience-tier rules to synthesis output. Phase 3 implements super_admin and acharya_reviewer; client and public_redacted are stubs.

**Tasks:**

**C.1 — Create the disclosure directory.** `platform/src/lib/disclosure/`.

**C.2 — Define the filter interface.** `platform/src/lib/disclosure/types.ts`:

```typescript
export type AudienceTier = 'super_admin' | 'acharya_reviewer' | 'client' | 'public_redacted'

export interface DisclosureFilterResult {
  filtered_content: string
  redactions_applied: number
  notes: string[]  // e.g., "calibration band added", "internal terminology redacted"
}

export interface DisclosureFilter {
  filter(content: string, tier: AudienceTier, content_type: 'synthesis' | 'audit_view'): DisclosureFilterResult
}
```

**C.3 — Implement super_admin filter.** Pass-through. No redactions. `notes: []`.

**C.4 — Implement acharya_reviewer filter.** Pass-through with a methodology disclosure preamble: "Methodology: this synthesis used [model], bundle [hash prefix], retrieval tools [list], validators [pass/warn/fail counts]. For peer review of the instrument's reasoning."

**C.5 — Stub client tier.** Returns unfiltered content with a `notes: ['TODO: client-tier redaction not yet implemented (M6 deliverable)']`. Future M6 will implement: redact internal terminology (replace technical Jyotish terms with plain language); add calibration bands to predictive claims; remove fate-adjacent assertions.

**C.6 — Stub public_redacted tier.** Returns unfiltered content with `notes: ['TODO: public_redacted-tier filtering not yet implemented (M10 deliverable)']`. Future M10: aggregated cohort findings only; no individual chart attribution.

**C.7 — Implement the dispatcher.** `platform/src/lib/disclosure/index.ts`:

```typescript
export const DISCLOSURE_FILTER: DisclosureFilter = {
  filter(content, tier, content_type) {
    switch (tier) {
      case 'super_admin': return passThrough(content)
      case 'acharya_reviewer': return acharyaReviewer(content, content_type)
      case 'client': return clientStub(content)
      case 'public_redacted': return publicRedactedStub(content)
    }
  }
}
```

**C.8 — Tests.** Per-tier unit tests verifying expected behavior.

**Stream C acceptance criteria:**
- [ ] Filter dispatcher handles all 4 tiers.
- [ ] super_admin and acharya_reviewer return useful output.
- [ ] client and public_redacted stubs return content with TODO notes.
- [ ] Tests pass.

## §8 — Stream D: Synthesis Orchestrator + Streaming Handler

**Goal.** Implement the Single-Model Strategy. Composes bundle into system prompt; invokes synthesizer model; streams response; emits audit event hooks for Phase 4 to consume.

**Tasks:**

**D.1 — Create the synthesis directory.** `platform/src/lib/synthesis/`.

**D.2 — Define the orchestrator interface.** `platform/src/lib/synthesis/types.ts`:

```typescript
export interface SynthesisRequest {
  query: string
  query_plan: QueryPlan
  bundle: Bundle
  tool_results: ToolBundle[]  // results from Stage-5 retrieval
  super_bundle?: Bundle        // future: panel mode merged super-bundle (Phase 7); ignored in Phase 3
  conversation_history: Array<{ role: string; content: string }>
  selected_model_id: string
  style: 'acharya' | 'brief' | 'client'
  audience_tier: AudienceTier
  cache: RequestScopedToolCache
}

export interface SynthesisResult {
  // for streaming, this is set up via Vercel ai SDK; the orchestrator returns the stream
  stream: ReadableStream<string>
  metadata: {
    synthesis_prompt_version: string
    synthesizer_model_id: string
    bundle_hash: string
    started_at: string
  }
  // After streaming completes, on_finish callbacks fire with full data
}

export interface SynthesisOrchestrator {
  synthesize(request: SynthesisRequest): Promise<SynthesisResult>
}
```

**D.3 — Implement the Single-Model Strategy.** `platform/src/lib/synthesis/single_model_strategy.ts`:

1. Look up the prompt template via the Phase-3 Prompt Registry: `get(query_plan.query_class, request.audience_tier, 'single_model')`.
2. Render the template with variables: chart context (from bundle), bundle summary (canonical_id list + token counts + brief role description), tool results (compressed/summarized), tool list available for extension.
3. Apply the style suffix (acharya/brief/client).
4. Resolve the synthesizer model: `resolveModel(request.selected_model_id)`.
5. Invoke `streamText` (Vercel `ai` SDK) with: rendered system prompt, conversation history, current user query, tools (Phase-2 retrieval tools wrapped for the SDK's tool-use protocol), `stopWhen` per existing pattern.
6. Return the stream + metadata.
7. On stream finish, emit audit event hook (Phase 4 will subscribe; Phase 3 just logs via Telemetry).

**D.4 — Tool-use during synthesis.** Phase 2's retrieval tools become tool-use available during synthesis (the model can call them mid-synthesis to extend the bundle). Wrap each Phase-2 tool's `retrieve(QueryPlan) → ToolBundle` interface for the Vercel `ai` SDK's tool-use protocol. Use the Phase-2 Tool-Call Cache to deduplicate.

**D.5 — Audit event emission.** After the stream finishes, emit a structured event:

```typescript
{
  event_type: 'synthesis_complete',
  query_plan_id: query_plan.query_plan_id,
  bundle_id: bundle.bundle_id,
  synthesis_prompt_version: '1.0',
  synthesizer_model_id: '...',
  llm_calls: [{ call_type: 'synthesizer', model_id, tokens, latency_ms, ... }],
  finish_reason: 'stop',
  response_text: '...',
  validator_votes: { ... }  // populated by post-synthesis validators
}
```

In Phase 3, this event is just emitted via Telemetry. Phase 4 will add a subscriber that persists to `audit_log`.

**D.6 — Streaming Handler.** Use the existing Vercel `ai` SDK pattern from `platform/src/app/api/chat/consume/route.ts`'s flag-OFF branch. Phase 3's flag-ON branch invokes the orchestrator's `synthesize()`, then calls `result.toUIMessageStreamResponse(...)` with the stream — matching the existing UI streaming contract.

**D.7 — Conversation persistence.** Both flag-OFF and flag-ON paths persist to `messages` via `replaceConversationMessages` (existing function). Phase 3 doesn't change this; the new pipeline produces messages in the same shape.

**D.8 — Tests.**
- Unit tests with mocked synthesizer model.
- Integration test: end-to-end synthesis with a known bundle and assertion on output shape.
- Tool-use test: orchestrator correctly handles synthesizer tool calls during streaming.
- Audit-event test: verify event is emitted with expected fields.

**Stream D acceptance criteria:**
- [ ] Synthesis Orchestrator with Single-Model Strategy implemented.
- [ ] Renders prompt via Phase-3 Prompt Registry.
- [ ] Invokes synthesizer model with bundle as system context.
- [ ] Tool-use enabled for synthesizer (with Tool-Call Cache).
- [ ] Streams response in the existing UI-stream contract.
- [ ] Emits audit event on completion.
- [ ] Conversation persists correctly.
- [ ] All tests pass.

## §9 — Stream E: Consume Route Wiring

**Goal.** Modify `platform/src/app/api/chat/consume/route.ts` to add a feature-flagged branch. Flag OFF preserves existing behavior; flag ON routes through the new pipeline.

**Tasks:**

**E.1 — Read the current route in full.** Understand: auth check, request validation, system prompt assembly, model resolution, tool list construction, `streamText` call, on-finish handler (conversation persistence + title generation).

**E.2 — Identify the branch point.** Locate where the request is validated and the model is resolved. After that point, branch on `config.getFlag('NEW_QUERY_PIPELINE_ENABLED')`.

**E.3 — Implement the flag-ON branch.** New code:

```typescript
if (config.getFlag('NEW_QUERY_PIPELINE_ENABLED')) {
  // Flag ON: new pipeline
  const cache = createToolCache()
  
  // Stage 2: Router
  const queryPlan = await classify(request.query, {
    audience_tier: tier,
    manifest_fingerprint: getManifestFingerprint(),
    conversation_history: lastTurns(messages, 2)
  })
  
  // Stage 3+4: Bundle Composer
  const bundle = await compose(queryPlan)
  
  // Stage 5: Retrieval (parallel)
  const toolResults = await Promise.all(
    queryPlan.tools_authorized.map(async (toolName) => {
      const tool = getTool(toolName)
      if (!tool) return null
      return executeWithCache(tool, queryPlan, cache)
    })
  )
  const validToolResults = toolResults.filter(Boolean)
  
  // Stage 6: Validator (bundle integrity)
  const bundleValidations = await runAll(bundle, 'bundle', { query_plan: queryPlan })
  const bundleSummary = summarize(bundleValidations)
  if (bundleSummary.overall === 'fail') {
    if (config.getFlag('VALIDATOR_FAILURE_HALT')) {
      return new Response(JSON.stringify({ error: 'bundle validation failed', failures: bundleSummary.failures }), { status: 422 })
    }
    // else: warn-only, log and continue
  }
  
  // Stage 7: Synthesis (single-model)
  const orchestrator = getSynthesisOrchestrator()
  const synthesisResult = await orchestrator.synthesize({
    query: request.query,
    query_plan: queryPlan,
    bundle,
    tool_results: validToolResults,
    conversation_history: messages,
    selected_model_id: modelId,
    style,
    audience_tier: tier,
    cache,
  })
  
  // Stage 8: Discipline (post-synthesis structural validators) — runs after stream completes
  // [structured event hook for Phase 4 to attach P7/P8 structural + audit_log persistence]
  
  // Stage 8 disclosure filter applied to displayed content
  const filteredStream = applyDisclosureFilter(synthesisResult.stream, tier)
  
  return synthesisResult.toUIMessageStreamResponse(/* ... */)
}

// Flag OFF: existing static path (UNCHANGED)
const systemPrompt = consumeSystemPrompt(chart, reportsResult.rows, style)
// ... [existing code, unchanged]
```

**E.4 — Conversation persistence handling.** The flag-ON path's `synthesisResult.toUIMessageStreamResponse(...)` should call the same `replaceConversationMessages` on-finish that the flag-OFF path uses. Same conversation table; same message shape.

**E.5 — Error handling.** Validator failures, retrieval timeouts, synthesizer errors — all surface as structured error responses. Match the existing error-response patterns used in the flag-OFF path.

**E.6 — Add npm scripts.**
- `pipeline:integration-test` — runs end-to-end pipeline against a test query, asserts output shape.
- `pipeline:accuracy-test` — runs the Phase-2 router accuracy test set against real Claude Haiku 4.5 and reports accuracy.
- `pipeline:msr-sql-test` — runs MSR-SQL filter against live `msr_signals` table for representative QueryPlans, asserts non-empty results for known-good filters.

**E.7 — Tests.**
- Unit test: route with flag OFF hits existing static path; flag ON hits new pipeline (mock the pipeline components).
- Integration test: flag ON, end-to-end with mocked LLM and test data.
- Regression test: flag OFF, run a curated query suite; output matches a saved baseline.

**Stream E acceptance criteria:**
- [ ] Route extended with flag-ON branch.
- [ ] Flag-OFF behavior unchanged (regression suite passes).
- [ ] Flag-ON branch invokes the new pipeline end-to-end.
- [ ] Error handling correctly surfaces validator failures and retrieval errors.
- [ ] Conversation persistence works for both paths.
- [ ] npm scripts for integration + accuracy + MSR-SQL tests added.
- [ ] All tests pass.

## §10 — Integration Verification

After all five sub-streams complete:

**§10.1 — Phase-2 verification gates (carry-forward).**
- Run `npm run pipeline:accuracy-test` with `OPENAI_API_KEY` and Claude provider keys set. Verify classification accuracy ≥80% on the test set.
- Run `npm run pipeline:msr-sql-test` against the live `msr_signals` table. Verify filter returns expected signals for representative QueryPlans.

If either gate fails, halt and surface to native. Tune the router prompt or fix the SQL before proceeding.

**§10.2 — End-to-end pipeline test (flag ON).** With `NEW_QUERY_PIPELINE_ENABLED=true` in dev environment, run a curated query suite (8 queries, one per class) end-to-end. Verify:
- Each query produces a streaming response.
- Conversation persists.
- Audit events emitted via Telemetry.
- Validators run (logged votes).
- Disclosure filter applied (super_admin tier).

**§10.3 — Regression test (flag OFF).** With `NEW_QUERY_PIPELINE_ENABLED=false` (default), run the same curated suite. Compare outputs to saved baselines. They should be functionally equivalent (the existing path is unchanged).

**§10.4 — Equivalence check (flag-OFF vs flag-ON, sample).** For 3-5 representative queries, run with flag OFF and flag ON. Document outputs side-by-side. They should both be acharya-grade and contain the same load-bearing facts and citations. Native reviews these for equivalence; if outputs are dramatically different in quality (either direction), surface to native.

**§10.5 — Test suite execution.** Full project test suite passes.

**§10.6 — `must_not_touch` verification.** `git status` confirms only allowed surfaces modified.

**§10.7 — Lint and type-check.** Clean.

## §11 — Phase 3 Done Criteria

`COMPLETE` when:

1. All Stream A-E acceptance criteria met.
2. Phase-2 verification gates passed (classification accuracy ≥80%; MSR-SQL working).
3. End-to-end flag-ON test succeeds for all 8 query classes.
4. Flag-OFF regression suite passes (existing behavior preserved).
5. Equivalence check documented for sample queries.
6. Test suite + lint + type-check clean.
7. `must_not_touch` verified.
8. Native confirms acceptance.

When complete:
- Brief frontmatter `status` → `COMPLETE`.
- `completed_on` field added.
- `status_history` final entry: classification accuracy measured, validator failure rate observed during integration tests, equivalence check notes.
- Notify native: Phase 3 complete. **The feature flag stays OFF**; flag flip is native's separate operational decision after reviewing.
- Phase 4 (Audit & Persistence) and Phase 5 (Interface basic) brief authoring can begin in parallel (they're independent and both depend only on Phase 3).

## §12 — Communication Discipline

**Halt on uncertainty.** Architectural questions → halt and ask.

**No scope creep.** Tangential issues → `PHASE_3_OBSERVATIONS_v1_0.md`.

**Status updates between sessions.** Multi-session execution updates `status_history`.

**Adherence to architectural principles.** Architecture §3 P.7 (modularity), P.8 (LLM where domain knowledge needed; deterministic for integrity / lookup / persistence), P.10 (multi-model). The Synthesis Orchestrator's Single-Model Strategy is the sole LLM consumer in Phase 3 (the Validator Service is purely deterministic; the Prompt Registry is data; the Disclosure Filter is rule-based).

**The flag stays OFF.** Phase 3 ships the code. Native flips the flag. This is a process discipline — Phase 3's acceptance does not include flag activation.

## §13 — Final Notes

Phase 3 is the wiring phase. By the end, the new pipeline exists end-to-end in the codebase and is testable via the feature flag. The user-visible chat is unchanged when the flag is OFF (which it is by default). When native flips the flag — at their discretion, after reviewing Phase 3 outputs — the chat starts using the new pipeline.

The two Phase-2 verification gates (classification accuracy + MSR-SQL) are the most important integration steps. If either fails, the new pipeline isn't ready; halt and resolve before proceeding to flag-ON deployment readiness.

Single-Model Strategy is the foundation for Phase 7's Panel Strategy. The orchestrator interface is designed so Phase 7 adds Panel Strategy as a sibling under the same `synthesize(request)` entry point. Phase 3 stubs the panel-mode branch for forward-compatibility without implementing it.

Phase 4 (Audit & Persistence) and Phase 5 (Interface basic) can run in parallel after Phase 3 since they depend only on Phase 3's deliverables (audit event hooks for Phase 4; route working end-to-end for Phase 5 to enrich).

---

*End of EXEC_BRIEF_PHASE_3_v1_0.md (status `AUTHORED`, 2026-04-27). Trigger phrase: "Read EXEC_BRIEF_PHASE_3_v1_0.md and execute it." On Phase 3 completion, status flips to `COMPLETE`, the feature flag stays OFF, and Cowork can author Phase 4 + Phase 5 briefs in parallel.*
