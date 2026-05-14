/**
 * nim_compat.test.ts — NIM toolChoice compatibility hardening unit tests
 *
 * Tests error classification, retry guard, and PlanInputJsonSchema validation.
 * No API calls, no mocking of external services needed — pure unit tests.
 */
import { describe, it, expect, vi } from 'vitest'

vi.mock('server-only', () => ({}))

import {
  PlannerCompatibilityError,
  isNimCompatibilityError,
  classifyNimError,
  shouldRetryNimError,
  validatePlanInputJsonSchema,
} from '@/lib/models/nvidia'

describe('PlannerCompatibilityError classification', () => {
  it('detects "does not support tool_choice" pattern', () => {
    expect(isNimCompatibilityError(new Error('model does not support tool_choice required'))).toBe(true)
  })

  it('detects "does not support response_format" pattern', () => {
    expect(isNimCompatibilityError(new Error('does not support response_format json_schema'))).toBe(true)
  })

  it('detects "tool_choice not supported" pattern', () => {
    expect(isNimCompatibilityError(new Error('tool_choice not supported for this model'))).toBe(true)
  })

  it('does not flag transient 5xx errors as compatibility errors', () => {
    expect(isNimCompatibilityError(new Error('NIM HTTP 500 internal server error'))).toBe(false)
  })

  it('does not flag timeout errors as compatibility errors', () => {
    expect(isNimCompatibilityError(new Error('Planner call timed out after 5000ms'))).toBe(false)
  })

  it('does not flag rate-limit errors as compatibility errors', () => {
    expect(isNimCompatibilityError(new Error('rate_limited: 429 Too Many Requests'))).toBe(false)
  })
})

describe('classifyNimError', () => {
  it('re-throws as PlannerCompatibilityError for toolChoice rejection', () => {
    const original = new Error('does not support tool_choice')
    expect(() => classifyNimError(original)).toThrow(PlannerCompatibilityError)
  })

  it('re-throws original error for non-compatibility errors', () => {
    const original = new Error('NIM HTTP 500')
    expect(() => classifyNimError(original)).toThrow(original)
  })

  it('PlannerCompatibilityError preserves cause', () => {
    const original = new Error('does not support response_format')
    try {
      classifyNimError(original)
    } catch (e) {
      expect(e).toBeInstanceOf(PlannerCompatibilityError)
      expect((e as PlannerCompatibilityError).cause).toBe(original)
    }
  })
})

describe('shouldRetryNimError', () => {
  it('returns false for PlannerCompatibilityError', () => {
    expect(shouldRetryNimError(new PlannerCompatibilityError('compat error'))).toBe(false)
  })

  it('returns true for transient errors', () => {
    expect(shouldRetryNimError(new Error('NIM HTTP 500'))).toBe(true)
    expect(shouldRetryNimError(new Error('rate_limited'))).toBe(true)
    expect(shouldRetryNimError(new Error('timeout'))).toBe(true)
  })
})

describe('validatePlanInputJsonSchema', () => {
  it('returns valid for a well-formed schema with tool_calls property', () => {
    const schema = {
      type: 'object',
      properties: {
        tool_calls: { type: 'array' },
      },
      required: ['tool_calls'],
    }
    const result = validatePlanInputJsonSchema(schema)
    expect(result.valid).toBe(true)
    expect(result.warnings).toHaveLength(0)
  })

  it('returns invalid for null schema', () => {
    const result = validatePlanInputJsonSchema(null)
    expect(result.valid).toBe(false)
    expect(result.warnings.some(w => w.includes('null'))).toBe(true)
  })

  it('warns when tool_calls property is missing', () => {
    const schema = { type: 'object', properties: { other: {} } }
    const result = validatePlanInputJsonSchema(schema)
    expect(result.valid).toBe(false)
    expect(result.warnings.some(w => w.includes('tool_calls'))).toBe(true)
  })

  it('warns when type is not object', () => {
    const schema = { type: 'array', properties: { tool_calls: {} } }
    const result = validatePlanInputJsonSchema(schema)
    expect(result.valid).toBe(false)
    expect(result.warnings.some(w => w.includes('type'))).toBe(true)
  })
})
