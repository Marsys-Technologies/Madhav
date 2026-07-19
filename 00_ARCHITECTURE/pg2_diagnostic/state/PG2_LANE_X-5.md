---
lane: X-5
wave: PG-2
status: complete
resolves: OT-11
implementer_model: opus (high reasoning effort)
posture: READ-ONLY on product source; diagnostic READ probes (SQL, schema) only
worktree: /Users/Dev/Vibe-Coding/Apps/Madhav-pg2-X-5 (branch pg2/X-5) — never left
governance: PC-8 (do NOT choose; cost both options as a native-level design decision)
prior_work: PG1-D3-0001, PG1-D3-0002, PG1-D3-0003, PG1-D3-0004
---

# PG-2 Lane X-5 — OT-11 Ledger Reconciliation Decision Memo

**Charge:** establish FACTS about the two disjoint prediction ledgers
(`mimamsa_predictions` vs `mcp_predictions`), cost both reconciliation options
(merge vs document-the-split), and — per **PC-8** — make **no choice**; the
canonical-ledger ruling is reserved for the native.

**Headline:** OT-11's "two ledgers" framing is a floor, not the whole picture.
The live landscape is **three prediction-tracking tables** plus the
`phala_anchors` anchor set that `record_outcome` actually resolves against.
`mimamsa_predictions` is the only **populated + referenced** ledger (384 rows);
`mcp_predictions` is **empty** (0 rows); a **third** ledger,
`brahma_prospective_ledger` (5 rows, added D-4a), sits on the same axis. And
**neither** `mimamsa_predictions` nor `mcp_predictions` satisfies §14.3 without a
schema change, and **neither** is what `record_outcome` writes to.

---

## 1. Both schemas, side by side

| Concept (§14.2/§14.3) | `mimamsa_predictions` (17 cols, **384 rows**) | `mcp_predictions` (24 cols, **0 rows**) |
|---|---|---|
| chart_id | `chart_id` **uuid NOT NULL** | `chart_id` **text, nullable** |
| prediction_id | `prediction_id` text (`PH-4-1.*` namespace) | `prediction_id` text (`PPL.CAL.*` / `PPL.MCP.*` namespace) |
| claim text | `outcome_claim` | `prediction_text` |
| domain | `domain` | `domain` |
| **window** | `observation_window` **DATERANGE** (start+end) | `horizon` **TEXT** (single string, no start/end) |
| **stated confidence** | `confidence_band` **NUMRANGE** (probabilistic, Brier-ready) | `confidence` **TEXT** (`high`/`medium`/`low` — Brier-unusable w/o mapping) |
| falsifier | `falsifier_jsonb` (structured) | `falsifier` (text) |
| direction | `magnitude_expected` (partial) | — |
| technique / grounding | `driving_signals` jsonb + `source_pramana_id` (partial) | — |
| base rate (Brier-vs-null) | `base_rate` | — |
| lifecycle / state | `lifecycle_status` (**4-state build machine**: pending/due/confirmed/denied) | `verified` bool + outcome cols (**binary**, no state machine) |
| outcome storage | *(none — via `mimamsa_calibration` + `mi_abhilekha`)* | **co-located**: `outcome_text`, `outcome_notes`, `outcome_recorded_at`, `outcome_key_id`, `outcome_trace_id` |
| provenance | `frozen_bundle_hash`, `bundle_formula_version`, `emitted_at`, `eval_date`, `created_at` | `key_id`, `trace_id`, `caller_context`, `query_hash`, `model_id`, `salience_formula_version`, `ayanamsha_id`, `logged_at`, `predicted_at_iso` |
| migration bookkeeping | — | `migrated_at`, `migrated_to` |
| **§14.3 message_part_id FK** | **ABSENT** (has `source_pramana_id`, a *build* ref, not an utterance FK) | **ABSENT** (has loose `trace_id`/`caller_context`) |
| **§14.3 created_from_channel** | **ABSENT** | **ABSENT** (only loose `caller_context`) |

