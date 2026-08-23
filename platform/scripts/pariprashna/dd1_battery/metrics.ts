/**
 * dd1_battery/metrics.ts — the DD-1 feel-proxy battery's metric registry.
 *
 * ══════════════════════════════════════════════════════════════════════════
 *  WHAT THIS BATTERY IS, AND WHAT IT IS NOT  (read before touching anything)
 * ══════════════════════════════════════════════════════════════════════════
 * This is the **DD-1 automated feel-proxy battery**. It is an explicitly
 * labelled MACHINE PROXY for the human question "does the default surface feel
 * right". It is **NOT AC-15** and it never becomes AC-15.
 *
 * AC-15 is the native's own week of use. Per the overnight charter §0 ruling 11
 * / §10.1, AC-15 was converted from a BLOCKING gate into an ASYNC signal and
 * this battery substitutes for that human seam **TONIGHT ONLY**. The swarm
 * records no AC-15 PASS, ever. A PASS from this battery means exactly one
 * thing: "the enumerated machine metrics below met their own stated thresholds
 * on the target surface". It means nothing about how a reading felt to a human.
 *
 * Every artifact this battery emits carries `PROXY_LABEL` (below) verbatim.
 *
 * ── WHERE THE METRIC DEFINITIONS COME FROM ────────────────────────────────
 * M1/M2/M3/M4/M5/M6/M8/M9 are NOT invented here. Each `definition` and
 * `threshold` string below is quoted VERBATIM from the project's own design
 * plan, `00_ARCHITECTURE/PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md` §1.6
 * (the success-metric table, lines 127-135) with its §12 acceptance-criteria
 * restatement (AC-1..AC-7) cited where it sharpens the operationalization.
 * `sourceRef` names the exact line. Nothing here was re-defined to something
 * easier to measure; where the project's definition needs a surface this
 * battery cannot reach, the metric is reported NOT-IMPLEMENTED rather than
 * quietly narrowed (CLAUDE.md §N.8).
 *
 * ── THE §N.8 CONTRACT, PER METRIC ─────────────────────────────────────────
 * `falsifier` answers, for each metric, the Earned-Signal question: *what code
 * path would have to run — and fail — for this signal to correctly read false?*
 * A metric whose `falsifier` reads "none" is `NOT_IMPLEMENTED`, not green. The
 * red-proof receipt (see `redProofKey` + `../red_proof.ts`) enforces this
 * STRUCTURALLY: a check with no banked red proof cannot report PASS.
 */

export type MetricStatus = 'PASS' | 'FAIL' | 'NOT_IMPLEMENTED'

export type MetricLane = 'prose' | 'browser' | 'fixture'

export interface MetricSpec {
  /** DD-1 / design-plan metric id (M1..M9) or a battery-local check id. */
  readonly id: string
  /** Human title. */
  readonly title: string
  /** VERBATIM from the design plan — never paraphrased. */
  readonly definition: string
  /** VERBATIM target from the design plan. */
  readonly threshold: string
  /** Exact provenance of the two strings above. */
  readonly sourceRef: string
  /** Which lane can actually measure it. */
  readonly lane: MetricLane
  /** True when DD-1's own enumeration names this metric. */
  readonly inDd1Enumeration: boolean
  /**
   * §N.8: the code path that would have to run and fail for this metric to
   * correctly read false. "none" ⇒ the metric is NOT_IMPLEMENTED by
   * construction.
   */
  readonly falsifier: string
  /** Key into the red-proof receipt. `null` ⇒ no red proof is possible ⇒ never PASS. */
  readonly redProofKey: string | null
}

/**
 * The label attached to EVERY result this battery emits — console, JSON, and
 * markdown alike. Charter §10.1 + §9 ("never present machine grading as the
 * native's judgment").
 */
export const PROXY_LABEL = [
  'MACHINE PROXY — NOT AC-15.',
  'This is the DD-1 automated feel-proxy battery: an explicitly-labelled machine',
  'substitute for the human "does the default surface feel right" seam, authorized',
  'for TONIGHT ONLY by native ruling 2026-08-22 (overnight charter §0 ruling 11 /',
  '§10.1). It is not AC-15 and it never becomes AC-15. AC-15 is the native\'s own',
  'week of use, recorded as waived-as-blocking with the verdict welcome',
  'asynchronously; the swarm records no AC-15 PASS. A PASS below means only that',
  'the enumerated machine metrics met their own stated thresholds on the named',
  'target. It is not a human verdict and must never be reported as one.',
].join('\n')

