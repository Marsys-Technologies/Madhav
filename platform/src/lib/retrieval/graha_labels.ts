/**
 * graha_labels.ts — CLIENT-SAFE graha label/code vocabulary, extracted from
 * address_resolver.ts.
 * =============================================================================
 * WHY THIS FILE EXISTS: address_resolver.ts mixes pure, in-memory lookup data
 * (this module's contents) with DB-querying resolution functions that import
 * `@/lib/db/client`, which itself begins with `import 'server-only'` — a
 * marker package that throws at build time the instant it is bundled into a
 * Client Component. Because `address_resolver.ts` is ONE FILE, importing
 * ANYTHING from it — even a pure constant — pulls that `server-only` marker
 * into whatever bundle reaches it. A `'use client'` component that only
 * needed `GRAHA_CODE_TO_NAME`/`grahaCodeOf` (zero DB access) broke the
 * production build this way (`QueryDNAPanel.tsx`, ADHIṢṬHĀNA campaign,
 * second GATE-EXECUTOR PARK, 2026-08-08).
 *
 * This module is the client-safe subset: the graha code/name/alias
 * normalization vocabulary plus the one pure function that resolves it —
 * zero I/O, zero imports of `@/lib/db/client` or any other server-only
 * module. `address_resolver.ts` imports from here and re-exports the same
 * names (`export { AddressResolutionError, GRAHA_CODE_TO_NAME, grahaCodeOf }
 * from './graha_labels'`), so every existing `address_resolver.X` call site
 * (server-side; DB-touching resolution still lives there) is unaffected —
 * moved, not copied, same "SSoT by promotion" discipline as Lane A2's own
 * Python-side `norm_graha` promotion to `brahmagyan/graha_vocabulary.py`.
 *
 * RULE FOR FUTURE CALLERS: a CLIENT COMPONENT that only needs graha
 * label/code lookup must import FROM THIS MODULE DIRECTLY
 * (`@/lib/retrieval/graha_labels`), never from `@/lib/retrieval/address_resolver`
 * — importing anything from address_resolver.ts, even a re-exported pure
 * name, still pulls in its top-level `import { query } from '@/lib/db/client'`
 * and poisons the client bundle.
 */

/** Thrown by `grahaCodeOf` (and, more broadly, by address_resolver.ts's own
 *  DB-touching resolution functions — it is the one shared address-resolution
 *  error type for the whole module, defined here because this is where the
 *  first/simplest throw site, `grahaCodeOf`, lives). No I/O; a plain `Error`
 *  subclass is pure. */
export class AddressResolutionError extends Error {}

/** graha_position / karaka_chara_position fact_subject code ↔ classical graha name. */
export const GRAHA_CODE_TO_NAME: Record<string, string> = {
  SUN: 'Sun',
  MOON: 'Moon',
  MAR: 'Mars',
  MER: 'Mercury',
  JUP: 'Jupiter',
  VEN: 'Venus',
  SAT: 'Saturn',
  RAH_MEAN: 'Rahu',
  KET_MEAN: 'Ketu',
}

const NAME_TO_GRAHA_CODE: Record<string, string> = Object.fromEntries(
  Object.entries(GRAHA_CODE_TO_NAME).map(([code, name]) => [name.toLowerCase(), code]),
)
// Common shorthand aliases seen in classical/DSL usage, plus the standard Sanskrit graha
// names (undisputed across every Vedic paradigm — BPHS nomenclature, safe to hardcode per
// B.10). Sanskrit aliases folded in at R5 W1 Ring-1 reconciliation (JL-010) from the
// chart_query lane's now-retired inline stopgap (`chart_query_about.ts`), which supported
// these but this canonical module did not yet — single-source mandate (design §19) means the
// alias set lives here, not duplicated in a second table.
const GRAHA_ALIASES: Record<string, string> = {
  su: 'SUN', mo: 'MOON', ma: 'MAR', me: 'MER', ju: 'JUP', ve: 'VEN', sa: 'SAT',
  ra: 'RAH_MEAN', ke: 'KET_MEAN',
  rahu: 'RAH_MEAN', ketu: 'KET_MEAN', mars: 'MAR', mercury: 'MER',
  jupiter: 'JUP', venus: 'VEN', saturn: 'SAT', sun: 'SUN', moon: 'MOON',
  // Sanskrit names (classical, undisputed):
  surya: 'SUN', chandra: 'MOON', mangala: 'MAR', kuja: 'MAR', budha: 'MER',
  guru: 'JUP', brihaspati: 'JUP', shukra: 'VEN', shani: 'SAT',
  // ADHIṢṬHĀNA Lane A2: bare "rah"/"ket" — already-recognized aliases in the
  // Python SSoT's own alias table (brahmagyan/graha_vocabulary._GRAHA_ALIASES:
  // "RAH"->RAH_MEAN, "KET"->KET_MEAN) that this TS module did not yet carry;
  // added for cross-language parity (MASTER_PLAN_v1_0.md §3 Rung P1) and to
  // let identifier_format.ts retire its own independent copy of these two
  // aliases into this SSoT rather than duplicating them.
  rah: 'RAH_MEAN', ket: 'KET_MEAN',
}

/** Normalize a graha name/alias/code (English, Sanskrit, or 2-letter shorthand) to its
 *  canonical fact_subject code (e.g. "Saturn" | "shani" | "SAT" -> "SAT"). Throws
 *  `AddressResolutionError` on an unrecognized name (B.10 — no silent fallback). */
export function grahaCodeOf(input: string): string {
  const k = input.trim().toLowerCase()
  if (NAME_TO_GRAHA_CODE[k]) return NAME_TO_GRAHA_CODE[k]
  if (GRAHA_ALIASES[k]) return GRAHA_ALIASES[k]
  const upper = input.trim().toUpperCase()
  if (GRAHA_CODE_TO_NAME[upper]) return upper
  throw new AddressResolutionError(`Unknown graha "${input}" — not in GRAHA_CODE_TO_NAME/aliases.`)
}
