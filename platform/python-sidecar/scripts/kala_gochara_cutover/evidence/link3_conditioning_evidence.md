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

## (b) Noon-boundary flooring comparison ('3.0' writer vs step06b projection) — SAME (historical; SUPERSEDED by E-020)

> **Wording correction (ADK-0026 §6):** this section originally said
> "midnight-flooring" / "midnight peaks floor to the prior day". That
> understated the defect: the real scope was instants **00:00–11:59 UTC
> (05:30–17:29 IST) dated one day early**. Corrected here.
>
> **Status after E-020/ADK-0026:** the native ruled this "SAME" verdict
> diagnosed a shared DEFECT, not a shared convention to keep — the '4.0'
> writer path was fixed to the true-inverse midnight-UTC convention
> (jd_of / date_of_jd / iso_date_of_jd / _jd_of_date, plus the
> CARTOGRAPHER-found second copy at legacy_semantics.py:1331,1342) and gate
> (b) was REOPENED under a falsifiable definition (see the E-020 remediation
> section below). '3.0'/v1 producers (resolution_hierarchy.py `_EPOCH_JD`,
> ka_gochara_v3_century_materialize.py) were deliberately NOT touched —
> handed to the L3 plan as a finding (E-020 §2). The comparison below is the
> historical pre-fix record.

Verdict (pre-fix): **SAME convention in both** — assessed non-blocking at the
time; the native's E-020 disposition reversed that assessment.

Code paths compared (pre-fix constants):

- step06b (`scripts/kala_gochara_cutover/step06b_windows_projection.py`):
  `jd_of(dt) = dt.timestamp()/86400 + 2440587.5` (true Julian Day),
  `date_of_jd = date(1970,1,1) + timedelta(days=int(jd − 2440588.0))`,
  `JD_UNIX_EPOCH = 2440588.0` (line 119). [All three corrected by E-020.]
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

Results (**SUPERSEDED 2026-09-28 — these numbers were computed with the
K3-F1 `RELATION_TO_PRIMITIVE` key bug, which silently excluded all 94,203
kakshya contacts per chart; the corrected re-run is in the "2026-09-28 —
ADK-0024 K3/O-2 remediation" section below; the delta-report files named
here have been regenerated in place by the corrected run**):

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

---

## 2026-09-28 — ADK-0024 K3/O-2 remediation (K3-F1 relation key, K3-F2 reversal windows cleanup)

