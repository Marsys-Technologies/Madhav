/**
 * CR register status allowlist — D-2 Lane V-1.
 *
 * Source of truth: BRIEF_D2.md §B0.1 ("known_gap reconciliation", resolved 2026-07-16
 * against POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md v1.5 + MARSYS_DEFECT_GAP_REGISTER
 * v2/v3). BIND_D-2.md (the Binder's own record) DOES NOT EXIST at the time this lane was
 * implemented — see the V-1 implementer's close notes. Absent that file, this module
 * treats BRIEF_D2.md §B0.1 as the authoritative bind-time CR-status snapshot, per this
 * lane's task instructions. A verifier/Binder pass should re-derive this list from the
 * live register at merge time and correct it if register state has moved since 2026-07-16.
 *
 * KNOWN CONFLICT (flag for the verifier, not silently resolved): BRIEF_D2.md §B0.1 lists
 * CR-55 as CLOSED ("cite as closed... do not re-plan"), but
 * POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md v1.5 §G row CR-55 itself is still marked
 * "OPEN — ELEVATED" in that file's body text as of this lane's read. This module follows
 * the brief's explicit instruction (never cite a CLOSED CR) and therefore does NOT emit
 * CR-55 as a known_gap anywhere in the registry — but the underlying defect
 * (`weakest_graha` factually wrong in the chart digest) is NOT independently re-verified
 * fixed here. Binder/verifier: reconcile and correct this file if the register's CR-55
 * row status has not actually changed.
 */

/** CRs the brief re-verified OPEN at register HEAD 2026-07-16 (BRIEF_D2.md §B0.1). */
export const OPEN_CRS = [
  'CR-9',
  'CR-14',
  'CR-39',
  'CR-15',
  'CR-16',
  'CR-24',
  'CR-25',
  'CR-26',
  'CR-64',
  'CR-28',
  'CR-30',
  'CR-36',
  'CR-44',
  'CR-61',
  'CR-62',
  'CR-73',
  'CR-76',
  'CR-77',
  'CR-78',
  'CR-84',
  'CR-85',
  'CR-86',
  'CR-90',
  // Not explicitly re-verified by BRIEF_D2.md §B0.1 (only CRs the brief's §F1 lane text
  // cites were reconciled there) but confirmed OPEN by direct inspection of
  // POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md v1.5 §G row text (2026-07-16 read,
  // no §F0/§B0 delta claims these shipped): the six §G.0 load-bearing-conclusion CRs plus
  // their immediate neighbors.
  'CR-54',
  'CR-56',
  'CR-59',
  'CR-63',
  'CR-65',
  'CR-66',
  'CR-67',
  'CR-68',
  'CR-69',
  'CR-37',
] as const;

/** LOGGED = inputs, not defects (BRIEF_D2.md §B0.1). Citable as known_gap context, never as a "fix this" CR. */
export const LOGGED_CRS = ['CR-27', 'CR-38', 'CR-71', 'CR-80'] as const;

/**
 * CRs explicitly CLOSED per BRIEF_D2.md §B0.1 — a known_gap MUST NEVER cite these.
 * (CR-55 is included here per the brief's instruction despite the register-body conflict
 * documented above; the registry completeness test below is what enforces "never CLOSED".)
 */
export const CLOSED_CRS = [
  'CR-7',
  'CR-51',
  'CR-55',
  'CR-57',
  'CR-58',
  'CR-60',
  'CR-72',
  'A7',
  'R-17',
  'R-47',
  'D15b-F2',
  'D15b-F3',
] as const;

export type CrId = (typeof OPEN_CRS)[number] | (typeof LOGGED_CRS)[number];

const CITABLE = new Set<string>([...OPEN_CRS, ...LOGGED_CRS]);
const CLOSED = new Set<string>(CLOSED_CRS);

/** True iff `crId` (e.g. "CR-56") is safe to cite as a primitive's `known_gap`. */
export function isCitableKnownGap(crId: string): boolean {
  return CITABLE.has(crId) && !CLOSED.has(crId);
}

/** True iff `crId` is a CLOSED CR that must never be cited as a known_gap. */
export function isClosedCr(crId: string): boolean {
  return CLOSED.has(crId);
}
