---
artifact: EXEC_BRIEF_PHASE_1A_v1_0.md
status: COMPLETE
completed_on: 2026-04-27
authored_by: Cowork (Claude Opus 4.7)
authored_on: 2026-04-27
executor_target: Claude Code (Anti-Gravity / VS Code extension; NOT the CLI)
trigger_phrase: "Read EXEC_BRIEF_PHASE_1A_v1_0.md and execute it."
phase_number: 1A
phase_name: Migration Foundation (Domain D1, additive)
status_history:
  - timestamp: 2026-04-27
    from: AUTHORED
    to: IN_PROGRESS_STREAM_A
    note: "Stream A dispatched — Storage Layer abstraction (types, postgres, gcs, filesystem adapters)"
  - timestamp: 2026-04-27
    from: IN_PROGRESS_STREAM_A
    to: IN_PROGRESS_STREAM_B
    note: "Stream A complete (16 tests pass). Stream B dispatched — DB migrations 008/009"
  - timestamp: 2026-04-27
    from: IN_PROGRESS_STREAM_B
    to: IN_PROGRESS_STREAM_E
    note: "Stream B complete (10 tests pass). Stream E dispatched — frontmatter discipline"
  - timestamp: 2026-04-27
    from: IN_PROGRESS_STREAM_E
    to: IN_PROGRESS_STREAM_C
    note: "Stream E complete (40 files updated across L1/L2.5/L3). Stream C dispatched — MSR ETL"
  - timestamp: 2026-04-27
    from: IN_PROGRESS_STREAM_C
    to: IN_PROGRESS_STREAM_D
    note: "Stream C complete (499 signals parsed, 9 tests pass). Stream D dispatched — Manifest Builder"
  - timestamp: 2026-04-27
    from: IN_PROGRESS_STREAM_D
    to: STREAMS_COMPLETE_PENDING_INTEGRATION
    note: "Stream D complete (49 manifest entries, 9 tests pass, fingerprint 91977551c4e430bd...)"
  - timestamp: 2026-04-27
    from: STREAMS_COMPLETE_PENDING_INTEGRATION
    to: COMPLETE
    note: "Integration verification passed: 44 Phase-1A tests pass, TS clean, must_not_touch verified. 499 signals loaded (ETL ready), manifest fingerprint 91977551c4e430bd..., 40 files updated."
