---
artifact: FORENSIC_V8_SWEEP_MANIFEST
version: 1.0
status: COMPLETE
created: 2026-06-08
branch: chore/l0-manual-texts-fetch
pr: 230
---

# FORENSIC_ASTROLOGICAL_DATA_v8_0 Reference Sweep Manifest

Governs the full sweep of `FORENSIC_ASTROLOGICAL_DATA_v8_0` references from
`platform/**` and `00_ARCHITECTURE/**` (excluding `99_ARCHIVE/**`), executed
on PR #230 `fix/forensic-reference-consistency`.

## Canonical replacement targets

| Role | Target |
|---|---|
| **Live data source** | `chart_facts` DB table via `platform/src/lib/ganita/forensic_render.ts` |
| **Archived doc** | `99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md` |
| **Provenance citation short form** | `FORENSIC v8.0 §X (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md)` |

---

## Category A — Source/doc comments describing what code replaces

**Action:** Update path to archive form. Keep descriptive text.

| File | Lines | Change |
|---|---|---|
| `platform/src/lib/ganita/forensic_render.ts` | 5, 508 | Updated path reference to archive path in JSDoc comments |
| `platform/src/lib/ganita/types.ts` | 8, 16, 18 | Updated domain coverage comment + source_uri/source_canonical_id examples |
| `platform/src/lib/forensic/snapshot.ts` | 26 | Updated canonical L1 source comment |
| `platform/src/lib/schools/types.ts` | 114 | Updated natal chart source comment |
| `platform/scripts/governance/manifest_reader.py` | 26 | Changed stale alias `"FORENSIC": "FORENSIC_ASTROLOGICAL_DATA_v8_0"` → removed (CAPABILITY_MANIFEST.json now uses canonical_id `"FORENSIC"` directly; self-referential alias is wrong and would cause parity-check failure) |

---

## Category B — Functional regex/token matchers

**Action: LEAVE AS-IS** — these patterns detect citation tokens in MSR signal text; changing them would break the ICR grounding detector.

| File | Lines | Reason LEAVE |
|---|---|---|
| `platform/src/lib/icr/l1_truth_index.ts` | 44–45, 9 | Regex `/FORENSIC_ASTROLOGICAL_DATA_v8_0/` matches this token as a valid L1 citation in MSR signal content. MSR signals legitimately contain this token; the regex must continue to match it. |
| `platform/scripts/governance/l1_truth_index.ts` | 92 | Docstring explaining the token list — documents the regex above. |
| `platform/src/scripts/manifest/auto_deriver.ts` | 178 | Comment illustrating ID derivation pattern; no runtime path dependency. |
| `platform/src/scripts/manifest/parity_validator.ts` | 323 | Comment about path-based IDs as an example; no runtime path dependency. |
| `platform/scripts/governance/drift_detector.py` | 497 | Entry in `KNOWN_MISSING_FILES` allowlist — this entry is **correct**: the file was deleted in PR #187; the allowlist tells drift_detector not to raise an alarm about it. Removing this entry would cause drift_detector to report a false error. |

---

## Category C — Test fixtures asserting old path as expected value

**Action:** Update fixture AND corresponding assertion together so the test still passes for the right reason.

| File | Lines | Change |
|---|---|---|
| `platform/src/lib/bundle/__tests__/manifest_reader.test.ts` | 30, 39 | Updated SAMPLE_MANIFEST FORENSIC path + SAMPLE_OVERRIDES_YAML path_pattern to archive form |
| `platform/src/scripts/manifest/__tests__/override_merger.test.ts` | 9 | Updated base entry path in test fixture |
| `platform/src/scripts/manifest/__tests__/parity_validator.test.ts` | 44, 49, 155, 250, 332 | Updated SAMPLE_CA_TEXT fixture YAML + FORENSIC_ENTRY path + two `toBe()` assertions |
| `platform/src/lib/ganita/__tests__/facts_store.test.ts` | 69, 71 | Updated `source_uri` GCS path + `source_canonical_id` from `FORENSIC_ASTROLOGICAL_DATA_v8_0` → `FORENSIC` |
| `platform/tests/unit/lib/schemas.test.ts` | 9 | Updated path in schema validation fixture (schema validates shape, not specific path values) |

