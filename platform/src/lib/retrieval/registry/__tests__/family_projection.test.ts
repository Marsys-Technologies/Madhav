/**
 * family_projection.test.ts — W5 lane L3 CI gate
 * ================================================================================
 * RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md §E W5 standing scope line:
 * "annotations + family_overrides + input_examples/search_result emissions".
 *
 * Three things are exercised here, matching the three items the brief names:
 *
 *   1. `buildMcpAnnotations()` — projects the registry's existing `cap.annotations`
 *      field (populated 118/118 by the W2 descriptor-migration backfill) into the
 *      REAL MCP SDK `ToolAnnotations` wire shape (readOnlyHint/destructiveHint/
 *      idempotentHint/openWorldHint/title — verified against this repo's installed
 *      `@modelcontextprotocol/sdk` types, not guessed).
 *   2. `buildFamilyToolDef()`/`buildFamilyToolDefs()`/`buildAllFamilyToolDefs()` —
 *      the `family_overrides` MERGE mechanism. `family_overrides` itself is 0/118
 *      populated on the live registry (W2's deliberate, documented non-population —
 *      genuine editorial judgment this campaign does not fabricate). This test
 *      proves the merge mechanism against the REAL live catalog (no-override path)
 *      AND against test-local mock override objects (every override field's path),
 *      so a future editorial wave's population is picked up with zero code changes.
 *   3. `input_examples`/`search_result_content_block` emission — both are fields
 *      inside `FamilyOverrideSpec`, exercised via the mock-override tests below.
 */
import { describe, it, expect } from 'vitest'
import { getCatalog } from '../catalog'
import type { CapabilityDescriptor, GlobalCapabilityDescriptor } from '../types'
import {
  buildMcpAnnotations,
  buildFamilyToolDef,
  buildFamilyToolDefs,
  buildAllFamilyToolDefs,
  findFamilyNameCollisions,
  applyStrictSchemaTransform,
  MODEL_FAMILIES,
  buildChatToolDef,
  buildMcpToolRegistration,
  toJsonSchema,
  resolveType,
} from '../../../../../scripts/manifest/projection_builders'

// ── Minimal, valid mock capability (satisfies the discriminated union's
// GlobalCapabilityDescriptor shape) — used only to exercise merge paths that
// require a REAL (test-local) family_overrides value the live registry does
// not yet declare on anything. Never asserted as representative of the live
// estate's content, only of the merge mechanism's correctness. ──────────────

function makeMockCap(overrides: Partial<CapabilityDescriptor> = {}): GlobalCapabilityDescriptor {
  const base: GlobalCapabilityDescriptor = {
    uri: 'marsys://tool/L1/mock_capability',
    type: 'tool',
    layer: 'L1',
    name: 'mock_capability',
    description: 'A mock capability for family-override merge testing.',
    input_schema: {
      chart_id: { type: 'string', description: 'Chart UUID' },
      limit: { type: 'number', description: 'Max rows', default: 10 },
    },
    required_inputs: [],
    handler: async () => ({ content: '' }),
    archetype: 'flat_fact',
    traversal_level: 'L-DOMAIN',
    tool_role: 'leaf',
    emits_references: false,
    lel_capable: false,
    scope: 'global',
  }
  return { ...base, ...overrides } as GlobalCapabilityDescriptor
}

// ── 1. MCP-spec annotations projection ───────────────────────────────────────

