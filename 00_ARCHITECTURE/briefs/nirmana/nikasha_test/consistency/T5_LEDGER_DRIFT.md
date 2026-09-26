# T5_LEDGER_DRIFT — ledger overlap reconciliation + governance detector runs

Date: 2026-09-26. Branch: campaign/nikasha-test (uncommitted). Scope: (A) `00_ARCHITECTURE/control/asset_gaps.jsonl` overlap reconciliation (register R28); (B) `drift_detector.py` + `manifest_fingerprint.py --check` runs.

## (A) Ledger overlap reconciliation

### Population and discriminator

- Ledger: 263 lines = 1 `_schema` row + 262 data rows (measured by parsing every line as JSON).
- **Actual discriminator:** census-emitted rows are identified by `owner == "asset_census"`. They also carry `detector` of the form `asset_census.py --layer L0 (<criterion>)`, an empty `change`, and gap_ids of the form `<asset_id>-<criterion>` (no numeric suffix). Hand-written rows use ids like `<asset>-G01` / `<asset>-O1` / `_layer_all-BT01`, non-empty `change`, and an owner naming a brief or the layer packet. Note: the brief's expectation that "census rows carry criterion/run fields" is only half true — **every** row (hand or census) carries `criterion`; there is no `run` field anywhere. `owner` is the reliable discriminator.
- Counts: **209 census rows, 53 hand-written rows** (`owner != "asset_census"`), plus the 1 `_schema` row.
- Census criteria in the ledger: `Build.completion`, `Build.count_integrity`, `Build.exercised`, `Build.history`, `Build.registered`, `Carr.detector`, `Complete.depth`, `Cost.baseline`, `Count.floor`, `Dens.served`, `Earn.build_record`, `Idem.pattern`, `Vocab.alias`.
- Census emission code (`platform/scripts/governance/asset_census.py:576-605`, `emit_gaps`): appends rows with deterministic id `<asset>-<criterion>`, skipping ids already present; `owner="asset_census"`, `change=""`, `state="OPEN"`.

### Overlap pairs (hand-written row overlaps a census row in substance: same asset, same underlying problem)

**Pair 1 — bg_ontology build record / earn**
- Hand `bg_ontology-G02` (`Earn.count_sql_scope` is G01; this is `Earn.build_record`), verbatim:
  `{"asset": "bg_ontology", "gap_id": "bg_ontology-G02", "kind": "gap", "criterion": "Earn.build_record", "what": "measured: asset_throughput.rows_written = 0 against 741 live rows, rows_per_second NULL, last_built_at 2026-09-04 / required: a build record carrying a real figure", "change": "instrument the seeder's run (rows, duration) into asset_throughput", "detector": "asset_throughput.rows_written non-zero after one build", "owner": "bg_ontology brief", "gate": "this asset's certification", "state": "OPEN", "ts": "2026-09-26T05:56:21+05:30"}`
- Census `bg_ontology-Earn.build_record`, verbatim:
  `{"asset": "bg_ontology", "gap_id": "bg_ontology-Earn.build_record", "kind": "gap", "criterion": "Earn.build_record", "what": "measured: rows_per_second=NULL, last_built=2026-09-04 / required: the Earn gate's claim", "change": "", "detector": "asset_census.py --layer L0 (Earn.build_record)", "owner": "asset_census", "gate": "this asset's certification", "state": "OPEN", "ts": "2026-09-26T13:19:10+05:30"}`
- Same asset, same criterion string, same underlying problem (no real build record; rows_per_second NULL, last_built 2026-09-04). The hand row adds rows_written=0 vs 741 live and a proposed change; the census row is the thin duplicate.

**Pair 2 — bg_ontology alias sets**
- Hand `bg_ontology-G07` (`Vocab.rule1.alias`):
  `{"asset": "bg_ontology", "gap_id": "bg_ontology-G07", "kind": "gap", "criterion": "Vocab.rule1.alias", "what": "measured: 79 of 79 dosha rows carry an empty synonyms array; the other 15 classes are complete / required: a non-empty closed alias set per entity", "change": "seed dosha alias sets through the writer", "detector": "per-class alias census: no_alias = 0 for all 16 classes", "owner": "bg_ontology brief", "gate": "W-L0-5", "state": "OPEN", "ts": "2026-09-26T05:56:21+05:30"}`
