import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AiConsoleError } from '../../errors'

const authorization = vi.hoisted(() => ({ invoke: vi.fn() }))
vi.mock('../../repository', () => ({ withCliInvocationAuthorization: authorization.invoke }))

import { createConfiguredCliRunner, createRemoteCliRunner } from '../runner'

const token = 't'.repeat(64)
const identity = {
  cliId: 'codex' as const,
  entrypoint: {
    candidate: '/home/owner/.local/bin/codex', realpath: '/home/owner/.local/bin/codex',
    device: '1', inode: '2', size: 10, modifiedMs: 1, changedMs: 1, mode: 0o100755, uid: 1000,
    sha256: 'a'.repeat(64),
  },
}

beforeEach(() => {
  authorization.invoke.mockReset()
  authorization.invoke.mockImplementation(async (_userId: string, _cliId: string,
    start: () => unknown) => start())
})

describe('remote CLI runner', () => {
  it('uses the private bridge without enabling local production process execution', async () => {
    const calls: Array<{ url: string; init: RequestInit; body: Record<string, unknown> }> = []
    const fetchImpl = vi.fn(async (input: URL | RequestInfo, init?: RequestInit) => {
      const body = JSON.parse(String(init?.body))
      calls.push({ url: String(input), init: init!, body })
      if (body.operation === 'inspect') return Response.json(identity)
      return Response.json({ stdout: 'codex-cli 0.158.0', exitCode: 0, signal: null })
    }) as unknown as typeof fetch
    const runner = createRemoteCliRunner({ endpoint: 'http://10.160.0.2:8787', token, fetchImpl })

    await expect(runner.inspectInstallation('codex')).resolves.toEqual(identity)
    await expect(runner.runVersionValidation('owner', 'codex')).resolves.toMatchObject({ exitCode: 0 })

    expect(calls).toHaveLength(2)
    expect(calls.every(call => call.url === 'http://10.160.0.2:8787/v1/invoke')).toBe(true)
    expect(calls.every(call => (call.init.headers as Record<string, string>).Authorization === `Bearer ${token}`)).toBe(true)
    expect(JSON.stringify(calls)).not.toContain('owner')
    expect(authorization.invoke).toHaveBeenCalledWith('owner', 'codex', expect.any(Function), 'validation')
  })

  it('fails closed for a public plaintext bridge, partial configuration, malformed responses, and safe remote errors', async () => {
    expect(() => createRemoteCliRunner({ endpoint: 'http://example.com:8787', token }))
      .toThrowError(AiConsoleError)
    expect(() => createRemoteCliRunner({ endpoint: 'https://example.com:8787', token }))
      .toThrowError(AiConsoleError)
    expect(() => createRemoteCliRunner({ endpoint: 'http://10.evil.example:8787', token }))
      .toThrowError(AiConsoleError)
    expect(() => createConfiguredCliRunner({ NODE_ENV: 'production', MARSYS_AI_CLI_BRIDGE_URL: 'http://10.0.0.2' }))
      .toThrowError(AiConsoleError)

    const malformed = createRemoteCliRunner({ endpoint: 'http://127.0.0.1:8787', token,
      fetchImpl: vi.fn(async () => Response.json({ secret: 'raw' })) as unknown as typeof fetch })
    await expect(malformed.runVersionValidation('owner', 'codex'))
      .rejects.toMatchObject({ code: 'AI_CLI_UNREACHABLE' })

    const timeout = createRemoteCliRunner({ endpoint: 'http://127.0.0.1:8787', token,
      fetchImpl: vi.fn(async () => Response.json({ error: 'AI_CLI_TIMEOUT' }, { status: 504 })) as unknown as typeof fetch })
    await expect(timeout.runProbeValidation('owner', 'codex', 'private prompt'))
      .rejects.toMatchObject({ code: 'AI_CLI_TIMEOUT' })
  })

  it('rejects unknown models after safe catalogue refresh and only executes a confirmed advertised model', async () => {
    const operations: string[] = []
    const executionBodies: Array<Record<string, unknown>> = []
    const confirmationBodies: Array<Record<string, unknown>> = []
    const fetchImpl = vi.fn(async (_input: URL | RequestInfo, init?: RequestInit) => {
      const body = JSON.parse(String(init?.body))
      operations.push(body.operation)
      if (body.operation === 'inspect') return Response.json(identity)
      if (body.operation === 'catalog') return Response.json({ models: [
        { modelId: 'gpt-6-sol', displayName: 'GPT-6 Sol', supportedEfforts: ['medium'],
          defaultEffort: 'medium', isCatalogDiscovered: true },
      ] })
      if (body.operation === 'confirm') {
        confirmationBodies.push(body)
        return Response.json({ ok: true })
      }
      if (body.operation === 'execute') {
        executionBodies.push(body)
        return Response.json({ stdout: '{"type":"turn.completed","usage":{}}', exitCode: 0, signal: null })
      }
      throw new Error(`unexpected ${body.operation}`)
    }) as unknown as typeof fetch
    const runner = createRemoteCliRunner({ endpoint: 'http://10.160.0.2:8787', token, fetchImpl })
    await runner.runModelCatalogValidation('owner', 'codex')
    await runner.confirmValidation('codex', identity, '0.158.0', [null, 'gpt-6-sol'])

    await expect(runner.runExecution('owner', 'codex', { modelId: 'not-approved', stdin: 'prompt' }))
      .rejects.toMatchObject({ code: 'AI_MODEL_UNAVAILABLE' })
    await expect(runner.runExecution('owner', 'codex', { modelId: 'gpt-6-sol', stdin: 'prompt', effort: 'medium' }))
      .resolves.toMatchObject({ exitCode: 0 })
    expect(executionBodies).toEqual([expect.objectContaining({ modelId: 'gpt-6-sol', effort: 'medium' })])
    expect(confirmationBodies.map(body => body.modelIds)).toEqual([
      [null, 'gpt-6-sol'], [null, 'gpt-6-sol'],
    ])
    expect(operations).toEqual(['catalog', 'confirm', 'inspect', 'catalog', 'inspect', 'confirm', 'execute'])
  })

  it('probes an exact remote CLI model before admitting it to execution', async () => {
    const operations: Array<Record<string, unknown>> = []
    const fetchImpl = vi.fn(async (_input: URL | RequestInfo, init?: RequestInit) => {
      const body = JSON.parse(String(init?.body)) as Record<string, unknown>
      operations.push(body)
      if (body.operation === 'confirm') return Response.json({ ok: true })
      return Response.json({ stdout: 'safe-machine-output', exitCode: 0, signal: null })
    }) as unknown as typeof fetch
    const runner = createRemoteCliRunner({ endpoint: 'http://10.160.0.2:8787', token, fetchImpl })
    await runner.confirmValidation('codex', identity, '0.158.0', [null])
    await runner.runModelProbeValidation('owner', 'codex', 'manual-model', 'Reply OK.')
    await runner.confirmManualModel('codex', identity, 'manual-model')
    await runner.runExecution('owner', 'codex', { modelId: 'manual-model', stdin: 'prompt' })
    expect(operations.map(item => item.operation)).toEqual(['confirm', 'probe_model', 'execute'])
    expect(operations[1]).toMatchObject({ cliId: 'codex', modelId: 'manual-model', stdin: 'Reply OK.' })
    expect(JSON.stringify(operations.slice(1))).not.toContain('owner')
  })
})
