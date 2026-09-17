import type { Depth } from '@/lib/vidhi/scope_classifier'
import type { CallType } from '@/lib/models/registry'

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
