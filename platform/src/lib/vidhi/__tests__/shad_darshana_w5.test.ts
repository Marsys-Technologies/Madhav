/**
 * shad_darshana_w5.test.ts — ṢAḌ-DARŚANA W5 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W5) planner
 * integration. Tests the piece of W5 that is IN scope tonight per the campaign's own
 * NEXT-ACTION lane (e) split: the eight primitives + question_frame threading + machine-band
 * defaults + the three kala-routing floors, all unit-testable without a live MCP call. The
 * native's hard gate (live-MCP verification table, brief §3 W5 "35 + 40") is explicitly
 * deferred to the next deploy — see the campaign ledger.
 */
import { describe, expect, it } from 'vitest';
import { compileContract, compileMultiDomainContract, defaultRegistry } from '@/lib/vidhi/compiler';
import { VIDHI_PRIMITIVES, VIDHI_INTENT_FLOORS } from '@/lib/vidhi/registry_data';
import type { QuestionFrame, ScopeTuple } from '@/lib/vidhi/types';

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa';

const KALA_PRIMITIVE_IDS = [
  'now_read',
  'ahead_read',
  'elect_read',
  'story_read',
  'priority_read',
  'explain_read',
  'upaya_read',
  'ritual_read',
] as const;

const KALA_LIVE_TOOLS = [
  'kala_now_get',
  'kala_ahead_get',
  'kala_elect_get',
  'kala_story_get',
  'kala_priority_get',
  'kala_explain_get',
  'kala_upaya_get',
  'kala_ritual_get',
] as const;

describe('ṢAḌ-DARŚANA W5 — the eight primitives', () => {
  it('all eight primitives are registered, each mapping to its own live kala_* tool', () => {
    const byId = new Map(VIDHI_PRIMITIVES.map((p) => [p.primitive_id, p]));
    for (let i = 0; i < KALA_PRIMITIVE_IDS.length; i++) {
      const primitive = byId.get(KALA_PRIMITIVE_IDS[i]!);
      expect(primitive, `primitive "${KALA_PRIMITIVE_IDS[i]}" is not registered`).toBeDefined();
      expect(primitive!.live_tool).toBe(KALA_LIVE_TOOLS[i]);
      expect(primitive!.known_gap).toBeNull();
    }
  });

  it('every one of the eight carries the question_frame placeholder in tool_args (E4 threading source)', () => {
    const byId = new Map(VIDHI_PRIMITIVES.map((p) => [p.primitive_id, p]));
    for (const id of KALA_PRIMITIVE_IDS) {
      const primitive = byId.get(id)!;
      expect(
        Object.values(primitive.tool_args).includes('{question_frame}'),
        `primitive "${id}" tool_args does not carry the {question_frame} placeholder`,
      ).toBe(true);
    }
  });

  it('upaya_read and ritual_read are category "remedy" — stripped when intervention:false, same as every other remedy primitive', () => {
    const byId = new Map(VIDHI_PRIMITIVES.map((p) => [p.primitive_id, p]));
    expect(byId.get('upaya_read')!.category).toBe('remedy');
    expect(byId.get('ritual_read')!.category).toBe('remedy');
  });
});

