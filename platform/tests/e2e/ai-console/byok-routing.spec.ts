import { readFile } from 'node:fs/promises'
import { isAbsolute } from 'node:path'
import { expect, test, type APIRequestContext, type BrowserContext } from '@playwright/test'

type ProviderId = 'openai' | 'anthropic' | 'google' | 'xai' | 'deepseek' | 'kimi' | 'openrouter'
type CliId = 'codex' | 'claude_code' | 'gemini_antigravity' | 'kimi_code'
type Choice = { kind: 'provider_model'; connectionId: string; modelId: string }
  | { kind: 'custom_configuration'; configurationId: string }
  | { kind: 'local_cli'; cliId: CliId; modelId: string | null }

interface ProviderSecret { apiKey: string; preferredModel?: string }
interface OwnerConfig {
  userId: string
  conversationId: string
  pariprashnaPath: string
  providers: Partial<Record<ProviderId, ProviderSecret>>
  sameProvider: { providerId: ProviderId; first: ProviderSecret; second: ProviderSecret }
  consultRequest: Record<string, unknown>
  mcp?: { url: string; headers: Record<string, string>; request: Record<string, unknown> }
  inspectionUrls?: string[]
}

const ENABLED = process.env.MARSYS_FLAG_AI_CONSOLE_BYOK === 'true'
  && process.env.NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK === 'true'
const SESSION_COOKIE = process.env.SMOKE_SESSION_COOKIE
const CONFIG_PATH = process.env.AI_CONSOLE_E2E_OWNER_CONFIG_PATH
const READY = ENABLED && Boolean(SESSION_COOKIE) && Boolean(CONFIG_PATH && isAbsolute(CONFIG_PATH))
const PROVIDER_AUTHORIZED = process.env.AI_CONSOLE_PROVIDER_SMOKE_AUTHORIZED === 'true'
const CLI_AUTHORIZED = process.env.AI_CONSOLE_CLI_SMOKE_AUTHORIZED === 'true'
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

let owner: OwnerConfig
const createdConnectionIds = new Set<string>()
const createdConfigurationIds = new Set<string>()

test.use({ trace: 'off', screenshot: 'off', video: 'off' })
test.describe.configure({ mode: 'serial' })

function assertOwnerConfig(value: unknown): asserts value is OwnerConfig {
  const row = value as Partial<OwnerConfig> | null
  if (!row || typeof row !== 'object' || typeof row.userId !== 'string' || typeof row.conversationId !== 'string'
    || typeof row.pariprashnaPath !== 'string' || !row.providers || !row.sameProvider
    || !row.consultRequest || typeof row.consultRequest !== 'object') throw new Error('AIC_E2E_CONFIG_INVALID')
}

async function json<T>(request: APIRequestContext, path: string, init?: Parameters<APIRequestContext['fetch']>[1]): Promise<T> {
  const response = await request.fetch(path, init)
  if (!response.ok()) throw new Error(`AIC_E2E_HTTP_${response.status()}`)
  try { return await response.json() as T } catch { throw new Error('AIC_E2E_RESPONSE_INVALID') }
}

async function authenticate(context: BrowserContext) {
  await context.addCookies([{ name: 'session', value: SESSION_COOKIE!, domain: 'localhost', path: '/', httpOnly: true }])
}

async function state(request: APIRequestContext) {
  return json<{
    connections: Array<{ id: string; name: string; providerId: ProviderId; validationState: string; confirmedValid: boolean }>
    models: Array<{ connectionId: string; modelId: string; available: boolean; compatibleRoles: string[] }>
    configurations: Array<{ id: string; name: string; version: number }>
    defaultChoice: Choice | null
  }>(request, '/api/ai-console')
}

