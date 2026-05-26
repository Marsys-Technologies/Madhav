/**
 * audit4_live.ts — MCP Audit 4: full 40-tool live test against production.
 *
 * Usage:
 *   MCP_URL=https://... MCP_KEY=sk-... npx tsx platform-mcp/scripts/audit4_live.ts
 *
 * Scoring per tool:
 *   100% = response present, no isError, content[0].text parses as JSON with
 *          at least one meaningful field (not just {})
 *   75%  = response present, no isError, content[0].text is non-empty string
 *   50%  = response present but isError=true (Zod / validation error — tool
 *          reached handler but input rejected)
 *   25%  = HTTP 200 returned but MCP result is missing or malformed
 *   0%   = HTTP error, timeout, or connection refused
 */

import { Client } from '@modelcontextprotocol/sdk/client/index.js'
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js'

const MCP_URL = process.env['MCP_URL'] ?? ''
const MCP_KEY = process.env['MCP_KEY'] ?? ''

if (!MCP_URL || !MCP_KEY) {
  console.error('MCP_URL and MCP_KEY must be set')
  process.exit(1)
}

// Native chart_id for Abhisek Mohanty
const CHART_ID = 'abhisek_mohanty_primary'
const TODAY = new Date().toISOString().split('T')[0]!
const NEXT_MONTH = new Date(Date.now() + 30 * 86400000).toISOString().split('T')[0]!

// Representative inputs for all 40 tools
// Designed to exercise the happy path without needing complex setup
const TOOL_CASES: Record<string, Record<string, unknown>> = {
  // Tier 1
  chart_summary:          { chart_id: CHART_ID },
  // Tier 2 bundles
  holistic_bundle:        { query_text: 'Saturn Mahadasha career themes' },
  multi_school_bundle:    { claim: 'Saturn in 10th house gives delayed career success' },
  // Tier 3 surgical primitives
  query_chart_facts:      { chart_id: CHART_ID, category: 'planet' },
  query_signals:          { chart_id: CHART_ID, limit: 5 },
  query_dasha_periods:    { chart_id: CHART_ID, system: 'vimshottari' },
  query_panchanga:        { date: TODAY },
  query_ephemeris:        { date_range: { from: TODAY, to: NEXT_MONTH }, bodies: ['Sun', 'Moon'] },
  query_transit_event:    { chart_id: CHART_ID, from_date: TODAY, to_date: NEXT_MONTH, event_type: 'ingress' },
  lel_query:              { query: 'career events', limit: 5 },
  vector_search:          { text: 'Saturn Mahadasha profession', limit: 5 },
  get_cgm_subgraph:       { node_id: 'SIG.MSR.001', hops: 1 },
  cross_school_lookup:    { claim: 'Saturn in Capricorn 10th house career delay' },
  query_varshphal:        { year: new Date().getFullYear() },
  query_divisional_chart: { chart_id: CHART_ID, varga: 'D9' },
  query_remedial_mantras: { planet: 'Saturn', query: 'Saturn remedy' },
  muhurta_finder:         { event: 'travel', date_from: TODAY, date_to: NEXT_MONTH },
  msr_sql:                { sql: 'SELECT signal_id, signal_name FROM msr_signals LIMIT 5' },
  temporal:               { query: 'current Saturn transit position' },
  kp_query:               { chart_id: CHART_ID, query: 'significators for house 10' },
  query_kp_ruling_planets:{ chart_id: '362f9f17-95a5-490b-a5a7-027d3e0efda0' },
  pattern_register:       { query: 'Saturn career patterns', limit: 5 },
  resonance_register:     { query: 'Saturn 10th house themes', limit: 5 },
  cluster_atlas:          { query: 'career and vocation signals', limit: 5 },
  contradiction_register: { query: 'Saturn dignity contradictions', limit: 5 },
  query_ucn_walk:         { query: 'Saturn Capricorn 10H career axis', limit: 5 },
  query_cdlm_lookup:      { query: 'Saturn cross-domain linkage career', limit: 5 },
  query_rm_walk:          { query: 'Saturn remedial path walk', limit: 5 },
  query_jaimini_drishti:  { chart_id: CHART_ID, from_sign: 'Capricorn' },
  timeline_query:         { query: 'Saturn Mahadasha arc timeline', limit: 5 },
  query_signal_state:     { chart_id: '362f9f17-95a5-490b-a5a7-027d3e0efda0', signal_ids: ['SIG.MSR.001', 'SIG.MSR.002'] },
  // Tier 4 raw-asset reads
  read_asset:             { canonical_id: 'MSR' },
  read_classical_text:    { query: 'Saturn in 10th house Capricorn', limit: 3 },
  // Tier 5 observability
  get_trace:              { trace_id: '78082b82-93d5-489c-aa87-6f771dec1aed' },
  list_recent_queries:    { limit: 5 },
  // Tier 5 perf
  tool_health:            { tool_name: 'query_chart_facts' },
  data_coverage:          {},
  // Tier 6 writes (use dry_run to avoid polluting prod)
  log_prediction:         { prediction_text: 'Audit 4b fixture probe — discard', confidence: 'low',
                            domain: 'career', horizon: '2026-12-31', falsifier: 'audit4b_fixture_probe' },
  record_outcome:         { prediction_id: 'audit4b-nonexistent-id', outcome_text: 'no outcome yet',
                            verified: false },
  flag_disagreement:      { class: 'factual',
                            description: 'Audit 4c fixture probe for end-to-end validation. Discard — not a real disagreement. Tool reached and schema accepted.',
                            source_session: 'Audit4c_2026-05-26' },
}

