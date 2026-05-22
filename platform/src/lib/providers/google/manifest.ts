/**
 * google/manifest.ts — Google (Gemini) ProviderCapabilities declaration.
 * Validated against CAPABILITY_MATRIX.md §9 cells for the Google column.
 */

import type { ProviderCapabilities } from '../capabilities';
import { validateManifest } from '../manifest-validator';

export const GOOGLE_MANIFEST: ProviderCapabilities = validateManifest({
  // Cluster A — Foundation
  extendedThinking: 'native_budget',    // Gemini 2.5 Pro: thinkingBudget integer parameter
  promptCaching: 'cached_content_api',  // Separate cachedContent API call; TTL configurable
  adaptiveToolLoop: 'finish_reason_function_calls',  // while (finish_reason === 'function_calls')
  interleavedThinkingTool: true,        // Gemini 2.5 interleaved thinking during tool use
  smoothStreaming: true,                // Marsys server adapter

  // Cluster B — Server-side tools
  webSearch: 'grounding',              // Google Search grounding via tools: [{ google_search: {} }]
  webFetch: null,                      // No first-party web_fetch; use function calling + fetcher
  codeExecution: 'first_party',        // Code Execution built-in (sandboxed Python)

  // Cluster C — Memory
  nativeMemory: 'workspace',           // Workspace context binding

  // Cluster D — Multi-modal input
  inputImage: true,                    // Native vision
  inputAudio: true,                    // Native (Gemini Live + Gemini 2.5)
  inputVideo: true,                    // Native (Gemini 2.5)
  inputPdf: 'files_api',              // Files API

  // Cluster D — Multi-modal output
  outputVoice: 'live_api',            // Gemini Live real-time TTS
  outputImage: 'imagen',              // Imagen via API

  // Cluster D — Computer use
  computerUse: null,                  // Not supported on Google API

  // Cross-cutting
  structuredOutputs: 'response_schema', // responseSchema in generation config
  maxContextTokens: 2_000_000,          // Gemini 2.5 Pro
});
