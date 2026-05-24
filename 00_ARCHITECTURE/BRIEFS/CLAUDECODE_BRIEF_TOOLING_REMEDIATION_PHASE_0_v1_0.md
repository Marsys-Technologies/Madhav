---
artifact: CLAUDECODE_BRIEF_TOOLING_REMEDIATION_PHASE_0_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: PENDING
authored_by: Cowork (Claude Sonnet 4.6) 2026-05-24
authored_for_session: TR-P0-S1
session_id: TR-P0-S1
session_name: "Tooling Remediation Phase 0 — Pre-flight Diagnostic Baseline"
executor: Claude Code (VS Code extension / Antigravity IDE)
execution_mode: single session, --dangerously-skip-permissions
worktree:
  name: MadhavToolingFix
  branch: feature/tooling-remediation
  path_absolute: /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix
governing_plan: 00_ARCHITECTURE/CONDUCTOR/tooling-remediation/MARSYS_JIS_TOOLING_REMEDIATION_PLAN_v1_0.md
predecessor_session: none (first session in workstream)
next_session_anticipated: TR-P1-S1 (Phase 1.1+1.2 — chart_summary + query_transit_event fixes)
---

# CLAUDECODE_BRIEF — TR-P0-S1
## Tooling Remediation Phase 0 — Pre-flight Diagnostic Baseline

**Purpose.** Before any code changes, capture the exact ground truth of what is broken,
what is empty, and what is mis-configured in the current prod MCP deployment. Every finding
in the 87-item audit must have a baseline measurement row in the tracker. The conductor's
Wave 1 briefs are written using this baseline — if Phase 0 is inaccurate, every downstream
brief will be calibrated to the wrong target.

---

## §0 — How to start this session

You are running inside the MadhavToolingFix worktree:

```bash
# Confirm position
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix
git status
# Expected: On branch feature/tooling-remediation, working tree clean

# Copy this brief as the active session dispatcher
cp 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_TOOLING_REMEDIATION_PHASE_0_v1_0.md CLAUDECODE_BRIEF.md
git add CLAUDECODE_BRIEF.md
git commit -m "TR-P0-S1: activate Phase 0 diagnostic brief"
```

Read CLAUDE.md (§C mandatory reading), then read this file fully before executing any step.
Execute all items in §3 in order. Commit after §3.4. Do not modify application code.

---

## §1 — Session identity

