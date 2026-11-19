---
asset_id: ga_dashas
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
track_i_items: [I-11, I-24, I-31]
ledger_gap_ids: [ga_dashas-Idem.pattern, ga_dashas-Earn.build_record, ga_dashas-Cost.baseline, ga_dashas-Build.history, ga_dashas-Carr.detector]
---
# ga_dashas — Daśā systems × ayanamshas (4-level tree), the layer's largest table

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Seven daśā systems × five ayanamshas for the canonical native, written to `chart_dashas` (`ga_writers/ga_dashas_writer.py:1-30`): 4-level Sukṣma depth (`level_n` 1–4, none at 5), KP as a `kp_sublevel` dimension, calculation window 1950-01-01..2100-12-31, one sanctioned JSONB column (`concurrent_system_lords_jsonb`). Engine is PyJHora through `pyjhora_adapter`; a FORENSIC Vimshottari assertion (Moon in Purva Bhadrapada → Jupiter first mahadasha) gates the build (`:21-37`). An independently re-implemented Vimshottari verifier (`ga_writers/_vimshottari_independent_verifier.py`, 1,483 lines) re-derives levels 1–4 boundary by boundary; `_apply_vimshottari_independent_verification` (`ga_dashas_writer.py:735`, called at `:3197`) stamps every non-KP level 1–4 Vimshottari row with its own verdict from `compare_row`, while the other six systems carry `CLASSICAL_MATCH` membership verdicts the code itself labels “relay fidelity, not re-derivation” (`:863-910`); whether the orchestrated substep path reaches the per-row stamp was not traced (layer instance §2.7). `_verify_vimshottari` still halts on the native FORENSIC lord but no longer broadcasts its verdict (`:3186-3190`). Idempotency: `replace_prior_chart_dashas` (`_idempotency.py:86`) plus the owner-receipt-gated `authorize_chart_fact_delete`.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data; prose_fields undeclared (null) | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1127` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_dashas.py:19` (heavy: substeps per system × ayanamsha); registry `has_writer` = True | writers dir; census `Build.registered` |
| target table(s) | `chart_dashas` (count_sql `SELECT count(*) FROM chart_dashas WHERE chart_id = $1`) | census CEN-R (`target_table`, `count_sql_tables`) |
| live rows / floor | 483,870 / 471,767 (Δ +12,103); `asset_throughput` lit / 483,870; seed floor literal 471767 (chart-dependent: the seed comment records 471,767 / 483,859 / 505,348 across charts) | census `live_rows`; floor and throughput from the layer instance §1.1 (live registry read 2026-09-30) |
| catalog_status | CURRENT | census |
| depends_on (live, 2026-09-30) | `ga_positions` (live and seed); the writer also reads `chart_divisionals` (see gaps) | layer instance §2.5 |
| blast radius | live registry incl. migration 1210 (applied; verified live 2026-10-01 14:37Z per the independent review): direct 16; census (2026-09-30, pre-1210): direct 14 / transitive 61; seed + 1210 reconstruction names 16 direct dependent(s): `bo_upaya`, `ga_condition`, `ga_sade_sati`, `ga_structural`, `ga_tajaka`, `ga_vichara`, `ga_yoga`, `ka_avadhi`, `ka_dasha_kala`, `ka_gochara`, `ka_jivana_parva`, `ka_kalasutra`, `ka_sangam`, `ka_taranga`, `ka_vighnakara`, `ka_yojaka` | census `blocking_radius`; live count from the independent review; names reconstructed from `asset_registry_seed.ts` + `platform/migrations/1210_asset_registry_direct_edges.sql` (other migrations also edit `depends_on`, so the reconstruction can differ from the live registry) |
| code readers / served surface | `get_dashas.ts:727` (declarations `read_evidence`), `get_dasha_lord_capability.ts`, `coverage_matrix.ts` (census: 3 modules, 1 declaring `density_contract`); census `reach.modules` lists 5; 13 of 42 built columns selected (31.0%) | census `reach.modules`; layer instance §1.2 |
| role / scoring mode | the clock foundation (layer instance §2.4 row 3.10: daśā, Tājaka, tithi-praveśa, Sudarśana); 16 direct (live incl. 1210; census pre-1210: 14) / 61 transitive dependents | layer instance §0.2, §4.4 (contribution layer; Computational correctness, T1 §11) |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: as the frontmatter `census_revision_used` (not repeated here).

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count). `Null.*` and `Narr.*` did not exist in the saved census.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.history | PARTIAL | latest run complete, but 18 error(s) and 6 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-05): orphaned_by_crash: prior orchestrator terminated while asset was in-flight |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run f2a62f44 complete/skip_no_delta (2026-09-07) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run f2a62f44 complete/skip_no_delta (2026-09-07) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | see the offline reading below |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Count.floor; Complete.depth; Vocab.identity; Ldgr.source_presence; Dens.served †; Build.exercised; Build.dep_liveness.

