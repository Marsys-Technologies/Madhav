/**
 * Paripraśna safety — FIXED RESPONSES (lane G1-A, HS-2 / HS-1 / HS-4).
 *
 * SAFETY_PRIVACY_TENANCY §2 HS-2: "Query classifier routes to a fixed, calm,
 * non-analytic response with support-resource framing; NO retrieval plan is
 * built (nothing to leak)."
 *
 * ── WHY THESE ARE CONSTANTS AND NOT PROMPTS ──────────────────────────────────
 * A generated response is a response an input can steer. The whole point of the
 * HS-2 path is that the turn produces text NO ONE composed at request time: no
 * model call, no retrieval, no chart data, no plan. These strings are the
 * output. They are exported as constants so a test can assert byte-for-byte
 * that what reached the wire is what is written here, and so that changing the
 * words is a reviewed diff rather than a prompt-tuning side effect.
 *
 * ── ON THE ABSENCE OF A HELPLINE NUMBER ──────────────────────────────────────
 * "Support-resource framing" is honored WITHOUT hard-coding a specific national
 * helpline number. A wrong or out-of-region number is worse than none, and this
 * instrument's subject population is not geographically bounded (the native is
 * in India; the cohort is undefined). The text therefore points at the
 * categories of help that exist everywhere rather than inventing a number this
 * lane cannot verify — the same "an honest null beats an invented judgment"
 * discipline §N.7 item 6 applies to prose. Provisioning a region-resolved
 * resource list is named as a real open item in the lane report, not silently
 * skipped.
 */

/**
 * The HS-2 response. Served verbatim; nothing is interpolated into it — no
 * name, no chart, no date, no model output.
 */
export const HS2_FIXED_RESPONSE = [
  'I’m not able to take this question into a chart reading.',
  '',
  'What you’ve raised is about your safety, and that sits outside what an astrological instrument should be asked to weigh in on — not because the question is unwelcome, but because a chart is the wrong thing to consult about it, and a reading here could do real harm.',
  '',
  'If you are in immediate danger, please contact your local emergency number now.',
  '',
  'If you are not in immediate danger but this is where your thoughts have been: please talk to a person — a doctor or mental-health professional, a crisis or suicide-prevention line in your country, or someone close to you who can stay with you today. Those conversations are the right ones for this, and they are available to you.',
  '',
  'I’ll be here for chart questions whenever you want to come back to them.',
].join('\n')

/**
 * The HS-1 withhold notice. Emitted when a reading is produced but a
 * date-of-death element was excluded from it, so the withholding is visible
 * ("Violation = withhold block + honest gap ribbon + audit row. NEVER silent.").
 */
export const HS1_WITHHOLD_NOTICE = [
  'One part of this question can’t be answered here: I don’t produce a date, year, or age of death for anyone — not as an estimate, not as a range, not indirectly.',
  '',
  'That is a fixed limit of this instrument rather than a judgment about your chart, and it holds for every chart and every reader. What the classical longevity material can honestly support is a discussion of period quality and of what the tradition treats as strengthening or straining, framed in aggregate rather than as an individual window — and nothing in this reading should be read as a substitute for the first kind of answer.',
].join('\n')

/**
 * The HS-4 aggregate-framing notice. Rides with any longevity-domain reading
 * that is released, stating the frame the material is being read under.
 */
export const HS4_AGGREGATE_FRAMING_NOTICE = [
  'A note on how the longevity material is being read: the classical āyurdāya calculations are treated here as aggregate, population-level statements about period quality — never as an individual mortality window.',
  '',
  'That framing is required, not stylistic: individualized mortality windows are disallowed in this instrument regardless of who is asking, and any longevity reading that leaves this session has been through an independent adversarial review and a separate sign-off before you see it.',
].join('\n')

/**
 * The HS-3 / HS-4 seal acknowledgment — what the reader sees INSTEAD of a
 * reading when the sign-off path is engaged.
 */
export const SEAL_PENDING_ACKNOWLEDGMENT = [
  'This question falls in a domain where a reading does not go out unreviewed.',
  '',
  'Health-crisis, mental-health, and longevity questions are held for two independent adversarial reviews and a separate human sign-off before any interpretation is released — a standing rule of this instrument, not a response to anything in your chart.',
  '',
  'Your question has been recorded and the review has been opened. Nothing has been discarded, and nothing partial has been shown to you in the meantime.',
].join('\n')

/**
 * The NCD-4 interstitial — the native-self deliberation pause that stands in
 * for the seal path on health-crisis / mental-health questions ONLY.
 */
export const NCD4_INTERSTITIAL_NOTICE = [
  'Before this reading: you’re asking about health, and this is the one place the instrument deliberately slows down.',
  '',
  'What follows is a reading of classical significations — not a diagnosis, not a prognosis, and not a reason to change or delay anything a clinician has told you. If this question is live for you right now rather than academic, the clinical conversation is the one that matters and this one is the footnote to it.',
].join('\n')

/**
 * The last-resort notice, emitted when the PRE-WIRE scan (not the classifier)
 * catches mortality-date phrasing in generated prose. Its presence in a turn is
 * evidence the two upstream controls both missed something.
 */
export const PREWIRE_REDACTION_NOTICE =
  'A phrase in this reading was withheld at the output stage: it read as a specific mortality date, which this instrument does not produce.'
