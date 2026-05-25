---
session_id: DAR-P1-S1
phase: 1
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
may_touch:
  - platform/src/app/api/mcp/asset/route.ts
  - platform/src/app/api/icr/confirm/route.ts
  - 00_ARCHITECTURE/manifest_overrides.yaml
  - platform/src/scripts/etl/__tests__/msr_parser.test.ts
  - 00_ARCHITECTURE/CONFLICT_PATCHES/PROPOSED/DIS.013_MSR.377_proposed.yaml
must_not_touch:
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
  - platform/python-sidecar/
  - platform/supabase/migrations/
  - .geminirules
---

# DAR-P1-S1: Blocking code fixes

## Context

This is the Data Asset Reconciliation (DAR) workstream. MSR has been upgraded to v5.0
(573 signals) but five pipeline surfaces still reference MSR_v3_0.md. This session fixes
the two blocking surfaces (MCP asset route + ICR confirm endpoint), the governance override
file, the test fixture, and deletes the stale PROPOSED conflict patch.

## Steps

1. Read `platform/src/app/api/mcp/asset/route.ts`.
   Find the SAFE_ASSET_MAP constant. Change the MSR entry:
   - From: any reference to `'MSR_v3_0.md'`
   - To:   `'MSR_v5_0.md'`
   Verify: `grep -n MSR route.ts` — no v3 or v4 references remain.

2. Read `platform/src/app/api/icr/confirm/route.ts`.
   Find MSR_PATH constant (line ~24). Change:
   - From: `'025_HOLISTIC_SYNTHESIS/MSR_v3_0.md'`
   - To:   `'025_HOLISTIC_SYNTHESIS/MSR_v5_0.md'`

3. Read `00_ARCHITECTURE/manifest_overrides.yaml`.
   Find MP.5 enforcement_rule and path_pattern. Change:
   - From: anything referencing `'MSR_v3_0'`
   - To:   `'MSR_v5_0'`

4. Read `platform/src/scripts/etl/__tests__/msr_parser.test.ts`.
   Find the fixture file path (line ~5). Change:
   - From: absolute path ending in `MSR_v3_0.md`
   - To:   absolute path ending in `MSR_v5_0.md`
   Verify: the assertion on line ~45 (expects source_file = `'MSR_v5_0.md'`) is now consistent.

5. Delete the stale PROPOSED patch:
   ```
   git rm 00_ARCHITECTURE/CONFLICT_PATCHES/PROPOSED/DIS.013_MSR.377_proposed.yaml
   ```
   The RESOLVED copy at `CONFLICT_PATCHES/RESOLVED/` is the canonical record.

6. Run vitest for the affected test file to confirm it passes:
   ```
   cd platform && npx vitest run src/scripts/etl/__tests__/msr_parser.test.ts
   ```

7. Commit:
   ```
   dar: P1-S1 fix read_asset + ICR + manifest_overrides + test fixture; rm stale PROPOSED patch
   ```

## Acceptance criteria

- `grep 'MSR_v3_0' platform/src/app/api/mcp/asset/route.ts` → 0 results
- `grep 'MSR_v3_0' platform/src/app/api/icr/confirm/route.ts` → 0 results
- `grep 'MSR_v3_0' 00_ARCHITECTURE/manifest_overrides.yaml` → 0 results
- `grep 'MSR_v3_0' platform/src/scripts/etl/__tests__/msr_parser.test.ts` → 0 results
- `test -f 00_ARCHITECTURE/CONFLICT_PATCHES/PROPOSED/DIS.013_MSR.377_proposed.yaml` → FALSE (deleted)
- vitest msr_parser.test → PASS
