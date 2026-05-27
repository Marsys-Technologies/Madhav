/**
 * agentic — the bounded-loop consult pipeline.
 *
 * Strategy: model-driven tool loop (R11.F bounded agentic loop, MAX_ITERATIONS=8).
 * The B.11 floor pre-executes deterministically via the shared
 * `injectB11Floor` helper; the loop then enters with a planner-authorised
 * subset and lets the model request additional tool calls under the iteration
 * cap. UI label: "Claude-style chat".
 *
 * In consult/route.ts this is the `runAgenticLoop(...)` branch
 * (route.ts line 1062). The body still lives there pending G5b; this
 * module exists so:
 *   • each pipeline kind owns its types + tests (AC.4)
 *   • the route's selector has a typed target to point at
 *   • the agentic vs single_pass split is structural, not just a boolean
 *
 * Tests in __tests__/agentic.test.ts assert the module's identity
 * (kind === 'agentic') and the describe() shape — the byte-identical
 * runtime test lives in route.ts's existing test suite.
 */

import type { QueryPipeline } from '../types'

export const agenticPipeline: QueryPipeline = {
  kind: 'agentic',
  describe() {
    return {
      kind: 'agentic',
      description:
        'Bounded model-driven tool loop (MAX_ITERATIONS=8). B.11 floor ' +
        'pre-executes deterministically via the planner; the loop enters with ' +
        'a planner-authorised subset and may request additional tool calls ' +
        'under the cap. UI label: Claude-style chat.',
    }
  },
}
