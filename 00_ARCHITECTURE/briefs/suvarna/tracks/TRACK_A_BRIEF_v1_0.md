---
artifact: SUVARNA_TRACK_A_BRIEF
canonical_id: SUVARNA_TRACK_A_BRIEF
version: "1.1"
status: "DRAFT — for native approval with N-1"
produced_on: 2026-09-29
produced_in: "Strategic Suvarṇa"
session: "Exec Suvarṇa"
decision_owner: "Native (Abhisek Mohanty)"
plan_item: "L.11"
governed_by:
  - "SUVARNA_CAMPAIGN_PLAN_v1_4.md §1, §2, §5.2 (Track A), §5.3 (Track F), §5.4 step 1"
  - "SUVARNA_AUTONOMY_CHARTER_v1_0.md v1.4 (G3, G16 decided with N-1; R1, R5, R8, R9; P3, P6–P8, P11)"
  - "SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md v1.4 §3.3, §6, §12.6, §12.9, §12.13–§12.15"
  - "decisions N-17, D2, D3 ($SUVARNA_HOME/run/DECISIONS.jsonl)"
changelog:
  - "1.1 (2026-09-29, review pass 2 folded): the PROVISIONAL banner lifts at the layer's instance acceptance after revalidation (A.Lxa, N-10.Lx.i; L0 at N-7.L0 after A.L0v), which ends the circle with N-10's close; family evaluation is its own item A.L3f; dispositions use the tier-4 list only (keep with fix designs is keep; integrate and unresolved go to the native); Track I starts at N-24 on provisional approvals; census exit codes include 75; --assets once E1.9 lands; D6 applied; L2 instance records the measured cascade; findings folded."
  - "1.0 (2026-09-29): first issue. The three items per layer (instance, briefs, revalidation), the census rules, the tier-gap and harvest format, the brief, disposition and fix-design rules, L3 family evaluation, the asset-brief approval rule, output paths and the read-only write boundary."
---

# Track A brief — analysis, all six layers (session "Exec Suvarṇa")

This brief is the write boundary for every Track A packet. Track A is **read-only on production and writes documents
only**. It runs across L0–L5 at once from N-1, and feeds two things: the tier-gap harvest (A.H) into the combined
reopen at J1, and fix designs into Track I.

## §1 · Scope and done

| Plan item | Per layer | Done means (evidence the Scribe folds with) |
|---|---|---|
| **A.Lxi** | census (provisional) and layer-instance draft, tier gaps recorded | census JSON with exit code and inspector commit; instance draft and tier-gap file committed; gate ACCEPT |
| **A.Lx** | provisional asset briefs, dispositions, fix designs (L3: plus family evaluation) | one brief per in-scope asset, the dispositions table, every design marked tier-independent or tier-dependent; gate ACCEPT |
| **A.Lxr** | after J1.6: re-measure with the frozen inspector, revalidate every brief | certifying census gate-reviewed (arch §12.14); every brief bumped with a revalidation changelog line |
| **A.Lxa** (L1–L5) · **A.L0v** | the native accepts the revalidated layer instance (N-10.Lx.i); for L0, the instance revalidated against the re-sealed tiers before N-7.L0 (J1.5) | the decisions log; lifts the PROVISIONAL banner |
| **A.L3f** | evaluation of the family sessions' latest briefs and, after J1, their mapping onto the re-sealed tier-4 template (§6) | the evaluation files; gate ACCEPT |
| **A.H** | once all six A.Lxi are done | the harvest file, deduplicated and assigned to tiers; gate ACCEPT (high) |

- **A.H and J1 wait only for the six A.Lxi.** Briefs never hold up the harvest.
- **In scope:** 127 active assets. L0 40 · L1 19 · L2 23 · L3 21 (16 non-family briefs + 5 family assets evaluated,
  §6) · L4 9 · L5 15 (includes `lel_events`). Asset lists are read from `asset_registry` at census time, never copied.
- **Queue:** `QUEUE.jsonl`; queue ids `A.L2-brief-014` style (arch §12.2); lane branches `suvarna/lane/<qid>` from
  `suvarna/trunk`; worktrees `$SUVARNA_HOME/lanes/<qid>`.

## §2 · Write set and boundary

**May write (on lane branches, merged to `suvarna/trunk` after gate ACCEPT):**
- `00_ARCHITECTURE/briefs/suvarna/layers/<Lx>/**` — instances, tier gaps, briefs, dispositions, designs, family
  evaluations (paths in §8);
