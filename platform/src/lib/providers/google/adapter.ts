/**
 * google/adapter.ts — Google (Gemini) CapabilityAdapter (R11.C real SDK wiring).
 *
 * Implements CapabilityAdapter for the Google/Gemini stack.
 * chat() uses streamText() + @ai-sdk/google with real streaming.
 * Supports thinking_delta events via 'reasoning' parts in the fullStream
 * (Gemini 2.5 extended thinking exposed via Vercel AI SDK reasoning-delta parts).
 * Other capability methods throw CapabilityUnsupportedError with phase pointers.
 *
 * Key Gemini-specific note: thinkingBudget is set via providerOptions.google.thinkingConfig.
 */

import { streamText, jsonSchema } from 'ai';
import { google as googleProvider } from '@ai-sdk/google';
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

export class GoogleAdapter implements CapabilityAdapter {
  readonly providerId = 'google';

  getManifest(): ProviderCapabilities {
    return GOOGLE_MANIFEST;
  }

  /**
   * Primary streaming chat — real implementation via Vercel AI SDK + @ai-sdk/google.
   * Streams text and thinking deltas from fullStream parts.
   * 'reasoning' parts map to thinking_delta (Gemini 2.5 extended thinking).
   * 'text-delta' parts map to text_delta.
   * 'finish' part emits usage + message_stop.
   */
  async *chat(request: ChatRequest): AsyncIterable<ChatEvent> {
    // Extract system instruction: explicit request.system takes priority,
    // then fall back to a system-role message in the messages array.
    const systemContent =
      request.system ??
      (request.messages.find((m) => m.role === 'system')?.content as string | undefined);

    // Filter out system messages — passed separately above.
    const conversationMessages = request.messages
      .filter((m) => m.role !== 'system')
      .map((m) => ({
        role: m.role as 'user' | 'assistant',
        content: m.content as string,
      }));

    // Build provider options — include thinkingConfig if set.
    // Gemini shape: providerOptions.google.thinkingConfig: { thinkingBudget: N }
    const thinkingConfig = request.thinkingConfig?.providerPayload?.['thinkingConfig'] as
      | Record<string, unknown>
      | undefined;
    const providerOptions = thinkingConfig
      ? { google: { thinkingConfig } }
      : undefined;

    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const streamParams: any = {
        model: googleProvider(request.model),
        messages: conversationMessages as Parameters<typeof streamText>[0]['messages'],
        maxOutputTokens: request.maxTokens ?? 8192,
      };
      if (systemContent) streamParams.system = systemContent;
      if (request.temperature !== undefined) streamParams.temperature = request.temperature;
      if (providerOptions) streamParams.providerOptions = providerOptions;
      // R11.F — B-S1: Forward tools to Gemini via Vercel AI SDK tool format.
      // Vercel AI SDK streamText accepts tools as Record<string, Tool> where each entry
      // has { description, inputSchema: jsonSchema(...) }. Gemini receives these as
      // functionDeclarations. Without this forwarding, Gemini never sees the tool
      // definitions and cannot emit tool-call parts (Break B2-G).
      if (request.tools && request.tools.length > 0) {
        streamParams.tools = Object.fromEntries(
          request.tools.map((tool) => [
            tool.name,
            {
              description: tool.description ?? '',
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              inputSchema: jsonSchema(tool.inputSchema as any),
            },
          ]),
        );
      }
      // R11.F — S4: Inject cachedContent name if provided via cacheConfig (D.3 wiring).
      // When route.ts creates a Gemini cachedContent object, it passes the returned
      // resource name through cacheConfig.providerPayload.cachedContentName so the
      // adapter can reference it in the streamText call.
      const cachedContentName = request.cacheConfig?.providerPayload?.['cachedContentName'] as string | undefined;
      if (cachedContentName) {
        streamParams.providerOptions = {
          ...streamParams.providerOptions,
          google: {
            ...(streamParams.providerOptions?.google ?? {}),
            cachedContent: cachedContentName,
          },
        };
      }
      const result = streamText(streamParams);

      for await (const part of result.fullStream) {
        if (part.type === 'text-delta') {
          yield { type: 'text_delta', text: part.text };
        } else if (part.type === 'reasoning-delta') {
          // Extended thinking — Vercel AI SDK surfaces Gemini thought parts as 'reasoning-delta'
          yield { type: 'thinking_delta', thinking: (part as unknown as { text: string }).text };
        } else if (part.type === 'tool-call') {
          // Gemini emits complete tool calls (no streaming deltas).
          // Synthesize the streaming protocol: start → full-JSON delta → complete.
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const tc = part as any;
          const id: string = tc.toolCallId;
          const name: string = tc.toolName;
          const args = tc.args as Record<string, unknown>;
          const argsJson = JSON.stringify(args);
          yield { type: 'tool_use_start', id, name };
          yield { type: 'tool_use_input_delta', id, partialJson: argsJson };
          yield { type: 'tool_use_complete', id, name, input: args };
        } else if (part.type === 'finish') {
          yield {
            type: 'usage',
            inputTokens: part.totalUsage.inputTokens ?? 0,
            outputTokens: part.totalUsage.outputTokens ?? 0,
          };
          // Map Vercel AI SDK 'tool-calls' finishReason to Google canonical 'function_calls'
          // so isToolUseSignal() with 'finish_reason_function_calls' config recognises it.
          const stopReason =
            part.finishReason === 'tool-calls' ? 'function_calls' : (part.finishReason ?? 'end_turn');
          yield {
            type: 'message_stop',
            stopReason,
          };
        } else if (part.type === 'error') {
          const errMsg = part.error instanceof Error ? part.error.message : String(part.error);
          yield { type: 'error', error: errMsg };
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      yield { type: 'error', error: message };
    }
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
