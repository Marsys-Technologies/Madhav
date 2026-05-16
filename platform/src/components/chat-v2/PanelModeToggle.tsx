'use client'

import { createContext, useContext } from 'react'

export interface PanelOptInContextValue {
  panelOptIn: boolean
  setPanelOptIn: (v: boolean) => void
}

export const PanelOptInCtx = createContext<PanelOptInContextValue>({
  panelOptIn: false,
  setPanelOptIn: () => {},
})

export function PanelModeToggle() {
  const { panelOptIn, setPanelOptIn } = useContext(PanelOptInCtx)

  return (
    <button
      type="button"
      role="switch"
      aria-checked={panelOptIn}
      onClick={() => setPanelOptIn(!panelOptIn)}
      title="Panel mode — runs multiple models and adjudicates for higher-confidence answers"
      className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-[11px] font-medium transition-colors ${
        panelOptIn
          ? 'bg-violet-600/30 text-violet-300 border border-violet-500/40'
          : 'bg-zinc-800/60 text-zinc-500 border border-zinc-700/40 hover:text-zinc-400 hover:bg-zinc-800'
      }`}
      data-testid="v2-panel-mode-toggle"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 14 14"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.3"
        className="h-3 w-3"
        aria-hidden="true"
      >
        <circle cx="5" cy="7" r="3" />
        <circle cx="9" cy="7" r="3" />
        <path d="M7 7h0" strokeWidth="2" strokeLinecap="round" />
      </svg>
      Panel mode
      {panelOptIn && <span className="text-[10px] opacity-60">on</span>}
    </button>
  )
}
