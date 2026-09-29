---
artifact: SUVARNA_L3_FOCUS_FAMILIES
canonical_id: SUVARNA_L3_FOCUS_FAMILIES
version: "1.4"
status: "PRE-FINAL v1.5 — for the parallel independent reviews (GPT-6 Astra, Kimi K3; N-30); then reconciled by Strategic Suvarṇa into the final set; then N-1"
produced_on: 2026-09-28
produced_in: session "Strategic Suvarṇa"
companion_of: SUVARNA_CAMPAIGN_PLAN_v1_5.md §5.3 (Track F)
evidence: >
  Three read-only reconciliations, 2026-09-28, each with a source for every claim:
  l3_recon/GOCHARA_RECON.md · l3_recon/KSHETRA_RECON.md · l3_recon/SANGAM_RECON.md.
  Figures below are theirs; effort figures are the researchers' estimates, in their own units.
  v1.4 Gochara facts: the Pravāha campaign's tracker (http://127.0.0.1:8766) and its decisions D-SCOPE, D-41, D-BRIEF,
  D-CLOUD, D-FLIP, ADK-0029 (read 2026-09-30); measurement/BASELINE_3_0_v2_1.md; git (285bff17c).
changelog:
  - "1.4 (2026-09-30, v1.5 fold): 'the L3 Gochara session' / 'the live workstream' renamed to the Pravāha campaign throughout (fold spec §5). Gochara facts: PR #2731 merged as 285bff17c, deploy in flight (Pravāha A1.2); first sound candidate '5.0' (D-41); build for 482012f1 only, no 1c826d5a switch (D-SCOPE/ADK-0029); the sealed v3.0 doctrine is the final brief (D-BRIEF; SEAL-G); migrations 1071/1072/1086 reported applied by Pravāha, not yet visible in _migrations_applied on 2026-09-30. New out-of-scope validity note ('3.0' baseline, plan §1.5). Saṅgam/Kṣetra: no family sessions known; Suvarṇa Track F owns design (Architect lanes, tier-4 template, Pravāha's L3_FAMILY_COORDINATION_v1_0.md as an input); implementation ownership at J1 (J1.FO). §5 regime rewritten (N-28, J1.FO; the N-17 regime kept as history). §6: F-3 decided (N-32, with the measured NOT NULL columns and the transitive cascade footprint); F-1/F-2/F-4/F-6 decided by Strategic Suvarṇa on the owning session's recommendation or from Track F's own design lanes (N-28). §7: D2 unchanged in substance, plus Pravāha's condition (nothing certifiable until the registered writer produces '5.0'); F3.G split into F3.Ga/Gb/Gc; seals, hand-backs and N-21 by Strategic Suvarṇa (N-28). Plan references → SUVARNA_CAMPAIGN_PLAN_v1_5.md."
  - "1.3 (2026-09-29, review pass 2): the cascade measured: eight ON DELETE CASCADE keys into bodha_msr_signals from seven tables (kala_convergence, kala_darshana, kala_bhavishya, kala_activation, kala_obstruction, bodha_signal_embeddings, bodha_contradictions ×2), so every L2 MSR rebuild also empties four non-family L3 tables and two L2 tables. F-3 now means cascade removed on all eight keys; L2 MSR waves, wave 0 included, wait for F-3 decided and the F3.FK detector. Brief seals recorded by Strategic Suvarṇa (SEAL-G/S/K). FAMILY_ASSETS.json path fixed."
  - "1.2 (2026-09-29, review pass 1 and D2 folded): §5 rewritten for the regime in force under N-17: the family sessions own F1–F4 under their own sealed briefs, are not gated by J1 and may change production while Suvarṇa waves run; the old Suvarṇa-run sequence (F0–F4) is kept only as history. New §7: how Suvarṇa certifies family assets (D2: orchestrator-built rebuild plus Suvarṇa re-measure; excluded from wave completion; readers wait asset by asset; staleness exemption; hand-back; Kṣetra on the L5 critical path; F-3 recorded decided by Strategic Suvarṇa, a foreign-key change preferred). §6 gains a status column from the decisions log. §0 and §1.2 brought up to date (the '4.1' century rebuild; PR #2731 open and mergeable). Sources: REVIEW_PASS1_SUBSTANCE #4, #9, #10, #22, #23; REVIEW_PASS1_CONSISTENCY #11; FABLE_REVIEW_D1_D5 §D2."
  - "1.1 (2026-09-29): Gochara brought up to date with the lane's ruling ADK-0027 (commit 33b725778). The lane switched the canonical chart to '4.0' at 19:22:58Z before F-0 arrived and reversed it at 19:29Z; '4.0' as a label is retired; F-0 is in force; the horizon default is now the full century (F-5 settled by F-0); §1.2 gains the seven-step standing sequence; Saṅgam and Kṣetra now wait on 'the new Gochara generation', not on '4.0'."
  - "1.0 (2026-09-28): first draft. Current state, target, gaps, effort and risk per family; the links between the three families; Track F's sequence; the rulings it needs."
