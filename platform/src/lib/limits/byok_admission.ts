import 'server-only'

import { checkRpm } from '@/lib/mcp/rate_limiter_core'

const MAX_QUESTION_CHARS = 32_000
const MAX_EVIDENCE_CHARS = 2_000_000
const MAX_OUTPUT_TOKENS = 16_384
const MAX_CONCURRENT_TURNS_PER_USER = 2

const activeTurns = new Map<string, number>()

export type ByokAdmission =
  | { allowed: true; release(): void }
  | { allowed: false; code: 'AI_RATE_LIMITED' | 'AI_EXECUTION_FAILED'; retryAfterSeconds?: number }

/**
 * BYOK admission deliberately has no price projection: provider prices and
 * subscription economics are not authoritative here. It applies the shared
 * request-rate counter plus explicit request/evidence/output hard caps once.
 */
export function admitByokTurn(input: {
  userId: string
  questionChars: number
  evidenceChars?: number
  outputTokens?: number
}): ByokAdmission {
  if (input.questionChars < 0 || input.questionChars > MAX_QUESTION_CHARS
    || (input.evidenceChars ?? 0) > MAX_EVIDENCE_CHARS
    || (input.outputTokens ?? MAX_OUTPUT_TOKENS) > MAX_OUTPUT_TOKENS) {
    return { allowed: false, code: 'AI_EXECUTION_FAILED' }
  }

  const rate = checkRpm(`web:byok:user:${input.userId}`)
  if (!rate.allowed) {
    return { allowed: false, code: 'AI_RATE_LIMITED', retryAfterSeconds: rate.retry_after_seconds }
  }

  const current = activeTurns.get(input.userId) ?? 0
  if (current >= MAX_CONCURRENT_TURNS_PER_USER) return { allowed: false, code: 'AI_RATE_LIMITED' }
  activeTurns.set(input.userId, current + 1)
  let released = false
  return {
    allowed: true,
    release() {
      if (released) return
      released = true
      const next = Math.max(0, (activeTurns.get(input.userId) ?? 1) - 1)
      if (next === 0) activeTurns.delete(input.userId)
      else activeTurns.set(input.userId, next)
    },
  }
}
