/**
 * MARSYS-JIS Phase 6 Stream A — Checkpoint 4.5 (Resolve→Retrieve)
 *
 * After entity resolution, before retrieval: confirms the resolved query plan
 * faithfully represents user intent. Catches ambiguity the deterministic router
 * collapsed too early (e.g., natal vs. transit Sun, wrong native's chart).
 *
 * Feature flags:
 *   CHECKPOINT_4_5_ENABLED   (default false) — invoke the checkpoint at all
 *   CHECKPOINT_4_5_FAIL_HARD (default false) — halt throws; default is warn-only
 *
 * LLM: claude-haiku-4-5  (fast + cheap; runs inline before retrieval)
 * Latency budget: ≤800ms p95
 */

import 'server-only'

import fs from 'fs'
import path from 'path'
import { runAdapter } from '@/lib/adapters'

import { getFlag } from '@/lib/config/index'
import { telemetry } from '@/lib/telemetry/index'
import { getEffectiveModel } from '@/lib/models/runtime_config'

import {
  Checkpoint45OutputSchema,
  CheckpointHaltError,
  skippedResult,
  type Checkpoint45Input,
  type Checkpoint45Result,
} from './types'

const CHECKPOINT_ID = 'checkpoint_4_5'

function loadPromptTemplate(): string {
  const templatePath = path.join(
    process.cwd(),
    'src/lib/prompts/checkpoints/checkpoint_4_5.md',
  )
  return fs.readFileSync(templatePath, 'utf-8')
}

function buildPrompt(input: Checkpoint45Input): string {
  const template = loadPromptTemplate()
  const discardedText =
    input.discarded_alternatives && input.discarded_alternatives.length > 0
      ? input.discarded_alternatives.join('\n')
      : '(none)'

  return template
    .replace('{{query}}', input.query)
    .replace('{{query_plan_json}}', JSON.stringify(input.query_plan, null, 2))
    .replace('{{discarded_alternatives}}', discardedText)
}

export async function runCheckpoint4_5(input: Checkpoint45Input): Promise<Checkpoint45Result> {
  if (!getFlag('CHECKPOINT_4_5_ENABLED')) {
    return skippedResult(CHECKPOINT_ID) as Checkpoint45Result
  }

  const started = Date.now()

  try {
    const prompt = buildPrompt(input)
    const checkpointModel = await getEffectiveModel('marsys', 'checkpoint_4_5', 'primary')

    const { finalText: text = '' } = await runAdapter({
      callType: 'checkpoint_4_5',
      modelOverride: { modelId: checkpointModel },
      systemPrompt: '',
      messages: [{ role: 'user', content: prompt }],
      maxOutputTokens: 512,
    })

    const latency_ms = Date.now() - started

    let parsed: unknown
    try {
      parsed = JSON.parse(text.trim())
    } catch {
      telemetry.recordMetric('checkpoint_4_5', 'parse_error', 1)
      return {
        checkpoint_id: CHECKPOINT_ID,
        verdict: 'pass',
        confidence: 0.5,
        reasoning: 'LLM output parse failed — defaulting to pass with warning',
        latency_ms,
        skipped: false,
      }
    }

    const validated = Checkpoint45OutputSchema.safeParse(parsed)
    if (!validated.success) {
      telemetry.recordMetric('checkpoint_4_5', 'schema_error', 1)
      return {
        checkpoint_id: CHECKPOINT_ID,
        verdict: 'pass',
        confidence: 0.5,
        reasoning: 'LLM output schema invalid — defaulting to pass with warning',
        latency_ms,
        skipped: false,
      }
    }

    const { verdict, confidence, reasoning, suggested_revision } = validated.data

    telemetry.recordMetric('checkpoint_4_5', `verdict_${verdict}`, 1)
    telemetry.recordLatency('checkpoint_4_5', 'run', latency_ms)

    const result: Checkpoint45Result = {
      checkpoint_id: CHECKPOINT_ID,
      verdict,
      confidence,
      reasoning,
      latency_ms,
      skipped: false,
      suggested_revision,
    }

    if (verdict === 'halt' && getFlag('CHECKPOINT_4_5_FAIL_HARD')) {
      throw new CheckpointHaltError(CHECKPOINT_ID, result)
    }

    return result
  } catch (err) {
    if (err instanceof CheckpointHaltError) throw err

    telemetry.recordError('checkpoint_4_5', 'unexpected_error', err as Error)
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
