/**
 * X-S11 — Mermaid Diagram Rendering
 * Amendment 2: parent-context integration tests.
 *
 * Click-path: Chat V2 response containing a ```mermaid block →
 *   visual diagram renders (not raw code text). During streaming,
 *   a placeholder ("Rendering diagram…") shows until streaming ends.
 *
 * Amendment 1: NEXT_PUBLIC_MARSYS_FLAG_R10_MERMAID client-side flag;
 *   MUST be in deploy.yml --build-arg (verified via acceptance grep).
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, act, waitFor } from '@testing-library/react'
import React from 'react'

// Mock next/dynamic to return the inner component synchronously in tests.
vi.mock('next/dynamic', () => ({
  default: (loader: () => Promise<React.ComponentType<any>>) => {
    // Resolve the loader immediately and return a wrapper component.
    let Comp: React.ComponentType<any> | null = null
    loader().then((m) => { Comp = m })
    return function DynamicWrapper(props: any) {
      if (!Comp) return <div data-testid="v2-mermaid-dynamic-loading">loading…</div>
      return React.createElement(Comp, props)
    }
  },
}))

// Mock mermaid to avoid heavy bundle and jsdom SVG limitations.
vi.mock('mermaid', () => ({
  default: {
    initialize: vi.fn(),
    render: vi.fn().mockResolvedValue({ svg: '<svg data-testid="mermaid-svg"><g/></svg>' }),
  },
}))

import { MarkdownContent } from '@/components/chat/MarkdownContent'
import { MermaidBlock } from '@/components/chat/MermaidBlock'

// ── Parent-context shell ──────────────────────────────────────────────────────

function MarkdownShell({ children, streaming = false }: { children: string; streaming?: boolean }) {
  return (
    <div data-testid="v2-chat-shell">
      <MarkdownContent streaming={streaming}>{children}</MarkdownContent>
    </div>
  )
}

const MERMAID_MD = '```mermaid\nflowchart TD\n  A --> B\n```'

// ── MermaidBlock unit tests ───────────────────────────────────────────────────

describe('MermaidBlock — unit', () => {
  it('shows streaming placeholder when isStreaming=true', () => {
    const { getByTestId } = render(<MermaidBlock code="flowchart TD\n  A-->B" isStreaming />)
    expect(getByTestId('v2-mermaid-streaming-placeholder')).toBeTruthy()
  })

  it('renders diagram when isStreaming=false and mermaid resolves', async () => {
    const { findByTestId } = render(<MermaidBlock code="flowchart TD\n  A-->B" isStreaming={false} />)
    // After mermaid.render resolves, the SVG is set.
    await findByTestId('v2-mermaid-diagram')
  })

  it('shows error fallback (raw code) when mermaid throws', async () => {
    const mermaid = (await import('mermaid')).default
    vi.mocked(mermaid.render).mockRejectedValueOnce(new Error('parse error'))

    const { findByTestId } = render(<MermaidBlock code="bad diagram" isStreaming={false} />)
    await findByTestId('v2-mermaid-error')
  })
})

// ── Parent-context tests per Amendment 2 ─────────────────────────────────────

describe('MarkdownContent — MermaidBlock parent-context (Amendment 2)', () => {
  beforeEach(() => {
    vi.stubEnv('NEXT_PUBLIC_MARSYS_FLAG_R10_MERMAID', 'true')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('renders streaming placeholder when isStreaming=true', async () => {
    const { findByTestId } = render(<MarkdownShell streaming>{MERMAID_MD}</MarkdownShell>)
    await findByTestId('v2-mermaid-streaming-placeholder')
  })

  it('renders diagram (not raw code) when isStreaming=false and flag=true', async () => {
    const { findByTestId, queryByRole } = render(
      <MarkdownShell streaming={false}>{MERMAID_MD}</MarkdownShell>,
    )
    // v2-mermaid-diagram or v2-mermaid-loading should appear (mermaid block rendered)
    const el = await findByTestId('v2-mermaid-diagram')
    expect(el).toBeTruthy()
    // Must NOT be a code element (raw code fallback)
    expect(queryByRole('code')).toBeNull()
  })

  it('renders as static code block when flag=false', async () => {
    vi.unstubAllEnvs()
    vi.stubEnv('NEXT_PUBLIC_MARSYS_FLAG_R10_MERMAID', 'false')

    const { container } = render(<MarkdownShell streaming={false}>{MERMAID_MD}</MarkdownShell>)
    await waitFor(() => {
      // Falls through to CodeBlock — no mermaid testids
      expect(container.querySelector('[data-testid="v2-mermaid-diagram"]')).toBeNull()
      expect(container.querySelector('[data-testid="v2-mermaid-streaming-placeholder"]')).toBeNull()
    })
  })
})
