---
asset_id: bg_ephemeris_engine
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
track_i_items: [TI-L0-03, TI-L0-06]
ledger_gap_ids: [bg_ephemeris_engine-Earn.build_record, bg_ephemeris_engine-Cost.baseline, bg_ephemeris_engine-Dens.served, bg_ephemeris_engine-Carr.detector]
---
# bg_ephemeris_engine — Ephemeris engine (service; no table)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. SS answered the open questions on 2026-10-01: decisions are recorded in §4 and §7 (items marked (R) are PROVISIONAL until the J1 review).

## 0 · Identity — what the asset is

A registered service, not a table: 'Swiss Ephemeris (pyswisseph) with the pinned SHA-256-verified sepl_18/semo_18/seas_18 corpus for file-backed sidereal planetary positions; foundation for all computational Jyotish; Lahiri canonical; MEAN_NODE convention: Rahu (ascending node)' (seed `platform/scripts/seed/asset_registry_seed.ts:465-483`; `storage_type: service`, `target_table`, `count_sql`, `target_floor` all null; it exposes `swisseph.calc_ut` through `provides_apis`). `has_writer = false`, no `@register`: a build cannot light it, its `asset_throughput` row reads `lit` with no rows. Declared dependent `bg_cohort` (census direct 1 / transitive 4). Served by 6 modules (`ephemeris_cache_native_lifetime.ts`, `ephemeris_cache_year.ts`, `query_aspects_at_time.ts`, `query_planet_position.ts`, `query_planet_transit.ts`, `query_retrograde_periods.ts`).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | service | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:465` | seed (live may differ by migration) |
| writer / `@register` | none registered in code; registry `has_writer` = False | writers dir, census `Build.registered` |
| target table(s) | `None`; count_sql tables: — | census CEN-R |
| live rows / floor | None / — (Δ —) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 1 / transitive 4 (every layer); named: `bg_cohort` | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | no table (service) | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | none; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | N/A | no writer, and the registry agrees (has_writer=false) — nothing to scan |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run cd79def6 complete/no disposition (2026-08-27) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 6 module(s): ephemeris_cache_native_lifetime.ts, ephemeris_cache_year.ts, query_aspects_at_time.ts, query_planet_position.ts, query_planet_transit.ts, query_retrograde_periods.ts; declaring density_contract: 0 |
| Build | Build.completion | N/A | no count_sql and nothing to count: has_writer=False, asset_kind='service', no target_table; build state='lit' |
| Build | Build.contract | N/A | no writer, and the registry agrees (has_writer=false) — nothing to scan |
| Build | Build.count_integrity | N/A | count_sql=no, integrity_check_sql=no |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Build | Build.registered | N/A | no writer, and the registry agrees (service or static) |
| Build | Build.target † | N/A | no target_table; asset_kind='service', has_writer=False |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run cd79def6 complete/no disposition (2026-08-27) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Build.dag †; Build.exercised (1 executed run(s) of 1 build_run_assets row(s), scope(s): asset_set, last executed 2026-08-27); Build.history.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr NO_DETECTOR · Idem NO_DETECTOR · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build NO_DETECTOR.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_ephemeris_engine-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_ephemeris_engine-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_ephemeris_engine-Dens.served | Dens | real as measured at rev 1 (Dens applies per SS Q2; offline re-measure in INDEX section 9.1) | CF-04 \| ledger: measured: 6 module(s): ephemeris_cache_native_lifetime.ts, ephemeris_cache_year.ts, query_aspects_at_time.ts, query_planet_position.ts, query_planet_transit.ts, query_re… |
| bg_ephemeris_engine-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| census: Ldgr (no reading) | Ldgr | detector | no recognised citation column on the target table; CF-08 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |
| census: services (T4 §4.2) | Earn | detector | the only status is `asset_throughput.state = lit` with no rows; no liveness or correctness probe can read false (CLAUDE.md §N.8); same finding as ledger `bg_panchanga-G01` for the sibling service |

## 3 · Disposition

**keep (P)** — a service asset with no data to reproduce; the open items are the status claim (a `lit` that no probe can read false), the missing carriage detector and the Dens reading. T4's storage clauses assume a table (TGH-T4-02).

Approver under Track A brief §10: **Steward (G16)**. Disposition accepted as proposed (SS 2026-10-01, Q10).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Service liveness-and-correctness probe

- **Answers:** census Earn NO_DETECTOR; `bg_panchanga-G01` pattern (sibling service); CF-05
- **Change:** a probe that answers a pinned instant for each body and compares to a stored expected longitude set (stored as a small fixture file, not a table) so `lit` can read false when the engine is down or wrong; it also serves as the D3 anchor. The corpus pin (SHA-256 of sepl_18/semo_18/seas_18) is part of the probe: a different corpus must fail it.
- **Files / declaration / migration:** a probe in Track E tooling plus a fixture under `platform/python-sidecar/tests/`; the engine code is not changed
- **Failing-first test and mutation:** failing-first: with the corpus path pointed at a wrong file the probe fails; mutation: perturb the expected set by 0.01° → fails
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 1 / transitive 4 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none
- **Gate it moves:** Earn, Carr
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: TGH-T4-02 (services have no storage/completeness clause)

### FD-2 · Carr detector — D3 on a pinned instant

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** the probe above is the carriage check: positions for pinned instants recomputed through the analytic route and compared within a declared tolerance.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 1 / transitive 4 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-3 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read the engine module behind `swisseph.calc_ut` (named in `provides_apis`) for any composed text column; declare `[]` (numeric service; no prose columns) with evidence from the service code
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 1 / transitive 4 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-4 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 6 modules (listed above); CF-04
- **Change:** decided (SS 2026-10-01, Q2): Dens applies because this asset reaches a served surface. Declare `density_contract` facets (`paginated`, `facets`, `empty_reason`) on the module(s); if the table is a uniform-authority vocabulary also declare `uniform_authority: true` in the declarations (R, PROVISIONAL until the J1 review); a mixed-authority table needs a real tier column.
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` module(s) named above; `platform/src/lib/retrieval/registry/types.ts` (descriptor, unchanged)
- **Failing-first test and mutation:** response-shape test for `empty_reason` and the trim; mutation: drop the declaration → census FAIL
- **Output change:** none
- **Blast radius:** no row changes (test or code-side only); declared dependents direct 1 / transitive 4 and the readers in the §0 row see no difference.
- **Rebuild:** none (TypeScript only)
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-independent for the facets (decided); the `uniform_authority` detector support is an (R) item for the E6 work
- **Decision:** ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3 probe
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-04** — Dens (serving density) on the L0 served modules: applies wherever a served surface is reached; `uniform_authority` (R). *This asset:* 6 modules
- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* bg_cohort’s DEP-ASSERT on this service (history) is explained by it having no writer

