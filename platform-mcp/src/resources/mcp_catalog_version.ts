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
 *
 * ────────────────────────────────────────────────────────────────────────────────────────
 * SAMĀPTI B-MCP-CATALOG-GAP (DVA Ruling 25) — the tool_count false-green, and its fix.
 * ────────────────────────────────────────────────────────────────────────────────────────
 * Until 2026-07-30 this module exported `MCP_CATALOG_TOOL_COUNT = MCP_SURFACE_PROFILES
 * .full.total` and `register_server_info.ts` served it as `mcp_server_info.tool_count` —
 * i.e. as "how many tools does this server serve". It was not that number and never had
 * been. The generated manifest enumerates RETRIEVAL-REGISTRY capability faces (built from
 * `getCatalog()` by `platform/scripts/manifest/generate_projections.ts`), a DIFFERENT
 * POPULATION from this server's `server.tool()` registrations. Measured 2026-07-30 against
 * revision `amjis-mcp-00517-b5q`: the manifest said 152 while `tools/list` returned 124,
 * overlapping by only 15 of 124 names — 109 genuinely-served MCP tools were absent from the
 * manifest, and manifest entries like `assess_career`/`assess_wealth` were counted although
 * they are registry faces, not MCP tools (see
 * `00_ARCHITECTURE/briefs/samapti/SAMAPTI_MCP_TOOL_GAP_CHARACTERIZATION_v1_0.md`).
 *
 * That is the §N.8 earned-signal violation in its purest form: a health number that would
 * NOT have moved if the served MCP surface had collapsed to zero. Worse than staleness —
 * staleness at least means the number was once true of the thing it names.
 *
 * The fix is RENAME AND RE-SOURCE, both, per Ruling 25:
 *   - `tool_count` (the field consumers already read as "the served catalog size") is now
 *     LIVE-DERIVED by `censusServedTools()` from the request-scoped `McpServer`'s own tool
 *     registry — the very object `tools/list` enumerates. It moves when the surface moves.
 *   - The manifest figure is NOT deleted (it answers a real, different question: how large
 *     is the retrieval registry's `full` projection). It is renamed to the self-describing
 *     `RETRIEVAL_REGISTRY_PROFILE_TOTAL` and carries `RETRIEVAL_REGISTRY_PROFILE_GENERATED_AT`,
 *     because a figure generated on one date and served forever after as live telemetry is
 *     stale by construction and must date-stamp itself.
 *
 * `MCP_CATALOG_VERSION`'s value is deliberately UNCHANGED (still derived from the manifest)
 * — it is a client-facing CACHE KEY, and re-sourcing it would invalidate every cached
 * catalog and silently change staleness semantics for existing callers. That it fingerprints
 * the registry projection rather than the served catalog is a real, separate defect; it is
 * reported as a residual by this lane, not silently re-pointed here.
 */
import { createHash } from 'node:crypto'
import { statSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import {
  MCP_SURFACE_PROFILES,
  MCP_SURFACE_PROFILES_GENERATED_AT,
} from '../generated/mcp_surface_profiles.generated.js'

/** Deterministic content hash of the full-profile tool_names census. */
function catalogContentHash(): string {
  const canonical = JSON.stringify(MCP_SURFACE_PROFILES.full.tool_names)
  return createHash('sha256').update(canonical).digest('hex').slice(0, 12)
}

/**
 * Size of the RETRIEVAL REGISTRY's `full` MCP projection, as recorded in the vendored
 * generated manifest. **This is not the served MCP tool count** — see the banner. Renamed
 * from the former `MCP_CATALOG_TOOL_COUNT`, which invited exactly that misreading and was
 * being served as `mcp_server_info.tool_count`. Always report it next to
 * `RETRIEVAL_REGISTRY_PROFILE_GENERATED_AT`; it is a build-time figure, not live telemetry.
 */
export const RETRIEVAL_REGISTRY_PROFILE_TOTAL = MCP_SURFACE_PROFILES.full.total

/** When `RETRIEVAL_REGISTRY_PROFILE_TOTAL` was generated. Never serve the total without it. */
export const RETRIEVAL_REGISTRY_PROFILE_GENERATED_AT = MCP_SURFACE_PROFILES_GENERATED_AT

/** The live MCP tool-catalog version, e.g. `catalog-1+t152+r3f9a1c8e2b04`. Deterministic — a
 *  pure function of the vendored generated manifest (tool_names + total). Value intentionally
 *  UNCHANGED by the Ruling-25 re-sourcing: it is a client cache key (see banner). */
export const MCP_CATALOG_VERSION =
  `catalog-1+t${RETRIEVAL_REGISTRY_PROFILE_TOTAL}+r${catalogContentHash()}`

// ── Live served-catalog census (DVA Ruling 25) ────────────────────────────────────────────

/** Minimal structural shape of one entry in the SDK's own registered-tool map. */
interface RegisteredToolLike {
  enabled?: boolean
}

export interface ServedToolCensus {
  /** Number of tools this request's server will return from `tools/list`. `null` = unreadable. */
  count: number | null
  /** Sorted names behind `count`. Empty iff `count` is 0 or `null`. */
  names: string[]
  /** How `count` was derived, or (when `null`) why it could not be. Never a fabricated number. */
  note: string
}

/**
 * Count the tools this request's `McpServer` will actually serve, by reading the SAME
 * registry the SDK's own `tools/list` handler enumerates.
 *
 * The SDK (`@modelcontextprotocol/sdk` ≥1.12, verified against 1.29.0
 * `dist/esm/server/mcp.js`) answers `ListToolsRequest` with
 * `Object.entries(this._registeredTools).filter(([, tool]) => tool.enabled)`. This function
 * mirrors that expression exactly, so its count is `tools/list`'s length by construction, not
 * by a parallel tally that can drift — which is the entire defect being fixed here.
 *
 * WHY READ THE REGISTRY RATHER THAN COUNT REGISTRATION CALLS: three gates in `server.ts`
 * (`applyStrictSchemaGate`, `applyDeprecatedToolGate`, `applyProfileGate`) monkeypatch
 * `.tool()` in layers, and the strict gate re-issues registrations through `.registerTool()`.
 * Any call-site tally would have to model all three gates correctly and would silently
 * over-report the day a fourth gate lands — the *precise* failure mode that made
 * `sc_pointer_validation.ts` pass 32 dead pointers (SAMĀPTI lane A2). The registry is
 * downstream of every gate, so it cannot over-report.
 *
 * PER-PROFILE BY DESIGN: a `consult`-profile OAuth caller sees a smaller catalog than a
 * first-party Bearer caller, and this returns each caller's OWN number — the honest answer to
 * "how many tools can I call". A first-party Bearer key resolves to `full`, for which
 * `applyProfileGate` is an explicit no-op, so it yields the unfiltered served surface.
 *
 * B.10 — NEVER FABRICATED: if the registry cannot be read (an SDK internal rename), this
 * returns `count: null` with a note saying so. It does not fall back to the manifest figure;
 * substituting a plausible number from the wrong population is the bug being removed.
 */
export function censusServedTools(server: McpServer): ServedToolCensus {
  const registry = (server as unknown as {
    _registeredTools?: Record<string, RegisteredToolLike>
  })._registeredTools

  if (registry === null || typeof registry !== 'object') {
    return {
      count: null,
      names: [],
      note:
        'Could not read this server instance\'s registered-tool registry to count the served ' +
        'catalog — never fabricated (B.10), and deliberately NOT defaulted to the generated ' +
        'retrieval-registry manifest figure (a different population; see ' +
        'retrieval_registry_profile_total). Call tools/list for the authoritative catalog.',
    }
  }

  const names = Object.entries(registry)
    .filter(([, tool]) => Boolean(tool?.enabled))
    .map(([name]) => name)
    .sort()

  return {
    count: names.length,
    names,
    note:
      'Live count of the tools registered on THIS request\'s MCP server after all gates ' +
      '(strict-schema, RC-14 deprecated-name, profile) have been applied — mirrors the SDK ' +
      'tools/list filter exactly, so it equals the length of your own tools/list response. ' +
      'Profile-scoped: a narrower OAuth profile legitimately sees a smaller number.',
  }
}

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
