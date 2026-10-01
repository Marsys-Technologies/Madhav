---
artifact: DESIGN_VIGHNAKARA_GANDANTA_WINDOWS
version: "1.1"
status: DRAFT-FOR-REVIEW (SS scope ruling applied; for merge)
produced_by: exec-suvarna
produced_on: 2026-10-01
asset_id: ka_vighnakara
track_i_item: "TI-L3-NEW: ka_vighnakara Gandanta entry/exit windows"
ruling: "SS N-28 (2026-10-01) option (b): root-find real windows. SS scope ruling on PR #2839: ANCHOR-SCOPED, not a lifetime sweep."
rulings_followed: "A-1, Q-L3-X1, and the PR #2839 rulings (columns + partial unique index; ph_pratikara unchanged; darshana joins by overlap; two-component digest spec after 1212)"
base_commit: "origin/main 4eb40bec1"
scope: "DOCS ONLY. No code, no migration, no DB write. DB reads as suvarna_reader."
evidence_dir: "/Users/Dev/suvarna-evidence/TrackI/vighnakara_windows/ (outside the repo); file list in Appendix A"
changelog:
  - "1.0 (2026-10-01): first draft (lifetime sweep)."
  - "1.1 (2026-10-01): SS scope ruling: anchor-scoped windows replace the lifetime sweep; sections 3-5 rewritten; row estimate from the writer's real anchors; table owner verified; detail to Appendix A."
---

# Design review: Gandanta windows for the anchors `ka_vighnakara` already tests

## 0. Scope (SS ruling) and two framing facts

- **Scope.** Lunar Gandanta passages are global ephemeris facts, identical for every chart. The asset means "obstructions at this chart's anchor dates". So for each anchor date the writer already tests (top 500 convergence peaks, `ka_vighnakara.py:205-213`, plus up to `_MAX_DASHA_ANCHORS = 200` dasha anchors, `:40`, `:281-295`), root-find whether that anchor's day overlaps a passage and store **that passage's exact entry/exit**. No lifetime sweep, no per-chart copy of a global fact.
- **The writer is not a daily sweep.** It probes the Moon at most once per anchor date, at 00:00 UT (`_jd_from_date`, `:169-173`).
- **The L1 zone is one contiguous 6°40' arc per junction** (last 3°20' of Cancer/Scorpio/Pisces plus first 3°20' of Leo/Sagittarius/Aries; `GANDANTA_ARC = 30/9`, `check_gandanta`, `ga_writers/ga_sensitive_degree_writer.py:198-224`). The Moon is in a junction 10.5-13.6 h, in each half-arc 5.2-6.8 h. "~80 passages a year" counts half-arcs; per junction it is 40.1.

## 1. Evidence (offline, reproducible; Moshier backend here, see A.3)

Lifetime scan, 2000-01-01..2030-12-31 UT (31.0 y), writer's own `_get_sidereal_lon`/`_jd_from_date`, L1 `GANDANTA_ARC`/`check_gandanta`, 6 h bracket scan, bisection to 0.5 s:

| measure | L1 junction (6°40') | half-arc (3°20') |
|---|---|---|
| passages | **1,243 = 40.1 / year** | 2,486 = 80.2 / year |
| dwell h (min / mean / max) | 10.47 / 12.14 / 13.56 | 5.23 / 6.07 / 6.78 |
| caught by a 00:00 UT sample | **633 = 50.9 %** | 25.5 % |

- 1,876 of 11,323 UT days (**16.6 %**) overlap a passage; the 00:00 UT instant is inside on 633 (5.6 %). So the day-overlap test finds about **3x** the hits of today's instant test.
- `swe.mooncross_ut` (independent oracle) agrees with the bisection to a maximum of 0.165 s over 3,732 instants.
- **Per-anchor algorithm validated against the lifetime scan:** applying it to every UT day of 2000-2030 finds the same 1,876 touched days and the same **1,243** distinct passages (nothing missed, nothing extra).

## 2. Reuse (do NOT write a new ephemeris)

