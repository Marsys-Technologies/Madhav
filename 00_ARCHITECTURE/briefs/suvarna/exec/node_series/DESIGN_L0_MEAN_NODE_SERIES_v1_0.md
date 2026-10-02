---
artifact: DESIGN_L0_MEAN_NODE_SERIES
version: "1.2"
status: "APPROVED by SS (N-68, c7883547f) with decisions (a)-(d); v1.1 adds reader ownership, the N-69 hazards and the decisions; v1.2 (2026-10-02) corrects the MEAN Ketu speed and retrograde flag (they EQUAL Rahu's: the stored TRUE Ketu rows have both inverted, F-L0-08), adds the node-series digest (section 12), the step-2 acceptance read-back and release report template (section 13) and the TRUE-Ketu correction pointer (section 14), and records that migration 1227 alone cannot create the index (amjis_app has no CREATE on schema public): the live index goes through a D6 owner-path executor (PR #2932); no code, migration or database write has been made by this document"
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

**v1.2 addendum to this finding (F-L0-08, `L0_FINDINGS_ADDENDUM_v1_1.md`).** The same rows carry a second defect that the MEAN series must not copy: stored TRUE **Ketu** `speed_dps` and `is_retrograde` are INVERTED relative to Rahu on all 91,676 paired dates (Ketu = Rahu + 180° so its speed and retrograde flag must EQUAL Rahu's; the writer negates the speed and derives the flag from the negated sign: `brahmagyan/l0_ephemeris.py:309-312,326-327`). Rahu is retrograde on 67,944 of 91,676 days (74.1%, the TRUE node reverses); stored Ketu on 23,732. See sections 1, 3, 4, 13, 14 and `REVIEW_TRUE_KETU_SPEED_FLAG_v1_0.md`.

## 1. Shape

Same table, same grain. New rows differ from the existing Rahu/Ketu rows only by `node_mode='mean'`; `epoch_convention='noon_ut'`, `ayanamsha_id='tropical'`,
coverage 1900-01-01..2150-12-31, Ketu = mean Rahu + 180° (lat 0). **v1.2 CORRECTION:** Ketu `speed_dps` = Rahu's speed (SAME sign) and Ketu `is_retrograde` = Rahu's flag; the mean node never reverses, so `is_retrograde` is TRUE on every mean row of both bodies (golden: Rahu mean speed −0.05295698 on 2026-11-30, Ketu mean speed −0.05295698). v1.0/v1.1 said "speed = −Rahu speed, same as the TRUE rows": that copied the stored TRUE-row defect (F-L0-08) and is withdrawn. Existing TRUE rows are not touched. Rows added:
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
  (`swe.calc_ut(jd, swe.MEAN_NODE, FLG_SWIEPH|FLG_SPEED)`; same flags as the TRUE rows; Ketu = (lon+180) mod 360; lat 0; **Ketu speed = Rahu's speed and Ketu `is_retrograde` = Rahu's flag, copied from the Rahu result of the same call, never derived from a negated or independent Ketu value** (v1.2; v1.1 said "speed negated", withdrawn: F-L0-08); `is_retrograde` for the mean Rahu = (speed < 0), which is TRUE on every day; `node_mode='mean'`).
- `pipeline/orchestrator/writers/bg_ephemeris.py`: the INSERT lists `node_mode` and `epoch_convention` for every row (today :126-130 omits both, so a fresh
  orchestrator-built row gets NULL `node_mode` even for TRUE rows: a latent defect this fixes); conflict target = the new key; mean rows are produced by the new module.
  A mean row can no longer overwrite a TRUE row because `node_mode` is in the key.
- Idempotency: L0 standard (`ON CONFLICT ... DO UPDATE ... WHERE ROW(...) IS DISTINCT FROM ROW(...)`), already-exact rows are untouched, so the existing rows are NOT
  rewritten EXCEPT (v1.2) the 91,676 stored TRUE Ketu rows, whose `speed_dps` and `is_retrograde` the corrected writer computes differently (F-L0-08): a rebuild inserts the
  183,352 new rows and rewrites exactly those 91,676 Ketu speed/flag values (the upsert's DO UPDATE set list already carries both columns). **Consequence: the writer fix must ship BEFORE any rebuild;
  with the old, inverted computation a rebuild after a data correction would silently revert the correction.** Acceptance check in the run: the digest ACCOUNT of section 13 (non-node rows
  and TRUE Rahu rows identical before and after; TRUE Ketu accounted for separately), not the single "non-mean digest identical" of v1.1 (that would be false by exactly the Ketu correction).
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
exactly one `true` and one `mean` row per date (no NULL node_mode on Rahu/Ketu); the 7 other bodies exactly one row per date with `node_mode IS NULL`; Ketu mean = (Rahu mean + 180) mod 360 to 1e-9; **Ketu mean `speed_dps` = Rahu mean `speed_dps` and Ketu mean `is_retrograde` = Rahu mean `is_retrograde` on every date, and `is_retrograde` is TRUE on every mean row (v1.2; the acceptance counts are in section 13).**
The registry update lands in the same D6 transaction as the old-constraint drop or immediately before the rebuild, so the probe is never red while data and contract disagree (and
`count_sql` stays `SELECT count(*) FROM ephemeris_daily`, so `Count.floor` delta becomes +183,352 until the floor is re-set to the achieved count, per the floors-are-aspirational rule).
The output-digest spec (migration 600 line 14) keys on `(date, body, ayanamsha_id)` and omits `node_mode`: two Rahu rows tie in its ORDER BY, so the digest becomes nondeterministic.
Specs are append-only, so a NEW spec row adds `node_mode` to the key/value columns and the registry is repointed (where `bg_ephemeris` links its spec was not traced; the live `asset_registry` has no
`output_digest_spec_sha256` column).

## 5. Digest / pin impact (measured, not guessed)

I ran the real digest generator (`pipeline.orchestrator.provenance_inventory`) in a scratch checkout at 2992093bc after appending one comment line:

| file edited | writer digests that move |
|---|---|
| `brahmagyan/l0_ephemeris.py` | **48**: L0 5 (bg_cohort, bg_ephemeris, bg_gochara_arcs, bg_muhurta_lattice, bg_sky_calendar), L1 13 (all ga_*), L2 23 (bo_*), L3 7 (ka_gochara, ka_graha_sancara, ka_kota_chakra, ka_moorti_nirnaya, ka_sudarshana_varsha, ka_vedha_gochara, ka_vighnakara); probe digest unchanged |
| `pipeline/orchestrator/writers/bg_ephemeris.py` | **1**: bg_ephemeris |
| `brahmagyan/ephemeris_routes.py` | **1**: bg_ephemeris |

Consequences, stated plainly:
- ANY change that touches only bg_ephemeris moves the L0 inventory (`bg_*`) and goes RED: `platform/src/generated/__tests__/nirmana-l0-analysis-receipts.test.ts` ("keeps the pinned writer-inventory digest in
  sync", `NIRMANA_L0_WRITER_INVENTORY_SHA256` in `nirmana_analysis_layer_pins.py` `L0_FROZEN_PINS`), and `NIRMANA_L0_ANALYSIS_RECEIPTS_AVAILABLE` would read false (`BLOCKS_CURRENT_ASSET` for all 40
  L0 assets: CAMPAIGN_STATE records exactly this failure mode, PR #1685). bg_ephemeris's already-accepted analysis receipt (bound to its old writer digest) no longer matches: it needs a fresh acceptance.
  No readmission shortcut is proposed. The only lawful routes are (a) leave the digest honest and let the gate read red until a separately ratified transparent re-pin lands (the D-NATIVE-06 / issue
  #2122 precedent re-derived the pin and verified that exactly the changed writer moved), or (b) the same PR carries that transparent re-pin. Which one is your/the native's call; I recommend (b) with the
  verification line "exactly one L0 digest moved, the other 39 byte-identical", shipped in the same PR so CI is green only because the pin is true.
- Nothing in the production run path reads the Nirmāṇa frozen definitions (N-51), so no build is blocked by a red pin; the cost is CI and the analysis-acceptance path.
- **Design rule that follows from the table:** mean-node logic must NOT be added to `brahmagyan/l0_ephemeris.py`. An edit there moves 48 digests across L0-L3 and turns the L1, L2 and L3 layer
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
`bg_ephemeris` (adds 183,352 rows). Verify: counts 1,008,436 / 11 per date; the digest ACCOUNT of section 13 (non-node rows identical; TRUE Rahu identical; TRUE Ketu accounted for separately because the corrected writer rewrites its speed and flag, F-L0-08); golden values (§1) to 1e-7°; the new integrity conjunct passes; the read-back and counts of section 13.
**Step 3:** readers switch to `'mean'` where the convention requires, one at a time, each with an attribution note: Pravāha's kernel-coherent set (P4-P7, P1/P2 with `ARC_ENGINE_VERSION` or `SUBSTRATE_VERSION` bumped,
because `arc_fingerprint` ignores `node_mode` and `ka_gochara`'s delta-aware skip would otherwise keep TRUE-derived rows; their upstream fingerprints deliberately exclude `ephemeris_daily` too), P8 only together with PATH-B
(`compute_transits.py:54,63`, `transit_search.py:10,64`, both TRUE) so the engine's two paths do not split.

**Reader edit in `l0_ephemeris.py` (S1-S6): two options.**
- A. Edit `l0_ephemeris.py` directly. Honest and simple; moves 48 digests (L0-L3) and turns the L0, L1, L2, L3 layer pins red until re-pinned.
- B (recommended). Put the pinned query functions in a new module `brahmagyan/l0_ephemeris_queries.py` and point `ephemeris_routes.py` at them; leave the old functions in `l0_ephemeris.py` untouched but marked
  deprecated and covered by the new lint's known-open ratchet. Moves 1 digest (bg_ephemeris) plus the L0 pin; nothing in L1-L3. Cost: a legacy unpinned copy stays until a later cleanup, which is exactly the "label/order variant" residue the known_open_readers ratchet exists to track.

## 7. Tests and the lint

- Lint (the §N.7 item 2 discipline, same shape as `check_fact_category_pinning.py` with a `known_open_readers` ratchet): any SQL text selecting from or joining `ephemeris_daily` (py, ts, sql) must contain a `node_mode` predicate or
  carry an explicit `# node-agnostic: <body list without Rahu/Ketu>` marker; a reader that does not pin fails CI; the known-open set starts as the census list and may only shrink.
- Golden tests: the §1 dates for the writer (mean Rahu/Ketu, Ketu = Rahu + 180, speeds, `node_mode`, `epoch_convention`), **plus a per-date equality assertion (v1.2): for every golden date AND for a sampled sweep of the 91,676 dates, mean Ketu `speed_dps` == mean Rahu `speed_dps` and mean Ketu `is_retrograde` == mean Rahu `is_retrograde` == True, and the corrected `bg_ephemeris` writer output for the TRUE rows has the same property (a test that pins the corrected behaviour; no test pins Ketu speed or flag today),** a duplicate-date regression for `w2g/db_source` and W2G V2/V4, and `test_bg_ephemeris_writer.py:98-120`
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
- (c) Migration numbers (renumbered 2026-10-02 by SS, formerly 1225/1226/1227; Pravāha holds 1220 and 1225): 1227 = new unique index `(date, body, ayanamsha_id, node_mode) NULLS NOT DISTINCT` (step 0; D6 owner path if `amjis_app` is not the owner: the table is owned by `amjis_app`, read 2026-10-02, so the migration path applies once the owner's hold lifts). **v1.2 CORRECTION of this clause: ownership is not enough. The routine migration login `amjis_app` has USAGE only on schema `public` (no CREATE; schema owner `data_plane_schema_owner`) and PostgreSQL needs CREATE on the schema for `CREATE INDEX` and `ADD CONSTRAINT UNIQUE`: both fail with `permission denied for schema public` (reproduced on a disposable PG 15). The live index is therefore created by a D6 owner-path executor (`exec/node_series/d6_index/`, plan hash for SS review, never run; PR #2932) and migration 1227 is the schema-of-record that verifies it (fail closed if absent). The ordering rule: D6 step first, then merge 1227.**; 1228 = replacement integrity contract + the append-only output-digest spec row; 1250 = drop of the old three-column constraint (step 2, at SS's release only). Files stay unwritten until the owner's line lifts the hold; intent documents meanwhile.
- (d) Rehearsal on a disposable Postgres with the real .se1 corpus approved (no production access); measure wall time (plan substeps per decade if above about 10 minutes) and non-mean digest equality.
- Also: the latent NULL-`node_mode` INSERT defect is fixed in the same writer change, with a test; the lint is step 0 with the index; `get_av_transit_gating` free-text planet gets a guard or pin in step 1.
- Priority: not on the J1 critical path and must not delay S-L1; lane order is the S-L1 mandatory set and the merge-train reviews first.

Reader ownership (SS, agreed with Pravāha): **Pravāha** takes P1, P2, P5, P6, P7, P14, P15, the `arc_fingerprint`/upstream-fingerprint traps, the `test_wp9_*` fixtures and the stale `v3_spline_accuracy` comment. **Suvarṇa** takes P3 (`ka_kshetra` `stage0_kinematics`, folded into I-10), P4 (`ka_kota_chakra`), P8 and P9 (`ka_graha_sancara` engine and `phala/muhurta`, with PATH-A and PATH-B on the SAME node at every step: step 1 both stay TRUE and say so; the switch to MEAN in step 3 is a REVIEW to SS with the list of rows that change), the L0 routes (S1-S11) and `get_av_transit_gating`. Step-1 PR for ours: NULL-safe pin to `'true'`, loud refusal on 0 or 2 rows per date for a node, behaviour-neutral, golden tests.

## 11. Additional hazards (N-69 request; read-only, 2026-10-02)

1. **TRUE_NODE code in the legacy ganita path.** `brahmagyan/ganita/engine.py:121` and `brahmagyan/ganita/l1_positions.py:128` use `swe.TRUE_NODE` for Rahu; `pipeline/brahma_pipeline.py:149-161` keeps `brahmagyan.ganita.engine` as the fallback in `_l1_ganita` and calls `graha_sthana_writer`. Reachability: no module under `ga_writers/`, `pipeline/orchestrator/`, `services/`, `routers/` or `main.py` imports `brahmagyan.ganita.engine`, `graha_sthana_writer` or `brahmagyan.ganita.l1_*` (grep of the import graph); `brahma_pipeline` itself is imported nowhere outside the package (migrations 962:26 and 963:11 independently record it as dead code); the five `l1_*` helpers that import `l1_positions` (`l1_dashas`, `l1_divisionals`, `l1_panchanga_birth`, `l1_sensitive_points`, `l1_strength`) are imported only inside `brahmagyan/ganita/` and by tests. The live L1 Rahu is `RAH_MEAN` from PyJHora (`engine_version pyjhora/1.0.0`; canonical `RAH_MEAN longitude_sidereal 49.0330441002811`). **No chart-build path reaches them.** Residual: dead-but-present code that would silently produce TRUE-node L1 values if revived; recommend deletion or a hard guard at import, scheduled, not urgent.
2. **`bg_cohort.py:333` pins `swe.TRUE_NODE`** for the 10,000-chart synthetic cohort, declared in its own `SAMPLING_METHOD_VERSION = "uniform_1900_2099_lat60_lon180_true_node_pinned_se1_v2"` (:156-159): a documented, versioned frame, but a DIFFERENT node frame from native charts (MEAN). Consumers: `bg_class_priors`/`bg_class_lifetime_counts` and the `ka_kshetra` salience stage cite the cohort; `bg_cohort` is L0, lit (last built 2026-09-07), guarded to Linux/x86_64. Action: document in the L0 sheet (F-L0-02) and schedule a `..._mean_node_..._v3` sampling version; any change moves `bg_cohort`'s digest (and the L0 pin) and needs a cohort rebuild, so it belongs with the L0 pin work, not in step 1.


## 12. The node-series digest (v1.2; L0-owned; ONE definition for both workstreams)

Requested by SS (Pravāha's step-3 upstream identity and our step-2 acceptance use the same text). Files: `digest/node_series_digest_v1.sql` (the definition),
`digest/node_series_digest_bodies_v1.sql` (same preimage, restricted to a body list: used for the step-2 account), `digest/non_node_digest_v1.sql` (same format over the seven
non-node bodies), `digest/tests/test_node_series_digest.py` (23 tests, run on disposable PostgreSQL 15.17 and 17). The SQL, verbatim:

```sql
-- node_series_digest v1 (the ONE definition; L0-owned; Pravaha reuses it VERBATIM as the upstream identity of a node series).
-- sha256 over the Rahu + Ketu rows of ONE node_mode of public.ephemeris_daily.
--   bind     node_mode = 'mean' | 'true'      psql: psql -v node_mode=mean -f node_series_digest_v1.sql   (the file uses :'node_mode')
--            a driver binds the same value in place of :'node_mode' (e.g. %(node_mode)s / $1); nothing else is parameterised.
--   preimage 'node_series_digest_v1' LF, then one line per row, rows ordered by (ayanamsha_id, body, date) under COLLATE "C",
--            lines joined by LF (no trailing LF), fields joined by '|', in this order:
--              ayanamsha_id | body | date as YYYY-MM-DD | node_mode | round(tropical_longitude, 9)::text | round(speed_dps, 9)::text | 1 or 0
--            numerics are the stored values rounded half away from zero to 9 decimals and printed by numeric::text with exactly 9
--            decimals (no locale, no float repr); is_retrograde is 1/0. UTF-8, sha256, lowercase hex.
--   columns  the key (date, body, ayanamsha_id, node_mode) plus tropical_longitude, speed_dps, is_retrograde: the position series.
--            sign_number, degree_in_sign, nakshatra_number are DERIVED from the longitude and stay OUT; latitude (0 on every node row),
--            epoch_convention (constant), source_citation, computed_at and id are provenance/bookkeeping and stay OUT.
--   result   n_rows, node_series_digest; the digest is NULL when the series has no row ("absent", never the hash of nothing).
--   moves on any change to a row of THIS series (a longitude or speed at the 6th decimal, a flag flip, a row added/removed/re-keyed);
--   does NOT move when non-node rows change, when the other node_mode's rows are present or change, or with insertion order.
SELECT count(*) AS n_rows,
       encode(sha256(convert_to(
         'node_series_digest_v1' || E'\n' ||
         string_agg(
           concat_ws('|',
             ayanamsha_id,
             body,
             to_char(date, 'YYYY-MM-DD'),
             node_mode,
             round(tropical_longitude, 9)::text,
             round(speed_dps, 9)::text,
             CASE WHEN is_retrograde THEN '1' ELSE '0' END),
           E'\n'
           ORDER BY ayanamsha_id COLLATE "C", body COLLATE "C", date),
         'UTF8')), 'hex') AS node_series_digest
FROM public.ephemeris_daily
WHERE node_mode = :'node_mode'
  AND body IN ('Rahu', 'Ketu');
```

**Column list (SS final, kept exactly):** the key `(date, body, ayanamsha_id, node_mode)` plus `tropical_longitude`, `speed_dps`, `is_retrograde`. `sign_number`, `degree_in_sign`,
`nakshatra_number` are derived from the longitude and stay OUT. I do not disagree with the list: `latitude` (0.000000 on all 183,352 live node rows), `epoch_convention` (one value, `noon_ut`),
`source_citation` (one value), `computed_at` and `id` carry no series identity and stay out too. Remaining remark, not a disagreement: because `epoch_convention` is out, a future change of the
epoch convention would have to ride a new `node_series_digest_v2`; and `ayanamsha_id` is in (a node row for another ayanamsha id would be a different series).

**Format (no locale, no float repr):** numerics are the STORED `numeric` values rounded half away from zero to 9 decimals and printed by `numeric::text`, which always carries exactly 9 decimals
(`round(0.1415931::numeric, 9)::text = '0.141593100'`); the date is `to_char(date,'YYYY-MM-DD')`; booleans are `1`/`0`; fields are joined by `|`, rows by LF (no trailing LF), after a first line
`node_series_digest_v1`; rows ordered by `(ayanamsha_id, body, date)` under `COLLATE "C"`, which is total because the key is unique within one `node_mode`; the hash is `sha256` over the UTF-8 bytes, lowercase hex.
The stored values have 6 decimals (`round(lon, 6)`, `round(speed, 7)` in the writer), so the 9-decimal grid loses nothing the table can hold. The digest is NULL (`n_rows` 0) for an absent series.
`concat_ws` drops NULL fields: every field of a node row is NOT NULL (`node_mode` is fixed by the WHERE; the four others are NOT NULL columns), and the non-node variant writes its NULL `node_mode` as `~`.

**Proven on the disposable PostgreSQL (`digest/tests`, 23 tests, PG 15.17 and 17; a shape of 1,008,436 rows = the real table after step 2):**
- does NOT move when non-node rows change (longitude, speed, flag changed; rows deleted; rows inserted), when TRUE rows are present beside it or are changed (values, flags, deleted, inserted),
  with physical or insertion order (all MEAN rows deleted and reinserted in `random()` order, then `VACUUM FULL`), or when `id`/`computed_at` change;
- DOES move on a 1e-6 longitude change (Rahu and Ketu), a 1e-6 speed change, a retrograde-flag flip, a row removed, a row added, a row re-keyed (another `ayanamsha_id`, another date);
- ignores a 1e-10 longitude change (below the 9-decimal grid) and any change of `latitude`, `source_citation`, `epoch_convention`, `sign_number`/`degree_in_sign`/`nakshatra_number`, `computed_at`, `id`;
- the bind works for `'true'` (the TRUE digest is unmoved by MEAN changes and vice versa); `bodies = '{Rahu,Ketu}'` returns exactly `node_series_digest_v1`; `{Rahu}` and `{Ketu}` split it;
- source-level mutations of the SQL (drop the `node_mode` filter, drop the ORDER BY, round to 5 decimals, drop `is_retrograde`) each turn the tests red;
- the preimage in the header is the real preimage: the test rebuilds it in Python from the rows and gets the same sha256.
**Cost** (synthetic 183,352-row series inside a 1,008,436-row table, local Apple-silicon PostgreSQL, psql start-up included): PG 15.17 0.53 s (MEAN) / 0.54 s (TRUE) / 1.85 s (non-node, 641,732 rows); PG 17 0.27 / 0.28 / 1.28 s.
It is one sequential aggregate with a sort of 183,352 short lines (about 18 MB of text): cheap enough to run before and after every step. Production timing is not measured (no production run).

## 13. Step-2 acceptance read-back and release report template (v1.2)

Added to the step-2 section as part of the release report. Read-only queries as `suvarna_reader`; `<NODE_DIGEST>` = `psql -v node_mode=... -f digest/node_series_digest_v1.sql`.

**A. Counts.** `SELECT count(*), count(DISTINCT date) FROM public.ephemeris_daily` = 1,008,436 / 91,676; per date exactly 11 rows (`SELECT count(*) FROM (SELECT date FROM public.ephemeris_daily GROUP BY date HAVING count(*) <> 11) x` = 0);
`SELECT body, node_mode, count(*) FROM public.ephemeris_daily GROUP BY 1,2` = 7 non-node bodies x NULL x 91,676, and Rahu and Ketu x (`true`, `mean`) x 91,676.

**B. Digest account (replaces v1.1's single "non-mean rows identical").** Capture before step 2 and after the build; the four lines must read:
| digest | before = after? | why |
|---|---|---|
| `non_node_digest_v1` (7 non-node bodies, `node_mode IS NULL`) | IDENTICAL | untouched by the node work |
| `node_series_digest_bodies_v1`, `node_mode=true`, `bodies={Rahu}` | IDENTICAL | TRUE Rahu is not rewritten |
| `node_series_digest_bodies_v1`, `node_mode=true`, `bodies={Ketu}` | DIFFERENT, and accounted for (below) | the corrected writer rewrites exactly the Ketu `speed_dps` and `is_retrograde` (F-L0-08) |
| `node_series_digest_v1`, `node_mode=mean` | absent before (NULL, 0 rows); after: the new value, recorded in the release report and handed to Pravāha as their upstream identity | the new series |
Accounting for TRUE Ketu: the number of TRUE Ketu rows whose `speed_dps` or `is_retrograde` changed = 91,676 (the writer's rewrite count; the same figure as the paired-date defect count today), `tropical_longitude` of every TRUE Ketu row is unchanged (the check below, `lon_not_180 = 0`, before and after) and no other column of any Ketu row changed.
If SS instead orders the TRUE-Ketu data correction BEFORE step 2 (see `REVIEW_TRUE_KETU_SPEED_FLAG_v1_0.md`), the Ketu line reads IDENTICAL across step 2 and the v1.1 invariant ("all non-mean rows identical") holds again.

**C. Golden values.** The seven §1 dates: stored mean Rahu/Ketu longitudes within 5e-7° (the stored value has 6 decimals; the design's 1e-7° tolerance applies to the computed, pre-rounding value in the writer test), speeds within 5e-8.

**D. The integrity conjunct (section 4) passes**, including the new Ketu clauses of E3.

**E. Read-back (SS, Pravāha's expectation).**
E1. Lahiri (`lahiri_chitrapaksha` = `SIDM_LAHIRI`, the repo's convention `l0_ephemeris.py:133,228`) SIDEREAL sign of MEAN Rahu and of stored TRUE Rahu for each day 2026-11-26..2026-12-06 inclusive. Query to run after the build:
```sql
SELECT date, node_mode, tropical_longitude, speed_dps, is_retrograde
FROM public.ephemeris_daily
WHERE body = 'Rahu' AND ayanamsha_id = 'tropical' AND date BETWEEN '2026-11-26' AND '2026-12-06'
ORDER BY date, node_mode;           -- expect 22 rows: 11 'mean' and 11 'true'
```
then, for each row, `sidereal = (tropical_longitude - swe.get_ayanamsa_ut(swe.julday(y, m, d, 12.0))) mod 360` after `swe.set_sid_mode(swe.SIDM_LAHIRI)` (noon UT, as the stored rows), sign = floor(sidereal / 30). Today's TRUE values (read from the stored rows 2026-10-02, pyswisseph 2.10.03 for the ayanamsa) and the
EXPECTED MEAN values (pyswisseph `MEAN_NODE`, independent of the build; stored mean longitudes must agree within 5e-7° in tropical terms):
| date | Lahiri ayanamsa | TRUE tropical (stored) | TRUE sidereal | TRUE sign | expected MEAN tropical | expected MEAN sidereal | expected MEAN sign |
|---|---|---|---|---|---|---|---|
| 2026-11-26 | 24.23291 | 324.075591 | 299.8427 | Capricorn | 324.723356 | 300.4904 | Aquarius |
| 2026-11-27 | 24.23295 | 323.957377 | 299.7244 | Capricorn | 324.670459 | 300.4375 | Aquarius |
| 2026-11-28 | 24.23298 | 323.887181 | 299.6542 | Capricorn | 324.617549 | 300.3846 | Aquarius |
| 2026-11-29 | 24.23302 | 323.858486 | 299.6255 | Capricorn | 324.564620 | 300.3316 | Aquarius |
| 2026-11-30 | 24.23306 | 323.855527 | **299.6225** | Capricorn | 324.511671 | **300.2786** | Aquarius |
| 2026-12-01 | 24.23310 | 323.857145 | 299.6240 | Capricorn | 324.458708 | 300.2256 | Aquarius |
| 2026-12-02 | 24.23314 | 323.841529 | 299.6084 | Capricorn | 324.405736 | 300.1726 | Aquarius |
| 2026-12-03 | 24.23317 | 323.790662 | 299.5575 | Capricorn | 324.352764 | 300.1196 | Aquarius |
| 2026-12-04 | 24.23321 | 323.693637 | 299.4604 | Capricorn | 324.299798 | 300.0666 | Aquarius |
| 2026-12-05 | 24.23325 | 323.548376 | 299.3151 | Capricorn | 324.246841 | 300.0136 | Aquarius |
| 2026-12-06 | 24.23329 | 323.361606 | 299.1283 | Capricorn | 324.193897 | 299.9606 | **Capricorn** |
**Pravāha's reference check: stored TRUE Rahu on 2026-11-30 is sidereal 299.6225 (Capricorn): it AGREES with their 299.6225 to four decimals (tropical 323.855527 minus ayanamsa 24.23306).** TRUE is in Capricorn on every one of the 11 days; the expected MEAN is in Aquarius through 12-05 and in Capricorn from 12-06 (299.9606), exactly Pravāha's expectation (MEAN 2026-11-30 sidereal 300.2786, Aquarius). The release report records the stored MEAN rows' sidereal values and signs next to this table and fails on any sign or 5e-7° disagreement.
E2. `is_retrograde` on the node rows (expected: MEAN not-retrograde count 0 for BOTH bodies):
```sql
SELECT body, node_mode, count(*) AS n, count(*) FILTER (WHERE is_retrograde IS NOT TRUE) AS not_retrograde
FROM public.ephemeris_daily WHERE body IN ('Rahu','Ketu') GROUP BY 1,2 ORDER BY 1,2;
```
Expected after the build: `Ketu|mean|91676|0`, `Rahu|mean|91676|0`; the TRUE rows for contrast. Today (read-only 2026-10-02) the TRUE rows read `Ketu|true|91676|67944` and `Rahu|true|91676|23732`; after the corrected writer/rebuild the TRUE Ketu row reads `23732` (equal to Rahu's, because the flags are equal), and the mean rows read 0.
E3. Ketu equals Rahu on every date (speed, flag; longitude differs by exactly 180 degrees), per node_mode:
```sql
SELECT r.node_mode, count(*) AS paired_dates,
       count(*) FILTER (WHERE k.speed_dps IS DISTINCT FROM r.speed_dps)       AS speed_differs,
       count(*) FILTER (WHERE k.is_retrograde IS DISTINCT FROM r.is_retrograde) AS flag_differs,
       count(*) FILTER (WHERE abs(((k.tropical_longitude - r.tropical_longitude - 180) % 360 + 540) % 360 - 180) > 0.000001) AS lon_not_180
FROM public.ephemeris_daily r
JOIN public.ephemeris_daily k ON k.date = r.date AND k.ayanamsha_id = r.ayanamsha_id AND k.node_mode IS NOT DISTINCT FROM r.node_mode AND k.body = 'Ketu'
WHERE r.body = 'Rahu' GROUP BY 1 ORDER BY 1;
```
Expected after the build: `mean|91676|0|0|0` and `true|91676|0|0|0`. Today (read-only, 2026-10-02): `true|91676|91676|91676|0` (speed differs on all 91,676 pairs and equals the NEGATED Rahu speed on all 91,676; flag differs on all 91,676; longitude is exactly Rahu + 180 on all). Any other count fails the release.

**Release report template (fill at step 2):** (1) A counts; (2) B four digests before/after with the Ketu account and the new mean digest value; (3) C golden table; (4) D integrity result; (5) E1 table with stored mean rows filled, E2 counts, E3 counts; (6) timing of the build and of each digest (the digest costs are in section 12); (7) the N-71 admission statement for the single moved L0 digest; (8) anything not verified.

## 14. The stored TRUE-Ketu defect: where it is handled

F-L0-08 (`L0_FINDINGS_ADDENDUM_v1_1.md`) records the finding with the aggregate and its SQL. `REVIEW_TRUE_KETU_SPEED_FLAG_v1_0.md` answers what to do with the existing TRUE Ketu rows (readers with owners, stored and served effects on the canonical chart,
the two data-fix routes, the writer lines and digest cost, the effect on the acceptance check, and the recommended timing). Summary of the design consequences already applied above: MEAN Ketu speed and flag equal Rahu's (sections 1, 3, 4); the corrected writer rewrites exactly 91,676 TRUE Ketu values at the first rebuild, so the writer fix ships before any rebuild
(section 3); the step-2 acceptance is the digest account (sections 6, 13).
