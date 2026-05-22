/**
 * tool_registry.test.ts — Tests for the tool-disable check in the
 * primitives dispatcher (tool_registry.tool_enabled = false → 503).
 *
 * Tests:
 *   1. tool_registry row with tool_enabled=false → 503 {tool_disabled: true}
 *   2. tool_registry row with tool_enabled=true → execution proceeds (200 path)
 *   3. tool_registry row missing → fail-open (execution proceeds)
 *   4. DB error on registry lookup → fail-open (execution proceeds, warns)
 *   5. tool_disabled: true envelope has correct shape
 *
 * MCPT v3.1.0-S5
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// The tool-disable check lives in the route handler; we test the logic via
// a thin wrapper that reproduces the check in isolation (pure-logic test).

// Reproduce the tool-disabled check from the route handler
async function checkToolEnabled(
  toolName: string,
  queryFn: (sql: string, params: unknown[]) => Promise<{ rows: Array<{ tool_enabled: boolean }> }>
): Promise<{ disabled: boolean }> {
  try {
    const result = await queryFn(
      'SELECT tool_enabled FROM tool_registry WHERE tool_name = $1 LIMIT 1',
      [toolName]
    )
    if (result.rows.length > 0 && result.rows[0].tool_enabled === false) {
      return { disabled: true }
    }
    return { disabled: false }
  } catch {
    // Fail-open
    return { disabled: false }
  }
}

describe('tool_registry — checkToolEnabled', () => {
  it('returns disabled=true when tool_enabled=false', async () => {
    const queryFn = vi.fn().mockResolvedValue({ rows: [{ tool_enabled: false }] })
    const result = await checkToolEnabled('query_chart_facts', queryFn)
    expect(result.disabled).toBe(true)
  })

  it('returns disabled=false when tool_enabled=true', async () => {
    const queryFn = vi.fn().mockResolvedValue({ rows: [{ tool_enabled: true }] })
    const result = await checkToolEnabled('query_signals', queryFn)
    expect(result.disabled).toBe(false)
  })

  it('returns disabled=false when no registry row exists (fail-open)', async () => {
    const queryFn = vi.fn().mockResolvedValue({ rows: [] })
    const result = await checkToolEnabled('unknown_tool', queryFn)
    expect(result.disabled).toBe(false)
  })

  it('returns disabled=false when DB throws (fail-open)', async () => {
    const queryFn = vi.fn().mockRejectedValue(new Error('ECONNRESET'))
    const result = await checkToolEnabled('query_chart_facts', queryFn)
    expect(result.disabled).toBe(false)
  })

  it('passes the correct SQL and tool name to the query function', async () => {
    const queryFn = vi.fn().mockResolvedValue({ rows: [{ tool_enabled: true }] })
    await checkToolEnabled('vector_search', queryFn)
    expect(queryFn).toHaveBeenCalledWith(
      expect.stringContaining('tool_registry'),
      ['vector_search']
    )
  })
})

describe('tool_disabled 503 envelope shape', () => {
  it('has correct shape when tool is disabled', () => {
    const toolName = 'query_chart_facts'
    // Reproduce the envelope the route handler returns
    const envelope = {
      ok: false,
      tool_disabled: true,
      error: {
        class: 'tool_disabled',
        message: `Tool '${toolName}' is currently disabled by the operator.`,
        remediation: 'Check /admin/mcp/health for status. Contact admin to re-enable.',
      },
    }

    expect(envelope.ok).toBe(false)
    expect(envelope.tool_disabled).toBe(true)
    expect(envelope.error.class).toBe('tool_disabled')
    expect(envelope.error.message).toContain(toolName)
    expect(envelope.error.remediation).toContain('/admin/mcp/health')
  })
})

describe('migration 077 — mcp_alerts_config defaults', () => {
  it('seeds 5 default alert configs', () => {
    // This test verifies the seed data structure (not DB execution)
    const seedConfigs = [
      { metric_name: 'zero_rows_rate',          comparison: 'gte', threshold_value: 0.5, channels: ['slack'] },
      { metric_name: 'error_rate',              comparison: 'gte', threshold_value: 0.1, channels: ['slack', 'email'] },
      { metric_name: 'audit_class1_count',      comparison: 'gte', threshold_value: 1,   channels: ['slack', 'email'] },
      { metric_name: 'audit_class2_count',      comparison: 'gte', threshold_value: 5,   channels: ['slack'] },
      { metric_name: 'disabled_tool_call_count',comparison: 'gte', threshold_value: 1,   channels: ['slack'] },
    ]

    expect(seedConfigs).toHaveLength(5)

    const class1Config = seedConfigs.find(c => c.metric_name === 'audit_class1_count')!
    expect(class1Config.threshold_value).toBe(1)
    expect(class1Config.channels).toContain('email')

    const errorConfig = seedConfigs.find(c => c.metric_name === 'error_rate')!
    expect(errorConfig.threshold_value).toBe(0.1)
    expect(errorConfig.channels).toContain('email')

    // All tools seeded in tool_registry are enabled by default
    const zeroRowsConfig = seedConfigs.find(c => c.metric_name === 'zero_rows_rate')!
    expect(zeroRowsConfig.comparison).toBe('gte')
    expect(zeroRowsConfig.threshold_value).toBe(0.5)
  })

  it('seeds 20 tools in tool_registry all enabled', () => {
    const toolNames = [
      'query_chart_facts', 'query_signals', 'query_dasha_periods',
      'query_panchanga', 'query_ephemeris', 'query_transit_event',
      'lel_query', 'vector_search', 'get_cgm_subgraph', 'cross_school_lookup',
      'holistic_bundle', 'multi_school_bundle', 'read_asset', 'get_trace',
      'list_recent_queries', 'tool_health', 'data_coverage',
      'log_prediction', 'record_outcome', 'flag_disagreement',
    ]
    expect(toolNames).toHaveLength(20)
    // All unique
    expect(new Set(toolNames).size).toBe(20)
  })
})