Information (never blockers, D3): Reach.fields NOT_GENERIC — reported, not graded — width 13/42 built column(s) (31.0%) selected by 5 capability module(s); dark: ['anchored_solar_return_iso', 'applies_to_this_chart_flag', 'build_id', 'chart_id', 'citation_human', 'citation_ref', 'computed_at', 'concurrent_system_lords_…; Complete.width NOT_GENERIC — no declared universe for this asset — declaring one is the first width gap.



**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; `NA_RULE_DECISIONS` is empty on main, so a measured N/A reads NO_DETECTOR; mixes old measurements with new rules; not a re-measure and not a certification; `_evidence/rollup_saved_L1.json` beside this file): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline re-scan of two criteria the saved census predates** (main's own code over this tree and the saved record, no database; indicative): Dens.served rev 4 reads **PARTIAL** — STRUCTURAL: 11 module(s) reach it by code: L1_ganita/coverage_matrix.ts, L1_ganita/get_dasha_lord_capability.ts, L1_ganita/get_dashas.ts, L3_kala/call_service_wrappers.ts, L3_kala/query_active_dashas.ts, L5_mimamsa/query_mechanism_retrodiction.ts (+5 more); a referencing capability declares density… (the saved rev-1 reading was PASS); Null/Narr graders over the declarations file 1.6.0 plus DDL-derived columns (`_evidence/narr_null_offline_L1.json`; `*` = INCONCLUSIVE because no row data was read): agree NO_DETECTOR; checkable NO_DETECTOR; fidelity_test NO_DETECTOR; lint NO_DETECTOR; schema_default NO_DETECTOR; blank_rows NO_DETECTOR.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **SS question** = real or not depends on a ruling; **artefact** = a saved census cell that reads a measurement the inspector's role could not make (pending a read by a role that can). A row naming several classes counts under its leading label.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell, or this brief) | gate | class | note |
|---|---|---|---|
| brief: undeclared read of `chart_divisionals` (Track I evidence §D) | Build.dag | real | `_load_natal_context_inner` selects D1 dignity from `chart_divisionals` (`ga_dashas_writer.py:579-587`) and writes it as `lord_natal_dignity_d1` (`:664`); `depends_on` is `[ga_positions]` only, so the scheduler can run `ga_dashas` before `ga_vargas`. Under Build.dag rev 2 the reads-match clause reads FAIL (Track I: "missing_edge ga_vargas, existing path: none"). The column is filled on the live rows (non-NULL on 292,354 of 483,870, the independent review of HEAD f9448c509 (reader queries, 2026-10-01; not in the repo)), so the table was readable to the builder when they were written; the other 191,516 NULL rows are not explained here. If the builder role is RLS-blind now (CF-16), a new build would write NULL; CF-13, CF-16 |
| brief: live correctness of the F-A12 dignity fix is not read | Vocab/Carr | SS question | W2 MUST F-A12: `lord_natal_dignity_d1` disagreed with the serve-time authority on 28,923 rows (`Enemy` vs `neutral`); the fix is on main (`ga_dashas_writer.py:590-599`). The column is non-NULL on 292,354 of 483,870 live rows; whether those values agree with `chart_facts.graha_dignity_per_varga` (and whether the 191,516 NULLs are legitimate) needs a read-only parity query (L1 authority, CLAUDE.md §N.5); the census cannot see it |
| brief: `prose_fields` undeclared although `citation_human` is composed | Null, Narr | real | declarations 1.6.0 `prose_fields: null`; the writer composes `citation_human` through `_citation(level, lords)` at `ga_dashas_writer.py:1156, 1500, 1685` and a literal at `:3424`; the declared value is a candidate `["citation_human"]` (composition sites read; the column list not enumerated); CF-06 |
| ga_dashas-Build.history | Build | history | PARTIAL: 18 errors / 6 aborts; latest error 2026-08-05 `orphaned_by_crash`; the latest run completed (`skip_no_delta` 2026-09-07, not a failure); CF-10 |
| brief: Dens (offline rev 4) | Dens | detector | PARTIAL: contract declared but `get_dasha_lord_capability.ts` and `query_mechanism_retrodiction.ts` carry no tier column in their served select; CF-04 |
| brief: Carr — a D3 verifier exists in code but the census cannot read it | Carr | detector | `two_pass_verified` is 46,009 of 483,870 `chart_dashas` rows (9.5%) and `single` 437,474 (90.4%) on the chart (layer instance §2.7): the verified subset is the checkable claim; CF-07 |
| brief: legacy `_telemetry` call site | Earn | information | `ga_dashas_writer.py:3078` (inside `_update_asset_throughput`, def `:3067`), reached at `:3307` (under `owns_conn`) and `:3575` (inside the CLI-shaped `build_ga_dashas`); CF-14 |
| ga_dashas-Idem.pattern | Idem | stale | ledger "no pattern in own SQL" is stale: the census reads PASS via `_idempotency.py:86`; CF-12 notes what that does not test |
| ga_dashas-Earn / Cost / Carr | Earn, Cost, Carr | detector | CF-05, CF-07 |

