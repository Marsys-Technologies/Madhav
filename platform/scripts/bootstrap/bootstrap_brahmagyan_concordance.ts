#!/usr/bin/env npx tsx
/**
 * bootstrap_brahmagyan_concordance.ts
 * Brahmagyan Layer-0 Concordance (BG-0-7) — derivation pipeline.
 *
 * Reads brahmagyan_rules (BG-0-6) and derives per-topic cross-school stances.
 * For each topic (identified by shared grahas/rasis/bhavas), computes:
 *   - Which schools have rules on the topic
 *   - Whether the schools agree, qualify, conflict, or are absent
 *   - Lineage: which rule_ids produced this stance
 *
 * Stance assignment logic:
 *   1. Cluster rules by topic signature (graha+rasi or graha+bhava combination).
 *   2. For each cluster, group rules by school.
 *   3. Compare assertions across schools:
 *      agree: assertion_structured polarity and domain align across all schools
 *      qualify: same domain, but one school adds conditions or has lower confidence
 *      conflict: opposing polarity (positive vs negative) or contradictory assertion
 *      absent: no rule from this school for this topic
 *
 * FORENSIC contract:
 *   concordance.lookup("Sun in 2nd house") → stances from BPHS + Jaimini + KP + Tajaka
 *   At minimum: parashari stance present; absent-stances for schools with no rule.
 *
 * Usage:
 *   DATABASE_URL="..." npx tsx platform/scripts/bootstrap/bootstrap_brahmagyan_concordance.ts
 *   DATABASE_URL="..." npx tsx platform/scripts/bootstrap/bootstrap_brahmagyan_concordance.ts --dry-run
 *
 * [BRAHMA-BG-0-7]
 */

import { Pool } from 'pg'

// ── Configuration ──────────────────────────────────────────────────────────────

const DATABASE_URL =
  process.env['DATABASE_URL'] ?? 'postgresql://amjis_app@localhost:5433/amjis'

const args = process.argv.slice(2)
const DRY_RUN = args.includes('--dry-run')

const BUILD_TIMESTAMP = new Date()
  .toISOString()
  .slice(0, 16)
  .replace('T', '-')
  .replace(':', '')
const BUILD_ID = `brahma-concordance-${DRY_RUN ? 'dryrun' : 'pilot'}-${BUILD_TIMESTAMP}`

const ALL_SCHOOLS = ['parashari', 'jaimini', 'kp', 'tajaka'] as const
type School = typeof ALL_SCHOOLS[number]
type Stance = 'agree' | 'qualify' | 'conflict' | 'absent'

// ── DB types ───────────────────────────────────────────────────────────────────

interface RuleRow {
  rule_id: string
  condition: string
  assertion: string
  condition_structured: {
    grahas?: string[]
    rasis?: string[]
    bhavas?: number[]
    aspects?: string[]
  } | null
  assertion_structured: {
    domain?: string
    outcome?: string
    polarity?: 'positive' | 'negative' | 'neutral' | string
    keywords?: string[]
  } | null
  source_verse_id: string
  source_work: string
  school: string
  scope: string
  domains_affected: string[]
  grahas_involved: string[]
  rasis_involved: string[]
  bhavas_involved: number[]
  confidence: string
  confidence_note: string
  verse_ref: string
}

// ── Concordance row for upsert ─────────────────────────────────────────────────

interface ConcordanceRow {
  topic: string
  topic_slug: string
  topic_category: string
  grahas: string[]
  rasis: string[]
  bhavas: number[]
  nakshatras: string[]
  school: School
  stance: Stance
  stance_note: string
  assertion_summary: string
  rules_cited: string[]
  rule_count: number
  primary_rule_id: string | null
  source_works: string[]
  verse_refs: string[]
  stance_confidence: number
  conflict_severity: string | null
  build_id: string
  extraction_method: string
}

// ── Topic slug helper ──────────────────────────────────────────────────────────

