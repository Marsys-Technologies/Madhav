'use client'

import { memo, useMemo } from 'react'
import { Streamdown, type Components } from 'streamdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import { CodeBlock } from './CodeBlock'
import { cn } from '@/lib/utils'
import { StreamingDots } from './StreamingDots'

interface Props {
  children: string
  className?: string
  streaming?: boolean
  customComponents?: Partial<Components>
}

function extractLang(className: string | undefined): string | undefined {
  if (!className) return undefined
  const match = className.match(/language-(\w+)/)
  return match ? match[1] : undefined
}

const MARKDOWN_COMPONENTS = (isStreaming: boolean): Components => ({
  p: ({ children }) => <p className="mb-4 last:mb-0">{children}</p>,
  a: ({ href, children }) => (
    <a
      href={href}
      target={href?.startsWith('http') ? '_blank' : undefined}
      rel={href?.startsWith('http') ? 'noopener noreferrer' : undefined}
      className="text-[var(--brand-gold-light)] underline decoration-[var(--brand-gold-light)]/60 underline-offset-2 hover:decoration-[var(--brand-gold-light)] hover:text-[var(--brand-gold)] transition-colors"
    >
      {children}
    </a>
  ),
  strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  // Downshift: markdown # → <h2>, ## → <h3>, etc. so ChatShell's <h1>
  // remains the sole h1 on the page (WCAG 2.4.6). Visual styling preserved.
  h1: ({ children }) => (
    <h2 className="mt-6 mb-3 font-heading text-2xl font-semibold tracking-tight">{children}</h2>
  ),
  h2: ({ children }) => (
    <h3 className="mt-6 mb-3 font-heading text-xl font-semibold tracking-tight">{children}</h3>
  ),
  h3: ({ children }) => (
    <h4 className="mt-5 mb-2 font-heading text-lg font-semibold tracking-tight">{children}</h4>
  ),
  h4: ({ children }) => (
    <h5 className="mt-4 mb-2 font-heading text-base font-semibold">{children}</h5>
  ),
  h5: ({ children }) => (
    <h6 className="mt-3 mb-1 font-heading text-sm font-semibold">{children}</h6>
  ),
  h6: ({ children }) => (
    <h6 className="mt-3 mb-1 font-heading text-sm font-semibold">{children}</h6>
  ),
  ul: ({ children }) => (
    <ul className="mb-4 list-disc space-y-1.5 pl-6 marker:text-muted-foreground">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="mb-4 list-decimal space-y-1.5 pl-6 marker:text-muted-foreground">{children}</ol>
  ),
  li: ({ children }) => <li className="leading-[1.65]">{children}</li>,
  blockquote: ({ children }) => (
    <blockquote className="my-4 border-l-2 border-border bg-muted/30 px-4 py-2 italic text-muted-foreground">
      {children}
    </blockquote>
  ),
  hr: () => <hr className="my-6 border-border" />,
  table: ({ children }) => (
    <div className="my-4 overflow-x-auto">
      <table className="w-full border-collapse text-sm">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="border-b border-border">{children}</thead>,
  tr: ({ children }) => <tr className="border-b border-border/60 last:border-0">{children}</tr>,
  th: ({ children }) => (
    <th className="px-3 py-2 text-left font-semibold text-foreground">{children}</th>
  ),
  td: ({ children }) => <td className="px-3 py-2 align-top">{children}</td>,
  code: ({ className: codeClass, children, ...rest }) => {
    const lang = extractLang(codeClass)
    if (!lang) {
      return (
        <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.88em]" {...rest}>
          {children}
        </code>
      )
    }
    // Internal blocks captured server-side — must not appear in visible prose.
    if (lang === 'marsys_methodology_block' || lang === 'marsys_citations') return null
    const raw = String(children).replace(/\n$/, '')
    return <CodeBlock code={raw} lang={lang} isStreaming={isStreaming} />
  },
  pre: ({ children }) => <>{children}</>,
})

function MarkdownContentImpl({ children, className, streaming = false, customComponents }: Props) {
  const components = useMemo(
    () => ({ ...MARKDOWN_COMPONENTS(streaming), ...customComponents }),
    [streaming, customComponents],
  )

  return (
    <div
      aria-live={streaming ? 'polite' : 'off'}
      aria-atomic="false"
      aria-busy={streaming}
      className={cn(
        'chat-prose text-[15px] leading-[1.72] text-foreground',
        '[&>*:first-child]:mt-0 [&>*:last-child]:mb-0',
        className
      )}
      style={streaming ? { contain: 'style' } : undefined}
    >
      <Streamdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={components}
        isAnimating={streaming}
      >
        {children}
      </Streamdown>
      {streaming && (
        <span className="inline-flex items-center ml-1" data-testid="v2-streaming-dots">
          <StreamingDots />
        </span>
      )}
    </div>
  )
}

export const MarkdownContent = memo(MarkdownContentImpl)
