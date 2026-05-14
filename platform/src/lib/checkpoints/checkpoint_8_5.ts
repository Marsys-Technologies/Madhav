/**
 * MARSYS-JIS Phase 6 Stream C — Checkpoint 8.5 (Synthesize→Discipline)
 *
 * After synthesis, before disclosure-tier filtering: confirms the synthesized
 * answer is coherent and makes a real claim (not an empty shell). Also extracts
 * a structured prediction object when the synthesis contains a time-indexed claim,
 * replacing Phase 4's heuristic prediction extractor when
 * CHECKPOINT_8_5_PREDICTION_EXTRACT is enabled.
 *
 * Feature flags:
 *   CHECKPOINT_8_5_ENABLED             (default false)
 *   CHECKPOINT_8_5_FAIL_HARD           (default false)
 *   CHECKPOINT_8_5_PREDICTION_EXTRACT  (default false) — gates prediction extraction only
 *
 * LLM: claude-sonnet-4-6  (synthesis-coherence judgment warrants larger model)
 * Latency budget: ≤2500ms p95
 *
 * The halt verdict for 8.5 is async (synthesis is already streamed to the user).
 * Halt prevents prediction logging and flags the audit event as empty-shell.
 */

import 'server-only'

import fs from 'fs'
import path from 'path'
import { runAdapter } from '@/lib/adapters'

import { getFlag } from '@/lib/config/index'
import { telemetry } from '@/lib/telemetry/index'
import { getEffectiveModel } from '@/lib/models/runtime_config'

import {
  Checkpoint85OutputSchema,
  CheckpointHaltError,
  skippedResult,
  type Checkpoint85Input,
  type Checkpoint85Result,
} from './types'

const CHECKPOINT_ID = 'checkpoint_8_5'

/** Max chars of synthesized text to include in prompt */
const SYNTHESIS_PREVIEW_CHARS = 4000

function loadPromptTemplate(): string {
  const templatePath = path.join(
    process.cwd(),
    'src/lib/prompts/checkpoints/checkpoint_8_5.md',
  )
  return fs.readFileSync(templatePath, 'utf-8')
}

function buildValidatorSummary(
  validatorResults: Checkpoint85Input['validator_results'],
): string {
  if (validatorResults.length === 0) return '(no validators run)'
  return validatorResults
    .map(v => `${v.validator_id} v${v.validator_version}: ${v.vote}${v.reason ? ` — ${v.reason}` : ''}`)
    .join('\n')
}

function buildPrompt(input: Checkpoint85Input): string {
  const template = loadPromptTemplate()
  const synthesisPreview = input.synthesized_text.slice(0, SYNTHESIS_PREVIEW_CHARS)
  return template
    .replace('{{query_class}}', input.query_class)
    .replace('{{validator_results_json}}', buildValidatorSummary(input.validator_results))
    .replace('{{synthesized_text}}', synthesisPreview)
}

export async function runCheckpoint8_5(input: Checkpoint85Input): Promise<Checkpoint85Result> {
  if (!getFlag('CHECKPOINT_8_5_ENABLED')) {
    return skippedResult(CHECKPOINT_ID) as Checkpoint85Result
  }

  const started = Date.now()

  try {
    const prompt = buildPrompt(input)
    const checkpointModel = await getEffectiveModel('marsys', 'checkpoint_8_5', 'primary')

    const { finalText: text = '' } = await runAdapter({
      callType: 'checkpoint_8_5',
      modelOverride: { modelId: checkpointModel },
      systemPrompt: '',
      messages: [{ role: 'user', content: prompt }],
      maxOutputTokens: 1024,
    })

    const latency_ms = Date.now() - started

    let parsed: unknown
    try {
      parsed = JSON.parse(text.trim())
    } catch {
      telemetry.recordMetric('checkpoint_8_5', 'parse_error', 1)
      return {
        checkpoint_id: CHECKPOINT_ID,
        verdict: 'pass',
        confidence: 0.5,
        reasoning: 'LLM output parse failed — defaulting to pass with warning',
        latency_ms,
        skipped: false,
      }
    }

    const validated = Checkpoint85OutputSchema.safeParse(parsed)
    if (!validated.success) {
      telemetry.recordMetric('checkpoint_8_5', 'schema_error', 1)
      return {
        checkpoint_id: CHECKPOINT_ID,
        verdict: 'pass',
        confidence: 0.5,
        reasoning: 'LLM output schema invalid — defaulting to pass with warning',
        latency_ms,
        skipped: false,
      }
    }

    const { verdict, confidence, reasoning, prediction: rawPrediction } = validated.data

    // Honour the prediction-extract sub-flag: strip prediction when flag is off
    const prediction =
      getFlag('CHECKPOINT_8_5_PREDICTION_EXTRACT') ? rawPrediction : undefined

    telemetry.recordMetric('checkpoint_8_5', `verdict_${verdict}`, 1)
    telemetry.recordLatency('checkpoint_8_5', 'run', latency_ms)
    if (prediction) {
      telemetry.recordMetric('checkpoint_8_5', 'prediction_extracted', 1)
    }

    const result: Checkpoint85Result = {
      checkpoint_id: CHECKPOINT_ID,
      verdict,
      confidence,
      reasoning,
      latency_ms,
      skipped: false,
      prediction,
    }

    // Halt is logged but does NOT throw — synthesis is already streaming to user.
    // Phase 4's prediction-ledger writer skips the prediction on halt.
    if (verdict === 'halt') {
      telemetry.recordMetric('checkpoint_8_5', 'halt_flagged', 1)
      if (getFlag('CHECKPOINT_8_5_FAIL_HARD')) {
        // In FAIL_HARD mode the orchestrator caller should surface this as a failure.
        throw new CheckpointHaltError(CHECKPOINT_ID, result)
      }
    }

    return result
  } catch (err) {
    if (err instanceof CheckpointHaltError) throw err

    telemetry.recordError('checkpoint_8_5', 'unexpected_error', err as Error)
    return {
      checkpoint_id: CHECKPOINT_ID,
      verdict: 'pass',
      confidence: 0.5,
      reasoning: `Checkpoint error — defaulting to pass: ${(err as Error).message}`,
      latency_ms: Date.now() - started,
      skipped: false,
    }
  }
}
