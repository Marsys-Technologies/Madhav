/**
 * MIGRATION NUMBER GUARD — cross-directory duplicate detector.
 *
 * SAMĀPTI lane B-MIGGUARD · brief v2.0 §4.4 (MIG-1) · protocol doc:
 * `00_ARCHITECTURE/MIGRATION_AND_MERGE_PROTOCOL_v1_0.md`.
 *
 * ── WHY THIS EXISTS ────────────────────────────────────────────────────────────
 * The repo has TWO migration directories that share ONE numeric sequence:
 *
 *   platform/migrations/            — the legacy sequence (README: "historical continuity only")
 *   platform/supabase/migrations/   — the active sequence (README: "all new migrations go here")
 *
 * `platform/scripts/migrate.ts` reads BOTH (`collectMigrationFiles`), concatenates them and
 * sorts by filename, then skips anything whose FILENAME is already in `_migrations_applied`.
 * So the number in the filename is not a key of anything — it is a human coordination token,
 * and nothing enforced it. Consequence, observed in git history:
 *
 *   467  claimed twice on two branches at once —
 *          f7160b5c  platform/supabase/migrations/467_pariprashna_canonical_message_parts.sql  (PB-2)
 *          455033ed  platform/migrations/467_asset_throughput_incomplete_state.sql             (SATYA-DĪPA)
 *        resolved only by a manual renumber (75a5d9e6, "renumber migration 467→474 after rebase")
 *        which left the file's own header comment still reading "Migration 467".
 *
 * A session that reads only ONE directory computes a "free" number that is already taken in the
 * other. This guard makes that computation a CI failure instead of a merge-time surprise.
 *
 * ── WHAT THIS GUARD ENFORCES (hard failures) ───────────────────────────────────
 *   E1  IDENTICAL FILENAME in both directories.
 *       Genuinely dangerous, not merely confusing: `runMigrations` keys `_migrations_applied`
 *       on the bare filename, so the second copy is SILENTLY SKIPPED — its SQL never runs and
 *       nothing reports a problem. Zero occurrences today; never allowlisted.
 *
 *   E2  DUPLICATE NUMBER (same leading integer, different filenames) that is NOT in the frozen
 *       baseline `migration_number_legacy_duplicates.json`. This is the 467 class. Detected
 *       across BOTH directories AND within each directory.
 *
 *   E3  A NEW FILE ADDED TO A BASELINED OR DISCLOSED GROUP. The baseline freezes exact file
 *       lists, not bare numbers, so a legacy collision cannot be used as cover for a new one.
 *
 *   E4  AN INCOMPLETE `disclosed_additions` ENTRY (missing owner/landed_at/disclosed_via/
 *       fixed_by_samapti/files). Same discipline as `schema_validator.py`'s `known_residuals`
 *       whitelist: exit-clean iff ITEMIZED. A bare or partial entry is treated as UNDISCLOSED,
 *       not as a partial pass — see DisclosedAddition's docstring below.
 *
 * ── DISCLOSED (not fixed) COLLISIONS — Dvārapāla RULING 70 ─────────────────────
 * The frozen baseline (`legacy_duplicate_groups`) is deliberately immutable — it is the exact set
 * that existed when this guard was introduced, and MUST NOT be hand-edited to silence a new
 * collision (that is the erosion the freeze exists to prevent). But a collision CAN still land
 * after the freeze, from a concurrent campaign this one does not own (RULING 70's own case: two
 * ṢAḌ-DARŚANA files both claimed migration 484 while B-MIGGUARD was in flight). Hard-failing
 * B-MIGGUARD's own PR on a bug it does not own is wrong; silently widening the baseline is
 * exactly the erosion the freeze exists to prevent. The third option — same one this codebase
 * already uses for `schema_validator`/`drift_detector`'s `known_residuals` whitelist — is a
 * SEPARATE, itemized `disclosed_additions` block: one entry per number, naming the files, the
 * owning campaign, the date it landed, the ruling that disclosed it, and whether SAMĀPTI has
 * since fixed it. See the `DisclosedAddition` interface for the required fields.
 *
 * ── WHAT THIS GUARD DOES *NOT* ENFORCE (stated so it cannot overclaim — CLAUDE.md §N.8) ──
 *   • It does NOT check that a migration is idempotent, reversible, or correct SQL.
 *   • It does NOT check that a migration was applied in production (that is SAṂGATI §8.5).
 *   • Header-number mismatch (`-- Migration 467:` inside `474_*.sql`) is reported as an
 *     ADVISORY WARNING ONLY and never fails CI. This is a standing constraint, not an oversight:
 *     **Dvārapāla RULING 44** requires it to stay warn-only until the 17-file backlog is cleared,
 *     because 17 pre-existing mismatches exist on `main` that this campaign did not create — a
 *     blocking check would turn `main` red on merge and read exactly like a regression this PR
 *     introduced. The warning is real output from a real full-file parse; it is not a silent pass.
 *     Full register: `00_ARCHITECTURE/MIGRATION_AND_MERGE_PROTOCOL_v1_0.md` §3.1.
 *   • Unnumbered `.sql` files (27 in platform/migrations/: `brahma_*`, `ws2_*`, `v13_*`) are
 *     outside the numeric sequence and are ignored entirely by the duplicate checks.
 *
 * ── USAGE ──────────────────────────────────────────────────────────────────────
 *   npm run guard:migration-numbers      # check; exit 1 on any hard failure
 *   npm run migration:next               # print the next allocatable number (max+1 across BOTH)
 *   tsx scripts/ci/migration_number_guard.ts --json
 */

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename_ = fileURLToPath(import.meta.url)
const __dirname_ = path.dirname(__filename_)

