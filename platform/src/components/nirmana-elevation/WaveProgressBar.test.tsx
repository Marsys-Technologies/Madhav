import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { WaveProgressBar } from './WaveProgressBar'

const waveProgress = [
  { wave_id: 'W1' as const, label: 'ANALYZE', milestone_id: 'analysed', earned: 17, required: 40 },
  { wave_id: 'W2' as const, label: 'DECIDE', milestone_id: 'decision_accepted', earned: 0, required: 40 },
  { wave_id: 'W3' as const, label: 'IMPLEMENT', milestone_id: 'built_or_dispositioned', earned: 0, required: 40 },
  { wave_id: 'W4' as const, label: 'EXECUTE', milestone_id: 'deployed_and_executed', earned: 0, required: 40 },
  { wave_id: 'W5' as const, label: 'VERIFY+CAPSULE', milestone_id: 'verified', earned: 0, required: 40 },
  { wave_id: 'W6' as const, label: 'FREEZE', milestone_id: 'frozen', earned: 0, required: 40 },
]

describe('WaveProgressBar', () => {
  it('renders all 6 waves with their earned/required counts', () => {
    render(<WaveProgressBar waveProgress={waveProgress} />)
    expect(screen.getByText('17/40')).toBeInTheDocument()
    expect(screen.getAllByText('0/40')).toHaveLength(5)
    expect(screen.getByText('W1')).toBeInTheDocument()
    expect(screen.getByText('FREEZE')).toBeInTheDocument()
  })
})
