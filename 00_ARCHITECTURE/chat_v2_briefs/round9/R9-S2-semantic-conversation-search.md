---
canonical_id: CHAT_V2_R9_S2_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
round: R9
session_id: R9-S2
owner: chat-v2/round9-elevation worktree
branch: chat-v2/round9-elevation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR9
flag_namespace: MARSYS_FLAG_R9_SEMANTIC_SEARCH
authored: 2026-05-20
depends_on: [R8-S3]
---

## Context

R9-S2 adds semantic search over conversation messages. The project already has a corpus-chunk embedder (in `platform/src/lib/embeddings/`) and `pg_trgm`-based conversation search shipped in R8-S3. This session layers cosine-similarity search on top of the existing trigram search, combining both signals into a hybrid ranked result set. A sidebar toggle keeps the default experience fast (trgm-only) while letting the user opt into semantic mode.

Depends on R8-S3 being merged: `conversation_messages` table exists, `platform/src/app/api/conversations/search/route.ts` exists and returns trgm results, sidebar search bar UI exists.

## Files in scope

**New files:**
- `platform/src/lib/embeddings/embedConversationMessage.ts` — embeds a single conversation message using the shared `embedText()` function; exported as `embedConversationMessage(messageId: string, text: string): Promise<void>` which writes to `conversation_message_embeddings`
- `platform/drizzle/migrations/<timestamp>_conversation_message_embeddings.sql` — migration that creates the `conversation_message_embeddings` table and `idx_cme_embedding` ivfflat index (exact SQL below in Acceptance criteria)

**Modified files:**
- `platform/src/app/api/conversations/search/route.ts` — add `?semantic=true` param, embed query, run cosine query, merge with trgm results, apply hybrid scoring
- `platform/src/lib/db/schema.ts` (or equivalent Drizzle schema file) — add `conversationMessageEmbeddings` table definition
- Message save path (locate the function/route that inserts into `conversation_messages` — likely `platform/src/app/api/conversations/[id]/messages/route.ts` or a service layer) — add non-blocking after-insert call to `embedConversationMessage`
- Sidebar search bar component (locate from R8-S3 implementation — likely `platform/src/components/consume/ConversationSidebar.tsx` or similar) — add semantic toggle icon button; controlled by local state; appends `&semantic=true` to search fetch URL when active; default OFF

## Files must not touch

- `platform/src/lib/embeddings/embedText.ts` (or whichever file exports `embedText`) — reuse as-is; no modifications
- Any corpus-chunk embedding pipeline files — this session touches only conversation message embedding
- `01_FACTS_LAYER/**`
- `025_HOLISTIC_SYNTHESIS/**`
- `00_ARCHITECTURE/**` (except this brief itself, already written)
- `.geminirules`
- `.gemini/project_state.md`
- `platform/src/components/consume/ConsumeChatV2.tsx` — currently modified on main; do not touch unless the message save path runs through it (in which case add only the non-blocking embed call and nothing else)
- Any file outside the `platform/` directory tree (except governance artifacts)

## Acceptance criteria

**AC-1 — Migration:** Running `pnpm drizzle-kit migrate` (or equivalent) applies the following DDL without error:
```sql
CREATE TABLE conversation_message_embeddings (
  message_id TEXT PRIMARY KEY REFERENCES conversation_messages(id) ON DELETE CASCADE,
  embedding vector(1536),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_cme_embedding ON conversation_message_embeddings
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```
The vector dimension (1536) must match the output dimension of the existing `embedText()` function; if the existing embedder uses a different dimension, adjust to match and document the change in this file's changelog.

**AC-2 — Embedding pipeline:** After a new message is saved to `conversation_messages`, `embedConversationMessage` is called non-blocking (via `setImmediate`, `Promise.resolve().then(...)`, or equivalent). The embedding row appears in `conversation_message_embeddings` within 5 seconds under normal conditions. Failure to embed (e.g. embedding API timeout) is caught, logged to `console.error`, and does not throw or reject the message save response.

