---
asset_id: ph_suddha_sodhana
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
disposition: "qualify (Q) - fix the "clean" semantics and the approval-state design; consolidation with ph_sodhana is a question (Q-L4-12), not proposed"
disposition_proposal_approver: "Steward (G16); any output change to SS (R5)"
disposition_value: qualify
risk_class: "R3 (CHECK-constraint and approval-state design; propagates into ph_phaladesa narration)"
decisions_applied: "none - SS has not answered the A.L4 questions (INDEX section 7); all dispositions and fix designs are proposals"
ss_questions: [Q-L4-01, Q-L4-12]
track_i_items: [TI-L4-01, TI-L4-15, TI-L4-19, TI-L4-20, TI-L4-21]
ledger_gap_ids: [ph_suddha_sodhana-Build.completion, ph_suddha_sodhana-Build.dep_liveness, ph_suddha_sodhana-Build.history, ph_suddha_sodhana-Carr.detector, ph_suddha_sodhana-Complete.depth, ph_suddha_sodhana-Cost.baseline, ph_suddha_sodhana-Count.floor, ph_suddha_sodhana-Dens.served, ph_suddha_sodhana-Earn.build_record]
---
# ph_suddha_sodhana - Cleansed anchor disposition (one row per anchor)

> **PROVISIONAL - until J1; may register gaps, may not certify.** Every figure below comes from a stated read-only query (suvarna_reader SELECTs on 2026-10-03, receipts under `/Users/Dev/suvarna-evidence/A_L4/data/`), from the census, from the repository at main `3de3f8b15` (file:line), or from running the asset's pure engine functions locally with no database. Where something could not be determined it says so. Nothing here certifies a gate, approves a disposition or changes an asset.

## 0 - Identity: what the asset is

`ph_suddha_sodhana` writes `phala_suddha_sodhana`: exactly one row per `phala_anchors` anchor (`platform/python-sidecar/pipeline/orchestrator/writers/ph_suddha_sodhana.py:120-126`), classified `clean` (no `phala_sodhana` flag), `flagged` (only minor/informational flags) or `staged_revision` (any major/critical flag) from the per-anchor severity counts of `phala_sodhana` (`platform/python-sidecar/services/ph_suddha_sodhana/engine.py:72-80`). For staged rows it lists the proposed corrections (`staged_revision_jsonb`, `auto_apply: false`, `:83-103`) and a rough `confidence_delta_if_applied` read by regex from the flag's expected-value text (`:106-125`). D43 rail: `revision_approved_by` and `revision_applied_at` are inserted as literal NULLs (`platform/python-sidecar/pipeline/orchestrator/writers/ph_suddha_sodhana.py:79-80`) and asserted None on the engine record (`:64-65`). Writer deletes the chart's rows then inserts with `ON CONFLICT (chart_id, anchor_id) DO UPDATE` (`:89-101`); the read of flags fails loud since F-16 (`:128-153`).

