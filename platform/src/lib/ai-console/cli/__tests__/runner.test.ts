import { chmod, mkdtemp, readFile, realpath, rm, symlink, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AiConsoleError } from '../../errors'
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

  it('sends Antigravity prompts as stream JSON over stdin instead of argv', async () => {
    const { definition } = await fixture(`
      let input=''; process.stdin.on('data', c => input += c); process.stdin.on('end', () => {
        const event=JSON.parse(input); process.stdout.write(JSON.stringify({event:'result',result:{
          status:'SUCCESS',response:JSON.stringify({event,argv:process.argv.slice(2)})}}))
      })`)
    const antigravity = { ...definition, id: 'gemini_antigravity' as const,
      execution: { args: ['--input-format', 'stream-json'], modelFlag: ['--model'],
        structuredSchemaFlag: ['--json-schema'], outputFormat: 'antigravity_stream_json' as const,
        transport: 'antigravity_stream_json' as const } }
    const runner = createCliRunner({ registry: { gemini_antigravity: antigravity } })
    const result = await runner.runProbeValidation('alice', 'gemini_antigravity', 'private prompt')
    const envelope = JSON.parse(JSON.parse(result.stdout).result.response)
    expect(envelope.event).toEqual({ event: 'user', message: { content: 'private prompt' } })
    expect(envelope.argv).toEqual(['--input-format', 'stream-json'])
    const identity = await runner.inspectInstallation('gemini_antigravity')
    await runner.confirmValidation('gemini_antigravity', identity, '1.0.0', [null])
    const generated = await runner.runExecution('alice', 'gemini_antigravity', {
      modelId: null, stdin: 'structured prompt', responseSchema: { type: 'object' },
    })
    const generatedEnvelope = JSON.parse(JSON.parse(generated.stdout).result.response)
    expect(generatedEnvelope.argv).toEqual([
      '--input-format', 'stream-json', '--json-schema', '{"type":"object"}',
    ])
  })

  it('discards successful auth-status output at the runner boundary', async () => {
    const { definition } = await fixture('process.stdout.write("private@example.com")')
    const result = await createCliRunner({ registry: { codex: definition } })
      .runAuthValidation('alice', 'codex')
    expect(result).toEqual({ stdout: '', exitCode: 0, signal: null })
    expect(JSON.stringify(result)).not.toContain('private@example.com')
  })

  it('sanitizes model-catalog output inside the runner boundary', async () => {
    const catalog = JSON.stringify({
      providers: { 'managed:kimi-code': { type: 'kimi', apiKey: 'private-token' } },
      models: { 'kimi-code/k3': { provider: 'managed:kimi-code', model: 'k3', displayName: 'K3' } },
    })
    const { definition } = await fixture(`process.stdout.write(${JSON.stringify(catalog)})`)
    const kimi = { ...definition, id: 'kimi_code' as const,
      modelCatalog: { args: ['provider', 'list', '--json'], format: 'kimi_provider_json' as const } }
    const result = await createCliRunner({ registry: { kimi_code: kimi } })
      .runModelCatalogValidation('alice', 'kimi_code')
    expect(result).toEqual([{ modelId: 'kimi-code/k3', displayName: 'K3' }])
    expect(JSON.stringify(result)).not.toContain('private-token')
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

  it('fails closed before inspecting or spawning CLIs in production unless the host opt-in is explicit', async () => {
    const { root, definition } = await fixture(`require('node:fs').writeFileSync(process.argv[2],'invoked')`)
    const marker = join(root, 'production-invoked.txt')
    const production = { ...definition, versionArgs: [marker] }
    const runner = createCliRunner({ registry: { codex: production }, environment: {
      ...process.env, NODE_ENV: 'production', MARSYS_AI_LOCAL_CLI_EXECUTION_ENABLED: 'false',
    } })
    await expect(runner.inspectInstallation('codex')).rejects.toMatchObject({ code: 'AI_CLI_UNREACHABLE' })
    await expect(runner.runVersionValidation('alice', 'codex')).rejects.toMatchObject({ code: 'AI_CLI_UNREACHABLE' })
    await expect(readFile(marker)).rejects.toMatchObject({ code: 'ENOENT' })
  })

  it('caps multibyte stdout and never returns stderr', async () => {
    const { definition } = await fixture('process.stderr.write("raw-secret"); process.stdout.write("💥".repeat(20))')
    const runner = createCliRunner({ registry: { codex: definition }, limits: { stdoutBytes: 20, stderrBytes: 8 } })
    const error = await runner.runProbeValidation('alice', 'codex', '').catch(value => value)
    expect(error).toMatchObject({ code: 'AI_CLI_OUTPUT_LIMIT' })
    expect(JSON.stringify(error)).not.toContain('raw-secret')
  })

  it('keeps the model token limit separate from the raw machine envelope limit', async () => {
    const envelope = JSON.stringify({ type: 'result', result: 'ok', padding: 'x'.repeat(20_000) })
    const { definition } = await fixture(`process.stdout.write(${JSON.stringify(envelope)})`)
    const runner = createCliRunner({ registry: { codex: definition } })
    const identity = await runner.inspectInstallation('codex')
    await runner.confirmValidation('codex', identity, '1.0.0', [null])

    await expect(runner.runExecution('alice', 'codex', {
      modelId: null, stdin: '', maxOutputTokens: 1,
    })).resolves.toEqual({ stdout: envelope, exitCode: 0, signal: null })
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
    const identity = await runner.inspectInstallation('codex')
    await runner.confirmValidation('codex', identity, '1.0.0', [null])
    await expect(runner.runExecution('alice', 'codex', { modelId: 'invented', stdin: '' }))
      .rejects.toMatchObject({ code: 'AI_MODEL_UNAVAILABLE' })
    await expect(runner.runProbeValidation('alice', 'codex', '123456789'))
      .rejects.toMatchObject({ code: 'AI_CLI_OUTPUT_LIMIT' })
  })

  it('executes only concrete model IDs sealed into the successful validation', async () => {
    const { definition } = await fixture('process.stdout.write(JSON.stringify(process.argv.slice(2)))')
    const runner = createCliRunner({ registry: { codex: definition } })
    const identity = await runner.inspectInstallation('codex')
    await runner.confirmValidation('codex', identity, '1.0.0', [null, 'approved-model'])
    await expect(runner.runExecution('alice', 'codex', { modelId: 'approved-model', stdin: '' }))
      .resolves.toMatchObject({ stdout: '["run","-m","approved-model"]' })
    await expect(runner.runExecution('alice', 'codex', { modelId: 'unapproved-model', stdin: '' }))
      .rejects.toMatchObject({ code: 'AI_MODEL_UNAVAILABLE' })
  })

  it('probes an exact manual model through CLI argv before admitting its execution', async () => {
    const { definition } = await fixture('process.stdout.write(JSON.stringify(process.argv.slice(2)))')
    const runner = createCliRunner({ registry: { codex: definition } })
    const identity = await runner.inspectInstallation('codex')
    await runner.confirmValidation('codex', identity, '1.0.0', [null])
    await expect(runner.runExecution('alice', 'codex', { modelId: 'manual-model', stdin: '' }))
      .rejects.toMatchObject({ code: 'AI_MODEL_UNAVAILABLE' })
    const probe = await runner.runModelProbeValidation('alice', 'codex', 'manual-model', 'Reply OK.')
    expect(probe.stdout).toBe('["run","-m","manual-model"]')
    await runner.confirmManualModel('codex', identity, 'manual-model')
    await expect(runner.runExecution('alice', 'codex', { modelId: 'manual-model', stdin: '' }))
      .resolves.toMatchObject({ stdout: '["run","-m","manual-model"]' })
  })

  it('runs Kimi over ACP in plan mode, with no MCP servers, and denies tool permission', async () => {
    const { definition } = await fixture(`
      const readline=require('node:readline'); const rl=readline.createInterface({input:process.stdin});
      let promptRequest; const seen={argv:process.argv.slice(2)};
      const send=value=>process.stdout.write(JSON.stringify(value)+'\\n');
      rl.on('line', line=>{ const message=JSON.parse(line);
        if(message.method==='initialize') send({jsonrpc:'2.0',id:message.id,result:{protocolVersion:1,
          agentCapabilities:{},agentInfo:{name:'Fake Kimi',version:'2.0.2'}}});
        else if(message.method==='session/new') { seen.cwd=message.params.cwd; seen.mcp=message.params.mcpServers;
          send({jsonrpc:'2.0',id:message.id,result:{sessionId:'safe-session',configOptions:[
            {type:'select',id:'model',currentValue:'kimi-code/k3',options:[{value:'kimi-code/k3',name:'K3'}]},
            {type:'select',id:'mode',currentValue:'default',options:[{value:'plan',name:'Plan'}]}]}}); }
        else if(message.method==='session/set_config_option') { seen[message.params.configId]=message.params.value;
          send({jsonrpc:'2.0',id:message.id,result:{configOptions:[]}}); }
        else if(message.method==='session/prompt') { promptRequest=message; seen.prompt=message.params.prompt;
          send({jsonrpc:'2.0',id:99,method:'session/request_permission',params:{sessionId:'safe-session',
            options:[{optionId:'allow_once',name:'Allow once',kind:'allow_once'}]}}); }
        else if(message.id===99) { seen.permission=message.result;
          send({jsonrpc:'2.0',method:'session/update',params:{sessionId:'safe-session',update:{
            sessionUpdate:'agent_message_chunk',content:{type:'text',text:JSON.stringify(seen)}}}});
          send({jsonrpc:'2.0',id:promptRequest.id,result:{stopReason:'end_turn'}}); }
      });`)
    const kimi = { ...definition, id: 'kimi_code' as const,
      execution: { args: ['acp'], modelFlag: [], outputFormat: 'kimi_acp_json' as const,
        transport: 'kimi_acp' as const } }
    const runner = createCliRunner({ registry: { kimi_code: kimi } })
    const probe = await runner.runProbeValidation('alice', 'kimi_code', 'probe prompt')
    expect(JSON.parse(probe.stdout).text).toContain('probe prompt')
    const identity = await runner.inspectInstallation('kimi_code')
    await runner.confirmValidation('kimi_code', identity, '1.0.0', [null, 'kimi-code/k3'])

    const result = await runner.runExecution('alice', 'kimi_code', {
      modelId: 'kimi-code/k3', stdin: 'private prompt',
    })
    const normalized = JSON.parse(result.stdout)
    const seen = JSON.parse(normalized.text)
    expect(seen.argv).toEqual(['acp'])
    expect(seen.mcp).toEqual([])
    expect(seen.mode).toBe('plan')
    expect(seen.model).toBe('kimi-code/k3')
    expect(seen.prompt).toEqual([{ type: 'text', text: 'private prompt' }])
    expect(seen.permission).toEqual({ outcome: { outcome: 'cancelled' } })
    expect(seen.cwd).toMatch(/madhav-ai-cli-/)
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
    await runner.confirmValidation('codex', identity, '1.0.0', [null])
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
    await runner.confirmValidation('codex', identity, '1.0.0', [null])
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
    await runner.confirmValidation('codex', identity, '1.0.0', [null])
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
    await expect(runner.confirmValidation('codex', identity, '2.0.0', [null]))
      .rejects.toMatchObject({ code: 'AI_CLI_UNREACHABLE' })
  })

  it('rehydrates executable identity and the model allowlist before first execution after restart', async () => {
    const { definition } = await fixture('process.stdout.write(JSON.stringify(process.argv.slice(2)))')
    const revalidate = vi.fn(async (_userId, cliId, _signal, target) => {
      const identity = await target.inspectInstallation(cliId)
      await target.confirmValidation(cliId, identity, '1.0.0', [null, 'approved-model'])
    })
    const runner = createCliRunner({ registry: { codex: definition }, revalidate })
    await expect(runner.runExecution('alice', 'codex', { modelId: 'approved-model', stdin: '' }))
      .resolves.toMatchObject({ stdout: '["run","-m","approved-model"]' })
    expect(revalidate).toHaveBeenCalledOnce()
    await expect(runner.runExecution('alice', 'codex', { modelId: 'approved-model', stdin: '' }))
      .resolves.toMatchObject({ stdout: '["run","-m","approved-model"]' })
    expect(revalidate).toHaveBeenCalledOnce()
  })

  it('preserves revoked permission and caller abort errors during restart revalidation', async () => {
    const { definition } = await fixture('process.stdout.write("must-not-run")')
    const revoked = createCliRunner({ registry: { codex: definition },
      revalidate: vi.fn().mockRejectedValue(new AiConsoleError('AI_CLI_NOT_GRANTED')) })
    await expect(revoked.runExecution('alice', 'codex', { modelId: null, stdin: '' }))
      .rejects.toMatchObject({ code: 'AI_CLI_NOT_GRANTED' })

    const controller = new AbortController(); controller.abort()
    const aborted = createCliRunner({ registry: { codex: definition },
      revalidate: vi.fn().mockRejectedValue(new AiConsoleError('AI_EXECUTION_FAILED')) })
    await expect(aborted.runExecution('alice', 'codex', { modelId: null, stdin: '', signal: controller.signal }))
      .rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
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
    const identity = await runner.inspectInstallation('codex')
    await runner.confirmValidation('codex', identity, '1.0.0', [null])
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
