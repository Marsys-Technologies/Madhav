---
canonical_id: F1_MUHURAT_OVERLOAD_BRIEF
version: 1.0.0
status: DRAFT
authored: 2026-05-21
---

# F.1 Muhurat Finder Overload — Root Cause + Design Brief

## FINDINGS

### root_cause

A 90-day Muhurat Finder request maps directly to 90 sequential `compute_panchang()` calls inside a single synchronous Python loop in `platform/python-sidecar/panchang_engine/muhurat.py` (`find_muhurat()`, lines 336–353). Each call invokes Swiss Ephemeris (`swisseph`) for 8 planet positions via `swe.calc_ut` (8 calls in `planets.py` `compute_all_grahas()`, lines 181–192) plus 4 `swe.rise_trans` calls for sunrise/sunset/moonrise/moonset (timings.py), plus a second `compute_sunrise_sunset` call for the next day's sunrise (needed for Choghadiya and Hora, `__init__.py` lines 86–91), totalling approximately 13–14 ephemeris C-extension calls per day. Across 90 days that is ~1,260 ephemeris calls made in a single synchronous request with no threading, no batch optimisation, and no result cache. The FastAPI endpoint at `routers/muhurat.py` line 113 is declared `async def` but the entire `find_muhurat()` inner loop is CPU-bound synchronous Python running in the event loop's thread — it cannot yield to other requests. The Cloud Run sidecar (`amjis-sidecar`) has no explicit `--concurrency`, `--memory`, `--cpu`, or `--timeout` flags in any deploy script (`cloudbuild-sidecar.yaml`, `EXEC_BRIEF_SIDECAR_IMAGE_REBUILD_v1_0.md`); the only documented Cloud Run deploy invocation for the sidecar uses `gcloud run deploy amjis-sidecar ... --image ... --region ... --project` with no resource flags, meaning it runs at Cloud Run defaults (1 vCPU, 512 MiB RAM, 60-second request timeout, concurrency=80). The 90-day wall-clock compute time approaches or exceeds the 60-second default timeout, causing a gateway error that the Next.js proxy at `platform/src/app/api/compute/muhurat/route.ts` line 43 maps to `res.sidecarDown()`, which the UI (`useMuhuratFinder.ts` line 77–88) surfaces as "Panchang Unavailable". Even when the timeout is not hit, the fully-blocking synchronous event loop means the single sidecar instance cannot serve any other request (panchanga queries, dasha chains, RAG) while a 90-day scan is in progress, amplifying the outage to all concurrent users.

### request_pattern

The client (`platform/src/app/panchang/hooks/useMuhuratFinder.ts`) fires a single POST to `/api/compute/muhurat` containing `date_from`, `date_to`, and the full parameter set. The Next.js proxy (`/api/compute/muhurat/route.ts`) forwards this as a single POST to the Python sidecar `/api/compute/muhurat`. The sidecar runs `find_muhurat()` which iterates one day at a time (`while current <= date_to: ... current += timedelta(days=1)`) — 90 iterations for a 90-day window — calling `compute_panchang()` synchronously for each day with no parallelism, no cache lookup, and no early exit. The retrieval tool (`platform/src/lib/retrieve/query_muhurat.ts`) uses the same single-POST pattern. There is no client-side batching, no pagination, and no progress reporting.

### sidecar_capacity

No explicit resource declarations exist in any committed deploy artefact for `amjis-sidecar`. The Dockerfile (`platform/python-sidecar/Dockerfile`) uses `uvicorn main:app --host 0.0.0.0 --port 8000` with no worker or concurrency flags. The sidecar therefore runs as a single-worker single-threaded uvicorn process. Cloud Run defaults apply:

| Setting | Value |
|---|---|
| CPU | 1 vCPU (default) |
| Memory | 512 MiB (default; confirmed from `EXEC_BRIEF_SIDECAR_IMAGE_REBUILD_v1_0.md` deploy command which has no `--memory` override) |
| Request timeout | 60 seconds (Cloud Run default) |
| Max concurrency per instance | 80 (Cloud Run default for HTTP/1.1) |
| Min instances | 0 (default — cold-start risk confirmed in `SIDECAR_500_INVESTIGATION_REPORT_v1_0.md`) |

