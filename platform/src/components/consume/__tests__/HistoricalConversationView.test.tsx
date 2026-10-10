import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

vi.mock('next/link', () => ({
  default: ({ href, children, ...rest }: { href: string; children: React.ReactNode } & Record<string, unknown>) => (
    <a href={href} {...rest}>{children}</a>
  ),
}))

import { HistoricalConversationView } from '../HistoricalConversationView'

const historical = {
  id: 'conv-1',
  chart_id: 'c1',
  title: 'Career reading',
  archived_at: '2026-09-27T10:00:00Z',
  archive_reason: 'chart_details_changed' as const,
  archived_chart_snapshot: {
    name: 'Test Native',
    preferred_name: null,
    subject_name: null,
    birth_date: '1984-02-05',
    birth_time: '10:43:00',
    birth_place: 'Bhubaneswar',
    birth_lat: 20.2961,
    birth_lng: 85.8245,
    timezone_id: 'Asia/Kolkata',
    effective_tz_offset_minutes: 330,
    ayanamshas: ['lahiri', 'true_chitra'],
    captured_at: '2026-09-27T10:00:00Z',
  },
}

const messages = [
  { id: 'm1', role: 'user' as const, text: 'What about my career?', createdAt: '2026-09-01T10:00:00Z' },
  { id: 'm2', role: 'assistant' as const, text: 'The tenth house suggests…', createdAt: '2026-09-01T10:00:05Z' },
]

describe('HistoricalConversationView', () => {
  it('states that the reading belongs to the pre-correction chart details', () => {
    render(<HistoricalConversationView conversation={historical} messages={messages} />)
    expect(screen.getByRole('note')).toHaveTextContent(/before the chart details were corrected/i)
    expect(screen.getByText(/historical · read-only/i)).toBeInTheDocument()
  })

  it('shows the old birth details from the snapshot, not the current chart', () => {
    render(<HistoricalConversationView conversation={historical} messages={messages} />)
    expect(screen.getByText(/05 Feb 1984/i)).toBeInTheDocument()
    const details = screen.getByRole('note')
    expect(details).toHaveTextContent('10:43')
    expect(details).toHaveTextContent('Bhubaneswar')
    expect(details).toHaveTextContent('Asia/Kolkata')
    expect(details).toHaveTextContent('UTC+05:30')
    expect(details).toHaveTextContent('20.2961')
    expect(details).toHaveTextContent('Lahiri (primary), True Chitra')
  })

  it('renders the transcript with speakers', () => {
    render(<HistoricalConversationView conversation={historical} messages={messages} />)
    expect(screen.getByText('What about my career?')).toBeInTheDocument()
    expect(screen.getByText('The tenth house suggests…')).toBeInTheDocument()
  })

  it('has no composer and no actions', () => {
    render(<HistoricalConversationView conversation={historical} messages={messages} />)
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /send|regenerate|unarchive|continue|delete/i })).not.toBeInTheDocument()
    expect(screen.queryAllByRole('button')).toHaveLength(0)
  })

  it('links back to the chart workspace', () => {
    render(<HistoricalConversationView conversation={historical} messages={messages} />)
    expect(screen.getByRole('link', { name: /jātaka workspace/i })).toHaveAttribute('href', '/clients/c1')
  })

  it('marks missing snapshot values as unavailable rather than inventing them', () => {
    render(
      <HistoricalConversationView
        conversation={{ ...historical, archived_chart_snapshot: { ...historical.archived_chart_snapshot, timezone_id: null, effective_tz_offset_minutes: null, birth_lat: null, birth_lng: null } }}
        messages={messages}
      />,
    )
    expect(screen.getByRole('note')).toHaveTextContent(/timezone not recorded/i)
    expect(screen.getByRole('note')).toHaveTextContent(/coordinates not recorded/i)
  })
})
