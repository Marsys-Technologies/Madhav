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

  thinking(request: ThinkingRequest): ThinkingResponse {
    // R11.C — Gemini thinkingBudget (integer 0–24576 in generation config).
    // Gemini 2.5 Pro uses thinkingConfig: { thinkingBudget: N } in generation config.
    // Default: 24576 (preserved from registry.ts — DO NOT CHANGE default).
    // Effort → budgetTokens mapping for adaptive budgets:
    //   low → 8192, medium → 24576 (default), high → 32768 (Gemini 2.5 Pro max)
    const GEMINI_DEFAULT_BUDGET = 24576;
    const effortToBudget: Record<string, number> = {
      low: 8192,
      medium: GEMINI_DEFAULT_BUDGET,
      high: 32768,
    };
    const effort = request.effort ?? 'medium';
    const budget = request.budgetTokens ?? effortToBudget[effort];
    return {
      mode: 'native_budget',
      effort,
      budgetTokens: budget,
      providerPayload: {
        // Gemini 2.5 generation config shape
        thinkingConfig: { thinkingBudget: budget },
      },
    };
  }

  cache(request: CacheRequest): CacheResponse {
    // R11.D — Google cachedContent API (D-S2).
    //
    // Gemini caching uses a separate cachedContent object creation step:
    //   1. POST /v1beta/cachedContents with { systemInstruction, contents, ttl }
    //   2. Reference the returned `name` in subsequent generateContent calls
    //      via { cachedContent: "cachedContents/abc123" }
    //
    // MARSYS canonical cache content: synthesis system prompt + RAG bundle.
    // TTL: 600s (10 min) — longer than Anthropic's 5-min to absorb slow-cadence
    // multi-turn sessions.
    //
    // Minimum cache size: ≥32,768 tokens (Gemini API requirement).
    // The R11.D route layer must check this before calling caches.create().
    //
    // cachedContentTokenCount flows to Observatory via extractGeminiCacheMetrics().
    return {
      mode: 'cached_content_api',
      breakpointPositions: request.breakpointPositions ?? [],
      providerPayload: {
        // TTL in seconds
        ttlSeconds: 600,
        // Minimum token threshold for cache creation
        minTokensForCache: 32768,
        // Display name for audit trail
        displayName: 'marsys-synthesis-cache',
        // Cache scope: system prompt + RAG bundle (static-within-session content)
        cacheScope: ['systemInstruction', 'ragBundle'],
        // SDK call reference
        sdkMethod: 'genai.caches.create',
        // Usage field in response: usageMetadata.cachedContentTokenCount
        usageField: 'cachedContentTokenCount',
      },
    };
  }

  tools(request: ToolsRequest): ToolsResponse {
    // R11.E — Gemini finish_reason=function_calls agentic loop (E-S2).
    //
    // Gemini terminates a tool-use turn with finish_reason === 'FUNCTION_CALL'
    // (SDK enum value) which normalizes to 'function_calls' in our unified layer.
    // The loop reuses agentic_loop.ts engine with GOOGLE_LOOP_CONFIG.
    //
    // Function call format: functionCalls[] array in the response candidate.
    // Interleaved text+tool ordering is preserved by Gemini 2.5 Pro.
    const maxIterations = request.maxIterations ?? 8;
    return {
      mode: 'finish_reason_function_calls',
      maxIterations,
      tools: request.tools,
      providerPayload: {
        // Google SDK finish_reason signals for tool-use (loop continues while this is observed)
        terminationSignal: 'finish_reason_function_calls',
        terminationValues: ['FUNCTION_CALL', 'function_calls'],
        // Tool declaration format for Gemini: functionDeclarations array in tools[]
        toolFormat: 'functionDeclarations',
        // Interleaved text+tool supported by Gemini 2.5 Pro (E-S6)
        supportsInterleavedTextTool: true,
      },
    };
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
