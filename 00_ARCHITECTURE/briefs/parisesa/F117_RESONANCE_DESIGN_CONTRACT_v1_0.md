---
canonical_id: F117_RESONANCE_DESIGN_CONTRACT
version: 1.0
status: OPEN — awaiting native design ruling
author: PARIŚEṢA-V4 (GA-2 design authority)
date: 2026-08-21
finding: F-117 — bo_upaya resonance placeholder terms
scope: platform/python-sidecar/pipeline/orchestrator/writers/bo_upaya.py
       platform/python-sidecar/bodha_writers/formulas.py (resonance_score_v1)
       00_ARCHITECTURE/A13_RM_SPEC_v1_0.md §3
---

# F-117 — bo_upaya resonance: what was repaired, and what still needs a ruling

## §0 — The finding

`bo_upaya`'s per-graha remedy ranking (`bodha_rm_resonances`) computes
`resonance_score_v1` = `weakness_score` × three multiplicative "burden" terms.
PARIŚEṢA-V4 observed on the native chart (`482012f1`) that all three burden terms
were CONSTANT across every graha, leaving `weakness_score` — itself dominated by
inverse ṣaḍbala at 30% weight — as the only varying input. The remedy priority
ranking was therefore an inverse-ṣaḍbala restatement wearing three decorative
multipliers, and `weakest_rank_in_chart` #1 carried the label `critical` at a
`resonance_score` of 0.173 on a 0..1 scale.

## §1 — Root cause, per term (three DIFFERENT causes)

| term | pre-F-117 state | root cause | live evidence (482012f1/krishnamurti) |
|---|---|---|---|
| `motif_burden` | 0.4 for all 9 grahas | **Implemented, but structurally incapable of varying.** Read `1 − MIN(motif_strength)`; `bo_cgm_motifs` writes `motif_strength` as a fixed per-motif-CLASS constant. | 600 motifs, exactly 2 distinct strengths (mutual_aspect = 0.6 ×180, mutual_aspect_triangle = 0.75 ×420). Every graha joins ≥1 mutual_aspect ⇒ `1 − 0.6 = 0.4`, always. |
| `domain_burden` | 0.0 for all 9 grahas | **Genuinely unimplemented** — hardcoded `0.0` with an accurate B.10 note that `bodha_cdlm_cells.weakest_constituent_graha_jsonb` is a dead column. That note has since been overtaken by CR-67. | CR-67's `_fetch_graha_cdlm_cells` (already in this same writer) returns real cells: Sun 26, Saturn 10, Jupiter 9, Rahu/Ketu 5, Mars 3, Moon 1. |
| `contradiction_factor` | 0.0 for 8 of 9 grahas (Mars 0.1) | **Implemented, wired to the WRONG input.** Fed dosha counts — the fact A13 §3 already spends `affliction_count_normalized` on, so one fact was counted twice under two names. The spec's designated source is unpopulated upstream. | 0 of 10,040 `bodha_msr_signals` rows carry a non-empty `contradicts_signals_array`; `bo_laksana` has no code path that writes it. |

Note for the record: the finding's "0 for EVERY graha" on `contradiction_factor`
is very slightly overstated — Mars carries 0.1 (one Manglik Dosha). The
substance of the finding stands; the number is corrected here for accuracy.

## §2 — What this PR REPAIRED (implemented, tested)

All three repairs implement **A13 §3's own stated definitions**, which the
implementation had drifted from. No new grounding was invented; "weakest" is
decided everywhere by the L1-authoritative ṣaḍbala ratio (§N.5 — referenced,
never recomputed).

1. **`motif_burden`** → share of a graha's CGM motif memberships in which it is
   the weakest participating node. Spec text: `normalized(sum(cgm_motifs_with_graha_as_weakest_node))`.
   Live result: 8 distinct values across 9 grahas, 0.00 → 1.00 (was: 0.4 ×9).
2. **`domain_burden`** → share of the CDLM cross-domain cells a graha materially
   constitutes in which it is the weakest constituent. Spec text:
   `normalized(sum(cdlm_weakest_constituent_count))`. Live result: Mars 1.00,
   Moon 1.00, Jupiter 0.89, Sun 0.65, Saturn 0.10, Rahu/Ketu 0.00 (was: 0.0 ×9).
3. **`contradiction_factor`** → read from `contradicts_signals_array` (the spec's
   own source), with a **real availability detector**. When the upstream column
   is empty chart-wide the column is written **NULL** ("not measured") rather
   than a `0.0` no reader could tell apart from a measured "no contradictions",
   and the formula uses the neutral 1.0 multiplier. Dosha counts are **not**
   substituted — the double-count is removed, not relocated.
4. **`sha=1.00` narration** (§N.7 item 1) → `citation_human` printed the
   missing-data NEUTRAL FALLBACK as if it were a measurement, and 1.00 reads as
   the strongest possible ratio for the two grahas the measure does not apply to.
   Now prints `sha=n/a (no classical shadbala for this graha)`, with
   `ephemeris_audit_jsonb.strength_basis` recording which case applies.