describe('W5 L3 — buildMcpAnnotations()', () => {
  it('emits the real MCP ToolAnnotations Hint-suffixed keys, only for fields the descriptor actually declares', () => {
    const cap = makeMockCap({
      annotations: { read_only: true, idempotent: true, destructive: false, open_world: false },
      display: { short_label: 'Mock Capability' },
    })
    const ann = buildMcpAnnotations(cap)
    expect(ann).toEqual({
      title: 'Mock Capability',
      readOnlyHint: true,
      idempotentHint: true,
      destructiveHint: false,
      openWorldHint: false,
    })
  })

  it('omits a key entirely (never fabricates false) when the descriptor annotation field is undefined', () => {
    const cap = makeMockCap({ annotations: undefined })
    const ann = buildMcpAnnotations(cap)
    expect(ann).toEqual({})
  })

  it('partial annotations only emit the declared subset', () => {
    const cap = makeMockCap({ annotations: { destructive: true } })
    const ann = buildMcpAnnotations(cap)
    expect(ann).toEqual({ destructiveHint: true })
  })

  it('every live getCatalog() capability with annotations declared produces a well-formed MCP annotations object', () => {
    const caps = getCatalog()
    const withAnnotations = caps.filter((c) => c.annotations !== undefined)
    expect(withAnnotations.length).toBeGreaterThan(0) // W2 backfilled 118/118
    for (const cap of withAnnotations) {
      const ann = buildMcpAnnotations(cap)
      for (const key of Object.keys(ann)) {
        expect(['title', 'readOnlyHint', 'destructiveHint', 'idempotentHint', 'openWorldHint']).toContain(key)
      }
    }
  })

  it('chat tool defs and MCP tool registrations both carry the annotations field additively (existing read_only/destructive fields untouched)', () => {
    const cap = makeMockCap({ annotations: { read_only: true, destructive: false, idempotent: true, open_world: false } })
    const chatDef = buildChatToolDef(cap)
    const mcpReg = buildMcpToolRegistration(cap)
    expect(chatDef.read_only).toBe(true)
    expect(chatDef.destructive).toBe(false)
    expect(chatDef.annotations).toEqual({ readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false })
    expect(mcpReg.annotations).toEqual({ readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false })
  })
})

// ── 2. family_overrides merge mechanism ──────────────────────────────────────

describe('W5 L3 — buildFamilyToolDef() / family_overrides merge', () => {
  it('no override declared: output is identical to the base descriptor for every family (the live-estate case today)', () => {
    const cap = makeMockCap()
    for (const family of MODEL_FAMILIES) {
      const def = buildFamilyToolDef(cap, family)
      expect(def.name).toBe(cap.name)
      expect(def.description).toBe(cap.description)
      expect(def.has_override).toBe(false)
      expect(def.name_overridden).toBe(false)
      expect(def.description_overridden).toBe(false)
      expect(def.strict_schema).toBe(false)
      expect(def.input_examples).toBeNull()
      expect(def.search_result_content_block).toBe(false)
    }
  })

  it('description_override applies only to the declaring family, others fall back to base description', () => {
    const cap = makeMockCap({
      family_overrides: { openai: { description_override: 'OpenAI-tuned description.' } },
    })
    const openaiDef = buildFamilyToolDef(cap, 'openai')
    const anthropicDef = buildFamilyToolDef(cap, 'anthropic')
    expect(openaiDef.description).toBe('OpenAI-tuned description.')
    expect(openaiDef.description_overridden).toBe(true)
    expect(anthropicDef.description).toBe(cap.description)
    expect(anthropicDef.description_overridden).toBe(false)
  })

  it('name_override applies (e.g. OpenAI <=64-char [a-z0-9_] constraint use case)', () => {
    const cap = makeMockCap({
      family_overrides: { openai: { name_override: 'mock_capability_openai_safe' } },
    })
    const def = buildFamilyToolDef(cap, 'openai')
    expect(def.name).toBe('mock_capability_openai_safe')
    expect(def.name_overridden).toBe(true)
  })

  it('strict_schema applies the OpenAI structured-output transform (additionalProperties:false, all-required) only when declared', () => {
    const cap = makeMockCap({
      family_overrides: { openai: { strict_schema: true } },
    })
    const strictDef = buildFamilyToolDef(cap, 'openai')
    const nonStrictDef = buildFamilyToolDef(cap, 'anthropic')
    expect(strictDef.strict_schema).toBe(true)
    expect(strictDef.input_schema['additionalProperties']).toBe(false)
    expect(strictDef.input_schema['required']).toEqual(['chart_id', 'limit'])
    expect(nonStrictDef.strict_schema).toBe(false)
    expect(nonStrictDef.input_schema).not.toHaveProperty('additionalProperties')
  })

  it('input_examples (few-shot) pass through verbatim for the declaring family only, null elsewhere', () => {
    const examples = [{ chart_id: '<chart_uuid>', limit: 5 }]
    const cap = makeMockCap({
      family_overrides: { anthropic: { input_examples: examples } },
    })
    const anthropicDef = buildFamilyToolDef(cap, 'anthropic')
    const openaiDef = buildFamilyToolDef(cap, 'openai')
    expect(anthropicDef.input_examples).toEqual(examples)
    expect(openaiDef.input_examples).toBeNull()
  })

  it('search_result_content_block flag emits true only for the declaring family', () => {
    const cap = makeMockCap({
      family_overrides: { anthropic: { search_result_content_block: true } },
    })
    const anthropicDef = buildFamilyToolDef(cap, 'anthropic')
    const geminiDef = buildFamilyToolDef(cap, 'gemini')
    expect(anthropicDef.search_result_content_block).toBe(true)
    expect(geminiDef.search_result_content_block).toBe(false)
  })

  it('a capability with family_overrides declared but a given family absent falls back to base for that family', () => {
    const cap = makeMockCap({
      family_overrides: { openai: { strict_schema: true } },
    })
    const deepseekDef = buildFamilyToolDef(cap, 'deepseek')
    expect(deepseekDef.has_override).toBe(false)
    expect(deepseekDef.strict_schema).toBe(false)
  })

  it('annotations still ride on every family tool def regardless of override presence', () => {
    const cap = makeMockCap({
      annotations: { read_only: true, destructive: false, idempotent: true, open_world: false },
      family_overrides: { openai: { strict_schema: true } },
    })
    for (const family of MODEL_FAMILIES) {
      const def = buildFamilyToolDef(cap, family)
      expect(def.annotations).toEqual({ readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false })
    }
  })
})

