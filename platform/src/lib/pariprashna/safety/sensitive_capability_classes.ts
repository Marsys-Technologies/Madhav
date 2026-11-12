/**
 * Mortality-domain capabilities. HS-1 point (a) excludes these from any plan
 * whose safety decision carries `hs1_date_of_death` or `hs4_mortality_window`
 * without a released aggregate-framing path.
 */
export const MORTALITY_CLASS_CAPABILITIES: readonly string[] = [
  'get_ayurdaya',
  'ganita_ayurdaya_get',
] as const

/**
 * Health/medical capabilities. HS-3 does not exclude these at plan time — a
 * health reading is permitted, it just cannot LEAVE the session unreviewed — so
 * this set is used by the `consult`-profile exclusion and by the classifier's
 * capability rules, not by the plan-time filter.
 */
export const MEDICAL_CLASS_CAPABILITIES: readonly string[] = [
  'assess_health',
  'get_medical_indications',
  'ganita_medical_get',
  'query_medical_mappings',
  'query_nakshatra_medical',
  'query_sign_medical',
  'ref_sign_medical_get',
] as const
