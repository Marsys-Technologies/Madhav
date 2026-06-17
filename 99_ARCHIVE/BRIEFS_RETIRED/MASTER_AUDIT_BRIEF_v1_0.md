---
brief_id: MASTER_AUDIT_BRIEF
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read MASTER_AUDIT_BRIEF_v1_0.md and execute it."
risk_classification: VARIES_BY_PHASE
parallelizable_with: []
output_artifact: platform/scripts/audit/MASTER_AUDIT_REPORT.md (rolling)
---

# MASTER AUDIT BRIEF — Complete System Audit + Repair

## How this brief works

This is a **rolling orchestrator brief**. Each time you trigger it, Sonnet:

1. Reads `platform/scripts/audit/.audit_state.json` (creates it if missing).
2. Determines the next "ready" phase based on dependencies + completion state.
3. Executes that phase's streams end-to-end (every stream is fully specified inline below).
4. Updates `.audit_state.json` with results.
5. **HALTS at any pause-point** — either because (a) the phase produced a finding that needs native judgment, or (b) the next phase requires a credential or decision native must provide.
6. Writes findings to `platform/scripts/audit/MASTER_AUDIT_REPORT.md` (appended each invocation).
7. Reports back with: phase just executed, findings, what's next, what native must do (if anything).

**Native re-invokes the same trigger phrase repeatedly** until `MASTER_AUDIT_REPORT.md` says all phases COMPLETE.

This pattern preserves Cowork's authoring discipline (one phase, one risk classification, one set of acceptance criteria) while letting native run the entire audit through a single command. The pause-points exist because some decisions (e.g., "should we enrich FORENSIC?", "which broken tool do we fix first?") are native-only judgment calls.

## Pre-flight gate (every invocation)

Before doing anything, verify:

1. `cd /Users/Dev/Vibe-Coding/Apps/Madhav` is the working directory.
2. **Cloud SQL Auth Proxy is running** for any phase from B onward:
   ```bash
   pgrep -fl 'cloud[_-]sql[_-]proxy' || echo "PROXY DOWN — required for Phase B+"
   ```
   If down and the next ready phase needs DB access, halt with: "Start the Auth Proxy first."
3. The session has these env vars set (some phases need them):
   - `SMOKE_SESSION_COOKIE`, `SMOKE_CHART_ID` (required for Phase G end-to-end)
   - `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY` or `GEMINI_API_KEY`, `DEEPSEEK_API_KEY` (required for Phase A.1 to verify, Phase E for live LLM smokes)
   - `GOOGLE_APPLICATION_CREDENTIALS` for Vertex AI ADC

If any required prerequisite is missing for the next ready phase, halt with a specific actionable message.

## State file schema

`platform/scripts/audit/.audit_state.json`:

```json
{
  "version": 1,
  "started_at": "ISO timestamp",
  "last_updated": "ISO timestamp",
  "phases": {
    "A.1": { "status": "AUTHORED|IN_PROGRESS|COMPLETE|BLOCKED|FAILED", "started_at": "...", "completed_at": "...", "findings_summary": "...", "report_path": "..." },
    "A.2": { ... },
    ...etc for all phases below...
  },
  "next_ready": "A.1",
  "halted_for_native_decision": false,
  "native_decision_pending": "..." 
}
```

If state file doesn't exist, create it with all phases at `AUTHORED` and `next_ready: A.1`.

## Phase ordering (dependency graph)

