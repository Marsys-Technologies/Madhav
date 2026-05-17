import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ConversationSidebarV2 as ConversationSidebar } from '@/components/consume/ConversationSidebarV2'

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ json: () => Promise.resolve({ conversations: [] }) })))
})

const defaultProps = {
  chartId: 'chart-test-123',
  activeId: null,
  onSelect: vi.fn(),
  onNew: vi.fn(),
  collapsed: false,
  onToggle: vi.fn(),
}

describe('ConversationSidebar background (A.2)', () => {
  it('sidebar wrapper does NOT contain bg-zinc-950', () => {
    render(<ConversationSidebar {...defaultProps} />)
    const sidebar = screen.getByTestId('v2-conversation-sidebar')
    expect(sidebar.className).not.toMatch(/bg-zinc-950/)
  })

  it('sidebar wrapper uses translucent brand-charcoal background', () => {
    render(<ConversationSidebar {...defaultProps} />)
    const sidebar = screen.getByTestId('v2-conversation-sidebar')
    expect(sidebar.className).toMatch(/brand-charcoal/)
    expect(sidebar.className).toMatch(/backdrop-blur/)
  })

  it('sidebar wrapper has gold hairline border-r', () => {
    render(<ConversationSidebar {...defaultProps} />)
    const sidebar = screen.getByTestId('v2-conversation-sidebar')
    expect(sidebar.className).toMatch(/brand-gold/)
  })

  it('collapsed strip does NOT contain bg-zinc-950', () => {
    render(<ConversationSidebar {...defaultProps} collapsed={true} />)
    // collapsed renders a div, not an aside — no v2-conversation-sidebar testid
    const strip = screen.getByTestId('v2-sidebar-expand').closest('div')
    expect(strip?.className).not.toMatch(/bg-zinc-950/)
    expect(strip?.className).toMatch(/brand-charcoal/)
  })
})