| field | value | source |
|---|---|---|
| kind | registry `asset_kind=artifact`, `asset_type=data`, `scope=per_chart`, `domain=chart`, `rung=R4`; role per L4 layer instance TG-L4-024: not assigned by any tier | `asset_registry` row, read 2026-10-03 |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2750` (live may differ by migration) | seed |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ph_suddha_sodhana.py:30`; engine `platform/python-sidecar/services/ph_suddha_sodhana/engine.py`; registry `has_writer=True` | code |
| target table(s) | `phala_suddha_sodhana` | registry `target_table` / `count_sql` |
| live rows (canonical chart) / floor / build record | 4 / 139 / `rows_written=139`; rows per chart in the table(s): phala_suddha_sodhana: 1c826d5a=56; 482012f1=4 | `count_sql` run read-only; `asset_throughput`; table group-by |
| state / last built | `stale` / 2026-08-13T01:16:09 UTC (run `cbd6ea44`); `built_against_writer_hash=unknown` | `asset_throughput` |
| catalog_status | CURRENT | registry |
| depends_on (declared, live) | `ph_sodhana`, `ph_nimitta` | `asset_registry.depends_on` |
| depends_on vs what the code reads | reads `phala_anchors` (`ph_nimitta` declared) and `phala_sodhana` (`ph_sodhana` declared). No undeclared read found and no declared-unread edge | code (file:line) + fresh census `Build.dag` |
| blast radius | declared dependents direct 2 / transitive 11 (active assets, every layer) | fresh census `blocking_radius` |
| code readers outside the asset (non-test py/ts/tsx, 8 files) | L5 / other writers (python-sidecar pipeline/orchestrator/writers): ph_phaladesa.py; python-sidecar other: bodha_writers/_idempotency.py; retrieval + app (platform/src): lib/jyotish/asset_names.ts, lib/retrieval/registry/knowledge/producer_editorial_review.ts, lib/retrieval/registry/knowledge/source_query_availability.ts, lib/retrieval/registry/layers/L4_phala/index.ts, lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts, lib/retrieval/registry/layers/L4_phala/salience_order.ts | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src at `3de3f8b15` (tests, generated and migrations excluded) |
| served surface | `L4_phala/query_phala_calibration.ts` `query_cleansed_anchors` (selects a tier column without `density_contract`, per the Dens text); read by `ph_phaladesa` (clean / staged counts and the top-anchor ranking) | code |
| role / scoring mode | manifestation-family asset of L4 Phala (T2 section 6.5); census `scoring: contribution`; 'usable/caveated/revision-staged anchor disposition' (T2c label); T2 section 6.5 calls it a provenance kernel | tiers + census |
| invalidation / FK | `anchor_id -> phala_anchors ON DELETE CASCADE` | `pg_constraint` read 2026-10-03 |

## 1 - Measured state and the nine gates

### 1.1 - Live state on the canonical chart (read-only, 2026-10-03)