describe('ṢAḌ-DARŚANA W5 — question_frame threading (E4)', () => {
  const tuple: ScopeTuple = {
    intent: 'undertaking_election',
    domains: ['career'],
    width: 'standard',
    depth: 'deepdive',
    horizon: 'current',
    intervention: true,
    entitlement: 'native',
  };

  it('a supplied questionFrame substitutes the {question_frame} placeholder on every carrying item', () => {
    const registry = defaultRegistry();
    const qf: QuestionFrame = { domain: 'career', entity: 'the Singapore role', intent_verb: 'when_should_i' };
    const contract = compileContract(tuple, registry, CHART_ID, qf);
    const electItem = contract.floor.find((i) => i.primitive_id === 'elect_read');
    expect(electItem).toBeDefined();
    expect(electItem!.tool_args.question_frame).toEqual(qf);
  });

  it('an omitted questionFrame leaves the placeholder unresolved as null (never a fabricated frame)', () => {
    const registry = defaultRegistry();
    const contract = compileContract(tuple, registry, CHART_ID);
    const electItem = contract.floor.find((i) => i.primitive_id === 'elect_read');
    expect(electItem!.tool_args.question_frame).toBeNull();
  });

  it('question_frame threading does not disturb {chart_id} substitution on the SAME compiled item', () => {
    const registry = defaultRegistry();
    const qf: QuestionFrame = { horizon: '90d' };
    const contract = compileContract(tuple, registry, CHART_ID, qf);
    const electItem = contract.floor.find((i) => i.primitive_id === 'elect_read');
    expect(electItem!.tool_args.chart_id).toBe(CHART_ID);
    expect(electItem!.tool_args.question_frame).toEqual(qf);
  });

  it('identical (tuple, chartId, questionFrame) compiles byte-identically — threading preserves determinism', () => {
    const registry = defaultRegistry();
    const qf: QuestionFrame = { domain: 'career' };
    const a = JSON.stringify(compileContract(tuple, registry, CHART_ID, qf));
    const b = JSON.stringify(compileContract(tuple, registry, CHART_ID, qf));
    expect(a).toBe(b);
  });

  it('a DIFFERING questionFrame produces a different compiled contract — the threading is not a no-op', () => {
    const registry = defaultRegistry();
    const a = JSON.stringify(compileContract(tuple, registry, CHART_ID, { domain: 'career' }));
    const b = JSON.stringify(compileContract(tuple, registry, CHART_ID, { domain: 'wealth' }));
    expect(a).not.toBe(b);
  });
});

describe('ṢAḌ-DARŚANA W5 — machine-band defaults (Six Views Design §8)', () => {
  const DEEPDIVE_INTENTS = [
    'wealth_deepdive',
    'career_deepdive',
    'health_deepdive',
    'marriage_deepdive',
    'spirituality_deepdive',
    'education_deepdive',
    'progeny_deepdive',
  ] as const;

  it('every domain deepdive machine band compiles NOW + AHEAD + PRIORITIZE', () => {
    const registry = defaultRegistry();
    for (const intent of DEEPDIVE_INTENTS) {
      const tuple: ScopeTuple = {
        intent, domains: ['general'], width: 'standard', depth: 'deepdive',
        horizon: 'current', intervention: true, entitlement: 'native',
      };
      const contract = compileContract(tuple, registry, CHART_ID);
      const machineIds = new Set(contract.machine_band.map((i) => i.primitive_id));
      expect(machineIds.has('now_read'), `${intent} machine band missing now_read`).toBe(true);
      expect(machineIds.has('ahead_read'), `${intent} machine band missing ahead_read`).toBe(true);
      expect(machineIds.has('priority_read'), `${intent} machine band missing priority_read`).toBe(true);
    }
  });

  it('general_synthesis (the E-0 foundation) also carries NOW + AHEAD + PRIORITIZE', () => {
    const registry = defaultRegistry();
    const tuple: ScopeTuple = {
      intent: 'general_synthesis', domains: ['general'], width: 'standard', depth: 'deepdive',
      horizon: 'current', intervention: true, entitlement: 'native',
    };
    const contract = compileContract(tuple, registry, CHART_ID);
    const machineIds = new Set(contract.machine_band.map((i) => i.primitive_id));
    expect(machineIds.has('now_read')).toBe(true);
    expect(machineIds.has('ahead_read')).toBe(true);
    expect(machineIds.has('priority_read')).toBe(true);
  });

  it('NOW/AHEAD/PRIORITIZE are hard_floor — a budget trim protects them first, never sacrifices them (§N.6)', () => {
    const registry = defaultRegistry();
    const tuple: ScopeTuple = {
      intent: 'wealth_deepdive', domains: ['wealth'], width: 'standard', depth: 'deepdive',
      horizon: 'current', intervention: true, entitlement: 'native',
    };
    const contract = compileContract(tuple, registry, CHART_ID);
    for (const id of ['now_read', 'ahead_read', 'priority_read']) {
      const item = contract.machine_band.find((i) => i.primitive_id === id);
      expect(item, `machine band missing ${id}`).toBeDefined();
      expect(item!.hard_floor, `${id} is not hard_floor`).toBe(true);
    }
  });

  it('a structure_read / retrieval_only tuple (no machine band) does NOT carry NOW/AHEAD/PRIORITIZE — depth doctrine unchanged', () => {
    const registry = defaultRegistry();
    const tuple: ScopeTuple = {
      intent: 'structure_read', domains: ['general'], width: 'standard', depth: 'structure',
      horizon: 'current', intervention: false, entitlement: 'native',
    };
    const contract = compileContract(tuple, registry, CHART_ID);
    expect(contract.machine_band.length).toBe(0);
  });
});

