/**
 * POST /api/panchang/feed/revoke
 *
 * Revokes iCal feed tokens for the current user.
 *
 * Body:
 *   {}                          — revokes ALL active tokens for the user
 *   { token_sig: string }       — revokes a specific token by its HMAC signature
 *
 * Returns: { revoked: number }  — count of tokens revoked
 *
 * After revocation, previously-issued feed URLs return 401.
 * Auth-gated: requires Firebase session.
 *
 * Phase: 4C-7 (Item 7)
 */

import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { res } from '@/lib/errors'
import { revokeAllUserTokens, revokeToken } from '@/lib/panchang/feed_revocations'

interface RevokeBody {
  jti?: string
}

export async function POST(request: NextRequest) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  let body: RevokeBody = {}
  try {
    body = (await request.json()) as RevokeBody
  } catch {
    // empty body is valid — means revoke all
  }

  if (body.jti) {
    // Revoke a specific token by jti
    const revoked = await revokeToken(user.uid, body.jti)
    return NextResponse.json({ revoked: revoked ? 1 : 0 })
  }

  // Revoke all tokens for this user
  const count = await revokeAllUserTokens(user.uid)
  return NextResponse.json({ revoked: count })
}
