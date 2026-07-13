---
artifact: NIGHT1_LANE5_DENSITY_RETROFIT
type: IMPLEMENTATION BRIEF (Sonnet-executable, self-contained)
version: 1.0
status: READY
campaign: Doctrine Campaign D-1 / Night-1
lane: L5 — §N.6 Serving Density Principle retrofit (scoped to surfaces touched by Lanes 1–4 ONLY)
depends_on_lanes: LANE3 + LANE4 merged (their outputs define what these tools serve); runs alongside their rebuild verification
register_rows: CR-45 (serving half), CR-43/CR-72 (serving gate), CR-50, CR-10/CR-42 (facet honesty, on touched tools only), CR-11 (empty_reason, touched tools only), CR-13/CR-49 (budget, touched tools only), CR-55 (handoff from Lane 4 if serving-side)
design_ref: DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §6 (§N.6 statement), §8 (build/serve split)
---

# LANE 5 — §N.6 density retrofit on the D-1-touched serving surfaces

## 0. The principle (design §6, quoted — this IS the spec)

> **§N.6 Serving Density Principle** … binding on every current and future asset/service — *(i)* family-collapse + dedup **at the writer**; *(ii)* projection facets honored **or rejected loudly** (kills the CR-42 silent-wrong-answer class forever); *(iii)* layered envelope (verdict ≤1KB → digest ≤4KB → paginated rows) as the only response shape; *(iv)* a per-tool **density contract** in the capability map enforced by the census harness in CI. A new asset that violates density fails its gate.

