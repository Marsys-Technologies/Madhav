/**
 * Motion constitution audit (§5.7, BRIEF_PB-4 Lane F-2) — "every animation
 * cites its constitution slot or is cut." This is the CI-checkable half of
 * that: it PARSES the real stylesheet (not a copy-pasted snapshot of it) and
 * asserts THIS LANE'S two new animation classes — `.pp-dock-seal-in` (the
 * Seal step 4, dock ledger fade) and `.pp-closing-rule` (the Seal step 5,
 * the closing-rule draw) — against the constitution's actual rules:
 *   - only `opacity` and/or `transform` may be animated (never layout
 *     properties);
 *   - the one easing curve (`var(--pp-ease)`, itself asserted to equal the
 *     spec's `cubic-bezier(0.25, 0.6, 0.3, 1)`) is used, never a bespoke one;
 *   - the duration sits in an explicitly-permitted slot: region mounts at
 *     160–200ms, or the two named >240ms exceptions (the Seal's
 *     closing-rule draw and the empty state's ecliptic line) at exactly
 *     400ms — nothing else may exceed 240ms.
 *
 * SCOPE (honest, not full-file): a full-repo audit would also need to grade
 * `pp-spin` (900ms), `pp-pulse` (1100ms), and `pp-breathe` (2400ms) — all
 * pre-existing, ambient, INFINITE-loop indicators authored by earlier lanes
 * (loading spinners, streaming dots), not one-shot state-transition
 * animations. Their raw durations read as violating "nothing slower than
 * 400ms" if that clause is applied to a continuous loop the same way it
 * applies to a discrete transition — but the constitution's own text names
 * the breathing hairline as "the only *ambient* motion", which pp-spin and
 * pp-pulse (also ambient/infinite, also pre-existing) sit alongside. That
 * tension predates this lane (`git log` shows these three keyframes were
 * already in `pariprashna.css` before Lane F-2 touched it) and is recorded
 * here as an honest, un-fixed residual rather than silently certified
 * clean by scoping the audit around it. This lane's sidebar streaming dot
 * REUSES the existing `data-pp-pulse` primitive rather than adding a new
 * ambient animation — asserted below — which is the compliant move
 * available within this lane's file scope.
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

const CSS_PATH = join(__dirname, '../../src/components/pariprashna/pariprashna.css')
const css = readFileSync(CSS_PATH, 'utf8')

const ONLY_MOTION_PROPERTIES = new Set(['opacity', 'transform'])
const SPEC_EASE = 'cubic-bezier(0.25, 0.6, 0.3, 1)'
// §5.7: 120ms micro, 160–200ms region mounts, 240ms sheet/popover max, and
// the two named exceptions at 400ms (Seal closing-rule draw + ecliptic line).
const PERMITTED_ONE_SHOT_DURATIONS_MS = [120, 160, 180, 200, 240, 400]

/** Extracts the animated CSS properties inside one `@keyframes <name> { ... }` block. */
function propertiesAnimatedByKeyframes(cssText: string, keyframesName: string): string[] {
  const re = new RegExp(`@keyframes\\s+${keyframesName}\\s*{([\\s\\S]*?)}\\s*(?=@keyframes|$)`, 'm')
  const match = cssText.match(re)
  if (!match) throw new Error(`@keyframes ${keyframesName} not found in pariprashna.css`)
  const body = match[1]
  const props = new Set<string>()
  // Matches `<property>:` inside each `from {}` / `to {}` / `N% {}` sub-block.
  for (const propMatch of body.matchAll(/([a-zA-Z-]+)\s*:/g)) {
    props.add(propMatch[1])
  }
  return Array.from(props)
}