describe('ṢAḌ-DARŚANA W5 — the three kala-routing floors (undertaking→ELECT, biography→STORY, ritual→RITUAL)', () => {
  it('undertaking_election is headlined by elect_read, hard_floor, order 1', () => {
    const floor = VIDHI_INTENT_FLOORS.find((f) => f.intent === 'undertaking_election')!;
    expect(floor).toBeDefined();
    const headline = floor.floor_items.find((i) => i.order === 1)!;
    expect(headline.primitive_id).toBe('elect_read');
    expect(headline.hard_floor).toBe(true);
    expect(headline.band).toBe('acharya_floor');
  });

  it('biography_narrative is headlined by story_read, hard_floor, order 1', () => {
    const floor = VIDHI_INTENT_FLOORS.find((f) => f.intent === 'biography_narrative')!;
    expect(floor).toBeDefined();
    const headline = floor.floor_items.find((i) => i.order === 1)!;
    expect(headline.primitive_id).toBe('story_read');
    expect(headline.hard_floor).toBe(true);
  });

  it('ritual_yajna is headlined by ritual_read, hard_floor, order 1', () => {
    const floor = VIDHI_INTENT_FLOORS.find((f) => f.intent === 'ritual_yajna')!;
    expect(floor).toBeDefined();
    const headline = floor.floor_items.find((i) => i.order === 1)!;
    expect(headline.primitive_id).toBe('ritual_read');
    expect(headline.hard_floor).toBe(true);
  });

  it('each of the three routing floors carries the Pūrṇa-Ādhāra structural minimum beneath its headline (not a bare single-tool answer)', () => {
    for (const intent of ['undertaking_election', 'biography_narrative', 'ritual_yajna'] as const) {
      const floor = VIDHI_INTENT_FLOORS.find((f) => f.intent === intent)!;
      // FOUNDATION_BAND_ITEMS carries chart_digest_read as its own hard_floor lead — confirms
      // the shared structural band rode along, not just the headline primitive alone.
      expect(
        floor.floor_items.some((i) => i.primitive_id === 'chart_digest_read'),
        `floor "${intent}" is missing the Pūrṇa-Ādhāra foundation (chart_digest_read)`,
      ).toBe(true);
      expect(floor.floor_items.length).toBeGreaterThan(5);
    }
  });

  it('all three routing floors compile without throwing at deepdive depth, both intervention states', () => {
    const registry = defaultRegistry();
    for (const intent of ['undertaking_election', 'biography_narrative', 'ritual_yajna'] as const) {
      for (const intervention of [true, false]) {
        expect(() =>
          compileContract(
            { intent, domains: ['general'], width: 'standard', depth: 'deepdive', horizon: 'current', intervention, entitlement: 'native' },
            registry,
            CHART_ID,
          ),
        ).not.toThrow();
      }
    }
  });

  it('ritual_yajna does NOT compile elect_read, and undertaking_election does NOT compile ritual_read or story_read — the routing split is real, not a merged floor', () => {
    const registry = defaultRegistry();
    const compile = (intent: 'undertaking_election' | 'biography_narrative' | 'ritual_yajna') =>
      compileContract(
        { intent, domains: ['general'], width: 'standard', depth: 'deepdive', horizon: 'current', intervention: true, entitlement: 'native' },
        registry,
        CHART_ID,
      );
    const ids = (c: ReturnType<typeof compile>) => new Set([...c.floor, ...c.machine_band].map((i) => i.primitive_id));

    const undertaking = ids(compile('undertaking_election'));
    expect(undertaking.has('elect_read')).toBe(true);
    expect(undertaking.has('ritual_read')).toBe(false);
    expect(undertaking.has('story_read')).toBe(false);

    const biography = ids(compile('biography_narrative'));
    expect(biography.has('story_read')).toBe(true);
    expect(biography.has('elect_read')).toBe(false);
    expect(biography.has('ritual_read')).toBe(false);

    const ritual = ids(compile('ritual_yajna'));
    expect(ritual.has('ritual_read')).toBe(true);
    expect(ritual.has('elect_read')).toBe(false);
    expect(ritual.has('story_read')).toBe(false);
  });
});

