import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ProvenanceChip } from './ProvenanceChip'

describe('ProvenanceChip', () => {
  it('renders Repo-declared for repo_declared', () => {
    render(<ProvenanceChip kind="repo_declared" />)
    expect(screen.getByText('Repo-declared')).toBeInTheDocument()
  })
  it('renders Evidence-derived for evidence_derived', () => {
    render(<ProvenanceChip kind="evidence_derived" />)
    expect(screen.getByText('Evidence-derived')).toBeInTheDocument()
  })
})
