# Lane 2 Evidence-Sufficiency — Shard 2-b18 (K5–K8, Kala-vidhi)

Worker: P-12 evidence-plan-then-acquire. Channel: DEPLOYED MCP connector (read-only,
doctrinal public channel). As-of date: 2026-07-12.
Charts: C1 = 482012f1-… (Abhisek Mohanty) · C2 = 1c826d5a-… (Abhinandan Mohanty).

Variant note: narrow vs broad share the SAME evidence-acquisition trace; only the width/
depth bar (and therefore the verdict) differs. Evidence acquired once per (code, chart).

§4 class legend (as used here): 1 = UNREACHABLE (retrieval/serving-plane gap; sub-types
served-only-by-down-pipeline / truly-unreachable / by-nonexistence) · 4 = EMPTY SHELL
(advertised category returns zero rows) · 5 = DISHONEST self-description (masking) · 6 =
UNUSABLE FORM · 9 = UNGOVERNED JUDGMENT (improvisation). UNANSWERABLE-BY-DESIGN = scope
boundary, not a defect.

---

## Cross-cutting infrastructure findings (bear on K5/K6/K7 for BOTH charts)

**INFRA-1 — Kala (L3) temporal layer is sidecar-down / fallback_empty.**
`kala_temporal_bundle` (include_snapshot=true, C1) → `sidecar_available:false`,
`mode:"fallback_empty"`, `note:"Sidecar unavailable — graceful-empty response (native data
removed by D7 remediation)"`. `active_dasha:null`, `transit_state:"sidecar unavailable —
no transit data"`, `timeline_excerpt:[]`, `convergence_windows:[]`, `obstructions:[]`,
`kala_readiness.score:null`. → EVERY dated Kala window / obstruction / current-transit
snapshot is empty on the public channel. Class 1 UNREACHABLE (served-only-by-down-pipeline).
This is the single biggest constraint on the Kala-vidhi (K) question group — these are
fundamentally temporal questions and the temporal engine is dark.

**INFRA-2 — `ganita_sade_sati_get` EMPTY SHELL on core categories.**
Advertises 15 `categories` incl. `sade_sati_cycle`, `sade_sati_phase`,
`sade_sati_phase_quarter`, `sade_sati_cancellation_check`,
`sade_sati_concurrent_dasha_overlay`, `janma_shani_period`, `dhaiya_period`. Actual rows
returned (default limit 25000, next_cursor=null → complete): **only 2 categories** —
`ardha_ashtama_shani_period` (58) + `anumukha_shani_period` (20) = 78 rows, IDENTICAL
structure on C1 and C2. The primary sade-sati phase/cycle/cancellation categories return
ZERO rows. Class 4 EMPTY SHELL + Class 5 DISHONEST (the `categories` array lists them as if
delivered — masking the empty core).

**INFRA-3 — `ganita_transit_anchors_get` is natal-only despite the name.**
graha=saturn, C1 → `total:1`, a single NATAL anchor (natal_sign libra,
natal_house_from_moon=9). No Saturn transit-ingress timeline. → the Saturn Pisces→Aries
ingress (= sade-sati END date) and current transit sign are NOT reachable here. Class 1
UNREACHABLE-BY-NONEXISTENCE (transit ingress timeline computed nowhere on this channel).

**INFRA-4 — envelope pagination anomaly (minor receipt-honesty).** ganita `*_get`
envelopes report `pagination:{limit:0,total:null,next_cursor:null}` even when the default
limit is 25000 and the full row set is returned. Reported limit (0) contradicts the applied
limit; `total` is null so a consumer cannot verify completeness from the envelope. No actual
truncation observed (78 rows < 25000). Low-severity Class 5 (envelope misreports its own
budget). trim_seen recorded true on the strength of this anomaly + INFRA-2 empty-shell.

**INFRA-5 — LEL walled off from the doctrinal channel (bears on K8).**
`lel_query` C1 and C2 → `total_count:0`, `no_leakage_note:"life_events is calibration
corpus only — must not feed prediction generation"`, `b3_compliant:true`. LEL anchoring is
deliberately unavailable on the public channel = UNANSWERABLE-BY-DESIGN for the
LEL-anchored dimension of K8.

