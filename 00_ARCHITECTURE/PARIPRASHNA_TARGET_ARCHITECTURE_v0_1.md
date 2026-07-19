---
artifact: PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md
canonical_id: PARIPRASHNA_TARGET_ARCHITECTURE
version: 0.5
status: DRAFT — LIVING
verified_against_tree: 2026-07-19 (full sweep, post-adversarial-review — see §0.5)
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

**Verified as of: 2026-07-19** (full sweep, post-adversarial-review).

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
| **D-17** | **Sequencing inverts: build the render bet first, as a shim over the existing engine. Capture starts week one.** | 2026-07-19 | Adopted from the adversarial review. v0.1–v0.4 scheduled four phases of invisible substrate work in front of the native's actual daily pain, and validated the architecture's most falsifiable bet last — the exact conditions under which a rebuild stalls and gets torn down a second time. P0' proves or kills the core bet in 3–4 weeks with a disposable shim, no monorepo, no store change, no planner work. Prediction capture moves from P6 to week one, because every month of delay loses calibration data forever on multi-year windows. **A-01 (monorepo) demoted** from P0 gate to optional — its justification was obsolete (§8.5). **OpenRouter and Tier C descoped** from the target. §19. |
| **D-18** | **Verification standing: current-state claims are re-verified at every version bump; corrections are made in place with the error visible.** | 2026-07-19 | v0.1–v0.4's §8.5 was materially false when written, along with four counts. This is the repo's own GA.1 failure mode applied to an architecture document. §0.5, T-7. |
| **D-16** | **The session pin is renamed and restructured: it is a per-turn provenance stamp, not a session pin.** | 2026-07-19 | Native's challenge: §N.3 mandates delete-then-insert, so exactly one build of a chart exists in Postgres and there is no archive. **A pin therefore cannot pin** — it has no power to hold a conversation at an earlier build, because that build is gone. The construct is a *witness*, not a lock. Restructured accordingly: (a) renamed **provenance stamp**; (b) moved from mutable `mcp_sessions.state_json` to immutable per-turn `conversation_messages.metadata_json`; (c) drift is detected by comparing this turn's stamp to the previous turn's, needing no shared session state; (d) **copied into every prediction-ledger row at confirmation time, never referenced** — a ledger row is an immutable historical claim and must not point at mutable state; (e) removed from the engine's input signature — provenance comes **out** with the answer, since the engine reads current build state itself. Deletes a mutable shared-state construct and its §31.3 collision-mitigation complexity. §11.4. |

### §1.1 Design conclusions accepted into the architecture

These are not native rulings but design conclusions carried forward as the
working architecture. They are open to challenge but are the current baseline.

