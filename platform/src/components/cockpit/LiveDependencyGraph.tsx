'use client'

/**
 * LiveDependencyGraph — SVG force-graph of the 28-asset dependency DAG.
 *
 * Renders per VISUAL_CONTRACT v2 §"Page 2 §3 Yantra Chitra force-graph":
 *   - 4 columns: Adhara (L1) / Sambandha (L2_5) / Sutra (L3) / Vyavahara (L4)
 *   - Bezier edges with marker-end arrows
 *   - Lit edges (live data transfer) in --gold-primary with pulse animation
 *   - Node states: complete / running / pending / failed / skipped
 *   - Sanskrit name labels from ASSET_NAMES
 *   - Column headers + dashed gutter dividers
 *
 * SSE dependency (Stream B R1): subscribes to /api/build/events/<buildId>
 * expecting node_added + edge_added events. Before Stream B's R1 lands on
 * main the graph degrades gracefully — no events → static display, no errors.
 *
 * [C-S3]
 */

import { useMemo } from 'react'
import { ASSET_NAMES, LAYER_NAMES, assetsByLayer, type AssetKey, type LayerKey } from '@/lib/jyotish/asset_names'
import { useSseSubscription } from '@/hooks/useSseSubscription'
import { ProgressRing } from './ProgressRing'

// ── Types ─────────────────────────────────────────────────────────────────────

export type NodeStatus = 'complete' | 'running' | 'pending' | 'failed' | 'skipped'

export interface GraphNode {
  asset_id: string
  layer: LayerKey
  status: NodeStatus
  row_count?: number
  progress?: number // 0-1
}

export interface GraphEdge {
  from: string
  to: string
  live?: boolean
}

interface Props {
  buildId?: string | null
  /** Static nodes for display when not driven by SSE (e.g. initial load). */
  initialNodes?: GraphNode[]
  /** Static edges for display when not driven by SSE. */
  initialEdges?: GraphEdge[]
  width?: number
  height?: number
}

// ── Layout constants ──────────────────────────────────────────────────────────

const COLUMN_ORDER: LayerKey[] = ['L1', 'L2_5', 'L3', 'L4']
const NODE_R = 10           // circle radius
const TERMINAL_W = 22       // rect width for L4 (Vyavahara) nodes
const TERMINAL_H = 14
const LABEL_OFFSET_X = 15  // label x from node center
const HEADER_H = 40         // column header row height
const ROW_PADDING = 36      // vertical padding between nodes

// Gold + status colours — ref theme tokens semantically, fallback to token values
const COLORS = {
  goldPrimary:   '#d4a648',
  goldLight:     '#e8c878',
  obsidianBg:    '#0a0908',
  obsidianBorder:'#1f1c17',
  success:       '#9bd49a',
  danger:        '#e89a9a',
  textSecondary: '#888373',
  textTertiary:  '#5d5b54',
  edgeNormal:    '#3a3328',
}

// ── Node geometry ─────────────────────────────────────────────────────────────

interface PositionedNode {
  key: AssetKey
  cx: number
  cy: number
  layer: LayerKey
  colIndex: number
}

function buildLayout(
  width: number,
  height: number,
): PositionedNode[] {
  const usableH = height - HEADER_H
  const colW = width / COLUMN_ORDER.length

  return COLUMN_ORDER.flatMap((layer, colIndex) => {
    const keys = assetsByLayer(layer)
    const colCx = colW * colIndex + colW / 2
    const spacing = Math.min(ROW_PADDING, usableH / (keys.length + 1))
    return keys.map((key, rowIndex) => ({
      key,
      cx: colCx,
      cy: HEADER_H + spacing * (rowIndex + 1),
      layer,
      colIndex,
    }))
  })
}

// ── Status helpers ─────────────────────────────────────────────────────────────

function nodeStroke(status: NodeStatus): string {
  switch (status) {
    case 'complete': return COLORS.goldPrimary
    case 'running':  return COLORS.goldLight
    case 'failed':   return COLORS.danger
    case 'skipped':  return COLORS.textTertiary
    default:         return COLORS.obsidianBorder
  }
}

function nodeFill(status: NodeStatus): string {
  switch (status) {
    case 'complete': return COLORS.goldPrimary
    default:         return 'none'
  }
}

// ── Bezier path ────────────────────────────────────────────────────────────────

