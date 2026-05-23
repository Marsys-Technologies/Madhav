/**
 * R11F-A-S6: tool_catalogue_schema_normalization.test.ts
 *
 * Regression guard: every ChatTool emitted by tool_catalogue.ts must have
 * a JSON Schema with `type: 'object'` at the root. This is required by the
 * Anthropic API (and enforced by Gemini + OpenAI as well). The normalizer
 * must be defensive — bad schemas from the retrieval registry never escape
 * the catalogue boundary.
 *
 * Companion fix: AnthropicAdapter.chat() must use the AI SDK v6 `inputSchema`
 * field (not the v5 `parameters` field) when constructing CoreTool objects.
 * The test in this file drives the catalogue side; the A-S4 fixture tightening
 * below drives the adapter side.
 */

import { describe, it, expect, vi } from 'vitest'
import {
  normalizeInputSchema,
  convertRetrievalToolToChatTool,
  buildChatToolsFromNames,
} from '@/lib/retrieve/tool_catalogue'

// ---------------------------------------------------------------------------
// normalizeInputSchema — the defensive boundary function
// ---------------------------------------------------------------------------

describe('normalizeInputSchema — always emits type:object schema', () => {
  it('adds type:object to a completely empty schema {}', () => {
    const result = normalizeInputSchema({})
    expect(result.type).toBe('object')
    expect(result.properties).toEqual({})
  })

  it('adds type:object when schema has properties but no type', () => {
    const result = normalizeInputSchema({
      properties: { date: { type: 'string' }, limit: { type: 'number' } },
    })
    expect(result.type).toBe('object')
    expect(result.properties).toEqual({
      date: { type: 'string' },
      limit: { type: 'number' },
    })
  })

  it('preserves required array when present', () => {
    const result = normalizeInputSchema({
      properties: { date: { type: 'string' } },
      required: ['date'],
    })
    expect(result.type).toBe('object')
    expect(result.required).toEqual(['date'])
  })

  it('does not inject a required field when the input has none', () => {
    const result = normalizeInputSchema({ properties: { date: { type: 'string' } } })
    expect(result.required).toBeUndefined()
  })

  it('defensively emits empty properties when properties is not a plain object', () => {
    // Malformed registry entry with properties as a string — must not throw
    const result = normalizeInputSchema({ properties: 'not-an-object' as unknown as Record<string, unknown> })
    expect(result.type).toBe('object')
    expect(result.properties).toEqual({})
  })

  it('passes through a fully valid schema unchanged', () => {
    const input = {
      type: 'object' as const,
      properties: { signal_id: { type: 'string' } },
      required: ['signal_id'],
      additionalProperties: false,
    }
    const result = normalizeInputSchema(input)
    expect(result.type).toBe('object')
    expect(result.properties).toEqual({ signal_id: { type: 'string' } })
    expect(result.required).toEqual(['signal_id'])
  })

  it('handles null input defensively', () => {
    const result = normalizeInputSchema(null as unknown as Record<string, unknown>)
    expect(result.type).toBe('object')
    expect(result.properties).toEqual({})
  })
})

// ---------------------------------------------------------------------------
// buildChatToolsFromNames — schema invariant across all real registry tools
// ---------------------------------------------------------------------------

describe('buildChatToolsFromNames — schema invariant', () => {
  it('all emitted ChatTools have inputSchema.type === "object"', () => {
    // Use the real registry; any known tool name works
    const tools = buildChatToolsFromNames([
      'query_ephemeris',
      'query_panchanga',
      'query_dasha_periods',
    ])
    expect(tools.length).toBeGreaterThan(0)
    for (const tool of tools) {
      expect(tool.inputSchema).toBeDefined()
      expect((tool.inputSchema as { type?: string }).type).toBe('object')
    }
  })

  it('skips an unknown tool name and still emits valid schemas for known ones', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const tools = buildChatToolsFromNames(['query_ephemeris', 'bad_unknown_tool'])
    expect(tools).toHaveLength(1)
    expect((tools[0].inputSchema as { type?: string }).type).toBe('object')
    warn.mockRestore()
  })
})

// ---------------------------------------------------------------------------
// convertRetrievalToolToChatTool — always type:object regardless of registry entry
// ---------------------------------------------------------------------------

describe('convertRetrievalToolToChatTool — inputSchema invariant', () => {
  it('emits type:object for a known tool', () => {
    const tool = convertRetrievalToolToChatTool('query_ephemeris')
    expect(tool).not.toBeNull()
    expect((tool!.inputSchema as { type?: string }).type).toBe('object')
  })
})
