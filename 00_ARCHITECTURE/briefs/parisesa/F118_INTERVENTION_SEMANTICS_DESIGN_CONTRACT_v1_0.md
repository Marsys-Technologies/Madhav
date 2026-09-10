---
canonical_id: F118_INTERVENTION_SEMANTICS_DESIGN_CONTRACT
version: 1.0
status: CURRENT
campaign: PARIŚEṢA-V4
finding: F-118
class: CL-09 (earned-signal violations — flag/grade with no detector, or a detector on a proxy)
authored: 2026-08-21
authored_by: PARIŚEṢA-V4 repair lane (GA-2 design authority)
execution_status: NOT EXECUTED — design contract only; the dedup/actionability half shipped separately
supersedes: none
---

# F-118 — intervention semantics: what shipped, and the per-row efficacy/feasibility
# detector that did not

## §1 — What this document is

F-118 named two defects in `kala_upaya_get`'s intervention slate. One is a serving-honesty
defect with a mechanical fix; the other is a from-scratch modelling question. This document
exists so the second is not smuggled into a code-repair PR as if it were the first.

| Half | Defect | Disposition |
|---|---|---|
| **A — duplicate/actionability** | 100 served "interventions" were 14 distinct labels; half the slate was a severity classification with no act in it | **SHIPPED** — see §3 |
| **B — efficacy/feasibility grading** | every row graded identically; no detector behind the grade | **DEFERRED to this contract** — see §4 |

Half A is shipped because it is a claim-correction: the rows were always what they were, the
response merely mis-stated how many distinct things they amounted to and what they were for.
Half B is deferred because it requires deciding, from the classical corpus and from calibration
data that does not yet exist, *what would make one attested remedy more efficacious than another
for this native, at this time*. That is a Jyotiṣa modelling decision, not a serving decision, and
authoring it inside a repair PR would be exactly the fabrication B.10 forbids.

## §2 — The measured facts (production, 2026-08-21, chart `482012f1-710e-4a25-994a-93821f5871aa`)

Reproducer: `kala_upaya_get(chart_id=482012f1-…, domain='relationship', as_of_date='2026-08-15')`.

Served: `intervention_count = 100`, over **14 distinct labels**.

**Source-side measurement (read-only SQL against production):**

| Surface | Rows/chart | Distinct served content | The duplicating axis |
|---|---|---|---|
| `phala_mitigation` | 536 | **4** `(intensity_tier, afflicting_graha, proportionality_basis)` combinations | one row per *obstruction* (`obstruction_id`, own `window_start`/`window_end`), but nothing in the served fields varies with it |
| `bodha_rm_remedy_prescriptions` | 135 | **27** remedies | `ayanamsha_id` — the identical remedy is stored once per each of the 5 ayanamshas |

**The `phala_mitigation` content finding (the more serious of the two).** Every one of the 536
rows carries:

```
program_jsonb           = {"scheduled_ids": [], "sequence_basis": "…", "total_scheduled": 0}
tradition_options_jsonb = {"vastu": [], "vedic": [], "modern": [], "tantra": [], "ayurvedic": [], "lal_kitab": []}
recommended_tier_jsonb  = {"free": [], "low_cost": [], "high_investment": []}
```

There is **no remedy in the row at all**. The label the tool served —
`'light — for saturn — severity=medium × anchor_magnitude=minor → light'` — was composed from
`intensity_tier` + `afflicting_graha` + `proportionality_basis`, i.e. from the row's *severity
classification*, because that is the only text the row has. Half the slate was a grade wearing a
remedy's clothes.

**The grading finding.** All 100 rows carried `efficacy_tier='classically_attested'` and
`targets_link='promise'`; `feasibility` was `null` on the 50 `phala_mitigation` rows and `0.9` on
all 50 `bodha_rm` rows. The tier is assigned by `assignEfficacyTier({hasCitation, isLiveSurface})`
— citation-PRESENCE only — and both surfaces carry a blanket citation constant on every row
(`'Brihat Parashara Hora Shastra — Upaya chapter'` / `'G27 remedy … for …'`). So the detector
behind the grade measures "does this table have a citation column populated", not "is this remedy
efficacious". §N.8, exactly: a signal computed by a detector that measures a proxy rather than
the claim it asserts.

