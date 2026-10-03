---
asset_id: ph_phaladesa
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
disposition: "qualify (Q) - make the summary derive only from rows that exist and the narration only from fields that mean what it says; the overlap with the serving read model is a question"
disposition_proposal_approver: "Steward (G16); any output change to SS (R5)"
disposition_value: qualify
risk_class: "R3 (narration text, summary semantics and silent loaders; the code fixes are R1-R2)"
decisions_applied: "none - SS has not answered the A.L4 questions (INDEX section 7); all dispositions and fix designs are proposals"
ss_questions: [Q-L4-01, Q-L4-12, Q-L4-16]
track_i_items: [TI-L4-01, TI-L4-36, TI-L4-37, TI-L4-38, TI-L4-39, TI-L4-40]
ledger_gap_ids: [ph_phaladesa-Build.dep_liveness, ph_phaladesa-Build.history, ph_phaladesa-Carr.detector, ph_phaladesa-Complete.depth, ph_phaladesa-Cost.baseline, ph_phaladesa-Dens.served, ph_phaladesa-Earn.build_record]
---
# ph_phaladesa - Domain result declaration (13 rows per chart)

> **PROVISIONAL - until J1; may register gaps, may not certify.** Every figure below comes from a stated read-only query (suvarna_reader SELECTs on 2026-10-03, receipts under `/Users/Dev/suvarna-evidence/A_L4/data/`), from the census, from the repository at main `3de3f8b15` (file:line), or from running the asset's pure engine functions locally with no database. Where something could not be determined it says so. Nothing here certifies a gate, approves a disposition or changes an asset.

## 0 - Identity: what the asset is

`ph_phaladesa` writes `phala_phaladesa`: one declaration per canonical domain (13 rows per chart, `platform/python-sidecar/services/ph_phaladesa/engine.py:48-55`) summarising the domain's anchors, their sodhana disposition, the top anchor (clean first, then `confidence_high`, `platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py:329-367`), outgoing and incoming spillovers, whether mitigation and muhurta rows exist for the domain, the top anchor's pramana window status, and a deterministic template narration (`narration_status='ready'`, `narration_model` NULL, method `deterministic_template_v1`, `platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py:94-151`). It also reads the Bodha MSR (B.11 'whole-chart read', `:289-325`). Delete-then-insert per chart with an `ON CONFLICT (chart_id, domain) DO UPDATE` second layer (`:237-262`). It is the last wave of L4 (wave 11) and the only one with a dedicated serving capability (`query_domain_result`).

| field | value | source |
|---|---|---|
| kind | registry `asset_kind=artifact`, `asset_type=data`, `scope=per_chart`, `domain=chart`, `rung=R4`; role per L4 layer instance TG-L4-024: not assigned by any tier | `asset_registry` row, read 2026-10-03 |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2804` (live may differ by migration) | seed |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py:154`; engine `platform/python-sidecar/services/ph_phaladesa/engine.py`; registry `has_writer=True` | code |
| target table(s) | `phala_phaladesa` | registry `target_table` / `count_sql` |
| live rows (canonical chart) / floor / build record | 13 / 13 / `rows_written=13`; rows per chart in the table(s): phala_phaladesa: 482012f1=13; 1c826d5a=13 | `count_sql` run read-only; `asset_throughput`; table group-by |
| state / last built | `stale` / 2026-08-13T01:16:27 UTC (run `cbd6ea44`); `built_against_writer_hash=unknown` | `asset_throughput` |
| catalog_status | CURRENT | registry |
| depends_on (declared, live) | `ph_nimitta`, `ph_muhurta`, `ph_pratikara`, `ph_suddha_sodhana`, `ph_sankrama`, `ph_pramana`, `bo_laksana` | `asset_registry.depends_on` |
| depends_on vs what the code reads | reads `phala_anchors`, `phala_suddha_sodhana`, `phala_pramana`, `phala_sankrama`, `phala_mitigation`, `phala_muhurta` (all declared) and `bodha_msr_signals` (`bo_laksana` declared). It does NOT read `phala_sodhana` although the module docstring lists it. No undeclared read found | code (file:line) + fresh census `Build.dag` |
| blast radius | declared dependents direct 1 / transitive 9 (active assets, every layer) | fresh census `blocking_radius` |
| code readers outside the asset (non-test py/ts/tsx, 8 files) | L5 / other writers (python-sidecar pipeline/orchestrator/writers): mi_bhavisya.py; python-sidecar other: brahmagyan/domain_vocabulary.py; serving (platform-mcp/src): resources/vidhi/dossier_slices/dossier_slices.generated.ts; retrieval + app (platform/src): lib/jyotish/asset_names.ts, lib/retrieval/registry/knowledge/producer_editorial_review.ts, lib/retrieval/registry/knowledge/source_query_availability.ts, lib/retrieval/registry/layers/L4_phala/index.ts, lib/retrieval/registry/layers/L4_phala/query_domain_result.ts | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src at `3de3f8b15` (tests, generated and migrations excluded) |
| served surface | `L4_phala/query_domain_result.ts` (`query_domain_result`; its header says 7 domains and the index comment '7 rows - by design'); no `density_contract` (Dens.served FAIL, 1 module) | code |
| role / scoring mode | manifestation-family asset of L4 Phala (T2 section 6.5); census `scoring: contribution`; 'per-domain overview of top anchor, contradictions, spillovers, action availability' (T2c); the only asset whose output is partly prose | tiers + census |
| invalidation / FK | none outward; `top_anchor_id` is a plain uuid with no FK (6 of 7 populated values dangle) | `pg_constraint` read 2026-10-03 |

