---
lane: <LANE-ID>
status: pending|investigating|verifying|receipted|rejected(n)|parked|merged
implementer_model: <model>
verifier_model: opus
attempts: 0
---

## Scope
<what this lane investigated, per BRIEF_PG-1 §F1>

## Findings summary
<count by class, headline finding>

## Evidence log
<pointers into pg1_findings_<lane>.jsonl>

## Receipt
```json
{"lane":"<LANE-ID>","verifier_model":"opus","diff_reviewed":"<sha>",
 "findings":{"emitted":N,"schema_valid":N,"evidence_complete":N},
 "assertions":{"script":"scripts/validate_findings.py","green":[],"red":[]},
 "scope_warden":"pass|fail","verdict":"ACCEPT|REJECT","diagnosis":""}
```
