# Stream A Conductor Log
Wave: postdeploy-a
Branch: feature/postdeploy-a-l0-activation
Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavPostA
Executed: 2026-06-05
Tag: postdeploy-a-l0-activated @ (see git tag below)

## Status
COMPLETE (a1/a3 green; a2 AMBER/proxy-constrained; a4 INFRA_PENDING/pre-existing)

---

## Session Results

### a1 — Apply L0 migrations: PASS
- `ws2_l0_ephemeris.sql` applied successfully — `ephemeris_daily` table created with 4 indexes
- `ws2_l0_remedy_corpus.sql` applied successfully — `brahma_remedy_corpus` table created with 5 indexes
- Both tables verified in `pg_tables` (schema: public)
- Migration files committed on `feature/postdeploy-a-l0-activation` (already in HEAD)
- DB connection: Cloud SQL proxy (port 5433) with v3 password from Secret Manager

**Tier-2 note**: `.env.rag` and `.env.local` contained stale v1/v2 passwords. 
Current v3 password retrieved from `gcloud secrets versions access latest --secret=amjis-db-password`.

### a2 — Ephemeris build: AMBER (proxy-constrained)
- Cloud Run Job `brahmagyan-ephemeris-build` NOT FOUND in asia-south1 (infrastructure gap)
- Fallback: direct Python via `brahmagyan/l0_ephemeris.py::build_ephemeris()`
- Write path verified: 1-day sample for 1984-02-05 → Sun=315.874° (Aquarius tropical, CORRECT)
- Full build attempted twice; both failed mid-run due to Cloud SQL proxy connection resets:
  - Attempt 1 (batch_size=365): 6,579 rows committed (1980-01-01 → 1984-02-05)
  - Attempt 2 (batch_size=30): 7,659 rows committed (1980-01-01 → 1984-06-04)
- **Final state**: 7,659 rows (851 dates × 9 bodies), last_date = 1984-06-04
- Volume floor: 29,200 rows (29,221 dates × 9 bodies for 1980-2060) — NOT YET MET
- Status: AMBER — partial build, safe to resume (ON CONFLICT DO NOTHING)
- See smriti/A2_EPHEMERIS_STATUS.md + smriti/CLOUDRUN_JOB_GAP.md

### a3 — Remedy corpus seed: PASS
- Cloud Run Job `brahmagyan-remedy-seed` NOT FOUND in asia-south1 (infrastructure gap)
- Fallback: direct Python via `brahmagyan/l0_remedy_corpus.py::seed_remedy_corpus()`
- Result: 55 rows seeded (volume floor: 50) — GREEN
- Volume check: `saturn_career_check.count=4` (AC: >= 1) — PASS
- `source_citation_check.null_count=0` — PASS
- All 55 rows have source_canonical_id (BPHS/Phaladeepika/Tajaka)

### a4 — Verify rag_chunks: INFRA_PENDING
- `rag_chunks` table does NOT exist in production DB
- Root cause: `001_baseline.sql` explicitly lists rag_chunks as a "DROP table" 
  (legacy RAG pipeline, intentionally excluded from brahma baseline squash)
- MCP Transformation migrations (072-080) that would restore/populate rag_chunks are 
  in `platform/supabase/migrations/_archive/` and listed as UNCONFIRMED in OPERATOR_ACTIONS_PENDING.md
- This is a PRE-EXISTING condition, NOT a Stream A regression
- Stream A scope covers ws2_l0_ephemeris and ws2_l0_remedy_corpus only
- WS-2 L0 architecture uses `classical_text_chunks` as the rag_chunks replacement
- See smriti/A4_RAG_CHUNKS_STATUS.md

---

## Operator Actions Required

### CRITICAL (blocks a2 GREEN):
1. **Ephemeris full build**: Run `build_ephemeris(start=date(1984,6,5), end=date(2060,12,31))` 
   in a context with stable long-lived DB connection (Cloud Run Job or sidecar container).
   Current partial build covers 1980-01-01 → 1984-06-04 (7,659 rows); needs 263k total.

### HIGH (blocks a4 GREEN):
2. **rag_chunks restoration**: Either apply archived MCP Transformation migrations 072-080,
   OR update a4 AC to check `classical_text_chunks` count (WS-2 replacement table).
   The WS-2 L0 texts migration (`ws2_l0_texts.sql`) creates `classical_text_chunks` — 
   apply it and seed it via the WS-2 text pipeline.

### MEDIUM (infrastructure provisioning):
3. **Cloud Run Jobs**: Create `brahmagyan-ephemeris-build` and `brahmagyan-remedy-seed` 
   Cloud Run Jobs in asia-south1 per the CLAUDECODE_BRIEF_BRAHMA_INFRA_PROVISIONING brief.

---

## Smṛti entries
- `smriti/CLOUDRUN_JOB_GAP.md` — Tier-2: Cloud Run Jobs missing, fallback to direct Python
- `smriti/A2_EPHEMERIS_STATUS.md` — Tier-2: Full build blocked by proxy connection resets
- `smriti/A4_RAG_CHUNKS_STATUS.md` — Tier-2: rag_chunks absent from prod schema (pre-existing)
