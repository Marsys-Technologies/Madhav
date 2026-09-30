---
artifact: NEAR_MISS_DOMAIN_PACKET
version: 1.0
status: RATIFIED_BY_OWNER_SURROGATE_PENDING_INDEPENDENT_DOMAIN_REVIEW
date: 2026-09-29
ruling: OSR-009 (answers OSR-001 / Addendum section 6 / section 11.2)
owner: purna-owner-surrogate
candidate_set_version: NMB-CAND-v1
eligibility_rule_version: NMB-ELIG-v1
schema_change: none
migration: none
install_path: 00_ARCHITECTURE/briefs/nirmana/purna_acceptance/NEAR_MISS_DOMAIN_PACKET_v1_0.md
note: Installed in purna_acceptance/ because edits to purna_anvesana/** are denied by the shared .claude/settings.json (L3 session posture, PR 2718). Move to purna_anvesana/ when that deny is lifted.
changelog:
  - 1.0 (2026-09-29): initial ratification from repository-sourced rules only. Independent domain review is a merge precondition; a review failure narrows the set, never widens it.
---

# Near-miss / formation-band domain packet v1.0

## 0. Principle
The band reports, for a closed list of wealth yogas, whether the chart satisfies the formation rule the repository already ships. It never authors a rule, tolerance, weight, or yoga. Present is decided only by L1 (`ga_yoga_firings`); L2 adds only the leg-level derivation of non-firings, with a ledger (B.1, B.3, N.5).

## 1. Source audit (origin/main cbded8e54)
- L0: `brahma_yoga_catalog` seeded by `platform/python-sidecar/brahmagyan/l0_yogas.py` (`YOGAS_CORE`, `DETECTOR_YOGAS`): `formation_rule_jsonb`, `formation_text`, `classical_citations`, `source_citation`.
- L1: `ga_writers/ga_yoga_writer.py` `_evaluate_yoga`, `_check_house_lord_association` (conjunction / exchange / mutual Parashari aspect of two distinct house lords), `YOGA_DETECTORS["dhana_yoga_house_lords"]`. It writes rows only for fired yogas and discards the failing leg (`return None`); `ga_yoga_firings` has never held a `fired=false` row.
- `ga_structural_writer._evaluate_catalog_rule` short-circuits at the first failing leg and returns only a reason string, so it cannot be the near-miss evaluator. The independent review's proposal to reuse it is corrected: reuse `ga_yoga_writer.ChartState`, `_lord_of_house`, `_house_of_planet`, `_check_house_lord_association`.
- L2: `bo_laksana` is `@register`, heavy, one substep per ayanamsha, `ctx.db_conn` never committed, delete-then-insert via `replace_prior_msr_for_chart` over `BO_LAKSANA_OWNED_SIGNAL_TYPE_CLASSES`, rows carry `build_id`. `bodha_msr_signals.fact_kind='absence'` is documented (migration 325, no CHECK) and never emitted. Fit confirmed; no migration, no contract change.
- Consumer: `register_d9_judgment.ts` hardcodes `notably_absent_yogas: not_computed` plus flag `notably_absent_not_checked`; `reading_checklist.ts` requires the unit; `WEALTH_READING_REQUIRED_ASSETS` lacks `bo_laksana`.
- PR #2705 (head 34991645b): 15 files, none a near-miss producer or consumer. Not merged, not a salvage base; regenerated snapshots are never transplanted. Salvage is the two worktree-only tests (section 7).

## 2. Closed candidate set NMB-CAND-v1
| canonical_id | L0 source | existing formation rule | near_miss-capable |
|---|---|---|---|
| dhana_yoga_house_lords | DETECTOR_YOGAS; BPHS Ch.41 | association of lords of h1 in {2,11} and h2 in {1,2,5,9,11}, h2 != h1, distinct lords, AND all placement houses non-dusthana (6/8/12) | yes (gate leg) |
| dhana_yoga_2_11 | YOGAS_CORE; BPHS Ch.41 | association of 2nd and 11th lords | no |
| dhana_yoga_5_9 | same | 5th and 9th lords | no |
| dhana_yoga_lagna_2 | same | lagna and 2nd lords | no |
| dhana_yoga_9_11 | same | 9th and 11th lords | no |
| dhana_yoga_2_5_9_11 | same | any pair among 2,5,9,11 lords | no |

Excluded (resumable only by a new packet version plus domain review):
- lakshmi_yoga: catalog leg "strong lagna lord" (no threshold) conflicts with the detector's Venus own/exalted leg; provenance conflict.
- chandra_mangala, guru_mangala, any row citing a text id with no chapter: no chapter-level provenance.
- pancha_mahapurusha rows: no wealth signification in catalog; would manufacture relevance.
- raja/viparita/nabhasa/other categories, Jaimini dhana rows: not category dhana, or not evaluable by ChartState.
- Any row the evaluators floor (`R6A2_FLOOR_REASONS`, `rule_shape_unimplemented`, `relation_unimplemented`).

## 3. Legs, tolerance, scope
- Mandatory legs: every leg in the rule text. Optional legs: none. Tolerance: none (no orb, percentage, one-sided-aspect relaxation, or `partial_formation_threshold`, which has no authoritative reader).
- near_miss exists only for dhana_yoga_house_lords: at least one lord pair is associated and the dusthana placement gate is its sole failing leg. "Association missing" is never near_miss (that would flag most pairs of every chart).
- Scope: D1 rashi, whole-sign houses from lagna, no Chandra/Surya frame, no varga, per canonical ayanamsha. Consumer serves the resolved ayanamsha and sets `ayanamsha_sensitive` if another ayanamsha's state differs.
- Inputs: L1 `chart_facts` via `ChartState`. Missing lagna/lord/house fact makes the pair unevaluable.

## 4. States (precedence per candidate x ayanamsha)
1. present: an L1 `ga_yoga_firings` row exists and the evaluator agrees. `bhanga_active` is carried as `l1_bhanga_active` ("formed, demoted"); state stays present.
2. indeterminate: any required input missing for any pair, or L1/evaluator disagreement (`l1_evaluator_disagreement`, logged, not build-fatal).
3. near_miss: no L1 firing, inputs complete, gate-only failure on at least one associated pair.
4. absent: no L1 firing, inputs complete, no near_miss condition.
Contradiction: if a sibling catalog dhana yoga is present on the same pair while the gated detector is near_miss, record `contradicting_present_siblings`; serve both and state the divergence. Cancellation applies only to formed yogas, never to a near_miss.

## 5. Producer (bo_laksana)
- New module `pipeline/orchestrator/writers/bo_laksana_yoga_band.py`: `build_yoga_band_signals(conn, chart_id, ayanamsha_id, build_id, now)` returns exactly six rows per ayanamsha, all four states represented, so completeness is provable.
- Row: `fact_kind='absence'`, `signal_type_class='yoga_formation_band'` (add to owned allowlist), `signal_type_id='yoga_formation_band:<id>'`, neutral valence, `computed_salience=0`, lowest tier, `constituent_facts_array` = consumed L1 fact_ids validated against `valid_fact_ids`, `classical_sources_jsonb` from catalog citations, `configuration_jsonb` = band/candidate/eligibility versions, candidate_id, state, reason, legs with fact_ids, pairs, l1_firing_ids, l1_bhanga_active, contradicting_present_siblings, scope.
- Insert after the navamsha block, excluded from or appended after ranking/normalisation/percentile/tier passes; SAVEPOINT-guarded; failure raises. Delete-then-insert through the class allowlist; UNIQUE key unchanged.
- Downstream isolation (mandatory): every reader of `bodha_msr_signals` excludes `fact_kind='absence'` unless it opts in; closed-allowlist source test prevents a new reader ingesting band rows.

## 6. Consumer
- `register_d9_judgment.ts` reads `yoga_formation_band` rows within `served_build_ids` for the resolved ayanamsha plus a fresh bo_laksana receipt.
- `served`: receipt resolves, six rows present (count = near_miss rows; `band_coverage` counts all four states). `empty_for_this_chart`: same but zero near_miss. `source_unproven`: no receipt, wrong generation, or under six rows. Never `not_computed`. Indeterminate rows are served as indeterminate.
- Array = near_miss rows only. Wording: "Not formed: <yoga> requires <rule>. The chart meets <legs>; it fails <leg>." Forbidden: has, gives, partial yoga, percentages, strength, effect, prediction. Retire `notably_absent_not_checked` when served.
- `reading_checklist.ts`: add `bo_laksana` to the wealth source fence via the existing served-generation mechanism. Update the tool description (~line 475); regenerate projections normally.

## 7. Tests (red then green)
Producer: present; near_miss (2nd/11th lords conjoin in 8th, no house_lords firing, `contradicting_present_siblings` contains dhana_yoga_2_11); absent; indeterminate (missing input); indeterminate (L1 disagreement). Negative controls: single-leg candidates never near_miss; same-lord pair never near_miss; bhanga_active firing stays present; exactly six ids emitted; no rank perturbation of other signals; all constituent fact_ids resolve; rerun idempotent and leaves `sudarshana_agreement` rows intact; allowlist contains the new class; reader-isolation test.
Consumer: keep and strengthen the two worktree tests (`/Users/Dev/.codex/worktrees/purna-wealth-near-miss/Madhav`, SHA-256 445b044d... contract regex tripwire, 31d2a8d0... integration `served` with count equal to array length) and add behavioural tests: near_miss served with forbidden-word check; empty_for_this_chart; source_unproven for no receipt / five rows / wrong generation; indeterminate surfaces; ayanamsha_sensitive; checklist fence includes bo_laksana.

## 8. Independent domain review (merge precondition)
- Reviewer A (`general-purpose`, independent Parashari acharya role, not the packet author) verifies via `search_classical_texts`/`read_classical_text` on BPHS Ch.41 and Ch.39: the lord-pair set, the dusthana gate, association modes, and that no candidate contradicts its chapter. If the dusthana gate cannot be sourced, near_miss is removed from v1 (present/absent/indeterminate only, `near_miss_capable_candidates: 0`); nothing widens.
- Reviewer B (`code-reviewer`): evaluator reuse, precedence, wording, generation fence, downstream isolation.
- `security-reviewer`: N/A (no auth/data-access change). `migration-guard`: N/A with a fresh census showing zero new migrations.

## 9. Files
`bo_laksana.py`; new `bo_laksana_yoga_band.py`; new tests under `writers/tests/`; readers of `bodha_msr_signals` per audit (incl. `L2_bodha/query_signals.ts`); `register_d9_judgment.ts`; `reading_checklist.ts`; their tests; regenerated projections. No change to `ga_yoga_writer.py`, orchestrator, migrations, IAM, or corpus.

## 10. Rebuild / generation
A production `bo_laksana` rebuild and its DAG dependents is implied (new rows, digest, receipt). Merge and deploy this before the single OSR-004 canonical rebuild so one rebuild covers L3, near-miss, builder changes. Served-generation identity changes only via that normal rebuild (new bo_laksana build id, wealth fence then requires its receipt); no SQL or manual build-state change. Until then the consumer returns `source_unproven`.
