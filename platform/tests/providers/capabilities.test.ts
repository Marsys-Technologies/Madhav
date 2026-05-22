/**
 * A-S0: capabilities.test.ts
 * Tests for ProviderCapabilities interface + manifest-validator runtime validation.
 */

import { describe, it, expect } from 'vitest';
import { PROVIDER_CAPABILITY_KEYS } from '../../src/lib/providers/capabilities';
import { validateManifest } from '../../src/lib/providers/manifest-validator';
import type { ProviderCapabilities } from '../../src/lib/providers/capabilities';

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

/** A minimal valid manifest representative of the Anthropic provider. */
const VALID_ANTHROPIC_MANIFEST: ProviderCapabilities = {
  extendedThinking: 'native_effort',
  promptCaching: 'explicit_4bp',
  adaptiveToolLoop: 'stop_reason',
  interleavedThinkingTool: true,
  smoothStreaming: true,
  webSearch: 'first_party',
  webFetch: 'first_party',
  codeExecution: 'first_party',
  nativeMemory: 'memory_tool',
  inputImage: true,
  inputAudio: false,
  inputVideo: false,
  inputPdf: 'files_api_inline',
  outputVoice: null,
  outputImage: null,
  computerUse: 'computer_use_api',
  structuredOutputs: 'tool_force',
  maxContextTokens: 1_000_000,
};

/** A minimal valid manifest representative of DeepSeek. */
const VALID_DEEPSEEK_MANIFEST: ProviderCapabilities = {
  extendedThinking: 'inline_blocks',
  promptCaching: 'implicit',
  adaptiveToolLoop: 'finish_reason_tool_calls',
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
  maxContextTokens: 128_000,
};

// ---------------------------------------------------------------------------
// PROVIDER_CAPABILITY_KEYS: structural tests
// ---------------------------------------------------------------------------

describe('PROVIDER_CAPABILITY_KEYS', () => {
  it('contains all 18 expected keys', () => {
    expect(PROVIDER_CAPABILITY_KEYS).toHaveLength(18);
  });

  it('contains maxContextTokens', () => {
    expect(PROVIDER_CAPABILITY_KEYS).toContain('maxContextTokens');
  });

  it('contains extendedThinking', () => {
    expect(PROVIDER_CAPABILITY_KEYS).toContain('extendedThinking');
  });
});

// ---------------------------------------------------------------------------
// validateManifest: valid manifests pass
// ---------------------------------------------------------------------------

