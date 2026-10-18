/** K9-6 explicit, additive public access to the existing published-stage readers.
 * (I) INTERPRETATION: callers opt in with exact stage selectors; legacy dates,
 * domains and undertakings are never converted into different identities.
 * The capability API owns chart authorization, as for the stage readers.
 */
import type { CapabilityContext, ToolResult } from '../../types'
import type { ViewName } from './view_common'

const readers = {
  now: () => import('./view_now').then(m => m.nowViewCapability),
  ahead: () => import('./view_ahead').then(m => m.aheadViewCapability),
  priority: () => import('./view_priority').then(m => m.priorityViewCapability),
  elect: () => import('./view_elect').then(m => m.electViewCapability),
  story: () => import('./view_story').then(m => m.storyViewCapability),
  ritual: () => import('./view_ritual').then(m => m.ritualViewCapability),
  explain: () => import('./view_explain').then(m => m.explainViewCapability),
}
const selectors = new Set(['at', 'date_from', 'date_to', 'event_class', 'assertion_id',
  'source_table', 'record_id', 'limit', 'offset'])

export async function servePublishedRequest(view: ViewName, args: Record<string, unknown>, context?: CapabilityContext): Promise<ToolResult> {
  const request = args.published_request
  if (typeof args.chart_id !== 'string' || !/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(args.chart_id)
    || !request || typeof request !== 'object' || Array.isArray(request)
    || Object.keys(request).some(key => !selectors.has(key))) {
    return { is_error: true, content: { view, manifest_id: null, empty_reason: 'invalid_request' } }
  }
  const capability = await readers[view]()
  return capability.handler!({ ...request, chart_id: args.chart_id }, context)
}
