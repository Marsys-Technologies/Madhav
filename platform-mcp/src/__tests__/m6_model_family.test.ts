/**
 * M6 — Per-model declared profile tests.
 *
 * Tests the model_family declaration mechanism:
 *   - Principal carries model_family from key validation
 *   - x-mcp-model-family header override takes precedence over key binding
 *   - Undeclared key → 'universal' fallback
 *   - sanitizeModelFamily validates allowed values
 *   - KeyValidateResponse carries model_family
 *
 * Chart-agnostic: no native chart_id or name in this file.
 * Vitest — not jest.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal, KeyValidateResponse } from '../types.js'

// ── Mock fetch globally ────────────────────────────────────────────────────────

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

// ── Import after mocking ───────────────────────────────────────────────────────

import { validateMcpKeyFromHeader, _testClearCache } from '../auth.js'

// ── Helpers ────────────────────────────────────────────────────────────────────

function makePrincipal(overrides: Partial<Principal> = {}): Principal {
  return {
    user_uid: 'user-m6-test',
    key_id: 'mcp_test_m6abc001',
    role: 'guest',
    ...overrides,
  }
}

function makeValidateResponse(overrides: Partial<KeyValidateResponse> = {}): KeyValidateResponse {
  return {
    valid: true,
    user_uid: 'user-m6-test',
    key_id: 'mcp_test_m6abc001',
    role: 'guest',
    model_family: null,
    ...overrides,
  }
}

beforeEach(() => {
  mockFetch.mockReset()
  _testClearCache()
})

// ── Principal type tests ───────────────────────────────────────────────────────

describe('Principal.model_family (M6 declared profile)', () => {
  it('accepts undefined model_family (undeclared key)', () => {
    const p = makePrincipal()
    expect(p.model_family).toBeUndefined()
  })

  it('accepts anthropic model_family', () => {
    const p = makePrincipal({ model_family: 'anthropic' })
    expect(p.model_family).toBe('anthropic')
  })

  it('accepts gemini model_family', () => {
    const p = makePrincipal({ model_family: 'gemini' })
    expect(p.model_family).toBe('gemini')
  })

  it('accepts openai model_family', () => {
    const p = makePrincipal({ model_family: 'openai' })
    expect(p.model_family).toBe('openai')
  })

  it('accepts deepseek model_family', () => {
    const p = makePrincipal({ model_family: 'deepseek' })
    expect(p.model_family).toBe('deepseek')
  })
})

// ── KeyValidateResponse carries model_family ──────────────────────────────────

describe('KeyValidateResponse.model_family', () => {
  it('response can carry null model_family (undeclared)', () => {
    const r = makeValidateResponse({ model_family: null })
    expect(r.model_family).toBeNull()
  })

  it('response can carry anthropic model_family', () => {
    const r = makeValidateResponse({ model_family: 'anthropic' })
    expect(r.model_family).toBe('anthropic')
  })

  it('valid=true with model_family=null is still a valid response', () => {
    const r = makeValidateResponse()
    expect(r.valid).toBe(true)
    expect(r.model_family).toBeNull()
  })
})

// ── validateMcpKeyFromHeader: model_family flows through from platform ────────

describe('validateMcpKeyFromHeader — model_family propagation', () => {
  const FAKE_KEY = 'mcp_test_ABCDEFGH12345678901234567890123456789012'

  it('populates model_family=anthropic when platform returns anthropic', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeValidateResponse({ model_family: 'anthropic' }),
    })

    const p = await validateMcpKeyFromHeader(`Bearer ${FAKE_KEY}`)
    expect(p).not.toBeNull()
    expect(p?.model_family).toBe('anthropic')
  })

  it('populates model_family=gemini when platform returns gemini', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeValidateResponse({ model_family: 'gemini' }),
    })

    const p = await validateMcpKeyFromHeader(`Bearer ${FAKE_KEY}`)
    expect(p?.model_family).toBe('gemini')
  })

  it('model_family is undefined when platform returns null', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeValidateResponse({ model_family: null }),
    })

    const p = await validateMcpKeyFromHeader(`Bearer ${FAKE_KEY}`)
    expect(p).not.toBeNull()
    expect(p?.model_family).toBeUndefined()
  })

  it('model_family is undefined when platform returns unknown value', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeValidateResponse({ model_family: 'unknown_llm' }),
    })

    const p = await validateMcpKeyFromHeader(`Bearer ${FAKE_KEY}`)
    expect(p).not.toBeNull()
    // Unknown families sanitized out → undefined
    expect(p?.model_family).toBeUndefined()
  })

  it('returns null when platform responds with valid=false', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ valid: false, error: 'revoked' }),
    })

    const p = await validateMcpKeyFromHeader(`Bearer ${FAKE_KEY}`)
    expect(p).toBeNull()
  })
})

// ── model_family precedence logic (express header override > key binding) ─────

describe('Model family precedence logic (unit)', () => {
  const ALLOWED_FAMILIES = ['anthropic', 'gemini', 'openai', 'deepseek'] as const
  type ModelFamily = typeof ALLOWED_FAMILIES[number]

  function resolveEffectiveFamily(
    headerFamily: string | undefined,
    principalFamily: ModelFamily | undefined
  ): string {
    return (
      (headerFamily && (ALLOWED_FAMILIES as readonly string[]).includes(headerFamily)
        ? headerFamily
        : principalFamily) ??
      'universal'
    )
  }

  it('header override takes precedence over key binding', () => {
    expect(resolveEffectiveFamily('gemini', 'anthropic')).toBe('gemini')
  })

  it('key binding used when no header override', () => {
    expect(resolveEffectiveFamily(undefined, 'anthropic')).toBe('anthropic')
  })

  it('universal fallback when neither header nor key binding', () => {
    expect(resolveEffectiveFamily(undefined, undefined)).toBe('universal')
  })

  it('unknown header value falls through to key binding', () => {
    expect(resolveEffectiveFamily('gpt99', 'anthropic')).toBe('anthropic')
  })

  it('unknown header + no key binding → universal', () => {
    expect(resolveEffectiveFamily('gpt99', undefined)).toBe('universal')
  })

  it('all 4 allowed families accepted in header position', () => {
    for (const f of ALLOWED_FAMILIES) {
      expect(resolveEffectiveFamily(f, undefined)).toBe(f)
    }
  })
})
