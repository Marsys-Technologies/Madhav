// Paripraśna acceptance harness — reference reducer.
//
// Plain ES module (not TypeScript) so it can be loaded two ways with zero
// build step:
//   1. `import` from vitest (tests/pariprashna/reducer/golden.test.ts) for
//      determinism/idempotency assertions;
//   2. `<script type="module" src="/reducer.mjs">` directly in the harness
//      browser page (tests/pariprashna/harness/public/client.mjs) — no
//      bundler in the loop for a test-only stub.
//
// The reducer is intentionally the ONLY place that understands the wire
// protocol's state-machine rules (block lifecycle, seam resolution,
// duplicate-id dedup). Both the golden test and the DOM harness call the
// exact same `applyEvent` function, so a bug caught by one is a bug the
// other would have hit too.
//
// Contract (mirrors src/lib/pariprashna/protocol/events.ts):
//  - Events may redeliver. Dedup key is `event.id`; a repeated id is a no-op.
//  - A `block.delta` or `block.commit` targeting an already-committed block
//    is a PROTOCOL VIOLATION — the reducer throws. This is the enforcement
//    point behind G-TRANSMUTE: if this never throws in real use, no delta
//    can ever mutate settled DOM.
//  - Unknown/malformed events are the caller's problem (see
//    `safeParseEvent` in events.ts) — this reducer assumes it is only ever
//    fed already-validated events via `applyEvent`, but exposes
//    `applyRawEvent` for callers that want the reducer itself to no-op
//    (rather than throw) on schema-invalid input, counting it in
//    `state.malformed_dropped`.

/**
 * @typedef {Object} BlockState
 * @property {string} id
 * @property {string} kind
 * @property {number} index
 * @property {string} text
 * @property {boolean} committed
 * @property {string|undefined} final_text
 */

/**
 * @typedef {Object} ReducerState
 * @property {string|null} turn_id
 * @property {string|null} phase
 * @property {Map<string, BlockState>} blocks
 * @property {string[]} block_order
 * @property {Map<string, object>} activities   // key -> latest row
 * @property {string[]} activity_order          // first-seen order of keys
 * @property {Map<string, object>} seams         // seam_id -> {block_id, anchor_offset, citation_id}
 * @property {Map<string, object>} citations     // citation_id -> definition
 * @property {object[]} flags
 * @property {object[]} grades
 * @property {object|null} turn_commit
 * @property {object|null} turn_close
 * @property {Set<string>} applied_ids           // dedup set
 * @property {number} events_applied             // count of NON-duplicate, non-dropped events
 * @property {number} duplicates_dropped
 * @property {number} malformed_dropped
 * @property {string[]} violations                // protocol violations detected (does not throw in tolerant mode)
 */

/** @returns {ReducerState} */
export function createInitialState() {
  return {
    turn_id: null,
    phase: null,
    blocks: new Map(),
    block_order: [],
    activities: new Map(),
    activity_order: [],
    seams: new Map(),
    citations: new Map(),
    flags: [],
    grades: [],
    turn_commit: null,
    turn_close: null,
    applied_ids: new Set(),
    events_applied: 0,
    duplicates_dropped: 0,
    malformed_dropped: 0,
    violations: [],
  }
}

/**
 * Apply one already-validated event to state, mutating and returning it.
 * Throws on a genuine protocol violation (delta/commit targeting an
 * already-committed block) when `opts.strict` (default true).
 *
 * @param {ReducerState} state
 * @param {any} event
 * @param {{ strict?: boolean }} [opts]
 * @returns {ReducerState}
 */
