/**
 * kp_school_voice.ts — ṢAḌ-DARŚANA W3K Lane 2, gap G-5 of
 * `W3K_SUBSTRATE_INVENTORY_v1_0.md` §2: KP served as a school-tagged voice that can
 * CONCUR WITH or DISSENT FROM the Parāśarī reading of the same running window.
 * ==========================================================================
 *
 * WHY THIS IS A VOICE AND NOT A CLOCK
 * -----------------------------------
 * `vimshottari_kp`'s period windows are not an independent timing generator — inside the
 * field horizon they are boundary-identical to classical Vimśottarī's, which
 * `services/ka_kshetra/stage3_clocks.py`'s `kp_window_redundancy` detector MEASURES per
 * chart (and which `gochara_intensity/permission.py` already refuses to double-count one
 * layer down, for DR-14's plurality sum). KP's genuine independence is a JUDGMENT-METHOD
 * independence — `W3K_SUBSTRATE_INVENTORY_v1_0.md` §4 — and this module is where it is
 * spent: over the SAME window every other school is reading, KP asks its own question:
 *
 *     does the running daśā lord SIGNIFY this house, by the KP significator ladder?
 *
 * That question has no Parāśarī analogue, so its answer can agree or disagree with the
 * Parāśarī verdict without either being wrong on its own terms. Disagreement is served as
 * intelligence, never hidden (Elevation §0 vision property 4; `ArgumentDissent`).
 *
 * THE LADDER'S ONE METHODOLOGICAL EDGE, PRESERVED HERE
 * ---------------------------------------------------
 * KP ranks the STAR-LORD limbs above the occupancy/ownership limbs (A: planets tenanting
 * the star of an occupant; B: the occupants; C: planets tenanting the star of the owner;
 * D: the owner) — see `ga_writers/ga_kp_significators.py`. It is also indifferent to a
 * graha's natural benefic/malefic nature: an "afflicting" occupant of a house is, in KP,
 * that house's own agent. That indifference is exactly where KP and Parāśarī part company,
 * so `matchedLimb` is carried through to the served row rather than flattened into a
 * boolean — a reader must be able to see WHICH limb produced the verdict.
 *
 * B.10 / §N.5 / §N.8 DISCIPLINE
 * -----------------------------
 * This module computes NOTHING astrological. It reads `kp_house_significators` (L1, written
 * by `ga_nakshatra`'s additive KP emitter) and the running `vimshottari_kp` rows (L1,
 * `chart_dashas`) and performs a set intersection. When the ladder is absent it returns
 * `state: 'honest_empty'` naming the missing fact_category — it never falls back to
 * re-deriving significators at serve time, and it never reports "no dissent" when what it
 * actually has is "no data" (§N.8: a signal with no detector behind it is null, not green).
 */

/** The four classical KP significator limbs, strongest first. */
export type KpLimb = 'a' | 'b' | 'c' | 'd'

export const KP_LIMB_ORDER: readonly KpLimb[] = ['a', 'b', 'c', 'd'] as const

export const KP_LIMB_LABEL: Record<KpLimb, string> = {
  a: 'tenants the star of an occupant of the house',
  b: 'occupies the house (KP/Placidus cusp frame)',
  c: 'tenants the star of the house owner',
  d: 'owns the house',
}

/** A: star-of-occupants and B: occupants are KP's strong (agency) limbs; C/D are the
 *  supporting lordship limbs. The split is classical, not a tuning choice. */
const STRONG_LIMBS: ReadonlySet<KpLimb> = new Set<KpLimb>(['a', 'b'])

/** One house's KP significator ladder, as stored in `chart_facts.kp_house_significators`. */
export interface KpHouseLadder {
  house: number
  cusp_owner: string | null
  level_a: string[]
  level_b: string[]
  level_c: string[]
  level_d: string[]
  ranked: string[]
  /** The `chart_facts.fact_id`s the limb rows above were read from — the derivation
   *  ledger for every claim this voice makes (B.3 / §N.5: an L2+ claim REFERENCES the L1
   *  fact it consumes). Empty only if the source rows genuinely carried no fact_id. */
  fact_ids: string[]
}

/** One running `vimshottari_kp` period at some level. */
export interface KpRunningPeriod {
  level_n: number
  lord_graha: string | null
  kp_sub_lord: string | null
  kp_sub_sub_lord: string | null
  start_date: string | null
  end_date: string | null
}

