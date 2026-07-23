---
artifact: STATIC_VIDHI_AUDIT
type: STATIC (pre-run) AUDIT of the Vidhi planning layer — reads code, runs nothing
initiative: UAT-DARPANA (pre-flight; feeds the battery and the §6.2 Vidhi track)
version: 1.1
status: CLOSURE RECORD — VIDHI-PŪRṆATĀ wave (native directive, 2026-07-23) closed all of
  F1-F7 + F9 against this audit. Sonnet Coordinator + Opus sub-agents (high→max effort),
  verifier-gated, executed on worktree `wave/vidhi-purnata/open`. Independent fresh-context
  Opus Gate ran twice: first pass FAILED on two narrow issues (F9 self-contradiction; F4
  Moon omission), both fixed, re-Gate PASSED all 8 criteria. This document supersedes
  v1.0's findings with their closure disposition; v1.0 is retained below unmodified as the
  finding base (§2 original) with a closure ledger appended (§2.1).
predecessor: STATIC_VIDHI_AUDIT_v1_0.md (COMPLETE, Fable 5, 2026-07-23 — the finding base)
governing_wave: 00_ARCHITECTURE/llm_consumption_audit/briefs/vidhi_purnata/BRIEF_VIDHI_PURNATA_v1_0.md
sources_read:
  - platform/src/lib/vidhi/registry_data.ts        (canonical VIDHI_PRIMITIVES, VIDHI_INTENT_FLOORS)
  - platform-mcp/src/resources/vidhi/registry_data.ts  (generated mirror)
  - platform/src/lib/vidhi/compiler.ts / platform-mcp/src/resources/vidhi/compiler.ts
  - platform-mcp/src/resources/vidhi/scope_resolver.ts (resolveScopeTuple + keyword fallback)
  - platform-mcp/src/tools/intent_scope_classifier.ts (DR-8 authoritative classifier)
  - platform/src/lib/vidhi/cr_status.ts / mirror (OPEN_CRS / CLOSED_CRS)
  - platform/migrations/462_vidhi_purnata_seed.sql, 463_vidhi_purnata_gate_fix.sql
---

# STATIC VIDHI AUDIT v1.1 — closure record for VIDHI-PŪRṆATĀ

## §1 — Closure summary

| Finding | Severity (v1.0) | Disposition | Evidence |
|---|---|---|---|
| F1 — no spirituality/education/progeny deepdive | HIGH — native-critical | **CLOSED** | 3 new `IntentClass` values + worked floors (24/23/19 items) reachable via enum, `intent_classify` `DOMAIN_RULES`, fallback keywords, `DOMAIN_TO_INTENT` bridge |
| F2 — marriage floor has no timing spine | HIGH | **CLOSED** | `taranga_curve` domain=marriage + `dasha_spine_lord_capability` added to `MARRIAGE_DEEPDIVE_ITEMS` machine band |
| F3 — marriage floor missing Jaimini spouse tools + dusthāna axis | MEDIUM-HIGH | **CLOSED** | `upapada_read` (UL + 2nd-from-UL derivation) + `chara_karaka_read` DK + bhava_condition H2/H8 added |
| F4 — health floor missing longevity/āyurdāya + 8th house | MEDIUM-HIGH | **CLOSED** (fixed on re-gate) | `ayurdaya_read`→`ganita_ayurdaya_get`, `medical_read`→`ganita_medical_get`, bhava_condition H8, karaka_condition Saturn **+ Moon** (Moon was missing on first Gate pass — FAIL-2, fixed, re-verified PASS) |
| F5 — naive-user depth trap (machine band silently stripped) | MEDIUM | **CLOSED** | depth is now intent-driven (`defaultDepthForIntent`), not keyword-gated; keyword depth gate deleted from `scope_resolver.ts` |
| F6 — intervention trap (remedies stripped without magic word) | LOW-MEDIUM | **CLOSED** | `defaultInterventionForIntent(intent)` — a domain deepdive includes the remedy/intervention layer by default; a keyword can still *add* it to a reduced intent, never required to keep it |
| F7 — career floor: Amātyakāraka absent | LOW | **CLOSED** | `chara_karaka_read` AmK added to `CAREER_DEEPDIVE_ITEMS` |
| F8 — plan ≠ delivery (dark primitives cap coverage) | MEDIUM | **HONORED, not closed by design** | Per the wave's honesty line (brief §0), this wave adds floor coverage and honestly flags what's dark — it does not fabricate data to close F8. See §3 surviving data-gap backlog. |
| F9 — possible register staleness (`dhana_yoga_scan` CR-56) | LOW — reconcile | **CLOSED** | Live-probed: `ganita_yoga_firings_get` fires `dhana_yoga_house_lords`. `known_gap` flipped `'CR-56'` → `null`; CR-56 moved `OPEN_CRS` → `CLOSED_CRS` (mirrors the CR-59/`nbry_scan` precedent). First Gate pass caught a self-contradiction (registry asserted the family both "absent" and "confirmed firing" in two places) — fixed, re-verified internally consistent. |

**Depth-default inversion (P-1, doctrine ruling)** is verified in the *compiled output*, not just the source: a keyword-free "tell me about my money" compiles the full `wealth_deepdive` floor + machine band + elevation tail; the equivalent naive spirituality question compiles the full `spirituality_deepdive` floor. No magic word required.

