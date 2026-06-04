---
artifact: BRAHMA_COMPLETION_PLAN_v1_0.md
canonical_id: BRAHMA_COMPLETION_PLAN
version: 1.0
status: CURRENT (the forward plan — from "live with thin data" to "fully built + drivable")
project_codename: Brahma
authored_by: Claude (Cowork) 2026-06-04
context: >
  The instrument is LIVE: Build button → Cloud Run Job → L0→L5 cascade → real DB rows; verified dasha
  (Mercury/Saturn/Sun). But the data is a thin first slice, not full depth, and the portal isn't yet
  drivable/visible by the native. This is the plan to finish it.
supersedes_scope_of: DATA_CORRECTNESS_BACKLOG_v1_0 (absorbs it as WS-2 + WS-3)
---

# Brahma — Completion Plan (Pass 3)

## §A — Where we are (honest)
Plumbing + the chain work end-to-end; L1 facts are real and verified. But: (1) every asset generated a
**thin slice**, not its full designed volume; (2) the **portal isn't drivable/visible** by the native
(no open/resume links, cockpit errors, no per-asset visibility); (3) the **Rule Base** is still the genuine
rework, so L2+ signals are ungrounded. Three workstreams close it.

## §B — The thin-data evidence (the volume gap, per asset)
| Asset | Built | Design target | Gap |
|---|---|---|---|
| ganita_positions | 9 | 9 grahas + upagrahas + sensitive points **× 5 ayanamshas** | ~1 ayanamsha, grahas only |
| ganita_dashas | 819 | Vimshottari + Yogini + Chara to **Sukshma (SD) depth** | MD/AD/PD only (3 of 5 levels) |
| bodha_graph | 21 edges | **573 MSR signals** + full CGM/CDLM/RM | a fraction |
| phala_anchors | 9 | lifetime event-anchor set | thin |
| L0 corpus/rules | minimal | full classical canon + extracted rules | scaffold |
Root cause: the **volume-floor gates passed thin data green** instead of flagging amber. WS-2 fixes that.

## §C — WS-1 · Make the portal drivable + visible (UI/UX completeness)
So the native runs and sees it himself.
1. **Dashboard** — each chart card gets **Open** + **Build / Resume** links (currently absent); resume picks up a partial build.
2. **Cockpit** — fix the runtime errors; apply the `build_events` table + wire the **SSE live rail** so the six-layer tower fills in real time.
3. **Asset Inspector** (per BRAHMA_BUILD_UX_SPEC) — click any asset → its **data sample, row counts, provenance, gate status** (amber if below volume floor). This is the native's visibility into all 42 assets.
4. **Brahma lexicon + states** surfaced correctly (green / amber-thin / parked).

## §D — WS-2 · Fully build the assets (data depth — THE priority)
Per-asset: make the writer generate its **complete** data, gated on the **real volume floor** (from the
per-layer design + the FORENSIC coverage benchmark, scaled by ayanamsha count). The mechanism:
- For each asset, declare its **expected full volume** (e.g. positions = N bodies × 5 ayanamshas; dashas to
  SD depth; 573 signals; lifetime anchors).
- The acceptance gate asserts **actual ≥ floor** → green; below → **amber**, re-run the writer to full depth.
- Per layer: **L0** ephemeris (full range × bodies) · reference (all tables) · **classical corpus (real
  editions — the big ingestion)** · ontology · almanac. **L1** all-ayanamsha positions + upagrahas + SD
  dashas + all vargas + full strength. **L2** full 573 signals + complete graph/links/resonance. **L3** full
  temporal fabric. **L4** lifetime anchors + mitigation + muhurta. **L5** LEL 57-event intake + ledger.
- Largely **swarm-driven** (runtime-guardian), but the gates must be **honest** (real volumes, no green-on-thin).

## §E — WS-3 · Rule Base + grounding (the depth soul — native-led)
The genuine rework: extraction method + confidence rubric + quality bar (BG-0-6). Then **re-ground every
signal** against the real rules (the §C cascade) and re-verify L2→L4 upward. This is what turns "populated"
into **acharya-grade**, and it's done *with* the native, not handed to the autonomy.

## §F — Sequence
1. **Immediate quick wins (days):** the L3/L5 one-liner fixes (DCB-001 kala_timeline, DCB-004 life_events) +
   apply `build_events` + the dashboard Open/Resume links + cockpit error fix → **the tower fills and the
   native can drive + see it.** (WS-1 core + the two parked plumbing items.)
2. **The depth build (WS-2):** systematically bring each asset to its real volume floor, layer by layer,
   bottom-up — swarm-driven, honest volume gates, watched via the cockpit + Asset Inspector.
3. **The Rule Base (WS-3, in parallel/after):** native-led; then re-ground the signals.
4. **Red-team IS.8(b)** on the fully-built, grounded instrument.

## §G — How it runs
Native-driven from the portal (form → Build/Resume), guarded by Runtime-Guardian Mode (fix-and-continue on
any UI/workflow/execution/deploy defect), with the **Asset Inspector** giving full visibility and the
**honest volume gates** ensuring "built" means *fully* built, not thinly green.

---

*End of BRAHMA_COMPLETION_PLAN v1.0 — three workstreams (drivable portal · full-depth data · grounded rules)
to take the live-but-thin instrument to fully-built + acharya-grade. Absorbs the data-correctness backlog.*