- `00_ARCHITECTURE/briefs/suvarna/layers/TIER_GAP_HARVEST_v1_0.md`;
- `00_ARCHITECTURE/briefs/suvarna/reviews/<qid>_REVIEW_<n>.md` (the gate reviewer's);
- `$SUVARNA_HOME/evidence/<qid>/**` — census output and scratch, not committed;
- fold requests `$SUVARNA_HOME/evidence/<qid>/FOLD_REQUEST.md` (arch §12.7) — never the fold itself.

**Must not touch (stop condition):** production data or schema by any path (P3); `--emit-gaps` or any ledger or
register line (the Scribe folds); code, writers, migrations, `asset_registry`, CI (Track I and E); tiers 1–4 and the
L0 instance v3.0 source (tier gaps are *recorded*, never *filled*); the family sessions' briefs, code and data (R8,
P11); the plan, plan model, charter, `CLAUDE.md`; `/Users/Dev/madhav-nikasha`, `/Users/Dev/madhav-engine` and the main
checkout (read only, via the census command); any chart but `482012f1-…` (R4); credentials (P1).

**Database access:** reads only, through `~/.config/suvarna/pgenv.sh` (`suvarna_reader`, D6 applied 2026-09-29), from the
census or `psql -X` in a subshell. No session-level `SET` that could lift read-only.

## §3 · The census (A.Lxi step 1; A.Lxr step 1)

- **One at a time, everywhere** (arch §3.3, §12.15), shared with the Nikaṣa Engine's E1 censuses and the family
  sessions:
  `python3 -m suvarna_tracker.census_lock --wait 900 --emit --actor analyst -- bash -c 'source ~/.config/suvarna/pgenv.sh && cd <checkout> && python3 platform/scripts/governance/asset_census.py --layer <Lx> --out $SUVARNA_HOME/evidence/<qid>/census_<Lx>.json'`.
  Exit 75 = the lock is held: wait or re-queue; never bypass.
- **Checkout** (arch §12.13): `/Users/Dev/madhav-nikasha` until E4.1 lands the inspector on `main`, then the
  `suvarna/trunk` worktree. Record the inspector's commit with the output.
- **Always `--out`** to the evidence folder (the default overwrites the committed `asset_census.json`). Never
  `--emit-gaps`.
- **Exit codes (arch §12.14):** 0 clean · 2 FAIL present · 3 PARTIAL/NO_DETECTOR/ERRORED present — all *measured*;
  4 unknown, 5 script error — the layer is **unmeasured**: report `failed`, do not work around it; 75 the census lock is
  held (re-queue).
- **Scope:** a whole layer here (A.Lxi). Once E1.9 lands `--assets`, level-wave re-measures census only their assets.
- **Gating:** provisional censuses (before J1) are checked by script — exit code, inspector commit, per-layer row
  counts. Certifying censuses (A.Lxr) get a gate review.
- **Order:** L0 (J1.5 needs the L0 instance), L1, L2, L4, L5, then L3 (`kala_field` ≈ 11 M rows, the slowest). The
  Conductor may interleave E1 census slots.

## §4 · Layer-instance draft and tier gaps (A.Lxi step 2)

- **Template:** tier 3 (`LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md`), inheriting tiers 1–2, filled from the tiers
  and the census only. **L0 starts from the v3.0 draft** (`MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md`,
  pending N-7.L0) and re-measures it; L1–L5 are first drafts.
