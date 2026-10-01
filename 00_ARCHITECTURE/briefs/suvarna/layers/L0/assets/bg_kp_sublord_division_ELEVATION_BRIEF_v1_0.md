---
asset_id: bg_kp_sublord_division
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
track_i_items: [TI-L0-06]
ledger_gap_ids: [bg_kp_sublord_division-Idem.pattern, bg_kp_sublord_division-Earn.build_record, bg_kp_sublord_division-Cost.baseline, bg_kp_sublord_division-Carr.detector, bg_kp_sublord_division-Build.history]
---
# bg_kp_sublord_division — KP sub-lord division of the sidereal zodiac (249 rows)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. SS answered the open questions on 2026-10-01: decisions are recorded in §4 and §7 (items marked (R) are PROVISIONAL until the J1 review).

## 0 · Identity — what the asset is

ADJUDICATION-7 Part 1: the canonical 249-fold Krishnamurti Paddhati sub-lord division: 243 Vimśottarī-proportional sub-segments (sub arc = lord_years/9 degrees, sequence starting from the nakshatra lord) cut at the 12 rāśi boundaries, plus 6 cut-induced segments (seed description; `platform/python-sidecar/pipeline/orchestrator/writers/bg_kp_sublord_division.py:1-18`). Stored in SIDEREAL longitude space with no ayanāṃśa key (the division is ayanāṃśa-invariant; the ayanāṃśa enters only when a chart is projected, an L1 concern). ON CONFLICT upsert (`brahmagyan/l0_kp_sublord_division.py:316`). Depends on `bg_nakshatra` as a build-ordering edge (the star-lord cross-check reads `reference_nakshatra` when present and otherwise reports `unverified`, never a pass: `bg_kp_sublord_division.py:19-30`). Declared dependent `ga_nakshatra` (census direct 1 / transitive 57). `source_citation` 249/249.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:932` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_kp_sublord_division.py:44`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bg_kp_sublord_division`; count_sql tables: `bg_kp_sublord_division` | census CEN-R |
| live rows / floor | 249 / 249 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | `bg_nakshatra` | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 1 / transitive 57 (every layer); named: `ga_nakshatra` | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `bg_kp_sublord_division`: 8 non-test py/ts/tsx files reference it (5 outside brahmagyan/ and bg_*.py writers): `ga_nakshatra.py`, `ga_kp_significators.py`, `stage3_clocks.py`, `producer_editorial_review.ts`, `school_conventions.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | none; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 21df3b6a complete/build (2026-09-04) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 0 error(s) and 1 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 21df3b6a complete/build (2026-09-04) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Ldgr.source_presence (source_citation populated on 249/249 rows); Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): bg_kp_sublord_division (brahmagyan/l0_kp_sublord…); Vocab.identity (declared key (table_version, division_index): 0 duplicate(s)); Build.completion; Build.contract; Build.count_integrity; Build.dag †; Build.dep_liveness; Build.exercised (3 executed run(s) of 4 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-04); Build.registered (@register in bg_kp_sublord_division.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build PARTIAL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_kp_sublord_division-Idem.pattern | Idem | stale | saved census Idem.pattern reads PASS (ON CONFLICT upsert at `l0_kp_sublord_division.py:316`) \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_kp_sublord_division-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_kp_sublord_division-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_kp_sublord_division-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| bg_kp_sublord_division-Build.history | Build | history | CF-10: a record of past errors/aborts; the latest run completed \| ledger: measured: latest run complete, but 0 error(s) and 1 abort(s) on record. / required: the Build gate's claim |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — the table is a derivation with its own documented cross-check, all applicable census cells PASS except the history record; it is the best candidate in L0 for a deterministic D3.

Approver under Track A brief §10: **Steward (G16)**. Disposition accepted as proposed (SS 2026-10-01, Q10).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Carr detector — D3 recomputation of the 249 divisions

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** recompute the division from the Vimśottarī year-proportions (sub arc = lord_years/9 within each nakshatra, started from the nakshatra lord, cut at rāśi boundaries: R1 + R2 of the module) and compare `(division_index, start_deg, end_deg, nakshatra_lord, sub_lord)` to the stored rows; the star-lord cross-check against `reference_nakshatra` becomes a counted comparison (matched / unverified / mismatched) rather than a note. Seeded mismatch: shift one boundary → must be caught. Fully deterministic; no oracle.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 1 / transitive 57 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-2 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `brahmagyan/l0_kp_sublord_division.py` for any composed text column; declare `[]` expected (numeric division; citation literal)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 1 / transitive 57 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-3 · Dens attribution

- **Answers:** census `Dens.served` N/A (no registry module references the table); `N22/dens_repair_needs` lists it among assets with no reference anywhere; CF-04
- **Change:** its consumer is L1 (`ga_nakshatra`), not an L0 capability module; Dens is therefore N/A by absence of a served surface, which must be declared by `carriage.served_surface = false` with evidence rather than left as an inspector inference.
- **Files / declaration / migration:** `asset_declarations.json` (`carriage`)
- **Failing-first test and mutation:** declarations validation
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 1 / transitive 57 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none
- **Gate it moves:** Dens (N/A with cause)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: N-22 applicability rule

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3 above
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-04** — Dens (serving density) on the L0 served modules: applies wherever a served surface is reached; `uniform_authority` (R). *This asset:* N/A by absence of a served surface
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* 1 abort on record; latest run complete

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(table_version, division_index)` (census, 0 duplicates). Upsert; the semantic fingerprint is the ordered `(division_index, start, end, nakshatra_lord, sub_lord)` tuple set at one `table_version`; volatile: `created_at`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 249-fold geometry (243 + 6), its ayanāṃśa-invariant sidereal storage and the disclosed sub-sub/pāda scope limit.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation from the Vimśottarī proportions).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Decisions applied (SS answered INDEX section 7 on 2026-10-01; no question is open in this brief)

Disposition accepted as proposed (Q10). Items marked (R) are PROVISIONAL until the J1 review.

1. CF-07: ANSWERED by SS 2026-10-01 (Q13): D1 anchor-term matching is accepted as the L0 carriage detector, but the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled. Ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, PROVISIONAL until the J1 review); it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.
2. CF-04: ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).
3. CF-10: ANSWERED by SS 2026-10-01 (Q11): yes: Build.history counts only runs since the last change to the writer or the registry row.

**Track I items arising (see INDEX section 8):** TI-L0-06.
