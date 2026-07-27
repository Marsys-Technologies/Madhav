/**
 * strict_tool_schema_gate.test.ts — ŚODHANA T4 (MC-024): portal-wide unknown-param rejection
 * ================================================================================
 * Covers:
 *   1. A raw zod shape argument passed to a NON-excluded tool name gets wrapped so an
 *      unknown/misspelled param is REJECTED (safeParse fails) instead of silently stripped.
 *   2. A known param still parses through correctly (the gate does not break normal calls).
 *   3. An excluded tool name (this builder's rails — other builders'/PV-locked territory)
 *      is passed through completely UNCHANGED — its schema still silently strips unknown
 *      keys, proving the gate never touches those files' behavior.
 *   4. Non-shape arguments (a description string, a ToolAnnotations object, the callback
 *      function) are never mistaken for a shape and passed through unchanged.
 */
import { describe, it, expect } from 'vitest'
import { z } from 'zod'
import {
  applyStrictSchemaGate,
  STRICT_SCHEMA_GATE_EXCLUDED_TOOL_NAMES,
  type StrictSchemaGateServer,
} from '../strict_tool_schema_gate.js'

/**
 * Fake server capturing BOTH registration entry points. A strict-ified registration (a raw
 * shape on a non-excluded tool) is now re-issued through `registerTool` — the positional
 * `.tool()` overload cannot carry a constructed ZodObject in SDK ≥1.29.0 (the P0 crash). A
 * pass-through registration (excluded name, no shape, annotations-only) still lands on `.tool`.
 */
function makeFakeServer() {
  const toolCalls: Array<{ name: string; rest: unknown[] }> = []
  const registerToolCalls: Array<{
    name: string
    config: { description?: string; inputSchema: z.ZodTypeAny; annotations?: Record<string, unknown> }
    cb: unknown
  }> = []
  const server: StrictSchemaGateServer = {
    tool: (name: string, ...rest: unknown[]) => {
      toolCalls.push({ name, rest })
      return { name, rest }
    },
    registerTool: (name, config, cb) => {
      registerToolCalls.push({ name, config, cb })
      return { name, config, cb }
    },
  }
  return { server, toolCalls, registerToolCalls }
}

describe('applyStrictSchemaGate()', () => {
  it('re-issues a raw zod shape for a non-excluded tool as a STRICT registerTool inputSchema', () => {
    const { server, toolCalls, registerToolCalls } = makeFakeServer()
    applyStrictSchemaGate(server)

    const shape = { chart_id: z.string(), limit: z.number().optional() }
    const cb = () => ({})
    server.tool('some_new_tool_get', 'a description', shape, cb)

    // The strict-ification path must go through registerTool, NOT the positional .tool()
    // overload (which crashes the real SDK when handed a constructed ZodObject).
    expect(registerToolCalls).toHaveLength(1)
    expect(toolCalls).toHaveLength(0)

    const call = registerToolCalls[0]
    expect(call.name).toBe('some_new_tool_get')
    expect(call.config.description).toBe('a description')
    expect(call.cb).toBe(cb)

    const receivedSchema = call.config.inputSchema
    // The gate must have replaced the plain shape with an actual strict ZodObject instance.
    expect(receivedSchema).not.toBe(shape)
    expect(typeof (receivedSchema as unknown as { safeParse: unknown }).safeParse).toBe('function')

    const goodResult = receivedSchema.safeParse({ chart_id: '482012f1-710e-4a25-994a-93821f5871aa' })
    expect(goodResult.success).toBe(true)

    const badResult = receivedSchema.safeParse({
      chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
      varhsa_year: 43, // deliberate misspelling of varsha_year
    })
    expect(badResult.success).toBe(false)
  })

  it('strict-ifies a shape carrying a nested .optional(z.object({...})) field (the prashna_ask/scope_tuple shape)', () => {
    const { server, registerToolCalls } = makeFakeServer()
    applyStrictSchemaGate(server)

    const shape = {
      chart_id: z.string().uuid(),
      question: z.string().min(1),
      scope_tuple: z
        .object({ intent: z.string(), width: z.enum(['narrow', 'standard', 'broad']) })
        .optional(),
      response_format: z.string(),
    }
    server.tool('prashna_ask_like', 'desc', shape, () => ({}))

    expect(registerToolCalls).toHaveLength(1)
    const receivedSchema = registerToolCalls[0].config.inputSchema
    // Valid: scope_tuple omitted (it is optional) still parses.
    expect(
      receivedSchema.safeParse({
        chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
        question: 'q',
        response_format: 'brief',
      }).success,
    ).toBe(true)
    // Unknown outer key still rejected (strict preserved despite the nested optional).
    expect(
      receivedSchema.safeParse({
        chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
        question: 'q',
        response_format: 'brief',
        bogus: 1,
      }).success,
    ).toBe(false)
  })

  it('passes an optional annotations object through registerTool alongside the strict schema', () => {
    const { server, registerToolCalls } = makeFakeServer()
    applyStrictSchemaGate(server)

    const annotations = { readOnlyHint: true, title: 'Some Tool' }
    server.tool('annotated_tool_get', 'desc', { a: z.string() }, annotations, () => ({}))

    expect(registerToolCalls).toHaveLength(1)
    expect(registerToolCalls[0].config.annotations).toBe(annotations)
  })

  it('leaves an excluded tool name (other builders / PV-locked territory) completely unwrapped', () => {
    const excludedName = [...STRICT_SCHEMA_GATE_EXCLUDED_TOOL_NAMES][0]
    expect(excludedName).toBeDefined()

    const { server, toolCalls, registerToolCalls } = makeFakeServer()
    applyStrictSchemaGate(server)

    const shape = { chart_id: z.string() }
    server.tool(excludedName as string, 'a description', shape, () => ({}))

    // Excluded names pass through byte-identical on .tool — the gate must not touch them.
    expect(registerToolCalls).toHaveLength(0)
    expect(toolCalls[0].rest[1]).toBe(shape)
  })

  it('does not mistake a ToolAnnotations-only registration for a zod shape', () => {
    const { server, toolCalls, registerToolCalls } = makeFakeServer()
    applyStrictSchemaGate(server)

    const annotations = { readOnlyHint: true, title: 'Some Tool' }
    server.tool('another_new_tool_get', 'a plain description', annotations, () => ({}))

    // No raw shape -> pass through to .tool untouched (not routed through registerTool).
    expect(registerToolCalls).toHaveLength(0)
    const [description, receivedAnnotations] = toolCalls[0].rest
    expect(description).toBe('a plain description')
    expect(receivedAnnotations).toBe(annotations)
  })

  it('a zero-arg tool(name, cb) registration is untouched (no shape argument at all)', () => {
    const { server, toolCalls, registerToolCalls } = makeFakeServer()
    applyStrictSchemaGate(server)

    const cb = () => ({})
    server.tool('zero_arg_tool', cb)

    expect(registerToolCalls).toHaveLength(0)
    expect(toolCalls[0].rest[0]).toBe(cb)
  })
})
