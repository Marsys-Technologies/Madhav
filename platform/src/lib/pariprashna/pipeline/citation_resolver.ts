/**
 * pariprashna/pipeline/citation_resolver.ts — G2-B "Citations at first
 * paint" (PPR-08, FD-2/FD-6).
 *
 * Builds the `CitationResolver` the live citation rewriter
 * (`citations/stream_wiring.ts`) uses to grade a sentinel DURING streaming.
 *
 * `CitationResolver.resolve` is SYNCHRONOUS by contract (`citations/types.ts`
 * — the rewriter calls it inline in the hot streaming loop and cannot await a
 * live DB round-trip per sentinel). So resolution here is a two-step split:
 *
 *   1. `fetchCandidateSignalLabels` — ONE prefetch pass (parallel per-source
 *      queries), run once before the synthesis stream opens, keyed on every
 *      id-shaped token visible in THIS TURN's own retrieved evidence
 *      (`EvidenceStageOutput.validToolResults`) AND scoped to THIS chart.
 *      Scoped to this turn's evidence deliberately: a sentinel naming an id
 *      that is real in some source table but was never part of what THIS
 *      turn actually retrieved is not grounded for this answer, and must
 *      resolve to null (→ unverified / hallucination-counted) rather than
 *      borrow a grade from an unrelated context. A superset scan (extra
 *      candidate ids that never get cited) costs one wasted row in the
 *      prefetch, never a correctness problem — the candidate ids are just a
 *      cache-population hint, not a filter.
 *   2. `buildTurnCitationResolver` — wraps the resulting Map in the
 *      synchronous `CitationResolver` interface. A ref found resolves to
 *      grade `primary` (CitationGrade's own doc: "directly grounded in an L1
 *      fact / firings-authoritative signal" — which is exactly what every
 *      source table below is); a ref not found returns null, the honest "I
 *      don't know" (§N.7 item 6).
 *
 * ── Id-shape space (V3-E-032 widening, S4) ───────────────────────────────
 * The pre-widening version of this module only recognized `SIG.MSR.NNN`-
 * shaped tokens and only queried `bodha_msr_signals`. Two problems, traced
 * against the live retrieval/DB layer rather than guessed:
 *
 *   (a) The synthesis prompt's own citation appendix
 *       (`pariprashna_synthesis_prompt_v1.ts` — PARIPRASHNA_CITATION_APPENDIX)
 *       instructs the model to cite "the exact reference id AS IT APPEARS IN
 *       THE RETRIEVED CONTEXT" — not scoped to MSR signal ids — and its own
 *       forbidden-list ("internal identifiers (signal ids, asset ids like
 *       bo_/ga_/…, table names, or register acronyms)") only makes sense if
 *       ids beyond MSR signals are legitimate INSIDE a sentinel.
 *   (b) Tracing the real schema (not the `SIG.MSR.NNN` convention documented
 *       in the MSR spec doc / python-sidecar analysis code, which describes
 *       the *signal-type catalog*, not the live per-chart row id): the
 *       `bodha_msr_signals.signal_id` column is a genuine `UUID` in
 *       production (verified live against the S4 bench chart
 *       `1c826d5a-41cb-4450-b4dc-59d440e5f75a`) — the literal string
 *       "SIG.MSR.NNN" does not occur anywhere in that table's data. Every
 *       `query_signals`/`msr_sql` tool call therefore hands the model a
 *       UUID-shaped `signal_id` in its retrieved content, and the old regex
 *       could never match it. This alone plausibly explains the reported
 *       183/183 `unverified` rate.
 *
 * Four id families are now recognized, each traced to a real column a real
 * capability serves into `ToolBundleResult.content` this turn:
 *
 *   - `SIG.MSR.NNN`  (legacy/back-compat) — kept byte-for-byte; still
 *     queried against `bodha_msr_signals` in case any source ever serves
 *     this literal form. A candidate that never matches costs one wasted
 *     row lookup, nothing else (see extraction-superset note above).
 *   - UUID-shaped id  (`bodha_msr_signals.signal_id`, `chart_divisionals.id`,
 *     `chart_dashas.dasha_row_id`) — all three are `UUID PRIMARY KEY`
 *     columns confirmed present in served content: `query_signals`
 *     (`L2_bodha/query_signals.ts`) serves raw `signal_id` rows;
 *     `chart_facts_query`'s `divisional_facts` section
 *     (`register_d7_channel.ts` §"S-12 / Gate B") serves `chart_divisionals
 *     .id` under the key `fact_id`; `get_dashas.ts`'s `COMPACT_FIELDS`
 *     projection always includes `dasha_row_id`.
 *   - 16-lowercase-hex-char id  (`chart_facts.fact_id`) — every `ga_*`
 *     writer (`ga_positions_writer.py`, `ga_sensitive_degree_writer.py`,
 *     `ga_sade_sati_writer.py`, `ga_structural_writer.py`,
 *     `ga_sensitive_writer.py`, `ga_vargas_writer.py`,
 *     `ga_panchanga_writer.py`, `ga_strength_writer.py`,
 *     `ga_ayurdaya_writer.py`) derives `fact_id` identically:
 *     `sha256(category|subject|key|chart_id|ayanamsha_id|build_id)[:16]`
 *     — confirmed against live `chart_facts` rows (e.g. `78720121094c0de8`).
 *     `chart_facts_query`'s own doc comment: "emits_references: every
 *     pivoted field carries its source fact_id for Bodha back-reference."
 *
 * NOT widened (investigated, not confidently verified as safely resolvable
 * in this pass — see citation_resolver's PR description for the honest
 * accounting): L0 `l0_citation_ids` family (`sutravali_rules.rule_id`,
 * `classical_texts_source.text_id`) — the registry's own `grounds_to`
 * taxonomy names this as a real reference family, but text_id/rule_id
 * formats are heterogeneous (slug-like vs UUID) and global (not chart-
 * scoped), which changes the fail-closed shape of the query in a way this
 * pass did not have budget to verify safely against a real corpus row.
 */

