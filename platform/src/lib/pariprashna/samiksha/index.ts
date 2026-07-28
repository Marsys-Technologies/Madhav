/**
 * SAMĪKṢĀ prediction-ledger module — PB-3 lane L-1.
 *
 * Public surface for `brahma_mimamsa_prediction_ledger`: the schema/lifecycle single source
 * of truth, the legal-transition matrix, and the typed writer/reader DAL. The table name is
 * fixed by MEMO_PB-3_0; the authority map is LEDGER_MAP_PB-3.md.
 */

export * from './schema'
export * from './transitions'
export * from './writer'
export * from './reader'
// PB-3 lane L-2 — capture: detector → candidate → confirm.
// NOTE: `detector`, `kala_rekha`, and `lifecycle_label` are ISOMORPHIC (safe to
// import from a client component); `confirm` is `server-only` (DAL + stamp read).
// Client components import the isomorphic files DIRECTLY (never via this index,
// which re-exports the server-only DAL).
export * from './detector'
export * from './kala_rekha'
export * from './lifecycle_label'
export * from './confirm'
