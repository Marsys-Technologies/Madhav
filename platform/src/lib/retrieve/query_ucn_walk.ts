/**
 * MARSYS-JIS Retrieval Tool: query_ucn_walk (COV-S5)
 *
 * Extracts structural slices from UCN_v4_0.md — the Unified Chart Narrative.
 * The UCN is the L2.5 document that synthesizes all planetary and house signals
 * into a unified reading, structured by Parts I-IV with labelled sections.
 *
 * WHY THIS TOOL EXISTS:
 *   - vector_search can find UCN chunks by semantic similarity but cannot
 *     target specific Part/section structures reliably.
 *   - query_ucn_walk surfaces paragraphs mentioning a keyword, optionally
 *     restricted to a specific Part (I, II, III, or IV).
 *   - Use when the query requires accessing specific narrative sections about
 *     a planet, house, yoga, or life domain as synthesized at the holistic level.
 */

import crypto from 'crypto'
import fs from 'fs'
import path from 'path'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_ucn_walk'
const TOOL_VERSION = '1.0.0'
// Resolve relative to repo root (one level up from the platform/ Next.js app dir)
const REPO_ROOT = path.resolve(process.cwd(), '..')
const UCN_PATH = path.join(REPO_ROOT, '025_HOLISTIC_SYNTHESIS/UCN_v4_0.md')

export interface UcnWalkInput {
  /** Section keyword to find — e.g. "Mercury", "Saturn", "Lagna", "marriage" */
  seed: string
  /** Max characters to return (default 2000, max 4000) */
  max_chars?: number
  /** Which Part to search in: 'I' | 'II' | 'III' | 'IV' | 'all' (default 'all') */
  part?: 'I' | 'II' | 'III' | 'IV' | 'all'
}

/** Split UCN content into Part sections, keyed by roman numeral */
function extractPartSection(content: string, part: 'I' | 'II' | 'III' | 'IV'): string {
  // Match "## PART I —", "## PART II —", "## Part I —" etc.
  // Use word boundary after roman numeral to avoid "I" matching "II", "III"
  const partPattern = /^## (?:PART|Part) (I{1,3}V?|IV) —/gm
  const matches: Array<{ index: number; part: string }> = []
  let m: RegExpExecArray | null
  while ((m = partPattern.exec(content)) !== null) {
    // Normalize: trim and use the exact matched numeral
    matches.push({ index: m.index, part: m[1] })
  }

  if (matches.length === 0) return content

  // Find ALL matches for the target part (there may be a "PART I" header AND a "Part I" section)
  // Find the first occurrence of the target part, then the next section with a DIFFERENT part
  const targetMatches = matches.filter(match => match.part === part)
  if (targetMatches.length === 0) return content

  const firstTargetIdx = matches.findIndex(match => match.part === part)
  // Find the next match that has a DIFFERENT part identifier
  let endIdx = content.length
  for (let i = firstTargetIdx + 1; i < matches.length; i++) {
    if (matches[i].part !== part) {
      endIdx = matches[i].index
      break
    }
  }

  const start = matches[firstTargetIdx].index
  return content.slice(start, endIdx)
}

/** Split content into paragraphs (separated by one or more blank lines) */
function toParagraphs(content: string): string[] {
  return content.split(/\n{2,}/).map(p => p.trim()).filter(p => p.length > 0)
}

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()

  const p: UcnWalkInput = {
    seed: (params?.seed as string | undefined) ?? plan.query_text,
    max_chars: Math.min((params?.max_chars as number | undefined) ?? 2000, 4000),
    part: (params?.part as UcnWalkInput['part']) ?? 'all',
  }

  const rawContent = fs.readFileSync(UCN_PATH, 'utf-8')
  const searchContent = p.part && p.part !== 'all'
    ? extractPartSection(rawContent, p.part)
    : rawContent

  const paragraphs = toParagraphs(searchContent)
  const seedLower = p.seed.toLowerCase()

  // Find matching paragraphs (mention seed keyword)
  const matchingIndices: number[] = []
  paragraphs.forEach((para, idx) => {
    if (para.toLowerCase().includes(seedLower)) {
      matchingIndices.push(idx)
    }
  })

  const results: ToolBundleResult[] = []

  if (matchingIndices.length === 0) {
    // No match — return empty results
  } else {
    // Take first match + next 2 paragraphs for context, up to max_chars
    let collected = ''
    const firstIdx = matchingIndices[0]
    const contextParas = paragraphs.slice(firstIdx, firstIdx + 3)
    for (const para of contextParas) {
      if (collected.length + para.length + 2 <= p.max_chars!) {
        collected += (collected ? '\n\n' : '') + para
      } else {
        const remaining = p.max_chars! - collected.length - 2
        if (remaining > 0) {
          collected += (collected ? '\n\n' : '') + para.slice(0, remaining)
        }
        break
      }
    }

    if (collected.length > 0) {
      results.push({
        content: collected,
        source_canonical_id: 'UCN',
        source_version: '4.1',
        confidence: 1.0,
        significance: 0.9,
        signal_id: `ucn_excerpt_1`,
      })
    }

    // Add additional non-overlapping matches (up to 2 more) if we have room
    let excerptCount = 1
    for (const idx of matchingIndices.slice(1)) {
      if (excerptCount >= 3) break
      // Skip if overlapping with previous
      if (idx < firstIdx + 3) continue
      const para = paragraphs.slice(idx, idx + 2).join('\n\n')
      if (para.length > 0) {
        results.push({
          content: para.slice(0, 1500),
          source_canonical_id: 'UCN',
          source_version: '4.1',
          confidence: 1.0,
          significance: 0.8,
          signal_id: `ucn_excerpt_${excerptCount + 1}`,
        })
        excerptCount++
      }
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
    invocation_params: { seed: p.seed, max_chars: p.max_chars, part: p.part },
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
    'Extracts structural slices from the UCN (Unified Chart Narrative) — the L2.5 document that ' +
    'synthesizes all planetary and house signals into a unified reading. Use when the query requires ' +
    'accessing specific narrative sections about a planet, house, yoga, or life domain as synthesized ' +
    'at the holistic level.',
  retrieve,
}