describe('W5 L3 — applyStrictSchemaTransform()', () => {
  it('sets additionalProperties:false and required = every declared property key', () => {
    const schema = toJsonSchema({ a: { type: 'string' }, b: { type: 'number' } })
    const strict = applyStrictSchemaTransform(schema)
    expect(strict['additionalProperties']).toBe(false)
    expect(strict['required']).toEqual(['a', 'b'])
  })

  it('handles an empty properties object without throwing', () => {
    const strict = applyStrictSchemaTransform(toJsonSchema(undefined, undefined))
    expect(strict['additionalProperties']).toBe(false)
    expect(strict['required']).toEqual([])
  })
})

// ── 3. Against the real live catalog: completeness + honesty ────────────────

describe('W5 L3 — buildFamilyToolDefs()/buildAllFamilyToolDefs() against the real live registry', () => {
  it('every family projection covers the same URI set as the base chat projection (type=tool + chat tag)', () => {
    const caps = getCatalog()
    const expectedUris = new Set(
      caps.filter((c) => resolveType(c) === 'tool' && (c.projection_tags ?? []).includes('chat')).map((c) => c.uri),
    )
    for (const family of MODEL_FAMILIES) {
      const defs = buildFamilyToolDefs(caps, family)
      const actualUris = new Set(defs.map((d) => d.uri))
      expect(actualUris).toEqual(expectedUris)
    }
  })

  it('buildAllFamilyToolDefs() returns all four families, each internally name-unique today (0 overrides live)', () => {
    const caps = getCatalog()
    const all = buildAllFamilyToolDefs(caps)
    expect(Object.keys(all).sort()).toEqual([...MODEL_FAMILIES].sort())
    for (const family of MODEL_FAMILIES) {
      const collisions = findFamilyNameCollisions(all[family])
      expect(collisions, `unexpected name collision(s) in ${family}: ${collisions.join(', ')}`).toEqual([])
    }
  })

  it('honest count: family_overrides is 0/N on the live registry today (W2 deliberate non-population) — not silently populated by this lane', () => {
    const caps = getCatalog()
    const declaring = caps.filter((c) => c.family_overrides !== undefined)
    expect(declaring.length).toBe(0)
  })

  it('findFamilyNameCollisions() detects a real collision when two mock defs share a name_override', () => {
    const defs = [
      buildFamilyToolDef(makeMockCap({ uri: 'marsys://tool/L1/a', name: 'a' }), 'openai'),
      buildFamilyToolDef(
        makeMockCap({
          uri: 'marsys://tool/L1/b',
          name: 'b',
          family_overrides: { openai: { name_override: 'a' } },
        }),
        'openai',
      ),
    ]
    expect(findFamilyNameCollisions(defs)).toEqual(['a'])
  })
})
