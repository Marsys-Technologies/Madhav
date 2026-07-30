/**
 * mcp_registered_tools.ts — shared static enumeration of every MCP tool name
 * actually registered on the live server.
 *
 * Ring-2 review finding (post-bacade1c): the original per-script copy of
 * this logic only matched literal `server.tool('name', ...)` call sites. It
 * missed the `regAlias(server, '<name>', ...)` / `globalAlias(server, '<name>',
 * ...)` helper pattern used by register_p1_aliases.ts (own header comment:
 * "The 47 aliases implemented in this file cover the remaining 47 of the 53
 * baseline tools") — those helpers call `server.tool(name, ...)` internally
 * with `name` passed in as a parameter, so the literal-string regex never
 * saw them. That produced two false-positive "unresolved pointer" findings
 * (phala_predictive_anchors_get, bodha_remedies_get — both ARE registered,
 * via regAlias at register_p1_aliases.ts:416 and :393) in the first cut of
 * sc_pointer_validation.ts.
 *
 * This module is the single source of truth for "is `name` a live tool" —
 * both sc_pointer_validation.ts and mcp_tool_smoke.ts import it so the fix
 * can't drift between the two call sites again.
 *
 * ── RC-14 GATE CORRECTION (SAMĀPTI lane A2, 2026-07-30) ──────────────────────
 * The claim in this file's own first line — "every MCP tool name actually
 * registered on the live server" — was FALSE BY 43 NAMES, and had been since
 * the RC-14 breaking flip (2026-07-23). RC-14 removed the 43 legacy P1 short
 * names from the served surface, but did so via a CENTRAL RUNTIME GATE
 * (`platform-mcp/src/lib/deprecated_tool_gate.ts`) rather than by deleting the
 * 43 `server.tool('legacy_name', ...)` call sites — deliberately, and for good
 * reasons stated in that file. The consequence for THIS resolver is that all
 * 43 gated names are still present as literal registration call sites in the
 * source it scans, so it kept reporting them as live.
 *
 * That is not a cosmetic over-count. It is what let `sc_pointer_validation.ts`
 * PASS 32 production drill-pointer/recover sites that dead-end on the live
 * server with "Tool <name> not found" — the exact SC-18 harm ("the recovery
 * path fires exactly when data was withheld and points at tool-not-found"),
 * reintroduced wholesale by RC-14 and invisible to the check meant to catch it.
 *
 * The fix models the gate instead of ignoring it: subtract
 * `DEPRECATED_MCP_TOOL_NAMES` from the statically-scanned set. This is exact,
 * not approximate — verified 2026-07-30 against the live catalog
 * (`tools/list` on the deployed amjis-mcp with a first-party Bearer key, which
 * resolves to the `full` profile and therefore applies NO profile filtering):
 *   167 scanned − 43 gated = 124 predicted, and the live catalog is 124 tools,
 *   set-for-set identical (zero predicted-not-live, zero live-not-predicted).
 * So the offline check is now live-accurate WITHOUT a network dependency in CI.
 */
import path from 'node:path'
import { readFileSync, readdirSync, statSync } from 'node:fs'

const REPO_ROOT = path.join(__dirname, '../../../../..')
const MCP_TOOLS_ROOT = path.join(REPO_ROOT, 'platform-mcp/src/tools')
const DEPRECATED_GATE_FILE = path.join(REPO_ROOT, 'platform-mcp/src/lib/deprecated_tool_gate.ts')

function walkTs(dir: string, out: string[]): void {
  let entries: string[]
  try {
    entries = readdirSync(dir)
  } catch {
    return
  }
  for (const entry of entries) {
    if (entry === 'node_modules' || entry === '.git') continue
    const full = path.join(dir, entry)
    const st = statSync(full)
    if (st.isDirectory()) walkTs(full, out)
    else if (entry.endsWith('.ts')) out.push(full)
  }
}

