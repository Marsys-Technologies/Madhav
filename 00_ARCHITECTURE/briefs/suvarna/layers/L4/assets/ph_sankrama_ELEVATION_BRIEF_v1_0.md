---
asset_id: ph_sankrama
layer: L4 Phala (ph_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL - until J1; may register gaps, may not certify"
produced_by: track-a-l4 (worker under Exec Suvarna)
produced_on: 2026-10-03
plan_item: A.L4 (briefs, dispositions, designs)
census_revision_used: "fresh census `/Users/Dev/suvarna-evidence/census_fresh/1e5781a/census_L4.json` (generated 2026-10-02T10:12:59+05:30, chart 482012f1, inspector 1e5781a at REGISTRY_REVISION 10; outside the repo) compared with the repo's saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L4.json` (2026-09-30T20:23:50+05:30, inspector 2a78ec64d). Main's inspector is now at REGISTRY_REVISION 15: the offline rollup below applies its rules to the fresh census; no live re-measure was run."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L4/L4_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)"
base_commit: "main 3de3f8b15"
disposition: "enrich (E) - fix the ayanamsha fan-out, asymmetry, cascade and silent loader; rebuild"
disposition_proposal_approver: "Steward (G16); any output change to SS (R5)"
disposition_value: enrich
risk_class: "R3 (grain change and a possible ayanamsha column)"
decisions_applied: "none - SS has not answered the A.L4 questions (INDEX section 7); all dispositions and fix designs are proposals"
ss_questions: [Q-L4-01, Q-L4-05, Q-L4-14]
track_i_items: [TI-L4-01, TI-L4-27, TI-L4-28, TI-L4-29, TI-L4-30, TI-L4-31]
ledger_gap_ids: [ph_sankrama-Build.completion, ph_sankrama-Build.dep_liveness, ph_sankrama-Build.history, ph_sankrama-Carr.detector, ph_sankrama-Complete.depth, ph_sankrama-Cost.baseline, ph_sankrama-Count.floor, ph_sankrama-Dens.served, ph_sankrama-Earn.build_record]
---
# ph_sankrama - Cross-domain spillover (anchor x CDLM cell)

> **PROVISIONAL - until J1; may register gaps, may not certify.** Every figure below comes from a stated read-only query (suvarna_reader SELECTs on 2026-10-03, receipts under `/Users/Dev/suvarna-evidence/A_L4/data/`), from the census, from the repository at main `3de3f8b15` (file:line), or from running the asset's pure engine functions locally with no database. Where something could not be determined it says so. Nothing here certifies a gate, approves a disposition or changes an asset.

## 0 - Identity: what the asset is

`ph_sankrama` writes `phala_sankrama`: for each anchor, every material `bodha_cdlm_cells` row (`net_linkage_strength >= 0.25`) whose `domain_row` equals the anchor's domain becomes a spillover row to the cell's `domain_col` (`platform/python-sidecar/pipeline/orchestrator/writers/ph_sankrama.py:112-176`; the anchor->CDLM map is empty by design since W3-3a recovered 250 rows, `:29-52`). Relationship type is `conflict` if the cell has contradicting pairs else `contagion` (`platform/python-sidecar/services/ph_sankrama/engine.py:131-134`); the projected window is the intersection of the anchor window with the cell's predicted activation windows, else the source window (`:91-128`); a cascade chain, a trajectory from the cell's gradient (NULL when unknown since W3-3a), a spillover confidence (`source confidence_high x linkage`, capped 0.8, `:194-198`) and a falsifier template are attached. `wealth` anchors produce nothing because CDLM has no `wealth` row domain (declared and logged, `:57`).