## 5 · Semantic fingerprint contract (for E5.5)

No table. The semantic contract is the function `swisseph.calc_ut` over the pinned corpus: same instant and flags → same longitude to the declared tolerance. Nothing to fingerprint in the database.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the pinned corpus (SHA-256) and the fail-closed rule; the Lahiri canonical default; the exported API.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation of a pinned instant by a second route).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Decisions applied (SS answered INDEX section 7 on 2026-10-01; no question is open in this brief)

Disposition accepted as proposed (Q10). Items marked (R) are PROVISIONAL until the J1 review.

1. ANSWERED by SS 2026-10-01 (Q5): authority-side declaration with NO stored-value change: `bg_ephemeris` declares `node: TRUE`; consumers needing MEAN must not read node values from it (a check, Track I item); body-name normalisation is declared the same way. BEFORE any wave touches `bg_ephemeris` or `bg_texts`, SS notifies Pravāha (Exec sends SS an ASK first).
2. CF-07: ANSWERED by SS 2026-10-01 (Q13): D1 anchor-term matching is accepted as the L0 carriage detector, but the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled. Ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, PROVISIONAL until the J1 review); it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.
3. CF-04: ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).
4. CF-03: ANSWERED by SS 2026-10-01 (Q6): a sibling's dispatch counts (`producer_covered`) when the registry declares the rider relation; the R61 cascade may stand until the first L0 dispatch.

**Track I items arising (see INDEX section 8):** TI-L0-03, TI-L0-06.
