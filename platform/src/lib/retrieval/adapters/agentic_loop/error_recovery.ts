/**
 * Agentic Loop Adapter — Error Recovery
 * =======================================
 * Semantic alternatives on tool failure.
 * Routes around broken tools to functionally equivalent ones.
 */

import type { CapabilityUri } from '@/lib/retrieval/registry/types'
import { getCapability, listCapabilities } from '@/lib/retrieval/registry'

export interface ToolError {
  uri: CapabilityUri
  error_message: string
  error_type: 'not_found' | 'timeout' | 'invalid_args' | 'server_error' | 'data_empty'
  iteration: number
}

export interface RecoveryPlan {
  strategy: 'retry' | 'substitute' | 'skip' | 'fail'
  substitute_uri?: CapabilityUri
  modified_args?: Record<string, unknown>
  reasoning: string
}

/**
 * Decide recovery strategy for a failed tool call.
 */
export function planRecovery(
  error: ToolError,
  prior_errors: ToolError[],
  available_retries: number
): RecoveryPlan {
  const same_tool_errors = prior_errors.filter((e) => e.uri === error.uri)

  // If this tool has failed 3+ times, skip or substitute
  if (same_tool_errors.length >= 2) {
    const substitute = findSubstitute(error.uri)
    if (substitute) {
      return {
        strategy: 'substitute',
        substitute_uri: substitute,
        reasoning: `Tool ${error.uri} failed ${same_tool_errors.length + 1} times — substituting with ${substitute}`,
      }
    }
    return {
      strategy: 'skip',
      reasoning: `Tool ${error.uri} failed ${same_tool_errors.length + 1} times and no substitute available — skipping`,
    }
  }

  // For transient errors, retry
  if (error.error_type === 'timeout' || error.error_type === 'server_error') {
    if (available_retries > 0) {
      return {
        strategy: 'retry',
        reasoning: `Transient error (${error.error_type}) — retrying (${available_retries} retries left)`,
      }
    }
  }

  // For invalid args, try with relaxed args
  if (error.error_type === 'invalid_args') {
    return {
      strategy: 'substitute',
      reasoning: 'Invalid arguments — will retry with relaxed schema',
    }
  }

  // For empty data, skip gracefully
  if (error.error_type === 'data_empty') {
    return {
      strategy: 'skip',
      reasoning: 'No data found for query — skipping this tool',
    }
  }

  // Default: skip after exhausting retries
  if (available_retries <= 0) {
    return {
      strategy: 'skip',
      reasoning: `No retries remaining for ${error.uri} — skipping`,
    }
  }

  return {
    strategy: 'retry',
    reasoning: `Error type ${error.error_type} — retrying`,
  }
}

/**
 * Find a semantically equivalent substitute tool.
 */
function findSubstitute(uri: CapabilityUri): CapabilityUri | null {
  // Semantic substitution map
  const SUBSTITUTES: Record<string, CapabilityUri> = {
    'marsys://tool/L0/resolve_entity': 'marsys://tool/L0/list_entities',
    'marsys://tool/L0/list_entities': 'marsys://tool/L0/resolve_entity',
  }

  return SUBSTITUTES[uri] || null
}

/**
 * Classify an error from a tool call response.
 */
export function classifyError(
  uri: CapabilityUri,
  error: Error | unknown,
  iteration: number
): ToolError {
  const message = error instanceof Error ? error.message : String(error)

  let error_type: ToolError['error_type'] = 'server_error'

  if (message.includes('not found') || message.includes('404')) {
    error_type = 'not_found'
  } else if (message.includes('timeout') || message.includes('ETIMEDOUT')) {
    error_type = 'timeout'
  } else if (message.includes('argument') || message.includes('schema') || message.includes('required')) {
    error_type = 'invalid_args'
  } else if (message.includes('empty') || message.includes('no results') || message.includes('0 rows')) {
    error_type = 'data_empty'
  }

  return { uri, error_message: message, error_type, iteration }
}