- Census `bg_ontology-Vocab.alias`:
  `{"asset": "bg_ontology", "gap_id": "bg_ontology-Vocab.alias", "kind": "gap", "criterion": "Vocab.alias", "what": "measured: 16 class(es); empty alias sets: dosha 79/79 / required: the Vocab gate's claim", "change": "", "detector": "asset_census.py --layer L0 (Vocab.alias)", "owner": "asset_census", "gate": "this asset's certification", "state": "OPEN", "ts": "2026-09-26T13:19:10+05:30"}`
- Same finding (dosha 79/79 empty alias sets), different criterion strings (`Vocab.rule1.alias` vs `Vocab.alias`) and different gates (W-L0-5 vs this asset's certification).

**Pair 3 — bg_ontology density contracts**
- Hand `bg_ontology-G10` (`Dens.density_contract`):
  `{"asset": "bg_ontology", "gap_id": "bg_ontology-G10", "kind": "gap", "criterion": "Dens.density_contract", "what": "measured: 0 of 2 capability modules serving this asset declare a density_contract (0 of 46 layer-wide) / required: declared where the capability paginates or facets", "change": "declare density_contract on resolve_entity and list_entities", "detector": "grep census over the L0 capability directory", "owner": "layer packet", "gate": "W-L0-8", "state": "OPEN", "ts": "2026-09-26T05:56:21+05:30"}`
- Census `bg_ontology-Dens.served`:
  `{"asset": "bg_ontology", "gap_id": "bg_ontology-Dens.served", "kind": "gap", "criterion": "Dens.served", "what": "measured: 2 module(s): list_entities.ts, resolve_entity.ts; declaring density_contract: 0 / required: the Dens gate's claim", "change": "", "detector": "asset_census.py --layer L0 (Dens.served)", "owner": "asset_census", "gate": "this asset's certification", "state": "OPEN", "ts": "2026-09-26T13:19:10+05:30"}`
- Same finding (0 density_contract across the same 2 modules), different criterion strings.

**Pair 4 — bg_ontology carrier/source-correspondence detector**
- Hand `bg_ontology-G05` (`Carr.D1`):
  `{"asset": "bg_ontology", "gap_id": "bg_ontology-G05", "kind": "gap", "criterion": "Carr.D1", "what": "measured: no detector compares a row to its source_citation; 741/741 rows carry one / required: a source-correspondence detector that can fail", "change": "build the D1 detector (layer packet W-L0-3) and run it over this asset", "detector": "the detector reports a non-zero mismatch count it could also report as zero", "owner": "layer packet", "gate": "W-L0-3", "state": "OPEN", "ts": "2026-09-26T05:56:21+05:30"}`
- Census `bg_ontology-Carr.detector`:
  `{"asset": "bg_ontology", "gap_id": "bg_ontology-Carr.detector", "kind": "gap", "criterion": "Carr.detector", "what": "measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim", "change": "", "detector": "asset_census.py --layer L0 (Carr.detector)", "owner": "asset_census", "gate": "this asset's certification", "state": "OPEN", "ts": "2026-09-26T13:19:10+05:30"}`
- Same problem (absent Carr detector). Hand row specifies D1 and supplies the count; census is the generic form.

**Pair 5 — bg_ephemeris build record**
- Hand `bg_ephemeris-G03` (`Earn.build_record`):
  `{"asset": "bg_ephemeris", "gap_id": "bg_ephemeris-G03", "kind": "gap", "criterion": "Earn.build_record", "what": "measured: asset_throughput.rows_written = 0 for the layer's largest table (825,084 rows), rows_per_second NULL / required: a build record carrying a real figure", "change": "instrument the COPY path", "detector": "rows_written non-zero and a rate after one build", "owner": "bg_ephemeris brief", "gate": "this asset's certification", "state": "OPEN", "ts": "2026-09-26T06:20:58+05:30"}`
- Census `bg_ephemeris-Earn.build_record`:
  `{"asset": "bg_ephemeris", "gap_id": "bg_ephemeris-Earn.build_record", "kind": "gap", "criterion": "Earn.build_record", "what": "measured: rows_per_second=NULL, last_built=2026-09-04 / required: the Earn gate's claim", "change": "", "detector": "asset_census.py --layer L0 (Earn.build_record)", "owner": "asset_census", "gate": "this asset's certification", "state": "OPEN", "ts": "2026-09-26T13:19:10+05:30"}`
- Same criterion, same problem.

**Pair 6 — bg_ephemeris density contracts**
- Hand `bg_ephemeris-G05` (`Dens.density_contract`):
  `{"asset": "bg_ephemeris", "gap_id": "bg_ephemeris-G05", "kind": "gap", "criterion": "Dens.density_contract", "what": "measured: 4 capability modules expose it, 0 declare a density_contract / required: declared where the capability paginates or facets", "change": "declare it on the 4 modules", "detector": "grep census over the L0 capability directory", "owner": "layer packet", "gate": "W-L0-8", "state": "OPEN", "ts": "2026-09-26T06:20:58+05:30"}`
- Census `bg_ephemeris-Dens.served`:
  `{"asset": "bg_ephemeris", "gap_id": "bg_ephemeris-Dens.served", "kind": "gap", "criterion": "Dens.served", "what": "measured: 4 module(s): query_aspects_at_time.ts, query_planet_position.ts, query_planet_transit.ts, query_retrograde_periods.ts; declaring density_contract: 0 / required: the Dens gate's claim", "change": "", "detector": "asset_census.py --layer L0 (Dens.served)", "owner": "asset_census", "gate": "this asset's certification", "state": "OPEN", "ts": "2026-09-26T13:19:10+05:30"}`
- Same finding (4 modules, 0 contracts).

**Pair 7 — bg_ephemeris re-derivation detector**
- Hand `bg_ephemeris-G02` (`Carr.D3`):
  `{"asset": "bg_ephemeris", "gap_id": "bg_ephemeris-G02", "kind": "gap", "criterion": "Carr.D3", "what": "measured: integrity_check_sql asserts shape (exact row count, span, 9-body set, ayanamsha_id='tropical') and never recomputes a position; 825,084 computed values, none independently re-derived / required: D3 re-derivation within a declared tolerance", "change": "build D3: recompute a sample a second way and compare; seed one error to prove it fails", "detector": "non-zero mismatch on the seeded case, zero on the corpus", "owner": "layer packet", "gate": "W-L0-4", "state": "OPEN", "ts": "2026-09-26T06:20:58+05:30"}`
- Census `bg_ephemeris-Carr.detector`:
  `{"asset": "bg_ephemeris", "gap_id": "bg_ephemeris-Carr.detector", "kind": "gap", "criterion": "Carr.detector", "what": "measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim", "change": "", "detector": "asset_census.py --layer L0 (Carr.detector)", "owner": "asset_census", "gate": "this asset's certification", "state": "OPEN", "ts": "2026-09-26T13:19:10+05:30"}`
- Same problem class (no D3 detector). Hand row adds the sharper observation that the existing `integrity_check_sql` is shape-only.

**Pair 8 — bg_panchanga liveness/build signal**
- Hand `bg_panchanga-G01` (`Earn.service_state`):
  `{"asset": "bg_panchanga", "gap_id": "bg_panchanga-G01", "kind": "gap", "criterion": "Earn.service_state", "what": "measured: the asset's only status is asset_throughput state='lit' with rows_written=0 — identical to what a writer that produced nothing would write; no liveness or correctness signal exists / required: a status that can return false for a broken service", "change": "give service assets their own probe: answer a pinned instant, compare to a stored expected limb set", "detector": "the probe fails when the service is down or wrong", "owner": "layer packet", "gate": "this asset's certification", "state": "OPEN", "ts": "2026-09-26T06:20:58+05:30"}`
- Census `bg_panchanga-Earn.build_record`:
  `{"asset": "bg_panchanga", "gap_id": "bg_panchanga-Earn.build_record", "kind": "gap", "criterion": "Earn.build_record", "what": "measured: rows_per_second=NULL, last_built=2026-08-27 / required: the Earn gate's claim", "change": "", "detector": "asset_census.py --layer L0 (Earn.build_record)", "owner": "asset_census", "gate": "this asset's certification", "state": "OPEN", "ts": "2026-09-26T13:19:10+05:30"}`
- and census `bg_panchanga-Cost.baseline`:
  `{"asset": "bg_panchanga", "gap_id": "bg_panchanga-Cost.baseline", "kind": "gap", "criterion": "Cost.baseline", "what": "measured: state=lit, rows_written=0, rps=- / required: the Cost gate's claim", "change": "", "detector": "asset_census.py --layer L0 (Cost.baseline)", "owner": "asset_census", "gate": "this asset's certification", "state": "OPEN", "ts": "2026-09-26T13:19:10+05:30"}`
- Partial three-way overlap: all three rows measure the same instrument (`asset_throughput` showing state=lit / rows_written=0 / rps NULL) for an asset that is a service, not a writer. The hand row's distinct claim is that this instrumentation is *category-wrong* for a service (it can never fail); the census rows merely record the NULL/zero readings. Overlap in measurement surface, not in full substance — recorded as a partial overlap.

**Pair 9 — bg_panchanga re-derivation detector**
- Hand `bg_panchanga-G02` (`Carr.D3`):
  `{"asset": "bg_panchanga", "gap_id": "bg_panchanga-G02", "kind": "gap", "criterion": "Carr.D3", "what": "measured: no detector recomputes a pañcāṅga limb a second way / required: D3 re-derivation on at least one limb", "change": "recompute tithi/vāra a second way for a pinned instant and compare", "detector": "mismatch reported on a seeded wrong convention", "owner": "layer packet", "gate": "W-L0-4", "state": "OPEN", "ts": "2026-09-26T06:20:58+05:30"}`
- Census `bg_panchanga-Carr.detector`:
  `{"asset": "bg_panchanga", "gap_id": "bg_panchanga-Carr.detector", "kind": "gap", "criterion": "Carr.detector", "what": "measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim", "change": "", "detector": "asset_census.py --layer L0 (Carr.detector)", "owner": "asset_census", "gate": "this asset's certification", "state": "OPEN", "ts": "2026-09-26T13:19:10+05:30"}`
- Same problem (no D3 detector for this asset).

**Pair 10 — bg_rules source correspondence**
- Hand `bg_rules-G03` (`Carr.D1`):
  `{"asset": "bg_rules", "gap_id": "bg_rules-G03", "kind": "gap", "criterion": "Carr.D1", "what": "measured: 3,002 encoded rules, each citing text_id + verse_ref, and no detector compares a rule to its verse / required: D1 source correspondence that can fail", "change": "build D1 (layer packet W-L0-3) and run it over this asset first — it is the largest encoded-claim set in L0", "detector": "non-zero mismatch count it could also report as zero; a seeded wrong rule is caught", "owner": "layer packet", "gate": "W-L0-3", "state": "OPEN", "ts": "2026-09-26T06:20:58+05:30"}`
- Census `bg_rules-Carr.detector`:
  `{"asset": "bg_rules", "gap_id": "bg_rules-Carr.detector", "kind": "gap", "criterion": "Carr.detector", "what": "measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim", "change": "", "detector": "asset_census.py --layer L0 (Carr.detector)", "owner": "asset_census", "gate": "this asset's certification", "state": "OPEN", "ts": "2026-09-26T13:19:10+05:30"}`
- Same problem (no D1 detector).

**Pair 11 — bg_rules dasha_system_id never populated**
- Hand `bg_rules-G06` (`Completeness.depth.dasha_link`):
  `{"asset": "bg_rules", "gap_id": "bg_rules-G06", "kind": "gap", "criterion": "Completeness.depth.dasha_link", "what": "measured: dasha_system_id populated on 0 of 3,002 rows — a column never used / required: populated where the rule is daśā-conditioned, or the column removed", "change": "populate or drop; an always-null column is a claim nobody makes", "detector": "count > 0, or the column gone", "owner": "bg_rules brief", "gate": "this asset's certification", "state": "OPEN", "ts": "2026-09-26T06:20:58+05:30"}`
- Census `bg_rules-Complete.depth`:
  `{"asset": "bg_rules", "gap_id": "bg_rules-Complete.depth", "kind": "gap", "criterion": "Complete.depth", "what": "measured: 3002 rows, 14 cols; fully populated 12; NEVER populated ['dasha_system_id'] / required: the Complete gate's claim", "change": "", "detector": "asset_census.py --layer L0 (Complete.depth)", "owner": "asset_census", "gate": "this asset's certification", "state": "OPEN", "ts": "2026-09-26T13:19:10+05:30"}`
- Same finding (dasha_system_id never populated, 3,002 rows), near-identical criterion strings (`Completeness.depth.dasha_link` vs `Complete.depth` — note the census uses `Complete.`, the hand row `Completeness.`).

### Non-overlaps checked

- `_layer_all-BT03` (`Build.registered.cross_layer`) names five L2/L3 assets (bo_cdlm_summary, bo_cgm_motifs, bo_cgm_paths, bo_chart_gestalt, ka_gochara_sweep); the two census `Build.registered` rows are for different assets (`bg_nakshatra_medical`, `bg_transit_engine`, both L0). Related theme, disjoint substance — not an overlap pair.
- Hand rows G01/G03/G04/G06/G08/G09 (bg_ontology), G01/G02/G04/G05/G07/G08 (bg_rules), G01/G04/G06 (bg_ephemeris), G03/G04 (bg_panchanga), G01/G02 (bg_sarvatobhadra_grid), BT01/BT02/BT04/BT05, and all `O*` opportunity rows have no census counterpart on the same substance.
- bg_sarvatobhadra_grid hand rows vs its 4 census rows: census rows are Build.count_integrity / Earn.build_record / Cost.baseline / Carr.detector readings; hand rows are Completeness.universe_blocked and Vocab.future_gate. No overlap.

### Namespace proposal (R28)

The ledger currently carries two row idioms for one artefact: hand rows (`<asset>-G<nn>` / `<asset>-O<n>` / `_layer_all-BT<nn>`, owner = brief or layer packet, substantive `change`) and census rows (`<asset>-<criterion>`, owner = `asset_census`, empty `change`), and the census's deterministic-id skip (`asset_census.py:592-599`) cannot dedupe across the two idioms, so the 11 pairs above coexist as separate OPEN rows for the same defect. Proposal: make the hand-written idiom the single ledger namespace — a gap exists as exactly one row with a hand-style id; the census stops being a writer and becomes a *detector reference*. Concretely: (1) `emit_gaps` should, instead of appending its own row, either attach its measurement to an existing row whose `(asset, substance-key)` matches, or append a new hand-style row only when no row covers the substance — where the substance key is `(asset, gate-criterion-family)` with the family's aliases resolved (e.g. `Vocab.rule1.alias` ≡ `Vocab.alias`; `Dens.density_contract` ≡ `Dens.served`; `Carr.D1|D2|D3` ≡ `Carr.detector`; `Completeness.*` ≡ `Complete.*`); (2) for the 11 existing pairs, fold each census row's `measured:` reading into the hand row's `what` (or leave it as the detector's re-run output) and WITHDRAW the census duplicate per the ledger's own state vocabulary; (3) add a `supersedes`/`superseded_by` field (or encode it in `detector`) so the fold is auditable without breaking append-only. The census's `change: ""` and `owner: "asset_census"` rows violate the schema doc's own spirit ("a row with no detector/measurement is not registered") only in the weak sense that they carry a measurement but no proposal — folding them into hand rows removes that category of row entirely.

## (B) Detector runs

### B1. drift_detector.py

Command: `cd /Users/Dev/madhav-nikasha && /opt/homebrew/opt/python@3.13/bin/python3.13 platform/scripts/governance/drift_detector.py`

Stdout verbatim:

```
drift_detector: 3 findings; exit=2
  JSON: 00_ARCHITECTURE/drift_reports/DRIFT_REPORT_adhoc_20260926T172934Z.json
  MD:   00_ARCHITECTURE/drift_reports/DRIFT_REPORT_adhoc_20260926T172934Z.md
```

Exit code: 2 (high). Full generated report (`00_ARCHITECTURE/drift_reports/DRIFT_REPORT_adhoc_20260926T172934Z.md`) verbatim:

```
# DRIFT REPORT — adhoc

*Generated by `platform/scripts/governance/drift_detector.py` on 2026-09-26T17:29:34.094141+00:00.*

Exit code: **2** (0 clean; 1 critical; 2 high; 3 medium/low; 4 script error)

Total findings: **3** — 0 CRITICAL, 1 HIGH, 0 MEDIUM, 2 LOW
Whitelisted (deferred WARN tickets): **0**

## HIGH

- **fingerprint_mismatch** (ASSET_ELEVATION_TEMPLATE)
  - Surfaces: 00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md, CANONICAL_ARTIFACTS
  - Evidence: declared=bb341cc1a696db7b5541af8792237aff12ac18985b1491979a73ed8ed98fa4dc observed=244e87dff30a38381ce01e02ef70e5031cb83ee0af8d1468b2596b598114a98f
  - Remediation: Rotate the row's fingerprint_sha256 AND update last_verified_session/last_verified_on

## LOW

- **schema_db_unreachable** (-)
  - Surfaces: platform/scripts/governance/CHART_FACTS_SCHEMA.json
  - Evidence: psql exit 2: psql: error: connection to server at "127.0.0.1", port 5433 failed: fe_sendauth: no password supplied
  - Remediation: Ensure DB is running on PGHOST:PGPORT for live schema checks
- **a3_schema_db_unreachable** (-)
  - Surfaces: chart_facts
  - Evidence: DB query failed: psql: error: connection to server at "127.0.0.1", port 5433 failed: fe_sendauth: no password supplied
  - Remediation: Ensure DB is running on PGHOST:PGPORT
```

### B2. manifest_fingerprint.py --check

Command: `/opt/homebrew/opt/python@3.13/bin/python3.13 platform/scripts/governance/manifest_fingerprint.py --check`

Stdout verbatim:

```
entries: 136 (declared 136)
fingerprint declared: 7794567b405a9207
fingerprint observed: 7794567b405a9207
MATCH
```

Exit code: 0.

### Expectation check

The expected known HIGH finding is **confirmed**: `fingerprint_mismatch (ASSET_ELEVATION_TEMPLATE)` with declared `bb341cc1a696...` vs observed `244e87dff30a...` — matching the brief's stated `bb341cc1…` vs `244e87dff3…` (the "v1.1→v2.0 edit never rotated" claim is consistent with the evidence but the cause is not itself machine-verified here). `manifest_fingerprint.py --check` passes overall (136/136 entries, fingerprint MATCH) — the drift lives in the CANONICAL_ARTIFACTS row checked by drift_detector, not in the manifest's own fingerprint. New findings beyond the expected one: none HIGH or above. The two LOW `*_schema_db_unreachable` findings are environmental (no local Postgres password on 127.0.0.1:5433), not content drift; they would resolve in an environment with the DB reachable.

## Proposed register rows

| Rnnn | <change w/ clause + proposed text> | T5 | OPEN |
|------|-------------------------------------|----|------|
| L1 | asset_census.py emit_gaps (§"deterministic ids"): dedupe across idioms, not just ids — "add a substance key (asset, criterion-family) with alias resolution (`Vocab.rule1.alias`≡`Vocab.alias`, `Dens.density_contract`≡`Dens.served`, `Carr.D1\|D2\|D3`≡`Carr.detector`, `Completeness.*`≡`Complete.*`); skip or attach when a hand row covers the substance" | T5 | OPEN |
| L2 | asset_gaps.jsonl _schema row: add supersession — "fields add `superseded_by`; folding a duplicate sets it on the thinner row and leaves the ledger append-only" | T5 | OPEN |
| L3 | Ledger cleanup (11 pairs in §A): "fold each census row's `measured:` reading into the hand row's `what`; mark the census row `superseded_by` the hand id" — pairs: bg_ontology G02/G07/G10/G05, bg_ephemeris G03/G05/G02, bg_panchanga G01(partial)/G02, bg_rules G03/G06 | T5 | OPEN |
| L4 | CANONICAL_ARTIFACTS row for ASSET_ELEVATION_TEMPLATE: "rotate fingerprint_sha256 to 244e87dff30a38381ce01e02ef70e5031cb83ee0af8d1468b2596b598114a98f and update last_verified_session/last_verified_on" (drift_detector remediation, verbatim) | T5 | OPEN |
| L5 | drift_detector schema_db_unreachable LOWs: "run the schema checks against a reachable DB or mark the two checks NOT_MEASURED when psql cannot authenticate; an unreachable instrument must not masquerade as a passing or a noise finding" | T5 | OPEN |
