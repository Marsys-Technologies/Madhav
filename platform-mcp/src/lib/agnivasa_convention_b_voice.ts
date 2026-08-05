/**
 * agnivasa_convention_b_voice.ts — SHAD_DARSHANA_ADJUDICATION_17_AGNIVASA_MULTI_CONVENTION_
 * GRADING_v1_0.md: Agnivāsa Convention (B) (`agnivasa_muhurta_chintamani_arithmetic`, MC 1.36,
 * extracted in ADJUDICATION-16) served as a SECOND, INFORMATIONAL concurrence/dissent voice
 * alongside Convention (A) (`agnivasa_tithi_element_prithvi`, native-confirmed). Same shape as
 * `kp_school_voice.ts` (W3K Lane 2): a second voice can agree or disagree with the operative
 * reading without either being wrong on its own terms, disclosed rather than hidden.
 *
 * WHY THIS NEVER ENTERS GRADING (ADJUDICATION-17)
 * ------------------------------------------------
 * `compileConstraint`'s `residence` branch (this file) is structurally bound to Convention A's
 * pre-baked `bg_muhurta_lattice` element classification and a hardcoded favourable-element
 * list — there is no way to blend a second, vara-dependent convention into that filter without
 * either rebuilding the lattice or letting an unconfirmed convention silently participate in
 * the hard gate (ADJUDICATION-8 rail 2/3). So Convention B is computed here, informationally,
 * from the SAME lattice atoms convention A already read for the SAME date — never gating.
 *
 * B.10 / §N.5 discipline: this module invents nothing. `tithi_id`/`vara_id` are read directly
 * off the `bg_muhurta_lattice` atom's own `detail` (written by `bg_muhurta_lattice.py`, which
 * already carries both fields for every `agnivasa`-family row) — never re-derived from a date.
 */

export type AgnivasaConventionBElement = 'prithvi' | 'akasha' | 'patala'

const ELEMENT_BY_REMAINDER: Record<number, AgnivasaConventionBElement> = {
  0: 'prithvi',
  1: 'akasha',
  2: 'patala',
  3: 'prithvi',
}

/** MC 1.36 (ADJUDICATION-16): remainder = (tithi_id + 1 + vara_id) mod 4. */
export function computeConventionBElement(tithiId: number, varaId: number): AgnivasaConventionBElement {
  const remainder = ((tithiId + 1 + varaId) % 4 + 4) % 4
  return ELEMENT_BY_REMAINDER[remainder]!
}

export const CONVENTION_B_FAVOURABLE: ReadonlySet<AgnivasaConventionBElement> = new Set(['prithvi'])

export type AgnivasaAgreement = 'agrees' | 'diverges' | 'not_comparable'

export interface AgnivasaConventionBVoice {
  /** Always 'muhurta_chintamani' — the school/source tag a reader routes on. */
  school: 'muhurta_chintamani'
  school_label: string
  state: 'computed' | 'honest_empty'
  /** Populated iff `state === 'honest_empty'`. */
  empty_reason: string | null
  tithi_id: number | null
  vara_id: number | null
  element: AgnivasaConventionBElement | null
  favourable: boolean | null
  /** Convention A's element for the SAME lattice atom, echoed for comparison. */
  convention_a_element: string | null
  convention_a_favourable: boolean | null
  agreement: AgnivasaAgreement
  /** One deterministic sentence stating Convention B's own verdict. Template-composed. */
  claim: string
}

export const AGNIVASA_CONVENTION_B_LABEL =
  'Muhūrta-Cintāmaṇi Agnivāsa arithmetic (MC 1.36) — second, non-native-confirmed convention'

