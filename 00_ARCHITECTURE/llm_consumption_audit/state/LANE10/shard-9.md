# LANE10 shard-9 — PROMISE-vs-DELIVERY (rectification / sankrama family)

Grader: Lane 10, Charter §7.5 (RATIFIED). Charts: native `482012f1-…`, Abhinandan `1c826d5a-…`.
Deployed channel: `https://amjis-mcp-qm256lasva-el.a.run.app/mcp`. DB = read-only truth.

## Cross-cutting discovery — asset-id ↔ promise remapping (class 3 promise-record)
The rectification build briefs were authored against asset-ids that were REASSIGNED before final build:
- `CLAUDECODE_BRIEF_L4_PH_SODHANA` promises **Birth-Time Rectification** → actually shipped as asset **`ph_rectification`** (table `phala_rectification` + `phala_rectification_best`, migration 333/334).
- `CLAUDECODE_BRIEF_L4_PH_SUDDHA_SODHANA` promises **Best Rectification** → the "best" landed in `phala_rectification_best`.
- Deployed `ph_sodhana` = **Anomaly detection** (registry), `ph_suddha_sodhana` = **Cleansed anchor disposition** (registry).
So the input promise_quotes for AP-066/AP-067 (rectification briefs) disagree with what those asset-ids actually are. Logged as class 3 INCONSISTENT on the promise-record per §7.5 rule 6.

## DB data-plane counts (verbatim)
| table | native 482012f1 | Abhinandan 1c826d5a |
|---|---|---|
| phala_rectification | 185 | 185 |
| phala_rectification_best | 1 | 1 |
| phala_sankrama | 635 | 1265 |
| phala_sodhana | 96 | 100 |
| phala_suddha_sodhana | 195 | 200 |

## Deployed retrieval surface
Only `phala_rectification_get` fronts this family. NO `*_sankrama_get`, `*_sodhana_get`, `*_suddha_sodhana_get` tool exists (tools/list grep = []). `phala_outlook` aggregates only PH-4-1..PH-4-4 (anchors/mitigations/rectification/muhurta) — sankrama/sodhana/suddha NOT included.

---
## AP-064 ph_rectification — SHORTFALL (compound)
promise_status: re-sourced (input NOT FOUND → found in asset_registry english_description + `phala_rectification_get` tool desc + ph_sodhana brief).
- **Data plane (partial/degraded):** 185 rows (37×5 ayanamsha) present but EVERY row `lel_fit_score=0.0000`, `lel_events_matched=0` of 36 tested, across all 5 ayanamshas. `phala_rectification_best`: `best_lel_fit_score=0.0000`, `confidence_label="unresolved"`, `win_margin=0.0000`, all 3 competing candidates score 0. The scorer matched ZERO training events → non-discriminating; promised "far more discriminating than ascendant-sign" not delivered.
- **Retrieval plane (empty shell):** `phala_rectification_get(482012f1)` → `candidates:[] count:0`; with `ayanamsha_id:"lahiri"` → still `candidates:0`. Tool defaults to `ayanamsha_id:"lahiri_chitrapaksha"` (not a stored value; table stores lahiri/true_chitra/kp/raman/surya_siddhanta) and filters zero-score candidates → consumer receives NO candidate birth times.
- **Dishonest envelope (class 5):** same empty response carries `judgment_flags{calibration:"calibrated", load_bearing:true, lel_event_count:57, calibration_state:"calibrated"}` — claims calibrated + load-bearing over an empty payload.
verdict SHORTFALL / shortfall_layer compound.

## AP-065 ph_sankrama — SHORTFALL (retrieval-plane)
promise_status: declared (brief matches registry: "Cross-domain spillover, multi-hop cascades").
- Data plane present: 635 native / 1265 Abhinandan rows in `phala_sankrama`.
- Retrieval plane UNREACHABLE: no deployed tool serves `phala_sankrama`; not in `phala_outlook`. The brief calls this "the asset that most directly delivers the project's founding promise: correlation depth and chains no human mind can hold" — 635 computed rows, zero reachable over the wire.
class 1 UNREACHABLE. verdict SHORTFALL / retrieval-plane.

## AP-066 ph_sodhana — SHORTFALL (compound)
promise_status: declared (input quote = rectification brief).
- class 3 INCONSISTENT (promise-record): brief promises Birth-Time Rectification via PyJHora per-candidate; deployed `ph_sodhana` = "Anomaly detection: 5 deterministic detectors" (registry). The rectification promise was delivered under a DIFFERENT asset (`ph_rectification`).
- Data plane present: 96 native rows (`phala_sodhana`, anomaly registry).
- Retrieval plane UNREACHABLE: no deployed tool fronts `phala_sodhana`.
verdict SHORTFALL / compound.

## AP-067 ph_suddha_sodhana — SHORTFALL (compound)
promise_status: declared (input quote = Best-Rectification brief).
- class 3 INCONSISTENT (promise-record): brief promises "living self-correcting Best Rectification verdict" (which landed in `phala_rectification_best`); deployed `ph_suddha_sodhana` = "Cleansed anchor disposition: one row per phala_anchors entry" (registry).
- Data plane present: 195 native rows (`phala_suddha_sodhana`).
- Retrieval plane UNREACHABLE: no deployed tool fronts `phala_suddha_sodhana`.
verdict SHORTFALL / compound.