describe('validateManifest — valid manifests', () => {
  it('accepts a full Anthropic-style manifest', () => {
    expect(() => validateManifest(VALID_ANTHROPIC_MANIFEST)).not.toThrow();
  });

  it('returns the same manifest object (typed)', () => {
    const result = validateManifest(VALID_ANTHROPIC_MANIFEST);
    expect(result).toBe(VALID_ANTHROPIC_MANIFEST);
  });

  it('accepts a DeepSeek-style manifest with null fields', () => {
    expect(() => validateManifest(VALID_DEEPSEEK_MANIFEST)).not.toThrow();
  });

  it('accepts a Google-style manifest', () => {
    const googleManifest: ProviderCapabilities = {
      extendedThinking: 'native_budget',
      promptCaching: 'cached_content_api',
      adaptiveToolLoop: 'finish_reason_function_calls',
      interleavedThinkingTool: true,
      smoothStreaming: true,
      webSearch: 'grounding',
      webFetch: null,
      codeExecution: 'first_party',
      nativeMemory: 'workspace',
      inputImage: true,
      inputAudio: true,
      inputVideo: true,
      inputPdf: 'files_api',
      outputVoice: 'live_api',
      outputImage: 'imagen',
      computerUse: null,
      structuredOutputs: 'response_schema',
      maxContextTokens: 2_000_000,
    };
    expect(() => validateManifest(googleManifest)).not.toThrow();
  });

  it('accepts an OpenAI-style manifest', () => {
    const openaiManifest: ProviderCapabilities = {
      extendedThinking: 'polyfill_cot',
      promptCaching: 'automatic',
      adaptiveToolLoop: 'finish_reason_tool_calls',
      interleavedThinkingTool: false,
      smoothStreaming: true,
      webSearch: 'preview_api',
      webFetch: null,
      codeExecution: 'first_party',
      nativeMemory: 'product_only',
      inputImage: true,
      inputAudio: true,
      inputVideo: false,
      inputPdf: 'files_api',
      outputVoice: 'tts_streaming',
      outputImage: 'gpt_image',
      computerUse: 'cua_responses',
      structuredOutputs: 'json_schema_strict',
      maxContextTokens: 200_000,
    };
    expect(() => validateManifest(openaiManifest)).not.toThrow();
  });

  it('accepts an NVIDIA NIM manifest (mostly null)', () => {
    const nvidiaManifest: ProviderCapabilities = {
      extendedThinking: null,
      promptCaching: null,
      adaptiveToolLoop: 'finish_reason_tool_calls',
      interleavedThinkingTool: false,
      smoothStreaming: true,
      webSearch: null,
      webFetch: null,
      codeExecution: null,
      nativeMemory: null,
      inputImage: true,
      inputAudio: false,
      inputVideo: false,
      inputPdf: null,
      outputVoice: null,
      outputImage: null,
      computerUse: null,
      structuredOutputs: null,
      maxContextTokens: 131_072,
    };
    expect(() => validateManifest(nvidiaManifest)).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// validateManifest: malformed manifests throw
// ---------------------------------------------------------------------------

describe('validateManifest — invalid manifests', () => {
  it('throws on null input', () => {
    expect(() => validateManifest(null)).toThrow(TypeError);
    expect(() => validateManifest(null)).toThrow('[manifest-validator]');
  });

  it('throws on non-object input (string)', () => {
    expect(() => validateManifest('anthropic')).toThrow(TypeError);
  });

  it('throws on non-object input (number)', () => {
    expect(() => validateManifest(42)).toThrow(TypeError);
  });

  it('throws when a required field is missing', () => {
    const { maxContextTokens: _removed, ...partial } = VALID_ANTHROPIC_MANIFEST;
    expect(() => validateManifest(partial)).toThrow('maxContextTokens');
  });

  it('throws when extendedThinking has an unknown value', () => {
    const bad = { ...VALID_ANTHROPIC_MANIFEST, extendedThinking: 'magic_thinking' };
    expect(() => validateManifest(bad)).toThrow('extendedThinking');
  });

  it('throws when promptCaching has an unknown value', () => {
    const bad = { ...VALID_ANTHROPIC_MANIFEST, promptCaching: 'turbo_cache' };
    expect(() => validateManifest(bad)).toThrow('promptCaching');
  });

  it('throws when webSearch has an unknown value', () => {
    const bad = { ...VALID_ANTHROPIC_MANIFEST, webSearch: 'bing_search' };
    expect(() => validateManifest(bad)).toThrow('webSearch');
  });

  it('throws when maxContextTokens is zero', () => {
    const bad = { ...VALID_ANTHROPIC_MANIFEST, maxContextTokens: 0 };
    expect(() => validateManifest(bad)).toThrow('maxContextTokens');
  });

  it('throws when maxContextTokens is negative', () => {
    const bad = { ...VALID_ANTHROPIC_MANIFEST, maxContextTokens: -1000 };
    expect(() => validateManifest(bad)).toThrow('maxContextTokens');
  });

  it('throws when maxContextTokens is a float', () => {
    const bad = { ...VALID_ANTHROPIC_MANIFEST, maxContextTokens: 128_000.5 };
    expect(() => validateManifest(bad)).toThrow('maxContextTokens');
  });

  it('throws when maxContextTokens is a string', () => {
    const bad = { ...VALID_ANTHROPIC_MANIFEST, maxContextTokens: '200000' as unknown as number };
    expect(() => validateManifest(bad)).toThrow('maxContextTokens');
  });

  it('throws when interleavedThinkingTool is a string instead of boolean', () => {
    const bad = { ...VALID_ANTHROPIC_MANIFEST, interleavedThinkingTool: 'yes' as unknown as boolean };
    expect(() => validateManifest(bad)).toThrow('interleavedThinkingTool');
  });

  it('error message lists ALL failed fields', () => {
    const bad = {
      ...VALID_ANTHROPIC_MANIFEST,
      extendedThinking: 'wrong',
      webSearch: 'wrong',
    };
    let errorMsg = '';
    try {
      validateManifest(bad);
    } catch (e) {
      errorMsg = (e as TypeError).message;
    }
    expect(errorMsg).toContain('extendedThinking');
    expect(errorMsg).toContain('webSearch');
  });
});
