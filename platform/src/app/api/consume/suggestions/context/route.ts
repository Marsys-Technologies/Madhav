/**
 * /api/consume/suggestions/context — Gate III §11.
 *
 * Returns 4–6 suggested questions grounded in the native's current dasha +
 * transit context. Cached per-session in-memory (TTL 24h) to avoid a Flash
 * call on every empty-state render.
 *
 * Auth: any authenticated user (suggestions are non-sensitive). Native-tier
 * gating happens at the surrounding consume page.
 */

import { generateText } from 'ai'
import { getServerUser } from '@/lib/firebase/server'
import { resolveModel } from '@/lib/models/resolver'
import { TITLE_MODEL_ID } from '@/lib/models/registry'
import { res } from '@/lib/errors'

// 24-hour TTL, in-memory single-instance cache. Cloud Run instances are
// short-lived, so cache hits only apply within an instance; that's fine for
// the empty-state surface which is rendered at most a few times per session.
interface CacheEntry { value: string[]; expiresAt: number }
const _cache = new Map<string, CacheEntry>()
const TTL_MS = 24 * 60 * 60 * 1000

function todayUtc(): string {
  return new Date().toISOString().slice(0, 10)
}

const FALLBACK_SUGGESTIONS = [
  'Give me a one-paragraph snapshot of where my chart is today.',
  'Which planets in my chart are most active in the current period?',
  'What does the running Mahadasha say about my next 6 months?',
  'Are there any classical contradictions in my current transit picture?',
  'Surface one signal I should pay attention to this week.',
]

export async function GET(request: Request) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  const url = new URL(request.url)
  const chartId = url.searchParams.get('chartId') ?? 'unknown'
  const key = `${user.uid}:${chartId}:${todayUtc()}`

  const cached = _cache.get(key)
  if (cached && cached.expiresAt > Date.now()) {
    return Response.json({ suggestions: cached.value, cached: true })
  }

  // For now, the prompt is moment-agnostic — generating chart-specific
  // moment suggestions requires reading the native's dasha/transit state,
  // which is best added behind a follow-up brief. Fall back to a small
  // Flash call that varies wording within a fixed pool, keyed by date.
  let suggestions: string[]
  try {
    const completion = await generateText({
      model: resolveModel(TITLE_MODEL_ID),
      system:
        'You suggest 5 evocative one-sentence questions a native might ask their Jyotish chart today. Return exactly 5 lines, each a question, no numbering, no preface, no trailing punctuation beyond a question mark.',
      prompt: `Today is ${todayUtc()}. Suggest 5 questions that frame a Jyotish chart inquiry without naming any planet or dasha by name (those are the native's surprise).`,
      maxOutputTokens: 250,
    })
    suggestions = completion.text
      .split('\n')
      .map(l => l.replace(/^[-*\d.\s]+/, '').trim())
      .filter(l => l.length > 0)
      .slice(0, 5)
    if (suggestions.length < 3) suggestions = FALLBACK_SUGGESTIONS
  } catch {
    suggestions = FALLBACK_SUGGESTIONS
  }

  _cache.set(key, { value: suggestions, expiresAt: Date.now() + TTL_MS })
  return Response.json({ suggestions, cached: false })
}

// Test helper — clears the per-instance cache.
export function __resetSuggestionsCache(): void {
  _cache.clear()
}
