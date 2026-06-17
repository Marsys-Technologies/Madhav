---
brief_id: EXEC_BRIEF_PHASE_7
version: 1.0
status: COMPLETE
authored_by: Cowork (Opus)
authored_at: 2026-04-27
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PHASE_7_v1_0.md and execute it."
phase: 7
phase_name: Panel Mode
risk_classification: MEDIUM-HIGH
parallelizable_with: [EXEC_BRIEF_PHASE_8_v1_0.md, M2/B.5 work]
depends_on: [EXEC_BRIEF_PHASE_3_v1_0.md (COMPLETE), EXEC_BRIEF_PHASE_5_v1_0.md (COMPLETE), EXEC_BRIEF_PHASE_6_v1_0.md (COMPLETE)]
estimated_streams: 5
---

# EXEC_BRIEF — Phase 7 — Panel Mode

## Mission

When the native opts in (per-query checkbox or global flag), run the synthesis stage as a **panel of 3 LLM members** plus a **separate adjudicator**. Each panel member sees the same bundle but produces an independent answer. The adjudicator — a model from a different provider family than any panel member — synthesizes their outputs into a single final answer with a divergence report.

This phase is the implementation home of the Panel Synthesis design that was previously living as `PANEL_SYNTHESIS_ADDENDUM_v0_1.md` and `PANEL_IMPLEMENTATION_BRIEF_v1_0.md` (both SUPERSEDED by the holistic architecture). Phase 7 is where it actually ships.

The motivating intuition: a single model has consistent blind spots. Three independent models surface contradictions that a single model would not see. The adjudicator's job is not to pick a winner but to synthesize — and to flag divergence as a first-class output (`DIS.class.*` taxonomy) rather than hide it.

## Scope (`may_touch` / `must_not_touch`)

