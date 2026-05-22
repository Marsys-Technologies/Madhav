/**
 * openai/manifest.ts — OpenAI (GPT) ProviderCapabilities declaration.
 * Validated against CAPABILITY_MATRIX.md §9 cells for the OpenAI column.
 *
 * Note: o-series reasoning models have been retired from the Marsys registry
 * (BHISMA Wave 2). The manifest reflects gpt-4.1 / GPT family capabilities.
 * extendedThinking = 'polyfill_cot' (chain-of-thought nudge in system prompt).
 */

import type { ProviderCapabilities } from '../capabilities';
import { validateManifest } from '../manifest-validator';

export const OPENAI_MANIFEST: ProviderCapabilities = validateManifest({
  // Cluster A — Foundation
  extendedThinking: 'polyfill_cot',      // System-prompt "think step by step" nudge
  promptCaching: 'automatic',            // Automatic (default on, 25% hit cost)
  adaptiveToolLoop: 'finish_reason_tool_calls',  // while (finish_reason === 'tool_calls')
  interleavedThinkingTool: false,        // GPT-4.1: no interleaved thinking + tool use
  smoothStreaming: true,                 // Marsys server adapter

  // Cluster B — Server-side tools
  webSearch: 'preview_api',             // web_search_preview tool (Responses API)
  webFetch: null,                        // No first-party web_fetch; polyfill in R11.F
  codeExecution: 'first_party',         // Code Interpreter (sandboxed Python + file I/O)

  // Cluster C — Memory
  nativeMemory: 'product_only',         // ChatGPT Memory feature — not API-native

  // Cluster D — Multi-modal input
  inputImage: true,                     // Native vision (GPT-4o, GPT-4.1)
  inputAudio: true,                     // Audio Preview models
  inputVideo: false,                    // Partial (frames only); not enabled in Marsys
  inputPdf: 'files_api',              // Files endpoint

  // Cluster D — Multi-modal output
  outputVoice: 'tts_streaming',        // Audio Preview / TTS streaming
  outputImage: 'gpt_image',           // gpt-image-1

  // Cluster D — Computer use
  computerUse: 'cua_responses',        // Computer Use Agent via Responses API

  // Cross-cutting
  structuredOutputs: 'json_schema_strict',  // response_format: { type: 'json_schema', strict: true }
  maxContextTokens: 200_000,               // GPT-4.1
});
