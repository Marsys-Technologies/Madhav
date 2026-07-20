/**
 * register_block.ts — RE-EXPORT SHIM (2026-07-20, W3 integration)
 * =================================================================
 * The register block / reading_contract / signal_reader_text machinery now lives
 * INLINE inside `envelope.ts` — see that file's "W3-L3 One Envelope register block"
 * section. It moved because `envelope.ts` is mechanically mirrored into `platform-mcp`
 * via `generate_envelope.ts`, which enforces a hard zero-import constraint on the file
 * (process-boundary self-containment, design §19) — this module's own cross-import of
 * `EpistemicGrade`/`DrillPointerType`/`PactStage` FROM `envelope.ts` tripped that guard
 * the moment `envelope.ts` imported back from here.
 *
 * This file is kept as a thin re-export so existing imports of `./register_block`
 * (tests, `registry/types.ts`) don't need to change.
 */
export {
  buildRegisterBlock,
  buildReadingContract,
  collectSignalReaderText,
  SIGNAL_CLASS_LABELS,
  SIGNAL_READER_TEXT,
  SIGNAL_CLASS_COUNT,
  EPISTEMIC_GRADE_LABELS,
  PACT_STAGE_LABELS,
  POINTER_TYPE_LABELS,
  DRILL_URI_FAMILY_LABELS,
  drillUriFamily,
  type RegisterEntry,
  type RegisterTokenKind,
  type BuildRegisterBlockParams,
  type BuildReadingContractParams,
} from './envelope'
