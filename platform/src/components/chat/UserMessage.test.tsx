/**
 * UserMessage.test.tsx — B-S2 gate test
 *
 * Verifies:
 *  1. v2-user-bubble class is applied to the text div
 *  2. v2-user-bubble--r11b-shape class is applied
 *  3. Component renders with message text
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { UserMessage } from './UserMessage';
import type { UIMessage } from 'ai';

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, className, ...rest }: React.ComponentPropsWithoutRef<'div'>) => (
      <div className={className} {...rest}>{children}</div>
    ),
  },
  useReducedMotion: () => false,
}));

const makeMessage = (text: string): UIMessage => ({
  id: 'test-msg-1',
  role: 'user',
  content: text,
  parts: [{ type: 'text', text }],
});

describe('UserMessage (B-S2 user-bubble shape)', () => {
  it('renders message text', () => {
    render(<UserMessage message={makeMessage('Hello world')} />);
    expect(screen.getByText('Hello world')).toBeTruthy();
  });

  it('applies v2-user-bubble class to bubble div', () => {
    const { container } = render(<UserMessage message={makeMessage('Test')} />);
    const bubble = container.querySelector('.v2-user-bubble');
    expect(bubble).toBeTruthy();
  });

  it('applies v2-user-bubble--r11b-shape class to bubble div', () => {
    const { container } = render(<UserMessage message={makeMessage('Test')} />);
    const bubble = container.querySelector('.v2-user-bubble--r11b-shape');
    expect(bubble).toBeTruthy();
  });

  it('bubble div has both v2-user-bubble and v2-user-bubble--r11b-shape', () => {
    const { container } = render(<UserMessage message={makeMessage('Test')} />);
    // The same element should have both classes
    const bubbleWithBoth = container.querySelector(
      '.v2-user-bubble.v2-user-bubble--r11b-shape'
    );
    expect(bubbleWithBoth).toBeTruthy();
  });

  it('renders without error when no onEditSubmit', () => {
    const { container } = render(<UserMessage message={makeMessage('Hi')} />);
    expect(container.firstChild).toBeTruthy();
  });
});
