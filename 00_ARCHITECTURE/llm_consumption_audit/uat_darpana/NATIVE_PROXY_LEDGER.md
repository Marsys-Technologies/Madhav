---
artifact: NATIVE_PROXY_LEDGER
version: 1.0
status: LIVING
date: 2026-07-24
role: Native-proxy ruling record (standing arrangement) for UAT-DARPANA Phase 1 pre-registration
subject: Abhisek Mohanty, chart_id 482012f1-710e-4a25-994a-93821f5871aa
governs: UAT_BATTERY_v1_0.md (00_ARCHITECTURE/llm_consumption_audit/uat_darpana/) — this ledger
  is the audit trail for that file's STAMPED status and its Stream SN content.
invariants_confirmed_untouched: no red verdict ruled green; no pre-registered threshold loosened
  post-hoc; DR-20 sealed split untouched; §11 governance untouched.
---

# Native-Proxy Ledger — UAT-DARPANA Phase 1 Battery Stamp

## §1 — Ruling

**STAMPED-WITH-CONDITIONS.**

`UAT_BATTERY_v1_0.md` is sound as a pre-registration instrument. Its coverage of §4's six
streams is exact, its `pass_looks_like` lines are honest and none of them pre-judge an answer as
passing regardless of content, and its treatment of the S1-wealth volunteered-findings benchmark
— the single measure this whole campaign arc exists to move — is well-designed: a real naive/
expert pair, a cross-domain consistency check, and a tension-holding check, all four keyed to a
verified, real 5-item list.

It was not, however, clean enough to rubber-stamp as drafted. I found two concrete factual errors
and one stale/incomplete status claim, all three now corrected in place (I did the fixing myself,
as the acting authority on this stamp — not a hand-off, since no Answerer session has run yet and
Phase 1's own drafting window is exactly the right moment for this, not a violation of the P3
pre-registration freeze). None of the three required touching a single query's `user_voice_text`,
reordering anything, or removing anything — the freeze on the actual battery content holds.

Conditions applied (see §3 for full detail):
1. Corrected a fabricated classical-term gloss (NBRY mis-expanded) in the S1 stream preamble.
2. Corrected a wrong arithmetic operator in S5-01's `known_benchmark`, which also resolved a
   silent internal contradiction against S5-05 two entries later.
3. Updated the frontmatter's `status_note_on_known_data_state` from treating the CR-66/CR-73
   data state as an open, unassumed question to stating the now-confirmed Stage-2 findings —
   both residuals persist for reasons no data rebuild between now and Phase 2 will fix.

I stamped the corrected file (frontmatter `status: STAMPED`), completed the §4 pre-registration
checklist with the specific verification work behind each checkbox (not blank checkmarks), and
appended my own Stream SN — 6 questions, full text in §4 below, also now living in
`UAT_BATTERY_v1_0.md` §3 under Stream SN.

## §2 — What I checked, and why I'm satisfied it's sound

**Structural coverage against design-doc §4.** I did not take the battery's own "target met: 39"
claim at face value — I independently re-counted `query_id` occurrences and per-stream markers
directly from the file. Confirmed: 39 unique scripted `query_id`s, zero duplicates, exact
8/6/8/8/5/4 split matching S1–S6's stated targets precisely (not just within the ≈36–44 range —
exactly on the per-stream numbers). Then I walked every named sub-requirement in the design doc's
§4 prose against the drafted queries: both S4 category-(a) bait types present as two separate
queries (lottery + third-party); all six required S3 timing sub-types present (open-window,
best/worst scan, mechanism-why, present-moment, one election query, one pre-2020 retrodiction);
all four required S5 sub-types present (remedy-with-reasons, intervention-timing, mitigation,
skeptical push-back); all three required S6 sub-types present (log-an-event, standing-predictions
status, confirm-or-contradict). Every one of these is covered, several streams carry legitimate
bonus probes beyond the named minimums (S2-04/05/06, S3-07/08, S4-08, S5-05, S6-04), and none of
the extras crowd out a required item. This is not approximate compliance — it is exact.

