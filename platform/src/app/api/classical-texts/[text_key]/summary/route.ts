/**
 * GET /api/classical-texts/[text_key]/summary
 * Returns metadata row from classical_texts for the given text_key.
 * Internal endpoint — requires x-mcp-internal-token header.
 *
 * brahmagyan.texts delta build 2026-06-03
 */

import { NextRequest, NextResponse } from 'next/server'
import { query } from '@/lib/db/client'

const INTERNAL_TOKEN = process.env.MCP_INTERNAL_TOKEN ?? ''

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ text_key: string }> }
): Promise<NextResponse> {
  const token = req.headers.get('x-mcp-internal-token') ?? ''
  if (!INTERNAL_TOKEN || token !== INTERNAL_TOKEN) {
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
