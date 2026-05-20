---
artifact: CLAUDECODE_BRIEF_PSHIP_S3H_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: READY
authored_by: Cowork 2026-05-20
session_id: PSHIP-S3H
session_name: PSHIP-S3H — Query-tool reconciliation + migration 061 (5-col cache) + bootstrap
executor: Claude Code sub-agent (Conductor)
worktree:
  branch: feature/panchang-ship
  path_absolute: /Users/Dev/Vibe-Coding/Apps/PanchangShip
predecessor: PSHIP-S2H
---

# CLAUDECODE_BRIEF — PSHIP-S3H
## Resolve the query_panchanga collision (D6) + extend the cache to 5 columns (D2/Option A)

Per D6: main's SQL `query_panchanga` stays the registered planner tool; our sidecar logic serves the UI directly and is NOT registered as a planner tool. Per D2 + Option A: migration 061 adds FIVE JSONB columns to `panchanga_daily` (special_yogas, inauspicious, auspicious, choghadiya, hora) + the bootstrap is updated to populate them, so the SQL tool can serve all 13 R-PA triggers.

---

## §0 — Pre-flight
```bash
cd /Users/Dev/Vibe-Coding/Apps/PanchangShip
git log --oneline -5   # PSHIP-S2H commits present
git show origin/main:platform/src/lib/retrieve/query_panchanga.ts >/dev/null && echo "main SQL tool present"
# confirm main's migration 060 + panchanga_daily exist
git ls-tree -r origin/main -- platform/supabase/migrations/ | grep -iE "060|panchang" | head
git show origin/main:platform/python-sidecar/pipeline/bootstrap_panchanga.py >/dev/null && echo "main bootstrap present"
```

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. `00_ARCHITECTURE/PANCHANG_RECONCILIATION_SPEC_v1_0.md` §1 (tool diff), §2 (compute paths), §5 (collisions), §9 D2+D6
3. main's `query_panchanga.ts` (the SQL tool you EXTEND) + its test
4. main's migration 060 (the panchanga_daily DDL — your migration 061 extends it)
5. main's `bootstrap_panchanga.py` + `panchanga_derivations.py` (you extend these to compute the 5 new columns)
6. our engine's `special_yogas.py` + `timings.py` (the source logic for the new columns: special_yogas, inauspicious=rahu/yama/gulika, auspicious=abhijit/brahma/amrit, choghadiya, hora)

## §3 — Scope (10 items)

### Item 1 — Resolve the query_panchanga.ts collision (D6)
Confirm main's `platform/src/lib/retrieve/query_panchanga.ts` is intact (S1 should NOT have overwritten it — it's M-classified). Our sidecar-direct logic must NOT be registered in `RETRIEVAL_TOOLS`. Decide + implement the cleanest of:
- (a) The `/api/panchang/*` Next.js routes call the sidecar directly (their own fetch) — then our `query_panchanga.ts` RetrievalTool file is redundant; remove it (keep its sidecar-calling logic only where the API routes need it).
- (b) Keep our sidecar logic in a clearly-named non-tool module (e.g., `platform/src/lib/panchang/sidecar_client.ts`) that the API routes import; ensure it is NOT in RETRIEVAL_TOOLS.
Either way: `RETRIEVAL_TOOLS` ends with ONLY main's `queryPanchanga` (the SQL tool). Confirm via introspection.

**AC.S3H.1:** RETRIEVAL_TOOLS has exactly one query_panchanga (main's SQL tool); our sidecar logic lives in a non-tool module the UI routes use; tsc clean.

### Item 2 — Author migration 061 (5 JSONB columns)
Create `platform/supabase/migrations/061_extend_panchanga_daily.sql`:
```sql
ALTER TABLE panchanga_daily
  ADD COLUMN special_yogas JSONB,   -- [{yoga, start, end, strength, stars}]
  ADD COLUMN inauspicious  JSONB,   -- {rahu_kalam, yamagandam, gulika_kalam, dur_muhurta[]}
  ADD COLUMN auspicious    JSONB,   -- {abhijit, brahma_muhurta, amrit_kalam, varjyam}
  ADD COLUMN choghadiya    JSONB,   -- {day:[...8], night:[...8]}
  ADD COLUMN hora          JSONB;   -- [...24 planetary hours]
CREATE INDEX IF NOT EXISTS idx_panchanga_daily_special_yogas
  ON panchanga_daily USING GIN(special_yogas);
```
Match main's migration numbering/format conventions exactly (check migration 060's header style).

**AC.S3H.2:** Migration 061 authored; matches project migration conventions; idempotent guards where appropriate.

