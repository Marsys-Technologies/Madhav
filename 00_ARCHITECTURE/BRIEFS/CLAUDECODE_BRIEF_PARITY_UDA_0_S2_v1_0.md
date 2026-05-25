---
title: "CLAUDECODE_BRIEF — Parity UDA-0-S2: Register 36 portal RETRIEVAL_TOOLS in manifest"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_0_S2
version: 1.0
status: CURRENT
phase: UDA-0
session_id: UDA-0-S2
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
---

# UDA-0-S2 — Register all portal RETRIEVAL_TOOLS in CAPABILITY_MANIFEST

## 1. Context

After UDA-0-S1 cleaned the manifest of duplicates and null fields, this session adds a complete, accurate entry for every portal RETRIEVAL_TOOL. The manifest currently has only ~4 tool entries for portal tools — all incomplete. This session brings it to 36 (one per tool in `platform/src/lib/retrieve/index.ts`).

Each entry must include: `canonical_id`, `type: "retrieval_tool"`, `channel: "portal"`, `name`, `path`, `status`, `description`, `input_schema_summary`, `output_summary`.

## 2. Scope

**may_touch:**
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`

**must_not_touch:**
- Any `platform/` source files
- Any `platform-mcp/` files
- Governance files

## 3. Files to read before starting

1. `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — current state after UDA-0-S1
2. `platform/src/lib/retrieve/index.ts` — authoritative list of 36 RETRIEVAL_TOOLS
3. Relevant tool files in `platform/src/lib/retrieve/` — to extract input/output schema summaries

## 4. Acceptance Criteria

- [ ] AC.1: Manifest has exactly 36 entries with `channel: "portal"` and `type: "retrieval_tool"`
- [ ] AC.2: Every entry has non-null: `canonical_id`, `name`, `path`, `status`, `description`
- [ ] AC.3: Every entry has `input_schema_summary` (one-line description of key input params)
- [ ] AC.4: Every entry has `output_summary` (one-line description of what rows/shape is returned)
- [ ] AC.5: `entry_count` updated
- [ ] AC.6: Valid JSON

## 5. Implementation Steps

### Step 1 — Extract all portal tool names

```bash
node -e "
  const src = require('fs').readFileSync('platform/src/lib/retrieve/index.ts','utf8');
  const names = [...src.matchAll(/name:\s*['\"]([^'\"]+)['\"]/g)].map(m => m[1]);
  console.log(JSON.stringify(names, null, 2));
  console.log('Count:', names.length);
"
```

### Step 2 — For each tool, read its source file and extract schema

For each tool name, find its file:
```bash
ls platform/src/lib/retrieve/*.ts | head -40
```

Read each tool file to extract:
- Input params (Zod schema fields)
- SQL table queried
- Output shape (what columns are returned)

### Step 3 — Build manifest entries

For each of the 36 tools, construct a manifest entry object:

```json
{
  "canonical_id": "RETRIEVAL_TOOL_<NAME_UPPER>",
  "type": "retrieval_tool",
  "channel": "portal",
  "name": "<tool_name>",
  "path": "platform/src/lib/retrieve/<file>.ts",
  "status": "CURRENT",
  "description": "<one line describing what it does>",
  "input_schema_summary": "<key params e.g.: chart_id(uuid), domain(string), min_confidence(float)>",
  "output_summary": "<e.g.: MSR signal rows ordered by calibrated confidence×significance>",
  "db_tables": ["<primary table>"],
  "added_campaign": "universal-parity"
}
```

### Step 4 — Remove any existing incomplete portal tool entries

Before adding the 36 complete entries, remove any existing partial/incorrect portal tool entries from the manifest (identified in UDA-0-S1 audit).

### Step 5 — Append to manifest

```javascript
m.entries.push(...portalToolEntries);
m.entry_count = m.entries.length;
```

### Step 6 — Validate

```bash
node -e "
  const m = JSON.parse(require('fs').readFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json','utf8'));
  const portal = m.entries.filter(e => e.channel === 'portal' && e.type === 'retrieval_tool');
  console.log('Portal tools in manifest:', portal.length);
  const incomplete = portal.filter(e => !e.description || !e.input_schema_summary);
  console.log('Incomplete entries:', incomplete.map(e => e.name));
"
```

### Step 7 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
git commit -m "feat(UDA-0-S2): register all 36 portal RETRIEVAL_TOOLS in manifest

36 entries added with channel=portal, type=retrieval_tool.
Each entry: canonical_id, name, path, status, description,
input_schema_summary, output_summary, db_tables.
entry_count updated."
```

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_0_S2_v1_0.md*
