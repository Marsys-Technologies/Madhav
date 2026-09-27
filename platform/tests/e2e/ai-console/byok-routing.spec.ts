import { readFile, readdir } from 'node:fs/promises'
import { basename, join } from 'node:path'
import { expect, test, type APIRequestContext, type BrowserContext, type TestInfo } from '@playwright/test'
import { preflightOwnerFixture, type OwnerConfig } from '../../../scripts/ai-console/owner_preflight'
import { captureLeakageBaseline, containsForbiddenLeakage, readFreshLeakageEvidence,
  type LeakageBaseline } from '../../../scripts/ai-console/leakage_evidence'
import { requestWithValidationThrottle } from '../../../scripts/ai-console/validation_scheduler'
import {
  assertSafeRoutingEvidence, assertStableAcceptanceNamespaceClean, parseConsultTerminal, parsePariprashnaTerminal,
  type SafeRoleMap, type SafeRoleTarget, type SafeSelection,
} from '../../../scripts/ai-console/e2e_evidence'

type ProviderId = 'openai' | 'anthropic' | 'google' | 'xai' | 'deepseek' | 'kimi' | 'openrouter'
type CliId = 'codex' | 'claude_code' | 'gemini_antigravity' | 'kimi_code'
type Choice = { kind: 'provider_model'; connectionId: string; modelId: string }
  | { kind: 'custom_configuration'; configurationId: string }
  | { kind: 'local_cli'; cliId: CliId; modelId: string | null }
type ProviderSecret = { apiKey: string; preferredModel?: string }
interface ConsoleState {
  connections: Array<{ id: string; name: string; providerId: ProviderId; validationState: string; confirmedValid: boolean; deletedAt: string | null }>
  models: Array<{ connectionId: string; modelId: string; available: boolean; compatibleRoles: string[] }>
  configurations: Array<{ id: string; name: string; version: number; deletedAt: string | null }>
  defaultChoice: Choice | null
}
interface RestoreState {
  defaultChoice: Choice
  conversationSelection?: SafeSelection
  grants?: Map<CliId, boolean>
}

const BASE_URL = process.env.AI_CONSOLE_E2E_BASE_URL ?? 'http://localhost:3000'
const SESSION_COOKIE = process.env.SMOKE_SESSION_COOKIE
const CONFIG_PATH = process.env.AI_CONSOLE_E2E_OWNER_CONFIG_PATH
const ENV_READY = process.env.MARSYS_FLAG_AI_CONSOLE_BYOK === 'true'
  && process.env.NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK === 'true'
  && process.env.AI_CONSOLE_E2E_EXTERNAL_SERVER === 'true'
  && Boolean(SESSION_COOKIE) && Boolean(CONFIG_PATH)
const PROVIDER_AUTHORIZED = process.env.AI_CONSOLE_PROVIDER_SMOKE_AUTHORIZED === 'true'
const CLI_AUTHORIZED = process.env.AI_CONSOLE_CLI_SMOKE_AUTHORIZED === 'true'
const PREFIX = 'AIC acceptance '
const providerCases: Array<{ label: string; id: ProviderId }> = [
  { label: 'openai', id: 'openai' }, { label: 'anthropic', id: 'anthropic' },
  { label: 'gemini', id: 'google' }, { label: 'xai', id: 'xai' },
  { label: 'deepseek', id: 'deepseek' }, { label: 'kimi', id: 'kimi' },
  { label: 'openrouter', id: 'openrouter' },
]
const cliCases: Array<{ label: string; id: CliId }> = [
  { label: 'codex', id: 'codex' }, { label: 'claude-code', id: 'claude_code' },
  { label: 'gemini-antigravity', id: 'gemini_antigravity' }, { label: 'kimi-code', id: 'kimi_code' },
]

