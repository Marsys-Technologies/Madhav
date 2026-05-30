---
artifact: RED_TEAM_MULTI_AYANAMSHA_BUILD_v1_0.md
document: Red-Team Plan — Multi-Ayanamsha Deterministic Build Orchestration
status: PENDING_NATIVE_REVIEW
version: 1.0
date: 2026-05-30
authored_by: Stream D Conductor (scope + attack surfaces; NOT yet executed)
operator_action_required: Native must execute IS.8(b) red-team review of this plan
---

# Red-Team Plan — Multi-Ayanamsha Deterministic Build

## §1 — Scope

This red-team covers the Multi-Ayanamsha Deterministic Build workstream, which spans:
- 22 per-chart asset writers (A1-A22)
- 6 META synthesis layers (α-ζ)
- UTEE cross-asset bridge matrix
- Build orchestration pipeline (Cloud Tasks → Cloud Run Jobs)
- ACC acceptance gates

## §2 — Attack Surfaces

### AS.1 — chart_facts contamination
Can chart_facts rows from one chart bleed into another chart's query results?
- Vector: missing `chart_id` filter in queries
- Test: INSERT rows with chart_id=A; query with chart_id=B; verify zero results
- Severity: Class 1 (data integrity)

### AS.2 — Ayanamsha filter bypass
Can an attacker (or buggy query) retrieve wrong-ayanamsha data?
- Vector: missing `ayanamsha_id` filter in MCP tool calls
- Test: Insert rows for ayanamsha_id='lahiri'; query with ayanamsha_id='krishnamurti'; verify zero results
- Severity: Class 1 (correctness)

### AS.3 — B.11 floor bypass
Can a query skip the L2.5 holistic synthesis layer?
- Vector: Direct chart_facts query without routing through MSR/CDLM/CGM
- Test: Call MCP tool `query_chart_facts_raw`; verify B.11 floor enforcement in response
- Severity: Class 2 (architectural)

### AS.4 — Narrative contamination in chart_facts
Can free-text narrative prose appear in `fact_value_text`?
- Vector: Writer inserting non-factual text
- Test: Scan `fact_value_text` for prose indicators (therefore, however, I believe, suggest)
- Severity: Class 1 (data quality)

### AS.5 — Concurrent build race condition
Can two concurrent builds for the same chart corrupt each other's chart_facts?
- Vector: Two builds with different build_ids writing to same (chart_id, ayanamsha_id) key
- Test: Trigger 2 builds simultaneously; verify chart_facts rows are keyed by build_id; verify supersedence logic
- Severity: Class 1 (data integrity)

### AS.6 — UTEE envelope NULL injection
Can a NULL UTEE column in vw_temporal_unified_lattice cause query failures?
- Vector: Missing event_iso on a temporal event row
- Test: Insert row with NULL event_iso; query vw_temporal_unified_lattice with date range; verify graceful NULL handling
- Severity: Class 2 (robustness)

### AS.7 — META divergence false positive storm
Can the divergence ledger writer produce an unbounded number of divergences?
- Vector: Ayanamsha comparison producing O(n²) divergences for n facts
- Test: Check `LIMIT 100` in scan_for_ayanamsha_divergences
- Severity: Class 2 (performance)

### AS.8 — Build pipeline secret exposure
Can the amjis-pipeline-db-url secret value be logged or exposed?
- Vector: Exception handlers logging connection strings
- Test: Grep writers for `logger.error(e)` patterns that might capture connection string
- Severity: Class 1 (security)

## §3 — Threat Model

| Threat | Likelihood | Impact | Priority |
|---|---|---|---|
| Cross-chart data contamination | Low (parameterized queries) | Critical | P1 |
| Ayanamsha filter bypass | Low (enforced in tool layer) | High | P1 |
| Narrative text in facts | Medium (writer discipline) | High | P1 |
| Concurrent build race | Low (build_id partitioning) | High | P1 |
| Secret exposure in logs | Low (exception handling discipline) | Critical | P1 |
| NULL propagation in views | Medium (COALESCE present) | Medium | P2 |
| Divergence storm | Low (LIMIT enforced) | Low | P3 |

## §4 — Operator Instructions

This artifact captures the red-team SCOPE. The native must execute the review per IS.8(b):
1. Execute each attack surface test manually or via `python platform/scripts/governance/red_team_probe.py --scope build_orchestrator`
2. Record findings as Class-1 (must-fix), Class-2 (should-fix), Class-3 (informational)
3. Zero Class-1 findings required before closing ACC3
4. Record findings in DISAGREEMENT_REGISTER_v1_0.md

**operator_action_pending**: Native red-team review required per IS.8(b). ACC3 is NOT blocking ACC4-ACC10.
