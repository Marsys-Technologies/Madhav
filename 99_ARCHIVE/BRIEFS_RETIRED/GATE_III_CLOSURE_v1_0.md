---
artifact: GATE_III_CLOSURE_v1_0.md
gate_id: GATE-III-INTELLIGENT-CHAT
version: 1.0
status: CLOSED
authored_by: Claude Opus 4.7 (Gate III Design + Coordination Cowork conversation) — 2026-05-13
closes_brief: 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_GATE_III_v1_0.md
companion_artifacts:
  - 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_GATE_III_v1_0.md (status: COMPLETE)
  - worktree:GATE_III_HANDOFF.md
  - worktree:GATE_III_AUDIT.md
  - worktree:GATE_III_SMOKE_FINDINGS.md
  - worktree:GATE_III_SMOKE_VISUAL_CHECKLIST.md (pending native walkthrough)
worktree_path: /Users/Dev/Vibe-Coding/Apps/marsys-gate3-smart-chat
branch: feature/gate3-intelligent-chat
initial_ship_commit: 991bcab
smoke_close_commit: a8a6029
merged_to_main: false
purpose: >
  Formal closure record for the Gate III design + execution + smoke arc.
  Documents all 25 ACs with final status, the 10 automated smoke ACs, smoke
  fixes, locked architectural decisions, the one significant deviation from
  the brief (SSE → Vercel AI UI message stream protocol), and open items
  carried forward to the macro plan conversation + Gate IV.
---

# Gate III — Intelligent Chat Interface — Formal Closure

**Gate scope:** Transform the consume chat into a domain-aware, pipeline-intelligent Jyotish interface. Add: live reasoning surface in classical Jyotish vocabulary, inline reasoning-in-prose with citations, factual correction doctrine, Sanskrit hover tooltips, post-answer provenance pills with expandable drawer, context-usage cue, smart prior-turn selection, conversation history drawer, conversation auto-titling, empty-state suggestions (class-based + dasha/transit-context-based). Run overnight as a single executor session, in parallel with Gate I (Performance Command Center) and Gate II (Trace Pipeline Alignment).

**Gate outcome:** Shipped on `feature/gate3-intelligent-chat` at commit `991bcab` (initial overnight ship) → `a8a6029` (post-smoke fixes). Not merged to `main`; merge sequencing belongs to the macro plan conversation per `OPUS_PLANNING_SESSION_v2_0.md §9` once Gate II also reports complete.

---

## §1 — Conversation Lifecycle

This closure record covers a single Cowork conversation (Opus 4.7) that owned Gate III end-to-end:

| Stage | Activity | Output |
|---|---|---|
| 1. Vision elicitation | Native described full vision (full chart context, ambient reasoning, sophisticated provenance, factual correction, reasoning-first answers, smart context handling) | Vision captured in §11 of the brief |
| 2. Scoping Q&A | 12-question batch across A–L; native answered with locked decisions on each | Decision table in conversation; carried into brief |
| 3. Architect's calls | Four outstanding questions (Q1–Q4) locked by Opus with native override window | §11 of brief |
| 4. Brief authoring | `CLAUDECODE_BRIEF_GATE_III_v1_0.md` — 16 work items (W0–W15), 25 ACs, may/must-not-touch scope, locked decisions | Authored to `00_ARCHITECTURE/briefs/` |
| 5. Worktree staging | Brief copied to `marsys-gate3-smart-chat` worktree root as `CLAUDECODE_BRIEF.md`; prerequisites verified (proxy on :5433, .env.local with GEMINI_API_KEY) | Worktree ready |
| 6. Overnight executor | Claude Code Sonnet 4.6 in Anti-Gravity, `--dangerously-skip-permissions` — completed W0–W15 | 24 new files + 6 modified; commit `991bcab` |
| 7. Smoke verification | Claude Code Sonnet 4.6 — 10/10 automated ACs against live Gemini; 4 smoke fixes; visual checklist authored | commit `a8a6029` |
| 8. Closure (this artifact) | Formal closure record + memory updates | This file |

