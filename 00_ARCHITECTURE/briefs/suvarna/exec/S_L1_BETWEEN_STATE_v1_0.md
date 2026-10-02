---
artifact: S_L1_BETWEEN_STATE
version: 1.2
status: DRAFT-FOR-REVIEW
produced_by: exec-suvarna (integration-docs worker)
produced_on: 2026-10-03
source: N-91 (owner surrogate, charter v1.0, 2026-10-03; /Users/Dev/suvarna-evidence/OwnerDecisions/N-91_between_state_ruling_v1_0.md), conditions 4 and 6, plus SS fact_id decisions of 2026-10-03 (three batches)
decision: N-91 RULING 1 (accept the between-state until S-L2 with conditions) and RULING 3 (clock from S-L1 CLOSE)
scope: documentation only. Text for the S-L1 window runbook v1.2 paragraph "state between S-L1 and S-L2", the W7 id check and the between-state acceptance check. Every query is a single read-only SELECT for the SELECT-only reader; nothing here writes. No birth data is read.
evidence:
  - /Users/Dev/suvarna-evidence/FactId/FACTID_IMPACT_REPORT.md (sha256 9eda8e6e20e2faad2d495d7cc6816ba57164761ceff2d6f44567a27305520ca7)
  - /Users/Dev/suvarna-evidence/FactId/FACTID_SERVED_IMPACT_REPORT.md (sha256 3346899bf4b4266ed626667273e159e3fa217a86df2dab0d427572171bd4d043)
  - /Users/Dev/suvarna-evidence/OwnerDecisions/N-91_between_state_ruling_v1_0.md
changelog:
  - "1.2 (2026-10-03): the ephemeris statements corrected to the measured truth (SE1_SHIFT_ANALYSIS; SS 2026-10-03 decision): 'about two hours on Vimshottari boundaries' and 'fact_ids, row counts and tiers are unaffected' replaced. Measured: Vimshottari +6,990..+6,994 s (about +1 h 56 m), Kalachakra +145,089..+145,111 s (about +40 h 18 m; Surya Siddhanta +150,309 s, about +41 h 45 m), Yogini / Ashtottari / Chara / Narayana / Naisargika exactly 0, Mudda 0..+1 s plus one -43 s bisection step (True Chitra 2001 varsha), Saturn ingress up to about 17 minutes. chart_dashas levels 1-3 are exact; level 4 changes by declared per-ayanamsha deltas (Vimshottari +12 / +2 / +1 / -9 / -6, Kalachakra +3 / 0 / +10 / -8 / -20); the five-ayanamsha total is not a check. chart_facts and chart_divisionals row counts and every fact_id are unaffected. Pointers to the W2/W6 backend-evidence rule and POST_WINDOW_FINDINGS (HOOKS_COMPLETENESS sections 10 and 11)."
  - "1.1 (2026-10-03): 'no chart value is wrong' qualified: the stored 2026-09-07/08 rows were built on the Moshier ephemeris and S-L1 rebuilds on the canonical Swiss .se1 backend (#2860), so graha longitudes move by up to 0.665 arcsec and Vimshottari boundaries by about +1.94 h on the canonical chart (section 10 item, HOOKS_W7_HAND_READBACK 1.2 H22/H23). fact_ids, row counts and tiers are unaffected."
  - "1.0 (2026-10-03): first version. Baseline values were read 2026-10-02 22:10 to 22:17 UTC (2026-10-03 03:40 to 03:47 IST) as suvarna_reader on the canonical chart 482012f1-710e-4a25-994a-93821f5871aa; the 'after' columns are to be filled at W7."
---

# S-L1 between-state: what the owner's chart looks like from S-L1 close to S-L2 close

## 1. The paragraph for the runbook (v1.2, "state between S-L1 and S-L2")

