/**
 * asset_health.ts — pure helpers for computing health badges on manifest assets.
 *
 * Badge semantics (from §H.2 spec):
 *   green  — CURRENT / LIVE / ACTIVE / CURRENT_ENGINE_DIRECT, expose_to_chat:true
 *   yellow — LIVING / STUB / SCAFFOLD / UNFITTED_SCAFFOLD / DRAFT (expected drift)
 *   red    — SUPERSEDED / ARCHIVED / CLOSED / PREDECESSOR / GOVERNANCE_CLOSED
 *   gray   — expose_to_chat:false OR layer 'governance'
 */

import type { AssetEntry } from '@/lib/bundle/types'

export type HealthBadge = 'green' | 'yellow' | 'red' | 'gray'
export type ReachabilityLabel = 'reachable' | 'no_tool'

const GREEN_STATUSES = new Set(['CURRENT', 'LIVE', 'ACTIVE', 'CURRENT_ENGINE_DIRECT'])
const YELLOW_STATUSES = new Set(['LIVING', 'STUB', 'SCAFFOLD', 'UNFITTED_SCAFFOLD', 'DRAFT'])
const RED_STATUSES = new Set(['SUPERSEDED', 'ARCHIVED', 'CLOSED', 'PREDECESSOR', 'GOVERNANCE_CLOSED', 'DEAD_DATA'])

export function computeHealthBadge(entry: AssetEntry): HealthBadge {
  if (!entry.expose_to_chat || entry.layer === 'governance') return 'gray'
  if (GREEN_STATUSES.has(entry.status)) return 'green'
  if (YELLOW_STATUSES.has(entry.status)) return 'yellow'
  if (RED_STATUSES.has(entry.status)) return 'red'
  return 'gray'
}

export function computeReachability(entry: AssetEntry & { bound_tools?: string[] }): ReachabilityLabel {
  return (entry.bound_tools ?? []).length > 0 ? 'reachable' : 'no_tool'
}

export const LAYER_ORDER: string[] = ['L1', 'L1.5', 'L2.5', 'L3', 'L3.5', 'L6', 'L8', 'L9', 'governance', '?']

export function layerLabel(layer: string): string {
  const map: Record<string, string> = {
    L1: 'L1 — Facts',
    'L1.5': 'L1.5 — Computed Facts',
    'L2.5': 'L2.5 — Holistic Synthesis',
    L3: 'L3 — Domain Reports',
    'L3.5': 'L3.5 — Temporal / Discovery',
    L6: 'L6 — Governance',
    L8: 'L8 — Corpus',
    L9: 'L9 — Summaries',
    governance: 'Governance',
    '?': 'Unclassified',
  }
  return map[layer] ?? layer
}

export const BADGE_COLORS: Record<HealthBadge, string> = {
  green: 'var(--status-success)',
  yellow: 'var(--status-warn)',
  red: 'var(--status-error)',
  gray: 'var(--muted-foreground)',
}

// ── Shared API response types ────────────────────────────────────────────────

export interface AssetCatalogEntry extends AssetEntry {
  health: HealthBadge
  reachability: ReachabilityLabel
  bound_tools: string[]
}

export interface AssetCatalogResponse {
  fingerprint: string
  total: number
  entries: AssetCatalogEntry[]
}
