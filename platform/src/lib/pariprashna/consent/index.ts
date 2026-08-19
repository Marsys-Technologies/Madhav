/**
 * Paripraśna — consent, subjects and exclusions (lane G1-B · NCD-9 · PPR-14).
 *
 * Everything exported here is inert until the `SUBJECT_CONSENT_ENFORCEMENT`
 * feature flag is ON (default OFF, `platform/src/lib/config/feature_flags.ts`):
 *   · `resolveSubjectConsent` short-circuits to `allow / enforcement_disabled`
 *     before touching the database;
 *   · every mutating entry point throws `ConsentFeatureDisabledError`.
 */

export * from './types'
export { CONSENT_FLAG, isConsentEnforcementEnabled } from './flag'
export { defaultConsentDb } from './db'
export {
  MINOR_AGE_THRESHOLD_YEARS,
  computeAgeYears,
  isMinorSubject,
  parseBirthDate,
  utcCalendarDate,
  type CalendarDate,
} from './minor_exclusion'
export {
  CONSENT_CHAIN_VERSION,
  canonicalJson,
  consentEntryHash,
  sha256Hex,
  tombstoneDigestSql,
  assertSafeTableIdentifier,
  verifyConsentChain,
  type ChainVerification,
  type ConsentEntryHashInput,
} from './hash_chain'
export {
  SUBJECT_SCOPE_PREFIXES,
  SUBJECT_SCOPE_EXTRA_TABLES,
  SUBJECT_SCOPE_DENY_TABLES,
  discoverSubjectScopedTables,
  isSubjectScopedTable,
} from './scope'
export {
  clearExclusion,
  listExcludedSubjects,
  listExclusionHistory,
  listOpenExclusions,
  registerExclusion,
  type RegisterExclusionInput,
} from './register'
export {
  loadChartSubject,
  loadConsentRow,
  resolveSubjectConsent,
  type ConsentAllow,
  type ConsentAllowReason,
  type ConsentRefusal,
  type ConsentRefusalReason,
  type ResolveSubjectConsentArgs,
  type SubjectConsentDecision,
} from './resolve'
export {
  appendConsentEvent,
  loadConsentChain,
  loadTombstones,
  withdrawConsentAndDelete,
  type TombstoneSummary,
  type WithdrawConsentArgs,
  type WithdrawalResult,
} from './withdrawal'
export {
  DELETION_SCOPE_DISPUTE_CLASS,
  listOpenDeletionScopeDisputes,
  openDeletionScopeDispute,
  renderDisagreementRegisterEntry,
  resolveDeletionScopeDispute,
  type DeletionScopeDisputeInput,
  type ResolveDisputeInput,
} from './dispute'
export {
  SUBJECT_EXPORT_MANIFEST_VERSION,
  buildSubjectExportManifest,
  serializeSubjectExportManifest,
  type BuildManifestArgs,
  type DataInventoryEntry,
  type ExportAudience,
  type SubjectExportManifest,
} from './export_manifest'
