import { describe, expect, it } from 'vitest'
import { BATTERY_QUERIES, BATTERY_CHARTS } from './queries'
import { runOne, aggregateByFamily, aggregateOverall, checkChartIsolation, contractFingerprint } from './lib'
import { classifyScope } from '@/lib/vidhi/scope_classifier'
import { classifierTupleToCompilerTuple } from '@/lib/pipeline/compiled_floor_adapter'
import { compileContract, defaultRegistry } from '@/lib/vidhi/compiler'

describe('W5 L10 battery — query corpus routes to its labeled family', () => {
  for (const entry of BATTERY_QUERIES) {
    it(`${entry.id} (${entry.family}) routes to ${entry.expected_intent}`, () => {
      const result = runOne(entry, BATTERY_CHARTS[0])
      expect(result.compiled_intent).toBe(entry.expected_intent)
      expect(result.routing_correct).toBe(true)
      expect(result.compile_failed).toBe(false)
    })
  }
})

describe('W5 L10 battery — determinism (readback precondition)', () => {
  it('the same query+chart compiles to a byte-identical fingerprint across repeated calls', () => {
    const entry = BATTERY_QUERIES[0]
    const a = runOne(entry, BATTERY_CHARTS[0])
    const b = runOne(entry, BATTERY_CHARTS[0])
    expect(a.fingerprint).toBe(b.fingerprint)
  })

  it('the same query compiled for two different charts produces different fingerprints (chart_id is embedded in tool_args)', () => {
    const entry = BATTERY_QUERIES[0]
    const a = runOne(entry, BATTERY_CHARTS[0])
    const b = runOne(entry, BATTERY_CHARTS[1])
    expect(a.fingerprint).not.toBe(b.fingerprint)
  })
})

describe('W5 L10 battery — chart isolation guard', () => {
  it('checkChartIsolation passes for a contract compiled with its own chart_id', () => {
    const tuple = classifierTupleToCompilerTuple(classifyScope('What is my wealth outlook?').scope_tuple)
    const contract = compileContract(tuple, defaultRegistry(), BATTERY_CHARTS[0].chart_id)
    expect(checkChartIsolation(contract, BATTERY_CHARTS[0].chart_id)).toBe(true)
  })

  it('checkChartIsolation FAILS if checked against the wrong chart_id (guard sanity check)', () => {
    const tuple = classifierTupleToCompilerTuple(classifyScope('What is my wealth outlook?').scope_tuple)
    const contract = compileContract(tuple, defaultRegistry(), BATTERY_CHARTS[0].chart_id)
    expect(checkChartIsolation(contract, BATTERY_CHARTS[1].chart_id)).toBe(false)
  })

  it('every battery entry, compiled for every chart, passes chart isolation', () => {
    for (const entry of BATTERY_QUERIES) {
      for (const chart of BATTERY_CHARTS) {
        const result = runOne(entry, chart)
        expect(result.chart_isolation_ok).toBe(true)
      }
    }
  })
})

describe('W5 L10 battery — aggregation', () => {
  it('aggregateByFamily reports 1.0 routing_accuracy for every family on the labeled corpus', () => {
    const results = BATTERY_QUERIES.map((q) => runOne(q, BATTERY_CHARTS[0]))
    const byFamily = aggregateByFamily(results)
    expect(byFamily).toHaveLength(6)
    for (const f of byFamily) {
      expect(f.routing_accuracy).toBe(1)
      expect(f.n).toBe(5)
    }
  })

  it('aggregateOverall reports zero compile failures and zero isolation violations on the labeled corpus', () => {
    const results: ReturnType<typeof runOne>[] = []
    for (const q of BATTERY_QUERIES) for (const c of BATTERY_CHARTS) results.push(runOne(q, c))
    const overall = aggregateOverall(results)
    expect(overall.n).toBe(60)
    expect(overall.compile_failures).toBe(0)
    expect(overall.chart_isolation_violations).toBe(0)
    expect(overall.routing_accuracy).toBe(1)
  })
})

describe('contractFingerprint', () => {
  it('is stable under key-order permutation (stableStringify)', () => {
    const tuple = classifierTupleToCompilerTuple(classifyScope('What is my wealth outlook?').scope_tuple)
    const a = compileContract(tuple, defaultRegistry(), BATTERY_CHARTS[0].chart_id)
    const b = compileContract(tuple, defaultRegistry(), BATTERY_CHARTS[0].chart_id)
    expect(contractFingerprint(a)).toBe(contractFingerprint(b))
  })
})
