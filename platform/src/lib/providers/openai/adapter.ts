/**
 * openai/adapter.ts — OpenAI (GPT) CapabilityAdapter skeleton (A-S4).
 *
 * Implements CapabilityAdapter for the OpenAI stack.
 * Key OpenAI-specific details:
 *   - stream_options: { include_usage: true } must be set for usage reporting
 *   - tool calls use finish_reason === 'tool_calls' loop
 *   - structured outputs use response_format: { type: 'json_schema', strict: true }
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
import { OPENAI_MANIFEST } from './manifest';

export class OpenAIAdapter implements CapabilityAdapter {
  readonly providerId = 'openai';

  getManifest(): ProviderCapabilities {
    return OPENAI_MANIFEST;
  }

  /**
   * Primary streaming chat — R11.A skeleton.
   * Note: production implementation must include stream_options: { include_usage: true }
   * for accurate token reporting through the Observatory.
   */
  async *chat(request: ChatRequest): AsyncIterable<ChatEvent> {
    if (!request.messages || request.messages.length === 0) {
      yield { type: 'error', error: 'OpenAIAdapter.chat: no messages provided' };
      return;
    }
    yield { type: 'text_delta', text: '' };
    yield { type: 'message_stop', stopReason: 'stop' };
  }

  thinking(_request: ThinkingRequest): ThinkingResponse {
    // R11.C — GPT: polyfill_cot ("think step by step" in system prompt)
    throw new CapabilityUnsupportedError('thinking', 'openai');
  }

  cache(_request: CacheRequest): CacheResponse {
    // R11.D — OpenAI: automatic caching (no explicit breakpoints; no setup needed)
    throw new CapabilityUnsupportedError('cache', 'openai');
  }

  tools(_request: ToolsRequest): ToolsResponse {
    // R11.E — OpenAI: finish_reason=tool_calls loop
    throw new CapabilityUnsupportedError('tools', 'openai');
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
