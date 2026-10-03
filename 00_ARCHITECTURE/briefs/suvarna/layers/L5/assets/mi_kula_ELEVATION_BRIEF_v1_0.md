---
asset_id: mi_kula
layer: L5 Mīmāṃsā (mi_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna (lane track-a-l5)
produced_on: 2026-10-03
plan_item: A.L5 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION). Offline rollup under main REGISTRY_REVISION 16. Live registry, row counts, receipts and fact queries re-read 2026-10-03 (read-only)."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L5/L5_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)"
base_commit: "main adb0db29d"
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16)"
risk_class: "low (declaration and label work; the silent-fallback fix is writer code, no output change while the registry is readable)"
decisions_applied: "none for L5 yet (no L5 decision sheet answered). L0-L3 rulings are cited by analogy only where a brief says so, PROVISIONAL until J1"
track_i_items: [TI-L5-09, TI-L5-10, TI-L5-11]
ledger_gap_ids: ["mi_kula-Earn.build_record", "mi_kula-Cost.baseline", "mi_kula-Complete.depth", "mi_kula-Build.history", "mi_kula-Carr.detector", "new: kula-N1", "new: kula-N2", "new: kula-N3", "new: kula-N4", "new: kula-N5", "new: kula-N6", "new: kula-N7"]
---

# mi_kula — Signal-family registry and negative-control battery (global catalog)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository at `main adb0db29d`, the saved census, and read-only database queries (`suvarna_reader`, `default_transaction_read_only=on`, canonical chart 482012f1) named in the section they appear in (B.10); no figure here was invented. No SS ruling has been given on L5 yet: every disposition below is a proposal under Track A brief section 10, items marked (R) change outputs or define a verdict and are provisional until the J1 review, and every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa. L5 is sealed in STRUCTURAL mode by design (CLAUDE.md §E; empirical calibration values fill in as prediction-to-outcome data accrues): an empty or `prior_only` calibration value is not a defect here; a value that claims to be measured without evidence behind it is.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/mi_kula.py`, at `main adb0db29d`. Lower-case ids in backticks such as `le_basic`, `cal_retro`, `pred_window`, `gun_n` are query ids in `_evidence/facts.json` / `facts2.json` (each holds its SQL and the rows read on 2026-10-03).*

LIGHT, **global** writer (`run(ctx)`, :295). Seeds two catalogs from literals embedded in the file: `_FAMILIES` (11 evidence families: 9 `ON`, 2 `CONTROL_ONLY` null-control families) into `mimamsa_signal_families` and `_CONTROLS` (4 known-false controls: `neg_random_uniform`, `neg_shuffled_birth`, `neg_future_leak`, `neg_antiphase`) into `mimamsa_negative_controls`; deletes both tables whole and re-inserts (:312-313). The only computed part: each family's `prior_weight` is overridden from `brahma_class_priors` (version 1.0, signal_tradition `*`, fact_kind `*`) through `_FAMILY_TO_PRIOR_KEY` (:30-41, :335-337), falling back to the literal if that SELECT fails (:77, a logged warning). 15 rows (11 + 4); `mi_gunanaka`, `mi_pariksha`, `mi_bhavisya` (via the family key helper), `mi_adhilepa` and `mi_darshana` take family ids from it.

**Canonical chart state (read-only, 2026-10-03).** 11 families + 4 controls, rows_written 15 = live 15 (census Build.completion PASS). Deployed `prior_weight` equals the registry priors for all 9 ON families (fam_yoga 1.4, fam_msr_signal 1.4, fam_convergence 1.2, fam_dasha_period 1.15, fam_graha_natal 1.1, fam_ashtakavarga / fam_divisional / fam_transit / fam_anchor 0.95; `fam`, `priors`), i.e. the override works and the literal fallbacks are not in use. All 11 families carry `calibration_status = 'prior_only'`; 7 are `CLASSICAL_CITED`, 2 `MARSYS_DERIVED_CITED`, 2 `NEGATIVE_CONTROL`. `mimamsa_negative_controls.last_harness_score` / `last_harness_status` are NULL on 4/4 (no harness has ever written them).