Practical concurrency is effectively 1 for CPU-bound requests: a single 90-day scan blocks the uvicorn event loop for the full wall-clock duration (estimated 30–90 seconds depending on instance warmth), starving all other in-flight requests.

### per_day_cost

Each `compute_panchang(date, lat, lon, tz_offset)` call performs:

- `compute_sunrise_sunset` — 2× `swe.rise_trans` (SUN RISE + SUN SET)
- `compute_moonrise_moonset` — 2× `swe.rise_trans` (MOON RISE + MOON SET)
- Second `compute_sunrise_sunset` for next-day sunrise (Choghadiya/Hora) — 2× `swe.rise_trans`
- `compute_all_grahas` — 1× `swe.calc_ut` for Sun + 7× `swe.calc_ut` for Moon/Mars/Mercury/Jupiter/Venus/Saturn/Rahu = 8× `swe.calc_ut`
- 5× anga computations (tithi, nakshatra, yoga, karana×2, vara) — pure Python arithmetic, negligible
- `detect_all_special_yogas` — pure Python logic on already-computed data, negligible
- `score_muhurat` + `_score_breakdown` — pure Python table lookups, negligible

Total per-day: approximately 6 `swe.rise_trans` + 8 `swe.calc_ut` = **14 Swiss Ephemeris C-extension calls per day**. Estimated wall-clock: 30–100 ms per day on a warmed Cloud Run instance (swisseph is fast per call but invoked ~14 times). For 90 days: **~2.7–9 seconds of ephemeris CPU time** plus Python overhead. At the high end this exceeds the 60-second timeout; at the low end it does not — but the event-loop blocking and cold-start overhead (documented at ~3s in `SIDECAR_500_INVESTIGATION_REPORT_v1_0.md`) compound to push many real requests into the timeout window.

**Contrast with `query_panchanga`:** The `query_panchanga` retrieval tool reads from the `panchanga_daily` SQL table (73,414 precomputed rows, bootstrapped under `phase-4c-enrich-20260521-r2`). It issues a single `SELECT … FROM panchanga_daily WHERE …` query to Cloud SQL (typically 1–5 ms). Muhurat does not touch `panchanga_daily` at all — it recomputes everything live via the engine on every request.

---

## DESIGN OPTIONS

### Option A — Read from panchanga_daily (SQL cache, read-path only)

- **summary:** Rewrite `find_muhurat()` to query `panchanga_daily` for the five angas (tithi_id, nakshatra_id, vara_id, special_yogas JSONB, inauspicious JSONB, sunrise_utc, sunset_utc, planets JSONB) and score them in Python, eliminating all 90×14 ephemeris calls. `panchanga_daily` already has the full enrichment needed (migration 069: `special_yogas`, `choghadiya`, `hora`, `inauspicious`, `auspicious` JSONB columns added 2026-05-20). The score function reads `tithi.id`, `nakshatra.id`, `vara.id`, `special_yogas`, `planets` — all present. The sidecar already has a DB connection pattern in `routers/panchang.py` and `routers/muhurat.py` (`_fetch_native_chart`). A 90-day range SELECT on an indexed date column returns ~90 rows in <5 ms.
- **effort:** M
- **files touched:**
  - `platform/python-sidecar/panchang_engine/muhurat.py` — add `find_muhurat_from_cache(date_from, date_to, lat, lon, …)` that queries DB instead of calling `compute_panchang()`; keep existing `find_muhurat()` as engine-direct fallback
  - `platform/python-sidecar/routers/muhurat.py` — call `find_muhurat_from_cache` when DB is available; fallback to engine-direct if `DATABASE_URL` not set or table miss
  - New helper: `panchang_engine/panchang_daily_reader.py` — deserialise JSONB columns back into `Panchang`-like objects for scoring
- **risks:**
  - `panchanga_daily` is bootstrapped for Bhubaneswar (20.27°N, 85.84°E). A user querying a different lat/lon gets Bhubaneswar-computed data. For the Muhurat Finder MVP (native chart, IST, Bhubaneswar assumed as default), this is acceptable. Non-Bhubaneswar requests must fall back to engine-direct.
  - JSONB schema evolution: if `panchanga_daily` schema changes, the reader must be updated in sync.
  - Cache miss for dates outside 1900–2100 (extremely unlikely in Muhurat Finder context).
