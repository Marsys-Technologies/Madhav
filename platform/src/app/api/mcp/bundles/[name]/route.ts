/**
 * /api/mcp/bundles/[name] — SSE-streaming bundle endpoint.
 *
 * Accepts POST from the platform-mcp sidecar. Emits SSE events per arch §8:
 *   event: bundle.sub_tool.started
 *   event: bundle.sub_tool.completed
 *   event: bundle.sub_tool.error
 *   event: bundle.completed  (full envelope)
 *
 * Supported bundle names:
 *   holistic_bundle     — 8-tool parallel holistic read
 *   multi_school_bundle — cross-school convergence check
 *
 * Auth: X-MCP-Internal-Token + X-MCP-User / X-MCP-Audience-Tier / X-MCP-Key-Id
 *
 * MCPT v3.1.0-S2
 */

import 'server-only'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { validateServiceToken } from '@/lib/mcp/service_token'

// ── Auth guard ─────────────────────────────────────────────────────────────────

function extractPrincipal(req: NextRequest): {
  user_uid: string
  audience_tier: string  // @deprecated L0FR: field retained for logging only; not used for access control
  key_id: string
} | null {
  const user_uid = req.headers.get('X-MCP-User')
  const key_id = req.headers.get('X-MCP-Key-Id')
  // L0FR Stream A: audience_tier no longer gates access; retained for logging only
  const audience_tier = req.headers.get('X-MCP-Audience-Tier') ?? 'default'
  if (!user_uid || !key_id) return null
  return { user_uid, audience_tier, key_id }
}

// ── SSE helpers ────────────────────────────────────────────────────────────────

function formatSSE(event: string, data: unknown): string {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`
}

// ── Bundle dispatcher ──────────────────────────────────────────────────────────

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ name: string }> }
): Promise<Response> {
  // Auth check
  if (!validateServiceToken(req)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const principal = extractPrincipal(req)
  if (!principal) {
    return NextResponse.json({ error: 'Missing principal headers' }, { status: 401 })
  }

  const { name: bundleName } = await params

  let body: Record<string, unknown>
  try {
    body = (await req.json()) as Record<string, unknown>
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  // M0 entitlement gate — authorize chart access when chart_id is supplied.
  const chartId = body['chart_id'] as string | undefined
  if (chartId) {
    const { authorizeChartAccess } = await import('../../../../../lib/auth/authorizeChartAccess')
    const { resolveMcpPrincipalRole } = await import('../../../../../lib/mcp/auth')
    const { query } = await import('../../../../../lib/db/client')
    const role = await resolveMcpPrincipalRole(principal.user_uid)
    const perm = await authorizeChartAccess({ principal: { uid: principal.user_uid, role }, chartId, db: { query } })
    if (perm === 'deny') {
      // R5.1 C2 item 3 (Denial ≠ empty): this SSE-streaming route pre-dates the shared
      // McpErrorEnvelope shape (it returns a plain JSON body, not an SSE stream, for this
      // pre-flight check) — bring it onto the same distinct denial contract as
      // /api/mcp/primitives and /api/mcp/writes instead of its own ad-hoc { error, chartId }
      // shape. `error: 'AUTHZ_DENIED'` is KEPT for back-compat with any existing caller
      // keying on it; `denial` is the new additive, unambiguous signal.
      return NextResponse.json(
        {
          error: 'AUTHZ_DENIED',
          chartId,
          denial: {
            reason: 'entitlement' as const,
            chart_id: chartId,
            permission_found: 'deny' as const,
            permission_required: 'view' as const,
            distinct_from_empty: true as const,
          },
        },
        { status: 401 }
      )
    }
  }

  if (bundleName !== 'holistic_bundle' && bundleName !== 'multi_school_bundle') {
    return NextResponse.json(
      { error: `Unknown bundle: ${bundleName}. Valid: holistic_bundle, multi_school_bundle` },
      { status: 400 }
    )
  }

  // ── SSE ReadableStream ────────────────────────────────────────────────────────

  const stream = new ReadableStream({
    async start(controller) {
      const enqueue = (event: string, data: unknown): void => {
        controller.enqueue(new TextEncoder().encode(formatSSE(event, data)))
      }

      try {
        if (bundleName === 'holistic_bundle') {
          const { executeHolisticBundle } = await import('../../../../../lib/mcp/bundle_adapters')
          await executeHolisticBundle(
            {
              query_text: (body['query_text'] as string) ?? '',
              focus_domains: body['focus_domains'] as string[] | undefined,
              time_window: body['time_window'] as { start?: string; end?: string } | undefined,
              subset: body['subset'] as string[] | undefined,
              tier: principal.audience_tier,
              chart_id: body['chart_id'] as string | undefined,
              // R4: Multi-LLM Exposure params
              response_format: body['response_format'] as 'minimal' | 'standard' | 'detailed' | undefined,
              model_family: body['model_family'] as 'anthropic' | 'gemini' | 'openai' | 'deepseek' | 'universal' | undefined,
              behavioral_overrides: body['behavioral_overrides'] as Record<string, Record<string, unknown>> | undefined,
            },
            principal,
            (event) => {
              enqueue(event.type, event)
            }
          )
        } else {
          const { executeMultiSchoolBundle } = await import('../../../../../lib/mcp/bundle_adapters')
          await executeMultiSchoolBundle(
            {
              claim: (body['claim'] as string) ?? '',
              schools: body['schools'] as Array<'parashara' | 'jaimini' | 'kp' | 'tajaka'> | undefined,
              tier: principal.audience_tier,
              chart_id: body['chart_id'] as string | undefined,
              // R4: Multi-LLM Exposure params
              response_format: body['response_format'] as 'minimal' | 'standard' | 'detailed' | undefined,
              model_family: body['model_family'] as 'anthropic' | 'gemini' | 'openai' | 'deepseek' | 'universal' | undefined,
              behavioral_overrides: body['behavioral_overrides'] as Record<string, Record<string, unknown>> | undefined,
            },
            principal,
            (event) => {
              enqueue(event.type, event)
            }
          )
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err)
        enqueue('bundle.error', { error: message })
      } finally {
        controller.close()
      }
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no',
    },
  })
}