5. **A regression detector** (§N.8) → the pre-existing degeneracy guard could not
   have caught F-117: `resonance_score` DID vary; its *inputs* did not. A new
   per-term guard warns when any burden term is identical across all grahas, and
   can genuinely read either way (it exempts `contradiction_factor` only in the
   exact case its own availability flag says the source is unpopulated).

## §3 — OPEN: items requiring a native design ruling (NOT implemented)

### D-1 — Rahu/Ketu have no strength basis, yet are ranked on one

Classical ṣaḍbala defines no requirement for the nodes; `ga_strength_writer`
correctly excludes them. `bo_upaya` substitutes the neutral 1.0 so the
`(1 − ṣaḍbala) × 0.30` and `(1 − bhāva-bala) × 0.15` terms contribute zero for
them. **The nodes are therefore scored on 55% of the weight basis the seven
classical grahas are scored on, and then ranked against them as if commensurable.**
On the native chart this places Ketu #3 and Rahu #4 of 9.

Options:
- **(a) Dispositor-inherited strength** *(recommended)*. BPHS holds that the
  nodes deliver the results of their dispositor and of grahas they associate
  with. Substituting the dispositor's ṣaḍbala ratio for the node's own gives the
  nodes a real, classically-defensible position on the same scale — restoring
  commensurability without inventing a number. Requires: naming the exact rule
  (dispositor only, or min(dispositor, closest conjunct)?) and a citation.
- **(b) Rank the nodes in a separate register** — a node track alongside the
  seven-graha track, never interleaved. Most conservative; changes the served
  shape.
- **(c) Status quo + disclosure only** — keep the neutral fallback, surface
  `strength_basis` (this PR already does this) and let readers decide.

Each option changes the served rank order for the native chart. Not taken
unilaterally.

### D-2 — `remedy_priority_class`: vocabulary drift + no absolute anchor

Two separable problems:
- **Vocabulary.** A13 §3's schema specifies `'urgent' | 'recommended' | 'optional'`
  — three levels. The implementation emits `'critical' | 'high' | 'medium' | 'low'`
  — four. A spec/implementation registry disagreement (GA.1 class). Changing it
  is a serving contract change (`query_remedies.ts`, generated MCP projections).
- **Absoluteness.** The class is assigned by rank thirds, so rank #1 receives the
  top label for *every chart ever built*, however mild — §N.8: no code path
  exists that could make `critical` read false. The rank-relative FRAME is
  correct and native-referenced (MC-025a) — remedying the relatively weakest
  graha is classical practice. The WORD is the problem.
  Options: (a) adopt the spec's softer vocabulary; (b) keep four levels but gate
  the top class behind an absolute `weakness_score` floor — needs calibration
  evidence this repair does not have; (c) disclosure only.
  This PR implements (c) as a floor: `ephemeris_audit_jsonb.priority_class_basis`
  now states the rank-relative frame explicitly.

### D-3 — Upstream: `bo_laksana` must populate `contradicts_signals_array`

`contradiction_factor` cannot be a measurement until it does. This is a
`bo_laksana` work item, out of scope for a `bo_upaya` repair; the honest NULL is
correct in the meantime, not a permanent answer.

### D-4 — Residual ṣaḍbala collinearity in `motif_burden` (honest disclosure)

The repaired `motif_burden` is no longer constant, but on the native chart it
correlates strongly with ṣaḍbala rank (Venus, the ṣaḍbala-weakest, is the weak
member of all 36 of its motifs). **This PR therefore does NOT claim to have
decoupled the ranking from inverse ṣaḍbala.** The cause is upstream motif
topology: `bo_cgm_motifs` currently emits only a near-uniform mutual-aspect
graph (every graha in exactly 36 motifs) because its stellium and
parivartana_chain detectors are Tier-3-blocked on missing `bo_karanajala`
dispositor edges. With a varied motif set the term separates on structure rather
than strength. `domain_burden` is already genuinely independent (Sun is the
ṣaḍbala-STRONGEST yet carries 0.65 domain burden; Saturn carries 0.10) — that
term does add real information today.

## §4 — Data rebuild required (NOT executed here)

Every change above is a **write-path** change. The already-computed
`bodha_rm_resonances` rows for the native chart still carry the old constants
until `bo_upaya` is re-run. Per session discipline this PR is **code only** — no
production rebuild was executed. Required to realise the fix:

- Re-run `bo_upaya` for each chart × ayanamsha (delete-then-insert per §N.3, so
  the rebuild REPLACES rather than accretes).
- Downstream readers of `bodha_rm_resonances` should be re-checked for a NULL
  `contradiction_factor` (previously always non-NULL):
  `query_remedies.ts`, `query_rm_resonances.ts`. Both pass the value through
  untransformed, so NULL propagates honestly; no arithmetic is performed on it
  in the serving layer.
