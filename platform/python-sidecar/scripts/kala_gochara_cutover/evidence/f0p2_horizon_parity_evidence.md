# F-0 PRECONDITION 2 — horizon parity ('4.1' full-horizon rebuild) — running evidence

Governing: ADK-0027 (native directive F-0), `00_ARCHITECTURE/autonomy/ADHIKARIN_RULINGS.md`.
Executor lane: `l3/gochara-autonomous-wp0-7` @ merge commit `f95cf19af`
(origin/main merged in, PRAMĀṆIN-verified, pushed).
New generation label: **`'4.1'`** — `'4.0'` is burned for chart 482012f1
(rolled_back, zero rows) and superseded for chart 1c826d5a (narrow-horizon
candidate, to be cleared via the candidate-scoped clear machinery).
This file is appended as the work proceeds (checkpoint-per-step).

## Step 0 — exception check (2026-09-29): NO NARROWING RULING FOUND → default governs

Surfaces searched for any native ruling that deliberately narrowed the
candidate horizon to `[2020-01-01, 2030-01-01)`:

- `00_ARCHITECTURE/autonomy/ADHIKARIN_RULINGS.md` (full register; ADK-0027
  F-0 text itself — its exception clause requires citing a prior ruling;
  none is cited there or anywhere else in the register). ADK-0025/0026
  discuss the horizon *edge* (2019-12-31 flooring defect), never a narrowing.
- `ESCALATIONS.md` (all "horizon"/"2020"/"2030" hits: H-3 honest
  requested-vs-completed horizon reporting, and the E-020 conjunct-(e) arc —
  no narrowing ruling).
- `GOCHARA_NATIVE_RULINGS_2026-09-24_v1_0.md` (the 2026-09-24 tranche
  authorizations — no horizon narrowing; only orb-narrowing discussion for
  M-1, a different axis).
- `GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md`, `REMAINDER_FINAL_REPORT_v1_0.md`,
  `GOCHARA_FAMILY_ELEVATION_PLAN_v2_0/v2_1.md` — these carry the OPPOSITE
  standing doctrine: "no cap, coarser grid or **narrower horizon** is a
  speedup / can ever pass as an equivalent optimisation" (plan §4.5,
  Strategy §5; Kimi packets). The `[2020, 2030)` decade was the lane's own
  candidate-1 rehearsal parameter, never a native narrowing.

**Verdict: no exception. DEFAULT governs — full-'3.0'-horizon candidate
rebuild for both charts under label `'4.1'`.**

## Step 1 — '3.0' horizon bounds + production pre-state (2026-09-29, read-only)

Access: own cloud-sql-proxy `127.0.0.1:55440` (instance
`madhav-astrology:asia-south1:amjis-postgres`); the native's 5433 never
touched; fresh `amjis-pipeline-db-url` pulled from Secret Manager immediately
before the connection; role `amjis_app`; read-only queries only.