### Item 3 — Extend the bootstrap to compute the 5 new columns
Update `bootstrap_panchanga.py` (+ `panchanga_derivations.py` if that's where compute lives) to compute special_yogas / inauspicious / auspicious / choghadiya / hora for each (date, location) row, reusing our engine's `special_yogas.py` + `timings.py` logic (import the engine, or port the computation). The bootstrap already computes sunrise/sunset, so choghadiya/hora derive from those.

**AC.S3H.3:** Bootstrap computes all 5 new columns for a sample row; values match the live engine's output for the same date/location (cross-check 3 sample days).

### Item 4 — Extend main's SQL query_panchanga.ts to surface the new columns
Add the 5 new fields to main's `query_panchanga.ts` return shape + field projection (`PanchangaField` type, ALL_FIELDS, the SELECT). So planner queries for special yogas / rahu kalam / choghadiya / hora get answered from the cache.

**AC.S3H.4:** SQL tool returns the 5 new field groups when requested; field projection works; tsc clean; main's tool tests updated + green.

### Item 5 — Bootstrap execution (or deferral)
Run the bootstrap to populate the 5 new columns for the existing 73K rows. This is a ~60min batch needing DB access (Cloud SQL Auth Proxy or equivalent). If the proxy/DB isn't available in this session's environment, DEFER the population (mark `BOOTSTRAP_061_DEFERRED` + document the exact command to run) — the migration + bootstrap CODE still land; the data population becomes a documented prod step in S6H. Do NOT fabricate cache data.

**AC.S3H.5:** Either 73K rows populated with the 5 columns, OR deferred-with-command documented for S6H.

### Item 6 — SQL-tool unit/integration tests for the new fields
Add tests asserting the SQL tool returns special_yogas / inauspicious / auspicious / choghadiya / hora correctly (mock the DB row with the new columns). Confirms the tool serves all 13 R-PA triggers' data once the cache is populated.

**AC.S3H.6:** New-field tests pass.

### Item 7 — Parity check: SQL tool vs live engine
For 3 sample days, confirm the SQL tool's output (post-061, for special yogas etc.) matches the live sidecar engine's output for the same date/location. They must agree (both derive from the same shastra logic). Document in `00_ARCHITECTURE/PSHIP_S3H_PARITY.md`.

**AC.S3H.7:** SQL-tool-vs-engine parity confirmed for 3 days (or any divergence flagged).

### Item 8 — Full test + tsc + validators
```bash
cd platform && npx tsc --noEmit && npm test 2>&1 | tail -30
cd /Users/Dev/Vibe-Coding/Apps/PanchangShip && python3 platform/scripts/governance/schema_validator.py && python3 platform/scripts/governance/drift_detector.py
```
Green/clean. (The 2 pre-existing validator failures: if PSHIP-S3 from the old round didn't run, they may still be present — note them as known/pre-existing, not S3H-introduced. Optionally fix here if quick.)

**AC.S3H.8:** tsc 0; tests green; validators clean or known-pre-existing documented.

### Item 9 — Auth-header check (carry-over from old PSHIP-S3)
Ensure the UI's sidecar-calling path (`/api/panchang/*` routes + the non-tool sidecar module from Item 1) sends `x-api-key: process.env.PYTHON_SIDECAR_API_KEY`. This was BUG 1 — must be fixed so /panchang works in prod (where the sidecar enforces the key).

**AC.S3H.9:** Every sidecar call from the UI path sends x-api-key; regression test added.

### Item 10 — Session close
CURRENT_STATE; SESSION_LOG; brief flip; FINAL_SUMMARY noting collision resolution, migration 061, bootstrap status (populated/deferred), parity result.

**AC.S3H.10:** Close protocol complete.

---

## §5 — Constraints
**may_touch:** main's `query_panchanga.ts` (extend) + its test; `retrieve/index.ts` (ensure only main's tool registered); our sidecar non-tool module + `/api/panchang/*` routes; `platform/supabase/migrations/061_*.sql` (new); `bootstrap_panchanga.py` + `panchanga_derivations.py`; `00_ARCHITECTURE/PSHIP_S3H_PARITY.md` (new); governance state; this brief.
**must_not_touch:** `PLANNER_PROMPT_v2_0.md` (S4H — the R-PA extension is NEXT session, not here); the engine internals (sealed — import, don't edit); main's migration 060; the nav/deploy/CLAUDE.md from S2H; Conductor; corpus.

## §6 — Close checklist
- [ ] 10 ACs PASS
- [ ] RETRIEVAL_TOOLS has exactly main's SQL query_panchanga (D6)
- [ ] Migration 061 (5 cols) + bootstrap extension; data populated OR deferred-with-command
- [ ] SQL tool surfaces all 5 new field groups
- [ ] SQL-tool-vs-engine parity for 3 days
- [ ] Auth header on UI sidecar path (BUG 1 fixed)
- [ ] tsc 0; tests green
- [ ] FINAL_SUMMARY emitted

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- D2 + Option A: 5 columns (NOT 3) — special_yogas, inauspicious, auspicious, choghadiya, hora. So the SQL tool serves all 13 R-PA triggers (chat/UI parity).
- D6: planner uses main's SQL tool; UI uses sidecar directly; our query_panchanga.ts is NOT a registered planner tool.
- The SQL tool and the live engine must agree (same shastra logic) — that's the parity check.
- Bootstrap of 73K rows may need Cloud SQL proxy; defer-with-command if unavailable (matches main's own DB-seed-deferred precedent).

## §9 — Canary
Item 7's SQL-tool-vs-engine parity. If the cache (post-bootstrap) and the live engine disagree on special yogas / rahu kalam for the same day, the bootstrap's port of the engine logic has a bug — halt and reconcile before the planner (S4H) starts routing to a tool that returns wrong data.

*End — PSHIP-S3H.*
