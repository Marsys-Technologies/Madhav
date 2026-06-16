---
title: "CLAUDECODE_BRIEF — Parity Campaign PRE-S1: Diagnostic Baseline"
canonical_id: CLAUDECODE_BRIEF_PARITY_PRE_S1
version: 1.0
status: CURRENT
phase: PRE
session_id: PRE-S1
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
authored_by: Cowork (Abhisek session 2026-05-25)
---

# PRE-S1 — Diagnostic Baseline

## 1. Context

This is the first session of the Universal Parity Campaign. No implementation in this session. Pure diagnostic: establish the exact pre-campaign state of all retrieval tools across all three channels, capture counts, detect any drift since the planning investigation, and write the baseline JSON file that TEST-0-S2 will compare against at campaign end.

Channels:
- **A + B (portal)**: `platform/src/lib/retrieve/index.ts` — RETRIEVAL_TOOLS array (both Classic Marsys planner and Claude-style agentic loop share this)
- **C (MCP)**: `platform-mcp/src/server.ts` — registered tools + `platform-mcp/src/tools/catalog.ts`
- **Manifest**: `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`

The output of this session is `eval-results/parity_baseline_pre_campaign.json`.

---

## 2. Scope

**may_touch:**
- `eval-results/parity_baseline_pre_campaign.json` (create)
- `eval-results/PRE_S1_DIAGNOSTIC_REPORT.md` (create)

**must_not_touch:**
- Any file under `platform/` (no implementation changes)
- Any file under `platform-mcp/` (no implementation changes)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (audit only, no writes)
- `CLAUDE.md`, `CURRENT_STATE_v1_0.md`, `SESSION_LOG.md` (governance files — do not touch)

---

## 3. Acceptance Criteria

- [ ] AC.PRE.1: `eval-results/parity_baseline_pre_campaign.json` exists and is valid JSON
- [ ] AC.PRE.2: JSON contains `portal_tools` array with exactly the count of tools exported from `platform/src/lib/retrieve/index.ts`
- [ ] AC.PRE.3: JSON contains `mcp_tools_registered` array from `platform-mcp/src/server.ts` import list
- [ ] AC.PRE.4: JSON contains `mcp_catalog_entries` array from `platform-mcp/src/tools/catalog.ts`
- [ ] AC.PRE.5: JSON contains `manifest_tool_entries` count from `CAPABILITY_MANIFEST.json`
- [ ] AC.PRE.6: JSON contains `gap_analysis` section: portal_only[], mcp_only[], shared[], mcp_catalog_missing[]
- [ ] AC.PRE.7: JSON contains `quality_delta` section with per-tool notes for shared tools
- [ ] AC.PRE.8: `eval-results/PRE_S1_DIAGNOSTIC_REPORT.md` written with human-readable summary matching JSON
- [ ] AC.PRE.9: All counts verified against actual file content (grep counts, not assumptions)

---

## 4. Step-by-Step Execution

