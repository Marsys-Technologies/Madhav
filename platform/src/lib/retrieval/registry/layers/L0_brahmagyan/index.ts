/**
 * retrieval/registry/layers/L0_brahmagyan/index.ts
 *
 * Registers all L0 Brahmagyan capabilities with the central registry.
 * Call registerL0Capabilities() at app startup (or import this module).
 *
 * L0FR Stream A — authored 2026-06-07
 */

import { registerCapability } from '../../index'
import { resolveEntityCapability } from './resolve_entity'
import { listEntitiesCapability } from './list_entities'
import { assetRegistryAllCapability } from './asset_registry_all'
import { assetRegistryL0Capability } from './asset_registry_l0'
import { intentClassifyCapability } from './intent_classify'

export const L0_CAPABILITIES = [
  resolveEntityCapability,
  listEntitiesCapability,
  assetRegistryAllCapability,
  assetRegistryL0Capability,
  intentClassifyCapability,
] as const

export function registerL0Capabilities(): void {
  for (const cap of L0_CAPABILITIES) {
    try {
      registerCapability(cap)
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
}
