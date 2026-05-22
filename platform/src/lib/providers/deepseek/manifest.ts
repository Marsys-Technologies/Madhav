/**
 * deepseek/manifest.ts — DeepSeek ProviderCapabilities declaration.
 * Validated against CAPABILITY_MATRIX.md §9 cells for the DeepSeek column.
 *
 * Key DeepSeek-specific notes:
 *   - Extended thinking: inline <think>...</think> blocks extracted via
 *     extractReasoningMiddleware from AI SDK
 *   - Prompt caching: implicit (prompt_cache_hit_tokens in usage response)
 *   - Tool loop: OpenAI-compatible (finish_reason=tool_calls)
 *   - No server-side tools (web search, fetch, code execution)
 *   - No vision support (as of DeepSeek V3)
 */

import type { ProviderCapabilities } from '../capabilities';
import { validateManifest } from '../manifest-validator';

export const DEEPSEEK_MANIFEST: ProviderCapabilities = validateManifest({
  // Cluster A — Foundation
  extendedThinking: 'inline_blocks',    // <think>...</think> blocks via extractReasoningMiddleware
  promptCaching: 'implicit',            // prompt_cache_hit_tokens reported in usage
  adaptiveToolLoop: 'finish_reason_tool_calls',  // OpenAI-compatible
  interleavedThinkingTool: false,       // DeepSeek: no interleaved thinking + tool use
  smoothStreaming: true,                // Marsys server adapter

  // Cluster B — Server-side tools (all null — DeepSeek V3 has no server-side tools)
  webSearch: null,
  webFetch: null,
  codeExecution: null,

  // Cluster C — Memory
  nativeMemory: null,                   // No native memory support

  // Cluster D — Multi-modal input (DeepSeek V3: text only)
  inputImage: false,
  inputAudio: false,
  inputVideo: false,
  inputPdf: null,

  // Cluster D — Multi-modal output (none)
  outputVoice: null,
  outputImage: null,

  // Cluster D — Computer use
  computerUse: null,

  // Cross-cutting
  structuredOutputs: null,             // OpenAI-compat partial; not fully structured
  maxContextTokens: 128_000,           // DeepSeek V3
});
