/**
 * tools/concordance_lookup.ts — brahmagyan.concordance MCP tool (BG-0-7).
 *
 * Tool: concordance.lookup(topic) → cross-school stances
 *
 * Given a topic (natural-language string or structured conditions),
 * returns the cross-school stances from the brahmagyan_concordance store.
 *
 * Each stance carries:
 *   {school, stance, stance_note, assertion_summary, rules_cited, stance_confidence,
 *    conflict_severity, source_works, verse_refs}
 *
 * Filtering:
 *   - topic: free-text search (FTS + slug match + dimension match)
 *   - school: restrict to one school (default: all four)
 *   - stance_filter: restrict to one stance type (agree|qualify|conflict|absent)
 *   - include_absent: whether to return absent-stances (default: true)
 *
 * FORENSIC contract:
 *   concordance.lookup("Sun in 2nd house") returns stances from all 4 schools
 *   (BPHS=parashari, Jaimini=jaimini, KP=kp, Tajaka=tajaka).
 *
 * [BRAHMA-BG-0-7]
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import pg from 'pg'

const { Pool } = pg

// ── DB connection (shared pool, lazy-initialised) ─────────────────────────────

let _pool: InstanceType<typeof Pool> | null = null

function getPool(): InstanceType<typeof Pool> {
  if (!_pool) {
    const DATABASE_URL = process.env['DATABASE_URL']
    if (!DATABASE_URL) {
      throw new Error('[concordance_lookup] DATABASE_URL not set')
    }
    _pool = new Pool({ connectionString: DATABASE_URL, max: 5 })
  }
  return _pool
}

// ── Input schema ──────────────────────────────────────────────────────────────

const ConcordanceLookupInputSchema = z.object({
  /** Topic to look up — free-text, e.g. "Sun in 2nd house" */
  topic: z
    .string()
    .min(1)
    .max(300)
    .describe(
      'Astrological topic to look up. Free-text, e.g. "Sun in 2nd house", "Saturn in Scorpio", "Venus in 7th". ' +
      'Can be a graha+bhava, graha+rasi, or a classical yoga name.',
    ),

  /** Optional school filter */
  school: z
    .enum(['parashari', 'jaimini', 'kp', 'tajaka'])
    .optional()
    .describe('Restrict results to one classical school. Default: all four schools.'),

  /** Optional stance type filter */
  stance_filter: z
    .enum(['agree', 'qualify', 'conflict', 'absent'])
    .optional()
    .describe('Return only stances of this type. Default: all stances.'),

  /** Whether to include absent-stances (schools with no rule) */
  include_absent: z
    .boolean()
    .optional()
    .default(true)
    .describe('Include schools that have no rule on this topic (stance=absent). Default: true.'),

  /** Maximum number of topic matches to return (each match returns up to 4 school stances) */
  limit: z
    .number()
    .int()
    .min(1)
    .max(20)
    .optional()
    .default(5)
    .describe('Maximum number of matching topics to return (each with up to 4 school stances). Default 5.'),
})

type ConcordanceLookupInput = z.infer<typeof ConcordanceLookupInputSchema>

// ── Result types ──────────────────────────────────────────────────────────────

interface SchoolStance {
  school: 'parashari' | 'jaimini' | 'kp' | 'tajaka'
  stance: 'agree' | 'qualify' | 'conflict' | 'absent'
  assertion_summary: string
  stance_note: string
  rules_cited: string[]
  rule_count: number
  primary_rule_id: string | null
  source_works: string[]
  verse_refs: string[]
  stance_confidence: number
  conflict_severity: string | null
}

interface TopicConcordance {
  topic: string
  topic_slug: string
  topic_category: string
  grahas: string[]
  rasis: string[]
  bhavas: number[]
  school_stances: SchoolStance[]
  has_conflict: boolean
  conflict_schools: string[]
  schools_present: number
  schools_absent: number
  lineage_summary: string
}

interface ConcordanceLookupEnvelope {
  query: {
    topic: string
    school: string | null
    stance_filter: string | null
    include_absent: boolean
  }
  topics: TopicConcordance[]
  total_topics_found: number
  total_stances_returned: number
  conflict_topics: number
  provenance: {
    asset_id: 'brahmagyan.concordance'
    asset_version: 'BG-0-7'
    layer: 'L0'
    schools: ['parashari', 'jaimini', 'kp', 'tajaka']
    quality_gate: 'derived_from_pilot_quality_pass_rules'
  }
  pilot_note: string
}