let owner: OwnerConfig | undefined
let fixtureCode = 'AIC_ACCEPTANCE_OWNER_FIXTURE_MISSING'
let restore: RestoreState | undefined
let currentPrefix: string | undefined
let runStartedAtMs = 0
let leakageBaselines: LeakageBaseline[] = []
const createdConnectionIds = new Set<string>()
const createdConfigurationIds = new Set<string>()
const turnCorrelationMarkers = new Set<string>()
const auditCorrelationMarkers = new Set<string>()

test.use({ trace: 'off', screenshot: 'off', video: 'off' })
test.describe.configure({ mode: 'serial' })

function configuredOwner(): OwnerConfig {
  test.skip(!owner, `UNQUALIFIED: ${fixtureCode}`)
  return owner!
}
function expectedOrigin(path: string): string { return new URL(path, BASE_URL).origin }
async function fetchNoRedirect(request: APIRequestContext, path: string, init?: Parameters<APIRequestContext['fetch']>[1]) {
  const response = await request.fetch(path, { ...init, maxRedirects: 0 })
  if (new URL(response.url()).origin !== expectedOrigin(path)) throw new Error('AIC_E2E_CROSS_ORIGIN_RESPONSE')
  return response
}
async function json<T>(request: APIRequestContext, path: string, init?: Parameters<APIRequestContext['fetch']>[1]): Promise<T> {
  const response = await fetchNoRedirect(request, path, init)
  if (!response.ok()) throw new Error(`AIC_E2E_HTTP_${response.status()}`)
  try { return await response.json() as T } catch { throw new Error('AIC_E2E_RESPONSE_INVALID') }
}
async function authenticate(context: BrowserContext) {
  await context.addCookies([{ name: '__session', value: SESSION_COOKIE!, url: BASE_URL, httpOnly: true, sameSite: 'Lax' }])
}
async function state(request: APIRequestContext) { return json<ConsoleState>(request, '/api/ai-console') }
async function assertIdentity(request: APIRequestContext, config: OwnerConfig) {
  expect(await json<{ userId: string }>(request, config.inspection.identityUrl)).toEqual({ userId: config.userId })
}

