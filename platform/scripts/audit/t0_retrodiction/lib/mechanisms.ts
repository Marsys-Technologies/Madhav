/**
 * mechanisms.ts — significator definitions for the T-0 retrodiction-gate
 * harness (BRIEF_D3.md §F1 Lane T-0).
 *
 * LOSS / WINDFALL significators are taken directly from what
 * `ganita_vichara_get`/`judgment_query` actually serve on 482012f1 today
 * (verified live during harness build, 2026-07-17):
 *
 * - LOSS (checks (a)): the "8L-Mars→2H wealth-loss mechanism" named in
 *   BRIEF_D3 §F0 (D-2's DR-9 valence-root fix). `ganita_vichara_get(family=
 *   valence_pass, subject=MAR)` row id 81288/81304 (varga D1, link_kind=
 *   lord_aspects, target_house=2, actor_houses_lorded=[1,8]) is exactly
 *   this mechanism: Mars is 1st+8th lord (yogakaraka for this Aries lagna)
 *   aspecting the 2nd (dhana) bhava. Significator = Mars alone, per the
 *   brief's own naming of the mechanism ("8L-Mars").
 * - WINDFALL (checks (b)): `judgment_query(domain=wealth, v3)` serves
 *   `bearing_yogas` including `dhana_yoga_2_5_9_11` and
 *   `dhana_yoga_house_lords`, both firing on constituent_planets
 *   [venus, jupiter] in the 9th house. Significators = Venus + Jupiter.
 *
 * BLIND-BATTERY domain->lord map (check (c)) is drawn from
 * `ganita_dasha_lord_capability_get`'s `ratification_domains` field — a
 * servable-today, already-computed domain-to-karaka mapping (ga_vichara
 * varga_ratification, §N.5-compliant: this harness reads it, never
 * restates it). Verified live 2026-07-17 on 482012f1:
 *   wealth: Jupiter(1.0), Saturn(0.8), Venus(1.0)
 *   career: Saturn(0.8)
 *   health: Mercury(1.0)
 *   marriage: Venus(1.0)
 * `general` has no dedicated karaka in this table — Mars and Sun are its
 * dasha-lord-capability `ratification_domains:['general']` entries and are
 * used as the fallback pair for LEL categories with no domain match.
 */

export const LOSS_SIGNIFICATORS: Record<string, number> = { Mars: 1.0 }
export const WINDFALL_SIGNIFICATORS: Record<string, number> = { Venus: 1.0, Jupiter: 1.0 }

/** From ganita_dasha_lord_capability_get, live on 482012f1 (2026-07-17). Keyed by the tool's `judgment_query` domain vocabulary. */
export const DOMAIN_LORDS: Record<string, Record<string, number>> = {
  wealth: { Jupiter: 1.0, Saturn: 0.8, Venus: 1.0 },
  career: { Saturn: 0.8 },
  health: { Mercury: 1.0 },
  marriage: { Venus: 1.0 },
  general: { Mars: 1.0, Sun: 1.0 },
}

/**
 * Maps an LEL `category` (the corpus's own free vocabulary — career,
 * health, spiritual, relationship, family, loss, finance, creative,
 * psychological, travel, education, other, residential+travel) to the
 * closest `judgment_query`/dasha-lord-capability domain. Anything without
 * a clean domain match falls back to `general` — an honest admission that
 * T-0 has no servable domain-specific karaka set for that LEL category
 * today, not a fabricated one.
 */
const CATEGORY_TO_DOMAIN: Record<string, string> = {
  finance: 'wealth',
  loss: 'wealth',
  career: 'career',
  health: 'health',
  psychological: 'health',
  relationship: 'marriage',
  family: 'marriage',
  education: 'general',
  creative: 'general',
  spiritual: 'general',
  travel: 'general',
  other: 'general',
  'residential+travel': 'general',
}

export function domainForCategory(category: string): string {
  return CATEGORY_TO_DOMAIN[category] ?? 'general'
}

export function significatorsForCategory(category: string): Record<string, number> {
  const domain = domainForCategory(category)
  return DOMAIN_LORDS[domain] ?? DOMAIN_LORDS.general
}
