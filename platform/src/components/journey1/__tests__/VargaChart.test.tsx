import '@testing-library/jest-dom/vitest'
import { afterEach, describe, expect, it } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { VargaChart } from '../VargaChart'
import type { ForensicChart } from '@/lib/forensic/snapshot'

afterEach(cleanup)
const empty: ForensicChart = {
  chartId: 'synthetic-chart', lagnaSign: '', lagnaDegreeDms: '',
  houses: Array.from({ length: 12 }, (_, i) => ({ house: i + 1, sign: '', planets: [] })),
  topYogas: [], currentDasha: null, isEmpty: true,
}
const completed: ForensicChart = { ...empty, lagnaSign: 'Aries', lagnaDegreeDms: '1°', isEmpty: false }

describe('VargaChart absent versus lookup unavailable', () => {
  it('keeps the original empty-computation display when availability is omitted', () => {
    render(<VargaChart charts={[empty, empty, empty]} ayanamsha="Synthetic frame" />)
    expect(screen.getByRole('img', { name: 'D1 · Rāśi: not yet computed' })).toBeInTheDocument()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
  it('discloses only the failed selected chart and keeps other completed charts accessible', () => {
    render(<VargaChart charts={[completed, empty, completed]} ayanamsha="Synthetic frame" availability={[true, false, true]} />)
    expect(screen.getByRole('img')).toHaveAccessibleName(/D1 · Rāśi, North Indian chart. Lagna Aries/)
    fireEvent.click(screen.getByRole('button', { name: 'D9 · Navāṃśa' }))
    expect(screen.getByRole('status')).toHaveTextContent('D9 · Navāṃśa is temporarily unavailable.')
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
    expect(screen.queryByText('Not yet computed')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'D10 · Daśāṃśa' }))
    expect(screen.getByRole('img')).toHaveAccessibleName(/D10 · Daśāṃśa, North Indian chart. Lagna Aries/)
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
  it('a failed D1 does not conceal a successful empty D9 or completed D10', () => {
    render(<VargaChart charts={[empty, empty, completed]} ayanamsha="Synthetic frame" availability={[false, true, true]} />)
    expect(screen.getByRole('status')).toHaveTextContent('D1 · Rāśi is temporarily unavailable.')
    fireEvent.change(screen.getByRole('slider', { name: 'Divisional chart' }), { target: { value: '1' } })
    expect(screen.getByRole('img', { name: 'D9 · Navāṃśa: not yet computed' })).toBeInTheDocument()
    fireEvent.change(screen.getByRole('slider', { name: 'Divisional chart' }), { target: { value: '2' } })
    expect(screen.getByRole('img')).toHaveAccessibleName(/Lagna Aries/)
  })
})
