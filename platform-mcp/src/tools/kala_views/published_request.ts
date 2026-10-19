/** K9-6 published-stage transport. Existing public calls remain legacy aliases.
 * This explicit request reads the same public registry identity the Vidhi bridge
 * resolves. No legacy selector conversion, astrology, fallback or state rewrite.
 */
import type { CallToolResult } from '@modelcontextprotocol/sdk/types.js'
import type { Principal } from '../../types.js'
import { remoteAuthorize } from '../../lib/authz.js'
import type { KalaView } from './registry_alias.js'
import { callKalaRegistryCap } from './shared.js'
import { stageDensityBudgetSections } from './stage_budget.js'
import { finalizeMcpBudget } from '../../lib/response_budget.js'

type Data = Record<string, unknown>
const object = (value: unknown): Data | null => value !== null && typeof value === 'object'
  && !Array.isArray(value) ? value as Data : null
const output = (content: Data, isError = false): CallToolResult => ({
  structuredContent: { type: 'object', object: content },
  content: [{ type: 'text', text: JSON.stringify(content) }], ...(isError ? { isError: true } : {}),
})

export async function servePublishedRequest(principal: Principal, view: KalaView, args: Data): Promise<CallToolResult> {
  const unavailable = (empty_reason: string) => output({ view, chart_id: args.chart_id ?? null,
    manifest_id: null, generation: null, empty_reason, rows: [] }, true)
  if (typeof args.chart_id !== 'string') return unavailable('invalid_request')
  try {
    if (await remoteAuthorize(principal, args.chart_id) !== true) return unavailable('authorization_denied')
  } catch { return unavailable('authorization_unavailable') }
  try {
    const response = object(await callKalaRegistryCap(`marsys://tool/L3/kala_${view}_get`,
      { chart_id: args.chart_id, published_request: args.published_request }, principal))
    if (response?.is_error === true) {
      return unavailable(typeof object(response.content)?.empty_reason === 'string'
        ? object(response.content)!.empty_reason as string : 'query_failed')
    }
    const content = object(response?.content)
    const manifest = object(content?.manifest)
    if (response?.is_error !== false || !content || content.view !== view || content.chart_id !== args.chart_id || !Array.isArray(content.rows)
      || (content.manifest_id === null ? content.empty_reason !== 'unpublished' || content.rows.length !== 0 || content.generation !== null || content.manifest !== null
        : typeof content.manifest_id !== 'string' || !content.manifest_id
          || typeof content.generation !== 'string' || !content.generation
          || manifest?.manifest_id !== content.manifest_id || manifest?.generation !== content.generation
          || (content.rows.length ? content.empty_reason !== null : content.empty_reason !== 'no_matching_rows'))) {
      return unavailable('invalid_published_snapshot')
    }
    const finalized = finalizeMcpBudget(content, { maxKb: 40, sections: stageDensityBudgetSections(content) })
    return output(finalized)
  } catch { return unavailable('query_failed') }
}
