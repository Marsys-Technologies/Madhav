/**
 * L0FR Stream A — Retrieval Registry
 * ====================================
 * Central registry for all MARSYS capabilities.
 * No audience_tier. Universal access.
 *
 * Usage:
 *   import { registerCapability, listCapabilities, getCapability } from '@/lib/retrieval/registry'
 */

import type {
  CapabilityDescriptor,
  CapabilityUri,
  CapabilityFilter,
  Layer,
  CapabilityType,
} from './types'

// ── Registry store ────────────────────────────────────────────────────────────

const _registry = new Map<CapabilityUri, CapabilityDescriptor>()

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Register a capability in the central registry.
 * Idempotent: re-registering the same URI overwrites the prior entry.
 */
export function registerCapability(descriptor: CapabilityDescriptor): void {
  if (!descriptor.uri) {
    throw new Error('[registry] descriptor.uri is required')
  }
  // Resources use 'loader' instead of 'handler'; accept either.
  const callable = descriptor.handler ?? (descriptor as unknown as Record<string, unknown>)['loader']
  if (!callable || typeof callable !== 'function') {
    throw new Error(`[registry] capability ${descriptor.uri} has no handler function`)
  }
  _registry.set(descriptor.uri, descriptor)
}

/**
 * Get a single capability by URI.
 * Returns undefined if not registered.
 */
export function getCapability(uri: CapabilityUri): CapabilityDescriptor | undefined {
  return _registry.get(uri)
}

/**
 * List all registered capabilities, with optional filtering.
 */
export function listCapabilities(filter?: CapabilityFilter): CapabilityDescriptor[] {
  const all = Array.from(_registry.values())
  if (!filter) return all

  return all.filter((cap) => {
    if (filter.type && cap.type !== filter.type) return false
    if (filter.layer && cap.layer !== filter.layer) return false
    if (filter.name_prefix && !cap.name.startsWith(filter.name_prefix)) return false
    return true
  })
}

/**
 * Get all capability URIs for parity checking.
 */
export function listCapabilityUris(): CapabilityUri[] {
  return Array.from(_registry.keys())
}

/**
 * Check if a URI is registered.
 */
export function hasCapability(uri: CapabilityUri): boolean {
  return _registry.has(uri)
}

/**
 * Get capabilities by layer.
 */
export function getCapabilitiesByLayer(layer: Layer): CapabilityDescriptor[] {
  return listCapabilities({ layer })
}

/**
 * Get capabilities by type.
 */
export function getCapabilitiesByType(type: CapabilityType): CapabilityDescriptor[] {
  return listCapabilities({ type })
}

/**
 * Clear all registered capabilities (used in tests).
 */
export function clearRegistry(): void {
  _registry.clear()
}

/**
 * Get registry size.
 */
export function registrySize(): number {
  return _registry.size
}

// Re-export types for convenience
export type {
  CapabilityDescriptor,
  CapabilityUri,
  CapabilityFilter,
  CapabilityHandler,
  ToolResult,
  CapabilityContext,
  Layer,
  CapabilityType,
  LLMHints,
  AgenticHints,
  BulkContextHints,
  InputSchema,
  ParityCheckResult,
} from './types'
