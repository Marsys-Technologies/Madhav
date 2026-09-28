import { lstat, realpath, readFile } from 'node:fs/promises'
import { isIP } from 'node:net'
import { isAbsolute, relative, resolve, sep } from 'node:path'
import { z } from 'zod'

const ProviderIdSchema = z.enum(['openai', 'anthropic', 'google', 'xai', 'deepseek', 'kimi', 'openrouter'])
const CliIdSchema = z.enum(['codex', 'claude_code', 'gemini_antigravity', 'kimi_code'])
const SecretSchema = z.object({ apiKey: z.string().min(1), preferredModel: z.string().min(1).optional() }).strict()
const LoopbackUrlSchema = z.string().min(1)

export const OwnerConfigSchema = z.object({
  userId: z.string().min(1),
  conversationId: z.string().uuid(),
  pariprashnaPath: z.string().startsWith('/'),
  providers: z.partialRecord(ProviderIdSchema, SecretSchema),
  sameProvider: z.object({ providerId: ProviderIdSchema, first: SecretSchema, second: SecretSchema }).strict(),
  pariprashnaRequest: z.record(z.string(), z.unknown()).refine(value =>
    typeof value.chartId === 'string' && Array.isArray(value.messages)
      && !('conversationId' in value) && !('ai_selection' in value)),
  consultRequest: z.record(z.string(), z.unknown()),
  inspection: z.object({
    identityUrl: LoopbackUrlSchema,
    routingEvidenceUrlTemplate: z.string().includes('{turnId}'),
    latestEvidenceUrl: LoopbackUrlSchema,
  }).strict(),
  leakage: z.object({
    serverLogPath: z.string().min(1),
    routingSnapshotPath: z.string().min(1),
    observatoryPath: z.string().min(1),
    auditPath: z.string().min(1),
    artifactDirectory: z.string().min(1),
    urls: z.array(LoopbackUrlSchema).min(1),
  }).strict(),
  mcp: z.object({ url: LoopbackUrlSchema, headers: z.record(z.string(), z.string()), request: z.record(z.string(), z.unknown()) }).strict().optional(),
  cliModels: z.partialRecord(CliIdSchema, z.string().nullable()).optional(),
}).strict()

export type OwnerConfig = z.infer<typeof OwnerConfigSchema>
export type OwnerFixturePreflight =
  | { readonly ok: true; readonly path: string; readonly config: OwnerConfig }
  | { readonly ok: false; readonly code: string }

function isWithin(parent: string, child: string): boolean {
  const value = relative(parent, child)
  return value === '' || (!value.startsWith(`..${sep}`) && value !== '..' && !isAbsolute(value))
}

function loopbackHostname(hostname: string): boolean {
  const unwrapped = hostname.startsWith('[') && hostname.endsWith(']') ? hostname.slice(1, -1) : hostname
  if (unwrapped.toLowerCase() === 'localhost' || unwrapped === '::1') return true
  return isIP(unwrapped) === 4 && unwrapped.split('.')[0] === '127'
}

export function parseLoopbackHttpUrl(value: string, originOnly = false): URL | null {
  try {
    const parsed = new URL(value)
    if (!['http:', 'https:'].includes(parsed.protocol) || !loopbackHostname(parsed.hostname)
      || parsed.username || parsed.password) return null
    if (originOnly && (parsed.pathname !== '/' || parsed.search || parsed.hash)) return null
    return parsed
  } catch { return null }
}

async function privatePath(path: string, repoRoot: string, kind: 'file' | 'directory'): Promise<string | null> {
  if (!isAbsolute(path)) return null
  let direct
  try { direct = await lstat(path) } catch { return null }
  if (direct.isSymbolicLink() || (kind === 'file' ? !direct.isFile() : !direct.isDirectory())) return null
  if ((direct.mode & 0o077) !== 0) return null
  if (typeof process.getuid === 'function' && direct.uid !== process.getuid()) return null
  let canonical: string
  try { canonical = await realpath(path) } catch { return null }
  return isWithin(repoRoot, canonical) ? null : canonical
}

