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

  cache(request: CacheRequest): CacheResponse {
    // R11.D — Anthropic 4-breakpoint cache_control (NATIVE_RULINGS §4).
    //
    // Canonical breakpoint positions (0-indexed, relative to assembled message array):
    //   BP0: end-of-tools     — after the tool definitions block
    //   BP1: end-of-system    — at the end of the system prompt
    //   BP2: end-of-RAG       — after the last retrieval/bundle message
    //   BP3: last-turn        — at the last assistant turn in history
    //
    // The prompt_assembler.ts (D-S1) injects `cache_control: { type: 'ephemeral' }`
    // at these positions when this config is returned.
    //
    // 5-minute TTL (ephemeral). Cache hits reduce input tokens by ~90%.
    // Cost model: cache write = 1.25x base; cache read = 0.1x base.
    const defaultBreakpoints = [
      0,  // BP0: end-of-tools
      1,  // BP1: end-of-system
      2,  // BP2: end-of-RAG-bundle
      3,  // BP3: last-assistant-turn
    ];
    return {
      mode: 'explicit_4bp',
      breakpointPositions: request.breakpointPositions ?? defaultBreakpoints,
      providerPayload: {
        // Anthropic API shape injected by prompt_assembler at each breakpoint position
        cacheControl: { type: 'ephemeral' },
        ttlMinutes: 5,
        maxBreakpoints: 4,
      },
    };
  }

  tools(request: ToolsRequest): ToolsResponse {
    // R11.E — Anthropic stop_reason agentic loop (E-S1).
    //
    // Loop terminates when stop_reason === 'tool_use'.
    // 8-iteration cap enforced by agentic_loop.ts checkIterationCap().
    // Default false (MARSYS_FLAG_R11E_ANTHROPIC_LOOP) — HIGH risk.
    // When flag=false, route.ts uses single-shot pipeline.
    const maxIterations = request.maxIterations ?? 8;
    return {
      mode: 'stop_reason',
      maxIterations,
      tools: request.tools,
      providerPayload: {
        // Anthropic stop_reason signal that triggers next iteration
        terminationSignal: 'stop_reason',
        terminationValue: 'tool_use',
        // Per-iteration usage accumulation for Observatory (E-S9)
        trackPerIterationUsage: true,
        // Interleaved text+tool ordering supported by Claude 4.x (E-S6)
        supportsInterleavedTextTool: true,
      },
    };
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
