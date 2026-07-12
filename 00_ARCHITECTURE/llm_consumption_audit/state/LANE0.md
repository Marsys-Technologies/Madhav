# LANE0 — Item-0 R-45 Triage — state shard + broadcast

```
resume:
  lane_id: LANE0
  ledger_file: ledgers/value_families.jsonl (Item-0 cites VF-2070..VF-2095, VF-2839..VF-2843; not a full sweep)
  last_completed_row_id: n/a (single binary fork test, not a per-row sweep)
  next_row_id: n/a
  rows_done: 1
  rows_total: 1
  findings_count: 1
  status: DONE
  checkpoint_ts: 2026-07-12 (native chart audit session, wave 1)
```

## Verdict: DATA_PLANE_WRITER_DEFECT (fork refined — NOT serving-path bug, NOT writer no-op)

Item-0 asked: is `kala_activation` EMPTY (writer no-op → L3 build fix) or POPULATED-but-unserved
(serving-query bug → retrieval fix)? The evidence resolves to a **third outcome the §5 decision
table did not enumerate**: the tables are POPULATED, the serving query is CORRECT, but ~99% of
rows carry **NULL `activation_start` / `activation_end`**, so a correct date-window filter
(correctly) excludes them. The defect is in the **L3 Kāla activation writer** (it emits activation
rows without computing their temporal bounds), NOT in `get_temporal_windows`.

### Evidence (all read-only `mcp__postgres__query`; serving query transcribed verbatim from
`platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts` lines 113–153)

**DB population (fork step a):**
| chart | kala_activation | kala_activation_predicates |
|---|---|---|
| 482012f1 (native) | 66,836 | 66,836 |
| 1c826d5a (Abhinandan) | 66,747 | 66,747 |
Global totals 133,583 each (only these two charts hold data). → **POPULATED** (writer exonerated, matches gate E-4).

