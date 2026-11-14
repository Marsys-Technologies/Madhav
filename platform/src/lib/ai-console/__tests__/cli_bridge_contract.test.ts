import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { EventEmitter } from 'node:events'
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'

type FixtureRequest = AsyncIterable<Buffer> & {
  method: string; url: string; headers: Record<string, string>
}
type FixtureResponse = { setHeader: () => void; statusCode: number; end: (body: string) => void }
const fixture = vi.hoisted(() => ({
  handler: undefined as undefined | ((request: FixtureRequest, response: FixtureResponse) => Promise<void>),
  spawn: vi.fn(), stdin: vi.fn(), writeFile: vi.fn(), rm: vi.fn(),
  fail: false,
}))
// Import the real executable below with every effectful boundary mocked. No
// actual HTTP listener, filesystem token/schema, CLI process or provider is used.
vi.mock('node:http', () => ({ createServer: (handler: typeof fixture.handler) => {
  fixture.handler = handler
  return { listen: vi.fn() }
} }))
vi.mock('node:child_process', () => ({ spawn: fixture.spawn }))
vi.mock('node:fs/promises', () => ({
  readFile: vi.fn(async () => 'synthetic-bridge-token-for-contract-tests'),
  mkdtemp: vi.fn(async () => '/Users/Dev/scratch.noindex/codex/madhav/20261114-bridge-live-contract-source/mock-execution'),
  writeFile: fixture.writeFile, rm: fixture.rm,
  lstat: vi.fn(), realpath: vi.fn(), stat: vi.fn(),
}))

const repositoryRoot = resolve(__dirname, '../../../../..')
const bridge = readFileSync(resolve(repositoryRoot, 'platform/scripts/ai-cli-bridge/server.mjs'), 'utf8')
const smoke = readFileSync(resolve(repositoryRoot, 'platform/scripts/ai-cli-bridge/smoke.mjs'), 'utf8')
const service = readFileSync(
  resolve(repositoryRoot, 'platform/scripts/ai-cli-bridge/marsys-ai-cli-bridge.service'),
  'utf8',
)

describe('private AI CLI bridge contract', () => {
  it('allows only fixed operations and executable paths', () => {
    expect(bridge).toContain("['inspect', 'confirm', 'version', 'auth', 'catalog', 'probe', 'probe_model', 'execute']")
    expect(bridge).toContain("path: join(HOME, '.local/bin/codex')")
    expect(bridge).toContain("path: join(HOME, '.local/bin/claude')")
    expect(bridge).toContain("path: join(HOME, '.local/bin/agy')")
    expect(bridge).toContain("versions: ['1.2.12', '1.2.13', '1.2.15']")
    expect(bridge).toContain('definition.versions.includes(payload.version)')
    expect(bridge).toContain("path: join(HOME, '.kimi-code/bin/kimi')")
    expect(bridge).not.toMatch(/raw\.(?:args|command|executable)/)
    expect(bridge).not.toContain('shell: true')
    expect(bridge.match(/return await runCommand/g)).toHaveLength(3)
    expect(bridge).toContain('return await runKimiAcp')
  })

  it('limits execution effort to known CLI model IDs and fixed arguments', () => {
    expect(bridge).toContain('const SAFE_EFFORT = /^[a-z][a-z0-9_]{0,31}$/')
    expect(bridge).toContain('models.get(modelId)?.includes(effort)')
    expect(bridge).toContain("if (effort) args.push('-c', `model_reasoning_effort=${effort}`)")
    expect(bridge).toContain("if (effort) args.push('--effort', effort)")
    expect(bridge).toContain("!['codex', 'claude_code'].includes(cliId)")
  })

  it('requires a file-backed bearer token and constant-time comparison', () => {
    expect(bridge).toContain("if (!TOKEN_FILE) throw new Error('MARSYS_AI_CLI_BRIDGE_TOKEN_FILE is required')")
    expect(bridge).toContain('timingSafeEqual(supplied, expected)')
    expect(bridge).toContain("response.setHeader('Cache-Control', 'no-store')")
  })

  it('smoke-tests every supported Antigravity version and confirms the detected one', () => {
    expect(smoke).toContain("versions: ['1.2.12', '1.2.13', '1.2.15']")
    expect(smoke).toContain('version: acceptedVersion')
  })

  it('runs as the non-root CLI owner with basic systemd isolation', () => {
    expect(service).toContain('User=mail_abhisek_mohanty_gmail_com')
    expect(service).toContain('NoNewPrivileges=true')
    expect(service).toContain('PrivateTmp=true')
    expect(service).toContain('ProtectSystem=strict')
    expect(service).toContain('MARSYS_AI_CLI_BRIDGE_HOST=10.160.0.2')
  })
})

