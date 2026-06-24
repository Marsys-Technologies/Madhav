---
artifact: BACKFILL_SCRIPT_NOT_FOUND.md
version: "2.0"
status: RESOLVED
produced_during: R9_Operator_Closeout
produced_on: 2026-05-20
resolved_on: 2026-05-20
executor: Claude Code (autonomous, native-authorized)
---

# Phase 7 RESOLVED — Backfill Complete

## Resolution (2026-05-20)

Script `platform/scripts/backfill_conversation_embeddings.ts` was found at the expected path and
executed successfully. See BACKFILL_RUN_REPORT.md for full run details.

**Results: 73/73 messages embedded, 0 errors, 0 remaining.**

A bug in the script was fixed before running: the SQL queries referenced `cm.content` but the
production schema uses `parts_json` (JSONB). Fixed to use `jsonb_array_elements(cm.parts_json)`
matching the pattern in the live semantic search route.

---

# Original HALTED Record (2026-05-20, superseded)

# Phase 7 HALTED — Backfill Script Not Found

## Status

Phase 7 (historical embedding backfill) halted per hard-halt condition:
> "If still absent, HALT with BACKFILL_SCRIPT_NOT_FOUND.md and note that
> R9_SEMANTIC_SEARCH historical coverage is incomplete."

## What was searched

- `platform/scripts/backfill_conversation_embeddings.ts` — not present
- `platform/scripts/backfill_*` — no matches
- `platform/scripts/*embed*` — no matches
- Full `find` across `platform/` (excluding node_modules/.next) — no backfill script found

## Impact

- `MARSYS_FLAG_R9_SEMANTIC_SEARCH=true` — **flipped and running** (Phase 5 COMPLETE)
- New messages written after Phase 5 flip **will** produce embeddings (live pipeline active)
- Historical messages in `conversation_messages` **will not** have embeddings until backfill runs
- Semantic search results will be sparse until backfill is executed
- trgm (trigram) fallback path still works; semantic ranking (cosine) is degraded for historical content

## What the backfill script needs to do

The script was described in the R9-S2 brief. It should:
1. Query `conversation_messages` for rows with non-empty body NOT already in `conversation_message_embeddings`
2. For each message, call `embedText(message.body)` (Vertex AI text-multilingual-embedding-002, 768 dims)
3. Insert `(message_id, embedding)` into `conversation_message_embeddings`
4. Batch 100 messages per iteration
5. Be idempotent (skip already-embedded messages)

Relevant existing code:
- `platform/src/lib/embedText.ts` — Vertex AI embedding call (768 dims, ADC auth)
- `platform/src/lib/conversation_writer.ts` → `embedConversationMessage()` — the live post-write hook added in R9-S2

## Resolution

Author `platform/scripts/backfill_conversation_embeddings.ts` using `embedConversationMessage`
logic as the template. Run via `DATABASE_URL=... npx tsx platform/scripts/backfill_conversation_embeddings.ts`.

Phase 8 seal proceeds — this gap is documented there.
