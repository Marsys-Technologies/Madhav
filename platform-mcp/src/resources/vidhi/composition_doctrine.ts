/**
 * composition_doctrine.ts — Elevation Campaign v2.1 · Stream γ (PŪRṆA) · Lane I (EL-29 + EL-05).
 * The served-reading composition doctrine: the SHAPE a fully-composed reading takes, emitted as
 * a `reading_contract` structure and STRUCTURALLY GATED by Ω5's `synthesis_gate`.
 * ============================================================================================
 *
 * WHAT THIS IS (and is NOT)
 * -------------------------
 * This is a DOCTRINE + SCHEMA deliverable, not a generator. It defines the canonical composition
 * SEQUENCE a reading must follow once the whole territory is in the model, and a deterministic
 * function that renders that sequence as a structured `ReadingContract` a downstream consumer
 * (Lane E's verdict layer, future composed-reading surfaces) can target. It does NOT compose the
 * reading — the synthesis over the whole slice is, by design, the consumer's job (B.10: no
 * generative synthesis in the serving path).
 *
 * THE COMPOSITION SEQUENCE (EL-29, charter §γ.I / §0.4.E)
 * ------------------------------------------------------
 * A served reading is composed in ONE fixed order, each stage building on the last:
 *   1. gestalt/orientation   — the chart's own headline: who this chart IS before any question.
 *                              MANDATORY top-N laksana/gestalt volunteering (EL-05) lives here.
 *   2. promise               — what the chart PROMISES in the domain (D1 + varga dignity/yoga).
 *   3. evidence chains       — the grounded chains that support/deny the promise (dispositor
 *                              chains, argala webs, CGM subgraphs — Ω6 first-class structures).
 *   4. tensions + adjudication — the contradictions the chains expose, and how they are RESOLVED
 *                              (not merely listed — adjudicated, with the winning side reasoned).
 *   5. timing                — when the promise/tension activates (daśā × gochara convergence).
 *   6. guidance              — the intervention/remedy, ranked by leverage, disclosure-tiered.
 *
 * THE GATE IS STRUCTURAL, NOT HORTATORY (Ω5 red-team finding #12)
 * --------------------------------------------------------------
 * `buildReadingContract` returns the composition sequence ONLY when the dossier page it is handed
 * reads `synthesis_gate === 'OPEN'`. Before OPEN it returns a BLOCKED contract carrying NO stage
 * content — the same structural discipline dossier.ts enforces on `composition_scaffold`. A
 * consumer that composes from a BLOCKED contract is visibly composing from an empty structure,
 * not a plausibly-complete one. Prose in a payload cannot stop premature composition; a missing
 * structure can.
 *
 * EL-05 VOLUNTEERING — TOP-N GESTALT IS MANDATORY, SERVED UNPROMPTED
 * -----------------------------------------------------------------
 * The chart's own top-N laksana/gestalt findings are NOT an on-request extra — they are stage 1
 * of every composed reading, served even to a naive question that never asked for them. Ω5's
 * `dossier` composition_scaffold (which this lane may not edit) does not itself carry a gestalt-
 * volunteer section; this doctrine supplies it as stage 1, naming the LIVE gestalt serving tools
 * (`synth_chart_brief_get` — the mahā-brief / top laksana; `bodha_discoveries_get` — the Bimba
 * image layer; `bodha_chart_digest_get` — the whole-chart digest) as the drill handles the
 * consumer hydrates. This is the graha_portrait/dossier "call the already-built handlers" pattern
 * (B.10): the doctrine names WHERE the gestalt lives, it never re-computes it.
 */

/** The six ordered composition stages (EL-29). Stage order is the doctrine — never reordered. */
export const COMPOSITION_SEQUENCE = [
  'gestalt',
  'promise',
  'evidence_chains',
  'tensions_adjudication',
  'timing',
  'guidance',
] as const;

export type CompositionStageId = (typeof COMPOSITION_SEQUENCE)[number];

/**
 * EL-05: the mandatory top-N gestalt volunteering that opens stage 1 of EVERY composed reading.
 * `top_n` is the default served-unprompted count; the serving tools are the LIVE laksana/gestalt
 * (bo_laksana) + Bimba (bo_bimba) handles — drill pointers, never inlined computation (B.10).
 */
export const MANDATORY_GESTALT_VOLUNTEER = {
  top_n: 5,
  mandatory: true,
  served_unprompted: true,
  rationale:
    'The chart\'s own headline findings are volunteered to naive questions, not withheld until ' +
    'asked (EL-05). A reading that answers "how is my wealth?" without first orienting on who ' +
    'the chart IS has skipped the acharya\'s first move.',
  // LIVE serving tools (verified on the deployed connector) the consumer hydrates for the gestalt.
  serving_tools: [
    { tool: 'synth_chart_brief_get', role: 'laksana', note: 'the mahā-brief: top laksana findings, graded.' },
    { tool: 'bodha_discoveries_get', role: 'bimba', note: 'the Bimba (image/reflection) layer — cross-domain acharya observations.' },
    { tool: 'bodha_chart_digest_get', role: 'digest', note: 'the whole-chart gestalt digest (defining threads, headline, watch list).' },
  ],
} as const;

