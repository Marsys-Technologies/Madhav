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
import { migrationAdapter } from '../migration-adapter';

export class DeepSeekAdapter implements CapabilityAdapter {
  readonly providerId = 'deepseek';

  getManifest(): ProviderCapabilities {
    return DEEPSEEK_MANIFEST;
  }

  /**
   * Primary streaming chat — delegates to MigrationAdapter (A-S10).
   * Production note: R11.C wires extractReasoningMiddleware from the AI SDK
   * to extract <think>...</think> blocks → ChatEvent { type: 'thinking_delta' }.
   */
  async *chat(request: ChatRequest): AsyncIterable<ChatEvent> {
    yield* migrationAdapter.stubChat(request, 'deepseek');
  }

  thinking(_request: ThinkingRequest): ThinkingResponse {
    // R11.C — DeepSeek: inline_blocks mode (thinking: true/false toggle)
    // extractReasoningMiddleware parses <think>...</think> at stream level
    throw new CapabilityUnsupportedError('thinking', 'deepseek');
  }

  cache(_request: CacheRequest): CacheResponse {
    // DeepSeek: implicit caching (prompt_cache_hit_tokens in usage)
    // R11.D — telemetry capture for implicit cache hits
    throw new CapabilityUnsupportedError('cache', 'deepseek');
  }

  tools(_request: ToolsRequest): ToolsResponse {
    // R11.E — DeepSeek: OpenAI-compat tool loop (finish_reason=tool_calls)
    throw new CapabilityUnsupportedError('tools', 'deepseek');
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
