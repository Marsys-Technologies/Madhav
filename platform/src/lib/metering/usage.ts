import type { UsageEvidence } from './types'

const object = (v: unknown): Record<string, unknown> => v && typeof v === 'object' ? v as Record<string, unknown> : {}
const RAW_KEYS = new Set(['input_tokens', 'output_tokens', 'prompt_tokens', 'completion_tokens', 'total_tokens',
  'cache_read_input_tokens', 'cache_creation_input_tokens', 'promptTokenCount', 'candidatesTokenCount',
  'cachedContentTokenCount', 'thoughtsTokenCount', 'totalTokenCount', 'reasoning_tokens', 'cached_tokens',
  'cache_write_tokens', 'accepted_prediction_tokens', 'rejected_prediction_tokens', 'audio_tokens', 'text_tokens',
  'ephemeral_5m_input_tokens', 'ephemeral_1h_input_tokens'])
const RAW_OBJECTS = new Set(['prompt_tokens_details', 'completion_tokens_details', 'cache_creation'])

/** Only numeric usage fields survive. Never retain provider bodies or arbitrary metadata. */
function safeRaw(value: unknown): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(object(value))) {
    if (RAW_KEYS.has(k) && typeof v === 'number' && Number.isSafeInteger(v) && v >= 0) out[k] = v
    else if (RAW_OBJECTS.has(k)) out[k] = safeRaw(v)
  }
  return out
}

/** AI SDK V3 totals enclose their detailed counts. Counts are never assumed to be additive. */
export function normalizeSdkUsage(value: unknown, source: UsageEvidence['source'] = 'provider_reported'): UsageEvidence {
  const v = object(value), input = object(v.inputTokens), output = object(v.outputTokens)
  const issues: string[] = []
  const count = (raw: unknown, name: string): number | null => {
    if (raw == null) return null
    if (typeof raw === 'number' && Number.isSafeInteger(raw) && raw >= 0) return raw
    issues.push(`invalid_${name}`); return null
  }
  const usage: UsageEvidence = {
    input: count(typeof v.inputTokens === 'number' ? v.inputTokens : input.total, 'input'),
    uncachedInput: count(input.noCache ?? object(v.inputTokenDetails).noCacheTokens, 'uncached_input'),
    cacheRead: count(input.cacheRead ?? object(v.inputTokenDetails).cacheReadTokens ?? v.cachedInputTokens, 'cache_read'),
    cacheWrite: count(input.cacheWrite ?? object(v.inputTokenDetails).cacheWriteTokens, 'cache_write'),
    output: count(typeof v.outputTokens === 'number' ? v.outputTokens : output.total, 'output'),
    textOutput: count(output.text ?? object(v.outputTokenDetails).textTokens, 'text_output'),
    reasoning: count(output.reasoning ?? object(v.outputTokenDetails).reasoningTokens ?? v.reasoningTokens, 'reasoning'),
    source: value == null ? 'unavailable' : source, raw: safeRaw(v.raw), issues,
  }
  if (usage.input !== null) {
    const subset = (usage.cacheRead ?? 0) + (usage.cacheWrite ?? 0)
    if (subset > usage.input || (usage.uncachedInput !== null && usage.uncachedInput + subset > usage.input)) {
      issues.push('input_subsets_exceed_total')
    } else if (usage.uncachedInput !== null && usage.uncachedInput + subset < usage.input) {
      issues.push('input_subsets_incomplete')
    } else if (usage.uncachedInput === null && (usage.input === 0 || usage.cacheRead !== null || usage.cacheWrite !== null)) {
      usage.uncachedInput = usage.input - subset
    }
  }
  if (usage.output !== null && ((usage.reasoning ?? 0) > usage.output
    || (usage.textOutput !== null && usage.textOutput + (usage.reasoning ?? 0) > usage.output))) {
    issues.push('output_subsets_exceed_total')
  }
  return usage
}
