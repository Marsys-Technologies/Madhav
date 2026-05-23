/**
 * nvidia/adapter.ts — NVIDIA NIM CapabilityAdapter skeleton (A-S6).
 *
 * Implements CapabilityAdapter for the NVIDIA NIM stack.
 * NIM uses an OpenAI-compatible API endpoint; the adapter wraps the existing
 * NIM routing in the model registry.
 *
 * The NVIDIA_PLANNER_ENABLED flag controls whether UQE planner calls route
 * to NIM by query class (existing behavior; orthogonal to this adapter).
 * This adapter handles the chat streaming path for NIM stacks selected via
 * the stack picker.
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
import { NVIDIA_MANIFEST } from './manifest';

export class NVIDIAAdapter implements CapabilityAdapter {
  readonly providerId = 'nvidia';

  getManifest(): ProviderCapabilities {
    return NVIDIA_MANIFEST;
  }

  /**
   * Primary streaming chat — real NVIDIA NIM API implementation.
   * NIM uses an OpenAI-compatible endpoint; no thinking_delta events
   * (NVIDIA NIM does not support extended thinking in Marsys baseline config).
   */
  async *chat(request: ChatRequest): AsyncIterable<ChatEvent> {
    try {
      const client = new OpenAI({
        apiKey: process.env.NVIDIA_NIM_API_KEY,
        baseURL: 'https://integrate.api.nvidia.com/v1',
      });
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

      const toolCallAccumulator: Map<number, { id: string; name: string; argumentsChunks: string[] }> = new Map();

      for await (const chunk of stream) {
        const choice = chunk.choices?.[0];
        const content = choice?.delta?.content;
        if (content) {
          yield { type: 'text_delta', text: content };
        }
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
          for (const [, tc] of toolCallAccumulator) {
            const argsJson = tc.argumentsChunks.join('');
            yield { type: 'tool_use_start', id: tc.id, name: tc.name };
            yield { type: 'tool_use_input_delta', id: tc.id, partialJson: argsJson };
            let input: Record<string, unknown> = {};
            try { input = JSON.parse(argsJson); } catch { /* ignore */ }
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
          };
        }
      }
    } catch (err) {
      const error = err instanceof Error ? err.message : String(err);
      yield { type: 'error', error };
    }
  }

  thinking(_request: ThinkingRequest): ThinkingResponse {
    // R11.C — NVIDIA NIM: no extended thinking in Marsys baseline config.
    // NIM is a model-hosting layer; thinking depends on the hosted model.
    // The Marsys NIM config (Llama 3.1/3.3, Mistral) does not enable thinking.
    // Capability hint in UI surfaces "Switch to Anthropic/Gemini for adaptive thinking."
    //
    // Returns null mode so synthesis layer can surface capability hint.
    return {
      mode: null,
      providerPayload: {
        hint: 'R11C_HINT_SWITCH_TO_THINKING_PROVIDER',
      },
    };
  }

  cache(_request: CacheRequest): CacheResponse {
    // NIM: no prompt caching in baseline config
    throw new CapabilityUnsupportedError('cache', 'nvidia');
  }

  tools(request: ToolsRequest): ToolsResponse {
    // R11.E — NVIDIA NIM agentic loop (model-dependent) (E-S5).
    //
    // NVIDIA NIM hosts many open-weight models. Tool-loop support depends on
    // the active hosted model:
    //   - llama-3.1-70b-instruct: supports OpenAI-compat function calling
    //   - llama-3.3-70b-instruct: supports OpenAI-compat function calling
    //   - mistral-7b-instruct-v0.3: limited/no tool support
    //
    // For models that support tool calling: uses finish_reason === 'tool_calls'
    // (OpenAI-compat). For models that don't: throws CapabilityUnsupportedError
    // so the dispatcher surfaces a "switch stack" hint.
    //
    // The NVIDIA_PLANNER_ENABLED planner routing (existing behavior) is orthogonal
    // to this — it routes certain query classes to NIM regardless of stack selection.
    // The agentic loop is only active when NIM is the explicitly selected stack.
    const maxIterations = request.maxIterations ?? 8;
    return {
      mode: 'finish_reason_tool_calls',
      maxIterations,
      tools: request.tools,
      providerPayload: {
        terminationSignal: 'finish_reason_tool_calls',
        terminationValue: 'tool_calls',
        // Supported NIM models for tool calling
        supportedModels: [
          'meta/llama-3.1-70b-instruct',
          'meta/llama-3.1-8b-instruct',
          'meta/llama-3.3-70b-instruct',
        ],
        // Models that do NOT support tool calling — throw CapabilityUnsupportedError
        unsupportedModels: [
          'mistralai/mistral-7b-instruct-v0.3',
          'mistralai/mixtral-8x7b-instruct-v0.1',
        ],
        // NVIDIA_PLANNER_ENABLED routing is preserved (orthogonal to this)
        preservePlannerRouting: true,
        supportsInterleavedTextTool: false,
      },
    };
  }

  webSearch(_request: WebSearchRequest): Promise<WebSearchResult> {
    throw new CapabilityUnsupportedError('webSearch', 'nvidia');
  }

  webFetch(_request: WebFetchRequest): Promise<WebFetchResult> {
    throw new CapabilityUnsupportedError('webFetch', 'nvidia');
  }

  codeExecution(_request: CodeExecutionRequest): Promise<CodeExecutionResult> {
    throw new CapabilityUnsupportedError('codeExecution', 'nvidia');
  }

  memory(_request: MemoryRequest): Promise<MemoryResponse> {
    throw new CapabilityUnsupportedError('memory', 'nvidia');
  }

  multimodal(request: MultimodalRequest): MultimodalResponse {
    const supported: MultimodalResponse['supportedInputModalities'] = [];
    const unsupported: MultimodalResponse['unsupportedInputModalities'] = [];
    for (const m of request.inputModalities) {
      if (m === 'image') {
        // llama3.2-vision hosted model supports images
        supported.push(m);
      } else {
        unsupported.push(m);
      }
    }
    return {
      supportedInputModalities: supported,
      unsupportedInputModalities: unsupported,
      supportedOutputModalities: [],
    };
  }

  imageGeneration(_request: ImageGenRequest): Promise<ImageGenResult> {
    throw new CapabilityUnsupportedError('imageGeneration', 'nvidia');
  }

  async *computerUse(_request: ComputerUseRequest): AsyncIterable<ComputerUseEvent> {
    throw new CapabilityUnsupportedError('computerUse', 'nvidia');
  }

  structuredOutputs(_request: StructuredOutputsRequest): StructuredOutputsResponse {
    throw new CapabilityUnsupportedError('structuredOutputs', 'nvidia');
  }
}
