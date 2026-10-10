/**
 * kp_frame_parity.test.ts — platform / platform-mcp KP frame constants PARITY (SS N-342 item 3).
 *
 * platform/src/lib/retrieval/kp_frame.ts and platform-mcp/src/lib/kp_frame.ts are written twice
 * (separate packages, no cross-import). This test imports both (test-only) and asserts they agree,
 * and that the KP frame is Krishnamurti, never the Lahiri primary.
 */
import { describe, it, expect } from 'vitest'
import * as platform from '../../kp_frame'
import * as mcp from '../../../../../../platform-mcp/src/lib/kp_frame'
import { PRIMARY_AYANAMSHA, STORED_AYANAMSHA_IDS } from '../../chart_facts_helpers'

describe('KP frame constants', () => {
  it('are identical on both sides', () => {
    expect(mcp.KP_FRAME_AYANAMSHA).toBe(platform.KP_FRAME_AYANAMSHA)
    expect(mcp.KP_FRAME_LABEL).toBe(platform.KP_FRAME_LABEL)
    for (const id of [undefined, null, '', 'krishnamurti', 'lahiri_chitrapaksha', 'raman', 'true_chitra']) {
      expect(mcp.kpFrameLabelFor(id)).toBe(platform.kpFrameLabelFor(id))
    }
  })

  it('the KP frame is the Krishnamurti ayanamsha, a stored id, and not the Lahiri primary', () => {
    expect(platform.KP_FRAME_AYANAMSHA).toBe('krishnamurti')
    expect(STORED_AYANAMSHA_IDS).toContain(platform.KP_FRAME_AYANAMSHA)
    expect(platform.KP_FRAME_AYANAMSHA).not.toBe(PRIMARY_AYANAMSHA)
    expect(platform.KP_FRAME_LABEL).toBe('KP frame (Krishnamurti ayanamsha)')
  })
})
