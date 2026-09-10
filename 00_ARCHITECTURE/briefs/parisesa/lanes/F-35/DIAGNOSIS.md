---
lane: F-35
stream: S3_SATYA
stage: D (DIAGNOSE) — COMPLETE
author: SATYA sub-agent (sonnet), Stage-D DIAGNOSIS-INCOMPLETE closure pass
---

# F-35 — mimamsa_insight_get mixes structural + "empirical" insight units with no
population-vs-per-chart disambiguator, and the "empirical" grade itself is weaker
than it presents

## 1. Live reproduction (today, 2026-08-16, verified)

`mimamsa_insight_get(chart_id=1c826d5a-41cb-4450-b4dc-59d440e5f75a, domain='career')`

Raw envelope saved: `raw_reproduce.json` (this dir). Salient fields from
`content.insight_units[]`:

- 5 `verdict_object` rows (`verdict_business_launch`, `verdict_career_change`,
  `verdict_career_setback`, `verdict_career_entry`, `verdict_career_advancement`),
  all `evidence_grade: "structural"`, all `last_calibrated_at: null`.
- 1 `manifestation_grammar` row: `insight_id: "gram_career_ch_career_verbal_2"`,
  `evidence_grade: "empirical"`, `last_calibrated_at: "2026-08-12
  17:12:31.519631+00"` (a real timestamp), `n_support: 9`, `rank_consequence: 0`,
  statement: *"For career events, the 'ch_career_verbal' channel fires with 0%
  propensity (n=9, empirical learning)."*
- `content.calibration_summary` for this chart: `{"total_matches": 0, "confirmed":
  "0", "partial": "0", "denied": "0", "mean_composite_score": null}`.

**CONFIRMED REPRODUCES** — a `structural` and an `empirical` grade genuinely sit
side by side in one `insight_units[]` array with no field disambiguating what
"empirical" is empirical *about*. Not ALREADY-FIXED. The `calibration_summary`
total_matches=0 fact turns out to be the load-bearing clue for §3 below.

## 2. Claim decomposition

- **C1** — the response mixes chart-specific structural-tier insights with at
  least one `evidence_grade='empirical'` manifestation-grammar insight carrying a
  real `last_calibrated_at`, in the same undifferentiated `insight_units[]` array.
- **C2** — no inline marker disambiguates the "empirical" grade from the chart's
  own structural-tier grades, so a caller filtering on `evidence_grade` alone could
  momentarily conflate the two.
- **C3 (the corpus's causal claim for why C1/C2 matter)** — that the "empirical"
  grade "reflects population-level cross-chart mining rather than this chart's own
  outcome history."

## 3. Mechanism (file:line, read directly — corrects the audit's causal claim,
not just its pin)

**C1/C2 are confirmed as coded.** The serving file is
`platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insights.ts`
(`marsys://tool/L5/query_insights`, bound to the `mimamsa_insight_get` MCP tool —
confirmed by matching the live envelope's `filters`/`total_returned`/
`calibration_summary` shape against this file). Its SQL (lines 102–112):

```ts
const sql = `
  SELECT insight_id, insight_type, domain, horizon, question_lens,
         statement, rank_consequence, confidence_band, n_support,
         leakage_status, evidence_grade, freshness_lel_version,
         last_calibrated_at, provenance_chain, is_negative_knowledge,
         surface_formula_version, updated_at
  FROM mimamsa_insight_units
  WHERE ${filters.join(' AND ')}
  ORDER BY rank_consequence DESC NULLS LAST
  LIMIT $${p}
`
```

Every row of `mimamsa_insight_units` — regardless of `insight_type` — is
projected through this one column list and returned in one `insight_units[]`
array (line 137: `insight_units: insightResult.rows`). There is no
population-level / provenance-scope column in the SELECT list, and no
post-processing that separates or annotates rows by what kind of "empirical"
they are. `insight_type` (`verdict_object` vs `manifestation_grammar`) is the
only other differentiator returned, and nothing in the schema or the handler
documents that a caller must cross-reference `insight_type` against
`evidence_grade` to avoid over-trusting an "empirical" row. **C1 and C2 confirmed
exactly as claimed.**

**C3 is FALSE as stated in the corpus, and the real mechanism is a different (and
arguably more serious) defect.** Tracing the write path:

