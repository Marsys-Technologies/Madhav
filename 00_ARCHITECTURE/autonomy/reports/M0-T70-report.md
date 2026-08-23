# M0-T70 — the entrypoint-guard ratchet's pawl reads a persisted FLOOR, not `HEAD^`

**Agent:** KARAKA-M0-T70 · **Authority:** D-95 (fix), bounded by D-96 (no exemption field) ·
**File touched:** `platform/scripts/governance/check_entrypoint_guard_ratchet.py` ·
**New artifact:** `platform/scripts/governance/entrypoint_guard_floor.json` ·
**Also touched:** `.github/workflows/nirmana-m0-guards.yml` (checkout depth + comments)

This report states what was built and observed. It does not certify the work — PARĪKṢAKA does
(I16/H7).

## The defect, restated from D-95

T68's pawl (D-87) asserted `committed allowlist ⊆ its own previous committed value`, where
"previous" meant `HEAD` (uncommitted edit) or `HEAD^` (clean checkout). PARĪKṢAKA's V-64 found
this reference **slides**: it is red at the exact commit that introduces a growth, and green
one commit later, because by then `HEAD^` has itself absorbed the growth and the comparison
becomes vacuous (self vs. self). Confirmed live on M0-T16's merge, which brought three
unguarded files in from `origin/main`.

## What was built

**A new persisted artifact, `entrypoint_guard_floor.json`**, holding the smallest allowlist
ever committed. Two new gating assertions replace the old `HEAD^`-based pawl entirely (per
D-95 point 5 — the floor *replaces* the previous-commit anchor, it does not sit beside it):

1. **`floor_containment`** — `current allowlist (read from disk) ⊆ floor (read from disk)`.
   No git ref logic needed here at all: both sides are read the same way `read_current_side`
   already read the allowlist (disk, dirty or clean), which is itself the fix for the sliding
   problem — the floor is not a function of *which commit you're on*, so there is no adjacent
   commit for it to slide behind.
2. **`floor_monotone_check`** — the floor's own self-protection (the thing that stops anyone
   hand-widening the floor file itself, the same class of hole D-87 closed for the allowlist,
   one layer up). Deliberately **not** shaped like D-87's adjacent `HEAD`-vs-`HEAD^` check —
   an adjacent-only check on the floor's own history would inherit the exact one-commit-release
   flaw D-95 exists to remove, just moved one file over. Instead it walks the floor's **entire**
   committed history (bounded by the existing `HISTORY_SCAN_LIMIT = 200`) and asserts the
   current floor is a subset of **every** value it has ever held, not merely its parent. This
   is what makes the merge-scenario self-test (below) actually prove non-release, rather than
   just re-proving the single-step case D-87 already had.

Both are D-89-anchored: either side being unreadable (`None`) is `determined=False` and
FATAL, never a vacuous pass — the same discipline `pawl_check` was built on, ported forward.

**The self-update ("same commit" enforcement — my design-fork resolution, see below).**
`--regenerate` (existing writer) now, after successfully writing a smaller allowlist, checks
whether the pay-down was a *strict* subset of the on-disk floor; if so it calls `sync_floor`
in the same invocation, rewriting `entrypoint_guard_floor.json` to match. A new standalone
`--sync-floor` flag exposes the same shrink-only write directly (used to seed the floor today,
and as a manual recovery path). Neither path can ever widen the floor: both refuse outright
the instant their target carries anything the existing floor lacks, and neither ever reads a
"requested" value from anywhere a hand could reach — the target is always a fresh scan
(`--regenerate`) or the already-baseline-checked on-disk allowlist (`--sync-floor`).

**Removed:** `PawlResult`, `pawl_check`, `_nearest_existing`, `run_pawl_self_test`, and
`_pawl_fixture_repo` (generalized and kept as `_git_fixture_repo`, reused by the floor
self-tests). `pawl_history` (the non-gating allowlist history-growth diagnostic) is
**unchanged and still non-gating**, per D-95's explicit instruction — it is now purely
diagnostic once the floor exists. A parallel non-gating diagnostic,
`floor_history_growth_steps`, was added for the floor's own history using the same
`pawl_history` function (it is generic over which path it reads).

## Design-fork resolution: how "same commit" is mechanised

D-95 flagged this as open ("think about how you enforce or verify this"). I chose: **fold the
floor-sync into `--regenerate` itself**, rather than requiring a separate `--sync-floor`
invocation every time. Rejected alternative — auto-write the floor on a bare (no-flag) check
run: rejected because a read-only gate mutating the tree it is checking is a surprise, breaks
the existing convention that only `--regenerate` writes files, and has no CI use (CI runs the
bare check, which would then need its own write-back-and-fail-if-dirty dance). Folding the
sync into `--regenerate` means one command produces one working-tree diff touching both files,
so whoever stages and commits does so together *by construction* — nothing to remember. D-96
check: does this let anything widen the floor other than committed growth landing? No —
`sync_floor` is shrink-only regardless of caller, and it is called only with `measured` (a
fresh scan) or the on-disk allowlist, never a hand value.

