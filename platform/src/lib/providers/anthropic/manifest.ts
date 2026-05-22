/**
 * anthropic/manifest.ts — Anthropic ProviderCapabilities declaration.
 *
 * Validated against CAPABILITY_MATRIX.md §9 cells for the Anthropic column.
 * Validated at module load via validateManifest().
 *
 * Capabilities shipped in this manifest but not yet wired in chat surface:
 *   - promptCaching='explicit_4bp'  → R11.D
 *   - extendedThinking='native_effort' → R11.C
 *   - webSearch/webFetch/codeExecution → R11.F
 *   - nativeMemory='memory_tool' → R11.G
 *   - computerUse='computer_use_api' → R11.K
 */

import type { ProviderCapabilities } from '../capabilities';
import { validateManifest } from '../manifest-validator';

export const ANTHROPIC_MANIFEST: ProviderCapabilities = validateManifest({
  // Cluster A — Foundation
  extendedThinking: 'native_effort',   // Opus 4.6+ / Sonnet 4.6+ — thinking.effort API
  promptCaching: 'explicit_4bp',       // Up to 4 cache_control breakpoints; 5-min/1-hour TTL
  adaptiveToolLoop: 'stop_reason',     // while (stop_reason === 'tool_use')
  interleavedThinkingTool: true,       // Claude 4.x interleaved thinking + tool use
  smoothStreaming: true,               // Always via Marsys server adapter

  // Cluster B — Server-side tools
  webSearch: 'first_party',           // web_search tool → web_search_tool_result content blocks
  webFetch: 'first_party',            // web_fetch first-party tool
  codeExecution: 'first_party',       // code_execution tool (sandboxed Python, charts, file I/O)

  // Cluster C — Memory
  nativeMemory: 'memory_tool',        // Memory tool (Claude 4.5+); API-accessible

  // Cluster D — Multi-modal input
  inputImage: true,                   // Vision (Claude 3.5+)
  inputAudio: false,                  // Not supported on Anthropic API
  inputVideo: false,                  // Not supported on Anthropic API
  inputPdf: 'files_api_inline',       // Files API + inline in message content

  // Cluster D — Multi-modal output
  outputVoice: null,                  // Not supported on Anthropic API
  outputImage: null,                  // Not supported on Anthropic API

  // Cluster D — Computer use
  computerUse: 'computer_use_api',    // Computer Use API (Claude 3.5 Sonnet+)

  // Cross-cutting
  structuredOutputs: 'tool_force',    // JSON output via tool_use forcing (no native json_schema)
  maxContextTokens: 1_000_000,        // Sonnet 4.6 / Opus 4.7 Enterprise
});
