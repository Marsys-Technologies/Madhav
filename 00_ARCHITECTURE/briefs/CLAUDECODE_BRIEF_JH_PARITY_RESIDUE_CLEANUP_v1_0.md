---
artifact: CLAUDECODE_BRIEF_JH_PARITY_RESIDUE_CLEANUP_v1_0.md
brief_id: JH_PARITY_RESIDUE_CLEANUP
version: 1.0
status: ACTIVE
authored_at: 2026-06-01
authored_by: cowork-planner
extends: implementation-brief follow-up F2 (which scoped only 00_ARCHITECTURE/ governance docs)
why: >
  The PR #184 AC4/AC5 greps were scoped to platform/python-sidecar/ and reported zero
  natal_engine / jh_parity hits. Repo-wide there is residue in platform/ code paths that
  the AC wording (platform/ src/) intended to catch and the standing directive
  [[no-jh-parity-anywhere]] forbids. This brief clears it.
may_touch:
  - platform/scripts/hard_gates_check.sh
  - platform/evals/acc2_hard_gates.json
  - platform/src/app/api/engine/current/route.ts
  - platform/src/app/api/engine/__tests__/current_route.test.ts
  - platform/src/app/api/build/__tests__/build.integration.test.ts
  - platform/python-sidecar/tests/test_pyjhora_adapter/_scratch/   (DELETE — committed by mistake)
  - platform/scripts/governance/CHART_FACTS_SCHEMA.json            (only if native approves provenance-string rewrite)
  - platform/migrations/124_builds.sql, 126_engine_versions.sql    (comments/defaults only — see §3, native call)