S-L1 re-runs the whole L1 (Gaṇita) layer for the owner's chart: **all 18 `ga_*` lanes**, including `ga_positions`, `ga_dashas` and `ga_vargas`. The fact_id formula in force drops `build_id` from the hash, so **about 99% of the chart's fact ids change once**: 142,094 of the 143,299 `chart_facts` rows get a new id; the 1,205 `ga_positions` rows (graha_position 430, bhava_cusps 360, house_chalit 225, graha_sign_attributes 100, sandhi_flag 90) keep theirs. The new ids are deterministic and **stable from then on** (a second rebuild reproduces them). The L2 (Bodha), L3 and L5 rows that cite the old ids are rebuilt only at S-L2, so between the two windows those citations point at ids that no longer exist. No chart value is wrong and nothing errors (the one value-level move at S-L1 is the ephemeris backend: sub-arcsecond on graha longitudes, about +1 h 56 m on Vimshottari boundaries, about +40 h 18 m on Kalachakra boundaries, Saturn ingress instants up to about 17 minutes, a handful of level-4 dasha rows appearing or disappearing per ayanamsha, section 10): the owner gets a quiet degradation, listed in section 3, and all of it clears when S-L2 closes. The window is accepted by owner-surrogate ruling N-91 (option (a)) on conditions that are listed in section 7. The clock runs from S-L1 CLOSE (section 8).

## 2. What changes at S-L1, by id space (canonical chart; read 2026-10-02 22:10 to 22:17 UTC)