| field | value | source |
|---|---|---|
| kind / scope / storage (live registry) | data / global / postgres_table | `asset_registry` (read-only SELECT, 2026-10-03) |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2885` | seed (live may differ by migration; differences listed in section 2) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/mi_kula.py:286` `@register("mi_kula")`; registry `has_writer` = t | writers dir / census `Build.registered` |
| target table(s) (live registry) | `mimamsa_signal_families`; count_sql tables: `mimamsa_signal_families`, `mimamsa_negative_controls` | registry / census |
| count_sql (live) | `SELECT   (SELECT count(*) FROM mimamsa_signal_families) +   (SELECT count(*) FROM mimamsa_negative_controls) AS count` | registry |
| live rows (canonical chart) / floor | 15 / 0 | count_sql run read-only ($1 = 482012f1); target_floor from registry |
| catalog_status / has_substeps / timeout | CURRENT / False / 10800s | registry |
| registry build state (canonical chart) | no throughput row for the canonical chart; recent canonical runs: complete 2026-09-06; complete 2026-09-06; complete 2026-07-27; complete 2026-07-14 | `asset_throughput`, `build_run_assets` (read-only) |
| depends_on (live) | `bg_rules`, `bg_class_priors` | registry (includes migration 1210 edges) |
| dependents (registry `depends_on`) | `mi_bhavisya`, `mi_darshana`, `mi_gunanaka`, `mi_pariksha` (registry); census transitive blocking radius 9 | registry (read-only `unnest(depends_on)`) |
| declared-vs-actual reads | Declared `bg_rules`, `bg_class_priors`. The writer reads the table `brahma_class_priors` (:60-66) — presumably `bg_class_priors`' target, not verified here — and never reads `bg_rules`; the 9 catalog `binding_spec` strings name sources (`chart_facts`, `chart_dashas`, `chart_divisionals`, `kala_gochara`, `kala_convergence`, `bodha_msr_signals`, `phala_anchors`) that this writer does not read and that no other code resolves (they are descriptions). | code reading of the writer and its services (grep; run 2026-10-03) |
| code readers / served surface | `query_signal_families.ts:9,96` (`marsys://tool/L5/query_signal_families`, also reads `mimamsa_negative_controls`), L5 writers `mi_gunanaka.py:118-123`, `mi_pariksha.py` ablation (`mi_pariksha.py:365`) and neg_control (`mi_pariksha.py:575`). Not exposed through any of the six named MCP tools except indirectly through `query_calibration` multipliers. Census Dens.served: 1 module declaring a density contract. | git grep over `platform/src`, `platform-mcp/src`, `platform/python-sidecar` (tests excluded) |
| tests that name it | `writers/tests/test_b04_mi_honesty.py` (source-text), `tests/l5/test_mimamsa_multiplier.py` (multiplier module, not this writer); no behavioural test of `mi_kula.run` was found | git ls-files + test-name read (not executed) |
| receipts / freshness / digest spec | `proven` global receipt (scope `__global__`) observed 2026-09-06T21:30:30Z with output digest and spec; freshness `fresh`; digest spec reviewed 2026-09-06T21:04Z; last run complete 2026-09-06 (no canonical-chart receipt applies: global) | `asset_provenance_receipts`, `asset_freshness`, `asset_output_digest_specs` (read-only) |
| Nirmāṇa freeze | not frozen; EGATE BLOCKED-ANCESTORS (6) (layer instance 1.1, 2026-09-30; not re-run here) | L5 layer instance section 0.3 |
| role / scoring mode | contribution (CEN `L5.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured by the current inspector (main is at REGISTRY_REVISION 16); the live registry and row counts in section 0 were re-read read-only on 2026-10-03.

`†` marks a criterion whose definition changed on main since the saved run: Build.dag rev 1 -> 2; Build.target rev 1 -> 2; Idem.pattern rev 1 -> 2; Dens.served rev 1 -> 5.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): mimamsa_negative_controls (mi_kula.py:312), mimamsa_signal_families (mi_kula.py:313) |
| Build | Build.target † | PASS | target_table=mimamsa_signal_families |
| Build | Build.dag † | PASS | 2 edge(s), all resolvable |
| Build | Build.count_integrity | PASS | count_sql=yes, integrity_check_sql=yes |
| Build | Build.completion | PASS | rows_written=15 = live=15 (count_sql total over 2 table(s): mimamsa_signal_families, mimamsa_negative_controls; global); target_table mimamsa_signal_families alone: 11 row(s), whole table — context, not the compared figure |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run a6111e46 complete/build (2026-09-06) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run a6111e46 complete/build (2026-09-06) |
| Count (information, D3) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=15) |
| Complete (information) | Complete.depth | PARTIAL | 11 rows, 20 cols; fully populated 16; NEVER populated ['data_source_pin', 'apply_point', 'interaction_value', 'interaction_status'] |
| Dens | Dens.served † | PASS | 1 module(s): query_signal_families.ts; declaring density_contract: 1 |
| Build | Build.history | PARTIAL | latest run complete, but 0 error(s) and 1 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only).  |
| Build | Build.dep_liveness | PASS | 2/2 declared dependencies lit at chart 482012f1 (or global) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |

**PASS cells (compact):** Build.registered, Build.contract, Vocab.identity, Build.exercised.

**Reported, not graded (NOT_GENERIC):** Reach.fields, Complete.width.

**Offline rollup** (main's `rollup_asset` rules, REGISTRY_REVISION 16, applied to the SAVED measurements; N/A reads NO_DETECTOR when no rule is declared; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L5/rollup_saved_L5.json`): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline Dens rev-4 static scan** (`capability_scan` + `_grade_dens` over the real source tree, no database; `offline_rollup_L5.py`): saved PASS -> PASS.



## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens verdict whose meaning changed at rev 4/5; **+ SS question** = the fix changes output or rests on a ruling. Ids beginning `new:` were found by reading code and data in this lane and are in no ledger.

**2.1 Ledger rows (inspector-emitted, all OPEN at 2026-09-27) and this lane's class for each**

| ledger gap id (`asset_gaps.jsonl` @ 2a78ec64d) | criterion | class | note |
|---|---|---|---|
| mi_kula-Earn.build_record | Earn.build_record | detector | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run a6111e46 com... |
| mi_kula-Cost.baseline | Cost.baseline | information | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run a6111e46 com... |
| mi_kula-Complete.depth | Complete.depth | information | measured: 11 rows, 20 cols; fully populated 16; NEVER populated ['data_source_pin', 'apply_point', 'interaction_value', 'interaction_status'] / req... |
| mi_kula-Build.history | Build.history | history | measured: latest run complete, but 0 error(s) and 1 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only).  / requir... |
| mi_kula-Carr.detector | Carr.detector | detector | measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim |

**2.2 Gaps found in this lane (code and read-only data)**

| gap id | gate | class | note |
|---|---|---|---|
| new: kula-N1 | Ldgr / Carr | detector | 7 families claim `evidence_tier = CLASSICAL_CITED` with `citation_refs` typed in the writer (e.g. "BPHS §3", "Saravali §4", "Phaladeepika §20"): none is verified at passage level, so under the SS citations rule (2026-10-01) each is `unsourced` until checked; Ldgr reads NO_DETECTOR and Carr.D1 (source correspondence) has no detector. The tier label asserts a verification the repository does not contain |
| new: kula-N2 | Vocab / design | real | `calibration_status = prior_only` is a literal in the catalog (never updated), while `mimamsa_multipliers.promotion_status` for `fam_graha_natal` and `fam_transit` reads `promoted` (see `mi_gunanaka`): two tables, two statuses for the same family, neither derived from the other (CF-L5-06) |
| new: kula-N3 | Build.dag | real | declared `bg_rules` unread; the actual prior source is read without an asset edge name verified (CF-L5-07) |
| new: kula-N4 | honest null | information | `last_harness_score` / `last_harness_status` NULL on 4/4 controls: correct, and consistent with `mi_pariksha` writing `not_implemented` for all 4 (no harness exists). The control `expected_score` is TEXT (`near_zero`, `chance`) with a numeric tolerance, so a harness has no numeric target to compare against |
| new: kula-N5 | idempotency | information | global delete-all-then-insert (:312-313) is correct for a catalog nothing references by foreign key (no FK to either table in the profiles); the family ids are referenced by value from `mimamsa_multipliers.target_ref`, `mimamsa_attribution.family_id`, `mi_bhavisya.driving_signals[].family_id` — a renamed family would orphan them silently |
| new: kula-N6 | Complete.depth | information | 4 columns never populated (`data_source_pin`, `apply_point`, `interaction_value`, `interaction_status`; census) |
| new: kula-N7 | prior provenance | detector | the numeric priors (1.4 for yoga and configuration, 0.7 for vastu/ashtakavarga-class, ...) come from `brahma_class_priors` v1.0; whether those numbers are classical, derived or engineering constants is the A.L0 `bg_class_priors` brief's question; here they are inputs with a stated source table |

**2.3 Earned-signal (§N.8) and narration-fidelity (§N.7) audit of this asset's flags, verdicts and numbers**

