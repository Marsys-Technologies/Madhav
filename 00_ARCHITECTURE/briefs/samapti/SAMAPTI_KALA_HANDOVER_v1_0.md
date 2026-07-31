---
artifact: SAMAPTI_KALA_HANDOVER
canonical_id: SAMAPTI_KALA_HANDOVER
version: 1.0
status: CURRENT — handed to ṢAḌ-DARŚANA
created: 2026-07-30
authored_by: SAMĀPTI conductor session (Claude Code, Opus), per DVA Ruling 83
context: >
  Native strategic redirection, 2026-07-30: SAMĀPTI stops auditing/fixing/rebuilding Kāla
  (L3) layer assets while ṢAḌ-DARŚANA is actively rewriting that layer into a six-views
  architecture. Every SAMĀPTI finding that touches Kāla STRUCTURE or Kāla ASSETS is handed
  over here as a precise, self-contained spec rather than built independently — auditing
  code about to be replaced is waste, and a guard/fix landed before the rewrite completes is
  structurally better than one applied after (the new layer inherits it for free; re-auditing
  new code for old sins is strictly worse). See DVA Ruling 83 in SAMAPTI_DVARAPALA_LEDGER.md
  for the full rationale.
delivered_to:
  - 00_ARCHITECTURE/briefs/samapti/SAMAPTI_KALA_HANDOVER_v1_0.md (this campaign's own record)
  - 00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/ (ṢAḌ-DARŚANA's brief directory)
resume_condition: >
  None of this is SAMĀPTI's to resume — it is ṢAḌ-DARŚANA's to absorb into the six-views
  rewrite at whatever point suits that campaign's own sequencing. If any item here is NOT
  absorbed by the time six-views ships, it should re-enter as a fresh finding against the
  settled new code, not be carried forward as an old-code patch.
---

# SAMĀPTI → ṢAḌ-DARŚANA: Kāla-layer findings handover

Everything below was found by SAMĀPTI's audit passes (A7-N8-AUDIT, A8-NAR-TRIAGE reopen,
A6-GOCHARA-DIAG) against the CURRENT (pre-six-views) Kāla code. None of it was fixed by
SAMĀPTI — per the native redirect, Kāla-touching work stops here and is handed over as a
spec, not code. Absorb what's still relevant once the rewrite settles; discard what the new
architecture makes moot.

---

## §1 — Narration/correctness findings (from A8-NAR-TRIAGE's corrected partition, originally scoped to lane B-NAR-KA)

Seven files, each with file path, the specific finding, and what a fix would need to do.
Severity classes (P1/P2/NEW) are SAMĀPTI's own triage bands — re-triage against the new code
rather than importing the label unexamined.

### 1.1 — `platform/python-sidecar/pipeline/orchestrator/writers/ka_bhavishya_lekha.py` — TWO defects, one file

**Defect A (P1-c, lines ~226/232) — obstruction narration silently dropped.** The writer
computes `obstruction_summary` and `net_label` but never narrates them — an obstructed
timing window and a clear one currently read identically to the reader, because the computed
obstruction data never reaches the narration string. Fix shape: thread `obstruction_summary`/
`net_label` into whatever narration-building function assembles the final text for this
writer, with an explicit branch for "obstructed" vs "clear."

**Defect B — stale domain vocabulary, PARKED-HONEST twice already, can fail a live build.**
The file (and likely siblings) use `finance`/`spiritual` where the canonical domain
vocabulary (per whatever the current domain-name source of truth is at rewrite time) is
`wealth`/`spirituality`. This has been found and parked across two prior campaigns without a
fix landing — close it in the rewrite rather than parking a third time. Fix shape: a
find/replace against the canonical vocabulary list, verified against whatever validates
domain names at write time (a CHECK constraint, an enum, a Zod schema — confirm which is
authoritative in the new architecture before fixing).

**Acceptance:** both defects verified independently (the obstruction narration fix needs its
own before/after proof that an obstructed window narrates differently from a clear one; the
vocabulary fix needs a proof that the old strings no longer appear anywhere the writer
outputs, and that whatever gate would have failed on them now passes).

### 1.2 — `platform/python-sidecar/pipeline/orchestrator/writers/ka_kala_darshana.py` — NEW-KA-1

**Finding (line ~168, `mode_label`).** Modes C and D are both mislabelled as "independent
sweep" in the narration. SAMĀPTI's audit found this is NOT cosmetic: in the canonical chart's
own served table, **100% of rows are Mode C**, so this mislabel is live on every served row
today, not an edge case. (A sibling finding at line 180, originally flagged as F27, was
adversarially re-examined and REJECTED — do not import that one; NEW-KA-1 at :168 is the real,
reachable defect that justifies opening this file.) Fix shape: correct the mode→label mapping
so Modes C and D get their own accurate labels, distinct from the true independent-sweep mode.

**Acceptance:** verify against the live served table (or its six-views equivalent) that the
previously-100%-Mode-C-mislabelled population now narrates correctly.

### 1.3 — `platform/python-sidecar/brahmagyan/kala/l3_snapshot.py:519` — P2

Flagged in the N8/narration sweep; SAMĀPTI did not carry a detailed root-cause for this one
beyond the line pointer — re-derive the specific defect against the line at rewrite time
(the surrounding code will have moved/changed under six-views regardless).

### 1.4 — `platform/python-sidecar/brahmagyan/kala/l3_timeline.py:270` — P2

`if "benefic" in pl_nature:` — a substring-containment check on what is presumably a planet-
nature string or list; worth checking whether this correctly handles multi-nature planets
(e.g. a planet with mixed benefic/malefic classification) or whether the containment check
produces a false positive/negative for such cases. Re-derive against the six-views
replacement.

### 1.5 — `platform/python-sidecar/brahmagyan/phala/muhurta.py:355` — P2

Note on ownership: this file physically lives under `brahmagyan/phala/` but was assigned to
the Kāla triage lane (electional-timing logic is conceptually Kāla-domain regardless of its
folder). Flag for re-triage at rewrite time — confirm whether the new six-views architecture
relocates or restructures muhurta logic, and re-derive the specific defect against wherever
it lands.

### 1.6 — `platform/python-sidecar/services/gochara_grammar/primitives.py:788`

`"bindu_count_resolved": False` — a hardcoded/literal boolean in what should presumably be a
computed resolution-status field. Worth checking whether this is a genuine §N.8-class
detector-less field (always False regardless of actual resolution state) or a legitimate
default awaiting a real computation elsewhere. Re-derive against the rewrite.

### 1.7 — `platform/python-sidecar/pipeline/orchestrator/writers/ka_jivana_parva.py` — two seed findings (F8, F19)

**F8 (line ~234).** `_build_parva_narrative` receives a composite string
`f"{md_planet}/{ad_planet}"` but the lookup table (`_PLANET_THEMES`) doesn't have entries for
composite keys, so it always falls back to `['transformation']` regardless of the actual
planet pair — every dasha/antardasha combination currently narrates identically on this
axis. Fix shape: either split the composite before lookup (look up `md_planet` and
`ad_planet` separately and combine their themes) or populate `_PLANET_THEMES` with composite
keys.

**F19 (line ~226).** `ad_dominant = … else dominant_class` — inherits the parent
mahadasha's dominant class instead of computing its own, where the sibling pratyantardasha
(PD) branch at line ~301 correctly returns `None` in the equivalent situation. The
antardasha (AD) branch should likely match the PD branch's behavior (return `None` rather
than inheriting), unless there's a reasoned justification for the asymmetry — worth
confirming intent before fixing.

