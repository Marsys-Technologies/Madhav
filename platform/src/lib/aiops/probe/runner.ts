import 'server-only'
import { runAdapter } from '@/lib/adapters'
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

  // Verify model is known before attempting the call
  const meta = getModelMeta(modelId)
  if (!meta) {
    return {
      model_id:  modelId,
      stack,
      call_type: callType,
      role,
      status:        'fail',
      latency_ms:    0,
      input_tokens:  null,
      output_tokens: null,
      output_text:   '',
      finish_reason: null,
      cost_usd:      null,
      error:         `Unknown model: ${modelId}`,
    }
  }

  const base: Omit<ProbeResult, 'status' | 'latency_ms' | 'input_tokens' | 'output_tokens' | 'output_text' | 'finish_reason' | 'cost_usd' | 'error'> = {
    model_id:  modelId,
    stack,
    call_type: callType,
    role,
  }

  const prompt = getProbePrompt(callType)
  const start = Date.now()

  try {
    const interaction = await runAdapter({
      callType,
      modelOverride: { modelId },
      systemPrompt: '',
      messages: [{ role: 'user', content: prompt }],
      maxOutputTokens: 256,
      timeoutMs: PROBE_TIMEOUT_MS,
    })

    const latency_ms    = Date.now() - start
    const input_tokens  = interaction.usage.inputTokens ?? null
    const output_tokens = interaction.usage.outputTokens ?? null
    const output_text   = (interaction.finalText ?? '').slice(0, 300)
    const finish_reason = interaction.finishReason ?? null
    const cost_usd = (input_tokens !== null && output_tokens !== null)
      ? (input_tokens * meta.costPer1MInput + output_tokens * meta.costPer1MOutput) / 1_000_000
      : null

    return { ...base, status: 'pass', latency_ms, input_tokens, output_tokens, output_text, finish_reason, cost_usd }
  } catch (err: unknown) {
    const isAbort = err instanceof Error && (err.name === 'AbortError' || err.message.includes('abort'))
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
