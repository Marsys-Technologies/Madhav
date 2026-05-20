/**
 * X-S10 — Interactive Tables
 * Amendment 2: parent-context integration tests.
 *
 * Click-path: Chat V2 response containing a Markdown table with ≥3 data rows →
 *   table headers are clickable → clicking a header sorts rows ascending →
 *   clicking again sorts descending → Download CSV button downloads file.
 *
 * Amendment 1: NEXT_PUBLIC_MARSYS_FLAG_R10_INTERACTIVE_TABLES client-side flag;
 *   MUST be in deploy.yml --build-arg (verified separately via acceptance grep).
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, act, fireEvent } from '@testing-library/react'
import React from 'react'
import { MarkdownContent } from '@/components/chat/MarkdownContent'
import { InteractiveTable } from '@/components/chat/InteractiveTable'

// ── Parent-context shell per Amendment 2 ─────────────────────────────────────

function MarkdownShell({
  children,
  streaming = false,
}: {
  children: string
  streaming?: boolean
}) {
  return (
    <div data-testid="v2-chat-shell">
      <MarkdownContent streaming={streaming}>{children}</MarkdownContent>
    </div>
  )
}

// ── Markdown with ≥3 data rows ───────────────────────────────────────────────

const TABLE_MD = `
| Planet | Sign | Degree |
|--------|------|--------|
| Sun    | Aries | 10.5 |
| Moon   | Taurus | 22.3 |
| Mars   | Gemini | 5.1 |
| Jupiter | Cancer | 18.9 |
`

const SMALL_TABLE_MD = `
| A | B |
|---|---|
| x | 1 |
| y | 2 |
`

// ── Tests against InteractiveTable (leaf unit — supplements parent tests) ────

describe('InteractiveTable — unit', () => {
  it('renders headers and all rows', () => {
    const { getByTestId, getByText } = render(
      <InteractiveTable
        headers={['Planet', 'Sign', 'Degree']}
        rows={[
          ['Sun', 'Aries', '10.5'],
          ['Moon', 'Taurus', '22.3'],
          ['Mars', 'Gemini', '5.1'],
        ]}
      />,
    )
    expect(getByTestId('v2-interactive-table')).toBeTruthy()
    expect(getByText('Planet')).toBeTruthy()
    expect(getByText('Sun')).toBeTruthy()
    expect(getByText('Mars')).toBeTruthy()
  })

  it('clicking a header sorts rows ascending', () => {
    const { getByTestId, getAllByRole } = render(
      <InteractiveTable
        headers={['Name', 'Score']}
        rows={[
          ['Charlie', '30'],
          ['Alice', '10'],
          ['Bob', '20'],
        ]}
      />,
    )
    const header0 = getByTestId('v2-table-header-0')
    fireEvent.click(header0)

    const cells = getAllByRole('cell').filter((_, i) => i % 2 === 0) // first col
    expect(cells[0].textContent).toBe('Alice')
    expect(cells[1].textContent).toBe('Bob')
    expect(cells[2].textContent).toBe('Charlie')
  })

  it('clicking header again reverses to descending', () => {
    const { getByTestId, getAllByRole } = render(
      <InteractiveTable
        headers={['Name', 'Score']}
        rows={[
          ['Charlie', '30'],
          ['Alice', '10'],
          ['Bob', '20'],
        ]}
      />,
    )
    const header0 = getByTestId('v2-table-header-0')
    fireEvent.click(header0) // asc
    fireEvent.click(header0) // desc

    const cells = getAllByRole('cell').filter((_, i) => i % 2 === 0)
    expect(cells[0].textContent).toBe('Charlie')
    expect(cells[2].textContent).toBe('Alice')
  })

  it('sorts numerically when column contains numbers', () => {
    const { getByTestId, getAllByRole } = render(
      <InteractiveTable
        headers={['Item', 'Value']}
        rows={[
          ['c', '100'],
          ['a', '2'],
          ['b', '20'],
        ]}
      />,
    )
    fireEvent.click(getByTestId('v2-table-header-1')) // sort by numeric Value col

    const cells = getAllByRole('cell').filter((_, i) => i % 2 === 1) // second col
    expect(cells[0].textContent).toBe('2')
    expect(cells[1].textContent).toBe('20')
    expect(cells[2].textContent).toBe('100')
  })

  it('shows sort indicator ▲ on first click, ▼ on second', () => {
    const { getByTestId } = render(
      <InteractiveTable
        headers={['A']}
        rows={[['x'], ['y'], ['z']]}
      />,
    )
    fireEvent.click(getByTestId('v2-table-header-0'))
    expect(getByTestId('v2-table-sort-indicator').textContent).toBe('▲')

    fireEvent.click(getByTestId('v2-table-header-0'))
    expect(getByTestId('v2-table-sort-indicator').textContent).toBe('▼')
  })

  it('CSV download button triggers anchor click', () => {
    const createSpy = vi.spyOn(document, 'createElement')
    const { getByTestId } = render(
      <InteractiveTable
        headers={['A', 'B']}
        rows={[
          ['1', '2'],
          ['3', '4'],
          ['5', '6'],
        ]}
      />,
    )

    const mockAnchor = {
      href: '',
      download: '',
      click: vi.fn(),
    } as unknown as HTMLAnchorElement
    createSpy.mockImplementation((tag: string) => {
      if (tag === 'a') return mockAnchor
      return document.createElement.call(document, tag)
    })

    fireEvent.click(getByTestId('v2-table-download-csv'))
    expect(mockAnchor.click).toHaveBeenCalled()
    createSpy.mockRestore()
  })
})

// ── Parent-context tests per Amendment 2 ─────────────────────────────────────

describe('MarkdownContent — InteractiveTable parent-context (Amendment 2)', () => {
  beforeEach(() => {
    vi.stubEnv('NEXT_PUBLIC_MARSYS_FLAG_R10_INTERACTIVE_TABLES', 'true')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('renders InteractiveTable for ≥3 data row tables when flag=true', async () => {
    const { findByTestId } = render(<MarkdownShell>{TABLE_MD}</MarkdownShell>)
    // InteractiveTable root
    const table = await findByTestId('v2-interactive-table')
    expect(table).toBeTruthy()
  })

  it('renders CSV download button inside MarkdownContent', async () => {
    const { findByTestId } = render(<MarkdownShell>{TABLE_MD}</MarkdownShell>)
    const csvBtn = await findByTestId('v2-table-download-csv')
    expect(csvBtn).toBeTruthy()
  })

  it('clicking header inside MarkdownContent sorts rows', async () => {
    const { findByTestId, findAllByRole } = render(<MarkdownShell>{TABLE_MD}</MarkdownShell>)
    await findByTestId('v2-interactive-table') // wait for render

    const header0 = await findByTestId('v2-table-header-0')
    await act(async () => { fireEvent.click(header0) })

    // After asc sort on Planet column: Jupiter < Mars < Moon < Sun
    const cells = (await findAllByRole('cell')).filter((_, i) => i % 3 === 0)
    expect(cells[0].textContent?.trim()).toBe('Jupiter')
  })

  it('small table (<3 data rows) renders as static table, not InteractiveTable', () => {
    const { container, queryByTestId } = render(<MarkdownShell>{SMALL_TABLE_MD}</MarkdownShell>)
    expect(queryByTestId('v2-interactive-table')).toBeNull()
    expect(container.querySelector('table')).toBeTruthy()
  })
})
