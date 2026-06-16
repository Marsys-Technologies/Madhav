---
canonical_id: FIX_PROMPT_REGISTRY_MISSING_TEMPLATES_BRIEF
version: 1.0
status: AUTHORED_READY_TO_EXECUTE
authored_on: 2026-05-19
category: hygiene / hot-fix
estimated_sessions: 1 (small — ~45 min wall)
two_stream_branch: feat/synthesis-templates-multi-school-classical
depends_on: PR #97 (Phase 5 + Yogini/Chara extension on main; this brief uses the same shared.ts gates)
---

# Fix Prompt Registry — Author Missing Templates for `multi_school_triangulation` + `classical_grounding`

## §1 Root cause

The `QueryClass` enum in `platform/src/lib/router/types.ts` declares 10 values:

```ts
'factual' | 'interpretive' | 'predictive' | 'cross_domain' | 'discovery' |
'holistic' | 'remedial' | 'cross_native' | 'classical_grounding' |
'multi_school_triangulation'
```

But the `PromptRegistry` in `platform/src/lib/prompts/index.ts` registers only 8. When the planner classifies a query as `multi_school_triangulation` (Phase 2A M9 work) or `classical_grounding` (Phase 2A M8-G work), the registry's `get()` throws:

```
PromptRegistry: no template found for (query_class="multi_school_triangulation", ...)
```

The consume route catches the throw and emits **HTTP 500 SYSTEM_INTERNAL** to the client. This surfaced as the persistent 500s on F005 / F008 / F010 in the Phase 4 eval rerun.

## §2 Scope

Author the two missing templates + register them. No new tools, no migrations, no architecture changes — purely closing a hole left when Phase 2A added the query classes without their synthesis prompts.

## §3 What you must NOT do

- **No branch other than `feat/synthesis-templates-multi-school-classical`**.
- **No Chat V2 files**.
- **No autonomous `npm run answer:eval`**.
- **Do not modify** the existing 8 templates — only ADD 2 new files.
- **Do not modify `shared.ts`** — read it for imports only. The existing gates already cover the new templates' needs.

## §4 Files to create / modify

### §4.1 New file — `platform/src/lib/prompts/templates/multi_school_triangulation.ts`

Mirror the existing template pattern (see `factual.ts` for the simplest shape, `cross_domain.ts` for the closest semantic neighbor). Body should:

- Surface per-school readings as a comparison structure (one paragraph per Jyotish school active in retrieval)
- Cite `school_signal_coverage` rows by `(school, signal_id)` reference where retrieved
- Cite `convergence_scores` for HIGH / MEDIUM / LOW convergence per domain
- Make clear where schools CONVERGE vs DIVERGE — do not synthesize the disagreement away. Reference the existing `CONTRADICTION_FRAMING` discipline in shared.ts (already included via `buildOpeningBlock`).

```ts
import type { PromptTemplate } from '../types'
import {
  buildOpeningBlock,
  PRESCRIPTIVE_CITATION_GATE,
  CALIBRATION_LANGUAGE_GATE,
  B11_EXPLICIT_LAYER_GATE,
  DASHA_DISCIPLINE_GATE,   // Phase 5B — applies when MS query touches dasha
  REQUIRED_PLACEHOLDERS_BASE,
  STYLE_SUFFIXES,
} from './shared'

export const template: PromptTemplate = {
  template_id: 'multi_school_triangulation_super_admin_single_model_v1',
  version: '1.0',
  query_class: 'multi_school_triangulation',
  audience_tier: 'super_admin',
  strategy: 'single_model',
  body: `${buildOpeningBlock()}

${B11_EXPLICIT_LAYER_GATE}

${DASHA_DISCIPLINE_GATE}

