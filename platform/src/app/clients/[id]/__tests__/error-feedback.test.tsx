import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import ChartError from '../error'
import ShareError from '@/app/share/[slug]/error'

beforeEach(() => vi.spyOn(console, 'error').mockImplementation(() => {}))
afterEach(() => vi.restoreAllMocks())

it('shows a neutral chart failure and retries the server route', () => {
  const retry = vi.fn()
  render(<ChartError error={new Error('internal chart detail')} unstable_retry={retry} />)

  expect(screen.getByText('The chart workspace could not be loaded.')).toBeInTheDocument()
  expect(screen.queryByText('internal chart detail')).not.toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Back to Birth Charts' })).toHaveAttribute('href', '/dashboard')
  fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
  expect(retry).toHaveBeenCalledTimes(1)
})

it('keeps a failed share read distinct from an invalid link', () => {
  const retry = vi.fn()
  render(<ShareError error={new Error('internal read failure')} unstable_retry={retry} />)

  expect(screen.getByText('The shared reading is temporarily unavailable.')).toBeInTheDocument()
  expect(screen.queryByText(/old link|was not found/i)).not.toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
  expect(retry).toHaveBeenCalledTimes(1)
})