```
Phase A (foundation, parallelizable):
  A.1 credentials → MUST PAUSE FOR NATIVE if missing keys discovered
  A.2 GCP services
  A.3 env vars
  A.4 dev hygiene
  ↓ [pause: native fixes any credentials]
Phase B (data layer, parallelizable):
  B.1 FORENSIC catalog
  B.2 MSR signals
  B.3 CGM graph
  B.4 UCN/CDLM/RM
  B.5 manifest cross-check
  B.6 GCS drift
  ↓ [pause: native decides on FORENSIC v8.1 if gaps found]
Phase C (embeddings) + Phase D (schema) parallel:
  C.1 rag_chunks
  C.2 rag_embeddings
  C.3 graph schema
  C.5 HNSW tuning
  D.1 migration state
  D.3 FK integrity
  ↓
Phase D.2 + Phase C.4 (HIGH VALUE — sequential):
  D.2 SQL-vs-schema cross-reference (this is where Phase 13-style bugs surface)
  C.4 re-embed any stale rows
  ↓ [pause: native reviews D.2 findings + decides surgical fix vs follow-up brief]
Phase E (pipeline code, parallelizable):
  E.1 router accuracy
  E.2 bundle composer content
  E.3 every retrieval tool tested (HIGH VALUE)
  E.4 synthesis strategies
  E.5 validators
  E.6 checkpoints
  E.7 disclosure tier
  ↓
Phase F (UI):
  F.1 component tree
  F.2 disclosure badge visibility (apply fix)
  F.3 audit view smoke
  F.4 panel UI smoke
  ↓ [pause: native does visual review]
Phase G (end-to-end):
  G.1 8-class smoke
  G.2 citation closed-loop
  G.3 outcome recording
  ↓ [pause: native subjective acharya-grade review]
Phase H (governance):
  H.1 manifest re-validate
  H.2 mirror discipline
  ↓
Phase I (closeout):
  I.1 architecture doc updates
  I.2 closeout report
```

Each phase below is fully specified — Sonnet executes from these specs, no need to consult the macro plan.

---

## PHASE A — Foundation Audit

### A.1 — Credentials & API Keys Audit

**Streams:**
1. Test ANTHROPIC_API_KEY: 1-token call to claude-haiku-4-5. Pass/fail.
2. Test OPENAI_API_KEY: 1-token call to gpt-4-1 (or gpt-4o if 4-1 unavailable). Pass/fail. **If missing or invalid, this is the known gap — flag explicitly to native and HALT.**
3. Test GOOGLE_API_KEY / GEMINI_API_KEY: 1-token call to gemini-1.5-pro. Pass/fail.
4. Test DEEPSEEK_API_KEY: 1-token call to deepseek-chat. Pass/fail.
5. Test Vertex AI ADC: embedding call against `text-multilingual-embedding-002`; verify 768-dim vector returned.
6. Verify Cloud SQL credentials: query `SELECT 1` via Auth Proxy; verify DB_USER/DB_NAME/DB_PASSWORD work.
7. Verify Firebase Admin: import the SDK, attempt token verification with a known good session.
8. Verify GCS service account: list both buckets (`madhav-astrology-chat-attachments`, `madhav-astrology-chart-documents`).

**Output:** `platform/scripts/audit/A1_credentials.md` with green/red per credential.

**Pause condition:** If any credential is missing or invalid, halt with: "Credential <X> is missing/invalid. Add it to `.env.local` (or Cloud Run env), then re-trigger this brief." Do NOT proceed to Phase B.

**Risk:** LOW. **Effort:** 30 min.

### A.2 — GCP Services Audit

**Streams:**
1. `gcloud run services describe amjis-web --region asia-south1` — health, deployed revision.
2. `gcloud run services describe amjis-sidecar --region asia-south1` — same.
3. `gcloud sql instances describe amjis-postgres` — state, tier, connection name.
4. `gsutil ls gs://madhav-astrology-chat-attachments` (head -5) + same for chart-documents bucket.
5. `gcloud secrets list` — verify amjis-db-password + amjis-voyage-api-key (note: voyage may be deprecated; flag if so).
6. `gcloud builds list --limit=5` — recent build status.
7. `gcloud artifacts repositories list` — Docker images present.
8. `nslookup madhav.marsys.in` — resolves to `34.54.231.91`.

**Output:** `platform/scripts/audit/A2_gcp_services.md`. **Risk:** LOW. **Effort:** 30 min.

### A.3 — Environment Variables Audit

**Streams:**
1. `grep -rh "process\.env\." platform/src/ | grep -oE 'process\.env\.[A-Z_]+' | sort -u` — list every env var the code reads.
2. For each, check presence in: `.env.example`, `.env.local`, Cloud Run env (via `gcloud run services describe`).
3. Build matrix: env var × (.env.example, .env.local, prod) × present/absent.
4. Flag: any env var read by code but absent everywhere (runtime failure waiting), any present in dev but absent in prod (deploy gap), any deprecated (e.g., SUPABASE_*, VOYAGE_API_KEY).

**Output:** `platform/scripts/audit/A3_env_matrix.md`. **Risk:** LOW. **Effort:** 45 min.

