/**
 * A-S1: adapter-interface.test.ts
 * Type-level tests for CapabilityAdapter interface + CapabilityUnsupportedError.
 *
 * This test file primarily serves as a TypeScript compile-time assertion that:
 * 1. A mock object satisfying the full CapabilityAdapter interface can be constructed.
 * 2. CapabilityUnsupportedError is throwable and has the right fields.
 * 3. The request/response types are correctly shaped.
 *
 * Runtime tests are minimal since this is a pure interface file.
 */

import { describe, it, expect } from 'vitest';
import type { CapabilityAdapter } from '../../src/lib/providers/adapter';
import { CapabilityUnsupportedError } from '../../src/lib/providers/adapter';
import type {
  ChatRequest,
  ChatEvent,
  ThinkingRequest,
  CacheRequest,
  ToolsRequest,
  WebSearchRequest,
  WebFetchRequest,
  CodeExecutionRequest,
  MemoryRequest,
  MultimodalRequest,
  ImageGenRequest,
  ComputerUseRequest,
  StructuredOutputsRequest,
} from '../../src/lib/providers/types';

// ---------------------------------------------------------------------------
// Type-level smoke test: build a minimal mock implementing CapabilityAdapter
// ---------------------------------------------------------------------------

/**
 * A mock adapter that implements the full interface by throwing
 * CapabilityUnsupportedError for every method. Proves the interface shape is correct.
 */
const MOCK_ADAPTER: CapabilityAdapter = {
  providerId: 'mock',

  getManifest() {
    return {
      extendedThinking: null,
      promptCaching: null,
      adaptiveToolLoop: null,
      interleavedThinkingTool: false,
      smoothStreaming: true,
      webSearch: null,
      webFetch: null,
      codeExecution: null,
      nativeMemory: null,
      inputImage: false,
      inputAudio: false,
      inputVideo: false,
      inputPdf: null,
      outputVoice: null,
      outputImage: null,
      computerUse: null,
      structuredOutputs: null,
      maxContextTokens: 1000,
    };
  },

  async *chat(_req: ChatRequest): AsyncIterable<ChatEvent> {
    throw new CapabilityUnsupportedError('chat', 'mock');
  },

  thinking(_req: ThinkingRequest) {
    throw new CapabilityUnsupportedError('thinking', 'mock');
  },

  cache(_req: CacheRequest) {
    throw new CapabilityUnsupportedError('cache', 'mock');
  },

  tools(_req: ToolsRequest) {
    throw new CapabilityUnsupportedError('tools', 'mock');
  },

  webSearch(_req: WebSearchRequest): Promise<never> {
    throw new CapabilityUnsupportedError('webSearch', 'mock');
  },

  webFetch(_req: WebFetchRequest): Promise<never> {
    throw new CapabilityUnsupportedError('webFetch', 'mock');
  },

  codeExecution(_req: CodeExecutionRequest): Promise<never> {
    throw new CapabilityUnsupportedError('codeExecution', 'mock');
  },

  memory(_req: MemoryRequest): Promise<never> {
    throw new CapabilityUnsupportedError('memory', 'mock');
  },

  multimodal(_req: MultimodalRequest) {
    return {
      supportedInputModalities: [],
      unsupportedInputModalities: [],
      supportedOutputModalities: [],
    };
  },

  imageGeneration(_req: ImageGenRequest): Promise<never> {
    throw new CapabilityUnsupportedError('imageGeneration', 'mock');
  },

  async *computerUse(_req: ComputerUseRequest) {
    throw new CapabilityUnsupportedError('computerUse', 'mock');
  },

  structuredOutputs(_req: StructuredOutputsRequest) {
    throw new CapabilityUnsupportedError('structuredOutputs', 'mock');
  },
};

// ---------------------------------------------------------------------------
// Runtime tests
// ---------------------------------------------------------------------------

describe('CapabilityUnsupportedError', () => {
  it('is an instance of Error', () => {
    const err = new CapabilityUnsupportedError('webSearch', 'nvidia');
    expect(err).toBeInstanceOf(Error);
  });

  it('has the correct name', () => {
    const err = new CapabilityUnsupportedError('webSearch', 'nvidia');
    expect(err.name).toBe('CapabilityUnsupportedError');
  });

  it('exposes capability and providerId', () => {
    const err = new CapabilityUnsupportedError('codeExecution', 'deepseek');
    expect(err.capability).toBe('codeExecution');
    expect(err.providerId).toBe('deepseek');
  });

  it('includes capability and provider in message', () => {
    const err = new CapabilityUnsupportedError('memory', 'openai');
    expect(err.message).toContain('memory');
    expect(err.message).toContain('openai');
  });
});

describe('CapabilityAdapter — interface shape', () => {
  it('mock adapter satisfies CapabilityAdapter interface', () => {
    // If this compiles, the interface is correctly satisfied
    expect(MOCK_ADAPTER.providerId).toBe('mock');
  });

  it('getManifest returns an object with required fields', () => {
    const manifest = MOCK_ADAPTER.getManifest();
    expect(manifest).toHaveProperty('extendedThinking');
    expect(manifest).toHaveProperty('maxContextTokens');
    expect(typeof manifest.maxContextTokens).toBe('number');
  });

  it('mock adapter has 13 methods + providerId', () => {
    const methods = [
      'getManifest',
      'chat',
      'thinking',
      'cache',
      'tools',
      'webSearch',
      'webFetch',
      'codeExecution',
      'memory',
      'multimodal',
      'imageGeneration',
      'computerUse',
      'structuredOutputs',
    ];
    for (const method of methods) {
      expect(typeof MOCK_ADAPTER[method as keyof CapabilityAdapter]).toBe('function');
    }
  });

  it('multimodal returns correct response shape', () => {
    const response = MOCK_ADAPTER.multimodal({
      inputModalities: ['image', 'audio'],
      outputModalities: ['voice'],
    });
    expect(response).toHaveProperty('supportedInputModalities');
    expect(response).toHaveProperty('unsupportedInputModalities');
    expect(response).toHaveProperty('supportedOutputModalities');
    expect(Array.isArray(response.supportedInputModalities)).toBe(true);
  });

  it('unsupported methods throw CapabilityUnsupportedError', () => {
    expect(() => MOCK_ADAPTER.thinking({ extendedThinkingMode: null })).toThrow(
      CapabilityUnsupportedError,
    );
    expect(() => MOCK_ADAPTER.cache({ cacheMode: null })).toThrow(CapabilityUnsupportedError);
    expect(() => MOCK_ADAPTER.tools({ toolLoopMode: null, tools: [], maxIterations: 8 })).toThrow(
      CapabilityUnsupportedError,
    );
  });
});
