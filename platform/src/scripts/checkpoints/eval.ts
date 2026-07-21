/**
 * MARSYS-JIS Phase 6 — Checkpoint offline accuracy evaluator
 *
 * Runs all three checkpoints against small hand-labeled example sets and
 * reports per-checkpoint accuracy. Pass rate ≥80% (4.5, 5.5) and ≥75% (8.5
 * prediction extraction) required before flag-flip.
 *
 * Usage:  npm run checkpoint:eval
 *
 * Environment requirements:
 *   ANTHROPIC_API_KEY must be set (real LLM calls; not mocked).
 *   All three CHECKPOINT_*_ENABLED flags must be ON for calls to execute.
 */

import { configService } from '@/lib/config/index'
import { runCheckpoint4_5 } from '@/lib/checkpoints/checkpoint_4_5'
import { runCheckpoint5_5 } from '@/lib/checkpoints/checkpoint_5_5'
import { runCheckpoint8_5 } from '@/lib/checkpoints/checkpoint_8_5'
import type { CheckpointVerdict } from '@/lib/checkpoints/types'

// ── Enable all checkpoint flags for eval ──────────────────────────────────────

configService.setFlag('CHECKPOINT_4_5_ENABLED', true)
configService.setFlag('CHECKPOINT_5_5_ENABLED', true)
configService.setFlag('CHECKPOINT_8_5_ENABLED', true)
configService.setFlag('CHECKPOINT_8_5_PREDICTION_EXTRACT', true)

// ── Labeled examples ──────────────────────────────────────────────────────────

const basePlan = {
  query_plan_id: 'eval-plan',
  query_text: '',
  query_class: 'interpretive' as const,
  domains: ['career'],
  forward_looking: false,
  tools_authorized: ['msr_sql'],
  history_mode: 'synthesized' as const,
  panel_mode: false,
  expected_output_shape: 'three_interpretation' as const,
  manifest_fingerprint: 'fp-eval',
  schema_version: '1.0' as const,
}

const baseBundle = {
  bundle_id: 'eval-bundle',
  query_plan_reference: 'eval-plan',
  manifest_fingerprint: 'fp-eval',
  mandatory_context: [
    {
      canonical_id: 'FORENSIC',
      version: '8.0',
      content_hash: 'sha256:eval',
      token_count: 1000,
      role: 'floor' as const,
      source: 'rule_composer' as const,
    },
  ],
  total_tokens: 1000,
  bundle_hash: 'sha256:eval-bundle',
  schema_version: '1.0' as const,
}

interface LabeledExample<T> {
  label: string
  input: T
  expected_verdict: CheckpointVerdict
}

