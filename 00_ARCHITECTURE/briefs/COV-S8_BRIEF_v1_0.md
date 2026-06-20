---
artifact: COV-S8_BRIEF_v1_0.md
canonical_id: COV-S8_BRIEF
version: 1.0
status: CURRENT
authored_on: 2026-05-21
authored_by: Cowork session COV-S8 — Discovery register version audit and smoke gate
session_label: COV-S8
audit_section: §G.8
parent_audit: CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT_v1_0.md (v1.2)
branch: feature/m5-coverage-remediation
may_touch:
  - platform/tests/governance/smoke_planner_register_tools.test.ts
  - 00_ARCHITECTURE/BRIEFS/COV-S8_BRIEF_v1_0.md
must_not_touch:
  - platform/src/**
  - platform/src/lib/pipeline/manifest_compressor.ts
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
acceptance_criteria:
  - smoke_planner_register_tools.test.ts passes under vitest run
  - tsc --noEmit exits 0
  - lint reports 0 errors for the test file
  - every entry in compressManifest result has a non-empty t field
  - manifest entries with interface_version carry it as a string
  - result.length >= 1
---

# COV-S8 BRIEF — Discovery register version audit and smoke gate

## §1 — Mission

COV-S1 extended `CAPABILITY_MANIFEST.json` with new optional fields (`output_schema`,
`linked_data_asset_ids`, `expose_to_planner`, `examples`, `gating_constraints`) and
declared that these are backward-compatible additions that do not require an
`interface_version` bump. COV-S8 adds an explicit smoke test to gate this contract:

1. Prove `compressManifest()` is callable with the live manifest and returns a non-empty
   array of valid `CompressedEntry` objects (each with a non-empty `t` field).
2. Prove the manifest's per-entry `interface_version` field is readable as a string
   (structural presence check only — not hardcoded to "1.0" so future bumps don't
   require test edits).
3. Confirm no regression in the manifest reader code path after COV-S1's schema changes.

This session is read-only with respect to production code. It only adds a test file
and this brief.

## §2 — Key findings from source reads

### manifest_compressor.ts

- `compressManifest(manifest: CapabilityManifest): CompressedEntry[]` is **pure** —
  no filesystem access. Callers must load and pass the manifest.
- Returns only entries whose `tool_name` is in `PRIMARY_TOOL_NAMES` (11 tools).
- `CompressedEntry` has 5 fields: `t` (tool_name), `d` (description ≤15 words),
  `p` (param names), `c` (token_cost_hint), `a` (linked_data_asset_id).
- The existing test at `tests/pipeline/manifest_compressor.test.ts` already loads the
  live manifest via `readFileSync` and calls `compressManifest()`. COV-S8's test at
  `tests/governance/` uses the same pattern for the smoke gate.

### CAPABILITY_MANIFEST.json

- `interface_version` is a **per-entry field** (not a top-level manifest field).
- Every entry in the live manifest carries `"interface_version": "1.0"`.
- There is no top-level `interface_version` key; assertions must target `entries[N]`.
- 163 total entries; 114 carry `interface_version`.

## §3 — Deliverable

`platform/tests/governance/smoke_planner_register_tools.test.ts`

Assertions (6 total):
1. `compressManifest(manifest)` returns an array.
2. Array length >= 1.
3. Every entry has a non-empty `t` string.
4. `manifest.entries` array exists and is non-empty.
5. At least one manifest entry carries `interface_version` as a string.
6. No manifest entry carries `interface_version` as a non-string (type consistency).

## §4 — Gate results (recorded at session close)

| Gate     | Result |
|----------|--------|
| tsc      | PASS   |
| vitest   | PASS   |
| lint     | PASS   |

Assertion count: 6
