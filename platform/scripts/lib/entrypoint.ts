/**
 * `scripts/lib/entrypoint.ts` — THE one shared `isDirectEntrypoint` implementation.
 *
 * ══════════════════════════════════════════════════════════════════════════════════════════
 * WHY THIS FILE EXISTS
 * ══════════════════════════════════════════════════════════════════════════════════════════
 *
 * Nirmāṇa M0-T60 filed finding **F-2**: `isDirectEntrypoint` existed in THREE production
 * copies with no detector asserting the bodies agree. M0-T65's wave-1 repair took that to
 * EIGHT, because ruling D-74 part 5 mandated the idiom and ruling D-9 forbids importing from
 * `scripts/migrate.ts`. Wave 2 (the remaining 53 tier-1 files) would have taken it to ~61.
 *
 * Ruling **D-67 part 3** granted F-2 and F-5 together: *"ONE SHARED IMPLEMENTATION PLUS ONE
 * CI GUARD THAT FAILS ON AN UNGUARDED TOP-LEVEL main(). Three copies of a security-relevant
 * predicate that can silently diverge is a defect on its own terms."* This module is the
 * first half; `scripts/governance/check_entrypoint_guard_ratchet.py` is the second.
 *
 * ══════════════════════════════════════════════════════════════════════════════════════════
 * WHY IMPORTING THIS IS SAFE WHERE IMPORTING `migrate.ts` IS NOT (ruling D-9)
 * ══════════════════════════════════════════════════════════════════════════════════════════
 *
 * D-9's standing instruction is not "never import" — it is "never acquire a module graph you
 * did not have". `migrate.ts` is a program: importing it used to apply every pending migration
 * to production. THIS module is a leaf:
 *
 *   - its ONLY imports are the three node builtins (`node:fs`, `node:path`, `node:url`) that
 *     every one of the eight callers already imported for its own private copy;
 *   - it has NO module-scope effect: no connection, no credential read, no filesystem write,
 *     no network call, no `process.exit`, no `main()`;
 *   - it exports one pure function and nothing else.
 *
 * So an importer's module graph gains exactly zero packages and exactly zero side effects.
 * That property is not a claim — it is asserted by
 * `scripts/__tests__/shared_entrypoint_module.test.ts` (§1) and by the ratchet guard's
 * `--canonical` divergence check, both of which fail if it ever stops holding.
 *
 * ══════════════════════════════════════════════════════════════════════════════════════════
 * THE CONTRACT (Nirmāṇa M0-T60 / `scripts/audit/A3_env_matrix.md` Addendum A3.4, rule 5)
 * ══════════════════════════════════════════════════════════════════════════════════════════
 *
 * This is the `isDirectEntrypoint` contract, NOT the `IMPORT_ONLY !== '1'` contract the two CI
 * gates use (M0-T50 / ruling D-49). The two answer opposite hazards and are not
 * interchangeable:
 *
 *   - A CI GATE's hazard is FAILING to run — a gate that silently does not execute reports
 *     success for a defect. Its safe default is therefore **RUN**, and `IMPORT_ONLY` is the
 *     right shape: an explicit opt-OUT.
 *   - A MIGRATOR's, a SEEDER's or a CREDENTIAL SCRIPT's hazard is RUNNING when it should not.
 *     Its safe default is **DO NOT RUN**, and this predicate is the right shape: run only on
 *     proof that this module IS the entrypoint.
 *
 * Do not "unify" the two. They are different answers to different questions and the campaign
 * has already paid for confusing them once.
 */

import { realpathSync } from 'node:fs'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

/**
 * True when this module is the process entrypoint — i.e. the runtime was told to execute
 * THIS file — and false when it was reached by an `import`.
 *
 * Compares the module's own URL against `process.argv[1]`, the path the runtime was told to
 * execute. Both sides are normalised through `realpathSync` where possible, so a symlinked
 * checkout, a `./`-prefixed spelling, or a `/tmp` → `/private/tmp` style realpath difference
 * does not make a direct run look like an import.
 *
 * ANY failure to resolve either side answers `false`. The safe direction is "assume imported",
 * because a wrongly-false answer makes an explicit `npx tsx <file>` exit having done nothing —
 * loud, recoverable and repeatable — while a wrongly-true answer performs the caller's
 * destructive work as an import side effect, inside a process that never asked for it.
 *
 * @param moduleUrl the caller's `import.meta.url`
 * @param argv1     the caller's `process.argv[1]` (may be `undefined` under `node --eval`)
 */
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