// Checkpoint 4.5: 10 labeled examples
const examples4_5: LabeledExample<Parameters<typeof runCheckpoint4_5>[0]>[] = [
  {
    label: '4.5-pass-01: clear career interpretive',
    input: {
      query: 'What does Saturn in 10th house indicate for my career?',
      query_plan: { ...basePlan, query_class: 'interpretive', domains: ['career'] },
    },
    expected_verdict: 'pass',
  },
  {
    label: '4.5-pass-02: predictive query correctly routed',
    input: {
      query: 'When will I change jobs?',
      query_plan: { ...basePlan, query_class: 'predictive', domains: ['career'], forward_looking: true },
    },
    expected_verdict: 'pass',
  },
  {
    label: '4.5-pass-03: holistic query routed holistic',
    input: {
      query: 'Give me a complete overview of my life patterns',
      query_plan: { ...basePlan, query_class: 'holistic', domains: ['career', 'relationships', 'health'] },
    },
    expected_verdict: 'pass',
  },
  {
    label: '4.5-warn-01: transit vs natal ambiguity',
    input: {
      query: 'What does the Sun in the 4th house mean right now?',
      query_plan: { ...basePlan, query_class: 'interpretive', domains: ['home'] },
      discarded_alternatives: ['transit_sun_4th_house'],
    },
    expected_verdict: 'warn',
  },
  {
    label: '4.5-warn-02: dasha ambiguity not flagged',
    input: {
      query: 'What is happening in my Jupiter period?',
      query_plan: { ...basePlan, query_class: 'interpretive', domains: ['career'] },
      discarded_alternatives: ['jupiter_MD', 'jupiter_AD'],
    },
    expected_verdict: 'warn',
  },
  {
    label: '4.5-pass-04: factual lookup clearly correct',
    input: {
      query: 'What is the position of my Ascendant?',
      query_plan: { ...basePlan, query_class: 'factual', domains: ['chart_basics'] },
    },
    expected_verdict: 'pass',
  },
  {
    label: '4.5-pass-05: remedial query correctly routed',
    input: {
      query: 'What remedies are recommended for Saturn?',
      query_plan: { ...basePlan, query_class: 'remedial', domains: ['remedies'] },
    },
    expected_verdict: 'pass',
  },
  {
    label: '4.5-pass-06: cross domain query',
    input: {
      query: 'How do my career and marriage intersect?',
      query_plan: { ...basePlan, query_class: 'cross_domain', domains: ['career', 'relationships'] },
    },
    expected_verdict: 'pass',
  },
  {
    label: '4.5-pass-07: discovery query',
    input: {
      query: 'What unusual patterns exist in my chart?',
      query_plan: { ...basePlan, query_class: 'discovery', domains: [] },
    },
    expected_verdict: 'pass',
  },
  {
    label: '4.5-warn-03: possible cross-native when only one routed',
    input: {
      query: 'How compatible are we?',
      query_plan: { ...basePlan, query_class: 'interpretive', domains: ['relationships'] },
      discarded_alternatives: ['cross_native_routing'],
    },
    expected_verdict: 'warn',
  },
]

