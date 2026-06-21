---
artifact: COV-S1_BRIEF_v1_0.md
session_id: COV-S1
campaign: M5_COVERAGE_REMEDIATION
stream: cov
audit_section: §G.1
status: ACTIVE
version: 1.0
authored_on: 2026-05-21
may_touch:
  - platform/src/lib/pipeline/manifest_compressor.ts
  - 00_ARCHITECTURE/manifest_overrides.yaml
  - platform/scripts/governance/build_manifest.ts   # does NOT exist as of 2026-05-21 — verify before touching
  - platform/scripts/governance/                    # any governance script that builds or validates the manifest
must_not_touch:
  - platform/src/lib/pipeline/manifest_compressor.ts  # compressor algorithm is COV-S3; type block only is in-scope
  - platform/src/lib/retrieve/index.ts                # tool registry is COV-S2
  - platform/src/app/**                               # no app code this session
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json          # generated file — only update via build script
gates:
  - tsc
  - vitest_changed
  - lint
---

# COV-S1 Brief — Manifest Schema Extension

## §A — Goal

Extend `CapabilityManifestEntry` (the shared TypeScript interface that governs every manifest entry) so every wired retrieval tool can carry first-class schema fields for planner consumption. The change is purely additive and backwards-compatible: all new fields are optional; existing entries pass through unchanged.

This session makes the schema ready for COV-S2 (per-tool entries) and COV-S3 (compressor cutover). It must not change runtime behavior — the compressor's `PRIMARY_TOOL_NAMES` filtering and `CompressedEntry` shape remain untouched in this session.

## §B — Files to touch (verified paths as of 2026-05-21)

### B.1 — Primary edit target

**`platform/src/lib/pipeline/manifest_compressor.ts`** — This is the canonical home of `CapabilityManifestEntry`. The interface is at lines 20–29. The type file path named in the audit spec (`platform/src/lib/types/capability_manifest.ts`) does **not exist** on disk; the actual type lives inside `manifest_compressor.ts`. COV-S1 extends the interface block there.

Current state of `CapabilityManifestEntry` (lines 20–29):

```typescript
export interface CapabilityManifestEntry {
  canonical_id: string
  tool_name?: string
  tool_description?: string
  description?: string
  query_schema?: QuerySchema
  token_cost_hint?: TokenCostHint
  linked_data_asset_id?: string
  [k: string]: unknown
}
```

Fields already present (no action needed):
- `tool_name` — already optional
- `tool_description` — already optional
- `query_schema` — already optional (typed as `QuerySchema`, which is a narrower version of `Record<string,unknown>` with `type`, `properties?`, `required?`)
- `cost_weight` — already captured by the index signature `[k: string]: unknown` and present in `CAPABILITY_MANIFEST.json`; no explicit field declaration required unless COV-S3 needs to read it typed

Fields to add (all optional):
- `output_schema?: Record<string, unknown>` — JSON Schema for the tool's return value
- `linked_data_asset_ids?: string[]` — plural array (note: singular `linked_data_asset_id?: string` already present; keep the singular for backwards compat, add the plural for multi-asset tools)
- `expose_to_planner?: boolean` — COV-S3 will use this to replace `PRIMARY_TOOL_NAMES` filtering
- `examples?: Array<{ query: string; expected_plan_fragment: string }>` — planner few-shot examples
- `gating_constraints?: Array<{ condition: string; action: string }>` — COV-S6 R-rule migration target

**Important scope limit on this file:** Only the `CapabilityManifestEntry` interface block (lines 20–29) and the `QuerySchema` interface (lines 14–18) may be touched. Do NOT modify `CompressedEntry`, `compressManifest()`, `compressedManifestToString()`, `PRIMARY_TOOL_NAMES`, or any runtime logic. Those belong to COV-S3.

### B.2 — Manifest overrides stubs

**`00_ARCHITECTURE/manifest_overrides.yaml`** — Add field stubs in the `schema_extension_fields:` section (or add that section if it does not exist) documenting the new optional fields so governance tooling can cross-check manifest entries against the declared schema. This is a documentation stub only; no executable code changes here.

### B.3 — Build script (conditional)

**`platform/scripts/governance/build_manifest.ts`** — This file does NOT exist as of 2026-05-21 (only Python scripts are present: `drift_detector.py`, `schema_validator.py`, `mirror_enforcer.py`, `manifest_reader.py`, `_ca_loader.py`, `serialize_build_state.py`). Do not create it in this session. If the audit acceptance criterion "manifest regenerates with new optional fields populated as null/empty" requires a build step, the existing `manifest_reader.py` or `schema_validator.py` should be checked first. If no build script exists, note this gap in the session-close checklist as a COV-S2 prerequisite.

## §C — Acceptance criteria (from §G.1)

1. **tsc clean** — `cd platform && npx tsc --noEmit` exits 0 with no new errors after the interface additions.

2. **Manifest regenerates** — Existing `CAPABILITY_MANIFEST.json` entries remain structurally valid after the schema extension. Any governance validator that parses manifest entries (e.g., `schema_validator.py`, `manifest_reader.py`) still exits 0. New optional fields are absent (null/empty) in existing entries — that is the correct backwards-compatible behavior.

3. **MANIFEST_AUDIT_v1_0.md scheduled job continues to pass** — Run `python3 platform/scripts/governance/schema_validator.py` (or equivalent) and confirm exit code 0.

4. **No runtime behavior change** — `manifest_compressor.ts`'s `PRIMARY_TOOL_NAMES` filtering, `CompressedEntry` shape, `compressManifest()`, and `compressedManifestToString()` are byte-for-byte identical before and after this session. Verified by `git diff platform/src/lib/pipeline/manifest_compressor.ts` showing changes only in the `CapabilityManifestEntry` and (optionally) `QuerySchema` interface blocks.

5. **Vitest for manifest_compressor still passes** — `cd platform && npx vitest run tests/pipeline/manifest_compressor.test.ts` exits 0. No test changes are expected; this is a regression guard.

6. **`linked_data_asset_id` (singular) preserved** — The existing singular field is retained for backwards compatibility; the new plural `linked_data_asset_ids?: string[]` is additive alongside it.

## §D — Hard rules

1. **Interface-only, no runtime** — Touch only type/interface declarations. Do not change any function, constant, or export behavior.

2. **No fabricated build script** — Do not create `build_manifest.ts` if it does not exist. Flag the absence as a note; do not fill the gap with invented code that wasn't scoped.

3. **Singular field preserved** — `linked_data_asset_id?: string` stays; add `linked_data_asset_ids?: string[]` alongside it.

4. **Index signature retained** — Keep `[k: string]: unknown` on `CapabilityManifestEntry` so unknown future fields don't break compile.

5. **No app code** — No changes under `platform/src/app/`.

6. **No tool registry** — `platform/src/lib/retrieve/index.ts` is not touched. Tool registration is COV-S2.

7. **No compressor algorithm** — `compressManifest()`, `compressedManifestToString()`, `PRIMARY_TOOL_NAMES`, and `CompressedEntry` are not touched. Compressor cutover is COV-S3.

8. **CAPABILITY_MANIFEST.json is generated** — Do not hand-edit it. If a regeneration step exists, run it via script only.

## §E — Verification commands

Run these in order after each gate:

### After tsc gate

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavCoverage/platform
npx tsc --noEmit 2>&1 | tail -20
# Expected: no output (exit 0)
```

### After vitest_changed gate

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavCoverage/platform
npx vitest run tests/pipeline/manifest_compressor.test.ts 2>&1 | tail -30
# Expected: all tests pass, no new failures
```

### After lint gate

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavCoverage/platform
npx eslint src/lib/pipeline/manifest_compressor.ts --max-warnings 0 2>&1 | tail -20
# Expected: exit 0 or only pre-existing warnings
```

### Schema validator (governance pass)

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavCoverage
python3 platform/scripts/governance/schema_validator.py 2>&1 | tail -20
# Expected: PASS or exit 0
```

### Diff scope check (confirm no runtime code changed)

```bash
git diff platform/src/lib/pipeline/manifest_compressor.ts
# Expected: changes only within the CapabilityManifestEntry interface block (lines ~20–29)
# and optionally QuerySchema interface (lines ~14–18)
# No changes to PRIMARY_TOOL_NAMES, CompressedEntry, compressManifest, compressedManifestToString
```

### Backwards compatibility check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavCoverage
python3 platform/scripts/governance/manifest_reader.py 2>&1 | tail -20
# Expected: PASS — existing manifest entries still valid
```

---

## §F — Session close-out notes (pre-populated for executor)

At session close, record in `CONDUCTOR_LOG.md` and `SESSION_LOG.md`:

- Whether `build_manifest.ts` exists (NO as of 2026-05-21) — flag as COV-S2 prerequisite if manifest regeneration requires a new script
- Whether `manifest_reader.py` or `schema_validator.py` was used as the schema-validation stand-in
- Any pre-existing tsc or lint warnings that were present before this session's changes (for baseline documentation)
- Confirmation that `PRIMARY_TOOL_NAMES`, `CompressedEntry`, and all runtime functions in `manifest_compressor.ts` are byte-identical to pre-session state

*End of COV-S1_BRIEF_v1_0.md (v1.0, 2026-05-21)*
