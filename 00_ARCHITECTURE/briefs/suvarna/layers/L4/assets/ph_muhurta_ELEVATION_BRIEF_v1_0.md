---
asset_id: ph_muhurta
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
disposition: "qualify (Q) - fix + rebuild; whether the table survives beside the live electional finder is Q-L4-10 (no retire proposed)"
disposition_proposal_approver: "Steward (G16); any output change to SS (R5)"
disposition_value: qualify
risk_class: "R3 (semantics and naming of score columns need SS/acharya; the code fixes are R1-R2; depends on a working Swiss ephemeris path at build time)"
decisions_applied: "none - SS has not answered the A.L4 questions (INDEX section 7); all dispositions and fix designs are proposals"
ss_questions: [Q-L4-01, Q-L4-05, Q-L4-10, Q-L4-11]
track_i_items: [TI-L4-01, TI-L4-04, TI-L4-11, TI-L4-12, TI-L4-13, TI-L4-14, TI-L4-47, TI-L4-48]
ledger_gap_ids: [ph_muhurta-Build.completion, ph_muhurta-Build.dep_liveness, ph_muhurta-Build.history, ph_muhurta-Carr.detector, ph_muhurta-Cost.baseline, ph_muhurta-Dens.served, ph_muhurta-Earn.build_record]
---
# ph_muhurta - Auspicious-window quality fused to anchors

> **PROVISIONAL - until J1; may register gaps, may not certify.** Every figure below comes from a stated read-only query (suvarna_reader SELECTs on 2026-10-03, receipts under `/Users/Dev/suvarna-evidence/A_L4/data/`), from the census, from the repository at main `3de3f8b15` (file:line), or from running the asset's pure engine functions locally with no database. Where something could not be determined it says so. Nothing here certifies a gate, approves a disposition or changes an asset.

## 0 - Identity: what the asset is

