/**
 * chart_refusal_gate.test.ts — proves the DD-1 battery's native's-real-chart
 * refusal binds EVERY flag combination, not just `driveTurn()`'s live-prose
 * lane.
 *
 * WHY THIS TEST EXISTS (post-#1501 REFUTED finding): before this fix, the
 * refusal lived only inside `live_turn.ts`'s `driveTurn()`. `--no-live` skips
 * `collectCorpus()` entirely, so `driveTurn()` is never called — and
 * `browser_lane.ts` built its target URL (`/clients/${chartId}/pariprashna`)
 * from the raw `--chart-id` argument with NO guard at all. So
 * `--no-live --chart-id <native>` drove a real authenticated turn on the
 * native's real chart against the live default surface. The fix moves the
 * refusal into `parseArgs()` so it fires before any lane is dispatched, for
 * every flag combination. This test is the §N.8 demonstration that the fixed
 * gate is actually capable of firing (and that it does NOT fire on the
 * synthetic chart, which is the case that must keep working).
 *
 * Fully hermetic — imports `parseArgs` directly, never spawns the process,
 * never touches a network. Importing `index.ts` does NOT run `main()`: the
 * module guards its auto-invocation behind an `isDirectRun` check specifically
 * so this import is side-effect-free.
 */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { parseArgs } from '../index'
import { REAL_NATIVE_CANONICAL_CHART_ID, SYNTHETIC_TEST_CHART_ID } from '../live_turn'

function mockExit() {
  const exitSpy = vi.spyOn(process, 'exit').mockImplementation(((code?: number) => {
    throw new Error(`__PROCESS_EXIT_${code}__`)
  }) as never)
  const errSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
  return { exitSpy, errSpy }
}

describe('dd1_battery parseArgs() — native chart refusal (fix for PR #1501 REFUTED finding)', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('refuses --chart-id <native> WITH --no-live present — the exact bypass path the refutation demonstrated', () => {
    const { exitSpy, errSpy } = mockExit()
    expect(() =>
      parseArgs(['--no-live', '--chart-id', REAL_NATIVE_CANONICAL_CHART_ID]),
    ).toThrow('__PROCESS_EXIT_1__')
    expect(exitSpy).toHaveBeenCalledWith(1)
    expect(errSpy).toHaveBeenCalledWith(expect.stringContaining(REAL_NATIVE_CANONICAL_CHART_ID))
  })

  it('refuses --chart-id <native> with --no-live AND --no-browser AND --no-fixture — no flag combination reaches past the gate', () => {
    const { exitSpy } = mockExit()
    expect(() =>
      parseArgs([
        '--no-live', '--no-browser', '--no-fixture',
        '--chart-id', REAL_NATIVE_CANONICAL_CHART_ID,
      ]),
    ).toThrow('__PROCESS_EXIT_1__')
    expect(exitSpy).toHaveBeenCalledWith(1)
  })

  it('refuses --chart-id <native> under the DEFAULT flags too (no --no-live)', () => {
    const { exitSpy } = mockExit()
    expect(() => parseArgs(['--chart-id', REAL_NATIVE_CANONICAL_CHART_ID])).toThrow(
      '__PROCESS_EXIT_1__',
    )
    expect(exitSpy).toHaveBeenCalledWith(1)
  })

  it('does NOT refuse the synthetic chart with --no-live — the legitimate case must keep working', () => {
    const exitSpy = vi.spyOn(process, 'exit').mockImplementation(() => {
      throw new Error('process.exit should not be called for the synthetic chart')
    })
    const args = parseArgs(['--no-live', '--chart-id', SYNTHETIC_TEST_CHART_ID])
    expect(args.chartId).toBe(SYNTHETIC_TEST_CHART_ID)
    expect(args.live).toBe(false)
    expect(exitSpy).not.toHaveBeenCalled()
  })

  it('does NOT refuse when no --chart-id is given (defaults to the synthetic chart)', () => {
    const exitSpy = vi.spyOn(process, 'exit').mockImplementation(() => {
      throw new Error('process.exit should not be called for the default chart id')
    })
    const args = parseArgs(['--no-live'])
    expect(args.chartId).toBe(SYNTHETIC_TEST_CHART_ID)
    expect(exitSpy).not.toHaveBeenCalled()
  })
})
