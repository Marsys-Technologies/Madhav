/**
 * b1_batch_artifact_io.ts — D-4b B-1 chunked re-run, reusable checkpointed-batching
 * infrastructure (CR-122, MARSYS_DEFECT_GAP_REGISTER_v2_0.md).
 *
 * Two consecutive unchunked B-1 dispatches crashed with zero committed progress
 * (hundreds of live sidecar/DB calls in one continuous agent turn). This module
 * is the durable fix: idempotent, delete-then-insert-per-key intermediate-artifact
 * I/O so a batch can be re-run without double-counting, and an assembly-time
 * manifest-hash consistency check so mismatched batches fail loudly instead of
 * silently merging incompatible inputs.
 *
 * Not scoped to B-1 specifically — any future heavy scoring lane (per CR-122)
 * should reuse this pattern: commit an immutable run manifest first, batch by
 * a natural key (contenders, event ranges, whatever fits the lane), write one
 * intermediate artifact file per batch keyed by (batchKey, manifestHash), and
 * assemble once at the end with a hash-consistency check.
 */

import { createHash } from 'node:crypto'
import * as fs from 'node:fs'
import * as path from 'node:path'

export interface BatchArtifact<TResult> {
  batchKey: string
  manifestHash: string
  writtenAt: string // ISO timestamp, caller-supplied (this module does not call Date.now())
  results: TResult
}

/** sha256 of a file's exact committed bytes -- the manifest-hash every batch must agree on. */
export function hashManifestFile(manifestPath: string): string {
  const bytes = fs.readFileSync(manifestPath)
  return createHash('sha256').update(bytes).digest('hex')
}

/**
 * Idempotent write: overwrites any prior artifact for the same (batchKey, manifestHash)
 * pair rather than appending -- a re-run of the same batch against the same manifest
 * never double-counts. A batchKey re-run against a DIFFERENT manifestHash is refused
 * (the caller must bump the manifest and re-run all batches, per BRIEF_D4B §1's
 * "identical everything" rule -- partial re-derivation against a changed manifest
 * would silently break that guarantee).
 */
export function writeBatchArtifact<TResult>(
  artifactsDir: string,
  batchKey: string,
  manifestHash: string,
  results: TResult,
  writtenAt: string,
): string {
  fs.mkdirSync(artifactsDir, { recursive: true })
  const filePath = path.join(artifactsDir, `batch_${batchKey}.json`)
  if (fs.existsSync(filePath)) {
    const existing = readBatchArtifact<TResult>(filePath)
    if (existing.manifestHash !== manifestHash) {
      throw new Error(
        `refusing to overwrite batch "${batchKey}": existing artifact was written against ` +
        `manifest hash ${existing.manifestHash}, this write targets ${manifestHash}. ` +
        `A changed manifest requires a fresh run of ALL batches, not a partial overwrite.`,
      )
    }
  }
  const artifact: BatchArtifact<TResult> = { batchKey, manifestHash, writtenAt, results }
  fs.writeFileSync(filePath, JSON.stringify(artifact, null, 2) + '\n', 'utf8')
  return filePath
}

export function readBatchArtifact<TResult>(filePath: string): BatchArtifact<TResult> {
  const raw = fs.readFileSync(filePath, 'utf8')
  return JSON.parse(raw) as BatchArtifact<TResult>
}

/**
 * Assembly-time check: every batch artifact in `artifactsDir` must carry the SAME
 * manifestHash as the currently-committed manifest file. Any mismatch fails loudly
 * (returns the list of offending batchKeys) rather than silently assembling
 * inconsistent data.
 */
export function checkManifestHashConsistency(
  artifactsDir: string,
  currentManifestPath: string,
): { consistent: boolean; expectedHash: string; mismatches: Array<{ batchKey: string; foundHash: string }> } {
  const expectedHash = hashManifestFile(currentManifestPath)
  const mismatches: Array<{ batchKey: string; foundHash: string }> = []
  if (!fs.existsSync(artifactsDir)) {
    return { consistent: false, expectedHash, mismatches: [] }
  }
  for (const file of fs.readdirSync(artifactsDir)) {
    if (!file.startsWith('batch_') || !file.endsWith('.json')) continue
    const artifact = readBatchArtifact(path.join(artifactsDir, file))
    if (artifact.manifestHash !== expectedHash) {
      mismatches.push({ batchKey: artifact.batchKey, foundHash: artifact.manifestHash })
    }
  }
  return { consistent: mismatches.length === 0, expectedHash, mismatches }
}
