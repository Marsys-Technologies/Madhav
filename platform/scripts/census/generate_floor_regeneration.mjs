#!/usr/bin/env node
/**
 * generate_floor_regeneration.mjs — Elevation Campaign v2.1, Stream γ (PŪRṆA), Lane Ω8.
 *
 * "The planner catches up to the TCI." Every domain floor (the minimum guaranteed-served
 * concept set a domain deepdive must include) is REGENERATED **from** the TCI slice + Ω2's
 * relevance map, NEVER hand-curated. This replaces the hand-authored per-domain varga/lagna/AV
 * lists in `platform/src/lib/vidhi/registry_data.ts` (VIDHI_INTENT_FLOORS) with a mechanically
 * enumerated, TCI-derived floor for each domain.
 *
 * WHAT THE CHARTER Ω8 SPEC ASKS FOR (§Ω8), realized here mechanically:
 *   - ashtakavarga_scan  → gains per-varga Ashtakavarga (all vargas, not just D1) as floor items
 *                          for domains where AV is classically relevant.
 *   - divisional_facts   → gains every domain-relevant varga (wealth→D2/D11, career→D10,
 *                          marriage/spirituality→D9, health→D6/D30, education→D24, progeny→D7)
 *                          — the vargas Ω2 classifies `primary` for the domain, ∪ the universal
 *                          {D1, D9} foundation. (wealth's Indu Lagna is carried by special_lagna_read.)
 *   - special_lagna_read → gains the FULL lagna + saham set (7 special lagnas + 70 sahams + upapada).
 *   - argala / dispositor-closure / cross-ayanamsha / mechanism primitives → added as floor items
 *     where domain-relevant (Ω6's covered surfaces).
 *
 * The domain→varga linkage is NOT hardcoded: it is read out of Ω2's DOMAIN_RELEVANCE_MAP by
 * scanning the chart_divisionals concepts for `domains[domain] === 'primary'`.
 *
 * OUTPUTS (this lane's manifest scope, capability_map/**):
 *   REGENERATED_FLOORS_v1_0.json          — per-domain, per-floor-tool TCI-derived floor items
 *                                           (the correct data an α/later pass wires into
 *                                           registry_data.ts; same pattern Lane E used for
 *                                           rank_vocabulary.ts — the floor CONSUMER is cross-manifest).
 *   FLOOR_COVERAGE_ACCOUNTING_v1_0.json   — the CI-gate artifact: each floor's own TCI-derived
 *                                           slice, accounted into the SAME five Ω3 states, per
 *                                           (domain × chart), with pass/fail. check_floor_coverage.mjs
 *                                           reads it and fails the build on any non-pass.
 *
 * No DB access required: state assignment mirrors Ω3's `stateFor` exactly
 * (row_count_per_canonical_chart[chart] > 0 → served; else computed_globally → empty_for_this_chart;
 * else not_computed_globally). Coverage completeness is a property of the TCI, not the live DB.
 */

import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(__dirname, '../../..');
const WORKTREES = resolve(REPO, '..');
const CAP_MAP = join(REPO, '00_ARCHITECTURE/llm_consumption_audit/capability_map');

const CHART_PRIMARY = '482012f1-710e-4a25-994a-93821f5871aa';
const CHART_SECOND = '1c826d5a-41cb-4450-b4dc-59d440e5f75a';
const CHARTS = [CHART_PRIMARY, CHART_SECOND];

// Domains regenerated: the 7 domain deepdive floors in registry_data.ts that map to an Ω2
// tracked domain carrying a classical varga linkage.
const DOMAINS = ['wealth', 'career', 'marriage', 'health', 'spirituality', 'education', 'progeny'];

// Vargas every deep reading carries regardless of domain (rasi anchor + navamsha foundation).
const UNIVERSAL_VARGAS = ['D1', 'D9'];

function firstExisting(cands) { return cands.find((p) => p && existsSync(p)); }
const TCI_PATH = process.env.TCI_PATH || firstExisting([
  join(CAP_MAP, 'TOTAL_CONCEPT_INVENTORY_v1_0.json'),
  join(WORKTREES, 'gamma-lane-omega-tci/00_ARCHITECTURE/llm_consumption_audit/capability_map/TOTAL_CONCEPT_INVENTORY_v1_0.json'),
]);
const RELEVANCE_PATH = process.env.RELEVANCE_PATH || firstExisting([
  join(CAP_MAP, 'DOMAIN_RELEVANCE_MAP_v1_0.json'),
  join(WORKTREES, 'gamma-lane-omega-relevance/00_ARCHITECTURE/llm_consumption_audit/capability_map/DOMAIN_RELEVANCE_MAP_v1_0.json'),
]);