QUERY CLASS: MULTI_SCHOOL_TRIANGULATION
----------------------------------------
You are producing a comparative read across multiple Jyotish schools — Parashari, Jaimini, KP, Tajika, Nadi, BNN, Yogini. The retrieval bundle contains \`multi_school_signal_lookup\` and/or \`convergence_score_lookup\` results. Your job is to surface what each school says, where they agree, and where they diverge — NOT to collapse the disagreement into a unified narrative.

Rules for multi_school_triangulation responses:

1. Structure the answer school-by-school. Name each school in the response (Parashari, Jaimini, KP, etc.) and quote its position from the retrieval bundle. Cite signal IDs from \`school_signal_coverage\` in the form (→ SIG.MSR.NNN [school:parashari]) or (→ SIG.MSR.NNN [school:jaimini]) so the audit can trace each per-school claim to its origin.

2. When convergence_scores are present, lead with the convergence verdict:
   - HIGH convergence: "X of 7 schools agree on this domain (convergence_level=HIGH); the read across schools is unified."
   - MEDIUM: "Partial convergence — schools split on direction. Surface both camps."
   - LOW: "Schools materially disagree. Treat as an open contradiction (CON.<id>) rather than averaging."

3. Cite convergence_scores explicitly: "Domain CAREER shows convergence_level=HIGH (7/7 schools agreeing, mean_domain_score 0.XX) → SIG.MSR.NNN".

4. For each DIVERGENT school's position, surface its full reading even if it disagrees with the majority. Calibration depends on knowing the dissent shape, not on smoothing it.

5. Do NOT prefer one school's framing over another by default. Parashari is the project's primary, but a Multi-School query is explicitly asking for the cross-school comparison — answer that question, not a Parashari-only answer.

6. When a school is SILENT on the queried topic (coverage_type='silent'), say so explicitly. Silence is a meaningful signal in classical triangulation.

7. The R-DA dasha discipline still applies. Any dasha-period claim must cite DSH.V.NNN (or DSH.Y.NNN / DSH.C.NNN). Cross-school analysis does not exempt the dasha citation requirement.

${CALIBRATION_LANGUAGE_GATE}

${PRESCRIPTIVE_CITATION_GATE}`,
  style_suffixes: { ...STYLE_SUFFIXES },
  required_placeholders: [...REQUIRED_PLACEHOLDERS_BASE],
}
```

### §4.2 New file — `platform/src/lib/prompts/templates/classical_grounding.ts`

Same pattern. Body should:

- Lead with the classical citation(s) — chapter, verse, text (BPHS, Phaladeepika, Saravali, etc.)
- Bridge from the classical principle to the native's chart fact
- Cite both `classical_attributions.confidence_tier` and the underlying `SIG.MSR.NNN`

```ts
import type { PromptTemplate } from '../types'
import {
  buildOpeningBlock,
  PRESCRIPTIVE_CITATION_GATE,
  CALIBRATION_LANGUAGE_GATE,
  B11_EXPLICIT_LAYER_GATE,
  REQUIRED_PLACEHOLDERS_BASE,
  STYLE_SUFFIXES,
} from './shared'

