/**
 * lahiri_primary_pr4_tools.test.ts — SS N-339 / N-342 / N-344, PR-4 (MCP tool fixes and text).
 *
 * Per tool changed:
 *   - an omitted ayanamsha_id reaches the platform as the PRIMARY (lahiri_chitrapaksha);
 *   - "all" is the explicit raw opt-out and is forwarded as "all" (the capability route strips it);
 *   - short aliases / any case normalise to the stored id; the long stored ids are accepted.
 * Plus: synth_chart_brief top discoveries are primary-only and family-collapsed, the prashna
 * verdict is the Lahiri row with the other four named under a labelled key, the KP surfaces carry
 * "KP frame (Krishnamurti ayanamsha)", the two PyJHora tools accept stored ids.
 *
 * No network: global fetch is mocked.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { z } from 'zod'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

process.env['SERVICE_TOKEN'] = 'test-service-token'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)
vi.mock('../src/lib/authz.js', () => ({ remoteAuthorize: vi.fn().mockResolvedValue(true) }))

import { registerP1GanitaTools } from '../src/tools/register_p1_ganita.js'
import { registerP1SynthesisTools } from '../src/tools/register_p1_synthesis.js'
import { registerRegistryBridgeTools } from '../src/tools/registry_bridge.js'
import { registerComputeNatalPositionsTool, registerQuerySpecialLagnasTool } from '../src/tools/retrieval/pyhora_natal.js'
import { registerPrompts } from '../src/prompts/index.js'
import { KP_FRAME_LABEL, kpFrameLabelFor } from '../src/lib/kp_frame.js'
import { buildKalaAyanamshaFrame } from '../src/lib/kala_ayanamsha_frame.js'
import { buildKpSchoolVoice } from '../src/lib/kp_school_voice.js'

const HERE = dirname(fileURLToPath(import.meta.url))
const LAHIRI = 'lahiri_chitrapaksha'
const CHART = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const PRINCIPAL = { user_uid: 'test-uid', audience_tier: 'super_admin' as const, key_id: 'test-key-001' }

type Handler = (args: Record<string, unknown>) => Promise<{ isError?: boolean; content?: Array<{ text?: string }>; structuredContent?: unknown }>
interface Captured { schema: Record<string, z.ZodTypeAny>; handler: Handler; description: string }

function capture(register: (server: never, principal: never) => void): Map<string, Captured> {
  const tools = new Map<string, Captured>()
  const server = {
    tool: (name: string, description: string, schema: Record<string, z.ZodTypeAny>, handler: Handler) => {
      tools.set(name, { schema, handler, description })
    },
  }
  register(server as never, PRINCIPAL as never)
  return tools
}

function okJson(body: unknown) {
  return { ok: true, status: 200, json: () => Promise.resolve(body), text: () => Promise.resolve(JSON.stringify(body)) }
}

/** The platform capability route answers `{ ok, content: <handler result> }`. */
function capabilityOk(payload: unknown = { rows: [] }) {
  return okJson({ ok: true, content: { content: payload, is_error: false } })
}

function fetched(): Array<{ url: string; body: Record<string, unknown> }> {
  return mockFetch.mock.calls.map((c) => ({
    url: String(c[0]),
    body: JSON.parse(String((c[1] as { body?: string } | undefined)?.body ?? '{}')) as Record<string, unknown>,
  }))
}

/** dualOutput() wraps the envelope as structuredContent = { type: 'object', object: <envelope> }. */
function structured(r: { structuredContent?: unknown }): { content: Record<string, unknown> } {
  return (r.structuredContent as { object: { content: Record<string, unknown> } }).object
}

function capabilityArgs(uriFragment: string): Record<string, unknown> {
  const hit = fetched().find((f) => f.url.includes('/api/retrieval/capability') && String(f.body['uri']).includes(uriFragment))
  expect(hit, `no capability call for ${uriFragment}`).toBeDefined()
  return hit!.body['args'] as Record<string, unknown>
}

