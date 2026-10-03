---
asset_id: ph_pramana
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
disposition: "keep (P) with one must-fix (chart-scope the life-event read) and a semantic question on what a "match" proves; rebuild"
disposition_proposal_approver: "Steward (G16); any output change to SS (R5)"
disposition_value: keep
risk_class: "R3 (a cross-chart contamination path in the read; D5 scope questions)"
decisions_applied: "none - SS has not answered the A.L4 questions (INDEX section 7); all dispositions and fix designs are proposals"
ss_questions: [Q-L4-01, Q-L4-15, Q-L4-05]
track_i_items: [TI-L4-01, TI-L4-32, TI-L4-33, TI-L4-34, TI-L4-35]
ledger_gap_ids: [ph_pramana-Build.completion, ph_pramana-Build.dep_liveness, ph_pramana-Build.history, ph_pramana-Carr.detector, ph_pramana-Complete.depth, ph_pramana-Cost.baseline, ph_pramana-Dens.served, ph_pramana-Earn.build_record]
---
# ph_pramana - Falsifiability evidence registry (no scoring)

> **PROVISIONAL - until J1; may register gaps, may not certify.** Every figure below comes from a stated read-only query (suvarna_reader SELECTs on 2026-10-03, receipts under `/Users/Dev/suvarna-evidence/A_L4/data/`), from the census, from the repository at main `3de3f8b15` (file:line), or from running the asset's pure engine functions locally with no database. Where something could not be determined it says so. Nothing here certifies a gate, approves a disposition or changes an asset.

## 0 - Identity: what the asset is

`ph_pramana` writes `phala_pramana`: exactly one record per `phala_anchors` row (`platform/python-sidecar/pipeline/orchestrator/writers/ph_pramana.py:124-158`) holding the falsifier text, its parsed `observable_criteria` (REFUTED / CONFIRMED clauses and the latest ISO date in the text, `platform/python-sidecar/services/ph_pramana/engine.py:117-140`), a window status against today (`pending / open / past_window`, `:102-111`), and an evidence type: `life_event_match` when a life-event row of the same normalised domain falls inside the anchor window (`:181-205`), `life_event_miss` when the window has closed and the log had data in the domain, `detector_unavailable` when it had none, else `pending_observation` (`:208-262`). `evidence_strength_label` is `direct / indirect / proxy` by type and domain (`:143-160`). The D5 NO-SCORING rule is enforced by a build-halt `_d5_gate` over eight forbidden field names (`platform/python-sidecar/pipeline/orchestrator/writers/ph_pramana.py:34-38,115-122`) and, in the registry integrity SQL, by a schema clause that the table has no numeric column at all. Delete-then-insert per chart (`:57`).

