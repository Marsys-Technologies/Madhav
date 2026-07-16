/**
 * alias_check.ts — D-2 Lane V-0, BIND_D-2.md §F1.7 ledger row 4.
 *
 * "Alias-count check: deployed tools/list count reconciles with V-3's canonical-face list +
 * declared deprecations; no orphan twins." V-3 (the lane that AUTHORS the canonical-face list,
 * BRIEF_D2.md §F1 Lane V-3 — "twin-alias dedup → the canonical-face list, authored HERE, Track-3
 * absent") is cycle-2, so at V-0 build time no canonical-face file exists yet. Per the task's own
 * instruction for this situation ("write the check to consume a canonical-face-list file/
 * registry entry by a stable path/interface; coordinate implicitly by using the interface V-3's
 * may_touch glob implies... if genuinely blocked, stub with a clear TODO and self-test evidence
 * showing the stub, and flag it explicitly"):
 *
 *   - CANONICAL_FACES_PATH below is the STABLE INTERFACE this check consumes, inside V-3's
 *     declared may_touch glob (`platform/src/lib/retrieval/registry/**`) — V-3 lands a file at
 *     this path (or the check is trivially repointed to whatever V-3 actually ships; the path is
 *     a documented contract, not a guess baked in twice).
 *   - Expected file shape: `{ canonical_faces: string[], deprecated_aliases: { [aliasName: string]: string } }`
 *     (each deprecated_aliases value is the canonical name the alias maps to).
 *   - Until V-3 ships that file, this module computes a MECHANICAL FALLBACK using the same
 *     `[Phase-1 alias] ... (same as <primitive>)` marker-discovery technique already live in
 *     platform/scripts/audit/alias_conformance_check.ts (out of this lane's may_touch — the
 *     technique is reused, the file is not touched) — deriving a best-effort canonical set
 *     directly from the live tools/list descriptions. This is NOT a substitute for V-3's
 *     authored dedup (only markers that were actually annotated `[Phase-1 alias]` are caught;
 *     BIND_D-2.md §B.5's alias-pair sample includes several NOT marked this way, e.g.
 *     get_signals/bodha_signals_get) — every result from this path is explicitly labeled
 *     `source: 'mechanical_fallback_pending_v3'` so a caller can never mistake it for V-3's
 *     authored list.
 */
