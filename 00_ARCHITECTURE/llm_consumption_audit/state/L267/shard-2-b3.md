# Lane 2 — Evidence-Sufficiency Shard 2-b3 (Group C. Vidya / education)

status: COMPLETE
worker: Lane2 EVIDENCE-SUFFICIENCY (P-12 evidence-plan-then-acquire)
questions: C1–C4 × {narrow,broad} × 2 charts = 16 rows
charts: 482=482012f1-710e-4a25-994a-93821f5871aa (Abhisek) · 1c8=1c826d5a-41cb-4450-b4dc-59d440e5f75a (Abhinandan)
channel: DEPLOYED MCP connector (read-only), via curl+SSE
trim_seen: YES (multiple surfaces)

---

## Retrieval reality for the Vidya (education) question family

Established by direct calls on both charts. These facts drive every C-row verdict below.

### A. No education domain exists in the synthesis layer
`get_domain_reading`, `get_signals`, `judgment_query`, `get_temporal_windows`, and `graha_portrait`'s
`orientation_context` ALL collapse to the **same chart-global orientation digest** regardless of the
`domain`/`bhava` argument passed. The `domain` argument is silently ignored (`ranking_basis.domain`
is always `null`; passing `domain:"education"` vs `domain:"vidya"` vs `bhava:4` returns byte-identical
entity_profiles/convergence_domains).
- Domains actually served (convergence_domains): **career, character, relationship, spirituality,
  wealth, health** — **education/vidya is NOT a modeled domain**.
- `top_signals: []` on every call (EMPTY SHELL — class 4; R-40 anchor).
- Lead entity is `UNATTRIBUTED` with **299 signals** (chart 482) — R-44 unattributed/DROWNED anchor
  rediscovered (class 7).
- There is **no `apex_*_assess` / assessor for education** — marriage/career/health/wealth each have
  `apex_marriage_assess`/`assess_career`/etc.; Vidya has none. (Coverage-honesty note.)

### B. Raw fact plane (`query_chart_facts`) — un-budgeted dump, capped, filters ignored
- Returns a declared 130 KB dump but hard-capped at **100 rows** (`returned_count:100`, `offset:0`),
  alphabetical **A-range only** (`abhukta_mula_dosha` → `CUSP_5`). Mercury/Jupiter/house-lords never appear.
- `fact_subject` and `bhava` filters are **silently ignored** (return the same A-range dump); only
  `limit` is honored. `offset` pages but **no `total` is disclosed** → to reach education-relevant
  facts a consumer must blind-page ~hundreds of pages. Class 6 (UNUSABLE FORM) + class 5 (ignored filters).
- Transport note: the full dump transport-truncated at 7 KB under a 40 s client timeout on first fetch;
  needed 90–120 s to complete — an un-budgeted-dump symptom (R-44c/R-30 class).

### C. Depth dossier (`graha_portrait`) — the only real usable education surface, but leaky
Mercury (vidya-karaka) dossier returned 8 sections (position, dignity, functional_nature, strength,
avasthas, yogas, dashas, cgm) — genuinely the Mercury-standard shape. Values retrieved:
- dignity D1 = **neutral, Capricorn, 10th house**; functional_nature = **temporal_malefic** (Aries lagna);
  avastha baladi = **mrit** (dead/weak); digest `weakest_graha = Mercury` (chart 482).
- **`strength: {rows:[], count:59}`** — 0 of 59 strength rows returned, yet `completeness.strength = "✓"`.
  DISHONEST self-description (class 5) — cannot weigh planetary capacity for a vidya read.
- narration **truncated mid-sentence** "for budget" (class 6); `trim_report` itself trimmed **11→1 rows**
  ("full trim_report omitted to fit budget"). `position` shows 1 of `count:9` rows. TRIM everywhere.
- `operative_vargas = [D1, D9, D10, D60]` — **no D24**.

### D. D24 (Chaturvimshamsha / Siddhamsha — the classical education varga) is ABSENT
The only "d24" strings in the fact dump are substrings of hex `fact_id` hashes. The education-specific
varga is **not computed at all** → UNREACHABLE-BY-NONEXISTENCE (class 1, data plane). This is the
classical-canon-exceeds-system delta (charter §2.1): the single most education-diagnostic varga is missing.

### E. Timing is unreachable for education years (kills every time-indexed C-row)
- `get_temporal_windows` → returns the generic orientation digest, not education windows (class 4).
- `get_dashas` AND `ganita_dashas_get` **silently ignore the requested `window`/`start_date`/`end_date`**
  and always serve a today-centered **2021-07-12 → 2031-07-12** decade (echoed in `facets_applied.window`
  even when 1990-2010 / 1995-2015 requested — confirmed on BOTH charts). Education-age years (~1990–2008)
  are categorically UNREACHABLE. Class 1/5. Dasha rows also carry `lord_natal_dignity_d1:null`,
  `lord_natal_shadbala_total:null` (strength not populated in dasha context either).

