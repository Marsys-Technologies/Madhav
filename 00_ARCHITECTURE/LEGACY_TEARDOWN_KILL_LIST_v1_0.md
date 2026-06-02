---
artifact: LEGACY_TEARDOWN_KILL_LIST_v1_0.md
canonical_id: LEGACY_TEARDOWN_KILL_LIST
version: 1.0
status: DRAFT (teardown plan — native review; EXECUTION IS HUMAN-GATED + DESTRUCTIVE)
authored_by: Claude (Cowork) 2026-06-02
purpose: >
  The exhaustive kill-list for the clean-slate rebuild. Wipes every built data asset, the code
  that builds it, FORENSIC v8.0, and ALL tools (retrieval + MCP) + their catalogs. Keeps the
  serve shells (web consume agentic loop + provider adapters, the MCP server shell, portal,
  auth) and the isolated LEL ground-truth. Lists the coupling points so the kept shells compile
  and boot tool-less after the wipe.
safety: >
  Nothing here is executed from Cowork. This is a plan. Dropping prod tables, deleting code,
  tearing down infra are destructive + human-gated. Protocol: archive snapshot → guard couplings
  → drop → verify boot → squash baseline. Verify every table/path against the live DB + repo
  before any drop (some paths/counts below are inferred and must be confirmed).
boundary_confirmed_by_native_2026-06-02:
  - wipe all data assets + the build code that produces them
  - wipe FORENSIC v8.0 entirely
  - wipe ALL tools (retrieval + MCP) + manifest/registry catalogs; rebuild per layer
  - KEEP the agentic tool-loop shell + the MCP server shell (+ portal, auth, LEL)
---

# Legacy Teardown — Kill-List

## §1 — Principle

Two halves: **build side** (produces data) and **serve side** (answers queries). We wipe the
build side + all data + all tools; we keep the serve *shells* and re-fill them per layer. LEL
(life-event ground truth) is isolated and untouched. After teardown the system is a clean shell:
auth + chat + provider loop + MCP transport, **zero data, zero tools** — ready for Layer 0.

## §2 — DROP · data/asset tables (grouped; migration in parens)

- **Astronomical:** `ephemeris_daily` (+staging) (015); `panchanga_daily` (+staging) (060/069).
- **L1 chart facts:** `chart_facts` (+staging) (014); `chart_facts_history` (128); `chart_facts_supersedence` (129); `divisional_charts`/varga rows; `varshaphala` (025).
- **L1 temporal (per-chart):** `dasha_periods` (022); `chart_dashas` (135); `l1_time_synchronicity` (145); `l1_phase_locked_anchors` (146); `l1_bhrigu_bindu_transits` (142); `l1_graha_aspects_lifetime` (143); `l1_vedha_extended` (144); `l1_varsha_digest` (147); `l1_tajik_varsha_year_lords` (148).
- **Reference chakra tables:** `l1_sarvatobhadra_positions` + `l1_sarvatobhadra_vedha` (140); `l1_sapta_shalaka` + `l1_kalanala_chakra` + `l1_kota_chakra` + `l1_ckn_chakra` (141). *(Rebuilt clean as Layer-0 reference tables.)*
- **L2.5 synthesis:** all `l25_*` — `l25_msr_signals`, `l25_ucn_sections`/`l25_ucn_digests`, `l25_cdlm_links`/`l25_cdlm_cells`, `l25_cgm_nodes`, `l25_cgm_edges`, `l25_rm_resonances` (+ all `_staging`) (018/137).
- **L3 meta:** `l25_pattern_catalog`, `l25_divergence_ledger`, `l25_negative_space_map`, `l25_derivation_graph_nodes`/`_edges` (153); `l25_chart_lattice_snapshots` (152); `l25_vedha_anchor_interactions` (150).
- **RAG / corpus:** `rag_chunks` (+staging), `rag_embeddings` (+staging), `rag_graph_nodes`, `rag_graph_edges`, `rag_queries`, `rag_retrievals`, `rag_feedback`, `rag_reproducibility_failures` (005/013).
- **Classical text store:** `classical_texts` (053), `classical_chunks` (054), `classical_attributions` (055).
- **Discovery registers:** `pattern_register`, `resonance_register`, `cluster_register`, `contradiction_register` (+ all `_staging`) (019).
- **Build orchestration tables:** `build_manifests` (013), `builds` (+staging) (124), `build_steps` (125), `build_events` (118), `build_notifications` (127), `build_engine_versions` (126), `build_checkpoints` (159), `build_dependencies` (158), `chart_documents` (131), `chart_ayanamsha_reports` (130).
- **FORENSIC v8.0:** the file `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` + any rows derived from it.

