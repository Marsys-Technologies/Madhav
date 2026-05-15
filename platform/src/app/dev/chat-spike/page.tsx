'use client'

/**
 * α0 assistant-ui fit-spike page.
 * Minimal Thread mount against /api/chat/spike to verify assistant-ui works
 * with MARSYS's edge-case requirements (reasoning, math, code, citations, scroll).
 *
 * Auth is enforced by /dev/layout.tsx (super-admin server check).
 *
 * Path deviation from brief: brief specified _dev/chat-spike but _-prefix
 * folders are private (non-routable) in Next.js App Router. Using /dev/chat-spike.
 */

import { AssistantRuntimeProvider } from '@assistant-ui/react'
import { useChatRuntime } from '@assistant-ui/react-ai-sdk'
import { DefaultChatTransport } from 'ai'
import { ChatSpikeThread } from '@/components/chat-v2/spike/ChatSpikeThread'

export default function ChatSpikePage() {
  const runtime = useChatRuntime({
    transport: new DefaultChatTransport({ api: '/api/chat/spike' }),
  })

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div
        className="flex h-screen flex-col bg-zinc-950 text-zinc-100"
        data-testid="chat-spike-root"
      >
        <header className="flex items-center gap-3 border-b border-zinc-800 px-6 py-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded border border-amber-400/20">
              DEV
            </span>
            <h1 className="text-sm font-semibold text-zinc-100">
              assistant-ui fit-spike — α0
            </h1>
          </div>
          <span className="ml-auto text-xs text-zinc-500">
            /api/chat/spike · fixture mode
          </span>
        </header>

        <main className="flex-1 overflow-hidden">
          <ChatSpikeThread />
        </main>
      </div>
    </AssistantRuntimeProvider>
  )
}
