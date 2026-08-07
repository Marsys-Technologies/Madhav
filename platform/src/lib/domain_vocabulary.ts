/**
 * domain_vocabulary.ts — TS mirror of the canonical 13-domain vocabulary.
 *
 * SERVE-SIDE MIRROR. The single source of truth is the Python module
 * ``brahmagyan/domain_vocabulary.py``. This file must stay in exact parity;
 * ``tests/test_domain_vocabulary.py`` asserts member-for-member agreement.
 *
 * ZERO-IMPORT: this file must not import from any other project module so it
 * can be consumed by any layer without creating circular dependencies.
 *
 * SHABDA-SHUDDHI campaign, R7, 2026-08-07.
 */

/**
 * The canonical 13-domain vocabulary. Mirrors the DB CHECK constraints from
 * migration 386 (canonical_domain_normalization).
 */
export const CANONICAL_DOMAINS = [
  'career',
  'character',
  'education',
  'family',
  'general',
  'health',
  'progeny',
  'relationship',
  'residence',
  'spirituality',
  'transition',
  'travel',
  'wealth',
] as const;

export type CanonicalDomain = (typeof CANONICAL_DOMAINS)[number];

const CANONICAL_DOMAIN_SET: ReadonlySet<string> = new Set(CANONICAL_DOMAINS);

/**
 * Synonym mapping: legacy / alternate terms -> canonical domain.
 * Keys are lowercase. Every value is a member of CANONICAL_DOMAINS.
 */
export const DOMAIN_SYNONYMS: Readonly<Record<string, CanonicalDomain>> = {
  // wealth
  financial: 'wealth',
  finance: 'wealth',
  money: 'wealth',
  // spirituality
  spiritual: 'spirituality',
  dharma: 'spirituality',
  moksha: 'spirituality',
  // character
  psychological: 'character',
  psychology: 'character',
  mind: 'character',
  // relationship
  marriage: 'relationship',
  spouse: 'relationship',
  relationships: 'relationship',
  // progeny
  children: 'progeny',
  progeny_children: 'progeny',
  creativity: 'progeny',
  // education
  intellect: 'education',
  // residence
  property: 'residence',
  residential: 'residence',
  // travel
  foreign: 'travel',
};

/**
 * Return the canonical domain for a given input, applying synonym resolution.
 * Returns `fallback` if no candidate resolves.
 */
export function canonicalDomain(
  candidate: string | null | undefined,
  fallback: CanonicalDomain = 'general',
): CanonicalDomain {
  if (!candidate) return fallback;
  const cl = candidate.toLowerCase().trim();
  const resolved = DOMAIN_SYNONYMS[cl] ?? cl;
  return CANONICAL_DOMAIN_SET.has(resolved)
    ? (resolved as CanonicalDomain)
    : fallback;
}

/**
 * Check whether a string is a member of the canonical vocabulary.
 */
export function isCanonicalDomain(domain: string | null | undefined): domain is CanonicalDomain {
  return domain != null && CANONICAL_DOMAIN_SET.has(domain);
}