## 1 - Measured state and the nine gates

### 1.1 - Live state on the canonical chart (read-only, 2026-10-03)

- **13 rows** (floor 13, build record 13: Build.completion PASS). **The rows describe a state that no longer exists.** The table says career has `anchor_count` 29 (28 clean), character 5, health 5, relationship 18, spirituality 6, transition 50, wealth 26 = **139 anchors; `phala_anchors` holds 4** (career 1, character 1, health 1, relationship 1; spirituality, transition, wealth 0). The integrity SQL returns **false** (reader run): `anchor_count` disagrees with the true anchor population.
- **`top_anchor_id` dangles on 6 of 7 populated domains** (only `career`'s resolves). The narration text for career reads 'rests on 29 predictive anchor(s), of which 28 passed clean sodhana review ... Remedial mitigation is available ... Supportive muhurta windows have been identified'; only 1 career anchor exists and `phala_mitigation.linked_anchor_id` is NULL on all 536 rows.
- **The narration asserts a contradiction count the data denies.** 7 of 7 populated narrations say '3 contradiction signal(s) temper this reading and warrant caution', while `contradiction_summary_jsonb.contested = false` on 7 of 7. The count is `len()` of a 3-key dict `{contested, net_direction, countervailing_thread}` (`platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py:138-142`); `test_nar_ph_phaladesa.py` exercises lists of dicts, the real shape is a dict.
- **Inflated and contradictory counts.** `incoming_spillover_count` is a multiple of 5 on every domain (0, 145 ... 315: the ayanamsha fan-out of `ph_sankrama`); `education` (0 anchors) narrates 'No predictive anchors were derived ... 170 cross-domain spillover(s) feed into this domain'. `spillover_domains_jsonb` for career holds 1,595 entries.
- **`narration_status='ready'` on 13 of 13 with `narration_model` and `narration_requested_at` NULL on 13** and `narration_jsonb.method='deterministic_template_v1'` on 13: honest as a template (the registry description still says 'Narration pending via Gemini/DeepSeek'). `mitigation_available` is true for 1 domain and `muhurta_available` for 7 of 13.
- Build is `stale`; 1 of 7 declared dependencies lit.

Build history for this asset (all charts, `build_run_assets`): 9 aborted, 35 complete, 30 error/blocked_dependency, 19 queued; the last complete canonical-chart run is `cbd6ea44` (2026-08-13), and the 26+ `error/blocked_dependency` rows are cascade skips, not writer errors. The only non-cascade errors on record: none visible through `suvarna_reader` on 2026-10-03 (9 aborts, last 2026-07-13). The census reports 1 error (a `CheckViolation` on `phala_phaladesa_domain_canonical`, 2026-07-04, quoted in section 1.3); that row is NOT reproducible through the reader's `build_run_assets` and is cited as a census statement only.

### 1.2 - Stored rows versus current code

Commits touching this asset's writer or engine AFTER its last build (2026-08-13 01:16 UTC): `8d61dab2d` 2026-09-06 L4 W3-3f: ph_phaladesa — headline anchor ranks clean before confidence_high (#1839).

`8d61dab2d` (W3-3f, 2026-09-06): the headline anchor ranks clean before `confidence_high`; `2d8540a11` and `46ed7cf9c` earlier changed vocabulary and the citation strip. The stored rows predate the ranking fix.

### 1.3 - Census cells (fresh run, compared with the saved run)

Census used: fresh census `/Users/Dev/suvarna-evidence/census_fresh/1e5781a/census_L4.json` (generated 2026-10-02T10:12:59+05:30, chart 482012f1, inspector 1e5781a at REGISTRY_REVISION 10; outside the repo) compared with the repo's saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L4.json` (2026-09-30T20:23:50+05:30, inspector 2a78ec64d). Main's inspector is now at REGISTRY_REVISION 15: the offline rollup below applies its rules to the fresh census; no live re-measure was run.

| gate | criterion | fresh verdict | measured (fresh census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13): complete with no disposition and not derivable as probe-green (no probe receipt names this run) — unclassified |
| Null | Null.schema_default | PARTIAL (saved 2026-09-30: (absent in saved run)) | no schema default on the declared prose column(s) narration_jsonb; writer literal fallbacks and constant columns are not measured here, so this is never PASS |
| Null | Null.blank_rows | PARTIAL (saved 2026-09-30: (absent in saved run)) | no blank or placeholder row among the checkable prose rows; schema defaults are read by Null.schema_default and writer literal fallbacks and constant columns are not measured, so this is never PASS |
| Narr | Narr.fidelity_test | PARTIAL (saved 2026-09-30: (absent in saved run)) | structural only: 2 test file(s) call the builder and assert in the same test function (test_bo_wp22_empty_shells.py, test_nar_ph_phaladesa.py); declared field(s) referenced: narration_jsonb.$.text; whether the assertion grades the sentence is not read, so this never reads PASS |
| Narr | Narr.lint | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — the narration lints are not applicable to this asset: no chart_facts fact_category selection in its 7-file writer scope and no declared column the raw-token lint covers; a clean scan of code they cannot see is not a pass |
| Dens | Dens.served | FAIL | STRUCTURAL: 1 module(s) reach it by code: L4_phala/query_domain_result.ts; 1 served select(s) of its table; no referencing capability that serves it declares density_contract |
| Build | Build.dep_liveness | PARTIAL | 1/7 declared dependencies lit at chart 482012f1 (or global); stale: ['ph_nimitta (stale, chart 482012f1)', 'ph_muhurta (stale, chart 482012f1)', 'ph_pratikara (stale, chart 482012f1)', 'ph_suddha_sodhana (stale, chart 482012f1)', 'ph_sankrama (stale, chart 482012f1)', 'ph_pramana (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Build | Build.history | PARTIAL | latest run complete, but 1 error(s) and 9 abort(s) on record (31 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-07-04): CheckViolation: new row for relation "phala_phaladesa" violates check constraint "phala_phaladesa_domain_canonical" DETAIL: Failing row contains (f3788905-85bb-40a1-8f65-7a90a279cd94, 1c826d5a-41cb-4 |
| Complete | Complete.depth | PARTIAL | 26 rows, 31 cols; fully populated 16; NEVER populated ['narration_requested_at', 'narration_model'] |
| Complete | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach | Reach.fields | NOT_GENERIC | reported, not graded — width 21/29 built column(s) (72.4%) selected by 1 capability module(s); dark: ['chart_id', 'computed_at', 'contradiction_summary_jsonb', 'derivation_ledger_jsonb', 'derivation_summary_jsonb', 'narration_jsonb', 'precedent_refs_jsonb', 'spillover_domains_jsonb']; depth 100.0% (a capability query reads it with no literal row pin (upper bound)) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13): complete with no disposition and not derivable as probe-green (no probe receipt names this run) — unclassified |
| Earn | Earn.service_state | N/A (saved 2026-09-30: (absent in saved run)) | declared kind 'data' is not `service`; Earn.service_state is the service-state check (a service's rows_written cannot tell healthy-and-idle from broken) |

**PASS cells (compact):** Ldgr.source_presence, Idem.pattern, Vocab.identity, Narr.agree, Narr.checkable, Build.registered, Build.contract, Build.target, Build.dag, Build.exercised, Build.completion, Build.count_integrity, Count.floor.

**Offline rollup** (main `asset_census.py` rollup rules at REGISTRY_REVISION 15 applied to the FRESH census; N/A reads NO_DETECTOR while `NA_RULE_DECISIONS` is empty; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null PARTIAL · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build PARTIAL.
Same rules over the SAVED 2026-09-30 census: Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build PARTIAL.

### 1.4 - Earned-signal (N.8), narration-fidelity (N.7) and honest-null audit of this asset's flags and verdicts

| field / claim | what it claims | what code path could make it read false | finding |
|---|---|---|---|
| `anchor_count`, `clean_anchor_count`, `staged_revision_count` | the anchors behind the domain and their review state | counted from `phala_anchors` x `phala_suddha_sodhana` at build time; stored 139 vs live 4; and `clean` is the unearned upstream label | **Stale counts presented as current** (real-stored); `clean` inherits CF-L4-03 |
| `top_anchor_id` | the headline anchor | first row per domain by (`clean` first, `confidence_high`) (`platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py:329-367`); no FK | dangles x6 (stored) |
| narration "N contradiction signal(s) temper this reading" | N real contradictions | `len(contradiction_summary_jsonb)` where the value is a 3-key dict (`platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py:138-142`) | **Invented count (always 3 for a dict) with `contested=false`** - a narration-fidelity defect (N.7 items 1 and 5: a sentence that grades something no fact says) |
| narration "N passed clean sodhana review" | N anchors were reviewed and passed | N = count of `cleanliness_status='clean'`, which is also the status of an unreviewable anchor | overstated while ph_sodhana cannot assess (G03 chain) |
| narration "Confidence band spans a-b" | an interval | the decorative +/-0.05 band of `ph_nimitta` (`platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py:119-123`) | repeats the unearned interval in prose |
| `incoming_spillover_count` | spillovers feeding the domain | row count of `phala_sankrama` for the target domain (`platform/python-sidecar/services/ph_phaladesa/engine.py:200`), = pairs x 5 ayanamshas | overcount x5 |
| `mitigation_available`, `muhurta_available` | remedies / windows exist for the domain | domain of the anchor each row is `linked_anchor_id`-joined to (`platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py:425-452`); a mitigation row with no linked anchor does not count (all 536 are unlinked) | **`false` means "no row linked to an anchor of this domain", not "no mitigation"** - 12 of 13 `false` beside 536 rows |
| B.11 whole-chart read (`b11_whole_chart_read: true`) | the Bodha synthesis informed the declaration | the ledger flag equals `count(bodha_msr_signals) > 0` (`platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py:301`); the MSR score is stored only in `derivation_summary_jsonb.b11_msr_score`; `b11_cdlm_link_count` and `b11_cgm_path_count` are always 0 because `cdlm_linkage_summary` / `cgm_paths_by_domain` are never populated by the writer | **A flag with no code path that could read false**: true whenever any MSR row exists, whatever was read or used (§N.8) |
| `derivation_ledger_jsonb.model_policy` | the narration model policy | the string "BANNED: anthropic/* PERMITTED: gemini/deepseek/gpt" (`platform/python-sidecar/services/ph_phaladesa/engine.py:227`) while the allowlist has no `gpt` (`platform/python-sidecar/services/ph_phaladesa/engine.py:42-45`, removed by SUDDHA-VACA Phase C) | stale literal contradicting the code |
| `narration_status` / engine docstring | "pending until an async step" | engine says `pending` always (`platform/python-sidecar/services/ph_phaladesa/engine.py:10,143,184,253`) and a test asserts it (`test_ph_wave7.py::test_narration_status_always_pending`); the writer overwrites it with `ready` (`platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py:279`) | two layers state opposite things; the tested layer is not the stored one |

### 1.5 - UUID chart_id check (the bo_*/ph_* adapter defect)

**Present but handled.** `derivation_ledger['chart_id'] = ctx.chart_id` (`platform/python-sidecar/services/ph_phaladesa/engine.py:222`) puts the raw `uuid.UUID` into a JSON payload; the writer serialises every payload with a local `_UUIDEncoder` (`platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py:35-40,272-281`), so it survives. The encoder is a copy of `ph_sodhana`'s (CF-L4-09). Other payload ids are `str()`.

## 2 - Gaps: which are real, which are detector or definition gaps

Class vocabulary: **real** = a shortfall in code, rows, registry row or served surface; **real-stored** = the CURRENT code already fixes it but the stored rows predate the fix (cured by a rebuild, not by an edit); **design** = needs an SS or acharya decision; **detector** = the instrument is absent or its definition is the open point; **history** = a recorded past outcome no edit can change; **information** = Count/Cost/Complete/Reach, never a blocker; **opportunity** = beyond the requirement.

| gap id | gate | class | note (evidence) |
|---|---|---|---|
| ph_phaladesa-G01 | Build / Carr | real-stored | Rows describe 139 anchors; 4 exist; `top_anchor_id` dangles x6; integrity SQL false; Build.completion PASS (13 = 13) earns nothing |
| ph_phaladesa-G02 | Narr | real | Contradiction sentence: count = dict length, `contested=false` x7 (`ph_phaladesa.py:138-142`) |
| ph_phaladesa-G03 | Earn | real | Silent-clean chain: "N passed clean sodhana review" while ph_sodhana cannot assess and ph_suddha_sodhana reads absence as clean (CF-L4-03) |
| ph_phaladesa-G04 | Null | real | Four loaders swallow every exception and return empty (`ph_phaladesa.py:318-323,396,421,452`): a read failure produces 13 rows saying "No predictive anchors were derived" and the build completes |
| ph_phaladesa-G05 | Earn | real | `b11_whole_chart_read` can never read false; CDLM/CGM counts always 0; MSR score only stored |
| ph_phaladesa-G06 | Narr | real | `incoming_spillover_count` x5 and "170 spillovers feed" into an anchor-less domain; `mitigation_available` reads the anchor link, not the obstruction domain |
| ph_phaladesa-G07 | Narr | real | Doc/ledger drift: model_policy string lists `gpt`; engine and test say `pending`, writer says `ready`; registry description, `index.ts`, `query_domain_result.ts` say 7 domains / "narration pending via Gemini/DeepSeek"; module docstring lists `phala_sodhana` as read |
| ph_phaladesa-G08 | Build | design | Overlap with the serving read model (`query_domain_result` could compute the same from the base tables) - T2 6.5 investigation (Q-L4-16) |
| ph_phaladesa-G09 | Vocab | real | `_ANCHOR_TO_PHALADESA_DOMAIN` keys are legacy words (`financial`, `spiritual`, `psychological`, `ph_phaladesa.py:53-57`), all dead since the anchor vocabulary converged |
| ph_phaladesa-G10 | Null / Narr / Dens | detector | Null PARTIAL, Narr.fidelity_test PARTIAL, Narr.lint NO_DETECTOR; Dens.served FAIL; `narration_model` / `narration_requested_at` NEVER populated (by design); Earn, Carr, Vocab.alias NO_DETECTOR |
| ph_phaladesa-G11 | Build | history | Build.history PARTIAL: the census reports 1 error (2026-07-04, a CheckViolation, since fixed) and 9 aborts; the reader's build history shows 0 errors and 9 aborts for this asset (not reconciled) |

## 3 - Disposition

DISPOSITION: qualify

EVIDENCE_POINTER: 00_ARCHITECTURE/briefs/suvarna/layers/L4/assets/_evidence/data/ph_phaladesa.json

EVIDENCE_EXTRA: this brief sections 1-4; 00_ARCHITECTURE/briefs/suvarna/layers/L4/assets/_evidence/upstream_receipts.json; 00_ARCHITECTURE/briefs/suvarna/layers/L4/assets/_evidence/rollup_L4.json; 00_ARCHITECTURE/briefs/suvarna/layers/L4/assets/_evidence/offline_checks.txt; 00_ARCHITECTURE/briefs/suvarna/layers/L4/assets/_evidence/rect_diag.txt; 00_ARCHITECTURE/briefs/suvarna/layers/census/census_L4.json (saved 2026-09-30 census); fresh 2026-10-02 census at /Users/Dev/suvarna-evidence/census_fresh/1e5781a/census_L4.json (outside the repo)

**qualify (Q) - make the summary derive only from rows that exist and the narration only from fields that mean what it says; the overlap with the serving read model is a question.** Qualify (Q): the asset is the layer's reader-facing summary and its mechanics are sound (13 rows by construction, empty domains stated, deterministic template, atomic replace), but it is the place where every upstream weakness becomes a sentence - an invented contradiction count, 'passed clean review', a confidence 'band', counts of rows that are not anchors. Its truthfulness is a function of the other eight, so it must be rebuilt last (wave 11) and its narration fixed first. T2 section 6.5's overlap investigation applies: whether a stored summary is needed beside the serving capability is Q-L4-16, not a proposal.

Approver under Track A brief section 10: **Steward (G16)** for keep/qualify/enrich; **SS** for any output change (R5). No disposition is applied by this brief.

## 4 - Fix designs (one per real gap; anything marked `needs production rebuild` or `needs migration` is a REVIEW item for Strategic Suvarna)

### FD-1 - Fix the narration before the next rebuild

- **Answers:** G02, G03, G06
- **Change:** (a) Contradiction sentence only when `contradiction_summary_jsonb.contested` is true, and report `net_direction`/`countervailing_thread`, not `len(dict)`; (b) "passed clean review" only for `cleanliness_status=clean` AND assessed (needs ph_suddha_sodhana `not_assessed`); (c) drop "Confidence band" until Q-L4-05 is answered; (d) report incoming spillovers as distinct (source, relationship) pairs.
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py:94-151`; `platform/python-sidecar/services/ph_phaladesa/engine.py:200`
- **Failing-first test and mutation:** failing-first: a dict with `contested:false` produces no sentence; a 3-key dict never yields "3"; mutation: restore `len()` -> fails (extends `test_nar_ph_phaladesa.py` with the REAL jsonb shape)
- **Output change:** yes - `narration_jsonb.text`
- **Blast radius:** `query_domain_result`
- **Rebuild:** rides FD-2
- **Gate it moves:** Narr
- **Fix class:** writer code; **risk class:** R2; **buildable before J1:** tier-independent for (a),(d); (b),(c) depend on CF-L4-03/04
- **Decision:** no question for (a),(d); Q-L4-05/12 for (b),(c)

### FD-2 - Rebuild last (wave 11)

- **Answers:** G01; CF-L4-01
- **Change:** Run after `ph_pramana`; it reads every sibling, so it is stale after any of them rebuilds.
- **Files / declaration / migration:** none
- **Failing-first test and mutation:** failing-first: integrity SQL true; `top_anchor_id` resolves for every domain with anchors; mutation: delete an anchor -> false
- **Output change:** yes
- **Blast radius:** `query_domain_result`
- **Rebuild:** needs production rebuild (REVIEW item)
- **Gate it moves:** Build
- **Fix class:** data (rebuild); **risk class:** R3; **buildable before J1:** tier-independent
- **Decision:** OPEN - Q-L4-01

### FD-3 - Fail loud; make B.11 a real read or say it is nominal

- **Answers:** G04, G05
- **Change:** Remove the four swallows (a missing sibling table is not a normal case once the DAG orders the build); either feed MSR/CDLM/CGM facts into output fields (e.g. a per-domain MSR salience column) or rename the ledger key `b11_msr_rows_present` and drop the CDLM/CGM counters.
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py:289-325,355-452`; `platform/python-sidecar/services/ph_phaladesa/engine.py:204-226`
- **Failing-first test and mutation:** failing-first: a forced read error fails the build; mutation: restore `except: return {}` -> fails
- **Output change:** none on a healthy read; ledger key rename
- **Blast radius:** none
- **Rebuild:** rides FD-2
- **Gate it moves:** Null, Earn
- **Fix class:** writer code; **risk class:** R2; **buildable before J1:** tier-independent
- **Decision:** no question; Steward

### FD-4 - Align every statement of what the asset is

- **Answers:** G07, G09
- **Change:** Update the registry description (13 domains, template narration), `index.ts` comment, `query_domain_result.ts` header, engine docstring and `model_policy` literal; delete the dead legacy domain map; make the engine's `narration_status` and the stored one the same.
- **Files / declaration / migration:** registry migration (description); the four code/doc locations above
- **Failing-first test and mutation:** failing-first: a test asserts the stored `narration_status` equals the engine's; mutation: set engine to `pending` -> fails
- **Output change:** none
- **Blast radius:** documentation + one registry text
- **Rebuild:** none
- **Gate it moves:** Narr
- **Fix class:** registry/declaration + docs; **risk class:** R1; **buildable before J1:** tier-independent
- **Decision:** no question; Steward

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L4-01** - *this asset:* rebuild wave 11; 13 rows describe 139 anchors
- **CF-L4-03** - *this asset:* narrates the silent-clean chain; Build.completion PASS earns nothing
- **CF-L4-04** - *this asset:* repeats the decorative band in prose
- **CF-L4-05** - *this asset:* four swallowing loaders
- **CF-L4-08** - *this asset:* `generated_at = date.today()` in narration
- **CF-L4-09** - *this asset:* UUID handled by a local encoder
- **CF-L4-10** - *this asset:* Null/Narr PARTIAL
- **CF-L4-11** - *this asset:* Dens FAIL
- **CF-L4-12** - *this asset:* description says 7 domains and pending narration
- **CF-L4-14** - *this asset:* legacy domain map

## 5 - Semantic fingerprint contract (for the rebuild plan)

Natural key `(chart_id, domain)` (13 per chart, CHECK-constrained to the canonical vocabulary). Fingerprint over every column except `phaladesa_id`, `computed_at` and `narration_jsonb` (embeds `date.today()` in `generated_at`, `platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py:150`; the registry note excludes it from the digest). Depends on the state of all eight siblings; compare only after the full wave.

## 6 - Preserved kernel, carriage check, opportunities

- **Preserved kernel:** Thirteen rows by construction (empty domains stated, not omitted), clean-first headline ranking (W3-3f), deterministic template with the method recorded, the narration-model allowlist and the DB CHECK that bans Anthropic models, atomic replace.
- **Carriage check (T4 4.1; one only):** D3: recompute `anchor_count`, `clean_anchor_count` and `top_anchor_id` per domain from `phala_anchors` x `phala_suddha_sodhana` (the integrity SQL does the first); recompute the narration from the stored columns with the builder and compare - possible because the narration is a pure function of the record.
- **By design, stated and not flagged:** Deterministic-first narration with `narration_model` NULL (no LLM), the Anthropic ban, and `phala_phaladesa_domain_canonical` are stated, not flagged.
- **Opportunities (never blocking):** serve the stored narration instead of re-deriving; store per-domain MSR salience.

## 7 - Decisions applied, questions for SS, Track I items arising

No decision has been applied: SS has not yet answered the A.L4 questions. This brief raises:

- **Q-L4-01** - Rebuild authority and order (see INDEX): this asset is last.
- **Q-L4-12** - Is "passed clean sodhana review" allowed in prose while `clean` can mean "not assessed"?
- **Q-L4-16** - Keep a stored per-domain summary beside the serving capability, or serve it from the base tables?

**Track I items arising (see INDEX section 8):** TI-L4-01, TI-L4-36, TI-L4-37, TI-L4-38, TI-L4-39, TI-L4-40.