import { readFileSync, existsSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import type { McpToolDescriptor } from './mcp_client'

// STABLE INTERFACE — V-3's may_touch glob is `platform/src/lib/retrieval/registry/**`; this is
// the path this check watches for the authored canonical-face list.
const CANONICAL_FACES_RELATIVE_PATH = 'platform/src/lib/retrieval/registry/canonical_faces.json'

export type CanonicalFacesFile = {
  canonical_faces: string[]
  deprecated_aliases: Record<string, string>
}

export type AliasCheckResult = {
  source: 'v3_canonical_face_list' | 'mechanical_fallback_pending_v3'
  live_tool_count: number
  canonical_face_count: number
  deprecated_alias_count: number
  orphan_twins: string[] // live tools that look like an alias pair but neither name is in the canonical set
  unaccounted_tools: string[] // live tools that are neither canonical nor a declared deprecated alias
  reconciles: boolean
  detail: string
}

function repoRoot(): string {
  const here = fileURLToPath(import.meta.url) // .../platform/scripts/audit/doctrine_harness/lib/alias_check.ts
  return join(here, '..', '..', '..', '..', '..', '..')
}

export function loadCanonicalFacesFile(): CanonicalFacesFile | null {
  const path = join(repoRoot(), CANONICAL_FACES_RELATIVE_PATH)
  if (!existsSync(path)) return null
  try {
    const parsed = JSON.parse(readFileSync(path, 'utf8'))
    if (!Array.isArray(parsed.canonical_faces)) return null
    return {
      canonical_faces: parsed.canonical_faces,
      deprecated_aliases: parsed.deprecated_aliases ?? {},
    }
  } catch {
    return null
  }
}

const ALIAS_MARKER = /^\[Phase-1 alias\]/
const SAME_AS_PATTERN = /\(same as ([a-zA-Z0-9_]+)\)/

/** Mechanical fallback: same discovery technique as alias_conformance_check.ts's
 *  discoverPairs — reused logic, not a copied file (that script lives outside V-0's may_touch). */
function mechanicalCanonicalFaces(tools: McpToolDescriptor[]): { canonical: Set<string>; aliasToCanonical: Map<string, string> } {
  const aliasToCanonical = new Map<string, string>()
  for (const t of tools) {
    const desc = t.description ?? ''
    if (!ALIAS_MARKER.test(desc)) continue
    const m = desc.match(SAME_AS_PATTERN)
    if (m) aliasToCanonical.set(t.name, m[1])
  }
  const allNames = new Set(tools.map((t) => t.name))
  const canonical = new Set([...allNames].filter((n) => !aliasToCanonical.has(n)))
  return { canonical, aliasToCanonical }
}

export function checkAliasCount(tools: McpToolDescriptor[]): AliasCheckResult {
  const liveNames = tools.map((t) => t.name)
  const canonicalFile = loadCanonicalFacesFile()

  if (canonicalFile) {
    const canonicalSet = new Set(canonicalFile.canonical_faces)
    const deprecatedSet = new Set(Object.keys(canonicalFile.deprecated_aliases))
    const unaccounted = liveNames.filter((n) => !canonicalSet.has(n) && !deprecatedSet.has(n))
    const orphanTwins = [...deprecatedSet].filter((alias) => {
      const canonical = canonicalFile.deprecated_aliases[alias]
      return !canonicalSet.has(canonical) // the alias's declared canonical target doesn't itself exist live
    })
    return {
      source: 'v3_canonical_face_list',
      live_tool_count: liveNames.length,
      canonical_face_count: canonicalFile.canonical_faces.length,
      deprecated_alias_count: deprecatedSet.size,
      orphan_twins: orphanTwins,
      unaccounted_tools: unaccounted,
      reconciles: unaccounted.length === 0 && orphanTwins.length === 0,
      detail: `Reconciled against V-3's authored canonical-face list (${CANONICAL_FACES_RELATIVE_PATH}).`,
    }
  }

  // TODO(V-3): once platform/src/lib/retrieval/registry/canonical_faces.json ships, this
  // fallback branch stops executing (loadCanonicalFacesFile() finds the file) and every result
  // reports source: 'v3_canonical_face_list' instead. Until then this branch is the documented,
  // explicitly-flagged stub.
  const { canonical, aliasToCanonical } = mechanicalCanonicalFaces(tools)
  const orphanTwins = [...aliasToCanonical.entries()]
    .filter(([, primitive]) => !canonical.has(primitive) && !liveNames.includes(primitive))
    .map(([alias]) => alias)
  return {
    source: 'mechanical_fallback_pending_v3',
    live_tool_count: liveNames.length,
    canonical_face_count: canonical.size,
    deprecated_alias_count: aliasToCanonical.size,
    orphan_twins: orphanTwins,
    unaccounted_tools: [], // mechanical fallback accounts for every tool by construction (canonical ∪ alias = all)
    reconciles: orphanTwins.length === 0,
    detail:
      `STUB: V-3's canonical-face list not found at ${CANONICAL_FACES_RELATIVE_PATH} — falling back to mechanical ` +
      `[Phase-1 alias] marker discovery (${aliasToCanonical.size} marked alias pairs found among ${liveNames.length} live tools). ` +
      `This under-counts true aliasing (BIND_D-2.md §B.5 names unmarked twins like get_signals/bodha_signals_get) — ` +
      `it is NOT a substitute for V-3's authored dedup. Re-run once V-3 ships the file.`,
  }
}