async function createConnection(request: APIRequestContext, providerId: ProviderId, secret: ProviderSecret, name: string) {
  const created = await json<{ connection: { id: string }; validation: { state: string } }>(request, '/api/ai-console/connections', {
    method: 'POST', data: { name, providerId, apiKey: secret.apiKey, acknowledgeCharge: true },
  })
  expect(created.validation.state).toBe('validated')
  createdConnectionIds.add(created.connection.id)
  const current = await state(request)
  const candidates = current.models.filter(model => model.connectionId === created.connection.id && model.available
    && ['synthesizer', 'planner', 'deep_planner', 'worker'].every(role => model.compatibleRoles.includes(role)))
  const model = secret.preferredModel
    ? candidates.find(candidate => candidate.modelId === secret.preferredModel) : candidates[0]
  expect(model, 'validated connection must expose one all-role compatible model').toBeTruthy()
  return { connectionId: created.connection.id, modelId: model!.modelId, name }
}

async function setDefault(request: APIRequestContext, choice: Choice) {
  await json(request, '/api/ai-console/default', { method: 'PUT', data: { choice } })
}

async function setConversation(request: APIRequestContext, selection: { kind: 'default' } | { kind: 'explicit'; choice: Choice }) {
  return json<{ availability: string; label: string; resolvedLabel: string | null }>(request,
    `/api/conversations/${owner.conversationId}/ai-selection`, { method: 'PUT', data: selection })
}

async function removeCreated(request: APIRequestContext) {
  for (const id of createdConfigurationIds) {
    await request.delete(`/api/ai-console/configurations/${id}`, { data: { confirm: true } }).catch(() => undefined)
  }
  for (const id of createdConnectionIds) {
    await request.delete(`/api/ai-console/connections/${id}`, { data: { confirm: true } }).catch(() => undefined)
  }
  createdConfigurationIds.clear()
  createdConnectionIds.clear()
}

function containsForbiddenSecret(value: unknown, secrets: readonly string[]): boolean {
  if (typeof value === 'string') return secrets.some(secret => secret.length > 0 && value.includes(secret))
    || /(?:authorization\s*:\s*bearer|\bsk-[a-z0-9_-]{8,})/i.test(value)
  if (Array.isArray(value)) return value.some(item => containsForbiddenSecret(item, secrets))
  if (!value || typeof value !== 'object') return false
  return Object.entries(value).some(([key, child]) =>
    /^(?:ciphertext|wrappedDataKey|wrapped_data_key|authTag|auth_tag|nonce|apiKey|api_key|credential|authorization|stdout|stderr|token|accessToken|access_token|refreshToken|refresh_token|prompt|probe|completion)$/i.test(key)
      || containsForbiddenSecret(child, secrets))
}