- `platform/python-sidecar/pipeline/orchestrator/writers/mi_darshana.py` line 12:
  the writer's own module docstring states `PER-CHART scope` for
  `mimamsa_insight_units`. Its manifestation-grammar block (lines 145–190) reads:

  ```python
  cur.execute(
      "SELECT channel_id, domain, channel_propensity, prior_propensity, "
      "       n_support, evidence_grade "
      "FROM mimamsa_manifestation_grammar WHERE chart_id = %s "
      "AND evidence_grade = 'empirical' ORDER BY n_support DESC LIMIT 20",
      (chart_id,),
  )
  ```
  (lines 149–151) — scoped by `chart_id`, not pooled across charts. There is no
  cross-chart join, no population table, and no mining step anywhere in
  `mi_darshana.py` or its upstream writer.

- `platform/python-sidecar/pipeline/orchestrator/writers/mi_sambandha.py` — the
  writer that populates `mimamsa_manifestation_grammar` — states in its own
  docstring (lines 1–9): *"Learns per-native channel propensity from the outcomes
  recorded in mimamsa_manifestation_sets + mimamsa_calibration... PER-CHART scope:
  DELETE WHERE chart_id = %s, then re-insert."* It aggregates
  `mimamsa_manifestation_sets` LEFT JOINed to `mimamsa_calibration` **for this
  chart's own `prediction_id`s only** (lines 56–66), and:

  ```python
  counts[key]["opp"] += 1                                    # line 80
  verdict = row.get("composite_verdict") or ""                # line 81
  ch_fired = row.get("manifestation_channel") or ""            # line 82
  if verdict in ("confirmed", "partial") and ch_fired == channel_id:
      counts[key]["fire"] += 1                                 # lines 83-84
  ...
  n = opp                                                      # line 95
  grade = "empirical" if n >= 5 else "prior_only"              # line 96
  ```

  **The defect:** `n` (which gates the `"empirical"` label) is the
  *opportunity_count* — the count of this chart's own predictions ever assigned to
  the channel — not the count of *confirmed/denied* outcomes. `fire_count` (the
  genuinely outcome-derived number) plays no role in the grade decision at all.
  For chart `1c826d5a` (Abhinandan, zero-history), the live `calibration_summary`
  shows `total_matches: 0` — **zero predictions have ever been scored** for this
  chart, so `verdict` is `''` for every row, `fire_count` is 0 for every channel,
  and every channel that merely accumulated ≥5 prediction-set *assignments*
  (regardless of outcome) is unconditionally labeled `"empirical"` with
  `propensity = 0/n`. The statement text — *"fires with 0% propensity (n=9,
  empirical learning)"* — reads as a learned negative finding but is mechanically
  indistinguishable from "this chart has recorded zero outcomes of any kind."

  Contrast with the genuinely outcome-derived sibling in
  `platform/python-sidecar/pipeline/orchestrator/writers/mi_pramana.py` lines
  454–474, where `mimamsa_reliability`'s `"empirical"` grade is computed from
  `hits = [verdict == "CONFIRMED" ...]` over real `mimamsa_calibration` rows — a
  genuine outcome tally, not an opportunity tally.