### A.4 — Dev Hygiene + Build Cache State

**Streams:**
1. `pgrep -fl 'next-server\|next dev'` — list running dev processes; flag any > 1 day old.
2. Check `platform/.next/BUILD_ID` mtime vs latest commit mtime.
3. Add `npm run dev:clean` script: kills + clears `.next` + restarts.
4. Document the dev-server-staleness anti-pattern in `platform/scripts/audit/A4_dev_hygiene.md`.

**Output:** `A4_dev_hygiene.md` + `package.json` script addition. **Risk:** LOW. **Effort:** 20 min.

---

## PHASE B — Data Layer Audit

### B.1 — FORENSIC v8.0 Completeness

**Streams:**
1. Read `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md`.
2. Build catalog: every planet (sun/moon/mars/mercury/jupiter/venus/saturn/rahu/ketu) × {sign, degree, house, nakshatra, pada}; every house cusp 1-12 × {sign, degree, nakshatra, pada}; ayanamsha + other constants.
3. For each fact: present in FORENSIC? If yes, value. If no, mark missing.
4. Cross-reference against the recent failing D1 query's `[EXTERNAL_COMPUTATION_REQUIRED]` markers.

**Output:** `platform/scripts/audit/B1_forensic.md` + `B1_forensic_catalog.json`.

**Pause condition:** if FORENSIC has substantive gaps, halt with: "FORENSIC v8.0 is missing N facts. Decide: (a) enrich to v8.1 with the missing values from chart record, or (b) accept these as legitimate `[EXTERNAL_COMPUTATION_REQUIRED]` per B.10. Native decision required."

**Risk:** LOW. **Effort:** 1.5 hr.

### B.2 — MSR Signals

**Streams:**
1. `SELECT count(*) FROM msr_signals` → assert 499.
2. Schema check: every required field present.
3. Cross-check against `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md`.
4. Find rows with missing derivation_ledger or significance_score.

**Output:** `B2_msr.md`. **Risk:** LOW. **Effort:** 1 hr.

### B.3 — CGM Graph

**Streams:**
1. Counts: rag_graph_nodes (~1752), rag_graph_edges (~3911), reconciled SUPPORTS/CONTRADICTS (~22).
2. Schema check.
3. Test cgm_graph_walk against live DB with known seed.
4. Cross-check counts vs CGM_v9_0.md.

**Output:** `B3_cgm.md`. **Risk:** LOW. **Effort:** 45 min.

### B.4 — UCN, CDLM, RM

**Streams:**
1. For each of UCN_v4_0.md, CDLM_v1_1.md, RM_v2_0.md: read source.
2. Determine: is it embedded into rag_chunks, or loaded from filesystem?
3. Verify consistency between source and embedded form (or filesystem path resolves).

**Output:** `B4_holistic.md`. **Risk:** LOW. **Effort:** 1 hr.

### B.5 — Manifest Cross-Check

**Streams:**
1. Parse `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`.
2. For each entry: file exists? sha256 matches stored hash? frontmatter version matches manifest version?
3. Categorize discrepancies: file-missing / hash-drift / version-drift.

**Output:** `B5_manifest.md`. **Risk:** LOW. **Effort:** 1 hr.

### B.6 — GCS Drift

**Streams:**
1. List GCS buckets contents.
2. For each L1/L2/L2.5 artifact: expected in GCS? Present? Content matches local file?
3. Flag local-only artifacts as deployment risk.

**Output:** `B6_gcs.md`. **Risk:** LOW. **Effort:** 1 hr.

---

## PHASE C — Embedding + Index Audit

### C.1 — rag_chunks

**Streams:**
1. `SELECT count(*), doc_type FROM rag_chunks GROUP BY doc_type`.
2. Find chunks with `embedding IS NULL`.
3. Find content < 50 or > 4000 chars.
4. Sample 10 chunks per doc_type; verify content shape.

**Output:** `C1_chunks.md`. **Risk:** LOW. **Effort:** 1 hr.

### C.2 — rag_embeddings

**Streams:**
1. Count rag_embeddings rows; cross-check with rag_chunks (memory says 977 vs 993 — investigate the gap).
2. Verify dim = 768 for every row.
3. **Critical**: read `vector_search.ts` after Phase 13 fix; for every column it references, verify it exists. Then read every other file that queries rag_embeddings and do the same.
4. HNSW p95 latency check.
5. Run a known-good vector_search query.

