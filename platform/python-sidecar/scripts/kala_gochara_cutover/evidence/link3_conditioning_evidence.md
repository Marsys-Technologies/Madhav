# Link 3 conditioning evidence — native conditions (a), (b), (c) + ADK-0023 §4 delta reports

Date: 2026-09-28. Branch `l3/gochara-autonomous-wp0-7`. Scope: **conditioning
only** — the authority flip itself was NOT authorized and was NOT performed.
All production access in this task was **read-only** over an own
cloud-sql-proxy on `127.0.0.1:55440` (the native's proxy on 5433 was never
touched); fresh credentials were pulled from Secret Manager
(`amjis-pipeline-db-url`) immediately before each production connection.
Writes for condition (4) landed only in a **disposable** local Postgres 17
(`127.0.0.1:55435`, db `gochara_link3`) restored from a production dump.

Charts in scope: `482012f1-710e-4a25-994a-93821f5871aa` (canonical),
`1c826d5a-41cb-4450-b4dc-59d440e5f75a` (second). Production state at read time
(read-only): authority = `'3.0'` on both charts; windows 3.0 = 1830 / v1 =
38287 / 4.0 = 0; contacts `'4.0'` = 138837 / 138836 per chart.

## (a) Soak abort triggers — PRESENT in step09 checklist

`step09_soak_checklist.md` §"Abort triggers (Link 3 native condition (a)) —
IMMEDIATE reversal" declares: 24 h minimum soak window recorded in the
evidence header; the five abort triggers verbatim —

1. any integrity conjunct (a)–(k) of `ka_gochara` `integrity_check_sql` RED at
   any evaluation;
