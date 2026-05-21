/**
 * conflict_panel.test.tsx — ICR-S5 UI smoke test
 *
 * Gate: confirmation_ui_smoke
 * Renders ConflictPanel with pending and empty states; asserts text content.
 */

import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { ConflictPanel } from '@/components/performance/ConflictPanel';

describe('ConflictPanel (confirmation_ui_smoke)', () => {
  it('renders "1 patch" text when proposedCount is 1', () => {
    const { getByText } = render(<ConflictPanel proposedCount={1} />);
    expect(getByText(/Conflict Resolution \(1 pending\)/i)).toBeTruthy();
    expect(getByText(/1 patch awaiting native review/i)).toBeTruthy();
  });

  it('renders "2 patches" (plural) when proposedCount is 2', () => {
    const { getByText } = render(<ConflictPanel proposedCount={2} />);
    expect(getByText(/Conflict Resolution \(2 pending\)/i)).toBeTruthy();
    expect(getByText(/2 patches awaiting native review/i)).toBeTruthy();
  });

  it('renders "No pending conflicts" when proposedCount is 0', () => {
    const { getByText } = render(<ConflictPanel proposedCount={0} />);
    expect(getByText(/Conflict Resolution \(0 pending\)/i)).toBeTruthy();
    expect(getByText(/No pending conflicts/i)).toBeTruthy();
  });
});
