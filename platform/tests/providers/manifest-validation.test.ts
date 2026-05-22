/**
 * A-S12: manifest-validation.test.ts
 * Verifies every manifest passes validateManifest() and
 * matches the CAPABILITY_MATRIX expectations.
 */

import { describe, it, expect } from 'vitest';
import { validateManifest } from '../../src/lib/providers/manifest-validator';
import { ANTHROPIC_MANIFEST } from '../../src/lib/providers/anthropic/manifest';
import { GOOGLE_MANIFEST } from '../../src/lib/providers/google/manifest';
import { OPENAI_MANIFEST } from '../../src/lib/providers/openai/manifest';
import { DEEPSEEK_MANIFEST } from '../../src/lib/providers/deepseek/manifest';
import { NVIDIA_MANIFEST } from '../../src/lib/providers/nvidia/manifest';
import { VALID_STACK_IDS, getAllManifests } from '../../src/lib/providers/dispatcher';

// ---------------------------------------------------------------------------
// validateManifest passes on every manifest
// ---------------------------------------------------------------------------

describe('manifest-validation: validateManifest() passes on all 5', () => {
  it('ANTHROPIC_MANIFEST validates cleanly', () => {
    expect(() => validateManifest(ANTHROPIC_MANIFEST)).not.toThrow();
  });

  it('GOOGLE_MANIFEST validates cleanly', () => {
    expect(() => validateManifest(GOOGLE_MANIFEST)).not.toThrow();
  });

  it('OPENAI_MANIFEST validates cleanly', () => {
    expect(() => validateManifest(OPENAI_MANIFEST)).not.toThrow();
  });

  it('DEEPSEEK_MANIFEST validates cleanly', () => {
    expect(() => validateManifest(DEEPSEEK_MANIFEST)).not.toThrow();
  });

  it('NVIDIA_MANIFEST validates cleanly', () => {
    expect(() => validateManifest(NVIDIA_MANIFEST)).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// getAllManifests returns the same manifests as the singletons
// ---------------------------------------------------------------------------

describe('manifest-validation: getAllManifests() consistency', () => {
  const all = getAllManifests();

  it('has exactly 5 entries', () => {
    expect(Object.keys(all)).toHaveLength(5);
  });

  it('all stacks in VALID_STACK_IDS are present', () => {
    for (const id of VALID_STACK_IDS) {
      expect(all[id]).toBeDefined();
    }
  });

  it('anthropic manifest identity matches singleton', () => {
    expect(all.anthropic).toBe(ANTHROPIC_MANIFEST);
  });
});

// ---------------------------------------------------------------------------
// CAPABILITY_MATRIX spot-checks (A-S0 values)
// ---------------------------------------------------------------------------

describe('manifest-validation: CAPABILITY_MATRIX spot-checks', () => {
  // Anthropic
  it('ANTHROPIC: maxContextTokens = 1_000_000', () => {
    expect(ANTHROPIC_MANIFEST.maxContextTokens).toBe(1_000_000);
  });
  it('ANTHROPIC: extendedThinking = native_effort', () => {
    expect(ANTHROPIC_MANIFEST.extendedThinking).toBe('native_effort');
  });
  it('ANTHROPIC: webSearch = first_party', () => {
    expect(ANTHROPIC_MANIFEST.webSearch).toBe('first_party');
  });
  it('ANTHROPIC: computerUse = computer_use_api', () => {
    expect(ANTHROPIC_MANIFEST.computerUse).toBe('computer_use_api');
  });

  // Google
  it('GOOGLE: maxContextTokens = 2_000_000', () => {
    expect(GOOGLE_MANIFEST.maxContextTokens).toBe(2_000_000);
  });
  it('GOOGLE: extendedThinking = native_budget', () => {
    expect(GOOGLE_MANIFEST.extendedThinking).toBe('native_budget');
  });
  it('GOOGLE: webSearch = grounding', () => {
    expect(GOOGLE_MANIFEST.webSearch).toBe('grounding');
  });
  it('GOOGLE: inputAudio = true', () => {
    expect(GOOGLE_MANIFEST.inputAudio).toBe(true);
  });
  it('GOOGLE: inputVideo = true', () => {
    expect(GOOGLE_MANIFEST.inputVideo).toBe(true);
  });

  // OpenAI
  it('OPENAI: maxContextTokens = 200_000', () => {
    expect(OPENAI_MANIFEST.maxContextTokens).toBe(200_000);
  });
  it('OPENAI: structuredOutputs = json_schema_strict', () => {
    expect(OPENAI_MANIFEST.structuredOutputs).toBe('json_schema_strict');
  });

  // DeepSeek
  it('DEEPSEEK: maxContextTokens = 128_000', () => {
    expect(DEEPSEEK_MANIFEST.maxContextTokens).toBe(128_000);
  });
  it('DEEPSEEK: extendedThinking = inline_blocks', () => {
    expect(DEEPSEEK_MANIFEST.extendedThinking).toBe('inline_blocks');
  });
  it('DEEPSEEK: webSearch = null', () => {
    expect(DEEPSEEK_MANIFEST.webSearch).toBeNull();
  });

  // NVIDIA
  it('NVIDIA: maxContextTokens = 131_072', () => {
    expect(NVIDIA_MANIFEST.maxContextTokens).toBe(131_072);
  });
  it('NVIDIA: extendedThinking = null', () => {
    expect(NVIDIA_MANIFEST.extendedThinking).toBeNull();
  });
  it('NVIDIA: inputImage = true', () => {
    expect(NVIDIA_MANIFEST.inputImage).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// maxContextTokens is a positive integer on every manifest
// ---------------------------------------------------------------------------

describe('manifest-validation: maxContextTokens is a positive integer', () => {
  const all = getAllManifests();
  for (const id of VALID_STACK_IDS) {
    it(`${id}: maxContextTokens is positive integer`, () => {
      const v = all[id].maxContextTokens;
      expect(typeof v).toBe('number');
      expect(Number.isInteger(v)).toBe(true);
      expect(v).toBeGreaterThan(0);
    });
  }
});
