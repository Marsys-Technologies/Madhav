import { adaptC2Fixture, type C2Fixture } from '../state/c2ProtocolAdapter'
import type { Fixture } from './types'

/**
 * Literal copies of two of lane C-2's actually-committed recorded fixtures
 * (`Madhav-pb-1-c2/platform/tests/pariprashna/fixtures/{single-pass,honest-gap}.json`
 * @ commit 9452e0e7), run through `adaptC2Fixture`. This is what proves the
 * renderer integrates against C-2's real protocol scaffold, not just our
 * own hand-authored mockup script — same reducer, same components, a
 * genuinely different (and differently-shaped) source of events.
 *
 * These are copied inline rather than imported from
 * `../../../../tests/pariprashna/fixtures/*.json` because that path does
 * not exist in THIS worktree (it lives on lane C-2's branch, `pb/1/c2`,
 * uncommitted-relative-to-us until both branches merge to `main`) — file
 * scope for this lane is also limited to `components/pariprashna/**` and
 * the app route, which excludes `platform/tests/**` in any case. Once both
 * land on `main`, swap this for a real `import … from
 * '@/../tests/pariprashna/fixtures/single-pass.json'` and delete the copy.
 */

const C2_SINGLE_PASS: C2Fixture = {
  name: 'single-pass',
  description: 'Minimal single retrieval pass, one paragraph block.',
  events: [
    { delay_ms: 0, event: { id: 'single-pass-0', seq: 0, t: 0, type: 'turn.open', turn_id: 'single-pass', reading_depth: 'standard' } },
    {
      delay_ms: 40,
      event: {
        id: 'single-pass-1', seq: 1, t: 40, type: 'activity.upsert',
        key: 'pass-1-retrieval', pass_id: 'pass-1', label_key: 'activity.retrieval.pass',
        status: 'done', detail: 'pass 1 of 1 — 2 signals',
      },
    },
    { delay_ms: 20, event: { id: 'single-pass-2', seq: 2, t: 60, type: 'block.open', block_id: 'b1', kind: 'paragraph', index: 0 } },
    {
      delay_ms: 20,
      event: {
        id: 'single-pass-3', seq: 3, t: 80, type: 'block.delta', block_id: 'b1',
        text: 'The retrieval layer surfaces three corroborating signals for this window.',
      },
    },
    {
      delay_ms: 10,
      event: {
        id: 'single-pass-4', seq: 4, t: 90, type: 'block.commit', block_id: 'b1',
        final_text: 'The retrieval layer surfaces three corroborating signals for this window.',
      },
    },
    { delay_ms: 10, event: { id: 'single-pass-5', seq: 5, t: 100, type: 'turn.commit', turn_id: 'single-pass', block_count: 1, citation_count: 0 } },
    { delay_ms: 5, event: { id: 'single-pass-6', seq: 6, t: 105, type: 'turn.close', turn_id: 'single-pass', reason: 'complete' } },
  ],
}

const C2_HONEST_GAP: C2Fixture = {
  name: 'honest-gap',
  description:
    "A seam resolves to citation_id: null (no source found) and a flag reports the gap — must render as an honest gap, never silently dropped.",
  events: [
    { delay_ms: 0, event: { id: 'honest-gap-0', seq: 0, t: 0, type: 'turn.open', turn_id: 'honest-gap', reading_depth: 'standard' } },
    { delay_ms: 20, event: { id: 'honest-gap-1', seq: 1, t: 20, type: 'block.open', block_id: 'b1', kind: 'paragraph', index: 0 } },
    {
      delay_ms: 15,
      event: {
        id: 'honest-gap-2', seq: 2, t: 35, type: 'block.delta', block_id: 'b1',
        text: "No contradiction was found against the prior turn's working hypothesis. ",
      },
    },
    { delay_ms: 10, event: { id: 'honest-gap-3', seq: 3, t: 45, type: 'seam.open', seam_id: 's1', block_id: 'b1', anchor_offset: 72 } },
    {
      delay_ms: 10,
      event: {
        id: 'honest-gap-4', seq: 4, t: 55, type: 'block.commit', block_id: 'b1',
        final_text: "No contradiction was found against the prior turn's working hypothesis. ",
      },
    },
    { delay_ms: 10, event: { id: 'honest-gap-5', seq: 5, t: 65, type: 'seam.set', seam_id: 's1', citation_id: null } },
    {
      delay_ms: 10,
      event: {
        id: 'honest-gap-6', seq: 6, t: 75, type: 'flag', flag_key: 'honest_gap.no_citation_found', severity: 'notice',
        detail: 'No classical source located for this claim within the current pass budget.',
      },
    },
    { delay_ms: 10, event: { id: 'honest-gap-7', seq: 7, t: 85, type: 'turn.commit', turn_id: 'honest-gap', block_count: 1, citation_count: 0 } },
    { delay_ms: 5, event: { id: 'honest-gap-8', seq: 8, t: 90, type: 'turn.close', turn_id: 'honest-gap', reason: 'complete' } },
  ],
}

export function buildC2SinglePassFixture(turnId = 't-c2-single'): Fixture {
  return { id: 'c2_single_pass', label: 'C-2 recorded · single pass', userText: '(replayed from lane C-2 fixture — no source question text)', events: adaptC2Fixture(turnId, C2_SINGLE_PASS) }
}

export function buildC2HonestGapFixture(turnId = 't-c2-gap'): Fixture {
  return { id: 'c2_honest_gap', label: 'C-2 recorded · honest gap', userText: '(replayed from lane C-2 fixture — no source question text)', events: adaptC2Fixture(turnId, C2_HONEST_GAP) }
}
