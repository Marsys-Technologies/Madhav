import { chmod, mkdtemp, readFile, realpath, rm, symlink, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { CliDefinition } from '../registry'
const authorization = vi.hoisted(() => ({ invoke: vi.fn() }))
const synchronousFileReads = vi.hoisted(() => ({ reject: false, calls: 0 }))
vi.mock('node:fs', async importOriginal => {
  const actual = await importOriginal<typeof import('node:fs')>()
  return { ...actual, readFileSync: (...args: Parameters<typeof actual.readFileSync>) => {
    synchronousFileReads.calls++
    if (synchronousFileReads.reject) throw new Error('synchronous full-file read is forbidden')
    return actual.readFileSync(...args)
  } }
})
vi.mock('../../repository', () => ({
  withCliInvocationAuthorization: authorization.invoke,
}))
import { createCliRunner } from '../runner'

const roots: string[] = []
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))
beforeEach(() => {
  synchronousFileReads.reject = false; synchronousFileReads.calls = 0
  authorization.invoke.mockImplementation(async (_userId: string, _cliId: string,
    start: () => unknown, _purpose: string, beforeStart?: () => Promise<void>) => {
    await beforeStart?.()
    return start()
  })
})
afterEach(async () => { await Promise.all(roots.splice(0).map(root => rm(root, { recursive: true, force: true }))) })

async function fixture(source: string) {
  const root = await mkdtemp(join(tmpdir(), 'madhav-cli-fixture-')); roots.push(root)
  const executable = join(root, 'fake-cli')
  await writeFile(executable, `#!/usr/bin/env node\n${source}`)
  await chmod(executable, 0o755)
  const definition: CliDefinition = {
    id: 'codex', productName: 'Fake Codex', candidates: [executable], allowedRealpathPrefixes: [`${await realpath(root)}/`],
    versionArgs: ['--version'], authStatusArgs: ['auth'], supportedVersion: '1.0.0', compatibleRoles: [],
    supportsTools: false, supportsStructuredOutput: false,
    execution: { args: ['run'], modelFlag: ['-m'], outputFormat: 'codex_jsonl' },
  }
  return { root, executable, definition }
}

