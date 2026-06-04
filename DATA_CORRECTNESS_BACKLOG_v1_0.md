---
artifact: DATA_CORRECTNESS_BACKLOG_v1_0.md
canonical_id: DATA_CORRECTNESS_BACKLOG
version: 1.0
status: LIVING (updated on each Runtime-Guardian build)
authored_by: Runtime-Guardian Swarm (2026-06-04)
purpose: >
  Records defects that could not be made correct within MAX_FIX_ATTEMPTS=5 or
  where the engine itself is correct but a plumbing/schema issue prevents data landing.
  Per RUNTIME_GUARDIAN_MODE §D: "park the defect + log to DATA_CORRECTNESS_BACKLOG,
  and continue with everything still buildable."
---

# Data Correctness Backlog

## Active Parks

### DCB-001 · kala.timeline — psycopg version mismatch
- **Layer:** L3 Kāla
- **Asset:** kala.timeline (`brahmagyan/kala/timeline.py`)
- **Symptom:** `No module named 'psycopg.extras'`
- **Root cause:** `brahmagyan/kala/timeline.py` imports `psycopg.extras` (a psycopg2 extension) but the venv has psycopg v3 (`psycopg[binary]>=3.2`). The `.extras` sub-module doesn't exist in psycopg v3.
- **Unblocked by:** Replace `psycopg.extras` usage with psycopg v3 equivalent (or add `psycopg2-binary` as explicit dep for this module).
- **Data impact:** `kala_timeline` has 0 rows for the native chart. Seeding started (67 years × daily rows ≈ 24,000 rows) but was interrupted at the DB write.
- **Parked:** 2026-06-04 (rt-guardian-20260604)
- **Severity:** MEDIUM — L3 does not block L4/L5.

### DCB-002 · bodha.signals — function name mismatch
- **Layer:** L2 Bodha
- **Asset:** bodha.signals (`brahmagyan/bodha/bo24.py`)
- **Symptom:** `cannot import name 'seed_bodha_signals' from 'brahmagyan.bodha.bo24'`
- **Root cause:** The pipeline called `seed_bodha_signals` but bo24.py exports a different function name. Need to read bo24.py and use the actual public function.
- **Unblocked by:** `grep '^def ' brahmagyan/bodha/bo24.py` + fix pipeline.
- **Data impact:** bodha_signals table not populated from this pipeline call (may already have data from prior Brahma Batch sessions).
- **Parked:** 2026-06-04 (rt-guardian-20260604)
- **Severity:** LOW — bodha_graph (21 edges) ✓.

### DCB-003 · phala.mitigation — function name mismatch
- **Layer:** L4 Phala
- **Asset:** phala.mitigation (`brahmagyan/phala/mitigation.py`)
- **Symptom:** `cannot import name 'seed_mitigation' from 'brahmagyan.phala.mitigation'`
- **Root cause:** Pipeline called `seed_mitigation` but that name doesn't exist.
- **Unblocked by:** `grep '^def ' brahmagyan/phala/mitigation.py` + fix pipeline.
- **Data impact:** phala_mitigation table not populated. phala_anchors (9 rows) ✓.
- **Parked:** 2026-06-04 (rt-guardian-20260604)
- **Severity:** LOW.

### DCB-004 · mimamsa.lel_intake — life_events.category NOT NULL
- **Layer:** L5 Mīmāṃsā
- **Asset:** mimamsa.lel_intake (`brahmagyan/mimamsa/lel_intake.py`)
- **Symptom:** `null value in column "category" of relation "life_events" violates not-null constraint`
- **Root cause:** The `life_events` table has a NOT NULL constraint on `category` but the lel_intake builder doesn't populate it (either omits it or the column was added after the builder was written).
- **Unblocked by:** Read the life_events schema + lel_intake builder; add the `category` mapping.
- **Data impact:** life_events has 0 rows. 57 events in `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` not ingested.
- **Parked:** 2026-06-04 (rt-guardian-20260604)
- **Severity:** MEDIUM — LEL is isolated from generation per design; non-blocking for chart reads.

### DCB-005 · build_events table absent in proxy DB
- **Layer:** All (plumbing)
- **Symptom:** `relation "build_events" does not exist`
- **Root cause:** The `build_events` table was created via Supabase migrations (not the `platform/migrations/` folder). The local Cloud SQL Proxy DB uses a different migration path.
- **Unblocked by:** Apply the build_events migration to the Cloud SQL instance (find + run the missing migration).
- **Data impact:** Cockpit SSE rail cannot show live progress. Build_events rows not emitted. Data writes (positions, dashas, bodha_graph, phala_anchors) succeed regardless — non-fatal.
- **Parked:** 2026-06-04 (rt-guardian-20260604)
- **Severity:** MEDIUM — affects cockpit live display; data is correct.

## Resolved

*(none yet)*

---
*End of DATA_CORRECTNESS_BACKLOG v1.0 — 5 parks from Runtime-Guardian run 2026-06-04.*
