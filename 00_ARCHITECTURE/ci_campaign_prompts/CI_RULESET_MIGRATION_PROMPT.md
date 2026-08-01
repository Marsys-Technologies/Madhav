# Claude Code task — migrate `main` protection from classic → ruleset, enabling merge queue (Madhav)

Merge queue is **not** available in this repo's classic branch protection — confirmed three ways:
REST exposes no merge-queue key, GraphQL `BranchProtectionRule` has no queue fields, and the classic
rule's edit page (read live in the browser) has no such checkbox. GitHub moved merge queue to
**Rulesets**. Abhisek has chosen to migrate `main` fully to a ruleset rather than run two systems.

This changes the repo's protection architecture. Do it **staged, verified, and reversible** — the
classic rule is not deleted until the ruleset is proven. Same standing rules as the whole campaign
(`00_ARCHITECTURE/CI_EFFICIENCY_AUDIT_v1_0.md §6`); the relevant ones here:

- A job-level `conclusion` is `success` even when a `continue-on-error` step exited 1 — read the
  queue-ref checks at step level.
- Impossible / wrong instructions get **recorded, not worked around**. Assume this brief has one.
- Verify on `main`, not from assumption.

---

## The current classic rule — VERIFY, then treat as the migration's source of truth

Read live from the classic rule's edit page on 2026-07-31. **Re-verify with
`gh api repos/amonty84/Madhav/branches/main/protection` before building anything** — if any line
differs, stop and report; the ruleset must replicate reality, not this snapshot.

- Branch pattern: `main`
- **Require a pull request before merging: OFF**  ← note: direct pushes to `main` are currently
  allowed for those with access. Merge queue REQUIRES PRs, so the migration necessarily turns this
  ON. Call that out in your report — it is a real behaviour change, intended, but not something the
  old rule did.
- Require status checks to pass: **ON**, strict (**Require branches up to date: ON**)
  - Required checks, all GitHub Actions, names must be **byte-identical** in the ruleset:
    `TypeScript (src only)` · `Unit Tests` · `Secret Scan (unit 0b.2)` ·
    `Governance Gates (drift / schema / edge / native-literal / py-sidecar)`
- Require conversation resolution: OFF · signed commits: OFF · linear history: OFF ·
  deployments: OFF · lock branch: OFF
- **Do not allow bypassing the above settings: ON**  → the ruleset must have an **empty bypass list**
  (no bypass actors), which is the equivalent.
- Allow force pushes: OFF · allow deletions: OFF  → ruleset includes `non_fast_forward` and
  `deletion` rules.

Precondition already met (#967, verify still on `main`): `ci.yml` declares `merge_group:` so the four
checks run on the queue ref. Without it the queue hangs every PR — if your re-verify shows it
missing, STOP.

---

## Step 1 — Build the ruleset as reviewable JSON, do not apply yet

Author a `POST /repos/amonty84/Madhav/rulesets` body (`gh api ... --input`) and **print it for
Abhisek before sending.** Target ref `refs/heads/main`. It must contain, at minimum:

- `enforcement: "active"`
- `bypass_actors: []`  (equivalent of "do not allow bypassing")
- rules: `required_status_checks` with the four contexts above and
  `strict_required_status_checks_policy: true`; `pull_request`; `merge_queue`
  (batch/group size **1**, squash to match repo practice); `non_fast_forward`; `deletion`.

Set the merge_queue parameters conservatively — group size 1, and the default check/merge timeouts.
State every field you set and why. If the ruleset API requires a field whose correct value you
cannot determine from the classic rule, ask rather than guess.

## Step 2 — Apply the ruleset ALONGSIDE classic protection

Create it. **Do not delete or weaken the classic rule yet.** Both now apply; GitHub takes the union
of restrictions, so `main` is at worst more protected during the overlap — the safe direction.

Verify the ruleset exists and reads back with the four contexts byte-identical and `strict` true
(`gh api repos/amonty84/Madhav/rulesets/<id>`).

## Step 3 — Canary through the queue

Use the existing throwaway **#972** (open, green, unarmed) — or a fresh trivial PR if #972 is no
longer suitable. Merge it via **"Merge when ready"**.

- **PASS:** the four required checks appear *and complete* on a `gh-readonly-queue/main/…` ref, and
  the PR merges. Read them at step level (rule 1).
- **ABORT:** checks don't appear within minutes, or any check on the queue ref reports `cancelled`
  (the `cancel-in-progress` fix didn't take → eviction). **Delete the ruleset** — classic protection
  is untouched underneath, so `main` is instantly back to exactly today's behaviour. Report and stop.

## Step 4 — Only after a clean queue merge: retire classic protection

With the ruleset proven, delete the classic `main` branch-protection rule so there is one coherent
system. The ruleset now carries strict + the four checks + require-PR + queue.

**Then, and only then, decide `strict` inside the ruleset.** The original campaign goal was to drop
`strict` *because* the queue makes it redundant. But confirm the queue genuinely enforces
merge-base freshness first — one clean canary proves the queue runs, not yet that dropping `strict`
is safe. Recommend, show Abhisek the reasoning, let him choose. Do not drop it in the same step you
delete classic protection.

---

## Guardrails

- Never delete or weaken classic protection until the ruleset has passed a live queue merge.
- The four required check names must be byte-identical — a mismatch makes every PR hang.
- Print the ruleset JSON before applying; print the read-back after.
- Prefer honestly red / honestly blocked over silently open.

## Deliverable

Prose. The re-verified classic state and any drift from the snapshot above; the ruleset JSON you
applied; the canary result read at step level; whether classic protection was retired; and your
`strict` recommendation with reasoning. End with a plain statement: **is `main` now on a single
ruleset-based protection with a working queue, yes or no** — and if no, what remains and what the
one-step rollback was.
