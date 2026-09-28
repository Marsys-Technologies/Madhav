import 'server-only'
import { z } from 'zod'
import { AiConsoleError } from '../errors'
import { validateCliModelId, type CliModelCatalogFormat } from './registry'

export interface CliDiscoveredModel {
  readonly modelId: string
  readonly displayName: string
}

const DisplayNameSchema = z.string().trim().min(1).max(256)
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