must_not_touch:
  - 00_ARCHITECTURE/                                               (F2's scope — separate arc)
  - platform/python-sidecar/pyjhora_adapter/                       (engine — don't disturb)
  - any applied migration's executed semantics (see §3 — strings only, no schema change)
hard_bans:
  - No Anthropic models.
  - Do not delete content based on filename alone — diff first ([[never-rm-based-on-filename]]).
prime_directive: only computed facts. no narrative.
---

# Clear the in-`platform/` jh-parity + natal_engine residue

## 1 · What PR #184 left behind (grounded grep on the merged branch)

AC4/AC5 were green only for `platform/python-sidecar/`. Repo-wide:

**jh-parity in live code paths (violates [[no-jh-parity-anywhere]] — primary target):**

- `platform/scripts/hard_gates_check.sh` — gate **G2** actively `find`s `jh_oracle.json`
  and marks `G2_jh_oracle_pinned` **GREEN when it is found**. A live gate that *rewards*
  the banned oracle's presence. This is the worst offender — it inverts the directive.
- `platform/evals/acc2_hard_gates.json` — carries `{"gate":"G2_jh_oracle_pinned",
  "status":"GREEN","note":"jh_oracle.json found"}`.
- `platform/src/app/api/engine/current/route.ts` — response body field `jh_parity_sha`
  (sentinel null), plus assertions in `current_route.test.ts` and
  `build.integration.test.ts` that `body.jh_parity_sha` is null.

**Committed-by-mistake scratch:**

- `platform/python-sidecar/tests/test_pyjhora_adapter/_scratch/discover_api.py` — the
  empirical-discovery scratch file the implementation brief said should be **gitignored**.
  It got tracked.

**natal_engine string literals (low risk — provenance markers, NOT imports):**

- `platform/migrations/124_builds.sql` — `engine_version DEFAULT 'natal_engine/0.2.0'`.
- `platform/migrations/126_engine_versions.sql` — comments referencing natal_engine.
- `platform/scripts/governance/CHART_FACTS_SCHEMA.json` — `since_engine_version:
  "natal_engine/0.1.0"` on several fields.

## 2 · Fixes (jh-parity — the part that matters)

1. **`hard_gates_check.sh` G2.** Remove the G2 gate entirely, or repurpose it to assert the
   *opposite* invariant: that **no** `jh_oracle.json` / `test_jh_parity*` exists anywhere in
   the repo (GREEN = absent), matching [[no-jh-parity-anywhere]]. Recommend repurpose — it
   turns a banned-artifact check into an enforcement of the ban. Update the gate id/name
   accordingly (e.g. `G2_no_jh_parity_artifacts`).
2. **`acc2_hard_gates.json`.** Update the G2 entry to match the repurposed gate (or remove
   it if the gate is removed). Keep the file's array shape valid.
3. **`jh_parity_sha` API field.** Remove the field from
   `engine/current/route.ts`'s response type and body. Update `current_route.test.ts` and
   `build.integration.test.ts` to drop the `jh_parity_sha` assertions. If a column/field is
   genuinely consumed downstream (check the cockpit + any `/api/engine/current` consumers
   first — [[grep-gate-catches-jsdoc-residue]]), coordinate the removal so nothing reads a
   now-absent field; if nothing consumes it, delete cleanly.
4. **`_scratch/discover_api.py`.** `git rm` it and add
   `platform/python-sidecar/tests/test_pyjhora_adapter/_scratch/` to `.gitignore`.

## 3 · natal_engine provenance strings (native decision — default: leave them)

The migration defaults and `CHART_FACTS_SCHEMA.json` `since_engine_version` strings are
**historical provenance**: they record which engine version first introduced a field.
Rewriting `'natal_engine/0.2.0'` → `'pyjhora/1.0.0'` would be **falsifying history** — that
field WAS introduced under natal_engine. Recommendation: **leave them as-is**; they are
accurate audit trail, not live engine references.

The only forward-looking default worth changing is migration 124's
`engine_version DEFAULT 'natal_engine/0.2.0'` **if** new build rows still inherit it — but
the pyjhora arc set `ENGINE_VERSION = "pyjhora/1.0.0"` in the writers (per CURRENT_STATE
v5.66), so new rows already carry the right value and the DEFAULT is dead. Changing an
*applied* migration's text is itself a hygiene smell ([[never-rm-based-on-filename]] —
applied migrations are immutable history). If the dead DEFAULT bothers the native, fix it
forward with a NEW migration that alters the column default, not by editing 124. **Default
posture: do nothing here; document as accepted provenance.**

## 4 · Acceptance criteria

1. `grep -rn "jh_parity\|jh_oracle" platform/ src/` → 0 hits in **executable code paths**
   (scripts, route handlers, evals, tests). Provenance-only string hits in
   `00_ARCHITECTURE/` are out of scope (F2).
2. `hard_gates_check.sh` no longer rewards the presence of `jh_oracle.json`; if repurposed,
   it asserts absence and is GREEN on the current repo.
3. `_scratch/` is gitignored and untracked.
4. `engine/current` has no `jh_parity_sha`; no consumer reads a missing field; tests green.
5. `tsc --noEmit` clean; `vitest` + `pytest` green.
6. natal_engine provenance strings: either left as accepted history (documented in PR) or
   fixed-forward via a new migration — never by editing applied migrations 124/126.

## 5 · Antigravity kickoff prompt (paste verbatim)

```
Execute CLAUDECODE_BRIEF_JH_PARITY_RESIDUE_CLEANUP_v1_0.md at
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_JH_PARITY_RESIDUE_CLEANUP_v1_0.md.

Scope is platform/ ONLY (00_ARCHITECTURE/ governance-doc cleanup is F2, a separate arc).
Primary target: the jh-parity residue in live code paths (§1, §2). Repurpose the
hard_gates G2 gate to enforce ABSENCE of jh_oracle/test_jh_parity artifacts, not reward
their presence. Remove the jh_parity_sha API field only after grepping all consumers.
git rm the committed _scratch/ file and gitignore the dir.

Do NOT touch applied migrations 124/126 text — provenance strings are accepted history
(§3); if a dead column default must change, write a NEW migration. Diff content before any
delete ([[never-rm-based-on-filename]]). Run tsc --noEmit + vitest + pytest. Halt at PR.

Paste the PR URL + the 6 acceptance criteria checked + the final
`grep -rn "jh_parity\|jh_oracle" platform/ src/` output.
```

---

*End of CLAUDECODE_BRIEF_JH_PARITY_RESIDUE_CLEANUP_v1_0.md*
