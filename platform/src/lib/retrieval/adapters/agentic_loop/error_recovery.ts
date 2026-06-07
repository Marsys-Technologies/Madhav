/**
 * adapters/agentic_loop/error_recovery.ts
 *
 * Semantic alternatives on tool failure.
 * When a tool call fails, finds semantically equivalent alternatives
 * and retries with exponential backoff.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import { listCapabilities } from '../../registry'

export interface ToolError {
  uri: string
  error: string
  args: Record<string, unknown>
  attempt: number
}

export interface RecoveryAction {
  action: 'retry' | 'fallback_uri' | 'skip' | 'abort'
  uri?: string
  modified_args?: Record<string, unknown>
  rationale: string
}

/**
 * Find semantically similar tools as fallback candidates.
 * Strategy: same layer, similar name tokens.
 */
function findFallbackCandidates(failedUri: string): string[] {
  const caps = listCapabilities({ primitive_type: 'tool' })
  const failedName = failedUri.split('/').pop() ?? ''
  const failedLayer = failedUri.match(/marsys:\/\/tool\/([^/]+)\//)?.[1]

  return caps
    .filter(c => {
      if (c.uri === failedUri) return false
      // Same layer preferred
      const sameLayer = c.uri.includes(`/${failedLayer}/`)
      // Similar name tokens
      const nameTokens = failedName.split('_')
      const hasOverlap = nameTokens.some(t => c.name.toLowerCase().includes(t.toLowerCase()))
      return sameLayer && hasOverlap
    })
    .map(c => c.uri)
    .slice(0, 3)
}

/**
 * Suggest a recovery action for a failed tool call.
 */
export function suggestRecovery(error: ToolError): RecoveryAction {
  const { attempt } = error

  // Attempt 1-2: retry with exponential backoff hint
  if (attempt <= 2) {
    return {
      action: 'retry',
      modified_args: error.args,
      rationale: `Transient error — retry attempt ${attempt + 1}`,
    }
  }

  // Attempt 3: try fallback URI
  const fallbacks = findFallbackCandidates(error.uri)
  if (fallbacks.length > 0) {
    return {
      action: 'fallback_uri',
      uri: fallbacks[0],
      modified_args: error.args,
      rationale: `Primary tool failed ${attempt} times — trying semantic alternative: ${fallbacks[0]}`,
    }
  }

  // Attempt 4: skip
  if (attempt >= 4) {
    return {
      action: 'skip',
      rationale: `Tool ${error.uri} failed ${attempt} times with no alternatives — skipping (non-fatal)`,
    }
  }

  return {
    action: 'skip',
    rationale: `No recovery path found for ${error.uri}`,
  }
}

/**
 * Error recovery log entry for Smriti audit.
 */
export interface RecoveryLogEntry {
  timestamp: string
  uri: string
  attempt: number
  error: string
  action: string
  rationale: string
}

export class ErrorRecoveryLog {
  private entries: RecoveryLogEntry[] = []

  record(error: ToolError, action: RecoveryAction): void {
    this.entries.push({
      timestamp: new Date().toISOString(),
      uri: error.uri,
      attempt: error.attempt,
      error: error.error,
      action: action.action,
      rationale: action.rationale,
    })
  }

  get log(): RecoveryLogEntry[] {
    return [...this.entries]
  }
}
