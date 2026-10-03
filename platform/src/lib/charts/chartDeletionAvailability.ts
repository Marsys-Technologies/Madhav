/**
 * Availability switch for `DELETE /api/charts/[id]`.
 *
 * Chart deletion is OFF until the full deletion-completeness program lands
 * (00_ARCHITECTURE/briefs/suvarna/layers/cross/CHART_DELETION_COMPLETENESS_DESIGN_v1_0.md).
 * Today the route cannot complete (its statements target a relation and a
 * column that do not exist, and NO ACTION / trigger-guarded keys would block
 * the final delete anyway), so a user who clicked delete could lose part of
 * their data. While this flag is false the route refuses up front after its
 * auth/ownership checks: no transaction, no DELETE.
 *
 * Kept in its own module (not exported from route.ts: a Next.js route file may
 * only export HTTP handlers and route-config names). The full program flips
 * this constant in the same change that replaces the route body.
 */
export const CHART_DELETION_ENABLED: boolean = false

export const CHART_DELETION_UNAVAILABLE_CODE = 'CHART_DELETION_UNAVAILABLE'

export const CHART_DELETION_UNAVAILABLE_MESSAGE =
  'Chart deletion is temporarily unavailable. Nothing was deleted.'
