import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
import { AssetProgressBar, SEG } from '../AssetProgressBar'
import { ALL_ASSET_STATES } from '@/app/api/cockpit/stats/deriveState'

/**
 * Packet B2 — C-3 (review B1_rereview2_20260926T193112Z.md, "BLOCKS whichever
 * packet next touches AssetProgressBar or adds an AssetState").
 *
 * THE DEFECT: `SEG` was `Record<string, SegmentColors>` — an index-signature type
 * has no required properties, so `SEG.partial`/`SEG.incomplete` being absent
 * compiled clean under `tsc`. Both states silently rendered 'dormant' styling in
 * production (`SEG[effectiveState] ?? SEG.dormant`).
 *
 * THE FIX: SEG's type annotation was removed so it infers its own literal-keyed
 * type, and `const _exhaustive: Record<AssetState, SegmentColors> = SEG` in
 * AssetProgressBar.tsx now makes `tsc` refuse to compile if a future AssetState
 * member has no SEG entry — proven by the delete-the-fix mutation recorded in
 * this packet's diff notes (removing 'partial'/'incomplete' from SEG, or removing
 * the `_exhaustive` line, both turned `tsc` red before being restored).
 *
 * THIS FILE is the RUNTIME counterpart §N.8 also requires: `tsc` exhaustiveness
 * proves the TYPE covers every state; this test proves the actual rendered
 * output for each state is a REAL, distinct mapping — not the 'dormant' fallback
 * — by asserting against ALL_ASSET_STATES (the same runtime array AssetState is
 * derived FROM, so this test cannot itself drift from the type).
 */
describe('AssetProgressBar — SEG exhaustiveness (Packet B2, C-3)', () => {
  it('every AssetState member has its OWN SEG entry — never silently sharing dormant\'s', () => {
    for (const s of ALL_ASSET_STATES) {
      expect(s in SEG, `AssetState '${s}' has no SEG entry — it will render 'dormant' styling`).toBe(true)
    }
  })

  it('partial and incomplete are mapped to a REAL, non-dormant entry (the two states this fix closes)', () => {
    expect(SEG.partial).not.toBe(SEG.dormant)
    expect(SEG.incomplete).not.toBe(SEG.dormant)
    // Grouped with 'stale' per LiveDependencyGraph.tsx's own convention
    // (unfinished/resumable, never a genuine error, never lit) — same colours.
    expect(SEG.partial).toEqual(SEG.stale)
    expect(SEG.incomplete).toEqual(SEG.stale)
  })

  it('a "partial" asset actually renders SEG.stale\'s colour family, not SEG.dormant\'s, in a real render', () => {
    // jsdom normalizes inline rgba() strings (spacing) when read back via
    // `.style.background`, so compare the numeric channels rather than the raw
    // literal — the same technique the pre-existing blocked-rendering test uses
    // (AssetRow_blocked.test.tsx: `.toContain('236, 197, 106')`).
    const rgbaNums = (s: string) => (s.match(/[\d.]+/g) ?? []).join(',')
    const dormantEmpty = rgbaNums(SEG.dormant.emptyBg)
    const staleEmpty = rgbaNums(SEG.stale.emptyBg)
    expect(staleEmpty).not.toBe(dormantEmpty) // sanity: the two fixtures actually differ

    const { container } = render(
      <AssetProgressBar state="partial" actualRows={10} />
    )
    const segEls = Array.from(container.querySelectorAll('div[style]')) as HTMLElement[]
    const backgrounds = segEls.map(el => rgbaNums(el.style.background))
    expect(backgrounds).toContain(staleEmpty)
    expect(backgrounds).not.toContain(dormantEmpty)
  })

  it('no console.warn fires for a KNOWN AssetState (only genuinely unmapped input should warn)', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    for (const s of ALL_ASSET_STATES) {
      render(<AssetProgressBar state={s} actualRows={0} />)
    }
    expect(warnSpy).not.toHaveBeenCalled()
    warnSpy.mockRestore()
  })
})
