---
plan_id: MACRO_PLAN_SYSTEM_AUDIT
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-28
context: Comprehensive system audit + repair after Phase 11A→13 surfaced multiple integration gaps. Native explicitly requested a macro plan covering credentials, data sources, GCP services, manifest, pipeline, tools, UI, embeddings, and end-to-end verification.
output: A series of EXEC briefs (one per phase below), each independently triggerable, with explicit dependency ordering.
---

# MACRO PLAN — Complete System Audit + Repair

## Why this plan exists

Over the last several days we have:
- Shipped the Phase 0–9 architecture (1,100+ tests).
- Flipped the new pipeline to default-on (Phase 11A).
- Discovered three architectural gaps in Phase 11A.DEBUG (bundle had names not content; chart context not plumbed; vector_search not authorized).
- Repaired the data-layer plumbing in Phase 12.
- Discovered a fourth gap in Phase 13: vector_search SQL filtered on a phantom `native_id` column, causing every vector_search call to silently fail.

The pattern is consistent: every gap was invisible to mocked unit tests. Every gap was found only when real LLMs hit real data. Some gaps were trivial to fix (missing prop, missing flag, missing column). One was foundational (bundle content loading was never built). One I should have flagged but didn't (the OpenAI API key — Phase 7 names `gpt-4-1` as a default panel member, Phase 12 Stream E requires OpenAI + Google + Anthropic keys, and I never asked you to confirm the keys are set).

This macro plan systematically audits **every layer** end-to-end, finds every remaining gap, and either fixes it or scopes a follow-up brief. It is intended to bring the system to a state where every assumption has been verified, not just specified.

## Honest framing of what's likely to be found

I expect this audit to surface some combination of:
- **Credentials gaps**: OpenAI (confirmed missing per native), maybe Google/DeepSeek too, possibly Vertex AI ADC scoping issues.
- **Schema-vs-code mismatches** like the `native_id` Phase 13 found — there are likely more elsewhere (rag_graph_nodes, rag_graph_edges, msr_signals, prediction_ledger, audit_log).
- **Manifest drift**: entries whose paths no longer exist, fingerprints that don't match current file content, version strings that disagree with frontmatter.
- **GCS bucket vs filesystem drift**: source files in the repo that aren't uploaded to GCS, or GCS files that diverge from the repo source.
- **Tool implementations that compile but fail in production**: Phase 9 shipped 10 tools; vector_search just turned out to be silently broken; the other 9 deserve the same scrutiny.
- **UI-prop chains that work in some routes and break in others**: per-client vs root consume routes were the Phase 11A bug; there may be analogous issues in the audit view, panel UI, etc.
- **Migrations that exist as files but aren't applied to the live DB**: Phase 13 found migration 011 was on disk but unapplied. Migrations 008–012 should all be re-verified.
- **L1 corpus completeness**: whether FORENSIC v8.0 actually carries every degree, nakshatra, pada, and house cusp the user expects.

Plan accordingly: this is not a 1-day exercise. Realistic timeline is 5–10 Claude Code sessions across the phases, plus several rounds of native verification.

## Plan structure

The plan has nine phases (A–I), each producing one or more execution briefs. Phases are sequenced so that earlier phases don't depend on later phases, but later phases can reuse earlier-phase findings. Each phase has its own pre-flight gate, scope, streams, done criteria, and risk classification — same pattern as every prior brief.

```
Phase A: Foundation (credentials, env, GCP services, dev hygiene)
   ↓
Phase B: Data Layer (L1 facts, MSR, CGM, UCN, CDLM, RM)
   ↓                 ↘
Phase C: Embedding +  Phase D: Schema + Migrations
   Index Audit          ↓
   ↓                  Phase E: Pipeline Code (router, bundle, tools, synthesis, validators, checkpoints)
   ↘                ↙
       Phase F: UI Audit
       ↓
       Phase G: End-to-End Verification
       ↓
Phase H: Manifest + Governance
   ↓
Phase I: Documentation + Closeout
```

Phases C and D can run in parallel after Phase B. Phase F can begin after Phase E ships its brief outputs; it doesn't need E to be COMPLETE first.

---

## PHASE A — Foundation Audit

**Goal:** every credential, every env variable, every GCP service, every cache state — verified before any other audit begins. Without this, downstream verifications produce false negatives because a missing API key or stale Auth Proxy looks identical to a code bug.

### Brief A.1 — Credentials & API Keys Audit

**Mission:** confirm every external-service credential the system depends on is present, valid, and properly scoped.

