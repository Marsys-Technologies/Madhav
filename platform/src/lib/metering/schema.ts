import { z } from 'zod'
const Id = z.string().min(1).max(512).regex(/^[^\u0000-\u001f]+$/)
const Count = z.number().int().nonnegative().max(Number.MAX_SAFE_INTEGER).nullable()
const Time = z.string().datetime({ offset: true })
const RawCount = z.number().int().nonnegative().max(Number.MAX_SAFE_INTEGER)
const RawKeys = z.enum(['input_tokens','output_tokens','prompt_tokens','completion_tokens','total_tokens',
  'cache_read_input_tokens','cache_creation_input_tokens','promptTokenCount','candidatesTokenCount',
  'cachedContentTokenCount','thoughtsTokenCount','totalTokenCount','reasoning_tokens','cached_tokens',
  'accepted_prediction_tokens','rejected_prediction_tokens','audio_tokens','text_tokens','cache_write_tokens',
  'ephemeral_5m_input_tokens','ephemeral_1h_input_tokens'])
const Raw = z.object({ prompt_tokens_details: z.record(RawKeys, RawCount).optional(),
  completion_tokens_details: z.record(RawKeys, RawCount).optional(), cache_creation: z.record(RawKeys, RawCount).optional() })
  .catchall(RawCount).superRefine((value, ctx) => {
    const allowed = new Set([...RawKeys.options,'prompt_tokens_details','completion_tokens_details','cache_creation'])
    if (Object.keys(value).some(k => !allowed.has(k as never))) ctx.addIssue({ code: 'custom', message: 'Unexpected usage key' })
  })
export const UsageEvidenceSchema = z.object({ input: Count, uncachedInput: Count, cacheRead: Count,
  cacheWrite: Count, output: Count, textOutput: Count, reasoning: Count,
  source: z.enum(['provider_reported','client_reported','legacy_reported','unavailable']), raw: Raw,
  issues: z.array(z.string().max(100).regex(/^[a-z_]+$/)).max(30) }).strict()
export const AttemptStartSchema = z.object({
  attemptId: z.string().uuid(), startedAt: Time, userId: Id, conversationId: Id.nullable(), turnId: Id,
  operationId: Id, parentOperationId: Id.nullish(), channel: z.enum(['web','mcp','api','backend','scheduled','unknown']),
  purpose: z.enum(['customer','admin_test','validation','evaluation','background','legacy']),
  payer: z.enum(['user','platform','subscription','unknown']), provider: Id.max(64), model: Id.max(256), role: Id.max(64),
  connectionId: Id.nullish(), snapshotId: Id.nullish(), testRunId: Id.nullish(), requestedModel: Id.max(256).nullish(),
  aggregation: z.enum(['transport','cli_aggregate','legacy_aggregate']) }).strict()
export const AttemptReceiptSchema = z.object({ attemptId: z.string().uuid(), finishedAt: Time,
  status: z.enum(['success','error','timeout','cancelled','incomplete']), usage: UsageEvidenceSchema,
  providerRequestId: z.string().max(256).regex(/^[\w.:/-]+$/).nullable(),
  finishReason: z.string().max(256).regex(/^[\w.:/-]+$/).nullable(), firstTokenAt: Time.nullable(),
  providerCostUsd: z.string().max(30).regex(/^\d{1,18}(\.\d{1,12})?$/).nullable() }).strict()
export const RecoveryEnvelopeSchema = z.object({ version: z.literal(1), start: AttemptStartSchema, receipt: AttemptReceiptSchema }).strict()
  .superRefine((v,ctx) => { if (v.start.attemptId !== v.receipt.attemptId) ctx.addIssue({ code: 'custom', message: 'Identity mismatch' }) })