async function createConnection(request: APIRequestContext, providerId: ProviderId, secret: ProviderSecret, name: string) {
  const response = await requestWithValidationThrottle(() => fetchNoRedirect(request, '/api/ai-console/connections', {
    method: 'POST', data: { name, providerId, apiKey: secret.apiKey, acknowledgeCharge: true },
  }))
  if (!response.ok()) throw new Error(`AIC_E2E_HTTP_${response.status()}`)
  let created: { connection: { id: string }; validation: { state: string } }
  try { created = await response.json() as typeof created } catch { throw new Error('AIC_E2E_RESPONSE_INVALID') }
  createdConnectionIds.add(created.connection.id)
  auditCorrelationMarkers.add(created.connection.id)
  expect(created.validation.state).toBe('validated')
  const candidates = (await state(request)).models.filter(model => model.connectionId === created.connection.id && model.available
    && ['synthesizer', 'planner', 'deep_planner', 'worker'].every(role => model.compatibleRoles.includes(role)))
  const model = secret.preferredModel ? candidates.find(candidate => candidate.modelId === secret.preferredModel) : candidates[0]
  expect(model, 'validated connection must expose one all-role compatible model').toBeTruthy()
  return { connectionId: created.connection.id, providerId, modelId: model!.modelId, name }
}
async function setDefault(request: APIRequestContext, choice: Choice) {
  await json(request, '/api/ai-console/default', { method: 'PUT', data: { choice } })
}
async function setConversation(request: APIRequestContext, selection: SafeSelection) {
  return json<{ selection: SafeSelection; availability: string; label: string; resolvedLabel: string | null }>(request,
    `/api/conversations/${configuredOwner().conversationId}/ai-selection`, { method: 'PUT', data: selection })
}
async function pollEvidence(request: APIRequestContext, path: string, expected: Parameters<typeof assertSafeRoutingEvidence>[1]) {
  for (let attempt = 0; attempt < 40; attempt += 1) {
    const response = await fetchNoRedirect(request, path)
    if (response.ok()) {
      try {
        const evidence = await response.json() as unknown
        assertSafeRoutingEvidence(evidence, expected)
        return evidence
      } catch { /* bounded retry for asynchronous Observatory persistence */ }
    }
    await new Promise(resolve => setTimeout(resolve, 250))
  }
  throw new Error('AIC_E2E_ROUTING_EVIDENCE_TIMEOUT')
}
async function runNativeTurn(request: APIRequestContext, selection: SafeSelection, resolvedChoice: Choice, roles: SafeRoleMap) {
  const config = configuredOwner()
  await setConversation(request, selection)
  const response = await fetchNoRedirect(request, '/api/pariprashna', {
    method: 'POST', data: { ...config.pariprashnaRequest, conversationId: config.conversationId, ai_selection: selection },
  })
  if (!response.ok()) throw new Error(`AIC_E2E_HTTP_${response.status()}`)
  const turnId = parsePariprashnaTerminal(await response.text())
  turnCorrelationMarkers.add(turnId)
  const path = config.inspection.routingEvidenceUrlTemplate.replace('{turnId}', encodeURIComponent(turnId))
  await pollEvidence(request, path, { userId: config.userId, correlationId: turnId, selection, resolvedChoice, roles })
  return turnId
}
async function latestEvidence(request: APIRequestContext, after: string, selection: SafeSelection, resolvedChoice: Choice, roles: SafeRoleMap) {
  const config = configuredOwner()
  const url = new URL(config.inspection.latestEvidenceUrl)
  url.searchParams.set('conversationId', config.conversationId)
  url.searchParams.set('after', after)
  for (let attempt = 0; attempt < 40; attempt += 1) {
    const response = await fetchNoRedirect(request, url.toString())
    if (response.ok()) {
      try {
        const evidence = await response.json() as { correlationId?: unknown }
        if (typeof evidence.correlationId === 'string') {
          assertSafeRoutingEvidence(evidence, { userId: config.userId, correlationId: evidence.correlationId, selection, resolvedChoice, roles })
          turnCorrelationMarkers.add(evidence.correlationId)
          return evidence.correlationId
        }
      } catch { /* bounded retry for asynchronous Observatory persistence */ }
    }
    await new Promise(resolve => setTimeout(resolve, 250))
  }
  throw new Error('AIC_E2E_ROUTING_EVIDENCE_TIMEOUT')
}

