---
artifact: BUILD_PROGRAM_TRACKER_v1_0.md
canonical_id: BUILD_PROGRAM_TRACKER
version: rolling
status: LIVING
authored_by: Claude (Cowork) 2026-06-02
last_updated: 2026-06-02 (program open — tracker authored; planning phase)
project_code: TBD (agentic-system name pending — see §0)
purpose: >
  Living status board for the chart-build watertight program: re-author every brief, implement,
  deploy, and verify the full build experience — dashboard → new client → birth-data form →
  save/build/consume → the complete asset DAG A0–A22 + META — guaranteed end-to-end by the
  agentic swarm defined in BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md. Updated at every session close.
  The single answer to "where are we right now?"
read_in_combination_with:
  - 00_ARCHITECTURE/BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md (the swarm + Asset Contract Registry)
  - 00_ARCHITECTURE/FACT_ENGINE_A1_SCOPE_ANALYSIS_v1_0.md (A1 brief correctness analysis)
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md (you-are-here)
legend: "🟢 done · 🟡 partial / in progress · 🔴 broken or stub · ⬜ not started · 🔒 gated/blocked"
---

# Build Program Tracker

*Update this file at every session close. Maintain §1. Append to §7. Update lifecycle status in §4–§6.*

---

## §0 — Name the agentic system (native to choose)

The swarm + orchestrator that runs this program needs a name (the native asked for one). It
becomes the `project_code` above and the program banner. Proposed (Sanskrit, project idiom):

| Option | Meaning | Why it fits |
|---|---|---|
| **Vishvakarman** (recommended) | the divine architect/engineer who builds the cosmos | The system *builds and guarantees* the whole instrument, end to end. |
| **Sthapati** | master builder / temple architect (Vāstu) | Evokes disciplined, spec-driven construction. |
| **Sākṣī** | the witness | Leans on the guarantor/verifier identity. |

*Decision pending. Once chosen, `project_code` + tracker title update; role names (Sūtradhāra,
Nirīkṣaka, …) stay as the swarm's internal cast per the charter.*

---

## §1 — Current State Block

```yaml
as_of: 2026-06-02
phase: PLANNING (square one — re-author rules + briefs before any implementation)
last_session: BUILD-PROGRAM-OPEN (this session) — charter + A1 scope analysis + this tracker authored
active_brief: null
blocking_item: null
immediate_next_actions:
  - Native confirms: (a) agentic-system name (§0); (b) what "A0" denotes (§3 note)
  - Native delivers the full plan + "all new rules" (program is native-led; Cowork drafts)
  - Begin Nirīkṣaka pass + brief re-author starting at A0/A1 (per native go-ahead)
governing_docs_authored_this_session:
  - BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md
  - FACT_ENGINE_A1_SCOPE_ANALYSIS_v1_0.md
  - BUILD_PROGRAM_TRACKER_v1_0.md (this file)
completed_units: 0 (re-author→implement→deploy→verify all-green)
total_units: 5 workflow + ~24 assets (A0–A22 + 6 META) + 1 swarm workstream
```

---

## §2 — Governing rules (the "new rules"; native-seeded, to be extended)

| # | Rule | Source |
|---|---|---|
| R1 | **LEL stays fully isolated** from any deterministic data we generate — never fitted to engine output. | Native, 2026-06-02 |
| R2 | **PyJHora is the source of truth by construction.** No JH-parity oracle anywhere; no pyswisseph cross-check; verification = internal consistency only. | Handoff 2026-06-01 §2 |
| R3 | **Reuse what is built.** A15–A22 + META exist (built-not-wired); cleanse/re-author briefs, do not green-field rebuild. | Native, 2026-06-02 |
| R4 | **A1 output contract must be an enumerated superset of v8.0** (every v8.0 domain + added PyJHora depth, × 5 ayanamshas, each gated). v8.0 = coverage checklist, not value oracle. | A1 scope analysis |
| R5 | **One domain, one unit.** No asset bolts another asset's domain on as a supplement. | Charter §F |
| R6 | **Cowork plans; Antigravity executes.** Deploy / prod-DB / merges are human-gated. | Standing |
| R7 | **No Anthropic models in any production path.** | Standing |
| *(native to add more as the plan is delivered)* | | |

---

## §3 — Lifecycle gate board (program-level)

| Gate | Meaning | Status |
|---|---|---|
| **G-RULES** | All-new rules finalized (§2 complete) | 🟡 in progress (native delivering plan) |
| **G-NAME** | Agentic system named (§0) | ⬜ pending native |
| **G-AUDIT** | Nirīkṣaka first pass — current-state of every unit pinned; naming drift reconciled | ⬜ not started |
| **G-AUTHOR** | All briefs cleansed + re-authored to the new rules (per-unit contract populated) | ⬜ not started |
| **G-IMPL** | All units implemented to contract | ⬜ not started |
| **G-DEPLOY** | All units deployed + verified live (Pratiṣṭhā) | ⬜ not started |
| **G-VERIFY** | Runtime gate green for the native build (Drashta · Pramāṇa · Sambandha · Darpaṇa) | ⬜ not started |