**Pending:** native's visual walkthrough of `GATE_III_SMOKE_VISUAL_CHECKLIST.md` (20 items). Findings, if any, land as additional commits on the same branch before merge.

---

## §2 — Acceptance Criteria — Final Status

### 2.1 — Structural / artifact-level (verified at executor close)

| AC | Description | Status |
|---|---|---|
| AC.III.1 | `lib/jyotish/domain_labels.ts` exists with `ASSET_LABELS`, `QUERY_CLASS_LABELS`, `PIPELINE_STEP_NARRATION`, `formatTechnicalTag`, `labelFor` | ✅ PASS |
| AC.III.2 | Every key in `ASSET_LABELS` and `PIPELINE_STEP_NARRATION` has a non-jargon value | ✅ PASS |
| AC.III.3 | `types/sse_events.ts` exists with all 10 event types fully typed | ✅ PASS (adapted to Vercel AI UI message metadata — see §4) |
| AC.III.6 | Synthesis prompt v2.0 includes reasoning narration, correction doctrine, inline citations, Sanskrit annotation, out-of-domain handling | ✅ PASS |
| AC.III.7 | Synthesis orchestrator parses `‹reasoning›`, `‹correction›`, `‹sanskrit›`, `‹out_of_domain›` markers and emits matching events | ✅ PASS |
| AC.III.12 | `/api/chat/consume` emits all 10 event types in correct order on a representative query | ✅ PASS (via Vercel AI UI protocol — see §4) |
| AC.III.14 | `LiveReasoningCard` renders thinking indicator, most-recent step, expand/collapse, persists after streaming | ✅ PASS (unit + smoke; visual walkthrough pending — checklist item 7) |
| AC.III.15 | `AnswerView` renders CorrectionNotice, OutOfDomainBanner, ContextUsageCue | ✅ PASS (unit + smoke; visual walkthrough pending — items 14, 15, 16) |
| AC.III.16 | `SanskritTermSpan` renders hover tooltip with term, transliteration, definition; keyboard accessible | ✅ PASS (unit + smoke; visual walkthrough pending — item 9) |
| AC.III.17 | `PostAnswerProvenance` renders three pills; click opens drawer; drawer has Astrological + Technical tabs; no internal jargon in Astrological tab | ✅ PASS (unit + smoke; visual walkthrough pending — items 11/12) |
| AC.III.18 | `ConversationHistoryDrawer` lists prior conversations; click navigates; search filters | ✅ PASS (unit + smoke; visual walkthrough pending — items 6, 18) |
| AC.III.20 | `EmptyState` renders two tabs; class-based suggestions appear; moment-based suggestions fetch and render | ✅ PASS (unit + smoke; visual walkthrough pending — items 3, 4, 5) |
| AC.III.22 | `ConsumeChat` wires all new components; trace drawer still opens and renders | ✅ PASS — trace surface byte-identical verified (see AC.III.22 below) |
| AC.III.23 | `npx tsc --noEmit`: no new errors vs baseline | ✅ PASS — 22 errors == baseline |
| AC.III.24 | `npm run lint`: clean | ✅ PASS |
| AC.III.25 | `npm test`: all tests green | ✅ PASS — 37/37 new + all existing |

### 2.2 — Live-LLM-required (verified at smoke close)