function toSlug(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
}

// ── Topic label helper ─────────────────────────────────────────────────────────

function makeTopicLabel(grahas: string[], rasis: string[], bhavas: number[]): string {
  const parts: string[] = []

  for (const g of grahas) {
    const gLabel = g.charAt(0) + g.slice(1).toLowerCase()  // "SUN" → "Sun"

    if (bhavas.length > 0) {
      for (const b of bhavas) {
        const suffix = b === 1 ? 'st' : b === 2 ? 'nd' : b === 3 ? 'rd' : 'th'
        parts.push(`${gLabel} in ${b}${suffix} house`)
      }
    } else if (rasis.length > 0) {
      for (const r of rasis) {
        const rLabel = r.charAt(0) + r.slice(1).toLowerCase()
        parts.push(`${gLabel} in ${rLabel}`)
      }
    } else {
      parts.push(gLabel)
    }
  }

  if (parts.length === 0) {
    // Fallback: rasis only
    for (const r of rasis) {
      const rLabel = r.charAt(0) + r.slice(1).toLowerCase()
      parts.push(rLabel)
    }
  }

  return parts.join(', ') || 'general'
}

// ── Topic category from dimensions ────────────────────────────────────────────

function categorize(grahas: string[], rasis: string[], bhavas: number[], scope: string): string {
  if (scope === 'transit') return 'transit'
  if (scope === 'dasha') return 'dasha'
  if (scope === 'muhurta') return 'general'
  if (bhavas.length > 0 && grahas.length > 0) return 'placement'
  if (rasis.length > 0 && grahas.length > 0) return 'placement'
  if (grahas.length === 0 && rasis.length === 0 && bhavas.length === 0) return 'general'
  return 'placement'
}

// ── Topic signature: stable key grouping rules on the same topic ───────────────

function topicSignature(rule: RuleRow): string | null {
  const g = [...(rule.grahas_involved ?? [])].sort()
  const r = [...(rule.rasis_involved ?? [])].sort()
  const b = [...(rule.bhavas_involved ?? [])].sort()

  // A rule needs at least one dimension to be clusterable
  if (g.length === 0 && r.length === 0 && b.length === 0) return null

  // Primary signature: graha+bhava is the most specific
  if (g.length > 0 && b.length > 0) {
    return `g:${g.join(',')}_b:${b.join(',')}`
  }
  // graha+rasi
  if (g.length > 0 && r.length > 0) {
    return `g:${g.join(',')}_r:${r.join(',')}`
  }
  // graha only
  if (g.length > 0) {
    return `g:${g.join(',')}`
  }
  // rasi only
  if (r.length > 0) {
    return `r:${r.join(',')}`
  }
  // bhava only
  return `b:${b.join(',')}`
}

// ── Stance derivation ─────────────────────────────────────────────────────────
//
// Given all rules from a single school on a topic, derive one stance.
// If multiple rules: pick the highest-confidence; note qualifications.

