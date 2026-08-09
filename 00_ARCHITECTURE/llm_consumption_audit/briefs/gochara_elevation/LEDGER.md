CAMPAIGN-STATUS: RUNNING
campaign: GOCHARA-UTKARṢA
plan: GOCHARA_UTKARSHA_CAMPAIGN_PLAN_v1_0.md
branch: utkarsha/campaign
conductor_model: claude-sonnet-4-6
launched: 2026-08-10
last_updated: 2026-08-10 (first launch)

---

## §I6(c) — Pre-Campaign Protected Corpus Snapshot

Recorded at first launch. These are the canonical checksums the rail verification checks against.

| chart_id | chart | generation | row_count | corpus_checksum_md5 |
|---|---|---|---|---|
| 482012f1-710e-4a25-994a-93821f5871aa | native | v1 | 16,297 | b9834dc43c545d0af9a8251d4af2ec9d |
| 1c826d5a-41cb-4450-b4dc-59d440e5f75a | Abhinandan | v1 | 19,323 | 47c30b7df1b256200dca94a2e6dc11cf |

**Checksum method:** `md5(string_agg(chart_id||'|'||event_class||'|'||temporal_shape||'|'||window_start||'|'||window_end||'|'||COALESCE(peak_date,'')||'|'||COALESCE(milestone_id,'')||'|'||COALESCE(signed_intensity,'')||'|'||COALESCE(raw_intensity,'')||'|'||COALESCE(valence,'')||'|'||COALESCE(is_adverse,'')||'|'||COALESCE(calibration_state,'')||'|'||COALESCE(generation,''), '||' ORDER BY chart_id, event_class, window_start, window_end, COALESCE(milestone_id,'')))`

---

## §I6(b) — Protection Rail Baseline (pre-campaign state)

Recorded at first launch for diff-comparison at every wave boundary.

**Triggers on `kala_gochara_windows`:**
- `trg_kala_gochara_windows_protect_row` → function `build_protected_assets_guard_row` (row-level, BEFORE DELETE/UPDATE)
- `trg_kala_gochara_windows_protect_truncate` → function `build_protected_assets_guard_truncate` (truncate-level)

**Guard function:** `build_protected_assets_guard_row` — checks `build_protected_assets` for `asset_id='ka_gochara_sweep'` + `chart_id=OLD.chart_id`; GUC `app.allow_protected_sweep_rewrite` bypass present (prohibited campaign-wide per I1). Generation-blind at baseline (W0.3 Phase B will add `protected_generations text[]`).

**Unique index:** `uq_kala_gochara_windows_natural_key` — `(chart_id, event_class, window_start, peak_date, COALESCE(milestone_id, ''))` — **generation-blind** (expected pre-W0.3; W0.3 Phase B replaces with generation-inclusive form).

**`build_protected_assets` rows at baseline:**
- `(asset_id='ka_gochara_sweep', chart_id='1c826d5a-41cb-4450-b4dc-59d440e5f75a')` — protected since 2026-08-06
- `(asset_id='ka_gochara_sweep', chart_id='482012f1-710e-4a25-994a-93821f5871aa')` — protected since 2026-08-06

**`protected_generations` column:** does NOT yet exist (added by W0.3 Phase B migration).

**Latest migration applied:** `555_brahma_event_ontology_g9_reconcile.sql` (id=414, applied 2026-08-09).

---

## §Lane Table

Status: QUEUED | BUILDING | VERIFYING | PASS | FAIL(n) | BLOCKED | MERGED

