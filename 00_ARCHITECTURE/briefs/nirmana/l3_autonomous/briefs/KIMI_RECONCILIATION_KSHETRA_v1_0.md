---
artifact: KIMI_RECONCILIATION_KSHETRA
version: "1.0"
status: CURRENT
date: 2026-09-23
reviewer: Kimi K3, effort=max (KIMI_K3_REVIEW_KSHETRA_v1_0.md; packet KIMI_REVIEW_PACKET_KSHETRA_v1_0.md)
reconciled_by: the Kshetra brief session (madhav-d2)
method: every load-bearing reviewer claim re-verified at source on main @ c58e86662 before acceptance; verdicts ACCEPT / ACCEPT-MODIFIED / REJECT with the evidence line
applied_to: KSHETRA_ELEVATION_BRIEF_v1_0.md v4.2 · KSHETRA_ECOSYSTEM_ELEVATION_PLAN_v1_0.md v1.2 (the .2 revisions add the Gochara-session corrections — real vedha source chain; second COALESCE site)
does_not_authorize: any code, migration, build or doctrine
---

# Reconciliation of the Kimi K3 review — `ka_kshetra`

The review is high-quality: it found one defect above everything the author found, corrected three
factual errors in the documents, and sharpened five contracts. It also drew one consequence the
source does not support. Nothing below was accepted on the reviewer's word alone.

## 1. The top finding — G3, verified and RE-FRAMED

| | |
|---|---|
| **Reviewer claim** | `FieldEvaluator.terms_at` passes all obstructions unfiltered; `layer1.project_layer1` route-filters; `dhara_null` replicates use the unfiltered path ⇒ **the null is computed under a different model than the served field**, biasing `null_p` low. |
| **Verified** | `stage4_field.py:866-873` — `hazard.evaluate(... obstructions=self.envelopes.obstructions_at(t))`, no filter ✔. `layer1.py:140-160` — `suppressed_keys` filter from `routes[].suppressed_by` ✔. `dhara_null.py:159-163` — replicates via `evaluator.ln_lambda` ✔. **And one site the reviewer did not check:** `dhara_sweep.dhara_build_segments` (`:163`, called from `writer.py:2094-2095` to build the served analytic field) evaluates via **`evaluator.terms_at`** (`:43,55`) — the same unfiltered path. |
| **Verdict** | **ACCEPT the observation; REJECT the consequence.** The served field and its null are **both chart-wide and mutually consistent**; `null_p` is not biased by a field/null split. The route filter exists only in `layer1.project_layer1`, a projection (the Pūrṇa Layer-1 term matrix) that never writes `kala_field`. This is Pūrṇa's G3 exactly as originally stated: *the documented contract (SM-R-7 Option B) is not the live behaviour of the stored field.* |
| **Consequence for the author** | The brief's own claim — "suppression is route-scoped; structurally impossible for an unrelated obstruction to touch a class" — described a property the stored field does not have. **A §N.7 overclaim, corrected in v4.1.** Rank-0 defect stands (which semantics is the contract is the native's ruling; whichever is chosen, field ≡ null ≡ projection must be enforced by a byte-equality test before any `null_p` is served). |

## 2. The fourteen document defects (K-8)

