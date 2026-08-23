# M0-T71 — D-94's atomic C-28 fix, salvaged by the conductor after the KĀRAKA stalled

**KĀRAKA-M0-T71 stalled — `Agent stalled: no progress for 600s (stream watchdog did not recover)`
— after its own last message said the two target files were untouched by any concurrent commit and
it planned "one more full self-test + syntax pass" before writing its report and committing.**
It never wrote a report. This report is authored by SŪTRADHĀRA (the conductor) instead, describing
what the stalled agent's uncommitted work actually contains, on the ground that the substance was
complete and disclosing/committing it honestly beats discarding real, apparently-correct work or
leaving it orphaned uncommitted in the shared tree. **This is not a certification — I do not verify
my own dispatches' work any more than a KĀRAKA certifies its own (I16/H7 applies to the spirit of
the rule even though I am not the author) — PARĪKṢAKA must verify this in full, with no shortcut for
the unusual provenance.**

## What I verified before deciding to commit

- Both target files parse clean: `python3 -m py_compile` on `check_asset_catalogue_contract.py` and
  `m0_exit_scorecard.py` — no syntax errors.
- `check_asset_catalogue_contract.py --self-test` — **exit 0**, every fixture behaves as its
  `_expect` block declares, including the new "X-06 ratchet probe" section (empty floor / matching
  floor / mismatched floor / differential-preserved / no-DATA_KINDS-reference structural check).
- No `UPDATE`/`INSERT`/`DELETE`/`ALTER` anywhere in either diff — read-only against the database,
  consistent with I13/I14.
- `git status` confirmed no other agent's files were touched; the diff is scoped exactly to what the
  dispatch asked for plus the new floor artifact.
- I did **not** run `m0_exit_scorecard.py` itself against the live database — that requires
  `DATABASE_URL` and a real connection, and I judged that live-DB verification belongs to
  PARĪKṢAKA's independent pass, not to a salvage operation.

## What the diff contains (D-94's grant, part by part)

1. **`check_asset_catalogue_contract.py`** — new function `x06()`, the all-asset-kind unearned-lit
   ratchet: `asset_throughput.state='lit'` with zero completed `build_run_assets` rows, **no
   `asset_kind` predicate at all**, so a future category change cannot walk an asset out of it the
   way M0-T21's (correct) repair walked `bg_panchanga` out of the old `c28()`. Ratchet shape per
   D-95 (a floor, not `HEAD^`): population compared against a new committed artifact
   `platform/scripts/governance/unearned_lit_floor.json` (32 entries, itemised, generated from a
   live measurement at `2026-08-23T19:30:52Z`, never hand-typed). Blocks only on **growth** — a live
   unearned-lit asset_id not in the floor. The floor may only shrink, via a
   `--regenerate-unearned-lit-floor` flag that refuses to write if the new measurement is not a
   subset of the existing committed floor (D-96: no exemption path).
2. **`m0_exit_scorecard.py`** — `C-28` is now **imported** from `check_asset_catalogue_contract.py`'s
   `c28()` via `_c28_via_contract_module()` (an `importlib` load, matching an established
   cross-directory pattern already in this file), rather than a second hand-written SQL copy. A
   failure to import or to measure is reported `NOT_MEASURABLE`, never a silent skip.
3. **The differential survives as a test (D-94 part 8)**, per the self-test's "X-06 ratchet probe"
   section: the old unfiltered set is asserted equal to (narrowed-C-28 rows) ∪ (non-DATA_KINDS
   unearned-lit rows) — so a future silent divergence between the narrow and broad questions is
   caught even though the second hand-written production copy is gone.
4. **`bg_panchanga` is not repaired.** It is a named member of the seeded floor (R0 intake item),
   exactly as D-94 requires — asset build state stays untouched, R0 is shut, I13 binds.

## F-V67-1 — a disclosed gap this code does NOT close, found by PARĪKṢAKA while T71 was stalled

PARĪKṢAKA's V-67 (a queue-empty spot-audit, unrelated to T71 directly) found that `build_run_assets`
carries **four asset_ids absent from `asset_registry`** — one deleted (migration 342), one
**renamed** (`ka_gochara_v2_materialize` → `ka_gochara`, migration 563, with `complete` rows as
recent as 2026-08-10 under the **old** id), and two legacy ids. PARĪKṢAKA states plainly: *"C-28 as
committed is SAFE... But the unearned-lit ratchet must declare which side it anchors on, or its
population moves by up to 4 for reasons unrelated to what it measures."*

**I did not fix this.** It is not in D-94's grant, T71's stalled agent never saw it (V-67 landed
after T71 stalled), and PARIKSAKA has already routed the anchoring question to ADHIKĀRIN as a ruling
("how D-42's authority is operationalised is a ruling, not a measurement") rather than a KĀRAKA task.

**Why I judged this a disclose-and-ship rather than a hold, stated plainly so the judgment is
checkable:** `x06()` iterates `s.assets` (asset_registry rows) and only tests `aid not in ran` —
an orphan id in `ran` that never matches any registry row is harmless by construction. The live
failure mode is narrower than "the population moves by up to 4": it specifically requires a
**renamed** asset (`ka_gochara`) to currently read `lit` under its *new* id while its completed-build
evidence sits under the *old* id in `build_run_assets` — in which case `x06()` would wrongly count it
as growth. I did not verify live whether `ka_gochara` is currently `lit` (that is a live-DB read I
left to PARIKSAKA, per the same reasoning as above). **Before this code existed, `bg_panchanga`'s
unearned lit had zero coverage from any rule. This code, even with the disclosed gap, is a strict
improvement** — it could at worst produce one avoidable false-positive-growth entry for a named,
already-diagnosed reason, never a silent miss. That is why I am shipping it rather than holding it
on an open ruling question that PARIKSAKA already flagged for exactly this file before I ever wrote
this report.

**Routed:** PARIKSAKA's V-67 already reached ADHIKĀRIN on this. I am not re-routing; I am confirming
in this report that the disclosure reached the file this campaign will actually read when grading
T71, not only the verdict ledger.

## What I did not do

- Did not run `m0_exit_scorecard.py --live` or any live database check myself.
- Did not touch the anchor-side question F-V67-1 raises — ADHIKĀRIN's, per PARIKSAKA's own routing.
- Did not repair `bg_panchanga`, `ka_gochara`, or any asset-registry row.
- Did not touch Wave 2, the entrypoint guard, or anything M0-T70 built.

I certify nothing here (I16/H7). PARĪKṢAKA verifies, and should treat the unusual provenance
(conductor-salvaged, not self-reported by the implementing agent) as a reason for MORE scrutiny, not
less.
