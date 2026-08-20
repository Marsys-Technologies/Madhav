/**
 * Paripraśna — the canonical §7.5 error-copy classifier.
 * ============================================================================
 * P2-G (Edge-state lexicon), roadmap item "PB-4 Lane F-3 / FD-11 / F-25b —
 * fold or delete the second error classifier."
 *
 * ── What this replaces (real evidence, not the spec's phrasing alone) ──────
 * Before this module, THREE independent, hand-authored `ClassifiedError`
 * shapers existed for the Paripraśna surface, none matching the design plan's
 * §7.5 table verbatim:
 *   1. `classifyError()` — an inline function in
 *      `components/pariprashna/state/s1LiveAdapter.ts`, classifying a
 *      server-sent in-stream `error` event's `code` string. Band labels were
 *      ad hoc ("The model is busy — retrying", "Please sign in again",
 *      "Something went wrong") — none is the §7.5 string.
 *   2. THREE separate inline `ClassifiedError` object literals in
 *      `components/pariprashna/hooks/useLiveStream.ts`, hand-built at each of
 *      three synthetic-failure call sites (never received `turn.open`; resume
 *      exhausted after `RECONNECT_MAX_ATTEMPTS`; the initial POST returned a
 *      non-2xx/no body). All three used the SAME placeholder
 *      `bandLabel: 'Something went wrong'` regardless of §7.5's dedicated
 *      network copy.
 *   3. `lib/chat/classify-error.ts` (`classifyChatError`) — a genuinely
 *      SEPARATE, pre-existing classifier for the legacy Consume chat surface
 *      (message-substring matching over a raw `Error`, 7-kind taxonomy incl.
 *      `insufficient_credits`). Grep confirms it is NOT dead code project-wide
 *      — it is imported by
 *      `lib/retrieval/adapters/agentic_loop/{loop_engine,error_recovery}.ts`,
 *      which are outside the Paripraśna surface entirely. It was never wired
 *      into the Paripraśna route (true, per BRIEF_PB-4 Lane F-3's framing),
 *      but it is not abandoned/unused code overall, so it is left untouched
 *      here — deleting a classifier with real non-Paripraśna callers is a
 *      Gate-7/F-5 residue-sweep decision (FD-11), not this lane's to make,
 *      and `lib/chat/**` is outside this lane's declared scope
 *      (`may_touch: components/pariprashna/**, lib/pariprashna/** (error-
 *      classifier fold/delete only)`).
 *
 * This module FOLDS (1) and (2) into ONE canonical classifier, reusing
 * `classify-error.ts`'s taxonomy shape (`kind` enum + structured result) —
 * the "adopt, don't rewrite" instruction from BRIEF_PB-4 Lane F-3 — while
 * reimplementing the matching logic, because the input differs (an in-stream
 * `code` string here vs. a thrown `Error`'s `message` there) and because
 * `ClassifiedErrorKind` (state/types.ts) is a 6-member subset of
 * `ChatErrorKind` (no `insufficient_credits` — Paripraśna's wire protocol has
 * no such code today). `hooks/useLiveStream.ts` and `state/s1LiveAdapter.ts`
 * both now call THIS module instead of hand-building `ClassifiedError`
 * literals — see the diff on both files.
 *
 * ── Source of truth ──────────────────────────────────────────────────────
 * `PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md` §7.5 "Error copy
 * (classify-error taxonomy → display language)" — every `bandLabel` and
 * `sentence` below is quoted verbatim from that table. Per the closed-lexicon
 * convention already established in `lib/pariprashna/lexicon.ts` (§7.8's
 * module), strings are authored in NATURAL (sentence) case; the client's CSS
 * applies tracked-caps at render time — this module never upper-cases.
 *
 * Rule from §7.5 itself: "never blame the user; always state what was
 * preserved; exactly one sentence + actions" — and separately, §7.8's edge
 * states table: "Never: raw provider error strings." So `sentence` below is
 * ALWAYS the fixed §7.5 copy; the raw in-stream `message`/`code` is used only
 * to CLASSIFY (which `kind`), never surfaced to the reader.
 */

export type PariprashnaErrorKind = 'rate_limit' | 'model_overload' | 'timeout' | 'network' | 'auth' | 'unknown'

export type PariprashnaErrorAction = 'retry' | 'switch_model' | 'continue' | 'settings'

export interface PariprashnaClassifiedError {
  kind: PariprashnaErrorKind
  bandLabel: string
  sentence: string
  actions: PariprashnaErrorAction[]
}

