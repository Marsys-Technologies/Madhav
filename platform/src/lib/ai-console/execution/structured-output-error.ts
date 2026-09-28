import 'server-only'

import { inspect } from 'node:util'

import type { AiRole } from '../types'

const MAX_REPAIR_CANDIDATE_CHARS = 65_536

/**
 * Server-only discriminator for a model response that failed local structured
 * validation. The bounded candidate is intentionally private and may only be
 * read to construct the one same-executor repair request.
 */
export class StructuredOutputValidationError extends Error {
  readonly code = 'AI_EXECUTION_FAILED' as const
  readonly role: AiRole
  #candidate: string

  constructor(role: AiRole, candidate: string) {
    super('AI execution failed.')
    this.name = 'StructuredOutputValidationError'
    this.role = role
    this.#candidate = candidate.slice(0, MAX_REPAIR_CANDIDATE_CHARS)
  }

  candidateText(): string { return this.#candidate }

  toJSON(): never { throw new Error('Structured output validation failures are not serializable') }

  [inspect.custom](): string { return `[StructuredOutputValidationError role=${this.role}]` }
}

export function isStructuredOutputValidationError(value: unknown): value is StructuredOutputValidationError {
  return value instanceof StructuredOutputValidationError
}