import { query } from '@/lib/db/client'
import type { CitationGrade, CitationResolver, ResolvedCitation } from '@/lib/pariprashna/citations/types'
import type { ToolBundle } from '@/lib/retrieval/shared_types'

const SIGNAL_ID_RE = /SIG\.MSR\.\d{3}/g
/** Standard UUID v4-shaped token (any of the 3 UUID-keyed row families below). */
const UUID_RE = /\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b/g
/** `chart_facts.fact_id` shape: sha256(...)[0:16], always lowercase hex. */
const FACT_ID_HEX_RE = /\b[0-9a-f]{16}\b/g

const SNIPPET_MAX = 295

interface CandidateSignalLabel {
  reader_label: string
  grade: CitationGrade
  /** Which table this id resolved against — feeds the resolver's audit_detail. */
  source_table: string
  /** Which column matched — feeds the resolver's audit_detail. */
  source_column: string
}

/** The id-shaped token groups pulled from this turn's retrieved evidence. */
export interface CandidateIds {
  /** `SIG.MSR.NNN`-shaped (legacy/back-compat; see module doc). */
  legacyMsrRefs: string[]
  /** Standard UUID-shaped — candidate `signal_id` / `chart_divisionals.id` / `dasha_row_id`. */
  uuidRefs: string[]
  /** 16-lowercase-hex-char — candidate `chart_facts.fact_id`. */
  factIdRefs: string[]
}

/** Scan this turn's retrieved tool results for every recognized candidate id shape. */
export function extractCandidateSignalIds(args: {
  validToolResults: readonly ToolBundle[]
}): CandidateIds {
  const legacy = new Set<string>()
  const uuids = new Set<string>()
  const factIds = new Set<string>()
  for (const tb of args.validToolResults) {
    for (const r of tb.results) {
      for (const m of r.content.matchAll(SIGNAL_ID_RE)) legacy.add(m[0])
      for (const m of r.content.matchAll(UUID_RE)) uuids.add(m[0].toLowerCase())
      for (const m of r.content.matchAll(FACT_ID_HEX_RE)) factIds.add(m[0])
    }
  }
  return { legacyMsrRefs: [...legacy], uuidRefs: [...uuids], factIdRefs: [...factIds] }
}

export interface PrefetchResult {
  labels: Map<string, CandidateSignalLabel>
  /**
   * True when at least one of the per-source prefetch queries itself faulted
   * (DB/infra error) — distinguishes a genuine degraded state from the
   * honest "nothing to resolve" case (§N.8: a signal needs a real detector
   * behind it, not a proxy). Does NOT change resolve-to-null behavior for
   * THIS turn's citations — a source that faulted still yields no labels
   * from that source, so any id that would have resolved there is null this
   * turn, same fail-closed direction as before. The caller should surface
   * this via a flag so a degraded prefetch is distinguishable, downstream,
   * from "the model just didn't cite anything real."
   */
  faulted: boolean
}

function buildSnippet(name: string | null, description: string | null, fallback: string): string {
  const full = name ? (description ? `${name} — ${description}` : name) : (description ?? fallback)
  return full.length > SNIPPET_MAX ? full.slice(0, SNIPPET_MAX - 1) + '…' : full
}

/**
 * Fetch reader labels for candidate ids from every source table that could
 * legitimately have served them this turn, scoped to `chartId`. Never
 * throws — a per-source query fault degrades that source to "no labels
 * from here" (the sentinels it would have resolved fall through to `null` /
 * unverified this turn, the honest fail-closed direction — see
 * `register_leak_lint.ts`'s own `lintReaderProse` for the same
 * fail-open-to-honest-null discipline on its internal-error path), while
 * `faulted` distinguishes that from a clean "nothing to resolve" prefetch.
 */
