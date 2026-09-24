---
artifact: KALA_EXECUTION_HANDOFF_PROTOCOL
canonical_id: KALA_EXECUTION_HANDOFF_PROTOCOL
version: "1.0"
status: CURRENT
date: 2026-09-24
audience: "the Kāla EXECUTION session (a separate Claude session); read in full before touching code"
authority: "operational only — it governs how work is dispatched and reported, and rules nothing about the assets themselves"
---

# Kāla execution handoff protocol

Two sessions, one layer.

* **Strategy session** (this repo's `00_ARCHITECTURE/control/` + the briefs). Owns the briefs, the
  order, the tracker, and verification. **Executes nothing.**
* **Execution session** — a separate session. Takes ONE asset at a time, executes its brief, reports
  back through the ledger. **Decides nothing** about scope, order or acceptance.

The two never edit the same file. The only channel between them is the append-only ledger.

## 1 — The ledger is the channel

`00_ARCHITECTURE/control/kala_elevation_ledger.jsonl` — one JSON object per line, append-only,
never edited, never reordered. Write to it **only** through:

```
python3 00_ARCHITECTURE/control/kala_record_event.py \
    --asset <ka_id> --event <event> --session <your session name> \
    [--commit <sha>] [--branch <name>] [--evidence <path|url>] \
    [--brief-version <v>] [--note "..."]
```

Hand-editing the file is a protocol violation: the helper is what enforces the vocabulary and the
`completed`-before-`verified` ordering.

| event | who appends | means |
|---|---|---|
| `handoff` | strategy | this asset is dispatched; brief is final and DAG-unblocked |
| `started` | execution | work has begun |
| `completed` | execution | the brief's change packet is landed and its own tests pass |
| `blocked` | execution | cannot proceed; `--note` states why, in one sentence |
| `verified` | **strategy only** | the strategy session independently checked the work |
| `reverted` | either | the change was backed out; asset returns to brief state |

`completed` is **not** elevation. The tracker shows `AWAITING_VERIFY` until the strategy session
appends `verified`. This is the §N.8 earned-signal rule applied to the handoff itself: the signal
that says "done" is written by a party that could have said "not done".

## 2 — Order is not negotiable

Assets are elevated in **DAG order** — a topological sort of `asset_registry.depends_on`, sourced
from the `ka_*` block of `platform/scripts/seed/asset_registry_seed.ts`.

An asset is dispatched only when **both** hold:

1. its brief is final (`BRIEF_FINAL`), and
2. every upstream `ka_*` dependency is already `ELEVATED`.

The tracker computes this and prints the unblocked set. The execution session does not choose its
own next asset and does not start an asset it was not handed. If an asset looks ready but was not
dispatched, ask — do not proceed.

## 3 — What the execution session does per asset

1. Read the brief in full, including `may_touch` / `must_not_touch`. Those globs are the scope
   fence; anything outside them is out of scope even if it looks broken.
2. Append `started`.
3. Execute the brief's change packet, on its own branch, and nowhere near another session's worktree.
4. Run the brief's §7 proof matrix. A brief's claim is met only when a detector that **could have
   failed** did not.
5. Append `completed` with `--commit`, `--branch`, and `--evidence` pointing at the proof output.
   If the brief cannot be executed as written, append `blocked` with the reason instead. Do **not**
   improvise a different change: a brief that is wrong is a strategy-session problem, and reporting
   it is worth more than working around it.

**Hard limits.** Do not edit a brief, this protocol, the tracker, or the ledger by hand. Do not
change the FROZEN orchestrator contract. Do not edit an applied migration. Pick a migration number
by scanning every `origin/*` head across BOTH `platform/migrations/` and
`platform/supabase/migrations/` — they are one runner sequence. Do not touch production data or
credentials.

## 4 — What the strategy session does

Watches, verifies, and updates the briefs. On a `completed` event it re-reads the evidence, checks
the claim against the code, and appends `verified` — or does not, and says why. On `blocked` it
reworks the brief and re-dispatches.

It is also the only session that revises a brief. When execution surfaces a finding that makes a
brief wrong, the brief is corrected here and the asset re-enters the ladder at its brief state.

## 5 — Watching it live

```
python3 00_ARCHITECTURE/control/kala_brief_tracker.py --watch   # rescan every 10s
open       00_ARCHITECTURE/control/kala_brief_tracker.html      # repaints every 5s
```

The page shows DAG rank, depth, lifecycle state, what each asset is waiting on, and the five-tier
criteria matrix with per-column coverage. A criteria tick means the brief *addresses* the criterion,
never that it addresses it correctly — the matrix cannot see correctness, and one brief currently
scores well while containing a claim known to be false.

## 6 — Known gaps in this mechanism, stated rather than hidden

* The ledger records what a session *says* it did. `verified` is the only event backed by an
  independent check, and only as far as the strategy session's own reading goes.
* Criteria detection is marker-based and will report a passing mention as coverage.
* `ka_gochara_sweep` exists in the registry seed but is in no brief and in no tracker row. It is a
  23rd `ka_*` asset. Nothing here covers it; that is a real hole, not an omission by design.
* Rows 4–6 (`ka_gochara_v3_century_materialize`, `ka_gochara_resonance`, `ka_vedha_gochara`) have no
  standalone brief and inherit the Gochara family plan, so their criteria cells repeat the family
  row and their coverage is not independently measured.
