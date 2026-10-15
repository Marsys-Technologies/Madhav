/**
 * Atomic chart correction and recompute (Jātaka chart workspace, Task 6).
 *
 * A fake transaction client records every statement in order, so these tests
 * assert the sequence the design requires — not just call counts: archive →
 * chart update → reverse-order strict clears → throughput reset → run insert →
 * run assets → run link on the archived rows → COMMIT → dispatch. Any failure
 * before COMMIT rolls everything back; a dispatch failure after COMMIT is the
 * honest Needs rebuild state.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import writerDigestInventory from '@/generated/nirmana-writer-digests.json'

vi.mock('server-only', () => ({}))

const { mockGetPool, mockDispatch, events } = vi.hoisted(() => ({
  mockGetPool: vi.fn(),
  mockDispatch: vi.fn(),
  events: [] as string[],
}))
vi.mock('@/lib/db/client', () => ({ getPool: mockGetPool, query: vi.fn() }))
vi.mock('@/lib/build/runDispatch', () => ({ dispatchPreparedRun: mockDispatch }))

import { ChartUpdateError, updateChartAndMaybeRecompute } from '../recomputeChart'

const CHART = '11111111-2222-4333-8444-555555555555'
const DIGESTS = writerDigestInventory.writers as Record<string, string>
const [W1, W2] = ['ka_kshetra', 'ka_avadhi'].filter((id) => DIGESTS[id])

const STORED = {
  id: CHART,
  name: 'Test Native',
  preferred_name: 'Test',
  subject_name: null,
  birth_date: '1984-02-05',
  birth_time: '10:43:00',
  birth_place: 'Bhubaneswar',
  birth_lat: 20.2961,
  birth_lng: 85.8245,
  timezone_id: 'Asia/Kolkata',
  ayanamsa: 'lahiri',
  owner_id: 'owner-uid',
  client_id: 'owner-uid',
}

const INPUT = {
  name: 'Test Native',
  preferred_name: 'Test',
  subject_name: null,
  birth_date: '1984-02-05',
  birth_time: '10:43',
  birth_place: 'Bhubaneswar',
  lat: 20.2961,
  lon: 85.8245,
  timezone_id: 'Asia/Kolkata',
  tz_offset: 5.5,
  ayanamshas: ['lahiri'],
}

const REGISTRY = [
  { asset_id: 'bg_ephemeris', layer: 'brahmagyan', scope: 'global', depends_on: [], estimated_seconds: 1, has_writer: true, target_table: 'bg_ephemeris_t', count_sql: null, natural_key_partition: null, asset_kind: 'data', asset_type: 'data', health_probe: null },
  { asset_id: W1, layer: 'kala', scope: 'per_chart', depends_on: [], estimated_seconds: 1, has_writer: true, target_table: 'kala_up', count_sql: null, natural_key_partition: null, asset_kind: 'data', asset_type: 'data', health_probe: null },
  { asset_id: W2, layer: 'kala', scope: 'per_chart', depends_on: [W1], estimated_seconds: 1, has_writer: true, target_table: 'kala_down', count_sql: null, natural_key_partition: null, asset_kind: 'data', asset_type: 'data', health_probe: null },
  { asset_id: 'mi_abhilekha', layer: 'mimamsa', scope: 'per_chart', depends_on: [W2], estimated_seconds: 1, has_writer: true, target_table: 'mimamsa_journal', count_sql: null, natural_key_partition: null, asset_kind: 'data', asset_type: 'data', health_probe: null },
  { asset_id: 'lel_events', layer: 'mimamsa', scope: 'per_chart', depends_on: [], estimated_seconds: 1, has_writer: false, target_table: 'life_events', count_sql: 'SELECT count(*) FROM life_events WHERE chart_id = $1', natural_key_partition: null, asset_kind: 'data', asset_type: 'data', health_probe: null },
]

interface Opts {
  chart?: Record<string, unknown> | null
  activeRun?: string | null
  protectedIds?: string[]
  failOn?: RegExp
  archivedIds?: string[]
  registry?: unknown[]
}

let statements: Array<{ sql: string; params: unknown[] }> = []

function setup(opts: Opts = {}) {
  statements = []
  events.length = 0
  const client = {
    query: vi.fn(async (sql: string, params: unknown[] = []) => {
      statements.push({ sql, params })
      if (/^(BEGIN|COMMIT|ROLLBACK)/.test(sql.trim())) events.push(sql.trim().split(/\s/)[0])
      if (opts.failOn?.test(sql)) throw new Error('forced failure')
      if (/FROM charts[\s\S]*FOR UPDATE/.test(sql)) return { rows: opts.chart === null ? [] : [opts.chart ?? STORED] }
      if (/SELECT id FROM build_runs/.test(sql)) return { rows: opts.activeRun ? [{ id: opts.activeRun }] : [] }
      if (/FROM asset_registry/.test(sql)) return { rows: opts.registry ?? REGISTRY }
      if (/FROM asset_throughput/.test(sql)) return { rows: [{ asset_id: 'bg_ephemeris', state: 'lit' }] }
      if (/FROM build_protected_assets/.test(sql)) return { rows: (opts.protectedIds ?? []).map((asset_id) => ({ asset_id })) }
      if (/FROM asset_freshness/.test(sql)) return { rows: [{ asset_id: 'bg_ephemeris', state: 'fresh', reasons: [] }] }
      if (/UPDATE conversations[\s\S]*RETURNING id/.test(sql)) return { rows: (opts.archivedIds ?? ['conv-1', 'conv-2']).map((id) => ({ id })) }
      if (/INSERT INTO build_runs/.test(sql)) return { rows: [{ id: 'run-new' }] }
      return { rows: [], rowCount: 0 }
    }),
    release: vi.fn(),
  }
  mockGetPool.mockResolvedValue({ connect: vi.fn().mockResolvedValue(client) })
  mockDispatch.mockImplementation(async () => {
    events.push('DISPATCH')
    return { ok: true, executionName: 'exec-1' }
  })
  return client
}

const idx = (re: RegExp) => statements.findIndex((s) => re.test(s.sql))
const has = (re: RegExp) => statements.some((s) => re.test(s.sql))
const MUTATION = /^\s*(UPDATE|INSERT|DELETE)/i

async function run(input: unknown = INPUT) {
  return updateChartAndMaybeRecompute({ chartId: CHART, principalId: 'owner-uid', input })
}

beforeEach(() => {
  mockGetPool.mockReset()
  mockDispatch.mockReset()
})

describe('updateChartAndMaybeRecompute — validation', () => {
  it('rejects invalid input before opening a transaction', async () => {
    setup()
    const err = await run({ ...INPUT, lat: 200 }).catch((e) => e)
    expect(err).toBeInstanceOf(ChartUpdateError)
    expect(err.code).toBe('VALIDATION_FAILED')
    expect(err.fields).toHaveProperty('lat')
    expect(mockGetPool).not.toHaveBeenCalled()
  })
})

describe('updateChartAndMaybeRecompute — birthplace safety', () => {
  it('rejects a place change that keeps the former coordinates, inside the transaction, with no mutation', async () => {
    setup()
    const err = await run({ ...INPUT, birth_place: 'Cuttack' }).catch((e) => e)
    expect(err).toBeInstanceOf(ChartUpdateError)
    expect(err.code).toBe('VALIDATION_FAILED')
    expect(err.status).toBe(422)
    expect(Object.keys(err.fields).sort()).toEqual(['birth_place', 'lat', 'lon'])
    expect(statements.some((s) => MUTATION.test(s.sql))).toBe(false)
    expect(events).toEqual(['BEGIN', 'ROLLBACK'])
    expect(mockDispatch).not.toHaveBeenCalled()
  })

  it('recomputes when the place, coordinates and timezone change together', async () => {
    setup()
    const result = await run({
      ...INPUT,
      birth_place: 'Kathmandu, Nepal',
      lat: 27.7172,
      lon: 85.324,
      timezone_id: 'Asia/Kathmandu',
      tz_offset: 5.5, // Nepal was UTC+05:30 in 1984 (UTC+05:45 from 1986)
    })
    expect(result.mode).toBe('recompute-started')
    // The new place's own timezone reaches the stored inputs (it genuinely changed).
    expect(INPUT.timezone_id).not.toBe('Asia/Kathmandu')
    const update = statements.find((s) => /^\s*UPDATE charts\b/.test(s.sql) && /timezone/i.test(s.sql))
    expect(update?.params).toContain('Asia/Kathmandu')
  })
})

describe('updateChartAndMaybeRecompute — no-op and display-only', () => {
  it('no-op: locks the row, commits, and mutates nothing', async () => {
    setup()
    expect(await run()).toEqual({ mode: 'noop', chartId: CHART, changedFields: [] })
    expect(statements[0].sql).toMatch(/^BEGIN ISOLATION LEVEL SERIALIZABLE/)
    expect(has(/FOR UPDATE/)).toBe(true)
    expect(statements.some((s) => MUTATION.test(s.sql))).toBe(false)
    expect(events).toEqual(['BEGIN', 'COMMIT'])
    expect(mockDispatch).not.toHaveBeenCalled()
  })

  it('display-only: updates only the labels, with no archive, clear or run', async () => {
    setup()
    const result = await run({ ...INPUT, name: 'Renamed Native' })
    expect(result).toEqual({ mode: 'display-only', chartId: CHART, changedFields: ['name'] })
    const mutations = statements.filter((s) => MUTATION.test(s.sql))
    expect(mutations).toHaveLength(1)
    expect(mutations[0].sql).toMatch(/^UPDATE charts SET name=\$2, preferred_name=\$3, subject_name=\$4 WHERE id=\$1$/)
    expect(mutations[0].params).toEqual([CHART, 'Renamed Native', 'Test', null])
    expect(has(/FROM asset_registry/)).toBe(false)
    expect(events).toEqual(['BEGIN', 'COMMIT'])
    expect(mockDispatch).not.toHaveBeenCalled()
  })
})

describe('updateChartAndMaybeRecompute — refusals roll back', () => {
  it('an active build returns RUN_ACTIVE and rolls back', async () => {
    setup({ activeRun: 'run-live' })
    await expect(run({ ...INPUT, birth_time: '10:44' })).rejects.toMatchObject({ code: 'RUN_ACTIVE', status: 409 })
    expect(statements.some((s) => MUTATION.test(s.sql))).toBe(false)
    expect(events).toEqual(['BEGIN', 'ROLLBACK'])
  })

  it('an active build blocks even a display-only edit', async () => {
    setup({ activeRun: 'run-live' })
    await expect(run({ ...INPUT, name: 'Other' })).rejects.toMatchObject({ code: 'RUN_ACTIVE' })
  })

  it('a missing chart is CHART_NOT_FOUND', async () => {
    setup({ chart: null })
    await expect(run()).rejects.toMatchObject({ code: 'CHART_NOT_FOUND', status: 404 })
  })

  it('a protected required asset returns PROTECTED with no mutation', async () => {
    setup({ protectedIds: [W2] })
    await expect(run({ ...INPUT, birth_time: '10:44' })).rejects.toMatchObject({ code: 'PROTECTED', status: 422 })
    expect(statements.some((s) => MUTATION.test(s.sql))).toBe(false)
    expect(events).toEqual(['BEGIN', 'ROLLBACK'])
    expect(mockDispatch).not.toHaveBeenCalled()
  })

  it('a writer without a safe clear spec returns CLEAR_SPEC_MISSING and rolls back the archive and update', async () => {
    // ga_positions has a real sidecar digest, so planning succeeds and only the clear spec is missing.
    setup({ registry: [...REGISTRY, { ...REGISTRY[1], asset_id: 'ga_positions', layer: 'ganita', target_table: null, count_sql: null, depends_on: [] }] })
    await expect(run({ ...INPUT, birth_time: '10:44' })).rejects.toMatchObject({ code: 'CLEAR_SPEC_MISSING', status: 422 })
    expect(events).toEqual(['BEGIN', 'ROLLBACK'])
    expect(mockDispatch).not.toHaveBeenCalled()
  })

  it('a failing clear rolls back the conversation archive, chart update and run — never commits', async () => {
    setup({ failOn: /DELETE FROM kala_up/ })
    await expect(run({ ...INPUT, birth_time: '10:44' })).rejects.toMatchObject({
      code: 'RECOMPUTE_PREPARATION_FAILED',
      status: 500,
    })
    expect(idx(/UPDATE conversations/)).toBeGreaterThan(-1)
    expect(idx(/^UPDATE charts/)).toBeGreaterThan(-1)
    expect(has(/INSERT INTO build_runs/)).toBe(false)
    expect(events).toEqual(['BEGIN', 'ROLLBACK'])
    expect(mockDispatch).not.toHaveBeenCalled()
  })
})

describe('updateChartAndMaybeRecompute — successful correction', () => {
  it('runs the full sequence in order, then dispatches after COMMIT', async () => {
    setup()
    const result = await run({ ...INPUT, birth_time: '10:44' })
    expect(result).toEqual({ mode: 'recompute-started', chartId: CHART, changedFields: ['birth_time'], runId: 'run-new' })

    const order = [
      idx(/FOR UPDATE/),
      idx(/FROM asset_registry/),
      idx(/UPDATE conversations[\s\S]*archive_reason='chart_details_changed'/),
      idx(/^UPDATE charts/),
      idx(/DELETE FROM mimamsa_journal/),
      idx(/DELETE FROM kala_down/),
      idx(/DELETE FROM kala_up/),
      idx(/UPDATE asset_throughput/),
      idx(/INSERT INTO build_runs/),
      idx(/INSERT INTO build_run_assets/),
      idx(/SET archived_by_run_id/),
    ]
    expect(order.every((i) => i >= 0)).toBe(true)
    expect([...order].sort((a, b) => a - b)).toEqual(order)
    expect(events).toEqual(['BEGIN', 'COMMIT', 'DISPATCH'])
    expect(mockDispatch).toHaveBeenCalledWith('run-new', { failurePrefix: 'JOB_DISPATCH_FAILED' })
  })

  it('locks every not-yet-locked conversation — active or manually archived — with the exact pre-correction snapshot', async () => {
    setup()
    await run({ ...INPUT, birth_time: '10:44' })
    const archive = statements.find((s) => /UPDATE conversations[\s\S]*RETURNING id/.test(s.sql))!
    // A manual archive must not escape the lock and be un-archived and continued later.
    expect(archive.sql).toMatch(/WHERE chart_id=\$1 AND archive_reason IS NULL/)
    expect(archive.sql).not.toMatch(/archived_at IS NULL/)
    // Keep a manual archive's original archive time; stamp active ones now.
    expect(archive.sql).toMatch(/archived_at=COALESCE\(archived_at, NOW\(\)\)/)
    const snapshot = JSON.parse(archive.params[1] as string)
    expect(snapshot).toEqual({
      name: 'Test Native',
      preferred_name: 'Test',
      subject_name: null,
      birth_date: '1984-02-05',
      birth_time: '10:43:00',
      birth_place: 'Bhubaneswar',
      birth_lat: 20.2961,
      birth_lng: 85.8245,
      timezone_id: 'Asia/Kolkata',
      effective_tz_offset_minutes: 330,
      ayanamshas: ['lahiri'],
      captured_at: expect.any(String),
    })
    expect(Object.keys(snapshot)).not.toContain('owner_id')
  })

  it('links the new run only to the conversations this correction archived', async () => {
    setup({ archivedIds: ['conv-a'] })
    await run({ ...INPUT, birth_time: '10:44' })
    const link = statements.find((s) => /SET archived_by_run_id/.test(s.sql))!
    expect(link.sql).toMatch(/WHERE id=ANY\(\$1::uuid\[\]\)/)
    expect(link.params).toEqual([['conv-a'], 'run-new'])
  })

  it('skips the run link when there was nothing to archive', async () => {
    setup({ archivedIds: [] })
    await run({ ...INPUT, birth_time: '10:44' })
    expect(has(/SET archived_by_run_id/)).toBe(false)
  })

  it('marks all five preserved chart-context surfaces stale for this chart, stamped with the new run id, before COMMIT', async () => {
    setup()
    await run({ ...INPUT, birth_time: '10:44' })
    const commitIdx = idx(/^COMMIT/)
    for (const table of [
      'event_chart_state_index',
      'mimamsa_predictions',
      'brahma_mimamsa_prediction_ledger',
      'brahma_prospective_ledger',
      'mimamsa_calibration_snapshot',
    ]) {
      const stmt = statements.find((s) => new RegExp(`UPDATE ${table}\\b`).test(s.sql))
      expect(stmt, `expected an UPDATE ${table} statement`).toBeDefined()
      expect(stmt!.params).toEqual([CHART, 'run-new'])
      // Runs after the run id is known, before COMMIT (inside the same transaction).
      const stmtIdx = idx(new RegExp(`UPDATE ${table}\\b`))
      expect(idx(/INSERT INTO build_runs/)).toBeLessThan(stmtIdx)
      expect(stmtIdx).toBeLessThan(commitIdx)
    }
  })

  it('rolls back the staleness marking along with everything else on a later failure', async () => {
    setup({ failOn: /SET archived_by_run_id/ })
    const err = await run({ ...INPUT, birth_time: '10:44' }).catch((e) => e)
    expect(err).toBeInstanceOf(ChartUpdateError)
    expect(events).toEqual(['BEGIN', 'ROLLBACK'])
    // The staleness UPDATEs were issued (and will be rolled back with everything else) —
    // proving they run inside the same transaction, not after it.
    expect(has(/UPDATE event_chart_state_index/)).toBe(true)
  })

  it('updates the chart-defining inputs in place and never its identity, owner or grants', async () => {
    setup()
    // The ayanamsha edit is part of this "today's behaviour" test, so the policy is `off`.
    await updateChartAndMaybeRecompute({
      chartId: CHART,
      principalId: 'owner-uid',
      input: { ...INPUT, birth_time: '10:44', ayanamshas: ['true_chitra', 'lahiri'] },
      ayanamshaPolicy: 'off',
    })
    const update = statements.find((s) => /^UPDATE charts/.test(s.sql))!
    expect(update.sql).not.toMatch(/\bid\s*=\s*\$\d+\s*,|owner_id|client_id/)
    expect(update.params[0]).toBe(CHART)
    expect(update.params).toContain('10:44:00')
    expect(update.params).toContain('lahiri,true_chitra')
    expect(has(/chart_grants|consent|DELETE FROM charts/)).toBe(false)
  })

  it('preserves life events and answered journal rows; event_chart_state_index is marked stale, never deleted', async () => {
    setup()
    await run({ ...INPUT, birth_time: '10:44' })
    // life_events is never referenced at all — not even to mark it stale (it
    // carries no derived chart-context data of its own).
    expect(has(/life_events/)).toBe(false)
    // event_chart_state_index is preserved by an additive UPDATE (staleness
    // marker), never a DELETE — the row itself is never destroyed.
    expect(has(/DELETE FROM event_chart_state_index/)).toBe(false)
    expect(has(/UPDATE event_chart_state_index/)).toBe(true)
    const journal = statements.find((s) => /mimamsa_journal/.test(s.sql))!
    expect(journal.sql).toMatch(/answered_at IS NULL/)
  })

  it('resets throughput for exactly the planned per-chart writers', async () => {
    setup()
    await run({ ...INPUT, birth_time: '10:44' })
    const reset = statements.find((s) => /UPDATE asset_throughput/.test(s.sql))!
    expect(reset.sql).toMatch(/SET state='dormant'/)
    expect(reset.params[0]).toBe(CHART)
    expect([...(reset.params[1] as string[])].sort()).toEqual([W1, W2, 'mi_abhilekha'].filter((id) => DIGESTS[id]).sort())
  })

  it('a post-commit dispatch failure returns needs-rebuild with the committed run', async () => {
    setup()
    mockDispatch.mockResolvedValue({ ok: false, code: 'JOB_DISPATCH_FAILED', message: 'spawn ENOENT' })
    const result = await run({ ...INPUT, birth_time: '10:44' })
    expect(result).toEqual({
      mode: 'needs-rebuild',
      chartId: CHART,
      changedFields: ['birth_time'],
      runId: 'run-new',
      error: 'spawn ENOENT',
    })
    expect(events).toEqual(['BEGIN', 'COMMIT'])
  })
})

// ── Ayanamsha edit guard (SS N-319) ─────────────────────────────────────────
// Editing the ayanamshas of an EXISTING chart is the destructive path (archive
// all conversations, strict clear, throughput reset, global rebuild). The
// policy switch decides whether such a request may run; nothing is written
// when it refuses, and every other kind of edit is unaffected.
describe('updateChartAndMaybeRecompute — ayanamsha edit guard', () => {
  const AYANAMSHA_CHANGE = { ...INPUT, ayanamshas: ['kp', 'lahiri'] }
  const runWith = (ayanamshaPolicy: 'block_all' | 'warn' | 'off', input: unknown) =>
    updateChartAndMaybeRecompute({ chartId: CHART, principalId: 'owner-uid', input, ayanamshaPolicy })
  const nothingWritten = () => {
    expect(statements.some((s) => MUTATION.test(s.sql))).toBe(false)
    expect(has(/FROM asset_registry/)).toBe(false)
    expect(events).toEqual(['BEGIN', 'ROLLBACK'])
    expect(mockDispatch).not.toHaveBeenCalled()
  }

  it('block_all refuses an ayanamsha edit with a plain message and writes nothing', async () => {
    setup()
    const err = await runWith('block_all', AYANAMSHA_CHANGE).catch((e) => e)
    expect(err).toBeInstanceOf(ChartUpdateError)
    expect(err.code).toBe('AYANAMSHA_EDIT_BLOCKED')
    expect(err.status).toBe(403)
    expect(err.message).toMatch(/ayanamsha of an existing chart can't be changed here/i)
    expect(err.message).toMatch(/contact support/i)
    expect(err.fields).toHaveProperty('ayanamshas')
    nothingWritten()
  })

  it('block_all refuses a mixed request as a whole, naming the ayanamsha; the birth-time change is not applied', async () => {
    setup()
    const err = await runWith('block_all', { ...AYANAMSHA_CHANGE, birth_time: '10:44', name: 'Renamed' }).catch((e) => e)
    expect(err.code).toBe('AYANAMSHA_EDIT_BLOCKED')
    expect(err.message).toMatch(/ayanamsha/i)
    expect(err.message).toMatch(/nothing was saved/i)
    nothingWritten()
  })

  it('block_all ignores confirm_destructive', async () => {
    setup()
    await expect(runWith('block_all', { ...AYANAMSHA_CHANGE, confirm_destructive: true })).rejects.toMatchObject({
      code: 'AYANAMSHA_EDIT_BLOCKED',
    })
    nothingWritten()
  })

  it('warn without confirmation returns a 409 that says it erases built results, archives conversations and needs confirmation', async () => {
    setup()
    const err = await runWith('warn', AYANAMSHA_CHANGE).catch((e) => e)
    expect(err.code).toBe('AYANAMSHA_EDIT_NEEDS_CONFIRMATION')
    expect(err.status).toBe(409)
    expect(err.message).toMatch(/erases all built results/i)
    expect(err.message).toMatch(/archives its conversations/i)
    expect(err.message).toMatch(/requires confirmation/i)
    nothingWritten()
  })

  it('warn with confirm_destructive: true runs the full destructive recompute exactly as before', async () => {
    setup()
    const result = await runWith('warn', { ...AYANAMSHA_CHANGE, confirm_destructive: true })
    expect(result).toEqual({ mode: 'recompute-started', chartId: CHART, changedFields: ['ayanamshas'], runId: 'run-new' })
    expect(has(/UPDATE conversations[\s\S]*archive_reason='chart_details_changed'/)).toBe(true)
    expect(statements.find((s) => /^\s*UPDATE charts\b/.test(s.sql))?.params).toContain('kp,lahiri')
    expect(events).toEqual(['BEGIN', 'COMMIT', 'DISPATCH'])
  })

  it('off is today’s behaviour: an ayanamsha edit recomputes without any flag', async () => {
    setup()
    const result = await runWith('off', AYANAMSHA_CHANGE)
    expect(result.mode).toBe('recompute-started')
    expect(events).toEqual(['BEGIN', 'COMMIT', 'DISPATCH'])
  })

  it('the default policy (env unset) is block_all', async () => {
    vi.stubEnv('CHART_AYANAMSHA_EDIT_POLICY', '')
    setup()
    await expect(run(AYANAMSHA_CHANGE)).rejects.toMatchObject({ code: 'AYANAMSHA_EDIT_BLOCKED' })
    vi.unstubAllEnvs()
  })

  it('the env var selects the policy at call time', async () => {
    vi.stubEnv('CHART_AYANAMSHA_EDIT_POLICY', 'warn')
    setup()
    await expect(run(AYANAMSHA_CHANGE)).rejects.toMatchObject({ code: 'AYANAMSHA_EDIT_NEEDS_CONFIRMATION' })
    vi.unstubAllEnvs()
  })

  it.each(['block_all', 'warn', 'off'] as const)('%s: a birth-time edit still recomputes (no ayanamsha change)', async (policy) => {
    setup()
    const result = await runWith(policy, { ...INPUT, birth_time: '10:44' })
    expect(result).toMatchObject({ mode: 'recompute-started', changedFields: ['birth_time'] })
  })

  it.each(['block_all', 'warn', 'off'] as const)('%s: a name-only edit stays display-only', async (policy) => {
    setup()
    expect(await runWith(policy, { ...INPUT, name: 'Renamed Native' })).toEqual({
      mode: 'display-only',
      chartId: CHART,
      changedFields: ['name'],
    })
  })

  it.each(['block_all', 'warn', 'off'] as const)('%s: an unchanged ayanamsha list is a no-op', async (policy) => {
    setup()
    expect(await runWith(policy, INPUT)).toEqual({ mode: 'noop', chartId: CHART, changedFields: [] })
  })

  it.each([
    ['a long-form stored value against the short id', 'lahiri_chitrapaksha', ['lahiri']],
    ['a mixed-form, differently ordered stored list against the short ids', 'krishnamurti,lahiri_chitrapaksha', ['lahiri', 'kp']],
    ['a legacy spelling of True Chitra', 'true_citra,lahiri', ['true_chitra', 'lahiri']],
  ])('block_all: %s is NOT an ayanamsha change', async (_label, storedValue, submitted) => {
    setup({ chart: { ...STORED, ayanamsa: storedValue } })
    expect(await runWith('block_all', { ...INPUT, ayanamshas: submitted })).toEqual({
      mode: 'noop',
      chartId: CHART,
      changedFields: [],
    })
  })

  it('block_all: an omitted ayanamshas list never counts as an edit, even when the stored list holds a legacy id the form cannot send', async () => {
    setup({ chart: { ...STORED, ayanamsa: 'lahiri,fagan_bradley' } })
    const { ayanamshas: _omit, ...withoutAyanamshas } = INPUT
    void _omit
    expect(await runWith('block_all', { ...withoutAyanamshas, name: 'Renamed Native' })).toMatchObject({
      mode: 'display-only',
      changedFields: ['name'],
    })
    // and the stored ayanamsa is never rewritten by a display-only edit
    expect(statements.filter((s) => MUTATION.test(s.sql))).toHaveLength(1)
  })

  it('block_all: an omitted ayanamshas list with a birth-time edit keeps the stored list in the recompute', async () => {
    setup({ chart: { ...STORED, ayanamsa: 'lahiri,fagan_bradley' } })
    const { ayanamshas: _omit, ...withoutAyanamshas } = INPUT
    void _omit
    await runWith('block_all', { ...withoutAyanamshas, birth_time: '10:44' })
    expect(statements.find((s) => /^\s*UPDATE charts\b/.test(s.sql))?.params).toContain('fagan_bradley,lahiri')
  })

  it('a genuine change away from a legacy id is still an ayanamsha change under block_all', async () => {
    setup({ chart: { ...STORED, ayanamsa: 'lahiri,fagan_bradley' } })
    await expect(runWith('block_all', INPUT)).rejects.toMatchObject({ code: 'AYANAMSHA_EDIT_BLOCKED' })
    nothingWritten()
  })

  it('the guard answers first: a blocked edit is reported as blocked even while a build is active', async () => {
    setup({ activeRun: 'run-live' })
    await expect(runWith('block_all', AYANAMSHA_CHANGE)).rejects.toMatchObject({ code: 'AYANAMSHA_EDIT_BLOCKED' })
  })
})
