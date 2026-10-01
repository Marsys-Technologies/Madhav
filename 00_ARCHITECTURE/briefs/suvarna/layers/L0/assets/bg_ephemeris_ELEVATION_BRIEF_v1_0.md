---
asset_id: bg_ephemeris
layer: L0 Brahmagyan (bg_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L0 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L0/L0_LAYER_INSTANCE_v3_1.md (3.1-rev1, PROVISIONAL)"
base_commit: "main 0250cbade"
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16)"
decisions_applied: "SS answers to INDEX section 7, 2026-10-01 (items marked R are PROVISIONAL until the J1 review); disposition accepted as proposed"
track_i_items: [TI-L0-01, TI-L0-03, TI-L0-05, TI-L0-06, TI-L0-17, TI-L0-19, TI-L0-25]
ledger_gap_ids: [bg_ephemeris-G01, bg_ephemeris-G02, bg_ephemeris-G03, bg_ephemeris-G04, bg_ephemeris-G05, bg_ephemeris-G06, bg_ephemeris-O1, bg_ephemeris-O2, bg_ephemeris-O3, bg_ephemeris-O4, bg_ephemeris-Build.completion, bg_ephemeris-Earn.build_record, bg_ephemeris-Cost.baseline, bg_ephemeris-Dens.served, bg_ephemeris-Carr.detector, bg_ephemeris-Earn.build_record, bg_ephemeris-G03, bg_ephemeris-Dens.served, bg_ephemeris-G05, bg_ephemeris-Carr.D3, bg_ephemeris-G02, bg_ephemeris-Carr.detector]
---
# bg_ephemeris — Daily ephemeris, 1900-01-01 → 2150-12-31 (825,084 rows)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. SS answered the open questions on 2026-10-01: decisions are recorded in §4 and §7 (items marked (R) are PROVISIONAL until the J1 review).

## 0 · Identity — what the asset is