**AC-3 — Semantic search query:** `GET /api/conversations/search?q=moon&semantic=true` returns conversations whose messages are semantically related to "moon" even when the word "moon" does not appear verbatim — e.g. conversations containing "Chandra", "Chandrama", or "lunar". Verified manually against a seeded test conversation.

**AC-4 — Hybrid scoring:** When `semantic=true`, the route:
1. Embeds the query string via `embedText()`.
2. Runs: `SELECT message_id, conversation_id, 1 - (embedding <=> $1) AS cosine_score FROM conversation_message_embeddings ORDER BY embedding <=> $1 LIMIT 50` (parameterised).
3. Filters to rows where `conversation_id` belongs to the authenticated user.
4. Separately runs the existing pg_trgm query from R8-S3 for the same `q` string.
5. Merges results (UNION DISTINCT on `conversation_id`).
6. Applies boost: cosine_score ≥ 0.78 → +2; trgm similarity ≥ 0.3 → +1; combined score used for final sort descending.
7. Returns ranked array of `{ conversationId, title, snippet, score }`.

**AC-5 — Graceful degradation:** If `embedText()` throws (network error, rate limit, etc.) inside the search route, the route falls back to trgm-only results and returns them with a response header `X-Search-Mode: trgm-fallback`. No 500 is returned to the client.

**AC-6 — Semantic toggle UI:** The sidebar search bar renders a small icon button (e.g. a sparkle or wand icon from the existing icon library) to the right of the search input. Default state: OFF (icon dimmed). Clicking toggles ON (icon highlighted). When ON, search fetches append `&semantic=true`. When OFF, behavior is identical to pre-R9-S2 (trgm only). Toggle state resets to OFF on sidebar close/unmount.

**AC-7 — Default path unchanged:** `GET /api/conversations/search?q=foo` (no `semantic` param, or `semantic=false`) returns results from the trgm path only — no embedding call is made, latency is unchanged from R8-S3 baseline.

**AC-8 — TypeScript clean:** `pnpm tsc --noEmit` exits 0. No `any` casts introduced in new files.

**AC-9 — Flag namespace:** The semantic search feature is gated by `MARSYS_FLAG_R9_SEMANTIC_SEARCH`. When the flag is false/absent: the semantic toggle is hidden in the UI; the `?semantic=true` param is ignored server-side (treated as false). Flag check uses the existing `feature_flags.ts` pattern.

## Pre-commit gates

Run all of the following and confirm exit 0 before committing:

```bash
# 1. TypeScript
pnpm --filter platform tsc --noEmit

# 2. Lint
pnpm --filter platform lint

# 3. Migration dry-run (no DB required — just schema validation)
pnpm --filter platform drizzle-kit check

# 4. Unit test (if a test file is added for embedConversationMessage)
pnpm --filter platform test --testPathPattern embedConversationMessage

# 5. Verify embedText import resolves without modification
grep -r "embedText" platform/src/lib/embeddings/ --include="*.ts" -l
```

If gate 3 is not available in the local toolchain, substitute a manual review of the generated migration SQL against AC-1 DDL.

## Commit message template

```
feat(search): R9-S2 semantic conversation search with hybrid trgm+cosine scoring

- Add conversation_message_embeddings table (vector(1536), ivfflat index)
- embedConversationMessage.ts: non-blocking after-insert embedding via shared embedText()
- /api/conversations/search: ?semantic=true param triggers cosine query + hybrid rank
- Hybrid boost: cosine>=0.78 +2, trgm>=0.3 +1; UNION DISTINCT merge
- Graceful fallback to trgm-only on embedding API failure (X-Search-Mode header)
- Sidebar semantic toggle (OFF by default); gated by MARSYS_FLAG_R9_SEMANTIC_SEARCH

Depends-on: R8-S3
Flag: MARSYS_FLAG_R9_SEMANTIC_SEARCH
```