## 3 · Disposition

**keep (P)** — every applicable census cell is PASS but the Build history record; the writer's four W2 `changed` fixes (F-A10 sentinels, migration 652; F-A12 dignity vocabulary; F-A17 bare tier literals, guarded by `tests/test_ga_dashas_f_a17_bare_tier_literals.py`) are on main; the open items are one missing edge, one undeclared prose column, and an unread live-parity question — fixes, not a different disposition.

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Declare the `ga_vargas` edge (design only) and sequence the rebuild

- **Answers:** Build.dag reads-match missing edge; CF-13
- **Change:** `depends_on` of `ga_dashas` += `ga_vargas` (and the seed literal); the edge is a producer→consumer ordering that the scheduler already needs, because the writer reads `chart_divisionals`
- **Files / declaration / migration:** a registry migration of the 1210 kind (a new migration; number = max+1 across every origin head and both migration directories at execution time) and `asset_registry_seed.ts:1127` (`depends_on`); Track I owns the migration lane
- **Failing-first test and mutation:** failing-first: Build.dag rev 2 reads FAIL for `ga_dashas` before and PASS after; mutation: remove the edge and it must flip back; the scheduler's topological order places `ga_vargas` before `ga_dashas`
- **Output change:** none
- **Blast radius:** changes `ga_dashas`' upstream hash (`compute_upstream_hash` hashes declared deps, 1210 header CONSEQUENCES 3) and the ordering: `ga_vargas` must be `lit` and fresh before `ga_dashas` can run (hard dependency gate, which reads the state and freshness, not row counts); `ga_vargas` is `lit`; whether its table is readable to the builder is the CF-16 access question, so declare the edge after the access fix is confirmed so the dependency is true. 14 direct dependents are downstream of the dashas
- **Rebuild:** needs production rebuild of `ga_dashas` (483,870 rows) if the upstream hash drives dispatch: a REVIEW item for SS
- **Gate it moves:** Build (dag)
- **Fix class:** registry/declaration; **buildable before J1:** tier-independent but needs its own review (Track I deliberately left it for a separately ruled migration)
- **Question for SS:** Declare `ga_dashas` → `ga_vargas` after CF-16 is resolved, accepting that the consumer then executes rather than skips?

### FD-2 · Read-only parity of `lord_natal_dignity_d1` against the serve-time authority (L1 authority check)

- **Answers:** brief gap F-A12 live correctness; CLAUDE.md §N.5
- **Change:** no code change. Run once, read-only: for the chart, join `chart_dashas.lord_natal_dignity_d1` (distinct per lord × ayanamsha) to `chart_facts` `graha_dignity_per_varga` D1 and count disagreements and NULLs. A disagreement is a halt-worthy bug (§N.5) and means a rebuild of `ga_dashas` is owed; zero disagreements closes the question
- **Files / declaration / migration:** a query recorded in the evidence folder, not a repo file
- **Failing-first test and mutation:** the query must return a non-zero count on a seeded wrong row (mutation) and 0 on live
- **Output change:** none
- **Blast radius:** none (read)
- **Rebuild:** none unless the query finds disagreements
- **Gate it moves:** Vocab/Carr (L1 authority claim)
- **Fix class:** detector/tooling (one-off read); **buildable before J1:** tier-independent
- **Question for SS:** May SS authorise this single read-only query?

### FD-3 · Declare `prose_fields` for `citation_human`

