import 'server-only'
import { NextResponse } from 'next/server'
import { readdirSync, readFileSync, existsSync } from 'node:fs'
import * as path from 'path'
import * as yaml from 'js-yaml'
import { guardPerformanceRoute } from '../_guard'

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export interface ConflictArtifact {
  filename: string
  conflict_id: string
  signal_id: string
  field: string
  current_value: string
  proposed_value: string
  rationale: string
  proposed_at: string
  status: 'proposed' | 'resolved'
}

export interface ConflictsResponse {
  proposed: ConflictArtifact[]
  resolved: ConflictArtifact[]
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function readArtifactsFromDir(dir: string, status: 'proposed' | 'resolved'): ConflictArtifact[] {
  if (!existsSync(dir)) return []

  let files: string[]
  try {
    files = readdirSync(dir).filter(f => f.endsWith('.yaml'))
  } catch {
    return []
  }

  const artifacts: ConflictArtifact[] = []
  for (const filename of files) {
    try {
      const raw = readFileSync(path.join(dir, filename), 'utf-8')
      const parsed = yaml.load(raw) as Record<string, unknown>
      if (!parsed || typeof parsed !== 'object') continue

      artifacts.push({
        filename,
        conflict_id: String(parsed.conflict_id ?? ''),
        signal_id: String(parsed.signal_id ?? ''),
        field: String(parsed.field ?? ''),
        current_value: String(parsed.current_value ?? ''),
        proposed_value: String(parsed.proposed_value ?? ''),
        rationale: String(parsed.rationale ?? ''),
        proposed_at: String(parsed.proposed_at ?? ''),
        status,
      })
    } catch {
      // Skip unparseable files
    }
  }

  return artifacts
}

// ─────────────────────────────────────────────────────────────────────────────
// Route
// ─────────────────────────────────────────────────────────────────────────────

export async function GET(): Promise<NextResponse> {
  const auth = await guardPerformanceRoute()
  if (auth instanceof NextResponse) return auth

  try {
    const repoRoot = process.cwd()
    const proposedDir = path.join(repoRoot, '00_ARCHITECTURE', 'CONFLICT_PATCHES', 'PROPOSED')
    const resolvedDir = path.join(repoRoot, '00_ARCHITECTURE', 'CONFLICT_PATCHES', 'RESOLVED')

    const proposed = readArtifactsFromDir(proposedDir, 'proposed')
    const resolved = readArtifactsFromDir(resolvedDir, 'resolved')

    const response: ConflictsResponse = { proposed, resolved }
    return NextResponse.json(response)
  } catch (err) {
    console.error('[api/performance/conflicts] failed', err)
    return NextResponse.json({ error: 'conflicts_read_failed' }, { status: 500 })
  }
}
