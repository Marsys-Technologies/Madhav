/**
 * kp_reaching_wrappers.test.ts — SS N-368 (Lahiri primary, PR-4): MCP wrappers that REACH a KP-frame read
 * must not turn an omitted ayanamsha_id into an explicit one.
 *
 * Defect: the wrappers pinned the Lahiri primary on omission (resolveChartFactsAyanamsha: falsy -> Lahiri) and
 * sent an explicit `ayanamsha_id` to /api/retrieval/capability. The platform KP handlers (PR-2) cannot tell a
 * wrapper-pinned id from a caller's request, so an MCP caller who named nothing got a false KP note ("the
 * requested ayanamsha does not apply here"). Fix: when the caller OMITTED the id AND the call reaches a
 * KP-frame read, no ayanamsha_id is sent (the handler applies its own default). An explicit id is forwarded
 * (normalised as before; "all" stays "all"); a call that cannot reach KP rows keeps the Lahiri pin.
 *
 * KP-reaching, per wrapper (platform handler -> why):
 *   query_chart_facts, ganita_chart_facts_get -> chart_facts_query: no category filter = a default page that carries
 *       KP rows; or a category list naming a KP-frame category;
 *   get_dashas, ganita_dashas_get, ganita_dasha_periods_get, query_dasha_periods -> get_dashas: system vimshottari_kp,
 *       "all" or an unrecognised system (a two-leg page with KP rows);
 *   ganita_condition_get facet=karakas -> get_karakas: the default page names KP categories.
 * Control: the same tools with a non-KP category / system / facet keep sending Lahiri.
 *
 * No network: global fetch is mocked.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import type { z } from 'zod'

process.env['SERVICE_TOKEN'] = 'test-service-token'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)
vi.mock('../src/lib/authz.js', () => ({ remoteAuthorize: vi.fn().mockResolvedValue(true) }))

import { registerP1GanitaTools } from '../src/tools/register_p1_ganita.js'
import { registerP1AliasTools } from '../src/tools/register_p1_aliases.js'
import { registerRegistryBridgeTools } from '../src/tools/registry_bridge.js'
import { KP_FRAME_CATEGORIES, categoryFilterReachesKpFrame, dashaSystemReachesKpFrame, ayanamshaArgForKpReach } from '../src/lib/kp_frame.js'
import { resolveChartFactsAyanamsha } from '../src/lib/ayanamsha.js'

const HERE = dirname(fileURLToPath(import.meta.url))
const LAHIRI = 'lahiri_chitrapaksha'
const CHART = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const PRINCIPAL = { user_uid: 'test-uid', audience_tier: 'super_admin' as const, key_id: 'test-key-001' }

type Handler = (args: Record<string, unknown>) => Promise<{ isError?: boolean }>
function capture(register: (server: never, principal: never) => void): Map<string, Handler> {
  const tools = new Map<string, Handler>()
  const server = {
    tool: (name: string, ...rest: unknown[]) => {
      tools.set(name, rest[rest.length - 1] as Handler)
      void (rest as unknown as z.ZodTypeAny[])
    },
  }
  register(server as never, PRINCIPAL as never)
  return tools
}

function capabilityOk(payload: unknown = { rows: [] }) {
  const body = { ok: true, content: { content: payload, is_error: false } }
  return { ok: true, status: 200, json: () => Promise.resolve(body), text: () => Promise.resolve(JSON.stringify(body)) }
}

function sentArgs(uriFragment: string): Record<string, unknown> {
  const hit = mockFetch.mock.calls
    .map((c) => JSON.parse(String((c[1] as { body?: string }).body ?? '{}')) as { uri?: string; args?: Record<string, unknown> })
    .find((b) => String(b.uri).includes(uriFragment))
  expect(hit, `no capability call for ${uriFragment}`).toBeDefined()
  return hit!.args ?? {}
}

beforeEach(() => {
  mockFetch.mockReset()
  mockFetch.mockImplementation(async () => capabilityOk())
})

const ganita = capture(registerP1GanitaTools)
const aliases = capture(registerP1AliasTools)
const bridge = capture(registerRegistryBridgeTools)

interface Case {
  tool: string
  reg: Map<string, Handler>
  uri: string
  /** call that reaches a KP-frame read */
  kp: Record<string, unknown>
  /** call that cannot (control) */
  nonKp: Record<string, unknown>
  /** capability the control call reaches, when it differs */
  nonKpUri?: string
}