- **composes with panchanga_daily cache:** Yes — this IS the cache read path. Zero ephemeris calls for Bhubaneswar requests. Non-Bhubaneswar falls through to engine-direct.

---

### Option B — Async engine with asyncio.gather (parallel days, no cache)

- **summary:** Move the per-day `compute_panchang()` calls to a thread pool using `asyncio.run_in_executor` so the event loop can serve other requests while the 90-day scan runs. Run days in parallel batches of N (e.g. N=10) to saturate the CPU without OOM.
- **effort:** M
- **files touched:**
  - `platform/python-sidecar/panchang_engine/muhurat.py` — replace the `while` loop with `asyncio.gather(*[loop.run_in_executor(…, compute_panchang, …) for day in range])` in batches
  - `platform/python-sidecar/routers/muhurat.py` — change endpoint to properly await the async `find_muhurat`
  - `platform/python-sidecar/Dockerfile` or Cloud Run deploy — add `--cpu=2` to give the scheduler room to run threads in parallel
- **risks:**
  - swisseph's thread-safety is not fully documented. Concurrent `swe.calc_ut` calls from multiple threads could produce data races on the shared ephemeris state. Would require either a lock per swe call (eliminating parallelism gain) or process-level isolation.
  - Total wall-clock is reduced but not eliminated — still ~90×14 ephemeris calls, just pipelined. At 90 days × 30 ms = 2.7 s minimum (best case, all parallel). More likely 5–15 s with thread overhead and GIL contention.
  - Cloud Run default 60-second timeout is still a ceiling; 90 days stays below it but leaves little margin.
  - Does not solve the fundamental design issue (no cache). Every user query re-computes.
- **composes with panchanga_daily cache:** No — Option B is engine-direct only. It can be combined with Option A (fall back to Option B for non-Bhubaneswar locations).

---

### Option C — Reduce maximum scan window (short-term gate)

- **summary:** Lower the validated maximum from 90 days to 30 days in the sidecar validation check (`routers/muhurat.py` line 147: `if delta > 89`). Update the UI to offer a maximum of 30 days per search and provide a "Next 30 days" button. This is not a fix — it is a stopgap that reduces the worst-case computation by 3×.
- **effort:** S
- **files touched:**
  - `platform/python-sidecar/routers/muhurat.py` — change `> 89` to `> 29`
  - `platform/src/app/panchang/components/MuhuratFinderModal.tsx` — cap the date picker range and add pagination UX
  - `platform/src/app/panchang/hooks/useMuhuratFinder.ts` — add batching logic if UI keeps 90-day intent
- **risks:**
  - Degrades UX: users who want the "best day for vivah in the next 3 months" must submit 3 separate queries and merge results themselves.
  - At 30 days × 14 swe calls × 30–100 ms each = 0.9–3 s, which is below the 60-second timeout with comfortable margin. Still blocks the event loop for 1–3 seconds.
  - Not a fix — re-opens under load or if the window is later restored.
- **composes with panchanga_daily cache:** Option C is independent and can be stacked with A or B as an additional guard.

---

### Option D — Sidecar timeout uplift + min-instances=1

- **summary:** Deploy `amjis-sidecar` with `--timeout=300` (5 minutes), `--cpu=2`, `--memory=1Gi`, and `--min-instances=1` to (a) stop the timeout-induced 503, (b) give the loop more CPU, and (c) eliminate the cold-start 3-second penalty. This is an infrastructure-only change with no code modifications.
- **effort:** S (one `gcloud run services update` command)
- **files touched:**
  - `platform/cloudbuild-sidecar.yaml` — add `--timeout`, `--cpu`, `--memory`, `--min-instances` to the deploy step
  - `platform/scripts/cloud_build_submit.sh` or a new `deploy_sidecar.sh` — document the flags