/** Directories that share the single migration number sequence, repo-root-relative. */
export const MIGRATION_DIRS = ['platform/migrations', 'platform/supabase/migrations'] as const

export interface MigrationEntry {
  /** repo-root-relative path, e.g. `platform/supabase/migrations/473_bg_sky_calendar.sql` */
  relPath: string
  dir: string
  filename: string
  /** leading integer of the filename (`0001_x.sql` → 1) */
  number: number
}

/**
 * A duplicate-number group discovered AFTER the baseline was frozen, disclosed rather than fixed.
 * Same discipline as `schema_validator.py`'s `known_residuals` whitelist (Dvārapāla RULING 70):
 * exit-clean iff ITEMIZED — every field below is required, or the entry does not count as
 * disclosed and the guard fails exactly as if it were never listed at all. This is what makes
 * `disclosed_additions` categorically different from silently widening `legacy_duplicate_groups`
 * by hand: a bare filename list would be indistinguishable from tampering; a complete record
 * with an owner, a date, and a named ruling is not.
 */
export interface DisclosedAddition {
  /** repo-root-relative paths claiming this number — must match the ACTUAL colliding set exactly. */
  files: string[]
  /** the campaign/lane that landed the collision (never "SAMĀPTI" for one this lane didn't create). */
  owner: string
  /** ISO date the collision landed on `main`. */
  landed_at: string
  /** where this was ruled/disclosed — a ledger ruling ID, not a vague "known issue". */
  disclosed_via: string
  /** true only once a future session has actually renumbered one of the files. */
  fixed_by_samapti: boolean
}

export interface Baseline {
  frozen_at?: string
  frozen_at_commit?: string
  legacy_duplicate_groups: Record<string, string[]>
  /** Post-freeze collisions, itemized/dated/attributed per DisclosedAddition — see its docstring. */
  disclosed_additions?: Record<string, DisclosedAddition>
}

export interface GuardResult {
  errors: string[]
  warnings: string[]
  entries: MigrationEntry[]
  maxNumber: number
  nextNumber: number
  duplicateGroups: Record<number, string[]>
}

/** Repo root, derived from this file's location (`<root>/platform/scripts/ci/`). */
export function repoRootFromHere(): string {
  return path.resolve(__dirname_, '..', '..', '..')
}

/**
 * `0001_brahma_baseline.sql` → 1 · `473_bg_sky_calendar.sql` → 473 · `brahma_kala.sql` → null
 *
 * The optional single-letter suffix is deliberate, not incidental. Two files on `main` use it —
 * `platform/migrations/346a_drop_legacy_mimamsa.sql` and
 * `platform/supabase/migrations/0000b_seed_legacy_v2.sql` — and `346` is ALREADY a duplicate
 * group (`346_mimamsa_kula.sql` + `346_fix_kala_chart_fk.sql`). A naive `^(\d+)[_-]` regex drops
 * `346a` out of the sequence entirely, which would leave `474a_anything.sql` as a trivial way to
 * walk straight past this guard. `346a` is a claim on 346 and is scored as one.
 */
