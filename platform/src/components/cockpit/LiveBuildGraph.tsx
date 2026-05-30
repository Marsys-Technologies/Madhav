'use client'

/**
 * LiveBuildGraph — canvas force-graph with SSE subscription
 * Subscribes to /api/build/events/[buildId]
 * [PHASE-C-03]
 */

import { useEffect, useRef, useCallback, useState } from 'react'
import dynamic from 'next/dynamic'
import { NodeDetailModal } from './NodeDetailModal'

// Dynamic import — react-force-graph-2d requires window (canvas-only)
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false })

// ─── Types ────────────────────────────────────────────────────────────────────

type NodeStatus = 'pending' | 'running' | 'success' | 'failed' | 'stopped'

interface GraphNode {
  id: string
  label: string
  assetId: string
  status: NodeStatus
  layer: string
  // force-graph internals (injected at runtime)
  x?: number
  y?: number
}

interface GraphEdge {
  source: string
  target: string
  type: string
}

interface GraphData {
  nodes: GraphNode[]
  links: GraphEdge[]
}

// ─── Colour map ───────────────────────────────────────────────────────────────

const STATUS_COLOR: Record<NodeStatus, string> = {
  pending: '#1a1820',
  running: '#d4a648',
  success: '#4a8c5c',
  failed:  '#9c3a2a',
  stopped: '#5a5550',
}

// ─── Component ────────────────────────────────────────────────────────────────

interface Props {
  buildId: string
  chartId: string
}

export function LiveBuildGraph({ buildId, chartId }: Props) {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] })
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [connected, setConnected] = useState(false)
  const esRef = useRef<EventSource | null>(null)

  const addNode = useCallback((node: GraphNode) => {
    setGraphData((prev) => {
      if (prev.nodes.find((n) => n.id === node.id)) {
        return { ...prev, nodes: prev.nodes.map((n) => n.id === node.id ? { ...n, ...node } : n) }
      }
      return { ...prev, nodes: [...prev.nodes, node] }
    })
  }, [])

  const addEdge = useCallback((edge: GraphEdge) => {
    setGraphData((prev) => {
      const key = `${edge.source}__${edge.target}`
      if (prev.links.find((l) => `${l.source}__${l.target}` === key)) return prev
      return { ...prev, links: [...prev.links, edge] }
    })
  }, [])

  const updateNodeStatus = useCallback((id: string, status: NodeStatus) => {
    setGraphData((prev) => ({
      ...prev,
      nodes: prev.nodes.map((n) => n.id === id ? { ...n, status } : n),
    }))
  }, [])

  useEffect(() => {
    if (!buildId) return

    const es = new EventSource(`/api/build/events/${buildId}`)
    esRef.current = es
    setConnected(true)

    es.addEventListener('node_added', (e: MessageEvent) => {
      try { addNode(JSON.parse(e.data) as GraphNode) } catch {}
    })
    es.addEventListener('edge_added', (e: MessageEvent) => {
      try { addEdge(JSON.parse(e.data) as GraphEdge) } catch {}
    })
    es.addEventListener('status_changed', (e: MessageEvent) => {
      try {
        const { id, status } = JSON.parse(e.data) as { id: string; status: NodeStatus }
        updateNodeStatus(id, status)
      } catch {}
    })
    es.addEventListener('complete', () => { setConnected(false); es.close() })
    es.addEventListener('error', () => { setConnected(false); es.close() })

    return () => { es.close(); setConnected(false) }
  }, [buildId, addNode, addEdge, updateNodeStatus])

  const handleNodeClick = useCallback((node: unknown) => {
    setSelectedNode(node as GraphNode)
  }, [])

  if (!buildId) {
    return (
      <div
        className="flex items-center justify-center rounded-xl border border-[#1a1820] text-[#5a5550] text-sm"
        style={{ height: 500, background: '#08070a' }}
      >
        No active build. Start a build to see the live graph.
      </div>
    )
  }

  return (
    <div className="relative">
      {/* Connection indicator */}
      <div className="absolute top-3 right-3 z-10 flex items-center gap-1.5 text-xs text-[#8a8070]">
        <span
          className={`inline-block h-2 w-2 rounded-full ${connected ? 'bg-[#4a8c5c] animate-pulse' : 'bg-[#5a5550]'}`}
        />
        {connected ? 'Live' : 'Disconnected'}
      </div>

      <div style={{ height: 500, background: '#08070a' }} className="rounded-xl border border-[#1a1820] overflow-hidden">
        <ForceGraph2D
          graphData={graphData as unknown as { nodes: object[]; links: object[] }}
          nodeId="id"
          nodeLabel="label"
          nodeColor={(node) => STATUS_COLOR[(node as GraphNode).status] ?? '#1a1820'}
          nodeRelSize={6}
          linkColor={() => '#2a2830'}
          linkWidth={1}
          backgroundColor="#08070a"
          onNodeClick={handleNodeClick}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const n = node as GraphNode & { x: number; y: number }
            const r = 8
            const color = STATUS_COLOR[n.status] ?? '#1a1820'
            // Pulsing ring for running nodes
            if (n.status === 'running') {
              ctx.beginPath()
              ctx.arc(n.x, n.y, r + 3, 0, 2 * Math.PI)
              ctx.strokeStyle = `${color}55`
              ctx.lineWidth = 2
              ctx.stroke()
            }
            ctx.beginPath()
            ctx.arc(n.x, n.y, r, 0, 2 * Math.PI)
            ctx.fillStyle = color
            ctx.fill()
            ctx.strokeStyle = '#1a1820'
            ctx.lineWidth = 1.5
            ctx.stroke()
            // Label
            if (globalScale > 0.8) {
              ctx.font = `${Math.max(10 / globalScale, 6)}px sans-serif`
              ctx.fillStyle = '#c8bfb0'
              ctx.textAlign = 'center'
              ctx.fillText(n.label ?? n.id, n.x, n.y + r + 8)
            }
          }}
        />
      </div>

      {selectedNode && (
        <NodeDetailModal
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
        />
      )}
    </div>
  )
}