export interface ClassifyErrorOptions {
  /**
   * Reader-facing provider display name (e.g. "Anthropic") for the
   * `model_overload` sentence template ("⟨Provider⟩ is under load…"). Omitted
   * → the generic "The provider" — an honest gap (§N.7.6: an honest null
   * beats an invented judgment) rather than guessing a provider name from
   * data this classifier does not reliably have.
   */
  providerLabel?: string
  /**
   * True (default) if this `network`-kind failure is TERMINAL — retries
   * exhausted or moot, so the band shows §7.5's "connection was lost" copy.
   * False mid-attempt reuses §7.8's `RECONNECTING…` edge-state label (the
   * in-progress state; not a failure yet). The two live states this maps to
   * are `EDGE_STATE_LABELS.network_drop` / a still-retrying network kind —
   * kept as a literal string here (not imported from `lexicon.ts`) to keep
   * this module dependency-free of the UI lexicon module; the two strings
   * are asserted equal in `__tests__/classify.test.ts`.
   */
  networkExhausted?: boolean
  /**
   * `auth` splits by audience per §7.5: native sees "renew in settings",
   * guest sees the switch-model framing. No caller today has audience
   * context at the point this classifier runs (the client's in-stream error
   * path and the synthetic network-failure sites in `useLiveStream.ts` carry
   * no entitlement signal) — defaults to `'native'`, matching the pre-
   * existing behaviour (the old inline classifiers always offered a
   * `'settings'` action for auth failures, never `'switch_model'`). This is a
   * documented gap, not a fabricated audience split.
   */
  audience?: 'native' | 'guest'
}

/** Best-effort `kind` classification from an in-stream error `code` (or a
 *  synthetic code string a caller mints for a client-side failure — see
 *  `useLiveStream.ts`'s three call sites). Case-insensitive substring match,
 *  same style as the two classifiers this replaces. */
function classifyKind(code: string): PariprashnaErrorKind {
  const c = code.toLowerCase()
  if (c.includes('rate') || c.includes('429')) return 'rate_limit'
  if (c.includes('overload') || c.includes('capacity') || c.includes('503') || c.includes('529')) {
    return 'model_overload'
  }
  if (c.includes('timeout') || c.includes('deadline')) return 'timeout'
  if (c.includes('network') || c.includes('fetch') || c.includes('econn') || c.includes('resume') || c.includes('httpfail')) {
    return 'network'
  }
  if (c.includes('auth') || c.includes('401') || c.includes('403')) return 'auth'
  return 'unknown'
}

/** §7.5 verbatim copy, keyed by kind. */
function copyFor(
  kind: PariprashnaErrorKind,
  opts: ClassifyErrorOptions
): Pick<PariprashnaClassifiedError, 'bandLabel' | 'sentence' | 'actions'> {
  switch (kind) {
    case 'rate_limit':
      return {
        bandLabel: 'A moment — the provider asks us to slow',
        sentence: 'Nothing was lost. Try again shortly, or switch models.',
        actions: ['retry', 'switch_model'],
      }
    case 'model_overload':
      return {
        bandLabel: 'The model is overloaded',
        sentence: `${opts.providerLabel ?? 'The provider'} is under load. Your question is kept; another model can take it.`,
        actions: ['retry', 'switch_model'],
      }
    case 'timeout':
      return {
        bandLabel: 'The reading ran long and was cut short',
        sentence: 'What arrived is above. The reading can be continued.',
        actions: ['continue', 'retry'],
      }
    case 'network':
      return opts.networkExhausted === false
        ? {
            bandLabel: 'Reconnecting…',
            sentence: 'What arrived is above; nothing was altered.',
            actions: ['continue'],
          }
        : {
            bandLabel: 'The connection was lost',
            sentence: 'What arrived is above; nothing was altered.',
            actions: ['continue'],
          }
    case 'auth':
      return opts.audience === 'guest'
        ? {
            bandLabel: 'This model is unavailable',
            sentence: 'Another model can take the question.',
            actions: ['switch_model'],
          }
        : {
            bandLabel: 'This model needs its key renewed',
            sentence: 'Renew in settings.',
            actions: ['settings'],
          }
    case 'unknown':
    default:
      return {
        bandLabel: 'Something failed on our side',
        sentence: 'Not the chart, not your question — the plumbing. It is logged.',
        actions: ['retry'],
      }
  }
}

/**
 * Classify an in-stream (or synthesized client-side) error `code` into the
 * §7.5 canonical band label, sentence, and action set. This is the ONLY
 * place a Paripraśna `ClassifiedError` should be constructed — every call
 * site imports this rather than hand-building the shape.
 */
export function classifyPariprashnaError(
  code: string,
  opts: ClassifyErrorOptions = {}
): PariprashnaClassifiedError {
  const kind = classifyKind(code)
  return { kind, ...copyFor(kind, opts) }
}