| # | Finding | Verdict | Evidence / disposition |
|---|---|---|---|
| 1 | G3 omitted | **ACCEPT-MODIFIED** | §1 above. Rank 0. Consequence corrected. |
| 2 | "BPHS Ch.29" miscitation | **ACCEPT** | Corpus vol1:23168-23170: Chapter 29 = **Bhāva Padas**; no gochara chapter; 2 "gochara" mentions in vol1, 0 in vol2. The phrase is **inherited verbatim from FOUNDATION_SAFETY §5:207** — a W0 record defect propagated, not authored, here. Admitted chain — corrected after a Gochara-session check, verified here: **L0 `bg_transit_rules` (`rule_type='favourable' AND vedha_house IS NOT NULL`, `services/ka_vedha_gochara/writer.py:100-101`), co-cited Phaladīpikā Ch.26 — the "BPHS Ch.29" half of that co-citation is a miscitation in the L0 data and in `logic.py:13,105` (Gochara F-23/G-8, L0 owner strikes it); sarvatobhadra from `bg_sarvatobhadra_grid`, lattā from `bg_phaladeepika_latta`, the malefic scale from `bg_vedha_malefic_scale` (Phaladīpikā PG353, ADJUDICATION-11). There is **no `bg_phaladeepika_vedha` relation** — that is a writer *filename*; earlier versions had named it as a table**. The reviewer, like the author, took the writer *filename* for a relation. Routed to W0's owner and the L0 owner. |
| 3 | Lattā "needs corpus extraction" — stale and self-contradictory | **ACCEPT** | `bg_phaladeepika_latta` exists (migration 528; `PhaladeepikaLattaWriter`, PG338-339). `stage1_symbolization.py:357-362` comment is stale. E8 → admit at disclosed tier, `unqualified`. |
| 4 | Ablation under-operationalized | **ACCEPT** | Three arms (Sangam · Sangam+Taranga · +segments), several class/chapter pairs incl. an ordinary period, pre-registered rubric keyed to Q06's text, named judge. |
| 5 | A1 underclaimed — invariance is by construction | **ACCEPT** | λ⁰ is a constant multiplier of λ(t); every replicate scales identically; window bounds, maxima, `q_threshold` and duration buckets all scale by the same constant; `null_p` is a rank statistic ⇒ invariant to float64. Stated as "by construction; asserted on a fixture." |
| 6 | §7 item 7 duplicated fragment + hedge violation | **ACCEPT** | Fragment confirmed at plan lines 288-289 (a line-index insert artifact). Fixed; §N.5 hedge carried into the recommendation sentence. |
| 7 | Node (b) — where the mean derivation lands | **ACCEPT** | In the L0 ephemeris service, frame on the row beside `ayanamsha_id`; a Kshetra-side derivation would be a new §N.5 shadow — the same defect class as internal vedha/moorti. |
| 8 | `mi_bhara.py:403` violates the path convention | **ACCEPT** | Full path: `platform/python-sidecar/pipeline/orchestrator/writers/mi_bhara.py:403`. |
| 9 | "Pūrṇa P4" undefined, collides with Strategy §5 P4 | **ACCEPT** | Defined once: the PRIORS RESEARCH LANE of `PURNA_KSHETRA_PLAN_v1_1.md` §2 P4 — citation-backed, PRATINIDHI-ratified demographic sourcing per class, the 6 `ne_v01` rows as template. Renamed **"Pūrṇa priors lane (PK-P4)"** throughout. |
| 10 | Age-structure overclaim | **ACCEPT** | "Can carry age shape; cannot carry an age-shaped *level* independent of classical operands; absolute expected counts by age are distorted." |
| 11 | E2 lacks the both-shifted arm; P1 contract lacks tolerance/grid pins | **ACCEPT** | Three-arm null (transit / ladder / both), ladder-shift oracle; P1 contract pins `_EXCEEDANCE_REL_TOL = 1e-12` (`stage5_null.py:93`) and `range(1,R)`, δ = r·H/R. |
| 12 | U11 omits `weights_version`/`x_schema_version` | **ACCEPT** | Added. |
| 13 | Q07 proof overclaims "disappearance" | **ACCEPT** | Noisy-OR over K routes: bridge removal may attenuate. Proof row asserts disappearance or declares attenuation a failure of the proof, not the asset. |
| 14 | "Most disciplined in L3" — superlative without audit | **ACCEPT** | Replaced with the brief's own wording: "against VA §10.2, otherwise unusually clean." |

## 3. Other review content — verdicts

