import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { fixtureV2 } from '@/lib/nirmana-elevation/__tests__/fixture-v2'
import type { NirmanaElevationSnapshotV2 } from '@/lib/nirmana-elevation/types'
import { LayerCard } from './LayerCard'

function snapshotFixture(): NirmanaElevationSnapshotV2 {
  return structuredClone(fixtureV2) as unknown as NirmanaElevationSnapshotV2
}

function layer(snapshot: NirmanaElevationSnapshotV2, layerId: string) {
  const found = snapshot.layers.find((candidate) => candidate.layer_id === layerId)
  if (!found) throw new Error(`Fixture must include ${layerId}.`)
  return found
}

describe('LayerCard', () => {
  it('renders the header, cumulative-% mini-bar, frozen/total, frontier count with its R7 limitation title, and last activity', () => {
    const snapshot = snapshotFixture()
    const l0 = layer(snapshot, 'L0')

    render(<LayerCard layer={l0} assets={snapshot.assets} onOpenAudit={vi.fn()} />)

    expect(screen.getByRole('button', { name: /^L0 · Brahmagyan/ })).toBeVisible()
    const miniBar = screen.getByRole('progressbar', { name: 'L0 cumulative completion' })
    expect(miniBar).toHaveAttribute('aria-valuenow', String(l0.completion.percent))
    expect(screen.getByText(`${l0.frozen}/${l0.assets_total ?? '—'} frozen`)).toBeVisible()
    const frontier = screen.getByText(`frontier: ${l0.frontier_ready.length} ready`)
    expect(frontier).toHaveAttribute('title', expect.stringContaining('C12'))
    expect(frontier).toHaveAttribute('title', expect.stringContaining('service-kind ancestors'))
    expect(screen.getByText(/^last activity /)).toBeVisible()
  })

  it.each([
    ['completed', 'Completed'],
    ['active', 'Active'],
    ['pending', 'Pending'],
    ['unknown', 'Unknown'],
  ] as const)('renders the %s state as the "%s" badge, never "locked"', (_state, label) => {
    const snapshot = snapshotFixture()
    const l0 = layer(snapshot, 'L0')
    if (label === 'Completed') Object.assign(l0, { assets_total: l0.frozen })
    if (label === 'Active') Object.assign(l0, { assets_total: l0.frozen + 1, completion: { ...l0.completion, earned: Math.max(l0.completion.earned, 1) } })
    if (label === 'Pending') Object.assign(l0, { assets_total: l0.frozen + 1, frozen: 0, completion: { ...l0.completion, earned: 0 } })
    if (label === 'Unknown') Object.assign(l0, { assets_total: null })

    render(<LayerCard layer={l0} assets={snapshot.assets} onOpenAudit={vi.fn()} />)

    const toggle = screen.getByRole('button', { name: /^L0 · Brahmagyan/ })
    expect(within(toggle).getByText(label)).toBeVisible()
    expect(within(toggle).queryByText(/locked/i)).not.toBeInTheDocument()
  })

  it('renders "—" and omits aria-valuenow on the mini-bar when the cumulative percent is null, never a fabricated 0', () => {
    const snapshot = snapshotFixture()
    const l0 = layer(snapshot, 'L0')
    Object.assign(l0, { completion: { earned: 0, required: 0, percent: null } })

    render(<LayerCard layer={l0} assets={snapshot.assets} onOpenAudit={vi.fn()} />)

    const miniBar = screen.getByRole('progressbar', { name: 'L0 cumulative completion' })
    expect(miniBar).not.toHaveAttribute('aria-valuenow')
    expect(screen.getByText((_, element) => element?.tagName === 'P' && element.textContent === '— · 0/0 milestones')).toBeVisible()
    expect(screen.queryByText(/^0%/)).not.toBeInTheDocument()
  })

  it('is collapsed by default, expanding on click to reveal the existing LayerStage internals (eligible-next preview, wave lanes, AssetCards) unchanged', () => {
    const snapshot = snapshotFixture()
    const l3 = layer(snapshot, 'L3')
    const onOpenAudit = vi.fn()

    const { container } = render(<LayerCard layer={l3} assets={snapshot.assets} onOpenAudit={onOpenAudit} />)

    const toggle = screen.getByRole('button', { name: /^L3 · Kala/ })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByText(/eligible-next preview/i)).not.toBeInTheDocument()

    fireEvent.click(toggle)

    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText(/eligible-next preview/i)).toBeVisible()
    // L3's one wave is not yet fully decided, so LayerStage collapses it behind its own
    // (unchanged) wave summary — open that too before reaching the AssetCard beneath it.
    const waveSummary = container.querySelector('summary')
    if (!waveSummary) throw new Error("L3's wave summary is missing.")
    fireEvent.click(waveSummary)
    expect(screen.getByRole('heading', { name: 'Kāla Smṛti' })).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: /audit details for ka_smriti/i }))
    expect(onOpenAudit).toHaveBeenCalledWith('ka_smriti')
  })

  it('never shows the raw pre-v2.1 sequential state ("Locked") in the expanded body of a non-current layer', () => {
    // L3 is not the fixture's current layer (L0 is), so `layer.state` — the pre-v2.1
    // single-current-layer sequential value LayerStage would otherwise render raw — is
    // 'locked' here. Expanding L3's card is exactly the interaction that used to leak that
    // word back into the v2.1 concurrent programme view.
    const snapshot = snapshotFixture()
    const l3 = layer(snapshot, 'L3')
    expect(l3.state).toBe('locked')

    render(<LayerCard layer={l3} assets={snapshot.assets} onOpenAudit={vi.fn()} />)
    const toggle = screen.getByRole('button', { name: /^L3 · Kala/ })
    fireEvent.click(toggle)

    const panelId = toggle.getAttribute('aria-controls')
    const panel = panelId ? document.getElementById(panelId) : null
    if (!panel) throw new Error("L3's expanded panel is missing.")
    // L3's own wave is legitimately sequence-locked within the layer (a real, different,
    // per-WAVE concept this fix does not touch), and both its collapsed `<summary>` ("Wave 0 ·
    // locked · 1 asset") and WaveLane's own per-wave state `<p>` legitimately say "locked" too —
    // so this targets the *exact* element the old raw per-LAYER state rendered as
    // (`<p className="capitalize">{layer.state}</p>`, no other classes) rather than any
    // substring/word match that would false-positive on that unrelated, still-present text.
    expect(within(panel).queryByText((content, element) => (
      element?.tagName === 'P' && element.className === 'capitalize' && content.trim().toLowerCase() === 'locked'
    ))).not.toBeInTheDocument()
    expect(within(panel).queryByText(/required gate/i)).not.toBeInTheDocument()
  })

  it('opens by default when defaultOpen is set, and shows the always-visible WaveProgressBar without needing to expand', () => {
    const snapshot = snapshotFixture()
    const l0 = layer(snapshot, 'L0')

    render(<LayerCard layer={l0} assets={snapshot.assets} onOpenAudit={vi.fn()} defaultOpen />)

    expect(screen.getByRole('button', { name: /^L0 · Brahmagyan/ })).toHaveAttribute('aria-expanded', 'true')
    const subWaveProgress = screen.getByLabelText(/programme sub-wave progress/i)
    for (const wave of l0.wave_progress) {
      expect(within(subWaveProgress).getByText(wave.wave_id)).toBeVisible()
    }
    // LayerStage's own internal WaveProgressBar is suppressed to avoid rendering it twice —
    // exactly one "Programme sub-wave progress" list exists even once the card is expanded.
    expect(screen.getAllByLabelText(/programme sub-wave progress/i)).toHaveLength(1)
  })
})
