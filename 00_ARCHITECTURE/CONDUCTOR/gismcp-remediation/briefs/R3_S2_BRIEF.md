---
session_id: R3-S2
status: PENDING
phase: GISMCP-R3
title: "MSR grounding completion — remediate all ungrounded signals"
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2
branch: fix/gismcp-r3
may_touch:
  - 00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/MSR_GROUNDING_AUDIT.md
  - platform/scripts/**
must_not_touch:
  - platform/src/**
  - platform-mcp/**
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
  - "*.yaml"
---

# R3-S2: MSR Grounding Completion

## Context

This session is CONDITIONAL on R3-S1 finding ungrounded signals. Read `MSR_GROUNDING_AUDIT.md` first.

- If `ungrounded_count: 0` → mark STREAM2_COMPLETE, skip to R3-T1.
- If `ungrounded_count > 0` → complete grounding for all ungrounded signals in this session.

---

## If ungrounded_count = 0 (VERIFIED_NO_GAP path)

Update `MSR_GROUNDING_AUDIT.md` to add:
```yaml
status: VERIFIED_NO_GAP
verification_note: "MCP Transformation 100% grounding claim confirmed. No remediation needed."
```

Then commit and proceed to R3-T1.

---

## If ungrounded_count > 0 (REMEDIATION path)

### Step 1: Read MSR_v5_0.md

Read `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` — this is the canonical MSR document with all 573 signals and their derivation context. Each signal has a `signal_code`, `description`, `layer`, `source` section.

For each ungrounded signal (identified by signal_code from R3-S1 audit), find the corresponding entry in MSR_v5_0.md and extract:
- The FORENSIC fact IDs it references (look for planet names, house positions, yoga names)
- The LEL event IDs if any life events are cited

### Step 2: Read FORENSIC data for context

Read `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` to understand the fact ID numbering system (e.g., `FORENSIC.ASC.ARIES`, `FORENSIC.MOON.PISCES`, etc.).

### Step 3: Generate and execute grounding SQL

For each ungrounded signal, construct a citation string following the format used in the grounded examples from R3-S1.

```sql
-- Example update (adjust format to match grounded examples)
UPDATE msr_signals
SET source_citation = '["FORENSIC.MOON.PISCES", "FORENSIC.ASC.ARIES"]'::jsonb
WHERE signal_code = 'MSR.XXX';
```

If there are many ungrounded signals (>100), write a Python script at `platform/scripts/complete_msr_grounding.py` that:
1. Reads MSR_v5_0.md
2. Maps each ungrounded signal_code to its FORENSIC/LEL citations
3. Batch-updates the DB

Run via DB proxy:
```bash
DB_PROXY_PORT=5433 python3 platform/scripts/complete_msr_grounding.py 2>&1 | tail -30
```

### Step 4: Verify count after remediation

```sql
SELECT COUNT(*) as still_ungrounded 
FROM msr_signals
WHERE source_citation IS NULL OR source_citation = '' OR source_citation = '{}';
```

Expected: 0

### Step 5: Update audit doc

Update `MSR_GROUNDING_AUDIT.md`:
```yaml
status: REMEDIATION_COMPLETE
post_remediation_ungrounded_count: 0
remediation_method: "Manual citation mapping from MSR_v5_0.md to FORENSIC fact IDs"
```

### Step 6: Commit

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavGISMCP-S2
git add 00_ARCHITECTURE/CONDUCTOR/gismcp-remediation/MSR_GROUNDING_AUDIT.md
git add platform/scripts/  # if script was written
git commit -m "fix(R3): MSR grounding completion — all 573 signals now have source_citation

Closes R3-S2 per GISMCP_REMEDIATION_PLAN_v1_0 §4"
```

## Acceptance Criteria

1. `MSR_GROUNDING_AUDIT.md` contains either `VERIFIED_NO_GAP` or `REMEDIATION_COMPLETE`
2. DB query: `SELECT COUNT(*) FROM msr_signals WHERE source_citation IS NULL` → 0
3. Commit made