describe('ṢAḌ-DARŚANA W5 — "every served row id pre-authorizes one EXPLAIN hop" (Six Views Design §8)', () => {
  it('every compiled floor item (except explain_read itself) gets an explain_on_request adaptive expansion', () => {
    const registry = defaultRegistry();
    const tuple: ScopeTuple = {
      intent: 'wealth_deepdive', domains: ['wealth'], width: 'standard', depth: 'deepdive',
      horizon: 'current', intervention: true, entitlement: 'native',
    };
    const contract = compileContract(tuple, registry, CHART_ID);
    const compiledIds = [...contract.floor, ...contract.machine_band].map((i) => i.primitive_id);
    const explainHops = contract.adaptive_expansions.filter((e) => e.rule === 'explain_on_request');
    const explainSources = new Set(explainHops.map((e) => e.source_primitive_id));

    for (const id of compiledIds) {
      if (id === 'explain_read') continue;
      expect(explainSources.has(id), `compiled item "${id}" has no explain_on_request hop`).toBe(true);
    }
    // Anti-vacuous + no self-loop: explain_read never authorizes an EXPLAIN-of-EXPLAIN hop.
    expect(explainHops.length).toBeGreaterThan(0);
    expect(explainSources.has('explain_read')).toBe(false);
    for (const e of explainHops) {
      expect(e.add_primitive_id).toBe('explain_read');
      expect(e.hop).toBe(1);
    }
  });

  it('the routing floors also get the explain hop on their headline item', () => {
    const registry = defaultRegistry();
    const contract = compileContract(
      { intent: 'undertaking_election', domains: ['general'], width: 'standard', depth: 'deepdive', horizon: 'current', intervention: true, entitlement: 'native' },
      registry,
      CHART_ID,
    );
    const hop = contract.adaptive_expansions.find((e) => e.rule === 'explain_on_request' && e.source_primitive_id === 'elect_read');
    expect(hop).toBeDefined();
  });
});

describe('ṢAḌ-DARŚANA W5 — E-4 multi-domain union still works with the new floors present', () => {
  it('compileMultiDomainContract on a plain deepdive tuple is unaffected by the new routing floors (single-domain path unchanged)', () => {
    const registry = defaultRegistry();
    const tuple: ScopeTuple = {
      intent: 'wealth_deepdive', domains: ['wealth'], width: 'standard', depth: 'deepdive',
      horizon: 'current', intervention: true, entitlement: 'native',
    };
    const single = JSON.stringify(compileContract(tuple, registry, CHART_ID));
    const multi = JSON.stringify(compileMultiDomainContract(tuple, registry, CHART_ID));
    expect(multi).toBe(single);
  });

  it('compileMultiDomainContract threads questionFrame through exactly like compileContract', () => {
    const registry = defaultRegistry();
    const tuple: ScopeTuple = {
      intent: 'undertaking_election', domains: ['general'], width: 'standard', depth: 'deepdive',
      horizon: 'current', intervention: true, entitlement: 'native',
    };
    const qf: QuestionFrame = { entity: 'the merger' };
    const contract = compileMultiDomainContract(tuple, registry, CHART_ID, qf);
    const electItem = contract.floor.find((i) => i.primitive_id === 'elect_read');
    expect(electItem!.tool_args.question_frame).toEqual(qf);
  });
});