| field | value | source |
|---|---|---|
| kind | registry `asset_kind=artifact`, `asset_type=data`, `scope=per_chart`, `domain=chart`, `rung=R4`; role per L4 layer instance TG-L4-024: not assigned by any tier | `asset_registry` row, read 2026-10-03 |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2768` (live may differ by migration) | seed |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ph_sankrama.py:63`; engine `platform/python-sidecar/services/ph_sankrama/engine.py`; registry `has_writer=True` | code |
| target table(s) | `phala_sankrama` | registry `target_table` / `count_sql` |
| live rows (canonical chart) / floor / build record | 155 / 2510 / `rows_written=2510`; rows per chart in the table(s): phala_sankrama: 1c826d5a=475; 482012f1=155 | `count_sql` run read-only; `asset_throughput`; table group-by |
| state / last built | `stale` / 2026-08-13T01:16:21 UTC (run `cbd6ea44`); `built_against_writer_hash=unknown` | `asset_throughput` |
| catalog_status | CURRENT | registry |
| depends_on (declared, live) | `ph_nimitta`, `bo_sangati` | `asset_registry.depends_on` |
| depends_on vs what the code reads | reads `phala_anchors` (`ph_nimitta` declared) and `bodha_cdlm_cells` (`bo_sangati` declared). No undeclared read found | code (file:line) + fresh census `Build.dag` |
| blast radius | declared dependents direct 2 / transitive 11 (active assets, every layer) | fresh census `blocking_radius` |
| code readers outside the asset (non-test py/ts/tsx, 9 files) | L5 / other writers (python-sidecar pipeline/orchestrator/writers): ph_phaladesa.py; python-sidecar other: bodha_writers/_idempotency.py; serving (platform-mcp/src): resources/vidhi/dossier_slices/dossier_slices.generated.ts; retrieval + app (platform/src): lib/jyotish/asset_names.ts, lib/retrieval/registry/knowledge/producer_editorial_review.ts, lib/retrieval/registry/knowledge/source_query_availability.ts, lib/retrieval/registry/layers/L4_phala/index.ts, lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts, lib/retrieval/registry/tool_name_bridge.ts | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src at `3de3f8b15` (tests, generated and migrations excluded) |
| served surface | `L4_phala/query_phala_calibration.ts` `query_spillover_cascades` (tool-name bridge `phala_spillover_get`, `tool_name_bridge.ts:205,598`; no `density_contract`); read by `ph_phaladesa` (incoming spillover counts) | code |
| role / scoring mode | manifestation-family asset of L4 Phala (T2 section 6.5); census `scoring: contribution`; 'cross-domain spillover and competing effects' (T2c); 'source-window fallback is not independent timing' (T2c) | tiers + census |
| invalidation / FK | `source_anchor_id -> phala_anchors ON DELETE CASCADE`; `cdlm_cell_id` has no FK by design | `pg_constraint` read 2026-10-03 |

## 1 - Measured state and the nine gates

### 1.1 - Live state on the canonical chart (read-only, 2026-10-03)

- **155 rows** from the 4 surviving anchors (floor and build record 2,510; Count.floor FAIL -2,355; Build.completion FAIL). By source domain career 55, character 45, health 30, relationship 25; relationship type contagion 140 / conflict 15.
- **155 rows are 31 distinct (anchor, target-domain) pairs x 5**: the CDLM holds one cell per ayanamsha (5) per domain pair (`static_natal`, `lahiri_chitrapaksha / krishnamurti / raman / surya_siddhanta_classical / true_chitra`, 11 material cells each for `career`), the natural key includes `cdlm_cell_id`, and `phala_sankrama` has no ayanamsha column - so a consumer counting rows overstates spillovers 5-fold. `ph_phaladesa.incoming_spillover_count` is a multiple of 5 on every domain (145-315).
- **155 of 155 projected windows equal the source window and `projected_peak_date = source_window_start`**: the cells carry no activation windows (0 of 280 `predicted_activation_dasha_windows_jsonb` populated), so SK1's 'lag derived from real windows - never a formula' degenerates to the fallback (`engine.py:91-94,124-125`).
- **`trajectory = 'stable'` on 155 of 155** (the pre-W3-3a `or 0.0` coercion; `cell_evolution_gradient_score` is 0 of 280 populated). Current code stores NULL (local run). **`asymmetry_score = 0.0` on 155 of 155**, but `asymmetry_score` is NULL on 280 of 280 upstream cells: the loader still coerces `or 0.0` (`platform/python-sidecar/pipeline/orchestrator/writers/ph_sankrama.py:259`), asserting 'symmetric' where nothing was measured.
- **`cdlm_cell_id` resolves for 0 of 155** - `bodha_cdlm_cells` was rebuilt (280 cells now, ids changed) - so every row's `cdlm_cell_id` and `bridge_path_jsonb.cdlm_cell_id` dangle. The asset's own integrity SQL (L2-drift clause `JOIN bodha_cdlm_cells c ON c.cell_id = s.cdlm_cell_id`) returns **true** on this state because the join finds nothing to compare: the check cannot fail on a dangling reference.
- `cascade_depth = 1` on 155 and `cascade_chain_jsonb` present on 135; `mitigation_ref` NULL on 155 (the engine comment says 'set post-facto by writer', no code does).

