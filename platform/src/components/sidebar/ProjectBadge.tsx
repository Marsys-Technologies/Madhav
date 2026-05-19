'use client'

interface ProjectBadgeProps {
  name: string
}

export function ProjectBadge({ name }: ProjectBadgeProps) {
  return (
    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-semibold tracking-wide bg-indigo-900/40 text-indigo-300 border border-indigo-700/30 ml-1 shrink-0 max-w-[80px] truncate">
      {name}
    </span>
  )
}