/** The Parāśarī side of the comparison, reduced from `pact_status`. */
export type ParasariStance = 'promised' | 'denied' | 'unknown'

/** The KP side. `signified` covers any limb; `strongest_limb` says which. */
export type KpStance = 'signified' | 'not_signified' | 'unknown'

export type KpAgreement = 'concurs' | 'dissents' | 'not_comparable'

export interface KpSignificatorMatch {
  /** The running lord that matched. */
  lord: string
  /** Which running level it was running at (`MD`/`AD`/`PD`/`SD`, or `KP_SUB`/`KP_SUB_SUB`). */
  running_level: string
  /** The strongest limb of the ladder this lord appears at. */
  limb: KpLimb
  limb_meaning: string
  strong: boolean
}

export interface KpSchoolVoice {
  /** Always 'kp' — the school tag a reader routes on. */
  school: 'kp'
  school_label: string
  state: 'computed' | 'honest_empty'
  /** Populated iff `state === 'honest_empty'`; names the specific missing substrate. */
  empty_reason: string | null
  bhava: number | null
  kp_stance: KpStance
  parasari_stance: ParasariStance
  agreement: KpAgreement
  /** The KP ladder for this house, echoed so the verdict is auditable in place. */
  ladder: KpHouseLadder | null
  /** The running lord identities KP judged (deduped, in running-level order). */
  running_lords: Array<{ running_level: string; lord: string }>
  matches: KpSignificatorMatch[]
  strongest_limb: KpLimb | null
  /** KP is canonically read in the Krishnamurti ayanāṃśa; the PACT chain is read in the
   *  caller's. Both are reported — served as data, never silently reconciled (brief §W3K). */
  kp_ayanamsha_id: string
  chain_ayanamsha_id: string
  ayanamsha_divergence: boolean
  /** One deterministic sentence stating KP's own verdict. Template-composed, no LLM. */
  claim: string
}

export const KP_SCHOOL_LABEL =
  'KP sub-lord clock (Krishnamurti Paddhati significator ladder)'

/** `chart_dashas.level_n` → the running-level vocabulary this product already uses. */
const LEVEL_TEXT: Record<number, string> = { 1: 'MD', 2: 'AD', 3: 'PD', 4: 'SD', 5: 'PrD' }

/** `pact_status` → the Parāśarī stance. `chain_incomplete_infra` is deliberately `unknown`,
 *  not `denied`: an unreachable ephemeris sidecar is an infrastructure gap, and grading it
 *  as a classical denial would manufacture a dissent out of an outage. */
export function parasariStanceFromPactStatus(pactStatus: string): ParasariStance {
  switch (pactStatus) {
    case 'denied_at_promise':
    case 'denied_at_confirmation':
    case 'denied_at_activation':
      return 'denied'
    case 'chain_complete':
    case 'chain_pending_activation':
      return 'promised'
    default:
      return 'unknown'
  }
}

/** Parses `kp_house_significators` EAV rows (one `fact_subject = HOUSE_NN`) into a ladder.
 *  Returns null when the rows are absent or carry the writer's own
 *  `[EXTERNAL_COMPUTATION_REQUIRED]` marker — an honest gap the writer already declared,
 *  which this layer relays rather than reinterprets (B.10). */
export function parseKpHouseLadder(
  rows: Array<Record<string, unknown>>,
  house: number,
): KpHouseLadder | null {
  const subject = `HOUSE_${String(house).padStart(2, '0')}`
  const LADDER_KEYS = new Set([
    'cusp_owner', 'level_a_star_of_occupants', 'level_b_occupants',
    'level_c_star_of_owner', 'level_d_owner', 'ranked_significators',
  ])
  const byKey = new Map<string, string>()
  const factIds: string[] = []
  for (const r of rows) {
    if (String(r['fact_subject'] ?? '') !== subject) continue
    const key = String(r['fact_key'] ?? '')
    const text = r['fact_value_text']
    if (typeof text !== 'string') continue
    byKey.set(key, text)
    // Ledger only the rows the verdict actually consumes — never every row in the page
    // (the over-scoped-grounding defect `chart_facts_query` itself already corrected).
    const factId = r['fact_id']
    if (LADDER_KEYS.has(key) && typeof factId === 'string' && !factIds.includes(factId)) {
      factIds.push(factId)
    }
  }
  if (byKey.size === 0) return null

  const ranked = byKey.get('ranked_significators') ?? ''
  if (ranked.startsWith('[EXTERNAL_COMPUTATION_REQUIRED]')) return null

  const split = (v: string | undefined): string[] =>
    !v || v === 'none' ? [] : v.split(',').map((s) => s.trim()).filter(Boolean)

  return {
    house,
    cusp_owner: byKey.get('cusp_owner') ?? null,
    level_a: split(byKey.get('level_a_star_of_occupants')),
    level_b: split(byKey.get('level_b_occupants')),
    level_c: split(byKey.get('level_c_star_of_owner')),
    level_d: split(byKey.get('level_d_owner')),
    ranked: split(ranked),
    fact_ids: factIds,
  }
}