function deriveSchoolStance(
  schoolRules: RuleRow[],
  otherSchoolsRules: RuleRow[],
): {
  stance: Stance
  stanceNote: string
  assertionSummary: string
  confidence: number
  conflictSeverity: string | null
  ruleIds: string[]
  sourceWorks: string[]
  verseRefs: string[]
  primaryRuleId: string | null
} {
  if (schoolRules.length === 0) {
    return {
      stance: 'absent',
      stanceNote: 'No rule found in this school for this topic.',
      assertionSummary: '[no rule]',
      confidence: 0.0,
      conflictSeverity: null,
      ruleIds: [],
      sourceWorks: [],
      verseRefs: [],
      primaryRuleId: null,
    }
  }

  // Sort by confidence descending
  const sorted = [...schoolRules].sort(
    (a, b) => parseFloat(b.confidence) - parseFloat(a.confidence),
  )
  const primary = sorted[0]
  const avgConfidence =
    sorted.reduce((s, r) => s + parseFloat(r.confidence), 0) / sorted.length

  const ruleIds = sorted.map(r => r.rule_id)
  const sourceWorks = [...new Set(sorted.map(r => r.source_work))]
  const verseRefs = sorted.map(r => r.verse_ref)
  const primaryRuleId = primary.rule_id

  // Polarity from assertion_structured (if available)
  const primaryPolarity = primary.assertion_structured?.polarity ?? 'neutral'
  const primaryDomain = primary.assertion_structured?.domain ?? 'general'
  const assertionSummary = primary.assertion.slice(0, 200)

  // Check against other schools
  const otherPolarities = otherSchoolsRules
    .map(r => r.assertion_structured?.polarity)
    .filter(Boolean) as string[]

  const hasConflict = otherPolarities.some(p => {
    if (primaryPolarity === 'positive' && p === 'negative') return true
    if (primaryPolarity === 'negative' && p === 'positive') return true
    return false
  })

  if (hasConflict) {
    // Determine severity
    const divergentCount = otherPolarities.filter(p =>
      (primaryPolarity === 'positive' && p === 'negative') ||
      (primaryPolarity === 'negative' && p === 'positive'),
    ).length

    const conflictSeverity = divergentCount >= 2 ? 'fundamental' : 'significant'

    return {
      stance: 'conflict',
      stanceNote:
        `This school's assertion (polarity=${primaryPolarity}) contradicts ${divergentCount} other school(s). ` +
        `Severity: ${conflictSeverity}. Primary rule: ${primaryRuleId}.`,
      assertionSummary,
      confidence: avgConfidence,
      conflictSeverity,
      ruleIds,
      sourceWorks,
      verseRefs,
      primaryRuleId,
    }
  }

  // Check for qualification (same domain, but lower confidence or added conditions)
  const qualifyIndicators = [
    sorted.length > 1 && sorted[0] && sorted[1] ?
      parseFloat(sorted[0].confidence) - parseFloat(sorted[1].confidence) > 0.2 : false,
    avgConfidence < 0.60,
    primaryDomain !== 'general' && otherSchoolsRules.some(
      r => r.assertion_structured?.domain !== primaryDomain &&
           r.assertion_structured?.domain != null,
    ),
  ]

  if (qualifyIndicators.some(Boolean)) {
    return {
      stance: 'qualify',
      stanceNote:
        `This school's rules qualify the topic with conditions. ` +
        `Confidence: ${avgConfidence.toFixed(3)}. Rules: ${ruleIds.length}. Primary: ${primaryRuleId}.`,
      assertionSummary,
      confidence: avgConfidence,
      conflictSeverity: null,
      ruleIds,
      sourceWorks,
      verseRefs,
      primaryRuleId,
    }
  }

  // Default: agree
  return {
    stance: 'agree',
    stanceNote:
      `This school has ${ruleIds.length} rule(s) on this topic. ` +
      `Avg confidence: ${avgConfidence.toFixed(3)}. Primary: ${primaryRuleId}.`,
    assertionSummary,
    confidence: avgConfidence,
    conflictSeverity: null,
    ruleIds,
    sourceWorks,
    verseRefs,
    primaryRuleId,
  }
}

// ── Main derivation logic ──────────────────────────────────────────────────────

