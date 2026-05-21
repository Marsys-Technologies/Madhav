/**
 * conflict_panel.test.tsx — PERF-S5 full ConflictPanel tests
 *
 * Gate: conflict_panel_smoke
 * Tests: smoke render, empty state, confirm action.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { ConflictPanel } from '@/components/performance/ConflictPanel';

// ── Shared mock data ──────────────────────────────────────────────────────────

const PROPOSED_PATCH = {
  filename: 'DIS.013_MSR.377_proposed.yaml',
  conflict_id: 'DIS.013',
  signal_ids_affected: ['MSR.377'],
  patch_description: 'Correct Muntha sign',
  authored_on: '2026-05-21',
  before: 'x',
  after: 'y',
  status: 'PROPOSED',
};

function makeFetchPatches(response: {
  proposed: typeof PROPOSED_PATCH[];
  resolved: typeof PROPOSED_PATCH[];
  rejected: typeof PROPOSED_PATCH[];
}) {
  return async (url: string) => {
    if (url === '/api/icr/patches') {
      return {
        ok: true,
        json: async () => response,
        statusText: 'OK',
      };
    }
    if (url === '/api/icr/confirm') {
      return { ok: true, json: async () => ({ ok: true }), statusText: 'OK' };
    }
    return { ok: false, json: async () => ({}), statusText: 'Not Found' };
  };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('ConflictPanel (PERF-S5)', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('conflict_panel_smoke — renders patch data and action buttons', async () => {
    vi.spyOn(global, 'fetch').mockImplementation(
      makeFetchPatches({
        proposed: [PROPOSED_PATCH],
        resolved: [],
        rejected: [],
      }) as typeof fetch,
    );

    render(<ConflictPanel />);

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('DIS.013')).toBeTruthy();
    });

    expect(screen.getByText('MSR.377')).toBeTruthy();
    expect(screen.getByText('Correct Muntha sign')).toBeTruthy();
    expect(screen.getByRole('button', { name: /confirm/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /reject/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /escalate/i })).toBeTruthy();
  });

  it('conflict_panel_empty_state — shows "No pending conflicts." when proposed is empty', async () => {
    vi.spyOn(global, 'fetch').mockImplementation(
      makeFetchPatches({
        proposed: [],
        resolved: [],
        rejected: [],
      }) as typeof fetch,
    );

    render(<ConflictPanel />);

    await waitFor(() => {
      expect(screen.getByText('No pending conflicts.')).toBeTruthy();
    });
    expect(screen.getByText('No history.')).toBeTruthy();
  });

  it('conflict_panel_confirm_action — POST is called and list is refreshed on Confirm', async () => {
    const fetchSpy = vi.spyOn(global, 'fetch').mockImplementation(
      makeFetchPatches({
        proposed: [PROPOSED_PATCH],
        resolved: [],
        rejected: [],
      }) as typeof fetch,
    );

    render(<ConflictPanel />);

    // Wait for the patch row to appear
    await waitFor(() => {
      expect(screen.getByText('DIS.013')).toBeTruthy();
    });

    // Count GET calls so far (should be 1)
    const getCallsBefore = fetchSpy.mock.calls.filter(
      (c) => c[0] === '/api/icr/patches',
    ).length;

    // Click the Confirm button
    fireEvent.click(screen.getByRole('button', { name: /confirm/i }));

    // Wait for the POST + refresh GET
    await waitFor(() => {
      const postCalls = fetchSpy.mock.calls.filter(
        (c) => c[0] === '/api/icr/confirm',
      );
      expect(postCalls.length).toBe(1);
    });

    // Verify POST payload
    const postCall = fetchSpy.mock.calls.find((c) => c[0] === '/api/icr/confirm');
    expect(postCall).toBeTruthy();
    const postBody = JSON.parse((postCall![1] as RequestInit).body as string);
    expect(postBody).toMatchObject({
      patch_file: 'DIS.013_MSR.377_proposed.yaml',
      action: 'confirm',
    });

    // Verify a second GET /api/icr/patches was issued (refresh after action)
    await waitFor(() => {
      const getCallsAfter = fetchSpy.mock.calls.filter(
        (c) => c[0] === '/api/icr/patches',
      ).length;
      expect(getCallsAfter).toBeGreaterThan(getCallsBefore);
    });
  });
});
