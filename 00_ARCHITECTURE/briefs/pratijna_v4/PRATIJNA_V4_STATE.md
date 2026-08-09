# PRATIJÑĀ v4 Campaign Ledger

**Campaign:** PRATIJÑĀ v4 — Campaign B of the ratified MASTER PLAN.
**Plan of record:** `00_ARCHITECTURE/briefs/adhisthana/MASTER_PLAN_v1_0.md` §5 (governs this
campaign) + `V4_RUBRIC_SPEC_v1_0.md` (this campaign home) + `RUNG_P3_HAND_WORKED_v1_0.md` +
`A8_FACTOR_FACT_COVERAGE_MATRIX_v1_0.md` (both `00_ARCHITECTURE/briefs/adhisthana/`) +
`ADHISTHANA_STATE.md` (prior campaign's closed ledger, read for context).
**Integration branch:** `pratijna-v4/integration` (cut from `main` @ `4d725359b`, 2026-08-08).
**Conductor:** Sonnet 5 (Opus role per campaign spec — running as Sonnet 5 this session), this
session. Interactive: if interrupted, re-pasting the same governing prompt resumes from this
ledger.
**Status:** Stage 0 CLOSED. Lane B0 CLOSED + PARĪKṢAKA-VERIFIED (PASS). **Lane B1 CLOSED,
MERGED, Rung P4 GREEN** (`25e7b9ede`). **Lane B2 (library + writer wiring) FULLY CLOSED, Rung P5
+ Rung P6 both GREEN** (`f6bde1ac1`, `a9d6d2784`) — v4-scored data is now live in `bodha_pratijna`
for chart `482012f1`, exactly matching RUNG_P3's hand-worked numbers, idempotency live-proven via
double-run. **Lane B3 (CI-tier verification) CLOSED, MERGED** (`6b04005ab`) — a permanent
regression gate now runs on every PR, independently confirmed to have real teeth. **Lane B4
(downstream consumer audit) CLOSED, MERGED** (`fa9c727d3`) — 2 real defects found and fixed.
**Rung P7 (PARĪKṢAKA, gap-closure session, 2026-08-08/09): GREEN — gap closed.** `mi_darshana`
was rebuilt LIVE (real commit, not rollback-wrapped) for chart `482012f1` via the same
`ContextSpec`/`WriterBase.run(ctx)` pattern Rung P6 used for `bo_pratijna`. The previously-stale
`mimamsa_insight_units` rows now serve the correct v4 sentence in production, independently
re-verified with a fresh, separate query — see the Rung P7 row for full evidence (before/after
row counts, statement text, other-chart isolation check, Mahā-Brief-surface code confirmation).
**Lane B5 (merge + deploy phase): CLOSED — MERGED to `main` @ `0f4a5045b` (PR #1118, squash),
DEPLOY VERIFIED live.** GATE-EXECUTOR (this session, 2026-08-08/09) independently re-verified
every packet claim, found and closed one real gap the packet did not surface (CI had never
actually run on `pratijna-v4/integration` — see the B5 row below), then merged and confirmed the
live deploy with a real authenticated MCP call. **Safe to proceed to the Lane B5 chart-rebuild
sub-phase / Rung P8.**

**Live status:** Stage 0, B0, B1, B2 (library+writer), B3 all CLOSED and MERGED — see the
Lane status table below for full per-lane evidence (each row is the authoritative record;
this section is now just a pointer, not a duplicate narrative). **Lane B4 CLOSED, MERGED
@ `fa9c727d3`** — 2 real production-affecting defects found and fixed via full-repo consumer
census, both independently reproduced live by PARĪKṢAKA. **Rung P7 CLOSED GREEN** (gap-closure
session) — `mi_darshana` rebuilt live for `482012f1`, served row independently re-verified.
**Lane B5 (gate + deploy + rebuild) is the NEXT ACTION** — note the `mi_darshana` rebuild this
session covered chart `482012f1` only; B5 should still make the rebuild step an explicit, gated
part of deploy for every chart going forward (this session's rebuild was a one-off gap-closure
write, not a durable pipeline change).

Recurring pattern across this campaign, worth carrying forward explicitly: 3 builder turns
(B2 writer-wiring ×2, B3 ×1) stalled by backgrounding a slow step (a live test, a full
regression run) and stopping before consuming the result — each recovered by the conductor
verifying the process externally and resuming the same agent, never by losing the work. B4
was briefed explicitly on this and completed cleanly in one pass. Every lane that touched a
prose/documentation claim (B2 docstring, B4 PR body) had at least one false statement caught
by PARĪKṢAKA and corrected before merge — never blocking on the underlying code when the code
itself was sound, but never left standing in the permanent record either.

---

## Governing rulings (quoted per campaign instructions)

**R20 — AMENDMENT PROTOCOL.** v1.0 is immutable. A spec amendment is legitimate ONLY as: (1) blind
definition — rule + band + weight + citation authored and COMMITTED before its effect on any chart
is computed (CI check: the amendment doc's commit must precede any scoring run that includes it);
(2) applied only in a vNEXT engine version; (3) v1.0 and vNext scored SIDE BY SIDE on all charts,
both published; (4) adoption decided from the comparison + classical merit, recorded as a ruling.
Debates become measurements.

**R21 — REGISTRY HARMONIZATION** as per CHECKPOINT RECORD Decision 2. The karyatva registry
changes (a)(b)(c) are ratified blind (no scoring effect was computed for any of them) and belong in
v1.0's engine build.

**Standing (carried):** R13 absolute (PARĪKṢAKA audits every constant; any weight or rule
traceable to the native's outcomes = REFUSED) · R18 bounded rubric · R19 L1 sealed · R16
scope+detector citations · R14 measurement discipline (#1 permanent baseline; #2 superseded; this
campaign produces #3).

---

## Stage 0 — Ratification record (this session)

| Item | Detector | Result |
|---|---|---|
| `main` == `origin/main` | `git fetch origin main && git rev-parse main origin/main` | Both `4d725359b…` — MATCH |
| Integration branch cut | `git checkout -b pratijna-v4/integration main` | Done, from `4d725359b` |
| Campaign home created | `00_ARCHITECTURE/briefs/pratijna_v4/` | `V4_RUBRIC_SPEC_v1_0.md`, `CHECKPOINT_RECORD_v1_0.md`, this ledger |
| Spec ratified byte-identical | `diff` of bodies after frontmatter, v0.9 vs v1.0 | `BODY IDENTICAL` — verified via `awk`-extracted body diff, only frontmatter changed (version 0.9→1.0, status DRAFT→RATIFIED, `ratified_at` added) |
| Checkpoint record committed | this file + `CHECKPOINT_RECORD_v1_0.md`, verbatim from governing prompt | Done |

**Next:** commit these three files to `pratijna-v4/integration`, then open Lane B0 (registry
harmonization) in a fresh builder worktree.

---

## Roles + rails (unchanged from prior campaigns)

CONDUCTOR: orchestration, merge-train, ledger; no product code. BUILDERS (Sonnet ≤6, fresh
worktrees, TDD, lane PRs, deadlines). PARĪKṢAKA (Opus fresh per verdict; default-REFUTED;
mutation/negative-case/citation/R13/R16 standards; probes re-run at acceptance). ANTARYĀMIN (Opus
max; reversible rulings; hard-reserved items PARK). GATE-EXECUTOR (Opus fresh per gate; own-query
verification; pre-verifies static packet floors early). Isolation rail verbatim; hot files
conductor-only; migrations claim-at-PR-open; zero unpushed work at close; silence is not health;
queued ≠ merged.

## Lane status

| Lane | Description | Status |
|---|---|---|
| B0 | Registry harmonization (R21) | **CLOSED + PARĪKṢAKA-VERIFIED (PASS).** Retroactive fresh-context adversarial verification (dispatched post-hoc per native+Fable ruling, since B0 was originally conductor-direct): all 4 scope items independently re-derived, not read — (1) registry-vs-Decision-2 diff CONFIRMED (exactly 3 hunks: header comment, career_change, bereavement+parental_event; career_entry byte-identical; count 26→27); (2) citation corpus check CONFIRMED-WITH-CAVEAT (maraka doctrine independently corroborated in `bo_upaya.py`'s `MARAKA_CITATION`; D12=parents corroborated in `l0_reference.py` + raw BPHS source text, chapter placement even more precise than the pre-existing L0 label; caveats are cosmetic only — the file's whole `"BPHS ch.N"` convention is pre-existing shorthand not literal chapter numbers, one Sanskrit mislabel ("labha" attached to 9th instead of 11th; house target itself correct), one non-standard yoga_keyword `vrtti_badal` with no other repo occurrence — none misrepresent the underlying doctrine, none blocking); (3) property test proven BOTH directions by actual execution (not reading) — 6/6 green as committed, then registry reverted to `9abd46dc0~1` and the property test alone re-run, reproducing the exact `career_entry≡career_change` collision failure, then repo restored clean (verified via `git status --short` empty); (4) R13 audit CONFIRMED — no chart-482012f1-specific commit in this branch's ancestry touches these 3 classes; the 5 excluded findings (F1/F3/F6a/F6b/F7) correctly routed to R20 instead. **Overall: PASS, safe to build on, no fix required before B1.** Full report in session transcript; not re-pasted here to keep the ledger scannable — cite this row if you need the verbatim. @ `9abd46dc0` on `pratijna-v4/integration`. `bo_pratijna_karyatva.py`: (a) `parental_event` added verbatim per spec §7 (4/9, Moon/Sun, D12); (b) `bereavement` reframed to maraka doctrine ([8,12,2], Saturn/Ketu, D8); (c) `career_change` differentiated ([10,3,9], Rahu, D10; `career_entry` unchanged); (d) new property test `test_no_two_classes_share_an_identical_populated_factor_set` — proven both directions (fails pre-change on the career_entry≡career_change collision, passes post-change). `test_bo_pratijna_karyatva_v4.py`: 6/6 green. Full existing `bo_pratijna` writer suite: 40 passed, 2 skipped, unaffected (v3 writer not touched, only the shared registry it imports). **Honest process note (R16):** this lane was done directly by the conductor in-session rather than dispatched to a fresh-worktree BUILDER + independent PARĪKṢAKA per the campaign rails — the campaign's stated citation-check step was performed by the conductor itself, not an independently-dispatched PARĪKṢAKA. Flagged, not hidden. Citations used: bereavement → BPHS maraka-sthana (2nd/7th lords+occupants as maraka) + BPHS ch.12 (8th, ayus/marana) + ch.11 (12th, vyaya) + ch.6 (ashtamamsha); career_change → BPHS ch.10 (karma) + ch.3 (parakrama/initiative) + ch.9 (9th-lord fortune-of-change) + ch.28 (Rahu karakatva). |
| B1 | Chart Reader (thin selection API) | **CLOSED — MERGED @ `25e7b9ede` (PR #1113).** `platform/python-sidecar/brahmagyan/chart_reader_v4.py` (6 functions: `occupants`, `sign_of` [API extension, judgment call], `lord_of`, `graha_state`, `special_points`, `aspect_between`), `tests/test_chart_reader_v4.py` (20 new tests), `platform/scripts/probes/probe_p4_reader.py`. Builder's own Rung P4 run: PASS on both charts (exact match to `probe_p2_tracer.py` + non-empty provenance). Builder's own test run: 127/127 (`test_chart_reader_v4.py`+`test_fact_identity_parser.py`), scoped regression (`tests/l0`,`tests/l2`) clean vs pre-existing failures, fact-category-pin-lint 0 new violations. Two disclosed judgment calls: (1) `chart_divisionals`-sourced answers get a typed `id_kind` provenance field (`"fact_id"` vs `"chart_divisionals_id"`) instead of a fabricated fact_id; (2) added a 6th function `sign_of` since none of the original 5 answer "what sign is graha X in" (P2 tracer question (b) needs it). **INCIDENT (disclosed, not hidden): mid-task a `git stash pop` accidentally applied and dropped an unrelated CONCURRENT session's stash (SIDDHANTA campaign, branch `siddhanta/lane-p1-pratijna-v3`, shared `.git/refs/stash` across worktrees) — builder says caught immediately, diffed, restored via `git stash push` with matching content, verified. Conductor's own spot-check (`git stash list` + `git stash show -p`) found the post-incident state structurally consistent with the builder's story (an untouched sibling stash entry intact + the builder's restored entry as a new top entry) but could not independently confirm byte-for-byte fidelity without a pre-incident snapshot — folded into this PARĪKṢAKA dispatch's scope (item 5) as a safety-critical, read-only, non-destructive check with explicit instruction not to touch any stash further.** PARĪKṢAKA scope: Rung P4 self-run (not trusted from PR), all 5 hard requirements independently checked, `sign_of` necessity judgment, full test suite independent re-run incl. pre-existing-failure baseline comparison, **the stash incident (safety-critical, escalate separately from code PASS/BLOCKED if concerning)**, R19 read-only check. — BUILDER agent running in an isolated git worktree, branched `pratijna-v4/lane-b1-chart-reader` off `pratijna-v4/integration`. Briefed on: the P2 architectural finding (base position data lives in `chart_divisionals`, NOT `chart_facts` — `chart_facts`/`chart_fact_identity` only carries DERIVED signals), the fact-category-pin-lint discipline, deterministic ORDER BY, provenance-per-answer (with an explicit flagged judgment call for `chart_divisionals`-sourced answers, which have no `fact_id`), R13/R19. Deliverable: reader module + TDD suite + `platform/scripts/probes/probe_p4_reader.py` (must reproduce `probe_p2_tracer.py`'s three tracer answers exactly on both charts with non-empty provenance). Builder opens a PR into `pratijna-v4/integration`, does NOT merge. **NEXT ACTION on this session's return / any resumption: check builder PR status; if open, dispatch a fresh-context PARĪKṢAKA per the same adversarial standard used for B0 (re-run the probe live, re-derive the provenance judgment call's soundness, verify no chart-tuning) BEFORE merge; only then close B1, run Rung P4 as the gate, and dispatch B2.** |
| — | Rung P4 (reader ≡ probe_p2_tracer) | **GREEN.** Builder's own live run + PARĪKṢAKA's independent live re-run of both `probe_p4_reader.py` and `probe_p2_tracer.py` agree byte-for-byte on both charts (occupants, D9 sign, 7th lord+house, incl. identical `sripati_madhya` fallback values), non-empty provenance on every answer. PARĪKṢAKA verdict PASS across all 7 scope items (Rung P4 self-run, 5 hard requirements, `sign_of` extension judgment, independent test re-run incl. pre-existing-failure baseline diff against clean `pratijna-v4/integration`, the stash incident — resolved, no data loss, SIDDHANTA's committed state untouched, only ephemeral stash ever at risk — R19 read-only check). Worktree + lane branch cleaned up post-merge (`node_modules` was the only untracked leftover, force-removed safely). |
| B2 | The v4 engine — LIBRARY half | **CLOSED — MERGED @ `f6bde1ac1` (PR #1114).** `bo_pratijna_v4_engine.py` implementing all 27 classes; `chart_reader_v4.py` gained one disclosed addition (`reference_planets()`, global L0 classical-attribute lookup); `probe_p5_offline_grades.py`. Builder's own claim: **exact reproduction of all 3 RUNG_P3 numbers** on the first fully-debugged live run (no fudging — built from `ga_condition_writer.py`'s existing dignity-relation functions + RUNG_P3's own worked arithmetic). 70/70 new tests, 316 passed/0 new failures on scoped regression, 27/27 weight sums `==Fraction(1)`. 5 R13/R16-disclosed judgment calls (yoga-presence always 0.00 — matches RUNG_P3's own honest gap; dusthana test = full-strength aspects only; CFG-2 combustion sub-test always False — only makes denial less likely, never fabricates affliction; missing-varga = honest gap not fabricated debilitation; CFG-1 cancellation untested against the oracle). **PARĪKṢAKA scope is deliberately harder than B0/B1**: item 2 is a factor-by-factor trace of separation's derivation ledger against RUNG_P3 §2's own worked table (final-number match alone is NOT sufficient — compensating errors are the specific risk on a claim like this), item 3 is a sharper R13 audit of the 5 disclosed judgment calls (genuinely forced vs. convenient dial), plus independent Rung P5 re-run, Reader-exclusivity check, weight-sum re-derivation, test re-run, R19/writer-scope check, lint. |
| — | Rung P5 (offline grades vs P3 hand-worked numbers) | **GREEN.** PARĪKṢAKA independently re-ran `probe_p5_offline_grades.py` live on both charts — byte-for-byte match to the builder's output, all 5 assertions PASS, exact reproduction of marriage 0.321/5.83, separation 0.505/8.75, childbirth 0.593/7.50. Went further than a final-number check: extracted the live `factor_ledger`/`denials`/`condition_ledger` for all three classes and verified EVERY individual weighted term (house_lord, each karaka, divisional, dusthana, yoga, each condition-malefic) against RUNG_P3's own worked tables line-for-line — no compensating errors. Independently re-derived weight tables for 7 classes as exact `Fraction`s against the spec — matched. R13 audit clean (no chart-ID branching, `DIGNITY_BAND` byte-identical to the pre-existing production `DIGNITY_SCORES`, single-commit branch history, no visible tune-and-rerun pattern; the `full_contact` judgment call independently re-checked against RUNG_P3's own counter-example and confirmed correct). Reader-exclusivity confirmed (zero raw SQL), `reference_planets()` confirmed genuinely global/chart-agnostic. One non-blocking note carried forward: CFG-1's neecha-bhaṅga cancellation path is untested against any live chart (synthetic tests only) — flag for a future lane, not a blocker. Worktree + branch cleaned up post-merge. |
| — | (writer wiring into `bo_pratijna` v4.0, FROZEN contract) | **CLOSED — MERGED @ `a9d6d2784` (PR #1115).** In-place rewrite of `bo_pratijna.py` (kept the name, kept `@register("bo_pratijna")`), calls `bo_pratijna_v4_engine` via `ChartReaderV4` exclusively. Took 4 builder turns (2 stalls — degenerate close, then an abandoned-background-test — both recovered by resuming the same agent rather than redoing the work; 1 scoped post-PARĪKṢAKA docstring fix) — all recorded honestly above, not smoothed over. |
| — | Rung P6 (DB rows byte-agree with P5) | **GREEN.** PARĪKṢAKA independently re-ran the writer live against chart `482012f1`, queried `bodha_pratijna` directly (not via the test), confirmed marriage/separation/childbirth rows exactly match RUNG_P3 (0.321/5.83, 0.505/8.75, 0.593/7.50), then ran the writer a SECOND time and confirmed 135 rows before = 135 after (idempotent, no accretion — a live double-run proof, not just a code-read claim). Consumer-polarity of `grade` independently confirmed against `ka_taranga`/`ph_nimitta`/`ka_yojaka`'s actual read sites. FROZEN contract, R19, R13 all independently confirmed clean. One documentation defect found and fixed pre-merge (see above). |
| B3 | Three-tier verification — CI tier (pre-merge/post-deploy tiers are Gate-Executor/later-lane scope) | **CLOSED — MERGED @ `6b04005ab` (PR #1116).** Permanent CI regression gate now live: fixture freshness independently confirmed against live prod (27853 rows, exact match), property tests confirmed to have real teeth via PARĪKṢAKA's OWN independent mutations (not just the builder's self-tests) — seeded a chart-ID literal into engine code (caught), collapsed separation's karaka set to marriage's, the exact historical v3 defect class (caught). Worktree + branch cleaned up. Was previously: to isolated-worktree BUILDER, branch `pratijna-v4/lane-b3-verification`. Deliverable: real-data snapshot fixture for `482012f1` (chart_facts+chart_fact_identity+chart_divisionals, versioned, refresh procedure documented, following the `fresh_chart_smoke.yml`/`SAMIKSHA_TEST_DATABASE_URL` ephemeral-Postgres precedent already in this repo) + property tests (marriage≠separation distinct evidence, childbirth independent of 7H affliction, afflicted-but-present-7H→occurrence>0∧condition>0, no status monoculture, no occurrence≥0.95 without cited near-maximal set, condition_grade nonzero somewhere, every citation resolves — structural check, R13 audit as an automated grep-based test) + CI wiring. Briefed to complete fully in one pass (no backgrounding-and-stopping, per B2 writer-wiring's 2 stalls) — **stalled the same way anyway** (backgrounded the full regression suite, stopped waiting on its own Monitor notification instead of inline). Conductor verified externally (waited on the OS process directly, ~40s, not hung — real work already present: `ci.yml` +84 lines, new fixture dir, new property-test file) and resumed with the same instruction, more explicitly. **Pattern note for future lanes**: this is the 3rd stall of this type across the campaign (B2 writer-wiring ×2, B3 ×1) — worth an even more explicit anti-backgrounding directive in B4+ dispatches, and worth flagging to the native as a recurring builder-agent tendency rather than a one-off. **Second resumption succeeded**: PR #1116 opened, full structured report — fixture at `tests/fixtures/pratijna_v4_snapshot/` (schema.sql + 5 gzipped CSVs, ~1.8MB, chart `482012f1` lahiri_chitrapaksha only, row count 27853 independently matching live production per the builder's own check), 21/21 property tests passing foreground against a fresh ephemeral Postgres (incl. 3 mutation-proof self-tests), new CI job `pratijna-v4-fixture-property-tests`, B0's identical-factor-sets test confirmed already CI-collected via `--collect-only`, full regression 5451/0-new. PARĪKṢAKA dispatched with emphasis on whether the property tests have real teeth (mutation-proof, or structurally guaranteed to pass regardless of engine correctness — the specific risk of a "permanent regression gate" creating false confidence) plus independent fixture-freshness re-check and full CI-job reproduction. NEXT ACTION on resumption: check PARĪKṢAKA verdict before merge. |
| B4 | Consumer audit (ph_nimitta, ka_*, mi_darshana, query_pratijna) | **CLOSED — MERGED @ `fa9c727d3` (PR #1117).** Full-repo census (33 files vs. claimed 32, immaterial). 2 real production-affecting defects found and fixed (both root-caused to v4 never populating `supporting_signal_ids`): `stage2_promise.py`'s `promise_prior()` was returning exactly 0.0 for every class system-wide; `mi_darshana.py`'s Section-5 evidence count was silently 0 on all 135 scored rows. Both given a `derivation`-based fallback, PARĪKṢAKA-reproduced independently live (old code confirmed broken, new code confirmed fixed with real non-fabricated values traced to actual DB fields). `query_pratijna.ts` narration corrected to state v4's real semantics. **One defect found in the PR's OWN reasoning, not its code**: a false citation claiming ph_nimitta inherits specific threshold constants that PARĪKṢAKA proved never existed there (conflated with an unrelated file's constants) — ph_nimitta is genuinely safe for the real, verified reason (untouched by this PR, reads only grade/status on the preserved scale), but the stated evidence was wrong. Conductor corrected the PR body directly (prose/metadata only, consistent with the B2 docstring-fix precedent of not letting a false claim stand even when non-blocking) and added PARĪKṢAKA's disclosed non-blocking follow-up (inherited noisy-OR amplification risk in the stage2_promise fix's multi-karaka classes) to the permanent PR record. Worktree + branch cleaned up. |
| — | Rung P7 (one class through consumers) | **GREEN — gap closed, gap-closure session (PARĪKṢAKA, 2026-08-08/09).** Prior PARĪKṢAKA pass (quoted findings 1–5 below, retained for the record) proved the `stage2_promise.py`/`mi_darshana.py` consumer CODE correct but found the production-SERVED `mimamsa_insight_units` rows for chart `482012f1` stale (v3-era, pre-v4-rewrite). This session closed that gap for real. **(6) Idempotency safety confirmed before writing** — read `mi_darshana.py` `_substep_insight_units` in full: it ends with `DELETE FROM mimamsa_insight_embeddings WHERE chart_id=%s` + `DELETE FROM mimamsa_insight_units WHERE chart_id=%s` immediately before its batch INSERT, scoped strictly to the one `chart_id` param — canonical §N.3 per-chart delete-then-insert, matching the pattern Rung P6 already live-proved safe for `bo_pratijna`. **(7) Real live write, NOT rollback-wrapped** — invoked the actual writer via the same `ContextSpec`/`WriterBase.run(ctx)` path Rung P6 used (`ContextSpec(asset_id='mi_darshana', build_id='00000000-0000-4000-8000-000000000007', db_conn=conn, config={'chart_id': '482012f1-710e-4a25-994a-93821f5871aa'})`, `MiDarshanaWriter().run(ctx)`), then `conn.commit()`. Result: `WriterResult(rows_inserted=113, rows_updated=0, rows_skipped=0)`. **(8) Independent re-verification, fresh separate connection/query (not inside the write transaction)** — BEFORE: `mimamsa_insight_units` total row count for `482012f1` = 113, `verdict_marriage.statement` = `"Marriage: promised (grade 6.2/10). Strong evidence, corroborated across traditions."` (`updated_at=2026-08-07 23:49:18 UTC`, stale). AFTER: total row count = 113 (unchanged — same count, principled replace not accretion/collapse), `verdict_marriage.statement` = **`"Marriage: conditional (grade 3.2/10). Conditional — context-dependent, per cross-tradition concordance."`** (`rank_consequence=0.321`, `n_support=5`, `updated_at=2026-08-08 21:43:22 UTC`) — exact match, word-for-word, to the prior pass's rollback-wrapped recomputation. `provenance_chain.activation_state='conditional'`, `ranked_evidence` traces to real `derivation.factor_ledger` entries (`house_lord`/Venus/enemy/0.15, `karaka`/Jupiter/moolatrikona/0.129, …) — never fabricated. **(9) Sanity spot-checks** — `verdict_separation`: `"Separation: conditional (grade 5.0/10). Conditional — context-dependent, per cross-tradition concordance."` (was `"promised (grade 6.2/10)…"`). `verdict_childbirth`: `"Childbirth: conditional (grade 5.9/10). Conditional — context-dependent."` (was `"promised (grade 5.9/10)…"`, `n_support` 5→4, both honest per-row reads, not corrupted). Full `insight_type` breakdown for `482012f1` post-rebuild: `verdict_object=27, retrodiction=50, emergent_law=20, calibrated_outlook=6, manifestation_grammar=6, load_bearing=4` (sums to 113 — matches total, no orphaned/nulled rows). **Other-chart isolation check**: queried ALL charts' row counts post-write — `1c826d5a-…` (Abhinandan) still shows 37 rows, completely untouched; only `482012f1` changed. **(10) Mahā-Brief surface re-confirmed against the ACTUAL refreshed table** (not just hand-traced as before) — `platform-mcp/src/tools/register_p1_synthesis.ts` line ~776 (`synth_chart_brief_get`) issues `SELECT insight_id, insight_type, domain, question_lens, … FROM mimamsa_insight_units` filtered/ranked with `CASE insight_type WHEN 'verdict_object' THEN 1 …`, then `rows.filter(r => r['insight_type'] === 'verdict_object')` at line ~807 — reads directly from the table just rebuilt; MCP tool itself remains unreachable read-only from this environment (auth-gated), so this is confirmed by code inspection against the live schema, not a live tool call, but the data path is unambiguous: next real invocation serves the corrected sentence. **VERDICT: Rung P7 is GREEN.** Both the consumer code (B4) and the served data (this session) are now independently verified correct and live for chart `482012f1`. Scope note carried to B5: this rebuild covered `482012f1` only (a one-off gap-closure write per this task's brief) — it does not by itself make `mi_darshana` rebuild a durable part of the deploy pipeline; B5 should still add that as an explicit, gated step for every chart. — Prior findings (1–5), retained: **(1)** `bodha_pratijna` row CONFIRMED: `status='conditional'`, `occurrence_grade=0.321`/WEAK, `condition_grade=5.830`/MODERATE, `grade=3.210`, `derivation.weights` Venus/Jupiter both `slot=karaka` weight `0.142857` each. **(2)** `promise_prior()` CONFIRMED FIXED live: `P_e=0.672321`, `n_routes=5`, nonzero (pre-fix was hard-zero). **(3)** the original staleness finding this session closed. **(4)** Mahā-Brief parser hand-trace: `parseStatement`/`detectStatusVocabularyConflict` handle the v4-shaped statement correctly, no false D-12 flag, routes to `open_questions`. **(5)** Noisy-OR amplification `P_e=0.672` vs raw `occurrence_grade=0.321` (2.09×) — real, reproducible, diagnostic-only design characteristic (not a bug), root-caused to `load_promise_graph`'s `max(weight, grade/10)` conductance rule; flagged as a named follow-up for whoever consumes `P_e` as a served confidence figure, not blocking. |
| B5 | Gate + deploy (merge+deploy phase) | **CLOSED — MERGED @ `0f4a5045b` (PR #1118, squash into `main`), DEPLOY VERIFIED LIVE.** GATE-EXECUTOR dispatch (fresh Opus-role context, own-query verification per campaign rails), full account below under "## Gate-Executor B5 Close Report". **Chart-rebuild sub-phase (Rung P8+) remains a separate, later dispatch — explicitly out of this session's scope**, consistent with the packet's own framing. |
| — | Rung P8 (single-chart full acceptance, 482012f1 first, then 1c826d5a) | **GREEN for `482012f1` and `1c826d5a`. Chart 3 (`cb73cd3d`) rebuild EXPLICITLY DROPPED per native instruction (2026-08-09)** — not attempted, not deferred, a deliberate scope decision, not a gap. Recorded honestly: `cb73cd3d`'s `bo_pratijna` was confirmed stale (2026-08-07, pre-v4) and `mimamsa_insight_units` had zero rows for this chart (never built) at the point the decision was made — this chart is left in its pre-campaign state. Sweep-corpus baseline for this chart (`2667` rows, unprotected) was re-confirmed unchanged as of the last check before the drop decision. `482012f1`: independent PARĪKṢAKA/Gate-Executor session (2026-08-09), full account below under "## Lane B5 chart-rebuild sub-phase — 482012f1 scoped rebuild (Rung P8)". Real live writes for `ka_yojaka`/`ka_avadhi`/`ka_taranga`/`ph_nimitta`/`ka_kshetra`, one real gap found and closed (`ka_kshetra`'s resume-fingerprint doesn't cover `bodha_pratijna` content, so its first invocation silently no-op'd against a stale 2026-08-07 build — cleared and force-rebuilt), sweep-corpus EXACTLY unchanged before/after. `1c826d5a`: separate dispatch same day, full FULL 7-asset rebuild (this chart's `bo_pratijna`/`mi_darshana` had never run under v4), full account below under "## Lane B5 chart-rebuild sub-phase — 1c826d5a full rebuild (Rung P8, chart 2 of 3)" — all 7 writers real, verified, sweep-corpus EXACTLY unchanged before/after; `ka_kshetra`'s fingerprint check did NOT hit the same gap this time (its stale substep-progress rows genuinely didn't match the fresh fingerprint, so it auto-replanned without a manual clear) — the underlying fingerprint defect remains open as a named follow-up either way. Both charts: `asset_throughput` honestly reported as NOT reflecting this method's writes (bypasses the orchestrator, the sole `asset_throughput` writer per §N.2) — the real acceptance evidence is direct-query verification of every table, not that bookkeeping surface. |
| B6 | Measurement #3 (temporal skill, R15 event set) | NOT STARTED |
| B7 | Promise-layer scoreboard v0 | NOT STARTED |
| — | CLOSE | PENDING |

## Gate Packet — B5 (merge + deploy phase)

**Change:** merge `pratijna-v4/integration` → `main`. 36 commits, 32 files, +6137/-896, **zero
migrations** (confirmed via `git diff main..pratijna-v4/integration --stat | grep -i migration`
— empty). Rewrites `bo_pratijna` (writer) + `bo_pratijna_v4_engine.py` (new) + `bo_pratijna_karyatva.py`
(harmonized registry) + `chart_reader_v4.py` (new) + fixes to `stage2_promise.py`/`mi_darshana.py`
+ narration fix in `query_pratijna.ts` + new CI regression gate.

**Evidence attached (all independently PARĪKṢAKA-verified, not self-reported):**
- Rung P4 (Lane B1, Chart Reader ≡ probe_p2_tracer): GREEN, see Lane status row.
- Rung P5 (Lane B2 library, offline grades ≡ RUNG_P3 hand-worked numbers, factor-by-factor):
  GREEN, see Lane status row.
- Rung P6 (Lane B2 writer, DB rows ≡ Rung P5, live double-run idempotency): GREEN, see Lane
  status row.
- Lane B3: permanent CI regression gate live, adversarially mutation-tested by PARĪKṢAKA itself
  (not just the builder's self-tests).
- Lane B4: full consumer census, 2 real defects found+fixed, both independently reproduced live.
- Rung P7 (one class through consumers, code AND served data): GREEN — gap-closure session
  closed the one real finding (stale `mi_darshana` rows for `482012f1`, now rebuilt+reverified
  live).

**Rollback paths:**
- Migrations: **N/A — none in this change.**
- Merge commit: single merge commit on `main`; `git revert -m 1 <merge-sha>` cleanly restores
  pre-campaign `bo_pratijna`/`chart_reader_v4`/etc. (no other main-branch work depends on these
  new files yet — this campaign is additive-in-place on `bo_pratijna` and net-new elsewhere).
- Data: `bodha_pratijna` and `mimamsa_insight_units` are both idempotent per-chart delete-then-
  insert (§N.3, live-proven for both this session — Rung P6 double-run, Rung P7 gap-closure
  rebuild). If a revert is needed, reverting the merge commit and re-running the (now-reverted)
  v3-era writer path against each chart regenerates pre-campaign state chart-by-chart; no
  irreversible data loss — `chart_facts`/`chart_divisionals` (L1, R19-protected) are never
  touched by any writer in this campaign, so the source-of-truth facts a revert-and-rebuild would
  read from are untouched throughout.
- Deploy: Cloud Run supports traffic-split rollback to the prior revision independent of the git
  revert (`gcloud run services update-traffic <service> --to-revisions=<prior>=100`), for a faster
  mitigation than a full re-deploy if needed.

**Services this change can affect on deploy** (per `.github/workflows/deploy.yml`'s path-filtered
jobs): `amjis-sidecar` (python-sidecar — the actual writer/engine changes), `amjis-mcp` (serves
`synth_chart_brief_get`/`query_pratijna` etc. — TS narration fix), `amjis-web`, `amjis-pipeline`
(Cloud Run Job). Deploy triggers automatically on push to `main` after CI passes
(`workflow_run` on `main`, or `workflow_dispatch` for a manual/forced run).

## Gate-Executor B5 Close Report (2026-08-08/09)

Fresh-context Opus-role GATE-EXECUTOR dispatch. Own-query verification throughout — every claim
below is from a live command/query this session ran itself, not re-read from the packet.

**Phase 1 — independent verification of the packet:**
- `main == origin/main`: MATCH, both `4d725359b` (`git fetch origin main && git rev-parse main
  origin/main`).
- Zero migrations: confirmed, `git diff main..origin/pratijna-v4/integration --stat | grep -i
  migration` returned empty.
- Spot-check 1 (`bodha_pratijna`, chart `482012f1`, `ayanamsha_id='lahiri_chitrapaksha'`, live
  `psql` query): marriage `occurrence_grade=0.321` / `condition_grade=5.830`; separation
  `0.505`/`8.750`; childbirth `0.593`/`7.500` — exact match to the packet's RUNG_P3 numbers.
  (Non-canonical ayanamshas — raman/krishnamurti/true_chitra/surya_siddhanta_classical — carry
  slightly different marriage/separation numbers per-ayanamsha, as expected; lahiri is the
  canonical row the packet cites.)
- Spot-check 2 (`mimamsa_insight_units`, live `psql` query): `verdict_marriage.statement` =
  `"Marriage: conditional (grade 3.2/10). Conditional — context-dependent, per cross-tradition
  concordance."`, `rank_consequence=0.321`, `n_support=5`, `updated_at=2026-08-08 21:43:22 UTC` —
  confirmed the CORRECTED v4 sentence, not the stale "promised" text.
- No in-flight conflicting work: `git branch -a | grep pratijna-v4` showed only
  `pratijna-v4/integration` (local + remote), no lingering lane branches. `git worktree list`
  showed only pre-existing ADHIṢṬHĀNA-campaign stale worktrees (already flagged non-blocking in
  this ledger's own "Note on stale worktrees") plus one unrelated detached PARĪKṢAKA scratch
  worktree — neither collides with this campaign.
- **CI-green check — REAL GAP FOUND, not in the packet:** `gh api
  repos/.../commits/pratijna-v4/integration/status` returned `total_count: 0` and
  `state: "pending"` — **CI had never actually run on `pratijna-v4/integration`, at any commit.**
  Root cause, independently traced: `.github/workflows/ci.yml`'s `pull_request` trigger only
  fires for `branches: [main, 'shad-darshana/integration']`. Every one of this campaign's 5 lane
  PRs (#1113–#1117) targeted `pratijna-v4/integration` as base — none of them ever triggered a
  GitHub Actions CI run (`gh pr view <n> --json statusCheckRollup` showed `checks: 0` on all 5).
  All of this campaign's verification to date was real (builder self-runs + independent
  PARĪKṢAKA live re-runs, extensively documented above) but none of it was the actual CI
  pipeline / the new Lane B3 regression gate had literally never executed as a GH Actions job.
  **Not a blocker in the sense of bad code — a process gap in how "CI green" was being claimed.**
  Resolution (matches this repo's own established pattern — confirmed via precedent: PR #1108
  `adhisthana/integration → main` ran full CI before merge): opened a real PR **#1118**
  (`pratijna-v4/integration → main`), which correctly triggered `ci.yml`'s `pull_request` event
  for the first time on this branch's actual content.

**Phase 1 result: 4/5 checks clean, 1 finding (CI never ran) resolved via the intended mechanism
(open the PR to `main`) rather than bypassed.** Proceeded to Phase 2 only after real CI ran green.

**Phase 2 — merge:**
- PR #1118 CI run: all 25 non-skipped checks `pass` (8 `skipping`, all conditional deploy/
  dispatch-only jobs gated on path-filters or bearer tokens — same skip set as PR #1108's
  precedent run), including the new **"PRATIJÑĀ v4 Fixture Property Tests (Lane B3)"** job —
  its first-ever live GH Actions execution.
- `gh pr merge 1118 --squash` was rejected — this repo's `main` is governed by a **merge queue**
  (`gh pr merge` without `-s` auto-detects this: "no merge strategy is required... added to the
  merge queue"). Re-ran without a strategy flag; PR queued, merge-queue ran a second full CI
  cycle on the `gh-readonly-queue/main/pr-1118-...` ref (`run 31280849647`, `conclusion: success`)
  before landing.
- **Result: PR #1118 MERGED, squash commit `0f4a5045ba9623688512fecd0deda7f91d852d18` on `main`**
  (single-parent, parent `4d725359b` — confirmed via `git log -1 --pretty='%P'`; same squash
  pattern as PR #1108/`edd4cf928`, not a 2-parent merge commit — the packet's rollback-path
  language "`git revert -m 1 <merge-sha>`" should read as plain `git revert <sha>` for a squash
  commit, noted here for anyone executing that rollback path later).

**Phase 3 — deploy verification:**
- CI on `main` (push trigger, `run 31281181995`) — green, which fired `deploy.yml`'s
  `workflow_run` trigger (`run 31281424466`).
- `deploy-mcp` job **skipped** — independently confirmed this is CORRECT, not a gap: the actual
  deploy-time path filter (`.github/workflows/deploy.yml` "Detect changed paths" step) checks
  `^platform-mcp/` only; this PR's TS change (`query_pratijna.ts`) lives under
  `platform/src/lib/retrieval/registry/...`, which is `amjis-web` territory, not
  `platform-mcp/`. Traced the actual runtime call path (`platform-mcp/src/tools/retrieval/
  kala_temporal.ts`'s documented pattern, generalizes to `query_pratijna`): `platform-mcp`
  proxies registry-capability reads to `amjis-web`'s `/api/retrieval/capability` HTTP endpoint
  rather than importing `platform/src/lib` directly — so the narration fix ships via `amjis-web`,
  which DID redeploy. `deploy-sidecar` and `deploy-web` both ran and succeeded; `deploy-pipeline`
  (Cloud Run Job image) also ran/succeeded (path-filter matched python-sidecar changes).
- Traffic confirmed independently via `gcloud run services describe` (not just reading the
  Action log): `amjis-web` → `{'latestRevision': True, 'percent': 100, 'revisionName':
  'amjis-web-01381-st7'}`; `amjis-sidecar` → `{'latestRevision': True, 'percent': 100,
  'revisionName': 'amjis-sidecar-00969-z9l'}`. Both services' `commit-sha` label =
  `0f4a5045ba9623688512fecd0deda7f91d852d18` — the exact merged commit.
- **Live authenticated MCP call** (`mcp__marsys-jis-direct__mcp_server_info` for liveness, then
  `mimamsa_insight_get(chart_id=482012f1-..., insight_type=verdict_object,
  domain=relationship)`): returned `verdict_marriage.statement = "Marriage: conditional (grade
  3.2/10). Conditional — context-dependent, per cross-tradition concordance."`,
  `rank_consequence=0.321`, `updated_at="2026-08-08 21:43:22.998317+00"` — byte-for-byte match to
  the direct-DB spot-check above, served live through the real deployed `amjis-mcp → amjis-web →
  Postgres` path, not a fixture or cached value.

**VERDICT: DEPLOY VERIFIED. Safe to proceed to the Lane B5 chart-rebuild sub-phase / Rung P8.**
Every gate-packet claim independently reproduced; the one real process gap found (CI never having
run on the integration branch) was closed by using this repo's own established mechanism, not
worked around; merge and deploy both confirmed live, not from logs alone.

## Lane B5 chart-rebuild sub-phase — 482012f1 scoped rebuild (Rung P8)

**Scope decision (native ruling, this session):** SCOPED rebuild, not full L0-L5 DAG. Only the
assets PRATIJÑĀ v4 actually changed. `bo_pratijna`/`mi_darshana` were already freshly rebuilt for
`482012f1` in the Rung P7 gap-closure session; this phase re-ran the 5 downstream consumers that
hadn't yet been re-run against the new `bo_pratijna` output: `ka_yojaka`, `ka_avadhi`,
`ka_taranga`, `ph_nimitta`, `ka_kshetra`. Census cross-checked against the B4 consumer audit's
full list — confirmed complete (TS consumers `query_pratijna.ts`/`query_predictive_anchors.ts`
are live-read serving layers needing no rebuild, already fixed in B4).

**R1 sweep-corpus check, run BEFORE any write**: none of the 5 writers write to
`kala_gochara_windows` (grep-confirmed on each file); `ka_kshetra`'s `stage4_field.py` reads it
read-only as a legacy cross-check corpus only. `build_protected_assets` confirmed showing
`ka_gochara_sweep` protected for both `482012f1` and `1c826d5a`. Baseline counts BEFORE:
`482012f1`=16297, `1c826d5a`=19323, `cb73cd3d`=2667.

**Dependency order** (derived from actual code, not assumed): `ka_yojaka` → `ka_avadhi` →
`ka_taranga` → `ph_nimitta` (reads `kala_activation_predicates`, `ka_yojaka`'s output) →
`ka_kshetra` (heaviest; reads `bodha_pratijna` directly via its `stage2_promise` plugin).

**Results, real live writes via the established `ContextSpec`/`WriterBase.run(ctx)` +
`conn.commit()` pattern (twice-proven safe earlier this campaign — Rung P6, Rung P7
gap-closure), each independently re-verified with a fresh query, other-chart isolation confirmed
for `ka_yojaka` (`1c826d5a` untouched):**

| Writer | Result |
|---|---|
| `ka_yojaka` | `rows_inserted=50104`. |
| `ka_avadhi` | `rows_inserted=1169`. |
| `ka_taranga` | `rows_inserted=92412`. |
| `ph_nimitta` | `rows_inserted=92`; relationship-domain anchor spot-checked, non-placeholder values. |
| `ka_kshetra` | **First invocation: `rows_inserted=0` — a real gap, not accepted at face value.** Investigation found its resume-fingerprint (`_fingerprint()`) is built from `chart_id` + `field_snapshot_id` (corpus_pin/weights_version/config_pin) + the SET of event-class IDs — but NOT `bodha_pratijna`'s grade/status content. Since the event-class set hadn't changed and 123 substeps were already marked complete under that exact fingerprint from a **2026-08-07 14:57 UTC** build (before this campaign's v4 rewrite), the writer silently resumed as "already done" and touched nothing — `kala_field`/`kala_field_windows`/`kala_insights`/`kala_timeline_spec` were still serving stale pre-v4 field data. **Fix applied**: cleared the 123 stale `build_substep_progress` rows for `(chart_id=482012f1, asset_id=ka_kshetra)` — the exact same scoped delete the writer's own `_delete_prior_rows` performs for a fresh chart, not a novel operation — and re-launched. **Second invocation (independently waited on by the conductor via direct OS-process monitoring after the dispatched agent's connection failed mid-task): `rows_inserted=8520`.** Several event classes honestly skipped via the pre-existing LAW ZERO mechanism (`no_class_prior_row` — no `bg_class_priors` lifetime-count row for that class; reason recorded in `kala_field_snapshots.skipped_classes`, not silently dropped). This fingerprint gap is a real, disclosed finding for a future lane: `ka_kshetra`'s resumption logic should incorporate `bodha_pratijna`'s own `computed_at`/content into its fingerprint so a future upstream rescoring doesn't require a manual substep-progress clear. |

**R1 sweep-corpus re-check, run AFTER all writes (conductor's own direct query, independent of
the dispatched agent — its connection failed twice mid-report, so this was verified directly
rather than trusted from a partial transcript):** `SELECT chart_id, count(*) FROM
kala_gochara_windows GROUP BY chart_id` → `1c826d5a`=19323, `482012f1`=16297, `cb73cd3d`=2667 —
**EXACTLY UNCHANGED**, matching the pre-write baseline to the row. `kala_field_windows` for
`482012f1` (a genuinely new table `ka_kshetra` writes, distinct from the protected
`kala_gochara_windows`): 6 rows, `computed_at` fresh.

**Rung P8 scoped acceptance:**
- `bodha_pratijna` marriage/separation/childbirth for `482012f1`/`lahiri_chitrapaksha`: still 3
  rows, `max(computed_at)=2026-08-08 19:44:48 UTC` — unaffected by this phase (as expected, this
  phase didn't re-touch `bo_pratijna`), still matching RUNG_P3 (verified earlier in this session
  and unchanged since).
- **Honest limitation, disclosed not hidden**: `asset_throughput` was NOT updated by any of these
  5 writer invocations — the direct `ContextSpec`/`WriterBase.run(ctx)` pattern bypasses the full
  orchestrator's `execute_run`, and per §N.2 the orchestrator is the SOLE `asset_throughput`
  writer. "Zero error/stale, detector-cited" per the master plan's literal text cannot be claimed
  against that bookkeeping surface via this method — the real acceptance evidence here is the
  direct per-table query verification above (row counts, fresh timestamps, non-placeholder
  content, sweep-corpus integrity), not an `asset_throughput` state read. Flagged for whoever
  next runs a REAL orchestrated build for this chart: `asset_throughput` will still show these 5
  assets in their pre-this-phase state until a real `execute_run` touches them.

**VERDICT: Rung P8 GREEN for chart `482012f1`'s scoped asset set.** Two real findings surfaced and
closed (the `ka_kshetra` fingerprint gap; two agent-connection failures recovered by direct
conductor verification rather than lost work) — both disclosed above, neither hidden. **Charts
`1c826d5a` and `cb73cd3d` remain out of scope — next dispatch, only after this record stands.**

## Lane B5 chart-rebuild sub-phase — 1c826d5a full rebuild (Rung P8, chart 2 of 3)

**Scope decision:** unlike `482012f1` (which only needed the 5-consumer phase, since its
`bo_pratijna`/`mi_darshana` were already freshly rebuilt in the Rung P7 gap-closure session),
chart `1c826d5a` (Abhinandan Mohanty) had NEVER had its `bo_pratijna` writer run under v4 — its
135 `bodha_pratijna` rows were all `computed_at=2026-08-07 14:43:17 UTC`, `occurrence_grade`/
`condition_grade` NULL on every row (v3-era placeholder state), and `mimamsa_insight_units` was
even staler (`max(updated_at)=2026-07-28`). So this dispatch ran the FULL 7-asset sequence:
`bo_pratijna` → `mi_darshana` → `ka_yojaka` → `ka_avadhi` → `ka_taranga` → `ph_nimitta` →
`ka_kshetra`.

**Baseline confirmed live before any write** (re-verified independently, not trusted from the
dispatch prompt): `build_protected_assets` shows `ka_gochara_sweep` protected for both
`482012f1` and `1c826d5a`. `kala_gochara_windows` counts BEFORE: `1c826d5a`=19323,
`482012f1`=16297, `cb73cd3d`=2667 — exact match to the campaign's standing baseline.
`bodha_pratijna` for `1c826d5a`: 135 rows / `computed_at=2026-08-07 14:43:17 UTC` / all grades
NULL — confirmed live via direct query, matching the dispatch's stated starting state exactly.

**Toolchain note (new, not previously documented in this ledger):** the writer modules import
`psycopg` (v3), not `psycopg2` — `conn.execute(...)` and dict-style row access
(`row["planet_id"]`) both require a real `psycopg.connect(..., row_factory=psycopg.rows.dict_row)`
connection; a plain `psycopg2` connection fails with `AttributeError: 'connection' object has no
attribute 'execute'` on the first `SET LOCAL statement_timeout` call, and even a bare `psycopg`
(v3) connection without `row_factory=dict_row` fails inside `ChartReaderV4.reference_planets()`
with `TypeError: tuple indices must be integers or slices, not str`. Both failure modes were hit
and diagnosed live this session before finding the correct connection recipe (matching the
pattern already used by `run_ph_pratikara_prod.py`/`run_ka_sangam_prod.py` in this repo).

**Results, real live writes via the established `ContextSpec`/`WriterBase.run(ctx)` (or
`plan_substeps`+`run_substep` for the two HEAVY writers) + `conn.commit()` pattern, each
independently re-verified with a fresh, separate query, other-chart isolation confirmed for every
writer (`482012f1` untouched throughout):**

| Writer | Result | Independent verification |
|---|---|---|
| `bo_pratijna` | `rows_inserted=135` (`status_counts={'promised': 25, 'conditional': 105, 'denied': 5}`, `no_evidence=0`). | Fresh query: 135/135 rows, `computed_at=2026-08-09 08:01:53 UTC`, **zero NULL `occurrence_grade`** (was 135/135 NULL pre-write). `lahiri_chitrapaksha` marriage/separation/childbirth: `('marriage','promised',0.714,8.330)`, `('separation','promised',0.670,10.000)`, `('childbirth','conditional',0.321,7.500)` — different numbers from `482012f1`'s RUNG_P3 figures, exactly as expected (different chart, not a byte-match target). `derivation` JSONB spot-checked non-fabricated: real `denials`/`weights` structure with classical config_ids (`CFG-1`, `CFG-3`) and actual dignity terms (house_lord/karaka/divisional weights summing correctly), `engine_version='bo_pratijna_v4.0'`. |
| `mi_darshana` | `insight_units` substep: `rows_inserted=37`. `embeddings` substep: 0 rows, `[EXTERNAL_COMPUTATION_REQUIRED]` note (honest, matches B.10 — embeddings need an external model call, correctly not fabricated). `views_verify`: view counts reported, non-zero. | Fresh query: 37/37 rows (same total as the stale pre-write count — principled replace, not accretion), `updated_at=2026-08-09 08:04:46 UTC`. `verdict_marriage.statement = "Marriage: promised (grade 7.1/10). Strong evidence, corroborated across traditions."`, `verdict_separation = "Separation: promised (grade 6.7/10). Strong evidence, corroborated across traditions."`, `verdict_childbirth = "Childbirth: conditional (grade 3.2/10). Conditional — context-dependent."` — each sentence's grade is the exact `occurrence_grade × 10` from the `bo_pratijna` row just written above (0.714→7.1, 0.670→6.7, 0.321→3.2), confirming the consumer correctly reads the fresh upstream data rather than serving a stale or fabricated number. Other-chart isolation: `482012f1` still shows 113 rows / `updated_at=2026-08-08 21:43:22 UTC`, completely untouched. |
| `ka_yojaka` | `rows_inserted=50171`. | Fresh query on `kala_activation_predicates`: 50171 rows, `bound_at=2026-08-09 08:05:41 UTC`. `482012f1` isolation: still 50104 rows / `bound_at=2026-08-08 23:42:05 UTC`, unchanged. |
| `ka_avadhi` | `rows_inserted=1160` (`systems=7;md=125;ad=1035`). | Fresh query on `kala_avadhi`: 1160 rows, `computed_at=2026-08-09 08:07:01 UTC`. `482012f1` isolation: still 1169 rows / prior timestamp, unchanged (the small count difference from `482012f1`'s 1169 is expected — different chart's own dasha period structure, not an error). |
| `ka_taranga` | `rows_inserted=92412` (`domains=24;event_classes=27;months=1800`). | Fresh query on `kala_taranga`: 92412 rows, `computed_at=2026-08-09 08:07:37 UTC` — identical row count to `482012f1`'s 92412 because this writer samples a fixed grid (24 domains × 27 event classes × 1800 months), not chart-specific event counts; the count match is expected structural behavior, not evidence of a copy/no-op (timestamps and chart_id scoping both independently confirmed distinct). `482012f1` isolation: still 92412 rows / prior (2026-08-08 23:42:49 UTC) timestamp, unchanged. |
| `ph_nimitta` | `rows_inserted=24`. Required `birth_params.datetime_iso` in `ctx.config` (Abhinandan Mohanty's real birth data — `1985-03-02T09:40:00+05:30` — independently read from the live `charts` table, not assumed) to drive the age-band base_rate lookup; ran successfully once supplied. | Fresh query on `phala_anchors`: 24 rows, `computed_at=2026-08-09 08:08:54 UTC`. Relationship-domain anchor spot-checked: real, non-placeholder `magnitude_basis = "rarity_years=1.0yr × effective_score=1.200 = 0.120 → minor"` with populated `confidence_low`/`confidence_high` (0.272/0.372). The 24-row count vs. `482012f1`'s 92 is expected — this writer's row count is driven by chart-specific `kala_convergence`/`kala_bhavishya`/`bodha_discoveries` content, not a fixed grid. `482012f1` isolation: still 92 rows / prior timestamp, unchanged. |
| `ka_kshetra` | HEAVY writer, `plan_substeps`+`run_substep` loop (522 substeps). **No fingerprint-gap manual fix was needed this time** — a genuinely different outcome from `482012f1`: the writer's own `_fingerprint()` check found the existing 47 `build_substep_progress` rows (a stale 2026-08-06 10:55–10:57 UTC pre-v4 build) did NOT match the current fingerprint, so `plan_substeps` took the `completed is None` branch, called its own `_delete_prior_rows`, and planned a full fresh 522-substep build automatically — no manual `build_substep_progress` clear was required or performed. Total `rows_inserted=9379` across all substeps (7 of 27 event classes computed; the other 20 honestly skipped via the pre-existing LAW ZERO mechanism — `no_class_prior_row`, recorded in `kala_field_snapshots.skipped_classes`, same disclosed pattern as `482012f1`'s rebuild). | Fresh queries, all chart-scoped: `kala_field`=60 rows, `kala_field_windows`=6, `kala_insights`=7, `kala_timeline_spec`=6, all `computed_at=2026-08-09 08:10:31 UTC`. `build_substep_progress` for `(1c826d5a, ka_kshetra)`: 123 rows now (was 47 stale), all `completed_at=2026-08-09 08:10:31 UTC` — confirms a genuine fresh replan, not a partial resume. `482012f1` isolation: `kala_field` still 60 rows / prior (2026-08-08 23:47:54 UTC) timestamp, unchanged. |

**Step 4 — sweep-corpus re-check, run AFTER all 7 writes (independent query, fresh connection):**
`SELECT chart_id, count(*) FROM kala_gochara_windows GROUP BY chart_id` → `1c826d5a`=19323,
`482012f1`=16297, `cb73cd3d`=2667 — **EXACTLY UNCHANGED**, matching the pre-write baseline to the
row. None of the 7 writers touch `kala_gochara_windows` (consistent with the `482012f1` rebuild's
own R1 finding — `ka_kshetra`'s `stage4_field.py` only reads it read-only as a legacy cross-check
corpus).

**Step 5 — Rung P8 acceptance, chart `1c826d5a`:** all 7 assets independently confirmed to show
fresh, non-placeholder, real data via direct query (not `asset_throughput` — same honest
limitation as the `482012f1` rebuild: the direct `ContextSpec`/`WriterBase.run(ctx)` invocation
method bypasses the orchestrator's `execute_run`, and per §N.2 the orchestrator is the sole
`asset_throughput` writer, so that bookkeeping surface will still show these 7 assets in their
pre-this-phase state until a real orchestrated build touches this chart). Mahā-Brief-equivalent
surface spot-check: `platform-mcp/src/tools/register_p1_synthesis.ts`'s `synth_chart_brief_get`
(~line 776) issues `SELECT insight_id, insight_type, domain, question_lens, … FROM
mimamsa_insight_units` filtered/ranked by `chart_id`/`insight_type`, reading directly from the
table just rebuilt for `1c826d5a` — confirmed by code inspection against the live schema (the MCP
tool itself remains unreachable read-only from this environment, auth-gated, same limitation as
the `482012f1` rebuild's own Rung P7 finding); the data path is unambiguous — the next real
invocation for this chart serves the corrected 37-row set.

**VERDICT: Rung P8 GREEN for chart `1c826d5a`'s full 7-asset rebuild.** One notable finding,
disclosed: unlike `482012f1`, `ka_kshetra`'s resume-fingerprint check correctly detected the stale
pre-v4 substep-progress rows as non-matching and replanned fully on its own — no manual
`build_substep_progress` clear was needed for this chart. This is consistent with (not a
contradiction of) the `482012f1` finding: the fingerprint gap identified there is real (it does
not incorporate `bodha_pratijna` content), but whether it actually causes a silent no-op on any
given chart still depends on whether that chart's other fingerprint inputs (event-class ID set,
`corpus_pin`/`weights_version`/`config_pin`) happen to coincidentally still match a stale prior
build — for `1c826d5a` they did not, so the gap did not fire this time; the underlying fingerprint
defect itself remains open as a named follow-up for a future lane (unchanged from the `482012f1`
finding). **Chart `cb73cd3d` remains out of scope — next dispatch, only after this record stands.**

## DB access (verified pattern; never park on this)

```
DBURL=$(gcloud secrets versions access latest --secret=amjis-pipeline-db-url \
  | python3 -c "
import sys, urllib.parse as u
s=sys.stdin.read().strip(); p=u.urlsplit(s)
print(u.urlunsplit((p.scheme, f'{p.username}:{p.password}@127.0.0.1:5433', p.path, '', '')))
")
```
Never print credentials. ECONNREFUSED → restart proxy, continue:
```
nohup cloud-sql-proxy --address 127.0.0.1 --port 5433 \
  madhav-astrology:asia-south1:amjis-postgres &
```

## State at open (verified)

ADHIṢṬHĀNA merged to main: `chart_fact_identity` live (375,856 rows, 100% coverage, 3 charts) ·
graha/domain/event-class SSoTs adopted (removal-census enforced) · `brahma_ontology` complete
(varga class, storage-code synonyms) · probes P1/P2 green and committed under
`platform/scripts/probes/`. The old `bo_pratijna` v3 rows in production are STALE (broken-matcher
content) — known, this campaign replaces them.

**Note on stale worktrees:** `git worktree list` at session open shows several worktrees left over
from the ADHIṢṬHĀNA campaign (branches already merged to `main`, e.g. `lane/a2-graha-ssot`,
`adhisthana/lane-a6-gates`, etc.). Not cleaned up by this session — out of scope for PRATIJÑĀ v4
unless they collide with a lane branch name. Flagged for hygiene, not blocking.