- **`'3.0'` served horizon (both charts): window rows span
  `1984-02-05 .. 2084-01-31`** — the century materialization anchored at
  birth 1984-02-05 (chart 482012f1: 914 rows; chart 1c826d5a: 916 rows).
  Parity horizon for `'4.1'` enumeration: **[1984-02-05T00:00Z, 2084-02-05T00:00Z)**
  (birth → birth+100y; the served max window_end 2084-01-31 is the last era
  band's clip inside that century).
- v1 protected history untouched (482012f1: 16,297 rows; 1c826d5a: 19,323;
  third archived chart cb73cd3d: 2,667 — out of scope, not a campaign chart).
- `kala_gochara_authority`: `'3.0'` on both charts. ✓ (post-reversal state)
- `kala_gochara_publication`: chart 1 manifest `d54d899b…` **rolled_back**
  (label burned); chart 2 manifest `4dc6c74c-4efa-4dc7-86ff-d31b1b038359`
  **candidate**, horizon `["2020-01-01","2030-01-01")`.
- Chart-2 `'4.0'` rows in production: **contacts 138,836 · coverage 48 ·
  windows 0** (step06b never ran for chart 2 in production). Chart 1: zero
  `'4.0'` rows anywhere.
- `_migrations_applied`: 1080–1084, 1087, 1091 (2026-09-24), 1120–1123,
  1124, 1125, **1150** (2026-09-28, conjunct-(e) UTC date-compare fix)
  applied. The production registry text for `ka_gochara.integrity_check_sql`
  is therefore the post-1150 corrected conjunct set.

## Step 2 — rehearsal DB + smoke + chart-2 clear rehearsal (2026-09-29)

**Rehearsal DB:** fresh disposable pg16 container `gochara-f0p2-rehearsal`
(`127.0.0.1:55436`, db `gochara_f0p2`, user wp6/disposable), rebuilt per the
documented Link-3 recipe: `pre_run_dump_20260927.dump`
(`pg_restore --no-owner --no-privileges`; 3 ignorable errors, all
`kala_gochara_generation_guard()` trigger creations — guard function outside
the dumped table set, as in step02's drill) + `rehearsal_schema.sql`
(mn/kvg "already exists" errors ignored — dump carries those tables) +
`rehearsal_reference_signs.sql` + `rehearsal_chart_facts.csv`
(`\copy` 283,016 rows) + overlay data sections with fingerprints
(`kala_moorti_nirnaya` TRUNCATE+reload = **148** rows,
`kala_vedha_gochara` = **344** rows — both match the documented counts) +
remaining data sections (`gochara_resonance_map` 1,595 rows, `bg_transit_rules`
76, `bg_transit_moorti` 32, `bg_vedha_malefic_scale` 10, `ga_yoga_firings` 202;
`bg_transit_rules` truncate required CASCADE-order note: truncated together
with `gochara_resonance_map` on retry) + `kala_gochara_windows_id_seq`
default re-attach (already present; setval 61,709) + minimal `asset_registry`
(pre-repin ka_gochara row) + **migration 1091 then 1150 applied**
(1150's UTC date-compare present in the live registry text — verified
`integrity_check_sql LIKE '%AT TIME ZONE ''UTC''%' = t`).

**Sanity vs production-equivalent:** windows 3.0 = 914 / 916, v1 = 16,297 /
19,323 (+2,667 archived chart); contacts 0. Matches the dump's verified
digests (v1/'3.0' unchanged since 2026-09-27 per step06/step09 evidence).

**Plumbing smoke (label '4.1', 1-year slice 2020-01-01→2021-01-01, chart
482012f1):** exit 0, 194 s, 13,220 post-dedupe contacts, refine ON, swieph
backend all bodies (retflag 65602). Extrapolated century compute ≈
100 × 194 s ≈ 5.4 h/chart — consistent with the "~10x" estimate.

**Chart-2 '4.0' clear rehearsal (production-shape):** rebuilt chart
1c826d5a's '4.0' candidate on the disposable from the retained production
payloads (`link2_episodes_1c826d5a.json` + `link2_coverage_1c826d5a.json`;
overlay fingerprints b78cd26f…/6b4ee79a…/6d3c0d58…, vedha/moorti freshness
FRESH), then ran the candidate-scoped clear
`gochara_kernel.ledger.clear_generation(conn, chart, '4.0')` (the C-1
EXPLICIT_CLEAR_OPS path: coverage then contacts, manifest marked, guard
refusals intact for published/v1/3.0):
**pre contacts 138,836 / coverage 48 → post 0 / 0; manifest
14898c60-c582-4def-9b51-9b4e578210a7 (disposable-local id) → rolled_back.**
GREEN. This is the exact operation queued for production chart 2 before the
'4.1' build (production manifest is `4dc6c74c-…`, status candidate).

**Century enumerations launched (both charts, parallel, background):**
`step06_enumerate_episodes.py --generation 4.1
--horizon-start 1984-02-05T00:00:00+00:00 --horizon-end 2084-02-05T00:00:00+00:00`
(refine ON, orb 5.0°, ephe `.run/se1`), payloads →
`.run/wp10_tranche2/f0p2_episodes_<chart>.json` / `f0p2_coverage_<chart>.json`,
logs `f0p2_enum_<chart>.log/.stderr`. Expected ~5–6 h each.

## Interruption + relaunch (2026-09-29, honest record)

The first century-enenumeration pair (tasks launched ~51 min earlier, both
workers verified healthy at ~99% CPU) was **terminated externally** when the
user manually interrupted a foreground wait — both processes exited with
code −1 and empty stderr simultaneously, and the disposable container
`gochara-f0p2-rehearsal` was removed from the machine in the same window
(the own proxy on 55440 was also stopped). No payload files were written
(the enumerator writes outputs only at completion); no partial DB state —
enumeration is read-only against the DB. Nothing was lost except compute
time; no production surface was involved at any point.

Recovery: the rehearsal DB rebuild is now scripted (`.run/f0p2_rebuild_rehearsal.sh`,
idempotent, 19 s — counts re-verified: rm 1,595 / mn 148 / kvg 344 / facts
283,016 / '3.0' windows 1,830) and both century enumerations were relaunched
fresh (same commands, same label '4.1', same horizon). The chart-2 '4.0'
clear rehearsal was consumed by the container loss and will be re-run after
rebuild if needed for the record (it is GREEN on record above; the
production-queued operation is unchanged).