/** Reduces the running `vimshottari_kp` rows to the distinct (running_level, lord) pairs
 *  KP judges. Both the period's own `lord_graha` and its KP sub / sub-sub lord columns are
 *  taken: those columns are the KP-native labels the system_id exists to carry. */
export function runningKpLords(
  periods: KpRunningPeriod[],
): Array<{ running_level: string; lord: string }> {
  const seen = new Set<string>()
  const out: Array<{ running_level: string; lord: string }> = []
  const push = (running_level: string, lord: string | null | undefined) => {
    if (!lord) return
    const key = `${running_level}:${lord}`
    if (seen.has(key)) return
    seen.add(key)
    out.push({ running_level, lord })
  }
  const ordered = [...periods].sort((a, b) => a.level_n - b.level_n)
  for (const p of ordered) {
    push(LEVEL_TEXT[p.level_n] ?? `L${p.level_n}`, p.lord_graha)
    push('KP_SUB', p.kp_sub_lord)
    push('KP_SUB_SUB', p.kp_sub_sub_lord)
  }
  return out
}

function strongestLimbFor(ladder: KpHouseLadder, lord: string): KpLimb | null {
  const members: Record<KpLimb, string[]> = {
    a: ladder.level_a, b: ladder.level_b, c: ladder.level_c, d: ladder.level_d,
  }
  for (const limb of KP_LIMB_ORDER) {
    if (members[limb].includes(lord)) return limb
  }
  return null
}

export interface BuildKpSchoolVoiceParams {
  bhava: number
  ladder: KpHouseLadder | null
  periods: KpRunningPeriod[]
  pactStatus: string
  kpAyanamshaId: string
  chainAyanamshaId: string
  /** Set when the underlying fetch itself failed/returned nothing — carried verbatim into
   *  `empty_reason` so an outage never reads as an astrological finding. */
  substrateNote?: string | null
}

/**
 * The whole voice, computed deterministically. Returns `honest_empty` (never a fabricated
 * agreement) whenever either side of the comparison is genuinely unavailable.
 */
