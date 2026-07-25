/**
 * mcp_catalog_version.ts — EL-13 (tool-catalog caching).
 * ========================================================
 * A caller polling the MCP tool catalog on every session (no way to know if it changed since
 * last fetch) is the "tool-catalog caching" gap EL-13 names. This mirrors the ALREADY-
 * ESTABLISHED `resources/vidhi/capability_version.ts` pattern (D-2 Lane V-2) — deterministic
 * content-hash version + `notifications/tools/list_changed` staleness kill — generalized from
 * "the vidhi registry" to "the whole MCP tool catalog", confirming that pattern (and SDK
 * support for `server.sendToolListChanged()`) generalizes cleanly rather than re-inventing it.
 *
 * catalog_version: a deterministic fingerprint of the 'full'-profile tool_names census carried
 * by the GENERATED manifest (`generated/mcp_surface_profiles.generated.ts`, itself built from
 * the live retrieval registry by `platform/scripts/manifest/generate_projections.ts`). Changes
 * whenever a tool is added, removed, or renamed — the authoritative "did the catalog change?"
 * signal a caller should actually compare.
 *
 * tools_changed_at: a BEST-EFFORT "when did the catalog last change" timestamp, derived from
 * the generated manifest file's filesystem mtime (checked as both the .ts source — present in
 * dev via `tsx watch`, per package.json — and the compiled .js sibling — present in the
 * production Docker image, which ships `dist/` only, see Dockerfile). Honest caveat (B.10 — no
 * fabricated values): some deploy pipelines (fresh git checkout, container image build) reset
 * file mtimes to checkout/build time rather than the true last-content-change instant, so this
 * is advisory, not a guaranteed-precise instant. Never fabricated: if neither candidate file
 * can be statted, this is `null` with an explicit `tools_changed_at_note`, never a guess.
 * `catalog_version` (the content hash) is the field a caller should trust for correctness.
 */
import { createHash } from 'node:crypto'
import { statSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { MCP_SURFACE_PROFILES } from '../generated/mcp_surface_profiles.generated.js'

/** Deterministic content hash of the full-profile tool_names census. */
function catalogContentHash(): string {
  const canonical = JSON.stringify(MCP_SURFACE_PROFILES.full.tool_names)
  return createHash('sha256').update(canonical).digest('hex').slice(0, 12)
}

export const MCP_CATALOG_TOOL_COUNT = MCP_SURFACE_PROFILES.full.total

/** The live MCP tool-catalog version, e.g. `catalog-1+t152+r3f9a1c8e2b04`. Deterministic — a
 *  pure function of the vendored generated manifest (tool_names + total). */
export const MCP_CATALOG_VERSION = `catalog-1+t${MCP_CATALOG_TOOL_COUNT}+r${catalogContentHash()}`

const GENERATED_MANIFEST_CANDIDATES = [
  'mcp_surface_profiles.generated.ts',  // dev: tsx watch runs .ts sources directly
  'mcp_surface_profiles.generated.js',  // prod: Dockerfile ships dist/ (compiled .js) only
]

function computeToolsChangedAt(): { tools_changed_at: string | null; tools_changed_at_note: string } {
  for (const filename of GENERATED_MANIFEST_CANDIDATES) {
    try {
      const path = fileURLToPath(new URL(`../generated/${filename}`, import.meta.url))
      const stat = statSync(path)
      return {
        tools_changed_at: stat.mtime.toISOString(),
        tools_changed_at_note:
          `Filesystem mtime of the generated tool-catalog manifest (${filename}) — best-effort, ` +
          'not a guaranteed-precise instant (some deploy pipelines reset file mtimes to ' +
          'checkout/build time). Compare `catalog_version` for an authoritative change signal.',
      }
    } catch {
      // Try the next candidate (dev vs. prod layout).
    }
  }
  return {
    tools_changed_at: null,
    tools_changed_at_note:
      'Could not stat the generated catalog manifest (checked both .ts and compiled .js) to ' +
      'derive a timestamp — never fabricated (B.10). Compare `catalog_version` (a content ' +
      'hash), not this field, to detect a real catalog change.',
  }
}

const TOOLS_CHANGED_AT = computeToolsChangedAt()
export const MCP_CATALOG_TOOLS_CHANGED_AT = TOOLS_CHANGED_AT.tools_changed_at
export const MCP_CATALOG_TOOLS_CHANGED_AT_NOTE = TOOLS_CHANGED_AT.tools_changed_at_note

/**
 * Compare a client-presented catalog version against the live one. Returns whether the client
 * is stale and, when a server is supplied AND the client is stale, emits a
 * `tools/list_changed` notification on that request-scoped server (mirrors
 * `notifyIfCapabilityStale` in resources/vidhi/capability_version.ts). Never throws: a
 * notification-send failure (e.g. transport not yet connected) is swallowed and reported via
 * `notified: false` rather than crashing the calling tool.
 */
export function notifyIfCatalogStale(
  clientVersion: string | undefined,
  server?: McpServer,
): { live: string; stale: boolean; notified: boolean } {
  const live = MCP_CATALOG_VERSION
  const stale = typeof clientVersion === 'string' && clientVersion.length > 0 && clientVersion !== live
  let notified = false
  if (stale && server) {
    try {
      server.sendToolListChanged()
      notified = true
    } catch {
      notified = false
    }
  }
  return { live, stale, notified }
}
