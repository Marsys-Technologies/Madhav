import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import { buildMcpEvidenceEnvelope, projectMcpEvidencePlan } from '@/lib/mcp/prashna_ask/evidence'
import type { SafeRoutingSnapshot } from '@/lib/ai-console/execution/types'

const evidencePath = path.join(
  process.cwd(),
  'src/lib/mcp/prashna_ask/evidence.ts',
)

describe('MCP BYOK evidence boundary', () => {
  it('has no internal synthesis or static model-stack dependency', () => {
    const source = readFileSync(evidencePath, 'utf8')
    expect(source).not.toMatch(/prashna_ask_synthesis|synthesis_stage|DEFAULT_STACK_ID|getEffectiveModel/)
  })

  it('defines the versioned external-synthesis envelope and omits reading', () => {
    const source = readFileSync(evidencePath, 'utf8')
    expect(source).toContain("schema_version: 'madhav.evidence.v1'")
    expect(source).toContain("mode: 'external'")
    expect(source).toContain('performed_by_madhav: false')
    expect(source).not.toMatch(/\breading\s*:/)
  })

  it('ignores arbitrary metadata keys that could overwrite the evidence contract', () => {
    const target = {
      kind: 'provider_model' as const,
      connectionId: 'connection-1',
      providerId: 'google' as const,
      modelId: 'model-1',
    }
    const snapshot = {
      source: 'mcp', userId: 'user-1', correlationId: 'correlation-1', conversationId: null,
      selection: { kind: 'default' }, resolvedChoice: { kind: 'provider_model', connectionId: 'connection-1', modelId: 'model-1' },
      configurationVersion: null,
      roles: { synthesizer: target, planner: target, deep_planner: target, worker: target },
    } satisfies SafeRoutingSnapshot
    const envelope = buildMcpEvidenceEnvelope({
      question: 'safe question', plan: null, results: [], completeness: null,
      judgmentFlags: [], responseAccountability: null, snapshot,
      metadata: {
        ok: true,
        reading: 'must not escape',
        model: 'must not escape',
        identity: 'must not escape',
        schema_version: 'attacker-version',
      } as never,
    })

    expect(envelope).toMatchObject({
      schema_version: 'madhav.evidence.v1',
      synthesis: { mode: 'external', performed_by_madhav: false },
      question: 'safe question',
      ok: true,
    })
    expect(envelope).not.toHaveProperty('reading')
    expect(envelope).not.toHaveProperty('model')
    expect(envelope).not.toHaveProperty('identity')
    expect(envelope.routing.roles).not.toHaveProperty('synthesizer')
  })

  it('projects only safe plan fields for normal and safety-withheld evidence', () => {
    const unsafePlan = {
      query_class: 'timing',
      query_intent_summary: 'summary',
      domains: ['career'],
      forward_looking: true,
      tool_calls: [{
        tool_name: 'safe_tool', priority: 1, token_budget: 400,
        params: { secret_query: 'must not escape' },
        reason: 'private planner rationale',
        runtime_binding: { credential: 'must not escape' },
      }],
      synthesis_guidance: 'hidden guidance',
      query_text: 'hidden raw query',
      prompt: 'hidden prompt',
    }
    const projected = projectMcpEvidencePlan(unsafePlan)

    expect(projected).toEqual({
      query_class: 'timing', query_intent_summary: 'summary', domains: ['career'],
      forward_looking: true,
      tools: [{ tool_name: 'safe_tool', priority: 1, token_budget: 400 }],
    })
    expect(JSON.stringify(projected)).not.toMatch(/secret_query|private planner|runtime_binding|hidden guidance|hidden raw query|hidden prompt/)
  })
})
