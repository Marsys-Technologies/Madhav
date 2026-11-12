import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import ts from 'typescript'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import * as legacy from '@/lib/charts/readiness'
import * as legacyImpact from '@/lib/charts/servingImpact'
import * as model from '../model'
import { getChartReadinessMap } from '../repository'
import * as impact from '../servingImpact'

const CHART_A = 'c0000000-0000-4000-8000-000000000001'
const CHART_B = 'c0000000-0000-4000-8000-000000000002'

const EXPECTED_SQL = [
  `SELECT at.chart_id, at.asset_id, at.state, at.rows_written, at.last_built_at
         FROM asset_throughput at
         JOIN asset_registry ar ON ar.asset_id = at.asset_id AND ar.is_active = true
        WHERE at.chart_id = ANY($1::uuid[])`,
  `SELECT l.*,
              ARRAY(SELECT bra.asset_id FROM build_run_assets bra WHERE bra.run_id = l.id ORDER BY bra.position) AS planned_assets
         FROM (
           SELECT DISTINCT ON (r.chart_id)
                  r.id, r.chart_id, r.state, r.scope, r.action, r.last_error, r.created_at, r.started_at, r.ended_at
             FROM build_runs r
            WHERE r.chart_id = ANY($1::uuid[])
            ORDER BY r.chart_id, r.created_at DESC, r.id DESC
         ) l`,
  `SELECT r.chart_id,
              COUNT(DISTINCT bra.asset_id)::int AS assets,
              COALESCE(bool_or(r.last_error LIKE 'JOB_DISPATCH_FAILED%'), false) AS dispatch_failed
         FROM build_runs r
         JOIN build_run_assets bra ON bra.run_id = r.id
         JOIN asset_registry ar ON ar.asset_id = bra.asset_id AND ar.is_active = true AND ar.scope = 'per_chart'
         LEFT JOIN asset_throughput at ON at.chart_id = r.chart_id AND at.asset_id = bra.asset_id
        WHERE r.chart_id = ANY($1::uuid[])
          AND r.state IN ('failed', 'stopped')
          AND NOT COALESCE(
                at.state = 'lit'
                AND (NOT (r.scope = 'global' AND r.action = 'rebuild') OR at.last_built_at >= r.created_at),
                false)
        GROUP BY r.chart_id`,
]

function pureDependencyErrors(name: string, source: string): string[] {
  const allowed: Record<string, readonly string[]> = {
    'model.ts': ['@/lib/brahma/lexicon', './servingImpact', './types'],
    'types.ts': ['@/lib/brahma/lexicon'],
    'servingImpact.ts': [],
    'lexicon.ts': [],
  }
  const parsed = ts.createSourceFile(name, source, ts.ScriptTarget.Latest, true)
  const errors: string[] = []
  function visit(node: ts.Node) {
    if (ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) {
      const target = node.moduleSpecifier
      if (target && (!ts.isStringLiteral(target) || !allowed[name]?.includes(target.text))) {
        errors.push('dependency outside pure readiness closure')
      }
    }
    if (ts.isCallExpression(node) && (
      node.expression.kind === ts.SyntaxKind.ImportKeyword ||
      (ts.isIdentifier(node.expression) && ['require', 'eval'].includes(node.expression.text))
    )) errors.push('dynamic dependency in pure readiness closure')
    ts.forEachChild(node, visit)
  }
  visit(parsed)
  return errors
}

beforeEach(() => {
  mockQuery.mockReset()
})

