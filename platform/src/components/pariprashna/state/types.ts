/**
 * Paripraśna — core state types.
 *
 * These mirror the wire protocol described in
 * `00_ARCHITECTURE/PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md` §8.3.
 *
 * INTEGRATION NOTE (PB-1/integrate): S-1's real SSE wire protocol
 * (`@/lib/pariprashna/protocol/events` — the canonical, Zod-typed
 * `PariprashnaEvent` union) is now MERGED. `WireEvent` below remains the
 * CLIENT-SIDE reducer action shape (richer/curation-facing than the minimal
 * wire), and `state/s1LiveAdapter.ts` is the seam that maps S-1's real
 * `PariprashnaEvent` → these `WireEvent`s at the live boundary (consumed by
 * `hooks/useLiveStream.ts`, which decodes the real SSE stream via S-1's
 * `decodeEvent`). `fixtures/` + `useFixtureStream` still supply recorded event
 * arrays for local dev / component work through the SAME reducer + components.
 * So the reducer and every component here consume `WireEvent` regardless of
 * whether it came from the live route or a fixture. See s1LiveAdapter's header
 * for the honest list of fields synthesized where S-1's wire is minimal.
 */

import type { StructuredPredictionCandidate } from '@/lib/pariprashna/samiksha/detector'

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
  /**
   * PB-6 (SAMĀPTI): real ISO `yyyy-mm-dd` kāla-rekhā anchors — the geometry is
   * computed live from these by the PURE `computeKalaRekha`
   * (lib/pariprashna/samiksha/kala_rekha.ts), never pre-baked as a fraction.
   * `today` is deliberately NOT stored here — it is read from the real clock
   * at render time (dock/PredictionCard.tsx), so the dot always advances.
   */
  readingDate: string
  windowStart: string
  windowEnd: string
  windowStartLabel: string
  windowEndLabel: string
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
  /**
   * G2-B (PPR-08/FD-2/FD-6). "server" when `gradeSummaryLabel` (and
   * `completenessLine`, when present) were derived from the wire's
   * server-computed `turn.commit.grounding_summary` (the server's own
   * citation-resolution ledger + floor/completeness receipt — never
   * re-derived client-side). "client_estimate" is the DISCLOSED degrade path:
   * the server sent no summary this turn (flag off, or none built), so this
   * turn's rollup is the client's own citation-tally guess and must be
   * labeled as such wherever it is shown — never rendered indistinguishably
   * from a server-derived summary (§N.7 item 6).
   */
  source: 'server' | 'client_estimate'
  /** Server-derived only (`source === 'server'`) — e.g. "4/6 floor items served". */
  completenessLine?: string
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

/**
 * A detected, ALREADY-PERSISTED prediction candidate awaiting the reader's
 * one-tap confirm (lane P2-A / G2-A · FD-4). `partId` is the REAL
 * `message_parts.id` the server minted at commit — never a client-guessed
 * id — so `LogToSamiksha`'s POST to `/api/pariprashna/samiksha/confirm` has
 * a genuine FK to attach to. Arrives via the wire's `prediction_card` event,
 * strictly AFTER the turn's parts are persisted (see
 * `pipeline/persistence_stage.ts`), so it can land any time after that point
 * in the stream — still well before `turn.close`.
 */
export interface PendingPredictionCandidate {
  partId: string
  conversationId: string
  candidate: StructuredPredictionCandidate
}

/**
 * P2-D (PPR-10, FD-9) — the settled_visual/durably_persisted split.
 *
 * `TurnState.status === 'settled'` is SETTLED_VISUAL: the reader sees a
 * finished answer. It says nothing about whether the assistant turn is
 * safely, irrecoverably stored — that is `TurnState.persistence`, tracked
 * SEPARATELY:
 *   'unknown' — no persistence signal has arrived yet (still streaming, or a
 *               pre-P2-D wire that never emits one at all — see below).
 *   'pending' — the write is underway/queued but not yet confirmed. An
 *               HONEST intermediate state, never treated as durable.
 *   'durable' — confirmed safely stored.
 *   'failed'  — the write did not succeed. The turn's PROSE is unaffected
 *               (it already rendered) — this is a storage-durability failure,
 *               not a reading failure.
 *
 * Back-compat note: `turn.commit`'s `status: 'ok'` already meant "the write
 * committed" in the pre-P2-D synchronous persistence path (see
 * pipeline/persistence_stage.ts) — there was never actually a gap in that
 * path, just no wire signal telling the client so. The reducer's `turn.commit`
 * case therefore optimistically resolves `persistence` to 'durable' at commit
 * time (never regressing an already-set value), so a pre-P2-D fixture/stream
 * that never emits `turn.persisted` shows NO incomplete-turn banner — exactly
 * today's behavior. A real `turn.persisted` event (only emitted by the new
 * durable-persistence code path, gated behind
 * `PARIPRASHNA_DURABLE_PERSISTENCE_ENABLED`) can then REFINE that optimistic
 * guess with the true state, including downgrading it back to 'pending'.
 */
