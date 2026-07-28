/**
 * Paripraśna durable conversation summaries — PB-2 (SMṚTI) lane M-3 — summarizer worker.
 *
 * `SummarizerWorker` (types.ts) is the family-worker interface; `LlmSummarizerWorker`
 * is the ONE concrete implementation live today. The codebase's existing
 * provider-family abstraction is the 5-provider adapter dispatcher
 * (`@/lib/providers/dispatcher.ts`, `StackId`), but the cross-provider call
 * shape THAT abstraction's callers actually use for a single, non-agentic,
 * non-streaming text completion is `runAdapter(QueryRequest) ->
 * ModelInteraction` (`@/lib/adapters/run_adapter.ts`) — the exact helper
 * `src/lib/pipeline/prashna_ask_synthesis.ts`'s `synthesizeReading` already
 * uses for its own single-shot LLM call. Reused here rather than re-invented:
 * `runAdapter` already resolves `stack -> provider adapter` under the hood, so
 * `LlmSummarizerWorker` is provider-family-ready via `getEffectiveModel`'s
 * stack routing without this module importing the dispatcher directly. A
 * future second `SummarizerWorker` implementation (a different model family,
 * or a non-LLM extractive summarizer) slots in behind the same
 * `summarize(input): Promise<string>` call shape.
 *
 * `callType: 'worker'` is the exact CallType the registry's own doc comment
 * names for this job: "title generation, HISTORY SUMMARIZATION, any call
 * where minimal latency and minimal cost dominate" (`@/lib/models/registry.ts`).
 */
import 'server-only'

import { runAdapter } from '@/lib/adapters/run_adapter'
import type { QueryRequest } from '@/lib/adapters/types'
import { getEffectiveModel } from '@/lib/models/runtime_config'
import { DEFAULT_STACK_ID } from '@/lib/models/registry'
import type { SummarizeInput, SummarizerWorker } from './types'

const SUMMARY_SYSTEM_PROMPT =
  `You are compressing the earlier turns of an in-progress Jyotish consultation ` +
  `into a compact, faithful summary for a synthesis model's context window. Rules:\n` +
  `- Preserve the substance of every "consulted <label> -> <result>" line (what ` +
  `was checked and what was found), condensed, never fabricated.\n` +
  `- Do not invent facts, numbers, dates, or citations that are not present in the input.\n` +
  `- Do not drop a citation reference (e.g. "SIG.MSR.042") if you choose to mention it — ` +
  `write it exactly as given. (Citation survival is also enforced independently of this call.)\n` +
  `- Output plain prose only, no headers or bullet lists, roughly 150-300 words.`

export class LlmSummarizerWorker implements SummarizerWorker {
  private modelIdUsed: string | null = null

  async summarize(input: SummarizeInput): Promise<string> {
    const modelId = await getEffectiveModel(DEFAULT_STACK_ID, 'worker', 'primary')
    this.modelIdUsed = modelId

    const req: QueryRequest = {
      callType: 'worker',
      modelOverride: { modelId },
      systemPrompt: SUMMARY_SYSTEM_PROMPT,
      messages: [
        {
          role: 'user',
          content: input.renderedText.trim() || '(no prior turns to summarize)',
        },
      ],
      traceId: input.conversationId,
    }

    const interaction = await runAdapter(req)
    return interaction.finalText?.trim() ?? ''
  }

  lastModelId(): string | null {
    return this.modelIdUsed
  }
}
