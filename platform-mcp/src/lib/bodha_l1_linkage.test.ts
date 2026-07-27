/**
 * bodha_l1_linkage.test.ts — ŚODHANA T2 (MC-001 freshness stamp).
 * Anti-vacuous: the live MC-001 case (0% resolution) must produce fresh:false.
 */
import { describe, it, expect } from 'vitest'
import { makeBodhaL1Linkage, resolveBodhaL1Linkage, type LinkageProbe } from './bodha_l1_linkage.js'

const LIVE = 'c5926cc8-5358-4ab6-8ef4-258785a58f79'

describe('makeBodhaL1Linkage — MC-001', () => {
  it('fresh when all refs resolve to the live build', () => {
    const probe: LinkageProbe = {
      liveL1BuildId: LIVE, sampledConstituentRefs: 500, resolvedConstituentRefs: 500, resolvedToL1BuildId: LIVE,
    }
    const l = makeBodhaL1Linkage(probe)
    expect(l.fresh).toBe(true)
    expect(l.built_against_hash).toBe(LIVE)
    expect(l.live_hash).toBe(LIVE)
    expect(l.constituent_resolution_pct).toBe(100)
    expect(l.note).toBeUndefined()
  })

  it('STALE: 0% resolution (the live MC-001 case) → fresh:false, built_against null', () => {
    const probe: LinkageProbe = {
      liveL1BuildId: LIVE, sampledConstituentRefs: 500, resolvedConstituentRefs: 0, resolvedToL1BuildId: null,
    }
    const l = makeBodhaL1Linkage(probe)
    expect(l.fresh).toBe(false)
    expect(l.built_against_hash).toBeNull()
    expect(l.live_hash).toBe(LIVE)
    expect(l.constituent_resolution_pct).toBe(0)
    expect(l.note).toContain('STALE')
  })

  it('PARTIAL: minority resolution → fresh:false with a partial note', () => {
    const probe: LinkageProbe = {
      liveL1BuildId: LIVE, sampledConstituentRefs: 100, resolvedConstituentRefs: 68, resolvedToL1BuildId: LIVE,
    }
    const l = makeBodhaL1Linkage(probe)
    expect(l.fresh).toBe(false)
    expect(l.constituent_resolution_pct).toBe(68)
    expect(l.note).toContain('PARTIAL')
  })

  it('just below threshold (98%) is not fresh; at/above 99% is fresh', () => {
    expect(makeBodhaL1Linkage({ liveL1BuildId: LIVE, sampledConstituentRefs: 100, resolvedConstituentRefs: 98, resolvedToL1BuildId: LIVE }).fresh).toBe(false)
    expect(makeBodhaL1Linkage({ liveL1BuildId: LIVE, sampledConstituentRefs: 100, resolvedConstituentRefs: 99, resolvedToL1BuildId: LIVE }).fresh).toBe(true)
  })

  it('no sample → indeterminate, fresh:false', () => {
    const l = makeBodhaL1Linkage({ liveL1BuildId: LIVE, sampledConstituentRefs: 0, resolvedConstituentRefs: 0, resolvedToL1BuildId: null })
    expect(l.fresh).toBe(false)
    expect(l.constituent_resolution_pct).toBeNull()
    expect(l.note).toContain('indeterminate')
  })

  it('resolveBodhaL1Linkage returns a safe stamp when the probe throws', async () => {
    const l = await resolveBodhaL1Linkage('chart', async () => { throw new Error('db down') })
    expect(l.fresh).toBe(false)
    expect(l.note).toContain('probe failed')
  })
})