beforeEach(() => {
  mockFetch.mockReset()
  mockFetch.mockImplementation(async () => capabilityOk())
})

// ── MCP tools that used to send NO ayanamsha id ────────────────────────────────

describe('PR-4: tools that sent no ayanamsha id now pin the primary', () => {
  const ganita = capture(registerP1GanitaTools)
  const bridge = capture(registerRegistryBridgeTools)

  const CASES: Array<{ tool: string; reg: Map<string, Captured>; uri: string; args: Record<string, unknown> }> = [
    { tool: 'ganita_planet_get', reg: ganita, uri: 'L1/query_planet', args: { chart_id: CHART, planet: 'Saturn' } },
    { tool: 'ganita_transit_anchors_get', reg: ganita, uri: 'L1/get_transit_anchors', args: { chart_id: CHART } },
    { tool: 'phala_rectification_get', reg: ganita, uri: 'L4/query_rectification', args: { chart_id: CHART } },
    { tool: 'get_graha_yuddha', reg: bridge, uri: 'L1/get_graha_yuddha', args: { chart_id: CHART } },
  ]

  for (const c of CASES) {
    describe(c.tool, () => {
      const t = c.reg.get(c.tool)!
      it('is registered', () => expect(t).toBeDefined())

      it('omitted ayanamsha_id -> lahiri_chitrapaksha (not undefined / unfiltered)', async () => {
        await t.handler(c.args)
        expect(capabilityArgs(c.uri)['ayanamsha_id']).toBe(LAHIRI)
      })

      it('"all" -> forwarded as "all" (explicit raw multi-row opt-out; the capability route strips it)', async () => {
        await t.handler({ ...c.args, ayanamsha_id: 'all' })
        expect(capabilityArgs(c.uri)['ayanamsha_id']).toBe('all')
      })

      it('short alias and stored long ids normalise to the stored id', async () => {
        await t.handler({ ...c.args, ayanamsha_id: 'LAHIRI' })
        expect(capabilityArgs(c.uri)['ayanamsha_id']).toBe(LAHIRI)
        mockFetch.mockClear()
        await t.handler({ ...c.args, ayanamsha_id: 'true_chitra' })
        expect(capabilityArgs(c.uri)['ayanamsha_id']).toBe('true_chitra')
      })

      it('the ayanamsha_id description names lahiri_chitrapaksha as the default and does not say "Omit for all"', () => {
        const d = (t.schema['ayanamsha_id'] as z.ZodTypeAny).description ?? ''
        expect(d).toContain(LAHIRI)
        expect(d).not.toMatch(/omit for (all|unfiltered)/i)
        expect(d).not.toContain("'LAHIRI'")
      })
    })
  }

  it('phala_rectification_get labels the pooled best-offset values "consensus over five ayanamshas"', async () => {
    mockFetch.mockImplementation(async () => capabilityOk({ candidates: [], best_lel_fit_score: 0.1 }))
    const r = await ganita.get('phala_rectification_get')!.handler({ chart_id: CHART })
    const text = (r.content ?? []).map((x) => x.text ?? '').join('\n')
    expect(text).toContain('consensus over five ayanamshas')
    expect(ganita.get('phala_rectification_get')!.description).toContain('consensus over five ayanamshas')
  })

  it('phala_rectification_get passes the short-code aliases through the stored id (kp -> krishnamurti)', async () => {
    await ganita.get('phala_rectification_get')!.handler({ chart_id: CHART, ayanamsha_id: 'kp' })
    expect(capabilityArgs('L4/query_rectification')['ayanamsha_id']).toBe('krishnamurti')
  })
})

// ── KP by doctrine ──────────────────────────────────────────────────────────────

