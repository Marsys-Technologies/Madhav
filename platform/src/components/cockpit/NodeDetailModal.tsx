'use client'

/**
 * NodeDetailModal — simple modal showing node details on click
 * [PHASE-C-03 sub]
 */

interface GraphNode {
  id: string
  label: string
  assetId: string
  status: string
  layer: string
}

interface Props {
  node: GraphNode
  onClose: () => void
}

export function NodeDetailModal({ node, onClose }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div
        className="bg-[#0d0c10] border border-[#1a1820] rounded-xl p-6 w-80 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-serif text-base text-[#d4a648]">{node.label || node.id}</h3>
          <button
            onClick={onClose}
            className="text-[#5a5550] hover:text-[#c8bfb0] text-lg leading-none"
          >
            ×
          </button>
        </div>
        <dl className="grid gap-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-[#8a8070]">Asset ID</dt>
            <dd className="font-mono text-[#c8bfb0] text-xs">{node.assetId}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-[#8a8070]">Status</dt>
            <dd className="text-[#f5f0e8] capitalize">{node.status}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-[#8a8070]">Layer</dt>
            <dd className="text-[#f5f0e8]">{node.layer}</dd>
          </div>
        </dl>
      </div>
    </div>
  )
}