- **Answers:** Null/Narr NO_DETECTOR; CF-06
- **Change:** declare `["citation_human"]` with `evidence.prose_fields` citing `ga_dashas_writer.py:1156,1500,1685,3424` (the composed sites) and the INSERT that binds the column (`:3457`); then the Narr criteria can measure (offline reading expected PARTIAL on fidelity, like the other declared L1 assets)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for `ga_dashas`
- **Failing-first test and mutation:** declarations validation (`test_e6_1_declarations.py`); mutation: declare `[]` and Narr.agree/lint must flag the composed text
- **Output change:** none
- **Blast radius:** none (census inputs only)
- **Rebuild:** none
- **Gate it moves:** Null, Narr
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-4 · Carr D3: read the verifier's outcome as a per-level carriage record

- **Answers:** Carr NO_DETECTOR; CF-07
- **Change:** a detector that reports, per `(system, level_n)`, the count of `two_pass_verified` vs `single` rows and PASSES only on the verified subset (never on presence); the independent verifier already exists (`_vimshottari_independent_verifier.py`) and is the second derivation
- **Files / declaration / migration:** Track E inspector tooling; no asset file
- **Failing-first test and mutation:** a seeded wrong boundary in a copy must be reported
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Carr
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment (TGH-T3-02)

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-13** — Build.dag reads-match: declared `depends_on` against the tables each L1 writer reads (missing edges, two back-reads). *This asset:* FD-1: missing edge to `ga_vargas`
- **CF-16** — `chart_divisionals` reads 0 rows for every login role since the migration-1035 ownership change (RLS deny-all): an access incident, data probably intact, UNVERIFIED until read as owner or builder (Track I I-11). *This asset:* downstream reader of `chart_divisionals`: `lord_natal_dignity_d1` reads it (`:579-587`); blind for the builder role only if the RLS deny-all is real (I-11)
- **CF-06** — `prose_fields` declarations for the L1 assets that have none or an incomplete one (Null and Narr gates). *This asset:* FD-3: undeclared; candidate `["citation_human"]`
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset (D3 dominates in L1). *This asset:* FD-4: D3
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it. *This asset:* PARTIAL 18/6: history
- **CF-04** — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution. *This asset:* offline PARTIAL: tier column absent in two served selects
- **CF-14** — Legacy `ga_writers/_telemetry.py` `update_asset_throughput` call sites (eight L1 writers, R34 residual). *This asset:* one of eight: `:3078`
- **CF-12** — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written. *This asset:* delete scope: `replace_prior_chart_dashas` scoped by system/level present in the rows (`_idempotency.py:86`)
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent: no change
- **CF-18** — Census population on shared tables: chart-scoped, partition-scoped cells for Complete / Ldgr / Vocab / Reach / Dens. *This asset:* `Complete.depth` / `Ldgr` over 1,460,985 rows (all charts): information; the asset's own `chart_dashas` is table-owned so the population error is smaller than for `chart_facts` but still whole-table

## 5 · Semantic fingerprint contract (for E5.5)

natural key `(chart_id, ayanamsha_id, system_id, level_n, start_iso)` (the table's unique key also includes `build_id`, `_idempotency.py:3-6`; the census Vocab key is `dasha_row_id`); volatile: `build_id`, `computed_at`, `dasha_row_id` if it is a surrogate (not read); hierarchical UUIDs are stabilised (`stabilize_hierarchical_uuids`, `ga_dashas_writer.py` import) so a rebuild keeps them.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 7 systems × 5 ayanamshas, the 4-level depth contract, the FORENSIC Vimshottari assertion and the independent verifier; the scope-cap sentinel rows.
- **Carriage check chosen (T4 §4.1; one only):** D3 — the independent Vimshottari verifier is the second derivation (levels 1–4); the verified subset is the PASS population.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Declare the `ga_dashas` → `ga_vargas` edge after CF-16 is resolved (the consumer then executes rather than skips, REVIEW)?
2. May the one-off read-only dignity-parity query (FD-2) be run?

## SS rulings (2026-10-02, decision N-62) for this asset

SS ruled the L1 decision sheet (`DECISION_SHEET_L1_v1_0.md`, PR #2844). Every recommendation is ACCEPTED with the specifics below; (R) items are provisional until the J1 review. S-L1 is the canonical chart first; the other two charts are the later stage S-L1b (separate REVIEW); S-L1 never waits for an optional item.

- Q-L1-02 accepted: declare `ga_dashas -> ga_vargas` (guarded migration; the consumer then executes rather than skips). Mandatory before S-L1. Track I: I-24. F-8: the third chart's `incomplete` state is a read-only answer to SS before S-L1 (I-31).