---

## K5 — sade-sati status/phase

**Evidence plan (acharya needs, in order):** (1) janma rashi = Moon sign; (2) current
Saturn transit sign → which of the 3 phases (Saturn in 12th/1st/2nd from Moon); (3) phase
start/end + pada quarter; (4) cancellation checks (Vedha/argala/exalt-cancellation); (5)
concurrent Vimshottari overlay; (6) remedial pointer. Tools: `ganita_sade_sati_get` (primary),
`kala_temporal_bundle` snapshot (current transit), `chart_snapshot` (Moon sign),
`ganita_transit_anchors_get` (Saturn ingress).

**Acquired:** `chart_snapshot` C1 → Moon = Aquarius 29°46' (Purva Bhadrapada) ⇒ janma rashi
Aquarius (janma-rashi sade-sati window = Saturn transiting Cap→Aqu→Pis). `ganita_sade_sati_get`
C1/C2 → INFRA-2 (only ardha-ashtama + anumukha period windows; e.g. C1 anumukha CYCLE_2
period_end 2027-06-02). `ganita_transit_anchors_get` saturn → natal-only (INFRA-3).
`kala_temporal_bundle` snapshot → sidecar-down, no current transit (INFRA-1).

**Verdicts:** narrow = **INSUFFICIENT** (the literal ask — current phase + phase end — needs
the empty `sade_sati_phase` category and a current Saturn transit that is sidecar-dark;
determining "which phase now" forces self-computation of Saturn's position = B.10
fabrication risk). broad = **SUFFICIENT-WITH-GAPS** (Moon=Aquarius + natal Saturn 9th-from-
Moon + dated ardha-ashtama/anumukha Saturn-period windows compose a partial Saturn-affliction
narrative; the sade-sati phase classification itself is a flagged, un-papered gap).

**Class-9 improvisation (logged):** to answer at all, the LLM must (a) choose to proxy the
sade-sati phase from the anumukha/ardha-ashtama period end dates OR self-compute Saturn's
transit sign (method choice); (b) translate the taxonomy tokens `anumukha_shani` /
`ardha_ashtama_shani` into life-language "the hard Saturn stretch" (taxonomy→life-language).

## K6 — dasha-sandhi risk periods

**Evidence plan:** (1) full Vimshottari maha/antara/pratyantara timeline with start/end
dates; (2) junction (sandhi) points + any sandhi risk flag; (3) severity/obstruction
classification at each junction; (4) concurrent transit at junction. Tools: `get_dashas`
(primary), `get_temporal_windows` / `kala_windows_get` (obstruction/severity),
`kala_temporal_bundle` (transit overlay).

**Acquired:** `get_dashas` C1 → chart_dashas timeline, Mercury maha 2010-08-18→2027-08-18,
antara/pratyantara rows, each carrying a `sandhi_flag` boolean (all observed = false).
`get_dashas` C2 → Saturn maha 2010-04-23→2029-04-23 (own-sign Scorpio, 8th), same structure.
Junction DATES are fully derivable (C1 maha turn 2027-08-18; C2 2029-04-23). Obstruction/
severity classification: sidecar-empty (INFRA-1). Transit overlay at junction: unreachable
(INFRA-1/3).

**Verdicts:** narrow = **SUFFICIENT-WITH-GAPS** (junction dates + built-in sandhi_flag give
a composable answer; gaps = no computed risk/severity window, no transit overlay). broad =
**SUFFICIENT-WITH-GAPS** (the multi-level junction picture across the 10-yr window is well
covered; the "risk" object itself is never computed — all sandhi_flag=false and no
obstruction asset — so the risk framing still rests on judgment).

**Class-9 improvisation:** the "risk" adjective is ungoverned — with sandhi_flag uniformly
false and Kala obstruction windows dark, the LLM must itself choose the sandhi width (last/
first 1/8? tithi-based?) and assign severity (method choice + silent decomposition).

## K7 — "when does the current difficulty end"

