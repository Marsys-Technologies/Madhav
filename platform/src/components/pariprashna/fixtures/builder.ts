import type {
  Citation,
  PredictionCardData,
  ReadingRole,
  TableBlockContent,
  WireEvent,
} from '../state/types'
import type { ScheduledEvent } from './types'

let eventSeq = 0
function nextEventId(): string {
  eventSeq += 1
  return `ev_${eventSeq}`
}

/**
 * A tiny imperative DSL for writing readable fixture scripts. Every `at*`
 * method appends one or more `ScheduledEvent`s at the builder's current
 * cursor time, then advances the cursor by the given duration — so a
 * fixture script reads top-to-bottom in wall-clock order, same as the
 * mockup's own `PASSES` timeline.
 */
export class FixtureBuilder {
  private t = 0
  private out: ScheduledEvent[] = []
  constructor(private turnId: string) {}

  private push(event: WireEvent, atMs?: number) {
    this.out.push({ atMs: atMs ?? this.t, event })
  }

  cursor(): number {
    return this.t
  }

  advance(ms: number) {
    this.t += ms
  }

  turnOpen(userText: string) {
    this.push({ type: 'turn.open', turnId: this.turnId, userText, eventId: nextEventId() })
  }

  phase(label: string) {
    this.push({ type: 'phase', turnId: this.turnId, label, eventId: nextEventId() })
  }

  /** One reasoning/tool activity row: appears "running", flips to "done" after `durationMs`. */
  activity(opts: {
    id: string
    passIndex: number
    label: string
    detail?: string
    kind: 'reasoning' | 'tool'
    durationMs: number
    ms: string
  }) {
    const startAt = this.t
    this.push(
      {
        type: 'activity.upsert',
        turnId: this.turnId,
        row: { id: opts.id, passIndex: opts.passIndex, label: opts.label, detail: opts.detail, kind: opts.kind, status: 'running' },
        eventId: nextEventId(),
      },
      startAt,
    )
    this.push(
      {
        type: 'activity.upsert',
        turnId: this.turnId,
        row: { id: opts.id, passIndex: opts.passIndex, label: opts.label, detail: opts.detail, kind: opts.kind, status: 'done', ms: opts.ms },
        eventId: nextEventId(),
      },
      startAt + opts.durationMs,
    )
    this.advance(opts.durationMs)
  }

  seamOpen(passIndex: number, liveLabel: string, blockId: string) {
    this.push({ type: 'pass.seam.open', turnId: this.turnId, passIndex, liveLabel, blockId, eventId: nextEventId() })
  }

  seamSettle(blockId: string, summary: string) {
    this.push({ type: 'pass.seam.settle', turnId: this.turnId, blockId, summary, eventId: nextEventId() })
  }

  citation(citation: Citation, atMs?: number) {
    this.push({ type: 'citation.define', turnId: this.turnId, citation, eventId: nextEventId() }, atMs)
  }

  /** Streams a paragraph/list block token-by-token (space-preserving split, matching the mockup's `typeInto`). */
  streamedBlock(opts: { blockId: string; role?: ReadingRole; text: string; tokenIntervalMs?: number }) {
    const interval = opts.tokenIntervalMs ?? 32
    this.push({ type: 'block.open', turnId: this.turnId, blockId: opts.blockId, kind: 'paragraph', role: opts.role, eventId: nextEventId() })
    const tokens = opts.text.split(/(?<=\s)/)
    let acc = ''
    for (const tok of tokens) {
      acc += tok
      this.push({ type: 'block.delta', turnId: this.turnId, blockId: opts.blockId, textDelta: tok, eventId: nextEventId() })
      this.advance(interval)
    }
    this.push({
      type: 'block.commit',
      turnId: this.turnId,
      blockId: opts.blockId,
      kind: 'paragraph',
      role: opts.role,
      html: acc,
      eventId: nextEventId(),
    })
  }

  /** Commit-only block types (tables, verse, gap ribbon, prediction card, headings): arrive whole. */
  commitOnlyBlock(opts: {
    blockId: string
    kind: 'table' | 'verse' | 'gap_ribbon' | 'prediction_card' | 'heading'
    role?: ReadingRole
    html?: string
    table?: TableBlockContent
    gapText?: string
    prediction?: PredictionCardData
  }) {
    this.push({
      type: 'block.commit',
      turnId: this.turnId,
      blockId: opts.blockId,
      kind: opts.kind,
      role: opts.role,
      html: opts.html,
      table: opts.table,
      gapText: opts.gapText,
      prediction: opts.prediction,
      eventId: nextEventId(),
    })
  }

  turnCommit(grounding: WireEvent extends { type: 'turn.commit'; grounding: infer G } ? G : never) {
    this.push({ type: 'turn.commit', turnId: this.turnId, grounding, eventId: nextEventId() })
  }

  turnClose() {
    this.push({ type: 'turn.close', turnId: this.turnId, eventId: nextEventId() })
  }

  reconnecting() {
    this.push({ type: 'reconnecting', turnId: this.turnId, eventId: nextEventId() })
  }

  reconnected() {
    this.push({ type: 'reconnected', turnId: this.turnId, eventId: nextEventId() })
  }

  build(): ScheduledEvent[] {
    return this.out.sort((a, b) => a.atMs - b.atMs)
  }
}