**Acceptance for both:** verify with real dasha/antardasha combinations that themes now vary
correctly (F8) and that AD-level dominant-class computation is either independently derived
or intentionally documented as inheriting (F19).

---

## §2 — Serving-layer finding (from B-NAR-TS's declared scope, the Kāla-relevant slice only)

### 2.1 — `platform-mcp/src/tools/retrieval/kala_temporal.ts:377`/`:380` — P1-d

Two related bugs in the same function:
- **`:377`** — `active_convergences: convergenceWindows.filter(...)` is scoped to a DATE
  RANGE, not "active today" as the field name implies — a convergence window that covers a
  wide date range but isn't actually active on the query date is still counted.
- **`:380`** — `active_obstructions: darshana?.obstruction_summary` — an empty-array
  truthiness bug: an empty array is truthy in JS, so `darshana?.obstruction_summary` being
  `[]` (no obstructions) may still read as "present" wherever this value's truthiness is
  checked downstream, rather than correctly reading as "no active obstructions."

Fix shape: (a) filter `convergenceWindows` against the actual query date, not just window
membership; (b) check `obstruction_summary.length > 0` (or equivalent) rather than relying on
array truthiness.

**Acceptance:** verify both — a convergence window that covers today's date range but whose
own specific dates don't include today no longer counts as "active"; an empty obstruction
list correctly reads as "no obstructions," not as truthy-present.

---

## §3 — `ka_gochara_sweep` — full root-cause diagnosis, PARKED-BY-DESIGN, not a defect

**This is NOT a bug report — it is a completed diagnosis SAMĀPTI is handing over because the
asset is being restructured, not because anything here needs fixing in the current code.**

Per DVA Ruling 83, SAMĀPTI's own C2-GOCHARA-RUN work on this asset is PARKED-BY-DESIGN: the
canonical chart (`482012f1`) is already 303/303 substeps complete; the two operator charts
(`1c826d5a` at 209/303, `cb73cd3d` at 70/303 as of hand-off) are incomplete for a
resource-budget reason, not a defect, and completing them further is second-order value
against an asset ṢAḌ-DARŚANA is rewriting anyway.

