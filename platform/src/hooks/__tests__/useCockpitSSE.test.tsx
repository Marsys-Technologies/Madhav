// @vitest-environment jsdom
import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useCockpitSSE } from '../useCockpitSSE'

class Source extends EventTarget {
  static instances: Source[] = []
  onerror: (() => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  close = vi.fn()
  constructor(readonly url: string) { super(); Source.instances.push(this) }
  send(type: string, data: unknown = {}) {
    this.dispatchEvent(new MessageEvent(type, { data: JSON.stringify(data) }))
  }
}

beforeEach(() => {
  vi.useFakeTimers()
  vi.setSystemTime(new Date('2026-11-15T00:00:00Z'))
  Source.instances = []
  vi.stubGlobal('EventSource', Source)
})
afterEach(() => { vi.clearAllTimers(); vi.useRealTimers(); vi.unstubAllGlobals() })

describe('Cockpit stream connection ownership', () => {
  it('keeps a healthy idle stream alive on named heartbeats without delivering bookkeeping as progress', () => {
    const onEvent = vi.fn()
    const { unmount } = renderHook(() => useCockpitSSE('chart', onEvent))
    const source = Source.instances[0]
    act(() => source.send('hello'))
    for (let i = 0; i < 5; i++) {
      act(() => { vi.advanceTimersByTime(30_000); source.send('heartbeat') })
    }
    expect(Source.instances).toHaveLength(1)
    expect(onEvent).not.toHaveBeenCalled()
    unmount()
    expect(vi.getTimerCount()).toBe(0)
  })

  it('coalesces repeated errors and watchdog expiry into one pending retry', () => {
    const { unmount } = renderHook(() => useCockpitSSE('chart', vi.fn()))
    const source = Source.instances[0]
    act(() => { source.send('hello'); vi.advanceTimersByTime(59_000); source.onerror?.(); source.onerror?.() })
    act(() => vi.advanceTimersByTime(1_000))
    expect(Source.instances).toHaveLength(2)
    unmount()
    expect(vi.getTimerCount()).toBe(0)
  })

  it('ignores stale source events/errors after replacement and reconciles only a genuine reconnect', () => {
    const event = vi.fn(), reconnect = vi.fn()
    const { unmount } = renderHook(() => useCockpitSSE('chart', event, reconnect))
    const old = Source.instances[0]
    act(() => { old.send('hello'); old.onerror?.(); vi.advanceTimersByTime(1_000) })
    const current = Source.instances[1]
    act(() => { current.send('hello'); old.onerror?.(); old.send('asset.progress', { type: 'asset.progress', asset_id: 'old' }) })
    expect(current.close).not.toHaveBeenCalled()
    expect(event).not.toHaveBeenCalled()
    expect(reconnect).toHaveBeenCalledTimes(1)
    act(() => vi.advanceTimersByTime(2_000))
    expect(Source.instances).toHaveLength(2)
    unmount()
  })

  it('cancels pending retry on unmount', () => {
    const { unmount } = renderHook(() => useCockpitSSE('chart', vi.fn()))
    act(() => Source.instances[0].onerror?.())
    unmount()
    expect(vi.getTimerCount()).toBe(0)
    act(() => vi.advanceTimersByTime(120_000))
    expect(Source.instances).toHaveLength(1)
  })

  it('stops after the existing 50-attempt failure cap', () => {
    const warning = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const { unmount } = renderHook(() => useCockpitSSE('chart', vi.fn()))
    for (let i = 0; i < 50; i++) {
      act(() => { Source.instances.at(-1)!.onerror?.(); vi.advanceTimersByTime(30_000) })
    }
    expect(Source.instances).toHaveLength(50)
    expect(warning).toHaveBeenCalledWith(expect.stringContaining('max reconnect'))
    unmount()
    expect(vi.getTimerCount()).toBe(0)
    warning.mockRestore()
  })

  it('preserves all progress payloads, latest callbacks, and chart-scoped teardown', () => {
    const first = vi.fn(), latest = vi.fn()
    const { rerender, unmount } = renderHook(({ chart, cb }) => useCockpitSSE(chart, cb), {
      initialProps: { chart: 'a & b', cb: first },
    })
    expect(Source.instances[0].url).toContain('chart_id=a%20%26%20b')
    rerender({ chart: 'a & b', cb: latest })
    const types = ['asset.state_change', 'asset.progress', 'asset.substep', 'edge.first_signal', 'run.state_change']
    act(() => { for (const type of types) Source.instances[0].send(type, { type, marker: 7 }) })
    expect(first).not.toHaveBeenCalled()
    expect(latest.mock.calls.map(([event]) => event)).toEqual(types.map(type => ({ type, marker: 7 })))
    rerender({ chart: 'second', cb: latest })
    expect(Source.instances).toHaveLength(2)
    expect(Source.instances[0].close).toHaveBeenCalled()
    unmount()
    expect(vi.getTimerCount()).toBe(0)
  })
})
