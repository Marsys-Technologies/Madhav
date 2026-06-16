---
brief_id: EXEC_BRIEF_PHASE_5
version: 1.0
status: COMPLETE
authored_by: Cowork (Opus)
authored_at: 2026-04-27
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PHASE_5_v1_0.md and execute it."
phase: 5
phase_name: Interface basic
risk_classification: LOW-MEDIUM
parallelizable_with: [EXEC_BRIEF_PHASE_4_v1_0.md, EXEC_BRIEF_PHASE_9_HOTFIX_v1_0.md, M2/B.5 work]
depends_on: [EXEC_BRIEF_PHASE_3_v1_0.md (COMPLETE)]
estimated_streams: 4
---

# EXEC_BRIEF — Phase 5 — Interface basic

## Mission

Render the new pipeline's output in the Consume chat UI when the feature flag is ON. The user must be able to (a) see the answer streamed token-by-token; (b) see citations rendered as clickable references to signal IDs / asset IDs; (c) see the disclosure tier the answer was filtered through; (d) see a clear failure-state message when a validator halts synthesis. Flag-OFF UI is unchanged.

This phase is intentionally **basic** — it makes the new pipeline's output visible and inspectable but does NOT yet build the audit-view UI (Phase 8) or panel-mode UI (Phase 7). It's the minimum interface delta to make flag-ON usable.

## Scope (`may_touch` / `must_not_touch`)

**`may_touch`:**
- `platform/src/components/consume/**` (Consume tab UI)
- `platform/src/components/citations/**` (new)
- `platform/src/components/disclosure/**` (new)
- `platform/src/lib/ui/**` (any client-side helpers needed for streaming/citation parsing)
- `platform/src/app/consume/page.tsx` (page-level integration)
- Storybook/component tests under existing `__tests__/` patterns
- `platform/src/styles/**` (only additions for new components; no global theme changes)

