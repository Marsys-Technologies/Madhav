/**
 * tool_verbs.ts — C-S5 R11.C
 *
 * Maps Marsys tool names to human-readable verb labels for ToolCallCard.
 * Pattern follows Claude's "Used <Verb>" pattern (e.g., "Looked up ephemeris").
 *
 * The label appears in the ToolCallCard header as:
 *   "Looked up panchang" (running: "Looking up panchang…")
 *
 * Unmapped tools fall back to the raw tool name with "Used" prefix.
 *
 * Maintained: add new tool names here when new tools are registered in the
 * retrieve layer (platform/src/lib/retrieve/index.ts).
 */

export interface ToolVerbEntry {
  /** Label for a completed tool call. */
  done: string
  /** Label while the tool call is still running. */
  running: string
}

/** Per-tool verb labels indexed by tool name. */
const TOOL_VERBS: Record<string, ToolVerbEntry> = {
  // ─── Panchang ──────────────────────────────────────────────────────────────
  query_panchanga: { done: 'Looked up panchang', running: 'Looking up panchang…' },
  muhurat_finder: { done: 'Found muhurat windows', running: 'Finding muhurat windows…' },

  // ─── Ephemeris ─────────────────────────────────────────────────────────────
  query_ephemeris: { done: 'Queried ephemeris', running: 'Querying ephemeris…' },
  query_transit_event: { done: 'Looked up transit events', running: 'Looking up transit events…' },
  query_dasha_periods: { done: 'Fetched dasha periods', running: 'Fetching dasha periods…' },

  // ─── Chart facts ───────────────────────────────────────────────────────────
  query_chart_facts: { done: 'Read chart facts', running: 'Reading chart facts…' },
  get_cgm_subgraph: { done: 'Walked the CGM graph', running: 'Walking CGM graph…' },
  cross_school_lookup: { done: 'Cross-referenced schools', running: 'Cross-referencing schools…' },

  // ─── Signals ───────────────────────────────────────────────────────────────
  query_signals: { done: 'Retrieved signals', running: 'Retrieving signals…' },
  vector_search: { done: 'Searched signal corpus', running: 'Searching signal corpus…' },
  lel_query: { done: 'Queried life events', running: 'Querying life events…' },

  // ─── Predictions ───────────────────────────────────────────────────────────
  log_prediction: { done: 'Logged prediction', running: 'Logging prediction…' },
  record_outcome: { done: 'Recorded outcome', running: 'Recording outcome…' },

  // ─── Observatory ───────────────────────────────────────────────────────────
  get_trace: { done: 'Fetched trace', running: 'Fetching trace…' },
  list_recent_queries: { done: 'Listed recent queries', running: 'Listing recent queries…' },

  // ─── Classical texts ───────────────────────────────────────────────────────
  read_classical_text: { done: 'Read classical text', running: 'Reading classical text…' },
  read_asset: { done: 'Read asset', running: 'Reading asset…' },

  // ─── Meta ──────────────────────────────────────────────────────────────────
  ask_madhav: { done: 'Consulted Madhav', running: 'Consulting Madhav…' },
  plan_query: { done: 'Planned query', running: 'Planning query…' },
  execute_plan: { done: 'Executed plan', running: 'Executing plan…' },
  flag_disagreement: { done: 'Flagged disagreement', running: 'Flagging disagreement…' },

  // ─── Tool health ───────────────────────────────────────────────────────────
  tool_health: { done: 'Checked tool health', running: 'Checking tool health…' },
  data_coverage: { done: 'Checked data coverage', running: 'Checking data coverage…' },
}

/**
 * Returns the verb label for a given tool name.
 * Falls back to `{ done: 'Used <toolName>', running: 'Using <toolName>…' }` for unmapped tools.
 */
export function getToolVerb(toolName: string): ToolVerbEntry {
  return TOOL_VERBS[toolName] ?? {
    done: `Used ${toolName}`,
    running: `Using ${toolName}…`,
  }
}

/** Returns all registered tool names (for testing + documentation). */
export function getRegisteredToolNames(): string[] {
  return Object.keys(TOOL_VERBS)
}