Ruling: `00_ARCHITECTURE/autonomy/ADHIKARIN_RULINGS.md` ADK-0024; review:
`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/gochara_wp0_7/wp7_packets/K3_O2_REVIEW_PRODUCTION_APPLICATION_SET.md`.
All DB work below on a **fresh disposable** Postgres 16 container
(`gochara-link3-disposable`, `127.0.0.1:55445`, db `gochara_link3`), rebuilt
from `.run/wp10_tranche2/pre_run_dump_20260927.dump` +
`rehearsal_schema.sql` + the `kala_moorti_nirnaya`/`kala_vedha_gochara`
sections of `rehearsal_data.sql` (the dump's own overlay rows lack
`upstream_fingerprint`, so the §12.9 freshness gate refuses until the
fingerprinted rows are loaded — 148 mn / 344 kvg, matching the prior
restore's counts), plus the `kala_gochara_windows.id` sequence-default
re-attach. The '4.0' candidate was rebuilt on the disposable from the
retained enumeration payloads (`link2_episodes_*.json`,
`link2_coverage_*.json`): contacts_written **138,837** (482012f1, manifest
`969bd194-996a-4aa7-a644-9eadb6122822`) / **138,836** (1c826d5a, manifest
`c4f043b0-7314-42dc-bb78-677b1bd6dc41`) — production-exact. Production was
never touched (READ-ONLY ruling honored; no proxy was even started).

### K3-F1 — relation-vocabulary key fix, validated

- `step06b_windows_projection.py`: `RELATION_TO_PRIMITIVE` key
  `"kakshya_cell"` → `"kakshya_cell_crossing"` (the pinned WP1 §3.1/§7
  vocabulary and the value actually stored in the ledger).
- `test_step06b_windows_projection.py::test_relation_to_primitive_vocabulary`
  now pins the correct key and regression-asserts all 8 enumerator relations
  (conjunction, return, drishti_contact, sign_ingress, nakshatra_ingress,
  kakshya_cell_crossing, station_retro_loop, eclipse_degree) are map keys.
- Loud disclosure: the writer now prints a stderr WARNING whenever
  `contacts_unmapped_relation` or `contacts_unmapped_no_class` is non-zero,
  and the stdout run report gains `windows_collapsed_dupes` +
  `windows_by_tier_basis` (the reconciliation the reviewer asked for:
  `sum(windows_by_tier) = windows_written + windows_collapsed_dupes`).

**Corrected re-run (both charts, exit 0; run reports retained this time —
`.run/wp10_tranche2/link3_step06b_runreport_<chart>.json` + `.stderr`):**

| chart | contacts read | unmapped_relation | unmapped_no_class | windows written (era/month/day) | collapsed dupes | mean raw 4.0 (all / era) | baseline 3.0 |
|---|---|---|---|---|---|---|---|
| 482012f1 | 138,837 | **0** (was 94,203 = 67.9%) | 0 | 4,417 (1435/1492/1492) | 2 | 0.559520 / 0.556359 | 914 |
| 1c826d5a | 138,836 | **0** | 0 | 3,955 (1263/1346/1346) | 0 | 0.541071 / 0.537113 | 916 |

Reconciliation holds on both charts (482012f1: 1435+1492+1492 = 4419 =
4417 + 2). Both delta reports regenerated in place
(`.run/wp10_tranche2/link2_delta_report_<chart>.md`); the §4 figures above
are the superseded stale set.

**Why the numbers barely moved — verified mechanism, not an assumption:**
every kakshya contact in the '4.0' ledger is a **zero-width instant**
(`t_in = t_exact = t_out`; per-chart histogram on the disposable:
kakshya_cell_crossing 94,203/94,203 zero-width, nakshatra_ingress 29,322/29,322,
sign_ingress 13,360/13,362 — boundary relations are instants by
construction). Under M-1 `linear_no_box_decay` the contribution is 0 at every
sampled point including the instant itself (`step06b_windows_projection.py:211`
returns 0 at `t == t_in == t_out` before the `span <= 0 → 1.0` branch can
fire). The excluded 67.9% of contacts were therefore **amplitude-inert**;
the entire activity signal comes from the nonzero-width relations
(drishti_contact 1,092 / conjunction 771 / return 87). The corrected run's
small deltas (+2 pre-dedupe windows on 482012f1, +10 on 1c826d5a) come from
the added contact **breakpoints** refining the sampled series (sub-day bumps
become visible), not from new amplitude. The fix is still required and
blocking-correct: the exclusion violated the pinned served-relation
vocabulary and was invisible end-to-end; the invariance "kakshya is inert"
holds only while enumeration writes boundary contacts as zero-width spans,
and is now pinned by the battery instead of left silent.

### K3-F2 (option iii) — reversal windows cleanup, implemented + drilled

- `services/gochara_kernel/ledger.py`: new explicit op
  `clear_windows_on_reversal(conn, chart_id, generation)` — the same scoped
  statement as `EXPLICIT_CLEAR_OPS['ka_gochara']`'s windows DELETE
  (`platform/src/lib/cockpit/assetClearSpec.ts:271`), parameterized by
  generation. Hard guard refuses (`PublishedGenerationRefusal`) unless the
  manifest is `candidate`/`rolled_back` AND the generation is not the chart's
  served authority AND the generation is not `'v1'`/`'3.0'`.
- `step08_flip.py --reverse` reordered per the ruling: authority → '3.0'
  FIRST, `ledger.rollback()` (coverage+contacts), then
  `clear_windows_on_reversal` — one transaction; report gains
  `windows_deleted` and `label_burned`.
- Docs: `step09_soak_checklist.md` reversal section and
  `GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md` step-8 row rewritten (3-step
  reverse, guard, post-reversal integrity evaluation, burned-label
  semantics, per-chart half-flip rule, conjunct-(i) vacuity note).

**Reversal drill (disposable, chart 482012f1, real production-density
projection):** flip exit 0 (authority 4.0, manifest published, contacts
138,837) → `--reverse` exit 0, `windows_deleted=4417` → post-state: 4.0
windows/contacts/coverage = 0/0/0, v1 = 16,297 and 3.0 = 914 untouched,
authority '3.0', manifest `rolled_back`, chart 1c826d5a untouched (3,955
4.0 windows — per-chart half-flip rule holds) → conjuncts (a)/(f) scoped to
the reversed chart GREEN → burned label verified: re-flip attempt exits 8
(`manifest status is 'rolled_back', not 'candidate'`), authority stays '3.0'.
Conjunct (i) is vacuous for step06b's row shape (bare-string
`active_sentences` carry no `contact_id` key) — recorded here, not earned.

