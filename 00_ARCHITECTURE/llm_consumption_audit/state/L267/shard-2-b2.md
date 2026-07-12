# Lane 2 shard-2-b2 — Group B (Buddhi & Svabhava): B3/B4/B5/B6

Worker: Lane 2 evidence-sufficiency (P-12 evidence-plan-then-acquire). Deployed MCP connector (read-only).
Charter §7.3 4-point scale. Charts: `482012f1` (Abhisek), `1c826d5a` (Abhinandan). 16 instances (4 Q × 2 variants × 2 charts).
(Independent second pass; corroborates the prior shard-2-b2 findings — same trim_seen + governance gaps reached independently.)

## Method note
Both charts share ONE tool/governance architecture; sufficiency verdicts are driven by that architecture, not chart content. I deep-probed `482012f1` and confirmed `1c826d5a` parity on the load-bearing surfaces (domain engine, bhava→domain map, empty temporal_windows). Content differs (education verdict 482=mixed/0.9 vs 1c8=contested/-1.7; bhava5 482=convergent_moderate vs 1c8=contested/-1.6) but the reachability/governance verdict is identical per (question×variant).

---

## Cross-cutting findings (reused across the group)

- **F-A (class 1 + 9) — no buddhi/character/svabhava/fear DOMAIN in `judgment_query`.** Domains FIXED to `marriage/career/wealth/health/progeny/education/spirituality` (proven: `judgment_query domain=character` → `content.error: "requires either domain (…7…) or bhava"`). Entire Group B factor space has NO governed verdict path; executor proxies/decomposes every question (class 9).
- **F-B (class 1 + 9) — the `bhava` escape hatch collapses the psychological facet.** `bhava=5`→"progeny/children" (NOT buddhi); `bhava=1`→"health/vitality" (NOT character/self); `bhava=8`→domain `null` generic; `bhava=12`→`null` generic; `bhava=9`→"spirituality/dharma"; `bhava=4`→"education". Confirmed both charts.
- **F-C (class 6) — `get_domain_reading domain=character` is an ID-wall.** `question_lenses` = 7314 ranked signals as `{signal_id,salience,class}` (no text); `signal_id_refs` = 7290 total capped to 200 bare UUIDs; `top_signals: []`; `token_safety_note: "Bounded to 3 lenses × 20 signals"`. No synthesis text; must chain to `get_signals`. `drill_next` = `marsys://tool/L2/query_signals` — tool NOT in exposed 130-list (broken drill pointer).
- **F-D (class 6 — narration integrity) — `graha_portrait` narration truncated mid-clause.** Mercury: `"…a consistent read across D…[truncated for budget]"`; `trim_report` 11→1. Structured dossier (8/8 completeness receipt, grounding_score 1) is present and good; only human narration severed.
- **F-E (class 4 + 3) — `get_temporal_windows` EMPTY SHELL (R-45).** `activation_count:0` both charts, default AND wide 2010–2040. Yet `kala_life_arc_get` reports `high_convergence_count:901` for the Jupiter parva alone → convergence data EXISTS but dedicated tool serves 0 (class 3 inconsistency).
- **F-F (class 7 — DROWNED; primarily Lane 6) — orientation top-K trivia + UNATTRIBUTED wall.** `entity_profiles[0]=UNATTRIBUTED` (299 signals); `top_signals[0]=graha_yoga_karaka_flag:is_yoga_karaka=false` ranked #1. Hits every **broad** variant's whole-chart-read. (R-44/R-37.)
- **F-G (class 1 — UNREACHABLE-BY-NONEXISTENCE) — psychological constructs unmodeled.** "Blind spots"/"psychological knots"/"fears" not computed; only structural proxies (afflicted grahas, 8th/12th occupancy, Moon/Saturn condition, doshas). Taxonomy→life-language translation 100% executor-side (class 9).
- **trim_seen: TRUE** — `graha_portrait` (text suppressed → structuredContent; trim_report), `get_domain_reading` (signal_id_refs_capped, token_safety_note), `judgment_query` (`[budget-capped … per R5.1 C1]`).

Surfaces that DID deliver: `graha_portrait` (structured dossier resolves), `get_signals domain=character` (real `signal_summary_text`/`citation_human`), `judgment_query domain=education/spirituality` (deterministic checklist + receipt), `get_dashas` (rich per-lord context), `kala_life_arc_get` (parvas = maturation timeline), `get_projections` (probabilistic future windows + falsifiability).

---

## B3 — intelligence character  → SUFFICIENT-WITH-GAPS (both variants, both charts)
Plan: Mercury dossier → bhava=5 → domain=education proxy → character signals → orientation(broad).
Acquired: Mercury weakest_graha, D1/D9/D10/D60 all neutral (narration truncated F-D); bhava=5 hijacked to progeny (F-B); education mixed/0.9 (482), contested/-1.7 (1c8); character reading ID-wall (F-C). Composable but buddhi ungoverned.
class9: chose education as intelligence proxy; discarded bhava=5 progeny-hijack; hand-ranked 7290 untexted character signals.

## B4 — moral fiber + blind spots  → SUFFICIENT-WITH-GAPS (both variants, both charts)
Plan: bhava=9/spirituality → Jupiter+Sun dossiers → doshas/Rahu/12th → orientation(broad).
Acquired: spirituality convergent_strong/5.7 (482) governs moral-fiber well; dosha_count=22; "blind spots" no governed surface (F-G) → self-assembled from afflictions.
class9: equated moral-fiber = dharma/9th verdict; constructed "blind spots" from ungoverned dosha/affliction selection.

## B5 — fears / psychological knots  → INSUFFICIENT (both variants, both charts)
Plan: bhava=8, bhava=12 → Moon+Saturn+Rahu dossiers → Moon-affliction signals.
Acquired: bhava=8 domain `null` generic (mixed/-0.8), bhava=12 `null` generic (convergent_moderate/2.2); no psychological framing (F-A,F-G). Only raw structural placements retrievable; fear/knot un-modeled + un-governed → acharya-grade read forces fabricated fear-taxonomy → generic astrology fallback (§7.3 INSUFFICIENT).
class9: would invent fear taxonomy, pick 8th vs 12th vs Moon vs Saturn as "seat of fear", translate dignity/avastha→knot language with zero governance.

## B6 — maturation arc  → SUFFICIENT-WITH-GAPS (both variants, both charts)
Plan: kala_life_arc_get → get_dashas → get_projections/get_temporal_windows → classical graha-maturation-years (sought).
Acquired: life_arc EXCELLENT (Jupiter parva 1984-91 "consolidating: expansion/wisdom", 901 windows, narrative); dashas full spine (Mercury MD 2010-27); projections w/ falsifiability. BUT temporal_windows EMPTY (F-E); graha-maturation-years unmodeled. Narrow (buddhi-specific maturation) leans harder on ungoverned proxy than broad.
class9: equated maturation = dasha-parva progression; re-projected life-domain themes onto buddhi axis (narrow); substituted life_arc for dead temporal_windows (undocumented).

---
*End shard-2-b2. 16/16 graded. Anchors R-44/R-45/R-37 rediscovered + new class-1/9 governance gaps for the whole Buddhi-Svabhava factor space.*