**`must_not_touch`:**
- `platform/src/app/api/consume/route.ts` (Phase 3 owns route; Phase 4 owns audit consumer; Phase 5 is UI-only)
- `platform/src/lib/synthesis/**`, `platform/src/lib/validators/**`, `platform/src/lib/prompts/**`, `platform/src/lib/disclosure/**` (Phase 3 frozen)
- `platform/src/lib/router/**`, `platform/src/lib/bundle/**`, `platform/src/lib/retrieve/**` (Phase 2/9 frozen)
- `platform/src/lib/audit/**`, `platform/src/lib/prediction/**` (Phase 4 territory)
- `platform/python-sidecar/**`
- Any flag-OFF UI path
- Any DB migration
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`

## Sub-streams (4 total)

### Stream A — Streaming text renderer
- New component `<StreamingAnswer />` that consumes the existing Vercel ai SDK stream Phase 3 emits.
- Renders tokens as they arrive; preserves whitespace; handles cancel/abort cleanly.
- When stream completes, hands off to a finalized `<AnswerView />` that locks in the rendered text.
- Loading state: subtle pulse on the cursor while streaming; no jarring layout shifts.
- Error state: if stream errors mid-flight, show a clear "synthesis failed" affordance with retry button.
- Flag check: component only mounts when `NEW_QUERY_PIPELINE_ENABLED=true` (read from a client-safe config endpoint Phase 0 already exposes — verify before authoring).
- 8+ tests: token-by-token rendering; abort handling; error display; flag-gated mount.

### Stream B — Citation rendering
- Phase 3's synthesis output embeds citation markers in the form `[signal:S0042]`, `[asset:CGM]`, `[chunk:rag_chunk_id]` per the prompt registry's instructions.
- New component `<CitationChip variant="signal|asset|chunk">` renders each marker as a small inline pill.
- Click behavior: opens a side panel `<CitationPreview />` that shows the cited row's content (signal definition, asset summary excerpt, or chunk text). Side panel is read-only.
- Citation parser `platform/src/lib/ui/citation-parser.ts`: extracts markers from the streamed text, returns `{text_with_placeholders, citation_index}`. Pure function, fully tested.
- Side panel fetches preview content via a NEW lightweight read endpoint `GET /api/citations/preview?type=signal&id=S0042` (or asset/chunk variants). Endpoint is part of Stream B; it reads from existing tables, no migrations, no writes.
- 12+ tests: parser correctness on synthetic inputs; chip render variants; click→panel flow; endpoint shape.

### Stream C — Disclosure tier indicator
- New component `<DisclosureTierBadge tier="super_admin|acharya_reviewer|client|public_redacted">` rendered above the answer.
- Visual: small pill in the answer header with tier name + tooltip describing what the tier means.
- Phase 3 sets the tier in the response payload (Stream C of Phase 3 already filters by tier; the chosen tier is passed through to UI).
- For `super_admin` (developer mode), include a "show methodology disclosure" expander that reveals the methodology block (Phase 3 emits this; Phase 5 just renders it).
- 6+ tests: tier-to-color mapping; tooltip render; methodology expand/collapse; default tier handling.

### Stream D — Validator failure / halt-state rendering
- When `VALIDATOR_FAILURE_HALT=true` and a validator (P1/P2/P5) fails, Phase 3 returns a structured failure object instead of streaming text.
- New component `<ValidatorFailureView failures={...} />`: shows which validator(s) failed with a concise human-readable explanation; provides a "show technical detail" expander with the raw validator payload; offers a "retry with different framing" action that simply re-submits the user's last query as a new chat turn.
- No retry-loop logic in UI; retry is a fresh submit. Sophisticated retry is Phase 6 territory (LLM Checkpoints).
- 6+ tests: render with single failure; render with multi failure; expand/collapse detail; retry-button submits.

## Critical constraints

- **Flag-OFF UI is byte-identical.** Phase 5 components mount only when flag is ON. Run flag-OFF regression — pixel-diff or snapshot test must pass unchanged.
- **No global theme/style mutation.** All new styles are component-scoped (CSS modules, Tailwind utilities, or styled-component locals — match the project's existing pattern). Do not edit global CSS.
- **No new client-side state libraries.** Use the project's existing state pattern (likely React state + maybe Zustand if already in use; verify before authoring).
- **No DB writes from Phase 5.** Stream B's preview endpoint is read-only; if no row matches, return 404 without side effects.
- **Streaming abort must be clean.** If user navigates away mid-stream, the in-flight request must be aborted (use AbortController). Verify with a test.
- **Accessibility.** Every interactive element (CitationChip, methodology expander, retry button, side panel) must have a keyboard path and ARIA labels. Run `axe-core` or equivalent in tests.

## Done criteria

1. Stream A: streaming renderer works against flag-ON pipeline; tests pass; abort verified.
2. Stream B: citation chips render correctly; preview endpoint round-trips; parser tests pass.
3. Stream C: disclosure badge renders for all 4 tiers; methodology expander works for super_admin.
4. Stream D: validator failure view renders for all 3 validators (P1/P2/P5); retry flow works.
5. Flag-OFF regression: all existing UI snapshot/pixel tests pass unchanged.
6. Manual smoke: with flag ON in dev environment, submit one query of each of the 8 classes; visually inspect the rendering for each.
7. Accessibility: axe-core (or project equivalent) reports no violations on the new components.
8. `lint` + `type-check` clean.
9. `must_not_touch` verified.
10. Native acceptance (visual review of the 8-class smoke).

## Risk classification: LOW-MEDIUM

UI changes are visible and easy to review, which lowers risk. Mitigations:
- Flag-OFF path is untouched (zero behavioral change without flag flip)
- New components are isolated; no global theme mutation
- Citation preview endpoint is read-only (no DB-write attack surface)
- Streaming uses well-understood primitives (Vercel ai SDK + AbortController)

The MEDIUM half of the rating reflects: streaming UIs are easy to break subtly (race conditions, abort handling, layout shifts under content). Tests + manual 8-class smoke catch these.

## Forward implications

- **Phase 4 (Audit & Persistence)** is independent — Phase 5 doesn't depend on audit_log existing; the audit row is written separately and Phase 5 doesn't read it (yet).
- **Phase 6 (LLM Checkpoints)** will extend the validator-failure view with checkpoint-aware retry suggestions.
- **Phase 7 (Panel Mode)** layers a new `<PanelAnswerView />` above this — Phase 5 sets the foundation by establishing the streaming + citation + disclosure pattern; Phase 7 extends it to N independent answers + 1 adjudication.
- **Phase 8 (Audit View UI)** is a separate UI surface (likely a new tab) that reads from `audit_log`. Phase 5 components are reused there for rendering but the audit-list view itself is Phase 8.

## How native triggers

Open a Claude Code session in Anti-Gravity (Sonnet 4.6 in VS Code extension). Paste:

> Read EXEC_BRIEF_PHASE_5_v1_0.md and execute it.

This brief is disjoint from Phase 4 and the Phase 9 hotfix — they touch different surfaces and can run in three concurrent Claude Code sessions safely. Phase 5 owns UI; Phase 4 owns DB; Phase 9 hotfix owns retrieve/vector_search.ts.

## Status updates

- AUTHORED 2026-04-27
- IN_PROGRESS_STREAM_A 2026-04-28 — Sonnet picked up brief; built streaming renderer + AnswerView
- IN_PROGRESS_STREAM_B 2026-04-28 — citation parser, CitationChip, CitationPreview, /api/citations/preview
- IN_PROGRESS_STREAM_C 2026-04-28 — DisclosureTierBadge, 4-tier tooltip + methodology expander
- IN_PROGRESS_STREAM_D 2026-04-28 — ValidatorFailureView, validator error parsing
- COMPLETE 2026-04-28 — 62 tests pass; tsc clean; lint clean; must_not_touch verified; no regressions
