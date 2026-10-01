---
asset_id: bg_vidhi_floors
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
disposition: "qualify (Q)"
disposition_proposal_approver: "Steward (G16)"
decisions_applied: "SS answers to INDEX section 7, 2026-10-01 (items marked R are PROVISIONAL until the J1 review); disposition accepted as proposed"
track_i_items: [TI-L0-03, TI-L0-06, TI-L0-28]
ledger_gap_ids: [bg_vidhi_floors-Earn.build_record, bg_vidhi_floors-Cost.baseline, bg_vidhi_floors-Carr.detector, bg_vidhi_floors-Build.history]
---
# bg_vidhi_floors — Vidhi registry — intent floors and floor items (14 + 409 = 423 rows; catalog_status DRAFT)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. SS answered the open questions on 2026-10-01: decisions are recorded in §4 and §7 (items marked (R) are PROVISIONAL until the J1 review).

## 0 · Identity — what the asset is

'Per-intent-class acharya floor + machine band header + ordered floor items: the compiled scope_tuple → contract input (D-2 Lane V-1)'. Targets `vidhi_intent_floors` (14) and `vidhi_floor_items` (409); the writer (`platform/python-sidecar/pipeline/orchestrator/writers/bg_vidhi_floors.py`, ON CONFLICT (intent) upsert at `:558`, DELETE statements at `:550,569`) mirrors the canonical TS registry `platform/src/lib/vidhi/registry_data.ts`, held in lockstep by a CI drift gate (`platform/scripts/census/check_vidhi_registry_parity.mjs`, run at `.github/workflows/ci.yml:1538`). **`catalog_status = DRAFT` is intentional** (migration 642, applied 2026-09-04): 12 of 14 intent floors are writer-tagged MANDATORY while `education_deepdive` and `progeny_deepdive` remain CANDIDATE (VIDHI-PŪRṆATĀ P-2, not ratified); the registry description says flipping to CURRENT 'would be fabricating settledness two floors don't have'. Depends on `bg_vidhi_primitives`; no declared dependents (census 0/0) though `platform/src/lib/vidhi/{types,registry_data}.ts` and `platform-mcp/src/resources/vidhi/` read the tables. Header comments in the TS file (52 primitives, 11 floors) are stale against the 60 / 14 the writer holds.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:807` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_vidhi_floors.py:526`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `vidhi_floor_items`; count_sql tables: `vidhi_intent_floors`, `vidhi_floor_items` | census CEN-R |
| live rows / floor | 423 / 423 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | DRAFT | census |
| depends_on (intra-L0, live) | `bg_vidhi_primitives` | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 0 / transitive 0 (every layer) | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `vidhi_floor_items`: 4 non-test py/ts/tsx files reference it (3 outside brahmagyan/ and bg_*.py writers): `types.ts`, `registry_data.ts`, `types.ts`; `vidhi_intent_floors`: 4 non-test py/ts/tsx files reference it (3 outside brahmagyan/ and bg_*.py writers): `types.ts`, `registry_data.ts`, `types.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | none; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 1d24dbed complete/build (2026-09-05) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 1 error(s) and 1 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-09-04): post-write integrity check failed: integrity_check_sql → False |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 1d24dbed complete/build (2026-09-05) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): vidhi_intent_floors (bg_vidhi_floors.py:555)); Vocab.identity (declared key (intent, item_order): 0 duplicate(s)); Build.completion; Build.contract; Build.count_integrity; Build.dag †; Build.dep_liveness; Build.exercised (7 executed run(s) of 8 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-05); Build.registered (@register in bg_vidhi_floors.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build PARTIAL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_vidhi_floors-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_vidhi_floors-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_vidhi_floors-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| bg_vidhi_floors-Build.history | Build | history | 1 error 2026-09-04 (`post-write integrity check failed`) and 1 abort; latest run complete; CF-10 \| ledger: measured: latest run complete, but 1 error(s) and 1 abort(s) on record. post-write integrity check failed: integrity_check_sql → False / required: the Build gate's claim |
| census: Ldgr (no reading) | Ldgr | detector | no recognised citation column on the target table; CF-08 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |
| layer instance §1.1.3 / TG-L0-024 | Build / certification | information (decided: DRAFT blocks certification, SS Q14) | DRAFT blocks certification while DRAFT (SS 2026-10-01); TGH-T3-21 records the missing tier clause |

## 3 · Disposition

**qualify (Q)** — agreed with the carried Q: DRAFT is the honest authority limit while two floors are unratified; the asset is retained and its limit kept explicit. T4 does not say what DRAFT blocks (TGH-T3-21).

Approver under Track A brief §10: **Steward (G16)**. Disposition accepted as proposed (SS 2026-10-01, Q10).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Register the existing CI parity gate as the Carr detector

- **Answers:** census Carr NO_DETECTOR; CF-07
- **Change:** the repository already runs a two-copy re-derivation: `check_vidhi_registry_parity.mjs` deep-compares the writer’s `--dump-json` output to `dump_vidhi_registry.ts` (the TS canonical source). That is a D3 check in all but name. Register it as this asset’s Carr detector (with its seeded-drift case) instead of building a new one; it covers the floors and the primitives.
- **Files / declaration / migration:** the inspector registry entry (Track E) pointing at `platform/scripts/census/check_vidhi_registry_parity.mjs`; no asset file changes
- **Failing-first test and mutation:** the gate’s own test: a seeded one-field drift must fail it (confirm it does before registering); mutation: edit one floor item in the TS file only → the gate fails
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 0 / transitive 0 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02

### FD-2 · DRAFT blocks certification; ratification after the milestone review

- **Answers:** registry description; TGH-T3-21; no census cell
- **Change:** decided (SS 2026-10-01, Q14): `catalog_status = DRAFT` blocks certification while DRAFT; SS ratifies the deep-dive floors (`education_deepdive`, `progeny_deepdive`) after the milestone independent review. Keep the DRAFT status and expose the per-floor MANDATORY/CANDIDATE tag as data.
- **Files / declaration / migration:** none beyond reading the existing tag; a declarations note
- **Failing-first test and mutation:** a query returns 12 MANDATORY and 2 CANDIDATE floors; mutation: flip a tag → the count moves
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 0 / transitive 0 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none
- **Gate it moves:** Null/Earn (a declared authority limit)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (decided)
- **Decision:** ANSWERED by SS 2026-10-01 (Q14): `catalog_status = DRAFT` blocks certification while DRAFT; SS ratifies the deep-dive floors after the milestone independent review.

### FD-3 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `bg_vidhi_floors.py`, `registry_data.ts` for any composed text column; declare `[]` expected: floor and band text is authored content mirrored from the TS registry, not composed from data; confirm no f-string in `bg_vidhi_floors.py`
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 0 / transitive 0 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-4 · Ldgr: make the source column readable

- **Answers:** census `Ldgr.source_presence` has no reading; CF-08
- **Change:** declare that the source of each row is carried in the floor items’ source pointers (to be named at design time; the saved census found no recognised citation column) so the inspector can read it; if the table has no source column the gap is real and is an output change (added by migration + writer)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` (`carriage`) and, only if no column exists, the writer + a migration
- **Failing-first test and mutation:** inspector reads PASS/FAIL on the declared column; a blank source must read FAIL
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 0 / transitive 0 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (declaration); a data fix would be a separate design
- **Gate it moves:** Ldgr (no reading → PASS/FAIL)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T3-01 (the Ldgr source is undefined in the gate map)

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* register the existing CI parity gate
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-08** — Ldgr: assets with no recognised citation column (16 "no reading"). *This asset:* no recognised citation column
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* 1 error, 1 abort; latest run complete

