/**
 * read_asset.ts — MCP Tier 4 tool: read a canonical MARSYS-JIS artifact.
 *
 * Returns the raw markdown of a canonical artifact (MSR, UCN, CDLM, CGM, RM,
 * FORENSIC, LEL, MACRO_PLAN, PROJECT_ARCHITECTURE) by canonical_id, with an
 * optional section filter.
 *
 * This is a Tier 4 tool per MCP_BRIEF §4.1. It is surgical (no planner, no
 * B.11 floor enforcement, no synthesis). Use when you need the full text of
 * a synthesis layer document — e.g., the full CGM for a graph overview, or
 * the full FORENSIC for a birth-data audit. For targeted fact lookups within
 * a document, prefer query_signals or query_chart_facts.
 *
 * Access control: Per decision D12 (full transparency), all authenticated
 * callers receive full file content.
 *
 * Path resolution (C9 fix — PROD_ENV: MARSYS_REPO_ROOT not set in Cloud Run):
 *   1. MARSYS_REPO_ROOT env var (set explicitly in dev or via Cloud Run env var).
 *   2. __dirname-relative: three levels up from dist/tools/ → project root.
 *      In the sidecar container (/app/dist/tools/) this resolves to /app/../..
 *      once files are copied by the Dockerfile.
 *   Fallback chain ensures local dev works with MARSYS_REPO_ROOT and prod works
 *   without it, as long as the Dockerfile copies the canonical files.
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { readFile } from 'fs/promises'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

// ── ESM __dirname shim ────────────────────────────────────────────────────────

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// ── Repository root resolution ────────────────────────────────────────────────
// Priority:
//   1. MARSYS_REPO_ROOT env var (explicit override — works in dev and prod if set).
//   2. __dirname-relative: dist/tools/ → up 3 levels → project root.
//      In the container: /app/dist/tools/ → /app/ (after canonical files are
//      copied by COPY docs/ ./docs/ in Dockerfile, they land at /app/docs/).
//      Adjust depth here if the bundle structure changes.

function resolveRepoRoot(): string {
  if (process.env['MARSYS_REPO_ROOT']) {
    return process.env['MARSYS_REPO_ROOT']
  }
  // __dirname = .../dist/tools (compiled output)
  // go up: dist/tools → dist → app-root → repo-root
  return join(__dirname, '..', '..', '..')
}

// ── Supported canonical IDs ──────────────────────────────────────────────────

export const KNOWN_CANONICAL_IDS = [
  'MSR',
  'UCN',
  'CDLM',
  'CGM',
  'RM',
  'FORENSIC',
  'LEL',
  'MACRO_PLAN',
  'PROJECT_ARCHITECTURE',
  'CURRENT_STATE',
] as const

export type KnownCanonicalId = typeof KNOWN_CANONICAL_IDS[number]

// Safe map: canonical_id → repo-relative path. Never constructed from user input.
export const SAFE_ASSET_MAP: Record<KnownCanonicalId, string> = {
  MSR:                  '025_HOLISTIC_SYNTHESIS/MSR_v3_0.md',
  UCN:                  '025_HOLISTIC_SYNTHESIS/UCN_v4_0.md',
  CDLM:                 '025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md',
  CGM:                  '025_HOLISTIC_SYNTHESIS/CGM_v9_0.md',
  RM:                   '025_HOLISTIC_SYNTHESIS/RM_v2_0.md',
  FORENSIC:             '01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md',
  LEL:                  '01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md',
  MACRO_PLAN:           '00_ARCHITECTURE/MACRO_PLAN_v2_0.md',
  PROJECT_ARCHITECTURE: '00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md',
  CURRENT_STATE:        '00_ARCHITECTURE/CURRENT_STATE_v1_0.md',
}

export const READ_ASSET_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Returns the raw markdown of a canonical MARSYS-JIS artifact by its canonical_id ' +
    '(MSR, UCN, CDLM, CGM, RM, FORENSIC, LEL, MACRO_PLAN, PROJECT_ARCHITECTURE, CURRENT_STATE), with optional section filter.',
  enumSource: KNOWN_CANONICAL_IDS,
  whenToPrefer:
    'Use when you need the full text of a synthesis layer document ' +
    '(e.g., full CGM for a graph overview, full FORENSIC for a birth-data audit). ' +
    'Prefer query_signals or query_chart_facts for targeted fact lookups within documents. ' +
    'Prefer holistic_bundle for any question requiring synthesis across multiple documents.',
})

// ── Section filter ────────────────────────────────────────────────────────────

function filterToSection(content: string, section: string): string {
  const lines = content.split('\n')
  const sectionLower = section.toLowerCase()
  let startLine = -1
  let headingLevel = 0

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const headingMatch = line.match(/^(#{1,6})\s+(.+)/)
    if (headingMatch && headingMatch[2].toLowerCase().includes(sectionLower)) {
      startLine = i
      headingLevel = headingMatch[1].length
      break
    }
  }

  if (startLine === -1) return content

  let endLine = lines.length
  for (let i = startLine + 1; i < lines.length; i++) {
    const line = lines[i]
    const headingMatch = line.match(/^(#{1,6})\s+/)
    if (headingMatch && headingMatch[1].length <= headingLevel) {
      endLine = i
      break
    }
  }

  return lines.slice(startLine, endLine).join('\n')
}

// ── Tool registration ─────────────────────────────────────────────────────────

export function registerReadAsset(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'read_asset',

    READ_ASSET_DESCRIPTION,

    // ── Input schema ──────────────────────────────────────────────────────────
    {
      canonical_id: z
        .string()
        .describe(
          `One of: ${KNOWN_CANONICAL_IDS.join(', ')}. Case-insensitive.`
        ),
      section: z
        .string()
        .optional()
        .describe(
          'Optional section heading filter (e.g., "§A" or "Planetary Positions"). ' +
          'Returns only the matched section and its content. ' +
          'Omit for the full document.'
        ),
    },

    // ── Handler ────────────────────────────────────────────────────────────────
    async ({ canonical_id, section }) => {
      void getPrincipal() // auth already validated by caller; reserved for future tier checks

      const normalised = canonical_id.trim().toUpperCase() as KnownCanonicalId
      const relativePath = SAFE_ASSET_MAP[normalised]

      if (!relativePath) {
        return errorResult({
          ok: false,
          error: {
            class: 'validation',
            message: `Unknown canonical_id: ${canonical_id}`,
            remediation: `Supported IDs: ${KNOWN_CANONICAL_IDS.join(', ')}`,
          },
        })
      }

      const repoRoot = resolveRepoRoot()
      const absolutePath = join(repoRoot, relativePath)

      let content: string
      try {
        content = await readFile(absolutePath, 'utf-8')
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        console.error(`[read_asset] Failed to read ${absolutePath}:`, msg)
        return errorResult({
          ok: false,
          error: {
            class: 'internal',
            message: `Failed to read artifact ${normalised}: ${msg}`,
            remediation:
              `Verify MARSYS_REPO_ROOT is set (current: ${process.env['MARSYS_REPO_ROOT'] ?? 'unset'}) ` +
              `or that canonical files are present at ${absolutePath}`,
          },
        })
      }

      const filteredContent = section ? filterToSection(content, section) : content
      const wordCount = filteredContent.split(/\s+/).filter(Boolean).length
      const traceId = crypto.randomUUID()

      return okResult({
        ok: true,
        trace_id: traceId,
        epistemics: { surgical: true, confidence_band: 'high' },
        result: {
          canonical_id: normalised,
          content: filteredContent,
          word_count: wordCount,
          path: relativePath,
          section_filter: section ?? null,
          repo_root_used: repoRoot,
        },
      })
    }
  )
}