**Scope narrowing (binding, from the campaign design's "binds new/modified assets" rule):** this lane applies §N.6 to the tools/writers Lanes 1–4 touched — NOT estate-wide. Estate-wide retrofit is explicitly not tonight's job.

## 1. Exact scope — the touched-surface list

Serving registry lives at `platform/src/lib/retrieval/registry/layers/` (TypeScript; per-layer folders `L0_brahmagyan` … `L5_mimamsa`, plus `register_d5..d10_*.ts` composite tools). The existing `empty_reason` pattern (present in e.g. `L1_ganita/get_ayurdaya.ts`, `register_d7_channel.ts`) and the C1 budget discipline are your in-repo precedents — read two of those files before writing anything.

| Surface (deployed tool name) | File (locate by grep, verified folder) | Why it's in scope | §N.6 work |
|---|---|---|---|
| `ganita_structural_get` | `layers/L1_ganita/` (grep `ganita_structural_get`; `get_yoga_dosha.ts` is adjacent) | Lane 1 modularized its writer; Lane 3 changed dosha semantics | (ii)+(iii); serve `catalog_only`/`fires` honestly — a `dosha_label` with `fires:null` must NEVER render as a finding (CR-72/CR-43 serving gate); CR-50: default ordering leads with the nine grahas + lagna, upagraha/aprakasha rows behind an explicit facet |
| `ganita_yogas_get` | `layers/L1_ganita/get_yoga_dosha.ts` | Lane 3 added detector firings | verdict must count served `yoga_label`/`yoga_fires` rows (CR-33 fix — never assert "not formed" from absence-in-page); separate `fired` vs `catalog` sections (CR-43); new detector firings served with grounds jsonb |
| NEW: `ganita_vichara_get` | new file `layers/L1_ganita/get_vichara.ts` (mirror the closest existing L1 tool's registration pattern end-to-end, including how it lands in the deployed tool census) | Lane 2's asset needs a serving face — a dark asset repeats CR-76's computed-then-dark failure | born §N.6-conformant: layered envelope; facets `family` (valence_pass/varga_ratification/varga_ratification_divergence/varga_consistency/leverage_index), `domain`, `subject`; loud facet rejection; empty_reason |
| `bodha_signals_get` (+ alias `get_signals`) | `layers/L2_bodha/query_signals.ts` | Lane 4 changed tiers/valence/headlines/columns | expose `ratification_factor` + `valence_source` in rows; verdict ≤1KB states tier distribution + top subjects; digest ≤4KB; rows paginated; facets honored-or-rejected |
| `judgment_query` | `layers/register_d9_judgment.ts` | consumes MSR tiers/valence — Lane 4 changed its substrate | receipt honesty ONLY where cheap (see anti-scope: CR-1/CR-63 timing_hooks wiring is D-3's temporal cluster — do NOT wire dasha joins tonight; DO make the receipt stop claiming `varga_confirmation`/`timing_anchored` success over empty payloads — an honest `false` is one line) |
| `bodha_chart_digest_get` / orientation digest | grep `weakest_graha` in `platform/src` | CR-55 handoff from Lane 4 if the false fact is serving-side | fix the computation to shadbala-based, or consume Lane 4's fixed value; must say VENUS for 482012f1 |

If a Lane-1–4 change touched a tool not on this list (check each lane's handback report), add it under the same rules; if a tool on this list turns out untouched by Lanes 1–4, drop it and say so in your report.

## 2. The three §N.6 mechanics, concretely

### (iii) Layered envelope — the only response shape
Every scoped tool returns: `verdict` (≤1KB: the one-paragraph machine-usable answer + counts + as_of/build_id), `digest` (≤4KB: family-grouped summaries), `rows` (paginated, default page small enough that verdict+digest+page-1 ≤ 12KB — the estate's C1 budget; CR-13/CR-49's oversize family must not gain members). Enforce sizes in code (byte-length check + trim with an explicit `trim_report`), not by hope. If the repo already has a shared envelope helper (grep `trim_report`/`verdict` in `src/lib/retrieval/`), extend it rather than hand-rolling per tool — design §2 names "one shared envelope library" the target shape; move toward it, don't fork it.

### (ii) Facets honored or rejected loudly
Every documented filter/facet param either (a) filters the actual corpus, or (b) returns an error naming the unsupported value + the supported vocabulary. **Never** proceed unfiltered after dropping a filter (CR-42: "a dropped filter must never degrade to a different corpus"; CR-10: case-insensitive normalization for planet/subject vocab — `Venus`≡`venus`≡`VENUS`).

### (i) Family-collapse + honest emptiness
Row lists group by family with member counts; identical-member families collapse to one line + count (CR-4/CR-29 pattern). Zero-row responses carry `empty_reason` naming the cause (CR-11) — including the new distinction "0 fired (N catalog-only rows exist, facet `include_catalog=true` to see them)".

### (iv) Density contract in the capability map
Find where the deployed tool census / capability map defines per-tool metadata (start: `00_ARCHITECTURE/llm_consumption_audit/DEPLOYED_TOOL_CENSUS_2026-07-13.md` for the shape, and grep `capability` under `platform/src/lib/retrieval/`). For each scoped tool add/annotate: `{max_verdict_bytes: 1024, max_digest_bytes: 4096, paginated: true, facets: [...], empty_reason: true}`. If a CI census harness exists (grep `census` in `.github/workflows` + `platform/src`), register the checks there; if it does not exist yet, land the contract data + a unit test per tool asserting the byte caps, and note "CI harness enforcement pending" in your report — do NOT build a new CI harness tonight.

## 3. Tests

Per scoped tool (follow the existing `*.integration.test.ts` / `*.test.ts` patterns in the registry folders): (a) envelope size caps respected on a fat fixture; (b) unknown facet value → loud rejection payload, not unfiltered fallback; (c) case-insensitive subject facet; (d) empty corpus → `empty_reason`; (e) tool-specific: `ganita_yogas_get` fired/catalog separation with a `catalog_only` fixture row; `bodha_signals_get` exposes `ratification_factor`/`valence_source`; `ganita_structural_get` default ordering (first rows are the nine grahas + lagna); digest `weakest_graha` = shadbala-min. Run the repo gate: `/run-checks` equivalent (ESLint + TypeScript + tests) green.

## 4. Acceptance criteria

- [ ] All scoped tools return the layered envelope with enforced byte caps; none exceeds 12KB at default args (CR-49 regression check on exactly these tools).
- [ ] `ganita_vichara_get` exists, is registered on the same path other L1 tools reach the deployed census through, and serves Lane 2's five families with facets.
- [ ] No scoped tool silently drops a filter (test-proven per tool).
- [ ] `dosha_label`/`yoga_label` catalog-only rows cannot be read as findings on any scoped tool (CR-72/CR-43 serving gate closed).
- [ ] `ganita_yogas_get` verdict counts its own served rows (CR-33 closed on this tool).
- [ ] `ganita_positions_get`-class default ordering: nine grahas + lagna first (CR-50) — on `ganita_structural_get` and, ONLY if Lanes 1–4 touched it, `ganita_positions_get`.
- [ ] Digest/orientation surfaces report `weakest_graha=VENUS` for 482012f1 (CR-55 closed wherever it lives).
- [ ] `judgment_query` receipt no longer claims success over empty sections (honest flags; no new joins).
- [ ] Density contracts landed in the capability map data for every scoped tool.
- [ ] TypeScript + ESLint + test suite green (the repo's 14/14 CI gate).

## 5. Known traps

- **Scope discipline is the trap.** CR-11/CR-42/CR-49 list dozens of offending tools estate-wide. You fix ONLY the touched list. Every extra tool you "quickly fix" is unreviewed blast radius on the merge train.
- **CR-51 (alias divergence)**: where a scoped tool has a twin alias (`get_signals`/`bodha_signals_get`), both faces must serve the identical payload after your change — test the pair, or you create a new CR-51 instance. Do not deprecate aliases tonight (that's D-2's CR-30/51 work).
- **CR-44 class**: do not let tool descriptions promise keys the payload lacks — if you add `ratification_factor` to the description, it must be in the payload, and vice versa.
- **Locked UI decisions** (platform/AGENTS.md): you are in serving/lib code only — do not touch `ConsumeChat.tsx`/`Composer.tsx`.
- **This Next.js is not the one you know** (platform/AGENTS.md): read `node_modules/next/dist/docs/` guidance before touching any route-adjacent file.

## 6. Anti-scope

- NO estate-wide retrofit (the design's narrowing is explicit).
- NO vidhi engine, two-pass SCAN/FETCH retrieval, capability-map live source (CR-9), alias deprecation, drill_pointers — all D-2 (§6's other half).
- NO temporal fixes: timing_hooks wiring, kala/activation joins, sidecar auth (CR-1/5/8/12/40/41/48/63 → D-3 supersession; §I.1: CR-41 is superseded, "do not spend effort repairing the L3 forward-projection writer").
- NO Python writer changes (Lanes 1–4 own those; if a serving fix "needs" a writer change, hand it back via CONDUCTOR).
- NO chart rebuilds/deploys (CONDUCTOR).

## 7. Done-definition / handback

Worktree branch: tool changes + new vichara face + contracts + tests, `/run-checks` green. Report: per-tool before/after payload sizes at default args, facet vocabulary per tool, where the CR-55 fix landed, any touched-tool list deltas, §4 checklist.
