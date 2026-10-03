---
asset_id: ph_rectification
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
disposition: "qualify (Q) - fix the three input defects behind the all-zero fit and the negative interval; state that the product is a lagna-stability map unless SS wants a rectifier"
disposition_proposal_approver: "Steward (G16); any output change to SS (R5)"
disposition_value: qualify
risk_class: "R4 (touches the D43 no-auto-override rail, an upward consumer in L3, a DB-grant gap, and what the asset is for)"
decisions_applied: "none - SS has not answered the A.L4 questions (INDEX section 7); all dispositions and fix designs are proposals"
ss_questions: [Q-L4-01, Q-L4-04, Q-L4-05, Q-L4-17]
track_i_items: [TI-L4-01, TI-L4-41, TI-L4-42, TI-L4-43, TI-L4-44, TI-L4-45, TI-L4-46]
ledger_gap_ids: [ph_rectification-Build.dep_liveness, ph_rectification-Build.history, ph_rectification-Carr.detector, ph_rectification-Cost.baseline, ph_rectification-Dens.served, ph_rectification-Earn.build_record]
---
# ph_rectification - Birth-time rectification scan (staged, never auto-applied)

> **PROVISIONAL - until J1; may register gaps, may not certify.** Every figure below comes from a stated read-only query (suvarna_reader SELECTs on 2026-10-03, receipts under `/Users/Dev/suvarna-evidence/A_L4/data/`), from the census, from the repository at main `3de3f8b15` (file:line), or from running the asset's pure engine functions locally with no database. Where something could not be determined it says so. Nothing here certifies a gate, approves a disposition or changes an asset.

## 0 - Identity: what the asset is

`ph_rectification` writes two tables. `phala_rectification`: 37 candidate birth-time offsets (-90..+90 minutes, 5-minute steps, `platform/python-sidecar/services/ph_rectification/engine.py:112-114,237-239`) x 5 ayanamshas = 185 rows, each with the candidate ascendant (PyJHora via `pyjhora_adapter.houses.compute_ascendant`, `platform/python-sidecar/pipeline/orchestrator/writers/ph_rectification/__init__.py:207-243`), `lagna_stable` (the sign equals the recorded-time sign under every ayanamsha, `platform/python-sidecar/services/ph_rectification/engine.py:462-463`) and, for stable candidates only, a `lel_fit_score` = classical-rule matches / (2 x training events) (`:396-433,477`). `phala_rectification_best`: the offset with the highest mean fit, ties broken by smallest |offset|, with `win_margin`, a confidence label (`decisive >= 0.10`, `probable >= 0.05`, else `unresolved`), a `confidence_low/high` band, the top three competing offsets and `judgment_flags` (`platform/python-sidecar/services/ph_rectification/engine.py:529-628`). Training events are the chart's OWN `life_events` before 2020-01-01, each placed on this chart's own Vimshottari dasha lords (`platform/python-sidecar/pipeline/orchestrator/writers/ph_rectification/__init__.py:125-178`). D43: `auto_action` is always `stage_for_review` and the charts table is never written.

