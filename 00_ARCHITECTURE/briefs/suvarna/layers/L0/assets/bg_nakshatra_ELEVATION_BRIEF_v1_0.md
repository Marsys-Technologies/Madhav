---
asset_id: bg_nakshatra
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
track_i_items: [TI-L0-03, TI-L0-05, TI-L0-06, TI-L0-16]
ledger_gap_ids: [bg_nakshatra-Idem.pattern, bg_nakshatra-Earn.build_record, bg_nakshatra-Cost.baseline, bg_nakshatra-Complete.depth, bg_nakshatra-Carr.detector]
---
# bg_nakshatra — Nakshatra reference (28 nakshatras incl. Abhijit, 108 padas, compatibility matrices; 2,857 rows)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. SS answered the open questions on 2026-10-01: decisions are recorded in §4 and §7 (items marked (R) are PROVISIONAL until the J1 review).

## 0 · Identity — what the asset is

Registry description: 'Global nakshatra reference — 28 nakshatras (incl. Abhijit), 108 padas, full Ashtakuta + supplementary compatibility matrices (2721 rows)'; the three tables sum to 28 + 108 + 2,721 = 2,857 (`reference_nakshatra`, `reference_nakshatra_pada`, `reference_nakshatra_matrix`). Delete-then-insert of the three tables (`platform/python-sidecar/brahmagyan/l0_nakshatra.py:1395-1397`). Declared dependents `bg_kp_sublord_division` and `ga_nakshatra` (census direct 2 / transitive 58). Complete.depth: `basis_above`, `basis_below`, `net_result` never populated (information). **Observation (no detector):** this reference holds 28 nakshatras while the ontology `nakshatra` class holds 27 (layer instance §2.6); the 28th, Abhijit, has a reference row but no ontology identity.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:514` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_nakshatra.py:20`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `reference_nakshatra`; count_sql tables: `reference_nakshatra`, `reference_nakshatra_pada`, `reference_nakshatra_matrix` | census CEN-R |
| live rows / floor | 2857 / 2,857 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 2 / transitive 58 (every layer); named: `bg_kp_sublord_division`, `ga_nakshatra` | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `reference_nakshatra`: 8 non-test py/ts/tsx files reference it (5 outside brahmagyan/ and bg_*.py writers): `ga_nakshatra.py`, `ga_nakshatra_emitters.py`, `ga_sensitive_degree_writer.py`, `route.ts`, `register_p1_reference.ts`; `reference_nakshatra_matrix`: 1 non-test py/ts/tsx files reference it (0 outside brahmagyan/ and bg_*.py writers); `reference_nakshatra_pada`: 5 non-test py/ts/tsx files reference it (4 outside brahmagyan/ and bg_*.py writers): `ga_nakshatra.py`, `ga_nakshatra_emitters.py`, `route.ts`, `register_p1_reference.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `register_p1_reference.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Complete (information, D3) | Complete.depth | PARTIAL | 28 rows, 46 cols; fully populated 33; NEVER populated ['basis_above', 'basis_below', 'net_result'] |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Idem.pattern † (the asset's own table(s) replaced by delete-then-insert: reference_nakshatra_matrix (brahmagyan/l0_nakshatra.…); Vocab.identity (declared key (nakshatra_id): 0 duplicate(s)); Build.completion; Build.contract; Build.count_integrity; Build.dag †; Build.exercised (3 executed run(s) of 3 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-04); Build.history; Build.registered (@register in bg_nakshatra.py; registry agrees); Build.target †; Count.floor.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build NO_DETECTOR.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_nakshatra-Idem.pattern | Idem | stale | ledger row from an earlier run; saved census Idem.pattern reads PASS \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_nakshatra-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_nakshatra-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_nakshatra-Complete.depth | Complete | information | columns never populated (D3: information, not a blocker) \| ledger: measured: 28 rows, 46 cols; fully populated 33; NEVER populated ['basis_above', 'basis_below', 'net_result'] / required: the Complete gate's claim |
| bg_nakshatra-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| census: Ldgr (no reading) | Ldgr | detector | no recognised citation column on the target table; CF-08 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — no failing cell; the identity observation is a Vocab question (rule 1/2: every reference identity resolves through the set), decided by SS (Q4) as a declared exception; not registered as a gap because no detector measures it.

Approver under Track A brief §10: **Steward (G16)**. Disposition accepted as proposed (SS 2026-10-01, Q10).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Abhijit: declared exception (27-id class stays canonical)

- **Answers:** no census cell and no ledger row (no detector exists); read from the seed description (28) against layer instance §2.6 (nakshatra 27); CF-09
- **Change:** decided (SS 2026-10-01, Q4): Abhijit (the 28th reference row) is a declared exception (classically intercalary); the 27-id `nakshatra` ontology class stays canonical and no ontology row is added. Record the exception in the declarations so a consumer joining on `canonical_id` does not drop or invent it; a read-only join census confirms exactly one reference id (Abhijit) outside the 27.
- **Files / declaration / migration:** a read-only census query (tier-independent) then, if chosen, `brahmagyan/l0_ontology.py` (ENTITIES) + `l0_nakshatra.py`
- **Failing-first test and mutation:** failing-first: the join census reports the reference ids with no ontology row (1 expected: Abhijit); after the fix it reports 0 or the declared exception; mutation: add an unknown id → reported
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 2 / transitive 58 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (declaration)
- **Gate it moves:** Vocab (rules 1-2)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (decided)
- **Decision:** ANSWERED by SS 2026-10-01 (Q4): the normalisation rule lives in the `bg_ontology` writer, the one authority; the vocabulary release id goes in the first wave if it is cheap; for the 11 two-class ids take the recommended option (a, class-aware resolvers) unless it changes served ids (then REVIEW to SS); of bhrigu_samhita, jaimini_sutram, lal_kitab_text keep any with a consumer and remove the rest; Abhijit is a declared exception (classically intercalary) and the 27-id class stays canonical.

### FD-2 · Carr detector — D3 on the compatibility matrix

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** recompute a sample of Ashtakūṭa scores from the kūṭa rules (the arithmetic of varṇa/vaśya/tārā/yoni/graha-maitrī/gaṇa/bhakūṭ/nāḍī) and compare to `reference_nakshatra_matrix`; the 28/108 base rows are checked D1 against the cited tables. Seeded mismatch must be caught.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 2 / transitive 58 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-3 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `brahmagyan/l0_nakshatra.py` for any composed text column; declare `[]` expected (literal reference rows) after reading `l0_nakshatra.py`
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 2 / transitive 58 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-4 · Ldgr: make the source column readable

- **Answers:** census `Ldgr.source_presence` has no reading; CF-08
- **Change:** declare that the source of each row is carried in the citation column on `reference_nakshatra` (to be named at design time; saved census found no recognised column) so the inspector can read it; if the table has no source column the gap is real and is an output change (added by migration + writer)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` (`carriage`) and, only if no column exists, the writer + a migration
- **Failing-first test and mutation:** inspector reads PASS/FAIL on the declared column; a blank source must read FAIL
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 2 / transitive 58 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (declaration); a data fix would be a separate design
- **Gate it moves:** Ldgr (no reading → PASS/FAIL)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T3-01 (the Ldgr source is undefined in the gate map)

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-09** — Identity and normalisation reconciliation at the authority (bg_ontology and its consumers). *This asset:* Abhijit identity observation
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3 on the matrix
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-08** — Ldgr: assets with no recognised citation column (16 "no reading"). *This asset:* no recognised citation column

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `nakshatra_id` for `reference_nakshatra` (census, 0 duplicates); the pada and matrix tables have their own keys (read at design time). Delete-then-insert of three tables: fingerprint is the ordered row sets; volatile: `created_at`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 28/108/2,721 reference rows and their Ashtakūṭa construction.
- **Carriage check chosen (T4 §4.1; one only):** D3 (recompute sampled compatibility scores) and D1 for the base tables.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Decisions applied (SS answered INDEX section 7 on 2026-10-01; no question is open in this brief)

Disposition accepted as proposed (Q10). Items marked (R) are PROVISIONAL until the J1 review.

1. ANSWERED by SS 2026-10-01 (Q4): the normalisation rule lives in the `bg_ontology` writer, the one authority; the vocabulary release id goes in the first wave if it is cheap; for the 11 two-class ids take the recommended option (a, class-aware resolvers) unless it changes served ids (then REVIEW to SS); of bhrigu_samhita, jaimini_sutram, lal_kitab_text keep any with a consumer and remove the rest; Abhijit is a declared exception (classically intercalary) and the 27-id class stays canonical.
2. CF-09: ANSWERED by SS 2026-10-01 (Q4): the normalisation rule lives in the `bg_ontology` writer, the one authority; the vocabulary release id goes in the first wave if it is cheap; for the 11 two-class ids take the recommended option (a, class-aware resolvers) unless it changes served ids (then REVIEW to SS); of bhrigu_samhita, jaimini_sutram, lal_kitab_text keep any with a consumer and remove the rest; Abhijit is a declared exception (classically intercalary) and the 27-id class stays canonical. ANSWERED by SS 2026-10-01 (Q5): authority-side declaration with NO stored-value change: `bg_ephemeris` declares `node: TRUE`; consumers needing MEAN must not read node values from it (a check, Track I item); body-name normalisation is declared the same way. BEFORE any wave touches `bg_ephemeris` or `bg_texts`, SS notifies Pravāha (Exec sends SS an ASK first).
3. CF-07: ANSWERED by SS 2026-10-01 (Q13): D1 anchor-term matching is accepted as the L0 carriage detector, but the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled. Ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, PROVISIONAL until the J1 review); it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.

**Track I items arising (see INDEX section 8):** TI-L0-03, TI-L0-05, TI-L0-06, TI-L0-16.