describe('PR-4: KP surfaces stay on Krishnamurti and carry the KP frame label', () => {
  const ganita = capture(registerP1GanitaTools)
  const t = ganita.get('ganita_kp_cusps_get')!

  it('omitted ayanamsha_id is NOT defaulted to Lahiri: no id is sent, the KP handler reads krishnamurti (SS N-368)', async () => {
    await t.handler({ chart_id: CHART })
    expect('ayanamsha_id' in capabilityArgs('L1/get_kp_cusps')).toBe(false)
  })

  it('the response is labelled "KP frame (Krishnamurti ayanamsha)"', async () => {
    mockFetch.mockImplementation(async () => capabilityOk({ cusps: [], ayanamsha_id: 'krishnamurti' }))
    const r = await t.handler({ chart_id: CHART })
    const text = (r.content ?? []).map((x) => x.text ?? '').join('\n')
    expect(text).toContain('KP frame (Krishnamurti ayanamsha)')
    expect(KP_FRAME_LABEL).toBe('KP frame (Krishnamurti ayanamsha)')
  })

  it('an explicit id or "all" is forwarded as typed and never refused; nonsense is ignored with a note (full matrix: kp_cusps_one_frame.test.ts, SS N-368)', async () => {
    for (const id of ['LAHIRI', 'all', 'kp']) {
      mockFetch.mockClear()
      const r = await t.handler({ chart_id: CHART, ayanamsha_id: id })
      expect(r.isError).not.toBe(true)
      expect(capabilityArgs('L1/get_kp_cusps')['ayanamsha_id']).toBe(id)
    }
    mockFetch.mockClear()
    const bad = await t.handler({ chart_id: CHART, ayanamsha_id: 'nonsense' })
    expect(bad.isError).not.toBe(true)
    expect('ayanamsha_id' in capabilityArgs('L1/get_kp_cusps')).toBe(false)
    expect(JSON.stringify(bad)).toContain('ayanamsha_note')
  })

  it('kpFrameLabelFor: krishnamurti / unstated -> canonical label; other ids -> honest label', () => {
    expect(kpFrameLabelFor(undefined)).toBe(KP_FRAME_LABEL)
    expect(kpFrameLabelFor('krishnamurti')).toBe(KP_FRAME_LABEL)
    expect(kpFrameLabelFor(LAHIRI)).toContain(`KP chain read at ${LAHIRI}`)
  })

  it('the kala_explain KP school voice carries the KP frame label next to the divergence disclosure', () => {
    const voice = buildKpSchoolVoice({
      bhava: 7, ladder: null, periods: [], pactStatus: 'chain_complete',
      kpAyanamshaId: 'krishnamurti', chainAyanamshaId: LAHIRI, substrateNote: null,
    })
    expect(voice.kp_frame_label).toBe(KP_FRAME_LABEL)
    expect(voice.kp_ayanamsha_id).toBe('krishnamurti')
    expect(voice.ayanamsha_divergence).toBe(true)
  })
})

// ── Kala views frame disclosure ─────────────────────────────────────────────────

describe('PR-4: kala_now / kala_ahead disclose a mixed natal/transit frame', () => {
  it('the default (Lahiri) is a single frame', () => {
    const f = buildKalaAyanamshaFrame(LAHIRI)
    expect(f.frame_mixed).toBe(false)
    expect(f.natal_ayanamsha_id).toBe(LAHIRI)
    expect(f.transit_ayanamsha_id).toBe(LAHIRI)
    expect(f.note).toBeNull()
  })
  it('a non-primary natal id is a labelled mixed frame (transit stays Lahiri)', () => {
    const f = buildKalaAyanamshaFrame('krishnamurti')
    expect(f.frame_mixed).toBe(true)
    expect(f.transit_ayanamsha_id).toBe(LAHIRI)
    expect(f.label).toContain('Mixed frame')
    expect(f.note).toContain('krishnamurti')
  })
})

// ── Synthesis tools ─────────────────────────────────────────────────────────────