export type PersistenceStatus = 'unknown' | 'pending' | 'durable' | 'failed'

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
  /** Detected prediction candidates awaiting the reader's confirm — see
   *  `PendingPredictionCandidate`. Append-only; a candidate is never removed
   *  from this list post-arrival (`LogToSamiksha` tracks its own
   *  confirmed/dismissed UI state internally). */
  pendingPredictionCandidates: PendingPredictionCandidate[]
  /**
   * Lane P2-C (PPR-09/16) — honest depth disclosure. The ACTUAL depth the
   * planner's `scope_tuple` resolved to for this turn (server-derived,
   * `plan_stage.ts`'s `reading_depth_received` grade), distinct from whatever
   * depth the composer requested. `null` until the event arrives — including
   * permanently, on a flag-OFF deploy or a turn the planner never scored — and
   * is rendered as an honest absence, never a guessed value (§N.7 item 6).
   */
  readingDepthReceived: string | null
  /** Most-recently-applied event id (debug/telemetry only — NOT the dedup key). */
  lastEventId: string | null
  /**
   * The set of every event id already applied to this turn — the dedup key.
   * A proper seen-set (not a single-slot last-id) so a NON-adjacent duplicate
   * (e.g. a reconnect replaying an earlier batch) is still recognized and
   * dropped, never double-applied. S-1's `seq` is monotonic + gapless per turn
   * and the live adapter encodes it into each `eventId` (`${turnId}-${seq}`),
   * so id-based dedup subsumes seq-based dedup while also covering the fixture
   * transport (which keys on string event ids).
   */
  seenEventIds: Set<string>
  reconnectHollowCaret: boolean
  /** P2-D (PPR-10, FD-9) — see `PersistenceStatus`'s doc comment. */
  persistence: PersistenceStatus
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
  /**
   * Lane P2-C. Distinct from `grade` above (a different, S-3 citation-tier
   * namespace) — the server's `reading_depth_received` grade subject maps
   * here rather than through `mapGrade`, which has no case for it.
   */
  | { type: 'reading_depth.received'; turnId: string; depth: string; eventId: string }
  | {
      type: 'turn.commit'
      turnId: string
      grounding: GroundingSummary
      eventId: string
      /**
       * P2-D ADDITIVE: the underlying wire `turn.commit.status` ('ok'|'error'),
       * forwarded so the reducer can seed `persistence` honestly (see
       * `PersistenceStatus`). Optional — a pre-P2-D adapter/fixture that never
       * sets this leaves `persistence` at 'unknown' until (if ever) a
       * `turn.persisted` event arrives, which is a strict subset of today's
       * behavior, never a regression (no existing consumer read this before).
       */
      persistStatus?: 'ok' | 'error'
    }
  /** P2-D (PPR-10, FD-9) — see `PersistenceStatus`'s doc comment on TurnState.
   *  Never 'unknown' on the wire — that value means "no signal has arrived",
   *  which is a client-side absence, not something a server ever asserts. */
  | { type: 'turn.persisted'; turnId: string; status: Exclude<PersistenceStatus, 'unknown'>; detail?: string; eventId: string }
  | { type: 'turn.close'; turnId: string; eventId: string }
  | { type: 'error'; turnId: string; error: ClassifiedError; eventId: string }
  | { type: 'reconnecting'; turnId: string; eventId: string }
  | { type: 'reconnected'; turnId: string; eventId: string }
  | { type: 'interrupted'; turnId: string; eventId: string }
  /**
   * PB-2/M-5 ADDITIVE: server-side reconnect (`/api/pariprashna/resume`)
   * fell back to a snapshot because the requested `Last-Event-ID` had
   * already been evicted from the ring buffer. Carries the FULL
   * committed-so-far text as one blob — the reducer REPLACES `blocks`/`tail`
   * wholesale (never appends), so this applies as a single write with no
   * replay animation (B.10: never silently lose data, never duplicate).
   */
  | {
      type: 'snapshot.apply'
      turnId: string
      text: string
      citations: Citation[]
      turnStatus: 'open' | 'closed' | 'interrupted'
      eventId: string
    }
  /**
   * PB-1... lane P2-A / G2-A ADDITIVE: a detected, already-persisted
   * prediction candidate. See `PendingPredictionCandidate` for the field
   * meanings — this is its wire-transport shape.
   */
  | {
      type: 'prediction_card'
      turnId: string
      partId: string
      conversationId: string
      candidate: StructuredPredictionCandidate
      eventId: string
    }

// ── Query controls (composer) ───────────────────────────────────────────

export type DepthOption = 'Auto' | 'Quick' | 'Standard' | 'Deep dive'
export type LengthOption = 'Auto' | 'Concise' | 'Balanced' | 'Detailed'
export interface ModelOption {
  id: string
  label: string
  tier: 'Auto' | 'A' | 'B' | 'C'
  tierNote: string
}

/**
 * Lane P2-C (PPR-09/16) — what the composer actually submits alongside the
 * question, once its three pills stopped being cosmetic. `modelId` is a REAL
 * registry id (`@/lib/models/registry`) or `undefined` for "Auto" (no
 * override — the stack's synthesis primary binds, same as today).
 * `readingDepth`/`lengthTier` are the wire's own request vocabulary
 * (`@/lib/pariprashna/protocol/events`), computed honestly from the picker
 * state rather than smuggled through the dev-fixture `mode` the live host
 * used to reuse for this.
 */
export interface SubmitControls {
  modelId?: string
  readingDepth: 'auto' | 'deep_dive'
  lengthTier: 'brief' | 'standard' | 'exhaustive'
}