| AC | Description | Status |
|---|---|---|
| AC.III.4 | Planner emits `prior_turn_relevance` field with valid `used`, `reason`, `mode` | ✅ PASS — smoke verified with live Gemini |
| AC.III.5 | Planner golden-set regression: recall ≥ 0.97, precision ≥ 0.95 | ✅ PASS — recall=**1.00**, precision=**1.00** |
| AC.III.8 | Reasoning vocabulary: no banned tokens (MSR, FORENSIC, CGM, UCN, CDLM, RM, LEL, pgvector, cosine, embedding, chunk_id) in any reasoning step | ✅ PASS — automated string scan over live synthesis output |
| AC.III.9 | 8/8 prompts with factual errors trigger `correction` with valid structure | ✅ PASS — Capricorn correction emitted correctly for the deliberate "Sun in Aries" probe |
| AC.III.10 | 4/4 non-Jyotish prompts trigger `out_of_domain`; 4/4 Jyotish prompts do not | ✅ PASS |
| AC.III.11 | Prompts likely to use Sanskrit emit ≥1 `sanskrit_terms` event with valid shape | ✅ PASS |
| AC.III.13 | First turn of new conversation emits `conversation_title`; subsequent turns do not | ✅ PASS |
| AC.III.19 | `/api/consume/conversations` returns expected shape and is auth-gated | ✅ PASS — 401 without auth |
| AC.III.21 | `/api/consume/suggestions/context` returns valid suggestion list and is cached per-session | ✅ PASS — live computation + cache verified |
| AC.III.22 (trace isolation) | `git diff --stat main -- 'components/trace/' 'lib/admin/trace_assembler.ts' 'lib/admin/trace_client.ts'` returns empty | ✅ PASS — Gate II's territory byte-identical |

**All 25 ACs: PASS at the verifiable layer.** Items requiring eye-test (drawer animations, hover styling, banner placement, the "does this feel right" subjective pass) are captured in `GATE_III_SMOKE_VISUAL_CHECKLIST.md` (20 items) and remain pending the native's walkthrough. Visual findings, if any, fold back as commits on the same branch before merge.

---

## §3 — Smoke Fixes Applied (commit `a8a6029`)

Four fixes landed during smoke verification. Each is one focused commit on `feature/gate3-intelligent-chat`:

1. **`regression_baseline.json` extended to GT.030–GT.046.** The planner golden set had been expanded from 29 → 46 entries during the pre-Gate-III pipeline gap plan work, but the baseline file (the per-query expected-output reference) lagged. Gate I's W0 audit had reported 29 — accurate against the baseline file, misleading against the actual dataset. This fix brings them into agreement. Resolves the open golden-set count discrepancy memory entry. Planner eval at the fixed baseline: recall=1.00, precision=1.00.

2. **Synthesis prompt `SANSKRIT_ANNOTATION_GATE` strengthened with a concrete worked example.** Showing `‹sanskrit term="Atmakaraka" def="..." translit="...">Atmakaraka‹/sanskrit›` in the prompt itself (rather than just describing the desired form) lifted Gemini's compliance with closing tags from inconsistent to reliable.

3. **`marker_parser.ts` `OUT_OF_DOMAIN_RX` made tolerant of open-only forms.** Gemini sometimes emits `‹out_of_domain reason="..."›` without a closing tag; the trailing content is the answer payload. The parser now accepts this shape rather than failing to capture the out-of-domain signal.

4. **`reasoning_vocabulary.smoke.ts` `containsBannedToken()` signature fix.** Minor test-infrastructure correction (1-arg, not 2). Caught during smoke; trivial.

---

## §4 — Significant Deviation from Brief

**Brief specification:** Multiplex 10 named SSE event types on `/api/chat/consume` (`reasoning_step`, `answer_chunk`, `context_usage`, `correction`, `out_of_domain`, `sanskrit_terms`, `provenance`, `conversation_title`, `done`, `error`).

**Implemented architecture:** Inline tagged markers in the streaming text (`‹reasoning›`, `‹correction›`, `‹sanskrit›`, `‹out_of_domain›`) plus `messageMetadata` for structured payloads (provenance, sanskrit_terms dictionary, conversation_title, context_usage). Same semantic event model; different wire format.

**Rationale:** The codebase imports from the `ai` npm package (version `^6.0.168`) across 20+ files including the consume route, both synthesis strategies, panel adjudicator, conversation title generator, `useChat` hook, StreamingAnswer, ConsumeChat. This package — published by Vercel, MIT-licensed, hosting-platform-agnostic, runs on Cloud Run identically to anywhere else — defines its own streaming wire protocol (`0:` / `2:` / `8:` / `e:` prefixed chunks) consumed by `useChat` on the client. Raw SSE and the `ai` SDK's protocol are mutually exclusive on the same response stream. Reimplementing the streaming layer to raw SSE would have rippled across all 20+ consumers, materially expanded scope, and broken the existing `useChat` integration. The executor's adaptation is the pragmatic translation that preserves the information model while respecting the codebase's existing architecture.

