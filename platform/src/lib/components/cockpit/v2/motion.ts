// motion.ts — the Nirmāṇa motion vocabulary.
// One small shared set of curves + durations so every animated surface on the
// build-tracker page (tabs, panels, rows, progress, modals, graph) moves with
// the same hand. Exponential ease-out, no springs / bounce / elastic
// (brand motion law: "ease out with exponential curves, no overshoot").

import type { Transition } from 'framer-motion'

// Cubic-bezier easing curves.
export const EASE = {
  // expo-out: decisive arrival, no overshoot — for one-directional entrances.
  out: [0.16, 1, 0.3, 1] as [number, number, number, number],
  // quint in-out: symmetric — for reversible motions (expand / collapse).
  inOut: [0.83, 0, 0.17, 1] as [number, number, number, number],
}

// Durations (seconds).
export const DUR = {
  micro: 0.12, // hover/colour cross-fades
  base: 0.22, // default UI transitions
  panel: 0.32, // layer expand / collapse
  modal: 0.26, // modal in / out
}

// Stagger rhythm between sibling items (rows, edges).
export const STAGGER = 0.035 // 35ms

// Ready-made transitions for the common cases.
export const T_OUT: Transition = { duration: DUR.base, ease: EASE.out }
export const T_PANEL: Transition = { duration: DUR.panel, ease: EASE.inOut }
export const T_MODAL: Transition = { duration: DUR.modal, ease: EASE.out }
