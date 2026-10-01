---
artifact: DESIGN_VIGHNAKARA_GANDANTA_WINDOWS
version: "1.0"
status: DRAFT-FOR-REVIEW
produced_by: exec-suvarna
produced_on: 2026-10-01
asset_id: ka_vighnakara
track_i_item: "TI-L3-NEW: ka_vighnakara Gandanta entry/exit windows"
ruling: "SS N-28 (2026-10-01), option (b): store real Moon entry/exit windows by root-find; remove the day-of-month tithi fallback"
base_commit: "origin/main 4eb40bec1 (writer read at main; PR #2836 branch suvarna/land/TI-vighnakara-gandanta-rikta-001 read at its tip; PR #2826 migration 1212 read on suvarna/land/TI-i45-provenance-001)"
scope: "DOCS ONLY. No code, no migration, no DB write. DB reads as suvarna_reader."
evidence_dir: "/Users/Dev/suvarna-evidence/TrackI/vighnakara_windows/ (outside the repo): vighnakara_windows_evidence.py + .json, tithi_fallback_mismatch.py + .json"
changelog:
  - "1.0 (2026-10-01): first draft for review."
---

# Design review: Gandanta windows by entry/exit root-find

## 0. Two corrections to the framing (measured, they change the design)

1. **The writer is not a daily sweep.** It runs the five detectors at **anchor dates only**: the top 500 `kala_convergence` peaks (`ka_vighnakara.py:213`) plus up to `_MAX_DASHA_ANCHORS = 200` dasha peaks (`:40`), each at 00:00 UT (`_jd_from_date`, `:169`). So it makes at most ~700 Moon probes per build, not 365 a year. The Abhinandan chart (`1c826d5a`) shows 38 distinct anchor dates among its 741 rows.
2. **The L1 zone is one contiguous 6°40' arc per junction, not six separate 3°20' arcs.** The last 3°20' of Cancer/Scorpio/Pisces and the first 3°20' of Leo/Sagittarius/Aries touch at the sign cusp (`GANDANTA_ARC = 30/9`, `check_gandanta`, `ga_writers/ga_sensitive_degree_writer.py:198-224`). The Moon is in a junction for 10.5-13.6 h, and in each half-arc for 5.2-6.8 h.

## 1. Problem and evidence

Offline, reproducible (`vighnakara_windows_evidence.py --repo <worktree>`; runs in about 1.5 s). It uses the writer's own `_get_sidereal_lon`/`_jd_from_date` and L1 `GANDANTA_ARC`/`check_gandanta`, a 6 h bracket scan, and bisection to 0.5 s. Window 2000-01-01 to 2030-12-31 UT (31.0 y).

| measure | L1 junction (6°40') | half-arc (3°20', the "six arcs") |
|---|---|---|
| passages | **1,243 = 40.1 / year** (40-41 every year) | 2,486 = 80.2 / year |
| dwell (h) min / mean / max | 10.47 / 12.14 / 13.56 | 5.23 / 6.07 / 6.78 |
| caught by a 00:00 UT sample | **633 = 50.9 %** (610 missed) | 633 = 25.5 % |

Day level: 1,876 of 11,323 UT days (16.6 %) contain Gandanta time. The 00:00 UT sample is inside on only 633 (33.7 % of those days). The Moon's speed over the window is 11.77-15.38 deg/day.

Today's coverage is far worse than "half": with at most ~700 anchors a build examines under 1 % of the roughly 4,650 passages in birth to 2100.

Independent check of the instants: `swe.mooncross_ut` (sidereal; not used by the writer) agrees with the bisection to a **maximum of 0.165 s over 3,732 instants** (mean 0.084 s).

**Caveat:** this machine has no `.se1` files, so the run used the Moshier fallback (retflag has bit 4). Dwell statistics are insensitive to that. The instants must be re-checked on SWIEPH (see section 7).

## 2. Existing engine pieces to reuse (do NOT write a new ephemeris)

