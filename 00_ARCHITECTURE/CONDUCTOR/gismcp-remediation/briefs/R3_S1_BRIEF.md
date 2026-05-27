---
session_id: R3-S1
status: PENDING
phase: GISMCP-R3
title: "MSR grounding audit — count ungrounded signals, sample, produce audit doc"
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2
branch: fix/gismcp-r3
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/MSR_GROUNDING_AUDIT.md
must_not_touch:
  - platform/**
  - platform-mcp/**
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
  - supabase/**
  - "*.yaml"
---

# R3-S1: MSR Grounding State Audit

## Context

The MCP Transformation workstream (COMPLETE 2026-05-22) claimed "573/573 MSR signals grounded (100%)." Subsequent workstreams (DAR, Universal Parity Campaign) touched MSR data. This session audits the CURRENT state of grounding in the DB.

**Definition of grounded:** A signal record in the `msr_signals` table (or equivalent) has a non-null, non-empty `source_citation` field containing at least one FORENSIC fact ID (format: `FORENSIC.*` or `LEL.EV.*`).

---

## Step 1: Identify the MSR table schema

```sql
-- Find the MSR table
SELECT table_name FROM information_schema.tables 
WHERE table_name ILIKE '%msr%' OR table_name ILIKE '%signal%'
ORDER BY table_name;

-- Get its schema
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns
WHERE table_name = '<msr_table_name>'
ORDER BY ordinal_position;
```

Look for columns like: `signal_id`, `signal_code`, `source_citation`, `grounding`, `forensic_refs`, `derivation`. Record the exact column names.

---

## Step 2: Count grounded vs ungrounded

```sql
-- Total signals
SELECT COUNT(*) as total FROM <msr_table>;

-- Grounded (source_citation is non-null and non-empty)
SELECT COUNT(*) as grounded 
FROM <msr_table>
WHERE source_citation IS NOT NULL 
  AND source_citation != ''
  AND source_citation != '{}';

-- Ungrounded
SELECT COUNT(*) as ungrounded 
FROM <msr_table>
WHERE source_citation IS NULL 
   OR source_citation = ''
   OR source_citation = '{}';
```

If the column name is different (e.g., `forensic_refs`, `grounding_refs`), adjust accordingly.

---

## Step 3: Sample 20 ungrounded signals (if any)

```sql
SELECT signal_id, signal_code, description, source_citation
FROM <msr_table>
WHERE source_citation IS NULL OR source_citation = '' OR source_citation = '{}'
LIMIT 20;
```

---

## Step 4: Sample 5 well-grounded signals (for reference)

```sql
SELECT signal_id, signal_code, source_citation
FROM <msr_table>
WHERE source_citation IS NOT NULL AND source_citation != ''
LIMIT 5;
```

---

## Step 5: Write MSR_GROUNDING_AUDIT.md

Create `00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/MSR_GROUNDING_AUDIT.md`:

```markdown
---
audit_date: 2026-05-26
session: R3-S1
---

# MSR Grounding Audit

## Summary
- total_signals: <N>
- grounded_count: <N>
- ungrounded_count: <N>
- grounding_percentage: <X>%
- status: COMPLETE (if ungrounded=0) | REMEDIATION_REQUIRED (if ungrounded>0)

## Table Info
- table_name: <actual table name>
- source_citation_column: <actual column name>
- schema_snapshot: [paste SELECT column_name result]

## Ungrounded Signal Sample (first 20)
[paste results from Step 3, or "NONE — all 573 grounded"]

## Grounded Signal Sample (reference)
[paste 5 examples showing expected source_citation format]

## MCP Transformation Claim
- Claimed 100% grounding: true
- Current DB state matches claim: <true/false>
- Explanation of any gap: [if applicable, explain what changed post-MCPT]
```

---

## Step 6: Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2
git add 00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/MSR_GROUNDING_AUDIT.md
git commit -m "audit(R3): MSR grounding state — <X>/573 signals grounded

Closes R3-S1 per GISMCP_REMEDIATION_PLAN_v1_0 §4"
```

## Acceptance Criteria

1. `test -f 00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/MSR_GROUNDING_AUDIT.md`
2. Audit doc contains `grounded_count:` field
3. Audit doc contains `ungrounded_count:` field
4. Audit doc contains `status:` field (COMPLETE or REMEDIATION_REQUIRED)
