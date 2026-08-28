/**
 * S4 Stage S1 investigation script — cross-door parity, latency bench, and adversarial-ambiguity probe.
 * Run: npx tsx .s4_scratch/s1_parity_and_bench.ts   (from platform-mcp/, using its tsx+deps for zod resolution
 *      via platform/node_modules since Portal file imports 'zod')
 *
 * Imports BOTH doors' classifiers directly (unit-level function calls = REPLAY/INTEGRATION rung).
 */
import { classifyScope as mcpClassify } from '../platform-mcp/src/tools/intent_scope_classifier.ts'
import { classifyScope as portalClassify } from '../platform/src/lib/vidhi/scope_classifier.ts'

const CHART_ID_NATIVE_FAMILY = '1c826d5a-41cb-4450-b4dc-59d440e5f75a' // synthetic test chart ONLY

// ── Representative query set for cross-door parity ──────────────────────────
const PARITY_QUERIES: string[] = [
  'What dasha am I running now?',
  'Where is Saturn transiting currently?',
  'Do I have a Gaja Kesari yoga?',
  'What is the Shadbala of my Jupiter?',
  'Analyze my 10th house lord',
  'What remedy should I do for Saturn?',
  'What is my birth nakshatra and tithi?',
  'What does BPHS say about the 8th lord?',
  'Give me a full reading of my chart',
  'Was my last prediction accurate?',
  'Assess my career prospects',
  'What sign is my Moon in?',                     // Ω4 narrow-pinpoint case (MCP only)
  'What is my career direction and its timing over the next few years?', // W6.1 domain-inferred fix (Portal only)
  'What is my finances outlook?',                  // plural "finances" — F-24 fix (MCP only)
  'Are there any surgeries indicated for my health?', // plural "surgeries"
  'What are my relationships prospects?',          // plural "relationships"
  'hey there, can you help me out with something?', // genuinely ambiguous — both should flag fallback
  'asdfqwer zxcv',                                  // gibberish
  '',                                                // empty
]

console.log('='.repeat(100))
console.log('PARITY CHECK — MCP intent_scope_classifier.ts  vs  Portal scope_classifier.ts')
console.log('='.repeat(100))

let divergences = 0
for (const q of PARITY_QUERIES) {
  const mcp = mcpClassify(q)
  const portal = portalClassify(q)
  const mcpT = mcp.scope_tuple
  const portalT = portal.scope_tuple
  const fieldsToCompare: Array<[string, unknown, unknown]> = [
    ['intent', mcpT.intent, portalT.intent],
    ['domains', JSON.stringify(mcpT.domains), JSON.stringify(portalT.domains)],
    ['width', mcpT.width, portalT.width],
    ['depth', mcpT.depth, portalT.depth],
    ['horizon', mcpT.horizon, portalT.horizon],
    ['intervention', mcpT.intervention, portalT.intervention],
    ['entitlement', mcpT.entitlement, portalT.entitlement],
    ['fallback_recommended', mcp.fallback_recommended, portal.fallback_recommended],
  ]
  const diffs = fieldsToCompare.filter(([, a, b]) => a !== b)
  console.log(`\nQ: ${JSON.stringify(q)}`)
  console.log(`  MCP    : intent=${mcpT.intent} domains=${JSON.stringify(mcpT.domains)} width=${mcpT.width} depth=${mcpT.depth} horizon=${mcpT.horizon} interv=${mcpT.intervention} ent=${mcpT.entitlement} fb=${mcp.fallback_recommended} route=${(mcp as any).route}`)
  console.log(`  Portal : intent=${portalT.intent} domains=${JSON.stringify(portalT.domains)} width=${portalT.width} depth=${portalT.depth} horizon=${portalT.horizon} interv=${portalT.intervention} ent=${portalT.entitlement} fb=${portal.fallback_recommended}`)
  if (diffs.length > 0) {
    divergences++
    console.log(`  >>> DIVERGE on: ${diffs.map(([f, a, b]) => `${f}(mcp=${a} vs portal=${b})`).join(', ')}`)
  } else {
    console.log('  MATCH')
  }
}
console.log(`\nTOTAL divergences: ${divergences} / ${PARITY_QUERIES.length} queries`)

