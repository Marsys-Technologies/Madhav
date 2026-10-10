import {
  AYANAMSHA_EDIT_POLICIES,
  DEFAULT_AYANAMSHA_EDIT_POLICY,
  type AyanamshaEditPolicy,
} from '@/lib/charts/ayanamshaEditGuard'

/**
 * Ayanamsha edit policy switch (SS N-319), server side.
 *
 * ONE environment variable, `CHART_AYANAMSHA_EDIT_POLICY`, chooses what a
 * request that changes the ayanamsha SET of an EXISTING chart may do:
 *
 *   block_all  (DEFAULT) refuse the request as a whole with
 *              `AYANAMSHA_EDIT_BLOCKED` (403); the edit form shows the
 *              ayanamsha selection read-only.
 *   warn       refuse with `AYANAMSHA_EDIT_NEEDS_CONFIRMATION` (409) unless the
 *              request carries `confirm_destructive: true`; the edit form shows
 *              a strong confirm dialog and sends the flag. With the flag, the
 *              full destructive recompute runs.
 *   off        today's behaviour exactly (any ayanamsha edit recomputes).
 *
 * Unset or empty means `block_all`. Surrounding whitespace and case are
 * ignored. An unknown value falls back to `block_all` and is logged, so a typo
 * can only ever make the guard stricter, never weaker. To change the policy set
 * the variable and restart the server, e.g. `CHART_AYANAMSHA_EDIT_POLICY=warn`.
 *
 * Creation of charts and edits of every other field (name, birth data, house
 * system, ...) are not governed by this switch.
 */

export const AYANAMSHA_EDIT_POLICY_ENV = 'CHART_AYANAMSHA_EDIT_POLICY'

export function parseAyanamshaEditPolicy(
  raw: string | undefined | null,
  onInvalid?: (raw: string) => void,
): AyanamshaEditPolicy {
  const value = (raw ?? '').trim().toLowerCase()
  if (value === '') return DEFAULT_AYANAMSHA_EDIT_POLICY
  if ((AYANAMSHA_EDIT_POLICIES as readonly string[]).includes(value)) return value as AyanamshaEditPolicy
  onInvalid?.(String(raw))
  return DEFAULT_AYANAMSHA_EDIT_POLICY
}

export function getAyanamshaEditPolicy(env: NodeJS.ProcessEnv = process.env): AyanamshaEditPolicy {
  return parseAyanamshaEditPolicy(env[AYANAMSHA_EDIT_POLICY_ENV], (raw) => {
    console.error(
      `[charts/ayanamsha-edit-policy] ${AYANAMSHA_EDIT_POLICY_ENV}=${JSON.stringify(raw)} is not one of ` +
        `${AYANAMSHA_EDIT_POLICIES.join('|')}; using ${DEFAULT_AYANAMSHA_EDIT_POLICY}`,
    )
  })
}
