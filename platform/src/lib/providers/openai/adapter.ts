/**
 * openai/adapter.ts — OpenAI (GPT) CapabilityAdapter skeleton (A-S4).
 *
 * Implements CapabilityAdapter for the OpenAI stack.
 * Key OpenAI-specific details:
 *   - stream_options: { include_usage: true } must be set for usage reporting
 *   - tool calls use finish_reason === 'tool_calls' loop
 *   - structured outputs use response_format: { type: 'json_schema', strict: true }
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
import { OPENAI_MANIFEST } from './manifest';

export class OpenAIAdapter implements CapabilityAdapter {
  readonly providerId = 'openai';

  getManifest(): ProviderCapabilities {
    return OPENAI_MANIFEST;
  }

  /**
   * Primary streaming chat — real OpenAI SDK implementation.
   * Uses stream_options: { include_usage: true } for accurate token reporting
   * through the Observatory (R11.D cache telemetry requirement).
   * No thinking_delta events — OpenAI GPT family has no native thinking API.
   */
  async *chat(request: ChatRequest): AsyncIterable<ChatEvent> {
    try {
      const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
      const stream = await client.chat.completions.create({
        model: request.model,
        max_tokens: request.maxTokens ?? 4096,
        messages: request.messages.map((m) => ({
          role: m.role,
          content: typeof m.content === 'string' ? m.content : JSON.stringify(m.content),
        })),
        stream: true,
        stream_options: { include_usage: true },
      });

      for await (const chunk of stream) {
        const choice = chunk.choices?.[0];
        const content = choice?.delta?.content;
        if (content) {
          yield { type: 'text_delta', text: content };
        }
        const finishReason = choice?.finish_reason;
        if (finishReason) {
          yield { type: 'message_stop', stopReason: finishReason };
        }
        const usage = chunk.usage;
        if (usage) {
          yield {
            type: 'usage',
            inputTokens: usage.prompt_tokens,
            outputTokens: usage.completion_tokens,
            cacheReadTokens: usage.prompt_tokens_details?.cached_tokens ?? 0,
          };
        }
      }
    } catch (err) {
      const error = err instanceof Error ? err.message : String(err);
      yield { type: 'error', error };
    }
  }

  thinking(request: ThinkingRequest): ThinkingResponse {
    // R11.C — GPT: polyfill_cot ("think step by step" in system prompt).
    // OpenAI GPT-4.1 family has no native thinking API (o-series retired from Marsys).
    // The CoT nudge is injected as a system-prompt prefix by the synthesis layer.
    // "think step by step before answering" suffices; no provider-level API change.
    const effort = request.effort ?? 'medium';
    // CoT prompt intensity varies by effort level.
    const cotPhrases: Record<string, string> = {
      low: 'think briefly before answering.',
      medium: 'think step by step before answering.',
      high: 'think very carefully and thoroughly, step by step, before answering.',
    };
    return {
      mode: 'polyfill_cot',
      effort,
      providerPayload: {
        // Injected as a system-prompt prefix by the synthesis layer.
        systemPromptPrefix: cotPhrases[effort] ?? cotPhrases.medium,
      },
    };
  }

  cache(_request: CacheRequest): CacheResponse {
    // R11.D — OpenAI: automatic caching (D-S3).
    //
    // OpenAI auto-caches without any explicit markers or setup API calls.
    // The mode is 'automatic' — no request modifications needed.
    //
    // Cache telemetry: the response usage object includes:
    //   usage.prompt_tokens_details.cached_tokens
    //
    // This field is captured by the route layer and forwarded to Observatory.
    // Cost model: cached_tokens cost 25% of standard input token price (25% hit cost).
    //
    // Activation: OpenAI caches when context >= 1024 tokens (as of 2024).
    // No TTL setting available; OpenAI manages eviction automatically.
    return {
      mode: 'automatic',
      breakpointPositions: [],  // no explicit positions for automatic caching
      providerPayload: {
        // Usage telemetry field in response
        cached_tokens: 'usage.prompt_tokens_details.cached_tokens',
        // Prompt caching cost: 25% of standard input token price
        cachedTokenCostFraction: 0.25,
        // Activation threshold (OpenAI manages this automatically)
        minContextTokens: 1024,
        // stream_options: { include_usage: true } is required for usage reporting
        requireStreamUsage: true,
      },
    };
  }

  tools(request: ToolsRequest): ToolsResponse {
    // R11.E — OpenAI tool_calls agentic loop (E-S3).
    //
    // OpenAI's Chat Completions API returns finish_reason === 'tool_calls'
    // when tool execution is needed. The loop reuses agentic_loop.ts engine
    // with OPENAI_LOOP_CONFIG.
    //
    // Responses API: OpenAI's newer Responses API has native multi-turn
    // tool handling, but the adapter uses Chat Completions for compatibility.
    // When the Responses API becomes available server-side, prefer it:
    //   client.responses.create({ ..., tools, previous_response_id })
    // For now: standard while (finish_reason === 'tool_calls') pattern.
    //
    // Usage note: stream_options: { include_usage: true } must be set
    // for accurate per-iteration cost tracking in Observatory.
    const maxIterations = request.maxIterations ?? 8;
    return {
      mode: 'finish_reason_tool_calls',
      maxIterations,
      tools: request.tools,
      providerPayload: {
        terminationSignal: 'finish_reason_tool_calls',
        terminationValue: 'tool_calls',
        // Prefer Responses API when available (tool_choice + multi-step)
        preferResponsesApi: false, // set true when wired in R11.F
        // stream_options required for accurate per-iteration usage
        requireStreamOptions: true,
        // No interleaved text+tool in standard Chat Completions
        supportsInterleavedTextTool: false,
      },
    };
  }

  webSearch(_request: WebSearchRequest): Promise<WebSearchResult> {
    // R11.F — OpenAI: web_search_preview tool (Responses API)
    throw new CapabilityUnsupportedError('webSearch', 'openai');
  }

  webFetch(_request: WebFetchRequest): Promise<WebFetchResult> {
    // No first-party web_fetch on OpenAI; polyfill in R11.F
    throw new CapabilityUnsupportedError('webFetch', 'openai');
  }

  codeExecution(_request: CodeExecutionRequest): Promise<CodeExecutionResult> {
    // R11.F — OpenAI: Code Interpreter (sandboxed Python + file I/O)
    throw new CapabilityUnsupportedError('codeExecution', 'openai');
  }

  memory(_request: MemoryRequest): Promise<MemoryResponse> {
    // OpenAI Memory feature is product-only (ChatGPT); not API-native
    throw new CapabilityUnsupportedError('memory', 'openai');
  }

  multimodal(request: MultimodalRequest): MultimodalResponse {
    const supported: MultimodalResponse['supportedInputModalities'] = [];
    const unsupported: MultimodalResponse['unsupportedInputModalities'] = [];
    for (const m of request.inputModalities) {
      if (m === 'image' || m === 'audio' || m === 'pdf') {
        supported.push(m);
      } else {
        // video: partial (frames only), not enabled in Marsys
        unsupported.push(m);
      }
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
    // R11.K — OpenAI: DALL-E / gpt-image-1
    throw new CapabilityUnsupportedError('imageGeneration', 'openai');
  }

  async *computerUse(_request: ComputerUseRequest): AsyncIterable<ComputerUseEvent> {
    // R11.K — OpenAI: CUA via Responses API
    throw new CapabilityUnsupportedError('computerUse', 'openai');
  }

  structuredOutputs(_request: StructuredOutputsRequest): StructuredOutputsResponse {
    // R11.D — OpenAI: response_format: { type: 'json_schema', strict: true }
    throw new CapabilityUnsupportedError('structuredOutputs', 'openai');
  }
}