/** Extracts the `animation: <name> <duration> <easing...>` shorthand for one class selector. */
function animationShorthandFor(cssText: string, selector: string): { name: string; durationMs: number; rest: string } {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const re = new RegExp(`${escaped}\\s*{[^}]*animation:\\s*([^;]+);`, 'm')
  const match = cssText.match(re)
  if (!match) throw new Error(`No animation shorthand found for ${selector}`)
  const decl = match[1].trim()
  const [name, durationToken, ...restTokens] = decl.split(/\s+/)
  const durationMs = durationToken.endsWith('ms') ? parseFloat(durationToken) : parseFloat(durationToken) * 1000
  return { name, durationMs, rest: restTokens.join(' ') }
}

describe('Motion constitution audit — this lane\'s new animations', () => {
  it('the one easing curve token resolves to the spec\'s cubic-bezier', () => {
    const match = css.match(/--pp-ease:\s*([^;]+);/)
    expect(match).not.toBeNull()
    expect(match![1].trim()).toBe(SPEC_EASE)
  })

  it('.pp-dock-seal-in (Seal step 4, dock ledger fade): opacity-only, region-mount duration, the shared ease', () => {
    const { name, durationMs, rest } = animationShorthandFor(css, '.pp-dock-seal-in')
    expect(name).toBe('pp-fade-in')
    expect(PERMITTED_ONE_SHOT_DURATIONS_MS).toContain(durationMs)
    expect(durationMs).toBeGreaterThanOrEqual(160)
    expect(durationMs).toBeLessThanOrEqual(200)
    expect(rest).toContain('var(--pp-ease)')

    const animatedProps = propertiesAnimatedByKeyframes(css, 'pp-fade-in')
    for (const prop of animatedProps) {
      expect(ONLY_MOTION_PROPERTIES.has(prop)).toBe(true)
    }
  })

  it('.pp-closing-rule (Seal step 5, the closing-rule draw): transform-only, exactly 400ms, the shared ease — the one named >240ms exception', () => {
    const { name, durationMs, rest } = animationShorthandFor(css, '.pp-closing-rule')
    expect(name).toBe('pp-draw-x')
    expect(durationMs).toBe(400)
    expect(rest).toContain('var(--pp-ease)')

    const animatedProps = propertiesAnimatedByKeyframes(css, 'pp-draw-x')
    for (const prop of animatedProps) {
      expect(ONLY_MOTION_PROPERTIES.has(prop)).toBe(true)
    }
  })

  it('the sidebar streaming dot reuses the existing pp-pulse primitive rather than adding a new ambient animation', () => {
    // history/Sidebar.tsx marks its streaming dots with `data-pp-pulse` —
    // the SAME hook `pariprashna.css` already styles for the dock/working
    // band. Asserting the shared selector still covers `[data-pp-pulse]`
    // generically (not sidebar-specific) proves the reuse is real, not a
    // same-named-but-different rule.
    expect(css).toMatch(/\.pp-root \[data-pp-pulse\]\s*{\s*animation:\s*pp-pulse/)
    const sidebarSource = readFileSync(join(__dirname, '../../src/components/pariprashna/history/Sidebar.tsx'), 'utf8')
    expect(sidebarSource).toMatch(/data-pp-pulse/)
    // No new @keyframes were authored for the sidebar dot.
    expect(sidebarSource).not.toMatch(/@keyframes/)
  })

  it('both new classes are covered by the reduced-motion collapse (the `.pp-root *` universal override)', () => {
    const reducedMotionBlock = css.match(/@media \(prefers-reduced-motion: reduce\) {([\s\S]*?)}\s*}\s*$/m)
    expect(reducedMotionBlock).not.toBeNull()
    // The universal `.pp-root * { animation-duration: 0.01ms !important; }`
    // rule applies to every element regardless of class, so a new class
    // never needs its own reduced-motion carve-out — asserted by presence
    // of that universal selector rather than per-class enumeration (which
    // would silently pass for a class the block never mentions).
    expect(css).toMatch(/\.pp-root \* {\s*transition-duration: 0\.01ms !important;\s*animation-duration: 0\.01ms !important;\s*}/)
  })
})
