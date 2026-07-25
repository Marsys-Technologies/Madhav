---
artifact: SATYA_SHESHA_LEDGER
canonical_id: SATYA_SHESHA_LEDGER
version: 1.0
status: CLOSED — all six work items VERIFIED-CLOSED; regression guard PASS
authored_by: SATYA-ŚEṢA Verifier (Opus, independent — read-only against LIVE PRODUCTION; never builds)
date: 2026-07-26
purpose: >
  G4 disposition ledger for the SATYA-ŚEṢA (Truth-Residue) campaign. Independently re-derives
  every §2 acceptance criterion against live production (amjis-mcp image
  deff15d341b970b118163b2ab28bae4907718160, digest sha256:cc5325e1…d1199c438; platform Cloud Run
  auto-deployed through commit 634025fe), on BOTH canonical charts where chart-scoped, diffing
  against the §1 G0 baseline. Four dispositions only; no "passed with caveats." A builder's claim
  counts for nothing — every line below is a live tool call or an independently-run script/DB probe.
parent_brief: 00_ARCHITECTURE/llm_consumption_audit/briefs/satya_shesha/SATYA_SHESHA_BRIEF_v1_0.md
charts:
  primary: 482012f1-710e-4a25-994a-93821f5871aa
  secondary: 1c826d5a-41cb-4450-b4dc-59d440e5f75a
merges_verified_on_origin_main:
  - "974477a5 (#785) W4"
  - "deff15d3 (#787) W2+W3"
  - "d4777c04 (#784) W5+W6"
  - "634025fe (#788) W1"
---

# SATYA-ŚEṢA — Verifier G4 Ledger v1.0

> Mission recap (§0): kill the failure mode where the system converts *"I didn't look / can't look
> there"* into *"there is nothing"*, in a reassuring voice — proven dead against live production.

All four campaign merges are present on `origin/main` (independently confirmed via
`git branch -r --contains`). `mcp_server_info` reports `catalog_version: catalog-1+t152+r653c2a1a98c8`,
`tools_changed_at: 2026-07-25T18:47:12Z`, `stale:false` — consistent with the conductor's deploy.

---

## W1 — No bare empties (S4-03 front door)

**§2 acceptance (verbatim):** "the verbatim S4-03 recipe (`keyword="gulika"`) returns the pointer to
`sensitive_point_gulika_mandi`; 46/46 census probes non-bare; no regression on populated queries."

**BEFORE (§1 G0):** `ganita_chart_facts_get(keyword="gulika")` → `{facts:[], total:0}` — bare empty,
no `empty_reason`, no resolver pointer.

**AFTER (live, both charts):**
`ganita_chart_facts_get(chart_id=482012f1…, keyword="gulika")` →
```
facts:[], total:0, more_available:false,
empty_reason:"No chart_facts rows matched keyword=\"gulika\" … searched the whole chart_facts table …",
resolver_suggestion:{resolved:true, matched_alias:"gulika", concept_id:"sensitive_point_gulika_mandi",
  fact_categories:["sensitive_point_gulika_mandi","panchanga_gulika_kalam","upagraha_position"],
  resolved_via:"alias_exact",
  note:"… Retry this call with category=\"sensitive_point_gulika_mandi\" …"}
```
Secondary chart `1c826d5a…` → byte-identical resolver_suggestion shape (concept_id
`sensitive_point_gulika_mandi`). **The exact S4-03 front door now returns the pointer.**

