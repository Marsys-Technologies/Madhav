---
artifact: PROJECT_KARN_PROTOCOL
canonical_id: PROJECT_KARN_PROTOCOL
version: 1.2
status: CURRENT
authored_by: Cowork (Claude) 2026-04-29
authored_for: Native + every future Cowork / Claude Code session
purpose: |
  Operating protocol for Project KARN — the M1/M2 corpus activation
  workstream within the larger MARSYS-JIS project. KARN is a workstream
  identifier, not a project replacement: the parent project remains
  MARSYS-JIS per CLAUDE.md, and KARN's deliverables feed M2 close.
project_name: KARN
project_meaning: |
  KARN = the M1/M2 ACTIVATION RUN. The name evokes Karna of the
  Mahabharata: a deeply-equipped warrior whose full power was held back
  by structural constraints he had to overcome. The work here is the
  same — the corpus has the depth; the activation removes the constraints.
changelog:
  - 1.2 (2026-04-30): Wave 2 expanded to 4 parallel briefs at Wave 1 close
    per native request — sidecar W2-R4 (M2_E_QUERY_ARCHIVE — BigQuery archive
    + GCS bucket + writer pipes) added because storage-infra scope is disjoint
    from corpus-ETL siblings (no file-path collision). Non-recurring exception;
    Wave 2 = 4 parallel for this wave only. Default cadence remains 3 parallel
    per wave; future waves stay at 3 unless similarly justified.
  - 1.1 (2026-04-29): Replaced S (Stage) with W (Wave); 3 parallel briefs
    per wave (was variable 4-6); added "close" ritual; added "KARN" bare
    bootstrap trigger; added Cowork conversation naming convention;
    rebalanced 18 briefs into 7 waves of 3 (last wave 2).
  - 1.0 (2026-04-29): Initial protocol with S-naming and variable wave widths.
---

# Project KARN — Operating Protocol v1.1

## §0 — What this is

A naming + cross-session-continuity protocol for the M1/M2 corpus activation workstream. Solves four problems:

1. **Cowork conversation identity.** Each wave has its own Cowork conversation, named `KARN-W{n}-<summary>`. Switch waves = switch windows.
2. **Claude Code session identity.** Each parallel run inside a wave has a unique short name `W{n}-R{m}` — easy to refer to in conversation, easy to track in logs.
3. **Cross-session memory.** A new Cowork conversation typing just `KARN` (or with a 5-word bootstrap prompt) becomes fully oriented in ~5 minutes.
4. **Clean wave handoff.** A "close" ritual seals each wave with a session-log entry and names the next wave's conversation.

## §1 — Naming convention

### §1.1 — Cowork conversation names (ONE per wave)

Format: `KARN-W{n}-{SUMMARY}`

- `KARN` — fixed project tag.
- `W{n}` — wave number (1 through 7 per the wave plan in §5).
- `{SUMMARY}` — 1–3-word UPPERCASE-HYPHENATED summary of the wave's theme.

Wave conversation names:

| Wave | Cowork conversation name | Theme |
|---|---|---|
| 1 | `KARN-W1-FOUNDATION` | Audits + filter + observability tables |
| 2 | `KARN-W2-ETL-EXPANSION` | MSR ETL + chart_facts ETL + CGM 339 edges |
| 3 | `KARN-W3-CORPUS-CHUNKERS` | Chunker completion + cluster recluster + pattern expansion |
| 4 | `KARN-W4-FACTS-TOOLS` | A-minor + KP/saham/divisional + chart_facts_query |
| 5 | `KARN-W5-NARRATIVE-TOOLS` | Temporal extension + L3/L4/L5 tools + res/con expansion |
| 6 | `KARN-W6-PLANNER-INTEGRITY` | Composition rules + per-tool planner + provenance audit |
| 7 | `KARN-W7-CLOSE` | Eval harness + M2 close |

These names also become the names you give your Cowork windows. One Cowork conversation per wave.

### §1.2 — Claude Code session names (3 PARALLEL per wave, mostly)

