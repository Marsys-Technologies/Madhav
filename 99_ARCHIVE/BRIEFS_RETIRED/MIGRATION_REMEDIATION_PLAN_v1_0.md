---
artifact: MIGRATION_REMEDIATION_PLAN_v1_0.md
canonical_id: MIGRATION_REMEDIATION_PLAN
version: "1.0"
status: AUTHORED
produced_during: Forensic Migration Audit (post-Phase-14G lockdown)
produced_on: "2026-04-29"
phase_14_lockdown_commit: 5b7d252
source_brief: EXEC_BRIEF_FORENSIC_MIGRATION_AUDIT_v1_0.md
divergence_register: 00_ARCHITECTURE/MIGRATION_DIVERGENCE_REGISTER_v1_0.json
---

# Migration Remediation Plan

## Summary

3 divergences found, 0 HIGH severity, 2 MEDIUM, 1 LOW. All divergences are governance-metadata
issues (incorrect manifest paths, missing manifest entries). No data loss. No content-integrity
failures. Phase 14 lockdown commit `5b7d252` is **not invalidated**.

---

## REM-A-001 — Correct CHART_FACTS path entries in CAPABILITY_MANIFEST.json

**Addresses:** DIV-001, DIV-002

**Finding:** Two CHART_FACTS files are declared in `CAPABILITY_MANIFEST.json` under the wrong
GCS prefix (`L1/structured/`) when they actually exist at `L1/facts/STRUCTURED/`.

| File | Incorrect path | Correct path |
|---|---|---|
| CHART_FACTS_EXTRACTION_v1_0.yaml | `gs://madhav-marsys-sources/L1/structured/CHART_FACTS_EXTRACTION_v1_0.yaml` | `gs://madhav-marsys-sources/L1/facts/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` |
| CHART_FACTS_SCHEMA_v1_0.json | `gs://madhav-marsys-sources/L1/structured/CHART_FACTS_SCHEMA_v1_0.json` | `gs://madhav-marsys-sources/L1/facts/STRUCTURED/CHART_FACTS_SCHEMA_v1_0.json` |

**Fix:** In `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`, update the `gcs_uri` field for both
entries from `L1/structured/` prefix to `L1/facts/STRUCTURED/` prefix. No GCS copy or data
migration needed — files are already at the correct location.

**Risk:** LOW. Purely a manifest metadata fix. Does not touch any data files.

**Gating:** Can execute at any time. Should execute before any tooling reads manifest GCS paths
for CHART_FACTS files (e.g., `loadManifest`, drift_detector, mirror_enforcer if they ever
dereference GCS URIs).

---

## REM-A-002 — Add three ephemeris CSVs to CAPABILITY_MANIFEST.json

**Addresses:** DIV-003

**Finding:** Three ephemeris CSV files were registered in `FILE_REGISTRY_v1_14.md` (now
SUPERSEDED) and are confirmed present in GCS, but were never added to `CAPABILITY_MANIFEST.json`
when it replaced `FILE_REGISTRY` in Phase 1B (2026-04-27).

| File | GCS path |
|---|---|
| ECLIPSES_1900_2100.csv | `gs://madhav-marsys-sources/L1/ephemeris/ECLIPSES_1900_2100.csv` |
| RETROGRADES_1900_2100.csv | `gs://madhav-marsys-sources/L1/ephemeris/RETROGRADES_1900_2100.csv` |
| EPHEMERIS_MONTHLY_1900_2100.csv | `gs://madhav-marsys-sources/L1/ephemeris/EPHEMERIS_MONTHLY_1900_2100.csv` |

**Fix:** Add three entries to `CAPABILITY_MANIFEST.json` under the `L1/ephemeris` section with
status `CURRENT`, layer `L1`, category `ephemeris_source`, and the correct GCS URIs. Include
SHA-256 hashes (available in Stream B evidence files) and local_path references.

**Risk:** LOW. Additive manifest entry only; no data migration.

**Gating:** Can execute at any time. Lower priority than REM-A-001 since downstream tables all
pass audit and manifest omission does not cause runtime failures.

---

## Execution sequence

```
REM-A-001 (manifest path fix — two lines)  →  REM-A-002 (manifest additive entries — three lines)
```

Both are manifest-only edits. Estimated effort: 30 minutes combined. No deployment or GCS
operations required.
