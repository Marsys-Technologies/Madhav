#!/usr/bin/env tsx
/**
 * Byte-equality against ONE REAL DEPLOYED READING — SAMĀPTI lane B-PB8-BYTEEQ,
 * the operator half of deliverable (b) of
 * `FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE.md`.
 *
 * Takes a REAL reading's raw SSE event stream (captured durably by
 * `src/lib/pariprashna/protocol/stream_capture.ts`), replays it through the REAL
 * production mapping (`store/replay_paths.ts`), and diffs the result against
 * that same reading's ACTUAL persisted `message_parts` rows. This is the run
 * BRIEF_PB-2 §G-1's second clause always demanded and never got.
 *
 *   npm run pariprashna:verify-captured -- --list
 *   npm run pariprashna:verify-captured -- --turn <turn_id>
 *   npm run pariprashna:verify-captured -- --latest
 *   npm run pariprashna:verify-captured -- --purge      # retention sweep
 *
 * EXIT CODES
 *   0  byte-identical — the claim holds for this reading
 *   1  DIVERGED — a real finding; the per-part diff is printed
 *   2  cannot run (capture disabled / no captured turn / turn never persisted).
 *      Deliberately NOT 0: "we couldn't check" must never read as "it passed".
 *
 * All comparison logic lives in `store/replay_compare.ts` (pure, unit-tested
 * without a database — `tests/pariprashna/replay_compare.test.ts`). This file is
 * I/O and argv only.
 */

import {
  readCapturedTurn,
  listCapturedTurns,
  isStreamCaptureEnabled,
  purgeExpiredStreamCaptures,
} from '../../src/lib/pariprashna/protocol/stream_capture'
import { readTurnParts, readCanonicalMessage } from '../../src/lib/pariprashna/store/reader'
import {
  compareReplayAgainstPersisted,
  formatReplayComparison,
  exitCodeFor,
  notComparable,
} from '../../src/lib/pariprashna/store/replay_compare'
import type { PariprashnaEvent } from '../../src/lib/pariprashna/protocol/events'

function arg(name: string): string | undefined {
  const i = process.argv.indexOf(`--${name}`)
  return i >= 0 ? process.argv[i + 1] : undefined
}
function has(name: string): boolean {
  return process.argv.includes(`--${name}`)
}

async function main(): Promise<number> {
  if (has('purge')) {
    console.log(`purged ${await purgeExpiredStreamCaptures()} expired capture row(s).`)
    return 0
  }

  if (has('list')) {
    const turns = await listCapturedTurns(Number(arg('limit') ?? 20))
    if (turns.length === 0) {
      console.log('No captured turns.')
      console.log(
        isStreamCaptureEnabled()
          ? 'Capture IS enabled here — no real reading has streamed since it was turned on.'
          : 'Capture is DISABLED here (PARIPRASHNA_STREAM_CAPTURE is not 1/true).',
      )
      return 2
    }
    for (const t of turns) console.log(`${t.captured_at}  ${t.turn_id}  ${t.events} events`)
    return 0
  }

  let turnId = arg('turn')
  if (!turnId && has('latest')) {
    const [latest] = await listCapturedTurns(1)
    turnId = latest?.turn_id
  }
  if (!turnId) {
    console.error('Usage: --turn <turn_id> | --latest | --list | --purge')
    return 2
  }

  const capture = await readCapturedTurn(turnId)
  if (!capture) {
    console.log(formatReplayComparison(notComparable(turnId, 'no captured stream for this turn')))
    return 2
  }

  const commit = capture.events.find(
    (e): e is Extract<PariprashnaEvent, { type: 'turn.commit' }> => e.type === 'turn.commit',
  )
  if (!commit) {
    console.log(
      formatReplayComparison(
        notComparable(turnId, 'captured turn has no turn.commit — the reading never persisted (interrupted/errored)'),
      ),
    )
    return 2
  }

  const message = await readCanonicalMessage(commit.message_id)
  if (!message) {
    console.log(
      formatReplayComparison(
        notComparable(turnId, `message ${commit.message_id} is absent or not canonical (schema_version NULL)`),
      ),
    )
    return 2
  }

  const persistedParts = await readTurnParts(commit.message_id)
  if (persistedParts.length === 0) {
    console.log(formatReplayComparison(notComparable(turnId, `message ${commit.message_id} has zero message_parts rows`)))
    return 2
  }

  const comparison = compareReplayAgainstPersisted({
    turnId,
    events: capture.events,
    message: {
      id: message.id,
      conversation_id: message.conversation_id,
      role: message.role,
      schema_version: message.schema_version,
      model_id: message.model_id,
      provider: message.provider,
    },
    persistedParts,
  })

  console.log(formatReplayComparison(comparison))
  return exitCodeFor(comparison)
}

main()
  .then((code) => process.exit(code))
  .catch((err) => {
    console.error(err)
    process.exit(2)
  })