**Output:** `C2_embeddings.md`. **Risk:** LOW. **Effort:** 1 hr.

### C.3 — Graph Schema

**Streams:**
1. Read every file under `platform/src/lib/retrieve/` that queries graph tables.
2. For every column reference, check `information_schema.columns`.
3. Run cgm_graph_walk against live DB.

**Output:** `C3_graph.md`. **Risk:** LOW. **Effort:** 45 min.

### C.4 — Re-embed Stale/Missing Rows (CONDITIONAL)

**Run only if** C.1 or C.2 found missing/stale embeddings.

**Streams:**
1. List rows needing re-embed.
2. Invoke python sidecar's embedding pipeline.
3. Verify embeddings landed.

**Output:** `C4_reembed.md`. **Risk:** MEDIUM (writes to rag_embeddings). **Effort:** depends on row count.

### C.5 — HNSW Tuning Check

**Streams:**
1. Inspect HNSW params (m, ef_construction, ef_search).
2. Latency benchmarks at top_K=10 and top_K=20.
3. If p95 > 200ms at top_K=20, propose tuning.

**Output:** `C5_hnsw.md`. **Risk:** LOW. **Effort:** 30 min.

---

## PHASE D — Schema + Migration Audit

### D.1 — Migration Application State

**Streams:**
1. List migrations on disk (008-012 expected; check for newer).
2. Query Supabase migration tracking table for applied state.
3. Reconcile per migration: on-disk + applied-dev + applied-prod.

**Output:** `D1_migrations.md`. **Risk:** LOW. **Effort:** 30 min.

### D.2 — SQL-vs-Schema Cross-Reference (HIGH VALUE)

**Streams:**
1. Grep `platform/src/` for SQL strings (SELECT/INSERT/UPDATE/DELETE patterns + tagged template literals).
2. For each: parse table + column references.
3. Cross-check against `information_schema.columns` for the live DB.
4. Flag every column reference that doesn't exist in the named table — these are silent runtime errors (the Phase 13 `native_id` bug class).
5. **For each unambiguous fix (≤10 lines, narrow scope, file in non-frozen list)**, apply surgical fix and document. For larger or ambiguous bugs, document for follow-up.

**Output:** `D2_sql_xref.md` + any surgical fix diffs.

**Pause condition:** if findings include ambiguous bugs requiring native judgment, halt with: "D.2 found N broken queries. Native review required for: [list]. Fix surgically or author follow-up brief?"

**Risk:** LOW (read-only) plus MEDIUM (any surgical fixes applied). **Effort:** 2 hr.

This brief is the highest-value brief in the audit. Likely surfaces ≥3 silent bugs.

### D.3 — FK Integrity

**Streams:**
1. `SELECT * FROM information_schema.table_constraints WHERE constraint_type = 'FOREIGN KEY'`.
2. Spot-check expected FKs: chart→profiles, conversation→chart, etc.
3. Find orphans.

**Output:** `D3_fk.md`. **Risk:** LOW. **Effort:** 30 min.

---

## PHASE E — Pipeline Code Audit

### E.1 — Router Accuracy

**Streams:**
1. Read `platform/src/lib/router/**`.
2. For each of 8 query classes, construct 3 representative queries.
3. Run `pipeline:accuracy-test` against real Claude Haiku.
4. Report per-class accuracy. Flag classes < 80%.

**Output:** `E1_router.md`. **Risk:** LOW. **Effort:** 30 min.

### E.2 — Bundle Composer Content

**Streams:**
1. For each query class, trigger a query (via /api/chat/consume) and capture the bundle.
2. Inspect: references + content, content size, floor-role assets actually loading.
3. Flag references-only bundles.

**Output:** `E2_bundle.md`. **Risk:** LOW. **Effort:** 1 hr.

### E.3 — Every Retrieval Tool (HIGH VALUE)

