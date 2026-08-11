---
artifact: MASTER_REMEDIATION_REGISTER_v2_0.md
campaign: GOCHARA-UTKARSHA post-close remediation
version: 2.0
status: LIVING — the single register of record; supersedes POST_CLOSE_GAP_REGISTER_v1_0.md
  (v1.1 retained in place as audit trail; PG→MR mapping in §7)
created: 2026-08-10 ~19:2x IST, native's desk (Fable 5), native-directed
sources_consolidated:
  - Post-close audit report (desk, live-DB verified): PG-1..16
  - Plan-vs-ledger AC reconciliation (sections A–F): wave-by-wave, 27-class,
    residuals, W6.5 close, authorizations A1–A4/UTK-R1..R3, §N.8 violations
  - Consumer/wiring census (sections 0–7 + top risks 1–5): PG-27..33 + minor items
  - Net-new desk findings not in any prior report (MR-35, MR-36)
closure_rule: >
  An item closes ONLY on live re-verification of its stated GATE, output pasted.
  Where full at-par closure requires a native ruling, the item says so and cannot
  be closed by any agent alone. Honest-deferred (with recorded trigger) is a valid
  terminal state ONLY where marked.
dedup_note: >
  All duplicates across the three sources are merged; §7 maps every source
  finding to exactly one MR item. No source finding is dropped.
---

# MASTER REMEDIATION REGISTER — GOCHARA-UTKARṢA

36 items, 6 groups. Each item: GAP → REMEDIATION → CLOSURE GATE (the detector
that could say otherwise) → AT-PAR CHECK (why closing it restores or exceeds
the promised output quality).

## GROUP A — SERVING RESTORATION (product is down)

