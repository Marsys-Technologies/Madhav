import { afterEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, renderHook, waitFor } from '@testing-library/react'
import { useLiveStream } from '@/components/pariprashna/hooks/useLiveStream'
import { AiConsoleError } from '@/lib/ai-console/errors'
afterEach(() => { cleanup(); vi.unstubAllGlobals() })
describe('Ask HTTP failures preserve actionable safe AI errors', () => {
  it('shows the default-choice repair instead of reporting a lost network connection', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => Response.json(new AiConsoleError('AI_DEFAULT_REQUIRED').toJSON(), { status: 400 })))
    const { result } = renderHook(() => useLiveStream('chart'))
    act(() => result.current.submit('Question', { aiMode: { kind: 'byok', selection: { kind: 'default' } } }))
    await waitFor(() => expect(result.current.state.turns[0]?.status).toBe('errored'))
    expect(result.current.state.turns[0].error).toMatchObject({ sentence: 'Choose a default in AI Console before continuing.', actions: ['settings'] })
  })
  it('does not display raw error messages or secrets from an untrusted response', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => Response.json({ code: 'AI_DEFAULT_REQUIRED', message: 'SECRET_PROVIDER_PAYLOAD', retryable: false }, { status: 400 })))
    const { result } = renderHook(() => useLiveStream('chart'))
    act(() => result.current.submit('Question'))
    await waitFor(() => expect(result.current.state.turns[0]?.status).toBe('errored'))
    expect(JSON.stringify(result.current.state.turns[0].error)).not.toContain('SECRET_PROVIDER_PAYLOAD')
  })
})
