---
audit_date: 2026-05-26
session: R3-S1
---

# MSR Grounding Audit

## Summary
- total_signals: 573
- grounded_count: 573
- ungrounded_count: 0
- grounding_percentage: 100%
- status: VERIFIED_NO_GAP
- verification_note: "MCP Transformation 100% grounding claim confirmed. No remediation needed."

## Table Info
- table_name: msr_signals
- source_citation_column: source_citation
- schema_snapshot:
  ```
   column_name          | data_type                | is_nullable
  ---------------------+--------------------------+-------------
   signal_id           | character varying        | NO
   native_id           | character varying        | NO
   domain              | character varying        | NO
   planet              | character varying        | YES
   house               | integer                  | YES
   nakshatra           | character varying        | YES
   dasha_lord          | character varying        | YES
   confidence          | numeric                  | NO
   significance        | numeric                  | NO
   is_forward_looking  | boolean                  | NO
   claim_text          | text                     | NO
   classical_basis     | text                     | YES
   falsifier           | text                     | YES
   source_file         | character varying        | NO
   source_version      | character varying        | NO
   ingested_at         | timestamp with time zone | NO
   signal_type         | text                     | YES
   temporal_activation | text                     | YES
   valence             | text                     | YES
   entities_involved   | jsonb                    | YES
   supporting_rules    | jsonb                    | YES
   rpt_deep_dive       | text                     | YES
   v6_ids_consumed     | jsonb                    | YES
   prior_id            | text                     | YES
   source_citation     | text                     | YES
   grounded_at         | timestamp with time zone | YES
   grounded_by         | text                     | YES
  ```

## Ungrounded Signal Sample (first 20)
NONE — all 573 signals are grounded

## Grounded Signal Sample (reference)
```
  signal_id  | source_citation
-------------+----------------------------------------------------------
 SIG.MSR.004 | FORENSIC §3.2 (Moon in Aquarius 11H)
 SIG.MSR.014 | FORENSIC §2 (Sun in Capricorn 10H)
 SIG.MSR.449 | FORENSIC §3.5 (Jupiter in Sagittarius 9H own-sign)
 SIG.MSR.023 | FORENSIC §3.3 (Mars in Aries 1H Lagna)
 SIG.MSR.032 | FORENSIC §7.7 (7H Libra: Saturn exalted — relationships)
```

## MCP Transformation Claim
- Claimed 100% grounding: true
- Current DB state matches claim: true
- Explanation of any gap: None — all 573 signals have non-null, non-empty source_citation values referencing FORENSIC fact sections. MCP Transformation claim confirmed valid. No subsequent workstream (DAR, Universal Parity Campaign) introduced any grounding regression.