/** One rendered stage of the composition sequence. */
export interface CompositionStage {
  readonly stage: CompositionStageId;
  readonly order: number;
  /** What the consumer must produce at this stage — the doctrine instruction, not prose output. */
  readonly directive: string;
  /**
   * Stage 1 only: the mandatory EL-05 gestalt volunteer spec (top-N + serving tools). Present
   * ONLY on the `gestalt` stage; every other stage omits it.
   */
  readonly gestalt_volunteer?: typeof MANDATORY_GESTALT_VOLUNTEER;
}

/**
 * The `reading_contract` structure a fully-composed reading targets (EL-29). When BLOCKED, the
 * `stages` array is EMPTY by construction — the structural gate (no reading_contract content
 * until synthesis_gate: OPEN).
 */
export interface ReadingContract {
  readonly contract: 'reading_contract';
  readonly version: string;
  readonly synthesis_gate: 'BLOCKED' | 'OPEN';
  /** The ordered composition stages — EMPTY when BLOCKED (structural gate). */
  readonly stages: readonly CompositionStage[];
  /** The single instruction that stands in place of stages when BLOCKED. */
  readonly gate_note: string;
}

const READING_CONTRACT_VERSION = '1.0';

/** The per-stage doctrine directives (stable text; the composition doctrine itself). */
const STAGE_DIRECTIVES: Record<CompositionStageId, string> = {
  gestalt:
    'Open with the chart\'s own top-N laksana/gestalt findings (see gestalt_volunteer) — served ' +
    'unprompted. Orient on who this chart IS before touching the question (EL-05).',
  promise:
    'State what the chart PROMISES in the domain: D1 house/lord/karaka condition + varga (D9/D10/' +
    'D2/D11 as domain-relevant) dignity and yoga. Ground every clause in L1 fact_ids (B.3).',
  evidence_chains:
    'Lay the grounded chains that carry or deny the promise — dispositor chains, argala/virodha ' +
    'webs, CGM subgraphs (Ω6 first-class structures). Read the STRUCTURE, not just its atoms.',
  tensions_adjudication:
    'Surface the contradictions the chains expose and ADJUDICATE them — name the winning side and ' +
    'the reasoning. A tension merely listed is not adjudicated. Carry the cross-ayanamsha ' +
    'agreement (n/5) as a confidence discount where a finding is ayanamsha-fragile (EL-27).',
  timing:
    'Anchor activation in time: daśā × gochara convergence windows, with falsifiable window ' +
    'bounds. Timing is not optional garnish — an un-timed promise is not yet a prediction.',
  guidance:
    'Close with intervention/remedy ranked by leverage, disclosure-tiered. Guidance follows from ' +
    'the adjudicated tensions + timing — never a generic remedy list detached from the reading.',
};

/**
 * A minimal view of a dossier page — the fields this doctrine reads. Kept structural (not an
 * import of Ω5's `DossierPage`) so this module stays a stable consumer of the dossier API
 * surface, not a fork of its type. Ω5's `dossier.ts` is the authority; this reads its contract.
 */
export interface DossierPageView {
  readonly synthesis_gate: 'BLOCKED' | 'OPEN';
  readonly coverage_so_far?: { readonly pct?: number };
}

/**
 * Render the EL-29 composition doctrine as a `reading_contract`, STRUCTURALLY GATED by the
 * dossier page's `synthesis_gate` (EL-29 wired to Ω5's gate). Deterministic; non-generative.
 *
 * - synthesis_gate BLOCKED → `stages: []` (no composition content — the structural gate) + a
 *   gate_note telling the consumer to keep paging.
 * - synthesis_gate OPEN → the full six-stage sequence, stage 1 carrying the mandatory EL-05
 *   gestalt volunteer.
 */
export function buildReadingContract(page: DossierPageView): ReadingContract {
  if (page.synthesis_gate !== 'OPEN') {
    const pct = page.coverage_so_far?.pct;
    return {
      contract: 'reading_contract',
      version: READING_CONTRACT_VERSION,
      synthesis_gate: 'BLOCKED',
      stages: [], // STRUCTURAL GATE: no composition content until the gate is OPEN.
      gate_note:
        `synthesis_gate: BLOCKED${pct !== undefined ? ` (${pct}% accounted)` : ''} — the ` +
        'composition sequence is WITHHELD by construction. Page the dossier to 100% coverage ' +
        '(follow its cursor) before composing. Do not narrate parts; the deliverable is the ' +
        'synthesis over the whole.',
    };
  }

  const stages: CompositionStage[] = COMPOSITION_SEQUENCE.map((stage, i) => ({
    stage,
    order: i + 1,
    directive: STAGE_DIRECTIVES[stage],
    ...(stage === 'gestalt' ? { gestalt_volunteer: MANDATORY_GESTALT_VOLUNTEER } : {}),
  }));

  return {
    contract: 'reading_contract',
    version: READING_CONTRACT_VERSION,
    synthesis_gate: 'OPEN',
    stages,
    gate_note:
      'synthesis_gate: OPEN — the whole territory is accounted. Compose the reading in the six ' +
      'stages below, in order. The synthesis over the whole is the deliverable, not a narration ' +
      'of the parts.',
  };
}

/**
 * WORKED EXAMPLE (documentation — the shape a fully-composed reading targets). This is the OPEN
 * contract for any domain once its dossier slice reaches 100% accounting. Exported so tests and
 * downstream consumers have a canonical reference instance.
 */
export const READING_CONTRACT_EXAMPLE: ReadingContract = buildReadingContract({
  synthesis_gate: 'OPEN',
  coverage_so_far: { pct: 100 },
});
