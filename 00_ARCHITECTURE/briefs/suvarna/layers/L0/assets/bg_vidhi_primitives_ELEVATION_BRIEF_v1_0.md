---
asset_id: bg_vidhi_primitives
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
track_i_items: [TI-L0-01, TI-L0-03, TI-L0-06, TI-L0-28]
ledger_gap_ids: [bg_vidhi_primitives-Build.completion, bg_vidhi_primitives-Earn.build_record, bg_vidhi_primitives-Cost.baseline, bg_vidhi_primitives-Carr.detector]
---
# bg_vidhi_primitives — Vidhi registry — primitives (60 rows)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. SS answered the open questions on 2026-10-01: decisions are recorded in §4 and §7 (items marked (R) are PROVISIONAL until the J1 review).

## 0 · Identity — what the asset is

'Versioned vidhi primitive atoms — definition, live-tool mapping+args, fallback face, known_gap CR pointer; global, chart-agnostic (D-2 Lane V-1)'. `vidhi_primitives` holds 60 rows; the writer is a content mirror of the canonical TS registry `VIDHI_PRIMITIVES` in `platform/src/lib/vidhi/registry_data.ts`, held in lockstep by the CI drift gate `platform/scripts/census/check_vidhi_registry_parity.mjs` (writer header `bg_vidhi_primitives.py:1-25`; `.github/workflows/ci.yml:1538`). ON CONFLICT DO UPDATE (`:149`), a DELETE at `:189`; depends on nothing; declared dependent `bg_vidhi_floors` (census 1 / 1). The seed literal for `catalog_status` is DRAFT while live is CURRENT (layer instance F-01). Header text in the TS file says 52 primitives (stale); the writer holds 60. Comment-only references mean the Dens scanner (rev 4) reads NO_DETECTOR, never N/A (`N22/dens_repair_needs`).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:787` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_vidhi_primitives.py:125`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `vidhi_primitives`; count_sql tables: `vidhi_primitives` | census CEN-R |
| live rows / floor | 60 / 60 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 1 / transitive 1 (every layer); named: `bg_vidhi_floors` | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `vidhi_primitives`: 4 non-test py/ts/tsx files reference it (3 outside brahmagyan/ and bg_*.py writers): `types.ts`, `registry_data.ts`, `types.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | none; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Build | Build.completion | FAIL | build record says rows_written=0 against live=60 (global) |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): vidhi_primitives (bg_vidhi_primitives.py:144)); Vocab.identity (declared key (primitive_id): 0 duplicate(s)); Build.contract; Build.count_integrity; Build.dag †; Build.exercised (7 executed run(s) of 7 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-04); Build.history; Build.registered (@register in bg_vidhi_primitives.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build FAIL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_vidhi_primitives-Build.completion | Build | real (T4 §4.2 check 6) | see the fix design \| ledger: measured: build record says rows_written=0 against live=60 / required: the Build gate's claim |
| bg_vidhi_primitives-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_vidhi_primitives-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_vidhi_primitives-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| census: Ldgr (no reading) | Ldgr | detector | no recognised citation column on the target table; CF-08 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — all applicable cells PASS except the changed-rows reading (CF-01) and the detector gaps; the CI parity gate is an existing carriage mechanism.

Approver under Track A brief §10: **Steward (G16)**. Disposition accepted as proposed (SS 2026-10-01, Q10).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Build.completion: declare the changed-rows convention (CF-01 option A, R)

- **Answers:** census `Build.completion` FAIL ("rows_written=0 against live=…"); CF-01
- **Change:** decided (SS 2026-10-01, Q1, R, PROVISIONAL until the J1 review): declare the changed-rows convention for this writer (`ON CONFLICT DO UPDATE` leaves unchanged rows without a rowcount; the record shows 0 against 60); Build.completion then reads PASS only if the convention is declared AND count_integrity PASSes on populated rows; completion is proven by the count, not by `rows_written`.
- **Files / declaration / migration:** `asset_declarations.json` entry (convention + writer `file:line`); the verdict rule is `platform/scripts/governance/asset_census.py` (E6 detector work); no writer change
- **Failing-first test and mutation:** see CF-01
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration + detector rule; no rebuild)
- **Gate it moves:** Build (completion)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (decided; the criterion change is provisional until the J1 review)

### FD-2 · Register the existing CI parity gate as the Carr detector

- **Answers:** census Carr NO_DETECTOR; CF-07
- **Change:** as for `bg_vidhi_floors`: `check_vidhi_registry_parity.mjs` compares the writer’s dump to the TS canonical registry; register it for this asset with its seeded-drift case.
- **Files / declaration / migration:** inspector registry entry (Track E); no asset file changes
- **Failing-first test and mutation:** seeded one-primitive drift must fail the gate; mutation: edit one primitive in the TS file only
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none
- **Gate it moves:** Carr
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: TGH-T3-02

### FD-3 · Seed literal catalog_status

- **Answers:** layer instance F-01 (seed DRAFT vs live CURRENT); CF-03
- **Change:** correct the `asset_registry_seed.ts` literal for `bg_vidhi_primitives` to CURRENT (live and the migration agree); the seed is the file the three-way diff guard reads.
- **Files / declaration / migration:** `platform/scripts/seed/asset_registry_seed.ts` (the `bg_vidhi_primitives` row)
- **Failing-first test and mutation:** the seed-vs-live comparison reads equal for this field; mutation: restore DRAFT → the comparison differs
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none
- **Gate it moves:** Build (seed/registry agreement; not a registered cell)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### FD-4 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `bg_vidhi_primitives.py` for any composed text column; declare `[]` expected (authored definitions mirrored from the TS registry)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-5 · Ldgr: make the source column readable

- **Answers:** census `Ldgr.source_presence` has no reading; CF-08
- **Change:** declare that the source of each row is carried in the primitive’s `known_gap` CR pointer / definition source (to be named; no recognised citation column) so the inspector can read it; if the table has no source column the gap is real and is an output change (added by migration + writer)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` (`carriage`) and, only if no column exists, the writer + a migration
- **Failing-first test and mutation:** inspector reads PASS/FAIL on the declared column; a blank source must read FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration); a data fix would be a separate design
- **Gate it moves:** Ldgr (no reading → PASS/FAIL)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T3-01 (the Ldgr source is undefined in the gate map)

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-01** — Build.completion for converged reruns (rows_written = changed rows): option A decided (R). *This asset:* rows_written = 0 against 60
- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* seed literal DRAFT vs live CURRENT
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* register the existing CI parity gate
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-08** — Ldgr: assets with no recognised citation column (16 "no reading"). *This asset:* no recognised citation column

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `primitive_id` (census, 0 duplicates). Fingerprint over `(primitive_id, definition, tool mapping, args, fallback face, known_gap)` as canonical JSON; volatile: `created_at`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 60 primitives and their live-tool mappings, as mirrored from the TS registry.
- **Carriage check chosen (T4 §4.1; one only):** D3-equivalent: the existing two-copy parity gate.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Decisions applied (SS answered INDEX section 7 on 2026-10-01; no question is open in this brief)

Disposition accepted as proposed (Q10). Items marked (R) are PROVISIONAL until the J1 review.

1. CF-01: ANSWERED by SS 2026-10-01 (Q1): CF-01 option A (R, PROVISIONAL until the J1 review): a converged rerun with `rows_written = 0` reads Build.completion PASS ONLY IF the writer declares the changed-rows convention AND count_integrity PASSes on populated rows; completion is proven by the count, not by `rows_written`.
2. CF-03: ANSWERED by SS 2026-10-01 (Q6): a sibling's dispatch counts (`producer_covered`) when the registry declares the rider relation; the R61 cascade may stand until the first L0 dispatch.
3. CF-07: ANSWERED by SS 2026-10-01 (Q13): D1 anchor-term matching is accepted as the L0 carriage detector, but the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled. Ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, PROVISIONAL until the J1 review); it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.

**Track I items arising (see INDEX section 8):** TI-L0-01, TI-L0-03, TI-L0-06, TI-L0-28.