| # | Conclusion | Section |
|---|---|---|
| A-01 | ~~pnpm monorepo with `@marsys/contract`; the hand-mirrored envelope is deleted.~~ **DEMOTED by D-17 (2026-07-19).** The mirror was already deleted and codegen'd before this document was written; the monorepo's entire justification was obsolete. Now: **extend the existing shim generator** toward full coverage (strangler, per the mandate the repo already adopted); wire `codegen:check` into CI (currently unwired — drift undetected). Monorepo is optional convenience, P5' or never. | §8.5 |
| A-21 | **Client-side block segmentation** with a stable-prefix parser; one markdown engine in the system. Server-side segmentation runs once post-stream, for persistence only. | §12.4 |
| A-22 | **The register lint is defanged**: rewrite (id-shaped tokens only) / redact-with-flag / telemetry. **Never fail-the-turn.** The primary defenses are clean evidence context and the structured citation channel. | §13.5 |
| A-23 | **Sentinel failure handling specified**: 64-byte / 400 ms hold-back with flush-as-plain-text, tolerant grammar with normalization logging, per-model hallucination counters feeding tier review. | §12.9.1 |
| A-24 | **Transport resilience**: `Last-Event-ID` replay-from-seq over a ring buffer, snapshot fallback with disclosure, reconnect on `visibilitychange`, half-committed turns marked incomplete and excluded from prediction detection. | §12.9.2 |
| A-25 | **Failure UX is a designed surface**, adopting the existing dead `classify-error.ts` rather than writing a new classifier. | §12.10 |
| A-26 | **Mobile is first-class**: tap-first citations, bottom sheets, `visualViewport` handling, touch scroll-break, mobile fixtures in the harness. | §12.11 |
| A-27 | **Accessibility is preserved and extended**, not added — the current `aria-live`-while-streaming pattern is correct and must survive the renderer rebuild. axe-core in the harness. | §12.12 |
| A-28 | **Cross-conversation, per-chart memory**, with `prior_reading` as its own citation kind that can never satisfy an acharya-floor requirement. | §11.5 |
| A-29 | **The instrument can ask**: clarification becomes a third planner outcome, triggered by scope-tuple confidence; drift and unresolved-window prompts. | §6.6 |
| A-30 | **Calibration is gated on minimum-n, pooled across charts by default, reported as intervals**, behind an explicit collect-only phase. | §14.6 |
| A-31 | **Compliance decay is designed for**: batch resolution, LEL-drafted outcomes, non-shameful lapsing, coverage reported alongside every score. | §14.7 |
| A-32 | **Disagreement is captured** as first-class rows; the engine re-retrieves rather than re-words, and never folds when the data supports it. | §14.8 |
| A-33 | **Sycophancy-drift defenses**: synthesis stateless w.r.t. user reactions, identical-question diffing, optimism-bias tracking. | §14.9 |
| A-34 | **Security, cost governance, durability**: injection containment, a middleware layer with rate limits and blocking spend caps, and a verified backup posture for the two irreplaceable tables. | §14A |
| A-35 | **The `audience_tier` residue is excised**, including the load-bearing prompt-template lookup that today produces different prose per tier. | §13.7 |
| A-36 | **Emotional register is a design input**: pacing, calibrated framing, calm gaps, attributive remedy language. | §13.8, §13.9 |
| A-02 | All 45 tool aliases are deleted; canonical naming is `layer_noun_verb`. `tool_name_bridge.ts` survives only for replaying persisted conversations. | §8.2 |
| A-03 | Three registry projections: MCP-full, MCP-compact (~25–35 umbrellas + `marsys_drill`), Chat (planner-filtered per turn). | §8.3 |
| A-04 | A `mutation: true` capability class is introduced; sidecar-served tools are pulled into the registry. | §8.4 |
| A-05 | `density_contract` becomes **mandatory** on every `CapabilityDescriptor`. | §8.6 |
| A-06 | One planner **pipeline**, not three planners: scope → route → constrained LLM synthesis → vidhi validator emitting a `PlanReceipt`. CR-28 closes with one intent classifier. | §9 |
| A-07 | **One agentic loop, two doors.** Extracted as a channel-agnostic service; MCP gets `prashna_ask`. | §6.3 |
| A-08 | **Neutral/canonical message store**: `conversation_messages` + `message_parts` child rows. Replaces the AI-SDK `UIMessage` blob. | §11.1 |
| A-09 | Model plane: registry-as-data + live health plane + explicit Tier A/B/C + OpenRouter meta-provider + CachePlanner + reasoning-token accounting. | §10 |
| A-10 | ~~Session pin promoted from MCP-only to all conversations.~~ **RESTRUCTURED by D-16 (2026-07-19).** Now: a **per-turn provenance stamp** recorded on every assistant turn in both channels, copied immutably into ledger rows. Not session state. | §11.4 |
| A-11 | **The AI SDK transport is replaced** by a typed SSE event protocol with a purpose-built client reducer. | §12.2 |
| A-12 | Stream semantics are **block-level**, not token-level; blocks commit and freeze. Stream protocol and storage schema are the same algebra. | §12.3 |
| A-13 | Three-region turn layout: permanent stable-height Working region, append-only Answer region, post-settle Grounding region. | §12.5 |
| A-14 | **No virtualization.** Frozen-block memoization + `content-visibility` instead. | §12.7 |
| A-15 | Citations: model emits sentinels; **server rewrites before the wire**; structured `citation.define` events; tier-projected rendering. | §12.9, §13.3 |
| ~~A-16~~ | ~~Three disclosure tiers — reader / practitioner / audit.~~ **STRUCK by D-15 (2026-07-19).** Replaced by: one reading, one register, audit detail as an **affordance** rather than a mode. | §13.4 |
| A-17 | Register enforcement is a **pre-commit server-side gate**, not a prompt instruction. | §13.5 |
| A-18 | Reader-facing vocabulary lives in the **capability registry** as a `register` block; missing labels fail CI. | §13.6 |
| A-19 | NO-LEAKAGE is enforced four ways: DB role grants, registry flag, out-of-process ledger writer, CI canary. | §14.6 |
| A-20 | Verification centres on a **streaming replay harness** with a zero-shift budget for settled content. | §17 |

