/**
 * KP frame doctrine (SS N-342 item 3 / N-339): Krishnamurti Paddhati cusps, sub-lords and
 * significators are read in the KRISHNAMURTI ayanamsha, never in the Lahiri primary, and every
 * surface that serves them says so.
 *
 * MIRROR of `platform-mcp/src/lib/kp_frame.ts` (platform and platform-mcp are separate
 * packages: no cross-import, the constants are written twice). Parity is enforced by
 * `registry/__tests__/kp_frame_parity.test.ts`.
 */

/** The stored ayanamsha id of the KP frame. */
export const KP_FRAME_AYANAMSHA = 'krishnamurti'

/** The label every KP-frame surface carries. */
export const KP_FRAME_LABEL = 'KP frame (Krishnamurti ayanamsha)'
