/**
 * Unit tests for platform/src/lib/retrieve/tool_catalogue.ts
 * R11F-A-S2 acceptance check AC.c
 */

import { describe, it, expect, vi } from 'vitest'
import {
  convertRetrievalToolToChatTool,
  buildChatToolsFromNames,
} from '@/lib/retrieve/tool_catalogue'

describe('convertRetrievalToolToChatTool', () => {
  it('returns a ChatTool for a known registry entry', () => {
    const tool = convertRetrievalToolToChatTool('query_ephemeris')
    expect(tool).not.toBeNull()
    expect(tool!.name).toBe('query_ephemeris')
    expect(typeof tool!.description).toBe('string')
    expect(tool!.description.length).toBeGreaterThan(0)
    expect(tool!.inputSchema).toBeDefined()
  })

  it('returns null for an unknown tool name', () => {
    const tool = convertRetrievalToolToChatTool('nonexistent_tool_xyz')
    expect(tool).toBeNull()
  })

  it('includes a valid JSON Schema object in inputSchema', () => {
    const tool = convertRetrievalToolToChatTool('query_panchanga')
    expect(tool).not.toBeNull()
    expect(tool!.inputSchema).toMatchObject({ type: 'object' })
  })
})

describe('buildChatToolsFromNames', () => {
  it('returns ChatTool array for known tools', () => {
    const tools = buildChatToolsFromNames(['query_ephemeris', 'query_panchanga'])
    expect(tools).toHaveLength(2)
    expect(tools[0].name).toBe('query_ephemeris')
    expect(tools[0].inputSchema).toBeDefined()
    expect(tools[1].name).toBe('query_panchanga')
  })

  it('skips unknown tools with warning', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const tools = buildChatToolsFromNames(['nonexistent_tool'])
    expect(tools).toHaveLength(0)
    expect(warn).toHaveBeenCalledWith(expect.stringContaining('nonexistent_tool'))
    warn.mockRestore()
  })

  it('returns empty array for empty input', () => {
    expect(buildChatToolsFromNames([])).toEqual([])
  })

  it('handles mixed known and unknown names, skipping unknown with warning', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const tools = buildChatToolsFromNames(['query_ephemeris', 'bad_tool', 'query_panchanga'])
    expect(tools).toHaveLength(2)
    expect(tools.map(t => t.name)).toEqual(['query_ephemeris', 'query_panchanga'])
    expect(warn).toHaveBeenCalledWith(expect.stringContaining('bad_tool'))
    warn.mockRestore()
  })
})
