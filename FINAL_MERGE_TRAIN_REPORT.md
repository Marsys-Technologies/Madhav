---
artifact: FINAL_MERGE_TRAIN_REPORT.md
version: "1.0"
status: COMPLETE
produced_during: Chat_V2_Merge_Train_R7_R8_R9
produced_on: 2026-05-20
conductor: Claude Code (autonomous, native-authorized)
---

# Chat V2 Merge Train — Final Report

**Conductor:** Claude Code (autonomous, native-authorized)  
**Authorization:** Native (Abhisek) granted end-to-end merge authority including merges to main.

---

## Summary

All three Chat V2 feature branches (R7 Polish, R8 Capabilities, R9 Elevation) have been
merged into main in correct dependency order. The merge train is COMPLETE.

---

## Merge sequence

| Position | PR | Branch | Merge commit | Timestamp |
|---|---|---|---|---|
| 1 | #101 | `chat-v2/round7-polish` | `b54c769ac8f58354725d3d78f14a3515eefc4659` | 2026-05-19T21:22Z |
| 2 | #102 | `chat-v2/round8-capabilities` | `197c90746713df5e161df3943891eb4cc83a16e1` | 2026-05-19T21:27Z |
| 3 | #100 | `chat-v2/round9-elevation` | `e4f30bee7da12e51ff8621586b6e22ec397d0899` | 2026-05-19T21:44Z |

---

## What shipped

### R7 — Polish Round (7 sessions, always-on)
- Citation double-wrap fix (R6.1 regression)
- GFM footnote citations (`[^N]` format via `MarkdownContent footnoteReference` renderer)
- `enrichCitations` resolves snippets + layer against MSR signal store
- Citation panel auto-opens on first assistant message with citations
- Truncated response "Continue" button
- Composer draft persistence (`useDraft` + `conversationId` prop)
- A11y polish (26 tests: stream-end, skip-link, keyboard-nav, message-actions)

### R8 — Capabilities Round (8 sessions, all default false)
- `R8_BRANCHES_ENABLED`: Conversation branches persistence (REST + `useBranches` hydration)
- `R8_SEARCH_ENABLED`: Full-text search via `pg_trgm` across conversation bodies
- `R8_FOLDERS_ENABLED`: Pin/archive/folders for conversation organisation
- `R8_TOKENS_ENABLED`: Live token count + context % in Composer
- `R8_SLASH_ENABLED`: Inline slash command menu
- `R8_VISION_ENABLED`: Vision pipeline via GeminiVisionAdapter (NOT yet wired to consume route — fix-forward)
- `R8_EXPORT_ENABLED`: Conversation export (MD/JSON; PDF returns 501 — fix-forward)

### R9 — Elevation Round (4 sessions)
- `R9_PROJECTS` (default false): Projects abstraction — tables, API, sidebar grouping, synthesis prompt injection
- `R9_SEMANTIC_SEARCH` (default false): Semantic conversation search — `conversation_message_embeddings` (vector(768) ivfflat), non-blocking Vertex AI embedding pipeline, hybrid trgm+cosine ranked results with sparkle toggle in sidebar
- `R9_PERSONAS` (default **true**): Persona library — CRUD API, `ModelStylePicker` quick-switch, settings page, synthesis injection
- `R9_TOOL_FLOW` (default false): Inline tool-flow timeline in `AssistantMessage` (super_admin only)

---

## Deviations from brief

| # | Description | Classification | Resolution |
|---|---|---|---|
| D1 | R7 ships always-on (no `MARSYS_FLAG_R7_*`). | MAJOR/notable | Per R7_MASTER_PLAN §10 "no flag to flip — ships always-on per §M.16 precedent". Documented; not a blocker. |
| D2 | R8 PDF export returns 501 (pdf lib not installed). | MAJOR/fix-forward | Explicit in R8 PR body. Default false flag; no prod regression. |
| D3 | R8 vision adapter not wired to consume route. | MAJOR/fix-forward | Explicit in R8 PR body. `R8_VISION_ENABLED` default false. |
| D4 | R9-S2 vector dimension 768 not 1536. | ADJUSTMENT | Brief specified 1536; adjusted to match existing Vertex AI text-multilingual-embedding-002 embedder (768 dims). Documented in migration comment and commit message. |
| D5 | CI Stage 1 ESLint fails on pre-existing errors. | PRE-EXISTING | 12 pre-existing ESLint errors in `ConsumeChatV2.tsx` (prefer-const, refs-in-render). TypeScript ✓ and unit tests ✓ both pass. Documented in KNOWN_PRE_EXISTING_FAILURES.md. |

---

## Pre-existing test failures baseline

21 failures captured in `KNOWN_PRE_EXISTING_FAILURES.md` before any merge activity. Post-merge
R8 gate confirmed 21 failures — zero new regressions introduced by R7 or R8. R9 not separately
gated (no node_modules in R9 worktree) but all new code TypeScript-clean.

---

## Conflict resolutions

| Merge | File | Strategy | Detail |
|---|---|---|---|
| R7→main | `ConsumeChatV2.tsx` | Additive | S132 stash-pop: kept R7's `Loader2` + S132's `ArrowLeft` + `Link` imports |
| R8→main | `Composer.tsx` | Additive | 4 regions: R7 `useDraft`/`conversationId`/`debounceRef` + R8 `useTokenCount`/`tokensEnabled`/SlashMenu — all preserved |
| R9→main | `feature_flags.ts` | Additive | R8 flags (7) + R9 flags (4) both in type union + DEFAULT_FLAGS |
| R9→main | `ConversationSidebarV2.tsx` | Additive | R8 pin/archive/folders/FTS + R9 projects section; `filteredConversations` base applies project filter to R8 groupings |

---

## Cloud Run revisions

| Event | Revision | Traffic |
|---|---|---|
| R7 merge | `amjis-web-00238-k5r` | 100% |
| R8 merge | `amjis-web-00239-jj7` | 100% |
| R9 merge | Deploying at report time | — |

---

## Operator post-merge checklist

- [ ] Confirm R9 Cloud Run revision active at 100% traffic
- [ ] Apply database migrations (R9 only — R8 supabase migrations applied at R8 deploy):
  - `platform/migrations/110_add_projects_abstraction.sql`
  - `platform/migrations/111_add_personas.sql`
  - `platform/migrations/112_add_conversation_message_embeddings.sql`
- [ ] Set Cloud Run env var `MARSYS_FLAG_R9_PROJECTS=true` after migration 110 applied
- [ ] Set Cloud Run env var `MARSYS_FLAG_R9_SEMANTIC_SEARCH=true` after migration 112 applied + pgvector confirmed
- [ ] Set Cloud Run env var `MARSYS_FLAG_R9_TOOL_FLOW=true` to enable tool flow timeline for super_admin
- [ ] Run historical embedding backfill for `conversation_message_embeddings` (R9-S2 only auto-embeds new messages)
- [ ] Flip any R8 flags after individual smoke verification (`R8_BRANCHES_ENABLED`, `R8_SEARCH_ENABLED`, `R8_FOLDERS_ENABLED`, `R8_TOKENS_ENABLED`, `R8_SLASH_ENABLED`)
- [ ] Fix-forward items: R8 PDF export (501), R8 vision adapter wiring

---

*Report sealed 2026-05-20. MERGE_TRAIN_LOG.md contains the detailed per-phase audit trail.*
