'use client'

import { Check, ChevronDown, Database, User } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  getModelMeta,
  stackPicker,
  type ModelStack,
} from '@/lib/models/registry'
import { cn } from '@/lib/utils'
import { usePersonas } from '@/hooks/usePersonas'

// ModelId kept as a string alias — legacy consumers may still import this type.
export type ModelId = string
export type StyleId = 'acharya' | 'brief' | 'client'

export const STYLE_OPTIONS: { id: StyleId; label: string; hint: string }[] = [
  { id: 'acharya', label: 'Acharya depth', hint: 'Full rigor, technical Jyotish' },
  { id: 'brief', label: 'Brief', hint: '1–2 short paragraphs, lead with the answer' },
  { id: 'client', label: 'Simple', hint: 'Plain language for someone unfamiliar with Jyotish' },
]

/** Format a raw token count as a human-readable context-window label. */
function formatCtx(tokens: number | undefined): string | null {
  if (!tokens) return null
  if (tokens >= 1_000_000) return `${tokens / 1_000_000}M ctx`
  if (tokens >= 1_000) return `${Math.round(tokens / 1_000)}K ctx`
  return `${tokens} ctx`
}

/**
 * P7 D.7.2 — NIM degraded indicator.
 *
 * The brief asked us not to invent a new health system. There is no
 * `useStackHealth` hook in this codebase; circuit-breaker state for the
 * planner exists but isn't exposed to the client. This helper reads
 * `NEXT_PUBLIC_NIM_STACK_DEGRADED` (build-time env), which an operator can
 * flip while NIM is impaired. Returns false by default — the option remains
 * fully selectable; only the visual cue toggles.
 */
function isNimDegraded(): boolean {
  if (typeof process === 'undefined') return false
  return process.env.NEXT_PUBLIC_NIM_STACK_DEGRADED === 'true'
}

interface Props {
  stack: ModelStack
  style: StyleId
  onStackChange: (s: ModelStack) => void
  onStyleChange: (s: StyleId) => void
  disabled?: boolean
  /** R9-S3: Active persona ID; null means no persona active. */
  activePersonaId?: string | null
  /** R9-S3: Callback when user selects a persona; null = clear selection. */
  onPersonaChange?: (personaId: string | null) => void
}

// DD-2 (PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md §2): ANTHROPIC_API_KEY is
// unprovisioned in production and the anthropic stack has been failing silently
// since 2026-08-01 (production default is Gemini). Delist it from the stack
// picker rather than provision a key. Hidden by default; set
// NEXT_PUBLIC_MARSYS_ANTHROPIC_HIDDEN=false explicitly to re-show it once a key
// is provisioned and the qualification suite passes.
const ANTHROPIC_HIDDEN = process.env.NEXT_PUBLIC_MARSYS_ANTHROPIC_HIDDEN !== 'false'