### Step 1 — Count portal tools

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
# Count exported tool names from RETRIEVAL_TOOLS
grep -c "name:" platform/src/lib/retrieve/index.ts || \
  node -e "
    const src = require('fs').readFileSync('platform/src/lib/retrieve/index.ts','utf8');
    const matches = src.match(/name:\s*['\"][^'\"]+['\"]/g);
    console.log('portal_tool_count:', matches ? matches.length : 0);
  "
```

Then extract all tool names:
```bash
grep "name:" platform/src/lib/retrieve/index.ts | grep -v "//" | sed "s/.*name: *['\"]//;s/['\"].*//"
```

### Step 2 — Count MCP registered tools

```bash
grep "^import { register" platform-mcp/src/server.ts | sed "s/.*register//;s/ .*//"
```

Count: `grep -c "^import { register" platform-mcp/src/server.ts`

### Step 3 — Count MCP catalog entries

```bash
grep "name:" platform-mcp/src/tools/catalog.ts | grep -v "//" | wc -l
```

Extract names:
```bash
grep "name:" platform-mcp/src/tools/catalog.ts | grep -v "//" | sed "s/.*name: *['\"]//;s/['\"].*//"
```

### Step 4 — Count manifest tool entries

```bash
node -e "
  const m = JSON.parse(require('fs').readFileSync('00_ARCHITECTURE/CAPABILITY_MANIFEST.json','utf8'));
  const tools = m.entries.filter(e => e.type === 'tool' || (e.canonical_id || '').includes('TOOL'));
  console.log('manifest_tool_entries:', tools.length);
"
```

### Step 5 — Compute gap analysis

From the sets identified in Steps 1–3:
- `portal_only` = portal tool names NOT in MCP registered tools (name-normalized)
- `mcp_only` = MCP registered tools NOT in portal (name-normalized, strip `query_` prefix where needed for comparison)
- `shared` = intersection
- `mcp_catalog_missing` = MCP registered tools NOT in catalog.ts

### Step 6 — Write baseline JSON

Write to `eval-results/parity_baseline_pre_campaign.json`:

```json
{
  "campaign": "universal-parity",
  "baseline_date": "<ISO date>",
  "session": "PRE-S1",
  "git_sha": "<git rev-parse HEAD>",
  "portal_tools": {
    "count": <N>,
    "names": [...]
  },
  "mcp_tools_registered": {
    "count": <N>,
    "names": [...]
  },
  "mcp_catalog_entries": {
    "count": <N>,
    "names": [...]
  },
  "manifest_tool_entries": {
    "count": <N>
  },
  "gap_analysis": {
    "portal_only": [...],
    "mcp_only": [...],
    "shared": [...],
    "mcp_catalog_missing": [...]
  },
  "quality_delta": {
    "mcp_ahead": [
      {"tool": "query_dasha_periods", "gap": "portal missing PD/SD levels (pratyantar/sookshma)"},
      {"tool": "query_ephemeris", "gap": "portal missing date_range struct, sample_step, return_changes_only, 1825-day guard"},
      {"tool": "query_chart_facts", "gap": "portal missing include_empty_counts and populated_count annotation"},
      {"tool": "query_signals", "gap": "portal missing dasha_lord, valence, temporal_activation filters"}
    ],
    "portal_ahead": [
      {"tool": "lel_query", "gap": "MCP omits chart_state column; uses float significance, not enum"},
      {"tool": "query_varshaphala", "gap": "MCP single year only, portal supports year_start/year_end range"},
      {"tool": "msr_sql", "gap": "MCP uncalibrated; portal has LL.1 domain-specific confidence floors"}
    ],
    "at_parity": []
  },
  "target_state": {
    "portal_tools_expected": "<N + 12 new Class B engines>",
    "mcp_tools_expected": "<N + 14 portal-only tools>",
    "manifest_tool_entries_expected": "<77 total: 36 portal + 41 MCP>",
    "quality_gaps_expected": 0
  }
}
```

### Step 7 — Write human-readable report

Write `eval-results/PRE_S1_DIAGNOSTIC_REPORT.md` with:
- Section per channel showing tool counts + list
- Gap analysis table (portal_only, mcp_only, shared)
- Quality delta table (MCP ahead, portal ahead)
- Target state summary
- Explicit confirmation of 6 known HAPs ahead

### Step 8 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add eval-results/parity_baseline_pre_campaign.json
git add eval-results/PRE_S1_DIAGNOSTIC_REPORT.md
git commit -m "diag(PRE-S1): parity campaign diagnostic baseline

Portal tools: <N>
MCP registered: <N>
MCP catalog entries: <N> (gap: <M> missing)
Manifest tool entries: <N>
Portal-only: <N> tools (not in MCP)
MCP-only: <N> tools (not in portal)
Shared: <N> tools
Quality gaps: 7 identified (4 MCP-ahead, 3 portal-ahead)"
```

---

## 5. Gate Commands

The conductor verifies these pass before marking PRE-S1 complete and queuing UDA-Q-S1:

```bash
# Gate 1: baseline JSON exists and is valid
node -e "JSON.parse(require('fs').readFileSync('eval-results/parity_baseline_pre_campaign.json','utf8')); console.log('GATE_PRE_S1_JSON: PASS')"

# Gate 2: gap_analysis section present
node -e "
  const b = JSON.parse(require('fs').readFileSync('eval-results/parity_baseline_pre_campaign.json','utf8'));
  if (!b.gap_analysis || !b.quality_delta) throw new Error('missing sections');
  console.log('GATE_PRE_S1_SECTIONS: PASS');
"

# Gate 3: diagnostic report exists
test -f eval-results/PRE_S1_DIAGNOSTIC_REPORT.md && echo "GATE_PRE_S1_REPORT: PASS"

# Gate 4: committed
git log --oneline -1 | grep -q "PRE-S1" && echo "GATE_PRE_S1_COMMIT: PASS"
```

All 4 gates must print PASS.

---

*End of CLAUDECODE_BRIEF_PARITY_PRE_S1_v1_0.md*
