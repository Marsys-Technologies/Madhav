'use client'

/**
 * ToolCoverageMatrix — P6 D.6.3.
 *
 * Compact flex-wrap of every manifest tool with one of four states:
 *   - gold: planned + executed + non-empty results
 *   - amber: planned + executed + empty results
 *   - dark: planned but never executed (rare; parallel fetch failure)
 *   - muted: not planned (skipped)
 */

interface ToolResult {
  rows?: number
  chunks?: number
  empty: boolean
}

interface Props {
  manifestTools: string[]
  planned: string[]
  executed: string[]
  results: Record<string, ToolResult | undefined>
}

type State = 'gold' | 'amber' | 'dark' | 'muted'

function classify(tool: string, planned: string[], executed: string[], results: Record<string, ToolResult | undefined>): State {
  if (!planned.includes(tool)) return 'muted'
  if (!executed.includes(tool)) return 'dark'
  const r = results[tool]
  if (r && !r.empty) return 'gold'
  return 'amber'
}

const STATE_CLASS: Record<State, string> = {
  gold: 'bg-[var(--brand-gold)]/15 text-[#fce29a] ring-1 ring-[var(--brand-gold)]/40',
  amber: 'bg-amber-400/10 text-amber-300 ring-1 ring-amber-400/30',
  dark: 'bg-[oklch(0.13_0.010_70)] text-muted-foreground/60 ring-1 ring-border',
  muted: 'bg-muted/20 text-muted-foreground ring-1 ring-border',
}

const STATE_SUB: Record<State, (r?: ToolResult) => string> = {
  gold: r => `${r?.rows ?? r?.chunks ?? 0} ${r?.chunks != null ? 'chunks' : 'rows'}`,
  amber: () => 'empty',
  dark: () => 'not run',
  muted: () => 'skipped',
}

export function ToolCoverageMatrix({ manifestTools, planned, executed, results }: Props) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {manifestTools.map(tool => {
        const state = classify(tool, planned, executed, results)
        return (
          <span
            key={tool}
            title={
              state === 'muted'
                ? 'Available in manifest but not selected by planner'
                : state === 'dark'
                  ? 'Planned but did not execute'
                  : state === 'amber'
                    ? 'Executed; returned no rows'
                    : 'Executed; returned data'
            }
            className={`inline-flex items-center gap-1 rounded px-2 py-1 text-[10px] ${STATE_CLASS[state]}`}
          >
            <span className="font-mono">{tool}</span>
            <span className="opacity-70">· {STATE_SUB[state](results[tool])}</span>
          </span>
        )
      })}
    </div>
  )
}
