---
artifact: STATUS_AT_SETUP_CLOSE
status: GOVERNANCE_RECORD
authored: 2026-05-20
session: chat-v2/governance-r7-r9-setup
branch_merged_to: main
---

# Chat V2 R7–R9 Elevation — Setup Close Status

## What Was Done

The governance branch `chat-v2/governance-r7-r9-setup` was authored, merged to main, and three worktrees were created. All governance artifacts are now on `main`.

### Artifacts authored (all at `00_ARCHITECTURE/chat_v2_briefs/`)

#### Round 7 — Polish (`round7/`)
| File | Content |
|---|---|
| `R7_MASTER_PLAN_v1_0.md` | Master plan: scope, session table, flags, files locked, acceptance, merge position |
| `session_queue.yaml` | 7 sessions with acceptance checks + commit templates |
| `R7-S1-citation-double-wrap-fix.md` | Fix preprocessCitations negative-lookbehind + export + unit tests |
| `R7-S2-footnote-citations.md` | GFM `[^N]` footnote format in synthesis prompt + MarkdownContent component (R6.2) |
| `R7-S3-enrich-citations.md` | Server-side snippet + layer enrichment via fetchMsrSnippets (R6.3) |
| `R7-S4-citation-panel-default-open.md` | CitationSidePanel auto-opens post-stream; pin becomes highlight |
| `R7-S5-auto-continue-on-truncation.md` | Continue button + `/api/chat/consume/continue` route |
| `R7-S6-composer-draft-persistence.md` | `useDraft` hook + debounced localStorage persistence in Composer |
| `R7-S7-a11y-polish.md` | aria-live stream-end + skip link + j/k nav + action keybinds |

#### Round 8 — Capabilities (`round8/`)
| File | Content |
|---|---|
| `R8_MASTER_PLAN_v1_0.md` | Master plan: 8 sessions, DB migrations, flags, merge position 2 |
| `session_queue.yaml` | 8 sessions with acceptance checks + commit templates |
| `R8-S1-branches-persistence.md` | `conversation_branches` table + GET/POST API + useBranches server mirror |
| `R8-S2-branch-picker-ui.md` | BranchPicker `‹ N/M ›` component on edited messages |
| `R8-S3-sidebar-fts-search.md` | `pg_trgm` index + search API + sidebar body-search expansion |
| `R8-S4-pin-archive-folders.md` | Pin/archive columns + folder tables + sidebar grouping |
| `R8-S5-token-estimate-composer.md` | gpt-tokenizer (lazy) + live token count + amber/red thresholds |
| `R8-S6-slash-command-menu.md` | SlashCommandMenu + shared lib/chat-commands.ts + Composer wiring |
| `R8-S7-vision-pipeline.md` | GeminiVisionAdapter + image routing through synthesis LLM |
| `R8-S8-pdf-md-export.md` | `/api/conversations/[id]/export` + ExportDropdown in ChatShell |

#### Round 9 — Elevation (`round9/`)
| File | Content |
|---|---|
| `R9_MASTER_PLAN_v1_0.md` | Master plan: 4 sessions, heavy schema, pgvector prereq, rollback plan |
| `session_queue.yaml` | 4 sessions with acceptance checks + operator prerequisites |
| `R9-S1-projects-abstraction.md` | `projects` + `project_files` + `project_conversations` tables + full API + sidebar |
| `R9-S2-semantic-conversation-search.md` | `conversation_message_embeddings` (vector) + hybrid trgm+cosine search |
| `R9-S3-persona-library.md` | `personas` table + CRUD API + ModelStylePicker group + settings page |
| `R9-S4-inline-tool-flow-timeline.md` | InlineToolFlow disclosure in AssistantMessage (admin only, flagged) |

#### Top-level governance
| File | Content |
|---|---|
| `MERGE_TRAIN_ORDER_v1_0.md` | Full rebase commands, conflict-resolution guidance, flag namespace ownership |

#### CLAUDE.md
- §E updated: "Four workstreams" → "Seven workstreams"
- R7, R8, R9 entries added with canonical_id, branch, worktree, status ACTIVE, brief path, kick-off date

### Worktrees created
| Stream | Branch | Worktree path |
|---|---|---|
| R7 | `chat-v2/round7-polish` | `/Users/Dev/Vibe-Coding/Apps/MadhavR7` |
| R8 | `chat-v2/round8-capabilities` | `/Users/Dev/Vibe-Coding/Apps/MadhavR8` |
| R9 | `chat-v2/round9-elevation` | `/Users/Dev/Vibe-Coding/Apps/MadhavR9` |

All three branches pushed to `origin`.

---

## What Each Stream Needs to Do Next

### R7 — Polish (start here, lowest risk)
1. Open worktree: `cd /Users/Dev/Vibe-Coding/Apps/MadhavR7`
2. Read `00_ARCHITECTURE/chat_v2_briefs/round7/R7_MASTER_PLAN_v1_0.md` and `round7/session_queue.yaml`
3. Execute sessions in order: **R7-S1 → R7-S2 → R7-S3 → R7-S4** (citation chain), then **R7-S5, R7-S6, R7-S7** in any order
4. Each session: read brief → implement → run acceptance check → commit
5. When all 7 sessions pass: open PR to `main`, run `--no-ff` merge