export function parseMigrationNumber(filename: string): number | null {
  const m = /^(\d+)[a-z]?[_-]/i.exec(filename)
  if (!m) return null
  return parseInt(m[1], 10)
}

/**
 * Collect every NUMBERED top-level `.sql` file from both directories.
 * Non-recursive on purpose: `_archive/` and `__tests__/` are historical/support, not sequence
 * members, and must not be able to claim or block a number.
 */
export function collectNumberedMigrations(
  repoRoot: string,
  dirs: readonly string[] = MIGRATION_DIRS
): MigrationEntry[] {
  const out: MigrationEntry[] = []
  for (const dir of dirs) {
    const abs = path.join(repoRoot, dir)
    if (!fs.existsSync(abs)) continue
    for (const filename of fs.readdirSync(abs).sort()) {
      if (!filename.endsWith('.sql')) continue
      if (!fs.statSync(path.join(abs, filename)).isFile()) continue
      const number = parseMigrationNumber(filename)
      if (number === null) continue
      out.push({ relPath: `${dir}/${filename}`, dir, filename, number })
    }
  }
  return out
}

/**
 * THE CORRECTED ALLOCATION RULE (brief v2.0 §1, CONDUCTOR_PROMPT §5):
 * `max(highest in platform/migrations/, highest in platform/supabase/migrations/) + 1`.
 * Reading only one directory is the defect this whole lane exists to kill.
 */
export function computeNextMigrationNumber(entries: MigrationEntry[]): number {
  if (entries.length === 0) return 1
  return Math.max(...entries.map(e => e.number)) + 1
}

/**
 * ADVISORY ONLY — never contributes to `errors`. See the file header for why, and
 * `00_ARCHITECTURE/MIGRATION_AND_MERGE_PROTOCOL_v1_0.md` §3.1 for the full 17-row register.
 *
 * Scans the WHOLE file, not a fixed prefix. A 5-line window was the first implementation and it
 * under-reported: `227_ga_structural_floor_update.sql` declares its header at line 24 and
 * `237_drop_signal_type_registry.sql` at line 10, so a prefix scan found 15 of the 17 real
 * mismatches. An advisory that silently under-counts is worse than none — it invites the reader
 * to treat the list as complete.
 *
 * Matches only the DECLARATION form `-- Migration <N>` anchored at the start of a comment line.
 * Prose references are deliberately NOT matched: `183_bg_texts_and_text_dependent_floors.sql`
 * says "never set by migration 174 or 179" in running text and is NOT a mismatch — a looser grep
 * scores it as one.
 */
function headerNumberMismatch(repoRoot: string, e: MigrationEntry): string | null {
  let text: string
  try {
    text = fs.readFileSync(path.join(repoRoot, e.relPath), 'utf8')
  } catch {
    return null
  }
  const m = /^[ \t]*--[ \t]*Migration[ \t]+0*(\d+)\b/im.exec(text)
  if (!m) return null
  const declared = parseInt(m[1], 10)
  if (declared === e.number) return null
  return `${e.relPath}: filename says ${e.number} but its header comment says "Migration ${declared}"`
}

export function loadBaseline(repoRoot: string): Baseline {
  const p = path.join(repoRoot, 'platform/scripts/ci/migration_number_legacy_duplicates.json')
  return JSON.parse(fs.readFileSync(p, 'utf8')) as Baseline
}