// Checkpoint 5.5: 10 labeled examples
const examples5_5: LabeledExample<Parameters<typeof runCheckpoint5_5>[0]>[] = [
  {
    label: '5.5-pass-01: adequate floor + interpretive signals',
    input: {
      query: 'What does Saturn in 10th indicate?',
      query_plan: { ...basePlan, query_class: 'interpretive', domains: ['career'] },
      bundle: {
        ...baseBundle,
        mandatory_context: [
          { canonical_id: 'FORENSIC', version: '8.0', content_hash: 'sha256:a', token_count: 1000, role: 'floor' as const, source: 'rule_composer' as const },
          { canonical_id: 'MSR', version: '3.0', content_hash: 'sha256:b', token_count: 500, role: 'interpretive' as const, source: 'rule_composer' as const },
        ],
        total_tokens: 1500,
      },
      tool_results: [
        {
          tool_bundle_id: 'tb-01',
          tool_name: 'msr_sql',
          tool_version: '1.0',
          invocation_params: {},
          results: [{ content: 'Saturn career discipline signal', signal_id: 'MSR-042', confidence: 0.9, significance: 0.85 }],
          served_from_cache: false,
          latency_ms: 50,
          result_hash: 'sha256:tb01',
          schema_version: '1.0' as const,
        },
      ],
    },
    expected_verdict: 'pass',
  },
  {
    label: '5.5-pass-02: predictive with dasha signals',
    input: {
      query: 'When will career change occur?',
      query_plan: { ...basePlan, query_class: 'predictive', domains: ['career'], forward_looking: true },
      bundle: { ...baseBundle, total_tokens: 1200 },
      tool_results: [
        {
          tool_bundle_id: 'tb-02',
          tool_name: 'temporal',
          tool_version: '1.0',
          invocation_params: {},
          results: [{ content: 'Jupiter MD 2026-2042 career expansion window', signal_id: 'TEMPORAL-001', confidence: 0.85, significance: 0.9 }],
          served_from_cache: false,
          latency_ms: 60,
          result_hash: 'sha256:tb02',
          schema_version: '1.0' as const,
        },
      ],
    },
    expected_verdict: 'pass',
  },
  {
    label: '5.5-warn-01: cross-domain with only career signals',
    input: {
      query: 'How do career and relationships intersect?',
      query_plan: { ...basePlan, query_class: 'cross_domain', domains: ['career', 'relationships'] },
      bundle: { ...baseBundle, total_tokens: 1000 },
      tool_results: [
        {
          tool_bundle_id: 'tb-03',
          tool_name: 'msr_sql',
          tool_version: '1.0',
          invocation_params: {},
          results: [{ content: 'Saturn career signal only', signal_id: 'MSR-100', confidence: 0.9, significance: 0.8 }],
          served_from_cache: false,
          latency_ms: 45,
          result_hash: 'sha256:tb03',
          schema_version: '1.0' as const,
        },
      ],
    },
    expected_verdict: 'warn',
  },
  {
    label: '5.5-pass-03: holistic with multi-domain signals',
    input: {
      query: 'Give an overview of my life patterns',
      query_plan: { ...basePlan, query_class: 'holistic', domains: ['career', 'health', 'relationships'] },
      bundle: { ...baseBundle, total_tokens: 2000 },
      tool_results: [
        {
          tool_bundle_id: 'tb-04',
          tool_name: 'query_msr_aggregate',
          tool_version: '1.0',
          invocation_params: {},
          results: [
            { content: 'Career dharma pattern', signal_id: 'MSR-200', confidence: 0.9, significance: 0.85 },
            { content: 'Health vitality pattern', signal_id: 'MSR-201', confidence: 0.85, significance: 0.8 },
            { content: 'Relationship karma pattern', signal_id: 'MSR-202', confidence: 0.88, significance: 0.82 },
          ],
          served_from_cache: false,
          latency_ms: 100,
          result_hash: 'sha256:tb04',
          schema_version: '1.0' as const,
        },
      ],
    },
    expected_verdict: 'pass',
  },
  {
    label: '5.5-pass-04: factual with floor only',
    input: {
      query: 'What is my Ascendant?',
      query_plan: { ...basePlan, query_class: 'factual', domains: ['chart_basics'] },
      bundle: { ...baseBundle, total_tokens: 1000 },
      tool_results: [],
    },
    expected_verdict: 'pass',
  },
  {
    label: '5.5-pass-05: remedial with prescriptions',
    input: {
      query: 'What remedies for Saturn?',
      query_plan: { ...basePlan, query_class: 'remedial', domains: ['remedies'] },
      bundle: { ...baseBundle, total_tokens: 1100 },
      tool_results: [
        {
          tool_bundle_id: 'tb-05',
          tool_name: 'pattern_register',
          tool_version: '1.0',
          invocation_params: {},
          results: [{ content: 'Saturn remedy: wear blue sapphire, chant Shani mantra', signal_id: 'PAT-050', confidence: 0.8, significance: 0.75 }],
          served_from_cache: false,
          latency_ms: 55,
          result_hash: 'sha256:tb05',
          schema_version: '1.0' as const,
        },
      ],
    },
    expected_verdict: 'pass',
  },
  {
    label: '5.5-pass-06: interpretive with resonance signals',
    input: {
      query: 'What does Jupiter in the 9th house mean?',
      query_plan: { ...basePlan, query_class: 'interpretive', domains: ['spirituality'] },
      bundle: { ...baseBundle, total_tokens: 1200 },
      tool_results: [
        {
          tool_bundle_id: 'tb-06',
          tool_name: 'resonance_register',
          tool_version: '1.0',
          invocation_params: {},
          results: [{ content: 'Jupiter 9th house dharma expansion resonance', signal_id: 'RES-010', confidence: 0.92, significance: 0.88 }],
          served_from_cache: false,
          latency_ms: 48,
          result_hash: 'sha256:tb06',
          schema_version: '1.0' as const,
        },
      ],
    },
    expected_verdict: 'pass',
  },
  {
    label: '5.5-warn-02: predictive with no temporal signals',
    input: {
      query: 'When will I get married?',
      query_plan: { ...basePlan, query_class: 'predictive', domains: ['relationships'], forward_looking: true },
      bundle: { ...baseBundle, total_tokens: 1000 },
      tool_results: [
        {
          tool_bundle_id: 'tb-07',
          tool_name: 'msr_sql',
          tool_version: '1.0',
          invocation_params: {},
          results: [{ content: 'Venus 7th house natal placement', signal_id: 'MSR-300', confidence: 0.9, significance: 0.85 }],
          served_from_cache: false,
          latency_ms: 42,
          result_hash: 'sha256:tb07',
          schema_version: '1.0' as const,
        },
      ],
    },
    expected_verdict: 'warn',
  },
  {
    label: '5.5-pass-07: discovery query with cluster signals',
    input: {
      query: 'What unusual patterns exist in my chart?',
      query_plan: { ...basePlan, query_class: 'discovery', domains: [] },
      bundle: { ...baseBundle, total_tokens: 1300 },
      tool_results: [
        {
          tool_bundle_id: 'tb-08',
          tool_name: 'cluster_atlas',
          tool_version: '1.0',
          invocation_params: {},
          results: [{ content: 'Cluster: Saturn-Mars mutual aspect with unusual intensity', signal_id: 'CLU-001', confidence: 0.85, significance: 0.9 }],
          served_from_cache: false,
          latency_ms: 70,
          result_hash: 'sha256:tb08',
          schema_version: '1.0' as const,
        },
      ],
    },
    expected_verdict: 'pass',
  },
  {
    label: '5.5-pass-08: interpretive single planet clear signal',
    input: {
      query: 'Explain Mars in 1st house',
      query_plan: { ...basePlan, query_class: 'interpretive', domains: ['personality'] },
      bundle: { ...baseBundle, total_tokens: 900 },
      tool_results: [
        {
          tool_bundle_id: 'tb-09',
          tool_name: 'msr_sql',
          tool_version: '1.0',
          invocation_params: {},
          results: [{ content: 'Mars 1st house: aggressive personality, high energy', signal_id: 'MSR-400', confidence: 0.93, significance: 0.88 }],
          served_from_cache: false,
          latency_ms: 40,
          result_hash: 'sha256:tb09',
          schema_version: '1.0' as const,
        },
      ],
    },
    expected_verdict: 'pass',
  },
]

