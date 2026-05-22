import 'server-only'

/**
 * agentic_loop.ts — Generic agentic tool-loop engine (E-S1).
 *
 * The generic loop dispatches tool calls returned by the model, feeds the
 * results back, and continues until the model signals end-of-turn.
 *
 * Each provider has its own termination signal:
 *   - Anthropic:  stop_reason === 'tool_use'
 *   - Google:     finish_reason === 'FUNCTION_CALL' (mapped to 'function_calls')
 *   - OpenAI:     finish_reason === 'tool_calls'
 *   - DeepSeek:   finish_reason === 'tool_calls' (OpenAI-compat)
 *   - NVIDIA:     finish_reason === 'tool_calls' (OpenAI-compat, model-dependent)
 *
 * Safety cap: MAX_ITERATIONS (default 8) prevents runaway cost spirals.
 * When the cap is hit, AgenticLoopCapExceeded is thrown; route.ts surfaces a
 * user-facing message in the response stream.
 *
 * Phase: R11.E (E-S1 base, E-S2..E-S5 per-provider wiring, E-S6 interleaving,
 *         E-S7 error recovery, E-S8 cap safety, E-S9 observability).
 */

export const MAX_ITERATIONS = 8

/** Thrown when the loop hits MAX_ITERATIONS without a natural end-of-turn signal. */
export class AgenticLoopCapExceeded extends Error {
  readonly iterations: number

  constructor(iterations: number) {
    super(
      `[agentic-loop] Loop exceeded MAX_ITERATIONS (${MAX_ITERATIONS}) after ${iterations} iterations. ` +
        `Halting to prevent cost spiral. Last stop reason: tool_use / tool_calls / function_calls.`,
    )
    this.name = 'AgenticLoopCapExceeded'
    this.iterations = iterations
  }
}

// ---------------------------------------------------------------------------
// Termination-signal taxonomy
// ---------------------------------------------------------------------------

export type ToolLoopTerminationSignal =
  | 'stop_reason'           // Anthropic: stop_reason === 'tool_use'
  | 'finish_reason_function_calls'  // Google: finish_reason === 'FUNCTION_CALL' | 'function_calls'
  | 'finish_reason_tool_calls'      // OpenAI / DeepSeek / NVIDIA

/** Per-provider configuration for the loop engine. */
export interface AgenticLoopConfig {
  providerId: string
  terminationSignal: ToolLoopTerminationSignal
  /** Whether the provider preserves interleaved text-before-tool ordering. */
  supportsInterleavedTextTool: boolean
  /** Whether the provider uses extractReasoningMiddleware for <think> blocks. */
  hasReasoningMiddleware: boolean
  /** Max iterations for this provider (defaults to MAX_ITERATIONS). */
  maxIterations?: number
}

// ---------------------------------------------------------------------------
// Per-provider default configs
// ---------------------------------------------------------------------------

export const ANTHROPIC_LOOP_CONFIG: AgenticLoopConfig = {
  providerId: 'anthropic',
  terminationSignal: 'stop_reason',
  supportsInterleavedTextTool: true,
  hasReasoningMiddleware: false,
}

export const GOOGLE_LOOP_CONFIG: AgenticLoopConfig = {
  providerId: 'google',
  terminationSignal: 'finish_reason_function_calls',
  supportsInterleavedTextTool: true,
  hasReasoningMiddleware: false,
}

export const OPENAI_LOOP_CONFIG: AgenticLoopConfig = {
  providerId: 'openai',
  terminationSignal: 'finish_reason_tool_calls',
  supportsInterleavedTextTool: false,
  hasReasoningMiddleware: false,
}

export const DEEPSEEK_LOOP_CONFIG: AgenticLoopConfig = {
  providerId: 'deepseek',
  terminationSignal: 'finish_reason_tool_calls',
  supportsInterleavedTextTool: false,
  hasReasoningMiddleware: true, // preserves <think> blocks via extractReasoningMiddleware
}

export const NVIDIA_LOOP_CONFIG: AgenticLoopConfig = {
  providerId: 'nvidia',
  terminationSignal: 'finish_reason_tool_calls',
  supportsInterleavedTextTool: false,
  hasReasoningMiddleware: false,
}

/** Map from providerId to loop config. */
export const LOOP_CONFIG_BY_PROVIDER: Record<string, AgenticLoopConfig> = {
  anthropic: ANTHROPIC_LOOP_CONFIG,
  google: GOOGLE_LOOP_CONFIG,
  openai: OPENAI_LOOP_CONFIG,
  deepseek: DEEPSEEK_LOOP_CONFIG,
  nvidia: NVIDIA_LOOP_CONFIG,
}

// ---------------------------------------------------------------------------
// Tool call + result shapes
// ---------------------------------------------------------------------------