export function checkMigrationNumbers(
  entries: MigrationEntry[],
  baseline: Baseline,
  opts: { repoRoot?: string } = {}
): GuardResult {
  const errors: string[] = []
  const warnings: string[] = []

  // ── E1 — identical filename present in more than one directory ──────────────
  const byFilename = new Map<string, MigrationEntry[]>()
  for (const e of entries) {
    const list = byFilename.get(e.filename) ?? []
    list.push(e)
    byFilename.set(e.filename, list)
  }
  for (const [filename, group] of [...byFilename].sort()) {
    if (group.length > 1) {
      errors.push(
        `[E1 SILENT-SKIP] filename "${filename}" exists in ${group.length} directories ` +
          `(${group.map(g => g.dir).join(', ')}). migrate.ts keys _migrations_applied on the bare ` +
          `filename, so only ONE of these will ever execute and the rest are skipped without a ` +
          `warning. Rename one of them before merge.`
      )
    }
  }

  // ── E2/E3 — duplicate numbers across BOTH directories, against the frozen baseline ──
  const byNumber = new Map<number, MigrationEntry[]>()
  for (const e of entries) {
    const list = byNumber.get(e.number) ?? []
    list.push(e)
    byNumber.set(e.number, list)
  }

  const duplicateGroups: Record<number, string[]> = {}
  for (const [number, group] of [...byNumber].sort((a, b) => a[0] - b[0])) {
    if (group.length < 2) continue
    const paths = group.map(g => g.relPath).sort()
    duplicateGroups[number] = paths

    const key = String(number)
    const legacyFiles = baseline.legacy_duplicate_groups[key]
    const disclosed = baseline.disclosed_additions?.[key]

    if (!legacyFiles && !disclosed) {
      errors.push(
        `[E2 NEW-COLLISION] migration number ${number} is claimed ${group.length} times:\n` +
          paths.map(p => `      - ${p}`).join('\n') +
          `\n      This number is NOT in the frozen legacy baseline. Renumber the NEW file to ` +
          `${computeNextMigrationNumber(entries)} — max() across BOTH directories, per ` +
          `00_ARCHITECTURE/MIGRATION_AND_MERGE_PROTOCOL_v1_0.md §3. Update the file's internal ` +
          `header comment to match.`
      )
      continue
    }

    // ── disclosed_additions path — RULING 70: exit-clean iff ITEMIZED, never a blanket pass ──
    // Same mechanism as schema_validator.py's known_residuals whitelist: an entry that is present
    // but missing a required field is treated as UNDISCLOSED, not as a partial pass.
    if (disclosed && !legacyFiles) {
      const missing: string[] = []
      if (!disclosed.owner) missing.push('owner')
      if (!disclosed.landed_at) missing.push('landed_at')
      if (!disclosed.disclosed_via) missing.push('disclosed_via')
      if (typeof disclosed.fixed_by_samapti !== 'boolean') missing.push('fixed_by_samapti')
      if (!Array.isArray(disclosed.files) || disclosed.files.length === 0) missing.push('files')

      if (missing.length > 0) {
        errors.push(
          `[E4 INCOMPLETE-DISCLOSURE] migration number ${number} is listed in disclosed_additions ` +
            `but is missing required field(s): ${missing.join(', ')}. An itemized disclosure needs ` +
            `owner + landed_at + disclosed_via + fixed_by_samapti + files — an incomplete entry is ` +
            `treated as UNDISCLOSED (same as if it were never listed), never a partial pass.`
        )
        continue
      }

      const disclosedSet = new Set(disclosed.files)
      const added = paths.filter(p => !disclosedSet.has(p))
      if (added.length > 0) {
        errors.push(
          `[E3 WIDENED-DISCLOSED-GROUP] migration number ${number} is a disclosed collision ` +
            `(owner: ${disclosed.owner}, via ${disclosed.disclosed_via}), but these files are new ` +
            `to it:\n` +
            added.map(p => `      - ${p}`).join('\n') +
            `\n      A disclosed collision is not a licence to add another. Renumber to ` +
            `${computeNextMigrationNumber(entries)}. Do not edit the baseline file to silence this.`
        )
      }
      warnings.push(
        `[disclosed-residual] migration number ${number}: owner ${disclosed.owner}, landed ` +
          `${disclosed.landed_at}, disclosed via ${disclosed.disclosed_via}, fixed by SAMĀPTI: ` +
          `${disclosed.fixed_by_samapti}. See ${disclosed.disclosed_via}.`
      )
      continue
    }

    // ── legacy_duplicate_groups path — the original frozen-at-instrument-creation baseline ──
    const baselineSet = new Set(legacyFiles)
    const added = paths.filter(p => !baselineSet.has(p))
    if (added.length > 0) {
      errors.push(
        `[E3 WIDENED-LEGACY-GROUP] migration number ${number} is a KNOWN legacy collision, but ` +
          `these files are new to it:\n` +
          added.map(p => `      - ${p}`).join('\n') +
          `\n      A pre-existing collision is not a licence to add another. Renumber to ` +
          `${computeNextMigrationNumber(entries)}. Do not edit the baseline file to silence this.`
      )
    }
    const removed = (legacyFiles ?? []).filter(p => !paths.includes(p))
    if (removed.length > 0) {
      warnings.push(
        `[baseline drift] legacy group ${number} no longer contains: ${removed.join(', ')} ` +
          `(renamed or deleted). Harmless; the baseline entry may be pruned in a governance pass.`
      )
    }
  }

  // Baselined/disclosed groups that fully disappeared — advisory, never fatal.
  for (const key of Object.keys(baseline.legacy_duplicate_groups)) {
    if (!(Number(key) in duplicateGroups)) {
      warnings.push(`[baseline drift] legacy duplicate group ${key} is fully resolved — entry is now stale.`)
    }
  }
  for (const key of Object.keys(baseline.disclosed_additions ?? {})) {
    if (!(Number(key) in duplicateGroups)) {
      warnings.push(`[baseline drift] disclosed group ${key} is fully resolved — entry is now stale.`)
    }
  }

  // ── ADVISORY — header/filename number mismatch ───────────────────────────────
  if (opts.repoRoot) {
    for (const e of entries) {
      const msg = headerNumberMismatch(opts.repoRoot, e)
      if (msg) warnings.push(`[header-mismatch · ADVISORY, non-fatal] ${msg}`)
    }
  }

  const maxNumber = entries.length ? Math.max(...entries.map(e => e.number)) : 0
  return {
    errors,
    warnings,
    entries,
    maxNumber,
    nextNumber: computeNextMigrationNumber(entries),
    duplicateGroups,
  }
}