export async function fetchCandidateSignalLabels(
  chartId: string,
  candidates: CandidateIds,
): Promise<PrefetchResult> {
  const labels = new Map<string, CandidateSignalLabel>()
  let faulted = false

  const signalCandidates = [...candidates.legacyMsrRefs, ...candidates.uuidRefs]
  const lookups: Array<Promise<void>> = []

  if (signalCandidates.length > 0) {
    lookups.push(
      query<{ signal_id: string; name: string | null; description: string | null }>(
        `SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description
         FROM bodha_msr_signals
         WHERE chart_id = $1 AND signal_id::text = ANY($2::text[])`,
        [chartId, signalCandidates],
      )
        .then(({ rows }) => {
          for (const r of rows) {
            labels.set(r.signal_id, {
              reader_label: buildSnippet(r.name, r.description, r.signal_id),
              grade: 'primary' as CitationGrade,
              source_table: 'bodha_msr_signals',
              source_column: 'signal_id',
            })
          }
        })
        .catch((err) => {
          faulted = true
          console.error('[pariprashna] citation resolver prefetch failed for bodha_msr_signals (non-fatal — refs resolve unverified this turn):', err)
        }),
    )
  }

  if (candidates.factIdRefs.length > 0) {
    lookups.push(
      query<{ fact_id: string; citation_human: string | null }>(
        `SELECT fact_id, citation_human
         FROM chart_facts
         WHERE chart_id = $1 AND fact_id = ANY($2::text[])`,
        [chartId, candidates.factIdRefs],
      )
        .then(({ rows }) => {
          for (const r of rows) {
            labels.set(r.fact_id, {
              reader_label: buildSnippet(r.citation_human, null, r.fact_id),
              grade: 'primary' as CitationGrade,
              source_table: 'chart_facts',
              source_column: 'fact_id',
            })
          }
        })
        .catch((err) => {
          faulted = true
          console.error('[pariprashna] citation resolver prefetch failed for chart_facts (non-fatal — refs resolve unverified this turn):', err)
        }),
    )
  }

  if (candidates.uuidRefs.length > 0) {
    lookups.push(
      query<{ row_id: string; citation_human: string | null }>(
        `SELECT id::text AS row_id, citation_human
         FROM chart_divisionals
         WHERE chart_id = $1 AND id::text = ANY($2::text[])`,
        [chartId, candidates.uuidRefs],
      )
        .then(({ rows }) => {
          for (const r of rows) {
            // Don't clobber an existing hit from a higher-precedence source
            // (signal_id is checked first, above) — a UUID collision across
            // tables is a PK-generation impossibility in practice, but this
            // keeps resolution order deterministic if it ever happened.
            if (!labels.has(r.row_id)) {
              labels.set(r.row_id, {
                reader_label: buildSnippet(r.citation_human, null, r.row_id),
                grade: 'primary' as CitationGrade,
                source_table: 'chart_divisionals',
                source_column: 'id',
              })
            }
          }
        })
        .catch((err) => {
          faulted = true
          console.error('[pariprashna] citation resolver prefetch failed for chart_divisionals (non-fatal — refs resolve unverified this turn):', err)
        }),
    )

    lookups.push(
      query<{ row_id: string; citation_human: string | null }>(
        `SELECT dasha_row_id::text AS row_id, citation_human
         FROM chart_dashas
         WHERE chart_id = $1 AND dasha_row_id::text = ANY($2::text[])`,
        [chartId, candidates.uuidRefs],
      )
        .then(({ rows }) => {
          for (const r of rows) {
            if (!labels.has(r.row_id)) {
              labels.set(r.row_id, {
                reader_label: buildSnippet(r.citation_human, null, r.row_id),
                grade: 'primary' as CitationGrade,
                source_table: 'chart_dashas',
                source_column: 'dasha_row_id',
              })
            }
          }
        })
        .catch((err) => {
          faulted = true
          console.error('[pariprashna] citation resolver prefetch failed for chart_dashas (non-fatal — refs resolve unverified this turn):', err)
        }),
    )
  }

  if (lookups.length === 0) return { labels, faulted: false }

  await Promise.all(lookups)
  return { labels, faulted }
}

/** Build a synchronous CitationResolver from a pre-fetched label map. */
export function buildTurnCitationResolver(
  labels: ReadonlyMap<string, CandidateSignalLabel>,
): CitationResolver {
  return {
    resolve(ref: string): ResolvedCitation | null {
      const hit = labels.get(ref)
      if (!hit) return null
      return {
        ref,
        reader_label: hit.reader_label,
        grade: hit.grade,
        audit_detail: `resolved from ${hit.source_table} where ${hit.source_column}='${ref}' (this turn's retrieved evidence)`,
      }
    },
    readerLabel(idToken: string): string | null {
      return labels.get(idToken)?.reader_label ?? null
    },
  }
}