**Streams:**
1. **Anthropic API key** — verify present in env (`ANTHROPIC_API_KEY`); test a 1-token call to confirm it works.
2. **OpenAI API key** — verify `OPENAI_API_KEY` set; test a 1-token call to gpt-4 or gpt-4-1; **flag explicitly to native if missing** (this is the open gap I should have surfaced earlier).
3. **Google AI / Gemini API key** — verify `GOOGLE_API_KEY` or `GEMINI_API_KEY` set (the audit will confirm which env var name the code reads); test a 1-token call to gemini-1.5-pro.
4. **DeepSeek API key** — verify `DEEPSEEK_API_KEY` set (Phase 7 default adjudicator family); test a 1-token call.
5. **Vertex AI ADC** — verify `GOOGLE_APPLICATION_CREDENTIALS` is set OR `gcloud auth application-default login` is active; test an embedding call against `text-multilingual-embedding-002`.
6. **Cloud SQL credentials** — verify `DB_PASSWORD` is in Secret Manager and accessible to dev; verify `DB_USER` and `DB_NAME` are correct.
7. **Firebase Admin** — verify session-cookie verification works (the auth gate on `/audit` and `/clients/[id]/consume`).
8. **GCS service account** — verify the service account that signs URLs and reads/writes the chart-attachments + chart-documents buckets has the right permissions.
9. **Output report**: `platform/scripts/audit/A1_credentials_report.md` with green/red status per credential, plus a "what to do if red" section per failure.

**Risk:** LOW (read-only test calls). **Required prerequisites:** none. **Estimated effort:** 30 minutes.

### Brief A.2 — GCP Services Audit

**Mission:** every GCP service the platform depends on is up, accessible, and on the version we expect.

**Streams:**
1. **Cloud Run services** — `amjis-web` and `amjis-sidecar` health checks; verify deployed revision matches latest commit.
2. **Cloud SQL `amjis-postgres`** — instance state, region, tier, connection string discoverable via `gcloud sql instances describe amjis-postgres`.
3. **GCS buckets** — `madhav-astrology-chat-attachments` + `madhav-astrology-chart-documents` exist; lifecycle rules; access permissions.
4. **Firebase Auth** — project ID matches; OAuth providers configured.
5. **Secret Manager** — list secrets; verify `amjis-db-password` exists and the dev service account can read it.
6. **Cloud Build** — last build status; build trigger health.
7. **Artifact Registry** — Docker images present for both Cloud Run services.
8. **Cloud Load Balancer** — `madhav.marsys.in` resolves to static IP `34.54.231.91`; SSL cert valid; backend services healthy.
9. **Output report**: `platform/scripts/audit/A2_gcp_services_report.md`.

**Risk:** LOW (read-only via `gcloud`). **Required prerequisites:** A.1 service account auth. **Estimated effort:** 30 minutes.

### Brief A.3 — Environment Variables Audit

**Mission:** every env var the code reads is set in every environment that uses it (`.env`, `.env.local`, Cloud Run env, Cloud Run secret refs).

**Streams:**
1. Grep `process.env.X` across all of `platform/src/`. Build a list of every env var the code reads.
2. For each env var: is it documented in `.env.example`? Is it set in `.env.local`? Is it set on Cloud Run for `amjis-web`? Is it set on Cloud Run for `amjis-sidecar`? Is it injected from Secret Manager (good) or hardcoded in the deployment (bad)?
3. Build a matrix: env var × environment × present/absent.
4. Flag any env var that the code reads but no environment sets — that's a guaranteed runtime failure waiting to happen.
5. Flag any env var that's set in dev but not in prod, or vice versa — likely a deploy-time accident.
6. **Output**: `platform/scripts/audit/A3_env_matrix.md` with the matrix and a "needs fixing" section.

**Risk:** LOW. **Required prerequisites:** A.1 + A.2. **Estimated effort:** 45 minutes.

### Brief A.4 — Dev Hygiene + Build Cache State

**Mission:** confirm the dev server's running code matches what's on disk (the singleton + Next.js cache problem we hit twice now).

**Streams:**
1. List all running node/next processes; flag any that have been running > 1 day (likely stale).
2. Check `.next/BUILD_ID` against git HEAD modification times; flag if BUILD_ID is older than the last code change.
3. Document a clean-restart procedure (kill + `rm -rf .next` + restart) and add it as `npm run dev:clean`.
4. Add a singleton-refresh signal: when `feature_flags.ts` is modified, the dev server should automatically refresh the singleton. Investigate whether Next.js 16.2.4 with Turbopack supports this; if not, document the limitation.
5. **Output**: `platform/scripts/audit/A4_dev_hygiene_report.md`.

