import { appendFile, chmod, mkdtemp, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { afterEach, describe, expect, it } from 'vitest'
import {
  captureLeakageBaseline,
  containsForbiddenLeakage,
  readFreshLeakageEvidence,
} from '../../../../scripts/ai-console/leakage_evidence'

const directories: string[] = []

afterEach(async () => {
  await Promise.all(directories.splice(0).map(path => rm(path, { recursive: true, force: true })))
})

describe('current-run leakage evidence', () => {
  it('rejects stale or empty evidence and accepts only appended current-run correlation', async () => {
    const directory = await mkdtemp(join(tmpdir(), 'aic-leakage-'))
    directories.push(directory)
    const path = join(directory, 'observatory.jsonl')
    await writeFile(path, '{}\n')
    await chmod(path, 0o600)
    const baseline = await captureLeakageBaseline(path)
    await expect(readFreshLeakageEvidence(baseline, {
      runStartedAtMs: Date.parse('2026-09-28T00:00:00.000Z'), markers: ['turn-current'],
    })).rejects.toThrow('AIC_E2E_LEAKAGE_INPUT_STALE')
    await appendFile(path, '{"correlationId":"turn-current","createdAt":"2026-09-28T00:00:01.000Z"}\n')
    await expect(readFreshLeakageEvidence(baseline, {
      runStartedAtMs: Date.parse('2026-09-28T00:00:00.000Z'), markers: ['turn-current'],
    })).resolves.toContain('turn-current')
  })

  it('detects forbidden fields and broader credential formats without returning a match', () => {
    expect(containsForbiddenLeakage('{"wrapped_data_key":"redacted"}', [])).toBe(true)
    expect(containsForbiddenLeakage('{"request":{"path":"/private/file"}}', [])).toBe(true)
    expect(containsForbiddenLeakage('Authorization: Bearer abcdefghijklmnop', [])).toBe(true)
    expect(containsForbiddenLeakage('{"status":"success","correlationId":"turn-1"}', [])).toBe(false)
    expect(containsForbiddenLeakage('safe output with owner-key-value', ['owner-key-value'])).toBe(true)
  })
})