function log(...a) { process.stderr.write(a.join(' ') + '\n'); }

const tci = JSON.parse(readFileSync(TCI_PATH, 'utf8'));
const rel = JSON.parse(readFileSync(RELEVANCE_PATH, 'utf8'));
const relById = new Map(rel.entries.map((e) => [e.concept_id, e]));
const tciById = new Map(tci.entries.map((e) => [e.concept_id, e]));
log(`TCI ${tci.entries.length} entries · relevance ${rel.entries.length} entries`);

// ---- helpers over TCI entries -------------------------------------------
const catOf = (e) => (e.serving_args || {}).category;         // post Ω8-fixup key
const vargaOf = (e) => (e.serving_args || {}).varga;

function stateFor(entry, chart) {
  const rc = entry.row_count_per_canonical_chart || {};
  const n = rc[chart];
  if (typeof n === 'number' && n > 0) return 'served';
  if (entry.computed_globally === true) return 'empty_for_this_chart';
  return 'not_computed_globally';
}

// Ω2 slice-membership: concept is in domain d's slice iff NOT domain_agnostic AND d key present.
function domainRelevant(cid, domain) {
  const r = relById.get(cid);
  if (!r || r.domain_agnostic) return false;
  return !!(r.domains && Object.prototype.hasOwnProperty.call(r.domains, domain));
}
function isAgnostic(cid) { return !!(relById.get(cid) || {}).domain_agnostic; }

// ---- derive Ω2-primary vargas per domain from the chart_divisionals concepts -------
const divisionalConcepts = tci.entries.filter(
  (e) => (e.source_axis || '').startsWith('L1:chart_divisionals') &&
    vargaOf(e) && !['ALL_VARGAS', 'CROSS'].includes(vargaOf(e)));
const divByVarga = new Map(divisionalConcepts.map((e) => [vargaOf(e), e]));

function primaryVargasFor(domain) {
  const out = [];
  for (const e of divisionalConcepts) {
    const r = relById.get(e.concept_id);
    if (r && !r.domain_agnostic && (r.domains || {})[domain] === 'primary') out.push(vargaOf(e));
  }
  return out.sort();
}

// ---- floor-tool → TCI concept selectors (the covering families) ---------------------
// Each selector is a predicate over TCI entries. A floor item's coverage = concepts matching
// the selector that are relevant to the domain (or agnostic-universal, tracked separately).
const SELECTORS = {
  ashtakavarga_scan: {
    kind: 'category_prefix',
    match: (e) => (catOf(e) || '').startsWith('ashtakavarga'),
    live_tool: 'ganita_chart_facts_get',
    note: 'D1 + per-varga Ashtakavarga (ashtakavarga_bindu / _sign / _per_varga / pinda_* / *_shodhana / kakshya).',
  },
  special_lagna_read: {
    kind: 'category_set',
    cats: ['special_lagna', 'saham_position', 'upapada_lagna'],
    match: (e) => ['special_lagna', 'saham_position', 'upapada_lagna'].includes(catOf(e)),
    live_tool: 'ganita_special_lagnas_get',
    note: 'Full lagna + saham set: 7 special lagnas (Indu/Sree/Ghati/Hora/Bhava/Varnada/Vighati) + 70 sahams + Upapada.',
  },
  argala_read: {
    kind: 'category_set',
    cats: ['argala_natal_matrix', 'virodha_argala_natal_matrix', 'net_argala_per_varga'],
    match: (e) => ['argala_natal_matrix', 'virodha_argala_natal_matrix', 'net_argala_per_varga'].includes(catOf(e)),
    live_tool: 'ganita_chart_facts_get',
    note: 'Argala / virodha-argala natal matrix + per-varga net argala (intervention structure on the bhavas).',
  },
  dispositor_closure_read: {
    kind: 'mixed',
    match: (e) => e.concept_id.toLowerCase().includes('dispositor') ||
      (e.serving_tool === 'bodha_mechanisms_get' &&
        ['convergent_dispositor_chain', 'dispositor_cycle'].some((m) => e.concept_id.includes(m))),
    live_tool: 'ganita_chart_facts_get + bodha_mechanisms_get',
    note: 'Dispositor-strength closure (composite_dispositor_strength …) + convergent-dispositor-chain / dispositor-cycle mechanism classes.',
  },
  mechanism_read: {
    kind: 'serving_tool',
    match: (e) => e.serving_tool === 'bodha_mechanisms_get' &&
      (e.source_axis || '').startsWith('L2:bodha_mechanisms'),
    live_tool: 'bodha_mechanisms_get',
    note: 'The 10 CGM mechanism classes (chains/circuits). Per CMN-1 the TCI row_count is ayanamsha-summed.',
  },
  cross_ayanamsha_agreement: {
    kind: 'axis',
    agnostic_universal: true,
    match: (e) => (e.source_axis || '').startsWith('meta:chart_facts(ayanamsha'),
    live_tool: 'ganita_positions_get',
    note: 'Cross-ayanamsha agreement (5-ayanamsha spread per anchor). Domain-agnostic universal — accounted in its own bucket.',
  },
};