| need | reuse | note |
|---|---|---|
| Moon sidereal longitude, SWIEPH-asserted | `services/gochara_kernel/knots.py:105 calc_sidereal_lon` (+ `EphemerisBackendError`, `:54`) | Lahiri, `FLG_SWIEPH\|FLG_SIDEREAL`, serialized seam, returns retflag. The writer's current `_get_sidereal_lon` (`ka_vighnakara.py:150`) sets no ephe path and asserts nothing. |
| root refinement | `services/gochara_kernel/contacts.py:116 swiss_bisect(body, jd_lo, jd_hi, level_wrapped_deg, ephe_path, tol_days)` | direct Swiss bisection on a wrapped separation, asserts SWIEPH on every call, one widen-on-lost-bracket. **Primary.** Valid for brackets under 180 deg of travel; ours are about 4 deg. |
| entry/exit window shape | `services/w2g/crossings.py:148 solve_contact_window` (`entry_truncated`/`exit_truncated`) | precedent for the output shape and honest horizon truncation. It runs on the arc substrate (`bg_gochara_arcs`, Moon: 3,357 arcs, JD 2415021-2506696). The Moon is Tier C LAZY there (`services/w2g/tiers.py`, ADJ-14: "never materialized full-span"), so it needs `include_lazy=True` (`services/w2g/solver.py`). **Not recommended for a lifetime sweep.** |
| second bisection precedent | `panchang_engine/angas.py:54 _bisect_boundary` (+/-1 s), `:47 _get_sun_moon_lon` | the writer already imports `panchang_engine`. The helper is private. |
| lunar-return root-find | `services/ka_tithi_pravesha/logic.py:121 lunar_return` | nearest-to-seed, 30 s tolerance, never raises (returns `converged: False`). Its docstring documents the +/-180 deg wrap trap. Pattern only, not fail-closed enough. |
| fail-closed backend assertion | `pipeline/orchestrator/writers/bg_sky_calendar.py:231 _require_swiss_file_backend` and `_require_reproducible_write_runtime` | copy the pattern around the new code. |
| arcs | `GANDANTA_ARC`, `check_gandanta` (L1) | `_WATER_SIGNS` is private; request a public accessor (Q8). |
| cross-check (tests only) | `swe.mooncross_ut(level, jd, FLG_SIDEREAL)` | independent oracle used in section 1. |

`services/ka_graha_sancara/engine.py:344 get_ephemeris` is daily-noon resolution (bg_ephemeris) or a live path documented as Moshier. Not usable for instants.

## 3. Proposed algorithm

- **Levels from the L1 constant, never literals.** For each water sign w in {Cancer 3, Scorpio 7, Pisces 11}: entry level `30w + (30 - GANDANTA_ARC)`, cusp `30(w+1) mod 360`, exit level `30(w+1) + GANDANTA_ARC (mod 360)` (116.667 / 120 / 123.333; 236.667 / 240 / 243.333; 356.667 / 0 / 3.333). Edges are inclusive in L1 (`>=`, `<=`), so entry is the first instant inside and exit the last.
- **Bracket on level crossings, not on "inside" state.** The Moon never retrogrades (minimum 11.77 deg/day), so unwrapped longitude is strictly increasing and each level is crossed once per 27.3 d revolution. A crossing shows as a change of `floor((u - L)/360)` between consecutive knots. The step therefore need not resolve the dwell. Use **6 h knots**: advance 2.94-3.85 deg per knot, below the 6.67 deg arc, and since the minimum dwell (10.47 h) exceeds 6 h every window must also contain at least one knot, which is a free redundancy assertion. **Fail closed:** any probe error, or any knot-to-knot advance outside (0, 20) deg, raises. Never skip.
- **Refine** each bracket with `swiss_bisect` to **0.5 s** (about 16 iterations; about 14k roots for birth to 2100, a few seconds). Seam: the Pisces-Aries junction uses levels 356.667 / 0 / 3.333; the wrapped separation is continuous inside a 4 deg bracket.
- **Pair** each entry with the next exit; the cusp instant is recorded inside the window (it is the exact junction).
- **Horizon edges.** Scan from one revolution (28 d) before the start to 28 d after the end, and store every window that overlaps the horizon **whole, never clipped**. Assert the horizon lies inside the ephemeris file span (`sepl_18`/`semo_18`, 1800-2400), else raise.
- **Backend.** Pin `set_ephe_path(SWE_EPHE_PATH)` under `swiss_state_scope` and assert `retflag & 2`, as `bg_sky_calendar` does. `panchang_engine.compute_panchang` calls `swe.set_ephe_path(None)` (`panchang_engine/__init__.py:71`), and the writer never re-sets it, so the Moon probe may already run on a reset path (unverified, section 7).
- **Stored precision:** instants rounded to the whole second (tolerance 0.5 s), UTC.

## 4. Output row shape and the table

**Today (live DDL, migration 245 plus FKs):** `kala_obstruction(id bigserial PK, chart_id, convergence_id NULL, signal_id NULL, obstruction_type CHECK(7 types), severity, severity_score, override_score, obstruction_detail jsonb, source_citation, computed_at)`. **There are no start/end columns and no unique key except `id`.** (The `brahma_kala_obstruction.sql` DDL with `date` and `UNIQUE(chart_id, date, type)` was dropped by 245.) Each row is a single-date verdict whose window, if any, is borrowed from `kala_convergence` through `convergence_id`.

**Verdict: a window row does not fit as-is.** Gandanta windows have no convergence link and no signal.

**Recommended (Option A, additive, one small migration, NOT written here):**

