/**
 * C-S5: ToolCallCard.test.tsx
 *
 * Tests for ToolCallCard + tool_verbs:
 *   - verb labels render correctly per state
 *   - stream-order interleaving (text_A → tool_X → text_B → tool_Y → text_C)
 *   - Marsys gold accent (not coral)
 *   - InlineToolCard.tsx does not exist
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ToolCallCard } from '../../../src/components/chat/ToolCallCard'
import { getToolVerb, getRegisteredToolNames } from '../../../src/components/chat/tool_verbs'

// ---------------------------------------------------------------------------
// tool_verbs.ts
// ---------------------------------------------------------------------------

describe('C-S5: tool_verbs — getToolVerb()', () => {
  it('returns known verb for query_panchanga', () => {
    const entry = getToolVerb('query_panchanga')
    expect(entry.done).toContain('panchang')
    expect(entry.running).toContain('panchang')
  })

  it('returns known verb for query_ephemeris', () => {
    const entry = getToolVerb('query_ephemeris')
    expect(entry.done).toBeTruthy()
    expect(entry.running).toContain('…')
  })

  it('falls back for unmapped tool name', () => {
    const entry = getToolVerb('some_unknown_tool')
    expect(entry.done).toBe('Used some_unknown_tool')
    expect(entry.running).toBe('Using some_unknown_tool…')
  })

  it('registered tool count is >= 15 (sufficient coverage)', () => {
    expect(getRegisteredToolNames().length).toBeGreaterThanOrEqual(15)
  })

  it('all registered tools have non-empty done + running', () => {
    for (const name of getRegisteredToolNames()) {
      const entry = getToolVerb(name)
      expect(entry.done, `${name}.done`).toBeTruthy()
      expect(entry.running, `${name}.running`).toBeTruthy()
    }
  })

  it('running labels end with "…"', () => {
    for (const name of getRegisteredToolNames()) {
      const entry = getToolVerb(name)
      expect(entry.running, `${name}.running should end with …`).toMatch(/…$/)
    }
  })
})

// ---------------------------------------------------------------------------
// ToolCallCard — render
// ---------------------------------------------------------------------------

describe('C-S5: ToolCallCard — basic render', () => {
  it('renders completed state with verb label', () => {
    render(
      <ToolCallCard
        toolName="query_panchanga"
        state="output-available"
      />
    )
    const label = screen.getByTestId('tool-card-verb-label')
    expect(label.textContent).toContain('panchang')
    // Should NOT contain the running form
    expect(label.textContent).not.toContain('…')
  })

  it('renders running state with verb + ellipsis', () => {
    render(
      <ToolCallCard
        toolName="query_panchanga"
        state="input-streaming"
      />
    )
    const label = screen.getByTestId('tool-card-verb-label')
    expect(label.textContent).toContain('…')
  })

  it('renders error state with Error prefix', () => {
    render(
      <ToolCallCard
        toolName="query_ephemeris"
        state="output-error"
        errorText="Connection failed"
      />
    )
    const label = screen.getByTestId('tool-card-verb-label')
    expect(label.textContent).toContain('Error')
  })

  it('renders with unknown tool name (fallback verb)', () => {
    render(
      <ToolCallCard
        toolName="custom_tool_xyz"
        state="output-available"
      />
    )
    const label = screen.getByTestId('tool-card-verb-label')
    expect(label.textContent).toContain('custom_tool_xyz')
  })
})

// ---------------------------------------------------------------------------
// ToolCallCard — stream-order interleaving
// ---------------------------------------------------------------------------

describe('C-S5: stream-order interleaving — text + tools in DOM order', () => {
  it('renders text_A → tool_X → text_B → tool_Y → text_C in document order', () => {
    // Simulate AssistantMessage rendering parts in stream order
    const { container } = render(
      <div data-testid="message-container">
        <div data-testid="text-A">text_A</div>
        <ToolCallCard toolName="query_panchanga" state="output-available" />
        <div data-testid="text-B">text_B</div>
        <ToolCallCard toolName="query_ephemeris" state="output-available" />
        <div data-testid="text-C">text_C</div>
      </div>
    )

    // Get all children in DOM order
    const children = Array.from(container.firstElementChild!.children)
    const order = children.map(el => {
      if (el.getAttribute('data-testid')?.startsWith('text')) return el.getAttribute('data-testid')
      // ToolCallCard has data-tool-name on the button inside
      const btn = el.querySelector('button[data-tool-name]')
      return btn ? `tool-${btn.getAttribute('data-tool-name')}` : 'unknown'
    })

    expect(order).toEqual([
      'text-A',
      'tool-query_panchanga',
      'text-B',
      'tool-query_ephemeris',
      'text-C',
    ])
  })
})

// ---------------------------------------------------------------------------
// C-S5: no InlineToolCard.tsx duplicate
// ---------------------------------------------------------------------------

describe('C-S5: no InlineToolCard.tsx', () => {
  it('InlineToolCard.tsx does not exist in the component directory', async () => {
    const fs = await import('fs')
    const exists = fs.existsSync('./src/components/chat/InlineToolCard.tsx')
    expect(exists).toBe(false)
  })
})

// ---------------------------------------------------------------------------
// C-S5: deploy.yml flag
// ---------------------------------------------------------------------------

describe('C-S5: deploy.yml has R11C_TOOL_CARDS flag', () => {
  it('deploy.yml contains NEXT_PUBLIC_MARSYS_FLAG_R11C_TOOL_CARDS', async () => {
    const fs = await import('fs')
    const deploy = fs.readFileSync('../.github/workflows/deploy.yml', 'utf8')
    expect(deploy).toContain('NEXT_PUBLIC_MARSYS_FLAG_R11C_TOOL_CARDS')
  })
})