/**
 * Computes Convention B's voice for one `bg_muhurta_lattice` `agnivasa` atom — the SAME atom
 * `compileConstraint`'s `residence` branch already resolved Convention A against.
 *
 * `latticeDetail` is the atom's raw `detail` JSON (loosely typed, matching this file's own
 * existing `(r.detail as {...})` cast convention elsewhere in `kala_sky_pattern.ts`).
 * `conventionBOperative` is whether a `computed` (not `declared_not_computed`) Convention B row
 * exists in the chart's `kala_paddhati_profile` — this voice reports `honest_empty` when it
 * does not, rather than computing anyway (a convention not yet flipped `computed` is not yet
 * authorized to be served, even informationally — ADJUDICATION-8 rail 2's spirit).
 */
export function computeAgnivasaConventionBVoice(
  latticeDetail: unknown,
  conventionBOperative: boolean,
): AgnivasaConventionBVoice {
  if (!conventionBOperative) {
    return {
      school: 'muhurta_chintamani',
      school_label: AGNIVASA_CONVENTION_B_LABEL,
      state: 'honest_empty',
      empty_reason:
        'agnivasa_muhurta_chintamani_arithmetic is not convention_status=computed in this ' +
        "chart's kala_paddhati_profile (paddhati_v02 not applied, or superseded).",
      tithi_id: null,
      vara_id: null,
      element: null,
      favourable: null,
      convention_a_element: null,
      convention_a_favourable: null,
      agreement: 'not_comparable',
      claim: 'Convention (B) is not computed for this chart — no second voice available.',
    }
  }

  const detail = (latticeDetail ?? null) as { tithi_id?: unknown; vara_id?: unknown; element?: unknown } | null
  const tithiId = typeof detail?.tithi_id === 'number' ? detail.tithi_id : null
  const varaId = typeof detail?.vara_id === 'number' ? detail.vara_id : null
  const conventionAElement =
    typeof detail?.element === 'string' ? detail.element.toLowerCase() : null

  if (tithiId === null || varaId === null) {
    return {
      school: 'muhurta_chintamani',
      school_label: AGNIVASA_CONVENTION_B_LABEL,
      state: 'honest_empty',
      empty_reason:
        'the bg_muhurta_lattice agnivasa atom carried no numeric tithi_id/vara_id in its ' +
        'detail — cannot compute Convention (B) without re-deriving from a date, which this ' +
        'module never does.',
      tithi_id: null,
      vara_id: null,
      element: null,
      favourable: null,
      convention_a_element: conventionAElement,
      convention_a_favourable: conventionAElement === 'prithvi',
      agreement: 'not_comparable',
      claim: 'Convention (B) could not be computed for this date — required fields missing.',
    }
  }

  const element = computeConventionBElement(tithiId, varaId)
  const favourable = CONVENTION_B_FAVOURABLE.has(element)
  const conventionAFavourable = conventionAElement === 'prithvi'

  const agreement: AgnivasaAgreement =
    conventionAElement === null ? 'not_comparable' : favourable === conventionAFavourable ? 'agrees' : 'diverges'

  const claim =
    agreement === 'not_comparable'
      ? `Convention (B) reads this date as ${element} (${favourable ? 'favourable' : 'unfavourable'}) — Convention (A)'s own element was not available for comparison.`
      : agreement === 'agrees'
        ? `Convention (B) reads this date as ${element} (${favourable ? 'favourable' : 'unfavourable'}), agreeing with Convention (A)'s ${conventionAElement} reading.`
        : `Convention (B) reads this date as ${element} (${favourable ? 'favourable' : 'unfavourable'}), DIVERGING from Convention (A)'s ${conventionAElement} reading (${conventionAFavourable ? 'favourable' : 'unfavourable'}) — Convention (A) remains the native-confirmed, operative reading; this is disclosed, not determinative.`

  return {
    school: 'muhurta_chintamani',
    school_label: AGNIVASA_CONVENTION_B_LABEL,
    state: 'computed',
    empty_reason: null,
    tithi_id: tithiId,
    vara_id: varaId,
    element,
    favourable,
    convention_a_element: conventionAElement,
    convention_a_favourable: conventionAElement === null ? null : conventionAFavourable,
    agreement,
    claim,
  }
}
