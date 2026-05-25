---
title: "CLAUDECODE_BRIEF — Parity UDA-Q-S8: Quality Delta Verification Audit"
canonical_id: CLAUDECODE_BRIEF_PARITY_UDA_Q_S8
version: 1.0
status: CURRENT
phase: UDA-Q
session_id: UDA-Q-S8
campaign: universal-parity
branch: feature/universal-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavParity
requires_hap: HAP-1
---

# UDA-Q-S8 — Verify all 7 quality gaps are closed

## 1. Context

Sessions UDA-Q-S1 through UDA-Q-S7 implemented 7 quality backports. This session runs a programmatic audit to confirm all 7 gaps are closed before proceeding to manifest work (UDA-0). This is a VERIFICATION-ONLY session — no new implementation.

The 7 quality gaps addressed:
1. (S1) Portal query_dasha_periods: pratyantar/sookshma levels
2. (S2) Portal query_ephemeris: date_range/sample_step/return_changes_only/span_guard
3. (S3) Portal chart_facts_query: include_empty_counts/populated_count
4. (S4) MCP lel_query: chart_state + significance enum
5. (S5) MCP query_varshphal: year range support
6. (S6) Portal msr_sql: dasha_lord/valence/temporal_activation filters
7. (S7) MCP query_signals: LL.1 calibration

After this session, **HAP-1** fires — the conductor halts for native review before UDA-0 begins.

## 2. Scope

**may_touch:**
- `eval-results/UDA_Q_S8_QUALITY_AUDIT.json` (create)
- `eval-results/UDA_Q_S8_QUALITY_AUDIT.md` (create)

**must_not_touch:**
- Any `platform/` source files (verification only — no fixes in this session)
- Any `platform-mcp/` source files
- Governance files

If an audit check FAILS, write the failure to the JSON and halt — do NOT attempt to fix it. A fix requires a separate session amendment; write a HALT entry in `CONDUCTOR_HALT_LOG.md`.

## 3. Acceptance Criteria

- [ ] AC.1: JSON written to `eval-results/UDA_Q_S8_QUALITY_AUDIT.json`
- [ ] AC.2: `open_quality_gaps` array in JSON is EMPTY (length 0) — all 7 gaps confirmed closed
- [ ] AC.3: Each of the 7 checks is explicitly recorded as `status: "PASS"` or `status: "FAIL"` with evidence
- [ ] AC.4: Human-readable report at `eval-results/UDA_Q_S8_QUALITY_AUDIT.md`
- [ ] AC.5: Committed

## 4. Audit Checks (run each; record result)

### Check 1 — Portal dasha_periods: pratyantar/sookshma

```bash
grep -c "pratyantar\|sookshma" platform/src/lib/retrieve/query_dasha_periods.ts
```
PASS: count >= 2 (both terms present)

```bash
grep -c "computePratyantar\|sub_periods" platform/src/lib/retrieve/query_dasha_periods.ts
```
PASS: count >= 1

### Check 2 — Portal ephemeris: 4 new features

```bash
grep -c "date_range\|sample_step\|return_changes_only\|1825" platform/src/lib/retrieve/query_ephemeris.ts
```
PASS: count >= 4

### Check 3 — Portal chart_facts: include_empty_counts + populated_count

```bash
grep -c "include_empty_counts\|populated_count" platform/src/lib/retrieve/chart_facts_query.ts
```
PASS: count >= 2

### Check 4 — MCP lel_query: chart_state + significance enum

```bash
grep -c "chart_state" platform-mcp/src/tools/lel_query.ts
```
PASS: count >= 1

```bash
grep -c "major\|moderate\|minor" platform-mcp/src/tools/lel_query.ts
```
PASS: count >= 1

### Check 5 — MCP query_varshphal: year_start/year_end

```bash
grep -c "year_start\|year_end" platform-mcp/src/tools/query_varshphal.ts
```
PASS: count >= 2

### Check 6 — Portal msr_sql: new filters present

```bash
grep -c "dasha_lord\|valence\|temporal_activation" platform/src/lib/retrieve/msr_sql.ts
```
PASS: count >= 3

```bash
grep -c "LL.1\|ll1_weights\|calibrat" platform/src/lib/retrieve/msr_sql.ts
```
PASS: count >= 1 (calibration preserved)

### Check 7 — MCP query_signals: LL.1 calibration

```bash
grep -c "LL1_CONFIDENCE_FLOORS\|confidence.*floor\|calibrat" platform-mcp/src/tools/query_signals.ts
```
PASS: count >= 1

```bash
grep -c "confidence \* significance\|confidence\*significance" platform-mcp/src/tools/query_signals.ts
```
PASS: count >= 1 (weighted ordering)

### Check 8 — TypeScript compile clean (both)

```bash
cd platform && npx tsc --noEmit 2>&1 | grep -c "error TS" || echo "0"
```
PASS: 0 errors

```bash
cd ../platform-mcp && npx tsc --noEmit 2>&1 | grep -c "error TS" || echo "0"
```
PASS: 0 errors

## 5. Output JSON Structure

```json
{
  "session": "UDA-Q-S8",
  "audit_date": "<ISO date>",
  "git_sha": "<git rev-parse HEAD>",
  "checks": [
    {
      "id": 1,
      "description": "Portal dasha_periods: pratyantar/sookshma levels",
      "status": "PASS|FAIL",
      "evidence": "<grep count or relevant snippet>"
    },
    ...7 more...
  ],
  "typescript_portal_errors": 0,
  "typescript_mcp_errors": 0,
  "open_quality_gaps": [],
  "verdict": "ALL_CLEAR|GAPS_REMAIN"
}
```

If `verdict` is `GAPS_REMAIN`, write the failing check IDs to `open_quality_gaps` and add a HALT entry to `CONDUCTOR_HALT_LOG.md` before committing.

## 6. Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavParity
git add eval-results/UDA_Q_S8_QUALITY_AUDIT.json
git add eval-results/UDA_Q_S8_QUALITY_AUDIT.md
git commit -m "audit(UDA-Q-S8): quality delta verification — all 7 gaps PASS

S1 portal dasha PD/SD: PASS
S2 portal ephemeris enhancements: PASS
S3 portal chart_facts introspection: PASS
S4 MCP lel_query chart_state+enum: PASS
S5 MCP varshphal year range: PASS
S6 portal msr_sql filter enrichment: PASS
S7 MCP query_signals LL.1 calibration: PASS
TS portal errors: 0, TS MCP errors: 0

HAP-1: Halting for native review before UDA-0."
```

---

*End of CLAUDECODE_BRIEF_PARITY_UDA_Q_S8_v1_0.md*