**Served (fork step b) — exact serving filter `chart_id=$1 AND ayanamsha_id='lahiri_chitrapaksha'
AND activation_end >= '2026-07-01' AND activation_start <= '2027-12-31'`, R-45 window:**
| chart | served activations (exact query) |
|---|---|
| 1c826d5a (R-45's original chart) | **64** — R-45's `activation_count:0` does NOT reproduce here today |
| 482012f1 (native) | **0** — R-45 REPRODUCES on the native chart for the default ayanamsha |

**Root cause (fork step c) — NULL temporal bounds, `fully_dated` = rows with non-null start AND end:**
| chart | ayanamsha | total rows | fully_dated | in-window served |
|---|---|---|---|---|
| 1c826d5a | lahiri_chitrapaksha | 13,369 | 84 | 64 |
| 1c826d5a | krishnamurti | 13,368 | 31 | — |
| 1c826d5a | raman | 13,289 | 77 | — |
| 1c826d5a | surya_siddhanta_classical | 13,349 | **0** | 0 |
| 1c826d5a | true_chitra | 13,372 | **0** | 0 |
| 482012f1 | lahiri_chitrapaksha (DEFAULT SERVING) | 13,364 | **0** | **0** |
| 482012f1 | krishnamurti | 13,367 | **0** | 0 |
| 482012f1 | raman | 13,383 | **0** | 0 |
| 482012f1 | surya_siddhanta_classical | 13,345 | **0** | 0 |
| 482012f1 | true_chitra | 13,377 | 110 | 50 |

- The native chart's 13,364 NULL-date lahiri rows ALSO have no fallback dates:
  `activation_predicted_dates_jsonb` populated on 0 of 13,364; `active_dasha_periods_jsonb` on only 15.
  → the activation windows were **never computed**, not hidden in JSONB.
- `normalizeAyanamsha(undefined)` → `DEFAULT_AYANAMSHA` = `'lahiri_chitrapaksha'` (platform-mcp
  registry_bridge.ts:85–89) — exact match to a stored key, so the ayanamsha-mismatch hypothesis
  is FALSIFIED. Date coverage reaches 2027-10-25 (inside window), so the window hypothesis is
  FALSIFIED. The only cause is NULL start/end columns.

### Finding record (Charter §3 schema) — feeds register dedupe at consolidation
- **reproducible call:** `get_temporal_windows(chart_id=482012f1-710e-4a25-994a-93821f5871aa,
  date_from=2026-07-01, date_to=2027-12-31, include_convergence=true)` → served `activation_count=0`;
  faithful reproduction via the transcribed serving SQL above (hosted tool not locally callable this
  session — see connectivity note; literal tool-envelope capture DEFERRED to a pipeline-enabled session).
- **verbatim evidence:** counts table above (per-chart × per-ayanamsha `fully_dated`).
- **primary failure class:** **4 EMPTY SHELL** at the DATA/WRITER plane (activation row exists but its
  defining temporal-bound payload is NULL) → consumer-visible effect is class **1 UNREACHABLE**
  (the temporal tool can never surface an undated row). Log both; primary = 4.
- **severity:** CRITICAL (the native's named "temporal engine has never worked in consumption" concern;
  for the native chart the default-ayanamsha temporal surface is 100% empty).
- **suspected layer:** L-writer (L3 Kāla `ka_*` activation writer — activation_start/activation_end
  population), NOT serving-query.
- **dedupe:** refines R-45 (re-attributes it from serving-path → data-plane) and R-39/R-40 (shared root
  cause CONFIRMED: undated activations ⇒ empty timing_hooks / activating_dasha windows). New native-chart
  specific severity delta. Register append/dedupe deferred to consolidation per DAG.

### Broadcast to Lanes 1 / 2 / 7 (per gate §4 + plan §12.7)
```json
{
  "item": "ITEM0_R45_TRIAGE",
  "run_at": "2026-07-12",
  "verdict": "DATA_PLANE_WRITER_DEFECT",
  "note": "Refines the fork: POPULATED + correct serving query + ~99% NULL activation_start/end. Not a serving-path query bug; not a writer no-op. Writer emits undated activation rows.",
  "db_counts": {
    "482012f1-710e-4a25-994a-93821f5871aa": {"kala_activation": 66836, "kala_activation_predicates": 66836},
    "1c826d5a-41cb-4450-b4dc-59d440e5f75a": {"kala_activation": 66747, "kala_activation_predicates": 66747}
  },
  "served_counts_exact_query_default_ayanamsha": {
    "482012f1-710e-4a25-994a-93821f5871aa": {"activation_count": 0, "predicate_count": 0},
    "1c826d5a-41cb-4450-b4dc-59d440e5f75a": {"activation_count": 64, "predicate_count": ">0"}
  },
  "fully_dated_rows_default_ayanamsha": {"482012f1": 0, "1c826d5a": 84},
  "ledger_citations": ["VF-2070..VF-2095", "VF-2839..VF-2843"],
  "implication_for_R39": "CONFIRMED shared root cause — undated activations cannot populate timing_hooks windows.",
  "implication_for_R40": "CONFIRMED shared root cause — activating_dasha.activations=0 follows from NULL activation windows.",
  "implication_for_rebuild": "CRITICAL: the Abhinandan/native rebuild already ran (66,747/66,836 rows) and STILL left ~99% NULL dates — the writer defect SURVIVES rebuild. A re-run alone will NOT fix it; the writer's activation_start/end population logic must be fixed first, else the rebuild re-produces undated rows.",
  "annotate_not_block": true
}
```

*Item-0 complete. Read-only; no fix, no product-code change. Verifier note (E-5): DB counts are
deterministic SELECTs, independently re-runnable from the SQL above; the one residual is literal
`get_temporal_windows` tool-envelope capture (hosted tool not reachable this session) — the served-0
claim rests on the verbatim-transcribed serving filter + the fully_dated=0 count, which are jointly
dispositive. Flag for a pipeline-enabled session to capture the literal envelope as belt-and-suspenders.*
