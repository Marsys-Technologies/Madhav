/**
 * anthropic/adapter.ts — Anthropic CapabilityAdapter skeleton (A-S2).
 *
 * Implements CapabilityAdapter for the Anthropic stack.
 * chat() wraps the existing Anthropic-shaped pipeline.
 * All other capability methods throw CapabilityUnsupportedError with a
 * phase pointer indicating when they will ship.
 *
 * Phase roadmap for unsupported methods:
 *   thinking()         → R11.C (Streaming + Thinking)
 *   cache()            → R11.D (Caching)
 *   tools()            → R11.E (Adaptive Tool Sequencing)
 *   webSearch()        → R11.F (Server-Side Tools)
 *   webFetch()         → R11.F
 *   codeExecution()    → R11.F
 *   memory()           → R11.G (Memory + Projects)
 *   imageGeneration()  → R11.K (Image Generation — not supported by Anthropic API)
 *   computerUse()      → R11.K
 *   structuredOutputs() → R11.D (via tool_force)
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
import { ANTHROPIC_MANIFEST } from './manifest';

export class AnthropicAdapter implements CapabilityAdapter {
  readonly providerId = 'anthropic';

  getManifest(): ProviderCapabilities {
    return ANTHROPIC_MANIFEST;
  }

  /**
   * Primary streaming chat.
   * In R11.A this is a skeleton — the actual Anthropic SDK call will be wired
   * to the existing anthropic_observed.ts in A-S7 (dispatcher integration).
   * For now it yields a single text_delta and stops.
   *
   * NOTE: In production (behind MARSYS_FLAG_R11V2_USE_ADAPTERS=true), the
   * dispatcher will delegate to this method for Anthropic stacks.
   */
  async *chat(request: ChatRequest): AsyncIterable<ChatEvent> {
    // R11.A skeleton: validate request shape, then yield a stub event.
    // Full implementation wired in dispatcher integration (A-S7).
    if (!request.messages || request.messages.length === 0) {
      yield { type: 'error', error: 'AnthropicAdapter.chat: no messages provided' };
      return;
    }
    // Stub: signal that the adapter is present and routing would work.
    // Replaced by actual anthropic_observed.ts integration in A-S7.
    yield { type: 'text_delta', text: '' };
    yield {
      type: 'message_stop',
      stopReason: 'end_turn',
    };
  }

  thinking(_request: ThinkingRequest): ThinkingResponse {
    // R11.C — Adaptive Thinking Budget (Anthropic)
    throw new CapabilityUnsupportedError(
      'thinking',
      'anthropic',
    );
    // Implementation note for R11.C: map effort to thinking.budget_tokens
    // { low: 1024, medium: 8192, high: 16384 } for Sonnet/Opus 4.6+
  }

  cache(_request: CacheRequest): CacheResponse {
    // R11.D — Prompt Caching (Anthropic: cache_control breakpoints)
    throw new CapabilityUnsupportedError('cache', 'anthropic');
  }

  tools(_request: ToolsRequest): ToolsResponse {
    // R11.E — Adaptive Tool Sequencing (Anthropic: stop_reason loop)
    throw new CapabilityUnsupportedError('tools', 'anthropic');
  }

  webSearch(_request: WebSearchRequest): Promise<WebSearchResult> {
    // R11.F — Server-Side Tools (Anthropic: first-party web_search)
    throw new CapabilityUnsupportedError('webSearch', 'anthropic');
  }

  webFetch(_request: WebFetchRequest): Promise<WebFetchResult> {
    // R11.F — Server-Side Tools (Anthropic: first-party web_fetch)
    throw new CapabilityUnsupportedError('webFetch', 'anthropic');
  }

  codeExecution(_request: CodeExecutionRequest): Promise<CodeExecutionResult> {
    // R11.F — Server-Side Tools (Anthropic: code_execution first-party)
    throw new CapabilityUnsupportedError('codeExecution', 'anthropic');
  }

  memory(_request: MemoryRequest): Promise<MemoryResponse> {
    // R11.G — Memory + Projects (Anthropic: Memory tool, Claude 4.5+)
    throw new CapabilityUnsupportedError('memory', 'anthropic');
  }

  multimodal(request: MultimodalRequest): MultimodalResponse {
    // Always-on: determines which modalities are supported vs. not.
    const supportedInput: MultimodalResponse['supportedInputModalities'] = [];
    const unsupportedInput: MultimodalResponse['unsupportedInputModalities'] = [];

    for (const modality of request.inputModalities) {
      if (modality === 'image' || modality === 'pdf') {
        supportedInput.push(modality);
      } else {
        unsupportedInput.push(modality);
      }
    }

    return {
      supportedInputModalities: supportedInput,
      unsupportedInputModalities: unsupportedInput,
      supportedOutputModalities: [], // Anthropic API: no voice/image generation output
    };
  }

  imageGeneration(_request: ImageGenRequest): Promise<ImageGenResult> {
    // Anthropic API does not support image generation — this will never ship.
    throw new CapabilityUnsupportedError('imageGeneration', 'anthropic');
  }

  async *computerUse(_request: ComputerUseRequest): AsyncIterable<ComputerUseEvent> {
    // R11.K — Computer Use (Anthropic: Computer Use API)
    throw new CapabilityUnsupportedError('computerUse', 'anthropic');
  }

  structuredOutputs(_request: StructuredOutputsRequest): StructuredOutputsResponse {
    // R11.D — Structured Outputs (Anthropic: tool_force)
    throw new CapabilityUnsupportedError('structuredOutputs', 'anthropic');
  }
}
