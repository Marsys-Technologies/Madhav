/**
 * lahiri_text_lint.test.ts — SS N-339 / N-342, PR-4: text lint for the LLM-visible ayanamsha text.
 *
 * Fails when a generated chat-tool / MCP definition, or the hand-written MCP tool source, says
 *   - `'LAHIRI'` (upper case, not a stored id) as a default, or
 *   - "Omit for all" / "Omit for unfiltered" / "Omit for default" on an `ayanamsha_id` whose tool
 *     now defaults to Lahiri.
 *
 * KNOWN_DEFERRED_TO_PR2 lists the platform registry handlers (layers/**, PR-2's files) whose
 * ayanamsha_id description still says "Omit for all". The list is a ratchet: an entry that is
 * ALREADY clean fails the test ("remove it from the list"), so PR-2 shrinks it to empty.
 */
import { describe, it, expect } from 'vitest'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const MCP_ROOT = join(HERE, '..')
const REPO_ROOT = join(MCP_ROOT, '..')
const PROJECTIONS = join(REPO_ROOT, 'platform/src/generated/projections')

/**
 * Registry handlers (platform/src/lib/retrieval/registry/layers/**, PR-2's files) whose
 * `ayanamsha_id` input_schema description still says "Omit for all/unfiltered/default". The
 * generated chat / MCP / family projections copy that text from the handler descriptor, so the
 * fix is in the handler (PR-2 changes each handler's omitted-id default and its text together).
 * Keyed by the capability name (the last segment of the capability URI).
 *
 * Combined Lahiri batch: the 15 readers that can serve KP-frame categories (get_aspects, get_ashtakavarga, get_avasthas,
 * get_bhava_bala, get_dignity, get_dispositors, get_sensitive_points, get_positions, get_nakshatra, get_karakas,
 * get_structural, get_sade_sati, get_panchanga, get_strength, get_yoga_dosha) were rewritten with the shared
 * KP_AWARE_AYANAMSHA_ID_TEXT and left this list; the remaining entries are still open.
 */
const KNOWN_DEFERRED_TO_PR2: ReadonlySet<string> = new Set([
  'get_argala', 'get_ayurdaya', 'get_condition_composite', 'get_divisionals', 'get_graha_yuddha',
  'get_medical_indications', 'get_prashna_lagna', 'get_sensitive_degrees', 'get_tajik',
  'get_tara_chandra_bala', 'get_transit_anchors', 'get_vastu_directions', 'get_vichara', 'get_yoga_firings',
  'query_cdlm_summary', 'query_cgm_motifs', 'query_cgm_paths', 'query_chart_gestalt', 'query_discoveries',
  'query_mechanisms', 'query_planet', 'query_pratijna', 'query_question_lenses', 'query_rm_chart_summary',
  'query_rm_dasha_windowed_prescriptions', 'query_rm_dosha_remedy_bundles', 'query_rm_pattern_remedies',
  'query_rm_prescriptions', 'query_rm_resonances', 'query_triangulation', 'traverse_chart_graph',
])

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

  it('no "Omit for all/unfiltered/default" outside the PR-2 deferred handlers', () => {
    const bad = all.filter((d) => OMIT_RE.test(d.description) && !KNOWN_DEFERRED_TO_PR2.has(d.tool))
    expect(bad.map((b) => `${b.file}:${b.tool}: ${b.description}`)).toEqual([])
  })

  it('ratchet: every KNOWN_DEFERRED_TO_PR2 entry still violates (remove it once PR-2 fixes the handler text)', () => {
    const stillBad = new Set(all.filter((d) => OMIT_RE.test(d.description)).map((d) => d.tool))
    const stale = [...KNOWN_DEFERRED_TO_PR2].filter((t) => !stillBad.has(t))
    expect(stale, 'these handlers are already clean: delete them from KNOWN_DEFERRED_TO_PR2').toEqual([])
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
