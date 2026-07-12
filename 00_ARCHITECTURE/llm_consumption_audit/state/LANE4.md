---
lane: "4"
title: "Receipt honesty — DISHONEST tools list"
status: CURRENT
generated: 2026-07-12
source: llm_consumption_audit / WIRE state (lane A = 1a+4)
---

# LANE 4 — Receipt Honesty: DISHONEST Self-Description (class 5)

A receipt is DISHONEST when its envelope / self-description asserts something the payload contradicts — an `ok:true` over an empty or error inner body, an echoed parameter that was silently ignored, or a help/remediation string that points at tools that do not work.

## DISHONEST tools (confirmed)

| Tool | Dishonesty |
|---|---|
| `lel_query` | Receipt self-description misrepresents what was served. |
| `list_entities` | Receipt self-description misrepresents what was served. |
| `query_chart_facts` | Echoes filter params (`fact_category`/`fact_subject`) in the receipt that are silently IGNORED — a full pivoted dump is returned regardless; defaults to `ay=lahiri_chitrapaksha` / row cap without disclosure (cross-ref LCA-3, LANE3). |
| `query_remedies_for_chart` | Receipt self-description misrepresents what was served. |
| `read_classical_text` | Receipt self-description misrepresents what was served. |

## Findings

### F4-1 — Whitelist remediation string advertises DEAD-19 tools as live (class 5, MEDIUM)

Spanning all 11 class-1 rejections, the remediation string's advertised `Surgical primitives are:` list enumerates **17 of the 19 DEAD-19 tools** (LCA-1) as if they were live surgical primitives:

`query_tara_balam, query_chandra_balam, jaimini_chara_dasha, jaimini_chara_dasha_full, temporal, kp_query, query_kp_ruling_planets, pattern_register, resonance_register, cluster_atlas, contradiction_register, query_ucn_walk, query_cdlm_lookup, query_rm_walk, query_jaimini_drishti, timeline_query, query_signal_state`

A consumer who follows the help text to any of those tools gets `Retrieval tool not found in registry` — the help text actively misdirects.

- Evidence tool: `bodha_chart_digest_get` rejection remediation.

### F4-2 — `chart_snapshot` refusal is HONEST (class 5, LOW — negative control)

The `chart_snapshot` error envelope accurately states the tool is not surgical and enumerates the real surgical whitelist — a factually correct refusal with no dishonest counter or flag. `receipt_honesty` is n/a because no payload was emitted; the honest remediation still (correctly) points at the LCA-2-broken `ask_madhav`. Logged as the honest counter-example that isolates F4-1 as a genuine self-description defect rather than an inherent property of the refusal envelope.

## Cross-lane systemic pattern (silent-param dishonesty)

Confirmed in LANE1c services and reinforced here: several surgical tools **accept a discriminating parameter into the receipt but never route it into the query**, then serve a fixed natal/default dataset —

- `query_panchanga` (`date` ignored → always birth-day panchanga),
- `query_varshaphala` (`year` inert → always static natal Tajika),
- `query_dasha_periods` (`system_id` ignored → always vimshottari; unknown `system` → silent `"all"` dump),
- `query_ephemeris` / `query_transit_event` (MCP outer `ok:true, confidence_band:"high"` wrapping an inner `sidecar 401 Invalid API key`, `count:0`).

Each echoes the parameter in `invocation_params` so the receipt *looks* honored while the payload is parameter-independent. This is the systemic class-5 spine of the audit: params are accepted into the receipt but not into the query, and error/empty inner bodies are cloaked by `ok:true` outer envelopes.
</content>
