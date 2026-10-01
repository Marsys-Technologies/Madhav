---
asset_id: bo_samskara
layer: L2 Bodha (bo_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L2 (briefs, dispositions, designs)
census_revision_used: "after-grant census `00_ARCHITECTURE/briefs/suvarna/layers/census/after_reader_grant/census_L2.json` (generated 2026-09-30T20:30:56+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). It differs from the first run (`census/census_L2.json`, 20:23:30) in exactly six cells (bo_anveshana, bo_sangati, bo_upaya: Build.completion and Count.floor, ERRORED then). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L2/L2_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)"
base_commit: "main 3311b0a06"
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16)"
nirmana_freeze: "t3, 2026-09-11"
ledger_gap_ids: [bo_samskara-Idem.pattern, bo_samskara-Earn.build_record, bo_samskara-Cost.baseline, bo_samskara-Count.floor, bo_samskara-Build.history, bo_samskara-Carr.detector]
---
# bo_samskara — Signal embeddings (one 768-dim vector per MSR signal)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question. Dispositions are proposals under Track A brief §10; every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

Creates one `bodha_signal_embeddings` row per `bodha_msr_signals` row (1:1): `embedding_input_summary` is a deterministic string of the signal's key fields (`fact_key=…`, `domains=…`, 512 characters at most) embedded with Vertex AI `text-multilingual-embedding-002` (768 dimensions, batches of 100) (`bo_samskara.py` docstring, `:45-60`, `:95-112`). A HEAVY writer: `plan_substeps` returns one sub-step per ayanamsha (`:212-216`); a rebuild reuses an embedding whose input text is unchanged by reading the prior generation's row snapshot before `replace_prior_signal_embeddings` deletes it (`:135-160`), `ON CONFLICT (signal_id) DO UPDATE`. `@register("bo_samskara")` at `bo_samskara.py:205`. 50,678 chart rows equal the chart's MSR rows; floor 60,000 (`Count.floor` FAIL, -9,322; seed 66,738). Declared dependencies: the six MSR producers. Dependents `bo_anveshana` (embedding outliers), `bo_pramana_mapa`, `ph_nimitta` (L4). Frozen under the t3 definition (2026-09-11).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1700` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_samskara.py:205`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bodha_signal_embeddings`; count_sql tables: `bodha_signal_embeddings` | census CEN-R |
| live rows / floor | 50678 / 60000 (chart 482012f1, count_sql scope) | census `live_rows`, `Count.floor` |
| catalog_status | CURRENT | census |
| depends_on (declared, seed incl. migration 1210) | `bo_arudha`, `bo_laksana`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana` | seed `asset_registry_seed.ts` (live may differ by migrations 913/1084/730/676) |
| blast radius | census (saved, pre-1210): direct 3 / transitive 22; seed-derived closure (post-1210): direct 3 / transitive 22; direct dependents: `bo_anveshana`, `bo_pramana_mapa`, `ph_nimitta` | census `blocking_radius`; seed + migration 1210 closure (`/Users/Dev/suvarna-evidence/A_L2/closure_L2.json`) |
| code readers | `bodha_signal_embeddings`: 12 non-test py/ts/tsx files reference it (6 outside bodha_writers/, brahmagyan/ and bo_*.py writers): `ph_nimitta.py`, `backfill_missing_signal_embeddings.py`, `engine.py`, `coverage_matrix.ts`, `query_insight_embeddings.ts`, `query_signals.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx; paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | none by the census (`Reach.fields` 0 modules);  | census reach |
| Nirmāṇa freeze | frozen by Nirmāṇa (t3, 2026-09-11; NIRMANA_SUPERSESSION_RECORD §2.3) | NIRMANA_SUPERSESSION_RECORD §2.3 |
| role / scoring mode | neither (supplies what manifestation and time rest on); contribution scoring (chart-product layer) | layer instance §2.5 (TG-L2-019), census `L2.scoring` |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: the after-grant saved census named in the frontmatter (inspector 2a78ec64d, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 0a3236eb complete/build (2026-09-11) |
| Idem | Idem.pattern† | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): bodha_signal_embeddings (bodha_writers/_idempotency.py:508 via bo_samskara.py → bodha_writers/_idempotency.py:replace_prior_signal_embeddings) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Build | Build.history | PARTIAL | latest run complete, but 36 error(s) and 8 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-12): worker_crash: OperationalError: the connection is lost |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 0a3236eb complete/build (2026-09-11) |
| Count (information) | Count.floor | FAIL | live=50678, floor=60000, delta=-9322 |
| Complete (information) | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach (information) | Reach.fields | NOT_GENERIC | reported, not graded — width 0/10 built column(s) (0.0%) selected by 0 capability module(s); dark: ['ayanamsha_id', 'build_id', 'chart_id', 'computed_at', 'embedding_id', 'embedding_input_summary', 'embedding_model', 'em… |

Census emits **no cell** (absent, not N/A) for: Ldgr.source_presence (MF-L2-003, register R128).

**PASS cells (compact):** Vocab.identity (declared key (embedding_id): 0 duplicate(s)); Dens.served† (1 module(s): query_signals.ts; declaring density_contract: 1); Build.registered; Build.contract; Build.target†; Build.dag†; Build.count_integrity; Build.completion (rows_written=50678 = live=50678 (count_sql over the target table; chart 482012f1)); Build.exercised (62 executed run(s) of 96 build_run_assets row(s), scope(s): asset, asset_set, global, layer, last executed 202…); Build.dep_liveness; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure, not a certification): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline static re-scans on main's code** (indicative, not a census; method in `INDEX.md` §1): Dens.served rev 4 reads **NO_DETECTOR** — 2 module(s) reach it by code: L1_ganita/coverage_matrix.ts, L2_bodha/query_signals.ts, but no served `SELECT ... FROM` its table was found (no served select): whether it is served cannot be told by code; Idem.pattern rev 2 reads **PASS**.

