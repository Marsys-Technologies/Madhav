/**
 * deepseek/adapter.ts — DeepSeek CapabilityAdapter skeleton (A-S5).
 *
 * Implements CapabilityAdapter for the DeepSeek stack.
 * Key DeepSeek-specific note: the AI SDK's extractReasoningMiddleware is used
 * to parse inline <think>...</think> blocks from the response stream, converting
 * them to reasoning_content that maps to our 'thinking_delta' ChatEvent type.
 *
 * This middleware call will be wired in A-S7 (dispatcher) when USE_ADAPTERS=true.
 */

import { streamText } from 'ai';
import { createDeepSeek } from '@ai-sdk/deepseek';
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
import { DEEPSEEK_MANIFEST } from './manifest';

export class DeepSeekAdapter implements CapabilityAdapter {
  readonly providerId = 'deepseek';

  getManifest(): ProviderCapabilities {
    return DEEPSEEK_MANIFEST;
  }

  /**
   * Primary streaming chat — real DeepSeek implementation via @ai-sdk/deepseek.
   *
   * DeepSeek R1 emits reasoning via `reasoning-delta` stream parts (AI SDK
   * extracts reasoning_content from the OpenAI-compat delta automatically).
   * Surfaced as ChatEvent { type: 'thinking_delta' }.
   *
   * Cache telemetry: prompt_cache_hit_tokens from usage maps to cacheReadTokens.
   */
  async *chat(request: ChatRequest): AsyncIterable<ChatEvent> {
    try {
      const deepseek = createDeepSeek({
        apiKey: process.env.DEEPSEEK_API_KEY ?? '',
        baseURL: 'https://api.deepseek.com/v1',
      });

      // Extract system prompt — explicit request.system takes priority,
      // then fall back to first system-role message.
      const systemPrompt: string | undefined =
        request.system ??
        (request.messages.find((m) => m.role === 'system')?.content as string | undefined);

      // Build messages for AI SDK — filter out system messages (passed separately)
      const messages = request.messages
        .filter((m) => m.role !== 'system')
        .map((m) => ({
          role: m.role as 'user' | 'assistant',
          content: typeof m.content === 'string' ? m.content : JSON.stringify(m.content),
        }));

      const result = streamText({
        model: deepseek(request.model),
        ...(systemPrompt ? { system: systemPrompt } : {}),
        messages,
        maxOutputTokens: request.maxTokens ?? 8192,
        ...(request.temperature !== undefined ? { temperature: request.temperature } : {}),
      });

      for await (const part of result.fullStream) {
        if (part.type === 'text-delta') {
          yield { type: 'text_delta', text: part.text };
        } else if (part.type === 'reasoning-delta') {
          // DeepSeek R1 reasoning_content surfaced by AI SDK as reasoning-delta
          yield { type: 'thinking_delta', thinking: part.text };
        } else if (part.type === 'finish') {
          // Emit usage before stop — AI SDK exposes totalUsage on finish
          const usage = part.totalUsage;
          yield {
            type: 'usage',
            inputTokens: usage.inputTokens ?? 0,
            outputTokens: usage.outputTokens ?? 0,
            // cacheReadTokens surfaced from inputTokenDetails when available
            cacheReadTokens: usage.inputTokenDetails?.cacheReadTokens ?? 0,
          };
          yield {
            type: 'message_stop',
            stopReason: part.finishReason ?? 'end_turn',
          };
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      yield { type: 'error', error: message };
    }
  }

  thinking(_request: ThinkingRequest): ThinkingResponse {
    // R11.C — DeepSeek: inline_blocks mode.
    // DeepSeek R1 uses <think>...</think> blocks extracted by extractReasoningMiddleware
    // from the AI SDK. The "thinking toggle" is simply enabling extractReasoningMiddleware
    // on the stream; there is no dedicated thinking API parameter.
    //
    // The existing <think> extraction (middleware) is preserved and unchanged per brief.
    // This method just signals to the synthesis layer that inline_blocks mode is active.
    return {
      mode: 'inline_blocks',
      effort: _request.effort ?? 'medium',
      providerPayload: {
        // Signal to synthesis: use extractReasoningMiddleware
        extractReasoningMiddleware: true,
        // DeepSeek has no budget_tokens concept; effort is advisory only.
      },
    };
  }

  cache(_request: CacheRequest): CacheResponse {
    // R11.D — DeepSeek implicit cache telemetry (D-S4).
    //
    // DeepSeek caches implicitly — no API markers, no cachedContent creation.
    // The `prompt_cache_hit_tokens` field appears in the usage response when
    // tokens were served from cache. Capture and forward to Observatory.
    //
    // DeepSeek usage response shape:
    //   { prompt_tokens, completion_tokens, prompt_cache_hit_tokens, prompt_cache_miss_tokens }
    //
    // Cost model (DeepSeek V3, 2024):
    //   cache hit:  0.014 USD / 1M tokens (vs. 0.27 USD / 1M for cache miss)
    //   ~19.3x cheaper on cache hits
    //
    // No request modifications needed — DeepSeek auto-determines cache eligibility.
    return {
      mode: 'implicit',
      breakpointPositions: [],  // no explicit positions
      providerPayload: {
        // Usage field: prompt_cache_hit_tokens
        prompt_cache_hit_tokens: 'usage.prompt_cache_hit_tokens',
        // Also available: prompt_cache_miss_tokens
        prompt_cache_miss_tokens: 'usage.prompt_cache_miss_tokens',
        // Cost ratio for cache hits vs. standard input tokens
        cachedTokenCostFraction: 0.014 / 0.27,  // ~0.052
      },
    };
  }

  tools(request: ToolsRequest): ToolsResponse {
    // R11.E — DeepSeek OpenAI-compat tool loop with reasoning preservation (E-S4).
    //
    // DeepSeek V3 uses OpenAI-compatible function calling.
    // finish_reason === 'tool_calls' signals that tool execution is needed.
    //
    // CRITICAL: extractReasoningMiddleware from the AI SDK is preserved throughout
    // loop iterations. The middleware extracts <think>...</think> blocks from the
    // raw stream and converts them to reasoning_content → ChatEvent 'thinking_delta'.
    // The loop engine must ensure the middleware wraps each iteration's stream,
    // not just the first call.
    //
    // DeepSeek uses OpenAI-compat function calling format (tools[].function).
    const maxIterations = request.maxIterations ?? 8;
    return {
      mode: 'finish_reason_tool_calls',
      maxIterations,
      tools: request.tools,
      providerPayload: {
        terminationSignal: 'finish_reason_tool_calls',
        terminationValue: 'tool_calls',
        // Preserve <think> extraction across all loop iterations
        extractReasoningMiddleware: true,
        // No interleaved text+tool in DeepSeek (OpenAI-compat format)
        supportsInterleavedTextTool: false,
      },
    };
  }

  webSearch(_request: WebSearchRequest): Promise<WebSearchResult> {
    // DeepSeek V3 does not support server-side web search
    throw new CapabilityUnsupportedError('webSearch', 'deepseek');
  }

  webFetch(_request: WebFetchRequest): Promise<WebFetchResult> {
    throw new CapabilityUnsupportedError('webFetch', 'deepseek');
  }

  codeExecution(_request: CodeExecutionRequest): Promise<CodeExecutionResult> {
    throw new CapabilityUnsupportedError('codeExecution', 'deepseek');
  }

  memory(_request: MemoryRequest): Promise<MemoryResponse> {
    throw new CapabilityUnsupportedError('memory', 'deepseek');
  }

  multimodal(request: MultimodalRequest): MultimodalResponse {
    // DeepSeek V3: text-only; all input modalities are unsupported
    const unsupported = [...request.inputModalities] as MultimodalResponse['unsupportedInputModalities'];
    return {
      supportedInputModalities: [],
      unsupportedInputModalities: unsupported,
      supportedOutputModalities: [],
    };
  }

  imageGeneration(_request: ImageGenRequest): Promise<ImageGenResult> {
    throw new CapabilityUnsupportedError('imageGeneration', 'deepseek');
  }

  async *computerUse(_request: ComputerUseRequest): AsyncIterable<ComputerUseEvent> {
    throw new CapabilityUnsupportedError('computerUse', 'deepseek');
  }

  structuredOutputs(_request: StructuredOutputsRequest): StructuredOutputsResponse {
    throw new CapabilityUnsupportedError('structuredOutputs', 'deepseek');
  }
}