**Overlap** = the thin conceptual core (chart_id / claim / domain / window /
confidence / falsifier) — but on **different column names AND different SQL
types**. **Divergence** = each table has a whole cluster the other lacks:
`mimamsa_predictions` carries the deterministic-build provenance + probabilistic
typing; `mcp_predictions` carries co-located outcomes + chat provenance + a
migration escape-hatch. **They are not two copies of one ledger — they are two
differently-typed tables that happen to share six concepts.**

---

## 2. Write / read map

### Writers
| Table | Writer(s) | Path | When |
|---|---|---|---|
| `mimamsa_predictions` | `mi_bhavisya.py` (DELETE-then-INSERT, sole populator); `mi_abhilekha.py` (UPDATE `lifecycle_status` from `mimamsa_journal`) | L5 orchestrator build | **Build-time** |
| `mcp_predictions` | `ppl_writer.ts` `logPrediction()`/`recordOutcome()`; `calibration_producer.ts` `recordCalibrationStamp()` | `/api/mcp/writes`, `onfinish_writethrough.ts` (via single `amjis_app` cred, per PG1-D3-0004) | **Serve-time (chat)** |

No writer touches both. The split at the write layer is **clean and
subsystem-aligned**: deterministic build orchestrator vs live chat relay.

### Readers / references
- `mimamsa_predictions` → **read by** `mi_pramana.py` (SELECTs it, then INSERTs
  `mimamsa_calibration` keyed by its `prediction_id`) and by the serve-time L5
  tool `query_predictions.ts`. **CONFIRMS PG1-D3-0003** that
  `mimamsa_calibration` references `mimamsa_predictions`.
- **REFINEMENT to PG-1:** `phala_anchors` does **not** reference
  `mimamsa_predictions`. Its only FKs are `bhavishya_id → kala_bhavishya.id`
  and `convergence_id → kala_convergence.convergence_id` (both L3, upstream).
  The dependency runs the **other** direction — `mimamsa_predictions` is
  downstream of the phala/kala anchor layer. PG-1's "phala_anchors references
  mimamsa_predictions" is inexact; the headline (mimamsa_predictions is the
  populated+referenced ledger) stands.
- `mcp_predictions` → read only by its own self-UPDATE (`recordOutcome`) and
  migration tooling. **No downstream analytical consumer, no inbound FK.**

---

## 3. §14.3 field-coverage — **neither table qualifies without a schema change**

§14.3 promotion writes the ledger with: `chart_id`, **source `message_part_id`
(FK to the exact utterance)**, structured claim, window, stated confidence,
technique attribution, **`created_from_channel`**; §14.2 adds `direction` +
`grounding_fact_ids[]`; §14.3 defines an **8-state lifecycle**
(`detected→confirmed→open→window_closed→outcome_recorded`, +`dismissed`/
`lapsed`/`unverifiable`).

| §14.3/§14.2 field | `mimamsa_predictions` | `mcp_predictions` |
|---|---|---|
| chart_id | ✅ | ✅ (text) |
| **source message_part_id FK** | ❌ (`source_pramana_id` = build ref) | ❌ (`trace_id`/`caller_context`, no FK) |
| structured claim | ✅ `outcome_claim` | ✅ `prediction_text` |
| window (start+end) | ✅ `observation_window` daterange | ⚠️ `horizon` text (single string) |
| stated confidence | ✅ `confidence_band` numrange | ⚠️ `confidence` text enum (not Brier-scorable) |
| technique attribution | ⚠️ `driving_signals`/`source_pramana_id` | ❌ |
| **created_from_channel** | ❌ | ⚠️ `caller_context` (loose) |
| direction | ⚠️ `magnitude_expected` | ❌ |
| grounding_fact_ids[] | ⚠️ `driving_signals` | ❌ |
| **8-state lifecycle** | ⚠️ 4-state build machine | ❌ binary `verified` |
| co-located outcome | ❌ (via calibration) | ✅ |

