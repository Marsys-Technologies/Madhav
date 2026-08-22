import 'server-only'
/**
 * The window-opening ask — THE TURN HOOK (lane P4-G).
 *
 * One function, called once per turn from the plan stage before the planner runs. It does the
 * two halves of the loop in the one order they can legally happen in:
 *
 *   1. CAPTURE any answer this turn carries to an ask made on a PREVIOUS turn, and
 *   2. EVALUATE whether to raise a new ask, and emit it if so.
 *
 * The order matters and is not arbitrary. Capture runs first so that a window resolved by this
 * very turn's answer is no longer selectable when step 2 looks for something to ask about —
 * otherwise the instrument would answer a question and then immediately re-ask it. Because the
 * selector is deterministic and totally ordered, step 2 naturally moves on to the next oldest
 * unresolved window, or falls silent.
 *
 * ── HOW THE ANSWER FINDS ITS WAY BACK (and the honest limit of what is wired) ───────────────
 * The correlation handle is the ask's own `ledger_row_id`, carried on the `window_ask` wire
 * event and echoed back by the client in `body.window_ask_answer`. This is exactly the
 * established `prediction_card` → `/api/pariprashna/samiksha/confirm` pattern: the server
 * hands out an opaque id with the affordance, the client hands it back with the reader's act.
 * No new table, no server-side guessing about which ask a message might be answering.
 *
 * The CLIENT half of that echo is not built by this lane — `components/pariprashna/**` is
 * outside its declared `may_touch`, and `prediction_card` itself shipped this same way (the
 * event landed, the client mount followed in a later lane). What that means precisely:
 *   · the ask fires, composes and reaches the wire — wired, and observable;
 *   · the answer reaches the ledger through `captureWindowAnswer` — wired, and observable;
 *   · the browser round-trip between the two — NOT wired. It is one field on the submit body
 *     in `components/pariprashna/hooks/useLiveStream.ts` plus a renderer for the event.
 * Stated here rather than in a report so the next reader of this file learns it from the file.
 *
 * ── FAILURE POSTURE ────────────────────────────────────────────────────────────────────────
 * Everything here is strictly non-fatal. An unsolicited sentence is a courtesy the instrument
 * pays the reader; it must never be able to cost them the reading they actually asked for. Any
 * throw is caught, logged, and the turn proceeds as though the feature did not exist.
 */

import type { PariprashnaEmitter } from '../../protocol/emitter'
import type { TurnParams } from '../../pipeline/stage_context'
import { evaluateWindowAsk } from './select'
import { captureWindowAnswer } from './capture'
import { isWindowAskEnabled } from './flag'

/** What the hook did this turn. Returned for tests and probes; the route ignores it. */
export interface WindowAskTurnHookResult {
  captured: Awaited<ReturnType<typeof captureWindowAnswer>> | null
  decision: Awaited<ReturnType<typeof evaluateWindowAsk>> | null
  emitted: boolean
}

/** UTC today as ISO `yyyy-mm-dd` — the selector's notion of "now". */
function todayIso(): string {
  return new Date().toISOString().slice(0, 10)
}

export async function runWindowAskTurnHook(args: {
  em: PariprashnaEmitter
  chartId: string
  conversationId: string
  params: TurnParams
  /** Test/probe seam ONLY; production reads the flag from the environment. */
  forceEnabled?: boolean
  /** Test/probe seam ONLY; production uses today. */
  asOf?: string
}): Promise<WindowAskTurnHookResult> {
  const enabled = args.forceEnabled ?? isWindowAskEnabled()
  const result: WindowAskTurnHookResult = { captured: null, decision: null, emitted: false }
  if (!enabled) return result

  const asOf = args.asOf ?? todayIso()

  // ── 1. Capture an answer to a PRIOR ask, if this turn carries one. ──
  const answer = args.params.windowAskAnswer
  if (answer) {
    try {
      result.captured = await captureWindowAnswer({
        ledgerRowId: answer.ledgerRowId,
        answerText: answer.text,
        chartId: args.chartId,
      })
      // Logged at info even on a refusal: a refusal is a DECISION the loop made, not an error,
      // and "the reader answered and nothing was recorded" is precisely the thing an operator
      // needs to be able to see. `reading.rule` names which rule refused.
      console.info(
        `[pariprashna/window_ask] answer captured: recorded=${result.captured.recorded} ` +
          `kind=${result.captured.reading.kind} rule=${result.captured.reading.rule} ` +
          `reason=${result.captured.not_recorded_reason ?? '-'} ` +
          `status_after=${result.captured.lifecycle_status_after}`,
      )
    } catch (err) {
      console.error('[pariprashna/window_ask] answer capture failed (non-fatal)', err)
    }
  }

  // ── 2. Raise a new ask, if there is a genuinely closed window to raise. ──
  try {
    const decision = await evaluateWindowAsk({ chartId: args.chartId, asOf, forceEnabled: true })
    result.decision = decision
    if (!decision.fired) {
      console.info(
        `[pariprashna/window_ask] no ask: reason=${decision.reason} — ${decision.detail}`,
      )
      return result
    }
    args.em.windowAsk({
      conversation_id: args.conversationId,
      ledger_row_id: decision.ask.ledgerRowId,
      ask_text: decision.ask.text,
      options: decision.ask.options.map((o) => ({ key: o.key, label: o.label })),
      composition: decision.ask.composition,
    })
    result.emitted = true
    console.info(
      `[pariprashna/window_ask] ask raised for ledger row ${decision.ask.ledgerRowId} ` +
        `(window last day ${decision.ask.derivedFrom.window_last_day})`,
    )
  } catch (err) {
    console.error('[pariprashna/window_ask] ask evaluation/emission failed (non-fatal)', err)
  }

  return result
}
