---
title: "CLAUDECODE_BRIEF — Parity UDA-0-S1: CAPABILITY_MANIFEST audit + dedup"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_0_S1
version: 1.0
status: CURRENT
phase: UDA-0
session_id: UDA-0-S1
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
---

# UDA-0-S1 — Audit and clean CAPABILITY_MANIFEST.json

## 1. Context

`00_ARCHITECTURE/CAPABILITY_MANIFEST.json` has 169 entries with the following known defects (from PRE-S1 diagnostic):
- Duplicate `canonical_id` values for classical text search entries (4 duplicates)
- Tool entries with `status: null` and `path: null/MISSING` (at minimum: lel_query, UCN_WALK_TOOL, CDLM_LOOKUP_TOOL, RM_WALK_TOOL)
- `TOOL_27_MULTI_SCHOOL_SIGNAL_LOOKUP` has `status: STUB`
- Zero MCP tools registered
- `entry_count` field may be stale

This session fixes ALL manifest defects and produces a clean, valid manifest ready for UDA-0-S2 (portal tool registration). No tool entries are added in this session — only cleanup.

## 2. Scope

**may_touch:**
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`

**must_not_touch:**
- Any `platform/` files
- Any `platform-mcp/` files
- `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md`
- Governance files

## 3. Files to read before starting

1. `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — full read; audit every entry
2. `platform/src/lib/retrieve/index.ts` — to identify correct names/paths for defective tool entries
3. `platform-mcp/src/tools/catalog.ts` — to understand MCP tool shapes (for later sessions)

## 4. Acceptance Criteria

- [ ] AC.1: Zero duplicate `canonical_id` values — every entry has a unique canonical_id
- [ ] AC.2: Zero entries with `status: null` — all entries have a non-null status
- [ ] AC.3: Zero entries with `path: null` or `path: "MISSING"` — all entries have a resolved path OR a documented reason (e.g., `path: "N/A - runtime tool"`)
- [ ] AC.4: `TOOL_27_MULTI_SCHOOL_SIGNAL_LOOKUP` status updated from `STUB` to `CURRENT` if the tool exists, or `DEPRECATED` if it does not
- [ ] AC.5: `entry_count` field updated to match actual `entries` array length
- [ ] AC.6: Manifest is valid JSON: `node -e "JSON.parse(require('fs').readFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json','utf8')); console.log('valid')"`
- [ ] AC.7: Audit report at `eval-results/UDA_0_S1_MANIFEST_AUDIT.md`

## 5. Implementation Steps

### Step 1 — Load and inspect the manifest

```bash
node -e "
  const m = JSON.parse(require('fs').readFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json','utf8'));
  console.log('Total entries:', m.entries.length);
  console.log('entry_count field:', m.entry_count);
  
  // Find duplicates
  const ids = m.entries.map(e => e.canonical_id);
  const dupes = ids.filter((id,i) => ids.indexOf(id) !== i);
  console.log('Duplicate canonical_ids:', dupes);
  
  // Find null status
  const nullStatus = m.entries.filter(e => !e.status).map(e => e.canonical_id);
  console.log('Null status:', nullStatus);
  
  // Find missing path
  const missingPath = m.entries.filter(e => !e.path || e.path === 'MISSING').map(e => e.canonical_id);
  console.log('Missing path:', missingPath);
  
  // Find stubs
  const stubs = m.entries.filter(e => e.status === 'STUB').map(e => e.canonical_id);
  console.log('STUBs:', stubs);
"
```

### Step 2 — Fix duplicate entries

For classical text search duplicates: keep the most complete/accurate entry, remove the duplicates. Use a unique suffix if needed (`_BPHS`, `_JAIMINI`, etc.).

### Step 3 — Resolve null-status entries

For each null-status tool entry:
- If the tool file exists in `platform/src/lib/retrieve/` → set `status: "CURRENT"`
- If the tool file exists in `platform-mcp/src/tools/` → set `status: "CURRENT"`
- If tool doesn't exist → set `status: "DEPRECATED"` with a `deprecated_reason` field

### Step 4 — Resolve null/MISSING paths

For each null-path tool entry:
- Portal tools: resolve to `platform/src/lib/retrieve/<tool_name>.ts`
- MCP tools: resolve to `platform-mcp/src/tools/<tool_name>.ts`
- Runtime tools with no file: set `path: "N/A"` with comment `runtime_only: true`

### Step 5 — Resolve STUB entries

Check if `TOOL_27_MULTI_SCHOOL_SIGNAL_LOOKUP` (or equivalent) exists:
```bash
grep -r "multi_school\|multi-school" platform/src/lib/retrieve/ | head -5
grep -r "multi_school\|multi-school" platform-mcp/src/tools/ | head -5
```
Update status accordingly.

### Step 6 — Update entry_count

```javascript
m.entry_count = m.entries.length;
```

### Step 7 — Write cleaned manifest

```bash
node -e "
  const fs = require('fs');
  const m = JSON.parse(fs.readFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json','utf8'));
  // ... (apply all fixes above) ...
  fs.writeFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json', JSON.stringify(m, null, 2));
  console.log('Written. entries:', m.entries.length);
"
```

### Step 8 — Write audit report

Write `eval-results/UDA_0_S1_MANIFEST_AUDIT.md` with:
- Pre-fix counts (duplicates, null-status, missing-path, STUBs)
- Post-fix counts (all zeros)
- List of every change made (which entry, what was fixed)

### Step 9 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
git add eval-results/UDA_0_S1_MANIFEST_AUDIT.md
git commit -m "fix(UDA-0-S1): CAPABILITY_MANIFEST dedup + null-field resolution

Pre-fix:  <N> dupes, <N> null-status, <N> missing-path, <N> STUBs
Post-fix: 0 dupes, 0 null-status, 0 missing-path, 0 STUBs
entry_count updated to match actual entries array length.
Audit report: eval-results/UDA_0_S1_MANIFEST_AUDIT.md"
```

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_0_S1_v1_0.md*