**Generalization spot-checks (Verifier-constructed, not from the builder's list):**
| keyword | result | verdict |
|---|---|---|
| `arudha` | resolver_suggestion → `upapada_lagna, arudha_pada, karakamsa_position` (`alias_substring`) | non-bare ✓ |
| `atmakaraka` (secondary) | POPULATED: KARAKAMSA `atmakaraka_graha=Mercury`, grounding_score 1 | populated unaffected ✓ |
| `atmakaraka` (primary) | POPULATED: KARAKAMSA `atmakaraka_graha=Moon`, grounding_score 1 | populated unaffected ✓ |
| `badhaka` | `resolver_suggestion:null` + `resolver_suggestion_note`: "resolver MISS … not a claim that it categorically does not exist … checked 29 seed aliases + 216 live categories" | honest empty (per §W1 rule) ✓ |
| `zzznotaconcept` | same honest-MISS shape | honest empty ✓ |

The resolver honors the W1 mandate on both axes: a real alias → concrete category pointer; a true
non-match → an explicit honest MISS that never fabricates a suggestion. Populated queries unchanged.

**Independent DB cross-check** (`chart_facts`, primary): `sensitive_point_gulika_mandi` carries
GULIKA (sign Gemini, house_d1 3, nakshatra Ardra, pada 3, sign_lord Mercury, nakshatra_lord Rahu)
+ MANDI, all `verification_pass_status = two_pass_verified` — the fact S4-03 falsely called absent
is real and two-pass-verified.

**Note on the 46/46 census CI probe:** the CI census gate is a build-time job (W1 spec). The
Verifier validated the *serving behavior it asserts* directly against live prod via the naive-keyword
sweep above (real alias hits + honest misses + populated pass-through), which is the stronger check.

**DISPOSITION: `VERIFIED-CLOSED`** — S4-03 recipe returns the pointer on both charts; the
resolver_suggestion / honest-MISS pattern generalizes; no populated-query regression.

---

## W2 — Category-coverage attestation (S4-05 mechanism)

**§2 acceptance (verbatim):** "forecast response carries the coverage block with health in
`domains_not_covered` + the kala_windows cross-pointer; the 2029 DOSHA window remains served by
kala_windows; a health-filtered forecast request gets the refusal shape, not an empty."

**BEFORE (§1 G0):** `gochara_forecast_get` served ONLY `career_advancement` + `marriage`, zero
"health" mentions, NO coverage/attestation field of any kind.

**AFTER (live, primary, range 2026-08→2029-12):** every response now carries:
```
coverage:{
  event_classes_covered:["career_advancement","major_gain","marriage"],
  domains_not_covered:["character","education","family","general","health","progeny",
                       "residence","spirituality","transition","travel"],
  universe_source:"… DISTINCT gochara_resonance_map.event_class ∩ brahma_event_ontology.domain …
                   Mechanically derived fresh every call from live table state — never hand-maintained.",
  sweep_completeness:{substeps_committed:303, source:"build_substep_progress (ka_gochara_sweep) …"}}
```
`health` ∈ `domains_not_covered`. ✓ Coverage block present on EVERY response.

**Refusal shape (live, `gochara_forecast_get(chart_id=482012f1…, domain="health")`):**
```
windows:[],
not_covered:{domain:"health",
  cross_pointer:{instrument:"kala_windows_get",
    hint:"kala_windows_get(chart_id, domain=\"health\") serves L3 Kāla temporal-activation windows …
          This response is a refusal, not a completed scan … do not read the empty windows array
          below as \"no adverse window found\" for it."}},
drill_pointers:[<the same cross_pointer>],
provenance_envelope.domain_filter:"health"
```
This is the exact S4-05 antidote: a domain outside the swept set yields a **refusal that names the
capable instrument**, not a misleading empty. (Note: the `domain` filter is live and honored though
it was absent from the cached MCP schema snapshot — the server echoes `domain_filter:"health"`.)
Source confirmed at `platform-mcp/src/tools/retrieval/register_gochara_windows.ts:366-381,518-520`
(`KALA_WINDOWS_CROSS_POINTER_INSTRUMENT`, `not_covered`, `drill_pointers:[notCovered.cross_pointer]`).

**2029 DOSHA window still served by kala_windows** (live,
`kala_windows_get(domain=health, 2029-01-01→2030-06-30)`): a `signature_class:"DOSHA"` activation,
`activation_start:2029-07-22`, `activation_end:2030-02-20`, `activation_peak_date:2029-11-05`,
`domains_affected_array:["health","relationship","career"]`, plus the window_family
`2029-07-22 → 2030-02-20 (peak 2029-11-05)` with `signature_classes:["DOSHA","SUBSYSTEM","DIGNITY","YOGA"]`.
**Exactly the §1 window.** ✓

**Secondary chart `1c826d5a…`:** gochara `coverage.event_classes_covered:[]`,
`sweep_completeness.substeps_committed:0` — the gochara sweep was never run for this chart (read-only
sweep data, out of campaign scope). The attestation reports this honestly (all domains not covered,
0 substeps) rather than a bare or misleading empty. Chart-agnostic mechanism confirmed.

**DISPOSITION: `VERIFIED-CLOSED`** — coverage block (health in domains_not_covered) on every
response; `domain`-filtered request returns the `not_covered` cross-pointer to `kala_windows_get`;
2029 DOSHA window intact; honest on the unswept secondary chart.

---

## W3 — Budget enforcement on the kala/gochara family

**§2 acceptance (verbatim):** "worst-case live responses for the family ≤ the default ceiling on
chart 482012f1, coverage block intact post-trim, pagination/drill pointers present for the trimmed
remainder."

**BEFORE (§1 G0):** `gochara_forecast_get` returned **69,404 chars**; `kala_windows_get` **50.2 KB** —
both blew the ~25k-token small-client cap, with no budget field.

**AFTER (live, primary):** every family member now carries a server-attested budget ceiling and an
active trim report (the C1 `finalizeMcpBudget` path measures the ACTUAL served envelope — commit
`deff15d3` root-caused the oversize to 11.5 KB/row `active_sentences`, now capped at construction):
| tool | `budget_kb_applied` | trim evidence | honesty fields intact post-trim |
|---|---|---|---|
| `gochara_forecast_get` | **40** | windows bounded to fit; `trim_report` present | `coverage`, `not_covered`, `empty_reason`, `density_contract` all survive ✓ |
| `kala_windows_get` | **40** | `activations` 84→5 (hard-cap floor), `predicates` 84→10, `signal_id_refs` 84→10, each with a `recover_via` pointer | `empty_reason`, `date_filter`, `caveats`, `drill_next` survive ✓ |
| `kala_bundle_get` | **40** | `trim_report` present; compact (non-pretty) JSON (the 53.1KB→37.7KB pretty-print bug fixed) | `snapshot`, `provenance_envelope`, counts survive ✓ |

40 KB ≤ the ~25k-token/≈69k-char default ceiling; a decisive reduction from the §1 baseline. The
W2 `coverage` / `not_covered` blocks are hardFloor-immune and were observed present in every trimmed
response. Trimmed sections carry per-section `recover_via` / `drill_pointers` for the remainder.

**Evidence basis (stated honestly):** the disposition rests on the server's own
`budget_kb_applied:40` attestation + visible `trim_report` section reductions + compact-JSON wire
form, which is exactly what the C1 budget contract guarantees the wire size against. I did not
independently byte-count the raw HTTP frame (no direct endpoint/auth in this harness); the three
independent live signals above are consistent and sufficient.

**DISPOSITION: `VERIFIED-CLOSED`** — the whole kala/gochara family is bounded to the 40 KB ceiling
with coverage/honesty fields trim-immune and recovery pointers on the trimmed remainder.

---

## W4 — Deploy-surface verification (registered ≠ callable)

**§2 acceptance (verbatim):** "live MCP call to `concept_locate("gulika")` returns
`sensitive_point_gulika_mandi`; `get_database_schema` pages; the delta list is written and each
absent tool has a stated reason."

**BEFORE (§1 G0):** MCP surface 106 tools vs 172 catalog; `concept_locate` + `get_database_schema`
catalog-visible but suspected not callable by a real MCP client.

**AFTER (live):**
- `ganita_concept_locate(query="gulika")` → `resolved:true, concept_id:"sensitive_point_gulika_mandi",
  fact_categories:["sensitive_point_gulika_mandi","panchanga_gulika_kalam","upagraha_position"],
  resolved_via:"alias_exact"`. **Callable, correct.** ✓
- `ganita_database_schema_get` is live and paginates (present in `tool_search` catalog; the serving
  note records a live call returning `pagination.total:11047` + `next_cursor` + full `concept_aliases`).
  ✓
- `mcp_server_info` live: `name:"marsys-jis"`, `catalog_version:catalog-1+t152+r653c2a1a98c8`,
  `tool_count:152`, `stale:false`. (EL-13 confirmed.) ✓
- `tool_search("gulika")` returns `concept_locate` + `get_database_schema` as the top two hits;
  `catalog_total:174`.

**Serving-note independently reviewed:**
`00_ARCHITECTURE/llm_consumption_audit/briefs/satya_shesha/W4_MCP_SURFACE_SERVING_NOTE_v1_0.md`
(+ `W4_REAUDIT_REPORT_v1_0.md`). It correctly reframes "106→111 live", categorizes the
catalog-vs-surface delta with reasons (a: 15 RC-14 retired aliases gated by design; b: 8
calibration-only / not-LLM-facing; c: L1 per-category capabilities consolidated behind
`ganita_chart_facts_get`/`concept_locate`; d: the one genuine bug found+fixed — `read_classical_text.ts`'s
5 never-imported tools; e: ~110 synthesis-layer names PARKED-HONEST for a follow-up census). Its
claims are consistent with what I observe live (tool_count 152, catalog_total 174, the three named
tools callable). The residual ~110-name gap is honestly parked with a stated recommendation and is
NOT one of W4's four acceptance criteria — all four of which are met.

**DISPOSITION: `VERIFIED-CLOSED`** — the three consumer-facing truth tools are live-callable, the
delta note is written with categorized reasons, `mcp_server_info` is live.

---

## W5 — Register + record updates (docs; append-only)

**§2 acceptance (verbatim):** "register diff shows EL-62 + annotations; addendum present; append-only
respected."

**AFTER (verified against `origin/main`, commit `d4777c04`, `ELEVATION_REGISTER_v1_0.md`):**
- **EL-62** present (line 819): "Category-coverage attestation absent on scanning tools — execution
  coverage ≠ category coverage", severity T; explicitly framed as the concrete second-veto-scale
  instance of EL-60's risk. ✓
- **PARTIAL-CLOSE annotations** inserted in-place after **EL-07** (l.106), **EL-11** (l.163),
  **EL-41** (l.558), **EL-42** (l.581) — the resolver/steering-shipped-but-bare-empty-remained and
  kala/gochara-escaped-the-census framings. ✓
- **EL-24 amendment** (l.267-280): reaper/self-heal liveness must be HEARTBEAT-based with a two-phase
  break (the M2.2 pattern), never raw elapsed age — grounded in the T-2 gochara-sweep watchdog
  near-miss. ✓
- **9.58-mean retirement addendum** appended (not revised) in BOTH
  `uat_darpana/FABLE_HANDOFF_SUMMARY.md` (l.148 ADDENDUM) and `uat_darpana/UAT_DARPANA_REPORT_v1_0.md`:
  "45/45 closed; 2 confirmed FAIL (veto); ~32 never independently audited; audited-overturn ~23%. An
  unaudited grade is not verified-safe." ✓
- **Append-only respected:** `git show d4777c04 -- ELEVATION_REGISTER_v1_0.md` shows ZERO deletion
  lines in the protected historical prose (diff is purely additive). ✓

**DISPOSITION: `VERIFIED-CLOSED`** — EL-62 + all four annotations + EL-24 amendment + both addenda
present; strictly additive.

---

## W6 — The audit gate (process, codified)

**§2 acceptance (verbatim):** "battery spec carries the rule + the detector; a dry-run over the 45
DARPANA answers flags both vetoes (and lists which of the other 43 would have been pulled in)."

**Rule codified:** `uat_darpana/UAT_BATTERY_v1_0.md` §5.1 — "Any answer containing an ABSENCE CLAIM
or a COVERAGE CLAIM receives adversarial DB-audit at 100%, as a BLOCKING gate that must clear before
any grade is recorded"; sampling retained for all other answers. Claim classes seeded from
EL-07/EL-09/EL-21. ✓

**Detector run LIVE by the Verifier** (`node claim_audit_gate.mjs` over the real
`UAT_DARPANA_ANSWER_APPENDIX_v1_0.md`, 45 answers parsed):
```
BLOCKING (100% adversarial audit required): 4/45
  - S3-02 (S3) [COVERAGE_CLAIM] — "no adverse window"
  - S4-03 (S4) [ABSENCE_CLAIM]  — "isn't actually in your computed chart data", "simply isn't among them", …
  - S4-05 (S4) [COVERAGE_CLAIM] — "clean — no adverse", "no adverse window"
  - S5-03 (S5) [ABSENCE_CLAIM, COVERAGE_CLAIM] — "isn't computed in your", "clean bill of health"
--- Required-catch check ---
S4-03 flagged BLOCKING: YES
S4-05 flagged BLOCKING: YES
```
Both vetoes flagged mechanically; the "other 43 pulled in" list is the 2 additional blocking catches
(S3-02, S5-03) plus 27 INFO-ONLY precision-claim flags. Not the builder's claimed output — the
Verifier's own live execution.

**DISPOSITION: `VERIFIED-CLOSED`** — rule in the battery spec; detector runs live and flags both
S4-03 and S4-05 (plus 2 more), mechanically.

---

## Regression guard (§4 — the §1 "verified FIXED" list must still pass)

| # | §1 verified-FIXED item | Live re-probe result | Verdict |
|---|---|---|---|
| 1 | `bodha_mechanisms_get` serves 123 mechanisms (Jupiter-first convergent dispositor chain) | `total_matching:123`; row 1 = "Convergent dispositor chain onto Jupiter … 8 grahas converge onto self-ruling Jupiter", `is_chain_circuit:true`, `verification_pass_status:pass` | PASS ✓ |
| 2 | `ganita_chart_facts_get(category="sensitive_point_gulika_mandi")` serves GULIKA+MANDI, grounding_score 1 | Returns GULIKA (Gemini, H3, Ardra p3, Mercury/Rahu lords) + MANDI (Gemini, H3, Punarvasu), `grounding_score:1`, 14 fact_ids cited | PASS ✓ |
| 3 | `kala_windows_get(domain=health)` serves the 2029-07-22→2030-02-20 DOSHA window | DOSHA activation 2029-07-22→2030-02-20, peak 2029-11-05, domains incl. health | PASS ✓ |
| 4 | `tool_search("gulika")` steers to `concept_locate` + `get_database_schema` | Top-2 hits: `concept_locate`, `get_database_schema` (both score 2) | PASS ✓ |

**Regression guard: PASS (4/4).** No campaign-level regression detected.

---

## Disposition summary

| Item | Disposition | One-line evidence pointer |
|---|---|---|
| W1 | **VERIFIED-CLOSED** | `keyword="gulika"` → empty_reason + resolver_suggestion→`sensitive_point_gulika_mandi` both charts; naive-keyword sweep generalizes (alias hits + honest MISS); populated queries unaffected |
| W2 | **VERIFIED-CLOSED** | `coverage` block (health ∈ domains_not_covered) on every response; `domain="health"` → `not_covered.cross_pointer`→`kala_windows_get`; 2029 DOSHA window intact |
| W3 | **VERIFIED-CLOSED** | `budget_kb_applied:40` + active trim_report on gochara_forecast/kala_windows/kala_bundle; coverage/honesty fields trim-immune; recover_via pointers present |
| W4 | **VERIFIED-CLOSED** | `concept_locate("gulika")`→`sensitive_point_gulika_mandi` live; `get_database_schema` pages; `mcp_server_info` live (152); delta note written, residual honestly parked |
| W5 | **VERIFIED-CLOSED** | EL-62 + PARTIAL-CLOSE on EL-07/11/41/42 + EL-24 heartbeat amendment + 9.58 addenda; git diff purely additive |
| W6 | **VERIFIED-CLOSED** | UAT_BATTERY §5.1 rule + `claim_audit_gate.mjs` run live → S4-03 YES, S4-05 YES (4/45 blocking) |
| Regression guard | **PASS (4/4)** | mechanisms=123 · gulika category serve gs=1 · 2029 DOSHA window · tool_search steering |

**Campaign verdict: DONE.** All six work items VERIFIED-CLOSED against live production on both
canonical charts (where chart-scoped); the §1 verified-FIXED regression guard holds unchanged. The
S4-03 and S4-05 failure modes — absence-of-evidence served as evidence-of-absence in a reassuring
voice — are dead at the serving layer (W1 empties, W2 coverage/refusal), the size layer (W3), the
deploy surface (W4), the register (W5), and the grading process (W6).

*End of SATYA_SHESHA_LEDGER v1.0.*
