/**
 * single_pass — the non-agentic consult pipeline.
 *
 * Strategy: one synthesis LLM call with the assembled tool bundle attached
 * to the system prompt (legacy "Classic Marsys" UI label). No model-driven
 * tool loop — every tool is invoked by the planner-derived plan, results
 * are bundled, and synthesis runs once.
 *
 * In consult/route.ts this is the `adapter.chat(adapterChatReq)` branch
 * (route.ts line 1068). The body still lives there pending G5b; this
 * module exists so:
 *   • each pipeline kind owns its types + tests (AC.4)
 *   • the route's selector has a typed target to point at
 *   • the agentic vs single_pass split is structural, not just a boolean
 *
 * Tests in __tests__/single_pass.test.ts assert the module's identity
 * (kind === 'single_pass') and the describe() shape — the byte-identical
 * runtime test lives in route.ts's existing test suite.
 */

import type { QueryPipeline } from '../types'

export const singlePassPipeline: QueryPipeline = {
  kind: 'single_pass',
  describe() {
    return {
      kind: 'single_pass',
      description:
        'Non-agentic synthesis. Planner-derived tool bundle is attached to ' +
        'the system prompt; one synthesis LLM call produces the final answer. ' +
        'UI label: Classic Marsys.',
    }
  },
}
