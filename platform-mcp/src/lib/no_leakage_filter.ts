/**
 * NO-LEAKAGE arm-2 capability filter (doctrine ruling F-R7, ACCEPTED).
 *
 * Any capability descriptor flagged `calibration_context_only: true` must be
 * excluded from every projection and from the `prashna_ask` tool set. The
 * authoritative `calibration_context_only` field lives on `CapabilityDescriptor`
 * in `platform/src/lib/retrieval/registry/types.ts` (the `platform` deployable).
 *
 * `platform-mcp` is a separate Cloud Run deployable with no shared import path
 * to `platform` (confirmed in a sibling task), so this file declares a minimal
 * local structural type carrying only the fields this filter needs, rather
 * than importing the real type across the process boundary.
 */

/** Minimal local mirror of the leakage-relevant shape of `CapabilityDescriptor`. */
export interface LeakageCheckedCapability {
  id: string;
  calibration_context_only?: boolean;
}

/**
 * Returns a new array containing only capabilities that are safe to expose —
 * i.e. every entry except those explicitly flagged `calibration_context_only: true`.
 * Entries where the flag is absent or `false` are kept. Pure function: does not
 * mutate the input array or its elements.
 */
export function filterLeakedCapabilities<T extends LeakageCheckedCapability>(
  capabilities: readonly T[],
): T[] {
  return capabilities.filter((capability) => capability.calibration_context_only !== true);
}