| field | value | source |
|---|---|---|
| kind | registry `asset_kind=artifact`, `asset_type=data`, `scope=per_chart`, `domain=chart`, `rung=R4`; role per L4 layer instance TG-L4-024: not assigned by any tier | `asset_registry` row, read 2026-10-03 |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2822` (live may differ by migration) | seed |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ph_rectification/__init__.py:246`; engine `platform/python-sidecar/services/ph_rectification/engine.py`; registry `has_writer=True` | code |
| target table(s) | `phala_rectification`, `phala_rectification_best` | registry `target_table` / `count_sql` |
| live rows (canonical chart) / floor / build record | 186 / 186 / `rows_written=186`; rows per chart in the table(s): phala_rectification: 482012f1=185; 1c826d5a=185; phala_rectification_best: 1c826d5a=1; 482012f1=1 | `count_sql` run read-only; `asset_throughput`; table group-by |
| state / last built | `stale` / 2026-08-13T01:16:06 UTC (run `cbd6ea44`); `built_against_writer_hash=unknown` | `asset_throughput` |
| catalog_status | CURRENT | registry |
| depends_on (declared, live) | `ph_nimitta` | `asset_registry.depends_on` |
| depends_on vs what the code reads | reads `life_events` (no producer asset), `chart_dashas` (`ga_dashas`, **undeclared** - fresh census Build.dag FAIL: reads `chart_dashas` at `platform/python-sidecar/pipeline/orchestrator/writers/ph_rectification/__init__.py:111`) and `chart_facts` graha-sign facts (`ga_positions`; not flagged by the census). **Declared `ph_nimitta` is unread**: the writer reads no `phala_anchors`, so the asset goes stale whenever the anchors are rebuilt | code (file:line) + fresh census `Build.dag` |
| blast radius | declared dependents direct 0 / transitive 0 (active assets, every layer) | fresh census `blocking_radius` |
| code readers outside the asset (non-test py/ts/tsx, 15 files) | python-sidecar other: brahmagyan/phala/rectification.py, services/ka_kshetra/uncertainty.py, services/mimamsa/lel_calibration.py; serving (platform-mcp/src): resources/vidhi/dossier_slices/dossier_slices.generated.ts, tools/phala_outlook.ts, tools/register_p1_ganita.ts; retrieval + app (platform/src): lib/build/recalibrationEnqueue.ts, lib/charts/servingImpact.ts, lib/cockpit/assetClearSpec.ts, lib/jyotish/asset_names.ts, lib/retrieval/registry/knowledge/producer_editorial_review.ts, lib/retrieval/registry/knowledge/source_query_availability.ts, lib/retrieval/registry/layers/L4_phala/index.ts, lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts, lib/retrieval/registry/layers/register_d7_channel.ts | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src at `3de3f8b15` (tests, generated and migrations excluded) |
| served surface | `L4_phala/query_phala_calibration.ts` `query_rectification` (candidates + best row; recomputes a 'non-discriminating' flag at read time); `platform-mcp/src/tools/register_p1_ganita.ts`, `phala_outlook.ts`; **an upward reader**: `services/ka_kshetra/stage3_clocks.py:1012` -> `uncertainty.fetch_sigma_t_days` reads `phala_rectification` to derive the birth-time uncertainty of L3 clocks, with no declared edge (`ka_kshetra` depends_on has no `ph_rectification`) | code |
| role / scoring mode | manifestation-family asset of L4 Phala (T2 section 6.5); census `scoring: contribution`; 'staged birth-time candidates and discrimination gate' (T2c); T1 section 13 'no automatic rectification, no outcome-driven personal tuning'; T2 6.5 separates rectification as its own method and authority gate | tiers + census |
| invalidation / FK | `chart_id -> charts` CASCADE on both tables (registry note); `phala_rectification_best.best_candidate_id` is a plain uuid (no FK). `native_adopted` / `adopted_at` are reset to their defaults on every rebuild (registry note) | `pg_constraint` read 2026-10-03 |

## 1 - Measured state and the nine gates

### 1.1 - Live state on the canonical chart (read-only, 2026-10-03)