async function deriveConcordance(pool: InstanceType<typeof Pool>): Promise<ConcordanceRow[]> {
  // Load all quality-passed rules
  const res = await pool.query<RuleRow>(`
    SELECT
      rule_id, condition, assertion,
      condition_structured, assertion_structured,
      source_verse_id, source_work, school, scope,
      domains_affected, grahas_involved, rasis_involved, bhavas_involved,
      confidence, confidence_note, verse_ref
    FROM brahmagyan_rules
    WHERE pilot_quality_pass = TRUE
    ORDER BY confidence DESC
  `)

  const rules = res.rows
  console.log(`[concordance] Loaded ${rules.length} quality-passed rules from brahmagyan_rules`)

  if (rules.length === 0) {
    console.warn('[concordance] brahmagyan_rules is empty. Run bootstrap_brahmagyan_rules.ts first.')
    return []
  }

  // Cluster rules by topic signature
  const clusters = new Map<string, RuleRow[]>()

  for (const rule of rules) {
    const sig = topicSignature(rule)
    if (!sig) {
      // Rule has no structured dimensions — group under 'general'
      const key = 'general'
      if (!clusters.has(key)) clusters.set(key, [])
      clusters.get(key)!.push(rule)
      continue
    }
    if (!clusters.has(sig)) clusters.set(sig, [])
    clusters.get(sig)!.push(rule)
  }

  console.log(`[concordance] ${clusters.size} topic clusters found`)

  const concordanceRows: ConcordanceRow[] = []

  for (const [sig, clusterRules] of clusters.entries()) {
    // Gather topic dimensions from the cluster
    const allGrahas = [...new Set(clusterRules.flatMap(r => r.grahas_involved ?? []))].sort()
    const allRasis = [...new Set(clusterRules.flatMap(r => r.rasis_involved ?? []))].sort()
    const allBhavas = [...new Set(clusterRules.flatMap(r => r.bhavas_involved ?? []))].sort(
      (a, b) => a - b,
    )
    const dominantScope = clusterRules[0]?.scope ?? 'general'

    const topic = sig === 'general'
      ? 'General (uncategorised)'
      : makeTopicLabel(allGrahas, allRasis, allBhavas)
    const topicSlug = toSlug(topic)
    const topicCategory = categorize(allGrahas, allRasis, allBhavas, dominantScope)

    // For each school, derive stance
    for (const school of ALL_SCHOOLS) {
      const schoolRules = clusterRules.filter(r => r.school === school)
      const otherSchoolsRules = clusterRules.filter(r => r.school !== school)

      const stance = deriveSchoolStance(schoolRules, otherSchoolsRules)

      concordanceRows.push({
        topic,
        topic_slug: topicSlug,
        topic_category: topicCategory,
        grahas: allGrahas,
        rasis: allRasis,
        bhavas: allBhavas,
        nakshatras: [],
        school,
        stance: stance.stance,
        stance_note: stance.stanceNote,
        assertion_summary: stance.assertionSummary,
        rules_cited: stance.ruleIds,
        rule_count: stance.ruleIds.length,
        primary_rule_id: stance.primaryRuleId,
        source_works: stance.sourceWorks,
        verse_refs: stance.verseRefs,
        stance_confidence: parseFloat(stance.confidence.toFixed(3)),
        conflict_severity: stance.conflictSeverity,
        build_id: BUILD_ID,
        extraction_method: 'derived_from_rules',
      })
    }
  }

  console.log(`[concordance] ${concordanceRows.length} concordance entries derived`)
  return concordanceRows
}

// ── Upsert to DB ──────────────────────────────────────────────────────────────