> **"A0" note (open):** searches find the asset numbering starts at **A1** (A1 = engine); there is
> no A0 in the DAG. The native references "A0–A22." Provisional reading: **A0 = the shared,
> build-once foundation** the engine depends on (raw ephemeris Parquet + L0 classical-text vector
> index, per FACT_ENGINE brief §1.1). Confirm what A0 should denote before G-AUTHOR.

---

## §4 — Workflow units (the build experience)

Lifecycle per unit: Re-author brief → Implement → Deploy → Verify.

| Unit | Surface | Re-author | Implement (current baseline) | Deploy | Verify | Notes |
|---|---|---|---|---|---|---|
| **W0** | Dashboard / roster · "New Client" entry | ⬜ | 🟢 exists | ⬜ | ⬜ | roster + health dots live |
| **W1** | New-Client + birth-data form | ⬜ | 🟡 exists; ayanamsha selection missing; preferred_name/tz migration history | ⬜ | ⬜ | `/clients/new` → `POST /api/clients` |
| **W2** | Save action (chart persists, resumable) | ⬜ | 🟢 exists | ⬜ | ⬜ | seeds pyramid_layers |
| **W3** | Build action + cockpit (live DAG progress) | ⬜ | 🔴 cockpit is a chat reading global GCS state, not per-chart live DAG | ⬜ | ⬜ | biggest UX gap vs goal; build-task 401 open |
| **W4** | Consume entry (chat on built chart) | ⬜ | 🟢 exists (full synthesis pipeline) | ⬜ | ⬜ | separate, working surface |

---

## §5 — Asset units (A0–A22 + META)

> Implement column = current baseline; **Nirīkṣaka G-AUDIT pins the authoritative status** (some
> reports conflict, e.g. panchanga/chart_facts wired-vs-stub). Codenames for A15–A22 differ between
> migration 158 and the 140–153 writers — reconcile in G-AUDIT.

### L1 — facts
| Asset | Name | Re-author | Implement | Deploy | Verify | Notes |
|---|---|---|---|---|---|---|
| **A0** | Shared foundation (ephemeris + L0 index) | ⬜ | 🟡 ephemeris + classical index exist | ⬜ | ⬜ | scope pending (§3 note) |
| **A1** | Engine (PyJHora compute) | ⬜ | 🔴 ~6 of ~25 domains; depth missing | ⬜ | ⬜ | **foundation; primary fix**; contract = superset of v8.0 |
| **A2** | Forensic render | ⬜ | 🔴 ~38% of v8.0; starved by A1 | ⬜ | ⬜ | un-stub after A1 enriched |
| **A3** | Chart facts | ⬜ | 🟡 conflicting (stub vs populated) | ⬜ | ⬜ | confirm in G-AUDIT |
| **A4** | Panchanga | ⬜ | 🟡 conflicting (4C shipped vs writer stub) | ⬜ | ⬜ | confirm in G-AUDIT |
| **A5** | Sensitive points | ⬜ | 🔴 stub | ⬜ | ⬜ | |
| **A6** | Vargas (D2–D60) | ⬜ | 🟢 wired (D1 off-by-one fixed) | ⬜ | ⬜ | |
| **A7** | Dashas | ⬜ | 🟢 wired | ⬜ | ⬜ | PyJHora/JH dates canonical (R1/R2) |
| **A8** | T1 structural (shadbala/ashtakavarga) | ⬜ | 🟢 wired | ⬜ | ⬜ | |
| **A9** | Sade Sati | ⬜ | 🔴 stub | ⬜ | ⬜ | |

### L2.5 — synthesis
| Asset | Name | Re-author | Implement | Deploy | Verify | Notes |
|---|---|---|---|---|---|---|
| **A10** | MSR | ⬜ | 🟢 wired | ⬜ | ⬜ | depends on A1 depth being real |
| **A11** | CDLM | ⬜ | 🟢 wired | ⬜ | ⬜ | |
| **A12** | CGM | ⬜ | 🟢 wired | ⬜ | ⬜ | |
| **A13** | RM | ⬜ | 🟢 wired | ⬜ | ⬜ | |
| **A14** | UCN digest | ⬜ | 🟢 wired | ⬜ | ⬜ | |