// ── Topic search ──────────────────────────────────────────────────────────────

interface RawRow {
  topic: string
  topic_slug: string
  topic_category: string
  grahas: string[]
  rasis: string[]
  bhavas: number[]
  school: string
  stance: string
  assertion_summary: string
  stance_note: string
  rules_cited: string[]
  rule_count: number
  primary_rule_id: string | null
  source_works: string[]
  verse_refs: string[]
  stance_confidence: string
  conflict_severity: string | null
}

async function lookupConcordance(
  input: ConcordanceLookupInput,
): Promise<ConcordanceLookupEnvelope> {
  const pool = getPool()

  const topicQuery = input.topic.trim()
  const topicSlug = topicQuery
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')

  // ── Step 1: find matching topic_slugs ─────────────────────────────────────
  //
  // Search order:
  // (a) Exact slug match
  // (b) Slug ILIKE match (partial)
  // (c) FTS on topic text
  // (d) Dimension match (parse grahas/bhavas from input)

  const matchedSlugsResult = await pool.query<{ topic_slug: string; rank: number }>(
    `SELECT DISTINCT topic_slug,
       CASE
         WHEN topic_slug = $1 THEN 100
         WHEN topic_slug ILIKE '%' || $1 || '%' THEN 80
         WHEN to_tsvector('english', topic) @@ plainto_tsquery('english', $2) THEN 60
         WHEN topic ILIKE '%' || $2 || '%' THEN 40
         ELSE 0
       END AS rank
     FROM brahmagyan_concordance
     WHERE topic_slug = $1
        OR topic_slug ILIKE '%' || $1 || '%'
        OR to_tsvector('english', topic) @@ plainto_tsquery('english', $2)
        OR topic ILIKE '%' || $2 || '%'
     ORDER BY rank DESC
     LIMIT $3`,
    [topicSlug, topicQuery, input.limit ?? 5],
  )

  const matchedSlugs = matchedSlugsResult.rows.map(r => r.topic_slug)

  if (matchedSlugs.length === 0) {
    // Return empty envelope with pilot note
    return buildEnvelope(input, [])
  }

  // ── Step 2: fetch all school stances for matched topics ───────────────────

  const conditions: string[] = [`topic_slug = ANY($1::text[])`]
  const params: unknown[] = [matchedSlugs]
  let paramIdx = 2

  if (input.school) {
    conditions.push(`school = $${paramIdx}`)
    params.push(input.school)
    paramIdx++
  }

  if (input.stance_filter) {
    conditions.push(`stance = $${paramIdx}`)
    params.push(input.stance_filter)
    paramIdx++
  }

  if (!(input.include_absent ?? true)) {
    conditions.push(`stance != 'absent'`)
  }

  const whereClause = conditions.join(' AND ')

  const rows = await pool.query<RawRow>(
    `SELECT
       topic, topic_slug, topic_category, grahas, rasis, bhavas,
       school, stance, assertion_summary, stance_note,
       rules_cited, rule_count, primary_rule_id,
       source_works, verse_refs, stance_confidence, conflict_severity
     FROM brahmagyan_concordance
     WHERE ${whereClause}
     ORDER BY topic_slug, school`,
    params,
  )

  return buildEnvelope(input, rows.rows)
}