## §3 — Half A, SHIPPED (PR `parisesa/repair-F118-intervention-dedup`)

Four changes, all inside Lane U's two owned files (`platform-mcp/src/lib/kala_upaya_diagnosis.ts`,
`platform-mcp/src/tools/kala_views/upaya.ts`) — the orchestrator is untouched, ruling U-1 holds,
no fourth remedy store, no recomputed ranking:

1. **`dedupeInterventions`** — rows whose *served content* is byte-identical collapse into one row
   carrying `duplicate_row_count` (never capped) and `duplicate_source_pks` (capped at 10, so every
   collapsed row stays reachable per §N.5) plus an honest `duplicate_note`. The note deliberately
   does **not** name a varying axis it has not measured.
2. **`actionable_prescription` + `splitPrescriptive`** — a new per-row field, `null` exactly when
   the row names no act. `extractPhalaMitigationPrescription` is the detector: it reads the three
   remedy-payload columns the serving layer already selected and previously ignored, and returns
   `null` when they are empty rather than falling back to the severity label. Non-prescriptive rows
   are served in `non_prescriptive_rows` with their own count and note (§N.6 density split, same
   shape as the pre-existing cited/uncited split) — never dropped (B.10), never inside
   `interventions`.
3. **The ayanamsha budget pin** — `bodha_rm_prescriptions_get` is called with
   `ayanamsha_id='lahiri_chitrapaksha'`, so the 50-row page holds 50 *distinct* remedies instead of
   10 remedies × 5 identical copies. It is a budget fix, not a filter: a chart with no rows on that
   ayanamsha is re-read unfiltered, and the collapse then does the whole job.
4. **`efficacy_discrimination`** — the honest disclosure of Half B. It measures whether this
   response's grading fields took more than one value at all and says so in the response. It does
   **not** fix the grading. `targets_link` is reported but never counted toward `discriminating`,
   because it is uniform by construction (every row routes to the one diagnosed failing link) and
   counting it would make the detector read green for a reason unrelated to the grade.

Post-fix on the reproducer's row shape: `intervention_count` = the number of distinct actionable
remedies, `source_rows_considered` and `duplicate_rows_collapsed` disclose the raw figures, and the
severity-classification row appears once, in `non_prescriptive_rows`, stating that it stands for 50
source rows.

## §4 — Half B, the DEFERRED contract: a genuine per-row efficacy/feasibility detector

### §4.1 The requirement

A per-row score that **discriminates between attested remedies on chart-specific signal**, such
that `assessEfficacyDiscrimination(...).discriminating` becomes `true` for a real reason, not by
construction. Any design that satisfies this must answer all five questions below. A design that
answers fewer is not ready to build.

### §4.2 The five questions a design must answer

**Q1 — What is the score OF?** Three different quantities are currently conflated under
"efficacy":
  - *attestation strength* — how well-attested the rite is in the corpus (what `efficacy_tier`
    gestures at today, badly);
  - *targeting fit* — how well this remedy addresses THIS chart's diagnosed failing link and
    afflicting graha (`resonance_match_score` and `targets_motif_id`/`targets_cell_id` on
    `bodha_rm_remedy_prescriptions` are candidate substrate, currently unread by Lane U);
  - *feasibility* — whether the native can actually perform it (`feasibility_score`,
    `estimated_cost_inr_range_jsonb`, `estimated_time_minutes_daily`, `ritual_complexity_class`,
    `requires_acharya_review_flag` all exist on the same table and are all currently unread).
  These are three axes, not one number. The design must state whether it serves three fields or
  one composite, and if composite, why collapsing them is not itself an information-destroying
  move of the kind this finding is about.