- **4 rows**, one per surviving anchor, **all `clean`** with `critical/major/minor_flag_count = 0`, `flag_ids_jsonb`, `staged_revision_jsonb`, `confidence_delta_if_applied`, `magnitude_delta_if_applied` NULL and the D43 columns NULL (as required). Floor 139, build record 139 (Build.completion FAIL, Count.floor FAIL: both consequences of the 135 anchors' removal).
- **`clean` here means 'ph_sodhana wrote nothing'.** `phala_sodhana` is empty for the chart because its chart-wide detectors cannot fire on 4 anchors (see ph_sodhana brief); `classify_cleanliness` returns `clean` for zero counts (`platform/python-sidecar/services/ph_suddha_sodhana/engine.py:72-80`). The 4 anchors are in fact identical in confidence (0.372) and carry the constant `(0, 3)` ceiling inputs. On the other built chart the same asset reads 19 `clean`, 1 `flagged`, 36 `staged_revision` of 56.
- **`magnitude_delta_if_applied` can never be populated**: it is computed only `if staged` (`platform/python-sidecar/services/ph_suddha_sodhana/engine.py:145-146`) and `staged` requires a major/critical flag, but the only detector that produces a magnitude flag (`magnitude_drift`) is severity `minor`. The census confirms the column NEVER populated.
- **A native approval cannot survive.** `revision_approved_by` / `revision_applied_at` are on a table the writer empties per chart on every rebuild (`:56-57`), and the registry integrity SQL forbids any non-NULL value on the chart (`WHERE revision_approved_by IS NOT NULL OR revision_applied_at IS NOT NULL ... = false`). The D43 'future operator action after native sign-off' therefore has no place to be stored.
- Build is `stale`; 0 of 2 declared dependencies lit (`ph_sodhana`, `ph_nimitta` both stale). The registry integrity SQL returns **true** (reader run).

Build history for this asset (all charts, `build_run_assets`): 9 aborted, 35 complete, 28 error/blocked_dependency, 19 queued; the last complete canonical-chart run is `cbd6ea44` (2026-08-13), and the 26+ `error/blocked_dependency` rows are cascade skips, not writer errors. The only non-cascade errors on record: none; 9 aborts (last 2026-07-13).

### 1.2 - Stored rows versus current code

Commits touching this asset's writer or engine AFTER its last build (2026-08-13 01:16 UTC): `b0f7fcb9a` 2026-09-06 L4 W3-3i: ph_suddha_sodhana — silent classify-clean on read failure (F-16) (#1849).

`b0f7fcb9a` (W3-3i / F-16, 2026-09-06): a read failure of `phala_sodhana` no longer labels every anchor `clean`. The stored rows were written by the older writer, so whether the 4 `clean` rows came from a real empty read or a swallowed error cannot be told from the rows.

### 1.3 - Census cells (fresh run, compared with the saved run)

Census used: fresh census `/Users/Dev/suvarna-evidence/census_fresh/1e5781a/census_L4.json` (generated 2026-10-02T10:12:59+05:30, chart 482012f1, inspector 1e5781a at REGISTRY_REVISION 10; outside the repo) compared with the repo's saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L4.json` (2026-09-30T20:23:50+05:30, inspector 2a78ec64d). Main's inspector is now at REGISTRY_REVISION 15: the offline rollup below applies its rules to the fresh census; no live re-measure was run.

| gate | criterion | fresh verdict | measured (fresh census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13): complete with no disposition and not derivable as probe-green (no probe receipt names this run) — unclassified |
| Null | Null.schema_default | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — prose_fields is undeclared for ph_suddha_sodhana: never read as 'no prose' |
| Null | Null.blank_rows | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — prose_fields is undeclared for ph_suddha_sodhana: never read as 'no prose' |
| Narr | Narr.agree | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — prose_fields is undeclared for ph_suddha_sodhana: never read as 'no prose' |
| Narr | Narr.checkable | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — prose_fields is undeclared for ph_suddha_sodhana: never read as 'no prose' |
| Narr | Narr.fidelity_test | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — prose_fields is undeclared for ph_suddha_sodhana: never read as 'no prose' |
| Narr | Narr.lint | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — prose_fields is undeclared for ph_suddha_sodhana: never read as 'no prose' |
| Dens | Dens.served | FAIL | STRUCTURAL: 1 module(s) reach it by code: L4_phala/query_phala_calibration.ts; 1 served select(s) of its table; no referencing capability that serves it declares density_contract |
| Build | Build.dep_liveness | PARTIAL | 0/2 declared dependencies lit at chart 482012f1 (or global); stale: ['ph_sodhana (stale, chart 482012f1)', 'ph_nimitta (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Build | Build.completion | FAIL | build record rows_written=139 disagrees with live=4 (count_sql over the target table; chart 482012f1) |
| Build | Build.history | PARTIAL | latest run complete, but 0 error(s) and 9 abort(s) on record (29 additional blocked_dependency row(s) excluded as cascade-only). |
| Count | Count.floor | FAIL | live=4, floor=139, delta=-135 |
| Complete | Complete.depth | PARTIAL | 60 rows, 16 cols; fully populated 10; NEVER populated ['revision_approved_by', 'revision_applied_at', 'magnitude_delta_if_applied'] |
| Complete | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach | Reach.fields | NOT_GENERIC | reported, not graded — width 9/13 built column(s) (69.2%) selected by 1 capability module(s); dark: ['chart_id', 'computed_at', 'derivation_ledger_jsonb', 'source_citation']; depth 100.0% (a capability query reads it with no literal row pin (upper bound)) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13): complete with no disposition and not derivable as probe-green (no probe receipt names this run) — unclassified |
| Earn | Earn.service_state | N/A (saved 2026-09-30: (absent in saved run)) | declared kind 'data' is not `service`; Earn.service_state is the service-state check (a service's rows_written cannot tell healthy-and-idle from broken) |

**PASS cells (compact):** Ldgr.source_presence, Idem.pattern, Vocab.identity, Build.registered, Build.contract, Build.target, Build.dag, Build.exercised, Build.count_integrity.

**Offline rollup** (main `asset_census.py` rollup rules at REGISTRY_REVISION 15 applied to the FRESH census; N/A reads NO_DETECTOR while `NA_RULE_DECISIONS` is empty; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.
Same rules over the SAVED 2026-09-30 census: Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

### 1.4 - Earned-signal (N.8), narration-fidelity (N.7) and honest-null audit of this asset's flags and verdicts

| field / claim | what it claims | what code path could make it read false | finding |
|---|---|---|---|
| `cleanliness_status = clean` | the anchor passed purification review | none beyond "no flag rows exist": an unassessable chart (n < 5, `ph_sodhana` G01) and a clean one are indistinguishable. The CHECK allows only `clean / flagged / staged_revision`, so "not assessed" is not expressible | **Unearned `clean`** (§N.7 item 6: absence of evidence read as evidence of cleanliness). ph_phaladesa narrates it as "passed clean sodhana review" |
| `staged_revision` | a correction is staged for native review | any major/critical flag; on the other chart 36 of 56 because of the superseded ceiling (ph_sodhana G02) | earned by its input; the input is the weak link |
| `confidence_delta_if_applied` | the confidence change if the correction were applied | regex `[\d.]+` over the first number in the expected-value text (`platform/python-sidecar/services/ph_suddha_sodhana/engine.py:106-125`), minus `observed` | parse of a prose string; fails silently to NULL on a format change (`except (ValueError, TypeError): pass`) |
| `magnitude_delta_if_applied` | "downgrade_magnitude_one_level" | unreachable (see live bullets) | dead column; NEVER populated |
| D43 rail (`revision_approved_by IS NULL`) | no correction is ever auto-applied | the writer inserts literal NULLs and asserts the engine record is None (a tautology: the engine sets None, `:64-65`); the SQL clause in the integrity check is the real detector | earned by the SQL clause; the writer-side assertion cannot fail |
| `rows_written` | rows inserted | `ON CONFLICT DO UPDATE` always affects one row, so the count is accurate (`:112`) | sound |

### 1.5 - UUID chart_id check (the bo_*/ph_* adapter defect)

`chart_id` appears only in psycopg parameters (`:41,49,71`), the `SuddhaContext` and an f-string `source_citation` (`engine.py:170`); the `json.dumps` sites (`:106-109`) serialise string ids from `str(row['sodhana_id'])` / `str(row['anchor_id'])` (`:127,138`). **Not present today.**

## 2 - Gaps: which are real, which are detector or definition gaps

Class vocabulary: **real** = a shortfall in code, rows, registry row or served surface; **real-stored** = the CURRENT code already fixes it but the stored rows predate the fix (cured by a rebuild, not by an edit); **design** = needs an SS or acharya decision; **detector** = the instrument is absent or its definition is the open point; **history** = a recorded past outcome no edit can change; **information** = Count/Cost/Complete/Reach, never a blocker; **opportunity** = beyond the requirement.

| gap id | gate | class | note (evidence) |
|---|---|---|---|
| ph_suddha_sodhana-G01 | Earn | real | `clean` = no flag rows, with no way to say "not assessed"; 4 of 4 clean on a chart where the chart-wide checks could not run (Q-L4-12) |
| ph_suddha_sodhana-G02 | Null | real | `magnitude_delta_if_applied` unreachable (`engine.py:145-146`); `mitigation_ref`-style dead column |
| ph_suddha_sodhana-G03 | Carr | design | Native approval storage: columns live in a table emptied per rebuild and forbidden non-NULL by the integrity SQL (D43 rail vs persistence) |
| ph_suddha_sodhana-G04 | Build | real-stored | Build record 139 vs live 4; floor 139 (consequences of the removed anchors) |
| ph_suddha_sodhana-G05 | Vocab | real | `_estimate_confidence_delta` parses a number out of English text (`engine.py:106-125`); a text change silently turns the delta NULL |
| ph_suddha_sodhana-G06 | Build | design | Overlap with `ph_sodhana`: the classification is a pure function of that table's severity counts (T2 6.5 asks for the investigation; Q-L4-12) |
| ph_suddha_sodhana-G07 | Null / Narr | detector | `prose_fields` undeclared: Null.* and Narr.* all NO_DETECTOR ("never read as no prose"); the table has `staged_revision_jsonb` text fields |
| ph_suddha_sodhana-G08 | Dens / Earn / Carr | detector | Dens.served FAIL; Earn, Carr, Vocab.alias NO_DETECTOR; Ldgr PASS (source_citation populated 4/4) |
| ph_suddha_sodhana-G09 | Build | history | Build.history PARTIAL: 0 errors, 9 aborts |

## 3 - Disposition

DISPOSITION: qualify

EVIDENCE_POINTER: 00_ARCHITECTURE/briefs/suvarna/layers/L4/assets/ph_suddha_sodhana_ELEVATION_BRIEF_v1_0.md (sections 1-4); receipts `_evidence/` (data/, upstream_receipts.json, rollup_L4.json, offline_checks.txt, rect_diag.txt); census `layers/census/census_L4.json` + fresh census `census_fresh/1e5781a/census_L4.json`

**qualify (Q) - fix the "clean" semantics and the approval-state design; consolidation with ph_sodhana is a question (Q-L4-12), not proposed.** Qualify (Q): the asset does what its name says mechanically and the D43 rail is enforced in SQL, but its only informative output ('clean') is currently an echo of an upstream silence, one column is unreachable, and the approval it exists to stage has no durable home. It is the clearest consolidation candidate in the layer on the evidence (its content is a function of `phala_sodhana` counts), proposed as a question rather than a disposition because `ph_phaladesa` and the `query_cleansed_anchors` capability read it by name.

Approver under Track A brief section 10: **Steward (G16)** for keep/qualify/enrich; **SS** for any output change (R5). No disposition is applied by this brief.

## 4 - Fix designs (one per real gap; anything marked `needs production rebuild` or `needs migration` is a REVIEW item for Strategic Suvarna)

### FD-1 - Add a "not assessed" disposition

- **Answers:** G01; CF-L4-03
- **Change:** Extend the CHECK to allow `not_assessed` and write it when `ph_sodhana` reports that its chart-wide checks did not run (coverage record from ph_sodhana FD-1) or when `phala_sodhana` has no rows for a chart whose anchor count is below the detector minimum; `ph_phaladesa` then narrates "N anchors not assessed" rather than "passed clean review".
- **Files / declaration / migration:** migration (`phala_suddha_sodhana_cleanliness_status_check`), `platform/python-sidecar/services/ph_suddha_sodhana/engine.py:72-80`, `platform/python-sidecar/pipeline/orchestrator/writers/ph_suddha_sodhana.py`
- **Failing-first test and mutation:** failing-first: with an empty `phala_sodhana` and 4 anchors the status is `not_assessed`; mutation: restore the zero-count rule -> `clean`
- **Output change:** yes - status values
- **Blast radius:** `ph_phaladesa` counts and narration; `query_cleansed_anchors`; the integrity SQL clause that recomputes the status must change in the same migration
- **Rebuild:** needs production rebuild
- **Gate it moves:** Earn
- **Fix class:** migration + writer code; **risk class:** R3; **buildable before J1:** tier-dependent: TG-L4-019
- **Decision:** OPEN - Q-L4-12

### FD-2 - Decide where a native approval lives

- **Answers:** G03
- **Change:** Option A: move approval state to a non-rebuilt table keyed by (chart_id, anchor identity) and join it at serve time; the D43 clause then checks that table. Option B: keep the columns but exclude them from the per-chart DELETE (UPSERT that preserves approval columns) and relax the integrity clause to "never set by the writer". Option C: state that approvals are an L5 action and drop the columns.
- **Files / declaration / migration:** migration; `platform/python-sidecar/pipeline/orchestrator/writers/ph_suddha_sodhana.py:56-57,89-101`
- **Failing-first test and mutation:** failing-first: an approval written between builds survives a rebuild (A/B); mutation: restore the delete -> approval lost
- **Output change:** structural
- **Blast radius:** D43 doctrine; ph_rectification has the same shape (`native_adopted`, `adopted_at` reset on every rebuild)
- **Rebuild:** none until chosen
- **Gate it moves:** Carr
- **Fix class:** migration + writer code; **risk class:** R4; **buildable before J1:** tier-dependent
- **Decision:** OPEN - Q-L4-12

### FD-3 - Make the magnitude and confidence deltas reachable or remove them

- **Answers:** G02, G05
- **Change:** Either stage a revision for `magnitude_drift` too (severity policy) or drop `magnitude_delta_if_applied`; replace the regex by a structured field (`expected_numeric`) on the flag's `derivation_ledger_jsonb` (ph_sodhana already writes `ceiling` and `observed` there, `engine.py:161`).
- **Files / declaration / migration:** `platform/python-sidecar/services/ph_suddha_sodhana/engine.py:106-146`; `services/ph_sodhana/engine.py:161`
- **Failing-first test and mutation:** failing-first: a confidence_inflation flag yields a delta from the ledger number, not from the text; mutation: change the English wording -> delta unchanged
- **Output change:** yes - delta values
- **Blast radius:** `query_cleansed_anchors`
- **Rebuild:** rides FD-1 of ph_sodhana
- **Gate it moves:** Null
- **Fix class:** writer code (engine); **risk class:** R2; **buildable before J1:** tier-independent
- **Decision:** no question; Steward

### FD-4 - Declarations

- **Answers:** G07, G08; CF-L4-10, CF-L4-11
- **Change:** Declare `prose_fields` (`staged_revision_jsonb` text keys) with `file:line` evidence and a `null_convention` for the NULL-by-rule columns.
- **Files / declaration / migration:** `asset_declarations.json`
- **Failing-first test and mutation:** failing-first: Null/Narr leave NO_DETECTOR; mutation: declare `[]` while the writer composes text -> Narr flags
- **Output change:** none
- **Blast radius:** census inputs
- **Rebuild:** none
- **Gate it moves:** Null, Narr
- **Fix class:** registry/declaration; **risk class:** R1; **buildable before J1:** tier-independent
- **Decision:** no question; Track E

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L4-01** - *this asset:* rebuild wave 9 (after `ph_sodhana`)
- **CF-L4-03** - *this asset:* the middle link of the silent-clean chain
- **CF-L4-09** - *this asset:* UUID: not present
- **CF-L4-10** - *this asset:* `prose_fields` undeclared
- **CF-L4-11** - *this asset:* Dens FAIL
- **CF-L4-12** - *this asset:* floor 139

## 5 - Semantic fingerprint contract (for the rebuild plan)

Natural key `(chart_id, anchor_id)` (UNIQUE `phala_suddha_sodhana_anchor_key`). Fingerprint over `(anchor_id, cleanliness_status, critical/major/minor_flag_count, flag_ids_jsonb)`; `entry_id` and `computed_at` excluded. Deterministic given the two upstream tables; it inherits every anchor-id change from `ph_nimitta`.

## 6 - Preserved kernel, carriage check, opportunities

- **Preserved kernel:** One row per anchor (tiling check in the SQL), the D43 rail in SQL, fail-loud flag read (F-16), `auto_apply: false` on every staged proposal.
- **Carriage check (T4 4.1; one only):** D3: recompute `cleanliness_status` from the severity counts (the registry SQL already does this); recompute counts from `phala_sodhana` for the chart. Deterministic, no ephemeris.
- **By design, stated and not flagged:** The D43 NO-AUTO-APPLY rail (no correction is applied without native sign-off) is stated, not flagged; `revision_approved_by` / `revision_applied_at` NULL on every row is the intended steady state.
- **Opportunities (never blocking):** surface `flag_ids_jsonb` joins in the capability; per-anchor reason text for `clean`.

## 7 - Decisions applied, questions for SS, Track I items arising

No decision has been applied: SS has not yet answered the A.L4 questions. This brief raises:

- **Q-L4-01** - Rebuild authority and order (see INDEX).
- **Q-L4-12** - Allow a `not_assessed` disposition; where does a native approval live; is this asset a view of `ph_sodhana`?

**Track I items arising (see INDEX section 8):** TI-L4-01, TI-L4-15, TI-L4-19, TI-L4-20, TI-L4-21.