Build history for this asset (all charts, `build_run_assets`): 9 aborted, 37 complete, 26 error/blocked_dependency, 19 queued; the last complete canonical-chart run is `cbd6ea44` (2026-08-13), and the 26+ `error/blocked_dependency` rows are cascade skips, not writer errors. The only non-cascade errors on record: none; 9 aborts (last 2026-07-13).

### 1.2 - Stored rows versus current code

Commits touching this asset's writer or engine AFTER its last build (2026-08-13 01:16 UTC): `79fda3d2c` 2026-09-05 L4 W3-3a: ph_sankrama — recover 250 destroyed rows, stop inventing a trajectory (#1788).

`79fda3d2c` (W3-3a, 2026-09-05): the 'transition' -> 'general' map that destroyed 250 rows (10%) is emptied, and an unmeasured gradient becomes NULL not 'stable'. The 155 stored rows still carry 'stable'. The row count a rebuild yields depends on how many anchors exist (the 2,510 floor was 139 anchors x their domains' material cells).

### 1.3 - Census cells (fresh run, compared with the saved run)

Census used: fresh census `/Users/Dev/suvarna-evidence/census_fresh/1e5781a/census_L4.json` (generated 2026-10-02T10:12:59+05:30, chart 482012f1, inspector 1e5781a at REGISTRY_REVISION 10; outside the repo) compared with the repo's saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L4.json` (2026-09-30T20:23:50+05:30, inspector 2a78ec64d). Main's inspector is now at REGISTRY_REVISION 15: the offline rollup below applies its rules to the fresh census; no live re-measure was run.

| gate | criterion | fresh verdict | measured (fresh census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13): complete with no disposition and not derivable as probe-green (no probe receipt names this run) — unclassified |
| Null | Null.schema_default | PARTIAL (saved 2026-09-30: (absent in saved run)) | no schema default on the declared prose column(s) mechanism_text; writer literal fallbacks and constant columns are not measured here, so this is never PASS |
| Null | Null.blank_rows | PARTIAL (saved 2026-09-30: (absent in saved run)) | no blank or placeholder row among the checkable prose rows; schema defaults are read by Null.schema_default and writer literal fallbacks and constant columns are not measured, so this is never PASS |
| Narr | Narr.agree | PARTIAL (saved 2026-09-30: (absent in saved run)) | all 1 declared prose entry resolve to column(s) of phala_sankrama (names, and JSON types for path entries; the writer binding is the declaration tests' claim, not read here); but the writer also writes prose-vocabulary column(s) it does not declare (undeclared): phala_sankrama.falsifier |
| Narr | Narr.fidelity_test | PARTIAL (saved 2026-09-30: (absent in saved run)) | 3 test file(s) call the builder and assert (test_ph_a5_fixes.py, test_ph_sankrama_domain_and_trajectory.py, test_ph_wave4.py): tests call the builder but none names a declared field (direct or indirect); declared: mechanism_text; structural only, never PASS |
| Narr | Narr.lint | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — the narration lints are not applicable to this asset: no chart_facts fact_category selection in its 4-file writer scope and no declared column the raw-token lint covers; a clean scan of code they cannot see is not a pass |
| Dens | Dens.served | FAIL | STRUCTURAL: 1 module(s) reach it by code: L4_phala/query_phala_calibration.ts; 1 served select(s) of its table; no referencing capability that serves it declares density_contract |
| Build | Build.dep_liveness | PARTIAL | 1/2 declared dependencies lit at chart 482012f1 (or global); stale: ['ph_nimitta (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Build | Build.completion | FAIL | build record rows_written=2510 disagrees with live=155 (count_sql over the target table; chart 482012f1) |
| Build | Build.history | PARTIAL | latest run complete, but 0 error(s) and 9 abort(s) on record (26 additional blocked_dependency row(s) excluded as cascade-only). |
| Count | Count.floor | FAIL | live=155, floor=2510, delta=-2355 |
| Complete | Complete.depth | PARTIAL | 630 rows, 26 cols; fully populated 24; NEVER populated ['mitigation_ref'] |
| Complete | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach | Reach.fields | NOT_GENERIC | reported, not graded — width 19/25 built column(s) (76.0%) selected by 1 capability module(s); dark: ['bridge_path_jsonb', 'cascade_chain_jsonb', 'chart_id', 'computed_at', 'derivation_ledger_jsonb', 'source_citation']; depth 100.0% (a capability query reads it with no literal row pin (upper bound)) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13): complete with no disposition and not derivable as probe-green (no probe receipt names this run) — unclassified |
| Earn | Earn.service_state | N/A (saved 2026-09-30: (absent in saved run)) | declared kind 'data' is not `service`; Earn.service_state is the service-state check (a service's rows_written cannot tell healthy-and-idle from broken) |

**PASS cells (compact):** Ldgr.source_presence, Idem.pattern, Vocab.identity, Narr.checkable, Build.registered, Build.contract, Build.target, Build.dag, Build.exercised, Build.count_integrity.

**Offline rollup** (main `asset_census.py` rollup rules at REGISTRY_REVISION 15 applied to the FRESH census; N/A reads NO_DETECTOR while `NA_RULE_DECISIONS` is empty; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null PARTIAL · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.
Same rules over the SAVED 2026-09-30 census: Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

### 1.4 - Earned-signal (N.8), narration-fidelity (N.7) and honest-null audit of this asset's flags and verdicts

| field / claim | what it claims | what code path could make it read false | finding |
|---|---|---|---|
| `trajectory` | strengthening / stable / weakening | gradient NULL upstream (0 of 280) -> NULL since W3-3a; 155 stored `stable` | real-stored; honest in current code |
| `asymmetry_score` | asymmetry of the linkage | `float(r.get('asymmetry_score') or 0.0)` (`platform/python-sidecar/pipeline/orchestrator/writers/ph_sankrama.py:259`) over an all-NULL column | **Unmeasured read as zero**; the same falsy-zero class W3-3a fixed for the gradient on the line above it |
| `projected_window_*`, `projected_peak_date` | independent timing of the spillover (lag from real activation windows) | falls back to the source window when the cell has none (all 280 cells) (`engine.py:91-94,124-125`) | **Not independent timing** (T2c warns exactly this); nothing in the row says which branch ran |
| `spillover_confidence` | confidence in the spillover | `source confidence_high x linkage`, cap 0.8 (`engine.py:194-198`); inherits the decorative band; 3 distinct values stored (0.3594-0.8) | **A product of a decorative number and a cell strength**; labelled `structural_not_yet_empirical` |
| `cascade_depth`, `cascade_chain_jsonb` | multi-hop A->B->C cascade up to depth 3 | `derive_cascade_chain` is never recursive (depth is always 0 at the call, `engine.py:250`), returns the first 3 cells in dictionary iteration order whose row-domain equals the target (`:171-189`); `cascade_depth` is 1 or 1 (`:287`); `next_cells` is unused (`:171`) | **Depth is a constant; hop selection is arbitrary (not ranked by linkage)** |
| row count | number of spillovers | 5 rows per spillover pair (one per ayanamsha cell), ayanamsha not stored | overcount x5 for any reader of row counts |
| `relationship_type` | contagion vs conflict | `contradicting_signal_pairs_count > 0` -> conflict (`engine.py:131-134`) | deterministic, from a cell fact |
| honest nulls / silent loader | fail loud if CDLM is unreadable | `_load_cdlm_cells` wraps the whole read in `except Exception: logger.warning; return []` (`platform/python-sidecar/pipeline/orchestrator/writers/ph_sankrama.py:273-275`): any read error yields zero spillover rows and a completed build | **Silent empty** (the F-16 class fixed in ph_suddha_sodhana, not here) |

### 1.5 - UUID chart_id check (the bo_*/ph_* adapter defect)

`chart_id` and `anchor_id` are psycopg parameters / `str(anchor['anchor_id'])` (`:78,101`); ledger ids are strings; the `json.dumps` sites (`:178-184`) take engine dicts of strings, floats and jsonb dicts. **Not present today.**

## 2 - Gaps: which are real, which are detector or definition gaps

Class vocabulary: **real** = a shortfall in code, rows, registry row or served surface; **real-stored** = the CURRENT code already fixes it but the stored rows predate the fix (cured by a rebuild, not by an edit); **design** = needs an SS or acharya decision; **detector** = the instrument is absent or its definition is the open point; **history** = a recorded past outcome no edit can change; **information** = Count/Cost/Complete/Reach, never a blocker; **opportunity** = beyond the requirement.

| gap id | gate | class | note (evidence) |
|---|---|---|---|
| ph_sankrama-G01 | Count / Build | real-stored | Build record 2,510 vs live 155; floor 2,510; the 155 rows are for the 4 surviving anchors; `trajectory=stable` x155 predates W3-3a |
| ph_sankrama-G02 | Vocab / Null | real | No ayanamsha column: 155 rows = 31 pairs x 5 ayanamshas (`phala_sankrama` columns; natural key includes `cdlm_cell_id`); row counts and `incoming_spillover_count` overstate 5-fold (Q-L4-14) |
| ph_sankrama-G03 | Null | real | `asymmetry_score or 0.0` over an all-NULL upstream column (`platform/python-sidecar/pipeline/orchestrator/writers/ph_sankrama.py:259`); 0.0 x155 |
| ph_sankrama-G04 | Carr | real | Projected window = source window on 155/155 (no activation windows upstream); not marked as a fallback |
| ph_sankrama-G05 | Earn | real | `cascade_depth` is constant 1 and the chain is the first 3 dict-order cells (`engine.py:158-189,250,287`) |
| ph_sankrama-G06 | Build | real | Dangling `cdlm_cell_id` x155 and an integrity clause that is vacuous when the cells are gone |
| ph_sankrama-G07 | Null | real | Silent empty on any CDLM read error (`:273-275`) |
| ph_sankrama-G08 | Earn | design | `spillover_confidence` = decorative band x linkage (Q-L4-05) |
| ph_sankrama-G09 | Null | real | `mitigation_ref` never populated (engine comment: set post-facto by writer; no code does) |
| ph_sankrama-G10 | Vocab | design | `wealth` anchors yield no spillover because CDLM has no `wealth` row domain although `wealth` is a CDLM column (20 target rows); declared in code, not in the registry |
| ph_sankrama-G11 | Narr / Dens | detector | Narr.agree PARTIAL (`falsifier` is written prose but undeclared); Dens.served FAIL; Earn, Carr, Vocab.alias NO_DETECTOR |
| ph_sankrama-G12 | Build | history | Build.history PARTIAL: 0 errors, 9 aborts |

## 3 - Disposition

DISPOSITION: enrich

EVIDENCE_POINTER: 00_ARCHITECTURE/briefs/suvarna/layers/L4/assets/ph_sankrama_ELEVATION_BRIEF_v1_0.md (sections 1-4); receipts `_evidence/` (data/, upstream_receipts.json, rollup_L4.json, offline_checks.txt, rect_diag.txt); census `layers/census/census_L4.json` + fresh census `census_fresh/1e5781a/census_L4.json`

**enrich (E) - fix the ayanamsha fan-out, asymmetry, cascade and silent loader; rebuild.** Enrich (E): the idea (ground cross-domain effects in CDLM cells, state the mechanism, give a falsifier) is the right L4 use of L2 and the W3-3a fix restored the rows a bad map destroyed, but the table currently overstates its content 5-fold, presents an unmeasured asymmetry as zero, and its 'independent timing' and 'cascade' are fallbacks and a constant. No consolidation or retirement proposed: one capability and `ph_phaladesa` read it.

Approver under Track A brief section 10: **Steward (G16)** for keep/qualify/enrich; **SS** for any output change (R5). No disposition is applied by this brief.

## 4 - Fix designs (one per real gap; anything marked `needs production rebuild` or `needs migration` is a REVIEW item for Strategic Suvarna)

### FD-1 - Rebuild after `ph_nimitta` (wave 8)

- **Answers:** G01, G06; CF-L4-01
- **Change:** Rebuild when anchors exist; the cell ids are regenerated by `bo_sangati`.
- **Files / declaration / migration:** none
- **Failing-first test and mutation:** failing-first: `cdlm_cell_id` resolves for 100% of rows; the L2-drift clause is non-vacuous (see FD-5)
- **Output change:** yes
- **Blast radius:** `ph_phaladesa` spillover counts
- **Rebuild:** needs production rebuild (REVIEW item)
- **Gate it moves:** Build, Count
- **Fix class:** data (rebuild); **risk class:** R3; **buildable before J1:** tier-independent
- **Decision:** OPEN - Q-L4-01

### FD-2 - Resolve the ayanamsha fan-out

- **Answers:** G02
- **Change:** Option A: add `ayanamsha_id` to the table and the natural key (additive; 155 rows stay 155, each labelled). Option B: collapse to one row per (anchor, target_domain, relationship_type) with `ayanamsha_agreement` (count of ayanamshas whose cell clears the threshold) and the cell ids in the ledger (31 rows). B changes the grain; A does not.
- **Files / declaration / migration:** migration (column + unique index) + `platform/python-sidecar/pipeline/orchestrator/writers/ph_sankrama.py:112-176`, `platform/python-sidecar/services/ph_sankrama/engine.py:207-293`
- **Failing-first test and mutation:** failing-first: no two rows share (anchor, target, cell ayanamsha); mutation: drop the ayanamsha from the key -> collision
- **Output change:** yes (structural)
- **Blast radius:** `ph_phaladesa.incoming_spillover_count`, `query_spillover_cascades`
- **Rebuild:** needs production rebuild
- **Gate it moves:** Vocab, Null
- **Fix class:** migration + writer code; **risk class:** R3; **buildable before J1:** tier-dependent
- **Decision:** OPEN - Q-L4-14

### FD-3 - Honest nulls: asymmetry, timing basis, cascade

- **Answers:** G03, G04, G05, G09
- **Change:** `asymmetry_score` None when the cell has None; record `timing_basis: activation_window | source_window_fallback` in the ledger and `bridge_path_jsonb`; either implement the multi-hop recursion (rank hops by linkage, stop at depth 3) and set `cascade_depth` from it, or drop `cascade_depth`/`cascade_chain_jsonb` and say one hop.
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_sankrama.py:255-262`; `platform/python-sidecar/services/ph_sankrama/engine.py:91-128,158-189,287`
- **Failing-first test and mutation:** failing-first: a NULL asymmetry stores NULL; a cell with no activation window records the fallback; a 3-hop fixture gives depth 3; mutation: restore `or 0.0` -> fails
- **Output change:** yes
- **Blast radius:** serving of those fields
- **Rebuild:** rides FD-1
- **Gate it moves:** Null, Earn
- **Fix class:** writer code (engine); **risk class:** R2; **buildable before J1:** tier-independent
- **Decision:** no question; Steward (the cascade policy is Q-L4-14)

### FD-4 - Fail loud on the CDLM read; make the L2-drift clause non-vacuous

- **Answers:** G07, G06
- **Change:** Remove the swallow in `_load_cdlm_cells`; change the integrity clause to also assert that every `cdlm_cell_id` resolves (an anti-join) rather than only comparing resolved rows.
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_sankrama.py:224-275`; registry `integrity_check_sql` (migration)
- **Failing-first test and mutation:** failing-first: the SQL returns false on the current state (155 dangling) and true after a rebuild; mutation: leave one dangling id -> false
- **Output change:** none
- **Blast radius:** registry row
- **Rebuild:** none
- **Gate it moves:** Build (integrity)
- **Fix class:** writer code + registry; **risk class:** R2; **buildable before J1:** tier-independent
- **Decision:** no question; Steward

### FD-5 - Edges, declarations, wealth

- **Answers:** G10, G11; CF-L4-10, CF-L4-11
- **Change:** Declare the wealth divergence in the registry; declare `falsifier` in `prose_fields`; Dens declaration is CF-L4-11.
- **Files / declaration / migration:** `asset_declarations.json`
- **Failing-first test and mutation:** Narr.agree leaves PARTIAL; mutation: remove the declaration -> PARTIAL returns
- **Output change:** none
- **Blast radius:** census inputs
- **Rebuild:** none
- **Gate it moves:** Narr
- **Fix class:** registry/declaration; **risk class:** R1; **buildable before J1:** tier-independent
- **Decision:** no question; Track E

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L4-01** - *this asset:* rebuild wave 8
- **CF-L4-03** - *this asset:* integrity SQL vacuous on dangling ids
- **CF-L4-04** - *this asset:* asymmetry 0.0, spillover_confidence
- **CF-L4-05** - *this asset:* silent CDLM loader
- **CF-L4-10** - *this asset:* `falsifier` prose undeclared
- **CF-L4-11** - *this asset:* Dens FAIL
- **CF-L4-12** - *this asset:* floor 2,510 is a count a different anchor set produced

## 5 - Semantic fingerprint contract (for the rebuild plan)

Natural key `(chart_id, source_anchor_id, cdlm_cell_id, target_domain, relationship_type)` (UNIQUE `phala_sankrama_natural_key`). Fingerprint over `(source_anchor_id, target_domain, relationship_type, linkage_strength, projected_window_*, trajectory)`; `sankrama_id`, `computed_at` excluded. Depends on both `anchor_id` (from `ph_nimitta`) and `cell_id` (regenerated by `bo_sangati`): neither is stable across upstream rebuilds, so compare on `(source_domain, target_domain, relationship_type, linkage_strength)` instead.

## 6 - Preserved kernel, carriage check, opportunities

- **Preserved kernel:** Grounding every row in a CDLM cell with its linkage and bridge seeds, the empty (identity) domain map and the loud declaration of the one divergence (wealth), NULL trajectory when the gradient is unknown, accepted-row counting, falsifier per row.
- **Carriage check (T4 4.1; one only):** D3: recompute `linkage_strength` and `target_domain` from `bodha_cdlm_cells` by `cdlm_cell_id` (the integrity SQL does this, but only over resolved ids) and recount the material cells per anchor domain; deterministic.
- **By design, stated and not flagged:** `structural_not_yet_empirical` and the 0.8 cap are the no-self-calibration stance; the 0.25 linkage threshold is a declared constant (`platform/python-sidecar/pipeline/orchestrator/writers/ph_sankrama.py:26`, `engine.py:26`).
- **Opportunities (never blocking):** expose `bridge_path_jsonb` and `cascade_chain_jsonb` (dark); ayanamsha agreement as a measured robustness signal (the thing `ph_nimitta.ayanamsha_robustness` pretends to carry).

## 7 - Decisions applied, questions for SS, Track I items arising

No decision has been applied: SS has not yet answered the A.L4 questions. This brief raises:

- **Q-L4-01** - Rebuild authority and order (see INDEX).
- **Q-L4-05** - Is `spillover_confidence` (decorative band x linkage) allowed in L4?
- **Q-L4-14** - Keep 5 rows per spillover with an ayanamsha column, or collapse to one row with an agreement count? Implement the multi-hop cascade or drop it?

**Track I items arising (see INDEX section 8):** TI-L4-01, TI-L4-27, TI-L4-28, TI-L4-29, TI-L4-30, TI-L4-31.

