---
artifact: PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md
canonical_id: PARIPRASHNA_TARGET_ARCHITECTURE
version: 0.11
status: SUPERSEDED — superseded-by-decomposition 2026-08-19 (G0 close); frozen forensic/history record; never to be renamed
verified_against_tree: >
  2026-08-18 (v0.11 re-baseline): full as-built census against git HEAD
  (dfbdfe620), the PB campaign close corpus (REPORT_PB-1/2/3,
  PB_CAMPAIGN_CLOSE_v1_0, PURNATA_CLOSE_REPORT_v1_0 §9), and a LIVE MCP census
  (mcp_server_info: 125 tools served, catalog-1+t152+r653c2a1a98c8). The
  2026-07-27 SUPERSEDED-IN-PART warning is DISCHARGED: its predicted staleness
  is corrected in place throughout, marked [GROUNDED 2026-08-18]; §16.9 is the
  as-built census of record. Prior standing retained for provenance:
  2026-07-19 for PG-1/PG-2 corrections; then stale for MCP/retrieval/data-plane
  as of 2026-07-27 after the Retrieval Plane Elevation (W0–W6) + Residual
  Closure campaigns and the ŚUDDHA-VĀCA→PŪRṆATĀ arc landed post-freeze.
authored_by: Claude (Cowork) + Fable 5 sub-agents, in consultation with the native
opened: 2026-07-19
supersedes: none (new artifact)
purpose: >
  The master target-state architecture for the MARSYS-JIS portal: the two
  conversation channels (Paripraśna and MCP), the one shared engine beneath
  them, the registry and retrieval plane, the model plane, the data plane, the
  render architecture, register separation, and the prediction→calibration
  loop. This document is the single running record of every architectural
  decision, open fork, and rationale for this workstream. It is enhanced
  continuously; it is not sealed until the workstream closes.
scope_note: >
  This is a TARGET-STATE document. It describes what should exist, not what
  exists. Current-state facts appear only in §16 (Forensic Appendix) and in
  the "today" column of inventory tables, and are marked as such.
governing_principle: >
  Design the most effective architecture irrespective of effort and cost.
  Existing assets are reused only where they fit and are replaced without
  hesitation where they do not. The eventual architecture is sacrosanct.
---

# Paripraśna — Target Architecture (Master Document)

> ## ✓ SUPERSEDED BY DECOMPOSITION — 2026-08-19 (G0 close complete)
>
> The native ruled (NCD-2, 2026-08-18) that this document decomposes into a
> five-artifact set. The successor set is AUTHORED, red-teamed
> (`RED_TEAM_G0_v1_0.md`, PASS-WITH-FIXES), registered, and CURRENT:
> **`PARIPRASHNA_ARCHITECTURE_v1_0.md`** (normative, status CURRENT),
> **`PARIPRASHNA_ASBUILT_BASELINE_v1_0.md`**, **`PARIPRASHNA_DECISION_REGISTER_v1_0.md`**,
> **`PARIPRASHNA_VERIFICATION_MATRIX_v1_0.md`** — all in `00_ARCHITECTURE/` —
> plus the v0.12 package under `briefs/pariprashna_v012/`.
> Superseded at G0 close 2026-08-19, session PB-3-Bot. This file is the frozen
> forensic/history record — retained in place, never renamed (30+ inbound
> referrers inventoried 2026-08-18, including production code comments).

> ## ✦ v0.11 AS-BUILT RE-BASELINE + ELEVATION — 2026-08-18
>
> **The largest fact about this document changed between v0.10 and v0.11: the
> conversation layer it designs was BUILT.** The PB campaign (PB-1 DHĀRĀ →
> PB-2 SMṚTI → PB-3 SAMĪKṢĀ → PB-3.1), executed inside the
> SAMĀPTI/NIḤŚEṢA/PŪRṆATĀ arc, shipped the Paripraśna surface to production —
> the typed SSE protocol, the three-region turn, the canonical `message_parts`
> store, durable summaries, ring-buffer resume, the server-side register-leak
> lint, and the full prediction lifecycle — behind `PARIPRASHNA_ENABLED`
> (default-off in code, **ON in production** via Cloud Run env since
> `amjis-web-01218-4ng`). On 2026-08-01, C4-LOOP-LIVE-PROOF drove a real
> reading end-to-end against production with all six criteria live, observed
> mid-proof by an uncoordinated real user (`PURNATA_CLOSE_REPORT_v1_0.md` §9).
> **T-9 is resolved forward: served readings now exist.**
>
> What v0.11 does, per D-18/§21:
> 1. **Grounds** every stale current-state claim in place, marked
>    `[GROUNDED 2026-08-18]` — the RG-1 re-baseline the 07-27 banner called
>    for. §16.9 is the new append-only as-built census; the honest **fidelity
>    debt register** (what shipped thinner than designed) lives there too.
> 2. **Moves resolved-by-events forks out of §2** (OT-2, OT-7, OT-8, OT-10,
>    OT-11, OT-12 — each resolved by a governed campaign, cited) into §1.2.
> 3. **Elevates** (marked `[ELEVATION F5 v0.11]`): A-37…A-48 in §1.1 and the
>    §19.5 forward sequence — the beyond-acharya bar applied to what now
>    exists: live block fidelity, the remembering wave, the window-opening
>    ask, voice enforcement, honest-depth serving, pre-cutover hardening.
> 4. **Leaves genuinely-open forks open**, with sharpened leans marked
>    `[PROPOSED v0.11]` — the native rules; this pass recommends.
>
> **What has NOT happened, stated plainly:** PB-4 PŪRṆATĀ (the cutover —
> default flip, consult/consume retirement, flag deletion) has never run;
> AC-15 (the native's week-of-use gate) is therefore unreached; NO-LEAKAGE
> arm-1 (DB roles) remains 0% built; the conversational-calibration sink is
> ruled (DVA 55/79) but unbuilt; and the live wire renders every block as a
> paragraph — the acharya-grade typography (verse, table, gap ribbon,
> prediction card) is reachable only through fixtures. §16.9 and §19.5 carry
> the full list with owners.

> ## ⚠ SUPERSEDED-IN-PART — 2026-07-27 (MCP / retrieval / data plane) — **DISCHARGED by v0.11 (2026-08-18)**
>
> *This banner is retained verbatim as provenance. Every row below has been
> resolved in place; the "do not implement" injunction is lifted — §16.9 is
> the census that replaces it.*
>
> These registers were **inputs** to a build campaign that then shipped much of
> the target state and did not update them. **Several `[CORRECTED PG-1]`
> verdicts in §1.1 are now stale in the opposite direction** — they say
> "unbuilt" of things that deployed. To be verified by **RG-1** (the
> retrieval-grounding audit, `briefs/CLAUDECODE_BRIEF_RG1_RETRIEVAL_GROUNDING_v1_0.md`),
> **not trusted from this banner:**
>
> | Item | §1/§2 says | Landed reality (2026-07-27) |
> |---|---|---|
> | **A-03** projections | "UNBUILT" | **BUILT** — `full`/`compact`/`consult` profiles, single generator + CI parity gate. `marsys_drill` not the mechanism. |
> | **A-07** `prashna_ask` | "zero source hits; one door" | **BUILT & DEPLOYED**, but a **single-pass plan→floor→one-synthesis job** (poll via `prashna_status`), **NOT** the extracted agentic loop. Register-lint/sentinel-rewrite gates **not** on the route. |
> | **OT-2 / OT-10** | "open forks" | **RESOLVED in code** — job-handle polling; `full`/`compact`/`consult` scope-gating. |
> | **A-19** NO-LEAKAGE | arm-1 "0%" | **arm-2 BUILT** (runtime filter, both doors, closed a real fail-open seam); **arm-1 (5 DB roles) still 0%** — the critical gap stands. |
> | **OT-11** ledgers | three, unresolved | **`standing_predictions_read` reads `brahma_prospective_ledger`** — for *standing/prospective* predictions the ledger is resolved in code; the Mīmāṃsā *calibration* ledger is distinct. OT-11 is narrower than §18 frames it. |
> | **Tool surface** | "~118/120/139" | **88 `/health`, ~111 `tools/list`** and moving. |
> | **Classical-texts corpus** | not present | **NEW L0 surface (5 tools), NOT embedding-RAG** — `classical_text_chunks` has no vector column; topic-array + full-text. The tools' "semantic search" wording overstates the schema. |
> | **`dossier`** | not present | **Completeness-gated composition tool** — withholds verdicts until 100% coverage. **Its defeat is live**: naive agents pick `assess_*` over it, scoring 15–33% on the depth mandate. **The planner must route to `dossier`.** |
> | **Gochara/temporal + `bodha_mechanisms_get` + KP + introspection** | not present | **NEW live surfaces** (D-4a/D-5/D-4b + Elevation). Gochara operationally fragile (`DATABASE_URL not set`); `ganita_database_schema_get` is the surface to audit for the threat model. |
>
> **Meta-finding (outranks any single delta): the codebase is moving faster than
> this document can track — two grounding sweeps in one day were each stale
> within the hour, and this banner itself was overwritten once by a concurrent
> session mid-edit.** A frozen tool inventory is the wrong instrument. RG-1's
> durable output is the **`shape_delta` register** (how shipped ≠ designed) and a
> **live census at BIND**. `CURRENT_STATE §2` also lags git HEAD — ground against
> HEAD. **Do not implement §1.1, §2, §6.3–§6.5, §7.4, §8, §14A from the current
> text until RG-1 produces v0.11.**

> **How to use this document.** §1 and §2 are the live registers — settled
> decisions and open forks. They are the first thing to read and the first
> thing to update. Everything else is elaboration. When a fork in §2 is ruled,
> move it to §1 with its date and rationale, and update the affected section.
> Every substantive change appends to §20.

---

## §0 — Purpose, scope, and standing

### §0.1 What this workstream is

The build arc L0–L5 (Brahmagyan → Mīmāṃsā) is complete and sealed. The data
plane, retrieval layer, and MCP channel exist. What does not exist to standard
is the **conversation layer** — the surface through which a human actually
asks the instrument a question and receives a reading.

This workstream designs and builds that layer, and in doing so resolves a set
of accumulated architectural debts that the conversation layer cannot be built
correctly on top of.

### §0.2 What is in scope

- The portal as a whole (topology, surfaces, roles, entitlements).
- **Paripraśna** — the internal chat surface.
- The **MCP channel** — its projections, its composite door, its session model.
- The **shared engine** both channels sit on (planner, agentic loop, registry
  dispatch, envelope, gates).
- The **registry and retrieval plane** — one registry, generated projections.
- The **model plane** — multi-provider, tiered, health-aware.
- The **conversation and memory model** — canonical message store, summaries,
  recall.
- The **render architecture** — streaming protocol, layout, stability.
- **Register separation** — reader vs practitioner vs audit vocabulary.
- The **prediction → calibration loop** — the front door to L5 maturation.

### §0.3 What is out of scope

- The FROZEN orchestrator and the `WriterBase` contract (§N.2). Sacrosanct,
  untouched.
- The L0–L5 build DAG and its writers. Sealed.
- Chart computation itself. Owned by L1 and the sidecar.
- Doctrine campaign lanes (D-1.x, D-2) already closed. Their outputs are
  inputs here.

### §0.4 Workstream split (2026-07-19)

This design is being carried in **two parallel conversations** with a shared
decision register (§1, §2 of this document).

| Workstream | Owns | Artifact |
|---|---|---|
| **Paripraśna** (this conversation) | The portal chat surface, render architecture, conversation and memory, register separation, the Samīkṣā loop, and the system-wide topology. | This document. |
| **MCP channel** | The MCP surface, projections, profile selection, `prashna_ask`, alias cutover, MCP session semantics, envelope self-sufficiency. | `00_ARCHITECTURE/briefs/MCP_CHANNEL_WORKSTREAM_HANDOFF_v1_0.md` — self-contained; a fresh session needs only `CLAUDE.md` plus it. |

**Shared substrate belongs to neither.** The engine, registry, planner,
envelope and gates (§6.5) are consumed by both and redesigned unilaterally by
neither. Either workstream may raise requirements against them; changes are
recorded here.

**Rulings flow back to this document.** A fork ruled in the MCP conversation
moves from §2 to §1 here, with date and rationale, and the affected sections
are updated in the same edit. New tensions go to §18; new defects append to
§16. Forks currently owned by the MCP workstream: **OT-2, OT-5, OT-6, OT-7,
OT-10.**

### §0.5 Verification standing (binding since v0.5)

**Current-state claims in this document decay, and they decayed once already.**
v0.1–v0.4's §8.5 asserted that the two-process envelope mirror was
hand-maintained and that "the codegen lane never landed." Both were false when
written. Four counts were also wrong. See T-7.

**Therefore, binding at every version bump:**

1. **§16 is re-verified against the working tree.** Not spot-checked — walked.
2. **Corrections are made in place with the error visible** — original claim
   struck, marked `[CORRECTED]`, never silently deleted. §16 is append-only.
3. **The verification date is stated** in the frontmatter and in §16's header.
4. **A claim that has not been verified is marked as unverified**, not
   presented as fact. The "stated disclosure tiers" paraphrase in §13.4 is the
   model for this.
5. **Any session executing from this document re-checks the specific claims its
   work depends on** before acting. This document is a design of record, not a
   substitute for looking.

**Verified as of: 2026-07-19** (full sweep, post-adversarial-review; re-grounded
against the working tree/DB/infra by the **PG-1 grounding-audit wave** — 87 findings,
all verified ACCEPT by the Opus floor. PG-1 corrections are marked `[CORRECTED PG-1]`
with the driving finding id; new forensic defects are appended in §16.7; the audit
report is `PARIPRASHNA_GROUNDING_AUDIT_REPORT_v1_0.md` and the current-state system
description is `RETRIEVAL_SYSTEM_TRUTH_v1_0.md`).

**Re-verified as of: 2026-08-18** (v0.11 re-baseline — full as-built sweep
against git HEAD `dfbdfe620`, the PB campaign close corpus, and a live MCP
census; corrections marked `[GROUNDED 2026-08-18]`; census of record §16.9.
The DB-level items — role grants, PITR — were NOT re-probed live this pass
and carry their last-verified dates explicitly.)

### §0.6 Standing relative to other governance artifacts

This document does not override `CLAUDE.md`, `PROJECT_ARCHITECTURE_v2_2.md`,
`MACRO_PLAN_v2_0.md`, `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md`, or
`CAPABILITY_MANIFEST.json`. Where it appears to conflict with any of them, the
conflict is a defect in this document and must be raised, not resolved
silently in this document's favour.

It **does** supersede any prior chat-layer plan (`CHAT_V2_*` corpus) as the
forward-looking design of record. The `CHAT_V2_*` documents remain valid as
historical record and as the source of the red-team findings carried forward
in §16.

---

## §1 — Settled decisions register

Decisions ruled by the native. Each is binding until explicitly revisited.

| # | Decision | Ruled | Rationale / note |
|---|---|---|---|
| **D-01** | The internal chat surface is named **Paripraśna** (परिप्रश्न). | 2026-07-19 | Gītā 4.34 — *"tad viddhi praṇipātena **paripraśnena** sevayā"*: approach the knower with reverence, with thorough questioning, with service. Contains *praśna* so the Jyotish resonance carries, without colliding with Praśna Śāstra (horary) which must remain available for the actual technique. No namespace collision in the codebase. |
| **D-02** | `consult` and `consume` retire as names and as routes. | 2026-07-19 | Two placeholder names for one surface was itself a symptom of the split. Route becomes `/clients/[id]/pariprashna`. |
| **D-03** | The channels are **not** separately named. | 2026-07-19 | Paripraśna is the *capability*; portal and MCP are transports. Naming them separately re-entrenches the split being erased. |
| **D-04** | Exactly **two channels**: Paripraśna (portal login → chart → converse) and MCP (no portal login → any LLM client). | 2026-07-19 | No third channel is designed for or accommodated. |
| **D-05** | Cross-channel **conversation transcript portability is DROPPED**. | 2026-07-19 | History lives in Paripraśna only. Rationale: the MCP protocol makes client-side assistant text structurally unrecoverable, so "identical transcripts" was a promise the architecture could not keep. See §2/OT-6 for the residual question this leaves. |
| **D-06** | Paripraśna's own conversation history must nonetheless be **done to a high bar**. | 2026-07-19 | Durable summaries, RAG recall over deep history, branching, resume. §11. |
| **D-07** | **Evolve at the architecture level; replace at the component level.** | 2026-07-19 | The registry, envelope, doctrine, contracts and topology survive and are built upon. Most of the chat spine is replaced. Both statements are true; the framing is pre-agreed so that §12/§13 do not read as a betrayal of "evolve". |
| **D-08** | **One registry**, all tools, sole source of truth. Every serving surface is a **generated projection** of it. | 2026-07-19 | Native's formulation was "one registry organized for both channels"; the reconciled form is *one registry, many generated projections*, because Tier B/C model limits mean no single surface is ever served to everyone. Native assent to this reconciliation is pending — see §2/OT-7. |
| **D-09** | Guest model: a **guest is a user analyzing charts on the portal**. The native is a guest whose role is super-admin. Plain guests exist. | 2026-07-19 | Implies multi-user, role-differentiated, chart-entitlement-scoped access control as a first-class subsystem. |
| **D-10** | Prediction-candidate capture is **implemented, not deferred**, with a review surface carrying a notification badge. | 2026-07-19 | Native's own design instinct. Elaborated into **Samīkṣā** (§14). This is the front door to L5 leaving STRUCTURAL mode. |
| **D-11** | **Architecture is finalized before code changes.** Overall architecture first (portal + MCP + data plane + retrieval layer), then descend into Paripraśna. | 2026-07-19 | This document is that architecture. |
| **D-12** | Governing principle: design for effectiveness **irrespective of effort and cost**. Existing components are kept only if they fit. | 2026-07-19 | Explicitly stated by the native. Migration cost is confined to a single appendix and never shapes the design. |
| **D-13** | The streaming/render bar is **Claude Code and Gemini** — robustness and resilience of presentation. | 2026-07-19 | Qualified by §18/T-1: adopt their *choreography*, reject their *epistemic opacity*. |
| **D-14** | Internal register (layer names, asset ids, `MSR`, `SIG.*`, table names) **must not appear in user-facing prose**. | 2026-07-19 | Architectural fix, not a prompt fix. Applies **universally — to every user including the native**. §13. |
| **D-15** | **No audience tier. No depth parameter. Acharya-grade by default, always.** | 2026-07-19 | The legacy model had a tier structure; it was deliberately torn down and must not return. Extends §N.4 ("no audience tier — writers emit all rows; serve-time governs access") from the build layer to the serve layer. The tier idea smuggled in a false assumption: *that plain language means a lesser reading*. The opposite is true — a real acharya explains precisely in words the person can hold. Speaking plainly **is** the higher standard. Consequences: A-16 is struck; OT-9 closes; the engine signature loses `depth` and `tier`. §13.4. |
| **D-17** | **Sequencing inverts: build the render bet first, as a shim over the existing engine. Capture starts week one.** | 2026-07-19 | Adopted from the adversarial review. v0.1–v0.4 scheduled four phases of invisible substrate work in front of the native's actual daily pain, and validated the architecture's most falsifiable bet last — the exact conditions under which a rebuild stalls and gets torn down a second time. ~~P0' proves or kills the core bet in 3–4 weeks with a disposable shim, no monorepo, no store change, no planner work.~~ **[CORRECTED PG-1 — `PG1-C2-0001`/`PG1-C2-0008`, critical]** The "disposable shim over the existing engine, no planner work, **old route untouched**, 3–4 weeks" premise is **FALSE as scoped.** A pure translation shim can re-label the events that already exist but **cannot** emit `turn.open` *before the planner runs* — the one event §19.7's "work visible immediately" row (and the whole dead-air bet) depends on — because today no SSE stream exists until `runAdapterDispatch` at `route.ts:988`, *after* the planner (`:436`) and tool fetch (`:752`), and the two planner/bundle 422 bail-outs (`:447`, `:803`) are structurally incompatible with an already-open stream. Emitting `turn.open` early requires hoisting `createUIMessageStream`, moving planner+tool-fetch into the stream `execute` body, and converting both 422s to in-stream errors — **a reorder of the very route D-17 promises to leave untouched.** Four §12.3 events (`citation.define`, `block.commit`, `reasoning.open/close`, keyed `activity.upsert`) have no source and need NEW emission, and §19.7's "no `as any` in the writer path" row is violated at six existing sites. Honest estimate for the full §19.7 gate: **~6–9 weeks with a bounded route reorder**, not 3–4 weeks untouched. **Native's call (PC-2, unresolved — now OT-12):** (1) keep 3–4wk but descope P0' to the render bet only (accept `turn.open` ships *after* planning, defer the dead-air row — which does not prove the bet P0' exists to prove); or (2) keep the full gate at ~6–9wk with the route reorder. The render HALF is genuinely cheap (Streamdown already does it, `PG1-C2-0006`); the risk lives in the SSE/route half, not the render half. Prediction capture moves from P6 to week one, because every month of delay loses calibration data forever on multi-year windows. **A-01 (monorepo) demoted** from P0 gate to optional — its justification was obsolete (§8.5). **OpenRouter and Tier C descoped** from the target. §19, §19.7, OT-12. |
| **D-18** | **Verification standing: current-state claims are re-verified at every version bump; corrections are made in place with the error visible.** | 2026-07-19 | v0.1–v0.4's §8.5 was materially false when written, along with four counts. This is the repo's own GA.1 failure mode applied to an architecture document. §0.5, T-7. |
| **D-16** | **The session pin is renamed and restructured: it is a per-turn provenance stamp, not a session pin.** | 2026-07-19 | Native's challenge: §N.3 mandates delete-then-insert, so exactly one build of a chart exists in Postgres and there is no archive. **A pin therefore cannot pin** — it has no power to hold a conversation at an earlier build, because that build is gone. The construct is a *witness*, not a lock. Restructured accordingly: (a) renamed **provenance stamp**; (b) moved from mutable `mcp_sessions.state_json` to immutable per-turn `conversation_messages.metadata_json`; (c) drift is detected by comparing this turn's stamp to the previous turn's, needing no shared session state; (d) **copied into every prediction-ledger row at confirmation time, never referenced** — a ledger row is an immutable historical claim and must not point at mutable state; (e) removed from the engine's input signature — provenance comes **out** with the answer, since the engine reads current build state itself. Deletes a mutable shared-state construct and its §31.3 collision-mitigation complexity. §11.4. |

### §1.1 Design conclusions accepted into the architecture

These are not native rulings but design conclusions carried forward as the
working architecture. They are open to challenge but are the current baseline.

> **[GROUNDED 2026-08-18 — v0.11]** The PB campaign built most of this table.
> Rows carry an as-built tag where the state changed: **BUILT** (shipped as
> designed, cite), **BUILT-Δ** (shipped with a named divergence — ruled or
> debt, see §16.9), **BUILT-UNWIRED** (the module exists, nothing calls it),
> **OPEN** (still unbuilt). Untagged rows are design-only and unaffected.
> A-37…A-48 at the end of this table are the `[ELEVATION F5 v0.11]` additions.

| # | Conclusion | Section |
|---|---|---|
| A-01 | ~~pnpm monorepo with `@marsys/contract`; the hand-mirrored envelope is deleted.~~ **DEMOTED by D-17 (2026-07-19).** The mirror was already deleted and codegen'd before this document was written; the monorepo's entire justification was obsolete. Now: **extend the existing shim generator** toward full coverage (strangler, per the mandate the repo already adopted); wire `codegen:check` into CI (currently unwired — drift undetected). Monorepo is optional convenience, P5' or never. | §8.5 |
| A-21 | **Client-side block segmentation** with a stable-prefix parser; one markdown engine in the system. Server-side segmentation runs once post-stream, for persistence only. | §12.4 |
| A-22 | **The register lint is defanged**: rewrite (id-shaped tokens only) / redact-with-flag / telemetry. **Never fail-the-turn.** The primary defenses are clean evidence context and the structured citation channel. **[GROUNDED 2026-08-18 — BUILT as specified]** REWRITE / REDACT+FLAG / TELEMETRY verdicts, never fail-the-turn; internal failure degrades to pass-through + flag. | §13.5 |
| A-23 | **Sentinel failure handling specified**: 64-byte / 400 ms hold-back with flush-as-plain-text, tolerant grammar with normalization logging, per-model hallucination counters feeding tier review. | §12.9.1 |
| A-24 | **Transport resilience**: `Last-Event-ID` replay-from-seq over a ring buffer, snapshot fallback with disclosure, reconnect on `visibilitychange`, half-committed turns marked incomplete and excluded from prediction detection. **[GROUNDED 2026-08-18 — BUILT]** Redis-primary ring buffer (500 events, TTL 600s/180s) with verbatim seq-preserving replay, `snapshot.apply` + disclosure flag on eviction, 8s-visibility-stall reconnect, 60s-grace interrupted finalization, hollow-caret reconnect UX. Disclosed Δ: the resume tail is 400ms poll-based (no pub/sub), and a snapshot resume degrades citation grades to catalog by design. | §12.9.2 |
| A-25 | **Failure UX is a designed surface**, adopting the existing dead `classify-error.ts` rather than writing a new classifier. | §12.10 |
| A-26 | **Mobile is first-class**: tap-first citations, bottom sheets, `visualViewport` handling, touch scroll-break, mobile fixtures in the harness. | §12.11 |
| A-27 | **Accessibility is preserved and extended**, not added — the current `aria-live`-while-streaming pattern is correct and must survive the renderer rebuild. axe-core in the harness. | §12.12 |
| A-28 | **Cross-conversation, per-chart memory**, with `prior_reading` as its own citation kind that can never satisfy an acharya-floor requirement. | §11.5 |
| A-29 | **The instrument can ask**: clarification becomes a third planner outcome, triggered by scope-tuple confidence; drift and unresolved-window prompts. **[GROUNDED 2026-08-18 — BUILT-Δ]** Clarification is LIVE: the planner's `clarification_needed` streams the question as a committed prose block and the turn finishes clean — no more bare 422. Drift is LIVE as the reader-facing `flag{chart_rebuilt}`. **The unresolved-window opening — the highest-leverage of the three — remains OPEN**, and its precondition now exists (a live ledger with queryable `window_closed` rows). Elevated to A-42. | §6.6 |
| A-30 | **Calibration is gated on minimum-n, pooled across charts by default, reported as intervals**, behind an explicit collect-only phase. **[GROUNDED 2026-08-18 — honored]** The collect-only discipline held under pressure: PB-3's L-5 calibration write was PARKED rather than forced against a mismatched schema, then RULED (DVA 55: new `mimamsa_conversational_calibration` table; DVA 79: exact schema, COLLECT-ONLY confirmed, leak guard required) and remains deliberately unbuilt. Brier is computed and stored on the ledger row at resolution; nothing touches serving. | §14.6 |
| A-31 | **Compliance decay is designed for**: batch resolution, LEL-drafted outcomes, non-shameful lapsing, coverage reported alongside every score. **[GROUNDED 2026-08-18 — BUILT-Δ]** Batch resolution shipped first-class (keyboard H/D/P/U roving-tabindex queue, one submit); coverage stats ship with the neutral W-2 framing (resolved and unverifiable both "attended to", honest-null before any close); the badge is gold-dim, never red. LEL-drafted outcomes remain OPEN. | §14.7 |
| A-32 | **Disagreement is captured** as first-class rows; the engine re-retrieves rather than re-words, and never folds when the data supports it. | §14.8 |
| A-33 | **Sycophancy-drift defenses**: synthesis stateless w.r.t. user reactions, identical-question diffing, optimism-bias tracking. | §14.9 |
| A-34 | **Security, cost governance, durability**: injection containment, a middleware layer with rate limits and blocking spend caps, and a verified backup posture for the two irreplaceable tables. | §14A |
| A-35 | **The `audience_tier` residue is excised**, including the load-bearing prompt-template lookup that today produces different prose per tier. **[GROUNDED 2026-08-18 — substantially RESOLVED]** The load-bearing sites are gone (live-tree grep at HEAD 2026-08-18 — these files sit outside the PB close corpus, so cite the tree, not the reports): prompt-template keying excised (`lib/prompts/index.ts` header — "Templates are keyed by (query_class, strategy). `audience_tier` was excised"), the consult-route stamp removed (C-2 tier_excision / DG1 ruling, comment at `consult/route.ts:512`), no tier forwarded to MCP lookups. Residue is now type/comment-level across ~12 files plus the two JSON-schema `required` fields — cleanup, not a live D-15 violation. F-25g downgraded accordingly (§16.9). | §13.7 |
| A-36 | **Emotional register is a design input**: pacing, calibrated framing, calm gaps, attributive remedy language. | §13.8, §13.9 |
| A-02 | All 45 tool aliases are deleted; canonical naming is `layer_noun_verb`. `tool_name_bridge.ts` survives only for replaying persisted conversations. | §8.2 |
| A-03 | Three registry projections: MCP-full, MCP-compact (~25–35 umbrellas + `marsys_drill`), Chat (planner-filtered per turn). **[CORRECTED PG-1 — `PG1-R1-0001`/`-0002`/`-0003`, `PG1-R1-0005`]** Confirmed UNBUILT (server registers all tools unconditionally; `marsys_drill` in doc prose only). Sizing baseline corrected: the "one registry" is **119** `marsys://tool/*` URIs, served as **139** MCP tool names (alias layer), documented internally as a stale **120**, and audited at BIND against **113** — which is `CAPABILITY_MANIFEST.json`, a governance-artifact catalog, **not** an MCP registry (category error). The MCP-compact umbrella count must derive from 119, never 113/120. **[GROUNDED 2026-08-18 — BUILT-Δ]** Generated projections shipped as **`full` / `compact` / `consult` surface profiles** (`platform-mcp/src/generated/mcp_surface_profiles.generated.ts`, single generator + CI parity gate) — profile-scoped OAuth selects the surface; `marsys_drill` was NOT the shipped mechanism. Live census 2026-08-18: **125 tools served** on the full profile, `catalog_version = catalog-1+t152+r653c2a1a98c8` (`mcp_server_info` now reports the live registry count, retiring the stale-census defect class of F-25i). | §8.3 |
| A-04 | A `mutation: true` capability class is introduced; sidecar-served tools are pulled into the registry. | §8.4 |
| A-05 | `density_contract` becomes **mandatory** on every `CapabilityDescriptor`. | §8.6 |
| A-06 | One planner **pipeline**, not three planners: scope → route → constrained LLM synthesis → vidhi validator emitting a `PlanReceipt`. CR-28 closes with one intent classifier. **[CORRECTED PG-1 — `PG1-R3-0001`/`-0005`/`-0006`]** Reality is **worse than "three planners": FOUR planner surfaces, two live-but-incompatible** (`PipelinePlan` on the web consult route vs `VidhiPlan` on MCP `plan_retrieval` — the identical question yields two non-interoperating plan objects), **two dead islands** (`retrieval/router/`, `lib/vidhi/compiler.ts`). **`PlanReceipt` is absent from code entirely** (docs-only, zero `.ts` hits) — its de-facto shipped analogue is the MCP `VidhiPlan` + `CompletenessReceipt`. The unification is **week-scale integration debt, not a contradiction** (§9.5, `PG1-R3-0007`): ~80% already exists as `VidhiPlan`; the real cost is a total `tool_name↔primitive_id` namespace map + wiring the web route through the vidhi compiler (coupled to the same route reorder C-2 priced). Do NOT treat A-06 as blocked. **[GROUNDED 2026-08-18 — OPEN, materially advanced]** The unified plan type still does not exist. But the route reorder C-2 priced HAS happened (PB-1 forked `/api/pariprashna` with stream-first ordering), and **the acharya floor is now LIVE on Door 1**: `compileFloorForPlan` + `ensureB11WholeChartReadFloor` + `ensureDashaContextFloor` + budget arbitration run inside the production route — B.11 is enforced by compilation, not convention, exactly as §9.6 designs. The remaining unification is `PipelinePlan`↔`VidhiPlan` reconciliation (§19.5 wave 4). | §9, §9.5 |
| A-07 | **One agentic loop, two doors.** Extracted as a channel-agnostic service; MCP gets `prashna_ask`. **[CORRECTED PG-1 — `PG1-R3-0002`]** HALF-BUILT: the loop IS a standalone module (`synthesis/agentic_loop.ts`) but its **only** live caller is the web dispatch (route-coupled), and **`prashna_ask` has ZERO source hits** across `platform/src` + `platform-mcp/src` (the apparent matches were the substring of the *unrelated* horary tool `prashna_undertaking_get`). So **"two doors" is really one door** (web); the channel-agnostic second door is unbuilt. §18/T-2's "D-05 safe only if `prashna_ask` ships" is currently unmet. **[GROUNDED 2026-08-18 — BUILT-Δ]** `prashna_ask` is **BUILT & DEPLOYED** (live on the 125-tool MCP surface, paired with `prashna_status`), so the second door exists and T-2's condition is met — **but as a single-pass plan→floor→one-synthesis job returning a job handle, NOT the extracted channel-agnostic agentic loop this row designs.** Register-lint/sentinel gates are not on that route. The loop-extraction half of A-07 remains OPEN (§19.5 wave 4). | §6.3 |
| A-08 | **Neutral/canonical message store**: `conversation_messages` + `message_parts` child rows. Replaces the AI-SDK `UIMessage` blob. **[CORRECTED PG-1 — `PG1-R3-0003`, `PG1-D1-0002`/`-0003`]** PARTIAL & mis-specified: `conversation_messages` exists but parts are a `parts_json` **blob column** (GIN-indexed), **not** normalized `message_parts` child rows, and `UIMessage` remains live across ~10 surfaces (not replaced). Critically, **every conversation table is empty (0 rows)** while the same DB holds 276,206 `chart_facts` — so the `parts_json` migration is a **green-field schema-hardening problem (add the version discriminator now, before the first row), NOT the "unverifiable salvage against a legacy corpus" F-25e frames.** There is no corpus to shape-infer. **[GROUNDED 2026-08-18 — BUILT-Δ]** PB-2 SMṚTI built the child-row store as designed: `message_parts` (migration 467, closed kind enum `text | reasoning | tool_call | tool_result | citation | prediction_candidate | attachment`), `conversation_summaries` (468), `schema_version`/`model_id`/`provider` columns, transactional `writeTurn` with delete-then-insert parts (`lib/pariprashna/store/writer.ts`). The Δ, disclosed in `REPORT_PB-2.md` §3: **assistant turns only** — user/history messages still persist via the legacy `writeConversationMessages` path, and the route writes only three kinds (text, citation, prediction_candidate); tool_call/tool_result/reasoning are a named residual (`store/route_writer_adapter.ts`). | §11.1 |
| A-09 | Model plane: registry-as-data + live health plane + explicit Tier A/B/C + OpenRouter meta-provider + CachePlanner + reasoning-token accounting. | §10 |
| A-10 | ~~Session pin promoted from MCP-only to all conversations.~~ **RESTRUCTURED by D-16 (2026-07-19).** Now: a **per-turn provenance stamp** recorded on every assistant turn in both channels, copied immutably into ledger rows. Not session state. | §11.4 |
| A-11 | **The AI SDK transport is replaced** by a typed SSE event protocol with a purpose-built client reducer. **[GROUNDED 2026-08-18 — BUILT]** 15-event Zod-discriminated protocol (`lib/pariprashna/protocol/events.ts`, "a malformed event can never reach the wire"), typed emitter with zero `as any` and a calibration-leak guard on every write, reducer with append-only laws and seen-set dedup (`components/pariprashna/state/reducer.ts`). | §12.2 |
| A-12 | Stream semantics are **block-level**, not token-level; blocks commit and freeze. Stream protocol and storage schema are the same algebra. **[GROUNDED 2026-08-18 — BUILT-Δ]** Shipped, with the shipped vocabulary differing from the §12.3 sketch in named ways (pass seams added; `reasoning.open/close` became `role: prose|thinking` on `block.open`; `snapshot.apply` added) — full delta record in the §12.3 grounded note. | §12.3 |
| A-13 | Three-region turn layout: permanent stable-height Working region, append-only Answer region, post-settle Grounding region. **[GROUNDED 2026-08-18 — BUILT-Δ]** Shipped; the visual grounding region moved to the collapsible **right dock** ("Windows · Grounding") by native ruling 2026-07-27 — the in-flow region ③ is now an `sr-only` settle announcement. A ruled delta, not debt. | §12.5 |
| A-14 | **No virtualization.** Frozen-block memoization + `content-visibility` instead. **[CORRECTED PG-2 2026-07-19 — `PG2-X4-0006`, INVERTED from the PG-1 assumption + mislabel fixed]** PG-1's `PG1-Z1-A0001` left this "unaudited" and mislabelled it **A-13** (A-13 is the unrelated three-region layout row above; the memoization ruling is A-14, §12.7). X-4 audited it and found today's code is the **opposite** of A-14's target: `VirtualizedMessageList.tsx` IS live (imported by `AdaptiveMessageList.tsx`), while **both** replacement techniques A-14 mandates are absent — `content-visibility`/`contentVisibility` = zero hits in `platform/src`; `React.memo`/frozen-block memoization = zero hits in the message-list components (the only `memo` hit is a `useMemo` code comment, the only `frozen` hit an unrelated scroll-state comment). So the virtualizer A-14 says to *remove* is running, and neither replacement is built — a real target-vs-actual gap for the A-11/A-12/A-14 render work, not merely an unaudited assumption. (Same mislabel class as A-08's "A-26" slip, `PG1-D1-0001`.) **[GROUNDED 2026-08-18 — BUILT on the new surface]** The Paripraśna renderer implements A-14 exactly: `FrozenBlock` is memoized with an always-equal comparator ("no committed FrozenBlock may ever re-render"), no virtualizer exists on the new surface, and the reducer replaces only the targeted turn so a long thread streaming re-renders one `<Turn>`. The inverted legacy state persists only in the consult tree PB-4 retires. | §12.7 |
| A-15 | Citations: model emits sentinels; **server rewrites before the wire**; structured `citation.define` events; tier-projected rendering. **[GROUNDED 2026-08-18 — BUILT-UNWIRED]** The S-3 streaming rewriter (64B/400ms hold-back, tolerant grammar, hallucination counter — exactly §12.9.1) exists at `lib/pariprashna/citations/rewriter.ts` and **is not on the live route**: the route's only import from `lib/pariprashna/citations/` is the leak lint. Live `citation.define` events arrive post-hoc from the persistence write-through, so chips depend on prose already carrying `⟦n⟧` tokens nothing currently rewrites mid-stream. Wiring it is A-38 (§19.5 wave 2). | §12.9, §13.3 |
| ~~A-16~~ | ~~Three disclosure tiers — reader / practitioner / audit.~~ **STRUCK by D-15 (2026-07-19).** Replaced by: one reading, one register, audit detail as an **affordance** rather than a mode. | §13.4 |
| A-17 | Register enforcement is a **pre-commit server-side gate**, not a prompt instruction. **[GROUNDED 2026-08-18 — BUILT]** `lib/pariprashna/citations/register_leak_lint.ts` runs server-side pre-wire at two points (per-delta + whole-block commit backstop), with SIX hard pattern classes (signal ids, asset ids, table names, register acronyms with grammar-preserving subject swap, spelled-out register names, bare fact-id namespaces) plus near-miss telemetry — hardened by three real production leak classes caught and closed across PB-1/PB-2 hotfixes. The §13.5 streaming contradiction stands as predicted: a leak split across a delta boundary reaches the screen before the block-commit backstop scrubs it. | §13.5 |
| A-18 | Reader-facing vocabulary lives in the **capability registry** as a `register` block; missing labels fail CI. **[GROUNDED 2026-08-18 — BUILT-Δ]** `lib/retrieval/register_block.ts` landed; `resolveReaderLabel` is the route's only legal activity-label source (fallback + console warn on a missing label, Gate 11 [integrity]); 33 capabilities carry backfilled `reader_label`s (PB-1). Coverage across the full 119-URI surface, and the CI fail-on-missing rule, remain OPEN (§19.5 wave 3). | §13.6 |
| A-19 | NO-LEAKAGE is enforced four ways: DB role grants, registry flag, out-of-process ledger writer, CI canary. **[CORRECTED PG-1 — `PG1-D3-0004`, critical; `PG1-C1-0011`]** Arm 1 (DB role grants) is **0% built, not partial**: none of §7.4's five designed roles (`role_web_serve`, `role_orchestrator`, `role_ledger_write`, `role_jobs`, `role_sidecar`) exist in the live DB; a **single `amjis_app` credential** — the same one the web app serves every request with — holds full CRUD on `mimamsa_predictions` (384-row ledger with outcome data) and `mimamsa_calibration`, the exact two write surfaces `role_web_serve` is designed to be denied. Repo-wide grep for the five role names: zero hits. Treat NO-LEAKAGE arm-1 as entirely unbuilt before any production reliance (see F-25q, §7.4). **[GROUNDED 2026-08-18]** Arm-2 is now BUILT on both doors (runtime `filterLeakedCapabilities` per doctrine F-R7, surfaced as a count-only wire flag; plus the collect-only trio — serving-path manifest grep gate, `assertNoCalibrationLeak` on every emitter write, byte-identity probe — mutation-proven 6/6 in C4). **Arm-1 (the five DB roles) remains 0% built — the critical gap stands unchanged**, and is scheduled in §19.5 wave 5. | §14.6 |
| A-20 | Verification centres on a **streaming replay harness** with a zero-shift budget for settled content. **[GROUNDED 2026-08-18 — BUILT-Δ]** PB-1 shipped a 12-fixture, 8-gate Playwright harness. The Δ is serious and disclosed: PB-2's golden byte-equality gate was a **confirmed false-confidence proxy** (one hand-authored fixture, a test-owned reducer reimplementation, no real-stream capture — `REPORT_PB-2.md` §3.1, re-confirmed as SAMĀPTI F-33). B-PB8-BYTEEQ (PR #927) built the real capture + replay-compare, but per DVA Ruling 80 the capture flag stays OFF until the Ruling-54 standing-posture follow-on closes. A green gate that cannot fail is the §17 anti-pattern; this row is not done until capture is standing. | §17 |

