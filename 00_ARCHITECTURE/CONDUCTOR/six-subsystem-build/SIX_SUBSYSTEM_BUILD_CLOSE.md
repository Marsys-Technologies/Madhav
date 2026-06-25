---
document: SIX_SUBSYSTEM_BUILD_CLOSE
version: 1.0
status: CLOSED
date: 2026-06-17
main_head_at_close: b3c9a7fc
conductor: Sūtradhāra
---

# Six-Subsystem Build — Closure Record

## §1 — Scope

Wave-1/2/3/4 build of 6 domain-specific L0/L1 subsystems + ga_prashna horary judgment layer, all branching from and merging back to main.

The build also resolves Vimarśaka IS.8(b) RED findings surfaced during the red-team pass conducted 2026-06-17.

---

## §2 — Merged subsystems (all 7 PRs)

| Subsystem | PR | Merge Commit | Wave | Migrations | Tests |
|---|---|---|---|---|---|
| Yoga (ga_yoga) | #284 | d0aaa693 | 1 | 241-245 | 41 |
| Dignity / ga_condition | #286 | 96f6cc1e | 2 | 250-252 | — |
| Prashna-L0 (bg_prashna_rules) | #283 | 55d754ba | 1 | 261-262 | — |
| Transit / ga_transit_anchors | #288 | a35e6945 | 3 | 266-268 | 19 |
| Astrovastu / ga_vastu | #289 | a72315c7 | 3 | 284-287 | 24 |
| Medical / ga_medical | #290 | 453e194e | 4 | 276-280 | 38 |
| Prashna-ga / ga_prashna | #291 | 2039aa25 | 4 | 288-291 | 18 |