## §3 — DROP · computed/legacy tables the sweeps mis-filed as KEEP (my correction — confirm)

These are corpus-derived or legacy, not ground-truth — they should drop with the rest:

- `sade_sati_phases` (+staging) (017) — **computed**, not LEL; folds into the engine. *(Only `life_events` is LEL.)*
- `school_signal_coverage`, `school_analysis_runs`, `convergence_scores`, `school_disagreements`, `multi_school_stances`, `school_convergence_index`, `data_source_expected` — corpus-derived multi-school analysis → DROP/rebuild.
- `pyramid_layers` (001) — old build-progress UI model, coupled to the dead build → DROP/rebuild for the new cockpit.
- `documents` (001), `predictions` (legacy, 062) — superseded → DROP.
- `mcp_bundle_cache`, `mcp_audit_findings` — caches/audit over old tools → DROP (rebuild with new tools).

## §4 — DROP · build code

- `platform/python-sidecar/pipeline/` — entire dir (`build_chart.py`, `dispatcher.py`, `writers/*`, `render/*`, `extractors/*`, `loaders/*`, `chunkers/*`, `linters/*`, all `bootstrap_*.py`, the L3 writers). ~70 files.
- `platform/python-sidecar/pyjhora_adapter/` — entire dir (~20 files).
- `.tools/` build scripts (`generate_ephemeris.py`, `generate_eclipses.py`, `generate_sade_sati.py`, `build_lel_v1_2.py`, etc.) — note: `build_lel_v1_2.py` is the LEL *builder*; keep its output (LEL) but the script can go.
- `tajik_tables.py` + any reference-constant modules (the hardcoded classical data → becomes Layer-0 tables).
- Any `natal_engine/` remnants.

## §5 — DROP · all tools + catalogs

- `platform/src/lib/retrieve/*` — all ~52 retrieval tools (delete; **stub `index.ts`** — see §8).
- `platform/src/lib/contract/tools/*` — 8 contract tool shapes.
- `platform-mcp/src/tools/*` — all ~90 MCP tool files (+ tests).
- Catalogs: `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`, `RETRIEVAL_INTERFACE_REGISTER_v1_0.md`, `INTERFACE_NORMALIZATION_REGISTER`, `VALIDATED_ASSET_REGISTRY_v1_0.json` — emptied; rebuilt per layer as each tool is authored.

## §6 — DROP · migrations, buckets, orchestration

- **Migrations:** squash 013–162 (platform) + the data-asset supabase migrations into a fresh `001_baseline.sql` (shell + auth + chat + LEL only). Keep an `ARCHIVE` doc recording dropped tables for audit. ~150 migrations collapse.
- **GCS:** purge `madhav-marsys-build-artifacts` (build state, manifests, ephemeris CSVs, extraction YAMLs, M9 Tajaka). **Keep** `madhav-astrology-chat-attachments`, `madhav-astrology-chart-documents`, `madhav-astrology-tf-state`.
- **Cloud Run:** delete the **`marsys-build-pipeline-job`** job. Keep `amjis-web`, `amjis-sidecar`, `amjis-mcp`.
- **Cloud Scheduler / IaC:** delete `build-reaper` + any build-trigger jobs; remove their SAs + IAM grants (`infra/cloud_scheduler/`, build SA roles in `infra/iam/`). Keep per-service runtime SAs.

