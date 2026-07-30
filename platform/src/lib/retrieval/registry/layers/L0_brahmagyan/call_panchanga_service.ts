/**
 * call_panchanga_service — date-parameterized panchanga compute service (chart_panchanga_cache)
 * ======================================================================================================
 * W2b Batch 3 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `chart_panchanga_cache`, migration 081_l0fr_schema.sql). Distinct from the already-served
 * natal-only `chart_panchanga` table (query_panchanga.ts) — this concept is a
 * date-parameterized (any date, any location) panchanga lookup, the same "dark service"
 * shape already named for `ka_graha_sancara`/`ka_muhurta_seva` (GT-50) and wired in the
 * prior W2-phase-1 pass via `call_service_wrappers.ts`'s fetch()/error-shape pattern.
 *
 * B.10 / honest-investigation note (this pass's own finding, not carried over from the
 * disposition doc): `chart_panchanga_cache` itself has ZERO writer anywhere in this repo
 * (confirmed by an exhaustive grep — no INSERT, no reference outside its own DDL) and the
 * backing `panchang.py` router's own docstring says its per-chart cache design was
 * superseded: "no SQL cache this session... 4C-2 will add panchang_daily cache below the
 * endpoint" — i.e. the actually-built cache is the DIFFERENT, GLOBAL `panchanga_daily`
 * table (already served via query_muhurat.ts/muhurta_finder.ts/phala_outlook.ts), not
 * this chart-scoped one. Wiring a capability against the literal `chart_panchanga_cache`
 * table would therefore always return nothing, forever — the honest disposition here
 * follows the task brief's own instruction ("fold into the same dark-SERVICE wiring
 * pattern... just needs a TS capability + wiring") and wires the REAL underlying compute
 * service (`panchang.py`'s `/api/compute/panchanga` + `/api/compute/panchanga/range`
 * endpoints — engine-direct, Swiss-Ephemeris-backed, not the dead table) rather than a
 * capability that queries a table with no writer. This is the same "compute service, not
 * a table" shape already established for `ka_graha_sancara` (asset_registry
 * target_table = null) in `DESIGN_KA_GRAHA_SANCARA_WIRING.md`.
 *
 * HARD CONSTRAINT COMPLIANCE: this file is deliberately placed in L0_brahmagyan, NOT
 * L3_kala — the campaign's hard constraint forbids touching kala_*-prefixed files or
 * Gochara/D-5-related serving semantics. `call_service_wrappers.ts` (L3_kala) was read
 * ONLY to copy its fetch()/error-shape pattern; it was never edited by this pass. Panchanga
 * (tithi/vara/nakshatra/yoga/karana) is a distinct classical-calendar concept from
 * Gochara (transit) — this capability calls a different sidecar router (`panchang.py`,
 * not `ephemeris.py`/gochara routes) and registers a brand-new URI/name never referenced
 * by any kala_* or gochara file. (Note: a literal "kala_* / gochara" adjacency here would
 * prematurely close this block comment — asterisk-then-slash — a known campaign trap;
 * kept split across two words for that reason.)
 *
 * Global scope by default (any date/location); chart_id is optional and, when provided,
 * hydrates a native_context overlay (birth nakshatra + Moon sign for Tara Bala / Chandra
 * Bala) — same optional-enrichment shape the sidecar route itself already supports.
 */
import type { CapabilityDescriptor } from '../../types'

// Bhubaneswar (project canonical default location per panchang.py's own _fetch_native_context
// fallback) — used only when lat/lon are omitted, so single-date lookups don't require
// callers to always supply coordinates.
const DEFAULT_LAT = 20.27
const DEFAULT_LON = 85.84
const DEFAULT_TZ_OFFSET_MINUTES = 330 // IST

