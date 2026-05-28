import { Client } from '@modelcontextprotocol/sdk/client/index.js'
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js'

const MCP_URL = process.env['MCP_URL'] ?? ''
const MCP_KEY = process.env['MCP_KEY'] ?? ''
const CHART_ID = 'abhisek_mohanty_primary'
const TODAY = new Date().toISOString().split('T')[0]!
const NEXT_MONTH = new Date(Date.now() + 30 * 86400000).toISOString().split('T')[0]!

const FAILING: Record<string, Record<string, unknown>> = {
  query_transit_event:    { chart_id: CHART_ID, from_date: TODAY, to_date: NEXT_MONTH },
  query_divisional_chart: { chart_id: CHART_ID, division: 'D9' },
  query_remedial_mantras: { planet: 'saturn', query: 'Saturn remedy' },
  muhurta_finder:         { event: 'travel', from_date: TODAY, to_date: NEXT_MONTH },
  query_kp_ruling_planets:{ chart_id: CHART_ID },
  query_signal_state:     { chart_id: CHART_ID, signal_ids: ['SIG.MSR.001', 'SIG.MSR.002'] },
  get_trace:              { limit: 1 },
  log_prediction:         { prediction: 'test', confidence: 'high', horizon: '2026-12-31', falsifier: 'test', dry_run: true },
  record_outcome:         { prediction_id: 'test_id', outcome: 'pending', notes: 'test', dry_run: true },
  flag_disagreement:      { tool_name: 'query_chart_facts', description: 'test', severity: 'low', dry_run: true },
}

async function main() {
  const transport = new StreamableHTTPClientTransport(
    new URL(`${MCP_URL}/mcp`),
    { requestInit: { headers: { Authorization: `Bearer ${MCP_KEY}` } } }
  )
  const client = new Client({ name: 'probe', version: '1.0' })
  await client.connect(transport)

  for (const [tool, args] of Object.entries(FAILING)) {
    const r = await client.callTool({ name: tool, arguments: args }) as any
    const text = r.content?.[0]?.text ?? ''
    console.log(`\n=== ${tool} ===`)
    console.log(text.slice(0, 600))
  }
  await client.close()
}

main().catch(console.error)