const CASES: Case[] = [
  { tool: 'query_chart_facts', reg: bridge, uri: 'L1/chart_facts_query', kp: { chart_id: CHART }, nonKp: { chart_id: CHART, category: 'graha_position' } },
  { tool: 'query_chart_facts', reg: bridge, uri: 'L1/chart_facts_query', kp: { chart_id: CHART, category: 'graha_position,cusp_kp_lords' }, nonKp: { chart_id: CHART, category: 'graha_position' } },
  { tool: 'ganita_chart_facts_get', reg: aliases, uri: 'L1/chart_facts_query', kp: { chart_id: CHART }, nonKp: { chart_id: CHART, category: 'graha_position' } },
  { tool: 'ganita_chart_facts_get', reg: aliases, uri: 'L1/chart_facts_query', kp: { chart_id: CHART, category: 'kp_house_significators' }, nonKp: { chart_id: CHART, category: 'graha_position' } },
  { tool: 'get_dashas', reg: bridge, uri: 'L1/get_dashas', kp: { chart_id: CHART, system_id: 'vimshottari_kp' }, nonKp: { chart_id: CHART } },
  { tool: 'get_dashas', reg: bridge, uri: 'L1/get_dashas', kp: { chart_id: CHART, system_id: 'all' }, nonKp: { chart_id: CHART, system_id: 'YOGINI' } },
  { tool: 'ganita_dashas_get', reg: aliases, uri: 'L1/get_dashas', kp: { chart_id: CHART, system: 'vimshottari_kp' }, nonKp: { chart_id: CHART, system: 'vimshottari' } },
  { tool: 'ganita_dasha_periods_get', reg: aliases, uri: 'L1/get_dashas', kp: { chart_id: CHART, system_id: 'all' }, nonKp: { chart_id: CHART } },
  { tool: 'query_dasha_periods', reg: aliases, uri: 'L1/get_dashas', kp: { chart_id: CHART, dasha_system: 'VIMSHOTTARI_KP' }, nonKp: { chart_id: CHART, dasha_system: 'yogini' } },
  { tool: 'ganita_condition_get', reg: ganita, uri: 'L1/get_karakas', kp: { chart_id: CHART, facet: 'karakas' }, nonKp: { chart_id: CHART, facet: 'dignity' }, nonKpUri: 'L1/get_dignity' },
]

describe.each(CASES)('$tool ($uri): $kp', ({ tool, reg, uri, kp, nonKp, nonKpUri }) => {
  const run = (args: Record<string, unknown>) => reg.get(tool)!(args)

  it('is registered', () => expect(reg.get(tool)).toBeDefined())

  it('KP-reaching + id OMITTED -> no ayanamsha_id is sent', async () => {
    await run(kp)
    expect(sentArgs(uri)).not.toHaveProperty('ayanamsha_id')
  })

  it('KP-reaching + blank id -> no ayanamsha_id is sent', async () => {
    await run({ ...kp, ayanamsha_id: '  ' })
    expect(sentArgs(uri)).not.toHaveProperty('ayanamsha_id')
  })

  it.each([
    ['raman', 'raman'], ['LAHIRI', LAHIRI], [LAHIRI, LAHIRI], ['KP', 'krishnamurti'], ['all', 'all'],
  ])('KP-reaching + explicit %s -> forwarded as %s (the platform decides the frame and the note)', async (typed, forwarded) => {
    await run({ ...kp, ayanamsha_id: typed })
    expect(sentArgs(uri)['ayanamsha_id']).toBe(forwarded)
  })

  it('control: a call that cannot reach KP rows still pins the Lahiri primary on omission', async () => {
    await run(nonKp)
    expect(sentArgs(nonKpUri ?? uri)['ayanamsha_id']).toBe(LAHIRI)
  })
})

describe('the KP-reach predicates', () => {
  it('categoryFilterReachesKpFrame: no filter or any KP-frame category -> true', () => {
    expect(categoryFilterReachesKpFrame(undefined)).toBe(true)
    expect(categoryFilterReachesKpFrame('')).toBe(true)
    for (const c of KP_FRAME_CATEGORIES) expect(categoryFilterReachesKpFrame(`graha_position, ${c}`)).toBe(true)
    expect(categoryFilterReachesKpFrame('graha_position,yoga_label')).toBe(false)
  })

  it('dashaSystemReachesKpFrame: absent / a plain system -> false; vimshottari_kp, all, unrecognised -> true', () => {
    for (const s of [undefined, '', 'VIMSHOTTARI', 'yogini', 'Chara_Karaka', 'naisargika']) expect(dashaSystemReachesKpFrame(s)).toBe(false)
    for (const s of ['vimshottari_kp', 'all', 'ALL', 'whatever']) expect(dashaSystemReachesKpFrame(s)).toBe(true)
  })

  it('ayanamshaArgForKpReach: omits only when omitted AND KP-reaching', () => {
    expect(ayanamshaArgForKpReach(undefined, true, resolveChartFactsAyanamsha)).toEqual({})
    expect(ayanamshaArgForKpReach(undefined, false, resolveChartFactsAyanamsha)).toEqual({ ayanamsha_id: LAHIRI })
    expect(ayanamshaArgForKpReach('raman', true, resolveChartFactsAyanamsha)).toEqual({ ayanamsha_id: 'raman' })
  })

  it('the mirrored KP category list equals the platform source list (PR-2 kp_categories.ts when it is in the tree)', () => {
    let src: string
    try {
      src = readFileSync(join(HERE, '../../platform/src/lib/retrieval/registry/kp_categories.ts'), 'utf8')
    } catch {
      return // lands with PR-2; the batch-merge tree runs this comparison
    }
    const block = /KP_FRAME_CATEGORIES[^=]*=\s*\[([\s\S]*?)\]/.exec(src)?.[1] ?? ''
    const names = [...block.matchAll(/'([a-z_]+)'/g)].map((m) => m[1])
    expect(names).toEqual([...KP_FRAME_CATEGORIES])
  })
})