**Net finding:** the corpus's mechanism ("population-level cross-chart mining")
does not exist anywhere in this call graph — `mimamsa_manifestation_grammar`,
`mimamsa_insight_units`, and every table `mi_darshana`/`mi_sambandha` touch are
chart-scoped by construction (`WHERE chart_id = %s`, `DELETE ... WHERE chart_id`).
The real defect is narrower but sharper: **`evidence_grade='empirical'` is granted
on assignment-count alone, with no floor on actual confirmed/denied outcome
count**, so a zero-outcome chart can and does emit `"empirical"`-graded,
real-timestamped insight rows that are not empirically grounded in any recorded
outcome at all — and `query_insights.ts` serves that grade verbatim beside
genuinely structural (never-claims-outcome-grounding) rows with no marker
distinguishing either the tier mixing (C1/C2) or the underlying opportunity-vs-
outcome conflation this diagnosis surfaces. This is a §N.7 item 4/6-class defect
("a verification flag/grade needs a real detector behind the specific claim, or
it's null") one layer inside a §N.6/CL-13 disclosure defect.

## 4. Sibling census

Grep scope: `platform/python-sidecar/pipeline/orchestrator/writers/mi_*.py` for
the `"empirical" if n >= ` grading pattern, and
`platform/src/lib/retrieval/registry/layers/L5_mimamsa/**` for surfaces mixing
`evidence_grade` values from more than one source table in one response.

| Site | Same defect (opportunity-count, not outcome-count, gates "empirical")? |
|---|---|
| `mi_sambandha.py:96` (`mimamsa_manifestation_grammar`) | **YES — this finding.** `n = opp` (assignment count), fire_count unused in the grade decision. |
| `mi_darshana.py:215` (`mimamsa_discoveries` → `emergent_law` insights) | Same textual pattern (`"empirical" if n >= 5 else "prior_only"`) but `n` there is `n_support` sourced from `mimamsa_discoveries`, itself populated by `mi_pariksha.py`'s retrodiction/pattern-mining substeps against this chart's own signal history — not traced further in this budget; flagging as a **candidate sibling, not confirmed**, for whoever specs the fix to check `mi_pariksha.py`'s own `n_support` semantics before assuming it is outcome-derived. |
| `mi_pramana.py:474` (`mimamsa_reliability` → `calibrated_outlook` insights) | **NO — clean.** `n = len(items)` where `items` are actual `mimamsa_calibration` rows with `hit = (verdict == "CONFIRMED")`; genuinely outcome-derived. This is the correct-pattern sibling, not a defect site. |
| `query_insights.ts` (mixing multiple `insight_type`s in one undifferentiated array) | **YES — this is C1/C2's serving-layer site**, the only `mimamsa_insight_units`-reading capability in `L5_mimamsa/`. |
| `query_calibration.ts` (`mimamsa_calibration_get`) | Also reads from multiple tables (`mimamsa_calibration`, `mimamsa_reliability`, `mimamsa_multipliers`, `mimamsa_qa_eval`) with `evidence_grade` present on the `mimamsa_reliability` block (lines 87–89) — a **structurally similar but functionally separate surface**, out of scope for F-35's own claim (which is specifically about `mimamsa_insight_get`) but worth a one-line note to whoever specs the fix, since the same disambiguation gap could recur there. |
| `query_manifestation_grammar.ts` | Single-source (`mimamsa_manifestation_grammar` only) — no mixing, not a C1/C2 site. |

No other file in the S3 lease (`L4_phala/**`, `ph_nimitta/**`, `muhurta.py`)
touches `mimamsa_insight_units` or `mimamsa_manifestation_grammar`.

## 5. Blast radius

- CL-00 controls: none of the known controls assert on `mimamsa_insight_get`'s
  `insight_units[]` shape or on `mi_sambandha`'s grade computation (checked
  `platform/scripts/governance/` control headings) — low risk of control
  regression from a fix.
- Other lanes sharing these files: `mi_darshana.py` and `mi_sambandha.py` are
  inside S3's declared lease (`L5_mimamsa/**` maps to the python-sidecar
  `mi_*` writers by extension of the L5 asset ownership); no other stream's OWNS
  list names them. `query_insights.ts` is squarely `L5_mimamsa/**`, S3-owned.
- A fix that tightens `mi_sambandha.py`'s grade predicate (e.g. gating
  `"empirical"` on `fire_count + (opp - fire_count of scored predictions) >= 5`,
  i.e. actual scored/verdicted count, not raw assignment count) changes
  `mimamsa_manifestation_grammar.evidence_grade` values for every chart, which
  ripples into `mi_darshana`'s insight_units re-synthesis on next rebuild and into
  `query_manifestation_grammar.ts`'s own served rows — both are same-file/same-
  writer consumers already inside S3's lease, not a cross-stream conflict.
- `mimamsa_calibration_get` (`query_calibration.ts`) is a likely second
  beneficiary of the same disclosure predicate if S3 specs this as a general
  "tag every served evidence_grade with its computing basis" fix rather than a
  point fix — flagged in §4, not claimed as part of F-35's own scope.

## 6. Correction to the audit corpus

The original `DIAGNOSIS-INCOMPLETE` entry's guessed mechanism ("population-level
cross-chart mining") should be retired, not carried into SPEC. The actual root
cause — an opportunity-count-only gate on the `"empirical"` grade label, which
happens to be most visible on a zero-outcome chart — is narrower, entirely
per-chart, and should be the mechanism statement SPEC works from. C1/C2 (the
missing-marker disclosure claim) stand as originally stated; C3 does not and is
replaced by the §3 finding above.
