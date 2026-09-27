import 'server-only'

import { safeValidateUIMessages, type UIMessage } from 'ai'
import { checkRpm } from '@/lib/mcp/rate_limiter_core'
import { AiConsoleError } from '@/lib/ai-console/errors'

export const BYOK_MAX_QUESTION_CHARS = 32_000
export const BYOK_MAX_EVIDENCE_CHARS = 2_000_000
export const BYOK_MAX_OUTPUT_TOKENS = 16_384
/** MCP's external host synthesizes; this ceiling is wire-size, not model context. */
export const MCP_BYOK_EVIDENCE_ENVELOPE_MAX_BYTES = 1800 * 1024
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
  if (input.questionChars < 0 || input.questionChars > BYOK_MAX_QUESTION_CHARS
    || (input.evidenceChars ?? 0) > BYOK_MAX_EVIDENCE_CHARS
    || (input.outputTokens ?? BYOK_MAX_OUTPUT_TOKENS) > BYOK_MAX_OUTPUT_TOKENS) {
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

/** Post-hydration cap check; this deliberately does not consume a second admission. */
export function isByokEvidenceWithinLimit(evidenceChars: number): boolean {
  return Number.isSafeInteger(evidenceChars) && evidenceChars >= 0
    && evidenceChars <= BYOK_MAX_EVIDENCE_CHARS
}

/** Measure an evidence payload after JSON normalization using its actual UTF-8 wire size. */
export function isByokEvidencePayloadWithinLimit(payload: unknown): boolean {
  try {
    return isByokEvidenceWithinLimit(Buffer.byteLength(JSON.stringify(payload), 'utf8'))
  } catch {
    return false
  }
}

export function isMcpEvidenceEnvelopeWithinLimit(payload: unknown): boolean {
  try {
    return Buffer.byteLength(JSON.stringify(payload), 'utf8') <= MCP_BYOK_EVIDENCE_ENVELOPE_MAX_BYTES
  } catch {
    return false
  }
}

/**
 * Validate the complete client-controlled UI history and cap its normalized
 * UTF-8 representation. This deliberately counts every supported part rather
 * than extracting only user text, so assistant reasoning/tool/data payloads
 * cannot bypass the pre-execution evidence ceiling.
 */
export async function validateByokUiMessages(input: unknown): Promise<UIMessage[]> {
  const validated = await safeValidateUIMessages({ messages: input })
  if (!validated.success) throw new AiConsoleError('AI_EXECUTION_FAILED')
  if (!isByokEvidencePayloadWithinLimit(validated.data)) throw new AiConsoleError('AI_EXECUTION_FAILED')
  return validated.data
}
