/**
 * kp_cusps_one_frame.test.ts — SS N-368 (Lahiri primary, PR-4): `ganita_kp_cusps_get` follows the
 * ONE-FRAME KP rule, with no asymmetry between the platform handlers and the MCP wrapper.
 *
 * The KP frame has ONE ayanamsha, Krishnamurti. The platform get_kp_cusps handler (PR-2) owns the rule:
 * it reads krishnamurti whatever id it receives, keeps the label "KP frame (Krishnamurti ayanamsha)" and
 * adds `ayanamsha_note` ONLY for an explicit non-Krishnamurti id or "all". So the wrapper must report the
 * caller's intent faithfully:
 *   - id omitted / blank  -> NO ayanamsha_id is sent (a pinned default would read as a request and draw a
 *                            false note);
 *   - id passed           -> forwarded exactly as typed (Lahiri, raman, "all", aliases, krishnamurti);
 *   - nonsense id         -> the capability route would 400 before the handler runs, so it is not forwarded;
 *                            it is ignored (never an error) and noted by the wrapper with PR-2's wording.
 * The label is always present; a note that the platform returns passes through untouched.
 *
 * No network: global fetch is mocked. (The platform half, through the real handler, is covered by PR-2's
 * kp_no_false_note.bridge.test.ts and platform/.../kp_cusps_bridge_no_inject.test.ts.)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { z } from 'zod'

process.env['SERVICE_TOKEN'] = 'test-service-token'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)
vi.mock('../src/lib/authz.js', () => ({ remoteAuthorize: vi.fn().mockResolvedValue(true) }))

import { registerP1GanitaTools } from '../src/tools/register_p1_ganita.js'

const CHART = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const PRINCIPAL = { user_uid: 'test-uid', audience_tier: 'super_admin' as const, key_id: 'test-key-001' }
const LABEL = 'KP frame (Krishnamurti ayanamsha)'

type Handler = (args: Record<string, unknown>) => Promise<{ isError?: boolean; content?: Array<{ text?: string }>; structuredContent?: unknown }>

function getTool(): Handler {
  let handler: Handler | undefined
  const server = {
    tool: (name: string, _d: string, _s: Record<string, z.ZodTypeAny>, h: Handler) => {
      if (name === 'ganita_kp_cusps_get') handler = h
    },
  }
  registerP1GanitaTools(server as never, PRINCIPAL as never)
  expect(handler).toBeDefined()
  return handler!
}

function capabilityOk(payload: unknown) {
  const body = { ok: true, content: { content: payload, is_error: false } }
  return { ok: true, status: 200, json: () => Promise.resolve(body), text: () => Promise.resolve(JSON.stringify(body)) }
}

function kpCalls(): Array<Record<string, unknown>> {
  return mockFetch.mock.calls
    .map((c) => JSON.parse(String((c[1] as { body?: string }).body ?? '{}')) as { uri?: string; args?: Record<string, unknown> })
    .filter((b) => String(b.uri).includes('L1/get_kp_cusps'))
    .map((b) => b.args ?? {})
}

/** The stamped KP payload (kp_frame_label, ayanamsha_note, ...) wherever the envelope put it. */
function payloadOf(r: { structuredContent?: unknown; content?: Array<{ text?: string }> }): Record<string, unknown> {
  const env = (r.structuredContent as { object?: { content?: Record<string, unknown> } } | undefined)?.object
  expect(env?.content, 'envelope content').toBeDefined()
  return env!.content!
}

beforeEach(() => {
  mockFetch.mockReset()
  mockFetch.mockImplementation(async () => capabilityOk({ cusps: [], ayanamsha_id: 'krishnamurti' }))
})

const OMITTED: Array<[string, Record<string, unknown>]> = [
  ['omitted', {}],
  ['undefined', { ayanamsha_id: undefined }],
  ['blank', { ayanamsha_id: '   ' }],
]

// explicit ids are forwarded exactly as typed: the platform decides the frame and the note
const EXPLICIT: string[] = [
  'krishnamurti', 'KP', 'kp',
  'lahiri_chitrapaksha', 'LAHIRI', 'raman', 'true_chitra', 'surya_siddhanta_classical', 'suryasiddhanta',
  'all', 'ALL',
]

