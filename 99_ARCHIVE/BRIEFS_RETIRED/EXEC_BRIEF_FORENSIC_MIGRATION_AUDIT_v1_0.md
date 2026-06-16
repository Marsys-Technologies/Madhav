---
brief_id: EXEC_BRIEF_FORENSIC_MIGRATION_AUDIT
version: 1.0
status: COMPLETE
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code (multi-session — see Execution model)
trigger_phrase: "Read EXEC_BRIEF_FORENSIC_MIGRATION_AUDIT_v1_0.md and execute it."
phase: post-Phase-14 — forensic audit of cloud migration faithfulness
phase_name: Forensic Migration Audit — local-vs-cloud variance detection across all layers
risk_classification: MEDIUM (audit is read-only against live data; risk is in discovering blocking divergences that mandate remediation work — but discovery itself is safe)
parallelizable_with: [Phase 11B (legacy deletion — but blocks until audit finds zero blocking divergences); Sidecar 500 investigation (orthogonal)]
must_complete_before: [any work that depends on cloud being a faithful copy of local — particularly any decision to delete local copies]
depends_on:
  - Phase 14 SEALED at commit 5b7d252 (PHASE_14_LOCKDOWN_v1_0.md)
  - Sidecar 500 investigation (independent — audit can run regardless)
output_artifacts:
  - 00_ARCHITECTURE/MIGRATION_AUDIT_REPORT_v1_0.md (NEW master report)
  - 00_ARCHITECTURE/MIGRATION_DIVERGENCE_REGISTER_v1_0.json (NEW machine-readable register of every divergence)
  - 00_ARCHITECTURE/MIGRATION_REMEDIATION_PLAN_v1_0.md (NEW per-divergence remediation actions)
  - verification_artifacts/MIGRATION_AUDIT/ (NEW directory — per-stream raw evidence)
---

# EXEC_BRIEF — Forensic Migration Audit (local-vs-cloud variance)

## Mission

Phase 14 migrated the MARSYS-JIS data layer from local filesystem and JSON-on-disk into Google Cloud (GCS sources bucket + Cloud SQL Postgres). The Phase 14G lockdown verified the migration was *structurally complete* — tables exist, row counts in expected ranges, FK integrity holds, tools registered. This brief verifies the migration is *content-faithful* — every byte that should have moved did move, every derivation that should have produced row N produces exactly that row, no truncation, no silent corruption, no skipped content.

Three commitments:

1. **Three-layer verification.** Migration occurred at three layers, each requires its own technique:
   - **Layer 1 (filesystem → GCS bucket)**: byte-level sha256 audit. Any divergence is a hard failure.
   - **Layer 2 (GCS → rag_chunks/rag_embeddings)**: re-derivation audit. Re-run the chunker on each GCS source; chunk IDs must match the DB.
   - **Layer 3 (GCS → structured Postgres tables)**: re-extraction + ground-truth cross-check. For deterministic derivations (Swiss Ephemeris, JSON parse), re-run and compare. For LLM-assisted extractions (FORENSIC → chart_facts), cross-check against ground-truth sources (EVENT_CHART_STATES) and source-section grounding.

2. **Every divergence gets a remediation plan, not a write-up.** The output isn't an "interesting findings" document — it's an actionable remediation plan with one entry per divergence: cause, scope, fix, who-applies, verification.

3. **The audit is read-only against live data.** No fix lands during the audit. After the audit closes with the divergence register + remediation plan, a subsequent brief executes the fixes. Mixing diagnosis and remediation in the same session is how silent re-corruption happens.

## Pre-flight gate

1. Verify Phase 14G is COMPLETE — frontmatter check + `00_ARCHITECTURE/PHASE_14_LOCKDOWN_v1_0.md` exists.
2. Verify the executor's environment can:
   - Run `gcloud storage` against `gs://madhav-marsys-sources` (read).
   - Connect to Cloud SQL `amjis-postgres` via Auth Proxy (read).
   - Re-run the existing chunkers and extractors locally (Python sidecar imports work).
   - Re-run Swiss Ephemeris (`pyswisseph` available).
3. Confirm git working tree clean.
4. Confirm enough disk space for cached GCS downloads (~100 MB max — markdown files are small).