export interface LoopToolCall {
  id: string
  name: string
  input: Record<string, unknown>
  /** Stream position — preserves interleaved ordering (E-S6). */
  streamPosition?: number
}

export interface LoopToolResult {
  id: string
  name: string
  /** Tool output as a string. Error messages go here too (E-S7). */
  output: string
  /** True if the tool execution failed; output is the error message. */
  isError: boolean
}

// ---------------------------------------------------------------------------
// Per-iteration telemetry (E-S9)
// ---------------------------------------------------------------------------

export interface LoopIterationTelemetry {
  iteration: number
  providerId: string
  conversationId?: string
  inputTokens: number
  outputTokens: number
  cacheReadTokens: number
  cacheCreationTokens: number
  reasoningTokens: number
  toolCallCount: number
  toolErrorCount: number
  terminationSignal: string | null
  /** ISO-8601 timestamp when the iteration completed. */
  completedAt: string
}

/**
 * Emit per-iteration telemetry to structured log.
 * Cloud Run log sink → BigQuery → Observatory ToolLoopMetricsTile (E-S9).
 */
export function emitLoopIterationTelemetry(record: LoopIterationTelemetry): void {
  console.log(
    JSON.stringify({
      marsys_event_type: 'tool_loop_iteration',
      ...record,
    }),
  )
}

// ---------------------------------------------------------------------------
// Core loop state
// ---------------------------------------------------------------------------

export interface AgenticLoopState {
  config: AgenticLoopConfig
  iterations: number
  totalInputTokens: number
  totalOutputTokens: number
  totalCacheReadTokens: number
  totalCacheCreationTokens: number
  totalReasoningTokens: number
  toolCallHistory: Array<{ iteration: number; toolCall: LoopToolCall; result: LoopToolResult }>
}

/**
 * Returns true if the given stop/finish reason indicates that the model
 * wants to make tool calls (i.e., the loop should continue).
 */
export function isToolUseSignal(
  reason: string | null | undefined,
  signal: ToolLoopTerminationSignal,
): boolean {
  if (!reason) return false
  switch (signal) {
    case 'stop_reason':
      // Anthropic: stop_reason === 'tool_use'
      return reason === 'tool_use'
    case 'finish_reason_function_calls':
      // Google: finish_reason may be 'FUNCTION_CALL' (SDK enum) or 'function_calls' (normalized)
      return reason === 'function_calls' || reason === 'FUNCTION_CALL'
    case 'finish_reason_tool_calls':
      // OpenAI / DeepSeek / NVIDIA: finish_reason === 'tool_calls'
      return reason === 'tool_calls'
    default:
      return false
  }
}

/**
 * Guards a tool executor: wraps it to catch errors and return an
 * isError=true LoopToolResult instead of throwing (E-S7).
 */
export async function safeExecuteTool(
  toolCall: LoopToolCall,
  executor: (tc: LoopToolCall) => Promise<string>,
): Promise<LoopToolResult> {
  try {
    const output = await executor(toolCall)
    return {
      id: toolCall.id,
      name: toolCall.name,
      output,
      isError: false,
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return {
      id: toolCall.id,
      name: toolCall.name,
      output: `Tool execution failed: ${message}`,
      isError: true,
    }
  }
}

/**
 * Creates a fresh AgenticLoopState.
 */
export function createLoopState(config: AgenticLoopConfig): AgenticLoopState {
  return {
    config,
    iterations: 0,
    totalInputTokens: 0,
    totalOutputTokens: 0,
    totalCacheReadTokens: 0,
    totalCacheCreationTokens: 0,
    totalReasoningTokens: 0,
    toolCallHistory: [],
  }
}

/**
 * Accumulates usage into the loop state.
 */
export function accumulateUsage(
  state: AgenticLoopState,
  usage: {
    inputTokens?: number
    outputTokens?: number
    cacheReadTokens?: number
    cacheCreationTokens?: number
    reasoningTokens?: number
  },
): void {
  state.totalInputTokens += usage.inputTokens ?? 0
  state.totalOutputTokens += usage.outputTokens ?? 0
  state.totalCacheReadTokens += usage.cacheReadTokens ?? 0
  state.totalCacheCreationTokens += usage.cacheCreationTokens ?? 0
  state.totalReasoningTokens += usage.reasoningTokens ?? 0
}

/**
 * Checks the iteration cap. Throws AgenticLoopCapExceeded if exceeded.
 */
export function checkIterationCap(state: AgenticLoopState): void {
  const cap = state.config.maxIterations ?? MAX_ITERATIONS
  if (state.iterations >= cap) {
    throw new AgenticLoopCapExceeded(state.iterations)
  }
}
