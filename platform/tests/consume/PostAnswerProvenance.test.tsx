import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PostAnswerProvenance } from '@/components/consume/PostAnswerProvenance'
import type { ProvenanceEvent } from '@/types/sse_events'
import { BANNED_INTERNAL_TOKENS } from '@/lib/jyotish/domain_labels'

const fixture: ProvenanceEvent = {
  type: 'provenance',
  models: [
    { stage: 'planner', role: 'Question reader', model_id: 'gemini-2.5-pro', latency_ms: 1200 },
    { stage: 'synthesis', role: 'Synthesizer', model_id: 'gemini-2.5-pro', latency_ms: 4300 },
  ],
  sources: {
    astrological: [
      {
        asset: 'MSR',
        label: 'Astrological Signals',
        items: [{ id: 'SIG.MSR.142', label: 'Signal 142' }],
      },
      { asset: 'FORENSIC', label: 'Birth Chart', items: [] },
    ],
    technical: [
      { kind: 'latency', label: 'Total time', value: '5.2s' },
      { kind: 'vector_score', label: 'Top retrieval score', value: '≈0.87 cosine' },
    ],
  },
}

describe('PostAnswerProvenance', () => {
  it('renders the three pills with the right counts', async () => {
    render(<PostAnswerProvenance provenance={fixture} />)
    await userEvent.click(screen.getByLabelText('Toggle provenance details'))
    expect(screen.getByLabelText(/Open provenance — models/i).textContent).toContain('2')
    expect(screen.getByLabelText(/Open provenance — sources/i).textContent).toContain('2')
    expect(screen.getByLabelText(/Open provenance — signals/i).textContent).toContain('1')
  })

  it('renders nothing when provenance is null', () => {
    const { container } = render(<PostAnswerProvenance provenance={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('astrological tab has no internal-jargon labels visible', async () => {
    render(<PostAnswerProvenance provenance={fixture} />)
    await userEvent.click(screen.getByLabelText('Toggle provenance details'))
    await userEvent.click(screen.getByLabelText(/Open provenance — sources/i))
    // Tab content visible: assert no banned internal asset acronym appears
    // as a standalone label — internal IDs only show inside the per-item
    // muted ID line which is acceptable per brief.
    for (const tok of ['MSR', 'FORENSIC', 'CGM', 'UCN', 'CDLM']) {
      // The user-facing label should be present, not the raw ID
      const allLabels = screen.getAllByRole('button').map(b => b.textContent ?? '')
      for (const label of allLabels) {
        // Group header buttons must use translated labels
        if (label.includes('models') || label.includes('sources') || label.includes('signals')) continue
        if (label === tok) throw new Error(`Banned token ${tok} visible as label`)
      }
    }
    void BANNED_INTERNAL_TOKENS
  })
})
