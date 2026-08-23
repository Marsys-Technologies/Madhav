/**
 * A HARMLESS STAND-IN for the five scripts repaired by Nirmāṇa M0-T65.
 *
 * WHY IT EXISTS. Ruling D-74 parts 2 and 3 forbid EXECUTING any of those five files — not to
 * verify, not "just the import", not with a stub env, not in a sandbox. They shell out for
 * secrets, `DELETE FROM charts`, grant `role='super_admin'`, mint a live super-admin session
 * cookie, and reset a live account password. So the behavioural half of the proof is run here
 * instead: this module carries the IDENTICAL guard idiom and the IDENTICAL `isDirectEntrypoint`
 * body, in the same directory tree, under the same `tsx` resolution — and its `main()` does
 * nothing but print a marker and exit.
 *
 * WHAT IT PROVES AND WHAT IT DOES NOT. It proves the idiom resolves correctly under this repo's
 * runtime for a `platform/scripts/**` ESM `.ts` file: direct run enters `main()` (including a
 * `./`-prefixed spelling and with `NODE_ENV=test` set), a side-effect import does not, and the
 * import does not have its exit hijacked. It does NOT prove anything about the five real files'
 * own runtime behaviour; that half is covered structurally, by asserting their guard text and
 * predicate bodies rather than by running them. `destructive_entrypoint_guards.test.ts` states
 * that split explicitly.
 *
 * `.fixture.ts`, not `.test.ts`, so vitest does not collect it as a suite.
 */
import { realpathSync } from 'node:fs'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

/** The observable. Printed only if `main()` is entered. */
export const STANDIN_MAIN_MARKER = 'STANDIN_MAIN_RAN'

/** Exit code `main()` uses, so an import that wrongly ran it is visible in the exit status too. */
export const STANDIN_MAIN_EXIT = 7

function main(): void {
  console.log(STANDIN_MAIN_MARKER)
  process.exit(STANDIN_MAIN_EXIT)
}

// ─────────────────────────────────────────────────────────────────────────────
// Byte-identical to the body in `scripts/migrate.ts`, `scripts/seed/asset_registry_seed.ts`,
// `scripts/pariprashna/ledger_writer_worker.ts` and the five files repaired by M0-T65.
// `destructive_entrypoint_guards.test.ts` asserts that equality rather than assuming it.
// ─────────────────────────────────────────────────────────────────────────────
export function isDirectEntrypoint(moduleUrl: string, argv1: string | undefined): boolean {
  if (!argv1) return false
  let modulePath: string
  try {
    modulePath = fileURLToPath(moduleUrl)
  } catch {
    return false
  }
  const entryPath = resolve(argv1)
  if (modulePath === entryPath) return true
  try {
    return realpathSync(modulePath) === realpathSync(entryPath)
  } catch {
    return false
  }
}

if (isDirectEntrypoint(import.meta.url, process.argv[1])) {
  main()
}
