---
session: DAR-P3-S10
date: 2026-05-25
contradiction_register: REBUILT
contradiction_register_count: 8
cluster_register: REBUILT
cluster_register_count: 12
pattern_register: REBUILT
pattern_register_count: 22
resonance_register: REBUILT
resonance_register_count: 12
school_signal_coverage_count: 4011
school_convergence_index: REFRESHED
school_convergence_index_count: 573
---

# Registers Rebuild Report — DAR-P3-S10

## Summary

All 4 L3 discovery registers rebuilt via `pipeline.ingest_l3_registers` (append-only swap semantics).
`school_signal_coverage` rebuilt via `platform/scripts/m9/run_coverage_audit.py` to 4,011 rows
(573 signals × 7 schools). `school_convergence_index` MV refreshed to 573 rows.

## Register Row Counts

| Table | Count | Source |
|---|---|---|
| contradiction_register | 8 | CONTRADICTION_REGISTER_v1_0.json (8 entries) |
| cluster_register | 12 | CLUSTER_ATLAS_v1_0.json (12 entries) |
| pattern_register | 22 | PATTERN_REGISTER_v1_0.json (22 entries) |
| resonance_register | 12 | RESONANCE_REGISTER_v1_0.json (12 entries) |
| school_signal_coverage | 4011 | 573 signals × 7 schools (run_coverage_audit.py) |
| school_convergence_index | 573 | REFRESH MATERIALIZED VIEW (one row per signal) |

## Anomalies

### Orphaned stale row removed from school_signal_coverage

Pre-existing artefact: `SIG.MSR.497 × tajika` was present from an earlier build (signal 497 is a
known gap in msr_signals — present in the old 514-signal universe but excluded from MSR v5.0).
The `run_coverage_audit.py` upsert left this row intact (ON CONFLICT does not delete orphans).

Resolution: `DELETE FROM school_signal_coverage WHERE signal_id NOT IN (SELECT signal_id FROM msr_signals);`
→ 1 row deleted (SIG.MSR.497 / tajika / secondary).

Post-clean count: 4,011 (target achieved).

## School Signal Coverage Breakdown (post-rebuild)

| School | Primary | Secondary | Silent |
|---|---|---|---|
| bnn | 105 | 2 | 466 |
| jaimini | 48 | 252 | 273 |
| kp | 0 | 0 | 573 |
| nadi | 5 | 0 | 568 |
| parashari | 299 | 138 | 136 |
| tajika | 174 | 5 | 394 |
| yogini | 30 | 292 | 251 |

Note: kp has 573 silent rows — consistent with prior audit finding that KP system has no
classical_attributions mapped to its text_keys in the current rag_chunks corpus.

## Invocation Details

```
# DB proxy: bash platform/scripts/start_db_proxy.sh
# Registers:
cd platform/python-sidecar
DATABASE_URL=postgresql://amjis_app:...@127.0.0.1:5433/amjis python3 -m pipeline.ingest_l3_registers
# school_signal_coverage:
DB_NAME=amjis DB_USER=amjis_app DB_PASSWORD=... python3 platform/scripts/m9/run_coverage_audit.py
# Orphan cleanup:
psql ... -c "DELETE FROM school_signal_coverage WHERE signal_id NOT IN (SELECT signal_id FROM msr_signals);"
# MV refresh:
psql ... -c "REFRESH MATERIALIZED VIEW school_convergence_index;"
```
