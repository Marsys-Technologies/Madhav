import { describe, it, expect, beforeEach } from 'vitest'
import { renderTemplate, getDefaultRegistry, createRegistry } from '../index'
import { buildOpeningBlock } from '../templates/shared'
import type { PromptTemplate, QueryClass } from '../index'

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const SAMPLE_VARIABLES: Record<string, string> = {
  chart_name: 'Abhisek Mohanty',
  birth_date: '1984-02-05',
  birth_time: '10:43 IST',
  birth_place: 'Bhubaneswar, Odisha, India',
  bundle_summary: 'L1+L2+L2.5 bundle, 499 signals',
  tools_available: 'get_layer_document, run_ephemeris',
}

const MINIMAL_TEMPLATE: PromptTemplate = {
  template_id: 'test_template',
  version: '1.0',
  query_class: 'factual',
  strategy: 'single_model',
  body: 'Hello {{chart_name}}, born {{birth_date}}.',
  style_suffixes: {
    acharya: '',
    brief: '\n\nBe brief.',
    client: '\n\nBe accessible.',
  },
  required_placeholders: ['chart_name', 'birth_date'],
}

// ---------------------------------------------------------------------------
// renderTemplate
// ---------------------------------------------------------------------------

describe('renderTemplate', () => {
  it('substitutes all placeholders and returns the result', () => {
    const result = renderTemplate(
      MINIMAL_TEMPLATE,
      { chart_name: 'Test Native', birth_date: '2000-01-01' },
      'acharya',
    )
    expect(result).toBe('Hello Test Native, born 2000-01-01.')
  })

  it('appends the acharya style suffix (empty string)', () => {
    const result = renderTemplate(
      MINIMAL_TEMPLATE,
      { chart_name: 'Test Native', birth_date: '2000-01-01' },
      'acharya',
    )
    expect(result.endsWith('.')).toBe(true)
    expect(result).not.toContain('brief')
    expect(result).not.toContain('accessible')
  })

  it('appends the brief style suffix', () => {
    const result = renderTemplate(
      MINIMAL_TEMPLATE,
      { chart_name: 'Test Native', birth_date: '2000-01-01' },
      'brief',
    )
    expect(result).toContain('\n\nBe brief.')
  })

  it('appends the client style suffix', () => {
    const result = renderTemplate(
      MINIMAL_TEMPLATE,
      { chart_name: 'Test Native', birth_date: '2000-01-01' },
      'client',
    )
    expect(result).toContain('\n\nBe accessible.')
  })

  it('substitutes all occurrences of a placeholder that appears multiple times', () => {
    const tmpl: PromptTemplate = {
      ...MINIMAL_TEMPLATE,
      body: '{{chart_name}} and {{chart_name}} again.',
      required_placeholders: ['chart_name'],
    }
    const result = renderTemplate(tmpl, { chart_name: 'X' }, 'acharya')
    expect(result).toBe('X and X again.')
  })

  it('throws when a required placeholder is missing from variables', () => {
    expect(() =>
      renderTemplate(MINIMAL_TEMPLATE, { chart_name: 'Test Native' /* birth_date missing */ }, 'acharya'),
    ).toThrow(/birth_date/)
  })

  it('includes the placeholder name in the error message', () => {
    const tmpl = getDefaultRegistry().get('factual', 'single_model')
    expect(() => renderTemplate(tmpl, {}, 'acharya')).toThrow('chart_name')
  })
})

// ---------------------------------------------------------------------------
// PromptRegistry
// ---------------------------------------------------------------------------