| lane | wave | tag | title | status | branch | worktree | builder_model | deps | notes |
|---|---|---|---|---|---|---|---|---|---|
| W0.1 | 0 | [mech] | Registry & seed hygiene | QUEUED | — | — | sonnet | none | Parallel W0 |
| W0.2 | 0 | [mech] | Baseline builds + error triage | QUEUED | — | — | sonnet | none | Parallel W0; never rebuilds ka_gochara_sweep for protected charts |
| W0.3 | 0 | [heavy] | Schema migration bundle | QUEUED | — | — | opus | none | Parallel W0; two-phase deploy (Phase A writer PR, Phase B migration) |
| W0.4 | 0 | [heavy] | Batched-context scoring engine | QUEUED | — | — | opus | none | Parallel W0; long pole |
| W0.5 | 0 | [adj] | Campaign rulings (UTK-R1/R2/R3) | QUEUED | — | — | ADJUDICATOR | none | ADJUDICATOR task, not a builder lane |
| W1.1 | 1 | [heavy] | Bounded λ_v3 core | QUEUED | — | — | opus | W0.4 PASS | Gate: W0.4 |
| W1.2 | 1 | [heavy] | Direction restored | QUEUED | — | — | opus | W1.1 PASS | Gate: W1.1 |
| W1.3 | 1 | [heavy] | Graded suppression | QUEUED | — | — | opus | W1.1 PASS | Gate: W1.1 |
| W1.4 | 1 | [heavy] | Self-normalizing thresholds | QUEUED | — | — | opus | W1.1 PASS | Gate: W1.1 |
| W1.5 | 1 | [mech] | λ decomposition + uncertainty output | QUEUED | — | — | sonnet | W1.1 PASS | Gate: W1.1 |
| W2.1 | 2 | [heavy] | Ashtakavarga gating, real | QUEUED | — | — | opus | W1.1 PASS | Parallel W2; needs W0.2 data |
| W2.2 | 2 | [mech] | Moorti nirnaya modifier | QUEUED | — | — | sonnet | W1.1 PASS | Parallel W2; needs W0.2 data |
| W2.3 | 2 | [mech] | Tara bala, alive | QUEUED | — | — | sonnet | W1.1 PASS | Parallel W2 |
| W2.4 | 2 | [heavy] | Sade Sati, fully | QUEUED | — | — | opus | W1.1 PASS | Parallel W2 |
| W2.5 | 2 | [mech] | Kota Chakra overlay | QUEUED | — | — | sonnet | W1.1 PASS | Parallel W2 |
| W2.6 | 2 | [mech] | Real eclipses | QUEUED | — | — | sonnet | W1.1 PASS | Parallel W2 |
| W2.7 | 2 | [heavy] | Annual context stack | QUEUED | — | — | opus | W1.1 PASS | Parallel W2 |
| W2.8 | 2 | [mech] | Bhava targets get degrees | QUEUED | — | — | sonnet | W1.1 PASS | Parallel W2 |
| W2.9 | 2 | [mech] | Citation resolution table | QUEUED | — | — | sonnet | W1.1 PASS | Parallel W2 |
| W3.1 | 3 | [heavy] | 27-class coverage | QUEUED | — | — | opus | W1.* PASS | No Wave-2 dep; can overlap W2 dispatch |
| W3.2 | 3 | [heavy] | Interval + chain shapes | QUEUED | — | — | opus | W1.4 PASS | Gate: W1.4 |
| W3.3 | 3 | [heavy] | Multi-resolution hierarchy | QUEUED | — | — | opus | W3.2 PASS | Gate: W3.2 |
| W3.4 | 3 | [heavy] | Century horizon + slice receipts | QUEUED | — | — | opus | W0.3 PASS + W3.2 PASS | Gate: W0.3 + W3.2 |
| W4.1 | 4 | [heavy] | λ contenders in the bakeoff | QUEUED | — | — | opus | W3.4 + ALL Wave-2 PASS | Gate: W3.4 + all W2.* |
| W4.2 | 4 | [heavy] | Negative-control harness | QUEUED | — | — | opus | W3.4 PASS | Gate: W3.4 |
| W4.3 | 4 | [heavy] | Ablation runner → grammar admissions | QUEUED | — | — | opus | W3.4 + ALL Wave-2 PASS | Gate: W3.4 + all W2.* |
| W4.4 | 4 | [heavy] | Weight fitting, cross-chart pooled | QUEUED | — | — | opus | W4.1 + W4.2 + W4.3 PASS | Gate: W4.1–W4.3 |
| W4.5 | 4 | [heavy] | empirically_calibrated, earnable + post-fit rebuild | QUEUED | — | — | opus | W4.4 PASS | Gate: W4.4; owns post-fit rebuild |
| W4.6 | 4 | [mech] | LEL mining (non-blocking) | QUEUED | — | — | sonnet | W3.4 PASS | Non-blocking; output is LEL_CANDIDATES_STAGED.md for native review |
| W5.1 | 5 | [heavy] | Serving elevation under density contract | QUEUED | — | — | opus | W3.3 + W4.5 PASS | Parallel W5 |
| W5.2 | 5 | [mech] | Nirmāṇa/DAG integration | QUEUED | — | — | sonnet | W3.3 + W4.5 PASS | Parallel W5 |
| W5.3 | 5 | [mech] | Docs-of-record | QUEUED | — | — | sonnet | W3.3 + W4.5 PASS | Parallel W5 |
| W5.4 | 5 | [heavy] | Writer repoint + mutation-guard evolution | QUEUED | — | — | opus | UTK-R1 + W0.3 + W3.4 PASS | Parallel W5; gate: UTK-R1 ruling + W0.3 + W3.4 |
| W6.1 | 6 | [ops] | Full-century production builds | QUEUED | — | — | ops | ALL W3/W4/W5 MERGED + W5.4 + W4.5 post-fit | Sequential; needs W5.4 repointed writer |
| W6.2 | 6 | [ops] | Three-legged replacement gate | QUEUED | — | — | VERIFIER | W6.1 PASS | Sequential |
| W6.3 | 6 | [ops] | Authority flip, rehearsed | QUEUED | — | — | ops | W6.2 PASS | Sequential; Abhinandan first, then native |
| W6.4 | 6 | [ops] | Retirement + rename | QUEUED | — | — | ops | W6.3 PASS | Sequential |
| W6.5 | 6 | [ops] | Campaign close | QUEUED | — | — | ops | W6.4 PASS | Sequential; final |

---

## §Rulings

*(No rulings yet — W0.5 ADJUDICATOR session pending)*

Ruling format: `UTK-R<N>: <topic> — <disposition>` with evidence link.

---

## §Wave Deployments

*(No wave deployments yet)*

Format: `WAVE N: DEPLOYED+SYNCED — revision <sha>, migrations applied through <N>, I6(b) rail check: <PASS/drift>`

---

## §I6(a) — DB Role Provisioning

**Status: PENDING** — `utkarsha_builder` Postgres role not yet provisioned. Requires ADJUDICATOR-reviewed migration/grant before any builder connects to DB. Migration to be authored in W0.5 session and reviewed before PR.

---

## §Event Log

- 2026-08-10: FIRST LAUNCH. Branch `utkarsha/campaign` created from origin/main (rev 3311ae0e3). LEDGER.md initialized. I6(c) snapshot recorded. I6(b) rail baseline recorded. Latest migration: 555 (id=414). All 34 lanes seeded QUEUED. ADJUDICATOR/VERIFIER not yet spawned. Wave 0 dispatch pending.
