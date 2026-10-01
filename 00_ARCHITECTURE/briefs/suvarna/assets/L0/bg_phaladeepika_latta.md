---
asset_id: bg_phaladeepika_latta
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
ledger_gap_ids: [bg_phaladeepika_latta-Idem.pattern, bg_phaladeepika_latta-Earn.build_record, bg_phaladeepika_latta-Cost.baseline, bg_phaladeepika_latta-Carr.detector]
---
# bg_phaladeepika_latta — Lattā vedha rule table (Phaladīpikā Adh. XXVI, 8 rows)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

ADJUDICATION-11 Part 4: the Lattā (obstruction-point) rule of Phaladīpikā Adh. XXVI PG338-339, Śloka 42-44, 'REAL and cited, transcribed verbatim', 8 grahas; **Ketu is deliberately absent because its counting rule was not found in the retrieved passage** (seed description). The module records the verbatim source text and the corpus chunk ids it was read from (`platform/python-sidecar/brahmagyan/l0_phaladeepika_vedha.py:1-40`: chunks `phaladeepika_pg0338_c01` + `…pg0339_c01`, read-only, before authoring). ON CONFLICT upsert (`:160`); `source_citation` 8/8. Consumed by `ka_vedha_gochara` (census direct 1 / transitive 31). Sibling of `bg_vedha_malefic_scale` (same module).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1001` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_phaladeepika_vedha.py:42`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bg_phaladeepika_latta`; count_sql tables: `bg_phaladeepika_latta` | census CEN-R |
| live rows / floor | 8 / 8 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 1 / transitive 31 (every layer); named: `ka_vedha_gochara` | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `bg_phaladeepika_latta`: 6 non-test py/ts/tsx files reference it (4 outside brahmagyan/ and bg_*.py writers): `logic.py`, `writer.py`, `query_vedha_gochara.ts`, `producer_editorial_review.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
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
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Ldgr.source_presence (source_citation populated on 8/8 rows); Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): bg_phaladeepika_latta (brahmagyan/l0_phaladeepik…); Vocab.identity (declared key (table_version, graha): 0 duplicate(s)); Build.completion; Build.contract; Build.count_integrity; Build.dag †; Build.exercised (2 executed run(s) of 2 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-04); Build.history; Build.registered (@register in bg_phaladeepika_vedha.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build NO_DETECTOR.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_phaladeepika_latta-Idem.pattern | Idem | stale | saved census Idem.pattern reads PASS (upsert at `l0_phaladeepika_vedha.py:160`) \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_phaladeepika_latta-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_phaladeepika_latta-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_phaladeepika_latta-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — a model L0 asset: cited verbatim from corpus chunks, with an honest abstention for the one row the source does not support. No failing cell.

Approver under Track A brief §10: **Steward (G16)**. 

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Carr detector — D1 against the named chunks

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** the strongest D1 in L0: compare the stored rows to the verbatim text of chunks `phaladeepika_pg0338_c01`/`pg0339_c01` (both in `classical_text_chunks`), e.g. that each graha’s counting rule (12th from the Sun, 3rd from Mars, 6th from Jupiter, …) matches the passage’s wording; report matched/unmatched. Seeded mismatch: alter one count → must be caught. Also assert that Ketu has no row (the abstention is preserved).
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-2 · Declared null reason for the Ketu abstention

- **Answers:** Track A §5 (null with a reason is a decided class, D3); no census cell
- **Change:** record in the declarations that Ketu has no row because the source passage states no counting rule, so the Null gate reads a declared reason rather than an unexplained absence.
- **Files / declaration / migration:** `asset_declarations.json` (null reason) — Track E file
- **Failing-first test and mutation:** declarations validation; mutation: add a Ketu row without source support → the D1 check fails
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none
- **Gate it moves:** Null
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (null-with-reason is decided)

### FD-3 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `brahmagyan/l0_phaladeepika_vedha.py` for any composed text column; declare `[]` expected (`effect_description` is verbatim)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D1 against the named chunks
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration (`effect_description` is verbatim source)
- **CF-12** — Idem: an orphan census for upsert-only writers (the Idem PASS does not test accretion). *This asset:* upsert, no DELETE found

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(table_version, graha)` (census, 0 duplicates). Upsert; volatile: `created_at`. A rebuild must keep exactly 8 rows and no Ketu row.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the eight verbatim Lattā counting rules and the Ketu abstention.
- **Carriage check chosen (T4 §4.1; one only):** D1 (verbatim correspondence to the named chunks).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2