| Item | Verdict | Note |
|---|---|---|
| K-1 Q06 narrowed to continuous sub-threshold shape + driver decomposition; Sangam+Taranga as the stronger baseline | **ACCEPT** | The narrowing is right: "mechanism change" is what Sangam's witness list gestures at; "who brought the weather on the days no storm came" is what only the field has. |
| K-2 term-by-term; re-ranking (G3 → sign → varṣa → AV → interaction → vedha/moorti seam → λ⁰ shape → bhaṅga → sandhi → null → lattā) | **ACCEPT** | Adopted as plan §2's ranking, with #11 lattā corrected per K-8 #3. Sandhi ±3-day band: no corpus anchor — declared engineering band, never cited as doctrine. |
| K-2 (c) clock term blind to lord dignity at commencement (BPHS Vol 2 Ch. 47 vv 5-6) and to transits during antardaśā (Ch. 57 vv 24-27A) | **ACCEPT** | The strongest classical omission; enters as a *named covariate* (K-3 (i)), not by duplicating L2 dignity in the clock. Citations are the reviewer's corpus reads; marked [D-reviewer] until re-read by the author. |
| K-3 moorti split across term families (`stage1_symbolization.py:229-230` loha → `obstructive`) | **ACCEPT** | Verified: `polarity = "supportive" if tier<=2 else "obstructive" if tier==4 else "neutral"`. One moorti family with declared term placement on ingestion. |
| K-3 AV: bindu/rekha polarity inversion between corpus volumes; kakṣyā not in corpus | **ACCEPT** | Polarity reconciliation is a precondition for any β on the AV gate; same AV source as Sangam E2. |
| K-3 sade-sati as a named 7.5-year arc; KP Reader only | **ACCEPT** | Declared convention, not cited doctrine. |
| K-3 Kota — no corpus occurrence; Tājika — no admitted text | **ACCEPT** | Varṣa layer = source-admission-gated, upstream of Kshetra. |
| K-4 three-arm null; `q_threshold` is a detection screen not the bar; R=1024 ⇒ ~35.7-day shift step under-samples 1.5–3-day bands; enumeration is the oracle | **ACCEPT** | The grid-step point is new and important: narrow features are coarsely sampled in the null; the exhaustive enumeration settles it. |
| K-4 "null_p biased low by G3" | **REJECT** | §1: field and null are consistent. |
| K-5 6-class product; rank-only for shape-only; life-table λ⁰(t) legitimate as a tagged structural prior | **ACCEPT** | — |
| K-6 additions: class-set receipt; `kala_gochara_authority` owner + remove `'v1'` COALESCE; served rows carry `weights_version`/`x_schema_version`; standing detector on `null_resolution`; `mi_bhara` consumes the tag | **ACCEPT** | The COALESCE point is exactly Strategy §4 step 3's forbidden implicit fall-through. |
| K-6 rectification posterior never admissible prospectively; admissible only in a purpose-gated Q11 retrospective arm | **ACCEPT** | Sharper than the plan's wording; adopted. |
| K-7 keep the lossless segment store; compact substrate is for *serving projections* (P2 direct reader); never dedupe breakpoints | **ACCEPT** | Resolves Strategy §5's "complete materialization vs compact substrate" for this asset. |
| K-7 U10: refusal, not degraded bind | **ACCEPT** | — |
| K-9 counterfactual-self ("what the vighna costs") → Q04, from stored columns | **ACCEPT** | Adopted as the plan's E0 — first consumer-facing derivative, no model change. |
| Coherence: run the ablation before the S1-ingestion packet; S1 ingestion its own packet | **ACCEPT** | Ordering changed in plan §4. |

## 4. What the reconciliation changes in the two documents

**Brief v4.1:** §2.4 suppression claim corrected (route scoping is a projection property, not a
stored-field property — G3); §3 rank list gains rank 0 (G3); §4.1 ablation protocol (three arms,
rubric, judge); §4.6 P1 contract pins tolerance + grid; §4.7 U11 fields; §4.5 receives table —
vedha citation → L0 Phaladīpikā chain; §2.4 `mi_bhara` full path; "Pūrṇa P4" → PK-P4 defined;
Q07 proof row reworded.

**Plan v1.1:** §0 superlative removed; §1 gains "what the reviewer caught"; §2 re-ranked (G3 at 0,
sign at 1, lattā corrected to L0-present); §3 guarantees extended (K-6); §4 stage 3 split — ablation
before ingestion, S1 its own packet; §5 gains E0 (counterfactual-self, Q04) and the three-arm E2;
§6a vedha citation corrected + G3 row; §6a.1 node (b) placement in L0; §7 item 7 fragment fixed,
hedge carried; §7 gains the G3 semantics decision and the ablation-judge decision.

## 5. Not accepted, and why

Only one: the G3 *consequence* ("null biased low"). The reviewer checked three sites and inferred
the fourth; the fourth (`dhara_sweep.py:43,55`) goes through the same unfiltered path as the null.
The defect is real and ranks first; its shape is "contract ≠ behaviour," not "test ≠ subject."
