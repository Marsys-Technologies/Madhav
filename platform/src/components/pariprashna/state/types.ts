/**
 * Paripraśna — core state types.
 *
 * These mirror the wire protocol described in
 * `00_ARCHITECTURE/PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md` §8.3.
 *
 * STUB NOTE: the real SSE wire (server → client event stream) does not exist
 * in this worktree yet — that is lane S-1's job. This module defines the
 * *shape* the reducer consumes; `fixtures/` supplies recorded event arrays
 * that a real server would eventually emit, and `useFixtureStream` replays
 * them with timing so the renderer can be built and demoed against them.
 * When S-1 lands a live stream, only the transport (EventSource / fetch
 * stream → dispatch) needs to change — the reducer and every component here
 * consume `WireEvent` regardless of where it came from.
 */

// ── Roles / grades / block kinds ────────────────────────────────────────────

export type ReadingRole = 'verdict' | 'elaboration' | 'verse' | 'caveat'

export type BlockKind =
  | 'paragraph'
  | 'heading'
  | 'list'
  | 'table'
  | 'verse'
  | 'gap_ribbon'
  | 'prediction_card'
  | 'seam' // pass-seam divider — our extension, see §5.8.1 ruling 8a

export type Grade = 'confirmed' | 'supported' | 'catalog' | 'honest_gap'

export interface Citation {
  n: number
  title: string
  sourceClass: 'chart_factor' | 'classical_source' | 'computed_window'
  relevance: string
  ref: string // mono ref line, e.g. "BPHS 34.12" or an entitled fact ref
  grade: Grade
}

export interface ActivityRow {
  id: string
  passIndex: number
  label: string
  detail?: string // e.g. "career · timing · 24 months" (reason) or a count
  kind: 'reasoning' | 'tool'
  status: 'running' | 'done'
  ms?: string
}

export interface TableBlockContent {
  headers: string[]
  rows: string[][]
}

export interface CommittedBlock {
  id: string
  kind: BlockKind
  role?: ReadingRole
  html: string // reader-safe HTML/text with citation sentinels already resolved to chip markup tokens
  table?: TableBlockContent
  gapText?: string
  prediction?: PredictionCardData
  seamSummary?: string // for kind === 'seam': the settled divider text
}

export interface PredictionCardData {
  id: string
  claim: string
  windowStartLabel: string
  windowEndLabel: string
  todayFractionOfSpan: number // 0..1 position of "today" dot across [span start, span end]
  windowStartFraction: number // 0..1 start of the gold window segment
  windowEndFraction: number // 0..1 end of the gold window segment
  confidencePhrase: string
  ref: string
  lifecycle: 'window_open' | 'window_closing' | 'awaiting_outcome' | 'resolved_confirmed' | 'resolved_missed' | 'resolved_mixed'
}

export interface GroundingSummary {
  factorCount: number
  classicalCount: number
  elapsedLabel: string
  compositionNote?: string // "Composed from complete house coverage" (dossier route)
  gradeSummaryLabel: string // "Core claim: WELL-GROUNDED" | "Honest gap — silence verified…"
}

export type ClassifiedErrorKind =
  | 'rate_limit'
  | 'model_overload'
  | 'timeout'
  | 'network'
  | 'auth'
  | 'unknown'

export interface ClassifiedError {
  kind: ClassifiedErrorKind
  bandLabel: string
  sentence: string
  actions: Array<'retry' | 'switch_model' | 'continue' | 'settings'>
}

export type TurnStatus =
  | 'submitted'
  | 'thinking'
  | 'streaming'
  | 'reconnecting'
  | 'settling'
  | 'settled'
  | 'interrupted'
  | 'errored'

export interface ActiveSeam {
  blockId: string
  passIndex: number
  liveLabel: string // "Looking further — the divisional charts…"
}

export interface TailBlock {
  blockId: string
  kind: Extract<BlockKind, 'paragraph' | 'list'>
  role?: ReadingRole
  text: string // accumulated committed-so-far text (already citation-token-resolved)
}

export interface TurnState {
  id: string
  userText: string
  status: TurnStatus
  phaseLabel: string
  passIndex: number
  /**
   * Client clock anchor (§8.5 "Elapsed counters: client clock from
   * turn.open receipt, no per-second wire chatter"). WorkingBand derives
   * its own live "· Ns" display from this with a local interval — elapsed
   * time never round-trips through the reducer, so a ticking clock cannot
   * cause a transcript-wide re-render.
   */
  openedAtMs: number
  activities: ActivityRow[]
  blocks: CommittedBlock[]
  tail: TailBlock | null
  activeSeam: ActiveSeam | null
  citations: Record<number, Citation>
  grounding: GroundingSummary | null
  error: ClassifiedError | null
  lastEventId: string | null
  reconnectHollowCaret: boolean
}

export type SurfaceStatus = 'empty' | 'idle' | 'composing'

export interface ThreadState {
  turns: TurnState[]
  surfaceStatus: SurfaceStatus
}

// ── Wire events ──────────────────────────────────────────────────────────
// Matches §8.3's canonical event list, plus the seam extension (our stub).

export type WireEvent =
  | { type: 'turn.open'; turnId: string; userText: string; eventId: string }
  | { type: 'phase'; turnId: string; label: string; eventId: string }
  | {
      type: 'activity.upsert'
      turnId: string
      row: Pick<ActivityRow, 'id' | 'passIndex' | 'label' | 'detail' | 'kind'> & { status?: ActivityRow['status']; ms?: string }
      eventId: string
    }
  | {
      type: 'pass.seam.open'
      turnId: string
      passIndex: number
      liveLabel: string
      blockId: string
      eventId: string
    }
  | {
      type: 'pass.seam.settle'
      turnId: string
      blockId: string
      summary: string
      eventId: string
    }
  | {
      type: 'block.open'
      turnId: string
      blockId: string
      kind: BlockKind
      role?: ReadingRole
      eventId: string
    }
  | { type: 'block.delta'; turnId: string; blockId: string; textDelta: string; eventId: string }
  | {
      type: 'block.commit'
      turnId: string
      blockId: string
      kind: BlockKind
      role?: ReadingRole
      html?: string
      table?: TableBlockContent
      gapText?: string
      prediction?: PredictionCardData
      eventId: string
    }
  | { type: 'citation.define'; turnId: string; citation: Citation; eventId: string }
  | { type: 'flag'; turnId: string; flag: string; eventId: string }
  | { type: 'grade'; turnId: string; grade: Grade; note?: string; eventId: string }
  | { type: 'turn.commit'; turnId: string; grounding: GroundingSummary; eventId: string }
  | { type: 'turn.close'; turnId: string; eventId: string }
  | { type: 'error'; turnId: string; error: ClassifiedError; eventId: string }
  | { type: 'reconnecting'; turnId: string; eventId: string }
  | { type: 'reconnected'; turnId: string; eventId: string }
  | { type: 'interrupted'; turnId: string; eventId: string }

// ── Query controls (composer) ───────────────────────────────────────────

export type DepthOption = 'Auto' | 'Quick' | 'Standard' | 'Deep dive'
export type LengthOption = 'Auto' | 'Concise' | 'Balanced' | 'Detailed'
export interface ModelOption {
  id: string
  label: string
  tier: 'Auto' | 'A' | 'B' | 'C'
  tierNote: string
}
