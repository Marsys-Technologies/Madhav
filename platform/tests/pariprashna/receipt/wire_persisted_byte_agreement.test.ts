/**
 * P3-D PREP (Paripraśna P3+P4 overnight run, Wave P3-3 precondition) —
 * THE WIRE↔PERSISTED RECEIPT SINGLE-REFERENCE GUARD (byte-equality is the
 * detection MECHANISM, not two independently-assembled derivations) for the
 * WEB door.
 *
 * RENAMED 2026-08-23 (review finding, blocks-merge fix 2). The previous
 * headline, "THE WIRE↔PERSISTED RECEIPT BYTE-AGREEMENT TEST," read as a
 * claim that the wire copy and the persisted copy are two independently
 * derived values which happen to agree byte-for-byte. They are not. Per
 * `persistence_stage.ts` (its own comment at the call site, lines ~503–506):
 * "the two copies (wire + persisted) are the same validated object, never
 * two independently-assembled ones that could drift" — `metadataWithReceipt
 * = withAcharyaReadingReceipt(metadataWithReceipt ?? {}, receipt)` (line
 * 499) and `em.receiptDefine({ turn_id: turnId, receipt })` (line 507) both
 * close over the SAME `receipt` object built once by
 * `assembleAcharyaReadingReceipt`. Given CLAUDE.md §N.8 instance 3 is
 * literally "a byte-equality claim with no byte comparison behind it," this
 * file must not itself carry a byte-equality headline resting on an
 * unstated identity invariant. What this file actually guards: that no
 * FUTURE code change silently introduces a second, independent derivation
 * on either side (a genuine two-copies bug) without a test going RED. The
 * assertion mechanism is still real byte comparison — it cannot fail on a
 * *value* divergence today because there is no second derivation to
 * diverge; it fails only if the CODE changes to produce two objects, which
 * is exactly why all five review sabotages (and this lane's own two
 * §N.8-capable-of-failing cases below) had to edit source to go RED. That
 * is a genuinely valuable regression guard — it is just not "independent
 * derivations happened to agree."
 *
 * WHY IT EXISTS
 * ─────────────
 * Charter §4 Wave P3-3: "Precondition first: the wire↔persisted byte-
 * agreement test on the web door exists and is green before the lane opens.
 * Parity hashes the persisted receipt object." P3-D's door-parity assertion
 * (still to be built, out of this lane's scope) hashes the PERSISTED
 * `AcharyaReadingReceipt` on each door. That assertion is only meaningful if
 * the web door's persisted receipt actually IS what the web door's own
 * reader saw on the wire — otherwise "the doors' receipts hash equal" could
 * be true of two receipts neither door's user ever received. This file is
 * the detector for that property, scoped to the web door only (the MCP door
 * has no persistence path to compare against — see DD-24 gap enumeration,
 * `00_ARCHITECTURE/briefs/pariprashna_swarm/DD24_DOOR_GAP_ENUMERATION_v1_0.md`,
 * item 1).
 *
 * WHAT "WIRE" AND "PERSISTED" MEAN HERE (read from the code, not assumed)
 * ────────────────────────────────────────────────────────────────────────
 *  · WIRE: `platform/src/lib/pariprashna/pipeline/persistence_stage.ts`
 *    calls `em.receiptDefine({ turn_id, receipt })` — a REAL
 *    `PariprashnaEmitter` (`protocol/emitter.ts`) writing a REAL SSE frame
 *    (`protocol/events.ts#serializeEvent`: `event: receipt.define\ndata:
 *    <JSON>\n\n`) onto a REAL `ReadableStreamDefaultController`-shaped sink.
 *    This test captures those raw bytes and decodes the SAME way a client
 *    would (`decodeEvent`), rather than reading the in-memory `receipt`
 *    object before it was ever serialized — a test that skipped the wire
 *    encode/decode round-trip would not be testing "the wire" at all.
 *  · PERSISTED: `platform/src/lib/pariprashna/store/writer.ts#writeTurn`
 *    inserts `metadata_json` as `JSON.stringify(msg.metadata ?? {})` — the
 *    EXACT serialization Postgres receives for the jsonb column. This test
 *    mocks only `writeTurn` itself (the pg boundary — no live DB tonight,
 *    RF-5) and re-derives the persisted bytes with that SAME
 *    `JSON.stringify(message.metadata ?? {})` call, so the comparison uses
 *    the real writer's own serialization contract, not a re-invented one.
 *  · The receipt lives at `metadata.acharya_reading_receipt`
 *    (`receipt/store.ts#RECEIPT_METADATA_KEY`) on the persisted side, and at
 *    `.receipt` on the wire event — both extracted before comparison.
 *  · Both of the above trace to the SAME `receipt` object reference (see the
 *    renamed-headline note above) — the wire/persisted split is real at the
 *    protocol level (SSE frame vs. jsonb column, two different transports),
 *    but not at the derivation level (one assembly, not two).
 *
 * §N.8 EARNED-SIGNAL COMPLIANCE
 * ──────────────────────────────
 * A byte-equality assertion with no byte comparison behind it is already a
 * named defect in CLAUDE.md §N.8 (instance 3, the PB-2 gate). The first
 * `describe` block below proves this comparator is CAPABLE OF FAILING —
 * fed two receipts that differ in exactly one field, it must fail — BEFORE
 * the second block's real-route green run is allowed to mean anything. That
 * capability-of-failing is what makes this a real guard despite the single-
 * object-reference fact above: the comparator itself is sound; what a
 * reader must not conclude from a green run is "two independent
 * assemblies agreed," because there are not two independent assemblies.
 *
 * CI SCOPE (disclosed honestly — corrected 2026-08-23, review finding,
 * blocks-merge fix 2)
 * ──────────────────────────────
 * Every collaborator this test touches is either the REAL, unmocked
 * application code under test (`runPersistenceStage`, `PariprashnaEmitter`,
 * `ReadingPartsAssembler`, `assembleAcharyaReadingReceipt`, the real SSE
 * `serializeEvent`/`decodeEvent` round-trip, the real `JSON.stringify`
 * writer contract) or a mock of a true I/O boundary (Postgres via
 * `store/writer#writeTurn`, `@/lib/db/client`, conversation history writes,
 * pending-stream bookkeeping, calibration-stamp logging, feature flags).
 * NO database is required — this runs in ordinary `vitest run` / CI, same
 * project as `route_golden_stream.test.ts` (`node`, not `jsdom` — see
 * `vitest.config.ts`'s DOM_TEST_GLOBS header). It does not prove the
 * `metadata_json` jsonb COLUMN round-trips byte-identically through
 * Postgres itself (jsonb may reorder/renormalize on ingest) — only that the
 * BYTES THIS PROCESS HANDS TO THE INSERT are the same bytes the reader's
 * client received. A live DB-read confirmation of the persisted row is
 * P3-D/DD-21's job, not this lane's (P3-D is explicitly out of scope here —
 * see the P3-D-PREP builder brief).
 *
 * WHAT THIS TEST DOES **NOT** PROVE, STATED PLAINLY: it does not prove that
 * two independently-assembled receipts happen to serialize identically —
 * there is only ever one assembled `receipt` object per turn on the web
 * door today (see the renamed-headline note). It proves (a) the byte
 * comparator itself can fail on a real divergence (§N.8 block below), and
 * (b) that object survives the wire-encode and the persisted-serialize
 * paths unchanged end to end through REAL application code. A future
 * refactor that gives the wire and the persisted paths two separate
 * derivations would need this test to still catch drift between them —
 * which it would, precisely because it is a byte comparison and not a
 * reference-identity check — but today's green run is a single-source
 * integrity guard, not evidence of independent-derivation agreement.
 *
 * Chart id used throughout is the SYNTHETIC probe chart
 * (`1c826d5a-41cb-4450-b4dc-59d440e5f75a`) per the overnight run's hard-never
 * on the native's real chart.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { UIMessage } from 'ai'

const SYNTHETIC_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

// ─────────────────────────────────────────────────────────────────────────────
// Captured `writeTurn` calls — the "persisted" side. Declared via `vi.hoisted`
// so the `vi.mock` factory below (hoisted above imports by vitest) can close
// over it.
// ─────────────────────────────────────────────────────────────────────────────
const { writeTurnCalls } = vi.hoisted(() => ({
  writeTurnCalls: [] as Array<{ message: Record<string, unknown>; parts: unknown[] }>,
}))

// ── Feature flags. Only PARIPRASHNA_RECEIPT_EMISSION_ENABLED is armed here.
//    CORRECTED 2026-08-23 (review finding, blocks-merge fix 1): this is NOT
//    the flag posture receipt emission actually ships under today. Read live
//    from the serving revision (`gcloud run services describe amjis-web`,
//    read-only, no production change):
//      MARSYS_FLAG_PARIPRASHNA_SEMANTIC_BLOCKS_ENABLED     = true
//      MARSYS_FLAG_PARIPRASHNA_TYPED_CONFIDENCE_ENABLED    = true
//      MARSYS_FLAG_PARIPRASHNA_INTERPRETATION_SETS_ENABLED = true
//    All three are read by the receipt path (`persistence_stage.ts:489
//    typedConfidenceEnabled: isTypedConfidenceEnabled()`; `confidence/
//    flag.ts:15`; `interpretation/flag.ts:17`) and production populates
//    `interpretation_sets` / `confidence_typing` where this harness (with
//    those flags OFF) gets `{"status": "unavailable"}` instead. Durable-
//    outbox persistence has no corresponding env var set on the serving
//    revision at all, so OFF is its real default here.
//    NET: this test exercises a STRICTLY SMALLER receipt than production
//    ships, not "the same posture." The wire↔persisted byte-agreement
//    property under test does not depend on which optional receipt fields
//    are populated — the invariant holds at any flag posture, because both
//    sides trace to the same object reference (see the file header's FIX 2
//    note) — so this narrower fixture does not weaken the guard. A
//    maximal-flag variant exercising all four flags ON would be strictly
//    more thorough and is left as follow-up, not required for this guard to
//    be sound. ──
vi.mock('@/lib/config/index', () => ({
  configService: {
    getFlag: vi.fn((key: string) => key === 'PARIPRASHNA_RECEIPT_EMISSION_ENABLED'),
  },
}))

// ── DB read boundary (MSR snippet fetch, prediction-part lookups). Nothing in
//    this test's fixture text triggers either path, but the mock exists so an
//    unexpected query never reaches a real pg pool in CI. ──
vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async () => ({ rows: [], rowCount: 0 })),
}))

// ── The ONLY persistence boundary this test allows through to a fake DB —
//    everything upstream of this call (canonical message assembly, receipt
//    assembly, validation, wire emission) is REAL application code. ──
vi.mock('@/lib/pariprashna/store/writer', () => ({
  writeTurn: vi.fn(async (message: Record<string, unknown>, parts: unknown[]) => {
    writeTurnCalls.push({ message, parts })
    return { message_id: message.id as string, parts_written: parts.length }
  }),
}))

vi.mock('@/lib/persistence/conversation_writer', () => ({
  writeConversationMessages: vi.fn(async () => ({ verified: true, messageIds: ['history-msg-1'] })),
}))

vi.mock('@/lib/persistence/pending_streams_writer', () => ({
  createPendingStreamWriter: vi.fn(() => ({ clear: vi.fn(async () => {}) })),
}))

vi.mock('@/lib/conversations/title', () => ({
  generateConversationTitle: vi.fn(async () => 'unused (isFirstTurn: false)'),
}))
vi.mock('@/lib/conversations', () => ({
  updateConversationTitle: vi.fn(async () => {}),
}))

vi.mock('@/lib/db/monitoring-write', () => ({
  writeContextAssemblyLog: vi.fn(async () => {}),
}))

vi.mock('@/lib/llm/pricing', () => ({
  computeCostUsd: vi.fn(() => null),
  getModelPricingSync: vi.fn(() => null),
}))

vi.mock('@/lib/predictions/calibration_producer', () => ({
  recordCalibrationStamp: vi.fn(async () => {}),
}))

vi.mock('@/lib/pariprashna/samiksha/capture', () => ({
  captureDetectedCandidates: vi.fn(async () => ({ created: [], skippedExisting: 0, unpaired: 0 })),
}))

// ── Provenance stamp compute (DB-bound in production) mocked to a fixed,
//    deterministic value; drift-detection logic itself (pure) stays REAL. ──
vi.mock('@/lib/pariprashna/provenance/stamp', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/pariprashna/provenance/stamp')>()
  return {
    ...actual,
    computeTurnProvenanceStamp: vi.fn(async () => ({
      build_id: 'build-harness',
      priors_version: 'v3',
      formula_versions: { salience_formula_ver: null },
      ranking_config: { mode: 'harness' },
      now_context_date: '2026-08-23',
      computed_at: '2026-08-23T00:00:00.000Z',
    })),
    getLastTurnStamp: vi.fn(async () => null),
  }
})

// ── Imports AFTER the mocks above (vitest hoists vi.mock calls regardless of
//    source order, but keeping the real imports below the mocks documents
//    the dependency direction for a human reader). ──
import { runPersistenceStage } from '@/lib/pariprashna/pipeline/persistence_stage'
import { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'
import { ReadingPartsAssembler } from '@/lib/pariprashna/pipeline/reading_parts'
import { decodeEvent, type PariprashnaEvent } from '@/lib/pariprashna/protocol/events'
import type { TurnIdentity, TurnParams } from '@/lib/pariprashna/pipeline/stage_context'
import type { PipelinePlan } from '@/lib/pipeline/types'

/** Deterministic byte-serialization for comparison — the SAME `JSON.stringify`
 *  contract `store/writer.ts#writeTurn` uses for the `metadata_json` column
 *  and `protocol/events.ts#serializeEvent` uses for the SSE `data:` payload.
 *  Not a "smarter" canonicalizer (no key sorting) — an actual divergence in
 *  key order between the two sides SHOULD fail this test, because it would
 *  mean the two serializations are not, in fact, byte-identical. */