- **186 rows** (185 + 1; floor 186; Build.completion PASS 186 = 186). Candidate rows: 5 ayanamsha codes (`lahiri`, `true_chitra`, `kp`, `raman`, `surya_siddhanta`) x 37 offsets; `lagna_stable` true on 95 rows (**19 of 37 offsets**, a contiguous sub-range that is not centred on the recorded time) and false on 90. `lagna_sign` at offset 0 equals the L1 `chart_facts` LAGNA sign under all 5 ayanamshas (reader join: true x5) - a sign-level carriage check that passes.
- **`lel_fit_score = 0.0000` on all 95 scored candidates** (`lel_events_matched = 0` of `lel_events_tested = 40`); the best row: offset 0, `best_lel_fit_score` 0, **`confidence_low = -0.2000`, `confidence_high = 0.2000`**, `win_margin = 0`, label `unresolved`, `lel_training_events = 40`, and `judgment_flags = {calibration_state: calibrated, load_bearing: true, lel_event_count: 64, rectification_basis: lel_fit}`. `load_bearing: true` on a fit of zero is the pre-F3 output (`_apply_discrimination_gate` now forces false when `win_margin` is 0, local run).
- **Why the fit is zero (diagnosed read-only, `rect_diag.txt`).** Two independent input defects in the writer: (1) the training event's domain is `row.get('domain') or row.get('category')` (`platform/python-sidecar/pipeline/orchestrator/writers/ph_rectification/__init__.py:173`) and `life_events.domain` is a compound slug (e.g. `health/chronic_onset`), but the engine looks up plain keys (`platform/python-sidecar/services/ph_rectification/engine.py:191-215`): only 1 of 40 events resolves any significator house; with the plain `category` 30 of 40 do (10 categories - `spiritual` 5, `psychological` 3, `other` 1, `finance` 1 - have no entry); (2) the natal sign index is keyed `fact_subject.capitalize()` (`platform/python-sidecar/pipeline/orchestrator/writers/ph_rectification/__init__.py:201`) while `chart_facts` subjects are 3-letter codes (`SAT`, `JUP`, `MAR`, `MER`, `VEN`, `RAH_MEAN`, `KET_MEAN`) and the dasha lords are full names (`Saturn` ...): **0 of 40 mahadasha lords resolve** (only `Sun` and `Moon` could). With both corrected the same function returns non-zero fits that DIFFER by candidate lagna sign (illustration only: 7, 21 and 12 matches out of 80 possible for three signs); it is not evidence that the rule is right.
- **Even a correct fit cannot choose within the stable window**: all 19 stable offsets share one lagna sign, so every stable candidate gets the same mean score, `win_margin` is 0 by construction, and the tie-break (smallest |offset|) selects offset 0 - the recorded time. `test_ph_rectification.py::test_uniform_scores_within_stable_window_is_expected` blesses this. Unstable candidates carry no score (`None`), so a better-fitting neighbouring sign is never compared.
- **Training-event precision is overstated**: every event is labelled `date_confidence='month-exact'` (`platform/python-sidecar/pipeline/orchestrator/writers/ph_rectification/__init__.py:175`) while `life_events.date_confidence` has `exact` 57, `year_only` 3, `month_known` 3 on this chart; of the 40 pre-2020 events 5 are `year_only`/`month_known`. The firewall (`platform/python-sidecar/services/ph_rectification/engine.py:218-234`) therefore cannot exclude them.
- **Role and grants.** `data_plane_builder` has INSERT/DELETE/SELECT on 8 `phala_*` tables but **no privilege at all on `phala_rectification` or `phala_rectification_best`** (`has_table_privilege`, read 2026-10-03); `ph_rectification` is not in the 25-asset canonical rebuild plan.

Build history for this asset (all charts, `build_run_assets`): 9 aborted, 37 complete, 26 error/blocked_dependency, 2 error, 19 queued; the last complete canonical-chart run is `cbd6ea44` (2026-08-13), and the 26+ `error/blocked_dependency` rows are cascade skips, not writer errors. The only non-cascade errors on record: 2 errors 2026-07-06 (`UndefinedColumn: column "chart_id" does not exist` on `life_events`; and `ValueError: no chart-specific LEL training-event corpus exists for chart_id=UUID('...')` - the UUID chart id repr is visible in that message), both fixed by the availability-driven rewrite, plus 9 aborts.

### 1.2 - Stored rows versus current code

Commits touching this asset's writer or engine AFTER its last build (2026-08-13 01:16 UTC): `0b10bdb32` 2026-09-06 L4 W3-3e: ph_rectification — load_bearing on a fit that discriminates nothing (#1834).

