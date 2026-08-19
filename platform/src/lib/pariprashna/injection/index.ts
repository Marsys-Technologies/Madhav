/**
 * Paripraśna injection containment — barrel (lane G1-G, PPR-13).
 *
 * The four controls PPR-13 names, in the order the pipeline meets them:
 *
 *   1. `delimit.ts`          — question + prior turns + retrieved evidence +
 *                              agentic tool results structurally delimited as
 *                              DATA, with the clause that makes the tags mean
 *                              something (prompt-side; depends on the model).
 *   2. `plan_closure.ts`     — the plan's two open surfaces closed against the
 *                              injection path (deterministic; does not).
 *   3. `tool_sequence.ts`    — executed-vs-authorized divergence, trace-flagged
 *                              and never blocked (the ruling's own wording).
 *   4. `entitlement_scan.ts` — answer-side foreign-chart-reference redaction,
 *                              folded into the pre-wire pass G1-A already runs
 *                              (deterministic, fail-closed; does not).
 *
 * Control 1 is the only one that depends on a model cooperating, which is why
 * there are four and not one — the same layering argument `safety/prompt_policy.ts`
 * makes for HS-1's three controls.
 */

export * from './flag'
export * from './delimit'
export * from './plan_closure'
export * from './tool_sequence'
export * from './entitlement_scan'
