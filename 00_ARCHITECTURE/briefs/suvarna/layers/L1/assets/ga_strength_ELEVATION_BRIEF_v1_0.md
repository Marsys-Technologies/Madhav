---
asset_id: ga_strength
layer: L1 Gaṇita (ga_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L1 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L1.json` (generated 2026-09-30T20:22:28+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr), with the `ga_prashna` cells read from the post-grant rerun `census/after_reader_grant/census_L1.json` (generated 2026-09-30T20:30:02+05:30; every other cell identical). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 at the base commit (7 on origin/main 066c58587: the revision note names a NA_CAUSES addition for Carr; the criterion bodies were not diffed beyond that) and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L1/L1_LAYER_INSTANCE_v1_0.md (1.0-rev1, PROVISIONAL)"
base_commit: "main 3311b0a06"
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16)"
decisions_applied: "SS answers logged 2026-10-01 and applied: Build.history window (L0 Q11: yes, runs since the last writer/registry change), Dens applicability (L0 Q2: wherever a served surface is reached; mixed-authority tables need a real tier), count_sql scope (L0 Q19: primary table, multi-table declared), the argala authority answer (L1 is the authority, L2 references); I-11 diagnosis (RLS) from the independent review; dispositions proposed, not yet answered by SS; SS ruling N-62 (2026-10-02) on the L1 decision sheet: every recommendation accepted, (R) items provisional until J1, recorded at the end of this brief"
track_i_items: [I-11, I-13, I-30, I-27]
ledger_gap_ids: [ga_strength-Idem.pattern, ga_strength-Build.completion, ga_strength-Earn.build_record, ga_strength-Cost.baseline, ga_strength-Dens.served, ga_strength-Build.history, ga_strength-Carr.detector]
---
# ga_strength — Ṣaḍbala, aṣṭakavarga, vimśopaka and bhāva-bala (strength tables)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Ṣaḍbala (7 rows per graha), aṣṭakavarga (bindus and pinda/bhinna/sarva), vimśopaka and bhāva-bala per ayanamsha into `chart_facts` (`ga_writers/ga_strength_writer.py:1-40`). Pass 1 is the real PyJHora computation (`pyjhora_adapter/strength.py`); pass 2 is, by the writer's own admission, a bounds/consistency guard and "NOT a second independent recomputation" (`:13-22`); the row tier is the lowest of the two verifiers' outputs through `_TIER_RANK` (`:1855`), the M-22 fix that replaced an unconditional `two_pass_verified` (`:1848-1859`). Rahu/Ketu carry a labelled `computed_extension` and `not_defined_for_nodes` where tradition defines no ṣaḍbala. Idempotency: category-scoped delete-then-insert on `chart_facts`.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data; prose_fields declared `['citation_human']` | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1151` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_strength.py:8` (`run`, light; `rows_inserted = total_chart_facts_rows`); registry `has_writer` = True | writers dir; census `Build.registered` |
| target table(s) | `chart_facts` (no registry `target_table`: partition by `count_sql` over `graha_shadbala_%`, `graha_ishta_phala`, `graha_kashta_phala`, `%vimsopaka%`, `ashtakavarga_%`, `%bhava_bala%`, `graha_saptavargaja_bala_component`, `graha_%_bala_per_varga`) | census CEN-R (`target_table`, `count_sql_tables`) |
| live rows / floor | 14,141 / 13,621 (Δ +520); `asset_throughput` lit / **13,715**; seed floor literal 13621 (migration 650: measured minimum across three charts) | census `live_rows`; floor and throughput from the layer instance §1.1 (live registry read 2026-09-30) |
| catalog_status | CURRENT | census |
| depends_on (live, 2026-09-30) | `ga_positions`, `ga_vargas` (live and seed); the writer reads `chart_divisionals` (`:1234-1236`, varga positions) | layer instance §2.5 |
| blast radius | live registry incl. migration 1210 (applied; verified live 2026-10-01 14:37Z per the independent review): direct 5; census (2026-09-30, pre-1210): direct 5 / transitive 56; seed + 1210 reconstruction names 5 direct dependent(s): `bo_laksana`, `ga_sade_sati`, `ga_structural`, `ga_vichara`, `ka_sangam` | census `blocking_radius`; live count from the independent review; names reconstructed from `asset_registry_seed.ts` + `platform/migrations/1210_asset_registry_direct_edges.sql` (other migrations also edit `depends_on`, so the reconstruction can differ from the live registry) |
| code readers / served surface | `get_strength.ts:189` (declarations `read_evidence`, a `chart_facts` read); `reading_checklist.ts` and 56 other modules reach `chart_facts` by table; `Dens.served` cannot attribute it (census: named in comments only in `get_dasha_lord_capability.ts`) | census `reach.modules`; layer instance §1.2 |
| role / scoring mode | DP04 condition decomposition (strength components with units); 5 direct / 56 transitive dependents | layer instance §0.2, §4.4 (contribution layer; Computational correctness, T1 §11) |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: as the frontmatter `census_revision_used` (not repeated here).

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count). `Null.*` and `Narr.*` did not exist in the saved census.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.completion | FAIL | build record rows_written=13715 disagrees with live=14141 (count_sql total over 1 table(s): chart_facts; chart 482012f1) |
| Build | Build.history | PARTIAL | latest run complete, but 7 error(s) and 9 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-07-14): BLOCKED: upstream dependency(ies) ga_vargas did not complete in this run; skipped to avoid building on incomplete data |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run aa9602ce complete/build (2026-09-07) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run aa9602ce complete/build (2026-09-07) |
| Dens | Dens.served † | NO_DETECTOR | NO_DETECTOR — no capability module's code references ga_strength; named in comments only in: get_dasha_lord_capability.ts — the served surface cannot be attributed by code (never the closable N/A) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | see the offline reading below |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Count.floor; Build.exercised; Build.dep_liveness.

Information (never blockers, D3): Reach.fields NOT_GENERIC — no target_table declared: no table to census at field level; Complete.width NOT_GENERIC — no declared universe for this asset — declaring one is the first width gap.



**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; `NA_RULE_DECISIONS` is empty on main, so a measured N/A reads NO_DETECTOR; mixes old measurements with new rules; not a re-measure and not a certification; `_evidence/rollup_saved_L1.json` beside this file): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build FAIL.

**Offline re-scan of two criteria the saved census predates** (main's own code over this tree and the saved record, no database; indicative): Dens.served rev 4 reads **NO_DETECTOR** — NO_DETECTOR — 1 module(s) reach it by code: reading_checklist.ts, but no served `SELECT ... FROM` its table was found (no served select): whether it is served cannot be told by code (the saved rev-1 reading was NO_DETECTOR); Null/Narr graders over the declarations file 1.6.0 plus DDL-derived columns (`_evidence/narr_null_offline_L1.json`; `*` = INCONCLUSIVE because no row data was read): agree PASS; checkable NO_DETECTOR*; fidelity_test PARTIAL; lint NO_DETECTOR; schema_default PARTIAL; blank_rows NO_DETECTOR*.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **SS question** = real or not depends on a ruling; **artefact** = a saved census cell that reads a measurement the inspector's role could not make (pending a read by a role that can). A row naming several classes counts under its leading label.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell, or this brief) | gate | class | note |
|---|---|---|---|
| ga_strength-Build.completion | Build | real | FAIL: `rows_written` 13,715 vs live 14,141 (+426). The asset's `count_sql` predicate overlaps rows `fact_category_ownership` assigns to `ga_structural` (420 rows, layer instance TG-L1-005) — whether the +426 is overlap or loss is not determined offline (MF-L1-005); CF-02 |
| ga_strength-Dens.served | Dens | detector | NO_DETECTOR in the saved census and offline (rev 4): no capability module's code references `ga_strength`; the served surface cannot be attributed by code although the served reader exists (`get_strength.ts:189`); CF-04, CF-18 |
| census: no Ldgr / Complete.depth / Vocab / Reach cells | Ldgr, Complete, Vocab | detector | no `target_table`, so four cells have no reading (MF-L1-003); CF-08, CF-18 |
| brief: is a bounds check a second pass? | Earn/Carr | SS question | the ashtakavarga check ("Σ sarva bindus = 337", `_verify_ashtakavarga`) returns `two_pass_verified` on pass (`:731`) although it validates an invariant of the computed output rather than a second derivation; the ṣaḍbala sum-vs-total check was already demoted to `single_pass` for this reason (`:711-721`). CF-19 asks which tier a bounds/invariant check earns |
| brief: verification-tier literals | Earn | real | 26 quoted tier strings (indicative), `"single_pass"` among them (`:1855`); CF-17 |
| brief: Narr fidelity (declared `citation_human`) | Narr | real | declared; offline: agree PASS, fidelity PARTIAL, lint NO_DETECTOR; CF-15 |
| ga_strength-Build.history | Build | history | PARTIAL: 7 errors / 9 aborts; latest error 2026-07-14 `BLOCKED: upstream ga_vargas did not complete` (a cascade); CF-10 |
| brief: sequencing hazard with `ga_vargas` access | Build | real | the saptavargaja component and per-varga bala read `chart_divisionals` (`:1234-1236`); if the builder role is RLS-blind (CF-16, I-11) a rebuild before the access fix would drop those rows (`not_defined`/floored states; code reading, not run) |
| brief: legacy `_telemetry` call site | Earn | information | `ga_strength_writer.py:1961` reached at `:1941` under `owns_conn` (`:1940`); wrapper passes `conn` (`ga_strength.py:20`); CF-14 |
| ga_strength-Earn / Cost / Carr / Idem | Earn, Cost, Carr, Idem | detector / stale | CF-05, CF-07; the Idem ledger row is stale (census PASS) |

## 3 · Disposition

**keep (P)** — sourced (PyJHora delegation, M-22 earned-tier fix on main), load-bearing (5/56) and honestly tiered; the W2 route was `rebuild_only` with its MUST finding (F-C1 selector) serving-side and fixed. What remains is a completion basis/ownership question, an unattributable served surface, and one tier question.

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Resolve the 426-row difference: ownership overlap or loss

- **Answers:** census Build.completion FAIL; CF-02
- **Change:** read-only first: list, by `fact_category`, the rows the `count_sql` counts that `fact_category_ownership` gives to `ga_structural` (420) and the remaining 6; then either (a) scope the asset's `count_sql` to the categories its writer writes (the precedent: `bg_class_lifetime_counts`) — which changes the live count and therefore the floor 13,621, re-declared in the same migration — or (b) correct the ownership table (`ga_structural` count_sql was already scoped by migrations 309/319)
- **Files / declaration / migration:** a registry migration (`count_sql`; number = max+1 at execution time) and/or `fact_category_ownership` rows
- **Failing-first test and mutation:** failing-first: `rows_written` of a rerun equals the asset's own count on a stated basis; mutation: re-add one structural category to the predicate and the test fails
- **Output change:** none
- **Blast radius:** cockpit counts for `ga_strength` and `ga_structural` (cosmetic); no consumer reads `count_sql`
- **Rebuild:** none for the registry part
- **Gate it moves:** Build (completion)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TG-L1-005 (ownership rule)
- **Question for SS:** Which asset owns the 420 overlapping rows?

### FD-2 · Make the ṣaḍbala/aṣṭakavarga tier honest per check (design)

- **Answers:** CF-19 question
- **Change:** after SS rules whether a bounds/invariant check earns `two_pass_verified`, either keep the aṣṭakavarga stamp or demote it to the tier the ruling names (for example `classical_match`); no value changes
- **Files / declaration / migration:** `ga_strength_writer.py:731, 1855`
- **Failing-first test and mutation:** the verifier returns the ruled tier on a seeded passing case; mutation: change the invariant constant and the check fails
- **Output change:** yes if demoted (stored tier on the aṣṭakavarga rows) — SS (R5); the L2 salience weight moves
- **Blast radius:** readers of the aṣṭakavarga rows; `two_pass_verified` is 9,320 of 143,299 `chart_facts` rows on the chart (layer instance §2.7), of which this asset's share is not attributed
- **Rebuild:** **needs production rebuild** if demoted: REVIEW
- **Gate it moves:** Earn, Carr
- **Fix class:** writer code + output change; **buildable before J1:** tier-dependent: TG-L1-022
- **Question for SS:** Does an invariant/bounds check earn `two_pass_verified`?

### FD-3 · Make the served surface attributable (design)

- **Answers:** Dens NO_DETECTOR; CF-04, CF-18
- **Change:** attribute `get_strength.ts` (a served read of `chart_facts` with the strength category predicate) to this asset by declaring the categories it serves (declarations `carriage.served_surface` with the `read_evidence` already present) so the inspector's Dens scan can attribute it by fact_category rather than by table
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` (already carries `read_evidence get_strength.ts:189`); inspector change is Track E
- **Failing-first test and mutation:** Dens reads a verdict, not NO_DETECTOR
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Dens
- **Fix class:** registry/declaration + detector/tooling; **buildable before J1:** tier-dependent: N-22 Dens applicability, TGH-T3-26

### FD-4 · Tier literals and Narr test

- **Answers:** CF-17, CF-15
- **Change:** as `ga_positions` FD-1/FD-2 for this writer (`"single_pass"` has an alias, no named constant of its own)
- **Files / declaration / migration:** `ga_strength_writer.py`; a test beside the writer tests
- **Failing-first test and mutation:** as ga_positions
- **Output change:** none
- **Blast radius:** none for data
- **Rebuild:** none
- **Gate it moves:** Earn, Narr
- **Fix class:** writer code + test; **buildable before J1:** tier-independent

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-02** — Producer attribution on the shared `chart_facts` table: partition-scoped `count_sql`, `fact_category_ownership`, multi-table writers. *This asset:* FD-1: overlap with `ga_structural`; no `target_table`
- **CF-19** — Earned verification tier: `two_pass_verified` stamped by default or by literal where no second derivation runs (CLAUDE.md §N.8). *This asset:* FD-2: a bounds check labelled `two_pass_verified`
- **CF-04** — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution. *This asset:* FD-3: unattributable
- **CF-18** — Census population on shared tables: chart-scoped, partition-scoped cells for Complete / Ldgr / Vocab / Reach / Dens. *This asset:* no Complete/Vocab/Reach cells: one of two assets with no `target_table`
- **CF-08** — Ldgr: assets with no recognised citation column (six L1 cells with no reading). *This asset:* no Ldgr cell: one of six
- **CF-16** — `chart_divisionals` reads 0 rows for every login role since the migration-1035 ownership change (RLS deny-all): an access incident, data probably intact, UNVERIFIED until read as owner or builder (Track I I-11). *This asset:* reads `chart_divisionals`: rebuild only after the CF-16 access fix
- **CF-17** — Verification-tier string literals in L1 writers (CLAUDE.md §N.4: named constants from `verification_vocab.py`). *This asset:* FD-4: 26 quoted tier strings
- **CF-15** — Narr golden tests that name the declared `citation_human` field (assertion on the sentence, not only on the builder). *This asset:* FD-4: declared
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it. *This asset:* PARTIAL 7/9: history
- **CF-12** — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written. *This asset:* delete scope: categories present in rows
- **CF-14** — Legacy `ga_writers/_telemetry.py` `update_asset_throughput` call sites (eight L1 writers, R34 residual). *This asset:* one of eight: `:1961`
- **CF-13** — Build.dag reads-match: declared `depends_on` against the tables each L1 writer reads (missing edges, two back-reads). *This asset:* edges: `ga_vargas` declared and read
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent: no change
- **CF-06** — `prose_fields` declarations for the L1 assets that have none or an incomplete one (Null and Narr gates). *This asset:* declared: `["citation_human"]`

## 5 · Semantic fingerprint contract (for E5.5)

natural key `(chart_id, ayanamsha_id, fact_category, fact_subject, fact_key)` (the table's unique key also includes `build_id`: `ga_writers/_idempotency.py:3-6`), restricted to this asset's `fact_category` partition over the strength categories listed under target tables; Rahu/Ketu `computed_extension` and `not_defined_for_nodes` rows are part of the fingerprint. `id`/`build_id`/`build_id_uuid`/`computed_at` are volatile and excluded; `fact_id` is a semantic hash that excludes `build_id` where the writer builds it that way (checked for `ga_ayurdaya`, `_fact_id` at `ga_ayurdaya_writer.py:183-186`; not read for every writer).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the PyJHora-delegated ṣaḍbala/aṣṭakavarga/vimśopaka (no hand-rolled heuristics), the labelled node extension, and the earned minimum-tier row stamp (M-22).
- **Carriage check chosen (T4 §4.1; one only):** D3 — an independent recomputation of at least the aṣṭakavarga bindus (classical bindu tables) against the PyJHora output; the existing bounds checks are consistency guards, not D3.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Does an invariant/bounds check (Σ sarva bindus = 337) earn `two_pass_verified`, or `classical_match`/`single`?
2. Which asset owns the 420 rows both `ga_strength`'s and `ga_structural`'s ownership read name?

## SS rulings (2026-10-02, decision N-62) for this asset

SS ruled the L1 decision sheet (`DECISION_SHEET_L1_v1_0.md`, PR #2844). Every recommendation is ACCEPTED with the specifics below; (R) items are provisional until the J1 review. S-L1 is the canonical chart first; the other two charts are the later stage S-L1b (separate REVIEW); S-L1 never waits for an optional item.

- Q-L1-04 accepted: narrow the `count_sql` predicate (`LIKE '%bhava_bala%'` over-claims 420 rows that `ga_structural` writes) (I-30). Q-L1-16(a): emit `single`, never `single_pass` (10,575 canonical rows) (I-27). The stored tier of this asset contains no `two_pass_verified` row.
