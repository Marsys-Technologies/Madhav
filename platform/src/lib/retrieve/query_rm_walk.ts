/**
 * MARSYS-JIS Retrieval Tool: query_rm_walk (COV-S5)
 *
 * Retrieves specific resonance entries from RM_v2_0.md — the Resonance Map.
 * The RM records structural amplification patterns between planetary configurations,
 * with entries labelled RM.1, RM.2, ... RM.35.
 *
 * WHY THIS TOOL EXISTS:
 *   - The RM has 35 named entries with specific IDs (RM.01–RM.35).
 *   - vector_search cannot reliably retrieve a specific RM entry by its exact ID.
 *   - query_rm_walk provides direct extraction by RM entry ID or keyword search.
 *   - Use when the query requires understanding how multiple signals reinforce
 *     or cancel each other at the synthesis level.
 */

import crypto from 'crypto'
import fs from 'fs'
import path from 'path'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_rm_walk'
const TOOL_VERSION = '1.0.0'
// Resolve relative to repo root (one level up from the platform/ Next.js app dir)
const REPO_ROOT = path.resolve(process.cwd(), '..')
const RM_PATH = path.join(REPO_ROOT, '025_HOLISTIC_SYNTHESIS/RM_v2_0.md')

export interface RmWalkInput {
  /** RM entry ID, e.g. "RM.1", "RM.15", or a theme keyword like "Mercury", "9H" */
  rm_seed: string
  /** Max chars (default 2000) */
  max_chars?: number
}

/** Split RM content into sections keyed by RM.NN heading */
function splitRmSections(content: string): Array<{ id: string; content: string }> {
  // Match headings like: "### RM.01 — Mercury..." or "### RM.1 — ..."
  const headingPattern = /^### (RM\.\d+) —/gm
  const matches: Array<{ index: number; id: string }> = []
  let m: RegExpExecArray | null
  while ((m = headingPattern.exec(content)) !== null) {
    matches.push({ index: m.index, id: m[1] })
  }

  const sections: Array<{ id: string; content: string }> = []
  for (let i = 0; i < matches.length; i++) {
    const start = matches[i].index
    const end = i + 1 < matches.length ? matches[i + 1].index : content.length
    sections.push({
      id: matches[i].id,
      content: content.slice(start, end).trim(),
    })
  }
  return sections
}

/** Normalize RM ID: "RM.1" → "RM.01", "RM.15" → "RM.15" */
function normalizeRmId(input: string): string {
  const match = /^RM\.(\d+)$/i.exec(input.trim())
  if (!match) return input
  const num = parseInt(match[1], 10)
  return `RM.${String(num).padStart(2, '0')}`
}

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()

  const p: RmWalkInput = {
    rm_seed: (params?.rm_seed as string | undefined) ?? plan.query_text,
    max_chars: Math.min((params?.max_chars as number | undefined) ?? 2000, 4000),
  }

  const rawContent = fs.readFileSync(RM_PATH, 'utf-8')
  const sections = splitRmSections(rawContent)

  const results: ToolBundleResult[] = []

  // Check if rm_seed looks like an RM entry ID (e.g., "RM.1", "RM.15", "RM.01")
  const isRmId = /^RM\.\d+$/i.test(p.rm_seed.trim())

  if (isRmId) {
    const normalizedId = normalizeRmId(p.rm_seed)
    const section = sections.find(s => s.id === normalizedId)
    if (section) {
      results.push({
        content: section.content.slice(0, p.max_chars),
        source_canonical_id: 'RM',
        source_version: '2.2',
        confidence: 1.0,
        significance: 1.0,
        signal_id: section.id,
      })
    }
  } else {
    // Keyword search across all sections
    const seedLower = p.rm_seed.toLowerCase()
    const matching = sections.filter(s => s.content.toLowerCase().includes(seedLower))

    let excerptCount = 0
    for (const section of matching) {
      if (excerptCount >= 3) break
      results.push({
        content: section.content.slice(0, Math.floor(p.max_chars! / Math.min(matching.length, 3))),
        source_canonical_id: 'RM',
        source_version: '2.2',
        confidence: 1.0,
        significance: 0.85,
        signal_id: section.id,
      })
      excerptCount++
    }
  }

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map(r => r.content.slice(0, 80)).sort()))
      .digest('hex')

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: { rm_seed: p.rm_seed, max_chars: p.max_chars },
    results,
    served_from_cache: false,
    latency_ms: Date.now() - start,
    result_hash,
    schema_version: '1.0',
  }

  return bundle
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Retrieves resonance entries from the RM (Resonance Map) — the L2.5 document recording ' +
    'structural amplification patterns between planetary configurations. Use when the query requires ' +
    'understanding how multiple signals reinforce or cancel each other at the synthesis level.',
  retrieve,
}
