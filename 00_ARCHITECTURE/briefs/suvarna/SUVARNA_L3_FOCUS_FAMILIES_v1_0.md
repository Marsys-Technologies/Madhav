---
artifact: SUVARNA_L3_FOCUS_FAMILIES
canonical_id: SUVARNA_L3_FOCUS_FAMILIES
version: "1.1"
status: DRAFT — for native review
produced_on: 2026-09-28
produced_in: session "Strategic Suvarṇa"
companion_of: SUVARNA_CAMPAIGN_PLAN_v1_2.md §5.3 (Track F)
evidence: >
  Three read-only reconciliations, 2026-09-28, each with a source for every claim:
  l3_recon/GOCHARA_RECON.md · l3_recon/KSHETRA_RECON.md · l3_recon/SANGAM_RECON.md.
  Figures below are theirs; effort figures are the researchers' estimates, in their own units.
changelog:
  - "1.1 (2026-09-29): Gochara brought up to date with the lane's ruling ADK-0027 (commit 33b725778). The lane switched the canonical chart to '4.0' at 19:22:58Z before F-0 arrived and reversed it at 19:29Z; '4.0' as a label is retired; F-0 is in force; the horizon default is now the full century (F-5 settled by F-0); §1.2 gains the seven-step standing sequence; Saṅgam and Kṣetra now wait on 'the new Gochara generation', not on '4.0'."
  - "1.0 (2026-09-28): first draft. Current state, target, gaps, effort and risk per family; the links between the three families; Track F's sequence; the rulings it needs."
---

# Suvarṇa — the L3 focus families: Gochara, Saṅgam, Kṣetra

## §0 · The picture in one page

**None of the three families is in a good state, and they depend on one another.**

| Family | What it is | State today, on the canonical chart `482012f1` |
|---|---|---|
| **Gochara** (transits) | Transit windows, vedha, resonance: when planets activate natal structure | Served generation `'3.0'` (914 rows, 1984–2084). The live workstream switched to `'4.0'` on 2026-09-28 at 19:22 UTC, found the serving code undeployed, and reversed it at 19:29 UTC. It now rebuilds on the full century under a new label, and switches only after PR #2731 is deployed (F-0). |
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
- **Saṅgam is locked to L2.** Its rows cascade-delete when `bo_laksana`'s signals are replaced. Once Saṅgam is rebuilt, the reverse happens: L2's replacement is refused (register R243).
- **Kṣetra's declared dependencies are wrong.** It declares `bo_upaya` and `bo_sangati` but never reads them, and reads about ten tables it never declares, including Gochara's windows. Through the phantom `bo_upaya` edge, `bo_upaya`'s known rebuild failure (R244) would mark Kṣetra BLOCKED.

**Effort to finish, as estimated by the researchers:**

| Family | To correct, and back in production | To "fully enriched" |
|---|---|---|
| Gochara (after the live workstream finishes, est. 2–5 days) | 12–25 agent-days | +30–55 agent-days |
| Saṅgam | 8–15 session-days | 33–60 session-days |
| Kṣetra | 5–9 weeks (a correct, published, served 6-class field) | 10–20+ weeks |

- These overlap and partly run in parallel. They are not a simple sum.
- **The longest pole is Kṣetra**, because nothing can reach its production data until W7 exists or you rule an interim clear.

---

## §1 · Gochara

### 1.1 · Inventory

- **Active:** `ka_gochara` (windows), `ka_gochara_resonance` (`gochara_resonance_map`), `ka_vedha_gochara` (`kala_vedha_gochara`).
- **Inactive:** `ka_gochara_v3_century_materialize` (the century writer, held and deactivated); `ka_gochara_sweep` (retired 2026-09-08).
- **L0 inputs:** `bg_gochara_arcs`, `bg_gochara_citation_resolution`.
- **Nirmāṇa "froze"** the three active assets; that is kept only as a starting point.

### 1.2 · The live workstream