// Precompute the matched concept lists once.
const matchedByTool = {};
for (const [tool, sel] of Object.entries(SELECTORS)) {
  matchedByTool[tool] = tci.entries.filter(sel.match);
}
// divisional_facts is domain-parametrised (varga set), handled per-domain below.

// ---- build regenerated floor + coverage per domain ----------------------------------
const regenFloors = [];
const coverageResults = [];

for (const domain of DOMAINS) {
  const primaryVargas = primaryVargasFor(domain);
  const floorVargas = [...new Set([...UNIVERSAL_VARGAS, ...primaryVargas])].sort();

  // ---- assemble floor items (the regenerated, TCI-derived floor) ----
  const floorItems = [];

  // divisional_facts — one item per floor varga, each backed by its chart_divisionals concept.
  for (const varga of floorVargas) {
    const concept = divByVarga.get(varga);
    floorItems.push({
      floor_tool: 'divisional_facts',
      live_tool: 'ganita_positions_get',
      serving_args: { chart_id: '<chart_id>', varga },
      classical_role: UNIVERSAL_VARGAS.includes(varga)
        ? 'universal_foundation' : 'omega2_primary_for_domain',
      covered_concept_ids: concept ? [concept.concept_id] : [],
      covered_count: concept ? 1 : 0,
    });
  }

  // the family-based floor tools (AV / special lagna / argala / dispositor / mechanism / cross-ayanamsha)
  for (const [tool, sel] of Object.entries(SELECTORS)) {
    const agnostic = !!sel.agnostic_universal;
    const covered = matchedByTool[tool].filter((e) =>
      agnostic ? isAgnostic(e.concept_id) : domainRelevant(e.concept_id, domain));
    floorItems.push({
      floor_tool: tool,
      live_tool: sel.live_tool,
      selector: sel.note,
      domain_agnostic_universal: agnostic || undefined,
      covered_count: covered.length,
      covered_sample: covered.slice(0, 5).map((e) => e.concept_id),
      covered_concept_ids: covered.map((e) => e.concept_id),
    });
  }

  regenFloors.push({
    domain,
    intent: `${domain}_deepdive`,
    omega2_primary_vargas: primaryVargas,
    floor_vargas: floorVargas,
    floor_item_count: floorItems.length,
    // strip the big id arrays from the human artifact; keep counts + samples. The full ids stay
    // available to the coverage computation below (same in-memory objects).
    floor_items: floorItems.map((it) => ({
      floor_tool: it.floor_tool,
      live_tool: it.live_tool,
      serving_args: it.serving_args,
      classical_role: it.classical_role,
      selector: it.selector,
      domain_agnostic_universal: it.domain_agnostic_universal,
      covered_count: it.covered_count,
      covered_sample: it.covered_sample,
    })),
  });

  // ---- coverage accounting (the CI gate) ----
  // Domain slice = union of covered ids across NON-agnostic floor items, ∩ Ω2 domain-relevance.
  // Agnostic-universal items (cross-ayanamsha) accounted in a separate bucket (matches Ω3's slice
  // rule, which excludes domain_agnostic concepts from S(domain)).
  const domainSliceIds = new Set();
  const agnosticSliceIds = new Set();
  const deadFloorItems = [];
  for (const it of floorItems) {
    if (it.covered_count === 0) deadFloorItems.push(it.floor_tool + (it.serving_args ? `(varga=${it.serving_args.varga})` : ''));
    for (const cid of it.covered_concept_ids) {
      if (it.domain_agnostic_universal) agnosticSliceIds.add(cid);
      else if (domainRelevant(cid, domain)) domainSliceIds.add(cid);
    }
  }

  for (const chart of CHARTS) {
    const chart8 = chart.slice(0, 8);
    const stateCounts = { served: 0, empty_for_this_chart: 0, not_computed_globally: 0, superseded_by_aggregate: 0, excluded_by_named_rule: 0 };
    const unaccounted = [];
    for (const cid of domainSliceIds) {
      const e = tciById.get(cid);
      if (!e) { unaccounted.push(cid); continue; }
      stateCounts[stateFor(e, chart)]++;
    }
    const agnostic = { served: 0, empty_for_this_chart: 0, not_computed_globally: 0 };
    for (const cid of agnosticSliceIds) {
      const e = tciById.get(cid);
      if (e) agnostic[stateFor(e, chart)]++;
    }
    const sliceSize = domainSliceIds.size;
    const accounted = Object.values(stateCounts).reduce((a, b) => a + b, 0);
    const pass = accounted === sliceSize && unaccounted.length === 0 && deadFloorItems.length === 0;
    coverageResults.push({
      domain, intent: `${domain}_deepdive`, chart_id: chart, chart8,
      floor_slice_size: sliceSize,
      accounted, unaccounted_count: unaccounted.length,
      unaccounted_sample: unaccounted.slice(0, 10),
      dead_floor_items: deadFloorItems,
      state_counts: stateCounts,
      agnostic_universal_counts: agnostic,
      served_fraction: sliceSize ? +(stateCounts.served / sliceSize).toFixed(4) : 0,
      pass,
    });
    log(`[${domain} | ${chart8}] slice=${sliceSize} served=${stateCounts.served} ` +
      `empty=${stateCounts.empty_for_this_chart} not_computed=${stateCounts.not_computed_globally} ` +
      `unaccounted=${unaccounted.length} dead_items=${deadFloorItems.length} PASS=${pass}`);
  }
}

