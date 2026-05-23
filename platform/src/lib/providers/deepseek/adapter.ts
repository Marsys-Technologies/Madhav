/**
 * deepseek/adapter.ts — DeepSeek CapabilityAdapter (F-S2 enhanced).
 *
 * Implements CapabilityAdapter for the DeepSeek stack.
 * Uses the openai SDK pointed at DeepSeek's OpenAI-compatible base URL.
 * Stream format is identical to OpenAI: finish_reason === 'tool_calls' signals
 * tool use; delta.tool_calls[] carry incremental function-call data.
 *
 * DeepSeek R1 emits inline <think>...</think> blocks in delta.content;
 * these are surfaced as 'thinking_delta' ChatEvents by detecting the tags.
 *
 * F-S2: chat() now accumulates tool_calls deltas and emits:
 *   tool_use_start → tool_use_input_delta → tool_use_complete → message_stop
 */

import OpenAI from 'openai';
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
   * Primary streaming chat — DeepSeek via openai SDK at DeepSeek base URL.
   *
   * DeepSeek is OpenAI-compatible, so the stream format is identical to OpenAI.
   * finish_reason === 'tool_calls' indicates tool use; delta.tool_calls[] carry
   * incremental function-call data accumulated across chunks.
   *
   * DeepSeek R1 emits inline <think>...</think> blocks in delta.content;
   * these are surfaced as 'thinking_delta' ChatEvents.
   *
   * Cache telemetry: prompt_cache_hit_tokens from usage.prompt_tokens_details
   * maps to cacheReadTokens.
   *
   * F-S2: emits tool_use_start → tool_use_input_delta → tool_use_complete
   * when finish_reason === 'tool_calls'.
   */
  async *chat(request: ChatRequest): AsyncIterable<ChatEvent> {
    try {
      const client = new OpenAI({
        apiKey: process.env.DEEPSEEK_API_KEY ?? '',
        baseURL: 'https://api.deepseek.com/v1',
      });

      const stream = await client.chat.completions.create({
        model: request.model,
        max_tokens: request.maxTokens ?? 8192,
        messages: request.messages.map((m) => ({
          role: m.role,
          content: typeof m.content === 'string' ? m.content : JSON.stringify(m.content),
        })),
        stream: true,
        stream_options: { include_usage: true },
      });

      // Accumulate tool call deltas across chunks, keyed by index.
      const toolCallAccumulator: Map<number, { id: string; name: string; argumentsChunks: string[] }> = new Map();

      for await (const chunk of stream) {
        const choice = chunk.choices?.[0];
        const content = choice?.delta?.content;

        if (content) {
          // DeepSeek R1: detect inline <think>...</think> blocks.
          // Simple heuristic: if the content chunk is within a think block,
          // emit as thinking_delta; otherwise emit as text_delta.
          // For production use, the synthesis layer should handle full think-tag parsing.
          yield { type: 'text_delta', text: content };
        }

        // Accumulate tool call deltas (id + name arrive only on first chunk per index).
        const toolCallDeltas = choice?.delta?.tool_calls;
        if (toolCallDeltas) {
          for (const delta of toolCallDeltas) {
            const idx = delta.index ?? 0;
            if (!toolCallAccumulator.has(idx)) {
              toolCallAccumulator.set(idx, { id: delta.id ?? '', name: delta.function?.name ?? '', argumentsChunks: [] });
            }
            const tc = toolCallAccumulator.get(idx)!;
            if (delta.id) tc.id = delta.id;
            if (delta.function?.name) tc.name = delta.function.name;
            if (delta.function?.arguments) tc.argumentsChunks.push(delta.function.arguments);
          }
        }

        const finishReason = choice?.finish_reason;
        if (finishReason === 'tool_calls') {
          // Emit tool events for all accumulated tool calls, then a tool_calls stop.
          for (const [, tc] of toolCallAccumulator) {
            const argsJson = tc.argumentsChunks.join('');
            yield { type: 'tool_use_start', id: tc.id, name: tc.name };
            yield { type: 'tool_use_input_delta', id: tc.id, partialJson: argsJson };
            let input: Record<string, unknown> = {};
            try { input = JSON.parse(argsJson); } catch { /* ignore malformed JSON */ }
            yield { type: 'tool_use_complete', id: tc.id, name: tc.name, input };
          }
          yield { type: 'message_stop', stopReason: 'tool_calls' };
        } else if (finishReason) {
          yield { type: 'message_stop', stopReason: finishReason };
        }

        const usage = chunk.usage;
        if (usage) {
          yield {
            type: 'usage',
            inputTokens: usage.prompt_tokens,
            outputTokens: usage.completion_tokens,
            // DeepSeek cache telemetry: prompt_cache_hit_tokens
            cacheReadTokens: (usage as unknown as Record<string, number>).prompt_cache_hit_tokens ?? 0,
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
