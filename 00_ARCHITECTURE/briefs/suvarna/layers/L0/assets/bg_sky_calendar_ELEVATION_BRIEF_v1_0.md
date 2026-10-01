---
asset_id: bg_sky_calendar
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
track_i_items: [TI-L0-01, TI-L0-03, TI-L0-05, TI-L0-06, TI-L0-25]
ledger_gap_ids: [bg_sky_calendar-Build.completion, bg_sky_calendar-Earn.build_record, bg_sky_calendar-Cost.baseline, bg_sky_calendar-Dens.served, bg_sky_calendar-Carr.detector]
---
# bg_sky_calendar — Chart-independent sky-event diary (31,081 events; rolling horizon)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. SS answered the open questions on 2026-10-01: decisions are recorded in §4 and §7 (items marked (R) are PROVISIONAL until the J1 review).

## 0 · Identity — what the asset is

Registry description: 'Chart-independent global sky-event diary: sign ingresses (9 grahas), planetary stations (5 classical planets), solar/lunar eclipse timing and Jupiter–Saturn double-transit conjunction geometry, over a rolling 1900 → today+10y horizon'; real pyswisseph computations (`platform/python-sidecar/pipeline/orchestrator/writers/bg_sky_calendar.py:1-40`). A LIGHT writer; `ON CONFLICT DO NOTHING` on the natural key (event type, bodies, rounded Julian day) (`:119,734`), so a rerun inserts only new events and never corrects an existing one. The horizon end is `today + 10y` computed at run time (`:104,189,298`), which is why live 31,081 exceeds the registry floor 31,059 by 22. No declared dependents in the live registry (census 0/0; the inactive `ka_gochara_v3_century_materialize` named it); per-chart contact joins live in `ka_kshetra` stage 1 (writer header). Served by `query_sky_calendar.ts` (shared with the muhūrta lattice); 9 non-test files reference the table.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:835` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_sky_calendar.py:606`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bg_sky_calendar`; count_sql tables: `bg_sky_calendar` | census CEN-R |
| live rows / floor | 31081 / 31,059 (Δ +22) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 0 / transitive 0 (every layer) | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `bg_sky_calendar`: 9 non-test py/ts/tsx files reference it (4 outside brahmagyan/ and bg_*.py writers): `ka_kshetra.py`, `w26_real_eclipses.py`, `producer_editorial_review.ts`, `source_query_availability.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `query_sky_calendar.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 1 module(s): query_sky_calendar.ts; declaring density_contract: 0 |
| Build | Build.completion | FAIL | build record says rows_written=0 against live=31081 (global) |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Ldgr.source_presence (source_citation populated on 31081/31081 rows); Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): bg_sky_calendar (bg_sky_calendar.py:734)); Vocab.identity (declared key (event_type, primary_body, secondary_body_key, event_jd): 0 duplicate(s)); Build.contract; Build.count_integrity; Build.dag †; Build.exercised (2 executed run(s) of 2 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-04); Build.history; Build.registered (@register in bg_sky_calendar.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_sky_calendar-Build.completion | Build | real (T4 §4.2 check 6) | see the fix design \| ledger: measured: build record says rows_written=0 against live=31081 / required: the Build gate's claim |
| bg_sky_calendar-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_sky_calendar-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_sky_calendar-Dens.served | Dens | real as measured at rev 1 (Dens applies per SS Q2; offline re-measure in INDEX section 9.1) | CF-04 \| ledger: measured: 1 module(s): query_sky_calendar.ts; declaring density_contract: 0 / required: the Dens gate's claim |
| bg_sky_calendar-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — every applicable cell PASS except the changed-rows reading (CF-01) and the Dens question; the `DO NOTHING` clause is a rebuild-consequence note, not a defect today.

Approver under Track A brief §10: **Steward (G16)**. Disposition accepted as proposed (SS 2026-10-01, Q10).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Build.completion: declare the changed-rows convention (CF-01 option A, R)

- **Answers:** census `Build.completion` FAIL ("rows_written=0 against live=…"); CF-01
- **Change:** decided (SS 2026-10-01, Q1, R, PROVISIONAL until the J1 review): declare the changed-rows convention for this writer (`ON CONFLICT DO NOTHING` returns only newly inserted events by construction (`bg_sky_calendar.py:119,734`)); Build.completion then reads PASS only if the convention is declared AND count_integrity PASSes on populated rows; completion is proven by the count, not by `rows_written`.
- **Files / declaration / migration:** `asset_declarations.json` entry (convention + writer `file:line`); the verdict rule is `platform/scripts/governance/asset_census.py` (E6 detector work); no writer change
- **Failing-first test and mutation:** see CF-01
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 0 / transitive 0 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (declaration + detector rule; no rebuild)
- **Gate it moves:** Build (completion)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (decided; the criterion change is provisional until the J1 review)

### FD-2 · Rebuild consequence of `DO NOTHING` and a rolling horizon

- **Answers:** Track A §5 (fingerprint for E5.5); layer instance §4.3 (rollback); CF-12
- **Change:** a corrected computation would not repair existing rows, and a later rebuild adds rows beyond the old horizon. Record both in the B.L0 impact statement: the fingerprint is taken over a fixed as-of window; a correction to the event computation needs an explicit delete-and-recompute step scoped to the affected event types (never the whole table).
- **Files / declaration / migration:** the brief’s §5 contract and the rebuild plan (no asset file change)
- **Failing-first test and mutation:** a test that two runs a day apart have identical fingerprints over the shared window; mutation: change one stored event time → the fingerprint differs
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 0 / transitive 0 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none
- **Gate it moves:** Build (rebuild correctness; E5.5)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### FD-3 · Carr detector — D3 re-find sampled events

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** for a stratified sample of ingresses and stations, re-find the event by root-finding on `ephemeris_daily` longitudes (or the analytic route) and compare the time within a declared tolerance; eclipses and the Jupiter–Saturn geometry are re-derived from the same longitudes. A seeded shift of one event must be caught. Same-engine reruns are labelled reproduction only.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 0 / transitive 0 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-4 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `bg_sky_calendar.py` for any composed text column; declare `[]` if `detail`/label columns are literals or numbers (read the INSERT near `:734`)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 0 / transitive 0 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-5 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 1 module: `query_sky_calendar.ts`; CF-04
- **Change:** decided (SS 2026-10-01, Q2): Dens applies because this asset reaches a served surface. Declare `density_contract` facets (`paginated`, `facets`, `empty_reason`) on the module(s); if the table is a uniform-authority vocabulary also declare `uniform_authority: true` in the declarations (R, PROVISIONAL until the J1 review); a mixed-authority table needs a real tier column.
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` module(s) named above; `platform/src/lib/retrieval/registry/types.ts` (descriptor, unchanged)
- **Failing-first test and mutation:** response-shape test for `empty_reason` and the trim; mutation: drop the declaration → census FAIL
- **Output change:** none
- **Blast radius:** no row changes (test or code-side only); declared dependents direct 0 / transitive 0 and the readers in the §0 row see no difference.
- **Rebuild:** none (TypeScript only)
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-independent for the facets (decided); the `uniform_authority` detector support is an (R) item for the E6 work
- **Decision:** ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-01** — Build.completion for converged reruns (rows_written = changed rows): option A decided (R). *This asset:* rows_written = 0 on a rerun with no new events
- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* floor 31,059 vs live 31,081 (optional refresh; information)
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3 above
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-04** — Dens (serving density) on the L0 served modules: applies wherever a served surface is reached; `uniform_authority` (R). *This asset:* 1 module
- **CF-12** — Idem: an orphan census for upsert-only writers (the Idem PASS does not test accretion). *This asset:* rolling-horizon `ON CONFLICT DO NOTHING`, no DELETE found; accumulation is by design

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(event_type, primary_body, secondary_body_key, event_jd)` (census, 0 duplicates). Fingerprint over a FIXED as-of window of `(event_type, bodies, event_jd, detail)`; volatile: surrogate id, `created_at`/`computed_at`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the four event families, the pyswisseph derivation and the natural key that makes reruns idempotent.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-find sampled events by root-finding).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Decisions applied (SS answered INDEX section 7 on 2026-10-01; no question is open in this brief)

Disposition accepted as proposed (Q10). Items marked (R) are PROVISIONAL until the J1 review.

1. Not in the SS answer list (an information-only or design-step point): no decision needed; it stays as written, not escalated.
2. CF-01: ANSWERED by SS 2026-10-01 (Q1): CF-01 option A (R, PROVISIONAL until the J1 review): a converged rerun with `rows_written = 0` reads Build.completion PASS ONLY IF the writer declares the changed-rows convention AND count_integrity PASSes on populated rows; completion is proven by the count, not by `rows_written`.
3. CF-03: ANSWERED by SS 2026-10-01 (Q6): a sibling's dispatch counts (`producer_covered`) when the registry declares the rider relation; the R61 cascade may stand until the first L0 dispatch.
4. CF-07: ANSWERED by SS 2026-10-01 (Q13): D1 anchor-term matching is accepted as the L0 carriage detector, but the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled. Ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, PROVISIONAL until the J1 review); it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.
5. CF-04: ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).
6. CF-12: ANSWERED by SS 2026-10-01 (Q12): yes: 'no orphan rows under the writer's own partition' is the Idem claim for L0 upsert writers.

**Track I items arising (see INDEX section 8):** TI-L0-01, TI-L0-03, TI-L0-05, TI-L0-06, TI-L0-25.