// ── Adversarial ambiguity probe — should NOT auto-resolve to a confident guess ──
console.log('\n' + '='.repeat(100))
console.log('ADVERSARIAL AMBIGUITY PROBE')
console.log('='.repeat(100))
const ADVERSARIAL: string[] = [
  'tell me about it',
  'what about the thing we discussed',
  'is it good or bad',
  'more please',
  'yes',
  'go on',
]
for (const q of ADVERSARIAL) {
  const mcp = mcpClassify(q)
  const portal = portalClassify(q)
  console.log(`Q: ${JSON.stringify(q)}`)
  console.log(`  MCP    : intent=${mcp.scope_tuple.intent} confidence=${mcp.confidence} fallback_recommended=${mcp.fallback_recommended}`)
  console.log(`  Portal : intent=${portal.scope_tuple.intent} confidence=${portal.confidence} fallback_recommended=${portal.fallback_recommended}`)
}

// ── Latency bench (p95 over N invocations) ──────────────────────────────────
console.log('\n' + '='.repeat(100))
console.log('LATENCY BENCH')
console.log('='.repeat(100))

function bench(name: string, fn: (q: string) => unknown, n: number): void {
  const queries = PARITY_QUERIES.filter((q) => q.length > 0)
  const durations: number[] = []
  // warmup
  for (let i = 0; i < 5; i++) fn(queries[i % queries.length])
  for (let i = 0; i < n; i++) {
    const q = queries[i % queries.length]
    const t0 = performance.now()
    fn(q)
    const t1 = performance.now()
    durations.push(t1 - t0)
  }
  durations.sort((a, b) => a - b)
  const p50 = durations[Math.floor(durations.length * 0.5)]
  const p95 = durations[Math.floor(durations.length * 0.95)]
  const max = durations[durations.length - 1]
  const mean = durations.reduce((a, b) => a + b, 0) / durations.length
  console.log(`${name}: n=${n} mean=${mean.toFixed(4)}ms p50=${p50.toFixed(4)}ms p95=${p95.toFixed(4)}ms max=${max.toFixed(4)}ms`)
}

bench('MCP    classifyScope', mcpClassify, 200)
bench('Portal classifyScope', portalClassify, 200)

// ── Clarification-trigger precision — positive + negative direction ─────────
console.log('\n' + '='.repeat(100))
console.log('CLARIFICATION-TRIGGER PRECISION (both directions)')
console.log('='.repeat(100))

const SHOULD_CLARIFY: string[] = [
  'hey there, can you help me out with something?',
  'asdfqwer zxcv',
  '',
  'tell me about it',
  'is it good or bad',
]
const SHOULD_NOT_CLARIFY: string[] = [
  'What dasha am I running now?',
  'Assess my career prospects',
  'What remedy should I do for Saturn?',
  'Give me a full reading of my chart',
  'What is my wealth outlook?',
]

function precisionReport(label: string, queries: string[], expectClarify: boolean, fn: (q: string) => { fallback_recommended: boolean }): void {
  let correct = 0
  for (const q of queries) {
    const r = fn(q)
    const got = r.fallback_recommended
    const ok = got === expectClarify
    if (ok) correct++
    console.log(`  [${ok ? 'OK' : 'FAIL'}] "${q}" -> fallback_recommended=${got} (expected ${expectClarify})`)
  }
  console.log(`${label}: ${correct}/${queries.length} correct`)
}

console.log('\n-- MCP classifier --')
precisionReport('MCP  should-clarify (positive)', SHOULD_CLARIFY, true, mcpClassify)
precisionReport('MCP  should-NOT-clarify (negative)', SHOULD_NOT_CLARIFY, false, mcpClassify)

console.log('\n-- Portal classifier --')
precisionReport('Portal  should-clarify (positive)', SHOULD_CLARIFY, true, portalClassify)
precisionReport('Portal  should-NOT-clarify (negative)', SHOULD_NOT_CLARIFY, false, portalClassify)

console.log(`\nCHART ANCHOR (never queried live, referenced only as classifier input for entitlement logic): ${CHART_ID_NATIVE_FAMILY}`)