// ---- write artifacts ----------------------------------------------------------------
const now = new Date().toISOString();
const provenance = {
  lane: 'Ω8 (Elevation Campaign v2.1, Stream γ / PŪRṆA) — floor reconciliation',
  generator: 'platform/scripts/census/generate_floor_regeneration.mjs',
  generated_at: now,
  source_tci: { path: TCI_PATH, version: tci.version },
  source_relevance_map: { path: RELEVANCE_PATH, version: rel.version },
  method_note:
    'Floors regenerated FROM the TCI slice + Ω2 relevance map (NEVER hand-curated). divisional_facts ' +
    'vargas = universal {D1,D9} ∪ Ω2-primary(domain); ashtakavarga_scan = full D1+per-varga AV family; ' +
    'special_lagna_read = full lagna+saham+upapada set; argala/dispositor/mechanism/cross-ayanamsha added ' +
    'as domain-relevant floor items. Coverage accounted into the five Ω3 states (SAME rule as C7/Ω3).',
};

writeFileSync(join(CAP_MAP, 'REGENERATED_FLOORS_v1_0.json'), JSON.stringify({
  artifact: 'REGENERATED_FLOORS',
  version: '1.0',
  status: 'GENERATED',
  ...provenance,
  cross_manifest_wiring_note:
    'The floor CONSUMER (VIDHI_INTENT_FLOORS in platform/src/lib/vidhi/registry_data.ts and its DB seed ' +
    'vidhi_intent_floors / vidhi_floor_items, migration 440) is OUTSIDE γ\'s manifest. This artifact is the ' +
    'correct TCI-derived floor DATA, ready for α (or a later pass) to wire in — PARKED-HONEST, blocked-on-α. ' +
    'Same pattern Lane E used for rank_vocabulary.ts.',
  domains: regenFloors,
}, null, 2) + '\n');

writeFileSync(join(CAP_MAP, 'FLOOR_COVERAGE_ACCOUNTING_v1_0.json'), JSON.stringify({
  artifact: 'FLOOR_COVERAGE_ACCOUNTING',
  version: '1.0',
  contract_id: 'C7-floor',
  status: 'GENERATED',
  ...provenance,
  gate_rule:
    'For each (domain × chart): served + empty_for_this_chart + not_computed_globally + ' +
    'superseded_by_aggregate + excluded_by_named_rule == 100% of the floor\'s own TCI-derived slice; ' +
    'AND every floor item resolves to ≥1 TCI concept (no dead/fabricated floor item). Same accounting ' +
    'states as Ω3/C7. superseded/excluded intentionally 0 (TCI lacks subsumption edges; slice audit ' +
    'must not surface excluded — mirrors Ω3\'s SUPERSEDED_NOTE).',
  all_pass: coverageResults.every((r) => r.pass),
  results: coverageResults,
}, null, 2) + '\n');

log(`\nwrote REGENERATED_FLOORS_v1_0.json + FLOOR_COVERAGE_ACCOUNTING_v1_0.json`);
log(`all_pass=${coverageResults.every((r) => r.pass)}`);
log('DONE');