async function upsertConcordance(
  pool: InstanceType<typeof Pool>,
  rows: ConcordanceRow[],
): Promise<void> {
  if (rows.length === 0) {
    console.log('[concordance] No rows to upsert.')
    return
  }

  let inserted = 0
  let updated = 0
  const BATCH_SIZE = 50

  for (let i = 0; i < rows.length; i += BATCH_SIZE) {
    const batch = rows.slice(i, i + BATCH_SIZE)

    for (const row of batch) {
      const result = await pool.query(
        `INSERT INTO brahmagyan_concordance
          (topic, topic_slug, topic_category,
           grahas, rasis, bhavas, nakshatras,
           school, stance, stance_note, assertion_summary,
           rules_cited, rule_count, primary_rule_id,
           source_works, verse_refs,
           stance_confidence, conflict_severity,
           build_id, extraction_method)
         VALUES
          ($1, $2, $3,
           $4::text[], $5::text[], $6::integer[], $7::text[],
           $8, $9, $10, $11,
           $12::text[], $13, $14,
           $15::text[], $16::text[],
           $17, $18,
           $19, $20)
         ON CONFLICT (topic_slug, school) DO UPDATE SET
           topic = EXCLUDED.topic,
           topic_category = EXCLUDED.topic_category,
           grahas = EXCLUDED.grahas,
           rasis = EXCLUDED.rasis,
           bhavas = EXCLUDED.bhavas,
           stance = EXCLUDED.stance,
           stance_note = EXCLUDED.stance_note,
           assertion_summary = EXCLUDED.assertion_summary,
           rules_cited = EXCLUDED.rules_cited,
           rule_count = EXCLUDED.rule_count,
           primary_rule_id = EXCLUDED.primary_rule_id,
           source_works = EXCLUDED.source_works,
           verse_refs = EXCLUDED.verse_refs,
           stance_confidence = EXCLUDED.stance_confidence,
           conflict_severity = EXCLUDED.conflict_severity,
           build_id = EXCLUDED.build_id,
           updated_at = now()
         RETURNING (xmax = 0) AS inserted`,
        [
          row.topic,
          row.topic_slug,
          row.topic_category,
          row.grahas,
          row.rasis,
          row.bhavas,
          row.nakshatras,
          row.school,
          row.stance,
          row.stance_note,
          row.assertion_summary,
          row.rules_cited,
          row.rule_count,
          row.primary_rule_id,
          row.source_works,
          row.verse_refs,
          row.stance_confidence,
          row.conflict_severity,
          row.build_id,
          row.extraction_method,
        ],
      )

      if (result.rows[0]?.inserted) {
        inserted++
      } else {
        updated++
      }
    }

    console.log(`[concordance] Batch ${Math.floor(i / BATCH_SIZE) + 1}: upserted ${batch.length} rows`)
  }

  console.log(`[concordance] Upsert complete: ${inserted} inserted, ${updated} updated`)
}

// ── Verification report ────────────────────────────────────────────────────────

async function verifyAndReport(pool: InstanceType<typeof Pool>): Promise<void> {
  const topicCount = await pool.query<{ count: string }>(
    `SELECT count(DISTINCT topic_slug) FROM brahmagyan_concordance`,
  )
  const totalRows = await pool.query<{ count: string }>(
    `SELECT count(*) FROM brahmagyan_concordance`,
  )
  const conflictCount = await pool.query<{ count: string }>(
    `SELECT count(*) FROM brahmagyan_concordance WHERE stance = 'conflict'`,
  )
  const absentCount = await pool.query<{ count: string }>(
    `SELECT count(*) FROM brahmagyan_concordance WHERE stance = 'absent'`,
  )

  // FORENSIC check: Sun in 2nd house topic
  const forensicCheck = await pool.query<{ topic: string; school: string; stance: string }>(
    `SELECT topic, school, stance
     FROM brahmagyan_concordance
     WHERE topic_slug ILIKE '%sun%2nd%' OR topic_slug ILIKE '%sun%second%'
        OR topic ILIKE '%Sun in 2nd%' OR topic ILIKE '%Sun in second%'
     ORDER BY school`,
  )

  console.log('\n── Concordance Verification Report ──────────────────────────────')
  console.log(`Topics covered:     ${topicCount.rows[0]?.count ?? 0}`)
  console.log(`Total stance rows:  ${totalRows.rows[0]?.count ?? 0}`)
  console.log(`Conflict stances:   ${conflictCount.rows[0]?.count ?? 0}`)
  console.log(`Absent stances:     ${absentCount.rows[0]?.count ?? 0}`)
  console.log(``)
  console.log(`FORENSIC — "Sun in 2nd house" topic coverage:`)
  if (forensicCheck.rows.length === 0) {
    console.log(`  [WARN] No rows found. Add Sun-in-2nd rules to brahmagyan_rules to populate.`)
    console.log(`  Pilot seed below ensures at least parashari absent-stance is present.`)
  } else {
    for (const row of forensicCheck.rows) {
      console.log(`  ${row.school}: ${row.stance}  (topic="${row.topic}")`)
    }
  }
  console.log('────────────────────────────────────────────────────────────────\n')
}