export const template: PromptTemplate = {
  template_id: 'classical_grounding_super_admin_single_model_v1',
  version: '1.0',
  query_class: 'classical_grounding',
  audience_tier: 'super_admin',
  strategy: 'single_model',
  body: `${buildOpeningBlock()}

${B11_EXPLICIT_LAYER_GATE}

QUERY CLASS: CLASSICAL_GROUNDING
---------------------------------
You are anchoring a chart reading in classical Jyotish authority — chapter and verse from BPHS, Phaladeepika, Saravali, Uttara Kalamrita, Jaimini Sutra, or Tier-3 texts (Hora Sara, Garga Hora, etc.). The retrieval bundle contains \`classical_text_search\` results and/or \`classical_attribution_lookup\` results mapping MSR signals to classical text passages.

Rules for classical_grounding responses:

1. LEAD with the classical citation. State the text, chapter, verse range, and the relevant principle directly. Example: "BPHS Ch.34 v.12 establishes that Saturn in the 10th house in own sign yields kingly results (rajayoga indication)."

2. Bridge from classical to chart-specific. After the classical citation, name how it applies to THIS native's chart, citing the underlying MSR signal:
   "This native's Saturn in Libra (its own / exaltation sign) in the 10th house (→ SIG.MSR.NNN, → FORENSIC.<id>) is a direct instance of the BPHS Ch.34 v.12 yoga."

3. Include classical_attributions.confidence_tier when present:
   - tier=HIGH: "BPHS is unambiguous on this point — no contradictions found."
   - tier=MEDIUM: "BPHS supports this; Phaladeepika is silent."
   - tier=LOW: "Only Tier-3 texts mention this; classical support is thin."

4. When classical_attributions surfaces a 'contradicts' or 'partial' attribution, NAME the conflict:
   "BPHS Ch.34 v.12 establishes X as positive; Phaladeepika Ch.7 v.4 qualifies that this requires <condition>. For this native, the condition is met (→ FORENSIC.<id>), so the positive reading holds."

5. If the user query asks WHY the classical authority gives a particular reading, surface the classical reasoning. Vedic astrology is grounded in source texts, not anonymous tradition.

6. Avoid hallucinating verse numbers. If the retrieved bundle says "BPHS Ch.34 v.12", cite it exactly. If chapter/verse is missing from the retrieval, write [EXTERNAL_COMPUTATION_REQUIRED: chapter/verse for classical claim on <topic>] rather than inventing.

7. R-DA dasha discipline applies if dasha is touched. The classical citation must coexist with DSH.V.NNN citation for any temporal claim.

${CALIBRATION_LANGUAGE_GATE}

${PRESCRIPTIVE_CITATION_GATE}`,
  style_suffixes: { ...STYLE_SUFFIXES },
  required_placeholders: [...REQUIRED_PLACEHOLDERS_BASE],
}
```

### §4.3 Update — `platform/src/lib/prompts/index.ts`

Two changes:

```ts
// Add imports near the existing template imports:
import { template as multiSchoolTemplate } from './templates/multi_school_triangulation'
import { template as classicalGroundingTemplate } from './templates/classical_grounding'
```

```ts
// In createRegistry(), add two registry.register() calls:
export function createRegistry(): PromptRegistry {
  const registry = new PromptRegistryImpl()

  registry.register(factualTemplate)
  registry.register(interpretiveTemplate)
  registry.register(predictiveTemplate)
  registry.register(crossDomainTemplate)
  registry.register(discoveryTemplate)
  registry.register(holisticTemplate)
  registry.register(remedialTemplate)
  registry.register(crossNativeTemplate)
  registry.register(multiSchoolTemplate)         // NEW
  registry.register(classicalGroundingTemplate)  // NEW

  return registry
}
```

Update the docstring on `getDefaultRegistry` to say "10 templates" instead of "8".

### §4.4 Extend — `platform/src/lib/prompts/__tests__/prompts.test.ts`

Add a `describe` block for the new templates:

```ts
describe('Synthesis templates — multi_school_triangulation + classical_grounding', () => {
  it('multi_school_triangulation template registers and renders cleanly', () => {
    const { getDefaultRegistry } = require('../index')
    const registry = getDefaultRegistry()
    const t = registry.get('multi_school_triangulation', 'super_admin', 'single_model')
    expect(t).toBeDefined()
    expect(t.body).toContain('MULTI_SCHOOL_TRIANGULATION')
    expect(t.body).toContain('school_signal_coverage')
    expect(t.body).toContain('DASHA DISCIPLINE GATE')   // §5B gate present
    expect(t.body).toContain('B.11 WHOLE-CHART-READ PROTOCOL')
  })

  it('classical_grounding template registers and renders cleanly', () => {
    const { getDefaultRegistry } = require('../index')
    const registry = getDefaultRegistry()
    const t = registry.get('classical_grounding', 'super_admin', 'single_model')
    expect(t).toBeDefined()
    expect(t.body).toContain('CLASSICAL_GROUNDING')
    expect(t.body).toContain('classical_attributions')
    expect(t.body).toContain('BPHS')
  })

  it('registry.list() now returns 10 templates', () => {
    const { getDefaultRegistry } = require('../index')
    const registry = getDefaultRegistry()
    expect(registry.list().length).toBe(10)
  })

  it('registry throws when looking up an UNKNOWN class (regression — must still fail loud)', () => {
    const { getDefaultRegistry } = require('../index')
    const registry = getDefaultRegistry()
    expect(() => registry.get('unknown_class' as any, 'super_admin', 'single_model'))
      .toThrow(/no template found/)
  })
})
```

## §5 Verification gates (pre-commit)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-500s-fix/platform

# G1: TypeScript compiles
npx tsc --noEmit

# G2: Prompts tests
npx vitest run src/lib/prompts/__tests__/prompts.test.ts

# G3: Full src/lib/ regression (other modules might import from prompts/index.ts)
npx vitest run src/lib/

# G4: planner_regression_gate — synthesis-only change should not affect planner
npx vitest run tests/eval/planner_regression_gate.test.ts
```

