import { describe, it, expect } from 'vitest'
import { stateColor } from '../ArmillaryGraph'

/**
 * Packet B2 — C-4, surface 3/3 (review B1_rereview2_20260926T193112Z.md, "BLOCKS
 * B2"): "ArmillaryGraph's stateColor — not previously named by anyone. A
 * 'blocked' asset's hover dot gets the neutral grey '#7C725B' rather than amber.
 * The tooltip text reads 'blocked' correctly, and it never reads as a failure,
 * so this is cosmetic — but it is a fourth instance of the same unmapped-default
 * shape and belongs in the record."
 *
 * `stateColor` was a closure-local const inside the ArmillaryGraph component
 * (untestable in isolation); this fix moves it to module scope — mirroring how
 * `aggregate()` was already extracted for the same reason — with no behavior
 * change beyond adding the missing branches.
 */
describe('ArmillaryGraph — stateColor (Packet B2, C-4)', () => {
  it('a blocked asset gets amber, never the neutral grey (the defect this fix closes)', () => {
    expect(stateColor('blocked')).toBe('#EC9332')
    expect(stateColor('blocked')).not.toBe('#7C725B')
  })

  it('blocked is distinct from both a genuine error (red) and dormant/idle (grey)', () => {
    expect(stateColor('blocked')).not.toBe(stateColor('error'))
    expect(stateColor('blocked')).not.toBe(stateColor('dormant'))
  })

  it('partial and incomplete join stale\'s amber family, not the grey default', () => {
    expect(stateColor('partial')).toBe(stateColor('stale'))
    expect(stateColor('incomplete')).toBe(stateColor('stale'))
    expect(stateColor('partial')).not.toBe('#7C725B')
    expect(stateColor('incomplete')).not.toBe('#7C725B')
  })

  it('pre-existing mappings are unchanged (no regression from the extraction)', () => {
    expect(stateColor('lit')).toBe('#8FD49B')
    expect(stateColor('service_ok')).toBe('#8FD49B')
    expect(stateColor('building')).toBe('#E8C878')
    expect(stateColor('stale')).toBe('#D2A23C')
    expect(stateColor('error')).toBe('#B5474C')
    expect(stateColor('service_down')).toBe('#B5474C')
    expect(stateColor('dormant')).toBe('#7C725B')
    expect(stateColor('not_migrated')).toBe('#7C725B')
  })
})
