/**
 * pariprashna/corpus/report_schema.ts — versioned corpus-run report shape
 * (lane P2-N, roadmap id G3-F).
 *
 * A report stamps THREE independent version numbers, per this lane's
 * versioning requirement: `report_schema_version` (this shape),
 * `corpus_fixture_set_version` (`fixtures.ts`'s `CORPUS_FIXTURE_SET_VERSION`
 * at run time), and `scoring_harness_version`
 * (`dimensions/index.ts`'s `CORPUS_SCORING_HARNESS_VERSION` at run time) —
 * so any two reports are comparable only when all three match, and a
 * mismatch is visible in the report itself rather than requiring the reader
 * to cross-reference source history.
 */

import { z } from 'zod'

import { DIMENSION_IDS, QUERY_CLASSES } from './types'

export const CORPUS_REPORT_SCHEMA_VERSION = 1 as const

export const CorpusTargetSchema = z.object({
  kind: z.enum(['mocked_pipeline', 'web_route', 'mcp_door']),
  /** Human-readable description of what was actually run against (a URL, or "in-memory fixture mock"). */
  description: z.string(),
})
export type CorpusTarget = z.infer<typeof CorpusTargetSchema>

export const DimensionResultReportSchema = z.object({
  dimension: z.enum(DIMENSION_IDS),
  status: z.enum(['scored', 'not_yet_measurable']),
  score: z.number().min(0).max(1).nullable(),
  reason: z.string().nullable(),
  findings: z.array(z.string()),
})

export const FixtureRunResultSchema = z.object({
  fixture_id: z.string(),
  fixture_version: z.number().int(),
  query_class: z.enum(QUERY_CLASSES),
  ran: z.boolean(),
  skipped_reason: z.string().nullable(),
  dimension_results: z.array(DimensionResultReportSchema),
})
export type FixtureRunResult = z.infer<typeof FixtureRunResultSchema>

export const CorpusRunSummarySchema = z.object({
  fixtures_total: z.number().int().nonnegative(),
  fixtures_run: z.number().int().nonnegative(),
  fixtures_skipped: z.number().int().nonnegative(),
  /** Mean of `score` across every `scored` result for that dimension, across all run fixtures; null if none scored. */
  mean_score_by_dimension: z.record(z.enum(DIMENSION_IDS), z.number().nullable()),
})

export const CorpusRunReportSchema = z.object({
  report_schema_version: z.literal(CORPUS_REPORT_SCHEMA_VERSION),
  corpus_fixture_set_version: z.number().int(),
  scoring_harness_version: z.number().int(),
  generated_at: z.string(),
  target: CorpusTargetSchema,
  fixture_results: z.array(FixtureRunResultSchema),
  summary: CorpusRunSummarySchema,
})
export type CorpusRunReport = z.infer<typeof CorpusRunReportSchema>
