---
title: "CLAUDECODE_BRIEF — Parity Campaign UDA-0-S2: Manifest Register all 36 portal RETRIEVAL_TOOLS"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_0_S2
version: 1.0
status: CURRENT
phase: UDA-0
session_id: UDA-0-S2
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
authored_by: Conductor (2026-05-25)
---

# UDA-0-S2 — Manifest: Register all 36 portal RETRIEVAL_TOOLS

## 1. Context

`CAPABILITY_MANIFEST.json` currently has very few portal retrieval tool entries. This session
registers all 36 tools from `platform/src/lib/retrieve/index.ts` `RETRIEVAL_TOOLS` array as
`channel: "portal"`, `type: "retrieval_tool"` entries with correct paths and metadata.

The 36 portal tools are (from the index.ts file header comment):
msr_sql, pattern_register, resonance_register, cluster_atlas, contradiction_register, temporal,
query_msr_aggregate, cgm_graph_walk, manifest_query, vector_search, kp_query, saham_query,
divisional_query, chart_facts_query, cross_varga_dignity_query, domain_report_query,
remedial_codex_query, timeline_query, query_signal_state, query_kp_ruling_planets,
query_varshaphala, lel_query, classical_text_search_tool, classical_attribution_lookup_tool,
multi_school_signal_lookup_tool, convergence_score_lookup_tool, query_ephemeris, query_panchanga,
query_transit_event, query_dasha_periods, query_muhurat, query_jaimini_drishti, query_v7_additions,
query_ucn_walk, query_cdlm_lookup, query_rm_walk.

---

## 2. Scope

**may_touch:**
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`

**must_not_touch:**
- Any files under `platform/` or `platform-mcp/`
- Any governance files

---

## 3. Acceptance Criteria

- [ ] AC.0_2.1: `CAPABILITY_MANIFEST.json` has ≥ 36 entries with `channel: "portal"` AND `type: "retrieval_tool"`
- [ ] AC.0_2.2: Each portal tool entry has `canonical_id`, `path` (pointing to its `.ts` file), `channel: "portal"`, `type: "retrieval_tool"`, `status: "CURRENT"`, `version: "1.0"`
- [ ] AC.0_2.3: No duplicate `canonical_id` values (verify with dedup check)
- [ ] AC.0_2.4: `CAPABILITY_MANIFEST.json` is valid JSON
- [ ] AC.0_2.5: Commit message contains `UDA-0-S2`

---

## 4. Step-by-Step Execution

### Step 1 — Extract all portal tool names and paths

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity

# Get the RETRIEVAL_TOOLS array names from index.ts
node -e "
  const src = require('fs').readFileSync('platform/src/lib/retrieve/index.ts','utf8');
  // Extract tool file names from imports
  const imports = src.match(/from '\.\/([\w_]+)'/g) || [];
  const names = imports.map(m => m.replace(/from '\.\//, '').replace(/'/, ''));
  const unique = [...new Set(names)].filter(n => n !== 'types' && n !== 'tool_catalogue');
  console.log(unique.join('\n'));
"
```

Then verify each file exists:
```bash
for name in msr_sql pattern_register resonance_register cluster_atlas contradiction_register temporal query_msr_aggregate cgm_graph_walk manifest_query vector_search kp_query saham_query divisional_query chart_facts_query cross_varga_dignity_query domain_report_query remedial_codex_query timeline_query query_signal_state query_kp_ruling_planets query_varshaphala lel_query classical_text_search_tool classical_attribution_lookup_tool multi_school_signal_lookup_tool convergence_score_lookup_tool query_ephemeris query_panchanga query_transit_event query_dasha_periods query_muhurat query_jaimini_drishti query_v7_additions query_ucn_walk query_cdlm_lookup query_rm_walk; do
  test -f "platform/src/lib/retrieve/${name}.ts" && echo "OK: $name" || echo "MISSING: $name"
done
```

### Step 2 — Read current manifest

```bash
node -e "
  const m = JSON.parse(require('fs').readFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json','utf8'));
  const existing = m.entries.filter(e => e.channel === 'portal' && e.type === 'retrieval_tool').map(e => e.canonical_id);
  console.log('existing portal tools:', existing.length);
  console.log(existing.join('\n'));
"
```

### Step 3 — Build new entries for missing tools

For each portal tool not yet registered, add an entry like:

```json
{
  "canonical_id": "PORTAL_TOOL_MSR_SQL",
  "path": "platform/src/lib/retrieve/msr_sql.ts",
  "channel": "portal",
  "type": "retrieval_tool",
  "tool_name": "msr_sql",
  "status": "CURRENT",
  "version": "1.0",
  "description": "MSR signal retrieval from msr_signals table with LL.1 calibration"
}
```

Use a Node.js script to automate this:

