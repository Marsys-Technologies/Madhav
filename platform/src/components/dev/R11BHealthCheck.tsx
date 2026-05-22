/**
 * R11BHealthCheck.tsx — B-S0 (R11.B Adapter Health Check)
 *
 * Dev-only component (excluded from production bundles) that verifies the
 * R11.A adapter substrate is healthy from R11.B's perspective.
 *
 * Renders the active provider's manifest summary (capability count, manifest
 * hash) using the dispatcher and the useMultiProviderParity() hook.
 *
 * Mounted conditionally when NODE_ENV !== 'production'.
 */

'use client';

import { useMemo } from 'react';
import { getAllManifests, VALID_STACK_IDS } from '@/lib/providers/dispatcher';
import { useMultiProviderParity, useChatShellMode } from '@/lib/chat-v2/useMultiProviderParity';
import type { StackId } from '@/lib/providers/dispatcher';
import type { ProviderCapabilities } from '@/lib/providers/capabilities';

// ---------------------------------------------------------------------------
// Manifest summary helpers
// ---------------------------------------------------------------------------

/**
 * Counts non-null capability values in a manifest.
 * 'false' booleans are treated as "declared but disabled", so they count.
 * null values mean "not supported" and do NOT count.
 */
function countCapabilities(manifest: ProviderCapabilities): number {
  return Object.values(manifest).filter(v => v !== null).length;
}

/**
 * Produces a stable short hash of a manifest for change detection.
 * Uses a simple djb2-style hash over the JSON serialization.
 * Not cryptographic — purely for dev-panel fingerprinting.
 */
function hashManifest(manifest: ProviderCapabilities): string {
  const str = JSON.stringify(manifest, Object.keys(manifest).sort());
  let h = 5381;
  for (let i = 0; i < str.length; i++) {
    h = ((h << 5) + h) ^ str.charCodeAt(i);
    h = h >>> 0; // Convert to unsigned 32-bit int
  }
  return h.toString(16).padStart(8, '0');
}

interface ManifestSummary {
  stackId: StackId;
  capabilityCount: number;
  manifestHash: string;
}

// ---------------------------------------------------------------------------
// R11BHealthCheck component
// ---------------------------------------------------------------------------

/**
 * Dev-only health-check panel for R11.B.
 *
 * Shows:
 *   - Per-stack manifest summaries (capability count + hash)
 *   - Active multi-provider parity state
 *   - Env-var kill-switch status
 *
 * MUST NOT render in production (checked at render time).
 */
export function R11BHealthCheck(): React.ReactElement | null {
  // Hard guard: never render in production
  if (process.env.NODE_ENV === 'production') {
    return null;
  }

  return <R11BHealthCheckInner />;
}

function R11BHealthCheckInner(): React.ReactElement {
  const isParityActive = useMultiProviderParity();
  const { mode, envEnabled } = useChatShellMode();

  const summaries = useMemo<ManifestSummary[]>(() => {
    const manifests = getAllManifests();
    return VALID_STACK_IDS.map(stackId => ({
      stackId,
      capabilityCount: countCapabilities(manifests[stackId]),
      manifestHash: hashManifest(manifests[stackId]),
    }));
  }, []);

  return (
    <div
      data-testid="r11b-health-check"
      style={{
        position: 'fixed',
        bottom: '1rem',
        right: '1rem',
        zIndex: 9999,
        background: 'rgba(10, 10, 20, 0.92)',
        border: '1px solid rgba(212, 175, 55, 0.4)',
        borderRadius: '8px',
        padding: '0.75rem 1rem',
        fontFamily: 'monospace',
        fontSize: '11px',
        color: '#e8e8e8',
        minWidth: '260px',
        maxWidth: '320px',
        backdropFilter: 'blur(8px)',
      }}
    >
      <div style={{ color: '#d4af37', fontWeight: 700, marginBottom: '0.5rem', fontSize: '12px' }}>
        R11.B Health Check (dev)
      </div>

      {/* Parity state */}
      <div style={{ marginBottom: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem' }}>
        <div>
          <span style={{ color: '#999' }}>envEnabled: </span>
          <span
            data-testid="r11b-env-enabled"
            style={{ color: envEnabled ? '#4ade80' : '#f87171' }}
          >
            {String(envEnabled)}
          </span>
        </div>
        <div>
          <span style={{ color: '#999' }}>shellMode: </span>
          <span data-testid="r11b-shell-mode" style={{ color: '#d4af37' }}>{mode}</span>
        </div>
        <div>
          <span style={{ color: '#999' }}>parityActive: </span>
          <span
            data-testid="r11b-parity-active"
            style={{ color: isParityActive ? '#4ade80' : '#f87171' }}
          >
            {String(isParityActive)}
          </span>
        </div>
      </div>

      {/* Per-stack manifest summaries */}
      <div style={{ color: '#999', fontSize: '10px', marginBottom: '0.25rem' }}>
        stacks ({summaries.length} registered):
      </div>
      {summaries.map(({ stackId, capabilityCount, manifestHash }) => (
        <div
          key={stackId}
          data-testid={`r11b-manifest-${stackId}`}
          style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem', fontSize: '10px', marginBottom: '0.15rem' }}
        >
          <span style={{ color: '#a78bfa', minWidth: '70px' }}>{stackId}</span>
          <span style={{ color: '#e8e8e8' }}>{capabilityCount} caps</span>
          <span style={{ color: '#6b7280', fontFamily: 'monospace' }}>#{manifestHash}</span>
        </div>
      ))}
    </div>
  );
}

export default R11BHealthCheck;
