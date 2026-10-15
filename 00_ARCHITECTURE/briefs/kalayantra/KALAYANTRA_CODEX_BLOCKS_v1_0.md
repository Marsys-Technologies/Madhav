---
artifact: KALAYANTRA_CODEX_BLOCKS
version: "1.0"
status: ACTIVE from the 2026-10-08 hand-over — owner direction: "plan blocks of work that we can send to Codex to execute headlessly"
amends: KALAYANTRA_VELOCITY_AMENDMENT_v1_0.md §1 and §8 (which agent runs which lane)
---

# KĀLA-YANTRA — Codex blocks

**Written for:** the conductor (the owner's Claude session) and the builder lanes.

## The split

| Who | Runs | Why |
|---|---|---|
| **Codex, headless** (lanes k1–k4, `codex exec` under the supervisor) | **blocks**: whole engine families that are fully specified by their algorithm cards, carry their own oracles, and need no cross-campaign coordination or production step | long, deterministic engineering; runs unattended overnight |
| **Claude lanes** (k5–k8, all verifiers, the surrogate) | everything that needs judgement or coordination: the J lane (Gochara absorption, inherited PRs, production steps), L0 (Suvarṇa reseal), K3, VC/K5 (verification campaign and decisions), K8/K9 (registration, publication), packet reviews | coordination, rulings, production discipline |
| **This session** | conductor: assigns blocks, queues, paces, fixes what bites | owner present |

**Cross-model review comes free:** a Codex-built PR is verified by a Claude verifier, so author and reviewer never share a model.

## The blocks (in the order they open)

| Block | Items, in order | Opens when | Size | Migrations | Lane |
|---|---|---|---|---|---|
| **CX-0 Foundation finish** | K0a-3 → K0a-4 | now (K0a-3 is k3's running item) | 13 files | 2 | k3 |
| **CX-1 Daśā clocks** | K1-1a → K1-1b | V-K0a | 6 files | 0 | k1 |
| **CX-2 Promise graph** | K2-1a → K2-1b → K2-2 | V-K0a | 12 files | 1 (K2-1b) | k2 |
| **CX-3 Gochara engine core** | KA-1e → KA-1w, then KA-2, KA-4 | V-K0a | ~30 files | 0 | k4 |
| **CX-4 Serving views** | K7-1a → K7-1b → K7-2 → K7-3 | V-K0a | 25 files | 0 | k3 (after CX-0) |
| **CX-5 Avadhi** | K1-2 | K1-1b ∧ K2-1b | 4 files | 1 | k1 (after CX-1) |
| **CX-6 Convergence** | K4-1 → K4-2a → K4-2aw → K4-2b → K4-3 | V-K3 | 31 files | 1 | k2 |
| **CX-7 Writers** | K6-123 → K6-4 → K6-5a → K6-5 | V-K4 (K6-4 also K5-G1b; K6-5a also D-R11) | 20 files | 3 | k4 |
| **CX-8 Reconciliation** | KR-1 | K9-6 | 12 files | 0 | any Codex lane |

Not blocks (Claude lanes): KA-3a, KA-3b, KA-4b (need J-0m, D-R8, L0-M), K3-1/K3-2 (J-5s), K5-*, VC-*, K7-4 (D-R6), K8-*, K9-*, KR-2, every J item, L0-*.

## How a block runs

1. The conductor writes `/Users/Dev/kalayantra/run/blocks/<lane>.json` = `{"block": "CX-n", "items": ["…", "…"], "by": "conductor", "ts": "…"}`.
2. The lane, at claim time, takes the **first item of its block that is READY or already its own**; when none is READY it takes the ordinary next READY item, so a block lane is never idle while the block waits on a dependency.
3. Each item goes to its PR under the v2 rules (one item, one PR, tests and mutations inside the PR, `precheck.sh --item`), and a Claude verifier reviews it.
4. When every item of the block is done, the conductor removes the block file or assigns the next block.

The conductor may reassign a block to another lane or agent at any time by rewriting the block file; the claim record keeps the branch and step, so nothing is lost.
