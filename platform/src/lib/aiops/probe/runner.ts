import 'server-only'
import { generateText } from 'ai'
import { resolveModel } from '@/lib/models/resolver'
import { getModelMeta, STACK_ROUTING, DEFAULT_STACK_ID } from '@/lib/models/registry'
import { getEffectiveModel } from '@/lib/models/runtime_config'
import { getProbePrompt } from './prompts'
import type { ProbeOptions, ProbeResult } from './types'

const PROBE_TIMEOUT_MS = 20_000

export async function runProbe(opts: ProbeOptions): Promise<ProbeResult> {
  const { stack, callType, role, modelOverride } = opts

  // Resolve model_id: explicit override → runtime_config → registry fallback
  let modelId: string
  if (modelOverride) {
    modelId = modelOverride
  } else {
    modelId = await getEffectiveModel(stack, callType, role)
      .catch(() => STACK_ROUTING[stack]?.[callType]?.[role] ?? STACK_ROUTING[DEFAULT_STACK_ID][callType][role])
  }

  const base: Omit<ProbeResult, 'status' | 'latency_ms' | 'input_tokens' | 'output_tokens' | 'output_text' | 'finish_reason' | 'cost_usd' | 'error'> = {
    model_id:  modelId,
    stack,
    call_type: callType,
    role,
  }

  const prompt = getProbePrompt(callType)
  const start = Date.now()

  // Attempt to resolve the model — models not in the registry will use a
  // best-effort fetch via the provider key directly.
  let model
  try {
    model = resolveModel(modelId)
  } catch {
    return {
      ...base,
      status:        'fail',
      latency_ms:    Date.now() - start,
      input_tokens:  null,
      output_tokens: null,
      output_text:   '',
      finish_reason: null,
      cost_usd:      null,
      error:         `Unknown model: ${modelId}`,
    }
  }

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), PROBE_TIMEOUT_MS)

  try {
    const result = await generateText({
      model,
      messages: [{ role: 'user', content: prompt }],
      maxOutputTokens: 256,
      abortSignal: controller.signal,
    })
    clearTimeout(timer)

    const latency_ms    = Date.now() - start
    const input_tokens  = result.usage?.inputTokens ?? null
    const output_tokens = result.usage?.outputTokens ?? null
    const output_text   = (result.text ?? '').slice(0, 300)
    const finish_reason = result.finishReason ?? null

    const meta = getModelMeta(modelId)
    const cost_usd = (meta && input_tokens !== null && output_tokens !== null)
      ? (input_tokens * meta.costPer1MInput + output_tokens * meta.costPer1MOutput) / 1_000_000
      : null

    return { ...base, status: 'pass', latency_ms, input_tokens, output_tokens, output_text, finish_reason, cost_usd }
  } catch (err: unknown) {
    clearTimeout(timer)
    const isAbort = err instanceof Error && err.name === 'AbortError'
    return {
      ...base,
      status:        isAbort ? 'timeout' : 'fail',
      latency_ms:    Date.now() - start,
      input_tokens:  null,
      output_tokens: null,
      output_text:   '',
      finish_reason: null,
      cost_usd:      null,
      error:         err instanceof Error ? err.message : String(err),
    }
  }
}