---

## Category D — Active seed script SOURCE constants

**Action:** Update SOURCE citation string to archive form; confirm it's a citation string not an `fs.readFile` (confirmed: no file I/O in seed script).

| File | Lines | Change |
|---|---|---|
| `platform/scripts/data/seed_chart_facts_planet.ts` | 5, 17, 201 | Updated comment + `const SOURCE` path + `source_version` field |

---

## Category E — Provenance citation strings

**Action:** Bulk-update path in Python SOURCE_CITATION constants, docstrings, SQL column comments, test comments. Preserve §-section references.

### Python brahmagyan files (~50 refs)

| File | Refs | Change |
|---|---|---|
| `platform/python-sidecar/brahmagyan/bodha/l2_lenses_salience.py` | 1 | Updated in-string path |
| `platform/python-sidecar/brahmagyan/ganita/l1_engine_check.py` | 1 | Updated comment |
| `platform/python-sidecar/brahmagyan/ganita/l1_panchanga_birth.py` | 2 | Updated docstring + SOURCE string |
| `platform/python-sidecar/brahmagyan/kala/l3_convergence.py` | 2 | Updated docstring + SOURCE_CITATION |
| `platform/python-sidecar/brahmagyan/kala/l3_l4_reverification_report.py` | 1 | Updated forensic_anchor string |
| `platform/python-sidecar/brahmagyan/kala/l3_obstruction.py` | 2 | Updated docstring + SOURCE_CITATION |
| `platform/python-sidecar/brahmagyan/kala/l3_snapshot.py` | 3 | Updated docstring + SOURCE_CITATION + inline source string |
| `platform/python-sidecar/brahmagyan/kala/l3_timeline.py` | 2 | Updated docstring + SOURCE_CITATION |
| `platform/python-sidecar/brahmagyan/kala/obstruction.py` | 2 | Updated docstring + source_citation comment |
| `platform/python-sidecar/brahmagyan/kala/timeline.py` | 1 | Updated comment |
| `platform/python-sidecar/brahmagyan/mimamsa/export_to_bigquery.py` | 1 | Updated source description string |
| `platform/python-sidecar/brahmagyan/mimamsa/l5_calibration_substrate.py` | 2 | Updated docstring + SOURCE_CITATION |
| `platform/python-sidecar/brahmagyan/mimamsa/l5_event_chart_state_index.py` | 2 | Updated docstring + SOURCE_CITATION |
| `platform/python-sidecar/brahmagyan/mimamsa/l5_learning_multiplier.py` | 2 | Updated docstring + SOURCE_CITATION |
| `platform/python-sidecar/brahmagyan/mimamsa/l5_lel_intake.py` | 1 | Updated docstring |
| `platform/python-sidecar/brahmagyan/mimamsa/lel_intake.py` | 1 | Updated docstring |
| `platform/python-sidecar/brahmagyan/phala/l4_anchors.py` | 3 | Updated docstring + SOURCE_CITATION + l1_ground_truth string |
| `platform/python-sidecar/brahmagyan/phala/l4_mitigation.py` | 3 | Updated docstring + SOURCE_CITATION + inline string |
| `platform/python-sidecar/brahmagyan/phala/l4_muhurta.py` | 2 | Updated docstring + SOURCE_CITATION |
| `platform/python-sidecar/brahmagyan/phala/l4_outlook.py` | 3 | Updated docstring + SOURCE_CITATION + l1_ground_truth string |
| `platform/python-sidecar/brahmagyan/phala/l4_rectification.py` | 2 | Updated docstring + SOURCE_CITATION |
| `platform/python-sidecar/brahmagyan/phala/rectification.py` | 4 | Updated docstring + SOURCE_CITATION + inline strings |
| `platform/python-sidecar/panchang_engine/jaimini_chara.py` | 1 | Updated comment |
| `platform/python-sidecar/pipeline/writers/__tests__/test_panchanga_writer.py` | 1 | Updated test comment |
| `platform/python-sidecar/tests/test_mimamsa_export.py` | 3 | Updated source_citation fixture strings |
| `platform/scripts/l1_volumetric_check.sql` | 1 | Updated SQL comment |