**Impact on Gate II:** None. The trace SSE stream (`/api/trace/stream/[queryId]`) is a separate endpoint with its own protocol; Gate II's trace-alignment work is unaffected by this consume-route deviation.

**Documentation:** Full rationale in `GATE_III_AUDIT.md` at the worktree root.

---

## §5 — Architect's Locked Decisions (carried into implementation)

These 23 decisions, locked during the native's planning Q&A, were preserved through implementation and smoke. Any post-merge change to consume behavior should justify itself against this list:

1. Drop "full chart pre-load" — retrieval is the only context mechanism.
2. Live reasoning surface uses classical Jyotish vocabulary only — no internal IDs.
3. Live reasoning placement: inline above streaming answer.
4. Live reasoning visibility: most-recent visible, full flow on click-to-expand, persists after streaming.
5. Reasoning narration source: both pipeline events (translated) and synthesis-time LLM narration.
6. Final answer reasoning: inline in prose, no separate section.
7. Citations: inline `[N]` markers, source list in provenance drawer.
8. Correction doctrine: lead with correction, no halt-and-confirm.
9. Correction scope: chart facts + classical-consensus errors + methodological errors.
10. Correction bar: "no classical citation supports the user's claim" — minority views with classical backing are not overridden.
11. Context handling: smart per-query selection by planner; context for comprehension only.
12. Visible context cue: yes, shows mode per response.
13. Provenance — models: every model in chain, hidden behind expand.
14. Provenance — sources: asset-level visible, granular on expand.
15. Provenance split: astrological + technical tabs, both hidden by default.
16. Dasha/transit panel: dropped.
17. Sanskrit definitions: hover tooltip only, LLM-annotated at synthesis time.
18. Empty state: two-tab toggle — class-based + moment-based.
19. Conversation persistence: across sessions, sidebar drawer.
20. Input intelligence: none; minimalist input.
21. Visual baseline: enhance current visual, don't redesign.
22. Conversation auto-titling: after first user query, one Flash call.
23. Out-of-domain: answer briefly + flag with banner; don't refuse or redirect.

Also resolved late in the planning conversation by architect's call (Q1–Q4): retrieval-phase reasoning translated to specific astrological phrases (b); pushback only when no classical citation supports user's claim; conversation title generated after first user query; out-of-domain answered briefly with prominent flag.

---

## §6 — Memory State

Memory entries created or updated during this conversation:

- `project_gate_iii_complete.md` — updated through both the initial ship and the smoke close; describes commit `a8a6029`, the 10/10 automated ACs, the smoke fixes, the deviation rationale, the open visual walkthrough, and the deferred `/consume` shortcut.
- `project_golden_set_count_discrepancy.md` — flipped from `open` to **RESOLVED**; documents root cause (stale `regression_baseline.json`) and resolution (extension to GT.030–046 at commit `a8a6029`).
- `feedback_gemini_open_only_tags.md` — NEW. Reusable feedback note: Gemini sometimes drops closing tags on XML-like markers; default parsers to tolerant + include concrete worked example in prompt to lift compliance. Applies forward to any future tagged-output design.
- `MEMORY.md` index — three lines updated/added to reflect the above.

---

## §7 — Open Items Carried Forward

### 7.1 — Open at this closure