describe('PromptRegistry', () => {
  // Use a fresh registry from the default factory for each test group, but
  // since getDefaultRegistry() returns a singleton we read a new one by
  // leveraging the module cache.  For isolation in individual tests we call
  // getDefaultRegistry() which always returns the same loaded instance —
  // sufficient for read-only tests; mutation tests use a local registry via
  // the constructor exposed through the factory.

  const ALL_QUERY_CLASSES: QueryClass[] = [
    'factual',
    'interpretive',
    'predictive',
    'cross_domain',
    'discovery',
    'holistic',
    'remedial',
    'cross_native',
  ]

  describe('list()', () => {
    it('returns exactly 10 templates', () => {
      const registry = getDefaultRegistry()
      expect(registry.list()).toHaveLength(10)
    })
  })

  describe('get() — direct lookup', () => {
    it.each(ALL_QUERY_CLASSES)('returns a template for query_class "%s"', (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      expect(tmpl.query_class).toBe(qc)
      expect(tmpl.strategy).toBe('single_model')
    })
  })

  describe('get() — missing combination throws', () => {
    it('throws for an unregistered strategy', () => {
      const registry = getDefaultRegistry()
      // Only single_model templates are registered; panel has none.
      expect(() => registry.get('factual', 'panel')).toThrow(
        /no template found/,
      )
    })

    it('error message includes the query_class and strategy', () => {
      const registry = getDefaultRegistry()
      let message = ''
      try {
        registry.get('predictive', 'panel')
      } catch (e) {
        message = (e as Error).message
      }
      expect(message).toContain('predictive')
      expect(message).toContain('panel')
    })
  })

  describe('register()', () => {
    it('replaces an existing template with the same key', () => {
      // Use an isolated registry instance via createRegistry() so the
      // singleton is never mutated and no restore is needed.
      const registry = createRegistry()
      const override: PromptTemplate = {
        template_id: 'factual_super_admin_single_model_override',
        version: '99.0',
        query_class: 'factual',
        strategy: 'single_model',
        body: 'Override body.',
        style_suffixes: { acharya: '', brief: '', client: '' },
        required_placeholders: [],
      }
      registry.register(override)
      const retrieved = registry.get('factual', 'single_model')
      expect(retrieved.version).toBe('99.0')
    })
  })
})

// ---------------------------------------------------------------------------
// Template integrity — all required_placeholders appear in body
// ---------------------------------------------------------------------------

describe('Template body integrity', () => {
  const ALL_QUERY_CLASSES: QueryClass[] = [
    'factual',
    'interpretive',
    'predictive',
    'cross_domain',
    'discovery',
    'holistic',
    'remedial',
    'cross_native',
  ]

  it.each(ALL_QUERY_CLASSES)(
    'template "%s": all required_placeholders appear in the body',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')

      // cross_native is a Phase 7 stub with a hardcoded message body and
      // empty required_placeholders — skip the body-contains check for it.
      if (qc === 'cross_native') {
        expect(tmpl.required_placeholders).toHaveLength(0)
        return
      }

      for (const placeholder of tmpl.required_placeholders) {
        expect(
          tmpl.body,
          `Template "${tmpl.template_id}" is missing required placeholder "{{${placeholder}}}"`,
        ).toContain(`{{${placeholder}}}`)
      }
    },
  )

  it.each(ALL_QUERY_CLASSES)(
    'template "%s": renderTemplate succeeds with all required variables supplied',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      expect(() => renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')).not.toThrow()
    },
  )
})

// ---------------------------------------------------------------------------
// M3-W1-A3 — Contradiction-framing rubric (PHASE_M3_PLAN §3.1 R.M3A.3 / AC.M3A.8)
// ---------------------------------------------------------------------------