**Full diagnosis (A6-GOCHARA-DIAG, `GOCHARA_PARITY_DIAGNOSIS_v1_0.md`, preserved on branch
`samapti/gochara-parity`):** `ka_gochara_sweep`'s substep plan is `3 event_classes × 101
years = 303 substeps`, each costing ~253-280s of writer wall-clock (measured from real
`build_substep_progress` timestamp deltas) — i.e. ~22h for the full plan, against a
`writer_timeout_seconds = 21600` (6h) budget. One dispatch therefore completes ~76-87
substeps (≈27% of the plan) before eviction — not a hang, not a stall, not a defect in the
writer. The canonical chart reached 303/303 only because it received six sequential resumed
dispatches; the operator charts received far fewer. **If the six-views rewrite changes this
asset's substep granularity, per-substep cost, or timeout budget, this diagnosis may no
longer apply and should be re-derived against the new shape, not assumed to carry over.**

**If ṢAḌ-DARŚANA wants to complete the operator charts under the OLD architecture before the
rewrite lands** (not SAMĀPTI's call to make): the diagnosis includes a full completion
procedure (one BUILD-LOCK-held dispatch at a time, `N_after - N_before >= 40` progress
assertion, `1c826d5a` needs ~3 more dispatches, `cb73cd3d` needs ~4) — see the diagnosis
document's §5 for the exact procedure. SAMĀPTI cancelled its own in-flight dispatch cleanly
(verified: `1c826d5a` at 209/303, no partial/corrupt substep rows) and will not resume it.

---

## §4 — Flagged for awareness, no specific defect found (SUPERSEDED for kala_envelope.ts — see §4-ADDENDUM)

**`platform-mcp/src/lib/kala_envelope.ts`** — a Kāla-domain serving file. SAMĀPTI's N8/
narration sweeps did not surface a specific finding against it, but it is structurally
Kāla-serving and worth a look as part of the six-views transformation's own review — flagging
its existence rather than asserting a defect that wasn't found.

---

## §4-ADDENDUM (NIḤŚEṢA, 2026-07-31) — kala_envelope.ts F-20, a real defect, code withheld

A later SAMĀPTI lane (B-N8-TS-SERVE, DVA Ruling 12, commit `b480d87b`) found a real,
specific defect in this file after §4 above was written — this addendum supersedes §4's
"no specific defect found" for this file only.

**F-20 · `KalaFreshness.stale` — literal `false`, estate-wide, no horizon ever checked.**
`stale` could only be `true` when `params.staleAfter` was supplied to `buildKalaFreshness`
in `kala_envelope.ts`. Grep at the time: **zero of the eight production `kala_views/*.ts`
call sites pass `staleAfter`.** `false` was therefore the only value the field could ever
take in production, while all three provenance fields (`ephemeris_version`,
`sweep_build_date`, `field_hash`) were simultaneously `null` — and
`composeFreshnessSentence` (in `platform-mcp/src/lib/argument_composer.ts`) rendered the
affirmative prose **"Freshness: current."** on every served response, regardless of
whether anything was actually checked. An unparseable `staleAfter` also silently fell
through to `false`. This is the CLAUDE.md §N.8 clean-looking-default shape.

**Prescribed fix (spec only — NOT applied to the file):** change `stale: boolean` to
`stale: boolean | null`. `null` = not determinable, carrying a named reason (mirror the
three-state discipline `KalaCoverageEntry` already uses in the same file: `'computed'` /
`'honest_empty'` / `'not_in_corpus'`). Reserve `false` for a horizon that was actually
declared and genuinely checked. Update `composeFreshnessSentence` to render the third
state as `"Freshness: UNKNOWN — <reason>"`, never as `"current"`. A working reference
implementation (not merged, do not treat as authoritative for the six-views rewrite —
re-derive against the new architecture) exists at commit `b480d87b` in this repo's
history, touching exactly: `kala_envelope.ts`, `kala_envelope.test.ts`,
`argument_composer.ts`'s `composeFreshnessSentence`, and one new test in
`argument_composer.test.ts`. NIḤŚEṢA (2026-07-31) extracted the other three, independent
fixes in that same commit (F-22/F-23/F-24, non-Kāla files) into a separate merged commit
and reverted this file and its coupled hunks back to main's pre-fix state before merging —
per the hard scope boundary, no Kāla-touching code from that commit was merged. See
`SAMAPTI_DVARAPALA_LEDGER.md` Ruling 12 (original finding) and the NIḤŚEṢA close report's
disposition table (PR #909) for the split decision.

**Why this is real, not speculative:** the finding shipped with a can-fail proof (source
reverted to pre-fix semantics, 4 tests observed to go red, then reverted to green) and
passed both a full `platform-mcp` test run and `tsc --noEmit` at the time it was written.

---

## §5 — What this handover does NOT include

- Anything in `platform/python-sidecar/pipeline/orchestrator/writers/ga_*.py`,
  `bo_*.py`, `mi_*.py`, `ph_*.py` — those are Gaṇita/Bodha/Mīmāṃsā/Phala layers, not Kāla,
  and remain SAMĀPTI's own scope (parked separately per Ruling 83's disposition test, not
  handed over here).
- Any code fix, migration, or test — this document is a specification for ṢAḌ-DARŚANA to
  absorb, not a patch to apply. SAMĀPTI performed no write against any file listed above.
- A claim that this list is exhaustive of every Kāla-layer defect that exists — it is
  exhaustive of what SAMĀPTI's specific audit passes (A7-N8-AUDIT, A8-NAR-TRIAGE, A6-GOCHARA-DIAG)
  happened to surface before the redirect, not a general Kāla-layer audit.
