/**
 * MARSYS-JIS Phase 6 Stream B — Checkpoint 5.5 (Retrieve→Validate)
 *
 * After bundle assembly, before synthesis: confirms the retrieved bundle contains
 * enough material to answer the query. Catches "19 holistic signals retrieved but
 * none address the actual subject" failure mode.
 *
 * Feature flags:
 *   CHECKPOINT_5_5_ENABLED   (default false)
 *   CHECKPOINT_5_5_FAIL_HARD (default false)
 *
 * LLM: claude-haiku-4-5  (larger context than 4.5 due to bundle content)
 * Latency budget: ≤1200ms p95
 */

import 'server-only'

import fs from 'fs'
import path from 'path'
import { runAdapter } from '@/lib/adapters'

import { getFlag } from '@/lib/config/index'
import { telemetry } from '@/lib/telemetry/index'
import { getEffectiveModel } from '@/lib/models/runtime_config'

import {
  Checkpoint55OutputSchema,
  CheckpointHaltError,
  skippedResult,
  type Checkpoint55Input,
  type Checkpoint55Result,
} from './types'

const CHECKPOINT_ID = 'checkpoint_5_5'

/** Max chars of content to include per bundle asset (prevents prompt overflow) */
const ASSET_PREVIEW_CHARS = 200
/** Max signals to include in preview */
const MAX_SIGNAL_PREVIEW = 30

function loadPromptTemplate(): string {
  const templatePath = path.join(
    process.cwd(),
    'src/lib/prompts/checkpoints/checkpoint_5_5.md',
  )
  return fs.readFileSync(templatePath, 'utf-8')
}

function buildBundleAssetsText(input: Checkpoint55Input): string {
  const lines: string[] = []
  for (const entry of input.bundle.mandatory_context) {
    const preview = `${entry.canonical_id} · ${entry.role} · (token_count: ${entry.token_count})`
    lines.push(preview.slice(0, ASSET_PREVIEW_CHARS))
  }
  return lines.length > 0 ? lines.join('\n') : '(no assets)'
}

function buildSignalsPreviewText(input: Checkpoint55Input): string {
  const lines: string[] = []
  for (const toolBundle of input.tool_results.slice(0, MAX_SIGNAL_PREVIEW)) {
    for (const result of toolBundle.results.slice(0, 3)) {
      const line = result.signal_id
        ? `${result.signal_id}: ${result.content.slice(0, 120)}`
        : result.content.slice(0, 120)
      lines.push(line)
    }
  }
  return lines.length > 0 ? lines.join('\n') : '(no signals retrieved)'
}

function buildPrompt(input: Checkpoint55Input): string {
  const template = loadPromptTemplate()
  return template
    .replace('{{query}}', input.query)
    .replace('{{query_class}}', input.query_plan.query_class)
    .replace('{{bundle_assets}}', buildBundleAssetsText(input))
    .replace('{{signals_preview}}', buildSignalsPreviewText(input))
}

export async function runCheckpoint5_5(input: Checkpoint55Input): Promise<Checkpoint55Result> {
  if (!getFlag('CHECKPOINT_5_5_ENABLED')) {
    return skippedResult(CHECKPOINT_ID) as Checkpoint55Result
  }

  const started = Date.now()

  try {
    const prompt = buildPrompt(input)
    const checkpointModel = await getEffectiveModel('marsys', 'checkpoint_5_5', 'primary')

    const { finalText: text = '' } = await runAdapter({
      callType: 'checkpoint_5_5',
      modelOverride: { modelId: checkpointModel },
      systemPrompt: '',
      messages: [{ role: 'user', content: prompt }],
      maxOutputTokens: 768,
    })

    const latency_ms = Date.now() - started

    let parsed: unknown
    try {
      parsed = JSON.parse(text.trim())
    } catch {
      telemetry.recordMetric('checkpoint_5_5', 'parse_error', 1)
      return {
        checkpoint_id: CHECKPOINT_ID,
        verdict: 'pass',
        confidence: 0.5,
        reasoning: 'LLM output parse failed — defaulting to pass with warning',
        latency_ms,
        skipped: false,
      }
    }

    const validated = Checkpoint55OutputSchema.safeParse(parsed)
    if (!validated.success) {
      telemetry.recordMetric('checkpoint_5_5', 'schema_error', 1)
      return {
        checkpoint_id: CHECKPOINT_ID,
        verdict: 'pass',
        confidence: 0.5,
        reasoning: 'LLM output schema invalid — defaulting to pass with warning',
        latency_ms,
        skipped: false,
      }
    }

    const { verdict, confidence, reasoning, missing_signal_hints } = validated.data

    telemetry.recordMetric('checkpoint_5_5', `verdict_${verdict}`, 1)
    telemetry.recordLatency('checkpoint_5_5', 'run', latency_ms)

    const result: Checkpoint55Result = {
      checkpoint_id: CHECKPOINT_ID,
      verdict,
      confidence,
      reasoning,
      latency_ms,
      skipped: false,
      missing_signal_hints,
    }

    if (verdict === 'halt' && getFlag('CHECKPOINT_5_5_FAIL_HARD')) {
      throw new CheckpointHaltError(CHECKPOINT_ID, result)
    }

    return result
  } catch (err) {
    if (err instanceof CheckpointHaltError) throw err

    telemetry.recordError('checkpoint_5_5', 'unexpected_error', err as Error)
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