- **Every clause the draft needs but the tiers do not supply is a tier gap**, never invented content. One row each in
  `<Lx>_TIER_GAPS_v1_0.md`: `TG-<Lx>-<nnn>` · the clause that failed to provide (file, section, line) · what the draft
  needed · evidence (census field, query, file) · the tier it belongs to · an existing register row if it duplicates
  one (then cite it, don't restate it). Gaps are written first so A.H is not delayed.
- **Layer specifics the draft must measure and record:**
  - L0: global scope; the other charts with L1+ rows (`1c826d5a`, `cb73cd3d`) named for N-12's input; `bg_vidhi_floors`
    DRAFT status; the Gochara L0 inputs flagged R9.
  - L1: the 8 `ga_*` call sites still timing through `ga_writers/_telemetry.py` (R34 residual) as an L1 gap.
  - **L2: the measured list of L2 MSR assets** (arch §12.9: writers whose rebuild replaces rows in
    `bodha_msr_signals`; seven by registry target today) and the cascade victims (eight `ON DELETE CASCADE` keys from
    seven tables, measured 2026-09-29), as the input to F-3 and F3.FK; R243's six chart-conditional PASSes carry their annotation;
    `bo_upaya` is Track E's (E4.2) — recorded, not redesigned.
  - L3: the family set and readers as found (the input to `FAMILY_ASSETS.json`, E6.3); Kṣetra's wrong edges noted.
  - L4: the three assets recording 139 rows written against 4 present.
  - L5: `lel_events` has no writer (R236, for N-14); calibration fills over time by design.

## §5 · Asset briefs, dispositions, fix designs (A.Lx)

- **Template:** tier 4, `ASSET_ELEVATION_TEMPLATE_v2_0.md` (draft, N-7.T4 pending). Every brief records the template's
  revision (the file's commit on its source branch) in its frontmatter and carries the banner **PROVISIONAL — until
  J1; may register gaps, may not certify** (tier-4 PILOT clause). The five L0 pilot briefs are worked examples of the
  shape, not inputs to copy.
- **Each brief:** §0 identity and the thirteen inherited rows · §1 measured state (census run id, never a typed
  figure) · §3 obligations · §4 the nine gates with the current verdicts from the census · §5 the gap rows it relies
  on, cited by ledger `gap_id` (`measured … / required …`, detector, population) · §6 change packet = its fix designs
  · §9 opportunities (`kind: opportunity`, never blocking). Non-gate criteria (Cost, Count, Complete, Reach) appear as
  information, never as blockers (D3).
- **Proposed additions** (plan §2.3): the requirement, its detector, why this asset. A class the native has not
  approved is marked `proposed — N-11 pending`; L2 briefs must not be approved while N-11 is open for a class they use.
  "Null with a reason" is already a decided class (D3), adopted per asset here.
- **Per-asset semantic detectors** (plan §2.1; D3 §5) are designed here as fix designs: Carr.D1 carriage for L0
  reference assets, Narr golden tests per narration writer, declared null reasons. They gate that asset's ELEVATED;
  they are not J1 inputs.
- **Disposition** from the tier-4 list: keep · integrate · enrich · qualify · consolidate · historical · retire ·
  unresolved. A kept asset with fix designs is `keep`; there is no "fix" disposition (plan §1.1(4)). Retire,
  consolidate, historical, integrate, unresolved or any output change is a proposal the Steward parks for the native
  (R5).
- **Fix design** (`designs/<ASSET_ID>_FIX_DESIGN_v1_0.md`): the gap rows it answers and the gate; the `write_set`
  (files, tables, migrations, registry rows); whether output changes; the failing-first test and its mutation; leases
  needed; **tier-independent** (buildable before J1: needs no clause the reopen may change) or **tier-dependent**
  (names the agenda row it waits for); anything needing a `WriterBase` change is raised to the Steward (R2), not
  designed around.

## §6 · L3 and the family sessions (charter R8, P11; plan §5.3)

- The family set (until `FAMILY_ASSETS.json` freezes at J1): `ka_gochara`, `ka_gochara_resonance`, `ka_vedha_gochara`,
  `ka_sangam`, `ka_kshetra` and its tables, plus any prerequisite a family brief claims (e.g. `ka_yojaka`; if claimed,
  it moves from the 16 briefs to evaluation).
- **Suvarṇa writes no brief and no fix design for a family asset.** A.L3 **evaluates the family sessions' latest
  briefs** (sealed or draft, the version and template revision recorded) and re-measures their assets with the
  inspector: `layers/L3/family/<GOCHARA|SANGAM|KSHETRA>_EVALUATION_v<n>.md`. Their claims are evidence, not verdicts.
- Readers of family assets get normal briefs, with the family input named and the D2 wait recorded
  (`waiting_on_family`); `mi_bhara` and `mi_sankalpa` carry the N-21 choice.
- The evaluation is its own item, **A.L3f**, **off the J1 path**, and may run any time after A.L3i; B.FG, B.FS and
  B.FK wait for it. It is a report: the Steward files it as a
  tracker note and Strategic Suvarṇa relays it; nobody in Exec Suvarṇa writes to a family session (P11).
- A.L3f also maps the family briefs onto the post-J1 tier-4 template after J1 (they were sealed on the draft).

## §7 · The harvest (A.H)

`layers/TIER_GAP_HARVEST_v1_0.md`: every `TG-*` row from the six layers, deduplicated across layers and against the
register and the E2.1 agendas, each assigned to T1, T2, T3 or T4 with the clause and a proposed remedy (never the final
text). The Nikaṣa Engine's E2 folds it into the combined agendas; Strategic Suvarṇa presents them (N-4.Tx). Once an
agenda opens it is closed: later gaps go to a second-round list in the same file. Gate review at high effort.

## §8 · Output paths (arch §12.6)

| Output | Path under `00_ARCHITECTURE/briefs/suvarna/layers/` |
|---|---|
| Layer instance | `<Lx>/<Lx>_LAYER_INSTANCE_v1_0.md` (L0: `L0/L0_LAYER_INSTANCE_v3_1.md`, continuing v3.0) |
| Tier gaps | `<Lx>/<Lx>_TIER_GAPS_v1_0.md` |
| Asset brief | `<Lx>/assets/<ASSET_ID>_ELEVATION_BRIEF_v1_0.md` (revalidation bumps to v1.1) |
| Dispositions | `<Lx>/<Lx>_DISPOSITIONS_v1_0.md` |
| Fix designs | `<Lx>/designs/<ASSET_ID>_FIX_DESIGN_v1_0.md` |
| Family evaluations | `L3/family/<FAMILY>_EVALUATION_v<n>.md` |
| Harvest | `TIER_GAP_HARVEST_v1_0.md` |

Every document carries frontmatter (artifact, version, status, produced_on, produced_in "Exec Suvarṇa", the census
run id and inspector commit it rests on, changelog).

## §9 · Revalidation after J1 (A.Lxr)

Re-census with the frozen inspector (certifying, gate-reviewed); re-read every brief against the re-sealed tiers, the
frozen registry (E6 applicability and N/A rules), the accepted tier 4 and the J1 level map; update gap citations,
gate verdicts and designs (a tier-dependent design is rewritten or confirmed against the sealed clause); bump the
version with a changelog line saying what changed, or "revalidated, no change". The Steward then requests the
layer's instance acceptance (A.Lxa, N-10.Lx.i; L0 via A.L0v and N-7.L0), batched; the PROVISIONAL banner is removed
when the log records it. That acceptance comes before the layer's first wave; the layer close (N-10.Lx.c) comes after.

## §10 · Who approves an asset brief (plan §5.4 step 1)

| Brief | Approver |
|---|---|
| Disposition keep (with or without fix designs), enrich or qualify, every addition in a class the native approved (N-11) | **Steward**, under G16 — **only once the native approves G16 (with N-1)**; until then the native |
| Retire, consolidate, historical, integrate, unresolved; any output change (R5); any addition outside an approved class | **native**, batched per layer |

- **When:** after the gate reviewer's ACCEPT. The Steward requests native approvals per layer, batched, with lead time
  (charter §7), each with its recommendation.
- **Provisional approval (before J1)** covers only the brief's **tier-independent** designs, so Track I may start them
  (Track I starts at N-24, before J1, lane to trunk only; plan §5.4); it never certifies anything. **Full approval** follows A.Lxr: a revalidation that changes the
  disposition, an addition or an output needs re-approval by the same rule; "no change" is confirmed by the approver
  who approved it.
- A gate reviewer accepts or rejects a brief's quality; it never approves it and never authors a PASS or an N/A (D3).

## §11 · Reviews, roles, estimates

- **Roles:** Analysts (Sonnet 5, medium; up to 6) write; the Architect (Opus 5.5, high) takes the derivability
  mechanisms behind tier gaps and any design needing algorithm judgement; gate reviewers (Opus 5.5; medium, **high**
  for instances, the harvest and designs touching writers or ledgers); the Scribe folds; the Steward parks R1/R5/R8/R11
  items and runs the approval requests.
- **Estimates (plan §5.2, §6.6):** instance drafts and derivability ≈ 157 h (the register's P9 primaries) · briefs
  ≈ 122 × 1–2 h ≈ 130–250 h · revalidation 30–65 h · semantic-detector designs, a share of 60–180 h (with Track I).
  L0 is measured first; the Conductor re-estimates after L0's A.L0 closes and reports the change against plan §10's
  trigger (a miss by more than half).
- **Findings for Strategic Suvarṇa:** all folded (exit codes; the Exec start prompt; the "fix" disposition). None open.
