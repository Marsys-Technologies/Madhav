/**
 * GET /api/classical-texts/[text_key]/summary
 * Returns metadata row from classical_texts for the given text_key.
 * Internal endpoint — requires x-mcp-internal-token header.
 *
 * brahmagyan.texts delta build 2026-06-03
 */

import { NextRequest, NextResponse } from 'next/server'
import { query } from '@/lib/db/client'
import { validateServiceToken } from '@/lib/mcp/service_token'

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ text_key: string }> }
): Promise<NextResponse> {
  if (!validateServiceToken(req)) {
    return NextResponse.json({ error: 'forbidden' }, { status: 403 })
  }

  const { text_key } = await params
  const result = await query<{
    text_key: string
    title: string
    author: string | null
    tradition: string
    school: string
    tier: number
    language_original: string
    translation_author: string | null
    chunk_count: number
    attribution_baseline_confidence: number
  }>(
    `SELECT text_key, title, author, tradition, school, tier, language_original,
            translation_author, chunk_count, attribution_baseline_confidence
     FROM classical_texts WHERE text_key = $1 LIMIT 1`,
    [text_key]
  )

  if (result.rows.length === 0) {
    return NextResponse.json({ error: 'not_found' }, { status: 404 })
  }
  return NextResponse.json(result.rows[0])
}
