'use client'

/**
 * CapabilityHint — A-S8 (UI Capability-Availability Surface)
 *
 * Wrapper component that:
 *   - Passes through `children` when the active stack's manifest declares
 *     support for `capability`.
 *   - Renders a small "Switch to <stacks>" pill when the manifest declares
 *     null / false for that capability.
 *
 * Feature wiring happens in later phases (R11.B / R11.F / R11.I). During R11.A,
 * this component establishes the pattern. Feature buttons will wrap their
 * affordances like:
 *
 *   <CapabilityHint capability="webSearch" activeStack={stack}>
 *     <WebSearchButton />
 *   </CapabilityHint>
 *
 * Flagless per §M.16 — additive, no feature wiring yet.
 *
 * Style: .capability-hint-chip in globals.css (Marsys gold-hairline border,
 * muted text, small padding, scoped to .consume-shell).
 */

import type { ProviderCapabilities } from '@/lib/providers/capabilities';
import type { StackId } from '@/lib/providers/dispatcher';
import { useProviderManifest } from '@/lib/chat-v2/useProviderManifest';
import { formatSupportingStackNames } from '@/lib/providers/manifest-helpers';

export interface CapabilityHintProps {
  /** The capability key to check on the active stack's manifest. */
  capability: keyof ProviderCapabilities;
  /** The stack ID currently active in the chat session. */
  activeStack: StackId;
  /** The feature button or affordance to render when the capability is supported. */
  children: React.ReactNode;
}

/**
 * Renders `children` when `activeStack` supports `capability`; renders a
 * chip with switch-stack copy otherwise.
 */
export function CapabilityHint({ capability, activeStack, children }: CapabilityHintProps) {
  const manifest = useProviderManifest(activeStack);
  const supported = manifest[capability] !== null && manifest[capability] !== false;

  if (supported) {
    return <>{children}</>;
  }

  const copy = formatSupportingStackNames(capability);
  const label =
    copy.length > 0
      ? `Switch to ${copy} to use this`
      : 'Not available on any stack';

  return (
    <div
      className="capability-hint-chip"
      role="status"
      aria-label={label}
      data-testid="capability-hint-chip"
      data-capability={capability}
      data-stack={activeStack}
    >
      <span>{label}</span>
    </div>
  );
}
