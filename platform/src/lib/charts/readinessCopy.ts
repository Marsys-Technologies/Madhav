/**
 * User-facing refusal copy for readiness-gated derived capabilities when the
 * shared chart readiness is not Ready. Paripraśna is adaptive and uses a
 * non-blocking completeness notice instead. Pure — no server-only imports — so
 * callers and their tests share one wording per state.
 */
export function readinessRefusalMessage(state: string | undefined): string {
  switch (state) {
    case 'building':
      return 'This chart is being recomputed. New readings will be available when it is ready.'
    case 'needs-rebuild':
      return 'This chart’s details changed and it needs to be rebuilt in Nirmāṇa before new readings can start.'
    case 'failed':
      return 'The latest build of this chart failed. New readings will be available once it is rebuilt.'
    case 'unavailable':
      return 'This chart’s readiness could not be confirmed. Please try again shortly.'
    default:
      return 'New readings open once this chart has been fully computed.'
  }
}
