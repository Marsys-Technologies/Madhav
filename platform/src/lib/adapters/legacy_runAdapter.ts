/**
 * Legacy adapter path — active when ADAPTERS_ENABLED=false (default through AD.4).
 *
 * Replicates the old streamText + resolveModel + providerOptions pattern that
 * existed at call sites before AD.4 migrated them to runAdapter/streamAdapterRaw.
 * Behaviorally byte-identical to the pre-migration code path; equivalence tests
 * assert this. Scheduled for deletion 2 weeks after AD.5 flag flip stabilises.
 */
import 'server-only'
import { streamText, stepCountIs, smoothStream, jsonSchema, type StreamTextResult } from 'ai'
import type { QueryRequest, ModelInteraction } from './types'
import type { ModelMeta } from '@/lib/models/registry'
import type { RawAdapterResult } from './raw'
import { resolveModel, deepseekProviderOptions, googleProviderOptions } from '@/lib/models/resolver'
import { getModelMeta, DEFAULT_STACK_ID, DEFAULT_MODEL_ID, STACK_ROUTING } from '@/lib/models/registry'

// ── Model resolution (mirrors stream_adapter resolveModelId) ─────────────────

function resolveModelId(req: QueryRequest): string {
  if (req.modelOverride) return req.modelOverride.modelId
  const stack = req.stack ?? DEFAULT_STACK_ID
  return STACK_ROUTING[stack]?.[req.callType]?.primary ?? DEFAULT_MODEL_ID
}

// ── Provider options (same as the old call-site pattern) ─────────────────────

function buildProviderOptions(modelId: string): Record<string, unknown> | undefined {
  const google = googleProviderOptions(modelId)
  const deepseek = deepseekProviderOptions(modelId, 'synthesis')
  const merged: Record<string, unknown> = {}
  if (google?.google) merged.google = google.google
  if (deepseek?.deepseek) merged.deepseek = deepseek.deepseek
  return Object.keys(merged).length > 0 ? merged : undefined
}

// ── Tool conversion ───────────────────────────────────────────────────────────

function buildTools(req: QueryRequest): Record<string, unknown> | undefined {
  if (!req.tools?.length) return undefined
  return Object.fromEntries(
    req.tools.map(t => [
      t.name,
      {
        description: t.description,
        parameters: jsonSchema(t.parameters as Record<string, unknown>),
      },
    ]),
  )
}

// ── Finish-reason normalisation ───────────────────────────────────────────────

function mapFinishReason(reason: string): ModelInteraction['finishReason'] {
  if (reason === 'length') return 'length'
  if (reason === 'tool-calls') return 'tool_calls'
  if (reason === 'content-filter') return 'content_filter'
  if (reason === 'error') return 'error'
  return 'stop'
}

// ── runAdapterLegacy ──────────────────────────────────────────────────────────

export async function runAdapterLegacy(req: QueryRequest): Promise<ModelInteraction> {
  const modelId = resolveModelId(req)
  const meta = getModelMeta(modelId)
  if (!meta) throw new Error(`runAdapterLegacy: unknown model ${modelId}`)

  const providerOptions = buildProviderOptions(modelId)
  const tools = buildTools(req)

  const controller = req.timeoutMs ? new AbortController() : undefined
  let timer: ReturnType<typeof setTimeout> | undefined
  if (controller && req.timeoutMs) {
    timer = setTimeout(() => controller.abort(), req.timeoutMs)
  }

  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const streamResult = streamText({
      model: resolveModel(modelId),
      system: req.systemPrompt,
      messages: req.messages as any,
      maxOutputTokens: req.maxOutputTokens ?? meta.maxOutputTokens,
      temperature: req.temperature,
      tools: tools as any,
      toolChoice: req.toolChoice as any,
      stopWhen: req.multiStep ? stepCountIs(req.multiStep.maxSteps) : undefined,
      experimental_transform: req.smoothStream ? smoothStream() : undefined,
      onStepFinish: req.onStepFinish as ((step: unknown) => Promise<void> | void) | undefined,
      onFinish: req.rawOnFinish as ((result: unknown) => Promise<void> | void) | undefined,
      ...(providerOptions && { providerOptions }),
      ...(req.disableSdkRetry && { maxRetries: 0 }),
      ...(controller && { abortSignal: controller.signal }),
    } as any)

    // Collect the stream into a ModelInteraction
    const startMs = Date.now()
    let finalText = ''
    const intermediate: ModelInteraction['intermediate'] = []
    let finishedInteraction: Partial<ModelInteraction> = {}

    for await (const part of streamResult.fullStream) {
      if (part.type === 'text-delta') {
        finalText += part.text
      } else if (part.type === 'tool-call') {
        intermediate.push({
          type: 'tool_call',
          ts: Date.now(),
          payload: {
            type: 'tool_call',
            ts: Date.now(),
            name: part.toolName,
            args: part.input,
            callId: part.toolCallId,
          },
        })
      } else if (part.type === 'finish') {
        const usage = part.totalUsage
        const inp = usage?.inputTokens ?? 0
        const out = usage?.outputTokens ?? 0
        finishedInteraction = {
          finishReason: mapFinishReason(part.finishReason),
          usage: {
            inputTokens: inp,
            outputTokens: out,
            costUsd: (inp * meta.costPer1MInput + out * meta.costPer1MOutput) / 1_000_000,
            latencyMs: Date.now() - startMs,
          },
        }
      }
    }

    return {
      modelId,
      provider: meta.provider,
      intermediate,
      finalText: finalText || undefined,
      finishReason: (finishedInteraction.finishReason as ModelInteraction['finishReason']) ?? 'stop',
      usage: finishedInteraction.usage ?? {
        inputTokens: 0,
        outputTokens: 0,
        costUsd: 0,
        latencyMs: Date.now() - startMs,
      },
      providerMeta: {},
    }
  } finally {
    if (timer) clearTimeout(timer)
  }
}

// ── streamAdapterRawLegacy ────────────────────────────────────────────────────

export function streamAdapterRawLegacy(req: QueryRequest): RawAdapterResult {
  const modelId = resolveModelId(req)
  const meta = getModelMeta(modelId)
  if (!meta) throw new Error(`streamAdapterRawLegacy: unknown model ${modelId}`)

  const providerOptions = buildProviderOptions(modelId)
  const tools = buildTools(req)

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const result: StreamTextResult<any, any> = streamText({
    model: resolveModel(modelId),
    system: req.systemPrompt,
    messages: req.messages as any,
    maxOutputTokens: req.maxOutputTokens ?? meta.maxOutputTokens,
    temperature: req.temperature,
    tools: tools as any,
    toolChoice: req.toolChoice as any,
    stopWhen: req.multiStep ? stepCountIs(req.multiStep.maxSteps) : undefined,
    experimental_transform: req.smoothStream ? smoothStream() : undefined,
    onStepFinish: req.onStepFinish as ((step: unknown) => Promise<void> | void) | undefined,
    onFinish: req.rawOnFinish as ((result: unknown) => Promise<void> | void) | undefined,
    ...(providerOptions && { providerOptions }),
    ...(req.disableSdkRetry && { maxRetries: 0 }),
  } as any)

  return { result, meta }
}