### Findings disclosed by the drill (pre-existing, outside K3 scope)

- **Conjunct (e) RED on the real-data projection**: 39 '4.0' rows (both
  charts, era/month/day resolutions) have `window_start = 2019-12-31`, one
  day before the manifest horizon's lower bound (2020-01-01T00:00) — the
  horizon-edge era-window flooring backs off one day. Present in the stale
  run too (same machinery); never previously evaluated against real data.
  The full 11-conjunct integrity check therefore reads `f` mid-flip on the
  disposable, and post-reversal reads `f` only while chart 2's
  (e)-violating rows remain. ADK-0024 §3's gates (b)/(c) re-verification
  must see this before Link 3 executes. Not patched here — the fix belongs
  to the window-start edge convention, not to the reversal path.
- Disposable restore loses the `kala_gochara_windows.id` sequence default
  and the dump's overlay rows lack fingerprints (both worked around as
  above); the dump also excludes the cockpit schema (`asset_registry` was
  recreated minimally and migration 1091 applied for the drill's integrity
  evaluations).

### Battery + gates after remediation

`cd platform/python-sidecar && WP6_LEDGER_DSN=postgresql://wp6:***@localhost:55443/wp6 GOCHARA_REMAINDER_DSN=postgresql://wp6:***@localhost:55444/wp6 python3 -m pytest tests/l3/gochara -q`
(fresh disposable containers `gochara-wp6-disposable` :55443,
`gochara-wp10-disposable` :55444): **378 passed, 0 failed, 0 skipped**
(up from PRAMĀṆIN's 359 passed/18 skipped at HEAD — the delta is the new
K3-F1/K3-F2 assertions plus previously-NOT_RUN DB tests now reachable).
Includes the extended `test_step08_flip_and_reverse` (post-reversal 4.0
windows = 0, v1/3.0 counts unchanged, integrity GREEN, burned label exit 8)
and the new `test_clear_windows_on_reversal_refusals` (served-authority,
published-manifest, and v1/3.0 refusals; legal candidate-path delete).

Per ADK-0024 §3: gates (b) and (c) must be re-verified against the corrected
projection and PRAMĀṆIN must re-verify the regenerated delta reports before
Link 3 executes. The flip itself remains unauthorized and unperformed.

## 2026-09-28 — E-020 disposition executed (ADK-0026; overrules ADK-0025)

Ruling: `00_ARCHITECTURE/autonomy/ADHIKARIN_RULINGS.md` ADK-0026. The
migration-1091 conjunct (e) is a **correct detector**; the 39 horizon-edge
dates (`window_start = 2019-12-31` against horizon `2020-01-01T00:00Z`) were
genuinely wrong data. Root cause: the writer's `date_of_jd` floored at the
**noon-UTC** anchor (`date(1970,1,1) + timedelta(days=int(jd − 2440588.0))`),
dating instants 00:00–11:59 UTC (05:30–17:29 IST) one day early. Fix the
data (the date convention), not the detector. All DB work on the same fresh
disposable (`gochara-link3-disposable` :55445, rebuilt as in the ADK-0024
section above, minimal `asset_registry` + migration 1091). Production
READ-ONLY throughout; migration 1150's production apply is deferred to
PRAMĀṆIN's pass (via `migrate.ts`, never `apply_migration.sh`).

### (b) Code fixes — midnight-UTC true-inverse date convention

- `step06b_windows_projection.py`: `JD_UNIX_EPOCH = 2440587.5` (was
  2440588.0); `date_of_jd` is now
  `datetime.fromtimestamp((jd − JD_UNIX_EPOCH) * 86400, tz=UTC).date()` — the
  true inverse of `jd_of` (which was already 2440587.5-based), same shape as
  `overlays.py:49-52`. `_jd_of_date` formula unchanged; with the corrected
  constant it yields midnight-UTC JDs.
