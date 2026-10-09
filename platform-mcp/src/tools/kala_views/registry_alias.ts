/**
 * KYD-123 legacy adapter for the seven public registry descriptors. The MCP
 * package is a separate deployment unit, so this structurally implements the
 * L3 LegacyViewAdapter contract without importing platform runtime modules.
 *
 * The registered aliases retain the established callbacks until a published
 * generation has a golden-equivalent binding. Dates, undertaking and domain
 * are never guessed into stage selectors; the registry's *_read tools remain
 * separately callable. There is no candidate cutover here.
 */
import type { McpServer, ToolCallback } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { ZodRawShapeCompat } from '@modelcontextprotocol/sdk/server/zod-compat.js'
import type { CallToolResult } from '@modelcontextprotocol/sdk/types.js'
import { remoteAuthorize } from '../../lib/authz.js'
import type { Principal } from '../../types.js'

export type KalaView = 'now' | 'ahead' | 'priority' | 'elect' | 'story' | 'ritual' | 'explain'
export type PublicViewName = `kala_${KalaView}_get`
export const publicViewName = (view: KalaView): PublicViewName => `kala_${view}_get`

export interface KalaLegacyAdapter {
  authorize(chart_id: string): Promise<boolean>
  invoke(public_name: PublicViewName, args: Record<string, unknown>): Promise<{
    content: CallToolResult; is_error: boolean
  }>
}

/**
 * Suitable for explicit injection into makeLegacyViewHandler(view, adapter).
 * Authorization stays tied to the MCP principal. The result is the complete
 * old MCP envelope, not a re-narration of the stage composite's rows.
 */
export function createKalaLegacyAdapter(
  principal: Principal,
  view: KalaView,
  legacy: (args: Record<string, unknown>) => Promise<CallToolResult>,
): KalaLegacyAdapter {
  return {
    authorize: chart_id => remoteAuthorize(principal, chart_id),
    async invoke(public_name, args) {
      if (public_name !== publicViewName(view)) {
        throw new Error(`Legacy adapter for ${publicViewName(view)} cannot answer ${public_name}`)
      }
      const content = await legacy(args)
      return { content, is_error: content.isError === true }
    },
  }
}

/** Keep the SDK schema, callback context, defaults and legacy authorization. */
export function registerKalaViewAlias<Args extends ZodRawShapeCompat>(
  server: McpServer,
  principal: Principal,
  view: KalaView,
  name: string,
  description: string,
  schema: Args,
  legacy: ToolCallback<Args>,
): void {
  if (name !== publicViewName(view)) throw new Error(`Unexpected public name for ${view}: ${name}`)
  // ToolCallback is an SDK conditional type. At this boundary Args is always a
  // raw object shape; the cast preserves that overload and its request context.
  type RawCallback = (args: Record<string, unknown>, extra: Parameters<ToolCallback<ZodRawShapeCompat>>[1]) =>
    CallToolResult | Promise<CallToolResult>
  const original = legacy as unknown as RawCallback
  const callback = (async (args, extra) => {
    const adapter = createKalaLegacyAdapter(principal, view, async forwarded => {
      return await original(forwarded, extra)
    })
    // MCP invokes the established callback's own entitlement gates. Explicit
    // registry injection calls adapter.authorize first; calling it twice here
    // would alter old refusal envelopes and ritual Mode-3's no-I/O redirect.
    return (await adapter.invoke(publicViewName(view), args)).content
  }) satisfies RawCallback
  server.tool(name, description, schema, callback as ToolCallback<Args>)
}
