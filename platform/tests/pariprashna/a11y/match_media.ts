/**
 * jsdom `window.matchMedia` mock — installed per-test, restored via
 * `restoreMatchMedia()` in an `afterEach`. Real component code
 * (`DockController.isNarrowViewport`, `PickerPopover.useIsMobileViewport`,
 * `useReducedMotion`) calls `window.matchMedia(query).matches` directly;
 * this mock lets a test deterministically simulate a given viewport/
 * preference state without a real browser layout engine.
 */
let original: typeof window.matchMedia | undefined

export function installMatchMedia(matches: (query: string) => boolean): void {
  if (original === undefined) original = window.matchMedia
  window.matchMedia = ((query: string) =>
    ({
      matches: matches(query),
      media: query,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    }) as unknown as MediaQueryList) as typeof window.matchMedia
}

/** All `(max-width: …)` queries match (mobile/narrow viewport); everything else (reduced-motion, contrast) does not. */
export function installMobileViewport(): void {
  installMatchMedia((q) => q.includes('max-width'))
}

/** No media query matches — desktop viewport, no reduced-motion/contrast preference. */
export function installDesktopViewport(): void {
  installMatchMedia(() => false)
}

export function restoreMatchMedia(): void {
  if (original !== undefined) window.matchMedia = original
}
