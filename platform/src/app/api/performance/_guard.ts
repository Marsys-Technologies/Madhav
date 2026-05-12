import 'server-only'
import { NextResponse } from 'next/server'
import type { DecodedIdToken } from 'firebase-admin/auth'
import { requireSuperAdmin, type ProfileAuth } from '@/lib/auth/access-control'

/**
 * Gate I — shared super-admin guard for /api/performance/* handlers.
 * Mirrors the observatory guard pattern (`_guard.ts` in admin/observatory),
 * minus the feature-flag — performance APIs are unconditionally super-admin.
 */
export interface PerformanceAuthContext {
  user: DecodedIdToken
  profile: ProfileAuth
}

export async function guardPerformanceRoute(): Promise<
  NextResponse | PerformanceAuthContext
> {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth
  return auth
}

/** ISO-8601 parsing helper used by all performance endpoints. */
export function parseTimeWindow(url: URL): { start: string; end: string } | { error: string } {
  const start = url.searchParams.get('window_start')
  const end = url.searchParams.get('window_end')
  if (!start || !end) return { error: 'window_start and window_end are required' }
  if (Number.isNaN(Date.parse(start)) || Number.isNaN(Date.parse(end))) {
    return { error: 'window_start and window_end must be ISO-8601' }
  }
  if (Date.parse(start) >= Date.parse(end)) {
    return { error: 'window_start must be before window_end' }
  }
  return { start, end }
}

export function parseSource(url: URL): 'consume' | 'eval' | 'all' {
  const s = url.searchParams.get('source')
  if (s === 'consume' || s === 'eval') return s
  return 'all'
}
