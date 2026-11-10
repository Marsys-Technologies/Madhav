import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { TimelineView } from '../TimelineView'

vi.mock('next/navigation', () => ({ useRouter: () => ({ refresh: vi.fn() }) }))

const events = [
  { id: 'career-event', category: 'career', date: '2022-06-17', body: 'Fictional career event' },
  { id: 'education-event', category: 'education', date: '2019-09', body: 'Fictional education event' },
]

it('keeps category and year filters named and announces the scoped results', async () => {
  render(<TimelineView chartId="fictional-chart" canLogEvent={false} events={events} />)

  const category = screen.getByRole('group', { name: 'Filter events by category' })
  const career = within(category).getByRole('button', { name: 'career' })
  await userEvent.click(career)

  expect(career).toHaveAttribute('aria-pressed', 'true')
  expect(screen.getByRole('status')).toHaveTextContent('Showing 1 of 2 life events.')
  expect(screen.getByText('Fictional career event')).toBeInTheDocument()
  expect(screen.queryByText('Fictional education event')).not.toBeInTheDocument()

  await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Filter events by year' }), '2019')
  expect(screen.getByRole('status')).toHaveTextContent('No events match the current filters.')
})

it('identifies a truly empty timeline and keeps a same-chart return', () => {
  render(<TimelineView chartId="fictional-chart" canLogEvent={false} events={[]} />)
  expect(screen.getByRole('status')).toHaveTextContent('No life events recorded for this chart.')
  expect(screen.getByRole('link', { name: 'Back to chart' })).toHaveAttribute('href', '/clients/fictional-chart')
})
