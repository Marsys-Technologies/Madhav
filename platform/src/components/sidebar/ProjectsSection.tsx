'use client'

import type { Project } from '@/types/projects'
import { FolderOpen } from 'lucide-react'

interface ProjectsSectionProps {
  projects: Project[]
  activeProjectId: string | null
  onSelectProject: (id: string | null) => void
  onNewProject: () => void
}

export function ProjectsSection({
  projects,
  activeProjectId,
  onSelectProject,
  onNewProject,
}: ProjectsSectionProps) {
  return (
    <div className="border-b border-zinc-800 pb-1">
      <div className="flex items-center justify-between px-3 pt-2 pb-1">
        <span className="text-[9px] font-semibold uppercase tracking-[0.20em] text-[rgba(var(--brand-gold-rgb),0.38)]">
          Projects
        </span>
        <button
          type="button"
          onClick={onNewProject}
          title="New project"
          className="flex h-5 w-5 items-center justify-center rounded text-zinc-500 hover:bg-zinc-800 hover:text-zinc-200 transition-colors"
          data-testid="v2-new-project"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none" className="h-3 w-3" aria-hidden>
            <path d="M8 2v12M2 8h12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      {projects.length === 0 && (
        <p className="px-3 py-1.5 text-[10px] text-zinc-600">No projects yet</p>
      )}

      {/* "All" shortcut — clears project filter */}
      {projects.length > 0 && (
        <button
          type="button"
          onClick={() => onSelectProject(null)}
          className={`w-full flex items-center gap-1.5 text-left px-3 py-1.5 text-xs rounded-md transition-colors ${
            activeProjectId === null
              ? 'bg-indigo-600/10 text-indigo-300'
              : 'text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300'
          }`}
          data-testid="v2-project-all"
        >
          <FolderOpen className="h-3 w-3 shrink-0" aria-hidden />
          All conversations
        </button>
      )}

      {projects.map(p => (
        <button
          key={p.id}
          type="button"
          onClick={() => onSelectProject(p.id)}
          className={`w-full flex items-center gap-1.5 text-left px-3 py-1.5 text-xs rounded-md transition-colors truncate ${
            activeProjectId === p.id
              ? 'bg-indigo-600/20 text-indigo-300'
              : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
          }`}
          data-testid={`v2-project-item-${p.id}`}
        >
          <FolderOpen className="h-3 w-3 shrink-0" aria-hidden />
          <span className="truncate">{p.name}</span>
        </button>
      ))}
    </div>
  )
}