### F. Chart parity
Chart 1c8 confirmed: same 6 non-education domains, `top_signals:[]`, UNATTRIBUTED present,
`ranking_basis.domain:null`, `weakest_graha:Saturn` (vs Mercury on 482), dasha window ignored
(2021-2031 echoed). All structural findings apply to both charts.

---

## Class-9 UNGOVERNED-JUDGMENT log (fires on EVERY C-row — no education governance exists)
1. **Method/krama choice** — system has no education domain and no Vidya assessor, so I had to *choose*
   the factor space (2/4/5/9 houses + Mercury/Jupiter/Ketu + D24 + education-year dashas). Ungoverned.
2. **Silent decomposition** — "education level + interruptions" self-split into capacity-read vs
   timing-read; "foreign education" into static-indication vs timing. No tool performs this split.
3. **Conflict adjudication** — digest asserts `contradiction_count:0` while the vidya-karaka Mercury is
   simultaneously `weakest_graha` + `temporal_malefic` + `mrit`. I had to decide how to weigh
   "karaka is weakest" against "no contradictions flagged." Ungoverned.
4. **Taxonomy→life-language** — translating "Mercury temporal_malefic + mrit + neutral dignity" into
   an "education level" statement has no governed mapping.
5. **Tool-routing improvisation** — with no education tool, I improvised a surrogate pipeline
   (graha_portrait + query_chart_facts + get_dashas). Ungoverned method choice + the
   graha_portrait→functional_nature hint is itself an undocumented chained call the domain question
   never implied.

## Anchor rediscoveries (audit-of-the-audit)
R-40 (empty `top_signals`), R-44/R-37 (299 UNATTRIBUTED / drowned), R-44c/R-30 (un-budgeted 130 KB dump),
R-32 analog (narration truncated mid-sentence).

---

## Per-question evidence plans + verdicts

**C1 education level + interruptions** — Plan: (1) education domain reading; (2) 4th/2nd/9th house+lord
placement & dignity; (3) Mercury+Jupiter dossiers (capacity); (4) 5th (buddhi) & Ketu (breaks); (5) D24;
(6) dashas over school/college years for interruption timing. Acquired: no education domain (A); Mercury
dossier weak but strength empty (C); D24 absent (D); education-year dashas unreachable (E); house-lords
only via blind paging (B). Verdict **INSUFFICIENT** (both variants, both charts): the "interruptions"
half is time-indexed and categorically unreachable; the "level" half is only a fragment (weak Mercury)
with D24+strength missing.

**C2 field aptitude** — Plan: (1) Mercury/Jupiter/Sun dossiers (dignity, house, nakshatra); (2) 4th/5th
lord sign+nakshatra; (3) Saraswati/Budhaditya yogas; (4) D24 for specialization; (5) planetary strength
ranking. Acquired: graha_portrait gives dignity+house+nakshatra+avastha for each graha (usable base);
BUT strength empty (C), D24 absent (D), yoga catalog matches empty (C). Verdict
**SUFFICIENT-WITH-GAPS** (both variants, both charts): a rough, honestly-hedged aptitude read is
composable from D1 dignity/house/nakshatra/avastha, but strength-ranking, D24 specialization, and
Saraswati/Budhaditya confirmation are sought-not-retrieved gaps. Broad variant carries strictly more gaps.

**C3 competitive-exam timing** — Plan: (1) dashas/antardashas over exam-age years; (2) 5th/9th/10th-lord
dasha periods; (3) Jupiter/Saturn transit windows; (4) upachaya activation. Acquired: dasha window
silently ignored → only 2021-2031 served (E); temporal_windows = orientation digest (E). Verdict
**INSUFFICIENT** (both variants, both charts): the entire relevant timing window is categorically
unreachable (retrieval-plane defect — window param non-functional).

**C4 foreign education** — Plan: (1) 9th house+lord (higher/foreign learning); (2) 12th house+lord
(residence abroad); (3) 4th (home vs away) + dispositor chains; (4) Rahu/Ketu axis; (5) dashas of
9th/12th lords over study years. Acquired: 9th/12th-lord placement only via graha_portrait dignity or
blind fact-paging (no "abroad" classification anywhere); timing unreachable (E); no foreign-education
routing. Verdict **INSUFFICIENT** (both variants, both charts): a partial static indication could be
scraped, but the question inherently needs timing (did/will it happen), which is unreachable, and there
is no foreign-education modeling at all.
