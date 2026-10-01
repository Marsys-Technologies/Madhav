---
asset_id: bg_dignity_reference
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
ledger_gap_ids: [bg_dignity_reference-Earn.build_record, bg_dignity_reference-Cost.baseline, bg_dignity_reference-Dens.served, bg_dignity_reference-Carr.detector]
---
# bg_dignity_reference — Planetary dignity and state reference (5 tables, 151 rows)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Seeds five classical reference tables — `bg_dignity_reference` (9 rows: exaltation/debilitation/mūlatrikoṇa/own signs per graha), `bg_graha_naisargika_friendship` (72), `bg_avastha_schemes` (35), `bg_motion_state_thresholds` (27), `bg_combustion_orbs` (8) — as static Python data, ON CONFLICT DO UPDATE (`platform/python-sidecar/pipeline/orchestrator/writers/bg_dignity_reference.py:1-24`; the seed logic originally lived in migration 250). No `brahmagyan/` module backs it. `classical_citation` is populated on 9/9 rows of the first table. Declared dependent: `ka_vighnakara` (migration 730; census direct 1 / transitive 23). Served surface: the saved reach names `platform-mcp/src/tools/register_p1_reference.ts` and `kala_views/ahead.ts`, `now.ts`; the L0 registry modules mention the asset only in comments, so `Dens.served` reads NO_DETECTOR (cannot be attributed by code).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:732` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_dignity_reference.py:347`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bg_dignity_reference`; count_sql tables: `bg_dignity_reference`, `bg_avastha_schemes`, `bg_combustion_orbs`, `bg_graha_naisargika_friendship`, `bg_motion_state_thresholds` | census CEN-R |
| live rows / floor | 151 / 151 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 1 / transitive 23 (every layer); named: `ka_vighnakara` | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `bg_avastha_schemes`: 3 non-test py/ts/tsx files reference it (1 outside brahmagyan/ and bg_*.py writers): `source_query_availability.ts`; `bg_combustion_orbs`: 7 non-test py/ts/tsx files reference it (4 outside brahmagyan/ and bg_*.py writers): `ka_vighnakara.py`, `bo_laksana.py`, `ga_condition_writer.py`, `source_query_availability.ts`; `bg_dignity_reference`: 16 non-test py/ts/tsx files reference it (7 outside brahmagyan/ and bg_*.py writers): `ga_condition_writer.py`, `route.ts`, `producer_editorial_review.ts`, `source_query_availability.ts`, `now.ts` +2; `bg_graha_naisargika_friendship`: 5 non-test py/ts/tsx files reference it (2 outside brahmagyan/ and bg_*.py writers): `ga_condition_writer.py`, `source_query_availability.ts`; `bg_motion_state_thresholds`: 4 non-test py/ts/tsx files reference it (2 outside brahmagyan/ and bg_*.py writers): `ga_condition_writer.py`, `source_query_availability.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `ahead.ts`, `now.ts`, `register_p1_reference.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 2ec6d233 complete/build (2026-09-04) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | NO_DETECTOR | NO_DETECTOR — no capability module's code references bg_dignity_reference; named in comments only in: index.ts, query_avastha_schemes.ts, query_combustion_orbs.ts, query_graha_naisargika_friendship.ts, query_motion_state_thresholds.ts — the served surface cannot be attributed by code (never the closable N/A) |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 2ec6d233 complete/build (2026-09-04) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Ldgr.source_presence (classical_citation populated on 9/9 rows); Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): bg_dignity_reference (bg_dignity_reference.py:41…); Vocab.identity (declared key (graha): 0 duplicate(s)); Build.completion; Build.contract; Build.count_integrity; Build.dag †; Build.exercised (3 executed run(s) of 3 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-04); Build.history; Build.registered (@register in bg_dignity_reference.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build NO_DETECTOR.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_dignity_reference-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_dignity_reference-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_dignity_reference-Dens.served | Dens | real as measured at rev 1; applicability and re-measure pending | CF-04 \| ledger: measured: 5 module(s): index.ts, query_avastha_schemes.ts, query_combustion_orbs.ts, query_graha_naisargika_friendship.ts, query_motion_state_thresholds.ts; declaring de… |
| bg_dignity_reference-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — all applicable Build/Idem/Vocab cells PASS; open items are detectors and the served-surface attribution. One seam is flagged for a read-only check (below): the combustion orbs exist in two L0 assets.