**Q2 — What is the DETECTOR, and what makes it read low?** Per §N.8, for each proposed field:
name the specific code path that would have to run and fail for the field to correctly report a
*poor* score. A field whose worst realistic value is "good" is not implemented. Note that
`feasibility_score = 0.9` on every bodha_rm row today is precisely this failure — the column
exists, is read, and is constant.

**Q3 — Where does the authority live?** §N.5: an L2+ signal never restates an L1/L2 computed
value as its own truth. If targeting fit is `resonance_match_score`, Lane U REFERENCES it — it
does not recompute it, does not renormalise it, does not blend it into an unattributable
composite. If no existing column carries the quantity, the honest answer is that the quantity does
not exist yet and the field is `null`, not that Lane U should compute it (that would be the fourth
remedy store ruling U-1 forbids).

**Q4 — What is the calibration story?** `efficacy_report` is `honest_empty` today for a stated
reason: `mimamsa_intervention_ledger` has no MCP read path and no resolved outcomes. Any
*empirical* efficacy claim is blocked on that ledger accumulating real adoption→outcome pairs
(LAW ZERO, `KALA_SUPREME_ELEVATION_v1_0.md` §13). The design must state which of its proposed
fields are structural (computable today from the chart) and which are empirical (blocked on
calibration), and must never let an empirical-shaped field default to a structural value.

**Q5 — Does the phala_mitigation surface get repaired, or retired from this slate?** The deeper
finding of §2 is that `ph_pratikara` writes 536 rows/chart with an empty remedy program. Either
(a) the L4 writer is meant to populate `program_jsonb`/`tradition_options_jsonb` and does not —
an L4 build defect that belongs to a Phala lane, not to Lane U; or (b) the rows are severity
bookkeeping never intended as prescriptions, in which case `kala_upaya_get` should stop reading
that surface for `interventions` entirely and the §3 non-prescriptive bucket is a transitional
measure, not the end state. **This question is not answerable from Lane U's files** and is the
single highest-value follow-up in this finding. It is flagged here for the Conductor rather than
silently worked around.

### §4.3 Explicit non-goals

- **No LLM-generated remedy text, ever.** `feedback-deterministic-first-for-data-build`: generative
  curation is not permitted. A remedy that is not in the corpus is not served.
- **No re-ranking of the source surfaces' own ORDER BY.** Ruling U-1.
- **No synthesised rite.** `speculative_extension` remains a serving label on a real row, never a
  licence to invent one.
- **No composite score that cannot be decomposed back to its cited inputs** (B.3 derivation-ledger
  mandate).

### §4.4 Acceptance gate for the eventual Half-B PR

1. `assessEfficacyDiscrimination` reports `discriminating: true` on the live canonical chart's
   `relationship` slate — for a reason the PR can name, not because a new field happens to vary.
2. A test exists per new field that makes that field read POORLY, and it fails if the detector is
   stubbed out (§N.8's own standard, and the standard the §3 tests already meet).
3. Every scored field traces to a cited source column or is `null` (§N.5, B.3).
4. Q5 is answered in writing, by the layer that owns `phala_mitigation`.

## §5 — Provenance

- Finding: PARIŚEṢA-V4 baseline `F-118`, class CL-09, evidence
  `evidence/E2_q4_raw_kala_upaya.json` @ `aa0227abc3749c104e27e17f3f6edf28184741ac`.
- Live re-reproduction 2026-08-21: `intervention_count=100`, 14 distinct labels, 50 byte-identical
  `phala_mitigation` rows — the finding was still fully live at repair time.
- Source measurements in §2 are read-only SQL against production; no chart data was written by the
  repair lane.
- Doctrine: CLAUDE.md §N.5 (L1/L2 authority), §N.6 (serving density), §N.7 item 6 (an honest null
  beats an invented judgment), §N.8 (earned signal); B.10 (no fabricated computation).
