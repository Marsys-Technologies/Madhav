import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'

const evidence = vi.hoisted(() => ({ grantsError: false, role: 'guest' }))
vi.mock('@/components/observatory/ObservatoryScope', () => ({ useObservatoryScope: () => ({ userId: 'operator-1' }) }))
vi.mock('@/components/journey1/Titles', () => ({ PageTitle: () => <h1>User details</h1> }))
vi.mock('@tanstack/react-query', () => ({
  useQuery: ({ queryKey, enabled = true }: { queryKey: string[]; enabled?: boolean }) => {
    const source = queryKey[2]
    if (source === 'user-details') return { data: { users: [{ id: 'guest-2', name: 'Biren Sen', role: evidence.role, status: 'active' }] } }
    if (source === 'user-chart-grants') return { data: { charts: [] } }
    return { isError: evidence.grantsError, isPending: !enabled, data: { grants: [{ cliId: 'codex', productName: 'Codex CLI', granted: true, hostState: 'unavailable', apiKey: 'fixture-not-rendered', model: 'private-model-fixture' }] } }
  },
}))
import { UserDetails } from './UserDetails'
afterEach(() => { cleanup(); vi.unstubAllEnvs(); evidence.grantsError = false; evidence.role = 'guest' })
describe('UserDetails', () => {
  it('retains the selected person when opening either canonical grant editor', () => {
    vi.stubEnv('NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK', 'true')
    render(<UserDetails selectedId="guest-2" />)
    expect(screen.getByRole('link', { name: 'Review AI product grants' })).toHaveAttribute('href', '/admin?tab=ai-access&userId=guest-2')
    expect(screen.getByRole('link', { name: 'Manage selected user chart grants' })).toHaveAttribute('href', '/admin?tab=charts&guest=guest-2')
    expect(screen.getByText('Codex CLI · Granted · Host unavailable')).toBeInTheDocument()
    expect(screen.queryByRole('switch')).toBeNull()
    expect(document.body.textContent).not.toMatch(/fixture-not-rendered|private-model-fixture/)
  })
  it('reports failed grant evidence as unavailable', () => {
    vi.stubEnv('NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK', 'true')
    evidence.grantsError = true
    render(<UserDetails selectedId="guest-2" />)
    expect(screen.getByRole('alert')).toHaveTextContent('AI product grants unavailable.')
    expect(screen.queryByText('Codex CLI · Granted · Host unavailable')).toBeNull()
  })
  it('keeps the AI feature gate and labels the guest-only chart editor for other roles', () => {
    vi.stubEnv('NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK', 'false')
    evidence.role = 'super_admin'
    render(<UserDetails selectedId="guest-2" />)
    expect(screen.queryByRole('heading', { name: 'AI product grants' })).toBeNull()
    expect(screen.queryByRole('link', { name: 'Review AI product grants' })).toBeNull()
    expect(screen.getByRole('link', { name: 'Browse guest chart grants' })).toHaveAttribute('href', '/admin?tab=charts')
  })
})
