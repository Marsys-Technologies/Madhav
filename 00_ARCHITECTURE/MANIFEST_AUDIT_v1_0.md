---
artifact: MANIFEST_AUDIT_v1_0.md
version: 1.0
status: CURRENT
authored_by: marsys-manifest-audit-scheduled
authored_at: 2026-05-21
---

# CAPABILITY_MANIFEST Audit Report

## entry_count reconciliation
Previous entry_count: 163
Actual entry count:   163
Fix applied: NO (already correct)

## Fingerprint audit summary
Entries checked: 163
PASS (fingerprint matches):   54
MISMATCH (fingerprint wrong): 12
MISSING (file not on disk):    0
SKIPPED (slug fingerprint):   97

## Mismatches (if any)
| canonical_id | path | stored_fingerprint (first 16) | actual_sha256 (first 16) |
|---|---|---|---|
| LEL | 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md | 2038964477623d41 | ced5f89ecdd19377 |
| 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/LL1_TWO_PASS_APPROVAL_v1_0 | 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/LL1_TWO_PASS_APPROVAL_v1_0.md | 2ad3a5b80577b6df | 93eb7d2b3bb6e0e7 |
| PATTERN_SCHEMA_v0_1 | 06_LEARNING_LAYER/SCHEMAS/pattern_schema_v0_1.json | d328860e1a98b639 | 55c23858f1bcca72 |
| PREDICTION_SCHEMA_v0_1 | 06_LEARNING_LAYER/SCHEMAS/prediction_schema_v0_1.json | 1db6a742f1fde195 | bf1189997a5d8e80 |
| TWO_PASS_EVENTS_SCHEMA_v0_1 | 06_LEARNING_LAYER/SCHEMAS/two_pass_events_schema_v0_1.json | 0ed502f6994726f3 | e7003c5911edd8f7 |
| PROMPT_REGISTRY_INDEX | 06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json | 74ffef4271ca6168 | ee986600a0eecf33 |
| PREDICTION_LEDGER_JSONL | 06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl | 47ac93ebb6449f8c | ac8a87cc55bbbe6d |
| PATTERN_REGISTER_JSON | 035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_v1_0.json | 729d850720a49863 | 11ed5d57d48c23a4 |
| RESONANCE_REGISTER_JSON | 035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_0.json | ac9f284bd591dc69 | 92a6cde8cb869ff0 |
| CONTRADICTION_REGISTER_JSON | 035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_0.json | 1e2fd304e400aee5 | 11c551afab85e627 |
| CLUSTER_ATLAS_JSON | 035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_0.json | 59d5d90c1759dce7 | fa1dbd13991f06f6 |
| DISCOVERY_REGISTERS_INDEX | 035_DISCOVERY_LAYER/REGISTERS/INDEX.json | f6891c9a2813a1e7 | dd3eb54f70c2adb1 |

## Missing files (if any)
None.

## Verdict
NEEDS_REVIEW — 12 mismatches found

### Notes on mismatch clusters
- **Discovery Layer registers (5 mismatches):** PATTERN_REGISTER_JSON, RESONANCE_REGISTER_JSON, CONTRADICTION_REGISTER_JSON, CLUSTER_ATLAS_JSON, DISCOVERY_REGISTERS_INDEX — all JSON registers in `035_DISCOVERY_LAYER/REGISTERS/`. These are living data files updated by ongoing sessions; fingerprint drift is expected but should be re-stamped at next session close.
- **Learning Layer schemas (3 mismatches):** PATTERN_SCHEMA_v0_1, PREDICTION_SCHEMA_v0_1, TWO_PASS_EVENTS_SCHEMA_v0_1 — schema files in `06_LEARNING_LAYER/SCHEMAS/` that may have been amended post-manifest-generation.
- **Learning Layer runtime files (2 mismatches):** PROMPT_REGISTRY_INDEX, PREDICTION_LEDGER_JSONL — both are append-only / actively-written files; fingerprint drift is expected.
- **LEL (1 mismatch):** LIFE_EVENT_LOG_v1_2.md — the Life Event Log is a LIVING document updated each session; fingerprint drift expected.
- **LL1_TWO_PASS_APPROVAL (1 mismatch):** A governance artifact that should be stable; warrants a targeted review to confirm whether amendment was intentional.