## Scope

**`may_touch` (read-only against cloud + DB):**
- All `gcloud storage` read operations against `gs://madhav-marsys-sources` and `gs://madhav-marsys-build-artifacts`.
- All read queries against Cloud SQL `amjis-postgres`. NO writes.
- Local reads of `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, `035_DISCOVERY_LAYER/` source files.
- `00_ARCHITECTURE/VALIDATED_ASSET_REGISTRY_v1_0.json` (read; ground truth for what was migrated).
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (read; ground truth for current cloud state).

**`may_touch` (filesystem / git — write only the audit artifacts):**
- `00_ARCHITECTURE/MIGRATION_AUDIT_REPORT_v1_0.md` (NEW master report)
- `00_ARCHITECTURE/MIGRATION_DIVERGENCE_REGISTER_v1_0.json` (NEW machine-readable per-divergence record)
- `00_ARCHITECTURE/MIGRATION_REMEDIATION_PLAN_v1_0.md` (NEW per-divergence remediation actions)
- `verification_artifacts/MIGRATION_AUDIT/` (NEW directory — per-stream raw evidence: hashes, diffs, sample outputs)

**`must_not_touch`:**
- Any GCS object (read-only audit).
- Any Postgres table (read-only audit).
- Any local source file (the audit cannot "fix" a source by editing it; remediation is a separate brief).
- Any chunker, embedder, extractor, or pipeline code (re-run them, do not modify).
- Any feature flag.
- Any locked CAPABILITY_MANIFEST entry (no LOCKED→TRANSITIONAL flips during audit).
- Any Phase 14 sealing artifact (`PHASE_14_LOCKDOWN_v1_0.md`).

## Execution model — multi-session

The audit decomposes into 11 streams. Stream A is foundational; B–J are roughly parallel; K is the synthesis. Recommended ordering:

| Order | Stream | Session # | Parallel-safe with |
|---|---|---|---|
| 1 | A — Inventory reconciliation (foundation) | 1 | (none) |
| 2 | B — Layer 1: byte-level sha256 audit | 2 | C, D, E, F, G, H, I, J |
| 2 | C — rag_chunks faithfulness audit | 3 | B, D, … |
| 2 | D — rag_embeddings audit | 4 | B, C, … |
| 2 | E — chart_facts ↔ FORENSIC audit | 5 | B, C, … |
| 2 | F — ephemeris_daily determinism audit | 6 | B, C, … |
| 2 | G — eclipses + retrogrades CSV audit | 7 | B, C, … |
| 2 | H — life_events + sade_sati audit | 8 | B, C, … |
| 2 | I — L2.5 structured tables audit | 9 | B, C, … |
| 2 | J — L3 register tables audit | 10 | B, C, … |
| 3 | K — Synthesis: divergence register + remediation plan | 11 | (gated on B–J done) |

If executor capacity permits, fan B–J into parallel Claude Code sessions. Each writes to its own `verification_artifacts/MIGRATION_AUDIT/<stream>/` subdirectory and produces a partial divergence list. Stream K aggregates.

## Sub-streams

### Stream A — Inventory reconciliation

Build a complete inventory of what *should* exist in GCS based on `VALIDATED_ASSET_REGISTRY_v1_0.json` + post-14F.1 amendments + 14C Stream D.0 CSV promotion.

1. Parse `VALIDATED_ASSET_REGISTRY_v1_0.json`. List every entry where `status IN ('CURRENT', 'TRANSITIONAL')` with its expected `gcs_uri`.
2. Parse `CAPABILITY_MANIFEST.json`. List every entry with a `gcs_uri` field.
3. List actual contents of GCS via `gcloud storage ls -r gs://madhav-marsys-sources/`. Capture filename + object size + creation timestamp + content-type.
4. Build three sets:
   - **Set A** — files registry says should be in GCS
   - **Set B** — files manifest says are in GCS
   - **Set C** — files actually in GCS

5. Surface:
   - **Missing in GCS**: Set A or Set B but NOT in Set C → upload gap.
   - **Extra in GCS**: Set C but NOT in Set A or Set B → drift; possible orphan upload.
   - **Renamed**: same content (sha256) but different path → naming drift.
   - **Manifest/Registry mismatch**: Set A ≠ Set B → governance drift between two source-of-truth docs.

