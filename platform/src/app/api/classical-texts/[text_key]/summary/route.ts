/**
 * GET /api/classical-texts/[text_key]/summary
 * Returns metadata row from classical_texts for the given text_key.
 * Internal endpoint — requires x-mcp-internal-token header.
 *
 * brahmagyan.texts delta build 2026-06-03
 */

import { NextRequest, NextResponse } from 'next/server'
import { validateServiceToken } from '@/lib/mcp/service_token'
import { getClassicalTextSummary } from '@/lib/tools/classical_text_summary'

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ text_key: string }> }
): Promise<NextResponse> {
  if (!validateServiceToken(req)) {
    return NextResponse.json({ error: 'forbidden' }, { status: 403 })
  }

  const { text_key } = await params
  const summary = await getClassicalTextSummary(text_key)
  if (summary === null) {
    return NextResponse.json({ error: 'not_found' }, { status: 404 })
  }
  return NextResponse.json(summary)
}
