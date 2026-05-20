---
artifact: PSHIP_PR_BODY_H.md
type: PR_BODY_DRAFT
version: 1.0
status: CURRENT
authored_by: Claude Code (PSHIP-S5H)
authored_on: 2026-05-20
session_id: PSHIP-S5H
target_pr: feature/panchang-ship → main
---

# PR Body — Phase 4C Panchang Module (Hybrid Architecture)

---

## Title

`feat: Phase 4C Panchang module — Option H hybrid (SQL planner tool + live sidecar UI)`

---

## Body

### Summary

Ships the full Vedic Panchang capability for MARSYS-JIS via a **hybrid architecture** (Option H):

- **Planner path** — keeps and extends main's existing SQL-backed `query_panchanga` retrieval tool, extended with 5 new JSONB enrichment columns (migration 069): `special_yogas`, `inauspicious`, `auspicious`, `choghadiya`, `hora`.
- **UI path** — net-new `/panchang` page backed by the live Python sidecar engine (no SQL for the UI); supports personalisation via chart_id + Tara Bala / Chandra Bala overlay.
- **Planner prompt** — R-PA rule extended with 13 trigger categories (inauspicious windows, named special yogas, direct panchang requests); R-PCI rule added for `<panchang_context>` injection from the /panchang page.

Both paths call the **same `panchang_engine` library** (deterministic Swiss Ephemeris, Lahiri ayanamsha, Bhubaneswar observer) — parity is architectural, not sampled.

---

### What changed

#### Kept from main (unchanged)
- `src/lib/retrieve/query_panchanga.ts` — SQL tool, **extended** with 5 enrichment field groups
- `src/lib/retrieve/index.ts` — RETRIEVAL_TOOLS registry; `query_panchanga` is the **only** panchang entry
- `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` — R-TC rule, few-shot examples — **base kept, extended**

#### Extended from main
- `query_panchanga.ts` — adds `special_yogas`, `inauspicious`, `auspicious`, `choghadiya`, `hora` JSONB columns; graceful null handling until bootstrap runs
- `PLANNER_PROMPT_v2_0.md` — R-PA rule: +7 sub-triggers (f/g) for inauspicious windows, named special yogas, direct requests; R-PCI rule added; examples 4.29–4.31 added

#### Net-new (from feature/phase-4c-panchang)
- **`/panchang` UI page** — full-screen Vedic calendar view; 5 angas, timings, special yoga badges, choghadiya, hora; personalise dropdown (Tara Bala / Chandra Bala overlay)
- **Muhurat Finder** — modal + API; 6 MVP event types; star-rated windows with breakdown; Ask-Madhav deep link
- **iCal export** — `.ics` file download + signed feed URL (`/api/panchang/feed.ics`)
- **Ask-Madhav context injection** — AskMadhavLink component injects `<panchang_context>` block; R-PCI rule in planner skips tool call and uses injected data
- **`panchang_engine` library** — 230-test Python library: compute_panchang, special_yogas detection, muhurat scoring, timings (inauspicious/auspicious/choghadiya/hora), serialization, validation, Lahiri Swiss Ephemeris
- **Python sidecar** — `routers/panchang.py` + `routers/muhurat.py` — FastAPI routers; API key enforcement (`PYTHON_SIDECAR_API_KEY`)
- **`bootstrap_panchanga.py`** — extended with `--rebuild` flag to backfill migration 069 enrichment columns (~60 min for 73K rows)
- **Migration 069** — `069_extend_panchanga_daily.sql` — 5 JSONB columns + 2 GIN indexes

---

### Architecture narrative (Option H)

The Wave 1 feature branch (`feature/phase-4c-panchang`) built the panchang tool engine-direct
(sidecar only). Main had already shipped a SQL-precomputed `query_panchanga` retrieval tool
optimised for the LLM planner's token budget and latency requirements.

PRECON-S1 analysis identified a true collision at `query_panchanga.ts`, with Option H as the
resolution: **keep main's SQL tool, extend it with the enrichment columns, and use the live
sidecar exclusively for the `/panchang` UI page**. The two paths are complementary, not competing.

| Path | When used | Compute | Latency | Token budget |
|---|---|---|---|---|
| Planner (SQL) | Chat queries via R-PA | Precomputed, bootstrapped | ~5ms | Token-optimal |
| UI (sidecar) | /panchang page + Muhurat Finder | Live engine, on-demand | ~200ms | Full rich output |

---

### Test coverage

| Layer | Tests | Result |
|---|---|---|
| `panchang_engine` Python | 230 | 230/230 PASS |
| `query_panchanga.ts` (SQL tool) | 14 | 14/14 PASS |
| Panchang UI components | 50+ | PASS |
| Muhurat Finder modal | 24 | 24/24 PASS |
| Choghadiya / Hora panels | 10+ | PASS |
| AskMadhavLink | 5+ | PASS |
| Planner probe set (R-PA + R-PCI) | 36 | 36/36 PASS |
| Full suite regressions | 315 suites | 303 PASS / 12 FAIL (all pre-existing on main) |

---

### Deploy steps (S6H — HUMAN)

**In order:**

1. Merge this PR to main
2. Deploy to Cloud Run (standard deploy workflow)
3. Apply migration 069:
   ```bash
   psql $PROD_DB_URL -f platform/supabase/migrations/069_extend_panchanga_daily.sql
   ```
4. Run bootstrap backfill (~60 min):
   ```bash
   DATABASE_URL=$PROD_DB_URL python -m pipeline.bootstrap_panchanga --rebuild
   ```
5. Set `PYTHON_SIDECAR_API_KEY` in Cloud Run env (same value as `SIDECAR_KEY` in existing config)
6. Smoke test `/panchang` page with key enforced
7. Smoke test planner query: "What is the rahu kalam today?" → should return enrichment data

**Until step 4 completes:** The planner SQL tool returns null for enrichment fields but
continues to serve the 5 core angas (graceful degradation confirmed). The UI/sidecar path
is unaffected and returns live engine data throughout.

---

### Ship-readiness

See `00_ARCHITECTURE/PSHIP_SHIP_READINESS_H_v1_0.md` for full GO/NO-GO report.

**Verdict: GO** — both paths verified, all 6 architecture decisions landed, quality gate clean.

---

### Related

- `PANCHANG_RECONCILIATION_SPEC_v1_0.md` — full analysis + Option H selection rationale
- `PSHIP_S3H_PARITY.md` — SQL-tool-vs-engine parity proof (architectural guarantee)
- `PSHIP_S5H_SMOKE.md` — smoke report for this verification session
- `PHASE_4C_PANCHANG_BRIEF_v1_0.md` — full workstream brief
