import { describe, it } from 'vitest'
import type { MsrSignal, Message } from '../types'

describe('DB types - compile check', () => {
  it('MsrSignal has required fields', () => {
    const _s: MsrSignal = {
      signal_id: 'SIG.MSR.001',
      native_id: 'abhisek',
      domain: 'career',
      planet: null,
      house: null,
      nakshatra: null,
      dasha_lord: null,
      confidence: 0.95,
      significance: 0.92,
      is_forward_looking: false,
      claim_text: 'test',
      classical_basis: null,
      falsifier: null,
      source_file: 'MSR_v3_0.md',
      source_version: '3.0',
      ingested_at: new Date().toISOString(),
    }
  })
  it('Message has native_id', () => {
    const m = {} as Message
    const _: string = m.native_id
  })
})
