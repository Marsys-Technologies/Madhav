/**
 * /api/mcp/surface-spec — Published seam output for per-model MCP surfaces.
 *
 * Exposes getMcpSurfaceSpec(family) as an HTTP endpoint so the MCP fork
 * (platform-mcp, a separate process) can call it at startup or per-request
 * to learn the surface constraints for a declared model family.
 *
 * The MCP fork is a separate Node.js process and cannot import from platform/src
 * directly. This route is the cross-process seam:
 *
 *   platform-mcp → GET /api/mcp/surface-spec?family=anthropic
 *               ← { family, max_tools, tool_name_pattern, requires_dual_output,
 *                   strip_mcp_constructs, transport }
 *
 * Auth: MCP_INTERNAL_TOKEN (X-MCP-Internal-Token header) — same service-to-service
 * auth used by all /api/mcp/* routes. No per-user principal needed; surface spec
 * is chart-agnostic and family-static.
 *
 * Both channels (chat engine + MCP fork) derive surface constraints from the SAME
 * getMcpSurfaceSpec() call. No per-channel duplication of per-family logic.
 *
 * Valid family values: 'anthropic' | 'gemini' | 'openai' | 'deepseek' | 'universal'
 * Omitting family or passing an unknown value → 'universal' (conservative fallback).
 *
 * R2.2 — RETRIEVAL_RECONFIRM published seam.
 */

import 'server-only'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { getMcpSurfaceSpec } from '@/lib/retrieval/maro'
import type { ModelFamily } from '@/lib/retrieval/maro'
import { validateServiceToken } from '@/lib/mcp/service_token'

const VALID_FAMILIES: ModelFamily[] = ['anthropic', 'gemini', 'openai', 'deepseek', 'universal']

export async function GET(req: NextRequest): Promise<Response> {
  if (!validateServiceToken(req)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const familyParam = req.nextUrl.searchParams.get('family')
  const family: ModelFamily =
    familyParam && (VALID_FAMILIES as string[]).includes(familyParam)
      ? (familyParam as ModelFamily)
      : 'universal'

  const spec = getMcpSurfaceSpec(family)

  return NextResponse.json({
    ok: true,
    spec,
    // Hint to MCP fork: resolved_family may differ from requested if the param was
    // unrecognized — MCP fork should log this for observability.
    resolved_family: family,
    requested_family: familyParam ?? null,
  })
}

// POST variant for callers that cannot easily set query params (e.g. some HTTP clients)
export async function POST(req: NextRequest): Promise<Response> {
  if (!validateServiceToken(req)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  let body: Record<string, unknown> = {}
  try {
    body = (await req.json()) as Record<string, unknown>
  } catch {
    // body is optional for POST — default to universal
  }

  const familyParam = typeof body['family'] === 'string' ? body['family'] : null
  const family: ModelFamily =
    familyParam && (VALID_FAMILIES as string[]).includes(familyParam)
      ? (familyParam as ModelFamily)
      : 'universal'

  const spec = getMcpSurfaceSpec(family)

  return NextResponse.json({
    ok: true,
    spec,
    resolved_family: family,
    requested_family: familyParam,
  })
}