- `services/gochara_kernel/legacy_semantics.py:1331,1342` (CARTOGRAPHER-found
  second copy of the convention, inside `build_resolution_hierarchy`):
  `int(peak_jd_true − 2440587.5)` / `2440587.5 + days`, with a disclosure
  comment recording the intentional divergence from
  `services/gochara_v3/resolution_hierarchy.py`'s noon convention.
- **Not touched** (recorded as L3-plan findings, E-020 §2): the '3.0'
  producer `resolution_hierarchy.py` (`_EPOCH_JD` noon anchor, :693) and
  `ka_gochara_v3_century_materialize.py`, and the v1 producers — authority
  stays '3.0'; changing them is outside this lane's grant.
- New tests (all pass):
  `test_jd_date_round_trip_true_inverses_e020` (every UTC hour across 4 dates
  incl. horizon edge JD 2458849.5 → 2020-01-01, both directions);
  `test_legacy_month_bounds_true_inverse_e020` (peak 2026-06-01 06:00Z →
  month enter at midnight June 1, not noon May 31).

### (c) Regeneration on the corrected convention (both charts, exit 0)

Instrumented harness `tests/l3/gochara/e020_gateb_harness.py` wraps the
writer's `_window_row` and logs every row whose old-convention date differs
from the corrected one to a JSONL shift ledger; the projection it writes is
identical to an uninstrumented run. Run reports:
`.run/wp10_tranche2/link3_step06b_runreport_<chart>.json`; shift ledgers:
`.run/wp10_tranche2/e020_gateb_shifts_<chart>.jsonl`; delta reports
regenerated in place (`.run/wp10_tranche2/link2_delta_report_<chart>.md`).

| chart | contacts read | unmapped (relation / no_class) | windows written (era/month/day) | collapsed dupes | peaks refined outside era | runtime |
|---|---|---|---|---|---|---|
| 482012f1 | 138,837 | 0 / 0 | **4,415** (1435/1490/1490) | 0 | 2 | ~2261 s |
| 1c826d5a | 138,836 | 0 / 0 | **3,947** (1263/1342/1342) | 0 | 5 | ~2211 s |

(Compare the ADK-0024 run: 4,417 / 3,955. The deltas are the date shifts
moving rows across dedupe keys plus the outside-era skip below.)

### Additional writer defect surfaced by gate (d) during this rehearsal

Conjunct (d) (window well-formedness) initially failed on the corrected
projection with **7 rows** (5 on 1c826d5a, 2 on 482012f1): month-tier rows
inverted (`window_end < window_start`, e.g. birth_anchor [2027-04-01,
2027-03-31]) or peak-escaped (`peak_date > window_end`, e.g. exam_outcome
[2027-07-19, 2027-07-27] peak 2027-07-31). Root cause:
`refine_peak_to_day`'s ±7-day argmax can land **outside** its own era
component (the peak belongs to the adjacent component, which emits it with
its own family); clipping that peak's calendar month against the
non-overlapping era inverts or truncates the row. Convention-independent —
reconstruction under the old noon anchor yields the identical inversions, so
this predates E-020; the earlier RED attribution pinned conjunct (e)'s 39
rows without decomposing (d). Fix (writer, `step06b_windows_projection.py`):
when the refined peak falls outside `[enter_jd, exit_jd]` of its era, skip
the month/day family and count it (`peaks_refined_outside_era` in the class
report); era rows are unaffected and no peak is lost. Pinned by
`test_refined_peak_outside_era_skips_month_day_family`. The '3.0' producer
`resolution_hierarchy.py` has the same ±7d refine + R8.6 clip shape — L3-plan
finding, untouched. After the fix: 0 malformed '4.0' rows (SQL conjunct-(d)
form).

### (d) Gate (b) — falsifiable comparison, contact level (GREEN)

Exhaustive over all **277,673** '4.0' contacts on the disposable:
new date = `(t_exact AT TIME ZONE 'UTC')::date`, old date =
`DATE '1970-01-01' + int(epoch/86400 + 2440587.5 − 2440588.0)`.
Shift distribution: **0: 137,464; +1: 140,209** — no other values.
Violations (shift ∉ {0,+1}): **0**. +1-shifts with UTC time-of-day ≥ 12:00:
**0**; 0-shifts with time-of-day < 12:00: **0**. Shifted per chart: 70,102
(482012f1) / 70,107 (1c826d5a). Shifted by relation: kakshya 96,444 /
nakshatra_ingress 28,620 / sign_ingress 13,237 / drishti 1,044 /
conjunction 771 / return 93.

