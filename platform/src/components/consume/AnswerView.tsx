'use client'

import { memo, useMemo, useState } from 'react'
import { Zap } from 'lucide-react'
import { parseCitations, type ParsedSegment } from '@/lib/ui/citation-parser'
import { CitationChip } from '@/components/citations/CitationChip'
import { StreamingMarkdown } from '@/components/chat/StreamingMarkdown'
import { TraceDrawer } from './TraceDrawer'
import { LogPredictionAction } from './LogPredictionAction'

interface Props {
  text: string
  className?: string
  traceId?: string
  queryId?: string
}

/**
 * Renders a finalized synthesis answer with inline citation chips.
 *
 * Footer (when relevant):
 *  - Trace button → opens TraceDrawer (only when traceId provided)
 *  - Log Prediction button → only when detectPrediction returns true
 */
function AnswerViewImpl({ text, className, traceId, queryId }: Props) {
  const { segments } = useMemo(() => parseCitations(text), [text])
  const nodes = useMemo(() => buildNodes(segments), [segments])
  const [traceOpen, setTraceOpen] = useState(false)

  const hasFooter = !!traceId || true // LogPredictionAction self-hides when no detection

  return (
    <div className={className}>
      <div>
        {nodes.map((node, i) => {
          if (node.type === 'markdown') {
            return (
              <StreamingMarkdown key={i} isStreaming={false}>
                {node.content}
              </StreamingMarkdown>
            )
          }
          return (
            <CitationChip
              key={i}
              type={node.citationType}
              id={node.citationId}
              className="mx-0.5 align-middle"
            />
          )
        })}
      </div>

      {hasFooter && (
        <div className="mt-3 flex items-center gap-2">
          {traceId && (
            <button
              type="button"
              onClick={() => setTraceOpen(true)}
              className="inline-flex items-center gap-1 rounded border border-border px-2 py-0.5 text-[11px] text-muted-foreground hover:border-[rgba(var(--status-warn-rgb),0.4)] hover:text-[var(--status-warn)] transition-colors"
              title="Open query trace"
            >
              <Zap className="h-3 w-3" />
              Trace
            </button>
          )}
          <LogPredictionAction answerText={text} queryId={queryId ?? traceId} />
        </div>
      )}

      {traceId && (
        <TraceDrawer
          queryId={traceId}
          open={traceOpen}
          onOpenChange={setTraceOpen}
        />
      )}
    </div>
  )
}

type MarkdownNode = { type: 'markdown'; content: string }
type ChipNode = { type: 'chip'; citationType: 'signal' | 'asset' | 'chunk'; citationId: string }
type RenderNode = MarkdownNode | ChipNode

function buildNodes(segments: ParsedSegment[]): RenderNode[] {
  const nodes: RenderNode[] = []
  let textBuf = ''

  for (const seg of segments) {
    if (seg.kind === 'text') {
      textBuf += seg.text ?? ''
    } else if (seg.kind === 'citation' && seg.citation) {
      if (textBuf.trim()) {
        nodes.push({ type: 'markdown', content: textBuf })
        textBuf = ''
      } else {
        textBuf = ''
      }
      nodes.push({
        type: 'chip',
        citationType: seg.citation.type,
        citationId: seg.citation.id,
      })
    }
  }

  if (textBuf.trim()) {
    nodes.push({ type: 'markdown', content: textBuf })
  }

  return nodes
}

export const AnswerView = memo(AnswerViewImpl)