All 4 gates green before commit.

## §6 Commit + PR

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-500s-fix

git add platform/src/lib/prompts/templates/multi_school_triangulation.ts \
        platform/src/lib/prompts/templates/classical_grounding.ts \
        platform/src/lib/prompts/index.ts \
        platform/src/lib/prompts/__tests__/prompts.test.ts

git commit -m "fix(prompts): author missing templates for multi_school_triangulation + classical_grounding

Root cause: Phase 2A added two query classes to the QueryClass enum
(multi_school_triangulation, classical_grounding) and the corresponding
planner R-rules (R31, R32) + retrieval tools (multi_school_signal_lookup,
convergence_score_lookup, classical_text_search, classical_attribution_lookup),
but never authored the synthesis prompt templates. When the planner
classified a query as either class, the PromptRegistry threw, surfacing
as HTTP 500 SYSTEM_INTERNAL to the client.

Surfaced as persistent 500s on F005 / F008 / F010 in the Phase 4 eval
rerun (2026-05-19, eval_post_phase4_gemini_20260519.json).

Fix: author the two missing templates following the existing pattern.
Both use buildOpeningBlock + B11_EXPLICIT_LAYER_GATE + CALIBRATION +
PRESCRIPTIVE_CITATION_GATE. multi_school_triangulation also wires in
the DASHA_DISCIPLINE_GATE since multi-school queries often touch dasha.

Template count 8 → 10. Registry list() now returns 10.

After deploy: F005 / F008 / F010 should succeed (or fail differently on
substantive grounds — keyword_recall + synthesis — not infrastructure).
Next eval rerun should move 21/24 → 24/24 if synthesis quality holds.

Refs: 00_ARCHITECTURE/briefs/FIX_PROMPT_REGISTRY_MISSING_TEMPLATES_BRIEF_v1_0.md"

git push origin feat/synthesis-templates-multi-school-classical

gh pr create \
  --base main \
  --head feat/synthesis-templates-multi-school-classical \
  --title "fix(prompts): author missing synthesis templates for multi_school_triangulation + classical_grounding" \
  --body "Closes the persistent HTTP 500s on F005 / F008 / F010 surfaced in the Phase 4 eval rerun.

Root cause: Phase 2A added two query classes (multi_school_triangulation, classical_grounding) to the enum and the planner R-rules + retrieval tools, but never authored the synthesis prompt templates. The PromptRegistry throws for unknown classes; the consume route catches and emits HTTP 500.

Fix: 2 new template files + registry registration + 4 unit tests. No tool / planner / migration changes — purely closing a synthesis-layer hole.

Template count 8 → 10.

Refs: 00_ARCHITECTURE/briefs/FIX_PROMPT_REGISTRY_MISSING_TEMPLATES_BRIEF_v1_0.md"

gh pr merge feat/synthesis-templates-multi-school-classical --merge --auto
```

## §7 Acceptance criteria

- [ ] `multi_school_triangulation.ts` ships with proper imports + body
- [ ] `classical_grounding.ts` ships
- [ ] `index.ts createRegistry` registers both
- [ ] 4 new unit tests pass; registry.list().length === 10
- [ ] `tsc --noEmit` clean
- [ ] Full src/lib/ regression green
- [ ] `planner_regression_gate` green (this is a synthesis-layer change, planner unaffected)
- [ ] Commit lands on `feat/synthesis-templates-multi-school-classical`; PR opened against main; auto-merge on green CI
- [ ] No Chat V2 files touched; no autonomous answer:eval

## §8 Report back

When complete:

1. Closing commit SHA + `git log --oneline -3` on the feat branch.
2. PR URL + merge status.
3. Test counts (existing total + 4 new from this brief).
4. Cloud Run revision after deploy (`gcloud run services describe amjis-web --format='value(status.latestReadyRevisionName)'`).
5. Recommendation on whether to re-run a small targeted eval (F005/F008/F010 only) post-deploy to confirm the 500s are gone — that's a 5-minute curl-loop, not a full answer:eval batch.

I'll then record the close in memory.
