/**
 * POST /api/panchang/feed/subscribe
 *
 * Generates a signed iCal feed URL for the current user.
 *
 * Body: { location: string; personalise?: boolean; chart_id?: string }
 *
 * Returns: { feed_url: string; expires_at: number; token_sig: string }
 *   - feed_url: the full subscribable URL (no PII — token only carries location + hash)
 *   - expires_at: unix timestamp (90 days from now)
 *   - token_sig: the HMAC portion (for revocation reference in the token list)
 *
 * Auth-gated: requires Firebase session.
 *
 * Phase: 4C-7 (Item 6)
 */

import { NextRequest, NextResponse } from 'next/server'
import { createHash, randomBytes } from 'crypto'
import { getServerUser } from '@/lib/firebase/server'
import { res } from '@/lib/errors'
import {
  signFeedToken,
  makeFeedTokenExpiry,
  type FeedTokenPayload,
} from '@/lib/security/sign_url'
import { registerFeedToken } from '@/lib/panchang/feed_revocations'

const APP_URL = process.env.NEXT_PUBLIC_APP_URL ?? 'https://amjis-web.run.app'

interface SubscribeBody {
  location?: string
  personalise?: boolean
  chart_id?: string
}

export async function POST(request: NextRequest) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  let body: SubscribeBody
  try {
    body = (await request.json()) as SubscribeBody
  } catch {
    return res.badRequest('Invalid request body')
  }

  const location = (body.location ?? 'bhubaneswar').toLowerCase().trim()
  const expires_at = makeFeedTokenExpiry()
  const issued_at = Math.floor(Date.now() / 1000)

  // Generate a random token ID (jti) — no PII in the token payload
  const jti = randomBytes(16).toString('hex')

  // If personalise + chart_id provided, hash the chart_id (never store/expose raw)
  let personalise: string | undefined
  if (body.personalise && body.chart_id) {
    personalise = createHash('sha256').update(body.chart_id).digest('hex').slice(0, 16)
  }

  // Token payload: NO user_id, NO chart_id — only jti + location + optional hash
  const tokenPayload: FeedTokenPayload = {
    jti,
    location,
    issued_at,
    expires_at,
    ...(personalise ? { personalise } : {}),
  }

  const token = signFeedToken(tokenPayload)

  // Register in DB: user_id stored only here (not in token)
  try {
    await registerFeedToken({
      user_id: user.uid,
      jti,
      location,
      issued_at,
      expires_at,
    })
  } catch (err) {
    // Log but don't fail — token is valid even if DB registration fails
    console.error('[subscribe] Failed to register token:', err)
  }

  const feedUrl = `${APP_URL}/api/panchang/feed.ics?token=${encodeURIComponent(token)}`

  return NextResponse.json(
    {
      feed_url: feedUrl,
      expires_at,
      jti,
    },
    { status: 200 },
  )
}
