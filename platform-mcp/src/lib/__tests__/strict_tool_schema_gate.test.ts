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

function makeFakeServer() {
  const calls: Array<{ name: string; rest: unknown[] }> = []
  const server: StrictSchemaGateServer = {
    tool: (name: string, ...rest: unknown[]) => {
      calls.push({ name, rest })
      return { name, rest }
    },
  }
  return { server, calls }
}

describe('applyStrictSchemaGate()', () => {
  it('wraps a raw zod shape for a non-excluded tool so an unknown param is rejected', () => {
    const { server, calls } = makeFakeServer()
    applyStrictSchemaGate(server)

    const shape = { chart_id: z.string(), limit: z.number().optional() }
    server.tool('some_new_tool_get', 'a description', shape, () => ({}))

    const receivedSchema = calls[0].rest[1] as z.ZodTypeAny
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

  it('leaves an excluded tool name (other builders / PV-locked territory) completely unwrapped', () => {
    const excludedName = [...STRICT_SCHEMA_GATE_EXCLUDED_TOOL_NAMES][0]
    expect(excludedName).toBeDefined()

    const { server, calls } = makeFakeServer()
    applyStrictSchemaGate(server)

    const shape = { chart_id: z.string() }
    server.tool(excludedName as string, 'a description', shape, () => ({}))

    const receivedSchema = calls[0].rest[1]
    // Excluded names pass through byte-identical — the gate must not touch this shape at all.
    expect(receivedSchema).toBe(shape)
  })

  it('does not mistake a description string or a ToolAnnotations object for a zod shape', () => {
    const { server, calls } = makeFakeServer()
    applyStrictSchemaGate(server)

    const annotations = { readOnlyHint: true, title: 'Some Tool' }
    server.tool('another_new_tool_get', 'a plain description', annotations, () => ({}))

    const [description, receivedAnnotations] = calls[0].rest
    expect(description).toBe('a plain description')
    // Not a zod shape (no schema-instance values) — passed through unchanged.
    expect(receivedAnnotations).toBe(annotations)
  })

  it('a zero-arg tool(name, cb) registration is untouched (no shape argument at all)', () => {
    const { server, calls } = makeFakeServer()
    applyStrictSchemaGate(server)

    const cb = () => ({})
    server.tool('zero_arg_tool', cb)

    expect(calls[0].rest[0]).toBe(cb)
  })
})