### Test file comments

| File | Refs | Change |
|---|---|---|
| `platform/src/lib/tools/brahma/l1/__tests__/query_panchanga.test.ts` | 2 | Updated source attribution comments |
| `platform/tests/classical/classical_texts_smoke.test.ts` | 2 | Updated source attribution comments |
| `platform/tests/icr/l1_truth_index.test.ts` | 2 | Updated fixture comment + inline source ref |

### SQL migrations

| File | Refs | Change |
|---|---|---|
| `platform/supabase/migrations/0001_brahma_baseline.sql` | 2 | Updated COLUMN COMMENT provenance strings (both live and staging tables) |

---

## Category F — Broken standalone scripts

**Action:** Fix broken path / dead link.

| File | Lines | Change |
|---|---|---|
| `platform/scripts/invariants_l1.py` | 12 | Repointed `FORENSIC_V8` constant from deleted `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` to archive copy at `99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md` |
| `platform/scripts/eval/README.md` | 145 | Fixed dead link to archive path |

---

## Category G — Frozen historical artifacts (LEAVE AS-IS)

All files below document past truths. Editing them would rewrite history.

| File / Pattern | Reason LEAVE |
|---|---|
| `platform/scripts/cutover/**` (5 files) | Frozen cutover audit snapshots from phase 13 |
| `platform/scripts/_archived/seed-abhisek.ts` | Archived script |
| `platform/scripts/eval/fixtures.json` | Frozen eval fixture per task Category G scope |
| `platform/tests/visual/4C4_close_report.md` | Frozen phase close report |
| `platform/vitest.config.ts` comment (line 35) | Documents historical reason tests are excluded (refers to PR #187 legacy teardown) |
| `platform/python-sidecar/scripts/gcs_sync_results.json` | Frozen GCS sync snapshot; GCS object may still exist at the old path |
| `platform/scripts/pipeline_smoke_audit.py` (line 483) | GCS path `L1/facts/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` — GCS object may still exist; audit script checks GCS state, not local FS. Changing this without verifying GCS would break the audit. LEAVE + note. |
| `platform/supabase/migrations/_pre_squash_schema_snapshot.sql` | Frozen pre-squash schema snapshot |
| `platform/supabase/migrations/_archive/079_tajaka_and_convergence.sql` | Archived migration |
| `00_ARCHITECTURE/grounding_review/msr_grounding_candidates_*.csv` | Frozen grounding review data (1,071 refs combined) |
| `00_ARCHITECTURE/SESSION_LOG.md` | Live governance log — refs document past session state |
| `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md` | Frozen governance record |
| `00_ARCHITECTURE/drift_reports/**` | Frozen drift report snapshots |
| `00_ARCHITECTURE/BRIEFS/**` (agent briefs, M2/kickoff docs) | Frozen planning artifacts |
| `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` | Session history record; refs are historical state pointers |
| `00_ARCHITECTURE/M2A_EXEC_PLAN_v1_0.md` | Frozen execution plan |
| `00_ARCHITECTURE/ASSET_INVENTORY_REPORT_v1_0.md` | Frozen audit report |
| `00_ARCHITECTURE/AUDIT/**` | Frozen audit artifacts |

---

## Post-sweep verification

```
git grep -n "FORENSIC_ASTROLOGICAL_DATA_v8_0" -- 'platform/**' '00_ARCHITECTURE/**' ':!99_ARCHIVE/**'
```

After sweep, only the intentional LEAVE-AS-IS refs remain (Category B + G), all documented above.
