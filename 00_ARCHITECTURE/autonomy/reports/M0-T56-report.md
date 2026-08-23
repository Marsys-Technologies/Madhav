# KĀRAKA-M0-T56 — report to PARĪKṢAKA

**Task:** M0-T56, paired per D-61 part 9. (1) F-G — the authority check authenticates the
AUTHOR, not the AUTHORISATION. (2) SQ-11 — pin C-28's population so V-27's trap cannot be
sprung politely.
**Agent:** KARAKA-M0-T56 · **Branch:** campaign/nirmana-autonomous · shared tree
**Files changed:** `platform/scripts/governance/check_asset_catalogue_contract.py` — ONLY.
**Commits (D-61 part 9's condition, in order, with a guard run recorded between them):**

| # | sha | what |
|---|---|---|
| 1 | `809b8eb25` | F-G + the stale-comment sweep SŪTRADHĀRA routed mid-task |
| 2 | `09a1600bd` | SQ-11 |

A sibling (SŪTRADHĀRA, `17ae9f68b` / `50e8e0a40`) committed between mine; both of mine are
ancestors of HEAD and neither touched a file the other did. Both commits used
`git commit --only <explicit file path>`, never a directory.

**I certify nothing (I16/H7).** Everything below is an observation with the command that
produced it.

---

## Baseline (R2, before any edit)

- HEAD at start `2c04409e0`, branch `campaign/nirmana-autonomous`.
- `git rev-parse HEAD:platform/scripts/.../check_asset_catalogue_contract.py` =
  `6f0ab3fe1aa6e65bd2725e714f7147d9a21355f9`; working-file sha256
  `e33ae828e3fd11f798bb492529e8c339e295f08be5d13a05e99e92a6cc37e591`;
  `git diff HEAD -- <file>` EMPTY. So the baseline was HEAD's blob, not a sibling's
  in-flight state. The temp copy I later extracted from that blob hashed to the same
  `e33ae828…`, which is the independent confirmation.
- BEFORE runs: `--self-test` exit 0; `--live` exit 0;
  `pass=13 fail=16 not_checkable=4`, blocking `[]`, rung `[]`,
  `disclosed_non_gating` = 15 rules, total violation rows 110. Identical to what M0-T51
  recorded, so nothing had moved under me.

---

## PART 1 — F-G

### What I changed (three functions)

1. **`decision_index()`** now retains `authorised_covers` from each ledger line. It
   previously kept only `agent`/`power`/`ts` and discarded the body, which is what made
   the check *structurally* incapable of asking whether a decision authorises anything
   (D-61 evidence line 3).
2. **`decision_grant(auth, rid)`** — NEW. Resolves what a decision authorises **for a rule
   id**, and returns `None` + a reason on every gap: no `authorised_covers` field, no
   entry keyed by that rule, no `covers` list. Keyed by the RULE ID (`C-28`), not the
   disclosure entry's own key (`C-28_residual`), which matters because the shipped file
   uses a different key for that one entry.
3. **`apply_rule_disclosures()`** — after the existing exists/ADHIKĀRIN conjuncts, the
   entry's `covers` must now be a **SUBSET** of the grant. Any identity outside it ⇒ no
   demotion, rule gates at declared severity, with the offending identities named in the
   note.

### Proof it refuses — ADHIKĀRIN's three probes, reproduced BEFORE and AFTER

Run through the guard's own `_RULE_DISCLOSURE_DOC` injection point, shipped residuals file
untouched, HEAD blob and my change side by side (driver in the session scratchpad;
`fg_probe.py`). Verbatim:

```
================ BEFORE (HEAD blob 6f0ab3fe) ================
  CONTROL  authorised_by=D-54 (real grant, covers=['lel_events'])
      ACCEPTED -> DISCLOSED_NON_GATING   (C-01 in blocking_failures: False)
  F-G      authorised_by=D-1  (real ADHIKARIN ruling about heartbeat.sh)
      ACCEPTED -> DISCLOSED_NON_GATING   (C-01 in blocking_failures: False)
  F-G ext  authorised_by=D-1  + INVENTED WIDER covers
      ACCEPTED -> DISCLOSED_NON_GATING   (C-01 in blocking_failures: False)
  F-G 4th  authorised_by=D-60 (the stall-detector ruling)
      ACCEPTED -> DISCLOSED_NON_GATING   (C-01 in blocking_failures: False)

================ AFTER (working tree, M0-T56) ================
  CONTROL  authorised_by=D-54 (real grant, covers=['lel_events'])
      ACCEPTED -> DISCLOSED_NON_GATING   (C-01 in blocking_failures: False)
  F-G      authorised_by=D-1  (real ADHIKARIN ruling about heartbeat.sh)
      REFUSED  -> gates at BLOCKING   (C-01 in blocking_failures: True)
        note: C-01: claims non_gating under 'D-1', which carries no `authorised_covers`
        field — a decision authorises a demotion in a machine-readable field or it
        authorises nothing, whatever its prose says (D-61 part 6) — no effect
  F-G ext  authorised_by=D-1  + INVENTED WIDER covers
      REFUSED  -> gates at BLOCKING   (C-01 in blocking_failures: True)
  F-G 4th  authorised_by=D-60 (the stall-detector ruling)
      REFUSED  -> gates at BLOCKING   (C-01 in blocking_failures: True)
```

All four ACCEPTED before, exactly as D-61 part 1 reported. After: the control still
ACCEPTED, the three attacks REFUSED and gating.

**The SUBSET conjunct, isolated** — because the three above all refuse at the *first* new
gap ("no `authorised_covers`"), which would leave the subset rule itself unproven. A real
grant (D-54, `C-01 → ['lel_events']`) with a hand-widened `covers`:

```
=== SUBSET CONJUNCT, BEFORE ===
  D-54, covers EXACTLY its grant ['lel_events']                     -> DISCLOSED_NON_GATING
  D-54, covers WIDENED by hand to include bg_reference              -> DISCLOSED_NON_GATING
=== SUBSET CONJUNCT, AFTER ===
  D-54, covers EXACTLY its grant ['lel_events']                     -> DISCLOSED_NON_GATING
  D-54, covers WIDENED by hand to include bg_reference              -> BLOCKING
        note: … 1 of them are OUTSIDE what that decision authorises for C-01
        ['bg_reference'] … A `covers` list wider than its grant PRE-AUTHORISES a future
        violation (D-54 part 5(a)); the subset rule is what makes that a detector
        instead of an honour system
```

### D-61 part 5's condition — the shipped fifteen

**All 15 still demote. Nothing was widened, nothing relaxed.**
`--live` after the fix is identical to before, rule for rule: I diffed
`(status, effective_severity, violation_count)` for all 33 rules and the answer was
`per-rule differences before->after: NONE`. Summary unchanged: `pass=13 fail=16
not_checkable=4`, blocking `[]`, rung `[]`, 15 `DISCLOSED_NON_GATING`, 110 violation rows,
exit 0.

I also made that a **detector rather than a claim in this report**: new self-test case 7b
walks the shipped file and asserts every demoting entry is inside its cited decision's
grant, DB-free. It prints
`[OK  ] all 15 shipped demotion(s) are inside the authorised_covers grant of the decision
they cite`, and if one ever is not it prints the refusal reason and says in the output
that this is a finding to report, never a reason to widen a grant.

### The probe's own positive case was part of the defect

`rule_disclosure_probe()` selected its authority as `sorted(adhikarin)[0]` = **D-1**, and
passed. It now selects, programmatically, a decision that actually grants C-01 for an
identity C-01 would flag (resolves to D-54 → `lel_events`), so the positive case exercises
a real warrant end to end. New cases 8–12: the three ADHIKĀRIN probes as must-refuse; a
grant keyed to another rule (C-04, not C-01) as must-refuse; and a **positive control**
proving the rule is `covers ⊆ grant` and not `covers == grant`, so the refusals are not
passing merely because everything now refuses.

---

## THE GUARD RUN BETWEEN THE TWO COMMITS (D-61 part 9)

At `HEAD = 809b8eb257d34daf7dcc229100ec225f33514b59`, file sha256
`da6e606a6bc8eba4bde35d404870ff265161cdb2fffc56497c0006efb04af2ab`, `2026-08-23T15:25:13Z`.
`python3 platform/scripts/governance/check_asset_catalogue_contract.py --self-test`,
verbatim:

```
contract cross-check OK — 28 rules parsed from 00_ARCHITECTURE/control/ASSET_CATALOGUE_CONTRACT_v1_0.md, all implemented, severities agree, and every rule the document marks not checkable is hard-wired NOT_CHECKABLE here.
  [FIXTURE OK  ] fail/catalogue__post590_violations.json — 33 expectations met (pass=24 fail=6 not_checkable=3)
  [FIXTURE OK  ] fail/catalogue__pre590_violations.json — 33 expectations met (pass=0 fail=24 not_checkable=9)
  [FIXTURE OK  ] pass/catalogue__clean_post590.json — 33 expectations met (pass=29 fail=0 not_checkable=4)
  [FIXTURE OK  ] pass/catalogue__clean_pre590.json — 33 expectations met (pass=24 fail=0 not_checkable=9)

  C-23 code-derivation probe (the truth is parsed from the writer classes, not read from a file):
      derived from source: 579 files, 123 @register decorators, 26 heavy / 97 light
      probe assets: heavy=bg_gochara_arcs  light=bg_class_lifetime_counts
      [OK  ] registry agrees with the writer classes: status=pass violations=0 classes={} declared_stale=None
      [OK  ] registry drifted AND the declared map is stale in the same direction (the old guard's blind spot): status=fail violations=2 classes={'false_negative': 1, 'false_positive': 1} declared_stale=2
      [OK  ] registry drifted, no declared map present: status=fail violations=2 classes={'false_negative': 1, 'false_positive': 1} declared_stale=None
      [OK  ] derivation unavailable ⇒ null, never a fallback to the declared map: status=not_checkable violations=0 classes=None declared_stale=None

  Rule-disclosure probe (severity is computed from the disclosure, and a disclosure can only demote what its own cited decision authorises):
      authority ledger: 64 decisions, 63 by ADHIKĀRIN, 62 of those carrying no `authorised_covers` at all
      probe cites D-54 (grants C-01 → 'lel_events'); un-authorising controls: D-1, D-60
      [OK  ] no disclosure ⇒ both BLOCKING rules gate
           got {'c01_status': 'fail', 'c01_violations': 1, 'c01_effective': 'BLOCKING', 'c01_gates': True, 'c05_gates': True}
      [OK  ] authorised + itemised + fully covering + inside the cited decision's own grant ⇒ C-01 reported, non-gating; C-05 STILL GATES
           got {'c01_status': 'fail', 'c01_violations': 1, 'c01_effective': 'DISCLOSED_NON_GATING', 'c01_gates': False, 'c05_gates': True}
      [OK  ] a violation outside `covers` ⇒ the rule gates again at BLOCKING
           got {'c01_status': 'fail', 'c01_violations': 2, 'c01_effective': 'BLOCKING', 'c01_gates': True, 'c05_gates': True}
      [OK  ] authorised_by names a decision that does not exist ⇒ no effect
           got {'c01_status': 'fail', 'c01_violations': 1, 'c01_effective': 'BLOCKING', 'c01_gates': True, 'c05_gates': True}
      [OK  ] authorised_by names a real but non-ADHIKĀRIN line (D-PROBE-NOT-ADHIKARIN, agent=KARAKA) ⇒ no effect — even carrying a perfectly-formed grant
           got {'c01_status': 'fail', 'c01_violations': 1, 'c01_effective': 'BLOCKING', 'c01_gates': True, 'c05_gates': True}
      [OK  ] ledger's own non-ADHIKĀRIN line (D-NATIVE-01) ⇒ no effect
           got {'c01_status': 'fail', 'c01_violations': 1, 'c01_effective': 'BLOCKING', 'c01_gates': True, 'c05_gates': True}
      [OK  ] gating_effect='non_gating' with no `covers` ⇒ GuardError (rule disclosure 'C-01' claims gating_effect='non_gating' but…)
      ── F-G (D-61): the cited decision must itself authorise the rule ──
      [OK  ] authorised_by names a real ADHIKĀRIN ruling that authorises nothing (D-1, no `authorised_covers`) ⇒ REFUSED
           got {'c01_status': 'fail', 'c01_violations': 1, 'c01_effective': 'BLOCKING', 'c01_gates': True, 'c05_gates': True}
      [OK  ] …the same ruling with an INVENTED, WIDER `covers` list ⇒ REFUSED (the list is no longer self-asserted)
           got {'c01_status': 'fail', 'c01_violations': 1, 'c01_effective': 'BLOCKING', 'c01_gates': True, 'c05_gates': True}
      [OK  ] a second unrelated ADHIKĀRIN ruling (D-60) ⇒ REFUSED
           got {'c01_status': 'fail', 'c01_violations': 1, 'c01_effective': 'BLOCKING', 'c01_gates': True, 'c05_gates': True}
      [OK  ] ADHIKĀRIN grant exists but is keyed to another rule (C-04, not C-01) ⇒ REFUSED
           got {'c01_status': 'fail', 'c01_violations': 1, 'c01_effective': 'BLOCKING', 'c01_gates': True, 'c05_gates': True}
      [OK  ] grant is WIDER than the entry's `covers` ⇒ still demotes (subset, not equality)
           got {'c01_status': 'fail', 'c01_violations': 1, 'c01_effective': 'DISCLOSED_NON_GATING', 'c01_gates': False, 'c05_gates': True}
      [OK  ] shipped asset_catalogue_disclosed_residuals.json: 19 rule disclosure(s) over 19 rule(s) parse and validate; claiming a gating effect: ['C-01', 'C-02', 'C-03', 'C-04', 'C-06', 'C-07', 'C-08', 'C-11', 'C-15', 'C-17', 'C-20', 'C-21', 'C-28', 'X-03', 'X-05']
      [OK  ] all 15 shipped demotion(s) are inside the `authorised_covers` grant of the decision they cite

  Snapshot-freshness probe (the age of the data a gate judges is itself measured, and an unmeasurable age is not a young age):
      migrations declare ['data_disposition', 'dead_flag', 'domain', 'natural_key_partition', 'rung', 'superseded_by'] on asset_registry (590_nirmana_m0_catalogue_contract_columns.sql, 591_nirmana_m0_partition_and_dead_flag_columns.sql)
      [OK  ] fresh snapshot, schema current ⇒ not stale: {'stale': False, 'age_exceeded': False, 'schema_behind_columns': []}
      [OK  ] 100h old ⇒ stale on age: {'stale': True, 'age_exceeded': True}
      [OK  ] fresh but missing migration-declared column `data_disposition` ⇒ stale on schema: {'stale': True, 'age_exceeded': False, 'schema_behind_columns': ['data_disposition']}
      [OK  ] no `_meta.read_at` at all ⇒ stale (an unmeasurable age is not a young age): {'stale': True}
      [OK  ] unparseable `_meta.read_at` ⇒ stale: {'stale': True}
      [OK  ] live mode is measured but never enforced on age: {'stale': True, 'enforced': False}
      shipped baseline asset_catalogue_baseline_20260823.json: stale=True age_hours=10.266 schema_behind=['data_disposition', 'dead_flag', 'domain', 'natural_key_partition', 'rung', 'superseded_by']
          · the snapshot is missing column(s) ['data_disposition', 'dead_flag', 'domain', 'natural_key_partition', 'rung', 'superseded_by'] that a migration in THIS checkout adds to asset_registry (590_nirmana_m0_catalogue_contract_columns.sql, 591_nirmana_m0_partition_and_dead_flag_columns.sql) — the snapshot provably predates a schema change that is already in the repo

self-test OK — every fixture behaved exactly as its _expect block declares, including every fixture built to make a rule FAIL, and C-23's code-derived truth was proved to fail on a divergence its declared map calls clean.
EXIT=0
```

And `--live` at the same commit: **exit 0**, summary tail verbatim:

```
  pass=13  fail=16  not_checkable=4
  BLOCKING failures : none
  RUNG failures     : none
  RESIDUAL failures : ['X-02'] (non-gating by construction — see X-02)
  ADVISORY failures : none
  DISCLOSED non-gating failures : ['C-01', 'C-02', 'C-03', 'C-04', 'C-06', 'C-07', 'C-08', 'C-11', 'C-15', 'C-17', 'C-20', 'C-21', 'C-28', 'X-03', 'X-05'] (…)
  not_checkable     : ['C-22', 'C-25', 'C-26', 'C-27']
  failing rules WITHOUT a disclosure entry : ['X-02']
  disclosures recorded but with NO gating effect : ['C-22', 'C-25', 'C-26', 'C-27']
```

---

## PART 2 — SQ-11

**`c28` itself is UNCHANGED.** The diff for commit 2 is `167 insertions(+), 0 deletions`.
I built the guard against the re-pointing; I did not perform it (D-43 part 6 = H3).

New `c28_population_probe()`, wired into `--self-test`. Four parts, following the
campaign's standing mutation-proof doctrine (D-41):

1. **behavioural positive** — a synthetic registry where 4 assets claim a built state and
   only 2 are witnessed by a run; the shipped rule must return exactly
   `['bg_probe_unwitnessed']` (V-27's Class A: `lit`, no estimate, no run record at all);
2. **paired negatives** — has an estimate / never `lit` / `service` kind (V-22's
   `bg_panchanga` case) must NOT fire, so part 1 cannot be satisfied by a rule that flags
   everything;
3. **seeded defect** — the re-pointed rule is BUILT INSIDE THE PROBE and run over the SAME
   snapshot. It must return **0**. The snapshot carries a `build_run_assets` section
   populated the way production's is — rows for the assets that DID run, and therefore
   structurally none for the asset whose missing run is the defect. This re-measures V-27
   rather than citing it, and it is what makes part 1 capable of going red;
4. **structural over `c28`'s own source** — the population loop must iterate `s.assets`,
   and `c28` must contain no `build_run*` reference at all; the same assertion is applied
   to the seeded-defect function as a **paired positive**, so a clean structural result is
   a measurement rather than a vacuously satisfied one.

Output at HEAD:

```
  C-28 population probe (SQ-11: the rule enumerates the assets CLAIMING a built state and joins OUTWARD to find absence):
      [OK  ] shipped C-28 over a registry claiming 4 assets built / 2 witnessed by a run: status=fail violations=['bg_probe_unwitnessed']
      [OK  ] the SAME snapshot through a C-28 re-pointed at build_run_assets: status=pass violations=0 — V-27's measurement reproduced; the defect vanishes and the gate would pass
      [OK  ] structural: c28 iterates `s.assets` and contains no reference to a run table
      [OK  ] structural, paired positive: the same assertion applied to the seeded defect reports 2 problem(s) — so a clean result above is a measurement, not a vacuous one
```

### Proof the SQ-11 fixture CAN fail — two mutations, in isolated copies

The shipped tree was never mutated. Each mutation was applied to a **copy** of the working
file in the session scratchpad, at equal repo depth with the guard's inputs symlinked, and
run there with absolute paths (R1/R2/R7). Shipped file sha256 re-checked afterwards and
`git status` showed only my own intended modification.

**Mutation A — the trap itself** (`c28`'s body re-pointed to enumerate from
`build_run_assets`):

```
      [BAD ] shipped C-28 over a registry claiming 4 assets built / 2 witnessed by a run: status=pass violations=[]
           expected status=fail violations=['bg_probe_unwitnessed'] — …
      [OK  ] the SAME snapshot through a C-28 re-pointed at build_run_assets: status=pass violations=0 …
      [BAD ] structural: c28's population has been re-pointed
               - c28: does not iterate `s.assets` — its population is not the set of assets making the claim
               - c28: references `build_run*` — C-28 must not read the run table at all; absence is found by the assets it does NOT contain
MUT_A_EXIT=3
```

**Mutation B — inverse direction** (the doctrine's requirement for a mutation that makes a
signal fire when it should NOT): `if True or (built and …)`:

```
      [BAD ] shipped C-28 …: status=fail violations=['bg_probe_unlit', 'bg_probe_unwitnessed', 'bg_probe_witnessed']
           expected status=fail violations=['bg_probe_unwitnessed'] — …
MUT_B_EXIT=3
```

### What part 4 does NOT establish — stated in the docstring, not assumed

It is a source-text assertion. It catches a re-pointing written in the obvious way. It
would NOT catch one that reached `build_run_assets` through an indirection, a helper in
another module, or a renamed snapshot key. Parts 1–3 are the behavioural backstop for
that, and they bind whatever the source looks like.

---

## The stale-comment sweep (routed to me mid-task by SŪTRADHĀRA, rode with commit 1)

Corrected, without softening or deleting the reasoning:

1. **The `CONSEQUENCE TODAY` block** (~l.470) asserted "all sixteen shipped entries lack
   both `gating_effect` and `authorised_by` … NOT ONE BLOCKING GATE IS DEMOTED". True when
   M0-T14 wrote it; falsified by M0-T49 at 14:06Z. Rewritten to say what is now true and
   **deliberately not to restate a fresh count** — it points at the guard's own
   `disclosed_non_gating` summary field instead, because a frozen count in a comment is
   exactly the mechanism that produced the stale claim. It also records what has NOT
   changed (a demoted rule still fails and still reports every violation) and re-verified
   the clause about the CI switch: `nirmana-m0-guards.yml`'s conformance job is still
   `continue-on-error`, so "still unflipped" remains true and I kept it.
2. **The third bullet's stated limit** — "it verifies such a ruling EXISTS and who authored
   it; it cannot verify the ruling says what the entry claims" — was the hole itself, and
   my own change falsifies it. Replaced with the new conjunct and with the limit that
   actually remains: the ledger is an append-only file in this repo, so the detector is
   exactly as trustworthy as the ledger's integrity — it proves the warrant was written,
   never that it was wise.
3. Two smaller factual touch-ups: the historical "Sixteen entries were written" now says
   "AT THAT TIME (the file has grown since)"; the `emit_text` DISCLOSED-non-gating legend
   now mentions the grant.

**Everything else I swept and found clean:** every other `ADHIKĀRIN`/`authority` mention
(l.80, 438, 1053, 1345, 1393, 1476, 1509, 1542, 1748, 1850) and every numeric/`inert`/
`decorative`/`not one` hit. The two "sixteen" occurrences in the M0-T40 defect narrative
and the probe docstring are past-tense history of what M0-T36 shipped, not claims about
the current file; I left their substance and only clarified the first. **No comment edit
changed any behaviour** — I re-ran `--self-test` and `--live` after the sweep and the
per-rule outcomes were byte-for-byte identical to the run before it.

---

## What I did NOT do

- Did not touch `asset_catalogue_disclosed_residuals.json`, or any other file. Two commits,
  one file, `--only` with an explicit path both times.
- Did not widen, relax or edit any `covers` list or any `authorised_covers` grant. The 15
  shipped demotions were verified to survive; had one not, D-61 part 5 says that is a
  finding and I would have stopped.
- Did not modify `c28`. Did not re-point any population at `build_run_assets` anywhere
  outside a probe-local function that is never called by the guard.
- Did not touch `.github/`, did not flip the blocking switch, did not add
  `continue-on-error`, did not make any failing rule pass.
- Did not touch asset data (I14), any registry row, any migration, any writer, or anything
  in a layer (I13).
- Did not read, log or rotate a credential; `--live` uses the guard's existing reader.
- Did not certify anything (I16/H7).

## What I am unsure about — please attack these

1. **New self-test case 7b is a new way for CI to go red on DATA, not code.** It asserts
   the *shipped* residuals file's demotions are inside their cited grants. That is the
   direction I believe is right (fail closed, and D-61 part 5 wants it proven by a
   detector), but it means a future authorised disclosure that ADHIKĀRIN writes *before*
   writing the matching `authorised_covers` will turn the DB-free self-test red rather
   than merely being inert. I judged that correct under D-61 part 6. If ADHIKĀRIN wanted
   the runtime check only, 7b is the piece to remove.
2. **`decision_grant` is keyed on `ent['rule']`, not the entry key.** That is what makes
   `C-28_residual` resolve against D-54's `C-28` grant. I believe this is right — an entry
   may be filed under any key but can only be authorised for the rule it declares — but it
   is a decision I made, not one D-61 spelled out.
3. **D-57's `corrected_grounds` is not parsed**, per D-61 part 6's explicit note that the
   detector reads D-54 and that this is an accident not to be relied on twice. So the
   current shipped 15 pass on D-54's field, and any *future* correction that changes what
   is authorised must land as `authorised_covers` or it will not be seen.
4. **The probe's authority selection follows the ledger.** If no ADHIKĀRIN decision ever
   grants C-01 for an identity C-01 would flag, the probe reports NOT CHECKABLE and
   returns a failure rather than skipping. That is deliberate (§N.8) but it does couple a
   DB-free self-test to the ledger's contents; a future ledger edit could turn it red.
5. **SQ-11's structural check is source-text.** Its limit is stated above and in the
   docstring. I did not attempt an AST-level or import-graph check.
6. **No new JSON fixture was added under `asset_catalogue_fixtures/`.** The `_expect`
   fixture format cannot express "and the trapped variant must return 0", which is the
   whole discriminating half of SQ-11, so I built it as a probe. If PARĪKṢAKA wants a
   static fixture as well, it would only cover part 1.
7. **Concurrency.** A sibling committed between my two commits. I re-verified both of mine
   are ancestors of HEAD and that my file's diff contained no one else's hunks, but I did
   not re-run the guard after the sibling's commit landed; the sibling touched no file this
   guard reads except possibly `state/` — worth a glance if PARĪKṢAKA re-runs and sees a
   different decision count than the 64 recorded above.
