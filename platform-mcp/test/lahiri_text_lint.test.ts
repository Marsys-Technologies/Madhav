/**
 * lahiri_text_lint.test.ts: SS N-339 / N-342, PR-4 (ratchet closed in the combined Lahiri batch): text lint for the LLM-visible ayanamsha text.
 *
 * Fails when a generated chat-tool / MCP definition, or the hand-written MCP tool source, says
 *   - `'LAHIRI'` (upper case, not a stored id) as a default, or
 *   - "Omit for all" / "Omit for unfiltered" / "Omit for default" on an `ayanamsha_id` whose tool
 *     now defaults to Lahiri.
 *
 * There is no allowlist: the former KNOWN_DEFERRED_TO_PR2 ratchet (46 registry handlers whose text still said
 * "Omit for all") was emptied by the combined batch and deleted. The detector itself is exercised on reverted
 * text below (`OMIT_RE` is not vacuous), and the platform-side counterpart reads the live registry descriptors
 * (`platform/src/lib/retrieval/registry/__tests__/kp_descriptor_text.test.ts`).
 */
import { describe, it, expect } from 'vitest'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const MCP_ROOT = join(HERE, '..')
const REPO_ROOT = join(MCP_ROOT, '..')
const PROJECTIONS = join(REPO_ROOT, 'platform/src/generated/projections')