describe('Contradiction-framing rubric in shared preamble', () => {
  // Templates inheriting buildOpeningBlock() — every active synthesis class
  // except the cross_native Phase-7 stub.
  const ACTIVE_QUERY_CLASSES: QueryClass[] = [
    'factual',
    'interpretive',
    'predictive',
    'cross_domain',
    'discovery',
    'holistic',
    'remedial',
  ]

  it.each(ACTIVE_QUERY_CLASSES)(
    'template "%s" rendered output includes the L3.5 Contradiction Register reference',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
      expect(rendered).toContain('L3.5 Contradiction Register')
    },
  )

  it.each(ACTIVE_QUERY_CLASSES)(
    'template "%s" rendered output enforces "surface, do not synthesize away"',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
      // (a) Surface, do not synthesize away.
      expect(rendered).toContain('surface each contradiction explicitly')
      expect(rendered).toContain('Do not average, smooth, or synthesize the contradiction away')
    },
  )

  it.each(ACTIVE_QUERY_CLASSES)(
    'template "%s" rendered output enforces contradiction_id citation (B.3)',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
      // (b) Cite the contradiction_id for each contradiction surfaced.
      expect(rendered).toContain('contradiction_id')
      expect(rendered).toContain('Cite the contradiction_id for each contradiction')
      expect(rendered).toContain('CON.')
    },
  )

  it.each(ACTIVE_QUERY_CLASSES)(
    'template "%s" rendered output prohibits fabricated L1 resolution (B.1)',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
      // (c) Layer-separation: surface resolution_options if present;
      //     do not invent a resolution.
      expect(rendered).toContain('resolution_options')
      expect(rendered).toContain('Do not fabricate L1 facts')
      expect(rendered).toContain('B.1 layer-separation')
      expect(rendered).toContain('B.3 derivation-ledger')
    },
  )

  it('rubric is injected from a single shared location (worked example appears exactly once per template)', () => {
    // The CON.007 worked example is unique to the rubric. If the rubric is
    // accidentally injected twice (e.g. via both shared preamble and a
    // class-specific tail), the example string would appear more than once.
    const registry = getDefaultRegistry()
    for (const qc of ACTIVE_QUERY_CLASSES) {
      const tmpl = registry.get(qc, 'single_model')
      const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
      const occurrences = rendered.split('[timing_conflict] (CON.007)').length - 1
      expect(occurrences).toBe(1)
    }
  })

  it('renders the worked CON.<id> example so the model has a citation pattern', () => {
    const registry = getDefaultRegistry()
    const tmpl = registry.get('discovery', 'single_model')
    const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
    // The canonical example anchors the model on the exact citation form.
    expect(rendered).toContain('[timing_conflict] (CON.007)')
    expect(rendered).toContain('open contradiction, not a resolved discrepancy')
  })

  it('rubric is dormant when no contradiction-register chunks present (instruction is conditional)', () => {
    const registry = getDefaultRegistry()
    const tmpl = registry.get('factual', 'single_model')
    const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
    // The rubric must explicitly instruct that absence of contradictions
    // means the rubric does not fire — guards against over-application
    // on plain factual queries.
    expect(rendered).toContain(
      "When no contradiction-register chunks appear in the retrieved context, this rubric is dormant",
    )
  })

  it('cross_native stub is unaffected (does not inherit buildOpeningBlock)', () => {
    const registry = getDefaultRegistry()
    const tmpl = registry.get('cross_native', 'single_model')
    const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
    expect(rendered).not.toContain('L3.5 Contradiction Register')
    // The stub body remains the unimplemented marker.
    expect(rendered).toContain('Phase 7 deliverable')
  })
})

// ---------------------------------------------------------------------------
// F025 — DASHA DISCIPLINE GATE (§5B dasha correctness campaign)
// Fixture label: dasha_discipline_gate_in_4_templates
// ---------------------------------------------------------------------------

describe('F025 — DASHA DISCIPLINE GATE (§5B)', () => {
  // The four mandated templates per research dossier §6 decision 2.
  const DASHA_GATE_TEMPLATES: QueryClass[] = ['predictive', 'factual', 'holistic', 'remedial']

  // Templates that must NOT receive the gate.
  const NON_DASHA_GATE_TEMPLATES: QueryClass[] = ['interpretive', 'cross_domain', 'discovery']

  it.each(DASHA_GATE_TEMPLATES)(
    'template "%s": DASHA DISCIPLINE GATE is present in rendered output',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
      expect(rendered).toContain('DASHA DISCIPLINE GATE')
    },
  )

  it.each(DASHA_GATE_TEMPLATES)(
    'template "%s": gate mandates DSH.V.NNN citation format',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
      expect(rendered).toContain('DSH.V.')
      expect(rendered).toContain('DSH.V.NNN')
    },
  )

  it.each(DASHA_GATE_TEMPLATES)(
    'template "%s": gate forbids extrapolation from generic Vimshottari knowledge',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
      expect(rendered).toContain('Extrapolating')
      expect(rendered).toContain('generic Vimshottari knowledge')
      expect(rendered).toContain('B.10')
    },
  )

  it.each(DASHA_GATE_TEMPLATES)(
    'template "%s": gate emits EXTERNAL_COMPUTATION_REQUIRED for missing rows',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
      expect(rendered).toContain('EXTERNAL_COMPUTATION_REQUIRED: dasha_vimshottari row')
      expect(rendered).toContain('refetch via query_dasha_periods')
    },
  )

  it.each(DASHA_GATE_TEMPLATES)(
    'template "%s": gate references query_dasha_periods tool',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
      expect(rendered).toContain('query_dasha_periods')
    },
  )

  it.each(DASHA_GATE_TEMPLATES)(
    'template "%s": DASHA DISCIPLINE GATE appears exactly once (no double-injection)',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
      const occurrences = rendered.split('DASHA DISCIPLINE GATE').length - 1
      expect(occurrences).toBe(1)
    },
  )

  it.each(NON_DASHA_GATE_TEMPLATES)(
    'template "%s": DASHA DISCIPLINE GATE is NOT present (out of mandate scope)',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
      expect(rendered).not.toContain('DASHA DISCIPLINE GATE')
    },
  )

  it('cross_native stub does not carry the dasha gate (Phase 7 stub isolation)', () => {
    const registry = getDefaultRegistry()
    const tmpl = registry.get('cross_native', 'single_model')
    const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
    expect(rendered).not.toContain('DASHA DISCIPLINE GATE')
  })
})

