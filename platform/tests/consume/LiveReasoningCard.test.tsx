import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LiveReasoningCard } from '@/components/consume/LiveReasoningCard'

const steps = (count: number) =>
  Array.from({ length: count }, (_, i) => ({
    type: 'reasoning_step' as const,
    phase: 'synthesis' as const,
    text: `Reasoning step ${i + 1} about the Lagna`,
    timestamp: 1700000000000 + i * 100,
  }))

describe('LiveReasoningCard', () => {
  it("renders 'Thinking…' when streaming with no steps", () => {
    render(<LiveReasoningCard reasoningSteps={[]} isStreaming />)
    expect(screen.getByText(/Thinking…/i)).toBeTruthy()
  })

  it('renders the most recent step when streaming with steps', () => {
    render(<LiveReasoningCard reasoningSteps={steps(3)} isStreaming />)
    expect(screen.getByText('Reasoning step 3 about the Lagna')).toBeTruthy()
  })

  it('renders nothing when not streaming and no steps', () => {
    const { container } = render(<LiveReasoningCard reasoningSteps={[]} isStreaming={false} />)
    expect(container.firstChild).toBeNull()
  })

  it('expand button reveals full list', async () => {
    render(<LiveReasoningCard reasoningSteps={steps(3)} isStreaming={false} />)
    const button = screen.getByRole('button')
    expect(button.getAttribute('aria-expanded')).toBe('false')
    await userEvent.click(button)
    expect(button.getAttribute('aria-expanded')).toBe('true')
    expect(screen.getByText('Reasoning step 1 about the Lagna')).toBeTruthy()
    expect(screen.getByText('Reasoning step 2 about the Lagna')).toBeTruthy()
  })
})
