import { render, screen } from '@testing-library/react'
import { expect, it, vi } from 'vitest'

const { getFlag, useAiAccountState } = vi.hoisted(() => ({ getFlag: vi.fn(), useAiAccountState: vi.fn() }))
vi.mock('@/lib/config', () => ({ getFlag }))
vi.mock('@/components/account/useAiAccountState', () => ({ useAiAccountState }))
vi.mock('@/hooks/usePersonas', () => ({ usePersonas: () => ({ personas: [] }) }))
vi.mock('@/components/observatory/ObservatoryScope', () => ({
  useObservatoryScope: () => ({ userId: 'guest-1', from: '2026-09-26', to: '2026-09-27' }),
}))
vi.mock('@tanstack/react-query', () => ({ useQuery: () => ({ isPending: true }) }))
vi.mock('next/navigation', () => ({
  usePathname: () => '/account/ai-cockpit', useSearchParams: () => new URLSearchParams(),
}))

import CockpitPage from '../page'

it.each([true, false])('matches AI Console links and reads to server availability (%s)', (enabled) => {
  getFlag.mockReturnValue(enabled)
  useAiAccountState.mockReturnValue({ error: false, clis: [] })
  render(<CockpitPage />)

  const destinations = screen.queryAllByRole('link').filter(link => link.getAttribute('href') === '/account/ai-cockpit/console')
  expect(destinations).toHaveLength(enabled ? 2 : 0)
  expect(useAiAccountState).toHaveBeenLastCalledWith(enabled)
  expect(screen.getAllByRole('link', { name: /AI Personas/ })).toHaveLength(2)
})
