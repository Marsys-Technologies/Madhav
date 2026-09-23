---
artifact: L0_REPAIR_EXECUTION_PROMPT
canonical_id: L0_REPAIR_EXECUTION_PROMPT
version: "1.0"
status: AUTHORIZED
date: 2026-09-24
authorized_by: "Native (Abhisek Mohanty), 2026-09-24, verbatim: 'I authorize layer zero repair give me the prompt'"
scope: "The eight L0 items of KALA_DELEGATED_DECISIONS_v1_0.md D-E. No authority beyond them."
---

# L0 REPAIR SESSION — execution prompt

Paste everything below the line into a fresh Claude Code session.

---

You are the **L0 repair session**. The native has authorized exactly the eight items below and
nothing else. You are not an L3 stream and you do not touch L3 code.

## 0. First action, before anything else

Do not work in an existing checkout. Another session's worktree was silently shared last night and
four sessions' commits tangled. From the repo root `/Users/Dev/Vibe-Coding/Apps/Madhav`:

```
git worktree add /Users/Dev/madhav-l0/repair -b l0/vedha-and-frame-repair origin/main
cd /Users/Dev/madhav-l0/repair
git rev-parse --show-toplevel && git rev-parse --abbrev-ref HEAD
```

Print both. If the toplevel is not `/Users/Dev/madhav-l0/repair` or the branch is not
`l0/vedha-and-frame-repair`, **stop and report**. Re-assert both before every commit.

Never touch `/Users/Dev/madhav-l3/readiness`, `/Users/Dev/madhav-l3/kshetra-stage3`, or any
`gochara-*` worktree. Never commit to `sangam/stage3`, `l3/kshetra-*`, `l3/gochara-*`.

## 1. Read first

- `CLAUDE.md` (repo root) — §N.3 idempotency, §N.4 build principles, §N.8 earned signals.
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_DELEGATED_DECISIONS_v1_0.md` — D-E is your scope.
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_PRE_ELEVATION_CHECKLIST_v1_0.md` — §C is your list, §G is your discipline.
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md` — the row-level spec for item 2.

## 2. Your eight items

All paths are from the repo root and all have been verified to resolve.

**1. Re-cite 39 `bg_transit_rules` rows.** They carry `classical_citation = "BPHS Ch.29 (Gochara
Phala)"`. That chapter is *Bhāva Padas* and the citation is refuted. Their content is verbatim
Phaladīpikā Adhyāya XXVI ślokas 3–8 at `phaladeepika:PG322:C1`–`PG323:C1`. Re-cite **page-anchored**
(`verse_ref` in this corpus is page-based; "Phaladīpikā 23.11"-style refs do not resolve). Writer:
`platform/python-sidecar/pipeline/orchestrator/writers/bg_transit_rules.py`.

**2. Repair the Venus and Mercury rows.** Per the Kṣetra spec: UPDATE Venus rows 35/44/45 to 1/5/11.
**Never DELETE.** INSERT the missing Mercury 8→1 row. Four exceptions are declared there as a
precision limit — carry them, do not silently resolve them.

**3. Six Rāhu/Ketu vedha rows.** Disposition under N-14 (`GOCHARA_RULING_SHEET_v1_0.md` on
`origin/l3/gochara-elevation`): the instrument casts no graha-dṛṣṭi from the nodes. Read N-14
**together with N-5, N-6, N-6a and N-10**, not alone.

**4. Populate `bg_sarvatobhadra_grid`.** Table created by
`platform/supabase/migrations/529_bg_sarvatobhadra_grid.sql`; currently empty. Transcribe from
`phaladeepika:PG346:C1`–`PG352:C1` — a complete primary construction in legible prose: 81 squares
from ten lines each way, 16 vowels in the corner squares from the north-east, 28 asterisms from
Kṛttikā, tithis/rāśis/weekdays (PG346); malefic set and weekday/tithi groups (PG347); the
motion-dependent vedha direction, retrograde→right and Sun/Moon→left (PG348); the five-fold effect
scale (PG349); quarter effects (PG350–351); the sensitive-star set (PG352). **`PG345:C1` is the
diagram page and is OCR-noise — you do not need it.** **`PG332:C1` is a DIFFERENT chakra** (the
28-asterism ring for the Sun-vedha rule at śl. 26–27). Do not splice them. Land with the checkable
partition invariant migration 526's own docstring proposed.

