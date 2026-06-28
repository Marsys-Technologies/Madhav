/**
 * D6 — Unified Capability Catalog
 * =================================
 * Imports all per-wave registration files and triggers capability registration
 * into the central registry. Also exports getCatalog() for callers that need
 * the complete registered set.
 *
 * GATE A (parallel coordination): this file is the ONLY place that imports
 * per-wave layer index files. Individual wave registration files (layers/L-x-/index.ts)
 * each call registerCapability() directly — they do NOT modify this file.
 * New waves register by adding their layer index import here.
 *
 * Both channels (MCP and chat) import getCatalog() to get the unified tool
 * surface — same registry, same handlers, drift impossible by construction.
 *
 * Usage:
 *   import { getCatalog } from '@/lib/retrieval/registry/catalog'
 *   const caps = getCatalog()  // triggers registration side-effects once
 *   const tool = getCapability('marsys://tool/L2/query_ucd')
 */

import type { CapabilityDescriptor } from './types'
import { getAllCapabilities } from './index'

// ── Per-wave registration imports ─────────────────────────────────────────────
// Each import executes the layer's index.ts which calls registerCapability() for
// each capability in that wave. Imports are idempotent (re-register overwrites).

// L0 Brahmagyan (15 capabilities: resolve_entity, list_entities, intent_classify,
// asset_registry_all, asset_registry_l0, query_classical_texts, query_yoga_catalog,
// query_dosha_catalog, query_remedy_corpus, query_planet_transit, query_planet_position,
// query_aspects_at_time, query_retrograde_periods, ephemeris_cache_year,
// ephemeris_cache_native_lifetime)
import './layers/L0_brahmagyan/index'

// L1 Gaṇita (19 capabilities: get_positions, get_strength, get_ashtakavarga,
// get_bhava_bala, get_aspects, get_yoga_dosha, get_argala, get_dispositors,
// get_sade_sati, get_panchanga, get_sensitive_points, get_karakas, get_dignity,
// get_avasthas, get_tajik, get_tara_chandra_bala, get_eclipse_flags, get_dashas,
// get_divisionals)
import './layers/L1_ganita/index'

// L2 Bodha (currently: query_ucd; drill/leaf/graph tools registered as D5 builds them)
import './layers/L2_bodha/index'

// L3 Kāla (placeholder — populated as D5 L3 tools land)
import './layers/L3_kala/index'

// L4 Phala (placeholder — populated as D5 L4 tools land)
import './layers/L4_phala/index'

// L5 Mīmāṃsā (query_insights, query_calibration — STUBBED-PENDING-DATA)
import './layers/L5_mimamsa/index'

// Router registration (D2)
import './layers/router_registration'

// ── getCatalog ────────────────────────────────────────────────────────────────

let _catalogLoaded = false

/**
 * Return the complete registered capability catalog.
 *
 * Triggers all per-wave registration side-effects on first call (idempotent).
 * Subsequent calls return the already-populated registry.
 *
 * Both MCP and chat channels call this to get the canonical tool surface.
 */
export function getCatalog(): CapabilityDescriptor[] {
  // Registration side-effects already fired via the imports above.
  // This function just returns the current state of the registry.
  _catalogLoaded = true
  return getAllCapabilities()
}

/**
 * Get a single capability by URI from the catalog.
 * Ensures catalog is loaded.
 */
export { getCapability, listCapabilities, listCapabilityUris } from './index'

// Mark catalog as loaded (for diagnostics)
export function isCatalogLoaded(): boolean {
  return _catalogLoaded
}
