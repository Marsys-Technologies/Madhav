---
artifact: LEGACY_TEARDOWN_CLOSE_v1_0.md
canonical_id: LEGACY_TEARDOWN_CLOSE
version: 1.0
status: COMPLETE
authored_by: Claude Code (LEGACY-TEARDOWN-S1)
session_branch: feature/legacy-teardown
date: 2026-06-02
governing_spec: 00_ARCHITECTURE/LEGACY_TEARDOWN_KILL_LIST_v1_0.md
brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_LEGACY_TEARDOWN_v1_0.md
---

# Legacy Teardown — Session Close

## §1 — Acceptance criteria (AC) status

| AC | Description | Result |
|----|-------------|--------|
| AC.1 | Worktree created; `pre-legacy-teardown` tag; `00_archive.sh` authored | PASS |
| AC.2 | Coupling guards: `retrieve/index.ts` stubbed; `contract/registry.ts` stubbed; MCP `server.ts` stripped; route.ts/planner safe for empty registry | PASS |
| AC.3 | Build code deleted: `pipeline/` (279 files), `pyjhora_adapter/` (20 files), `tools/generate_derivation_ledger_stubs.py` | PASS |
| AC.4 | All tools deleted: 81 retrieve files + tests, 8 contract/tools, 108 MCP tool files; registers emptied (CAPABILITY_MANIFEST already empty; RETRIEVAL_INTERFACE_REGISTER + INTERFACE_NORMALIZATION_REGISTER + VALIDATED_ASSET_REGISTRY → WIPED) | PASS |
| AC.5 | `FORENSIC_ASTROLOGICAL_DATA_v8_0.md` (1,938 lines) deleted | PASS |
| AC.6 | `platform/migrations/001_baseline.sql` (1,503 lines, 34 sections, all KEEP tables); migrations 001–163 archived to `_archive/`; `01_drop_tables.sql` written (65 DROP tables) | PASS |
| AC.7 | Operator scripts authored under `infra/teardown/`: `00_archive.sh`, `01_drop_tables.sql`, `02_purge_gcs.sh`, `03_delete_cloud_run_job.sh`, `04_delete_scheduler.sh`, `05_iac_diff.tf`; `cloudbuild.yaml` build pipeline steps removed | PASS |
| AC.8 | `tsc --noEmit` clean (0 new `src/` errors, platform-mcp 0 errors); no dangling imports; FORENSIC gone; operator scripts present; this close artifact authored; PR opened | PASS |

## §2 — Files deleted (summary)

| Category | Count |
|----------|-------|
| Python pipeline code (`pipeline/` + `pyjhora_adapter/` + `tools/`) | 300 files |
| Retrieval tools (`retrieve/*`, `contract/tools/*`) | 89 files |
| MCP tool files (`platform-mcp/src/tools/*`) | 108 files |
| FORENSIC v8.0 | 1 file (1,938 lines) |
| **Total deleted** | **~498 files** |

## §3 — Operator scripts written

All scripts are under `infra/teardown/` — **do not run via automation**.

| Script | Purpose | Run order |
|--------|---------|-----------|
| `00_archive.sh` | Snapshot DROP tables + build GCS bucket to cold storage | 1st (always first) |
| `01_drop_tables.sql` | DROP all 65 legacy data tables (psql) | 2nd |
| `02_purge_gcs.sh` | Delete `madhav-marsys-build-artifacts` GCS bucket | 3rd |
| `03_delete_cloud_run_job.sh` | Delete `marsys-build-pipeline-job` Cloud Run Job | 4th |
| `04_delete_scheduler.sh` | Delete `build-reaper` Scheduler + SA | 5th |
| `05_iac_diff.tf` | Documents IaC resources to remove (guidance only) | After 04 |

## §4 — Tables listed for DROP (operator action required)

65 tables across categories (see `infra/teardown/01_drop_tables.sql`):

