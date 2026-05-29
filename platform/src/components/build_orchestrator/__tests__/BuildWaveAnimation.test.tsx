/**
 * BuildWaveAnimation.test.tsx
 * H-04: Unit tests for the Framer Motion natal-wheel progress sweep.
 * Minimum 10 test cases per acceptance criteria.
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import BuildWaveAnimation, {
  type AyanamshaWaveState,
  type WavePhase,
} from '../BuildWaveAnimation'

// ── Mock framer-motion so tests run without a DOM animation engine ─────────────
jest.mock('framer-motion', () => {
  const actual = jest.requireActual('framer-motion')
  // Provide pass-through components that render their children with the
  // relevant props forwarded to the underlying SVG element.
  const motionProxy = new Proxy(
    {},
    {
      get: (_t, tag: string) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const El = (props: any) => {
          const { initial: _i, animate: _a, exit: _e, transition: _t2, ...rest } = props
          // React.createElement needs a real string or component
          const svgTags = new Set(['circle', 'path', 'g', 'svg', 'line', 'rect'])
          const element = svgTags.has(tag) ? tag : 'div'
          return React.createElement(element, rest)
        }
        El.displayName = `motion.${tag}`
        return El
      },
    },
  )
  return {
    ...actual,
    motion: motionProxy,
    AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    useAnimationFrame: (cb: (t: number) => void) => {
      // Call once synchronously with t=0 so pulse state initialises
      React.useEffect(() => { cb(0) }, [])
    },
  }
})

// ── Fixtures ─────────────────────────────────────────────────────────────────

function makeState(
  id: string,
  phase: WavePhase,
  progress_pct: number,
  color?: string,
): AyanamshaWaveState {
  return {
    ayanamsha_id: id,
    display_name: id,
    progress_pct,
    phase,
    color,
  }
}

const FIVE_ACTIVE: AyanamshaWaveState[] = [
  makeState('lahiri',          'wave_2', 75),
  makeState('true_chitra',     'wave_1', 40),
  makeState('kp',              'wave_1', 30),
  makeState('raman',           'initializing', 5),
  makeState('surya_siddhanta', 'wave_3', 90),
]

const ALL_COMPLETE: AyanamshaWaveState[] = [
  makeState('lahiri',          'complete', 100),
  makeState('true_chitra',     'complete', 100),
  makeState('kp',              'complete', 100),
  makeState('raman',           'complete', 100),
  makeState('surya_siddhanta', 'complete', 100),
]

const MIXED_WITH_IDLE: AyanamshaWaveState[] = [
  makeState('lahiri',      'wave_1', 50),
  makeState('true_chitra', 'idle',   0),
  makeState('kp',          'wave_2', 60),
]

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('BuildWaveAnimation', () => {
  // Test 1 — empty array → idle sentinel div rendered, no SVG
  it('renders idle sentinel div when ayanamshaStates is empty', () => {
    render(<BuildWaveAnimation ayanamshaStates={[]} />)
    expect(screen.getByTestId('build-wave-idle')).toBeInTheDocument()
    expect(screen.queryByTestId('build-wave-animation')).toBeNull()
  })

  // Test 2 — all-idle states → same idle sentinel
  it('renders idle sentinel when all phases are idle', () => {
    const allIdle: AyanamshaWaveState[] = [
      makeState('lahiri', 'idle', 0),
      makeState('kp',     'idle', 0),
    ]
    render(<BuildWaveAnimation ayanamshaStates={allIdle} />)
    expect(screen.getByTestId('build-wave-idle')).toBeInTheDocument()
    expect(screen.queryByTestId('build-wave-animation')).toBeNull()
  })

  // Test 3 — any active phase → main SVG rendered
  it('renders SVG container when at least one state is active', () => {
    render(<BuildWaveAnimation ayanamshaStates={[makeState('lahiri', 'wave_1', 50)]} />)
    expect(screen.getByTestId('build-wave-animation')).toBeInTheDocument()
  })

  // Test 4 — 5 ayanamsha arcs rendered
  it('renders a wave group for each non-idle ayanamsha', () => {
    render(<BuildWaveAnimation ayanamshaStates={FIVE_ACTIVE} />)
    expect(screen.getByTestId('wave-lahiri')).toBeInTheDocument()
    expect(screen.getByTestId('wave-true_chitra')).toBeInTheDocument()
    expect(screen.getByTestId('wave-kp')).toBeInTheDocument()
    expect(screen.getByTestId('wave-raman')).toBeInTheDocument()
    expect(screen.getByTestId('wave-surya_siddhanta')).toBeInTheDocument()
  })

  // Test 5 — all-complete → celebration ring visible
  it('renders complete-ring when all states are complete', () => {
    render(<BuildWaveAnimation ayanamshaStates={ALL_COMPLETE} />)
    expect(screen.getByTestId('complete-ring')).toBeInTheDocument()
  })

  // Test 6 — not-all-complete → complete-ring absent
  it('does not render complete-ring when not all states are complete', () => {
    render(<BuildWaveAnimation ayanamshaStates={FIVE_ACTIVE} />)
    expect(screen.queryByTestId('complete-ring')).toBeNull()
  })

  // Test 7 — active phases → activity-ring shown
  it('renders activity-ring while any build is actively progressing', () => {
    render(<BuildWaveAnimation ayanamshaStates={FIVE_ACTIVE} />)
    expect(screen.getByTestId('activity-ring')).toBeInTheDocument()
  })

  // Test 8 — all-complete → activity-ring absent
  it('does not render activity-ring when all builds are complete', () => {
    render(<BuildWaveAnimation ayanamshaStates={ALL_COMPLETE} />)
    expect(screen.queryByTestId('activity-ring')).toBeNull()
  })

  // Test 9 — idle entries within a mixed list are skipped
  it('skips idle entries in a mixed states list', () => {
    render(<BuildWaveAnimation ayanamshaStates={MIXED_WITH_IDLE} />)
    expect(screen.getByTestId('wave-lahiri')).toBeInTheDocument()
    expect(screen.queryByTestId('wave-true_chitra')).toBeNull()  // idle — skipped
    expect(screen.getByTestId('wave-kp')).toBeInTheDocument()
  })

  // Test 10 — custom color override is passed as stroke to the arc path
  it('accepts custom color overrides per ayanamsha', () => {
    const customColor = '#FF00FF'
    const states: AyanamshaWaveState[] = [
      makeState('lahiri', 'wave_1', 50, customColor),
    ]
    const { container } = render(<BuildWaveAnimation ayanamshaStates={states} />)
    // The motion.path inside the wave group should receive the custom stroke color
    const paths = container.querySelectorAll('path')
    const hasCustomColor = Array.from(paths).some(
      (p) => p.getAttribute('stroke') === customColor,
    )
    expect(hasCustomColor).toBe(true)
  })

  // Test 11 — progress_pct=0 → no leading tip dot rendered
  it('does not render a leading tip dot when progress is 0', () => {
    const states: AyanamshaWaveState[] = [
      makeState('lahiri', 'wave_1', 0),
    ]
    render(<BuildWaveAnimation ayanamshaStates={states} />)
    expect(screen.queryByTestId('tip-lahiri')).toBeNull()
  })

  // Test 12 — progress_pct > 0 on active phase → tip dot rendered
  it('renders leading tip dot for active phase with progress > 0', () => {
    const states: AyanamshaWaveState[] = [
      makeState('lahiri', 'wave_2', 45),
    ]
    render(<BuildWaveAnimation ayanamshaStates={states} />)
    expect(screen.getByTestId('tip-lahiri')).toBeInTheDocument()
  })

  // Test 13 — failed phase → failed-marker rendered (not a tip dot)
  it('renders failed-marker for failed phase', () => {
    const states: AyanamshaWaveState[] = [
      makeState('kp', 'failed', 55),
    ]
    render(<BuildWaveAnimation ayanamshaStates={states} />)
    expect(screen.getByTestId('failed-marker-kp')).toBeInTheDocument()
    expect(screen.queryByTestId('tip-kp')).toBeNull()
  })

  // Test 14 — complete phase → no tip dot (wave stopped)
  it('does not render leading tip dot for complete phase', () => {
    const states: AyanamshaWaveState[] = [
      makeState('raman', 'complete', 100),
    ]
    render(<BuildWaveAnimation ayanamshaStates={states} />)
    expect(screen.queryByTestId('tip-raman')).toBeNull()
  })

  // Test 15 — accepts custom size prop, viewBox reflects it
  it('renders with the specified size as viewBox dimensions', () => {
    const { container } = render(
      <BuildWaveAnimation ayanamshaStates={FIVE_ACTIVE} size={600} />,
    )
    const svg = container.querySelector('svg')
    expect(svg?.getAttribute('viewBox')).toBe('0 0 600 600')
  })
})