| Field | Value |
|---|---|
| session_id | TR-P0-S1 |
| wave | 0 |
| phase | 0 |
| branch | feature/tooling-remediation |
| worktree | /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix |
| may_touch | eval-results/**, 00_ARCHITECTURE/CONDUCTOR/tooling-remediation/**, 00_ARCHITECTURE/TOOLING_AUDIT_TRACKER_v1_0.md, CLAUDECODE_BRIEF.md |
| must_not_touch | platform/**, platform-mcp/**, python-sidecar/**, 025_HOLISTIC_SYNTHESIS/**, 01_FACTS_LAYER/**, .geminirules, CLAUDE.md |

---

## §2 — Context: what the diagnostic must answer

The `MARSYS_JIS_TOOLING_REMEDIATION_PLAN_v1_0.md` (in `00_ARCHITECTURE/CONDUCTOR/tooling-remediation/`)
identified 87 findings from the post-Sankalpa audit. The verification pass disputed 6 bugs as
being in the platform primitive rather than the MCP wrapper. Phase 0 resolves the disputes
by reproducing each failure in prod and tracing the exact layer where the bug lives.

Four questions this session must answer for every broken/partial tool:
1. Does the MCP tool respond at all? (schema-valid JSON response)
2. What is the exact error or wrong-value payload?
3. Which layer is the bug in? (MCP wrapper / platform primitive / DB data / prod env)
4. What is the DB row count for data-layer findings?

---

## §3 — Execution steps

### §3.1 — DB proxy setup

The prod DB is accessible via Cloud SQL Proxy. Start it:

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix
bash platform/scripts/start_db_proxy.sh &
sleep 5
# Proxy listens on 127.0.0.1:5433
# Credentials are in .env.local (DB_URL or POSTGRES_* vars)
```

Extract the DB connection string from `.env.local`:
```bash
grep -E 'DATABASE_URL|POSTGRES_' /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix/.env.local | head -5
```

Use `psql` throughout this session at `postgresql://...@127.0.0.1:5433/...`.

### §3.2 — MCP server availability check

The MCP sidecar runs in prod Cloud Run. The API key and endpoint are in `.env.local`.

```bash
grep -E 'MCP_|AMJIS_MCP' /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix/.env.local
```

Run a health check against the MCP server:
```bash
MCP_URL=$(grep MCP_SERVER_URL /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix/.env.local | cut -d= -f2)
MCP_KEY=$(grep MCP_API_KEY /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix/.env.local | cut -d= -f2)

curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $MCP_KEY" \
  "$MCP_URL/health"
# Expected: 200
```

If the MCP server is unreachable, record "MCP_UNREACHABLE" in the baseline and derive what you
can from direct DB queries. Do not halt — continue with §3.3.

### §3.3 — Observability tools baseline

**A. data_coverage** — call via MCP or directly if available in Claude Code's MCP client:

```bash
curl -s -X POST "$MCP_URL/mcp/v1/tools/data_coverage/invoke" \
  -H "Authorization: Bearer $MCP_KEY" \
  -H "Content-Type: application/json" \
  -d '{"tier":"super_admin","chart_id":"362f9f17-95a5-490b-a5a7-027d3e0efda0"}' \
  | tee /tmp/data_coverage_raw.json | jq '.'
```

**B. tool_health** — last 30 days:

```bash
curl -s -X POST "$MCP_URL/mcp/v1/tools/tool_health/invoke" \
  -H "Authorization: Bearer $MCP_KEY" \
  -H "Content-Type: application/json" \
  -d '{"days":30}' \
  | tee /tmp/tool_health_raw.json | jq '.'
```

Save both responses. If `data_coverage` returns a `tools_status` block, copy it verbatim into
the baseline. If it returns an error, record the error and continue.

### §3.4 — Per-tool minimal invocations (C1–C11)

For each tool below, run the minimal invocation and capture:
- `schema_valid`: did it return JSON without a top-level `error` key?
- `row_count` or `record_count` from the response (0 is a valid capture)
- `error_shape`: first 200 chars of any error message
- `layer_hypothesis`: one of `wrapper` / `primitive` / `data_empty` / `prod_env` / `unknown`

Use the native's chart_id `362f9f17-95a5-490b-a5a7-027d3e0efda0` for all calls unless noted.

```bash
CHART="362f9f17-95a5-490b-a5a7-027d3e0efda0"

# C1: chart_summary — audit says 0 rows always
curl -s -X POST "$MCP_URL/mcp/v1/tools/chart_summary/invoke" \
  -H "Authorization: Bearer $MCP_KEY" -H "Content-Type: application/json" \
  -d "{\"chart_id\":\"$CHART\",\"tier\":\"super_admin\"}" > /tmp/c1_chart_summary.json

# C2: holistic_bundle UCN/RM/CDLM sub-tools — audit says always error
curl -s -X POST "$MCP_URL/mcp/v1/tools/holistic_bundle/invoke" \
  -H "Authorization: Bearer $MCP_KEY" -H "Content-Type: application/json" \
  -d "{\"chart_id\":\"$CHART\",\"tier\":\"super_admin\",\"include_ucn\":true,\"include_rm\":true,\"include_cdlm\":true}" \
  > /tmp/c2_holistic_bundle.json

# C3: cross_school_lookup — audit says always silent
curl -s -X POST "$MCP_URL/mcp/v1/tools/cross_school_lookup/invoke" \
  -H "Authorization: Bearer $MCP_KEY" -H "Content-Type: application/json" \
  -d "{\"claim\":\"Jupiter lord of 9H gives dharmic career\",\"tier\":\"super_admin\"}" \
  > /tmp/c3_cross_school.json

# C4: query_signals — test that filters fire
curl -s -X POST "$MCP_URL/mcp/v1/tools/query_signals/invoke" \
  -H "Authorization: Bearer $MCP_KEY" -H "Content-Type: application/json" \
  -d "{\"chart_id\":\"$CHART\",\"tier\":\"super_admin\",\"forward_looking\":true,\"min_confidence\":0.8}" \
  > /tmp/c4_query_signals.json

# C5: query_ephemeris — test date_range
curl -s -X POST "$MCP_URL/mcp/v1/tools/query_ephemeris/invoke" \
  -H "Authorization: Bearer $MCP_KEY" -H "Content-Type: application/json" \
  -d "{\"date_range\":{\"from\":\"2026-06-01\",\"to\":\"2026-06-30\"},\"planets\":[\"Jupiter\",\"Saturn\"],\"tier\":\"super_admin\"}" \
  > /tmp/c5_query_ephemeris.json

# C6: query_transit_event — test event_type behaviour
curl -s -X POST "$MCP_URL/mcp/v1/tools/query_transit_event/invoke" \
  -H "Authorization: Bearer $MCP_KEY" -H "Content-Type: application/json" \
  -d "{\"planet\":\"Jupiter\",\"target\":\"natal_moon\",\"date_range\":{\"from\":\"2026-01-01\",\"to\":\"2027-01-01\"},\"tier\":\"super_admin\"}" \
  > /tmp/c6_query_transit_event.json

# C7: query_dasha_periods — check PD/SD presence
curl -s -X POST "$MCP_URL/mcp/v1/tools/query_dasha_periods/invoke" \
  -H "Authorization: Bearer $MCP_KEY" -H "Content-Type: application/json" \
  -d "{\"chart_id\":\"$CHART\",\"tier\":\"super_admin\"}" \
  > /tmp/c7_query_dasha.json

# C8: query_panchanga — check enrichment columns
curl -s -X POST "$MCP_URL/mcp/v1/tools/query_panchanga/invoke" \
  -H "Authorization: Bearer $MCP_KEY" -H "Content-Type: application/json" \
  -d "{\"date\":\"2026-05-24\",\"tier\":\"super_admin\"}" \
  > /tmp/c8_query_panchanga.json

# C9: read_asset — test MACRO_PLAN and LEL
curl -s -X POST "$MCP_URL/mcp/v1/tools/read_asset/invoke" \
  -H "Authorization: Bearer $MCP_KEY" -H "Content-Type: application/json" \
  -d "{\"canonical_id\":\"MACRO_PLAN\",\"tier\":\"super_admin\"}" \
  > /tmp/c9_read_asset_macro.json

curl -s -X POST "$MCP_URL/mcp/v1/tools/read_asset/invoke" \
  -H "Authorization: Bearer $MCP_KEY" -H "Content-Type: application/json" \
  -d "{\"canonical_id\":\"LEL\",\"tier\":\"super_admin\"}" \
  > /tmp/c9_read_asset_lel.json

# C10: read_classical_text — test chapter:verse lookup (will fail if not implemented)
curl -s -X POST "$MCP_URL/mcp/v1/tools/read_classical_text/invoke" \
  -H "Authorization: Bearer $MCP_KEY" -H "Content-Type: application/json" \
  -d "{\"text_id\":\"BPHS\",\"query\":\"Jupiter lord of 9H\",\"tier\":\"super_admin\"}" \
  > /tmp/c10_read_classical.json

# C11: query_chart_facts — test empty categories
curl -s -X POST "$MCP_URL/mcp/v1/tools/query_chart_facts/invoke" \
  -H "Authorization: Bearer $MCP_KEY" -H "Content-Type: application/json" \
  -d "{\"chart_id\":\"$CHART\",\"categories\":[\"deity_assignment\",\"ishta_kashta\",\"chandra_placement\",\"avastha\"],\"tier\":\"super_admin\"}" \
  > /tmp/c11_chart_facts_empty.json
```

For each `/tmp/cN_*.json` file, extract schema_valid, row_count, error_shape.

### §3.5 — DB data-layer counts

Run these queries against prod DB (via proxy at 5433):

```sql
-- D5: chart_facts row count per category
SELECT category, COUNT(*) as row_count
FROM chart_facts
GROUP BY category
ORDER BY row_count DESC;

-- D4: school_convergence_index per school × coverage_type
SELECT school, coverage_type, COUNT(*) as row_count
FROM school_convergence_index
GROUP BY school, coverage_type
ORDER BY school, coverage_type;

-- D6: rag_chunks by source and doc_type
SELECT source, doc_type, COUNT(*) as chunk_count
FROM rag_chunks
GROUP BY source, doc_type
ORDER BY chunk_count DESC;

-- Panchanga enrichment check (D for C8)
SELECT
  COUNT(*) as total_rows,
  COUNT(special_yogas) as has_special_yogas,
  COUNT(choghadiya) as has_choghadiya,
  COUNT(hora) as has_hora,
  COUNT(inauspicious) as has_inauspicious,
  COUNT(auspicious) as has_auspicious
FROM panchanga_daily
WHERE date >= '2026-01-01';
```

Save the output of each query to `/tmp/db_counts.txt`.

### §3.6 — Compile the baseline JSON

Create `eval-results/` directory if it doesn't exist.
Write `/Users/Dev/Vibe-Coding/Apps/MadhavToolingFix/eval-results/tooling_audit_baseline_20260524.json`
with this structure (populate each field from the data gathered above):

```json
{
  "captured_at": "2026-05-24",
  "mcp_server_reachable": true,
  "data_coverage_response": "<raw or error>",
  "tool_health_response": "<raw or error>",
  "tool_tests": {
    "C1_chart_summary": {
      "schema_valid": false,
      "row_count": 0,
      "error_shape": "<first 200 chars>",
      "layer_hypothesis": "primitive|wrapper|data_empty|prod_env|unknown"
    },
    "C2_holistic_bundle_ucn_rm_cdlm": { ... },
    "C3_cross_school_lookup": { ... },
    "C4_query_signals_filters": { ... },
    "C5_query_ephemeris_date_range": { ... },
    "C6_query_transit_event": { ... },
    "C7_query_dasha_periods_pd_sd": { ... },
    "C8_query_panchanga_enrichment": { ... },
    "C9_read_asset_macro_plan": { ... },
    "C9_read_asset_lel": { ... },
    "C10_read_classical_text": { ... },
    "C11_chart_facts_empty_categories": { ... }
  },
  "db_counts": {
    "chart_facts_by_category": { "<category>": <count>, ... },
    "school_convergence_index_by_school_coverage": { "<school>:<coverage_type>": <count>, ... },
    "rag_chunks_by_source": { "<source>:<doc_type>": <count>, ... },
    "panchanga_enrichment_coverage": {
      "total_rows": 0,
      "has_special_yogas": 0,
      "has_choghadiya": 0,
      "has_hora": 0,
      "has_inauspicious": 0,
      "has_auspicious": 0
    }
  },
  "layer_decisions": {
    "C1_bug_layer": "wrapper|primitive|data_empty|prod_env",
    "C2_bug_layer": "...",
    "C3_bug_layer": "...",
    "C4_bug_layer": "...",
    "C5_bug_layer": "...",
    "C9_bug_layer": "...",
    "C11_bug_layer": "..."
  },
  "key_surprises": []
}
```

Use your judgment to fill `layer_decisions` based on the response shapes you observed.
`key_surprises` is a list of findings that contradict the plan's `§1 Verification result` — if the wrapper
is broken where the plan said it was correct, or data exists where the plan said empty, note it here.

### §3.7 — Write the tracker

Create `00_ARCHITECTURE/TOOLING_AUDIT_TRACKER_v1_0.md` with the following frontmatter and table:

```markdown
---
artifact: TOOLING_AUDIT_TRACKER_v1_0.md
version: 1.0
status: LIVING
phase_0_status: COMPLETE
authored_by: TR-P0-S1 (2026-05-24)
---

# MARSYS-JIS Tooling Audit Tracker

Source: MARSYS_JIS_TOOLING_REMEDIATION_PLAN_v1_0.md (87 findings).
Baseline captured: TR-P0-S1, 2026-05-24.

## §1 — Tool-behaviour findings (C1–C11)

| Code | Finding | Phase | Status | Baseline |
|---|---|---|---|---|
| C1 | chart_summary 0 rows | 1.1 | OPEN | <layer from baseline> |
| C2 | holistic_bundle UCN/RM/CDLM error | 5.1 | OPEN | <layer> |
| C3 | cross_school_lookup silent | 2.1 | OPEN | <layer> |
| C4 | query_signals filters ignored | 1.3 | OPEN | <layer> |
| C5 | query_ephemeris date_range | 1.4 | OPEN | <layer> |
| C6 | query_transit_event event_type missing | 1.2 | OPEN | confirmed wrapper |
| C7 | query_dasha_periods no PD/SD | 7.1 | OPEN | confirmed schema |
| C8 | query_panchanga missing enrichment cols | 1.6 | OPEN | <layer> |
| C9 | read_asset ENOENT | 1.5 | OPEN | <layer> |
| C10 | read_classical_text no citation lookup | 2.5 | OPEN | confirmed schema |
| C11 | query_chart_facts empty categories | 3.1 | OPEN | <row count from DB> |

## §2 — Data-layer findings (D1–D7)

| Code | Finding | Phase | Status | Baseline |
|---|---|---|---|---|
| D1 | deity_assignment/ishta_kashta/chandra_placement/avastha empty | 3.1 | OPEN | <row counts> |
| D2 | shadbala no roll-up | 6.4 | OPEN | confirmed schema |
| D3 | read_asset ENOENT in prod | 1.5 | OPEN | <same as C9> |
| D4 | school_convergence_index all silent | 2.1 | OPEN | <row count per school> |
| D5 | chart_facts 2717 row claim disputed | 3.4 | OPEN | <actual row count from DB> |
| D6 | rag_chunks 4589 claim unverified | 2.4 | OPEN | <actual count from DB> |
| D7 | only 4 classical texts indexed | 2.4 | OPEN | confirmed 4 |

## §3 — Missing tools (Class A — wrap existing engine)

| Tool | Phase | Status |
|---|---|---|
| query_varshphal | 4.1 | OPEN |
| query_divisional_chart | 4.2 | OPEN |
| query_remedial_mantras | 4.3 | OPEN |
| muhurta_finder | 4.4 | OPEN |
| tara_balam_for_native | 4.5 | OPEN |
| chandra_balam_for_native | 4.6 | OPEN |

## §4 — Missing tools (Class B — build engine)

| Tool | Phase | Status |
|---|---|---|
| query_transits_over_natal | 6.1 | OPEN |
| query_yogas_active_now | 6.2 | OPEN |
| get_planet_avastha | 6.3 | OPEN |
| get_shadbala_full | 6.4 | OPEN |
| query_planetary_period_predictions | 7.3 | OPEN |
| query_dasamsha_career | 7.4 | OPEN |
| query_shashtiamsha | 7.5 | OPEN |
| query_drekkana_drishti | 7.6 | OPEN |
| query_remedies_prescribed | 8.3 | OPEN |

## §5 — Missing tools (Class C — implement stub)

| Tool | Phase | Status |
|---|---|---|
| query_jaimini_chara_dasha | 7.2 | OPEN |
| query_eclipse_transits | 8.1 | OPEN |
| query_planet_war | 8.2 | OPEN |

## §6 — Missing tools (Class D — deferred / greenfield)

| Tool | Phase | Status |
|---|---|---|
| compute_synastry | 12.1 | DEFERRED (needs spouse data) |
| compute_business_chart | 12.2 | DEFERRED (needs founding data) |
| query_kp_horary | 12.3 | DEFERRED v1.1 |
| vastu_audit | 12.4 | DEFERRED v1.1 |
| numerology_sync | 12.5 | DEFERRED v1.1 |
| compute_progressions | 12.6 | DEFERRED v1.1 |

## §7 — Methodology (Part IV)

| Rule | Phase | Status |
|---|---|---|
| Session-start diagnostic (data_coverage + tool_health) | 10.1 | OPEN |
| No date estimation — use query_ephemeris | 10.2 | OPEN |
| log_prediction mandatory | 10.3 | OPEN |
| flag_disagreement on broken tools | 10.4 | OPEN |
| Cross-school required before high-confidence | 10.5 | OPEN |
| Pre-compute chart summary at session start | 10.6 | OPEN |
| vector_search + get_cgm_subgraph proactive | 10.7 | OPEN |
| Triangulate MSR→chart_facts→ephemeris | 10.8 | OPEN |
| Mark permanent / dasha-tied / transit-tied | 10.9 | OPEN |
| Re-read tool schemas before first use | 10.10 | OPEN |

## §8 — Server-level (Part V)

| Item | Phase | Status |
|---|---|---|
| Schema param honour-check | 9.1 | OPEN |
| Streaming / pagination for large responses | 9.2 | OPEN (also 5.4) |
| Better error messages | 9.3 | OPEN |
| list_available_assets endpoint | 9.4 | OPEN (also 1.5) |
| populated_count on every category | 9.5 | OPEN (also 3.5) |
| Composition recipes (3 for v1.0) | 9.6 | OPEN |
| Versioned corpus snapshots endpoint | 9.7 | OPEN |
| Tier surfacing in descriptions | 9.8 | OPEN |
| Multi-language Sanskrit output | 9.9 | OPEN |
| Real-time ephemeris computation | DEFERRED | out-of-scope v1.0 |
```

Populate the `Baseline` column in §1 and §2 from the measurements in §3.4 and §3.5.

### §3.8 — Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix
mkdir -p eval-results
git add eval-results/tooling_audit_baseline_20260524.json
git add 00_ARCHITECTURE/TOOLING_AUDIT_TRACKER_v1_0.md
git add CLAUDECODE_BRIEF.md
git commit -m "TR-P0-S1: Phase 0 diagnostic baseline — eval-results + tracker with 87 findings"
git push origin feature/tooling-remediation
```

---

## §4 — Acceptance criteria

| ID | Criterion | Gate method |
|---|---|---|
| AC.1 | `eval-results/tooling_audit_baseline_20260524.json` exists and is valid JSON | `python3 -c "import json,sys; json.load(open('eval-results/tooling_audit_baseline_20260524.json'))"` |
| AC.2 | Baseline captures schema_valid + error_shape for all 11 C-findings | `jq '.tool_tests | keys | length' eval-results/tooling_audit_baseline_20260524.json` = 12 (C9 has 2 entries) |
| AC.3 | DB counts captured for chart_facts, school_convergence_index, rag_chunks | `jq '.db_counts.chart_facts_by_category | length > 0' eval-results/tooling_audit_baseline_20260524.json` = true |
| AC.4 | Tracker exists with `phase_0_status: COMPLETE` | `grep -q 'phase_0_status: COMPLETE' 00_ARCHITECTURE/TOOLING_AUDIT_TRACKER_v1_0.md` |
| AC.5 | Commit pushed to origin | `git log --oneline -1` shows TR-P0-S1 commit |

---

## §5 — Gate command (conductor uses this)

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix && \
python3 -c "import json,sys; d=json.load(open('eval-results/tooling_audit_baseline_20260524.json')); sys.exit(0 if len(d.get('tool_tests',{})) >= 11 else 1)" && \
grep -q 'phase_0_status: COMPLETE' 00_ARCHITECTURE/TOOLING_AUDIT_TRACKER_v1_0.md
```

---

## §6 — FINAL_SUMMARY schema (emit at session end)

```
---FINAL_SUMMARY---
session_id: TR-P0-S1
status: PASS | HALT_NEEDS_HUMAN
mcp_reachable: true | false
tool_test_count: <N>  # should be 12
db_count_tables_captured: 3  # chart_facts, school_convergence_index, rag_chunks
chart_facts_total_rows: <N>
school_convergence_index_total_rows: <N>
rag_chunks_total_rows: <N>
key_surprises: <list any findings that contradict plan §1 verification>
layer_decisions_summary: |
  C1: primitive|wrapper|data_empty|prod_env
  C2: ...
  C3: ...
  C4: ...
  C5: ...
  C9: ...
  C11: ...
notes_for_orchestrator: <any info the conductor needs to adjust Wave 1 briefs>
---
```

---

*End of CLAUDECODE_BRIEF_TOOLING_REMEDIATION_PHASE_0_v1_0.md*
*Authored: 2026-05-24, Cowork session (Tooling Remediation kickoff).*