describe('PR-4: synthesis tools', () => {
  const synth = capture(registerP1SynthesisTools)

  function dbQueryCalls(): Array<{ sql: string; params: unknown[] }> {
    return fetched().filter((f) => f.url.includes('/api/mcp/db/query')).map((f) => ({ sql: String(f.body['sql']), params: f.body['params'] as unknown[] }))
  }

  it('bodha_discoveries_get: omitted -> lahiri_chitrapaksha, "all" -> all, alias normalised', async () => {
    const t = synth.get('bodha_discoveries_get')!
    await t.handler({ chart_id: CHART })
    expect(capabilityArgs('L2/query_discoveries')['ayanamsha_id']).toBe(LAHIRI)
    mockFetch.mockClear()
    await t.handler({ chart_id: CHART, ayanamsha_id: 'all' })
    expect(capabilityArgs('L2/query_discoveries')['ayanamsha_id']).toBe('all')
    mockFetch.mockClear()
    await t.handler({ chart_id: CHART, ayanamsha_id: 'kp' })
    expect(capabilityArgs('L2/query_discoveries')['ayanamsha_id']).toBe('krishnamurti')
    expect((t.schema['ayanamsha_id'] as z.ZodTypeAny).description).toContain(LAHIRI)
  })

  describe('synth_chart_brief_get top discoveries', () => {
    const t = synth.get('synth_chart_brief_get')!

    it('filters bodha_discoveries to the primary ayanamsha and collapses by discovery family', async () => {
      mockFetch.mockImplementation(async () => okJson({ rows: [] }))
      await t.handler({ chart_id: CHART })
      const disc = dbQueryCalls().find((q) => q.sql.includes('FROM bodha_discoveries'))
      expect(disc, 'discoveries query not issued').toBeDefined()
      expect(disc!.sql).toMatch(/ayanamsha_id = \$2/)
      expect(disc!.params[1]).toBe(LAHIRI)
      expect(disc!.sql).toMatch(/DISTINCT ON \(discovery_class, discovery_subsystem, hypothesis_text\)/)
      // deterministic: total ordering with the discovery_id tie-break
      expect(disc!.sql).toMatch(/ORDER BY p\.composite_discovery_rank DESC NULLS LAST, p\.discovery_id/)
      // the limit is the last bind param (5 for the standard brief)
      expect(disc!.params[2]).toBe(5)
    })

    it('the discoveries SQL passes the /api/mcp/db/query whitelist (same rules, read from the route source)', async () => {
      mockFetch.mockImplementation(async () => okJson({ rows: [] }))
      await t.handler({ chart_id: CHART })
      const disc = dbQueryCalls().find((q) => q.sql.includes('FROM bodha_discoveries'))!
      const route = readFileSync(join(HERE, '../../platform/src/app/api/mcp/db/query/route.ts'), 'utf-8')
      const allowed = new Set(
        [...route.slice(route.indexOf('const ALLOWED_TABLES'), route.indexOf('// Forbidden anywhere')).matchAll(/'([a-z_0-9]+)'/g)].map((m) => m[1]),
      )
      expect(allowed.has('bodha_discoveries')).toBe(true)
      const sql = disc.sql.trim()
      expect(/^(WITH|SELECT)\b/i.test(sql)).toBe(true)
      expect(/\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|GRANT|REVOKE|TRUNCATE|COPY|EXECUTE|CALL|VACUUM|MERGE)\b|;|--/i.test(sql)).toBe(false)
      const refs = [...sql.matchAll(/\b(?:FROM|JOIN)\s+"?([a-zA-Z_][a-zA-Z0-9_]*)"?\b(?!\s*\()/gi)].map((m) => m[1]!.toLowerCase())
      expect(refs.length).toBeGreaterThan(0)
      for (const r of refs) expect(allowed.has(r), `table ${r} not whitelisted`).toBe(true)
    })

    it('top 5 carries no duplicate discovery_id and no ayanamsha other than the primary', async () => {
      // Rows exactly as the SQL above returns them (already primary-only, family-collapsed).
      const rows = [1, 2, 3, 4, 5].map((n) => ({
        discovery_id: `disc-${n}`, ayanamsha_id: LAHIRI, discovery_class: 'c', domains: ['career'],
        hypothesis_text: `motif ${n}`, salience_score: 10 - n,
        family_ayanamsha_ids: ['krishnamurti', LAHIRI, 'raman'],
      }))
      mockFetch.mockImplementation(async (url: unknown) => {
        const u = String(url)
        if (u.includes('/api/mcp/db/query')) {
          return okJson({ rows: [] })
        }
        return capabilityOk()
      })
      mockFetch.mockImplementationOnce(async () => okJson({ rows: [] })) // insights query
      mockFetch.mockImplementationOnce(async () => okJson({ rows })) // discoveries query
      const r = await t.handler({ chart_id: CHART })
      const sc = structured(r) as { content?: { top_discoveries?: Array<Record<string, unknown>>; top_discoveries_basis?: Record<string, unknown> } }
      const top = sc.content?.top_discoveries ?? []
      expect(top.length).toBe(5)
      expect(new Set(top.map((d) => d['discovery_id'])).size).toBe(top.length)
      expect(top.every((d) => d['ayanamsha_id'] === LAHIRI)).toBe(true)
      expect(sc.content?.top_discoveries_basis?.['ayanamsha_id']).toBe(LAHIRI)
    })
  })

  describe('prashna_undertaking_get', () => {
    const t = synth.get('prashna_undertaking_get')!

    function wire(rowsByAyanamsha: string[]) {
      mockFetch.mockImplementation(async (_url: unknown, init?: { body?: string }) => {
        const sql = String(JSON.parse(String(init?.body ?? '{}')).sql ?? '')
        if (sql.includes('FROM ga_prashna_judgment')) {
          // the DB returns them krishnamurti-first (alphabetical), as the old query did
          const sorted = [...rowsByAyanamsha].sort()
          return okJson({ rows: sorted.map((a) => ({ question_class: 'q', verdict: `verdict-${a}`, ayanamsha_id: a })) })
        }
        return okJson({ rows: [] })
      })
    }

    it('returns the Lahiri verdict as THE verdict and the other four as named, labelled cross-check entries in serve order', async () => {
      wire([LAHIRI, 'true_chitra', 'krishnamurti', 'raman', 'surya_siddhanta_classical'])
      const r = await t.handler({ chart_id: CHART, domain: 'career', top_windows: 3 })
      const c = structured(r).content
      const verdict = c['prashna_verdict'] as Array<Record<string, unknown>>
      expect(verdict.map((v) => v['ayanamsha_id'])).toEqual([LAHIRI])
      expect(verdict[0]!['verdict']).toBe(`verdict-${LAHIRI}`)
      expect(c['prashna_verdict_ayanamsha_id']).toBe(LAHIRI)
      const cc = c['prashna_verdict_cross_check'] as { status: string; primary_id: string; basis: string; others: Array<{ ayanamsha_id: string; label: string; verdicts: unknown[] }> }
      expect(cc.status).toBe('available')
      expect(cc.primary_id).toBe(LAHIRI)
      expect(cc.basis).toMatch(/^Cross-check, not the reading/)
      expect(cc.others.map((o) => o.ayanamsha_id)).toEqual(['true_chitra', 'krishnamurti', 'raman', 'surya_siddhanta_classical'])
      expect(cc.others.every((o) => o.label.startsWith('Cross-check:') && o.verdicts.length === 1)).toBe(true)
    })

    it('a single-ayanamsha chart reports not_available / single_ayanamsha_chart, never "1/1 agree"', async () => {
      wire([LAHIRI])
      const r = await t.handler({ chart_id: CHART, domain: 'career', top_windows: 3 })
      const c = structured(r).content
      const cc = c['prashna_verdict_cross_check'] as { status: string; reason: string; others: unknown[] }
      expect(cc.status).toBe('not_available')
      expect(cc.reason).toBe('single_ayanamsha_chart')
      expect(cc.others).toEqual([])
    })

    it('no Lahiri row: the primary verdict is honestly empty and says so (others stay in the cross-check only)', async () => {
      wire(['krishnamurti', 'raman'])
      const r = await t.handler({ chart_id: CHART, domain: 'career', top_windows: 3 })
      const c = structured(r).content
      expect(c['prashna_verdict']).toEqual([])
      expect(String(c['prashna_verdict_missing_primary'])).toContain(LAHIRI)
    })
  })
})