### (d) Gate (b) — window level, from the shift ledgers (GREEN)

Every ledger record has `shift_days == 1` and `0 ≤ time_of_day < 12h`, with
exactly two records (482012f1, era `window_end`, jd 2462244.9999999925)
whose ledger field reads 12.0 — the ledger stores `round(hours, 6)`; direct
computation gives 2029-04-18 **11:59:59.999356 UTC**, inside the morning
scope. Shifted field-records per chart per tier:

| chart | era (start/end/peak) | month (start/end/peak) | day (start/end/peak) | total |
|---|---|---|---|---|
| 482012f1 | 700/728/683 | 989/1037/704 | 704/704/704 | 6,953 |
| 1c826d5a | 648/626/634 | 923/940/665 | 665/665/665 | 6,431 |

### The 39 horizon-edge rows — disposition

Zero '4.0' rows with `window_start < 2020-01-01` (SQL, both charts). The
corrected projection dates the former violators **2020-01-01**; they remain
in the projection. SQL count of rows starting exactly 2020-01-01: 482012f1 —
12 era + 7 month; 1c826d5a — 13 era + 11 month + 7 day — an **exact** match
with the shift ledgers' horizon records (50 total). The 39 was the
conjunct-(e) RED count on the earlier production-candidate projection, whose
dedupe/collapse differed from this run; the current boundary set reconciles
row-for-row between the independent instrumentation ledger and SQL.

### (e) Migration 1150 — conjunct (e) amended to UTC date-compare

`platform/migrations/1150_wp10_ka_gochara_conjunct_e_utc_date_compare.sql`:
UPDATE of `asset_registry.integrity_check_sql` for `ka_gochara`; only
conjunct (e) changes — `w.window_start < (lower(m.horizon) AT TIME ZONE
'UTC')::date OR w.window_end > (upper(m.horizon) AT TIME ZONE 'UTC')::date`.
The horizon is half-open `[lower, upper)`: a window dated `date(upper)` is
the clipped boundary day, not an undisclosed claim, hence strict `>` on the
upper comparison (the timezone-correct form of the original semantics).
Gate-probe DO block asserts the new form present, the old `::timestamptz`
casts gone (checked against the SQL with `--` comments stripped — the amended
conjunct's own comment names the old cast as prose), and the flanking
conjuncts intact. `npm run guard:migration-numbers` PASS; number verified
free across all 1,087 origin refs in both migration dirs.
Triple (via `migrate.ts`'s own `sqlIdentityOf`):
filename `1150_wp10_ka_gochara_conjunct_e_utc_date_compare.sql`,
sha256 `c64c89b1dcadb9d56c050b33a068a515b74d5c176d1aa9d54c84d253d3c05709`,
sql_identity `bd2e61f5611e586772ce84d3affef590429f234f777ec61633412e48d4c9b64c`.

**Dual-timezone rehearsal on the disposable** (1150 applied: UPDATE 1 + DO
clean; stored text evaluated as-is):

| TimeZone | conjunct (e) OLD (1091 form) | conjunct (e) NEW (1150 form) | full (a)–(k) OLD | full (a)–(k) NEW |
|---|---|---|---|---|
| UTC | t | t | t | **t** |
| Asia/Kolkata | **f** | t | **f** | **t** |

The old form's verdict depended on the session timezone (Asia/Kolkata shifts
the window date's midnight by −05:30, re-dating morning windows and pushing
the 50 horizon rows below the horizon) — exactly the defect ADK-0026 records.
The amended detector is timezone-independent and GREEN on the corrected
projection. Detector version: before = migration 1091 text; after = migration
1150 text (rehearsal only — no production apply).

### Battery

`pytest tests/l3/gochara -q` with the WP6/remainder DSNs on the disposable
containers: **381 passed, 0 failed, 0 skipped** (378 prior + 3 new E-020
tests).

### What remains before Link 3

PRAMĀṆIN re-verification of the amended detector (1150) and its production
apply via `migrate.ts`, re-run of PRAMĀṆIN's pass on the regenerated
projection, and K3/O-2 re-review under condition (d). The flip remains
unauthorized and unperformed.

## 2026-09-28 — Migration 1150 PRODUCTION APPLY (E-020 (e) closure; PRODUCTION_MIGRATION_AUTHORIZED, PRAMĀṆIN-passed)

Authorization: native's `PRODUCTION_MIGRATION_AUTHORIZED` for migration 1150
only, unconditional-on-this-side after the GREEN/GREEN dual-timezone
disposable rehearsal and PRAMĀṆIN's full re-derivation pass (old conjunct
text RED under Asia/Kolkata, new text GREEN under both, triple recomputed and
matching, number 1150 free across all refs).

