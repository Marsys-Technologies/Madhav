/**
 * useProviderManifest — React hook returning the ProviderCapabilities manifest
 * for the given stack ID.
 *
 * Reads from the dispatcher's registry (pre-instantiated at module load).
 * Returns a stable reference — the manifest object does not change at runtime.
 *
 * Usage:
 *   const manifest = useProviderManifest('anthropic');
 *   if (manifest.webSearch) { ... }
 *
 * A-S8: UI availability surface.
 */

import { useMemo } from 'react';
import { getManifest } from '../providers/dispatcher';
import type { StackId } from '../providers/dispatcher';
import type { ProviderCapabilities } from '../providers/capabilities';

/**
 * Returns the ProviderCapabilities manifest for `stackId`.
 *
 * The return value is memo-ised by `stackId` so React does not re-render
 * consumers when the parent re-renders with the same stack.
 */
export function useProviderManifest(stackId: StackId): ProviderCapabilities {
  return useMemo(() => getManifest(stackId), [stackId]);
}