## 5 · Semantic fingerprint contract (for E5.5)

Natural keys `(intent, item_order)` (census, 0 duplicates) for `vidhi_floor_items` and `intent` for `vidhi_intent_floors`. Fingerprint over the ordered `(intent, item_order, item, band)` plus the MANDATORY/CANDIDATE tag; volatile: `created_at`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 14 intent floors and 409 ordered items as ratified or tagged; the DRAFT status and its stated reason.
- **Carriage check chosen (T4 §4.1; one only):** D3-equivalent: the existing two-copy parity gate (TS canonical source vs Python seed).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Decisions applied (SS answered INDEX section 7 on 2026-10-01; no question is open in this brief)

Disposition accepted as proposed (Q10). Items marked (R) are PROVISIONAL until the J1 review.

1. ANSWERED by SS 2026-10-01 (Q14): `catalog_status = DRAFT` blocks certification while DRAFT; SS ratifies the deep-dive floors after the milestone independent review.
2. CF-07: ANSWERED by SS 2026-10-01 (Q13): D1 anchor-term matching is accepted as the L0 carriage detector, but the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled. Ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, PROVISIONAL until the J1 review); it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.
3. CF-10: ANSWERED by SS 2026-10-01 (Q11): yes: Build.history counts only runs since the last change to the writer or the registry row.

**Track I items arising (see INDEX section 8):** TI-L0-03, TI-L0-06, TI-L0-28.
