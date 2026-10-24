---
artifact: DESIGN_L0_MEAN_NODE_SERIES
version: "1.2"
status: "APPROVED by SS (N-68, c7883547f) with decisions (a)-(d); v1.1 adds reader ownership, the N-69 hazards and the decisions; v1.2 (2026-10-02) corrects the digest counts measured in step 1 and records the step-1 follow-ups (section 12); the frontmatter does not mark the file write-once, so it is versioned in place like v1.1"
produced_by: Exec Suvarṇa
produced_on: 2026-10-02
ruling: "SS N-68 (house convention stays MEAN node, N-57; L0 gains a MEAN Rahu/Ketu series alongside the labelled TRUE one) + N-68 design constraints (same table and grain; binding rollout order)"
scope: "design only. Evidence: scratchpad/census files copied to /Users/Dev/suvarna-evidence/NodeSeries/ (census_ephemeris_nodes.md, rahu_cmp.py, rahu_series.txt, golden_mean_node.txt)"
---

# L0 mean-node series for `ephemeris_daily` (design REVIEW)

## 0. Finding (first-class L0 item; paste into the L0 sheet)

**Documented deviation from the house standard, measured.** `ephemeris_daily` (asset `bg_ephemeris`, L0) stores the TRUE node for Rahu and Ketu
(`swe_id 11 = SE_TRUE_NODE`; Ketu = TRUE Rahu + 180°; `node_mode='true'`, `epoch_convention='noon_ut'`, `ayanamsha_id='tropical'`; 91,676 rows per
body, 1900-01-01..2150-12-31; `brahmagyan/l0_ephemeris.py:8-15,65-67,96-97,306-314`). The house convention is MEAN node (N-57), and the gochara
kernel pins MEAN (`services/gochara_kernel/knots.py:37-48`). The two disagree by up to 0.73° (2026-11-18..30, Lahiri sidereal level 300°) and the
sidereal-300° crossing differs by about 10.25 days (TRUE JD 2461370.25, MEAN JD 2461380.5), which is what made `ka_moorti_nirnaya` raise
"Rahu: separation root at 300.0000° lost its bracket" (run b5f5e32d, 2026-10-01). The stored series is exactly SE_TRUE_NODE (0.0000 difference on all
14 sampled dates against real Swiss .se1). Ruling: fix at the source by ADDING a MEAN series, keeping TRUE as the named variant, and requiring every reader to
pin `node_mode`. Result (R): provisional until J1, by name "node convention in L0 ephemeris".

## 1. Shape

Same table, same grain. New rows differ from the existing Rahu/Ketu rows only by `node_mode='mean'`; `epoch_convention='noon_ut'`, `ayanamsha_id='tropical'`,
coverage 1900-01-01..2150-12-31, Ketu = mean Rahu + 180° (lat 0, speed = −Rahu speed, same as the TRUE rows). Existing TRUE rows are not touched. Rows added:
2 bodies × 91,676 = **183,352** (825,084 → 1,008,436; per-date rows 9 → 11).

Golden values (real Swiss .se1, swe 2.10.03, noon UT, tropical; `golden_mean_node.txt`):

| date | JD | mean Rahu lon | mean speed | TRUE Rahu lon (stored) | mean Ketu |
|---|---|---|---|---|---|
| 1900-01-01 | 2415021.0 | 259.13485378 | −0.05290797 | 260.25843484 | 79.13485378 |
| 1984-02-05 | 2445736.0 | 72.64887788 | −0.05298150 | 73.62905799 | 252.64887788 |
| 2000-01-01 | 2451545.0 | 125.04064606 | −0.05295180 | 123.95402284 | 305.04064606 |
| 2026-11-17 | 2461362.0 | 325.19987627 | −0.05296077 | 325.14425619 | 145.19987627 |
| 2026-11-25 | 2461370.0 | 324.77625055 | −0.05289796 | 324.23721510 | 144.77625055 |
| 2026-11-30 | 2461375.0 | 324.51167110 | −0.05295698 | 323.85552650 | 144.51167110 |
| 2150-12-31 | 2506696.0 | 84.59133269 | −0.05291705 | 85.47074076 | 264.59133269 |