export const METRICS: readonly MetricSpec[] = [
  {
    id: 'M1',
    title: 'Settled-region layout shift during streaming',
    definition: 'Settled-region layout shift during streaming',
    threshold: 'CLS contribution = 0 above the volatile tail',
    sourceRef: 'PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md §1.6 line 127; AC-1 line 938',
    lane: 'browser',
    inDd1Enumeration: true,
    falsifier:
      'browser_lane.ts installs a rAF loop that re-reads every [data-committed="true"] ' +
      'block\'s bounding rect against the rect recorded at its commit; any |drift| > 0.5px ' +
      'increments settledShiftCount and the check reports FAIL. Red-proven by injecting a ' +
      'spacer <div> at the top of the settled region mid-stream (redProofKey m1_settled_shift).',
    redProofKey: 'm1_settled_shift',
  },
  {
    id: 'M2',
    title: 'Caret orphaning',
    definition:
      'Caret orphaning (caret rendered detached from last text node — under a table, ' +
      'after a block boundary, on its own line)',
    threshold: '0 occurrences across the streaming fixture corpus',
    sourceRef: 'PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md §1.6 line 128; AC-2 line 939',
    lane: 'browser',
    inDd1Enumeration: true,
    falsifier:
      'browser_lane.ts asserts, per animation frame while a tail is live, that [data-pp-caret] ' +
      'is the last inline child of the deepest last text-bearing node of the tail block (AC-2\'s ' +
      'own DOM invariant), cross-checked geometrically (caret top within one line-height of the ' +
      'tail\'s last text rect and to its right). A detached caret increments caretViolations ' +
      'and the check reports FAIL. Red-proven by forcing a block-break before the caret ' +
      '(redProofKey m2_caret_orphan).',
    redProofKey: 'm2_caret_orphan',
  },
  {
    id: 'M3',
    title: 'Time-to-first-visible-signal (submit → working region live)',
    definition: 'Time-to-first-visible-signal (submit → working region live)',
    threshold:
      '< 300 ms perceived (region mounts instantly on optimistic turn open; server phase ' +
      'label may arrive later)',
    sourceRef: 'PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md §1.6 line 129; AC-7 line 946',
    lane: 'browser',
    inDd1Enumeration: true,
    falsifier:
      'browser_lane.ts installs a MutationObserver BEFORE dispatching submit, stamps ' +
      'performance.now() at the click and again at the first mutation adding the working ' +
      'band (.pp-band), and reports FAIL when the delta >= 300ms. NOTE: this is a CLIENT-side ' +
      'quantity by the design plan\'s own definition (optimistic mount, not a server ack); it ' +
      'is deliberately NOT approximated from the SSE wire, which would measure a different ' +
      'thing. Red-proven by asserting the same probe against a target with the band selector ' +
      'renamed (redProofKey m3_ttfs).',
    redProofKey: 'm3_ttfs',
  },
  {
    id: 'M4',
    title: 'Time-to-first-token (submit → first answer prose)',
    definition: 'Time-to-first-token (submit → first answer prose)',
    threshold:
      'p50 < 4 s, p90 < 12 s for interpretive queries (dossier-routed turns will be slower)',
    sourceRef: 'PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md §1.6 line 130; AC-7 line 946',
    lane: 'prose',
    inDd1Enumeration: false, // charter §10.1's "latency ... thresholds"; not in DD-1's own list
    falsifier:
      'live_turn.ts stamps the POST and the arrival of the first block.delta carrying prose; ' +
      'the p50/p90 across the probe set are compared to 4s/12s and the check reports FAIL when ' +
      'either is exceeded. Red-proven by feeding the same percentile computation a synthetic ' +
      'transcript set with inflated first-delta timestamps (redProofKey m4_ttft).',
    redProofKey: 'm4_ttft',
  },
  {
    id: 'M5',
    title: 'Internal-ID leakage in reader prose',
    definition: 'Internal-ID leakage in reader prose (SIG.*, fact_id, asset names, "L2", table names)',
    threshold: '0 — enforced by server-side prose lint before the wire (§8.4)',
    sourceRef: 'PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md §1.6 line 131; AC-4 line 941',
    lane: 'prose',
    inDd1Enumeration: true,
    falsifier:
      'prose_checks.ts runs the project\'s OWN detector — lintReaderProse() from ' +
      'src/lib/pariprashna/citations/register_leak_lint.ts — over the DELIVERED reader prose of ' +
      'every probe turn and reports FAIL when leakCount > 0 or when the lint\'s `clean` output ' +
      'differs from the delivered text (i.e. something the pre-wire lint should have caught ' +
      'reached the reader). Red-proven against a corpus containing SIG.MSR.413, bo_laksana, ' +
      'bodha_signals, PLN.SUN and a bare register acronym (redProofKey m5_id_leak).',
    redProofKey: 'm5_id_leak',
  },
  {
    id: 'M6',
    title: 'Citation-chip transmutation',
    definition: 'Citation-chip transmutation (plain text later replaced by a badge)',
    threshold: '0 — chips render at final geometry on first paint',
    sourceRef: 'PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md §1.6 line 132; AC-3 line 940',
    lane: 'browser',
    inDd1Enumeration: true,
    falsifier:
      'Two independent halves. (a) WIRE half (prose lane, id M6-wire): the define-then-reference ' +
      'reducer law — every citation index referenced in committed prose has a citation.define ' +
      'event at an EARLIER wire seq, and no block_id is ever re-committed with different text; ' +
      'a violation reports FAIL. (b) DOM half (browser lane, this id): each committed block\'s ' +
      'outerHTML is snapshotted at commit and re-read every subsequent step, and each ' +
      '[data-testid="pp-citation-chip"] rect is recorded at first paint; any byte difference or ' +
      'rect change reports FAIL. Red-proven by mutating a committed block\'s innerHTML mid-stream ' +
      '(redProofKey m6_transmute) and by a wire corpus with a late define (m6_wire_late_define).',
    redProofKey: 'm6_transmute',
  },
  {
    id: 'M6-wire',
    title: 'Citation define-then-reference + committed-block immutability (wire half of M6)',
    definition:
      '`citation.define` may arrive *before* its chip\'s prose (define-then-reference), so chips ' +
      'render fully-formed on first paint — M6 … `block.commit` moves tail→blocks append-only',
    threshold: '0 late defines; 0 re-committed blocks with changed text',
    sourceRef: 'PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md §8.3 line 823 (reducer laws)',
    lane: 'prose',
    inDd1Enumeration: true, // the wire-observable half of DD-1's M6
    falsifier:
      'prose_checks.ts walks the ordered SSE event list per turn: for each citation index that ' +
      'appears in a committed block, it locates the citation.define carrying that index and ' +
      'reports FAIL if the define is absent or arrives at a LATER array position than the ' +
      'commit; and it reports FAIL if any block_id appears in two block.commit events with ' +
      'different text. Red-proven on a synthetic transcript with a deliberately late define ' +
      'and a re-committed block (redProofKey m6_wire_late_define).',
    redProofKey: 'm6_wire_late_define',
  },
  {
    id: 'M8',
    title: 'Mobile fixture pass',
    definition: 'Mobile fixture pass',
    threshold: '100% of §9 mobile scenarios (keyboard, tap-citation, sheet, reconnect)',
    sourceRef: 'PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md §1.6 line 134; AC-14 line 963',
    lane: 'browser',
    inDd1Enumeration: true,
    falsifier:
      'NOT-IMPLEMENTED AS DEFINED. The definition is "100% of §9 mobile scenarios (keyboard, ' +
      'tap-citation, sheet, reconnect)" and AC-14 requires physical iOS + Android. This battery ' +
      'implements the device-emulation substrate (real CDP Emulation.setDeviceMetricsOverride at ' +
      '390x844, isMobile/hasTouch, not a resized desktop viewport) and runs the whole browser ' +
      'lane inside it — reported as the separate check M8-emu — but it does NOT run all four §9 ' +
      'scenarios and does not run on physical devices. Reporting M8 PASS on that basis would be ' +
      'exactly the §N.8 defect this project has named three times, so M8 stays NOT_IMPLEMENTED.',
    redProofKey: null,
  },
  {
    id: 'M8-emu',
    title: 'Browser lane executed under real mobile device emulation (390x844)',
    definition:
      'Battery-local sub-check: the browser lane runs under real CDP device emulation at ' +
      '390x844 with isMobile + hasTouch, not a resized desktop viewport.',
    threshold: 'device metrics observed as 390x844, deviceScaleFactor > 1, "ontouchstart" in window',
    sourceRef: 'Overnight charter §10.1 dispatch requirement 3 (battery-local, NOT a design-plan metric)',
    lane: 'browser',
    inDd1Enumeration: false,
    falsifier:
      'browser_lane.ts reads back window.innerWidth/innerHeight, devicePixelRatio, ' +
      'navigator.maxTouchPoints and ("ontouchstart" in window) from inside the page AFTER ' +
      'emulation is applied, and reports FAIL if any disagrees with the requested profile. ' +
      'Red-proven by running the same read-back against a desktop context ' +
      '(redProofKey m8_device_emulation).',
    redProofKey: 'm8_device_emulation',
  },
  {
    id: 'M9',
    title: 'axe-core',
    definition: 'axe-core',
    threshold: '0 critical / 0 serious violations on every state fixture',
    sourceRef: 'PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md §1.6 line 135; AC-6 line 943',
    lane: 'browser',
    inDd1Enumeration: true,
    falsifier:
      'browser_lane.ts runs @axe-core/playwright against the LIVE surface at each observed ' +
      'state (idle / streaming / settled) and reports FAIL on any violation of impact ' +
      '"critical" or "serious". Red-proven by injecting an unlabelled <img> + a contrast-' +
      'violating node into the live DOM and observing axe report it (redProofKey m9_axe).',
    redProofKey: 'm9_axe',
  },
  {
    id: 'REG',
    title: 'Register / voice lint across the probe set',
    definition:
      'register/voice lint across a probe set of real readings on the synthetic chart ' +
      '(charter §10.1)',
    threshold:
      '0 voice_imperative_detected + 0 voice_pacing_order_violation + 0 voice_lint_internal_error ' +
      '(warn-level in the pipeline lint by design; FATAL in this battery — see prose_checks.ts REG_FATAL_CODES)',
    sourceRef: 'Overnight charter §10.1; detector = src/lib/pariprashna/voice/voice_lint.ts',
    lane: 'prose',
    inDd1Enumeration: true,
    falsifier:
      'prose_checks.ts runs the project\'s OWN lintVoiceProse() over each delivered reading in ' +
      'BOTH difficultFinding modes and reports FAIL on voice_imperative_detected, ' +
      'voice_pacing_order_violation, or voice_lint_internal_error. Those are level:"warn" inside ' +
      'voice_lint.ts (deliberately — the pipeline must not kill a turn over prose it cannot ' +
      'safely rewrite); a "fail only on level===error" rule would have been unfallible, since ' +
      'voice_lint.ts emits no error-level flag at all. Red-proven with a corpus containing a bare ' +
      'second-person remedy imperative ("You should wear a ruby...") and a severity claim with no ' +
      'preceding uncertainty frame (redProofKey reg_voice_lint).',
    redProofKey: 'reg_voice_lint',
  },
  {
    id: 'PLAIN',
    title: 'Reader-register plainness checks (§7.1 / §7.3)',
    definition:
      '§7.1 reader-register rules 1-5 and §7.3\'s explicit banned-phrasing list. NOTE ON ' +
      'PROVENANCE: the overnight charter §10.1 calls these "the §J plainness checks". §J of ' +
      'CLAUDE.md is the acharya-grade quality standard and enumerates NO plainness checks, and ' +
      'no artifact in this repo defines a "§J plainness" rubric. Rather than invent one, this ' +
      'check is scoped to the design plan\'s own enumerated, machine-checkable register rules ' +
      '(§7.1 rules 3 and 5, §7.3\'s banned list, §7.4\'s "a bare percentage never leads a ' +
      'sentence") and is labelled as such. See BATTERY_REPORT for the honest gap. UNCOVERED ' +
      'GAPS, disclosed at the same length as the §J provenance gap above rather than left ' +
      'implicit (F-1, PR #1501 refutation): §7.3\'s "any apology" clause is a class ban, not a ' +
      'literal-phrase ban — this check only matches the four NAMED §7.3 openers ("Unfortunately, ' +
      'no data…", "I couldn\'t find…", "The system was unable…", "It is not for us to know…") and ' +
      'has no detector for an apology of arbitrary phrasing ("I\'m sorry, but…", "My apologies…"). ' +
      '§7.1 rule 2 (Sanskrit glossed-on-first-use discipline) and rule 4 (verdict-first ordering) ' +
      'are not checked here at all — rule 2 needs semantic gloss-matching this battery does not ' +
      'attempt, and rule 4 (verdict-first) is the density-layering claim §N.6/judgment_query\'s own ' +
      'gate covers, not a prose-lint.',
    threshold:
      '0 banned §7.3 phrasings (the four named openers only — see the "uncovered gaps" note in ' +
      '`definition`, NOT the general "any apology" class); 0 occurrences of the literal "you ' +
      'will <verb>" construction (ONE surface form of §7.1 rule 3\'s oracular-second-person ban — ' +
      '"you shall…", "you\'ll…", "you\'re going to…" are NOT matched by this detector and are not ' +
      'claimed as covered); 0 hedging stacks',
    sourceRef: 'PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md §7.1 lines 656-660, §7.3 lines 671-676, §7.4 line 691',
    lane: 'prose',
    inDd1Enumeration: true,
    falsifier:
      'prose_checks.ts matches each delivered reading against (a) §7.3\'s literal banned openers ' +
      '("Unfortunately, no data", "I couldn\'t find", "The system was unable", "It is not for us ' +
      'to know") — NOT the full "any apology" class, (b) the literal "you will <verb>" surface ' +
      'form of §7.1 rule 3\'s oracular second-person ban — NOT "you shall"/"you\'ll"/"you\'re going ' +
      'to", (c) §7.1 rule 5\'s hedging stack (two or more of perhaps/possibly/maybe/it may be ' +
      'within one sentence), (d) §7.4\'s "a bare percentage never leads a sentence". Any hit ' +
      'reports FAIL. Red-proven against a corpus containing one instance of each (redProofKey ' +
      'plain_register).',
    redProofKey: 'plain_register',
  },
  {
    id: 'CITE',
    title: 'Citation integrity',
    definition:
      'citation integrity (charter §10.1): no unresolved sentinel residue reaches the reader, ' +
      'every defined citation carries a legal grade, and no malformed_sentinel flag fired.',
    threshold: '0 sentinel residues in delivered prose; 0 malformed_sentinel flags; all grades legal',
    sourceRef:
      'Overnight charter §10.1; grammar from src/lib/pariprashna/citations/grammar.ts, ' +
      'grades from citations/types.ts CitationGradeSchema',
    lane: 'prose',
    inDd1Enumeration: true,
    falsifier:
      'prose_checks.ts scans delivered prose for the project\'s OWN sentinel openers ' +
      '(grammar.ts OPENERS + the required "cite:" keyword) and reports FAIL on any residue; ' +
      'reports FAIL on any flag event with flag/code "malformed_sentinel"; and reports FAIL on ' +
      'any citation.define whose grade is outside the CitationGrade vocabulary. Red-proven with ' +
      'a corpus carrying a raw "⟦cite: PLN.SUN⟧" residue and an illegal grade ' +
      '(redProofKey cite_integrity).',
    redProofKey: 'cite_integrity',
  },
  {
    id: 'EDGE',
    title: 'Edge-state fixture suite',
    definition: 'plus the edge-state fixture suite (DD-1, verbatim)',
    threshold: 'the existing Paripraśna gate battery is green (desktop + mobile-390x844 projects)',
    sourceRef:
      'DD-1 in PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md §2; suite = ' +
      'platform/tests/pariprashna/gates/*.spec.ts via playwright.config.ts',
    lane: 'fixture',
    inDd1Enumeration: true,
    falsifier:
      'The battery shells out to the repo\'s OWN `npm run pariprashna:gates` and ' +
      '`pariprashna:gates:mobile` and reports FAIL on a non-zero exit. Those specs each carry ' +
      'their own in-file RED PROOF test (a seeded ?violate=<key> run asserted to be detected), ' +
      'and `npm run pariprashna:selftest` automates the literal red-then-green demonstration. ' +
      'IMPORTANT HONESTY NOTE, reported with every result: this suite runs against the ' +
      'standalone replay harness page (tests/pariprashna/harness/public/index.html), NOT the ' +
      'production React surface — it is a FIXTURE lane by construction and cannot substitute ' +
      'for the live-surface browser lane.',
    redProofKey: 'edge_fixture_suite',
  },
]

export function metricById(id: string): MetricSpec {
  const m = METRICS.find((x) => x.id === id)
  if (!m) throw new Error(`unknown metric id: ${id}`)
  return m
}
