/**
 * manifest-helpers.ts — Static utilities for querying capability availability
 * across all registered provider stacks.
 *
 * All computations are performed at module load from the 5 registered manifests.
 * UI surfaces (CapabilityHint, getSwitchStackHint) call these helpers; they do
 * not import the dispatcher directly.
 *
 * A-S8: UI availability surface.
 */

import type { ProviderCapabilities } from './capabilities';
import { getAllManifests, VALID_STACK_IDS, isCapabilityAvailable } from './dispatcher';
import type { StackId } from './dispatcher';

// Pre-compute all manifests at module load (cached for the session)
const ALL_MANIFESTS: Readonly<Record<StackId, ProviderCapabilities>> = getAllManifests();

/**
 * Returns an array of stack IDs that declare support for `capability`.
 * Order follows VALID_STACK_IDS order.
 */
export function getStacksSupporting(capability: keyof ProviderCapabilities): StackId[] {
  return VALID_STACK_IDS.filter(id => isCapabilityAvailable(capability, id));
}

/**
 * Returns a human-readable comma-or-series list of stacks that support
 * `capability`. Examples:
 *   ["anthropic"]             → "Anthropic"
 *   ["anthropic", "google"]   → "Anthropic or Google"
 *   ["a", "b", "c"]           → "Anthropic, Google, or OpenAI"
 *
 * Capitalises the first letter of each stack id for UI copy.
 */
export function formatSupportingStackNames(capability: keyof ProviderCapabilities): string {
  const stacks = getStacksSupporting(capability);
  if (stacks.length === 0) return '';
  const names = stacks.map(s => s.charAt(0).toUpperCase() + s.slice(1));
  if (names.length === 1) return names[0];
  if (names.length === 2) return `${names[0]} or ${names[1]}`;
  const last = names[names.length - 1];
  const rest = names.slice(0, -1).join(', ');
  return `${rest}, or ${last}`;
}

export { ALL_MANIFESTS };
