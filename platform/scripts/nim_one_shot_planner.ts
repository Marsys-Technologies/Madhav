/**
 * nim_one_shot_planner.ts — single-call debug shim for callLlmPlanner().
 *
 * Captures the AI SDK wire body (via NIM_DEBUG_BODY) and immediately surfaces
 * the first real error or success so the diff vs. probe P3 is unambiguous.
 *
 * Usage (from platform/):
 *   NIM_DEBUG_BODY=1 \
 *   PLANNER_MODEL_ID=nvidia/llama-3.3-nemotron-super-49b-v1 \
 *   npx tsx --conditions=react-server scripts/nim_one_shot_planner.ts
 *
 * Set NIM_DEBUG_BODY=1 to print the first 3000 chars of the request body to
 * stderr before the NIM call is made. The resulting stderr output can be
 * diffed against the probe P3 body to find the first diverging field.
 *
 * CHART_ID defaults to "test-native". PLANNER_MODEL_ID defaults to
 * nvidia/llama-3.3-nemotron-super-49b-v1.
 */
import { isDirectEntrypoint } from './lib/entrypoint'

const modelId = process.env.PLANNER_MODEL_ID ?? 'nvidia/llama-3.3-nemotron-super-49b-v1'
const chartId  = process.env.CHART_ID ?? 'test-native'

const QUERY = 'What is the strength of the lagna lord and how does it affect career prospects?'

async function main(): Promise<void> {
  process.stderr.write(`[one-shot] model=${modelId} chart=${chartId}\n`)
  process.stderr.write(`[one-shot] query="${QUERY}"\n`)
  if (!process.env.NIM_DEBUG_BODY) {
    process.stderr.write(`[one-shot] TIP: set NIM_DEBUG_BODY=1 to capture wire body\n`)
  }

  const { callLlmPlanner } = await import('@/lib/pipeline/manifest_planner')

  try {
    const plan = await callLlmPlanner(QUERY, [], modelId, chartId)
    process.stderr.write(`[one-shot] ✅ SUCCESS\n`)
    process.stderr.write(`  query_class: ${plan.query_class}\n`)
    process.stderr.write(`  tool_calls:  ${plan.tool_calls.length}\n`)
    plan.tool_calls.forEach((tc, i) => {
      process.stderr.write(`    [${i}] ${tc.tool_name} priority=${tc.priority} budget=${tc.token_budget}\n`)
    })
    process.exit(0)
  } catch (err) {
    process.stderr.write(`[one-shot] ❌ FAILED\n`)
    process.stderr.write(`  ${err instanceof Error ? err.message : String(err)}\n`)
    if (err instanceof Error && (err as NodeJS.ErrnoException & { cause?: unknown }).cause) {
      const cause = (err as NodeJS.ErrnoException & { cause?: unknown }).cause
      process.stderr.write(`  cause: ${cause instanceof Error ? cause.message : String(cause)}\n`)
      // Surface the NIM response body if available on APICallError
      const apiErr = cause as Record<string, unknown>
      if (apiErr?.responseBody) {
        process.stderr.write(`  nim_response_body: ${String(apiErr.responseBody).slice(0, 1000)}\n`)
      }
    }
    process.exit(1)
  }
}

if (isDirectEntrypoint(import.meta.url, process.argv[1])) {
  main().catch(err => {
    process.stderr.write(`[one-shot] fatal: ${err}\n`)
    process.exit(1)
  })
}
