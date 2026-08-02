/**
 * _kala_tool_registration.ts — static, mechanical check of whether each of the eight
 * ṢAḌ-DARŚANA kala_* views/capabilities (SHAD_DARSHANA_BRIEF_v2_0.md §0/§2) is registered
 * yet on `platform-mcp/src/tools/**`.
 *
 * WHY THIS EXISTS: this lane (shad-darshana-ci-skeletons) builds ONLY the CI skeletons —
 * the eight tool facades themselves (`tools/kala_views/*.ts`) are built by sibling
 * `.worktrees/shad-darshana-*` lanes landing concurrently, and are very likely NOT merged
 * yet when this lane's PR opens. Every gate script in this directory that would otherwise
 * hard-fail on "tool not found" instead calls `isKalaToolRegistered()` first and reports an
 * honest SKIPPED result naming the missing tool — never a fabricated PASS, and never a
 * FAIL for something genuinely out of this lane's control (CLAUDE.md §N.7 Earned-Signal
 * Principle: a check with no real detector behind it is null, not green — the inverse is
 * also true, a check that fails for a reason outside its own claim is a false signal too).
 *
 * Read-only source-text scan (grep), same pattern and same cross-manifest-isolation
 * rationale as `platform/scripts/census/elev_gates/_tool_enumeration.ts`.
 *
 * DETECTOR FIX (W2, lane w2-specificity-hard, 2026-08-02): the original detector only
 * matched a STRING LITERAL adjacent to `server.tool(` / `regAlias(server,`. Four of the
 * eight kala_* views (now, ahead, priority, explain) register via an identifier —
 * `const TOOL_NAME = 'kala_now_get'` … `server.tool(TOOL_NAME, …)` — and were reported
 * unregistered while live in production (the false negative that retired CI items 1/3/6;
 * see CI_EFFICIENCY_AUDIT_v1_0.md §4.8 and the workflow header). The detector now ALSO
 * resolves identifier registration by looking the identifier up among the same file's
 * `const NAME = '<string literal>'` declarations. Honest scope: resolution is same-file
 * only — an identifier imported from another module is NOT resolved and yields no
 * detection (never a fabricated one); no such cross-module registration exists under
 * platform-mcp/src/tools today, and if one appears the census reports it missing, which
 * is the honest-failure direction.
 *
 * TEST HOOK: `SHAD_DARSHANA_MCP_TOOLS_ROOT` overrides the scanned root, so the census
 * FAIL path is provable end-to-end (mirrors authority_basis_census_seed's own
 * MCP_TOOLS_ROOT repoint, the mutation proof recorded in the workflow header).
 */
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs'
import path from 'node:path'

// This file lives at platform/scripts/census/shad_darshana_gates/ — four levels up is
// platform/, five is the repo root.
const REPO_ROOT = path.join(__dirname, '..', '..', '..', '..')
export const MCP_TOOLS_ROOT = process.env['SHAD_DARSHANA_MCP_TOOLS_ROOT'] || path.join(REPO_ROOT, 'platform-mcp/src/tools')
export const REGISTRY_BRIDGE_PATH = path.join(MCP_TOOLS_ROOT, 'registry_bridge.ts')
export const KALA_VIEWS_ROOT = path.join(MCP_TOOLS_ROOT, 'kala_views')

/** The eight kala_* views/capabilities per brief §0.1 + §2 file map. */
export const SHAD_DARSHANA_EIGHT_TOOLS = [
  'kala_now_get',
  'kala_ahead_get',
  'kala_elect_get',
  'kala_story_get',
  'kala_priority_get',
  'kala_explain_get',
  'kala_upaya_get',
  'kala_ritual_get',
] as const

export type ShadDarshanaToolName = (typeof SHAD_DARSHANA_EIGHT_TOOLS)[number]

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
    let st
    try {
      st = statSync(full)
    } catch {
      continue
    }
    if (st.isDirectory()) walkTs(full, out)
    else if (entry.endsWith('.ts')) out.push(full)
  }
}

/** Every `.ts` file under platform-mcp/src/tools, read once (test files included —
 *  registration can legitimately be pinned by a *.test.ts too; we only care whether the
 *  string literal exists in a server.tool()/regAlias() call site anywhere). */
function listToolSourceFiles(): string[] {
  const files: string[] = []
  walkTs(MCP_TOOLS_ROOT, files)
  return files.sort()
}

/**
 * Extracts every statically-registered tool name from one source file's text.
 * Handles both registration shapes observed under platform-mcp/src/tools:
 *   - literal:    `server.tool('kala_elect_get', …)` / `regAlias(server, 'name', …)`
 *     (single- or multi-line — `\s*` crosses newlines);
 *   - identifier: `server.tool(TOOL_NAME, …)` / `regAlias(server, ALIAS_NAME, …)` where
 *     `const TOOL_NAME = 'kala_now_get'` is declared IN THE SAME FILE. An identifier with
 *     no same-file string-literal const is skipped — never fabricated into a detection.
 * Pure function (no fs) so the resolution logic is unit-testable in isolation.
 */
export function extractRegisteredToolNames(src: string): string[] {
  const constByIdent = new Map<string, string>()
  for (const m of src.matchAll(/\bconst\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*['"]([a-zA-Z0-9_]+)['"]/g)) {
    constByIdent.set(m[1]!, m[2]!)
  }
  const names = new Set<string>()
  for (const m of src.matchAll(/server\.tool\(\s*(?:['"]([a-zA-Z0-9_]+)['"]|([A-Za-z_$][A-Za-z0-9_$]*)\s*,)/g)) {
    if (m[1]) names.add(m[1])
    else if (m[2]) {
      const resolved = constByIdent.get(m[2])
      if (resolved) names.add(resolved)
    }
  }
  for (const m of src.matchAll(/\b(?:regAlias|globalAlias)\(\s*server,\s*(?:['"]([a-zA-Z0-9_]+)['"]|([A-Za-z_$][A-Za-z0-9_$]*)\s*,)/g)) {
    if (m[1]) names.add(m[1])
    else if (m[2]) {
      const resolved = constByIdent.get(m[2])
      if (resolved) names.add(resolved)
    }
  }
  return [...names]
}

/**
 * Returns, for each of the eight tools, whether it is statically found as a registered
 * tool name anywhere under platform-mcp/src/tools (literal OR same-file-const identifier
 * registration — see `extractRegisteredToolNames`), and which file(s) it was found in.
 */
export function collectShadDarshanaRegistration(): Record<ShadDarshanaToolName, string[]> {
  const byName: Record<string, string[]> = Object.fromEntries(SHAD_DARSHANA_EIGHT_TOOLS.map((n) => [n, []]))
  if (!existsSync(MCP_TOOLS_ROOT)) return byName as Record<ShadDarshanaToolName, string[]>
  for (const f of listToolSourceFiles()) {
    const src = readFileSync(f, 'utf-8')
    for (const name of extractRegisteredToolNames(src)) {
      if (name in byName && !byName[name]!.includes(f)) byName[name]!.push(f)
    }
  }
  return byName as Record<ShadDarshanaToolName, string[]>
}

/** True iff `toolName` is statically registered anywhere under platform-mcp/src/tools. */
export function isKalaToolRegistered(toolName: ShadDarshanaToolName, registration?: Record<ShadDarshanaToolName, string[]>): boolean {
  const reg = registration ?? collectShadDarshanaRegistration()
  return (reg[toolName]?.length ?? 0) > 0
}