| Item | Owner | Where it lands |
|---|---|---|
| Visual walkthrough of 20-item checklist | Native | `GATE_III_SMOKE_VISUAL_CHECKLIST.md`; findings (if any) fold back as commits on `feature/gate3-intelligent-chat` |
| Three-way merge sequence (Gate II → Gate I → Gate III rebased) | Macro plan conversation | `OPUS_PLANNING_SESSION_v2_0.md §9` |
| SESSION_LOG.md entry on main for the Gate III code mutation | Macro plan conversation, post-merge | `00_ARCHITECTURE/SESSION_LOG.md` |
| CURRENT_STATE_v1_0.md update reflecting Gate III merge | Macro plan conversation, post-merge | `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` |

### 7.2 — Deferred to Gate IV (M5 Launchpad)

| Item | Specification | Rationale for deferral |
|---|---|---|
| `/consume` top-level shortcut route | `app/consume/page.tsx` resolves user's most-recently-active chart and `redirect(`/clients/${chartId}/consume`)`; pattern mirrors existing `app/build/page.tsx` `permanentRedirect('/cockpit')` | Native asked for cleaner URL during Gate III planning conversation. Touches the nav rail (Gate IV's W1 territory) and adds a Consume entry to NAV_ITEMS — naturally pairs with the existing Gate IV nav-additions work |
| Nav item: `Consume → /consume` for all three roles | Add to `AppShellRail.tsx` and `MobileNavSheet.tsx` NAV_ITEMS | Same — Gate IV W1 already touches the nav |

To be authored as **Gate IV W1b** when the macro plan conversation authors the Gate IV brief.

### 7.3 — Already resolved by smoke (no carry-forward)

- Golden-set count discrepancy → RESOLVED (smoke fix #1)
- Gemini closing-tag emission reliability → RESOLVED (smoke fix #2)
- Out-of-domain marker parsing → RESOLVED (smoke fix #3)
- Test infrastructure call signature → RESOLVED (smoke fix #4)

---

## §8 — What This Closure Does NOT Cover

To avoid claiming more than this conversation accomplished:

- **No merge has happened.** Branch `feature/gate3-intelligent-chat` is at `a8a6029` and remains unmerged. This artifact records the design-through-smoke arc; merge is the macro plan conversation's responsibility.
- **No `SESSION_LOG.md` entry on `main`.** The Gate III code change isn't on `main` yet; a SESSION_LOG entry now would claim governance changes not visible on `main`. The merge-time entry on `main` will be authored by the macro plan conversation post-merge per `OPUS_PLANNING_SESSION_v2_0.md §8`.
- **No `CURRENT_STATE_v1_0.md` advancement.** Same reason — premature until merge.
- **No Gate IV brief.** Gate IV is authored after the three-way merge is verified.

---

## §9 — Closure Sign-off

| Field | Value |
|---|---|
| Gate ID | GATE-III-INTELLIGENT-CHAT |
| Brief | `CLAUDECODE_BRIEF_GATE_III_v1_0.md` (status: COMPLETE) |
| Branch | `feature/gate3-intelligent-chat` |
| Initial ship | `991bcab` (overnight executor) |
| Smoke close | `a8a6029` (10/10 automated ACs PASS, 4 fixes) |
| Worktree | `/Users/Dev/Vibe-Coding/Apps/marsys-gate3-smart-chat` |
| ACs verified | 25/25 at the verifiable layer (visual walkthrough pending; not blocking closure) |
| Tests | 37/37 new Gate III + all existing pass; `tsc` 22/22 (baseline); lint clean |
| Trace surface | Byte-identical (Gate II isolation preserved) |
| Banned items | None — no anthropic/* models, no new npm packages |
| Memory updated | 3 entries (project_gate_iii_complete, project_golden_set_count_discrepancy → RESOLVED, feedback_gemini_open_only_tags NEW) |
| Open items | Visual walkthrough (native), merge (macro plan), Gate IV W1b /consume shortcut (Gate IV brief) |
| Closure date | 2026-05-13 |
| Closure authored by | Claude Opus 4.7 (Gate III Cowork conversation) |

**Status:** CLOSED at the design + execution + smoke layer. Awaiting native visual walkthrough + sibling-gate completion + three-way merge for full lifecycle close.

---

*End of GATE_III_CLOSURE_v1_0.md*
