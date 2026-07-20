/**
 * Service manifest — sidecar/service router inventory (W1 Lane L1c)
 * =====================================================================
 * Consolidated, machine-readable declaration of every router the Python
 * compute sidecar (`amjis-sidecar`, `platform/python-sidecar/main.py`)
 * mounts, plus the five L3 Kala `call_*` logical-service wrappers
 * (`platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts`).
 *
 * Source of truth: `service_manifest.json` in this directory. Regenerate it
 * with the same method documented in its own `extraction_method` field
 * (hand-enumerate `app.include_router()` calls in main.py, cross-check
 * against a live `GET /openapi.json` snapshot — see `openapi_snapshot.json`
 * in this directory, fetched 2026-07-20 from the deployed service).
 *
 * v1 SCOPE NOTE: this manifest documents what exists; it does not (yet)
 * wire anything, gate anything, or enforce concurrency. See
 * `service_manifest.json`'s `sidecar_service.concurrency_note` for why
 * `concurrency_cap` fields are qualitative cost-class judgments, not
 * measured or enforced numbers. See `DESIGN_KA_GRAHA_SANCARA_WIRING.md`
 * for the GT-50 dark-service wiring proposal (design only — wiring is W2).
 */

import serviceManifestData from './service_manifest.json'

export interface ServiceManifestEndpoint {
  path: string
  method: string
}

export interface ServiceManifestRouter {
  module: string
  router_variable: string
  mount_prefix: string
  main_py_include_router_line: number
  conditional_mount: boolean
  summary: string
  provides_apis: ServiceManifestEndpoint[]
  endpoint_count: number
  health_probe: Record<string, unknown>
  concurrency_cap: {
    isolation: string
    cost_class: 'cheap' | 'medium' | 'expensive'
  }
}

export interface ServiceManifestLogicalL3Service {
  capability_name: string
  logical_service_id: string
  wired: boolean
  backing: string
  notes: string
}

export interface ServiceManifestDarkSetEntry {
  service_id: string
  ground_truth_ref: string
  priority: string
  stub_file: string
  stub_lines: string
  disposition: string
  design_note: string | null
}

export interface ServiceManifest {
  schema_version: string
  generated_at: string
  wave: string
  extraction_method: string
  validation: {
    openapi_total_paths: number
    manifest_computed_paths: number
    missing_from_openapi: string[]
    extra_in_openapi_not_in_manifest: string[]
    clean_match: boolean
  }
  sidecar_service: Record<string, unknown>
  routers: ServiceManifestRouter[]
  app_level_endpoints: Array<{ path: string; method: string; summary: string }>
  logical_l3_services: {
    source: string
    note: string
    services: ServiceManifestLogicalL3Service[]
  }
  dark_set: ServiceManifestDarkSetEntry[]
  orphaned_artifacts: Array<{ path: string; finding: string }>
}

export const serviceManifest = serviceManifestData as ServiceManifest

/** Total endpoint count across all mounted sidecar routers (excludes /health). */
export function getTotalRouterEndpointCount(): number {
  return serviceManifest.routers.reduce((sum, r) => sum + r.endpoint_count, 0)
}

/** Look up a router entry by its mount prefix (e.g. '/api/pyhora'). Ambiguous for
 * shared prefixes like '/api/compute' — use `module` for a unique lookup there. */
export function findRoutersByPrefix(prefix: string): ServiceManifestRouter[] {
  return serviceManifest.routers.filter(r => r.mount_prefix === prefix)
}

/** The dark (not-yet-wired) L3 Kala service ids, e.g. ['ka_graha_sancara', 'ka_muhurta_seva']. */
export function getDarkServiceIds(): string[] {
  return serviceManifest.dark_set.map(d => d.service_id)
}
