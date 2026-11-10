import { render } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ReviewSourcePage from '@/app/clients/[id]/consult/[conversationId]/source/[partId]/page'
import { ReviewSourceFocus } from '@/components/consume/ReviewSourceFocus'
import { ReviewSourceReading } from '@/components/consume/ReviewSourceReading'

const mocks = vi.hoisted(() => ({ user: vi.fn() }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mocks.user }))
vi.mock('@/components/consume/ReviewSourceReading', () => ({ ReviewSourceReading: () => null }))
vi.mock('next/navigation', () => ({
  redirect: (target: string) => { throw new Error(target) },
}))

const id = '10000000-0000-4000-8000-000000000001'
const conversationId = '10000000-0000-4000-8000-000000000002'
const partId = '10000000-0000-4000-8000-000000000003'
const sourcePage = (requestedPart = partId) =>
  ReviewSourcePage({ params: Promise.resolve({ id, conversationId, partId: requestedPart }) })

describe('path-only source bookmark', () => {
  beforeEach(() => mocks.user.mockReset())

  it('uses the existing path-only sign-in return and rejects an unsafe segment', async () => {
    mocks.user.mockResolvedValue(null)
    const path = `/clients/${id}/consult/${conversationId}/source/${partId}`
    await expect(sourcePage()).rejects.toThrow(`/login?next=${encodeURIComponent(path)}`)
    await expect(sourcePage('..')).rejects.toThrow(/^\/login$/)
  })

  it('passes the exact chart, reading, part and current user to the shared checked reader', async () => {
    mocks.user.mockResolvedValue({ uid: 'fictional-reader' })
    const page = await sourcePage()
    expect(page.type).toBe(ReviewSourceReading)
    expect(page.props).toEqual({ chartId: id, conversationId, partId, userId: 'fictional-reader', focusAnswer: true })
  })

  it('focuses the resolved answer without a URL fragment', () => {
    const answerId = 'pp-answer-fictional'
    render(<><article id={answerId} tabIndex={-1}>Fictional answer</article><ReviewSourceFocus answerId={answerId} /></>)
    expect(document.activeElement?.id).toBe(answerId)
  })
})
