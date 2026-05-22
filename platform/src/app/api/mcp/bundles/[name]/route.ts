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

const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

// ── Auth guard ─────────────────────────────────────────────────────────────────

function validateInternalToken(req: NextRequest): boolean {
  const token = req.headers.get('X-MCP-Internal-Token')
  return !!token && token === MCP_INTERNAL_TOKEN
}

function extractPrincipal(req: NextRequest): {
  user_uid: string
  audience_tier: string
  key_id: string
} | null {
  const user_uid = req.headers.get('X-MCP-User')
  const audience_tier = req.headers.get('X-MCP-Audience-Tier')
  const key_id = req.headers.get('X-MCP-Key-Id')
  if (!user_uid || !audience_tier || !key_id) return null
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
  if (!validateInternalToken(req)) {
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
          const { executeHolisticBundle } = await import('../../../../../../lib/mcp/bundle_adapters.js')
          await executeHolisticBundle(
            {
              query_text: (body['query_text'] as string) ?? '',
              focus_domains: body['focus_domains'] as string[] | undefined,
              time_window: body['time_window'] as { start?: string; end?: string } | undefined,
              subset: body['subset'] as string[] | undefined,
              tier: principal.audience_tier,
              chart_id: body['chart_id'] as string | undefined,
            },
            principal,
            (event) => {
              enqueue(event.type, event)
            }
          )
        } else {
          const { executeMultiSchoolBundle } = await import('../../../../../../lib/mcp/bundle_adapters.js')
          await executeMultiSchoolBundle(
            {
              claim: (body['claim'] as string) ?? '',
              schools: body['schools'] as Array<'parashara' | 'jaimini' | 'kp' | 'tajaka'> | undefined,
              tier: principal.audience_tier,
              chart_id: body['chart_id'] as string | undefined,
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