test.describe('AI Console owner-operated local cutover', () => {
  test.skip(!READY, 'UNQUALIFIED: local flags, authenticated disposable user, and absolute owner config path are required')

  test.beforeAll(async () => {
    let parsed: unknown
    try { parsed = JSON.parse(await readFile(CONFIG_PATH!, 'utf8')) } catch { throw new Error('AIC_E2E_CONFIG_INVALID') }
    assertOwnerConfig(parsed)
    owner = parsed
  })

  test.beforeEach(async ({ context }) => authenticate(context))
  test.afterEach(async ({ request }) => removeCreated(request))

  test('@desktop renders the authenticated three-section console without request interception', async ({ page }) => {
    await page.goto('/ai-console')
    await expect(page.getByRole('heading', { level: 1, name: 'AI Console' })).toBeVisible()
    await expect(page.getByRole('heading', { level: 2 })).toHaveText([
      'Provider connections', 'Custom configurations', 'Local CLIs',
    ])
  })

  test('@mobile keeps the same console hierarchy and operable controls', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/ai-console')
    await expect(page.getByRole('heading', { level: 2 })).toHaveText([
      'Provider connections', 'Custom configurations', 'Local CLIs',
    ])
    const add = page.getByRole('button', { name: /add connection/i })
    await expect(add).toBeVisible()
    expect((await add.boundingBox())?.height).toBeGreaterThanOrEqual(44)
  })

  for (const provider of providerCases) {
    test(`@provider-${provider.label} validates a real owner-supplied ${provider.label} connection`, async ({ request }) => {
      test.skip(!PROVIDER_AUTHORIZED || !owner.providers[provider.id],
        `UNQUALIFIED: authorized ${provider.label} credential is absent from the private owner config`)
      const name = `AIC ${provider.label} ${crypto.randomUUID().slice(0, 8)}`
      const created = await createConnection(request, provider.id, owner.providers[provider.id]!, name)
      expect(created.connectionId).toBeTruthy()
      expect(created.modelId).toBeTruthy()
    })
  }

  test('@routing exercises two same-provider connections, four-role configuration lifecycle, live Default, explicit pinning, and cross-context persistence', async ({ browser, request }) => {
    test.skip(!PROVIDER_AUTHORIZED, 'UNQUALIFIED: real provider validation was not explicitly authorized')
    const suffix = crypto.randomUUID().slice(0, 8)
    const first = await createConnection(request, owner.sameProvider.providerId, owner.sameProvider.first, `AIC first ${suffix}`)
    const second = await createConnection(request, owner.sameProvider.providerId, owner.sameProvider.second, `AIC second ${suffix}`)
    expect(first.name).not.toBe(second.name)
    const firstChoice: Choice = { kind: 'provider_model', connectionId: first.connectionId, modelId: first.modelId }
    const secondChoice: Choice = { kind: 'provider_model', connectionId: second.connectionId, modelId: second.modelId }
    await setDefault(request, firstChoice)

    const roles = { synthesizer: firstChoice, planner: secondChoice, deep_planner: firstChoice, worker: secondChoice }
    const configuration = await json<{ configuration: { id: string; version: number } }>(request, '/api/ai-console/configurations', {
      method: 'POST', data: { name: `AIC quartet ${suffix}`, roles },
    })
    createdConfigurationIds.add(configuration.configuration.id)
    const edited = await json<{ configuration: { version: number } }>(request,
      `/api/ai-console/configurations/${configuration.configuration.id}`, {
        method: 'PATCH', data: { name: `AIC quartet edited ${suffix}`, expectedVersion: configuration.configuration.version,
          roles: { synthesizer: secondChoice, planner: firstChoice, deep_planner: secondChoice, worker: firstChoice } },
      })
    expect(edited.configuration.version).toBe(configuration.configuration.version + 1)
    const duplicate = await json<{ configuration: { id: string } }>(request, '/api/ai-console/configurations', {
      method: 'POST', data: { name: `AIC quartet copy ${suffix}`, duplicateFrom: configuration.configuration.id },
    })
    createdConfigurationIds.add(duplicate.configuration.id)
    await setDefault(request, { kind: 'custom_configuration', configurationId: configuration.configuration.id })

    await setDefault(request, firstChoice)
    let view = await setConversation(request, { kind: 'default' })
    expect(view.resolvedLabel).toContain(first.name)
    await setDefault(request, secondChoice)
    view = await json(request, `/api/conversations/${owner.conversationId}/ai-selection`)
    expect(view.resolvedLabel).toContain(second.name)
    view = await setConversation(request, { kind: 'explicit', choice: firstChoice })
    await setDefault(request, secondChoice)
    expect(view.label).toContain(first.name)
    const pinned = await json<{ label: string }>(request, `/api/conversations/${owner.conversationId}/ai-selection`)
    expect(pinned.label).toContain(first.name)

    const secondContext = await browser.newContext()
    await authenticate(secondContext)
    try {
      const fromSecondContext = await json<{ label: string }>(secondContext.request,
        `/api/conversations/${owner.conversationId}/ai-selection`)
      expect(fromSecondContext.label).toContain(first.name)
      const secondPage = await secondContext.newPage()
      await secondPage.goto(owner.pariprashnaPath)
      await expect(secondPage.getByRole('button', { name: new RegExp(`AI.*${first.name}`, 'i') })).toBeVisible()
    } finally { await secondContext.close() }

    await json(request, `/api/ai-console/configurations/${duplicate.configuration.id}`, {
      method: 'DELETE', data: { confirm: true },
    })
    createdConfigurationIds.delete(duplicate.configuration.id)
  })

  test('@backend runs a logged-in backend request through the current user default', async ({ request }) => {
    test.skip(!PROVIDER_AUTHORIZED || !owner.providers.openai,
      'UNQUALIFIED: an authorized provider credential is required for backend execution')
    const direct = await createConnection(request, 'openai', owner.providers.openai!, `AIC backend ${crypto.randomUUID().slice(0, 8)}`)
    await setDefault(request, { kind: 'provider_model', connectionId: direct.connectionId, modelId: direct.modelId })
    const response = await request.post('/api/chat/consult', { data: owner.consultRequest })
    expect(response.ok()).toBe(true)
    await response.body()
  })

  test('@mcp returns evidence for external synthesis and no Madhav synthesized reading', async ({ request }) => {
    test.skip(!owner.mcp, 'UNQUALIFIED: authenticated local MCP bridge configuration is absent')
    const response = await request.post(owner.mcp!.url, { headers: owner.mcp!.headers, data: owner.mcp!.request })
    expect(response.ok()).toBe(true)
    const envelope = await response.json() as Record<string, unknown>
    expect(envelope.schema_version).toBe('madhav.evidence.v1')
    expect(envelope.synthesis).toEqual({ mode: 'external', performed_by_madhav: false })
    expect(envelope).not.toHaveProperty('reading')
  })

  for (const cli of cliCases) {
    test(`@cli-${cli.label} grants, validates, invokes, and revokes ${cli.label}`, async ({ request }) => {
      test.skip(!CLI_AUTHORIZED, `UNQUALIFIED: real ${cli.label} subscription execution was not explicitly authorized`)
      await json(request, `/api/admin/users/${encodeURIComponent(owner.userId)}/ai-cli-grants`, {
        method: 'PATCH', data: { cliId: cli.id, granted: true },
      })
      try {
        const validation = await json<{ validation: { state: string } }>(request,
          `/api/ai-console/clis/${cli.id}/validate`, { method: 'POST', data: {} })
        expect(validation.validation.state).toBe('reachable')
        const cards = await json<{ clis: Array<{ cliId: CliId; state: string; models: Array<{ modelId: string | null }> }> }>(request, '/api/ai-console/clis')
        const card = cards.clis.find(row => row.cliId === cli.id)
        expect(card?.state).toBe('reachable')
        expect(card?.models.length).toBeGreaterThan(0)
        await setDefault(request, { kind: 'local_cli', cliId: cli.id, modelId: card!.models[0].modelId })
        const response = await request.post('/api/chat/consult', { data: owner.consultRequest })
        expect(response.ok()).toBe(true)
        await response.body()
      } finally {
        await json(request, `/api/admin/users/${encodeURIComponent(owner.userId)}/ai-cli-grants`, {
          method: 'PATCH', data: { cliId: cli.id, granted: false },
        })
      }
      const blocked = await request.post(`/api/ai-console/clis/${cli.id}/validate`, { data: {} })
      expect(blocked.ok()).toBe(false)
    })
  }

  test('@leakage finds no owner secrets or secret-bearing fields in safe application projections', async ({ request }) => {
    const values: unknown[] = [await state(request), await json(request, '/api/ai-console/clis')]
    for (const url of owner.inspectionUrls ?? []) values.push(await json(request, url))
    const secrets = [
      ...Object.values(owner.providers).map(row => row?.apiKey ?? ''),
      owner.sameProvider.first.apiKey, owner.sameProvider.second.apiKey,
    ]
    expect(values.some(value => containsForbiddenSecret(value, secrets))).toBe(false)
  })
})
