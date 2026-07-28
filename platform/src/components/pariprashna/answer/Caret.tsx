/**
 * The caret (§5.4): a styled inline element that is a DOM sibling of the
 * streaming text node inside the tail block. It moves because text is
 * inserted before it, never by coordinate math — so it can never orphan.
 * `hollow` swaps its fill during a reconnect (same element, no reflow).
 */
export function Caret({ hollow = false }: { hollow?: boolean }) {
  return <span className="pp-caret" data-pp-caret data-hollow={hollow || undefined} aria-hidden />
}
