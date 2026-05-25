/**
 * AssistantMessage.test.tsx — B-S3 gate test
 *
 * Verifies:
 *  1. AssistantMessage renders with v2-assistant-message-wrapper class
 *  2. Component renders message content
 *  3. The wrapper class enables r11b-active CSS targeting for bubble-less layout
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AssistantMessage } from './AssistantMessage';
import type { UIMessage } from 'ai';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, className, ...rest }: React.ComponentPropsWithoutRef<'div'>) => (
      <div className={className} {...rest}>{children}</div>
    ),
  },
  useReducedMotion: () => true, // reduce animations in tests
}));

// Mock StreamingMarkdown to avoid heavy deps
vi.mock('./StreamingMarkdown', () => ({
  StreamingMarkdown: ({ text }: { text: string }) => <div data-testid="streaming-md">{text}</div>,
}));

// Mock other sub-components
vi.mock('./ToolCallCard', () => ({
  ToolCallCard: () => <div data-testid="tool-card" />,
}));
vi.mock('./StreamingDots', () => ({
  StreamingDots: () => <div data-testid="streaming-dots" />,
}));
vi.mock('./MessageActions', () => ({
  MessageActions: () => <div data-testid="message-actions" />,
}));
vi.mock('@/components/disclosure/DisclosureTierBadge', () => ({
  DisclosureTierBadge: () => null,
}));
vi.mock('./InlineToolFlow', () => ({
  InlineToolFlow: () => null,
}));

const makeAssistantMessage = (text: string): UIMessage => ({
  id: 'test-msg-1',
  role: 'assistant',
  parts: [{ type: 'text', text }],
});

describe('AssistantMessage (B-S3 message container shape)', () => {
  it('renders message content', () => {
    render(
      <AssistantMessage
        message={makeAssistantMessage('Hello from assistant')}
        isStreaming={false}
        isLast={true}
      />
    );
    expect(screen.getByTestId('streaming-md')).toBeTruthy();
  });

  it('has v2-assistant-message-wrapper class on root div', () => {
    const { container } = render(
      <AssistantMessage
        message={makeAssistantMessage('Test')}
        isStreaming={false}
        isLast={false}
      />
    );
    const wrapper = container.querySelector('.v2-assistant-message-wrapper');
    expect(wrapper).toBeTruthy();
  });

  it('has data-role="assistant-message" on root div', () => {
    const { container } = render(
      <AssistantMessage
        message={makeAssistantMessage('Test')}
        isStreaming={false}
        isLast={false}
      />
    );
    const wrapper = container.querySelector('[data-role="assistant-message"]');
    expect(wrapper).toBeTruthy();
  });

  it('v2-message-row class appears in ConsumeChatV2 for 48rem column targeting', async () => {
    // This test verifies that the class exists in the source — CSS-only solution
    // for r11b-active max-width: 48rem pinning
    const fs = await import('node:fs');
    const path = await import('node:path');
    const filePath = path.resolve(__dirname, '../consume/ConsumeChatV2.tsx');
    const source = fs.readFileSync(filePath, 'utf-8');
    expect(source).toContain('v2-message-row');
    expect(source).toContain('48rem');
  });
});