## The merge-commit scenario (D-95's motivating case), reproduced and closed

Per the hard requirement to prove non-release rather than assert it, `run_floor_self_test`
Case 6 builds an isolated throwaway repo (git, `/tmp`, per D-77/PARK-9 — no live mutation on
this tree) with commits v0 (floor=[a,b,c]) → v1 (paydown to [a,b]) → v2 (a merge-shaped commit
resurrecting [a,b,c], reproducing M0-T16's shape) → v3 (an unrelated commit that does **not**
touch the floor, simulating "the campaign kept working"). `floor_monotone_check` is evaluated
at v3 (one commit *after* the merge, nothing further done) and still returns `ok=False`,
naming v1 as the violated ancestor — proving the check does not release the way D-87's did.
Case 7 then adds a genuine recovery commit (shrink back to `[a,b]`) and proves the check goes
green again — the clearability property that distinguishes this from D-39 part 2's forbidden
permanently-red shape.

## Self-test results

`--self-test` now runs 11 floor-specific cases (containment pass/fail, D-89 anchoring on both
sides, monotonicity on a shrink-only history, the merge scenario, the recovery-clears-it case,
an uncommitted hand-widening, an absent-current case, and `sync_floor`'s never-widens /
does-shrink / does-create behaviors), alongside the existing 10 fixture-based idiom tests.
All pass:

```
check_entrypoint_guard_ratchet: SELF-TEST PASS (6 pass fixture(s) silent, 4 fail fixture(s)
caught, 5/5 guard idioms exercised, 11 floor case(s) proven in both directions).
```

## The floor's initial value — measured, not hand-typed

`--sync-floor` was run once against today's on-disk, already-baseline-validated allowlist.
Seed value: **71 entries**, identical to the 71-file allowlist current at this session's
starting `HEAD` (measured — not asserted). Re-running `--sync-floor` afterward reports
"floor already in sync (71 entries) — nothing to do", confirming idempotency.

## An unrelated, pre-existing finding — not fixed, flagged

The plain gate (no flags) currently exits 1 for a reason that has **nothing to do with this
task**: three genuinely new unguarded top-level `main()` files exist under
`platform/scripts/probe/` (`p4k_narration_analyzer.ts`, `p4k_sequence_driver.ts`,
`post_deploy_behavior_smoke.ts`) that are not in M0-T64's settled baseline at all — this is
assertion (i) territory (`hand_added`/`new`), not the floor. I confirmed this by running the
**unmodified, pre-patch script** (from a backup) against the same tree: it fails identically.
This is real drift, out of my scope (I was told not to repair any of the 71/72 unguarded files
or touch Wave 2), and I am not fixing it. The floor mechanism itself is clean:
`floor: allowlist (71) ⊆ floor (71), and the floor ⊆ every value its own committed history has
ever held — neither grew.` This should be raised as a new finding/task, not conflated with
D-95's closure.

## CI workflow

`fetch-depth: 2` → `fetch-depth: 0` (full history), because `floor_monotone_check`'s
full-history walk needs every commit that ever touched `entrypoint_guard_floor.json` present
in the checkout, not merely the last one — a shallow `fetch-depth: 2` would silently narrow
the floor's own self-protection back down to a single-step check, reopening exactly the
release hole D-95 closes. The script still bounds its own walk to `HISTORY_SCAN_LIMIT` (200
commits) regardless of how much history is fetched, so this line controls visibility, not the
script's own cost ceiling. Side benefit noted and reported honestly: the *plain containment*
check (current allowlist ⊆ floor) needs **no git history at all** — both sides are read
straight off the checked-out working tree — so if CI cost from `fetch-depth: 0` ever becomes a
concern, a future session could split the floor's self-protection into its own less-frequent
job without weakening the main containment gate. I did not make that split myself; it is a
possible follow-on, not something D-95 asked for.

## What I did not do

- Did not touch Wave 2, did not repair any of the 71/72 unguarded files (or the 3 newly-found
  ones above), did not touch any `I14` asset-data work.
- Did not add any exemption/declared-growth field anywhere (D-96). The only widening path is
  guard-the-file-then-shrink (already how the allowlist and floor both work) or a brand new,
  explicitly-ruled baseline file — never a flag in either JSON.
- Did not use `git checkout` in the shared tree (PARK-9); all mutation testing ran in
  throwaway repos under a `tempfile.TemporaryDirectory()`, per D-77.
- Did not certify this work. PARĪKṢAKA verifies; this report states observations only.