**Streams:**
1. Enumerate tools from `platform/src/lib/retrieve/index.ts` `RETRIEVAL_TOOLS` registry.
2. For each tool (vector_search, msr_sql, cgm_graph_walk, manifest_query + 6 others): write a smoke test calling it directly with realistic params.
3. Verify each returns sensible non-empty results.
4. For any tool returning empty or erroring: capture exact SQL/API call, diagnose (likely schema mismatch like Phase 13's native_id), apply surgical fix or document.

**Output:** `E3_tools.md` with per-tool ✅/✗ + any surgical fixes.

**Pause condition:** if multiple tools are broken, halt with: "E.3 found N broken tools. Native review for prioritization."

**Risk:** MEDIUM. **Effort:** 3 hr.

This is the second-highest-value brief.

### E.4 — Synthesis Strategies

**Streams:**
1. Real LLM smoke through single_model_strategy for each query class.
2. Real LLM smoke through panel_strategy with PANEL_MODE_ENABLED=true.
3. Verify family-exclusion + anonymization actually hold by inspecting captured panel prompts.
4. Verify checkpoints fire when their flags are on.

**Output:** `E4_synthesis.md`. **Risk:** MEDIUM ($2-5 LLM cost). **Effort:** 1.5 hr.

### E.5 — Validators

**Streams:**
1. Construct synthetic outputs violating P1/P2/P5; verify caught.
2. Construct compliant outputs; verify pass.

**Output:** `E5_validators.md`. **Risk:** LOW. **Effort:** 1 hr.

### E.6 — Checkpoints

**Streams:**
1. Enable each of 4.5/5.5/8.5 individually.
2. Run real query; verify checkpoint fires.
3. Verify 8.5's prediction extractor produces valid Prediction object when synthesis is time-indexed.

**Output:** `E6_checkpoints.md`. **Risk:** LOW. **Effort:** 1 hr.

### E.7 — Disclosure Tier

**Streams:**
1. For each tier (super_admin, acharya_reviewer, client, public_redacted): send sample synthesis output with methodology + redactable signals.
2. Verify filter behavior per tier.

**Output:** `E7_disclosure.md`. **Risk:** LOW. **Effort:** 30 min.

---

## PHASE F — UI Audit

### F.1 — Component Tree

**Streams:**
1. For each Phase 5/7/8 component: identify importing route; verify reachability.
2. For each route: auth gate correct?
3. Visual smoke: open each, capture screenshot via headless browser if available; otherwise document the manual smoke list.

**Output:** `F1_components.md`. **Risk:** LOW. **Effort:** 1.5 hr.

### F.2 — Disclosure Badge Visibility (apply fix)

**Streams:**
1. Modify `ConsumeChat.tsx` (or wherever the badge mounts): make `<DisclosureTierBadge />` render unconditionally in the sticky header.
2. Add small "running new pipeline" indicator visible on initial page load.
3. Test fresh-page, post-query, validator-halt states.

**Output:** `F2_disclosure_visibility.md` + ~10 lines of code change. **Risk:** LOW. **Effort:** 30 min.

### F.3 — Audit View Smoke

**Streams:**
1. Submit test queries to populate audit_log.
2. Navigate /audit, drill into row, verify 8 sections.
3. Try outcome form; verify sacrosanct rule.
4. Try compare view.

**Output:** `F3_audit_ui.md`. **Risk:** LOW. **Effort:** 1 hr.

### F.4 — Panel UI Smoke (CONDITIONAL)

**Run only if** OPENAI_API_KEY confirmed in A.1.

**Streams:**
1. Set MARSYS_FLAG_PANEL_MODE_ENABLED=true. Restart dev.
2. Verify per-query checkbox appears.
3. Tick + submit; verify panel mode runs against all 4 families.
4. Verify divergence report renders + member outputs anonymized.

**Output:** `F4_panel.md`. **Risk:** MEDIUM ($5-10 panel query cost). **Effort:** 1 hr.

---

## PHASE G — End-to-End Verification

### G.1 — 8-Class Smoke

**Streams:**
1. One canonical query per class (use `synthesis_golden_v1_0.json` where applicable).
2. Run each through live system via curl with SMOKE_SESSION_COOKIE.
3. Capture audit row + response + citations + bundle.
4. Tabulate per-class pass/fail with brief description.

**Output:** `G1_8class.md`.

**Pause condition:** native subjective acharya-grade review of the 8 responses. Halt with: "G.1 captured 8 responses. Native review for acharya-grade-ness required."

**Risk:** MEDIUM ($5-15 cost). **Effort:** 2 hr including pause.

### G.2 — Citation Closed-Loop

**Streams:**
1. Take a recent response with citations.
2. For each marker, hit `GET /api/citations/preview`, verify content returned.
3. Verify side-panel rendering in browser.

**Output:** `G2_citations.md`. **Risk:** LOW. **Effort:** 1 hr.

### G.3 — Outcome Recording

**Streams:**
1. Generate time-indexed prediction (with CHECKPOINT_8_5_PREDICTION_EXTRACT=true).
2. Verify lands in prediction_ledger.
3. Test sacrosanct rule: outcome submission before vs after horizon_start.

**Output:** `G3_outcomes.md`. **Risk:** LOW. **Effort:** 45 min.

---

## PHASE H — Manifest + Governance

### H.1 — Manifest Re-Validate

**Streams:**
1. Re-run manifest builder.
2. Diff old vs new fingerprint.
3. Run drift_detector.py + schema_validator.py + mirror_enforcer.py.

**Output:** `H1_manifest.md`. **Risk:** LOW. **Effort:** 30 min.

### H.2 — Mirror Discipline

**Streams:**
1. Read .geminirules + .gemini/project_state.md.
2. Compare to current Claude-side artifacts.
3. Apply same-session adapted-parity updates per CLAUDE.md §K.

**Output:** `H2_mirror.md`. **Risk:** LOW. **Effort:** 30 min.

---

## PHASE I — Documentation + Closeout

### I.1 — Architecture Doc Updates

**Streams:**
1. Add to PROJECT_ARCHITECTURE §B principles:
   - "Every mocked-LLM test must be paired with a live-LLM smoke before claiming a feature is shipped."
   - "Every SQL query in the codebase must be cross-checked against `information_schema.columns` as part of CI."
   - "Every external service credential the code reads must be verified at session-open."
2. Update CLAUDE.md §F state pointer.
3. Update CURRENT_STATE_v1_0.md.

**Output:** doc edits. **Risk:** LOW. **Effort:** 1 hr.

### I.2 — Closeout Report

**Streams:**
1. Write `platform/scripts/audit/AUDIT_CLOSEOUT_v1_0.md` aggregating every phase's findings.
2. Sections: green ✅ items, red ✗ items still open, deferred items.
3. "Next 30 days" backlog.

**Output:** the closeout report. **Risk:** LOW. **Effort:** 1 hr.

---

## Critical constraints (apply across all phases)

- **Keep new pipeline ON throughout.** Do NOT touch `NEW_QUERY_PIPELINE_ENABLED` or `AUDIT_ENABLED` defaults.
- **Surgical fixes only when unambiguous, ≤10 lines, in non-frozen scope.** Anything else → document for follow-up brief.
- **No re-embedding without explicit native trigger.** C.4 only runs if C.1/C.2 surface need; even then it's a separate decision.
- **Halt at every pause-point.** The state file's `halted_for_native_decision: true` flag tells the next invocation to ask native what to do.
- **Update state file atomically.** After each phase: write report, then update state. Order matters so a crashed mid-phase doesn't lie about completion.
- **Cite specific evidence in every finding.** File:line, audit_log column, captured JSON dump path.

## Done criteria (whole brief)

1. All phases A.1 → I.2 are `COMPLETE` in state file (or explicitly `BLOCKED` with documented reason).
2. `MASTER_AUDIT_REPORT.md` aggregates per-phase findings.
3. `AUDIT_CLOSEOUT_v1_0.md` exists with the green/red/deferred breakdown.
4. Native acceptance: native reviews G.1's 8-class smoke + AUDIT_CLOSEOUT and signs off.

## How native triggers

In a Claude Code session in Anti-Gravity:

> Read MASTER_AUDIT_BRIEF_v1_0.md and execute it.

Re-trigger the same phrase repeatedly. Each invocation runs the next ready phase, halts at any pause-point requiring decision, and updates the state file. After native makes whatever decision is requested, re-trigger to continue.

Total expected invocations: ~10–15 across the audit (some phases run multiple sub-streams in one invocation; others halt for native decision).

Total wall-clock time: 3–5 calendar days realistic, with 2–3 native review cycles between phases.

## Status updates

- AUTHORED 2026-04-28
- IN_PROGRESS_PHASE_X — set when Sonnet picks up a phase
- COMPLETE — set when all phases COMPLETE and AUDIT_CLOSEOUT exists