// Checkpoint 8.5: 10 labeled examples (coherence)
const examples8_5: LabeledExample<Parameters<typeof runCheckpoint8_5>[0]>[] = [
  {
    label: '8.5-pass-01: substantive interpretive answer',
    input: {
      synthesized_text: 'Saturn in the 10th house creates a strong career dharma for this native. The delay-and-reward dynamic is central: professional breakthroughs come after periods of sustained effort, typically in the 30s-40s. The 10th lord placement further reinforces this pattern with authority and structure being key career themes.',
      query_class: 'interpretive',
      validator_results: [
        { validator_id: 'p1_layer_separation', validator_version: '1.0', vote: 'pass' },
        { validator_id: 'p2_citation', validator_version: '1.0', vote: 'pass' },
      ],
    },
    expected_verdict: 'pass',
  },
  {
    label: '8.5-pass-02: predictive with time-indexed claim',
    input: {
      synthesized_text: 'During Jupiter Mahadasha / Saturn Antardasha (2027-2029), the native faces a high-probability window for significant professional advancement. Confidence: 0.72. The Saturn-Jupiter exchange in the natal chart supports this timing, and the transit Saturn will conjoin the natal 10th lord during this period.',
      query_class: 'predictive',
      validator_results: [
        { validator_id: 'p1_layer_separation', validator_version: '1.0', vote: 'pass' },
      ],
    },
    expected_verdict: 'pass',
  },
  {
    label: '8.5-pass-03: holistic synthesis with multi-domain coverage',
    input: {
      synthesized_text: 'The native\'s chart shows a consistent pattern of delayed but substantial achievements across career (Saturn 10th), relationships (Venus in 7th but hemmed by malefics), and health (Mars-Ketu conjunction). The overarching theme is karmic completion: each domain shows the native working through obligations before flowering. The second half of life (post-42) shows a systematic release of this pressure across all three domains.',
      query_class: 'holistic',
      validator_results: [
        { validator_id: 'p1_layer_separation', validator_version: '1.0', vote: 'pass' },
        { validator_id: 'p5_signal_id_resolution', validator_version: '1.0', vote: 'pass' },
      ],
    },
    expected_verdict: 'pass',
  },
  {
    label: '8.5-warn-01: adequate but overly hedged',
    input: {
      synthesized_text: 'Saturn in the 10th house may or may not indicate career challenges depending on various factors. Some astrologers suggest delays, while others see this as a period of building. The native might experience professional growth, though this could vary. Different traditions interpret this placement differently.',
      query_class: 'interpretive',
      validator_results: [
        { validator_id: 'p1_layer_separation', validator_version: '1.0', vote: 'pass' },
      ],
    },
    expected_verdict: 'warn',
  },
  {
    label: '8.5-pass-04: remedial answer with clear prescriptions',
    input: {
      synthesized_text: 'For Saturn-related delays in career, the Parashari tradition recommends: (1) Chanting the Shani Beej Mantra 108 times on Saturdays, (2) Wearing a blue sapphire (neelam) set in silver on the middle finger of the right hand after purification, (3) Serving the elderly or disabled on Saturdays. These remedies directly address Saturn\'s significations as karaka of longevity, discipline, and service.',
      query_class: 'remedial',
      validator_results: [
        { validator_id: 'p1_layer_separation', validator_version: '1.0', vote: 'pass' },
      ],
    },
    expected_verdict: 'pass',
  },
  {
    label: '8.5-pass-05: factual answer with specific data',
    input: {
      synthesized_text: 'The native\'s Ascendant is Taurus (Vrishabha Lagna) at 24°32\'. The Ascendant lord Venus is placed in the 9th house in Capricorn, creating a Dharma-Karma Adhipati Yoga with the 10th lord Saturn. This is a classic yoga for professional distinction through dharmic action.',
      query_class: 'factual',
      validator_results: [],
    },
    expected_verdict: 'pass',
  },
  {
    label: '8.5-warn-02: cross-domain answer missing one domain',
    input: {
      synthesized_text: 'The career patterns in this chart are dominated by Saturn in the 10th house, creating the delay-and-reward dynamic. The native will experience professional advancement in their mid-30s. Regarding relationships, I do not have sufficient signals to make a meaningful statement about the intersection.',
      query_class: 'cross_domain',
      validator_results: [
        { validator_id: 'p1_layer_separation', validator_version: '1.0', vote: 'pass' },
      ],
    },
    expected_verdict: 'warn',
  },
  {
    label: '8.5-pass-06: discovery answer with novel findings',
    input: {
      synthesized_text: 'An unusual pattern emerges from this chart: the native has four planets in mutual exchange (parivartana yoga) — a rare configuration. Saturn-Mars exchange creates Viparita Raja Yoga conditions while Jupiter-Mercury exchange produces strong intellectual-dharmic coherence. The combined effect suggests a life trajectory that begins with apparent setbacks (Saturn-Mars) but produces lasting institutional achievements (Jupiter-Mercury). This pattern appears in approximately 2-3% of charts in the MSR signal database.',
      query_class: 'discovery',
      validator_results: [
        { validator_id: 'p1_layer_separation', validator_version: '1.0', vote: 'pass' },
        { validator_id: 'p5_signal_id_resolution', validator_version: '1.0', vote: 'pass' },
      ],
    },
    expected_verdict: 'pass',
  },
  {
    label: '8.5-pass-07: interpretive with citations',
    input: {
      synthesized_text: 'Per signals MSR-0042 (Saturn 10th career dharma) and MSR-0089 (10th lord strength), the native exhibits the classic Shani-karma pattern: professional excellence through sustained effort and service. The contradiction register (CONTRA-012) notes a tension between the 10th lord in the 9th and Saturn\'s aspect on the 7th, suggesting career advancement comes at the cost of partnership balance.',
      query_class: 'interpretive',
      validator_results: [
        { validator_id: 'p2_citation', validator_version: '1.0', vote: 'pass' },
        { validator_id: 'p5_signal_id_resolution', validator_version: '1.0', vote: 'pass' },
      ],
    },
    expected_verdict: 'pass',
  },
  {
    label: '8.5-warn-03: synthesis too short for holistic query',
    input: {
      synthesized_text: 'The chart shows interesting patterns. Multiple domains are active. More analysis would be needed for a complete picture.',
      query_class: 'holistic',
      validator_results: [
        { validator_id: 'p1_layer_separation', validator_version: '1.0', vote: 'pass' },
      ],
    },
    expected_verdict: 'warn',
  },
]