**`[ELEVATION F5 v0.11]` — the beyond-acharya register.** The rows above
describe an instrument that streams honestly. The rows below describe the gap
between that and the commissioned bar: *a reading experience no other
conversational product can offer, with zero internal vocabulary, at
beyond-acharya depth.* Each is a design conclusion of this pass, open to
challenge like every A-row, and scheduled in §19.5.

| # | Conclusion | Section |
|---|---|---|
| **A-37** | **Live block fidelity — the wire must carry what the design promised.** Today every live block renders as a paragraph: `TableBlock`, `VerseBlock`, `GapRibbonBlock`, heading levels, prose roles (verdict/elaboration/caveat), and the inline `prediction_card` are reachable ONLY through fixtures, because `s1LiveAdapter` hardcodes `kind:'paragraph'` and the wire carries no block typing beyond `prose|thinking`. **A beyond-acharya reading is typographically structured** — a daśā table that arrives as a table, a BPHS verse set as a verse with its gloss, an honest gap as the calm ribbon T-5 mandates. Target: server-side commit-time block typing (the server owns the full block text at commit; classifying a committed block is deterministic and testable — this is NOT the §12.4 mid-stream segmentation trap, which stays client-safe), carried as `kind` + `role` on `block.commit`, rendered at final geometry. `prediction_card` becomes a first-class wire event carrying the structured candidate + part id — which is precisely the protocol change `capture.ts` names as the prerequisite for mounting the in-stream confirm affordance. One change unlocks three debts. | §12.3, §16.9 |
| **A-38** | **Citations become first-paint chips on the live path.** Wire the built S-3 rewriter into the route so `⟦cite:…⟧` sentinels rewrite to `⟦n⟧` + `citation.define` DURING streaming; the grounding summary becomes server-derived (counts, grade rollup, "composed from complete house coverage" when the floor's completeness receipt says so) instead of client-synthesized from a citation tally. The client-side rollup remains as the degrade path for snapshot resumes. This is the difference between grounding as decoration and grounding as the product's spine arriving in real time. | §12.9, §13.3 |
| **A-39** | **Every control is honest or absent.** The composer's Model and Length pickers currently ship selections that never leave the component; `length_tier` is accepted, echoed, persisted, and does nothing (`TODO(PB-4)`); three of four Depth choices collapse to `deep_dive`. **A control that does nothing is a trust defect in an instrument whose brand is honesty.** Target: plumb `model_id` and `length_tier` end-to-end (both already exist in `LiveSubmitOptions` and the route contract — this is wiring, not architecture), implement length shaping in synthesis, or remove the pill until it works. No third state. | §10.9, §16.9 |
| **A-40** | **Depth is derived, not defaulted.** `reading_depth` should come from the DR-8 scope tuple (interpretive/domain questions → deep floor + higher iteration cap; pinpoint factual → standard), not from a picker default that silently runs 16-iteration deep dives on "what time is sunrise". The scope classifier exists; the route already forces `dasha_context_required` on deep_dive. Serve the depth received visibly: the settled band's "Grounded in N sources" plus the completeness receipt IS the depth signal (design plan G4) — never two identical presentations for a 3-fact answer and a 40-fact dossier. | §9.2, §13.4 |
| **A-41** | **The remembering wave — the instrument that returns.** The built-but-unwired pgvector recall (`lib/pariprashna/recall/`) gets its caller: per-chart cross-thread recall surfacing prior conclusions as `prior_reading`-graded citations (already structurally barred from satisfying floors), with contradiction surfacing ("in March, under a prior build, I said X") made adjudicable by the D-16 stamp both readings carry. Plus the arrival line: one chrome line on thread open — current daśā year + open prediction windows — derived from L1/Kāla truth, never model-composed. P9's accrual bet, now cheap because every substrate row exists. | §11.5 |
| **A-42** | **The window-opening ask.** Before planning, the engine checks the ledger for `window_closed` rows whose domain overlaps the question; if found, it opens with one sentence — *"Before I answer: in March I indicated X for April–June. What happened?"* — with the one-tap outcome affordance attached, then answers in the same turn regardless of reply. This converts the loop's worst weakness (outcome-recording decay, §14.7) into its most natural moment, at the exact instant the user is already thinking about the domain. Every precondition shipped in PB-3: the ledger, the lifecycle, the resolve action, the Brier recorder. This is the single highest-leverage unbuilt feature in the architecture. | §6.6, §14.7 |
| **A-43** | **Voice is enforced, not requested.** Extend the shipped lint infrastructure from vocabulary to register: (a) a second-person-imperative detector on remedial-class blocks — "you should wear" flags; "the tradition prescribes" passes (§13.8, deterministically checkable, same defanged verdicts); (b) pacing as block policy for difficult findings — shorter committed blocks, uncertainty stated before severity, the calibrated phrase leading and the number one affordance away (§13.9, P6). The register eval (§17.5) scores difficult-topic answers for pacing and framing on the REAL persisted corpus that now exists. | §13.8, §13.9 |
| **A-44** | **Signal reader text, prioritized by observed reality.** The §13.6 editorial problem (573 machine-register signals, no reader-facing column) is now prioritizable by fact: citations persist as parts, so the top-cited signals are a SQL query, not a guess. Generate-review-freeze `signal_reader_text` for the observed top ~50 first; the citation card falls back to classical source + grade until covered — never the internal text. | §13.6 |
| **A-45** | **New engine layers surface at their earned tier only.** Since 2026-08-01 the engine beneath this surface gained a ruled, amended v4.1 promise layer (the marriage verdict: conditional / 0.450 MODERATE — the first production verdict set by a measured, classically-cited amendment), a v3 arc-solved transit engine whose calibration stamps are honestly `structural_prior` (PARIṢKĀRA), the KP sub-lord clock, and a unified fact-identity substrate. **The serving rule extends T-8 to every new layer: a verdict enters a reading with its tier named in reader language** — "held with moderate confidence, from the chart's structure" vs anything implying empirical validation that has not occurred. Beyond-acharya depth is these layers COMPOSED in prose; beyond-acharya honesty is never letting a structural prior wear a calibrated costume. | §14.6, T-8 |
| **A-46** | **Pre-cutover hardening is a PB-4 entry condition.** Before the default flip: (a) middleware + per-user rate limit + per-turn/daily spend ceilings on `/api/pariprashna` and `prashna_ask` (still absent; `maxDuration=120` and the QoS queue are not caps); (b) the Cloud SQL PITR/restore posture verified and drilled (last verified state: PITR disabled, no restore drill — F-25t); (c) `ANTHROPIC_API_KEY` provisioned or the stack removed from the selectable list (it fails instantly today, masked by the Gemini default). **A flagged surface without caps is an experiment; a DEFAULT surface without caps is an incident.** | §14A, §19.5 |
| **A-47** | **The reading returns as an artifact.** The sealed-reading export (design plan §10.6, OD-2(b)): a settled turn renders to a print-grade single-ivory-inversion document — the one thing a person shows their family after a consultation. Cheap (the turn is already an immutable parts row + grounding), high-signal, and the natural home of the D-16 stamp as a colophon ("read against the chart as built on …"). | design plan §10.6 |
| **A-48** | **Close the loop on disagreement before it costs another signal.** §14.8 remains fully unbuilt and the feedback endpoint still silently discards every rating (F-25c stands at HEAD). The dispute affordance now has a natural home (the dock card / turn menu), a natural store (a first-class row keyed to message_part + D-16 stamp, beside the prediction ledger), and a natural review surface (Samīkṣā). Re-retrieve, never re-word; never fold when the data supports the claim. | §14.8 |

---

### §1.2 Resolved-by-events register (new v0.11)

Forks from §2 that were resolved not by a ruling session against this document
but **by governed campaigns whose gates the native's own protocols ran**. Each
is recorded here with its mechanism and citation, per §21 rule 1; the §2 row
is struck in place. A resolution recorded here has the same standing as a §1
ruling — it was made under DVA/Pratinidhi authority inside a gated campaign —
but is kept in its own register so the provenance (code-first, not
document-first) stays visible.

| Fork | Resolution | Resolved by | Date |
|---|---|---|---|
| **OT-2** (`prashna_ask` transport) | **Option (c) — job handle.** `prashna_ask` returns `{job_id, status:'pending'}` immediately; `prashna_status` polls to progress/result. MCP progress notifications are best-effort, not relied on. | Retrieval Plane Elevation campaign; live on the production MCP surface | ≤2026-07-27 |
| **OT-7** (assent to generated projections) | **Resolved in code as generated surface profiles** — `full` / `compact` / `consult`, one generator, CI parity gate (`mcp_surface_profiles.generated.ts`). D-08's "one registry, many generated projections" reading won. | Retrieval Plane Elevation campaign | ≤2026-07-27 |
| **OT-8** (fate of `ConsumeChatV2.tsx`) | **Option (a) — rebuilt on canonical parts.** PB-1 built the new renderer from scratch (`components/pariprashna/**`); the consult tree survives untouched only as the pre-cutover fallback and is deleted by PB-4 F-5 per the refreshed census. | PB-1 DHĀRĀ (`REPORT_PB-1.md`) | 2026-07-28 |
| **OT-10** (who chooses the MCP path) | **Option (b) enforced by (c)** — connect-time surface profiles gated by OAuth scope. The `consult` profile exists as designed; `prashna_ask` requires the `full`/`compact` profile and is rejected for `consult`. | Retrieval Plane Elevation campaign | ≤2026-07-27 |
| **OT-11** (canonical prediction ledger) | **Resolved forward: `brahma_mimamsa_prediction_ledger` was BUILT** (migration 470) as the canonical conversational ledger — 9-state lifecycle, confidence `numrange`, window `daterange`, five frozen D-16 stamp fields, DB freeze trigger. `mcp_predictions` retired with backup (migration 471). The build-time `mimamsa_predictions` and `brahma_prospective_ledger` remain distinct by the provenance axis §14.1 endorses; `LEDGER_MAP_PB-3.md` is the authority map per caller. | PB-3 SAMĪKṢĀ, MEMO_PB-3_0 (`REPORT_PB-3.md`) | 2026-07-29 |
| **OT-12** (P0' scope: shim vs route reorder) | **Resolved by events as (b)-shaped: PB-1 built the FORK with the reorder** — `/api/pariprashna` opens the SSE stream and emits `turn.open` as the first bytes, before the planner; both 422 bail-outs became in-stream errors; the consult route stayed byte-identical (must_not_touch). The "3–4 week untouched-route shim" premise PG-1 struck was never attempted. | PB-1 DHĀRĀ (`REPORT_PB-1.md`; route header) | 2026-07-28 |
| **PARK_PB-3_L-5** (calibration sink schema) | **Option B ruled**: a new, separate `mimamsa_conversational_calibration` table (DVA Ruling 55), exact schema + COLLECT-ONLY + mandatory leak guard fixed by DVA Ruling 79. **Implementation deliberately unbuilt** — a future session proceeds directly from the rulings. | DVA Rulings 55/79 (`PARK_PB-3_L-5`, `PB_CAMPAIGN_CLOSE` §4) | 2026-07-31 |

---

## §2 — Open decisions register

The genuine forks. Each blocks something specific; none should be answered by
default.

> **[GROUNDED 2026-08-18 — v0.11]** Six forks resolved by events — struck
> below, recorded in §1.2. The remaining open forks carry sharpened leans
> marked `[PROPOSED v0.11]`; they remain the native's to rule.

| # | Fork | Blocks | Options | Lean |
|---|---|---|---|---|
| **OT-1** | **Where does the engine live?** | Deployment topology; `prashna_ask` timeout behaviour | (a) In-process with the Next.js web app; MCP edge calls its internal API. (b) Standalone engine service both call over HTTP. | (a) — the engine is TypeScript sharing the contract package, and process separation buys nothing until a second UI exists. Caveat: constrains long-running `prashna_ask` to Next.js execution limits. **[PROPOSED v0.11]** Confirm (a) as the standing answer and close: events chose it — the live route runs in-process with `maxDuration=120`, and `prashna_ask` sidestepped the execution-limit caveat via the OT-2 job handle. Reopen only if a second UI or a genuine long-loop requirement appears. |
| ~~**OT-2**~~ | ~~**`prashna_ask` transport semantics.**~~ **RESOLVED BY EVENTS — Option (c), job handle (`prashna_ask` → `{job_id}`, `prashna_status` polls). See §1.2.** | — | — | — |
| **OT-3** | **Jobs runner deployment shape.** | Ops surface; NO-LEAKAGE arm 3 | (a) Dedicated third deployable — clean role separation, one more thing to operate. (b) Cron-triggered routes inside the web app, with the **ledger writer** as the only separately-deployed worker. | (b). NO-LEAKAGE strictly requires only the ledger writer out-of-process; the rest is taste, and for a single-operator system every always-on subsystem is future 2 a.m. debugging. **[PROPOSED v0.11]** Confirm (b) and close: events chose it — the consolidated daily job (window-close + closing-soon + digest in one pass, PB-3 L-4, secret fixed in PB-3.1 G2) runs as a scheduled task, not a third deployable. The out-of-process ledger writer remains the arm-3 obligation and lands with arm-1 in §19.5 wave 5. |
| **OT-4** | **Guest build rights.** | Nirmāṇa authz model | (a) Guests may trigger a rebuild of their own chart. (b) Build execution is super-admin-only; guests are read-only on build state. | Undecided — this is a cost and failure-ownership question, not a technical one. Decides entitlement-scoped vs role-gated authz on orchestrator triggers. **[PROPOSED v0.11] (b) — build execution stays super-admin-only; guests read build state.** Rationale: a rebuild is expensive, destroys the prior build irrecoverably (§N.3, no archive — every open conversation silently drifts), and its failure modes land on the operator. A guest-triggered rebuild is an irreversible act performed by someone who does not own its consequences. Offer guests "request a rebuild" (a notification to the native), which preserves agency without transferring the trigger. Revisit only when a second operator-grade user exists. |
| **OT-5** | **MCP OAuth issuer.** | Identity spine; entitlement resolution | (a) Self-issued OAuth 2.1 in the edge — full control of token lifecycle. (b) Delegate to Firebase, edge as resource server — one identity spine, entitlements resolve from one user table with no mapping layer. | (b) is architecturally cleaner if Firebase can act as an OIDC provider for MCP clients; (a) is the current direction. Decides whether an MCP identity *is* a portal user or merely maps to one. **[PROPOSED v0.11]** Keep MCP-workstream ownership; recommend ratifying the shipped direction rather than re-litigating — the live edge serves Bearer-key + OAuth-profile auth in production and the cost of an issuer migration now exceeds its elegance dividend for a single-operator identity population. Revisit at the D-09 moment (a real second human). |
| **OT-6** | **Does the MCP channel get *any* durable memory?** | §11.5; whether MCP is a second-class channel | (a) None — raw tools + `prashna_ask`, stateless beyond the session pin. (b) Journaling tools so an MCP session's *questions and retrievals* persist even though assistant text cannot. | Flagged by §18/T-2: D-05 is safe **only if** `prashna_ask` ships. If A-07 were rejected, D-05 should be revisited. **[PROPOSED v0.11] (a) — close as "none," with T-2's condition now MET.** `prashna_ask` shipped (§1.2/OT-2), so D-05 stands on its own terms: the MCP channel has the instrument, not just the database. Journaling tools would add a durable-memory surface to the channel with the weakest containment story for marginal value; the one cross-channel durable memory that matters — the prediction ledger — already exists and is channel-agnostic by design. Reopen only on observed demand from real MCP sessions. |
| ~~**OT-7**~~ | ~~**Assent to "one registry, many generated projections."**~~ **RESOLVED BY EVENTS — generated `full`/`compact`/`consult` surface profiles, one generator, CI parity gate. See §1.2.** | — | — | — |
| ~~**OT-8**~~ | ~~**Fate of `ConsumeChatV2.tsx` (2,304 lines).**~~ **RESOLVED BY EVENTS — Option (a): PB-1 rebuilt on canonical parts; the consult tree is the pre-cutover fallback, deleted by PB-4 F-5. See §1.2.** | — | — | — |
| ~~**OT-10**~~ | ~~**MCP profile selection — who decides whether a query gets the engine or the raw retrieval plane?**~~ **RESOLVED BY EVENTS — (b) enforced by (c): connect-time surface profiles, OAuth-scope-gated; `prashna_ask` rejected on the `consult` profile. See §1.2.** | — | — | — |
| **OT-11** | **Which prediction ledger is canonical for the NO-LEAKAGE design?** *(raised PG-1 — `PG1-D3-0003`, F-25p; COSTED PG-2 — `PG2-X5-0001..0007`)* | §7.4 role design; NO-LEAKAGE arm 1; which table `role_ledger_write` gates | ~~Two disjoint ledgers exist: (a) `mimamsa_predictions` (L5 build-time, 384 rows, referenced by `mimamsa_calibration`/`phala_anchors`); (b) `mcp_predictions` (chat-side detector, 0 rows).~~ **[CORRECTED PG-2 2026-07-19 — `PG2-X5-0006`]** The landscape is **three** tables, not two: (a) `mimamsa_predictions` (L5 build-time, **384 rows**, referenced by `mimamsa_calibration`); (b) `mcp_predictions` (chat-detector interim relay, **0 rows**, migration 071, explicitly TODO-migrate); (c) `brahma_prospective_ledger` (D-4a §11 explicit-filing, **5 rows**). PG-1's "`phala_anchors` references `mimamsa_predictions`" is inexact (`PG2-X5-0003`): `phala_anchors` FKs point up to L3 kāla; the dependency runs the other way. `record_outcome` writes to **neither prediction ledger** — two same-sounding tools hit different tables (`record_outcome`→`phala_anchors`+`mimamsa_calibration`; `mimamsa_outcome_record`→`mcp_predictions`, `PG2-X5-0005`). | **Still OPEN — native's call, NO choice made (PC-8).** Now fully costed (`PG2-X5-0007`; full analysis `PG2_DIAGNOSTIC_REPORT_v1_0.md §7`). **NEITHER table satisfies §14.3 without a schema change** — none carries the `message_part_id` FK, `created_from_channel`, or 8-state lifecycle §14.3 mandates (`PG2-X5-0004`); §14.3's named `brahma_mimamsa_prediction_ledger` matches no live table. **Option A (merge into one canonical ledger):** unify incompatible types (`chart_id` text→uuid; `horizon` text→daterange; `confidence` text-enum→numeric for Brier), add the 3 missing §14.3 columns, reconcile 2 disjoint id namespaces, fold in `brahma_prospective_ledger`; rewrite `mi_bhavisya`/`mi_abhilekha`/`mi_pramana` + `ppl_writer` + `calibration_producer` + both `record_outcome` surfaces + count_sql; migration risk concentrated on the 384-row `mimamsa_predictions` (the sole calibration dependency). **Option B (keep all three + document):** no migration risk; ongoing cost is permanent reader confusion + §7.4 `role_ledger_write` still cannot name one physical table; needs a ledger-authority map + `record_outcome` tool disambiguation. The build-time-vs-conversational split is a **partially** principled provenance axis (§14.1 endorses it) tangled with 2–3 interim scaffolds. **[RESOLVED BY EVENTS 2026-07-29 — see §1.2.]** PB-3 built `brahma_mimamsa_prediction_ledger` (migration 470) as the canonical conversational ledger with everything §14.3 mandates (message-part FK, `created_from_channel`, the 9-state lifecycle, frozen D-16 stamp fields); `mcp_predictions` was retired with backup; `LEDGER_MAP_PB-3.md` is the per-caller authority map for the remaining principled split. The fork is closed. |
| **OT-12** | **P0' scope — render bet only, or the full §19.7 gate?** *(raised PG-1 — `PG1-C2-0001`/`-0008`, critical; the PC-2 call D-17 defers to the native)* | The entire P0' sequencing and its timeline honesty | (a) Keep 3–4 weeks, **descope** P0' to the render bet only — `turn.open` ships *after* planning, dead-air row deferred (does not prove the bet P0' exists to prove). (b) Keep the full §19.7 gate, **budget ~6–9 weeks** with a bounded `consult/route.ts` + dispatch reorder, dropping "old route untouched". | Native's call. What is NOT honest is claiming the full gate in 3–4 weeks with an untouched route. See D-17 correction, §19.7. **[RESOLVED BY EVENTS 2026-07-28 — see §1.2.]** PB-1 built the (b)-shaped answer: a FORK of the consult route with the full reorder — stream-first `turn.open`, in-stream faults, consult byte-identical. OT-12's fork is moot; the §19.7 gate rows are now assessed against the shipped surface in §16.9. |
| ~~OT-9~~ | ~~Sanskrit exposure policy at reader tier.~~ **CLOSED by D-15 (2026-07-19).** With no tiers, the question dissolves: Sanskrit is used where it *is* the substance (a yoga's name), glossed inline, **for everyone**. "Śaśa Yoga — Saturn strongly placed in its own sign in an angle." A layperson learns something; a practitioner reads past the gloss. One text serves both. | — | — | — |

---

## §3 — Naming canon

### §3.1 Locked (pre-existing, unchanged)

| Term | Meaning |
|---|---|
| Brahmagyan · Gaṇita · Bodha · Kāla · Phala · Mīmāṃsā | External names for L0–L5. **Never show "L0–L5" externally.** |
| `bg_* ga_* bo_* ka_* ph_* mi_*` | Per-layer asset-id prefixes. Dot-notation retired. |
| **Nirmāṇa** | The build tracker surface. |

### §3.2 New in this workstream

| Term | Meaning | Status |
|---|---|---|
| **Paripraśna** (परिप्रश्न) | The conversation capability, and the portal surface at `/clients/[id]/pariprashna`. | D-01, settled |
| **Samīkṣā** (समीक्षा) | The prediction review surface — "review, close examination". Per-chart tab plus a global dashboard roll-up. | Proposed, §14.4 |
| `prashna_ask` | The MCP composite tool exposing the agentic loop as one call. | Proposed, A-07 |
| `marsys_drill` | The single dispatcher tool in the MCP-compact projection that fans out to leaf capabilities via drill pointers. | Proposed, A-03 |
| `@marsys/contract` | The shared workspace package holding envelope, descriptor, receipt and scope types. | Proposed, A-01 |

### §3.3 Rejected names, with reasons (so they are not re-proposed)

| Candidate | Why rejected |
|---|---|
| **Saṃvāda** | Best semantic fit — the frame-dialogue form of Jyotish śāstra transmission — but `bo_samvada` already exists as an L2 asset id. Permanent grep and mental-model collision; the sealed layer forbids renaming it. |
| **Praśna** | Most Jyotish-native word available, but Praśna Śāstra is horary astrology, a distinct technique with an existing capability (`prashna_undertaking_get`). Naming the general chat surface Praśna forecloses the correct name for the actual feature. Reserved. |
| **Ākāśavāṇī** | Wrong register — oracular pronouncement without dialogue. Also the name of All India Radio. |
| **Pṛcchā** | Viable second choice ("the asking", the term Praśna Mārga uses for the querent's act). Shorter, slightly less resonant. Held in reserve. |
| `consult` / `consume` | Semantically poor placeholders; two names for one surface. Retired by D-02. |

---

## §4 — Topology (Context view)

```
                                        EXTERNAL WORLD
  ┌─────────────────┐   ┌──────────────────────┐   ┌───────────────────────────────┐
  │  Browser        │   │  MCP clients         │   │  LLM providers                │
  │  (guest /       │   │  (Claude, any LLM    │   │  Anthropic · OpenAI · Google  │
  │   super-admin)  │   │   client; no portal  │   │  · OpenRouter (meta-provider, │
  │                 │   │   login)             │   │    dynamic catalog)           │
  └────────┬────────┘   └──────────┬───────────┘   └──────────────▲────────────────┘
           │ HTTPS + Firebase       │ MCP protocol                 │ outbound only
           │ session                │ + OAuth 2.1                  │ (via ModelPlane)
═══════════╪════════════════════════╪══════ TRUST BOUNDARY ════════╪═════════════════
           │                        │                              │
  ┌────────▼────────────────┐   ┌───▼──────────────────────┐       │
  │  WEB APP  (deployable 1)│   │  MCP EDGE (deployable 2) │       │
  │  Next.js                │   │  no direct DB access —   │       │
  │  ┌────────────────────┐ │   │  isolation is the point  │       │
  │  │ Portal UI          │ │   │  ┌─────────────────────┐ │       │
  │  │ Paripraśna·Nirmāṇa │ │   │  │ OAuth 2.1 authz     │ │       │
  │  │ Samīkṣā·Cockpit·   │ │   │  │ Projections:        │ │       │
  │  │ Observatory        │ │   │  │  · MCP-full         │ │       │
  │  ├────────────────────┤ │   │  │  · MCP-compact      │ │       │
  │  │ API routes         │◄┼───┼──┤    (~30 umbrellas + │ │       │
  │  │ (serve the edge's  │ │   │  │     marsys_drill)   │ │       │
  │  │  internal API)     │ │   │  │ prashna_ask tool    │ │       │
  │  ├────────────────────┤ │   │  └─────────────────────┘ │       │
  │  │ ENGINE (shared     │ │   └──────────────────────────┘       │
  │  │  spine — §6):      │ │                                      │
  │  │  Planner pipeline  │ │   ┌──────────────────────────┐       │
  │  │  Agentic loop      │ │   │  @marsys/contract        │       │
  │  │  Registry+dispatch │◄┼───┤  (pnpm workspace pkg —   │       │
  │  │  Envelope builders │ │   │   NOT a process)         │       │
  │  │  Grounding gate    │ │   │  envelope types+builders │       │
  │  │  ModelPlane ───────┼─┼──►│  CapabilityDescriptor    │       │
  │  └────────────────────┘ │   │  density_contract        │       │
  └───────┬────────┬────────┘   │  trim-report · PlanReceipt│      │
          │        │            │  scope-tuple types        │      │
          │        │            └──────────────────────────┘       │
          │        │ HTTP (localhost/private net)                  │
          │   ┌────▼─────────────┐  ┌───────────────────────┐      │
          │   │ python-sidecar   │  │ JOBS (deployable 3,   │      │
          │   │ residual compute │  │  or cron-in-webapp —  │      │
          │   │ (Swiss Ephemeris │  │  fork OT-3)           │──────┘
          │   │  adjunct calcs)  │  │ · model-health probe  │  (probe calls providers)
          │   └────┬─────────────┘  │ · window-close daily  │
          │        │                │ · closing_soon −14d   │
          │        │                │ · email digest        │
          │        │                │ · summarizer worker   │
          │        │                │ · LEDGER WRITER (out- │
          │        │                │   of-process, sole    │
          │        │                │   mutation:true exec) │
          │        │                └───────────┬───────────┘
  ════════╪════════╪═══ DB GRANT BOUNDARY ══════╪══ (roles, §7.4) ═══════
          │        │                            │
  ┌───────▼────────▼────────────────────────────▼────────────────────────┐
  │  POSTGRES + pgvector (single cluster)                                │
  │  layer tables (bg/chart_/bodha_/kala_/phala_/mimamsa_) · asset_      │
  │  registry · conversation store · prediction ledger · model_health ·  │
  │  session pins · users/roles/entitlements                             │
  └──────────────────────────────────────────────────────────────────────┘

  Also inside WEB APP process: FROZEN orchestrator (WriterBase DAG driver, §N.2)
  + trace emitter → SSE. Firebase Auth is the browser IdP; OAuth 2.1 is the MCP
  IdP. The two auth surfaces never mix — that is why the MCP edge stays a
  separate deployable.
```

### §4.1 Invariants of this topology

1. **The MCP edge never touches the database.** It speaks only to the web
   app's internal API. This isolation is a security property, not an
   accident, and is the reason the edge remains a separate deployable even
   though the monorepo removes the code-sharing obstacle.
2. **`@marsys/contract` is a package, not a process.** It is compiled into
   every TS deployable. Its existence deletes the hand-maintained envelope
   mirror.
3. **LLM provider access is outbound-only and flows through the ModelPlane.**
   No component calls a provider directly.
4. **Only one component holds the ledger-write DB role** — the out-of-process
   ledger writer. See §7.4 and §14.6.

---

## §5 — Portal surface map

Grouped by minimum role. Fate tags: **KEEP / RENAME / MERGE / RETIRE / NEW**.

```
 PUBLIC (no auth)
 ┌───────────────────────────────────────────────────────────────────────┐
 │ /login ······································· KEEP                   │
 │ /reset-password ······························ KEEP                   │
 │ /share/[slug] ································ KEEP  (read-only chart │
 │                                                      share, tiered    │
 │                                                      disclosure)      │
 │ /panchang ···································· KEEP  (public daily    │
 │                                                      panchanga)       │
 └───────────────────────────────────────────────────────────────────────┘

 GUEST (any authenticated user; sees ONLY entitled charts)
 ┌───────────────────────────────────────────────────────────────────────┐
 │ /dashboard ··································· KEEP → chart list =    │
 │                                                entitlements + Samīkṣā │
 │                                                badge + build status   │
 │ /clients/new ································· KEEP  (create chart → │
 │                                                auto-entitled owner)   │
 │ /clients/[id]/pariprashna ···················· RENAME (consult →      │
 │     the conversation surface; threads,          pariprashna; consume  │
 │     streaming, in-stream prediction             MERGES into it — its  │
 │     confirm + one-tap outcome log)              reading views become  │
 │                                                 pariprashna panels)   │
 │ /clients/[id]/consume ························ RETIRE (merged above)  │
 │ /clients/[id]/nirmana ························ KEEP  (build progress; │
 │                                                 rebuild rights per    │
 │                                                 fork OT-4)            │
 │ /clients/[id]/timeline ······················· KEEP  (kala/phala      │
 │                                                 windows view)         │
 │ /clients/[id]/panchang ······················· KEEP                   │
 │ /clients/[id]/pratikruti ····················· KEEP  (chart imagery)  │
 │ /clients/[id]/edit ··························· KEEP  (birth-data edit │
 │                                                 → triggers rebuild)   │
 │ /clients/[id]/samiksha ······················· NEW   (Samīkṣā review  │
 │     tab: Awaiting confirmation / Open /         — per-chart scope;    │
 │     Resolve; can't-tell → unverifiable;         global roll-up lives  │
 │     badge counts on dashboard)                  on /dashboard)        │
 │ /settings ···································· KEEP  (profile, email  │
 │                                                 digest prefs)         │
 └───────────────────────────────────────────────────────────────────────┘

 SUPER-ADMIN (the native; guest + everything below)
 ┌───────────────────────────────────────────────────────────────────────┐
 │ /cockpit/* ··································· MERGE 12 → ~6 pages:   │
 │   · build command-center (command-center      (build orchestration is │
 │     + plan + parallel + activity → ONE)        one workflow, not four │
 │   · atlas ···································· KEEP  pages)           │
 │   · sessions ································· KEEP                   │
 │   · registry ································· KEEP → becomes the     │
 │       single registry browser: capabilities,   canonical registry     │
 │       density_contracts, projections diff      inspection surface     │
 │   · interventions ···························· KEEP                   │
 │   · health ··································· MERGE → observatory    │
 │ /observatory/* ······························· MERGE 10 → ~5:         │
 │   cost · cache · anomaly · pricing ··········· KEEP (consolidated)    │
 │   + model plane (model_health, tiers,          NEW panel              │
 │     probe history, quirks)                                            │
 │   + calibration observatory (Brier by          NEW panel — the L5     │
 │     domain, priors_version history)            loop made visible      │
 │ /admin/mcp ··································· KEEP  (keys, OAuth     │
 │                                                 clients, MCP health)  │
 │ /admin/trace ································· KEEP  (trace viewer +  │
 │                                                 PlanReceipt viewer)   │
 │ /admin/foundation, /admin/tracker ············ RETIRE (historical     │
 │                                                 build-arc surfaces;   │
 │                                                 arc is complete)      │
 │ /admin/users ································· NEW   (users, roles,   │
 │                                                 chart entitlements —  │
 │                                                 required by D-09;     │
 │                                                 nothing serves this   │
 │                                                 today)                │
 │ /dev/* ······································· RETIRE from prod build │
 └───────────────────────────────────────────────────────────────────────┘
```

### §5.1 What a plain guest actually sees

Login → dashboard listing *their* charts → per chart: Paripraśna, Nirmāṇa,
Timeline, Panchang, Pratikruti, Edit, Samīkṣā. No cockpit, no observatory, no
admin, no other charts.

**Enforcement is layered.** Route middleware enforces role; capability dispatch
re-enforces entitlement per `chart_id` at every call. UI hiding is never the
security boundary.

### §5.2 API surface consolidation

The ~160 current API routes collapse behind the engine: everything
conversational goes through the one conversation service; everything retrieval
goes through registry dispatch. Survivors are auth, entitlements,
build/orchestrator control, trace SSE, and admin CRUD. Target: well under
half.

---

## §6 — Request paths: two doors, one engine

### §6.1 The diagram

```
 DOOR 1: PARIPRAŚNA                        DOOR 2: MCP
 ═══════════════════                       ═══════════
 Browser                                   MCP client (any LLM)
   │ POST /api/.../pariprashna               │ MCP call
   │ (Firebase session)                      │ (OAuth 2.1 token)
   ▼                                         ▼
 ┌─────────────────────┐                   ┌──────────────────────────────┐
 │ AuthN + entitlement │                   │ MCP EDGE                     │
 │ check (chart_id)    │                   │ token → scopes → chart       │
 └──────────┬──────────┘                   │ entitlements                 │
            │                              │  ┌─────────────────────────┐ │
            ▼                              │  │ projection served to    │ │
 ┌─────────────────────┐                   │  │ this client:            │ │
 │ CONVERSATION SVC    │                   │  │  MCP-full │ MCP-compact │ │
 │ load thread from    │                   │  └───────┬──────────┬──────┘ │
 │ canonical store;    │                   └──────────┼──────────┼────────┘
 │ splice durable      │                       raw    │          │
 │ summaries (prefix-  │                       tool   │          │ prashna_ask
 │ stable) + RAG       │                       call   │          │ (chart_id,
 │ recall (pgvector)   │                              │          │  question,
 └──────────┬──────────┘                              │          │  scope_tuple?,
            │                                          │          │ response_format)
            │ question + context                      │          │ entitlement-
            │                                         │          │ gated,
            │              ┌──────────────────────────┼──────────┘ cost-capped
            ▼              ▼                          │
 ╔════════════════════════════════════════════╗      │
 ║              THE ENGINE                    ║      │
 ║                                            ║      │
 ║  PLANNER PIPELINE (one, not three)         ║      │
 ║  ┌──────────────────────────────────────┐  ║      │
 ║  │ 1 deterministic scope resolution     │  ║      │
 ║  │   → DR-8 scope tuple                 │  ║      │
 ║  │ 2 deterministic route classification │  ║      │
 ║  │   (D2 router as fast front; regex-   │  ║      │
 ║  │   first, LLM fallback — CR-28 closed)│  ║      │
 ║  │ 3 LLM plan synthesis, constrained    │  ║      │
 ║  │   by 1+2 output                      │  ║      │
 ║  │ 4 vidhi compiler = validator →       │  ║      │
 ║  │   PlanReceipt (echoed scope tuple,   │  ║      │
 ║  │   acharya floor + machine band,      │  ║      │
 ║  │   completeness receipt served/empty/ │  ║      │
 ║  │   dark w/ open CRs, capability_      │  ║      │
 ║  │   version + staleness kill)          │  ║      │
 ║  └───────────────┬──────────────────────┘  ║      │
 ║                  ▼                         ║      │
 ║  AGENTIC LOOP (channel-agnostic service)   ║      │
 ║  ┌──────────────────────────────────────┐  ║      │
 ║  │ provenance stamp (priors_version,    │  ║      │
 ║  │ formula_versions, ranking_config,    │  ║      │
 ║  │ build_id, now_context_date + drift   │  ║      │
 ║  │ detect) — per-turn, D-16             │  ║      │
 ║  │        │                             │  ║      │
 ║  │        ▼          ┌───────────────┐  │  ║      │
 ║  │  ModelPlane ─────►│ LLM provider  │  │  ║      │
 ║  │  (tier A/B/C,     │ (via registry-│  │  ║      │
 ║  │   health, cache   │  as-data +    │  │  ║      │
 ║  │   breakpoints,    │  model_health)│  │  ║      │
 ║  │   quirks.max_tools└───────┬───────┘  │  ║      │
 ║  │   → which projection)     │ tool     │  ║      │
 ║  │                           ▼ calls    │  ║      │
 ║  │  ┌─────────────────────────────────┐ │  ║      │
 ║  │  │ ONE REGISTRY  (source of truth) │◄┼──╫──────┘
 ║  │  │ CapabilityDescriptors, density_ │ │  ║   raw tool calls dispatch
 ║  │  │ contract MANDATORY, mutation:   │ │  ║   into the SAME registry
 ║  │  │ true class (never planner-      │ │  ║   (via edge → internal API)
 ║  │  │ callable in read context),      │ │  ║
 ║  │  │ canonical layer_noun_verb names │ │  ║
 ║  │  │ (45 aliases dead; tool_name_    │ │  ║
 ║  │  │ bridge = replay-only)           │ │  ║
 ║  │  └───────────────┬─────────────────┘ │  ║
 ║  │                  ▼                   │  ║
 ║  │  capability dispatch → SQL/pgvector  │  ║
 ║  │  → v3 ENVELOPE (density-layered,     │  ║
 ║  │    §N.6: verdict/grounding/drill_    │  ║
 ║  │    pointers/judgment_flags; response │  ║
 ║  │    budget w/ hardFloor trim)         │  ║
 ║  │        │                             │  ║
 ║  │        ▼                             │  ║
 ║  │  GROUNDING GATE (envelope-native):   │  ║
 ║  │  citation parts validated against    │  ║
 ║  │  in-turn envelopes; enforcement arm  │  ║
 ║  │  of §N.6 rule 3                      │  ║
 ║  └───────┬───────────────────┬──────────┘  ║
 ╚══════════╪═══════════════════╪═════════════╝
            │ Door 1            │ Door 2 (prashna_ask return)
            ▼                   ▼
 ┌─────────────────────┐   ┌─────────────────────────────┐
 │ STREAM events to    │   │ non-streaming result or MCP │
 │ browser (§12.3)     │   │ progress notifications;     │
 │                     │   │ epistemic annotations +     │
 │                     │   │ PlanReceipt in payload      │
 └──────────┬──────────┘   └─────────────────────────────┘
            ▼
 ┌─────────────────────┐   BOTH doors, always:
 │ PERSIST to canonical│   · PlanReceipt attached to the turn
 │ store: conversation_│   · trace emitted → SSE /admin/trace
 │ messages + message_ │   · prediction DETECTION runs on the answer;
 │ parts (canonical    │     candidates → human confirmation
 │ tool names, never   │     (Door 1: in-stream affordance;
 │ provider frames)    │      Door 2: Samīkṣā queue)
 └─────────────────────┘     → ledger via out-of-process writer

                           Tier C model variant: no tool schemas shown;
                           plan → platform executes → context bundle →
                           one fat prompt.
```

### §6.2 What is shared and what is not

**Shared by both doors:** the planner pipeline, the agentic loop, the
registry, capability dispatch, the envelope, the grounding gate, the session
pin, the ModelPlane, trace emission, and prediction detection.

**Door 1 only:** the conversation service, canonical message persistence,
durable summaries, RAG recall, and the streaming render protocol.

**Door 2 only:** OAuth resolution, projection selection, and MCP
serialization.

### §6.3 The `prashna_ask` rationale (fork #6, resolved as A-07)

The product contains an orchestrating brain: the loop that plans retrieval,
calls tools in dependency order, enforces B.11 (Bodha first), runs the
grounding gate, and writes a layered calibrated answer.

- **Without `prashna_ask`**, the MCP client's own LLM is the brain. It sees
  the tool surface, picks what it likes, may skip Bodha entirely — a B.11
  violation *invisible to us* — and may read `catalog_only` rows as confirmed
  findings if it ignores `judgment_flags`. Our envelopes are honest; the
  synthesis over them is not ours.
- **With `prashna_ask`**, the foreign LLM is demoted from astrologer to
  courier. It calls one tool, waits, and relays a finished layered reading.

D-05 (dropping cross-channel history) **strengthens** this case: a raw-tools
MCP session is now both stateless and brainless. `prashna_ask` restores the
brain even though the thread lives only client-side.

Raw tools remain available alongside — power users and Claude-Code sessions
want the drill surface. DR-5 is not reopened: the loop already exists
in-product; this is a second door on it, not a new brain.

> **[GROUNDED 2026-08-18 — v0.11]** `prashna_ask` SHIPPED (job-handle
> semantics — OT-2, §1.2) and the foreign LLM is demoted to courier as this
> section designs. One honest asymmetry remains: the shipped implementation
> is a single-pass plan→floor→one-synthesis job, not the shared agentic loop,
> and the register-lint/sentinel gates are NOT on its route — so §6.4's
> stage-9 row is currently ✅ for Door 1 and only partially true for
> `prashna_ask`. Re-basing it onto the extracted loop with the same gates is
> §19.5 wave 4.

---

### §6.4 Query lifecycle — there are three paths, not two

The topology diagram implies two channels sharing one engine. **The truth is
three paths sharing far less than that.** The dividing question is: *who owns
the synthesizing LLM?*

| Stage | Paripraśna | MCP raw tools | MCP `prashna_ask` |
|---|---|---|---|
| 1 Query origination | Browser composer | Client's chat window | Client's chat window |
| 2 AuthN + chart entitlement | Firebase session | OAuth token | OAuth token |
| 3 **Conversation context** (thread, summaries, RAG recall) | ✅ ours | ❌ none | ❌ none |
| 4 Provenance stamp | ✅ | ✅ | ✅ |
| 5 **Planning → PlanReceipt** | ✅ ours | ❌ **the client's LLM plans** | ✅ ours |
| 6 **Agentic loop** | ✅ ours | ❌ **the client's loop** | ✅ ours |
| 7 Registry dispatch → SQL → v3 envelope → budget | ✅ | ✅ | ✅ |
| 8 **Synthesis into prose** | ✅ our model | ❌ **their model, invisible to us** | ✅ our model |
| 9 **Pre-commit gates** (grounding, register lint, sentinel rewrite) | ✅ | ❌ **impossible** | ✅ |
| 10 Delivery | Streaming block events | Envelope JSON → their renderer | One payload / progress notifications |
| 11 Persistence (canonical parts) | ✅ | ❌ (D-05) | ❌ (D-05) |
| 12 Prediction detection | ✅ in-stream | ⚠️ tool traffic only | ✅ on the answer |

**Only stages 2, 4 and 7 are common to all three** — authentication, the
provenance stamp, and dispatch-to-envelope. Everything that makes the
instrument *an instrument* is ours in two paths and theirs in one.

**Paripraśna and `prashna_ask` are the same architecture** from stage 4
through 9 — genuinely one engine, differing only in what wraps it.
**Paripraśna and raw-tools MCP are not the same architecture at all.** They
share a data-access layer. Raw tools is best understood not as "the same
engine over a different transport" but as **"we expose our retrieval plane;
someone else's brain uses it."**

#### §6.4.1 Two guarantees that cannot cross to the raw-tools path

**B.11 is unenforceable there.** Whole-Chart-Read discipline lives in the
planner's acharya floor (§9.5). If the client's LLM plans, it can skip Bodha
entirely and we never know. The floor is a guarantee on *our* paths only.

**D-14 is structurally undeliverable there.** §13's entire architecture rests
on a pre-commit server-side lint over prose crossing our boundary. On the
raw-tools path **no prose crosses our boundary** — the client's LLM receives
internal-register envelopes (`SIG.MSR.413`, `bodha_msr_signals`,
`catalog_only`) and writes prose in whatever register it likes, in their
client, invisibly. **We cannot lint what we never see.**

Therefore **the envelope is the only defense on that path** — which
retroactively justifies the doctrine work. `judgment_flags`, honest coverage
with `total: null`, epistemic grades, `catalog_only_rows_present`, the density
contract: on our paths these are inputs to a gate we run; on the raw-tools path
they are the **entire** epistemic safety mechanism.

The design consequence: the envelope must be self-describing enough that a
foreign LLM reading it carefully gets it right, and visibly flagged enough that
one reading it carelessly fails **loudly** rather than silently. Worth
considering whether the `register` block's reader-facing labels (§8.7) should
ship *in the envelope* on that path, so a foreign model has plain-language
material to work from rather than only internal ids.

### §6.5 The engine boundary

**The engine is door-agnostic and lives outside both channels.** Paripraśna is
a browser-side wrapper; the MCP edge is a protocol-side wrapper; both call the
same engine. Retrieval, planning, the loop, the envelope and the gates belong
to **neither** channel.

```
 ┌─ PARIPRAŚNA (browser-side wrapper) ────────────────────┐
 │  composer · conversation service · thread history ·    │
 │  summaries + RAG recall · stream protocol · three-     │
 │  region render · Samīkṣā UI · canonical persistence    │
 └───────────────────────┬────────────────────────────────┘
                         │  ask(chart_id, question)
                         ▼
 ╔═══ THE ENGINE (shared, door-agnostic) ═════════════════╗
 ║  planner pipeline → PlanReceipt · agentic loop ·       ║
 ║  ModelPlane · registry + capability dispatch ·         ║
 ║  v3 envelope + response budget · grounding gate ·      ║
 ║  register lint · sentinel rewrite · prediction detect  ║
 ╚═══════════════════════▲════════════════════════════════╝
                         │  same call
 ┌───────────────────────┴────────────────────────────────┐
 │─ MCP EDGE (protocol-side wrapper) ─────────────────────│
 │  OAuth · profile + projection selection · prashna_ask  │
 │  raw tool dispatch · MCP serialization · session       │
 └────────────────────────────────────────────────────────┘
```

**The design test that keeps this honest: the engine must never branch on
which door it is serving.** If any code inside the engine asks "am I in chat
or MCP?", the boundary is in the wrong place.

**Corollary — the engine must be callable headlessly.** No browser, no
conversation row, no stream. That is what makes it testable, what makes
`prashna_ask` possible at all, and what would make a fourth consumer (a batch
job, a scheduled reading, an eval harness) trivial rather than a rewrite.

#### §6.5.1 OT-10 — who chooses the path?

**There is one MCP connection, not two channels.** `prashna_ask` is one tool
*within* the exposed set, alongside the raw retrieval tools. So when a user
types a question into an MCP client, **the client's model decides which to
call.** There is no routing logic of ours.

It may call `prashna_ask` and receive a full acharya-grade reading. Or it may
call `ganita_dashas_get` + `kala_windows_get` directly and synthesize its own
answer — bypassing the planner, the acharya floor (and therefore B.11), the
grounding gate, and the register lint.

**Same question, same connection, two radically different quality floors,
decided by a model we do not control.** This was never designed; it fell out
of "keep raw tools too."

The distinction that matters: raw tools are a **practitioner surface**
(drill-down investigation, debugging, research composition, deliberate bypass
by someone who knows what they are asking for); `prashna_ask` is the
**consultation surface** (someone wants a reading and should receive the
instrument, not the database). Leaving the choice to a foreign LLM's
tool-selection heuristics collapses that distinction at exactly the wrong
moment.

Note this is **not** an audience tier (D-15) — both paths are acharya-grade
where the engine runs. It is about *which mechanism answers*, not about giving
different people different quality.

Logged as **OT-10**; owned by the MCP workstream (§0.5). Lean: two connection
profiles selected at connect time, enforced by OAuth scope, adding a third
generated projection (**MCP-consult**) so a plain guest cannot accidentally
receive an ungrounded reading.

---

### §6.6 The instrument must be able to ask (new v0.5)

**Praśna śāstra is the art of the question. The surface named for Gītā 4.34's
*paripraśna* — "thorough questioning" — has, in v0.1–v0.4, no design for
questioning back.** Verified: the planner has exactly two outcomes, a
`PipelinePlan` or a 422 (`consult/route.ts:445–453`). **There is no state in
which the engine returns a question to the user** (§16.6).

A consultation surface should almost never interrupt. Three exceptions are
worth building, and all three are acharya behaviour:

**1. Material under-specification.** "Career change" — initiated by you, or
feared from outside? That is a real praśna distinction and it forks the
reading. **The trigger already exists**: the scope tuple's confidence score.
Below threshold on a *material* axis, the engine returns one clarifying
question instead of guessing. Design constraints: at most one question, never
two in a row, and always offer "just read it as asked" so the user is never
trapped. This becomes a third planner outcome —
`PlanReceipt | ClarificationRequest | PlannerFault` — and it is a small change
to a pipeline being rebuilt anyway (§9.2).

**2. Provenance drift mid-conversation.** If the chart was rebuilt since the
last turn, say so **before answering**, not in chrome. §11.4 renders drift as
ambient chrome, which is right for the passive case and insufficient when the
drift is material to the question being asked.

**3. An unresolved prediction window relevant to the current question.**
*"Before I answer — in March I indicated X for April–June. What happened?"*

That third one is the highest-leverage idea available to this architecture:
**it converts the calibration loop's worst weakness (outcome-recording decay,
§14.7) into a natural conversational moment.** The user is already thinking
about this domain; the window is already closed; asking costs one sentence.
Nothing else in the design solves compliance decay this cheaply.

Implementation seam: the engine checks the ledger for
`window_closed AND domain-overlaps(question)` before planning, and if found,
emits the clarification path with the outcome-capture affordance attached. The
answer follows in the same turn once the user responds — or immediately, if
they decline.

---

## §7 — Data plane

### §7.1 The diagram

```
 BUILD SIDE (write path — per chart)          SERVE SIDE (read path)
 ═══════════════════════════════════          ══════════════════════
 FROZEN ORCHESTRATOR (§N.2)                   ONE REGISTRY dispatch
 drives @register('<asset_id>')                 │ chart-scoped SELECTs
 WriterBase subclasses in DAG order             │ + pgvector search
 (writers never commit ctx.db_conn)             ▼
   │                                          v3 envelopes → engine
   ▼ delete-then-insert per (chart_id
      × natural key), §N.3
 ┌─────────────────────────────────────────────────────────────────┐
 │ L0 bg_*  Brahmagyan  → global reference tables (upsert)         │
 │ L1 ga_*  Gaṇita      → chart_facts · chart_dashas ·             │
 │                        chart_divisionals  (9 assets + service)  │
 │ L2 bo_*  Bodha       → bodha_*   (14 assets; bo_laksana root)   │
 │ L3 ka_*  Kāla        → kala_*    (12 assets)                    │
 │ L4 ph_*  Phala       → phala_*   (9 assets; D5 NO-SCORING gate) │
 │ L5 mi_*  Mīmāṃsā     → mimamsa_* (12 assets; STRUCTURAL mode —  │
 │                        calibration fills as outcomes accrue)    │
 │ asset_registry (count_sql per asset — cockpit truth)            │
 └─────────────────────────────────────────────────────────────────┘

 CONVERSATION STORE                    CALIBRATION LOOP
 ══════════════════                    ════════════════
 conversation_threads                  answer → detection →
 conversation_messages                 prediction_candidate part →
   (schema_version, model_id,          human confirm + elicited p →
    provider, metadata_json)           brahma_mimamsa_prediction_ledger
 message_parts                           │
   (seq, kind ∈ {text, reasoning,        ├─ daily job: window-close,
    tool_call, tool_result,              │  closing_soon @ −14d
    citation, prediction_candidate,      ├─ Samīkṣā tab + email digest
    attachment}, body jsonb,             ▼
    model_visible bool)                record_outcome (incl. can't-tell
 conversation_summaries (durable,       → unverifiable, Brier-excluded)
   family-worker summarizer,             │
   prefix-stable splice points)          ▼
 message embeddings (pgvector)         mimamsa_calibration → bumps
 provenance_stamps (build provenance)  priors_version in provenance stamp →
                                       epistemic annotations in
 IDENTITY                              phala/kala envelopes
 ════════
 users · roles(guest, super_admin)
 chart_entitlements(user × chart × grant)
 oauth_clients / mcp_keys
 model_health (probe results)
```

> **[CORRECTED PG-1 — `PG1-D3-0001`/`-0003`, F-25r/F-25p]** The diagram above is
> **target-state**; several of its table names do not exist in the live DB and must
> not be read as current. **Absent:** `brahma_mimamsa_prediction_ledger`,
> `brahma_mimamsa_answer_quality`, `brahma_phala_anchors`, and `message_parts`
> (parts are a `parts_json` blob column on `conversation_messages`, per A-08
> correction). **The real live tables:** `mimamsa_predictions` (384 rows — the L5
> orchestrator-built ledger `mimamsa_calibration` + `phala_anchors` actually
> reference), `phala_anchors` (384), `mimamsa_qa_eval` (147, the answer-quality
> analogue), `mimamsa_calibration` (0). **Two disjoint prediction ledgers exist**
> with no shared id space: this `mimamsa_predictions` (build-time, populated) and
> `mcp_predictions` (chat-side detector path, **0 rows**) — the "single ledger" the
> diagram and §7.4 NO-LEAKAGE design assume does not physically exist; §7.4 must
> name which table `role_ledger_write` gates.

> **[GROUNDED 2026-08-18 — v0.11]** The conversation-store half of this diagram
> is no longer target-state: **`message_parts` (migration 467),
> `conversation_summaries` (468), and `brahma_mimamsa_prediction_ledger` (470)
> all EXIST and are populated by production traffic**; `mcp_predictions` was
> retired with backup (471). The calibration-loop column is live through
> `outcome_recorded` with Brier stored on the ledger row; the
> `mimamsa_calibration` upsert at its foot is superseded by DVA Rulings 55/79
> (a NEW `mimamsa_conversational_calibration` table, ruled, deliberately
> unbuilt, collect-only). The identity block's `users/roles/entitlements` and
> the five-role grant boundary remain target-state (F-25q stands).

### §7.2 Build-side invariants (inherited, unchanged)

- **§N.2** — the orchestrator is FROZEN. New assets onboard by writing a
  `@register('<asset_id>')` `WriterBase` subclass; the orchestrator is never
  extended.
- **§N.3** — L1+ idempotency is per-chart delete-then-insert scoped to
  `(chart_id × natural key)`. Rebuild REPLACES, never accretes.
- **§N.4** — floors are aspirational, not gates; no audience tier at write
  time; deterministic-first; no JH-parity oracle; each asset carries a correct
  chart-scoped `count_sql`; surgical migrations only.
- **§N.5** — L1 is the authority over L2+ derivations. An L2+ signal
  references an L1 `fact_id`; it never restates a computed value as its own
  truth.

### §7.3 Serve-side invariants

- **B.11** — every query routes through L2 Bodha synthesis first, surfaces
  cross-domain signals, then produces its domain answer. Enforced by the
  planner's acharya floor (§9), not by convention.
- **§N.6** — the Serving Density Principle. Catalog matches are never
  presented as confirmed findings; the densest layer is protected first by the
  trim; the verdict layer is never empty when grounding exists; density
  signalling is data, not narration.
- **B.10** — no fabricated computation. `total: null` in a coverage stamp is
  the honest value.

### §7.4 DB role grants — the NO-LEAKAGE enforcement

```
 ┌──────────────────┬───────────────────────────────────────────────┐
 │ role_web_serve   │ SELECT layer tables, conv store R/W, pins R/W,│
 │  (web app engine)│ ledger SELECT-status-only. NO ledger INSERT/  │
 │                  │ UPDATE. NO mimamsa_calibration write.         │
 │ role_orchestrator│ INSERT/DELETE layer tables (build), asset_    │
 │  (build path in  │ registry/throughput write. No conv, no ledger.│
 │  web app proc)   │                                               │
 │ role_ledger_write│ ledger + outcome + calibration write. Held    │
 │  (jobs runner    │ ONLY by the out-of-process ledger writer.     │
 │  only)           │                                               │
 │ role_jobs        │ model_health write, summaries write, digest   │
 │                  │ reads.                                        │
 │ role_sidecar     │ minimal compute-support read.                 │
 │ (MCP edge)       │ NO ROLE — no DB connection exists.            │
 └──────────────────┴───────────────────────────────────────────────┘
```

The hard invariant: **`life_events` must never feed prediction generation,
only post-hoc calibration.** Four enforcement arms in §14.6.

> **[CORRECTED PG-1 — `PG1-D3-0004`, critical; F-25q]** The five roles above are
> **entirely target-state — 0% built, not partially built.** `pg_roles` on the live
> DB shows exactly one application role, **`amjis_app`** (plus Cloud SQL system
> roles); none of `role_web_serve`/`role_orchestrator`/`role_ledger_write`/`role_jobs`/
> `role_sidecar` exist, and a repo-wide grep for those five strings returns zero
> hits. `amjis_app` — the single credential `platform/src/lib/db/client.ts` uses for
> **every** web-serving request, including the consult chat route — holds full CRUD
> (SELECT/INSERT/UPDATE/DELETE/TRUNCATE) on `mimamsa_predictions` (the 384-row ledger
> with outcome data) **and** `mimamsa_calibration`, the exact two write surfaces
> `role_web_serve` is designed to be denied. **Today the serving credential can leak
> outcome data into new predictions — the NO-LEAKAGE invariant has no DB-level
> backstop.** Before any production reliance, either create the five roles + migrate
> the web app off `amjis_app` for read paths, or downgrade this section from an
> enforced invariant to an application-level convention. Also: §7.4 must name **which**
> physical ledger table `role_ledger_write` gates — two disjoint ledgers exist
> (`mimamsa_predictions` populated vs `mcp_predictions` empty; F-25p).

> **[GROUNDED 2026-08-18 — v0.11]** Arm-1 status unchanged: **the five roles
> remain 0% built** and the single-credential exposure stands. Two things
> changed around it: (1) the naming question is answered —
> `role_ledger_write` gates **`brahma_mimamsa_prediction_ledger`** (OT-11
> resolved, §1.2) plus the ruled-but-unbuilt
> `mimamsa_conversational_calibration`; (2) the application-level arms
> hardened materially — the runtime NO-LEAKAGE filter runs on both doors,
> `assertNoCalibrationLeak` guards every emitter write, and the collect-only
> canary/manifest/byte-identity trio is mutation-proven (C4, A6). That is
> defense-in-depth at the layer above this one, not a substitute for it.
> Arm-1 is scheduled with the out-of-process writer in §19.5 wave 5, and A-46
> makes it part of the pre-cutover hardening conversation.

---

## §8 — Registry and retrieval architecture

### §8.1 The governing statement

**There is exactly one registry (`platform/src/lib/retrieval/registry/`), it is
the sole source of truth for the tool surface, and every serving channel is a
generated projection of it.** Nothing is registered imperatively anywhere. The
MCP server's ~20 `register*Tools()` calls and its hand-maintained census
comment cease to exist. `tools served == descriptors registered` becomes a CI
assertion, not a comment.

### §8.2 Naming: kill all aliases

Canonical scheme is `layer_noun_verb` with the locked prefixes (`ganita_`,
`bodha_`, `kala_`, `phala_`, `mimamsa_`, `ref_`, `synth_`, `util_`, plus
`prashna_` for the composite door).

- All 45 aliases deleted; `register_p1_aliases.ts` deleted.
- The ~40 unprefixed legacy canonical names renamed.
- The 6 DEFERRED aliases resolved by renaming their targets canonically.
- One release, one breaking change. MCP has
  `notifications/tools/list_changed`; the client population is small and
  consented.
- `tool_name_bridge.ts` survives **only** as a historical legacy→canonical
  lookup for replaying old persisted conversations. New `tool_call` parts
  store canonical names from day one.

### §8.3 Three projections, all generated

The descriptor already carries `archetype`, `tool_role`, `traversal_level`,
`drill_children` — that *is* the facet metadata. Use it to generate surfaces
rather than to document them.

| Projection | Contents | For |
|---|---|---|
| **MCP-full** | Every capability, canonical names, full schemas. | Sophisticated clients; the native's own Claude-Code sessions. |
| **MCP-compact** | ~25–35 umbrella + graph tools, plus a single `marsys_drill(pointer)` dispatcher. Leaf tools reachable via envelope `drill_pointers` rather than individual registrations. | Clients and models that degrade past ~40–60 tools. |
| **Chat** | The agentic loop's per-turn set: the plan's tools plus their drill children. | The loop never needs the full surface in context. |

Which projection a session receives is a session/tier setting, driven by
`quirks.max_tools` (§10) — **not** a fork of the registry.

### §8.4 Mutation capability class

Introducing `mutation: true` on the descriptor union, which today assumes
read-retrieval. Properties:

- Writes ledger/outcome/calibration rows.
- Requires elevated entitlement.
- **Never planner-callable in a read context.**
- Carries `calibration_context_only` where applicable (§14.6 arm 2).

This is the correct home for `record_outcome` and the calibration writers, and
it is what allows the sidecar-served tools (`mimamsa_outcome`,
`phala_event_anchors` — currently marked "KEYSTONE REQUEST: no registry
primitive") to be pulled into the registry rather than bypassing envelope and
density discipline.

### §8.5 The two-process contract seam — CORRECTED 2026-07-19

> **⚠ This section was materially wrong in v0.1–v0.4 and is corrected here.**
> It claimed the envelope mirror was hand-maintained and "the codegen lane
> never landed." **Both claims were false.** The correction, and what it
> changes, follow.

**Verified current state (2026-07-19):**

| Claim in v0.1–v0.4 | Reality |
|---|---|
| `platform-mcp/src/lib/envelope.ts` is a hand-maintained mirror | **Does not exist.** Deleted; imports repointed. |
| The codegen lane never landed | **It landed.** `platform-mcp/src/generated/envelope.ts` (19.5KB) generated by `platform-mcp/scripts/generate_envelope.ts` |
| — | `platform-mcp/package.json` carries four scripts: `codegen:envelope`, `codegen:registry-shims`, `codegen`, `codegen:check` |
| — | `platform-mcp/scripts/generate_registry_shims.ts` also exists — **3 pilot instruments only, deliberately NOT wired in** |

**The governing mandate this repo already adopted** —
`RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md:538`, §19 *"The structural
finding: the two-process contract seam"*:

> **Design mandate (binding on W0): SINGLE-SOURCE CONTRACT GENERATION.** The
> facet schema for each instrument is declared ONCE, in the registry's
> CapabilityDescriptor. The MCP-side Zod shims and the name maps are GENERATED
> from the registry at build time (codegen step in CI), never hand-edited. A CI
> contract test round-trips every declared facet through the seam and asserts
> it altered the result. This replaces the §8 W0 line "request/response
> contract types" with something stronger: the contract has one home and the
> seam becomes mechanical.

And the **strangler discipline** that binds it, cited by the generator itself
(`generate_registry_shims.ts:4–6`, quoting brief §6.2):

> *"STRANGLER — migrate one instrument at a time, behind a parity gate; **no
> single PR regenerates the estate**."*

**What this changes in the target architecture:**

1. **The monorepo (A-01) is no longer load-bearing.** Its entire stated
   justification was "the mirror exists only because two repos cannot share an
   import." Codegen already delivers single-source contracts *across the
   process boundary without a monorepo*. **A-01 is demoted** from P0 gate to
   optional convenience (see §19). It may still be worth doing; it is no
   longer a prerequisite for anything.
2. **The path to D-08's "every serving surface is a generated projection" is
   to extend the existing shim generator** from its 3-instrument pilot to the
   full surface — incremental, already proven, and consistent with the
   strangler mandate. Not a workspace conversion.
3. **The big-bang cutovers proposed in v0.1–v0.4 contradict a mandate this
   repo already adopted.** §19's alias cutover ("one release, one breaking
   change") is re-specified as strangler migration in v0.5.

**One real gap the correction surfaces.** §19's mandate says "codegen step in
CI." `codegen:check` exists as an npm script and **no workflow invokes it** —
eight workflows exist (`ci.yml`, `chat-v2-ci.yml`, `chat-v2-smoke.yml`,
`tap-ci.yml`, `deploy.yml`, `brahma-conductor.yml`, `iac-apply.yml`,
`icr_weekly_scan.yml`) and none reference codegen. **Contract drift is
currently undetected.** Wiring `codegen:check` into CI is a one-line change
with outsized value and is now a P0' item (§19).

**Registry shims are generated but unwired.** The generated file states its own
status: *"LANDED ALONGSIDE, NOT WIRED IN (brief §6.2 strangler discipline):
these schemas are NOT imported by `register_p1_ganita.ts`'s live `server.tool()`
registrations."* Tool registration in `server.ts` remains fully imperative —
24 `register*` call sites, zero imports from `src/generated/`. So the
*mechanism* for D-08 exists and is proven; the *coverage* is 3 of ~120.

### §8.6 `density_contract` becomes mandatory

Currently declared by 6 of ~118 capabilities — a doctrine (§N.6) with 5%
enforcement. Make the field **required** on `CapabilityDescriptor`. For
trivially small tools the honest declaration is
`{paginated: false, facets: [], empty_reason: 'none_defined'}`.

Effect: the CI census harness anticipated by §N.6 Part 2 can assert byte caps
and facet/empty-reason coverage across the whole surface. A required field
with a legal "this tool is small" value costs an afternoon and converts §N.6
from prose into the type system.

### §8.7 The `register` block (see also §13.6)

Every descriptor additionally carries reader-facing vocabulary:

```ts
register: {
  reader_label: 'timing cycles',              // plain-language noun
  canonical_term: 'Vimśottarī daśā',          // the Sanskrit, used WITH a gloss
  reader_verb: 'Checked your timing cycles',  // activity-row phrasing
  id_namespaces: [{ pattern: 'SIG.MSR.*', reader_noun: 'chart indicator' }],
}
```

Note per D-15: `canonical_term` is **not** a practitioner-tier alternative to
`reader_label`. It is the correct term, surfaced alongside the gloss in one
text — "your timing cycles (Vimśottarī daśā)" — for every reader.

Adding a capability without register labels fails CI — the same discipline as
`count_sql`.

---

## §9 — The planner pipeline

### §9.1 The problem being solved

Three planners exist and are mutually ignorant:

- **D2 router** — deterministic, ordered-specificity, first-match-wins
  classifier into route classes + traversal level; optional injected-model
  fallback at low confidence; throws without `chart_id`; biases ERROR over
  fabrication.
- **`pipeline_planner`** — LLM-first, consumes the planner prompt + compressed
  manifest + a context window, emits a Zod-validated `PipelinePlan`, no silent
  fallback. This is what the live chat calls.
- **vidhi compiler** (behind `plan_retrieval`) — returns the echoed resolved
  scope tuple, the compiled acharya floor + machine band each naming live
  tool+args, a completeness receipt marking served/empty/dark with every
  `dark` citing the open CR that makes it a known gap, plus
  `capability_version` and a staleness kill.

Similarly, three intent implementations exist; **CR-28 is formally open**
because `util_intent_classify` returns a *prompt*, not a classification.

### §9.2 The architecture: a pipeline, not a choice

```
  question
     │
     ▼
  ① SCOPE RESOLUTION (deterministic)
     regex/rule first pass; LLM fallback only below confidence threshold
     → DR-8 scope tuple {intent, domains, width, depth, horizon,
                          intervention, entitlement}
     │
     ▼
  ② ROUTE CLASSIFICATION (deterministic)
     D2 router as the fast front — route class + traversal level;
     every rule logs its name; ERROR over fabrication
     │
     ▼
  ③ PLAN SYNTHESIS (LLM, constrained)
     pipeline_planner's LLM stage, re-targeted to emit a vidhi-shaped plan.
     The LLM may ADD to the machine band; it may NEVER subtract below the
     acharya floor.
     │
     ▼
  ④ VALIDATION + RECEIPT (deterministic)
     vidhi compiler validates any plan regardless of origin and issues the
     PlanReceipt: echoed scope tuple · acharya floor + machine band ·
     completeness receipt (served/empty/dark, dark cites its open CR) ·
     capability_version + staleness kill
     │
     ▼
  PlanReceipt  ──►  agentic loop  (and, over MCP, plan_retrieval returns it)
```

**All three existing planners survive as stages. None survives as a standalone
planner.** What dies is their mutual ignorance.

### §9.3 Why the vidhi output contract wins

It is the only planner whose output is auditable and honest about its own
gaps. It is the planner equivalent of the v3 envelope. `plan_retrieval` (MCP)
and the chat loop consume the identical `PlanReceipt` type.

### §9.4 CR-28 closure

One intent classifier, one output type (the scope tuple), two internal stages
(deterministic first pass, LLM fallback). The L0 `intent_classify` prompt
template is retired or retained purely as the fallback's prompt asset. The
regex-first bulk-context classifier's cheap wins are absorbed into stage one.

### §9.5 What the unification actually costs (new v0.5)

v0.1–v0.4 said "all three planners survive as stages" as though the work were
re-wiring. **It is not.** The three components are the easy 30%.

The vidhi compiler was built to **compile** floors from a scope tuple. §9.2
stage ④ re-purposes it to **validate any plan regardless of origin** and emit
a `PlanReceipt`. Validating an LLM-synthesized `PipelinePlan` — a different
type, from `pipeline_planner`'s Zod schema — against a vidhi floor **requires a
common plan algebra that does not exist today.**

Building that algebra *is* the planner unification. Until the common type is
designed, this is three planners plus a coordinator, which is four planners.

**Therefore the P2' deliverable is the unified plan type, specified first, in
the contract package** — not the pipeline diagram. Concretely it must express:
floor items and machine-band items as one addressable set; per-item served /
empty / dark with CR references; tool + args resolved against
`capability_version`; and a subsumption relation so "does this plan satisfy
that floor?" is decidable rather than argued. **If that type is hard to write,
the unification is not ready** — and discovering that early is cheap.

> **[CONFIRMED + SHARPENED PG-1 — `PG1-R3-0007`, the falsification exercise (PC-3)]**
> The unified plan type was actually sketched and stress-tested this wave. **Verdict:
> WEEK-SCALE INTEGRATION, NOT A CONTRADICTION** — and the claim "the common plan
> algebra does not exist" is **~80% wrong**: it already exists, unrecognized, as the
> MCP `VidhiPlan`. `completeness_receipt.ts`'s `uniqueFloorItems()` already collapses
> `[...floor, ...machine_band]` into one deduped addressable set keyed by
> `primitive_id`; served/empty/dark with OPEN/LOGGED `cr_row` is done; tool+args
> resolve per `CompiledFloorItem.live_tool` + `compileContract(chart_id)`, versioned
> by `VIDHI_CAPABILITY_VERSION`; a `subsumes` relation over `primitive_id`
> set-containment is trivially decidable. The **real cost (5–8 days)** is three
> non-fatal gaps: (1) a total `tool_name↔primitive_id` namespace map + its CI proof
> — the web `PipelinePlan` keys on `tool_name` (R-alias names) while `VidhiPrimitive`
> keys on bare `live_tool` names, an overlapping-but-distinct namespace; (2) promoting
> the free-text `llm_extension_note` band-3 to addressable `PlanItem`s; (3) wiring the
> web consult route through the already-built vidhi compiler to emit the unified plan
> — **coupled to the same `consult/route.ts` reorder C-2 priced** (§19.7, D-17). The
> only contradiction candidate ("a deterministic floor cannot contain a
> non-deterministic LLM plan in one set") resolves: LLM items are additive-only and
> `subsumes` ignores them, preserving floor determinism. **A-06 is integration debt,
> not a design impossibility — do not treat it as blocked.**

### §9.6 The acharya floor as the B.11 enforcement point

B.11 (Whole-Chart-Read discipline) currently rests on convention. In the
target it rests on the floor: a plan that does not consult Bodha does not
validate. This is also what makes the Tier C path (§10.4) safe — with no
drill-on-demand, the floor must be complete up front.

---

## §10 — The model plane

### §10.1 Starting point

A capability-tiered model registry **already exists** (`lib/models/registry.ts`,
~1,365 lines) with per-model `quirks` (`tool_use_format`,
`structured_output_format`, `cache_strategy`, `system_prompt_shape`,
`reasoning_via`), tiers, stacks, and call-type routing. It is a good design
being eroded by ops drift: dead models preserved as long comment blocks,
smoke-test results fossilized as source comments, a default flipped by credit
exhaustion.

**Missing:** OpenRouter, explicit tool-calling tiers, tool-count limits, live
health state, reasoning-token accounting.

### §10.2 Registry-as-data plus a live health plane

`ModelMeta` moves ops facts out of comments:

- `status: 'live' | 'degraded' | 'dead' | 'deprecated'`
- `last_probed_at`
- populated by a scheduled probe job writing to a `model_health` table.

The static registry holds declarations only. The picker and dispatcher read
`declared ∧ probed`.

### §10.3 Explicit capability tiers

| Tier | Definition | Treatment |
|---|---|---|
| **A** | Native parallel tool calling, ≥64 tools, streaming tool deltas. Claude family, GPT-4.1 family, Gemini 2.5. | Full agentic loop; full or route-filtered tool set. |
| **B** | Tool calling works but constrained — serial-only, unreliable past ~20–40 tools, or flaky argument JSON. DeepSeek, most OpenRouter mid-models. | MCP-compact-style projection: umbrellas + `marsys_drill`. Planner pre-selects ≤ `quirks.max_tools` per turn. Schema-repair retries on malformed args. |
| **C** | No reliable tool calling (`tool_use_format: 'none'`). | See §10.4. |

### §10.4 Tier C, operationally

The model **never sees tool schemas.** The pipeline runs as separate calls:

1. The unified planner (§9) runs on a Tier A/B **worker**, regardless of the
   user's synthesis-model choice, and produces the `PlanReceipt`.
2. The platform executes the plan's tools itself.
3. Results assemble into a context bundle.
4. The Tier C model receives one fat prompt (bundle + question) and writes
   prose.

No mid-answer tool use, therefore no drill-on-demand — which is exactly why
the acharya floor must be complete up front (§9.5). **Tier C is not a degraded
hack; it is the pipeline architecture with the loop's inner iteration count
set to 1.** It is also the practical path to "many models via OpenRouter."

### §10.5 OpenRouter as a meta-provider

- One adapter, `provider: 'openrouter'`, with a **dynamic** model catalog
  fetched from `/models`.
- Declared `supported_parameters` map to a provisional tier; default Tier B
  until a probe promotes to A.
- Cost accounting reads OpenRouter's per-request `usage` plus their pricing
  metadata, requiring a `cost_source: 'static' | 'reported'` discriminator.
- `cache_strategy: 'none'` always — no caching guarantees pass through.

### §10.6 Dialect and streaming normalization

- The **canonical message store (§11.1) is the replay normalizer.** Adapters
  map canonical parts → provider frames per `quirks.tool_use_format`.
- Streaming normalizes into the §12.3 event vocabulary, including a reasoning
  block lifecycle fed by `reasoning_via: 'native'` (Gemini/Anthropic extended
  thinking) or by `<think>`-extraction middleware (DeepSeek) — one reasoning
  surface regardless of source.

### §10.7 Reasoning tokens

Add to quirks:

- `reasoning_replay: 'signature' | 'text' | 'drop'`. Anthropic requires
  signature blocks replayed intact **within-provider**; cross-provider replay
  always downgrades to text-summary or drop. This is a canonical-store rule.
- `reasoning_tokens` as a separate cost line on the cost part and in
  `metadata_json` — they bill as output but are not visible output, so cost
  is otherwise silently wrong on exactly the models used for hard judgments.

### §10.8 Prompt caching

A **CachePlanner** inserts breakpoints per family given the assembled prompt:

- **Anthropic** — `cache_control` markers after (system + tool schemas) and
  after (chart bundle).
- **OpenAI** — prefix stability only; order the prompt so stable sections
  lead.
- **Gemini** — explicit context-cache object for the chart bundle keyed by
  `(chart_id, build_id)` with TTL; the session pin's build-drift detection is
  the natural invalidator.

**Critical interaction:** history compression must only ever mutate the
tail-ward end of the prompt, never the cached prefix (§11.3). Violating this
silently zeroes cache hits at exactly the moment conversations get long and
caching matters most.

### §10.9 Mid-conversation model switching

- A switch is a new turn with `model_id` changed.
- The replay assembler renders canonical history for the target dialect: tool
  calls re-encoded, foreign reasoning downgraded per §10.7.
- Per-turn `model_id` on the message row records attribution (today only
  last-assistant metadata carries it).
- A model-switch marker renders the seam in the UI.
- **Tier transitions** are the hard case: switching down to Tier C mid-thread
  means prior tool traffic replays as text (fine), but the new turn runs the
  Tier C pipeline. The user sees a one-line notice that drill follow-ups will
  be slower and coarser.

### §10.10 Operational caution

Noted in §18/T-3: a live health plane, probe scheduler, and dynamic OpenRouter
catalog are **ongoing operational** surface, not one-time build. For a
single-operator system every always-on subsystem is future 2 a.m. debugging.
Keep it to one probe job and one table. The model plane serves the instrument;
it is not the instrument.

---

## §11 — Conversation and memory

### §11.1 The canonical message store

**Today:** `conversation_messages.parts_json` holds the Vercel AI SDK
`UIMessage.parts` array verbatim. This is *framework*-native, not
provider-native, and has three defects:

1. **Pinned to a churning external schema with no version stamp.** The SDK's
   v4→v5 tool-part rename means every stored conversation is a fossil in
   whatever SDK version wrote it; a future upgrade either silently misparses
   or forces an unverifiable lossy migration.
2. **Model context and UI presentation are conflated.** Custom data parts
   (stage, cost, observability) sit in the same array the replay path feeds
   toward the model, depending on an unowned filter to keep telemetry out of
   the prompt.
3. **The blob is opaque to the database.** Citations, tool calls and
   prediction candidates cannot be indexed; embeddings take only the first
   text part; the ledger has no durable anchor.

**Target:**

```sql
conversation_messages
  id, conversation_id, parent_message_id, role, created_at,
  schema_version int NOT NULL,      -- version of OUR format, not the SDK's
  model_id text, provider text,     -- per-turn attribution
  metadata_json jsonb               -- cost, tokens, stop reason, pin snapshot

message_parts                        -- ordered child rows, not a blob
  id, message_id, seq int,
  kind text NOT NULL,               -- text | reasoning | tool_call | tool_result
                                    --  | citation | prediction_candidate | attachment
  body jsonb NOT NULL,
  model_visible boolean NOT NULL    -- does this part re-enter model context on replay?
```

- `tool_call.body` = `{call_id, tool_name (canonical), args, envelope_ref?}` —
  **never** a provider function-call frame.
- `reasoning.body` = `{text, signature?, provider_opaque?}`, with opaque
  provider blobs storable but never replayed cross-provider.
- Telemetry-only parts are better emitted to the trace than persisted as
  parts; where persisted, `model_visible: false`.

**Why this survives D-05.** Cross-channel history was never the main argument.
The load-bearing requirement is mid-conversation model switching — turn N by
Gemini replayed to DeepSeek on turn N+1 is a cross-provider serialization
boundary happening *inside one conversation, every time the picker flips*.
Reasoning signatures, thought signatures, and tool-call-id format constraints
are where naive replay errors or silently degrades. Canonical storage turns
each into a mapper case. The prediction ledger's need for a durable FK target
makes it overdetermined.

### §11.2 Threads, branching, sharing

Retained from the existing model and extended:

- Branching via `parent_message_id`, surfaced as **alternate reading paths** —
  same praśna, different model or different doctrinal route, comparable
  side-by-side. Cheap given the schema already supports it, and genuinely
  novel for the research-instrument goal.
- Shares, folders, projects, export: retained.
- Resume-after-interrupt: retained, re-expressed in the §12.3 protocol.

### §11.3 History compression → durable summaries

**Today's implementation is replaced.** It is char/4 token estimation, then a
hardcoded Anthropic Haiku summarization cached in an in-process `Map`, spliced
in as a synthetic turn pair. Four independent failures:

1. **Multipart-blind** — head messages with array content collapse to the
   literal string `'[multipart content]'`, so in a tool-heavy reality it
   discards precisely the tool results and citations the summary most needs.
2. **Provider-pinned** — a Gemini-stack conversation carries a hardcoded
   Anthropic dependency.
3. **Cache is a `Map`** — gone on every cold start, so it re-summarizes
   constantly and pays per request.
4. **Cache-hostile** — splicing at position 0 rewrites the prompt prefix and
   destroys prompt-cache hits.

**Target, to the D-06 bar:**

- `conversation_summaries` rows: `conversation_id`, `covers_through_message_id`,
  `summary_text`, `model_id`, `created_at`. Written once per threshold
  crossing, reused across processes.
- Summarizer is a **family worker** via the ModelPlane, never a hardcoded
  provider.
- **Canonical-store-aware**: tool parts render as
  "consulted `kala_windows_get` → [envelope verdict line]" rather than being
  discarded.
- **Citation-preserving**: fact_ids named in summarized turns survive verbatim
  so the grounding gate's refs do not dangle.
- **Prefix-stable splicing**: the summary occupies a fixed structural slot so
  caching survives (§10.8).
- **RAG recall**: summaries plus the existing pgvector message embeddings let
  Paripraśna answer "what did we conclude about the 2019 Saturn return?"
  without replaying 200 turns. This is the actual memory upgrade D-06 asks
  for.

> **[GROUNDED 2026-08-18 — v0.11]** This target SHIPPED in PB-2 to its own
> spec: `conversation_summaries` rows written every 6 new canonical messages
> (2-message verbatim tail held back), a family worker via the ModelPlane
> (`callType:'worker'`, never a hardcoded provider), independent
> citation-survival enforcement, and the summary spliced into a FIXED prefix
> slot (`[Conversation summary — earlier turns]` / `(none yet)`) for
> prompt-cache stability. One disclosed asymmetry: summaries build from
> assistant rows only, because user/history turns still persist on the legacy
> writer (A-08 Δ). RAG recall shipped as a module and is NOT yet wired — see
> §11.5.

### §11.4 The provenance stamp (D-16)

**The construct formerly called the "session pin" cannot pin.** §N.3 mandates
delete-then-insert per `(chart_id × natural key)`, so exactly one build of a
chart exists in Postgres and there is no archive. Once build Y lands, build X
is gone — nothing can hold a conversation at it. The construct is a **witness,
not a lock**, and is renamed accordingly.

**What it carries** (unchanged fields, one of which is doing a different job):

| Field | Purpose |
|---|---|
| `build_id` | Which build produced the data this turn read |
| `priors_version` | Which calibration priors were in effect |
| `formula_versions` | Which rule versions computed the values |
| `ranking_config` | Which ranking parameters ordered the results |
| `now_context_date` | **Not about builds at all.** "The next two years" means something different asked in 2026 than in 2028. A genuine input to the reading that was bundled in with the version fields. |

**What it earns, honestly assessed:**

1. **Drift disclosure — modest but real.** Turn 1 at build X, chart rebuilt,
   turn 5 at build Y: the two halves of the conversation rest on different
   numbers. The stamp is what lets the surface *say so*. §N.6's honesty
   posture applied to time rather than coverage.
2. **Audit provenance — real.** A settled turn labelled "build X" stays
   correctly labelled forever. Because there is no archive, that reading is
   **not reproducible** — and knowing that it isn't is itself honest
   information.
3. **Calibration attribution — the reason it must exist.** A prediction made
   under `build_id` X / `priors_version` P / `formula_versions` F is scored
   eighteen months later. Without knowing what produced it, **the Brier score
   attributes error to the wrong thing** — penalising a technique whose
   formula was since revised, or crediting a prior since replaced. The
   `mimamsa_calibration` grain (chart × technique × ayanamsha) only means
   something across time if each ledger row carries the versions in effect
   when the claim was made. **Without provenance, calibration is noise dressed
   as evidence.**

**Structural consequences of D-16:**

| | Was | Is |
|---|---|---|
| Where it lives | `mcp_sessions.state_json`, re-keyed per chart_id, mutable | `conversation_messages.metadata_json` — one immutable stamp per assistant turn |
| Scope | MCP only | Every turn produced by the engine, both channels |
| Drift detection | Compare session pin to current build | Compare this turn's stamp to the previous turn's — **no shared session state required** |
| Ledger attribution | References the pin | **Copies** the stamp into the ledger row at confirmation time |
| Engine signature | Passed in as a parameter | Comes **out** with the answer; the engine reads current build state itself |

The ledger rule is a hard requirement, not a preference: **a ledger row is an
immutable historical claim and must never point at mutable state.** If it
referenced a session pin that later refreshed, the attribution would be
silently corrupted — the worst class of failure, because nothing would look
wrong.

This deletes a mutable shared-state construct along with its §31.3
collision-mitigation complexity, replacing it with an immutable per-turn field.

**Rendering.** The stamp surfaces as ambient chrome in the Paripraśna
conversation header (§12.5). If the chart was rebuilt mid-conversation, the UI
says so — a drifted reading is a different reading.

> **[GROUNDED 2026-08-18 — v0.11]** D-16 SHIPPED to its structural spec:
> the stamp is computed per assistant turn, persisted DB-only (never
> streamed — the one reader-facing exception is `flag{chart_rebuilt}` on
> detected drift), and **copied — never referenced — into every ledger row at
> confirmation time**, with a DB trigger (`trg_bmpl_freeze_confirmed`)
> freezing the five stamp fields exactly as the "immutable historical claim"
> rule demands. The code-level rename landed at v0.9 (RC-13).

> **Known limitation, recorded not solved.** Because builds are not archived, a
> past reading cannot be re-derived. The stamp records *that* it cannot, but
> cannot restore it. Two cheap partial mitigations exist if this ever matters:
> a `build_manifest` row per build (versions, counts, timestamp — not the data,
> so it is tiny), and/or snapshotting the specific envelopes a turn consumed
> into the turn's parts, which makes *that reading* reproducible even though
> the chart is not. The second is nearly free, since the grounding gate already
> holds those envelopes at commit time.

### §11.5 Cross-conversation memory (new v0.5)

**The document designed the turn superbly and the relationship not at all.**
D-06 promises "what did we conclude about the 2019 Saturn return?" — but
§11.3's summaries and recall are specified **per conversation**. The real
product need on the hundredth conversation is **per-chart memory across
threads**.

The schema permits it (embeddings are chart-scoped and queryable; the backfill
script `platform/scripts/backfill_conversation_embeddings.ts` already exists —
§15 should have listed it as an asset). What is undesigned:

- **Retrieval.** Per-chart semantic recall across all threads, not just the
  current one. Extends the existing pgvector pipeline; not new.
- **Contradiction handling.** Two past readings may disagree — because the
  chart was rebuilt, because a formula changed, or because the model was
  wrong. Recall must surface the disagreement, not silently pick one. The
  provenance stamp (§11.4) is what makes this adjudicable: *"in March, under a
  prior build, I said X."*
- **What grade a past conclusion carries.** **A past reading is not an L1
  fact.** It cannot enter `grounding` as though it were. It needs its own
  citation kind — `prior_reading` — with its own grade, explicitly weaker than
  `verified`, and it must never satisfy an acharya-floor requirement. Without
  this rule, self-reference silently launders interpretation into evidence,
  which is a B.1 violation by the back door.
- **Dedup and decay.** A hundred conversations produce redundant conclusions;
  recall must rank by recency, provenance freshness, and whether the
  underlying build still stands.

> **[GROUNDED 2026-08-18 — v0.11]** Substantially BUILT, entirely UNWIRED:
> `lib/pariprashna/recall/` implements pgvector cross-thread recall over
> `conversation_message_embeddings` with similarity+freshness ranking, and the
> `prior_reading` citation grade is structurally forbidden from marking a B.11
> floor item served (`citations/floor_gate.ts`) — exactly the self-reference
> firewall this section demands. **Zero production callers.** Wiring it — plus
> contradiction surfacing and the arrival line — is A-41, §19.5 wave 3. The
> remembering wave is now cheap because every substrate row exists.

### §11.6 What the MCP channel has

Per D-05: no conversation transcript. It retains the session pin, entitlement
resolution, and — per OT-6 — possibly nothing else. The one durable memory
that *is* channel-agnostic by necessity is the prediction ledger (§14), and
§18/T-2 flags that this must not be "simplified away" in the name of D-05.

---

## §12 — Paripraśna render architecture

### §12.1 The reported failures and their causes

Full forensic detail with file:line references is in §16. Summarized:

| Symptom (native's words) | Root cause |
|---|---|
| "Takes a while… then gives me the full response" | The entire pipeline — planner call, bundle hydration, all tool executions — runs **before the HTTP response body opens**. Then stages are replayed retroactively in one burst. |
| "Some or part of [the thinking] was visible" | Reasoning chunks are written with an invalid protocol type for the SDK major version in use, cast through `as any`, and carry a message id where a part id is required. No open/close lifecycle. |
| "The presentation breaks… they move up and down" | The progress region is mounted **inside** the answer flow, above the text, gated on `isStreaming`. Tool cards mount above streaming text; a "still working" indicator self-inserts; and at stream end the whole region **unmounts**, snapping the settled answer upward. |
| "The MSR signals… broken, out of whack" | Two transmutation mechanisms firing in one message: GFM footnote definitions arrive at the end, causing a whole-message reparse and re-layout at completion; and a full-text regex rewrite runs on every delta, so a partially-streamed id flips from prose to badge mid-paragraph. |
| "The cursor would be somewhere at the very bottom… under the sequences" | The streaming cursor is appended as a **sibling after the entire markdown output**. Markdown emits block-level elements, so an inline span after a `<div>`/`<table>` renders on its own line at the left margin below the last block — never after the last glyph. |
| "Snappy… uncontrolled" | No frame decoupling anywhere. Rendering cadence equals network cadence; five independent store subscribers re-run per token, one of them writing to `sessionStorage` on every token. |

**Attribution.** The SDK genuinely does not provide progressive
block-freezing markdown, a progress-region model, scroll discipline, or
register separation — expecting it to was a category error; it is a transport
and state library. But nearly every failure above is the integration.

### §12.2 Framework ruling: the AI SDK transport goes

Four reasons in weight order:

1. The target contract is **canonical message parts**, not `UIMessage`.
   Keeping the SDK means permanently maintaining a bidirectional mapping
   between the canonical schema and the SDK's shape — reintroducing at the
   wire the exact blob disease being excised from storage.
2. The current code already fights the SDK: every server write is `as any`,
   data parts ride two racing transports, and the engine's real semantics
   (stages, gates, citations, registers, tiers) have no SDK representation.
   **~15% of the SDK is used and 100% of its shape is paid for.**
3. The SDK's value is server-side provider abstraction — but a provider
   adapter layer already exists and the live path does not call `streamText`.
   The client SDK is abstraction over an abstraction that is not used.
4. Effort and cost are declared not a constraint (D-12), and the bar is Claude
   Code (D-13), which is a purpose-built renderer over a typed event protocol.

**Replacement:** a typed SSE protocol, one client reducer, a purpose-built
renderer, with Zod schemas shared between engine and client via
`@marsys/contract` so `as any` is structurally impossible. The MCP door
consumes the same engine emitting the same events; MCP serialization becomes a
projection of the event log — the "one engine, two doors" topology falling out
for free.

### §12.3 The stream contract

**Semantics are block-level, not token-level**, for everything except the open
text block. The server owns segmentation: it has the full text as it generates,
and a small incremental splitter on fence/blank-line/heading boundaries is
deterministic and testable server-side.

```
turn.open        {turn_id, conversation_id, mode}
phase            {phase: plan|retrieve|synthesize|verify|persist,
                  status: start|done, ms?}
activity.upsert  {activity_id, kind: plan|tool|gate, label_key,
                  status: running|ok|error, ms?, counts?, detail_ref?}
                                       // keyed upsert — NEVER a new row per update
reasoning.open   {block_id}
reasoning.delta  {block_id, text}
reasoning.close  {block_id, ms, token_estimate}
block.open       {block_id, kind: markdown|table|code, after: block_id|null}
block.delta      {block_id, text}      // ONLY the open block receives deltas
block.commit     {block_id, final_md, anchors: [{marker_n, ref_id}]}
                                       // settles the block; byte-final
citation.define  {ref_id, marker_n, grade, reader_label, source:{kind,id}}
flag             {kind: out_of_domain|correction|truncated|gap, payload}
grade            {gate: citation|validator, verdict, detail_ref}
turn.commit      {message_id, part_manifest}
turn.close       {usage, cost?, trace_ref}
error            {class, retryable, message_key}
```

**Ordering guarantees.** `seq` strictly increasing. At most one open `block.*`
at a time. `activity.upsert` may interleave anywhere — it targets a different
region, so interleaving is layout-safe *by construction*. `block.commit` for
block N precedes `block.open` for N+1. Every `citation.define` precedes the
`block.commit` of the block containing its marker.

**Append-only surfaces:** committed blocks, closed reasoning blocks,
citations.
**Mutable-by-upsert surfaces:** activities, phase, the single open block.

**`block.commit.final_md` is authoritative.** The client discards its
accumulated deltas and re-renders the block once from the final string —
self-healing against dropped deltas — then freezes the subtree (memoized on
`block_id`, props never change again).

**The protocol and the storage schema are the same algebra.** These same
commits are what persistence writes as `message_parts` rows, which eliminates
the live-vs-persisted dual-source race entirely.

**The stream opens immediately on POST.** `turn.open` and
`phase{plan, start}` go out before the planner runs. Dead air becomes a live
plan phase.

**Persistence moves after `turn.close`** from the client's perspective: emit
`turn.commit` with pre-allocated ids, close the visual turn, then do DB work.
The client must never show "streaming" during bookkeeping.

> **[GROUNDED 2026-08-18 — v0.11] The protocol SHIPPED (PB-1), and the shipped
> vocabulary differs from this sketch in ways worth naming rather than
> retrofitting.** The live contract is the 15-event Zod union in
> `lib/pariprashna/protocol/events.ts` — the single source of truth; this
> section remains the design rationale, that file the law. Deltas:
> **(1)** pass seams were added (`seam.open`/`seam.set`) — a second transient
> slot for multi-pass agentic turns this sketch never anticipated, derived
> purely from the engine's own control flow; **(2)** `reasoning.open/delta/
> close` shipped as `role: prose|thinking` on `block.open` — one lifecycle,
> not two (see this §12.3 note, the vocabulary record of reference); **(3)** `snapshot.apply` was added for degraded resume;
> **(4)** `citation.define` gained additive `reader_label` + `grade`;
> **(5)** the stream-first ordering shipped exactly as designed —
> `turn.open` + `phase{plan,start}` are the first bytes, before the planner,
> with the ring buffer seeded before the first event. Every event is
> schema-validated at emit (`serializeEvent` throws — a malformed event can
> never reach the wire) and guarded by `assertNoCalibrationLeak`. **The one
> place the shipped wire is thinner than this design: block TYPING.** The live
> wire says which bytes belong to which block but not what the block IS —
> tables, verses, gap ribbons, headings, prose roles and prediction cards are
> client `BlockKind`s reachable only from fixtures. Closing that is A-37.

### §12.4 Progressive markdown — CLIENT-side segmentation (revised v0.5)

> **Revised.** v0.1–v0.4 put block segmentation on the **server**. The
> adversarial review identified this as "the weakest technical decision in the
> document," and the objection holds. Segmentation moves to the client.

**Why server-side segmentation was wrong:**

1. **CommonMark block structure is not delimited by blank lines.** Blank lines
   occur legally *inside* loose lists — committing on them fragments a nested
   list, breaking numbering continuity and tight/loose rendering. Setext
   headings are only recognizable one line *after* their text. Tables need no
   preceding blank line. Blockquotes can contain fences containing blank lines.
   The "small deterministic splitter" converges on a real block parser or
   commits wrong.
2. **It recreates the exact disease §8.5 exists to cure, at a worse layer.**
   A server splitter and a client renderer must agree byte-for-byte at block
   granularity, forever — a hand-maintained *semantic* mirror where
   disagreement produces **visible rendering corruption rather than a type
   error**. Having just corrected §8.5's claim about one mirror, creating
   another would be indefensible.
3. **`block.commit` is declared byte-final; the LLM has made no such
   commitment.** Models restructure mid-thought: what streamed as a paragraph
   turns out to be a list lead-in; a heading is orphaned when a section is
   abandoned. Once committed, no repair is possible. Discard-and-re-render
   from `final_md` handles *transport* divergence, not *authorial* divergence.
4. **Latency.** Buffering to block boundaries means a long table or fence
   streams nothing committable for its whole duration.

**The revised design — stable-prefix parsing on the client:**

- The server streams **raw text deltas** plus the structured events
  (`activity.upsert`, `citation.define`, `phase`, `flag`, `grade`) that are
  the genuinely valuable part of the protocol.
- The **client** parses accumulated text with **one markdown engine**, freezes
  every block except the last, and memoizes frozen subtrees on a content hash.
- This preserves the §12.4 structural invariant exactly: *because everything
  above the tail is frozen, no completion can move settled content.* The
  invariant was never dependent on *where* segmentation happened — only on
  freezing.
- **One markdown parser exists in the system.** No mirror, no drift, no
  server buffering.
- Authorial restructuring is now recoverable: the client re-parses accumulated
  text, so a paragraph that becomes a list lead-in simply re-renders within
  the volatile region rather than being wrongly frozen.

**Persistence-time segmentation still happens server-side** — but *once,
post-stream*, where it is trivial and has no latency or agreement constraint.
That is what produces `message_parts` rows. The protocol keeps `block.commit`
as a **persistence and citation-anchoring** event, not as a rendering
instruction.

- Frozen blocks are memoized static renders. Only the tail block re-parses per
  flush — parse cost is O(tail), not O(message), because the stable prefix is
  memoized even though the parse input is the full accumulated string.
- **Incomplete constructs, tail-block policy:** unterminated fence renders as
  an open code block; a half table row renders the rows so far with
  `table-layout: fixed` and a server-hinted column count so widths do not
  thrash; a partial link stays plain text until the closing paren.
- **The structural invariant:** because everything above the tail is frozen,
  *no completion can move settled content.* This holds structurally, not
  heuristically.
- **Token application clock:** buffer incoming deltas; flush to state on
  `requestAnimationFrame`, coalescing all events arrived that frame. One state
  commit per frame maximum. This alone eliminates the per-token fan-out class
  regardless of network cadence.

### §12.5 The three-region turn layout

```
┌─ Turn (assistant) ─────────────────────────────────────────────┐
│ ① WORKING REGION (fixed-position header band, stable height)   │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ ◐ Consulting the chart · 12s        [∨ details]            │ │   ← one line, always.
│ │  (expanded: )                                              │ │     Label from phase
│ │  ✓ Understood the question                        0.8s     │ │     events. Finishing
│ │  ✓ Gathered chart evidence · 6 sources            3.2s     │ │     flips label to
│ │  ◐ Reading timing cycles…                                  │ │     "Grounded in 14
│ │  ▸ Reasoning (2.1k tokens) [collapsed]                     │ │     sources · 12s" —
│ └────────────────────────────────────────────────────────────┘ │     SAME BOX. Never
│ ② ANSWER REGION (append-only frozen blocks + one volatile tail)│     unmounts.
│   Saturn's period, which began in late 2022, has been the      │
│   engine behind the career pressure you describe ⟦1⟧. Three    │
│   independent indications converge on mid-2027 ⟦2⟧⟦3⟧ as ...▊  │  ← caret inline,
│ ③ GROUNDING REGION (appears once, post-settle, stable)         │     last glyph
│   Grounded in 14 chart factors · 3 classical sources           │
│   [1] Saturn–Moon angle (verified ✓)  [2] Dasha timing …       │
│   ⚑ 1 claim could not be fully verified — view                 │
└────────────────────────────────────────────────────────────────┘
```

- **Region ① is in-flow but permanent and height-stable** — a one-line header
  per turn, existing from `turn.open` onward forever. It *is* the audit
  affordance in the transcript. Activities are keyed rows updated in place.
  Collapsed by default at reader tier; expanded by default at audit tier.
  Reasoning is an entry *inside* ①, not a separate flow element.
- **Expansion pushes with a max-height and internal scroll** — honest,
  bounded, and only user-initiated, so movement is expected.
- **Region ② is the append-only document.** Nothing but blocks. No banners
  ever insert above it mid-stream; `flag` events render in ① while streaming
  and in ③ post-settle.
- **Region ③ mounts exactly once**, after `turn.commit`, *below* the answer.
  Appending below settled content is layout-safe. Citation chips in ②
  scroll/highlight into ③ entries on click.
- **Session-pin chrome** lives in the conversation header above all turns —
  chart, build id, drift flags (§11.4).

### §12.6 Scroll and cursor discipline

- Remove smooth-scroll behaviour from the viewport; smooth only for
  user-initiated jumps.
- Pin-to-bottom via an IntersectionObserver sentinel plus **immediate break on
  upward intent** (wheel deltaY < 0, touchmove) rather than waiting for the
  observer. Re-pin only via the pill or by scrolling back to bottom.
- While pinned, apply growth and scroll in the same rAF flush (write
  `scrollTop` after DOM commit) so there is never a visible intermediate
  frame.
- `overflow-anchor: none` on the viewport — we own anchoring.
- **The caret is rendered by the tail-block renderer, on the last text node of
  the volatile block.** It cannot orphan because it does not exist outside the
  tail block. On `block.commit` with no successor open, it moves to region ①'s
  header until `turn.close`. It is never a sibling of block-level output.

### §12.7 Virtualization ruling: none

Delete the dead list implementations. Conversations here are tens of turns,
not tens of thousands; frozen blocks are cheap static subtrees. Virtualizing
variable-height streaming content is the jitter source, not the cure.

The correct instruments are: frozen-block memoization (render cost ~O(tail)),
`content-visibility: auto` + `contain-intrinsic-size` on off-screen settled
turns (browser-native lazy layout with anchoring preserved), and turn-level
lazy hydration for restored long histories. If a pathological transcript ever
matters, paginate history above the fold; do not virtualize the live region.

### §12.8 Tool-call presentation — one row model, two zoom levels

Per D-15 this is **not** a tier projection. It is one `activity.upsert` row
rendered at two zoom levels, and **anyone can move between them by clicking**.

- **Collapsed (default for everyone):** rows use `label_key → reader_label`
  from the registry (§8.7): "Gathered chart evidence · 6 sources", "Checked
  timing cycles". Reader-legible; no tool names, no milliseconds, no ok/err
  counts. Often the region ① header alone is all anyone needs.
- **Expanded (available to everyone; content gated by entitlement to the
  underlying data):** the same rows showing `capability_id`, params digest,
  row counts, latency, cache hit, `detail_ref` into the trace drawer, gate
  verdicts inline.

The only role-dependence is **what data you are entitled to see** when you
expand — not whether the affordance exists. Super-admin sees more on expand
because they hold broader entitlement, not because they are in a different
mode.

**Stable-height rules.** A row is born at final height with a status-glyph
slot, a label slot, and a *reserved* right-aligned metrics slot rendered as
`—` until known. Completion swaps the glyph and fills metrics — no width or
height change, no mount or unmount. Rows never disappear at stream end; the
header label simply changes.

### §12.9 Citations, render mechanics

The model emits `⟦cite: SIG.MSR.413⟧` sentinels. **The server rewrites them to
`⟦n⟧` plus a `citation.define` event before any byte reaches the client.**

Three properties this guarantees:

1. **No mid-stream transmutation** — chip geometry is fixed from first render;
   there is no plain-text→badge flip.
2. **No end-of-stream reflow** — there is no footnote definition block;
   definitions are events, not prose.
3. **The grounding gate becomes envelope-native and *pre-commit*** — it
   validates `citation.define.ref_id` against the turn's retrieval envelopes
   server-side, per block, before `block.commit`. An unverifiable citation can
   be flagged or downgraded to an "unverified" chip style *while the turn is
   still streaming*, instead of a gate banner mounting above a finished answer.

#### §12.9.1 Sentinel handling — the fallback, specified (new v0.5)

v0.1–v0.4 said "the server rewrites sentinels before the wire" in one sentence
and specified none of the failure modes. **Models are unreliable at exact-token
emission, and this system has direct evidence of it**: the *current* prompt
already demands exact `[^N]: SIG.MSR.413` footnote format
(`synthesis_prompt_v2.ts:26–46`), and §16.2 is partly a record of that failing.
**Exact-format emission is historically this system's least reliable link.**
Budget accordingly.

**Hold-back buffer.** The sentinel arrives across delta boundaries — `⟦ci` +
`te: SIG.M` + `SR.413⟧`. From the first `⟦`, the server holds bytes back until
close-or-disproof. Hard rules:

- **`MAX_SENTINEL_HOLDBACK` = 64 bytes.** Exceeded → flush held bytes as plain
  text, emit `flag{kind:'malformed_sentinel'}`, resume normal streaming.
- **`SENTINEL_HOLDBACK_TIMEOUT` = 400 ms** with no further bytes → same flush
  path. **Without both, an unclosed `⟦` stalls the tail of the stream
  forever.**
- Held-back bytes never reach the client unresolved, so no transmutation.

**Tolerant grammar.** A strict grammar drops citations silently — and in a
system whose differentiation is groundedness, that makes a well-grounded
reading *look* less grounded. Accept and normalize: `[[cite: …]]`,
`⟦cite:… ⟧` (internal whitespace), case-insensitive ids, missing space after
the colon. Log each normalization; a rising normalization rate per model is a
model-health signal.

**Hallucinated ids** resolve to an `unverified` chip (already specified) **and
increment a per-model counter**. Sustained high rates feed ModelPlane tier
review (§10.3). No silent tolerance: a model that invents citations is a model
that should lose Tier A standing.

**Failure taxonomy summary:**

| Failure | Response |
|---|---|
| Unclosed sentinel | Flush as plain text at 64B / 400ms; `flag` |
| Malformed but recognizable | Normalize, log |
| Well-formed, unresolvable id | `unverified` chip; per-model counter |
| Zero sentinels in a prescriptive-class answer | Existing prescriptive-class ERROR (`citation_check.ts:91,129–135`) — **retained**, re-pointed at citation *parts* |

> **[GROUNDED 2026-08-18 — v0.11]** §12.9.1 was BUILT faithfully — hold-back
> buffer (64B/400ms), tolerant grammar with normalization logging, per-model
> hallucination counter — as `lib/pariprashna/citations/rewriter.ts` +
> `protocol_adapter.ts`. **And it is not on the live route**: the route's only
> import from `lib/pariprashna/citations/` is the leak lint (it separately
> imports `extractCitations` and the post-accumulation validator from the
> older `lib/citations`/synthesis modules), so live `citation.define` events
> arrive post-hoc from the persistence write-through after synthesis ends, and
> chip rendering depends on `⟦n⟧` tokens nothing rewrites mid-stream. The
> citation gate itself runs (post-accumulation `validateCitationsForStream` →
> `grade{citation_gate}` + WARN/ERROR flags, `CITATION_GATE_OVERRIDE`
> demotion available). Net: the failure taxonomy above is dormant code, not a
> live guarantee. Wiring it is A-38, §19.5 wave 2 — first-paint chips are the
> visible half of "grounding is the product."

### §12.9.2 Transport resilience — reconnection, backpressure, error recovery (new v0.5)

v0.1–v0.4 designed the happy path and gave resume one sentence. Verified
current state (F-25f): resume is **snapshot-based, not event replay** —
`accumulated_text` sliced by `since_chars`, one-shot on page reload,
`last_event_seq` stored but never consumed, **no reconnection on a mid-session
network drop**. A custom transport must do better, not worse.

**Reconnection.** The protocol carries monotonic `seq`; make it usable:

- Client sends `Last-Event-ID: <seq>` on reconnect.
- Server replays from `seq+1` out of a per-turn ring buffer (bounded; on
  overflow, replay the accumulated-text snapshot plus a `flag{kind:'replayed_
  from_snapshot'}` so the gap is disclosed rather than hidden).
- **Mobile Safari suspends SSE aggressively** — reconnect must be automatic on
  `visibilitychange`, not only on reload.
- Exponential backoff with jitter; a visible, calm "reconnecting" state in
  region ① — never a silent stall.

**Backpressure.** The rAF flush (§12.4) is the natural throttle: coalesce all
events arrived per frame. If the buffer grows beyond a threshold (slow device,
background tab), drop to text-only rendering for the tail and reconcile at
`block.commit` — degrade rendering fidelity, never correctness.

**Half-committed turns.** If the stream dies after N frozen blocks:

- Persist what committed; mark the turn `incomplete`.
- Render the frozen blocks plus an explicit incomplete marker — **never a
  turn that merely looks finished.**
- Offer continue-from-here (the existing `continue` route is the seam).
- An incomplete turn is **excluded from prediction detection** — a truncated
  claim must not enter the ledger.

**Idempotency.** Duplicate `seq` on replay is discarded by the reducer;
`turn.commit` carries pre-allocated ids so a replayed commit is a no-op.

### §12.10 Failure UX (new v0.5)

The document designed honest *gaps* (T-5) and never designed honest *failure*.
Given D-13's bar: **Claude Code's error presentation is a designed surface**,
not an exception path.

**Adopt the existing classifier — do not write a new one.**
`platform/src/lib/chat/classify-error.ts` already implements 7 kinds
(rate_limit, insufficient_credits, model_overload, auth, timeout, network,
unknown), each with a user-facing title and hint. **It is dead code — never
imported** (F-25b). This is a working asset, not a gap.

| Failure | What the reader sees |
|---|---|
| Planner fault (today: bare 422 JSON, `consult/route.ts:445–453`) | Region ① states plainly what could not be planned, with a retry. A planner fault is **not** the reader's error and must not read like one. |
| Provider error mid-block | Frozen blocks stay; classified message in region ①; retry preserves the question and the plan (don't re-plan a plan that was fine). |
| All Tier A models down | Explicit degraded-mode offer: a different stack, or "come back later" — **never a silent quality drop the reader cannot detect.** §10 designs detection and never designed the user-facing posture. |
| Tool call fails | Activity row goes `error` in place (stable height, §12.8); if the acharya floor is breached the turn reports the gap via `flag` rather than answering around it. |
| Grounding gate downgrades many citations | Region ③ says so in one calm line. Degraded grounding is a finding, not a defect to hide. |

**The rule:** a failure message names *what failed*, *whether the reader can
do anything*, and *what was preserved*. No stack traces, no "something went
wrong."

> **[GROUNDED 2026-08-18 — v0.11]** Shipped differently than prescribed:
> `s1LiveAdapter` classifies error codes into rate_limit / model_overload /
> timeout / network / auth bands with calm reader sentences, planner faults
> stream as in-stream `error` events (no more bare 422), interrupted turns
> keep everything that arrived, and reconnect shows "Connection dropped —
> resuming… Nothing was lost." The specific instruction to adopt
> `classify-error.ts` was NOT followed — it remains dead code at HEAD (F-25b
> stands) while a parallel classifier lives in the adapter. Disposition:
> fold or delete in PB-4's dead-code sweep; two classifiers is the drift
> pattern this document exists to prevent. The §7.8 edge-state lexicon
> completion (every failure a fixture with exact copy) is PB-4 Lane F-3.

### §12.11 Mobile (new v0.5)

**v0.1–v0.4 contained zero sentences about mobile — while specifying "hover
the chip" as the primary citation interaction (§13.3). There is no hover on
the device where a person most plausibly asks about their marriage at 11pm.**

Verified current state: Tailwind `md:` breakpoints only; a mobile drawer and
a 44px sidebar toggle exist; **no `matchMedia`, no touch/swipe handlers, no
virtual-keyboard handling.** A two-state split, not a responsive system.

Requirements:

- **Citation chips are tap-first.** Tap opens the card as a bottom sheet;
  hover is a desktop enhancement, never the only path. Chip hit area ≥44×44
  regardless of visual size.
- **Region ① expansion is a sheet on mobile**, not push-with-max-height —
  pushing the answer down on a small viewport is the §12.5 failure mode in
  miniature.
- **Virtual keyboard**: `visualViewport` handling so the composer is not
  occluded and the pin-to-bottom target accounts for keyboard height.
- **Scroll discipline on touch**: `touchmove` upward breaks the pin (§12.6
  already specifies this — it is *more* important on touch, where momentum
  scrolling makes accidental re-pinning jarring).
- **The three-region layout collapses gracefully**: region ① one line, region
  ③ below the fold with an anchor from the chips.
- Replay-harness fixtures and visual-regression checkpoints (§17) run at a
  mobile viewport, not only desktop.

### §12.12 Accessibility (new v0.5)

**v0.1–v0.4 contained zero mentions.** The correction is not "add a11y" — the
current implementation is **partial but genuinely decent**, and a from-scratch
renderer would regress it. Preserve and extend:

**Already present, must not be lost:** message log landmark
(`ConsumeChatV2.tsx:1579–1583`, `role="log" aria-live="polite"
aria-atomic="false"`), streaming markdown toggling `aria-live` **only while
streaming** (`MarkdownContent.tsx:172–173` — this is the correct pattern and
non-obvious), SR-only announcer (`AssistantMessage.tsx:129`), `role="status"`
across four components, `role="alert"` on validator bands, icons
`aria-hidden`, buttons labelled.

**To add:**

- **`aria-live` discipline for frozen blocks.** A frozen block must leave the
  live region once settled, or a screen reader re-announces the whole answer
  on every commit. This is the accessibility twin of the visual freeze
  invariant.
- Focus trap for the drawer/modal; skip link to the composer.
- Citation chips reachable and expandable by keyboard; region ① expandable by
  keyboard.
- Region ③ mount announced once, politely.
- **`prefers-reduced-motion`** honoured by the caret and any transitions.
- **axe-core pass in the replay harness** (§17) at fixed checkpoints — a11y
  regressions caught the same way layout regressions are.

### §12.13 Verdicts on the three flagged legacy components

| Component | Verdict | Reasoning |
|---|---|---|
| **Citation gate** | **DEPRECATE-AND-REPLACE** | Welded to the MSR-markdown signal-id format while the substrate is now DB-native Bodha with v3 envelopes carrying structured grounding. It literally cannot validate an answer grounded in the current serving surface. Its second layer was always weak — "this id appears somewhere in the context JSON" is membership, not grounding. Replacement per §12.9; keep the PASS/WARN/ERROR and prescriptive-class-ERROR semantics, which are right. |
| **Streaming citation validator** | **DELETE (fold in)** | ~78 lines, misnamed — it calls the validator in `onFinish`, post-stream. Once the gate is envelope-native this file has no independent existence. If genuinely streaming validation is wanted, the replacement gate grows it. |
| **History compression** | **DEPRECATE-AND-REPLACE** | Four independent failures, §11.3. The threshold/split skeleton is reusable; the rest is replaced. |

---

## §13 — Register separation and disclosure tiers

### §13.1 The principle

**The derivation ledger is data attached to the message, never sentences
inside it.**

B.3 mandates that every L2+ claim carry a derivation ledger listing the L1
fact ids it consumes. B.1 mandates facts/interpretation separation. Neither
requires — and D-14 forbids — that the ledger be spoken aloud in the reader's
prose.

### §13.2 Where the leak originates

Four sources, all architectural:

1. **The prompt requires the model to write internal ids into visible prose.**
   The citation appendix instruction mandates footnote definitions naming
   `SIG.MSR.NNN`; the UI then tries to *hide* them with `sr-only` and fence
   nulling. Emit-then-suppress guarantees leakage under drift — and mid-stream
   they are visible regardless.
2. **The model's entire evidence context is written in the internal
   register.** Tool results reach synthesis carrying signal ids, asset names
   and layer tags. A model whose sources speak the internal register will
   speak it back.
3. **The only register control is one sentence in one of three styles.** The
   default style has none.
4. **Enforcement is client-side regex for one pattern family.** The citation
   gate validates id presence and provenance, not vocabulary — it would
   happily PASS a response reading "per the L2 Bodha laksana table…".

### §13.3 The two registers, one ledger

The message-part schema enforces the separation:

| Part kind | Register | Contract |
|---|---|---|
| `text` | **Reader** | Zero internal identifiers. May contain `⟦n⟧` sentinels only. |
| `citation` | **Both, one zoom axis** | `{marker_n, ref_id, grade, reader_label, audit_detail}`. This *is* the derivation-ledger entry — first-class, auditable, bound to the exact claim span. `practitioner_label` struck by D-15. |
| `tool_call` / `tool_result` | **Internal** | Full internal register; machine-facing. |

`grade` uses the §N.6 density classes:
`verified | corroborating | catalog_only | unverified`.

**Same citation, two zoom levels — both available to anyone.**

- *Hover the chip (default):* "Saturn's angle to your Moon — a classical
  indicator of sustained career pressure. Verified against your chart. ✓"
- *Expand the same chip:* `SIG.MSR.413 · bodha_msr_signals · grade: verified ·
  constituent facts: F.L1.0231, F.L1.0248 · gate: PASS · BPHS 34.12`

Entitlement governs *what data* the expansion contains, never whether the
expansion is offered.

### §13.4 One reading, one register, audit as affordance (D-15)

**There are no audience tiers.** The legacy model had a tier structure; it was
deliberately torn down and must not return. §N.4 already ruled this at the
build layer ("writers emit all rows; serve-time governs access"); D-15 extends
it to the serve layer.

**Why the tier idea was wrong.** It smuggled in a false assumption — *that
plain language means a lesser reading*. The opposite is true. A real acharya
does not speak in citation ids; they explain precisely, in words the person can
hold, and cite exactly when it matters. **Speaking plainly is the higher
standard, not the degraded one.** "Reader tier gets simplified output" was
never a disclosure question; it was a quality question wearing a disclosure
costume.

**The three rules that replace it:**

1. **One reading. Always acharya-grade.** No depth parameter, no mode, no
   quality axis. Every user who asks the instrument a question receives the
   full planner pipeline, the full acharya floor, the full grounding gate.
   There is no lesser path.

2. **One prose register — reader-legible, universally.** D-14 applies to
   *everyone, including the native*. Internal ids, asset names, layer numbers
   and acronyms never appear in prose for any user. This is a property of the
   output, not a setting. **If a sentence needs `SIG.MSR.413` to be
   understood, the sentence is badly written.**

3. **Audit detail is an affordance, not a mode.** Expanding a citation chip,
   opening the working region, viewing the `PlanReceipt` — things anyone can
   *click*, gated only by entitlement to the underlying data.

**The distinction that carries the design: a tier changes what gets produced;
an affordance is progressive disclosure over one thing that was produced.**
Everything tiers were wanted for — the chip expanding into the full ledger, the
collapsed working region opening into capability ids and latencies — works
better as an affordance, because it is *the same artifact viewed more closely*
rather than a different artifact.

**Consequence for the engine signature.** No `tier` parameter and no `depth`
parameter:

```
ask(chart_id, question)
  → { answer_parts, PlanReceipt, citations, activities, provenance }
```

`depth` is gone because the DR-8 scope tuple already derives width, depth and
horizon from the question — which is where that information actually lives.
`tier` is gone because no such concept exists. `pin` is gone per D-16 —
provenance comes **out** with the answer rather than going **in** as a
parameter, since the engine reads current build state itself. Budget ceilings,
where they apply, are an entitlement property of the caller, never a parameter
of the ask.

> **Open check.** An earlier draft justified tiers by citing the Ethical
> Framework's "stated disclosure tiers". That clause is plausibly about *what
> is disclosed regarding uncertainty and method* — a different axis, untouched
> by D-15. The paraphrase was not verified against source and should be
> checked before any claim is built on it.

### §13.5 Where enforcement belongs

Three layers; the structural guarantee is layers 2 and 3.

1. **Prompt — helpful, not trusted.** Instruct reader-register prose;
   citations via the structured channel; never name internal systems. Reduces
   frequency; guarantees nothing.
2. **Channel design — the real fix.** Citations leave the prose channel
   entirely. The model emits `⟦cite: id⟧` sentinels and the **server** rewrites
   them to `⟦n⟧` + `citation.define` before any byte crosses the wire.
   Internal ids never reach a reader-tier client.
3. **Server-side register lint — DEFANGED (revised v0.5).** A deterministic
   scanner over emitted text. Pattern classes:
   - `SIG\.\w+\.\d+`
   - `\b(MSR|UCN|CGM|CDLM|LEL)\b`
   - `\b(bo|ga|ka|ph|mi|bg)_[a-z_]+\b`
   - table names

   **Verdicts: rewrite (id-shaped tokens only) · redact-with-flag ·
   telemetry. Never fail-the-turn.**

> **⚠ The streaming contradiction, stated honestly.** v0.1–v0.4 claimed the
> gate runs "pre-commit, so a leak can never settle into a reader-tier
> transcript." **The deltas have already gone out.** `block.delta` streams the
> open block as it generates; the lint runs pre-*commit*, not pre-*delta*. So
> an internal id in the model's prose is **on the reader's screen for the
> entire time the block is open**, and rewriting it at commit produces exactly
> the mid-stream transmutation that F-06 records as a legacy defect and §12.9
> promises to eliminate.
>
> The honest statement of the guarantee: **the leak does not persist, but the
> reader saw it.** That is materially weaker than v0.1–v0.4 implied, and
> pretending otherwise would be the kind of quiet dishonesty §N.6 exists to
> prevent.

**Three consequent changes:**

- **`\bL[0-5](\.\d)?\b` is removed from the pattern set.** In a Jyotish
  instrument that answers health questions, "L1 vertebra" is not far-fetched.
  The false-positive cost exceeds the benefit.
- **The "Bodha/Gaṇita/… when used as system names" rule is deleted.** That is
  a semantic judgment, not implementable in the deterministic scanner this
  section promises — and its allowlist referenced "practitioner tier", a
  D-15 ghost.
- **Rewrite applies only to id-shaped tokens with registry labels.** For
  prose-embedded acronyms, rewrite corrupts grammar ("the MSR's 413th signal"
  → ?). Redact-with-flag is the only safe deterministic action there.
- **Fail-the-turn is abolished.** Discarding three paragraphs the reader has
  already read because the fourth contained "CDLM" is a worse product failure
  than the leak. If a hard stop is ever wanted, it belongs at
  retry-before-first-byte, never mid-stream.

**Where the load actually sits.** §13.2 already identified the real fix and
v0.1–v0.4 then built the strongest mechanism on the layer it correctly called a
backstop. Corrected weighting:

| Layer | Role | Strength |
|---|---|---|
| **Clean evidence context** (reader-register labels in the envelope; §6.4.1) | The model never sees ids it could quote | **Primary** |
| **Structured citation channel** (§12.9 — ids leave prose entirely) | Nothing requires the model to write an id | **Primary** |
| Prompt instruction | Reduces frequency | Helpful, untrusted |
| Register lint | Catches residue; redacts; **measures leak rate as a health metric** | Backstop + telemetry |

If evidence is clean and citations leave prose, the lint should almost never
fire. **Its firing rate is the signal that the primary layers are working** —
which is a better use for it than turn control.

> **[GROUNDED 2026-08-18 — v0.11]** The lint SHIPPED beyond this spec, and it
> earned its keep the hard way: three real production leak classes escaped in
> sequence during PB-1/PB-2 (raw tool names + `marsys://` URIs in activity
> labels; register acronyms; then **bare fact-id namespace codes like
> `KRK.C8.AMATYA` reaching a reader**) and each hardened the scanner — it now
> carries SIX hard pattern classes plus near-miss telemetry, with a
> grammar-preserving subject swap so redaction never breaks a sentence
> ("The UCN concludes…" → "This concludes…"). It runs server-side pre-wire at
> two points: per-delta, with the whole-block commit lint as backstop. The
> streaming contradiction stated above is now an OBSERVED property, not a
> prediction: a leak split across an SSE chunk boundary passes the delta lint
> and reaches the screen until block-commit scrubs it — the disclosed residual
> in the route itself. The clean-evidence PRIMARY layer also advanced: 33
> capabilities carry `reader_label`s, `resolveReaderLabel` is the only legal
> activity-string source, and the NO-LEAKAGE capability filter reports strips
> as a count, never a name.

### §13.6 The vocabulary layer

The glossary belongs in the **capability registry** (§8.7). The sentinel
rewriter and the register linter both read that table.

**Sanskrit policy (OT-9 closed by D-15):**

- Sanskrit is used where it **is** the substance — a yoga's name, a graha, a
  daśā — and is **always glossed inline**: "Śaśa Yoga — Saturn strongly placed
  in its own sign in an angle."
- This holds **for everyone**. A layperson learns something; a practitioner
  reads past the gloss. One text serves both, and the gloss is what makes it
  acharya-grade rather than merely correct.
- **Never, for anyone** — asset ids, layer numbers, table names, artifact
  acronyms.

**One residual problem — now sized, and it is not small.** Signal content in
`bodha_msr_signals` is machine-generated internal register:
`signal_summary_text` is documented as *"lossless deterministic NL (every
config key); embedding input for bo_samskara"* and `signal_headline_text` as
*"short deterministic sentence for display/retrieval"*
(`migrations/325_l2_bodha_enriched_schema.sql:70–71`). **Neither is plain
language, and there is no reader-facing column.**

**This gates whether D-14 actually works**, because the citation card's text
has to come from somewhere. At MSR v5.0's 573 signals this is weeks of
acharya-grade writing, or a generation-plus-review pipeline. **v0.1–v0.4
flagged it and put it in no phase.** It is now an explicit P5' workstream
(§19) with a defined shape:

- Add `signal_reader_text` as a new column — do not overwrite the
  deterministic columns, which are load-bearing for embeddings.
- Generate candidates with an LLM from `(config keys + classical source)`,
  then **review and freeze**. Generated-then-frozen, never generated at serve
  time — a reader label that varies between readings is a new drift surface.
- Prioritize by observed citation frequency: the top ~50 signals will cover
  most readings. Full coverage is a long tail that can lag.
- Until a signal has reader text, its citation card falls back to the
  classical source name plus the grade — honest and useful, just less
  informative. **The fallback must never be the internal text.**

### §13.7 The `audience_tier` excision (new v0.5 — a live D-15 violation)

D-15 abolished audience tiers. **The concept is still live in the codebase**,
in a half-excised state that is more dangerous than either extreme, because
the parts that remain look decorative and are not.

**Already removed:** the DB column (migration 090, 2026-05-28), tier gating
(DG1 ruling), retrieval-layer tiering (`lib/cache/with_cache.ts:40` —
*"audience_tier removed (DG1 ruling — retrieval layer is universal-access; no
tier gating)"*), and MCP auth (`lib/mcp/auth.ts:97,128`). `lib/perf/
audit_nightly.ts:154–157` demotes it explicitly: *"audience_tier gate removed —
all responses checked uniformly … field is logging metadata only."*

**Still live, and three of these are load-bearing:**

| Site | What it does | Disposition |
|---|---|---|
| `consult/route.ts:459` | `plan.audience_tier = isSuperAdmin ? 'super_admin' : 'client'` — stamped in the "never LLM output" block | **DELETE** |
| `consult/route.ts:587, 616, 809, 992` | Type decl, plan assembly, local recompute, dispatch param | **DELETE** |
| `lib/prompts/index.ts:10,35,37,45,58,61` | **Keys prompt-template lookup** — different tiers get different prompts | **LOAD-BEARING.** Collapse to one template set before deleting the key. |
| `lib/synthesis/prompts/adjudicator_prompt_v1.ts:40` | **Injected into adjudicator prompt text** | **LOAD-BEARING.** Rewrite the prompt. |
| `lib/mcp/bundle_adapters.ts:142` | Forwarded as `X-MCP-Audience-Tier` header | **DELETE** (coordinate with MCP workstream) |
| `lib/schemas/audit_event.schema.json:8,15` | **`required` field**, 4-value enum | **SCHEMA MIGRATION** — required→removed; existing audit rows carry it. |
| `lib/schemas/query_plan.schema.json:8,15` | **`required` field**, same enum | **SCHEMA MIGRATION** |
| `lib/mcp/types.ts:18–19,108–109,180–181,197–198` | Four vestigial optionals, each commented "removed" | **DELETE** |
| `lib/mcp/epistemics.ts:116,134`; `lib/router/types.ts:22,169`; `lib/pipeline/types.ts:306`; `lib/bundle/types.ts:36` | Type residue | **DELETE** |

**The trap:** the prompt-template lookup means **the system today produces
materially different prose for super-admin vs client.** That is exactly the
tier behaviour D-15 outlaws, hiding in a lookup key. Collapsing to one template
set is a prose-quality decision, not a mechanical deletion — the surviving
template must be the *better* one, which per D-15 means the one that explains
plainly.

> **[GROUNDED 2026-08-18 — v0.11] The trap is sprung — the load-bearing sites
> are excised.** Verified at HEAD: `lib/prompts/index.ts` header reads
> "`audience_tier` was excised"; the consult-route stamp is gone
> (C-2 tier_excision / DG1 ruling, `consult/route.ts:512` comment); no tier
> header is forwarded to registry lookups. **The system no longer produces
> different prose per tier — the live D-15 violation is closed.** Residue at
> HEAD: type/comment-level vestiges across ~12 files and the two JSON-schema
> `required` fields — mechanical cleanup for PB-4's sweep, no longer
> load-bearing. F-25g is downgraded accordingly in §16.9.

### §13.8 Remedy register — the prescriptive line (new v0.5)

The Ethical Framework exists at governance level; **almost none of it has been
translated into rendering and prose-register decisions, and that translation is
this workstream's job.**

The sharpest untranslated line: **"the tradition prescribes X" versus "you
should do X."** That is where an astrology product becomes exploitative.

Verified current state: the *citation* gate is real and good —
`citation_check.ts:91` sets `PRESCRIPTIVE_CLASSES = {'remedial','predictive'}`
and `:129–135` hard-fails a zero-citation prescriptive response
(*"prescriptive query produced 0 citations — guidance must be grounded"*).
Prompt-side, `CALIBRATION_LANGUAGE_GATE` bans "will happen"/"guaranteed", and
`remedial.ts:35,47` require naming the traditional source and framing as
mitigation.

**But nothing enforces register.** No lint on second-person imperative in
remedy output; no classifier on remedy phrasing. **The line is a prompt
instruction checked by no code.**

Target: extend the prescriptive-class machinery from *grounding* to *register*.
A remedy claim must attribute (`the tradition prescribes` / `BPHS recommends`)
rather than direct (`you should` / `wear` / `perform`). This is deterministically
checkable — second-person imperative in a remedial-class block is a
detectable pattern — and belongs alongside the register lint (§13.5), with the
same defanged verdicts: rewrite where attributable, flag otherwise, never
fail-the-turn.

### §13.9 Emotional register — a design input, not a disclaimer (new v0.5)

People will ask this instrument about a parent's illness, a failing marriage,
their own death. The `ganita_ayurdaya_get` tool exists on the surface. **The
architecture treated tone as out of scope; it is not — it is a rendering and
prompt-register obligation.**

| Concern | Requirement |
|---|---|
| **Pacing** | A hard reading delivered at full speed in a dense wall reads as callous. Difficult findings use shorter blocks and lead with uncertainty. This is a synthesis-prompt and block-segmentation concern, not an ethics page. |
| **Probability framing** | Laypeople read "70%" as certainty. Calibrated language — *"more likely than not; I'd hold this loosely"* — with the number available on expansion. This serves D-15's own philosophy better than a bare percentage: explain precisely, in words the person can hold. |
| **Honest gaps must read calm, never ominous** | In a fear state, users read gaps as withheld bad news. *"The chart is silent on this"* must be visually and tonally neutral. T-5 requires gaps be unmissable; **§13.9 requires they be unfrightening.** Both, simultaneously. |
| **Remedies** | §13.8. |
| **No unsolicited severity** | An answer about career does not volunteer a health finding because a signal fired. Cross-domain surfacing is a B.11 *retrieval* discipline, not a licence to alarm. |

**These are testable.** The register eval (§17.5) should score difficult-topic
answers for pacing and framing, not only for vocabulary.

---

## §14 — The prediction → calibration loop

### §14.1 Why this is mission-critical

L5 Mīmāṃsā is sealed in **STRUCTURAL mode** — its empirical calibration values
are empty *by design*, and can only fill from prediction→outcome data. The
conversation surface is the only place that data can come from. This loop is
therefore not a feature; it is the front door to the instrument's central
claim of being calibrated and correctable.

Today, `predictionCandidatePart` is detected and streamed, and then dies.
Nothing carries it to a ledger.

### §14.2 Detection

The existing two-stage design is sound and is kept: a synchronous regex pass
(sub-millisecond) plus an asynchronous classifier post-stream.

Extended to extract a **structured candidate**:

```
{claim_text, domain, window_start, window_end, direction,
 confidence_stated?, technique_refs[], grounding_fact_ids[]}
```

The grounding refs come free once citations are parts (§13.3), and they are
what make calibration attributable to *technique* — the `mimamsa_calibration`
grain is chart × technique × ayanamsha.

### §14.3 Candidate → ledger

The candidate persists as a canonical `prediction_candidate` message part in
state `detected`.

```
detected ──► confirmed ──► open ──► window_closed ──► outcome_recorded
    │                                     │                  │
    └──► dismissed                        └──► lapsed        └──► unverifiable
                                                                (Brier-excluded)
detected ──(aged out)──► lapsed_unconfirmed
```

**Confirmation is human.** The native, or an entitled guest for their own
chart, promotes a candidate. Promotion writes
`brahma_mimamsa_prediction_ledger` with: `chart_id`, source `message_part_id`
(FK — provenance to the exact utterance), the structured claim, the window,
the stated confidence, technique attribution, and `created_from_channel`.

**Elicit a probability at confirmation time** if the text did not state one.
Brier scoring needs a number, and forcing the confirmer to commit one is
itself good epistemics.

**No auto-promotion.** A calibration ledger polluted with mis-parsed
"predictions" is worse than a sparse one. But candidates are **never silently
dropped** either — unconfirmed candidates age out visibly as
`lapsed_unconfirmed`, so detector recall remains auditable. Dismissal-with-reason
feeds detector precision tuning.

### §14.4 Samīkṣā — the review surface

Two surfaces, not one.

**1. The Samīkṣā tab** (`/clients/[id]/samiksha`), per chart, with a badge on
the dashboard counting items needing human action (`detected` awaiting
confirmation + `window_closed` awaiting outcome).

| Section | Contents |
|---|---|
| **Awaiting confirmation** | Candidate text shown in its message context; one-tap confirm / edit / dismiss; probability slider on confirm. |
| **Open** | Timeline of live predictions — a good product surface in its own right. |
| **Resolve** | Closed windows: happened / didn't / partially / **can't-tell**, optional note. "Can't-tell" → `unverifiable`, excluded from Brier, counted separately as an honesty metric. |

**2. The in-stream affordance** at generation time — one-tap "log this" at the
moment of utterance, because confirmation propensity decays fast. The tab is
the net that catches what the moment misses.

**Push, don't only badge.** Window-close resolution also sends an email digest
from the daily job. A badge requires opening the app, and outcome-recording
latency is the loop's real failure mode. A `closing_soon` notice fires at
window_end − 14 days, when the window can still be *observed* rather than
reconstructed.

### §14.5 Trigger mechanism and loop-back

- A **daily scheduled job** selects `state='open' AND window_end < now()`,
  transitions to `window_closed`, and enqueues a resolution task; plus the
  −14d `closing_soon` pass.
- Resolution calls `record_outcome` → Brier `(confidence − outcome)²` →
  `mimamsa_calibration` upsert. `source_citation NOT NULL` is satisfied by the
  ledger row id — **the ledger is the citation.**
- **Loop-back into serving:** calibration writes bump `priors_version` in the
  session pin; drift-detection semantics extend to
  `calibration_updated_mid_session`; and phala/kala envelopes gain an
  epistemic annotation — "technique X on this chart: n=7, Brier 0.18". That is
  L5 doing exactly what STRUCTURAL mode promised.

> **[GROUNDED 2026-08-18 — v0.11] §14.2–§14.5 are BUILT and PROVEN LIVE.**
> PB-3 shipped the whole lifecycle (26-column `brahma_mimamsa_prediction_
> ledger`, 9 states, legal-transition matrix in code AND a DB freeze trigger;
> two-stage detection with deterministic Stage-2 enrichment; both confirm
> paths; the Samīkṣā tab with awaiting/open/resolve; the consolidated daily
> job; `recordConversationalOutcome` computing Brier with `unverifiable`
> triple-excluded — DB CHECK, DAL, and named predicate). PB-3 closed
> SHIP-DEGRADED — **the loop was inert: no live entry, no live exit** — and
> PB-3.1 (G1–G5) made it live piece by piece, until **C4-LOOP-LIVE-PROOF
> (2026-08-01) proved all six criteria against production with no fixture
> substitution**: a real reading produced real `detected` rows; the live
> review tab rendered them; a UI resolution wrote `outcome_value = NULL` on
> can't-tell under the CHECK constraint; the daily job transitioned a real
> row; exactly one outcome map with a live caller; the calibration leak guard
> mutation-proven 6/6 — with an uncoordinated real user on the review tab
> mid-proof (`PURNATA_CLOSE_REPORT_v1_0.md` §9). The §14.5 loop-back into
> serving remains correctly OFF per §14.6's collect-only phase and DVA
> Rulings 55/79. Still open here: the in-stream confirm affordance
> (`LogToSamiksha` — built, unmounted, blocked on the A-37 wire event), the
> −14d digest's real transport (log-only stub), and LEL-drafted outcomes.

### §14.6 Minimum-n gating and the collect-only phase (new v0.5)

**v0.1–v0.4's own illustrative annotation was "technique X on this chart: n=7,
Brier 0.18." At n=7 that is indistinguishable from a coin flip with vague
windows. Serving it as an epistemic annotation is precision theater — in the
one subsystem whose entire purpose is honesty.**

The arithmetic: the calibration grain is `chart × technique × ayanamsha`. At a
realistic single-operator rate of a few confirmed predictions per week spread
across techniques, with resolution windows of months to years, **most cells
will not reach meaningful n within five years, and many never will.**

**Three corrections:**

1. **Pool across charts by default.** The default calibration grain becomes
   `technique × ayanamsha`, pooled over all charts. Per-chart calibration is a
   long-horizon aspiration, served only where a cell independently passes
   threshold. This multiplies effective n by the number of charts under
   observation.
2. **Minimum-n gate on every served annotation.** Below threshold, **serve
   nothing** — not a hedged number. An `insufficient_calibration_data`
   `judgment_flag` is the honest output, and §N.6 rule 3 already establishes
   that an honest empty goes through flags rather than a hollow value.
   Threshold to be set empirically; it is not below n=30 for a point estimate.
3. **Report intervals, not points.** Where a cell does pass, serve the
   interval. "Brier 0.18" implies a precision the sample cannot support;
   "0.12–0.31 (n=34)" is the same information told honestly.

**The collect-only phase — explicit, and possibly years long.**

```
  PHASE C1 — COLLECT ONLY  (from day one; duration: years)
    ledger accrues · Samīkṣā operates · observatory displays
    NOTHING touches serving. No priors_version bumps from calibration.
    No epistemic annotations in phala/kala envelopes.

  PHASE C2 — PER-CELL ACTIVATION  (as thresholds pass, cell by cell)
    a cell that passes minimum-n begins serving its interval
    everything else stays in C1
```

L5 is sealed in STRUCTURAL mode. **STRUCTURAL honesty means the structure is
built and the values are empty until earned** — feeding n=7 noise into
readings would violate the seal's own premise. v0.1–v0.4's §14.5 loop-back
fired as soon as calibration writes occurred; it now fires per cell, on
threshold.

### §14.7 Designing for compliance decay (new v0.5)

**Assume the honest prediction: a single operator's outcome-recording
compliance decays within months. Every quantified-self product ever built
demonstrates this.** A design that requires sustained manual diligence for
years, and degrades silently when it does not get it, is a design that fails.

Mitigations, in addition to §14.4's badge, in-stream affordance, email digest
and −14d notice:

- **`lapsed` is normal and non-shameful.** No red counters, no guilt UI. A
  lapsed prediction is data about coverage, not a personal failure. Coverage
  rate is reported as a *statistic*, not a *scold*.
- **Batch resolution is first-class.** Resolving fifteen closed windows in one
  sitting must be a designed flow — a queue with keyboard-fast
  happened/didn't/partial/can't-tell — not fifteen separate interactions.
- **Auto-draft outcomes from the LEL.** Where a life event is already logged
  that plausibly resolves a window, pre-fill the resolution for confirmation.
  **This is NO-LEAKAGE-safe**: the invariant forbids `life_events` feeding
  *prediction generation*; post-hoc calibration reads are exactly what it
  permits. The draft is always human-confirmed.
- **The conversational capture moment (§6.6.3)** is the single strongest
  mitigation — it asks at the moment the user is already thinking about the
  domain, rather than requiring them to visit a tab.
- **Coverage as a first-class honesty metric.** If only 40% of closed windows
  are ever resolved, the calibration is drawn from a biased sample —
  memorable outcomes get recorded, unmemorable ones lapse. **Report
  resolution coverage alongside every Brier interval**, because a Brier score
  from a 40%-resolved sample is not the same claim as one from a 90%-resolved
  sample, and pretending otherwise is the subtlest dishonesty available here.

### §14.8 Capturing disagreement (new v0.5)

**The most valuable event a research instrument's conversation can produce is
the user saying "that's wrong."** Verified current state: it is only ever
another turn, and the feedback endpoint **silently discards** every rating
(F-25c — table dropped in WS-0, POST persists nothing, UI appears to work).

Grounded-and-wrong is the hard class. The gates catch *ungrounded* claims;
they cannot catch a reading where every fact is cited and the conclusion is
still off. Only the native can catch that — and he knows this chart better
than the instrument does.

**Design:**

- A **dispute affordance** on any turn: "this doesn't match what happened."
- Disputes persist as first-class rows keyed to `(message_id, claim_span)`,
  carrying the provenance stamp — never a discarded rating.
- The engine's response to a dispute must **re-retrieve, not re-word.** If
  challenged on a fact, go back to the data. If the data supports the original
  claim, **say so and show the grounding** — do not fold. Sycophantic
  capitulation to the operator is corruption of the instrument, not politeness.
- Disputes surface in Samīkṣā alongside predictions. A disputed reading is
  calibration-adjacent evidence and belongs in the same review flow.
- **Restore or replace the feedback endpoint before it collects another
  signal it will throw away.**

> **[GROUNDED 2026-08-18 — v0.11]** Still fully unbuilt, and the feedback
> endpoint still discards every rating at HEAD (F-25c stands verbatim —
> "returns empty/ok stubs"). Elevated to A-48 with a concrete home: the dock
> card / turn menu affordance, a first-class dispute row keyed to
> message_part + D-16 stamp, reviewed in Samīkṣā. §19.5 wave 3.

### §14.9 Sycophancy drift over a long relationship (new v0.5)

Over hundreds of conversations with one user, a model shaped by that user's
reactions drifts toward telling him what he responds well to. **In this domain
that is lethal to the mission**: the premise is *testable* prediction, and
drift toward pleasing readings corrupts the ledger upstream of any Brier score
— the calibration would then be measuring a flattered instrument against
itself.

Defenses, all cheap:

- **Synthesis is stateless with respect to the user's reactions.** Recall past
  *conclusions* (§11.5); never recall sentiment, ratings, or which readings he
  liked.
- **Periodic identical-question diffing.** Run a fixed question set through a
  fresh context on a schedule and diff against prior runs. Drift shows up as
  divergence.
- **Optimism-bias tracking as a first-class observatory metric**: predicted-
  favourable rate versus base rate, over time. A rising favourable rate with
  flat outcomes is the signature.
- The dispute flow (§14.8) explicitly **must not** train toward agreement.

### §14.10 NO-LEAKAGE, enforced four ways

The invariant — `life_events` must never feed prediction generation, only
post-hoc calibration — is too important for prose alone.

| Arm | Mechanism |
|---|---|
| **1. DB role separation** | The serving/planner role has no SELECT on `life_events`, on ledger outcome columns, or on open-prediction-scoped calibration rows. Grants, not conventions. See §7.4. |
| **2. Registry flag** | Outcome and LEL read tools carry `calibration_context_only`, excluding them from every planner projection and from `prashna_ask`'s tool set. The mutation class (§8.4) gives this a home. |
| **3. Out-of-process writer** | The ledger writer runs outside the synthesis process and holds the only write role. |
| **4. CI canary** | A canary query per release asserts that no serving-path plan can reach a leakage-flagged tool. |

---

## §14A — Security, cost governance, and durability (new v0.5)

Three areas v0.1–v0.4 omitted entirely. Each is verified-absent today
(§16.6), and each becomes materially more exposed under the target
architecture.

### §14A.1 `prashna_ask` is a prompt-injection surface

A foreign — possibly compromised — MCP client passes free text that our engine
feeds to **our planner and our agentic loop, with tool access**. Entitlement
gating is designed (§6.3); containment is not.

Verified today: `queryText` flows raw into `runPlanner`
(`consult/route.ts:436–444`), prior turns raw into `plannerHistory`
(`:407–414`). The only thing resembling a defense is
`QUERY_INDEPENDENCE_GATE` (`lib/prompts/templates/shared.ts:55`), instructing
the model to treat history as "background noise" — **a prompt heuristic, not a
defense**.

Required:

- **Structural containment**: the question is data, never instruction.
  Delimited and labelled in the prompt; the planner's output is Zod-validated
  against a closed plan type (§9.5), so injected text cannot *become* a plan.
- **The chart_id is never taken from the question text.** It comes from the
  authenticated call and is re-authorized per capability. This already holds
  via `chart_agnostic_gate.ts`'s build-time enforcement — **state it as a
  security property**, because it is the main cross-tenant exfiltration
  defense.
- **Answer-side scan**: an answer must not contain `chart_id`s or facts from a
  chart the caller is not entitled to. The register lint (§13.5) already walks
  the text; entitlement checking is a second pattern class in the same pass.
- **Tool-sequence anomaly logging**: a plan that reaches for unusual
  capability combinations is worth a trace flag, not a block.

### §14A.2 Rate limiting and spend caps

**Verified absent on chat, with no place to put it**: no `src/middleware.ts`
exists; grep for `rateLimit|429` under `src/app/api/chat` returns zero. The
"budget" code allocates token budgets per tool call and does retrospective cost
analytics — **neither blocks a request** (F-25d).

Under the target this gets worse: `prashna_ask` is *"the most expensive tool by
two orders of magnitude"* (§6.3) and is exposed to foreign clients. **One
runaway MCP client can spend real money on Tier A tokens with nothing in the
path to stop it.**

Required, in order:

1. A middleware layer (it does not exist — create it).
2. Per-user request rate limits on chat and on `prashna_ask`, reusing
   `lib/mcp/rate_limiter.ts` rather than writing a second one.
3. **A hard per-turn spend ceiling enforced before dispatch**, and a per-user
   daily ceiling. Exceeding it is a designed failure state (§12.10), not a 500.
4. Cost attribution per `(user, channel, model)` so the observatory can see
   who is spending what — the panels exist; the attribution does not.

### §14A.3 Backup and durability of the irreplaceable data

**This is the closest thing in this document to a mission-level omission.**

Charts are rebuildable. Layer tables are derivable. **The conversation store
and the prediction ledger are the only data in the system that cannot be
regenerated** — and D-16 makes the point precisely: there is no build archive,
so a past reading is unreproducible and **the ledger row is its only witness**.

Verified: no scheduled backup job, no restore script, no PITR/RPO/RTO
documentation, no DR runbook in the repo. Only one-off tooling —
`infra/teardown/00_archive.sh:149` (teardown `pg_dump`) and an archived
migration script that once set `--backup-start-time=02:00`
(`99_ARCHIVE/scripts/gcp_migrate.sh:145,216`). Cloud SQL automated backups may
be enabled at the instance level; **nothing in-repo verifies or documents
that**, which means nobody knows.

Required:

- **Verify and document** the Cloud SQL backup configuration — PITR window,
  retention, and where it lives. First action, costs an hour.
- **A restore runbook that has actually been executed once** against a scratch
  instance. An untested backup is a belief, not a backup.
- **Independent logical export of the two irreplaceable tables** —
  `conversation_messages` + `message_parts`, and the prediction ledger — on a
  schedule, to separate storage. These are small, slow-growing, and
  disproportionately valuable.
- **Stated RPO/RTO.** For a single-operator research instrument, "24h RPO on
  layer data, near-zero on ledger and conversations" is a defensible posture —
  but it must be *stated*, so restore decisions are not improvised during an
  incident.

> **[GROUNDED 2026-08-18 — v0.11] §14A is the least-moved section of the
> document, and it matters more now than when it was written.** Verified at
> HEAD: `src/middleware.ts` still does not exist; zero `rateLimit|429` hits
> under the chat AND pariprashna API trees; nothing blocks a request or a
> spend. What changed is the exposure: `prashna_ask` is now LIVE to foreign
> MCP clients (profile-gated, cost-capped by its own budget arbitration, but
> with no per-user rate or spend ceiling), the Paripraśna route runs
> 16-iteration deep dives by default for most picker states, and PB-4 wants
> to make this surface the DEFAULT. Two partial mitigations shipped
> incidentally — `maxDuration = 120` and the shared QoS dispatch queue
> (interactive priority class) — neither is a cap. Backup posture: last
> verified state (F-25t, 2026-07-19) was PITR **disabled**, daily backups ×7,
> **no restore drill ever executed**; nothing in the PB corpus re-verified
> it since. **A-46 binds this section to the PB-4 gate: a flagged surface
> without caps is an experiment; a default surface without caps is an
> incident.**

---

## §15 — Component inventory

| Component | What it is | Target | Note |
|---|---|---|---|
| `@marsys/contract` | Workspace pkg: envelope types/builders, CapabilityDescriptor, density_contract, trim-report, PlanReceipt, scope tuple | **NEW** | Kills the hand-mirrored envelope |
| Registry (`lib/retrieval/registry/`) | Sole capability source of truth | **EVOLVE** | density_contract mandatory; `mutation:true` class; sidecar tools pulled in; zero imperative registration |
| Projection generators | MCP-full, MCP-compact (+`marsys_drill`), Chat per-turn filter | **NEW** | Pure functions of the registry; `quirks.max_tools` selects |
| `tool_name_bridge.ts` | Alias mapper | **RETIRE→shim** | Replay of persisted conversations only |
| Planner pipeline | scope → route → constrained LLM synth → vidhi validator | **REPLACE** (3→1) | All three existing planners survive as stages |
| Intent classifier | Deterministic first pass + LLM fallback → scope tuple | **REPLACE** (3→1) | Closes CR-28 |
| Agentic loop service | Channel-agnostic engine core | **REPLACE** (extract) | Door 1 streaming; Door 2 `prashna_ask` |
| MCP edge (`platform-mcp`) | Separate deployable, OAuth, no DB | **EVOLVE** | Keeps isolation + distinct auth surface; loses hand-written envelope/tool code |
| Conversation store | `conversation_messages` + `message_parts` + `conversation_summaries` | **REPLACE** | Canonical parts; canonical tool names only |
| History compression | Summarizer worker + prefix-stable splice + pgvector recall | **REPLACE** | Durable rows, not in-flight |
| Grounding gate | Envelope-native, pre-commit citation-part validator | **REPLACE** | Streaming citation validator deleted/folded |
| Stream protocol + client reducer | Typed SSE + purpose-built renderer | **NEW** | Replaces AI SDK transport + `useChat` |
| ModelPlane (`lib/models/registry.ts`) | Registry-as-data + health probe + tiers + CachePlanner + reasoning cost | **EVOLVE** | OpenRouter meta-provider; Tier C fat-prompt path |
| Session pin | Build-provenance pin + drift detection | **EVOLVE** | Promoted MCP-only → all conversations |
| Prediction/calibration loop | detect → confirm → ledger → jobs → Samīkṣā → outcome → calibration | **NEW** (assembled) | Ledger writer out-of-process; NO-LEAKAGE ×4 |
| FROZEN orchestrator + WriterBase | L0–L5 build driver | **KEEP** | Sacrosanct; contract untouched |
| python-sidecar | Residual compute | **KEEP** | Its two *serving* tools move into the registry; compute stays |
| Trace emitter + SSE | Trace → `/admin/trace` | **KEEP/EVOLVE** | Gains PlanReceipt rendering |
| Firebase Auth | Browser IdP | **KEEP** | + roles/entitlements tables (NEW) |
| Paripraśna UI | `/clients/[id]/pariprashna` | **RENAME + REBUILD?** | consult renamed; consume absorbed. Shell fate = OT-8 |
| Samīkṣā UI | Review tab + dashboard badge | **NEW** | Per-chart + global roll-up |
| Nirmāṇa | Build tracker | **KEEP** | Exists |
| Cockpit | Super-admin ops (12→~6) | **MERGE** | Registry page becomes canonical registry browser |
| Observatory | Analytics (10→~5) | **MERGE** | + model plane + calibration panels |
| Jobs runner | Probes, window-close, digests, summarizer, ledger writer | **NEW** | Deployment shape = OT-3 |
| Dead list implementations | `AdaptiveMessageList`, `VirtualizedMessageList`, orphaned hooks | **DELETE** | Zero importers |
| `/admin/foundation`, `/admin/tracker`, `/dev/*` | Historical/dev surfaces | **RETIRE** | Build arc complete |

---

## §16 — Forensic appendix: legacy defects

Preserved because each names a trap the rebuild must not re-enter.

> **Verification standing.** Every row was **re-verified against the working
> tree on 2026-07-19** following the adversarial review (§18/T-7). Rows that
> changed on re-verification are marked **[CORRECTED]** with the original claim
> struck, per §21 rule 3 (this appendix is append-only; wrong claims are
> corrected in place with their error visible, never deleted). Current-state
> claims decay — this appendix carries a re-verification obligation at every
> version bump, and §0.6 states how.

### §16.1 Streaming and render

| # | Defect | Location |
|---|---|---|
| F-01 | Entire pipeline (planner, hydration, all tool execution) completes **before** the response body opens; stages then replayed retroactively in one burst. | `api/chat/consult/route.ts` 435–454, 688–689, 740–796, 988; `lib/pipelines/shared/run_adapter_dispatch.ts` 291, 294–304 |
| F-02 | Reasoning written as `{type:'reasoning', delta} as any` — not a valid chunk type for the SDK major version in use; requires start/delta/end with a **part** id, but the **message** id is passed. | `run_adapter_dispatch.ts` 332–334 |
| F-03 | `as any` casts suppress protocol type errors throughout the writer path. | `run_adapter_dispatch.ts` 294, 325, 329, 354, 574 |
| F-04 | Progress region (StageStepper, ToolCallCard stack, StillWorkingIndicator) mounted **above** message parts inside the same column, gated on `isStreaming` → mounts shove text down mid-stream; **unmounts at stream end**, snapping the answer upward. | `ConsumeChatV2.tsx` 683–697 |
| F-05 | GFM footnote definitions instructed to be emitted at the **end** → references render as literal text throughout the stream, then the whole message reparses and re-lays-out at completion. | `lib/synthesis/prompts/synthesis_prompt_v2.ts` 26–46; `MarkdownContent.tsx` 150–158 |
| F-06 | Three regex passes over the **entire accumulated text on every delta**; a partially-streamed id flips prose→badge mid-paragraph, rewrapping the line. | `ConsumeChatV2.tsx` 255–277, 307–310 |
| F-07 | Streaming cursor appended as a **sibling after all block-level markdown output** → renders on its own line at the left margin below the last block; never after the last glyph. | `MarkdownContent.tsx` 193–197 |
| F-08 | No throttling on the runtime; five independent subscribers re-run per token; one writes `sessionStorage` on **every token**. | `ConsumeChatV2.tsx` 1033, 1302, 1342, 1435, 1452–1457, 1526, 2247–2275 |
| F-09 | `useDataParts` memoizes on values that change every delta → eight downstream memos recompute per token per message. | `lib/chat-v2/useDataParts.ts` 35–61; `ConsumeChatV2.tsx` 537–585 |
| F-10 | Two data-part transports (live metadata vs persisted content) merged **without dedupe** → the same logical part can render twice after persistence. | `useDataParts.ts` 26–33 |
| F-11 | `smoothStream` imported but **never used** on the live adapter path → raw multi-paragraph provider slabs. | `route.ts` 5 |
| F-12 **[CORRECTED]** | Smooth-behaviour scrolling re-triggered while content grows every frame → rubber-band bounce. ~~The good scroll mechanism exists but is behind a default-off flag.~~ **Wrong.** `useScrollDiscipline` (2,093 bytes, `X-S6`) is **live and unflagged** — imported at `ConsumeChatV2.tsx:22`, destructured at `:1522` (`isAtBottom, unreadCount, sentinelRef, incrementUnread, scrollToBottom`), no env gate, no conditional. It is an `IntersectionObserver` rooted on `[data-testid="v2-thread-viewport"]`. **Only the `scroll-smooth` defect stands.** §12.6 must therefore *harden an existing live mechanism*, not enable a dormant one — and must add the upward-intent break, which the hook does not implement. | `ConsumeChatV2.tsx` 22, 1522, 1577; `platform/src/hooks/useScrollDiscipline.ts` |
| F-13 | Persistence write-through **awaited inside the stream before the finish chunk** → streaming dots shown on a finished answer during DB bookkeeping. | `run_adapter_dispatch.ts` 354, 492–571, 574 |
| F-14 | Client posts to `/api/chat/consume`, a 308 redirect stub → every turn pays a redirect + full body re-POST. | `ConsumeChatV2.tsx` 2249; `api/chat/consume/route.ts` 1–25 |
| F-15 **[CORRECTED]** | Three generations of chat plumbing coexist. ~~All four modules have zero importers.~~ **Split, precisely:** `AdaptiveMessageList` — genuinely importerless ✅. `useChatSession` (`platform/src/hooks/`) — genuinely importerless ✅. `VirtualizedMessageList` — **has an importer** (`AdaptiveMessageList.tsx:6,65`); it is *transitively* dead, a weaker claim. `useChatLifecycle` — lives at `platform/src/lib/hooks/` (not `hooks/`) and has **8 importers**, 5 of them production components under `components/consume/lifecycle/`; all are `import type` only, and that folder has no external importers — so the accurate claim is "type-only importers inside a dead cluster." Deletion order matters: the cluster must go before the hook. The virtualizer's fixed-120px estimate would jitter catastrophically if ever enabled. | `VirtualizedMessageList.tsx` 30–31, 62–88; `AdaptiveMessageList.tsx` 6, 65 |
| F-25b **[NEW 2026-07-19]** | **A fully-built error classifier is dead code.** `platform/src/lib/chat/classify-error.ts` implements 7 error kinds (rate_limit, insufficient_credits, model_overload, auth, timeout, network, unknown), each with a user-facing title and hint. **`classifyChatError` is never imported anywhere.** Users get generic AI-SDK error surfacing instead. §12.11's failure UX should adopt this file rather than write a new one. | `platform/src/lib/chat/classify-error.ts` |
| F-25c **[NEW 2026-07-19]** | **The feedback endpoint lies.** `api/conversations/[id]/feedback/route.ts` — header reads *"message_feedback table dropped in WS-0. Endpoint returns empty/ok stubs."* GET returns `{feedback: []}` (`:10`); **POST validates auth, echoes the rating back, and persists nothing** (`:18`). `src/hooks/useFeedback.ts` calls it, so the UI appears to work while discarding every signal. Every thumbs-up/down the native has ever given is gone. | `api/conversations/[id]/feedback/route.ts` 2, 10, 18 |
| F-25d **[NEW 2026-07-19]** | **Chat routes have no rate limit and no spend cap — and there is no middleware layer to add one at.** `src/middleware.ts` does not exist. Rate limiting exists elsewhere (chart creation 5/hr at `api/clients/create/route.ts:248–271`; MCP via `lib/mcp/rate_limiter.ts`) but grep for `rateLimit\|429` in `src/app/api/chat` returns **zero hits**. The "budget" code (`lib/pipeline/budget_arbiter.ts`, `lib/observatory/budget/evaluate.ts`) allocates token budgets per tool call and does retrospective cost analytics — **neither blocks a request**. | `src/app/api/chat/**` (absence); `src/middleware.ts` (absent) |
| F-25e **[NEW 2026-07-19]** | **`parts_json` has no version discriminator.** Declared `jsonb DEFAULT '[]' NOT NULL` at `supabase/migrations/0001_brahma_baseline.sql:1702`; neither it nor `metadata_json` carries a schema-version column. §11.1's own analysis says AI SDK v4/v5 part shapes differ — so **the blob→parts migration is unverifiable by this document's own argument**. Any migration must infer version from shape and accept a residue it cannot prove correct. | `0001_brahma_baseline.sql` 1702 |
| F-25f **[NEW 2026-07-19]** | **Stream resume is snapshot-based, not event replay.** `pending_streams` is written debounced during the stream (`lib/persistence/pending_streams_writer.ts:29`); `api/chat/consult/resume/route.ts:20–54` returns `accumulated_text` sliced by `since_chars`. `last_event_seq` **is stored and returned (`:52`) but never consumed by the client.** Recovery is one-shot on page reload only (`ConsumeChatV2.tsx:1423`, `:1809–1849`, rendering *"(Stream interrupted — showing recovered partial response.)"* at `:1838`). **A mid-session network drop does not reconnect.** No `Last-Event-ID`, no replay-from-seq. | `pending_streams_writer.ts` 29, 72; `consult/resume/route.ts` 20–54; `ConsumeChatV2.tsx` 1423, 1809–1849 |
| F-25g **[NEW 2026-07-19]** | **`audience_tier` is half-excised, and the residue is load-bearing in three places.** The DB column was dropped (migration 090, 2026-05-28), gating was removed by the DG1 ruling, and `lib/perf/audit_nightly.ts:154–157` demotes it explicitly (*"audience_tier gate removed — all responses checked uniformly … field is logging metadata only"*). **Yet** it is still stamped at `consult/route.ts:459` (`plan.audience_tier = isSuperAdmin ? 'super_admin' : 'client'`), still forwarded as the `X-MCP-Audience-Tier` header (`lib/mcp/bundle_adapters.ts:142`), still a **required** field in two JSON schemas (`audit_event.schema.json:8,15`; `query_plan.schema.json:8,15`), still keys prompt-template lookup (`lib/prompts/index.ts:10,35,37,45,58,61`) and is injected into adjudicator prompt text (`adjudicator_prompt_v1.ts:40`). **This is a live D-15 violation with a concrete migration.** See §13.7. | 14 sites, listed in §13.7 |

### §16.2 Register leakage

| # | Defect | Location |
|---|---|---|
| F-16 | Prompt **requires** the model to emit internal ids in visible prose; UI then attempts to suppress them. Emit-then-suppress leaks under drift and is visible mid-stream regardless. | `synthesis_prompt_v2.ts` 26–46; `MarkdownContent.tsx` 139, 158 |
| F-17 | Tool payloads reach synthesis carrying signal ids, asset names, layer tags — the model's entire evidence is internal-register. | `route.ts` 161–171 |
| F-18 | Register control is a single sentence in one of three styles; the default style has none. | `lib/claude/system-prompts.ts` 48–49 |
| F-19 | Enforcement is client-side regex for one pattern family; the gate validates provenance, not vocabulary. | `lib/synthesis/citation_check.ts`, `streaming_citation_validator.ts` |

### §16.3 Historical defects worth remembering

| # | Defect | Status |
|---|---|---|
| F-20 | Weak 32-bit rolling hash in the retrieval cache collapsed distinct `chart_id`s to one shared cache key under concurrent load — **wrong-chart substitution**, load-correlated and therefore invisible in isolated probes. | Fixed (LCA-17 / WP-0.1): SHA-256 key-sorted cache keys + server-side chart_id echo-back guard |
| F-21 | Consult path unconditionally queried the retired `reports` relation and **failed for every chart in production**. | Fixed 2026-07-13 (LCA-2 / WP-1.1) |
| F-22 | R11E loop feature flags were pure stubs — `adapter.loop()` existed but the route had zero references; Gemini cache flag likewise never called. | Historical |
| F-23 | Unapplied migrations silently broke production features (branches, search, pin/archive). | Historical |
| F-24 | Stream-resume token forgery vulnerability. | Found and fixed during CHAT_V2 red-team (P.5): `user_id` column + ownership check |
| F-25 | Prop-drop bug: a component did not destructure `initialMessages`, so local state shadowed the prop and silently dropped deeplink context on every navigation. | Historical |

### §16.4 Corrected counts

| Item | v0.1–v0.4 said | Verified 2026-07-19 |
|---|---|---|
| Alias count | 45 | **55.** Three sources disagree: 55 actual (35 direct `server.tool` + 17 `regAlias` + 3 `globalAlias`), 47 in the file header (`register_p1_aliases.ts:16`), 45 in the `server.ts` census (`:493`). Names missing from the census include `ganita_ayurdaya_get`, `ganita_medical_get`, `ganita_vichara_get`, `ganita_yoga_firings_get`, `kala_priority_ranking_get`, `phala_predictive_anchors_get`, `ref_sign_medical_get`. |
| Total tools | ~118 | ~~**Census constant says 120** (`REGISTERED_TOOL_COUNT`, `server.ts:520`); **raw `server.tool(` count is 126.**~~ **[CORRECTED PG-1 — `PG1-R1-0002`/`-0003`, F-25i]** The "126 raw count" itself undercounts — it missed the `regAlias()`/`globalAlias()` helper registrations. The **live tool-name surface is 139** (120 census + 5 `registry_bridge.ts` + 3 `register_p1_synthesis.ts` + 10 `register_p1_aliases.ts` + 1 `register_p2_dasha_lord.ts`, the last imported/called at `server.ts:364` but never in the running total), over **119 distinct registry URIs** (`platform/src/lib/retrieval/registry/`). The health endpoint reports the stale 120. **Four numbers, none interchangeable: 119 registry URIs · 139 served tool names · 120 stale census · 113 = `CAPABILITY_MANIFEST.json`, a governance-artifact catalog, not an MCP registry at all (`PG1-R1-0001` category error).** This is exactly what D-08's generated projections exist to eliminate. |
| Planners | 3 | ~~**2 live, 2 dead**~~ **[CORRECTED PG-1 — `PG1-R3-0001`]** **4 planner surfaces: 2 live-but-incompatible** (`PipelinePlan` on web consult vs `VidhiPlan` on MCP `plan_retrieval` — the identical question produces two non-interoperating plan objects), **2 dead islands** (`retrieval/router/`, `lib/vidhi/compiler.ts`). See §16.5. |
| `density_contract` coverage | 6 of ~118 | **Confirmed: 6.** `get_dasha_lord_capability.ts:148`, `get_vichara.ts:124`, `get_yoga_dosha.ts:68`, `get_yoga_firings.ts:61`, `register_d9_judgment.ts:415`, `L2_bodha/query_signals.ts:226`. Five of six are L1. |

### §16.5 The planner census, corrected

v0.1–v0.4 said "three unreconciled planners." The adversarial review said four.
**Both were wrong.** Verified:

| Component | Path | Status |
|---|---|---|
| Live agentic loop | `platform/src/lib/synthesis/agentic_loop` | **LIVE** — the real loop; 18+ test files import it |
| `pipeline_planner` | `platform/src/lib/pipeline/pipeline_planner.ts` | **LIVE** — what the chat route calls |
| D2 router | `platform/src/lib/retrieval/router/` | ~~**LIVE**~~ **[CORRECTED PG-1 — `PG1-R3-0001`]** **DEAD ISLAND** — zero production importer (only its own test + barrel). |
| vidhi compiler | `platform/src/lib/vidhi/` | ~~**LIVE** — behind `plan_retrieval`~~ **[CORRECTED PG-1 — `PG1-R3-0001`]** **DEAD ISLAND** — `platform/src/lib/vidhi/compiler.ts` has zero production importer. The LIVE vidhi planner is **`platform-mcp/src/resources/vidhi/plan_builder.ts` (`buildVidhiPlan`)** behind MCP `plan_retrieval` — a *different* module from this platform-side one, which is an unwired duplicate. |
| `adaptive_planner.ts` | `platform/src/lib/retrieval/**adapters**/agentic_loop/` | **DEAD** — 3.6KB; exports `planNextAction`/`shouldStopEarly`; its only importers are `loop_engine.ts` and `reflection.ts`, both siblings in the same folder. **The entire 7-file folder is an unreferenced island.** |
| `singlePassPipeline` | `platform/src/lib/pipelines/single_pass/` | ~~**DEAD BRANCH** — operationally unreachable.~~ **[CORRECTED PG-1 — `PG1-R3-0004`, supersedes both this row AND C-3's "not dead, do not delete"]** Precise status: a **test-load-bearing structural scaffold NOT on the runtime path.** The module has exactly 2 production importers (both internal to `lib/pipelines/`: the barrel + `selector.ts`), the selector's own exports have **zero** production importers (the selector never runs live), and `singlePassPipeline` is an inert descriptor (`{kind, describe()}`, no `run()`). The **actual** runtime single-vs-agentic decision is made inline at `run_adapter_dispatch.ts:314` (`useAgenticLoop && loopConfig ? runAgenticLoop(...) : adapter.chat(...)`), onfinish hardcoded `pipelineKind:'agentic'` at `:494`. So the live single-pass CODE PATH is the inline `adapter.chat` branch, not the module. The arch doc is right the *selector* never reaches it; C-3 is right it is not *orphan-deletable* (barrel + tests break); neither was precise. If deleting: remove selector + single_pass + agentic descriptor + their tests together; the live path is unaffected. |

**Trap for the rebuild:** there are **two folders named `agentic_loop`** —
`lib/retrieval/adapters/agentic_loop/` (dead island, contains
`adaptive_planner`) and `lib/synthesis/agentic_loop` (live). Any statement
about the loop or the planner must name the full path. This near-namesake
collision produced the erroneous census in v0.1–v0.4 *and* in the adversarial
review.

Net: ~~the unification is **3 live planning components → 1 pipeline**, plus
**deletion of two dead islands**. Materially smaller than "four planners"~~ **[CORRECTED
PG-1 — `PG1-R3-0001`/`-0004`/`-0007`]** The precise live-planning inventory is: the
**live agentic loop** (`synthesis/agentic_loop`, execution not planning), the **web
`pipeline_planner`** (emits `PipelinePlan`), and the **MCP `plan_builder`** (emits
`VidhiPlan`) — the last two are the two genuinely-divergent live *planners*, plus the
two dead islands above (`retrieval/router/`, `lib/vidhi/compiler.ts`) and the inert
`single_pass` scaffold. The unification is therefore **reconciling the web
`PipelinePlan` onto the MCP `VidhiPlan` shape** (which already carries floor + dark +
`capability_version`), and R-3's falsification (§9.5, `PG1-R3-0007`) prices this at
**week-scale integration, not a contradiction** — ~80% already exists as `VidhiPlan`.
§9.6 records why it is still harder than it looks.

### §16.6 Capabilities that do not exist today

The forensic appendix above records what is *broken*. This records what is
**absent** — verified 2026-07-19. Each is a target-architecture obligation
that v0.1–v0.4 assumed away.

| Capability | Status | Evidence / note |
|---|---|---|
| Reconnection / event replay | **ABSENT** (snapshot resume only) | F-25f. `last_event_seq` stored, never consumed. |
| Rate limiting on chat | **ABSENT** | F-25d. No middleware file exists at all. |
| Spend caps that block | **ABSENT** | Budget code allocates and analyses; nothing blocks. |
| Backup / DR posture | **ABSENT in repo** | Only one-off tooling: `infra/teardown/00_archive.sh:149` (teardown `pg_dump`), `99_ARCHIVE/scripts/gcp_migrate.sh:216` (one-time migration; sets `--backup-start-time=02:00` at `:145`). **No scheduled backup job, no restore script, no PITR/RPO/RTO documentation, no DR runbook.** Cloud SQL automated backups may be on at instance level; nothing in-repo verifies or documents it. |
| Prompt-injection defense | **ABSENT** | `queryText` flows raw into `runPlanner` (`consult/route.ts:436–444`); prior turns raw into `plannerHistory` (`:407–414`). Nearest thing is `QUERY_INDEPENDENCE_GATE` (`lib/prompts/templates/shared.ts:55`) instructing the model to treat history as "background noise" — a prompt heuristic, not a defense. |
| `parts_json` migration tooling | **ABSENT** | F-25e. No transform script, and no version discriminator to write one safely against. |
| TTFT / streaming metrics | **ABSENT** | Per-request trace rows exist (`lib/trace/writer.ts:27,55,171–174`) — debugging, not aggregate. Grep for `ttft\|first_token\|histogram` across `src`: **zero matches.** You cannot answer "what is p95 TTFT this week" without writing new SQL. |
| Clarifying questions | **ABSENT** | Grep for `clarif\|underspecified\|needs_clarification\|ask_back`: one irrelevant hit. The planner has exactly two outcomes — a `PipelinePlan`, or `PlannerFault` → 422 (`consult/route.ts:445–453`). **There is no state in which the engine returns a question to the user.** See §6.6. |
| Disagreement / correction capture | **ABSENT (worse: stubbed)** | F-25c. Saying "that's wrong" is only ever another turn, and the feedback UI silently discards. |
| Reader-facing signal text | **ABSENT** | `bodha_msr_signals` has `signal_summary_text` (*"lossless deterministic NL (every config key); embedding input"*) and `signal_headline_text` (*"short deterministic sentence"*) — `migrations/325_l2_bodha_enriched_schema.sql:70–71`. **Both are deterministic machine renderings of config keys; neither is plain language.** §13.6's editorial problem is therefore real and unowned. |
| Remedy register guardrail | **PARTIAL** | The *citation* gate exists — `citation_check.ts:91` `PRESCRIPTIVE_CLASSES = {'remedial','predictive'}`, hard-failing zero-citation prescriptive responses at `:129–135`. Prompt-side `CALIBRATION_LANGUAGE_GATE` bans "will happen"/"guaranteed"; `remedial.ts:35,47` require naming the traditional source and framing as mitigation. **But nothing enforces "the tradition prescribes X" vs "you should do X"** — no lint on second-person imperative, no classifier on remedy register. The line is a prompt instruction checked by no code. See §13.8. |
| Mobile design | **PARTIAL** | Tailwind `md:` breakpoints only — no `sm:`/`lg:`/`xl:` tiering. Mobile drawer `ConsumeChatV2.tsx:1966`, sidebar toggle `:2056` (44px touch target), camera shortcut `:1224–1233`. **No `useMediaQuery`/`matchMedia`, no touch/swipe handlers, no virtual-keyboard handling.** A two-state desktop/mobile split, not a responsive system. |
| Accessibility | **PARTIAL — better than assumed** | Genuinely present: message log landmark `ConsumeChatV2.tsx:1579–1583` (`role="log" aria-live="polite" aria-atomic="false"`), streaming markdown toggling `aria-live` only while streaming (`MarkdownContent.tsx:172–173`), SR-only announcer (`AssistantMessage.tsx:129`), `role="status"` across four components, `role="alert"` on validator bands, icons `aria-hidden`, buttons labelled. **Missing:** focus trap for modal/drawer, skip links, and any focus management beyond textarea `.focus()`. **This is an asset to preserve, not a gap to fill** — see §12.13. |

### §16.7 New forensic defects — PG-1 grounding-audit wave (2026-07-19)

Append-only, per §21 rule 3. Continues the F-number sequence from §16.1 (highest was
F-25g). Each row is a NEW current-state defect surfaced by the PG-1 wave and not
already carried above; the driving PG1 finding id is cited. Full detail:
`PARIPRASHNA_GROUNDING_AUDIT_REPORT_v1_0.md §2`.

| # | Defect | Severity | Location / evidence | Finding |
|---|---|---|---|---|
| **F-25h** | Stale self-referential parity comment — `run_adapter_dispatch.ts:357` claims the adapter citation gate "mirrors the legacy gate at `route.ts:1373-1475`", but `consult/route.ts` is only 1030 lines; the range does not exist. The "mirrors legacy" framing throughout §16 may itself be stale — the adapter path may be the only citation gate left. | low | `run_adapter_dispatch.ts:357`; `consult/route.ts` (1030 lines) | `PG1-C1-0012` |
| **F-25i** | Hand-maintained tool census wrong — `server.ts:522 REGISTERED_TOOL_COUNT = 120` (self-labelled "authoritative") undercounts 4 files; live surface is **139** tool names over **119** registry URIs; the health endpoint reports the stale 120. GA.1/B.8 drift class. Fix: compute from `server.registrationCount` at runtime. | high | `server.ts:522,364`; `registry_bridge.ts`; `register_p1_aliases.ts` | `PG1-R1-0002` |
| **F-25j** | `drill_pointers`/`recover_via` degrade to the literal string `"unknown_tool"` on sidecar/alias-backed tools (`kala_windows_get` ×3, `phala_outlook_get` ×2), making the recovery pointer unusable ("call `unknown_tool` again"); registry-backed L1 tools resolve correctly. Tool-name-threading bug in the trim-report constructor for the alias path. | medium | `mcp:kala_windows_get`, `mcp:phala_outlook_get`; fallback string `register_p1_ganita.ts:148`, `register_p1_aliases.ts:181` | `PG1-R2-0001` |
| **F-25k** | `phala_anchors_get` schema over-promises — `date_range` is `.optional()` in the tool JSON/Zod schema but **mandatory** at the sidecar (`/api/compute/phala/event_anchors` 422s "Field required"); the alias wrapper synthesizes no default. First-day hard error on documented usage. | medium | `register_p1_aliases.ts:1294-1297`; live 422 | `PG1-R2-0002` |
| **F-25l** | `ref_dignity_reference_get` returns **400 `internal_error`** ("platform DB query failed: 400") on its flagship documented filter `planet=Saturn` — a broken code path on a non-exotic parameter, surfaced as a 500-class error instead of an honest empty. | high | `mcp:ref_dignity_reference_get` | `PG1-R2-0003` |
| **F-25m** | Default legacy envelope leaves top-level `pagination.total` null even when `content.total` is known one level down (520/340/39 observed) — false "total unknown"; populated only on the v3 path. Fix: always promote `content.total`. | medium | `mcp:ganita_strength_get`/`ganita_condition_get`/`ganita_nakshatra_get` | `PG1-R2-0008` |
| **F-25n** | Three KEYSTONE sidecar tools (`mimamsa_calibration_get`, `mimamsa_insight_get`, `phala_mitigation_get`) double-encode their payload as a JSON **string** one level deeper than every other tool; `phala_mitigation_get`'s is additionally truncated mid-JSON by the budget. Breaks uniform envelope parsing. (Confirms A-04's sidecar pull-in inventory from the wire shape.) | medium | `mcp:mimamsa_calibration_get`, `mcp:phala_mitigation_get` | `PG1-R2-0010` |
| **F-25o** | Dead cost-accounting schema — `llm_usage_events`, `llm_provider_cost_reports`, `llm_cost_reconciliation` exist with the exact cost-attribution columns §14A.2 says are needed, and hold **0 rows each**, never wired into the request path. `query_trace_steps.latency_ms` is NULL on all 493+ rows, `step_type` is `'sql'` only. Cost/latency budgets in §14A.2/§17.4/§17.8 are design targets against **zero measured baseline**. Fix: wire the existing schema, don't design a new one. | medium (blocks §17.4/§17.8) | `db:llm_usage_events`, `db:query_trace_steps` | `PG1-D2-0001`/`-0002` |
| **F-25p** | Two disjoint, unreconciled prediction ledgers with no shared id space — `mcp_predictions` (chat-side detector path, **0 rows**, id `PPL.CAL.*`) and `mimamsa_predictions` (L5 build-time, **384 rows**, the one `mimamsa_calibration`/`phala_anchors` reference). §7's diagram presents one ledger; the codebase built two. §7.4 NO-LEAKAGE cannot say which it gates. | medium | `calibration_producer.ts:61`; `assetClearSpec.ts:119`; `db:` counts | `PG1-D3-0003` |
| **F-25q** | **NO-LEAKAGE role separation 0% built (critical).** None of §7.4's five roles exist; the single `amjis_app` credential the web app serves every request with holds full CRUD on the prediction ledger + calibration it is designed to be walled from. Repo-wide grep for the five role names: zero hits. See §7.4 correction. | critical | `db:pg_roles`, `db:role_table_grants`; `client.ts:58` | `PG1-D3-0004` |
| **F-25r** | §7 pipeline-diagram table names do not exist live — `brahma_mimamsa_prediction_ledger`, `brahma_mimamsa_answer_quality`, `brahma_phala_anchors` return zero rows in `information_schema`. Real tables: `mimamsa_predictions`, `mimamsa_qa_eval`, `phala_anchors` (no `brahma_` prefix). Target-state mislabelled as current. See §7.1 correction. | medium | `db:information_schema.tables` | `PG1-D3-0001` |
| **F-25s** | Build-side interpretive-data integrity defects — `bodha_discoveries` hypothesis rows carry an internal-varga citation mismatch (`aggregate_D108` row with `meaningfulness_basis: aggregate_d10`); `mimamsa_insight_units` verdict strings render grade→word incoherence (`denied` at a neutral grade 5.0/10, band `[0.35,0.65)`, prose "Conditional"). A build-time consistency assertion (verdict word × grade × band; varga citation) is missing before persistence. | medium | `db:bodha_discoveries`, `db:mimamsa_insight_units` | `PG1-Q1-0005`/`-0009` |
| **F-25t** | Cloud SQL PITR **disabled** on prod `amjis-postgres` (`pointInTimeRecoveryEnabled=False`); daily backups exist (7 retained, 02:00) but **no PITR** and **no restore drill ever executed** against a scratch instance — worst-case RPO ~24h on the irreplaceable ledger/conversation tables, not the near-zero §14A.3 calls for. Resolves §16.6's "nobody knows" backup row to verified-and-insufficient. | high | `gcloud sql instances describe amjis-postgres` | `PG1-O1-0001`/`-0002` |
| **F-25u** | ~~`chart_facts` live row count diverges **+402%** from the sealed L1_GANITA_CLOSURE canonical (27,554 canonical vs **138,519** at BIND probe; **276,206** in later lane probes) — outside §8.7's ±1% tolerance, and the number is unstable across probes. Either legitimate post-closure enrichment or an idempotency/duplication defect; **undiagnosed** (PG-1 read-only). A sealed closure figure and the live table disagree by ~5×.~~ **[CORRECTED PG-2 2026-07-19 — `PG2-X1-0001..0006`, RESOLVED BENIGN; alarm retracted per PC-2]** Not a defect. `chart_facts` stores one full ~27,677-row fact set **per ayanamsha** (5 partitions: raman/true_chitra/krishnamurti/lahiri_chitrapaksha/surya_siddhanta_classical) + a 135-row ayanamsha-invariant partition, so one fully-built chart = **138,519 rows** (the correct all-ayanamsha total), the two built charts sum to **276,206** (138,519 Abhisek + 137,687 Abhinandan, exact), and the sealed **27,554 is the stale v1.0 single-ayanamsha/pre-enrichment figure**. The "divergence" is a **scope-labeling mismatch** (per-ayanamsha vs all-ayanamsha), not conflation/accretion/duplication: fact_ids are 100% unique (`count(*) = count(DISTINCT fact_id) = 138,519`), no natural key spans two build_ids (multiple build_ids are benign scope-limited-rebuild provenance under §N.3), and the count is byte-identical across three spaced probes with the table two days stale. The **"unstable across probes"** framing was itself a category error — an *unfiltered all-charts* count (276,206) compared against a *chart-scoped* count (138,519), not one query drifting. All six hypotheses resolved (H1 per-ayanamsha CONFIRMED; H2 legitimate ga_structural combinatorial growth CONFIRMED; H3 accretion, H4 conflation, H5 active-write, H6 non-determinism all REFUTED). The live cockpit `count_sql` does not filter by ayanamsha_id, so the canonical figure should be restated as the all-ayanamsha 138,519. Prior partial diagnosis existed and PG-1 did not cite it: `ABHINANDAN_POST_REGEN_DATA_AUDIT_v1_0.md` (2026-06-28) flagged the multi-build_id state as worth investigating — reconciled by X-1's decisive `0 natural keys span >1 build_id` test as benign, not an accumulation bug. | ~~high~~ **resolved-benign** | BIND B-5; `db:chart_facts` (`PG1-D1-0003`, `PG1-D3-0002`); PG-2 `PG2-X1-0001..0006` | BIND B-5; PG-2 X-1 |
| **F-25v** | The Bearer-key MCP auth face returns **401** (`POST /mcp`, `Authorization: Bearer $MARSYS_MCP_KEY` → "Invalid or missing Bearer API key") while the `?api_key=` seat is live. Stale/rotated prod key or an auth regression — unverifiable root cause, confirmed symptom; blocked the R-2 Bearer-face sweep and the verifier's `mcp:` evidence replay. | medium | BIND B-3 | BIND B-3 |

**Corroboration (not a new F-number):** `PG1-C2-0007` confirms the writer path is
saturated with `as any` (six sites) and reasoning has no open/close lifecycle —
this corroborates existing **F-02/F-03** and is the direct cause the §19.7 gate row
"no `as any` in the writer path" cannot be met by a shim (see §19.7 correction).

### §16.8 PG-2 diagnostic-wave corrections + resolutions (2026-07-19)

Append-only, per §21 rule 3. The PG-2 diagnostic wave (six lanes, 44 findings, all
ACCEPT) closed the high-consequence items PG-1 left undiagnosed. The two headline
resolutions (F-25u chart_facts → **resolved benign**; T-9 chat engine → **NO, code-confirmed
broken**) are corrected in place at §16.7 (F-25u row) and §18 (T-9 block) respectively.
This section records the remaining PG-2 corrections that do not belong to a single existing
row. Full detail: `PG2_DIAGNOSTIC_REPORT_v1_0.md`; current-state description
`RETRIEVAL_SYSTEM_TRUTH_v2_0.md` (supersedes v1.0).

- **The serving path was invoked live for the first time — it 500s (`PG2-X2-0001`, critical).**
  The deployed `/api/chat/consult` engine fails deterministically with HTTP 500 at
  `bundle_hydrator.ts:25` because `FLOOR_ASSET_IDS = ['FORENSIC','CGM']` hard-codes the
  retired `FORENSIC` asset (deleted from `CAPABILITY_MANIFEST.json` in PR #187), so
  `hydrateBundle` throws before any stream opens. Same failure CLASS as LCA-2, one stage
  downstream; a NEW regression. **One-line fix** (drop `'FORENSIC'`). This is a hard
  prerequisite before the P0'/§19.7 render-bet work (D-17/OT-12) can be observed
  end-to-end, and is separate from and far cheaper than the ~6–9wk C-2 shim scope.

- **A-14 memoization ruling — MISLABEL FIXED + INVERTED (`PG2-X4-0006`).** PG-1's
  `PG1-Z1-A0001` left this "unaudited" and mislabelled it **A-13** (A-13 is the unrelated
  three-region layout row; the memoization ruling is **A-14**, §12.7, §1.1 assumption
  table). X-4 audited it: today's code is the **opposite** of A-14's target — the
  virtualizer A-14 says to remove (`VirtualizedMessageList.tsx`) IS live (imported by
  `AdaptiveMessageList.tsx`), while **both** replacement techniques A-14 mandates are absent
  (`content-visibility` = 0 hits in `platform/src`; frozen-block memoization = 0 hits in the
  message-list components). A real target-vs-actual gap for the A-11/A-12/A-14 render work,
  not merely an unaudited assumption. (Same mislabel class as PG-1's own A-26/A-08 slip.)
  The §1.1 assumption-table A-14 row is corrected in place.

- **Citation shape clarified (`PG2-X4-0003`).** PG-1's S1-0003 "no citations found" was a
  **DB-emptiness artifact**, not evidence of absence. Citations DO have a definite shape:
  a `CitationPart` (`{type:'citation', index, signal_id: /^SIG\.MSR\.\d{3}$/, layer, snippet}`,
  `citation_data_part.ts`) emitted as an AI-SDK data-part **inside the message's `parts_json`
  array** — not `message_parts` child rows (which do not exist). PG-1 found 0 because
  `conversation_messages` = 0 rows, not because the shape is missing. §19 P5' should query
  `parts_json` for `{"type":"citation"}` against a **production-traffic** DB instance, not
  the diagnostic one.

- **`chart_agnostic_gate` (A-2) CONFIRMED fail-closed (`PG2-X4-0002`).** A `per_chart`
  capability with no `chart_id` returns `400 {error_class:'validation', message:'CHART_REQUIRED'}`
  before any handler, with **no** default-UUID substitution — resolved from `args['chart_id']`
  or the `X-MCP-Chart-Id` header, defaulting to `null` (never `NATIVE_CHART_ID`). Backed by a
  second handler-level re-check and a FROZEN CI gate (`chart_agnostic_gate.ts`) that statically
  forbids a `default` on the `chart_id` schema. No leak. (Residual: a true raw-HTTP-from-outside
  probe still needs a running server; this is a decisive code-read verdict, not yet a live
  observation.)

- **Two-vs-three prediction ledgers (`PG2-X5-0006`).** F-25p/§7/OT-11 framed the landscape as
  two disjoint ledgers; the live landscape is **three** (`mimamsa_predictions` 384 /
  `mcp_predictions` 0 / `brahma_prospective_ledger` 5) plus the `phala_anchors` anchor set that
  `record_outcome` actually resolves against. This materially widens OT-11 (the canonical-ledger
  ruling is not binary) — see the OT-11 row correction in §18 for the full costed fork (PC-8, no
  choice made). Also: PG-1's "`phala_anchors` references `mimamsa_predictions`" is inexact
  (`PG2-X5-0003`) — `phala_anchors` FKs run **up** to L3 kāla, not down to `mimamsa_predictions`.

- **F-25v (Bearer 401) RESOLVED, not broken auth (`PG2-X3-0001`).** X-3 got HTTP 200 + full
  139-tool `tools/list` with the correct Bearer key; a garbage key reproduced PG-1's 401
  byte-for-byte. Root cause: a **stale/wrong key value** at PG-1 audit time, not an auth
  regression. F-25v is downgraded from an open symptom to a resolved key-hygiene note.

- **Coverage now 133/139 (~96%) (`PG2-X3-0010`).** PG-1 R-2's 35 tools + PG-2 X-3's 98 close
  the G.4 coverage gap. Two tools remain genuinely unexercised (`prashna_undertaking_get`,
  `mimamsa_outcome_record`). New defects surfaced: catalog-family `unknown_tool` drill
  degradation (`PG2-X3-0004`), `record_outcome` 500 on bad id (`PG2-X3-0005`),
  `holistic_bundle_chart_facts` reports "completed" while 5/8 sub-tools error (`PG2-X3-0006`),
  and several whole-chart tools (92–289KB) exceeding the client token ceiling (`PG2-X3-0009`).

- **PG-1's gate re-audited VALID (`PG2-M1-0001..0012`).** An adversarial fresh-context M-1
  re-audit (independently re-confirmed by this wave's verifier) upheld **GATE GREEN**: the G.1
  addendum is genuine (forward-causality proven), all integrity assertions hold, 10/10
  spot-verified findings hold. Six correction-worthy hygiene defects were found, **none
  gate-voiding** — most notably the sealed report's stale **87** finding count (actually **98**)
  and **5** critical count (actually **6**), corrected in place in the sealed artifacts.

### §16.9 The as-built census — 2026-08-18 (v0.11 re-baseline, RG-1 discharge)

Append-only, per §21 rule 3. Sources: git HEAD `dfbdfe620` (full read of
`components/pariprashna/**`, `lib/pariprashna/**`, `app/api/pariprashna/**`,
the samiksha trees, `feature_flags.ts`); the PB close corpus (`REPORT_PB-1/2/3`,
`PB_CAMPAIGN_CLOSE_v1_0`, `PURNATA_CLOSE_REPORT_v1_0` §9, `SAMAPTI_CLOSE_REPORT_v1_0`);
a live `mcp_server_info` census. This section replaces the 2026-07-27 banner
as the current-state instrument; per the banner's own meta-finding, treat it
as dated the day after it is written and ground against HEAD before executing.

#### §16.9.1 Doors and deployment

| Fact | State 2026-08-18 |
|---|---|
| `/clients/[id]/pariprashna` + `/clients/[id]/samiksha` | LIVE in production, gated by `PARIPRASHNA_ENABLED` (default `false` in code, **ON via Cloud Run env** since `amjis-web-01218-4ng`, PB-1). Flag-off → redirect to consult. |
| `/api/pariprashna` (POST) | LIVE. A FORK of consult (never an edit; consult byte-identical, must_not_touch). Stream-first: `turn.open` + `phase{plan,start}` are the first bytes; all faults in-stream. 1,179 lines. `maxDuration=120`. |
| `/api/pariprashna/resume` (GET) | LIVE. Replay / snapshot / interrupted-finalize; source-grep-enforced isolation from writers. |
| `/api/pariprashna/samiksha/confirm` | LIVE. Auth + chart-authz gated; NOT flag-gated (the one always-reachable family endpoint). |
| `/clients/[id]/consult` + `/api/chat/consult` | STILL LIVE, un-gated — the production default surface until PB-4. Byte-identical through every PB wave (one disclosed neutered no-op: `recordCalibrationStamp`). |
| MCP | 125 tools served on the `full` profile (`catalog-1+t152+r653c2a1a98c8`); `full`/`compact`/`consult` generated profiles; `prashna_ask`+`prashna_status` live, job-handle semantics, rejected on `consult`. |
| **PB-4 PŪRṆATĀ (cutover)** | **NEVER RUN.** No default flip, no consult retirement, no flag deletion, no seven-smoke hold. Gate condition (a) — loop proven live — is MET since C4; standing ruling R-0/PB-4 decides at the gate. AC-15 (the native's week-of-use) is unreached until then. |
| **C4-LOOP-LIVE-PROOF (2026-08-01)** | **COMPLETE, all six criteria live** against production, no fixture substitution; a real uncoordinated user interacted with the live review tab mid-proof. T-9 resolved forward. |

#### §16.9.2 §19.7 gate rows, re-assessed against the SHIPPED surface

| §19.7 assertion | As-built verdict |
|---|---|
| Settled content never moves | Architecture holds structurally (`FrozenBlock` always-equal memo; single volatile element; `overflow-anchor` off; owned rAF scroller). CI layout-shift assertions run in the PB-1 harness. |
| Caret never orphans | Caret is an inline DOM sibling of streaming text inside `VolatileTail`, moved by text insertion; hollow variant on reconnect. |
| No transmutation | Live chips render at final geometry — trivially, because nothing rewrites mid-stream (A-38 gap): the property currently holds by absence, not by the designed mechanism. |
| Work visible immediately | MET — stream-first ordering shipped (the exact thing PG-1 proved a shim could not do). |
| Reasoning has a lifecycle | MET differently — `role: thinking` blocks, zero `as any` in the emitter (typed builders). |
| Survives bad networks | Ring buffer + `Last-Event-ID` replay + snapshot + visibility-stall reconnect; poll-based tail disclosed. |
| Works on a phone | PARTIAL — bottom-sheet citations + 900px dock breakpoint shipped; the full §12.11 checklist (visualViewport composer, G-MOBILE battery) is PB-4 Lane F-4. |
| Works with a screen reader | PARTIAL — one polite live region (the tail), sr-only settle announcement; full §12.12 discipline is PB-4 Lane F-4. |
| **Feels like Claude Code** | **UNTESTED — this is AC-15, unreachable until PB-4 makes the surface the default. Never claimed (ruling W-4).** |

#### §16.9.3 The fidelity debt register — where the build is thinner than the design

Each row is disclosed lossiness or unwired capability, NOT a ruled design
change (ruled deltas — the dock, the seams — are recorded in §1.1 tags). This
register is the raw material of §19.5 waves 2–3.

| # | Debt | Evidence | Owner |
|---|---|---|---|
| FD-1 | **Live wire renders paragraphs only.** `s1LiveAdapter` hardcodes `kind:'paragraph'`; TableBlock/VerseBlock/GapRibbonBlock/headings/roles/inline prediction_card have NO live producer — fixture-only. | `s1LiveAdapter.ts` (documented "honest lossiness") | A-37 |
| FD-2 | **S-3 citation rewriter built, unwired.** The route's only import from `lib/pariprashna/citations/` is the leak lint; `citation.define` arrives post-hoc from the write-through. | route imports; `rewriter.ts` | A-38 |
| FD-3 | **Composer Model + Length pickers are cosmetic**; `length_tier` accepted-echoed-persisted-nonfunctional (`TODO(PB-4)`); 3 of 4 Depth choices → `deep_dive` (16 iterations). | `Composer.tsx submit()`; route `TODO(PB-4)` | A-39/A-40 |
| FD-4 | **`LogToSamiksha` (in-stream confirm) built, mounted nowhere** — blocked on a structured prediction wire event. | grep: zero importers; `capture.ts` prerequisite note | A-37/A-42 |
| FD-5 | **pgvector recall built, zero callers.** | `lib/pariprashna/recall/` | A-41 |
| FD-6 | **Grounding summary is client-synthesized** from the citation tally (honest labels, WELL-GROUNDED only if ≥1 confirmed AND zero weak; snapshot resume degrades all to catalog). Server-derived summary + completeness line unbuilt. | `s1LiveAdapter`, `groundingRollup.ts` | A-38 |
| FD-7 | **Delta-boundary lint escape** — a leak split across an SSE chunk reaches the screen until block-commit scrubs it (the §13.5 contradiction, now observed). | route lint call sites | accepted residual + A-38 (clean evidence shrinks exposure) |
| FD-8 | **Canonical store covers assistant turns only**; user/history on the legacy writer; tool_call/tool_result/reasoning parts unwritten; summaries therefore assistant-only. | `route_writer_adapter.ts` | P1' completion, §19.5 wave 4 |
| FD-9 | **Byte-equality capture flag must stay OFF** (Ruling 80) until the Ruling-54 standing-posture follow-on closes; until then the golden gate has no standing real-stream corpus. | `PB_MEMO_INDEX` row 4; PR #927 | follow-on lane |
| FD-10 | **Digest transport is a log-only stub; digest journal is file-based** (ephemeral on fresh runners). | `daily_job.ts`, `digest.ts` | §19.5 wave 3 |
| FD-11 | **Two error classifiers** — the adapter's live bands + the dead `classify-error.ts`. Fold or delete. | F-25b + `s1LiveAdapter` | PB-4 sweep |
| FD-12 | **`reading_depth` client mapping is crude** — composer mode, not scope tuple, decides depth. | `PariprashnaApp.tsx` | A-40 |

#### §16.9.4 Defect dispositions at HEAD (F-register)

| Defect | Disposition 2026-08-18 |
|---|---|
| F-01 (pipeline-before-stream) | **FIXED on the new surface** (stream-first fork); stands on consult until PB-4 retires it. |
| F-02/F-03 (`as any` writer path) | **SUPERSEDED on the new surface** — typed emitter, zero casts; consult path unchanged. |
| F-04–F-11 (render defects) | **SUPERSEDED by the PB-1 renderer** on the new surface; alive on consult until retirement. |
| F-25b (dead error classifier) | **STANDS** — still zero importers (verified at HEAD). See FD-11. |
| F-25c (feedback endpoint discards) | **STANDS** — verified at HEAD, stub verbatim. See A-48. |
| F-25d (no rate limit / spend cap / middleware) | **STANDS** — verified at HEAD, now on BOTH chat trees. Bound to the PB-4 gate via A-46. |
| F-25e (`parts_json` no version stamp) | **SUPERSEDED FORWARD** — `message_parts` child rows + `schema_version` shipped (migration 467); legacy blob remains only on the history path (FD-8). |
| F-25f (snapshot-only resume) | **SUPERSEDED on the new surface** — replay-from-seq + snapshot + interrupted-finalize shipped. |
| F-25g (`audience_tier` load-bearing) | **DOWNGRADED to cleanup** — prompt keying + route stamp excised (verified at HEAD); type/schema residue only. |
| F-25q (NO-LEAKAGE arm-1 0%) | **STANDS — critical.** Unchanged. §19.5 wave 5. |
| F-25t (PITR disabled, no restore drill) | **STANDS at last verification** (2026-07-19); not re-verified since. A-46 requires re-verification before cutover. |
| T-9 (no served reading has ever existed) | **RESOLVED FORWARD** — see §18 T-9 correction. |

#### §16.9.5 The engine beneath the surface — content deltas since 2026-08-01

The conversation layer's serving code is unchanged since the arc closed; the
readings it serves are not, because the engine advanced under it. Recorded
here because §J-grade prose is a function of BOTH: **PRATIJÑĀ v4 → F1
ADOPTION** (2026-08-09): the v4.1 promise engine live in production; the
marriage verdict now *conditional / 0.450 MODERATE* — the first production
verdict set by a measured, ruled, classically-cited amendment.
**GOCHARA-UTKARṢA + PARIṢKĀRA** (2026-08-10/12): transit engine v1→v3
(bounded λ, 10 fitted + 2 structural mechanisms, century materialization),
re-closed for real under MR-29 after the campaign's own false self-close —
calibration stamps honestly `structural_prior`, prospective ledger genuinely
auto-seeding. **ṢAḌ-DARŚANA** (2026-08-07, PARKED-FINAL): KP sub-lord clock
live. **ADHIṢṬHĀNA** (2026-08-08): one graha map, one domain vocabulary, the
fact-identity index at 100% on all canonical charts. **SAMPŪRTI W0**
(2026-08-10): KNOWN_DOMAINS 7→13, `kala_dasha_sandhi_get` registered, LEL
resolver backfilled. A-45 states the serving rule these create.

---

## §17 — Verification strategy

The question is how to **prove** these are fixed, not believe it.

### §17.1 The streaming replay harness (keystone)

Record real provider event streams into fixtures. **Rendering** fixtures:

- `gemini-big-chunks` · `anthropic-with-thinking` · `mid-stream-tool-call`
- `unterminated-fence` · `giant-table` · `citation-dense`
- `nested-loose-list` (the §12.4 segmentation trap)
- `authorial-restructure` (paragraph that becomes a list lead-in)

**Transport-failure fixtures (new v0.5 — v0.1–v0.4 tested rendering only):**

- `disconnect-mid-block` → reconnect → replay-from-seq
- `duplicate-seq` (reducer must discard idempotently)
- `server-restart-mid-turn`
- `ring-buffer-overflow` → snapshot fallback + disclosure flag
- `tab-suspend-resume` (mobile Safari SSE suspension)
- `half-committed-turn` (stream dies after N frozen blocks)

**Sentinel fixtures (new v0.5):**

- `sentinel-split-across-deltas` · `unclosed-sentinel` (must flush at 64B/400ms,
  never stall) · `malformed-variants` · `hallucinated-id`

A replay server feeds all of these at recorded **and adversarial** cadences:
1-byte trickle, 50KB slabs, 3-second stalls. Every render test runs against
replays — deterministic and provider-free in CI.

**Every fixture runs at both desktop and mobile viewport** (§12.11), and
**every visual checkpoint carries an axe-core pass** (§12.12).

### §17.2 Layout-thrash detection

The falsifiable form of "nothing above the caret moves":

1. `PerformanceObserver` layout-shift entries — **assert CLS contribution
   ≈ 0 for any element above the volatile tail. Settled-region shift budget:
   0.00.**
2. Per-block `getBoundingClientRect` snapshots each frame during replay —
   committed blocks' rects must be frame-over-frame identical.
3. The caret rect must always lie within the tail block's rect.
4. At `turn.close`, total document height delta ≤ caret removal only.

### §17.3 Frame budget

- Zero long tasks > 50 ms mid-stream at 4× replay speed.
- React commit count ≤ frames elapsed (proves rAF coalescing).
- Dropped-frame rate < 1% on a throttled-CPU profile.

### §17.4 Latency budgets as assertions

| Budget | Target |
|---|---|
| POST → `turn.open` | < 300 ms |
| POST → first `activity.upsert` | < 1 s |
| `turn.close` → interactive (no bookkeeping tail) | < 100 ms |

### §17.5 Register-leak lint — three deployments of one scanner

1. **Unit corpus** — harvest real historical leaky outputs; the scanner must
   catch 100% of seeded internal ids.
2. **Live gate telemetry** — every rewrite or redaction increments a counter;
   leak rate is a tracked health trend.
3. **Periodic eval** — N generated answers per tier across query classes,
   scanner plus an LLM judge scoring "would a layperson understand every
   term?", thresholded in CI.

### §17.6 Protocol conformance

- Zod-validate every event server-side at emit and client-side at ingest —
  fail loudly in dev, count in prod.
- **Golden test:** replay → client reducer → final client state must
  byte-equal the persisted `message_parts` for the same turn. This kills the
  live-vs-persisted dual-source class permanently.

### §17.7 Visual regression

Playwright screenshots at fixed replay checkpoints (25/50/75/100%) per
fixture, per tier, diffed. Catches transmutation-class bugs that rect checks
can miss.

### §17.8 Production observability of the protocol (new v0.5)

§17.1–§17.7 is CI verification. **Production observability of the new stream
was absent** — and verified absent today: per-request trace rows exist
(`lib/trace/writer.ts:27,55,171–174`) but grep for
`ttft|first_token|histogram` across `src` returns **zero matches**. You cannot
answer "what is p95 TTFT this week" without writing new SQL.

Required, as aggregate metrics not per-request rows:

| Metric | Why |
|---|---|
| **TTFT** — POST → first `block.delta` | The number that governs perceived quality (§17.4 measures `turn.open`, which is necessary and insufficient) |
| Per-event-type latency histograms | Where the pipeline actually spends time |
| Delta → commit lag | Detects segmentation or lint stalls |
| Reconnect rate, replay-from-snapshot rate | Transport health |
| Gate verdict rates (grounding, register lint) | **Register-lint firing rate is the health signal that §13.5's primary layers are working** |
| Sentinel normalization + hallucination rate per model | Feeds ModelPlane tier review (§12.9.1) |
| Cost per turn, per user, per channel | §14A.2 attribution |
| Prediction capture and resolution coverage | §14.7 — coverage is an honesty metric |

### §17.9 Registry and doctrine CI

- `tools served == descriptors registered` assertion.
- `density_contract` census across the whole surface (byte caps, facet and
  empty-reason coverage).
- Missing `register` labels fail the build.
- NO-LEAKAGE canary (§14.6 arm 4).

---

## §18 — Tensions and pushback register

Open tensions that must not be resolved silently.

### T-1 — "Like Claude Code and Gemini" vs §N.6

**The tension.** Claude Code and Gemini are general assistants whose tool
activity is incidental plumbing; hiding it costs nothing. This instrument's
*entire differentiation* — B.3's ledger mandate, §N.6's density layering, the
Ethical Framework's calibrated-and-auditable posture — is that epistemic
structure is inspectable. A Paripraśna that renders like Gemini with
everything collapsed would be a beautifully smooth **generic astrology
product**, which §L line 1 prohibits.

**The resolution.** Adopt their *choreography* — stable geometry, append-only
rendering, one volatile region, collapsed density — while rejecting their
*epistemic opacity*. Grounding surfaces (chips, grade marks, the
"could not be verified" flag, region ③) are **product surface, always on at
every tier**, rendered with the same stability discipline as the prose. What
gets collapsed is only the *procedural* machinery — which tool, how many
milliseconds.

**The formulation to hold onto:** *hide how the instrument worked; never hide
why the claim stands.*

And the diagnostic observation behind it: the native's pain was never "I saw
machinery" — it was "machinery was presented incontinently." Fix the
incontinence; keep the epistemics.

### T-2 — D-05 creates a two-class channel unless `prashna_ask` ships

Dropping cross-channel history is safe **only if** the MCP channel gets the
engine via `prashna_ask` (A-07). Raw-tools-only MCP with neither history nor
brain would be a strictly worse product wearing the same brand — and the
native is himself the heaviest MCP user. **If A-07 were rejected, D-05 should
be revisited.** Tracked as OT-6.

**Sharpened by §6.4.1 (2026-07-19).** The two-class risk is not primarily about
missing conversation history. It is that raw-tools MCP receives **neither the
acharya floor (B.11), nor the grounding gate, nor the register guarantee
(D-14)** — the last being *structurally* undeliverable there, since no prose
crosses our boundary to lint. So `prashna_ask` is not a convenience wrapper:
**it is the only mechanism by which the MCP channel receives the instrument
rather than the database.** This raises A-07 from a good idea to a
load-bearing one, and makes OT-10 (which path a query actually takes) the
gating question for whether the guarantee is reliably delivered at all.

Related: the prediction ledger is chart-scoped and channel-agnostic by
necessity, so one class of durable memory *is* cross-channel regardless. The
architecture must state precisely that what D-05 dropped is **conversational
transcript portability only**, or §14 will get incorrectly "simplified"
against D-05.

### T-3 — "Effort is no constraint" hides ongoing operational cost

A live model-health plane, probe scheduler and dynamic OpenRouter catalog are
*ongoing operational* surface, not one-time build. For a single-operator
system, every always-on subsystem is future 2 a.m. debugging. D-12 removes
build-cost as a constraint; it does not remove *operating* cost. Keep the
model plane to one probe job and one table, and resist gold-plating it. It
serves the instrument; it is not the instrument.

### T-4 — "Evolve" is true at the architecture level and false at the component level

Tally of verdicts in this document: message store new, citation gate replaced,
streaming validator deleted, history compression replaced, aliases deleted,
envelope mirror deleted, all three planners demoted to stages, the transport
replaced, the consult route decomposed.

What genuinely evolves: registry descriptors and the D1 topology (excellent —
keep), envelope + response budget (keep, share), the model registry (evolve
hard), persistence tables (extend), the trace and event vocabulary (keep), the
FROZEN orchestrator (untouched).

Both statements are true. D-07 pre-agrees the framing precisely so that a
reader holding "evolve" as a component-level promise does not experience §12
and §13 as a betrayal. It is not — the native's own caveat ("fully aligned or
enhanced or deprecated") licensed it.

### T-5 — Honest gaps must interrupt smoothness, deliberately

A §N.6-honest turn sometimes ends with an empty verdict layer and an explicit
gap. The Claude-Code aesthetic would tuck that into a collapsed row. It must
instead be a first-class element in the answer region — calm, but unmissable.
**Smoothness is in service of trust; when the honest thing is friction,
friction wins.** Written here so that a future polish pass does not "fix" it.

### T-7 — This document's current-state claims decay, and decayed once already

**v0.1–v0.4 asserted that the envelope mirror was hand-maintained and the
codegen lane never landed. Both were false when written** — the mirror was
already deleted and generated, with `codegen:check` in `package.json` (§8.5).
The adversarial review's judgment is recorded here because it is the right
standard: *"A target-state document whose forensic appendix is stale on its own
first work item cannot be trusted on the claims I did not check."*

This is the repo's own GA.1 failure mode — registries disagreeing — applied to
an architecture document. Four other counts were also wrong (aliases 45 → **55**,
tools ~118 → **120 declared / 126 actual**, planners "three" → **3 live + 2 dead
islands**, `useScrollDiscipline` "flag-gated" → **live and unflagged**).

**Mitigation, now binding (§0.6):** every version bump re-verifies §16 and every
current-state claim against the working tree; corrections are made in place with
the error visible; and the document states its verification date prominently.
An architecture document that misdescribes its origin point misdirects every
session that executes from it.

### T-8 — Cheap honesty mechanisms can become dishonest at low n

§14.6's finding generalizes. Serving "Brier 0.18, n=7" is *more* misleading
than serving nothing, because a number carries an implicit claim about its own
reliability. The same trap is latent elsewhere: an epistemic grade derived from
a handful of verification passes, a coverage stamp whose denominator is
uncertain, a confidence interval on three observations.

**The rule this implies, and §N.6 should probably absorb it: a quantity is
served only when the sample supports the precision implied by its
presentation.** Below that, the honest output is the flag, not the hedged
number. B.10 forbids fabricating a computation; T-8 extends it — **do not
fabricate a precision either.**

### T-6 — Region ① must persist, unlike a terminal spinner

Claude Code's transcript is ephemeral scrollback. Paripraśna's transcript is
an **audit artifact** feeding the prediction ledger and the Mīmāṃsā outcome
loop. So the working region must persist in history (collapsed) rather than
evaporate — every past turn stays re-openable to its full plan/tool/gate
record at audit tier. The record-keeping obligations here are stricter than
either comparator's.

### T-9 — The instrument has never produced a served reading; §J is unproven *(new PG-1)*

*(raised by the PG-1 grounding audit — `PG1-Q1-0001`/`-0012`, critical.)* The entire
conversation store is empty (`conversation_messages = 0`, `llm_call_log = 0`, every
conversation-adjacent table 0 rows) while the same DB holds 276,206 `chart_facts`.
**No user-facing reading has ever left this instrument and been persisted.** Two
consequences the design must hold honestly: **(1)** the §J acharya-grade claim is, as
of this audit, *entirely unvalidated by any live output* — it is aspirational until
the serve-time synthesis path runs end-to-end and real readings are put in front of
the bar; and **(2)** every current-state audit of the *serving* path in this wave
(prediction detector firing, calibration write-through, envelope behaviour under real
traffic) is an audit of an **unexercised** path, so "wired but 0 rows" cannot be read
as "works" — it may equally be "never traffic'd" or "silently failing in a swallowing
try/catch." The deeper tension Q-1 surfaced: the persisted interpretive proxies (L5
verdicts, discoveries, remedies) **describe the instrument's own machinery — z-scores,
salience, embedding distance, internal signal keys — in place of reading the chart.**
The pipeline computes structure impeccably and stops one layer short of the reading.
This is a *synthesis-layer* gap, not the (by-design) STRUCTURAL-mode calibration gap —
and it is not resolved by any decision currently in §1. It must not be silently closed
(§21 rule 4). Gate §J claims on a live eval of served prose, never on the structural
scaffold.

> **[CORRECTED PG-2 2026-07-19 — `PG2-X2-0001`, T-9 resolved to a definitive answer.]**
> PG-1 could only observe `conversation_messages = 0` and correctly refused to read
> "wired but 0 rows" as "works." PG-2's Lane X-2 performed the actual authenticated
> live invocation PG-1 could not, and the answer is now specific, not a mystery:
> **the chat engine does NOT work.** The deployed `/api/chat/consult` engine
> authenticates and plans a query correctly but **fails deterministically with HTTP
> 500 at the bundle-hydration stage, before any synthesis, streaming, or reading is
> produced**, because `platform/src/lib/bundle/bundle_hydrator.ts:25` hard-codes the
> retired `FORENSIC` asset as a mandatory floor asset
> (`FLOOR_ASSET_IDS = ['FORENSIC','CGM']`) that no longer exists in
> `CAPABILITY_MANIFEST.json` (deleted in PR #187 Legacy Teardown), so `hydrateBundle`
> throws `bundle_hydrator: floor asset 'FORENSIC' not found in manifest` and the
> outer catch returns a 500. Confirmed identical across two Firebase-authenticated
> invocations 3.5 min apart (steady-state, not cold-start), with byte-identical
> Cloud Run server logs. This is the **same retired-legacy-relic failure CLASS as
> LCA-2** (the retired `reports` table, `route.ts:306-316`), one pipeline stage
> further downstream — a NEW, distinct regression, not a recurrence. It also
> explains WHY the `mcp_predictions` detector (`PG1-D3-0002`) never fires: it is
> wired correctly but **structurally unreachable** — every request dies at
> `hydrateBundle`, upstream of `onFinish`. So T-9's "no served reading has ever
> existed" is confirmed and its cause is now known and cheap to unblock (a one-line
> fix: drop `'FORENSIC'` from `FLOOR_ASSET_IDS`), but §J remains **unproven** — even
> after the fix, whether the engine then produces a clean end-to-end reading or hits
> a THIRD retired relic downstream cannot be known read-only, and `conversation_messages`
> is still 0 all-time. The synthesis-layer §J gap above stands unchanged; this
> correction only converts the *reachability* half of T-9 from "unknown" to
> "code-confirmed broken at a named line." (Two orphaned `conversations` rows were
> created by the probe and kept as the first serving-path evidence:
> `14d96091-…`, `3829624c-…`.)

> **[GROUNDED 2026-08-18 — v0.11: T-9 RESOLVED FORWARD.] Served readings now
> exist.** The `FORENSIC` relic was fixed, PB-1 shipped and flipped the new
> surface, and real production readings flowed through every PB verification
> wave, culminating in C4's fully live loop proof (2026-08-01) and PŪRṆATĀ's
> Q-graded readings. The *reachability* half of T-9 is closed. The
> *synthesis-quality* half — is the served prose actually §J acharya-grade,
> sustained, in the native's hand? — remains governed by AC-15, which cannot
> run until PB-4 makes the surface the default (ruling W-4: handed to the
> native, never claimed). The deeper Q-1 tension (machinery-describing
> interpretive proxies) was worked by the ŚUDDHA-VĀCA→PŪRṆATĀ narration arc;
> its named remainders and the post-six-views narration audit are the #2
> handoff item (`PURNATA_CLOSE_REPORT` §5). T-9 is not silently closed; it is
> superseded by a narrower, better question with a designated gate.

### T-10 — As-built divergence must be classified, or it compounds *(new v0.11)*

The build produced three distinct kinds of difference from this document, and
they must never be filed together: **ruled deltas** (the dock, the pass seams
— a native or DVA decision, recorded, binding), **disclosed lossiness**
(paragraph-only wire, client-synthesized grounding — named in code comments
and reports, honest, but nobody RULED them), and **silent debt** (the two
error classifiers). The trap: disclosed lossiness ages into de-facto
architecture if no register owns it — six months from now "the live wire is
paragraphs" reads as a decision nobody made. §16.9.3 is that register. The
rule: every future divergence lands in one of the three bins at merge time,
and only the first bin closes without further work.

### T-11 — The cutover inverts the risk polarity of every open gap *(new v0.11)*

Every §14A absence was tolerable while Paripraśna was a flagged parallel
surface with one primary user: a runaway spend, a missed backup, an
unthrottled client hits an experiment. PB-4 flips the polarity — the same
gaps on the DEFAULT surface hit the product. This is why A-46 binds rate
limits, spend ceilings, and a verified restore posture to the PB-4 entry
condition rather than to a someday-hardening wave, and why the seven-smoke
hold (W-1) is necessary but not sufficient: smokes prove the happy path;
caps bound the unhappy one. The general form: **a gate that promotes a
surface must re-price every risk that was priced under the old exposure.**

---

## §19 — Sequencing (RESTRUCTURED v0.5 — shim-first)

> **v0.1–v0.4's P0–P7 was dependency-clean and execution-wrong.** It is
> superseded. The original is preserved at §19.3 with the critique, because
> the reasoning matters.

> **[GROUNDED 2026-08-18 — v0.11]** The shim-first bet below was vindicated by
> events, in substance if not in mechanism: the PB campaign executed the
> spirit of P0'–P1' and most of P4' — the render bet was proven FIRST on a
> production fork (not a shim; OT-12 resolved, §1.2), capture started early
> and the loop is live (C4), the canonical store and summaries shipped, and
> the collect-only discipline held. P2' (engine extraction + planner
> unification) and P3's loop-extracted `prashna_ask` did NOT happen as
> designed — the shipped `prashna_ask` is a single-pass job, and the unified
> plan type remains unwritten. **§19.5 is the forward sequence from the
> as-built position; P0'–P5' below are retained as the reasoning of record.**

### §19.1 Why the original order would have failed

Three faults, in severity order:

1. **The core bet was validated last.** A-11/A-12/A-13 — custom protocol,
   client reducer, three-region renderer — is the largest and most falsifiable
   bet in the architecture, and P4 scheduled it *after* the store, registry,
   planner and engine work. If the render architecture had not survived
   contact with reality, everything upstream would have been shaped around a
   falsified assumption.
2. **Months of invisible work in front of the actual pain.** Four phases of
   substrate sat between day one and any visible improvement, while the
   native's daily experience — the render defects of §16.1 — waited in P4.
   **That is precisely the condition under which a rebuild stalls and gets
   torn down a second time**, which is the one outcome this workstream exists
   to avoid.
3. **P0's anchor item was already done.** The envelope mirror was deleted and
   codegen'd before this document was written (§8.5). The monorepo — P0's
   headline — lost its stated justification entirely.

And one contradiction: P6 (calibration) was labelled *"LAST in dependency
order; FIRST in mission importance"* — but the **ledger schema and capture
affordance have almost no dependencies**. A candidate row needs a message id,
which today's store already supplies. **Every month without capture is
calibration data lost forever, on windows that take years to resolve.**

### §19.2 The revised sequence

```
 ┌──────────────────────────────────────────────────────────────────┐
 │ P0'  THE RENDER SPIKE — prove or kill the core bet (3–4 weeks)   │
 │                                                                  │
 │  A new flagged route /clients/[id]/pariprashna serving the       │
 │  typed SSE protocol via a TRANSLATION SHIM over the EXISTING     │
 │  engine — re-emitting run_adapter_dispatch's events as           │
 │  turn.open / phase / activity.upsert / block.* / citation.define │
 │  — rendered by the new three-region client.                      │
 │                                                                  │
 │  NO monorepo. NO message-store change (persist via existing      │
 │  path). NO planner work. Old route untouched.                    │
 │                                                                  │
 │  Exercises every risky element: client-side segmentation,        │
 │  sentinel hold-back, frozen blocks, scroll + caret, region       │
 │  layout, reconnection, failure UX, mobile, a11y.                 │
 │                                                                  │
 │  + replay harness — built AGAINST the shim, because it is the    │
 │    executable spec                                               │
 │  + prediction ledger schema + in-stream "log this"               │
 │    → CAPTURE STARTS NOW, collect-only (§14.6 C1)                 │
 │  + wire codegen:check into CI (one line; drift is currently      │
 │    undetected — §8.5)                                            │
 │  + verify and document Cloud SQL backup config (§14A.3)          │
 │                                                                  │
 │  GATE: does it feel like Claude Code? If yes → commit the        │
 │  substrate. If no → you learned it in 4 weeks, not 8 months,     │
 │  and the shim is disposable.                                     │
 └────────────────────────────┬─────────────────────────────────────┘
                              ▼
 ┌──────────────────────────────────────────────────────────────────┐
 │ P1'  CANONICAL STORE                                             │
 │  · conversation_messages + message_parts + summaries             │
 │  · MIGRATION of existing parts_json blobs (shape-inferred;       │
 │    no version discriminator exists — F-25e — so accept and       │
 │    quarantine an unprovable residue)                             │
 │  · golden test: replay → reducer → final state MUST byte-equal   │
 │    persisted message_parts (§17.6)                               │
 │  · new route persists canonically; OLD ROUTE UNTOUCHED           │
 │    → rollback is a flag flip, not a revert                       │
 │  · per-turn provenance stamp (D-16)                              │
 └────────────────────────────┬─────────────────────────────────────┘
                              ▼
 ┌──────────────────────────────────────────────────────────────────┐
 │ P2'  ENGINE EXTRACTION + PLANNER UNIFICATION                     │
 │  · unified plan type FIRST (§9.5 — if it's hard to write, the    │
 │    unification isn't ready)                                      │
 │  · loop extracted as channel-agnostic service, headless-callable │
 │  · delete the two dead islands (adapters/agentic_loop/,          │
 │    single_pass) — §16.5                                          │
 │  · clarification as a third planner outcome (§6.6)               │
 │  · pre-commit grounding gate; register lint as rewrite/telemetry │
 │  · audience_tier excision incl. prompt-template collapse (§13.7) │
 │  · rate limiting + spend caps + middleware layer (§14A.2)        │
 └────────────────────────────┬─────────────────────────────────────┘
                              ▼
 ┌──────────────────────────────────────────────────────────────────┐
 │ P3'  MCP CHANNEL  (parallel-capable with P4')                    │
 │  · prashna_ask + MCP-consult projection + OT-10 ruling           │
 │  · alias cutover as STRANGLER, one instrument at a time behind   │
 │    a parity gate — NOT one breaking release (§8.5 mandate)       │
 │  · extend the shim generator from 3 pilots toward full coverage  │
 │  · injection containment (§14A.1)                                │
 └────────────────────────────┬─────────────────────────────────────┘
                              ▼
 ┌──────────────────────────────────────────────────────────────────┐
 │ P4'  SAMĪKṢĀ + THE LOOP CLOSES                                   │
 │  · review surfaces, jobs, digest, window-close                   │
 │  · conversational capture moment (§6.6.3)                        │
 │  · dispute capture (§14.8) + feedback endpoint restored          │
 │  · NO-LEAKAGE arms 2 and 4                                       │
 │  · minimum-n gating before ANY serving loop-back (§14.6 C2)      │
 └────────────────────────────┬─────────────────────────────────────┘
                              ▼
 ┌──────────────────────────────────────────────────────────────────┐
 │ P5'  BREADTH  (parallelizable; ideal for idle agent capacity)    │
 │  · register blocks across the capability surface                 │
 │  · density_contract mandatory + CI census                        │
 │  · signal reader-text editorial pass (~573 signals, top-50       │
 │    first — §13.6)                                                │
 │  · cross-conversation memory (§11.5)                             │
 │  · cockpit 12→6, observatory 10→5                                │
 │  · /admin/users: two-role stub → real, ONLY when a second human  │
 │    exists                                                        │
 │  · sycophancy-drift monitoring (§14.9)                           │
 │  · monorepo — whenever convenient, or never                      │
 └──────────────────────────────────────────────────────────────────┘
```

### §19.3 What was deferred, descoped, or demoted

| Item | v0.1–v0.4 | v0.5 | Why |
|---|---|---|---|
| **Monorepo (A-01)** | P0 gate | Optional, P5' or never | Codegen already delivers single-source contracts across the seam (§8.5). Its justification is obsolete. |
| **Multi-user authz (D-09)** | P1, before the reading surface | Two-role stub; real subsystem only when a second human exists | A first-class access-control subsystem for a system with one real user, scheduled ahead of fixing the reading. |
| **OpenRouter meta-provider** | P3 (A-09) | **Descoped from target** | Elegant, near-certainly zero real usage — the operator uses frontier models. Addable later precisely *because* the tier abstraction is good. |
| **Tier C fat-prompt path** | P3 (§10.4) | **Descoped from target** | Same. The design is recorded and remains correct; it is not built now. |
| **Alias cutover** | "One release, one breaking change" | Strangler, instrument-at-a-time | Contradicted a mandate this repo already adopted (§8.5). |
| **Calibration loop-back** | On first calibration write | Per-cell, on minimum-n | n=7 Brier is precision theater (§14.6). |
| **Prediction capture** | P6, last | **P0', week one** | Every month of delay is data lost forever on multi-year windows. |

**Always-on component budget.** T-3 warned that every always-on subsystem is
future 2 a.m. debugging, then applied the warning only to the model plane.
v0.1–v0.4 proposed **five**: jobs runner, probe scheduler, summarizer worker,
email digest, ledger writer. v0.5 reduces the near-term set to **two** — the
ledger writer (required by NO-LEAKAGE arm 3) and one consolidated scheduled
job that does window-close, digest and summarization in a single cron entry.
The probe scheduler arrives with the model plane, which is now P5'-or-later.

### §19.4 The original sequence (superseded, retained for the reasoning)

P0 Substrate hygiene → P1 Data plane → P2 Registry + planner → P3 Engine +
model plane → {P4 Paripraśna, P5 MCP} → P6 Calibration → P7 Cross-cutting.

Its dependency logic was sound and its stated principle — *"nothing in P0–P5
may make P6 harder"* — remains binding. What it got wrong was treating
dependency order as execution order for a single operator with a broken
surface and a decade-scale calibration clock already running.

**The superseded diagram, retained verbatim:**

```
  ┌──────────────────────────────────────────────────────────────┐
  │ P0  SUBSTRATE HYGIENE                                        │
  │  · monorepo + @marsys/contract; delete envelope mirror       │
  │  · kill 45 aliases; canonical naming                         │
  │  · density_contract mandatory; register block added          │
  │  · CR-28 intent consolidation                                │
  │  Nothing new is built on a two-headed substrate.             │
  └───────────────────────────┬──────────────────────────────────┘
                              ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ P1  DATA PLANE                                               │
  │  · canonical message store (conversation_messages +          │
  │    message_parts + conversation_summaries)                   │
  │  · prediction/calibration schema                             │
  │  · session pin promoted to all conversations                 │
  │  · users / roles / chart_entitlements                        │
  │  · DB role grants (NO-LEAKAGE arms 1 and 3)                  │
  └───────────────────────────┬──────────────────────────────────┘
                              ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ P2  REGISTRY + PLANNER                                       │
  │  · mutation class; sidecar tools pulled in                   │
  │  · three generated projections                               │
  │  · one planner pipeline → PlanReceipt                        │
  │  · acharya floor as the B.11 enforcement point               │
  └───────────────────────────┬──────────────────────────────────┘
                              ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ P3  ENGINE + MODEL PLANE                                     │
  │  · agentic loop extracted as a channel-agnostic service      │
  │  · ModelPlane: health plane, tiers A/B/C, OpenRouter,        │
  │    CachePlanner, reasoning-token accounting                  │
  │  · envelope-native pre-commit grounding gate                 │
  │  · register lint gate                                        │
  └──────────────┬──────────────────────────┬────────────────────┘
                 ▼                          ▼
  ┌────────────────────────────┐  ┌──────────────────────────────┐
  │ P4  PARIPRAŚNA             │  │ P5  MCP CHANNEL              │
  │  · stream protocol +       │  │  · prashna_ask               │
  │    client reducer          │  │  · projection serving        │
  │  · three-region layout     │  │  · session semantics         │
  │  · progressive markdown    │  │  · entitlement tiers +       │
  │  · scroll/caret discipline │  │    cost caps                 │
  │  · disclosure tiers        │  │                              │
  │  · route rename            │  │                              │
  └──────────────┬─────────────┘  └──────────────┬───────────────┘
                 └────────────┬─────────────────┘
                              ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ P6  THE CALIBRATION LOOP                                     │
  │  · detection → confirmation → ledger                         │
  │  · Samīkṣā tab + badge + in-stream affordance                │
  │  · daily job, closing_soon, email digest                     │
  │  · record_outcome → mimamsa_calibration → priors_version     │
  │  · NO-LEAKAGE arms 2 and 4                                   │
  │  LAST in dependency order; FIRST in mission importance.      │
  │  Nothing in P0–P5 may make this harder. P4 ships the         │
  │  prediction card even in rough form.                         │
  └───────────────────────────┬──────────────────────────────────┘
                              ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ P7  CROSS-CUTTING                                            │
  │  · replay harness + layout-shift assertions                  │
  │  · register-leak telemetry                                   │
  │  · registry/doctrine CI gates                                │
  │  · observability unification across both channels            │
  │  · migration sequencing appendix (the ONLY place migration   │
  │    cost is permitted to appear, per D-12)                    │
  └──────────────────────────────────────────────────────────────┘
```

### §19.5 The v0.11 forward sequence — from the as-built position `[ELEVATION F5 v0.11]`

Six waves, ordered by what each unblocks. Waves 1–3 are the beyond-acharya
product work; waves 4–6 are the substrate debts that were always real and are
now the only ones left. Per D-11/§21 rule 6, this is a design of sequence, not
an execution authorization — each wave gets its own brief.

```
 ┌──────────────────────────────────────────────────────────────────┐
 │ WAVE 1 — PB-4 PŪRṆATĀ, gated on A-46 hardening                   │
 │  · pre-cutover hardening FIRST (A-46): middleware + per-user     │
 │    rate limit + per-turn/daily spend ceilings; PITR re-verified  │
 │    + one executed restore drill; ANTHROPIC key provisioned or    │
 │    the stack delisted                                            │
 │  · then BRIEF_PB-4 as written: F-6 smoke → F-1..F-4 → default    │
 │    flip → 7-green hold → retirement → deflag → Q-2 → §G gate     │
 │  · AC-15 begins the day the default flips — the week-of-use      │
 │    gate is the arc's real terminal                               │
 │  UNBLOCKS: everything below runs against the DEFAULT surface.    │
 └────────────────────────────┬─────────────────────────────────────┘
                              ▼
 ┌──────────────────────────────────────────────────────────────────┐
 │ WAVE 2 — FIDELITY: the reading looks like the design (A-37..40)  │
 │  · block typing on the wire (kind+role at commit); verse/table/  │
 │    gap-ribbon/heading live; prediction_card as a wire event      │
 │    → LogToSamiksha mounts (FD-1, FD-4)                           │
 │  · S-3 rewriter wired; first-paint chips; server-derived         │
 │    grounding summary + completeness line (FD-2, FD-6)            │
 │  · every control honest: model_id + length_tier plumbed and      │
 │    implemented, or removed (FD-3); depth from the scope tuple    │
 │    (FD-12)                                                       │
 │  GATE: a real daśā question renders a table AS a table, a verse  │
 │  AS a verse, chips at first paint — on the live wire, no fixture.│
 └────────────────────────────┬─────────────────────────────────────┘
                              ▼
 ┌──────────────────────────────────────────────────────────────────┐
 │ WAVE 3 — THE INSTRUMENT REMEMBERS AND ASKS (A-41, A-42, A-48)    │
 │  · recall wired (prior_reading grade, contradiction surfacing,   │
 │    dedup/decay); the arrival line from L1/Kāla truth             │
 │  · the window-opening ask (pre-plan ledger check → one sentence  │
 │    + one-tap outcome) — the compliance-decay converter           │
 │  · dispute capture + feedback endpoint restored (A-48)           │
 │  · digest transport real; journal → DB (FD-10)                   │
 │  · voice enforcement: remedial-imperative lint + pacing policy   │
 │    (A-43); signal reader text, top-cited-first (A-44)            │
 │  · register labels across the full capability surface + the CI   │
 │    fail-on-missing rule (A-18 completion)                        │
 │  GATE: a returning thread greets with where the daśā stands; a   │
 │  closed window gets asked about in conversation; a remedy is     │
 │  never imperative — all on the register eval's REAL corpus.      │
 └────────────────────────────┬─────────────────────────────────────┘
                              ▼
 ┌──────────────────────────────────────────────────────────────────┐
 │ WAVE 4 — ONE ENGINE IN FACT (the P2' debt)                       │
 │  · unified plan type (PipelinePlan ↔ VidhiPlan reconciliation —  │
 │    ~80% exists as VidhiPlan, §9.5)                               │
 │  · loop extracted headless; prashna_ask re-based onto it —       │
 │    the MCP door gets the SAME gates (register lint, sentinel     │
 │    rewrite) the web door has (closes §6.4's stage-9 asymmetry)   │
 │  · store completion: history/user turns canonical; tool_call/    │
 │    tool_result/reasoning parts written (FD-8)                    │
 └────────────────────────────┬─────────────────────────────────────┘
                              ▼
 ┌──────────────────────────────────────────────────────────────────┐
 │ WAVE 5 — THE WALLS (arm-1 + the sink)                            │
 │  · five DB roles + web app off amjis_app for reads (F-25q);      │
 │    out-of-process ledger writer (arm-3)                          │
 │  · mimamsa_conversational_calibration built EXACTLY per DVA      │
 │    Rulings 55/79 (collect-only, leak-guarded)                    │
 │  · PB-9-DETECTOR: the no-auto-promotion CI detector              │
 │  · byte-equality standing capture posture (Ruling 54 close;      │
 │    FD-9)                                                         │
 └────────────────────────────┬─────────────────────────────────────┘
                              ▼
 ┌──────────────────────────────────────────────────────────────────┐
 │ WAVE 6 — THE AUDIT THAT NEVER ENDS                               │
 │  · post-six-views narration audit (PŪRṆATĀ handoff #2) against   │
 │    the settled Kāla layer, by the arc's proven method            │
 │  · sealed-reading export (A-47)                                  │
 │  · §17.8 production observability (TTFT, gate rates, lint        │
 │    firing rate, coverage) — wire the existing dead cost schema   │
 │    (F-25o), don't design a new one                               │
 │  · sycophancy-drift monitoring (A-33/§14.9) once real usage      │
 │    accrues                                                       │
 └──────────────────────────────────────────────────────────────────┘
```

Two orderings are deliberate. **Hardening precedes the flip** (T-11): the
cutover re-prices every §14A gap, so A-46 is a gate condition, not a wave-6
nicety. **Fidelity precedes remembering**: the arrival line and the
window-ask spend their trust budget through the same surface the reading
does — a paragraph-slab reading with a beautiful arrival line is jewelry on
an unfinished garment. Wave 4 can run parallel to 2–3 where lanes do not
touch; wave 5's arm-1 should land before any second real human gets an
entitlement (D-09's moment).

### §19.6 Decide vs. design

The native decides **values and boundaries**: naming, breaking changes, who
gets what at what cost, launch scope, the OT forks in §2.

Everything mechanical — schemas, projection generation, gate design, protocol
shape — is designed *for* him, each with a one-paragraph ratification ask.

### §19.7 What the P0' gate actually tests

The spike is a falsification instrument, so its pass condition is stated
before it is built:

> **[CORRECTED PG-1 — `PG1-C2-0001`/`-0007`/`-0008`, critical]** This gate is
> **unsatisfiable by a translation shim over the untouched route** (D-17's scoping).
> The **"Work is visible immediately | POST → `turn.open` < 300 ms"** row cannot be
> met today: no SSE stream exists until `runAdapterDispatch` (`route.ts:988`), *after*
> the planner (`:436`) and tool fetch (`:752`), and the two 422 bail-outs (`:447`,
> `:803`) are structurally incompatible with an already-open stream. The **"no `as
> any` anywhere in the writer path"** clause of the reasoning-lifecycle row is
> violated at six existing sites (`run_adapter_dispatch.ts:294,325,329,334,354,573`).
> Passing the full gate requires a bounded reorder of `consult/route.ts` + the
> dispatch delta loop and ~6–9 weeks, **not** 3–4 weeks with an untouched route (see
> D-17 correction, OT-12). The render rows (settled-content/caret/no-transmutation)
> ARE cheaply achievable — Streamdown already implements them (`PG1-C2-0006`).

| Assertion | Measured by |
|---|---|
| Settled content never moves | CLS contribution ≈ 0 above the volatile tail; per-block rect identity frame-over-frame (§17.2) |
| The caret never orphans | Caret rect always within the tail block's rect |
| No transmutation | Visual-regression diffs across replay checkpoints |
| Work is visible immediately | POST → `turn.open` < 300 ms; first activity < 1 s |
| Reasoning has a lifecycle | Valid open/close events; **no `as any` anywhere in the writer path** |
| It survives bad networks | 1-byte trickle, 50 KB slabs, 3 s stalls, mid-block disconnect, reconnect-and-replay |
| It works on a phone | Full fixture suite at mobile viewport; tap-first citations |
| It works with a screen reader | axe-core pass; no re-announcement on block commit |
| **It feels like Claude Code** | The native's judgment. **This is the real gate and it is not automatable.** |

> **[GROUNDED 2026-08-18 — v0.11]** Assessed row-by-row against the shipped
> surface in §16.9.2. The unsatisfiable-by-a-shim finding above became moot
> when PB-1 built the fork with the reorder (OT-12, §1.2); the final,
> non-automatable row is AC-15 and waits on the PB-4 default flip.

---

## §20 — Changelog

| Version | Date | Change |
|---|---|---|
| **superseded** | **2026-08-19** | **G0 CLOSE — SUPERSEDED BY DECOMPOSITION.** The G0-close session (PB-3-Bot, 2026-08-19) executed the mechanics ruled by NCD-2 (2026-08-18): the five-artifact successor set (`PARIPRASHNA_ARCHITECTURE_v1_0.md` + three LIVING companions + `briefs/pariprashna_v012/`) registered in `CAPABILITY_MANIFEST.json` and `PARIPRASHNA_ARCHITECTURE_v1_0.md` flipped to `CURRENT` (red-team record: `RED_TEAM_G0_v1_0.md`, PASS-WITH-FIXES). This file's status is now `SUPERSEDED — superseded-by-decomposition`. It is the frozen forensic/history record for the Paripraśna design arc: §16/§18/§20 remain the corpus of record for how this design was learned; §4–§14A are superseded by `PARIPRASHNA_ARCHITECTURE_v1_0.md` for normative content. Retained in place, never renamed (30+ inbound referrers inventoried 2026-08-18 per R-5 note in the master review). |
| **0.11** | **2026-08-18** | **AS-BUILT RE-BASELINE + FABLE-5 ELEVATION (RG-1 discharge).** The 2026-07-27 SUPERSEDED-IN-PART banner is DISCHARGED — its predicted staleness corrected in place, marked `[GROUNDED 2026-08-18]`, against git HEAD `dfbdfe620`, the PB close corpus, and a live MCP census (**125 tools, `catalog-1+t152+r653c2a1a98c8`**).<br><br>**THE HEADLINE: the conversation layer was BUILT.** PB-1 DHĀRĀ (typed 15-event Zod SSE protocol, stream-first fork of consult, three-region renderer with freeze discipline, right dock, closed lexicon, server-side register lint), PB-2 SMṚTI (`message_parts` migration 467, durable summaries to the §11.3 spec, Redis ring-buffer resume with `Last-Event-ID` replay, the D-16 per-turn stamp), PB-3 SAMĪKṢĀ + PB-3.1 (the 9-state `brahma_mimamsa_prediction_ledger` with the stamp copied at confirm under the `trg_bmpl_freeze_confirmed` DB trigger, review tab, batch resolve, daily job, Brier at resolution) — live in production behind `PARIPRASHNA_ENABLED` (ON via env since PB-1), **proven end-to-end by C4-LOOP-LIVE-PROOF 2026-08-01 with a real concurrent user (T-9 RESOLVED FORWARD)**. NOT happened: PB-4 cutover, AC-15, arm-1 roles, the ruled-unbuilt calibration sink, PB-9-DETECTOR.<br><br>**NEW REGISTERS:** §1.2 resolved-by-events (OT-2 job handle · OT-7/OT-10 generated `full`/`compact`/`consult` profiles · OT-8 rebuilt-on-parts · OT-11 canonical ledger built · OT-12 fork-with-reorder · PARK L-5 ruled by DVA 55/79); §16.9 the as-built census — doors/deployment, §19.7 gate re-assessment, the **fidelity debt register FD-1..FD-12** (paragraph-only live wire; S-3 rewriter built-unwired; cosmetic model/length pickers + nonfunctional `length_tier`; `LogToSamiksha` unmounted; recall unwired; client-synthesized grounding; delta-boundary lint escape; assistant-only canonical store; capture flag held OFF per Ruling 80; log-only digest; two error classifiers; crude depth mapping), F-register dispositions (F-25b/c/d/q/t STAND; F-01..F-11, F-25e/f SUPERSEDED on the new surface; F-25g downgraded — the tier prompt-keying is excised, the live D-15 violation closed), and the engine-content deltas since 08-01 (PRATIJÑĀ v4.1 adopted verdicts, GOCHARA v3 under PARIṢKĀRA's honest re-close, KP sub-lord clock, fact-identity index, SAMPŪRTI W0).<br><br>**ELEVATION `[ELEVATION F5 v0.11]` — A-37..A-48, the beyond-acharya register:** live block fidelity with `prediction_card` as a wire event (one change unlocking three debts) · first-paint citations + server-derived grounding · every control honest or absent · depth derived from the scope tuple, served visibly · the remembering wave (recall + arrival line + contradiction surfacing) · **the window-opening ask — the single highest-leverage unbuilt feature** (every precondition shipped) · voice enforced not requested (remedial-imperative lint, pacing policy) · signal reader text prioritized by observed citation frequency · new engine layers surface at their earned tier only (T-8 extended) · pre-cutover hardening as a PB-4 entry condition · the sealed-reading export · dispute capture. **§19.5 forward sequence** (six waves: harden→cutover, fidelity, remember+ask, one-engine-in-fact, the walls, the unending audit). **PROPOSED rulings** on all remaining open forks (OT-1 confirm in-process · OT-3 confirm cron-in-webapp · OT-4 super-admin-only builds with guest request · OT-5 ratify shipped auth · OT-6 close as none, T-2's condition met). **NEW TENSIONS:** T-10 (as-built divergence must be classified: ruled / disclosed-lossy / silent debt — or lossiness ages into de-facto architecture) and T-11 (**a gate that promotes a surface must re-price every risk priced under the old exposure**). Authored by Claude (Cowork, Fable 5) in consultation with the native; per §21 rule 6 this version authorizes no code change. |
| 0.10 | ~2026-07-27 | **Reconstructed at v0.11 — this row was never written, a §21 rule 2 violation disclosed rather than papered over.** The frontmatter reached `version: 0.10` (and the footer was left saying v0.6 — same drift class) with no changelog entry. Best reconstruction from the artifact itself: v0.10 = the ⚠ SUPERSEDED-IN-PART banner of 2026-07-27 and its staleness table, added after the Retrieval Plane Elevation + Residual Closure campaigns outran the registers. No design content is attributed to 0.10 beyond that banner. |
| **0.9** | **2026-07-22** | **RC-13 (R-4 / W-17) — the code-level `session_pin` → `provenance_stamp` rename v0.8 deferred is now EXECUTED**, Resolver-ratified against the D-16 doctrine already on record (§11.4). GT-F28 closed (was NEEDS-RULING). §7.1's live storage diagram corrected at source: the `session_pins (build provenance)` / `priors_version in session pin →` line read `provenance_stamps (build provenance)` / `priors_version in provenance stamp →`. Internal-only, zero behavior/contract/UX change — pure identifier + served-JSON-field rename (`session_pin` → `provenance_stamp`) across `platform/src/lib/retrieval/session_pin.ts` (renamed `provenance_stamp.ts`) and its ~13 code-file consumer set (route handlers, MCP session/chart-selection/session tools, the codegen'd envelope mirror, capabilities resource doc). Does NOT execute the broader D-16 storage restructuring (immutable per-turn `conversation_messages.metadata_json`, per-turn drift detection, ledger-row copy-not-reference) — that remains separately scoped, unexecuted work; this residual closed naming only, per its own DONE bar. Full platform + platform-mcp suites green with zero test-count delta versus the pre-rename baseline. |
| **0.8** | **2026-07-22** | **W-19 (AMBIG-4-authorized docs task, retrieval campaign W6):** §6.1 diagram corrected at source — the `prashna_ask` box listed a stale `depth` param (struck by D-15, v0.2) and the AGENTIC LOOP box still said "session pin ... pinned for ALL conversations" (struck/restructured by D-16, v0.3). Diagram now reads `prashna_ask(chart_id, question, scope_tuple?, response_format)` and "provenance stamp (...) — per-turn, D-16", matching this document's own already-ratified D-15/D-16 rulings and the C-1 signature actually shipped. Docs-only fix, scoped to §6.1 per AMBIG-4's authorization — does NOT execute the broader code-level `session_pin` → `provenance_stamp` rename (W-17/GT-F28), which remains its own unratified item (see `briefs/retrieval_audit/GROUND_TRUTH_REGISTER.md` GT-F28, status NEEDS-RULING) carried to the campaign's §H residuals. |
| **0.7** | **2026-07-19** | **PG-2 diagnostic-wave integration (Lane Z-2 synthesis).** The six-lane PG-2 wave (44 findings, all ACCEPT) closed the high-consequence items PG-1 left undiagnosed, in place with the original visible (`[CORRECTED PG-2]` + finding id), per §0.5/D-18. **F-25u RESOLVED BENIGN** (`PG2-X1-0001..0006`): the `chart_facts` "+402% divergence / unstable across probes" alarm is retracted — `chart_facts` stores one ~27,677-row fact set **per ayanamsha** (5 partitions) + 135 invariant rows = **138,519** per fully-built chart; 138,519+137,687=276,206 (two built charts); 27,554 is the stale v1.0/single-ayanamsha figure; zero dup fact_ids, zero natural keys span >1 build_id; "unstable" was an unfiltered-vs-chart-scoped category error. **T-9 RESOLVED** (`PG2-X2-0001`, critical): the chat engine does **NOT** work — `/api/chat/consult` 500s deterministically at `bundle_hydrator.ts:25` on the retired `FORENSIC` floor asset (deleted from the manifest in PR #187), before any stream opens; same class as LCA-2, one stage downstream; **one-line fix**. This resolves T-9's "wired but 0 rows" ambiguity into a definite, code-confirmed broken-at-a-named-line answer. **§16.8 (new):** A-14 memoization ruling mislabel-fixed + **INVERTED** (`PG2-X4-0006` — virtualizer IS live, both replacements absent); citation shape clarified (`PG2-X4-0003` — a `CitationPart` in `parts_json`; PG-1's "none found" was a DB-emptiness artifact); `chart_agnostic_gate` A-2 confirmed fail-closed (`PG2-X4-0002` — `400 CHART_REQUIRED`, no leak); two-vs-three prediction ledgers (`PG2-X5-0006`); F-25v Bearer 401 resolved (`PG2-X3-0001` — stale key, not broken auth); coverage now **133/139 (~96%)** (`PG2-X3-0010`). **OT-11 costed, not resolved** (`PG2-X5-0007`, PC-8 — no choice made): three ledgers not two, neither satisfies §14.3 without a schema change; Option A (merge) and Option B (document) fully priced. **A-31 compliance decay** confirmed absent (`PG2-X4-0007`); **A-03/04/06/09** reclassified unverifiable→confirmed-not-built (`PG2-X4-0008`). **PG-1's gate re-audited VALID** (`PG2-M1-0001..0012`) — GATE GREEN upheld; the sealed report's stale 87 finding count (→98) and 5 critical count (→6) corrected in place in the PG-1 sealed artifacts. Sibling artifacts authored this wave: `PG2_DIAGNOSTIC_REPORT_v1_0.md` (per-question resolutions + 44-finding severity table) and `RETRIEVAL_SYSTEM_TRUTH_v2_0.md` (supersedes v1.0; adds the first live serving-path datum). |
| **0.6** | **2026-07-19** | **PG-1 grounding-audit integration (Lane Z-1 synthesis).** The independent 12-lane PG-1 wave re-grounded this document against the working tree, live DB, and infra — 87 findings, all verified ACCEPT by the Opus floor. Corrections made **in place with the original visible** (`[CORRECTED PG-1]` + finding id), never deleted, per §0.5/D-18. **Register corrections:** D-17's "3–4 week disposable shim, no planner work, old route untouched" premise struck as **FALSE as scoped** (`PG1-C2-0001`/`-0008`) — a shim cannot emit `turn.open` before the planner without a `consult/route.ts` reorder; full §19.7 gate is ~6–9wk (new fork **OT-12** for the native's PC-2 call). **§1.1 assumptions:** A-03 capability counts corrected (**119 registry URIs / 139 tool names / 120 stale census / 113 = wrong artifact**, a category error, `PG1-R1-0001..0003`); A-06 corrected (**4 planner surfaces, 2 live-divergent** `PipelinePlan`↔`VidhiPlan`, 2 dead islands; **`PlanReceipt` absent from code entirely**); A-07 corrected (**"two doors" is one door** — `prashna_ask` has ZERO source hits); A-08 corrected (parts are a `parts_json` **blob**, not child rows; store is **empty** so the migration is green-field schema-hardening, not salvage); A-19 corrected (**NO-LEAKAGE arm-1 is 0% built** — single `amjis_app` credential has full CRUD on ledger + calibration, critical). **§7.1/§7.4:** target-state table names (`brahma_*`) and the five NO-LEAKAGE roles do not exist live; two disjoint prediction ledgers (**OT-11**). **§9.5/§16.5:** the planner-unification is **confirmed week-scale integration, not a contradiction** (`PG1-R3-0007`, ~80% already in MCP `VidhiPlan`); `single_pass` precise status corrected (**test scaffold, not on the runtime path** — supersedes both the prior "dead branch" AND C-3's "not dead"); D2 router + platform `lib/vidhi/compiler.ts` corrected to **dead islands**. **§16.4 counts** corrected (139/119, not 126). **§19.7** annotated as unsatisfiable by an untouched-route shim. **NEW §16.7 — fifteen forensic defects F-25h…F-25v:** stale parity comment; stale tool census; `unknown_tool` drill fallback; `phala_anchors_get` 422 / `ref_dignity_reference_get` 400 (first-day hard errors); null-total legacy envelope; double-encoded KEYSTONE sidecars; dead cost-accounting schema (cost/latency **unmeasurable today**); two disjoint prediction ledgers; **NO-LEAKAGE roles 0% built (critical)**; `brahma_*` phantom tables; build-side grade/varga incoherence; **Cloud SQL PITR disabled + no restore drill**; **`chart_facts` +402% divergence from the sealed L1 closure**; **Bearer-key MCP 401**. **NEW T-9:** the instrument has never produced a served reading — §J is unproven and every serving-path audit is of an unexercised path. Sibling artifacts authored this wave: `RETRIEVAL_SYSTEM_TRUTH_v1_0.md` (current-state system description) and `PARIPRASHNA_GROUNDING_AUDIT_REPORT_v1_0.md` (full report: A1–A32 verdict table — 29/32 audited — the verbatim shim-feasibility=NO, Q-1 reading-quality, and R-3 falsification verdicts, and the prioritized immediate-fixes list led by wiring `codegen:check` into CI). |
| **0.5** | **2026-07-19** | **Adversarial-review integration — the largest revision to date. Every finding from the independent Fable 5 review is implemented, plus a full re-verification sweep that found further errors the review had not caught.**<br><br>**CORRECTIONS (the document was wrong):** §8.5 rewritten — the envelope mirror **was already deleted and codegen'd** (`platform-mcp/src/generated/envelope.ts`, four codegen scripts in `package.json`); "the codegen lane never landed" was false; **A-01 monorepo demoted** from P0 gate to optional since its justification was obsolete; the repo's own §19 SINGLE-SOURCE CONTRACT GENERATION mandate and its brief-§6.2 STRANGLER discipline (*"no single PR regenerates the estate"*) are now quoted and honoured, replacing v0.1–v0.4's big-bang cutovers. **New gap surfaced by the correction: `codegen:check` exists and no CI workflow invokes it — contract drift is currently undetected** (now a P0' one-liner). §16 corrected counts: aliases 45 → **55** (three sources disagree: 55 actual / 47 header / 45 census); tools ~118 → **120 declared, 126 actual**; planners "three" → **3 live + 2 dead islands**, incl. the trap that **two folders are named `agentic_loop`**; F-12 corrected — `useScrollDiscipline` is **live and unflagged**, not dormant; F-15 split into four precise claims (2 genuinely dead, 1 transitively dead, 1 with type-only importers in a dead cluster).<br><br>**SEVEN NEW FORENSIC DEFECTS (F-25b…g):** a fully-built error classifier that **nothing imports**; a feedback endpoint that **validates auth, echoes the rating, and persists nothing** while the UI appears to work; **no rate limit or spend cap on chat and no middleware file to add one at**; `parts_json` with **no version discriminator**, making its own migration unverifiable; stream resume that is **snapshot-based with `last_event_seq` stored but never consumed** — no reconnection on a mid-session drop; and **`audience_tier` half-excised but still load-bearing in prompt-template lookup**, meaning the system today produces different prose per tier — a live D-15 violation.<br><br>**NEW §16.6 — capabilities that do not exist:** reconnection, rate limiting, blocking spend caps, backup/DR posture, prompt-injection defense, migration tooling, TTFT metrics, clarifying questions, disagreement capture, reader-facing signal text, remedy register guardrails. Mobile verified PARTIAL (`md:` only, no touch handlers); **accessibility verified better than assumed** — `role="log"`, `aria-live` toggled only while streaming, SR announcer — an asset to preserve rather than a gap to fill.<br><br>**DESIGN CHANGES:** **§12.4 segmentation moves server → client** (blank lines are legal inside loose lists; a server splitter recreates the mirror disease at a layer where drift renders wrong instead of failing to compile; and `block.commit` cannot be byte-final when the LLM restructures mid-thought). **§13.5 lint defanged** — fail-the-turn abolished, `\bL[0-5]\b` removed as a false-positive risk in health readings, and the **streaming contradiction stated honestly: the deltas already went out, so the leak does not persist but the reader saw it**. **§12.9.1 sentinel failure handling specified** (64B/400ms hold-back or the stream stalls forever; tolerant grammar; per-model hallucination counters). **§9.5 planner-unification realism** — the common plan algebra does not exist and *is* the work.<br><br>**NEW SECTIONS:** §6.6 the instrument must be able to ask (praśna śāstra is the art of the question and the surface named for *paripraśna* could not ask one) incl. the unresolved-window opening that converts compliance decay into a conversational moment; §11.5 cross-conversation memory with `prior_reading` as a citation kind that can never satisfy the acharya floor; §12.9.2 transport resilience; §12.10 failure UX; §12.11 mobile; §12.12 accessibility; §13.7 the `audience_tier` excision; §13.8 remedy register; §13.9 emotional register as design input; §14.6 minimum-n gating and the collect-only phase (**n=7 Brier is precision theater**); §14.7 designing for compliance decay; §14.8 capturing disagreement; §14.9 sycophancy drift; §14A security, cost governance and durability (**the conversation store and ledger are the only irreplaceable data and have no backup posture**); §17.8 production observability.<br><br>**§19 RESTRUCTURED shim-first (D-17):** P0' proves or kills the core bet in 3–4 weeks via a translation shim over the existing engine — no monorepo, no store change, no planner work, old route untouched — with capture starting week one. Multi-user authz demoted to a two-role stub; OpenRouter and Tier C descoped; always-on components cut 5 → 2. **§19.7 states the gate's pass conditions before it is built**, ending with the one that is not automatable: *does it feel like Claude Code?*<br><br>**NEW TENSIONS:** T-7 (this document's claims decay and did) and T-8 (**cheap honesty mechanisms become dishonest at low n** — B.10 forbids fabricating a computation; do not fabricate a precision either). **D-17, D-18 ruled; A-01 demoted; A-21…A-36 added.** |
| 0.4 | 2026-07-19 | **Consolidation pass — captures everything discussed since v0.1 that had not yet been written down.** New **§0.4 Workstream split**: the design now runs in two parallel conversations with a shared decision register; the MCP channel has its own self-contained handoff (`briefs/MCP_CHANNEL_WORKSTREAM_HANDOFF_v1_0.md`); shared substrate belongs to neither and is redesigned unilaterally by neither; OT-2/5/6/7/10 are MCP-owned and their rulings flow back here. New **§6.4 Query lifecycle**: a 12-stage table proving there are **three paths, not two** — only auth, provenance and dispatch-to-envelope are common to all three; Paripraśna and `prashna_ask` are one architecture, raw-tools MCP is not ("we expose our retrieval plane; someone else's brain uses it"). New **§6.4.1**: two guarantees cannot cross to raw tools — **B.11 is unenforceable** there, and **D-14 is structurally undeliverable** because no prose crosses our boundary to lint; therefore the envelope is the only defense on that path, which retroactively justifies the doctrine work. New **§6.5 The engine boundary**: the engine is door-agnostic and outside both channels, with the design test *"the engine must never branch on which door it is serving"* and the corollary that it must be callable headlessly. New **§6.5.1 / OT-10**: there is one MCP connection, not two channels — `prashna_ask` is one tool among the raw tools, so **the client's model decides which quality floor applies**, a decision we do not control and never designed; noted explicitly as *not* an audience-tier question (D-15). **T-2 sharpened**: the two-class risk is about missing guarantees, not missing history, raising A-07 from a good idea to load-bearing. |
| 0.3 | 2026-07-19 | **D-16 ruled: the session pin is a per-turn provenance stamp, not a session pin.** Native's challenge — §N.3's delete-then-insert means one build exists and nothing is archived, so a pin has no power to hold a conversation at an earlier build. Assessed honestly: the construct is a witness, not a lock, and earns its keep on three grounds (drift disclosure, audit provenance, and above all **calibration attribution** — without it the Brier score attributes error to the wrong technique version, making calibration "noise dressed as evidence"). Restructured: renamed provenance stamp; moved from mutable `mcp_sessions.state_json` to immutable per-turn `conversation_messages.metadata_json`; drift detected by comparing consecutive turns rather than via shared session state; **copied immutably into ledger rows**, never referenced; removed from the engine's input signature. **A-10 restructured.** §11.4 rewritten. Engine signature now `ask(chart_id, question) → {…, provenance}`. Known limitation recorded (not solved, at the native's direction): readings are not reproducible without build archives; two cheap partial mitigations noted for if that ever matters. Also noted: `now_context_date` was doing a different job from the version fields all along. |
| 0.2 | 2026-07-19 | **D-15 ruled: no audience tier, no depth parameter, acharya-grade by default, always.** Native rationale: the legacy model had a tier structure that was deliberately torn down and must not return; this extends §N.4's build-layer rule to the serve layer. Consequences applied throughout: **A-16 struck** (three disclosure tiers); **OT-9 closed** (Sanskrit policy dissolves — used where substantive, glossed inline, for everyone); §13.4 rewritten as *one reading, one register, audit as affordance* with the tier-vs-affordance distinction as its spine; §12.8 recast from tier projection to one row model at two zoom levels; §13.3 `practitioner_label` struck from the citation part; §8.7 `register` block gains `canonical_term` replacing `practitioner_label`, explicitly not a tier alternative; engine signature reduced to `ask(chart_id, question, pin)`. Also recorded: an unverified paraphrase of the Ethical Framework's "stated disclosure tiers" was used to justify A-16 and is flagged in §13.4 as needing a source check before anything is built on it. |
| 0.1 | 2026-07-19 | Initial draft. Captures the full consultation to date: naming (D-01/D-02/D-03 + rejected candidates), two-channel model (D-04/D-05), guest model (D-09), topology and monorepo (A-01), registry projections and alias removal (A-02/A-03/A-04/A-05), planner unification and CR-28 (A-06), one-loop-two-doors and `prashna_ask` (A-07), canonical message store (A-08), model plane with tiers and OpenRouter (A-09), session pin promotion (A-10), AI SDK transport replacement and block-level stream protocol (A-11/A-12), three-region layout (A-13), no virtualization (A-14), citation sentinel rewriting (A-15), disclosure tiers (A-16), pre-commit register gate (A-17), registry-held vocabulary (A-18), four-arm NO-LEAKAGE (A-19), replay-harness verification (A-20). Forensic appendix §16 records 25 verified legacy defects with file:line. Six tensions registered in §18. Nine open forks in §2. |

---

## §21 — How this document evolves

1. **§1 and §2 are the live registers.** A ruling moves a row from §2 to §1
   with its date and rationale, and the affected section is updated in the
   same edit.
2. **Every substantive change appends to §20.** Version bumps follow B.8:
   0.x while DRAFT, 1.0 when the architecture is ratified and execution
   begins.
3. **§16 is append-only.** Defects found later are added; nothing is removed,
   because the appendix's purpose is to prevent re-entering traps.
4. **§18 tensions are never silently closed.** A tension is resolved only by
   an explicit decision recorded in §1.
5. **Conflicts with governing artifacts are defects in this document.** If
   this document appears to contradict `CLAUDE.md`,
   `PROJECT_ARCHITECTURE_v2_2.md`, `MACRO_PLAN_v2_0.md`, the
   `GOVERNANCE_INTEGRITY_PROTOCOL`, or `CAPABILITY_MANIFEST.json`, raise it —
   do not resolve it in this document's favour.
6. **This document does not authorize code changes.** Per D-11, execution
   begins only when the architecture is ratified and a `CLAUDECODE_BRIEF` is
   issued with explicit `may_touch` / `must_not_touch` scope.

*End of PARIPRASHNA_TARGET_ARCHITECTURE v0.11 (2026-08-18) — DRAFT, LIVING.
v0.11 = as-built re-baseline (RG-1 discharge) + Fable-5 elevation pass;
corrections in place per §0.5/D-18; §16.9 is the as-built census of record;
§19.5 the forward sequence. The surface exists — what remains is making it
worthy of its name.*
