import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LiveDependencyGraph, type GraphNode, type GraphEdge } from '../LiveDependencyGraph'

// Stub EventSource (not in jsdom)
const mockEventSource = {
  onopen: null as (() => void) | null,
  onerror: null as ((e: Event) => void) | null,
  onmessage: null as ((e: MessageEvent) => void) | null,
  close: vi.fn(),
}
vi.stubGlobal('EventSource', vi.fn(() => mockEventSource))

// Stub next/navigation (already mocked in test-setup.ts globally)

const RUNNING_NODES: GraphNode[] = [
  { asset_id: 'ga_positions', layer: 'L1', status: 'running', progress: 0.4 },
]
const COMPLETE_NODES: GraphNode[] = [
  { asset_id: 'ga_positions', layer: 'L1', status: 'complete' },
  { asset_id: 'ga_dashas',    layer: 'L1', status: 'complete' },
]
const PENDING_NODES: GraphNode[] = [
  { asset_id: 'ph_nimitta', layer: 'L4', status: 'pending' },
]
const FAILED_NODES: GraphNode[] = [
  { asset_id: 'bo_graph', layer: 'L2', status: 'failed' },
]
const SKIPPED_NODES: GraphNode[] = [
  { asset_id: 'bo_holistic', layer: 'L2', status: 'skipped' },
]
const LIVE_EDGES: GraphEdge[] = [
  { from: 'ga_positions', to: 'bo_signals', live: true },
]
const NORMAL_EDGES: GraphEdge[] = [
  { from: 'ga_dashas', to: 'ka_timeline', live: false },
]

describe('LiveDependencyGraph', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the SVG graph container', () => {
    render(<LiveDependencyGraph />)
    expect(screen.getByTestId('dependency-graph-svg')).toBeTruthy()
  })

  it('renders all 4 column layer headers (Sanskrit names)', () => {
    const { container } = render(<LiveDependencyGraph />)
    const texts = container.querySelectorAll('text')
    const textContent = Array.from(texts).map((t) => t.textContent ?? '')
    expect(textContent.some((t) => t.includes('Adhara'))).toBe(true)
    expect(textContent.some((t) => t.includes('Sambandha'))).toBe(true)
    expect(textContent.some((t) => t.includes('Sutra'))).toBe(true)
    expect(textContent.some((t) => t.includes('Vyavahara'))).toBe(true)
  })

  it('renders layer micro-labels L1, L2.5, L3, L4', () => {
    const { container } = render(<LiveDependencyGraph />)
    const texts = Array.from(container.querySelectorAll('text')).map((t) => t.textContent ?? '')
    expect(texts.some((t) => t === 'L1')).toBe(true)
    expect(texts.some((t) => t === 'L2.5')).toBe(true)
    expect(texts.some((t) => t === 'L3')).toBe(true)
    expect(texts.some((t) => t === 'L4')).toBe(true)
  })

  it('renders Yantra Chitra heading', () => {
    render(<LiveDependencyGraph />)
    expect(screen.getByText(/Yantra Chitra/)).toBeTruthy()
  })

  it('renders node with correct data-status for complete', () => {
    render(<LiveDependencyGraph initialNodes={COMPLETE_NODES} />)
    const node = screen.getByTestId('node-pratyaksha')
    expect(node.getAttribute('data-status')).toBe('complete')
  })

  it('renders node with correct data-status for running', () => {
    render(<LiveDependencyGraph initialNodes={RUNNING_NODES} />)
    const node = screen.getByTestId('node-pratyaksha')
    expect(node.getAttribute('data-status')).toBe('running')
  })

  it('renders node with correct data-status for pending', () => {
    render(<LiveDependencyGraph initialNodes={PENDING_NODES} />)
    const node = screen.getByTestId('node-prashna')
    expect(node.getAttribute('data-status')).toBe('pending')
  })

  it('renders node with correct data-status for failed', () => {
    render(<LiveDependencyGraph initialNodes={FAILED_NODES} />)
    const node = screen.getByTestId('node-karana_jala')
    expect(node.getAttribute('data-status')).toBe('failed')
  })

  it('renders node with correct data-status for skipped', () => {
    render(<LiveDependencyGraph initialNodes={SKIPPED_NODES} />)
    const node = screen.getByTestId('node-sangam')
    expect(node.getAttribute('data-status')).toBe('skipped')
  })

  it('renders live edge with data-testid edge-live', () => {
    render(
      <LiveDependencyGraph
        initialNodes={COMPLETE_NODES}
        initialEdges={LIVE_EDGES}
      />
    )
    const liveEdge = screen.getByTestId('edge-live')
    expect(liveEdge).toBeTruthy()
    expect(liveEdge.getAttribute('data-from')).toBe('pratyaksha')
    expect(liveEdge.getAttribute('data-to')).toBe('lakshana_kosha')
  })

  it('renders normal edge with data-testid edge-normal', () => {
    render(
      <LiveDependencyGraph
        initialNodes={COMPLETE_NODES}
        initialEdges={NORMAL_EDGES}
      />
    )
    expect(screen.getByTestId('edge-normal')).toBeTruthy()
  })

  it('shows legend with Complete / Running / Pending labels', () => {
    render(<LiveDependencyGraph />)
    expect(screen.getByText(/Complete 0/)).toBeTruthy()
    expect(screen.getByText(/Running 0/)).toBeTruthy()
    expect(screen.getByText(/Pending 0/)).toBeTruthy()
  })

  it('legend counts update with initial nodes', () => {
    render(
      <LiveDependencyGraph
        initialNodes={[
          { asset_id: 'pratyaksha', layer: 'L1', status: 'complete' },
          { asset_id: 'panchanga',  layer: 'L1', status: 'running' },
          { asset_id: 'varga',      layer: 'L1', status: 'pending' },
        ]}
      />
    )
    expect(screen.getByText(/Complete 1/)).toBeTruthy()
    expect(screen.getByText(/Running 1/)).toBeTruthy()
    expect(screen.getByText(/Pending 1/)).toBeTruthy()
  })

  it('renders empty state without crashing (no nodes, no edges)', () => {
    expect(() => render(<LiveDependencyGraph />)).not.toThrow()
  })

  it('renders the progress ring for running nodes', () => {
    render(<LiveDependencyGraph initialNodes={RUNNING_NODES} />)
    expect(screen.getAllByTestId('progress-ring').length).toBeGreaterThan(0)
  })

  it('does not render progress ring for non-running nodes', () => {
    render(<LiveDependencyGraph initialNodes={COMPLETE_NODES} />)
    expect(screen.queryAllByTestId('progress-ring').length).toBe(0)
  })

  it('renders at least one pratyaksha label (Sanskrit name from ASSET_NAMES)', () => {
    render(<LiveDependencyGraph />)
    // At minimum, the static layout should show Pratyaksha in a text node
    const { container } = render(<LiveDependencyGraph />)
    const texts = Array.from(container.querySelectorAll('text')).map((t) => t.textContent ?? '')
    expect(texts.some((t) => t.includes('Pratyaksha'))).toBe(true)
  })

  it('dashed gutter dividers are present (3 lines for 4 columns)', () => {
    const { container } = render(<LiveDependencyGraph />)
    const dashedLines = Array.from(container.querySelectorAll('line[stroke-dasharray]'))
    expect(dashedLines.length).toBe(3)
  })
})