purpose: First half of Phase 1 (Data Plane). Builds the Storage Layer abstraction, additive DB schema migrations (per-native namespacing + Phase-7 columns + msr_signals table), MSR ETL, Manifest Builder, and frontmatter discipline updates on stable data layers. Phase 1A is purely additive — coexists with FILE_REGISTRY + CANONICAL_ARTIFACTS without replacing them. The migration cutover is Phase 1B.
depends_on:
  - 00_ARCHITECTURE/MARSYS_JIS_ARCHITECTURE_v1_0.md (APPROVED 2026-04-27)
  - 00_ARCHITECTURE/MARSYS_JIS_PROJECT_PLAN_v1_0.md (APPROVED 2026-04-27 — Phase 1 specification at §5; Phase 1A is the additive half per project plan §18 brief-splitting)
  - EXEC_BRIEF_PHASE_0_v1_0.md (COMPLETE — Phase 0 deliverables are dependencies: Schema Registry for asset_entry validation, Configuration Service for feature flags, Storage Layer's relationship to telemetry)
  - CLAUDE.md (project orientation)
parallel_stream_tolerance: |
  Phase 1A is designed to run with the M2/B.5 governance/discovery/retrieval thread RESUMED in parallel
  if native chooses. Phase 1A is purely additive in the platform/src/lib/, platform/src/scripts/, and
  in-place frontmatter additions on stable data layers (L1, L2, L2.5, L3). It does NOT touch governance
  tooling, does NOT modify Python sidecar files, and does NOT update L3.5 or L6 frontmatter (those active
  surfaces are deferred to Phase 1B). Phase 1B (the cutover) will require M2/B.5 to be paused at a clean
  session boundary; Phase 1A does not.
chosen_path: Aggressive (Q1/Q2/Q3 resolved per native 2026-04-27). Phase 1A is the low-risk additive
  half; Phase 1B is the higher-risk cutover half. Trivially reversible at any point in 1A.
---

# EXECUTION BRIEF — Phase 1A: Migration Foundation (additive)

## §0 — Trigger and Execution Model

Native triggers this brief by saying to a Claude Code session: **"Read EXEC_BRIEF_PHASE_1A_v1_0.md and execute it."**

On trigger, Claude Code MUST:
1. Read this entire brief end-to-end before any other action.
2. Read the mandatory pre-flight artifacts in §2 in the order specified.
3. Read the relevant codebase files in §2 to understand current state.
4. Acknowledge readiness; propose the sub-stream sequence the session will execute (one of A-E in series, parallel via subagents, or multi-session parallel).
5. Execute per the specifications in §5 through §9.
6. On completion: run integration verification per §10; flip this brief's `status` to `COMPLETE`; notify native.

**Status transitions.** AUTHORED → IN_PROGRESS_STREAM_(A|B|C|D|E) → STREAMS_COMPLETE_PENDING_INTEGRATION → COMPLETE. Each transition writes a `status_history` entry with timestamp and one-line note.

**Multi-session coordination.** Native confirmed parallel Claude Code streams permitted. If multiple sessions are active concurrently, each session claims one or more sub-streams. Stream A is foundational for C; B is foundational for C; D should run last so it captures E's frontmatter updates. Order: A+B in parallel → C → D+E in parallel.

## §1 — Mission

Build the additive foundation for the Capability Manifest migration. Phase 1A produces:
- A unified Storage Layer abstraction (C1.3) over PostgreSQL + GCS + filesystem.
- Additive DB schema migrations: per-native namespacing on tenant-relevant tables (Q3 forward-compat), the `panel_metadata` JSONB column on messages (Phase-7 prerequisite), composite indices, and the new `msr_signals` table.
- An MSR ETL script that parses `MSR_v3_0.md` and loads its 499 signals into `msr_signals`.
- The Manifest Builder script that auto-derives a Capability Manifest from the filesystem + frontmatter, plus a curated `manifest_overrides.yaml`. The manifest is published but does NOT yet replace FILE_REGISTRY or CANONICAL_ARTIFACTS — those stay as-is until Phase 1B.
- Frontmatter discipline updates on stable data layers (L1, L2, L2.5, L3) — adding `expose_to_chat`, `supplements_parent` where applicable, and `native_id` to canonical files.

Everything in Phase 1A coexists with existing infrastructure. No governance tooling is rewired. No registry is flipped. No file is moved. The migration cutover happens in Phase 1B.

The phase is parallelizable into five sub-streams (A-E). Stream A and B are foundational; Stream C depends on A+B; Streams D and E can run after the others. Within a single Claude Code session, subagent parallelism is the right pattern (per Phase 0 precedent).

## §2 — Mandatory Pre-flight Reading

Read in full, in this order. Do not skip.

**§2.1 — Architectural and project context (read first):**

1. `CLAUDE.md` (project root) — project orientation, principles, current execution position.
2. `00_ARCHITECTURE/MARSYS_JIS_ARCHITECTURE_v1_0.md` — pay particular attention to: §4.1 Domain D1 components (C1.1 Asset Catalog, C1.2 Ingestion, C1.3 Storage); §6 The Catalog (Capability Manifest schema, auto-derivation pattern, overrides); §7 Asset Lifecycle Management (the five-category model); §14 Multi-model and multi-native compatibility (per-native namespacing rationale); Appendix A AssetEntry schema.
3. `00_ARCHITECTURE/MARSYS_JIS_PROJECT_PLAN_v1_0.md` — read §5 Phase 1 specification in full. Note: Phase 1A is the additive half; Phase 1B (deferred until 1A completes and is reviewed) will do the cutover.
4. `EXEC_BRIEF_PHASE_0_v1_0.md` (project root) — Phase 0 deliverables you depend on. Schema Registry at `platform/src/lib/schemas/` is the source for the asset_entry schema you'll validate manifests against. Configuration Service at `platform/src/lib/config/` provides feature flags. Telemetry at `platform/src/lib/telemetry/` provides metric recording.

**§2.2 — Current code state (read to understand what you're modifying or extending):**

5. `platform/src/lib/schemas/asset_entry.schema.json` — the schema your Manifest Builder must produce records compatible with.
6. `platform/src/lib/schemas/index.ts` — the validation utility you'll use to validate the manifest you produce.
7. `platform/src/lib/config/index.ts` — Configuration Service. Add new feature flags as needed.
8. Existing DB schema. Locate migration files and table definitions. Find the `messages`, `conversations`, `documents`, `charts`, `reports`, `pyramid_layers` tables. Understand column types, indices, foreign keys.
9. `platform/src/lib/claude/consume-tools.ts` — the existing 8 tools. You're NOT modifying this file (it stays as-is for now), but reading it tells you what tables exist and how they're queried today.
10. Existing TypeScript ETL or script patterns the project uses (look in `platform/scripts/` or `platform/src/scripts/`). Match them when authoring the new scripts.

**§2.3 — Data layer reconnaissance (read to understand what frontmatter updates you'll apply):**

11. Sample frontmatter from current canonical files to understand existing fields before adding new ones:
    - `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` (first 30 lines)
    - `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (first 30 lines)
    - `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` (first 30 lines)
    - `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` (first 30 lines + a sample signal block)
    - `03_DOMAIN_REPORTS/REPORT_FINANCIAL_v2_1.md` (first 30 lines)
12. `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md` (read-only) — the current canonical artifact registry. Phase 1A's Manifest Builder must produce a manifest that is *equivalent* to this registry's information for the assets covered. (Parity validation is Phase 1B; for 1A, just ensure equivalence is achievable.)
13. `00_ARCHITECTURE/FILE_REGISTRY_v1_11.md` (read-only) — the delta registry. Same parity expectation as #12.

**§2.4 — Sources for MSR ETL:**

14. `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` in full. The 499 signals are structured per-signal blocks. Understand the field layout (signal_id, domain, planet, house, nakshatra, dasha_lord, confidence, significance, is_forward_looking, claim_text, classical_basis, falsifier). The ETL parses this structure.

After completing pre-flight reading, summarize your understanding in 5-7 sentences before proceeding. This confirms the design landed correctly and you have a clean mental model of the stable-vs-active data surfaces (which informs Stream E's scope).

## §3 — Hard Scope Constraints

### `may_touch` (allowed surfaces)

**New files (creation allowed):**
- `platform/src/lib/storage/` — Storage Layer abstraction (Stream A).
- `platform/src/scripts/etl/` — ETL scripts including MSR ETL (Stream C).
- `platform/src/scripts/manifest/` — Manifest Builder (Stream D).
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — manifest output (Stream D, additive — does not replace anything yet).
- `00_ARCHITECTURE/manifest_overrides.yaml` — curated overrides input file (Stream D).
- DB migration files in the project's existing migration directory (Stream B).
- Test files in the project's existing test pattern.

**Existing files (modification allowed only as specified):**
- `platform/src/lib/config/feature_flags.ts` — add new flags as needed for Phase 1A (Stream A/D).
- Frontmatter blocks (top-of-file YAML between `---` markers) of canonical files in stable layers ONLY (Stream E):
  - All CURRENT files in `01_FACTS_LAYER/` (excluding `JHORA_TRANSCRIPTION_v8_0_SOURCE.md` which gets `category: source`; excluding `EVENT_CHART_STATES_v1_0.md` which is intermediate-superseded).
  - All CURRENT files in `025_HOLISTIC_SYNTHESIS/` (CGM v9.0, MSR v3.0, UCN v4.0, CDLM v1.1, RM v2.0, plus any RED_TEAM or AUDIT files which get `category: quality`).
  - All CURRENT files in `03_DOMAIN_REPORTS/` (the 9 v1.1+ reports, plus CROSS_REPORT_COHERENCE_AUDIT_v1_0.md which gets `category: quality`).
- The existing predecessor files (FORENSIC v6.0, FORENSIC v7 supplement, MSR v1.0/v2.0 in 99_ARCHIVE if it exists, CGM v1.0/v2.0, UCN v1.0-v3.0) — frontmatter-only updates to add `native_id` and ensure `status: SUPERSEDED` is set. NO file moves (Phase 1B).

**This brief itself** — only for status transitions and `status_history` updates.

### `must_not_touch` (forbidden surfaces — parallel-stream protection)

The M2/B.5 thread MAY be running in parallel. Phase 1A is designed to coexist with M2/B.5 active. The following surfaces are off-limits:

**Governance tooling (Phase 1B's territory, not 1A's):**
- `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md` — do NOT flip status; do NOT modify content. (Phase 1B will flip to SUPERSEDED.)
- `00_ARCHITECTURE/FILE_REGISTRY_v1_11.md` — do NOT flip status; do NOT modify content.
- `platform/scripts/governance/drift_detector.py` — do NOT modify (Phase 1B rewires it).
- `platform/scripts/governance/schema_validator.py` — do NOT modify (Phase 1B rewires it).
- `platform/scripts/governance/mirror_enforcer.py` — do NOT modify (Phase 1B rewires it).

**Architecture documents (read-only context):**
- `00_ARCHITECTURE/MARSYS_JIS_ARCHITECTURE_v1_0.md` — do NOT update.
- `00_ARCHITECTURE/MARSYS_JIS_PROJECT_PLAN_v1_0.md` — do NOT update.
- The four superseded predecessor docs — leave SUPERSEDED status.

**M2/B.5 active surfaces (especially while M2/B.5 may be running):**
- `platform/python-sidecar/` — entire Python sidecar. M2/B.5 may be writing here.
- `platform/scripts/governance/` — governance scripts (also covered above).
- `platform/src/lib/rag/` (if present) — recent B.6 retrieval client work.
- `035_DISCOVERY_LAYER/` — entire directory. M2/B.5 may be writing patterns/resonances/contradictions here. Phase 1A does NOT update L3.5 frontmatter (deferred to Phase 1B with M2/B.5 paused).
- `06_LEARNING_LAYER/` — entire directory. M2/B.5 may be writing prediction ledger entries. Phase 1A does NOT update L6 frontmatter (deferred to Phase 1B).
- The active `CLAUDECODE_BRIEF.md` (project root, if present) — belongs to M2/B.5 stream.
- `.gemini/` directory and `.geminirules` — Gemini-side mirror surfaces.

**Existing pipeline code (not modified in 1A):**
- `platform/src/lib/claude/consume-tools.ts` — existing 8 tools stay as-is.
- `platform/src/lib/claude/system-prompts.ts` — existing system prompt stays as-is.
- `platform/src/app/api/chat/consume/route.ts` — main route stays as-is.
- `platform/src/components/consume/*` — existing UI components stay as-is.
- `platform/src/lib/models/*` — Phase 0 deliverables stay as-is.

**No file moves in Phase 1A.** No predecessor moves to 99_ARCHIVE/. No source files move to SOURCES/ subdir. All Phase 1A changes are in-place frontmatter additions and new file creations.

### Behavioral constraints

- Existing single-model behavior MUST NOT regress.
- DB schema migrations MUST be additive only (new columns, new tables, new indices). NO column drops, NO type changes on existing columns, NO data deletions.
- All new columns either have a default value (`DEFAULT 'abhisek'` for `native_id`) or are nullable (`NULL` for `panel_metadata`). Existing rows are unaffected.
- The Manifest Builder produces a manifest at the published path, but it is NOT YET consumed by any production code path. Governance tooling continues to read from FILE_REGISTRY + CANONICAL_ARTIFACTS in Phase 1A.
- Frontmatter additions are **additive only**. Existing fields preserved exactly. Field ordering can be normalized (alphabetical or canonical-first) for consistency, but no existing field's value changes.
- If Stream E encounters a file where adding `native_id` or `expose_to_chat` would conflict with existing fields of the same name, halt and ask native.

If you encounter a situation where Phase 1A work seems to require touching a `must_not_touch` surface, halt and ask native. Do not proceed under any interpretation that loosens these constraints.

## §4 — Sub-Stream Overview and Dependencies

**Stream A — Storage Layer Abstraction.** TypeScript abstraction over PostgreSQL + GCS + filesystem. Foundational for Stream C and Stream D.

**Stream B — DB Schema Migrations (additive).** Per-native namespacing, panel_metadata column, new msr_signals table, indices. Foundational for Stream C.

**Stream C — MSR ETL.** TypeScript script parsing MSR_v3_0.md → 499 rows in msr_signals via Storage Layer. Depends on A + B.

**Stream D — Manifest Builder.** TypeScript script walking data dirs + parsing frontmatter → CAPABILITY_MANIFEST.json. Depends on A (storage abstraction for filesystem reads). Should run after Stream E so the manifest captures E's frontmatter updates.

**Stream E — Frontmatter Discipline (stable layers only).** In-place frontmatter updates on canonical files in L1, L2, L2.5, L3 (NOT L3.5 or L6 — those are M2/B.5 active surfaces). Independent of A/B/C; can run any time after pre-flight reading.

**Recommended execution order (subagent parallelism within one Claude Code session):**

```
Time 1 (parallel): Stream A      Stream B      Stream E
                       │             │             │
Time 2:                │  ◄──────── ◄┘             │
                       │   (B done; C can start)   │
                   Stream C ────────► (uses A + B)
Time 3 (parallel):                Stream D ────────► (uses A; reads E's updates)
```

For multi-session parallelism (separate Claude Code sessions): one session takes A+E (independent), one takes B, one takes C+D (sequential dependency). Coordinate via `status_history`.

## §5 — Stream A: Storage Layer Abstraction

**Goal.** Build the unified Storage Layer abstraction at C1.3 specified in architecture §4.1. Single interface over PostgreSQL (Cloud SQL with pgvector), Google Cloud Storage, and filesystem. Higher-domain components call this abstraction; they don't reach into individual backends.

**Tasks (in order):**

**A.1 — Create the storage directory.** Create `platform/src/lib/storage/`.

**A.2 — Define the StorageClient interface.** Create `platform/src/lib/storage/types.ts`:

```typescript
export interface StorageClient {
  // PostgreSQL operations
  query<T = unknown>(sql: string, params?: unknown[]): Promise<{ rows: T[]; rowCount: number }>
  transaction<T>(fn: (tx: TransactionClient) => Promise<T>): Promise<T>
  
  // Object storage operations (GCS)
  readObject(bucket: string, path: string): Promise<Buffer>
  writeObject(bucket: string, path: string, content: Buffer | string, contentType?: string): Promise<void>
  objectExists(bucket: string, path: string): Promise<boolean>
  
  // Filesystem operations (read-only for canonical markdown corpus)
  readFile(repoRelativePath: string): Promise<string>
  fileExists(repoRelativePath: string): Promise<boolean>
  listFiles(repoRelativePath: string, options?: { recursive?: boolean; pattern?: string }): Promise<string[]>
}

export interface TransactionClient {
  query<T = unknown>(sql: string, params?: unknown[]): Promise<{ rows: T[]; rowCount: number }>
}
```

**A.3 — Implement the PostgreSQL adapter.** Create `platform/src/lib/storage/postgres.ts`. Wraps the existing pg client (or whatever Postgres driver the project uses). Connection pooling per existing patterns. Transaction support via the project's transaction primitives.

**A.4 — Implement the GCS adapter.** Create `platform/src/lib/storage/gcs.ts`. Uses `@google-cloud/storage` if present; otherwise add to dependencies. Operations on the existing GCS bucket.

**A.5 — Implement the filesystem adapter.** Create `platform/src/lib/storage/filesystem.ts`. Read-only operations on the repo root. `repoRelativePath` resolves to absolute path within `/Users/Dev/Vibe-Coding/Apps/Madhav/`. NEVER allow paths that escape the repo root (path traversal protection).

**A.6 — Implement the unified StorageClient.** Create `platform/src/lib/storage/index.ts`. Singleton-pattern client that composes the three adapters. Exports `getStorageClient()` factory.

**A.7 — Wire telemetry.** Each storage operation emits a metric via the Phase-0 Telemetry service: `recordLatency('storage.postgres', 'query', latencyMs)`, etc. Include backend identifier in tags.

**A.8 — Tests.** Create `platform/src/lib/storage/__tests__/`:
- `types.test.ts` — type checks (compile-time).
- `postgres.test.ts` — unit tests with mocked pg client.
- `gcs.test.ts` — unit tests with mocked storage client.
- `filesystem.test.ts` — unit tests including path traversal protection.
- `integration.test.ts` — integration test against the development DB and GCS bucket (gated to dev environment).

**Stream A acceptance criteria:**
- [ ] `platform/src/lib/storage/` directory exists with types, postgres, gcs, filesystem, index.
- [ ] `StorageClient.query()` returns expected results against a test query.
- [ ] `StorageClient.readFile()` reads a known canonical file (e.g., FORENSIC v8.0).
- [ ] `StorageClient.readObject()` reads a known GCS object.
- [ ] Path traversal protection: `readFile('../../etc/passwd')` rejects.
- [ ] Telemetry emits per operation.
- [ ] Unit tests pass.
- [ ] Integration test passes against development environment.

## §6 — Stream B: DB Schema Migrations (additive)

**Goal.** Apply additive migrations: per-native namespacing on tenant-relevant tables, the panel_metadata column on messages (Phase-7 prerequisite), composite indices, the new msr_signals table.

**Tasks (in order):**

**B.1 — Locate the migrations directory.** Find where the project stores DB migrations. Common patterns: `platform/db/migrations/`, `platform/migrations/`, or a Prisma/Knex/etc. equivalent. Use the existing pattern.

**B.2 — Author migration: per-native namespacing.** Create a new migration file (timestamp-prefixed per project convention). SQL:

```sql
-- Forward
ALTER TABLE messages ADD COLUMN native_id VARCHAR(64) NOT NULL DEFAULT 'abhisek';
ALTER TABLE conversations ADD COLUMN native_id VARCHAR(64) NOT NULL DEFAULT 'abhisek';
ALTER TABLE documents ADD COLUMN native_id VARCHAR(64) NOT NULL DEFAULT 'abhisek';
ALTER TABLE reports ADD COLUMN native_id VARCHAR(64) NOT NULL DEFAULT 'abhisek';
ALTER TABLE pyramid_layers ADD COLUMN native_id VARCHAR(64) NOT NULL DEFAULT 'abhisek';
-- (extend to charts, user_preferences, or other tenant-relevant tables found during recon)

-- Composite indices for per-native query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_native_conversation 
  ON messages(native_id, conversation_id, created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_native_layer_name 
  ON documents(native_id, layer, name);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_native_domain 
  ON reports(native_id, domain);

-- Rollback
ALTER TABLE messages DROP COLUMN native_id;
-- (corresponding drops for the other tables)
DROP INDEX IF EXISTS idx_messages_native_conversation;
-- etc.
```

Adjust table list per actual schema found during recon (B.1).

**B.3 — Author migration: panel_metadata column.** Add `ALTER TABLE messages ADD COLUMN panel_metadata JSONB NULL` to the same migration or as a separate migration. Schema corresponds to the panel_metadata JSON Schema from Phase 0.

**B.4 — Author migration: msr_signals table.** New migration file:

```sql
-- Forward
CREATE TABLE msr_signals (
  signal_id VARCHAR(64) PRIMARY KEY,
  native_id VARCHAR(64) NOT NULL DEFAULT 'abhisek',
  domain VARCHAR(64) NOT NULL,
  planet VARCHAR(32),
  house INTEGER,
  nakshatra VARCHAR(64),
  dasha_lord VARCHAR(32),
  confidence DECIMAL(4,3) NOT NULL,  -- 0.000 to 1.000
  significance DECIMAL(4,3) NOT NULL,
  is_forward_looking BOOLEAN NOT NULL DEFAULT false,
  claim_text TEXT NOT NULL,
  classical_basis TEXT,
  falsifier TEXT,
  source_file VARCHAR(256) NOT NULL,
  source_version VARCHAR(32) NOT NULL,
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT msr_signals_confidence_range CHECK (confidence BETWEEN 0 AND 1),
  CONSTRAINT msr_signals_significance_range CHECK (significance BETWEEN 0 AND 1)
);

CREATE INDEX idx_msr_signals_native_domain 
  ON msr_signals(native_id, domain, confidence DESC, significance DESC);
CREATE INDEX idx_msr_signals_planet 
  ON msr_signals(planet) WHERE planet IS NOT NULL;
CREATE INDEX idx_msr_signals_dasha_lord 
  ON msr_signals(dasha_lord) WHERE dasha_lord IS NOT NULL;
CREATE INDEX idx_msr_signals_forward_looking 
  ON msr_signals(is_forward_looking) WHERE is_forward_looking = true;

-- Rollback
DROP TABLE msr_signals;
```

**B.5 — Apply migrations to development DB.** Run forward migration. Verify schema via psql or equivalent. Test rollback (apply, verify, rollback, verify pre-migration state, re-apply forward).

**B.6 — Update TypeScript types.** Wherever the project has types matching the DB schema (e.g., `platform/src/lib/db/types.ts` or generated types), update them to reflect the new columns and table. Add `MsrSignal` type matching the new table.

**B.7 — Tests.**
- `platform/src/lib/db/__tests__/migrations.test.ts` — verify forward + rollback work.
- `platform/src/lib/db/__tests__/per_native_isolation.test.ts` — verify queries filtered by `native_id='abhisek'` return only that native's data; with multiple native_ids in test data, isolation holds.

**Stream B acceptance criteria:**
- [ ] All migration files committed.
- [ ] Forward migration applies cleanly to dev DB.
- [ ] Rollback migration reverts cleanly.
- [ ] All tenant-relevant tables have `native_id` column with default 'abhisek'.
- [ ] `messages` table has `panel_metadata JSONB NULL` column.
- [ ] `msr_signals` table exists with correct columns and indices.
- [ ] Existing queries against pre-existing tables continue to work (no regression).
- [ ] Test query `SELECT * FROM msr_signals LIMIT 1` succeeds (returns 0 rows; ETL populates in Stream C).
- [ ] All tests pass.

## §7 — Stream C: MSR ETL

**Goal.** Parse `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` and load its 499 signals into the `msr_signals` table.

**Dependencies.** Stream A (Storage Layer) and Stream B (msr_signals table) must be complete first.

**Tasks (in order):**

**C.1 — Create the ETL directory.** Create `platform/src/scripts/etl/` if not exists.

**C.2 — Examine the MSR structure.** Open `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` and understand the per-signal block structure. Each signal is a delimited block with structured fields. The exact format will dictate the parser.

**C.3 — Author the parser.** Create `platform/src/scripts/etl/msr_parser.ts`. Pure function: input is the raw markdown content; output is `MsrSignal[]` (matching the Stream B type). Handle edge cases: missing optional fields (`planet`, `house`, etc.), multi-line text fields, escaped characters.

**C.4 — Author the loader.** Create `platform/src/scripts/etl/msr_loader.ts`. Uses the Storage Layer (`getStorageClient().query()` or `.transaction()`) to insert/upsert signals. Recommended pattern: clear-and-reload (DELETE existing rows for `native_id='abhisek'` from `msr_signals`, then INSERT all 499). Wrapped in a transaction for atomicity.

**C.5 — Author the entry-point script.** Create `platform/src/scripts/etl/msr_etl.ts`. CLI entry point. Reads `MSR_v3_0.md` via the Storage Layer's filesystem adapter, runs the parser, runs the loader, reports counts (parsed, inserted, errors). Idempotent: running it twice produces the same end state.

**C.6 — Add npm script.** Add to `package.json`:
```json
"scripts": {
  "etl:msr": "tsx platform/src/scripts/etl/msr_etl.ts"
}
```
(Or whatever runner the project uses for TypeScript scripts — `ts-node`, `tsx`, etc.)

**C.7 — Run the ETL.** Execute `npm run etl:msr` against the development DB. Verify 499 rows in `msr_signals` table. Run a sample query: `SELECT * FROM msr_signals WHERE domain='financial' AND confidence > 0.7 LIMIT 5` and confirm signals are returned with expected structure.

**C.8 — Tests.**
- `platform/src/scripts/etl/__tests__/msr_parser.test.ts` — unit tests on small known fragments.
- `platform/src/scripts/etl/__tests__/msr_loader.test.ts` — unit tests with mocked Storage Layer.
- `platform/src/scripts/etl/__tests__/msr_etl.test.ts` — idempotency test (run twice, verify identical state).

**Stream C acceptance criteria:**
- [ ] Parser handles all 499 signals without error.
- [ ] All 499 signals loaded into `msr_signals` table.
- [ ] Each row has correct values across all fields (sample verification: pick 5 random signals, manually verify against MSR_v3_0.md).
- [ ] Re-running the ETL produces the same end state (idempotent).
- [ ] Sample query returns expected results.
- [ ] All tests pass.

## §8 — Stream D: Manifest Builder

**Goal.** Auto-derive a Capability Manifest from the filesystem walk + frontmatter, merged with curated overrides. Phase 1A produces the manifest but does NOT yet consume it for governance — that's Phase 1B.

**Dependencies.** Stream A (Storage Layer for filesystem reads) and Stream E (frontmatter updates) should ideally complete first so the manifest captures the new fields. If Stream E lags, Stream D can still produce a manifest with whatever frontmatter is currently in place.

**Tasks (in order):**

**D.1 — Create the manifest directory.** Create `platform/src/scripts/manifest/`.

**D.2 — Author the auto-deriver.** Create `platform/src/scripts/manifest/auto_deriver.ts`:
- Walks the data directories (`01_FACTS_LAYER`, `02_*`, `025_HOLISTIC_SYNTHESIS`, `03_DOMAIN_REPORTS`, `035_DISCOVERY_LAYER`, `06_LEARNING_LAYER`, plus 99_ARCHIVE if present) via Storage Layer's filesystem adapter.
- Parses each markdown file's frontmatter (top YAML block between `---` markers).
- For each canonical file, builds an `AssetEntry` matching the Phase-0 asset_entry schema: `canonical_id`, `path`, `version`, `status`, `layer`, `expose_to_chat`, `representations`, `interface_version`, `fingerprint` (sha256 of file content), `native_id`, `supplements_parent`, etc.
- Skips: predecessor versions explicitly archived (`status: SUPERSEDED` files are listed but their `expose_to_chat: false`), source files (similar), quality files (similar).
- Emits a base manifest as a JavaScript object.

**D.3 — Author the override-merger.** Create `platform/src/scripts/manifest/override_merger.ts`. Reads `00_ARCHITECTURE/manifest_overrides.yaml` (creating the file with empty content if it doesn't exist). Merges curated fields (`preferred_for`, `cost_weight`, `tool_binding`, etc.) into the base manifest.

**D.4 — Initial manifest_overrides.yaml.** Create `00_ARCHITECTURE/manifest_overrides.yaml` with initial curated content for the Tier-1 eligible set (per architecture §8 — FORENSIC, LEL, SADE_SATI, UCN, CDLM, RM, CGM, the 4 L3.5 registers). Each entry specifies `preferred_for` (the query classes that prefer this asset), `cost_weight`, `always_required` flag (set for FORENSIC and CGM per the floor mandatory rule). Format:

```yaml
overrides:
  FORENSIC:
    preferred_for: [factual, interpretive, predictive, holistic]
    cost_weight: 1.0
    always_required: true   # part of mandatory floor
  CGM:
    preferred_for: [interpretive, cross_domain, holistic]
    cost_weight: 1.0
    always_required: true   # part of mandatory floor
  UCN:
    preferred_for: [interpretive, cross_domain, holistic]
    cost_weight: 0.8
  CDLM:
    preferred_for: [interpretive, cross_domain, discovery]
    cost_weight: 0.7
  # ... (continue for the rest of the eligible set per architecture §8)
```

**D.5 — Author the validator.** Validate the produced manifest against the asset_entry JSON Schema from Phase 0 (using the existing `validate()` utility from `platform/src/lib/schemas/`).

**D.6 — Author the entry-point script.** Create `platform/src/scripts/manifest/build.ts`. CLI entry point. Runs auto-derive → merge overrides → validate → write `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` with fingerprint (sha256 of manifest content) included in the manifest. Idempotent: same input = same output.

**D.7 — Add npm script.**
```json
"scripts": {
  "manifest:build": "tsx platform/src/scripts/manifest/build.ts"
}
```

**D.8 — Run the builder.** Execute `npm run manifest:build`. Verify:
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` exists.
- Manifest validates against the asset_entry schema.
- Manifest contains entries for all CURRENT canonical files in the scanned directories.
- Manifest's fingerprint changes if any source file changes (verify by touching one source file and rebuilding).
- Manifest entries for L1, L2, L2.5, L3 files include the new frontmatter fields populated by Stream E (`expose_to_chat`, `native_id`, etc.).
- Manifest entries for L3.5 and L6 files (which Stream E does NOT update) have those fields absent or with default values — this is acceptable for Phase 1A.

**D.9 — Tests.**
- `platform/src/scripts/manifest/__tests__/auto_deriver.test.ts` — unit tests on small fragments.
- `platform/src/scripts/manifest/__tests__/override_merger.test.ts` — merge correctness tests.
- `platform/src/scripts/manifest/__tests__/build.test.ts` — end-to-end with a small test corpus.

**Stream D acceptance criteria:**
- [ ] `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` exists and is valid.
- [ ] `00_ARCHITECTURE/manifest_overrides.yaml` exists with initial curated content.
- [ ] Auto-deriver produces correct AssetEntry records for sampled CURRENT files.
- [ ] Override merge correctly applies `preferred_for`, `cost_weight`, `always_required` fields.
- [ ] Manifest validates against the asset_entry schema (the Phase-0 validator returns valid: true for every entry).
- [ ] Re-running the builder produces a manifest with the same fingerprint (idempotent unless source files change).
- [ ] All tests pass.

## §9 — Stream E: Frontmatter Discipline (stable layers only)

**Goal.** Apply additive frontmatter updates to canonical files in stable data layers. Stream E's scope is L1, L2 (if present), L2.5, L3 only — NOT L3.5, NOT L6 (those are M2/B.5 active surfaces, deferred to Phase 1B).

**Frontmatter additions per canonical file** (existing fields preserved verbatim; new fields added):

```yaml
# Existing frontmatter preserved verbatim (artifact, version, status, etc.)
# New fields added:
expose_to_chat: true
native_id: "abhisek"
layer: "L1"  # or L2, L2.5, L3 per the file's actual layer; field added if missing
```

**Special cases:**

For source-category files (e.g., `JHORA_TRANSCRIPTION_v8_0_SOURCE.md`, `EVENT_CHART_STATES_v1_0.md`):
```yaml
expose_to_chat: false
native_id: "abhisek"
category: "source"
```

For quality-category files (RED_TEAM, AUDIT files):
```yaml
expose_to_chat: false
native_id: "abhisek"
category: "quality"
```

For supplement files (e.g., `FORENSIC_DATA_v8_0_SUPPLEMENT.md`):
```yaml
expose_to_chat: true
native_id: "abhisek"
supplements_parent: "FORENSIC_ASTROLOGICAL_DATA_v8_0.md"
```

For predecessor files with `status: SUPERSEDED` (e.g., `FORENSIC_ASTROLOGICAL_DATA_v6.0_ABHISEK_MOHANTY.md`):
```yaml
expose_to_chat: false
native_id: "abhisek"
# status: SUPERSEDED (already present)
```

**Tasks (in order):**

**E.1 — Enumerate target files.** List all CURRENT and SUPERSEDED files in `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, `03_DOMAIN_REPORTS/` (and `02_*` if present). For each, classify into one of: canonical-current, canonical-supplement, predecessor, source, quality.

**E.2 — Apply frontmatter updates.** For each file, read the existing frontmatter (the YAML block between the leading `---` markers), add the new fields per the special-case rules above, write back. PRESERVE all existing fields exactly. Common pitfalls to avoid:
- Don't reorder existing fields (or if you must, normalize alphabetically, but don't change values).
- Don't change YAML formatting style (single-quotes vs double-quotes vs no-quotes — match existing).
- Don't add fields if they're already present with a different value (halt and ask).

**E.3 — Verify integrity.** After updates, every modified file should still parse as valid YAML in the frontmatter, and every existing field's value should be unchanged. Run a quick verification script (or manual diff) on a few sample files before bulk-applying.

**E.4 — Tests.** Manual verification + automated check:
- `platform/src/scripts/manifest/__tests__/frontmatter_check.test.ts` — for each modified file, verify frontmatter parses, verify new fields are present, verify pre-existing fields are unchanged.

**Stream E acceptance criteria:**
- [ ] Every CURRENT canonical file in L1, L2.5, L3 has `expose_to_chat`, `native_id`, `layer` fields.
- [ ] Source-category files have `expose_to_chat: false` and `category: source`.
- [ ] Quality-category files have `expose_to_chat: false` and `category: quality`.
- [ ] Supplement files have `supplements_parent` field pointing to their parent.
- [ ] Predecessor files have `expose_to_chat: false`.
- [ ] No pre-existing field's value was changed.
- [ ] No file in L3.5 or L6 was modified (verifiable via git status — those layers are NOT in this phase's scope).
- [ ] All YAML parses correctly.

## §10 — Integration and Final Acceptance

After all five sub-streams are complete, run integration verification:

**§10.1 — Dependency graph verification.** Confirm:
- Stream A (Storage Layer) is importable by Stream C (MSR ETL) and Stream D (Manifest Builder).
- Stream B (DB schema) is queryable by Stream C (MSR ETL writes) and verifies the panel_metadata column will be available for Phase 7.
- Stream D's manifest reflects Stream E's frontmatter updates.

**§10.2 — End-to-end smoke test.**
- Run `npm run manifest:build` — produces a valid manifest.
- Run `npm run etl:msr` — populates msr_signals (or verifies it's already populated).
- SQL: `SELECT count(*) FROM msr_signals WHERE native_id='abhisek'` returns 499.
- Inspect a sample manifest entry for FORENSIC_ASTROLOGICAL_DATA_v8_0.md — confirm `expose_to_chat: true`, `native_id: 'abhisek'`, `layer: 'L1'`, `always_required: true`, `preferred_for` includes 'factual' and 'interpretive'.
- Existing Consume tab queries continue to work (no regression).

**§10.3 — Test suite execution.** Run the full project test suite. All tests must pass.

**§10.4 — `must_not_touch` verification.** `git status` (or equivalent). Confirm no file in the must_not_touch list of §3 has been modified. Particular attention: no governance script modified, no python-sidecar file modified, no L3.5 or L6 file modified.

**§10.5 — Lint and type-check.** Project's lint and type-check commands. No new warnings or errors.

**§10.6 — Backward compatibility.** Existing single-model queries against the Consume tab continue to work end-to-end (regression test from Phase 0).

## §11 — Phase 1A Done Criteria

This brief is `COMPLETE` when ALL of the following are true:

1. All Stream A acceptance criteria met (Storage Layer working).
2. All Stream B acceptance criteria met (DB schema migrations applied, msr_signals table created).
3. All Stream C acceptance criteria met (499 MSR signals loaded).
4. All Stream D acceptance criteria met (manifest published).
5. All Stream E acceptance criteria met (frontmatter discipline applied to stable layers).
6. All §10 integration verification steps passed.
7. `git status` shows no modifications to `must_not_touch` surfaces.
8. The project builds and tests pass.
9. Native (or designated reviewer) confirms acceptance.

When all criteria met:
- Update this brief's frontmatter `status` field from current state to `COMPLETE`.
- Add `completed_on` field with the current date.
- Append a `status_history` final entry summarizing what was accomplished, including: number of signals loaded, manifest fingerprint, files updated count.
- Notify native that Phase 1A is complete and Phase 1B brief authoring can begin.

## §12 — Communication Discipline

**Halt on uncertainty.** If during execution you discover an architectural choice the brief didn't make, do NOT improvise. Halt, surface the question to native, and wait for direction.

**No scope creep.** If you find a tangentially related issue, note it in `PHASE_1A_OBSERVATIONS_v1_0.md` for native review. Do not fix it as part of this brief.

**Status updates between sessions.** Multi-session execution leaves `status_history` updated.

**Multi-session coordination.** If multiple Claude Code sessions run in parallel, each session claims one or more sub-streams in `status_history`.

**Adherence to architectural principles.** Architecture §3 P.7 (modular componentization with stable interfaces), P.8 (domain knowledge → LLM, integrity/lookup/persistence → deterministic), P.10 (multi-native forward-compatibility) govern Phase 1A. The Storage Layer is pure infrastructure; the manifest builder is pure data lookup; the MSR ETL is pure data transformation; frontmatter updates are pure metadata extension. No LLM calls in Phase 1A.

**Conflict with M2/B.5.** If M2/B.5 is running in parallel and you observe a conflict (e.g., a file you're updating was just touched by M2/B.5), halt and report. Don't try to resolve concurrency issues unilaterally.

## §13 — Final Notes

Phase 1A is the foundation for the Capability Manifest migration. Done well, Phase 1B (cutover) becomes a small, low-risk operation. Done sloppily, Phase 1B becomes a debugging marathon.

The MSR ETL is the largest single data operation in Phase 1A. Spend time on the parser — getting 499 signals right matters because every retrieval call from Phase 6 onward queries this table.

The Manifest Builder is the next-largest. Its output is informational in Phase 1A but becomes load-bearing in Phase 1B (when governance tooling cuts over to read it). Make sure every CURRENT canonical file is captured correctly.

Frontmatter discipline (Stream E) looks tedious but is exactly the kind of work where missing one file creates downstream confusion. Be thorough. The test in E.4 is your safety net.

When Phase 1A completes, native reviews. Phase 1B authoring depends on what 1A learned — particularly any unexpected files, frontmatter conflicts, or schema surprises that Phase 1A surfaces.

---

*End of EXEC_BRIEF_PHASE_1A_v1_0.md (status `AUTHORED`, 2026-04-27). Trigger phrase: "Read EXEC_BRIEF_PHASE_1A_v1_0.md and execute it." On Phase 1A completion, status flips to `COMPLETE` and Cowork authors `EXEC_BRIEF_PHASE_1B_v1_0.md` (the migration cutover).*
