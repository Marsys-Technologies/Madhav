import 'server-only'
import { z } from 'zod'
import { AiConsoleError } from '../errors'
import { validateCliModelId, type CliModelCatalogFormat } from './registry'

export interface CliDiscoveredModel {
  readonly modelId: string
  readonly displayName: string
  readonly supportedEfforts?: readonly string[]
  readonly defaultEffort?: string | null
  readonly isCatalogDiscovered?: boolean
  readonly isDefault?: boolean
}

const DisplayNameSchema = z.string().trim().min(1).max(120).refine(value => !/[\u0000-\u001f\u007f]/.test(value))
export const DiscoveredCliModelSchema = z.object({
  modelId: z.string().min(1).max(512).refine(value => !value.startsWith('-')
    && !/[\u0000-\u001f\u007f]/.test(value)), displayName: DisplayNameSchema,
  supportedEfforts: z.array(z.string().regex(/^[a-z][a-z0-9_]{0,31}$/)).max(16).optional(),
  defaultEffort: z.string().regex(/^[a-z][a-z0-9_]{0,31}$/).nullable().optional(),
  isCatalogDiscovered: z.boolean().optional(), isDefault: z.boolean().optional(),
}).strict().superRefine((model, ctx) => {
  if (model.defaultEffort && !model.supportedEfforts?.includes(model.defaultEffort)) {
    ctx.addIssue({ code: 'custom', message: 'Default effort is not supported' })
  }
  if (model.supportedEfforts && new Set(model.supportedEfforts).size !== model.supportedEfforts.length) {
    ctx.addIssue({ code: 'custom', message: 'Duplicate effort' })
  }
})
const KimiCatalogSchema = z.object({
  providers: z.record(z.string(), z.unknown()),
  models: z.record(z.string(), z.object({
    provider: z.string(),
    model: z.string(),
    displayName: z.string(),
  }).passthrough()),
}).passthrough()

export function parseCliModelCatalog(format: CliModelCatalogFormat, stdout: string): CliDiscoveredModel[] {
  let models: CliDiscoveredModel[]
  if (format === 'antigravity_models') {
    models = stdout.split(/\r?\n/).filter(Boolean).map(line => {
      const fields = line.split('\t')
      if (fields.length !== 2) throw new AiConsoleError('AI_EXECUTION_FAILED')
      return safeModel(fields[0], fields[1])
    })
  } else if (format === 'codex_app_server' || format === 'claude_control') {
    let raw: unknown
    try { raw = JSON.parse(stdout) } catch { throw new AiConsoleError('AI_EXECUTION_FAILED') }
    const parsed = z.array(DiscoveredCliModelSchema).min(1).max(100).safeParse(raw)
    if (!parsed.success) throw new AiConsoleError('AI_EXECUTION_FAILED')
    models = parsed.data.map(model => ({ ...model, ...safeModel(model.modelId, model.displayName) }))
  } else {
    let raw: unknown
    try { raw = JSON.parse(stdout) } catch { throw new AiConsoleError('AI_EXECUTION_FAILED') }
    const parsed = KimiCatalogSchema.safeParse(raw)
    if (!parsed.success) throw new AiConsoleError('AI_EXECUTION_FAILED')
    const managedProvider = parsed.data.providers['managed:kimi-code']
    if (!managedProvider || typeof managedProvider !== 'object') throw new AiConsoleError('AI_EXECUTION_FAILED')
    models = Object.entries(parsed.data.models)
      .filter(([, value]) => value.provider === 'managed:kimi-code')
      .map(([modelId, value]) => safeModel(modelId, value.displayName))
  }
  if (models.length === 0 || models.length > 100) throw new AiConsoleError('AI_EXECUTION_FAILED')
  const ids = new Set(models.map(model => model.modelId))
  if (ids.size !== models.length) throw new AiConsoleError('AI_EXECUTION_FAILED')
  return models
}

function safeModel(modelId: string, displayName: string): CliDiscoveredModel {
  const safeId = validateCliModelId(modelId)
  const safeName = DisplayNameSchema.safeParse(displayName)
  if (!safeId || !safeName.success) throw new AiConsoleError('AI_EXECUTION_FAILED')
  return Object.freeze({ modelId: safeId, displayName: safeName.data })
}
