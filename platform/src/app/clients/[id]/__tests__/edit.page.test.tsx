/**
 * /clients/[id]/edit — loads every stored editable field for owners only
 * (Jātaka chart workspace, Task 7). The initial offset is derived with the same
 * resolver the PATCH route verifies against; a missing or invalid timezone is
 * surfaced (null), never silently defaulted.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render } from '@testing-library/react'

vi.mock('server-only', () => ({}))

const { mockQuery, mockResolveAccess, mockRedirect, formProps } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockResolveAccess: vi.fn(),
  mockRedirect: vi.fn(() => {
    throw new Error('NEXT_REDIRECT')
  }),
  formProps: { current: null as unknown },
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/auth/chart-page-guard', () => ({ resolveChartPageAccess: mockResolveAccess }))
vi.mock('next/navigation', () => ({ redirect: mockRedirect }))
vi.mock('@/components/clients/EditClientForm', () => ({
  EditClientForm: (props: unknown) => {
    formProps.current = props
    return null
  },
}))

import EditPage from '../edit/page'

const ROW = {
  id: 'c1',
  name: 'Test Native',
  preferred_name: null,
  subject_name: 'Native A',
  birth_date: '1984-02-05',
  birth_time: '10:43:00',
  birth_place: 'Bhubaneswar',
  birth_lat: 20.2961,
  birth_lng: 85.8245,
  timezone_id: 'Asia/Kolkata',
  ayanamsa: 'true_chitra,lahiri',
}

async function load() {
  render(await EditPage({ params: Promise.resolve({ id: 'c1' }) }))
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.unstubAllEnvs()
  vi.stubEnv('CHART_AYANAMSHA_EDIT_POLICY', '')
  formProps.current = null
  mockResolveAccess.mockResolvedValue({ user: { uid: 'u' }, role: 'guest', permission: 'all', canBuild: true })
  mockQuery.mockResolvedValue({ rows: [ROW] })
})

describe('/clients/[id]/edit', () => {
  it('sends a view-only grantee back to the workspace', async () => {
    mockResolveAccess.mockResolvedValue({ user: { uid: 'u' }, role: 'guest', permission: 'view', canBuild: false })
    await expect(load()).rejects.toThrow('NEXT_REDIRECT')
    expect(mockRedirect).toHaveBeenCalledWith('/clients/c1')
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('loads every editable stored field as text-stable values', async () => {
    await load()
    const [sql] = mockQuery.mock.calls[0]
    for (const column of ['preferred_name', 'subject_name', 'timezone_id', 'ayanamsa']) expect(sql).toContain(column)
    expect(sql).toMatch(/birth_date::text/)
    expect(sql).toMatch(/birth_time::text/)
    expect(formProps.current).toEqual({
      ayanamshaEditPolicy: 'block_all',
      chart: {
        id: 'c1',
        name: 'Test Native',
        preferred_name: null,
        subject_name: 'Native A',
        birth_date: '1984-02-05',
        birth_time: '10:43:00',
        birth_place: 'Bhubaneswar',
        birth_lat: 20.2961,
        birth_lng: 85.8245,
        timezone_id: 'Asia/Kolkata',
        tz_offset_hours: 5.5,
        ayanamshas: ['lahiri', 'true_chitra'],
      },
    })
  })

  it('passes a null offset for a missing or invalid timezone instead of defaulting', async () => {
    mockQuery.mockResolvedValue({ rows: [{ ...ROW, timezone_id: 'Not/AZone' }] })
    await load()
    expect((formProps.current as { chart: { tz_offset_hours: number | null } }).chart.tz_offset_hours).toBeNull()
    mockQuery.mockResolvedValue({ rows: [{ ...ROW, timezone_id: null }] })
    await load()
    expect((formProps.current as { chart: { timezone_id: string | null } }).chart.timezone_id).toBeNull()
  })

  it.each([
    ['warn', 'warn'],
    ['off', 'off'],
    ['  WARN ', 'warn'],
    ['nonsense', 'block_all'],
  ])('hands the server-read ayanamsha edit policy %j to the form as %s', async (env, expected) => {
    vi.stubEnv('CHART_AYANAMSHA_EDIT_POLICY', env)
    vi.spyOn(console, 'error').mockImplementation(() => undefined)
    await load()
    expect((formProps.current as { ayanamshaEditPolicy: string }).ayanamshaEditPolicy).toBe(expected)
  })

  it('folds a long-form stored ayanamsha to the short id the form offers', async () => {
    mockQuery.mockResolvedValue({ rows: [{ ...ROW, ayanamsa: 'lahiri_chitrapaksha' }] })
    await load()
    expect((formProps.current as { chart: { ayanamshas: string[] } }).chart.ayanamshas).toEqual(['lahiri'])
  })
})