export function buildKpSchoolVoice(params: BuildKpSchoolVoiceParams): KpSchoolVoice {
  const {
    bhava, ladder, periods, pactStatus, kpAyanamshaId, chainAyanamshaId, substrateNote,
  } = params

  const base = {
    school: 'kp' as const,
    school_label: KP_SCHOOL_LABEL,
    bhava,
    ladder,
    kp_ayanamsha_id: kpAyanamshaId,
    chain_ayanamsha_id: chainAyanamshaId,
    ayanamsha_divergence: kpAyanamshaId !== chainAyanamshaId,
  }

  const parasari_stance = parasariStanceFromPactStatus(pactStatus)

  if (!ladder) {
    return {
      ...base,
      state: 'honest_empty',
      empty_reason:
        substrateNote ??
        `no \`kp_house_significators\` rows for HOUSE_${String(bhava).padStart(2, '0')} ` +
        `(ayanamsha ${kpAyanamshaId}). The KP significator ladder is written by ` +
        '`ga_nakshatra`\'s additive KP emitter (ga_writers/ga_kp_significators.py, W3K Lane 1); ' +
        'this chart has not been rebuilt since that emitter landed. No KP verdict is served — ' +
        'significators are NOT re-derived at serve time (§N.5), and an absent ladder is ' +
        'reported as absent, never as agreement (§N.8).',
      kp_stance: 'unknown',
      parasari_stance,
      agreement: 'not_comparable',
      running_lords: runningKpLords(periods),
      matches: [],
      strongest_limb: null,
      claim:
        'KP has no served verdict for this house on this chart yet — the significator ladder ' +
        'is not built. Reported as a gap, not as concurrence.',
    }
  }

  const running_lords = runningKpLords(periods)
  if (running_lords.length === 0) {
    return {
      ...base,
      state: 'honest_empty',
      empty_reason:
        substrateNote ??
        'no running `vimshottari_kp` period rows for this chart at the evaluated date — ' +
        'KP judges a RUNNING window, and there is none to judge.',
      kp_stance: 'unknown',
      parasari_stance,
      agreement: 'not_comparable',
      running_lords: [],
      matches: [],
      strongest_limb: null,
      claim:
        'KP has no running sub-period to judge at this date — reported as a gap, not as a verdict.',
    }
  }

  const matches: KpSignificatorMatch[] = []
  for (const { running_level, lord } of running_lords) {
    const limb = strongestLimbFor(ladder, lord)
    if (limb === null) continue
    matches.push({
      lord,
      running_level,
      limb,
      limb_meaning: KP_LIMB_LABEL[limb],
      strong: STRONG_LIMBS.has(limb),
    })
  }

  const strongest_limb =
    matches.length === 0
      ? null
      : KP_LIMB_ORDER.find((l) => matches.some((m) => m.limb === l)) ?? null

  const kp_stance: KpStance = matches.length > 0 ? 'signified' : 'not_signified'

  let agreement: KpAgreement
  if (parasari_stance === 'unknown') {
    agreement = 'not_comparable'
  } else if (
    (kp_stance === 'signified' && parasari_stance === 'promised') ||
    (kp_stance === 'not_signified' && parasari_stance === 'denied')
  ) {
    agreement = 'concurs'
  } else {
    agreement = 'dissents'
  }

  const claim = composeKpClaim({ bhava, ladder, matches, strongest_limb, kp_stance, agreement })

  return {
    ...base,
    state: 'computed',
    empty_reason: null,
    kp_stance,
    parasari_stance,
    agreement,
    running_lords,
    matches,
    strongest_limb,
    claim,
  }
}

/** Deterministic template prose — no LLM, no adjectives the data does not carry. */
export function composeKpClaim(p: {
  bhava: number
  ladder: KpHouseLadder
  matches: KpSignificatorMatch[]
  strongest_limb: KpLimb | null
  kp_stance: KpStance
  agreement: KpAgreement
}): string {
  const { bhava, ladder, matches, strongest_limb, kp_stance, agreement } = p
  const houseRef = `the ${bhava}th house`

  if (kp_stance === 'not_signified') {
    const sentence =
      `no running daśā lord signifies ${houseRef} on the KP ladder ` +
      `(ranked significators: ${ladder.ranked.join(', ') || 'none'}), so KP reads this window ` +
      `as not delivering ${houseRef}'s matters.`
    return agreement === 'dissents'
      ? `${sentence} This DISSENTS from the Parāśarī reading, which finds the matter promised and its window open.`
      : sentence
  }

  const strong = matches.filter((m) => m.strong)
  const lead = strong[0] ?? matches[0]!
  const lordList = [...new Set(matches.map((m) => m.lord))].join(', ')
  const levels = [...new Set(matches.map((m) => m.running_level))].join('/')

  const sentence =
    `the running ${levels} lord${matches.length > 1 ? 's' : ''} (${lordList}) signif${matches.length > 1 ? 'y' : 'ies'} ` +
    `${houseRef} on the KP ladder — ${lead.lord} ${KP_LIMB_LABEL[lead.limb]} ` +
    `(limb ${lead.limb.toUpperCase()}${strongest_limb && STRONG_LIMBS.has(strongest_limb) ? ', a strong agency limb' : ''}), ` +
    `so KP reads this window as actively delivering ${houseRef}'s matters.`

  return agreement === 'dissents'
    ? `${sentence} This DISSENTS from the Parāśarī reading, which halts the chain before delivery. ` +
      'The split is methodological and expected: KP treats a house\'s occupants as its own agents ' +
      'irrespective of natural benefic/malefic nature, where the Parāśarī checklist grades those ' +
      'same occupants as affliction.'
    : sentence
}