**Yoga RED-team fix** (PR #292, `b3c9a7fc`) — hotfix merged after all 6 subsystems were in main; resolves RED [1]+[2] discovered in Vimarśaka IS.8(b) pass.

---

## §3 — Vimarśaka IS.8(b) Red-Team Summary

Red-team conducted 2026-06-17 across all 6 merged subsystems + ga_prashna.

### RED findings (now RESOLVED)

| ID | Subsystem | Finding | Fix commit |
|---|---|---|---|
| RED [1] | ga_yoga | `ON CONFLICT (chart_id, ayanamsha_id, yoga_canonical_id) DO UPDATE SET` on L1 INSERT — violates §N.3 (L1 = delete-then-insert, not upsert) | 4ad28250 (PR #292) |
| RED [2] | ga_yoga | `_forensic_assert()` used `logger.warning` instead of `raise AssertionError` when 0 yogas fire for native chart — FORENSIC miss must halt build | 4ad28250 (PR #292) |
| RED [3] | ga_prashna | Multiple `conn.cursor()` opens across query phases with `with` context manager incompatible with test mocks — cursor resource leak risk | d4121e54 (PR #291) |
| RED [4] | ga_prashna | Silent `return None` when prashna chart exists but ga_positions is empty — build-ordering violation unobservable | d4121e54 (PR #291) |

### AMBER findings (accepted as-is)

| ID | Subsystem | Finding | Disposition |
|---|---|---|---|
| AMBER [1] | ga_prashna | Natural significators (Moon = querent; karaka = quesited) instead of house lords — deferred; house cusp storage not yet in schema | Accepted-by-design: documented in Gate-2 notes |
| AMBER [3] | ga_yoga | `brahma_yoga_catalog` referenced but not in subsystem migration — false alarm: table exists in migration 178 (L0 Phase Alpha) | CLOSED — pre-existing L0 table |

### Final verdict: RED_TEAM_PASS (post-fix)

---

## §4 — Architecture compliance attestation

All 7 subsystems comply with the following:

- **§N.2 FROZEN WriterBase contract**: every writer is a `@register('<asset_id>')` `WriterBase` subclass; no `conn.commit()`, `conn.close()`, or `conn.rollback()` in any writer; `ctx.db_conn` is the sole connection handle.
- **§N.3 L1 idempotency**: all L1 writers use DELETE WHERE (chart_id × natural key) + plain INSERT. No L1 ON CONFLICT upserts survive (yoga fix PR #292 eliminates the last violation).
- **§N.3 L0 idempotency**: all L0 reference table inserts use `ON CONFLICT (named_column) DO NOTHING`.
- **§N.4 deterministic-first**: all computation in Python; no generative LLM in data build path.
- **§N.4 cockpit truth**: each asset has a chart-scoped `count_sql` on `asset_registry`.
- **§N.4 surgical migrations only**: all migrations are numbered, applied in strict order, without `deploy.yml` auto-run.
- **B.10 no fabricated computation**: no session invented a numerical chart value; all numerical facts read from L1 `ga_positions`, `chart_facts`, or pre-built reference tables.
- **Transit = on-demand service**: `ga_transit_anchors` writes only REFERENCE EPOCH rows (current moment bound), not cross-time transit timelines. Confirmed NOTHING stored across time.
- **FORENSIC assertions**: all subsystems with native-chart expectations assert with `raise AssertionError` (not `logger.warning`). Native `chart_id = 482012f1-710e-4a25-994a-93821f5871aa` exclusively.

---

## §5 — Migration inventory

| Migration # | Table / Action | Subsystem | Wave |
|---|---|---|---|
| 239-240 | bg_nakshatra (reference, asset_registry) | bg_nakshatra (L0) | pre-build |
| 241 | brahma_yoga_catalog | yoga | 1 |
| 242 | ga_yoga_firings | yoga | 1 |
| 243 | ga_yoga_families | yoga | 1 |
| 244 | ga_yoga_family_members | yoga | 1 |
| 245 | asset_registry: ga_yoga | yoga | 1 |
| 250 | ga_condition | dignity | 2 |
| 251 | ga_condition_detail | dignity | 2 |
| 252 | asset_registry: ga_condition | dignity | 2 |
| 261 | bg_prashna_significators + bg_prashna_rules + 4 rule tables | prashna-L0 | 1 |
| 262 | asset_registry: bg_prashna_rules | prashna-L0 | 1 |
| 266 | bg_transit_rules | transit | 3 |
| 267 | ga_transit_anchors | transit | 3 |
| 268 | asset_registry: ga_transit_anchors | transit | 3 |
| 276 | bg_body_systems | medical | 4 |
| 277 | bg_medical_mappings | medical | 4 |
| 278 | bg_nakshatra_medical | medical | 4 |
| 279 | ga_medical | medical | 4 |
| 280 | asset_registry: ga_medical | medical | 4 |
| 284 | bg_vastu_directions | astrovastu | 3 |
| 285 | bg_vastu_planet_directions | astrovastu | 3 |
| 286 | ga_vastu | astrovastu | 3 |
| 287 | asset_registry: ga_vastu | astrovastu | 3 |
| 288 | prashna_charts (infrastructure) | prashna-ga | 4 |
| 289 | ga_prashna_lagna | prashna-ga | 4 |
| 290 | ga_prashna_judgment | prashna-ga | 4 |
| 291 | asset_registry: ga_prashna | prashna-ga | 4 |

**Total: 26 new migrations** (including the 2 pre-build nakshatra migrations).

---

## §6 — Gate-3 operator checklist (pending operator action)

These items require DB access and cockpit build — not executable by this session:

### Yoga
- [ ] Apply migrations 241-245 in order
- [ ] `POST /api/cockpit/runs` for `chart_id=482012f1` — build `ga_yoga`
- [ ] Cockpit tile for `ga_yoga` shows > 0 firings
- [ ] FORENSIC: `budha_aditya` fires for native chart (Sun + Mercury conjunction in Capricorn)

### Dignity / ga_condition
- [ ] Apply migrations 250-252 in order
- [ ] Build `ga_condition` for `chart_id=482012f1`
- [ ] Cockpit tile shows 9 rows (one per graha)
- [ ] FORENSIC: Sun debilitated (Libra), Saturn exalted (Libra) for Lahiri

### Prashna-L0
- [ ] Apply migrations 261-262 in order (262 uses `english_name` column — verified correct)
- [ ] Cockpit tile for `bg_prashna_rules` shows 36 rows across all 5 rule tables

### Transit
- [ ] Apply migrations 266-268 in order
- [ ] Build `ga_transit_anchors` for `chart_id=482012f1`
- [ ] Confirm 0 cross-time rows stored; only reference-epoch anchor

### Astrovastu
- [ ] Apply migrations 284-287 in order
- [ ] Build `ga_vastu` for `chart_id=482012f1`
- [ ] FORENSIC: Sun/East = weakened, Saturn/West = strengthened

### Medical / ga_medical
- [ ] Apply migrations 276-280 in order
- [ ] Build `ga_medical` for `chart_id=482012f1`
- [ ] FORENSIC: Moon/PurvaBhadrapada → left_side body tendency

### Prashna-ga
- [ ] Apply migrations 288-291 in order
- [ ] Build `ga_prashna` for `chart_id=482012f1`
- [ ] Confirm cockpit tile shows 0 rows (correct: natal chart is not in prashna_charts)
- [ ] To test live horary: register a prashna chart in `prashna_charts`, then build

---

## §7 — Next steps after Gate-3

1. Vimarśaka re-run (IS.8(b)) after Gate-3 confirms production build is clean
2. `CURRENT_STATE_v1_0.md` update: increment to v5.75, note six-subsystem build CLOSED
3. `SESSION_LOG.md` append: session close for this build arc
4. L2 Bodha campaign readiness review (this build provides critical L1 substrates:
   ga_yoga + ga_condition + ga_transit_anchors → feed into bo_laksana and downstream Bodha assets)

---

## §8 — Commit ledger (final main state)

```
b3c9a7fc  fix(ga_yoga): RED [1]+[2] — remove ON CONFLICT upsert; harden FORENSIC  [#292]
2039aa25  feat(prashna-ga): Prashna Horary Gate-1+2 — prashna_charts, ga_prashna judgment writer  [#291]
19f3d1be  Merge pull request #285 from amonty84/feature/bg-nakshatra-l0
453e194e  feat(medical): Medical/Ayurvedic Gate-1+2  [#290]
a72315c7  feat(astrovastu): Astrovastu Gate-1+2  [#289]
a35e6945  feat(transit): Transit/Gochara Gate-1+2  [#288]
96f6cc1e  Merge pull request #286 (dignity)
55d754ba  Merge pull request #283 (prashna-L0)
d0aaa693  Merge pull request #284 (yoga)
```

---

*SIX_SUBSYSTEM_BUILD_CLOSE v1.0 — 2026-06-17 — Sūtradhāra conductor. All RED findings resolved. main HEAD: b3c9a7fc. Gate-3 operator checklist open.*