`0b10bdb32` (W3-3e, 2026-09-06): `load_bearing` is forced false when the fit does not discriminate. The stored `judgment_flags` still say `load_bearing: true`. `b9d2d254b` (2026-10-02, Swiss `.se1` made the canonical ephemeris backend) did not touch this writer, which uses PyJHora (`@records_swiss_backend` is not applied), so the N-28 backend receipt does not cover it (not determined whether PyJHora's ascendant agrees with the Swiss one at the degree level).

### 1.3 - Census cells (fresh run, compared with the saved run)

Census used: fresh census `/Users/Dev/suvarna-evidence/census_fresh/1e5781a/census_L4.json` (generated 2026-10-02T10:12:59+05:30, chart 482012f1, inspector 1e5781a at REGISTRY_REVISION 10; outside the repo) compared with the repo's saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L4.json` (2026-09-30T20:23:50+05:30, inspector 2a78ec64d). Main's inspector is now at REGISTRY_REVISION 15: the offline rollup below applies its rules to the fresh census; no live re-measure was run.

| gate | criterion | fresh verdict | measured (fresh census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13): complete with no disposition and not derivable as probe-green (no probe receipt names this run) — unclassified |
| Null | Null.schema_default | PARTIAL (saved 2026-09-30: (absent in saved run)) | no schema default on the declared prose column(s) judgment_flags, leakage_firewall_note; writer literal fallbacks and constant columns are not measured here, so this is never PASS |
| Null | Null.blank_rows | PARTIAL (saved 2026-09-30: (absent in saved run)) | no blank or placeholder row among the checkable prose rows; schema defaults are read by Null.schema_default and writer literal fallbacks and constant columns are not measured, so this is never PASS |
| Narr | Narr.checkable | PARTIAL (saved 2026-09-30: (absent in saved run)) | checkable rows per declared entry: judgment_flags.$.load_bearing_note=0, leakage_firewall_note=2; none or unknown on judgment_flags.$.load_bearing_note |
| Narr | Narr.fidelity_test | PARTIAL (saved 2026-09-30: (absent in saved run)) | structural only: 2 test file(s) call the builder and assert in the same test function (test_ph_rectification.py, test_ph_rectification_discrimination_gate.py); declared field(s) referenced: judgment_flags.$.load_bearing_note; no qualifying test names: leakage_firewall_note; whether the assertion grades the sentence is not read, so this never reads PASS |
| Dens | Dens.served | NO_DETECTOR (saved 2026-09-30: FAIL) | NO_DETECTOR — 1 serving-root file(s) naming phala_rectification lose the string scanner's sync (an unbalanced quote, a nested template literal, or a regex literal holding a quote desynced it): platform-mcp/src/tools/register_p1_ganita.ts; its served select and density_contract cannot be read — never FAIL, never the closable N/A |
| Build | Build.dag | FAIL (saved 2026-09-30: PASS) | 1 declared edge(s); exists: all 1 are active registry assets (every layer); cycle: ph_rectification is on no dependency cycle (registry-wide graph); reads-match: FAIL — missing depends_on edge: ph_rectification -> ga_dashas (reads chart_dashas at ph_rectification/__init__.py:111; the producer is reachable transitively via ph_nimitta, so ordering holds but the edge is undeclared) |
| Build | Build.dep_liveness | PARTIAL | 0/1 declared dependencies lit at chart 482012f1 (or global); stale: ['ph_nimitta (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Build | Build.history | PARTIAL | latest run complete, but 2 error(s) and 9 abort(s) on record (26 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-07-06): UndefinedColumn: column "chart_id" does not exist LINE 4: WHERE chart_id = $1 AND event_date IS NOT NULL ^ Traceback (most recent call last): File "/app/platfor |
| Complete | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach | Reach.fields | NOT_GENERIC | reported, not graded — width 12/13 built column(s) (92.3%) selected by 1 capability module(s); dark: ['chart_id']; depth 100.0% (a capability query reads it with no literal row pin (upper bound)) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13): complete with no disposition and not derivable as probe-green (no probe receipt names this run) — unclassified |
| Earn | Earn.service_state | N/A (saved 2026-09-30: (absent in saved run)) | declared kind 'data' is not `service`; Earn.service_state is the service-state check (a service's rows_written cannot tell healthy-and-idle from broken) |

**PASS cells (compact):** Idem.pattern, Vocab.identity, Narr.agree, Narr.lint, Build.registered, Build.contract, Build.target, Build.exercised, Build.completion, Build.count_integrity, Count.floor, Complete.depth.

**Offline rollup** (main `asset_census.py` rollup rules at REGISTRY_REVISION 15 applied to the FRESH census; N/A reads NO_DETECTOR while `NA_RULE_DECISIONS` is empty; this is not a re-measure and not a certification): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null PARTIAL · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr PARTIAL · Dens NO_DETECTOR · Build FAIL.
Same rules over the SAVED 2026-09-30 census: Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build PARTIAL.

### 1.4 - Earned-signal (N.8), narration-fidelity (N.7) and honest-null audit of this asset's flags and verdicts

| field / claim | what it claims | what code path could make it read false | finding |
|---|---|---|---|
| `lel_fit_score`, `lel_events_matched` | how well the dasha-lord house placement fits the life events from this candidate lagna | two input defects make it identically 0 (see live bullets); with them corrected it would still be uniform within a lagna sign | **A measurement that cannot read non-zero** (§N.8); stored 0.0000 x95 |
| `confidence_low` / `confidence_high` | an interval around the best score | `score -/+ (1 - score) x 0.2` (`platform/python-sidecar/services/ph_rectification/engine.py:591-592`): at score 0 it is [-0.2, 0.2] | **Out-of-range value persisted** (negative probability-like bound; no CHECK on `numeric`). Reproduced on current code (`offline_checks.txt`) |
| `confidence_label` | decisive / probable / unresolved | from `win_margin` only (`platform/python-sidecar/services/ph_rectification/engine.py:529-535`) | `unresolved` is the honest label and is earned; the label cannot become `decisive` while all stable candidates share a sign |
| `judgment_flags.calibration_state = calibrated`, `load_bearing` | enough events to lean on the fit | event COUNT >= 10 (`brahma_formula_constants.mimamsa_calibration_min_events = {n_min: 10}`), counted BEFORE the firewall (64 vs 40 trained) and unrelated to fit quality; `load_bearing` now gated on `win_margin` (`platform/python-sidecar/pipeline/orchestrator/writers/ph_rectification/__init__.py:49-80`) | stored `true` is real-stored; `calibrated` still means "10+ events exist", not "the fit is trustworthy" |
| `lagna_stable` | the lagna sign holds across all five ayanamshas for this candidate | real comparison of PyJHora ascendants per ayanamsha (`platform/python-sidecar/services/ph_rectification/engine.py:462-463`); offset-0 sign equals L1's | earned - the one substantive output of the asset: a map of how near the recorded time is to a sign boundary |
| `date_confidence` | precision of each training event's date | constant `month-exact` (`platform/python-sidecar/pipeline/orchestrator/writers/ph_rectification/__init__.py:175`) | a precision claim with no source; 5 of 40 events are coarser |
| `leakage_firewall_note` | post-2020 events held out | text built from `n_training` (`platform/python-sidecar/services/ph_rectification/engine.py:555-559`); the cutoff is a hard-coded date | accurate text of the code; the cutoff is a design constant |
| `ayanamsha_id` | the ayanamsha of the candidate | short codes (`lahiri`, `kp`, ...) vs the long ids used by L1/L2 (`lahiri_chitrapaksha`, `krishnamurti`, `surya_siddhanta_classical`) | a third ayanamsha vocabulary inside the chain; Vocab.identity tests uniqueness only |

### 1.5 - UUID chart_id check (the bo_*/ph_* adapter defect)

`ctx.config['chart_id']` is passed to `resolve_birth_params(chart_id, ...)` and psycopg parameters (`:257,269,296,297,337`); `best_candidate_id` comes from `RETURNING id` as a uuid and is passed back as a parameter (`:361-363,372`), never JSON-serialised; the one `json.dumps` (`:387-393`) carries `competing_candidates` (ints/floats) and the flag dict. **Evidence from the registry history that the UUID chart_id reached this writer's error text on 2026-07-06** (`ValueError ... chart_id=UUID('...')`, from the pre-rewrite corpus guard, now removed). **Not present today.**

## 2 - Gaps: which are real, which are detector or definition gaps

Class vocabulary: **real** = a shortfall in code, rows, registry row or served surface; **real-stored** = the CURRENT code already fixes it but the stored rows predate the fix (cured by a rebuild, not by an edit); **design** = needs an SS or acharya decision; **detector** = the instrument is absent or its definition is the open point; **history** = a recorded past outcome no edit can change; **information** = Count/Cost/Complete/Reach, never a blocker; **opportunity** = beyond the requirement.

| gap id | gate | class | note (evidence) |
|---|---|---|---|
| ph_rectification-G01 | Earn / Carr | real | Fit is 0.0000 on every scored candidate from two writer-input defects: compound domain slug (`ph_rectification/__init__.py:173`) and 3-letter fact subjects vs full dasha-lord names (`:201`); 0 of 40 lords resolve |
| ph_rectification-G02 | Null | real | `confidence_low = -0.2000` persisted (`engine.py:591`); no clamp, no CHECK |
| ph_rectification-G03 | Earn | real-stored | Stored `load_bearing: true` on a zero fit (fixed in code by `0b10bdb32`) |
| ph_rectification-G04 | Earn | design | The scan cannot discriminate within a lagna sign by construction; `calibrated` counts events before the firewall; the product is a lagna-stability map unless SS wants a rectifier (D41 whole-instrument scoring is future, `engine.py:34-66`) (Q-L4-17) |
| ph_rectification-G05 | Null | real | Constant `date_confidence = month-exact` for every event (`:175`); 5 of 40 trained events are coarser |
| ph_rectification-G06 | Build | real | Builder role has no privilege on the two tables; asset absent from the rebuild plan (Q-L4-04) |
| ph_rectification-G07 | Build | real | Undeclared edge `ga_dashas` (census FAIL, `:111`); declared-unread `ph_nimitta` |
| ph_rectification-G08 | Carr | real | An L3 asset reads this table without a declared edge (`ka_kshetra`, `stage3_clocks.py:1012`); inert today because < 2 usable candidates (all fits 0) so it uses the 120 s default |
| ph_rectification-G09 | Carr | real | The engine module embeds the canonical native's own birth instant and coordinates, a 19-event corpus, natal sign indices and dasha boundaries as constants and falls back to them when a caller omits arguments (`engine.py:93-96,166-186,253-259,287-290,450-452,516,553`); the writer always passes explicit values (JL-017 firewall) but the defaults remain |
| ph_rectification-G10 | Ldgr | real | No `source_citation` column on either table: Ldgr.source_presence has no row (layer instance 3.3). Provenance is derivable from the writer (inputs: the chart's birth parameters, `life_events` ids, engine rule) but is not recorded per row; see section 6 for the table-level declaration proposal |
| ph_rectification-G11 | Vocab | real | Ayanamsha short codes differ from the L1/L2 long ids (`lahiri` vs `lahiri_chitrapaksha`, `kp` vs `krishnamurti`) |
| ph_rectification-G12 | Build | design | D43 approval state (`native_adopted`, `adopted_at`) is reset on every rebuild (registry note) - same design question as ph_suddha_sodhana (Q-L4-12) |
| ph_rectification-G13 | Carr | detector | PyJHora ascendant backend is outside the N-28 Swiss-backend receipt; degree-level parity with L1 not determined |
| ph_rectification-G14 | Null / Narr / Dens | detector | Null PARTIAL, Narr.checkable / fidelity_test PARTIAL (declared `judgment_flags.load_bearing_note`, `leakage_firewall_note`); Dens.served NO_DETECTOR (scanner desync on `register_p1_ganita.ts`); Earn, Carr, Vocab.alias NO_DETECTOR |
| ph_rectification-G15 | Build | history | Build.history PARTIAL: 2 errors (2026-07-06, fixed) + 9 aborts |

## 3 - Disposition

DISPOSITION: qualify

EVIDENCE_POINTER: 00_ARCHITECTURE/briefs/suvarna/layers/L4/assets/ph_rectification_ELEVATION_BRIEF_v1_0.md (sections 1-4); receipts `_evidence/` (data/, upstream_receipts.json, rollup_L4.json, offline_checks.txt, rect_diag.txt); census `layers/census/census_L4.json` + fresh census `census_fresh/1e5781a/census_L4.json`

**qualify (Q) - fix the three input defects behind the all-zero fit and the negative interval; state that the product is a lagna-stability map unless SS wants a rectifier.** Qualify (Q): the asset is correctly fenced (no auto-override, stage-only, per-chart firewall) and its `lagna_stable` map is real and consistent with L1, but its scoring half has never produced a non-zero number, persists an out-of-range interval, and cannot discriminate within a sign even when repaired. It should be described and served as what it measurably is until SS decides whether a true rectifier is wanted. T2 section 6.5 keeps rectification under its own authority gate, so no consolidation is proposed; retirement is not proposed because an L3 asset reads it (inertly) and the stability map is useful.

Approver under Track A brief section 10: **Steward (G16)** for keep/qualify/enrich; **SS** for any output change (R5). No disposition is applied by this brief.

## 4 - Fix designs (one per real gap; anything marked `needs production rebuild` or `needs migration` is a REVIEW item for Strategic Suvarna)

### FD-1 - Repair the two input defects (and prove the fit moves)

- **Answers:** G01, G05
- **Change:** (a) `TrainingEvent.domain` <- the plain `category` (or split `domain` on `/` and keep the head); (b) key the natal sign index by the dasha-lord vocabulary (map `SAT`->`Saturn`, `RAH_MEAN`->`Rahu`, ... or read `fact_subject` through the shared graha-name table); (c) pass the event's real `date_confidence` and map `year_only` / `month_known` below the firewall threshold; (d) add the missing categories to `_DOMAIN_HOUSES` only with an acharya mapping.
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_rectification/__init__.py:125-201`; `platform/python-sidecar/services/ph_rectification/engine.py:191-215`
- **Failing-first test and mutation:** failing-first: for the canonical fixtures `lel_events_matched > 0` on at least one stable candidate and differs between candidate lagna signs; mutation: restore either defect -> matched = 0. The diagnostic `rect_diag.py` is the starting harness
- **Output change:** yes - every candidate row's `lel_fit_score`, the best row
- **Blast radius:** `ka_kshetra` sigma_T (would become non-default only if >= 2 usable candidates carry positive fit), `query_rectification`, L5 readers of judgment_flags
- **Rebuild:** needs production rebuild (and a builder grant, FD-4)
- **Gate it moves:** Earn, Null
- **Fix class:** writer code; **risk class:** R3 (the first non-zero fits will be read as rectification evidence; an acharya should review the rule before they are served); **buildable before J1:** tier-dependent (acharya on the rule, Q-L4-17)
- **Decision:** OPEN - Q-L4-17

### FD-2 - Clamp the interval and keep the discrimination gate honest

- **Answers:** G02, G03, G04
- **Change:** Clamp `confidence_low/high` to [0, 1] (or store NULL when the score is 0 / unresolved); add a CHECK; compute `calibration_state` from the firewall-surviving count (40) not the raw count (64) and add the fit/discrimination condition to `calibrated`, not only to `load_bearing`.
- **Files / declaration / migration:** `platform/python-sidecar/services/ph_rectification/engine.py:591-592`; `platform/python-sidecar/pipeline/orchestrator/writers/ph_rectification/__init__.py:296-328`; migration (CHECK)
- **Failing-first test and mutation:** failing-first: a zero-fit best row has NULL or in-range bounds; mutation: restore the formula -> -0.2; amends `test_ph_rectification.py::test_confidence_interval_widens_below_one`
- **Output change:** yes
- **Blast radius:** `query_rectification` reads `confidence_*`
- **Rebuild:** needs production rebuild
- **Gate it moves:** Null, Earn
- **Fix class:** writer code (+ CHECK migration); **risk class:** R2; **buildable before J1:** tier-independent for the clamp; `calibrated` semantics shared with L5 (`services/mimamsa/lel_calibration.py` says do not reshape without a coordinated migration)
- **Decision:** no question for the clamp; Q-L4-05 for the shared flags

### FD-3 - Say what the scan is

- **Answers:** G04
- **Change:** Serve and describe `phala_rectification` as a lagna-stability map (candidate ascendant per ayanamsha, stability, fit NULL until a discriminating rule exists) and set `best_*` to NULL when `win_margin = 0` instead of electing offset 0; or commission the D41 whole-instrument scoring (bhava cusps, navamsa, sub-degree).
- **Files / declaration / migration:** registry description; `ph_rectification/__init__.py:323-398`; serving docs
- **Failing-first test and mutation:** failing-first: `win_margin = 0` yields `best_candidate_id IS NULL` and label `unresolved`; mutation: restore tie-break election -> fails
- **Output change:** yes
- **Blast radius:** `query_rectification` consumers
- **Rebuild:** needs production rebuild
- **Gate it moves:** Earn
- **Fix class:** writer code + docs; **risk class:** R4; **buildable before J1:** tier-dependent
- **Decision:** OPEN - Q-L4-17

### FD-4 - Grants, plan membership, edges

- **Answers:** G06, G07, G08
- **Change:** Grant `data_plane_builder` the same privileges it holds on the other 8 `phala_*` tables (migration) and decide whether the asset joins the canonical rebuild plan; declare `ph_rectification -> ga_dashas`; drop or justify `ph_nimitta`; declare or remove the L3 reader (`ka_kshetra`) - the one-way rule says an L4 conclusion must not feed an L3 computation.
- **Files / declaration / migration:** migration (grant + edges)
- **Failing-first test and mutation:** failing-first: `has_table_privilege('data_plane_builder', ...)` true; Build.dag PASS; mutation: revoke -> permission denied at the writer
- **Output change:** none
- **Blast radius:** rebuild plan membership; `ka_kshetra` sigma_T source
- **Rebuild:** none
- **Gate it moves:** Build
- **Fix class:** registry/declaration + migration; **risk class:** R3 (grant; cross-layer consumer); **buildable before J1:** tier-independent for the edges; the grant and the L3 reader are SS's
- **Decision:** OPEN - Q-L4-04

### FD-5 - Remove personal constants from the engine module; vocabulary

- **Answers:** G09, G11
- **Change:** Move the embedded native corpus and constants to a test fixture and make `recorded_birth_utc`, `training_events`, `dasha_lord_natal_sign_index` required (no defaults); translate ayanamsha codes at the write boundary or add the L1 long id as a column.
- **Files / declaration / migration:** `platform/python-sidecar/services/ph_rectification/engine.py:93-96,166-186,253-259,287-290,450-552`; tests that import the constants
- **Failing-first test and mutation:** failing-first: calling `run_rectification` without explicit inputs raises; mutation: restore a default -> fails
- **Output change:** none for the writer path
- **Blast radius:** unit tests that rely on the defaults (`test_ph_rectification.py` ~15 tests)
- **Rebuild:** none
- **Gate it moves:** Carr, Vocab
- **Fix class:** writer code (engine); **risk class:** R2; **buildable before J1:** tier-independent
- **Decision:** no question; Steward

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L4-01** - *this asset:* not in the canonical plan; stored rows are pre-F3 output
- **CF-L4-02** - *this asset:* builder grant gap
- **CF-L4-04** - *this asset:* zero fit, negative interval
- **CF-L4-07** - *this asset:* undeclared `ga_dashas`, declared-unread `ph_nimitta`
- **CF-L4-09** - *this asset:* UUID chart_id seen in 2026-07-06 error text; not present today
- **CF-L4-10** - *this asset:* Null/Narr PARTIAL
- **CF-L4-11** - *this asset:* Dens NO_DETECTOR (scanner desync)
- **CF-L4-13** - *this asset:* upward consumer `ka_kshetra`
- **CF-L4-15** - *this asset:* Ldgr: no citation column

## 5 - Semantic fingerprint contract (for the rebuild plan)

Natural keys `(chart_id, offset_minutes, ayanamsha_id)` and `phala_rectification_best (chart_id)`. Fingerprint over `(offset_minutes, ayanamsha_id, lagna_sign, lagna_longitude_deg, lagna_degree_in_sign, lagna_stable, lel_fit_score, lel_events_matched)` and the best row's `(offset_minutes, confidence_label, win_margin)`; `id`, `scored_at`, `best_candidate_id`, `native_adopted`, `adopted_at` excluded. The scan grid is chart-independent by design; the ascendants are per chart. Deterministic for fixed inputs.

## 6 - Preserved kernel, carriage check, opportunities

- **Preserved kernel:** D43 stage-only (`auto_action='stage_for_review'` asserted in the engine and DB), the per-chart training-event firewall (the JL-017 contamination guard in the writer), the 37 x 5 grid, the lagna-stability test across ayanamshas (consistent with L1 at offset 0), the discrimination gate on `load_bearing`.
- **Carriage check (T4 4.1; one only):** D3 (re-derivation): recompute the ascendant sign of the offset-0 candidate for each of the five ayanamshas through the L1 chart_facts LAGNA sign (done once above at sign level: equal x5) and, at degree level, through the canonical Swiss backend; recompute `lel_fit_score` from the stored candidates and the chart's events with the repository's `_score_dasha_match` (`rect_diag.py`).
- **By design, stated and not flagged:** D43 NO-AUTO-OVERRIDE and 'no automatic rectification' (T1 section 13) are stated, not flagged; the leakage firewall (pre-2020 cut) is a design constant; the sign-level (not sub-degree) scan is documented in the engine header as the current architecture. Table-level provenance proposal for the citation-less tables: `phala_rectification` and `phala_rectification_best` are COMPUTED from the chart's own birth parameters and `life_events` rows (ids carried implicitly by `lel_events_tested/matched`, with the rule in `engine.py`); a table-level declaration (inputs, rule, engine path, firewall cutoff) with evidence pointers `ph_rectification/__init__.py:257-352` and `engine.py:396-433` is adequate for the candidate table, while the best row additionally lacks the engine/code version and the input event ids - that part is a real gap for Track I.
- **Opportunities (never blocking):** record the input event ids and engine version on the best row; a sub-degree scan on real ephemeris.

## 7 - Decisions applied, questions for SS, Track I items arising

No decision has been applied: SS has not yet answered the A.L4 questions. This brief raises:

- **Q-L4-01** - Rebuild authority and order (see INDEX); this asset is outside the current plan.
- **Q-L4-04** - Grant `data_plane_builder` on the two rectification tables and add the asset to the canonical rebuild plan? May `ka_kshetra` keep reading `phala_rectification`?
- **Q-L4-05** - Is a stored 0-1 `lel_fit_score` / `confidence_*` an allowed L4 score?
- **Q-L4-17** - (acharya) Is "dasha lord in a domain-significator house from the candidate lagna" a rule you accept for rectification, and is the intended product a lagna-stability map or a rectifier?

**Track I items arising (see INDEX section 8):** TI-L4-01, TI-L4-41, TI-L4-42, TI-L4-43, TI-L4-44, TI-L4-45, TI-L4-46.

