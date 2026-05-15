/**
 * Chat V2 — Playwright global setup.
 *
 * Responsibilities:
 *  1. Enable fixture mode so E2E tests don't call real providers.
 *  2. Validate the fixture directory tree is present.
 *  3. Log configuration for debugging.
 */
import { FullConfig } from '@playwright/test'
import path from 'path'
import fs from 'fs'

export default async function globalSetup(_config: FullConfig): Promise<void> {
  // Activate fixture mode for the server process under test.
  // Next.js reads this via process.env at request time.
  process.env.MARSYS_FIXTURE_MODE = process.env.MARSYS_FIXTURE_MODE ?? 'true'

  if (process.env.MARSYS_FIXTURE_MODE === 'true') {
    const fixtureRoot = path.join(process.cwd(), 'tests', 'fixtures', 'chat-v2')
    if (!fs.existsSync(fixtureRoot)) {
      throw new Error(
        `[chat-v2/global-setup] Fixture root not found: ${fixtureRoot}.\n` +
          'Run the worktree setup or restore fixtures from the repo.',
      )
    }
    console.log(`[chat-v2/global-setup] Fixture mode ENABLED — root: ${fixtureRoot}`)
  } else {
    console.log(
      '[chat-v2/global-setup] Fixture mode DISABLED — tests will call live providers.',
    )
  }

  // Log base URL for debugging.
  const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3000'
  console.log(`[chat-v2/global-setup] Base URL: ${baseURL}`)
}