function bytes(value: unknown): string {
  return JSON.stringify(value)
}

/** A minimal fake `ReadableStreamDefaultController<Uint8Array>` that only
 *  captures enqueued chunks — enough for `PariprashnaEmitter`, which never
 *  calls anything else on the controller in the success path. */
class CapturingController {
  readonly chunks: Uint8Array[] = []
  enqueue(chunk: Uint8Array): void {
    this.chunks.push(chunk)
  }
  close(): void {}
  error(): void {}
  get desiredSize(): number {
    return 1
  }
}

function decodeWireEvents(controller: CapturingController): PariprashnaEvent[] {
  const raw = Buffer.concat(controller.chunks.map((c) => Buffer.from(c))).toString('utf8')
  const events: PariprashnaEvent[] = []
  // Real SSE framing per `serializeEvent`: `event: <type>\ndata: <json>\n\n`.
  for (const frame of raw.split('\n\n')) {
    const dataLine = frame.split('\n').find((l) => l.startsWith('data: '))
    if (!dataLine) continue
    const decoded = decodeEvent(dataLine.slice('data: '.length))
    if (decoded) events.push(decoded)
  }
  return events
}

interface TurnRunResult {
  wireEvents: PariprashnaEvent[]
  wireReceipt: unknown
  persistedMessage: Record<string, unknown> | undefined
  persistedMetadata: Record<string, unknown> | undefined
  persistedReceipt: unknown
}

