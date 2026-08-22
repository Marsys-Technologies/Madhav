/**
 * extract_registrar_capability_bridge.ts — F-155 fix (PARIŚEṢA V4)
 * ================================================================================
 * FINDING: `projection_builders.ts`'s `buildMcpToolRegistration()` emitted
 * `tool_name: cap.name` — the registry's INTERNAL capability name (e.g.
 * `chart_facts_query`, `get_positions`, `call_priority_ranking`) — where the
 * request-time serving gate (`platform-mcp/src/lib/mcp_profile.ts::applyProfileGate`)
 * matches the PUBLIC name a real `server.tool(...)` call registers under (e.g.
 * `ganita_chart_facts_get`, `ganita_positions_get`, `kala_priority_ranking_get`).
 * Fails closed (an unmatched name is simply never callable — no security exposure),
 * but under-serves: measured, the compact/consult allowlists this mismatch produced
 * resolve only a fraction of their declared entries against the real registration set.
 *
 * ROOT CAUSE, IN FULL: THREE separate name layers exist for the same capability:
 *   1. `cap.name` (registry descriptor identity) — near-always the tail segment of
 *      `cap.uri` (e.g. `marsys://tool/L1/chart_facts_query` -> `chart_facts_query`).
 *   2. The legacy hand-written name `registry_bridge.ts` registers it under (e.g.
 *      `query_chart_facts`) — DIFFERENT again from (1), and often already gated OFF
 *      unconditionally by `platform-mcp/src/lib/deprecated_tool_gate.ts` (the RC-14
 *      breaking flip; mirrors `canonical_faces.json`'s `deprecated_aliases` KEYS).
 *   3. The CANONICAL go-forward public face (e.g. `ganita_chart_facts_get`) —
 *      registered by `register_p1_aliases.ts` / `register_p1_ganita.ts` / etc., and
 *      the ONLY one of the three actually reachable through both gates for most
 *      capabilities. `canonical_faces.json`'s `canonical_faces` array already curates
 *      most of these by hand — this module derives the same answer MECHANICALLY, by
 *      source-text parsing every registrar file's real `server.tool(...)` call sites
 *      (generalizing `extract_registry_bridge_tools.ts`'s method — source-TEXT parsing,
 *      not import/execution, so this needs no runnable MCP server), so newly-added
 *      registrations are picked up without a second hand-authored list to keep in sync.
 *
 * PRIOR ART THIS GENERALIZES (do not invent a new mechanism — see plan §F-155):
 *   - `extract_registry_bridge_tools.ts` already mechanically extracts
 *     `server.tool(...)` names + `marsys://` URIs from ONE file (`registry_bridge.ts`)
 *     by source-text parsing. This module applies the same technique across EVERY
 *     registrar file under `platform-mcp/src/tools/` (register_p1_aliases.ts,
 *     register_p1_ganita.ts, l0_brahmagyan.ts, kala_views/*.ts, retrieval/*.ts, …).
 *   - `sensitive_capability_class.ts:37-50` (MORTALITY_CLASS_CAPABILITIES etc.) already
 *     works around this exact internal/public split by hand — listing BOTH
 *     `get_ayurdaya` (internal) AND `ganita_ayurdaya_get` (public) side by side rather
 *     than resolving the mapping once. That belt-and-suspenders list stays (cheap,
 *     harmless insurance for a safety-critical exclusion), but a systemic fix removes
 *     the NEED for every future consumer to duplicate names defensively like this.
 *
 * RESOLUTION ALGORITHM, per catalog capability:
 *   1. If `cap.name` ITSELF is a live (non-deprecated) `server.tool()` registration
 *      anywhere in the registrar surface, keep it — most capabilities (workflow tools
 *      like `chart_snapshot`, `judgment_query`, `pact_query`, `assess_*`, and every
 *      `ganita_*_get`/`bodha_*_get`/… P1 alias whose OWN registered name already equals
 *      `cap.name`) are ALREADY correct; this step guarantees zero behavior change for
 *      them.
 *   2. Else, resolve via `cap.uri`: find every registrar block whose SOLE literal
 *      registry-capability call (`callRegistryCapability(...)` / `callRegistryCap(...)`,
 *      or `callPlatformPrim(...)` resolved through `tool_name_bridge.ts`'s
 *      `TOOL_NAME_TO_URI`, or a `regAlias(server, name, desc, uri, ...)` /
 *      `globalAlias(...)` call's explicit URI argument) is `cap.uri`. A block with
 *      MULTIPLE distinct capability calls is a workflow/aggregator tool with no honest
 *      1:1 answer and is excluded from candidacy (it never needed step 2 anyway — its
 *      own name already resolves via step 1, or it genuinely has none).
 *   3. Zero, one, or many candidates: zero means the capability has NO real serving
 *      tool anywhere — reported as `unresolved` so the profile builder can honestly
 *      EXCLUDE it (never emit a name nobody can call). One is the answer. Many (a real
 *      capability served under more than one live alias) picks the candidate also
 *      listed in `canonical_faces.json`'s curated `canonical_faces` array when exactly
 *      one qualifies, else the lexicographically-first candidate — both cases reported
 *      under `ambiguous` for auditability rather than silently arbitrary.
 *
 * ONE DOCUMENTED CARVE-OUT: `marsys://tool/L1/get_chart_header` is EXCLUDED from step 2's
 * "sole capability call" signal. It is fetched via the shared `resolveChartHeader()` /
 * `fetchOrientationContext()` enrichment helpers to fill the `chart_header`/
 * `orientation_context` block of many UNRELATED tools' responses (B.11 frame-safety),
 * never as any tool's own reason to exist. Verified concretely: without this carve-out,
 * the dispatcher tool `ganita_structural_get` (whose OWN capability URI is resolved at
 * runtime through a `facet` lookup TABLE — a variable, never a source-text literal) would
 * be mechanically misattributed as `get_chart_header`'s serving tool, because the
 * `get_chart_header` enrichment call is the ONLY literal registry-capability call visible
 * in its block. Carving it out makes `get_chart_header` correctly resolve to zero live
 * candidates (honest — it has no dedicated public tool) instead of a fabricated wrong name.
 */
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'
import canonicalFacesRaw from '../../src/lib/retrieval/registry/canonical_faces.json'
import { TOOL_NAME_TO_URI } from '../../src/lib/retrieval/registry/tool_name_bridge'
import type { CapabilityDescriptor, CapabilityUri } from '../../src/lib/retrieval/registry/types'