export function applyEvent(state, event, opts = {}) {
  const strict = opts.strict !== false

  if (!event || typeof event.id !== 'string') {
    state.malformed_dropped += 1
    return state
  }

  if (state.applied_ids.has(event.id)) {
    state.duplicates_dropped += 1
    return state
  }
  state.applied_ids.add(event.id)
  state.events_applied += 1

  switch (event.type) {
    case 'turn.open': {
      state.turn_id = event.turn_id
      break
    }
    case 'phase': {
      state.phase = event.phase
      break
    }
    case 'activity.upsert': {
      if (!state.activities.has(event.key)) {
        state.activity_order.push(event.key)
      }
      state.activities.set(event.key, {
        key: event.key,
        pass_id: event.pass_id,
        label_key: event.label_key,
        status: event.status,
        detail: event.detail,
      })
      break
    }
    case 'block.open': {
      state.blocks.set(event.block_id, {
        id: event.block_id,
        kind: event.kind,
        index: event.index,
        text: '',
        committed: false,
        final_text: undefined,
      })
      state.block_order.push(event.block_id)
      break
    }
    case 'block.delta': {
      const block = state.blocks.get(event.block_id)
      if (!block) {
        state.violations.push(`block.delta targets unknown block_id=${event.block_id}`)
        if (strict) throw new Error(`block.delta targets unknown block_id=${event.block_id}`)
        break
      }
      if (block.committed) {
        const msg = `block.delta targets ALREADY-COMMITTED block_id=${event.block_id} (transmutation violation)`
        state.violations.push(msg)
        if (strict) throw new Error(msg)
        break
      }
      block.text += event.text
      break
    }
    case 'block.commit': {
      const block = state.blocks.get(event.block_id)
      if (!block) {
        state.violations.push(`block.commit targets unknown block_id=${event.block_id}`)
        if (strict) throw new Error(`block.commit targets unknown block_id=${event.block_id}`)
        break
      }
      if (block.committed) {
        const msg = `block.commit targets ALREADY-COMMITTED block_id=${event.block_id} (double-commit)`
        state.violations.push(msg)
        if (strict) throw new Error(msg)
        break
      }
      if (block.text !== event.final_text) {
        state.violations.push(
          `block.commit final_text mismatch for block_id=${event.block_id}: accumulated deltas != final_text`,
        )
      }
      block.committed = true
      block.final_text = event.final_text
      break
    }
    case 'seam.open': {
      state.seams.set(event.seam_id, {
        seam_id: event.seam_id,
        block_id: event.block_id,
        anchor_offset: event.anchor_offset,
        citation_id: undefined,
      })
      break
    }
    case 'seam.set': {
      const seam = state.seams.get(event.seam_id)
      if (!seam) {
        state.violations.push(`seam.set targets unknown seam_id=${event.seam_id}`)
        break
      }
      seam.citation_id = event.citation_id
      break
    }
    case 'citation.define': {
      state.citations.set(event.citation_id, {
        citation_id: event.citation_id,
        label: event.label,
        verification: event.verification,
        source_ref: event.source_ref,
      })
      break
    }
    case 'flag': {
      state.flags.push({
        flag_key: event.flag_key,
        severity: event.severity,
        detail: event.detail,
      })
      break
    }
    case 'grade': {
      state.grades.push({
        target_block_id: event.target_block_id,
        score: event.score,
        basis: event.basis,
      })
      break
    }
    case 'turn.commit': {
      state.turn_commit = {
        turn_id: event.turn_id,
        block_count: event.block_count,
        citation_count: event.citation_count,
      }
      break
    }
    case 'turn.close': {
      state.turn_close = { turn_id: event.turn_id, reason: event.reason }
      break
    }
    case 'error': {
      // Reported, not fatal to reducer state — surfaced via flags for the
      // harness to render.
      state.flags.push({ flag_key: `error.${event.code}`, severity: 'warning', detail: event.message })
      break
    }
    default: {
      state.violations.push(`unknown event type: ${String(event && event.type)}`)
      state.malformed_dropped += 1
    }
  }

  return state
}

/**
 * Apply a whole ordered array of events to a fresh state. Convenience for
 * tests. Non-strict by default (never throws) so a whole fixture — including
 * ones that deliberately contain violations, e.g. the stall/disconnect
 * fixtures which end mid-block on purpose — can be replayed to completion
 * and inspected.
 *
 * @param {any[]} events
 * @param {{ strict?: boolean }} [opts]
 * @returns {ReducerState}
 */
export function reduceAll(events, opts = {}) {
  let state = createInitialState()
  for (const event of events) {
    state = applyEvent(state, event, opts)
  }
  return state
}

/** Derive a plain-JSON-serializable snapshot of state, for determinism
 *  comparisons (Maps/Sets don't JSON.stringify usefully on their own). */
export function snapshot(state) {
  return {
    turn_id: state.turn_id,
    phase: state.phase,
    blocks: state.block_order.map((id) => state.blocks.get(id)),
    activities: state.activity_order.map((key) => state.activities.get(key)),
    seams: Array.from(state.seams.values()),
    citations: Array.from(state.citations.values()),
    flags: state.flags,
    grades: state.grades,
    turn_commit: state.turn_commit,
    turn_close: state.turn_close,
    events_applied: state.events_applied,
    duplicates_dropped: state.duplicates_dropped,
    malformed_dropped: state.malformed_dropped,
    violations: state.violations,
  }
}