async function snapshotMutableState(request: APIRequestContext, title: string) {
  const current = await state(request)
  test.skip(!current.defaultChoice, 'UNQUALIFIED: disposable user needs a pre-existing restorable default')
  restore = { defaultChoice: current.defaultChoice! }
  if (title.includes('@routing')) {
    restore.conversationSelection = (await json<{ selection: SafeSelection }>(request,
      `/api/conversations/${configuredOwner().conversationId}/ai-selection`)).selection
  }
  if (title.includes('@cli-')) {
    const grants = await json<{ grants: Array<{ cliId: CliId; granted: boolean }> }>(request,
      `/api/admin/users/${encodeURIComponent(configuredOwner().userId)}/ai-cli-grants`)
    restore.grants = new Map(grants.grants.map(row => [row.cliId, row.granted]))
  }
}
async function cleanup(request: APIRequestContext) {
  const errors: unknown[] = []
  const attempt = async (operation: () => Promise<unknown>) => {
    try { await operation() } catch (error) { errors.push(error) }
  }
  const prefix = currentPrefix
  let discovered: ConsoleState | undefined
  if (prefix) await attempt(async () => { discovered = await state(request) })
  for (const row of discovered?.connections ?? []) if (row.name.startsWith(prefix!)) createdConnectionIds.add(row.id)
  for (const row of discovered?.configurations ?? []) if (row.name.startsWith(prefix!)) createdConfigurationIds.add(row.id)
  if (restore?.conversationSelection) await attempt(() => setConversation(request, restore!.conversationSelection!))
  if (restore?.defaultChoice) await attempt(() => setDefault(request, restore!.defaultChoice))
  if (restore?.grants) {
    for (const [cliId, granted] of restore.grants) {
      await attempt(() => json(request, `/api/admin/users/${encodeURIComponent(configuredOwner().userId)}/ai-cli-grants`, {
        method: 'PATCH', data: { cliId, granted },
      }))
    }
  }
  for (const id of createdConfigurationIds) {
    await attempt(async () => {
      await json(request, `/api/ai-console/configurations/${id}`, { method: 'DELETE', data: { confirm: true } })
      expect((await fetchNoRedirect(request, `/api/ai-console/configurations/${id}`)).status()).toBe(404)
    })
  }
  for (const id of createdConnectionIds) {
    await attempt(async () => {
      await json(request, `/api/ai-console/connections/${id}`, { method: 'DELETE', data: { confirm: true } })
      expect((await fetchNoRedirect(request, `/api/ai-console/connections/${id}`)).status()).toBe(404)
    })
  }
  await attempt(async () => {
    const current = await state(request)
    for (const id of createdConfigurationIds) expect(current.configurations.find(row => row.id === id)?.deletedAt).toBeTruthy()
    for (const id of createdConnectionIds) expect(current.connections.find(row => row.id === id)?.deletedAt).toBeTruthy()
    if (prefix) {
      expect(current.configurations.filter(row => row.name.startsWith(prefix) && !row.deletedAt)).toEqual([])
      expect(current.connections.filter(row => row.name.startsWith(prefix) && !row.deletedAt)).toEqual([])
    }
    assertStableAcceptanceNamespaceClean(current)
  })
  createdConfigurationIds.clear()
  createdConnectionIds.clear()
  restore = undefined
  currentPrefix = undefined
  if (errors.length > 0) throw new Error('AIC_E2E_CLEANUP_FAILED')
}
function providerRoles(target: { providerId: ProviderId; connectionId: string; modelId: string }): SafeRoleMap {
  const roleTarget: SafeRoleTarget = { kind: 'provider_model', ...target }
  return { synthesizer: roleTarget, planner: roleTarget, deep_planner: roleTarget, worker: roleTarget }
}
async function artifactFiles(root: string): Promise<string[]> {
  const files: string[] = []
  for (const entry of await readdir(root, { withFileTypes: true })) {
    const path = join(root, entry.name)
    if (entry.isDirectory()) files.push(...await artifactFiles(path))
    else if (entry.isFile()) files.push(path)
    else throw new Error('AIC_E2E_ARTIFACT_ENTRY_INVALID')
  }
  return files
}

