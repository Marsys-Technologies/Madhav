import { describe, expect, it } from 'vitest'
import { AI_ERROR_CODES, AiConsoleError, PublicAiErrorSchema, normalizeAiError } from '../errors'

describe('AI Console public errors', () => {
  it('includes stable configuration and execution codes', () => {
    expect(AI_ERROR_CODES).toEqual(expect.arrayContaining([
      'AI_DEFAULT_REQUIRED', 'AI_CHOICE_BROKEN', 'AI_CONNECTION_INVALID',
      'AI_MODEL_UNAVAILABLE', 'AI_ROLE_INCOMPATIBLE', 'AI_CLI_NOT_GRANTED',
      'AI_CLI_UNREACHABLE', 'AI_PROVIDER_UNREACHABLE',
    ]))
    for (const code of AI_ERROR_CODES) {
      const error = new AiConsoleError(code, 'worker')
      const normalized = normalizeAiError(error, { source: 'provider' })
      expect(normalized.code).toBe(code)
      expect(normalized.role).toBe('worker')
      expect(PublicAiErrorSchema.parse(normalized)).toEqual(normalized)
      expect(JSON.parse(JSON.stringify(error))).toEqual(normalized)
    }
  })

  it.each([
    [401, 'AI_CONNECTION_INVALID'], [403, 'AI_PERMISSION_DENIED'],
    [402, 'AI_BILLING_UNAVAILABLE'], [404, 'AI_MODEL_UNAVAILABLE'],
    [429, 'AI_RATE_LIMITED'], [500, 'AI_PROVIDER_UNREACHABLE'],
  ])('classifies provider HTTP %s without exposing upstream data', (status, code) => {
    const error = { status, message: 'SYNTHETIC_SENSITIVE_SENTINEL', body: 'SYNTHETIC_SENSITIVE_SENTINEL',
      headers: { authorization: 'SYNTHETIC_SENSITIVE_SENTINEL' }, stack: 'SYNTHETIC_SENSITIVE_SENTINEL', cause: 'SYNTHETIC_SENSITIVE_SENTINEL' }
    const result = normalizeAiError(error, { source: 'provider', role: 'planner' })
    expect(result.code).toBe(code)
    expect(result.role).toBe('planner')
    expect(JSON.stringify(result)).not.toContain('SYNTHETIC_SENSITIVE_SENTINEL')
    expect(Object.keys(result).sort()).toEqual(['code', 'message', 'retryable', 'role'])
  })

  it('supports statusCode used by provider SDK errors', () => {
    expect(normalizeAiError({ statusCode: 401 }, { source: 'provider' }).code).toBe('AI_CONNECTION_INVALID')
  })

  it.each([
    ['ENOENT', 'AI_CLI_NOT_INSTALLED'], ['ETIMEDOUT', 'AI_CLI_TIMEOUT'],
    ['AUTH_UNAVAILABLE', 'AI_CLI_AUTH_UNAVAILABLE'], ['OUTPUT_LIMIT', 'AI_CLI_OUTPUT_LIMIT'],
    ['GRANT_REVOKED', 'AI_CLI_NOT_GRANTED'], ['ECONNREFUSED', 'AI_CLI_UNREACHABLE'],
    ['anything', 'AI_EXECUTION_FAILED'],
  ])('classifies CLI %s using fixed output', (code, expected) => {
    const result = normalizeAiError({ code, stderr: 'SYNTHETIC_SENSITIVE_SENTINEL' }, { source: 'cli' })
    expect(result.code).toBe(expected)
    expect(JSON.stringify(result)).not.toContain('SYNTHETIC_SENSITIVE_SENTINEL')
  })

  it('never trusts an upstream public-looking code, message, or serialization method', () => {
    const upstream = { code: 'AI_DEFAULT_REQUIRED', message: 'SYNTHETIC_SENSITIVE_SENTINEL', toJSON: () => { throw new Error('must not run') } }
    expect(normalizeAiError(upstream, { source: 'provider' }).code).toBe('AI_EXECUTION_FAILED')
    for (const error of [null, undefined, 'SYNTHETIC_SENSITIVE_SENTINEL', new Error('SYNTHETIC_SENSITIVE_SENTINEL')]) {
      expect(JSON.stringify(normalizeAiError(error, { source: 'provider' }))).not.toContain('SYNTHETIC_SENSITIVE_SENTINEL')
    }
  })

  it('regenerates fixed messages even for a modified internal error', () => {
    const error = new AiConsoleError('AI_CHOICE_BROKEN')
    error.message = 'SYNTHETIC_SENSITIVE_SENTINEL'
    expect(JSON.stringify(normalizeAiError(error, { source: 'provider' }))).not.toContain('SYNTHETIC_SENSITIVE_SENTINEL')
  })

  it('rejects raw details and arbitrary text on the public error boundary', () => {
    const safe = normalizeAiError({ status: 401 }, { source: 'provider' })
    expect(PublicAiErrorSchema.safeParse({ ...safe, cause: 'secret' }).success).toBe(false)
    expect(PublicAiErrorSchema.safeParse({ ...safe, message: 'secret' }).success).toBe(false)
    expect(PublicAiErrorSchema.safeParse({ ...safe, role: 'inspector' }).success).toBe(false)
    expect(PublicAiErrorSchema.safeParse({ ...safe, retryable: true }).success).toBe(false)
  })

  it('marks only transient errors retryable, always on the already resolved target', () => {
    expect(normalizeAiError({ status: 429 }, { source: 'provider' }).retryable).toBe(true)
    expect(normalizeAiError({ status: 401 }, { source: 'provider' }).retryable).toBe(false)
    expect(normalizeAiError({ code: 'GRANT_REVOKED' }, { source: 'cli' }).retryable).toBe(false)
    expect(normalizeAiError({ status: 400 }, { source: 'provider' }).retryable).toBe(false)
    expect(normalizeAiError(new Error('unknown failure'), { source: 'provider' }).retryable).toBe(false)
    expect(normalizeAiError({ status: 503 }, { source: 'provider' }).retryable).toBe(true)
    expect(normalizeAiError({ code: 'ECONNRESET' }, { source: 'provider' }).retryable).toBe(true)
    expect(normalizeAiError({ code: 'ERR_CANCELED' }, { source: 'provider' }).retryable).toBe(false)
  })
})
