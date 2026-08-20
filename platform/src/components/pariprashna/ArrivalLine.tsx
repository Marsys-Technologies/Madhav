/**
 * The arrival line (§3.2, §4 J2, AC-16) — "the instrument saying *I know
 * where we are* before a word is typed." Chrome, not transcript: it sits
 * beneath the thread header, renders once per session, never scrolls with
 * the conversation, and is derived from L1/Kāla truth — NEVER model-composed
 * (gate 7 wire-taps this).
 *
 * SCOPE NOTE (P2-H / lane F-2): the real L1/Kāla-sourced line is P4-F
 * territory (recall + arrival-line wave, `PARIPRASHNA_TARGET_ARCHITECTURE`
 * A-41) — this lane's file scope (`components/pariprashna/**` +
 * `app/clients/[id]/pariprashna/page.tsx`) does not include the data layer
 * (`lib/pariprashna/**`, API routes, or a `kala_now_get`-shaped capability
 * call) that would compute a real daśā year / open-window count. This
 * component is therefore the STRUCTURAL placeholder only: it renders
 * `arrival` verbatim when a caller supplies it (the real integration's
 * contract), and renders nothing at all — an honest null, never an invented
 * "coming soon" caption a real user would see — when no data is wired
 * (§N.7 item 6: an honest null beats an invented judgment). The fixture host
 * (`fixtures/arrival.ts`) supplies a labelled sample string for dev/QA
 * demonstration only; the live host passes no `arrival` prop today.
 */
export interface ArrivalLineData {
  /** e.g. "Śani daśā, fourth year · one prediction window open — mid-2027." */
  text: string
}

export function ArrivalLine({ arrival }: { arrival: ArrivalLineData | null }) {
  if (!arrival) return null
  return (
    <p
      data-testid="pp-arrival-line"
      className="px-6"
      style={{
        margin: '10px 0 0',
        fontFamily: 'var(--pp-font-sans)',
        fontSize: 12.5,
        color: 'var(--pp-ink-dim)',
        lineHeight: 1.4,
      }}
    >
      {arrival.text}
    </p>
  )
}
