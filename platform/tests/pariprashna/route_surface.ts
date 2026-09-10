/**
 * The Paripraśna reading route's SOURCE SURFACE — shared by the source-level
 * mount/contract guards.
 *
 * WHY THIS EXISTS (P0-C / RF-1, 2026-08-19)
 * ────────────────────────────────────────
 * Several guards in this suite are deliberately cheap source reads of the live
 * reading route: they exist to catch "a refactor silently orphaned the entry
 * point" — the exact failure that closed PB-3 SHIP-DEGRADED. They were written
 * when the whole pipeline lived in one 1,179-line `route.ts`.
 *
 * The RF-1 ports refactor moved that pipeline into typed stage modules under
 * `src/lib/pariprashna/pipeline/`, leaving `route.ts` as the composing shell.
 * The guards' QUESTION is unchanged — "is this wired into the live reading
 * route?" — so what changed is only WHERE the answer is written. Pointing them
 * at the shell alone would make them pass vacuously (the strings simply are not
 * there any more); deleting them would remove the detector. Both are the
 * anti-pattern §N.8 forbids. So they now read the whole surface: the shell plus
 * every stage module it composes.
 *
 * The surface is assembled from the route shell's OWN import list, not from a
 * hardcoded file list — a stage module that stops being imported by the route
 * drops out of the surface, and any guard that depended on its content goes RED.
 * That is the property the mount guards need: an orphaned stage is not a
 * silently-passing stage.
 */

import { readFileSync, readdirSync } from 'node:fs'
import path from 'node:path'

const PLATFORM_ROOT = path.resolve(__dirname, '..', '..')
export const ROUTE_SHELL_PATH = 'src/app/api/pariprashna/route.ts'
const PIPELINE_DIR = 'src/lib/pariprashna/pipeline'

function read(rel: string): string {
  return readFileSync(path.join(PLATFORM_ROOT, rel), 'utf8')
}

/** The route shell source, on its own. */
export function readRouteShell(): string {
  return read(ROUTE_SHELL_PATH)
}

/**
 * Stage modules REACHABLE from the route shell through pipeline imports —
 * the transitive closure, not just the shell's direct imports. `reading_parts`,
 * for instance, is imported by `synthesis_stage` and `persistence_stage` rather
 * than by the shell, and is unquestionably part of the live route.
 *
 * A module present on disk but reachable from nothing the shell composes is NOT
 * part of the surface: orphan it and any guard that depended on its content
 * goes red, which is precisely the PB-3 failure mode these guards exist for.
 */
export function pipelineModulesImportedByShell(): string[] {
  const onDisk = readdirSync(path.join(PLATFORM_ROOT, PIPELINE_DIR))
    .filter((f) => f.endsWith('.ts') && !f.endsWith('.test.ts'))
    .map((f) => f.replace(/\.ts$/, ''))

  const reachable = new Set<string>()
  const frontier: string[] = [readRouteShell()]
  while (frontier.length > 0) {
    const src = frontier.pop()!
    for (const mod of onDisk) {
      if (reachable.has(mod)) continue
      // Absolute alias (used by the shell) or sibling-relative (used between stages).
      if (src.includes(`@/lib/pariprashna/pipeline/${mod}`) || src.includes(`'./${mod}'`)) {
        reachable.add(mod)
        frontier.push(read(`${PIPELINE_DIR}/${mod}.ts`))
      }
    }
  }
  return [...reachable].sort()
}

/**
 * The full live-route source surface: the shell followed by every stage module
 * it composes, joined by a banner so per-file locality is preserved for
 * proximity assertions (a `try {` in one file can never "reach" a `catch` in
 * the next).
 */
export function readRouteSurface(): string {
  const parts = [`/* ==== ${ROUTE_SHELL_PATH} ==== */\n${readRouteShell()}`]
  for (const mod of pipelineModulesImportedByShell()) {
    const rel = `${PIPELINE_DIR}/${mod}.ts`
    parts.push(`/* ==== ${rel} ==== */\n${read(rel)}`)
  }
  return parts.join('\n/* ======================================== */\n')
}
