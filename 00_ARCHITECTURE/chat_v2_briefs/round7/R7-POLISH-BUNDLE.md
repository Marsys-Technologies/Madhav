---
name: R7 POLISH BUNDLE — single-PR closure of Chat V2 post-§M.16 polish backlog
canonical_id: CHAT_V2_R7_POLISH_BUNDLE
version: 1.0
status: READY_FOR_EXECUTION
authored: 2026-05-18
governing_forensic: 00_ARCHITECTURE/CHAT_V2_F3_FORENSIC_v1_0.md §1 L4 + §2 + §3 + §4
governing_decision: Operator decision 2026-05-18 — R7 polish authorized for single-PR execution with --dangerously-skip-permissions, no per-PR operator visual review (workstream is closed, items are enhancement only)
branch: feat/chat-v2-r7-polish-bundle
base: main (POST R6.2 #84 + R6.3 #85 merge if those have landed; otherwise on top of §M.16 6c431f9 — R7 items do not conflict with R6.2/R6.3)
pr_title: "feat(chat-v2/r7): polish bundle — sidebar Logo + brand tokens + tracker consolidation + dead-component delete + tier-setter rename + mobile citation collapse + conversation rename/delete + CI smoke wiring"
estimated_loc: ~+250 (mostly N3 rename/delete + O6 mobile state + CI workflow); ~-200 (O5 consolidation + O11 delete + miscellaneous cleanup)
estimated_files: ~12
may_touch:
  - platform/src/components/consume/ConversationSidebarV2.tsx (L4 Logo + N2 typography + N3 DropdownMenu)
  - platform/src/components/consume/ConsumeChatV2.tsx (O5 tracker consolidation, O4 rename, mount-point updates)
  - platform/src/components/chat/CitationSidePanel.tsx (O6 mobile peek-collapse mode)
  - platform/src/components/consume/LiveReasoningCard.tsx (DELETE - O11)
  - platform/src/components/consume/__tests__/lifecycle_co3.test.tsx (O11 cleanup — remove LiveReasoningCard reference)
  - platform/src/components/consume/StreamingAnswer.tsx (O11 cleanup — remove dead comment)
  - platform/playwright.config.ts (add webServer block for CI)
  - .github/workflows/chat-v2-smoke.yml (CI smoke env vars)
  - .env.example (document new CI-only env var keys — read-only, never required for local dev)
must_not_touch:
  - platform/src/components/consume/AnswerView.tsx (LogPredictionAction is still ACTIVE here)
  - platform/src/components/consume/LogPredictionAction.tsx (DO NOT delete — actively used)
  - platform/src/components/consume/ConsumeChat.tsx (10-LoC re-export; do not modify)
  - platform/src/lib/firebase/server.ts (only consumed, not edited)
  - any feature flag (CHAT_V2_ENABLED is gone; no others touched)
  - the route.ts or any backend route handlers
  - the R6.2 / R6.3 fix-forward code paths (citation rendering — separate work)
operator_followups:
  - Provision GitHub Actions secrets: SMOKE_SESSION_COOKIE + SMOKE_CHART_ID (one-time setup, documented in §3.H)
  - Enable `chat-v2 smoke / smoke` as required check on `main` branch protection (manual GitHub UI step)
---

# §1 Mission

The Chat V2 Big Bang workstream closed at §M.16 (commit `6c431f9`) + §M.17 governance close (commit `1f82bdd`). The forensic at `CHAT_V2_F3_FORENSIC_v1_0.md` identified a dozen+ polish items beyond the P0 fixes (R6.1-R6.6 + §M.16). Seven of them remain unaddressed; this bundle ships all seven in a single PR plus the CI smoke wiring follow-up. After this lands, the F.3 forensic is fully discharged and the Chat V2 workstream has no remaining queued work.

Per operator decision 2026-05-18, R7 polish runs with:
- `--dangerously-skip-permissions` executor mode (no per-action approval prompts)
- No per-item operator visual review halts (items are non-functional polish)
- Automated gates only: `tsc --noEmit`, ESLint, `npm test`, grep proofs
- Single PR with all 7 items bundled — auto-merge authorized
- Items shipped in low-risk-first order so any failure halts at the smallest possible blast radius

Bounded by the same Ethical Framework as parent plans. No new architectural commitments — wire-up, refactoring, and CI plumbing only.

# §2 Scope

| § | ID | Item | Files | Net LoC |
|---|---|---|---|---|
| §3.A | L4 | Sidebar `<Logo />` at bottom of expanded state | ConversationSidebarV2 | +5 |
| §3.B | N2 | Sidebar header typography → brand-gold token | ConversationSidebarV2 | 0 (className swap) |
| §3.C | O5 | Consolidate 3 trackers → 1 `V2RuntimeTracker` | ConsumeChatV2 | -45 |
| §3.D | O11 | Delete `LiveReasoningCard.tsx` + cleanup references | 3 files | -120 (mostly the deleted file) |
| §3.E | O4 | Rename `setActiveTier` → `setActiveTierOverride` | ConsumeChatV2 + callers | 0 (4 sites renamed) |
| §3.F | O6 | Mobile citation panel peek-collapse mode | CitationSidePanel | +35 |
| §3.G | N3 | Conversation rename/delete via DropdownMenu | ConversationSidebarV2 | +75 |
| §3.H | CI | Playwright `webServer` + GitHub Actions secrets wiring | playwright.config.ts + chat-v2-smoke.yml + .env.example | +30 |

# §3 Implementation specification

## §3.A — Sidebar `<Logo />` at bottom of expanded state (L4)

**File:** `platform/src/components/consume/ConversationSidebarV2.tsx`

**Add import** (group with other component imports):
```tsx
import { Logo } from '@/components/brand/Logo'
```

**Render site:** at the bottom of the EXPANDED-state `<aside>` block (lines 178-264; closing `</aside>` at L263), insert before the closing tag:

```tsx
<div className="flex items-center justify-center px-3 py-3 border-t border-zinc-800 mt-auto">
  <Logo size="sm" className="opacity-40" />
</div>
```

Notes:
- `mt-auto` anchors to bottom of flex column.
- `opacity-40` keeps brand-gold low-volume so it doesn't compete with conversation rows.
- `size="sm"` matches the AppShellRail Logo presentation pattern.
- Logo render only in EXPANDED state — do NOT render in the collapsed-strip `null`-return path (L172-174).

## §3.B — Sidebar header typography → brand-gold token (N2)

**File:** `platform/src/components/consume/ConversationSidebarV2.tsx`

Two sites:

**Site 1 — SectionHeader (around L70):**

Current:
```tsx
className="text-[10px] font-semibold uppercase tracking-widest text-zinc-500 select-none"
```

Target:
```tsx
className="text-[9px] font-semibold uppercase tracking-[0.20em] text-[rgba(var(--brand-gold-rgb),0.38)] select-none"
```

**Site 2 — "Conversations" header (around L185):**

Current:
```tsx
className="text-xs font-semibold text-zinc-400 uppercase tracking-wide"
```

Target:
```tsx
className="text-[9px] font-semibold uppercase tracking-[0.20em] text-[rgba(var(--brand-gold-rgb),0.38)]"
```

Both now match the chart-meta typography token in `ConsumeChatV2.tsx:1420`. Visually unifies the brand language across header + sidebar.

## §3.C — Consolidate 3 trackers → 1 `V2RuntimeTracker` (O5)

**File:** `platform/src/components/consume/ConsumeChatV2.tsx`

Three components currently:
- `V2QueryIdTracker` (L969-994)
- `V2ConversationIdTracker` (L998-1030)
- `V2TitleTracker` (L1034-1061)

Mount sites (L1588-1594):
```tsx
<V2QueryIdTracker />
<V2ConversationIdTracker />
<V2TitleTracker />
```

**Replace** the three functions with a single `V2RuntimeTracker`:

```tsx
function V2RuntimeTracker() {
  const runtime = useThreadRuntime()
  const onQueryId = useContext(V2QueryIdCb)
  const onConversationId = useContext(V2ConversationIdCb)
  const onTitle = useContext(V2TitleCb)

  useEffect(() => {
    if (!onQueryId && !onConversationId && !onTitle) return

    let lastQueryId: string | null = null
    let lastConversationId: string | null = null
    let lastTitleEmit = false

    const unsub = runtime.subscribe(() => {
      const state = runtime.getState()
      const messages = state.messages

      // Single backward walk; collect query_id from latest assistant msg.
      // Single forward walk for title (first occurrence wins, emits once).
      let queryIdHit: string | null = null
      let conversationIdHit: string | null = null
      let titleHit = false

      for (let i = messages.length - 1; i >= 0; i--) {
        const msg = messages[i]
        if (msg.role !== 'assistant') continue
        if (!queryIdHit) {
          const custom = (msg.metadata as { custom?: { queryId?: string } } | undefined)?.custom
          if (custom?.queryId) {
            queryIdHit = custom.queryId
          } else {
            const data = (msg.metadata as unknown as { unstable_data?: ReadonlyArray<unknown> } | undefined)?.unstable_data ?? []
            for (const part of data) {
              const p = part as { query_id?: string }
              if (p.query_id) { queryIdHit = p.query_id; break }
            }
          }
        }
        if (!conversationIdHit) {
          const content = (msg.content ?? []) as ReadonlyArray<unknown>
          for (const part of content) {
            if (
              typeof part === 'object' && part !== null &&
              (part as Record<string, unknown>).type === 'data' &&
              (part as Record<string, unknown>).name === 'persistence'
            ) {
              const data = (part as Record<string, unknown>).data as Record<string, unknown>
              if (typeof data?.conversation_id === 'string') {
                conversationIdHit = data.conversation_id
                break
              }
            }
          }
        }
        if (queryIdHit && conversationIdHit) break
      }

      // Forward walk for title (any assistant msg with data-title part).
      for (const msg of messages) {
        if (msg.role !== 'assistant') continue
        const content = (msg.content ?? []) as ReadonlyArray<unknown>
        for (const part of content) {
          if (
            typeof part === 'object' && part !== null &&
            (part as Record<string, unknown>).type === 'data' &&
            (part as Record<string, unknown>).name === 'title'
          ) {
            titleHit = true
            break
          }
        }
        if (titleHit) break
      }

      // Emit only on transitions (avoid spam).
      if (queryIdHit && queryIdHit !== lastQueryId) {
        lastQueryId = queryIdHit
        if (onQueryId) onQueryId(queryIdHit)
      }
      if (conversationIdHit && conversationIdHit !== lastConversationId) {
        lastConversationId = conversationIdHit
        if (onConversationId) onConversationId(conversationIdHit)
      }
      if (titleHit && !lastTitleEmit) {
        lastTitleEmit = true
        if (onTitle) onTitle()
      }
    })

    return unsub
  }, [runtime, onQueryId, onConversationId, onTitle])

  return null
}
```

**Mount-point update (L1588-1594):**

Replace the three `<V2QueryIdTracker />` etc. lines with:
```tsx
{/* C.2 + W5 + E.1: unified runtime tracker — emits query_id, conversation_id, title in one subscribe loop */}
<V2RuntimeTracker />
```

**Idempotency notes:**
- `lastQueryId` + `lastConversationId` + `lastTitleEmit` are closure-scoped per-mount, replicating the original effect's "fire once per change" semantics.
- All three callbacks remain optional (consumer Context may be undefined).
- Performance: ~3x fewer subscribe loops during streams.

Delete the three old functions in their entirety.

## §3.D — Delete `LiveReasoningCard.tsx` + cleanup references (O11)

**File 1 — DELETE:** `platform/src/components/consume/LiveReasoningCard.tsx`

```bash
git rm platform/src/components/consume/LiveReasoningCard.tsx
```

**File 2 — `platform/src/components/consume/StreamingAnswer.tsx`** (L45 area): remove the now-stale comment reference to `LiveReasoningCard`. The comment is the only mention; no active import.

**File 3 — `platform/src/components/consume/__tests__/lifecycle_co3.test.tsx`**: remove the test cases that reference `LiveReasoningCard.tsx`. If the test file becomes empty after removal, delete the file entirely. Otherwise leave only the surviving assertions.

**DO NOT TOUCH** `LogPredictionAction.tsx` — actively imported and used by `AnswerView.tsx:9, 67`.

## §3.E — Rename `setActiveTier` → `setActiveTierOverride` (O4)

**File:** `platform/src/components/consume/ConsumeChatV2.tsx`

Four exact-match sites to update (use `replace_all` from `setActiveTier` to `setActiveTierOverride`):

1. **L173** (interface field):
   ```tsx
   setActiveTier: (t: AudienceTier) => void
   ```
   → 
   ```tsx
   setActiveTierOverride: (t: AudienceTier) => void
   ```

2. **L1212** (useState destructure):
   ```tsx
   const [activeTier, setActiveTier] = useState<AudienceTier>(audienceTier)
   ```
   → 
   ```tsx
   const [activeTier, setActiveTierOverride] = useState<AudienceTier>(audienceTier)
   ```

3. **L1213-1217** (context memo): the literal in the `useMemo` body and dependency array.

4. **L1141 (V2BottomBar useContext destructure + TierPicker onChange)**:
   ```tsx
   const { stack, style, lelEnabled, activeTier, audienceTier, setStack, setStyle, setLelEnabled, setActiveTier } = useContext(V2PrefsCtx)
   <TierPicker tier={activeTier} onChange={setActiveTier} />
   ```
   → both `setActiveTier` references renamed.

Use a single `replace_all` (only this exact identifier) — search for `setActiveTier` (without the suffix) and confirm there are exactly 4 hits across the file. Apply the rename.

Verify post-rename: `grep -c 'setActiveTier\b' platform/src/components/consume/ConsumeChatV2.tsx` returns 0 (no remaining bare references).

**Also**: add a JSDoc above the `audienceTier` field in `V2PrefsCtxValue` interface noting it's read-only (server prop, no setter):

```tsx
/** READ-ONLY: server-provided audience tier from chart_meta. The in-chat override is `activeTier` + `setActiveTierOverride`. */
audienceTier: AudienceTier
```

## §3.F — Mobile citation panel peek-collapse mode (O6)

**File:** `platform/src/components/chat/CitationSidePanel.tsx`

Add an internal collapsed state for mobile. Default collapsed when first cited. Tapping the peek header toggles expanded. Desktop (md+) ignores collapsed state — always full sidebar.

**Current outer aside:**
```tsx
<aside
  className="fixed bottom-0 inset-x-0 z-30 max-h-[45vh] overflow-y-auto md:static md:max-h-none md:w-64 md:shrink-0 md:overflow-y-auto flex flex-col gap-2 border-t md:border-t-0 md:border-l border-zinc-800 bg-zinc-950 p-3"
  data-testid="v2-citation-panel"
  aria-label="Pinned citations"
>
```

**Target — add state + peek header + conditional content:**

At top of `CitationSidePanel` function body, add:
```tsx
const [isCollapsed, setIsCollapsed] = useState(true)
```

Replace the outer aside with:
```tsx
<aside
  className={cn(
    'fixed bottom-0 inset-x-0 z-30 overflow-y-auto md:static md:w-64 md:shrink-0 md:overflow-y-auto flex flex-col gap-2 border-t md:border-t-0 md:border-l border-zinc-800 bg-zinc-950 p-3 transition-[max-height] duration-200',
    // Mobile collapsed/expanded; desktop ignores state.
    isCollapsed ? 'max-h-[60px]' : 'max-h-[45vh]',
    'md:max-h-none'
  )}
  data-testid="v2-citation-panel"
  aria-label="Pinned citations"
>
  {/* Mobile peek header — visible only on mobile (hidden md:hidden) */}
  <button
    type="button"
    onClick={() => setIsCollapsed(c => !c)}
    className="md:hidden flex items-center justify-between w-full text-xs font-semibold uppercase tracking-[0.20em] text-[rgba(var(--brand-gold-rgb),0.6)]"
    aria-expanded={!isCollapsed}
    aria-label={isCollapsed ? 'Expand citations' : 'Collapse citations'}
    data-testid="v2-citation-panel-peek-toggle"
  >
    <span>Citations · {pinnedCitations.length}</span>
    <span aria-hidden>{isCollapsed ? '▲' : '▼'}</span>
  </button>

  {/* Content — always rendered on desktop; hidden when mobile-collapsed */}
  <div className={cn('flex flex-col gap-2', isCollapsed && 'hidden md:flex')}>
    {/* existing content goes here */}
  </div>
</aside>
```

Keep the existing children inside the `<div className="flex flex-col gap-2">` wrapper. If `cn` utility is not yet imported, add `import { cn } from '@/lib/utils'`.

**Behavior:**
- Mobile collapsed (default): only the peek header shows; 60px tall.
- Mobile tapped: expands to 45vh, shows full list.
- Desktop: peek header hidden (`md:hidden`); content always visible.

## §3.G — Conversation rename/delete via DropdownMenu (N3)

**File:** `platform/src/components/consume/ConversationSidebarV2.tsx`

**Imports to add:**
```tsx
import { useState } from 'react'  // (may already be imported)
import { MoreHorizontal, PenSquare, Trash2 } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
```

**Add prop to `ConversationSidebarV2Props`:**
```tsx
onRename?: (id: string, currentTitle: string) => Promise<void> | void
onDelete?: (id: string) => Promise<void> | void
```

**Wire props through `ConversationItem` sub-component** (the one with `useState(false)` for hovered around L76-92):

Add to `ConversationItem` props:
```tsx
onRename?: (id: string, currentTitle: string) => Promise<void> | void
onDelete?: (id: string) => Promise<void> | void
```

**Replace the decorative `<span>` at L106-127** with a DropdownMenu:

```tsx
{(hovered || menuOpen) && (
  <DropdownMenu open={menuOpen} onOpenChange={setMenuOpen}>
    <DropdownMenuTrigger
      aria-label="Conversation actions"
      data-testid={`v2-conversation-menu-${conv.id}`}
      className="absolute right-1.5 top-1/2 -translate-y-1/2 inline-flex h-5 w-5 items-center justify-center rounded text-zinc-500 hover:text-zinc-200 hover:bg-zinc-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/30"
    >
      <MoreHorizontal className="h-3.5 w-3.5" aria-hidden />
    </DropdownMenuTrigger>
    <DropdownMenuContent align="end" sideOffset={2}>
      <DropdownMenuItem onClick={() => onRename?.(conv.id, conv.title)} data-testid={`v2-conversation-rename-${conv.id}`}>
        <PenSquare className="h-3.5 w-3.5" aria-hidden />
        Rename
      </DropdownMenuItem>
      <DropdownMenuSeparator />
      <DropdownMenuItem variant="destructive" onClick={() => onDelete?.(conv.id)} data-testid={`v2-conversation-delete-${conv.id}`}>
        <Trash2 className="h-3.5 w-3.5" aria-hidden />
        Delete
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
)}
```

Add a `const [menuOpen, setMenuOpen] = useState(false)` near the existing `hovered` state. The `menuOpen` flag ensures the menu doesn't disappear when the cursor leaves the row while a dropdown item is being clicked.

**Wire handlers in `ConsumeChatV2.tsx`** — the parent that mounts `<ConversationSidebarV2 />` (around L1359):

Add two handler functions near `handleSelectConversation`:

```tsx
const handleRenameConversation = useCallback(async (id: string, currentTitle: string) => {
  const newTitle = window.prompt('Rename conversation', currentTitle)
  if (!newTitle || newTitle.trim() === currentTitle.trim()) return
  try {
    const r = await fetch(`/api/conversations/${id}`, {
      method: 'PATCH',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ title: newTitle.trim() }),
    })
    if (!r.ok) throw new Error(`PATCH failed ${r.status}`)
    setSidebarReloadTick(t => t + 1)
  } catch (err) {
    console.error('Rename failed', err)
  }
}, [])

const handleDeleteConversation = useCallback(async (id: string) => {
  if (!window.confirm('Archive this conversation? It will be hidden from the list.')) return
  try {
    const r = await fetch(`/api/conversations/${id}`, { method: 'DELETE' })
    if (!r.ok) throw new Error(`DELETE failed ${r.status}`)
    if (activeConversationId === id) setActiveConversationId(null)
    setSidebarReloadTick(t => t + 1)
  } catch (err) {
    console.error('Delete failed', err)
  }
}, [activeConversationId])
```

Pass through to `<ConversationSidebarV2 ... onRename={handleRenameConversation} onDelete={handleDeleteConversation} />`.

**Note on UX:** `window.prompt` + `window.confirm` are intentionally minimal — this is R7 polish wiring, not a full UX. A nicer inline-input rename and modal-confirm delete are R8-tier work. The window dialogs unblock the functional gap and use the API endpoints correctly. Document this in the PR description.

## §3.H — Playwright `webServer` + GitHub Actions secrets wiring (CI smoke)

**File 1: `platform/playwright.config.ts`**

Add `webServer` block before the closing `})`:

```ts
webServer: {
  command: 'npm run dev',
  url: 'http://localhost:3000',
  reuseExistingServer: !process.env.CI,
  timeout: 120_000,
  stdout: 'pipe',
  stderr: 'pipe',
},
```

This spawns a dev server before tests in CI; reuses existing local server in dev.

**File 2: `.github/workflows/chat-v2-smoke.yml`**

Update the playwright step's `env:` block to inject Firebase + smoke env vars:

```yaml
env:
  SMOKE_SESSION_COOKIE: ${{ secrets.SMOKE_SESSION_COOKIE }}
  SMOKE_CHART_ID: ${{ secrets.SMOKE_CHART_ID }}
  NEXT_PUBLIC_FIREBASE_API_KEY: ${{ secrets.NEXT_PUBLIC_FIREBASE_API_KEY }}
  NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN: ${{ secrets.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN }}
  NEXT_PUBLIC_FIREBASE_PROJECT_ID: ${{ secrets.NEXT_PUBLIC_FIREBASE_PROJECT_ID }}
  NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET: ${{ secrets.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET }}
  NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID: ${{ secrets.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID }}
  NEXT_PUBLIC_FIREBASE_APP_ID: ${{ secrets.NEXT_PUBLIC_FIREBASE_APP_ID }}
  FIREBASE_ADMIN_CREDENTIALS: ${{ secrets.FIREBASE_ADMIN_CREDENTIALS }}
```

Replace the top-of-file informational comment block to reflect new state: "After R7-CI-WIRING (this commit), CI smoke runs E2E if secrets are provisioned; otherwise still skips."

**File 3: `.env.example`**

Append a CI-only section:

```
# ── CI smoke (R7-CI-WIRING) — DO NOT SET LOCALLY ──
# These vars are read by chat-v2-smoke.yml workflow only.
# Mint a long-lived session cookie locally and store as a GitHub Actions secret.
# SMOKE_SESSION_COOKIE=<long-lived __session cookie value>
# SMOKE_CHART_ID=<chart id accessible to the session user>
```

**Operator follow-up (NOT in this PR — documented in PR description):**

1. Mint a long-lived session cookie via `platform/scripts/dev/mint_session_cookie.ts` (existing tool).
2. Provision GitHub Actions secrets via repo Settings → Secrets:
   - `SMOKE_SESSION_COOKIE`
   - `SMOKE_CHART_ID`
   - (Firebase secrets above are likely already provisioned — verify, otherwise add)
3. Enable `chat-v2 smoke / smoke` as a required check on `main` branch protection rule.
4. Open a probe PR (e.g., README typo touching one of the workflow's path filters) to verify the workflow fires + passes E2E.

# §4 Acceptance criteria

For each section, automated proofs. No operator visual review halts.

**§3.A — L4 Logo:**
- [ ] `grep -n "from '@/components/brand/Logo'" platform/src/components/consume/ConversationSidebarV2.tsx` returns 1 hit.
- [ ] `grep -c '<Logo' platform/src/components/consume/ConversationSidebarV2.tsx` returns ≥ 1.

**§3.B — N2 typography:**
- [ ] `grep -c 'text-zinc-500' platform/src/components/consume/ConversationSidebarV2.tsx` decreases by 1.
- [ ] `grep -c 'text-zinc-400 uppercase tracking-wide' platform/src/components/consume/ConversationSidebarV2.tsx` returns 0.
- [ ] `grep -c 'tracking-\[0.20em\]' platform/src/components/consume/ConversationSidebarV2.tsx` returns ≥ 2.

**§3.C — O5 tracker consolidation:**
- [ ] `grep -c 'function V2QueryIdTracker\|function V2ConversationIdTracker\|function V2TitleTracker' platform/src/components/consume/ConsumeChatV2.tsx` returns 0.
- [ ] `grep -c 'function V2RuntimeTracker' platform/src/components/consume/ConsumeChatV2.tsx` returns 1.
- [ ] `grep -c '<V2RuntimeTracker' platform/src/components/consume/ConsumeChatV2.tsx` returns 1.

**§3.D — O11 dead code:**
- [ ] `test ! -f platform/src/components/consume/LiveReasoningCard.tsx` passes.
- [ ] `grep -rn 'LiveReasoningCard' platform/src` returns 0 hits.
- [ ] `LogPredictionAction.tsx` STILL EXISTS (`test -f platform/src/components/consume/LogPredictionAction.tsx`).

**§3.E — O4 setter rename:**
- [ ] `grep -c 'setActiveTierOverride' platform/src/components/consume/ConsumeChatV2.tsx` returns 4.
- [ ] `grep -c '\bsetActiveTier\b' platform/src/components/consume/ConsumeChatV2.tsx` returns 0 (note word-boundary).
- [ ] `grep -rn '\bsetActiveTier\b' platform/src` (without override suffix) returns 0 hits.

**§3.F — O6 mobile citation collapse:**
- [ ] `grep -n 'v2-citation-panel-peek-toggle' platform/src/components/chat/CitationSidePanel.tsx` returns 1 hit.
- [ ] `grep -n 'isCollapsed' platform/src/components/chat/CitationSidePanel.tsx` returns ≥ 2 hits.

**§3.G — N3 rename/delete:**
- [ ] `grep -c 'handleRenameConversation\|handleDeleteConversation' platform/src/components/consume/ConsumeChatV2.tsx` returns ≥ 4 (definitions + prop passes).
- [ ] `grep -c '<DropdownMenu' platform/src/components/consume/ConversationSidebarV2.tsx` returns ≥ 1.
- [ ] `grep -c 'v2-conversation-rename\|v2-conversation-delete' platform/src/components/consume/ConversationSidebarV2.tsx` returns 2.

**§3.H — CI smoke wiring:**
- [ ] `grep -c 'webServer' platform/playwright.config.ts` returns 1.
- [ ] `grep -c 'NEXT_PUBLIC_FIREBASE_API_KEY' .github/workflows/chat-v2-smoke.yml` returns ≥ 1.
- [ ] `grep -c 'SMOKE_SESSION_COOKIE' .env.example` returns ≥ 1.

**Cross-cutting:**
- [ ] `cd platform && npx tsc --noEmit` exits 0.
- [ ] `cd platform && npx eslint src/components/consume src/components/chat src/lib/config` exits 0.
- [ ] `cd platform && npm test` exits 0 (lifecycle_co3 test cleaned of LiveReasoningCard refs; all other tests still pass).

# §5 Verification commands

```bash
cd platform

# All section grep proofs (per §4)
grep -c "from '@/components/brand/Logo'" src/components/consume/ConversationSidebarV2.tsx
grep -c 'tracking-\[0.20em\]' src/components/consume/ConversationSidebarV2.tsx
grep -c 'function V2RuntimeTracker' src/components/consume/ConsumeChatV2.tsx
test ! -f src/components/consume/LiveReasoningCard.tsx && echo "LRC deleted" || echo "FAIL: LRC still exists"
grep -rn 'LiveReasoningCard' src/ && echo "FAIL: residual refs" || echo "LRC clean"
test -f src/components/consume/LogPredictionAction.tsx && echo "LPA preserved" || echo "FAIL: LPA gone"
grep -c 'setActiveTierOverride' src/components/consume/ConsumeChatV2.tsx  # expect 4
grep -c '\bsetActiveTier\b' src/components/consume/ConsumeChatV2.tsx      # expect 0
grep -n 'v2-citation-panel-peek-toggle' src/components/chat/CitationSidePanel.tsx
grep -c '<DropdownMenu' src/components/consume/ConversationSidebarV2.tsx
grep -c 'webServer' playwright.config.ts
grep -c 'NEXT_PUBLIC_FIREBASE_API_KEY' ../.github/workflows/chat-v2-smoke.yml

# Compile + lint + test
npx tsc --noEmit
npx eslint src/components/consume src/components/chat src/lib/config
npm test

# Workflow YAML still parses
npx --yes js-yaml ../.github/workflows/chat-v2-smoke.yml > /dev/null && echo "YAML clean"

cd ..
```

# §6 Hard constraints

- DO NOT touch `AnswerView.tsx` or `LogPredictionAction.tsx` (LogPredictionAction is active).
- DO NOT modify any other feature flag, route handler, or test fixture beyond §3.D's cleanup.
- DO NOT auto-merge if any acceptance criterion in §4 fails — halt with a report.
- DO NOT touch R6.2 or R6.3 code paths (synthesis prompt, MarkdownContent footnote component, lib/citations).
- DO NOT enable the required-check branch protection rule (§3.H operator follow-up).
- DO NOT provision the GitHub Actions secrets in this PR (operator manual step).
- DO NOT add per-PR operator visual review halts (R7 polish is auto-merge per operator decision 2026-05-18).
- DO use sub-agents within the executor session for items that touch DIFFERENT files (§3.D + §3.H can run in parallel; §3.A + §3.B + §3.C + §3.E + §3.G all touch ConvSidebarV2 or ConsumeChatV2 and must serialize).

# §7 Risks + mitigations

| Risk | Mitigation |
|---|---|
| Tracker consolidation introduces subtle regression in query_id / conversation_id / title emission | Add 3 unit tests under `__tests__/V2RuntimeTracker.test.tsx` (one per emit path). If unit tests don't fit Round 7's scope, instead manually verify each emit by sending a query in dev — but skip the manual gate per operator decision; rely on tsc + existing lifecycle tests to catch type drift. |
| `setActiveTierOverride` rename misses a use-site | `grep -rn '\bsetActiveTier\b' platform/src` after edit must return 0 hits. Cross-file (a typed import would surface as tsc error). |
| LiveReasoningCard test cleanup removes coverage for live-streaming animation | The component is already orphaned (StreamingAnswer references it only in a comment); deleting the test just removes test debt. Document in PR. |
| DropdownMenu wiring (N3) breaks accessibility (focus trap, keyboard nav) | The pattern is borrowed verbatim from existing `ConversationSidebar.tsx` legacy DropdownMenu wire — accessibility was tested there. Verify keyboard nav (Tab + Enter on menu item) post-merge in dev server. |
| `window.prompt` + `window.confirm` for rename/delete UX is too minimal — users will find it jarring | Documented as known-limited; R8 polish would replace with inline-input + modal. The window dialogs are the simplest unblock that uses the real endpoints. |
| Playwright `webServer` block fails to spawn dev server in CI due to missing Firebase env at boot | Operator follow-up provisions secrets BEFORE enabling required-check. Until then, smoke workflow uses webServer but skips actual tests if `SMOKE_SESSION_COOKIE` is missing — same skip-on-missing-secret behavior as before; this PR doesn't make CI worse. |
| Bundling 7 items in one PR makes review harder | Each section is self-contained per §3; reviewer can read by section. Net diff is small (~+250 / -200 LoC). Single PR is the operator's explicit velocity preference. |
| Auto-merge without visual review ships a UI regression | Items are non-functional polish. The visible risks (typography, Logo placement, mobile collapse, DropdownMenu pattern) are well-bounded; tsc + eslint + npm test catch type and lint issues. Worst case: rollback via `git revert`. |

# §8 PR description template

```
## What this PR ships

R7 polish bundle — single-PR closure of the Chat V2 post-§M.16 polish backlog. Seven discrete items + Playwright CI smoke wiring. After this lands, the F.3 forensic is fully discharged and the Chat V2 workstream has no remaining queued work.

Per operator decision 2026-05-18, R7 runs with `--dangerously-skip-permissions`, no per-item operator visual review halts, automated gates only (tsc + eslint + npm test + grep proofs), single PR with auto-merge.

## Items

| § | ID | Item | Status |
|---|---|---|---|
| §3.A | L4 | Sidebar `<Logo />` at bottom of expanded sidebar | ✅ |
| §3.B | N2 | Sidebar headers → brand-gold typography | ✅ |
| §3.C | O5 | Consolidate 3 trackers → 1 `V2RuntimeTracker` | ✅ |
| §3.D | O11 | Delete `LiveReasoningCard.tsx` (preserved `LogPredictionAction.tsx` — still active) | ✅ |
| §3.E | O4 | Rename `setActiveTier` → `setActiveTierOverride` | ✅ |
| §3.F | O6 | Mobile citation panel peek-collapse mode | ✅ |
| §3.G | N3 | Conversation rename/delete via DropdownMenu + `PATCH` / `DELETE` API wiring | ✅ |
| §3.H | CI | Playwright `webServer` + GitHub Actions secrets scaffold | ✅ (code) / ⏳ (operator follow-up) |

## Net code change

~+250 LoC across new logic; ~-200 LoC from O5 consolidation + O11 delete. Net ~+50 LoC. 12 files touched.

## ⚠ Operator follow-up for §3.H (CI smoke wiring)

This PR ships the code-side wiring. The full E2E gate requires:

1. Mint a long-lived `__session` cookie via `platform/scripts/dev/mint_session_cookie.ts`.
2. Provision GitHub Actions secrets (repo Settings → Secrets):
   - `SMOKE_SESSION_COOKIE`
   - `SMOKE_CHART_ID`
   - Verify `NEXT_PUBLIC_FIREBASE_*` + `FIREBASE_ADMIN_CREDENTIALS` already provisioned (used by deploy.yml).
3. Enable `chat-v2 smoke / smoke` as a required check on `main` branch protection.
4. Open a probe PR touching a workflow-filtered path to verify the workflow fires E2E.

Until those four steps are done, the workflow still skips vacuously — same as before this PR. This PR makes the wiring ready, not the gate active.

## Known limitations

- §3.G uses `window.prompt` + `window.confirm` for rename/delete UX. Functional but minimal — a future R8 polish would replace with inline-input + modal dialog. The window dialogs use the real API endpoints (existing `PATCH` + `DELETE /api/conversations/[id]`).

## Refs

- `00_ARCHITECTURE/chat_v2_briefs/round7/R7-POLISH-BUNDLE.md` (this PR's EXEC brief)
- `00_ARCHITECTURE/CHAT_V2_F3_FORENSIC_v1_0.md` §1 L4 + §2 + §3 + §4
- Operator decision 2026-05-18: single-PR R7 with auto-merge
```

# §9 Post-merge

- §3.H operator follow-up runbook (4 manual steps above).
- After secrets provisioned + required-check enabled: open a probe PR to verify the workflow fires E2E.
- Chat V2 workstream has no remaining queued work.

# §10 Changelog

- **v1.0 (2026-05-18, READY_FOR_EXECUTION)** — Initial authoring. Seven items + CI smoke wiring bundled into one PR. Operator decision authorized auto-merge for R7 polish. Per-item file:line targets verified via parallel sub-agent investigation. Two forensic corrections applied (O2 already-resolved, O11 reduced to single file delete preserving still-active `LogPredictionAction.tsx`).