The MEAN node is analytic: Moshier and file-backed Swiss agree to ≤ 6e-8° (1900) and exactly elsewhere, so the mean rows do not depend on the .se1 corpus.

## 2. Table key (the blocker)

Live: only `ephemeris_daily_date_body_ayanamsha_id_key UNIQUE (date, body, ayanamsha_id)` (a constraint) plus `ephemeris_daily_pkey (id)`; `node_mode` is under
`CHECK (node_mode IS NULL OR node_mode IN ('true','mean'))` and is NOT in any key (read from `pg_constraint`/`pg_indexes`, 2026-10-02). A mean row for the same
(date,'Rahu','tropical') violates it. `node_mode` is NULL for the 7 non-node bodies, so a plain 4-column UNIQUE would not dedupe them.

**Proposed key:** `UNIQUE INDEX ... ON ephemeris_daily (date, body, ayanamsha_id, node_mode) NULLS NOT DISTINCT` (PostgreSQL 15.18 live supports it; engine measurements
record `PostgreSQL 15.18 on x86_64-pc-linux-gnu`). Four steps, in this order (the order is what keeps every writer working at every moment):
1. ADD the new unique index (additive; the old constraint stays; the new key is a superset, so no row can violate it). Owner is `amjis_app`.
2. Deploy writers whose conflict target is `(date, body, ayanamsha_id, node_mode)` (they work while both keys exist).
3. At release (step 2 of the rollout in §6): DROP the old constraint, then insert the mean rows.
4. Old-key writers do not remain: the only `ON CONFLICT (date, body, ayanamsha_id)` targets are `l0_ephemeris.py:547` and `bg_ephemeris.py:133` (census).
Route: owner-path D6 plan (hash as REVIEW) for the DDL, as for the chart_divisionals incident; the schema-of-record migration (numbers: see section 10(c)) follows
once the owner's migration hold lifts. I will not create migration files before that.

## 3. Writer change

- NEW module `brahmagyan/l0_ephemeris_mean_node.py` (not an edit of `l0_ephemeris.py`, see §5): `compute_mean_node_rows(d, swe, ephe_path)` returning the Rahu/Ketu mean rows
  (`swe.calc_ut(jd, swe.MEAN_NODE, FLG_SWIEPH|FLG_SPEED)`; same flags as the TRUE rows; Ketu = (lon+180) mod 360; lat 0; speed negated; `node_mode='mean'`).
- `pipeline/orchestrator/writers/bg_ephemeris.py`: the INSERT lists `node_mode` and `epoch_convention` for every row (today :126-130 omits both, so a fresh
  orchestrator-built row gets NULL `node_mode` even for TRUE rows: a latent defect this fixes); conflict target = the new key; mean rows are produced by the new module.
  A mean row can no longer overwrite a TRUE row because `node_mode` is in the key.
- Idempotency: L0 standard (`ON CONFLICT ... DO UPDATE ... WHERE ROW(...) IS DISTINCT FROM ROW(...)`), already-exact rows are untouched, so the existing 825,084 are NOT
  rewritten: a rebuild only inserts the 183,352 new rows. Acceptance check in the run: digest of `node_mode IS DISTINCT FROM 'mean'` rows identical before and after.
- Cost: not measured. Compute is 91,676 `calc_ut` calls for the new series plus the unchanged TRUE/other pass; inserts 183,352. Risk to settle by a rehearsal on a disposable PostgreSQL 15
  with the real .se1 corpus before any production run: bg_ephemeris is a light `run()` writer and the cockpit watchdog reaps a `building` asset after 15 minutes with only
  sub-steps heartbeating (R-25), so if the pass exceeds ~10 minutes it must become `plan_substeps` (per-decade; allowed by the frozen contract). Past production runs of this asset
  recorded 0 s (no-delta converge), so they give no timing.
- Linux/x86_64: `bg_sky_calendar` and `bg_cohort` hard-guard Linux/x86_64 for reproducibility (`bg_sky_calendar.py:129,261-272`; `bg_cohort.py:211`); `bg_ephemeris` has no such guard today. Mean-node values
  are analytic and platform-stable to ≥ 1e-7°, but I propose the production rows are written only by the production job (Linux/x86_64), never by a local backfill, and the golden test
  tolerance is 1e-7°.

