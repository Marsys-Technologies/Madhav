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
import { migrationAdapter } from '../migration-adapter';

export class AnthropicAdapter implements CapabilityAdapter {
  readonly providerId = 'anthropic';

  getManifest(): ProviderCapabilities {
    return ANTHROPIC_MANIFEST;
  }

  /**
   * Primary streaming chat — delegates to MigrationAdapter (A-S10).
   *
   * The migration adapter bridges the existing Anthropic pipeline into the
   * unified ChatEvent shape. R11.C will replace this with a direct
   * anthropic_observed.ts streaming call.
   */
  async *chat(request: ChatRequest): AsyncIterable<ChatEvent> {
    // A-S10: delegate to migration adapter stub.
    // R11.C wires in the actual anthropic_observed.ts stream.
    yield* migrationAdapter.stubChat(request, 'anthropic');
  }

  thinking(request: ThinkingRequest): ThinkingResponse {
    // R11.C — Adaptive Thinking Budget (Anthropic)
    // Anthropic API shape: { type: 'enabled', effort: 'low'|'medium'|'high' }
    // for Opus 4.6+ / Sonnet 4.6+ (effort-based API).
    // For older models: { type: 'enabled', budget_tokens: N }
    // Effort → budget_tokens fallback mapping (used if effort API unsupported):
    //   low → 1024, medium → 8192, high → 32768
    const effort = request.effort ?? 'medium';
    const effortToBudget: Record<string, number> = {
      low: 1024,
      medium: 8192,
      high: 32768,
    };
    return {
      mode: 'native_effort',
      effort,
      budgetTokens: request.budgetTokens ?? effortToBudget[effort],
      providerPayload: {
        // effort-based API (Opus 4.6+, Sonnet 4.6+)
        thinking: { type: 'enabled', effort },
        // budget_tokens fallback (legacy models)
        thinking_budget_fallback: { type: 'enabled', budget_tokens: request.budgetTokens ?? effortToBudget[effort] },
      },
    };
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