`ephemeris_daily`: tropical longitudes for 9 bodies (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu) × 91,676 days at a noon-UT epoch, computed with pyswisseph from the pinned file-backed corpus; a governed rebuild fails closed rather than accept the analytic fallback (`platform/python-sidecar/pipeline/orchestrator/writers/bg_ephemeris.py:36-45`). Registry description 'Swiss Ephemeris DE441 — raw astronomical positions'; raw tropical stored, five ayanāṃśas derived at read time (seed `asset_registry_seed.ts:185-200`, floor 825,084). Idempotency is a conditional upsert that leaves exact rows untouched, so a rerun reports only inserted or repaired rows (`bg_ephemeris.py:9-12`, `ON CONFLICT (date, body, ayanamsha_id) DO UPDATE` at `:133`). **The node frame is TRUE node, noon UT, declared per row in `node_mode`/`epoch_convention`** (`brahmagyan/l0_ephemeris.py:9-17,66-70`), while the engine service, `routers/ephemeris.py` and `panchang_engine/planets.py` mandate MEAN_NODE as the house standard (same header). Highest-consumption L0 table: 46 non-test py/ts/tsx files reference `ephemeris_daily`. Declared dependents: `bg_gochara_arcs` (an R9 asset) and five Kāla assets (`ka_gochara`, `ka_graha_sancara`, `ka_kota_chakra`, `ka_moorti_nirnaya`, `ka_vedha_gochara`); census direct 6 / transitive 35.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:185` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_ephemeris.py:38`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `ephemeris_daily`; count_sql tables: `ephemeris_daily` | census CEN-R |
| live rows / floor | 825084 / 825,084 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 6 / transitive 35 (every layer); named: `bg_gochara_arcs`, `ka_gochara`, `ka_graha_sancara`, `ka_kota_chakra`, `ka_moorti_nirnaya`, `ka_vedha_gochara` | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `ephemeris_daily`: 46 non-test py/ts/tsx files reference it (35 outside brahmagyan/ and bg_*.py writers): `ephemeris.py`, `panchang.py`, `transit_search.py`, `brahma_pipeline.py`, `ka_moorti_nirnaya.py` +30 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `get_graha_yuddha.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 4 module(s): query_aspects_at_time.ts, query_planet_position.ts, query_planet_transit.ts, query_retrograde_periods.ts; declaring density_contract: 0 |
| Build | Build.completion | FAIL | build record says rows_written=0 against live=825084 (global) |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Ldgr.source_presence (source_citation populated on 825084/825084 rows); Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): ephemeris_daily (bg_ephemeris.py:125)); Vocab.identity (declared key (date, body, ayanamsha_id): 0 duplicate(s)); Build.contract; Build.count_integrity; Build.dag †; Build.exercised (3 executed run(s) of 3 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-04); Build.history; Build.registered (@register in bg_ephemeris.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_ephemeris-G01 | Vocab | real | `body` stored capitalised (`Jupiter`) against lowercase ontology ids (`jupiter`); `integrity_check_sql` pins the capitalised array. Not measured by the census (Vocab.identity reads the declared key only) \| ledger: measured: body is stored as 'Jupiter'/'Ketu'/'Mars' while brahma_ontology planet canonical_ids are lowercase (jupiter, ketu, mars) — every join from the most-read L0 tab… |
| bg_ephemeris-G02 | Carr | detector | no D3 re-derivation; the integrity SQL asserts shape only |
| bg_ephemeris-G03 | Build | real (T4 check 6); cause established as the changed-rows convention | the ledger proposes "instrument the COPY path"; the writer docstring (`bg_ephemeris.py:9-12`) says rowcount counts only inserted or repaired rows, so 0 is expected on a converged rerun (whether the latest recorded run was one was not read from build_run_assets); CF-01 |
| bg_ephemeris-G04 | Complete | information / opportunity | `node_mode` holds one value (`true`); mean-node rows are not held \| ledger: measured: node_mode holds one value ('true'); mean-node positions are not held, while the schema can express both and the data plane warns against erasing true/mean conv… |
| bg_ephemeris-G05 | Dens | real as measured at rev 1 (Dens applies per SS Q2; offline re-measure in INDEX section 9.1) | 4 modules, 0 declare a density_contract; CF-04 \| ledger: measured: 4 capability modules expose it, 0 declare a density_contract / required: declared where the capability paginates or facets |
| bg_ephemeris-G06 | Reach | information | field-level exposure census was not run in the ledger; the saved census records reach for this asset (`Reach.fields`) \| ledger: measured: field-level exposure census NOT RUN for the 4 serving modules / required: measured, not assumed |
| bg_ephemeris-O1 | NONE | opportunity | mean-node rows or a declared limit (P13) \| ledger: answers P13 for the node, which today cannot be answered from this table |
| bg_ephemeris-O2 | NONE | opportunity | sub-daily grain decision \| ledger: the grain decision taken deliberately once instead of inherited |
| bg_ephemeris-O3 | NONE | opportunity | D3 as a standing check \| ledger: a real second opinion on 825,084 computed values |
| bg_ephemeris-O4 | NONE | opportunity | a rate baseline for the layer’s largest build \| ledger: a baseline for the layer's largest build, without which O2's options cannot be compared |
| bg_ephemeris-Build.completion | Build | real (T4 §4.2 check 6) | see the fix design \| ledger: measured: build record says rows_written=0 against live=825084 / required: the Build gate's claim |
| bg_ephemeris-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_ephemeris-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_ephemeris-Dens.served | Dens | real as measured at rev 1 (Dens applies per SS Q2; offline re-measure in INDEX section 9.1) | duplicate of G05 after folding (R81) \| ledger: measured: 4 module(s): query_aspects_at_time.ts, query_planet_position.ts, query_planet_transit.ts, query_retrograde_periods.ts; declaring density_contract: 0 / required… |
| bg_ephemeris-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| bg_ephemeris-Carr.D3 | Carr | detector | same as G02 (folded) |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — the grid is complete (91,676 days × 9 bodies, no missing cell, layer instance Q-14) and every Build cell is PASS except the `rows_written = 0` convention reading. The open items are the vocabulary mismatch, the unproven carriage and a documented node-convention split now declared at the authority (`node: TRUE`, SS 2026-10-01).

Approver under Track A brief §10: **Steward (G16)**. Disposition accepted as proposed (SS 2026-10-01, Q10).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Authority-side declarations: `node: TRUE` and body-name normalisation; no stored-value change

- **Answers:** ledger `bg_ephemeris-G01`; census Vocab.identity PASS (declared key only); CF-09 (b)
- **Change:** decided (SS 2026-10-01, Q5): `bg_ephemeris` declares `node: TRUE` (the table holds the TRUE node at noon UT, `l0_ephemeris.py:9-17,66-70`) and the body-name normalisation (planet ids lowercase in the ontology; the table stores the display form) at the authority, with NO stored-value change. A consumer needing MEAN must not read node values from this table (a check, Track I item). The rewrite option is not taken.
- **Files / declaration / migration:** declarations entry for `bg_ephemeris` + the ontology writer’s normalisation rule (TI-L0-11) + a consumer check
- **Failing-first test and mutation:** failing-first join census: `body` resolves to exactly one ontology `planet` row with no case handling (fails today); mutation: add a body spelling not in the set → raised, not silently matched
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration + check); before any wave touches bg_ephemeris SS notifies Pravāha (ASK first)
- **Gate it moves:** Vocab (rule 3)
- **Fix class:** registry/declaration only (recommended) or data; **buildable before J1:** tier-independent (decided)
- **Decision:** ANSWERED by SS 2026-10-01 (Q5): authority-side declaration with NO stored-value change: `bg_ephemeris` declares `node: TRUE`; consumers needing MEAN must not read node values from it (a check, Track I item); body-name normalisation is declared the same way. BEFORE any wave touches `bg_ephemeris` or `bg_texts`, SS notifies Pravāha (Exec sends SS an ASK first).

### FD-2 · Build.completion: declare the changed-rows convention (CF-01 option A, R)

- **Answers:** census `Build.completion` FAIL ("rows_written=0 against live=…"); CF-01
- **Change:** decided (SS 2026-10-01, Q1, R, PROVISIONAL until the J1 review): declare the changed-rows convention for this writer (the writer docstring declares the changed-rows convention (`bg_ephemeris.py:9-12`); the declaration + detector rule of CF-01 A closes it without a rebuild); Build.completion then reads PASS only if the convention is declared AND count_integrity PASSes on populated rows; completion is proven by the count, not by `rows_written`.
- **Files / declaration / migration:** `asset_declarations.json` entry (convention + writer `file:line`); the verdict rule is `platform/scripts/governance/asset_census.py` (E6 detector work); no writer change
- **Failing-first test and mutation:** see CF-01
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration + detector rule; no rebuild)
- **Gate it moves:** Build (completion)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (decided; the criterion change is provisional until the J1 review)

### FD-3 · Carr detector — D3 re-derivation by a second path

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** recompute a stratified sample of stored longitudes with pyswisseph through a different ephemeris route (the analytic Moshier mode, which is independent of the file-backed corpus) and compare within a declared tolerance; add a continuity check (day-to-day delta against the speed implied by neighbouring rows) and a station-sign check against `bg_sky_calendar`. Reproduction by the same pinned corpus is a weaker second check and is stated as such. Seeded error: shift one row by a degree → must be caught. No JH-parity oracle (CLAUDE.md §N.4).
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-4 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `bg_ephemeris.py`, `brahmagyan/l0_ephemeris.py` for any composed text column; declare `[]` expected (numeric table; `source_citation` is a literal)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-5 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 4 modules: `query_aspects_at_time.ts`, `query_planet_position.ts`, `query_planet_transit.ts`, `query_retrograde_periods.ts`; CF-04
- **Change:** decided (SS 2026-10-01, Q2): Dens applies because this asset reaches a served surface. Declare `density_contract` facets (`paginated`, `facets`, `empty_reason`) on the module(s); if the table is a uniform-authority vocabulary also declare `uniform_authority: true` in the declarations (R, PROVISIONAL until the J1 review); a mixed-authority table needs a real tier column.
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` module(s) named above; `platform/src/lib/retrieval/registry/types.ts` (descriptor, unchanged)
- **Failing-first test and mutation:** response-shape test for `empty_reason` and the trim; mutation: drop the declaration → census FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (TypeScript only)
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-independent for the facets (decided); the `uniform_authority` detector support is an (R) item for the E6 work
- **Decision:** ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-01** — Build.completion for converged reruns (rows_written = changed rows): option A decided (R). *This asset:* rows_written = 0 on a converged rerun by the writer’s stated convention
- **CF-09** — Identity and normalisation reconciliation at the authority (bg_ontology and its consumers). *This asset:* body-name case
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3 above
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-04** — Dens (serving density) on the L0 served modules: applies wherever a served surface is reached; `uniform_authority` (R). *This asset:* 4 modules
- **CF-08** — Ldgr: assets with no recognised citation column (16 "no reading"). *This asset:* no gap: `source_citation` 825,084/825,084
- **CF-12** — Idem: an orphan census for upsert-only writers (the Idem PASS does not test accretion). *This asset:* conditional upsert over a fixed grid; orphans would need a shrunk date range (low risk)

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(date, body, ayanamsha_id)` (census, 0 duplicates) over 825,084 rows; the semantic fingerprint is the ordered longitudes (and `node_mode`, `epoch_convention` for the nodes). Volatile columns excluded: `created_at`, any build id. Conditional upsert: a converged rebuild leaves the fingerprint unchanged by construction.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 91,676 × 9 grid, the pinned file-backed corpus and fail-closed rule, the noon-UT epoch, the per-row node declaration.
- **Carriage check chosen (T4 §4.1; one only):** D3 (independent re-derivation by a second ephemeris route plus continuity).
- **Opportunities (never blocking):** the four ledger opportunities `bg_ephemeris-O1…O4` (mean-node rows or a declared limit; grain decision; standing D3; build-cost baseline).

## 7 · Decisions applied (SS answered INDEX section 7 on 2026-10-01; no question is open in this brief)

Disposition accepted as proposed (Q10). Items marked (R) are PROVISIONAL until the J1 review.

1. ANSWERED by SS 2026-10-01 (Q5): authority-side declaration with NO stored-value change: `bg_ephemeris` declares `node: TRUE`; consumers needing MEAN must not read node values from it (a check, Track I item); body-name normalisation is declared the same way. BEFORE any wave touches `bg_ephemeris` or `bg_texts`, SS notifies Pravāha (Exec sends SS an ASK first).
2. ANSWERED by SS 2026-10-01 (Q1): CF-01 option A (R, PROVISIONAL until the J1 review): a converged rerun with `rows_written = 0` reads Build.completion PASS ONLY IF the writer declares the changed-rows convention AND count_integrity PASSes on populated rows; completion is proven by the count, not by `rows_written`.
3. CF-09: ANSWERED by SS 2026-10-01 (Q4): the normalisation rule lives in the `bg_ontology` writer, the one authority; the vocabulary release id goes in the first wave if it is cheap; for the 11 two-class ids take the recommended option (a, class-aware resolvers) unless it changes served ids (then REVIEW to SS); of bhrigu_samhita, jaimini_sutram, lal_kitab_text keep any with a consumer and remove the rest; Abhijit is a declared exception (classically intercalary) and the 27-id class stays canonical. ANSWERED by SS 2026-10-01 (Q5): authority-side declaration with NO stored-value change: `bg_ephemeris` declares `node: TRUE`; consumers needing MEAN must not read node values from it (a check, Track I item); body-name normalisation is declared the same way. BEFORE any wave touches `bg_ephemeris` or `bg_texts`, SS notifies Pravāha (Exec sends SS an ASK first).
4. CF-07: ANSWERED by SS 2026-10-01 (Q13): D1 anchor-term matching is accepted as the L0 carriage detector, but the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled. Ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, PROVISIONAL until the J1 review); it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.
5. CF-04: ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).
6. CF-12: ANSWERED by SS 2026-10-01 (Q12): yes: 'no orphan rows under the writer's own partition' is the Idem claim for L0 upsert writers.

**Track I items arising (see INDEX section 8):** TI-L0-01, TI-L0-03, TI-L0-05, TI-L0-06, TI-L0-17, TI-L0-19, TI-L0-25.
