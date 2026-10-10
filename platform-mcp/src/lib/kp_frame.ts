/**
 * KP frame doctrine (SS N-342 item 3 / N-339): Krishnamurti Paddhati cusps, sub-lords and
 * significators are read in the KRISHNAMURTI ayanamsha, never in the Lahiri primary, and every
 * surface that serves them says so.
 *
 * MIRROR of `platform/src/lib/retrieval/kp_frame.ts` (platform and platform-mcp are separate
 * packages: no cross-import, the constants are written twice). Parity is enforced by
 * `platform/src/lib/retrieval/registry/__tests__/kp_frame_parity.test.ts`.
 */

/** The stored ayanamsha id of the KP frame. */
export const KP_FRAME_AYANAMSHA = 'krishnamurti'

/** The label every KP-frame surface carries. */
export const KP_FRAME_LABEL = 'KP frame (Krishnamurti ayanamsha)'

/**
 * Label for a KP-frame payload read at `ayanamshaId`. Krishnamurti (or an unstated id, which the
 * KP handler defaults to Krishnamurti) -> the canonical label. Any other explicit id -> an honest
 * label naming the frame actually used, so a non-doctrinal KP read is never mistaken for the
 * canonical one.
 */
export function kpFrameLabelFor(ayanamshaId: string | null | undefined): string {
  if (ayanamshaId === undefined || ayanamshaId === null || ayanamshaId === '' || ayanamshaId === KP_FRAME_AYANAMSHA) {
    return KP_FRAME_LABEL
  }
  return `KP chain read at ${ayanamshaId} (explicit non-doctrinal frame; the ${KP_FRAME_LABEL} is the canonical one)`
}