## §7 — KEEP · the shells + isolated source

- **Serve shells:** `platform/src/lib/providers/*` (24 files — adapters, dispatcher, capabilities); the consume route `platform/src/app/api/chat/consult/route.ts`; the MCP server shell `platform-mcp/src/server.ts` (transport + auth, **minus** tool registrations).
- **Portal + auth:** `platform/src/app/*` (UI, auth routes); sidecar entrypoint shell.
- **Identity / chat:** `profiles`, `charts`, `chart_grants`, `conversations` + `conversation_*`, `projects`, `personas`, `selective_shares`, `pending_streams`.
- **LEL (ground truth, isolated):** `life_events` (+staging) (017) — **keep, untouched**.
- **Ops / governance / observability:** `mcp_api_keys`, `mcp_predictions`, `mcp_prediction_outcomes`, `mcp_disagreements`, `mcp_alerts_config`, `tool_registry`/`capability_tool_registry`, `audit_*`, `observatory`/telemetry, `llm_call_log`, `tool_execution_log`, `query_trace_steps`, `feature_flags`, `runtime_config`, `aiops_*`, `prediction_calibration`. *(These govern the serve loop; they survive but their tool/asset references get rebuilt.)*

## §8 — COUPLING POINTS to guard (so the kept shells boot tool-less)

Deleting all tools while keeping the loop + MCP server will break compile/boot unless these are stubbed:

1. `platform/src/lib/retrieve/index.ts` — **stub** `export const RETRIEVAL_TOOLS = []`; remove all tool imports; keep type + re-exports.
2. `platform/src/lib/retrieve/tool_catalogue.ts` — works with empty registry; no change (verify `getTool` returns null gracefully).
3. `platform/src/app/api/chat/consult/route.ts` — guard `getTool()` / `buildChatToolsFromNames()` for empty registry (return [] / handle null); the loop must answer "no tools available" cleanly.
4. `platform-mcp/src/server.ts` — remove all `register*` imports + calls (lines ~48–102, ~170–220); keep auth/transport/health; server boots with 0 tools.
5. Planner/manifest load — find where `CAPABILITY_MANIFEST.json` is read; handle empty manifest.
6. Synthesis/planner prompts — remove hardcoded tool/asset names.
7. Build API endpoints (`api/build/*`, `api/charts/*`) — remove pipeline invocations; keep result-serving shells (will be rebuilt for the new cockpit).

## §9 — Execution protocol (human-gated, in order)

1. **Archive** — snapshot all DROP tables + GCS prefixes to cold storage (audit trail), tag a git branch with current code.
2. **Guard couplings** (§8) in a branch — stub registries, strip MCP registrations, guard route — verify `tsc` + local boot of web + MCP with **0 tools**.
3. **Delete build code + tools + catalogs** (§4–§5) in the same branch; re-verify build/boot.
4. **Drop tables** (§2–§3) via reviewed SQL; **tear down** job + scheduler + bucket + IaC build pieces (§6).
5. **Squash migrations** to the fresh baseline (§6).
6. **Verify** — web loads (auth + chat), MCP server boots, consume loop answers "no tools yet" cleanly; no dangling references.
7. **Seal** — record in a teardown-close artifact; this clears the deck for Layer 0.

## §10 — End state

A clean shell: auth, chat, the provider/agentic loop, the MCP transport — **zero data, zero tools, zero legacy migrations** — onto which we build Layer 0 → Layer 3 fresh, each asset shipping with its own layer-appropriate tool.

---

*End of LEGACY_TEARDOWN_KILL_LIST v1.0 — DRAFT, 2026-06-02. Destructive + human-gated. Verify
every item against live DB + repo before execution.*