function bezierPath(
  x1: number, y1: number,
  x2: number, y2: number,
): string {
  const cpX1 = x1 + (x2 - x1) * 0.5
  const cpX2 = x2 - (x2 - x1) * 0.5
  return `M ${x1} ${y1} C ${cpX1} ${y1}, ${cpX2} ${y2}, ${x2} ${y2}`
}

// ── Legend counts ──────────────────────────────────────────────────────────────

interface LegendCounts { complete: number; running: number; pending: number }

function computeLegend(nodes: GraphNode[]): LegendCounts {
  return nodes.reduce(
    (acc, n) => {
      if (n.status === 'complete') acc.complete++
      else if (n.status === 'running') acc.running++
      else acc.pending++
      return acc
    },
    { complete: 0, running: 0, pending: 0 } as LegendCounts,
  )
}

// ── Component ──────────────────────────────────────────────────────────────────

export function LiveDependencyGraph({
  buildId = null,
  initialNodes = [],
  initialEdges = [],
  width = 900,
  height = 520,
}: Props) {
  const { nodes: sseNodes, edges: sseEdges, connected } = useSseSubscription(buildId)

  // SSE nodes take priority; fall back to static props
  const nodes = sseNodes.length > 0 ? sseNodes : initialNodes
  const edges = sseEdges.length > 0 ? sseEdges : initialEdges

  const layout = useMemo(() => buildLayout(width, height), [width, height])

  // Build node position lookup
  const posMap = useMemo(() => {
    const m = new Map<string, { cx: number; cy: number }>()
    for (const n of layout) m.set(n.key, { cx: n.cx, cy: n.cy })
    return m
  }, [layout])

  // Merge live status into layout
  const statusMap = useMemo(() => {
    const m = new Map<string, GraphNode>()
    for (const n of nodes) m.set(n.asset_id, n)
    return m
  }, [nodes])

  const legend = computeLegend(nodes)
  const colW = width / COLUMN_ORDER.length

  // Marker defs
  const markerId = 'arrow-normal'
  const markerLitId = 'arrow-lit'

  return (
    <div
      className="relative"
      style={{
        background: COLORS.obsidianBg,
        borderRadius: 12,
        overflow: 'hidden',
        border: `1px solid ${COLORS.obsidianBorder}`,
      }}
    >
      {/* Panel header */}
      <div
        className="flex items-center justify-between px-4 py-3"
        style={{ borderBottom: `1px solid ${COLORS.obsidianBorder}` }}
      >
        <div>
          <span
            style={{
              fontFamily: 'var(--font-cormorant, "Cormorant Garamond", serif)',
              fontStyle: 'italic',
              fontSize: 18,
              color: COLORS.goldPrimary,
            }}
          >
            Yantra Chitra
          </span>
          <span
            style={{
              fontFamily: 'var(--font-sans, Inter, sans-serif)',
              fontSize: 11,
              color: COLORS.textSecondary,
              marginLeft: 12,
              letterSpacing: '0.04em',
            }}
          >
            Live dependency graph · 28 assets{' '}
            {connected && (
              <span style={{ color: COLORS.success }}>· synced to data plane</span>
            )}
          </span>
        </div>
        {/* Legend */}
        <div
          className="flex gap-3"
          style={{
            fontFamily: 'var(--font-jetbrains-mono, "JetBrains Mono", monospace)',
            fontSize: 10,
          }}
        >
          <span style={{ color: COLORS.success }}>Complete {legend.complete}</span>
          <span style={{ color: COLORS.goldLight }}>Running {legend.running}</span>
          <span style={{ color: COLORS.textTertiary }}>Pending {legend.pending}</span>
        </div>
      </div>

      {/* SVG graph */}
      <svg
        data-testid="dependency-graph-svg"
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        style={{ display: 'block' }}
        aria-label="Yantra Chitra — live asset dependency graph"
      >
        <defs>
          {/* Normal edge arrow */}
          <marker
            id={markerId}
            viewBox="0 0 6 6"
            refX="5"
            refY="3"
            markerWidth="5"
            markerHeight="5"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 6 3 L 0 6 z" fill={COLORS.edgeNormal} />
          </marker>
          {/* Lit edge arrow */}
          <marker
            id={markerLitId}
            viewBox="0 0 6 6"
            refX="5"
            refY="3"
            markerWidth="5"
            markerHeight="5"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 6 3 L 0 6 z" fill={COLORS.goldPrimary} />
          </marker>
        </defs>

        {/* Column backgrounds + dashed gutters */}
        {COLUMN_ORDER.map((layer, colIndex) => {
          const x = colW * colIndex
          const layerMeta = LAYER_NAMES[layer]
          return (
            <g key={layer}>
              {/* Dashed gutter divider (skip first column's left edge) */}
              {colIndex > 0 && (
                <line
                  x1={x} y1={HEADER_H}
                  x2={x} y2={height}
                  stroke={COLORS.obsidianBorder}
                  strokeDasharray="4 6"
                  strokeWidth={1}
                />
              )}
              {/* Column header */}
              <text
                x={x + colW / 2}
                y={18}
                textAnchor="middle"
                style={{
                  fontFamily: 'var(--font-cormorant, "Cormorant Garamond", serif)',
                  fontStyle: 'italic',
                  fontSize: 14,
                  fill: COLORS.goldPrimary,
                }}
              >
                {layerMeta.sanskrit}
              </text>
              <text
                x={x + colW / 2}
                y={32}
                textAnchor="middle"
                style={{
                  fontFamily: 'var(--font-jetbrains-mono, "JetBrains Mono", monospace)',
                  fontSize: 9,
                  fill: COLORS.textTertiary,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                }}
              >
                {layer.replace('_', '.')}
              </text>
            </g>
          )
        })}

        {/* Edges */}
        {edges.map((edge, i) => {
          const fromPos = posMap.get(edge.from)
          const toPos = posMap.get(edge.to)
          if (!fromPos || !toPos) return null
          const isLit = edge.live === true
          return (
            <path
              key={`edge-${i}`}
              data-testid={isLit ? 'edge-live' : 'edge-normal'}
              data-from={edge.from}
              data-to={edge.to}
              d={bezierPath(fromPos.cx + NODE_R, fromPos.cy, toPos.cx - NODE_R, toPos.cy)}
              fill="none"
              stroke={isLit ? COLORS.goldPrimary : COLORS.edgeNormal}
              strokeWidth={isLit ? 1.5 : 1}
              markerEnd={`url(#${isLit ? markerLitId : markerId})`}
              className={isLit ? 'edge-live' : undefined}
            />
          )
        })}

        {/* Nodes */}
        {layout.map(({ key, cx, cy, layer }) => {
          const liveNode = statusMap.get(key)
          const status: NodeStatus = liveNode?.status ?? 'pending'
          const progress = liveNode?.progress ?? 0
          const entry = ASSET_NAMES[key]
          const isTerminal = layer === 'L4'

          return (
            <g
              key={key}
              data-testid={`node-${key}`}
              data-status={status}
              className={liveNode ? 'node-enter' : undefined}
            >
              {/* Node shape */}
              {isTerminal ? (
                <rect
                  x={cx - TERMINAL_W / 2}
                  y={cy - TERMINAL_H / 2}
                  width={TERMINAL_W}
                  height={TERMINAL_H}
                  rx={4}
                  fill={nodeFill(status)}
                  stroke={nodeStroke(status)}
                  strokeWidth={status === 'skipped' ? 0.5 : 1.5}
                  opacity={status === 'skipped' ? 0.4 : 1}
                />
              ) : (
                <circle
                  cx={cx}
                  cy={cy}
                  r={NODE_R}
                  fill={nodeFill(status)}
                  stroke={nodeStroke(status)}
                  strokeWidth={status === 'skipped' ? 0.5 : 1.5}
                  opacity={status === 'skipped' ? 0.4 : 1}
                />
              )}

              {/* Progress ring overlay for running nodes */}
              {status === 'running' && !isTerminal && (
                <foreignObject
                  x={cx - NODE_R}
                  y={cy - NODE_R}
                  width={NODE_R * 2}
                  height={NODE_R * 2}
                >
                  <ProgressRing progress={progress} radius={NODE_R - 2} strokeWidth={2} />
                </foreignObject>
              )}

              {/* Sanskrit label */}
              <text
                x={cx + (isTerminal ? TERMINAL_W / 2 + 4 : LABEL_OFFSET_X)}
                y={cy + 4}
                style={{
                  fontFamily: 'var(--font-cormorant, "Cormorant Garamond", serif)',
                  fontSize: 11,
                  fill: status === 'complete'
                    ? COLORS.goldPrimary
                    : status === 'skipped'
                    ? COLORS.textTertiary
                    : COLORS.textSecondary,
                  opacity: status === 'skipped' ? 0.5 : 1,
                  textDecoration: status === 'skipped' ? 'line-through' : undefined,
                }}
              >
                {entry.sanskrit}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}