### L3 — temporal + meta (built, NOT wired into the active DAG)
| Asset | Name (per writer) | Re-author | Implement | Deploy | Verify | Notes |
|---|---|---|---|---|---|---|
| **A15** | time-synchronicity | ⬜ | 🟡 built, not wired | ⬜ | ⬜ | mig 145 |
| **A16** | phase-locked anchors | ⬜ | 🟡 built, not wired | ⬜ | ⬜ | mig 146 |
| **A17** | sarvatobhadra chakra | ⬜ | 🟡 built, not wired | ⬜ | ⬜ | mig 140–141 (name drift vs 158) |
| **A18** | vedha (extended) | ⬜ | 🟡 built, not wired | ⬜ | ⬜ | mig 144 |
| **A19** | bhrigu bindu transits | ⬜ | 🟡 built, not wired | ⬜ | ⬜ | mig 142 |
| **A20** | tajik varsha year-lords | ⬜ | 🟡 built, not wired | ⬜ | ⬜ | mig 148 |
| **A21** | graha aspects lifetime | ⬜ | 🟡 built, not wired | ⬜ | ⬜ | mig 143 (name drift vs 158) |
| **A22** | varsha digest | ⬜ | 🟡 built, not wired | ⬜ | ⬜ | mig 147 |
| **META_α** | chart lattice | ⬜ | 🟡 built, not wired | ⬜ | ⬜ | mig 152 |
| **META_β** | pattern catalog | ⬜ | 🟡 built, not wired | ⬜ | ⬜ | mig 153 |
| **META_γ** | divergence ledger | ⬜ | 🟡 built, not wired | ⬜ | ⬜ | mig 153 |
| **META_δ** | negative-space map | ⬜ | 🟡 built, not wired | ⬜ | ⬜ | mig 153 |
| **META_ε** | derivation graph | ⬜ | 🟡 built, not wired | ⬜ | ⬜ | mig 153 |
| **META_ζ** | unified-lattice view | ⬜ | 🟡 built (SQL view), not wired | ⬜ | ⬜ | mig 151 |
| **BRIDGE** | vedha-anchor interactions | ⬜ | 🟡 built, not wired | ⬜ | ⬜ | mig 150 |

---

## §6 — Swarm + orchestrator workstream

| Role | Charter ref | Status | Notes |
|---|---|---|---|
| Asset Contract Registry | §F | ⬜ | populated by Nirīkṣaka G-AUDIT |
| Sūtradhāra (orchestrator / Conductor enhance) | §E.3 | 🟡 base exists (Conductor) | add watchdog, CI gate, contract-awareness |
| Nirīkṣaka (current-state auditor) | §E.1 | ⬜ NEW | first pass = the asset review |
| Racayitā (gap author) | §E.2 | ⬜ NEW | drafts re-authored briefs |
| Śilpī builders | §E.4 | 🟢 exists (Conductor sub-agents) | |
| Review Swarm ×5 | §E.5 | ⬜ NEW | contract·layer·schema·tests·security |
| Pratiṣṭhā (deploy verifier) | §E.6 | ⬜ NEW | deploy gate |
| Drashta / Pramāṇa | §E.7/§E.8 | 🟢 exists (Pariksha) | rename JH-parity Cat 7 → FORENSIC-consistency |
| Sambandha (dependency-completeness) | §E.9 | ⬜ NEW | |
| Darpaṇa (render-coverage) | §E.10 | ⬜ NEW | |
| Praharī (watchdog) / Smṛti (state) | §E.11/§E.12 | ⬜ NEW | |

---

## §7 — Recently completed

| Item | Date | Session | Notes |
|---|---|---|---|
| Build-guarantor swarm charter authored + wired into CLAUDE.md §C/§D | 2026-06-02 | BUILD-PROGRAM-OPEN | v2 topology; 12 roles + Gate 0 |
| A1 fact-engine brief scope analysis | 2026-06-02 | BUILD-PROGRAM-OPEN | spine OK; scope under-specified; verification stale |
| A15–A22 + META confirmed built-not-wired | 2026-06-02 | BUILD-PROGRAM-OPEN | writers + tables + tests exist (mig 140–153) |
| This tracker authored | 2026-06-02 | BUILD-PROGRAM-OPEN | GANGA-style living board |

---

## §8 — Open decisions (require native input)

| Decision | Question | Status |
|---|---|---|
| Agentic-system name | §0 — Vishvakarman / Sthapati / Sākṣī / other? | PENDING |
| "A0" definition | §3 note — shared foundation, or rename, or off-by-one? | PENDING |
| Full plan + remaining rules | Native to deliver the complete plan + any further governing rules | PENDING |
| Start point | Confirm we begin Nirīkṣaka + re-author at A0/A1 | PENDING |

---

*Update at every session close. §1 current-state block first. Append to §7. Roll lifecycle status in §4–§6.*
