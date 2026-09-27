import { expect, test } from '@playwright/test'

const SESSION_COOKIE = process.env.SMOKE_SESSION_COOKIE
const ENABLED = process.env.MARSYS_FLAG_AI_CONSOLE_BYOK === 'true'
  && process.env.NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK === 'true'
const READY = Boolean(SESSION_COOKIE) && ENABLED
const CAPTURE = process.env.AI_CONSOLE_CAPTURE_SCREENSHOTS === 'true'

const connectionId = '11111111-1111-4111-8111-111111111111'
const safeConsoleState = {
  connections: [{ id: connectionId, providerId: 'openai', name: 'Personal OpenAI', maskedSuffix: '•••1234',
    validationState: 'invalid', lastValidatedAt: null, lastCheckedAt: '2026-09-27T10:00:00.000Z',
    lastErrorCode: 'AI_CONNECTION_INVALID', deletedAt: null }],
  models: [{ connectionId, modelId: 'removed-model', displayName: 'Removed model',
    compatibleRoles: ['synthesizer', 'planner', 'deep_planner', 'worker'], supportsTools: false,
    supportsStructuredOutput: true, available: false }],
  configurations: [],
  defaultChoice: { kind: 'provider_model', connectionId, modelId: 'removed-model' },
  validationDisclosure: 'Testing this connection makes a tiny generation request and may incur a tiny provider charge.',
}
const safeCliState = { clis: [
  { cliId: 'codex', productName: 'Codex CLI', state: 'needs_attention', detectedProduct: 'Codex CLI', detectedVersion: '0.155.1', lastCheckedAt: null, models: [] },
  { cliId: 'claude_code', productName: 'Claude Code', state: 'not_granted' },
  { cliId: 'gemini_antigravity', productName: 'Gemini / Antigravity', state: 'not_granted' },
  { cliId: 'kimi_code', productName: 'Kimi Code', state: 'needs_attention', detectedProduct: null, detectedVersion: null, lastCheckedAt: null, models: [] },
] }

test.describe('AI Console — safe local UI contract', () => {
  test.skip(!READY, 'UNQUALIFIED: authenticated local session and both AI Console flags are required')

  test.beforeEach(async ({ context, page }) => {
    await context.addCookies([{ name: 'session', value: SESSION_COOKIE!, domain: 'localhost', path: '/' }])
    await page.route('**/api/ai-console/clis', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(safeCliState) }))
    await page.route('**/api/ai-console', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(safeConsoleState) }))
  })

  test('renders the three sections, invalid credential, broken default, and disclosure-safe CLIs', async ({ page }, testInfo) => {
    await page.goto('/ai-console')
    await expect(page.getByRole('heading', { level: 1, name: 'AI Console' })).toBeVisible()
    await expect(page.getByRole('heading', { level: 2 })).toHaveText(['Provider connections', 'Custom configurations', 'Local CLIs'])
    await expect(page.getByText('Credential rejected')).toBeVisible()
    await expect(page.getByText(/Default unavailable/)).toBeVisible()
    await expect(page.getByText(/tiny provider charge/)).toBeVisible()
    const antigravityCard = page.getByText('Gemini / Antigravity').locator('xpath=ancestor::article')
    await expect(antigravityCard.getByText('Not granted')).toBeVisible()
    await expect(page.getByText(/sk-|authorization:|bearer /i)).toHaveCount(0)
    if (CAPTURE) await page.screenshot({ path: testInfo.outputPath('ai-console-desktop.png'), fullPage: true })
  })

  test('preserves section order and usable controls at 390x844', async ({ page }, testInfo) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/ai-console')
    await expect(page.getByRole('heading', { level: 2 })).toHaveText(['Provider connections', 'Custom configurations', 'Local CLIs'])
    const add = page.getByRole('button', { name: /add connection/i })
    await expect(add).toBeVisible()
    expect((await add.boundingBox())?.height).toBeGreaterThanOrEqual(44)
    if (CAPTURE) await page.screenshot({ path: testInfo.outputPath('ai-console-mobile.png'), fullPage: true })
  })
})