export function ModelStylePicker({ stack, style, onStackChange, onStyleChange, disabled, activePersonaId, onPersonaChange }: Props) {
  const stacks = stackPicker().filter(s => !(ANTHROPIC_HIDDEN && s.stack === 'anthropic'))
  const currentStack = stacks.find(s => s.stack === stack) ?? stacks[0]
  const currentStyle = STYLE_OPTIONS.find(s => s.id === style) ?? STYLE_OPTIONS[0]
  const ctxLabel = formatCtx(currentStack.synthesisContextWindow)

  // R9-S3: Persona list — only fetch when personas are enabled (NEXT_PUBLIC flag)
  const showPersonas = process.env.NEXT_PUBLIC_MARSYS_FLAG_R9_PERSONAS !== 'false'
  const { personas } = usePersonas()
  const activePersona = personas.find(p => p.id === activePersonaId) ?? null

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        disabled={disabled}
        aria-label={`Stack: ${currentStack.label}, Style: ${currentStyle.label}`}
        className={cn(
          'inline-flex h-7 items-center gap-1.5 rounded-md px-2 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40',
          disabled && 'pointer-events-none opacity-50'
        )}
      >
        <Database className="size-3.5" />
        <span className="font-medium text-foreground">{currentStack.label}</span>
        {ctxLabel && <span className="text-muted-foreground">{ctxLabel}</span>}
        <span className="hidden sm:inline">· {currentStyle.label}</span>
        <ChevronDown className="size-3" />
      </DropdownMenuTrigger>

      <DropdownMenuContent align="start" className="w-72">
        {/* ── R9-S3: Personas section ────────────────────────────────────────── */}
        {showPersonas && onPersonaChange && (
          <>
            <DropdownMenuGroup>
              <DropdownMenuLabel className="text-[11px] uppercase tracking-wider text-muted-foreground flex items-center gap-1">
                <User className="size-3" aria-hidden />
                Persona
              </DropdownMenuLabel>

              {personas.length === 0 ? (
                <DropdownMenuItem
                  className="text-xs text-muted-foreground"
                  onSelect={() => { window.location.href = '/settings/personas' }}
                >
                  No personas yet — Manage
                </DropdownMenuItem>
              ) : (
                <>
                  {/* "None" option — clears persona */}
                  <DropdownMenuItem onClick={() => onPersonaChange(null)} className="flex items-start gap-2">
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium text-muted-foreground">None</div>
                    </div>
                    {activePersonaId === null && <Check className="mt-0.5 size-3.5 shrink-0" />}
                  </DropdownMenuItem>
                  {personas.map(p => (
                    <DropdownMenuItem key={p.id} onClick={() => {
                      onPersonaChange(p.id)
                      if (p.default_style) onStyleChange(p.default_style as StyleId)
                      if (p.default_stack) onStackChange(p.default_stack as ModelStack)
                    }} className="flex items-start gap-2">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1">
                          <span className="text-sm font-medium">{p.name}</span>
                          {p.is_default && <span className="rounded bg-muted px-1 py-0.5 text-[10px] text-muted-foreground">default</span>}
                        </div>
                        <div className="flex gap-1 mt-0.5">
                          {p.default_style && <span className="rounded bg-muted px-1 text-[9px] text-muted-foreground">{p.default_style}</span>}
                          {p.default_stack && <span className="rounded bg-muted px-1 text-[9px] text-muted-foreground">{p.default_stack}</span>}
                        </div>
                      </div>
                      {activePersonaId === p.id && <Check className="mt-0.5 size-3.5 shrink-0" />}
                    </DropdownMenuItem>
                  ))}
                  <DropdownMenuItem
                    className="text-[11px] text-muted-foreground mt-0.5"
                    onSelect={() => { window.location.href = '/settings/personas' }}
                  >
                    Manage Personas →
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
          </>
        )}

        {/* ── Stack section ─────────────────────────────────────────────────── */}
        <DropdownMenuGroup>
          <DropdownMenuLabel className="text-[11px] uppercase tracking-wider text-muted-foreground">
            Model Stack
          </DropdownMenuLabel>
          {stacks.map(opt => {
            const synthMeta = getModelMeta(opt.synthesisModelId)
            const optCtx = formatCtx(opt.synthesisContextWindow)
            const showLimited = opt.stack === 'nim' && isNimDegraded()
            return (
              <DropdownMenuItem
                key={opt.stack}
                onClick={() => onStackChange(opt.stack)}
                className="flex items-start gap-2"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm font-medium">{opt.label}</span>
                    {opt.isDefault && (
                      <span className="rounded bg-muted px-1 py-0.5 text-[10px] text-muted-foreground">
                        default
                      </span>
                    )}
                    {showLimited && (
                      <span
                        title="NIM is currently degraded; calls may fall back to the secondary stack."
                        className="rounded bg-amber-400/10 px-1.5 py-0 text-[9px] text-amber-400 ring-1 ring-amber-400/30"
                      >
                        Limited
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-muted-foreground">
                    {synthMeta?.label ?? opt.synthesisModelId}
                    {optCtx && ` · ${optCtx}`}
                  </div>
                </div>
                {stack === opt.stack && <Check className="mt-0.5 size-3.5 shrink-0" />}
              </DropdownMenuItem>
            )
          })}
        </DropdownMenuGroup>

        <DropdownMenuSeparator />

        {/* ── Style section (unchanged) ────────────────────────────────────── */}
        <DropdownMenuGroup>
          <DropdownMenuLabel className="text-[11px] uppercase tracking-wider text-muted-foreground">
            Style
          </DropdownMenuLabel>
          {STYLE_OPTIONS.map(opt => (
            <DropdownMenuItem
              key={opt.id}
              onClick={() => onStyleChange(opt.id)}
              className="flex items-start gap-2"
            >
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium">{opt.label}</div>
                <div className="text-[11px] text-muted-foreground">{opt.hint}</div>
              </div>
              {style === opt.id && <Check className="mt-0.5 size-3.5 shrink-0" />}
            </DropdownMenuItem>
          ))}
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