Approver under Track A brief §10: **Steward (G16)**. 

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Duplicate-authority parity check (combustion orbs)

- **Answers:** no census cell and no ledger row (no detector exists); found by reading `l0_formula_constants.py:28-48` against `bg_dignity_reference.py` (combustion rows): the same orbs (Moon 12, Mars 17/15, Mercury 14/12, Jupiter 11/9, Venus 10/8, Saturn 15/12, Rahu/Ketu 9/7) are held both in `brahma_formula_constants` (`combustion_orbs`, citing "Already in bg_combustion_orbs; ka_vighnakara must read from here") and in `bg_combustion_orbs`
- **Change:** add a parity test that the two copies agree value by value (and, if SS wants one authority, name which asset owns the value and make the other read it). The values agree where visible in code; no divergence is claimed. `dignity_scores` in formula_constants was not compared.
- **Files / declaration / migration:** a test under `platform/python-sidecar/pipeline/orchestrator/writers/tests/` comparing the two seed structures; no asset file changes
- **Failing-first test and mutation:** failing-first: perturb one copy in a fixture → test fails
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (test only)
- **Gate it moves:** Carr/Vocab (independent-authority check; no registered gate cell yet)
- **Fix class:** detector/tooling (test); **buildable before J1:** tier-independent
- **Question for SS:** Is the second copy of the combustion orbs (formula_constants vs bg_combustion_orbs) intended redundancy, or a consolidation question (T2 §10.1 C)?

### FD-2 · Carr detector — D1 against cited sources

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** each of the 151 rows carries a `classical_citation` (BPHS, Jātaka Pārijāta, Phaladīpikā, Uttara Kālāmṛta, Sārāvalī per the writer header); resolve each cited text to the corpus and test the anchor terms; report matched/unmatched.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-3 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `bg_dignity_reference.py` (data structures L186-340) for any composed text column; declare `[]` expected: the avasthā schemes carry JSON determination rules and short notes as literals (confirm there is no f-string)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-4 · Dens: attribute the served surface

- **Answers:** census `Dens.served` NO_DETECTOR (comment-only mentions in the L0 registry modules); CF-04
- **Change:** the real readers are `platform-mcp/src/tools/register_p1_reference.ts` and the Kāla views; Dens cannot be read until a served read of the table is attributable by code (declared `carriage.served_surface` with `read_evidence` as a repo path:line of a non-test SQL read). Add the carriage declaration with evidence, then CF-04 applies.
- **Files / declaration / migration:** `asset_declarations.json` (`carriage`/`read_evidence`)
- **Failing-first test and mutation:** declarations validation; inspector reads a served read
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none
- **Gate it moves:** Dens (NO_DETECTOR → FAIL/PASS/N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: N-22 + TGH-T3-26
- **Question for SS:** Does Dens apply to this reference table at all (CF-04)?

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D1 above
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-04** — Dens (serving density) on the L0 served modules. *This asset:* NO_DETECTOR by attribution, not FAIL
- **CF-12** — Idem: an orphan census for upsert-only writers (the Idem PASS does not test accretion). *This asset:* upsert over five tables, no DELETE found

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `graha` for `bg_dignity_reference` (census, 0 duplicates); each sub-table has its own key (friendship `(graha, other)`, schemes, thresholds, orbs: to be read from the DDL at design time). Upsert; volatile: `id` surrogate (dark column), `created_at`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 151 classical reference rows with their citations; the per-graha dignity boundaries.
- **Carriage check chosen (T4 §4.1; one only):** D1 (source correspondence); the duplicated combustion orbs add an internal-consistency check.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Combustion orbs held in two L0 assets: redundancy or consolidation candidate?
