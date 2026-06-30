/**
 * prompts/index.ts — MCP guided-reading prompt registration for MARSYS-JIS.
 *
 * Registers 3 astrologically-teaching guided prompts that Claude receives
 * at session attach. These prompts encode the Whole-Chart-Read Protocol
 * (B.11) and classical Jyotish reading discipline directly into the
 * conversation scaffolding — not as soft instructions, but as executable
 * workflow templates the host can invoke.
 *
 * Prompts registered:
 *   - orient_chart        — full chart orientation before any domain work
 *   - assess_domain       — B.11-compliant domain drill with classical citations
 *   - find_active_yogas   — dasha-gated yoga activation with teaching commentary
 *
 * SDK: server.prompt(name, description, argsSchema, callback)
 * Return shape: { messages: [{ role: 'user'|'assistant', content: { type: 'text', text } }] }
 *
 * R5 — Richness Layer (2026-06-30)
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

export function registerPrompts(server: McpServer): void {

  // ── 1. orient_chart ─────────────────────────────────────────────────────────
  //
  // Encodes the mandatory pre-reading orientation step per B.11.
  // In classical Jyotish, an acharya begins every chart reading by assessing
  // the Lagna lord (the chart's master karaka), the Moon (manas karaka — mind
  // and emotional temperament), and the dominant pattern before touching any
  // domain. This prompt makes that discipline executable.
  server.prompt(
    'orient_chart',
    'Orient to a chart before any domain analysis. Encodes the B.11 Whole-Chart-Read Protocol: Lagna lord condition, Moon nakshatra character, and the 3 dominant cross-domain themes from the L2 synthesis layer. Call this first — every domain reading presupposes this holistic foundation.',
    {
      chart_id: z.string().uuid().describe(
        'UUID of the chart to orient. Required — no default chart.'
      ),
      ayanamsha_id: z.string().optional().describe(
        "Ayanamsha for signal computation (default: 'LAHIRI'). Parashara tradition uses Lahiri."
      ),
    },
    async ({ chart_id, ayanamsha_id }) => ({
      messages: [
        {
          role: 'user' as const,
          content: {
            type: 'text' as const,
            text: [
              `Orient me to chart ${chart_id} before any domain analysis.`,
              '',
              'Step 1 — Call get_chart_orientation with:',
              `  chart_id: "${chart_id}"`,
              `  ayanamsha_id: "${ayanamsha_id ?? 'LAHIRI'}"`,
              '  response_format: "summary"',
              '',
              'Step 2 — From the orientation result, explain in teaching language:',
              '  (a) The Lagna (Ascendant) sign and its lord — which planet rules the chart, where it sits, and what that means for the native\'s primary life direction (dharma karaka).',
              '  (b) The Moon sign and nakshatra — the manas karaka, governing emotional temperament, habitual mind, and the quality of consciousness the native brings to all experiences.',
              '  (c) The 3 dominant MSR themes by computed_salience — what the chart most strongly emphasizes across domains.',
              '',
              'Step 3 — Note any immediate cross-domain tensions (e.g. Lagna lord in a dushtana, Moon in a challenging nakshatra pada, or a powerful yoga in the 12th).',
              '',
              'This orientation is the mandatory floor for all subsequent domain readings. Do not proceed to any domain analysis without completing it.',
            ].join('\n'),
          },
        },
      ],
    })
  )

  // ── 2. assess_domain ────────────────────────────────────────────────────────
  //
  // A B.11-compliant domain drill. Classical Jyotish teaches that no domain
  // (bhava) can be read in isolation — a career reading without knowing the
  // Moon's state, the 10th lord's dispositor chain, and the current dasha
  // lord's nature is incomplete. This prompt enforces that methodology by
  // always prefacing the domain drill with a holistic orientation.
  server.prompt(
    'assess_domain',
    'Assess a specific life domain (career, relationship, health, wealth, spirituality, character) for a chart. Enforces the B.11 orient-before-domain discipline: orientation runs first, then the domain drill, then classical citations contextualize the signals. Teaching format explains the 3 most important signals with their Jyotish rationale.',
    {
      chart_id: z.string().uuid().describe(
        'UUID of the chart. Required.'
      ),
      domain: z.string().describe(
        'Life domain to assess. Classical Jyotish domains: career (10th/6th/2nd), relationship (7th/5th/2nd), health (1st/6th/8th), wealth (2nd/11th/5th/9th), spirituality (9th/12th/5th), character (1st/Lagna lord/Moon).'
      ),
      ayanamsha_id: z.string().optional().describe(
        "Ayanamsha (default: 'LAHIRI')."
      ),
    },
    async ({ chart_id, domain, ayanamsha_id }) => ({
      messages: [
        {
          role: 'user' as const,
          content: {
            type: 'text' as const,
            text: [
              `Assess the "${domain}" domain for chart ${chart_id}.`,
              '',
              'Step 1 — Orientation (mandatory B.11 floor):',
              `  Call get_chart_orientation(chart_id="${chart_id}", ayanamsha_id="${ayanamsha_id ?? 'LAHIRI'}", response_format="digest")`,
              '  This ensures the domain reading is grounded in the full chart context.',
              '',
              `Step 2 — Domain drill:`,
              `  Call get_domain_reading(chart_id="${chart_id}", domain="${domain}", ayanamsha_id="${ayanamsha_id ?? 'LAHIRI'}")`,
              '',
              'Step 3 — Classical citations:',
              `  Call get_classical_citation(query="${domain} bhava lord placement", limit=3)`,
              '  These locate the classical śāstric basis for the signals surfaced in Step 2.',
              '',
              'Step 4 — Teaching synthesis (3 most important signals):',
              `  For each of the top 3 signals by computed_salience in the "${domain}" domain:`,
              '    (a) State the signal in plain language (what planet, what house, what condition).',
              '    (b) Explain the classical Jyotish rationale — which śāstra rule is operating, which bhava karaka is involved.',
              '    (c) State the domain implication — how this manifests in lived experience for this native.',
              '    (d) If a classical citation applies, quote the relevant verse/sūtra.',
              '',
              'Maintain the layer discipline: L1 facts (planet positions) → L2 signals (patterns) → L3 temporal activation → L4/L5 projections. Do not collapse layers.',
            ].join('\n'),
          },
        },
      ],
    })
  )

  // ── 3. find_active_yogas ────────────────────────────────────────────────────
  //
  // Yoga activation is dasha-gated in classical Jyotish: a Rajayoga formed by
  // 9th and 10th lords conjoined gives results primarily when those lords run
  // their dasha/antardasha. This prompt enforces that temporal gate — surfacing
  // which yogas are structurally present AND currently active in the native's
  // dasha sequence, which is the clinically meaningful question.
  server.prompt(
    'find_active_yogas',
    'Find which classical Jyotish yogas (planetary combinations) are structurally present in the chart AND actively firing in the current or near-future dasha period. Classical teaching: a yoga gives results when its constituent lords run their period. This prompt combines the temporal gate (L3 Kāla activation) with the structural yoga inventory (L2 Bodha signals) to answer the question an acharya actually asks.',
    {
      chart_id: z.string().uuid().describe(
        'UUID of the chart. Required.'
      ),
      ayanamsha_id: z.string().optional().describe(
        "Ayanamsha (default: 'LAHIRI')."
      ),
      horizon_months: z.number().int().min(1).max(60).optional().describe(
        'How many months forward to check for yoga activation (default: 24).'
      ),
    },
    async ({ chart_id, ayanamsha_id, horizon_months }) => {
      const months = horizon_months ?? 24
      const today = new Date().toISOString().slice(0, 10)
      const future = new Date(Date.now() + months * 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
      return {
        messages: [
          {
            role: 'user' as const,
            content: {
              type: 'text' as const,
              text: [
                `Find which yogas are actively firing for chart ${chart_id} over the next ${months} months.`,
                '',
                'Step 1 — Orientation (B.11 floor):',
                `  Call get_chart_orientation(chart_id="${chart_id}", ayanamsha_id="${ayanamsha_id ?? 'LAHIRI'}", response_format="digest")`,
                '',
                'Step 2 — Structural yoga inventory:',
                `  Call get_signals(chart_id="${chart_id}", ayanamsha_id="${ayanamsha_id ?? 'LAHIRI'}", min_salience=0.6, limit=30)`,
                '  Filter for signals whose signal_type contains "yoga" or whose tag_labels mention Raja, Dhana, Viparita, Pancha Mahapurusha, or other yoga categories.',
                '',
                'Step 3 — Temporal activation (dasha gate):',
                `  Call get_temporal_windows(chart_id="${chart_id}", ayanamsha_id="${ayanamsha_id ?? 'LAHIRI'}", date_from="${today}", date_to="${future}", include_convergence=true)`,
                '  This surfaces which planetary lords are running their dasha/antardasha in the window.',
                '',
                'Step 4 — Cross-reference: a yoga is "actively firing" when:',
                '  (a) Its constituent lords are in the current or upcoming dasha/antardasha sequence, OR',
                '  (b) A transit of the yoga lord over a natal activation point falls in the window.',
                '  Yogas that are structurally strong but temporally dormant are "pending" — note them separately.',
                '',
                'Step 5 — Teaching commentary on the 3 most significant active yogas:',
                '  (a) Name the yoga (e.g. Gajakesari, Neechabhanga Raja, Viparita Raja).',
                '  (b) Explain the classical rule that forms it (which planets, which houses/signs).',
                '  (c) State the temporal activation: which dasha lord triggers it and when the period runs.',
                '  (d) State the expected life-domain result in plain language.',
                `  (e) Call get_classical_citation(query="<yoga_name> results", limit=2) for each yoga to anchor the teaching in śāstra.`,
                '',
                'Yogas without temporal activation are structurally present but not ripe — do not conflate them with active ones.',
              ].join('\n'),
            },
          },
        ],
      }
    }
  )
}
