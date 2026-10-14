/** K7-3: exact-instant, published-stage disclosure beside the legacy NOW answer.
 * This is transport/identity validation only. State, roots, release, context,
 * coverage are carried from now_read. No empty page
 * becomes evaluated_silent, and no density is inferred from roles or roots.
 * Stored tier carriage is checked independently at this public boundary.
 */
import { isVerifiedPassStatus, VERIFICATION_PASS_STATUS_VOCAB } from '../../generated/envelope.js'

type Data = Record<string, unknown>
const object = (value: unknown): Data | null =>
  value !== null && typeof value === 'object' && !Array.isArray(value) ? value as Data : null

export interface PublishedNowDisclosure {
  at: string
  capability: 'marsys://tool/L3/now_read'
  status: 'published' | 'information_unavailable'
  empty_reason: string | null
  snapshot: Data | null
}

export function validPublishedNowInstant(at: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(at)) return false
  const millis = Date.parse(at)
  if (!Number.isFinite(millis)) return false
  // Date.parse rolls February 30 into March. Validate the supplied calendar
  // components independently of its UTC offset; never turn a date into an instant.
  const day = at.slice(0, 10)
  return new Date(`${day}T00:00:00Z`).toISOString().slice(0, 10) === day
}

export function publishedNowDisclosure(
  chart_id: string,
  at: string,
  response: { ok: boolean; content: Data | null },
): PublishedNowDisclosure {
  const unavailable = (empty_reason: string): PublishedNowDisclosure => ({ at,
    capability: 'marsys://tool/L3/now_read', status: 'information_unavailable', empty_reason, snapshot: null })
  if (!response.ok) return unavailable('query_failed')
  const source = response.content
  const manifest = object(source?.manifest)
  if (source?.empty_reason === 'unpublished') return unavailable('unpublished')
  if (!source || source.view !== 'now' || source.chart_id !== chart_id || !manifest
    || typeof source.manifest_id !== 'string' || !source.manifest_id
    || typeof source.generation !== 'string' || !source.generation
    || manifest.manifest_id !== source.manifest_id || manifest.generation !== source.generation
    || !Array.isArray(source.rows)
    || (source.rows.length > 0 ? source.empty_reason !== null : source.empty_reason !== 'no_matching_rows')) {
    return unavailable('invalid_published_snapshot')
  }
  const columns = object(source.density_contract)?.stored_tier_columns
  const bound = Array.isArray(columns) && columns.includes('kala_darshana.verification_pass_status')
    && columns.includes('kala_obstruction.verification_pass_status')
  // Partial explicit contracts are still accepted per row: never transfer proof
  // across a sibling source. Old snapshots lacking bindings keep null density.
  const hasBindings = bound || (Array.isArray(columns) && columns.length > 0)
  const counts = { scope: 'page', confirmed: 0, testimony: 0, catalog_only: 0, unknown: 0, context_only: 0 }
  const rows = source.rows.map(value => {
    const row = object(value) ?? {}
    const data = object(row.data)
    const proof = object(row.verification)
    const column = `${row.source_table}.verification_pass_status`
    const status = data?.verification_pass_status
    const admitted = ['kala_darshana','kala_obstruction'].includes(String(row.source_table))
    const valid = admitted && Array.isArray(columns) && columns.includes(column)
      && data?.generation === source.generation && row.qualification === 'published'
      && proof?.column === column && proof.status === status
      && proof.generation === source.generation && proof.manifest_id === source.manifest_id
      && VERIFICATION_PASS_STATUS_VOCAB.some(entry => entry.status === status)
    const density = valid ? (isVerifiedPassStatus(status) ? 'confirmed' : 'catalog_only') : null
    if (density === null) counts.unknown++
    else counts[density]++
    if (row.qualification === 'context_only') counts.context_only++
    return { ...row, density, density_reason: valid ? null : 'stored_tier_contract_unavailable' }
  })
  return { at, capability: 'marsys://tool/L3/now_read',
    status: source.rows.length ? 'published' : 'information_unavailable',
    empty_reason: source.empty_reason as string | null, snapshot: { ...source,
      density: hasBindings ? counts : null,
      density_reason: hasBindings ? null : 'stored_tier_contract_unavailable', rows,
      ...(hasBindings ? { catalog_only_rows_in_page: counts.catalog_only + counts.unknown } : {}),
    } }
}