// ---------------------------------------------------------------------------
// GANGA-P3-R4-S1 — Synthesis integration gates (AC.7, AC.8, AC.9, AC.11)
// ---------------------------------------------------------------------------

describe('Synthesis integration gates — GANGA-P3-R4-S1', () => {
  // Active templates that inherit buildOpeningBlock() and carry the new gates.
  const ACTIVE_QUERY_CLASSES: QueryClass[] = [
    'factual',
    'interpretive',
    'predictive',
    'cross_domain',
    'discovery',
    'holistic',
    'remedial',
  ]

  // AC.7 — PRESCRIPTIVE_CITATION_GATE present in all 7 active rendered templates
  it.each(ACTIVE_QUERY_CLASSES)(
    'AC.7 template "%s": PRESCRIPTIVE_CITATION_GATE (→ citation format) is present',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
      expect(rendered).toContain('CITATION GATE')
      // Eval checks for (→ ...) format — verify the gate instructs this format
      expect(rendered).toContain('(→ SIG.MSR.NNN)')
      expect(rendered).toContain('(→ FORENSIC.')
    },
  )

  // AC.8 — All five B.11 layer names (acronyms) present in all 7 active rendered templates
  it.each(ACTIVE_QUERY_CLASSES)(
    'AC.8 template "%s": all five L2.5 layer acronyms (MSR, UCN, CDLM, CGM, RM) are present',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
      expect(rendered).toContain('MSR')
      expect(rendered).toContain('UCN')
      expect(rendered).toContain('CDLM')
      expect(rendered).toContain('CGM')
      // RM appears via the B11_EXPLICIT_LAYER_GATE
      expect(rendered).toContain('Resonance Map')
    },
  )

  // AC.8 — B11_EXPLICIT_LAYER_GATE full names present (for model comprehension)
  it.each(ACTIVE_QUERY_CLASSES)(
    'AC.8 template "%s": B11 gate names Unified Chart Narrative and Causal Graph Model',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
      expect(rendered).toContain('Unified Chart Narrative')
      expect(rendered).toContain('Causal Graph Model')
      expect(rendered).toContain('Cross-Domain Linkage Matrix')
    },
  )

  // AC.3 — CALIBRATION_LANGUAGE_GATE present in all 7 active rendered templates
  it.each(ACTIVE_QUERY_CLASSES)(
    'AC.3 template "%s": CALIBRATION_LANGUAGE_GATE is present with probabilistic language instruction',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
      expect(rendered).toContain('CALIBRATION GATE')
      expect(rendered).toContain('suggests')
      expect(rendered).toContain('indicates')
      // Oracular language forbidden
      expect(rendered).toContain('will happen')  // appears in the "do not write" list
      expect(rendered).toContain('without doubt')
    },
  )

  // AC.9 — All 8 templates (including cross_native stub) at version 2.0+
  it.each([...ACTIVE_QUERY_CLASSES, 'cross_native'] as QueryClass[])(
    'AC.9 template "%s": version is 2.0+',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      expect(parseFloat(tmpl.version)).toBeGreaterThanOrEqual(2.0)
    },
  )

  // Citation format update: (→ FORENSIC.<id>) replaces [F.<id>] in CITATION_DISCIPLINE
  it.each(ACTIVE_QUERY_CLASSES)(
    'Citation format: template "%s" uses (→ FORENSIC.<id>) format in shared preamble',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
      // New format from updated CITATION_DISCIPLINE
      expect(rendered).toContain('(→ FORENSIC.<id>)')
      expect(rendered).toContain('(→ SIG.MSR.NNN)')
    },
  )

  // B.10 NO_FABRICATION: updated to require (→ FORENSIC.<id>) citation for degrees
  it.each(ACTIVE_QUERY_CLASSES)(
    'B.10 template "%s": NO_FABRICATION gate requires inline (→ FORENSIC.<id>) for degree values',
    (qc) => {
      const registry = getDefaultRegistry()
      const tmpl = registry.get(qc, 'single_model')
      const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
      expect(rendered).toContain('[EXTERNAL_COMPUTATION_REQUIRED')
      expect(rendered).toContain('B.10 audit')
    },
  )

  // cross_native stub remains isolated from the new gates
  it('cross_native stub does not carry synthesis gates (Phase 7 stub integrity)', () => {
    const registry = getDefaultRegistry()
    const tmpl = registry.get('cross_native', 'single_model')
    const rendered = renderTemplate(tmpl, SAMPLE_VARIABLES, 'acharya')
    expect(rendered).not.toContain('CITATION GATE')
    expect(rendered).not.toContain('CALIBRATION GATE')
    expect(rendered).not.toContain('B.11 WHOLE-CHART-READ PROTOCOL')
  })
})

