---
title: "CLAUDECODE_BRIEF — Parity UDA-0-S3: Register 41 MCP tools in manifest + fix catalog.ts"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_0_S3
version: 1.0
status: CURRENT
phase: UDA-0
session_id: UDA-0-S3
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
requires_hap: HAP-2
---

# UDA-0-S3 — Register all MCP tools in manifest + complete catalog.ts

## 1. Context

Two gaps to close in this session:

**Gap A — CAPABILITY_MANIFEST:** Zero MCP tools currently registered. After TR (bace7b45) the MCP sidecar has 41 registered tools (`platform-mcp/src/server.ts`). All 41 need manifest entries with `channel: "mcp"`.

**Gap B — catalog.ts:** `platform-mcp/src/tools/catalog.ts` has only 23 entries. The 18 tools added by TR to `server.ts` are missing from catalog.ts. The catalog is used by the MCP `tool_health` and `data_coverage` meta-tools to enumerate available tools. This is a functional gap — meta-tools return incomplete data.

After this session, **HAP-2** fires — conductor halts for native review before UDA-1 begins.

## 2. Scope

**may_touch:**
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`
- `platform-mcp/src/tools/catalog.ts`

**must_not_touch:**
- `platform-mcp/src/server.ts` (reference only)
- Any `platform/` files
- Governance files

## 3. Files to read before starting

1. `platform-mcp/src/server.ts` — authoritative list of 41 registered MCP tools (all imports)
2. `platform-mcp/src/tools/catalog.ts` — current 23-entry catalog (to be completed)
3. `platform-mcp/src/tools/` directory listing — all tool files
4. `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — current state after UDA-0-S2

## 4. Acceptance Criteria

**Manifest:**
- [ ] AC.1: Manifest has exactly 41 entries with `channel: "mcp"` and `type: "retrieval_tool"`
- [ ] AC.2: Each MCP entry has: `canonical_id`, `name`, `path`, `status`, `description`, `input_schema_summary`, `output_summary`
- [ ] AC.3: `entry_count` updated to reflect total (now 36 portal + 41 MCP + other entries)

**catalog.ts:**
- [ ] AC.4: `platform-mcp/src/tools/catalog.ts` has entries for all 41 tools registered in `server.ts`
- [ ] AC.5: Each new catalog entry follows the existing shape (read existing entries for the exact TypeScript interface)
- [ ] AC.6: TypeScript compiles: `cd platform-mcp && npx tsc --noEmit`
- [ ] AC.7: `tool_health` meta-tool (if callable) returns 41 tools (not 23)

## 5. Implementation Steps

### Step 1 — Extract all 41 MCP tool names from server.ts

```bash
grep "^import { register" platform-mcp/src/server.ts | \
  sed "s/.*register//;s/ .*//"
```

This gives the function names. Derive tool names from them (e.g., `registerQueryChartFacts` → `query_chart_facts`).

Also get the exact registered names from the tool files:
```bash
for f in platform-mcp/src/tools/*.ts; do
  name=$(grep -m1 "name:" "$f" | sed "s/.*name: *['\"]//;s/['\"].*//")
  echo "$f: $name"
done
```

### Step 2 — Identify the 18 missing catalog.ts entries

Compare the 41 server.ts tools against the 23 catalog.ts entries:
```bash
node -e "
  const catalog = require('fs').readFileSync('platform-mcp/src/tools/catalog.ts','utf8');
  const catalogNames = [...catalog.matchAll(/name:\s*['\"]([^'\"]+)['\"]/g)].map(m => m[1]);
  console.log('Catalog entries:', catalogNames.length, catalogNames);
"
```

The 18 missing are the TR additions: query_transits_over_natal, query_yogas_active_now, get_planet_avastha, get_shadbala_full, query_drekkana_drishti, query_jaimini_chara_dasha, query_planetary_period_predictions, query_dasamsha_career, query_shashtiamsha, query_eclipse_transits, query_planet_war, query_remedies_prescribed, tara_balam_for_native, chandra_balam_for_native, muhurta_finder, query_varshphal (if name differs from existing), query_divisional_chart, query_remedial_mantras.

### Step 3 — Read existing catalog entry shape

```bash
head -60 platform-mcp/src/tools/catalog.ts
```

Each entry likely has: `name`, `description`, `inputSchema`, `category` or similar. Match the exact interface.

### Step 4 — Add 18 missing entries to catalog.ts

For each missing tool, read its tool file to extract the description and input schema, then add a catalog entry matching the existing interface pattern.

### Step 5 — Build 41 manifest entries for MCP

For each of the 41 MCP tools, add a manifest entry:
```json
{
  "canonical_id": "MCP_TOOL_<NAME_UPPER>",
  "type": "retrieval_tool",
  "channel": "mcp",
  "name": "<tool_name>",
  "path": "platform-mcp/src/tools/<file>.ts",
  "status": "CURRENT",
  "description": "<one line>",
  "input_schema_summary": "<key params>",
  "output_summary": "<what is returned>",
  "added_campaign": "universal-parity"
}
```

### Step 6 — Validate

```bash
node -e "
  const m = JSON.parse(require('fs').readFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json','utf8'));
  const mcp = m.entries.filter(e => e.channel === 'mcp' && e.type === 'retrieval_tool');
  console.log('MCP tools in manifest:', mcp.length);
"
```

```bash
node -e "
  const src = require('fs').readFileSync('platform-mcp/src/tools/catalog.ts','utf8');
  const names = [...src.matchAll(/name:\s*['\"]([^'\"]+)['\"]/g)].map(m => m[1]);
  console.log('Catalog entries:', names.length);
"
```

```bash
cd platform-mcp && npx tsc --noEmit 2>&1 | head -20
```

### Step 7 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
git add platform-mcp/src/tools/catalog.ts
git commit -m "feat(UDA-0-S3): register 41 MCP tools in manifest + complete catalog.ts

Manifest: 41 MCP tool entries added (channel=mcp, type=retrieval_tool)
catalog.ts: 18 missing TR tools added (was 23, now 41)
Total manifest entries: <N> (36 portal + 41 MCP + others)
TypeScript clean.

HAP-2: Halting for native review before UDA-1 (portal porting) begins."
```

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_0_S3_v1_0.md*