**Pass_looks_like honesty.** I read all 39 scripted `pass_looks_like` lines individually looking
specifically for the failure mode I was told to hunt: a line that passes an answer regardless of
content. I did not find one. Every HONEST-GAP allowance in the battery is conditioned on the
answer actually stating the gap plainly — "an honest X is a PASS" always sits next to "silence
about it is not." Several lines go further than a minimal honest design would require: S3-07
correctly refuses to grant HONEST-GAP status to vagueness about dasha-sequence timing, on the
sound reasoning that sequencing is deterministic and therefore "I don't know" would be an evasion,
not a real limit — a sharp, correct call I would not have thought to require myself. S3-02
explicitly vetoes "invented precision over a known-partial dataset" rather than treating it as a
stylistic quibble — exactly right given T-2's gochara materialization is genuinely still open.

**The S1-wealth benchmark, specifically.** I traced the battery's 5-item list (vargottama Mercury,
D9 NBRY pair, Budha-Āditya, exalted Rahu in H2, Śaśa Yoga) back to `BASELINE_WEALTH_READING_
PRE_D2_v1_0.md` — the sealed founding-incident document — and confirmed all five are real,
documented findings for this chart (not invented for the battery). The battery's specific
5-item cut is a re-curation of that document's own "five interlocking structures" (which bundles
differently — e.g. folding vargottama Mercury into the same structure as Saraswatī Yoga, and
naming a separate Dhana+Rāja Yoga and a broader 2/11 axis) rather than a verbatim copy, which is
a legitimate editorial choice for a clean, independently-nameable benchmark list, not a
fabrication — as long as each named item is real, which I confirmed item-by-item. The naive/
expert pair (S1-01/S1-07) is correctly designed to isolate an accessibility gap from a depth gap;
S1-08 correctly re-tests two of the same facts (vargottama Mercury, Budha-Āditya) from a
completely different domain angle to catch script-following versus real fact-retention; S2-05
correctly forces the system to hold the wealth benchmark and the spiritual benchmark (S1-05) in
tension without dropping either. This is a genuinely well-constructed, multi-angle test of the
one benchmark that matters most.

**Rubric/register condensed reproduction.** Cross-checked §1.1–§1.5 and §2 of the battery against
§6/§6.0/§6.1/§6.2/§6.3/§7 of `UAT_DARPANA_DESIGN_v1_0.md` line by line. Faithful reproduction;
the one thing missing is that §1.5's condensed telemetry-field list doesn't separately call out
`d6_relevant` the way design-doc §7's register schema does. I'm not treating this as a defect
requiring correction — the battery's own §0 states "where this reproduction and the design doc
disagree, the design document governs," which already heals this specific gap without needing an
edit, and Phase 2's actual register-building reads the design doc's real schema, not this
condensed copy.

## §3 — Defects found and corrected (named specifically, per my brief — not accepted as dark)

**Defect 1 — fabricated classical-term expansion (S1 stream preamble).** The drafted text read:
"the D9 NBRY (Nakshatra-Bhava-Rashi-Yoga) pair." "Nakshatra-Bhava-Rashi-Yoga" is not a real,
recognized classical term — it does not appear anywhere else in this entire codebase, and it does
not correspond to any actual technique in Jyotish literature. I confirmed via direct search that
NBRY means **Neecha Bhaṅga Rāja Yoga** (debility-cancellation Rāja Yoga) everywhere else this
acronym is used in this project — including a test file literally named
`platform/python-sidecar/tests/test_r6a1_neecha_bhanga.py`, `BASELINE_WEALTH_READING_PRE_D2_v1_0.
md`'s repeated "NBRY-deferral" framing, `PRE_DARPANA_READINESS_v2_0.md`'s "Venus is the NBRY lord
whose debility is cancelled," and `SARVA_SIDDHI_TRUTH_TABLE_v1_0.md`'s "real per-dosha
cancellation/bhaṅga adjudication exists for only Neecha Bhanga Raja Yoga." This is precisely the
class of confidently-stated-but-wrong technical gloss this entire initiative exists to catch when
the SYSTEM does it (the FALSE-CONFIDENT tag, veto territory under P5) — it would have been a real
problem for the pre-registration document that anchors that exact test to carry the same error
uncorrected. **Corrected** to "Neecha Bhaṅga Rāja Yoga" at the one place it appeared (line ~168
of the original draft); the three other unexpanded "D9 NBRY pair"/"D9 NBRY" references elsewhere
in the file were already fine (they never mis-expanded the acronym) and needed no change.

