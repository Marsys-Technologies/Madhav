---
lane: F-14
stream: S2 (MĀTRĀ)
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-2
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read PROTOCOL.md, SPEC.md, DIAGNOSIS.md for F-14. No prior REVIEW.md content (placeholder only). Read source at `/Users/Dev/par-night/main-ro/platform-mcp/src/tools/registry_bridge.ts` (4730 lines), `/Users/Dev/par-night/main-ro/platform-mcp/src/lib/response_budget.ts`, and `/Users/Dev/par-night/main-ro/platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts`. Verified every file:line citation in SPEC and DIAGNOSIS against current source. Traced exit-test failure path line-by-line against current source (live MCP call not possible from this role; trace is complete and sufficient).

## Q1 — Mechanism vs. symptom

SPEC addresses all three independent mechanisms directly:
- §2a: missing `health`/`relationship` keys in all five `DOMAIN_READING_*` maps (code-traced to `registry_bridge.ts:1034-1043`, confirmed exact)
- §2b: missing `attachDomainCompleteness`/`attachDomainReading` call sites in `assess_marriage` (`:2989→2990`) and `assess_health` (`:3071→3072`) handlers (confirmed absent; `assess_career` at `:3030-3032` and `assess_wealth` at `:3112-3114` confirmed present as exemplars)
- §2c: wrong key `response['completeness']` at `buildAssessResponse:2925` (key never populated — `attachDomainCompleteness` sets `response['domain_completeness']`; `completeness_directive` is never referenced at all)
- §2d: silent no-op in `attachDomainCompleteness:837` when `assembleDomainCompleteness` returns null (confirmed: only `career_*`/`wealth_*` bundles exist in `dossier_slices.generated.ts`; no `health_*`/`relationship_*` keys)

All four are mechanism-level fixes. PASS.

## Q2 — Diagnosis sub-claims mapped to spec elements

| Diagnosis claim | Spec element |
|---|---|
| C1: assess_health never returns `reading` | §2a (map key) + §2b (call site) |
| C2: assess_health never returns `domain_completeness` | §2a + §2b + §2c |
| C3: assess_health never returns `completeness_directive` | §2a + §2b + §2c |
| §3.3: call sites absent for assess_health/assess_marriage | §2b |
| §3.4: buildAssessResponse key mismatch affects all four tools | §2c |
| §2d/F-31: silent no-op when no dossier bundle for domain | §2d |
| §5: deep_dive all-or-nothing grounding drop | explicitly out-of-scope §7, with stated justification |

All diagnosis claims mapped. No unmapped claim found. PASS.

## Q3 — Exit test genuinely fails today

Traced line-by-line:

**Test 1** (`reading` present for all four tools):
- `assess_wealth`/`assess_career`: call `attachDomainReading` → `buildDomainReading` → `DOMAIN_READING_FAMILIES['wealth'/'career']` found → `families_total > 0` → `response['reading']` set → `buildAssessResponse:2924` copies it to `grounding['reading']`. PASS for these two today.
- `assess_marriage`/`assess_health`: neither calls `attachDomainReading`. `response['reading']` never set. `grounding['reading']` absent. **Test FAILS today** for these two tools. ✓

**Test 2a** (`domain_completeness`/`completeness_directive` for career/wealth):
- `attachDomainCompleteness` sets `response['domain_completeness']` (line 838) and `response['completeness_directive']` (line 844).
- `buildAssessResponse:2925` checks `response['completeness']` — this key is NEVER set by anything. → `grounding['domain_completeness']` absent.
- `completeness_directive` is never referenced in `buildAssessResponse` at all. → `grounding['completeness_directive']` absent.
- **Test FAILS today** (`expect(grounding).toHaveProperty('domain_completeness')` → fails). ✓

**Test 2b** (`domain_completeness_empty_reason` for health/marriage):
- `attachDomainCompleteness` not called for these handlers.
- Field `domain_completeness_empty_reason` does not exist anywhere in source today.
- **Test FAILS today**. ✓

All exit-test branches confirmed to fail on current source. PASS.

## Q4 — Sibling sites covered

Diagnosis §4 provides a complete census of five maps and four handlers. SPEC §2a covers all five maps (§4 confirms all five are wealth/career-only). §2b covers both missing call sites (assess_marriage, assess_health) — the other two (career, wealth) already have them. §2c covers the single shared `buildAssessResponse` function serving all four tools. §2d covers `attachDomainCompleteness:837` (the silent early return). `IMMUNE_HONESTY_FIELDS` addition for `domain_completeness_empty_reason` is also specified.

No sibling site left uncovered or excluded without stated reason. PASS.

## Q5 — Recurrence guard

Exit test iterates all four `assess_*` tools by name (not a subset). It checks:
1. `reading` presence — catches any future handler that forgets the call site
2. `domain_completeness`/`completeness_directive` key names — catches any future allow-list key rename in `buildAssessResponse`
3. `domain_completeness_empty_reason` disclosure — catches any future silent no-op regression

Guard detects the actual defect class (missing call site, wrong key name, silent omission), not a proxy. PASS.

## Q7 — Unverified assumptions / citation accuracy

All file:line citations in SPEC verified against current source:
- `registry_bridge.ts:1020-1043` (DOMAIN_READING_* maps): EXACT ✓
- `registry_bridge.ts:2923-2927` (buildAssessResponse grounding allow-list): EXACT ✓
- `registry_bridge.ts:835-837` (attachDomainCompleteness early return): EXACT ✓
- `registry_bridge.ts:678` (assembleDomainCompleteness): EXACT ✓
- `registry_bridge.ts:2986-2989` (assess_marriage insert point): CONFIRMED ("near" qualifier is honest) ✓
- `registry_bridge.ts:3068-3071` (assess_health insert point): CONFIRMED ✓
- `register_d8_assess_domain.ts:184-188` (DOMAIN_DIRECT_VARGAS): EXACT ✓
- `response_budget.ts:56-101` (IMMUNE_HONESTY_FIELDS): EXACT ✓
- assess_health docstring at `:3042` ("1st+6th+8th lords + Sun kāraka"): EXACT ✓
- assess_marriage docstring at `:2960` ("7th lord + Venus kāraka"): EXACT ✓
- Dossier bundles: only `career_*`/`wealth_*` keys confirmed in `dossier_slices.generated.ts` ✓

Spec §2a's house/karaka/varga assignments are sourced from live file docstrings and `DOMAIN_DIRECT_VARGAS` — not invented. The "BUILD must re-verify" instruction is appropriate belt-and-suspenders. No unverified assumptions found. PASS.

## writer_asset / data_delta / RS-A

Not applicable. F-14 is a pure MCP-presentation-layer fix in `registry_bridge.ts` with no DB migration, no writer-layer change, no asset generation. No shadow run, rebuild group, or RS-A entry required.

## Named deficiencies

None.

## Verdict: COMPLETE

Spec fully addresses all three mechanisms identified by diagnosis (missing map keys, missing call sites, wrong allow-list key in buildAssessResponse) plus the §2d disclosure gap. All citations verified exact. Exit test confirmed to fail on all branches today. Sibling census complete. Recurrence guard genuine. The deep_dive all-or-nothing grounding drop (DIAGNOSIS §5) is explicitly scoped out of this spec with a clear justification and a recommendation for a new finding — acceptable. VERIFIER should confirm at Stage V that the spec is not claimed to close the deep_dive case (§7 already states this clearly).
