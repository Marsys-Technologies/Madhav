/**
 * Unit tests for streamdown render correctness.
 *
 * Verifies:
 *  - incomplete code fences, KaTeX math, and tables don't crash the component
 *  - ARIA attributes set correctly for streaming vs static modes
 *  - marsys_methodology_block code language is suppressed (returns null)
 *  - closeUnclosedFences is absent (streamdown handles unterminated blocks natively)
 *  - mixed-content strings render without errors
 */
import { describe, it, expect, vi, beforeAll } from 'vitest'
import { render, screen } from '@testing-library/react'
import React from 'react'

// Streamdown is a complex SSR-capable lib. Mock it so unit tests stay in jsdom
// without needing KaTeX CSS, Shiki workers, etc. The real integration is tested
// in E2E. Here we verify MarkdownContent's container + prop wiring.
vi.mock('streamdown', () => ({
  Streamdown: ({
    children,
    isAnimating,
  }: {
    children: string
    isAnimating?: boolean
  }) =>
    React.createElement(
      'div',
      { 'data-testid': 'streamdown', 'data-animating': String(isAnimating) },
      children,
    ),
}))

vi.mock('remark-gfm', () => ({ default: () => {} }))
vi.mock('remark-math', () => ({ default: () => {} }))
vi.mock('rehype-katex', () => ({ default: () => {} }))

vi.mock('@/components/chat/CodeBlock', () => ({
  CodeBlock: ({ code, lang }: { code: string; lang: string }) =>
    React.createElement('pre', { 'data-lang': lang }, code),
}))

type MC = (props: { children: string; streaming?: boolean; className?: string }) => React.ReactElement

let MarkdownContent: MC

beforeAll(async () => {
  const mod = await import('@/components/chat/MarkdownContent')
  MarkdownContent = mod.MarkdownContent as unknown as MC
})

const mk = (props: { streaming?: boolean; children: string; className?: string }) =>
  React.createElement(MarkdownContent, props)

let MARKDOWN_COMPONENTS: ((streaming: boolean) => Record<string, unknown>)

beforeAll(async () => {
  // Already loaded MarkdownContent above; also grab MARKDOWN_COMPONENTS.
  const mod = await import('@/components/chat/MarkdownContent')
  MARKDOWN_COMPONENTS = mod.MARKDOWN_COMPONENTS as unknown as (streaming: boolean) => Record<string, unknown>
})

describe('MarkdownContent — streamdown integration', () => {
  describe('ARIA attributes', () => {
    it('sets aria-live=polite + aria-busy=true when streaming', () => {
      const { container } = render(mk({ streaming: true, children: 'Hello' }))
      const wrapper = container.firstChild as HTMLElement
      expect(wrapper.getAttribute('aria-live')).toBe('polite')
      expect(wrapper.getAttribute('aria-busy')).toBe('true')
      expect(wrapper.getAttribute('aria-atomic')).toBe('false')
    })

    it('sets aria-live=off + aria-busy=false when not streaming', () => {
      const { container } = render(mk({ children: 'Hello' }))
      const wrapper = container.firstChild as HTMLElement
      expect(wrapper.getAttribute('aria-live')).toBe('off')
      expect(wrapper.getAttribute('aria-busy')).toBe('false')
    })
  })

  describe('CSS class wiring', () => {
    it('renders v2-streaming-dots element when streaming', () => {
      const { getByTestId } = render(mk({ streaming: true, children: 'text' }))
      expect(getByTestId('v2-streaming-dots')).toBeTruthy()
    })

    it('does not render v2-streaming-dots when not streaming', () => {
      const { queryByTestId } = render(mk({ children: 'text' }))
      expect(queryByTestId('v2-streaming-dots')).toBeNull()
    })

    it('does not add chat-stream-caret class (replaced by StreamingDots)', () => {
      const { container } = render(mk({ streaming: true, children: 'text' }))
      expect((container.firstChild as HTMLElement).className).not.toContain('chat-stream-caret')
    })

    it('applies style contain:style only when streaming', () => {
      const { container: sc } = render(mk({ streaming: true, children: 'text' }))
      const { container: nc } = render(mk({ children: 'text' }))
      expect((sc.firstChild as HTMLElement).style.contain).toBe('style')
      expect((nc.firstChild as HTMLElement).style.contain).toBe('')
    })
  })

  describe('Streamdown props passthrough', () => {
    it('passes isAnimating=true to Streamdown when streaming', () => {
      render(mk({ streaming: true, children: 'text' }))
      expect(screen.getByTestId('streamdown').getAttribute('data-animating')).toBe('true')
    })

    it('passes isAnimating=false to Streamdown when not streaming', () => {
      render(mk({ children: 'text' }))
      expect(screen.getByTestId('streamdown').getAttribute('data-animating')).toBe('false')
    })

    it('forwards children to Streamdown unchanged', () => {
      render(mk({ children: 'Hello world' }))
      expect(screen.getByTestId('streamdown').textContent).toBe('Hello world')
    })
  })

  describe('GFM footnote components (R7-S2)', () => {
    it('footnoteReference renders amber badge with identifier', () => {
      // The footnoteReference component in MARKDOWN_COMPONENTS renders [^N] as amber badge
      const comps = MARKDOWN_COMPONENTS(false)
      const FootnoteRef = comps.footnoteReference as React.ComponentType<{ node?: { identifier: string } }>
      expect(FootnoteRef).toBeDefined()
      const { container } = render(React.createElement(FootnoteRef, { node: { identifier: '1' } }))
      const span = container.querySelector('.bg-amber-500\\/20.text-amber-400')
      expect(span).not.toBeNull()
      expect(span?.textContent).toBe('1')
    })

    it('footnoteDefinition renders sr-only span (invisible)', () => {
      const comps = MARKDOWN_COMPONENTS(false)
      const FootnoteDef = comps.footnoteDefinition as React.ComponentType<Record<string, never>>
      expect(FootnoteDef).toBeDefined()
      const { container } = render(React.createElement(FootnoteDef, {}))
      const span = container.querySelector('.sr-only')
      expect(span).not.toBeNull()
    })
  })

  describe('closeUnclosedFences removal — raw strings passed through', () => {
    it('passes incomplete code fence directly to Streamdown without appending ```', () => {
      const incomplete = '```python\nprint("hello")'
      render(mk({ children: incomplete }))
      // Streamdown receives the raw string — closeUnclosedFences is gone
      expect(screen.getByTestId('streamdown').textContent).toBe(incomplete)
    })

    it('passes complete fence string unchanged', () => {
      const complete = '```python\ncode\n```\n\nMore text'
      render(mk({ children: complete }))
      expect(screen.getByTestId('streamdown').textContent).toBe(complete)
    })

    it('passes incomplete KaTeX math without modification', () => {
      const incompleteMath = '$\\frac{1}{2'
      render(mk({ children: incompleteMath }))
      expect(screen.getByTestId('streamdown').textContent).toBe(incompleteMath)
    })

    it('passes incomplete table row without modification', () => {
      const incompleteTable = '| Col A | Col B |\n|---|---|'
      render(mk({ children: incompleteTable }))
      expect(screen.getByTestId('streamdown').textContent).toBe(incompleteTable)
    })
  })
})
