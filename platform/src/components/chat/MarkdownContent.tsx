'use client'

import { memo, useMemo } from 'react'
import { Streamdown, type Components } from 'streamdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import { CodeBlock } from './CodeBlock'
import { InteractiveTable } from './InteractiveTable'
import { MermaidBlock } from './MermaidBlock'
import { cn } from '@/lib/utils'
import { StreamingDots } from './StreamingDots'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function extractNodeText(node: any): string {
  if (!node) return ''
  if (node.type === 'text') return node.value ?? ''
  if (Array.isArray(node.children)) return node.children.map(extractNodeText).join('')
  return ''
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function extractHastTableData(node: any): { headers: string[]; rows: string[][] } | null {
  const children: any[] = node?.children ?? [] // eslint-disable-line @typescript-eslint/no-explicit-any
  const thead = children.find((c: any) => c.tagName === 'thead') // eslint-disable-line @typescript-eslint/no-explicit-any
  const tbody = children.find((c: any) => c.tagName === 'tbody') // eslint-disable-line @typescript-eslint/no-explicit-any
  if (!thead || !tbody) return null

  const headerRow = (thead.children ?? []).find((c: any) => c.tagName === 'tr') // eslint-disable-line @typescript-eslint/no-explicit-any
  const dataRows = (tbody.children ?? []).filter((c: any) => c.tagName === 'tr') // eslint-disable-line @typescript-eslint/no-explicit-any
  if (dataRows.length < 3) return null

  const headers = (headerRow?.children ?? [])
    .filter((c: any) => c.tagName === 'th') // eslint-disable-line @typescript-eslint/no-explicit-any
    .map(extractNodeText)
  const rows = dataRows.map((row: any) => // eslint-disable-line @typescript-eslint/no-explicit-any
    (row.children ?? []).filter((c: any) => c.tagName === 'td').map(extractNodeText), // eslint-disable-line @typescript-eslint/no-explicit-any
  )
  return { headers, rows }
}

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

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type AugmentedComponents = Components & Record<string, any>

export const MARKDOWN_COMPONENTS = (isStreaming: boolean): AugmentedComponents => ({
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
  table: ({ children, ...rest }) => {
    // Read flag at render time (not at module load) so tests can stub it.
    const flagEnabled =
      process.env.NEXT_PUBLIC_MARSYS_FLAG_R10_INTERACTIVE_TABLES === 'true'
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const node = (rest as any).node
    if (flagEnabled && node) {
      const tableData = extractHastTableData(node)
      if (tableData) {
        return <InteractiveTable headers={tableData.headers} rows={tableData.rows} />
      }
    }
    return (
      <div className="my-4 overflow-x-auto">
        <table className="w-full border-collapse text-sm">{children}</table>
      </div>
    )
  },
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
    // Route mermaid blocks to MermaidBlock when flag enabled.
    if (lang === 'mermaid' && process.env.NEXT_PUBLIC_MARSYS_FLAG_R10_MERMAID === 'true') {
      return <MermaidBlock code={raw} isStreaming={isStreaming} />
    }
    return <CodeBlock code={raw} lang={lang} isStreaming={isStreaming} />
  },
  pre: ({ children }) => <>{children}</>,
  // GFM footnote reference: renders as amber superscript badge (R7-S2).
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  footnoteReference: ({ node }: { node?: any }) => (
    <sup>
      <span className="inline-flex items-center rounded px-1 text-xs font-medium bg-amber-500/20 text-amber-400">
        {node?.identifier ?? '?'}
      </span>
    </sup>
  ),
  // GFM footnote definition block: invisible (data flows via data parts, not footnote HTML).
  footnoteDefinition: () => <span className="sr-only" />,
})

function MarkdownContentImpl({ children, className, streaming = false, customComponents }: Props) {
  const components = useMemo(
    () => ({ ...MARKDOWN_COMPONENTS(streaming), ...customComponents }) as AugmentedComponents,
    [streaming, customComponents],
  )

  // markdown-content: R11.B B-S6 CSS target.
  // .consume-shell.r11b-active .markdown-content overrides typescale in globals.css
  // (1rem body / 1.65 leading, serif h1-h3, mono code at 14px/8px radius).
  return (
    <div
      aria-live={streaming ? 'polite' : 'off'}
      aria-atomic="false"
      aria-busy={streaming}
      className={cn(
        'markdown-content chat-prose leading-[1.72] text-foreground',
        '[&>*:first-child]:mt-0 [&>*:last-child]:mb-0',
        className
      )}
      style={{
        fontSize: 'calc(15px * var(--text-scale, 1))',
        ...(streaming ? { contain: 'style' } : {}),
      }}
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
