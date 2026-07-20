/**
 * retrieval/registry/layers/L0_brahmagyan/index.ts
 *
 * Registers all L0 Brahmagyan capabilities with the central registry.
 * Call registerL0Capabilities() at app startup (or import this module).
 *
 * L0FR Stream A — 5 foundation capabilities (resolve_entity, list_entities, asset_registry_all/l0, intent_classify)
 * L0FR Stream B — 6 ephemeris capabilities (planet_position, planet_transit, aspects_at_time, retrograde_periods, ephemeris_cache_year/native-lifetime)
 * Wave 3 R2 — 4 corpus query tools (yoga/dosha/remedy/classical texts)
 */
import { registerCapability } from '../../index'
import type { CapabilityDescriptor } from '../../types'

import { assetRegistryL0Capability }  from './asset_registry_l0'
import { assetRegistryAllCapability } from './asset_registry_all'
import { listEntitiesCapability }     from './list_entities'
import { resolveEntityCapability }    from './resolve_entity'
import { intentClassifyCapability }   from './intent_classify'
import { queryYogaCatalogCapability } from './query_yoga_catalog'
import { queryDoshaCatalogCapability} from './query_dosha_catalog'
import { queryRemedyCorpusCapability} from './query_remedy_corpus'
import { queryClassicalTextsCapability } from './query_classical_texts'
// Stream B: ephemeris capabilities
import { queryPlanetPositionCapability } from './query_planet_position'
import { queryPlanetTransitCapability } from './query_planet_transit'
import { queryAspectsAtTimeCapability } from './query_aspects_at_time'
import { queryRetrogradePeriodsCapability } from './query_retrograde_periods'
import { ephemerisCacheYearCapability } from './ephemeris_cache_year'
import { ephemerisCacheNativeLifetimeCapability } from './ephemeris_cache_native_lifetime'
// W4-loop-1 (E-6): rāśi→medical reference (bg_sign_medical)
import { querySignMedicalCapability } from './query_sign_medical'
// W2 dark-set wiring: naisargika friendship + combustion-orb reference tables
// (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set, same migration file as the
// already-served-elsewhere bg_dignity_reference)
import { queryGrahaNaisargikaFriendshipCapability } from './query_graha_naisargika_friendship'
import { queryCombustionOrbsCapability } from './query_combustion_orbs'

export const L0_CAPABILITIES = [
  // Stream A: foundation + ontology
  resolveEntityCapability,
  listEntitiesCapability,
  assetRegistryAllCapability,
  assetRegistryL0Capability,
  intentClassifyCapability,
  // Wave 3 R2: corpus query tools
  queryYogaCatalogCapability,
  queryDoshaCatalogCapability,
  queryRemedyCorpusCapability,
  queryClassicalTextsCapability,
  // Stream B: ephemeris (1900-2150, 9 bodies, pyswisseph DE441)
  queryPlanetPositionCapability,
  queryPlanetTransitCapability,
  queryAspectsAtTimeCapability,
  queryRetrogradePeriodsCapability,
  ephemerisCacheYearCapability,
  ephemerisCacheNativeLifetimeCapability,
  // W4-loop-1 (E-6): rāśi→medical reference
  querySignMedicalCapability,
  // W2 dark-set wiring: naisargika friendship + combustion-orb reference
  queryGrahaNaisargikaFriendshipCapability,
  queryCombustionOrbsCapability,
] as const

export function registerL0Capabilities(): void {
  for (const cap of L0_CAPABILITIES) {
    try {
      registerCapability(cap as unknown as CapabilityDescriptor)
    } catch (e) {
      // Ignore duplicate registration (idempotent)
      if (e instanceof Error && e.message.includes('Duplicate URI')) {
        // already registered — safe to skip
      } else {
        throw e
      }
    }
  }
}

// Auto-register on import (safe — registry/index.ts does NOT import this file)
registerL0Capabilities()

export {
  resolveEntityCapability,
  listEntitiesCapability,
  assetRegistryAllCapability,
  assetRegistryL0Capability,
  intentClassifyCapability,
  queryYogaCatalogCapability,
  queryDoshaCatalogCapability,
  queryRemedyCorpusCapability,
  queryClassicalTextsCapability,
  queryPlanetPositionCapability,
  queryPlanetTransitCapability,
  queryAspectsAtTimeCapability,
  queryRetrogradePeriodsCapability,
  ephemerisCacheYearCapability,
  ephemerisCacheNativeLifetimeCapability,
  querySignMedicalCapability,
  queryGrahaNaisargikaFriendshipCapability,
  queryCombustionOrbsCapability,
}