Format: `KARN-W{n}-R{m}-{SUMMARY}` — but inside a wave's Cowork conversation, the project prefix is implicit, so we refer to runs as `W{n}-R{m}` for short.

- `R{m}` — run number within the wave (1, 2, 3). Each wave has 3 parallel-launchable Claude Code sessions, except Wave 7 which has 2 (eval + close are sequential).

Examples:

- `KARN-W1-R1-PHASE-ALPHA` (full name) → `W1-R1` (short, used in the wave's Cowork conversation)
- `W2-R3` short for `KARN-W2-R3-CGM-FULL-EDGES`

The full name appears in:
- Brief frontmatter (`karn_session_name` field)
- Session log entries
- Anywhere ambiguity is possible

The short name appears in:
- Inside-the-wave conversation
- Quick references between Cowork and the native

## §2 — Bootstrap (starting any wave's Cowork conversation)

### §2.1 — The minimal trigger

In a fresh Cowork window, type one of:

**Lazy (1 word):**
```
KARN
```

The Claude in that window has filesystem access. It will recognize "KARN" as a project trigger, find `00_ARCHITECTURE/PROJECT_KARN_BOOTSTRAP.md` via the workspace mount, and bootstrap automatically.

**Reliable (1 line, ~10 seconds to type):**
```
KARN — read 00_ARCHITECTURE/PROJECT_KARN_BOOTSTRAP.md and orient me.
```

Both work. The reliable version eliminates any ambiguity about whether Claude will find the bootstrap doc.

### §2.2 — Bootstrap procedure (~5 min)

The new Claude reads, in this order:

1. `00_ARCHITECTURE/PROJECT_KARN_BOOTSTRAP.md` — entry point
2. `00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md` — this file
3. `00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md` — what's done, what's next
4. `00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md` — operating manual
5. `00_ARCHITECTURE/M1_M2_ACTIVATION_MASTER_PLAN_v0_1_DRAFT.md` — strategy
6. `00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md` — when it exists
7. `CLAUDE.md` — project rules

Then prints a concise orientation summary:
- Current wave + which conversation we're in
- Last 3 sessions that closed (from log)
- The 3 briefs to launch in this wave
- Any halts or open questions

Then waits for instruction. Does NOT run anything autonomously.

### §2.3 — Cowork thread name proposal

Per `CLAUDE.md` and `CONVERSATION_NAMING_CONVENTION_v1_0.md §4`, the new Cowork Claude proposes its conversation thread name at the top of its first substantive response. For KARN waves, the proposal MUST be `KARN-W{n}-{SUMMARY}` matching §1.1.

## §3 — Session log

Append-only log at `00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md`.

### §3.1 — Per-brief entry format

```
## KARN-W{n}-R{m}-{SUMMARY}

- **Brief:** <path to CLAUDECODE_BRIEF_M2_*.md>
- **Status:** PENDING | IN_PROGRESS | COMPLETE | HALTED | ROLLED_BACK
- **Started:** <ISO timestamp>
- **Closed:** <ISO timestamp>
- **Predecessors:** <KARN session names>
- **Stream:** A | B | C | D | E | F
- **One-line summary:** <human readable>
- **Files created/modified:** <bullet list>
- **DB changes:** <table: row count before → after>
- **Cloud Run:** <revision>
- **Tests:** <X passed / Y failed before> → <X' passed / Y' failed after>
- **Key findings:** <2–4 sentences max>
- **Halt-and-report cases:** <none | 1-2 paragraph description>
- **Next pointer:** <KARN session name or "wave close pending">
```

The Claude Code session writing the brief appends its own entry as part of its closing summary.

### §3.2 — Per-wave close marker

When all 3 (or 2 for W7) briefs in a wave are COMPLETE and the native types `close`, the Cowork conversation appends a wave-close marker:

```
## ─── KARN-W{n}-{SUMMARY} CLOSED ───

- **All briefs in wave:** W{n}-R1 ✅ COMPLETE | W{n}-R2 ✅ COMPLETE | W{n}-R3 ✅ COMPLETE
- **Sync findings:** <any cross-stream observations from the closing wave>
- **Wave outcome (one paragraph):** <what changed in the project as a result>
- **Next wave's Cowork conversation name:** `KARN-W{n+1}-{SUMMARY}`
- **Next wave bootstrap prompt:** `KARN — read 00_ARCHITECTURE/PROJECT_KARN_BOOTSTRAP.md and orient me.`
- **Closed at:** <ISO timestamp>
```

The marker is the boundary between waves in the session log. New Cowork conversation reads up through the most recent close marker to know where to start.

## §4 — The "close" ritual

This is how a wave's Cowork conversation cleanly ends.

### §4.1 — Native types `close`

When all briefs in the wave are COMPLETE per the session log AND the native is satisfied with the outcome, the native types one word:

```
close
```

### §4.2 — Cowork verifies

Cowork (this Claude) verifies:

1. All 3 briefs in the wave have `status: COMPLETE` per the log.
2. Sync points for that wave have been satisfied (e.g., Sync 1 after W1: native confirmed activation matrix).
3. No HALTED briefs without resolution.

If verification fails, Cowork pushes back: "Wave is not yet ready to close — W{n}-R{m} is still {status}. Suggest waiting / addressing it / overriding with explicit instruction."

### §4.3 — Cowork seals

If verification passes, Cowork:

1. Appends the wave-close marker to `PROJECT_KARN_SESSION_LOG.md` per §3.2.
2. Optionally updates `M1_M2_ACTIVATION_MATRIX.md` if Wave 1 just closed (and matrix gained new green rows).
3. Optionally drafts the next wave's brief catalog refinements based on this wave's findings.
4. Provides the native with the next-wave bootstrap prompt.

### §4.4 — Cowork can also propose close

If Cowork (this Claude) sees that all briefs in the wave are COMPLETE before the native types `close`, Cowork proactively says:

> All three briefs in W{n} are COMPLETE. Wave is ready to close. Type `close` to seal.

Native still confirms with `close`.

### §4.5 — What "close" does NOT do

- Does not auto-launch the next wave. Native opens a new Cowork window for that.
- Does not auto-merge branches or auto-deploy. The wave's briefs already handled their own deploys.
- Does not alter the briefs themselves. They stay as historical artifacts.

## §5 — Wave plan (7 waves)

### Wave 1 — `KARN-W1-FOUNDATION` (3 parallel briefs)

| Run | Brief | Stream |
|---|---|---|
| `W1-R1` | `M2_PHASE_ALPHA` (4 audits) | A |
| `W1-R2` | `M2_C6_VECTOR_SEARCH_FILTER` (F2.2) | B |
| `W1-R3` | `M2_D56_OBSERVABILITY` (audit_events + query_plans tables) | E |

**Sync 1 after close:** native reads A1's activation matrix, confirms W2 scope.

### Wave 2 — `KARN-W2-ETL-EXPANSION` (4 parallel — sidecar expansion 2026-04-30)

| Run | Brief | Stream |
|---|---|---|
| `W2-R1` | `M2_A1_MSR_ETL` (msr_signals columns + re-ingest) | A |
| `W2-R2` | `M2_A2_CHART_FACTS_ETL` (chart_facts FORENSIC §1–§27 coverage) | A |
| `W2-R3` | `M2_B1_CGM_FULL_EDGES` (CGM 126 → ~339 edges) | A |
| `W2-R4` | `M2_E_QUERY_ARCHIVE` (BigQuery archive + GCS bucket + writer pipes) | E |

**Sync 2 after close:** native confirms ingest counts AND query archive populated (≥5 live queries
in BigQuery + GCS objects, response_text captured).

### Wave 3 — `KARN-W3-CORPUS-CHUNKERS` (3 parallel)

| Run | Brief | Stream |
|---|---|---|
| `W3-R1` | `M2_B2_CHUNKER_COMPLETION` (UCN H3, cgm_node UCN merge, LEL chunks) | A |
| `W3-R2` | `M2_B3_CLUSTER_RECLUSTER` (MSR coverage 34% → 80%+) | C |
| `W3-R3` | `M2_B4_PATTERN_EXPANSION` (patterns 22 → 70+) | C |

### Wave 4 — `KARN-W4-FACTS-TOOLS` (3 parallel)

| Run | Brief | Stream |
|---|---|---|
| `W4-R1` | `M2_A_MINOR` (Vimshottari + pada + chalit) | A |
| `W4-R2` | `M2_C234_BUNDLE` (kp_query + saham_query + divisional_query) | B |
| `W4-R3` | `M2_C1_CHART_FACTS_QUERY` (the big new tool) | B |

**Sync 3 after close:** native confirms deploy convergence.

### Wave 5 — `KARN-W5-NARRATIVE-TOOLS` (3 parallel)

| Run | Brief | Stream |
|---|---|---|
| `W5-R1` | `M2_C5_TEMPORAL_EXTENSION` (dasha_chain + sade_sati + ephemeris) | B |
| `W5-R2` | `M2_D234_BUNDLE` (domain_report + remedial_codex + timeline tools) | B |
| `W5-R3` | `M2_B5_RES_CON_EXPANSION` (resonances + contradictions corpus) | C |

### Wave 6 — `KARN-W6-PLANNER-INTEGRITY` (3 parallel)

| Run | Brief | Stream |
|---|---|---|
| `W6-R1` | `M2_D1_COMPOSITION_RULES` (remedial + domainReport + timeline rules) | D |
| `W6-R2` | `M2_D7_PER_TOOL_PLANNER` (Haiku per-tool planner stage) | D |
| `W6-R3` | `M2_E1_PROVENANCE_AUDIT` (3 integrity audits) | F |

**Sync 4 already happened pre-W6-R2 (per execution plan).**

### Wave 7 — `KARN-W7-CLOSE` (2 sequential, not parallel)

| Run | Brief | Stream |
|---|---|---|
| `W7-R1` | `M2_E2_EVAL_HARNESS` (B.9 golden 50-query eval) | F |
| `W7-R2` | `M2_E34_CLOSE` (B.10 red-team + thin UI + M2 close + handoff) | F |

**Sync 5 between W7-R1 and W7-R2:** native reviews quality bar against master plan §1.

After Wave 7: M2 closed. Native opens M3.

## §6 — Native interaction protocol

Per wave (one Cowork conversation):

| Action | Time |
|---|---|
| Open new Cowork window, name it `KARN-W{n}-{SUMMARY}`, paste bootstrap | ~10 sec |
| Read orientation summary | ~30 sec |
| Open 3 terminal tabs, paste 3 kickoff prompts (one per `W{n}-R{m}`) | ~2 min total |
| Walk away. Sessions run autonomously. | ~1–2 days wall-clock |
| Read 3 closing summaries as briefs land | ~30 sec each |
| Type `close` to seal the wave | 5 sec |
| Read wave-close marker + next wave's bootstrap prompt | ~30 sec |

**Total native time per wave: ~5–10 minutes spread over 1–2 calendar days.**

Across 7 waves: ~35–70 minutes of native attention over 7–14 calendar days.

## §7 — Conflict resolution policy

Same as `M1_M2_EXECUTION_PLAN §5`. Disjoint paths by stream + migration numbering + concurrent-deploys-handled-by-Cloud-Run.

## §8 — When to update this protocol

Re-version when:
- Wave plan changes (new brief added, brief moved between waves)
- Naming convention changes
- Bootstrap procedure changes
- Close ritual changes

Use semver: 1.1 → 1.2 (additive), 2.0 (breaking).

---

*End of PROJECT_KARN_PROTOCOL v1.1. Companions: PROJECT_KARN_BOOTSTRAP.md (entry point), PROJECT_KARN_SESSION_LOG.md (audit trail).*