**5. Pin the malefic scale.** Adhyāya XXVI carries **two** 1–5 scales: `PG349:C1` (agitation, fear,
loss, disease, death) and `PG353:C1` (fear, failure, killing, death, ignominy — the battle context).
`bg_vedha_malefic_scale` cites PG353. Make the row say which and why.

**6. Replace migration 624's node anchor.**
`platform/supabase/migrations/624_nirmana_l0_ephemeris_probe_contract.sql` asserts
`node_mode: "mean"` and anchors it at **sign** level. Both frames give the same sign at the forensic
instant (TRUE 50.049248°, MEAN 49.033044°, both Taurus, both Rohiṇī, differing only in pāda), so the
anchor **provably cannot fail**. Replace with a **degree-level** anchor: expected mean-node
longitude **49.033°** ± arcseconds at **JD 2445735.717361**. **624 IS APPLIED — never edit it.**
Write a NEW migration that supersedes it.

**7. Declare `ephemeris_daily`'s node frame and epoch.** The table stores the **TRUE** node under a
contract asserting mean, at a **noon-UT** epoch, and declares neither. Both must be declared on the
row. Reference: `platform/python-sidecar/brahmagyan/l0_ephemeris.py`.

**8. Correct the docstring in
`platform/python-sidecar/services/ka_vedha_gochara/logic.py`.** It states the ingested corpus holds
"BPHS, Jaimini Sutram, KP, and KP_Reader material only", that there is no Muhūrta Cintāmaṇi text,
that tier-(i) citation is unavailable for the SBC grid, and that this was "confirmed by direct
search, not assumed." Every load-bearing part is false: the corpus holds **15 populated texts**,
`muhurta_chintamani` has **274 chunks**, there is **no `kp`/`kp_reader` text_id at all**, and the
SBC **is** sourced (item 4). The defect is the parenthetical equating the ingested corpus with
`00_ARCHITECTURE/SOURCE_DATA/classical_texts/`, a source-data folder. That one sentence misled four
sessions for a day. Correct it and say what it actually checked.

## 3. Hard rules

- **Migrations: use 1075 or higher.** 1070–1074 are claimed by four unmerged branches. Author
  surgically, VERIFY it applied, and **never edit an applied migration** (§N.4).
- **L0 idempotency is `ON CONFLICT DO NOTHING` / `DO UPDATE`** — global reference tables (§N.3).
  Delete-then-insert is the L1+ rule and is wrong here.
- **Absence is established by `count(*)` against `classical_text_chunks`.** Never a directory
  listing, never the search tool (it ranked the load-bearing chunk 7th of 12 on a vedha query), never
  another artifact's assurance that it checked.
- **Assert the post-condition, not the exit code.** A `str.replace` that matches nothing still
  writes the file and still commits clean. `set -e` does not halt inside pipelines or command
  substitutions. Every edit ends with a check that the change is present.
- **Read the ruling set, not a ruling.**
- **Verification tiers come from `platform/python-sidecar/brahmagyan/verification_vocab.py` named
  constants, never string literals.**
- **Every status you emit needs a code path that could make it read false**, or it is null (§N.8).
- Both DB endpoints (`127.0.0.1:5433`, `:5434`) were refusing as of 2026-09-24. If they still are,
  stage the SQL, say so, and do not report staged work as applied.

## 4. Out of scope

Anything that changes what the instrument tells the native. Every item above is a citation, a
declaration, a repair to a known-wrong value, or a transcription from a cited primary. If an item
seems to require an interpretive judgement, stop and raise it.

You are also not authorized to edit `CLAUDE.md`, any governance register, any config, or any L3
stream's files. If you believe a governance register needs an entry, say so and let the register's
owner write it. A stage-3 executor appended to one last night without authority, and the content
was good but the scope was not.

## 5. Close

Open a PR from `l0/vedha-and-frame-repair` to `main`. Name an **independent reviewer who is not the
Saṅgam, Kṣetra or Gochara stream** — those three are conflicted, having produced the findings this
work rests on. Your close states, per item: what was applied, what was staged, and what a reader
would have to run to falsify it.