- **risks:**
  - `--min-instances=1` incurs continuous cost even when idle (estimated ~$10–20/month for 1 vCPU, 1 GiB).
  - Increased timeout means a runaway or stuck request can hold an instance for 5 minutes, wasting Cloud Run quota.
  - Does not eliminate the event-loop blocking problem. A 90-day scan with `--cpu=2` still pins one core; other requests queue behind it.
  - Does not reduce compute cost. Users pay for 90 ephemeris loops on every search.
- **composes with panchanga_daily cache:** Yes — Option D should be applied regardless of which compute fix is chosen, as a deployment hygiene improvement.

---

### Option E — Precomputed muhurat score table (extend panchanga_daily)

- **summary:** Add a `muhurat_scores` JSONB column (or a separate `muhurat_daily` table) to `panchanga_daily` containing per-event scores for all 6 MVP events per day. The bootstrap script populates it once; Muhurat Finder queries reduce to a single SELECT with ORDER BY score DESC LIMIT top_n. Native overlay (Tara Bala) is computed in Python after the DB read (one tara_bala_score() call per result row, not per day scanned).
- **effort:** L
- **files touched:**
  - New migration: `platform/supabase/migrations/XXX_muhurat_scores.sql` — add `muhurat_scores JSONB` to `panchanga_daily`
  - `platform/python-sidecar/pipeline/bootstrap_panchanga.py` — extend to score all 6 events per row and write `muhurat_scores`
  - `platform/python-sidecar/panchang_engine/muhurat.py` — add `find_muhurat_from_scores_table()` path
  - `platform/python-sidecar/routers/muhurat.py` — route to table path; fall back to engine-direct
- **risks:**
  - Bootstrap time: 73,414 rows × 6 events × scoring = ~440,000 score computations. Pure Python arithmetic (no swe calls needed — data already in DB). Estimated bootstrap time: 5–15 minutes.
  - Schema is Bhubaneswar-fixed (same caveat as Option A).
  - Native overlay (Tara Bala) still runs in Python post-SELECT but only on `top_n` rows (10 by default), not 90.
  - Largest effort of all options; requires migration, bootstrap re-run, and swap cycle.
- **composes with panchanga_daily cache:** Yes — this is an extension of the panchanga_daily substrate. It provides the most complete solution: O(1) DB lookup for any 90-day window.

---

## RECOMMENDATION

**Implement Option A + Option D together as a single session.**

Option A (read from `panchanga_daily`) eliminates the root cause — 90 sequential Swiss Ephemeris loops — for the dominant use case (Bhubaneswar / IST, the native's location and the default for all Muhurat Finder calls in the current UI). The data is already precomputed and stored. The JSONB enrichment columns added in migration 069 contain all five scoring inputs (tithi, nakshatra, vara, special_yogas, inauspicious). Implementation requires a DB-backed code path in `find_muhurat()` and a JSONB deserialiser — approximately one session of work.

Option D (timeout uplift + min-instances=1) is a one-command infrastructure fix that should be applied regardless of which compute path is chosen. It eliminates the cold-start failure mode documented in `SIDECAR_500_INVESTIGATION_REPORT_v1_0.md` and gives a safety margin if a non-Bhubaneswar engine-direct request is ever triggered.

Option C (window cap to 30 days) should be deferred unless Option A + D proves insufficient after deployment — it degrades UX without solving the root problem.

Option B (asyncio parallelism) is inadvisable until swisseph thread-safety is confirmed and the cache path is unavailable.

Option E (muhurat_scores table) is the cleanest long-term architecture but requires a migration and bootstrap re-run; it should be scheduled as a follow-up improvement (Phase 4C.2 or 4D scope) once Option A is live and validated.

**Implementation order for the next session:**
1. Option D — deploy sidecar with `--timeout=300 --cpu=2 --memory=1Gi --min-instances=1` (immediate, no code change, eliminates 503s while Option A is developed).
2. Option A — `panchang_engine/panchang_daily_reader.py` + DB-backed `find_muhurat_from_cache()` + router fallback logic.
3. Smoke test: 90-day vivah request for Bhubaneswar → should return in <200 ms from DB; verify non-Bhubaneswar lat/lon falls back to engine-direct gracefully.
