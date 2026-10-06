import { afterEach, expect, it, vi } from 'vitest'
import { act, renderHook, waitFor } from '@testing-library/react'
import { useAssetStats } from '@/hooks/useAssetStats'
import { statOf } from './fixtures'
afterEach(() => vi.unstubAllGlobals())
it('updates evidence errors and timestamps even when row count and state are unchanged', async () => {
  const old = statOf({ asset_id: 'fixture', state: 'lit', actual_rows: 9 })
  const updated = { ...old, error: 'Fictional unavailable source', last_built_at: '2026-10-05T19:00:00Z' }
  vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce({ ok: true, json: async () => ({ data: { assets: [old] } }) })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ data: { assets: [updated] } }) })
    .mockResolvedValue({ ok: false, status: 503 }))
  const { result } = renderHook(() => useAssetStats({ chartId: 'fictional-chart' }))
  await waitFor(() => expect(result.current.stats.get('fixture')?.error).toBeNull())
  act(() => result.current.refetch())
  await waitFor(() => expect(result.current.stats.get('fixture')?.error).toBe(updated.error))
  expect(result.current.stats.get('fixture')?.last_built_at).toBe(updated.last_built_at)
  act(() => result.current.refetch())
  await waitFor(() => expect(result.current.error).toBe('HTTP 503'))
  expect(result.current.stats.get('fixture')?.error).toBe(updated.error)
})
