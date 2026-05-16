/**
 * Fixture-mode adapter — server-side.
 *
 * When MARSYS_FIXTURE_MODE=true, provider calls are replaced by pre-recorded
 * JSON fixtures from tests/fixtures/chat-v2/providers/<provider>/<scenario>.json.
 *
 * This module is only imported in route handlers; it must remain Node-compatible
 * (no browser APIs).
 *
 * Usage in a route:
 *   if (isFixtureModeEnabled()) {
 *     return streamFixture(provider, scenario, res)
 *   }
 */

import path from 'path'
import fs from 'fs'

export type FixtureProvider =
  | 'anthropic'
  | 'anthropic_thinking'
  | 'gemini_pro'
  | 'gemini_thinking'
  | 'openai'
  | 'deepseek_v4'
  | 'deepseek_r1'
  | 'nim'

export interface FixtureMetadata {
  provider: FixtureProvider
  scenario: string
  _fixture_status: string
  model?: string
  input_tokens?: number
  output_tokens?: number
  reasoning_tokens?: number
}

export interface FixtureFile {
  metadata: FixtureMetadata
  chunks?: unknown[]
  response?: unknown
}

export function isFixtureModeEnabled(): boolean {
  return process.env.MARSYS_FIXTURE_MODE === 'true'
}

/**
 * Resolve the absolute path for a fixture file.
 * Searches relative to process.cwd() (the Next.js project root = platform/).
 */
export function resolveFixturePath(provider: FixtureProvider, scenario: string): string {
  return path.join(
    process.cwd(),
    'tests',
    'fixtures',
    'chat-v2',
    'providers',
    provider,
    `${scenario}.json`,
  )
}

/**
 * Load and parse a fixture file.
 * Throws if the file does not exist or cannot be parsed.
 */
export function loadFixture(provider: FixtureProvider, scenario: string): FixtureFile {
  const fixturePath = resolveFixturePath(provider, scenario)

  if (!fs.existsSync(fixturePath)) {
    throw new Error(
      `[fixture_mode_adapter] Fixture not found: ${fixturePath}\n` +
        `  provider=${provider} scenario=${scenario}\n` +
        '  Add a fixture file or run provider recording (see CLAUDECODE_BRIEF §M item 2).',
    )
  }

  let raw: string
  try {
    raw = fs.readFileSync(fixturePath, 'utf-8')
  } catch (err) {
    throw new Error(
      `[fixture_mode_adapter] Failed to read fixture: ${fixturePath}\n  ${String(err)}`,
    )
  }

  try {
    return JSON.parse(raw) as FixtureFile
  } catch (err) {
    throw new Error(
      `[fixture_mode_adapter] Invalid JSON in fixture: ${fixturePath}\n  ${String(err)}`,
    )
  }
}

/**
 * List available scenarios for a provider.
 */
export function listFixtures(provider: FixtureProvider): string[] {
  const providerDir = path.join(
    process.cwd(),
    'tests',
    'fixtures',
    'chat-v2',
    'providers',
    provider,
  )

  if (!fs.existsSync(providerDir)) {
    return []
  }

  return fs
    .readdirSync(providerDir)
    .filter((f) => f.endsWith('.json'))
    .map((f) => f.replace(/\.json$/, ''))
}