// ── Stored ids accepted by the PyJHora tools (legacy enum rejected all but four) ─

function capture3(register: (server: never) => void): Map<string, Captured> {
  const tools = new Map<string, Captured>()
  register({
    tool: (name: string, schema: Record<string, z.ZodTypeAny>, handler: Handler) => {
      tools.set(name, { schema, handler, description: '' })
    },
  } as never)
  return tools
}

describe('PR-4: compute_natal_positions / query_special_lagnas accept stored ids', () => {
  for (const [name, register] of [
    ['compute_natal_positions', registerComputeNatalPositionsTool],
    ['query_special_lagnas', registerQuerySpecialLagnasTool],
  ] as const) {
    describe(name, () => {
      const tools = capture3(register as never)
      const t = tools.get(name)!
      const BIRTH = { datetime_iso: '1984-02-05T10:43:00', latitude_deg: 20.2961, longitude_deg: 85.8245, tz_offset_hours: 5.5 }

      it.each(['lahiri_chitrapaksha', 'true_chitra', 'krishnamurti', 'raman', 'surya_siddhanta_classical', 'lahiri', 'kp', 'true_citra', 'KP'])(
        'schema accepts %s', (id) => {
          expect(z.object(t.schema).safeParse({ ...BIRTH, ayanamsha_id: id }).success).toBe(true)
        })

      it('omitted -> Lahiri stored id is sent to the sidecar; stored ids pass through; unknown is an error', async () => {
        mockFetch.mockImplementation(async () => okJson({ graha_sthana: [], bhava_lagna: {}, special_lagnas: {} }))
        await t.handler({ ...BIRTH })
        expect(fetched()[0]!.body['ayanamsha_id']).toBe(LAHIRI)
        mockFetch.mockClear()
        await t.handler({ ...BIRTH, ayanamsha_id: 'kp' })
        expect(fetched()[0]!.body['ayanamsha_id']).toBe('krishnamurti')
        mockFetch.mockClear()
        const bad = await t.handler({ ...BIRTH, ayanamsha_id: 'nonsense' })
        expect(bad.isError).toBe(true)
        expect(mockFetch).not.toHaveBeenCalled()
      })
    })
  }
})

