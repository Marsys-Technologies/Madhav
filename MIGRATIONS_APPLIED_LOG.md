---
artifact: MIGRATIONS_APPLIED_LOG.md
version: "1.0"
status: CURRENT
produced_during: R9_Operator_Closeout
produced_on: 2026-05-20
executor: Claude Code (autonomous, native-authorized)
---

# R9 Migrations Applied to Production

**Applied:** 2026-05-20 ~04:18 IST  
**Environment:** Cloud SQL `madhav-astrology:asia-south1:amjis-postgres` / DB `amjis`  
**Applied by:** Claude Code (operator close-out session)

---

## Migration 110 — Projects Abstraction

**File:** `platform/migrations/110_add_projects_abstraction.sql`  
**Status:** APPLIED ✓  
**Bug fixed:** `project_conversations.conversation_id` declared as `TEXT` in migration but `conversations.id` is `UUID` in production schema. Fixed to `UUID` before apply. Fix committed to migration file.  
**Tables created:**
- `projects` (id, user_id, name, system_prompt_addition, chart_id, deleted_at, created_at, updated_at)
- `project_files` (id, project_id→projects, storage_path, filename, mime_type, created_at)
- `project_conversations` (project_id→projects, conversation_id→conversations, composite PK)

**Indexes created:**
- `idx_project_conv_project` on project_conversations(project_id)
- `idx_project_conv_conv` on project_conversations(conversation_id)

---

## Migration 111 — Personas

**File:** `platform/migrations/111_add_personas.sql`  
**Status:** APPLIED ✓  
**Tables created:**
- `personas` (id, user_id, name, system_prompt, default_style, default_stack, is_default, created_at, updated_at)

**Indexes created:**
- `idx_personas_user_id` on personas(user_id)
- `idx_personas_user_default` UNIQUE partial on personas(user_id) WHERE is_default = TRUE

---

## Migration 112 — Conversation Message Embeddings (pgvector)

**File:** `platform/migrations/112_add_conversation_message_embeddings.sql`  
**Status:** APPLIED ✓  
**Bug fixed:** `message_id TEXT` declared but `conversation_messages.id` is `UUID`. Fixed to `UUID` before apply. Fix committed to migration file.  
**pgvector version:** 0.8.1 (pre-installed in Cloud SQL instance) ✓  
**Tables created:**
- `conversation_message_embeddings` (message_id UUID→conversation_messages, embedding vector(768), created_at)

**Indexes created:**
- `idx_cme_embedding` using ivfflat (embedding vector_cosine_ops) WITH (lists=100)
  - Note: ivfflat created with empty table — low recall warning expected and documented; recall improves as backfill populates the table.

---

## Post-apply verification

All 5 target tables confirmed present:
- `conversation_message_embeddings` ✓
- `personas` ✓
- `project_conversations` ✓
- `project_files` ✓
- `projects` ✓

Vector column type: `vector` (pgvector native type, 768 dimensions) ✓
