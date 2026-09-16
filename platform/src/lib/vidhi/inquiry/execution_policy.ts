import type {
  ExecutionChannel,
  SemanticCapabilityBinding,
} from '../../retrieval/registry/knowledge/types'

/**
 * The surface carrying an Inquiry Contract. A presentation transport is not a
 * capability exposure declaration: all inquiry actions are still dispatched
 * server-side after the normal principal, chart, lifecycle, argument, and
 * overlay checks have succeeded.
 */
export type InquiryPresentationTransport = 'portal' | 'managed_mcp' | 'raw_mcp'

/**
 * Legacy callers store an execution channel on the immutable contract. Keep
 * that receipt intact while deriving the presentation transport explicitly.
 */
export function presentationTransportForInquiry(
  executionChannel: ExecutionChannel,
  explicitTransport?: InquiryPresentationTransport,
): InquiryPresentationTransport {
  if (explicitTransport) return explicitTransport
  return executionChannel === 'platform_internal' ? 'portal' : 'raw_mcp'
}

const SERVER_DISPATCH_CHANNELS: Readonly<Record<InquiryPresentationTransport, readonly ExecutionChannel[]>> = {
  portal: ['platform_internal'],
  managed_mcp: ['platform_internal'],
  // Raw inquiry is authenticated and lifecycle-authorized before dispatch. It
  // may use an already-safe internal registry handler; this is not public MCP
  // registration. Existing reviewed public registry handlers remain usable.
  raw_mcp: ['platform_internal', 'mcp_full'],
}

/**
 * Whether a snapshot binding may be invoked by the server-side Inquiry
 * dispatcher for this presentation transport. This deliberately rejects MCP
 * aliases: their public spelling is not proof of a registry handler that the
 * inquiry dispatcher can safely invoke.
 */
export function isInquiryServerDispatchEligible(
  binding: SemanticCapabilityBinding,
  transport: InquiryPresentationTransport,
): boolean {
  if (binding.kind !== 'registry_capability' || !binding.executable) return false
  if (binding.binding_id !== `registry:${binding.capability_uri}`) return false
  const channels = binding.execution_channels ?? ['platform_internal']
  return SERVER_DISPATCH_CHANNELS[transport].some((channel) => channels.includes(channel))
}