Question asked of each: what does the signal claim, and what code path would have to run and fail for it to read false? A calibration or status value with no outcome or detector behind it must be null, not a default.

| flag / value | what it claims | what actually produces it | reading |
|---|---|---|---|
| `prior_weight` | classical prior multiplier for the family | read from `brahma_class_priors` (:60-80), literal fallback if the SELECT fails | **earned** as a restatement of the registry value (deployed values equal registry values); the silent fallback to the literal on error (logged only) would not be |
| `evidence_tier = CLASSICAL_CITED` | the family rests on a cited classical source | a literal string in the catalog | **unearned label** until the citations are verified (kula-N1) |
| `calibration_status = prior_only` | the family has no empirical calibration | a literal | **true today and by design (STRUCTURAL mode)**, but a literal that cannot change: when a family earns calibration nothing updates it |
| `last_harness_*` NULL | no negative-control harness has run | never written | **earned null** |

**2.4 Honest-null cases (where the asset already tells the truth, and where it does not)**

- GOOD: harness columns left NULL; `prior_only` stated rather than a fabricated calibration.
- RISK: if `brahma_class_priors` is unreadable, `_load_registry_priors` returns {} and the catalog literals (e.g. fam_yoga 0.9, which differs from the registry 1.4) are written with only a log warning — a different number, silently (:77). The build does not fail.

**2.5 Known-defect checks requested by the lane brief**

- **UUID `chart_id` into `canonical_json` / `json.dumps` / `stable_uuid` (the ga_* and bo_* class):** Global asset: `ctx.config` carries no `chart_id`; the writer touches no chart id. No `json.dumps` of an id (the `json.dumps` calls at :98-279 serialise literal citation lists and a literal string 'shuffle_chart_id'). Not exposed to the UUID class.
- **Outcome-leakage guard:** Not applicable: the catalog contains no outcome data. The `neg_future_leak` control is a declared control name (`backdated_signal_post_event`), not an implemented detector (`mi_pariksha` writes `not_implemented`).
- **People-entered data (N-46) / LEL data contract:** Global catalog, regenerable; no people-entered data. The delete-all-and-reseed is safe for people data because no L5 people-entered table references it by foreign key.

## 3 · Disposition

**keep (P)** — a small deterministic catalog with the right honesty about its calibration status; the defects are unverified citations (a label claiming more than the repo holds), a literal status that cannot update, and a silent fallback path.

Approver under Track A brief section 10: **Steward (G16)**. Risk class: **low (declaration and label work; the silent-fallback fix is writer code, no output change while the registry is readable)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L5-023).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Label the citations honestly (R)

- **Answers:** kula-N1; CF-L5-14; citations rule
- **Change:** mark each `citation_refs` entry `unsourced` (or `sourced_ocr_unverified` where the A.L0 text index finds the passage) and make `evidence_tier` say `CLASSICAL_CITED` only for passage-verified refs; add a `ldgr_source`-style declaration
- **Files / declaration / migration:** `mi_kula.py:86-246` catalog; `asset_declarations.json`
- **Failing-first test and mutation:** failing-first: no family reads `CLASSICAL_CITED` unless its refs carry a verified state; mutation: flip a ref to unverified -> tier must change
- **Output change:** yes: `evidence_tier` text on up to 7 rows -> SS (R5)
- **Blast radius:** query_signal_families readers
- **Rebuild:** global rebuild (idempotent, no chart rows) — REVIEW
- **Gate it moves:** Ldgr, Carr
- **Fix class:** data (label) + writer code + declaration; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-09

### FD-2 · Fail loudly when the priors cannot be read

- **Answers:** kula-N3, risk bullet
- **Change:** raise instead of falling back to the literal weights (the literals disagree with the registry), or write the literal rows as `prior_weight` NULL-marked `fallback`
- **Files / declaration / migration:** `mi_kula.py:55-80,330-340`
- **Failing-first test and mutation:** failing-first: a missing `brahma_class_priors` table raises; mutation: restore the fallback -> FAIL
- **Output change:** none while the registry is readable
- **Blast radius:** this asset only
- **Rebuild:** none
- **Gate it moves:** Earn (honest failure)
- **Fix class:** writer code; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-10

### FD-3 · Derive family calibration status from the multipliers