**Decisive common gap:** neither carries the **message_part_id FK**, a
**created_from_channel** column, or the **§14.3 8-state lifecycle**. §14.3's own
named target table `brahma_mimamsa_prediction_ledger` **matches no live table**.

---

## 4. `record_outcome` trace — writes to **neither ledger**

There are **two distinct `record_outcome` tool surfaces**, hitting **two
different tables**, and **mimamsa_predictions is not either of them**:

1. MCP tool **`record_outcome`** (`platform-mcp/.../mimamsa_outcome.ts`) →
   sidecar `/api/compute/mimamsa/record_outcome` (`brahmagyan/mimamsa/outcome.py`)
   → **UPDATE `phala_anchors`** (`prediction_state`, `outcome_note`,
   `outcome_recorded_at`) then `update_calibration()` → **`mimamsa_calibration`**.
2. P1 alias **`mimamsa_outcome_record`** → `callPlatformPrim('record_outcome')`
   → `/api/mcp/writes/record_outcome` → `ppl_writer.recordOutcome()` →
   **UPDATE `mcp_predictions`** (same-row outcome cols).

`mimamsa_predictions`' own lifecycle is transitioned **only** by build-time
`mi_abhilekha.py`, never by any `record_outcome`.

**Additional defect (bears on the trace, not OT-11 core):** the sidecar
`outcome.py` SELECTs/UPDATEs `phala_anchors` columns that **do not exist** in the
live schema — it references `id`, `confidence`, `prediction_state`,
`outcome_note`, `outcome_recorded_at`, `updated_at`, but live `phala_anchors`
has `anchor_id`, `confidence_low`/`confidence_high`, `posterior`, `computed_at`
and none of those outcome columns. The sidecar `record_outcome` would **fail at
runtime** against live `phala_anchors` (schema drift). Flagged for a follow-up
lane; the `update_calibration()` function body was not inspected here.

---

## 5. The landscape is **three** ledgers, not two

| Table | Rows | Writer | Role |
|---|---|---|---|
| `mimamsa_predictions` | **384** | `mi_bhavisya` (build) | Build-time deterministic L5 analytical predictions; referenced by `mimamsa_calibration`; probabilistic-typed |
| `mcp_predictions` | **0** | `ppl_writer` (chat) | Chat-side detector **interim PPL relay** (migration 071); header says **TODO-migrate** to formal substrate |
| `brahma_prospective_ledger` | **5** | `/api/mcp/writes/prospective_ledger_file` | **D-4a Lane A-4** §11 explicit-filing prospective ledger; matched against LEL events |

Plus `phala_anchors` (384) — the L4 anchor set the sidecar `record_outcome`
resolves against. **The "which ledger is canonical" decision is not binary.**

---

## 6. BOTH OPTIONS, COSTED — *(no choice made; PC-8 reserves it for the native)*

### Option A — merge into one canonical ledger
**Schema work:**
- Unify incompatible types: `chart_id` text→uuid (backfill + validate);
  `horizon` text → daterange (parse/normalize); `confidence` text-enum → numeric
  (so chat-captured rows are Brier-scorable at all).
- **Add the §14.3 columns neither has:** `message_part_id` FK, `created_from_channel`,
  the 8-state lifecycle enum.
- Reconcile **two disjoint id namespaces** (`PH-4-1.*` vs `PPL.*`).
- For a *truly* single ledger, also fold in `brahma_prospective_ledger` (5 rows)
  and reconcile `phala_anchors` as `record_outcome`'s real target — i.e. the
  merge surface is **3–4 tables, not 2**.

**Code rewrites:** `mi_bhavisya` / `mi_abhilekha` / `mi_pramana`,
`mimamsa_calibration.prediction_id` linkage, `query_predictions.ts`,
`ppl_writer.ts`, `calibration_producer.ts`, **both** `record_outcome` surfaces,
`assetClearSpec` count_sql.

