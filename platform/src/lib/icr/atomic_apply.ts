// atomic_apply.ts — apply a propose-patch artifact atomically
// ICR-S5 (2026-05-21): atomic apply infrastructure for PROPOSED/ → RESOLVED/ pipeline

import { readFileSync, writeFileSync, mkdirSync, renameSync, existsSync, unlinkSync } from 'node:fs'
import * as path from 'node:path'
import type { ProposePatch } from './patch_emitter'
import * as yaml from 'js-yaml'

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export type ApplyResult =
  | { ok: true; resolved_path: string; backup_path: string }
  | { ok: false; error: string }

// ─────────────────────────────────────────────────────────────────────────────
// Target path resolution
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Resolve the synthesis file path for a given signal_id.
 * Supports MSR.* and UCN.* prefixes.
 */
export function resolveTargetPath(signalId: string, repoRoot: string): string | null {
  if (signalId.startsWith('MSR.')) {
    return path.join(repoRoot, '025_HOLISTIC_SYNTHESIS', 'MSR_v5_0.md')
  }
  if (signalId.startsWith('UCN.')) {
    return path.join(repoRoot, '025_HOLISTIC_SYNTHESIS', 'UCN_v4_0.md')
  }
  return null
}

// ─────────────────────────────────────────────────────────────────────────────
// Main atomic apply
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Atomically apply a propose-patch artifact.
 *
 * Steps:
 * 1. Read and parse the PROPOSED/ YAML
 * 2. Resolve the target synthesis file from signal_id
 * 3. Read target file and validate current_value exists
 * 4. Replace current_value with proposed_value
 * 5. Write updated file (with backup)
 * 6. Move PROPOSED/ artifact to RESOLVED/
 *
 * On any failure after step 5, the backup is restored.
 * On success, the backup is removed.
 *
 * @param proposedPath - absolute path to the PROPOSED/ YAML file
 * @param repoRoot     - absolute path to the repo root
 * @param dryRun       - if true, validate but do not write anything
 */
export function atomicApply(
  proposedPath: string,
  repoRoot: string,
  dryRun = false,
): ApplyResult {
  // 1. Read and parse patch artifact
  let patch: ProposePatch
  try {
    const raw = readFileSync(proposedPath, 'utf-8')
    patch = yaml.load(raw) as ProposePatch
  } catch (e) {
    return { ok: false, error: `Failed to read proposed artifact: ${e}` }
  }

  if (!patch || !patch.signal_id || !patch.current_value || !patch.proposed_value) {
    return { ok: false, error: 'Proposed artifact is missing required fields (signal_id, current_value, proposed_value)' }
  }

  // 2. Resolve target file
  const targetPath = resolveTargetPath(patch.signal_id, repoRoot)
  if (!targetPath) {
    return { ok: false, error: `Cannot resolve target file for signal_id: ${patch.signal_id}` }
  }

  // 3. Read target file
  let content: string
  try {
    content = readFileSync(targetPath, 'utf-8')
  } catch (e) {
    return { ok: false, error: `Failed to read target file ${targetPath}: ${e}` }
  }

  // 4. Validate current_value exists
  if (!content.includes(patch.current_value)) {
    return {
      ok: false,
      error: `current_value not found in ${targetPath}. The file may have already been patched or drifted.`,
    }
  }

  // Compute paths for dry-run return
  const resolvedDir = path.join(repoRoot, '00_ARCHITECTURE', 'CONFLICT_PATCHES', 'RESOLVED')
  const resolvedName = path.basename(proposedPath).replace('_proposed.yaml', '_resolved.yaml')
  const resolvedPath = path.join(resolvedDir, resolvedName)
  const backupPath = targetPath + '.icr_bak'

  if (dryRun) {
    // Dry run: validate only, no writes
    return { ok: true, resolved_path: resolvedPath, backup_path: backupPath }
  }

  // 5. Apply patch with backup
  const updated = content.replace(patch.current_value, patch.proposed_value)

  try {
    writeFileSync(backupPath, content, 'utf-8') // backup original
    writeFileSync(targetPath, updated, 'utf-8') // apply patch
  } catch (e) {
    // Attempt restore from memory (backup may not have been written yet)
    try { writeFileSync(targetPath, content, 'utf-8') } catch { /* best-effort */ }
    return { ok: false, error: `Write failed: ${e}` }
  }

  // 6. Move artifact PROPOSED/ → RESOLVED/
  try {
    mkdirSync(resolvedDir, { recursive: true })
    renameSync(proposedPath, resolvedPath)

    // Remove backup on success
    if (existsSync(backupPath)) unlinkSync(backupPath)

    return { ok: true, resolved_path: resolvedPath, backup_path: backupPath }
  } catch (e) {
    // Roll back file write
    try { writeFileSync(targetPath, content, 'utf-8') } catch { /* best-effort */ }
    // Remove backup if it exists
    try { if (existsSync(backupPath)) unlinkSync(backupPath) } catch { /* best-effort */ }
    return { ok: false, error: `RESOLVED/ move failed: ${e}` }
  }
}