/** Runs the REAL `runPersistenceStage` (the exact module the web door's
 *  route shell calls — see `route.ts`'s `runPersistenceStage` call site)
 *  against a REAL `PariprashnaEmitter` writing to a captured sink, with a
 *  REAL `ReadingPartsAssembler`-built prose block so `committedBlocks` /
 *  `accumulatedText` are the same shapes production code produces — not a
 *  hand-authored fixture standing in for what the assembler would have
 *  built. */
async function runTurn(assistantProse: string): Promise<TurnRunResult> {
  writeTurnCalls.length = 0
  const controller = new CapturingController()
  const em = new PariprashnaEmitter(
    controller as unknown as ReadableStreamDefaultController<Uint8Array>,
  )

  const assembler = new ReadingPartsAssembler(em, 1)
  const block = assembler.ensureBlock('prose')
  assembler.appendProse(block, assistantProse)
  assembler.commitBlock()

  const identity: TurnIdentity = {
    turnId: 'turn-byte-agreement-1',
    queryId: 'query-byte-agreement-1',
    conversationId: 'conv-byte-agreement-1',
    chartId: SYNTHETIC_CHART_ID,
    isFirstTurn: false,
  }
  const params: TurnParams = {
    selectedStack: 'default' as TurnParams['selectedStack'],
    modelId: 'harness-model',
    modelMeta: { maxInputTokens: 100_000, provider: 'harness' } as unknown as TurnParams['modelMeta'],
    readingDepth: 'standard' as TurnParams['readingDepth'],
    deepDive: false,
    lengthTier: 'standard' as TurnParams['lengthTier'],
    lelContextEnabled: true,
    style: 'plain',
  }
  const userMessage: UIMessage = {
    id: 'user-msg-1',
    role: 'user',
    parts: [{ type: 'text', text: 'What house is my Moon in, and what does it mean for my inner life?' }],
  } as UIMessage
  const plan = { domains: ['self', 'mind'], query_class: 'diagnostic' } as unknown as PipelinePlan

  await runPersistenceStage({
    em,
    identity,
    params,
    user: { uid: 'harness-uid' },
    isSuperAdmin: false,
    messages: [userMessage],
    lastUserMessage: userMessage,
    plan,
    plannerModelId: 'planner-harness-model',
    plannerLatencyMs: 250,
    committedBlocks: assembler.committedBlocks,
    accumulatedText: assembler.accumulatedText,
    validToolResults: [],
    citationGate: { gateResult: 'PASS', layer1Count: 0, layer2Verified: 0 },
    synthesisStartedAt: Date.now() - 500,
    completenessReceipt: null,
    citationHallucinationCount: 0,
  })

  const wireEvents = decodeWireEvents(controller)
  const receiptEvent = wireEvents.find((e) => e.type === 'receipt.define')
  const persistedMessage = writeTurnCalls.at(-1)?.message
  const persistedMetadata = persistedMessage?.metadata as Record<string, unknown> | undefined

  return {
    wireEvents,
    wireReceipt: (receiptEvent as { receipt?: unknown } | undefined)?.receipt,
    persistedMessage,
    persistedMetadata,
    persistedReceipt: persistedMetadata?.['acharya_reading_receipt'],
  }
}