| field | value | source |
|---|---|---|
| kind | registry `asset_kind=artifact`, `asset_type=data`, `scope=per_chart`, `domain=chart`, `rung=R4`; role per L4 layer instance TG-L4-024: not assigned by any tier | `asset_registry` row, read 2026-10-03 |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2786` (live may differ by migration) | seed |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ph_pramana.py:40`; engine `platform/python-sidecar/services/ph_pramana/engine.py`; registry `has_writer=True` | code |
| target table(s) | `phala_pramana` | registry `target_table` / `count_sql` |
| live rows (canonical chart) / floor / build record | 4 / none / `rows_written=139`; rows per chart in the table(s): phala_pramana: 1c826d5a=56; 482012f1=4 | `count_sql` run read-only; `asset_throughput`; table group-by |
| state / last built | `stale` / 2026-08-13T01:16:22 UTC (run `cbd6ea44`); `built_against_writer_hash=unknown` | `asset_throughput` |
| catalog_status | CURRENT | registry |
| depends_on (declared, live) | `ph_nimitta`, `ph_sankrama`, `ph_muhurta`, `ph_pratikara`, `ph_sodhana`, `ph_suddha_sodhana` | `asset_registry.depends_on` |
| depends_on vs what the code reads | reads `phala_anchors` (`ph_nimitta` declared) and `life_events` (no producer asset: the registry row `lel_events` has no table and `has_writer=false`, so no edge can be declared). **Five of the six declared edges are unread**: `ph_sankrama`, `ph_muhurta`, `ph_pratikara`, `ph_sodhana`, `ph_suddha_sodhana` (the writer reads only the two tables above; `linked_sodhana_id` is never set). Ordering-only edges, kept so `ph_phaladesa` can follow; they make this asset go stale whenever any sibling rebuilds | code (file:line) + fresh census `Build.dag` |
| blast radius | declared dependents direct 2 / transitive 10 (active assets, every layer) | fresh census `blocking_radius` |
| code readers outside the asset (non-test py/ts/tsx, 20 files) | L5 / other writers (python-sidecar pipeline/orchestrator/writers): bo_laksana.py, bo_samskara.py, mi_bhavisya.py, ph_phaladesa.py; python-sidecar other: bodha_writers/_idempotency.py, brahmagyan/l0_formula_constants.py, ga_writers/ga_dashas_writer.py, services/ph_sodhana/engine.py; serving (platform-mcp/src): resources/vidhi/dossier_slices/dossier_slices.generated.ts; retrieval + app (platform/src): lib/build/recalibrationEnqueue.ts, lib/charts/servingImpact.ts, lib/jyotish/asset_names.ts, lib/retrieval/registry/knowledge/producer_editorial_review.ts, lib/retrieval/registry/knowledge/source_query_availability.ts, lib/retrieval/registry/layers/L3_kala/query_projections.ts, lib/retrieval/registry/layers/L4_phala/index.ts, lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts, lib/retrieval/registry/layers/L4_phala/query_predictive_anchors.ts, lib/retrieval/registry/layers/L4_phala/salience_order.ts, lib/retrieval/registry/layers/L5_mimamsa/query_predictions.ts | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src at `3de3f8b15` (tests, generated and migrations excluded) |
| served surface | `L4_phala/query_phala_calibration.ts` `query_falsifiers`, `L3_kala/query_projections.ts` (an L3 serving module reading an L4 table), `L5_mimamsa/query_predictions.ts`; read by `ph_phaladesa` (window status, evidence type) and `mi_bhavisya` (registry edge). No `density_contract` on any of the three (Dens.served FAIL) | code |
| role / scoring mode | manifestation-family asset of L4 Phala (T2 section 6.5); census `scoring: contribution`; 'observable criteria / falsifiers, window states, evidence links' (T2c); 'retain hard no-scoring; subject-scope event lookup and separate criteria from event matching' (T2c, not a tier) | tiers + census |
| invalidation / FK | `anchor_id -> phala_anchors ON DELETE CASCADE`; `linked_sodhana_id` has no FK | `pg_constraint` read 2026-10-03 |

## 1 - Measured state and the nine gates

### 1.1 - Live state on the canonical chart (read-only, 2026-10-03)

