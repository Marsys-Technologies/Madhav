/** K7-3: exact-instant, published-stage disclosure beside the legacy NOW answer.
 * This is transport/identity validation only. State, roots, release, context,
 * coverage are carried from now_read. No empty page
 * becomes evaluated_silent, and no density is inferred from roles or roots.
 * KYD-125: producer-stored tier columns and their detector proof remain due.
 */
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
  return { at, capability: 'marsys://tool/L3/now_read',
    status: source.rows.length ? 'published' : 'information_unavailable',
    empty_reason: source.empty_reason as string | null, snapshot: { ...source,
      // The dependency's reader still infers tiers from roles/roots. KYD-125
      // forbids exposing those as density proof through this new public path.
      // Do not substitute catalog_only either: the producer has not classified
      // the row. Raw stored data, provenance and context disclosure stay intact.
      density: null, density_reason: 'stored_tier_contract_unavailable',
      rows: source.rows.map(row => ({ ...object(row), density: null,
        density_reason: 'stored_tier_contract_unavailable' })),
    } }
}
