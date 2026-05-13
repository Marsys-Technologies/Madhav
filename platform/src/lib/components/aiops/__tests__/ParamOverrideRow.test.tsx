import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

const DEFAULT_PARAM_VALUES = {
  max_output_tokens: { current: null,  default: 4096 },
  temperature:       { current: null,  default: 1.0 },
  thinkingBudget:    { current: null,  default: 0 },
  timeout_ms:        { current: null,  default: 30000 },
}

describe('ParamOverrideRow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
  })

  it('renders collapsed by default (no param rows visible)', async () => {
    const { ParamOverrideRow } = await import('../ParamOverrideRow')
    render(
      <ParamOverrideRow
        stack="gemini"
        callType="synthesis"
        paramValues={DEFAULT_PARAM_VALUES}
        onUpdate={vi.fn()}
      />,
    )
    expect(screen.queryByText('temperature')).toBeFalsy()
    expect(screen.getByText(/Advanced params/i)).toBeTruthy()
  })

  it('expands to show all 4 param rows when clicked', async () => {
    const { ParamOverrideRow } = await import('../ParamOverrideRow')
    render(
      <ParamOverrideRow
        stack="gemini"
        callType="synthesis"
        paramValues={DEFAULT_PARAM_VALUES}
        onUpdate={vi.fn()}
      />,
    )
    fireEvent.click(screen.getByText(/Advanced params/i))
    expect(screen.getByText('temperature')).toBeTruthy()
    expect(screen.getByText('max_output_tokens')).toBeTruthy()
    expect(screen.getByText('thinkingBudget')).toBeTruthy()
    expect(screen.getByText('timeout_ms')).toBeTruthy()
  })

  it('shows all 4 inputs when expanded', async () => {
    const { ParamOverrideRow } = await import('../ParamOverrideRow')
    render(
      <ParamOverrideRow
        stack="gemini"
        callType="synthesis"
        paramValues={DEFAULT_PARAM_VALUES}
        onUpdate={vi.fn()}
      />,
    )
    fireEvent.click(screen.getByText(/Advanced params/i))
    const inputs = screen.getAllByRole('textbox')
    expect(inputs).toHaveLength(4)
  })

  it('shows reset link when param has current override', async () => {
    const { ParamOverrideRow } = await import('../ParamOverrideRow')
    render(
      <ParamOverrideRow
        stack="gemini"
        callType="synthesis"
        paramValues={{
          ...DEFAULT_PARAM_VALUES,
          temperature: { current: 0.2, default: 1.0 },
        }}
        onUpdate={vi.fn()}
      />,
    )
    fireEvent.click(screen.getByText(/Advanced params/i))
    expect(screen.getByText('reset')).toBeTruthy()
  })

  it('does not show reset link when param uses default (no override)', async () => {
    const { ParamOverrideRow } = await import('../ParamOverrideRow')
    render(
      <ParamOverrideRow
        stack="gemini"
        callType="synthesis"
        paramValues={DEFAULT_PARAM_VALUES}
        onUpdate={vi.fn()}
      />,
    )
    fireEvent.click(screen.getByText(/Advanced params/i))
    expect(screen.queryByText('reset')).toBeFalsy()
  })

  it('shows current override value in label when set', async () => {
    const { ParamOverrideRow } = await import('../ParamOverrideRow')
    render(
      <ParamOverrideRow
        stack="gemini"
        callType="synthesis"
        paramValues={{
          ...DEFAULT_PARAM_VALUES,
          temperature: { current: 0.2, default: 1.0 },
        }}
        onUpdate={vi.fn()}
      />,
    )
    fireEvent.click(screen.getByText(/Advanced params/i))
    // Current value should be visible
    expect(screen.getByText('0.2')).toBeTruthy()
  })
})