export const callPanchangaServiceCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/call_panchanga_service',
  type:  'tool',
  layer: 'L0',
  name:  'call_panchanga_service',

  description: [
    'Compute panchanga (tithi/vara/nakshatra/yoga/karana + sunrise/sunset) for an',
    'arbitrary date and location (panchang.py compute service, Swiss-Ephemeris-backed,',
    'engine-direct — not a table lookup). mode=single (default): one date, returns full',
    'panchang + optional native_context if chart_id is provided. mode=range: date_from..',
    'date_to (max 31 days inclusive), returns one entry per day. Defaults to Bhubaneswar/',
    'IST coordinates when lat/lon/tz_offset_minutes are omitted. Distinct from the natal-',
    'only chart_panchanga (query_panchanga) — this is date-parameterized, any date.',
  ].join(' '),

  input_schema: {
    mode:              { type: 'string', description: 'single (default) or range.', enum: ['single', 'range'] },
    date:              { type: 'string', description: 'mode=single: ISO date (YYYY-MM-DD). Required for mode=single.' },
    date_from:         { type: 'string', description: 'mode=range: start ISO date. Required for mode=range.' },
    date_to:           { type: 'string', description: 'mode=range: end ISO date, inclusive, max 31 days from date_from. Required for mode=range.' },
    lat:               { type: 'number', description: `Latitude, -90..90. Default ${DEFAULT_LAT} (Bhubaneswar).` },
    lon:               { type: 'number', description: `Longitude, -180..180. Default ${DEFAULT_LON} (Bhubaneswar).` },
    tz_offset_minutes: { type: 'number', description: `Timezone offset in minutes, -720..840. Default ${DEFAULT_TZ_OFFSET_MINUTES} (IST).` },
    chart_id:          { type: 'string', description: 'mode=single only: optional chart UUID to hydrate a native_context overlay (birth nakshatra + Moon sign).' },
  },

  required_inputs: [],
  scope: 'global',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'temporal',
  emits_references: false,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'medium', cacheable: true },
    bulk_context: { pre_fetch_priority: 20, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const mode = args['mode'] ? String(args['mode']) : 'single'
    const lat = args['lat'] != null ? Number(args['lat']) : DEFAULT_LAT
    const lon = args['lon'] != null ? Number(args['lon']) : DEFAULT_LON
    const tz_offset_minutes = args['tz_offset_minutes'] != null ? Number(args['tz_offset_minutes']) : DEFAULT_TZ_OFFSET_MINUTES

    const sidecarUrl = process.env.PYTHON_SIDECAR_URL
    const sidecarKey = process.env.PYTHON_SIDECAR_API_KEY ?? ''

    if (!sidecarUrl) {
      return { content: { error: 'PYTHON_SIDECAR_URL not configured — panchanga service unavailable' }, is_error: true }
    }

    try {
      if (mode === 'single') {
        const date = args['date'] ? String(args['date']) : ''
        if (!date) return { content: { error: 'date is required for mode=single' }, is_error: true }
        const chart_id = args['chart_id'] ? String(args['chart_id']) : undefined

        const resp = await fetch(`${sidecarUrl}/api/compute/panchanga`, {
          method:  'POST',
          headers: { 'Content-Type': 'application/json', 'x-api-key': sidecarKey },
          body:    JSON.stringify({ date, lat, lon, tz_offset_minutes, chart_id }),
        })
        if (!resp.ok) {
          const err = await resp.json().catch(() => ({}))
          return { content: { error: `Sidecar ${resp.status}`, detail: err }, is_error: true }
        }
        const data = await resp.json() as {
          ok: boolean; panchang: unknown; native_context: unknown
          native_context_error?: string | null; cache_hit: boolean
        }
        return {
          content: {
            mode, date, lat, lon, tz_offset_minutes,
            panchang: data.panchang,
            native_context: data.native_context,
            // ṢAḌ-DARŚANA W1 verify-reopen: the sidecar now fails the OPTIONAL native_context
            // overlay soft and names the reason instead of 500-ing the whole panchāṅga payload
            // (routers/panchang.py compute_panchanga_endpoint). Passed through verbatim so a
            // consumer can disclose the SPECIFIC gap ("birth-chart overlay unavailable: …")
            // rather than mislabelling it as service unreachability (CLAUDE.md §N.8).
            native_context_error: data.native_context_error ?? null,
            provenance: { source: 'panchang.py /api/compute/panchanga (Swiss-Ephemeris, engine-direct)' },
          },
          is_error: false,
        }
      }

      if (mode === 'range') {
        const date_from = args['date_from'] ? String(args['date_from']) : ''
        const date_to   = args['date_to'] ? String(args['date_to']) : ''
        if (!date_from || !date_to) return { content: { error: 'date_from and date_to are required for mode=range' }, is_error: true }

        const resp = await fetch(`${sidecarUrl}/api/compute/panchanga/range`, {
          method:  'POST',
          headers: { 'Content-Type': 'application/json', 'x-api-key': sidecarKey },
          body:    JSON.stringify({ date_from, date_to, lat, lon, tz_offset_minutes }),
        })
        if (!resp.ok) {
          const err = await resp.json().catch(() => ({}))
          return { content: { error: `Sidecar ${resp.status}`, detail: err }, is_error: true }
        }
        const data = await resp.json() as { ok: boolean; panchangs: unknown[]; count: number }
        return {
          content: {
            mode, date_from, date_to, lat, lon, tz_offset_minutes,
            panchangs: data.panchangs,
            count:     data.count,
            provenance: { source: 'panchang.py /api/compute/panchanga/range (Swiss-Ephemeris, engine-direct)' },
          },
          is_error: false,
        }
      }

      return { content: { error: `Unknown mode: ${mode}` }, is_error: true }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
