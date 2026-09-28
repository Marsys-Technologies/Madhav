import { describe, expect, it } from 'vitest'
import { mkdtemp, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import {
  acceptanceCommands,
  acceptanceExitCode,
  environmentForCommand,
  executeAcceptanceCommand,
  parseTestCounts,
  runLocalAcceptance,
  type AcceptanceCommandResult,
  type AcceptanceEnvironment,
} from '../../../../scripts/ai-console/local_acceptance'

const BASE_ENV: AcceptanceEnvironment = {
  MARSYS_FLAG_AI_CONSOLE_BYOK: 'true',
  NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK: 'true',
  RUN_DB_TESTS: '1',
  AI_CONSOLE_TEST_DATABASE_URL: 'postgresql://test@127.0.0.1:5432/ai_console_test_acceptance',
  SMOKE_SESSION_COOKIE: 'present',
  AI_CONSOLE_E2E_OWNER_CONFIG_PATH: '/private/ai-console-owner.json',
  AI_CONSOLE_PROVIDER_SMOKE_AUTHORIZED: 'true',
  AI_CONSOLE_CLI_SMOKE_AUTHORIZED: 'true',
  AI_CONSOLE_E2E_EXTERNAL_SERVER: 'true',
  AI_CONSOLE_E2E_ARTIFACT_DIR: '/private/artifacts',
  __AIC_OWNER_FIXTURE_VALIDATED: 'true',
}

const passed = (executedCount = 1, skippedCount = 0): AcceptanceCommandResult => ({
  exitCode: 0, executedCount, skippedCount,
})

describe('AI Console local acceptance runner', () => {
  it('parses Vitest and Playwright executed/skipped counts without retaining raw output', () => {
    expect(parseTestCounts('Tests  7 passed | 2 skipped (9)')).toEqual({ executedCount: 7, skippedCount: 2 })
    expect(parseTestCounts('  5 passed\n  3 skipped')).toEqual({ executedCount: 5, skippedCount: 3 })
    expect(parseTestCounts('\u001b[32m  58 passed\u001b[39m (36.4s)\n\u001b[33m  6 skipped\u001b[39m')).toEqual({ executedCount: 58, skippedCount: 6 })
    expect(parseTestCounts('Running 64 tests using 1 worker\n\n  6 skipped\n  58 passed (36.4s)')).toEqual({ executedCount: 58, skippedCount: 6 })
    expect(parseTestCounts('No tests found')).toEqual({ executedCount: 0, skippedCount: 0 })
  })

  it('marks missing external prerequisites UNQUALIFIED while still running independent gates', async () => {
    const invoked: string[] = []
    const report = await runLocalAcceptance({
      env: {}, revision: '0123456789abcdef0123456789abcdef01234567',
      now: () => new Date('2026-09-28T00:00:00.000Z'),
      execute: async command => {
        invoked.push(command.id)
        return command.id === 'route_graph_clean' ? { exitCode: 1 } : passed()
      },
    })

    expect(report.summary).toEqual({ pass: expect.any(Number), fail: 1, unqualified: expect.any(Number) })
    expect(report.dimensions.find(row => row.id === 'disposable_database')?.status).toBe('UNQUALIFIED')
    expect(report.dimensions.find(row => row.id === 'provider_openai')?.status).toBe('UNQUALIFIED')
    expect(report.dimensions.find(row => row.id === 'cli_codex')?.status).toBe('UNQUALIFIED')
    expect(report.dimensions.find(row => row.id === 'route_graph_clean')?.status).toBe('FAIL')
    expect(invoked).toContain('typecheck')
    expect(invoked).not.toContain('database')
    expect(acceptanceExitCode(report)).toBe(1)
  })

  it('never promotes a zero-executed or skip-only test command to PASS', async () => {
    const report = await runLocalAcceptance({
      env: BASE_ENV, revision: '0123456789abcdef0123456789abcdef01234567',
      now: () => new Date('2026-09-28T00:00:00.000Z'),
      execute: async command => command.kind === 'test' ? passed(0, 4) : passed(),
    })

    expect(report.dimensions.filter(row => row.commandKind === 'test').every(row => row.status === 'UNQUALIFIED')).toBe(true)
    expect(acceptanceExitCode(report)).toBe(2)
  })

  it('returns FAIL and exit 1 when an executed required dimension fails', async () => {
    const report = await runLocalAcceptance({
      env: BASE_ENV, revision: '0123456789abcdef0123456789abcdef01234567',
      now: () => new Date('2026-09-28T00:00:00.000Z'),
      execute: async command => command.id === 'build' ? { exitCode: 1 } : passed(),
    })

    expect(report.dimensions.find(row => row.id === 'build')?.status).toBe('FAIL')
    expect(acceptanceExitCode(report)).toBe(1)
  })

  it('returns PASS and exit 0 only when every required dimension ran and passed', async () => {
    const report = await runLocalAcceptance({
      env: BASE_ENV, revision: '0123456789abcdef0123456789abcdef01234567',
      now: () => new Date('2026-09-28T00:00:00.000Z'),
      execute: async command => passed(command.kind === 'test' ? 2 : 1),
    })

    expect(report.summary).toEqual({ pass: report.dimensions.length, fail: 0, unqualified: 0 })
    expect(acceptanceExitCode(report)).toBe(0)
    expect(JSON.stringify(report)).not.toMatch(/present|postgresql|private\/ai-console|SMOKE_SESSION_COOKIE/)
  })

  it('rejects a non-disposable or non-local database target before execution', async () => {
    const badEnv = { ...BASE_ENV, AI_CONSOLE_TEST_DATABASE_URL: 'postgresql://test@db.example.com:5432/production' }
    const invoked: string[] = []

    const report = await runLocalAcceptance({
      env: badEnv, revision: '0123456789abcdef0123456789abcdef01234567',
      now: () => new Date('2026-09-28T00:00:00.000Z'),
      execute: async command => { invoked.push(command.id); return passed() },
    })

    expect(report.dimensions.find(row => row.id === 'disposable_database')).toMatchObject({
      status: 'UNQUALIFIED', code: 'AIC_ACCEPTANCE_DB_NOT_DISPOSABLE_LOCAL',
    })
    expect(invoked).not.toContain('database')
  })

  it('passes only minimal and command-specific environment variables to subprocesses', () => {
    const source = {
      PATH: '/safe/bin', HOME: '/private/home', TMPDIR: '/private/tmp', CI: '1',
      SMOKE_SESSION_COOKIE: 'secret-session', AI_CONSOLE_E2E_OWNER_CONFIG_PATH: '/private/owner.json',
      AI_CONSOLE_E2E_BASE_URL: 'http://127.0.0.1:3000', MARSYS_FLAG_AI_CONSOLE_BYOK: 'true',
      NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK: 'true', AI_CONSOLE_PROVIDER_SMOKE_AUTHORIZED: 'true',
      AI_CONSOLE_CLI_SMOKE_AUTHORIZED: 'true', AI_CONSOLE_E2E_EXTERNAL_SERVER: 'true',
      AI_CONSOLE_E2E_ARTIFACT_DIR: '/private/artifacts',
      AI_CONSOLE_TEST_DATABASE_URL: 'postgresql://local-test',
      DATABASE_URL: 'postgresql://must-not-leak', OPENAI_API_KEY: 'must-not-leak', RANDOM_SECRET: 'must-not-leak',
    }
    const all = acceptanceCommands()
    const typecheck = environmentForCommand(all.find(row => row.id === 'typecheck')!, source)
    const database = environmentForCommand(all.find(row => row.id === 'disposable_database')!, source)
    const browser = environmentForCommand(all.find(row => row.id === 'authenticated_desktop')!, source)

    expect(typecheck).toEqual({ PATH: '/safe/bin', HOME: '/private/home', TMPDIR: '/private/tmp', CI: '1' })
    expect(database).toMatchObject({ AI_CONSOLE_TEST_DATABASE_URL: 'postgresql://local-test', RUN_DB_TESTS: '1' })
    expect(database).not.toHaveProperty('DATABASE_URL')
    expect(browser).toMatchObject({ SMOKE_SESSION_COOKIE: 'secret-session', AI_CONSOLE_E2E_OWNER_CONFIG_PATH: '/private/owner.json' })
    expect(browser).not.toHaveProperty('OPENAI_API_KEY')
    expect(browser).not.toHaveProperty('AI_CONSOLE_TEST_DATABASE_URL')
    expect(browser).not.toHaveProperty('RANDOM_SECRET')
  })

  it('terminates a timed-out command process group and reports a stable timeout fact', async () => {
    const directory = await mkdtemp(join(tmpdir(), 'aic-deadline-'))
    const marker = join(directory, 'child.pid')
    const command = {
      id: 'deadline_fixture', kind: 'command' as const, command: process.execPath,
      args: ['-e', `const{spawn}=require('node:child_process');const{writeFileSync}=require('node:fs');const c=spawn(process.execPath,['-e','setInterval(()=>{},1000)'],{stdio:'ignore'});writeFileSync(${JSON.stringify(marker)},String(c.pid));setInterval(()=>{},1000)`],
      timeoutMs: 150, environment: 'base' as const,
    }

    try {
      const result = await executeAcceptanceCommand(command, { PATH: process.env.PATH })
      expect(result).toMatchObject({ exitCode: 124, timedOut: true })
      const descendantPid = Number(await readFile(marker, 'utf8'))
      await expect.poll(() => {
        try { process.kill(descendantPid, 0); return 'alive' } catch { return 'gone' }
      }, { timeout: 2_000 }).toBe('gone')
    } finally { await rm(directory, { recursive: true, force: true }) }
  })
})
