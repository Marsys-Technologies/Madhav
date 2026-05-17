/**
 * Unit tests for B.4 — streamdown wired into V2AssistantText (audit finding O6).
 *
 * Mirrors legacy markdown_render.test.ts patterns: verifies that MarkdownContent
 * is imported and used in V2AssistantText instead of the bare <p> element.
 * End-to-end rendering of code blocks / KaTeX / GFM tables is tested via
 * the existing streamdown unit suite (streamdown_render.test.ts).
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'

const v2Src = readFileSync(
  join(__dirname, '../../../src/components/consume/ConsumeChatV2.tsx'),
  'utf-8',
)

const markdownSrc = readFileSync(
  join(__dirname, '../../../src/components/chat/MarkdownContent.tsx'),
  'utf-8',
)

describe('B.4 — streamdown in V2AssistantText', () => {
  it('MarkdownContent is imported in ConsumeChatV2', () => {
    expect(v2Src).toContain("from '../chat/MarkdownContent'")
  })

  it('V2AssistantText renders via MarkdownContent not bare <p>', () => {
    const fn = v2Src.slice(
      v2Src.indexOf('function V2AssistantText'),
      v2Src.indexOf('function V2AssistantText') + 2500,
    )
    expect(fn).toContain('<MarkdownContent')
    expect(fn).not.toContain('<p className="whitespace-pre-wrap"')
  })

  it('V2AssistantText passes streaming prop based on message.status', () => {
    const fn = v2Src.slice(
      v2Src.indexOf('function V2AssistantText'),
      v2Src.indexOf('function V2AssistantText') + 2500,
    )
    expect(fn).toContain('streaming={isStreaming}')
    expect(fn).toContain("'running'")
  })

  it('V2AssistantText passes data-testid for E2E targeting', () => {
    const fn = v2Src.slice(
      v2Src.indexOf('function V2AssistantText'),
      v2Src.indexOf('function V2AssistantText') + 2500,
    )
    expect(fn).toContain('v2-message-text')
  })

  it('MarkdownContent uses streamdown (not ReactMarkdown) — α2 swap preserved', () => {
    expect(markdownSrc).toContain('streamdown')
    expect(markdownSrc).not.toContain("from 'react-markdown'")
  })

  it('MarkdownContent accepts isAnimating prop (streamdown live animation)', () => {
    expect(markdownSrc).toContain('isAnimating')
  })

  it('MarkdownContent applies remarkGfm (GFM tables/strikethrough)', () => {
    expect(markdownSrc).toContain('remarkGfm')
  })

  it('MarkdownContent applies remarkMath + rehypeKatex (LaTeX)', () => {
    expect(markdownSrc).toContain('remarkMath')
    expect(markdownSrc).toContain('rehypeKatex')
  })

  it('MarkdownContent custom code block component handles fenced blocks', () => {
    expect(markdownSrc).toContain('CodeBlock')
  })

  it('MarkdownContent handles incomplete fences (streamdown native)', () => {
    // Streamdown handles unterminated blocks natively (closeUnclosedFences deleted at α2)
    expect(markdownSrc).not.toContain('closeUnclosedFences')
  })

  it('citation count still computed for drawer badge in V2AssistantText', () => {
    const fn = v2Src.slice(
      v2Src.indexOf('function V2AssistantText'),
      v2Src.indexOf('function V2AssistantText') + 2500,
    )
    expect(fn).toContain('onCitationCount')
    expect(fn).toContain('renderWithCitations')
  })

  it('V2AssistantText uses useMessage() to detect streaming status', () => {
    const fn = v2Src.slice(
      v2Src.indexOf('function V2AssistantText'),
      v2Src.indexOf('function V2AssistantText') + 800,
    )
    expect(fn).toContain('useMessage()')
    expect(fn).toContain('isStreaming')
  })
})
