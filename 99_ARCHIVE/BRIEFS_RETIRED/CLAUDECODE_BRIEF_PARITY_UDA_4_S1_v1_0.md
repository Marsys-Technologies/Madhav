---
session_id: UDA-4-S1
phase: UDA-4
title: "MSR citation scaffolds — top-50 ungrouped signals"
status: pending
---

# UDA-4-S1: MSR Citation Scaffolds — Top 50

## Goal
Add FORENSIC/LEL citation scaffolds to the 50 highest-significance MSR signals that
currently lack explicit source citations.

## Context
- MSR file: `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` (573 signals)
- Signals with citations have `forensic_ref:` or cite `FORENSIC §` or `LEL-` inline
- 419/573 signals are ungrouped (no explicit citation) per V1_3_AUDIT_QUEUE_v1_0.md
- Canonical FORENSIC data: `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md`

## Steps

1. Read `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md`. Identify the 50 signals with the highest
   `significance` scores that do NOT have any `forensic_ref:`, `FORENSIC §`, or `LEL-` citation.

2. For each of the 50 signals, add a citation scaffold. Format:
   ```
   forensic_ref: FORENSIC §<section> <!-- <brief description of what fact it maps to> -->
   ```
   Use the FORENSIC file to find the right section. If uncertain, add:
   ```
   forensic_ref: FORENSIC §PENDING <!-- requires manual verification -->
   ```
   Do NOT fabricate citations. Scaffolds with §PENDING are acceptable.

3. Write `00_ARCHITECTURE/MSR_CITATION_SCAFFOLDS_v1_0.md`:
   - List all 50 signals that received scaffolds
   - Format: MSR.NNN | signal summary | assigned_forensic_ref | confidence (confirmed|pending)

4. Commit:
   ```bash
   git add 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md 00_ARCHITECTURE/MSR_CITATION_SCAFFOLDS_v1_0.md
   git commit -m "governance(uda4): UDA-4-S1 — MSR citation scaffolds top-50 ungrouped signals"
   ```

## Acceptance criteria
- MSR_CITATION_SCAFFOLDS_v1_0.md exists with ≥50 MSR.NNN entries
- grep -c 'forensic_ref' 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md returns ≥50
