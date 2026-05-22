/**
 * nvidia/manifest.ts — NVIDIA NIM ProviderCapabilities declaration.
 * Validated against CAPABILITY_MATRIX.md §9 cells for the NVIDIA column.
 *
 * NVIDIA NIM is a model-hosting layer, not a single model. Capabilities depend
 * on the hosted model. The manifest reflects the common baseline supported by
 * the Marsys NIM stack (Llama 3.1/3.3, Mistral, etc.) as registered in the
 * model registry.
 *
 * Key NIM-specific notes:
 *   - No extended thinking (depends on hosted model; not enabled in Marsys NIM config)
 *   - Tool loop: OpenAI-compatible API endpoint
 *   - Vision: supported by some NIM models (llama3.2-vision) — inputImage=true
 *   - No server-side tools (web search, fetch, code execution)
 */

import type { ProviderCapabilities } from '../capabilities';
import { validateManifest } from '../manifest-validator';

export const NVIDIA_MANIFEST: ProviderCapabilities = validateManifest({
  // Cluster A — Foundation
  extendedThinking: null,               // Depends on hosted model; not enabled in Marsys NIM
  promptCaching: null,                  // Not supported (depends on hosted model)
  adaptiveToolLoop: 'finish_reason_tool_calls',  // OpenAI-compat
  interleavedThinkingTool: false,
  smoothStreaming: true,                // Marsys server adapter

  // Cluster B — Server-side tools (none in baseline NIM)
  webSearch: null,
  webFetch: null,
  codeExecution: null,

  // Cluster C — Memory
  nativeMemory: null,

  // Cluster D — Multi-modal input (llama3.2-vision supports images)
  inputImage: true,                    // Via llama3.2-vision hosted model
  inputAudio: false,
  inputVideo: false,
  inputPdf: null,

  // Cluster D — Multi-modal output (none)
  outputVoice: null,
  outputImage: null,

  // Cluster D — Computer use
  computerUse: null,

  // Cross-cutting
  structuredOutputs: null,             // Depends on hosted model
  maxContextTokens: 131_072,           // Llama 3.1 70B / 3.3 70B via NIM
});
