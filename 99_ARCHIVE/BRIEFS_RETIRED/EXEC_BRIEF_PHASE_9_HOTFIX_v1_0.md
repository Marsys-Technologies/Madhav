---
artifact: EXEC_BRIEF_PHASE_9_HOTFIX_v1_0.md
status: COMPLETE
completed_on: 2026-04-28
authored_by: Cowork (Claude Opus 4.7)
authored_on: 2026-04-27
executor_target: Claude Code (Anti-Gravity / VS Code extension; NOT the CLI)
trigger_phrase: "Read EXEC_BRIEF_PHASE_9_HOTFIX_v1_0.md and execute it."
phase_number: 9-hotfix
phase_name: Phase 9 Vector Search Embedding Provider Correction
purpose: |
  HOTFIX. Phase 9's Stream C delivered platform/src/lib/retrieve/vector_search.ts
  using Voyage-3-large embeddings via the Voyage AI HTTP API. The actual rag_embeddings
  table is populated with 977 rows of Vertex AI text-multilingual-embedding-002 at
  768-dim (verified by SQL on 2026-04-27 — column declared vector(768), all rows
  768-dim). Voyage produces 1024-dim vectors; pgvector would reject the cosine query
  with a dimension mismatch, and the tool would silently return empty via its graceful
  degradation path. This brief replaces the Voyage call with a Vertex AI call using
  Application Default Credentials (matching embed.py's pattern), updates the test
  mocks from 1024-dim to 768-dim, and adds a documentary migration 010 recording
  the schema state. Single sub-stream; ~30 minutes of Sonnet work.
verified_db_state_2026-04-27:
  - "rag_embeddings.embedding column declared vector(768)"
  - "977 rows, all 768-dim, no mixed-dimension data, no orphan rows"
  - "Schema is consistent with Vertex AI text-multilingual-embedding-002"
depends_on:
  - 00_ARCHITECTURE/MARSYS_JIS_ARCHITECTURE_v1_0.md (APPROVED 2026-04-27 — §17 Migration from Current State references Vertex AI text-multilingual-embedding-002 as the embedding model; this is correct)
  - 00_ARCHITECTURE/MARSYS_JIS_PROJECT_PLAN_v1_0.md
  - EXEC_BRIEF_PHASE_9_v1_0.md (COMPLETE — its Stream C delivered the file being corrected)
  - platform/python-sidecar/rag/embed.py (READ-ONLY reference — source of truth for Vertex AI auth pattern; uses google-auth-library with Application Default Credentials)
  - CLAUDE.md
parallel_stream_tolerance: |
  This hotfix is purely additive/corrective in scope. It modifies platform/src/lib/retrieve/vector_search.ts
  and its test file plus adds one documentary migration. M2/B.5 may run freely in parallel.
  Phase 3 (currently IN_PROGRESS) does NOT touch vector_search.ts; no collision. The hotfix
  can run alongside Phase 3 in a third Claude Code session.
risk_classification: LOW. Surgical fix to one file; well-defined contract change (1024 → 768
  + Voyage → Vertex AI); existing tests updated to match new dim; functional verification
  via real DB query post-fix is the primary acceptance.
status_history:
  - timestamp: 2026-04-28
    from: AUTHORED
    to: IN_PROGRESS
    note: "Claude Code (Sonnet 4.6, Anti-Gravity session) began execution. Pre-flight confirmed: vector_search.ts already at v1.1.0 with Vertex AI implementation (static GoogleAuth import, 768-dim, RETRIEVAL_QUERY, direct fetch with ADC token). Migration 010 already present. Test file already had 768-dim mock. Root issue identified: vitest 4.x breaking change — vi.fn().mockImplementation(() => ({...})) with arrow function is no longer a valid constructor, silently returning warning bundle instead of success."
  - timestamp: 2026-04-28
    from: IN_PROGRESS
    to: COMPLETE
    note: |
      Two surgical changes made:
      (1) vector_search.ts — confirmed static `import { GoogleAuth } from 'google-auth-library'` at top of file; removed stale dynamic `await import()` inside getQueryEmbedding (~2 lines changed).
      (2) vector_search.test.ts — fixed GoogleAuth mockImplementation from arrow function `() => ({...})` to regular function `function() { return {...} }` (vitest 4.x breaking change: arrow functions are not valid constructors in vi.fn().mockImplementation()).
      Migration 010 already existed; no changes needed.
      Result: all 22 vector_search tests pass. TypeScript type-check clean. Pre-existing failures (e2e/clients supabase import, parity_validator count, build-tools read_document) confirmed pre-existing — not introduced by hotfix; match Phase 9 status_history note.
      Live DB smoke test: deferred (Cloud SQL Auth Proxy not running locally). Native to run when convenient.
      must_not_touch verified: no python-sidecar, no Phase 3 surfaces, no governance scripts, no other Phase 9 deliverables modified.
---

# EXECUTION BRIEF — Phase 9 Hotfix: Vector Search → Vertex AI

## §0 — Trigger and Execution Model

Native triggers this brief by saying to a Claude Code session: **"Read EXEC_BRIEF_PHASE_9_HOTFIX_v1_0.md and execute it."**

On trigger, Claude Code MUST:
1. Read this entire brief end-to-end.
2. Read the mandatory pre-flight artifacts in §2.
3. Execute the single sub-stream per §5.
4. On completion: integration verification per §7; flip status to `COMPLETE`; notify native.

**Status transitions.** AUTHORED → IN_PROGRESS → COMPLETE.

## §1 — Mission

Replace the Voyage-3-large embedding call in `platform/src/lib/retrieve/vector_search.ts` with a Vertex AI `text-multilingual-embedding-002` call (768-dim) using Application Default Credentials. The DB state is already correct (977 rows at 768-dim, column declared `vector(768)`); only the query-time embedding generation in the TypeScript tool is wrong.

Concretely the hotfix:
- Removes Voyage HTTP call + `VOYAGE_API_URL` + `VOYAGE_MODEL` constants + `VOYAGE_API_KEY` env reference.
- Adds Vertex AI client call with Application Default Credentials, model `text-multilingual-embedding-002`, `task_type: 'RETRIEVAL_QUERY'`, output dimension 768.
- Updates the test file's `MOCK_EMBEDDING = new Array(1024).fill(0.01)` to `new Array(768).fill(0.01)` and updates any other dim-1024 assertions.
- Removes any `.env.example` reference to `VOYAGE_API_KEY` if Phase 9 added one (it should not have been needed since the project uses Google Cloud, but verify).
- Adds `platform/supabase/migrations/010_vertex_ai_embedding_dim.sql` — a documentary migration that records the in-place schema change (uses IF-NOT-EXISTS / idempotent SQL so it's safe to run; doesn't actually change anything because the schema is already correct).

The graceful degradation pattern stays unchanged — if Vertex AI is unavailable or the DB query fails, the tool returns an empty `ToolBundle` rather than throwing.

## §2 — Mandatory Pre-flight Reading

Read in full, in this order. Do not skip.

**§2.1 — Hotfix context:**

1. `EXEC_BRIEF_PHASE_9_v1_0.md` (project root, status COMPLETE) — the brief this hotfix corrects. Read the status_history note for what was delivered.
2. `00_ARCHITECTURE/MARSYS_JIS_ARCHITECTURE_v1_0.md` §17 — confirms Vertex AI as the embedding model. Architecture intent was always correct; the hotfix aligns implementation to it.

**§2.2 — Source-of-truth reference:**

3. `platform/python-sidecar/rag/embed.py` — **READ ONLY** as reference. Note specifically:
   - `EMBED_MODEL = "text-multilingual-embedding-002"`
   - `EMBED_DIM = 768`
   - The Vertex AI client setup (uses Application Default Credentials — no API key)
   - The `task_type` parameter for ingestion (likely `RETRIEVAL_DOCUMENT`)
   - The TypeScript hotfix should use **`RETRIEVAL_QUERY`** (not `RETRIEVAL_DOCUMENT`) because we're embedding a query at retrieval time, not a document at ingest time.
   - DO NOT modify embed.py — it lives in `must_not_touch` Python sidecar territory.

**§2.3 — File being corrected:**

4. `platform/src/lib/retrieve/vector_search.ts` — the file with the Voyage call. Read in full.
5. `platform/src/lib/retrieve/__tests__/vector_search.test.ts` — the test file with the 1024-dim mock. Read in full.

**§2.4 — Vertex AI integration patterns to study:**

6. Search the codebase for any other Vertex AI integration (e.g., grep for `aiplatform`, `vertexai`, `google-auth-library`). If embed.py uses a Python pattern, the TypeScript equivalent is the `@google-cloud/aiplatform` Node.js SDK or direct fetch with ADC token. Pick whichever matches existing TypeScript patterns; if no precedent exists in the TypeScript codebase, prefer the SDK.

After pre-flight, summarize in 3-4 sentences: which embedding model, which auth pattern, which task_type, what dim mocks need to change.

## §3 — Hard Scope Constraints

### `may_touch`

- `platform/src/lib/retrieve/vector_search.ts` — modify the embedding call + dim assumptions.
- `platform/src/lib/retrieve/__tests__/vector_search.test.ts` — update mocks from 1024-dim to 768-dim.
- `platform/supabase/migrations/010_vertex_ai_embedding_dim.sql` — NEW file (documentary).
- `package.json` — if `@google-cloud/aiplatform` (or `google-auth-library`) is not already a dependency, add it. Match the version pattern of existing Google Cloud dependencies if any.
- `.env.example` — only if Phase 9 added a `VOYAGE_API_KEY` entry; if so, remove it. Do NOT add Vertex AI credentials to .env.example — Application Default Credentials use the local auth chain, not env vars.
- `platform/src/lib/config/feature_flags.ts` — only if descriptive comments mentioning Voyage need updating; do not change flag names or defaults.
- This brief itself — for status transitions.

### `must_not_touch`

- `platform/python-sidecar/` — entire Python sidecar including `embed.py`. Read-only reference.
- All Phase 3 surfaces (`platform/src/lib/synthesis/`, `validators/`, `prompts/`, `disclosure/`, `route.ts`).
- All other Phase 9 deliverables (`cgm_graph_walk.ts`, `manifest_query.ts`) — leave as-is.
- All other tools in `platform/src/lib/retrieve/` — leave as-is.
- The Capability Manifest, manifest_overrides.yaml.
- Governance scripts.
- Architecture document, project plan.
- All other Phase 0/1A/1B/2 deliverables.
- The active CLAUDECODE_BRIEF.md (M2/B.5 stream).
- The four superseded predecessor documents.

### Behavioral constraints

- The hotfix produces a vector_search.ts that, when invoked against the live DB, returns expected nearest-neighbor results for a known-good query. This is the primary functional acceptance.
- All existing tests in vector_search.test.ts continue to pass after dim updates.
- Graceful degradation behavior preserved: API failure → empty ToolBundle, no throw.
- The new migration file 010 is idempotent — running it against the current DB has no effect (schema already correct). It exists as documentation for replay reproducibility.

## §4 — Verified DB State (do not re-verify; native verified 2026-04-27)

The pre-flight question on DB state was already answered. As of 2026-04-27 SQL verification:
- `rag_embeddings.embedding` column declared `vector(768)`.
- 977 rows present, all 768-dim, no mixed-dimension data.
- Schema is consistent with Vertex AI `text-multilingual-embedding-002`.

You do NOT need to re-verify. Proceed directly to implementation.

## §5 — The Hotfix (single sub-stream)

**Tasks (in order):**

**1. Update vector_search.ts.**

Remove:
- `VOYAGE_API_URL` constant.
- `VOYAGE_MODEL` constant.
- The `getQueryEmbedding` function's Voyage HTTP call body.
- Any reference to `VOYAGE_API_KEY` env var.

Add:
- Constants for Vertex AI: `VERTEX_EMBED_MODEL = 'text-multilingual-embedding-002'`, `VERTEX_EMBED_DIM = 768`, `VERTEX_TASK_TYPE = 'RETRIEVAL_QUERY'`.
- Vertex AI embedding generation. Two implementation options — pick the one that matches existing project patterns:
  - **(a) `@google-cloud/aiplatform` SDK**: import the PredictionServiceClient, call `predict()` with the publisher model `publishers/google/models/text-multilingual-embedding-002`, pass instances with `content` and `task_type: 'RETRIEVAL_QUERY'`. Authentication via Application Default Credentials happens automatically through the SDK.
  - **(b) Direct fetch**: use `google-auth-library` to obtain an access token via `GoogleAuth.getClient().getAccessToken()`, then POST to `https://us-central1-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/us-central1/publishers/google/models/text-multilingual-embedding-002:predict` with `Authorization: Bearer <token>`.
- Project ID resolution: read `GOOGLE_CLOUD_PROJECT` env var; if not set, attempt `gcloud config get-value project` fallback (probably overkill; the env var should be set in any environment that runs this).
- Preserve the graceful degradation: any error in embedding generation → empty ToolBundle returned with appropriate status field; no throw.

The SQL portion of vector_search.ts (the pgvector cosine query joining `rag_embeddings + rag_chunks`) stays unchanged — it's correct as written.

**2. Update vector_search.test.ts.**

- Change `MOCK_EMBEDDING = new Array(1024).fill(0.01)` → `new Array(768).fill(0.01)`.
- Find any other dimension assertions (e.g., expectations that the embedding has length 1024) and change to 768.
- If any test mocks the Voyage HTTP response, change the mock to mock the Vertex AI client (or fetch response if using direct fetch).
- All 22 existing tests should still pass after the updates.

**3. Add documentary migration 010.**

Create `platform/supabase/migrations/010_vertex_ai_embedding_dim.sql`:

```sql
-- Migration 010: Document the Vertex AI text-multilingual-embedding-002 (768-dim) schema state.
--
-- Background: Migration 005 originally created rag_embeddings.embedding as vector(1024) for
-- Voyage-3-large. The project subsequently migrated to Vertex AI text-multilingual-embedding-002
-- at 768-dim. The schema was updated in-place outside the numbered migration sequence.
-- This migration is documentary — it records the change for replay reproducibility.
--
-- IDEMPOTENT: this migration uses guarded statements so it has no effect on a database whose
-- schema already reflects the 768-dim state. Safe to run multiple times.

DO $$
BEGIN
  -- Check current declared dim of rag_embeddings.embedding
  IF EXISTS (
    SELECT 1
    FROM pg_attribute
    WHERE attrelid = 'rag_embeddings'::regclass
      AND attname = 'embedding'
      AND atttypmod = 1024
  ) THEN
    -- Column is still vector(1024); convert to vector(768). This will fail if any rows
    -- contain 1024-dim data — caller must drop/repopulate first if so.
    RAISE NOTICE 'Migrating rag_embeddings.embedding from vector(1024) to vector(768)...';
    ALTER TABLE rag_embeddings ALTER COLUMN embedding TYPE vector(768);
  ELSE
    RAISE NOTICE 'rag_embeddings.embedding already at vector(768) or unexpected dim; no change.';
  END IF;
END $$;

-- Re-create the HNSW index if it was dropped during the in-place change. IF NOT EXISTS guards.
CREATE INDEX IF NOT EXISTS idx_rag_embeddings_hnsw
  ON rag_embeddings
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Documentation: comment on the column to record the embedding model.
COMMENT ON COLUMN rag_embeddings.embedding IS
  'Vertex AI text-multilingual-embedding-002 (768-dim). Migrated from Voyage-3-large 1024-dim. '
  'Generated via embed.py using Application Default Credentials. task_type at ingest: RETRIEVAL_DOCUMENT.';
```

The exact `atttypmod` value pgvector stores for `vector(N)` is implementation-detail; if the check above fails to match, adjust to use `format_type(atttypid, atttypmod)` or query `information_schema.columns` to compare against `'vector(1024)'`. Confirm syntax against an actual psql session if uncertain — when in doubt, simpler is better.

If applying this migration is awkward (Supabase CLI requires sequential apply, you don't want to run it because the change is already in place), it's acceptable to mark it as a recording-only migration with a clear comment that says "this migration documents the in-place state; it has no effect if the schema is already correct." The point is the file existing and being readable, not necessarily being applied.

**4. Run tests.**

Run the existing test suite. All vector_search tests must pass with the new 768-dim mocks. Confirm no other tests broke (e.g., type-checks against the updated module).

**5. Verify `must_not_touch` clean.**

`git status` shows only the four allowed surfaces modified: `vector_search.ts`, `vector_search.test.ts`, the new migration file, possibly `package.json`/`package-lock.json` if a dependency was added. NO modifications to `embed.py`, governance scripts, architecture documents, other phase deliverables.

## §6 — Verification (functional, against live DB)

If a live database is reachable from your dev environment via the Cloud SQL Auth Proxy:

**6.1 — Live query test.** Write a small smoke script (or use an existing CLI pattern in the project) that:
- Constructs a representative QueryPlan: `{ query_class: 'discovery', domains: ['career'], audience_tier: 'super_admin', tools_authorized: ['vector_search'], ... }` (use sensible defaults for other QueryPlan fields).
- Invokes `vector_search.retrieve(plan, { question: 'career and dharma' })`.
- Logs the returned ToolBundle.

Expected: ToolBundle with non-empty results array. Each result has a `content` field containing chunk text related to career/dharma. `served_from_cache: false`. Latency < 300ms target.

**6.2 — Failure path test.** Temporarily set `VECTOR_SEARCH_ENABLED=false` in env; re-run the smoke test. Expect: empty ToolBundle returned cleanly, no error thrown.

**6.3 — If live DB is not reachable:** unit tests + dim assertions are sufficient acceptance for the hotfix. Document in status_history that live verification was deferred. Native will run live verification when convenient.

## §7 — Done Criteria

`COMPLETE` when:

1. vector_search.ts uses Vertex AI text-multilingual-embedding-002 with ADC; no Voyage references remain.
2. vector_search.test.ts uses 768-dim mocks; all 22 existing tests pass.
3. Migration 010 file exists and is well-formed (regardless of whether it's applied — it's documentary).
4. Project test suite passes; lint + type-check clean.
5. `git status` shows only allowed surfaces modified.
6. (If live DB reachable) §6.1 smoke test returns non-empty results.

When complete:
- Update brief frontmatter `status` to `COMPLETE`.
- Add `completed_on` field.
- Append final `status_history` entry summarizing: lines changed in vector_search.ts, dim mocks updated, migration 010 created (applied? yes/no), live smoke test result if run.
- Notify native that the hotfix is complete and Phase 9's vector search is now functionally aligned with the actual DB state.

## §8 — Communication Discipline

**Halt on uncertainty.** If you find that something else is wrong in vector_search.ts beyond the embedding provider (e.g., the SQL query is also stale, or there's another assumption mismatch), halt and surface to native rather than fixing more than the brief specifies.

**No scope creep.** If you find tangential issues (e.g., the project would benefit from a generalized `EmbeddingProvider` abstraction), note them in `PHASE_9_HOTFIX_OBSERVATIONS_v1_0.md` for native review. Do not implement the abstraction as part of this brief.

**Vertex AI auth.** The project uses Application Default Credentials. In dev: `gcloud auth application-default login` provides the credentials; the Vertex AI client picks them up automatically. In Cloud Run: the service account attached to the deployment provides them. No env-var-based API key needed.

**Project ID.** Vertex AI requires a project ID in the API endpoint. Read it from `GOOGLE_CLOUD_PROJECT` env var. If embed.py has a different convention (e.g., reads from a config file), match that pattern.

## §9 — Final Notes

This is a small, well-bounded fix. The architectural intent (Vertex AI, per architecture v1.0 §17 and per embed.py) was always correct; only the TypeScript implementation in Phase 9's vector_search.ts diverged. The hotfix realigns implementation to intent.

After this hotfix lands, vector_search.ts joins the rest of Phase 9 as functionally complete and live-DB-compatible. Phase 6 (LLM Checkpoints, when authored) and Phase 7 (Panel Mode) won't trip over the dimension mismatch.

A small forward-thinking observation worth noting (in observations file, NOT acting on): if the project ever wants to swap embedding providers in the future, the work would be cleaner with a `platform/src/lib/embeddings/` abstraction that both `vector_search.ts` and any other client consume. embed.py is Python-side and won't share that abstraction. Phase 6 or a later hygiene pass could introduce this if needed; not now.

---

*End of EXEC_BRIEF_PHASE_9_HOTFIX_v1_0.md (status `AUTHORED`, 2026-04-27). Trigger phrase: "Read EXEC_BRIEF_PHASE_9_HOTFIX_v1_0.md and execute it."*