---

## §2 — Open decisions register

The genuine forks. Each blocks something specific; none should be answered by
default.

| # | Fork | Blocks | Options | Lean |
|---|---|---|---|---|
| **OT-1** | **Where does the engine live?** | Deployment topology; `prashna_ask` timeout behaviour | (a) In-process with the Next.js web app; MCP edge calls its internal API. (b) Standalone engine service both call over HTTP. | (a) — the engine is TypeScript sharing the contract package, and process separation buys nothing until a second UI exists. Caveat: constrains long-running `prashna_ask` to Next.js execution limits. |
| **OT-2** | **`prashna_ask` transport semantics.** | MCP edge design; whether a job table exists | (a) Non-streaming request/response — simple, but deep questions run minutes and clients time out. (b) MCP progress notifications — better UX, uneven client support. (c) Job handle: `prashna_ask` returns a ticket, `prashna_result` fetches. | (b) with (c) as fallback. Needs a ruling because it shapes the edge and possibly the schema. |
| **OT-3** | **Jobs runner deployment shape.** | Ops surface; NO-LEAKAGE arm 3 | (a) Dedicated third deployable — clean role separation, one more thing to operate. (b) Cron-triggered routes inside the web app, with the **ledger writer** as the only separately-deployed worker. | (b). NO-LEAKAGE strictly requires only the ledger writer out-of-process; the rest is taste, and for a single-operator system every always-on subsystem is future 2 a.m. debugging. |
| **OT-4** | **Guest build rights.** | Nirmāṇa authz model | (a) Guests may trigger a rebuild of their own chart. (b) Build execution is super-admin-only; guests are read-only on build state. | Undecided — this is a cost and failure-ownership question, not a technical one. Decides entitlement-scoped vs role-gated authz on orchestrator triggers. |
| **OT-5** | **MCP OAuth issuer.** | Identity spine; entitlement resolution | (a) Self-issued OAuth 2.1 in the edge — full control of token lifecycle. (b) Delegate to Firebase, edge as resource server — one identity spine, entitlements resolve from one user table with no mapping layer. | (b) is architecturally cleaner if Firebase can act as an OIDC provider for MCP clients; (a) is the current direction. Decides whether an MCP identity *is* a portal user or merely maps to one. |
| **OT-6** | **Does the MCP channel get *any* durable memory?** | §11.5; whether MCP is a second-class channel | (a) None — raw tools + `prashna_ask`, stateless beyond the session pin. (b) Journaling tools so an MCP session's *questions and retrievals* persist even though assistant text cannot. | Flagged by §18/T-2: D-05 is safe **only if** `prashna_ask` ships. If A-07 were rejected, D-05 should be revisited. |
| **OT-7** | **Assent to "one registry, many generated projections."** | Every downstream registry decision | The native's D-08 sentence admits two readings: "same surface everywhere" vs "best surface per channel/tier". | Explicit ruling needed. §8.3 assumes the latter. |
| **OT-8** | **Fate of `ConsumeChatV2.tsx` (2,304 lines).** | §12 execution | (a) Rebuild the UI shell on canonical parts. (b) Refactor in place. | Not yet assessed as a component. Given A-11/A-12 change the client's entire data model, (a) is likely, but this must be assessed before it is asserted. |
| **OT-10** | **MCP profile selection — who decides whether a query gets the engine or the raw retrieval plane?** | The entire MCP surface design | See §6.5. (a) Both tools exposed, steer via tool descriptions. (b) **Two connection profiles selected at connect time** (consultation vs practitioner). (c) One connection, scope-gated. (d) `prashna_ask` only. | **(b) with (c) as the enforcement mechanism.** Owned by the MCP workstream (see §0.5); ruled there, recorded here. |
| ~~OT-9~~ | ~~Sanskrit exposure policy at reader tier.~~ **CLOSED by D-15 (2026-07-19).** With no tiers, the question dissolves: Sanskrit is used where it *is* the substance (a yoga's name), glossed inline, **for everyone**. "Śaśa Yoga — Saturn strongly placed in its own sign in an angle." A layperson learns something; a practitioner reads past the gloss. One text serves both. | | |

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
 └──────────┬──────────┘                              │          │  depth)
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
 ║  │ session pin (priors_version, formula_│  ║      │
 ║  │ versions, ranking_config, build_id,  │  ║      │
 ║  │ now_context_date + drift detect) —   │  ║      │
 ║  │ pinned for ALL conversations         │  ║      │
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
 session_pins (build provenance)       priors_version in session pin →
                                       epistemic annotations in
 IDENTITY                              phala/kala envelopes
 ════════
 users · roles(guest, super_admin)
 chart_entitlements(user × chart × grant)
 oauth_clients / mcp_keys
 model_health (probe results)