**Elevation lanes E-0 through E-7 (P-3b)** all landed in this pass — none deferred to a follow-on:
- E-0 Pūrṇa-Ādhāra foundational floor replaces the 6-item `general_synthesis` stub with a ~24-item layered whole-chart foundation (digest/rollup first, `hardFloor`-protected), gated so it serves as a safety net (unclassifiable questions) without displacing dedicated domain floors (classifiable questions still route to their own floor — verified both directions on re-gate).
- E-1 wires `gochara_activation_read`/`gochara_forecast_read`/`election_read` into every deepdive's machine band (data reachability itself flagged `known_gap: CR-131` — the MCP probe environment could not confirm DB-direct row data; tools are registered/live).
- E-2 `standing_predictions_read` → `phala_predictive_anchors_get`, confirmation/disclosure only, in every deepdive.
- E-3 anusaraṇa one-hop expansion rules — verified structurally incapable of transitive closure (`computeAdaptiveExpansions` iterates the resolved floor once, never re-feeds its own output).
- E-4 multi-domain union — a two-domain question compiles the dedup'd union of both floors.
- E-5 `contradiction_scan` added to every deepdive's machine band.
- E-6 `lel_retrodiction` (domain-scoped) added to every domain deepdive.
- E-7 the insight band (`tail_divergence_read`→`synth_tail_divergence_get`, `mechanism_read`, `statistical_context`, upgraded `llm_extension_note` insight mandate) closes every deepdive plan, `hardFloor`-protected.

## §2 — Gate history (for the record)

1. **First Gate (fresh-context Opus, max effort):** FAIL, scoped to criterion 1 only. Criteria 2-8 (depth-default inversion, honesty ledger, determinism + three-copy parity, E-3 one-hop cap, E-4 union, E-0 dual gate, no-fabrication) independently verified PASS on the first pass already.
   - FAIL-1: F9 self-contradiction (see above).
   - FAIL-2: F4 health floor missing `karaka_condition {karaka:'moon'}` — explicitly named in both this audit's F4 text and the governing brief's §A floor design, data-backed, simply omitted.
2. **Fix pass:** both issues corrected in the canonical registry + both mirrors + a new surgical migration (`463_vidhi_purnata_gate_fix.sql`), full vidhi suite re-run green (46 platform + 21 platform-mcp tests).
3. **Second Gate (fresh-context Opus, independent, no memory of the fix pass's self-report):** re-ran the full 8-criterion checklist from scratch (not just the two deltas, to catch any regression the fix could have introduced) — **PASS**, no residual issues, no new defects.

## §3 — Surviving data-gap backlog (honesty ledger; not fabricated, not blockers for this wave)

Per the wave's binding honesty line: every floor item this wave added resolves to a live tool OR carries a truthful `known_gap:<CR>`. The following are OPEN and logged in `cr_status.ts` — planner coverage now correctly *asks* for these aspects; the data layer is the surviving ceiling, not the planner:

| Primitive | CR | Gap |
|---|---|---|
| `spiritual_yoga_scan` | CR-130 | Jaimini "spiritual" yoga family (pravrajyā/sannyāsa) not present as a `family_ids` key on `ganita_yoga_firings_get` — new gap surfaced by this wave's P-0 probe, not fabricated. |
| `gochara_activation_read` / `gochara_forecast_read` / `election_read` | CR-131 | Tools are registered/live; row-level data reachability could not be confirmed through the probe connector (`DATABASE_URL not set`, DB-direct required). Not proof of empty — needs confirmation in a DB-connected runtime. |
| `upapada_read` | CR-61 (pre-existing) | UL/arudha positions are stored and served raw; RANKING (which arudha dominates) remains the open gap. |
| `taranga_curve` (education domain) | CR-66 (pre-existing) | Live probe surfaced only transition/health/career phala-domain anchors in the top-6 sample; no education-domain anchor confirmed. Flagged, not assumed empty — needs a domain-filtered re-probe. |
| 2nd-from-UL, from-karakāṃśa 12th, beeja/kshetra sphuta | none (derivation) | Computed from data-backed facts (UPA position, karakāṃśa), not a distinct stored fact — no dedicated tool exists to verify against; flagged as a derivation, not faked. |

**One item explicitly outside this wave's scope, surfaced for the data team (not fixed here — `must_not_touch`):** the D7 `chart_divisionals` writer's `varga_karya_bhava` row reads `spouse_karya` for Saptāṃśa (classically progeny/5th, never spouse/7th) — a genuine L1 writer mislabel, not intentional multi-use tagging. The `progeny_deepdive` floor was deliberately keyed off H5/Jupiter/PuK/D7-facts instead of this label to avoid propagating the bug. Recommend a new data-team CR to fix the L1 write; out of scope for a Vidhi-registry wave.

**One pre-existing, non-blocking observation from the re-gate** (not introduced by this wave): the coarse MCP fallback-keyword regex for marriage matches "marriage"/"spouse" but not "married"/"marry" — `resolveScopeTuple('when will I get married')` falls through to `general_synthesis` on the fallback path (the authoritative `intent_classify` path is unaffected). This is the deliberately-coarse V-2 fallback design (defers to the authoritative classifier); worth a follow-up keyword-coverage note, not gate-blocking.

## §4 — What this means for UAT-DARPANA

Per the governing brief §4: this closure re-confirms F1-F7 + F9 closed against the fixed planner. UAT-DARPANA may now open its dynamic run against this planner. The §6.2 Vidhi track's replay should confirm empirically that the previously-planned-but-dark gaps (F8's cluster, plus this wave's own CR-130/131/66/61) are attributed correctly to the data layer rather than the planner in the Synthesist's cross-read — the planner now asks for everything an acharya would; what remains dark is a data-layer ceiling, honestly disclosed.

## Appendix — v1.0 original findings (unmodified, for reference)

See `STATIC_VIDHI_AUDIT_v1_0.md` for the full original text (§0-§5, sources_read, the original severity-ranked F1-F9 write-ups and R1-R6 candidate remediations). This v1.1 does not restate it in full; §1 above is the closure ledger against those exact findings.
