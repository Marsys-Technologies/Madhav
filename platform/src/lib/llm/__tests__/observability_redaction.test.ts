// Tests — legacy prompt redaction plus closed BYOK routing metadata.
import { afterEach, describe, expect, it } from 'vitest'
import { createHash } from 'node:crypto'
import {
  __resetActivePolicyForTests, defaultRedactionPolicy, getActivePolicy, hashPromptPolicy,
} from '../observability/redaction'
import type { ObservedLLMRequest, ObservedLLMResponse } from '../observability/types'
import { SafeAiRoutingParametersSchema, SafeMcpExternalSynthesisSchema } from '@/lib/ai-console/observability'

const sampleReq: ObservedLLMRequest = {
  provider: 'anthropic', model: 'claude-opus-4-6',
  prompt_text: 'What is the capital of France?', system_prompt: 'You are a helpful assistant.',
  parameters: { temperature: 0.7, max_tokens: 100 }, conversation_id: 'conv-1',
  conversation_name: 'Geography quiz', prompt_id: 'prompt-1', parent_prompt_id: 'prompt-0',
  user_id: 'user-1', pipeline_stage: 'classify',
}
const sampleRes: ObservedLLMResponse = {
  response_text: 'The capital of France is Paris.',
  usage: { input_tokens: 10, output_tokens: 8, cache_read_tokens: 0,
    cache_write_tokens: 0, reasoning_tokens: 0 },
  provider_request_id: 'req-anthropic-abc', status: 'success',
  started_at: new Date('2026-05-03T12:00:00Z'), finished_at: new Date('2026-05-03T12:00:01Z'),
}
const sha256 = (text: string) => createHash('sha256').update(text, 'utf8').digest('hex')

describe('defaultRedactionPolicy', () => {
  it('is the identity function (no field changes)', () => {
    expect(defaultRedactionPolicy(sampleReq, sampleRes)).toEqual({ request: sampleReq, response: sampleRes })
  })
})

describe('hashPromptPolicy', () => {
  it('hashes text while leaving all non-text fields intact', () => {
    const { request, response } = hashPromptPolicy(sampleReq, sampleRes)
    expect(request).toEqual({ ...sampleReq, prompt_text: sha256(sampleReq.prompt_text!),
      system_prompt: sha256(sampleReq.system_prompt!) })
    expect(response).toEqual({ ...sampleRes, response_text: sha256(sampleRes.response_text!) })
  })
  it('preserves null values without hashing', () => {
    const { request, response } = hashPromptPolicy({ ...sampleReq, prompt_text: null, system_prompt: null },
      { ...sampleRes, response_text: null })
    expect(request.prompt_text).toBeNull()
    expect(request.system_prompt).toBeNull()
    expect(response.response_text).toBeNull()
  })
})

describe('getActivePolicy (RT.5 — hash-by-default)', () => {
  const key = 'OBSERVATORY_HASH_PROMPTS'
  const original = process.env[key]
  afterEach(() => {
    if (original === undefined) delete process.env[key]
    else process.env[key] = original
    __resetActivePolicyForTests()
  })
  it('uses hashing when unset', () => {
    delete process.env[key]; __resetActivePolicyForTests()
    expect(getActivePolicy()).toBe(hashPromptPolicy)
  })
  it('permits an explicit false opt-out', () => {
    process.env[key] = 'false'; __resetActivePolicyForTests()
    expect(getActivePolicy()).toBe(defaultRedactionPolicy)
  })
  it('uses hashing when explicitly true', () => {
    process.env[key] = 'true'; __resetActivePolicyForTests()
    expect(getActivePolicy()).toBe(hashPromptPolicy)
  })
})

const safe = {
  schema_version: 'madhav.ai-routing.v1', snapshot_id: '10000000-0000-4000-8000-000000000001',
  invocation_id: '10000000-0000-4000-8000-000000000002', correlation_id: 'turn-1',
  conversation_id: null, user_id: 'user-1', source: 'backend', role: 'worker',
  selection_mode: 'default', resolved_choice_kind: 'provider_model', configuration_id: null,
  configuration_version: null, target_kind: 'provider_model',
  connection_id: '10000000-0000-4000-8000-000000000003', provider: 'openai', model_id: 'gpt-test',
  cli_id: null, built_in_default: false, terminal_status: 'success',
  started_at: '2026-09-27T00:00:00.000Z', finished_at: '2026-09-27T00:00:00.010Z',
  latency_ms: 10, input_tokens: null, output_tokens: null, total_tokens: null,
  retry_count: null, error_code: null, fallback_used: false, fallback_from_correlation_id: null,
} as const

describe('AI routing observability redaction', () => {
  it.each(['apiKey', 'credential', 'ciphertext', 'nonce', 'tag', 'wrappedKey', 'fingerprint',
    'prompt', 'systemPrompt', 'completion', 'probe', 'body', 'upstreamError', 'message', 'stack',
    'headers', 'authorization', 'cookie', 'stdout', 'stderr', 'command', 'executable', 'path', 'home',
    'token', 'refreshToken', 'accessToken', 'sessionSecret'])('rejects sensitive field %s', field => {
    expect(SafeAiRoutingParametersSchema.safeParse({ ...safe, [field]: 'secret-value' }).success).toBe(false)
  })
  it('accepts only a safe public error code, never raw error text', () => {
    expect(SafeAiRoutingParametersSchema.parse({ ...safe, terminal_status: 'error',
      error_code: 'AI_CONNECTION_INVALID' }).error_code).toBe('AI_CONNECTION_INVALID')
    expect(SafeAiRoutingParametersSchema.safeParse({ ...safe, error: '401 body with key' }).success).toBe(false)
  })
  it('keeps external synthesis closed and non-usage', () => {
    const marker = { schema_version: 'madhav.external-synthesis.v1',
      correlation_id: '10000000-0000-4000-8000-000000000006', conversation_id: null,
      user_id: 'user-1', call_stage: 'external_synthesis_handoff', external_synthesis: true,
      performed_by_madhav: false, status: 'not_observed', fallback_used: null }
    expect(SafeMcpExternalSynthesisSchema.safeParse({ ...marker, model: 'forbidden' }).success).toBe(false)
    expect(SafeMcpExternalSynthesisSchema.safeParse({ ...marker, prompt: 'forbidden' }).success).toBe(false)
    expect(SafeMcpExternalSynthesisSchema.parse(marker)).toEqual(marker)
  })
})