- `window_start TIMESTAMPTZ NULL`, `window_end TIMESTAMPTZ NULL`, `CHECK (window_end > window_start)`.
- Migration-679-style natural key, additive: `CREATE UNIQUE INDEX ... ON kala_obstruction (chart_id, obstruction_type, window_start) WHERE window_start IS NOT NULL`. Dry-run it against real rows before finalizing (679's lesson: its first two candidate keys failed live).
- Window rows: `obstruction_type='gandanta'`, `convergence_id NULL`, `signal_id NULL`. `severity 'moderate'`, `severity_score 0.55`, `override_score 0.22` unchanged (CF-27 is a separate SS question; nothing new is invented). `obstruction_detail`: junction, entry/cusp/exit instants, entry/exit longitude, `GANDANTA_ARC` reference, tolerance, solver name, `GANDANTA_CITATION`. No wall-clock and no `peak_date`.
- **Option B (alternative):** a new table `kala_gandanta_window` with a true natural key `(chart_id, junction, window_start)`. Zero blast radius on the three readers, but needs a CREATE plus grants (646-style), a second `count_sql` term, a new serving capability and a second digest component. Choose B only if SS wants no consumer change.

**Digest spec (migration 1212 on branch TI-i45-provenance-001).** 1212 hashes `chart_id, signal_id, obstruction_type, severity, severity_score, override_score, obstruction_detail`, with `signal_id` among its non-NULL key columns. Its own header (limit d) says a NULL `signal_id` errors the build. Standalone windows have NULL `signal_id`, so **1212 as written would make the first window build error.** It also does not hash `window_start`/`window_end`. Needed: a re-issued spec (new `spec_sha256`; 1212's row retired) with two components, using the grammar that exists in `pipeline/orchestrator/output_digest.py:52-80` (`where_equals`, `where_is_null`): (A) legacy anchored types, `where_is_null: [window_start]`, as 1212; (B) windows, `where_equals obstruction_type='gandanta'`, key `window_start`, values include `window_end` and `obstruction_detail`. Land it before or with the writer change. Whether the two-component spec validates end-to-end is unverified until built.

**Idempotency.** Delete-then-insert per chart (CLAUDE.md N.3), but **compute all rows first, then DELETE + INSERT in one orchestrator transaction.** Today the DELETE (`:203`) precedes the convergence read, and the early return "No convergence windows" (`:220`) would leave the chart empty. Windows do not depend on convergence and must be emitted regardless. Digest stability needs byte-stable instants: pin the runtime (backend + library) as `bg_sky_calendar` does.

**Row-count estimate (canonical chart; 40.1 / year, one row per junction passage):** 10 y about 401; 100 y (the convergence horizon 1950-2050) about 4,010; birth 1984-02-05 to 2100-01-01 (the `ka_jivana_parva` horizon, `date(2100,1,1)`) about **4,650**. Per half-arc, double. The last canonical build held 536 rows (38 gandanta; today 0 rows, `ka_sangam` empty), so the table grows about 9x.

## 5. Output changes, consumers, rebuild, tests, risk

| consumer | today | consequence |
|---|---|---|
| `ka_kala_darshana.py:38-74` | groups obstructions by `convergence_id`; override = max over a window | standalone windows never match, so Gandanta stops affecting any darshana score unless the reader joins by **overlap** with the convergence window or peak date. A civil-day overlap touches about 3x more days than the 00:00 UT instant (16.6 % vs 5.6 %), so the 0.22 override would hit about 3x more windows. SS ruling needed (Q4). |
| `ph_pratikara.py:205-232` | one `phala_mitigation` per `kala_obstruction` row, ordered by `severity_score` | would add about 4,650 programs with no graha/domain/window bridge. **Must exclude standalone windows** (or SS rules otherwise). Unguarded this is a silent about 9x fan-out. |
| `ph_muhurta.py:282-310` | INNER JOIN `kala_convergence` | standalone rows ignored (unchanged). Opportunity: avoid windows in muhurta selection (out of scope). |
| `query_obstruction_periods.ts:80-89` | explicit columns, top 50 by `severity_score`, no date filter | add `window_start/end` to SELECT and a date filter. About 4,650 rows at 0.55 would crowd out other types in the top 50 (density rule, CLAUDE.md N.6). `platform-mcp/src/tools/retrieval/kala_temporal.ts:373` ("kala_obstruction carries no date range at all") and its test line 228 become partly false. |
| registry | `target_floor` 536, migration 856 formula | reset the floor after the build (floors are aspirational); the 856 volume formula needs a window term; `nirmana-writer-digests.json` / declarations pins change (as PR #2836 did). |

**Rebuild impact.** The digest changes, so `ka_kala_darshana`, `ka_bhavishya_lekha`, `ka_tulana`, `ph_muhurta`, `ph_pratikara` go stale (direct 5 / transitive 22 per the brief census). The canonical chart currently has 0 obstruction and 0 convergence rows and is queued for rebuild (wave 4), so **land this before that rebuild to avoid a double rebuild.** The anchored point detector `_check_gandanta` is retired once windows land (one source of truth); Gandanta stops being written as an anchored row.

**Test plan.**
1. Golden instants: 12+ hand-pinned entry/cusp/exit instants over 4 passages (one Pisces-Aries seam, one at a year boundary), against `swe.mooncross_ut` and a third path (tropical longitude minus `swe.get_ayanamsa_ut`, scipy `brentq`). Tolerance 1 s.
2. Zone equivalence: at 1,000 random instants, inside-any-window iff L1 `check_gandanta` fires; windows are disjoint, sorted, 10-14 h, 40-41 per year.
3. Edge arcs: seam junction; Moon exactly on an edge (L1's inclusive rule; the 9-decimal rounding trap fixed in PR #2836); window straddling a UT midnight and a year end; horizon-start window in progress (stored whole); a non-monotone knot series must raise.
4. Backend: Moshier must raise (mirrors `bg_sky_calendar`).
5. Digest: identical across two builds with reversed row order; moves when `window_start` moves 1 s.
6. Consumers: darshana overlap semantics; `phala_mitigation` count unchanged; `query_obstruction_periods` returns start/end and honors a date filter.

**Risk.** About 9x rows; consumer fan-out (`ph_pratikara`); digest re-issue ordering; backend pinning; classical granularity (junction vs half-arc; acharya); cross-asset import of a `gochara_kernel` helper (a thin local copy is the alternative, Q7).

## 6. Removal of the tithi fallback

On main: `ka_vighnakara.py:717-719` (`tithi = (peak_date.day % 15) or 15`), Rikta test `:722`, label `:732`. PR #2836 changes the Rikta set to the engine's but **leaves the proxy**.

- The location resolver already raises on main (`_resolve_native_location`, `:349-410`, CR-87), so "resolver fails" is already loud. The silent paths that remain: (i) `KaMuhurtaSevaService` import failure sets `_muhurta=None` (`:229-233`), then the proxy runs for every anchor; (ii) a `compute_panchang` exception is only `logger.debug`-ed (`:714-715`), then the proxy; (iii) the label `'panchang_engine' if muhurta_service else 'day_mod_proxy'` (`:732`) reports the wrong source in case (ii); (iv) `_detect_all` swallows every detector exception at debug level (`:574-575`), so a missing row looks like "no obstruction". `muhurta_service` is only a boolean gate and is never called.
- **Proposal:** delete the proxy and the label; drop the `muhurta_service` gate; take the tithi from `compute_panchang`; on engine failure **raise** (systemic) and record any per-anchor "engine declined" count in `WriterResult.notes` (never a default tithi). This is the N.7 item 6 / N.8 rule: no row must not read as clear.
- Measured, 2000-2030, true tithi from Sun/Moon separation at 00:00 UT: the proxy's Rikta verdict is wrong on **35.3 %** of days against the engine's set (4/9/14/19/24/29), and 31.5 % even against its own 4/9/14 subset. The tithi number is wrong on 93 %. SS's "about 29 %" is not reproduced; the figure depends on the definition.

## 7. Open questions and unverified items

- **Q1** Row granularity: one row per junction passage (recommended; half-arcs in `detail`) or one per half-arc (the literal "six arcs", 2x rows)?
- **Q2** Option A (columns on `kala_obstruction`) or Option B (new table)?
- **Q3** Horizon: birth to 2100-01-01, or the convergence span?
- **Q4** Darshana semantics for a date-granular peak: instant at 00:00 UT, or any overlap with the UT/IST civil day? Effect on the 0.22 override.
- **Q5** `ph_pratikara`: exclude standalone windows (recommended) or mitigate per window?
- **Q6** One constant severity 0.55 per window, or graded by depth (distance to the cusp)? Acharya (CF-27).
- **Q7** Reuse `gochara_kernel.swiss_bisect` across assets, or a thin local helper?
- **Q8** L1 must export the water-sign set (or the six edge levels) publicly; `_WATER_SIGNS` is private.
- **Q9** Which instant does `compute_panchang(...).tithi` report (sunrise-local?) versus the Moon's UT instant? The Rikta detector and the Gandanta windows may use different time conventions.
- **Unverified:** (a) the production container's effective ephemeris path for the writer (see section 3: `compute_panchang` resets it, `Dockerfile` sets `SWE_EPHE_PATH=/app/ephe`); (b) the instants on SWIEPH (this run is Moshier; the 0.165 s agreement is for like-with-like); (c) two-component digest spec end-to-end; (d) 1212 retire mechanics (`retired_at` UPDATE permission); (e) PR #2835/#2836/#2826 are unmerged at base; (f) `swiss_bisect` was read, not executed, here (it raises `EphemerisBackendError` on Moshier).