2. cockpit count ≠ `count_sql`;
3. any guard-trigger refusal not on the expected-protection list;
4. either chart has a `'4.0'` window with `window_start` before its own birth
   date (#2534 class);
5. the §3 F-02 walkthroughs (ordinary quarter; marriage 2013) show episodes
   without contacts —

each triggering **immediate** `step08_flip.py --reverse`, pre-authorized by
Link 3 condition (a), with recording in `evidence/step09_evidence.md` and
escalation to the native. No further work required.

## (b) Midnight-flooring comparison ('3.0' writer vs step06b projection) — SAME

Verdict: **SAME convention in both** — non-blocking; proceed.

Code paths compared:

- step06b (`scripts/kala_gochara_cutover/step06b_windows_projection.py`):
  `jd_of(dt) = dt.timestamp()/86400 + 2440587.5` (true Julian Day),
  `date_of_jd = date(1970,1,1) + timedelta(days=int(jd − 2440588.0))`,
  `JD_UNIX_EPOCH = 2440588.0` (line 119).
- '3.0' writer
  (`pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py:1515`
  `_jd_to_date`): identical formula `int(jd − 2440588.0)`; its peak/enter/exit
  JDs are true Swiss-Ephemeris JDs (`swe.julday` throughout,
  `services/ka_gochara_sweep/sweep.py:338`).
- `resolution_hierarchy.py:693–705` shares the 2440588.0 convention.

The writer's BIRTH_JD epoch anomaly (implied epoch 2440588.5, lines ~450–476)
affects only era-slice boundaries, **not** peak_date flooring.

Numeric proof: BOTH actual functions were imported and run over 9 real
production `'4.0'` contact instants (`kala_gochara_contacts.t_exact`) straddling
IST midnight and the 17:30 IST boundary (e.g. 2020-01-03T01:02 IST → both floor
to 2020-01-02). '3.0' date == step06b date for all 9. Floor rule in both:
UT time-of-day < 12:00 (IST < 17:30) → previous UTC date. The int()-vs-floor
asymmetry exists only before 1970-01-01 12:00 UT — out of range for all
in-scope charts (1984+).

Caveat (recorded honestly): '3.0' peak instants are not stored in
`kala_gochara_windows` (dates only), so this check is convention-level plus
instant-level, not row-level recomputation.

## (c) `era_slice_key` exposure in the retrieval layer — PASS (honest degrade)

`platform-mcp/src/tools/retrieval/register_gochara_windows.ts`:

- `era_slice_key` present in all three density contracts (lines 1496, 1507,
  1515 — the native's anchors).
- `computeWindowFacets` (lines 1650–1710) emits
  `era_slice_key: {by_key, null_count, null_semantics}`.
- Disclosure strings `ERA_SLICE_NULL_SEMANTICS_4_0` / `_LEGACY` (lines
  1640–1648) name migration 1091 conjunct (g): a non-null `era_slice_key`
  inside `'4.0'` is century-writer contamination; a null era slice is a
  contract boundary, not an absence ("no windows that decade" must not be
  inferred).

Verification:

- `npx vitest run src/tools/retrieval/register_gochara_windows_era_slice_facet.test.ts`
  → 5/5 passed.
- `npx tsc --noEmit` → clean.
- Production facet counts (read-only): generation `'3.0'` = 1830/1830 non-null
  (`g3_1984_1994` … `g3_2074_2084`); `'v1'` = 38287/38287 null; no `'4.0'`
  windows exist yet (candidate not built).

Verdict: PASS — the honest-degrade path (explicit null_semantics disclosure) is
implemented; non-blocking for conditioning.

## (4) ADK-0023 §4 — step06b §4.11 delta reports generated (both charts)

Method (production read-only; writes only on a disposable copy):

1. Fresh credentials pulled from Secret Manager immediately before each
   production connection; own cloud-sql-proxy on `127.0.0.1:55440` (the
   native's 5433 proxy never touched).
2. `step06a_class_context.py` (SELECTs only) run per chart against production
   to build the real per-class permission context
   (`l1_permission_wiring:v1` — union of `gochara_intensity.permission` over
   each class's candidate contact `t_exact` instants; DR-14 static-collapse
   disclosed in the output):
   - `.run/wp10_tranche2/link3_class_context_482012f1.json`
   - `.run/wp10_tranche2/link3_class_context_1c826d5a.json`

   Log hygiene (honest record, per PRAMĀṆIN's review): the step06a logs are
   incomplete. `.run/wp10_tranche2/link3_step06a_482012f1.log` is empty and
   `link3_step06a_1c826d5a.log` contains only a failed-attempt traceback
   (wrong-socket connect — an unquoted DSN substitution silently produced an
   empty DSN and psycopg fell back to `/tmp/.s.PGSQL.5432`). Both JSONs are
   genuine outputs, produced by an **unlogged retry** after that failure
   (the retry ran under the fixed, quoted-DSN invocation; its terminal output
   confirmed `exit=0` and the context source line above).
3. Disposable Postgres 17 (`127.0.0.1:55435`, db `gochara_link3`) restored
   from a production dump (contacts 277673; windows 40117; publication 2;
   gochara_resonance_map 1595; kala_vedha_gochara 344;
   kala_moorti_nirnaya 148; bg_vedha_malefic_scale 5; bg_transit_rules 76;
   bg_transit_moorti 27). One restore fix was needed: `kala_gochara_windows.id`
   had lost its sequence default — re-attached
   (`ALTER COLUMN id SET DEFAULT nextval(...)`, setval past max(id)).
   step06b's §12.9 overlay-freshness gate passed on the restored rows
   (house_vedha + moorti both `fresh`, fingerprints recorded in each report
   header).
4. `step06b_windows_projection.py` run per chart against the disposable DB
   with the real class context and `--delta-report-out`.

Results:

| chart | 4.0 windows (era subset) | mean raw 4.0 | baseline 3.0 read | report |
|---|---|---|---|---|
| 482012f1 (canonical) | 4417 (1435 era) | 0.5594 | 914 | `.run/wp10_tranche2/link2_delta_report_482012f1.md` |
| 1c826d5a (second) | 3945 (1263 era) | 0.5407 | 916 | `.run/wp10_tranche2/link2_delta_report_1c826d5a.md` |

Headline deltas (canonical chart): most classes show mean raw 4.0 above the
'3.0' per-class mean (e.g. business_launch +0.399, education_milestone +0.416,
career_change +0.336); career_setback is lower (−0.054). Second chart is
broadly positive but flatter (marriage +0.213, career_change +0.202). Baseline
factor cells are honest '—' (3.0 stores intensities only).

Code change this surfaced (disclosed): step06b had never been run on real
production-density data. Its projection can emit two rows with the same
`uq_kala_gochara_windows_natural_key` when peaks from adjacent components
refine (`refine_peak_to_day`) onto the same calendar day — first observed as
a UniqueViolation on `(exam_outcome, 2027-07-30, day, 4.0)`. Fix in
`write_windows` (`step06b_windows_projection.py`): natural-key dedupe, first
occurrence in insert order kept, children of a skipped row re-pointed to the
retained row's id, skip count printed to stderr.

Battery figures after the fix (two DIFFERENT scopes — do not conflate;
correction per PRAMĀṆIN's review, which caught this section originally
labelling the wider scope as "the campaign battery"):

- **Wider gochara-related selection** — `pytest tests/l3/gochara/
  tests/l3/test_s4_05_health_adverse_class.py
  services/ka_gochara_resonance/tests/ tests/test_l1_sensitive_points.py
  tests/test_ga5_writer.py tests/test_gochara_intensity.py
  tests/test_gochara_grammar.py -q` → **645 passed, 85 skipped, 0 failures**.
  This is the run quoted against the fix above; it is broader than the
  campaign battery.
- **Documented campaign battery** — `pytest tests/l3/gochara -q` at HEAD
  `47d6905d5` (377 collected): PRAMĀṆIN reproduced **359 passed, 18 skipped,
  0 failures**; my re-run in a partially torn-down environment (some
  disposable DBs already stopped) gave 297 passed, 80 skipped, 0 failures —
  the skip delta is environment-dependent (disposable-DB reachability gates
  those tests), and both runs have zero failures.

Production itself was never written: no candidate manifest, no '4.0' rows, no
authority change. The flip remains unauthorized and unperformed.