6. Write `verification_artifacts/MIGRATION_AUDIT/A_inventory.json` containing all four sets + the three diff lists.

**Gate**: if any "Missing in GCS" entries exist, the migration was incomplete. Document but proceed; remediation is in Stream K.

### Stream B — Layer 1: byte-level sha256 audit

For every (local_path, gcs_uri) pair in Stream A's reconciled inventory:

1. Compute local sha256: `sha256sum <local_path>` → `local_hash`.
2. Stream the GCS object content and compute its sha256: `gcloud storage cat <gcs_uri> | sha256sum` → `gcs_hash`.
3. Compare. Mismatches = byte-level divergence.
4. Also capture from GCS metadata: `crc32c` and `md5Hash` (gcloud provides both); cross-check against locally-computed values. (gcloud reports crc32c base64-encoded; decode before compare.)

Note: GCS object versioning is enabled (per `GCS_LAYOUT`). If the audit finds an older version is the live one (e.g., a re-upload was overwritten by a stale push), surface the version history.

5. Capture per-file evidence to `verification_artifacts/MIGRATION_AUDIT/B_layer1/<safe_filename>.json`:
   ```json
   {
     "local_path": "01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md",
     "gcs_uri": "gs://madhav-marsys-sources/L1/facts/FORENSIC_ASTROLOGICAL_DATA_v8_0.md",
     "local_sha256": "...",
     "gcs_sha256": "...",
     "gcs_md5": "...",
     "gcs_crc32c": "...",
     "local_size_bytes": 12345,
     "gcs_size_bytes": 12345,
     "match": true,
     "gcs_generation": "1234567890123456",
     "gcs_versions_count": 1
   }
   ```
6. Aggregate to `verification_artifacts/MIGRATION_AUDIT/B_layer1_summary.csv`: rows = files; columns = local_hash, gcs_hash, match, size_delta, version_count.

**Expected result**: 100% match. Any mismatch is a HIGH-severity divergence requiring re-upload from canonical local source.

### Stream C — rag_chunks faithfulness audit

For every GCS source that gets chunked into `rag_chunks`:

1. Download the GCS source content to a local temp dir.
2. Re-run the appropriate chunker from `platform/python-sidecar/rag/chunkers/` against the downloaded content. The chunker is content-hash-idempotent — same input produces same chunk IDs.
3. Capture: list of (chunk_id, content_hash, doc_type, source_file, source_version) for every chunk re-derivation produces.
4. Query the live DB for the same source's chunks. Capture the same fields.
5. Compare:
   - **Set match**: every re-derived chunk_id appears in DB; every DB chunk_id is re-derived. Hard equality.
   - **Content match**: for every shared chunk_id, content_hash matches between re-derivation and DB.
   - **Count match**: |re-derived chunks| = |DB chunks for this source|.
6. Capture per-source evidence to `verification_artifacts/MIGRATION_AUDIT/C_chunks/<safe_source_name>.json`.