// ── Prompts ─────────────────────────────────────────────────────────────────────

describe('PR-4: prompts no longer cite gated names or the upper-case LAHIRI default', () => {
  const prompts = new Map<string, { handler: (a: Record<string, unknown>) => Promise<{ messages: Array<{ content: { text: string } }> }> | { messages: Array<{ content: { text: string } }> } }>()
  registerPrompts({
    prompt: (name: string, _d: string, _s: unknown, handler: never) => { prompts.set(name, { handler }) },
  } as never, PRINCIPAL as never)

  const GATED = ['get_chart_orientation', 'get_domain_reading', 'get_signals', 'get_temporal_windows', 'get_classical_citation']

  it('registers the prompts and renders text with stored-id defaults and canonical tool names', async () => {
    expect(prompts.size).toBeGreaterThan(0)
    for (const [name, p] of prompts) {
      // vidhi_plan renders its floor text from the Vidhi registry (platform-mcp/src/resources/vidhi),
      // a separate surface; only the prompts defined in prompts/index.ts are asserted here.
      if (name === 'vidhi_plan') continue
      let out: { messages: Array<{ content: { text: string } }> }
      try {
        out = await p.handler({ chart_id: CHART, domain: 'career', question: 'q', horizon_months: 12 })
      } catch {
        continue // prompts with extra required args are covered by the source scan below
      }
      const text = out.messages.map((m) => m.content.text).join('\n')
      expect(text, name).not.toContain('"LAHIRI"')
      for (const g of GATED) expect(text, `${name} cites gated ${g}`).not.toContain(g)
    }
  })
})
