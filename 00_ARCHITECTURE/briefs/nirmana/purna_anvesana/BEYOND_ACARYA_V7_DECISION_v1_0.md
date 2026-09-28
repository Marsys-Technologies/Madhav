---
artifact: BEYOND_ACARYA_V7_DECISION
canonical_id: BEYOND_ACARYA_V7_DECISION
version: 1.0
status: DECIDED
created: 2026-09-27
lane: JATAKA-PHASE-A3-SOURCE-INTEGRITY (item 5)
governed_by: 00_ARCHITECTURE/briefs/jataka/JATAKA_CHART_WORKSPACE_PHASE_A3_SOURCE_INTEGRITY_ADDENDUM_v1_0.md
---

# Decision: create BEYOND_ACARYA_ACCEPTANCE_v7.json as v6's source-provenance successor

## Decision

Create `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v7.json`, naming
`BEYOND_ACARYA_ACCEPTANCE_v6.json` as its immutable predecessor. v6 is not modified, overwritten,
or regenerated in place — it remains byte-identical (`sha256:04579974349aed1377b26755b4a737dcb4cd14adee808b773e6cc986a956aec5`),
now treated as historical, exactly like v2 through v5.

## Authority

Native message (2026-09-27) accepting the Phase-A2 report at `7673c96b8` and authorizing the
Phase-A3 source-integrity pass, item 5: "Create a new Pūrṇa Beyond-Ācārya successor against the
same reviewed head... Authorized only if externally-defined corpus/denominators aren't weakened,
novel-combination coverage remains passing, omission count remains zero, route/semantic-edge
coverage doesn't regress, long-inquiry closure and abstention-quality remain passing, all
fingerprint/hash changes are explained by the reviewed Phase-A3 changes."

## Gate verification (performed before creating the artifact, not after)

Ran the real `evaluateBeyondAcaryaAcceptance()` evaluator (no fabricated values) against the
committed `capability_knowledge.snapshot.json` at the reviewed technical head
(`ed5ad601c5e568f5d6c5d8ec72bc7c8f9ff2bd2b`) and the unchanged, externally-defined
`BEYOND_ACARYA_ACCEPTANCE_CASES` corpus (`beyond-acarya-inquiry-corpus-v1`, untouched this
session). Result, compared metric-by-metric against v6:

| metric | v6 | v7 (this decision) | verdict |
|---|---|---|---|
| novel_combination_suite | passed, 5 cases, 13 expected, 0 missing | identical | no regression |
| omission_rate | passed, 0 omitted / 25 expected | identical | no regression |
| route_coverage | passed, 34 / 34 | identical | no regression |
| semantic_edge_coverage | passed, 9 / 9 | identical | no regression |
| long_inquiry_closure | passed, 1/1 completed, 10 min iterations, evidence retained | identical | no regression |
| abstention_quality | passed, 3/3 | identical | no regression |
| overall `passed` | true | true | no regression |

Only `capability_content_hash` / `report_hash` / the four snapshot fingerprints moved:
- `capability_content_hash`: `sha256:0a2a675d...` → `sha256:6a595916...`
- `report_hash`: `sha256:bfe04932...` → `sha256:7bdef361...`

Both changes are fully explained by real, already-reviewed Phase-A3 source edits landed in this
same branch: `query_prospective_ledger.ts` and `standing_predictions_read`'s new `include_stale`
input-schema fields, and `source_query_availability.ts`'s corrected `contract_sha256`/`source_ref`
for `source-query:query-prospective-ledger:v1` — no unrelated or unreviewed change contributes to
the shift. No corpus denominator was edited, added, or removed to produce this result.

## What this decision does NOT do

- Does not reopen or close the Pūrṇa campaign.
- Does not claim live, deployed, expert, empirical, or production acceptance — `evidence_kind`
  remains `synthetic_source_local`, `source_status` remains `SOURCE_ONLY_NOT_LIVE`,
  `empirical_answer_quality` / `production_validation` / `deployed_route_validation` /
  `candidate_validation` all remain `NOT_RUN`, `expert_domain_review` remains
  `REQUIRED_BEFORE_EMPIRICAL_ACCEPTANCE`.
- Does not narrow or widen `claim_ceiling` — retained verbatim from v6
  (`SOURCE_SCOPE_COMPLETE_WITH_AUTHORITY_BOUND_REMAINDER`).
- Does not touch v6.json or any earlier historical artifact (v2-v5) in any way.

## Consequence for the test suite

`beyond_acarya_acceptance.test.ts` updated so v6 becomes an immutable historical predecessor
(pinned to its own file hash, exactly like v2-v5) and v7 becomes the current executable-report
check — a future capability change will turn v7's check red without mutating any historical
artifact, the same mechanism that already governed the v2→v6 progression. See commit `03f372efc`.