**Evidence plan:** (1) identify the CURRENT difficulty object (active malefic dasha lord in
bad condition / active sade-sati phase / active obstruction window); (2) its end date; (3)
corroborating transit. Tools: `kala_temporal_bundle` (obstructions — the literal
"difficulty" windows), `get_dashas` (current lord + end), `phala_outlook` / `event_anchors`
(dated anchors), `ganita_sade_sati_get`.

**Acquired:** obstruction windows → sidecar-empty (INFRA-1); sade_sati_phase → empty
(INFRA-2). `get_dashas` C1 → current Mercury maha ends 2027-08-18 (antara derivable).
`phala_outlook` C1 (12-mo horizon) → forward anchors are direction **elevated / opportunity**
(career/transition discovery events, magnitude minor, conf 0.322 structural-not-yet-
empirical) — NOT a "difficulty" characterization. `event_anchors` C1 (2020–2028) → dated
anchor windows with falsifiers, again elevated/opportunity-typed. There is no computed
"current difficulty" object to bound.

**Verdicts:** narrow = **INSUFFICIENT** (the question presupposes a difficulty object the
system does not surface on this channel — obstructions dark, sade-sati phase empty; picking
"the difficulty" and its end date is unsupported). broad = **SUFFICIENT-WITH-GAPS** (dasha
timeline lets one say "the current Mercury mahādaśā turns ~Aug 2027" and pair it with phala
anchors as a general "the chapter shifts ~2027" answer, honestly flagged as not a computed
difficulty-terminus).

**Class-9 improvisation:** SILENT DECOMPOSITION — the LLM must self-select what "the current
difficulty" refers to (sade-sati? antardaśā? a dosha?) with no computed anchor; and
translate an "elevated/opportunity" phala anchor into difficulty-language if it leans on
phala_outlook (taxonomy→life-language, against the data's own valence).

## K8 — retrospective period explanation (LEL-anchored where available)

**Evidence plan:** (1) past LEL events (dated); (2) the dasha/bhukti + transit active at
each event; (3) map event ↔ period → explanation. Tools: `lel_query` (primary — the
anchors), `get_dashas` (past back-timeline), `event_anchors` (dated windows),
`judgment_query`.

**Acquired:** `lel_query` C1 and C2 → **0 events** (INFRA-5, no-leakage firewall — LEL is
calibration-only and walled from this channel). `get_dashas` back-timeline available to 2010
(C1 Mercury maha from 2010; C2 Saturn maha from 2010) → generic retrospective dasha mapping
possible. `event_anchors` returns forward/structural anchors, not attested past events.

**Verdicts:** narrow = **INSUFFICIENT** (the "LEL-anchored" retrospective — explaining a past
period against attested life events — is impossible with lel_query returning 0; the LEL
anchoring is UNANSWERABLE-BY-DESIGN on this channel, and without it the anchored explanation
cannot be composed). broad = **SUFFICIENT-WITH-GAPS** (the dasha back-timeline supports a
generic "2010–2027 you ran Mercury mahādaśā; sub-lords were X/Y…" retrospective, but with no
event anchoring it is unfalsifiable narrative — the gap must be stated).

**Class-9 improvisation:** with no LEL anchors, any "explanation" of a past period is the LLM
choosing which dasha transition to narrate and inventing the lived correlate (conflict
adjudication + taxonomy→life-language), the exact leakage the no-leakage note forbids
feeding into generation.

---

## Tools called (verbatim trace)
`tools/list` · `ganita_sade_sati_get` (C1,C2) · `kala_temporal_bundle` (C1) ·
`chart_snapshot` (C1) · `get_dashas` (C1,C2) · `get_temporal_windows` (C1) ·
`ganita_transit_anchors_get` saturn (C1) · `lel_query` (C1,C2) · `event_anchors` (C1) ·
`phala_outlook` (C1) · `phala_predictive_anchors_get` (C1). Throttled ~1s between calls.
C2 phala/kala not re-called — parity assumed from identical infra behavior (INFRA-1/2/5
confirmed chart-agnostic: C2 sade_sati identical 2-category structure, C2 lel=0, C2 kala
same sidecar).
