'use client'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { UIMessage } from 'ai'

export function ReadingView({ messages }: { messages: UIMessage[] }) {
  return <div className="space-y-6">{messages.map(message => <section key={message.id} className="break-inside-avoid">
    <p className="mb-2 text-xs font-semibold text-muted-foreground print:text-gray-600">{message.role === 'user' ? 'Question' : 'Reading'}</p>
    {message.parts.filter(p => p.type === 'text').map((part, i) => <div key={i} className="prose prose-invert max-w-none print:prose-neutral"><ReactMarkdown remarkPlugins={[remarkGfm]}>{part.text}</ReactMarkdown></div>)}
    {message.parts.filter(p => p.type === 'reasoning').map((part, i) => <details key={`r${i}`} className="mt-3 text-sm"><summary>Reasoning</summary><ReactMarkdown>{part.text}</ReactMarkdown></details>)}
  </section>)}</div>
}

export function PrintReadingButton() {
  return <button type="button" onClick={() => window.print()} className="mb-6 rounded-md border border-border px-3 py-2 text-sm print:hidden">Print / Save PDF</button>
}
