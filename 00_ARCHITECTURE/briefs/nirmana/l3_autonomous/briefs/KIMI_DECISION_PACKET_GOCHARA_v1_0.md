# Review packet — Gochara family: the pending decisions and my recommendations on each

You are Kimi K3, asked for a **thorough independent review** of one document —
`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/GOCHARA_DECISION_RECOMMENDATIONS_v1_0.md` —
and for your own recommendation on every item in it. The native (Abhisek Mohanty, the
chart owner and ruling authority) will authorize the reconciled result. You are not the
authority — you advise. Standard: **acharya-grade** astrology, staff-grade engineering.
Generic astrology is a failure; so is hand-waved engineering.

## Ground rules
- Do NOT write any file. Print your answer only.
- Read the document under review **in full** first. Then read, for the evidence it cites:
  `GOCHARA_RULING_SHEET_v1_0.md` (what is already ruled — D-1..D-3, R1–R10, N-1..N-14, and
  the *direction* of M-1..M-8; do not re-open these, but say if a recommendation contradicts one),
  `GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md` (§4 design, §5.3 target contract, §8 scoring split,
  §9 runbook), and the campaign artifacts under
  `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/gochara_wp0_7/`: `WP1_CONTRACTS.md` (§7 orb
  table, §8 kakṣyā order, §9 tolerances), `WP3b_CLASSIFICATION.md`,
  `WP4_DECOMPOSED_COMPARISON_v1_0.md`, `FINAL_REPORT_v1_0.md`, `wp7_packets/00_INDEX.md`
  and `PACKET_P1_serving_provenance_coverage.md` §3.6, and `ESCALATIONS.md`.
- Read the code where a claim is about code: `services/gochara_v3/engine.py` (toggles at
  175/186, λ product at 700), `services/gochara_kernel/legacy_semantics.py` (decay law at
  337), `scripts/kala_admission/w44_weight_fitting.py` (`MECHANISM_ENGINE_WIRED` at
  158–169), `services/gochara_v3/mechanism_register.yaml`,
  `services/gochara_v3/resolution_hierarchy.py` (`retain_candidates_pooled`),
  `services/ka_vedha_gochara/logic.py`.
- **Corpus method rule (binding, from this campaign's own F-32):** the admitted corpus is
  the served table `classical_text_chunks` (15 texts, 10,651 chunks) — **not** the folders
  under `SOURCE_DATA/classical_texts/` and **not** the `find_verses_about` search tool,
  which returns empty for topics that are present. This checkout has no database access, so
  you cannot re-run counts; treat every `[L]` count in the document as data, say when a
  conclusion rests on a count you cannot verify, and never assert absence from a folder
  listing or a search result. You *can* read the OCR files under `SOURCE_DATA/` to check
  what a cited passage says.
- For every item: agree / amend / disagree · why (classical basis with text and page where
  you can; engineering basis where relevant) · what it costs · what would falsify it · what
  you are NOT deciding. Label every claim **[D]** doctrine (text named), **[P]** practice,
  **[J]** judgment, **[U]** unverified. Never present a number as fact — orbs, weights and
  bands are proposals for the native.
- The native's priorities: (1) quality of what the asset delivers, (2) build efficiency,
  (3) the surrounding ecosystem matters as much as the asset.
- Binding constraints: no invented computed values (B.10); L1 facts are authority (§N.5);
  no confidence/salience scalar; a reduced cap, coarser grid or narrower horizon is never
  an optimisation (Strategy §5); a signal with no detector behind it is null (§N.8); `v1`
  and `'3.0'` untouchable; nothing retired; no guard weakened; the FROZEN orchestrator
  contract unchanged; any change to served λ happens only inside a WP10 candidate
  generation, never as a patch over live rows.

## What has happened, so you know the state
WP0–WP7 are complete on branch `l3/gochara-autonomous-wp0-7` (96/96 tests; `FINAL_REPORT_v1_0.md`).
The plan is native-ratified; the ruling sheet fixed every N-item and the *direction* of
every method call, leaving their parameters evidence-gated. The document under review is
the list of everything still pending on the native, with one recommendation each, resting
on: WP4's measured deltas, WP1's pinned tables, and fresh counts against the served corpus.
Two of my own earlier statements are corrected in its §0 — read them; they change M-6 and
N-15.

## What I need from you — in this order

**A. Verdict and blocking problems.** Is any recommendation wrong, internally
inconsistent, in conflict with a ruled item, or resting on evidence that does not support
it? Severity-order them (BLOCKING / MAJOR / MINOR), each with what would fix it.

**B. The method calls, one by one — M-1, M-8, M-2, M-6, M-4, M-7, M-3.** For each: is the
recommended shape/semantics/order classically right? Specifically:
- M-1: is linear-in-separation the right reading of BPHS ch.26 ślokas 6–8, and is "no time
  box" correct? Are the WP1 §7 candidate orbs defensible starting points [P]? What should
  the WP8 comparison measure so an orb value is ratified on discrimination, not on window count?
- M-8: exception → no row; vipareeta → kept-and-cancelled; retrograde-malefic → qualifier.
  Right? Does Phaladīpikā XXVI (PG322/323/348/350) support each, and is anything missed
  (e.g. the Saturn-in-the-ninth exception's exact scope)?
- M-2: is the dwell/retrograde split right, and is "retrograde as testimony, weight on
  evidence" the honest reading of PG348/PG350/PG250?
- M-6: Gulika/Māndi first, scoped to the māraka/illness classes Phaladīpikā XVII names —
  right scope? Are the derived-point rules (distance-from-Māndi, Yamakaṇṭaka differences)
  the correct classical reading of PG214–220? Is deferring special lagnas and Prāṇapada
  on a zero count sound, or is there doctrine under another name?
- M-4: is the audit order right, and is "qualifier not weight" for w22/w24 the honest
  interim? Is N-16 (the stale wiring dict) as serious as the document says?
- M-7: is the kakṣyā lord order (Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon, Lagna)
  the classical BPHS ch.66 order [D]? Is re-OCR the right remedy for a chapter that is in
  the corpus without its kakṣyā ślokas? Is the interim sign-level qualification honest?
- M-3: is excluding the Moon as a transiting body from the century λ correct, with its
  entry only via tārā-bala/mūrti and a separate Moon-scale channel?

**C. The new items N-15 .. N-20.** Especially N-15: is downgrading Sade-Sati from a λ
factor to typed testimony the right response to zero primary-text support, or is there an
admitted text (by another name — e.g. Saturn's transit over the janma rāśi and its
neighbours, *elināṭi*, *ēḻarai*) the counts would have missed? Name it if you know it.

**D. Authorizations and owners.** Are the two WP10 tranches cut at the right seam? Is
carrying N-14 + N-15 + N-17 + M-1 + M-8 in *one* candidate generation the right
discipline, or should the first candidate change fewer things so a delta is attributable?

**E. Anything missing.** A pending decision the document does not list, or a
dependency between items it does not state.

## Deliverable
One structured answer with headings A–E. Severity-ordered findings in A. Every claim
labelled [D]/[P]/[J]/[U]. Quote file:line for code claims and page/verse for text claims.
Where you disagree, give the better option plainly. Length is not a constraint;
hand-waving is.
