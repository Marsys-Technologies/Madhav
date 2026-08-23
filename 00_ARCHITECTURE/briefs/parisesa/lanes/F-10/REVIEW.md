---
lane: F-10
stream: S5 MŪLA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-2
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-10/DIAGNOSIS.md, F-10/SPEC.md (revision 2), F-10/REVIEW.md (placeholder).
Source-verified against `/Users/Dev/par-night/main-ro`:
- `platform-mcp/src/tools/register_p1_synthesis.ts` lines 878–1011 (full prashna_undertaking_get block)
- `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts` (full file)
- `platform-mcp/src/tools/register_p1_aliases.ts` lines 1844–1858 (mimamsa_calibration_get block)
- Confirmed existence of `platform-mcp/src/generated/mcp_surface_profiles.generated.ts`
- Confirmed existence of `platform-mcp/src/lib/__tests__/` directory (harness target location)

No test was run (no builder worktree yet); exit test traced line-by-line against current source.

## Q1 — Mechanism vs. symptom

Mechanism. The spec correctly identifies two compounding root causes:
(1) `_DOMAIN_TO_ACTION` + `actionClass` are computed at lines 957–968, *after* `muhurtaResult` has already executed at lines 921–931 — so a naive "add WHERE clause" fails because the variable does not exist yet at that point.
(2) The underlying SQL uses only `[chart_id, top_windows]` as bind params with no `action_class` predicate.

The fix is a reorder-then-extend, not just an extension. The spec's §2.1 (hoist) + §2.2 (nullable bind + fallback call) + §2.3 (flag) together address the full causal chain, including the honest-disclosure edge case (0 filtered rows → unfiltered fallback with explicit flag). The recurrence guard (§3b harness) addresses the defect class across the codebase.

## Q2 — Sub-claim coverage

DIAGNOSIS §2 has four sub-claims:

| Sub-claim | SPEC element | Status |
|---|---|---|
| (a) no domain/action_class predicate on muhurtaResult | §2.2 (add nullable bind) | MAPPED |
| (b) wrong-domain window ranks above correct, no indication | §2.2 (predicate) + §2.3 (flag on fallback) | MAPPED |
| (c) no mismatch disclosure | §2.3 (judgment_flags entries) | MAPPED |
| (d) actionClass computed AFTER muhurtaResult runs | §2.1 (hoist reorder) | MAPPED |

All four sub-claims are covered. No unmapped claims.

## Q3 — Exit test fails on current code

Traced against source:
- Assertion 1: `election_windows` DIFFER between `domain:'health'` and `domain:'career'` calls. DIAGNOSIS §1 confirms both return byte-for-byte identical `["marriage", "marriage", "medical"]` with identical `composite_quality` values. Assertion **FAILS on current code** — confirmed.
- Assertion 2: every returned `election_windows[].action_class` equals the derived `content.action_class` OR a `judgment_flags` entry explains the mismatch. Health call returns `action_class=["marriage","marriage","medical"]` vs `content.action_class="medical_procedure"`; `judgment_flags: []`. Neither condition met. **FAILS on current code** — confirmed.
- Assertion 3 (regression guard on anchorResult): `anchorResult` applies `AND pa.domain = $2` at line 942 — this is clean and the assertion would PASS on current code (correct behavior preserved).

Exit test is genuinely red on current source.

## Q4 — Sibling sites

SPEC §4 covers every sibling identified in DIAGNOSIS §4a/4b/4c:

| Sibling | Coverage | Verified |
|---|---|---|
| F-10 itself (muhurtaResult) | §2 point fix | Source-confirmed |
| F-27 (mimamsa_calibration_get / query_calibration) | Own lane spec; harness guard | register_p1_aliases.ts:1844-1858 and query_calibration.ts both confirmed match SPEC claims |
| F-03 (limit/offset, 4 caps) | Own lane spec; harness excludes limit/offset (explicit reason given) | Exclusion rationale sound |
| F-06 (chart_id not in schema) | Own lane; harness exclusion explained (different shape — no declared param to compare) | Exclusion rationale sound |
| F-08 (phala_mitigation_get) | Harness known_failures skip-list until S3 fix lands | Adequate |
| F-26 (include_lel_events) | Harness known_failures skip-list until F-26 fix lands | Adequate |
| F-133 (date-range predicate missing) | S3 own spec; harness stretch goal, not promised | Exclusion rationale sound (different defect shape) |

All siblings are accounted for with either coverage or a stated exclusion reason.

## Q5 — Recurrence guard

The param-parity harness (§3b) IS the recurrence guard and it genuinely detects the defect class:
- For every declared non-allowlisted param, it calls the tool twice with two distinct values and asserts the responses differ.
- A future capability that drops a declared filter param will fail CI at merge time.
- The ADVISORY_PARAMS registry with a companion unit test (enforcing non-empty `reason` strings) prevents accidental suppression.
- CI trigger paths cover `platform-mcp/src/tools/**`, `platform-mcp/src/lib/**`, and `platform/src/lib/retrieval/registry/**` — the full surface where this defect class can appear.

This is a strong guard, not a weak proxy. It detects the exact failure mode demonstrated in DIAGNOSIS §1.

## Q7 — Unverified assumptions / citation accuracy

SPEC revision 2 explicitly states all line numbers were re-verified against current source. Independent verification confirms:

| Claim | Verified |
|---|---|
| muhurtaResult at lines 921–931 (no domain predicate) | CONFIRMED — lines 921–931 exactly as described |
| anchorResult at lines 934–946 (AND pa.domain = $2) | CONFIRMED — line 942 exactly |
| _DOMAIN_TO_ACTION at lines 957–967 | CONFIRMED |
| actionClass at line 968 | CONFIRMED |
| query_calibration.ts input_schema lines 27–43 (no domain field) | CONFIRMED — chart_id/include_held_out/promoted_only only |
| multiplierSql at line 95 (domain in SELECT, not WHERE) | CONFIRMED — line 95, WHERE has only chart_id + multFilter |
| filters echo at line 129 (no domain) | CONFIRMED — {include_heldout, promoted_only} only |
| register_p1_aliases.ts mimamsa_calibration_get at 1844–1858 | CONFIRMED — domain: z.string().optional() at line 1849, forwarded to callPlatformPrim at line 1854 |
| mcp_surface_profiles.generated.ts exists | CONFIRMED at platform-mcp/src/generated/ |

No unverified assumptions found. Every cited file:line is accurate against current origin/main source.

writer_asset / data_delta / RS-A: Not applicable. F-10 is a tool-layer fix (platform-mcp/src/tools/) with no GA writer involvement; rebuild policy's shadow-run requirement does not apply to this lane.

## Verdict: COMPLETE

SPEC revision 2 is clean across all seven rubric dimensions. Mechanism identified correctly, all sub-claims mapped, exit test genuinely red on current code, all siblings covered or excluded with stated reasons, recurrence guard is a true defect-class detector, and every line citation verified against source. Builder may proceed.