export async function preflightOwnerFixture(
  path: string,
  options: { readonly platformRoot: string; readonly baseUrl: string },
): Promise<OwnerFixturePreflight> {
  if (!parseLoopbackHttpUrl(options.baseUrl, true)) {
    return { ok: false, code: 'AIC_ACCEPTANCE_BASE_URL_NOT_LOOPBACK' }
  }
  if (!path || !isAbsolute(path)) return { ok: false, code: 'AIC_ACCEPTANCE_OWNER_FIXTURE_MISSING' }
  let direct
  try { direct = await lstat(path) } catch { return { ok: false, code: 'AIC_ACCEPTANCE_OWNER_FIXTURE_MISSING' } }
  if (direct.isSymbolicLink()) return { ok: false, code: 'AIC_ACCEPTANCE_OWNER_FIXTURE_SYMLINK' }
  if (!direct.isFile()) return { ok: false, code: 'AIC_ACCEPTANCE_OWNER_FIXTURE_INVALID' }
  if ((direct.mode & 0o077) !== 0 || (typeof process.getuid === 'function' && direct.uid !== process.getuid())) {
    return { ok: false, code: 'AIC_ACCEPTANCE_OWNER_FIXTURE_PERMISSIONS' }
  }

  const unresolvedRepoRoot = resolve(options.platformRoot, '..')
  const repoRoot = await realpath(unresolvedRepoRoot).catch(() => unresolvedRepoRoot)
  let canonical: string
  try { canonical = await realpath(path) } catch { return { ok: false, code: 'AIC_ACCEPTANCE_OWNER_FIXTURE_INVALID' } }
  if (isWithin(repoRoot, canonical)) return { ok: false, code: 'AIC_ACCEPTANCE_OWNER_FIXTURE_IN_REPOSITORY' }

  let unknownConfig: unknown
  try { unknownConfig = JSON.parse(await readFile(canonical, 'utf8')) } catch {
    return { ok: false, code: 'AIC_ACCEPTANCE_OWNER_FIXTURE_INVALID' }
  }
  const parsed = OwnerConfigSchema.safeParse(unknownConfig)
  if (!parsed.success) return { ok: false, code: 'AIC_ACCEPTANCE_OWNER_FIXTURE_INVALID' }
  const config = parsed.data
  const endpointValues = [config.inspection.identityUrl, config.inspection.latestEvidenceUrl,
    config.inspection.routingEvidenceUrlTemplate.replace('{turnId}', '10000000-0000-4000-8000-000000000001'),
    ...config.leakage.urls, ...(config.mcp ? [config.mcp.url] : [])]
  if (endpointValues.some(value => !parseLoopbackHttpUrl(value))) {
    return { ok: false, code: 'AIC_ACCEPTANCE_OWNER_FIXTURE_INVALID' }
  }
  const leakageFiles = [config.leakage.serverLogPath, config.leakage.routingSnapshotPath,
    config.leakage.observatoryPath, config.leakage.auditPath]
  for (const required of leakageFiles) {
    if (!await privatePath(required, repoRoot, 'file')) {
      return { ok: false, code: 'AIC_ACCEPTANCE_LEAKAGE_INPUT_INVALID' }
    }
  }
  const artifactDirectory = await privatePath(config.leakage.artifactDirectory, repoRoot, 'directory')
  if (!artifactDirectory) {
    return { ok: false, code: 'AIC_ACCEPTANCE_LEAKAGE_INPUT_INVALID' }
  }
  if (isWithin(artifactDirectory, canonical)) {
    return { ok: false, code: 'AIC_ACCEPTANCE_OWNER_FIXTURE_IN_ARTIFACTS' }
  }
  return { ok: true, path: canonical, config }
}