| id space | rows (before) | at S-L1 | stable afterwards | W0 map (old id to natural key) |
|---|---|---|---|---|
| `chart_facts.fact_id` | 143,299 | 142,094 change, 1,205 keep (the five `ga_positions` categories). Of the 142,094, 2,925 rows (seven `ga_condition` categories) are random uuid36 today, so they were never stable | yes, from the first S-L1 generation (every writer's id is `sha256(category|subject|key|chart|ayanamsha[|formula_id])[:16]`; `ga_sensitive` always appends `|formula_id`, empty when none) | yes, mandatory |
| `chart_vichara.id` | 8,524 | all change (the column is `nextval('chart_vichara_id_seq')` and `ga_vichara` is delete-then-insert per ayanamsha); the row count changes 8,524 to 7,774 by the dedupe | no: serial, changes at every rebuild | yes, mandatory |
| `chart_divisionals.id` | 24,392 | all change (random uuid v4 from `gen_random_uuid()` in `ga_vargas_writer.py`) | no: random at every rebuild | yes, mandatory |
| `chart_dashas.dasha_row_id` | 483,870 | all change (uuid v4) | no: random at every rebuild | yes, mandatory |
| `chart_vichara.constituent_fact_ids` / `constituent_facts_array` | 8,524 rows, 22,108 cites, 9,635 distinct ids, all in four non-`ga_positions` categories (bhava_significance_link 5,400 ids, aspect_parashari_per_varga 2,850, graha_dignity_per_varga 1,350, graha_shadbala_total 35), 0 orphans | every row cites NEW ids (natural-key-equivalent, one id replaced by one id; the id count per row is unchanged by construction), rebuilt by `ga_vichara` in the same window, orphan check expected 0 | yes | n/a (rebuilt, not re-linked) |
| `ga_yoga_firings.constituent_fact_ids` | 53 rows, 145 cites (36 stable ids, 4 changing: `karakamsa_position`), 0 orphans | rebuilt by `ga_yoga` in the same window, orphan check expected 0 | yes | n/a |

Where each count comes from: FACTID_IMPACT_REPORT.md P2, P4, P6 and sections 2 and 3; FACTID_SERVED_IMPACT_REPORT.md DEFECT-4. The old-id to natural-key correspondence is one-to-one today (0 duplicate groups of `(ayanamsha_id, fact_category, fact_subject, fact_key, coalesce(formula_id,''))` over all 143,299 rows, FACTID_SERVED_IMPACT_REPORT.md "Natural-key uniqueness"); whether the rebuilt `chart_facts` reproduces every key is only knowable after S-L1.

### 2.1 The W0 maps (captured read-only BEFORE any S-L1 delete; N-91 condition 1)

If a map cannot be captured read-only, S-L1 does not open. Each map is stored under `/Users/Dev/suvarna-evidence/FactId/` with its row count and sha256, and cites the S-L1 plan reference. The rows are unrecoverable after the rebuild.

| map | rows expected (read 2026-10-02) | columns | row count captured | sha256 |
|---|---|---|---|---|
| `chart_facts.fact_id` to natural key | 143,299 | fact_id, fact_category, fact_subject, fact_key, ayanamsha_id, formula_id, build_id | ______ | ______ |
| `chart_vichara.id` to grain | 8,524 | id, ayanamsha_id, vichara_family, subject, target, domain, varga_id, formula_version, constituent_fact_ids | ______ | ______ |
| `chart_divisionals.id` to natural key | 24,392 | id and its natural key columns | ______ | ______ |
| `chart_dashas.dasha_row_id` to natural key | 483,870 | dasha_row_id and its natural key columns | ______ | ______ |

The `chart_facts` count is checked against the baseline snapshot (143,299); a mismatch stops W0.

## 3. The expected served picture between S-L1 close and S-L2 close

The state is quiet degradation, not an error. Sources: FACTID_SERVED_IMPACT_REPORT.md (code read on origin/main, the 52% from a SQL replica, not a live run).

| surface | what the reader sees | cause | clears at |
|---|---|---|---|
| DEFECT-001 note (`freshness_notes.ts`) on `bodha_signals_get`, the domain-reading and quality tools, `assess_*` | reads **OPEN at about 97.7%** (71,401 of 73,049 MSR constituent cites orphaned; 49,557 of 50,678 signals cite at least one orphan). The note itself says "reference-only, not an error" | MSR rows cite old ids | S-L2 (MSR rebuild) |
| `bodha_quality_get` | `defect_001_alert.severity = 'HIGH'` | the same live orphan count | S-L2 |
| `query_ucd` orientation digest (prefetched for every per-chart tool) | entity attribution reduced: about **52% of the top-300 pool** (157 of 300 in the replica) becomes unattributed, unless the D1/disclosure PR is live. With that PR live the digest serves `resolvable` computed (not the literal `true`), `cited_fact_count` / `unresolved_fact_count`, and an attribution note naming stale ids as the cause | the digest resolves constituent ids against `chart_facts` and silently drops the unresolved | S-L2 |
| echo-class tools (`judgment_query`, `pact_query`, `assess_*`, `bodha_signals_get`) | without the disclosure, the reading contract says "grounded in N resolvable L1 fact reference(s)" over ids that no longer resolve (a count, never a resolution). With the disclosure live: the `l2_receipts_predate_l1` flag in `judgment_flags` and, on `judgment_query`, the "NOT yet anchored ... drill before treating it as confirmed" sentence with the cause appended | count-only grounding sentence | S-L2 |
| portal chat citations | a stale id resolves to nothing and renders `[unverified citation n]` with grade `unverified` | `citation_resolver` is fail-closed on an id missing from `chart_facts` | S-L2 |
| in-flight inquiries | an inquiry STARTED BEFORE S-L1 gets **409 `CAPABILITY_OVERLAY_STALE`** (the served-generation build identity changed; not an id problem) | build identity | start a new inquiry; zero open inquiries at S-L1 open (section 7) |
| hallucination counter and the corpus `citation_precision` dimension | each unresolved portal citation increments the hallucination counter against the model, and a corpus or calibration run scores the stale-data effect as model error. **No corpus or calibration run from S-L1 open to S-L2 close** | DEFECT-5 | S-L2 |
| L1 output digests | change **by construction** on every digest-spec'd `ga_*` asset except `ga_positions` (migrations 875, 886, 887, 889, 891, 892, 893, 914, 919 key `chart_facts` by `fact_id` and list it in the value columns; 918 `ga_yoga` and 920 `ga_vichara` include `constituent_fact_ids`). Stable from the second build. A changed digest is not evidence of a value change and equality is not expected | the id formula | (stable from the second build) |
| L1 capture history (migration 1035) | cannot pair old and new rows across the S-L1 boundary: a one-time identity break | `fact_identity` = the row's `fact_id` | n/a |
| `chart_vichara.id` citations in L2 | `bodha_cgm_edges.constituent_ga_vichara_ids_array` 754 edges / 1,387 cites, `bodha_mechanisms` 605 rows / 3,058 cites (served raw by `bodha_mechanisms_get`), `bodha_rm_dasha_windowed_prescriptions` 5 rows dangle (DEFECT-4) | the serial changes | S-L2 |

What the owner does not see: no wrong chart value, no data loss, no error status. Everything that cites by natural key keeps working.

## 4. `chart_fact_identity`: cascade-emptied, then refilled (G-IDX)

`chart_fact_identity.fact_id` is a foreign key to `chart_facts` ON DELETE CASCADE, and the `ga_positions` rebuild is a delete then insert (`replace_prior_chart_facts`). The 1,205 identity rows (all `ga_positions` categories) are therefore deleted by the cascade at the `ga_positions` rebuild even though the ids come back identical. The index is built by a standalone script, not a registered asset: `platform/python-sidecar/scripts/build_fact_identity_index.py` (delete-then-insert per chart; consumed by `bo_pratijna` and `brahmagyan/chart_reader_v4.py`).

**G-IDX, immediately after W2 (`ga_positions`):** run `build_fact_identity_index.py` for the chart and verify **1,205 rows**. Serving that joins through the index is affected between the cascade and the refill.

```sql
SELECT count(*) AS identity_rows FROM chart_fact_identity i JOIN chart_facts f USING (fact_id) WHERE f.chart_id='482012f1-710e-4a25-994a-93821f5871aa'
```

Before (2026-10-02): 1,205. Expected: 0 after the `ga_positions` rebuild until the refill, **1,205 after G-IDX** (and at W7). After-value: ______.

## 5. The W7 id check (S-L1 acceptance; N-91 condition 4)

`flip_detector.py` never selects `fact_id` (FACTID_IMPACT_REPORT.md P1), so no tool in the W7 machine verdict checks that ids changed once, are stable and match the formula. These two single SELECTs are the check. Part 2 of the W7 report records each with expected and actual.

**5.1 Formula match and zero uuid36 rows.** An id matches when it equals `sha256(category|subject|key|chart|ayanamsha)[:16]` or the same with `|formula_id` appended (formula_id empty when null, the `ga_sensitive` form; `ga_nakshatra` variants and `ga_sensitive` non-null variants are the same string).

```sql
SELECT count(*) AS n_rows, count(*) FILTER (WHERE fact_id = left(encode(sha256(convert_to(k,'UTF8')),'hex'),16) OR fact_id = left(encode(sha256(convert_to(k||'|'||coalesce(formula_id,''),'UTF8')),'hex'),16)) AS n_formula_match, count(*) FILTER (WHERE length(fact_id)=36) AS n_uuid36 FROM (SELECT fact_id, formula_id, fact_category||'|'||fact_subject||'|'||fact_key||'|'||chart_id::text||'|'||ayanamsha_id AS k FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa') s
```

Before (read 2026-10-02): `143299|1205|2925` (only the `ga_positions` rows match; the 2,925 uuid36 rows are the seven `ga_condition` categories). Expected after: **n_uuid36 = 0**; n_formula_match = n_rows minus the documented exception: the seven `graha_shadbala_total.required_rupa` rows (ayanamsha INVARIANT), whose id hashes the last loop ayanamsha (`surya_siddhanta_classical`), so `n_rows - n_formula_match = 7` (FACTID_IMPACT_REPORT.md section 3; that id is deterministic only while the writer's pass order is fixed). The expectation is from the writer formulas, not a measurement: W7 is the first full-chain measurement. To list any non-matching row: add `WHERE NOT (...)` and group by category, key and ayanamsha; any category other than `graha_shadbala_total.required_rupa` is a finding (stop and tell SS). After-values: ______.

**5.2 Zero orphans in `chart_vichara` and `ga_yoga_firings`.**

```sql
SELECT 'chart_vichara' AS t, count(*) AS n_cited, count(*) FILTER (WHERE f.fact_id IS NULL) AS n_orphan FROM chart_vichara v CROSS JOIN LATERAL unnest(v.constituent_fact_ids) AS c(id) LEFT JOIN chart_facts f ON f.fact_id = c.id AND f.chart_id = v.chart_id WHERE v.chart_id='482012f1-710e-4a25-994a-93821f5871aa' UNION ALL SELECT 'ga_yoga_firings', count(*), count(*) FILTER (WHERE f.fact_id IS NULL) FROM ga_yoga_firings y CROSS JOIN LATERAL jsonb_array_elements_text(y.constituent_fact_ids) AS c(id) LEFT JOIN chart_facts f ON f.fact_id = c.id AND f.chart_id = y.chart_id WHERE y.chart_id='482012f1-710e-4a25-994a-93821f5871aa' ORDER BY 1
```

Before (read 2026-10-02): `chart_vichara|22108|0` and `ga_yoga_firings|145|0`. Expected after: **n_orphan = 0 on both rows** (n_cited moves with the dedupe: `ga_vichara` removes 750 duplicate rows; `ga_yoga_firings` 145 is unchanged unless the firing set moves). A non-zero orphan count means `ga_vichara` or `ga_yoga` ran before `ga_structural` / `ga_strength` finished: STOP, tell SS. After-values: ______.

W7 also keeps the existing acceptance file's A9 (`evidence/ga_vichara_writer_ACCEPTANCE.sql`; `HOOKS_W7_HAND_READBACK_v1_0.md` H6) and H22 (the ten `graha_position` ids identical, `build_id` new).

## 6. Between-state acceptance check (N-91 condition 3, with the SS wording of 2026-10-03)

The disclosure detector is built by the combined served PR (D1 `query_ucd` plus Form A, a receipt-pin lineage detector that fails closed). Two flag codes exist in `judgment_flags`: `l2_receipts_predate_l1` (the L2 receipts behind the cited ids predate the served L1 generation's receipts for this chart) and `l2_lineage_check_failed` (the detector could not run; fail closed). The flag is read from production receipts, never from a config value or an environment switch, and is merged into `judgment_flags`, never assigned.

Two live calls, on the canonical chart, **before S-L1** and **after S-L1 close**:

| call | check | before S-L1 | after S-L1 close |
|---|---|---|---|
| `judgment_query` | the flag `l2_receipts_predate_l1` in `judgment_flags` AND the reading-contract sentence | flag **false** (absent); the normal sentence "grounded in N resolvable L1 fact reference(s)" | flag **true**; the not-anchored sentence "Its reading is NOT yet anchored to resolvable L1 fact references in this envelope; drill via the pointers before treating it as confirmed. Cause: the L2 receipts behind these fact_ids predate the current L1 (chart_facts) rebuild ..." |
| any one `assess_*` (career, health, marriage, wealth) | the flag in `kernel.flags` only (no sentence exists on that wire) | flag **false** | flag **true** |

The calls are made **at least 3 minutes after the last L1 receipt lands** (the served detector result is memoised for 60 seconds and `pact_query` is uncached; three minutes clears the memo with a margin). `l2_lineage_check_failed` must NOT be the flag that is set: that is a failed detector, not a passing check. If the flag is false after S-L1 close, or the check-failed flag is set, the between-state acceptance fails: tell SS.

**S-L1 acceptance add (SS 2026-10-03):** every rebuilt `ga_*` asset has a **PROVEN receipt newer than its pre-window one**. The flag only sees S-L1 if the rebuilt assets get NEW receipts. If any rebuilt asset lacks one, the window is not complete.

```sql
SELECT asset_id, max(observed_at) FILTER (WHERE receipt_state = 'proven') AS newest_proven_receipt, count(*) FILTER (WHERE receipt_state <> 'proven') AS n_not_proven FROM asset_provenance_receipts WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND asset_id LIKE 'ga\_%' GROUP BY asset_id ORDER BY asset_id
```

Before (the pre-window newest proven receipt per `ga_*` asset, 19 assets in `asset_registry`, S-L1 rebuilds 18 of them per the runbook's W6 list; read 2026-10-02): ga_ayurdaya 2026-09-07 12:07:16+00; ga_condition 2026-09-07 20:31:48+00; ga_dashas 2026-09-07 20:14:04+00; ga_medical 2026-09-08 04:22:11+00; ga_nakshatra 2026-09-07 11:42:36+00; ga_panchanga 2026-09-07 11:22:09+00; ga_positions 2026-09-07 08:37:20+00 (one non-proven receipt row also exists); ga_prashna 2026-09-07 11:32:06+00; ga_sade_sati 2026-09-08 04:54:10+00; ga_sensitive 2026-09-07 11:19:43+00; ga_sensitive_degree 2026-09-07 12:10:20+00; ga_strength 2026-09-07 12:04:08+00; ga_structural 2026-09-08 01:33:20+00; ga_tajaka 2026-09-08 03:31:25+00; ga_transit_anchors 2026-09-07 14:46:19+00; ga_vargas 2026-09-07 11:03:25+00; ga_vastu 2026-09-08 06:19:14+00; ga_vichara 2026-09-08 08:10:42+00; ga_yoga 2026-09-08 07:42:27+00; n_not_proven 0 except ga_positions 1. Expected after: for every rebuilt asset `newest_proven_receipt` is later than the value above and later than the window-open time. After-values: ______.

## 7. Window rules and the conditions that bind (N-91 conditions 1 to 8)

1. **W0 maps** captured read-only before any S-L1 delete (section 2.1); if not capturable read-only, S-L1 does not open.
2. **D1 (`query_ucd`) fix** merged, independently reviewed, deployed and observed live on the canonical chart before the window.
3. **Echo-class disclosure** merged, reviewed, deployed and verified live by one `judgment_query` and one `assess_*` call before S-L1 (flag false, normal sentence); the same two calls after S-L1 close are the between-state acceptance check (section 6). It must not land during the regeneration freeze; if a Purna-owned baseline would move, stop and tell SS.
4. **This text** is in the runbook (which `ga_*` run; ~99% of ids change once; the served picture; changed output digests by construction; the `chart_fact_identity` refill; the W7 id check as acceptance).
5. **Zero open inquiries at S-L1 open; no corpus or calibration run from S-L1 open to S-L2 close.** An inquiry open across S-L1 gets 409 `CAPABILITY_OVERLAY_STALE`.
6. **Three false statements corrected** before the operator relies on them (done in this commit; section 9).
7. **S-L2 preparation is the top priority from S-L1 close**, tracked against the clock in section 8: I-20 (including signal ids that embed `chart_divisionals.id`, section 10), I-21 with its short L1 re-run, the restored digest spec, the runway ruling, the rehearsal.
8. **Recorded outside the window:** DEFECT-3 (the eval harness literal `n5_violations_in_registry: 0` cannot go red), DEFECT-6 (a doc claim about `resolve_signals` that the code contradicts), and the **1,340 vargottama signal_ids** that move at the first MSR regeneration after a `ga_vargas` rebuild (vargottama_per_varga:is_vargottama 1,305; graha_vargottama_amplification_factor 35).

## 8. The S-L2 clock (N-91 RULING 3)

- **Starts at S-L1 CLOSE**: the rebuilt L1 is the served generation and S-L1 acceptance is recorded.
- **Day 7 checkpoint:** if S-L2's off-production rehearsal has passed and its window is scheduled within 72 hours, no remedy. Otherwise remedy (c) starts in its narrow form: the `query_ucd` resolver, the portal `citation_resolver` and `freshness_notes` `remapped_refs`; every remap-resolved id is labelled `resolved_via: remap` and counted separately; the map expires at S-L2 and the table is dropped.
- **Day 14 absolute:** if S-L2 has not closed, (c) must be live and SS re-plans the S-L2 shape.
- **Override:** if the owner states he is using the chart, the checkpoint collapses to 48 hours from that statement.

Confidence on the 7- and 14-day numbers is medium (N-91).

## 9. Corrections made in this commit (N-91 condition 6)

The three statements became false at S-L1 because every non-`ga_positions` fact_id changes once. They were true only against the main-branch hash input or the writer formula, not against ids stored in production. Corrected in place (each file's changelog says so):

| file | old statement | new statement |
|---|---|---|
| `s_l1_attribution_hooks/evidence/ga_vichara_writer_HOOK_DECLARATION.json` (and the INFO comment in `ga_vichara_writer_ACCEPTANCE.sql`) | "ORDER-ONLY ... Membership identical." (N = 4,773) | every surviving row's ids are NEW; membership natural-key-equivalent, not id-identical; 4,773 counts rows unsorted in the OLD id space |
| `gandanta/GANDANTA_X1_LANE_INTENT_v1_0.md` | "every canonical `fact_id` is byte-identical to before" and "keep their value and `fact_id`" | identical to main's formula, not to stored ids; all 50 canonical ids change once at S-L1 |
| `karaka_roles/KARAKA_ROLES_LANE_INTENT_v1_0.md` | "The kn_rao PUTRAKARAKA / GNATIKARAKA / DARAKARAKA ids are unchanged" | unchanged by this lane's formula; all 525 stored `karaka_chara_position` ids change once at S-L1 |

Two further statements of the same family were found and left, each for the reason given: `evidence/tiers_evidence_v1_3.json` ("fact_id untouched by this lane": true for that lane only, the change comes from the formula already on main) and `evidence/argala_HOOK_DECLARATION_old_shape.json` (`unchanged_columns` lists `fact_id`; kept verbatim as the superseded shape). The code comment in `pipeline/orchestrator/writers/ga_nakshatra.py` ("Canonical rows keep the exact id they always had") has the same flaw; it is a writer source file, so editing it would move a writer digest, and a docs-only commit does not touch it. It goes on the post-window list.

## 10. Things this window does not fix, stated so nobody assumes otherwise

- **Ephemeris backend: Moshier to .se1 (a value move, not an id move).** The stored 2026-09-07/08 rows for the canonical chart were built on the Moshier ephemeris, not the `.se1` files (independent re-derivation: every stored planetary longitude matches Moshier to under 0.001 arcsec; `/Users/Dev/suvarna-evidence/SwissThreadMode/AUDIT_NOTE.md`, SWE_THREAD_AUDIT section 4a/4c). S-L1 rebuilds on the canonical Swiss `.se1` backend (#2860, `SE_EPHE_PATH` in both Dockerfiles). Expected: `graha_position` and every value derived from it moves by sub-arcsecond amounts (Moon +0.665 arcsec stored-minus-se1, Jupiter +0.202, Saturn -0.152, Mars +0.118, Venus +0.036, Mercury -0.016, Sun, nodes and Lagna about 0; the bound used at W7 is 0.0003 deg = 1.08 arcsec), and the Moon-anchored dasha boundaries (`start_iso` / `end_iso`) move later, measured per system: **Vimshottari +6,990 to +6,994 s (about +1 h 56 m)**, **Kalachakra +145,089 to +145,111 s (about +40 h 18 m; Surya Siddhanta +150,309 s, about +41 h 45 m)**, Yogini / Ashtottari / Chara-karaka / Narayana / Naisargika **exactly 0**, Mudda 0 to +1 s plus one -43 s bisection step (True Chitra varsha of 2001-02-04), Saturn sign-ingress instants up to about 17 minutes (Krishnamurti +-1,044 s; the sade_sati `*_iso` facts move with them) and Saturn stations +-31 s. **Row counts:** `fact_id`s, tiers and the `chart_facts` / `chart_divisionals` row counts are unaffected (no class flip anywhere in the compared payload); in `chart_dashas` dasha levels 1 to 3 are exact (row sets and lords unchanged) and level 4 changes by natural-key membership with a declared per-ayanamsha delta (the dasha writers drop a period whose UTC start date is not before its end date, so the shift moves sub-day Sukshma rows across UTC midnight): Vimshottari level 4 lahiri +12, true_chitra +2, krishnamurti +1, raman -9, surya_siddhanta -6; Kalachakra level 4 +3, 0, +10, -8, -20. The five-ayanamsha total is NOT a check (the Vimshottari deltas cancel to 0 by coincidence). The earlier statements here ("about two hours on Vimshottari boundaries", "row counts ... unaffected") were wrong for Kalachakra and for the level-4 row sets. Owners of anything keyed on an exact longitude or an exact dasha boundary instant of this chart (L3 windows, calibration data) should expect it to move once. The detector declaration is `s_l1_attribution_hooks/ephemeris_backend_shift.json`; the W2/W6 evidence rule (one `ephemeris_backend=swieph` log line per decorated asset, missing or non-swieph = STOP) and the post-window findings are in `s_l1_attribution_hooks/HOOKS_COMPLETENESS_v1_0.md` sections 10 and 11.
- **The blind spot.** About 3.8% of the ids cited by L2 rows fall in 40 categories that no active L1 output-digest spec covers (figure as supplied to this worker by Exec Suvarṇa; the two reports in `/Users/Dev/suvarna-evidence/FactId/` do not carry it). It is **irrelevant for S-L1**, because all 18 lanes rebuild and every category is rewritten. It matters for any later partial rebuild: a change there would not move a digest.
- **Signal ids embedding `chart_divisionals.id` (I-20).** 1,340 canonical MSR signals embed a random `chart_divisionals.id` in `configuration_jsonb` and `signal_summary_text` (1,305 distinct ids). `signal_id` is `uuid_v5(chart, ayanamsha, signal_type, varga, configuration_jsonb)` (migration 661), so the first MSR regeneration after a `ga_vargas` rebuild gives them new signal ids, stranding `kala_*` and `phala_*` rows keyed on them. `bodha_pratijna` also cites 190 `chart_divisionals` ids (135 rows). This is named in the I-20 "bo_laksana signal identity" design item. The fact_id change itself does not move any signal_id (0 of 1,787 id-like tokens in MSR `configuration_jsonb` resolve to a `chart_facts` id).
- **Pravāha's `gochara_resonance_map.target_ref`** (88 rows, 17 distinct ids: arudha_pada and sensitive_degree_check categories) cites ids that change at S-L1. Pravāha's table: not touched here. SS passes it on. Relinking would change contact and window identities and `class_fingerprint`, and it has no served benefit (the table is read by natural key, not by id).
- **Other L3 and L2 stores** that carry changing ids: `kala_field_promise_edges.source_fact_id` (31 rows), `bodha_rm_dasha_windowed_prescriptions.schedule_jsonb` (5 rows), `bodha_cgm_edges.constituent_fact_ids_array` (285 rows), `bodha_msr_signals.constituent_facts_array` (49,557 rows). All are repaired by the S-L2 rebuild or are Pravāha's; no re-link is run (N-91 refused option (b): migration 1036 admits L2 writes only from a real producer run).

## 11. References

- N-91 ruling: `/Users/Dev/suvarna-evidence/OwnerDecisions/N-91_between_state_ruling_v1_0.md`
- `/Users/Dev/suvarna-evidence/FactId/FACTID_IMPACT_REPORT.md` and `/Users/Dev/suvarna-evidence/FactId/FACTID_SERVED_IMPACT_REPORT.md` (hashes in the frontmatter)
- W7 hand read-back list: `s_l1_attribution_hooks/HOOKS_W7_HAND_READBACK_v1_0.md` (H6, H10, H14, H15, H22, H23); hooks completeness (with the ephemeris backend-evidence rule and POST_WINDOW_FINDINGS): `s_l1_attribution_hooks/HOOKS_COMPLETENESS_v1_0.md`
- Combined served PR (D1 plus the lineage disclosure): draft PR #2986, branch `suvarna/land/TI-d1-query-ucd-disclosure-001`; merges AFTER the integration PR, deploys before the window