describe('ganita_kp_cusps_get: one KP frame (SS N-368)', () => {
  describe.each(OMITTED)('id %s', (_n, extra) => {
    it('sends no ayanamsha_id at all, keeps the label, adds no note', async () => {
      const r = await getTool()({ chart_id: CHART, ...extra })
      expect(r.isError).not.toBe(true)
      const calls = kpCalls()
      expect(calls).toHaveLength(1)
      expect(calls[0]).not.toHaveProperty('ayanamsha_id')
      expect(calls[0]).not.toHaveProperty('ayanamsha_scope')
      const p = payloadOf(r)
      expect(p['kp_frame_label']).toBe(LABEL)
      expect(p['kp_frame_ayanamsha_id']).toBe('krishnamurti')
      expect(p).not.toHaveProperty('ayanamsha_note')
    })
  })

  describe.each(EXPLICIT)('explicit id %s', (raw) => {
    it('is forwarded exactly as typed (not normalised, not refused), the label is kept', async () => {
      const r = await getTool()({ chart_id: CHART, ayanamsha_id: raw })
      expect(r.isError).not.toBe(true) // "all" used to be refused
      const calls = kpCalls()
      expect(calls).toHaveLength(1)
      expect(calls[0]!['ayanamsha_id']).toBe(raw)
      expect(payloadOf(r)['kp_frame_label']).toBe(LABEL)
    })

    it('a note returned by the platform handler passes through unchanged', async () => {
      const note = `KP has one frame by doctrine (Krishnamurti); the requested ayanamsha_id/scope '${raw}' does not apply here`
      mockFetch.mockImplementation(async () => capabilityOk({ cusps: [], ayanamsha_id: 'krishnamurti', ayanamsha_note: note }))
      const r = await getTool()({ chart_id: CHART, ayanamsha_id: raw })
      expect(payloadOf(r)['ayanamsha_note']).toBe(note)
      expect(payloadOf(r)['kp_frame_label']).toBe(LABEL)
    })
  })

  it('a nonsense id is ignored (no error, not forwarded), the label is kept and the wrapper adds the note', async () => {
    const r = await getTool()({ chart_id: CHART, ayanamsha_id: 'nonsense' })
    expect(r.isError).not.toBe(true)
    const calls = kpCalls()
    expect(calls).toHaveLength(1)
    expect(calls[0]).not.toHaveProperty('ayanamsha_id')
    const p = payloadOf(r)
    expect(p['kp_frame_label']).toBe(LABEL)
    expect(p['ayanamsha_note']).toBe(
      "KP has one frame by doctrine (Krishnamurti); the requested ayanamsha_id/scope 'nonsense' does not apply here",
    )
  })

  it('include_graha_kp_lords is forwarded next to the id', async () => {
    await getTool()({ chart_id: CHART, ayanamsha_id: 'raman', include_graha_kp_lords: true })
    expect(kpCalls()[0]).toMatchObject({ ayanamsha_id: 'raman', include_graha_kp_lords: true })
  })

  it('doctrinal branches: an echoed krishnamurti and an absent echo both carry the canonical label and the krishnamurti id', async () => {
    mockFetch.mockImplementation(async () => capabilityOk({ cusps: [], ayanamsha_id: 'krishnamurti' }))
    const echoed = payloadOf(await getTool()({ chart_id: CHART }))
    expect(echoed['kp_frame_label']).toBe(LABEL)
    expect(echoed['kp_frame_ayanamsha_id']).toBe('krishnamurti')
    expect(echoed).not.toHaveProperty('kp_frame_warning')
    mockFetch.mockImplementation(async () => capabilityOk({ cusps: [] }))
    const bare = payloadOf(await getTool()({ chart_id: CHART }))
    expect(bare['kp_frame_label']).toBe(LABEL)
    expect(bare['kp_frame_ayanamsha_id']).toBe('krishnamurti')
    expect(bare).not.toHaveProperty('kp_frame_warning')
  })

  it('an honest label: a platform that answered in another frame is not relabelled as the KP frame', async () => {
    mockFetch.mockImplementation(async () => capabilityOk({ cusps: [], ayanamsha_id: 'lahiri_chitrapaksha' }))
    const r = await getTool()({ chart_id: CHART })
    const p = payloadOf(r)
    expect(p['kp_frame_label']).toBeNull()
    expect(p['kp_frame_ayanamsha_id']).toBe('lahiri_chitrapaksha')
    expect(String(p['kp_frame_warning'])).toContain("answered in 'lahiri_chitrapaksha', not the KP frame")
  })
})
