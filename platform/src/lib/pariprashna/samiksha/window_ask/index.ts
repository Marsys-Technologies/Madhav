/**
 * The window-opening ask (lane P4-G) — public surface.
 *
 * A closed prediction window gets asked about in conversation, and the answer reaches the
 * ledger. Architecture authority: `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` A-42.
 *
 * NOTE the split, which mirrors `samiksha/index.ts`'s own: `compose` and `classify` are
 * ISOMORPHIC (pure, safe to import from a client component); `select`, `capture` and `flag`
 * are server-side. A client component must import the isomorphic files DIRECTLY, never through
 * this index, which re-exports the server-only halves.
 */

export * from './flag'
export * from './compose'
export * from './classify'
export * from './select'
export * from './capture'
export * from './turn_hook'
