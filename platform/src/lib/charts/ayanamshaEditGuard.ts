/**
 * Ayanamsha edit guard: policy vocabulary, machine-readable error codes, plain
 * messages and the pure decision (SS N-319). Client-safe (no env, no server
 * imports) so the edit form and the server share one wording and one decision.
 *
 * Why the guard exists: editing the `ayanamshas` field of an EXISTING chart is
 * classified as a computation change, so the PATCH runs the full destructive
 * path (archive every conversation, invalidate built assets, reset throughput,
 * persist and dispatch a global rebuild) while the field itself controls
 * nothing in the builders. The policy switch (see `ayanamshaEditPolicy.ts`)
 * decides what such a request is allowed to do. Chart creation is untouched;
 * only a changed ayanamsha SET on an existing chart is guarded.
 */

export const AYANAMSHA_EDIT_POLICIES = ['block_all', 'warn', 'off'] as const
export type AyanamshaEditPolicy = (typeof AYANAMSHA_EDIT_POLICIES)[number]
export const DEFAULT_AYANAMSHA_EDIT_POLICY: AyanamshaEditPolicy = 'block_all'

export const AYANAMSHA_EDIT_BLOCKED = 'AYANAMSHA_EDIT_BLOCKED'
export const AYANAMSHA_EDIT_NEEDS_CONFIRMATION = 'AYANAMSHA_EDIT_NEEDS_CONFIRMATION'
export type AyanamshaEditErrorCode = typeof AYANAMSHA_EDIT_BLOCKED | typeof AYANAMSHA_EDIT_NEEDS_CONFIRMATION

/** Request flag that acknowledges the destructive effect under the `warn` policy. */
export const CONFIRM_DESTRUCTIVE_FIELD = 'confirm_destructive'

export const AYANAMSHA_EDIT_BLOCKED_MESSAGE =
  "The ayanamsha of an existing chart can't be changed here. Contact support if it must change."

export const AYANAMSHA_EDIT_BLOCKED_WHOLE_REQUEST_MESSAGE =
  `${AYANAMSHA_EDIT_BLOCKED_MESSAGE} This request also changed other details; nothing was saved.`

export const AYANAMSHA_EDIT_CONFIRMATION_MESSAGE =
  'Changing the ayanamsha of an existing chart erases all built results for this chart and archives its conversations. ' +
  `This change requires confirmation: resend the request with ${CONFIRM_DESTRUCTIVE_FIELD}: true. Nothing was saved.`

export type AyanamshaEditVerdict =
  | { action: 'proceed' }
  | { action: 'refuse'; code: AyanamshaEditErrorCode; message: string }

/**
 * Pure decision. `ayanamshasChanged` is true only when the normalised ayanamsha
 * SET differs from the stored one; `otherFieldsChanged` only shapes the message
 * (a mixed request is refused as a whole, never partly applied).
 */
export function decideAyanamshaEdit(args: {
  policy: AyanamshaEditPolicy
  ayanamshasChanged: boolean
  otherFieldsChanged: boolean
  confirmDestructive: boolean
}): AyanamshaEditVerdict {
  const { policy, ayanamshasChanged, otherFieldsChanged, confirmDestructive } = args
  if (!ayanamshasChanged || policy === 'off') return { action: 'proceed' }
  if (policy === 'warn') {
    return confirmDestructive
      ? { action: 'proceed' }
      : { action: 'refuse', code: AYANAMSHA_EDIT_NEEDS_CONFIRMATION, message: AYANAMSHA_EDIT_CONFIRMATION_MESSAGE }
  }
  return {
    action: 'refuse',
    code: AYANAMSHA_EDIT_BLOCKED,
    message: otherFieldsChanged ? AYANAMSHA_EDIT_BLOCKED_WHOLE_REQUEST_MESSAGE : AYANAMSHA_EDIT_BLOCKED_MESSAGE,
  }
}
