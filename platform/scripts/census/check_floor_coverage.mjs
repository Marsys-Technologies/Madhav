#!/usr/bin/env node
/**
 * check_floor_coverage.mjs — Elevation Campaign v2.1, Stream γ (PŪRṆA), Lane Ω8 CI gate.
 *
 * The floor-coverage gate. Reads FLOOR_COVERAGE_ACCOUNTING_v1_0.json (produced by
 * generate_floor_regeneration.mjs) and enforces, for every (domain × chart) floor:
 *
 *   1. 100%-accounting: served + empty_for_this_chart + not_computed_globally +
 *      superseded_by_aggregate + excluded_by_named_rule == floor_slice_size  (the SAME five-state
 *      rule Ω3/C7 uses).
 *   2. zero unaccounted concepts.
 *   3. zero dead/fabricated floor items (every floor item resolves to ≥1 real TCI concept).
 *
 * Exit 0 iff all floors pass; exit 1 (build-failing) otherwise, with a per-floor diagnostic.
 * Regenerate the accounting first: `node platform/scripts/census/generate_floor_regeneration.mjs`.
 */
import { readFileSync, existsSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CAP_MAP = resolve(__dirname, '../../..', '00_ARCHITECTURE/llm_consumption_audit/capability_map');
const ACC = process.env.FLOOR_ACCOUNTING_PATH || join(CAP_MAP, 'FLOOR_COVERAGE_ACCOUNTING_v1_0.json');

if (!existsSync(ACC)) {
  console.error(`FAIL: floor-coverage accounting not found at ${ACC}\n` +
    `Run: node platform/scripts/census/generate_floor_regeneration.mjs`);
  process.exit(1);
}

const acc = JSON.parse(readFileSync(ACC, 'utf8'));
const results = acc.results || [];
let failures = 0;

for (const r of results) {
  const sc = r.state_counts || {};
  const summed = Object.values(sc).reduce((a, b) => a + b, 0);
  const reasons = [];
  if (summed !== r.floor_slice_size) reasons.push(`accounting ${summed} != slice ${r.floor_slice_size}`);
  if (r.unaccounted_count > 0) reasons.push(`${r.unaccounted_count} unaccounted`);
  if ((r.dead_floor_items || []).length > 0) reasons.push(`dead floor items: ${r.dead_floor_items.join(', ')}`);
  if (r.pass !== true) reasons.push('pass flag false');
  const ok = reasons.length === 0;
  if (!ok) failures++;
  const tag = ok ? 'PASS' : 'FAIL';
  process.stdout.write(
    `[${tag}] ${r.domain} | ${r.chart8}  slice=${r.floor_slice_size} ` +
    `served=${sc.served} empty=${sc.empty_for_this_chart} not_computed=${sc.not_computed_globally}` +
    (ok ? '' : `  <- ${reasons.join('; ')}`) + '\n');
}

const total = results.length;
process.stdout.write(`\nFloor-coverage gate: ${total - failures}/${total} floors PASS ` +
  `(${acc.artifact} v${acc.version}, all_pass=${acc.all_pass})\n`);

if (failures > 0 || total === 0) {
  console.error(`GATE FAILED: ${failures}/${total} floor(s) not 100%-accounted`);
  process.exit(1);
}
process.exit(0);