```bash
node -e "
  const fs = require('fs');
  const m = JSON.parse(fs.readFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json','utf8'));

  const tools = [
    { name: 'msr_sql', desc: 'MSR signals with LL.1 calibration, domain floors, Pancha-MP dedup' },
    { name: 'pattern_register', desc: 'Cross-domain pattern registry lookup' },
    { name: 'resonance_register', desc: 'Signal resonance patterns' },
    { name: 'cluster_atlas', desc: 'Signal cluster atlas' },
    { name: 'contradiction_register', desc: 'Contradictions and tensions between signals' },
    { name: 'temporal', desc: 'Vedic temporal data: sade sati, eclipses, retrogrades, dasha chain' },
    { name: 'query_msr_aggregate', desc: 'MSR signal aggregates by domain/planet' },
    { name: 'cgm_graph_walk', desc: 'CGM causal graph walk' },
    { name: 'manifest_query', desc: 'Manifest capability query' },
    { name: 'vector_search', desc: 'Semantic similarity search over rag_chunks' },
    { name: 'kp_query', desc: 'KP sub-lord + significator data' },
    { name: 'saham_query', desc: 'Arabic parts (Saham) data' },
    { name: 'divisional_query', desc: 'Divisional chart positions (D1–D60)' },
    { name: 'chart_facts_query', desc: 'Chart facts: strengths, BAV, placements, yogas' },
    { name: 'cross_varga_dignity_query', desc: 'Cross-divisional dignity surface D1/D9/D10' },
    { name: 'domain_report_query', desc: 'Domain-specific astrological reports' },
    { name: 'remedial_codex_query', desc: 'Remedial measures codex lookup' },
    { name: 'timeline_query', desc: 'Dasha arc timeline from rag_chunks (structural L5)' },
    { name: 'query_signal_state', desc: 'Signal state surface M3-B' },
    { name: 'query_kp_ruling_planets', desc: 'KP ruling planets substrate + Varshaphala' },
    { name: 'query_varshaphala', desc: 'Varshaphala annual chart with year_start/year_end range' },
    { name: 'lel_query', desc: 'Life Event Log ground-truth events from life_events table' },
    { name: 'classical_text_search_tool', desc: 'Classical corpus search' },
    { name: 'classical_attribution_lookup_tool', desc: 'Classical attribution lookup' },
    { name: 'multi_school_signal_lookup_tool', desc: 'Multi-school signal triangulation' },
    { name: 'convergence_score_lookup_tool', desc: 'School convergence score lookup' },
    { name: 'query_ephemeris', desc: 'Date-indexed planetary positions from ephemeris_daily' },
    { name: 'query_panchanga', desc: 'Daily panchanga: tithi, vara, nakshatra, yoga, karana' },
    { name: 'query_transit_event', desc: 'Transit event search: when does X happen?' },
    { name: 'query_dasha_periods', desc: 'Vimshottari dasha schedule with PD/SD sub-period support' },
    { name: 'query_muhurat', desc: 'Muhurta sidecar wrapper' },
    { name: 'query_jaimini_drishti', desc: 'Jaimini Drishti sidecar wrapper' },
    { name: 'query_v7_additions', desc: 'V7 additions sidecar wrapper' },
    { name: 'query_ucn_walk', desc: 'UCN structural graph walk' },
    { name: 'query_cdlm_lookup', desc: 'CDLM cross-domain linkage matrix lookup' },
    { name: 'query_rm_walk', desc: 'RM remedial map walk' },
  ];

  const existingIds = new Set(m.entries.map(e => e.canonical_id));

  tools.forEach(t => {
    const id = 'PORTAL_TOOL_' + t.name.toUpperCase();
    if (!existingIds.has(id)) {
      m.entries.push({
        canonical_id: id,
        path: 'platform/src/lib/retrieve/' + t.name + '.ts',
        channel: 'portal',
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
  const portalTools = m.entries.filter(e => e.channel === 'portal' && e.type === 'retrieval_tool');
  console.log('portal retrieval_tools now:', portalTools.length);
"
```

### Step 4 — Verify count

```bash
node -e "
  const m = JSON.parse(require('fs').readFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json','utf8'));
  const portalTools = m.entries.filter(e => e.channel === 'portal' && e.type === 'retrieval_tool');
  console.log('portal retrieval_tools:', portalTools.length, '(expected: >= 36)');
  if (portalTools.length < 36) process.exit(1);
  console.log('GATE_UDA_0_S2_COUNT: PASS (' + portalTools.length + ')');
"
```

### Step 5 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
git commit -m "feat(UDA-0-S2): register all 36 portal RETRIEVAL_TOOLS in CAPABILITY_MANIFEST

Portal tools: 36 entries with channel=portal, type=retrieval_tool."
```

---

## 5. Gate Commands

```bash
node -e "
  const m = JSON.parse(require('fs').readFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json','utf8'));
  const portalTools = m.entries.filter(e => e.channel === 'portal' && e.type === 'retrieval_tool');
  if (portalTools.length < 36) {
    console.error('GATE_UDA_0_S2_COUNT: FAIL — found ' + portalTools.length + ', expected 36');
    process.exit(1);
  }
  console.log('GATE_UDA_0_S2_COUNT: PASS (' + portalTools.length + ' portal tools)');
"

git log --oneline -3 | grep -q 'UDA-0-S2' && echo 'GATE_UDA_0_S2_COMMIT: PASS'
```

All 2 gates must print PASS.

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_0_S2_v1_0.md*
