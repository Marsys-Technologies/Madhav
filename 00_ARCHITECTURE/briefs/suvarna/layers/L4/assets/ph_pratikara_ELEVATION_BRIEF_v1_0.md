---
asset_id: ph_pratikara
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
disposition: "enrich (E) - fix the cost tiering, the graha fallback and the fan-out before promoting from DRAFT; rebuild after L3"
disposition_proposal_approver: "Steward (G16); any output change to SS (R5)"
disposition_value: enrich
risk_class: "R3 (DRAFT status, upstream attribution-state coupling, remedy claims; code fixes R1-R2)"
decisions_applied: "none - SS has not answered the A.L4 questions (INDEX section 7); all dispositions and fix designs are proposals"
ss_questions: [Q-L4-01, Q-L4-13, Q-L4-05]
track_i_items: [TI-L4-01, TI-L4-22, TI-L4-23, TI-L4-24, TI-L4-25, TI-L4-26]
ledger_gap_ids: [ph_pratikara-Build.dep_liveness, ph_pratikara-Build.history, ph_pratikara-Carr.detector, ph_pratikara-Complete.depth, ph_pratikara-Cost.baseline, ph_pratikara-Dens.served, ph_pratikara-Earn.build_record]
---
# ph_pratikara - Mitigation programme per obstruction

> **PROVISIONAL - until J1; may register gaps, may not certify.** Every figure below comes from a stated read-only query (suvarna_reader SELECTs on 2026-10-03, receipts under `/Users/Dev/suvarna-evidence/A_L4/data/`), from the census, from the repository at main `3de3f8b15` (file:line), or from running the asset's pure engine functions locally with no database. Where something could not be determined it says so. Nothing here certifies a gate, approves a disposition or changes an asset.

## 0 - Identity: what the asset is

`ph_pratikara` writes `phala_mitigation`: one row per `kala_obstruction` row (strict 1:1, registry note), bridged to its `kala_convergence` row for the window, domain and afflicting graha (`constituent_factors->>'planet'`, `platform/python-sidecar/pipeline/orchestrator/writers/ph_pratikara.py:203-231`). For each obstruction it selects the graha's `bodha_rm_remedy_prescriptions` (bo_upaya), topologically orders them by prerequisites and drops incompatibles (`platform/python-sidecar/services/ph_pratikara/engine.py:63-111`), bins them into free / low_cost / high_investment by `max_inr` (`:115-148`), counts distinct traditions (`:151-160`), derives an intensity tier from obstruction severity x the linked anchor's magnitude (`:163-170`) and sets a re-evaluation date (`:229-239`) and an outcome hook for L5. The linked anchor is the domain-matched influenceable anchor, preferring window overlap, else NULL (`_select_anchor`, `platform/python-sidecar/pipeline/orchestrator/writers/ph_pratikara.py:38-62`; F-3.4). The registry marks the asset `catalog_status = DRAFT`, the only DRAFT among the nine.

