---
artifact: CLAUDECODE_BRIEF_TOOLING_REMEDIATION_TR-P1-S3_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: PENDING
authored_by: Conductor (2026-05-25)
session_id: TR-P1-S3
---

# CLAUDECODE_BRIEF — TR-P1-S3
## Phase 1.5 + 1.6: read_asset prod cwd fix + list_assets + query_panchanga 5 enrichment columns

## §0 — Start

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix
git status  # must be clean
```

## §1 — Scope

may_touch: platform-mcp/src/tools/read_asset.ts, platform-mcp/src/tools/query_panchanga.ts, platform-mcp/src/tools/read_asset.test.ts, platform-mcp/src/tools/query_panchanga.test.ts, platform-mcp/src/tools/list_assets.ts, platform-mcp/src/index.ts
must_not_touch: 025_HOLISTIC_SYNTHESIS/**, 01_FACTS_LAYER/**, .geminirules, CLAUDE.md, 00_ARCHITECTURE/CONDUCTOR/tooling-remediation/**, platform/src/**

## §2 — Task

### Phase 0 findings

**C9 — read_asset:** Bug is **PROD_ENV** — `MARSYS_REPO_ROOT` env var is not set in the Cloud Run sidecar. Every call to `read_asset` resolves the path as `path.join(undefined, canonical_path)` which becomes `/canonical_path` (an absolute path starting at `/`, which does not exist in the container). Fix: use `__dirname`-relative resolution or a hardcoded fallback path constant; do NOT rely on `MARSYS_REPO_ROOT` alone.

**C8 — query_panchanga:** Bug is **wrapper** layer — the 5 enrichment JSONB columns (`special_yogas`, `choghadiya`, `hora`, `inauspicious`, `auspicious`) are fully populated in the DB (all rows since 2026-01-01). The `query_panchanga` handler's SQL SELECT simply omits them. Fix: add them to the SELECT and response shape.

---

### 2.1 — Fix read_asset (C9)

File: `platform-mcp/src/tools/read_asset.ts` (or whichever file handles read_asset)

1. Read the file fully. Find the path resolution logic.
2. The prod Cloud Run sidecar has the project files under a known path (check the Dockerfile in `platform-mcp/Dockerfile` or `platform/Dockerfile` for the WORKDIR and COPY destinations).
3. Fix strategy — in priority order:
   a. **Use `__dirname`-relative resolution.** The sidecar JS bundle is at `/app/` or similar. The canonical documents are copied there too. Use: `path.join(__dirname, '../../..', canonical_path)` or similar (adjust depth based on the actual bundle structure).
   b. **Fallback chain:** `process.env.MARSYS_REPO_ROOT ?? path.join(__dirname, '../..')` — this way it works both locally (where MARSYS_REPO_ROOT may be set) and in prod (where it isn't).
4. Also read the Dockerfile to confirm where project files land in the container image.
5. Add `list_assets` as a new tool (same file or new file `platform-mcp/src/tools/list_assets.ts`):
   - No params needed.
   - Reads the `CAPABILITY_MANIFEST.json` (at the known repo path) and returns `{ canonical_ids: [{ id, path, status }] }` for all entries.
   - Alternatively, hardcode the list of known canonical_ids with their paths (simpler and safer for prod).

### 2.2 — read_asset regression tests

File: `platform-mcp/src/tools/read_asset.test.ts` (create if absent)

- Mock `fs.readFileSync`; test that `read_asset({ canonical_id: "MACRO_PLAN" })` resolves to a non-empty content string.
- Test that `read_asset({ canonical_id: "NONEXISTENT" })` returns a clean error (not an unhandled exception).
- Test `list_assets()` returns an array with at least 10 ids.

### 2.3 — Fix query_panchanga enrichment (C8)

File: `platform-mcp/src/tools/query_panchanga.ts`

1. Read the file fully. Find the SQL SELECT statement or the fields returned from the primitive.
2. Add the 5 JSONB columns to the SELECT:
   ```sql
   SELECT ..., special_yogas, choghadiya, hora, inauspicious, auspicious FROM panchanga_daily WHERE ...
   ```
3. In the response mapping, include these 5 columns:
   ```typescript
   const result = {
     date: row.date,
     // ... existing fields ...
     special_yogas: row.special_yogas ?? null,
     choghadiya: row.choghadiya ?? null,
     hora: row.hora ?? null,
     inauspicious: row.inauspicious ?? null,
     auspicious: row.auspicious ?? null,
   };
   ```
4. Update the Zod output schema (if one exists) to include these 5 fields as `z.any().optional()`.

### 2.4 — query_panchanga regression tests

File: `platform-mcp/src/tools/query_panchanga.test.ts` (create if absent)

- Mock the DB call; test that `query_panchanga({ date: "2026-05-24" })` response includes `choghadiya` field (even if null in the mock).
- Test that the SELECT query string contains "choghadiya" (grep the SQL string in the handler).

### 2.5 — Register list_assets in the MCP tool registry

File: `platform-mcp/src/index.ts` (or wherever tools are registered)

Add `list_assets` to the registered tools list.

### 2.6 — Commit

```bash
git add platform-mcp/src/tools/read_asset.ts \
        platform-mcp/src/tools/query_panchanga.ts \
        platform-mcp/src/tools/list_assets.ts \
        platform-mcp/src/tools/read_asset.test.ts \
        platform-mcp/src/tools/query_panchanga.test.ts \
        platform-mcp/src/index.ts
git commit -m "fix(TR-P1-S3): read_asset cwd+list_assets; query_panchanga 5 enrichment columns"
```

## §3 — Acceptance criteria

| ID | Criterion |
|---|---|
| AC.1 | `read_asset.ts` uses `__dirname`-relative path OR `MARSYS_REPO_ROOT ?? __dirname` fallback — not naked `MARSYS_REPO_ROOT` |
| AC.2 | `list_assets` tool registered and returns ≥10 canonical_ids |
| AC.3 | `read_asset.test.ts` passes — MACRO_PLAN resolves; NONEXISTENT returns clean error |
| AC.4 | `query_panchanga.ts` SELECT includes all 5 enrichment JSONB columns |
| AC.5 | Both test files pass: `npx vitest run src/tools/read_asset.test.ts src/tools/query_panchanga.test.ts` exits 0 |

## §4 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix && \
(npx vitest run src/tools/read_asset.test.ts src/tools/query_panchanga.test.ts --reporter=verbose 2>&1 | grep -E 'passed|PASS' | grep -q '.')
```

## §5 — FINAL_SUMMARY

```
---FINAL_SUMMARY---
session_id: TR-P1-S3
status: PASS | HALT_NEEDS_HUMAN
tests_passed: <N>
files_changed: <list>
commit_sha: <git log --format=%H -1>
notes_for_orchestrator: <path chosen for read_asset; any deviations>
---
```
