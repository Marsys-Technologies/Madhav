import { describe, it, expect } from 'vitest'
import { arbitrateBudgets } from '@/lib/pipeline/budget_arbiter'
import { ensureB11WholeChartReadFloor } from '@/lib/pipeline/compiled_floor_adapter'
import type { PipelinePlan } from '@/lib/pipeline/types'

describe('S5 failure-honesty: budget_arbiter can zero a floor tool token_budget while presence-check floor guarantees treat it as satisfied', () => {
  it('planner-supplied msr_sql (priority 3) gets zeroed by arbitration; ensureB11WholeChartReadFloor then no-ops, believing the floor is met', () => {
    const tools = [
      { tool_name: 'msr_sql', priority: 3 as const, token_budget: 2000 },
      { tool_name: 'some_other_p1_tool', priority: 1 as const, token_budget: 2000 },
    ]
    const arbitrated = arbitrateBudgets(tools, {
      synthesis_model_max_context: 2000,
      system_prompt_reserve: 800,
      synthesis_guidance_reserve: 0,
      safety_margin: 0.85,
      min_tokens_per_tool: 200,
    })
    const msr = arbitrated.find((t) => t.tool_name === 'msr_sql')!
    console.log('msr_sql token_budget after arbitration:', msr.token_budget)
    expect(msr.token_budget).toBe(0) // fully trimmed away (p3 floor = 0, "can be trimmed away entirely")

    // Now simulate plan_stage.ts's exact sequence: toolsAuthorized built from
    // (arbitrated) plan.tool_calls tool_name list — token_budget=0 entries are NOT removed.
    const toolsAuthorized = arbitrated.map((t) => t.tool_name)
    const plan = { tool_calls: [], query_class: 'holistic' } as unknown as PipelinePlan
    const injected = ensureB11WholeChartReadFloor(plan, toolsAuthorized)

    console.log('ensureB11WholeChartReadFloor injected new tools?', injected)
    console.log('toolsAuthorized after:', toolsAuthorized)
    // The floor guarantee believes msr_sql (an L2_5_TOOLS member) already satisfies B.11,
    // solely because the NAME is present -- even though its token_budget is 0 and it will
    // contribute ~nothing to synthesis. No replacement/top-up tool is injected.
    expect(injected).toBe(false)
  })
})