**Risk:** LOW. **Required prerequisites:** none. **Estimated effort:** 20 minutes.

---

## PHASE B — Data Layer Audit

**Goal:** every L1 fact, every L2 derivation, every L2.5 holistic synthesis artifact — accounted for, current, complete.

### Brief B.1 — FORENSIC v8.0 Completeness Audit

**Mission:** does FORENSIC v8.0 actually carry every fact the system needs to answer chart questions?

**Streams:**
1. Read FORENSIC v8.0 end-to-end. Build a structured catalog (same shape as Phase 13's Stream A): for every planet, every house cusp, every ayanamsha-relevant constant, every nakshatra-and-pada — is the value present?
2. Build a per-fact present/absent table.
3. Identify gaps. For each gap, classify:
   - **Truly missing**: data should be in FORENSIC but isn't.
   - **Lives elsewhere**: data is in MSR signals or rag_chunks but not in FORENSIC.
   - **Out-of-scope**: data requires external computation per B.10 (legitimate `[EXTERNAL_COMPUTATION_REQUIRED]`).
4. For each "truly missing" gap, propose a v8.1 minor bump with the missing values, sourced from the user's chart records.
5. **Output**: `platform/scripts/audit/B1_forensic_audit.md` + `platform/scripts/audit/B1_forensic_catalog.json`.

**Risk:** LOW (audit-only; v8.1 bump is a follow-up brief). **Required prerequisites:** none. **Estimated effort:** 1.5 hours.

### Brief B.2 — MSR Signals Audit

**Mission:** all 499 signals present, well-formed, with correct schema.

**Streams:**
1. Query `msr_signals` for total count; assert = 499 (or document if changed).
2. Schema validation: every row has the required fields (`signal_id`, `subject`, `claim_text`, `significance_score`, `derivation_ledger`, etc.).
3. Cross-check against `MSR_v3_0.md` source-of-truth: every signal in the MD file is in the DB; every DB row traces back to the MD file.
4. Identify signals with missing `derivation_ledger` (B.3 violation), missing significance scores, or other shape issues.
5. **Output**: `platform/scripts/audit/B2_msr_audit.md`.

**Risk:** LOW. **Required prerequisites:** A.1 + Auth Proxy. **Estimated effort:** 1 hour.

### Brief B.3 — CGM Graph Audit

**Mission:** rag_graph_nodes and rag_graph_edges are complete, schema-consistent, and queryable.

**Streams:**
1. Count nodes (target ~1752 per memory), count edges (target ~3911), count reconciled SUPPORTS/CONTRADICTS edges (target ~22).
2. Schema check: every node has the fields cgm_graph_walk expects; every edge has source/target that exist in nodes.
3. Test cgm_graph_walk against live DB: BFS depth-1 from a known node returns expected results.
4. Verify the SUPPORTS/CONTRADICTS edge count matches CGM_v9_0.md.
5. **Output**: `platform/scripts/audit/B3_cgm_audit.md`.

**Risk:** LOW. **Required prerequisites:** Auth Proxy. **Estimated effort:** 45 minutes.

### Brief B.4 — UCN, CDLM, RM Audit

**Mission:** the L2.5 holistic-synthesis artifacts are present in the DB or filesystem in the form retrieval expects.

**Streams:**
1. UCN_v4_0.md — read source; query whichever DB table or file location synthesis expects; confirm consistency.
2. CDLM_v1_1.md — same.
3. RM_v2_0.md — same.
4. For each: are the chunks embedded into rag_chunks? Or are they loaded directly from filesystem at compose time? The architecture should be consistent across these three.
5. **Output**: `platform/scripts/audit/B4_holistic_audit.md`.

**Risk:** LOW. **Required prerequisites:** Auth Proxy. **Estimated effort:** 1 hour.

### Brief B.5 — Asset → Manifest Cross-Check

**Mission:** every entry in `CAPABILITY_MANIFEST.json` points at a real file with the right content hash.

**Streams:**
1. Parse `CAPABILITY_MANIFEST.json`. For each entry: does the file exist at the named path? Compute its current sha256; does it match the manifest's stored hash? Does the version string match the file's frontmatter version?
2. Categorize discrepancies: (a) file missing entirely, (b) file present but content drifted (hash mismatch), (c) version drift (frontmatter says v8.1 but manifest says v8.0).
3. For each discrepancy, propose the minimal fix: re-hash the manifest entry, OR move/restore the file, OR bump the version.
4. **Output**: `platform/scripts/audit/B5_manifest_crosscheck.md`.

**Risk:** LOW. **Required prerequisites:** none. **Estimated effort:** 1 hour.

### Brief B.6 — GCS vs Filesystem Drift Audit

**Mission:** every source artifact that should be in GCS is there with current content; nothing critical lives only in the local repo.

**Streams:**
1. List GCS buckets `madhav-astrology-chat-attachments` and `madhav-astrology-chart-documents`.
2. For each L1/L2/L2.5 artifact (FORENSIC, MSR, CGM, UCN, CDLM, RM), determine whether it's expected to live in GCS. If yes: is it there? Does its content match the current local file?
3. Flag any artifact that lives only locally — that's a deployment risk (production Cloud Run instances won't have the file).
4. **Output**: `platform/scripts/audit/B6_gcs_drift.md`.

