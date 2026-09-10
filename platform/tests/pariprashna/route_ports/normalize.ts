/**
 * P0-C / RF-1 — golden-record normalisation + comparison.
 *
 * "Semantic equality" is the bar RF-1 sets, so this module states EXACTLY what
 * is compared and what is deliberately excused, in code rather than in prose:
 *
 *   COMPARED (byte-for-byte after normalisation)
 *     · the ordered list of wire events, every field, including `seq`
 *     · the HTTP status and response headers
 *     · the ordered list of boundary side-effects (tool dispatch, canonical
 *       writeTurn parts, legacy history write, SAMĪKṢĀ capture, ring-buffer +
 *       stream-capture mirroring, title/pending-stream/ledger calls)
 *
 *   EXCUSED (replaced with a stable token, because they are wall-clock or
 *   host-dependent and cannot be equal across two runs of ANY code)
 *     · `t` on every event, `ms` on every event, `*_ms` fields anywhere
 *     · `latency_ms` / `elapsed` numerics inside recorded side-effect args
 *
 * Nothing else is excused. In particular `seq`, event ORDER, side-effect ORDER,
 * every id, and every text field are compared verbatim — a decomposition that
 * reordered emissions or renumbered blocks fails here.
 *
 * UUIDs are NOT normalised: the harness installs a deterministic
 * `crypto.randomUUID` counter, so the *order in which the route mints ids* is
 * itself part of the golden record. A refactor that moves a `randomUUID()` call
 * across another one changes the record and is caught.
 */

export const MS_TOKEN = '<ms>'

/** Field names whose value is wall-clock derived and therefore excused. */
const TIMING_KEYS = new Set(['t', 'ms', 'latency_ms', 'synthesisElapsedMs', 'planning_latency_ms', 'duration_ms'])

function isTimingKey(key: string): boolean {
  return TIMING_KEYS.has(key) || key.endsWith('_ms') || key.endsWith('ElapsedMs')
}

/** Recursively replace wall-clock numerics with a stable token. */
export function normalizeValue(value: unknown, key?: string): unknown {
  if (key !== undefined && isTimingKey(key) && typeof value === 'number') return MS_TOKEN
  if (Array.isArray(value)) return value.map((v) => normalizeValue(v))
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      out[k] = normalizeValue(v, k)
    }
    return out
  }
  // ISO timestamps that leak in via metadata.
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(value)) return '<iso>'
  return value
}

export interface GoldenRecord {
  scenario: string
  derived_from: string
  http: { status: number; headers: Record<string, string> }
  /** Wire events, normalised, in emission order. */
  events: unknown[]
  /** Boundary side-effects, normalised, in call order. */
  side_effects: unknown[]
}

export function normalizeRecord(rec: GoldenRecord): GoldenRecord {
  return {
    scenario: rec.scenario,
    derived_from: rec.derived_from,
    http: rec.http,
    events: normalizeValue(rec.events) as unknown[],
    side_effects: normalizeValue(rec.side_effects) as unknown[],
  }
}

export function serializeRecord(rec: GoldenRecord): string {
  return JSON.stringify(normalizeRecord(rec), null, 2) + '\n'
}

export interface RecordDiff {
  identical: boolean
  /** First diverging JSON path, or null when identical. */
  firstDivergence: string | null
  detail: string | null
}

/** Structural diff that names the FIRST diverging path — never a bare boolean. */
export function diffRecords(baseline: GoldenRecord, candidate: GoldenRecord): RecordDiff {
  const a = normalizeRecord(baseline)
  const b = normalizeRecord(candidate)
  const path = firstDiff(a as unknown, b as unknown, '$')
  if (path === null) return { identical: true, firstDivergence: null, detail: null }
  return {
    identical: false,
    firstDivergence: path.path,
    detail: `baseline=${trunc(path.a)} candidate=${trunc(path.b)}`,
  }
}

function trunc(v: unknown): string {
  const s = JSON.stringify(v)
  return s === undefined ? 'undefined' : s.length > 240 ? s.slice(0, 240) + '…' : s
}

function firstDiff(a: unknown, b: unknown, path: string): { path: string; a: unknown; b: unknown } | null {
  if (a === b) return null
  const aIsObj = a !== null && typeof a === 'object'
  const bIsObj = b !== null && typeof b === 'object'
  if (!aIsObj || !bIsObj) {
    return JSON.stringify(a) === JSON.stringify(b) ? null : { path, a, b }
  }
  if (Array.isArray(a) !== Array.isArray(b)) return { path, a, b }
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) {
      const n = Math.min(a.length, b.length)
      for (let i = 0; i < n; i++) {
        const d = firstDiff(a[i], b[i], `${path}[${i}]`)
        if (d) return d
      }
      return { path: `${path}.length`, a: a.length, b: b.length }
    }
    for (let i = 0; i < a.length; i++) {
      const d = firstDiff(a[i], b[i], `${path}[${i}]`)
      if (d) return d
    }
    return null
  }
  const ao = a as Record<string, unknown>
  const bo = b as Record<string, unknown>
  const keys = Array.from(new Set([...Object.keys(ao), ...Object.keys(bo)])).sort()
  for (const k of keys) {
    if (!(k in ao)) return { path: `${path}.${k}`, a: undefined, b: bo[k] }
    if (!(k in bo)) return { path: `${path}.${k}`, a: ao[k], b: undefined }
    const d = firstDiff(ao[k], bo[k], `${path}.${k}`)
    if (d) return d
  }
  return null
}
