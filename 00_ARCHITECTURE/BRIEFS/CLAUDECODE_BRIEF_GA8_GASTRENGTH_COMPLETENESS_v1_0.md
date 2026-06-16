---
artifact: CLAUDECODE_BRIEF_GA8_GASTRENGTH_COMPLETENESS_v1_0.md
canonical_id: GA8_GASTRENGTH_COMPLETENESS_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-12
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
governing_decision: L1_L2_RELATIONSHIP_ARCHITECTURE_DECISION_v1_0 (ga_structural = sole enumeration engine)
target_writers: ga_writers/ga_structural_writer.py + ga_writers/ga_strength_writer.py (coordinated pass)
data_plane: ALWAYS prod via Cloud SQL proxy
blocked_by: CLAUDECODE_BRIEF_PRE_GA8_CLOSURE_v1_0 (the 3 deck-clearers run first)
delivery_model: branch + plan-then-execute; surgical migrations; tracker rows; verify against prod
---

# GA8 + ga_strength — L1 Relationship Completeness Amendment v1.0

## §0 — Goal + the shared root cause

Add every legitimately-computable relationship class ga_structural does NOT yet capture, across all
30 vargas × 5 ayanamshas. **All additions are genuine deterministic facts — NOT padding.** Volume
grows as a CONSEQUENCE of completeness, never as a target; floors aspirational.

**Shared root cause to fix once, in both writers:** `CLASSICAL_GRAHAS = 7` (no Rahu/Ketu).
- `ga_structural_writer.py:104` — nodes excluded from ALL relationship enumeration.
- `ga_strength_writer.py:188` — `if name not in NAISARGIKA_BALA: continue` excludes nodes from strength.
Fix coherently: add Rahu (RAH_MEAN) + Ketu (KET_MEAN) everywhere they participate. (Use classical
node treatment: Rahu/Ketu have their OWN special aspects — 5th/7th/9th per many authorities — and act
as co-lords/karakas; apply the node-aspect rules, do not just treat them as ordinary grahas.)

## §1 — TIER 1 (highest value — real gaps)

### T1.1 — Rahu & Ketu in ga_structural relationships (the big one)
Add nodes to: aspects (incl. their special node-aspects), conjunctions, dispositor participation,
avastha/dignity-where-defined, argala participation — across all 30 vargas × 5 ayanamshas. Going
7→9 grahas ~1.7×'s the pairwise relationship layer.

### T1.2 — Kala Sarpa / Kala Amrita structural detection (unlocked by T1.1)
Now that nodes are in the graph, deterministically detect whether ALL 7 classical grahas are hemmed
within the Rahu→Ketu arc (Kala Sarpa) or Ketu→Rahu arc (Kala Amrita), per varga. Emit as a structural
relationship fact (the 12 named KS variants by Rahu's house are LABELLED from bg_dosha_catalog, not
hardcoded). This is impossible without the nodes — it's a real completeness unlock.

### T1.3 — Special points as relationship participants
ga_structural currently only CHECKS that GA5 sensitive points exist (line 532); it never reads them as
relationship endpoints. Read them and enumerate their relationships: Gulika/Mandi (maraka points) +
Arudha Lagna + the sahams as aspect-receivers / aspect-givers / conjunction participants, per varga.
"Gulika conjunct/aspected-by X in D-varga" is classically read and currently absent.

### T1.4 — ga_strength: nodal strength + the stubs
- Add Rahu/Ketu to shadbala / ashtakavarga / bhava-bala (extend `NAISARGIKA_BALA` + remove the
  line-188 skip). Use the classical node-strength treatment (nodes have no naisargika bala in strict
  Parashara — emit explicitly as 0/NA-flagged, NOT silently absent; some schools assign node strength
  — emit those as a documented variant).
- **kala-bala daytime hardcode** (`is_daytime=True`) → compute real day/night from birth time.
- **drik-bala stub** (0.375) → compute from the actual aspect matrix (now available — GA8 computes it).

## §2 — TIER 2 (new relationship CLASSES)