// ── Evaluation runner ─────────────────────────────────────────────────────────

interface EvalResult {
  label: string
  expected: CheckpointVerdict
  actual: CheckpointVerdict
  match: boolean
  latency_ms: number
}

async function runEval<T>(
  name: string,
  examples: LabeledExample<T>[],
  runner: (input: T) => Promise<{ verdict: CheckpointVerdict; latency_ms: number }>,
): Promise<void> {
  console.log(`\n${'─'.repeat(60)}`)
  console.log(`Checkpoint ${name} — ${examples.length} examples`)
  console.log('─'.repeat(60))

  const results: EvalResult[] = []

  for (const ex of examples) {
    process.stdout.write(`  ${ex.label}... `)
    try {
      const result = await runner(ex.input as T)
      const match = result.verdict === ex.expected_verdict
      results.push({
        label: ex.label,
        expected: ex.expected_verdict,
        actual: result.verdict,
        match,
        latency_ms: result.latency_ms,
      })
      console.log(`${match ? '✓' : '✗'} (expected: ${ex.expected_verdict}, got: ${result.verdict}, ${result.latency_ms}ms)`)
    } catch (err) {
      results.push({
        label: ex.label,
        expected: ex.expected_verdict,
        actual: 'pass',
        match: false,
        latency_ms: 0,
      })
      console.log(`✗ ERROR: ${(err as Error).message}`)
    }
  }

  const passed = results.filter(r => r.match).length
  const accuracy = (passed / results.length) * 100
  const avgLatency = results.reduce((sum, r) => sum + r.latency_ms, 0) / results.length

  console.log(`\nResult: ${passed}/${results.length} correct (${accuracy.toFixed(1)}%)`)
  console.log(`Avg latency: ${avgLatency.toFixed(0)}ms`)

  if (accuracy < 75) {
    console.log(`⚠️  BELOW ACCURACY THRESHOLD (75% minimum)`)
  } else if (accuracy < 80) {
    console.log(`⚠️  Below 80% target accuracy`)
  } else {
    console.log(`✓ Meets accuracy target`)
  }
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main() {
  console.log('MARSYS-JIS Phase 6 — Checkpoint offline accuracy evaluation')
  console.log(`Date: ${new Date().toISOString()}`)

  if (!process.env.ANTHROPIC_API_KEY) {
    console.error('ERROR: ANTHROPIC_API_KEY not set')
    process.exit(1)
  }

  await runEval('4.5 (Resolve→Retrieve)', examples4_5, runCheckpoint4_5)
  await runEval('5.5 (Retrieve→Validate)', examples5_5, runCheckpoint5_5)
  await runEval('8.5 (Synthesize→Discipline)', examples8_5, runCheckpoint8_5)

  console.log('\nEvaluation complete.')
}

main().catch(err => {
  console.error('Eval failed:', err)
  process.exit(1)
})
