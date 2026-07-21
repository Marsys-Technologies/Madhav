/**
 * Smoke test: MSR-SQL filter against live msr_signals table.
 * Run: npm run pipeline:msr-sql-test
 * Requires DATABASE_URL or Cloud SQL env vars to be set.
 */
// D7 Step 4: getTool() from lib/retrieve retired — use getToolByName from tool_name_bridge
import { getToolByName as getTool } from '@/lib/retrieval/registry/tool_name_bridge'

const TEST_PLANS = [
  {
    query_plan_id: 'smoke-1',
    query_text: 'career',
    query_class: 'interpretive' as const,
    domains: ['career'],
    forward_looking: false,
    tools_authorized: ['msr_sql'],
    history_mode: 'synthesized' as const,
    panel_mode: false,
    expected_output_shape: 'three_interpretation' as const,
    manifest_fingerprint: 'smoke',
    schema_version: '1.0' as const,
  },
]

async function main() {
  const tool = getTool('msr_sql')
  if (!tool) {
    console.error('msr_sql tool not found')
    process.exit(1)
  }

  for (const plan of TEST_PLANS) {
    console.log(`Testing plan: ${plan.query_plan_id} (domains: ${plan.domains.join(', ')})`)
    try {
      const result = await tool.retrieve(plan)
      if (result.results.length === 0) {
        console.warn(`  WARN: No results for plan ${plan.query_plan_id}`)
      } else {
        console.log(`  OK: ${result.results.length} results`)
      }
    } catch (err) {
      console.error(`  FAIL:`, err)
      process.exit(1)
    }
  }

  console.log('MSR-SQL smoke test passed.')
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