- **Answers:** kula-N2
- **Change:** stop storing `calibration_status` as a literal: either drop it from the catalog or compute it from `mimamsa_multipliers` per chart at serve time
- **Files / declaration / migration:** `mi_kula.py` catalog; `query_signal_families.ts`
- **Failing-first test and mutation:** failing-first: a family with `promotion_status = promoted` is not served as `prior_only`; mutation: restore the literal -> FAIL
- **Output change:** served label changes for `fam_graha_natal`, `fam_transit` -> SS (R5)
- **Blast radius:** query_signal_families
- **Rebuild:** none
- **Gate it moves:** Vocab
- **Fix class:** writer code + served surface (TS); **buildable before J1:** tier-independent once SS rules (Q-L5-20)
- **Track I item:** TI-L5-11

### Landed or in flight (not designs of this lane)

No Track I I-item touches this asset (checked against the L5 layer instance and the L0-L3 INDEX files).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L5-04** — kula-N1/N2: labels without detectors
- **CF-L5-06** — status vocabulary across tables
- **CF-L5-07** — kula-N3
- **CF-L5-11** — global receipt present
- **CF-L5-12** — Earn/Cost instrument absent
- **CF-L5-14** — Ldgr / Carr declarations

## 5 · Semantic fingerprint contract (for E5.5)

Global; deterministic. Hash all columns except `created_at`, `updated_at`. The `prior_weight` column depends on `brahma_class_priors` v1.0: pin the prior version in the comparison.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** The 9 + 2 family ids and the 4 control ids (referenced by value downstream), the registry-sourced `prior_weight`, and the CONTROL_ONLY separation.
- **Carriage check chosen (T4 §4.1; one only):** D1 (source correspondence) applies to the 7 `CLASSICAL_CITED` families once their citations are verified at passage level; until then Carr reads NO_DETECTOR honestly. (L0 Q13 analogy, provisional.)
- **Opportunities (never blocking):** a harness for the four controls would turn `not_implemented` into a measured status; a numeric `expected_score` would give it a target.

## 7 · Decisions applied and open questions

No SS ruling exists for L5 at the time of writing. The L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A) and the L3 carry-over ruling (Q-L3-16) are the nearest precedent and are cited **by analogy only**; whether they carry to L5 is Q-L5-19 in the INDEX. Citations rule (SS, all layers, 2026-10-01): an OCR hit not checked against print is `sourced_ocr_unverified`; a passage not found is `unsourced`; only a citation verified at passage level counts toward Ldgr PASS.

Questions put to Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L5-04** — Constants: ratify as named documented approximations (in `brahma_formula_constants`) the engineering thresholds and weights (verdict 0.65 / 0.35, composite weights, bin width 0.1, n >= 5, k = 5, cap 3, n >= 3 promotion, discovery 3 / 0.15 / 20) — and drop (NULL) the invented priors and missing-term defaults (mi_sambandha channel priors and the 0.5 default, +-0.1 bands, 0.5 / 1.0 fallbacks)? *Recommendation:* Thresholds and weights: ratify as named constants (ask the L3 Q-L3-01 precedent: option 1). Invented priors, bands and defaults: option 2, NULL / `unsourced`. (R)
- **Q-L5-20** — Tier vocabulary (TG-L5-014): adopt `structural / prior_only / assignment_only / empirical` (the vocabulary `mi_darshana` already stores with a `grade_basis`) as the layer vocabulary, with a named detector for each tier and one meaning of "empirical" (chronology-clean, adjudicated, independent, n >= ratified minimum)? *Recommendation:* Yes. (R)
- **Q-L5-17** — depends_on corrections (Track I D-1 class): add `lel_events` to the three LEL readers; add / remove the edges listed in INDEX CF-L5-07 (including the unread `ph_pramana`, `ph_phaladesa`, `bg_ghatana`, `bg_rules`, `ka_kshetra`, `mi_pariksha` edges and the unread-declared reads of `phala_anchors`, `mimamsa_predictions`); move `_signal_family_key` out of `mi_adhilepa`. Accept the batch as one registry migration? *Recommendation:* Yes, as one reviewed batch; precedent Q-L3-08 (unread build-time edges are removed).
- **Q-L5-19** — Do the L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A by cause) and the L3 carry-over (Q-L3-16) carry to L5, provisionally until J1? Several L5 cells (Dens on platform-mcp readers, Build.history cascades, Carr N/A for user data) depend on it. *Recommendation:* Yes, by analogy, provisionally; with `user_data` and `ratified_judgment` as N/A causes for SS approval.
