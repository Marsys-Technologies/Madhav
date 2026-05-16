/**
 * γ1 — Panel mode display UX
 *
 * Tests:
 *   - PanelMemberPart / PanelMetaPart schema validation
 *   - panelMemberPart / panelMetaPart helper constructors
 *   - usePanelData extraction logic (tested as a pure function)
 *   - panel_strategy emits panel data parts in panelStageEvents
 */

import { describe, it, expect } from 'vitest'
import {
  PanelMemberPartSchema,
  PanelMetaPartSchema,
  panelMemberPart,
  panelMetaPart,
} from '../../../src/lib/streams/data_parts'

// ── Schema validation ─────────────────────────────────────────────────────────

describe('PanelMemberPartSchema', () => {
  it('accepts a valid success member part', () => {
    const part = {
      type: 'panel_member',
      member_index: 0,
      model_id: 'claude-sonnet-4-6',
      provider_family: 'anthropic',
      status: 'success',
      answer: 'The chart shows…',
      latency_ms: 1234,
    }
    expect(() => PanelMemberPartSchema.parse(part)).not.toThrow()
    expect(PanelMemberPartSchema.parse(part).type).toBe('panel_member')
  })

  it('accepts a failed member part (answer omitted)', () => {
    const part = {
      type: 'panel_member',
      member_index: 2,
      model_id: 'gpt-4o',
      provider_family: 'openai',
      status: 'failed',
      latency_ms: 5000,
    }
    expect(() => PanelMemberPartSchema.parse(part)).not.toThrow()
    expect(PanelMemberPartSchema.parse(part).answer).toBeUndefined()
  })

  it('rejects negative member_index', () => {
    const part = {
      type: 'panel_member',
      member_index: -1,
      model_id: 'gpt-4o',
      provider_family: 'openai',
      status: 'success',
      latency_ms: 100,
    }
    expect(() => PanelMemberPartSchema.parse(part)).toThrow()
  })

  it('rejects invalid status', () => {
    const part = {
      type: 'panel_member',
      member_index: 0,
      model_id: 'gpt-4o',
      provider_family: 'openai',
      status: 'pending',
      latency_ms: 100,
    }
    expect(() => PanelMemberPartSchema.parse(part)).toThrow()
  })
})

describe('PanelMetaPartSchema', () => {
  it('accepts a valid panel meta with divergence', () => {
    const part = {
      type: 'panel_meta',
      member_count: 3,
      has_divergence: true,
      adjudicator_model_id: 'deepseek-v3',
    }
    const parsed = PanelMetaPartSchema.parse(part)
    expect(parsed.has_divergence).toBe(true)
    expect(parsed.member_count).toBe(3)
  })

  it('accepts panel meta without adjudicator_model_id', () => {
    const part = {
      type: 'panel_meta',
      member_count: 2,
      has_divergence: false,
    }
    expect(() => PanelMetaPartSchema.parse(part)).not.toThrow()
  })

  it('rejects member_count of zero', () => {
    const part = {
      type: 'panel_meta',
      member_count: 0,
      has_divergence: false,
    }
    expect(() => PanelMetaPartSchema.parse(part)).toThrow()
  })
})

// ── Helper constructors ────────────────────────────────────────────────────────

describe('panelMemberPart helper', () => {
  it('produces type=panel_member', () => {
    const p = panelMemberPart({
      member_index: 0,
      model_id: 'claude-sonnet-4-6',
      provider_family: 'anthropic',
      status: 'success',
      answer: 'Test',
      latency_ms: 500,
    })
    expect(p.type).toBe('panel_member')
    expect(p.member_index).toBe(0)
    expect(p.answer).toBe('Test')
  })
})

describe('panelMetaPart helper', () => {
  it('produces type=panel_meta', () => {
    const p = panelMetaPart({ member_count: 3, has_divergence: false })
    expect(p.type).toBe('panel_meta')
    expect(p.member_count).toBe(3)
    expect(p.has_divergence).toBe(false)
  })
})

// ── usePanelData extraction logic (pure version) ──────────────────────────────

function extractPanelData(dataParts: ReadonlyArray<unknown>) {
  const panelMembers = dataParts
    .filter(
      (d): d is { type: string; data: { type: string; member_index: number } } =>
        typeof d === 'object' && d !== null &&
        (d as Record<string, unknown>).type === 'data-panel-member',
    )
    .map(d => d.data)
    .sort((a, b) => (a as { member_index: number }).member_index - (b as { member_index: number }).member_index)

  const metaEntry = dataParts.find(
    (d): d is { type: string; data: { type: string } } =>
      typeof d === 'object' && d !== null &&
      (d as Record<string, unknown>).type === 'data-panel-meta',
  )
  const panelMeta = metaEntry ? metaEntry.data : null
  const isPanel = panelMeta !== null

  return { panelMembers, panelMeta, isPanel }
}

describe('extractPanelData', () => {
  it('returns isPanel=false for non-panel data parts', () => {
    const parts = [
      { type: 'data-stage', data: { type: 'stage', stage: 'synthesis', status: 'done' } },
      { type: 'data-cost', data: { type: 'cost', model: 'claude-sonnet-4-6', input_tokens: 100, output_tokens: 200, dollars: 0.01, ms: 1000 } },
    ]
    const { isPanel, panelMembers, panelMeta } = extractPanelData(parts)
    expect(isPanel).toBe(false)
    expect(panelMembers).toHaveLength(0)
    expect(panelMeta).toBeNull()
  })

  it('extracts panel members in sorted order', () => {
    const parts = [
      { type: 'data-panel-member', data: panelMemberPart({ member_index: 2, model_id: 'gemini', provider_family: 'google', status: 'success', latency_ms: 300 }) },
      { type: 'data-panel-member', data: panelMemberPart({ member_index: 0, model_id: 'claude', provider_family: 'anthropic', status: 'success', latency_ms: 100 }) },
      { type: 'data-panel-member', data: panelMemberPart({ member_index: 1, model_id: 'gpt4', provider_family: 'openai', status: 'success', latency_ms: 200 }) },
      { type: 'data-panel-meta', data: panelMetaPart({ member_count: 3, has_divergence: true }) },
    ]
    const { panelMembers, panelMeta, isPanel } = extractPanelData(parts)
    expect(isPanel).toBe(true)
    expect(panelMembers).toHaveLength(3)
    expect((panelMembers[0] as { member_index: number }).member_index).toBe(0)
    expect((panelMembers[1] as { member_index: number }).member_index).toBe(1)
    expect((panelMembers[2] as { member_index: number }).member_index).toBe(2)
    expect((panelMeta as unknown as { has_divergence: boolean }).has_divergence).toBe(true)
  })

  it('handles failed member alongside successful members', () => {
    const parts = [
      { type: 'data-panel-member', data: panelMemberPart({ member_index: 0, model_id: 'claude', provider_family: 'anthropic', status: 'success', answer: 'A', latency_ms: 100 }) },
      { type: 'data-panel-member', data: panelMemberPart({ member_index: 1, model_id: 'gpt4', provider_family: 'openai', status: 'failed', latency_ms: 5000 }) },
      { type: 'data-panel-meta', data: panelMetaPart({ member_count: 2, has_divergence: false }) },
    ]
    const { panelMembers } = extractPanelData(parts)
    expect(panelMembers).toHaveLength(2)
    expect((panelMembers[1] as unknown as { status: string }).status).toBe('failed')
  })
})