const canonicalFaces = canonicalFacesRaw as { canonical_faces: string[]; deprecated_aliases: Record<string, string> }

export const PLATFORM_MCP_TOOLS_DIR = join(__dirname, '..', '..', '..', 'platform-mcp', 'src', 'tools')

/** Mirror of `canonical_faces.json`'s `deprecated_aliases` KEYS — see module banner §layer 2.
 *  These names are unconditionally gated off by `platform-mcp/src/lib/deprecated_tool_gate.ts`
 *  (all profiles, including `full`) and must never be treated as "live". */
const DEPRECATED_NAMES: ReadonlySet<string> = new Set(Object.keys(canonicalFaces.deprecated_aliases))

/** See module banner "ONE DOCUMENTED CARVE-OUT". */
const ENRICHMENT_ONLY_URIS: ReadonlySet<CapabilityUri> = new Set(['marsys://tool/L1/get_chart_header'])

// ── Directory walk ────────────────────────────────────────────────────────────

function walkTsFiles(dir: string): string[] {
  const out: string[] = []
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry)
    const st = statSync(p)
    if (st.isDirectory()) {
      out.push(...walkTsFiles(p))
    } else if (entry.endsWith('.ts') && !entry.includes('.test.') && !p.includes('__tests__')) {
      out.push(p)
    }
  }
  return out
}

// ── Source-text scanning primitives (same discipline as extract_registry_bridge_tools.ts) ──

/** Quote-aware scan of a string literal starting at `s[i]` (s[i] must be `'`, `"`, or `` ` ``). */
function scanStringLiteral(s: string, i: number): { content: string; end: number } {
  const quote = s[i]
  let j = i + 1
  let content = ''
  while (j < s.length && s[j] !== quote) {
    if (s[j] === '\\') {
      content += s[j] + (s[j + 1] ?? '')
      j += 2
    } else {
      content += s[j]
      j += 1
    }
  }
  return { content, end: j + 1 }
}

/** Every occurrence of `marker` followed (after whitespace) by a string-literal first argument. */
function scanLiteralFirstArgCalls(
  text: string,
  marker: string,
): { arg: string; index: number }[] {
  const out: { arg: string; index: number }[] = []
  let searchFrom = 0
  for (;;) {
    const idx = text.indexOf(marker, searchFrom)
    if (idx === -1) break
    searchFrom = idx + marker.length
    let i = idx + marker.length
    while (i < text.length && /\s/.test(text[i]!)) i++
    if (!"'\"`".includes(text[i] ?? '')) continue
    const { content } = scanStringLiteral(text, i)
    out.push({ arg: content, index: idx })
  }
  return out
}