**Risk:** LOW (read-only). **Required prerequisites:** A.1 service account. **Estimated effort:** 1 hour.

---

## PHASE C — Embedding + Index Audit

### Brief C.1 — rag_chunks Audit

**Mission:** all 993 chunks present, embedded correctly, with valid metadata.

**Streams:**
1. Count rows. Assert ~993 (memory says post-Exec_6).
2. For each `doc_type`: how many chunks? Cross-check counts against the source documents.
3. Check `embedding` column dimension (should be 768 per Phase 9 hotfix).
4. Find chunks where `embedding IS NULL` (un-embedded). Should be 0; if not, schedule re-embed for those rows.
5. Find chunks with content length < 50 chars (likely junk) or > 4000 chars (likely chunk-boundary issue).
6. Sample 10 chunks per doc_type; print first 200 chars to confirm content shape is sensible.
7. **Output**: `platform/scripts/audit/C1_rag_chunks_audit.md`.

**Risk:** LOW. **Required prerequisites:** Auth Proxy. **Estimated effort:** 1 hour.

### Brief C.2 — rag_embeddings Audit

**Mission:** every chunk has a valid embedding; HNSW index is healthy.

**Streams:**
1. Count rag_embeddings rows. Assert match with rag_chunks (993 ÷ 977 — investigate the 16-row gap).
2. Verify dimension: every row's vector length = 768.
3. Schema audit: confirm column names match what `vector_search.ts` queries (this is exactly the Phase 13 bug — investigate every column reference vector_search.ts uses against the actual schema).
4. HNSW p95 latency check (target ≤ 100ms).
5. Run a known-good vector_search query against the live DB; confirm it returns results in the expected order.
6. **Output**: `platform/scripts/audit/C2_rag_embeddings_audit.md`.

**Risk:** LOW. **Required prerequisites:** Auth Proxy. **Estimated effort:** 1 hour.

### Brief C.3 — rag_graph_nodes / rag_graph_edges Schema Consistency

**Mission:** the graph schema matches what cgm_graph_walk and other tools query.

**Streams:**
1. Read `cgm_graph_walk.ts` (or wherever it lives in `platform/src/lib/retrieve/`). For every column it references in nodes/edges tables: does that column actually exist?
2. Same drill for any other tool that touches the graph.
3. Run cgm_graph_walk against live DB with a known seed node; confirm it returns sensible results.
4. **Output**: `platform/scripts/audit/C3_graph_schema_audit.md`.

**Risk:** LOW. **Required prerequisites:** Auth Proxy. **Estimated effort:** 45 minutes.

### Brief C.4 — Re-embed Anything Stale or Missing

**Mission:** if Brief C.1 or C.2 finds gaps, run the re-embedding pipeline for those rows.

**Streams:**
1. Read the missing-chunks list from C.1.
2. Invoke the python sidecar's embedding pipeline (`platform/python-sidecar/rag/embed.py` — frozen for code, but invocable for execution) to re-embed those rows.
3. Verify embeddings landed.
4. **Output**: `platform/scripts/audit/C4_reembed_report.md`.

**Risk:** MEDIUM (writes to rag_embeddings; affects retrieval). **Required prerequisites:** C.1, C.2 complete + Auth Proxy. **Estimated effort:** depends on chunk count; ~1 minute per chunk via Vertex AI.

### Brief C.5 — pgvector HNSW Index Tuning Check

**Mission:** confirm HNSW parameters are reasonable for our dataset size.

**Streams:**
1. Inspect the current HNSW index params (`m`, `ef_construction`, `ef_search`).
2. Run latency benchmarks at top_K=10 and top_K=20 (Phase 13 bumped the default to 20).
3. If p95 > 200ms at top_K=20, propose parameter tuning.
4. **Output**: `platform/scripts/audit/C5_hnsw_tuning.md`.

