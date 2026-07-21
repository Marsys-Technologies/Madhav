import { describe, it, expect } from 'vitest'
import { validate } from '@/lib/schemas/index'

describe('Schema validation', () => {
  describe('asset_entry', () => {
    it('accepts a valid asset entry', () => {
      const valid = {
        canonical_id: 'FORENSIC',
        path: '99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md',
        version: 'v8.0',
        status: 'CURRENT',
        layer: 'L1',
        expose_to_chat: true,
        representations: ['file', 'chunks'],
        interface_version: '1.0',
        fingerprint: 'abc123',
        native_id: 'universal',
      }
      expect(validate('asset_entry', valid).valid).toBe(true)
    })

    it('rejects an asset entry with invalid status', () => {
      const invalid = {
        canonical_id: 'FORENSIC',
        path: 'some/path.md',
        version: 'v1.0',
        status: 'INVALID_STATUS',
        layer: 'L1',
        expose_to_chat: true,
        representations: ['file'],
        interface_version: '1.0',
        fingerprint: 'abc123',
        native_id: 'universal',
      }
      const result = validate('asset_entry', invalid)
      expect(result.valid).toBe(false)
      expect(result.errors).toBeDefined()
    })
  })

  describe('query_plan', () => {
    it('accepts a valid query plan', () => {
      const valid = {
        query_plan_id: '123e4567-e89b-12d3-a456-426614174000',
        query_text: 'What does my chart say about career?',
        query_class: 'interpretive',
        domains: ['career'],
        forward_looking: false,
        tools_authorized: ['msr_sql'],
        history_mode: 'synthesized',
        panel_mode: false,
        expected_output_shape: 'three_interpretation',
        manifest_fingerprint: 'sha256abc',
        schema_version: '1.0',
      }
      expect(validate('query_plan', valid).valid).toBe(true)
    })

    it('rejects a query plan with invalid query_class', () => {
      const invalid = {
        query_plan_id: '123e4567-e89b-12d3-a456-426614174000',
        query_text: 'test',
        query_class: 'invalid_class',
        domains: [],
        forward_looking: false,
        tools_authorized: [],
        history_mode: 'synthesized',
        panel_mode: false,
        expected_output_shape: 'single_answer',
        manifest_fingerprint: 'sha256abc',
        schema_version: '1.0',
      }
      expect(validate('query_plan', invalid).valid).toBe(false)
    })
  })

  describe('bundle', () => {
    it('accepts a valid bundle', () => {
      const valid = {
        bundle_id: '123e4567-e89b-12d3-a456-426614174001',
        query_plan_reference: '123e4567-e89b-12d3-a456-426614174000',
        manifest_fingerprint: 'sha256abc',
        mandatory_context: [
          {
            canonical_id: 'FORENSIC',
            version: 'v8.0',
            content_hash: 'hashvalue',
            token_count: 40000,
            role: 'floor',
            source: 'rule_composer',
          },
        ],
        total_tokens: 40000,
        bundle_hash: 'bundlehash',
        schema_version: '1.0',
      }
      expect(validate('bundle', valid).valid).toBe(true)
    })

    it('rejects a bundle missing required fields', () => {
      expect(validate('bundle', { bundle_id: 'only-id' }).valid).toBe(false)
    })
  })

  describe('tool_bundle', () => {
    it('accepts a valid tool bundle', () => {
      const valid = {
        tool_bundle_id: '123e4567-e89b-12d3-a456-426614174002',
        tool_name: 'msr_sql',
        tool_version: '1.0',
        invocation_params: { query: 'SELECT * FROM signals' },
        results: [{ content: 'signal data here' }],
        served_from_cache: false,
        latency_ms: 120,
        result_hash: 'resulthash',
        schema_version: '1.0',
      }
      expect(validate('tool_bundle', valid).valid).toBe(true)
    })

    it('rejects a tool bundle with missing tool_name', () => {
      expect(
        validate('tool_bundle', {
          tool_bundle_id: 'id',
          tool_version: '1.0',
          invocation_params: {},
          results: [],
          served_from_cache: false,
          latency_ms: 0,
          result_hash: 'h',
          schema_version: '1.0',
        }).valid,
      ).toBe(false)
    })
  })
})
