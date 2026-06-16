---
title: "CLAUDECODE_BRIEF — Parity Campaign UDA-0-S3: Manifest Register all 41 MCP tools + fix catalog.ts"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_0_S3
version: 1.0
status: CURRENT
phase: UDA-0
session_id: UDA-0-S3
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
authored_by: Conductor (2026-05-25)
---

# UDA-0-S3 — Manifest: Register all 41 MCP tools + fix catalog.ts

## 1. Context

This session completes the manifest population by registering all MCP tools
(`platform-mcp/src/server.ts` registered tools) as `channel: "mcp"`, `type: "retrieval_tool"`
entries in `CAPABILITY_MANIFEST.json`. It also ensures `platform-mcp/src/tools/catalog.ts`
has entries for every registered tool.

The MCP tools registered in `server.ts` are (from the import list):
query_chart_facts, query_signals, query_dasha_periods, query_panchanga, query_ephemeris,
query_transit_event, lel_query, vector_search, get_cgm_subgraph, cross_school_lookup,
query_varshphal, query_divisional_chart, query_remedial_mantras, muhurta_finder,
tara_balam_for_native, chandra_balam_for_native, query_transits_over_natal,
query_yogas_active_now, get_planet_avastha, get_shadbala_full, interpret_current_dasha,
list_canonical_artifact_versions, query_drekkana_drishti, query_jaimini_chara_dasha,
query_planetary_period_predictions, query_dasamsha_career, query_shashtiamsha,
query_eclipse_transits, query_planet_war, query_remedies_prescribed, read_asset,
read_classical_text, list_assets, get_trace, list_recent_queries, log_prediction,
record_outcome, flag_disagreement, chart_summary, holistic_bundle, multi_school_bundle,
tool_health, data_coverage.

Count the exact number from server.ts imports and use that as the target.

After this session, HAP-2 fires and the native reviews the manifest before UDA-1 begins.

---

## 2. Scope

**may_touch:**
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`
- `platform-mcp/src/tools/catalog.ts` (add missing entries only)

**must_not_touch:**
- `platform-mcp/src/server.ts` (read only to count tools)
- Any files under `platform/`
- Any governance files

---

## 3. Acceptance Criteria

- [ ] AC.0_3.1: `CAPABILITY_MANIFEST.json` has ≥ 41 entries with `channel: "mcp"` AND `type: "retrieval_tool"`
- [ ] AC.0_3.2: Each MCP tool entry has `canonical_id`, `path`, `channel: "mcp"`, `type: "retrieval_tool"`, `status: "CURRENT"`, `version: "1.0"`
- [ ] AC.0_3.3: `platform-mcp/src/tools/catalog.ts` has ≥ 41 tool name entries
- [ ] AC.0_3.4: No duplicate `canonical_id` values in manifest
- [ ] AC.0_3.5: `cd platform-mcp && npx tsc --noEmit` passes with 0 errors
- [ ] AC.0_3.6: Commit message contains `UDA-0-S3`

---

## 4. Step-by-Step Execution

### Step 1 — Count MCP tools in server.ts

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
grep "^import { register" platform-mcp/src/server.ts | wc -l
grep "^import { register" platform-mcp/src/server.ts | sed "s/.*from '\.\///;s/\.js'.*//"
```

### Step 2 — Check current catalog.ts entries

```bash
grep "name:" platform-mcp/src/tools/catalog.ts | grep -v "//" | wc -l
grep "name:" platform-mcp/src/tools/catalog.ts | grep -v "//" | sed "s/.*name: *['\"]//;s/['\"].*//"
```

### Step 3 — Add missing MCP tools to manifest

