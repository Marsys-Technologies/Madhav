import type { Depth } from '@/lib/vidhi/scope_classifier'
import type { CallType } from '@/lib/models/registry'
import type { InquiryPlanningProvenance } from './types'

export interface InquiryPlanningPolicy {
  readonly callType: Extract<CallType, 'planner_fast' | 'planner_deep'>
  readonly reasoning: 'auto' | 'enable'
}

/**
 * The deterministic scope classifier, rather than model prose, chooses the
 * planning budget. Deep inquiry is the only scope that may consume the deep
 * planner slot; all bounded lookup/standard requests retain the fast path.
 */
export function selectInquiryPlanningPolicy(depth: Depth): InquiryPlanningPolicy {
  return depth === 'deep'
    ? { callType: 'planner_deep', reasoning: 'enable' }
    : { callType: 'planner_fast', reasoning: 'auto' }
}

/** Planning provenance for a door whose server-side planner model proposed the plan. */
export function serverPlannerProvenance(
  depth: Depth,
  metrics: { readonly active_model_id?: string; readonly fallback_used?: boolean } | null | undefined,
): InquiryPlanningProvenance {
  const policy = selectInquiryPlanningPolicy(depth)
  return {
    planner: 'model',
    ai_proposal_source: 'server_planner',
    call_type: policy.callType,
    reasoning_requested: policy.reasoning,
    model_id: typeof metrics?.active_model_id === 'string' ? metrics.active_model_id : null,
    fallback_used: typeof metrics?.fallback_used === 'boolean' ? metrics.fallback_used : null,
  }
}

/** Planning provenance for the raw door: deterministic compilation of a caller proposal. */
export function deterministicCompilerProvenance(callerProposal: boolean): InquiryPlanningProvenance {
  return {
    planner: 'deterministic_compiler',
    ai_proposal_source: callerProposal ? 'caller' : 'none',
    call_type: null,
    reasoning_requested: null,
    model_id: null,
    fallback_used: null,
  }
}
