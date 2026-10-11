---
artifact: KU_REPLACEMENTS_v2_7.md
version: 2.7
status: DRAFT — pending the B-0c independent review
source: reviews/ASTRA_REVIEW_KALAYANTRA_RELAUNCH_v2_2.md §3 (KU-01…KU-03), verbatim; machine copy in ku_bindings.json
rule: these clauses enter the named B-1 packets unchanged (plan v2.7 §14 B-0c; carried, not closed, per §17); they change no approved plan, prompt or paste anchor. Nothing enforces this yet — kypacket.py is a B-1 deliverable; until it exists the packet reviewer verifies each clause hash by hand against ku_bindings.json
---

# Astra KU-01…KU-03 — exact replacements for the B-1 packets

## KU-01 — HIGH before conductor paste: audit disagrees with typed completion

**Packets (B-1 components):** `tracker-semantics`, `preflight-v3`, `kyverdicts`  
**Also binds:** B-2 preflight acceptance: remaining legacy claim/verdict findings are reconciled explicitly first

> Audit and guarded completion shall share the same normalized, typed evidence requirements. Data-writing code requires ACCEPTED post_deploy evidence at the observed squash merge commit. Code-only completion requires verified successful deployment containment of its mapped merge commit, without inventing a post_deploy obligation. Artifact and operation completion retain their digest-bound acceptance requirements. Apply the shared reviewed-patch inheritance predicate wherever reviewed-head validity is evaluated.
>
> Acceptance fixtures shall prove: valid code-only completion without post_deploy passes; missing deployment containment fails; data-writing completion with missing or wrong-commit post_deploy evidence fails; invalid inheritance fails. Reconcile remaining legacy claim/verdict findings explicitly before B-2 preflight acceptance. Do not fabricate verdicts, rewrite historical events or suppress unresolved findings.

## KU-02 — HIGH before conductor paste: DB storage and cleanup lack executable acceptance

**Packets (B-1 components):** `local-db`, `kylock`, `finalize-v3`, `kyloop-crash-cleanup`, `dispatcher-ready-receipts`  
**Also binds:** every session that starts a test database: session-close / lock-release path and finalisation

> Every v3 test database shall record its originating session and use PostgreSQL data storage explicitly bind-mounted beneath that session’s dated KY_SCRATCH realpath. Record container identity, mount source, database ownership and seed hashes in its receipt; reject an anonymous volume, an out-of-root mount or an ownership mismatch. Preserve incompatible pre-existing containers and report them; do not repurpose or delete them automatically.
>
> Before the originating planner or conductor session closes, including handoff, stop relevant admissions, drain or terminate its test processes while preserving work, remove its test databases and owned storage, and verify physical absence. Remove a container only when session ownership permits it and no foreign database remains. Enforce this through the session-close/lock-release path as well as finalisation. Test wrong mounts, stale READY receipts, ownership conflicts and stop-without-removal. A later session recreates required databases from an admitted seed.

## KU-03 — LOW: generated-file names disagree

**Packets (B-1 components):** `kyversion`  
**Also binds:** run/VERSIONS.bootstrap.json generated_pairs (kymanifest.py build/check); bootstrap acceptance refuses missing or unequal copies

> For WORKTREE_DISPOSITIONS, ACCEPTANCE_ROOTS and CLOSURE, use the plan’s named paths as canonical. Materialize the paired prompt’s differently named outputs as compatibility copies containing exactly the same reviewed bytes; retain content version 2.2. Record both absolute paths, the canonical role and their common SHA-256 in VERSIONS.bootstrap.json. Consumers use the canonical path; version checks verify both copies. Missing or unequal copies refuse bootstrap acceptance. Neither copy may be edited independently.