- **4 rows** (build record 139; no `target_floor` by design, the registry note says a floor would 'enshrine a count a dead detector produced'). All 4: `pending_observation`, `proxy`, `open`; `lel_entry_id`, `lel_entry_jsonb`, `linked_sodhana_id` NULL x4 (census NEVER populated). `lel_entry_id` can never be set: `life_events.id` is a uuid and the column is bigint (`platform/python-sidecar/pipeline/orchestrator/writers/ph_pramana.py:201`).
- **Unscoped life-event read, live consequence on the other chart.** `_load_lel` selects `FROM life_events ORDER BY event_date` with no chart filter (`platform/python-sidecar/pipeline/orchestrator/writers/ph_pramana.py:187-192`) and its docstring says the table 'carries no chart_id column'. The live table has `chart_id NOT NULL`, and **all 63 `life_events` rows belong to the canonical chart; the other built chart has 0**. Yet the other chart's `phala_pramana` holds **8 `life_event_miss` / `past_window` / `indirect` rows (spirituality anchors)**: refutations recorded for one person's anchors, against a log that has no events for that person. (They were written on 2026-08-12 by code that stamped every past-window anchor a miss - registry note; whether the canonical chart's events were consulted at that build is not provable from the rows.) **Under the current code the same unscoped read would compare those 8 anchors with the canonical chart's 10 `spiritual` events** - a path predicted from the code, not run.
- **Vocabulary reach.** Of the 63 events, 10 have a `category` the shared synonym map cannot resolve (`residential+travel` 3, `loss` 3, `other` 2, `creative` 2; local run of `_normalize_domain`, `offline_checks.txt`), so a quarter of the log can never match any anchor domain.
- The registry integrity SQL returns **true** (reader run): one row per anchor, no duplicates, and **no numeric column** in `phala_pramana` (the D5 schema clause). Build is `stale`, 0 of 6 declared dependencies lit.

Build history for this asset (all charts, `build_run_assets`): 9 aborted, 35 complete, 28 error/blocked_dependency, 19 queued; the last complete canonical-chart run is `cbd6ea44` (2026-08-13), and the 26+ `error/blocked_dependency` rows are cascade skips, not writer errors. The only non-cascade errors on record: none; 9 aborts (last 2026-07-13).

### 1.2 - Stored rows versus current code

Commits touching this asset's writer or engine AFTER its last build (2026-08-13 01:16 UTC): `09d4a9d8a` 2026-09-06 L4 W3-3g: ph_pramana — domain vocabulary mismatch made life_event_match unreachable (#1842).

`09d4a9d8a` (W3-3g, 2026-09-06): `life_event_match` made reachable through category normalisation, and a miss is only earned when the log has data in that domain (else `detector_unavailable`). The stored rows predate it; the 8 `life_event_miss` rows on the other chart are the old default behaviour.

### 1.3 - Census cells (fresh run, compared with the saved run)

Census used: fresh census `/Users/Dev/suvarna-evidence/census_fresh/1e5781a/census_L4.json` (generated 2026-10-02T10:12:59+05:30, chart 482012f1, inspector 1e5781a at REGISTRY_REVISION 10; outside the repo) compared with the repo's saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L4.json` (2026-09-30T20:23:50+05:30, inspector 2a78ec64d). Main's inspector is now at REGISTRY_REVISION 15: the offline rollup below applies its rules to the fresh census; no live re-measure was run.

| gate | criterion | fresh verdict | measured (fresh census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13): complete with no disposition and not derivable as probe-green (no probe receipt names this run) — unclassified |
| Null | Null.schema_default | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — prose_fields is undeclared for ph_pramana: never read as 'no prose' |
| Null | Null.blank_rows | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — prose_fields is undeclared for ph_pramana: never read as 'no prose' |
| Narr | Narr.agree | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — prose_fields is undeclared for ph_pramana: never read as 'no prose' |
| Narr | Narr.checkable | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — prose_fields is undeclared for ph_pramana: never read as 'no prose' |
| Narr | Narr.fidelity_test | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — prose_fields is undeclared for ph_pramana: never read as 'no prose' |
| Narr | Narr.lint | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — prose_fields is undeclared for ph_pramana: never read as 'no prose' |
| Dens | Dens.served | FAIL | STRUCTURAL: 3 module(s) reach it by code: L3_kala/query_projections.ts, L4_phala/query_phala_calibration.ts, L5_mimamsa/query_predictions.ts; 1 served select(s) of its table; no referencing capability that serves it declares density_contract |
| Build | Build.dep_liveness | PARTIAL | 0/6 declared dependencies lit at chart 482012f1 (or global); stale: ['ph_nimitta (stale, chart 482012f1)', 'ph_sankrama (stale, chart 482012f1)', 'ph_muhurta (stale, chart 482012f1)', 'ph_pratikara (stale, chart 482012f1)', 'ph_sodhana (stale, chart 482012f1)', 'ph_suddha_sodhana (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Build | Build.completion | FAIL | build record rows_written=139 disagrees with live=4 (count_sql over the target table; chart 482012f1) |
| Build | Build.history | PARTIAL | latest run complete, but 0 error(s) and 9 abort(s) on record (29 additional blocked_dependency row(s) excluded as cascade-only). |
| Complete | Complete.depth | PARTIAL | 60 rows, 14 cols; fully populated 11; NEVER populated ['lel_entry_id', 'lel_entry_jsonb', 'linked_sodhana_id'] |
| Complete | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach | Reach.fields | NOT_GENERIC | reported, not graded — width 8/11 built column(s) (72.7%) selected by 1 capability module(s); dark: ['chart_id', 'computed_at', 'derivation_ledger_jsonb']; depth 100.0% (a capability query reads it with no literal row pin (upper bound)) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13): complete with no disposition and not derivable as probe-green (no probe receipt names this run) — unclassified |
| Earn | Earn.service_state | N/A (saved 2026-09-30: (absent in saved run)) | declared kind 'data' is not `service`; Earn.service_state is the service-state check (a service's rows_written cannot tell healthy-and-idle from broken) |

**PASS cells (compact):** Ldgr.source_presence, Idem.pattern, Vocab.identity, Build.registered, Build.contract, Build.target, Build.dag, Build.exercised, Build.count_integrity.

**Offline rollup** (main `asset_census.py` rollup rules at REGISTRY_REVISION 15 applied to the FRESH census; N/A reads NO_DETECTOR while `NA_RULE_DECISIONS` is empty; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.
Same rules over the SAVED 2026-09-30 census: Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

### 1.4 - Earned-signal (N.8), narration-fidelity (N.7) and honest-null audit of this asset's flags and verdicts

| field / claim | what it claims | what code path could make it read false | finding |
|---|---|---|---|
| `evidence_type = life_event_match` / `evidence_strength_label = direct` | the predicted event happened (direct evidence) | a life event whose normalised domain equals the anchor's and whose date lies in the window (`engine.py:181-205`); the anchor's magnitude floor, direction and `observable_criteria` are parsed but never evaluated against the event | **A domain-and-date coincidence labelled `direct`.** Since the falsifier says "no event of magnitude >= minor", any same-domain event satisfies it; fine as a pointer, overstated as evidence |
| `evidence_type = life_event_miss` | the predicted event did not happen (a refutation) | earned only if the log had data in the domain (since W3-3g); but the log is read unscoped by chart (`platform/python-sidecar/pipeline/orchestrator/writers/ph_pramana.py:187-192`) | **Cross-chart contamination risk** and a recorded refutation of 8 anchors on a chart with no log (stored) |
| `window_status` | pending / open / past_window | `date.today()` (`platform/python-sidecar/pipeline/orchestrator/writers/ph_pramana.py:51`) | correct arithmetic, but a calendar-dependent stored value: it goes stale daily without a rebuild |
| `observable_criteria_jsonb` | machine-evaluable criteria | regex over the falsifier text; falls back to the literal "(see falsifier_text)" (`engine.py:117-140`); census cannot test it (no `prose_fields` declared) | a restatement of the falsifier text |
| D5 gate (`_d5_gate`) | no scoring field can be written | `hasattr(rec, col)` on a closed dataclass the engine defines in the same module (`platform/python-sidecar/pipeline/orchestrator/writers/ph_pramana.py:115-122`) - cannot read false unless someone adds a field | tautological in the writer; **the real detector is the schema clause in the integrity SQL** (no numeric column). By design; not flagged |
| `rows_written` | rows inserted | `rows_inserted += 1` unconditional beside `ON CONFLICT DO NOTHING` (`platform/python-sidecar/pipeline/orchestrator/writers/ph_pramana.py:108-110`) | latent (one row per anchor); same pattern as ph_sodhana |
| LEL recency | training vs outcome evidence | `life_events.recorded_at` (2000-01-01 to 2026-08-08) is ignored; `services/mimamsa/lel_calibration.py` routes by it for L5 | an event recorded after an anchor was computed can become its `match`; the freeze discipline is L5's, not enforced here |

### 1.5 - UUID chart_id check (the bo_*/ph_* adapter defect)

`chart_id` is a psycopg parameter (`:50,57,59,64,80,99`); `anchor_id` is `str(r['anchor_id'])` (`:139`); the LEL jsonb carries `str(r['id'])` (the uuid is stringified on purpose, `:213-214`). The `json.dumps` sites (`:102-107`) carry strings and dates-as-strings. **Not present today.**

## 2 - Gaps: which are real, which are detector or definition gaps

Class vocabulary: **real** = a shortfall in code, rows, registry row or served surface; **real-stored** = the CURRENT code already fixes it but the stored rows predate the fix (cured by a rebuild, not by an edit); **design** = needs an SS or acharya decision; **detector** = the instrument is absent or its definition is the open point; **history** = a recorded past outcome no edit can change; **information** = Count/Cost/Complete/Reach, never a blocker; **opportunity** = beyond the requirement.

| gap id | gate | class | note (evidence) |
|---|---|---|---|
| ph_pramana-G01 | Carr / Build | real | Unscoped `life_events` read (`ph_pramana.py:187-192`): table has `chart_id NOT NULL`; 8 stored `life_event_miss` rows on a chart that has 0 events; current code would match them against another chart's events |
| ph_pramana-G02 | Earn | design | `direct` evidence label for a domain+date coincidence; criteria never evaluated (Q-L4-15) |
| ph_pramana-G03 | Vocab | real | 10 of 63 life-event categories unresolvable (`residential+travel`, `loss`, `other`, `creative`); `_normalize_domain` returns None and the event can never match |
| ph_pramana-G04 | Null | real | Three columns can never be populated: `lel_entry_id` (uuid vs bigint), `lel_entry_jsonb` only on a match, `linked_sodhana_id` (never set) |
| ph_pramana-G05 | Build | real | Five declared-unread sibling edges (ordering only); `life_events` has no producer asset to declare |
| ph_pramana-G06 | Build | real-stored | Build record 139 vs live 4 (cascade of the anchors); pending/open statuses are calendar-dependent |
| ph_pramana-G07 | Build | real | `rows_inserted += 1` unconditional (`ph_pramana.py:110`) |
| ph_pramana-G08 | Narr | real | Registry description overclaims ("L5 onboarding contract + evaluation-staging + portfolio/reverse-calibration channel") against a one-row-per-anchor classifier; `_load_lel` docstring says there is no chart_id column |
| ph_pramana-G09 | Null / Narr | detector | `prose_fields` undeclared: Null.* and Narr.* all NO_DETECTOR |
| ph_pramana-G10 | Dens / Earn / Carr | detector | Dens.served FAIL (3 modules incl. an L3 module); Earn, Carr, Vocab.alias NO_DETECTOR |
| ph_pramana-G11 | Build | history | Build.history PARTIAL: 0 errors, 9 aborts |

## 3 - Disposition

DISPOSITION: keep

EVIDENCE_POINTER: 00_ARCHITECTURE/briefs/suvarna/layers/L4/assets/ph_pramana_ELEVATION_BRIEF_v1_0.md (sections 1-4); receipts `_evidence/` (data/, upstream_receipts.json, rollup_L4.json, offline_checks.txt, rect_diag.txt); census `layers/census/census_L4.json` + fresh census `census_fresh/1e5781a/census_L4.json`

**keep (P) with one must-fix (chart-scope the life-event read) and a semantic question on what a "match" proves; rebuild.** Keep (P): the asset is small, structural and its no-scoring rule is the best-protected in the layer (schema clause in SQL), and a falsifier registry is exactly what L5 needs to calibrate against. It keeps with one must-fix that is a data-isolation defect, not a style point (G01), and a question on what a 'match' may be called (G02). Nothing is proposed for consolidation: T2 section 6.5 lists it in the overlap investigation, but its responsibility (falsifier criteria + window state + evidence link) is not duplicated by the other five.

Approver under Track A brief section 10: **Steward (G16)** for keep/qualify/enrich; **SS** for any output change (R5). No disposition is applied by this brief.

## 4 - Fix designs (one per real gap; anything marked `needs production rebuild` or `needs migration` is a REVIEW item for Strategic Suvarna)

### FD-1 - Chart-scope the life-event read

- **Answers:** G01
- **Change:** `SELECT ... FROM life_events WHERE chart_id = %s AND event_date IS NOT NULL ORDER BY event_date, id`, as `ph_rectification._load_chart_training_events` already does; correct the docstring.
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_pramana.py:160-192`
- **Failing-first test and mutation:** failing-first: a fixture with events for chart A only builds chart B with `detector_unavailable`/`pending`, never `life_event_match`/`miss`; mutation: drop the filter -> B matches A's event
- **Output change:** yes - the 8 stored misses on the other chart are replaced on its rebuild
- **Blast radius:** the other chart's `phala_pramana` and `ph_phaladesa` rows
- **Rebuild:** needs production rebuild of BOTH built charts (REVIEW item); it is a privacy-relevant isolation fix, so it should land before any rebuild of a second chart
- **Gate it moves:** Carr
- **Fix class:** writer code; **risk class:** R2 (code) / R3 (second-chart effects); **buildable before J1:** tier-independent
- **Decision:** no question for the code; the rebuild is Q-L4-01

### FD-2 - Say what a match is

- **Answers:** G02, G03
- **Change:** Rename the label `direct` to `domain_window_coincidence` (or add `criteria_evaluated: false`) until `observable_criteria` is evaluated against the event's direction/magnitude; extend the synonym map for the four unresolvable categories only with an acharya mapping (`loss` -> ?, `creative` -> ?), otherwise record `unmapped_category` in the ledger rather than silently never matching.
- **Files / declaration / migration:** `platform/python-sidecar/services/ph_pramana/engine.py:143-195`; `brahmagyan/domain_vocabulary.py`
- **Failing-first test and mutation:** failing-first: an unmapped event category is counted in the ledger; mutation: drop the count -> fails
- **Output change:** yes - labels
- **Blast radius:** `ph_phaladesa.evidence_type`, `query_falsifiers`, L5 `mi_pariksha` retrodiction (reads anchors, not this table)
- **Rebuild:** needs production rebuild
- **Gate it moves:** Earn, Vocab
- **Fix class:** writer code (engine) + vocabulary; **risk class:** R3; **buildable before J1:** tier-dependent
- **Decision:** OPEN - Q-L4-15

### FD-3 - Make the never-populated columns honest

- **Answers:** G04
- **Change:** Carry the life-event uuid in a uuid column (additive) or document `lel_entry_id` as deprecated; either populate `linked_sodhana_id` from the anchor's worst flag or drop the column.
- **Files / declaration / migration:** migration; `platform/python-sidecar/pipeline/orchestrator/writers/ph_pramana.py:95-110`
- **Failing-first test and mutation:** failing-first: a match stores its event uuid; mutation: drop -> NULL
- **Output change:** additive
- **Blast radius:** low
- **Rebuild:** rides FD-1
- **Gate it moves:** Null
- **Fix class:** migration + writer code; **risk class:** R2; **buildable before J1:** tier-independent
- **Decision:** no question; Steward

### FD-4 - Edges, counting, declarations

- **Answers:** G05, G07, G08, G09; CF-L4-06, CF-L4-07, CF-L4-10
- **Change:** Drop the five unread sibling edges and express `ph_phaladesa`'s ordering on `ph_phaladesa` itself (it already declares them), or keep them with a registry note; count accepted rows; correct the registry description; declare `prose_fields` (`falsifier_text`).
- **Files / declaration / migration:** registry migration + `asset_declarations.json` + `platform/python-sidecar/pipeline/orchestrator/writers/ph_pramana.py:108-110`
- **Failing-first test and mutation:** failing-first: Build.dag still PASS after the edge drop; mutation: add a `phala_sankrama` read without the edge -> FAIL
- **Output change:** none
- **Blast radius:** freshness: stops going stale on unrelated sibling rebuilds
- **Rebuild:** none
- **Gate it moves:** Build, Null, Narr
- **Fix class:** registry/declaration + writer code; **risk class:** R2; **buildable before J1:** tier-independent
- **Decision:** no question; Steward

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L4-01** - *this asset:* rebuild wave 10
- **CF-L4-06** - *this asset:* unconditional `rows_inserted += 1`
- **CF-L4-07** - *this asset:* five declared-unread edges
- **CF-L4-08** - *this asset:* `date.today()` in window status
- **CF-L4-09** - *this asset:* UUID: handled by stringifying; not present
- **CF-L4-10** - *this asset:* `prose_fields` undeclared
- **CF-L4-11** - *this asset:* Dens FAIL (incl. an L3 module)
- **CF-L4-13** - *this asset:* L3 serving module reads this table
- **CF-L4-14** - *this asset:* life-event category vocabulary

## 5 - Semantic fingerprint contract (for the rebuild plan)

Natural key `(chart_id, anchor_id)` (the table's UNIQUE is the wider `(anchor_id, evidence_type, COALESCE(lel_entry_id,-1))`, `phala_pramana_natural_key`). Fingerprint over `(anchor_id, evidence_type, evidence_strength_label, window_status, falsifier_text)`; `pramana_id` and `computed_at` excluded. `window_status` is calendar-dependent: fix an as-of date for any before/after comparison.

## 6 - Preserved kernel, carriage check, opportunities

- **Preserved kernel:** One record per anchor; the schema-level no-numeric-column rule; the build-halt on forbidden scoring names; `detector_unavailable` instead of a refutation when the log had no data (W3-3g); the F2 category normalisation; the parsed REFUTED/CONFIRMED criteria.
- **Carriage check (T4 4.1; one only):** D2 (witness): for a sample of `life_event_match` rows, the stored `lel_entry_jsonb.id` must exist in `life_events` for THE SAME chart with a date inside the anchor window. This is also the isolation test for FD-1.
- **By design, stated and not flagged:** The D5 NO-SCORING gate and the layer's stance that calibration is L5's are stated, not flagged. The writer-side `hasattr` check being tautological is noted because the SQL schema clause is the real detector.
- **Opportunities (never blocking):** evaluate `observable_criteria` against the event (direction/magnitude) so a match is evidence; attach the event's `recorded_at` partition.

## 7 - Decisions applied, questions for SS, Track I items arising

No decision has been applied: SS has not yet answered the A.L4 questions. This brief raises:

- **Q-L4-01** - Rebuild authority and order (see INDEX); the chart-scope fix should precede any second-chart rebuild.
- **Q-L4-15** - May a same-domain, in-window life event be called `direct` evidence, and who maps the four unresolved life-event categories?
- **Q-L4-05** - Confirm the scope of D5: which stored columns elsewhere in L4 count as "scores"?

**Track I items arising (see INDEX section 8):** TI-L4-01, TI-L4-32, TI-L4-33, TI-L4-34, TI-L4-35.

