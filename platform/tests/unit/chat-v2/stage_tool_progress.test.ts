/**
 * Unit tests for B.5 — StageStepper + ToolCallCard wired into V2Message (audit finding O3).
 *
 * Source-shape tests verifying:
 * - StageStepper component structure (3 tests)
 * - ToolCallCard component structure (3 tests)
 * - ConsumeChatV2 integration wiring (3 tests)
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'

const stepperSrc = readFileSync(
  join(__dirname, '../../../src/components/chat-v2/StageStepper.tsx'),
  'utf-8',
)

const toolCardSrc = readFileSync(
  join(__dirname, '../../../src/components/chat-v2/ToolCallCard.tsx'),
  'utf-8',
)

const v2Src = readFileSync(
  join(__dirname, '../../../src/components/consume/ConsumeChatV2.tsx'),
  'utf-8',
)

// ── StageStepper component tests ─────────────────────────────────────────────

describe('B.5 — StageStepper', () => {
  it('renders nothing (early return) when stages is empty', () => {
    expect(stepperSrc).toContain('if (stages.length === 0) return null')
  })

  it('renders a chip per stage with data-testid containing stage name', () => {
    expect(stepperSrc).toContain('data-testid={`v2-stage-${s.stage}`}')
    expect(stepperSrc).toContain('data-testid="v2-stage-stepper"')
  })

  it('imports StagePart from data_parts and uses STAGE_LABELS lookup', () => {
    expect(stepperSrc).toContain("from '@/lib/streams/data_parts'")
    expect(stepperSrc).toContain('STAGE_LABELS')
    expect(stepperSrc).toContain("compose_bundle")
    expect(stepperSrc).toContain("synthesis")
  })
})

// ── ToolCallCard component tests ──────────────────────────────────────────────

describe('B.5 — ToolCallCard', () => {
  it('renders data-testid using tool.name for E2E targeting', () => {
    expect(toolCardSrc).toContain('data-testid={`v2-tool-card-${tool.name}`}')
  })

  it('shows ms label when tool is done', () => {
    expect(toolCardSrc).toContain("tool.status === 'done'")
    expect(toolCardSrc).toContain('tool.ms')
    expect(toolCardSrc).toContain('ms</span>')
  })

  it('imports ToolPart from data_parts and handles all four status values', () => {
    expect(toolCardSrc).toContain("from '@/lib/streams/data_parts'")
    expect(toolCardSrc).toContain("'running'")
    expect(toolCardSrc).toContain("'done'")
    expect(toolCardSrc).toContain("'error'")
    expect(toolCardSrc).toContain("'pending'")
  })
})

// ── ConsumeChatV2 integration wiring tests ────────────────────────────────────

describe('B.5 — ConsumeChatV2 wiring', () => {
  it('imports StageStepper and ToolCallCard from chat-v2 directory', () => {
    expect(v2Src).toContain("from '../chat-v2/StageStepper'")
    expect(v2Src).toContain("from '../chat-v2/ToolCallCard'")
  })

  it('V2Message extracts stageHistory and toolHistory from dataParts', () => {
    expect(v2Src).toContain('stageHistory')
    expect(v2Src).toContain('toolHistory')
    expect(v2Src).toContain("'data-stage'")
    expect(v2Src).toContain("'data-tool'")
  })

  it('StageStepper and ToolCallCard render inside V2Message gated on isStreaming', () => {
    const msgFn = v2Src.slice(
      v2Src.indexOf('function V2Message'),
      v2Src.indexOf('function V2Message') + 7000,
    )
    expect(msgFn).toContain('isStreaming && stageHistory.length > 0')
    expect(msgFn).toContain('<StageStepper stages={stageHistory}')
    expect(msgFn).toContain('isStreaming && toolHistory.length > 0')
    expect(msgFn).toContain('v2-tool-cards')
    expect(msgFn).toContain('<ToolCallCard key={tool.name} tool={tool}')
  })
})