```bash
node -e "
  const fs = require('fs');
  const m = JSON.parse(fs.readFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json','utf8'));

  const mcpTools = [
    { name: 'query_chart_facts', desc: 'Chart facts parametric retrieval: strengths, BAV, yogas, placements' },
    { name: 'query_signals', desc: 'MSR signal corpus lookup with LL.1 calibration' },
    { name: 'query_dasha_periods', desc: 'Vimshottari dasha schedule with PD/SD sub-period levels' },
    { name: 'query_panchanga', desc: 'Daily panchanga with enrichment fields' },
    { name: 'query_ephemeris', desc: 'Planetary positions from ephemeris_daily' },
    { name: 'query_transit_event', desc: 'Transit event search' },
    { name: 'lel_query', desc: 'Life Event Log ground-truth retrieval' },
    { name: 'vector_search', desc: 'Semantic search over rag_chunks' },
    { name: 'get_cgm_subgraph', desc: 'CGM causal graph subgraph' },
    { name: 'cross_school_lookup', desc: 'Cross-school signal triangulation' },
    { name: 'query_varshphal', desc: 'Varshaphala annual chart lookup' },
    { name: 'query_divisional_chart', desc: 'Divisional chart positions' },
    { name: 'query_remedial_mantras', desc: 'Remedial mantra corpus search' },
    { name: 'muhurta_finder', desc: 'Auspicious muhurta window finder' },
    { name: 'tara_balam_for_native', desc: 'Tara Bala (Star Strength) for native' },
    { name: 'chandra_balam_for_native', desc: 'Chandra Bala (Moon Strength) for native' },
    { name: 'query_transits_over_natal', desc: 'Transit-to-natal aspect windows' },
    { name: 'query_yogas_active_now', desc: 'Yoga activation status vs current dasha' },
    { name: 'get_planet_avastha', desc: 'Planetary avastha (state) lookup' },
    { name: 'get_shadbala_full', desc: 'Full Shadbala roll-up with classical minimums' },
    { name: 'interpret_current_dasha', desc: 'Current dasha interpretation' },
    { name: 'list_canonical_artifact_versions', desc: 'List canonical artifact versions' },
    { name: 'query_drekkana_drishti', desc: 'Jaimini Drekkana Drishti aspects' },
    { name: 'query_jaimini_chara_dasha', desc: 'Jaimini Chara Dasha schedule' },
    { name: 'query_planetary_period_predictions', desc: 'Classical predictions for MD/AD combinations' },
    { name: 'query_dasamsha_career', desc: 'D10 Dasamsha career analysis' },
    { name: 'query_shashtiamsha', desc: 'D60 Shashtiamsha karma analysis' },
    { name: 'query_eclipse_transits', desc: 'Eclipse detection in date range' },
    { name: 'query_planet_war', desc: 'Graha Yuddha planetary war detection' },
    { name: 'query_remedies_prescribed', desc: 'Remedial prescription cross-reference' },
    { name: 'read_asset', desc: 'Read a canonical L1/L2 asset file' },
    { name: 'read_classical_text', desc: 'Read classical text corpus chunks' },
    { name: 'list_assets', desc: 'List available canonical assets' },
    { name: 'get_trace', desc: 'Retrieve query trace by trace_id' },
    { name: 'list_recent_queries', desc: 'List recent MCP queries' },
    { name: 'log_prediction', desc: 'Log a time-indexed prediction' },
    { name: 'record_outcome', desc: 'Record an outcome against a prediction' },
    { name: 'flag_disagreement', desc: 'Flag a disagreement for governance review' },
    { name: 'chart_summary', desc: 'Chart summary holistic snapshot' },
    { name: 'holistic_bundle', desc: 'Holistic multi-layer synthesis bundle' },
    { name: 'multi_school_bundle', desc: 'Multi-school synthesis bundle' },
    { name: 'tool_health', desc: 'Tool health check' },
    { name: 'data_coverage', desc: 'Data coverage audit' },
  ];

  const existingIds = new Set(m.entries.map(e => e.canonical_id));

  mcpTools.forEach(t => {
    const id = 'MCP_TOOL_' + t.name.toUpperCase();
    if (!existingIds.has(id)) {
      m.entries.push({
        canonical_id: id,
        path: 'platform-mcp/src/tools/' + t.name + '.ts',
        channel: 'mcp',
        type: 'retrieval_tool',
        tool_name: t.name,
        status: 'CURRENT',
        version: '1.0',
        description: t.desc,
      });
      existingIds.add(id);
    }
  });

  fs.writeFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json', JSON.stringify(m, null, 2) + '\n');
  const mcpRegistered = m.entries.filter(e => e.channel === 'mcp' && e.type === 'retrieval_tool');
  console.log('mcp retrieval_tools now:', mcpRegistered.length);
"
```

### Step 4 — Check catalog.ts for missing entries

```bash
cat platform-mcp/src/tools/catalog.ts
```

If any registered tool is missing from `catalog.ts`, add it. The catalog format is typically:
```typescript
{ name: 'tool_name', description: '...', surgical: true|false, tier: [...] }
```

Add missing entries to the CATALOG array in `catalog.ts`.

### Step 5 — TypeScript compile check

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
cd platform-mcp && npx tsc --noEmit
```

### Step 6 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add 00_ARCHITECTURE/CAPABILITY_MANIFEST.json platform-mcp/src/tools/catalog.ts
git commit -m "feat(UDA-0-S3): register all MCP tools in CAPABILITY_MANIFEST + catalog.ts

MCP tools: <N> entries. catalog.ts: <N> entries. tsc: 0 errors.
HAP-2 gate artifact ready."
```

---

## 5. Gate Commands

```bash
node -e "
  const m = JSON.parse(require('fs').readFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json','utf8'));
  const mcpTools = m.entries.filter(e => e.channel === 'mcp' && e.type === 'retrieval_tool');
  if (mcpTools.length < 41) {
    console.error('GATE_UDA_0_S3_MANIFEST: FAIL — found ' + mcpTools.length + ', expected 41');
    process.exit(1);
  }
  console.log('GATE_UDA_0_S3_MANIFEST: PASS (' + mcpTools.length + ' MCP tools)');
"

node -e "
  const src = require('fs').readFileSync('platform-mcp/src/tools/catalog.ts','utf8');
  const names = src.match(/name:\s*['\"][^'\"]+['\"]/g) || [];
  if (names.length < 41) {
    console.error('GATE_UDA_0_S3_CATALOG: FAIL — found ' + names.length + ', expected 41');
    process.exit(1);
  }
  console.log('GATE_UDA_0_S3_CATALOG: PASS (' + names.length + ' entries)');
"

git log --oneline -3 | grep -q 'UDA-0-S3' && echo 'GATE_UDA_0_S3_COMMIT: PASS'
```

All 3 gates must print PASS.

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_0_S3_v1_0.md*