---

# Suvarṇa — the L3 focus families: Gochara, Saṅgam, Kṣetra

## §0 · The picture in one page

**None of the three families is in a good state, and they depend on one another.**

| Family | What it is | State today, on the canonical chart `482012f1` |
|---|---|---|
| **Gochara** (transits) | Transit windows, vedha, resonance: when planets activate natal structure | Served generation `'3.0'` (914 rows, 1984–2084). Run by the **Pravāha campaign**. PR #2731 merged 2026-09-30 as `285bff17c`; the post-merge deploy is in flight (Pravāha A1.2). `'4.1'` is an engineering proof, never flipped; the first sound candidate is `'5.0'` (D-41), built for `482012f1` only (D-SCOPE). The flip waits for Pravāha's J2 (`'5.0'` gated and retrodicted) and its N-FLIP. |
| **Saṅgam** (convergence) | Where several timing systems agree on the same window | **0 rows.** Almost certainly wiped by a cascade when `bo_laksana` was rebuilt on 2026-09-08. The September elevation work is unmerged. |
| **Kṣetra** (the timing field) | The combined field over life events: which event classes are active when | **Never successfully built.** 8.57 million rows left over from a crashed build, on a time axis shifted by about 15.9 years. Rebuilds are refused by design until versioned storage (W7) exists. |

**How they connect:**

```
        bo_laksana (L2) ──cascade delete──► Saṅgam rows
                                  ▲
Gochara ─────windows───────► Saṅgam
   │
   └──windows (read, but not declared)──► Kṣetra ◄── bo_upaya (declared, but never read)
```

- **Gochara is upstream of both others.** Saṅgam and Kṣetra pick up whatever Gochara generation is live on their next build.
- **Saṅgam is locked to L2.** Its rows cascade-delete when `bo_laksana`'s signals are replaced. Once Saṅgam is rebuilt, the reverse happens: L2's replacement is refused (register R243). F-3 (N-32) removes the lock (§4, §6).
- **Kṣetra's declared dependencies are wrong.** It declares `bo_upaya` and `bo_sangati` but never reads them, and reads about ten tables it never declares, including Gochara's windows. Through the phantom `bo_upaya` edge, `bo_upaya`'s known rebuild failure (R244) would mark Kṣetra BLOCKED.

**Effort to finish, as estimated by the researchers:**