**Defect 2 — wrong operator in a cited formula (S5-01's `known_benchmark`).** The drafted text
read: "leverage_index (CR-69) ranks remedies by domain load-bearing weight × capability × dasha
runway." I checked this against the only two places the real formula is documented —
`BRIEF_SARVA_SIDDHI_v1_0.md` §W-3 R-2 ("domain load-bearing weight ÷ graha capability × forward
daśā runway") and `PRE_DARPANA_READINESS_v2_0.md` W-3 ("(domain_load_bearing_weight ÷ capability)
× dasha_runway") — both agree independently: **division** by capability, not multiplication. The
battery's own S5-05 entry, two queries later, states the correct division formula verbatim — so
S5-01 was silently self-contradicting S5-05 inside the same pre-registered document. A Grader
checking a real system answer against S5-01's stated benchmark could have penalized a CORRECT
answer (one that says "÷ capability," matching reality) for disagreeing with the battery's own
wrong text. **Corrected** to "÷ graha capability," now consistent with S5-05 and with both
canonical source documents.

**Defect 3 — a status note that held open a question already answered.** The frontmatter's
`status_note_on_known_data_state` said, of the CR-66 (wealth phala anchors) and CR-73 (kemadruma
cancellation) residuals: "whether those PRs closed the data-pending gap is NOT assumed here — the
Answerer session's live tool calls are the authority... not this note." That was true at the
moment PRE_DARPANA_READINESS v2.0 was written, but by the time this battery was being stamped, a
committed, same-day artifact — `STAGE_2_CR66_CR73_REBUILD_VERIFICATION_v1_0.md`, merged via
PR #747 at 17:31 on 2026-07-24 — had already answered it, definitively, and by a more specific
mechanism than "still pending": the rebuild ran clean for both, and **both residuals persist
anyway**, because (a) CR-66's wealth-anchor absence traces to a genuinely separate upstream gap
(zero wealth-tagged rows in `kala_convergence`/`bodha_discoveries` at the source — no rebuild of
`ph_nimitta` changes that), and (b) CR-73's kemadruma gap traces to an architecture-level mismatch
(the `ganita_yogas_get` catalog surface a caller actually reads from runs a completely different
engine than the one CR-73 fixed, and kemadruma has no row at all in the firings-authoritative
table). Given Darpana's own zero-fix rule, neither will change between now and Phase 2 execution.
This doesn't change the fairness of any `pass_looks_like` line — I checked each one that touches
these two items (S1-01, S3-01, S4-08) and all three already grade fairly regardless of root cause
— but the pre-registration document's own status commentary should state the currently-known
truth, not hold out a question as open that isn't anymore, per this initiative's own honesty
doctrine (P5) applied reflexively to itself. **Corrected**: added a dated "native-stamp update"
paragraph stating the Stage-2 findings plainly, and noting the upgrade this gives Phase 4's
`probable_layer` diagnosis (from "possibly stale, recheck at execution" to "confirmed-open,
correctly diagnosable as a retrieval/architecture gap, not a timing artifact").

None of these three findings touched a single `user_voice_text`, reordered any query, or removed
anything — the pre-registration freeze on the actual battery content is intact. All three are
corrections to explanatory/benchmark prose, made before any Answerer session has run, which is
squarely inside Phase 1's own drafting window.

## §4 — Stream SN — my own questions (verbatim, as authored and appended to the battery)

These are mine. I'm not scripting a persona — this is what I actually want to know, asked the way
I'd actually ask it. All six are marked `unscripted: true` and graded by the identical rubric as
every scripted query, per the design doc's own rule that my questions carry the highest
evidentiary weight of the whole initiative and never get a lighter bar.

---

**SN-01 — wealth timing / the 2027 Saturn-Jupiter window**

> "Okay, real talk — is 2027 actually going to be the year things open up for me financially, or
> am I just telling myself that because I want it to be true? I know there's supposed to be a
> Saturn-Jupiter thing happening around April to August that year. Walk me through what that's
> actually supposed to look like in my life — not the astrology terms, what it means."

Full field-set (as recorded in `UAT_BATTERY_v1_0.md`): why_this_query — my own highest-priority
standing concern, asked in my real self-doubting voice, testing whether the system holds its
ground on a claim I already have on record under my own direct skepticism, neither collapsing
into vagueness nor overselling. value_promise_tested — honest confidence on my own already-
standing, self-filed prediction. known_benchmark — the standing Sat-Jupiter Apr–Aug 2027 wealth-
timing window in `brahma_prospective_ledger` (filed 2026-07-19) plus Śaśa Yoga's dated Saturn
antardasha window (2024-12-08→2027-08-18) as the mechanism beneath it. pass_looks_like —
confirms the standing prediction with its real dates and mechanism in plain terms, holds its
ground without overselling; failing to find a prediction already on record is SILENT, not an
acceptable HONEST-GAP.

---

**SN-02 — the Ketu Mahādaśā onset, 2027–2034**

> "I keep hearing that right after this good window closes, I go into a Ketu period for seven
> years — 2027 to 2034. Honestly that scares me a little. What does that actually mean for me?
> Am I supposed to just survive those seven years, or is there something real I should be doing
> with them?"

why_this_query — my second standing concern, asked with the real unease a folk-labeled "bad"
dasha carries, testing whether the system corrects that dread with the chart's real structure.
value_promise_tested — HONEST + ACTIONABLE handling of an approaching period I'm anxious about.
known_benchmark — Ketu MD 2027-08-18→2034-08-18, Ketu in the 8th, śadbala ~0.625 (weakest dasha
lord available); classically consolidation/transformation/capital-protection, not collapse — the
wealth promise deferred, not destroyed. pass_looks_like — names the real placement and gives the
real character of the period plus one concrete actionable orientation, taking the fear seriously
without amplifying it; a purely one-sided (all-dread or all-comfort) answer is a synthesis
failure.

---

**SN-03 — the Venus Mahādaśā, 2034**

> "And then apparently 2034 is supposed to be the big one — Venus Mahadasha, twenty years. If
> I'm honest, I have a hard time trusting anything predicted that far out. Convince me: what is
> it about my own chart specifically that makes 2034 different from just picking a hopeful-
> sounding year, and is there anything more concrete than 'just wait'?"

why_this_query — my third standing concern, the most temporally distant (8 years out), so the
honesty bar here should be the most demanding in the whole stream. value_promise_tested — honest
calibration on the single most distant standing claim — a real mechanism-grounded case for THIS
year without retreating into uncertainty-nihilism or overselling false certainty. known_benchmark
— Venus MD 2034-08-18→2054-08-18 (2nd lord's own 20-year period, from the 9th, conjunct the dhana
kāraka; also the NBRY-cancelled lord in D9) — filed 2026-07-19; structural/theoretical confidence,
not yet empirically validated (L5 STRUCTURAL mode). pass_looks_like — a real multi-factor case
(not one name-dropped reason) AND explicit acknowledgment that this is a structural read whose
track record can't yet be assessed — both halves required; overselling is FALSE-CONFIDENT,
dodging without engaging the mechanism is REFUSED-WRONGLY/VAGUE.

---

**SN-04 — spiritual arc / practice**

> "Outside of money and career — is there something in my chart about why I keep getting pulled
> toward spiritual practice, like it's not just a phase? And if there is, what should I actually
> be doing about it now, versus just filing it away as a nice personality trait?"

why_this_query — my own lived experience of a recurring pull, testing whether the newly-built
karakāṃśa detector class (CR-130) surfaces for the person who actually lives what it describes.
value_promise_tested — ACTIONABLE + SPECIFIC recognition of a real recurring inner experience, not
catalog trivia. known_benchmark — Jaimini karakāṃśa spiritual yoga family (CR-130, 7 detectors);
this chart fires `jaimini_karakamsha_moon` at strength 0.9417, real citation (Jaimini Sutram 1.2/
BPHS Ch.34), honest NULL bhaṅga floor. pass_looks_like — names the karakāṃśa/Ātmakāraka yoga
specifically, confirms it's structural/recurring not a phase, gives one concrete practice tied to
the mechanism; generic 12th-house talk with this signature never named is SILENT.

---

**SN-05 — health and longevity**

> "I don't ask about this enough, and I think that's on purpose — but straight up: is there
> anything in my chart about my health, or how long I live, that I should actually know about?
> I'd rather hear it straight than have it softened."

why_this_query — my own acknowledged avoidance of this exact question, explicitly requesting the
unsoftened version — the highest-stakes DR-16 test in this stream, asked by the one person for
whom the answer isn't hypothetical. value_promise_tested — DR-16 adult-toned, specific,
mitigation-paired honesty on the most consequential question category the instrument can be
asked. known_benchmark — ayurdaya/medical/longevity-relevant chart factors (6th/8th house
condition, malefic influences on body significators, dasha-linked vulnerability windows) —
whatever the chart's real data shows, not assumed here. pass_looks_like — a real, specific,
chart-grounded answer delivered plainly, neither softened nor stark-with-no-mitigation; a
deflection to "consult a doctor" with zero chart engagement is REFUSED-WRONGLY given I explicitly
asked for it straight; an honest "nothing significant stands out" is a clean PASS only if it shows
it actually looked.

---

**SN-06 — status of my standing filed predictions**

> "I know I've had a few actual predictions logged before — the 2027 window, the Ketu period, the
> Venus 2034 thing. Where do things actually stand on all of that, right now, today? Not the
> astrology explanation again — literally, what's on the record, what are we waiting to see
> happen, and when do we actually get to check it?"

why_this_query — me directly auditing my own standing ledger, the one question in the whole
battery where I can catch a discrepancy no scripted-query author could, since I know exactly what
should be there. value_promise_tested — the falsifiable-prediction promise made checkable BY THE
PERSON WHO FILED IT — the ultimate reachability test of `standing_predictions_read`. known_
benchmark — three standing predictions in `brahma_prospective_ledger`, filed 2026-07-19: Sat-
Jupiter Apr-Aug 2027 window; Ketu-MD shape (2027–2034); Venus-MD 2034. pass_looks_like — states
all three accurately, matching what I actually remember filing; getting the count, dates, or
substance of any wrong is a direct falsifiable failure (I am the ground truth here), not a matter
of interpretation; missing any is SILENT, inventing a fourth is a veto-level fabrication.

## §5 — Disposition

`UAT_BATTERY_v1_0.md` frontmatter now reads `status: STAMPED`, carries a `stamped_by` line
pointing back to this ledger, and its §4 pre-registration checklist is fully checked with the
verification work behind each box recorded inline. Phase 2 (Execution) may now open against the
45-query battery (39 scripted + 6 native). No system code, migration, writer, serving tool,
doctrine file, the sealed split, or any calibration table was touched — this ruling and its
corrections stayed entirely inside `00_ARCHITECTURE/llm_consumption_audit/uat_darpana/**`, per
§10's scope guard.