function buildEnvelope(
  input: ConcordanceLookupInput,
  rows: RawRow[],
): ConcordanceLookupEnvelope {
  // Group rows by topic_slug
  const byTopic = new Map<string, RawRow[]>()
  for (const row of rows) {
    if (!byTopic.has(row.topic_slug)) byTopic.set(row.topic_slug, [])
    byTopic.get(row.topic_slug)!.push(row)
  }

  const topics: TopicConcordance[] = []

  for (const [, topicRows] of byTopic.entries()) {
    const first = topicRows[0]!

    const schoolStances: SchoolStance[] = topicRows.map(r => ({
      school: r.school as SchoolStance['school'],
      stance: r.stance as SchoolStance['stance'],
      assertion_summary: r.assertion_summary,
      stance_note: r.stance_note,
      rules_cited: r.rules_cited ?? [],
      rule_count: r.rule_count ?? 0,
      primary_rule_id: r.primary_rule_id ?? null,
      source_works: r.source_works ?? [],
      verse_refs: r.verse_refs ?? [],
      stance_confidence: parseFloat(r.stance_confidence),
      conflict_severity: r.conflict_severity ?? null,
    }))

    const conflictSchools = schoolStances
      .filter(s => s.stance === 'conflict')
      .map(s => s.school)

    const presentStances = schoolStances.filter(s => s.stance !== 'absent')
    const absentStances = schoolStances.filter(s => s.stance === 'absent')

    const allRulesCount = schoolStances.reduce((s, ss) => s + ss.rule_count, 0)
    const lineageSummary =
      presentStances.length === 0
        ? 'No school has rules on this topic yet (pilot scope). Full-canon ingestion will populate.'
        : `${presentStances.length} school(s) have rules (${allRulesCount} rules total). ` +
          (conflictSchools.length > 0
            ? `Conflicts detected in: ${conflictSchools.join(', ')}.`
            : 'No inter-school conflicts detected.')

    topics.push({
      topic: first.topic,
      topic_slug: first.topic_slug,
      topic_category: first.topic_category ?? 'general',
      grahas: first.grahas ?? [],
      rasis: first.rasis ?? [],
      bhavas: first.bhavas ?? [],
      school_stances: schoolStances,
      has_conflict: conflictSchools.length > 0,
      conflict_schools: conflictSchools,
      schools_present: presentStances.length,
      schools_absent: absentStances.length,
      lineage_summary: lineageSummary,
    })
  }

  const conflictTopicsCount = topics.filter(t => t.has_conflict).length
  const totalStances = topics.reduce((s, t) => s + t.school_stances.length, 0)

  const pilotNote = topics.length === 0
    ? `No concordance entries found for "${input.topic}". ` +
      'This may indicate the topic is not yet covered in the pilot Rule Base. ' +
      'Run bootstrap_brahmagyan_concordance.ts after bootstrap_brahmagyan_rules.ts to populate.'
    : `Concordance derived from the BG-0-6 pilot Rule Base (BPHS Chapter 1). ` +
      `Full-canon ingestion (all four classical texts) will expand topic coverage.`

  return {
    query: {
      topic: input.topic,
      school: input.school ?? null,
      stance_filter: input.stance_filter ?? null,
      include_absent: input.include_absent ?? true,
    },
    topics,
    total_topics_found: topics.length,
    total_stances_returned: totalStances,
    conflict_topics: conflictTopicsCount,
    provenance: {
      asset_id: 'brahmagyan.concordance',
      asset_version: 'BG-0-7',
      layer: 'L0',
      schools: ['parashari', 'jaimini', 'kp', 'tajaka'],
      quality_gate: 'derived_from_pilot_quality_pass_rules',
    },
    pilot_note: pilotNote,
  }
}

// ── MCP tool registration ─────────────────────────────────────────────────────

export function registerConcordanceLookupTool(server: McpServer): void {
  server.tool(
    'concordance_lookup',
    'Look up cross-school stances for an astrological topic from the Brahmagyan concordance (BG-0-7). ' +
    'Returns agree/qualify/conflict/absent stances from all four classical schools ' +
    '(Parashari/BPHS, Jaimini, KP, Tajaka) with verse-level lineage. ' +
    'Conflicts are surfaced, not flattened. ' +
    'FORENSIC: concordance_lookup("Sun in 2nd house") returns stances from all 4 schools.',
    ConcordanceLookupInputSchema.shape,
    async (input: ConcordanceLookupInput) => {
      try {
        const envelope = await lookupConcordance(input)
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify(envelope, null, 2),
            },
          ],
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err)
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify({
                error: 'concordance_lookup_failed',
                message,
                asset_id: 'brahmagyan.concordance',
                layer: 'L0',
              }),
            },
          ],
          isError: true,
        }
      }
    },
  )
}

// ── Export for testing ────────────────────────────────────────────────────────

export {
  lookupConcordance,
  buildEnvelope,
  ConcordanceLookupInputSchema,
}
export type {
  ConcordanceLookupInput,
  ConcordanceLookupEnvelope,
  TopicConcordance,
  SchoolStance,
}
