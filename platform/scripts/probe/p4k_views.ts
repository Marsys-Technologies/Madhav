/**
 * p4k_views.ts — the six Kāla views, empirically enumerated (P4-K, PARIPRASHNA_P3_P4
 * overnight run, lane p4-k).
 *
 * NOT invented for this audit. Sourced from `platform-mcp/src/resources/vidhi/
 * registry_data.ts` (the `now_read`/`ahead_read`/`elect_read`/`story_read`/
 * `priority_read`/`explain_read` primitive rows, "ṢAḌ-DARŚANA W5 primitives" block) and
 * `00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/SHAD_DARSHANA_BRIEF_v2_0.md`
 * §1 ("Eight tools: six views (`kala_now_get`, `kala_ahead_get`, `kala_elect_get`,
 * `kala_story_get`, `kala_priority_get`, `kala_explain_get`) + two capabilities
 * (`kala_upaya_get`, `kala_ritual_get`)"). `kala_upaya_get`/`kala_ritual_get` are
 * CAPABILITIES, not views, per that same source — excluded here on purpose.
 *
 * The roadmap names this audit "the post-six-views narration audit... against the
 * now-settled Kāla layer" (G8-G / GAP-18, `PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md`
 * line 188) — this file is the harness's single source of truth for what those six
 * views are, so the driver and the analyzer never drift from each other or from a
 * hand-typed list re-guessed at each call site.
 *
 * The SEQUENCE below is a deliberate reader-movement order, not the registry's
 * arbitrary listing order: NOW -> AHEAD -> PRIORITIZE mirrors the "machine-band
 * default... compiled into every domain deepdive alongside" grouping the registry
 * itself declares (now_read + ahead_read + priority_read travel together); STORY
 * follows as the life-arc read a reader naturally reaches for next; ELECT is the
 * "when should I act" question a reader asks once they understand where they stand;
 * EXPLAIN closes the loop by asking the assistant to justify a specific claim already
 * made earlier in the SAME thread — operationalizing the registry's own "every served
 * row id pre-authorizes one EXPLAIN hop" rule (registry_data.ts, explain_read
 * definition) as a real cross-turn probe, not just a design note.
 */

export type ViewLabel = 'NOW' | 'AHEAD' | 'PRIORITIZE' | 'STORY' | 'ELECT' | 'EXPLAIN'

export interface ViewSpec {
  view: ViewLabel
  /** vidhi compiler primitive_id, per registry_data.ts. */
  primitive_id: string
  /** the live MCP tool the primitive compiles to. */
  live_tool: string
  /** the question_frame this view answers, verbatim from registry_data.ts's own
   *  definition string (the "VIEW N — LABEL (\"...\")" quoted frame). */
  question_frame: string
  /** the natural-language question this harness actually sends through the live
   *  conversation door (`/api/pariprashna`) to elicit that view. A reader-phrased
   *  question, not a tool call — the audit tests the SERVED SURFACE, not the MCP
   *  tool directly. */
  probe_question: string
}

export const SIX_VIEWS: ViewSpec[] = [
  {
    view: 'NOW',
    primitive_id: 'now_read',
    live_tool: 'kala_now_get',
    question_frame: 'what is my temporal state right now?',
    probe_question:
      "What is my temporal state right now — what's active for me at this moment?",
  },
  {
    view: 'AHEAD',
    primitive_id: 'ahead_read',
    live_tool: 'kala_ahead_get',
    question_frame: 'what is coming?',
    probe_question: 'What is coming for me over the next few months?',
  },
  {
    view: 'PRIORITIZE',
    primitive_id: 'priority_read',
    live_tool: 'kala_priority_get',
    question_frame: 'what matters most right now?',
    probe_question: 'Of everything going on in my chart right now, what matters most?',
  },
  {
    view: 'STORY',
    primitive_id: 'story_read',
    live_tool: 'kala_story_get',
    question_frame: 'what has my life been?',
    probe_question: 'What has my life been like so far, as this chart tells it?',
  },
  {
    view: 'ELECT',
    primitive_id: 'elect_read',
    live_tool: 'kala_elect_get',
    question_frame: 'when should I…?',
    probe_question: 'When should I start a new business venture?',
  },
  {
    view: 'EXPLAIN',
    primitive_id: 'explain_read',
    live_tool: 'kala_explain_get',
    question_frame: 'why do you say that?',
    // Deliberately references the FIRST turn's claim by natural back-reference
    // ("what's active for me right now") rather than a fresh topic — this is the
    // "every served row id pre-authorizes one EXPLAIN hop" rule (registry_data.ts)
    // exercised as a real cross-turn probe: does EXPLAIN actually re-open the NOW
    // claim's own causal chain, or does it drift onto unrelated material?
    probe_question:
      "Why do you say that about what's active for me right now — what's the reasoning, step by step?",
  },
]

export const SYNTHETIC_TEST_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
