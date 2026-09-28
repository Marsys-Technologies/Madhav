import { chmod, mkdir, mkdtemp, symlink, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { afterEach, describe, expect, it } from 'vitest'
import { preflightOwnerFixture } from '../../../../scripts/ai-console/owner_preflight'

const scratch: string[] = []

async function privateFixture(overrides: Record<string, unknown> = {}) {
  const root = await mkdtemp(join(tmpdir(), 'aic-owner-'))
  scratch.push(root)
  await chmod(root, 0o700)
  const paths = {
    serverLogPath: join(root, 'server.log'), routingSnapshotPath: join(root, 'routing.json'),
    observatoryPath: join(root, 'observatory.json'), auditPath: join(root, 'audit.json'), artifactDirectory: join(root, 'artifacts'),
  }
  await mkdir(paths.artifactDirectory, { mode: 0o700 })
  for (const path of [paths.serverLogPath, paths.routingSnapshotPath, paths.observatoryPath, paths.auditPath]) {
    await writeFile(path, '{}\n', { mode: 0o600 })
  }
  const value = {
    userId: 'owner-1', conversationId: '10000000-0000-4000-8000-000000000001', pariprashnaPath: '/clients/1/pariprashna',
    providers: { openai: { apiKey: 'fixture-only' } },
    sameProvider: { providerId: 'openai', first: { apiKey: 'fixture-first' }, second: { apiKey: 'fixture-second' } },
    pariprashnaRequest: { chartId: '20000000-0000-4000-8000-000000000002', messages: [{ role: 'user', parts: [{ type: 'text', text: 'fixture' }] }] },
    consultRequest: { chartId: '20000000-0000-4000-8000-000000000002', messages: [{ role: 'user', parts: [{ type: 'text', text: 'fixture' }] }] },
    inspection: {
      identityUrl: 'http://127.0.0.1:3000/local-test/identity',
      routingEvidenceUrlTemplate: 'http://127.0.0.1:3000/local-test/routing/{turnId}',
      latestEvidenceUrl: 'http://127.0.0.1:3000/local-test/routing/latest',
    },
    leakage: { ...paths, urls: ['http://127.0.0.1:3000/api/ai-console'] },
    ...overrides,
  }
  const path = join(root, 'owner.json')
  await writeFile(path, JSON.stringify(value), { mode: 0o600 })
  return { root, path, value }
}

afterEach(async () => {
  const { rm } = await import('node:fs/promises')
  await Promise.all(scratch.splice(0).map(path => rm(path, { recursive: true, force: true })))
})

describe('owner fixture preflight', () => {
  it('accepts an owner-only regular fixture outside the repository with loopback inspection inputs', async () => {
    const fixture = await privateFixture()
    await expect(preflightOwnerFixture(fixture.path, {
      platformRoot: '/workspace/repository/platform', baseUrl: 'http://localhost:3000',
    })).resolves.toMatchObject({ ok: true })
  })

  it('rejects symlinked or group/world-readable fixture files', async () => {
    const fixture = await privateFixture()
    const link = join(fixture.root, 'owner-link.json')
    await symlink(fixture.path, link)
    await expect(preflightOwnerFixture(link, {
      platformRoot: '/workspace/repository/platform', baseUrl: 'http://localhost:3000',
    })).resolves.toEqual({ ok: false, code: 'AIC_ACCEPTANCE_OWNER_FIXTURE_SYMLINK' })

    await chmod(fixture.path, 0o644)
    await expect(preflightOwnerFixture(fixture.path, {
      platformRoot: '/workspace/repository/platform', baseUrl: 'http://localhost:3000',
    })).resolves.toEqual({ ok: false, code: 'AIC_ACCEPTANCE_OWNER_FIXTURE_PERMISSIONS' })
  })

  it('rejects a fixture inside the repository and malformed or non-loopback URLs', async () => {
    const fixture = await privateFixture({ inspection: {
      identityUrl: 'https://example.com/identity',
      routingEvidenceUrlTemplate: 'http://127.0.0.1:3000/routing/{turnId}',
      latestEvidenceUrl: 'http://127.0.0.1:3000/routing/latest',
    } })
    await expect(preflightOwnerFixture(fixture.path, {
      platformRoot: fixture.root, baseUrl: 'http://localhost:3000',
    })).resolves.toEqual({ ok: false, code: 'AIC_ACCEPTANCE_OWNER_FIXTURE_IN_REPOSITORY' })
    await expect(preflightOwnerFixture(fixture.path, {
      platformRoot: '/workspace/repository/platform', baseUrl: 'http://localhost:3000',
    })).resolves.toEqual({ ok: false, code: 'AIC_ACCEPTANCE_OWNER_FIXTURE_INVALID' })
    await expect(preflightOwnerFixture(fixture.path, {
      platformRoot: '/workspace/repository/platform', baseUrl: 'https://example.com',
    })).resolves.toEqual({ ok: false, code: 'AIC_ACCEPTANCE_BASE_URL_NOT_LOOPBACK' })
  })

  it('rejects a fixture stored inside its evidence artifact directory', async () => {
    const fixture = await privateFixture()
    const value = { ...fixture.value, leakage: { ...(fixture.value.leakage as object), artifactDirectory: fixture.root } }
    await writeFile(fixture.path, JSON.stringify(value), { mode: 0o600 })
    await expect(preflightOwnerFixture(fixture.path, {
      platformRoot: '/workspace/repository/platform', baseUrl: 'http://localhost:3000',
    })).resolves.toEqual({ ok: false, code: 'AIC_ACCEPTANCE_OWNER_FIXTURE_IN_ARTIFACTS' })
  })
})
