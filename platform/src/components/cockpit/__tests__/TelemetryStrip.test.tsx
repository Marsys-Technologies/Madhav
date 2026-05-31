import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TelemetryStrip } from '../TelemetryStrip'

const DEFAULTS = {
  qps: 12.3,
  activeWriters: 4,
  queueDepth: 7,
  sidecarHealthy: true,
  buildId: 'abc12345-def6-7890-ghij-klmnopqrstuv',
}

describe('TelemetryStrip', () => {
  it('renders with data-testid telemetry-strip', () => {
    render(<TelemetryStrip {...DEFAULTS} />)
    expect(screen.getByTestId('telemetry-strip')).toBeTruthy()
  })

  it('renders QPS metric label', () => {
    render(<TelemetryStrip {...DEFAULTS} />)
    expect(screen.getByTestId('metric-qps')).toBeTruthy()
  })

  it('renders QPS value', () => {
    render(<TelemetryStrip {...DEFAULTS} />)
    expect(screen.getByTestId('metric-qps-value').textContent).toBe('12.3')
  })

  it('renders WRITERS metric', () => {
    render(<TelemetryStrip {...DEFAULTS} />)
    expect(screen.getByTestId('metric-writers')).toBeTruthy()
    expect(screen.getByTestId('metric-writers-value').textContent).toBe('4')
  })

  it('renders QUEUE metric', () => {
    render(<TelemetryStrip {...DEFAULTS} />)
    expect(screen.getByTestId('metric-queue')).toBeTruthy()
    expect(screen.getByTestId('metric-queue-value').textContent).toBe('7')
  })

  it('renders SIDECAR healthy state as OK', () => {
    render(<TelemetryStrip {...DEFAULTS} sidecarHealthy={true} />)
    expect(screen.getByTestId('metric-sidecar-value').textContent).toBe('OK')
  })

  it('renders SIDECAR unhealthy state as DOWN', () => {
    render(<TelemetryStrip {...DEFAULTS} sidecarHealthy={false} />)
    expect(screen.getByTestId('metric-sidecar-value').textContent).toBe('DOWN')
  })

  it('renders BUILD ID metric', () => {
    render(<TelemetryStrip {...DEFAULTS} />)
    expect(screen.getByTestId('metric-build id')).toBeTruthy()
  })

  it('truncates buildId to first 8 characters', () => {
    render(<TelemetryStrip {...DEFAULTS} buildId="abc12345-longersuffix" />)
    const value = screen.getByTestId('metric-build id-value').textContent
    expect(value).toBe('abc12345')
  })

  it('shows dash when buildId is empty', () => {
    render(<TelemetryStrip {...DEFAULTS} buildId="" />)
    expect(screen.getByTestId('metric-build id-value').textContent).toBe('—')
  })

  it('renders healthy sidecar with success color style', () => {
    render(<TelemetryStrip {...DEFAULTS} sidecarHealthy={true} />)
    const val = screen.getByTestId('metric-sidecar-value')
    expect(val.getAttribute('style')).toContain('success')
  })

  it('renders unhealthy sidecar with danger color style', () => {
    render(<TelemetryStrip {...DEFAULTS} sidecarHealthy={false} />)
    const val = screen.getByTestId('metric-sidecar-value')
    expect(val.getAttribute('style')).toContain('danger')
  })

  it('formats QPS to 1 decimal place', () => {
    render(<TelemetryStrip {...DEFAULTS} qps={5} />)
    expect(screen.getByTestId('metric-qps-value').textContent).toBe('5.0')
  })

  it('renders all 5 metrics', () => {
    render(<TelemetryStrip {...DEFAULTS} />)
    expect(screen.getByTestId('metric-qps')).toBeTruthy()
    expect(screen.getByTestId('metric-writers')).toBeTruthy()
    expect(screen.getByTestId('metric-queue')).toBeTruthy()
    expect(screen.getByTestId('metric-sidecar')).toBeTruthy()
    expect(screen.getByTestId('metric-build id')).toBeTruthy()
  })
})
