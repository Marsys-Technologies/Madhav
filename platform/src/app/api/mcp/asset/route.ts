/**
 * /api/mcp/asset — Canonical artifact read endpoint for read_asset MCP tool.
 *
 * POST — Read a canonical artifact by canonical_id and return its markdown
 * content (optionally filtered to a section).
 *
 * Auth model (two-layer, same as /api/mcp/execute):
 *   Layer 1: X-MCP-Internal-Token — service-to-service secret.
 *   Layer 2: X-MCP-User, X-MCP-Audience-Tier, X-MCP-Key-Id — resolved principal.
 *
 * Security: canonical_id is validated against a SAFE_ASSET_MAP — never used
 * to construct a file path directly. Path traversal attacks are impossible
 * because the map is hardcoded.
 *
 * Access control: Per D12 (full transparency), all authenticated callers
 * receive full file content. Audience-tier-based section redaction is reserved
 * for Phase 2.
 *
 * Supported canonical_ids:
 *   FORENSIC, LEL, MACRO_PLAN, PROJECT_ARCHITECTURE
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { readFile } from 'fs/promises'
import { join } from 'path'
import { buildEnvelope, buildErrorEnvelope, buildEpistemicsBlock } from '@/lib/mcp/epistemics'
import { validateServiceToken } from '@/lib/mcp/service_token'

// ── Safe canonical_id → relative file path map ───────────────────────────────
// Paths are relative to the repository root (the parent of platform/).
// The MadhavMCP worktree root is two levels up from this file
// (platform/src/app/api/mcp/asset/ → ../../../../../.. → project root).
// We use process.cwd() which in Next.js is the platform/ directory,
// so we go one level up to reach the repo root.

// WS-0 (2026-06-04): removed MSR/UCN/CDLM/CGM/RM — superseded by Brahma L2 Bodha layer
const SAFE_ASSET_MAP: Record<string, string> = {
  // v8.0 markdown deleted from 01_FACTS_LAYER/ in PR #187; cold benchmark at archive path below.
  // Live FORENSIC source is chart_facts DB table via forensic_render.ts — not served as a file.
  FORENSIC:             '99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md',
  LEL:                  '01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md',
  MACRO_PLAN:           '00_ARCHITECTURE/MACRO_PLAN_v2_0.md',
  PROJECT_ARCHITECTURE: '00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md',
}

// MARSYS_REPO_ROOT is baked into the container image by platform/Dockerfile
// (ENV MARSYS_REPO_ROOT=/app in the runner stage, which also copies 01_FACTS_LAYER/
// and 025_HOLISTIC_SYNTHESIS/ into /app). Fallback to cwd/.. for local dev where
// process.cwd() is the platform/ directory and the repo root is one level up.
//
// NOTE: intentionally a lazy getter (function) rather than a module-level constant.
// A module-level `join(process.cwd(), '..')` causes Turbopack to create a
// DirAssetReference for the parent directory, which contains python-sidecar/venv/
// with a broken symlink (→ python3.13) that triggers a fatal Turbopack panic.
// Deferring to call-time resolves at runtime without any Turbopack static analysis.
function getRepoRoot(): string {
  return process.env.MARSYS_REPO_ROOT ?? join(process.cwd(), '..')
}

// ── Section filter ────────────────────────────────────────────────────────────

/**
 * Filter markdown content to a specific section.
 * Matches headings containing the section string (case-insensitive).
 * Returns the section content from the matched heading until the next heading
 * of the same or higher level.
 * Returns the full content if no matching section is found.
 */
function filterToSection(content: string, section: string): string {
  const lines = content.split('\n')
  const sectionLower = section.toLowerCase()

  // Find the heading line that best matches the section filter
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

  if (startLine === -1) {
    // No matching section found — return full content
    return content
  }

  // Find the end: next heading of same or higher level
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

// ── POST handler ─────────────────────────────────────────────────────────────

interface AssetRequestBody {
  canonical_id?: string
  section?: string
}

export async function POST(request: Request) {
  // Layer 1: service-to-service auth
  if (!validateServiceToken(request)) {
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'auth',
        message: 'Invalid service token',
        remediation: 'MCP server must pass MCP_INTERNAL_TOKEN header',
      }),
      { status: 401 }
    )
  }

  // Layer 2: resolved principal headers
  const userUid = request.headers.get('x-mcp-user')
  const audienceTierHeader = request.headers.get('x-mcp-audience-tier') as
    | 'client'
    | 'super_admin'
    | null
  const keyId = request.headers.get('x-mcp-key-id')

  if (!userUid || !audienceTierHeader || !keyId) {
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'auth',
        message: 'Missing principal headers (X-MCP-User, X-MCP-Audience-Tier, X-MCP-Key-Id)',
      }),
      { status: 401 }
    )
  }

  const audienceTier: 'client' | 'super_admin' =
    audienceTierHeader === 'super_admin' ? 'super_admin' : 'client'

  // Parse request body
  let body: AssetRequestBody
  try {
    body = await request.json()
  } catch {
    return NextResponse.json(
      buildErrorEnvelope({ error_class: 'validation', message: 'Invalid JSON body' }),
      { status: 400 }
    )
  }

  const canonicalId = body.canonical_id?.trim().toUpperCase()
  if (!canonicalId) {
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'validation',
        message: 'canonical_id is required',
        remediation: `Supported IDs: ${Object.keys(SAFE_ASSET_MAP).join(', ')}`,
      }),
      { status: 400 }
    )
  }

  // Validate canonical_id against the safe map (path traversal prevention)
  const relativePath = SAFE_ASSET_MAP[canonicalId]
  if (!relativePath) {
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'validation',
        message: `Unknown canonical_id: ${canonicalId}`,
        remediation: `Supported IDs: ${Object.keys(SAFE_ASSET_MAP).join(', ')}`,
      }),
      { status: 400 }
    )
  }

  // Resolve absolute path (repo root + relative)
  const absolutePath = join(getRepoRoot(), relativePath)

  // Read the file
  let content: string
  try {
    content = await readFile(absolutePath, 'utf-8')
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    console.error(`[mcp:asset] Failed to read ${absolutePath}`, msg)
    return NextResponse.json(
      buildErrorEnvelope({
        error_class: 'internal',
        message: `Failed to read artifact ${canonicalId}: ${msg}`,
        remediation: 'Verify the artifact exists at the canonical path',
      }),
      { status: 500 }
    )
  }

  // Apply section filter if provided
  const section = body.section?.trim()
  const filteredContent = section ? filterToSection(content, section) : content

  // Compute word count
  const wordCount = filteredContent.split(/\s+/).filter(Boolean).length

  const traceId = crypto.randomUUID()

  return NextResponse.json(
    buildEnvelope({
      trace_id: traceId,
      audience_tier: audienceTier,
      epistemics: buildEpistemicsBlock({ surgical: true, confidence_band: 'high' }),
      result: {
        canonical_id: canonicalId,
        content: filteredContent,
        word_count: wordCount,
        path: relativePath,
        section_filter: section ?? null,
      },
      citations: [],
      plan: null,
      predictions_logged: [],
      synthesis_audit: null,
      suggested_followups: [],
      warnings: [],
    })
  )
}