`ph_muhurta` writes `phala_muhurta`: for each influenceable or semi-influenceable `phala_anchors` row (ordered by `confidence_high`, cap 400; `platform/python-sidecar/pipeline/orchestrator/writers/ph_muhurta.py:255-279`) it maps the anchor's domain to an action class (`_DOMAIN_TO_ACTION`, `:710-718`; default `new_venture`, `:111`), takes the action's governing graha (the chart's 10th lord for business actions, `:93-97`, else `ACTION_GRAHA_MAP`, `platform/python-sidecar/services/ph_muhurta/engine.py:23-40`), and emits ONE row whose window is the anchor's window (start normalised to 06:00, `_to_datetime`, `:721-731`). The score is `panchanga_score x chart_personalization x (tarabala x chandrabala)^0.5 x (1 - adversity penalty)` (`platform/python-sidecar/services/ph_muhurta/engine.py:69-88`) with `panchanga_score = condition x 0.8 + 0.2` (`:138`), personalization = mean(`ga_condition_composite` score of the graha, transit factor) and a 0.3 penalty when the window overlaps a `kala_obstruction` window (`:126-134`). Tarabala/chandrabala come from `panchang_engine.panchanga_instant` evaluated at the window start (`:659-707`) or the 0.5/0.5 placeholder labelled `placeholder_no_ephemeris`. Natural key (chart, action_class, window_start): anchors that map to the same pair collapse (`ON CONFLICT DO NOTHING`, `:206`) and the accepted-row count is reported (`:239-242`). The decorator `@records_swiss_backend` (`:49`) records the ephemeris backend in `WriterResult.notes` (N-28).

| field | value | source |
|---|---|---|
| kind | registry `asset_kind=artifact`, `asset_type=data`, `scope=per_chart`, `domain=chart`, `rung=R4`; role per L4 layer instance TG-L4-024: not assigned by any tier | `asset_registry` row, read 2026-10-03 |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2696` (live may differ by migration) | seed |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ph_muhurta.py:48`; engine `platform/python-sidecar/services/ph_muhurta/engine.py`; registry `has_writer=True` | code |
| target table(s) | `phala_muhurta` | registry `target_table` / `count_sql` |
| live rows (canonical chart) / floor / build record | 134 / 134 / `rows_written=139`; rows per chart in the table(s): phala_muhurta: 482012f1=134; 1c826d5a=49 | `count_sql` run read-only; `asset_throughput`; table group-by |
| state / last built | `stale` / 2026-08-13T01:16:03 UTC (run `cbd6ea44`); `built_against_writer_hash=unknown` | `asset_throughput` |
| catalog_status | CURRENT | registry |
| depends_on (declared, live) | `ph_nimitta`, `ka_kalasutra`, `ga_panchanga`, `ka_vighnakara`, `ga_condition`, `ka_gochara`, `ga_positions`, `ka_sangam` | `asset_registry.depends_on` |
| depends_on vs what the code reads | reads `phala_anchors` (`ph_nimitta` declared), `kala_obstruction` joined to `kala_convergence` (`ka_vighnakara`, `ka_sangam` declared), `ga_condition_composite` (`ga_condition`), `chart_facts` Moon/LAGNA facts (`ga_positions`/`ga_panchanga` declared), `brahma_activity_ontology` (L0, bedrock-exempt). **Declared but not read: `ka_gochara`** (`_load_gochara_transits` returns `{}` explicitly, `:358-382`; the MR-09 docstring says so) and **`ka_kalasutra`** (no `kala_activation` read found). No undeclared read found | code (file:line) + fresh census `Build.dag` |
| blast radius | declared dependents direct 2 / transitive 11 (active assets, every layer) | fresh census `blocking_radius` |
| code readers outside the asset (non-test py/ts/tsx, 18 files) | L5 / other writers (python-sidecar pipeline/orchestrator/writers): ph_nimitta.py, ph_phaladesa.py, ph_sankrama.py; python-sidecar other: brahmagyan/phala/l4_outlook.py, brahmagyan/phala/muhurta.py, main.py, routers/muhurta_score.py, services/ph_pratikara/engine.py; serving (platform-mcp/src): resources/vidhi/dossier_slices/dossier_slices.generated.ts, tools/register_p1_synthesis.ts; retrieval + app (platform/src): app/api/mcp/db/query/route.ts, lib/jyotish/asset_names.ts, lib/retrieval/registry/knowledge/producer_editorial_review.ts, lib/retrieval/registry/knowledge/source_query_availability.ts, lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts, lib/retrieval/registry/layers/L4_phala/index.ts, lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts, lib/retrieval/registry/layers/L4_phala/salience_order.ts | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src at `3de3f8b15` (tests, generated and migrations excluded) |
| served surface | `L4_phala/query_phala_calibration.ts` (`query_auspicious_windows`, 'Reach.fields' 13 of 24 columns selected, 11 dark including `panchanga_snapshot_jsonb`, `tarabala_chandrabala_jsonb`, `significators_met_jsonb`); `platform-mcp/src/tools/register_p1_synthesis.ts:1017-1038` (prashna undertaking: election windows by domain); a DIFFERENT live electional finder exists (`platform-mcp/src/tools/phala_muhurta_finder.ts`, `L4_phala/query_muhurat.ts`) that scores real candidate times | code |
| role / scoring mode | manifestation-family asset of L4 Phala (T2 section 6.5); census `scoring: contribution`; 'electional windows (tara/candra, lord resolution, obstruction)' (T2c label); T2 section 6.5 keeps electional assets under their own method and authority gate | tiers + census |
| invalidation / FK | `linked_anchor_id -> phala_anchors ON DELETE SET NULL` (no cascade); `overlapping_obstruction_id` has no FK. Natural key `phala_muhurta_natural_key (chart_id, action_class, window_start)` | `pg_constraint` read 2026-10-03 |

## 1 - Measured state and the nine gates

### 1.1 - Live state on the canonical chart (read-only, 2026-10-03)

- **134 rows** (floor 134; build record 139: the 5-row gap is key collisions the OLD writer counted as writes; the current writer counts accepted rows, `:239-242`). Action classes: travel 50, new_venture 34, start_business 28, marriage 17, medical 5. `window_start` spans 1990-03-20 to 2050-04-01 and `window_end` to 2052-05-18, all stored as `06:00:00+00` (database TimeZone is UTC).
- **134 of 134 `window_quality_verdict='mediocre'`** with `verdict_reason` 'Best available window scores 0.26 / 0.13 / 0.09 / 0.18 / 0.12 / 0.08 ... Moon may be afflicted or no fixed nakshatra available' (6 distinct strings). `tarabala_chandrabala_jsonb.source = 'placeholder_no_ephemeris'` on **134 of 134** (both scores 0.5), so the Moon-strength factor was never measured and the geometric mean is pinned at 0.5, capping `composite_quality` at 0.5 (below the 0.55 'adequate' threshold). The explanation names the chart's Moon for a factor nothing computed.
- **The score does not discriminate within an action class.** `panchanga_score` has exactly one value per action class (new_venture and start_business 0.820, travel 0.556, marriage 0.536, medical 0.516), `chart_personalization_score` likewise, so every window of a class has an identical score except where the 0.3 obstruction penalty applies (37 rows carry `overlapping_obstruction_id`, `personal_adversity_penalty > 0` on 37). `composite_quality` ranges 0.081-0.261.
- **130 of 134 rows have `linked_anchor_id` NULL** (SET NULL when their anchors were deleted); only 4 resolve to a surviving anchor. The 37 `overlapping_obstruction_id`s cite `kala_obstruction` rows that no longer exist for this chart (0 rows).
- The registry integrity SQL returns **true** (reader run): linked anchors resolve or are NULL, windows ordered, fingerprints distinct per chart. It cannot detect any of the above, and the build is `stale` (5 of 8 declared dependencies stale: `ph_nimitta`, `ka_kalasutra`, `ka_vighnakara`, `ka_gochara`, `ka_sangam`).

Build history for this asset (all charts, `build_run_assets`): 9 aborted, 37 complete, 26 error/blocked_dependency, 19 queued; the last complete canonical-chart run is `cbd6ea44` (2026-08-13), and the 26+ `error/blocked_dependency` rows are cascade skips, not writer errors. The only non-cascade errors on record: none; 9 aborts (last 2026-07-13).

### 1.2 - Stored rows versus current code

Commits touching this asset's writer or engine AFTER its last build (2026-08-13 01:16 UTC): `b9d2d254b` 2026-10-02 Ephemeris: canonical backend is Swiss .se1 (swieph): SE_EPHE_PATH in both Dockerfiles, fail-closed shared hel…; `bd398f065` 2026-09-05 L4 W3-3b: ph_muhurta — stop grading a window whose Moon strength was never measured (#1791).

`bd398f065` (W3-3b, 2026-09-05) stops grading a window whose Moon strength was never measured: `classify_verdict(..., tara_chandra_known=False)` now returns `(None, reason)` (verified by a local call: placeholder -> `None`, live -> `mediocre`), so the 134 stored `mediocre` rows and their invented reason are the OLD output. `b9d2d254b` (2026-10-02) makes the Swiss `.se1` backend canonical for the ephemeris helper used by the live tara/chandra path. **Whether the build environment can reach the live path is not determined here** (no run): if it cannot, a rebuild still stores 0.5/0.5 and now a NULL verdict.

### 1.3 - Census cells (fresh run, compared with the saved run)

Census used: fresh census `/Users/Dev/suvarna-evidence/census_fresh/1e5781a/census_L4.json` (generated 2026-10-02T10:12:59+05:30, chart 482012f1, inspector 1e5781a at REGISTRY_REVISION 10; outside the repo) compared with the repo's saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L4.json` (2026-09-30T20:23:50+05:30, inspector 2a78ec64d). Main's inspector is now at REGISTRY_REVISION 15: the offline rollup below applies its rules to the fresh census; no live re-measure was run.

| gate | criterion | fresh verdict | measured (fresh census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13): complete with no disposition and not derivable as probe-green (no probe receipt names this run) — unclassified |
| Null | Null.schema_default | PARTIAL (saved 2026-09-30: (absent in saved run)) | no schema default on the declared prose column(s) verdict_reason; writer literal fallbacks and constant columns are not measured here, so this is never PASS |
| Null | Null.blank_rows | PARTIAL (saved 2026-09-30: (absent in saved run)) | no blank or placeholder row among the checkable prose rows; schema defaults are read by Null.schema_default and writer literal fallbacks and constant columns are not measured, so this is never PASS |
| Narr | Narr.fidelity_test | PARTIAL (saved 2026-09-30: (absent in saved run)) | structural only: 5 test file(s) call the builder and assert in the same test function (test_fix_plan_proofs.py, test_ph_a5_fixes.py, test_ph_muhurta_bala_join.py, test_ph_muhurta_verdict_honesty.py…); declared field(s) referenced: verdict_reason; whether the assertion grades the sentence is not read, so this never reads PASS |
| Narr | Narr.lint | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — the narration lints are not applicable to this asset: no chart_facts fact_category selection in its 36-file writer scope and no declared column the raw-token lint covers; a clean scan of code they cannot see is not a pass |
| Dens | Dens.served | NO_DETECTOR (saved 2026-09-30: FAIL) | NO_DETECTOR — 1 serving-root file(s) naming phala_muhurta lose the string scanner's sync (an unbalanced quote, a nested template literal, or a regex literal holding a quote desynced it): platform-mcp/src/tools/register_p1_synthesis.ts; its served select and density_contract cannot be read — never FAIL, never the closable N/A |
| Build | Build.dep_liveness | PARTIAL | 3/8 declared dependencies lit at chart 482012f1 (or global); stale: ['ph_nimitta (stale, chart 482012f1)', 'ka_kalasutra (stale, chart 482012f1)', 'ka_vighnakara (stale, chart 482012f1)', 'ka_gochara (stale, chart 482012f1)', 'ka_sangam (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Build | Build.completion | FAIL | build record rows_written=139 disagrees with live=134 (count_sql over the target table; chart 482012f1) |
| Build | Build.history | PARTIAL | latest run complete, but 0 error(s) and 9 abort(s) on record (26 additional blocked_dependency row(s) excluded as cascade-only). |
| Complete | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach | Reach.fields | NOT_GENERIC | reported, not graded — width 13/24 built column(s) (54.2%) selected by 1 capability module(s); dark: ['chart_id', 'computed_at', 'derivation_ledger_jsonb', 'follow_up_hook_jsonb', 'fructification_anchor', 'overlapping_obstruction_id', 'panchanga_snapshot_jsonb', 'personalization_graha', 'significators_met_jsonb', 'source_citation', 'tarabala_chandrabala_jsonb']; depth 100.0% (a capability query reads it with no literal row pin (upper bound)) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13): complete with no disposition and not derivable as probe-green (no probe receipt names this run) — unclassified |
| Earn | Earn.service_state | N/A (saved 2026-09-30: (absent in saved run)) | declared kind 'data' is not `service`; Earn.service_state is the service-state check (a service's rows_written cannot tell healthy-and-idle from broken) |

**PASS cells (compact):** Ldgr.source_presence, Idem.pattern, Vocab.identity, Narr.agree, Narr.checkable, Build.registered, Build.contract, Build.target, Build.dag, Build.exercised, Build.count_integrity, Count.floor, Complete.depth.

**Offline rollup** (main `asset_census.py` rollup rules at REGISTRY_REVISION 15 applied to the FRESH census; N/A reads NO_DETECTOR while `NA_RULE_DECISIONS` is empty; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null PARTIAL · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build FAIL.
Same rules over the SAVED 2026-09-30 census: Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

### 1.4 - Earned-signal (N.8), narration-fidelity (N.7) and honest-null audit of this asset's flags and verdicts

| field / claim | what it claims | what code path could make it read false | finding |
|---|---|---|---|
| `window_quality_verdict` | strong / adequate / mediocre / none_genuine for the window | before W3-3b: only `mediocre` reachable when bala was the placeholder (composite capped at 0.5 < 0.55); after: NULL with an honest reason when the placeholder is in use | stored rows: **134/134 `mediocre` is an unearned verdict** (real-stored). Current code earns NULL. A real verdict additionally needs a real panchanga factor (next row) |
| `panchanga_score` | the panchanga quality of the window | none: `condition x 0.8 + 0.2` from the graha's `ga_condition_composite` score (`:138`); snapshot labelled `ka_muhurta_seva_proxy` (`:162`); `ka_muhurta_seva` is never called | **Column name claims a panchanga computation that does not occur.** One value per action class |
| `hora_lord` | the planetary-hour lord of the window | the action's governing graha (`hora_lord=relevant_graha`, `:160`); identical to `personalization_graha` on every row (0 of 183 rows differ, both charts; stored on this chart as saturn 62, mercury 50, venus 17, moon 5) | **Mislabelled.** A hora lord is a function of the time of day; this is the action significator |
| `chart_personalization_score` | chart-specific suitability | mean of the graha's condition score and a transit factor that is the constant 0.5 (`_load_gochara_transits` returns `{}`, `:382`) | half of the personalization is a constant; the other half is a per-graha value shared by all windows of the class |
| `composite_quality` | a window quality in [0,1] | always a product of the above; with the placeholder bala it cannot exceed 0.5 | a real arithmetic over mostly proxy inputs; not a probability (C3); stored on 134/134 |
| window itself | an auspicious window to act in | the anchor's prediction window (up to years wide) graded at ONE instant, 06:00 on its first day (`:116-117,144-146`); `window_end` is the anchor's end | **A muhurta is a short electional slot; this is an anchor window labelled with the Moon at one moment.** The live finder scores real candidate times |
| stored instant | the instant that was graded | the naive 06:00 is passed to `panchanga_instant` as LOCAL time at the birth-place offset (`panchang_engine/__init__.py:203-217`), but stored into `timestamptz` as `06:00:00+00` (session TimeZone UTC) | the stored timestamp is not the instant that was evaluated (offset equal to the birth-place UTC offset); consumers reading `window_start` as UTC mis-read it |
| `follow_up_hook_jsonb` | a hook consumed by `P7B_prashna_followup_scheduler` | no consumer of that name was found in the tree (grep `P7B_prashna_followup_scheduler` over py/ts/md/sql: only the literal at `services/ph_muhurta/engine.py:253`) | a label for a consumer that does not exist; `already_satisfied=false` on every placeholder row |
| honest nulls | NULL where unknown | tara/chandra: 0.5 + source label (honest by label); `condition_scores` missing -> 0.5 per graha with a warning (`:354-356`); career lord falls back to saturn silently (`:491`) | two silent fallbacks (see G09) |

### 1.5 - UUID chart_id check (the bo_*/ph_* adapter defect)

`chart_id` is used only as a psycopg parameter and in log lines (`:60,65,269,309,341,481`); `rec.linked_anchor_id` is `str(anchor['anchor_id'])` (`:104`); the six `json.dumps` sites (`:220-226`) serialise engine dicts whose members are strings, floats and the jsonb dicts read from `brahma_activity_ontology`. No UUID object reaches a JSON payload and no `canonical_json` / `stable_uuid` call exists. **Verdict: not present today**; no `_UUIDEncoder` in this writer.

## 2 - Gaps: which are real, which are detector or definition gaps

Class vocabulary: **real** = a shortfall in code, rows, registry row or served surface; **real-stored** = the CURRENT code already fixes it but the stored rows predate the fix (cured by a rebuild, not by an edit); **design** = needs an SS or acharya decision; **detector** = the instrument is absent or its definition is the open point; **history** = a recorded past outcome no edit can change; **information** = Count/Cost/Complete/Reach, never a blocker; **opportunity** = beyond the requirement.

| gap id | gate | class | note (evidence) |
|---|---|---|---|
| ph_muhurta-G01 | Earn | real-stored | 134/134 `mediocre` with an invented Moon explanation; fixed in code by `bd398f065`, not in the rows |
| ph_muhurta-G02 | Build | real-stored | `rows_written` 139 vs live 134 (census Build.completion FAIL): the old writer counted 5 key collisions as inserts; current writer counts accepted rows |
| ph_muhurta-G03 | Carr / Earn | real | Moon strength unmeasured at build (placeholder x134); no check that the live `panchanga_instant` path is available in the build environment; instant stored as UTC though evaluated as birth-place local time |
| ph_muhurta-G04 | Narr / Earn | real | `panchanga_score` is a condition proxy, `hora_lord` is the action graha, transit factor is the constant 0.5: three score/label columns that do not measure what they are named for (`:138,160,382`) |
| ph_muhurta-G05 | Carr | design | The "window" is the anchor window graded at one instant; a live electional finder already exists (Q-L4-10) |
| ph_muhurta-G06 | Vocab | real | `_DOMAIN_TO_ACTION` keys are the pre-CR-66 words (`financial`, `spiritual`, `psychological`, `:710-718`); canonical `wealth`, `spirituality`, `character` (and the six other canonical domains) fall to the default `new_venture` (`:111`) - a Jyotish mapping that was never decided for 9 of 13 domains (Q-L4-11) |
| ph_muhurta-G07 | Build | real | Orphans: 130 of 134 `linked_anchor_id` NULL; 37 `overlapping_obstruction_id` dangling (no FK; `kala_obstruction` empty for the chart) |
| ph_muhurta-G08 | Build | real | Declared-unread edges `ka_gochara`, `ka_kalasutra` (ordering-only; the writer says gochara is deferred) |
| ph_muhurta-G09 | Null | real | Silent fallbacks: condition scores (`:354-356` -> 0.5 each), obstruction windows (`:320-326` swallowed), career lord (`:489-491` -> saturn), activity ontology (`:512-519` -> `{}`); a read failure is indistinguishable from "no data" |
| ph_muhurta-G10 | Vocab | real | `_resolve_career_lord` reads `chart_facts` LAGNA sign with `LIMIT 1`, no ayanamsha pin and no ORDER BY (`:475-480`) (N.7 item 2; passes the fact_key lint because the key is pinned) |
| ph_muhurta-G11 | Narr | real | `follow_up_hook_jsonb` names a consumer (`P7B_prashna_followup_scheduler`) that does not exist in the tree |
| ph_muhurta-G12 | Dens | detector | Dens.served NO_DETECTOR (scanner desync on `register_p1_synthesis.ts`); Reach.fields: 11 of 24 columns dark |
| ph_muhurta-G13 | Null / Narr | detector | Null PARTIAL (declared prose field `verdict_reason` only); Narr.fidelity_test PARTIAL (5 tests call the builder; none grades the sentence); Narr.lint NO_DETECTOR |
| ph_muhurta-G14 | Earn / Carr / Vocab | detector | Earn.build_record, Carr (no D1/D2/D3), Vocab.alias NO_DETECTOR |
| ph_muhurta-G15 | Build | history | Build.history PARTIAL: 0 errors, 9 aborts on record |

## 3 - Disposition

DISPOSITION: qualify

EVIDENCE_POINTER: 00_ARCHITECTURE/briefs/suvarna/layers/L4/assets/ph_muhurta_ELEVATION_BRIEF_v1_0.md (sections 1-4); receipts `_evidence/` (data/, upstream_receipts.json, rollup_L4.json, offline_checks.txt, rect_diag.txt); census `layers/census/census_L4.json` + fresh census `census_fresh/1e5781a/census_L4.json`

**qualify (Q) - fix + rebuild; whether the table survives beside the live electional finder is Q-L4-10 (no retire proposed).** Qualify (Q): the asset has live readers (the prashna undertaking synthesis, `query_auspicious_windows`) and a sound pattern (accepted-row counting, honest placeholder label, verdict NULL when the Moon factor is unmeasured), but what it stores is an anchor window labelled as a muhurta, scored by proxies, with three mislabelled columns and a hard-coded domain->action map. The question is the table's purpose next to the live electional finder, not its code hygiene (Q-L4-10). If SS answers that the finder is the electional authority, the proposal becomes consolidate (C): keep `phala_muhurta` only as an anchor-linked quality annotation under a new name. No retire proposed: the prashna undertaking reads it.

Approver under Track A brief section 10: **Steward (G16)** for keep/qualify/enrich; **SS** for any output change (R5). No disposition is applied by this brief.

## 4 - Fix designs (one per real gap; anything marked `needs production rebuild` or `needs migration` is a REVIEW item for Strategic Suvarna)

### FD-1 - Rebuild (wave 8) and prove the live Moon path in the build environment

- **Answers:** G01, G02, G03; CF-L4-01
- **Change:** Rebuild after `ph_nimitta`. Before accepting, run one smoke read that `panchang_engine.panchanga_instant` succeeds under the build image's `SE_EPHE_PATH` (the `records_swiss_backend` note in `WriterResult.notes` is the receipt), otherwise the rebuild reproduces 0.5/0.5 and a NULL verdict on all rows.
- **Files / declaration / migration:** none (dispatch + smoke)
- **Failing-first test and mutation:** failing-first: `tarabala_chandrabala_jsonb.source = panchang_engine_live` on rows > 0; mutation: unset `SE_EPHE_PATH` -> `placeholder_no_ephemeris` and NULL verdict (already tested by `test_ph_muhurta_verdict_honesty.py`)
- **Output change:** yes - verdicts become NULL or earned; counts change with the anchor count
- **Blast radius:** `ph_pramana`, `ph_phaladesa` (muhurta_available), prashna undertaking synthesis
- **Rebuild:** needs production rebuild (REVIEW item)
- **Gate it moves:** Build, Earn
- **Fix class:** data (rebuild); **risk class:** R3; **buildable before J1:** tier-independent
- **Decision:** OPEN - Q-L4-01

### FD-2 - Name the columns for what they hold, or measure them

- **Answers:** G04; CF-L4-04
- **Change:** (a) `panchanga_score`: wire the real panchanga factor (the finder computes one; the writer's own docstring says `ka_muhurta_seva` is "not available at writer import time", `:136`) or store NULL and let the composite renormalise as `TestCompositeHandlesUnassessedTransit` (`test_phala_muhurta.py`) already does for the finder; (b) `hora_lord`: rename to `action_graha` or compute the true hora lord at the window start; (c) transit factor: NULL not 0.5 until gochara is wired.
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_muhurta.py:136-146,160,382`; `platform/python-sidecar/services/ph_muhurta/engine.py:69-88`; migration if a column is renamed (additive new column + backfill by rebuild)
- **Failing-first test and mutation:** failing-first: a row with no panchanga source has `panchanga_score IS NULL` and a composite computed over the factors that exist; mutation: restore the proxy -> test fails
- **Output change:** yes (column values/names)
- **Blast radius:** serving of `query_auspicious_windows`, `ph_phaladesa` (muhurta_available), L5 readers of composite_quality (none found)
- **Rebuild:** needs production rebuild
- **Gate it moves:** Narr, Earn
- **Fix class:** writer code (+ migration if renamed); **risk class:** R3; **buildable before J1:** tier-dependent: what an L4 "muhurta" may claim (T2 6.5 gives electional assets their own authority gate)
- **Decision:** OPEN - Q-L4-10

### FD-3 - Decide the purpose, then the window semantics

- **Answers:** G05
- **Change:** If the finder is the electional authority: relabel the table as "anchor-linked window quality at window start", drop `window_end` as a muhurta end, and point consumers at the finder for slots. If this table is meant to be electional: grade a set of candidate slots inside the anchor window (the finder's method) instead of one instant.
- **Files / declaration / migration:** registry description, `platform/python-sidecar/pipeline/orchestrator/writers/ph_muhurta.py:110-146`
- **Failing-first test and mutation:** failing-first depends on the decision; baseline: two slots in one window can score differently
- **Output change:** yes
- **Blast radius:** as FD-2
- **Rebuild:** needs production rebuild
- **Gate it moves:** Carr
- **Fix class:** writer code; **risk class:** R4; **buildable before J1:** tier-dependent
- **Decision:** OPEN - Q-L4-10

### FD-4 - Complete the domain -> action-class map (acharya)

- **Answers:** G06; CF-L4-14
- **Change:** Replace the legacy keys by the 13 canonical domains with an explicit action class (or an explicit "no electional action" NULL) for each of: wealth, spirituality, character, education, family, progeny, residence, travel, general. Today 9 of 13 domains default to `new_venture`.
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_muhurta.py:710-718,111`
- **Failing-first test and mutation:** failing-first: every canonical domain resolves to a declared action or NULL; mutation: add a 14th domain -> test fails (extends `test_domain_vocabulary_census.py`)
- **Output change:** yes - action_class of rows from those domains
- **Blast radius:** `query_auspicious_windows` filters; prashna undertaking synthesis maps by action class
- **Rebuild:** needs production rebuild
- **Gate it moves:** Vocab
- **Fix class:** writer code + acharya decision; **risk class:** R3; **buildable before J1:** tier-dependent (acharya)
- **Decision:** OPEN - Q-L4-11

### FD-5 - Fail loud on required reads; pin the lagna fact

- **Answers:** G09, G10
- **Change:** `_load_condition_scores`, `_load_obstruction_windows`, `_resolve_career_lord`, `_load_activity_ontology` raise (or return an explicit "unavailable" that is stored as such) instead of substituting neutral values, mirroring `ph_suddha_sodhana._load_flags_grouped` after F-16; add `ayanamsha_id = 'lahiri_chitrapaksha'` and an ORDER BY to the LAGNA read.
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_muhurta.py:329-356,281-327,466-491,493-519`
- **Failing-first test and mutation:** failing-first: a forced read error makes the build fail (or stores `condition_source=unavailable`); mutation: restore `except: return {}` -> fails
- **Output change:** none on a healthy read
- **Blast radius:** none when reads succeed
- **Rebuild:** rides FD-1
- **Gate it moves:** Null
- **Fix class:** writer code; **risk class:** R1; **buildable before J1:** tier-independent
- **Decision:** no question; Steward

### FD-6 - Store the evaluated instant

- **Answers:** G03 (stored instant)
- **Change:** Convert the evaluated local instant to UTC with the same offset before the INSERT (or store the local-time instant in a documented column), so `window_start` is the instant that was graded.
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_muhurta.py:116-117,721-731`
- **Failing-first test and mutation:** failing-first: for a given birth-place offset the stored UTC instant minus the offset equals the evaluated local wall time; mutation: store naive -> fails
- **Output change:** yes - `window_start`/`window_end` shift by the offset; the natural key changes (window_start is a key column)
- **Blast radius:** natural key `(chart_id, action_class, window_start)`; consumers comparing dates
- **Rebuild:** needs production rebuild
- **Gate it moves:** Carr
- **Fix class:** writer code; **risk class:** R3 (key change); **buildable before J1:** tier-independent
- **Decision:** OPEN - Q-L4-10

### FD-7 - Edges and declarations

- **Answers:** G08, G12, G13; CF-L4-07, CF-L4-10
- **Change:** Remove the declared-unread edges `ka_gochara` and `ka_kalasutra` (or wire gochara); add `null_convention` for `overlapping_obstruction_id`, `linked_anchor_id`, `fructification_anchor`; fix the scanner desync file (Track E).
- **Files / declaration / migration:** one registry migration + `asset_declarations.json`
- **Failing-first test and mutation:** failing-first: Build.dag reads-match still PASS after the edge removal; mutation: add a read of `kala_gochara_windows_v2` without the edge -> FAIL
- **Output change:** none
- **Blast radius:** ordering only
- **Rebuild:** none
- **Gate it moves:** Build, Null, Dens
- **Fix class:** registry/declaration; **risk class:** R2; **buildable before J1:** tier-independent
- **Decision:** no question; Steward

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L4-01** - *this asset:* rebuild wave 8; 134 rows are pre-W3-3b output with an unearned verdict
- **CF-L4-04** - *this asset:* proxy and constant scores (panchanga_score, transit 0.5, hora_lord)
- **CF-L4-05** - *this asset:* silent loaders (condition scores, obstruction windows, career lord, ontology)
- **CF-L4-07** - *this asset:* declared-unread `ka_gochara`, `ka_kalasutra`
- **CF-L4-08** - *this asset:* stored instant vs evaluated instant; windows are anchor windows
- **CF-L4-09** - *this asset:* UUID: not present
- **CF-L4-10** - *this asset:* Null/Narr declarations (prose field declared, `null_convention` absent)
- **CF-L4-11** - *this asset:* Dens scanner desync; 11 dark columns
- **CF-L4-12** - *this asset:* floor 134 is below any rebuild with a corrected key; description says "live-transit scored"
- **CF-L4-14** - *this asset:* legacy domain->action keys

## 5 - Semantic fingerprint contract (for the rebuild plan)

Natural key `(chart_id, action_class, window_start)` (the table's live UNIQUE index). Fingerprint over `(action_class, window_start, window_end, hora_lord, composite_quality, window_quality_verdict, linked_anchor_id)`; `muhurta_id` (random uuid) and `computed_at` excluded. Rows depend on the anchor set, so the pre/post comparison is only meaningful after `ph_nimitta` is rebuilt; `linked_anchor_id` changes with every anchor rebuild. `window_start` is a naive 06:00 stored as UTC (FD-6 would move the key).

## 6 - Preserved kernel, carriage check, opportunities

- **Preserved kernel:** Anchor-linked rows (M3), the obstruction penalty (M2), the explicit placeholder label and the NULL verdict when bala is unmeasured, accepted-row counting, the composite formula's structure, `significators_met_jsonb` / `fructification_anchor` taken from `brahma_activity_ontology` rather than invented.
- **Carriage check (T4 4.1; one only):** D3 (re-derivation): recompute `tarabala` and `chandrabala` for a sample of stored windows through `panchang_engine.compute_tara_bala_score` / `compute_chandra_bala_score` (the same helpers `ka_muhurta_seva` uses) at the stored (corrected) instant and compare with `tarabala_chandrabala_jsonb`; recompute `composite_quality` from `derivation_ledger_jsonb` (pure). Requires the Swiss ephemeris path for the Moon.
- **By design, stated and not flagged:** `ON CONFLICT DO NOTHING` collapsing anchors that map to one (action_class, day) is documented and now counted honestly (`:230-251`); the neutral 0.5 label for unavailable ephemeris is an explicit placeholder, not a hidden default.
- **Opportunities (never blocking):** rank slots inside an anchor window with the finder's method; expose `panchanga_snapshot_jsonb` (dark); a real hora lord.

## 7 - Decisions applied, questions for SS, Track I items arising

No decision has been applied: SS has not yet answered the A.L4 questions. This brief raises:

- **Q-L4-01** - Rebuild authority and order (see INDEX).
- **Q-L4-05** - Are `panchanga_score`, `chart_personalization_score`, `composite_quality` allowed as stored scores, and under what names, given they are proxies?
- **Q-L4-10** - What is `phala_muhurta` for, next to the live electional finder - and is a one-instant grade of an anchor window an acceptable "muhurta"?
- **Q-L4-11** - (acharya) Which action class (or none) belongs to each of the 13 canonical domains?

**Track I items arising (see INDEX section 8):** TI-L4-01, TI-L4-04, TI-L4-11, TI-L4-12, TI-L4-13, TI-L4-14, TI-L4-47, TI-L4-48.