```

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
| Total tools | ~118 | **Census constant says 120** (`REGISTERED_TOOL_COUNT`, `server.ts:520`); **raw `server.tool(` count is 126.** The health endpoint reports the hardcoded 120. The gap is the alias undercount. **The census is hand-maintained and wrong in both directions — this is exactly what D-08's generated projections exist to eliminate.** |
| Planners | 3 | **2 live, 2 dead** — see §16.5. |
| `density_contract` coverage | 6 of ~118 | **Confirmed: 6.** `get_dasha_lord_capability.ts:148`, `get_vichara.ts:124`, `get_yoga_dosha.ts:68`, `get_yoga_firings.ts:61`, `register_d9_judgment.ts:415`, `L2_bodha/query_signals.ts:226`. Five of six are L1. |

### §16.5 The planner census, corrected

v0.1–v0.4 said "three unreconciled planners." The adversarial review said four.
**Both were wrong.** Verified:

| Component | Path | Status |
|---|---|---|
| Live agentic loop | `platform/src/lib/synthesis/agentic_loop` | **LIVE** — the real loop; 18+ test files import it |
| `pipeline_planner` | `platform/src/lib/pipeline/pipeline_planner.ts` | **LIVE** — what the chat route calls |
| D2 router | `platform/src/lib/retrieval/router/` | **LIVE** |
| vidhi compiler | `platform/src/lib/vidhi/` | **LIVE** — behind `plan_retrieval` |
| `adaptive_planner.ts` | `platform/src/lib/retrieval/**adapters**/agentic_loop/` | **DEAD** — 3.6KB; exports `planNextAction`/`shouldStopEarly`; its only importers are `loop_engine.ts` and `reflection.ts`, both siblings in the same folder. **The entire 7-file folder is an unreferenced island.** |
| `singlePassPipeline` | `platform/src/lib/pipelines/single_pass/` | **DEAD BRANCH** — `selector.ts` docstring: *"R11E loop flags permanently true (WS-0 2026-06-04): all 5 providers use the agentic path unconditionally."* `AGENTIC_PROVIDERS` covers all five adapters, so single_pass is returned only for an unknown adapter id. Structurally live, operationally unreachable. |

**Trap for the rebuild:** there are **two folders named `agentic_loop`** —
`lib/retrieval/adapters/agentic_loop/` (dead island, contains
`adaptive_planner`) and `lib/synthesis/agentic_loop` (live). Any statement
about the loop or the planner must name the full path. This near-namesake
collision produced the erroneous census in v0.1–v0.4 *and* in the adversarial
review.

Net: the unification is **3 live planning components → 1 pipeline**, plus
**deletion of two dead islands**. Materially smaller than "four planners", but
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

---

## §19 — Sequencing (RESTRUCTURED v0.5 — shim-first)

> **v0.1–v0.4's P0–P7 was dependency-clean and execution-wrong.** It is
> superseded. The original is preserved at §19.3 with the critique, because
> the reasoning matters.

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

### §19.6 Decide vs. design

The native decides **values and boundaries**: naming, breaking changes, who
gets what at what cost, launch scope, the OT forks in §2.

Everything mechanical — schemas, projection generation, gate design, protocol
shape — is designed *for* him, each with a one-paragraph ratification ask.

### §19.7 What the P0' gate actually tests

The spike is a falsification instrument, so its pass condition is stated
before it is built:

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

---

## §20 — Changelog

| Version | Date | Change |
|---|---|---|
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

*End of PARIPRASHNA_TARGET_ARCHITECTURE v0.1 (2026-07-19) — DRAFT, LIVING.*