- **Branch:** `l3/gochara-autonomous-wp0-7`. **PR #2731:** open, with merge conflicts.
- **Already in production:** guard triggers; migrations 1080–1084, 1087, 1091 and 1150; a registry re-pin; and a `'4.0'` candidate (138,837 contacts and 48 coverage rows per chart, unpublished).
- **One production write failed tonight** (23:27 IST, lost connection) while writing the first `'4.0'` windows.
- **What it will deliver:** `'4.0'` windows for 2020–2030, each citing its contact ids; authority switched on both charts after a 24-hour soak; the old `'2.0'` rows retired; eventually PR #2731 merged (kernel, vedha exceptions, serving code).
- ~~The switch is pre-authorized~~ **Superseded 2026-09-29 by F-0 (ADK-0027).**

**Update, 2026-09-29 (ADK-0027, commit `33b725778`):**
- **What happened.** The switch on chart `482012f1` ran at 19:22:58 UTC under the old authorization, before F-0 arrived. The lane traced the risk itself and reversed it at 19:29 UTC: authority back to `'3.0'`, 4,415 `'4.0'` windows deleted, integrity checks (a)–(k) green in both time zones, served output byte-identical to before. For those six minutes the hazard was live, but nothing consumed it: the Gochara session checked read-only and found no rows in `query_plan_log` or `audit_events` for 19:22–19:30 UTC, no MCP requests, and no reading, chat or transit requests to the web app. Chart `1c826d5a` was never switched.
- **`'4.0'` is retired as a label.** Both charts move to a new full-century generation under a new label.
- **Standing sequence (the lane's plan until the native rules otherwise):**
  1. rebuild the candidate on the full century, both charts, and re-run all evidence and gates;
  2. merge `main` into the branch (a merge commit) and build the readiness packet;
  3. report readiness to the native;
  4. the native merges PR #2731 and deploys;
  5. verify the running code from the service's `env.DEPLOY_SHA`;
  6. switch `482012f1`, with trigger #0 (served rows carry the new generation, or reverse at once), then soak;
  7. switch `1c826d5a`, then soak.

### 1.3 · Gaps that remain after the workstream finishes

1. **Serving code not deployed.** `main`'s forecast tools have no `'4.0'` branch. A switch before PR #2731 is deployed would serve `'4.0'` data under v1 provenance. **No deploy-before-switch gate was found** (the gap was real: see the §1.2 update; now closed by F-0).
2. **No normal build path.** The registered `ka_gochara` writer is unchanged and still writes the old `_v2` / `'2.0'` table. `'4.0'` comes only from hand-run cutover scripts, so no new chart can get it through the orchestrator.
3. **The horizon shrinks** from about 100 years to 10 (2020–2030). The plan's own example (a 2013 marriage) falls outside it. The researcher found no disclosure of this. (Now addressed: F-0 makes the full century the default.)
4. **The scoring loses variation.** In `'4.0'`, "promise" is 1.0 for all 27 classes; "permission" is a fixed value per class; the tārā factor is skipped; vedha data covers about 15 months of the 10 years.
5. **Designed fixes not yet in production:**
   - resonance fixes R-1 to R-6 (154 targets built on negative results, 54 dangling yoga targets, every row falsely marked "resolved");
   - overlays cover only about 460 days;
   - `main`'s writers would wipe the new stamp columns on any rebuild;
   - the bindu matrix and the Moon channel are not built.
6. **The registry mismatch (R240) has worsened.** The registry, `main`'s seed, the branch's seed and the registered writer now name different tables or generations. Migration 1150 did not touch it; it changed only an integrity check.

### 1.4 · Target ("fully enriched")

From the family's own design documents: a century-horizon, cited, orchestrator-built transit layer with a resolution hierarchy, vedha exceptions, resonance with honest resolution states, and full serving. Details in `l3_recon/GOCHARA_RECON.md` §5.

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
- **A Kṣetra writer change sits on the Gochara branch**, not on `main`. Its migration 1084 is already applied in production.

### 3.3 · Gaps

1. **No rebuild path.** W7, or your ruling for an interim archive-and-clear of about 11 million rows (about 6.7 GB). Until then no fix can reach production.
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
| `bo_laksana` → Saṅgam (cascade delete) | Every L2 re-elevation either wipes Saṅgam or is refused by it (R243). | A ruling or a foreign-key change **before** Suvarṇa rebuilds any L2 MSR signal asset (ruling F-3). |
| `bo_upaya` → Kṣetra (phantom edge) | `bo_upaya`'s known failure would block Kṣetra for no reason. | Drop the edge. Fix `bo_upaya` anyway (N-6). |
| Kṣetra → Gochara windows (undeclared read) | The orchestrator cannot order builds correctly. | Declare it. |
| A Kṣetra change lives on the Gochara branch | Two workstreams edit the same writer. | Land it through PR #2731, then Kṣetra work starts from `main`. |
| W7 (Kṣetra) and Gochara's generation-and-switch pattern | Both need versioned "build the candidate, then switch authority" storage. | **Proposal:** design W7 by generalising Gochara's pattern rather than building a second one. This is an inference, to be tested in Track F's design step. |

---

## §5 · Track F — the sequence

Hybrid, as in the rest of the plan: design runs in parallel now; production changes follow the data dependencies.

### F0 · Now (days) — contain and coordinate

- **Ask the Gochara workstream for a deploy-before-switch gate**, or confirmation of which code production serves. **Urgent**, because the switch is pre-authorized.
- Relay R240 and the worsened registry and seed mismatch to them.
- Agree the hand-over point: Suvarṇa leaves the family alone until the workstream finishes and PR #2731 merges.
  - No rebuild from `main` (it would erase stamps and invalidate the candidate).
  - No registry re-seed (it would re-arm the century writer).
- Take asset leases on Saṅgam and Kṣetra for design work only.

### F1 · Design, in parallel (starts now, read-only and fixtures only)

- **Gochara:** the orchestrator writer for the new generation; registry and seed alignment; the horizon question; the resonance fixes; overlays; the bindu matrix and Moon channel.
- **Saṅgam:** fix stage 3's defects on its branch (target point, `peak_date`, grouping key, CI), with tests that touch a real test database.
- **Kṣetra:** the stage-3 code fixes (axis, null scope, flag, L4 read, deterministic tables, dependency list); the W7 design, generalising Gochara's pattern.
- **All three:** their Nikaṣa asset briefs (Track A).

### F2 · Gochara to `main` (after the workstream finishes)

- Merge and deploy PR #2731; register the orchestrator writer; align the registry and seed; retire the century writer.
- Re-measure with Nikaṣa; certify what passes.

### F3 · Saṅgam and Kṣetra to production (after F2 and the rulings)

- **Saṅgam:** rebuild `ka_yojaka` first, then `ka_sangam` on the new Gochara generation. Only after ruling F-3 on the cascade lock.
- **Kṣetra:** W7 (or the interim clear, per ruling F-1), then rebuild on the new Gochara generation with the stage-3 fixes, then serving (`query_field_trajectory`).

### F4 · Enrichment

- Each family's documented "fully enriched" target, as its own packets, gated like everything else.

### Where Track F meets the rest of the plan

- F1 runs alongside Tracks E and A.
- F2 and F3 are production changes, so they wait for J1 (the engine freeze) like everything else. Their certifications follow the dependency waves.
- **F3 for Saṅgam also waits on L2's MSR assets** (the cascade lock). Track F and the L2 work in Tracks I/B must be sequenced together.

---

## §6 · Rulings Track F needs

| ID | Ruling | Needed by | Researcher's view |
|---|---|---|---|
| F-0 | Gochara: require a deploy-before-switch gate on the live workstream | **now** | **Decided 2026-09-28 (yes); in force as ADK-0027** |
| F-1 | Kṣetra: build W7 first, or authorize an interim archive-and-clear of ~11M rows (~6.7 GB, with a verified snapshot) | F3 | W7 generalised from Gochara's pattern, if the design confirms it; the interim clear only if W7 slips |
| F-2 | Saṅgam: elevate it, or retire it into `kala_field` (ŚAḌ-DARŚANA) | before F1 investment | Decide first; it changes what F1 designs |
| F-3 | The L2↔L3 cascade lock: foreign-key change, or a sequencing rule | before any L2 MSR rebuild | Needed by both Track F and the L2 work |
| F-4 | Kṣetra: stay at 6 classes (ruling 1), or reopen it | F4 | Stay at 6 until the 6-class field is correct, published and served |
| F-5 | Gochara: accept the 2020–2030 horizon for `'4.0'`, or require the century horizon before it counts as elevated | F2 | **Settled by F-0 (ADK-0027): full century is the default.** The lane stops and asks only if it finds a prior ruling that narrowed it |
| F-6 | Saṅgam: the Mode D design (80% of rows, one set of windows repeated) | F1 | Decide with F-2 |
