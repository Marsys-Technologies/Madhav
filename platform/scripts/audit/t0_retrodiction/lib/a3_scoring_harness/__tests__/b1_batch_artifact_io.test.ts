import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import * as fs from 'node:fs'
import * as os from 'node:os'
import * as path from 'node:path'
import {
  hashManifestFile,
  writeBatchArtifact,
  readBatchArtifact,
  checkManifestHashConsistency,
} from '../b1_batch_artifact_io'

describe('b1_batch_artifact_io', () => {
  let tmpDir: string
  let manifestPath: string
  let artifactsDir: string

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'b1-batch-io-test-'))
    manifestPath = path.join(tmpDir, 'manifest.json')
    artifactsDir = path.join(tmpDir, 'batches')
    fs.writeFileSync(manifestPath, JSON.stringify({ hello: 'world' }))
  })

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true })
  })

  it('hashManifestFile is deterministic for identical bytes', () => {
    const h1 = hashManifestFile(manifestPath)
    const h2 = hashManifestFile(manifestPath)
    expect(h1).toBe(h2)
    expect(h1).toMatch(/^[0-9a-f]{64}$/)
  })

  it('hashManifestFile changes when the file content changes', () => {
    const before = hashManifestFile(manifestPath)
    fs.writeFileSync(manifestPath, JSON.stringify({ hello: 'different' }))
    const after = hashManifestFile(manifestPath)
    expect(after).not.toBe(before)
  })

  it('writes and reads back a batch artifact round-trip', () => {
    const hash = hashManifestFile(manifestPath)
    const file = writeBatchArtifact(artifactsDir, 'batch1', hash, { score: 42 }, '2026-07-22T00:00:00Z')
    const readBack = readBatchArtifact<{ score: number }>(file)
    expect(readBack.batchKey).toBe('batch1')
    expect(readBack.manifestHash).toBe(hash)
    expect(readBack.results.score).toBe(42)
  })

  it('re-writing the same batch against the SAME manifest hash overwrites (idempotent, no double-count)', () => {
    const hash = hashManifestFile(manifestPath)
    writeBatchArtifact(artifactsDir, 'batch1', hash, { score: 1 }, '2026-07-22T00:00:00Z')
    writeBatchArtifact(artifactsDir, 'batch1', hash, { score: 2 }, '2026-07-22T00:01:00Z')
    const file = path.join(artifactsDir, 'batch_batch1.json')
    const readBack = readBatchArtifact<{ score: number }>(file)
    expect(readBack.results.score).toBe(2) // overwritten, not accumulated
    const filesInDir = fs.readdirSync(artifactsDir)
    expect(filesInDir.length).toBe(1) // no duplicate files
  })

  it('refuses to overwrite a batch artifact with a DIFFERENT manifest hash', () => {
    const hash1 = hashManifestFile(manifestPath)
    writeBatchArtifact(artifactsDir, 'batch1', hash1, { score: 1 }, '2026-07-22T00:00:00Z')
    fs.writeFileSync(manifestPath, JSON.stringify({ hello: 'changed' }))
    const hash2 = hashManifestFile(manifestPath)
    expect(hash2).not.toBe(hash1)
    expect(() => writeBatchArtifact(artifactsDir, 'batch1', hash2, { score: 99 }, '2026-07-22T00:02:00Z')).toThrow(
      /refusing to overwrite/,
    )
  })

  it('checkManifestHashConsistency reports consistent when all batches match the current manifest', () => {
    const hash = hashManifestFile(manifestPath)
    writeBatchArtifact(artifactsDir, 'batch1', hash, { score: 1 }, '2026-07-22T00:00:00Z')
    writeBatchArtifact(artifactsDir, 'batch2', hash, { score: 2 }, '2026-07-22T00:01:00Z')
    const result = checkManifestHashConsistency(artifactsDir, manifestPath)
    expect(result.consistent).toBe(true)
    expect(result.mismatches).toEqual([])
  })

  it('checkManifestHashConsistency FAILS LOUDLY when a batch was written against a stale manifest', () => {
    const hash1 = hashManifestFile(manifestPath)
    writeBatchArtifact(artifactsDir, 'batch1', hash1, { score: 1 }, '2026-07-22T00:00:00Z')
    // Manifest changes after batch1 was written but before batch2 runs -- simulate by
    // writing batch2 with a hand-crafted stale hash via direct file write (bypassing the
    // write-time guard, which only protects same-key overwrites, not cross-batch drift).
    fs.mkdirSync(artifactsDir, { recursive: true })
    fs.writeFileSync(
      path.join(artifactsDir, 'batch_batch2.json'),
      JSON.stringify({ batchKey: 'batch2', manifestHash: 'stale-hash-from-before-a-manifest-bump', writtenAt: 't', results: {} }),
    )
    const result = checkManifestHashConsistency(artifactsDir, manifestPath)
    expect(result.consistent).toBe(false)
    expect(result.mismatches).toEqual([{ batchKey: 'batch2', foundHash: 'stale-hash-from-before-a-manifest-bump' }])
  })

  it('checkManifestHashConsistency reports not consistent when the artifacts dir does not exist yet', () => {
    const result = checkManifestHashConsistency(path.join(tmpDir, 'does-not-exist'), manifestPath)
    expect(result.consistent).toBe(false)
  })
})