const OMIT_RE = /omit for (all|unfiltered|default)/i
const UPPER_DEFAULT_RE = /default:?\s*['"]LAHIRI['"]/

interface Found { tool: string; description: string }

/**
 * Every `ayanamsha_id` property description in a generated JSON document, keyed by the capability
 * name (last segment of the nearest enclosing `uri`, else the nearest `name` / `tool_name`).
 */
function ayanamshaDescriptions(node: unknown, ctx: { tool: string } = { tool: 'unknown' }, out: Found[] = []): Found[] {
  if (Array.isArray(node)) {
    for (const n of node) ayanamshaDescriptions(n, ctx, out)
  } else if (node !== null && typeof node === 'object') {
    const rec = node as Record<string, unknown>
    let tool = ctx.tool
    for (const k of ['tool_name', 'name']) if (typeof rec[k] === 'string') tool = rec[k] as string
    if (typeof rec['uri'] === 'string') tool = (rec['uri'] as string).split('/').pop() ?? tool
    const aya = rec['ayanamsha_id']
    if (aya !== null && typeof aya === 'object' && typeof (aya as Record<string, unknown>)['description'] === 'string') {
      out.push({ tool, description: (aya as Record<string, unknown>)['description'] as string })
    }
    for (const v of Object.values(rec)) ayanamshaDescriptions(v, { tool }, out)
  }
  return out
}

function walkTs(dir: string, acc: string[] = []): string[] {
  for (const e of readdirSync(dir)) {
    const p = join(dir, e)
    const st = statSync(p)
    if (st.isDirectory()) {
      if (e === 'node_modules' || e === '__tests__' || e === 'generated') continue
      walkTs(p, acc)
    } else if (p.endsWith('.ts') && !p.endsWith('.test.ts')) {
      acc.push(p)
    }
  }
  return acc
}

describe('generated chat-tool / MCP definitions', () => {
  const FILES = [
    'chat_tool_defs.generated.json',
    'mcp_tool_registrations.generated.json',
    'family_tool_defs.generated.json',
    'mcp_surface_profiles.generated.json',
  ]
  const all: Array<Found & { file: string }> = []
  for (const f of FILES) {
    const doc = JSON.parse(readFileSync(join(PROJECTIONS, f), 'utf-8')) as unknown
    for (const d of ayanamshaDescriptions(doc)) all.push({ ...d, file: f })
  }

  it('scans a non-trivial number of ayanamsha_id descriptions', () => {
    expect(all.length).toBeGreaterThan(100)
  })

  it("no description says (default: 'LAHIRI')", () => {
    const bad = all.filter((d) => UPPER_DEFAULT_RE.test(d.description))
    expect(bad.map((b) => `${b.file}:${b.tool}`)).toEqual([])
  })

  it('no "Omit for all/unfiltered/default" on any ayanamsha_id description (no allowlist)', () => {
    const bad = all.filter((d) => OMIT_RE.test(d.description))
    expect(bad.map((b) => `${b.file}:${b.tool}: ${b.description}`)).toEqual([])
  })

  it('the detector is not vacuous: it flags the pre-primary phrasings that were removed', () => {
    for (const reverted of [
      'Filter by ayanamsha. Omit for all.',
      "Filter by ayanamsha (e.g. 'lahiri_chitrapaksha'). Omit for all 5.",
      'Filter by ayanamsha. Omit for all ayanamshas present.',
      'Ayanamsha filter. Omit for default.',
      'Omit for unfiltered rows',
    ]) {
      expect(OMIT_RE.test(reverted), reverted).toBe(true)
    }
    for (const fixed of [
      'Ayanamsha to read: a stored id or short alias, any case. Omitted = lahiri_chitrapaksha (the Lahiri primary reading); "all" = the explicit raw multi-ayanamsha rows.',
    ]) {
      expect(OMIT_RE.test(fixed)).toBe(false)
    }
  })
})

describe('platform-mcp generated surface profile (TS mirror)', () => {
  const text = readFileSync(join(MCP_ROOT, 'src/generated/mcp_surface_profiles.generated.ts'), 'utf-8')
  it("does not say (default: 'LAHIRI')", () => {
    expect(text.match(/default:?\s*['"\\]+LAHIRI/g) ?? []).toEqual([])
  })
})

describe('hand-written MCP tool source', () => {
  const files = walkTs(join(MCP_ROOT, 'src'))
  it("no source file defaults to the upper-case 'LAHIRI' (stored id is lahiri_chitrapaksha)", () => {
    const bad: string[] = []
    for (const f of files) {
      const t = readFileSync(f, 'utf-8')
      if (/default:?\s*['"]LAHIRI['"]/.test(t) || /\?\?\s*['"]LAHIRI['"]/.test(t)) bad.push(f.replace(MCP_ROOT + '/', ''))
    }
    expect(bad).toEqual([])
  })

  it('no "tropical, subtract Lahiri" text (the sidecar already serves sidereal Lahiri)', () => {
    const bad: string[] = []
    for (const f of files) {
      const t = readFileSync(f, 'utf-8')
      if (/Subtract Lahiri ayanamsha|tropical coordinates\)/.test(t)) bad.push(f.replace(MCP_ROOT + '/', ''))
    }
    expect(bad).toEqual([])
  })

  it('prompts/index.ts cites no gated legacy tool names', () => {
    const t = readFileSync(join(MCP_ROOT, 'src/prompts/index.ts'), 'utf-8')
    for (const g of ['get_chart_orientation', 'get_domain_reading', 'get_signals(', 'get_temporal_windows', 'get_classical_citation']) {
      expect(t, g).not.toContain(g)
    }
  })

  it('the MCP tool descriptions of the changed tools name lahiri_chitrapaksha and carry no "Omit for all" ayanamsha text', () => {
    const SRC = ['src/tools/register_p1_ganita.ts', 'src/tools/register_p1_synthesis.ts']
    for (const f of SRC) {
      const t = readFileSync(join(MCP_ROOT, f), 'utf-8')
      const lines = t.split('\n').filter((l) => /ayanamsha_id:\s*z\./.test(l) || /Omit for (all|unfiltered)/i.test(l))
      for (const l of lines) {
        if (/ayanamsha/i.test(l) && OMIT_RE.test(l)) throw new Error(`${f}: ${l.trim()}`)
      }
    }
  })
})

describe('platform handler text fixed in this PR', () => {
  it("register_d8_assess_domain.ts says lahiri_chitrapaksha, not 'LAHIRI'", () => {
    const t = readFileSync(join(REPO_ROOT, 'platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts'), 'utf-8')
    expect(t).not.toMatch(/default: 'LAHIRI'/)
  })
})
