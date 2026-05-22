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
import { migrationAdapter } from '../migration-adapter';

export class NVIDIAAdapter implements CapabilityAdapter {
  readonly providerId = 'nvidia';

  getManifest(): ProviderCapabilities {
    return NVIDIA_MANIFEST;
  }

  /**
   * Primary streaming chat — delegates to MigrationAdapter (A-S10).
   * R11.C wires NIM API streaming; NVIDIA planner routing preserved.
   */
  async *chat(request: ChatRequest): AsyncIterable<ChatEvent> {
    yield* migrationAdapter.stubChat(request, 'nvidia');
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