/** `const IDENT = 'literal'` module-level declarations (resolves `server.tool(TOOL_NAME, ...)`
 *  call sites where the name argument is a bare identifier — e.g. phala_outlook.ts's
 *  `const TOOL_NAME = 'phala_outlook'` pattern — rather than a literal). */
function scanLocalConstStrings(text: string): Map<string, string> {
  const map = new Map<string, string>()
  const re = /const\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*[^=]+)?=\s*(['"])((?:\\.|(?!\2).)*)\2/g
  let m: RegExpExecArray | null
  while ((m = re.exec(text))) map.set(m[1]!, m[3]!)
  return map
}

/** Direct `server.tool('name', ...)` call sites (literal name, or identifier resolved via
 *  a local `const` — see `scanLocalConstStrings`). Next-occurrence bounded blocks. */
function scanToolRegistrations(text: string): { name: string; index: number }[] {
  const constMap = scanLocalConstStrings(text)
  const marker = 'server.tool('
  const out: { name: string; index: number }[] = []
  let searchFrom = 0
  for (;;) {
    const idx = text.indexOf(marker, searchFrom)
    if (idx === -1) break
    searchFrom = idx + marker.length
    let i = idx + marker.length
    while (i < text.length && /\s/.test(text[i]!)) i++
    if ("'\"`".includes(text[i] ?? '')) {
      const { content } = scanStringLiteral(text, i)
      out.push({ name: content, index: idx })
      continue
    }
    // Bare identifier — resolve via local const map; skip (defensively) if unresolvable
    // rather than fabricate a name (same discipline as extract_registry_bridge_tools.ts).
    let j = i
    while (j < text.length && /[A-Za-z0-9_]/.test(text[j]!)) j++
    const ident = text.slice(i, j)
    const resolved = constMap.get(ident)
    if (resolved) out.push({ name: resolved, index: idx })
  }
  return out
}

/** `regAlias(server, 'name', 'desc', 'uri', ...)` / `globalAlias(...)` direct (name, uri) pairs
 *  (register_p1_aliases.ts's helper wrappers — the actual `server.tool(name, ...)` call inside
 *  them uses a variable, not a literal, so `scanToolRegistrations` cannot see these; the name
 *  and URI are both literal ARGUMENTS to the wrapper call itself, which this scans directly). */
function scanAliasHelperPairs(text: string): { name: string; uri: string }[] {
  const out: { name: string; uri: string }[] = []
  for (const marker of ['regAlias(server,', 'globalAlias(server,']) {
    let searchFrom = 0
    for (;;) {
      const idx = text.indexOf(marker, searchFrom)
      if (idx === -1) break
      searchFrom = idx + marker.length
      let i = idx + marker.length
      while (i < text.length && /\s/.test(text[i]!)) i++
      if (!"'\"`".includes(text[i] ?? '')) continue
      const { content: name, end } = scanStringLiteral(text, i)
      // Walk the next up-to-two string literals: description, then URI.
      let p = end
      const literals: string[] = []
      for (let n = 0; n < 2 && p < text.length; n++) {
        while (p < text.length && !"'\"`".includes(text[p]!) && text[p] !== ')') p++
        if (text[p] === ')') break
        const lit = scanStringLiteral(text, p)
        literals.push(lit.content)
        p = lit.end
      }
      if (literals.length >= 2 && literals[1]!.startsWith('marsys://')) {
        out.push({ name, uri: literals[1]! })
      }
    }
  }
  return out
}

// ── Per-file, per-block capability-URI binding ──────────────────────────────────

export interface RegistrarCapabilityBinding {
  tool_name: string
  capability_uri: CapabilityUri
  source_file: string
}

/**
 * Every registrar file's real, live (`server.tool()`-reachable) tool-name -> capability-URI
 * binding, established only where a block's own capability call is UNAMBIGUOUS (see module
 * banner, resolution step 2). Also returns the plain set of every literal tool name found
 * (regardless of URI ambiguity) for resolution step 1.
 */
export function extractRegistrarCapabilityBindings(toolsDir: string = PLATFORM_MCP_TOOLS_DIR): {
  bindings: RegistrarCapabilityBinding[]
  liveDirectNames: Set<string>
} {
  const files = walkTsFiles(toolsDir)
  const bindings: RegistrarCapabilityBinding[] = []
  const liveDirectNames = new Set<string>()

  for (const file of files) {
    const text = readFileSync(file, 'utf-8')

    const regs = scanToolRegistrations(text).sort((a, b) => a.index - b.index)
    for (const r of regs) if (!DEPRECATED_NAMES.has(r.name)) liveDirectNames.add(r.name)

    const capCalls = [
      ...scanLiteralFirstArgCalls(text, 'callRegistryCapability('),
      ...scanLiteralFirstArgCalls(text, 'callRegistryCap('),
    ]
    const primCalls = scanLiteralFirstArgCalls(text, 'callPlatformPrim(')

    for (let i = 0; i < regs.length; i++) {
      const cur = regs[i]!
      if (DEPRECATED_NAMES.has(cur.name)) continue
      const blockStart = cur.index
      const blockEnd = i + 1 < regs.length ? regs[i + 1]!.index : Infinity

      const urisInBlock = new Set(
        capCalls
          .filter((c) => c.index > blockStart && c.index < blockEnd)
          .map((c) => c.arg)
          .filter((uri) => !ENRICHMENT_ONLY_URIS.has(uri)),
      )
      const primsInBlock = new Set(
        primCalls.filter((c) => c.index > blockStart && c.index < blockEnd).map((c) => c.arg),
      )
      const primUris = new Set(
        Array.from(primsInBlock)
          .map((p) => (TOOL_NAME_TO_URI as Record<string, string>)[p])
          .filter((u): u is string => Boolean(u)),
      )

      const allUris = new Set([...urisInBlock, ...primUris])
      if (allUris.size === 1) {
        bindings.push({ tool_name: cur.name, capability_uri: [...allUris][0]!, source_file: file })
      }
    }

    for (const { name, uri } of scanAliasHelperPairs(text)) {
      if (DEPRECATED_NAMES.has(name)) continue
      bindings.push({ tool_name: name, capability_uri: uri, source_file: file })
    }
  }

  return { bindings, liveDirectNames }
}

// ── Capability -> public-name resolution ────────────────────────────────────────

export interface CapabilityPublicNameBridge {
  /** cap.name -> resolved live public tool_name. Every entry is a REAL, callable name. */
  resolved: ReadonlyMap<string, string>
  /** cap.name -> full candidate set, only present when 2+ live names serve the same URI
   *  (an honest ambiguity — `resolved` still picks one deterministically). */
  ambiguous: ReadonlyMap<string, readonly string[]>
  /** cap.name list with ZERO live serving tool anywhere in the registrar surface. */
  unresolved: readonly string[]
}

export function buildCapabilityPublicNameBridge(
  caps: readonly CapabilityDescriptor[],
  toolsDir: string = PLATFORM_MCP_TOOLS_DIR,
): CapabilityPublicNameBridge {
  const { bindings, liveDirectNames } = extractRegistrarCapabilityBindings(toolsDir)

  const uriToNames = new Map<string, Set<string>>()
  for (const b of bindings) {
    if (!uriToNames.has(b.capability_uri)) uriToNames.set(b.capability_uri, new Set())
    uriToNames.get(b.capability_uri)!.add(b.tool_name)
  }

  const canonicalSet = new Set(canonicalFaces.canonical_faces)
  const resolved = new Map<string, string>()
  const ambiguous = new Map<string, string[]>()
  const unresolved: string[] = []

  for (const cap of caps) {
    if (liveDirectNames.has(cap.name)) {
      resolved.set(cap.name, cap.name)
      continue
    }
    const candidates = Array.from(uriToNames.get(cap.uri) ?? [])
    if (candidates.length === 0) {
      unresolved.push(cap.name)
      continue
    }
    if (candidates.length === 1) {
      resolved.set(cap.name, candidates[0]!)
      continue
    }
    // Ambiguous: 2+ live names serve this URI. Prefer the one canonical_faces.json
    // curates, when exactly one candidate qualifies; else lexicographically first —
    // both deterministic, both reported (never silently arbitrary).
    const canonicalCandidates = candidates.filter((n) => canonicalSet.has(n))
    const chosen = canonicalCandidates.length === 1 ? canonicalCandidates[0]! : [...candidates].sort()[0]!
    resolved.set(cap.name, chosen)
    ambiguous.set(cap.name, candidates.sort())
  }

  return { resolved, ambiguous, unresolved }
}