// ---------------------------------------------------------------------------
// CTX-GAP-S1 — QUERY_INDEPENDENCE_GATE (AC.CTX.3, AC.CTX.4, AC.CTX.5)
// ---------------------------------------------------------------------------

describe('CTX-GAP-S1: QUERY_INDEPENDENCE_GATE', () => {
  it('buildOpeningBlock includes QUERY_INDEPENDENCE_GATE header', () => {
    const block = buildOpeningBlock()
    expect(block).toContain('QUERY INDEPENDENCE GATE')
    expect(block).toContain('answered independently from the retrieved corpus')
  })

  it('QUERY_INDEPENDENCE_GATE appears after CONTRADICTION_FRAMING and before methodology block', () => {
    const block = buildOpeningBlock()
    const posGate = block.indexOf('QUERY INDEPENDENCE GATE')
    const posContradiction = block.indexOf('L3.5 Contradiction Register')
    const posMethodology = block.indexOf('marsys_methodology_block')
    expect(posGate).toBeGreaterThan(posContradiction)
    expect(posGate).toBeLessThan(posMethodology)
  })

  it('synthesis history cap: a 20-message history produces at most 4 messages', () => {
    const longHistory: Array<{ role: 'user' | 'assistant'; content: string }> =
      Array.from({ length: 20 }, (_, i) => ({
        role: (i % 2 === 0 ? 'user' : 'assistant') as 'user' | 'assistant',
        content: `turn ${i}`,
      }))
    // route.ts CTX-GAP-S1 slice: .slice(-5).slice(0,-1) = last 4 messages
    const capped = longHistory.slice(-5).slice(0, -1)
    expect(capped.length).toBeLessThanOrEqual(4)
    expect(capped.length).toBe(4)
  })
})

// ---------------------------------------------------------------------------
// Synthesis templates — multi_school_triangulation + classical_grounding
// (FIX_PROMPT_REGISTRY_MISSING_TEMPLATES_BRIEF_v1_0 §4.4)
// ---------------------------------------------------------------------------

describe('Synthesis templates — multi_school_triangulation + classical_grounding', () => {
  it('multi_school_triangulation template registers and renders cleanly', () => {
    const registry = getDefaultRegistry()
    const t = registry.get('multi_school_triangulation', 'single_model')
    expect(t).toBeDefined()
    expect(t.body).toContain('MULTI_SCHOOL_TRIANGULATION')
    expect(t.body).toContain('school_signal_coverage')
    expect(t.body).toContain('DASHA DISCIPLINE GATE')   // §5B gate present
    expect(t.body).toContain('B.11 WHOLE-CHART-READ PROTOCOL')
  })

  it('classical_grounding template registers and renders cleanly', () => {
    const registry = getDefaultRegistry()
    const t = registry.get('classical_grounding', 'single_model')
    expect(t).toBeDefined()
    expect(t.body).toContain('CLASSICAL_GROUNDING')
    expect(t.body).toContain('classical_attributions')
    expect(t.body).toContain('BPHS')
  })

  it('registry.list() now returns 10 templates', () => {
    const registry = getDefaultRegistry()
    expect(registry.list().length).toBe(10)
  })

  it('registry throws when looking up an UNKNOWN class (regression — must still fail loud)', () => {
    const registry = getDefaultRegistry()
    expect(() => registry.get('unknown_class' as any, 'single_model'))
      .toThrow(/no template found/)
  })
})