/** Run the guard against a real checkout. */
export function runGuard(repoRoot: string): GuardResult {
  const entries = collectNumberedMigrations(repoRoot)
  return checkMigrationNumbers(entries, loadBaseline(repoRoot), { repoRoot })
}

// ── CLI ────────────────────────────────────────────────────────────────────────
function main(): void {
  const argv = process.argv.slice(2)
  const repoRoot = repoRootFromHere()
  const result = runGuard(repoRoot)

  if (argv.includes('--next')) {
    // Machine-readable single line — the Conductor's merge-time allocation call (§5).
    process.stdout.write(`${result.nextNumber}\n`)
    return
  }

  if (argv.includes('--json')) {
    process.stdout.write(JSON.stringify(result, null, 2) + '\n')
    process.exit(result.errors.length > 0 ? 1 : 0)
  }

  const perDir = MIGRATION_DIRS.map(d => {
    const nums = result.entries.filter(e => e.dir === d).map(e => e.number)
    return `  ${d}: ${nums.length} numbered .sql, highest ${nums.length ? Math.max(...nums) : '—'}`
  }).join('\n')

  const baselineForPrint = loadBaseline(repoRoot)
  process.stdout.write(
    `MIGRATION NUMBER GUARD (cross-directory)\n${perDir}\n` +
      `  next allocatable number (max across BOTH + 1): ${result.nextNumber}\n` +
      `  duplicate-number groups present: ${Object.keys(result.duplicateGroups).length} ` +
      `(frozen legacy baseline: ${Object.keys(baselineForPrint.legacy_duplicate_groups).length} + ` +
      `disclosed additions: ${Object.keys(baselineForPrint.disclosed_additions ?? {}).length})\n\n`
  )

  for (const w of result.warnings) process.stdout.write(`WARN  ${w}\n`)
  if (result.warnings.length) process.stdout.write('\n')

  if (result.errors.length === 0) {
    process.stdout.write('PASS — no new migration-number collision.\n')
    return
  }
  for (const e of result.errors) process.stderr.write(`FAIL  ${e}\n`)
  process.stderr.write(
    `\n${result.errors.length} migration-number violation(s). ` +
      `See 00_ARCHITECTURE/MIGRATION_AND_MERGE_PROTOCOL_v1_0.md §3.\n`
  )
  process.exit(1)
}

// Run only as the process entrypoint (`tsx scripts/ci/migration_number_guard.ts`) — NOT when
// migration_number_guard.test.ts imports the pure functions. Same idiom as
// scripts/generate_vidhi_registry_mirror.ts.
const isEntrypoint = (() => {
  try {
    const argv1 = process.argv[1] ?? ''
    return (
      import.meta.url === `file://${argv1}` || import.meta.url === `file://${path.resolve(argv1)}`
    )
  } catch {
    return false
  }
})()

if (isEntrypoint) main()
