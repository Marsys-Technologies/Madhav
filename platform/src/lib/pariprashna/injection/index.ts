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
 *
 * ── DOOR COVERAGE, STATED RATHER THAN IMPLIED (§N.8) ────────────────────────
 * These controls are NOT uniformly wired across the three serving doors, and
 * the gaps are scope boundaries rather than oversights. Anyone reading "PPR-13
 * is done" should read this table first:
 *
 *   | control                  | /api/pariprashna | /api/chat/consult | prashna_ask |
 *   |--------------------------|------------------|-------------------|-------------|
 *   | 1 delimiting + clause    | yes              | yes               | yes         |
 *   | 2 plan closure           | yes              | tool-input arm    | no          |
 *   | 3 tool-sequence trace    | yes              | no                | n/a (¹)     |
 *   | 4 entitlement scan       | yes              | no                | no          |
 *
 * (¹) `prashna_ask` is explicitly non-agentic — it has no tool loop to diverge,
 *     so there is no sequence for control 3 to watch. That is an honest n/a,
 *     not an untested "no".
 *
 * Controls 3 and 4 need a per-turn emitter, a block/commit state machine and an
 * authenticated entitlement set to hang off. The Paripraśna pipeline has all
 * three as typed stages; the other two doors have their own, differently-shaped
 * machinery, and retrofitting them is a larger change than this lane's brief.
 * The consult door DOES get the tool-input identity rejection (the half of
 * control 2 that guards a live cross-tenant path) because that one needed no
 * new plumbing.
 */

export * from './flag'
export * from './delimit'
export * from './plan_closure'
export * from './tool_sequence'
export * from './entitlement_scan'