**Access discipline:** own cloud-sql-proxy on `127.0.0.1:55440`
(`madhav-astrology:asia-south1:amjis-postgres`, ADC; the listener was
started for this apply and killed afterwards — port confirmed closed); fresh
`amjis-pipeline-db-url` credentials fetched from Secret Manager immediately
before EACH connection (rotation happened — no cached string used), host:port
rewritten to the proxy and the `host=` query parameter stripped (it points at
the cloudsql socket dir); the native's 5433 session never touched.

**Apply mechanism:** `migrate.ts` cannot restrict itself to a single file
here — `--only 1150…` would jump the known unapplied predecessors
1071/1072/1086 and the runner refuses by design (`--only would jump
unapplied predecessor migration(s)`), and 1071/1072/1086 must NOT be
touched. Per the authorization's fallback clause the file was applied with
its `_migrations_applied` row recorded **in the same transaction**:

```
BEGIN;
  <1150 file contents>            → UPDATE 1; DO (gate probe PASS)
  INSERT INTO _migrations_applied (filename, sha256, sql_identity)
    VALUES ('1150_wp10_ka_gochara_conjunct_e_utc_date_compare.sql',
            'c64c89b1dcadb9d56c050b33a068a515b74d5c176d1aa9d54c84d253d3c05709',
            'bd2e61f5611e586772ce84d3affef590429f234f777ec61633412e48d4c9b64c');
COMMIT;
```

Triple recomputed immediately before applying via `migrate.ts`'s own
`sqlIdentityOf` + sha256 over the on-disk file: **both MATCH** the authorized
values. psql output: `BEGIN / UPDATE 1 / DO / INSERT 0 1 / COMMIT`
(`ON_ERROR_STOP=1`; any failure would have rolled back before COMMIT).

**Pre-state (read-only, verified immediately before):** authority `3.0` on
both charts; windows v1=38,287 / 3.0=1,830 / zero '4.0'; registry held the
1091 conjunct-(e) text (`window_start::timestamptz` present, UTC date-compare
absent); two '4.0' candidate manifests; no 1150 ledger row; production
default TimeZone = UTC.

**Post-verify:**
- Ledger row present: id 885,
  `1150_wp10_ka_gochara_conjunct_e_utc_date_compare.sql`, applied_at
  2026-09-28 16:20:33 UTC, sha256/sql_identity exactly as above.
- `npx tsx scripts/migrate.ts --dry-run` against production (fresh creds):
  `Dry run — would apply: 1071_kala_gochara_windows_generation_guard.sql,
  1072_kala_b1_registry_truth_and_sweep_protection.sql,
  1086_nirmana_l1_gochara_g10_ga_strength_contributor_digest_spec.sql` —
  **1150 NOT pending**; the three known pendings untouched. (Two non-fatal
  `[migration-hash-disclosure]` warnings for ws2_l0 files are pre-existing
  Dvārapāla RULING 73 disclosed residuals, unrelated to this apply.)
- Registry text now carries the UTC date-compare form (the one remaining
  `::timestamptz` occurrence is the prose mention inside the amended
  conjunct's own comment — same as rehearsal).
- **Full (a)–(k) integrity check against production with the NEW registry
  text: GREEN under the session default timezone (UTC) AND under
  `SET TimeZone='Asia/Kolkata'`** — both `t`. Conjunct (e) alone: `t` under
  both (vacuously true at present — zero '4.0' windows in production — and
  now timezone-independent). No conjunct regressed: the stored check is the
  conjunction of (a)–(k), and it evaluates `t`.

**Scope honored:** this ONE migration only; no other production write of any
kind. Proxy torn down after the checks; helper script and temp files removed.