## 4. Integrity conjunct (new contract replaces migration 606's)

Migration 606's `ephemeris_check` (applied; must not be edited) requires `COUNT(*) = 825084` and `NOT EXISTS (... GROUP BY date HAVING COUNT(*) <> 9 ...)`, run by `asset_runner.py:951-966`.
It goes RED on the first mean row. Live registry row: `target_floor 825084`, `rebuild_on_probe_fail = f` (so a red probe does not auto-regenerate; it just reads red). A NEW registry update
replaces `integrity_check_sql`/`target_floor` with: total 1,008,436; dates 1900-01-01..2150-12-31; 11 distinct (body,node_mode) pairs; per date exactly 11 rows; for each of Rahu and Ketu
exactly one `true` and one `mean` row per date (no NULL node_mode on Rahu/Ketu); the 7 other bodies exactly one row per date with `node_mode IS NULL`; Ketu mean = (Rahu mean + 180) mod 360 to 1e-9.
The registry update lands in the same D6 transaction as the old-constraint drop or immediately before the rebuild, so the probe is never red while data and contract disagree (and
`count_sql` stays `SELECT count(*) FROM ephemeris_daily`, so `Count.floor` delta becomes +183,352 until the floor is re-set to the achieved count, per the floors-are-aspirational rule).
The output-digest spec (migration 600 line 14) keys on `(date, body, ayanamsha_id)` and omits `node_mode`: two Rahu rows tie in its ORDER BY, so the digest becomes nondeterministic.
Specs are append-only, so a NEW spec row adds `node_mode` to the key/value columns and the registry is repointed (where `bg_ephemeris` links its spec was not traced; the live `asset_registry` has no
`output_digest_spec_sha256` column).

## 5. Digest / pin impact (measured, not guessed)

I ran the real digest generator (`pipeline.orchestrator.provenance_inventory`) in a scratch checkout at 2992093bc after appending one comment line:

| file edited | writer digests that move |
|---|---|
| `brahmagyan/l0_ephemeris.py` | **49** (v1.2 correction; v1.0/1.1 said 48, measured at 2992093bc): L0 5 (bg_cohort, bg_ephemeris, bg_gochara_arcs, bg_muhurta_lattice, bg_sky_calendar), L1 13 (all ga_*), L2 23 (bo_*), L3 **8** (ka_gochara, ka_gochara_v4_41_candidate, ka_graha_sancara, ka_kota_chakra, ka_moorti_nirnaya, ka_sudarshana_varsha, ka_vedha_gochara, ka_vighnakara; the eighth, ka_gochara_v4_41_candidate, is a writer added on main after 2992093bc); probe digest unchanged. Re-measured 2026-10-02 on main 936c4cd0c + the step-1 stack |
| `pipeline/orchestrator/writers/bg_ephemeris.py` | **1**: bg_ephemeris |
| `brahmagyan/ephemeris_routes.py` | **0** (v1.2 correction; v1.0/1.1 said 1: bg_ephemeris). Re-measured 2026-10-02: no writer digest moves when this file is edited, so step 1 moves no L0 digest and the same-PR L0 re-pin of decision (b) is not needed for the step-1 route changes |