| Family | To correct, and back in production | To "fully enriched" |
|---|---|---|
| Gochara (2026-09-28 estimate; the Pravāha campaign's own plan now governs) | 12–25 agent-days | +30–55 agent-days |
| Saṅgam | 8–15 session-days | 33–60 session-days |
| Kṣetra | 5–9 weeks (a correct, published, served 6-class field) | 10–20+ weeks |

- These overlap and partly run in parallel. They are not a simple sum.
- **The longest pole is Kṣetra**, because nothing can reach its production data until W7 exists or Strategic Suvarṇa decides an interim clear (F-1).

---

## §1 · Gochara

### 1.1 · Inventory

- **Active:** `ka_gochara` (windows), `ka_gochara_resonance` (`gochara_resonance_map`), `ka_vedha_gochara` (`kala_vedha_gochara`).
- **Inactive:** `ka_gochara_v3_century_materialize` (the century writer, held and deactivated); `ka_gochara_sweep` (retired 2026-09-08).
- **L0 inputs:** `bg_gochara_arcs`, `bg_gochara_citation_resolution`.
- **Nirmāṇa "froze"** the three active assets; that is kept only as a starting point.

### 1.2 · The Pravāha campaign (formerly "the live workstream")

**Current, 2026-09-30.** Gochara is run by the campaign **Pravāha**: a steward session and two Kimi Code sessions, its
own tracker (http://127.0.0.1:8766, reading `/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/control/pravaha/plan_model.json`)
and its own decisions (D-*, ADK-*). There is no separate "L3 Gochara session". Suvarṇa records only its own decisions
and cites Pravāha's ids for Gochara facts (N-SCOPE/D-SCOPE, N-41/D-41, N-BRIEF/D-BRIEF, N-CLOUD/D-CLOUD,
N-FLIP/D-FLIP, ADK-0029).

- **PR #2731 merged** 2026-09-30 as `285bff17c`; the post-merge deploy is in flight (Pravāha item A1.2, verified from
  the running service's `env.DEPLOY_SHA`).
- **Scope (D-SCOPE, recorded as ADK-0029):** build for `482012f1` only; `1c826d5a` is not built or switched.
- **Labels (D-41):** `'4.1'` is an engineering proof, never flipped; the first sound candidate is **`'5.0'`**.
  Century builds on Cloud Run are candidate-only (D-CLOUD). The flip of `482012f1` to `'5.0'` (A6.1) waits for J2
  (`'5.0'` gated and retrodicted) and N-FLIP (pending).
- **Final brief:** the sealed doctrine
  `/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/sealed/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md`
  (status SEALED; countersigned by the native, N-BRIEF/D-BRIEF). It satisfies Suvarṇa's SEAL-G.
- **Migrations:** Pravāha reports 1071, 1072 and 1086 applied; on 2026-09-30 they were **not yet visible** in
  `_migrations_applied` (read as `suvarna_reader`: the highest Gochara row is still 1150). Re-read before relying on
  them.

**History (2026-09-28/29, before Pravāha):**

- **Branch:** `l3/gochara-autonomous-wp0-7`. **PR #2731:** open; mergeable since `main` was merged into the branch (2026-09-29).
- **Already in production:** guard triggers; migrations 1080–1084, 1087, 1091 and 1150; a registry re-pin; and a `'4.0'` candidate (138,837 contacts and 48 coverage rows per chart, unpublished).
- **One production write failed tonight** (23:27 IST, lost connection) while writing the first `'4.0'` windows.
- **What it planned to deliver before ADK-0027** (superseded by the standing sequence below): `'4.0'` windows for 2020–2030, each citing its contact ids; authority switched on both charts after a 24-hour soak; the old `'2.0'` rows retired; eventually PR #2731 merged (kernel, vedha exceptions, serving code).
- ~~The switch is pre-authorized~~ **Superseded 2026-09-29 by F-0 (ADK-0027).**

**Update, 2026-09-29 (ADK-0027, commit `33b725778`):**
- **What happened.** The switch on chart `482012f1` ran at 19:22:58 UTC under the old authorization, before F-0 arrived. The lane traced the risk itself and reversed it at 19:29 UTC: authority back to `'3.0'`, 4,415 `'4.0'` windows deleted, integrity checks (a)–(k) green in both time zones, served output byte-identical to before. For those six minutes the hazard was live, but nothing consumed it: the Gochara lane (now the Pravāha campaign) checked read-only and found no rows in `query_plan_log` or `audit_events` for 19:22–19:30 UTC, no MCP requests, and no reading, chat or transit requests to the web app. Chart `1c826d5a` was never switched.
- **`'4.0'` is retired as a label.** Both charts move to a new full-century generation under a new label.
- **Standing sequence (amended by ADK-0029 per D-41 and D-SCOPE: one chart, the `'5.0'` candidate; step 7 dropped):**
  1. rebuild the candidate (`'5.0'`) on the full century for `482012f1` only (D-SCOPE), and re-run all evidence and gates;
  2. merge `main` into the branch (a merge commit) and build the readiness packet;
  3. report readiness to the native;
  4. PR #2731 merged (done 2026-09-30, `285bff17c`; Pravāha's own merge, outside Suvarṇa's merge model) and deployed;
  5. verify the running code from the service's `env.DEPLOY_SHA`;
  6. switch `482012f1`, with trigger #0 (served rows carry the new generation, or reverse at once), then soak;
  7. ~~switch `1c826d5a`, then soak~~ — dropped (D-SCOPE).

### 1.3 · Gaps found on 2026-09-28 (Pravāha's sealed doctrine and plan now carry them)

1. **Serving code not deployed.** (Now merged with #2731; deploy in flight, A1.2.) `main`'s forecast tools have no `'4.0'` branch. A switch before PR #2731 is deployed would serve `'4.0'` data under v1 provenance. **No deploy-before-switch gate was found** (the gap was real: see the §1.2 update; now closed by F-0).
2. **No normal build path.** The registered `ka_gochara` writer is unchanged and still writes the old `_v2` / `'2.0'` table. `'4.0'` comes only from hand-run cutover scripts, so no new chart can get it through the orchestrator. (Pravāha A5.3: the registered writer.)
3. **The horizon shrinks** from about 100 years to 10 (2020–2030). The plan's own example (a 2013 marriage) falls outside it. The researcher found no disclosure of this. (Now addressed: F-0 makes the full century the default.)
4. **The scoring loses variation.** In `'4.0'`, "promise" is 1.0 for all 27 classes; "permission" is a fixed value per class; the tārā factor is skipped; vedha data covers about 15 months of the 10 years.
5. **Designed fixes not yet in production:**
   - resonance fixes R-1 to R-6 (154 targets built on negative results, 54 dangling yoga targets, every row falsely marked "resolved");
   - overlays cover only about 460 days;
   - `main`'s writers would wipe the new stamp columns on any rebuild;
   - the bindu matrix and the Moon channel are not built.
6. **The registry mismatch (R240) has worsened.** The registry, `main`'s seed, the branch's seed and the registered writer now name different tables or generations. Migration 1150 did not touch it; it changed only an integrity check.

### 1.4 · Target ("fully enriched")

From the family's own design documents: a century-horizon, cited, orchestrator-built transit layer with a resolution hierarchy, vedha exceptions, resonance with honest resolution states, and full serving. Details in `l3_recon/GOCHARA_RECON.md` §5. **Superseded as the target of record** by Pravāha's sealed v3.0 doctrine (§1.2). Mapping it onto the tier-4 template's nine gates is Suvarṇa's own A.L3 work, never required of Pravāha.

### 1.5 · A validity note for the native (out of scope; information only)

Astrological validity is not a data-plane obligation of this campaign (plan §1.5); this is recorded so the native sees
it. Pravāha measured the served `'3.0'` generation under its protocol v2.1
(`/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/BASELINE_3_0_v2_1.md`): **T-cover 32/47**
held-out events (68.1 %), against random-control coverage of **68.6 %**, so no observed separation; **T-FP fails on 8
of 9 adverse classes**, whose admitted day-fraction is **99.87 %**. Pravāha's own gates (J2) decide whether `'5.0'`
does better; Suvarṇa certifies data-plane properties only.

---

## §2 · Saṅgam

### 2.1 · Inventory

- `ka_sangam` → `kala_convergence`. Eleven upstreams, including `ka_gochara`, `ka_yojaka`, `ka_dasha_kala` and `bo_laksana`.
- Main downstream reader: `ka_kala_darshana`.
- **Not frozen by Nirmāṇa.** Eight open Nikaṣa gaps.

### 2.2 · State

- **0 rows** on the canonical chart. `kala_convergence.signal_id` cascades on delete from `bodha_msr_signals`, so the `bo_laksana` rebuild on 2026-09-08 almost certainly wiped it. Four sibling `kala_*` tables with the same link are also empty.
- The only rows left: 17,957 on `1c826d5a` (built 2026-08-12) and 2,540 on `cb73cd3d` (Mode D only). Both come from pre-September code.
- No `ka_sangam` build since 2026-08-13.
- **Stage 3** (22–24 Sep, branch `sangam/stage3`) is unmerged. PR #2735 is an open draft failing four CI checks. None of its migrations (1092, 1093, 1088, 1089, 1090) are applied. The independent review said "conforms with amendments", with one high-severity item: the aṣṭakavarga check depends on data no writer produces.
- **Stage 4** was written but never run.

### 2.3 · Gaps

1. **Wrong target point.** On `main`, Modes A and B measure every transit contact against 0° Aries: none of the 50,678 canonical predicates carries a target longitude, and the engine defaults to 0.0. Stage 3 fixes this only partly; dosha predicates get no target at all.
2. **Stage-3 rows are incompatible with `main`.** They carry `peak_date = NULL`, which `main`'s integrity check rejects and readers filter out. The episode grouping key omits `mode`. No stage-3 test touches a database.
3. **Merge blockers.** Four CI failures; two branches disagree on migration numbers; `l3/kala-layer-briefs` holds an older copy of the code.
4. **Scores not comparable across modes.** Mode D is 80% of rows (the same 478 windows repeated for 25 predicates). Several scoring inputs are always empty.
5. **The target design is not built:** reusing Gochara's episode finder; the E1, E3 and E4 elevations; retiring `confidence_*` across five readers; the output-contract columns; density contracts on its two serving modules.
6. **A prerequisite:** `ka_yojaka` is stale, and 79 canonical predicates point at signals that no longer exist. It must be rebuilt first.

### 2.4 · An open strategic question

- ŚAḌ-DARŚANA planned to **retire Saṅgam into `kala_field`** (Kṣetra's table). The elevation plan invests in Saṅgam instead.
- **These are unreconciled.** They must be settled before investing in either (ruling F-2).

---

## §3 · Kṣetra

### 3.1 · Inventory

- `ka_kshetra` → `kala_field`, plus its window, salience, insight, timeline and snapshot tables.
- **Not frozen by Nirmāṇa.** Nine open Nikaṣa gaps. Its `Idem.pattern` gate reads FAIL (refused rebuild).

### 3.2 · State

- **The canonical chart has never had a successful full build.** Its 8,570,075 rows (25 event classes) are left over from 29 build attempts on 2026-09-10/11. The last died with "the connection is lost".
  - Only 14 of the 25 classes got their time windows.
  - Nothing reached the salience, insight, timeline or snapshot stages, so nothing is published.
- **A wrong time axis.** Transit times counted from 2000 are placed on a birth-relative axis: a shift of about 15.9 years, measured live.
- **85.7% of windows** rest on a synthetic baseline rather than real event-rate data.
- **The only published field** is a 6-class run on `1c826d5a` from 2026-08-12. It predates later fixes and has the same axis defect.
- **Rebuilds are refused by design.** Since PR #2607 (2026-09-16), the writer raises `KshetraReplacementHeld` on any populated chart until versioned publish-then-switch storage ("W7") exists. W7 is not built.
- **All Kṣetra branches are merged, but as documents only.** Stage 3 (code fixes proven on fixtures) was authorized on 2026-09-24 and never started. No Kṣetra code has changed on `main` since #2607.
- **A Kṣetra writer change was carried on the Gochara branch**; it reached `main` with PR #2731 (`285bff17c`, 2026-09-30). Its migration 1084 is applied in production.

### 3.3 · Gaps

1. **No rebuild path.** W7, or a Strategic Suvarṇa decision (F-1) for an interim clear of about 11 million rows (about 6.7 GB) under a rebuild plan and a serving guard (N-29, N-33). Until then no fix can reach production.
2. **Correctness defects:**
   - the time axis;
   - the null test is scoped to the whole chart instead of per route;
   - the synthetic-baseline flag is computed, then dropped;
   - a forbidden read up into L4;
   - two tables that differ on every rebuild.
3. **Wrong dependency list:** remove the phantom `bo_upaya` and `bo_sangati` edges; declare the ~10 real reads, including Gochara's windows.
4. **No serving.** `kala_field` is read by nothing. `query_field_trajectory` does not exist. L5's `mi_bhara` attaches to an arbitrary unpublished snapshot.
5. **Nothing tested or enriched.** The planned comparison test was never run. Real priors exist for only 6 classes, with no fitted weights.

### 3.4 · A scope question

- Going beyond 6 classes would reopen ruling 1, which made the 6-class run the product (ruling F-4).

---

## §4 · The links, and what they force

| Link | Consequence | Response |
|---|---|---|
| Gochara → Saṅgam, Kṣetra | Both pick up whichever Gochara generation is live on their next build. | Gochara settles first. Saṅgam and Kṣetra are rebuilt only on the new Gochara generation, after it is deployed and served. |
| L2 MSR writers → Saṅgam and six other tables (cascade delete) | Every L2 MSR rebuild deletes rows in `kala_convergence` (Saṅgam), `kala_darshana`, `kala_bhavishya`, `kala_activation`, `kala_obstruction`, `bodha_signal_embeddings` and `bodha_contradictions` (eight `ON DELETE CASCADE` keys, measured 2026-09-29); a restricting key would instead refuse the rebuild (R243). | F-3 **decided (N-32): all eight keys dropped** (target `no_fk`) and `assert_l2_msr_delete_safe` never refuses; the downstream is rebuilt in wave order; applied and proven (F3.FK, F3.GUARD, F3.PROOF) **before** Suvarṇa rebuilds any L2 MSR asset; wave 0 holds two. Details in §6. |
| `bo_upaya` → Kṣetra (phantom edge) | `bo_upaya`'s known failure would block Kṣetra for no reason. | Drop the edge. Fix `bo_upaya` anyway (N-6). |
| Kṣetra → Gochara windows (undeclared read) | The orchestrator cannot order builds correctly. | Declare it. |
| A Kṣetra change lived on the Gochara branch | Two workstreams edited the same writer. | Landed through PR #2731 (`285bff17c`); Kṣetra work starts from `main`. |
| W7 (Kṣetra) and Gochara's generation-and-switch pattern | Both need versioned "build the candidate, then switch authority" storage (the serving-guard pattern, N-33). | **Proposal:** design W7 by generalising Gochara's pattern rather than building a second one. This is an inference, to be tested in Track F's design step. |
| Gochara's output changes shape | Saṅgam and Kṣetra consume three objects (contacts, relationship records, evaluated windows) with frames, coverage and lineage. | Pravāha's consumer contract `…/pravaha/design/L3_FAMILY_COORDINATION_v1_0.md` is an input to both final briefs. |

---

## §5 · Track F — who does what (the regime in force)

**Gochara — the Pravāha campaign (verified 2026-09-30).** Pravāha owns Gochara end to end under its own authority
and its own log: it is not gated by J1, not bound by the Suvarṇa charter, and its production changes can happen while
Suvarṇa's waves run. Its final brief is its sealed v3.0 doctrine (D-BRIEF), which satisfies SEAL-G. Suvarṇa's part:
mapping that doctrine onto the nine gates (A.L3, its own work, never asked of Pravāha); never changing a Gochara asset
(charter R8 always covers Gochara); certifying what Pravāha builds (§7). Suvarṇa's Gochara items read Pravāha's tracker
through a `peer_tracker_item` detector: F1.G → B0.2; F2 keeps `pr_merged 2731`; F2.1 → J2; F2.3 → A1.2; F2.4 → A6.1
(gated on Pravāha's N-FLIP); F2.5 removed (N-SCOPE: no `1c826d5a` build); F3.G split into F3.Ga → A5.3, F3.Gb → A5.6,
F3.Gc → A6.2.

**Saṅgam and Kṣetra — Suvarṇa's Track F owns the design now (N-28).** No family session is known to exist: none has
acknowledged anything, and Pravāha has never been contacted by one. Architect-led Track F lanes write the two final
briefs on the tier-4 template (F1.S, F1.K), using the kept prompts `prompts/L3_SANGAM_FINAL_BRIEF_PROMPT_v1_0.md` and
`prompts/L3_KSHETRA_FINAL_BRIEF_PROMPT_v1_0.md` (v1.4) as lane briefs and Pravāha's consumer contract
`/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/L3_FAMILY_COORDINATION_v1_0.md` as an input; an
independent reviewer breaks each draft; Strategic Suvarṇa seals them (SEAL-S, SEAL-K). The prompts are used as session
prompts only if the native opens such a session.

- **Implementation ownership is decided at J1 (J1.FO, Strategic Suvarṇa):** if by J1 a family session has acknowledged
  the correction notice (FI-8) or shown commits on `sangam`/`kshetra` branches, that session owns implementation and
  charter R8 applies to it; otherwise the Suvarṇa swarm implements them as ordinary Track I/B work under the charter.
- **Until then R8 covers** Gochara (Pravāha) always, and Saṅgam or Kṣetra **only if** a family session has claimed it.
- **Each brief records the tier-4 template revision it follows** (the template changes at J1); A.L3r maps gate
  sections onto the re-sealed template.
- **Findings to Pravāha, or to a family session, go as reports, never instructions** (charter P11). The correction
  notice v1.3 (FI-8) is published on the campaign-coordination branch; FI-8 is no longer an N-1 prerequisite.

**The sequencing that still holds** (data dependencies):
- Gochara settles first: Saṅgam and Kṣetra are rebuilt only on `'5.0'`, after it is deployed and served (F2.4 → A6.1).
- Saṅgam's rebuild waits for its own `ka_yojaka` rebuild and for F-3's migration (F3.FK, F3.GUARD, F3.PROOF).
- Kṣetra's rebuild waits for W7 or the interim clear (F-1).

**History (v1.2–v1.3, N-17):** the three family sessions (L3 Gochara, L3 Saṅgam, L3 Kṣetra) were to own their families
end to end, with rulings and seals by the native. No Saṅgam or Kṣetra session materialised, and Gochara passed to
Pravāha; N-28 moved every campaign decision to Strategic Suvarṇa.

**History (v1.0–v1.1, superseded by N-17):** the earlier sequence had Suvarṇa run Track F itself: F0 contain (ask
Gochara for a deploy-before-switch gate; relay R240; agree a hand-over), F1 design in parallel, F2 Gochara to `main`,
F3 Saṅgam and Kṣetra to production, F4 enrichment, with F2 and F3 waiting for J1. F0's containment is done (F-0,
ADK-0027); the rest passed to the family sessions (N-17), then as above.

---

## §6 · Rulings Track F needs

Suvarṇa's decisions log: `$SUVARNA_HOME/authority/DECISIONS.jsonl` (N-37), written only by Strategic Suvarṇa. Under
N-28, F-1, F-2, F-4 and F-6 are decided by Strategic Suvarṇa on the owning session's recommendation, or, where no such
session exists (today, for both), from Track F's own design lanes. Pravāha's Gochara rulings live in Pravāha's log and
are cited, not re-recorded.

| ID | Ruling | Needed by | Researcher's view | Status |
|---|---|---|---|---|
| F-0 | Gochara: require a deploy-before-switch gate on the live workstream | **now** | — | **decided** 2026-09-28 (yes); in force as ADK-0027 |
| F-1 | Kṣetra: build W7 first, or an interim clear of ~11M rows (~6.7 GB) under a rebuild plan and a serving guard (N-29, N-33) | Kṣetra rebuild | W7 generalised from Gochara's pattern, if the design confirms it; the interim clear only if W7 slips | **open**: Strategic Suvarṇa decides from Track F's Kṣetra lane (or a Kṣetra session's recommendation) |
| F-2 | Saṅgam: elevate it, or retire it into `kala_field` (ŚAḌ-DARŚANA) | before Saṅgam design investment | Decide first; it changes what the design covers | **open**: Strategic Suvarṇa, from Track F's Saṅgam lane (or a Saṅgam session's recommendation) |
| F-3 | The L2↔L3 cascade lock | before wave 0 | Drop the keys; integrity checked by detector (D2) | **decided** (principle, N-28/N-29; concrete form **N-32**): see below. Gates every Suvarṇa wave with an L2 MSR writer, W0 included (F3.FK, F3.GUARD, F3.PROOF) |
| F-4 | Kṣetra: stay at 6 classes (ruling 1), or reopen it | enrichment | Stay at 6 until the 6-class field is correct, published and served | **open**: Strategic Suvarṇa, as F-1 |
| F-5 | Gochara: accept the 2020–2030 horizon, or require the century horizon before it counts as elevated | Gochara switch | The lane stops and asks only if it finds a prior ruling that narrowed it | **decided** (full century, by F-0) |
| F-6 | Saṅgam: the Mode D design (80% of rows, one set of windows repeated) | Saṅgam design | Decide with F-2 | **open**: Strategic Suvarṇa, as F-2 |

**F-3's concrete form (N-32).**

- **Migration** (Track E, Suvarṇa range 1200–1299; coordinated by lease note with whoever owns Saṅgam): `DROP
  CONSTRAINT` on all eight foreign keys into `bodha_msr_signals` (target `no_fk`: zero keys of any kind), and `CREATE OR
  REPLACE FUNCTION assert_l2_msr_delete_safe` without its refusal branch. It keeps the admitted-asset-context check and
  records referencing-row counts as build evidence; the replacement also removes the re-arm if a key is re-added.
- **Why it is safe:** signal ids are deterministic (`test_bo_*_signal_identity.py`,
  `test_bo_shared_msr_signal_identity.py`), so an unchanged signal keeps its id and its references. Changed or removed
  signals leave dangling references until the downstream asset rebuilds in its own wave; staleness propagation marks
  it, the serving guard covers the gap, and `msr_referential_integrity.py` measures dangling references after each wave.
- **Rejected alternative:** `ON DELETE SET NULL` on all eight. 4 of the 8 referencing columns are NOT NULL
  (`bodha_contradictions.signal_a_id`, `bodha_contradictions.signal_b_id`, `bodha_signal_embeddings.signal_id`,
  `kala_activation.signal_id`; measured 2026-09-30), and nulled references would be served as meaningless rows.
- **Transitive footprint** (measured 2026-09-30, `pg_constraint` closure; these keys stay): `kala_convergence` cascades
  into `kala_darshana`, `kala_obstruction` and `phala_anchors` (SET NULL into `kala_bhavishya`); `phala_anchors`
  cascades into `phala_pramana`, `phala_sankrama`, `phala_sodhana` and `phala_suddha_sodhana` (SET NULL into
  `phala_mitigation`, `phala_muhurta`). Every wave's impact statement lists its transitive footprint (E5.9), and the
  downstream is rebuilt in wave order. The family downstream (`kala_convergence`) is notified by lease note.
- **Acceptance:** F3.FK (no foreign key), F3.GUARD (the guard no longer refuses, with evidence), F3.PROOF (on the
  rehearsal database: an MSR writer's delete/reinsert with referencing rows present in all seven tables; no refusal;
  dangling count recorded; the downstream rebuild restores referential integrity).

---

## §7 · How Suvarṇa certifies the family assets (D2)

- **The Build exercise is the family's own orchestrator rebuild**, and counts only if it was an orchestrator run on the
  canonical chart (any `triggered_by`) whose substep plan completed. A hand-run cutover script does not count. Gochara
  today has no normal build path (§1.3 gap 2), so its registered writer (F3.Ga → Pravāha A5.3) must land first. **Pravāha
  has agreed: nothing is certifiable until the registered writer produces `'5.0'`.**
- **Suvarṇa's independent re-measure writes the certification** (plan items B.FG, B.FS, B.FK). That is Suvarṇa's
  ledger, not family build state, so charter R8 is not touched. The family's claims are evidence, not verdicts.
- **Waves do not wait for families.** The family set and its readers (16 readers measured: `ka_gochara`, `ka_kshetra`,
  `ka_sangam`, `ka_kalasutra`, `ka_taranga`, `ka_vighnakara`, `ka_kala_darshana`, `ka_bhavishya_lekha`,
  `ka_jivana_parva`, `ka_tulana`, `ph_nimitta`, `ph_muhurta`, `ph_pratikara`, `mi_bhara`, `mi_sankalpa`,
  `mi_adhilepa`) are frozen in `00_ARCHITECTURE/control/FAMILY_ASSETS.json` at J1 and excluded from wave completion. Each reader waits, asset by
  asset, for its family input to be certified (B.FR.L3, B.FR.L4, B.FR.L5).
- **Staleness is not a breach.** A Suvarṇa wave upstream with a real delta makes the orchestrator flip family assets to
  `stale`; charter R8 exempts that. The wave evidence records it and the owner (Pravāha, or a claiming family session)
  is told by lease note; the owner rebuilds.
- **Saṅgam is certified only after its L2 upstreams are certified** (B.W2). Once F-3's migration drops the keys
  (F3.FK), a later L2 rebuild no longer deletes its rows.
- **Brief seals.** A session's or lane's own `done` is not a seal: F1.S/F1.K close when Strategic Suvarṇa seals the
  brief (SEAL-S, SEAL-K; N-28). F1.G reads Pravāha's B0.2; SEAL-G is satisfied by D-BRIEF.
- **Currency.** Every certification records what it was measured against (job image tag, upstream certification ids,
  row-set fingerprint), so a later family change invalidates it (E5.5).
- **Hand-back.** When a family owner closes, Strategic Suvarṇa records HB-G, HB-S or HB-K: that family's assets leave
  the R8 set and become ordinary Suvarṇa assets, with the owner's rebuild runbook attached. Until then, a rebuild a
  family asset needs is parked to Strategic Suvarṇa by the Steward, with lead time.
- **Kṣetra is on the L5 critical path.** `mi_bhara` and `mi_sankalpa` read it, and Kṣetra is 5–9 weeks from a correct,
  published field. Strategic Suvarṇa either accepts that or dispositions those two readers `qualify` pending Kṣetra
  (N-21).
- **Risks carried:** family briefs sealed on the draft tier-4 template may need re-mapping after J1 (A.L3r); Kṣetra's
  wrong registry edges move the level map when fixed (snapshot at J1, re-derive per wave); the families can change
  production mid-wave, so the pre-wave fingerprint and the stale-certification detector are the tripwires.