describe('running bridge stdin/schema contract — real handler, mocked boundaries', () => {
  beforeAll(async () => {
    vi.stubEnv('MARSYS_AI_CLI_BRIDGE_TOKEN_FILE', '/Users/Dev/scratch.noindex/codex/madhav/20261114-bridge-live-contract-source/mock-token')
    await import('../../../../scripts/ai-cli-bridge/server.mjs')
  })
  beforeEach(() => {
    fixture.fail = false
    fixture.spawn.mockReset()
    fixture.stdin.mockReset()
    fixture.writeFile.mockReset().mockResolvedValue(undefined)
    fixture.rm.mockReset().mockResolvedValue(undefined)
    // Simulated child is already gone when production cleanup checks its PID.
    vi.spyOn(process, 'kill').mockImplementation(() => { throw Object.assign(new Error('gone'), { code: 'ESRCH' }) })
    fixture.spawn.mockImplementation((_executable: string, args: string[]) => {
      const child = Object.assign(new EventEmitter(), {
        pid: 424242, stdout: new EventEmitter(), stderr: new EventEmitter(),
        stdin: Object.assign(new EventEmitter(), { end: (input: string) => {
          fixture.stdin(input)
          queueMicrotask(() => {
            if (fixture.fail) {
              child.stderr.emit('data', Buffer.from('synthetic-private-stderr'))
              child.emit('close', 1, null)
            } else {
              const output = args[0] === 'auth'
                ? '{"loggedIn":true,"authMethod":"claude.ai","apiProvider":"firstParty"}'
                : '{"result":"synthetic answer"}'
              child.stdout.emit('data', Buffer.from(output))
              child.emit('close', 0, null)
            }
          })
        } }),
      })
      return child
    })
  })
  afterEach(() => { vi.restoreAllMocks() })
  afterAll(() => { vi.unstubAllEnvs() })

  async function invoke(stdin: string, options: { schema?: object; padding?: number; chunked?: boolean; token?: string } = {}) {
    const payload = { operation: 'execute', cliId: 'claude_code', modelId: null, stdin,
      ...(options.schema ? { responseSchema: options.schema } : {}) }
    const body = ' '.repeat(options.padding ?? 0) + JSON.stringify(payload)
    const request: FixtureRequest = {
      method: 'POST', url: '/v1/invoke',
      headers: { authorization: `Bearer ${options.token ?? 'synthetic-bridge-token-for-contract-tests'}`,
        ...(options.chunked ? {} : { 'content-length': String(Buffer.byteLength(body)) }) },
      async *[Symbol.asyncIterator]() { yield Buffer.from(body) },
    }
    const response = { setHeader: vi.fn(), statusCode: 0, end: vi.fn() }
    await fixture.handler!(request, response)
    return { status: response.statusCode, body: JSON.parse(response.end.mock.calls[0][0]) }
  }

  it.each([256 * 1024 + 1, 1024 * 1024, 3 * 1024 * 1024])('accepts %i stdin bytes without truncation', async (bytes) => {
    expect(await invoke('x'.repeat(bytes))).toMatchObject({ status: 200 })
    expect(Buffer.byteLength(fixture.stdin.mock.calls.at(-1)![0])).toBe(bytes)
    expect(fixture.spawn).toHaveBeenCalledTimes(2) // fixed auth check + generation
  })

  it('accepts JSON body overhead above the stdin cap, within the running body cap', async () => {
    expect(await invoke('x'.repeat(3 * 1024 * 1024), { padding: 100 * 1024 })).toMatchObject({ status: 200 })
  })

  it('rejects stdin above 3 MiB before launching even the auth command', async () => {
    expect(await invoke('x'.repeat(3 * 1024 * 1024 + 1)))
      .toEqual({ status: 422, body: { error: 'AI_CLI_OUTPUT_LIMIT' } })
    expect(fixture.spawn).not.toHaveBeenCalled()
  })

  it.each([false, true])('keeps the body cap enforced (chunked=%s)', async (chunked) => {
    expect(await invoke('', { padding: 3 * 1024 * 1024 + 512 * 1024 + 1, chunked }))
      .toEqual({ status: 422, body: { error: 'AI_CLI_OUTPUT_LIMIT' } })
    expect(fixture.spawn).not.toHaveBeenCalled()
  })

  it('passes Claude schema as literal JSON while retaining private temporary schema cleanup', async () => {
    const schema = { type: 'object', properties: { answer: { type: 'string' } } }
    expect(await invoke('synthetic question', { schema })).toMatchObject({ status: 200 })
    const args: string[] = fixture.spawn.mock.calls.at(-1)![1]
    expect(args[args.indexOf('--json-schema') + 1]).toBe(JSON.stringify(schema))
    expect(fixture.writeFile).toHaveBeenCalledWith(expect.stringContaining('/output-schema.json'),
      JSON.stringify(schema), { mode: 0o600, flag: 'wx' })
    expect(fixture.rm).toHaveBeenCalledWith(expect.any(String), { recursive: true, force: true })
  })

  it('still refuses unauthorized callers without spawning', async () => {
    expect(await invoke('question', { token: 'wrong' })).toEqual({ status: 401, body: { error: 'unauthorized' } })
    expect(fixture.spawn).not.toHaveBeenCalled()
  })

  it('keeps private child stderr out of both response and diagnostic logging', async () => {
    fixture.fail = true
    const log = vi.spyOn(process.stderr, 'write').mockReturnValue(true)
    const result = await invoke('question')
    expect(result).toEqual({ status: 503, body: { error: 'AI_CLI_AUTH_UNAVAILABLE' } })
    expect(JSON.stringify(result)).not.toContain('synthetic-private-stderr')
    expect(log.mock.calls.flat().join(' ')).not.toContain('synthetic-private-stderr')
  })
})