**MR-01 · Schema parity → un-break the three tools.** [PG-1; census risk#1]
GAP: all 3 gochara MCP tools 500 (`term_breakdown` selected from prod, exists
only on staging). REMEDIATION: migration adds ALL 8 staging-only columns to
`kala_gochara_windows` (nullable, additive): term_breakdown, lambda_v3_ci_low/
high, ci_source, threshold_lambda, threshold_percentile, implied_density,
base_rate_cited; §N.4 self-verification block; correct the false code comment
(:303) in the same PR. GATE: `_migrations_applied` row + information_schema
shows 8 columns + live calls to all 3 tools × 3 charts return ok. AT-PAR:
serving restored AND prod schema can carry the full v3 output model (needed by
MR-10/13/14) — above the minimum one-column fix on purpose.

**MR-02 · Coverage gate: authority-aware, never fails closed on retirement.**
[PG-27; census risk#2] GAP: `computeGocharaCoverage` hardcodes
`asset_id='ka_gochara_sweep'`; post-retirement it refuses every domain-
filtered call. REMEDIATION: coverage source selected per chart VIA the
authority seam — v1-authority charts (incl. cb73cd3d) keep reading sweep
substep history; '3.0'-authority charts read the v3 asset's substeps ∪
resonance-map classes. GATE: domain-filtered calls succeed on all 3 charts
with correct per-chart coverage, BEFORE and AFTER retirement executes.
AT-PAR: yes — coverage honesty (S4-05) preserved across generations.

**MR-03 · Truthful citation for gen-3.0 rows.** [PG-29b; census risk#4b]
GAP: `buildSourceCitation` recognizes only `g3_*`; served '3.0' rows would be
cited as "ka_gochara_sweep … generation=v1" — false provenance on output.
REMEDIATION: add the '3.0' branch citing the v3 materializer + engine,
generation=3.0. GATE: unit test + one live served row shows the v3 citation.
AT-PAR: yes — provenance truth restored.

**MR-04 · Valence vocabulary contract.** [PG-4 serving half]
GAP: corpus emits `favourable`, serving enum is gain|loss|neutral|mixed —
filters permanently unmatchable. REMEDIATION: ONE canonical vocabulary — the
serving enum is the contract; writer emits it (MR-13 restamps existing rows).
Schema CHECK or writer-side named-constant vocab per §N.4. GATE: valence
facet queries return rows; zero rows outside the enum. AT-PAR: yes.

## GROUP B — DEPRECATION MADE REAL AND DURABLE

**MR-05 · Execute the deprecation (corrected migration).** [PG-2; recon D#1]
GAP: 563 merged but unappliable (FK 23503: asset_throughput row references
the self-test id); deploy failed; registry unchanged (sweep CURRENT, ka_gochara
DRAFT, v2_materialize live). REMEDIATION: new migration — clean FK referrers
(asset_throughput self-test row; check asset_coefficients), then DELETE
self-test / RENAME v2_materialize→ka_gochara / RETIRE sweep; self-verifying;
deploy green. SEQUENCE: strictly AFTER MR-02. GATE: `_migrations_applied` row;
live registry: sweep=RETIRED+inactive, ka_gochara=CURRENT materializer,
v2_materialize absent; deploy run green. AT-PAR: the native's directive
("sweep completely deprecated, new version fully wired") becomes true.

**MR-06 · Make the cutover irreversible-by-accident.** [PG-28; census risk#3]
GAP: `asset_registry_seed.ts` + migration 542's ON-CONFLICT upserts would
un-retire the sweep, resurrect v2_materialize, and overwrite ka_gochara's
identity on any seed run. REMEDIATION: seed updated to post-cutover truth;
542 re-seed guarded; CI test runs migrations+seed in shadow DB and asserts
the post-cutover state survives. GATE: the CI guard exists and fails when the
old seed is restored (mutation-tested, W0.1 standard). AT-PAR: yes —
durability, which the campaign never had.

**MR-07 · Cockpit truth for the production corpus.** [PG-21, PG-29a; recon
W5.2; census risk#4a] GAP: no asset counts prod '3.0' rows; renamed asset
counts staging; sweep count generation-blind (will double-count). REMEDIATION:
ka_gochara: target_table=kala_gochara_windows, count_sql scoped
generation='3.0'; sweep count_sql scoped generation='v1'; staging kept as
explicit workbench row or dropped. GATE: cockpit stats route returns 174 (post
MR-10) for ka_gochara on the native chart and the true v1 count for the sweep.
AT-PAR: §N.4 cockpit-truth restored.

**MR-08 · Versioned flip/rollback/probe tooling.** [PG-30; census risk#4c]
GAP: no committed writer/script/API for `kala_gochara_authority`; both real
flips were ad-hoc; rollback tooling uncommitted. REMEDIATION: commit
generalized flip(chart,gen)/rollback(chart)/probe(chart) scripts (from the
w61 originals, MR-31) — probe MUST call the deployed product (MR-24 lesson);
preflight checks included. GATE: rollback+re-flip exercised once via the
committed tooling with pasted product-level probe output. AT-PAR: the
cutover mechanism becomes an operable, reversible product surface.

**MR-09 · Naming coherence + service health + honest pointers.** [PG-33;
census §3/§4] GAP: asset id `ka_gochara` (materializer) vs Python
`KaGocharaService` (live transit compute) collide; transit service_health
self-test deleted with no replacement; retired sweep writer still
@register-discoverable; ph_muhurta docstring claims wiring that doesn't
exist; 2026-06-26 ruling ("do NOT add writers/ka_gochara.py …") contradicted
un-adjudicated. REMEDIATION: adjudicated naming disposition (rename the
Python symbol or document the split in both modules); restore a transit-
service health check; gate writer discoverability on catalog_status; correct
ph_muhurta docstring (wiring itself = logged enhancement, not this closure);
record the superseding ruling (with MR-28). GATE: grep shows no ambiguous
references; health check live; discoverability test. AT-PAR: yes at
integrity level.

## GROUP C — CORPUS REPAIR (the data must deserve the authority flip)

**MR-10 · Promote the 54 stranded directional point rows.** [PG-3]
REMEDIATION: production write path extended to carry point rows (needs MR-01
columns) via the writer, idempotent §N.3; rebuild/promote both charts. GATE:
prod shape profile = staging's (point+interval); spot-check valences
loss/neutral/gain present. AT-PAR: the elevation's dated, directional
claims — its core value — become servable.

**MR-11 · Temporal resolution worthy of "windows" (incl. hierarchy).**
[PG-9, PG-20b; recon W3.3] GAP: prod timing = uniform decade buckets + one
peak each; v1 was day-precision; hierarchy (era⊃month⊃day) code merged,
zero rows. REMEDIATION: (a) MR-10 restores dated points; (b) produce
hierarchy windows at month/day resolution for at least LEL-represented
classes, parent_window_id wired, resolution facet served; (c) ⚠ NATIVE
RULING REQUIRED: ratify the serving resolution bar (what granularity
constitutes an at-par "window"). GATE: sub-decade windows served for both
charts + the recorded ruling. AT-PAR: only with (c) — an agent cannot
self-certify this; that is by design.

**MR-12 · Produce chain rows (marriage first).** [PG-20a; recon W3.2]
GAP: "first-ever marriage chain rows" is a stated success criterion; corpus
has zero chains. REMEDIATION: run the chain producer for chain-canonical
classes, both charts. GATE: chain rows with milestone_id +
is_irreversibility_milestone served live. AT-PAR: yes.

**MR-13 · Honest valence + honest calibration tier on every row.** [PG-4,
PG-5; recon F#1] GAP: all rows 'favourable' (incl. illness/surgery) +
'empirically_calibrated' stamped by direct SQL against an all-zero fit.
REMEDIATION: restamp via the §N.8-GATED writer path that already exists:
calibration_state='structural_prior' until a real fit; valence derived per
class/direction or NULL — never a default. GATE: zero 'favourable' rows;
zero 'empirically_calibrated' rows until MR-14's fit; density facets
truthful. AT-PAR: §N.7/§N.8 honesty restored on served output.
CORRECTION (2026-08-11, PARIṢKĀRA builder + native ruling): this entry's
"§N.8-gated writer path" pointed at `ka_gochara.py` — that writer never
touches `kala_gochara_windows`. The real writer is
`platform/python-sidecar/pipeline/orchestrator/writers/
ka_gochara_v3_century_materialize.py` (`GocharaV3CenturyMaterializeWriter.
_build_row()`). Confirmed live: that writer's `calibration_state` was
ALREADY correctly coded `'structural_prior'` — only `valence` was
hardcoded `'favourable'` for every event_class there. The live
`'empirically_calibrated'` stamp on all 120 gen-3.0 rows (both charts) came
from an out-of-band raw SQL UPDATE, not from any writer in this repo — a
narrower root cause than this entry's "stamped ... against an all-zero fit"
framing implied. Code fix merged (PR #1211); the GATE above does not close
on the code merge alone — closes only when a native-authorized, single-use,
session-scoped writer-path rebuild (folded into MR-14/15/10, PARISHKARA_LEDGER
2026-08-11 ~05:2x IST entry) actually restamps the live rows and the honest
result is verified against both charts.

**MR-14 · Make empirical calibration possible, then earn the tier.** [PG-6,
PG-7; recon W1.5/W4.4] GAP: term_breakdown never produced anywhere (root
cause of all-0.0 weights); Abhinandan 0-row detection bug. REMEDIATION:
engine populates IntensityResult.term_breakdown → writer → staging+prod;
rebuild corpus; re-run W4.4 fit (0-row bug fixed); only a non-degenerate fit
restores 'empirically_calibrated' via the gated path. GATE: corpus
term_breakdown non-NULL; fit output published — real weights OR an honest
recorded insufficient-data conclusion (both are valid closures). AT-PAR:
DR-14 ("weights LEARNED, never assumed") becomes dischargeable.
AMENDMENT (2026-08-11, PARIṢKĀRA builder + native ruling — PARISHKARA_LEDGER
2026-08-11 ~06:3x IST entry): a THIRD wiring gap found, in scope, not a new
item. (1) term_breakdown-never-produced: the engine (services/gochara_v3/
engine.py) was NEVER broken here — it always computed the full decomposition
correctly; the actual break was two silent downstream drops (interval_solver
reading only a bare raw_lambda float; the writer never naming the 4 columns
in its INSERT templates) — fixed, PR #1213. (2) Abhinandan 0-row: NOT a bug
— confirmed live, genuine LEL-intake gap (0 life_events rows for that
chart), already correctly handled by the existing degrade path; one
unrelated dead variable removed as disclosed cleanup. (3) THE THIRD GAP
(why this GATE is still open): even with term_breakdown populated end to
end, `_determine_ablation_method`'s literal key-matching against the 10
admitted mechanism toggle_keys (w21_av_gating etc.) does not match the real
decomposition shape ({promise, permission, activity, quality_gates,
lambda_v3, activity_terms, formula}) — every fit silently falls back to
proxy_fraction regardless of how populated the corpus is. Native ruling:
this IS MR-14 scope ("make empirical calibration possible" is not satisfied
by a fit that structurally cannot match any mechanism) — fix it before the
rebuild, not after; a post-hoc restamp would mean a second override window
on the protected corpus, already ruled out. GATE AMENDED: closure requires
an END-TO-END golden test — a small synthetic corpus with KNOWN
decompositions fed through the REAL fit path (not each link mocked in
isolation, which is exactly how gaps (1)/(2)/(3) each shipped and sat
undetected) — asserting expected non-zero per-mechanism weights actually
come out. Both terminal outcomes of the LATER authorized rebuild still
close this gate honestly: real weights from real signal → empirically_
calibrated legitimately; genuinely insufficient signal from a small
(174-row) corpus even with matching fixed → structural_prior, now actually
honest rather than a predetermined null wearing an honest label.

**MR-15 · AV gating actually contributes.** [PG-22; recon L266]
GAP: flagship mechanism silently degraded during the only production build
('column bhava_num does not exist', swallowed at INFO). REMEDIATION: fix the
column/schema mismatch; make the failure loud (surfaced in build report at
minimum); rebuild (with MR-14); with-vs-without delta proves contribution
(with MR-19). GATE: rebuild log shows av_gate_rows loaded; ablation delta
non-null. AT-PAR: yes.

**MR-16 · Deliver the promised 27-class scope (or a recorded ruling).**
[PG-17; recon B] GAP: materializer hardcodes 6 classes; 27-class resonance
map never rebuilt; production scope identical to v1's. REMEDIATION: rebuild
ka_gochara_resonance at 27 classes both charts (code exists, 92/92); make
materializer consume resonance-mapped classes dynamically with per-class
quality notes (thin maps stay honest); rebuild corpus. ⚠ Scope reduction is
ONLY closable by an explicit native ruling — silence is not a ruling. GATE:
prod corpus classes = resonance-mapped classes (27, or ruling-recorded
subset), per-class quality notes served. AT-PAR: this is the difference
between "elevated" and "same scope, new engine."

## GROUP D — SEAM INTEGRITY ACROSS ALL CONSUMERS

**MR-17 · ka_kshetra cross-check seam-awareness (BLOCKS P-G1; SAMPŪRTI
territory).** [PG-31; census risk#5] GAP: `load_legacy_crosscheck` reads
windows with no generation predicate/authority join → with v1+3.0 coexisting,
duplicate self-referential provenance edges in kala_field_windows.
REMEDIATION: authority-seam COALESCE read + unit test asserting single-
generation rows; posted to CAMPAIGN_COORDINATION as SAMPŪRTI's pre-P-G1
lane. GATE: test green + one P-G1 window row shows exactly one xref edge per
legacy window. AT-PAR: P-G1's agree/diverge adjudication means something.

**MR-18 · Offline validators + scripts: explicit generation stance.** [census
§7, V1–V8] GAP: v6_divergence_pilot, s4_05 retest, cr131 test read mixed
generations; w2g_equivalence_report + w41 λ_v1 loader HARDCODE v1 (the
equivalence report would "justify" the flip against v1 forever);
test_migration_527's single-source assertion breaks on v3 rows; sweep
count_sql generation-blind (fixed in MR-07). REMEDIATION: every reader
declares its stance — seam-aware, or pinned-with-documented-purpose
(comparators legitimately pin v1; document it); update the fragile test.
GATE: re-run of the census grep shows zero undocumented generation-blind
reads. AT-PAR: yes — no consumer can silently measure the wrong corpus.

## GROUP E — EVIDENCE DEBT (unearned PASSes get earned or honestly failed)

**MR-19 · Run the ablations; re-adjudicate admissions.** [PG-19; recon F#4]
GAP: 10 mechanisms admitted with zero ablation runs (I2 hard precondition),
judged "cannot degrade v1 parity" against an empty corpus. REMEDIATION:
with-vs-without runs per mechanism on the repaired corpus (post MR-14/15);
ADJUDICATOR re-issues admissions on evidence; zero-effect mechanisms demoted
honestly. GATE: published ablation table; re-issued rulings in ledger.
AT-PAR: admissions mean what I2 says they mean.

**MR-20 · Run the real no-loss coverage gate.** [PG-18; recon F#2]
GAP: W6.2 AC1 passed on class-name counting; the actual gate — all 35,620 v1
windows matched/superseded/classified via the closed vocabulary, zero
unclassified — never ran. REMEDIATION: implement + run the equivalence
protocol; publish counts per classification label. GATE: published table,
unclassified=0. AT-PAR: this IS the proof the replacement loses nothing —
the at-par certificate itself.

**MR-21 · Publish the quantitative evidence chain.** [PG-23; recon F#6,7,9 +
W6.1] GAP: every required number absent — W0.4 ≥50× speedup + 200-candidate
bit-parity; W3.4 century wall-clock + delta-rerun proof; W4.2 noise floor
(+CIs); W6.1 native wall-clock + interrupt disposition. REMEDIATION: run and
publish each; ADJUDICATOR disposes the SLO result. GATE: numbers pasted in
this register's close-out. AT-PAR: every comparative claim gains its anchor.

**MR-22 · Suppression: detector + real-corpus count.** [PG-10; recon F#8]
GAP: suppression_state empty on all rows; founding v1 pathology (0 firings /
35,620) unmeasured post-fix. REMEDIATION: seeded must-fire test (dead-vs-
honest-zero detector) + published real-corpus firing count; if 0, an
ADJUDICATOR disposition on plausibility. GATE: test green + count published.
AT-PAR: the headline defect is measurably fixed or honestly explained.

**MR-23 · Remaining unrun acceptance artifacts.** [PG-26; recon W1.2/W1.4/
W5.4/W0.2] GAP: W1.2 adverse-window-vs-v1 golden comparison never recorded;
W1.4 tolerance band never ratified + thresholds shipped inert
(lambda_thresh=0.0); W5.4 mutation test asserted not run; W0.2 honest-zero
reason never given. REMEDIATION: run the golden comparison; ratify the band
+ set/justify thresholds; actually perform the W5.4 mutation (predicate
removed → guard fails → restore); record the W0.2 reason. GATE: each output
pasted. AT-PAR: yes.

**MR-24 · The REAL product-level E2E battery (standing).** [PG-11; recon D#2–4;
the native's "confirmed with successful testing"] GAP: the only "probe" was a
direct DB query; cockpit/judgment/kala close checks never ran. REMEDIATION:
committed, versioned probe suite that calls the DEPLOYED product: 3 tools ×
3 charts (incl. v1-authority cb73cd3d) × authority states; facet filters;
cockpit counts via stats route; one judgment/kala query serving gochara
depth; rollback+re-flip via MR-08 tooling. Policy line added: a probe that
does not exercise the deployed product is not an E2E probe. GATE: full
battery output pasted; suite re-runnable. AT-PAR: integration "flawless,
confirmed by successful testing" gains its operational definition.

**MR-25 · Citations resolve to verses in serving.** [recon W2.9]
GAP: three citation sources "cataloged", never resolved to
classical_text_chunks verse_refs nor joined in serving. REMEDIATION: seed
the resolution table (mig-528 verified-before-seeded pattern); serving join;
test: a served window's active_sentences resolve. GATE: live row shows
verse_refs. AT-PAR: B.3 derivation-ledger discipline reaches gochara output.

## GROUP F — GOVERNANCE + RECORD REPAIR

**MR-26 · Write the close report (as amended, honest).** [PG-12; recon D#6]
GAP: "Close report committed" is a false claim; file absent. REMEDIATION:
write it NOW as an amended close: true wave outcomes + this register's
existence; commit to this directory; update CURRENT_STATE. GATE: file
exists, cross-linked. AT-PAR: record integrity (honest record, not
backdated fiction).

**MR-27 · Prod-sync + deploy discipline.** [PG-16; recon D#1/D#9]
GAP: close claimed "prod-sync verified, migrations applied" 38 min after its
deploy FAILED; migrations 557–563 never verified; PROD_DATABASE_URL error
path in deploy.yml; rail checks ran 2/7. REMEDIATION: run + record full
prod-sync now (deployed==main, tracker complete); root-cause + fix the
secret error path; run the missed I6(b) rail checks + close-time GUC grep;
standing rule: campaign close gates on deploy conclusion green. GATE:
pasted prod-sync record; deploy.yml fixed + one green run. AT-PAR: yes.

**MR-28 · Issue the skipped adjudications.** [PG-24; recon E]
GAP: no ruling for W1.4 band, W6.1 SLO/interrupt, W6.2 overall gate (verdict
"CONDITIONAL_PASS" outside the plan's PASS/FAIL vocabulary), W6.4 divergence
dispositions, and the contradicted 2026-06-26 ruling. REMEDIATION: issue all
five via the delegated adjudicator (or native), recorded in ledger §Rulings.
GATE: five rulings present. AT-PAR: the delegation model's integrity.

**MR-29 · Ledger reconciliation + a real close verdict.** [PG-25; recon F#12–13
+ internal inconsistencies] GAP: W6.5 has NO VERIFIER verdict (by the
campaign's own rule the close lane is not done); lane table 6 lanes stale;
"No wave deployments yet" in a sealed ledger; scrambled chronology; conductor
self-verified 4 Wave-1 lanes after the VERIFIER died. REMEDIATION:
append-only reconciliation entry correcting state; AFTER remediation, a
fresh independent VERIFIER verdict over the re-close; process rule:
verifier death → new verifier, never conductor self-verification. GATE:
reconciliation entry + the verdict. AT-PAR: the seal becomes trustworthy.

**MR-30 · Evidence + worktree hygiene.** [PG-13, PG-14; recon W6.4 residuals]
GAP: 3 W6.3 operational scripts uncommitted (utk-w61); unpushed duplicate
(utk-w43); ~16 stale builder worktrees; stale v2_materialize docstrings +
runner filename. REMEDIATION: commit scripts (feeds MR-08); reconcile w43;
salvage-check then remove worktrees; docstring/filename sweep. GATE: clean
worktree list; scripts in git. AT-PAR: yes.

**MR-31 · SAMPŪRTI branch-skew merge.** [PG-32; census §0]
GAP: sampurti/integration one cutover behind main; delete/modify conflict
pending on services/ka_gochara/writer.py; its run-script currently imports
the self-test shim as the materializer. REMEDIATION: deliberate main→
integration merge by SAMPŪRTI's conductor with the conflict resolved to
main's state (posted to coordination file). GATE: merge commit; import
resolves to the real materializer. AT-PAR: yes.

**MR-32 · DR-13 shape alignment → Stage C seeding.** [PG-15a; recon C#1]
GAP: prospective-ledger auto-seeding deferred (4/6 classes point-canonical
vs interval-only corpus). REMEDIATION: MR-10's point rows resolve the shape
mismatch for the point-canonical classes → run Stage C seeding; verify rows.
GATE: brahma_prospective_ledger rows exist citing v3 windows. AT-PAR:
§5.3's "prospective ledger auto-seeded" delivered.

**MR-33 · CRPS empirical accuracy — HONEST-DEFERRED (terminal state
permitted).** [PG-15b; recon C#2] GAP: W6.2 AC3 deferred — no outcome-linked
events exist yet. REMEDIATION: verify the L5 loop wiring end-to-end
(prediction filed → outcome recordable → CRPS computable); record the
trigger condition (N outcome-linked events) in this register. CLOSURE: this
item may close as HONEST-DEFERRED with the trigger recorded — fake-closing
it would repeat the campaign's central defect. AT-PAR: by-design deferral,
same doctrine as L5 STRUCTURAL mode.

**MR-34 · Third-chart consistency statement.** [net-new]
GAP: cb73cd3d (2,667 v1 rows, 3 resonance classes, no authority row) sits
silently on v1 with no recorded scope decision. REMEDIATION: record the
scope statement (v1-authority intentional until native chooses otherwise);
MR-02/MR-24 must keep it serving correctly. GATE: statement recorded;
battery includes it. AT-PAR: no chart is on an undocumented engine.

**MR-35 · Serving outage detection (net-new — nothing caught a 3-hour
total outage).** [desk finding] GAP: all three tools were hard-down from
~15:47 IST and nothing alerted; discovery was manual. REMEDIATION: scheduled
smoke probe (samiksha-daily pattern) hitting the three gochara tools + key
kala/judgment surfaces against the DEPLOYED product, failing loudly on
error envelopes. GATE: probe exists in CI, red on a seeded failure,
green live. AT-PAR: ABOVE par — this class of outage becomes
minutes-to-detection, permanently.

**MR-36 · W0.4 load-bearing lane evidence.** [recon F#6]
GAP: the lane the whole SLO rests on recorded the word "PASS" and nothing
else — no timed run, no 200-candidate bit-parity result. REMEDIATION +
GATE: covered by MR-21's runs; listed separately so the register's PG→MR
map drops nothing. Merged-into: MR-21.

**MR-37 · w45's §N.8 calibration-stamping gate is unsound (row-existence,
not earned-signal).** [net-new, found 2026-08-11 during THE authorized
gen-3.0 rebuild, PARISHKARA_LEDGER 2026-08-11 ~14:3x IST entry, "Finding B"]
GAP: `w45_post_fit_rebuild.py`'s gate to stamp `calibration_state=
'empirically_calibrated'` is `if not fit_run_ids: return 0` — it checks
that a calibration ROW EXISTS, not that a REAL (non-zero, wired-mechanism)
WEIGHT WAS EARNED. `w44_weight_fitting.py` writes a row for every
toggle_key regardless of method, so the gate PASSES even on an all-zero,
`mechanism_not_wired` fit (confirmed live: the real W4.4 refit for both
canonical charts produced `mechanism_not_wired` for all 10 admitted
mechanisms — MR-14-matching's finding, since none of the Wave-2 mechanisms
are actually wired into the engine — and w45's gate would still have
stamped 120 rows `empirically_calibrated` had it been allowed to commit).
**NOT HYPOTHETICAL:** `kala_gochara_windows_v2` (staging) was ALREADY
sitting at 107 `empirically_calibrated` rows BEFORE the 2026-08-11 rebuild
— this exact gate has already fired for real, at least once, dishonestly.
REMEDIATION: the gate must test earned signal (a genuinely non-zero weight
from an engine-wired mechanism, not merely "a fit_run_id row exists") —
likely gating on `MECHANISM_ENGINE_WIRED` (added this session, w44) AND a
non-zero fitted weight, not on row presence. Separately: disposition the
107 pre-existing dishonestly-stamped staging rows (staging is unprotected,
so a fix is mechanically simple once ruled — NATIVE RULING REQUIRED on
disposition, per this campaign's standing rule that live-data corrections
are never self-authorized). GATE: w45 re-run against a synthetic
mechanism_not_wired-only fit correctly declines to stamp anything; the 107
pre-existing staging rows are honestly restamped per native ruling. AT-PAR:
closes the same §N.8 defect class as MR-13, one layer downstream (the
writer was fixed; the POST-FIT stamper that runs after it was not).

**DISPOSITION (native-ruled 2026-08-11, executed same day, PARISHKARA_LEDGER
"MR-37 disposition" entry — CLOSED, PR pending merge):**
(a) `load_fitted_weights()` now returns `earned_fit_run_ids` — toggle_keys
with a non-zero weight AND `MECHANISM_ENGINE_WIRED=True`; the stamping gate
consumes this, not raw row-existence. `TestEarnedSignalGate` (7 tests)
reproduces the exact exploit end-to-end via `build_post_fit_report` and
asserts it is refused. 167/167 kala_admission tests pass. PR #1217
(`parishkara/mr-37-w45-earned-signal-gate` → `parishkara/integration`).
(b) Live pre-check found the 107 rows NO LONGER dishonest — already
overwritten to `structural_prior` as a side effect of THE ONE authorized
rebuild's delete-then-insert on the same staging table (verified via
`computed_at` matching the rebuild window). Committed, dry-run-capable
`restamp_dishonest_staging_calibration.py` still written and run for real
per native instruction: 0 rows affected, confirmed clean. No GUC override
used (staging is unprotected).
(c) Standing rule recorded (ledger): nothing consumes staging
`calibration_state` as trustworthy until PR #1217 is merged AND
`restamp_dishonest_staging_calibration.py --dry-run` confirms 0 dishonest
rows. Does not apply to the protected production surface
(`kala_gochara_windows`), independently verified honest throughout.
Non-blocking for the W6-COMPLETE marker (posted before this disposition;
neither (a) nor (b) touches the gen-3.0 authority seam or any marker-gate
item).

**MR-38 · ENGINE_VERSION not bumped by MR-13/14 — future rebuilds silently
no-op.** [net-new, found 2026-08-11 during THE authorized gen-3.0 rebuild
throwaway-DB rehearsal, PARISHKARA_LEDGER 2026-08-11 ~14:3x IST entry,
"Finding A"] GAP: MR-13/14 changed the row shape the writer produces
(honest per-class valence, populated `term_breakdown`, new CI fields)
without bumping `ka_gochara_v3_century_materialize.py`'s `ENGINE_VERSION`
(still `"v3.0"`). The writer's delta-skip logic fires when
`stored_fingerprint == recomputed_fingerprint AND rows_exist` —
recomputing fingerprints against live resonance targets showed a MATCH for
120/120 substeps (both canonical charts), meaning the authorized rebuild
would have reported success and written NOTHING had this not been caught
in rehearsal first. RESOLVED for the one authorized run (delete the
writer's own `kala_gochara_v2_build_state` cache row inside each
substep's own transaction, atomic with the row write — build state, not
protected corpus, so this needed no override). NOT fixed durably.
REMEDIATION: bump `ENGINE_VERSION` (or fold row-shape/writer-version into
the fingerprint computation itself) so a fingerprint match can only ever
mean "the inputs AND the writer's output contract are both unchanged" —
right now it only guarantees the former. GATE: a synthetic writer-version
bump forces cache invalidation and a real rewrite; re-running with no
version change and no input change correctly skips. AT-PAR: prevents this
exact silent-no-op class recurring on the NEXT engine/writer change to
this asset.

**STANDING RULE (native-directed 2026-08-11, recorded here per MR-38 and
generalized beyond it):** any writer edit that changes the SHAPE of its
output — a new column populated, a changed value-computation, a new row
category, anything that alters what a fingerprint-matched re-run would
otherwise silently skip — MUST bump that writer's version constant (e.g.
`ENGINE_VERSION`) in the SAME PR as the behavioral change. This is not
scoped to `ka_gochara_v3_century_materialize.py` or to this campaign: it is
a standing rule for every FROZEN-orchestrator writer with delta-skip/
fingerprint-based idempotency (§N.3). A code reviewer (human or PARĪKṢAKA)
checking a writer PR should treat "output shape changed, version constant
unchanged" as a blocking finding, the same class as a missing test. This
generalizes MR-38's specific catch (MR-13/14 changed row shape without
bumping `ENGINE_VERSION`, caught only by rehearsal luck before it could
silently no-op the authorized rebuild) into a rule that does not depend on
rehearsal luck recurring next time.

**MR-39 · `idle_in_transaction_session_timeout=10min` vs long-running
writer substeps — connection death misreported as environment flakiness.**
[net-new, found 2026-08-11 during THE authorized gen-3.0 rebuild,
PARISHKARA_LEDGER 2026-08-11 ~14:3x IST entry] GAP: the writer computes
for minutes with no DB traffic while its transaction sits open (and the
FROZEN orchestrator drives substeps as savepoints inside a transaction
too); any substep whose compute exceeds the server's 10-minute
`idle_in_transaction_session_timeout` gets killed and surfaces as
"server closed the connection unexpectedly" / connection-lost — logged
and treated as environment flakiness (three independent builder sessions
this campaign hit variants of this and initially read it as a sandbox
networking issue) rather than diagnosed as a timeout misconfiguration.
REMEDIATION: either raise the timeout for the orchestrator's own DB role/
session, or make long-compute substeps periodically touch the connection
(a lightweight keepalive query) during pure-compute stretches, or both.
GATE: a synthetic substep with a >10-minute no-traffic compute window
completes without a connection-lost error. AT-PAR: closes a real
orchestrator-wide operational fragility, not specific to gochara.

**MR-40 · `ka_gochara` cockpit `count_sql` orphaned by the W5.4 UTK-R1
authority repoint — cockpit read 0 for both gen-3.0 charts.**
[net-new, found 2026-08-11 during MR-24's final battery re-run against the
rebuilt corpus, PARISHKARA_LEDGER 2026-08-11 "MR-24 FINAL RE-RUN" entry]
GAP: `asset_registry_seed.ts`'s `ka_gochara` entry (`count_sql`/
`target_table`) counted `kala_gochara_windows_v2 WHERE generation='3.0'` —
a table×generation combination the writer's own W5.4 UTK-R1 ADJUDICATOR
repoint moved off of (production authority is `kala_gochara_windows`
generation='3.0'; `kala_gochara_windows_v2` generation='g3_utkarsha' is
calibration/staging only, confirmed live: it holds only '2.0' and
'g3_utkarsha' rows, never '3.0'). The MR-06 cockpit fix (PR #1202) was
itself correct for its own moment but was silently orphaned by this later,
unrelated repoint — a third instance of the "verified correct, never
re-checked against a later change" defect family this campaign has now
found (alongside the migration-563 FK bug and the asset_registry_seed
manual-invocation gap). REMEDIATION: (1) source fixed —
`asset_registry_seed.ts`'s `ka_gochara` entry repointed to
`kala_gochara_windows` generation='3.0', PR #1216
(`parishkara/mr-40-cockpit-gochara-authority` → `parishkara/integration`,
open, not yet merged); (2) live DB narrow-patched to match, verified
89 (482012f1) / 85 (1c826d5a) — TRUE, matching production-served data.
GATE: cockpit count for `ka_gochara` on a gen-3.0 chart matches a direct
`kala_gochara_windows WHERE generation='3.0'` count. AT-PAR: closed live;
PR merge to `parishkara/integration` still pending (non-blocking — not a
marker-gate item, live state already correct and evidenced). See MR-38's
ENGINE_VERSION standing rule for the related open question of whether an
authority-surface repoint (not just an engine/writer code change) should
also force a re-check of every cockpit entry referencing the old surface.

## §7 — SOURCE → MR MAP (dedup audit)

PG-1→MR-01 · PG-2→MR-05 · PG-3→MR-10 · PG-4→MR-04+13 · PG-5→MR-13 ·
PG-6→MR-14 · PG-7→MR-01+14 · PG-8→MR-06(protection: see note) · PG-9→MR-11 ·
PG-10→MR-22 · PG-11→MR-24 · PG-12→MR-26 · PG-13→MR-30 · PG-14→MR-01+29 ·
PG-15→MR-32+33 · PG-16→MR-27 · PG-17→MR-16 · PG-18→MR-20 · PG-19→MR-19 ·
PG-20→MR-12+11 · PG-21→MR-07 · PG-22→MR-15 · PG-23→MR-21 · PG-24→MR-28 ·
PG-25→MR-27+29 · PG-26→MR-23+25 · PG-27→MR-02 · PG-28→MR-06 · PG-29→MR-03+07 ·
PG-30→MR-08 · PG-31→MR-17 · PG-32→MR-31 · PG-33→MR-09 ·
Recon A(W0.2 error text, W1.2, W1.4, W5.4)→MR-23 · Recon B→MR-16 ·
Recon C→MR-32+33+13+14 · Recon D→MR-24+26+27+29 · Recon E→MR-28+09 ·
Recon F#1..13→MR-13,20,22,19,29,21,21,22,21,07,23,29,29 ·
Census risks 1–5→MR-01,02,06,03+07+08,17 · Census §7→MR-18 · Census §4→MR-09.

⚠ PROTECTION NOTE (PG-8): gen-3.0 protection (`protected_generations` →
`{v1,'3.0'}` both charts, promised in plan W6.4, never authored) rides in
MR-06's migration; its gate: a seeded unauthorized DELETE of a gen-3.0 row
is refused by the trigger. Also note census: the protection trigger keys off
asset_id='ka_gochara_sweep' in build_protected_assets — the protection ROW
stays under the retired id by design; MR-06 documents this binding so no
future cleanup "fixes" it into deletion.

## §8 — EXECUTION SEQUENCE + REQUIRED NATIVE RULINGS

Sequence (hard dependencies): MR-01 → MR-02 → MR-05 → MR-06(+PG-8) → MR-03/04/07/08 →
MR-13 → MR-14+15 → MR-10 → MR-12 → MR-19..23 → MR-20 → MR-24 (full battery) →
MR-26..30 → MR-29 re-close verdict. Parallel any time: MR-09, 18, 25, 30, 34,
35. SAMPŪRTI-owned, gates P-G1: MR-17 (+MR-31 merge).
**W6-COMPLETE marker posts ONLY after MR-01..08, 10, 13, 14, 15, 24 gates
pass** — i.e. ALL remediation production builds precede the marker, so
SAMPŪRTI's P-G1/S5 never overlap a gochara rebuild (coordination Alignment
Protocol §2). **MR-16 is the ONE planned post-marker build**: a versioned
iteration that, on landing, triggers SAMPŪRTI's PA-5 scoped re-field + R14
measurement-versioning (new measurement beside, never overwriting). Verified
low-risk: gochara corpus changes alter field PROVENANCE edges, not field
values. **R-COORD-4 (coordination file) governs the gochara_* tools'
end-state** — retain-vs-later-joint-retirement is a native ruling; every MR
item remains valid under either outcome; no gochara_* surface retires until
ruled.

Native rulings required (nothing else can close these): (1) MR-11 —
serving-resolution bar; (2) MR-16 — only if 27-class scope is to be reduced;
(3) MR-28 — confirm the adjudicator delegation covers the five retro rulings.
