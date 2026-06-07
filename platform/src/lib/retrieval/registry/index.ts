/**
 * retrieval/registry/index.ts
 *
 * Central registry for all L0-L5 capabilities.
 * Provides: registerCapability, listCapabilities, getCapability(uri)
 *
 * L0FR Stream A — authored 2026-06-07
 */

import type { Capability } from './types'

// ── In-memory registry ────────────────────────────────────────────────────────

const _registry = new Map<string, Capability>()

/**
 * Register a capability. Throws if URI already registered (duplicate detection).
 */
export function registerCapability(capability: Capability): void {
  if (_registry.has(capability.uri)) {
    throw new Error(`[retrieval:registry] Duplicate URI: ${capability.uri}`)
  }
  _registry.set(capability.uri, capability)
}

/**
 * Return all registered capabilities, optionally filtered.
 */
export function listCapabilities(opts?: {
  layer?: string
  primitive_type?: 'tool' | 'resource' | 'prompt'
}): Capability[] {
  let caps = Array.from(_registry.values())
  if (opts?.layer) {
    caps = caps.filter(c => c.layer === opts.layer)
  }
  if (opts?.primitive_type) {
    caps = caps.filter(c => c.primitive_type === opts.primitive_type)
  }
  return caps
}

/**
 * Look up a capability by URI.
 * Returns undefined if not registered.
 */
export function getCapability(uri: string): Capability | undefined {
  return _registry.get(uri)
}

/**
 * Return a Map-style dump of all URIs (for parity_check).
 */
export function getRegistrySnapshot(): Map<string, Capability> {
  return new Map(_registry)
}

/**
 * Clear the registry (test-only).
 */
export function _clearRegistryForTests(): void {
  _registry.clear()
}

// ── Layer registration ────────────────────────────────────────────────────────
// Layer capabilities are registered by importing their respective index files
// at app startup. To avoid circular imports, this module does NOT auto-import
// the layer files. Instead, call registerAllLayers() or import each layer index
// explicitly in your app entry point.
//
// Example (app startup):
//   import '@/lib/retrieval/registry/layers/L0_brahmagyan/index'
//   (which calls registerCapability() for each L0 capability)