### R8 — Capabilities (parallel with R7, merges after R7)
1. Open worktree: `cd /Users/Dev/Vibe-Coding/Apps/MadhavR8`
2. Read `R8_MASTER_PLAN_v1_0.md` and `round8/session_queue.yaml`
3. Execute migrations-first: **R8-S1, R8-S3, R8-S4** (schema changes), then **R8-S2** (depends on S1), then **R8-S5, R8-S6, R8-S7, R8-S8** independently
4. Rebase on main after R7 merges, before opening R8 PR

### R9 — Elevation (parallel with R7/R8, merges last)
1. Open worktree: `cd /Users/Dev/Vibe-Coding/Apps/MadhavR9`
2. Read `R9_MASTER_PLAN_v1_0.md` and `round9/session_queue.yaml`
3. **Operator gate before R9-S2:** verify `pgvector` extension in production Postgres
4. Execute: **R9-S1, R9-S3, R9-S4** independently; **R9-S2** only after R8-S3 is merged
5. Rebase on main after R7+R8 merge; resolve `search/route.ts` conflict per MERGE_TRAIN_ORDER guidance

---

## Kick-off Prompts

Paste one of the following into the appropriate Claude Code session (in the corresponding worktree) to begin execution:

### R7 Kick-off
```
You are executing the Chat V2 R7 Polish Round in the worktree at /Users/Dev/Vibe-Coding/Apps/MadhavR7 on branch chat-v2/round7-polish.

Read the master plan and session queue:
  00_ARCHITECTURE/chat_v2_briefs/round7/R7_MASTER_PLAN_v1_0.md
  00_ARCHITECTURE/chat_v2_briefs/round7/session_queue.yaml

Then execute R7-S1 (R7-S1-citation-double-wrap-fix.md) per the brief. Run all pre-commit gates. Commit with the template in the brief. Then proceed to R7-S2. Continue autonomously through R7-S4, then execute R7-S5 through R7-S7. When all 7 sessions are committed, report the summary.
```

### R8 Kick-off
```
You are executing the Chat V2 R8 Capabilities Round in the worktree at /Users/Dev/Vibe-Coding/Apps/MadhavR8 on branch chat-v2/round8-capabilities.

Read the master plan and session queue:
  00_ARCHITECTURE/chat_v2_briefs/round8/R8_MASTER_PLAN_v1_0.md
  00_ARCHITECTURE/chat_v2_briefs/round8/session_queue.yaml

Execute R8-S1 first (schema migration + useBranches server mirror). Then R8-S3 (pg_trgm FTS). Then R8-S4 (pin/archive/folders). Then R8-S2 (depends on S1). Then R8-S5 through R8-S8 in any order. Run acceptance checks per session queue. Commit per templates. Report when all 8 sessions are committed.
```

### R9 Kick-off
```
You are executing the Chat V2 R9 Elevation Round in the worktree at /Users/Dev/Vibe-Coding/Apps/MadhavR9 on branch chat-v2/round9-elevation.

IMPORTANT: Do NOT execute R9-S2 (semantic search) until R8-S3 (pg_trgm) has been merged to main and you have rebased.
IMPORTANT: Verify pgvector extension is installed in production Postgres before running the R9-S2 migration.

Read the master plan and session queue:
  00_ARCHITECTURE/chat_v2_briefs/round9/R9_MASTER_PLAN_v1_0.md
  00_ARCHITECTURE/chat_v2_briefs/round9/session_queue.yaml

Execute R9-S1 (projects abstraction), then R9-S3 (persona library), then R9-S4 (inline tool flow). Hold R9-S2 until R8-S3 is confirmed merged. Report when sessions are committed.
```

---

## Merge Train Order Summary

```
main ──[R7 merge]──[R8 rebase+merge]──[R9 rebase+merge]──► final state
```

1. **R7 PR** — no rebase needed (started from same main); merge immediately after all 7 sessions pass gates
2. **R8 PR** — `git rebase origin/main` from MadhavR8 after R7 merges; conflict in `Composer.tsx` (take R7's changes as base, layer R8-S5 on top) and `feature_flags.ts` (append R8 flags, keep R7 flags)
3. **R9 PR** — `git rebase origin/main` from MadhavR9 after R7+R8 merge; conflict in `search/route.ts` (keep R8-S3 trgm handler, add R9-S2 semantic branch)

Full commands and conflict-resolution guidance: `00_ARCHITECTURE/chat_v2_briefs/MERGE_TRAIN_ORDER_v1_0.md`

---

## BLOCKERS

None at setup close. All governance artifacts authored and committed. Worktrees created and branches pushed.

**Operator actions required before execution begins:**
- [ ] Provision `SMOKE_SESSION_COOKIE` + `SMOKE_CHART_ID` GitHub Actions secrets (documented in R7-S1 brief §Pre-commit gates)
- [ ] Verify `pgvector` extension installed in production Postgres (required before R9-S2 migration)

---
*STATUS_AT_SETUP_CLOSE.md — authored 2026-05-20 at governance setup branch close.*