test.describe('AI Console owner-operated local cutover', () => {
  test.skip(!ENV_READY, 'UNQUALIFIED: local flags, authenticated disposable user, and private owner fixture are required')
  test.beforeAll(async () => {
    runStartedAtMs = Date.now()
    const checked = await preflightOwnerFixture(CONFIG_PATH!, { platformRoot: process.cwd(), baseUrl: BASE_URL })
    if (checked.ok && process.env.AI_CONSOLE_E2E_ARTIFACT_DIR === checked.config.leakage.artifactDirectory) {
      owner = checked.config
      leakageBaselines = await Promise.all([checked.config.leakage.serverLogPath, checked.config.leakage.routingSnapshotPath,
        checked.config.leakage.observatoryPath, checked.config.leakage.auditPath].map(captureLeakageBaseline))
    }
    else if (checked.ok) fixtureCode = 'AIC_ACCEPTANCE_LEAKAGE_INPUT_INVALID'
    else fixtureCode = checked.code
  })
  test.beforeEach(async ({ context }, testInfo: TestInfo) => {
    const config = configuredOwner()
    await authenticate(context)
    await assertIdentity(context.request, config)
    const current = await state(context.request)
    assertStableAcceptanceNamespaceClean(current)
    currentPrefix = `${PREFIX}${crypto.randomUUID()} `
    expect(current.connections.filter(row => row.name.startsWith(currentPrefix!))).toEqual([])
    expect(current.configurations.filter(row => row.name.startsWith(currentPrefix!))).toEqual([])
    if (/@routing|@backend|@cli-|@leakage/.test(testInfo.title)) await snapshotMutableState(context.request,
      testInfo.title.includes('@leakage') ? `${testInfo.title} @routing` : testInfo.title)
  })
  test.afterEach(async ({ context }) => { if (owner) await cleanup(context.request) })

  test('@desktop renders the authenticated three-section console without request interception', async ({ page }) => {
    await page.goto('/ai-console')
    await expect(page.getByRole('heading', { level: 1, name: 'AI Console' })).toBeVisible()
    await expect(page.getByRole('heading', { level: 2 })).toHaveText(['Provider connections', 'Custom configurations', 'Local CLIs'])
  })
  test('@mobile keeps the same console hierarchy and operable controls', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/ai-console')
    await expect(page.getByRole('heading', { level: 2 })).toHaveText(['Provider connections', 'Custom configurations', 'Local CLIs'])
    const add = page.getByRole('button', { name: /add connection/i })
    await expect(add).toBeVisible()
    expect((await add.boundingBox())?.height).toBeGreaterThanOrEqual(44)
  })
  for (const provider of providerCases) {
    test(`@provider-${provider.label} validates a real owner-supplied ${provider.label} connection`, async ({ context }) => {
      const config = configuredOwner()
      test.skip(!PROVIDER_AUTHORIZED || !config.providers[provider.id], `UNQUALIFIED: authorized ${provider.label} credential is absent`)
      const created = await createConnection(context.request, provider.id, config.providers[provider.id]!, `${currentPrefix}${provider.label}`)
      expect(created.connectionId).toBeTruthy()
      expect(created.modelId).toBeTruthy()
    })
  }

  test('@routing proves real direct, custom, moved Default, and pinned turns with exact safe evidence', async ({ browser, context }) => {
    const config = configuredOwner()
    test.skip(!PROVIDER_AUTHORIZED, 'UNQUALIFIED: real provider execution was not explicitly authorized')
    const suffix = crypto.randomUUID().slice(0, 8)
    const first = await createConnection(context.request, config.sameProvider.providerId, config.sameProvider.first, `${currentPrefix}first ${suffix}`)
    const second = await createConnection(context.request, config.sameProvider.providerId, config.sameProvider.second, `${currentPrefix}second ${suffix}`)
    const firstChoice: Choice = { kind: 'provider_model', connectionId: first.connectionId, modelId: first.modelId }
    const secondChoice: Choice = { kind: 'provider_model', connectionId: second.connectionId, modelId: second.modelId }
    const firstTarget: SafeRoleTarget = { kind: 'provider_model', providerId: first.providerId, connectionId: first.connectionId, modelId: first.modelId }
    const secondTarget: SafeRoleTarget = { kind: 'provider_model', providerId: second.providerId, connectionId: second.connectionId, modelId: second.modelId }
    const roles = { synthesizer: firstChoice, planner: secondChoice, deep_planner: firstChoice, worker: secondChoice }
    const configuration = await json<{ configuration: { id: string; version: number } }>(context.request, '/api/ai-console/configurations', {
      method: 'POST', data: { name: `${currentPrefix}quartet ${suffix}`, roles },
    })
    createdConfigurationIds.add(configuration.configuration.id)
    auditCorrelationMarkers.add(configuration.configuration.id)
    const configurationChoice: Choice = { kind: 'custom_configuration', configurationId: configuration.configuration.id }
    await runNativeTurn(context.request, { kind: 'explicit', choice: firstChoice }, firstChoice, providerRoles(first))
    await runNativeTurn(context.request, { kind: 'explicit', choice: configurationChoice }, configurationChoice, {
      synthesizer: firstTarget, planner: secondTarget, deep_planner: firstTarget, worker: secondTarget,
    })
    await setDefault(context.request, firstChoice)
    await runNativeTurn(context.request, { kind: 'default' }, firstChoice, providerRoles(first))
    await setDefault(context.request, secondChoice)
    await runNativeTurn(context.request, { kind: 'default' }, secondChoice, providerRoles(second))
    await setConversation(context.request, { kind: 'explicit', choice: firstChoice })
    await runNativeTurn(context.request, { kind: 'explicit', choice: firstChoice }, firstChoice, providerRoles(first))

    const edited = await json<{ configuration: { version: number } }>(context.request,
      `/api/ai-console/configurations/${configuration.configuration.id}`, {
        method: 'PATCH', data: { name: `${currentPrefix}quartet edited ${suffix}`, expectedVersion: configuration.configuration.version,
          roles: { synthesizer: secondChoice, planner: firstChoice, deep_planner: secondChoice, worker: firstChoice } },
      })
    expect(edited.configuration.version).toBe(configuration.configuration.version + 1)
    const duplicate = await json<{ configuration: { id: string } }>(context.request, '/api/ai-console/configurations', {
      method: 'POST', data: { name: `${currentPrefix}quartet copy ${suffix}`, duplicateFrom: configuration.configuration.id },
    })
    createdConfigurationIds.add(duplicate.configuration.id)
    auditCorrelationMarkers.add(duplicate.configuration.id)
    const secondContext = await browser.newContext()
    await authenticate(secondContext)
    try {
      await assertIdentity(secondContext.request, config)
      const persisted = await json<{ selection: SafeSelection }>(secondContext.request,
        `/api/conversations/${config.conversationId}/ai-selection`)
      expect(persisted.selection).toEqual({ kind: 'explicit', choice: firstChoice })
      const page = await secondContext.newPage()
      await page.goto(config.pariprashnaPath)
      await expect(page.getByRole('button', { name: new RegExp(`AI.*${first.name}`, 'i') })).toBeVisible()
    } finally { await secondContext.close() }
  })

  test('@backend consumes a terminal Consult event and exact default routing evidence', async ({ context }) => {
    const config = configuredOwner()
    test.skip(!PROVIDER_AUTHORIZED || !config.providers.openai, 'UNQUALIFIED: authorized OpenAI credential is absent')
    const direct = await createConnection(context.request, 'openai', config.providers.openai!, `${currentPrefix}backend`)
    const choice: Choice = { kind: 'provider_model', connectionId: direct.connectionId, modelId: direct.modelId }
    await setDefault(context.request, choice)
    const after = new Date().toISOString()
    const response = await fetchNoRedirect(context.request, '/api/chat/consult', { method: 'POST', data: config.consultRequest })
    if (!response.ok()) throw new Error(`AIC_E2E_HTTP_${response.status()}`)
    parseConsultTerminal(await response.text())
    await latestEvidence(context.request, after, { kind: 'default' }, choice, providerRoles(direct))
  })
  test('@mcp returns evidence for external synthesis and no Madhav synthesized reading', async ({ context }) => {
    const config = configuredOwner()
    test.skip(!config.mcp, 'UNQUALIFIED: authenticated loopback MCP bridge configuration is absent')
    const response = await fetchNoRedirect(context.request, config.mcp!.url, {
      method: 'POST', headers: config.mcp!.headers, data: config.mcp!.request,
    })
    expect(response.ok()).toBe(true)
    const envelope = await response.json() as Record<string, unknown>
    expect(envelope.schema_version).toBe('madhav.evidence.v1')
    expect(envelope.synthesis).toEqual({ mode: 'external', performed_by_madhav: false })
    expect(envelope).not.toHaveProperty('reading')
  })
  for (const cli of cliCases) {
    test(`@cli-${cli.label} grants, validates, executes to terminal evidence, and restores ${cli.label}`, async ({ context }) => {
      const config = configuredOwner()
      test.skip(!CLI_AUTHORIZED, `UNQUALIFIED: real ${cli.label} subscription execution was not explicitly authorized`)
      await json(context.request, `/api/admin/users/${encodeURIComponent(config.userId)}/ai-cli-grants`, {
        method: 'PATCH', data: { cliId: cli.id, granted: true },
      })
      const validationResponse = await requestWithValidationThrottle(() => fetchNoRedirect(context.request,
        `/api/ai-console/clis/${cli.id}/validate`, { method: 'POST', data: {} }))
      if (!validationResponse.ok()) throw new Error(`AIC_E2E_HTTP_${validationResponse.status()}`)
      const validation = await validationResponse.json() as { validation: { state: string } }
      expect(validation.validation.state).toBe('reachable')
      const cards = await json<{ clis: Array<{ cliId: CliId; state: string; models: Array<{ modelId: string | null }> }> }>(context.request, '/api/ai-console/clis')
      const card = cards.clis.find(row => row.cliId === cli.id)
      expect(card?.state).toBe('reachable')
      expect(card?.models.length).toBeGreaterThan(0)
      const choice: Choice = { kind: 'local_cli', cliId: cli.id, modelId: card!.models[0].modelId }
      await setDefault(context.request, choice)
      const after = new Date().toISOString()
      const response = await fetchNoRedirect(context.request, '/api/chat/consult', { method: 'POST', data: config.consultRequest })
      if (!response.ok()) throw new Error(`AIC_E2E_HTTP_${response.status()}`)
      parseConsultTerminal(await response.text())
      const target: SafeRoleTarget = { kind: 'local_cli', cliId: cli.id, modelId: choice.modelId }
      await latestEvidence(context.request, after, { kind: 'default' }, choice, {
        synthesizer: target, planner: target, deep_planner: target, worker: target,
      })
      await json(context.request, `/api/admin/users/${encodeURIComponent(config.userId)}/ai-cli-grants`, {
        method: 'PATCH', data: { cliId: cli.id, granted: false },
      })
      expect((await fetchNoRedirect(context.request, `/api/ai-console/clis/${cli.id}/validate`, { method: 'POST', data: {} })).ok()).toBe(false)
    })
  }
  test('@leakage inspects mandatory logs, snapshot, Observatory, audit, URLs, and capture artifacts', async ({ context }) => {
    const config = configuredOwner()
    test.skip(!PROVIDER_AUTHORIZED, 'UNQUALIFIED: a current-run provider turn is required for leakage evidence')
    const direct = await createConnection(context.request, config.sameProvider.providerId, config.sameProvider.first,
      `${currentPrefix}leakage`)
    const choice: Choice = { kind: 'provider_model', connectionId: direct.connectionId, modelId: direct.modelId }
    await runNativeTurn(context.request, { kind: 'explicit', choice }, choice, providerRoles(direct))
    const values: string[] = [JSON.stringify(await state(context.request)), JSON.stringify(await json(context.request, '/api/ai-console/clis'))]
    for (const url of config.leakage.urls) values.push(JSON.stringify(await json(context.request, url)))
    for (const [index, baseline] of leakageBaselines.entries()) {
      const markers = index === 3 ? [...auditCorrelationMarkers] : [...turnCorrelationMarkers]
      values.push(await readFreshLeakageEvidence(baseline, { runStartedAtMs, markers }))
    }
    const artifacts = await artifactFiles(config.leakage.artifactDirectory)
    expect(artifacts.map(path => basename(path)).some(name => /(?:trace.*\.zip|.*\.(?:png|jpe?g|webm|har))$/i.test(name))).toBe(false)
    for (const path of artifacts) values.push(await readFile(path, 'utf8'))
    const secrets = [...Object.values(config.providers).map(row => row?.apiKey ?? ''),
      config.sameProvider.first.apiKey, config.sameProvider.second.apiKey, SESSION_COOKIE!,
      ...Object.values(config.mcp?.headers ?? {})]
    expect(values.some(value => containsForbiddenLeakage(value, secrets))).toBe(false)
  })
})
