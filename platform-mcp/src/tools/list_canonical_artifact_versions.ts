/**
 * list_canonical_artifact_versions.ts — MCP Tier 4 tool: list all canonical artifact versions.
 *
 * What it does: Reads 00_ARCHITECTURE/CAPABILITY_MANIFEST.json from disk and returns
 * a structured list of every canonical artifact with its canonical_id, version, status,
 * and path. This is a filesystem read — no platform HTTP call is made.
 *
 * Path resolution follows the same pattern as read_asset.ts:
 *   1. MARSYS_REPO_ROOT env var (explicit override — works in dev and prod if set).
 *   2. __dirname-relative: dist/tools/ → up 4 levels → project root.
 *
 * Output shape: { ok: true, artifact_count: number, artifacts: ArtifactEntry[] }
 * Each ArtifactEntry: { canonical_id, version, status, path } — missing fields → null.
 *
 * Session: TR-P9-S2
 */

import * as path from 'path'
import * as fs from 'fs'
import { fileURLToPath } from 'url'
import { dirname } from 'path'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

// ── ESM __dirname shim ────────────────────────────────────────────────────────

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// ── Manifest path resolution ──────────────────────────────────────────────────

function resolveManifestPath(): string {
  if (process.env['MARSYS_REPO_ROOT']) {
    return path.join(process.env['MARSYS_REPO_ROOT'], '00_ARCHITECTURE', 'CAPABILITY_MANIFEST.json')
  }
  // __dirname = .../dist/tools (compiled output)
  // go up: dist/tools → dist → platform-mcp → repo root
  return path.join(__dirname, '../../../../00_ARCHITECTURE/CAPABILITY_MANIFEST.json')
}

// ── Artifact entry type ───────────────────────────────────────────────────────

interface ArtifactEntry {
  canonical_id: string | null
  version: string | null
  status: string | null
  path: string | null
}

// ── Normalize one manifest entry → ArtifactEntry ─────────────────────────────

function normalizeEntry(entry: unknown): ArtifactEntry | null {
  if (!entry || typeof entry !== 'object') return null
  const e = entry as Record<string, unknown>
  return {
    canonical_id: (e['canonical_id'] as string | undefined) ?? null,
    version: (e['version'] as string | undefined) ?? null,
    status: (e['status'] as string | undefined) ?? null,
    path: (e['path'] as string | undefined) ?? (e['canonical_path'] as string | undefined) ?? null,
  }
}

// ── Extract artifact list from manifest (array or object shape) ───────────────

function extractArtifacts(manifest: unknown): ArtifactEntry[] {
  const artifacts: ArtifactEntry[] = []

  if (Array.isArray(manifest)) {
    // Manifest is an array of entries
    for (const entry of manifest) {
      const normalized = normalizeEntry(entry)
      if (normalized) artifacts.push(normalized)
    }
    return artifacts
  }

  if (manifest && typeof manifest === 'object') {
    const obj = manifest as Record<string, unknown>

    // Try common wrapper keys: "artifacts", "canonical_artifacts", "entries"
    for (const key of ['artifacts', 'canonical_artifacts', 'entries']) {
      if (Array.isArray(obj[key])) {
        for (const entry of obj[key] as unknown[]) {
          const normalized = normalizeEntry(entry)
          if (normalized) artifacts.push(normalized)
        }
        if (artifacts.length > 0) return artifacts
      }
    }

    // Fallback: treat object values as entries (each value is an artifact entry)
    for (const [, value] of Object.entries(obj)) {
      if (value && typeof value === 'object' && !Array.isArray(value)) {
        const normalized = normalizeEntry(value)
        if (normalized) artifacts.push(normalized)
      }
    }
  }

  return artifacts
}

// ── Tool description ──────────────────────────────────────────────────────────

export const LIST_CANONICAL_ARTIFACT_VERSIONS_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Reads 00_ARCHITECTURE/CAPABILITY_MANIFEST.json from disk and returns ' +
    'a structured list of all canonical artifacts with canonical_id, version, status, and path. ' +
    'No platform HTTP call — pure filesystem read. Useful for introspecting the artifact registry.',
  whenToPrefer:
    'Use when you need to enumerate all canonical artifacts and their current versions or statuses. ' +
    'Prefer read_asset when you need the full text of a specific artifact. ' +
    'Prefer list_assets for the curated subset of LLM-readable assets.',
})

// ── Tool registration ─────────────────────────────────────────────────────────

export function registerListCanonicalArtifactVersions(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'list_canonical_artifact_versions',
    LIST_CANONICAL_ARTIFACT_VERSIONS_DESCRIPTION,
    {
      // No required input parameters — returns all artifacts from manifest
      filter_status: z.string().optional().describe(
        'Optional status filter (e.g. "CURRENT", "SUPERSEDED", "LIVING"). ' +
        'Case-insensitive. When provided, only artifacts with matching status are returned.'
      ),
    },
    async ({ filter_status }) => {
      void getPrincipal() // auth already validated; reserved for future tier checks

      const manifestPath = resolveManifestPath()

      let rawJson: string
      try {
        rawJson = fs.readFileSync(manifestPath, 'utf-8')
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        console.error(`[list_canonical_artifact_versions] Failed to read ${manifestPath}:`, msg)
        return errorResult({
          ok: false,
          error: {
            class: 'internal',
            message: `Failed to read CAPABILITY_MANIFEST.json: ${msg}`,
            remediation:
              `Verify MARSYS_REPO_ROOT is set (current: ${process.env['MARSYS_REPO_ROOT'] ?? 'unset'}) ` +
              `or that 00_ARCHITECTURE/CAPABILITY_MANIFEST.json exists at ${manifestPath}`,
          },
        })
      }

      let manifest: unknown
      try {
        manifest = JSON.parse(rawJson)
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return errorResult({
          ok: false,
          error: {
            class: 'internal',
            message: `CAPABILITY_MANIFEST.json is not valid JSON: ${msg}`,
            remediation: 'Verify the manifest file is valid JSON at ' + manifestPath,
          },
        })
      }

      let artifacts = extractArtifacts(manifest)

      // Apply optional status filter
      if (filter_status) {
        const filterUpper = filter_status.toUpperCase()
        artifacts = artifacts.filter(
          a => a.status !== null && a.status.toUpperCase() === filterUpper
        )
      }

      return okResult({
        ok: true,
        artifact_count: artifacts.length,
        artifacts,
        manifest_path_used: manifestPath,
      })
    }
  )
}