| field | value | source |
|---|---|---|
| kind | registry `asset_kind=artifact`, `asset_type=data`, `scope=per_chart`, `domain=chart`, `rung=R4`; role per L4 layer instance TG-L4-024: not assigned by any tier | `asset_registry` row, read 2026-10-03 |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2732` (live may differ by migration) | seed |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ph_pratikara.py:85`; engine `platform/python-sidecar/services/ph_pratikara/engine.py`; registry `has_writer=True` | code |
| target table(s) | `phala_mitigation` | registry `target_table` / `count_sql` |
| live rows (canonical chart) / floor / build record | 536 / 536 / `rows_written=536`; rows per chart in the table(s): phala_mitigation: 1c826d5a=741; 482012f1=536 | `count_sql` run read-only; `asset_throughput`; table group-by |
| state / last built | `stale` / 2026-08-13T01:16:05 UTC (run `cbd6ea44`); `built_against_writer_hash=unknown` | `asset_throughput` |
| catalog_status | DRAFT | registry |
| depends_on (declared, live) | `ph_nimitta`, `bo_upaya`, `ka_vighnakara`, `ka_sangam` | `asset_registry.depends_on` |
| depends_on vs what the code reads | reads `kala_obstruction` + `kala_convergence` (`ka_vighnakara`, `ka_sangam` declared), `phala_anchors` (`ph_nimitta`), `bodha_rm_remedy_prescriptions` (`bo_upaya`; the registry `target_table` of `bo_upaya` is `bodha_rm_resonances`, the prescriptions table is a co-table). No undeclared read found. The census Build.dag reads PASS | code (file:line) + fresh census `Build.dag` |
| blast radius | declared dependents direct 2 / transitive 11 (active assets, every layer) | fresh census `blocking_radius` |
| code readers outside the asset (non-test py/ts/tsx, 19 files) | L5 / other writers (python-sidecar pipeline/orchestrator/writers): ph_phaladesa.py, ph_suddha_sodhana.py; python-sidecar other: brahmagyan/phala/l4_outlook.py, brahmagyan/phala/mitigation.py, pipeline/brahma_pipeline.py, pipeline/orchestrator/dag_edge_guard.py, run_ph_pratikara_prod.py, services/ka_tulana/ranker.py; serving (platform-mcp/src): lib/kala_upaya_diagnosis.ts, tools/kala_views/upaya.ts, tools/phala_mitigation_map.ts, tools/phala_outlook.ts; retrieval + app (platform/src): lib/jyotish/asset_names.ts, lib/retrieval/registry/knowledge/producer_editorial_review.ts, lib/retrieval/registry/knowledge/source_query_availability.ts, lib/retrieval/registry/layers/L4_phala/index.ts, lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts, lib/retrieval/registry/layers/L4_phala/salience_order.ts, lib/retrieval/registry/tool_name_bridge.ts | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src at `3de3f8b15` (tests, generated and migrations excluded) |
| served surface | `L4_phala/query_phala_calibration.ts` `query_remedy_program` (5 modules reach it, a tier column selected without a contract); `platform-mcp/src/tools/phala_mitigation_map.ts`, `phala_outlook.ts`, `kala_views/upaya.ts`, `lib/kala_upaya_diagnosis.ts` (the last keys `efficacy_tier` off `citation !== null`) | code |
| role / scoring mode | manifestation-family asset of L4 Phala (T2 section 6.5); census `scoring: contribution`; 'sequenced, conflict-aware mitigation programmes' (T2c); T2 says L2 owns prescriptions and L4 retains feasibility while binding obstruction/domain/window | tiers + census |
| invalidation / FK | `linked_anchor_id -> phala_anchors ON DELETE SET NULL`; `obstruction_id` has no FK | `pg_constraint` read 2026-10-03 |

## 1 - Measured state and the nine gates

### 1.1 - Live state on the canonical chart (read-only, 2026-10-03)

