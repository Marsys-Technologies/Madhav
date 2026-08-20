/**
 * Lane P2-A (G2-A) — proves the already-built `TableBlock`/`VerseBlock`/
 * `GapRibbonBlock` renderers actually activate when `FrozenBlock` receives a
 * real committed block carrying that `kind` — the exact shape the live
 * route now produces at commit time when the semantic-blocks flag is on.
 * Before this lane, nothing on the live path ever passed `kind !== 'paragraph'`
 * to this component (the wire never carried a real kind), so these renderers
 * were reachable only from hand-authored fixtures.
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FrozenBlock } from '../FrozenBlock'
import type { CommittedBlock } from '../../state/types'

function renderBlock(block: CommittedBlock) {
  return render(<FrozenBlock turnId="t1" block={block} citations={{}} />)
}

describe('FrozenBlock — kind routing', () => {
  it('renders a table block through TableBlock', () => {
    const block: CommittedBlock = {
      id: 'b1',
      kind: 'table',
      html: '',
      table: { headers: ['Planet', 'Sign'], rows: [['Sun', 'Capricorn']] },
    }
    renderBlock(block)
    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(screen.getByText('Planet')).toBeInTheDocument()
    expect(screen.getByText('Sun')).toBeInTheDocument()
    expect(screen.getByText('Capricorn')).toBeInTheDocument()
  })

  it('renders a verse block through VerseBlock', () => {
    const block: CommittedBlock = {
      id: 'b2',
      kind: 'verse',
      html: 'A classical line.\n— BPHS 12.4',
    }
    const { container } = renderBlock(block)
    expect(container.querySelector('.pp-verse')).not.toBeNull()
    expect(screen.getByText(/A classical line/)).toBeInTheDocument()
  })

  it('renders a gap_ribbon block through GapRibbonBlock', () => {
    const block: CommittedBlock = {
      id: 'b3',
      kind: 'gap_ribbon',
      html: '',
      gapText: 'The chart is silent — no factor consulted distinguishes them.',
    }
    renderBlock(block)
    expect(screen.getByText('The chart is silent here')).toBeInTheDocument()
    expect(screen.getByText(/no factor consulted distinguishes them/)).toBeInTheDocument()
  })

  it('renders a heading block as an <h3>', () => {
    const block: CommittedBlock = { id: 'b4', kind: 'heading', html: 'Career Outlook' }
    renderBlock(block)
    expect(screen.getByRole('heading', { level: 3, name: 'Career Outlook' })).toBeInTheDocument()
  })

  it('a plain paragraph block still renders as prose (unchanged, pre-lane behavior)', () => {
    const block: CommittedBlock = { id: 'b5', kind: 'paragraph', html: 'Ordinary prose text.' }
    renderBlock(block)
    expect(screen.getByText('Ordinary prose text.')).toBeInTheDocument()
  })
})