**Risk:** LOW (measurement-only). **Required prerequisites:** Auth Proxy. **Estimated effort:** 30 minutes.

---

## PHASE D — Schema + Migration Audit

### Brief D.1 — Migration Application State

**Mission:** every migration in `platform/supabase/migrations/` is applied to live DB.

**Streams:**
1. List migration files (008–012 known; check for any newer).
2. Query the migrations tracking table (whatever Supabase CLI uses) for what's actually applied.
3. Reconcile: for each migration, is it on disk? Applied to dev DB? Applied to prod DB?
4. Phase 13 found 011 was on disk but unapplied — verify this didn't recur for any other migration.
5. **Output**: `platform/scripts/audit/D1_migrations_state.md`.

**Risk:** LOW. **Required prerequisites:** Auth Proxy. **Estimated effort:** 30 minutes.

### Brief D.2 — Schema-vs-Code Cross-Reference

**Mission:** every SQL query in the codebase references columns that actually exist.

**Streams:**
1. Grep all `.ts` files for SQL strings (look for `SELECT`, `INSERT`, `UPDATE`, `DELETE` patterns).
2. For each SQL string, parse out the table name and the column references.
3. Cross-check against the live DB's `information_schema.columns`.
4. Flag every column reference that doesn't exist in the named table — these are silent runtime errors waiting to happen (the Phase 13 `native_id` bug).
5. **Output**: `platform/scripts/audit/D2_schema_code_xref.md` with a "broken queries" list.

**Risk:** LOW (read-only). **Required prerequisites:** Auth Proxy. **Estimated effort:** 2 hours.

This brief is the most likely to surface additional `native_id`-style bugs hiding in other tools. **High-value brief.**

### Brief D.3 — Foreign Key + Referential Integrity

**Mission:** every FK constraint that should exist does; orphan rows are flagged.

**Streams:**
1. List all FK constraints in the live DB.
2. Spot-check expected relationships: chart→profiles, conversation→chart, message→conversation, audit_log→chart, prediction_ledger→audit_log.
3. Find any orphans (rows whose FK target no longer exists).
4. **Output**: `platform/scripts/audit/D3_fk_integrity.md`.

**Risk:** LOW. **Required prerequisites:** Auth Proxy. **Estimated effort:** 30 minutes.

---

## PHASE E — Pipeline Code Audit

### Brief E.1 — Router End-to-End Verification

**Mission:** the router classifies all 8 query classes correctly against real Claude Haiku.

**Streams:**
1. Read `platform/src/lib/router/**`. Identify every query class.
2. For each class, construct 3 representative queries.
3. Run `pipeline:accuracy-test` (Phase 3 deliverable) against real Claude Haiku.
4. Report classification accuracy per class.
5. Flag any class where accuracy < 80%.
6. **Output**: `platform/scripts/audit/E1_router_accuracy.md`.

**Risk:** LOW. **Required prerequisites:** Anthropic API key + Auth Proxy. **Estimated effort:** 30 minutes.

### Brief E.2 — Bundle Composer Content Loading

**Mission:** Phase 12's bundle content loading actually works for every query class.