**Migration risk:** concentrated on `mimamsa_predictions` — the **only**
populated + referenced ledger (384 rows) and the single thing L5 STRUCTURAL-mode
calibration depends on. `mcp_predictions` data-migration is **trivial** (0 rows)
but its **writer** must be repointed. **What breaks if done wrong:** the
`mimamsa_calibration` FK, the `mi_pramana` build step, the cockpit count, and the
§7.4 NO-LEAKAGE role that must name one physical table.

### Option B — keep both/three, document the split
**Schema/migration risk:** none.

**Ongoing cost:** permanent reader confusion. A caller invoking `record_outcome`
hits `phala_anchors` + `mimamsa_calibration`; `mimamsa_outcome_record` hits
`mcp_predictions`; **neither** hits `mimamsa_predictions`. §7.4's
`role_ledger_write` still cannot name one physical table.

**Documentation needed:** a ledger-map declaring authority —
`mimamsa_predictions` = build-time deterministic analytical predictions
(referenced by calibration); `mcp_predictions` = chat-side interim PPL relay
(0 rows, TODO-migrate); `brahma_prospective_ledger` = D-4a §11 explicit-filing
prospective ledger; `phala_anchors` = L4 anchors `record_outcome` resolves
against — **plus** a `record_outcome` tool-disambiguation note.

**Is the split semantically justified?** *(stated as fact, not as a recommendation)*
**Partially yes.** Build-time **analytical** predictions vs conversationally
**surfaced live** predictions IS a principled provenance distinction the
architecture's own **§14.1** endorses ("the conversation surface is the only
place [outcome] data can come from" — the chat channel is the *intended*
outcome-data front door). **But** the as-built three-table state tangles that one
clean axis with **historical interim scaffolds**: `mcp_predictions` predates §14
(migration 071, self-described interim relay), and `brahma_prospective_ledger` is
a **third** later attempt on the same axis. So: the distinction is real; the
current implementation is not a clean expression of it.

### Does either table alone satisfy §14 without a schema change?
**No, for both.** §14.3 mandates **message_part_id-FK utterance provenance +
created_from_channel + the 8-state lifecycle**, which neither has.
`mimamsa_predictions` is closest on the **calibration/probabilistic** side
(numrange confidence, base_rate, calibration FK) but lacks utterance provenance
and runs a 4-state build machine. `mcp_predictions` is closest on
**conversational capture** (co-located outcomes, caller_context) but its text
confidence is Brier-unusable, and it lacks window start/end and technique
attribution.

---

## 7. Explicit non-decision (PC-8)

This memo makes **no recommendation** on which ledger to keep. The canonical-
ledger ruling — and the associated §7.4 `role_ledger_write` target and §14.3
lifecycle-migration scope — are **reserved as a native-level design decision**.
The facts above are assembled so that decision can be made; they do not make it.

---

## 8. Corrections / refinements to PG-1 (for Z-2 reconciliation)
- **Confirmed:** PG1-D3-0003 (two disjoint ledgers; `mimamsa_predictions` is the
  populated+referenced one) and that `mimamsa_calibration` references it.
- **Refined:** PG1-D3-0003's claim that **`phala_anchors` references
  `mimamsa_predictions`** is inexact — `phala_anchors` FKs point to
  `kala_bhavishya`/`kala_convergence`; the dependency runs the other way.
- **Extended:** the landscape is **three** ledgers (add `brahma_prospective_ledger`),
  and `record_outcome` writes to **neither** named ledger (it targets
  `phala_anchors`+`mimamsa_calibration` or `mcp_predictions` depending on which
  of two same-named tool surfaces is called).
- **New defect surfaced:** sidecar `outcome.py` `record_outcome` references
  `phala_anchors` columns absent from the live schema (runtime-breaking drift).

*Findings: `00_ARCHITECTURE/pg2_diagnostic/deliverables/pg2_findings_X-5.jsonl`
(PG2-X5-0001 … 0007).*