| need | reuse |
|---|---|
| Moon sidereal longitude, SWIEPH-asserted | `services/gochara_kernel/knots.py:105 calc_sidereal_lon` (+ `EphemerisBackendError :54`). The writer's own `_get_sidereal_lon` (`:150`) sets no ephe path and asserts nothing. |
| root refinement (primary) | `services/gochara_kernel/contacts.py:116 swiss_bisect(body, jd_lo, jd_hi, level_wrapped_deg, ephe_path, tol_days)`: direct Swiss bisection, SWIEPH asserted per call. Brackets here are about 4 deg of travel, far below its 180 deg limit. |
| entry/exit shape precedent | `services/w2g/crossings.py:148 solve_contact_window` (`entry_truncated`/`exit_truncated`). Arc-substrate based, and the Moon is Tier C LAZY there (`services/w2g/tiers.py`), so not used. |
| fail-closed backend pattern | `pipeline/orchestrator/writers/bg_sky_calendar.py:231 _require_swiss_file_backend` + `_require_reproducible_write_runtime` |
| arcs | L1 `GANDANTA_ARC`/`check_gandanta` today; per ruling A-1 the shared L0 Gandanta module (TI-L3-26) once it exists. `_WATER_SIGNS` is private, so a public accessor is needed either way (Q3). |
| other precedents, tests | `panchang_engine/angas.py:54`, `services/ka_tithi_pravesha/logic.py:121`, `swe.mooncross_ut` (oracle). Detail in A.1. |

## 3. Algorithm (per anchor date)

1. **Anchor day = the UT day of `peak_date`, `[00:00, 24:00)` UT.** The writer evaluates at `swe.julday(y, m, d, 0.0)` (`_jd_from_date`, `:169-173`, used at `:253` and `:291`), so the UT day is the writer's own convention for the Moon. *Local-day alternative:* the writer also holds the chart's tz offset (`_resolve_native_location`, `:349-410`), used today only for the tithi detector (`compute_panchang(peak_date, lat, lon, tz_offset_minutes)`, `:704-710`). A chart-local day would be `[d 00:00 local, +24 h)`; because windows are stored as absolute UTC instants, switching is only the overlap predicate (measured: IST days touched 1,876, identical). Overlap test, half-open: `window_start < day_end AND window_end > day_start`.
2. **Bracket.** Scan `[day_start - 1 d, day_end + 1 d]` with 6 h knots (12 intervals). The Moon never retrogrades (min 11.77 deg/day), so unwrapped longitude is strictly increasing and a level crossing shows as a change of `floor((u - L)/360)`. The step need not resolve the dwell. The 1 d margin exceeds the 13.6 h maximum dwell, so a passage straddling the scan edge is found whole.
3. **Levels** for the three junctions come from the shared definition (never literals): entry `30w + (30 - GANDANTA_ARC)`, cusp `30(w+1) mod 360`, exit `30(w+1) + GANDANTA_ARC` for w in {Cancer 3, Scorpio 7, Pisces 11} (Pisces-Aries uses 356.667 / 0 / 3.333; wrapped separation is continuous in a 4 deg bracket). Edges inclusive as in L1.
4. **Refine** each crossing with `swiss_bisect` to **0.5 s**; pair entry with the next exit; keep passages that overlap the anchor day. An anchor day overlaps **at most one** passage (junction passages are at least about 9 d apart).
5. **Fail closed:** probe error, or knot-to-knot advance outside (0, 20) deg, raises. Pin `set_ephe_path(SWE_EPHE_PATH)` under `swiss_state_scope` and assert `retflag & 2`. `compute_panchang` calls `swe.set_ephe_path(None)` (`panchang_engine/__init__.py:71`) and the writer never re-sets it, so the Moon probe may already run on a reset path (A.3).
6. **Dedup.** Two anchors hitting the same passage produce one row (section 4).

Cost: at most 700 anchors x about 13 knots + a few roots each: well under a second per build. Horizon edges are not an issue (no horizon): every stored passage is whole. Assert the anchor date lies in the ephemeris file span (`sepl_18`/`semo_18`, 1800-2400), else raise.

## 4. Output row shape, key, migration, digest, count

**Today.** Live DDL: `kala_obstruction(id bigserial PK, chart_id, convergence_id NULL, signal_id NULL, obstruction_type CHECK(7), severity, severity_score, override_score, obstruction_detail jsonb, source_citation, computed_at)`. **No start/end columns and no unique key except `id`.** A single-date verdict borrows a window from `kala_convergence` through `convergence_id`. A window row does not fit as-is.