**`may_touch`:**
- `platform/src/lib/synthesis/panel_strategy.ts` (new — sibling of `single_model_strategy.ts`)
- `platform/src/lib/synthesis/panel/**` (new submodule for panel member runner, adjudicator, divergence detector)
- `platform/src/lib/synthesis/__tests__/panel/**`
- `platform/src/lib/prompts/panel/**` (new — panel-aware prompt variants for member + adjudicator)
- `platform/src/lib/checkpoints/checkpoint_8_5.ts` (extension only — adapt prompt for panel-adjudicator output; no behavior change in single-model path)
- `platform/src/components/consume/PanelAnswerView.tsx` (new)
- `platform/src/components/consume/DivergenceReport.tsx` (new)
- `platform/src/components/consume/ConsumeChat.tsx` (extend with per-query Panel checkbox; auto-resets per native's earlier directive)
- `platform/src/lib/synthesis/orchestrator.ts` (add strategy switch: when `PANEL_MODE_ENABLED=true` AND request opts in, route to panel_strategy; default = single_model_strategy)
- `platform/src/app/api/consume/route.ts` (add request-level panel opt-in flag pass-through; flag-OFF behavior unchanged)
- `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md` (additive — register `DIS.class.panel_divergence` taxonomy entries; do NOT touch existing entries)

**`must_not_touch`:**
- `platform/src/lib/synthesis/single_model_strategy.ts` (single-model path frozen — Phase 7 adds parallel strategy, doesn't modify)
- `platform/src/lib/validators/**`, `platform/src/lib/prompts/*.ts` outside the new `panel/` subdirectory, `platform/src/lib/disclosure/**`, `platform/src/lib/router/**`, `platform/src/lib/bundle/**`, `platform/src/lib/retrieve/**` (all frozen)
- `platform/src/lib/audit/**`, `platform/src/lib/prediction/**` (Phase 4 territory — Phase 7 emits via the existing audit hook only)
- `platform/src/lib/checkpoints/checkpoint_4_5.ts`, `checkpoint_5_5.ts` (frozen — only 8.5 needs panel-aware variant)
- `platform/python-sidecar/**`
- `platform/src/components/citations/**`, `platform/src/components/disclosure/**` (Phase 5 territory — Phase 7 reuses these components, doesn't modify)
- Any DB migration
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`
- Any flag-OFF code path

## Sub-streams (5 total)

### Stream A — Panel Member Runner

- New file `platform/src/lib/synthesis/panel/member_runner.ts`. Function `runPanelMembers(bundle, request, members: PanelMemberConfig[]): Promise<PanelMemberOutput[]>`.
- Each `PanelMemberConfig` specifies: provider family (`anthropic | openai | google | deepseek`), model id, temperature, prompt variant tag (default `panel_member_v1`).
- Default panel: 3 members chosen by the request's `panel_slate` config or fallback `[claude-sonnet-4-6, gpt-4-1, gemini-1-5-pro]`. The exact default slate is defined in `platform/src/lib/synthesis/panel/default_slate.ts` for easy override.
- All members run **concurrently** via `Promise.allSettled`. A member that fails (timeout, provider error, parse error) returns a structured `PanelMemberOutput` with `status: 'failed'` rather than throwing — the panel proceeds with the surviving members.
- **Concurrent retry with N=3.** Each member call wraps in a retry loop of up to 3 concurrent attempts (the first to succeed wins, others abort) — this is the pattern the native pre-approved during the panel brainstorm. Per-member helper at `platform/src/lib/synthesis/panel/concurrent_retry.ts`.
- **Opt-in 2-of-3 degrade mode.** If `PANEL_DEGRADE_2_OF_3=true` and one member permanently fails, the panel proceeds with 2 surviving members and emits a `DegradeNotice` field on the audit event. Default `PANEL_DEGRADE_2_OF_3=false` — failure of any member halts the panel with a structured failure object that Phase 5's `<ValidatorFailureView />` renders.
- 12+ tests: 3 happy paths; one-member-fails with degrade ON; one-member-fails with degrade OFF; concurrent-retry race; timeout handling; structured output parsing per member.

### Stream B — Adjudicator

- New file `platform/src/lib/synthesis/panel/adjudicator.ts`. Function `adjudicate(memberOutputs: PanelMemberOutput[], bundle, request): Promise<AdjudicationResult>`.
- The adjudicator is a separate LLM call. **Family-level exclusion rule** (from the panel brainstorm): the adjudicator's provider family MUST be different from every panel member's provider family. Helper `selectAdjudicator(memberSlate, candidatePool): AdjudicatorConfig` enforces this; throws if no candidate exists.
- Default candidate pool: same 4 families as panel members. Default selection: pick the family not in the panel slate; if all 4 are in the panel slate (impossible with default slate of 3), error out.
- The adjudicator receives **anonymized panel outputs** — each member output is presented as `Member 1 / Member 2 / Member 3` with the model identity stripped. Helper `anonymizePanelOutputs(outputs)` does this. Test that the adjudicator prompt does not contain provider/model names.
- Adjudicator's job is **synthesis, not selection**. The prompt explicitly forbids "pick the best one" — instructs the adjudicator to (a) identify points of agreement and disagreement; (b) synthesize a unified answer that incorporates the agreed material and explicitly flags the disagreements; (c) attach a `divergence_summary` field describing where members differed and on what.
- Output: `AdjudicationResult = {final_answer: string, divergence_summary: DivergenceSummary, member_alignment: {member_1: 'aligned'|'partial'|'dissent', member_2: ..., member_3: ...}}`.
- Default adjudicator model: configurable; fallback `gemini-1-5-pro` (assumes default panel slate is Anthropic+OpenAI+Google → wait, that's a conflict; correct fallback adjudicator is `deepseek-chat` since DeepSeek is the family not in the default slate). Verify the slate→adjudicator mapping in `platform/src/lib/synthesis/panel/default_slate.ts`.
- 10+ tests: family-exclusion enforced; anonymization complete (no model names leak through); synthesis-not-selection prompt; partial-dissent rendering; adjudicator-fails-too edge case (halt).

### Stream C — Divergence Detector + Taxonomy

- New file `platform/src/lib/synthesis/panel/divergence_detector.ts`. Function `classifyDivergence(memberOutputs, adjudication): DivergenceClassification`.
- Classifies each pair-wise disagreement into one of:
  - `DIS.class.factual` — members disagree on a stated fact (which house, which dasha period, etc.)
  - `DIS.class.interpretive` — members agree on facts but interpret differently
  - `DIS.class.scope` — members chose different framings of the question
  - `DIS.class.confidence` — members agree on direction but differ in confidence
  - `DIS.class.extension` — one member extended into territory others did not (e.g., added a remedial recommendation when the others stayed analytical)
- New register additions in `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md` under a new section `DIS.class.panel_divergence` — additive, sibling to existing `DIS.class.mirror_desync` etc. Use existing schema; do not modify existing entries.
- The divergence classification attaches to the audit event payload at `payload.panel.divergence_classification` — Phase 4's v1 consumer stores it as JSONB without schema bump.
- 10+ tests: each class has a synthetic example that the classifier picks correctly; mixed-class output (multiple disagreements at once); empty-divergence case (panel agreed).

### Stream D — Panel UI Layer

- New component `<PanelAnswerView panel={...} />` at `platform/src/components/consume/PanelAnswerView.tsx`. Renders:
  - The adjudicator's final answer (using existing `<StreamingAnswer />` + `<CitationChip />` pattern from Phase 5)
  - A collapsed-by-default `<DivergenceReport />` that lists the divergence classifications with member-level dissent indicators
  - A "show panel members" expander that reveals the 3 anonymized member outputs side-by-side or stacked (responsive)
- New component `<DivergenceReport classifications={...} alignment={...} />` at `platform/src/components/consume/DivergenceReport.tsx`. Color-coded by class; shows member alignment badges.
- Per-query Panel checkbox in `<ConsumeChat />`: a small toggle above the input that auto-resets to OFF after each submit (per the native's earlier directive — panel mode is opt-in per query, not sticky).
- Global enable: `PANEL_MODE_ENABLED` flag (default `false`). When OFF, the checkbox is hidden entirely. When ON, the checkbox is visible but unchecked by default for each new query.
- 12+ tests: panel-view rendering; expander; divergence-report variants; checkbox auto-reset; flag-OFF hides checkbox.

### Stream E — Strategy Switch + Orchestrator + Route Wiring

- Extend `platform/src/lib/synthesis/orchestrator.ts` with a strategy selector: when `PANEL_MODE_ENABLED=true` AND `request.panel_opt_in === true`, route to `panel_strategy.ts`; otherwise route to `single_model_strategy.ts`. Both paths converge on the same audit event emission.
- New file `platform/src/lib/synthesis/panel_strategy.ts` orchestrates Streams A → B → checkpoint 8.5 (panel-aware variant) → C. Returns the same `SynthesisOutput` shape as `single_model_strategy.ts` but with optional `panel` payload attached.
- Checkpoint 8.5 prompt extension: when input is panel-adjudicator output, add a clause "the input is a panel-synthesized answer; verify the divergence_summary is honest (no contradictions silently smoothed) in addition to standard coherence checks."
- Route wiring in `platform/src/app/api/consume/route.ts`: thread `panel_opt_in` request field through. Flag-OFF behavior unchanged byte-identical.
- 8+ tests at the strategy-switch level: flag-OFF + opt-in=true → still single-model; flag-ON + opt-in=false → single-model; flag-ON + opt-in=true → panel; audit-event shape consistent across both paths.

## Critical constraints

- **Family-level adjudicator exclusion is non-negotiable.** This is the core epistemic claim of the design — the adjudicator must come from outside the panel's collective bias surface. Tests must verify the rule programmatically, not just by inspection.
- **Anonymization must be complete.** The adjudicator must NOT see which member produced which output. Tests must check the rendered prompt for absence of model/provider names.
- **Synthesis-not-selection.** The adjudicator prompt must not instruct picking a winner. Tests must verify the adjudicator never returns "Member 2 was correct" — instead returns a synthesized answer with divergence flagged.
- **Concurrent retry pattern (N=3).** First success wins; others abort. Test the abort path — late winners must not corrupt state.
- **Default `PANEL_DEGRADE_2_OF_3=false`.** Strict mode is the default. Native opts in to degrade mode after observing live behavior.
- **Per-query checkbox auto-resets.** Panel mode is opt-in per query, never sticky. UI test must verify checkbox state resets after submit.
- **Flag-OFF behavior is byte-identical to Phase 3 single-model path.** Regression suite proves this.
- **Audit event compatibility.** Panel payload lands at `payload.panel.*` — Phase 4 v1 consumer stores as JSONB, Phase 8 Audit View later renders it.
- **Cost discipline.** Panel mode is 4× the LLM cost of single-model (3 members + 1 adjudicator). The flag default OFF and the per-query opt-in protect against accidental burn.

## Done criteria

1. Stream A: panel member runner with concurrent retry + degrade-mode flag passes 12+ tests.
2. Stream B: adjudicator with family-exclusion + anonymization + synthesis-not-selection passes 10+ tests.
3. Stream C: divergence detector + taxonomy register addition passes 10+ tests; `DISAGREEMENT_REGISTER_v1_0.md` updated additively.
4. Stream D: `<PanelAnswerView />` + `<DivergenceReport />` + per-query checkbox passes 12+ tests; flag-OFF hides checkbox.
5. Stream E: strategy switch passes 8+ tests; flag-OFF byte-identical to Phase 3.
6. End-to-end: with `PANEL_MODE_ENABLED=true` in dev and per-query opt-in, run one query of each of the 8 query classes; visually inspect panel rendering and divergence report.
7. End-to-end with `PANEL_DEGRADE_2_OF_3=true`: simulate one member failing; verify panel proceeds and renders DegradeNotice.
8. Family-exclusion programmatic verification: attempting to use an adjudicator from a panel family throws.
9. Anonymization verification: rendered adjudicator prompt contains no model/provider names.
10. `lint` + `type-check` clean.
11. `must_not_touch` verified.
12. Native acceptance.

## Risk classification: MEDIUM-HIGH

Phase 7 is the largest behavior delta since Phase 3. It introduces a new synthesis strategy with complex orchestration (concurrent calls, anonymization, family-exclusion, divergence). Mitigations:
- Strict feature-flag isolation (`PANEL_MODE_ENABLED` + per-query opt-in)
- Single-model strategy path is frozen and proven
- Default `PANEL_DEGRADE_2_OF_3=false` keeps strict mode as the default
- Family-exclusion is enforced programmatically, not by convention
- Anonymization is verified by test, not by inspection
- Concurrent retry pattern uses well-understood primitives (`Promise.race` with abort)
- Cost discipline via OFF default and per-query opt-in

## Forward implications

- **Phase 8 (Audit View UI)** will render panel payload as a sub-section of audit rows when `payload.panel` is present. Phase 7 ships the data; Phase 8 ships the view.
- **Phase 10 (Calibration Loop)** treats panel-derived predictions and single-model predictions as separate calibration buckets — the calibration_bucket field in `prediction_ledger` will distinguish them.
- **Multi-Agent governance.** The DIS.class.panel_divergence taxonomy entries land in the existing DISAGREEMENT_REGISTER alongside DIS.class.mirror_desync etc., maintaining consistency with Cowork–Gemini collaboration governance.

## How native triggers

Open a Claude Code session in Anti-Gravity (Sonnet 4.6 in VS Code extension). Paste:

> Read EXEC_BRIEF_PHASE_7_v1_0.md and execute it.

Disjoint from Phase 8 (audit UI surface) — both can run concurrently in two sessions.

## Status updates

- AUTHORED 2026-04-27
- IN_PROGRESS — 2026-04-28 (Claude Code Sonnet 4.6, VS Code)
- COMPLETE — 2026-04-28. All 5 streams implemented; 104 Phase 7 tests passing; 0 TypeScript errors; pre-existing failures unchanged.
