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
   * Primary streaming chat — R11.A skeleton.
   * Full NIM API integration wired in A-S7 (dispatcher).
   */
  async *chat(request: ChatRequest): AsyncIterable<ChatEvent> {
    if (!request.messages || request.messages.length === 0) {
      yield { type: 'error', error: 'NVIDIAAdapter.chat: no messages provided' };
      return;
    }
    yield { type: 'text_delta', text: '' };
    yield { type: 'message_stop', stopReason: 'stop' };
  }

  thinking(_request: ThinkingRequest): ThinkingResponse {
    // NVIDIA NIM baseline: no extended thinking support
    throw new CapabilityUnsupportedError('thinking', 'nvidia');
  }

  cache(_request: CacheRequest): CacheResponse {
    // NIM: no prompt caching in baseline config
    throw new CapabilityUnsupportedError('cache', 'nvidia');
  }

  tools(_request: ToolsRequest): ToolsResponse {
    // R11.E — NIM: OpenAI-compat finish_reason=tool_calls loop
    throw new CapabilityUnsupportedError('tools', 'nvidia');
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