describe('Build readiness owners and compatibility exports', () => {
  it('preserves the exact function and mutable constant identities through both shims', () => {
    expect(legacy.deriveChartReadiness).toBe(model.deriveChartReadiness)
    expect(legacy.emptyChartReadiness).toBe(model.emptyChartReadiness)
    expect(legacy.isDerivedChartReady).toBe(model.isDerivedChartReady)
    expect(legacy.getChartReadinessMap).toBe(getChartReadinessMap)
    expect(legacy.CHART_READINESS_LABELS).toBe(model.CHART_READINESS_LABELS)
    expect(legacy.JOB_DISPATCH_FAILED_PREFIX).toBe(model.JOB_DISPATCH_FAILED_PREFIX)
    expect(legacyImpact.NON_SERVING_RECALIBRATION_ASSETS).toBe(impact.NON_SERVING_RECALIBRATION_ASSETS)
    expect(legacyImpact.runBlocksReadings).toBe(impact.runBlocksReadings)

    const labels = legacy.CHART_READINESS_LABELS
    const previous = labels['not-built']
    try {
      labels['not-built'] = 'Synthetic alias witness'
      expect(model.emptyChartReadiness().label).toBe('Synthetic alias witness')
    } finally {
      labels['not-built'] = previous
    }
    const assets = legacyImpact.NON_SERVING_RECALIBRATION_ASSETS as Set<string>
    try {
      assets.add('synthetic_alias_witness')
      expect(impact.runBlocksReadings({ scope: 'asset', planned_assets: ['synthetic_alias_witness'] })).toBe(false)
    } finally {
      assets.delete('synthetic_alias_witness')
    }
  })

  it('keeps the model, public types and policy client-safe without a Build to roster dependency', () => {
    const sources: Record<string, string> = {
      'model.ts': readFileSync(join(__dirname, '../model.ts'), 'utf8'),
      'types.ts': readFileSync(join(__dirname, '../types.ts'), 'utf8'),
      'servingImpact.ts': readFileSync(join(__dirname, '../servingImpact.ts'), 'utf8'),
      'lexicon.ts': readFileSync(join(__dirname, '../../../brahma/lexicon.ts'), 'utf8'),
    }
    for (const [name, source] of Object.entries(sources)) {
      expect(pureDependencyErrors(name, source)).toEqual([])
    }
    for (const dependency of ['server-only', '@/lib/db/client', '@/lib/roster/types']) {
      expect(pureDependencyErrors('model.ts', `import '${dependency}'`)).not.toEqual([])
      expect(pureDependencyErrors('model.ts', `export * from '${dependency}'`)).not.toEqual([])
    }
    expect(pureDependencyErrors('model.ts', "import('@/lib/db/client')")).not.toEqual([])
    expect(pureDependencyErrors('model.ts', "require('@/lib/roster/types')")).not.toEqual([])
  })
})

describe('Build readiness repository contract', () => {
  it('preserves all three exact queries, call order and bound chart-list identity before any result resolves', async () => {
    const ids = [CHART_B, CHART_A, CHART_B]
    const resolutions: Array<(value: { rows: unknown[] }) => void> = []
    mockQuery.mockImplementation(() => new Promise((resolve) => resolutions.push(resolve)))

    const pending = getChartReadinessMap(ids)
    expect(mockQuery.mock.calls.map(([sql]) => sql)).toEqual(EXPECTED_SQL)
    expect(resolutions).toHaveLength(3)
    for (const [, values] of mockQuery.mock.calls) {
      expect(values).toHaveLength(1)
      expect(values[0]).toBe(ids)
    }
    resolutions[0]({ rows: [{ chart_id: CHART_A, asset_id: 'ga_positions', state: 'lit', rows_written: 0, last_built_at: '2026-01-01T00:00:00Z' }] })
    resolutions[1]({ rows: [{ chart_id: CHART_B, id: 'synthetic-run', state: 'running', scope: 'global', action: 'rebuild', last_error: null }] })
    resolutions[2]({ rows: [] })
    const result = await pending
    expect([...result.keys()]).toEqual([CHART_B, CHART_A])
    expect(result.get(CHART_A)).toEqual(model.deriveChartReadiness({
      throughput: [{ asset_id: 'ga_positions', state: 'lit', rows_written: 0, last_built_at: '2026-01-01T00:00:00Z' }],
      latestRun: null,
      unresolvedFailure: { assets: 0, dispatchFailed: false },
    }))
    expect(result.get(CHART_B)?.state).toBe('building')
  })

  it('does not query for an empty chart-list', async () => {
    expect(await getChartReadinessMap([])).toEqual(new Map())
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it.each([0, 1, 2])('propagates query %i rejection unchanged after initiating every batch read', async (failingQuery) => {
    const failure = new Error(`synthetic-query-${failingQuery}`)
    let call = 0
    mockQuery.mockImplementation(() => call++ === failingQuery ? Promise.reject(failure) : Promise.resolve({ rows: [] }))
    await expect(getChartReadinessMap([CHART_A])).rejects.toBe(failure)
    expect(mockQuery.mock.calls.map(([sql]) => sql)).toEqual(EXPECTED_SQL)
  })
})