beforeEach(() => {
  writeTurnCalls.length = 0
})

// ─────────────────────────────────────────────────────────────────────────────
// §N.8 — the comparator must be demonstrated CAPABLE OF FAILING before its
// first real pass counts. This is the "deliberately mismatched receipt" the
// charter names explicitly (§4 Wave P3-3, §6.2).
// ─────────────────────────────────────────────────────────────────────────────
describe('wire↔persisted receipt single-reference guard (byte-equality mechanism) — the detector can fail (§N.8)', () => {
  it('FAILS when the wire receipt and the persisted receipt diverge by one field', () => {
    const wireReceipt = {
      receipt_schema_version: 1,
      turn_id: 'turn-byte-agreement-1',
      conversation_id: 'conv-byte-agreement-1',
      chart_id: SYNTHETIC_CHART_ID,
      receipt_hash: 'sha256:AAAA',
      coverage: { status: 'unavailable', served: null },
    }
    // A deliberately mismatched persisted copy — the exact class of bug this
    // test exists to catch: the reader saw one receipt_hash, the DB holds
    // another (e.g. a race, a second independent assembly, a stale write).
    const persistedReceipt = { ...wireReceipt, receipt_hash: 'sha256:BBBB' }

    expect(() => {
      expect(bytes(wireReceipt)).toBe(bytes(persistedReceipt))
    }).toThrow()
  })

  it('FAILS when the wire receipt and the persisted receipt diverge only in key order', () => {
    // A more subtle divergence class: same logical content, different
    // serialization — exactly what a "two independently-assembled copies"
    // bug (rather than a single shared reference) would produce. Byte
    // equality is deliberately stricter than deep-equality here.
    const wireReceipt = { a: 1, b: 2 }
    const persistedReceiptReordered = { b: 2, a: 1 }

    expect(() => {
      expect(bytes(wireReceipt)).toBe(bytes(persistedReceiptReordered))
    }).toThrow()
  })

  it('PASSES on two genuinely identical receipts (sanity: the comparator is not always-fail)', () => {
    const receipt = { turn_id: 'x', receipt_hash: 'sha256:CCCC' }
    expect(bytes(receipt)).toBe(bytes({ ...receipt }))
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// The real regression guard: the web door's actual persistence stage, run
// end to end (minus the true pg/Postgres boundary — RF-5, no live DB
// tonight), asserting the SSE `receipt.define` payload and the
// `metadata_json` the writer would insert are byte-identical.
// ─────────────────────────────────────────────────────────────────────────────
describe('wire↔persisted receipt single-reference guard (byte-equality mechanism) — the real web-door persistence stage', () => {
  it('emits a receipt.define wire event', async () => {
    const result = await runTurn(
      'The Moon in Pūrva Bhādrapada colors this turn toward introspection, restlessness, ' +
        'and a private intensity that rarely announces itself outwardly.',
    )
    expect(result.wireReceipt).toBeDefined()
  })

  it('persists a receipt at metadata.acharya_reading_receipt', async () => {
    const result = await runTurn(
      'Saturn from the ascendant asks for patience before results — the timing is slower ' +
        'than the question wants it to be, not absent.',
    )
    expect(result.persistedReceipt).toBeDefined()
  })

  it('the receipt on the wire is byte-identical to the receipt persisted to metadata_json', async () => {
    const result = await runTurn(
      'Jupiter aspecting the seventh house widens the field of who counts as a real partner, ' +
        'for better and for worse.',
    )
    expect(result.wireReceipt).toBeDefined()
    expect(result.persistedReceipt).toBeDefined()

    // GREEN — the property under test. Re-derives the persisted bytes with
    // the SAME serialization `store/writer.ts#writeTurn` actually uses for
    // the jsonb insert (`JSON.stringify(msg.metadata ?? {})`), scoped to the
    // receipt sub-key, so this assertion is checking the writer's real
    // contract rather than a re-invented one.
    const persistedBytesFullMetadata = JSON.stringify(result.persistedMessage?.metadata ?? {})
    const persistedMetadataRoundTrip = JSON.parse(persistedBytesFullMetadata) as Record<string, unknown>
    const persistedReceiptBytes = bytes(persistedMetadataRoundTrip['acharya_reading_receipt'])
    const wireReceiptBytes = bytes(result.wireReceipt)

    expect(wireReceiptBytes).toBe(persistedReceiptBytes)
  })

  // DOCUMENTATION ASSERTION (review finding, blocks-merge fix 2, disposition:
  // labelled not dropped). This case adds NO detection beyond the full-object
  // byte-equality assertion above — because both sides trace to the same
  // `receipt` object reference (see file header), `receipt_hash` can only
  // diverge here if the WHOLE receipt already diverged, which the assertion
  // above already catches, field-by-field-inclusive. Verified under review:
  // this case stayed GREEN under all five independent sabotages, including
  // one that deleted a whole field — it can only fail if `receipt_hash`
  // itself is perturbed on one side in isolation, which in this codebase
  // today only this file's own §N.8 block above does deliberately. Kept, not
  // dropped, because it documents in the test's own name which specific
  // field DD-24's parity assertion will hash — a fact worth pinning even
  // though the assertion mechanics add no independent coverage.
  it('DOCUMENTATION: receipt_hash — the specific field DD-24 parity will hash — is present and identical on both sides', async () => {
    const result = await runTurn(
      'Rahu in the tenth house of career often reads as ambition first and clarity second — ' +
        'the drive arrives before the native fully knows what it is driving toward.',
    )
    const wireHash = (result.wireReceipt as { receipt_hash?: unknown } | undefined)?.receipt_hash
    const persistedHash = (result.persistedReceipt as { receipt_hash?: unknown } | undefined)?.receipt_hash
    expect(typeof wireHash).toBe('string')
    expect(wireHash).toBe(persistedHash)
  })
})
