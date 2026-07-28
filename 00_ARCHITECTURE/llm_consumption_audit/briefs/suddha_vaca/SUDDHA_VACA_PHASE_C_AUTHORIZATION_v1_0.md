---
artifact: SUDDHA_VACA_PHASE_C_AUTHORIZATION
canonical_id: SUDDHA_VACA_PHASE_C_AUTH
version: 1.0
status: ACTIVE — supersedes the Phase-0.2 Dvārapāla QUEUE-BEHIND ruling
created: 2026-07-27
authority: NATIVE DIRECTIVE (Abhisek), issued in Cowork after reading SUDDHA_VACA_REPORT_v1_0.md
amends: >
  00_ARCHITECTURE/llm_consumption_audit/briefs/suddha_vaca/SUDDHA_VACA_REPORT_v1_0.md §Phase 0.2.
  The Dvārapāla's QUEUE-BEHIND ruling was CORRECT but OVER-BROAD: it parked all of Phase C/D/E
  when only two of seven P0 lanes are actually entangled with PARISHODHANA. This authorization
  narrows the park to those two lanes and releases the other five.
---

# Śuddha-Vāca — Phase C/D/E Partial Authorization

## §1 — The ruling being amended

Phase 0.2 ruled **QUEUE-BEHIND**: Phases C/D/E wait for PARISHODHANA's 7 open PRs to land. The
evidence for that ruling stands — PRs #827/#828 edit `registry_bridge.ts` with a hunk adjacent to
the Ṣaḍbala block, and a third overlaps `ph_nimitta.py`. **That entanglement is real and is not
waived.** What is amended is its *scope*: the ruling blocked seven lanes when the evidence
implicates two.

## §2 — Authorized to proceed NOW (5 lanes, writer-side, disjoint from PARISHODHANA)

| Lane | Primary file | P0 items | Rebuild radius |
|---|---|---|---|
| `lane:bo-laksana` | `pipeline/orchestrator/writers/bo_laksana.py` | P0-5, P0-6 | **L2 → L5** |
| `lane:bo-sudarshana` | `bodha_writers/sudarshana_emitter.py` | P0-7 | L2 cascade |
| `lane:ka-convergence` | `brahmagyan/kala/l3_convergence.py` | P0-8 | **L3 → L5** |
| `lane:mi-darshana` | `pipeline/orchestrator/writers/mi_darshana.py` | P0-10 | L5 only |
| `lane:ph-nimitta-engine` | `services/ph_nimitta/engine.py` | P0-11 | **L4 → L5** |

Also authorized in this wave (one-line, no rebuild, closes a standing contamination hole):
`services/ph_phaladesa/engine.py:39` — narrow `PERMITTED_NARRATION_MODELS` to match its own
docstring (it currently permits `gpt-4o`/`gpt-4-turbo` while charter §J bans Anthropic and the
docstring says Gemini/DeepSeek only).

## §3 — REMAIN PARKED (2 lanes) until PARISHODHANA lands

- `lane:serve-shadbala` — `registry_bridge.ts` (P0-1..4). Blocked on PRs **#827 / #828**.
- `lane:ga-tajaka` — `ga_writers/ga_tajaka_writer.py` (P0-9, **L1 → L5**, widest radius).

Re-check PARISHODHANA PR state at the start of every wave. The moment those PRs land, these two
lanes are released **under the original brief with no further authorization needed** — the native
has pre-authorized them; only the entanglement blocks them.

## §4 — Concurrency protocol with the PARIPRAŚNA BUILD (PB) campaign

The native has authorized PB to kick off **in parallel**. Disjointness was verified at file level
before authorization:

- **PB touches:** `platform/src/app/api/pariprashna/**`, `platform/src/lib/pariprashna/lexicon.ts`,
  `platform/scripts/backfill_conversation_embeddings.ts` — Next.js / TypeScript.
- **Śuddha-Vāca touches:** `platform/python-sidecar/**` — Python writers, emitters, service engines.
- **Overlap: none.** PB's briefs name zero Śuddha-Vāca lane files.

Binding on BOTH campaigns while they run concurrently:

1. **Branch/worktree isolation.** Śuddha-Vāca uses `.worktrees/suddhavaca-*` and branch prefix
   `suddhavaca/`. PB uses its own. Neither campaign merges, rebases, or deletes the other's
   branches, worktrees, or stashes.
2. **Rebuild exclusivity — Śuddha-Vāca holds it.** ŚV performs destructive L1–L5 asset rebuilds.
   PB's lifecycle declares `REBUILD(scope-limited, usually none)`; for the duration of concurrency
   PB's rebuild scope is **NONE**. If any PB wave determines it needs an asset rebuild, it STOPS and
   the Pratinidhi/Dvārapāla coordinates rather than proceeding.
3. **`backfill_conversation_embeddings.ts` gate.** Before running it, PB must confirm it writes only
   to conversation/embedding tables and touches **no chart-asset table** under ŚV rebuild. If it
   touches any shared table, it waits for the ŚV rebuild wave to complete.
4. **Deploy lanes are separate.** PB deploys `platform` (Next.js). ŚV deploys the python-sidecar and
   — only once `lane:serve-shadbala` unparks — `amjis-mcp`. Neither deploys the other's target.
   Before any deploy, verify main contains no half-merged work from the other campaign.
5. **No cross-campaign file edits.** If a campaign finds a defect in the other's territory, it
   RECORDS it as a finding and hands it over; it does not fix it.

## §5 — Unchanged

Everything else in `SUDDHA_VACA_BRIEF_v1_0.md` remains binding verbatim: prime directives §1,
test-first discipline §5, snapshot-with-tested-rollback before every destructive rebuild §6,
proof-not-assertion §7, hard boundaries §9, acceptance criteria §10. The PRIME RULE stands —
truth over completion; PARKED-HONEST is a legitimate close.

The two parked lanes mean **acceptance criteria §10 cannot be fully met in this wave.** That is
expected and correct. Do NOT flip `CLAUDECODE_BRIEF.md` to COMPLETE until the parked lanes land and
every criterion holds. Close this wave as **PARTIAL — 5 of 7 P0 lanes VERIFIED-FIXED, 2 PARKED on
documented external dependency**, with evidence.

*End of authorization v1.0.*
