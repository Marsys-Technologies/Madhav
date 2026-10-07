'use client'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { UIMessage } from 'ai'
import { savedReadingTimestamp } from '@/lib/conversations/readingTimestamp'

export function ReadingView({ messages }: { messages: UIMessage[] }) {
  return <div className="space-y-6">{messages.map(message => {
    const savedAt = savedReadingTimestamp(message.metadata)
    return <section key={message.id} className="break-inside-avoid">
    <p className="mb-2 flex flex-wrap items-center justify-between gap-2 text-xs font-semibold text-muted-foreground print:text-gray-600">
      <span>{message.role === 'user' ? 'Question' : 'Reading'}</span>
      {savedAt && <time dateTime={savedAt} className="font-normal">Saved {savedAt.replace('T', ' ').replace('Z', ' UTC')}</time>}
    </p>
    {message.parts.filter(p => p.type === 'text').map((part, i) => <div key={i} className="prose prose-invert max-w-none print:prose-neutral"><ReactMarkdown remarkPlugins={[remarkGfm]}>{part.text}</ReactMarkdown></div>)}
    {message.parts.filter(p => p.type === 'reasoning').map((part, i) => <details key={`r${i}`} className="mt-3 text-sm"><summary>Reasoning</summary><ReactMarkdown>{part.text}</ReactMarkdown></details>)}
  </section>})}</div>
}

export function PrintReadingButton() {
  return <button type="button" onClick={() => window.print()} className="mb-6 rounded-md border border-border px-3 py-2 text-sm print:hidden">Print / Save PDF</button>
}