/**
 * Statically resolves every tool name registered on the live MCP server by
 * scanning platform-mcp/src/tools for three registration shapes:
 *   1. `server.tool('name', ...)`               — direct literal call sites.
 *   2. `regAlias(server, 'name', ...)`           — chart-scoped alias helper
 *      (register_p1_aliases.ts), which itself calls `server.tool(name, ...)`.
 *   3. `globalAlias(server, 'name', ...)`        — global-scope alias helper,
 *      same file, same delegation pattern.
 *   4. `server.tool(TOOL_NAME, ...)` where `const TOOL_NAME = 'name'` is
 *      declared in the SAME file as the call site — resolved per-file, not
 *      hardcoded to one filename. (R6 3b-budgets fix: the original version
 *      only special-cased kala_temporal.ts by path; phala_event_anchors.ts
 *      uses the identical pattern and was silently missed — a Ring-2-adjacent
 *      finding surfaced when a new self-recovery pointer in that file first
 *      cited its own TOOL_NAME-registered name, tripping SC-pointer's
 *      registered-set check. Generalizing per-file avoids the next file that
 *      adopts this pattern hitting the same silent gap.)
 */
export function collectRegisteredTools(): Set<string> {
  const names = collectRegistrationCallSites()
  for (const gated of collectDeprecatedToolNames()) names.delete(gated)
  return names
}

/**
 * The raw pre-gate scan: every name that HAS a registration call site in
 * source, including the RC-14-gated legacy names. Exported for diagnostics
 * (the static-vs-served delta is itself a finding worth reporting) — callers
 * asking "is this servable?" want `collectRegisteredTools()`, not this.
 */
export function collectRegistrationCallSites(): Set<string> {
  const files: string[] = []
  walkTs(MCP_TOOLS_ROOT, files)
  const names = new Set<string>()
  for (const f of files) {
    const src = readFileSync(f, 'utf-8')
    for (const m of src.matchAll(/server\.tool\(\s*['"]([a-zA-Z0-9_]+)['"]/g)) names.add(m[1])
    for (const m of src.matchAll(/\b(?:regAlias|globalAlias)\(\s*server,\s*['"]([a-zA-Z0-9_]+)['"]/g)) names.add(m[1])
    if (/server\.tool\(\s*TOOL_NAME\s*,/.test(src)) {
      const m = src.match(/const TOOL_NAME\s*=\s*['"]([a-zA-Z0-9_]+)['"]/)
      if (m) names.add(m[1])
    }
  }
  return names
}

/**
 * Parses `DEPRECATED_MCP_TOOL_NAMES` out of `deprecated_tool_gate.ts` — the
 * RC-14 removal set, applied UNCONDITIONALLY at runtime for every profile
 * including `full`.
 *
 * THROWS rather than degrading if the set cannot be parsed. A silent fallback
 * to "assume nothing is gated" would restore precisely the over-approximation
 * this function exists to remove, and would do it invisibly — a detector that
 * quietly stops detecting is worse than one that is absent (CLAUDE.md §N.8).
 * If the gate file's shape changes, this must fail loudly and be re-pointed.
 */
export function collectDeprecatedToolNames(): Set<string> {
  const src = readFileSync(DEPRECATED_GATE_FILE, 'utf-8')
  const declIdx = src.indexOf('DEPRECATED_MCP_TOOL_NAMES')
  if (declIdx === -1) {
    throw new Error(
      `mcp_registered_tools: DEPRECATED_MCP_TOOL_NAMES not found in ${DEPRECATED_GATE_FILE}. ` +
      `The RC-14 gate has moved or been renamed — re-point this parser. Refusing to fall back to ` +
      `an ungated (43-name over-reporting) tool set.`
    )
  }
  const openIdx = src.indexOf('new Set([', declIdx)
  const closeIdx = src.indexOf('])', openIdx)
  if (openIdx === -1 || closeIdx === -1) {
    throw new Error(
      `mcp_registered_tools: could not parse the DEPRECATED_MCP_TOOL_NAMES set literal in ` +
      `${DEPRECATED_GATE_FILE}. Refusing to fall back to an ungated tool set.`
    )
  }
  const names = new Set<string>(
    [...src.slice(openIdx, closeIdx).matchAll(/['"]([a-zA-Z0-9_.]+)['"]/g)].map((m) => m[1])
  )
  if (names.size === 0) {
    throw new Error(
      `mcp_registered_tools: DEPRECATED_MCP_TOOL_NAMES parsed to ZERO names — the literal's shape ` +
      `has drifted. Refusing to fall back to an ungated tool set.`
    )
  }
  return names
}
