---
artifact: CLAUDECODE_BRIEF_L3_KA_JIVANA_PARVA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L3_KA_JIVANA_PARVA
brief_for: ka_jivana_parva — Jīvana-parva / THE DAŚĀ MACRO-NARRATIVE (L3 Kāla; QT-5, life-arc as OUTPUT) [NEW]
parent_plan: 00_ARCHITECTURE/L3_KALA_CAMPAIGN_PLAN_v1_0.md (currently v0.10 DRAFT)
plan_refs: [§5.11.4-L (the daśā macro-narrative — life-arc as OUTPUT) + I-12, QT-5 ("what are the major chapters of my next N years?"), §5.6 Pillar-1 (daśā as the from-within engine), §5.7.1 (the daśā plane = WHAT THEME is live, over years)]
version: 1.0
status: AUTHORED — ready for the autonomous swarm
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
executor: agentic swarm (Conductor-driven) / Claude Code in Antigravity — commands embedded
authored_by: Cowork 2026-06-21
swarm_coordination:
  wave: K6
  blocked_by: [ka_dasha_kala, ka_sangam, ka_kala_darshana]   # macro daśā structure + the windows that populate the chapters
  blocks: []
  may_touch:
    - platform/python-sidecar/services/ka_jivana_parva/**             # NEW
    - platform/python-sidecar/pipeline/orchestrator/writers/ka_jivana_parva.py  # thin artifact (the chapters)
    - platform/supabase/migrations/<next>_kala_jivana_parva.sql       # NEW table (the life-arc chapters)
    - platform/scripts/seed/asset_registry_seed.ts                    # register ka_jivana_parva (artifact-kind)
  parallel_safe_with: [ka_tulana, ka_bhavishya_lekha]   # all K6 derived products; disjoint
---

# CLAUDECODE BRIEF — ka_jivana_parva (The Daśā Macro-Narrative) [NEW]

## §0 — What this asset IS
`ka_jivana_parva` (Jīvana-parva, "the chapters/epochs of life") answers **QT-5 (life-arc/macro)**:
*"what are the major chapters of my next N years?"* It zooms OUT from individual windows to the
macro-structure: the chart's coming years organized into CHAPTERS (e.g. a building phase, a harvest
window, a consolidation), driven by the daśā macro-structure and annotated with the consequential windows
that fall inside each. It makes **daśā an OUTPUT product, not just a search input** (plan §5.11.4-L): the
daśā plane tells you WHAT THEME is live over years (plan §5.7.1), and this surfaces that theme as a
readable life-arc.

## §1 — Why it matters / strategic role
- **It gives the client the STRATEGIC frame the tactical windows sit inside (plan §5.11.4-L).** Individual
  opportune/danger windows are tactical; the macro-narrative is the map that says which SEASON of life
  the native is in — so a window's meaning is understood in context ("this opportune window lands in your
  harvest chapter").
- **It is the natural OUTPUT of the daśā engine.** `ka_dasha_kala` was built as a search PRIOR; this is
  where the same daśā structure becomes a first-class narrative product — the §5.6 Pillar-1 payoff.
- **It frames the catalog + prioritization.** The chapters give `ka_kala_darshana`'s discoveries and
  `ka_tulana`'s rankings a temporal home ("the most consequential opening of your building chapter").

## §2 — VERIFIED ground truth (code-checked 2026-06-21)
- **The daśā macro-structure EXISTS** — `ganita_dashas` MD (level 1) intervals per `dasha_system` give the
  coarse epochs; `ka_dasha_kala` already walks them. The Mahādaśā sequence (and its lords' significations,
  from L1/L2) IS the chapter spine.
- **The window inputs are scored** — `ka_sangam` (opportune) + `ka_vighnakara` (danger) +
  `ka_kala_darshana` (the lifetime discoveries) provide the consequential events to annotate each chapter.
- **The native's chart-bound lifetime is finite** (plan §5.10) → the chapters are a PRECOMPUTABLE artifact
  (computed once, served instantly).

## §3 — The build (chapters from the macro-structure + annotation)
**3.1 — Derive the chapters.** Segment the horizon (birth → ~lifespan+margin) into chapters keyed on the
Mahādaśā boundaries (level-1 `ganita_dashas`), optionally refined by major AD transitions where an MD is
long. Each chapter = {start, end, ruling MD lord(s), the lord's significations → a THEME label}. The theme
(building / harvest / consolidation / challenge / transition) is derived from the MD lord's nature +
dignity + the houses it rules FOR THIS NATIVE (read from L1/L2 — never a generic lord-meaning).

**3.2 — Annotate each chapter with its consequential windows.** For each chapter, attach: the top
`ka_sangam` opportune windows, the top `ka_vighnakara` danger windows, and any `ka_kala_darshana`
lifetime-discoveries that fall inside — so a chapter reads as "this season's theme + its key moments."

**3.3 — The chapter character.** Per chapter, compute a coarse character summary: net favorability
(aggregate of its windows, signed), the dominant domains active (from the windows' `domains_affected`),
and the single most consequential moment. This is the "what is this chapter ABOUT" line the LLM narrates.

**3.4 — Cross-daśā chapter view (optional, flag).** Because L3 has multiple daśā systems (`ka_dasha_kala`),
a richer view overlays the Vimśottarī chapters with Yoginī/Chara epochs to show where systems AGREE on a
life-phase (a stronger chapter signal) vs. diverge. Default: Vimśottarī-primary chapters; cross-daśā as an
enrichment flag.

**3.5 — Storage.** A thin artifact (`kala_jivana_parva`): one row per chapter (chart, ayanamsha, chapter
index, start/end, MD lord, theme, net_favorability, dominant_domains, key_moment_ref). Idempotent
delete-then-insert (plan §N.3). `target_floor` = achieved chapter count (plan §N.4 floors-aspirational).

## §4 — Asset registration (NEW, artifact-kind)
`ka_jivana_parva`: `asset_kind='artifact'`, `layer:'kala'`, sanskrit `'Jīvana-parva'`, english
`'Daśā macro-narrative'`, `target_table:'kala_jivana_parva'`, chart-scoped count_sql,
`depends_on: ['ka_dasha_kala','ka_sangam','ka_kala_darshana']`. Per-chart, ×5 ayanamsha.

## §5 — Acceptance criteria [tagged; prod-verified per plan §9]
1. **[verify: pytest]** chapters tile the horizon with no gaps/overlaps; boundaries align to MD
   transitions in `ganita_dashas` for `482012f1`.
2. **[verify: pytest]** each chapter's THEME is derived from the MD lord's nature + dignity + ruled houses
   FOR THIS NATIVE (read from L1/L2), not a generic lord-meaning (assert it uses chart facts).
3. **[verify: pytest]** chapters are annotated with the correct `ka_sangam`/`ka_vighnakara`/
   `ka_kala_darshana` events that fall within their date range.
4. **[verify: pytest]** net_favorability + dominant_domains + key_moment are computed per chapter.
5. **[verify: anti-drift]** chapter rows reference the daśā intervals + the window refs; no restated L1
   values; no L2 writes.
6. **[verify: psql_prod + curl_prod]** registered artifact-kind; cockpit count = chapter count;
   target_floor = achieved; idempotent rebuild; FORENSIC chart unaffected.
7. **[contract]** the writer never commits/rolls back `ctx.db_conn` (plan §9 / Vimarśaka-RED).

## §6 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/l3-ka-jivana-parva
# the MD chapter spine
psql_prod -c "SELECT dasha_system, lord, start_date, end_date FROM ganita_dashas WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND level=1 AND dasha_system='vimshottari' ORDER BY start_date;"
# tests
cd platform/python-sidecar && pytest -q services/ka_jivana_parva -k "jivana or parva or chapter or macro"
```
> Branch/merge: Madhav human-gated PR (plan memory); Conductor stages, master plan gates.

## §7 — Definition of done
- [ ] Chapters derived from MD boundaries; gap/overlap-free.
- [ ] Per-chapter theme from THIS native's MD lord (chart-grounded, not generic).
- [ ] Chapters annotated with opportune/danger/discovery events.
- [ ] Net favorability + dominant domains + key moment per chapter.
- [ ] Registered artifact-kind; target_floor = achieved; anti-drift clean; PR opened.

---

## §8 — VALUE ADDED BY THIS BRIEF (beyond the baseline)
1. **Gives the client the life-MAP the tactical windows live inside** — without it, L3 answers "when" at
   the moment level but never "what season am I in"; the macro-narrative is the strategic frame that makes
   every individual window meaningful in context.
2. **Promotes daśā from search-input to a first-class PRODUCT** — realizing the §5.6 Pillar-1 payoff: the
   same daśā structure that gates the search now narrates the life-arc, which is arguably the single most
   recognizable thing a Jyotish reading delivers (your daśā periods and what they hold).
3. **Grounds each chapter's theme in THIS native's chart** — by deriving the theme from the actual MD
   lord's dignity + ruled houses (not a generic "Saturn = hardship" cliché), it keeps the macro-narrative
   acharya-grade and specific, not horoscope-column generic.
4. **Frames the catalog + prioritization** — by giving `ka_kala_darshana`'s discoveries and `ka_tulana`'s
   rankings a chapter to belong to, it ties the whole layer's outputs into one coherent life-story instead
   of disconnected windows.
5. **Honors the precompute boundary** — the native's chaptered lifetime is finite + chart-bound, so it is
   a legitimate stored artifact (computed once), consistent with §5.10.
6. **Sets up cross-daśā life-phase agreement** — the optional multi-system chapter overlay surfaces where
   independent daśā traditions concur on a life-phase, a richer signal than any single system gives.

---
*End of CLAUDECODE_BRIEF_L3_KA_JIVANA_PARVA v1.0. The chapters of life — daśā as narrative.*