### T2.1 — House-lord relationship matrix (core Parashari)
Enumerate lord-to-lord relationships: which house-lord aspects/conjuncts which other house-lord; where
each house-lord is placed (lord-in-house); lord exchanges. Per varga. This is a DIFFERENT relationship
type than graha-to-graha (it's bhava-lord interplay — the engine of most prediction) and is currently
absent. Compute house-lords per varga from that varga's sign occupancy.

### T2.2 — Bhava-to-bhava / sign-to-sign aspects (Jaimini rāśi-drishti on houses)
Beyond graha aspects: the rāśi-drishti relationships between houses/signs themselves, per varga.

### T2.3 — Karaka inter-relationships (Jaimini chara-karaka web)
Atmakaraka–Amatyakaraka–Darakaraka (and the full 8-karaka set) aspect/conjunction/placement
relationships among themselves, per varga. (Karaka assignments come from GA5/GA7; enumerate their
mutual relationships here.)

## §3 — TIER 3 (finer-grained, still real)

### T3.1 — Graded aspect strength (not just existence)
Emit the partial-aspect strength tier per aspect (Tajik virupa / percentage drishti — e.g. a 3rd/10th
Saturn aspect at 30/60/100% per orb), so the DEGREE of each aspect is a stored value, not just a boolean.
### T3.2 — Graha yuddha (planetary war)
When two non-node grahas are within ~1° in the same sign, emit the yuddha relationship + winner/loser
by longitude, per varga.
### T3.3 — Retrograde-interaction + combustion-as-relationship
Combustion (graha within combustion-orb of Sun) and retrograde-modified aspects emitted as RELATIONAL
rows (X combust-by-Sun; X's aspect modified by retrograde), not just the existing per-graha flags.

## §4 — Hard requirements (carry from the prior GA8 briefs)
- **Disambiguation:** every row fully qualified — varga + sign + ayanamsha + participating bodies +
  position/orb. No unqualified relationship rows. (Nodes tagged RAH_MEAN/KET_MEAN; special points by
  their canonical id.)
- **Label-not-gate:** named patterns (incl. Kala Sarpa, node-yogas) LABELLED from
  bg_yoga_catalog/bg_dosha_catalog; unnamed configs still stored (`uncatalogued` flag).
- **No silent drops:** any missing input (a varga, a sensitive point) logs WARNING / halts — never a
  silent `continue`. Nodes-have-no-naisargika is emitted as an explicit flag, not an omission.
- **Real fact_ids** (the `_fact_id` formula, never mock); two-pass verification on every new row;
  FORENSIC 7/7 guarded to native; per-chart delete-then-insert idempotency.
- **Orchestrator FROZEN contract unchanged.** This is now a MUCH heavier writer — confirm
  `plan_substeps` chunks (per-ayanamsha and/or per-varga) keep each sub-step within limits; keep the
  `executemany()` batch insert + per-ayanamsha fresh connections from PR #274.

## §5 — Volume expectation (honest)
Rahu/Ketu (~1.7× the relationship layer) + special-point participation + house-lord matrix + karaka
web + graded aspects, across 30 vargas × 5 ayanamshas, will push ga_structural from ~54k toward
roughly **~90k–120k rows** (estimate; the executor reports the true count). Set `target_floor` =
achieved count. ga_strength grows modestly (nodes added to its existing categories). Do NOT trim to a
number; do NOT skip any varga or relationship class.

## §6 — Acceptance [verify-against: prod]
- [ ] Rahu/Ketu present in ga_structural aspects + conjunctions + dispositors across all 30 vargas. `[psql_prod]`
- [ ] Kala Sarpa / Kala Amrita structural detection emits (labelled from dosha catalog). `[psql_prod]`
- [ ] Gulika/Mandi/Arudha/sahams appear as relationship participants. `[psql_prod]`
- [ ] House-lord relationship matrix + karaka inter-relationships present per varga. `[psql_prod]`
- [ ] Graded aspect strength, graha yuddha, combustion/retrograde relational rows present. `[psql_prod]`
- [ ] ga_strength: Rahu/Ketu have strength rows (or explicit NA-flag); kala-bala day/night computed; drik-bala from aspect matrix. `[psql_prod]`
- [ ] Every new row fully qualified; no silent drops; FORENSIC 7/7; two-pass true. `[psql_prod + log]`
- [ ] `target_floor` updated; orchestrator unchanged; build completes within step/timeout limits.

## §7 — Out of scope
Dasha-temporal (L3 Kāla); MSR/bo_laksana projection; the retrievability/query layer; ganita_positions
dual-write deprecation. This brief = L1 relationship+strength completeness only, in ga_structural + ga_strength.

---
*End of GA8_GASTRENGTH_COMPLETENESS v1.0. One coordinated pass adding every Tier 1/2/3 relationship
class + fixing the shared 7-graha root cause across ga_structural AND ga_strength. Nodes everywhere,
special points + house-lords + karaka web as relationship participants, graded aspects, Kala Sarpa
unlocked. Completeness-first; volume is the consequence (~90–120k rows est.); no silent drops; runs
after the pre-GA8 closure.*
