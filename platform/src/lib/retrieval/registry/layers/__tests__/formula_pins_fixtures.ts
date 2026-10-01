/**
 * Shared fixtures for the formula-pin reader tests (formula_pins_readers.test.ts = behaviour,
 * formula_pins_tool_text.test.ts = served-text). Row VALUES are transcribed from production (native
 * chart 482012f1, lahiri_chitrapaksha, read as suvarna_reader 2026-10-02; INVESTIGATION_L1_DUPLICATE_
 * KEYS_v1_0.md section 2.4). Not a test file (no `.test.ts` suffix): vitest does not collect it.
 */
export type Row = Record<string, unknown>

const base = { fact_value_jsonb: null, unit: 'deg', verification_pass_status: 'two_pass_verified', citation_ref: 'c' }
const r = (o: Row): Row => ({ ...base, fact_value_num: null, fact_value_text: null, formula_id: null, ...o })

export const YOGI_ALT = r({ fact_id: '8ed0713d195cc400', fact_category: 'esoteric_point_yogi', fact_subject: 'YOGI_POINT', fact_key: 'longitude_sidereal', fact_value_num: 355.68451411812, formula_id: 'alt_96_40' })
export const YOGI_BPHS = r({ fact_id: '1ab369a4dca61235', fact_category: 'esoteric_point_yogi', fact_subject: 'YOGI_POINT', fact_key: 'longitude_sidereal', fact_value_num: 352.351180718121, formula_id: 'bphs_93_20' })
export const MR_BPHS = r({ fact_id: '8fca8f53f8e3adbd', fact_category: 'esoteric_point_mrityu', fact_subject: 'MRITYU_SPHUTA', fact_key: 'longitude_sidereal', fact_value_num: 96.4418410650319, formula_id: 'bphs_ch39' })
export const MR_SAR = r({ fact_id: '978b2ee3709d60d6', fact_category: 'esoteric_point_mrityu', fact_subject: 'MRITYU_SPHUTA', fact_key: 'longitude_sidereal', fact_value_num: 8.00640374694672, formula_id: 'saravali' })
export const MR_TAJ = r({ fact_id: 'ab797429df2f3476', fact_category: 'esoteric_point_mrityu', fact_subject: 'MRITYU_SPHUTA', fact_key: 'longitude_sidereal', fact_value_num: 247.80790552491, formula_id: 'tajik_aapamrityu' })
export const DK_PA = r({ fact_id: '0aa0001f8b1188e3', fact_category: 'karaka_chara_position', fact_subject: 'DARAKARAKA', fact_key: 'assigned_graha', fact_value_text: 'Mercury', formula_id: 'parashari_rahu_excluded' })
export const DK_KN = r({ fact_id: '130f96d334c42797', fact_category: 'karaka_chara_position', fact_subject: 'DARAKARAKA', fact_key: 'assigned_graha', fact_value_text: 'Jupiter', formula_id: 'kn_rao_rahu_included' })
export const SK_KN = r({ fact_id: 'sk-kn', fact_category: 'karaka_chara_position', fact_subject: 'STRIKARAKA', fact_key: 'assigned_graha', fact_value_text: 'Mercury', formula_id: 'kn_rao_rahu_included' })
export const PLAIN = r({ fact_id: 'plain-1', fact_category: 'graha_position', fact_subject: 'LAGNA', fact_key: 'nakshatra', fact_value_text: 'Ashwini', formula_id: null })