// ── FORENSIC seed: ensure "Sun in 2nd house" has all-school stances ───────────
//
// The FORENSIC contract requires concordance.lookup("Sun in 2nd house") to return
// stances from all 4 schools. If the Rule Base (pilot scope = BPHS Ch.1) does not
// contain Sun-in-2nd-house rules yet, we seed absent-stances so the tool can return
// a well-formed envelope for all schools (absent = correct and honest).

async function ensureForensicTopic(pool: InstanceType<typeof Pool>): Promise<void> {
  const FORENSIC_TOPIC = 'Sun in 2nd house'
  const FORENSIC_SLUG = 'sun_2nd_house'

  for (const school of ALL_SCHOOLS) {
    // Check if entry already exists (from derivation or prior seed)
    const existing = await pool.query(
      `SELECT id FROM brahmagyan_concordance WHERE topic_slug = $1 AND school = $2`,
      [FORENSIC_SLUG, school],
    )
    if (existing.rows.length > 0) continue  // already present

    // Seed an absent-stance entry so tool returns a well-formed response
    await pool.query(
      `INSERT INTO brahmagyan_concordance
        (topic, topic_slug, topic_category,
         grahas, rasis, bhavas, nakshatras,
         school, stance, stance_note, assertion_summary,
         rules_cited, rule_count, primary_rule_id,
         source_works, verse_refs,
         stance_confidence, conflict_severity,
         build_id, extraction_method)
       VALUES
        ($1, $2, 'placement',
         ARRAY['SUN'], ARRAY[]::text[], ARRAY[2]::integer[], ARRAY[]::text[],
         $3, 'absent',
         'No rule yet extracted for this school on this topic. Full-canon ingestion will populate.',
         '[no rule in pilot scope]',
         ARRAY[]::text[], 0, NULL,
         ARRAY[]::text[], ARRAY[]::text[],
         0.000, NULL,
         $4, 'derived_from_rules')
       ON CONFLICT (topic_slug, school) DO NOTHING`,
      [FORENSIC_TOPIC, FORENSIC_SLUG, school, BUILD_ID],
    )
    console.log(`[concordance] FORENSIC seed: ${school} absent-stance for "${FORENSIC_TOPIC}"`)
  }
}

// ── Entry point ───────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log(`[concordance] bootstrap_brahmagyan_concordance.ts — BG-0-7`)
  console.log(`[concordance] BUILD_ID: ${BUILD_ID}`)
  console.log(`[concordance] DRY_RUN: ${DRY_RUN}`)

  const pool = new Pool({ connectionString: DATABASE_URL, max: 5 })

  try {
    // 1. Derive concordance rows from Rule Base
    const rows = await deriveConcordance(pool)

    if (DRY_RUN) {
      console.log('[concordance] DRY RUN — showing first 10 rows:')
      for (const row of rows.slice(0, 10)) {
        console.log(
          `  [${row.school}] ${row.topic} → ${row.stance} (conf=${row.stance_confidence})`,
        )
      }
      console.log(`[concordance] DRY RUN complete. ${rows.length} rows would be upserted.`)
      return
    }

    // 2. Upsert to DB
    await upsertConcordance(pool, rows)

    // 3. Ensure FORENSIC topic has all-school stances
    await ensureForensicTopic(pool)

    // 4. Verify and report
    await verifyAndReport(pool)

    console.log('[concordance] Bootstrap complete. [BRAHMA-BG-0-7]')
  } finally {
    await pool.end()
  }
}

main().catch(err => {
  console.error('[concordance] Fatal error:', err)
  process.exit(1)
})