- **Astronomical (2+staging):** `ephemeris_daily`, `panchanga_daily`
- **L1 chart facts (5):** `chart_facts`, `chart_facts_history`, `chart_facts_supersedence`, `divisional_charts`, `varshaphala`
- **L1 temporal (9):** `dasha_periods`, `chart_dashas`, `l1_time_synchronicity`, `l1_phase_locked_anchors`, `l1_bhrigu_bindu_transits`, `l1_graha_aspects_lifetime`, `l1_vedha_extended`, `l1_varsha_digest`, `l1_tajik_varsha_year_lords`
- **Chakra tables (6):** `l1_sarvatobhadra_*`, `l1_sapta_shalaka`, `l1_kalanala_chakra`, `l1_kota_chakra`, `l1_ckn_chakra`
- **L2.5 synthesis (8+staging):** all `l25_*` tables
- **L3 meta (7):** `l25_pattern_catalog`, `l25_divergence_ledger`, `l25_negative_space_map`, `l25_derivation_graph_*`, `l25_chart_lattice_snapshots`, `l25_vedha_anchor_interactions`
- **RAG/corpus (10):** `rag_chunks`, `rag_embeddings`, `rag_graph_*`, `rag_queries`, `rag_retrievals`, `rag_feedback`, `rag_reproducibility_failures`
- **Classical text (3):** `classical_texts`, `classical_chunks`, `classical_attributions`
- **Discovery registers (4+staging):** `pattern_register`, `resonance_register`, `cluster_register`, `contradiction_register`
- **Build orchestration (10):** `build_manifests`, `builds`, `build_steps`, `build_events`, `build_notifications`, `build_engine_versions`, `build_checkpoints`, `build_dependencies`, `chart_documents`, `chart_ayanamsha_reports`
- **§3 corrections (12):** `sade_sati_phases`, multi-school tables, `pyramid_layers`, `documents`, `predictions`, `mcp_bundle_cache`, `mcp_audit_findings`, `audit_job_runs`, `eclipses_retrogrades`, `msr_signals`, `signal_states`, `kp_sublords`

## §5 — Kill-list mismatches found

| Item | Note |
|------|------|
| `.tools/` directory | Not present in worktree (may only exist on main dev machine). If present, delete manually. |
| `natal_engine/` | Directory exists but is empty — no files to delete. |
| `CAPABILITY_MANIFEST.json` | Already had `"entries": []` before teardown — no tool/asset entries to wipe. |
| `tajik_tables.py` | Located inside `pipeline/` (deleted with AC.3), not at repo root. Kill-list path was approximate. |

## §6 — What is kept (ground truth)

- `platform/src/lib/providers/**` — all 5 provider adapters (untouched)
- `platform/src/app/api/chat/consult/route.ts` — serve shell (untouched)
- `platform-mcp/src/server.ts` — MCP transport shell (tools stripped, auth/health kept)
- `platform/src/app/**` — portal, auth routes (untouched)
- `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` — LEL ground truth (untouched)
- `life_events` + `life_events_staging` DB tables (in new baseline, untouched)
- All `conversations*` / chat tables (in new baseline, untouched)

## §7 — Operator checklist to complete the teardown

After PR is reviewed and merged to main:

- [ ] **Step 1:** Run `infra/teardown/00_archive.sh` — verify ARCHIVE_MANIFEST.txt in GCS
- [ ] **Step 2:** Scale `amjis-web` + `amjis-sidecar` to 0 instances
- [ ] **Step 3:** Run `infra/teardown/01_drop_tables.sql` against production DB
- [ ] **Step 4:** Scale services back to 1 instance; verify boot
- [ ] **Step 5:** Run `infra/teardown/02_purge_gcs.sh`
- [ ] **Step 6:** Run `infra/teardown/03_delete_cloud_run_job.sh`
- [ ] **Step 7:** Run `infra/teardown/04_delete_scheduler.sh`
- [ ] **Step 8:** Apply IaC changes per `infra/teardown/05_iac_diff.tf`
- [ ] **Step 9:** Run `platform/migrations/001_baseline.sql` on a scratch DB; verify all KEEP tables created
- [ ] **Step 10:** Proceed to Layer-0 rebuild

---

*Sealed by LEGACY-TEARDOWN-S1, 2026-06-02. Governing brief: CLAUDECODE_BRIEF_LEGACY_TEARDOWN_v1_0.md. Status: HALT after PR — do not merge without native review.*