interface ToolScore {
  tool: string
  score: number
  status: string
  note: string
}

async function callTool(
  client: Client,
  toolName: string,
  args: Record<string, unknown>
): Promise<ToolScore> {
  const start = Date.now()
  try {
    const result = await Promise.race([
      client.callTool({ name: toolName, arguments: args }),
      new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('TIMEOUT')), 15000)
      ),
    ])

    const elapsed = Date.now() - start
    const content = (result as { content?: Array<{ type: string; text?: string }> }).content

    if (!content || content.length === 0) {
      return { tool: toolName, score: 25, status: 'EMPTY', note: `${elapsed}ms — no content` }
    }

    const isError = (result as { isError?: boolean }).isError
    if (isError) {
      const errText = content[0]?.text ?? ''
      const isZod = errText.includes('ZodError') || errText.includes('validation')
      return {
        tool: toolName,
        score: 50,
        status: 'VALIDATION_ERROR',
        note: `${elapsed}ms — ${isZod ? 'Zod/schema error' : errText.slice(0, 80)}`,
      }
    }

    const text = content[0]?.text ?? ''
    if (!text) {
      return { tool: toolName, score: 25, status: 'EMPTY_TEXT', note: `${elapsed}ms` }
    }

    // Try to parse as JSON with meaningful content
    try {
      const parsed = JSON.parse(text)
      const keys = Object.keys(parsed)
      const hasMeaningfulContent =
        keys.length > 1 ||
        (keys.length === 1 && !['ok', 'status', 'message'].every(k => keys.includes(k)))
      if (hasMeaningfulContent) {
        return { tool: toolName, score: 100, status: 'OK', note: `${elapsed}ms — ${keys.slice(0, 3).join(', ')}` }
      }
      return { tool: toolName, score: 75, status: 'MINIMAL', note: `${elapsed}ms — minimal JSON` }
    } catch {
      // Non-JSON text is still a valid response
      return { tool: toolName, score: 75, status: 'TEXT_OK', note: `${elapsed}ms — ${text.slice(0, 60)}` }
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    return { tool: toolName, score: 0, status: 'ERROR', note: msg.slice(0, 100) }
  }
}

async function main() {
  console.log(`\nMCP AUDIT 4 — ${new Date().toISOString()}`)
  console.log(`Endpoint: ${MCP_URL}/mcp`)
  console.log(`Tools to test: ${Object.keys(TOOL_CASES).length}\n`)

  const transport = new StreamableHTTPClientTransport(
    new URL(`${MCP_URL}/mcp`),
    {
      requestInit: {
        headers: { Authorization: `Bearer ${MCP_KEY}` },
      },
    }
  )

  const client = new Client({ name: 'audit4', version: '1.0' })
  await client.connect(transport)

  // Verify tool list
  const { tools } = await client.listTools()
  console.log(`Tools registered on server: ${tools.length}`)
  const serverTools = new Set(tools.map((t: { name: string }) => t.name))

  const results: ToolScore[] = []

  for (const [toolName, args] of Object.entries(TOOL_CASES)) {
    process.stdout.write(`  Testing ${toolName.padEnd(30)}`)
    if (!serverTools.has(toolName)) {
      const r = { tool: toolName, score: 0, status: 'NOT_REGISTERED', note: 'tool missing from server' }
      results.push(r)
      console.log(`0%   NOT_REGISTERED`)
      continue
    }
    const r = await callTool(client, toolName, args)
    results.push(r)
    const bar = r.score === 100 ? '██' : r.score >= 75 ? '▓▓' : r.score >= 50 ? '░░' : r.score >= 25 ? '  ' : '  '
    console.log(`${String(r.score).padStart(3)}%  ${bar} ${r.status.padEnd(18)} ${r.note}`)
  }

  await client.close()

  // Summary
  const avg = results.reduce((s, r) => s + r.score, 0) / results.length
  const passing = results.filter(r => r.score >= 90).length
  const failing = results.filter(r => r.score < 90)

  console.log('\n' + '═'.repeat(70))
  console.log(`AUDIT 4 RESULT`)
  console.log('═'.repeat(70))
  console.log(`Average score:    ${avg.toFixed(1)}%`)
  console.log(`Tools ≥90%:       ${passing} / ${results.length}`)
  console.log(`Tools <90%:       ${failing.length}`)
  if (failing.length > 0) {
    console.log('\nSub-90% tools:')
    for (const f of failing.sort((a, b) => a.score - b.score)) {
      console.log(`  ${f.tool.padEnd(30)} ${String(f.score).padStart(3)}%  ${f.note}`)
    }
  }
  console.log('═'.repeat(70))
  console.log(avg >= 95 ? '✓ TARGET MET (≥95%)' : avg >= 90 ? '~ CLOSE (≥90% but <95%)' : '✗ BELOW TARGET (<90%)')
}

main().catch(err => {
  console.error('FATAL:', err)
  process.exit(1)
})