Special cases:
- If a chunker has been modified post-14B build, re-running it now produces *different* chunks than what the build pipeline produced. This is a real risk if anyone touched chunker code post-14B; check git log on `platform/python-sidecar/rag/chunkers/` for commits after 14B's commit `dc6d922`.
- If git log shows post-14B chunker commits, the audit must run against the chunker SHA frozen in `build_manifests.pipeline_image_uri` — pull that image, run the chunker from inside it. (More work, but it's the only way to get a true comparison.)

**Expected result**: 100% set match + content match for every source. Discrepancies likely cause: chunker code change post-14B, or partial pipeline run.

### Stream D — rag_embeddings audit

1. Query DB: `SELECT COUNT(*) FROM rag_embeddings;` — expected 941 (or whatever 14B built).
2. Query DB: `SELECT vector_dims(embedding) FROM rag_embeddings GROUP BY vector_dims;` — expected single row, dim=768.
3. Query DB: `SELECT chunk_id, COUNT(*) FROM rag_embeddings GROUP BY chunk_id HAVING COUNT(*) > 1;` — expected zero rows (1:1 chunk:embedding).
4. Cross-check chunk:embedding 1:1: `SELECT c.chunk_id FROM rag_chunks c LEFT JOIN rag_embeddings e USING (chunk_id) WHERE e.chunk_id IS NULL;` — expected zero rows.
5. Spot-check embedding semantic sanity: pick 5 random chunks, embed their content via Vertex AI `text-multilingual-embedding-002`, compute cosine similarity vs DB embedding. Should be ≥0.98 (Vertex AI is deterministic; small drift from float precision is acceptable).
6. Capture evidence to `verification_artifacts/MIGRATION_AUDIT/D_embeddings.json`.

**Expected result**: 941 rows, 768-dim, 1:1, sanity-check ≥0.98 cosine. Any failure indicates embedding regeneration or model drift; re-embed the affected chunks.

### Stream E — chart_facts ↔ FORENSIC source-section audit

This is the highest-discipline-risk stream because chart_facts originated from LLM-assisted extraction.

1. Query DB: `SELECT fact_id, value_text, value_number, value_json, source_section FROM chart_facts;` — all 589 rows.
2. For each fact:
   - Verify `source_section` references a section that actually exists in `FORENSIC_ASTROLOGICAL_DATA_v8_0.md` (e.g., `§4.1 row 12` resolves to a real row in the §4.1 KP cusps table).
   - For numeric facts (longitude, degree, minute), verify the value appears verbatim or within ±0.01° tolerance somewhere in the cited source section. Do this by reading the source section and confirming the value is present.
   - For categorical facts (sign, nakshatra, planet), verify the value matches what's in the cited section.
3. **Ground-truth cross-check**: for natal-chart facts (planet longitudes, ascendant, KP cusps), cross-check against `EVENT_CHART_STATES_v1_0.md` (Swiss Ephemeris truth for the natal moment). Mismatch >0.001° = HIGH-severity divergence.
4. **Sahams + special lagnas**: these are derived from natal positions; verify the derivation reproduces the stated value.
5. **Yogas**: verify each yoga's listed-conditions are met by the natal positions.
6. Capture per-fact evidence to `verification_artifacts/MIGRATION_AUDIT/E_chart_facts.json`. Group by status: `verified`, `unresolvable_section`, `value_mismatch`, `ground_truth_mismatch`.

**Expected result**: ≥99% verified. Any value_mismatch or ground_truth_mismatch is a HIGH-severity divergence requiring re-extraction (and possibly correction of FORENSIC if the extraction is right and FORENSIC is wrong — but that's a Stream K decision, not an audit decision).

### Stream F — ephemeris_daily determinism audit

Swiss Ephemeris is deterministic — same date + same ayanamsha = same longitude. The audit re-computes a sample and compares.

1. Query DB: pick 1000 random `(date, planet)` pairs from `ephemeris_daily`. Capture stored `longitude_deg`, `is_retrograde`, `nakshatra`, `nakshatra_pada`, `sign`.
2. Locally re-compute each via `pyswisseph` with `swe.set_sid_mode(swe.SIDM_LAHIRI)` — same code path as `bootstrap_ephemeris.py`.
3. Compare:
   - longitude_deg: ≤0.0001° delta = match (allow float-precision drift).
   - is_retrograde: exact boolean match.
   - sign, nakshatra, nakshatra_pada: derived; verify derivation reproduces.
4. Also: query for boundary cases — first date (1900-01-01), last date (2100-12-31), nakshatra-pada-boundary days. Expected to compute cleanly.
5. Total count check: `SELECT COUNT(*) FROM ephemeris_daily;` matches expected 660,726.
6. Capture evidence to `verification_artifacts/MIGRATION_AUDIT/F_ephemeris.json`.

**Expected result**: 1000/1000 sample matches. Any mismatch indicates ayanamsha drift or version-of-pyswisseph drift between bootstrap and audit; surface and reconcile.

### Stream G — eclipses + retrogrades CSV audit

1. **Eclipses**:
   - Read local CSV `01_FACTS_LAYER/ECLIPSES_1900_2100.csv`. Count rows.
   - Query DB: `SELECT COUNT(*) FROM eclipses;` — should match (or be very close — schema may have filtered rows for missing fields).
   - Sample 50 random eclipse rows from DB. For each, find the matching row in the CSV by date+type. Verify longitude, sign, nakshatra, visibility_region match.
2. **Retrogrades**:
   - Same approach for `RETROGRADES_1900_2100.csv` and `retrogrades` table.
   - Sample 100 random rows.
3. **CSV vs GCS**: Stream B already verified the CSVs are byte-identical between local and GCS. Stream G verifies the CSVs were faithfully ingested.
4. Capture evidence to `verification_artifacts/MIGRATION_AUDIT/G_eclipses_retrogrades.json`.

**Expected result**: row counts within 1% of CSV (some rows may legitimately filter due to NULL fields), 100% of sampled rows verbatim match.

### Stream H — life_events + sade_sati audit

1. **life_events** (must be 36 exactly):
   - Read `LIFE_EVENT_LOG_v1_2.md` frontmatter + structured event blocks. Extract all 36 events into a local list.
   - Query DB: `SELECT event_id, event_date, category, description, chart_state, source_section FROM life_events ORDER BY event_date;`
   - Compare row by row. Flag any:
     - Missing event (in markdown, not in DB)
     - Extra event (in DB, not in markdown)
     - Date mismatch (markdown says 2014-05-12, DB says 2014-05-13)
     - Description truncation (DB content shorter than markdown)
     - chart_state JSON malformed or missing
   - For each event with `chart_state`, cross-check 1–2 chart_state fields against `EVENT_CHART_STATES_v1_0.md` (Swiss Ephemeris truth) — at minimum the date matches and the planetary positions are within tolerance.

2. **sade_sati_phases** (46 rows expected):
   - Read `SADE_SATI_CYCLES_ALL.md`. Parse phase blocks (4 cycles × multiple phases × possible nakshatra sub-windows).
   - Query DB: `SELECT cycle_number, phase, start_date, end_date, saturn_sign_at_start, source_section FROM sade_sati_phases ORDER BY cycle_number, start_date;`
   - Verify:
     - 14G's classification stands (46 includes nakshatra sub-windows; not duplicates).
     - Every DB phase has a corresponding markdown block (date ranges align).
     - `saturn_sign_at_start` is consistent with ephemeris_daily for that start_date (cross-stream check).
3. Capture evidence to `verification_artifacts/MIGRATION_AUDIT/H_life_events_sade_sati.json`.

**Expected result**: 36 life_events exact match; 46 sade_sati_phases all traceable to markdown source.

### Stream I — L2.5 structured tables audit

For each L2.5 table (msr_signals, ucn_sections, cdlm_links, cgm_nodes, cgm_edges, rm_resonances):

1. Re-run the corresponding extractor from `platform/python-sidecar/pipeline/extractors/` against the GCS-downloaded source markdown.
2. Compare extractor output to live DB rows on:
   - Set match (every row appears in both)
   - Content match (for shared rows, all fields match)
   - Count match
3. Special focus:
   - **msr_signals** (499): every signal_id 001–499 present? Any duplicate? Any with null name/description?
   - **cdlm_links** (81 = 9×9): every (from_domain, to_domain) pair present? Diagonal cells correct?
   - **cgm_edges** (21 — known reduced): cross-check with the cgm_edges_anomaly Stream F finding from 14G. Verify the 21 edges are exactly the explicit edges in CGM_v9_0.md.
   - **ucn_sections** (134): every section_id resolves to a parent_section_id chain or is top-level. derived_from_signals references resolve.
   - **rm_resonances** (28): every signal_a/b resolves against msr_signals.
4. Capture evidence per table to `verification_artifacts/MIGRATION_AUDIT/I_l2_5/<table>.json`.

**Expected result**: 100% set match for all tables. Discrepancies likely indicate extractor changes post-14D (check git log on extractors after commit dc6d922) or markdown drift between GCS and local.

### Stream J — L3 register tables audit

For each L3 register (pattern_register, resonance_register, cluster_register, contradiction_register):

1. Read the corresponding canonical JSON from local `035_DISCOVERY_LAYER/REGISTERS/*.json`.
2. Read the corresponding JSON from GCS at `L3/registers/*.json` (Stream B already verified byte-identical).
3. Parse JSON. Count entries.
4. Query DB: `SELECT COUNT(*), MIN(<id_field>), MAX(<id_field>) FROM <table>;`
5. Compare:
   - JSON entry count = DB row count.
   - Every JSON entry's primary ID present in DB.
   - Every DB row traces to a JSON entry.
   - For 5 random entries per register, full field-by-field comparison.
6. Verify FK validation: every signal_id, fact_id, event_id, pattern_id reference resolves (this duplicates 14G Stream B; re-check anyway).
7. Capture evidence to `verification_artifacts/MIGRATION_AUDIT/J_l3/<table>.json`.

**Expected result**: 100% match between JSON and DB. Append-only swap should preserve every JSON entry.

### Stream K — Synthesis: divergence register + remediation plan

After Streams A–J complete:

1. **Aggregate** all per-stream divergence outputs into `00_ARCHITECTURE/MIGRATION_DIVERGENCE_REGISTER_v1_0.json`. Schema:
   ```json
   {
     "audit_run_id": "<uuid>",
     "audit_completed_at": "2026-04-28T..Z",
     "phase_14_lockdown_commit": "5b7d252",
     "divergences": [
       {
         "div_id": "DIV.001",
         "layer": "L1|L2|L3",
         "source_file": "01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md",
         "target_location": "gs://... | postgres:chart_facts",
         "stream": "B",
         "type": "byte_mismatch | missing | extra | renamed | content_mismatch | count_mismatch | ground_truth_mismatch",
         "severity": "HIGH | MEDIUM | LOW",
         "evidence_uri": "verification_artifacts/MIGRATION_AUDIT/B_layer1/forensic.json",
         "description": "...",
         "remediation_plan_id": "REM.001"
       }
     ]
   }
   ```
2. **Severity classification**:
   - **HIGH**: byte-level divergence in L1 (canonical source corrupted), ground-truth mismatch in chart_facts, ephemeris determinism failure, missing register entries.
   - **MEDIUM**: count mismatch within tolerance (1–5% off), unresolvable source_section in chart_facts (extracted fact can't be cited), ucn_section orphan reference.
   - **LOW**: renamed file with same content, version-history-only divergence.

3. **Remediation plan** per divergence (`MIGRATION_REMEDIATION_PLAN_v1_0.md`):
   - **DIV → REM mapping**: every divergence gets a `REM.NNN` remediation entry.
   - **REM entry contents**:
     - Cause analysis (1 paragraph)
     - Fix scope (which files / tables / cloud resources change)
     - Fix complexity (small / medium / large)
     - Who applies (executor in next session | native decides | requires multi-agent input)
     - Verification step (how to confirm fix landed)
     - Acceptance gate (what marks REM as discharged)

4. **Aggregate analysis**:
   - Total divergences by layer.
   - Total divergences by severity.
   - Cluster fixes (multiple divergences with same root cause = one fix; group them).
   - Estimate remediation time (HIGH severity = blocking, others = backlog).

5. **Master report** (`MIGRATION_AUDIT_REPORT_v1_0.md`):
   - Executive summary (one paragraph: did the migration succeed faithfully or not?)
   - Per-stream summary
   - Divergence register reference
   - Remediation plan reference
   - **Lockdown integrity statement**: does the divergence register invalidate Phase 14 lockdown? If HIGH-severity divergences exist in LOCKED entries, lockdown should be reopened until remediated. State explicitly.

6. **Atomic commit**. Title: `Forensic migration audit — <N divergences found, M HIGH severity>`.

## Done criteria

1. Every stream A–J has produced a divergence sub-report.
2. `MIGRATION_DIVERGENCE_REGISTER_v1_0.json` exists with one entry per divergence.
3. `MIGRATION_REMEDIATION_PLAN_v1_0.md` exists with one REM entry per DIV entry.
4. `MIGRATION_AUDIT_REPORT_v1_0.md` exists with executive summary, per-stream summary, lockdown integrity statement.
5. `verification_artifacts/MIGRATION_AUDIT/` contains all raw evidence.
6. Atomic commit landed.
7. If HIGH-severity divergences exist, the lockdown integrity statement explicitly says "Phase 14 lockdown should be reopened until remediated" — do not silently pass through.

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Audit finds HIGH-severity divergence in chart_facts (LLM extraction error) | Medium | HIGH | Stream E's ground-truth cross-check is built specifically for this; halt + surface; remediation = re-extract with stricter validation gate |
| Re-running chunker against current GCS produces different chunks than DB (chunker code changed post-14B) | Medium | HIGH | Stream C checks git log on chunkers after commit dc6d922; if changed, audit runs against frozen image SHA from build_manifests; harder but only valid path |
| Swiss Ephemeris version drift between bootstrap and audit | Low | MEDIUM | Pin pyswisseph version in audit; cross-check against `bootstrap_ephemeris.py` requirements.txt |
| 1000-sample ephemeris audit takes hours | Low | Low | Sample is parallelizable; can split across sessions if needed |
| GCS object versioning shows old version is live (re-upload regression) | Low | HIGH | Stream B captures `gcs_generation` + version count; if multi-version objects exist, surface; remediation = re-upload + delete stale version |
| Audit reveals a tool's runtime expectation diverges from DB schema (Phase 14C/D/E left a runtime gap) | Medium | MEDIUM | Audit is data-side only; if it surfaces a runtime gap, queue follow-up brief; do NOT fix in audit scope |
| Remediation plan for HIGH divergences blocks Phase 11B / Exec_15 | Medium | HIGH | If remediation is needed, native decides whether to halt downstream work or proceed with documented integrity gap. Audit's job is to surface; native's job is to decide. |
| Some local files have been edited since migration (audit detects local-vs-cloud diff but cause is local edit, not cloud corruption) | Medium | MEDIUM | For each L1 divergence, check git log on local file: any commit after the file's GCS upload timestamp? If yes, classify as "local edit post-migration; cloud is correct relative to migration moment; re-upload from current local source if you want them to match." |
| Audit takes longer than expected and the user wants to ship feature work | Low | Medium | Streams parallelize; the gating output for any new feature is the lockdown integrity statement, which can be produced after Streams A + B (the byte-level layer). Other streams provide depth but L1 byte-faithfulness is the load-bearing check. |

## Trigger phrase

"Read EXEC_BRIEF_FORENSIC_MIGRATION_AUDIT_v1_0.md and execute it."

## Notes for the executor

- **Read-only is sacrosanct.** No fixes during the audit. If you see something obviously wrong, write the divergence entry and resist the urge to "just fix it." Mixing diagnosis and remediation in the same session is how silent re-corruption happens. The remediation brief is its own session.

- **Streams parallelize aggressively.** Streams B–J only need GCS read + DB read + local file read. They write to disjoint subdirectories under `verification_artifacts/MIGRATION_AUDIT/`. Fan them out across sessions.

- **The byte-level audit (Stream B) is the load-bearing one.** If Stream B is 100% clean, you have a strong floor — the rest is auditing derivations from a known-faithful base. If Stream B has ANY mismatch, that's a HIGH severity finding that propagates up.

- **Chunker / extractor reproducibility requires version pinning.** Check git log on chunker and extractor files for commits after the relevant Phase 14 commit. If anything changed, the audit must run the *frozen* version (from the Docker image referenced in `build_manifests.pipeline_image_uri`) — not the current HEAD.

- **Local-edit-after-migration vs cloud-corruption distinction.** When Stream B finds a hash mismatch, the mitigation table covers this: check git log on the local file. If the local file was edited after its GCS upload timestamp, the cloud is correct *as of migration*; the divergence is intentional drift. Document and ask native whether to re-upload (sync local→cloud) or accept the drift.

- **The lockdown integrity statement at Stream K is non-negotiable.** Phase 14 was sealed on the assumption of faithful migration. If the audit finds otherwise, lockdown must be reopened. Don't soften that — write it plainly.

- **One big-picture question this audit should answer**: "If we deleted the local copies tomorrow, would we have lost anything?" Answer this in the executive summary of `MIGRATION_AUDIT_REPORT_v1_0.md`. If yes — name what would be lost. If no — say it explicitly. That's the question that motivates the whole audit.