Consequences, stated plainly:
- ANY change that touches only bg_ephemeris moves the L0 inventory (`bg_*`) and goes RED: `platform/src/generated/__tests__/nirmana-l0-analysis-receipts.test.ts` ("keeps the pinned writer-inventory digest in
  sync", `NIRMANA_L0_WRITER_INVENTORY_SHA256` in `nirmana_analysis_layer_pins.py` `L0_FROZEN_PINS`), and `NIRMANA_L0_ANALYSIS_RECEIPTS_AVAILABLE` would read false (`BLOCKS_CURRENT_ASSET` for all 40
  L0 assets: CAMPAIGN_STATE records exactly this failure mode, PR #1685). bg_ephemeris's already-accepted analysis receipt (bound to its old writer digest) no longer matches: it needs a fresh acceptance.
  No readmission shortcut is proposed. The only lawful routes are (a) leave the digest honest and let the gate read red until a separately ratified transparent re-pin lands (the D-NATIVE-06 / issue
  #2122 precedent re-derived the pin and verified that exactly the changed writer moved), or (b) the same PR carries that transparent re-pin. Which one is your/the native's call; I recommend (b) with the
  verification line "exactly one L0 digest moved, the other 39 byte-identical", shipped in the same PR so CI is green only because the pin is true.
- Nothing in the production run path reads the Nirmāṇa frozen definitions (N-51), so no build is blocked by a red pin; the cost is CI and the analysis-acceptance path.
- **Design rule that follows from the table:** mean-node logic must NOT be added to `brahmagyan/l0_ephemeris.py`. An edit there moves 49 digests across L0-L3 (v1.2: 48 in v1.0/1.1) and turns the L1, L2 and L3 layer
  pins red while S-L1 is about to launch. Hence the new module in §3. The six node-unsafe query functions that DO live in `l0_ephemeris.py` (S1-S6 in the census) are the one place the pin
  forces an edit there: see §6, options A and B. I recommend B.

## 6. Rollout (your binding order) and reader changes

Census: `census_ephemeris_nodes.md` (94 code files, 40 reader entries). Summary by owner (full file:line in the census; the Pravāha family part was sent separately):

**Step 0 (invisible):** add the new unique index (§2 step 1) via D6; add the reader-pin lint (below).
**Step 1 (behaviour-neutral, deployed before any mean row exists):** every reader pins `node_mode` with a NULL-safe predicate, `(body NOT IN ('Rahu','Ketu') OR node_mode = 'true')`, or a `node` parameter.
Ours (Suvarṇa/L0 and served tools): S1 `query_planet_position`, S2 `query_planet_transit`, S3 `query_aspects_at_time` (double counting and a Rahu-vs-Rahu "conjunction" if unpinned), S4 `query_retrograde_periods`,
S6 `query_ephemeris`, S9 `/all_bodies_range` (cap shrinks 1,111 to ~909 days; TS page cap 3,285 cannot cover a year at 4,026 rows/year), S5/S7/S10/S11 counts (floor semantics, hard-coded `expected_rows`),
S17 integrity probe, T1/T2 TS descriptions/caps, T7 UI copy ("rebuilt with MEAN_NODE Rahu" is false today). Also output `node_mode` in the served rows so callers can tell the two apart.
L1: none (no `ga_*` writer or L1 service reads the table; `get_positions.ts` reads `chart_facts`, already mean; `get_graha_yuddha.ts` reads only Mars/Mercury/Jupiter/Venus/Saturn; `get_av_transit_gating.ts` reaches the nodes only through a
free-text `planet`). So this does not touch S-L1.
Pravāha's (we do not edit; list handed over): P1-P3 fail LOUD (duplicate knots), P4-P8, P14, P15 fail SILENT (P7 retrograde union over-fires the `retrograde_malefic` stamp; P8 last-row-wins and shares PATH-B TRUE).
**Step 2 (your release, after Pravāha confirms their readers are pinned and deployed):** D6 drops the old constraint, the registry integrity contract + new digest spec land, the production job rebuilds
`bg_ephemeris` (adds 183,352 rows). Verify: counts 1,008,436 / 11 per date; digest of all non-mean rows identical before and after; golden values (§1) to 1e-7°; the new integrity conjunct passes.
**Step 3:** readers switch to `'mean'` where the convention requires, one at a time, each with an attribution note: Pravāha's kernel-coherent set (P4-P7, P1/P2 with `ARC_ENGINE_VERSION` or `SUBSTRATE_VERSION` bumped,
because `arc_fingerprint` ignores `node_mode` and `ka_gochara`'s delta-aware skip would otherwise keep TRUE-derived rows; their upstream fingerprints deliberately exclude `ephemeris_daily` too), P8 only together with PATH-B
(`compute_transits.py:54,63`, `transit_search.py:10,64`, both TRUE) so the engine's two paths do not split.

**Reader edit in `l0_ephemeris.py` (S1-S6): two options.**
- A. Edit `l0_ephemeris.py` directly. Honest and simple; moves 48 digests (L0-L3) and turns the L0, L1, L2, L3 layer pins red until re-pinned.
- B (recommended). Put the pinned query functions in a new module `brahmagyan/l0_ephemeris_queries.py` and point `ephemeris_routes.py` at them; leave the old functions in `l0_ephemeris.py` untouched but marked
  deprecated and covered by the new lint's known-open ratchet. Moves 0 digests when only `ephemeris_routes.py` is re-pointed (v1.2 measurement; v1.0/1.1 said 1, bg_ephemeris); nothing in L1-L3. Cost: a legacy unpinned copy stays until a later cleanup, which is exactly the "label/order variant" residue the known_open_readers ratchet exists to track.

## 7. Tests and the lint

- Lint (the §N.7 item 2 discipline, same shape as `check_fact_category_pinning.py` with a `known_open_readers` ratchet): any SQL text selecting from or joining `ephemeris_daily` (py, ts, sql) must contain a `node_mode` predicate or
  carry an explicit `# node-agnostic: <body list without Rahu/Ketu>` marker; a reader that does not pin fails CI; the known-open set starts as the census list and may only shrink.
- Golden tests: the §1 dates for the writer (mean Rahu/Ketu, Ketu = Rahu + 180, speeds, `node_mode`, `epoch_convention`), a duplicate-date regression for `w2g/db_source` and W2G V2/V4, and `test_bg_ephemeris_writer.py:98-120`
  (asserts the exact upsert text) updated to the new target. `tests/test_l0_ephemeris.py` pins (9 bodies, `NODE_MODE=='true'`, swe_id 11) stay valid because the TRUE constants are unchanged; add the MEAN constants alongside.
- Pravāha's `test_wp9_*` fixtures have no `node_mode` column and key on (date, body, ayanamsha_id): they need the column and seeded Rahu/Ketu `node_mode` once their readers pin (their lane).
- Integrity: a node-aware healthy fixture for the new contract (`platform/tests/unit/migrations/nirmana_l0_wave0_integrity_contracts.test.ts` currently builds 9 bodies × 91,676 dates without `node_mode`).
- Census (`census_L0.json`) `Count.floor` delta becomes +183,352 until the floor is re-set to the achieved count; `Vocab.identity` reads the new declared key from `pg_constraint`/index at run time.

## 8. What I need from SS

1. Decide A or B for the S1-S6 reader edit (recommend B).
2. Decide how the L0 pin moves (recommend the same-PR transparent re-pin, with the one-digest-moved verification line, ratified by the native).
3. Allocate migration numbers for the schema-of-record (index add, constraint drop, integrity contract replacement, output-digest spec) so the follow-up files exist once the owner's hold lifts; the live changes go by D6 plans, each with its own hash REVIEW.
4. Approve the rehearsal on a disposable PostgreSQL (no production access) to measure the pass time and the reaper risk before any step-2 plan.

## 9. Not verified

- The old key's index/constraint is confirmed live; `asset_registry` link to the output-digest spec was not traced; the live column list of `ephemeris_daily` beyond `node_mode`/`epoch_convention` was not compared with the legacy-column readers (S13/S14/S20 look dead).
- Row-order behaviour of Postgres for ties was reasoned, not observed.
- Whether `bg_transit_rules` carries Rahu/Ketu rows consumed by muhurta grading (P9) and whether `register_d10_pact` karaka sets can include the nodes were not traced.
- The digest measurement used a one-line comment edit; the real change set may move additional or fewer digests if the new modules are imported elsewhere (it will not, by design).

## 10. SS decisions on v1.0 (2026-10-02) and reader ownership

- (a) Option B: new `brahmagyan/l0_ephemeris_queries.py` that `ephemeris_routes.py` points at; mean-node logic in the new `l0_ephemeris_mean_node.py`; `l0_ephemeris.py` stays byte-identical; the old query functions stay, deprecated, under the lint ratchet.
- (b) L0 pin: same-PR transparent re-pin, PR body states exactly "exactly one L0 digest moved (bg_ephemeris), other 39 byte-identical" with the before/after inventory sha; cite decisions N-68/N-70 in `DECISIONS.jsonl` if a test or doc needs a ratification record.
- (c) Migration numbers (renumbered 2026-10-02 by SS, formerly 1225/1226/1227; Pravāha holds 1220 and 1225): 1227 = new unique index `(date, body, ayanamsha_id, node_mode) NULLS NOT DISTINCT` (step 0; D6 owner path if `amjis_app` is not the owner: the table is owned by `amjis_app`, read 2026-10-02, so the migration path applies once the owner's hold lifts); 1228 = replacement integrity contract + the append-only output-digest spec row; 1250 = drop of the old three-column constraint (step 2, at SS's release only). Files stay unwritten until the owner's line lifts the hold; intent documents meanwhile.
- (d) Rehearsal on a disposable Postgres with the real .se1 corpus approved (no production access); measure wall time (plan substeps per decade if above about 10 minutes) and non-mean digest equality.
- Also: the latent NULL-`node_mode` INSERT defect is fixed in the same writer change, with a test; the lint is step 0 with the index; `get_av_transit_gating` free-text planet gets a guard or pin in step 1.
- Priority: not on the J1 critical path and must not delay S-L1; lane order is the S-L1 mandatory set and the merge-train reviews first.

Reader ownership (SS, agreed with Pravāha): **Pravāha** takes P1, P2, P5, P6, P7, P14, P15, the `arc_fingerprint`/upstream-fingerprint traps, the `test_wp9_*` fixtures and the stale `v3_spline_accuracy` comment. **Suvarṇa** takes P3 (`ka_kshetra` `stage0_kinematics`, folded into I-10), P4 (`ka_kota_chakra`), P8 and P9 (`ka_graha_sancara` engine and `phala/muhurta`, with PATH-A and PATH-B on the SAME node at every step: step 1 both stay TRUE and say so; the switch to MEAN in step 3 is a REVIEW to SS with the list of rows that change), the L0 routes (S1-S11) and `get_av_transit_gating`. Step-1 PR for ours: NULL-safe pin to `'true'`, loud refusal on 0 or 2 rows per date for a node, behaviour-neutral, golden tests.

## 11. Additional hazards (N-69 request; read-only, 2026-10-02)

1. **TRUE_NODE code in the legacy ganita path.** `brahmagyan/ganita/engine.py:121` and `brahmagyan/ganita/l1_positions.py:128` use `swe.TRUE_NODE` for Rahu; `pipeline/brahma_pipeline.py:149-161` keeps `brahmagyan.ganita.engine` as the fallback in `_l1_ganita` and calls `graha_sthana_writer`. Reachability: no module under `ga_writers/`, `pipeline/orchestrator/`, `services/`, `routers/` or `main.py` imports `brahmagyan.ganita.engine`, `graha_sthana_writer` or `brahmagyan.ganita.l1_*` (grep of the import graph); `brahma_pipeline` itself is imported nowhere outside the package (migrations 962:26 and 963:11 independently record it as dead code); the five `l1_*` helpers that import `l1_positions` (`l1_dashas`, `l1_divisionals`, `l1_panchanga_birth`, `l1_sensitive_points`, `l1_strength`) are imported only inside `brahmagyan/ganita/` and by tests. The live L1 Rahu is `RAH_MEAN` from PyJHora (`engine_version pyjhora/1.0.0`; canonical `RAH_MEAN longitude_sidereal 49.0330441002811`). **No chart-build path reaches them.** Residual: dead-but-present code that would silently produce TRUE-node L1 values if revived; recommend deletion or a hard guard at import, scheduled, not urgent.
2. **`bg_cohort.py:333` pins `swe.TRUE_NODE`** for the 10,000-chart synthetic cohort, declared in its own `SAMPLING_METHOD_VERSION = "uniform_1900_2099_lat60_lon180_true_node_pinned_se1_v2"` (:156-159): a documented, versioned frame, but a DIFFERENT node frame from native charts (MEAN). Consumers: `bg_class_priors`/`bg_class_lifetime_counts` and the `ka_kshetra` salience stage cite the cohort; `bg_cohort` is L0, lit (last built 2026-09-07), guarded to Linux/x86_64. Action: document in the L0 sheet (F-L0-02) and schedule a `..._mean_node_..._v3` sampling version; any change moves `bg_cohort`'s digest (and the L0 pin) and needs a cohort rebuild, so it belongs with the L0 pin work, not in step 1.

## 12. Step-1 follow-ups (v1.2, 2026-10-02; SS decisions on PRs #2942, #2944, #2946)

**12.1 Dead copies kept byte-identical (remove at the next planned digest move).** Step 1 pinned the readers by routing callers to NEW modules and left the
old unpinned functions in place, because editing their files moves many writer digests. They are baselined in `platform/scripts/governance/node_series_pin_baseline.json`
as DEAD UNPINNED COPIES (not retired) and each has a pinned twin. List, label "remove at the next planned digest move":

| # | file | dead copy | pinned twin |
|---|---|---|---|
| 1 | `brahmagyan/l0_ephemeris.py` | `query_planet_position` (S1) | `brahmagyan/l0_ephemeris_queries.py` same name |
| 2 | `brahmagyan/l0_ephemeris.py` | `query_planet_transit` (S2) | same module |
| 3 | `brahmagyan/l0_ephemeris.py` | `query_aspects_at_time` (S3) | same module |
| 4 | `brahmagyan/l0_ephemeris.py` | `query_retrograde_periods` (S4) | same module |
| 5 | `brahmagyan/l0_ephemeris.py` | `get_ephemeris_cache_native_lifetime` (S5) | same module |
| 6 | `brahmagyan/l0_ephemeris.py` | `query_ephemeris` (S6) | same module |
| 7 | `brahmagyan/l0_ephemeris.py` | `check_volume` (S7) | same module |
| 8 | `services/ka_graha_sancara/engine.py` | `_read_from_bg_ephemeris` and `get_ephemeris` (P8; one baseline entry, two functions) | `services/ka_graha_sancara/engine_pinned.py` same names |

Items 1-7 are the seven in `l0_ephemeris.py` (an edit there moves 49 writer digests), item 8 is `engine.py` (an edit there moves about 43: 13 ga_*, 23 bo_*, 7 ka_*, per the
measurement in step 1). Both files are protected by byte-identity tests (`engine.py` by a sha256 pin in `tests/test_ka_graha_sancara_engine_pinned.py`; the `l0_ephemeris.py` copies are
driven as strict-xfail LEGACY rows in `tests/test_node_series_readers_ignore_mean_rows.py`, which fail if a dead copy ever becomes pinned or disappears without its row being updated).
Removing them must be done in one PR that is already moving those digests for another reason, together with the baseline retirements and the sha pin update.

**12.2 S11 `expected_rows` constant is stale (L0 finding, no code).** `/native_lifetime_meta` carries a hard-coded `expected_rows = 157266` and a `coverage_pct` derived from it.
It is wrong for the table as it is (and for the 11-body table after step 2). Step 1 deliberately left the served numbers untouched (SS); deriving it from days x bodies is a wave 2 item.
Record it in the L0 sheet; no code in step 1.

**12.3 Digest counts corrected.** `l0_ephemeris.py` moves **49** writer digests, not 48 (section 5, re-measured on current main); `ephemeris_routes.py` moves **none**, not bg_ephemeris
(section 5 and section 6 option B). Consequence: PR #2942 moves no L0 digest; the transparent L0 re-pin in decision (b) is needed only if a later change touches
`bg_ephemeris.py` or `l0_ephemeris.py` itself.

**12.4 Served rows do not carry `node_mode`.** The pinned readers return the same row shape as before (no `node_mode` key); a consumer cannot tell a TRUE row from a MEAN
row in the served output. SS ruled served output unchanged for step 1; adding `node_mode` to served rows is a **wave 2** item (with the S9 cap and the S5/S7/S10/S11 count semantics).

**12.5 Step-1 stack (for traceability).** #2933 (pin lint) -> #2942 (A: L0 query module + routes + parametrised mean-row proof, now earned in CI) -> #2944 (B: P4 ka_kota_chakra; moves
the `ka_kota_chakra` digest) -> #2946 (C: P8/P9 via `engine_pinned.py`, narrow `except NodeSeriesError: raise` in `phala/muhurta.py`; moves the `ka_graha_sancara` digest; `engine.py` untouched).
D (TypeScript guard) and E (P3 / I-10 digest move) are not started.