describe('governed CLI runner', () => {
  it('passes exact argv/stdin in an isolated cwd and strips token/project environment', async () => {
    const { root, definition } = await fixture(`
      let input=''; process.stdin.on('data', c => input += c); process.stdin.on('end', () => {
        process.stdout.write(JSON.stringify({argv:process.argv.slice(2),input,cwd:process.cwd(),
          secret:process.env.OPENAI_API_KEY,canary:process.env.MADHAV_CANARY_TOKEN,nodeOptions:process.env.NODE_OPTIONS}))
      })`)
    const runner = createCliRunner({ registry: { codex: definition }, environment: {
      ...process.env, OPENAI_API_KEY: 'secret', MADHAV_CANARY_TOKEN: 'canary', NODE_OPTIONS: '--inspect', HOME: root,
    } })
    const result = await runner.runProbeValidation('alice', 'codex', 'prompt')
    const value = JSON.parse(result.stdout)
    expect(value.argv).toEqual(['run'])
    expect(value.input).toBe('prompt')
    expect(value.cwd).toMatch(/madhav-ai-cli-/)
    expect(value.secret).toBeUndefined()
    expect(value.canary).toBeUndefined()
    expect(value.nodeOptions).toBeUndefined()
    await expect(readFile(value.cwd)).rejects.toMatchObject({ code: 'ENOENT' })
  })

  it('discards successful auth-status output at the runner boundary', async () => {
    const { definition } = await fixture('process.stdout.write("private@example.com")')
    const result = await createCliRunner({ registry: { codex: definition } })
      .runAuthValidation('alice', 'codex')
    expect(result).toEqual({ stdout: '', exitCode: 0, signal: null })
    expect(JSON.stringify(result)).not.toContain('private@example.com')
  })

  it('rejects missing, world-writable, unsafe-parent, and escaping-symlink executables', async () => {
    const missing = await fixture('process.stdout.write("ok")')
    missing.definition = { ...missing.definition, candidates: [join(missing.root, 'absent')] }
    await expect(createCliRunner({ registry: { codex: missing.definition } })
      .runVersionValidation('alice', 'codex')).rejects.toMatchObject({ code: 'AI_CLI_NOT_INSTALLED' })

    const first = await fixture('process.stdout.write("ok")')
    await chmod(first.executable, 0o777)
    await expect(createCliRunner({ registry: { codex: first.definition } })
      .runVersionValidation('alice', 'codex')).rejects.toMatchObject({ code: 'AI_CLI_UNREACHABLE' })

    const unsafeParent = await fixture('process.stdout.write("ok")')
    await chmod(unsafeParent.root, 0o777)
    await expect(createCliRunner({ registry: { codex: unsafeParent.definition } })
      .runVersionValidation('alice', 'codex')).rejects.toMatchObject({ code: 'AI_CLI_UNREACHABLE' })

    const second = await fixture('process.stdout.write("ok")')
    const outside = join(tmpdir(), `madhav-outside-${process.pid}`)
    await writeFile(outside, '#!/usr/bin/env node\nprocess.stdout.write("bad")')
    roots.push(outside)
    await chmod(outside, 0o755)
    const link = join(second.root, 'link')
    await symlink(outside, link)
    const escaped = { ...second.definition, candidates: [link] }
    await expect(createCliRunner({ registry: { codex: escaped } })
      .runVersionValidation('alice', 'codex')).rejects.toMatchObject({ code: 'AI_CLI_UNREACHABLE' })
  })

  it('never invokes a registered detect-only CLI', async () => {
    const { root, definition } = await fixture(`require('node:fs').writeFileSync(process.argv[2],'invoked')`)
    const marker = join(root, 'invoked.txt')
    const detectOnly = { ...definition, versionArgs: [marker], authStatusArgs: undefined, execution: undefined }
    await expect(createCliRunner({ registry: { codex: detectOnly } })
      .runVersionValidation('alice', 'codex')).rejects.toMatchObject({ code: 'AI_CLI_UNREACHABLE' })
    await expect(readFile(marker)).rejects.toMatchObject({ code: 'ENOENT' })
  })

  it('caps multibyte stdout and never returns stderr', async () => {
    const { definition } = await fixture('process.stderr.write("raw-secret"); process.stdout.write("💥".repeat(20))')
    const runner = createCliRunner({ registry: { codex: definition }, limits: { stdoutBytes: 20, stderrBytes: 8 } })
    const error = await runner.runProbeValidation('alice', 'codex', '').catch(value => value)
    expect(error).toMatchObject({ code: 'AI_CLI_OUTPUT_LIMIT' })
    expect(JSON.stringify(error)).not.toContain('raw-secret')
  })

  it('enforces the per-invocation output ceiling before returning any partial stdout', async () => {
    const { definition } = await fixture('process.stdout.write("123456789")')
    const runner = createCliRunner({ registry: { codex: definition } })
    const identity = await runner.inspectInstallation('codex')
    await runner.confirmValidation('codex', identity, '1.0.0')

    await expect(runner.runExecution('alice', 'codex', {
      modelId: null, stdin: '', maxOutputTokens: 8,
    })).rejects.toMatchObject({ code: 'AI_CLI_OUTPUT_LIMIT' })
    await expect(runner.runExecution('alice', 'codex', {
      modelId: null, stdin: '', maxOutputTokens: 9,
    })).resolves.toEqual({ stdout: '123456789', exitCode: 0, signal: null })
  })

  it('rejects non-executable files and invalid UTF-8 machine output', async () => {
    const blocked = await fixture('process.stdout.write("ok")')
    await chmod(blocked.executable, 0o644)
    await expect(createCliRunner({ registry: { codex: blocked.definition } })
      .runVersionValidation('alice', 'codex')).rejects.toMatchObject({ code: 'AI_CLI_UNREACHABLE' })
    const invalid = await fixture('process.stdout.write(Buffer.from([0xff]))')
    await expect(createCliRunner({ registry: { codex: invalid.definition } })
      .runVersionValidation('alice', 'codex')).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
  })

  it('times out, cancels, and removes the isolated directory', async () => {
    const { root, definition } = await fixture(`
      const fs=require('node:fs'); fs.writeFileSync(process.argv[2],process.cwd()); setInterval(() => {}, 1000)`)
    const cwdRecord = join(root, 'cwd.txt')
    const timedDefinition = { ...definition, execution: { ...definition.execution!, args: [cwdRecord] } }
    const runner = createCliRunner({ registry: { codex: timedDefinition }, limits: { timeoutMs: 1_500, killGraceMs: 10 } })
    await expect(runner.runProbeValidation('alice', 'codex', '')).rejects.toMatchObject({ code: 'AI_CLI_TIMEOUT' })
    const isolatedCwd = await readFile(cwdRecord, 'utf8')
    await expect(readFile(isolatedCwd)).rejects.toMatchObject({ code: 'ENOENT' })
    expect(runner.inspectForTests().active).toBe(0)
  })

  it('enforces the global and per-CLI concurrency limits independently', async () => {
    const { definition } = await fixture('setTimeout(() => process.stdout.write("done"), 100)')
    const claude = { ...definition, id: 'claude_code' as const }
    const runner = createCliRunner({ registry: { codex: definition, claude_code: claude },
      limits: { perCliConcurrency: 1, globalConcurrency: 2 } })
    const first = runner.runProbeValidation('alice', 'codex', '')
    const queuedSameCli = runner.runProbeValidation('alice', 'codex', '')
    const otherCli = runner.runProbeValidation('alice', 'claude_code', '')
    expect(runner.inspectForTests()).toEqual({ active: 2, queued: 1 })
    await Promise.all([first, queuedSameCli, otherCli])
    expect(runner.inspectForTests()).toEqual({ active: 0, queued: 0 })
  })

  it('rejects non-catalog model IDs and oversized stdin before spawning', async () => {
    const { definition } = await fixture('process.stdout.write("spawned")')
    const runner = createCliRunner({ registry: { codex: definition }, limits: { stdinBytes: 8 } })
    await expect(runner.runExecution('alice', 'codex', { modelId: 'invented', stdin: '' }))
      .rejects.toMatchObject({ code: 'AI_MODEL_UNAVAILABLE' })
    await expect(runner.runProbeValidation('alice', 'codex', '123456789'))
      .rejects.toMatchObject({ code: 'AI_CLI_OUTPUT_LIMIT' })
  })

  it('reassembles fragmented stdout and maps nonzero exit or signal without exposing stderr', async () => {
    const fragmented = await fixture(`
      process.stdout.write('{"ok":'); setTimeout(()=>process.stdout.end('true}'),5)`)
    const success = await createCliRunner({ registry: { codex: fragmented.definition } })
      .runProbeValidation('alice', 'codex', '')
    expect(JSON.parse(success.stdout)).toEqual({ ok: true })

    const failed = await fixture('process.stderr.write("private"); process.exit(7)')
    const exitError = await createCliRunner({ registry: { codex: failed.definition } })
      .runProbeValidation('alice', 'codex', '').catch(value => value)
    expect(exitError).toMatchObject({ code: 'AI_CLI_UNREACHABLE' })
    expect(JSON.stringify(exitError)).not.toContain('private')

    const signalled = await fixture("process.kill(process.pid,'SIGTERM')")
    await expect(createCliRunner({ registry: { codex: signalled.definition } })
      .runProbeValidation('alice', 'codex', '')).rejects.toMatchObject({ code: 'AI_CLI_UNREACHABLE' })
  })

  it('requires the exact validated executable identity before execution and rejects a swapped entrypoint', async () => {
    const { executable, definition } = await fixture('process.stdout.write("original")')
    const runner = createCliRunner({ registry: { codex: definition } })
    const identity = await runner.inspectInstallation('codex')
    await runner.confirmValidation('codex', identity, '1.0.0')
    await writeFile(executable, '#!/usr/bin/env node\nprocess.stdout.write("swapped")')
    await expect(runner.runExecution('alice', 'codex', { modelId: null, stdin: '' }))
      .rejects.toMatchObject({ code: 'AI_CLI_UNREACHABLE' })
  })

  it('preserves confirmed execution during revalidation without synchronous file reads', async () => {
    const { definition } = await fixture('process.stdout.write("ok")')
    const runner = createCliRunner({ registry: { codex: definition } })
    synchronousFileReads.reject = true
    const identity = await runner.inspectInstallation('codex')
    expect(identity.entrypoint.sha256).toMatch(/^[a-f0-9]{64}$/)
    await runner.confirmValidation('codex', identity, '1.0.0')
    await runner.inspectInstallation('codex')
    await expect(runner.runExecution('alice', 'codex', { modelId: null, stdin: '' }))
      .resolves.toMatchObject({ stdout: 'ok' })
    expect(synchronousFileReads.calls).toBe(0)
  })

  it('binds and rechecks the fixed interpreter chain before execution', async () => {
    const { root, definition } = await fixture('process.stdout.write("entry")')
    const interpreter = join(root, 'fixed-node')
    await writeFile(interpreter, '#!/usr/bin/env node\nprocess.stdout.write("original-launcher")')
    await chmod(interpreter, 0o755)
    const interpreted = { ...definition, interpreter: { candidate: interpreter,
      allowedRealpathPrefixes: [`${await realpath(root)}/`] } }
    const runner = createCliRunner({ registry: { codex: interpreted } })
    const identity = await runner.inspectInstallation('codex')
    await runner.confirmValidation('codex', identity, '1.0.0')
    await writeFile(interpreter, '#!/usr/bin/env node\nprocess.stdout.write("swapped-launcher")')
    await expect(runner.runExecution('alice', 'codex', { modelId: null, stdin: '' }))
      .rejects.toMatchObject({ code: 'AI_CLI_UNREACHABLE' })
  })

  it('fails closed after restart or a mismatched validated version', async () => {
    const { definition } = await fixture('process.stdout.write("should-not-run")')
    const runner = createCliRunner({ registry: { codex: definition } })
    await expect(runner.runExecution('alice', 'codex', { modelId: null, stdin: '' }))
      .rejects.toMatchObject({ code: 'AI_CLI_UNREACHABLE' })
    const identity = await runner.inspectInstallation('codex')
    await expect(runner.confirmValidation('codex', identity, '2.0.0'))
      .rejects.toMatchObject({ code: 'AI_CLI_UNREACHABLE' })
  })

  it('honors abort before admission and while queued behind the per-CLI cap', async () => {
    const { definition } = await fixture('setTimeout(() => process.stdout.write("done"), 200)')
    const runner = createCliRunner({ registry: { codex: definition }, limits: { perCliConcurrency: 1, globalConcurrency: 1 } })
    const first = runner.runProbeValidation('alice', 'codex', '')
    const controller = new AbortController()
    const second = runner.runProbeValidation('alice', 'codex', '', controller.signal)
    controller.abort()
    await expect(second).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    await first
    expect(runner.inspectForTests()).toEqual({ active: 0, queued: 0 })
    const already = new AbortController(); already.abort()
    await expect(runner.runProbeValidation('alice', 'codex', '', already.signal))
      .rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
  })

  it('kills the detached process group, including descendants, on caller abort', async () => {
    const { root, definition } = await fixture(`
      const {spawn}=require('node:child_process'); const fs=require('node:fs');
      const child=spawn(process.execPath,['-e','setInterval(()=>{},1000)'],{stdio:'ignore'});
      fs.writeFileSync(process.argv[2],String(child.pid)); setInterval(()=>{},1000)`)
    const pidFile = join(root, 'descendant.pid')
    const descendantDefinition = { ...definition, execution: { ...definition.execution!, args: [pidFile] } }
    const controller = new AbortController()
    const runner = createCliRunner({ registry: { codex: descendantDefinition }, limits: { killGraceMs: 20 } })
    const identity = await runner.inspectInstallation('codex'); await runner.confirmValidation('codex', identity, '1.0.0')
    const running = runner.runExecution('alice', 'codex', { modelId: null, stdin: '', signal: controller.signal })
    let childPid = 0
    // Parallel Vitest workers can delay process startup on a busy host; give
    // the fixture enough time to prove the descendant actually started.
    for (let attempt = 0; attempt < 400 && !childPid; attempt++) {
      try { childPid = Number(await readFile(pidFile, 'utf8')) } catch { await delay(5) }
    }
    expect(childPid).toBeGreaterThan(0)
    controller.abort()
    await expect(running).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    let alive = true
    for (let attempt = 0; attempt < 100 && alive; attempt++) {
      try { process.kill(childPid, 0); await delay(5) } catch { alive = false }
    }
    expect(alive).toBe(false)
  })

  it.each([
    ['lingering', 'setInterval(()=>{},1000)'],
    ['SIGTERM-resistant', "process.on('SIGTERM',()=>{}); setInterval(()=>{},1000)"],
  ])('terminates a %s descendant before a successful call resolves', async (_name, descendantSource) => {
    const { root, definition } = await fixture(`
      const {spawn}=require('node:child_process'); const fs=require('node:fs');
      const child=spawn(process.execPath,['-e',${JSON.stringify(descendantSource)}],{stdio:'ignore'});
      child.unref(); fs.writeFileSync(process.argv[2],String(child.pid)); process.stdout.write('ok')`)
    const pidFile = join(root, 'success-descendant.pid')
    const descendantDefinition = { ...definition, execution: { ...definition.execution!, args: [pidFile] } }
    const result = await createCliRunner({ registry: { codex: descendantDefinition }, limits: { killGraceMs: 20 } })
      .runProbeValidation('alice', 'codex', '')
    expect(result.stdout).toBe('ok')
    const childPid = Number(await readFile(pidFile, 'utf8'))
    expect(() => process.kill(childPid, 0)).toThrow()
  })

  it('observes fast child rejection while authorization commit fails', async () => {
    const { definition } = await fixture('process.exit(7)')
    const commitError = new Error('authorization commit failed')
    authorization.invoke.mockImplementation(async (_userId: string, _cliId: string,
      start: () => { completion: Promise<unknown> }, _purpose: string, beforeStart?: () => Promise<void>) => {
      await beforeStart?.()
      start()
      await delay(50)
      throw commitError
    })
    const unhandled: unknown[] = []
    const observe = (reason: unknown) => { unhandled.push(reason) }
    process.on('unhandledRejection', observe)
    try {
      await expect(createCliRunner({ registry: { codex: definition } })
        .runProbeValidation('alice', 'codex', '')).rejects.toBe(commitError)
      await delay(25)
      expect(unhandled).toEqual([])
    } finally { process.off('unhandledRejection', observe) }
  })
})
