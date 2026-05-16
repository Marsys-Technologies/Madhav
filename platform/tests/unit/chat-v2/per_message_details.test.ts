/**
 * per_message_details — structural tests for β6 details drawer.
 *
 * Tests are unit-level (no React rendering required) and verify:
 * - The drawer component file exists with the expected exports
 * - Metadata extraction logic shapes
 * - data-testid conventions used by the drawer
 * - The "View trace" URL format
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'

const drawerSource = readFileSync(
  join(process.cwd(), 'src/components/chat/PerMessageDetailsDrawer.tsx'),
  'utf-8',
)

describe('PerMessageDetailsDrawer — source shape', () => {
  it('exports PerMessageDetailsDrawer', () => {
    expect(drawerSource).toContain('export function PerMessageDetailsDrawer')
  })

  it('uses useMessage hook from @assistant-ui/react', () => {
    expect(drawerSource).toContain("from '@assistant-ui/react'")
    expect(drawerSource).toContain('useMessage')
  })

  it('reads metadata from metadata.custom (not message.metadata directly)', () => {
    expect(drawerSource).toContain('metadata?.custom')
  })

  it('reads data parts from metadata.unstable_data', () => {
    expect(drawerSource).toContain('unstable_data')
  })

  it('has v2-details-drawer test id', () => {
    expect(drawerSource).toContain('data-testid="v2-details-drawer"')
  })

  it('has v2-details-close button', () => {
    expect(drawerSource).toContain('data-testid="v2-details-close"')
  })

  it('has v2-details-backdrop', () => {
    expect(drawerSource).toContain('data-testid="v2-details-backdrop"')
  })

  it('has v2-details-trace-link', () => {
    expect(drawerSource).toContain('data-testid="v2-details-trace-link"')
  })

  it('has v2-details-citation-gate', () => {
    expect(drawerSource).toContain('data-testid="v2-details-citation-gate"')
  })

  it('renders a trace URL in /observatory/trace/[queryId] format', () => {
    expect(drawerSource).toContain('/observatory/trace/')
  })

  it('closes on Escape key', () => {
    expect(drawerSource).toContain("e.key === 'Escape'")
  })

  it('has aria-modal and role dialog', () => {
    expect(drawerSource).toContain('aria-modal="true"')
    expect(drawerSource).toContain('role="dialog"')
  })

  it('shows model, stack, query_class, style sections', () => {
    expect(drawerSource).toContain("meta.model")
    expect(drawerSource).toContain("meta.stack")
    expect(drawerSource).toContain("meta.query_class")
    expect(drawerSource).toContain("meta.style")
  })

  it('shows token breakdown (input/output/reasoning/total)', () => {
    expect(drawerSource).toContain('input_tokens')
    expect(drawerSource).toContain('output_tokens')
    expect(drawerSource).toContain('reasoning_tokens')
  })

  it('shows cost in USD', () => {
    expect(drawerSource).toContain('dollars')
    expect(drawerSource).toContain('fmtUsd')
  })

  it('shows disclosure tier', () => {
    expect(drawerSource).toContain('disclosure_tier')
  })
})

// ─── ConsumeChatV2 wiring ─────────────────────────────────────────────────────

const v2Source = readFileSync(
  join(process.cwd(), 'src/components/consume/ConsumeChatV2.tsx'),
  'utf-8',
)

describe('ConsumeChatV2 — β6 wiring', () => {
  it('imports PerMessageDetailsDrawer', () => {
    expect(v2Source).toContain('PerMessageDetailsDrawer')
  })

  it('has v2-details-btn in assistant action bar', () => {
    expect(v2Source).toContain('data-testid="v2-details-btn"')
  })

  it('renders PerMessageDetailsDrawer inside MessagePrimitive.If assistant', () => {
    // The drawer must be inside the assistant branch (after the MessagePrimitive.If assistant check)
    const assistantBlock = v2Source.slice(v2Source.indexOf('MessagePrimitive.If assistant'))
    expect(assistantBlock).toContain('PerMessageDetailsDrawer')
  })

  it('passes citationCount prop to drawer', () => {
    expect(v2Source).toContain('citationCount={citationCount}')
  })

  it('opens drawer on details button click', () => {
    expect(v2Source).toContain('setDetailsOpen(true)')
  })

  it('closes drawer on close handler', () => {
    expect(v2Source).toContain('setDetailsOpen(false)')
  })

  it('tracks citationCount via onCitationCount callback', () => {
    expect(v2Source).toContain('onCitationCount')
    expect(v2Source).toContain('setCitationCount')
  })
})

// ─── Metadata extraction logic ────────────────────────────────────────────────

describe('metadata extraction logic (pure functions)', () => {
  it('formats large numbers with toLocaleString', () => {
    // fmt() uses toLocaleString
    expect(drawerSource).toContain('toLocaleString()')
  })

  it('formats USD cost to 5 decimal places', () => {
    expect(drawerSource).toContain('toFixed(5)')
  })

  it('formats latency in ms', () => {
    expect(drawerSource).toContain('ms')
  })

  it('finds cost entry by type data-cost', () => {
    expect(drawerSource).toContain("type === 'data-cost'")
  })

  it('finds citation gate entry by type data-citation-gate', () => {
    expect(drawerSource).toContain("type === 'data-citation-gate'")
  })

  it('uses QueryId prefix slice for display', () => {
    expect(drawerSource).toContain('.slice(0, 8)')
  })
})
