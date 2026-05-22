/**
 * google/adapter.ts — Google (Gemini) CapabilityAdapter skeleton (A-S3).
 *
 * Implements CapabilityAdapter for the Google/Gemini stack.
 * chat() provides a skeleton that will be wired to the Gemini AI SDK in A-S7.
 * Other capability methods throw CapabilityUnsupportedError with phase pointers.
 *
 * Key Gemini-specific note: thinkingBudget is set via the generation config
 * `thinkingConfig: { thinkingBudget: N }` — the adapter will handle this in R11.C.
 */

import type { CapabilityAdapter } from '../adapter';
import { CapabilityUnsupportedError } from '../adapter';
import type { ProviderCapabilities } from '../capabilities';
import type {
  ChatRequest,
  ChatEvent,
  ThinkingRequest,
  ThinkingResponse,
  CacheRequest,
  CacheResponse,
  ToolsRequest,
  ToolsResponse,
  WebSearchRequest,
  WebSearchResult,
  WebFetchRequest,
  WebFetchResult,
  CodeExecutionRequest,
  CodeExecutionResult,
  MemoryRequest,
  MemoryResponse,
  MultimodalRequest,
  MultimodalResponse,
  ImageGenRequest,
  ImageGenResult,
  ComputerUseRequest,
  ComputerUseEvent,
  StructuredOutputsRequest,
  StructuredOutputsResponse,
} from '../types';
import { GOOGLE_MANIFEST } from './manifest';
import { migrationAdapter } from '../migration-adapter';

export class GoogleAdapter implements CapabilityAdapter {
  readonly providerId = 'google';

  getManifest(): ProviderCapabilities {
    return GOOGLE_MANIFEST;
  }

  /**
   * Primary streaming chat — delegates to MigrationAdapter (A-S10).
   * R11.C will wire in the actual Gemini SDK stream.
   */
  async *chat(request: ChatRequest): AsyncIterable<ChatEvent> {
    yield* migrationAdapter.stubChat(request, 'google');
  }

  thinking(_request: ThinkingRequest): ThinkingResponse {
    // R11.C — Gemini thinkingBudget (integer 0–24576 in generation config)
    throw new CapabilityUnsupportedError('thinking', 'google');
  }

  cache(_request: CacheRequest): CacheResponse {
    // R11.D — Google cachedContent API (separate creation step)
    throw new CapabilityUnsupportedError('cache', 'google');
  }

  tools(_request: ToolsRequest): ToolsResponse {
    // R11.E — Gemini finish_reason=function_calls loop
    throw new CapabilityUnsupportedError('tools', 'google');
  }

  webSearch(_request: WebSearchRequest): Promise<WebSearchResult> {
    // R11.F — Google Search grounding (tools: [{ google_search: {} }])
    throw new CapabilityUnsupportedError('webSearch', 'google');
  }

  webFetch(_request: WebFetchRequest): Promise<WebFetchResult> {
    // Google does not support first-party web_fetch; polyfill in R11.F
    throw new CapabilityUnsupportedError('webFetch', 'google');
  }

  codeExecution(_request: CodeExecutionRequest): Promise<CodeExecutionResult> {
    // R11.F — Google Code Execution built-in
    throw new CapabilityUnsupportedError('codeExecution', 'google');
  }

  memory(_request: MemoryRequest): Promise<MemoryResponse> {
    // R11.G — Google Workspace context binding
    throw new CapabilityUnsupportedError('memory', 'google');
  }

  multimodal(request: MultimodalRequest): MultimodalResponse {
    // Gemini 2.5: image, audio, video, pdf all supported
    const supported: MultimodalResponse['supportedInputModalities'] = [];
    const unsupported: MultimodalResponse['unsupportedInputModalities'] = [];
    for (const m of request.inputModalities) {
      // All 4 modalities supported on Gemini 2.5
      supported.push(m);
    }
    return {
      supportedInputModalities: supported,
      unsupportedInputModalities: unsupported,
      supportedOutputModalities:
        (request.outputModalities ?? []).filter(
          (m): m is 'voice' | 'image' => m === 'voice' || m === 'image',
        ),
    };
  }

  imageGeneration(_request: ImageGenRequest): Promise<ImageGenResult> {
    // R11.K — Google Imagen via API
    throw new CapabilityUnsupportedError('imageGeneration', 'google');
  }

  async *computerUse(_request: ComputerUseRequest): AsyncIterable<ComputerUseEvent> {
    // Google does not support Computer Use API
    throw new CapabilityUnsupportedError('computerUse', 'google');
  }

  structuredOutputs(_request: StructuredOutputsRequest): StructuredOutputsResponse {
    // R11.D — Google responseSchema
    throw new CapabilityUnsupportedError('structuredOutputs', 'google');
  }
}
