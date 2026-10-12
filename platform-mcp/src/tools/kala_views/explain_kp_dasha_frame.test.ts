/**
 * explain_kp_dasha_frame.test.ts: SS N-412 item 1 (Lahiri-primary combined batch, PR-4).
 *
 * `fetchKpSchoolVoice` used to read the running `vimshottari_kp` stack at the CHAIN ayanamsha (Lahiri by
 * default) while labelling the whole voice KP. By doctrine KP has one frame (krishnamurti, retrieval/kp_frame.ts), so
 * the stack must be read there. Live proof of harm on chart 482012f1: the level-3 lord is Rahu at krishnamurti but Mars at
 * lahiri_chitrapaksha, so the KP-labelled voice was judging the wrong running lords.
 *
 * The mocked platform answers get_dashas per the ayanamsha_id it RECEIVES, with exactly that divergence. On the old code
 * (ayanamsha_id: chainAyanamshaId) the voice reports Mars and this file fails; on the fix it reports Rahu and never Mars.
 * No network, no DB.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../../types.js'
import { fetchKpSchoolVoice } from './explain.js'
import { KP_FRAME_AYANAMSHA, KP_FRAME_LABEL } from '../../lib/kp_frame.js'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const LAHIRI = 'lahiri_chitrapaksha'
const PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }

/** vimshottari_kp running stack of the live divergence: MD/AD identical, level 3 differs by ayanamsha. */
const STACK: Record<string, Array<Record<string, unknown>>> = {
  [KP_FRAME_AYANAMSHA]: [
    { level_n: 1, lord_graha: 'Mars', start_date: '2020-01-01', end_date: '2027-01-01' },
    { level_n: 2, lord_graha: 'Saturn', start_date: '2025-01-01', end_date: '2027-01-01' },
    { level_n: 3, lord_graha: 'Rahu', start_date: '2026-06-01', end_date: '2026-12-01' },
  ],
  [LAHIRI]: [
    { level_n: 1, lord_graha: 'Mars', start_date: '2020-01-01', end_date: '2027-01-01' },
    { level_n: 2, lord_graha: 'Saturn', start_date: '2025-01-01', end_date: '2027-01-01' },
    { level_n: 3, lord_graha: 'Mars', start_date: '2026-06-01', end_date: '2026-12-01' },
  ],
}

const LADDER_ROWS = [
  // house 7 ladder: Rahu signifies via level a (strongest limb), Mars only via a weaker limb
  { fact_subject: 'HOUSE_07', fact_key: 'level_a', fact_value_text: 'Rahu', fact_id: 'f-a' },
  { fact_subject: 'HOUSE_07', fact_key: 'level_b', fact_value_text: 'Mars', fact_id: 'f-b' },
]

const seen: Array<{ uri: string; args: Record<string, unknown> }> = []

beforeEach(() => {
  seen.length = 0
  vi.stubGlobal('fetch', vi.fn(async (_url: string, init?: RequestInit) => {
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri: string; args: Record<string, unknown> }
    seen.push({ uri: body.uri, args: body.args })
    let inner: Record<string, unknown> = {}
    if (body.uri === 'marsys://tool/L1/get_dashas') {
      const aya = String(body.args['ayanamsha_id'])
      inner = { rows: STACK[aya] ?? [] }
    } else if (body.uri === 'marsys://tool/L1/chart_facts_query') {
      inner = { rows: LADDER_ROWS }
    }
    return {
      ok: true,
      json: async () => ({ ok: true, content: { content: inner, is_error: false } }),
      text: async () => '',
    } as Response
  }))
})

describe('fetchKpSchoolVoice reads the running vimshottari_kp stack in the KP frame (SS N-412 item 1)', () => {
  it('chain ayanamsha = Lahiri: the KP-labelled voice judges Rahu (krishnamurti), never Mars (lahiri level 3)', async () => {
    const voice = await fetchKpSchoolVoice({
      chartId: CHART, bhava: 7, asOfDate: '2026-08-04', chainAyanamshaId: LAHIRI, pactStatus: 'chain_complete', principal: PRINCIPAL,
    })
    expect(voice.kp_frame_label).toBe(KP_FRAME_LABEL)
    const pd = voice.running_lords.find((r) => r.running_level === 'PD')
    expect(pd?.lord).toBe('Rahu')
    // the level-3 Mars of the Lahiri stack must not appear as a PD lord; Mars is only the MD here (identical in both frames)
    expect(voice.running_lords.filter((r) => r.running_level === 'PD').map((r) => r.lord)).not.toContain('Mars')
    expect(voice.running_lords.map((r) => `${r.running_level}:${r.lord}`)).toEqual(['MD:Mars', 'AD:Saturn', 'PD:Rahu'])
    const dashaCall = seen.find((c) => c.uri === 'marsys://tool/L1/get_dashas')
    expect(dashaCall, 'get_dashas was called').toBeDefined()
    expect(dashaCall!.args['ayanamsha_id']).toBe(KP_FRAME_AYANAMSHA)
    expect(dashaCall!.args['system_id']).toBe('vimshottari_kp')

    expect(voice.kp_ayanamsha_id).toBe(KP_FRAME_AYANAMSHA)
    expect(voice.chain_ayanamsha_id).toBe(LAHIRI)
  })

  it('a non-Lahiri chain id (raman) is not what the KP stack is read at either', async () => {
    await fetchKpSchoolVoice({
      chartId: CHART, bhava: 7, asOfDate: '2026-08-04', chainAyanamshaId: 'raman', pactStatus: 'chain_complete', principal: PRINCIPAL,
    })
    const dashaCall = seen.find((c) => c.uri === 'marsys://tool/L1/get_dashas')!
    expect(dashaCall.args['ayanamsha_id']).toBe(KP_FRAME_AYANAMSHA)
    const ladderCall = seen.find((c) => c.uri === 'marsys://tool/L1/chart_facts_query')!
    expect(ladderCall.args['ayanamsha_id']).toBe(KP_FRAME_AYANAMSHA)
  })
})
