/**
 * _envelope.test.ts — Unit tests for the shared MCP envelope serializer.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { okResult, errorResult } from '../src/tools/_envelope.js'
import type { McpEnvelope } from '../src/tools/_envelope.js'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function setVerbose(value: string | undefined) {
  if (value === undefined) {
    delete process.env['MCP_VERBOSE']
  } else {
    process.env['MCP_VERBOSE'] = value
  }
}

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const successEnvelope: McpEnvelope = {
  ok: true,
  result: { rows: [{ planet: 'Saturn', value: '7.4 rupas' }] },
  trace_id: 'trace-abc-123',
  epistemics: { surgical: true, confidence_band: 'high' },
}

const errorEnvelope: McpEnvelope = {
  ok: false,
  error: 'Forbidden',
  message: 'data_coverage is restricted to super_admin and acharya tiers.',
}

// ---------------------------------------------------------------------------
// okResult
// ---------------------------------------------------------------------------

describe('okResult', () => {
  beforeEach(() => setVerbose(undefined))
  afterEach(() => setVerbose(undefined))

  it('returns content array with a single text item', () => {
    const result = okResult(successEnvelope)
    expect(result.content).toHaveLength(1)
    expect(result.content[0].type).toBe('text')
    expect(typeof result.content[0].text).toBe('string')
  })

  it('does not set isError', () => {
    const result = okResult(successEnvelope)
    expect((result as { isError?: boolean }).isError).toBeUndefined()
  })

  it('serialised text parses back to the original envelope', () => {
    const result = okResult(successEnvelope)
    const parsed = JSON.parse(result.content[0].text)
    expect(parsed).toEqual(successEnvelope)
  })

  it('propagates ok: true', () => {
    const result = okResult(successEnvelope)
    const parsed = JSON.parse(result.content[0].text)
    expect(parsed.ok).toBe(true)
  })

  it('produces compact JSON by default (no trailing newline, no multi-space indent)', () => {
    const result = okResult(successEnvelope)
    const text = result.content[0].text
    // Compact JSON must not contain the two-space indent pattern used by pretty-print
    expect(text).not.toMatch(/\n  /)
    expect(text).toBe(JSON.stringify(successEnvelope))
  })

  it('produces compact JSON when MCP_VERBOSE=false', () => {
    setVerbose('false')
    const result = okResult(successEnvelope)
    expect(result.content[0].text).toBe(JSON.stringify(successEnvelope))
  })

  it('produces pretty-printed JSON when MCP_VERBOSE=true', () => {
    setVerbose('true')
    const result = okResult(successEnvelope)
    const text = result.content[0].text
    // Pretty-print includes newlines + indent
    expect(text).toContain('\n')
    expect(text).toContain('  ')
    expect(text).toBe(JSON.stringify(successEnvelope, null, 2))
  })

  it('pretty-printed output parses back correctly', () => {
    setVerbose('true')
    const result = okResult(successEnvelope)
    const parsed = JSON.parse(result.content[0].text)
    expect(parsed).toEqual(successEnvelope)
  })
})

// ---------------------------------------------------------------------------
// errorResult
// ---------------------------------------------------------------------------

describe('errorResult', () => {
  beforeEach(() => setVerbose(undefined))
  afterEach(() => setVerbose(undefined))

  it('returns content array with a single text item', () => {
    const result = errorResult(errorEnvelope)
    expect(result.content).toHaveLength(1)
    expect(result.content[0].type).toBe('text')
    expect(typeof result.content[0].text).toBe('string')
  })

  it('sets isError: true', () => {
    const result = errorResult(errorEnvelope)
    expect(result.isError).toBe(true)
  })

  it('serialised text parses back to the original envelope', () => {
    const result = errorResult(errorEnvelope)
    const parsed = JSON.parse(result.content[0].text)
    expect(parsed).toEqual(errorEnvelope)
  })

  it('propagates ok: false', () => {
    const result = errorResult(errorEnvelope)
    const parsed = JSON.parse(result.content[0].text)
    expect(parsed.ok).toBe(false)
  })

  it('produces compact JSON by default', () => {
    const result = errorResult(errorEnvelope)
    expect(result.content[0].text).toBe(JSON.stringify(errorEnvelope))
  })

  it('produces pretty-printed JSON when MCP_VERBOSE=true', () => {
    setVerbose('true')
    const result = errorResult(errorEnvelope)
    const text = result.content[0].text
    expect(text).toContain('\n')
    expect(text).toBe(JSON.stringify(errorEnvelope, null, 2))
  })

  it('pretty-printed error output parses back correctly', () => {
    setVerbose('true')
    const result = errorResult(errorEnvelope)
    const parsed = JSON.parse(result.content[0].text)
    expect(parsed).toEqual(errorEnvelope)
  })
})

// ---------------------------------------------------------------------------
// Edge cases
// ---------------------------------------------------------------------------

describe('edge cases', () => {
  afterEach(() => setVerbose(undefined))

  it('handles minimal envelope {ok: true}', () => {
    const env: McpEnvelope = { ok: true }
    const result = okResult(env)
    expect(JSON.parse(result.content[0].text)).toEqual({ ok: true })
  })

  it('handles envelope with null values', () => {
    const env: McpEnvelope = { ok: false, result: null, trace_id: null }
    const result = errorResult(env)
    const parsed = JSON.parse(result.content[0].text)
    expect(parsed.result).toBeNull()
    expect(parsed.trace_id).toBeNull()
  })

  it('handles nested arrays and objects', () => {
    const env: McpEnvelope = {
      ok: true,
      rows: [{ a: 1 }, { b: [2, 3] }],
    }
    const result = okResult(env)
    expect(JSON.parse(result.content[0].text)).toEqual(env)
  })
})