**Build.dag rev 2 (E6 g+h; recompute over the saved registry BEFORE migration 1210, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`, reads-match clause):** PASS (not in the recompute's L2 gate-diff list; no change from the saved rev-1 PASS) The saved census cell Build.dag PASS † above is the rev-1 reading.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row, declaration or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row from the 2026-09-27 run (`asset_gaps.jsonl` @ 2a78ec64d, not on main) that the saved 2026-09-30 census no longer reads as written; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **real-or-SS-question** = read in code, not measured by the census, whose verdict needs a ruling.

| gap id (ledger or census cell) | gate | class | note |
|---|---|---|---|
| census cells Dens.served † (PASS) vs Reach.fields (0 modules) (MF-L2-013) | Dens | real (served assertion) + detector | the saved rev-1 Dens PASS reads `query_signals.ts` (declares a contract) but no capability selects `bodha_signal_embeddings`; `query_signals.ts:484` states that the semantic (embedding) query is unavailable at query time and salience ranking is used, while its tool descriptions still say a `semantic_query` uses pgvector cosine similarity over the embeddings (`:223`, `:321`) and its file header cites 66,738 rows (`:4`); `coverage_matrix.ts:709` maps the table to a serve pointer `marsys://tool/L2/get_signal_embeddings` that exists nowhere else in the repository. The declaration (`served_surface: null`) records the same disagreement. FD-1; CF-04. |
| `bo_samskara-Count.floor` | Count (information) | information | live 50,678 vs floor 60,000 (-9,322): the same shortfall as `bo_laksana` (the 1:1 table follows the MSR count); CF-03 (refresh after a coherent rebuild). |
| census: no `Ldgr.source_presence` cell (MF-L2-003) | Ldgr | detector | no citation column; the row's provenance is `signal_id` (FK to the MSR row). Declare it as the carrying column. CF-08. |
| declarations `prose_fields: null` (undeclared) | Null, Narr | detector (declaration) | `embedding_input_summary` is composed by f-string from key fields of the signal (`bo_samskara.py:105-111`: `fact_key=…`, `fact_value_text=…`, `graha=…`, `domains=…`): it states computed values as text, so by the SS 2026-10-01 rule (a composed string that states a computed value is narration) it is a candidate for `["embedding_input_summary"]`; the string is the embedding's input, not a reader-facing sentence. CF-06. |
| `bo_samskara-Idem.pattern` | Idem | stale | ledger row (`ON CONFLICT where the layer convention is delete-then-insert`) is from 2026-09-27; saved census PASS (`replace_prior_signal_embeddings`, `_idempotency.py:508`), offline rev-2 PASS; the upsert in the insert is intentional (reuse key `signal_id`). |
| `bo_samskara-Build.history` | Build (history) | history | latest run complete; 36 errors and 8 aborts on record (latest error 2026-08-12, `worker_crash: OperationalError: the connection is lost`). CF-10. |
| `bo_samskara-Earn.build_record`, `-Cost.baseline`, `-Carr.detector` | Earn, Carr | detector | instrument absent / no D1-D3 detector; CF-05, CF-07. |

## 3 · Disposition

**keep (P)** — the table is complete 1:1 with the signals and the writer is idempotent with cost-aware reuse; the open question is the served status of the embeddings (an internal navigation aid per T2 §6.3, used by the discovery engine and L4), where three artifacts disagree. No asset change is required for the data.

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Make the served claim about embeddings true

- **Answers:** the Dens/Reach disagreement and the stale descriptions; MF-L2-013
- **Change:** either (a) remove the `semantic_query` wording from `query_signals.ts` (`:223`, `:321`) and its stale 66,738 header (`:4`) and drop or re-point the `coverage_matrix.ts:709` pointer to the real consumer (`bo_anveshana`/`ph_nimitta`), declaring the table `served_surface: false` with the consumers as `terminal_by_construction`; or (b) implement the semantic path the descriptions promise (an output change of the served tool)
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts`, `platform/src/lib/retrieval/registry/layers/L1_ganita/coverage_matrix.ts:709`, `asset_declarations.json`
- **Failing-first test and mutation:** a descriptor-honesty test (the existing `list_entities_honesty_wp15` pattern): the tool description never promises a path its handler does not run; mutation: restore the sentence → the test fails
- **Output change:** none for (a); (b) changes a served tool: SS (R5)
- **Blast radius:** `query_signals` is the layer's widest served tool (named by `register_d8_assess_domain.ts`, `register_d9_judgment.ts`, `traverse_chart_graph.ts` and the L3 wrappers, 19 modules in the offline Dens scan): a description edit changes tool metadata only; `coverage_matrix.ts:709` is a coverage-claim map read by the L1 coverage tooling; option (b) would add a served path
- **Rebuild:** none
- **Gate it moves:** Dens, Reach
- **Fix class:** served surface (TS) + declaration; **buildable before J1:** tier-dependent: the served-surface rule for navigation aids (T2 §6.3) and N-22
- **Question for SS:** Is the embedding table a navigation aid with no served surface (declare it so), or must the semantic query be built?

### FD-2 · Narr golden-value test for the declared prose columns

- **Answers:** Narr gate (NO_DETECTOR); CF-14; Track A §5 (per-asset Narr golden tests)
- **Change:** golden fixture: a signal with `fact_key`, `fact_value_text`, `graha` and domains → `embedding_input_summary` equals the hand-written key=value string, truncated at 512 characters exactly as the writer does
- **Files / declaration / migration:** a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can find it; no asset or registry change
- **Failing-first test and mutation:** failing-first: the test fails on a writer whose narrated value differs from the cited fact; mutation: change one composed value (a house number, a count) in the writer → the test fails
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 3: `bo_anveshana`, `bo_pramana_mapa`, `ph_nimitta`; transitive 22); the touched surface is a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can f
- **Rebuild:** none
- **Gate it moves:** Narr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling (test); **buildable before J1:** tier-independent (SS ruling 2026-10-01 defines narration; declarations 1.6.0 exists)

### FD-3 · Carr detector

- **Answers:** Carr.detector NO_DETECTOR; CF-07
- **Change:** D3 (re-derivation of the input): rebuild `embedding_input_summary` from the signal's stored fields with the writer's pure function and compare; check that the row count equals the MSR row count and every `signal_id` resolves. The vector itself is not re-derived (a model call); sample cosine equivalence on a stratified sample.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 3: `bo_anveshana`, `bo_pramana_mapa`, `ph_nimitta`; transitive 22); the touched surface is a new check in the Nikaṣa inspector tooling (Track E) registered for this asset
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-04** — Dens (serving density) on the L2 served modules. *This asset:* FD-1; the detector disagreement is the same one as `bo_cdlm_summary`'s
- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* Count.floor refresh after a coherent rebuild; seed 66,738
- **CF-08** — Ldgr: assets with no recognised citation column (no census cell). *This asset:* no Ldgr reading
- **CF-06** — prose_fields declarations for the L2 assets that have none (Null and Narr gates). *This asset:* declare `embedding_input_summary`
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* carriage D3 (§6)
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* history PARTIAL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `signal_id` (one embedding per signal; `signal_id` is the MSR row's id, so the fingerprint must key through the signal's natural key `(chart_id, ayanamsha_id, signal_type_id, configuration_jsonb)`). Fingerprint: `embedding_input_summary`, `embedding_model`, `embedding_model_version`; **the embedding vector's equivalence policy:** two vectors from the same model, version and input text are equivalent when the cosine distance is below a declared tolerance (Vertex is not guaranteed bit-identical across calls), and a reused vector (unchanged input) is identical by construction. **Volatile:** `embedding_id`, `build_id`, `computed_at`; the exact vector bytes. Expected 50,678 rows on the chart.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** 1:1 embedding of every signal, the deterministic input text, cost-aware reuse keyed on unchanged input.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation of the input) (design in FD-3)
- **Opportunities (never blocking):** a served semantic path, if wanted; the ledger of how many embeddings a rebuild reused.

## 7 · Rebuild and frozen-manifest consequences

Frozen manifest: Nirmāṇa froze this asset under definition t3 on 2026-09-11 (NIRMANA_SUPERSESSION_RECORD §2.3). Migration 1210 added no edge to this row. Manifest staleness has two severities (`src/lib/nirmana-elevation/definitions.ts:379-396`, `monitor.ts:374-393`): a `depends_on`, layer or membership change makes `assertManifestMatchesRegistryIdentity` throw (the monitor reports `plan_adaptation_required`; `dispatch_nirmana_campaign_wave.py` refuses the wave); a change to `count_sql`, `natural_key_partition`, `catalog_status`, `target_table` or `integrity_check_sql` only trips `assertManifestMatchesRegistry` (`evidence_refresh_required`: accepted evidence must be refreshed). The Nirmāṇa campaign is OFF (NIRMANA_SUPERSESSION_RECORD §1, §3), so the staleness has no running consumer, but the frozen-definition DB row still reads `frozen`. **A production rebuild (SS REVIEW):** its direct dependents (`bo_anveshana`, `bo_pramana_mapa`, `ph_nimitta`) re-run after it in DAG order; seed-derived transitive closure 22 assets. **F-3 invariant (this asset carries or derives from MSR signal ids):** it must be rebuilt strictly after every MSR producer and not before a later MSR regeneration in the same window (`msr_rebuild_order_guard.py`, F3 `plan_invariant.md`); I-6: an unguarded MSR replace took the `kala_*` tables from 4 rows to 0 and erased the canonical chart's five Kāla tables on 2026-09-08; charts 1c826d5a and cb73cd3d (all-v4 ids) make the guard mandatory; see INDEX §7. A rebuild after an MSR replacement re-embeds only changed inputs (reuse); the cascade from `bodha_msr_signals` deletes all rows when any producer is replaced (instance §6.2), so after any MSR replacement it must re-run (registry level 7), then `bo_karanajala`, `bo_laksana_rerank` and `bo_anveshana`. Cost: a Vertex AI call per changed signal.

## 8 · Questions for Strategic Suvarṇa

1. FD-1: is the embedding table a navigation aid with no served surface (declare it), or must the semantic query be built?
2. CF-06: is `embedding_input_summary` narration (a composed string of computed values) or an embedding input, outside the Narr rule?
