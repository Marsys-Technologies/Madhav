---
canonical_id: PHASE_5B_DASHA_DISCIPLINE_BRIEF
version: 1.0
status: AUTHORED_READY_TO_EXECUTE
author: Claude (analysis stream)
authored_on: 2026-05-19
parent_plan: PHASE_5_DASHA_CORRECTNESS_MASTER_PLAN_v1_0.md
sub_phase: 5B
depends_on: 5A (closed — commit 67b36de)
two_stream_branch: analysis/backend-data-pipeline-perf-audit
---

# Phase 5B — Synthesis Dasha Discipline Gate

## §0 Purpose

§5A delivered discoverability + retrieval: the planner now has the R-DA rule and the
`query_dasha_periods` tool to pull ground-truth dasha rows from the DB. §5B closes the
next gap: synthesis is still not **mandated** to use those rows. Even when the correct
data arrives in the context bundle, the model can paraphrase from its pretrained
Vimshottari knowledge instead of citing `DSH.V.NNN`. This brief adds a hard synthesis
gate that makes dasha citation mandatory across all four synthesis templates.

Root-cause reference: `DASHA_CORRECTNESS_RESEARCH_v1_0.md §2.5 Gap E` + `§4.D`.

## §1 Scope

Exactly four files changed (three new exports from shared.ts + four template bodies):

| File | Change |
|---|---|
| `platform/src/lib/prompts/templates/shared.ts` | Export `DASHA_DISCIPLINE_GATE` constant |
| `platform/src/lib/prompts/templates/predictive.ts` | Import + inject gate; version 3.0 → 3.1 |
| `platform/src/lib/prompts/templates/factual.ts` | Import + inject gate; version 2.0 → 2.1 |
| `platform/src/lib/prompts/templates/holistic.ts` | Import + inject gate; version 2.0 → 2.1 |
| `platform/src/lib/prompts/templates/remedial.ts` | Import + inject gate; version 2.0 → 2.1 |
| `platform/src/lib/prompts/__tests__/prompts.test.ts` | §5B test suite (8 tests) + F025 fixture |

**Out of scope for §5B (§C scope):**
- `checkpoint_dasha.ts` — post-synthesis validator (§5C)
- Any change to `PLANNER_PROMPT_v2_0.md` (R-DA already shipped in §5A)
- `interpretive.ts`, `cross_domain.ts`, `discovery.ts` — not in the 4-template mandate
- New retrieval tools — none needed
- `npm run answer:eval` — pre-commit verification only

## §2 Gate text (canonical — from research dossier §4.D, approved §6.2)

```
DASHA DISCIPLINE GATE (mandatory):
Whenever this response claims a current, previous, next, or upcoming dasha lord
(MD / AD / PD / SD / PD2 at any level), the claim MUST be grounded in the
dasha rows present in the context bundle OR the query_dasha_periods tool result.

Citation format:
  "current MD lord is Mercury (→ DSH.V.015, 2010-08-18 to 2027-08-19)"
  "next MD is Ketu (→ DSH.V.024, 2027-08-19 to 2034-08-18)"

Forbidden:
  - Asserting a dasha lord without a DSH.V.NNN citation
  - Asserting dasha period dates without citing the FORENSIC §5.1 row
  - Extrapolating "next" / "previous" from generic Vimshottari knowledge
    when the bundle's dasha_vimshottari rows are present — this is a B.10
    fabricated-computation violation

If the required dasha row is absent from the bundle, write:
  [EXTERNAL_COMPUTATION_REQUIRED: dasha_vimshottari row for <range> not
   present in bundle; refetch via query_dasha_periods]
Do not guess the period from training-data knowledge of the Vimshottari cycle.
```

## §3 Placement in each template

The gate is added **after** `${CALIBRATION_LANGUAGE_GATE}` and before the
per-class response-structure block. This mirrors the pattern of FALSIFIER_GATE and
CALIBRATION_LANGUAGE_GATE — inline in the body string, not in buildOpeningBlock()
(because it applies only to the 4 dasha-relevant classes, not universally).

### predictive.ts (version 3.0 → 3.1)

Placement: after `${CALIBRATION_LANGUAGE_GATE}` and before `RESPONSE STRUCTURE
(mandatory for this query class):`.

### factual.ts (version 2.0 → 2.1)

Placement: after `${CALIBRATION_LANGUAGE_GATE}` and before
`${PRESCRIPTIVE_CITATION_GATE}`.

### holistic.ts (version 2.0 → 2.1)

Placement: after `${CALIBRATION_LANGUAGE_GATE}` and before `Rules for holistic
responses:`.

### remedial.ts (version 2.0 → 2.1)

Placement: after `${CALIBRATION_LANGUAGE_GATE}` and before `Rules for remedial
responses:`.

## §4 Test suite (F025 fixture — prompts.test.ts)

New describe block: `DASHA DISCIPLINE GATE — §5B`.

8 tests:

1. All 4 mandated templates contain `DASHA DISCIPLINE GATE` in rendered output.
2. Gate mandates `DSH.V.NNN` citation format.
3. Gate forbids extrapolation from generic Vimshottari knowledge.
4. Gate contains `EXTERNAL_COMPUTATION_REQUIRED` for missing rows.
5. Gate references `query_dasha_periods` tool.
6. Gate is injected once per template (not duplicated).
7. Templates NOT in the mandate (`interpretive`, `cross_domain`, `discovery`) do NOT
   carry the gate.
8. `cross_native` stub does not carry the gate.

Label: `F025 — dasha_discipline_gate_in_4_templates`

## §5 Acceptance criteria

- [ ] `tsc --noEmit` green (no new type errors).
- [ ] `vitest run platform/src/lib/prompts/__tests__/prompts.test.ts` — all tests pass
      (existing + 8 new §5B tests).
- [ ] `vitest run platform/src/lib/` full retrieve + prompts suite — no regressions.
- [ ] `vitest run platform/tests/eval/planner_regression_gate.test.ts` — 2/2 PASS
      (no drops from the §5A baseline).
- [ ] Gate text appears verbatim in rendered output for all 4 mandated templates.
- [ ] `interpretive`, `cross_domain`, `discovery`, `cross_native` rendered outputs do NOT
      contain `DASHA DISCIPLINE GATE`.
- [ ] Version numbers bumped: predictive 3.0 → 3.1; factual/holistic/remedial 2.0 → 2.1.

## §6 Commit target

```
feat(dasha): DASHA_DISCIPLINE_GATE in all 4 synthesis templates (§5B)
```

## §7 Post-close

On successful close:
1. Update `PHASE_5_DASHA_CORRECTNESS_MASTER_PLAN_v1_0.md §B` state tracker:
   - `5B_synthesis_dasha_gate.status: CLOSED`
   - `5B_synthesis_dasha_gate.closing_commit_sha: <sha>`
   - `5B_synthesis_dasha_gate.closed_on: 2026-05-19`
2. Advance campaign status: `§5A CLOSED; §5B CLOSED; §5C PENDING`.
3. Author §5C brief in a subsequent Cowork session.

---

*End PHASE_5B_DASHA_DISCIPLINE_BRIEF_v1_0. Authored 2026-05-19.*