**Streams:**
1. For each of 8 query classes, trigger a query and capture the bundle that gets composed.
2. Inspect each bundle: does it contain references AND content? What's the content size? Are floor-role assets (FORENSIC, MSR, CGM) actually loading?
3. Flag any class where bundle is references-only (the Phase 12 fix didn't cover that class) or content is suspiciously small.
4. **Output**: `platform/scripts/audit/E2_bundle_content.md`.

**Risk:** LOW. **Required prerequisites:** all credentials + Auth Proxy. **Estimated effort:** 1 hour.

### Brief E.3 — Every Retrieval Tool Tested Against Live DB

**Mission:** all 10 tools shipped in Phase 9 (7 Phase 2 + 3 Phase 9) work against the live DB. **Phase 13 found vector_search broken silently. The other 9 deserve the same scrutiny.**

**Streams:**
1. Enumerate the 10 tools from `platform/src/lib/retrieve/index.ts` `RETRIEVAL_TOOLS` registry.
2. For each tool, write a smoke test that calls it directly with realistic params and verifies it returns sensible non-empty results.
3. Each tool's smoke is a separate sub-stream. Tools include (memory-derived):
   - msr_sql
   - cgm_graph_walk (Phase 9)
   - manifest_query (Phase 9)
   - vector_search (Phase 9, post-fix)
   - and 6 others from Phase 2
4. For any tool that returns empty/errors: capture the SQL or API call, diagnose the issue (likely another schema mismatch), apply surgical fix or recommend follow-up.
5. **Output**: `platform/scripts/audit/E3_tools_smoke.md` with per-tool ✅/✗.

**Risk:** MEDIUM (may surface multiple Phase-13-style bugs). **Required prerequisites:** all credentials + Auth Proxy. **Estimated effort:** 3 hours.

This brief is **the highest-value brief in Phase E**. It's where most remaining "silent failures" likely live.

### Brief E.4 — Synthesis Orchestrator + Strategies

**Mission:** single-model and panel strategies both produce well-formed output.

**Streams:**
1. Run a real LLM smoke through `single_model_strategy.ts` for each query class.
2. Run a real LLM smoke through `panel_strategy.ts` with PANEL_MODE_ENABLED=true and panel_opt_in=true. Verify family-exclusion + anonymization actually hold.
3. Verify checkpoints fire at 4.5/5.5/8.5 when their flags are on.
4. **Output**: `platform/scripts/audit/E4_synthesis_smoke.md`.

**Risk:** MEDIUM (live LLM calls; cost ~$2-5). **Required prerequisites:** all credentials. **Estimated effort:** 1.5 hours.

### Brief E.5 — Validators (P1/P2/P5)

**Mission:** structural validators catch the failures they're supposed to and don't catch what they aren't.

**Streams:**
1. Construct synthetic synthesis outputs that violate P1 (layer mixing), P2 (broken citation), and P5 (signal_id not in bundle).
2. Run each through the validators; verify it's caught.
3. Construct compliant outputs; verify they pass.
4. **Output**: `platform/scripts/audit/E5_validators.md`.

**Risk:** LOW (synthetic data only). **Required prerequisites:** none. **Estimated effort:** 1 hour.

### Brief E.6 — Checkpoints (4.5/5.5/8.5)

**Mission:** Phase 6's checkpoints actually work as live LLM calls when their flags are on.

**Streams:**
1. Enable each checkpoint flag individually.
2. Run a real query; verify the checkpoint fires.
3. Verify the structured prediction extractor in 8.5 produces a valid Prediction object when the synthesis is time-indexed, and omits it otherwise.
4. **Output**: `platform/scripts/audit/E6_checkpoints.md`.

**Risk:** LOW. **Required prerequisites:** all credentials + Auth Proxy. **Estimated effort:** 1 hour.

### Brief E.7 — Disclosure Tier Filter

**Mission:** all 4 tiers (super_admin, acharya_reviewer, client, public_redacted) correctly filter content.

**Streams:**
1. For each tier, send a synthesis output that contains methodology, redactable signals, etc.
2. Verify the filter strips appropriately for client/public_redacted tiers.
3. Verify super_admin pass-through works.
4. **Output**: `platform/scripts/audit/E7_disclosure.md`.

**Risk:** LOW. **Required prerequisites:** none. **Estimated effort:** 30 minutes.

---

## PHASE F — UI Audit

### Brief F.1 — Component Tree Audit

**Mission:** every component shipped in Phases 5/7/8 is reachable, renders, and is wired to the right data.

**Streams:**
1. For each component (StreamingAnswer, AnswerView, CitationChip, CitationPreview, DisclosureTierBadge, ValidatorFailureView, PanelAnswerView, DivergenceReport, audit-tree views): is it imported by a route that's reachable?
2. For each route, is it gated correctly (super_admin auth, etc.)?
3. Visual smoke: open each route in browser, screenshot, attach to report.
4. **Output**: `platform/scripts/audit/F1_component_tree.md`.

**Risk:** LOW. **Required prerequisites:** all of Phase A + dev server running. **Estimated effort:** 1.5 hours.

### Brief F.2 — DisclosureTierBadge Visibility (UX gap from earlier)

**Mission:** address the empty-state UX gap where users can't tell whether the new pipeline is active.

**Streams:**
1. Make `DisclosureTierBadge` render unconditionally in the sticky header (not just after the first message).
2. Add a small "running new pipeline" indicator visible on initial page load.
3. Test fresh-page, post-query, and validator-halt states.
4. **Output**: `platform/scripts/audit/F2_disclosure_visibility.md` + ~10 lines of code change.

**Risk:** LOW. **Required prerequisites:** none. **Estimated effort:** 30 minutes.

### Brief F.3 — Audit View Spot-Check

**Mission:** all 4 audit routes (/audit, /audit/[query_id], /audit/predictions, /audit/compare) work end-to-end with real data.

**Streams:**
1. Submit a few test queries to populate audit_log.
2. Navigate the audit list, drill into one row, verify all 8 sections render.
3. Try the prediction outcome form; verify sacrosanct rule (rejects future-horizon).
4. Try compare view side-by-side.
5. **Output**: `platform/scripts/audit/F3_audit_ui.md`.

**Risk:** LOW. **Required prerequisites:** Phase E.4 + Auth Proxy. **Estimated effort:** 1 hour.

### Brief F.4 — Panel UI Smoke

**Mission:** the panel checkbox flow works end-to-end with PANEL_MODE_ENABLED=true.

**Streams:**
1. Set MARSYS_FLAG_PANEL_MODE_ENABLED=true.
2. Restart dev.
3. Verify the per-query checkbox appears.
4. Tick + submit; verify panel mode runs.
5. Verify divergence report renders + member outputs are anonymized in audit row.
6. **Output**: `platform/scripts/audit/F4_panel_smoke.md`.

**Risk:** MEDIUM (4× LLM cost; ~$5-10 per query). **Required prerequisites:** Phase E.4 with all 4 family API keys (this is where OpenAI key gap will hit hard if not resolved in A.1). **Estimated effort:** 1 hour.

---

## PHASE G — End-to-End Verification

### Brief G.1 — 8-Class Smoke

**Mission:** one representative query for each of the 8 query classes, executed end-to-end against live LLMs and live DB, verified to produce a coherent grounded answer.

**Streams:**
1. Construct one canonical query per class (already exist for some via `synthesis_golden_v1_0.json`).
2. Run each through the live system.
3. Capture the audit row, the response, the citations, the bundle.
4. Native subjective acceptance: does each answer feel acharya-grade?
5. **Output**: `platform/scripts/audit/G1_8class_smoke.md` with pass/fail per class + native commentary.

**Risk:** MEDIUM (8 real LLM queries; cost ~$5-15). **Required prerequisites:** Phases A–F complete. **Estimated effort:** 2 hours including native review.

### Brief G.2 — Citation Closed-Loop

**Mission:** every citation marker in a response actually resolves to real content via the preview endpoint.

**Streams:**
1. Take a recent response with citations.
2. For each marker, hit `GET /api/citations/preview` and verify it returns the cited content.
3. UI-side: click each chip in the browser; verify the side panel renders.
4. **Output**: `platform/scripts/audit/G2_citations.md`.

**Risk:** LOW. **Required prerequisites:** G.1 has populated audit_log. **Estimated effort:** 1 hour.

### Brief G.3 — Outcome Recording End-to-End

**Mission:** the prediction-outcome form (Phase 8) actually writes to prediction_ledger and respects the sacrosanct rule.

**Streams:**
1. Generate a time-indexed prediction (Phase 6's 8.5 should produce one if `CHECKPOINT_8_5_PREDICTION_EXTRACT=true`).
2. Verify it lands in `prediction_ledger`.
3. Try to record an outcome before `horizon_start`; verify rejection.
4. Try after `horizon_start`; verify acceptance.
5. **Output**: `platform/scripts/audit/G3_outcomes.md`.

**Risk:** LOW. **Required prerequisites:** Phase E.6. **Estimated effort:** 45 minutes.

---

## PHASE H — Manifest + Governance

### Brief H.1 — CAPABILITY_MANIFEST.json Full Re-Validation

**Mission:** after all the prior fixes, re-validate the manifest as the canonical source of truth.

**Streams:**
1. Re-run the manifest builder.
2. Diff old vs new fingerprint; document any expected changes.
3. Run `drift_detector.py`, `schema_validator.py`, `mirror_enforcer.py`.
4. **Output**: `platform/scripts/audit/H1_manifest_revalidate.md`.

**Risk:** LOW. **Required prerequisites:** Phases A–G. **Estimated effort:** 30 minutes.

### Brief H.2 — Mirror Discipline Cross-Check

**Mission:** Gemini-side artifacts (.geminirules, .gemini/project_state.md) are in adapted-parity with Claude-side per the MP.1/MP.2 mirror pairs.

**Streams:**
1. Read .geminirules and .gemini/project_state.md.
2. Compare against current Claude-side artifacts.
3. Apply same-session adapted-parity updates per CLAUDE.md §K.
4. **Output**: `platform/scripts/audit/H2_mirror_check.md`.

**Risk:** LOW. **Required prerequisites:** all prior phases. **Estimated effort:** 30 minutes.

---

## PHASE I — Documentation + Closeout

### Brief I.1 — Update CLAUDE.md and Architecture Docs

**Mission:** capture the lessons-learned in the architecture documents so the next person (or next session) doesn't repeat the same gaps.

**Streams:**
1. Add a new principle to PROJECT_ARCHITECTURE §B: "Every mocked-LLM test must be paired with a live-LLM smoke before claiming a feature is shipped."
2. Add a new principle: "Every SQL query in the codebase must be cross-checked against `information_schema.columns` as part of CI."
3. Add a new principle: "Every external service credential the code reads must be verified at session-open time."
4. Update CLAUDE.md §F state pointer to reflect post-audit state.
5. **Output**: edits to CLAUDE.md, PROJECT_ARCHITECTURE_v2_2.md, CURRENT_STATE_v1_0.md.

**Risk:** LOW. **Required prerequisites:** all prior phases. **Estimated effort:** 1 hour.

### Brief I.2 — Audit Closeout Report

**Mission:** one master document summarizing every brief above + every fix shipped + every gap remaining.

**Streams:**
1. Write `platform/scripts/audit/AUDIT_CLOSEOUT_v1_0.md` with sections per phase.
2. Aggregate all green ✅ items, all red ✗ items still open, all deferred items.
3. Produce a "next 30 days" backlog of any remaining work.
4. **Output**: the closeout report.

**Risk:** LOW. **Required prerequisites:** all prior phases. **Estimated effort:** 1 hour.

---

## Estimated total effort

Rough sum across phases: **~25–35 hours of Claude Code execution time** (across multiple sessions), plus your own native-review time on G.1.

Many briefs can run in parallel (A.1 + A.2 simultaneously; B.1–B.6 can run as a fan-out; C.1–C.5 can run as a fan-out after Brief D.1 is done; etc.). With 2-3 parallel Claude Code sessions, this could compress to **3–5 calendar days** of work.

## Suggested execution sequence (linear)

1. **Day 1, morning**: Brief A.1 (credentials — biggest gap) → Brief A.2 (GCP) → Brief A.3 (env) → Brief A.4 (dev hygiene). Phase A complete.
2. **Day 1, afternoon**: Brief B.1 (FORENSIC) parallel with B.2 (MSR). Brief B.5 (manifest) sequential.
3. **Day 2, morning**: Briefs B.3 + B.4 + B.6 parallel.
4. **Day 2, afternoon**: Brief D.1 + D.2 + D.3 (the high-value SQL audit). Brief D.2 will likely surface multiple silent bugs to fix.
5. **Day 3, morning**: Brief C.1 + C.2 + C.3. Re-embed via C.4 if needed.
6. **Day 3, afternoon**: Brief E.3 (the high-value tools audit). This is where the most surprises will surface.
7. **Day 4, morning**: Briefs E.1 + E.4 + E.5 + E.6 + E.7.
8. **Day 4, afternoon**: Phase F (UI).
9. **Day 5, morning**: Phase G (end-to-end verification, including the 8-class smoke).
10. **Day 5, afternoon**: Phase H + Phase I (governance + closeout).

## How to trigger this plan

Each brief above will become its own `EXEC_BRIEF_AUDIT_<phase>_<n>_v1_0.md` file. Cowork authors them on demand; you trigger one at a time in Claude Code with the standard pattern:

> Read EXEC_BRIEF_AUDIT_A1_v1_0.md and execute it.

You decide the cadence. Some briefs (A.1, D.2, E.3) are high-value — those should go early. Some (F.4 panel smoke, E.6 checkpoints) are deeper observability tests that can wait until other phases are stable.

## What the user should do right now

Three actions before triggering any brief:

1. **Set the OpenAI API key.** Add `OPENAI_API_KEY=...` to `.env.local`. Without it, Phase 7 panel mode fails immediately, and several Phase E briefs would fail in their LLM smokes.
2. **Verify Cloud SQL Auth Proxy is running.** It needs to be up for almost every brief from Phase B onward.
3. **Tell me which brief to author first.** I'll write the actual EXEC_BRIEF for it. Recommend starting with A.1.

## Honest acknowledgment

I should have flagged the OpenAI key gap when authoring Phase 7 originally (which named `gpt-4-1` as a default panel slate member) and reinforced it in Phase 12's Stream E (which lists "Anthropic + OpenAI + Google API keys" as a smoke prerequisite). I treated the API keys as "a thing the user has" rather than "a thing the user might not have, and we should ask." That's a discipline gap on my side. Brief A.1 is built to catch exactly this class of issue, going forward.

---

*End of MACRO_PLAN_SYSTEM_AUDIT_v1_0.md. Author the first brief on demand; chain through phases at the cadence you choose.*