**Migration (NOT written here; SS ruling 1: YES, ALTER-only).**
- `ALTER TABLE kala_obstruction ADD COLUMN IF NOT EXISTS window_start TIMESTAMPTZ, ADD COLUMN IF NOT EXISTS window_end TIMESTAMPTZ` (nullable, no default: metadata-only), `CHECK (window_end > window_start)`.
- Migration-679-style natural key, additive: `CREATE UNIQUE INDEX IF NOT EXISTS ... ON kala_obstruction (chart_id, obstruction_type, window_start) WHERE window_start IS NOT NULL`. Dry-run it on real rows first (679's first two candidate keys failed live).
- Start with `SET LOCAL lock_timeout = '5s'`, as 1212 does.
- **Owner verified read-only from the catalog:** `kala_obstruction`, its sequence `kala_obstruction_id_seq`, `kala_convergence` and `asset_output_digest_specs` are all owned by **`amjis_app`** (`pg_class.relowner`). The pre-approval condition (amjis_app owns the table) holds. The migration role itself is unverified (A.3).

**Row.** `obstruction_type='gandanta'`, `window_start/window_end` (UTC, whole seconds), `convergence_id NULL`, `signal_id NULL`, `severity 'moderate'`, `severity_score 0.55`, `override_score 0.22` unchanged (CF-27 is a separate question). `obstruction_detail`: junction, cusp instant, entry/exit longitudes, `anchor_dates` (sorted ISO list), `anchor_sources` (`convergence` / `dasha_timeline`), tolerance, solver, `GANDANTA_CITATION`. No wall-clock.

**Natural key and dedup: one row per distinct passage per chart** (`(chart_id, 'gandanta', window_start)`), not per anchor. Several anchors on adjacent days that hit the same passage are listed in `anchor_dates` of one row. Consequences for consumers: a window row cannot carry a single `convergence_id`/`signal_id` (one passage may serve several convergence peaks or dasha anchors, and `convergence_id` is regenerated by every `ka_sangam` rebuild), so **consumers join by time overlap, never by FK.**

**Digest (1212 first, with PR #2826; then this).** 1212 hashes `chart_id, signal_id, obstruction_type, severity, severity_score, override_score, obstruction_detail` with `signal_id` among its non-NULL key columns; its limit (d) says a NULL `signal_id` errors the build, and it does not hash the window columns. So **1212 alone would error on the first window row.** The re-issued spec (new `spec_sha256`, 1212's row retired, landing before the first window build) has two components, using the grammar in `pipeline/orchestrator/output_digest.py:52-80` (`where_equals`, `where_is_null`): (A) legacy anchored types, `where_is_null: [window_start]`, as in 1212; (B) windows, `where_equals obstruction_type='gandanta'`, key `window_start`, values incl. `window_end`, `obstruction_detail`. End-to-end validity is unverified until built.

**Idempotency.** Delete-then-insert per chart (N.3), but compute all rows first, then DELETE + INSERT in the one orchestrator transaction (today the DELETE at `:203` precedes the read). Digest stability needs byte-stable instants: whole seconds, and the runtime pinned as `bg_sky_calendar` does.

**Row-count estimate (anchor scope).** Rows = distinct passages overlapped by an anchor day = about 0.166 x D, where D = distinct anchor dates (at most 700). Measured with the writer's own anchor selection (read-only; `vighnakara_anchor_scope_evidence.py --mode chart`):

| chart | convergence rows chosen -> distinct peak dates | dasha anchor dates | D | anchors overlapping a passage | **rows** | today's instant test |
|---|---|---|---|---|---|---|
| 1c826d5a | 500 -> 15 | 45 | 60 | 8 (13.3 %) | **8** | 1 |
| cb73cd3d | 500 -> 193 | 45 | 238 | 42 (17.6 %) | **42** | 14 |
| 482012f1 (canonical, `kala_convergence` empty now) | 0 | 45 | 45 | 9 (20 %) | 9 (dasha only) | 2 |

**Expected per chart: roughly 10-45 rows; hard ceiling about 120 (700 x 16.6 %).** Anchors cluster heavily (500 convergence rows collapse to 15-193 dates), which is why D is far below 700. The last canonical build held 38 gandanta rows (old, wrong zones) of 536. The table stays at its present scale. Dasha anchors are an upper bound (the read-only role cannot read `public.charts`, so the birth clip was skipped; capped at 200). Note: the writer returns early when `kala_convergence` is empty (`:220`), so today the canonical chart would not even reach its dasha anchors; unchanged by this design (Q4).

## 5. Consumers, rebuild, tests, risk

| consumer | consequence |
|---|---|
| `ka_kala_darshana.py:38-74` (groups by `convergence_id`) | **joins by overlap** (ruling 2): a window row applies to a convergence whose `peak_date` UT day overlaps it (the peak anchor, not the whole convergence span). Hits rise about 3x (16.6 % vs 5.6 % of days), so the 0.22 override applies to more windows: a visible output change. |
| `ph_pratikara.py:205-232` (one mitigation per row) | **no change, no exclusion needed** (ruling 2): about 10-45 window rows, the same scale as today's gandanta rows. Window rows arrive convergence-less (LEFT JOIN yields NULL domain/graha/window), as dasha-anchored rows already do. Optional later: read `COALESCE(o.window_start, c.window_start)`. |
| `ph_muhurta.py:282-310` (INNER JOIN `kala_convergence`) | unchanged; window rows ignored, as dasha-anchored rows are. |
| `query_obstruction_periods.ts:80-89`, `kala_temporal.ts:373` | add `window_start/end` to the SELECT and a date filter; "carries no date range" becomes partly false (and its test, line 228). No flooding: scale unchanged. |
| registry | reset `target_floor` after the build (floors are aspirational); migration 856's volume formula needs a window term; `nirmana-writer-digests.json`/declaration pins change (as PR #2836 did). |

**Rebuild impact.** The digest changes, so `ka_kala_darshana`, `ka_bhavishya_lekha`, `ka_tulana`, `ph_muhurta`, `ph_pratikara` go stale (direct 5 / transitive 22 per the A.L3 brief census). The canonical chart is queued for rebuild (wave 4): land this before it to avoid a double rebuild. The anchored point detector `_check_gandanta` is retired (one source of truth).

**Tests.**
1. Golden instants: 12+ entry/cusp/exit instants over 4 passages (one Pisces-Aries seam, one at a year boundary) against `swe.mooncross_ut` and a third path (tropical minus `swe.get_ayanamsa_ut`, `brentq`). Tolerance 1 s.
2. Equivalence: per-anchor algorithm over a full multi-year day range equals the lifetime scan (already shown for 2000-2030: 1,876 days, 1,243 passages).
3. Dedup: two anchors on adjacent days hitting one passage give one row with both dates. A passage straddling UT midnight is hit by both days.
4. Edges: anchor day exactly touching a window edge (half-open rule); Moon exactly on an L1 edge (inclusive; the 9-decimal rounding trap fixed in PR #2836); non-monotone knots raise; Moshier raises.
5. Digest: identical across two builds with reversed row order; moves when `window_start` moves 1 s.
6. Consumers: darshana overlap; `phala_mitigation` count unchanged by the window rows' presence beyond today's scale; `query_obstruction_periods` returns start/end and honors a date filter.

**Risk.** Digest re-issue ordering (1212 first, then the two-component spec, before any window build); backend pinning; consumer join semantics (darshana overlap changes scores); classical granularity (junction vs half-arc, acharya); cross-asset import of a `gochara_kernel` helper (a thin local copy is the alternative).

## 6. Removal of the tithi fallback (unchanged in substance; follows Q-L3-X1)

On main: `ka_vighnakara.py:717-719` (`tithi = (peak_date.day % 15) or 15`), Rikta test `:722`, label `:732`. PR #2836 changes the Rikta set to the engine's but leaves the proxy.

- The location resolver already raises (`_resolve_native_location`, `:349-410`, CR-87). Silent paths remaining: (i) `KaMuhurtaSevaService` import failure sets `_muhurta=None` (`:229-233`) and the proxy runs for every anchor; (ii) a `compute_panchang` exception is only `logger.debug`-ed (`:714-715`); (iii) the label `'panchang_engine' if muhurta_service else 'day_mod_proxy'` (`:732`) misreports (ii); (iv) `_detect_all` swallows every detector exception at debug level (`:574-575`). `muhurta_service` is only a boolean gate, never called.
- **Proposal:** delete the proxy and label; drop the gate; tithi from `compute_panchang`. Per-anchor engine failure: **no panchanga row** plus `detector_status` (flag only, never a score) counted in `WriterResult.notes`; never a default tithi. Systemic failure (resolver, service import, backend) raises. N.7 item 6 / N.8: a missing row must carry a status.
- Measured 2000-2030 (true tithi from Sun/Moon separation at 00:00 UT): the proxy's Rikta verdict is wrong on **35.3 %** of days against the engine's Rikta set (4/9/14/19/24/29), 31.5 % against its own 4/9/14 subset; the tithi number is wrong on 93 %. SS's "about 29 %" is not reproduced (definition-dependent).

## 7. Open questions

Ruled by SS (no longer open): scope (anchor-scoped), additive columns + partial unique index, `ph_pratikara` no change, darshana overlap, two-component digest spec.

- **Q1** Row granularity: one row per junction passage (recommended; half-arc boundaries in `detail`) or per half-arc (2x rows)?
- **Q2** Severity: one constant 0.55 per window, or graded by depth (distance to the cusp)? Acharya (CF-27).
- **Q3** The shared Gandanta module (A-1) must publicly export the water-sign set or the six edge levels. Does the window builder wait for it or start on L1 `GANDANTA_ARC`?
- **Q4** The early return at `:220` hides dasha anchors when `kala_convergence` is empty. Relax it (45 dasha anchors reachable on the canonical chart) or leave as is?
- **Q5** Anchor-day convention for darshana and the writer: UT day (this design, the writer's Moon convention) or chart-local day (the tithi detector's convention)? Which instant does `compute_panchang(...).tithi` report?
- **Q6** Reuse `gochara_kernel.swiss_bisect` across assets, or a thin local helper?

## Appendix A. Detail

**A.1 Other precedents.** `panchang_engine/angas.py:54 _bisect_boundary` (+/-1 s, private) and `:47 _get_sun_moon_lon`; `services/ka_tithi_pravesha/logic.py:121 lunar_return` (nearest-to-seed, 30 s tolerance, never raises: returns `converged: False`; its docstring documents the +/-180 deg wrap trap; pattern only); `services/ka_graha_sancara/engine.py:344 get_ephemeris` is daily-noon (bg_ephemeris) or a live path documented as Moshier, not usable for instants; the Moon arcs in `bg_gochara_arcs` (3,357 arcs, JD 2415021-2506696) exist but the Moon is LAZY (`services/w2g/solver.py` needs `include_lazy=True`).

**A.2 Evidence files** (in `/Users/Dev/suvarna-evidence/TrackI/vighnakara_windows/`): `vighnakara_windows_evidence.py/.json` (lifetime scan, section 1); `vighnakara_anchor_scope_evidence.py` with `anchor_scope_validate.json` (per-anchor vs lifetime) and `anchor_scope_chart_<id8>.json` (section 4 table); `tithi_fallback_mismatch.py/.json` (section 6).

**A.3 Unverified.** (a) The production writer's effective ephemeris path (this run is Moshier, no `.se1` locally; `Dockerfile` sets `SWE_EPHE_PATH=/app/ephe`; `compute_panchang` resets the path); (b) instants on SWIEPH (0.165 s agreement is like-with-like on Moshier); (c) the two-component digest spec end-to-end, and the retire mechanics for 1212's row; (d) which DB role `migrate.ts` connects as (it must be `amjis_app` or a member to ALTER); (e) PRs #2826/#2835/#2836 are unmerged at base; (f) `swiss_bisect` was read, not executed (it raises on Moshier); (g) the dasha-anchor counts exclude the birth clip (read-only role cannot read `public.charts`), so they are upper bounds, and the canonical chart's figure is hypothetical until `ka_sangam` is rebuilt; (h) the canonical row count remains a projection.
