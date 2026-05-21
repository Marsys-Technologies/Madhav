import { readFileSync, readdirSync, existsSync } from 'fs'
import * as path from 'path'
import type { ConflictRecord } from '../icr/types'

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export type ConflictStatus = 'PROPOSED' | 'RESOLVED' | 'OPEN'

export interface ConflictSummaryEntry extends ConflictRecord {
  status: ConflictStatus
}

export interface ConflictSummaryReport {
  entries: ConflictSummaryEntry[]
  total: number
  resolved_count: number
  proposed_count: number
  open_count: number
}

// ─────────────────────────────────────────────────────────────────────────────
// Filename → conflict_id parser
// Supports both "DIS.013_..." and "DIS.AUTO.214_..." patterns.
// ─────────────────────────────────────────────────────────────────────────────

function parseConflictIdFromFilename(filename: string): string | null {
  // Strip extension
  const base = filename.replace(/\.[^.]+$/, '')
  // Filenames look like: DIS.013_MSR_377_resolved.yaml → base: DIS.013_MSR_377_resolved
  // or DIS.AUTO.214_... → base: DIS.AUTO.214_...
  // The conflict_id is the leading dot-delimited token(s) before the first underscore.
  const underscoreIdx = base.indexOf('_')
  if (underscoreIdx === -1) return base || null
  return base.slice(0, underscoreIdx) || null
}

function collectIds(dir: string): Set<string> {
  const ids = new Set<string>()
  if (!existsSync(dir)) return ids
  let files: string[]
  try {
    files = readdirSync(dir)
  } catch {
    return ids
  }
  for (const f of files) {
    if (!f.endsWith('.yaml')) continue
    const id = parseConflictIdFromFilename(f)
    if (id) ids.add(id)
  }
  return ids
}

// ─────────────────────────────────────────────────────────────────────────────
// Main export
// ─────────────────────────────────────────────────────────────────────────────

export function getConflictSummary(repoRoot: string): ConflictSummaryReport {
  const outputPath = path.join(
    repoRoot,
    '06_LEARNING_LAYER/ICR_DETECTOR_OUTPUT_v1_0.json'
  )

  if (!existsSync(outputPath)) {
    return { entries: [], total: 0, resolved_count: 0, proposed_count: 0, open_count: 0 }
  }

  let raw: { conflicts?: ConflictRecord[] }
  try {
    raw = JSON.parse(readFileSync(outputPath, 'utf-8')) as {
      conflicts?: ConflictRecord[]
    }
  } catch {
    return { entries: [], total: 0, resolved_count: 0, proposed_count: 0, open_count: 0 }
  }

  const conflicts: ConflictRecord[] = Array.isArray(raw.conflicts)
    ? raw.conflicts
    : Array.isArray(raw)
    ? (raw as unknown as ConflictRecord[])
    : []

  const proposedIds = collectIds(path.join(repoRoot, 'PROPOSED'))
  const resolvedIds = collectIds(path.join(repoRoot, 'RESOLVED'))

  let resolved_count = 0
  let proposed_count = 0
  let open_count = 0

  const entries: ConflictSummaryEntry[] = conflicts.map(c => {
    let status: ConflictStatus
    if (resolvedIds.has(c.conflict_id)) {
      status = 'RESOLVED'
      resolved_count++
    } else if (proposedIds.has(c.conflict_id)) {
      status = 'PROPOSED'
      proposed_count++
    } else {
      status = 'OPEN'
      open_count++
    }
    return { ...c, status }
  })

  return {
    entries,
    total: entries.length,
    resolved_count,
    proposed_count,
    open_count,
  }
}
