/**
 * manifest-validator.ts — Runtime validator for ProviderCapabilities manifests.
 *
 * Asserts that a provider's declared manifest conforms to the ProviderCapabilities
 * interface. Throws a descriptive TypeError on validation failure so that bad
 * manifests are caught at module load, not at first use.
 *
 * Usage (in each provider's manifest.ts):
 *   import { validateManifest } from '../manifest-validator';
 *   export const MY_PROVIDER_MANIFEST: ProviderCapabilities = validateManifest({ ... });
 */

import type { ProviderCapabilities } from './capabilities';
import { PROVIDER_CAPABILITY_KEYS } from './capabilities';

// ---------------------------------------------------------------------------
// Allowed values per field (mirrors CAPABILITY_MATRIX.md §9)
// ---------------------------------------------------------------------------

const ALLOWED_VALUES: Record<string, ReadonlyArray<string | boolean | number | null>> = {
  extendedThinking: ['native_effort', 'native_budget', 'inline_blocks', 'polyfill_cot', null],
  promptCaching: ['explicit_4bp', 'cached_content_api', 'automatic', 'implicit', null],
  adaptiveToolLoop: [
    'stop_reason',
    'finish_reason_function_calls',
    'finish_reason_tool_calls',
    null,
  ],
  interleavedThinkingTool: [true, false],
  smoothStreaming: [true, false],
  webSearch: ['first_party', 'grounding', 'preview_api', null],
  webFetch: ['first_party', null],
  codeExecution: ['first_party', null],
  nativeMemory: ['memory_tool', 'workspace', 'product_only', null],
  inputImage: [true, false],
  inputAudio: [true, false],
  inputVideo: [true, false],
  inputPdf: ['files_api', 'inline', 'files_api_inline', null],
  outputVoice: ['live_api', 'tts_streaming', null],
  outputImage: ['imagen', 'dalle', 'gpt_image', null],
  computerUse: ['computer_use_api', 'cua_responses', null],
  structuredOutputs: ['json_schema_strict', 'response_schema', 'tool_force', null],
  // maxContextTokens: validated separately as a positive integer
};

// ---------------------------------------------------------------------------
// Validator
// ---------------------------------------------------------------------------

/**
 * Runtime assertion that `m` conforms to `ProviderCapabilities`.
 * Throws `TypeError` on validation failure (missing field, wrong type, unknown value).
 * Returns the validated manifest typed as `ProviderCapabilities` for convenience.
 *
 * @example
 *   const ANTHROPIC_MANIFEST = validateManifest({
 *     extendedThinking: 'native_effort',
 *     ...
 *   });
 */
export function validateManifest(m: unknown): ProviderCapabilities {
  if (m === null || typeof m !== 'object') {
    throw new TypeError(
      `[manifest-validator] Expected a manifest object, got ${m === null ? 'null' : typeof m}`,
    );
  }

  const manifest = m as Record<string, unknown>;
  const errors: string[] = [];

  // 1. Ensure all required keys are present
  for (const key of PROVIDER_CAPABILITY_KEYS) {
    if (!(key in manifest)) {
      errors.push(`Missing required field: "${key}"`);
    }
  }

  // Early-exit if keys are missing to avoid cascading errors
  if (errors.length > 0) {
    throw new TypeError(
      `[manifest-validator] Invalid ProviderCapabilities manifest:\n  ${errors.join('\n  ')}`,
    );
  }

  // 2. Validate each field's value
  for (const key of PROVIDER_CAPABILITY_KEYS) {
    const value = manifest[key];

    if (key === 'maxContextTokens') {
      // Special case: must be a positive finite integer
      if (typeof value !== 'number' || !Number.isFinite(value) || value <= 0 || !Number.isInteger(value)) {
        errors.push(
          `Field "maxContextTokens" must be a positive integer, got ${JSON.stringify(value)}`,
        );
      }
      continue;
    }

    const allowed = ALLOWED_VALUES[key];
    if (allowed !== undefined) {
      // For boolean fields, typeof check
      const allowedTypes = new Set(allowed.map((v) => typeof v));
      const valueType = value === null ? 'object' : typeof value;

      // null is allowed if null is in the allowed list
      const nullAllowed = allowed.includes(null);
      if (value === null && nullAllowed) {
        continue; // valid
      }
      if (value === null && !nullAllowed) {
        errors.push(`Field "${key}" does not allow null`);
        continue;
      }

      if (!allowed.includes(value as string | boolean | null)) {
        errors.push(
          `Field "${key}" has invalid value ${JSON.stringify(value)}. ` +
            `Allowed: [${allowed.map((v) => JSON.stringify(v)).join(', ')}]`,
        );
      }
      void allowedTypes; // suppress unused variable
      void valueType;
    }
  }

  if (errors.length > 0) {
    throw new TypeError(
      `[manifest-validator] Invalid ProviderCapabilities manifest:\n  ${errors.join('\n  ')}`,
    );
  }

  return m as ProviderCapabilities;
}