- **536 rows** = 536 obstructions of the pre-wipe build; **`kala_obstruction` now has 0 rows for the canonical chart**, so all 536 `obstruction_id`s dangle (the registry integrity SQL's tiling clause is **false**: 536 mitigation rows without an obstruction; reader run of the SQL = false). The other built chart is intact (741 = 741).
- **Every programme is empty.** `program_jsonb.total_scheduled = 0` on **536 of 536**, `recommended_tier_jsonb` has no entries, `cross_tradition_corroboration = 0` on 536. (Cause: the prescription read selected nonexistent columns until `5f097e738` fixed it on 2026-08-21, eight days after this build; registry note 'empty programmes'.)
- **One invented citation on every row**: `classical_citation = 'Brihat Parashara Hora Shastra - Upaya chapter'` on 536 of 536, `source_id` NULL on 536 (`initiation_muhurta_ref` NULL on 536). W3-3j (`938351c65`) removed the fabrication in code: with no prescription the record now carries `classical_citation = None` (local run).
- **`linked_anchor_id` NULL on 536** (anchors removed; SET NULL), `intensity_tier = light` on 536 from `severity x anchor_magnitude = minor`, `afflicting_graha = saturn` on 492 and blank on 44 (those 44 also have NULL windows). Across both charts `afflicting_graha` is `saturn` on 1,193 of 1,277 rows and blank on 84: the bridge yields one graha.
- **What a rebuild would load** (read-only counts, canonical chart): 135 prescriptions, 15 per graha for all nine grahas, all tradition `parashari`, **none with prerequisites or incompatibles** (0 and 0), **none with `max_inr`** in the cost dict (the field is `{available: false, cost_tier: free 60 / low 40 / medium 10 / null 25}`), `classical_sources_jsonb.source_id` = `BPHS` 70 / `classical_tradition` 65.

Build history for this asset (all charts, `build_run_assets`): 9 aborted, 37 complete, 26 error/blocked_dependency, 19 queued; the last complete canonical-chart run is `cbd6ea44` (2026-08-13), and the 26+ `error/blocked_dependency` rows are cascade skips, not writer errors. The only non-cascade errors on record: none; 9 aborts (last 2026-07-13).

### 1.2 - Stored rows versus current code

Commits touching this asset's writer or engine AFTER its last build (2026-08-13 01:16 UTC): `37de14edc` 2026-09-06 fix(ph_pratikara): F-3.4 -- match obstruction domain to anchor, don't grab the first one found anywhere (#183…; `93ba7b539` 2026-09-06 L4 W3-3l: ph_pratikara — propagate classical_sources_jsonb.source_id (F-6, partial) (#1864); `938351c65` 2026-09-05 L4 W3-3j: ph_pratikara — stop fabricating a classical citation (F-3/F-5, hard-floor) (#1854); `5f097e738` 2026-08-21 fix(parisesa): F-173 — ph_pratikara SELECTs nonexistent columns → empty prescriptions for every chart (#1454).

Four fixes landed after the build: `5f097e738` (2026-08-21, F-173: prescriptions SELECT repaired), `938351c65` (W3-3j, 2026-09-05: no invented citation), `93ba7b539` (W3-3l, F-6: `source_id` propagated), `37de14edc` (F-3.4, 2026-09-06: domain-matched anchor selection). All 536 stored rows predate all four. Deployed writer version not observable.

### 1.3 - Census cells (fresh run, compared with the saved run)

Census used: fresh census `/Users/Dev/suvarna-evidence/census_fresh/1e5781a/census_L4.json` (generated 2026-10-02T10:12:59+05:30, chart 482012f1, inspector 1e5781a at REGISTRY_REVISION 10; outside the repo) compared with the repo's saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L4.json` (2026-09-30T20:23:50+05:30, inspector 2a78ec64d). Main's inspector is now at REGISTRY_REVISION 15: the offline rollup below applies its rules to the fresh census; no live re-measure was run.

| gate | criterion | fresh verdict | measured (fresh census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13): complete with no disposition and not derivable as probe-green (no probe receipt names this run) — unclassified |
| Null | Null.schema_default | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — prose_fields is undeclared for ph_pratikara: never read as 'no prose' |
| Null | Null.blank_rows | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — prose_fields is undeclared for ph_pratikara: never read as 'no prose' |
| Narr | Narr.agree | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — prose_fields is undeclared for ph_pratikara: never read as 'no prose' |
| Narr | Narr.checkable | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — prose_fields is undeclared for ph_pratikara: never read as 'no prose' |
| Narr | Narr.fidelity_test | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — prose_fields is undeclared for ph_pratikara: never read as 'no prose' |
| Narr | Narr.lint | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — prose_fields is undeclared for ph_pratikara: never read as 'no prose' |
| Dens | Dens.served | FAIL | STRUCTURAL: 5 module(s) reach it by code: L4_phala/query_phala_calibration.ts, platform-mcp/src/tools/kala_views/upaya.ts, platform-mcp/src/tools/phala_mitigation_map.ts, platform-mcp/src/tools/phala_outlook.ts, platform-mcp/src/lib/kala_upaya_diagnosis.ts; 2 served select(s) of its table; no referencing capability that serves it declares density_contract; a tier column is selected without a contract in: L4_phala/query_phala_calibration.ts |
| Build | Build.dep_liveness | PARTIAL | 0/4 declared dependencies lit at chart 482012f1 (or global); stale: ['ph_nimitta (stale, chart 482012f1)', 'bo_upaya (stale, chart 482012f1)', 'ka_vighnakara (stale, chart 482012f1)', 'ka_sangam (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Build | Build.history | PARTIAL | latest run complete, but 0 error(s) and 9 abort(s) on record (26 additional blocked_dependency row(s) excluded as cascade-only). |
| Complete | Complete.depth | PARTIAL | 1277 rows, 22 cols; fully populated 16; NEVER populated ['initiation_muhurta_ref', 'source_id'] |
| Complete | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach | Reach.fields | NOT_GENERIC | reported, not graded — width 15/20 built column(s) (75.0%) selected by 1 capability module(s); dark: ['chart_id', 'computed_at', 'derivation_ledger_jsonb', 'outcome_hook_jsonb', 'source_citation']; depth 100.0% (a capability query reads it with no literal row pin (upper bound)) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13): complete with no disposition and not derivable as probe-green (no probe receipt names this run) — unclassified |
| Earn | Earn.service_state | N/A (saved 2026-09-30: (absent in saved run)) | declared kind 'data' is not `service`; Earn.service_state is the service-state check (a service's rows_written cannot tell healthy-and-idle from broken) |

**PASS cells (compact):** Ldgr.source_presence, Idem.pattern, Vocab.identity, Build.registered, Build.contract, Build.target, Build.dag, Build.exercised, Build.completion, Build.count_integrity, Count.floor.

**Offline rollup** (main `asset_census.py` rollup rules at REGISTRY_REVISION 15 applied to the FRESH census; N/A reads NO_DETECTOR while `NA_RULE_DECISIONS` is empty; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build PARTIAL.
Same rules over the SAVED 2026-09-30 census: Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build PARTIAL.

### 1.4 - Earned-signal (N.8), narration-fidelity (N.7) and honest-null audit of this asset's flags and verdicts

| field / claim | what it claims | what code path could make it read false | finding |
|---|---|---|---|
| `recommended_tier_jsonb` (free / low_cost / high_investment) | an economics tiering of the remedies | `max_cost = cost_range.get('max_inr', 0)`; `0` -> free (`platform/python-sidecar/services/ph_pratikara/engine.py:131-143`). Upstream never writes `max_inr` (0 of 135), only `cost_tier`. Local run: a prescription with `cost_tier='medium'` and no `max_inr` lands in `free` | **Every remedy would be labelled free** - a gemstone as costless. The qualitative `cost_tier` the corpus supplies is ignored. Real defect for the first non-empty rebuild |
| `classical_citation` | the source of the remedy | first non-empty citation among the graha's prescriptions (`platform/python-sidecar/services/ph_pratikara/engine.py:266-269`), one string for a programme of many remedies; honest None when none (since `938351c65`) | stored: invented string x536 (real-stored). Current: a programme-level citation borrowed from its first prescription, not a per-remedy one |
| `source_id` | the corpus source | first non-empty `source_id` (`:276-279`); 65 of 135 upstream rows say `classical_tradition` | the token SS ruled NOT acceptable as provenance for L0 (A.L0 Q3: `attribution_state`); it will propagate into this column unchanged |
| `afflicting_graha` / prescriptions chosen | remedies for the planet afflicting THIS obstruction | prescriptions by graha key (`platform/python-sidecar/pipeline/orchestrator/writers/ph_pratikara.py:139`); obstruction_type fallback `prescriptions_by_graha.get(obs_type)` can never match (keys are graha names, `:142`); then `jupiter` (`:144`) | **Plausible default**: an obstruction with no known planet gets Jupiter's remedies (44 rows today). And since all bridged grahas are Saturn, the 492 programmes are the same 15 prescriptions |
| `intensity_tier` | remedy intensity proportional to severity x magnitude | lookup table `platform/python-sidecar/services/ph_pratikara/engine.py:30-43`; severity from obstruction `severity` (only low/medium on the data), magnitude from the linked anchor or `moderate` | a deterministic table; with `anchor_magnitude=minor` on every stored row it was constant `light` |
| `re_evaluation_date` | date to re-check the obstruction | `window_end`, else `date.today() + 90 d` (`platform/python-sidecar/services/ph_pratikara/engine.py:236-239`) | calendar-dependent for 44 rows (no window) |
| `outcome_hook_jsonb.question` | a falsifiable question for L5 | "Did the {severity} obstruction ease by {date}?" (`platform/python-sidecar/services/ph_pratikara/engine.py:243-247`) | severity is the mapped low/medium/high word, not an observable; not falsifiable by a life event as written |
| `rows_written` | rows inserted | `rows_inserted += 1` unconditional beside `ON CONFLICT DO NOTHING` (`platform/python-sidecar/pipeline/orchestrator/writers/ph_pratikara.py:182-198`) | latent (one row per obstruction id); same counting pattern fixed elsewhere |

### 1.5 - UUID chart_id check (the bo_*/ph_* adapter defect)

`chart_id` is a psycopg parameter only (`:95,102,229,245,272`); `obstruction_id` is an int, `linked_anchor_id` `str(a['anchor_id'])` (`_select_anchor`, `:60,62`), `prescription_id` `str(...)` (`:284`). The `json.dumps` sites (`:187-195`) carry those strings. **Not present today.**

## 2 - Gaps: which are real, which are detector or definition gaps

Class vocabulary: **real** = a shortfall in code, rows, registry row or served surface; **real-stored** = the CURRENT code already fixes it but the stored rows predate the fix (cured by a rebuild, not by an edit); **design** = needs an SS or acharya decision; **detector** = the instrument is absent or its definition is the open point; **history** = a recorded past outcome no edit can change; **information** = Count/Cost/Complete/Reach, never a blocker; **opportunity** = beyond the requirement.

| gap id | gate | class | note (evidence) |
|---|---|---|---|
| ph_pratikara-G01 | Earn / Carr | real-stored | 536/536 programmes empty, 536/536 invented citation, 536/536 `linked_anchor_id` NULL: the stored rows are pre-fix output (`5f097e738`, `938351c65`, `37de14edc`) |
| ph_pratikara-G02 | Build | real | 536 `obstruction_id`s dangle (`kala_obstruction` has 0 rows for the chart); the asset's tiling integrity clause is false; Build.completion PASS (536 = 536) earns nothing |
| ph_pratikara-G03 | Vocab / Null | real | Cost tiering reads `max_inr`, the upstream carries `cost_tier`: every remedy would be `free` (`engine.py:131-143`) |
| ph_pratikara-G04 | Narr | real | Fallback to Jupiter's prescriptions for an obstruction with no planet (`:144`) and a dead `obstruction_type` fallback (`:142`) |
| ph_pratikara-G05 | Ldgr / Carr | design | `source_id` will carry `classical_tradition` (65 of 135 upstream rows); a programme-level citation is borrowed from its first prescription |
| ph_pratikara-G06 | Narr | real | Fan-out: grain is one row per obstruction but content is per graha - 492 rows share the same 15 prescriptions (all bridged grahas are Saturn); topological order and incompatibility exclusion run on 0 prerequisites and 0 incompatibles |
| ph_pratikara-G07 | Null | real | `initiation_muhurta_ref` never populated: the engine comment says the writer sets it after `ph_muhurta` (`engine.py:194,301`) but no code does and `ph_muhurta` is not a dependency; `source_id` NULL on all stored rows |
| ph_pratikara-G08 | Build | real | `rows_inserted += 1` unconditional (`platform/python-sidecar/pipeline/orchestrator/writers/ph_pratikara.py:198`) |
| ph_pratikara-G09 | Build | design | `catalog_status = DRAFT`: no tier defines DRAFT or when it ends (TG-L4-006); the serving layer serves it without distinction (Q-L4-13) |
| ph_pratikara-G10 | Dens | detector | Dens.served FAIL (5 modules reach it, 2 selects, a tier column selected without a contract) |
| ph_pratikara-G11 | Null / Narr | detector | `prose_fields` undeclared: Null.* / Narr.* NO_DETECTOR; Earn, Carr, Vocab.alias NO_DETECTOR |
| ph_pratikara-G12 | Build | history | Build.history PARTIAL: 0 errors, 9 aborts |

## 3 - Disposition

DISPOSITION: enrich

EVIDENCE_POINTER: 00_ARCHITECTURE/briefs/suvarna/layers/L4/assets/ph_pratikara_ELEVATION_BRIEF_v1_0.md (sections 1-4); receipts `_evidence/` (data/, upstream_receipts.json, rollup_L4.json, offline_checks.txt, rect_diag.txt); census `layers/census/census_L4.json` + fresh census `census_fresh/1e5781a/census_L4.json`

**enrich (E) - fix the cost tiering, the graha fallback and the fan-out before promoting from DRAFT; rebuild after L3.** Enrich (E): the design (consume bo_upaya, never author remedy text, honour prerequisites and conflicts, proportionality, outcome hook) is right and the W3 fixes removed the worst fabrications, but the asset has never produced a single non-empty programme on the canonical chart, its cost tiering would label all remedies free the moment it does, and it is DRAFT. It should not be promoted before a rebuild shows non-empty, correctly tiered, per-remedy-cited programmes. No consolidation or retirement is proposed: the capability and four MCP tools read it.

Approver under Track A brief section 10: **Steward (G16)** for keep/qualify/enrich; **SS** for any output change (R5). No disposition is applied by this brief.

## 4 - Fix designs (one per real gap; anything marked `needs production rebuild` or `needs migration` is a REVIEW item for Strategic Suvarna)

### FD-1 - Rebuild after L3 (wave 8) and re-measure

- **Answers:** G01, G02; CF-L4-01
- **Change:** Rebuild after `ka_vighnakara` has repopulated `kala_obstruction` and `ph_nimitta` has anchors; until then a rebuild would write 0 rows and be `dormant` (target_floor 536 > 0).
- **Files / declaration / migration:** none
- **Failing-first test and mutation:** failing-first: Build.completion PASS and the tiling clause true with non-empty programmes; mutation: delete one obstruction -> tiling false
- **Output change:** yes - all rows
- **Blast radius:** `ph_phaladesa` (mitigation_available), mitigation serving
- **Rebuild:** needs production rebuild (REVIEW item)
- **Gate it moves:** Build
- **Fix class:** data (rebuild); **risk class:** R3; **buildable before J1:** tier-independent
- **Decision:** OPEN - Q-L4-01

### FD-2 - Tier remedies by the qualitative cost_tier the corpus supplies

- **Answers:** G03
- **Change:** Use `estimated_cost_inr_range.cost_tier` (free / low / medium / high) when `max_inr` is absent; if neither exists put the remedy in an explicit `cost_unknown` bucket - never `free`.
- **Files / declaration / migration:** `platform/python-sidecar/services/ph_pratikara/engine.py:115-148`; `platform/python-sidecar/pipeline/orchestrator/writers/ph_pratikara.py:286-300` (pass `cost_tier` through)
- **Failing-first test and mutation:** failing-first: `tier_prescriptions` of a `cost_tier='medium'` remedy lands in medium/high, a no-cost remedy lands in `cost_unknown`; mutation: restore `max_inr` default 0 -> free (extends `test_ph_wave4.py::TestTierPrescriptions`)
- **Output change:** yes - `recommended_tier_jsonb` shape gains a key
- **Blast radius:** serving of `recommended_tier_jsonb`
- **Rebuild:** rides FD-1
- **Gate it moves:** Narr, Null
- **Fix class:** writer code (engine); **risk class:** R2; **buildable before J1:** tier-independent
- **Decision:** no question; Steward

### FD-3 - Remove the plausible fallbacks; keep the fan-out honest

- **Answers:** G04, G06
- **Change:** Drop the Jupiter fallback and the dead obstruction_type lookup: an obstruction with no planet gets an empty programme with `afflicting_graha NULL`, stated. Decide whether one row per obstruction with an identical per-graha programme is intended; if not, store the programme once per graha and reference it.
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_pratikara.py:136-145`
- **Failing-first test and mutation:** failing-first: a graha-less obstruction produces `total_scheduled = 0`; mutation: restore the jupiter fallback -> fails
- **Output change:** yes (44 rows today lose borrowed remedies)
- **Blast radius:** mitigation serving
- **Rebuild:** rides FD-1
- **Gate it moves:** Narr
- **Fix class:** writer code; **risk class:** R2; **buildable before J1:** tier-independent for the fallback; the grain is Q-L4-13
- **Decision:** OPEN - Q-L4-13

### FD-4 - Carry the upstream attribution state; cite per remedy

- **Answers:** G05
- **Change:** When A.L0 TI-L0-09 lands (`attribution_state` on the L0 catalogues) and bo_upaya carries it per prescription, copy it per scheduled remedy into the programme and stop collapsing a programme to one citation/`source_id`. Until then store `source_id` only when it is not `classical_tradition`.
- **Files / declaration / migration:** `platform/python-sidecar/services/ph_pratikara/engine.py:262-279`
- **Failing-first test and mutation:** failing-first: a programme of mixed sources keeps each remedy's citation; mutation: collapse -> fails
- **Output change:** yes
- **Blast radius:** `kala_upaya_diagnosis.ts` keys efficacy off `citation !== null`
- **Rebuild:** rides FD-1
- **Gate it moves:** Ldgr, Carr
- **Fix class:** writer code; **risk class:** R3; **buildable before J1:** tier-dependent (A.L0 Q3 ruling is PROVISIONAL until J1)
- **Decision:** OPEN - Q-L4-13

### FD-5 - Counting, dead column, declarations

- **Answers:** G07, G08, G10, G11; CF-L4-06, CF-L4-10, CF-L4-11
- **Change:** Count accepted rows (`cur.rowcount == 1`); either wire `initiation_muhurta_ref` or drop it; declare `prose_fields` (`proportionality_basis`, `outcome_hook_jsonb.question`).
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_pratikara.py:182-198`; declarations
- **Failing-first test and mutation:** failing-first: duplicate-key insert not counted; mutation: restore -> fails
- **Output change:** none
- **Blast radius:** build record
- **Rebuild:** none
- **Gate it moves:** Build, Null
- **Fix class:** writer code + declaration; **risk class:** R1; **buildable before J1:** tier-independent
- **Decision:** no question; Steward

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L4-01** - *this asset:* rebuild wave 8; all 536 rows are pre-fix output
- **CF-L4-02** - *this asset:* dangling `kala_obstruction` ids; upstream rebuild order
- **CF-L4-03** - *this asset:* Build.completion PASS (536 = 536) earns nothing
- **CF-L4-06** - *this asset:* unconditional `rows_inserted += 1`
- **CF-L4-08** - *this asset:* `date.today() + 90 d` re-evaluation date
- **CF-L4-10** - *this asset:* `prose_fields` undeclared
- **CF-L4-11** - *this asset:* Dens FAIL
- **CF-L4-12** - *this asset:* floor 536 and DRAFT status

## 5 - Semantic fingerprint contract (for the rebuild plan)

Natural key `(chart_id, obstruction_id, intensity_tier)` (live UNIQUE; `obstruction_id` is the serial of `kala_obstruction`, which changes on every `ka_vighnakara` rebuild). Fingerprint over `(obstruction_id, afflicting_graha, intensity_tier, program_jsonb.scheduled_ids, recommended_tier_jsonb, linked_anchor_id)`; `mitigation_id`, `computed_at` excluded; `re_evaluation_date` is calendar-dependent when no window exists (44 rows).

## 6 - Preserved kernel, carriage check, opportunities

- **Preserved kernel:** One programme per obstruction; consume-never-author (a test asserts no authored remedy text, `test_ph_wave4.py::test_anti_drift_no_authored_remedy_text`); topological order + conflict exclusion machinery; severity mapping (mild/moderate/severe -> low/medium/high) checked by the integrity SQL; honest None citation; domain-matched anchor selection with an honest NULL.
- **Carriage check (T4 4.1; one only):** D1 (source correspondence): for a sample of programmes, each scheduled `prescription_id` must exist in `bodha_rm_remedy_prescriptions` for the chart and the stored citation must equal that prescription's `classical_sources_jsonb.citation`; plus the severity mapping (already in the SQL). Deterministic.
- **By design, stated and not flagged:** DRAFT catalogue status is a registry fact, not a defect by itself. 'L2 owns prescriptions; L4 consumes' (T2c) is the intended division.
- **Opportunities (never blocking):** expose the dark `tradition_options_jsonb`; per-remedy outcome hooks; use `requires_acharya_review`.

## 7 - Decisions applied, questions for SS, Track I items arising

No decision has been applied: SS has not yet answered the A.L4 questions. This brief raises:

- **Q-L4-01** - Rebuild authority and order (see INDEX).
- **Q-L4-13** - Criteria to promote `ph_pratikara` from DRAFT; is one programme per obstruction (identical per graha) the intended grain; may `classical_tradition` flow into `source_id`?
- **Q-L4-05** - Is `cross_tradition_corroboration` a count (fine) or a score?

**Track I items arising (see INDEX section 8):** TI-L4-01, TI-L4-22, TI-L4-23, TI-L4-24, TI-L4-25, TI-L4-26.

