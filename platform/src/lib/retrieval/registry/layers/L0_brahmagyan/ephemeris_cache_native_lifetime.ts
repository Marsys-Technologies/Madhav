/**
 * retrieval/registry/layers/L0_brahmagyan/ephemeris_cache_native_lifetime.ts
 *
 * Resource: marsys://resource/ephemeris-cache/native-lifetime
 * Pre-filtered ephemeris metadata for Abhisek Mohanty's lifetime period (1984-2070).
 * Provides coverage statistics and native chart context.
 *
 * L0FR Stream B — authored 2026-06-07
 */

import type { ResourceCapability } from '../../types'

const SIDECAR_URL = process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8001'

// Native: Abhisek Mohanty, 1984-02-05, Bhubaneswar
const NATIVE_LIFETIME_START = '1984-01-01'
const NATIVE_LIFETIME_END = '2070-12-31'

export const ephemerisCacheNativeLifetimeCapability: ResourceCapability = {
  uri: 'marsys://resource/ephemeris-cache/native-lifetime',
  primitive_type: 'resource',
  layer: 'L0',
  name: 'ephemeris_cache_native_lifetime',
  description:
    'Ephemeris coverage statistics for the native\'s lifetime (1984-2070). ' +
    'Provides: row count, date range, body count, and native birth chart context. ' +
    'Use as a prefetch sanity check before querying native-lifetime transits. ' +
    'Native: Abhisek Mohanty, born 1984-02-05 10:43 IST, Bhubaneswar, Odisha, India. ' +
    'Expected: ~157,266 rows (86 years × 365.25 days × 9 bodies).',
  mime_type: 'application/json',
  scope: 'global',
  archetype: 'orientation_digest',
  traversal_level: 'L-OVERVIEW',
  tool_role: 'umbrella',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      always_prefetch: true,  // prefetch at session open for native-lifetime queries
      latency_ms_p50: 30,
    },
    bulk_context: {
      pre_fetch_priority: 95,
      always_include: true,  // always include — metadata only, cheap
      result_size_kb_p50: 1,
    },
    result_max_kb: 4,
  },
  async loader(_ctx?: unknown) {
    try {
      const params = new URLSearchParams({
        start_date: NATIVE_LIFETIME_START,
        end_date: NATIVE_LIFETIME_END,
        count_only: 'true',
      })

      const res = await fetch(
        `${SIDECAR_URL}/brahmagyan/ephemeris/native_lifetime_meta?${params}`,
        { headers: { 'Content-Type': 'application/json' } }
      )
      if (!res.ok) {
        // Graceful fallback: return static metadata if sidecar not available
        return {
          ok: true,
          resource: 'marsys://resource/ephemeris-cache/native-lifetime',
          native: {
            name: 'Abhisek Mohanty',
            birth_date: '1984-02-05',
            birth_time_ist: '10:43:00',
            birth_location: 'Bhubaneswar, Odisha, India',
            lat: 20.2735,
            lon: 85.8334,
          },
          coverage: {
            start: NATIVE_LIFETIME_START,
            end: NATIVE_LIFETIME_END,
            expected_rows: 157266,
            status: 'sidecar_unavailable',
          },
        }
      }
      return res.json()
    } catch (_err) {
      // Static fallback
      return {
        ok: true,
        resource: 'marsys://resource/ephemeris-cache/native-lifetime',
        native: {
          name: 'Abhisek Mohanty',
          birth_date: '1984-02-05',
          birth_time_ist: '10:43:00',
          birth_location: 'Bhubaneswar, Odisha, India',
        },
        coverage: {
          start: NATIVE_LIFETIME_START,
          end: NATIVE_LIFETIME_END,
          note: 'sidecar not reachable; static metadata returned',
        },
      }
    }
  },
}
