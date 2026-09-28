/**
 * The door-side constructor for the shared envelope evaluator's live state (Packet B).
 *
 * The evaluator itself is pure. This is the one place that binds it to the process's real registry,
 * the no-leakage filter and the request's safety exclusions, so Portal, managed and raw MCP read
 * the same facts the same way and differ only in what they know about the request (principal,
 * access, cost, exclusions).
 */
import { filterLeakedCapabilities } from '@/lib/pipeline/no_leakage_filter'
import { applyCapabilityExclusion } from '@/lib/pariprashna/safety/sensitive_capabilities'
import { getCapability } from '@/lib/retrieval/registry'
import { getToolByName } from '@/lib/retrieval/registry/tool_name_bridge'
import type { InquiryPresentationTransport } from './execution_policy'
import type { SuccessorAdmissionLiveContext } from './authorization_envelope'

export function buildSuccessorAdmissionLive(args: {
  transport: InquiryPresentationTransport
  /** The chart this request is authorized for. */
  chart_id: string
  overlay: { readonly overlay_version: string | null; readonly build_id: string | null }
  principal_subject: string
  /** The principal that owns the lifecycle / request the contract was issued to. */
  owner_principal_subject: string
  /** The permission the door's own chart authorization returned for this principal in this request. */
  chart_permission: 'all' | 'view' | 'deny' | null
  /** Capabilities the request's own safety pass excluded (names or URIs). Empty for a door with no such pass. */
  excluded_capabilities?: readonly string[]
  cost_exhausted: boolean
}): SuccessorAdmissionLiveContext {
  const excluded = args.excluded_capabilities ?? []
  return {
    transport: args.transport,
    chart_id: args.chart_id,
    principal_subject: args.principal_subject,
    owner_principal_subject: args.owner_principal_subject,
    chart_permission: args.chart_permission,
    overlay_version: args.overlay.overlay_version,
    build_id: args.overlay.build_id,
    describe: (uri) => getCapability(uri),
    tool_exists: (uri) => getToolByName(uri) !== undefined,
    is_capability_denied: (uri) => filterLeakedCapabilities([uri]).length === 0
      || applyCapabilityExclusion([uri], excluded).stripped.length > 0,
    cost_exhausted: args.cost_exhausted,
  }
}
